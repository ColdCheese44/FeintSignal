"""Source validation and reliability tiering.

Validates required source fields, normalises ``source_type``, and derives a
trust tier. Does NOT assign defamatory labels to any real outlet — for mock data
all sources are fictional/neutral and reliability is supplied explicitly.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from ..core.schemas import SOURCE_TYPES

REQUIRED_FIELDS = (
    "name",
    "url",
    "published_at",
    "source_type",
    "reliability_score",
    "political_lean",
    "country_of_origin",
    "independence_group",
)

# Source types considered "primary/credible" structurally (before reliability).
CREDIBLE_TYPES = {"official", "major_media", "international_media", "specialist", "academic", "ngo"}


def validate_source(source: dict) -> Tuple[bool, List[str]]:
    """Return (is_valid, issues). A source is valid if it has the required
    fields, a known source_type, and a reliability_score in [0, 100]."""
    issues: List[str] = []
    for field in REQUIRED_FIELDS:
        if source.get(field) in (None, ""):
            issues.append(f"missing:{field}")

    stype = source.get("source_type")
    if stype is not None and stype not in SOURCE_TYPES:
        issues.append(f"invalid_source_type:{stype}")

    url = source.get("url")
    if url and not (str(url).startswith("http://") or str(url).startswith("https://")):
        issues.append("invalid_url_scheme")

    try:
        rel = float(source.get("reliability_score"))
        if not 0.0 <= rel <= 100.0:
            issues.append("reliability_out_of_range")
    except (TypeError, ValueError):
        issues.append("reliability_not_numeric")

    return (len(issues) == 0, issues)


def reliability_tier(score: float) -> str:
    if score >= 80:
        return "high"
    if score >= 65:
        return "moderate"
    if score >= 45:
        return "low"
    return "unverified"


def independence_groups(sources: List[dict]) -> List[str]:
    return sorted({s.get("independence_group") for s in sources if s.get("independence_group")})


def has_official_source(sources: List[dict]) -> bool:
    return any(s.get("source_type") == "official" for s in sources)


def count_independent_sources(sources: List[dict]) -> int:
    """Distinct independence groups among structurally-credible, valid sources."""
    groups = set()
    for s in sources:
        if s.get("source_type") in CREDIBLE_TYPES:
            ok, _ = validate_source(s)
            if ok:
                groups.add(s.get("independence_group"))
    return len(groups)


def validate_event_sources(event: dict) -> Dict[str, object]:
    """Summarise the source posture of an event for scoring / alerting / UI."""
    sources = event.get("sources") or []
    valid, invalid = [], []
    for s in sources:
        ok, issues = validate_source(s)
        (valid if ok else invalid).append({"name": s.get("name"), "issues": issues})

    reliabilities = [float(s.get("reliability_score", 0) or 0) for s in sources]
    best = max(reliabilities) if reliabilities else 0.0

    return {
        "source_count": len(sources),
        "valid_count": len(valid),
        "invalid_sources": [v for v in invalid if v["issues"]],
        "independent_groups": independence_groups(sources),
        "independent_source_count": count_independent_sources(sources),
        "has_official_source": has_official_source(sources),
        "best_reliability": best,
        "best_reliability_tier": reliability_tier(best),
        "meets_min_reliability": best >= 70.0,
    }
