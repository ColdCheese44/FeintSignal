"""Supervised in-process scheduler with overlap protection and persisted status."""
from __future__ import annotations

import threading
from datetime import timedelta
from typing import Optional

from ..core.config import get_settings
from ..core.time_utils import now_iso, now_utc

STATE_KEY = "scheduler"


class SchedulerBusyError(RuntimeError):
    pass


class UpdateScheduler:
    def __init__(self, interval_minutes: Optional[int] = None):
        settings = get_settings()
        self.interval_minutes = max(1, interval_minutes or settings.update_interval_minutes)
        self._timer: Optional[threading.Timer] = None
        self._state_lock = threading.RLock()
        self._run_lock = threading.Lock()
        self._enabled = False
        self._running_now = False
        self._last_started_at: Optional[str] = None
        self._next_run_at: Optional[str] = None
        self._last_status: Optional[dict] = None

    def _persist(self) -> None:
        try:
            from . import event_service

            event_service.set_system_state(STATE_KEY, self.status())
        except Exception:
            # Scheduling must continue even if a transient state write fails.
            pass

    def _schedule(self) -> None:
        with self._state_lock:
            if not self._enabled:
                return
            self._next_run_at = (now_utc() + timedelta(minutes=self.interval_minutes)).isoformat().replace("+00:00", "Z")
            self._timer = threading.Timer(self.interval_minutes * 60, self._tick)
            self._timer.daemon = True
            self._timer.start()
        self._persist()

    def _tick(self) -> None:
        with self._state_lock:
            if not self._enabled:
                return
            self._timer = None
            self._next_run_at = None
        try:
            self.run_once("scheduler")
        except SchedulerBusyError:
            with self._state_lock:
                self._last_status = {"ok": False, "reason": "overlap_prevented", "finished_at": now_iso()}
        finally:
            with self._state_lock:
                should_continue = self._enabled
            if should_continue:
                self._schedule()

    def run_once(self, trigger: str = "manual") -> dict:
        if not self._run_lock.acquire(blocking=False):
            raise SchedulerBusyError("A FeintSignal pipeline run is already active.")
        with self._state_lock:
            self._running_now = True
            self._last_started_at = now_iso()
            self._next_run_at = None
        self._persist()
        try:
            from ..agents import orchestrator

            result = orchestrator.run_pipeline(trigger=trigger)
            with self._state_lock:
                self._last_status = {"ok": True, **result["run"]}
            return result
        except Exception as exc:
            with self._state_lock:
                self._last_status = {"ok": False, "error": type(exc).__name__, "finished_at": now_iso()}
            try:
                from . import discord_service

                discord_service.dispatch_error(type(exc).__name__, trigger)
            except Exception:
                pass
            raise
        finally:
            with self._state_lock:
                self._running_now = False
            self._run_lock.release()
            self._persist()

    def start(self, interval_minutes: Optional[int] = None, run_immediately: bool = False) -> dict:
        with self._state_lock:
            if interval_minutes is not None:
                self.interval_minutes = max(1, interval_minutes)
            if self._enabled:
                return self.status()
            self._enabled = True
        if run_immediately:
            threading.Thread(target=self._tick, name="feintsignal-scheduler", daemon=True).start()
        else:
            self._schedule()
        self._persist()
        return self.status()

    def stop(self) -> dict:
        with self._state_lock:
            self._enabled = False
            self._next_run_at = None
            if self._timer:
                self._timer.cancel()
                self._timer = None
        self._persist()
        return self.status()

    def status(self) -> dict:
        with self._state_lock:
            return {
                "scheduler_enabled": self._enabled,
                "scheduler_interval_minutes": self.interval_minutes,
                "scheduler_running_now": self._running_now,
                "scheduler_last_started_at": self._last_started_at,
                "scheduler_next_run_at": self._next_run_at,
                "scheduler_last_status": self._last_status,
            }


scheduler = UpdateScheduler()
