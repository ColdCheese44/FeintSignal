"""Persistence/query service over the SQLite store."""
from __future__ import annotations

import json
from typing import Dict, List, Optional

from ..core import database
from ..core.time_utils import now_iso


def persist_run(
    events: List[dict],
    feintcon: Dict[str, object],
    briefing: Dict[str, object],
    alerts: List[dict],
    run_record: Dict[str, object],
) -> None:
    """Upsert the current event set and append run/briefing/alert records.

    Events are UPDATE-or-INSERTed (not wiped) so operator notes and status
    survive a re-run. Foreign keys from ``notes`` make a DELETE-then-INSERT swap
    illegal once an event has notes, so we never delete referenced parent rows.
    """
    conn = database.get_connection()
    try:
        conn.executescript(database.SCHEMA)
        now = now_iso()

        existing = {r["id"]: r["status"] for r in conn.execute("SELECT id, status FROM events").fetchall()}
        new_ids = {ev.get("id") for ev in events}

        # Prune events no longer present (and their notes) before upserting.
        for stale_id in [eid for eid in existing if eid not in new_ids]:
            conn.execute("DELETE FROM notes WHERE event_id = ?", (stale_id,))
            conn.execute("DELETE FROM events WHERE id = ?", (stale_id,))

        conn.execute("DELETE FROM alerts;")

        for ev in events:
            eid = ev.get("id")
            # Preserve an operator-set status across re-runs.
            status = existing.get(eid, ev.get("status", "new"))
            ev["status"] = status
            row = (
                ev.get("title"),
                ev.get("category"),
                ev.get("region"),
                ev.get("country"),
                ev.get("lat"),
                ev.get("lon"),
                float(ev.get("signal_score", 0) or 0),
                float(ev.get("confidence_score", 0) or 0),
                float(ev.get("feintcon_impact", 0) or 0),
                ev.get("alert_level", "none"),
                1 if ev.get("is_duplicate") else 0,
                status,
                ev.get("published_at"),
                now,
                json.dumps(ev),
            )
            if eid in existing:
                conn.execute(
                    """UPDATE events SET
                        title=?, category=?, region=?, country=?, lat=?, lon=?, signal_score=?,
                        confidence_score=?, feintcon_impact=?, alert_level=?, is_duplicate=?,
                        status=?, published_at=?, updated_at=?, payload=?
                       WHERE id=?""",
                    row + (eid,),
                )
            else:
                conn.execute(
                    """INSERT INTO events
                       (title, category, region, country, lat, lon, signal_score,
                        confidence_score, feintcon_impact, alert_level, is_duplicate,
                        status, published_at, updated_at, payload, id)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    row + (eid,),
                )
        for alert in alerts:
            conn.execute(
                """INSERT INTO alerts
                   (event_id, created_at, alert_level, channel, sent, payload)
                   VALUES (?,?,?,?,?,?)""",
                (
                    alert.get("event_id"),
                    now,
                    alert.get("alert_level"),
                    alert.get("channel"),
                    1 if alert.get("sent") else 0,
                    json.dumps(alert.get("payload", {})),
                ),
            )
        conn.execute(
            """INSERT INTO briefings (briefing_date, generated_at, feintcon_level, content)
               VALUES (?,?,?,?)""",
            (
                briefing.get("briefing_date"),
                briefing.get("generated_at"),
                feintcon.get("level"),
                json.dumps(briefing),
            ),
        )
        conn.execute(
            """INSERT INTO agent_runs
               (started_at, finished_at, status, trigger, events_processed, duplicates,
                alerts_generated, feintcon_level, summary)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                run_record.get("started_at"),
                run_record.get("finished_at"),
                run_record.get("status", "ok"),
                run_record.get("trigger"),
                run_record.get("events_processed", 0),
                run_record.get("duplicates", 0),
                run_record.get("alerts_generated", 0),
                feintcon.get("level"),
                json.dumps(run_record),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def list_events(
    region: Optional[str] = None,
    category: Optional[str] = None,
    min_signal: Optional[float] = None,
    include_duplicates: bool = True,
) -> List[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute("SELECT payload FROM events ORDER BY signal_score DESC").fetchall()
    finally:
        conn.close()
    events = [json.loads(r["payload"]) for r in rows]
    if region:
        events = [e for e in events if e.get("region") == region]
    if category:
        events = [e for e in events if e.get("category") == category]
    if min_signal is not None:
        events = [e for e in events if float(e.get("signal_score", 0)) >= min_signal]
    if not include_duplicates:
        events = [e for e in events if not e.get("is_duplicate")]
    return events


def get_event(event_id: str) -> Optional[dict]:
    conn = database.get_connection()
    try:
        row = conn.execute("SELECT payload FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            return None
        event = json.loads(row["payload"])
        notes = conn.execute(
            "SELECT author, text, created_at FROM notes WHERE event_id = ? ORDER BY id", (event_id,)
        ).fetchall()
        event["notes"] = [dict(n) for n in notes]
        return event
    finally:
        conn.close()


def set_status(event_id: str, status: str) -> Optional[dict]:
    conn = database.get_connection()
    try:
        row = conn.execute("SELECT payload FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            return None
        event = json.loads(row["payload"])
        event["status"] = status
        conn.execute(
            "UPDATE events SET status = ?, payload = ?, updated_at = ? WHERE id = ?",
            (status, json.dumps(event), now_iso(), event_id),
        )
        conn.commit()
        return event
    finally:
        conn.close()


def add_note(event_id: str, text: str, author: str = "operator") -> Optional[dict]:
    conn = database.get_connection()
    try:
        row = conn.execute("SELECT id FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            return None
        conn.execute(
            "INSERT INTO notes (event_id, author, text, created_at) VALUES (?,?,?,?)",
            (event_id, author, text, now_iso()),
        )
        conn.commit()
    finally:
        conn.close()
    return get_event(event_id)


def list_runs(limit: int = 25) -> List[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute(
            """SELECT id, started_at, finished_at, status, trigger, events_processed,
                      duplicates, alerts_generated, feintcon_level
               FROM agent_runs ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def latest_run() -> Optional[dict]:
    runs = list_runs(limit=1)
    return runs[0] if runs else None


def latest_briefing() -> Optional[dict]:
    conn = database.get_connection()
    try:
        row = conn.execute(
            "SELECT content FROM briefings ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return json.loads(row["content"]) if row else None
    finally:
        conn.close()


def list_alerts() -> List[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute(
            "SELECT event_id, created_at, alert_level, channel, sent, payload FROM alerts ORDER BY id DESC"
        ).fetchall()
        out = []
        for r in rows:
            rec = dict(r)
            rec["payload"] = json.loads(rec["payload"])
            out.append(rec)
        return out
    finally:
        conn.close()


def get_system_state(key: str, default=None):
    conn = database.get_connection()
    try:
        conn.executescript(database.SCHEMA)
        row = conn.execute("SELECT value FROM system_state WHERE key = ?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default
    finally:
        conn.close()


def set_system_state(key: str, value) -> None:
    conn = database.get_connection()
    try:
        conn.executescript(database.SCHEMA)
        conn.execute(
            """INSERT INTO system_state (key, value, updated_at) VALUES (?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (key, json.dumps(value), now_iso()),
        )
        conn.commit()
    finally:
        conn.close()
