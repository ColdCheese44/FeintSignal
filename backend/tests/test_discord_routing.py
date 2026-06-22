"""Discord config, routing, and default-off delivery tests."""
from pathlib import Path

from backend.agents import alert_router
from backend.core import config as config_module
from backend.core.discord_routing import load_discord_config, route_channel
from backend.services import discord_service

ROOT = Path(__file__).resolve().parents[2]


def _source(group: str) -> dict:
    return {
        "name": f"Source {group}",
        "url": f"https://example.org/{group}",
        "published_at": "2026-06-21T00:00:00Z",
        "source_type": "major_media",
        "reliability_score": 85,
        "political_lean": "center",
        "country_of_origin": "X",
        "independence_group": group,
    }


def _critical_event(category: str = "politics") -> dict:
    return {
        "id": "critical-1",
        "title": "Corroborated critical development",
        "category": category,
        "tags": [category],
        "signal_score": 90,
        "confidence_score": 82,
        "is_duplicate": False,
        "is_stale": False,
        "sources": [_source("one"), _source("two")],
    }


def test_config_loads_all_command_center_channels():
    loaded = load_discord_config()
    channels = loaded["channels"]
    assert loaded["bot_name"] == "Watchtower"
    assert len(channels) == 37
    assert len({item["channel_name"] for item in channels}) == 37
    assert all(item["channel_id_env_var"] for item in channels)
    assert len({item["channel_id_env_var"] for item in channels}) == 37
    assert all(item["enabled_by_default"] is False for item in channels)
    assert route_channel("heartbeat")["channel_name"] == "fs-heartbeat-log"


def test_all_configured_environment_fields_exist_in_example():
    keys = {
        line.split("=", 1)[0]
        for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#") and "=" in line
    }
    loaded = load_discord_config()
    expected = {loaded["send_enabled_env_var"], loaded["server_id_env_var"]}
    for item in loaded["channels"]:
        expected.update(value for value in (item.get("env_var"), item.get("channel_id_env_var")) if value)
    assert expected <= keys
    assert "DISCORD_BOT_NAME" in keys


def test_critical_alert_routes_to_critical_when_review_gate_is_off(monkeypatch):
    monkeypatch.setenv("REQUIRE_HUMAN_REVIEW_FOR_CRITICAL", "false")
    config_module._settings = None
    decision = alert_router.evaluate_alert(_critical_event())
    assert decision["alert_level"] == "critical"
    assert decision["requires_human_review"] is False
    assert decision["channel"] == "fs-critical-alerts"
    config_module._settings = None


def test_review_gated_critical_routes_to_human_review(monkeypatch):
    monkeypatch.setenv("REQUIRE_HUMAN_REVIEW_FOR_CRITICAL", "true")
    config_module._settings = None
    decision = alert_router.evaluate_alert(_critical_event("conflict"))
    assert decision["requires_human_review"] is True
    assert decision["channel"] == "fs-human-review"
    config_module._settings = None


def test_discord_send_remains_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_DISCORD_SEND", raising=False)
    monkeypatch.setenv("DISCORD_WEBHOOK_HEARTBEAT", "https://not-called.invalid/webhook")
    config_module._settings = None
    result = discord_service.send({"content": "test"}, channel="heartbeat")
    assert result == {
        "sent": False,
        "reason": "discord_send_disabled",
        "channel": "fs-heartbeat-log",
    }
    config_module._settings = None
