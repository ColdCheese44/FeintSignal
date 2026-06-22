"""FeintSignal FastAPI application.

Local-first intelligence dashboard backend. On startup it ensures the database
exists and, if empty, runs the configured pipeline once so the UI has data.
External services remain independently capability-gated.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    routes_agents,
    routes_briefings,
    routes_discord,
    routes_events,
    routes_system,
)
from .core import database
from .core.config import get_settings

logger = logging.getLogger("feintsignal")

app = FastAPI(
    title="FeintSignal",
    version="0.1.0",
    description=(
        "Local-first AI/current-affairs intelligence dashboard. "
        "FEINTCON is an internal readiness indicator, not official DEFCON."
    ),
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.frontend_port}",
        f"http://127.0.0.1:{settings.frontend_port}",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_system.router)
app.include_router(routes_events.router)
app.include_router(routes_agents.router)
app.include_router(routes_briefings.router)
app.include_router(routes_discord.router)


@app.on_event("startup")
def _startup() -> None:
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    # httpx INFO records include complete request URLs; Discord webhook URLs are
    # credentials and must never be written to local runtime logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    database.init_db()
    # Auto-seed once if there are no events yet, so the dashboard is never empty.
    from .services import event_service

    if not event_service.list_events():
        from .agents import orchestrator

        try:
            orchestrator.run_pipeline(trigger="startup")
            logger.info("Startup pipeline seeded mock data.")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Startup seeding skipped: %s", exc)
    if settings.enable_scheduler:
        from .services.scheduler_service import scheduler

        scheduler.start(interval_minutes=settings.update_interval_minutes)


@app.on_event("shutdown")
def _shutdown() -> None:
    from .services.scheduler_service import scheduler

    scheduler.stop()


@app.get("/")
def root():
    return {
        "service": "feintsignal",
        "docs": "/docs",
        "health": "/health",
        "note": "FEINTCON is an internal FeintSignal readiness indicator, not official DEFCON.",
    }
