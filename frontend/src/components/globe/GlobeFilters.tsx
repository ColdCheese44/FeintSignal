interface Props {
  showDuplicates: boolean;
  onToggleDuplicates: (v: boolean) => void;
  minSignal: number;
  onMinSignal: (v: number) => void;
}

export function GlobeFilters({ showDuplicates, onToggleDuplicates, minSignal, onMinSignal }: Props) {
  return (
    <div style={{ display: "flex", gap: 16, alignItems: "center", fontSize: 12, marginBottom: 10 }}>
      <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
        <input
          type="checkbox"
          checked={showDuplicates}
          onChange={(e) => onToggleDuplicates(e.target.checked)}
        />
        Show suppressed duplicates
      </label>
      <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
        Min signal <span className="mono">{minSignal}</span>
        <input
          type="range"
          min={0}
          max={100}
          step={5}
          value={minSignal}
          onChange={(e) => onMinSignal(Number(e.target.value))}
        />
      </label>
    </div>
  );
}
