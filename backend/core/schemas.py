"""Pydantic schemas for API requests/responses and the core domain objects.

The scoring pipeline operates on plain dicts for speed and testability; these
models document the contract and validate request bodies. Response models allow
extra fields so the pipeline can attach derived data without breaking the API.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

SOURCE_TYPES = {
    "official",
    "major_media",
    "local_media",
    "international_media",
    "specialist",
    "academic",
    "ngo",
    "social",
    "unknown",
}

EVENT_STATUSES = {"new", "reviewing", "confirmed", "monitoring", "dismissed", "archived"}


class Source(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    url: str
    published_at: Optional[str] = None
    source_type: str = "unknown"
    reliability_score: float = 0.0
    political_lean: str = "unknown"
    country_of_origin: str = "unknown"
    independence_group: str = "unknown"


class ScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="allow")

    severity_score: float = 0.0
    urgency_score: float = 0.0
    confidence_score: float = 0.0
    relevance_score: float = 0.0
    source_quality_score: float = 0.0
    base_score: float = 0.0
    penalty_total: float = 0.0
    signal_score: float = 0.0
    feintcon_impact: float = 0.0
    score_explanation: str = ""


class Event(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    title: str
    summary: str = ""
    category: str = "unknown"
    region: str = "unknown"
    country: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    published_at: Optional[str] = None
    occurred_at: Optional[str] = None
    status: str = "new"
    tags: List[str] = Field(default_factory=list)
    sources: List[Source] = Field(default_factory=list)

    severity_score: float = 0.0
    urgency_score: float = 0.0
    confidence_score: float = 0.0
    relevance_score: float = 0.0
    source_quality_score: float = 0.0
    signal_score: float = 0.0
    feintcon_impact: float = 0.0
    score_explanation: str = ""

    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    conflicting_reports: bool = False
    is_stale: bool = False
    social_only: bool = False
    sensational: bool = False
    requires_human_review: bool = False
    alert_level: str = "none"


# ---- Request bodies -------------------------------------------------------

class StatusUpdate(BaseModel):
    status: str = Field(..., description="One of: new, reviewing, confirmed, monitoring, dismissed, archived")


class NoteCreate(BaseModel):
    text: str
    author: str = "operator"


class RunNowRequest(BaseModel):
    reason: str = "manual"


class DiscordTestRequest(BaseModel):
    channel: str = Field("system_status", description="A configured Discord route ID or fs-* channel name.")
    dry_run: bool = True
