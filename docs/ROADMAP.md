# FeintSignal Roadmap

## Completed operational foundations

- Supervised in-process hourly scheduler with controls, overlap protection, and persisted status snapshots.
- Windows Task Scheduler option for out-of-process hourly operation.
- Offline-capable 3D globe with category filters, dossiers, alert rings, and correlation arcs.
- Deterministic perspective analysis with neutral, left, center, right, consensus, and uncertainty sections.
- Discord command-center routing and gated dispatch for alerts, operations, errors, and daily briefings.
- Full-screen desktop launcher and chromeless dashboard window.

Do not run both hourly supervision modes at once. Use the dashboard scheduler while the backend remains open, or install the Windows scheduled updater for machine-level supervision.

## Next priorities

1. RSS and live-source ingestion behind `ENABLE_LIVE_RESEARCH=false`, with allowlists, rate limits, and provenance capture.
2. An LLM provider adapter behind `ENABLE_LLM=false`, requiring citations to collected evidence and preserving deterministic fallback output.
3. Frontend automated tests for filters, dossiers, scheduler controls, and Discord dry runs.
4. Human-review approval and acknowledgement with operator identity and audit history.
5. Agent-run timeline with per-agent duration, retry state, and failure detail.
6. Markdown/PDF briefing export and a configurable daily delivery time.

## Guardrails

- FEINTCON remains internal and never represents official DEFCON.
- Correlation arcs never imply coordination or causation.
- Live research, LLM calls, and Discord sending remain off by default.
- Sensitive or critical claims remain review-gated.
