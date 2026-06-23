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
          <span>{s.signal_score.toFixed(0)}</span>
        </div>
      ))}

      {briefing.perspective_analysis?.length > 0 && (
        <div className="perspective-brief">
          <h3>Perspective analysis</h3>
          {briefing.perspective_analysis.slice(0, 3).map((analysis) => (
            <details key={analysis.event_id} className="perspective-card">
              <summary>{analysis.title}</summary>
              <Perspective label="Neutral assessment" text={analysis.neutral_assessment} />
              <Perspective label="What the Left says" text={analysis.what_the_left_says} />
              <Perspective label="What the Center says" text={analysis.what_the_center_says} />
              <Perspective label="What the Right says" text={analysis.what_the_right_says} />
              <Perspective label="Consensus" text={analysis.consensus} />
              {analysis.evidence_citations && analysis.evidence_citations.length > 0 && (
                <div className="perspective-block">
                  <strong>Evidence</strong>
                  <p>
                    {analysis.evidence_citations.map((citation, index) => (
                      <span key={citation.id}>
                        {index > 0 && " · "}
                        <a href={citation.url} target="_blank" rel="noreferrer">{citation.label}</a>
                      </span>
                    ))}
                  </p>
                </div>
              )}
              <div className="perspective-block uncertainty">
                <strong>Uncertainties</strong>
                <ul>{analysis.uncertainties.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
              <button className="btn" onClick={() => onSelectEvent(analysis.event_id)}>Open full dossier</button>
            </details>
          ))}
          <p className="disclaimer">{briefing.intelligence_method}</p>
        </div>
      )}
      <p className="disclaimer">{briefing.disclaimer}</p>
    </div>
  );
}

function Perspective({ label, text }: { label: string; text: string }) {
  return <div className="perspective-block"><strong>{label}</strong><p>{text}</p></div>;
}
