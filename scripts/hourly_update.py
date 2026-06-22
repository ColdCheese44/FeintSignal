"""One-shot pipeline run intended for Windows Task Scheduler / cron.

Runs collect -> score -> FEINTCON -> alerts -> persist once and prints a summary.
Discord sending remains gated by ENABLE_DISCORD_SEND. No live research by default.

    python scripts/hourly_update.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.core import database  # noqa: E402
from backend.agents import orchestrator  # noqa: E402
from backend.core.time_utils import now_iso  # noqa: E402


def main() -> int:
    database.init_db()
    result = orchestrator.run_pipeline(trigger="hourly", persist=True)
    print(f"[{now_iso()}] hourly update: {orchestrator.summarize(result)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
