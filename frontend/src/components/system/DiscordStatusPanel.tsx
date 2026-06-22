import { useState } from "react";
import type { DiscordStatus } from "../../lib/types";

interface Props {
  status: DiscordStatus | null;
  onTest: (channel: string) => Promise<void>;
}

export function DiscordStatusPanel({ status, onTest }: Props) {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);
  const routes = Object.entries(status?.channels ?? {});
  const configured = routes.filter(([, channel]) => channel.webhook_configured).length;

  async function test() {
    setTesting(true);
    try {
      await onTest("system_status");
      setTestResult("dry-run generated");
    } catch (error) {
      setTestResult(error instanceof Error ? error.message : "dry-run failed");
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="drawer-cell">
      <h4>Watchtower / Discord command center</h4>
      <div className="kv">
        <span>Sending</span>
        <span><span className={`dot ${status?.enable_discord_send ? "on" : "off"}`} />{status?.enable_discord_send ? "ENABLED" : "SAFE / OFF"}</span>
      </div>
      <div className="kv"><span>Webhook routes</span><span>{configured} / {routes.length}</span></div>
      <div className="discord-route-list">
        {routes.map(([route, channel]) => (
          <span key={route} title={route} className={channel.webhook_configured ? "configured" : ""}>
            {channel.channel_name}
          </span>
        ))}
      </div>
      <div className="drawer-actions">
        <button className="btn" onClick={test} disabled={testing}>{testing ? "Testing..." : "Dry-run status payload"}</button>
        <span>{testResult ?? `${status?.pending_alerts.filter((alert) => alert.requires_human_review).length ?? 0} review`}</span>
      </div>
    </div>
  );
}
