import type { AgentRun, DiscordStatus, Heartbeat, SchedulerStatus } from "../../lib/types";
import { AgentStatusPanel } from "../system/AgentStatusPanel";
import { HeartbeatPanel } from "../system/HeartbeatPanel";
import { CostControlPanel } from "../system/CostControlPanel";
import { DiscordStatusPanel } from "../system/DiscordStatusPanel";
import { SchedulerPanel } from "../system/SchedulerPanel";

interface Props {
  heartbeat: Heartbeat | null;
  runs: AgentRun[];
  discord: DiscordStatus | null;
  scheduler: SchedulerStatus | null;
  onSchedulerEnabled: (enabled: boolean) => Promise<void>;
  onDiscordTest: (channel: string) => Promise<void>;
}

export function BottomToolDrawer({ heartbeat, runs, discord, scheduler, onSchedulerEnabled, onDiscordTest }: Props) {
  return (
    <footer className="bottom-drawer">
      <AgentStatusPanel heartbeat={heartbeat} runs={runs} />
      <HeartbeatPanel heartbeat={heartbeat} lastRun={runs[0] ?? heartbeat?.last_run ?? null} />
      <CostControlPanel heartbeat={heartbeat} />
      <SchedulerPanel status={scheduler} onEnabled={onSchedulerEnabled} />
      <DiscordStatusPanel status={discord} onTest={onDiscordTest} />
    </footer>
  );
}
