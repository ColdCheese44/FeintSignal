import type { AlertLevel, FeintEvent, Source } from "./types";

export function signalBand(score: number): { id: string; label: string; color: string } {
  if (score >= 85) return { id: "critical", label: "Critical", color: "var(--band-critical)" };
  if (score >= 75) return { id: "high", label: "High", color: "var(--band-high)" };
  if (score >= 60) return { id: "elevated", label: "Elevated", color: "var(--band-elevated)" };
  return { id: "routine", label: "Routine", color: "var(--band-routine)" };
}

export function alertColor(level: AlertLevel): string {
  if (level === "critical") return "var(--band-critical)";
  if (level === "standard") return "var(--band-high)";
  return "var(--band-routine)";
}

export function feintconColor(level: number): string {
  return (
    {
      1: "var(--feintcon-1)",
      2: "var(--feintcon-2)",
      3: "var(--feintcon-3)",
      4: "var(--feintcon-4)",
      5: "var(--feintcon-5)",
    }[level] ?? "var(--feintcon-5)"
  );
}

export function relativeTime(iso?: string | null): string {
  if (!iso) return "-";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "-";
  const deltaMinutes = Math.round((then - Date.now()) / 60000);
  const future = deltaMinutes > 0;
  const mins = Math.abs(deltaMinutes);
  if (mins < 1) return "just now";
  if (mins < 60) return future ? `in ${mins}m` : `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 48) return future ? `in ${hrs}h` : `${hrs}h ago`;
  const days = Math.round(hrs / 24);
  return future ? `in ${days}d` : `${days}d ago`;
}

export function titleCase(s: string): string {
  return s.replace(/(^|[\s-])\w/g, (m) => m.toUpperCase());
}

function isHttp(url?: string): boolean {
  return !!url && (url.startsWith("http://") || url.startsWith("https://"));
}

/** The best clickable source for an event: highest-reliability source with a valid link. */
export function primarySource(event: FeintEvent): Source | null {
  const linked = (event.sources || []).filter((s) => isHttp(s.url));
  if (linked.length === 0) return null;
  return [...linked].sort((a, b) => (b.reliability_score || 0) - (a.reliability_score || 0))[0];
}

export function hostname(url?: string): string {
  if (!isHttp(url)) return "";
  try {
    return new URL(url as string).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

/** Visual identity for a political lean column. */
export function leanColor(lean: "left" | "center" | "right"): string {
  return { left: "var(--lean-left)", center: "var(--lean-center)", right: "var(--lean-right)" }[lean];
}
