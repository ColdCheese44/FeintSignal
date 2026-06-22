"""System endpoints: health, FEINTCON, heartbeat."""
from __future__ import annotations

from fastapi import APIRouter

from ..agents import feintcon_agent, heartbeat_agent
from ..core.config import get_settings
from ..services import event_service

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
