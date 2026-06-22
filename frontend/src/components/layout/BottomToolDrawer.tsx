import { useState } from "react";
import type { AgentRun, DiscordStatus, Heartbeat, SchedulerStatus } from "../../lib/types";
import { AgentStatusPanel } from "../system/AgentStatusPanel";
import { CostControlPanel } from "../system/CostControlPanel";
import { DiscordStatusPanel } from "../system/DiscordStatusPanel";
import { HeartbeatPanel } from "../system/HeartbeatPanel";
import { SchedulerPanel } from "../system/SchedulerPanel";

type ToolTab = "agents" | "heartbeat" | "cost" | "scheduler" | "discord";

interface Props {
  heartbeat: Heartbeat | null;
  runs: AgentRun[];
  discord: DiscordStatus | null;
  scheduler: SchedulerStatus | null;
  onSchedulerEnabled: (enabled: boolean) => Promise<void>;
  onDiscordTest: (channel: string) => Promise<void>;
}

export function BottomToolDrawer({ heartbeat, runs, discord, scheduler, onSchedulerEnabled, onDiscordTest }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<ToolTab>("heartbeat");
  const tabs: Array<{ id: ToolTab; label: string }> = [
    { id: "agents", label: "Agents" },
    { id: "heartbeat", label: "Heartbeat" },
    { id: "cost", label: "Cost Controls" },
    { id: "scheduler", label: "Scheduler" },
    { id: "discord", label: "Watchtower" },
  ];

  return (
    <footer className={`bottom-drawer ${expanded ? "expanded" : "collapsed"}`}>
      <div className="drawer-bar">
        <button
          className="drawer-toggle"
          type="button"
          aria-expanded={expanded}
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "Close tools" : "Open tools"}
        </button>

        {expanded ? (
          <div className="drawer-tabs" role="tablist" aria-label="System tools">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                className={activeTab === tab.id ? "active" : ""}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>
        ) : (
          <div className="drawer-summary">
            <span><span className="dot ok" />{heartbeat?.status ?? "offline"}</span>
            <span>Scheduler {scheduler?.scheduler_enabled ? "armed" : "standby"}</span>
            <span>Discord {discord?.enable_discord_send ? "on" : "safe/off"}</span>
          </div>
        )}
      </div>

      {expanded && (
        <div className="drawer-content" role="tabpanel">
          {activeTab === "agents" && <AgentStatusPanel heartbeat={heartbeat} runs={runs} />}
          {activeTab === "heartbeat" && <HeartbeatPanel heartbeat={heartbeat} lastRun={runs[0] ?? heartbeat?.last_run ?? null} />}
          {activeTab === "cost" && <CostControlPanel heartbeat={heartbeat} />}
          {activeTab === "scheduler" && <SchedulerPanel status={scheduler} onEnabled={onSchedulerEnabled} />}
          {activeTab === "discord" && <DiscordStatusPanel status={discord} onTest={onDiscordTest} />}
        </div>
      )}
    </footer>
  );
}
