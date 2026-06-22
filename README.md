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

The MVP scaffold has been generated and validated locally in this ChatGPT runtime as a downloadable package. It includes:

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

## Validation completed before handoff

```text
pytest backend/tests -q
12 passed

python scripts/seed_mock_data.py
Seeded FeintSignal mock data: 11 events, 3 alert payload(s).

FastAPI smoke checks:
/health 200
/events 200
/system/feintcon 200
/system/heartbeat 200
/briefings/daily/latest 200

frontend npm run build
vite build succeeded
```

## Safety posture

- `.env` is ignored.
- `.env.example` contains placeholders only.
- Live research is disabled by default.
- LLM calls are disabled by default.
- Discord send is disabled by default.
- FEINTCON is explicitly internal and not official DEFCON.

## Local run commands after scaffold is copied into this repo

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

## Next engineering step

Copy or commit the generated scaffold files into this repository, then run the validation commands above on the Windows host at `D:\Windows\FeintSignal`.
