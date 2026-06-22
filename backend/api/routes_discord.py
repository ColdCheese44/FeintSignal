"""Discord endpoints. Sending stays disabled by default; payloads are generated
for inspection without delivery. Webhook URLs are never returned."""
from __future__ import annotations

from fastapi import APIRouter

from ..core.config import get_settings
from ..core.schemas import DiscordTestRequest
from ..services import discord_service, event_service

router = APIRouter(tags=["discord"])


@router.post("/discord/test")
def discord_test(body: DiscordTestRequest | None = None):
    settings = get_settings()
    channel = body.channel if body else "system_status"
    dry_run = body.dry_run if body else True

    payload = discord_service.build_test_payload(channel)

    if dry_run or not settings.enable_discord_send:
        return {
            "sent": False,
            "dry_run": True,
            "reason": "discord_send_disabled" if not settings.enable_discord_send else "dry_run_requested",
            "channel": channel,
            "webhook_configured": settings.webhook_configured(channel),
            "payload": payload,
        }

    result = discord_service.send(payload, channel=channel)
    return {**result, "dry_run": False, "payload": payload}


@router.get("/discord/status")
def discord_status():
    settings = get_settings()
    return {
        "enable_discord_send": settings.enable_discord_send,
        "channels": {
            c: settings.webhook_configured(c)
            for c in ("heartbeat", "breaking", "daily_briefing", "system_status")
        },
        "pending_alerts": [
            {
                "event_id": a["event_id"],
                "alert_level": a["alert_level"],
                "requires_human_review": bool(a["requires_human_review"]),
                "sent": bool(a["sent"]),
            }
            for a in event_service.list_alerts()
        ],
    }
