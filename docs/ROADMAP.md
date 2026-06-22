# FeintSignal Roadmap

## Completed operational foundations

- Supervised in-process hourly scheduler with controls, overlap protection, and persisted status snapshots.
- Windows Task Scheduler option for out-of-process hourly operation.
- Offline-capable 3D globe with category filters, dossiers, alert rings, and correlation arcs.
- Deterministic perspective analysis with neutral, left, center, right, consensus, and uncertainty sections.
- Discord command-center routing and gated dispatch for alerts, operations, errors, and daily briefings.
- Full-screen desktop launcher and chromeless dashboard window.
- Allowlisted, keyless RSS collection with balanced source buckets, per-feed limits, and provenance capture.

Do not run both hourly supervision modes at once. Use the dashboard scheduler while the backend remains open, or install the Windows scheduled updater for machine-level supervision.

## Next priorities

1. An LLM provider adapter behind `ENABLE_LLM=false`, requiring citations to collected evidence and preserving deterministic fallback output.
2. Frontend automated tests for filters, dossiers, scheduler controls, and Discord dry runs.
3. Agent-run timeline with per-agent duration, retry state, and failure detail.
4. Markdown/PDF briefing export and a configurable daily delivery time.

## Guardrails

- FEINTCON remains internal and never represents official DEFCON.
- Correlation arcs never imply coordination or causation.
- Live research, LLM calls, and Discord sending remain off by default.
- Alerts remain threshold-qualified and Discord sending remains independently gated.
