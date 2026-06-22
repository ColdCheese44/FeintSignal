import { useEffect, useState } from "react";
import type { FeintEvent, PerspectiveAnalysis } from "../../lib/types";
import { api } from "../../lib/api";
import { leanColor } from "../../lib/formatters";

interface Props {
  event: FeintEvent;
}

// The neutral, AI-written article view for a single event: a balanced lede,
// Left / Center / Right framing columns, consensus, open questions, and citations.
export function ArticleView({ event }: Props) {
  const [persp, setPersp] = useState<PerspectiveAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setNote(null);
    api
      .perspective(event.id)
      .then((p) => active && (setPersp(p), setLoading(false)))
      .catch(() => active && (setNote("Analysis is unavailable."), setLoading(false)));
    return () => {
      active = false;
    };
  }, [event.id]);

  async function generate() {
    setGenerating(true);
    setNote(null);
    try {
      const res = await api.generatePerspective(event.id);
      setPersp(res.perspective);
      if (res.llm_analysis?.status === "disabled") {
        setNote("AI synthesis is off (ENABLE_LLM=false) — showing deterministic analysis.");
      } else if (res.llm_analysis && res.llm_analysis.status !== "ok") {
        setNote(`AI synthesis fell back to deterministic (${res.llm_analysis.reason ?? res.llm_analysis.status}).`);
      }
    } catch {
      setNote("AI generation failed; showing the previous analysis.");
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return <div className="panel article"><div className="muted">Loading neutral analysis…</div></div>;
  }
  if (!persp) {
    return <div className="panel article"><div className="muted">{note ?? "No analysis available."}</div></div>;
  }

  const columns: Array<{ key: "left" | "center" | "right"; label: string; text: string }> = [
    { key: "left", label: "What the Left says", text: persp.what_the_left_says },
    { key: "center", label: "What the Center says", text: persp.what_the_center_says },
    { key: "right", label: "What the Right says", text: persp.what_the_right_says },
  ];

  return (
    <div className="panel article">
      <div className="article-head">
        <h2>Neutral Briefing</h2>
        <span className={`ai-badge ${persp.ai_generated ? "on" : "off"}`}>
          {persp.ai_generated ? "AI-assisted" : "Deterministic"}
        </span>
        <div style={{ flex: 1 }} />
        <button className="btn" onClick={generate} disabled={generating}>
          {generating ? "Generating…" : persp.ai_generated ? "Regenerate" : "Generate AI analysis"}
        </button>
      </div>

      <p className="article-lede">{persp.neutral_assessment || event.summary}</p>

      <div className="lean-columns">
        {columns.map((c) => (
          <div className="lean-col" key={c.key} style={{ borderTopColor: leanColor(c.key) }}>
            <h3 style={{ color: leanColor(c.key) }}>{c.label}</h3>
            <p>{c.text}</p>
          </div>
        ))}
      </div>

      <div className="article-row">
        <div className="article-block">
          <h3>Consensus</h3>
          <p>{persp.consensus}</p>
        </div>
        <div className="article-block">
          <h3>Open questions</h3>
          <ul className="uncertainty-list">
            {(persp.uncertainties || []).map((u, i) => (
              <li key={i}>{u}</li>
            ))}
          </ul>
        </div>
      </div>

      {persp.evidence_citations && persp.evidence_citations.length > 0 && (
        <div className="article-block">
          <h3>Citations</h3>
          <div className="citations">
            {persp.evidence_citations.map((c) => (
              <a key={c.id} href={c.url} target="_blank" rel="noreferrer" className="citation">
                {c.label} ↗
              </a>
            ))}
          </div>
        </div>
      )}

      {note && <p className="article-note">{note}</p>}
      <p className="disclaimer">{persp.method}</p>
    </div>
  );
}
