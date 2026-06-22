# FeintSignal Scoring Model

Scoring is **deterministic** and pure — the same event always produces the same
score and the same `score_explanation`. The source of truth is
`backend/agents/signal_scorer.py` (`DEFAULT_SCORING_RULES`), mirrored for the UI
in `config/scoring_rules.json`.

## Component scores

Every event carries:

| Field | Meaning |
|---|---|
| `severity_score` | Magnitude / potential harm (input) |
| `urgency_score` | Time pressure (input) |
| `confidence_score` | How confirmed the event is (input) |
| `relevance_score` | Relevance to monitored topics/watchlists (input) |
| `source_quality_score` | Derived from source reliability + independence |
| `signal_score` | Final composite after penalties |
| `feintcon_impact` | Per-event contribution to global readiness |

## Source quality

```
best  = max(reliability_score over sources)
avg   = mean(reliability_score over sources)
bonus = 5 if >= 2 distinct independence_groups else 0
source_quality = clamp(best*0.6 + avg*0.4 + bonus, 0, 100)
```

## Base formula

```
signal_score =
    severity        * 0.30 +
    urgency         * 0.20 +
    confidence      * 0.25 +
    relevance       * 0.15 +
    source_quality  * 0.10
```

## Penalties (subtracted from the base)

| Penalty | Points | Trigger |
|---|---:|---|
| duplicate | 15 | flagged by the deduper |
| low_confidence | 10 | `confidence < 50` |
| conflicting_reports | 8 | sources disagree (data flag) |
| stale | 6 | `published_at` older than 72h |
| social_only | 12 | every source is type `social` |
| sensational | 5 | curated clickbait term detected |

The final `signal_score` is clamped to `[0, 100]`. Each event's
`score_explanation` spells out the base components and every applied penalty, e.g.:

```
base 81.9 = sev 85x.30 + urg 80x.20 + conf 78x.25 + rel 82x.15 + srcq 85.6x.10;
penalties [no penalties] -> signal 81.86
```

> Sensational detection is deliberately conservative: legitimate crisis
> vocabulary ("earthquake", "outbreak", "ceasefire") is **not** penalised — only
> clickbait phrasing is.

## Alert thresholds

- **Standard**: `signal >= 75` AND `confidence >= 60` AND at least one source with
  `reliability >= 70`, and not a duplicate.
- **Critical**: `signal >= 85` AND `confidence >= 75` AND (two independent sources
  OR one official source), not duplicate, not stale.

See INTELLIGENCE_DOCTRINE.md for source doctrine, uncertainty handling, and automatic alert routing.
