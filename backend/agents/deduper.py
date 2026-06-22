"""Duplicate / near-duplicate detection and noise suppression.

Two events are considered the same story when they share region AND category and
their titles overlap meaningfully (token overlap or a shared tag). The
higher-confidence event is kept as canonical; the others are flagged
``is_duplicate`` with ``duplicate_of`` pointing at the canonical id.
"""
from __future__ import annotations

import re
from typing import Dict, List

STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "or", "as",
    "amid", "ahead", "along", "near", "over", "after", "before", "with", "by",
    "reported", "reports", "report", "claim", "claims", "says", "say", "new",
    "update", "breaking", "live",
}


def _tokens(title: str) -> set:
    words = re.findall(r"[a-z0-9]+", (title or "").lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def similarity(e1: dict, e2: dict) -> float:
    """0-1 similarity used for clustering. Requires same region+category to be
    considered at all (geographic/topical guard against false merges)."""
    if (e1.get("region"), e1.get("category")) != (e2.get("region"), e2.get("category")):
        return 0.0
    t1, t2 = _tokens(e1.get("title", "")), _tokens(e2.get("title", ""))
    overlap = len(t1 & t2)
    jac = _jaccard(t1, t2)
    shared_tag = bool(set(e1.get("tags") or []) & set(e2.get("tags") or []))
    score = jac
    if overlap >= 2:
        score = max(score, 0.6)
    if shared_tag and overlap >= 1:
        score = max(score, 0.6)
    return round(score, 3)


def find_duplicates(events: List[dict], threshold: float = 0.6) -> Dict[str, str]:
    """Return a mapping of duplicate_event_id -> canonical_event_id."""
    duplicate_of: Dict[str, str] = {}
    # Canonical preference: higher confidence, then higher severity, then earlier.
    ordered = sorted(
        events,
        key=lambda e: (float(e.get("confidence", 0) or 0), float(e.get("severity", 0) or 0)),
        reverse=True,
    )
    canonicals: List[dict] = []
    for ev in ordered:
        matched = None
        for canon in canonicals:
            if similarity(ev, canon) >= threshold:
                matched = canon
                break
        if matched is None:
            canonicals.append(ev)
        else:
            duplicate_of[ev["id"]] = matched["id"]
    return duplicate_of


def mark_duplicates(events: List[dict], threshold: float = 0.6) -> List[dict]:
    """Annotate events in place-style (returns new list) with duplicate flags."""
    mapping = find_duplicates(events, threshold)
    out = []
    for ev in events:
        ev = dict(ev)
        if ev["id"] in mapping:
            ev["is_duplicate"] = True
            ev["duplicate_of"] = mapping[ev["id"]]
        else:
            ev.setdefault("is_duplicate", False)
            ev.setdefault("duplicate_of", None)
        out.append(ev)
    return out
