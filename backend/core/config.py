"""Runtime configuration for FeintSignal.

All capability gates default to OFF. The system is fully functional on mock data
without any external services, API keys, or network access.

Secrets are never logged or printed. ``Settings.safe_summary`` deliberately omits
webhook URLs and API keys.
"""
from __future__ import annotations

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
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", ""))

    enable_discord_send: bool = field(default_factory=lambda: _as_bool(os.getenv("ENABLE_DISCORD_SEND"), False))
    require_human_review_for_critical: bool = field(
        default_factory=lambda: _as_bool(os.getenv("REQUIRE_HUMAN_REVIEW_FOR_CRITICAL"), True)
    )

    update_interval_minutes: int = field(default_factory=lambda: _as_int(os.getenv("UPDATE_INTERVAL_MINUTES"), 60))
    max_events_per_run: int = field(default_factory=lambda: _as_int(os.getenv("MAX_EVENTS_PER_RUN"), 50))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Derived paths
    db_path: Path = field(default_factory=lambda: DATA_DIR / "feintsignal.db")
    config_dir: Path = CONFIG_DIR
    data_dir: Path = DATA_DIR

    def webhook_configured(self, channel: str) -> bool:
        """Return whether a webhook env var is set, WITHOUT revealing the value."""
        key = {
            "heartbeat": "DISCORD_WEBHOOK_HEARTBEAT",
            "breaking": "DISCORD_WEBHOOK_BREAKING",
            "daily_briefing": "DISCORD_WEBHOOK_DAILY_BRIEFING",
            "system_status": "DISCORD_WEBHOOK_SYSTEM_STATUS",
        }.get(channel)
        if not key:
            return False
        return bool(os.getenv(key, "").strip())

    def configured_webhook_channels(self) -> List[str]:
        return [c for c in ("heartbeat", "breaking", "daily_briefing", "system_status") if self.webhook_configured(c)]

    def safe_summary(self) -> Dict[str, object]:
        """Non-sensitive view of config for the API/UI. No secrets, no URLs."""
        return {
            "env": self.env,
            "backend": f"{self.backend_host}:{self.backend_port}",
            "frontend_port": self.frontend_port,
            "enable_live_research": self.enable_live_research,
            "enable_llm": self.enable_llm,
            "llm_provider": self.llm_provider or None,
            "enable_discord_send": self.enable_discord_send,
            "require_human_review_for_critical": self.require_human_review_for_critical,
            "update_interval_minutes": self.update_interval_minutes,
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
