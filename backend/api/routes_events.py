"""Event endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..agents import perspective_agent
from ..core.schemas import EVENT_STATUSES, NoteCreate, StatusUpdate
from ..services import event_service

router = APIRouter(tags=["events"])


def _primary_url(event: dict) -> Optional[str]:
    """Best clickable source URL for the event (first valid http(s) link)."""
    for source in event.get("sources") or []:
        url = str(source.get("url") or "")
        if url.startswith("http://") or url.startswith("https://"):
            return url
    return None


def _briefing_perspective(event_id: str) -> Optional[dict]:
    """An AI-enriched perspective card for this event from the latest briefing, if any."""
    briefing = event_service.latest_briefing()
    if not briefing:
        return None
    for entry in briefing.get("perspective_analysis") or []:
        if entry.get("event_id") == event_id:
            return entry
    return None


@router.get("/events")
def get_events(
    region: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_signal: Optional[float] = Query(None),
    include_duplicates: bool = Query(True),
):
    events = event_service.list_events(
        region=region,
        category=category,
        min_signal=min_signal,
        include_duplicates=include_duplicates,
    )
    return {"count": len(events), "events": events}


@router.get("/events/{event_id}")
def get_event(event_id: str):
    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    return event


@router.post("/events/{event_id}/status")
def update_status(event_id: str, body: StatusUpdate):
    if body.status not in EVENT_STATUSES:
        raise HTTPException(status_code=422, detail=f"invalid status; allowed: {sorted(EVENT_STATUSES)}")
    event = event_service.set_status(event_id, body.status)
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    return {"ok": True, "event": event}


@router.post("/events/{event_id}/notes")
def add_note(event_id: str, body: NoteCreate):
    event = event_service.add_note(event_id, body.text, body.author)
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    return {"ok": True, "event": event}


@router.get("/events/{event_id}/perspective")
def event_perspective(event_id: str):
    """Neutral left/center/right article for one event.

    Deterministic baseline, overlaid with any AI-enriched version already produced
    for this event in the latest daily briefing.
    """
    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    card = perspective_agent.analyze_event(event)
    enriched = _briefing_perspective(event_id)
    if enriched:
        card = {**card, **{k: v for k, v in enriched.items() if v}}
    card["primary_url"] = _primary_url(event)
    return card


@router.post("/events/{event_id}/perspective/generate")
def generate_event_perspective(event_id: str):
    """Generate (or refresh) an AI-written neutral article for one event on demand.

    Reuses the evidence-bound, gated llm_service. With ENABLE_LLM=false this
    returns the deterministic baseline and a disabled status — never an error.
    """
    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    # Imported here so the module import stays light for the rest of the API.
    from ..services import llm_service

    baseline = perspective_agent.analyze_event(event)
    mini_briefing = {"perspective_analysis": [baseline], "briefing_date": ""}
    llm_service.enrich_briefing(mini_briefing, [event])
    card = mini_briefing["perspective_analysis"][0]
    card["primary_url"] = _primary_url(event)
    return {"perspective": card, "llm_analysis": mini_briefing.get("llm_analysis")}
