"""Alert routing: decide whether a scored event warrants an alert, whether it
needs human review, and build a (non-sent) Discord payload.

Building a payload NEVER sends it. Sending is handled by discord_service and is
disabled unless ENABLE_DISCORD_SEND=true with a configured webhook.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from ..core.config import get_settings
from . import source_validator
from .feintcon_agent import DISCLAIMER

# Categories / claim types that ALWAYS require human review before a critical
# Discord alert. Matched against event category and tags.
HUMAN_REVIEW_CATEGORIES = {"conflict", "war", "terrorism", "cyber", "health", "nuclear", "coup"}
HUMAN_REVIEW_TAGS = {
    "war-start", "escalation", "terrorism", "mass-casualty", "attribution",
    "election-interference", "outbreak", "nuclear", "strategic-weapon",
    "assassination", "coup", "panic-risk",
}

STANDARD = "standard"
CRITICAL = "critical"
NONE = "none"


def requires_human_review(event: dict) -> bool:
    settings = get_settings()
    if event.get("social_only"):
        return True
    if event.get("category") in HUMAN_REVIEW_CATEGORIES:
        return True
    if set(event.get("tags") or []) & HUMAN_REVIEW_TAGS:
        return True
    # Global safety default: gate ALL criticals behind review when configured.
    if settings.require_human_review_for_critical and _meets_critical(event):
        return True
    return False


def _meets_standard(event: dict) -> bool:
    sources = event.get("sources") or []
    best = source_validator.validate_event_sources(event)["best_reliability"]
    return (
        float(event.get("signal_score", 0)) >= 75.0
        and float(event.get("confidence_score", event.get("confidence", 0))) >= 60.0
        and float(best) >= 70.0
        and not event.get("is_duplicate")
    )


def _meets_critical(event: dict) -> bool:
    summary = source_validator.validate_event_sources(event)
    enough_corroboration = summary["independent_source_count"] >= 2 or summary["has_official_source"]
    return (
        float(event.get("signal_score", 0)) >= 85.0
        and float(event.get("confidence_score", event.get("confidence", 0))) >= 75.0
        and enough_corroboration
        and not event.get("is_duplicate")
        and not event.get("is_stale")
    )


def evaluate_alert(event: dict) -> Dict[str, object]:
    """Return an alert decision dict (does not send anything)."""
    reasons: List[str] = []
    level = NONE

    if _meets_critical(event):
        level = CRITICAL
        reasons.append("signal>=85, confidence>=75, corroborated, not duplicate/stale")
    elif _meets_standard(event):
        level = STANDARD
        reasons.append("signal>=75, confidence>=60, reliable source present")
    else:
        reasons.append("below alert thresholds")

    needs_review = requires_human_review(event) if level != NONE else requires_human_review(event)
    channel = "breaking" if level != NONE else None

    return {
        "event_id": event.get("id"),
        "alert_level": level,
        "channel": channel,
        "requires_human_review": needs_review,
        "reasons": reasons,
    }


def build_payload(event: dict, decision: Optional[dict] = None, channel: str = "breaking") -> Dict[str, object]:
    """Build a Discord-style webhook payload. Generation only — never sent here."""
    decision = decision or evaluate_alert(event)
    level = decision.get("alert_level", NONE)
    sources = event.get("sources") or []
    top_sources = ", ".join(s.get("name", "?") for s in sources[:3]) or "none"

    color = {CRITICAL: 0xCC2222, STANDARD: 0xE0A317, NONE: 0x3A6EA5}.get(level, 0x3A6EA5)
    review_note = "⚠ HUMAN REVIEW REQUIRED before any send." if decision.get("requires_human_review") else "Auto-eligible."

    return {
        "channel": channel,
        "username": "FeintSignal",
        "embeds": [
            {
                "title": f"[{level.upper()}] {event.get('title', 'Untitled signal')}",
                "description": event.get("summary", ""),
                "color": color,
                "fields": [
                    {"name": "Signal", "value": str(event.get("signal_score")), "inline": True},
                    {"name": "Confidence", "value": str(event.get("confidence_score", event.get("confidence"))), "inline": True},
                    {"name": "Region", "value": str(event.get("region")), "inline": True},
                    {"name": "Category", "value": str(event.get("category")), "inline": True},
                    {"name": "Sources", "value": top_sources, "inline": False},
                    {"name": "Review", "value": review_note, "inline": False},
                ],
                "footer": {"text": DISCLAIMER},
            }
        ],
    }


def route_alerts(events: List[dict]) -> List[dict]:
    """Evaluate every event; return a list of alert records (payloads built, not sent)."""
    alerts: List[dict] = []
    for ev in events:
        decision = evaluate_alert(ev)
        ev["requires_human_review"] = decision["requires_human_review"]
        ev["alert_level"] = decision["alert_level"]
        if decision["alert_level"] != NONE:
            alerts.append(
                {
                    **decision,
                    "title": ev.get("title"),
                    "payload": build_payload(ev, decision, channel=decision.get("channel") or "breaking"),
                }
            )
    return alerts
