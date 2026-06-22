import type { FeintEvent } from "../../lib/types";

export function BiasPanel({ event }: { event: FeintEvent }) {
  const framing = event.political_framing;
  const leans = Array.from(new Set(event.sources.map((s) => s.political_lean)));

  return (
    <div className="panel">
      <h2>Bias &amp; Framing</h2>
      <div className="kv">
        <span>Source leans</span>
        <span>{leans.join(", ") || "—"}</span>
      </div>
      <div className="kv">
        <span>Conflicting reports</span>
        <span>{event.conflicting_reports ? "yes" : "no"}</span>
      </div>
      {framing ? (
        <div style={{ marginTop: 8 }}>
          {framing.left_frame && (
            <p style={{ margin: "4px 0", fontSize: 12.5 }}>
              <strong className="muted">What the Left says:</strong> {framing.left_frame}
            </p>
          )}
          {framing.right_frame && (
            <p style={{ margin: "4px 0", fontSize: 12.5 }}>
              <strong className="muted">What the Right says:</strong> {framing.right_frame}
            </p>
          )}
          {framing.contested_terms && framing.contested_terms.length > 0 && (
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>
              {framing.contested_terms.map((t) => (
                <span className="tag" key={t}>{t}</span>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="muted" style={{ marginTop: 8, fontSize: 12 }}>
          No explicit political framing detected for this event.
        </div>
      )}
    </div>
  );
}
