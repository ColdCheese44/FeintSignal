"""Normalizer: cleans/standardises raw events before scoring.

Ensures required fields exist, derives staleness from ``published_at``, and
guarantees lat/lon for map/globe markers (falls back to a region centroid).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from ..core.config import get_settings
from ..core.time_utils import is_stale
from .signal_scorer import DEFAULT_SCORING_RULES

_REGION_CENTROIDS: Optional[Dict[str, dict]] = None


def _region_centroids() -> Dict[str, dict]:
    global _REGION_CENTROIDS
    if _REGION_CENTROIDS is None:
        path = Path(get_settings().config_dir) / "regions.json"
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            _REGION_CENTROIDS = {r["label"]: r for r in data.get("regions", [])}
        except (OSError, json.JSONDecodeError):
            _REGION_CENTROIDS = {}
    return _REGION_CENTROIDS


def normalize_event(event: dict) -> dict:
    ev = dict(event)
    ev.setdefault("status", "new")
    ev.setdefault("tags", [])
    ev.setdefault("conflicting_reports", False)
    ev.setdefault("country", None)

    # Numeric inputs default to 0 if absent.
    for field in ("severity", "urgency", "confidence", "relevance"):
        ev[field] = float(ev.get(field, 0) or 0)

    # Geo fallback to region centroid so every marker is plottable.
    if ev.get("lat") is None or ev.get("lon") is None:
        centroid = _region_centroids().get(ev.get("region"))
        if centroid:
            ev["lat"] = centroid.get("lat")
            ev["lon"] = centroid.get("lon")

    stale_hours = float(DEFAULT_SCORING_RULES["thresholds"]["stale_hours"])  # type: ignore[index]
    ev["is_stale"] = is_stale(ev.get("published_at"), stale_hours)

    return ev


def normalize(events: List[dict]) -> List[dict]:
    return [normalize_event(e) for e in events]
