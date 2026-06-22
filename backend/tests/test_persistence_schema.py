"""Persistence should match the informational-only workflow."""
from backend.core import database
from backend.services import event_service


def test_fresh_schema_has_no_review_gate_columns(tmp_path, monkeypatch):
    db_path = tmp_path / "feintsignal-test.db"
    original_get_connection = database.get_connection
    monkeypatch.setattr(database, "get_connection", lambda: original_get_connection(db_path))

    event_service.persist_run(
        events=[{
            "id": "evt-1",
            "title": "Informational event",
            "category": "politics",
            "region": "Global",
            "signal_score": 72,
            "confidence_score": 70,
            "feintcon_impact": 1,
            "alert_level": "none",
            "is_duplicate": False,
            "status": "new",
        }],
        feintcon={"level": 4},
        briefing={"briefing_date": "2026-06-22", "generated_at": "2026-06-22T00:00:00Z"},
        alerts=[],
        run_record={"started_at": "2026-06-22T00:00:00Z", "status": "ok"},
    )

    with original_get_connection(db_path) as conn:
        event_columns = {row["name"] for row in conn.execute("PRAGMA table_info(events)")}
        alert_columns = {row["name"] for row in conn.execute("PRAGMA table_info(alerts)")}
    assert "requires_human_review" not in event_columns
    assert "requires_human_review" not in alert_columns

    # Existing local databases may retain the removed columns. New writes omit
    # them and remain compatible with SQLite's historical defaults.
    with original_get_connection(db_path) as conn:
        conn.execute("ALTER TABLE events ADD COLUMN requires_human_review INTEGER DEFAULT 0")
        conn.execute("ALTER TABLE alerts ADD COLUMN requires_human_review INTEGER DEFAULT 0")
        conn.commit()
    event_service.persist_run(
        events=[{"id": "evt-1", "title": "Updated event", "status": "new"}],
        feintcon={"level": 4},
        briefing={"briefing_date": "2026-06-22", "generated_at": "2026-06-22T01:00:00Z"},
        alerts=[],
        run_record={"started_at": "2026-06-22T01:00:00Z", "status": "ok"},
    )
