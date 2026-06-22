import type { Heartbeat } from "../../lib/types";

export function CostControlPanel({ heartbeat }: { heartbeat: Heartbeat | null }) {
  const gates = heartbeat?.gates ?? {};
  return (
    <div className="drawer-cell">
      <h4>Cost Controls</h4>
      <div className="kv">
        <span>Live research</span>
        <span><span className={`dot ${gates.live_research ? "on" : "off"}`} />{gates.live_research ? "ON" : "OFF"}</span>
      </div>
      <div className="kv">
        <span>LLM calls</span>
        <span><span className={`dot ${gates.llm ? "on" : "off"}`} />{gates.llm ? "ON" : "OFF"}</span>
      </div>
      <div className="kv">
        <span>External calls</span>
        <span>{gates.live_research || gates.llm ? "possible" : "none"}</span>
      </div>
      <div className="muted" style={{ fontSize: 11, marginTop: 6 }}>
        Local-first: $0 spend while gates are OFF.
      </div>
    </div>
  );
}
