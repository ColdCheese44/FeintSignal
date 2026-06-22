"""Pipeline Discord dispatch remains routed, observable, and network-free in tests."""
from types import SimpleNamespace

from backend.core.discord_routing import channels
from backend.services import discord_service


def _settings(**overrides):
    values = {
        "enable_discord_send": True,
        "enable_discord_fanout": False,
        "enable_discord_digests": False,
        "enable_discord_raw_logs": False,
        "discord_max_fanout_per_run": 24,
        "discord_bot_name": "Watchtower",
        "env": "test",
        "enable_live_research": True,
        "enable_llm": True,
        "llm_provider": "anthropic",
        "update_interval_minutes": 60,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _memory_state(initial=None):
    state = dict(initial or {})
    return state, lambda key: state.get(key), lambda key, value: state.__setitem__(key, value)


def test_dispatch_routes_alerts_and_operational_payloads(monkeypatch):
    calls = []

    def fake_send(payload, channel="breaking"):
        calls.append((channel, payload["channel"]))
        return {"sent": False, "reason": "test", "channel": payload["channel"]}

    monkeypatch.setattr(discord_service, "send", fake_send)
    monkeypatch.setattr(discord_service, "get_settings", lambda: _settings())
    _, get_state, set_state = _memory_state()
    monkeypatch.setattr("backend.services.event_service.get_system_state", get_state)
    monkeypatch.setattr("backend.services.event_service.set_system_state", set_state)
    alert = {
        "route": "critical",
        "payload": {"route": "critical", "channel": "fs-critical-alerts", "embeds": []},
    }
    briefing = {
        "briefing_date": "2026-06-22",
        "summary": "Daily summary.",
        "top_signals": [],
    }
    run = {"trigger": "test", "status": "ok", "events_processed": 1, "alerts_generated": 1, "duplicates": 0}
    result = discord_service.dispatch_pipeline([alert], briefing, run, {"level": 3})
    assert [route for route, _ in calls] == [
        "critical", "heartbeat", "agent_runs", "system_status", "command_center",
        "daily_briefing", "sitrep", "bias_framing", "cost_control",
    ]
    assert alert["sent"] is False
    assert result["daily_briefing"]["reason"] == "test"


def test_operational_payloads_use_expected_channel_names():
    run = {"trigger": "hourly", "status": "ok", "events_processed": 11, "alerts_generated": 3, "duplicates": 1}
    assert discord_service.build_heartbeat_payload(run, {"level": 3})["channel"] == "fs-heartbeat-log"
    assert discord_service.build_agent_run_payload(run)["channel"] == "fs-agent-runs"
    assert discord_service.build_error_payload("RuntimeError", "scheduler")["channel"] == "fs-error-log"


def test_should_dispatch_escalation_logic():
    assert discord_service._should_dispatch("standard", None) is True   # new story
    assert discord_service._should_dispatch("standard", "standard") is False  # already alerted
    assert discord_service._should_dispatch("critical", "standard") is True   # escalation
    assert discord_service._should_dispatch("standard", "critical") is False  # de-escalation


def test_dispatch_skips_already_alerted_event(monkeypatch):
    """An event already in the ledger at the same level is not re-posted."""
    sent_channels = []

    def fake_send(payload, channel="breaking"):
        sent_channels.append(channel)
        return {"sent": True, "status_code": 204, "channel": payload["channel"]}

    monkeypatch.setattr(discord_service, "send", fake_send)
    monkeypatch.setattr(discord_service, "get_settings", lambda: _settings())
    monkeypatch.setattr(
        "backend.services.event_service.get_system_state",
        lambda key: {"rss-known": {"level": "critical", "ts": "2026-06-22T00:00:00Z"}} if key == discord_service.ALERT_LEDGER_KEY else None,
    )
    monkeypatch.setattr("backend.services.event_service.set_system_state", lambda *a, **k: None)

    alerts = [
        {"event_id": "rss-known", "alert_level": "critical", "route": "critical", "channel": "fs-critical-alerts",
         "payload": {"route": "critical", "channel": "fs-critical-alerts", "embeds": []}},
        {"event_id": "rss-new", "alert_level": "standard", "route": "breaking", "channel": "fs-breaking-alerts",
         "payload": {"route": "breaking", "channel": "fs-breaking-alerts", "embeds": []}},
    ]
    briefing = {"briefing_date": "2026-06-22", "summary": "s", "top_signals": []}
    run = {"trigger": "test", "status": "ok", "events_processed": 2, "alerts_generated": 2, "duplicates": 0}
    discord_service.dispatch_pipeline(alerts, briefing, run, {"level": 3})

    assert alerts[0]["sent"] is False and alerts[0]["delivery"]["reason"] == "already_dispatched"
    assert alerts[1]["sent"] is True
    assert "breaking" in sent_channels and "critical" not in sent_channels


def test_alert_fanout_uses_region_domain_and_global_for_critical():
    destinations = discord_service.alert_fanout_destinations({
        "route": "critical",
        "alert_level": "critical",
        "region": "Europe",
        "category": "terrorism",
    })
    assert destinations == ["region_europe", "domain_terrorism", "region_global"]


def test_send_prefers_bot_for_non_webhook_destination(monkeypatch):
    calls = []
    monkeypatch.setattr(discord_service, "get_settings", lambda: _settings())
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
    monkeypatch.setenv("DISCORD_CHANNEL_TERRORISM", "123456789")

    def fake_post(url, body, headers, channel_name, transport):
        calls.append((url, body, headers, channel_name, transport))
        return {"sent": True, "status_code": 200, "channel": channel_name, "transport": transport}

    monkeypatch.setattr(discord_service, "_post_discord", fake_post)
    result = discord_service.send(
        {"username": "Watchtower", "content": "test", "embeds": []},
        channel="domain_terrorism",
    )

    assert result["sent"] is True and result["transport"] == "bot"
    assert calls[0][0].endswith("/channels/123456789/messages")
    assert "username" not in calls[0][1]
    assert calls[0][1]["allowed_mentions"] == {"parse": []}
    assert calls[0][2]["Authorization"] == "Bot test-token"


def test_failed_webhook_falls_back_to_bot(monkeypatch):
    calls = []
    monkeypatch.setattr(discord_service, "get_settings", lambda: _settings())
    monkeypatch.setenv("DISCORD_WEBHOOK_SYSTEM_STATUS", "https://example.test/webhook")
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
    monkeypatch.setenv("DISCORD_CHANNEL_SYSTEM_STATUS", "123456789")

    def fake_post(url, body, headers, channel_name, transport):
        calls.append(transport)
        if transport == "webhook":
            return {"sent": False, "status_code": 404, "channel": channel_name, "transport": transport}
        return {"sent": True, "status_code": 200, "channel": channel_name, "transport": transport}

    monkeypatch.setattr(discord_service, "_post_discord", fake_post)
    result = discord_service.send({"content": "test"}, channel="system_status")
    assert calls == ["webhook", "bot"]
    assert result["sent"] is True and result["fallback_from"] == "webhook"


def test_embed_payload_stays_under_discord_character_budget():
    payload = discord_service._embed_payload(
        "bias_framing", "T" * 500, "D" * 5000,
        [{"name": "N" * 300, "value": "V" * 2000} for _ in range(25)], 0x123456,
    )
    embed = payload["embeds"][0]
    total = len(embed["title"]) + len(embed["description"]) + len(embed["footer"]["text"])
    total += sum(len(field["name"]) + len(field["value"]) for field in embed["fields"])
    assert total <= 5800


def test_all_channels_report_bot_delivery_coverage(monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-token")
    for item in channels():
        monkeypatch.setenv(item["channel_id_env_var"], f"id-{item['id']}")
    status = discord_service.safe_destination_status()
    assert len(status) == 32
    assert all(item["delivery_available"] for item in status.values())
    assert status["domain_terrorism"]["preferred_transport"] == "bot"


def test_dispatch_fans_out_and_builds_daily_digests(monkeypatch):
    calls = []
    monkeypatch.setattr(
        discord_service,
        "get_settings",
        lambda: _settings(enable_discord_fanout=True, enable_discord_digests=True, enable_discord_raw_logs=True),
    )

    def fake_send(payload, channel="breaking"):
        calls.append(channel)
        return {"sent": True, "status_code": 200, "channel": payload["channel"], "transport": "test"}

    monkeypatch.setattr(discord_service, "send", fake_send)
    _, get_state, set_state = _memory_state()
    monkeypatch.setattr("backend.services.event_service.get_system_state", get_state)
    monkeypatch.setattr("backend.services.event_service.set_system_state", set_state)

    event = {
        "id": "evt-1", "title": "Security incident", "summary": "Summary",
        "region": "Europe", "category": "terrorism", "signal_score": 90,
        "confidence_score": 85, "alert_level": "critical", "is_duplicate": False,
    }
    alert = {
        **event, "event_id": "evt-1", "route": "critical", "channel": "fs-critical-alerts",
        "payload": {"route": "critical", "channel": "fs-critical-alerts", "embeds": []},
    }
    briefing = {
        "briefing_date": "2026-06-22", "summary": "Daily summary", "headline": "Headline",
        "top_signals": [], "perspective_analysis": [], "llm_analysis": {},
    }
    run = {"trigger": "test", "status": "ok", "events_processed": 1, "alerts_generated": 1, "duplicates": 0}
    result = discord_service.dispatch_pipeline([alert], briefing, run, {"level": 2}, events=[event])

    assert {"critical", "region_europe", "domain_terrorism", "region_global"} <= set(calls)
    assert "raw_logs" in calls
    assert set(result["digests"]) == {"region_europe", "domain_terrorism", "region_global"}
    assert len(result["alert_fanout"]) == 3
    summary = discord_service.summarize_dispatch(result)
    assert summary["sent"] == summary["attempted"]
    assert summary["transports"] == {"test": summary["sent"]}
