"""Collector: loads candidate events.

By default this reads bundled mock data only. Live ingestion (RSS/web) is gated
behind ENABLE_LIVE_RESEARCH and is intentionally NOT implemented in the MVP —
the stub raises a clear, safe message so live mode can never silently fire.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from ..core.config import get_settings
from ..core.time_utils import hours_ago


def _load_json(path: Path) -> object:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_source_catalog(data_dir: Path | None = None) -> Dict[str, dict]:
    settings = get_settings()
    data_dir = data_dir or settings.data_dir
    raw = _load_json(data_dir / "mock_sources.json")
    catalog = {s["id"]: s for s in raw.get("sources", [])}
    return catalog


def _resolve_sources(event: dict, catalog: Dict[str, dict]) -> List[dict]:
    sources: List[dict] = []
    for sid in event.get("source_ids", []):
        template = catalog.get(sid)
        if not template:
            continue
        src = {k: v for k, v in template.items() if k not in ("id", "age_hours")}
        age = template.get("age_hours", event.get("age_hours", 6))
        src["published_at"] = hours_ago(age)
        sources.append(src)
    # Allow fully-inline sources too.
    for inline in event.get("sources", []) or []:
        src = dict(inline)
        if "published_at" not in src:
            src["published_at"] = hours_ago(inline.get("age_hours", event.get("age_hours", 6)))
        sources.append(src)
    return sources


def collect(data_dir: Path | None = None) -> List[dict]:
    settings = get_settings()
    if settings.enable_live_research:
        raise NotImplementedError(
            "Live research is enabled but no live collector is implemented in the MVP. "
            "Keep ENABLE_LIVE_RESEARCH=false until an RSS/web ingestor is added."
        )

    data_dir = data_dir or settings.data_dir
    catalog = load_source_catalog(data_dir)
    raw = _load_json(data_dir / "mock_events.json")

    events: List[dict] = []
    for item in raw.get("events", []):
        ev = dict(item)
        age = ev.get("age_hours", 6)
        ev.setdefault("published_at", hours_ago(age))
        ev.setdefault("occurred_at", hours_ago(age + 0.5))
        ev["sources"] = _resolve_sources(ev, catalog)
        ev.pop("source_ids", None)
        events.append(ev)

    return events[: settings.max_events_per_run]
