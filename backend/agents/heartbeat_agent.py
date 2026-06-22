"""Heartbeat: reports the health/posture of the agent pipeline and config gates."""
from __future__ import annotations

from typing import Dict, List, Optional

from ..core.config import get_settings
from ..core.time_utils import now_iso

AGENTS: List[str] = [
    "collector_agent",
    "normalizer_agent",
    "source_validator",
    "deduper",
    "signal_scorer",
    "feintcon_agent",
    "alert_router",
    "perspective_agent",
    "briefing_agent",
    "heartbeat_agent",
]


def build_heartbeat(last_run: Optional[dict] = None, feintcon_level: Optional[int] = None) -> Dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "checked_at": now_iso(),
        "mode": settings.env,
        "agents": [{"name": a, "status": "ready"} for a in AGENTS],
        "last_run": last_run,
        "feintcon_level": feintcon_level,
        "gates": {
            "live_research": settings.enable_live_research,
            "llm": settings.enable_llm,
            "discord_send": settings.enable_discord_send,
        },
        "update_interval_minutes": settings.update_interval_minutes,
    }
