"""Deterministic signal scoring.

signal_score =
    severity        * 0.30 +
    urgency         * 0.20 +
    confidence      * 0.25 +
    relevance       * 0.15 +
    source_quality  * 0.10

then penalties are subtracted. Every scored event carries a human-readable
``score_explanation``. The function is pure and side-effect free so it can be
unit-tested with exact expected values.
"""
from __future__ import annotations

from typing import Dict, List, Optional

# Weights MUST sum to 1.0. Mirrored in config/scoring_rules.json for the UI.
DEFAULT_SCORING_RULES: Dict[str, object] = {
    "weights": {
        "severity": 0.30,
        "urgency": 0.20,
        "confidence": 0.25,
        "relevance": 0.15,
        "source_quality": 0.10,
    },
    "penalties": {
        "duplicate": 15.0,
        "low_confidence": 10.0,
        "conflicting_reports": 8.0,
        "stale": 6.0,
        "social_only": 12.0,
        "sensational": 5.0,
    },
    "thresholds": {
        "low_confidence_below": 50.0,
        "stale_hours": 72.0,
    },
}

# Curated clickbait / sensational terms. Deliberately conservative so legitimate
# crisis vocabulary ("earthquake", "outbreak") is NOT penalised.
SENSATIONAL_TERMS = (
    "shocking",
    "you won't believe",
    "bombshell",
    "jaw-dropping",
    "apocalyptic",
    "obliterate",
    "annihilate",
    "blows the lid",
    "explosive claim",
    "they don't want you to know",
    "terrifying truth",
    "world war 3",
)


def _num(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def compute_source_quality(sources: List[dict]) -> float:
    """Aggregate source reliability into a 0-100 quality score.

    Rewards a strong best source, a healthy average, and independent corroboration.
    """
    if not sources:
        return 0.0
    reliabilities = [_num(s.get("reliability_score")) for s in sources]
    best = max(reliabilities)
    avg = sum(reliabilities) / len(reliabilities)
    groups = {s.get("independence_group") for s in sources if s.get("independence_group")}
    diversity_bonus = 5.0 if len(groups) >= 2 else 0.0
    return round(clamp(best * 0.6 + avg * 0.4 + diversity_bonus), 2)


def detect_sensational(text: str) -> bool:
    lowered = (text or "").lower()
    return any(term in lowered for term in SENSATIONAL_TERMS)


def detect_social_only(sources: List[dict]) -> bool:
    if not sources:
        return False
    return all((s.get("source_type") == "social") for s in sources)


def score_event(event: dict, rules: Optional[Dict[str, object]] = None) -> dict:
    """Return a new dict with all score_* fields and a score_explanation populated.

    Cross-event flags (``is_duplicate``, ``conflicting_reports``, ``is_stale``)
    are expected to be set upstream by the deduper / normalizer. Derivable flags
    (``social_only``, ``sensational``, low-confidence) are computed here.
    """
    rules = rules or DEFAULT_SCORING_RULES
    weights = rules["weights"]  # type: ignore[index]
    penalties = rules["penalties"]  # type: ignore[index]
    thresholds = rules["thresholds"]  # type: ignore[index]

    out = dict(event)
    sources = out.get("sources") or []

    severity = clamp(_num(out.get("severity")))
    urgency = clamp(_num(out.get("urgency")))
    confidence = clamp(_num(out.get("confidence")))
    relevance = clamp(_num(out.get("relevance")))
    source_quality = compute_source_quality(sources)

    base = (
        severity * weights["severity"]
        + urgency * weights["urgency"]
        + confidence * weights["confidence"]
        + relevance * weights["relevance"]
        + source_quality * weights["source_quality"]
    )

    social_only = detect_social_only(sources)
    sensational = detect_sensational(f"{out.get('title', '')} {out.get('summary', '')}")
    low_confidence = confidence < _num(thresholds["low_confidence_below"], 50.0)

    applied: List[str] = []
    penalty_total = 0.0

    def add(flag: bool, key: str, label: str) -> None:
        nonlocal penalty_total
        if flag:
            amount = _num(penalties[key])
            penalty_total += amount
            applied.append(f"-{amount:g} {label}")

    add(bool(out.get("is_duplicate")), "duplicate", "duplicate")
    add(low_confidence, "low_confidence", "low confidence")
    add(bool(out.get("conflicting_reports")), "conflicting_reports", "conflicting reports")
    add(bool(out.get("is_stale")), "stale", "stale information")
    add(social_only, "social_only", "social-only sourcing")
    add(sensational, "sensational", "sensational wording")

    signal = round(clamp(base - penalty_total), 2)
    # Per-event contribution to global readiness (drives FEINTCON & UI heat).
    feintcon_impact = round(clamp(0.7 * signal + 0.3 * severity), 2)

    out["severity_score"] = round(severity, 2)
    out["urgency_score"] = round(urgency, 2)
    out["confidence_score"] = round(confidence, 2)
    out["relevance_score"] = round(relevance, 2)
    out["source_quality_score"] = source_quality
    out["base_score"] = round(base, 2)
    out["penalty_total"] = round(penalty_total, 2)
    out["signal_score"] = signal
    out["feintcon_impact"] = feintcon_impact
    out["social_only"] = social_only
    out["sensational"] = sensational
    out["low_confidence"] = low_confidence

    penalty_text = "; ".join(applied) if applied else "no penalties"
    out["score_explanation"] = (
        f"base {base:.1f} = sev {severity:g}x.30 + urg {urgency:g}x.20 + "
        f"conf {confidence:g}x.25 + rel {relevance:g}x.15 + srcq {source_quality:g}x.10; "
        f"penalties [{penalty_text}] -> signal {signal:g}"
    )
    return out


def score_events(events: List[dict], rules: Optional[Dict[str, object]] = None) -> List[dict]:
    return [score_event(e, rules) for e in events]
