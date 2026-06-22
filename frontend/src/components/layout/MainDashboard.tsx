import { lazy, Suspense, useState } from "react";
import type { Briefing, FeintEvent, FeintconStatus } from "../../lib/types";
import { GlobeFilters } from "../globe/GlobeFilters";
import { EventFeed } from "../events/EventFeed";
import { DailyBriefing } from "../briefing/DailyBriefing";

const SignalGlobe = lazy(() => import("../globe/SignalGlobe").then((module) => ({ default: module.SignalGlobe })));

interface Props {
  events: FeintEvent[];
  feintcon: FeintconStatus | null;
  briefing: Briefing | null;
  selectedId: string | null;
  onSelect: (event: FeintEvent) => void;
  onSelectId: (id: string) => void;
  categoryFilter: string | null;
  onCategoryFilter: (category: string | null) => void;
}

export function MainDashboard({ events, feintcon, briefing, selectedId, onSelect, onSelectId, categoryFilter, onCategoryFilter }: Props) {
  const [showDuplicates, setShowDuplicates] = useState(false);
  const [minSignal, setMinSignal] = useState(0);
  const [showCorrelations, setShowCorrelations] = useState(true);
  const categories = [...new Set(events.map((event) => event.category))].sort();

  const visible = events
    .filter((e) => (showDuplicates ? true : !e.is_duplicate))
    .filter((e) => e.signal_score >= minSignal)
    .filter((e) => (categoryFilter ? e.category === categoryFilter : true));

  return (
    <main className="main">
      <div className="main-left">
        <div className="panel globe-panel">
          <h2>Signal Map</h2>
          <GlobeFilters
            showDuplicates={showDuplicates}
            onToggleDuplicates={setShowDuplicates}
            minSignal={minSignal}
            onMinSignal={setMinSignal}
            categories={categories}
            categoryFilter={categoryFilter}
            onCategoryFilter={onCategoryFilter}
            showCorrelations={showCorrelations}
            onShowCorrelations={setShowCorrelations}
          />
          <Suspense fallback={<div className="globe-loading">Initializing 3D signal theater...</div>}>
            <SignalGlobe
              events={visible}
              onSelect={onSelect}
              selectedId={selectedId}
              showCorrelations={showCorrelations}
            />
          </Suspense>
          {feintcon && (
            <p className="disclaimer">
              FEINTCON {feintcon.level} — {feintcon.label}. {feintcon.disclaimer}
            </p>
          )}
        </div>

      </div>

      <div className="main-right">
        <div className="panel event-feed-panel">
          <h2>Event Feed ({visible.length})</h2>
          <EventFeed events={visible} onSelect={onSelect} />
        </div>
        <DailyBriefing briefing={briefing} onSelectEvent={onSelectId} />
        {feintcon && (
          <div className="panel">
            <h2>Readiness Detail</h2>
            <div className="kv"><span>Level</span><span>FEINTCON {feintcon.level}</span></div>
            <div className="kv"><span>High-signal</span><span>{feintcon.metrics.high_signal_events}</span></div>
            <div className="kv"><span>Critical</span><span>{feintcon.metrics.critical_events}</span></div>
            <div className="kv"><span>Regions</span><span>{feintcon.metrics.region_count}</span></div>
            <p className="disclaimer">{feintcon.rationale}</p>
          </div>
        )}
      </div>
    </main>
  );
}
