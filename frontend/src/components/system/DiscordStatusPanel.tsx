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
  const destinations = Object.values(status?.destinations ?? {});
  const deliverable = destinations.filter((destination) => destination.delivery_available).length;

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
      {status?.bot && (
        <div className="kv">
          <span>{status.bot.name} identity</span>
          <span>{status.bot.identity_configured && status.bot.server_configured ? "READY" : "INCOMPLETE"}</span>
        </div>
      )}
      {status?.bot && <div className="kv"><span>Channel IDs</span><span>{status.bot.channel_ids_configured}</span></div>}
      {destinations.length > 0 && <div className="kv"><span>Delivery coverage</span><span>{deliverable} / {destinations.length}</span></div>}
      <div className="kv"><span>Alert fanout</span><span>{status?.fanout_enabled ? "ON" : "OFF"}</span></div>
      <div className="kv"><span>Daily digests</span><span>{status?.digests_enabled ? "ON" : "OFF"}</span></div>
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
        <span>{testResult ?? `${status?.pending_alerts.filter((alert) => !alert.sent).length ?? 0} pending`}</span>
      </div>
    </div>
  );
}
