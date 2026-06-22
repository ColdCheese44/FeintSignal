# Dashboard Design

FeintSignal is a full-screen intelligence Situation Room intended for a dedicated monitor.

## Layout

- **Top status bar**: product identity, FEINTCON, capability gates, and manual pipeline control.
- **Left rail**: collapsible regions, categories, review queue, and suppressed-duplicate counts.
- **Central workspace**: a single tabbed theater with Signal Map as the default and primary view. Event Feed, Daily Briefing, and Readiness replace the map only when selected instead of competing in separate windows.
- **Bottom tool drawer**: collapses to a compact health strip. When open, Agents, Heartbeat, Cost Controls, Scheduler, and Watchtower appear one tab at a time.
- **Event dossier**: an in-app dialog with scoring, sources, political framing, operator status, and notes.

## 3D signal theater

`SignalGlobe.tsx` uses `react-globe.gl` and bundled Natural Earth country geometry, so it does not depend on remote map tiles. The globe is lazy-loaded behind the stable event contract:

```ts
interface GlobeProps {
  events: FeintEvent[];
  onSelect: (event: FeintEvent) => void;
  selectedId?: string | null;
  showCorrelations?: boolean;
}
```

Markers are sized by signal score and colored by alert posture. Alerting events pulse with rings. Category filters, including the persistent Terrorism filter, affect both the globe and event feed. Optional arcs connect same-category events across different regions; they are analytical correlations and never claims of causation.

## Perspective reporting

The daily briefing provides neutral assessment, what the left says, what the center says, what the right says, consensus, and explicit uncertainties. Missing viewpoints are labeled missing rather than invented. While `ENABLE_LLM=false`, this is deterministic synthesis from supplied event framing and source metadata.

## Responsive behavior

The desktop layout prioritizes a fixed central theater. Collapsing the left rail expands the workspace from a 240px navigation column to a 42px control strip. Below 860px, the shell becomes a single flowing column and both tab bars can scroll horizontally.

## Color language

- Signal: routine, elevated, high, critical.
- FEINTCON: 5 green through 1 red.
- Flags: review, conflicting, stale, duplicate, and social-primary.

FEINTCON is an internal FeintSignal readiness indicator, not official DEFCON.
