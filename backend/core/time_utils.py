"""Time helpers. All timestamps are UTC ISO-8601 strings with a trailing 'Z'."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

UTC = timezone.utc


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def now_iso() -> str:
    return to_iso(now_utc())


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def hours_ago(hours: float) -> str:
    return to_iso(now_utc() - timedelta(hours=hours))


def hours_since(value: Optional[str], reference: Optional[datetime] = None) -> Optional[float]:
    dt = parse_iso(value)
    if dt is None:
        return None
    ref = reference or now_utc()
    return (ref - dt).total_seconds() / 3600.0


def is_stale(published_at: Optional[str], threshold_hours: float, reference: Optional[datetime] = None) -> bool:
    age = hours_since(published_at, reference)
    if age is None:
        return False
    return age > threshold_hours
