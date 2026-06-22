import type { AlertLevel } from "./types";

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
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const mins = Math.round((Date.now() - then) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 48) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}

export function titleCase(s: string): string {
  return s.replace(/(^|[\s-])\w/g, (m) => m.toUpperCase());
}
