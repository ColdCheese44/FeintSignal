"""Discord endpoints. Sending stays disabled by default; payloads are generated
for inspection without delivery. Webhook URLs are never returned."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..core.config import get_settings
from ..core.schemas import DiscordTestRequest
from ..services import discord_service, event_service

router = APIRouter(tags=["discord"])


@router.post("/discord/test")
def discord_test(body: DiscordTestRequest | None = None):
    settings = get_settings()
    channel = body.channel if body else "system_status"
    dry_run = body.dry_run if body else True

    try:
        payload = discord_service.build_test_payload(channel)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if dry_run or not settings.enable_discord_send:
        return {
            "sent": False,
            "dry_run": True,
            "reason": "discord_send_disabled" if not settings.enable_discord_send else "dry_run_requested",
            "channel": payload["channel"],
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
        "fanout_enabled": settings.enable_discord_fanout,
        "digests_enabled": settings.enable_discord_digests,
        "raw_logs_enabled": settings.enable_discord_raw_logs,
        "bot": {
            "name": settings.discord_bot_name,
            "identity_configured": all(settings.secret_configured(name) for name in (
                "DISCORD_APPLICATION_ID", "DISCORD_PUBLIC_KEY", "DISCORD_BOT_TOKEN"
            )),
            "server_configured": settings.secret_configured("DISCORD_SERVER_ID"),
            "channel_ids_configured": settings.discord_channel_id_count(),
            "runtime": "hybrid_webhook_bot_outbound",
        },
        "channels": discord_service.safe_channel_status(),
        "destinations": discord_service.safe_destination_status(),
        "pending_alerts": [
            {
                "event_id": a["event_id"],
                "alert_level": a["alert_level"],
                "sent": bool(a["sent"]),
            }
            for a in event_service.list_alerts()
        ],
    }
