"""Print a secret-safe configuration and optional live integration health report."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.core.config import get_settings  # noqa: E402

PROJECT_ENV = {key: str(value or "") for key, value in dotenv_values(ROOT / ".env").items()}


def _project_value(name: str) -> str:
    """Prefer this repository's .env so unrelated host variables cannot collide."""
    return PROJECT_ENV.get(name, os.getenv(name, "")).strip()


def _project_bool(name: str, default: bool = False) -> bool:
    value = _project_value(name)
    return value.lower() in {"1", "true", "yes", "on"} if value else default


def _get(client: httpx.Client, url: str, headers: dict) -> tuple[bool, int | None, object]:
    try:
        response = client.get(url, headers=headers)
        data = response.json() if response.status_code < 300 else None
        return response.status_code < 300, response.status_code, data
    except (httpx.HTTPError, ValueError):
        return False, None, None


def report(live: bool = False) -> dict:
    settings = get_settings()
    try:
        channel_registry = json.loads((settings.config_dir / "discord_channels.json").read_text(encoding="utf-8"))
        channel_env_names = [item.get("channel_id_env_var") for item in channel_registry.get("channels", [])]
        webhook_env_names = [item.get("env_var") for item in channel_registry.get("channels", [])]
    except (OSError, json.JSONDecodeError):
        channel_env_names = []
        webhook_env_names = []
    channel_values = [_project_value(name) for name in channel_env_names if name and _project_value(name)]
    provider = _project_value("LLM_PROVIDER").lower()
    provider_key = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}.get(provider)
    result = {
        "mode": "live" if live else "configuration",
        "llm": {
            "enabled": _project_bool("ENABLE_LLM"),
            "provider": provider or None,
            "provider_ready": bool(_project_bool("ENABLE_LLM") and provider_key and _project_value(provider_key)),
            "anthropic_key_configured": bool(_project_value("ANTHROPIC_API_KEY")),
            "openai_key_configured": bool(_project_value("OPENAI_API_KEY")),
        },
        "discord": {
            "bot_identity_configured": all(_project_value(name) for name in (
                "DISCORD_APPLICATION_ID", "DISCORD_PUBLIC_KEY", "DISCORD_BOT_TOKEN"
            )),
            "server_configured": bool(_project_value("DISCORD_SERVER_ID")),
            "channel_ids_configured": len(channel_values),
            "webhooks_configured": sum(1 for name in webhook_env_names if name and _project_value(name)),
            "sending_enabled": _project_bool("ENABLE_DISCORD_SEND"),
        },
    }
    if not live:
        return result

    with httpx.Client(timeout=15.0) as client:
        anthropic_key = _project_value("ANTHROPIC_API_KEY")
        if anthropic_key:
            ok, status, data = _get(client, "https://api.anthropic.com/v1/models", {
                "x-api-key": anthropic_key, "anthropic-version": "2023-06-01"
            })
            result["llm"]["anthropic_live"] = {
                "model_catalog_ok": ok, "status_code": status,
                "models_visible": len(data.get("data", [])) if isinstance(data, dict) else 0,
            }

        openai_key = _project_value("OPENAI_API_KEY")
        if openai_key:
            ok, status, data = _get(client, "https://api.openai.com/v1/models", {
                "authorization": f"Bearer {openai_key}"
            })
            result["llm"]["openai_live"] = {
                "model_catalog_ok": ok, "status_code": status,
                "models_visible": len(data.get("data", [])) if isinstance(data, dict) else 0,
            }

        bot_token = _project_value("DISCORD_BOT_TOKEN")
        if bot_token:
            headers = {"authorization": f"Bot {bot_token}"}
            identity_ok, identity_status, identity = _get(client, "https://discord.com/api/v10/users/@me", headers)
            guilds_ok, guilds_status, guilds = _get(client, "https://discord.com/api/v10/users/@me/guilds", headers)
            server_id = _project_value("DISCORD_SERVER_ID")
            reachable = 0
            for channel_id in channel_values:
                channel_ok, _, _ = _get(client, f"https://discord.com/api/v10/channels/{channel_id}", headers)
                reachable += int(channel_ok)
            result["discord"]["live"] = {
                "identity_ok": identity_ok,
                "identity_status_code": identity_status,
                "bot_account": bool(isinstance(identity, dict) and identity.get("bot")),
                "guilds_ok": guilds_ok,
                "guilds_status_code": guilds_status,
                "target_server_visible": bool(
                    server_id and isinstance(guilds, list)
                    and any(str(guild.get("id")) == server_id for guild in guilds)
                ),
                "channels_reachable": reachable,
                "channels_checked": len(channel_values),
            }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Perform read-only provider and Discord API checks.")
    args = parser.parse_args()
    result = report(live=args.live)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
