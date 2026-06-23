"""Deterministic daily briefing generator and LLM fallback baseline."""
from __future__ import annotations

from typing import Dict, List

from ..core.time_utils import now_iso, now_utc
from .feintcon_agent import DISCLAIMER
from .perspective_agent import analyze_events


def _top_signals(events: List[dict], limit: int = 5) -> List[dict]:
    active = [event for event in events if not event.get("is_duplicate")]
    ordered = sorted(active, key=lambda event: float(event.get("signal_score", 0)), reverse=True)
    return [
        {
            "id": event.get("id"),
            "title": event.get("title"),
            "region": event.get("region"),
            "category": event.get("category"),
            "signal_score": event.get("signal_score"),
        }
        for event in ordered[:limit]
    ]


def generate_briefing(events: List[dict], feintcon: Dict[str, object]) -> Dict[str, object]:
    active = [event for event in events if not event.get("is_duplicate")]
    by_region: Dict[str, int] = {}
    for event in active:
        region = event.get("region", "unknown")
        by_region[region] = by_region.get(region, 0) + 1

    top = _top_signals(active)
    headline = top[0]["title"] if top else "No notable signals."
    alert_count = sum(event.get("alert_level") in ("standard", "critical") for event in active)

    return {
        "briefing_date": now_utc().date().isoformat(),
        "generated_at": now_iso(),
        "feintcon_level": feintcon.get("level"),
        "feintcon_label": feintcon.get("label"),
        "headline": headline,
        "summary": (
            f"FEINTCON {feintcon.get('level')} - {feintcon.get('label')}. "
            f"{len(active)} active signals across {len(by_region)} regions. "
            f"{alert_count} alert-qualified item(s)."
        ),
        "top_signals": top,
        "events_by_region": by_region,
        "perspective_analysis": analyze_events(active, limit=15),
        "intelligence_method": (
            "Multi-source deterministic synthesis. Political framing is attributed, uncertainty is explicit, "
            "and any optional AI enrichment is recorded separately."
        ),
        "disclaimer": DISCLAIMER,
    }
