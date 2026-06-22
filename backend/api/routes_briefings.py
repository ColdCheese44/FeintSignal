"""Daily briefing endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..agents import orchestrator
from ..services import event_service

router = APIRouter(tags=["briefings"])


@router.get("/briefings/daily/latest")
def latest_briefing():
    briefing = event_service.latest_briefing()
    if not briefing:
        raise HTTPException(status_code=404, detail="no briefing generated yet; run the pipeline first")
    return briefing


@router.post("/briefings/daily/generate")
def generate_briefing():
    result = orchestrator.run_pipeline(trigger="briefing")
    return result["briefing"]
