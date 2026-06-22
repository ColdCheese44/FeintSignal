"""Load and resolve the non-secret Discord command-center configuration."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Dict, List

from .config import CONFIG_DIR

REQUIRED_CHANNEL_FIELDS = {
    "id", "category", "channel_name", "purpose", "webhook_recommended",
    "bot_channel_id_recommended", "env_var", "placeholder_server_id",
    "placeholder_channel_id", "enabled_by_default",
}


@lru_cache(maxsize=1)
def load_discord_config() -> Dict[str, object]:
    with (CONFIG_DIR / "discord_channels.json").open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    channels = config.get("channels")
    routes = config.get("routes")
    if not isinstance(channels, list) or not isinstance(routes, dict):
        raise ValueError("Discord config must contain channels and routes.")
    seen_ids = set()
    seen_names = set()
    for channel in channels:
        missing = REQUIRED_CHANNEL_FIELDS - set(channel)
        if missing:
            raise ValueError(f"Discord channel is missing fields: {sorted(missing)}")
        if channel["id"] in seen_ids or channel["channel_name"] in seen_names:
            raise ValueError(f"Duplicate Discord channel: {channel['id']}")
        if channel["enabled_by_default"] is not False:
            raise ValueError(f"Discord channel must default disabled: {channel['id']}")
        seen_ids.add(channel["id"])
        seen_names.add(channel["channel_name"])
    unknown_routes = set(routes.values()) - seen_ids
    if unknown_routes:
        raise ValueError(f"Discord routes reference unknown channels: {sorted(unknown_routes)}")
    return config


def channels() -> List[dict]:
    return list(load_discord_config()["channels"])  # type: ignore[arg-type]


def resolve_channel(channel: str) -> dict:
    for item in channels():
        if channel in {item["id"], item["channel_name"]}:
            return item
    raise ValueError(f"Unknown Discord channel route: {channel}")


def route_channel(message_type: str) -> dict:
    routes = load_discord_config()["routes"]
    channel_id = routes.get(message_type)  # type: ignore[union-attr]
    if not channel_id:
        raise ValueError(f"Unknown Discord message type: {message_type}")
    return resolve_channel(channel_id)


def webhook_channels() -> List[dict]:
    return [item for item in channels() if item.get("webhook_recommended")]
