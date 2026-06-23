"""LLM enrichment must remain evidence-bound and fail closed to deterministic output."""
from types import SimpleNamespace

from backend.services import llm_service


def _settings(**overrides):
    values = {
        "enable_llm": True,
        "llm_provider": "anthropic",
        "anthropic_model": "claude-sonnet-4-6",
        "openai_model": "gpt-5-mini",
        "llm_max_events": 3,
        "llm_max_output_tokens": 1800,
        "llm_timeout_seconds": 45,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _event():
    return {
        "id": "evt-1",
        "title": "Negotiations continue",
        "summary": "Officials reported that talks continued on Monday.",
        "region": "Europe",
        "category": "politics",
        "signal_score": 82,
        "confidence_score": 76,
        "is_duplicate": False,
        "sources": [{
            "name": "Example News",
            "url": "https://example.test/report",
            "source_type": "major_media",
            "political_lean": "center",
        }],
    }


def _briefing():
    return {
        "perspective_analysis": [{
            "event_id": "evt-1",
            "title": "Negotiations continue",
            "neutral_assessment": "Baseline",
            "what_the_left_says": "No explicit left frame.",
            "what_the_center_says": "One center source.",
            "what_the_right_says": "No explicit right frame.",
            "consensus": "Talks continued.",
            "uncertainties": ["Only one source."],
            "source_balance": {"center": 1, "total": 1},
            "method": "Deterministic.",
        }],
        "intelligence_method": "Deterministic synthesis.",
    }


def test_anthropic_enrichment_maps_only_known_citations(monkeypatch):
    provider_result = {
        "analyses": [{
            "event_id": "evt-1",
            "neutral_assessment": "Talks were reported as continuing.",
            "what_the_left_says": "No distinct left evidence was supplied.",
            "what_the_center_says": "The supplied report emphasizes process.",
            "what_the_right_says": "No distinct right evidence was supplied.",
            "consensus": "The talks continued according to the supplied report.",
            "uncertainties": ["Independent corroboration was not supplied."],
            "evidence_citations": ["S1", "S99"],
        }]
    }
    monkeypatch.setattr(llm_service, "_request_anthropic", lambda _prompt, _settings, _count: (provider_result, {
        "input_tokens": 100, "output_tokens": 50
    }))

    result = llm_service.enrich_briefing(_briefing(), [_event()], _settings())

    analysis = result["perspective_analysis"][0]
    assert analysis["ai_generated"] is True
    assert analysis["evidence_citations"] == [{
        "id": "S1", "label": "Example News", "url": "https://example.test/report"
    }]
    assert result["llm_analysis"]["status"] == "ok"
    assert result["llm_analysis"]["usage"] == {"input_tokens": 100, "output_tokens": 50}


def test_provider_failure_preserves_deterministic_analysis(monkeypatch):
    def fail(_prompt, _settings, _count):
        raise llm_service.LLMServiceError("anthropic_http_429")

    monkeypatch.setattr(llm_service, "_request_anthropic", fail)
    briefing = _briefing()
    result = llm_service.enrich_briefing(briefing, [_event()], _settings())

    assert result["perspective_analysis"][0]["neutral_assessment"] == "Baseline"
    assert result["llm_analysis"]["status"] == "fallback"
    assert result["llm_analysis"]["reason"] == "anthropic_http_429"


def test_unsupported_provider_never_attempts_a_request():
    result = llm_service.enrich_briefing(_briefing(), [_event()], _settings(llm_provider="dual"))
    assert result["llm_analysis"]["status"] == "fallback"
    assert result["llm_analysis"]["reason"] == "unsupported_provider"


def test_json_parser_accepts_fenced_provider_output():
    assert llm_service._parse_json_text("```json\n{\"analyses\": []}\n```") == {"analyses": []}


def test_non_http_source_url_is_not_exposed_as_a_citation(monkeypatch):
    event = _event()
    event["sources"][0]["url"] = "javascript:alert(1)"
    provider_result = {"analyses": [{
        "event_id": "evt-1",
        "neutral_assessment": "Assessment",
        "what_the_left_says": "No evidence.",
        "what_the_center_says": "No evidence.",
        "what_the_right_says": "No evidence.",
        "consensus": "Consensus",
        "uncertainties": ["Limited evidence."],
        "evidence_citations": ["S1"],
    }]}
    monkeypatch.setattr(llm_service, "_request_anthropic", lambda _prompt, _settings, _count: (provider_result, {}))
    result = llm_service.enrich_briefing(_briefing(), [event], _settings())
    assert result["perspective_analysis"][0]["evidence_citations"] == []


def test_unexpected_provider_error_is_sanitized_and_falls_back(monkeypatch):
    monkeypatch.setattr(
        llm_service,
        "_request_anthropic",
        lambda _prompt, _settings, _count: (_ for _ in ()).throw(TypeError("sensitive provider detail")),
    )
    result = llm_service.enrich_briefing(_briefing(), [_event()], _settings())
    assert result["llm_analysis"]["reason"] == "anthropic_internal_TypeError"
    assert "sensitive provider detail" not in result["intelligence_method"]
