"""Daily briefing generator.

Produces a deterministic, template-based briefing from scored events and the
FEINTCON status. No LLM is used (ENABLE_LLM=false by default); the structure is
LLM-upgradeable later behind that gate.
"""
from __future__ import annotations

from typing import Dict, List

from ..core.time_utils import now_iso, now_utc
from .feintcon_agent import DISCLAIMER


def _top_signals(events: List[dict], limit: int = 5) -> List[dict]:
    active = [e for e in events if not e.get("is_duplicate")]
    ordered = sorted(active, key=lambda e: float(e.get("signal_score", 0)), reverse=True)
    return [
        {
            "id": e.get("id"),
            "title": e.get("title"),
            "region": e.get("region"),
            "category": e.get("category"),
            "signal_score": e.get("signal_score"),
            "requires_human_review": e.get("requires_human_review", False),
        }
        for e in ordered[:limit]
    ]


def generate_briefing(events: List[dict], feintcon: Dict[str, object]) -> Dict[str, object]:
    active = [e for e in events if not e.get("is_duplicate")]
    by_region: Dict[str, int] = {}
    for e in active:
        by_region[e.get("region", "unknown")] = by_region.get(e.get("region", "unknown"), 0) + 1

    review_queue = [
        {"id": e.get("id"), "title": e.get("title")}
        for e in active
        if e.get("requires_human_review") and e.get("alert_level") in ("standard", "critical")
    ]

    top = _top_signals(active)
    headline = top[0]["title"] if top else "No notable signals."

    return {
        "briefing_date": now_utc().date().isoformat(),
        "generated_at": now_iso(),
        "feintcon_level": feintcon.get("level"),
        "feintcon_label": feintcon.get("label"),
        "headline": headline,
        "summary": (
            f"FEINTCON {feintcon.get('level')} — {feintcon.get('label')}. "
            f"{len(active)} active signals across {len(by_region)} regions. "
            f"{len(review_queue)} item(s) awaiting human review."
        ),
        "top_signals": top,
        "events_by_region": by_region,
        "human_review_queue": review_queue,
        "disclaimer": DISCLAIMER,
    }
