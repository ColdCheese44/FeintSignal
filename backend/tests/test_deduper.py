"""Tests for duplicate / near-duplicate detection."""
from backend.agents.deduper import mark_duplicates


def test_near_duplicate_is_flagged_lower_confidence_loses():
    events = [
        {
            "id": "A",
            "title": "Cross-border strikes reported along contested frontier",
            "region": "Middle East",
            "category": "conflict",
            "confidence": 72,
            "severity": 90,
            "tags": ["conflict", "frontier"],
        },
        {
            "id": "B",
            "title": "Unverified posts claim large blasts along contested frontier",
            "region": "Middle East",
            "category": "conflict",
            "confidence": 35,
            "severity": 40,
            "tags": ["conflict", "frontier", "rumor"],
        },
    ]
    result = {e["id"]: e for e in mark_duplicates(events)}
    assert result["A"]["is_duplicate"] is False
    assert result["B"]["is_duplicate"] is True
    assert result["B"]["duplicate_of"] == "A"


def test_distinct_events_not_merged():
    events = [
        {"id": "C", "title": "Cyber intrusion hits grid operator", "region": "North America", "category": "cyber", "confidence": 78, "severity": 85},
        {"id": "D", "title": "Coalition talks collapse before election", "region": "Europe", "category": "politics", "confidence": 80, "severity": 45},
    ]
    result = {e["id"]: e for e in mark_duplicates(events)}
    assert result["C"]["is_duplicate"] is False
    assert result["D"]["is_duplicate"] is False
