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
        "username": "FeintSignal",
        "content": "FeintSignal connectivity test (no live alert).",
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
    if payload.get("requires_human_review") and target["id"] != route_channel("human_review")["id"]:
        return {"sent": False, "reason": "awaiting_human_review", "channel": channel_name}
    webhook = _webhook_for(target["id"])
    if not webhook:
        return {"sent": False, "reason": "webhook_not_configured", "channel": channel_name}
    try:
        import httpx

        body = {k: v for k, v in payload.items() if k not in {"route", "channel", "requires_human_review"}}
        response = httpx.post(webhook, json=body, timeout=10.0)
        return {"sent": response.status_code < 300, "status_code": response.status_code, "channel": channel_name}
    except Exception as exc:  # pragma: no cover - network path is disabled in tests
        return {"sent": False, "reason": "delivery_error", "error": type(exc).__name__, "channel": channel_name}
