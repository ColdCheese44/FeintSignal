# FeintSignal Architecture

FeintSignal is a **local-first** current-affairs intelligence dashboard. It runs
entirely on your machine against bundled mock data — no external services, API
keys, or network access are required, and all capability gates default to OFF.

## High-level

```
            ┌────────────────────────── Frontend (React/Vite/TS) ──────────────────────────┐
            │  TopStatusBar · LeftRail · SignalGlobe(2D) · EventFeed · EventDialog          │
            │  DailyBriefing · Agent/Heartbeat/Cost/Discord panels                          │
            └───────────────▲───────────────────────────────────────────────────────────────┘
                            │  typed fetch (lib/api.ts)
                            │  HTTP JSON
            ┌───────────────┴───────────────── Backend (FastAPI) ───────────────────────────┐
            │  api/  routes_events · routes_agents · routes_briefings · routes_system ·       │
            │        routes_discord                                                          │
            │  services/  event_service (SQLite) · scheduler_service · discord_service       │
            │  agents/  orchestrator → collector → normalizer → source_validator →           │
            │           deduper → signal_scorer → feintcon → alert_router → briefing         │
            │  core/  config · database · schemas · time_utils                               │
            └───────────────▲───────────────────────────────────────────────────────────────┘
                            │
                    SQLite (data/feintsignal.db, git-ignored, reproducible)
                    Mock data (data/mock_events.json, data/mock_sources.json)
                    Config (config/*.json)
```

## The agent pipeline

The orchestrator chains nine deterministic agents:

1. **collector_agent** — loads candidate events (mock by default; live ingestion
   is gated behind `ENABLE_LIVE_RESEARCH` and intentionally unimplemented).
2. **normalizer_agent** — standardises fields, fills geo from region centroids,
   derives staleness from `published_at`.
3. **source_validator** — validates required source fields, tiers reliability,
   counts independent groups, detects official sources.
4. **deduper** — clusters near-duplicate stories (region+category+title overlap)
   and suppresses the lower-confidence copies.
5. **signal_scorer** — the deterministic scoring core (see SCORING_MODEL.md).
6. **feintcon_agent** — rolls events up into the FEINTCON readiness level.
7. **alert_router** — evaluates standard/critical alert rules and human-review
   gating; builds (does not send) Discord payloads.
8. **briefing_agent** — produces the daily briefing (template-based, no LLM).
9. **heartbeat_agent** — reports pipeline/config health.

Each agent is a small, pure, individually unit-tested function.

## Persistence

SQLite via the stdlib `sqlite3` module (no ORM). Events are stored with indexed
filter columns plus a full JSON `payload`. Operator state (status, notes) is
**preserved across pipeline re-runs** — events are upserted, never wiped, so the
`notes` foreign key stays valid. The DB is always reproducible from mock data via
`scripts/seed_mock_data.py`.

## Safety boundaries

- All gates (`ENABLE_LIVE_RESEARCH`, `ENABLE_LLM`, `ENABLE_DISCORD_SEND`) default
  to `false`.
- Webhook URLs live only in environment variables and are never returned,
  logged, or rendered.
- Critical alerts and sensitive claim types require human review before any send.
- FEINTCON is explicitly an internal indicator, not official DEFCON.
