import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import type { FeintEvent, FeintconStatus, PerspectiveAnalysis } from "../../lib/types";
import { api } from "../../lib/api";
import { feintconColor, hostname, leanColor, primarySource, relativeTime, signalBand } from "../../lib/formatters";

const ROTATE_MS = 15000;

interface Props {
  events: FeintEvent[];
  feintcon: FeintconStatus | null;
  onExit: () => void;
}

// Full-screen, glanceable second-screen view: large type, auto-rotating top
// stories with the neutral Left/Center/Right read, a live clock, and an alert ticker.
export function PresentationMode({ events, feintcon, onExit }: Props) {
  const stories = useMemo(
    () => events.filter((e) => !e.is_duplicate).sort((a, b) => b.signal_score - a.signal_score).slice(0, 15),
    [events]
  );
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [now, setNow] = useState(() => new Date());
  const [persp, setPersp] = useState<PerspectiveAnalysis | null>(null);
  const [perspLoading, setPerspLoading] = useState(false);
  const cache = useRef<Map<string, PerspectiveAnalysis>>(new Map());
  const stageRef = useRef<HTMLElement>(null);
  const fitRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  const current = stories[index] ?? null;
  const count = Math.max(1, stories.length);
  const next = () => setIndex((i) => (i + 1) % count);
  const prev = () => setIndex((i) => (i - 1 + count) % count);

  useEffect(() => {
    if (index >= stories.length && stories.length > 0) setIndex(0);
  }, [stories.length, index]);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (paused || stories.length <= 1) return;
    const t = setTimeout(() => setIndex((i) => (i + 1) % stories.length), ROTATE_MS);
    return () => clearTimeout(t);
  }, [index, paused, stories.length]);

  // Generate (and cache) the AI Left/Center/Right analysis for one story.
  async function ensurePerspective(id: string): Promise<PerspectiveAnalysis | null> {
    const cached = cache.current.get(id);
    if (cached) return cached;
    try {
      const res = await api.generatePerspective(id);
      cache.current.set(id, res.perspective);
      return res.perspective;
    } catch {
      try {
        const p = await api.perspective(id);
        cache.current.set(id, p);
        return p;
      } catch {
        return null;
      }
    }
  }

  useEffect(() => {
    if (!current) {
      setPersp(null);
      return;
    }
    const cached = cache.current.get(current.id);
    if (cached) {
      setPersp(cached);
      setPerspLoading(false);
      return;
    }
    setPersp(null);
    setPerspLoading(true);
    let active = true;
    ensurePerspective(current.id).then((p) => {
      if (!active) return;
      setPersp(p);
      setPerspLoading(false);
    });
    return () => {
      active = false;
    };
  }, [current?.id]);

  // Prefetch the next story's analysis so the rotation is instant.
  useEffect(() => {
    if (stories.length < 2) return;
    const upcoming = stories[(index + 1) % stories.length];
    if (upcoming && !cache.current.has(upcoming.id)) {
      void ensurePerspective(upcoming.id);
    }
  }, [index, stories]);

  // Restart the rotation from the top whenever a new cycle changes the story set.
  const storySig = useMemo(() => stories.map((s) => s.id).join("|"), [stories]);
  const prevSig = useRef(storySig);
  useEffect(() => {
    if (prevSig.current !== storySig) {
      prevSig.current = storySig;
      setIndex(0);
    }
  }, [storySig]);

  // Column text: show loading only while fetching; otherwise fall back to the
  // event's own framing, then a neutral default — never a stuck "Loading…".
  const framing = current?.political_framing;
  function colText(value?: string, fallback?: string): string {
    if (perspLoading) return "Loading neutral analysis…";
    const v = (value || "").trim();
    if (v) return v;
    const f = (fallback || "").trim();
    if (f) return f;
    return "No distinct framing in the current evidence set.";
  }

  // Scale the current article so it always fits the screen without scrolling.
  useLayoutEffect(() => {
    function fit() {
      const stage = stageRef.current;
      const content = fitRef.current;
      if (!stage || !content) return;
      const style = window.getComputedStyle(stage);
      const padding = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
      const avail = stage.clientHeight - padding;
      const natural = content.scrollHeight;
      setScale(natural > avail && natural > 0 ? Math.max(0.4, avail / natural) : 1);
    }
    fit();
    const t = window.setTimeout(fit, 80);
    window.addEventListener("resize", fit);
    return () => {
      window.clearTimeout(t);
      window.removeEventListener("resize", fit);
    };
  }, [current?.id, persp, perspLoading, stories.length]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onExit();
      else if (e.key === "ArrowRight") next();
      else if (e.key === "ArrowLeft") prev();
      else if (e.key === " ") {
        e.preventDefault();
        setPaused((p) => !p);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onExit, stories.length]);

  const src = current ? primarySource(current) : null;
  const band = current ? signalBand(current.signal_score) : null;

  return (
    <div className="present-root">
      <header className="present-top">
        {feintcon && (
          <span className="present-feintcon" style={{ background: feintconColor(feintcon.level) }}>
            FEINTCON {feintcon.level}
            <small>{feintcon.label}</small>
          </span>
        )}
        <div className="present-spacer" />
        <span className="present-clock">{now.toLocaleTimeString()}</span>
        <button className="btn" onClick={prev} aria-label="Previous story">‹ Prev</button>
        <button className="btn" onClick={next} aria-label="Next story">Next ›</button>
        <button className="btn" onClick={() => setPaused((p) => !p)}>{paused ? "Play" : "Pause"}</button>
        <button className="btn" onClick={onExit} aria-label="Exit presentation">Exit ✕</button>
      </header>

      {current ? (
        <main className="present-stage" ref={stageRef}>
          <div
            className="present-fit"
            ref={fitRef}
            style={{ transform: scale < 1 ? `scale(${scale})` : undefined, transformOrigin: "top center" }}
          >
          <div className="present-counter">{index + 1} / {stories.length} · top signals</div>
          <div className="present-meta">
            {band && (
              <span className="present-signal" style={{ background: band.color }}>{current.signal_score.toFixed(0)}</span>
            )}
            <span>{current.region}</span>
            <span>·</span>
            <span>{current.category}</span>
            <span>·</span>
            <span>{relativeTime(current.published_at)}</span>
            {current.alert_level !== "none" && (
              <span className="present-alert">{current.alert_level.toUpperCase()} ALERT</span>
            )}
          </div>
          <h1 className="present-title">{current.title}</h1>
          <p className="present-lede">{persp?.neutral_assessment || current.summary}</p>
          <div className="present-cols">
            <div className="present-col" style={{ borderTopColor: leanColor("left") }}>
              <h3 style={{ color: leanColor("left") }}>What the Left says</h3>
              <p>{colText(persp?.what_the_left_says, framing?.left_frame)}</p>
            </div>
            <div className="present-col" style={{ borderTopColor: leanColor("center") }}>
              <h3 style={{ color: leanColor("center") }}>What the Center says</h3>
              <p>{colText(persp?.what_the_center_says)}</p>
            </div>
            <div className="present-col" style={{ borderTopColor: leanColor("right") }}>
              <h3 style={{ color: leanColor("right") }}>What the Right says</h3>
              <p>{colText(persp?.what_the_right_says, framing?.right_frame)}</p>
            </div>
          </div>
          {src && (
            <a className="present-source" href={src.url} target="_blank" rel="noreferrer">
              Read at {hostname(src.url) || src.name} ↗
            </a>
          )}
          <div className="present-progress" key={index}>
            <span style={{ animationDuration: `${ROTATE_MS}ms`, animationPlayState: paused ? "paused" : "running" }} />
          </div>
          </div>
        </main>
      ) : (
        <main className="present-stage">
          <div className="muted" style={{ fontSize: 28 }}>Monitoring — no active signals.</div>
        </main>
      )}

      <footer className="present-ticker" aria-hidden="true">
        <div className="present-ticker-track">
          {[...stories, ...stories].map((s, i) => (
            <span key={`${s.id}-${i}`} className="present-ticker-item">
              <b style={{ color: signalBand(s.signal_score).color }}>{s.signal_score.toFixed(0)}</b> {s.title}
            </span>
          ))}
        </div>
      </footer>
    </div>
  );
}
