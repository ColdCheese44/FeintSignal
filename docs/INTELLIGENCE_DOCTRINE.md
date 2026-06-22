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

## Human review before critical alerts

Even when an alert qualifies, the following claim types **must** be reviewed by a
human operator before any Discord send:

- war-start / escalation claims
- terrorism claims
- mass-casualty claims
- cyberattack attribution
- election-interference claims
- disease-outbreak claims
- nuclear / strategic-weapon claims
- assassination / coup claims
- social-media-primary claims
- anything likely to cause panic if wrong

With `REQUIRE_HUMAN_REVIEW_FOR_CRITICAL=true` (the default), **all** critical
alerts are additionally gated behind human review. This is a safety-first posture:
the system is designed to under-alert rather than spread an unverified claim.
