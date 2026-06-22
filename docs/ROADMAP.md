# FeintSignal Roadmap

The MVP is a complete, validated, local-first scaffold. The items below are the
prioritised next steps, each kept behind a safety gate where relevant.

## 1. True hourly scheduler hardening
`services/scheduler_service.py` is a simple `threading.Timer` loop, OFF by
default. Harden it: process supervision, overlap protection, jittered backoff,
persisted last-run state, and a clean start/stop API surfaced in the UI. Pair
with `scripts/hourly_update.py` + Windows Task Scheduler for an out-of-process
option.

## 2. Dashboard-visible agent run history refresh
The bottom drawer shows run counts and heartbeat; surface the full
`/agents/runs` history (timeline, per-run deltas, alert counts) with live refresh
and a manual "refresh now" affordance distinct from "run now".

## 3. 3D globe upgrade
Replace the 2D `SignalGlobe` with a three.js / react-globe.gl implementation
behind the **same `{events, onSelect, selectedId}` contract**. Add arcs for
cross-region linkage and a day/night terminator.

## 4. RSS / live source ingestion (behind `ENABLE_LIVE_RESEARCH=false`)
Implement a real collector for RSS/Atom and selected APIs. Must stay OFF by
default, respect robots/rate limits, normalise into the existing event schema,
and never bypass source validation or human-review gates.

## 5. Frontend smoke tests
Add Vitest + React Testing Library coverage for the API client, formatters, and
key components (EventCard flags, ScorePanel math, SignalGlobe projection), plus a
Playwright happy-path against a seeded backend.

## Further out
- Optional LLM summarisation of briefings behind `ENABLE_LLM=false`.
- Per-watchlist relevance boosting (config already present in `watchlists.json`).
- Alert acknowledgement / approval workflow with audit trail.
- Export (PDF/Markdown) of the daily briefing.
