"""Agent run endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..core.schemas import RunNowRequest
from ..services import event_service, scheduler_service

router = APIRouter(tags=["agents"])


@router.get("/agents/runs")
def get_runs(limit: int = 25):
    runs = event_service.list_runs(limit=limit)
    return {"count": len(runs), "runs": runs}


@router.post("/agents/run-now")
def run_now(body: RunNowRequest | None = None):
    trigger = body.reason if body else "manual"
    try:
        result = scheduler_service.scheduler.run_once(trigger=trigger)
    except scheduler_service.SchedulerBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    from ..agents import orchestrator
    return {
        "ok": True,
        "summary": orchestrator.summarize(result),
        "run": result["run"],
        "feintcon_level": result["feintcon"]["level"],
        "alerts_generated": len(result["alerts"]),
    }
