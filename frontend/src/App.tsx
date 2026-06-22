import { useCallback, useEffect, useState } from "react";
import { api } from "./lib/api";
import type {
  AgentRun,
  Briefing,
  DiscordStatus,
  FeintEvent,
  FeintconStatus,
  Heartbeat,
  SchedulerStatus,
} from "./lib/types";
import { TopStatusBar } from "./components/layout/TopStatusBar";
import { LeftRail } from "./components/layout/LeftRail";
import { MainDashboard } from "./components/layout/MainDashboard";
import { BottomToolDrawer } from "./components/layout/BottomToolDrawer";
import { EventDialog } from "./components/events/EventDialog";

export default function App() {
  const [events, setEvents] = useState<FeintEvent[]>([]);
  const [feintcon, setFeintcon] = useState<FeintconStatus | null>(null);
  const [heartbeat, setHeartbeat] = useState<Heartbeat | null>(null);
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [discord, setDiscord] = useState<DiscordStatus | null>(null);
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null);

  const [regionFilter, setRegionFilter] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [selected, setSelected] = useState<FeintEvent | null>(null);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [ev, fc, hb, rn, dc, sc] = await Promise.all([
        api.events(),
        api.feintcon(),
        api.heartbeat(),
        api.runs(),
        api.discordStatus(),
        api.schedulerStatus(),
      ]);
      setEvents(ev.events);
      setFeintcon(fc);
      setHeartbeat(hb);
      setRuns(rn.runs);
      setDiscord(dc);
      setScheduler(sc);
      try {
        setBriefing(await api.latestBriefing());
      } catch {
        setBriefing(null);
      }
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to reach backend");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 30000);
    return () => clearInterval(t);
  }, [refresh]);

  async function runNow() {
    setRunning(true);
    try {
      await api.runNow("dashboard");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Run failed");
    } finally {
      setRunning(false);
    }
  }

  async function openById(id: string) {
    try {
      setSelected(await api.event(id));
    } catch {
      /* ignore */
    }
  }

  async function setSchedulerEnabled(enabled: boolean) {
    try {
      setScheduler(enabled ? await api.schedulerStart(60) : await api.schedulerStop());
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scheduler control failed");
    }
  }

  async function testDiscord(channel: string) {
    try {
      await api.discordTest(channel);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Discord dry run failed");
      throw e;
    }
  }

  const filtered = events.filter((e) => (regionFilter ? e.region === regionFilter : true));

  if (loading) {
    return <div className="loading">Connecting to FeintSignal backend at {api.base}…</div>;
  }

  return (
    <div className="app-shell">
      <TopStatusBar feintcon={feintcon} heartbeat={heartbeat} onRunNow={runNow} running={running} />

      {error && (
        <div style={{ background: "var(--band-critical)", color: "#fff", padding: "6px 16px", fontSize: 13 }}>
          {error} — is the backend running on {api.base}? (start it with scripts/run_backend.ps1)
        </div>
      )}

      <div className={`app-body ${leftCollapsed ? "rail-collapsed" : ""}`}>
        <LeftRail
          events={events}
          regionFilter={regionFilter}
          onRegionFilter={setRegionFilter}
          categoryFilter={categoryFilter}
          onCategoryFilter={setCategoryFilter}
          collapsed={leftCollapsed}
          onCollapsed={setLeftCollapsed}
        />
        <MainDashboard
          events={filtered}
          feintcon={feintcon}
          briefing={briefing}
          selectedId={selected?.id ?? null}
          onSelect={(e) => openById(e.id)}
          onSelectId={openById}
          categoryFilter={categoryFilter}
          onCategoryFilter={setCategoryFilter}
        />
      </div>

      <BottomToolDrawer
        heartbeat={heartbeat}
        runs={runs}
        discord={discord}
        scheduler={scheduler}
        onSchedulerEnabled={setSchedulerEnabled}
        onDiscordTest={testDiscord}
      />

      {selected && (
        <EventDialog
          event={selected}
          onClose={() => setSelected(null)}
          onChanged={(ev) => {
            setSelected(ev);
            refresh();
          }}
        />
      )}
    </div>
  );
}
