"""Tests for alert routing and human-review gating."""
from backend.agents.alert_router import evaluate_alert


def _src(**o):
    base = {
        "name": "Src",
        "url": "https://example.org/s",
        "published_at": "2026-06-21T00:00:00Z",
        "source_type": "major_media",
        "reliability_score": 80,
        "political_lean": "center",
        "country_of_origin": "X",
        "independence_group": "a",
    }
    base.update(o)
    return base


def test_standard_alert_no_review_for_neutral_category():
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
    assert decision["requires_human_review"] is False


def test_critical_conflict_requires_human_review():
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
    assert decision["requires_human_review"] is True
