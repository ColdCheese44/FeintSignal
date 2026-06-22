import { lazy, Suspense, useState } from "react";
import type { Briefing, FeintEvent, FeintconStatus } from "../../lib/types";
import { DailyBriefing } from "../briefing/DailyBriefing";
import { EventFeed } from "../events/EventFeed";
import { GlobeFilters } from "../globe/GlobeFilters";

const SignalGlobe = lazy(() => import("../globe/SignalGlobe").then((module) => ({ default: module.SignalGlobe })));

type WorkspaceTab = "map" | "feed" | "briefing" | "readiness";

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
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("map");
  const [showDuplicates, setShowDuplicates] = useState(false);
  const [minSignal, setMinSignal] = useState(0);
  const [showCorrelations, setShowCorrelations] = useState(true);

  const eventCategories = new Set(events.map((event) => event.category));
  const preferredCategories = ["conflict", "terrorism", "crime", "cyber", "disaster", "energy", "geopolitics", "health", "politics", "technology"];
  const categories = [
    ...preferredCategories,
    ...[...eventCategories].filter((category) => !preferredCategories.includes(category)).sort(),
  ];

  const visible = events
    .filter((event) => (showDuplicates ? true : !event.is_duplicate))
    .filter((event) => event.signal_score >= minSignal)
    .filter((event) => (categoryFilter ? event.category === categoryFilter : true));

  const tabs: Array<{ id: WorkspaceTab; label: string; count?: number }> = [
    { id: "map", label: "Signal Map" },
    { id: "feed", label: "Event Feed", count: visible.length },
    { id: "briefing", label: "Daily Briefing" },
    { id: "readiness", label: "Readiness" },
  ];

  return (
    <main className="main">
      <section className="workspace" aria-label="Intelligence workspace">
        <div className="workspace-tabs" role="tablist" aria-label="Intelligence views">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              id={`workspace-tab-${tab.id}`}
              role="tab"
              aria-selected={activeTab === tab.id}
              aria-controls={`workspace-panel-${tab.id}`}
              className={activeTab === tab.id ? "active" : ""}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}{typeof tab.count === "number" ? ` (${tab.count})` : ""}
            </button>
          ))}
        </div>

        <div
          id={`workspace-panel-${activeTab}`}
          className={`workspace-view workspace-${activeTab}`}
          role="tabpanel"
          aria-labelledby={`workspace-tab-${activeTab}`}
        >
          {activeTab === "map" && (
            <div className="globe-panel">
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
            </div>
          )}

          {activeTab === "feed" && (
            <div className="workspace-scroll">
              <div className="workspace-heading">
                <h2>Event Feed</h2>
                <span>{visible.length} signals match the current map filters</span>
              </div>
              <EventFeed events={visible} onSelect={onSelect} />
            </div>
          )}

          {activeTab === "briefing" && (
            <div className="workspace-scroll briefing-tab">
              <DailyBriefing briefing={briefing} onSelectEvent={onSelectId} />
            </div>
          )}

          {activeTab === "readiness" && (
            <div className="workspace-scroll readiness-tab">
              <div className="workspace-heading">
                <h2>Readiness Detail</h2>
                <span>Internal FeintSignal posture, not an official government or military readiness level.</span>
              </div>
              {feintcon ? (
                <div className="readiness-grid">
                  <div className="readiness-hero">
                    <span>FEINTCON</span>
                    <strong>{feintcon.level}</strong>
                    <p>{feintcon.label}</p>
                  </div>
                  <div className="readiness-metrics">
                    <div className="kv"><span>High-signal events</span><span>{feintcon.metrics.high_signal_events}</span></div>
                    <div className="kv"><span>Critical events</span><span>{feintcon.metrics.critical_events}</span></div>
                    <div className="kv"><span>Active regions</span><span>{feintcon.metrics.region_count}</span></div>
                    <p>{feintcon.rationale}</p>
                    <p className="disclaimer">{feintcon.disclaimer}</p>
                  </div>
                </div>
              ) : (
                <div className="muted">Readiness data is unavailable.</div>
              )}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
