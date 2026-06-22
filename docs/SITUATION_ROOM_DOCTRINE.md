# FeintSignal Situation Room Doctrine

## Mission

FeintSignal maintains private awareness of major world events. It should explain what is happening, how confident the evidence is, and how political audiences frame it. It is not a military command system.

## Intelligence cycle

1. **Direction**: watchlists, regions, domains, and operator priorities define collection needs.
2. **Collection**: mock data today; approved RSS and API sources later behind the live-research gate.
3. **Processing**: normalize time, geography, source identity, political lean, and independence groups.
4. **Validation**: assess reliability, corroboration, staleness, conflicts, sensationalism, and duplicates.
5. **Analysis**: score importance, test alternative explanations, identify contested language, and separate confirmed facts from uncertainty.
6. **Dissemination**: present globe markers, dossiers, briefings, and threshold-qualified Discord alerts.
7. **Feedback**: operator notes and watchlist changes inform the next cycle.

## Analytic strategies

- **Competing perspectives**: show left, center, right, consensus, and uncertainty separately.
- **Source independence**: repeated syndication from one wire or ownership group is not independent corroboration.
- **Evidence tiers**: distinguish official, major media, local, specialist, academic, NGO, social, and unknown sources.
- **Confidence calibration**: signal importance and factual confidence are separate measurements.
- **Indicators and warnings**: track escalation, geographic spread, infrastructure, supply chains, and humanitarian effects.
- **Alternative hypotheses**: keep conflicting reports and uncertain attribution visible.
- **Bias without false balance**: document viewpoint coverage without forcing evidence into artificial symmetry.
- **Correlation discipline**: globe arcs show shared categories, never causal conclusions.

## Automation posture

The scheduler may refresh the deterministic pipeline hourly. Manual and scheduled runs cannot overlap inside the backend. Live research, LLM calls, and outbound Discord delivery require separate explicit gates. Starting automation never changes those gates.

## Discord posture

Discord is the mobile dissemination layer. Webhooks handle outbound operations today; channel IDs and bot credentials are reserved for future interactive commands. Standard alerts use `fs-breaking-alerts`; critical alerts use `fs-critical-alerts`.
