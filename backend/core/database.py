"""SQLite persistence layer (stdlib only — no ORM).

Events are stored with indexed columns for filtering plus a JSON ``payload``
column holding the full scored object. The database file lives under ``data/``
and is git-ignored; it is always reproducible from mock data via the seed script.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from .config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    category        TEXT,
    region          TEXT,
    country         TEXT,
    lat             REAL,
    lon             REAL,
    signal_score    REAL,
    confidence_score REAL,
    feintcon_impact REAL,
    alert_level     TEXT,
    requires_human_review INTEGER DEFAULT 0,
    is_duplicate    INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'new',
    published_at    TEXT,
    updated_at      TEXT,
    payload         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_signal ON events(signal_score);
CREATE INDEX IF NOT EXISTS idx_events_region ON events(region);

CREATE TABLE IF NOT EXISTS notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    TEXT NOT NULL,
    author      TEXT,
    text        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    FOREIGN KEY(event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at        TEXT NOT NULL,
    finished_at       TEXT,
    status            TEXT NOT NULL,
    trigger           TEXT,
    events_processed  INTEGER DEFAULT 0,
    duplicates        INTEGER DEFAULT 0,
    alerts_generated  INTEGER DEFAULT 0,
    feintcon_level    INTEGER,
    summary           TEXT
);

CREATE TABLE IF NOT EXISTS briefings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    briefing_date TEXT NOT NULL,
    generated_at  TEXT NOT NULL,
    feintcon_level INTEGER,
    content       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id      TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    alert_level   TEXT NOT NULL,
    channel       TEXT,
    requires_human_review INTEGER DEFAULT 0,
    sent          INTEGER DEFAULT 0,
    payload       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS system_state (
    key           TEXT PRIMARY KEY,
    value         TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
"""


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else get_settings().db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def reset_db(db_path: Optional[Path] = None) -> None:
    """Drop all rows (used by the seed script for a clean reproducible state)."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        for table in ("alerts", "briefings", "agent_runs", "notes", "events", "system_state"):
            conn.execute(f"DELETE FROM {table};")
        conn.commit()
    finally:
        conn.close()
