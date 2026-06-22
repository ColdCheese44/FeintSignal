import { useState } from "react";
import type { Briefing, FeintEvent, FeintconStatus } from "../../lib/types";
import { SignalGlobe } from "../globe/SignalGlobe";
import { GlobeFilters } from "../globe/GlobeFilters";
import { EventFeed } from "../events/EventFeed";
import { DailyBriefing } from "../briefing/DailyBriefing";

interface Props {
  events: FeintEvent[];
  feintcon: FeintconStatus | null;
  briefing: Briefing | null;
  selectedId: string | null;
  onSelect: (event: FeintEvent) => void;
  onSelectId: (id: string) => void;
}

export function MainDashboard({ events, feintcon, briefing, selectedId, onSelect, onSelectId }: Props) {
  const [showDuplicates, setShowDuplicates] = useState(false);
  const [minSignal, setMinSignal] = useState(0);

  const visible = events
    .filter((e) => (showDuplicates ? true : !e.is_duplicate))
    .filter((e) => e.signal_score >= minSignal);

  return (
    <main className="main">
      <div className="main-left">
        <div className="panel">
          <h2>Signal Map</h2>
          <GlobeFilters
            showDuplicates={showDuplicates}
            onToggleDuplicates={setShowDuplicates}
            minSignal={minSignal}
            onMinSignal={setMinSignal}
          />
          <SignalGlobe events={visible} onSelect={onSelect} selectedId={selectedId} />
          {feintcon && (
            <p className="disclaimer">
              FEINTCON {feintcon.level} — {feintcon.label}. {feintcon.disclaimer}
            </p>
          )}
        </div>

        <div className="panel">
          <h2>Event Feed ({visible.length})</h2>
          <EventFeed events={visible} onSelect={onSelect} />
        </div>
      </div>

      <div className="main-right">
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
