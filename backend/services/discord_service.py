"""Discord dissemination through webhooks and Watchtower bot-channel delivery.

Every outbound path is controlled by ``ENABLE_DISCORD_SEND``. Webhooks remain
preferred for the nine operational routes; Watchtower's bot token and channel
IDs provide delivery for the rest of the command-center topology. No credential,
webhook URL, channel ID, or Discord response body is returned or logged.
"""
from __future__ import annotations

import copy
import os
import time
from collections import defaultdict
from datetime import timedelta
from typing import Dict, Iterable, Optional

from ..agents.feintcon_agent import DISCLAIMER
from ..core.config import get_settings
from ..core.discord_routing import (
    channels,
    domain_channel,
    region_channel,
    resolve_channel,
    route_channel,
    webhook_channels,
)
from ..core.time_utils import now_iso, now_utc, parse_iso

LEVEL_RANK = {"none": 0, "standard": 1, "critical": 2}
ALERT_LEDGER_KEY = "discord_alert_ledger"
ALERT_LEDGER_TTL_DAYS = 7


def _should_dispatch(level: str, prev_level: Optional[str]) -> bool:
    """Return whether an alert outranks the level already sent to a destination."""
    return LEVEL_RANK.get(str(level), 0) > LEVEL_RANK.get(str(prev_level or "none"), 0)


def _prune_alert_ledger(ledger: dict) -> dict:
    cutoff = now_utc() - timedelta(days=ALERT_LEDGER_TTL_DAYS)
    pruned = {}
    for event_id, record in ledger.items():
        ts = parse_iso(record.get("ts")) if isinstance(record, dict) else None
        if ts is None or ts >= cutoff:
            pruned[event_id] = record
    return pruned


def _webhook_for(channel: str) -> Optional[str]:
    try:
        key = resolve_channel(channel).get("env_var")
    except ValueError:
        return None
    return (os.getenv(key, "").strip() or None) if key else None


def _bot_channel_for(channel: str) -> Optional[str]:
    try:
        key = resolve_channel(channel).get("channel_id_env_var")
    except ValueError:
        return None
    return (os.getenv(key, "").strip() or None) if key else None


def _bot_token() -> Optional[str]:
    return os.getenv("DISCORD_BOT_TOKEN", "").strip() or None


def safe_channel_status() -> Dict[str, Dict[str, object]]:
    """Legacy nine-webhook status contract used by the dashboard."""
    settings = get_settings()
    return {
        item["id"]: {
            "channel_name": item["channel_name"],
            "webhook_configured": settings.webhook_configured(item["id"]),
        }
        for item in webhook_channels()
    }


def safe_destination_status() -> Dict[str, Dict[str, object]]:
    """Report secret-free delivery readiness for all 32 Discord destinations."""
    token_ready = bool(_bot_token())
    result = {}
    for item in channels():
        webhook_ready = bool(_webhook_for(item["id"]))
        bot_channel_ready = bool(_bot_channel_for(item["id"]))
        bot_ready = token_ready and bot_channel_ready
        result[item["id"]] = {
            "channel_name": item["channel_name"],
            "category": item["category"],
            "webhook_configured": webhook_ready,
            "bot_channel_configured": bot_channel_ready,
            "delivery_available": webhook_ready or bot_ready,
            "preferred_transport": "webhook" if webhook_ready else "bot" if bot_ready else None,
        }
    return result


def build_test_payload(channel: str = "system_status") -> Dict[str, object]:
    settings = get_settings()
    target = resolve_channel(channel)
    return {
        "route": target["id"],
        "channel": target["channel_name"],
        "username": settings.discord_bot_name,
        "content": "Watchtower connectivity test (no live alert).",
        "embeds": [{
            "title": "System Status Test",
            "description": "Generated connectivity test. No real alert was triggered.",
            "color": 0x3A6EA5,
            "fields": [
                {"name": "Environment", "value": settings.env, "inline": True},
                {"name": "Discord send", "value": str(settings.enable_discord_send), "inline": True},
            ],
            "footer": {"text": DISCLAIMER},
        }],
    }


