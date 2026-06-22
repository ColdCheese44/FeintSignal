import type { FeintEvent } from "../../lib/types";
import { alertColor, signalBand } from "../../lib/formatters";

interface Props {
  events: FeintEvent[];
  onSelect: (event: FeintEvent) => void;
  selectedId?: string | null;
}

// 2D fallback map (equirectangular). This component implements the same
// {events, onSelect} contract a future 3D globe (e.g. react-globe.gl / three.js)
// would consume, so the upgrade is a drop-in swap. See docs/DASHBOARD_DESIGN.md.
const W = 720;
const H = 360;

function project(lat: number, lon: number): [number, number] {
  const x = ((lon + 180) / 360) * W;
  const y = ((90 - lat) / 180) * H;
  return [x, y];
}

export function SignalGlobe({ events, onSelect, selectedId }: Props) {
  const plottable = events.filter(
    (e) => typeof e.lat === "number" && typeof e.lon === "number" && !e.is_duplicate
  );

  const graticule: JSX.Element[] = [];
  for (let lon = -150; lon <= 150; lon += 30) {
    const [x] = project(0, lon);
    graticule.push(<line key={`v${lon}`} x1={x} y1={0} x2={x} y2={H} stroke="var(--border)" strokeWidth={0.5} />);
  }
  for (let lat = -60; lat <= 60; lat += 30) {
    const [, y] = project(lat, 0);
    graticule.push(<line key={`h${lat}`} x1={0} y1={y} x2={W} y2={y} stroke="var(--border)" strokeWidth={0.5} />);
  }

  return (
    <div className="globe-wrap">
      <svg className="globe-svg" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Signal map">
        <rect x={0} y={0} width={W} height={H} fill="var(--bg-0)" />
        {graticule}
        {/* equator + prime meridian emphasis */}
        <line x1={0} y1={H / 2} x2={W} y2={H / 2} stroke="var(--text-2)" strokeWidth={0.6} opacity={0.5} />
        <line x1={W / 2} y1={0} x2={W / 2} y2={H} stroke="var(--text-2)" strokeWidth={0.6} opacity={0.5} />

        {plottable.map((e) => {
          const [x, y] = project(e.lat as number, e.lon as number);
          const band = signalBand(e.signal_score);
          const color = e.alert_level !== "none" ? alertColor(e.alert_level) : band.color;
          const r = 4 + (e.signal_score / 100) * 7;
          const selected = e.id === selectedId;
          return (
            <g key={e.id} onClick={() => onSelect(e)} className="globe-marker">
              {e.alert_level !== "none" && (
                <circle cx={x} cy={y} r={r + 5} fill={color} opacity={0.18} />
              )}
              <circle
                cx={x}
                cy={y}
                r={r}
                fill={color}
                stroke={selected ? "#fff" : "rgba(0,0,0,0.5)"}
                strokeWidth={selected ? 2 : 1}
              />
            </g>
          );
        })}
      </svg>
      <div className="globe-note">
        2D fallback projection · {plottable.length} active markers · 3D globe upgrade is a drop-in
        replacement (same data contract).
      </div>
    </div>
  );
}
