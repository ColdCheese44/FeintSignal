"""Seed the local SQLite database from bundled mock data.

Resets the DB to a clean, reproducible state and runs the agent pipeline once.
Safe to run repeatedly. No network access; no secrets touched.

    python scripts/seed_mock_data.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.core import database  # noqa: E402
from backend.agents import orchestrator  # noqa: E402


def main() -> int:
    database.reset_db()
    result = orchestrator.run_pipeline(trigger="seed", persist=True)
    n_events = result["run"]["events_processed"]
    n_alerts = result["run"]["alerts_generated"]
    feintcon = result["feintcon"]["level"]
    print(f"Seeded FeintSignal mock data: {n_events} events, {n_alerts} alert payload(s).")
    print(f"FEINTCON {feintcon} — {result['feintcon']['label']}")
    print(f"({result['feintcon']['disclaimer']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
