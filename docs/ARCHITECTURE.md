# FeintSignal Architecture

FeintSignal follows the FeintTrade and FeintSupplyCo local-operator pattern: a loopback dashboard, deterministic automation pipeline, SQLite state, explicit capability gates, Discord as the mobile operations layer, Windows background supervision, and a native desktop launcher.

## Components

```text
Desktop launcher / scheduled task
             |
React + Vite Situation Room
  top bar | left rail | 3D globe | dossiers | intel column | tool drawer
             |
FastAPI on 127.0.0.1:8765
  events | briefings | agents | scheduler | Discord | system status
             |
Deterministic agent pipeline
  collect -> normalize -> validate -> dedupe -> score -> FEINTCON
          -> alert route -> perspective analysis -> briefing -> persist/dispatch
             |
SQLite + JSON config + mock/live source adapters
```

## Agent pipeline

1. `collector_agent`: mock collection by default; allowlisted, keyless RSS collection behind the live-research gate.
2. `normalizer_agent`: fields, timestamps, and geographic centroids.
3. `source_validator`: reliability, independence, and official-source checks.
4. `deduper`: duplicate/noise suppression.
5. `signal_scorer`: deterministic importance and confidence scoring.
6. `feintcon_agent`: internal readiness posture.
7. `alert_router`: direct standard and critical alert routing.
8. `perspective_agent`: evidence-bound viewpoint, consensus, and uncertainty analysis.
9. `briefing_agent`: digestible daily intelligence report.
10. `heartbeat_agent`: agent and capability posture.

## Scheduler

The in-process scheduler exposes status, start, and stop APIs, prevents overlapping manual/scheduled runs, and persists safe status snapshots. It runs only while the backend is alive. For machine-level operation, the launcher can install the separate Windows scheduled updater. Operators should choose one hourly mode, not both.

## Discord

The JSON command-center config is the source of truth for 32 channels. Nine webhook routes are active in the MVP. The pipeline can dispatch eligible alerts, heartbeats, agent summaries, safe error reports, and at most one successful daily briefing per briefing date. Every network call still requires `ENABLE_DISCORD_SEND=true` and the matching webhook.

## Safety boundaries

- Live research, LLM calls, in-process scheduling, and Discord delivery default off.
- Alerts require deterministic score, confidence, source-quality, corroboration, duplicate, and freshness checks.
- Webhook URLs and API keys never appear in API responses or logs.
- FEINTCON is not official DEFCON.
- Globe correlation arcs do not claim causation.
