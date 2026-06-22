"""Agent run endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from ..agents import orchestrator
from ..core.schemas import RunNowRequest
from ..services import event_service

router = APIRouter(tags=["agents"])


@router.get("/agents/runs")
def get_runs(limit: int = 25):
    runs = event_service.list_runs(limit=limit)
    return {"count": len(runs), "runs": runs}


@router.post("/agents/run-now")
def run_now(body: RunNowRequest | None = None):
    trigger = body.reason if body else "manual"
    result = orchestrator.run_pipeline(trigger=trigger)
    return {
        "ok": True,
        "summary": orchestrator.summarize(result),
        "run": result["run"],
        "feintcon_level": result["feintcon"]["level"],
        "alerts_generated": len(result["alerts"]),
    }
