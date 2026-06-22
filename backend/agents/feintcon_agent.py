"""FEINTCON — FeintSignal internal readiness indicator.

IMPORTANT: FEINTCON is an internal FeintSignal readiness indicator. It is NOT an
official government or military readiness condition (DEFCON). The interface is
"DEFCON-style" in presentation only.

Levels:
  5 = Normal monitoring
  4 = Elevated global noise or regional instability
  3 = Significant multi-region instability or major confirmed crisis
  2 = Severe global risk posture / cascading crisis potential
  1 = Extreme global crisis posture
"""
from __future__ import annotations

from typing import Dict, List

DISCLAIMER = (
    "FEINTCON is an internal FeintSignal readiness indicator. "
    "It is not an official government or military readiness condition."
)

LABELS = {
    5: "Normal monitoring",
    4: "Elevated global noise or regional instability",
    3: "Significant multi-region instability or major confirmed crisis",
    2: "Severe global risk posture / cascading crisis potential",
    1: "Extreme global crisis posture",
}

HIGH_SIGNAL_MIN = 70.0
HIGH_SIGNAL_CONFIDENCE_MIN = 55.0
CRITICAL_SIGNAL_MIN = 85.0
CRITICAL_CONFIDENCE_MIN = 75.0


def compute_feintcon(events: List[dict]) -> Dict[str, object]:
    active = [e for e in events if not e.get("is_duplicate")]

    high = [
        e for e in active
        if float(e.get("signal_score", 0)) >= HIGH_SIGNAL_MIN
        and float(e.get("confidence_score", e.get("confidence", 0))) >= HIGH_SIGNAL_CONFIDENCE_MIN
    ]
    critical = [
        e for e in active
        if float(e.get("signal_score", 0)) >= CRITICAL_SIGNAL_MIN
        and float(e.get("confidence_score", e.get("confidence", 0))) >= CRITICAL_CONFIDENCE_MIN
        and not e.get("is_stale")
    ]
    regions = sorted({e.get("region") for e in high if e.get("region")})
    n_high, n_crit, n_regions = len(high), len(critical), len(regions)

    if n_crit >= 3 or (n_crit >= 2 and n_regions >= 4):
        level = 1
    elif n_crit >= 2 or (n_high >= 5 and n_regions >= 3):
        level = 2
    elif n_crit >= 1 or (n_high >= 3 and n_regions >= 2):
        level = 3
    elif n_high >= 1:
        level = 4
    else:
        level = 5

    rationale = (
        f"{n_high} high-signal event(s) across {n_regions} region(s); "
        f"{n_crit} at critical threshold."
    )

    return {
        "level": level,
        "label": LABELS[level],
        "rationale": rationale,
        "disclaimer": DISCLAIMER,
        "metrics": {
            "high_signal_events": n_high,
            "critical_events": n_crit,
            "regions_in_focus": regions,
            "region_count": n_regions,
        },
        "is_official_defcon": False,
    }
