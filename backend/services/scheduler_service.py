"""Lightweight background scheduler for the hourly update loop.

Intentionally simple (stdlib ``threading.Timer``) and OFF by default — the API
exposes manual ``run-now`` and the seed/hourly scripts cover automation. This is
a known area flagged for hardening (see docs/ROADMAP.md).
"""
from __future__ import annotations

import threading
from typing import Optional

from ..core.config import get_settings


class UpdateScheduler:
    def __init__(self, interval_minutes: Optional[int] = None):
        settings = get_settings()
        self.interval_seconds = (interval_minutes or settings.update_interval_minutes) * 60
        self._timer: Optional[threading.Timer] = None
        self._running = False
        self.last_status: Optional[dict] = None

    def _tick(self) -> None:
        if not self._running:
            return
        try:
            from ..agents import orchestrator

            result = orchestrator.run_pipeline(trigger="scheduler")
            self.last_status = {"ok": True, **result["run"]}
        except Exception as exc:  # pragma: no cover - defensive
            self.last_status = {"ok": False, "error": type(exc).__name__}
        finally:
            if self._running:
                self._schedule()

    def _schedule(self) -> None:
        self._timer = threading.Timer(self.interval_seconds, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def start(self, run_immediately: bool = False) -> None:
        if self._running:
            return
        self._running = True
        if run_immediately:
            self._tick()
        else:
            self._schedule()

    def stop(self) -> None:
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    @property
    def running(self) -> bool:
        return self._running
