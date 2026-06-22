import type { AgentRun, DiscordStatus, Heartbeat } from "../../lib/types";
import { AgentStatusPanel } from "../system/AgentStatusPanel";
import { HeartbeatPanel } from "../system/HeartbeatPanel";
import { CostControlPanel } from "../system/CostControlPanel";
import { DiscordStatusPanel } from "../system/DiscordStatusPanel";

interface Props {
  heartbeat: Heartbeat | null;
  runs: AgentRun[];
  discord: DiscordStatus | null;
}

export function BottomToolDrawer({ heartbeat, runs, discord }: Props) {
  return (
    <footer className="bottom-drawer">
      <AgentStatusPanel heartbeat={heartbeat} runs={runs} />
      <HeartbeatPanel heartbeat={heartbeat} lastRun={runs[0] ?? heartbeat?.last_run ?? null} />
      <CostControlPanel heartbeat={heartbeat} />
      <DiscordStatusPanel status={discord} />
    </footer>
  );
}
