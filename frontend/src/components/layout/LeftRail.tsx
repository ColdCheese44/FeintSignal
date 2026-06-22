import type { FeintEvent } from "../../lib/types";

interface Props {
  events: FeintEvent[];
  regionFilter: string | null;
  onRegionFilter: (region: string | null) => void;
}

export function LeftRail({ events, regionFilter, onRegionFilter }: Props) {
  const byRegion = new Map<string, number>();
  const byCategory = new Map<string, number>();
  for (const e of events) {
    if (e.is_duplicate) continue;
    byRegion.set(e.region, (byRegion.get(e.region) ?? 0) + 1);
    byCategory.set(e.category, (byCategory.get(e.category) ?? 0) + 1);
  }

  const reviewCount = events.filter((e) => e.requires_human_review).length;
  const dupCount = events.filter((e) => e.is_duplicate).length;

  return (
    <aside className="left-rail">
      <div className="rail-section">
        <h3>Feed</h3>
        <div
          className={`rail-item ${regionFilter === null ? "active" : ""}`}
          onClick={() => onRegionFilter(null)}
        >
          <span>All regions</span>
          <span className="count">{events.filter((e) => !e.is_duplicate).length}</span>
        </div>
        <div className="rail-item">
          <span>Awaiting review</span>
          <span className="count">{reviewCount}</span>
        </div>
        <div className="rail-item">
          <span>Suppressed dupes</span>
          <span className="count">{dupCount}</span>
        </div>
      </div>

      <div className="rail-section">
        <h3>Regions</h3>
        {[...byRegion.entries()].sort((a, b) => b[1] - a[1]).map(([region, count]) => (
          <div
            key={region}
            className={`rail-item ${regionFilter === region ? "active" : ""}`}
            onClick={() => onRegionFilter(regionFilter === region ? null : region)}
          >
            <span>{region}</span>
            <span className="count">{count}</span>
          </div>
        ))}
      </div>

      <div className="rail-section">
        <h3>Categories</h3>
        {[...byCategory.entries()].sort((a, b) => b[1] - a[1]).map(([cat, count]) => (
          <div key={cat} className="rail-item">
            <span>{cat}</span>
            <span className="count">{count}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}
