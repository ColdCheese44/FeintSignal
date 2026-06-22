"""Tests for direct signal-threshold alert routing."""
from backend.agents.alert_router import evaluate_alert


def _src(**overrides):
    source = {
        "name": "Src",
        "url": "https://example.org/s",
        "published_at": "2026-06-21T00:00:00Z",
        "source_type": "major_media",
        "reliability_score": 80,
        "political_lean": "center",
        "country_of_origin": "X",
        "independence_group": "a",
    }
    source.update(overrides)
    return source


def test_standard_alert_routes_to_breaking():
    event = {
        "id": "s1",
        "title": "Federal budget standoff",
        "category": "politics",
        "tags": ["politics"],
        "signal_score": 80,
        "confidence_score": 70,
        "is_duplicate": False,
        "is_stale": False,
        "sources": [_src(reliability_score=80, independence_group="a")],
    }
    decision = evaluate_alert(event)
    assert decision["alert_level"] == "standard"
    assert decision["route"] == "breaking"
    assert decision["channel"] == "fs-breaking-alerts"


def test_critical_conflict_routes_directly_to_critical():
    event = {
        "id": "c1",
        "title": "Cross-border strikes along contested frontier",
        "category": "conflict",
        "tags": ["conflict", "escalation"],
        "signal_score": 90,
        "confidence_score": 80,
        "is_duplicate": False,
        "is_stale": False,
        "sources": [
            _src(source_type="official", reliability_score=88, independence_group="gov"),
            _src(source_type="international_media", reliability_score=80, independence_group="wire"),
        ],
    }
    decision = evaluate_alert(event)
    assert decision["alert_level"] == "critical"
    assert decision["route"] == "critical"
    assert decision["channel"] == "fs-critical-alerts"
