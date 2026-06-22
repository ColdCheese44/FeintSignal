"""FeintSignal agent pipeline.

Each agent is a small, deterministic, individually testable unit. The
``orchestrator`` chains them: collect -> normalize -> validate -> dedupe ->
score -> feintcon -> alert -> persist.
"""
