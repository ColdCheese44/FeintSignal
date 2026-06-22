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
- Discord alert payload generation with default-off delivery
- Watchtower Discord command-center routing for 32 operational channels
- gated Discord dispatch for alerts, heartbeats, agent runs, errors, and once-daily briefings
- React/Vite/TypeScript dashboard shell
- globe-first tabbed workspace with an offline-capable interactive 3D globe, collapsible navigation, and collapsible system tools
- balanced keyless RSS collection across left, center, right, international, official, and specialist source buckets
- neutral perspective dossiers with left, center, right, consensus, and uncertainty sections
- evidence-bound Anthropic/OpenAI synthesis with source links, bounded usage, and deterministic fallback
- supervised hourly scheduler with overlap protection and dashboard controls
- mock current affairs data
- pytest backend test suite
- Windows PowerShell run scripts
- WPF desktop control panel and chromeless dashboard launcher
- docs for architecture, scoring, Discord setup, and dashboard design

## Validation results

```text
pytest backend/tests -q
34 passed

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

npm audit
0 vulnerabilities
```

## Safety posture

- `.env` is ignored.
- `.env.example` contains placeholders only.
- Live research is disabled by default.
- LLM calls are disabled in the template and remain bounded when enabled locally.
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

Secret-safe integration check:

```powershell
python scripts/check_integrations.py --live
```

Desktop launcher:

```powershell
npm run install-launcher  # create Desktop and Start Menu shortcuts
npm run app               # open the WPF control panel
npm run terminal          # open the dashboard as a desktop app window
```

Discord setup is documented in [docs/DISCORD_SETUP.md](docs/DISCORD_SETUP.md). The exact APIs and credentials to obtain now versus later are listed in [docs/API_REQUIREMENTS.md](docs/API_REQUIREMENTS.md). All real values belong only in local `.env`.

## Project layout

```
backend/   FastAPI app, agent pipeline (collector → normalizer → source_validator →
           deduper → signal_scorer → feintcon → alert_router → briefing), services, tests
frontend/  React + Vite + TypeScript tactical dashboard (2D SignalGlobe + 3D-ready contract)
config/    topics, regions, scoring rules, source taxonomy, channels, watchlists, UI
data/      mock_events.json, mock_sources.json (the SQLite DB is generated, not tracked)
scripts/   PowerShell run scripts + seed/hourly Python entry points
launcher/  WPF control panel, dashboard app-window launcher, icon, and shortcut installer
docs/      architecture, doctrine, scoring, Discord/API setup, dashboard design, and roadmap
```

## Next engineering steps

See [docs/SITUATION_ROOM_DOCTRINE.md](docs/SITUATION_ROOM_DOCTRINE.md) for the operating model and [docs/ROADMAP.md](docs/ROADMAP.md) for live-source ingestion, LLM adapters, frontend tests, and audit workflow work.
