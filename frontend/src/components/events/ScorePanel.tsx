import type { FeintEvent } from "../../lib/types";

function Bar({ label, value }: { label: string; value: number }) {
  return (
    <div className="score-bar-row">
      <span className="muted">{label}</span>
      <span className="score-track">
        <span className="score-fill" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
      </span>
      <span className="mono">{value.toFixed(0)}</span>
    </div>
  );
}

export function ScorePanel({ event }: { event: FeintEvent }) {
  return (
    <div className="panel">
      <h2>Signal Score · {event.signal_score.toFixed(1)}</h2>
      <Bar label="Severity" value={event.severity_score} />
      <Bar label="Urgency" value={event.urgency_score} />
      <Bar label="Confidence" value={event.confidence_score} />
      <Bar label="Relevance" value={event.relevance_score} />
      <Bar label="Source quality" value={event.source_quality_score} />
      <div className="kv" style={{ marginTop: 8 }}>
        <span>Base score</span>
        <span>{(event.base_score ?? 0).toFixed(2)}</span>
      </div>
      <div className="kv">
        <span>Penalties</span>
        <span>-{(event.penalty_total ?? 0).toFixed(2)}</span>
      </div>
      <div className="kv">
        <span>FEINTCON impact</span>
        <span>{event.feintcon_impact.toFixed(1)}</span>
      </div>
      <p className="disclaimer">{event.score_explanation}</p>
    </div>
  );
}
