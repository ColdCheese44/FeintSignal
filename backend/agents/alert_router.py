"""Score-threshold alert routing and Discord payload generation.

Building a payload never sends it. Delivery remains disabled unless
ENABLE_DISCORD_SEND=true and the matching webhook is configured.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from ..core.discord_routing import resolve_channel
from . import source_validator
from .feintcon_agent import DISCLAIMER

STANDARD = "standard"
CRITICAL = "critical"
NONE = "none"


def _meets_standard(event: dict) -> bool:
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
    """Return an alert decision without sending anything."""
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

    route = "critical" if level == CRITICAL else "breaking" if level == STANDARD else None
    channel = resolve_channel(route)["channel_name"] if route else None
    return {
        "event_id": event.get("id"),
        "alert_level": level,
        "route": route,
        "channel": channel,
        "reasons": reasons,
    }


def build_payload(event: dict, decision: Optional[dict] = None, channel: Optional[str] = None) -> Dict[str, object]:
    """Build a Discord webhook payload without sending it."""
    decision = decision or evaluate_alert(event)
    target = resolve_channel(channel or str(decision.get("route") or "breaking"))
    level = decision.get("alert_level", NONE)
    sources = event.get("sources") or []
    top_sources = ", ".join(source.get("name", "?") for source in sources[:3]) or "none"
    color = {CRITICAL: 0xCC2222, STANDARD: 0xE0A317, NONE: 0x3A6EA5}.get(level, 0x3A6EA5)

    return {
        "route": target["id"],
        "channel": target["channel_name"],
        "username": "Watchtower",
        "embeds": [
            {
                "title": f"[{str(level).upper()}] {event.get('title', 'Untitled signal')}",
                "description": event.get("summary", ""),
                "color": color,
                "fields": [
                    {"name": "Signal", "value": str(event.get("signal_score")), "inline": True},
                    {"name": "Confidence", "value": str(event.get("confidence_score", event.get("confidence"))), "inline": True},
                    {"name": "Region", "value": str(event.get("region")), "inline": True},
                    {"name": "Category", "value": str(event.get("category")), "inline": True},
                    {"name": "Sources", "value": top_sources, "inline": False},
                ],
                "footer": {"text": DISCLAIMER},
            }
        ],
    }


def route_alerts(events: List[dict]) -> List[dict]:
    """Evaluate all events and return alert records for eligible signals."""
    alerts: List[dict] = []
    for event in events:
        decision = evaluate_alert(event)
        event["alert_level"] = decision["alert_level"]
        if decision["alert_level"] != NONE:
            alerts.append(
                {
                    **decision,
                    "title": event.get("title"),
                    "payload": build_payload(event, decision, channel=decision.get("route") or "breaking"),
                }
            )
    return alerts