def _clean_fields(fields: Iterable[dict], budget: int) -> list[dict]:
    cleaned = []
    remaining = max(0, budget)
    for field in list(fields)[:25]:
        name = str(field.get("name", "-"))[:256]
        available = min(1024, remaining - len(name))
        if available <= 0:
            break
        value = str(field.get("value", "-"))[:available]
        cleaned.append({"name": name, "value": value, "inline": bool(field.get("inline", False))})
        remaining -= len(name) + len(value)
    return cleaned


def _embed_for_target(target: dict, title: str, description: str, fields: list[dict], color: int) -> Dict[str, object]:
    clean_title = str(title)[:256]
    footer = DISCLAIMER[:2048]
    clean_description = str(description)[: min(3500, max(0, 5800 - len(clean_title) - len(footer)))]
    field_budget = 5800 - len(clean_title) - len(clean_description) - len(footer)
    return {
        "route": target["id"],
        "channel": target["channel_name"],
        "username": get_settings().discord_bot_name,
        "embeds": [{
            "title": clean_title,
            "description": clean_description,
            "color": color,
            "fields": _clean_fields(fields, field_budget),
            "footer": {"text": footer},
            "timestamp": now_iso(),
        }],
    }


def _embed_payload(route: str, title: str, description: str, fields: list[dict], color: int) -> Dict[str, object]:
    return _embed_for_target(route_channel(route), title, description, fields, color)


def build_heartbeat_payload(run: dict, feintcon: dict) -> Dict[str, object]:
    return _embed_payload(
        "heartbeat", "FeintSignal Heartbeat",
        "The intelligence pipeline completed its scheduled posture check.",
        [
            {"name": "Events", "value": run.get("events_processed", 0), "inline": True},
            {"name": "Alerts", "value": run.get("alerts_generated", 0), "inline": True},
            {"name": "FEINTCON", "value": feintcon.get("level", "-"), "inline": True},
        ],
        0x2E7D32,
    )


def build_agent_run_payload(run: dict) -> Dict[str, object]:
    return _embed_payload(
        "agent_runs", "Agent Run Complete", f"Trigger: {run.get('trigger', 'unknown')}",
        [
            {"name": "Status", "value": run.get("status", "unknown"), "inline": True},
            {"name": "Processed", "value": run.get("events_processed", 0), "inline": True},
            {"name": "Duplicates", "value": run.get("duplicates", 0), "inline": True},
        ],
        0x3A6EA5,
    )


def build_system_status_payload(run: dict, feintcon: dict) -> Dict[str, object]:
    settings = get_settings()
    return _embed_payload(
        "system_status", "Watchtower System Status", "Current FeintSignal runtime posture.",
        [
            {"name": "Pipeline", "value": run.get("status", "unknown"), "inline": True},
            {"name": "FEINTCON", "value": feintcon.get("level", "-"), "inline": True},
            {"name": "Live research", "value": "ON" if settings.enable_live_research else "OFF", "inline": True},
            {"name": "LLM", "value": settings.llm_provider if settings.enable_llm else "OFF", "inline": True},
            {"name": "Fanout", "value": "ON" if settings.enable_discord_fanout else "OFF", "inline": True},
            {"name": "Digests", "value": "ON" if settings.enable_discord_digests else "OFF", "inline": True},
        ],
        0x3A6EA5,
    )


def build_daily_briefing_payload(briefing: dict) -> Dict[str, object]:
    top = briefing.get("top_signals") or []
    lines = [f"{index + 1}. {item.get('title')} [{float(item.get('signal_score', 0)):.0f}]" for index, item in enumerate(top[:5])]
    llm = briefing.get("llm_analysis") or {}
    return _embed_payload(
        "daily_briefing", f"Daily Intelligence Brief | {briefing.get('briefing_date', '')}",
        str(briefing.get("summary", "")),
        [
            {"name": "Top signals", "value": "\n".join(lines) or "No active signals."},
            {"name": "AI synthesis", "value": f"{llm.get('status', 'deterministic')} ({llm.get('events_enriched', 0)}/{llm.get('events_requested', 0)})", "inline": True},
        ],
        0x4F9FE0,
    )


