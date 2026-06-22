"""Pipeline Discord dispatch remains routed, observable, and network-free in tests."""
from backend.services import discord_service


def test_dispatch_routes_alerts_and_operational_payloads(monkeypatch):
    calls = []

    def fake_send(payload, channel="breaking"):
        calls.append((channel, payload["channel"]))
        return {"sent": False, "reason": "test", "channel": payload["channel"]}

    monkeypatch.setattr(discord_service, "send", fake_send)
    monkeypatch.setattr("backend.services.event_service.get_system_state", lambda key: None)
    alert = {
        "route": "critical",
        "payload": {"route": "critical", "channel": "fs-critical-alerts", "embeds": []},
    }
    briefing = {
        "briefing_date": "2026-06-22",
        "summary": "Daily summary.",
        "top_signals": [],
        "human_review_queue": [],
    }
    run = {"trigger": "test", "status": "ok", "events_processed": 1, "alerts_generated": 1, "duplicates": 0}
    result = discord_service.dispatch_pipeline([alert], briefing, run, {"level": 3})
    assert [route for route, _ in calls] == ["critical", "heartbeat", "agent_runs", "daily_briefing"]
    assert alert["sent"] is False
    assert result["daily_briefing"]["reason"] == "test"


def test_operational_payloads_use_expected_channel_names():
    run = {"trigger": "hourly", "status": "ok", "events_processed": 11, "alerts_generated": 3, "duplicates": 1}
    assert discord_service.build_heartbeat_payload(run, {"level": 3})["channel"] == "fs-heartbeat-log"
    assert discord_service.build_agent_run_payload(run)["channel"] == "fs-agent-runs"
    assert discord_service.build_error_payload("RuntimeError", "scheduler")["channel"] == "fs-error-log"
