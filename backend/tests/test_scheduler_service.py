"""Scheduler state, controls, and overlap protection."""
import threading

import pytest

from backend.services import scheduler_service


def test_scheduler_start_stop_status(monkeypatch):
    monkeypatch.setattr(scheduler_service.UpdateScheduler, "_persist", lambda self: None)
    instance = scheduler_service.UpdateScheduler(interval_minutes=60)
    started = instance.start(interval_minutes=30)
    assert started["scheduler_enabled"] is True
    assert started["scheduler_interval_minutes"] == 30
    assert started["scheduler_next_run_at"]
    stopped = instance.stop()
    assert stopped["scheduler_enabled"] is False
    assert stopped["scheduler_next_run_at"] is None


def test_scheduler_prevents_overlapping_runs(monkeypatch):
    monkeypatch.setattr(scheduler_service.UpdateScheduler, "_persist", lambda self: None)
    entered = threading.Event()
    release = threading.Event()

    def slow_pipeline(trigger):
        entered.set()
        release.wait(timeout=2)
        return {"run": {"trigger": trigger, "status": "ok"}}

    from backend.agents import orchestrator

    monkeypatch.setattr(orchestrator, "run_pipeline", slow_pipeline)
    instance = scheduler_service.UpdateScheduler(interval_minutes=60)
    worker = threading.Thread(target=lambda: instance.run_once("first"))
    worker.start()
    assert entered.wait(timeout=1)
    with pytest.raises(scheduler_service.SchedulerBusyError):
        instance.run_once("second")
    release.set()
    worker.join(timeout=2)
    assert instance.status()["scheduler_last_status"]["ok"] is True
