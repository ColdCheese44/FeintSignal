import type { SchedulerStatus } from "../../lib/types";
import { relativeTime } from "../../lib/formatters";

interface Props {
  status: SchedulerStatus | null;
  onEnabled: (enabled: boolean) => Promise<void>;
}

export function SchedulerPanel({ status, onEnabled }: Props) {
  const enabled = status?.scheduler_enabled ?? false;
  return (
    <div className="drawer-cell">
      <h4>Hourly supervisor</h4>
      <div className="kv"><span>State</span><span><span className={`dot ${enabled ? "ok" : "off"}`} />{enabled ? "ARMED" : "STANDBY"}</span></div>
      <div className="kv"><span>Cadence</span><span>{status?.scheduler_interval_minutes ?? 60} min</span></div>
      <div className="kv"><span>Running now</span><span>{status?.scheduler_running_now ? "YES" : "NO"}</span></div>
      <div className="kv"><span>Next run</span><span>{status?.scheduler_next_run_at ? relativeTime(status.scheduler_next_run_at) : "-"}</span></div>
      <button className={`btn ${enabled ? "" : "primary"}`} onClick={() => onEnabled(!enabled)}>
        {enabled ? "Stop scheduler" : "Start hourly scheduler"}
      </button>
    </div>
  );
}