def build_command_center_payload(briefing: dict, run: dict, feintcon: dict) -> Dict[str, object]:
    return _embed_payload(
        "command_center", "Watchtower Command Summary", str(briefing.get("headline") or briefing.get("summary") or "No headline."),
        [
            {"name": "FEINTCON", "value": feintcon.get("level", "-"), "inline": True},
            {"name": "Active events", "value": run.get("events_processed", 0), "inline": True},
            {"name": "Alerts", "value": run.get("alerts_generated", 0), "inline": True},
            {"name": "Next cadence", "value": f"{get_settings().update_interval_minutes} minutes", "inline": True},
        ],
        0x6B8EDE,
    )


def build_sitrep_payload(briefing: dict, feintcon: dict) -> Dict[str, object]:
    top = briefing.get("top_signals") or []
    lines = [f"- {item.get('title')} ({item.get('region')}, {item.get('category')})" for item in top[:5]]
    try:
        level = int(feintcon.get("level", 5) or 5)
    except (TypeError, ValueError):
        level = 5
    return _embed_payload(
        "sitrep", f"SITREP | FEINTCON {feintcon.get('level', '-')}", str(briefing.get("summary", "")),
        [{"name": "Priority signals", "value": "\n".join(lines) or "No active signals."}],
        0xE0A317 if level <= 3 else 0x3A6EA5,
    )


def build_bias_payload(briefing: dict) -> Dict[str, object]:
    analyses = briefing.get("perspective_analysis") or []
    analysis = analyses[0] if analyses else {}
    return _embed_payload(
        "bias_framing", "Perspective & Framing Brief", str(analysis.get("title") or "No priority framing item."),
        [
            {"name": "Neutral assessment", "value": analysis.get("neutral_assessment", "Unavailable")},
            {"name": "Left framing", "value": analysis.get("what_the_left_says", "Unavailable")},
            {"name": "Center framing", "value": analysis.get("what_the_center_says", "Unavailable")},
            {"name": "Right framing", "value": analysis.get("what_the_right_says", "Unavailable")},
            {"name": "Consensus", "value": analysis.get("consensus", "Unavailable")},
        ],
        0x8A63D2,
    )


def build_cost_payload(briefing: dict) -> Dict[str, object]:
    llm = briefing.get("llm_analysis") or {}
    usage = llm.get("usage") or {}
    return _embed_payload(
        "cost_control", "AI Usage & Cost Control", "Provider usage recorded for this briefing cycle.",
        [
            {"name": "Provider", "value": llm.get("provider") or "deterministic", "inline": True},
            {"name": "Model", "value": llm.get("model") or "none", "inline": True},
            {"name": "Status", "value": llm.get("status") or "disabled", "inline": True},
            {"name": "Input tokens", "value": usage.get("input_tokens", 0), "inline": True},
            {"name": "Output tokens", "value": usage.get("output_tokens", 0), "inline": True},
        ],
        0x8A6D3B,
    )


def build_raw_log_payload(run: dict, feintcon: dict) -> Dict[str, object]:
    return _embed_payload(
        "raw_logs", "Pipeline Telemetry", "Compact machine-readable run telemetry.",
        [{"name": "Record", "value": str({
            "trigger": run.get("trigger"), "status": run.get("status"),
            "events": run.get("events_processed"), "duplicates": run.get("duplicates"),
            "alerts": run.get("alerts_generated"), "feintcon": feintcon.get("level"),
        })}],
        0x596273,
    )


def build_error_payload(error_name: str, context: str, route: str = "errors") -> Dict[str, object]:
    return _embed_payload(route, "FeintSignal Operational Error", f"{context}: {error_name}", [], 0xE5484D)


