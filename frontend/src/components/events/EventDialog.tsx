import { useState } from "react";
import type { FeintEvent } from "../../lib/types";
import { api } from "../../lib/api";
import { relativeTime } from "../../lib/formatters";
import { ScorePanel } from "./ScorePanel";
import { SourcePanel } from "./SourcePanel";
import { BiasPanel } from "./BiasPanel";

interface Props {
  event: FeintEvent;
  onClose: () => void;
  onChanged: (event: FeintEvent) => void;
}

const STATUSES = ["new", "reviewing", "confirmed", "monitoring", "dismissed", "archived"];

export function EventDialog({ event, onClose, onChanged }: Props) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  async function changeStatus(status: string) {
    setBusy(true);
    try {
      const res = await api.setStatus(event.id, status);
      onChanged(res.event);
    } finally {
      setBusy(false);
    }
  }

  async function submitNote() {
    if (!note.trim()) return;
    setBusy(true);
    try {
      const res = await api.addNote(event.id, note.trim());
      setNote("");
      onChanged(res.event);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <button className="close" onClick={onClose} aria-label="Close dossier">X</button>
        <h1>{event.title}</h1>
        <div className="ec-meta" style={{ marginBottom: 12 }}>
          <span>{event.region}</span>
          {event.country && <span>· {event.country}</span>}
          <span>· {event.category}</span>
          <span>· {relativeTime(event.published_at)}</span>
          <span>· status: <strong>{event.status}</strong></span>
        </div>

        <p style={{ lineHeight: 1.5 }}>{event.summary}</p>

        <div className="dialog-grid">
          <ScorePanel event={event} />
          <BiasPanel event={event} />
        </div>

        <SourcePanel sources={event.sources} />

        <div className="panel">
          <h2>Operator</h2>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
            {STATUSES.map((s) => (
              <button
                key={s}
                className={`btn ${event.status === s ? "primary" : ""}`}
                disabled={busy}
                onClick={() => changeStatus(s)}
              >
                {s}
              </button>
            ))}
          </div>

          <div style={{ display: "flex", gap: 6 }}>
            <input
              style={{
                flex: 1,
                background: "var(--bg-3)",
                border: "1px solid var(--border)",
                color: "var(--text-0)",
                borderRadius: 5,
                padding: "5px 8px",
              }}
              placeholder="Add analyst note…"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submitNote()}
            />
            <button className="btn" onClick={submitNote} disabled={busy}>
              Add
            </button>
          </div>

          {event.notes && event.notes.length > 0 && (
            <div style={{ marginTop: 10 }}>
              {event.notes.map((n, i) => (
                <div key={i} className="kv">
                  <span>{n.author} · {relativeTime(n.created_at)}</span>
                  <span style={{ color: "var(--text-0)", fontFamily: "var(--sans)" }}>{n.text}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
