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
    assert len(channels) == 32
    assert len({item["channel_name"] for item in channels}) == 32
    assert all(item["channel_id_env_var"] for item in channels)
    assert len({item["channel_id_env_var"] for item in channels}) == 32
    assert "human_review" not in loaded["routes"]
    removed = {"fs-human-review", "fs-escalated", "fs-source-review", "fs-research-queue", "fs-monitoring"}
    assert not removed & {item["channel_name"] for item in channels}
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


def test_critical_alert_routes_directly_to_critical():
    decision = alert_router.evaluate_alert(_critical_event())
    assert decision["alert_level"] == "critical"
    assert decision["channel"] == "fs-critical-alerts"


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


def test_discord_payloads_use_watchtower_identity():
    payload = discord_service.build_test_payload("system_status")
    assert payload["username"] == "Watchtower"
    assert payload["content"].startswith("Watchtower connectivity test")
