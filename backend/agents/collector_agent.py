"""Mock and keyless RSS collection behind explicit capability gates."""
from __future__ import annotations

import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Callable, Dict, List

import httpx

from ..core.config import get_settings
from ..core.time_utils import hours_ago, hours_since, now_iso, to_iso

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")

CATEGORY_RULES = [
    ("terrorism", ("terror", "militant attack", "extremist", "bombing")),
    ("conflict", ("war", "military", "airstrike", "missile", "troops", "ceasefire", "armed forces")),
    ("cyber", ("cyber", "ransomware", "malware", "data breach", "hacker", "vulnerability")),
    ("disaster", ("earthquake", "flood", "wildfire", "hurricane", "cyclone", "volcano", "landslide")),
    ("health", ("outbreak", "disease", "virus", "health", "epidemic", "pandemic")),
    ("energy", ("oil", "gas", "pipeline", "power grid", "energy", "electricity")),
    ("economy", ("economy", "inflation", "tariff", "trade", "market", "recession", "central bank")),
    ("crime", ("cartel", "organized crime", "trafficking", "kidnap", "gang")),
    ("technology", ("artificial intelligence", " ai ", "technology", "semiconductor", "robot")),
    ("politics", ("election", "president", "parliament", "government", "minister", "congress")),
]

REGION_RULES = [
    ("Middle East", ("israel", "gaza", "iran", "iraq", "syria", "lebanon", "yemen", "saudi", "qatar")),
    ("Europe", ("ukraine", "russia", "europe", "britain", "uk ", "france", "germany", "italy", "poland", "nato")),
    ("Asia-Pacific", ("china", "taiwan", "japan", "korea", "india", "pakistan", "australia", "philippines", "indonesia")),
    ("Africa", ("africa", "sudan", "congo", "somalia", "ethiopia", "nigeria", "kenya", "sahel")),
    ("Latin America", ("mexico", "brazil", "argentina", "colombia", "venezuela", "chile", "peru", "caribbean")),
    ("North America", ("united states", "u.s.", " us ", "canada", "washington", "white house")),
]

CATEGORY_SEVERITY = {
    "terrorism": 82,
    "conflict": 78,
    "disaster": 76,
    "cyber": 72,
    "health": 68,
    "energy": 66,
    "crime": 64,
    "economy": 62,
    "politics": 60,
    "technology": 56,
    "geopolitics": 64,
}


def _load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_source_catalog(data_dir: Path | None = None) -> Dict[str, dict]:
    settings = get_settings()
    data_dir = data_dir or settings.data_dir
    raw = _load_json(data_dir / "mock_sources.json")
    return {source["id"]: source for source in raw.get("sources", [])}


def load_live_source_registry(config_dir: Path | None = None) -> dict:
    settings = get_settings()
    path = (config_dir or settings.config_dir) / "live_sources.json"
    registry = _load_json(path)
    if not isinstance(registry, dict) or not isinstance(registry.get("sources"), list):
        raise ValueError("Live source registry must contain a sources list.")
    return registry


def _resolve_sources(event: dict, catalog: Dict[str, dict]) -> List[dict]:
    sources: List[dict] = []
    for source_id in event.get("source_ids", []):
        template = catalog.get(source_id)
        if not template:
            continue
        source = {key: value for key, value in template.items() if key not in ("id", "age_hours")}
        age = template.get("age_hours", event.get("age_hours", 6))
        source["published_at"] = hours_ago(age)
        sources.append(source)
    for inline in event.get("sources", []) or []:
        source = dict(inline)
        if "published_at" not in source:
            source["published_at"] = hours_ago(inline.get("age_hours", event.get("age_hours", 6)))
        sources.append(source)
    return sources


def _clean_markup(value: str | None, limit: int = 1200) -> str:
    without_tags = _TAG_RE.sub(" ", value or "")
    return _SPACE_RE.sub(" ", html.unescape(without_tags)).strip()[:limit]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for child in node.iter():
        if _local_name(child.tag) in names and child.text and child.text.strip():
            return child.text.strip()
    return ""


def _entry_link(node: ET.Element) -> str:
    for child in node.iter():
        if _local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href", "").strip()
        if href and child.attrib.get("rel", "alternate") in {"alternate", ""}:
            return href
        if child.text and child.text.strip().startswith("http"):
            return child.text.strip()
    guid = _child_text(node, ("guid", "id"))
    return guid if guid.startswith("http") else ""


def _published_iso(value: str) -> str:
    if not value:
        return now_iso()
    try:
        parsed = parsedate_to_datetime(value)
        return to_iso(parsed)
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return to_iso(parsed)
    except ValueError:
        return now_iso()


