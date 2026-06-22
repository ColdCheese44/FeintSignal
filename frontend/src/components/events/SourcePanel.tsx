import type { Source } from "../../lib/types";

export function SourcePanel({ sources }: { sources: Source[] }) {
  return (
    <div className="panel">
      <h2>Sources ({sources.length})</h2>
      {sources.length === 0 && <div className="muted">No sources attached.</div>}
      {sources.map((s, i) => (
        <div className="source-row" key={i}>
          <div className="sr-name">
            {s.name}{" "}
            <span className="muted" style={{ fontWeight: 400 }}>· {s.source_type}</span>
          </div>
          <div className="sr-meta">
            reliability {s.reliability_score} · lean {s.political_lean} · {s.country_of_origin} · group{" "}
            {s.independence_group}
          </div>
          <a href={s.url} target="_blank" rel="noreferrer" style={{ fontSize: 11 }}>
            {s.url}
          </a>
        </div>
      ))}
    </div>
  );
}
