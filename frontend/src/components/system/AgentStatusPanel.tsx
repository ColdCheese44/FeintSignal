import type { AgentRun, Heartbeat } from "../../lib/types";

interface Props {
  heartbeat: Heartbeat | null;
  runs: AgentRun[];
}

export function AgentStatusPanel({ heartbeat, runs }: Props) {
  const agents = heartbeat?.agents ?? [];
  return (
    <div className="drawer-cell">
      <h4>Agents</h4>
      {agents.map((a) => (
        <div className="kv" key={a.name}>
          <span><span className="dot ok" />{a.name}</span>
          <span>{a.status}</span>
        </div>
      ))}
      <div className="kv" style={{ marginTop: 6 }}>
        <span>Runs recorded</span>
        <span>{runs.length}</span>
      </div>
    </div>
  );
}
