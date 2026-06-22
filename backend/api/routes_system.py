"""System endpoints: health, FEINTCON, heartbeat."""
from __future__ import annotations

from fastapi import APIRouter

from ..agents import feintcon_agent, heartbeat_agent
from ..core.config import get_settings
from ..core.schemas import SchedulerStartRequest
from ..services import event_service, scheduler_service

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "feintsignal", "config": get_settings().safe_summary()}


@router.get("/system/feintcon")
def feintcon():
    events = event_service.list_events()
    status = feintcon_agent.compute_feintcon(events)
    return status


@router.get("/system/heartbeat")
def heartbeat():
    last_run = event_service.latest_run()
    feintcon_level = last_run.get("feintcon_level") if last_run else None
    return heartbeat_agent.build_heartbeat(last_run=last_run, feintcon_level=feintcon_level)


@router.get("/system/scheduler")
def scheduler_status():
    return scheduler_service.scheduler.status()


@router.post("/system/scheduler/start")
def scheduler_start(body: SchedulerStartRequest | None = None):
    return scheduler_service.scheduler.start(
        interval_minutes=body.interval_minutes if body else None,
        run_immediately=body.run_immediately if body else False,
    )


@router.post("/system/scheduler/stop")
def scheduler_stop():
    return scheduler_service.scheduler.stop()
