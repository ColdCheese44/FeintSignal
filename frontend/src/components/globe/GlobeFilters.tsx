interface Props {
  showDuplicates: boolean;
  onToggleDuplicates: (value: boolean) => void;
  minSignal: number;
  onMinSignal: (value: number) => void;
  categories: string[];
  categoryFilter: string | null;
  onCategoryFilter: (category: string | null) => void;
  showCorrelations: boolean;
  onShowCorrelations: (value: boolean) => void;
}

export function GlobeFilters({
  showDuplicates,
  onToggleDuplicates,
  minSignal,
  onMinSignal,
  categories,
  categoryFilter,
  onCategoryFilter,
  showCorrelations,
  onShowCorrelations,
}: Props) {
  return (
    <div className="globe-filters" aria-label="Globe intelligence filters">
      <div className="filter-row">
        <button className={`filter-chip ${categoryFilter === null ? "active" : ""}`} onClick={() => onCategoryFilter(null)}>
          All intel
        </button>
        {categories.map((category) => (
          <button
            key={category}
            className={`filter-chip ${categoryFilter === category ? "active" : ""}`}
            onClick={() => onCategoryFilter(categoryFilter === category ? null : category)}
          >
            {category}
          </button>
        ))}
      </div>
      <div className="filter-row filter-controls">
        <label>
          <input type="checkbox" checked={showDuplicates} onChange={(event) => onToggleDuplicates(event.target.checked)} />
          Suppressed duplicates
        </label>
        <label>
          <input type="checkbox" checked={showCorrelations} onChange={(event) => onShowCorrelations(event.target.checked)} />
          Cross-region correlations
        </label>
        <label className="signal-range">
          Min signal <span className="mono">{minSignal}</span>
          <input type="range" min={0} max={100} step={5} value={minSignal} onChange={(event) => onMinSignal(Number(event.target.value))} />
        </label>
      </div>
    </div>
  );
}
