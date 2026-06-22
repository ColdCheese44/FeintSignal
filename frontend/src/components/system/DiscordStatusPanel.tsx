import type { DiscordStatus } from "../../lib/types";

export function DiscordStatusPanel({ status }: { status: DiscordStatus | null }) {
  return (
    <div className="drawer-cell" style={{ borderRight: "none" }}>
      <h4>Discord</h4>
      <div className="kv">
        <span>Sending</span>
        <span>
          <span className={`dot ${status?.enable_discord_send ? "on" : "off"}`} />
          {status?.enable_discord_send ? "ENABLED" : "DISABLED"}
        </span>
      </div>
      {status &&
        Object.entries(status.channels).map(([ch, configured]) => (
          <div className="kv" key={ch}>
            <span>{ch}</span>
            <span>{configured ? "configured" : "—"}</span>
          </div>
        ))}
      <div className="kv" style={{ marginTop: 6 }}>
        <span>Pending alerts</span>
        <span>{status?.pending_alerts.length ?? 0}</span>
      </div>
      {status && status.pending_alerts.some((a) => a.requires_human_review) && (
        <div className="muted" style={{ fontSize: 11, marginTop: 4, color: "var(--band-high)" }}>
          {status.pending_alerts.filter((a) => a.requires_human_review).length} awaiting human review
        </div>
      )}
    </div>
  );
}
