import { useEffect, useMemo, useRef, useState } from "react";
import Globe, { type GlobeMethods } from "react-globe.gl";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import world from "world-atlas/countries-110m.json";
import type { FeintEvent } from "../../lib/types";

interface Props {
  events: FeintEvent[];
  onSelect: (event: FeintEvent) => void;
  selectedId?: string | null;
  showCorrelations?: boolean;
}

interface GlobePoint {
  event: FeintEvent;
  lat: number;
  lng: number;
  color: string;
  radius: number;
  altitude: number;
}

interface CorrelationArc {
  startLat: number;
  startLng: number;
  endLat: number;
  endLng: number;
  color: string;
  label: string;
}

const topology = world as unknown as Topology<{ countries: GeometryCollection<{ name: string }> }>;
const countries = feature(topology, topology.objects.countries).features;

function text(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character] ?? character);
}

function rendererColor(event: FeintEvent): string {
  if (event.alert_level === "critical") return "#e5484d";
  if (event.alert_level === "standard") return "#e0a317";
  if (event.signal_score >= 85) return "#e5484d";
  if (event.signal_score >= 75) return "#e0a317";
  if (event.signal_score >= 60) return "#4f9fe0";
  return "#5c6670";
}

function correlations(points: GlobePoint[]): CorrelationArc[] {
  const arcs: CorrelationArc[] = [];
  const byCategory = new Map<string, GlobePoint[]>();
  for (const point of points) {
    const group = byCategory.get(point.event.category) ?? [];
    group.push(point);
    byCategory.set(point.event.category, group);
  }
  for (const [category, group] of byCategory) {
    const ordered = group.sort((a, b) => b.event.signal_score - a.event.signal_score);
    for (let index = 1; index < Math.min(ordered.length, 4); index += 1) {
      if (ordered[0].event.region === ordered[index].event.region) continue;
      arcs.push({
        startLat: ordered[0].lat,
        startLng: ordered[0].lng,
        endLat: ordered[index].lat,
        endLng: ordered[index].lng,
        color: ordered[0].color,
        label: `Same-domain correlation: ${category}`,
      });
    }
  }
  return arcs;
}

export function SignalGlobe({ events, onSelect, selectedId, showCorrelations = true }: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const globeRef = useRef<GlobeMethods>();
  const [size, setSize] = useState({ width: 900, height: 500 });

  useEffect(() => {
    if (!hostRef.current) return;
    const observer = new ResizeObserver(([entry]) => {
      const width = Math.max(320, entry.contentRect.width);
      const viewportBudget = Math.max(300, window.innerHeight - 420);
      setSize({ width, height: Math.min(570, width * 0.62, viewportBudget) });
    });
    observer.observe(hostRef.current);
    return () => observer.disconnect();
  }, []);

  const points = useMemo<GlobePoint[]>(() => events
    .filter((event) => typeof event.lat === "number" && typeof event.lon === "number" && !event.is_duplicate)
    .map((event) => {
      return {
        event,
        lat: event.lat as number,
        lng: event.lon as number,
        color: rendererColor(event),
        radius: event.id === selectedId ? 0.85 : 0.45 + event.signal_score / 180,
        altitude: event.id === selectedId ? 0.1 : 0.025 + event.signal_score / 1800,
      };
    }), [events, selectedId]);

  const arcs = useMemo(() => showCorrelations ? correlations(points) : [], [points, showCorrelations]);
  const alertPoints = useMemo(() => points.filter((point) => point.event.alert_level !== "none"), [points]);

  function ready() {
    const controls = globeRef.current?.controls();
    if (controls) {
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.28;
      controls.enablePan = false;
    }
    globeRef.current?.pointOfView({ lat: 24, lng: 12, altitude: 2.05 }, 0);
  }

  return (
    <div className="globe-wrap" ref={hostRef}>
      <Globe
        ref={globeRef}
        width={size.width}
        height={size.height}
        backgroundColor="#0a0e14"
        globeImageUrl={null}
        showGlobe
        showGraticules
        showAtmosphere
        atmosphereColor="#4f9fe0"
        atmosphereAltitude={0.16}
        polygonsData={countries}
        polygonCapColor={() => "rgba(35, 55, 76, 0.92)"}
        polygonSideColor={() => "rgba(12, 20, 30, 0.9)"}
        polygonStrokeColor={() => "rgba(79, 159, 224, 0.24)"}
        polygonAltitude={0.006}
        polygonLabel={(country) => text(String((country as { properties?: { name?: string } }).properties?.name ?? ""))}
        pointsData={points}
        pointLat={(point) => (point as GlobePoint).lat}
        pointLng={(point) => (point as GlobePoint).lng}
        pointColor={(point) => (point as GlobePoint).color}
        pointRadius={(point) => (point as GlobePoint).radius}
        pointAltitude={(point) => (point as GlobePoint).altitude}
        pointResolution={16}
        pointLabel={(point) => {
          const item = (point as GlobePoint).event;
          return `<b>${text(item.title)}</b><br/>${text(item.region)} | ${text(item.category)} | Signal ${item.signal_score.toFixed(0)}`;
        }}
        onPointClick={(point) => onSelect((point as GlobePoint).event)}
        ringsData={alertPoints}
        ringLat={(point) => (point as GlobePoint).lat}
        ringLng={(point) => (point as GlobePoint).lng}
        ringColor={(point: object) => [(point as GlobePoint).color, "rgba(0,0,0,0)"]}
        ringMaxRadius={4}
        ringPropagationSpeed={1.2}
        ringRepeatPeriod={1600}
        arcsData={arcs}
        arcStartLat={(arc) => (arc as CorrelationArc).startLat}
        arcStartLng={(arc) => (arc as CorrelationArc).startLng}
        arcEndLat={(arc) => (arc as CorrelationArc).endLat}
        arcEndLng={(arc) => (arc as CorrelationArc).endLng}
        arcColor={(arc: object) => [(arc as CorrelationArc).color, "rgba(79,159,224,0.25)"]}
        arcLabel={(arc) => text((arc as CorrelationArc).label)}
        arcAltitudeAutoScale={0.35}
        arcStroke={0.35}
        arcDashLength={0.35}
        arcDashGap={0.7}
        arcDashAnimateTime={3200}
        onGlobeReady={ready}
      />
      <div className="globe-hud">
        <strong>3D SIGNAL THEATER</strong>
        <span>{points.length} active markers</span>
        <span>{arcs.length} same-domain cross-region links</span>
      </div>
      <div className="globe-top-signals" aria-label="Highest priority globe signals">
        {points.slice().sort((a, b) => b.event.signal_score - a.event.signal_score).slice(0, 4).map((point) => (
          <button key={point.event.id} onClick={() => onSelect(point.event)}>
            <span style={{ background: point.color }} />
            {point.event.title}
          </button>
        ))}
      </div>
      <div className="globe-note">
        Drag to rotate, scroll to zoom, click a marker for its dossier. Arcs indicate shared categories, not confirmed causation.
      </div>
    </div>
  );
}
