import type { FeintEvent } from "../../lib/types";
import { alertColor, hostname, primarySource, relativeTime, signalBand } from "../../lib/formatters";

interface Props {
  event: FeintEvent;
  onClick: () => void;
}

export function EventCard({ event, onClick }: Props) {
  const band = signalBand(event.signal_score);
  const source = primarySource(event);
  const edge = event.alert_level !== "none" ? alertColor(event.alert_level) : band.color;

  return (
    <div className="event-card" style={{ borderLeftColor: edge }} onClick={onClick}>
      <div className="ec-head">
        <span className="signal-badge" style={{ background: band.color }}>
          {event.signal_score.toFixed(0)}
        </span>
        <span className="ec-title">{event.title}</span>
      </div>
      <div className="ec-meta">
        <span>{event.region}</span>
        <span>·</span>
        <span>{event.category}</span>
        <span>·</span>
        <span>{relativeTime(event.published_at)}</span>
        <span>·</span>
        <span>conf {event.confidence_score.toFixed(0)}</span>
      </div>
      <div className="ec-summary">{event.summary}</div>
      {source && (
        <a
          className="ec-source-link"
          href={source.url}
          target="_blank"
          rel="noreferrer"
          onClick={(e) => e.stopPropagation()}
          title={source.name}
        >
          ↗ Read at {hostname(source.url) || source.name}
        </a>
      )}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {event.alert_level !== "none" && (
          <span className="flag" style={{ background: alertColor(event.alert_level), color: "#0a0e14" }}>
            {event.alert_level.toUpperCase()} ALERT
          </span>
        )}
        {event.conflicting_reports && <span className="flag conflict">CONFLICTING</span>}
        {event.is_stale && <span className="flag stale">STALE</span>}
        {event.is_duplicate && <span className="flag dup">DUPLICATE</span>}
        {event.social_only && <span className="flag dup">SOCIAL-ONLY</span>}
        {event.tags.slice(0, 3).map((t) => (
          <span key={t} className="tag">{t}</span>
        ))}
      </div>
    </div>
  );
}
