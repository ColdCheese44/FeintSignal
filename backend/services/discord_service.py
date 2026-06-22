"""Discord webhook delivery with default-off capability and review gates."""
from __future__ import annotations

import os
from typing import Dict, Optional

from ..agents.feintcon_agent import DISCLAIMER
from ..core.config import get_settings
from ..core.discord_routing import resolve_channel, route_channel, webhook_channels


def _webhook_for(channel: str) -> Optional[str]:
    try:
        key = resolve_channel(channel).get("env_var")
    except ValueError:
        return None
    if not key:
        return None
    return os.getenv(key, "").strip() or None


def safe_channel_status() -> Dict[str, Dict[str, object]]:
    settings = get_settings()
    return {
        item["id"]: {
            "channel_name": item["channel_name"],
            "webhook_configured": settings.webhook_configured(item["id"]),
        }
        for item in webhook_channels()
    }


def build_test_payload(channel: str = "system_status") -> Dict[str, object]:
    settings = get_settings()
    target = resolve_channel(channel)
    return {
        "route": target["id"],
        "channel": target["channel_name"],
        "username": "Watchtower",
        "content": "Watchtower connectivity test (no live alert).",
        "embeds": [
            {
                "title": "System Status Test",
                "description": "This is a generated test payload. No real alert was triggered.",
                "color": 0x3A6EA5,
                "fields": [
                    {"name": "Env", "value": settings.env, "inline": True},
                    {"name": "Discord send enabled", "value": str(settings.enable_discord_send), "inline": True},
                ],
                "footer": {"text": DISCLAIMER},
            }
        ],
    }


def _embed_payload(route: str, title: str, description: str, fields: list[dict], color: int) -> Dict[str, object]:
    target = route_channel(route)
    return {
        "route": target["id"],
        "channel": target["channel_name"],
        "username": "Watchtower",
        "embeds": [{
            "title": title[:256],
            "description": description[:4096],
            "color": color,
            "fields": fields[:25],
            "footer": {"text": DISCLAIMER},
        }],
    }


def build_heartbeat_payload(run: dict, feintcon: dict) -> Dict[str, object]:
    return _embed_payload(
        "heartbeat",
        "FeintSignal Heartbeat",
        "The local intelligence pipeline completed its scheduled posture check.",
        [
            {"name": "Events", "value": str(run.get("events_processed", 0)), "inline": True},
            {"name": "Alerts", "value": str(run.get("alerts_generated", 0)), "inline": True},
            {"name": "FEINTCON", "value": str(feintcon.get("level", "-")), "inline": True},
        ],
        0x2E7D32,
    )


def build_agent_run_payload(run: dict) -> Dict[str, object]:
    return _embed_payload(
        "agent_runs",
        "Agent Run Complete",
        f"Trigger: {run.get('trigger', 'unknown')}",
        [
            {"name": "Status", "value": str(run.get("status", "unknown")), "inline": True},
            {"name": "Processed", "value": str(run.get("events_processed", 0)), "inline": True},
            {"name": "Duplicates", "value": str(run.get("duplicates", 0)), "inline": True},
        ],
        0x3A6EA5,
    )


def build_daily_briefing_payload(briefing: dict) -> Dict[str, object]:
    top = briefing.get("top_signals") or []
    lines = [f"{index + 1}. {item.get('title')} [{float(item.get('signal_score', 0)):.0f}]" for index, item in enumerate(top[:5])]
    return _embed_payload(
        "daily_briefing",
        f"Daily Intelligence Brief | {briefing.get('briefing_date', '')}",
        str(briefing.get("summary", "")),
        [
            {"name": "Top signals", "value": "\n".join(lines)[:1024] or "No active signals.", "inline": False},
            {"name": "Active signals", "value": str(len(briefing.get("top_signals") or [])), "inline": True},
        ],
        0x4F9FE0,
    )


def build_error_payload(error_name: str, context: str) -> Dict[str, object]:
    return _embed_payload(
        "errors",
        "FeintSignal Operational Error",
        f"{context}: {error_name}",
        [],
        0xE5484D,
    )


def dispatch_pipeline(alerts: list[dict], briefing: dict, run: dict, feintcon: dict) -> Dict[str, object]:
    """Dispatch pipeline outputs through mandatory global and per-route gates."""
    alert_results = []
    for alert in alerts:
        result = send(alert["payload"], channel=str(alert.get("route") or "breaking"))
        alert["sent"] = bool(result.get("sent"))
        alert["delivery"] = result
        alert_results.append(result)

    operational = {
        "heartbeat": send(build_heartbeat_payload(run, feintcon), channel="heartbeat"),
        "agent_run": send(build_agent_run_payload(run), channel="agent_runs"),
    }

    daily_result: Dict[str, object] = {"sent": False, "reason": "already_sent_today", "channel": "fs-daily-brief"}
    try:
        from . import event_service

        briefing_date = str(briefing.get("briefing_date", ""))
        if event_service.get_system_state("discord_daily_brief_date") != briefing_date:
            daily_result = send(build_daily_briefing_payload(briefing), channel="daily_briefing")
            if daily_result.get("sent"):
                event_service.set_system_state("discord_daily_brief_date", briefing_date)
    except Exception as exc:
        daily_result = {"sent": False, "reason": "state_error", "error": type(exc).__name__, "channel": "fs-daily-brief"}

    return {"alerts": alert_results, **operational, "daily_briefing": daily_result}


def send(payload: Dict[str, object], channel: str = "breaking") -> Dict[str, object]:
    """Attempt delivery without ever returning or logging webhook values."""
    settings = get_settings()
    try:
        target = resolve_channel(channel)
    except ValueError:
        return {"sent": False, "reason": "unknown_channel", "channel": channel}
    channel_name = target["channel_name"]
    if not settings.enable_discord_send:
        return {"sent": False, "reason": "discord_send_disabled", "channel": channel_name}
    webhook = _webhook_for(target["id"])
    if not webhook:
        return {"sent": False, "reason": "webhook_not_configured", "channel": channel_name}
    try:
        import httpx

        body = {k: v for k, v in payload.items() if k not in {"route", "channel"}}
        response = httpx.post(webhook, json=body, timeout=10.0)
        return {"sent": response.status_code < 300, "status_code": response.status_code, "channel": channel_name}
    except Exception as exc:  # pragma: no cover - network path is disabled in tests
        return {"sent": False, "reason": "delivery_error", "error": type(exc).__name__, "channel": channel_name}
