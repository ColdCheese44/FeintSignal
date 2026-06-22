"""Tests for source validation."""
from backend.agents.source_validator import validate_event_sources, validate_source


def _valid_source(**overrides):
    base = {
        "name": "Sentinel News Wire",
        "url": "https://example.org/sentinel",
        "published_at": "2026-06-21T00:00:00Z",
        "source_type": "major_media",
        "reliability_score": 80,
        "political_lean": "center",
        "country_of_origin": "Multinational",
        "independence_group": "wire-alpha",
    }
    base.update(overrides)
    return base


def test_valid_source_passes():
    ok, issues = validate_source(_valid_source())
    assert ok is True
    assert issues == []


def test_invalid_source_is_flagged():
    bad = _valid_source(url="", source_type="blog", reliability_score=150)
    ok, issues = validate_source(bad)
    assert ok is False
    assert "missing:url" in issues
    assert "invalid_source_type:blog" in issues
    assert "reliability_out_of_range" in issues


def test_event_source_summary_counts_independence_and_official():
    event = {
        "sources": [
            _valid_source(source_type="official", reliability_score=88, independence_group="gov"),
            _valid_source(source_type="international_media", reliability_score=80, independence_group="wire"),
        ]
    }
    summary = validate_event_sources(event)
    assert summary["independent_source_count"] == 2
    assert summary["has_official_source"] is True
    assert summary["meets_min_reliability"] is True
