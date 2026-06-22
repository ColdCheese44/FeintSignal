"""Event endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..core.schemas import EVENT_STATUSES, NoteCreate, StatusUpdate
from ..services import event_service

router = APIRouter(tags=["events"])


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
