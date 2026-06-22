"""Runtime configuration for FeintSignal.

All capability gates default to OFF. The system is fully functional on mock data
without any external services, API keys, or network access.

Secrets are never logged or printed. ``Settings.safe_summary`` deliberately omits
webhook URLs and API keys.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

try:  # python-dotenv is optional at runtime; absence must not break startup.
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - defensive
    def load_dotenv(*_args, **_kwargs):  # type: ignore
        return False


# Repo layout: backend/core/config.py -> repo root is two parents up.
REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"
DATA_DIR = REPO_ROOT / "data"
LOGS_DIR = REPO_ROOT / "logs"

# Load .env if present (local only). Values already in the environment win.
load_dotenv(REPO_ROOT / ".env", override=False)


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    env: str = field(default_factory=lambda: os.getenv("FEINTSIGNAL_ENV", "local"))
    backend_host: str = field(default_factory=lambda: os.getenv("BACKEND_HOST", "127.0.0.1"))
    backend_port: int = field(default_factory=lambda: _as_int(os.getenv("BACKEND_PORT"), 8765))
    frontend_port: int = field(default_factory=lambda: _as_int(os.getenv("FRONTEND_PORT"), 5173))

    enable_live_research: bool = field(default_factory=lambda: _as_bool(os.getenv("ENABLE_LIVE_RESEARCH"), False))
    enable_llm: bool = field(default_factory=lambda: _as_bool(os.getenv("ENABLE_LLM"), False))
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "").strip().lower())
    anthropic_model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6").strip())
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-5-mini").strip())
    llm_max_events: int = field(default_factory=lambda: _as_int(os.getenv("LLM_MAX_EVENTS"), 3))
    llm_max_output_tokens: int = field(default_factory=lambda: _as_int(os.getenv("LLM_MAX_OUTPUT_TOKENS"), 1800))
    llm_timeout_seconds: int = field(default_factory=lambda: _as_int(os.getenv("LLM_TIMEOUT_SECONDS"), 45))

    enable_discord_send: bool = field(default_factory=lambda: _as_bool(os.getenv("ENABLE_DISCORD_SEND"), False))
    discord_bot_name: str = field(default_factory=lambda: os.getenv("DISCORD_BOT_NAME", "Watchtower").strip() or "Watchtower")

    update_interval_minutes: int = field(default_factory=lambda: _as_int(os.getenv("UPDATE_INTERVAL_MINUTES"), 60))
    enable_scheduler: bool = field(default_factory=lambda: _as_bool(os.getenv("ENABLE_SCHEDULER"), False))
    max_events_per_run: int = field(default_factory=lambda: _as_int(os.getenv("MAX_EVENTS_PER_RUN"), 50))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Derived paths
    db_path: Path = field(default_factory=lambda: DATA_DIR / "feintsignal.db")
    config_dir: Path = CONFIG_DIR
    data_dir: Path = DATA_DIR

    def webhook_configured(self, channel: str) -> bool:
        """Return whether a webhook env var is set, WITHOUT revealing the value."""
        from .discord_routing import resolve_channel

        try:
            key = resolve_channel(channel).get("env_var")
        except ValueError:
            return False
        if not key:
            return False
        return bool(os.getenv(key, "").strip())

    def configured_webhook_channels(self) -> List[str]:
        from .discord_routing import webhook_channels

        return [item["id"] for item in webhook_channels() if self.webhook_configured(item["id"])]

    @staticmethod
    def secret_configured(name: str) -> bool:
        """Report whether a secret exists without returning any part of it."""
        return bool(os.getenv(name, "").strip())

    def llm_provider_ready(self) -> bool:
        key_names = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}
        key_name = key_names.get(self.llm_provider)
        return bool(self.enable_llm and key_name and self.secret_configured(key_name))

    def discord_channel_id_count(self) -> int:
        try:
            registry = json.loads((self.config_dir / "discord_channels.json").read_text(encoding="utf-8"))
            names = [item.get("channel_id_env_var") for item in registry.get("channels", [])]
        except (OSError, json.JSONDecodeError):
            names = []
        return sum(1 for name in names if name and os.getenv(name, "").strip())

    def safe_summary(self) -> Dict[str, object]:
        """Non-sensitive view of config for the API/UI. No secrets, no URLs."""
        return {
            "env": self.env,
            "backend": f"{self.backend_host}:{self.backend_port}",
            "frontend_port": self.frontend_port,
            "enable_live_research": self.enable_live_research,
            "enable_llm": self.enable_llm,
            "llm_provider": self.llm_provider or None,
            "llm_provider_ready": self.llm_provider_ready(),
            "llm_model": (
                self.anthropic_model if self.llm_provider == "anthropic"
                else self.openai_model if self.llm_provider == "openai"
                else None
            ),
            "llm_max_events": max(1, min(self.llm_max_events, 5)),
            "openai_key_configured": self.secret_configured("OPENAI_API_KEY"),
            "anthropic_key_configured": self.secret_configured("ANTHROPIC_API_KEY"),
            "enable_discord_send": self.enable_discord_send,
            "update_interval_minutes": self.update_interval_minutes,
            "enable_scheduler": self.enable_scheduler,
            "max_events_per_run": self.max_events_per_run,
            "log_level": self.log_level,
            "discord_webhooks_configured": self.configured_webhook_channels(),
        }


_settings: Settings | None = None


def get_settings() -> Settings:
    """Process-wide settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
