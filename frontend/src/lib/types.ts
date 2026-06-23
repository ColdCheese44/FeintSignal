// Shared types mirroring the FeintSignal backend payloads.

export type AlertLevel = "none" | "standard" | "critical";

export interface Source {
  name: string;
  url: string;
  published_at?: string;
  source_type: string;
  reliability_score: number;
  political_lean: string;
  country_of_origin: string;
  independence_group: string;
}

export interface PoliticalFraming {
  left_frame?: string;
  right_frame?: string;
  contested_terms?: string[];
}

export interface Note {
  author: string;
  text: string;
  created_at: string;
}

export interface FeintEvent {
  id: string;
  title: string;
  summary: string;
  category: string;
  region: string;
  country?: string | null;
  lat?: number | null;
  lon?: number | null;
  published_at?: string | null;
  occurred_at?: string | null;
  status: string;
  tags: string[];
  sources: Source[];

  severity_score: number;
  urgency_score: number;
  confidence_score: number;
  relevance_score: number;
  source_quality_score: number;
  base_score?: number;
  penalty_total?: number;
  signal_score: number;
  feintcon_impact: number;
  score_explanation: string;

  is_duplicate: boolean;
  duplicate_of?: string | null;
  conflicting_reports: boolean;
  is_stale: boolean;
  social_only: boolean;
  sensational: boolean;
  alert_level: AlertLevel;

  political_framing?: PoliticalFraming;
  notes?: Note[];
}

export interface EventsResponse {
  count: number;
  events: FeintEvent[];
}

export interface FeintconMetrics {
  high_signal_events: number;
  critical_events: number;
  regions_in_focus: string[];
  region_count: number;
}

export interface FeintconStatus {
  level: number;
  label: string;
  rationale: string;
  disclaimer: string;
  metrics: FeintconMetrics;
  is_official_defcon: boolean;
}

export interface AgentInfo {
  name: string;
  status: string;
}

export interface Heartbeat {
  status: string;
  checked_at: string;
  mode: string;
  agents: AgentInfo[];
  last_run: AgentRun | null;
  feintcon_level: number | null;
  gates: Record<string, boolean>;
  update_interval_minutes: number;
}

export interface AgentRun {
  id?: number;
  started_at: string;
  finished_at?: string;
  status: string;
  trigger?: string;
  events_processed: number;
  duplicates: number;
  alerts_generated: number;
  feintcon_level: number | null;
  discord?: {
    attempted: number;
    sent: number;
    skipped: number;
    failed: number;
    transports: Record<string, number>;
  };
}

export interface TopSignal {
  id: string;
  title: string;
  region: string;
  category: string;
  signal_score: number;
}

export interface Briefing {
  briefing_date: string;
  generated_at: string;
  feintcon_level: number;
  feintcon_label: string;
  headline: string;
  summary: string;
  top_signals: TopSignal[];
  events_by_region: Record<string, number>;
  perspective_analysis: PerspectiveAnalysis[];
  intelligence_method: string;
  llm_analysis?: {
    requested: boolean;
    provider?: string | null;
    model?: string | null;
    status: string;
    events_requested?: number;
    events_enriched?: number;
    usage?: { input_tokens: number; output_tokens: number };
    reason?: string;
  };
  disclaimer: string;
}

export interface PerspectiveAnalysis {
  event_id: string;
  title: string;
  neutral_assessment: string;
  what_the_left_says: string;
  what_the_center_says: string;
  what_the_right_says: string;
  consensus: string;
  uncertainties: string[];
  source_balance: Record<string, number>;
  method: string;
  ai_generated?: boolean;
  evidence_citations?: { id: string; label: string; url: string }[];
  primary_url?: string | null;
}

export interface GeneratePerspectiveResponse {
  perspective: PerspectiveAnalysis;
  llm_analysis?: {
    requested: boolean;
    provider?: string | null;
    model?: string | null;
    status: string;
    reason?: string;
  };
}

export interface DiscordChannelStatus {
  channel_name: string;
  webhook_configured: boolean;
}

export interface DiscordStatus {
  enable_discord_send: boolean;
  fanout_enabled?: boolean;
  digests_enabled?: boolean;
  raw_logs_enabled?: boolean;
  bot?: {
    name: string;
    identity_configured: boolean;
    server_configured: boolean;
    channel_ids_configured: number;
    runtime: string;
  };
  channels: Record<string, DiscordChannelStatus>;
  destinations?: Record<string, DiscordChannelStatus & {
    category: string;
    bot_channel_configured: boolean;
    delivery_available: boolean;
    preferred_transport: "webhook" | "bot" | null;
  }>;
  pending_alerts: {
    event_id: string;
    alert_level: string;
    sent: boolean;
  }[];
}

export interface SchedulerStatus {
  scheduler_enabled: boolean;
  scheduler_interval_minutes: number;
  scheduler_running_now: boolean;
  scheduler_last_started_at: string | null;
  scheduler_next_run_at: string | null;
  scheduler_last_status: ({ ok: boolean; status?: string; reason?: string; error?: string } & Partial<AgentRun>) | null;
}