def build_digest_payload(destination: str, label: str, events: list[dict], briefing_date: str) -> Dict[str, object]:
    target = resolve_channel(destination)
    active = sorted(
        [event for event in events if not event.get("is_duplicate")],
        key=lambda event: float(event.get("signal_score", 0)),
        reverse=True,
    )
    lines = [
        f"{index + 1}. {event.get('title')} [{float(event.get('signal_score', 0)):.0f}]"
        for index, event in enumerate(active[:5])
    ]
    alerts = sum(event.get("alert_level") in {"standard", "critical"} for event in active)
    return _embed_for_target(
        target, f"{label} Daily Digest | {briefing_date}",
        f"{len(active)} active signal(s); {alerts} alert-qualified.",
        [{"name": "Priority signals", "value": "\n".join(lines) or "No active signals."}],
        0x4F9FE0,
    )


def _copy_payload_for(payload: dict, destination: str) -> dict:
    target = resolve_channel(destination)
    copied = copy.deepcopy(payload)
    copied["route"] = target["id"]
    copied["channel"] = target["channel_name"]
    return copied


def alert_fanout_destinations(alert: dict) -> list[str]:
    """Resolve unique secondary destinations for one alert."""
    destinations = []
    region = region_channel(str(alert.get("region") or ""))
    domain = domain_channel(str(alert.get("category") or ""))
    for target in (region, domain):
        if target:
            destinations.append(target["id"])
    if str(alert.get("alert_level")) == "critical":
        destinations.append(route_channel("global")["id"])
    primary = str(alert.get("route") or "breaking")
    return list(dict.fromkeys(destination for destination in destinations if destination != primary))


def _previous_level(ledger: dict, event_id: str, destination: str, primary: bool = False) -> Optional[str]:
    record = ledger.get(event_id)
    if not isinstance(record, dict):
        return None
    destinations = record.get("destinations")
    if isinstance(destinations, dict) and isinstance(destinations.get(destination), dict):
        return destinations[destination].get("level")
    return record.get("level") if primary else None


def _mark_dispatched(ledger: dict, event_id: str, destination: str, level: str, primary: bool = False) -> None:
    record = ledger.setdefault(event_id, {"destinations": {}})
    if not isinstance(record.get("destinations"), dict):
        record["destinations"] = {}
    stamp = now_iso()
    record["destinations"][destination] = {"level": level, "ts": stamp}
    record["ts"] = stamp
    if primary:
        record["level"] = level


def _state_send_once(event_service, state_key: str, state_value: str, payload: dict, channel: str) -> dict:
    try:
        if event_service.get_system_state(state_key) == state_value:
            return {"sent": False, "reason": "already_sent", "channel": resolve_channel(channel)["channel_name"]}
        result = send(payload, channel=channel)
        if result.get("sent"):
            event_service.set_system_state(state_key, state_value)
        return result
    except Exception as exc:
        return {"sent": False, "reason": "state_error", "error": type(exc).__name__, "channel": channel}


def _daily_digests(event_service, events: list[dict], briefing_date: str) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    labels: dict[str, str] = {}
    active = [event for event in events if not event.get("is_duplicate")]
    for event in active:
        region = region_channel(str(event.get("region") or ""))
        domain = domain_channel(str(event.get("category") or ""))
        if region:
            grouped[region["id"]].append(event)
            labels[region["id"]] = str(event.get("region") or "Regional")
        if domain:
            grouped[domain["id"]].append(event)
            labels[domain["id"]] = domain["channel_name"].removeprefix("fs-").replace("-", " ").title()
    grouped[route_channel("global")["id"]] = active
    labels[route_channel("global")["id"]] = "Global"

    results = {}
    for destination, destination_events in grouped.items():
        results[destination] = _state_send_once(
            event_service,
            f"discord_digest_{destination}_date",
            briefing_date,
            build_digest_payload(destination, labels[destination], destination_events, briefing_date),
            destination,
        )
    return results


