import type { FeintconStatus, Heartbeat } from "../../lib/types";
import { feintconColor } from "../../lib/formatters";

interface Props {
  feintcon: FeintconStatus | null;
  heartbeat: Heartbeat | null;
  onRunNow: () => void;
  running: boolean;
}

export function TopStatusBar({ feintcon, heartbeat, onRunNow, running }: Props) {
  const gates = heartbeat?.gates ?? {};
  return (
    <header className="top-bar">
      <div className="brand">
        FeintSignal <small>local-first intelligence</small>
      </div>

      {feintcon && (
        <span
          className="feintcon-chip"
          style={{ background: feintconColor(feintcon.level) }}
          title={feintcon.disclaimer}
        >
          FEINTCON {feintcon.level}
          <span style={{ fontWeight: 400, fontSize: 11 }}>{feintcon.label}</span>
        </span>
      )}

      <div className="top-spacer" />

      <GatePill label="LIVE RESEARCH" on={!!gates.live_research} />
      <GatePill label="LLM" on={!!gates.llm} />
      <GatePill label="DISCORD SEND" on={!!gates.discord_send} />

      <button className="btn primary" onClick={onRunNow} disabled={running}>
        {running ? "Running…" : "Run pipeline now"}
      </button>
    </header>
  );
}

function GatePill({ label, on }: { label: string; on: boolean }) {
  const cls = on ? "on" : "off";
  return <span className={`gate-pill ${cls}`}>{label}: {on ? "ON" : "OFF"}</span>;
}
