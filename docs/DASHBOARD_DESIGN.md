# Dashboard Design

A full-screen, dark, tactical SOC/intelligence layout. Functional MVP first —
styling is intentionally restrained so progress is measured in working features,
not pixel polish.

## Layout

```
┌──────────────────────────── TopStatusBar ────────────────────────────┐
│ Brand · FEINTCON chip · gate pills (live/llm/discord/review) · Run    │
├──────────┬────────────────────────────────────────────────────────────┤
│ LeftRail │  MainDashboard                                              │
│  feed    │   ┌── Signal Map (2D globe) ──┐  ┌── Daily Briefing ──┐     │
│  regions │   │ equirectangular markers   │  │ headline + top     │     │
│  cats    │   └───────────────────────────┘  │ signals + review   │     │
│          │   ┌── Event Feed ─────────────┐  └────────────────────┘     │
│          │   │ EventCards (click → modal)│  ┌── Readiness detail ─┐    │
│          │   └───────────────────────────┘  └─────────────────────┘    │
├──────────┴────────────────────────────────────────────────────────────┤
│ BottomToolDrawer:  Agents │ Heartbeat │ Cost Controls │ Discord        │
└────────────────────────────────────────────────────────────────────────┘
```

The **EventDialog** modal shows the full ScorePanel (component bars +
explanation), BiasPanel (framing/leans), SourcePanel, and operator controls
(status buttons + analyst notes).

## Globe: 2D now, 3D later

`SignalGlobe.tsx` is a 2D equirectangular SVG fallback. It defines the data
contract a future 3D globe will consume:

```ts
interface GlobeProps {
  events: FeintEvent[];          // markers come from lat/lon
  onSelect: (e: FeintEvent) => void;
  selectedId?: string | null;
}
```

To upgrade to 3D (e.g. `react-globe.gl` / three.js), implement a new component
with the **same props** and swap it in `MainDashboard.tsx`. No other code needs
to change — markers, selection, and filtering already flow through this contract.

Markers are sized by `signal_score` and coloured by alert level (falling back to
signal band). Alerting events get a soft halo.

## Color language

- Signal bands: routine → elevated → high → critical.
- FEINTCON: 5 green → 1 red.
- Flags: REVIEW (red), CONFLICTING (orange), STALE (amber), DUPLICATE/SOCIAL-ONLY
  (grey).

## Data flow

All data flows through the typed client in `src/lib/api.ts`. The app polls every
30s and after every mutation (status change, note, run-now).
