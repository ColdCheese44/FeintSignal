"""Perspective analysis must stay attributed, neutral, and uncertainty-aware."""
from backend.agents.perspective_agent import analyze_event


def test_perspective_analysis_uses_supplied_frames_and_source_balance():
    event = {
        "id": "evt-1",
        "title": "Budget negotiations stall",
        "summary": "Negotiators missed a procedural deadline.",
        "conflicting_reports": False,
        "sources": [
            {"political_lean": "center-left"},
            {"political_lean": "center"},
            {"political_lean": "right"},
        ],
        "political_framing": {
            "left_frame": "Service continuity is at risk.",
            "right_frame": "Spending restraint remains unresolved.",
            "contested_terms": ["shutdown"],
        },
    }
    result = analyze_event(event)
    assert result["what_the_left_says"] == "Service continuity is at risk."
    assert result["what_the_right_says"] == "Spending restraint remains unresolved."
    assert result["source_balance"] == {
        "left": 1, "center": 1, "right": 1, "state_aligned": 0, "unknown": 0, "total": 3
    }
    assert "Contested language" in result["uncertainties"][0]


def test_perspective_analysis_does_not_invent_missing_frames():
    result = analyze_event({"id": "evt-2", "title": "Earthquake", "summary": "Damage assessments continue.", "sources": []})
    assert result["what_the_left_says"].startswith("No explicit")
    assert result["what_the_right_says"].startswith("No explicit")
    assert "Only one source" in result["uncertainties"][0]
    assert "no external AI call" in result["method"]
