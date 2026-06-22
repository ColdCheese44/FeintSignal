import type { Briefing } from "../../lib/types";

interface Props {
  briefing: Briefing | null;
  onSelectEvent: (id: string) => void;
}

export function DailyBriefing({ briefing, onSelectEvent }: Props) {
  if (!briefing) {
    return (
      <div className="panel">
        <h2>Daily Briefing</h2>
        <div className="muted">No briefing yet. Run the pipeline to generate one.</div>
      </div>
    );
  }
  return (
    <div className="panel">
      <h2>Daily Briefing · {briefing.briefing_date}</h2>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{briefing.headline}</div>
      <p style={{ fontSize: 12.5, color: "var(--text-1)" }}>{briefing.summary}</p>

      <h3 style={{ fontSize: 11, color: "var(--text-2)", textTransform: "uppercase", letterSpacing: 1 }}>
        Top signals
      </h3>
      {briefing.top_signals.map((s) => (
        <div
          key={s.id}
          className="kv"
          style={{ cursor: "pointer" }}
          onClick={() => onSelectEvent(s.id)}
        >
          <span>{s.title.slice(0, 42)}{s.title.length > 42 ? "…" : ""}</span>
          <span>{s.signal_score.toFixed(0)}{s.requires_human_review ? " ⚠" : ""}</span>
        </div>
      ))}

      {briefing.human_review_queue.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <h3 style={{ fontSize: 11, color: "var(--band-critical)", textTransform: "uppercase", letterSpacing: 1 }}>
            Review queue ({briefing.human_review_queue.length})
          </h3>
          {briefing.human_review_queue.map((q) => (
            <div key={q.id} className="kv" style={{ cursor: "pointer" }} onClick={() => onSelectEvent(q.id)}>
              <span>{q.title.slice(0, 46)}</span>
              <span>⚠</span>
            </div>
          ))}
        </div>
      )}
      <p className="disclaimer">{briefing.disclaimer}</p>
    </div>
  );
}
