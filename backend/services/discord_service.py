"""Discord delivery service.

Hard safety rules:
  * Sending is disabled unless ENABLE_DISCORD_SEND=true AND the target webhook
    env var is configured.
  * Webhook URLs are NEVER returned, logged, or printed.
  * Critical alerts that require human review are blocked from auto-send.
"""
from __future__ import annotations

import os
from typing import Dict, Optional

from ..agents.feintcon_agent import DISCLAIMER
from ..core.config import get_settings

CHANNEL_ENV = {
    "heartbeat": "DISCORD_WEBHOOK_HEARTBEAT",
    "breaking": "DISCORD_WEBHOOK_BREAKING",
    "daily_briefing": "DISCORD_WEBHOOK_DAILY_BRIEFING",
    "system_status": "DISCORD_WEBHOOK_SYSTEM_STATUS",
}


def _webhook_for(channel: str) -> Optional[str]:
    return os.getenv(CHANNEL_ENV.get(channel, ""), "").strip() or None


def build_test_payload(channel: str = "system_status") -> Dict[str, object]:
    settings = get_settings()
    return {
        "channel": channel,
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


def send(payload: Dict[str, object], channel: str = "breaking", *, force: bool = False) -> Dict[str, object]:
    """Attempt to deliver a payload, honouring all safety gates.

    Returns a status dict. Never includes the webhook URL.
    """
    settings = get_settings()
    if not settings.enable_discord_send and not force:
        return {"sent": False, "reason": "discord_send_disabled", "channel": channel}

    if payload.get("requires_human_review"):
        return {"sent": False, "reason": "awaiting_human_review", "channel": channel}

    webhook = _webhook_for(channel)
    if not webhook:
        return {"sent": False, "reason": "webhook_not_configured", "channel": channel}

    try:
        import httpx  # imported lazily so the dependency is optional

        body = {k: v for k, v in payload.items() if k != "channel"}
        resp = httpx.post(webhook, json=body, timeout=10.0)
        return {"sent": resp.status_code < 300, "status_code": resp.status_code, "channel": channel}
    except Exception as exc:  # pragma: no cover - network path, never hit by default
        return {"sent": False, "reason": "delivery_error", "error": type(exc).__name__, "channel": channel}
