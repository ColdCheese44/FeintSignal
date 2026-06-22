import type { FeintEvent } from "../../lib/types";

interface Props {
  events: FeintEvent[];
  regionFilter: string | null;
  onRegionFilter: (region: string | null) => void;
  categoryFilter: string | null;
  onCategoryFilter: (category: string | null) => void;
  collapsed: boolean;
  onCollapsed: (collapsed: boolean) => void;
}

export function LeftRail({ events, regionFilter, onRegionFilter, categoryFilter, onCategoryFilter, collapsed, onCollapsed }: Props) {
  const byRegion = new Map<string, number>();
  const byCategory = new Map<string, number>();
  for (const event of events) {
    if (event.is_duplicate) continue;
    byRegion.set(event.region, (byRegion.get(event.region) ?? 0) + 1);
    byCategory.set(event.category, (byCategory.get(event.category) ?? 0) + 1);
  }

  const reviewCount = events.filter((event) => event.requires_human_review).length;
  const dupCount = events.filter((event) => event.is_duplicate).length;

  return (
    <aside className={`left-rail ${collapsed ? "collapsed" : ""}`} aria-label="Signal navigation">
      <button
        className="rail-toggle"
        type="button"
        aria-expanded={!collapsed}
        aria-label={collapsed ? "Expand signal navigation" : "Collapse signal navigation"}
        onClick={() => onCollapsed(!collapsed)}
      >
        {collapsed ? ">" : "<"}
      </button>

      {!collapsed && (
        <div className="rail-content">
          <div className="rail-section">
            <h3>Feed</h3>
            <button className={`rail-item ${regionFilter === null ? "active" : ""}`} onClick={() => onRegionFilter(null)}>
              <span>All regions</span>
              <span className="count">{events.filter((event) => !event.is_duplicate).length}</span>
            </button>
            <div className="rail-summary"><span>Awaiting review</span><span className="count">{reviewCount}</span></div>
            <div className="rail-summary"><span>Suppressed dupes</span><span className="count">{dupCount}</span></div>
          </div>

          <div className="rail-section">
            <h3>Regions</h3>
            {[...byRegion.entries()].sort((a, b) => b[1] - a[1]).map(([region, count]) => (
              <button
                key={region}
                className={`rail-item ${regionFilter === region ? "active" : ""}`}
                onClick={() => onRegionFilter(regionFilter === region ? null : region)}
              >
                <span>{region}</span>
                <span className="count">{count}</span>
              </button>
            ))}
          </div>

          <div className="rail-section">
            <h3>Categories</h3>
            {[...byCategory.entries()].sort((a, b) => b[1] - a[1]).map(([category, count]) => (
              <button
                key={category}
                className={`rail-item ${categoryFilter === category ? "active" : ""}`}
                onClick={() => onCategoryFilter(categoryFilter === category ? null : category)}
              >
                <span>{category}</span>
                <span className="count">{count}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
}
