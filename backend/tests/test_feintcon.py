"""Tests for FEINTCON readiness computation."""
from backend.agents.feintcon_agent import compute_feintcon


def test_normal_monitoring_is_level_5():
    events = [
        {"id": "a", "signal_score": 40, "confidence_score": 70, "region": "Europe"},
        {"id": "b", "signal_score": 30, "confidence_score": 60, "region": "Africa"},
    ]
    status = compute_feintcon(events)
    assert status["level"] == 5
    assert status["is_official_defcon"] is False
    assert "not an official" in status["disclaimer"].lower()


def test_one_critical_drives_level_3():
    events = [
        {"id": "crit", "signal_score": 90, "confidence_score": 80, "region": "Middle East", "is_stale": False},
        {"id": "hi1", "signal_score": 78, "confidence_score": 70, "region": "North America"},
        {"id": "hi2", "signal_score": 80, "confidence_score": 75, "region": "Asia-Pacific"},
    ]
    status = compute_feintcon(events)
    assert status["level"] == 3
    assert status["metrics"]["critical_events"] == 1
    assert status["metrics"]["region_count"] == 3