def parse_feed(xml_content: bytes | str) -> List[dict]:
    """Parse RSS or Atom into publisher-neutral article records."""
    root = ET.fromstring(xml_content)
    entries = [node for node in root.iter() if _local_name(node.tag) in {"item", "entry"}]
    articles: List[dict] = []
    for entry in entries:
        title = _clean_markup(_child_text(entry, ("title",)), limit=300)
        link = _entry_link(entry)
        if not title or not link:
            continue
        articles.append(
            {
                "title": title,
                "url": link,
                "summary": _clean_markup(_child_text(entry, ("description", "summary", "encoded", "content"))),
                "published_at": _published_iso(_child_text(entry, ("pubDate", "published", "updated", "date"))),
            }
        )
    return articles


def _infer_category(text: str, default: str) -> str:
    lowered = f" {text.lower()} "
    for category, keywords in CATEGORY_RULES:
        if any(keyword in lowered for keyword in keywords):
            return category
    return default


def _infer_region(text: str) -> str:
    lowered = f" {text.lower()} "
    for region, keywords in REGION_RULES:
        if any(keyword in lowered for keyword in keywords):
            return region
    return "Global"


def _urgency(published_at: str) -> float:
    age = hours_since(published_at)
    if age is None or age <= 6:
        return 80.0
    if age <= 24:
        return 68.0
    return 52.0


def article_to_event(article: dict, source_config: dict) -> dict:
    combined = f"{article.get('title', '')} {article.get('summary', '')}"
    category = _infer_category(combined, str(source_config.get("default_category", "geopolitics")))
    source_url = str(article["url"])
    published_at = str(article["published_at"])
    reliability = float(source_config.get("reliability_score", 75))
    event_id = "rss-" + hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:20]
    return {
        "id": event_id,
        "title": article["title"],
        "summary": article.get("summary") or article["title"],
        "category": category,
        "region": _infer_region(combined),
        "country": None,
        "lat": None,
        "lon": None,
        "published_at": published_at,
        "occurred_at": published_at,
        "status": "new",
        "tags": [category, "live-rss"],
        "severity": float(CATEGORY_SEVERITY.get(category, 60)),
        "urgency": _urgency(published_at),
        "confidence": min(90.0, max(55.0, reliability)),
        "relevance": 70.0,
        "conflicting_reports": False,
        "sources": [
            {
                "name": source_config["name"],
                "url": source_url,
                "published_at": published_at,
                "source_type": source_config["source_type"],
                "reliability_score": reliability,
                "political_lean": source_config.get("perspective_bucket", "unknown"),
                "country_of_origin": source_config.get("country_of_origin", "unknown"),
                "independence_group": source_config["independence_group"],
            }
        ],
    }


def _fetch_feed(url: str) -> bytes:
    with httpx.Client(
        follow_redirects=True,
        timeout=15.0,
        headers={"User-Agent": "FeintSignal/0.1 RSS reader"},
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.content


def collect_live(
    config_dir: Path | None = None,
    fetcher: Callable[[str], bytes] | None = None,
) -> List[dict]:
    settings = get_settings()
    registry = load_live_source_registry(config_dir)
    per_source_limit = int(registry.get("default_per_source_limit", 8))
    fetch = fetcher or _fetch_feed
    events: List[dict] = []
    enabled_sources = [source for source in registry["sources"] if source.get("enabled", False)]

    for source in enabled_sources:
        try:
            articles = parse_feed(fetch(str(source["feed_url"])))
        except (httpx.HTTPError, ET.ParseError, OSError, ValueError):
            continue
        events.extend(article_to_event(article, source) for article in articles[:per_source_limit])

    if not events:
        raise RuntimeError(f"Live collection returned no events from {len(enabled_sources)} configured feeds.")
    return sorted(events, key=lambda event: str(event.get("published_at", "")), reverse=True)[: settings.max_events_per_run]


def collect(data_dir: Path | None = None) -> List[dict]:
    settings = get_settings()
    if settings.enable_live_research:
        return collect_live()

    data_dir = data_dir or settings.data_dir
    catalog = load_source_catalog(data_dir)
    raw = _load_json(data_dir / "mock_events.json")
    events: List[dict] = []
    for item in raw.get("events", []):
        event = dict(item)
        age = event.get("age_hours", 6)
        event.setdefault("published_at", hours_ago(age))
        event.setdefault("occurred_at", hours_ago(age + 0.5))
        event["sources"] = _resolve_sources(event, catalog)
        event.pop("source_ids", None)
        events.append(event)
    return events[: settings.max_events_per_run]
