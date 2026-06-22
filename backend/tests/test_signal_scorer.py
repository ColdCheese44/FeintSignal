"""Tests for deterministic signal scoring."""
from backend.agents.signal_scorer import compute_source_quality, detect_sensational, score_event


def test_base_score_no_penalties():
    event = {
        "id": "t1",
        "title": "Routine regional update",
        "summary": "",
        "severity": 80,
        "urgency": 60,
        "confidence": 70,
        "relevance": 50,
        "sources": [
            {"source_type": "major_media", "reliability_score": 80, "independence_group": "a"},
            {"source_type": "international_media", "reliability_score": 70, "independence_group": "b"},
        ],
    }
    scored = score_event(event)
    # best 80*.6 + avg 75*.4 + diversity 5 = 83.0
    assert scored["source_quality_score"] == 83.0
    # 24 + 12 + 17.5 + 7.5 + 8.3 = 69.3, no penalties
    assert scored["signal_score"] == 69.3
    assert scored["penalty_total"] == 0.0


def test_penalties_stack_and_clamp_to_zero():
    event = {
        "id": "t2",
        "title": "unconfirmed chatter",
        "summary": "",
        "severity": 40,
        "urgency": 40,
        "confidence": 30,
        "relevance": 40,
        "is_duplicate": True,
        "sources": [{"source_type": "social", "reliability_score": 30, "independence_group": "s"}],
    }
    scored = score_event(event)
    # duplicate 15 + low_confidence 10 + social_only 12 = 37 against base 36.5 -> clamped 0
    assert scored["penalty_total"] == 37.0
    assert scored["signal_score"] == 0.0
    assert scored["social_only"] is True
    assert scored["low_confidence"] is True


def test_sensational_wording_penalised():
    assert detect_sensational("A SHOCKING bombshell claim") is True
    assert detect_sensational("Magnitude 7.1 earthquake strikes coast") is False

    event = {
        "id": "t3",
        "title": "SHOCKING bombshell claim rocks capital",
        "summary": "",
        "severity": 90,
        "urgency": 90,
        "confidence": 90,
        "relevance": 90,
        "sources": [
            {"source_type": "official", "reliability_score": 90, "independence_group": "g"},
            {"source_type": "major_media", "reliability_score": 85, "independence_group": "h"},
        ],
    }
    scored = score_event(event)
    assert scored["sensational"] is True
    # base 90.4 - sensational 5 = 85.4
    assert scored["signal_score"] == 85.4
    assert compute_source_quality(event["sources"]) == 94.0
