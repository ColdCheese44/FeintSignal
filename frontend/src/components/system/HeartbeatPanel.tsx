import type { AgentRun, Heartbeat } from "../../lib/types";
import { relativeTime } from "../../lib/formatters";

interface Props {
  heartbeat: Heartbeat | null;
  lastRun: AgentRun | null;
}

export function HeartbeatPanel({ heartbeat, lastRun }: Props) {
  return (
    <div className="drawer-cell">
      <h4>Heartbeat</h4>
      <div className="kv">
        <span>Status</span>
        <span><span className="dot ok" />{heartbeat?.status ?? "—"}</span>
      </div>
      <div className="kv">
        <span>Mode</span>
        <span>{heartbeat?.mode ?? "—"}</span>
      </div>
      <div className="kv">
        <span>Checked</span>
        <span>{relativeTime(heartbeat?.checked_at)}</span>
      </div>
      <div className="kv">
        <span>Last run</span>
        <span>{lastRun ? relativeTime(lastRun.finished_at ?? lastRun.started_at) : "—"}</span>
      </div>
      <div className="kv">
        <span>Interval</span>
        <span>{heartbeat?.update_interval_minutes ?? "—"}m</span>
      </div>
    </div>
  );
}
