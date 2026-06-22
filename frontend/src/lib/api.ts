// Typed FeintSignal API client. All dashboard data flows through here.
import type {
  Briefing,
  DiscordStatus,
  EventsResponse,
  FeintEvent,
  FeintconStatus,
  Heartbeat,
  AgentRun,
} from "./types";

const API_BASE =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://127.0.0.1:8765";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

export const api = {
  base: API_BASE,
  health: () => request<{ status: string; config: Record<string, unknown> }>("/health"),
  events: () => request<EventsResponse>("/events"),
  event: (id: string) => request<FeintEvent>(`/events/${encodeURIComponent(id)}`),
  setStatus: (id: string, status: string) =>
    request<{ ok: boolean; event: FeintEvent }>(`/events/${encodeURIComponent(id)}/status`, {
      method: "POST",
      body: JSON.stringify({ status }),
    }),
  addNote: (id: string, text: string, author = "operator") =>
    request<{ ok: boolean; event: FeintEvent }>(`/events/${encodeURIComponent(id)}/notes`, {
      method: "POST",
      body: JSON.stringify({ text, author }),
    }),
  feintcon: () => request<FeintconStatus>("/system/feintcon"),
  heartbeat: () => request<Heartbeat>("/system/heartbeat"),
  runs: () => request<{ count: number; runs: AgentRun[] }>("/agents/runs"),
  runNow: (reason = "manual") =>
    request<{ ok: boolean; summary: string; feintcon_level: number; alerts_generated: number }>(
      "/agents/run-now",
      { method: "POST", body: JSON.stringify({ reason }) }
    ),
  latestBriefing: () => request<Briefing>("/briefings/daily/latest"),
  generateBriefing: () => request<Briefing>("/briefings/daily/generate", { method: "POST" }),
  discordStatus: () => request<DiscordStatus>("/discord/status"),
  discordTest: (channel = "system_status") =>
    request<Record<string, unknown>>("/discord/test", {
      method: "POST",
      body: JSON.stringify({ channel, dry_run: true }),
    }),
};