def dispatch_pipeline(
    alerts: list[dict], briefing: dict, run: dict, feintcon: dict, events: Optional[list[dict]] = None
) -> Dict[str, object]:
    """Dispatch primary, fanout, operational, and daily intelligence outputs."""
    from . import event_service

    settings = get_settings()
    ledger = event_service.get_system_state(ALERT_LEDGER_KEY) or {}
    if not isinstance(ledger, dict):
        ledger = {}

    alert_results = []
    fanout_results = []
    fanout_count = 0
    fanout_limit = max(1, min(settings.discord_max_fanout_per_run, 50))
    for alert in alerts:
        event_id = str(alert.get("event_id") or "")
        level = str(alert.get("alert_level") or "none")
        primary = str(alert.get("route") or "breaking")
        prev_level = _previous_level(ledger, event_id, primary, primary=True) if event_id else None
        if event_id and not _should_dispatch(level, prev_level):
            result = {"sent": False, "reason": "already_dispatched", "channel": str(alert.get("channel") or "")}
        else:
            result = send(alert["payload"], channel=primary)
            if result.get("sent") and event_id:
                _mark_dispatched(ledger, event_id, primary, level, primary=True)
        alert["sent"] = bool(result.get("sent"))
        alert["delivery"] = result
        alert_results.append(result)

        per_alert_fanout = []
        if settings.enable_discord_fanout:
            for destination in alert_fanout_destinations(alert):
                if fanout_count >= fanout_limit:
                    per_alert_fanout.append({"sent": False, "reason": "fanout_limit", "channel": destination})
                    continue
                previous = _previous_level(ledger, event_id, destination) if event_id else None
                if event_id and not _should_dispatch(level, previous):
                    secondary = {"sent": False, "reason": "already_dispatched", "channel": resolve_channel(destination)["channel_name"]}
                else:
                    secondary = send(_copy_payload_for(alert["payload"], destination), channel=destination)
                    fanout_count += 1
                    if secondary.get("sent") and event_id:
                        _mark_dispatched(ledger, event_id, destination, level)
                per_alert_fanout.append(secondary)
                fanout_results.append(secondary)
        alert["fanout"] = per_alert_fanout

    if alerts:
        try:
            event_service.set_system_state(ALERT_LEDGER_KEY, _prune_alert_ledger(ledger))
        except Exception:
            pass

    operational = {
        "heartbeat": send(build_heartbeat_payload(run, feintcon), channel="heartbeat"),
        "agent_run": send(build_agent_run_payload(run), channel="agent_runs"),
        "system_status": send(build_system_status_payload(run, feintcon), channel="system_status"),
    }
    if settings.enable_discord_raw_logs:
        operational["raw_logs"] = send(build_raw_log_payload(run, feintcon), channel="raw_logs")

    briefing_date = str(briefing.get("briefing_date", ""))
    daily = {
        "command_center": _state_send_once(
            event_service, "discord_command_center_date", briefing_date,
            build_command_center_payload(briefing, run, feintcon), "command_center",
        ),
        "daily_briefing": _state_send_once(
            event_service, "discord_daily_brief_date", briefing_date,
            build_daily_briefing_payload(briefing), "daily_briefing",
        ),
        "sitrep": _state_send_once(
            event_service, "discord_sitrep_date", briefing_date,
            build_sitrep_payload(briefing, feintcon), "sitrep",
        ),
        "bias_framing": _state_send_once(
            event_service, "discord_bias_framing_date", briefing_date,
            build_bias_payload(briefing), "bias_framing",
        ),
        "cost_control": _state_send_once(
            event_service, "discord_cost_control_date", briefing_date,
            build_cost_payload(briefing), "cost_control",
        ),
    }
    digests = _daily_digests(event_service, events or [], briefing_date) if settings.enable_discord_digests and events else {}

    return {
        "alerts": alert_results,
        "alert_fanout": fanout_results,
        **operational,
        "daily": daily,
        "daily_briefing": daily["daily_briefing"],
        "digests": digests,
    }


