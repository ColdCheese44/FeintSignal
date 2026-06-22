# FeintSignal

FeintSignal is a local-first current affairs intelligence dashboard designed for Brendan Dodd's Feint ecosystem.

This repo has been initialized for the target local path:

```powershell
D:\Windows\FeintSignal
```

Clone location:

```powershell
mkdir D:\Windows
cd D:\Windows
git clone https://github.com/ColdCheese44/FeintSignal.git
cd FeintSignal
```

## MVP scaffold status

The MVP scaffold is **implemented and committed in this repository** and validated locally on the Windows host at `D:\Windows\FeintSignal`. It includes:

- Python/FastAPI backend
- SQLite local state
- deterministic signal scoring
- source validation
- duplicate/noise suppression
- FEINTCON calculation
- Discord alert payload generation without auto-send
- React/Vite/TypeScript dashboard shell
- 2D globe fallback contract for later 3D globe upgrade
- mock current affairs data
- pytest backend test suite
- Windows PowerShell run scripts
- docs for architecture, scoring, Discord setup, and dashboard design

## Validation results

```text
pytest backend/tests -q
12 passed

python scripts/seed_mock_data.py
Seeded FeintSignal mock data: 11 events, 3 alert payload(s).
FEINTCON 3 — Significant multi-region instability or major confirmed crisis

FastAPI smoke checks (all 200):
GET  /health
GET  /events                       (11 events; 1 suppressed duplicate)
GET  /events/{id}
POST /events/{id}/status
POST /events/{id}/notes
GET  /system/feintcon              (level 3)
GET  /system/heartbeat
GET  /briefings/daily/latest
POST /briefings/daily/generate
GET  /agents/runs
POST /agents/run-now
POST /discord/test                 (sent:false — sending disabled by default)

frontend npm run build
tsc + vite build succeeded (dist/ emitted)
```

## Safety posture

- `.env` is ignored.
- `.env.example` contains placeholders only.
- Live research is disabled by default.
- LLM calls are disabled by default.
- Discord send is disabled by default.
- FEINTCON is explicitly internal and not official DEFCON.

## Local run commands

Backend:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\seed_mock_data.py
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8765
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Tests:

```powershell
pytest backend/tests -q
```

## Project layout

```
backend/   FastAPI app, agent pipeline (collector → normalizer → source_validator →
           deduper → signal_scorer → feintcon → alert_router → briefing), services, tests
frontend/  React + Vite + TypeScript tactical dashboard (2D SignalGlobe + 3D-ready contract)
config/    topics, regions, scoring rules, source taxonomy, channels, watchlists, UI
data/      mock_events.json, mock_sources.json (the SQLite DB is generated, not tracked)
scripts/   PowerShell run scripts + seed/hourly Python entry points
docs/      ARCHITECTURE, INTELLIGENCE_DOCTRINE, SCORING_MODEL, DISCORD_SETUP, DASHBOARD_DESIGN, ROADMAP
```

## Next engineering steps

See [docs/ROADMAP.md](docs/ROADMAP.md): hourly scheduler hardening, dashboard-visible
agent run history, 3D globe upgrade, RSS/live ingestion behind `ENABLE_LIVE_RESEARCH=false`,
and frontend smoke tests.
