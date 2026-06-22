"""Pipeline orchestrator: chains agents and (optionally) persists results.

collect -> normalize -> dedupe -> score -> feintcon -> alert -> briefing -> persist
"""
from __future__ import annotations

from typing import Dict, List, Optional

from ..core.time_utils import now_iso
from . import (
    alert_router,
    briefing_agent,
    collector_agent,
    deduper,
    feintcon_agent,
    normalizer_agent,
    signal_scorer,
)


def run_pipeline(trigger: str = "manual", persist: bool = True, data_dir=None) -> Dict[str, object]:
    started_at = now_iso()

    raw = collector_agent.collect(data_dir=data_dir)
    normalized = normalizer_agent.normalize(raw)
    deduped = deduper.mark_duplicates(normalized)
    scored = signal_scorer.score_events(deduped)

    feintcon = feintcon_agent.compute_feintcon(scored)
    alerts = alert_router.route_alerts(scored)  # mutates scored: sets alert_level/requires_human_review
    briefing = briefing_agent.generate_briefing(scored, feintcon)

    finished_at = now_iso()
    duplicates = sum(1 for e in scored if e.get("is_duplicate"))
    run_record = {
        "started_at": started_at,
        "finished_at": finished_at,
        "status": "ok",
        "trigger": trigger,
        "events_processed": len(scored),
        "duplicates": duplicates,
        "alerts_generated": len(alerts),
        "feintcon_level": feintcon.get("level"),
    }

    from ..services import discord_service

    discord = discord_service.dispatch_pipeline(alerts, briefing, run_record, feintcon)

    if persist:
        # Imported here to avoid a heavy import at module load / test time.
        from ..services import event_service

        event_service.persist_run(scored, feintcon, briefing, alerts, run_record)

    return {
        "run": run_record,
        "feintcon": feintcon,
        "events": scored,
        "alerts": alerts,
        "briefing": briefing,
        "discord": discord,
    }


def summarize(result: Dict[str, object]) -> str:
    run = result["run"]  # type: ignore[index]
    return (
        f"events={run['events_processed']} duplicates={run['duplicates']} "
        f"alerts={run['alerts_generated']} feintcon={run['feintcon_level']}"
    )
