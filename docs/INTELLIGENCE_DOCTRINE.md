# FeintSignal Intelligence Doctrine

This document defines how FeintSignal treats sources, uncertainty, and the
FEINTCON readiness indicator. It is the conceptual companion to SCORING_MODEL.md.

## FEINTCON is internal — not DEFCON

> **FEINTCON is an internal FeintSignal readiness indicator. It is not an
> official government or military readiness condition.**

The interface is *DEFCON-style* in presentation only. FeintSignal never claims to
represent any official government, military, or intergovernmental posture.

| Level | Meaning |
|---|---|
| FEINTCON 5 | Normal monitoring |
| FEINTCON 4 | Elevated global noise or regional instability |
| FEINTCON 3 | Significant multi-region instability or major confirmed crisis |
| FEINTCON 2 | Severe global risk posture / cascading crisis potential |
| FEINTCON 1 | Extreme global crisis posture |

Level is derived from the count of high-signal and critical events and how many
distinct regions are in focus (see `backend/agents/feintcon_agent.py`).

## Source doctrine

- Sources carry `source_type`, `reliability_score`, `political_lean`,
  `country_of_origin`, and `independence_group`.
- **Independence** matters more than count: three outlets in one group corroborate
  less than two in different groups.
- **No real outlet is labelled** with a fixed reliability or bias in this repo.
  Mock sources are fictional and neutral; reliability values are illustrative.
- Social/unverified sources are treated as low-trust and trigger a `social_only`
  penalty when they are the *only* sourcing.

## Uncertainty and noise suppression

- Near-duplicate stories are clustered; the lower-confidence copy is suppressed.
- Conflicting reports reduce signal rather than inflate it.
- Stale information decays.

## Alert qualification

FeintSignal is a private news-awareness system. Alerts are routed automatically
after meeting deterministic score, confidence, source-quality, corroboration,
duplicate, and freshness thresholds. Standard alerts go to `fs-breaking-alerts`;
critical alerts go directly to `fs-critical-alerts`. Discord delivery still
requires the explicit global send gate and a configured webhook or Watchtower bot destination.
