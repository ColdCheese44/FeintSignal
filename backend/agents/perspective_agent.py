"""Deterministic viewpoint analysis for neutral situation-room briefings.

This agent does not invent reporting or claim that an LLM performed research.
It synthesizes only framing and source metadata already attached to an event.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List

LEFT_LEANS = {"left", "center-left"}
RIGHT_LEANS = {"right", "center-right"}
CENTER_LEANS = {"center"}


def _source_balance(event: dict) -> Dict[str, int]:
    counts = Counter(str(source.get("political_lean", "unknown")) for source in event.get("sources") or [])
    return {
        "left": sum(counts[lean] for lean in LEFT_LEANS),
        "center": sum(counts[lean] for lean in CENTER_LEANS),
        "right": sum(counts[lean] for lean in RIGHT_LEANS),
        "state_aligned": counts["state-aligned"],
        "unknown": counts["unknown"],
        "total": sum(counts.values()),
    }


def _uncertainties(event: dict, balance: Dict[str, int]) -> List[str]:
    items: List[str] = []
    if event.get("conflicting_reports"):
        items.append("Sources disagree on material details.")
    if event.get("social_only"):
        items.append("The available evidence is social-primary and remains unverified.")
    if event.get("is_stale"):
        items.append("The underlying reporting is stale and may not reflect current conditions.")
    if balance["total"] < 2:
        items.append("Only one source is represented; independent corroboration is limited.")
    framing = event.get("political_framing") or {}
    terms = framing.get("contested_terms") or []
    if terms:
        items.append(f"Contested language: {', '.join(str(term) for term in terms)}.")
    if not items:
        items.append("No material uncertainty flags were generated from the current evidence set.")
    return items


def analyze_event(event: dict) -> Dict[str, object]:
    """Build an attributed perspective card from existing event evidence."""
    framing = event.get("political_framing") or {}
    balance = _source_balance(event)
    left = framing.get("left_frame") or "No explicit left-leaning frame is supplied in the current evidence set."
    right = framing.get("right_frame") or "No explicit right-leaning frame is supplied in the current evidence set."
    center = (
        f"The evidence set contains {balance['total']} source(s): "
        f"{balance['left']} left/center-left, {balance['center']} center, "
        f"{balance['right']} right/center-right, {balance['state_aligned']} state-aligned, "
        f"and {balance['unknown']} unknown."
    )
    consensus = str(event.get("summary") or "No neutral event summary is available.")
    if event.get("conflicting_reports"):
        consensus = f"Confirmed core: {consensus} Specific disputed details require continued monitoring."
    return {
        "event_id": event.get("id"),
        "title": event.get("title"),
        "neutral_assessment": str(event.get("summary") or ""),
        "what_the_left_says": left,
        "what_the_center_says": center,
        "what_the_right_says": right,
        "consensus": consensus,
        "uncertainties": _uncertainties(event, balance),
        "source_balance": balance,
        "method": "Deterministic synthesis of supplied source metadata and attributed framing; no external AI call.",
    }


def analyze_events(events: List[dict], limit: int = 5) -> List[dict]:
    active = [event for event in events if not event.get("is_duplicate")]
    ordered = sorted(active, key=lambda event: float(event.get("signal_score", 0)), reverse=True)
    return [analyze_event(event) for event in ordered[:limit]]