def dispatch_error(error_name: str, context: str) -> dict:
    """Send operational and bot-specific error notices without recursion."""
    return {
        "operations": send(build_error_payload(error_name, context, "errors"), channel="errors"),
        "bot": send(build_error_payload(error_name, context, "bot_errors"), channel="bot_errors"),
    }


def summarize_dispatch(result: dict) -> dict:
    """Reduce a nested dispatch result to transport-safe delivery counters."""
    leaves = []
    seen = set()

    def collect(value):
        if isinstance(value, dict):
            if "sent" in value:
                if id(value) not in seen:
                    seen.add(id(value))
                    leaves.append(value)
                return
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(result)
    transports: dict[str, int] = defaultdict(int)
    for item in leaves:
        if item.get("sent") and item.get("transport"):
            transports[str(item["transport"])] += 1
    return {
        "attempted": len(leaves),
        "sent": sum(bool(item.get("sent")) for item in leaves),
        "skipped": sum(item.get("reason") in {"already_dispatched", "already_sent", "fanout_limit"} for item in leaves),
        "failed": sum(not item.get("sent") and item.get("reason") not in {"already_dispatched", "already_sent", "fanout_limit"} for item in leaves),
        "transports": dict(transports),
    }


def _delivery_body(payload: Dict[str, object], bot: bool) -> dict:
    body = {k: v for k, v in payload.items() if k not in {"route", "channel"}}
    body["allowed_mentions"] = {"parse": []}
    if bot:
        body.pop("username", None)
    if "content" in body:
        body["content"] = str(body["content"])[:2000]
    return body


def _post_discord(url: str, body: dict, headers: Optional[dict], channel_name: str, transport: str) -> Dict[str, object]:
    try:
        import httpx

        response = httpx.post(url, headers=headers, json=body, timeout=10.0)
        if response.status_code == 429:
            try:
                retry_after = min(float(response.json().get("retry_after", 0)), 5.0)
            except (TypeError, ValueError):
                retry_after = 0
            if retry_after > 0:
                time.sleep(retry_after)
                response = httpx.post(url, headers=headers, json=body, timeout=10.0)
        return {
            "sent": response.status_code < 300,
            "status_code": response.status_code,
            "channel": channel_name,
            "transport": transport,
        }
    except Exception as exc:  # pragma: no cover - exercised through mocked transport tests
        return {
            "sent": False,
            "reason": "delivery_error",
            "error": type(exc).__name__,
            "channel": channel_name,
            "transport": transport,
        }


def send(payload: Dict[str, object], channel: str = "breaking") -> Dict[str, object]:
    """Deliver through a configured webhook or Watchtower bot channel."""
    settings = get_settings()
    try:
        target = resolve_channel(channel)
    except ValueError:
        return {"sent": False, "reason": "unknown_channel", "channel": channel}
    channel_name = target["channel_name"]
    if not settings.enable_discord_send:
        return {"sent": False, "reason": "discord_send_disabled", "channel": channel_name}

    webhook = _webhook_for(target["id"])
    bot_token = _bot_token()
    bot_channel = _bot_channel_for(target["id"])
    if webhook:
        result = _post_discord(webhook, _delivery_body(payload, bot=False), None, channel_name, "webhook")
        if result.get("sent") or not result.get("status_code") or not (bot_token and bot_channel):
            return result
        fallback = _post_discord(
            f"https://discord.com/api/v10/channels/{bot_channel}/messages",
            _delivery_body(payload, bot=True),
            {"Authorization": f"Bot {bot_token}", "User-Agent": "FeintSignal-Watchtower/1.0"},
            channel_name,
            "bot",
        )
        fallback["fallback_from"] = "webhook"
        return fallback
    if bot_token and bot_channel:
        return _post_discord(
            f"https://discord.com/api/v10/channels/{bot_channel}/messages",
            _delivery_body(payload, bot=True),
            {"Authorization": f"Bot {bot_token}", "User-Agent": "FeintSignal-Watchtower/1.0"},
            channel_name,
            "bot",
        )
    return {"sent": False, "reason": "destination_not_configured", "channel": channel_name}
