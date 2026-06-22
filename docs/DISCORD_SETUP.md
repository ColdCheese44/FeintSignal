# FeintSignal Discord Command Center

Discord is the mobile alert layer for FeintSignal. The current MVP sends outbound webhook payloads only. It does not require a Discord bot, server ID, or channel IDs, and sending remains disabled until `ENABLE_DISCORD_SEND=true` and the selected webhook is configured.

## Server creation checklist

Create these categories and text channels in order:

- **FEINTSIGNAL COMMAND**: `fs-command-post`, `fs-human-review`, `fs-watchlist`, `fs-operator-notes`
- **FEINTSIGNAL OPS**: `fs-heartbeat-log`, `fs-system-status`, `fs-agent-runs`, `fs-error-log`, `fs-cost-control`
- **FEINTSIGNAL ALERTS**: `fs-breaking-alerts`, `fs-critical-alerts`, `fs-monitoring`, `fs-escalated`
- **FEINTSIGNAL INTEL**: `fs-daily-brief`, `fs-sitrep`, `fs-source-review`, `fs-bias-framing`, `fs-research-queue`
- **FEINTSIGNAL REGIONS**: `fs-global`, `fs-north-america`, `fs-latin-america`, `fs-europe`, `fs-middle-east`, `fs-africa`, `fs-asia-pacific`
- **FEINTSIGNAL DOMAINS**: `fs-cyber`, `fs-conflict`, `fs-politics`, `fs-economy`, `fs-energy-supplychain`, `fs-disasters-health`, `fs-crime-cartels`, `fs-tech-ai`
- **FEINTSIGNAL DEV/BOT**: `fs-bot-errors`, `fs-raw-logs`, `fs-dev-notes`

The machine-readable copy, purposes, environment-variable names, and future ID fields live in `config/discord_channels.json`.

## Webhooks needed now

Create webhooks only for these ten channels:

| Channel | Local `.env` variable |
| --- | --- |
| `fs-heartbeat-log` | `DISCORD_WEBHOOK_HEARTBEAT` |
| `fs-system-status` | `DISCORD_WEBHOOK_SYSTEM_STATUS` |
| `fs-agent-runs` | `DISCORD_WEBHOOK_AGENT_RUNS` |
| `fs-error-log` | `DISCORD_WEBHOOK_ERRORS` |
| `fs-cost-control` | `DISCORD_WEBHOOK_COST_CONTROL` |
| `fs-breaking-alerts` | `DISCORD_WEBHOOK_BREAKING` |
| `fs-critical-alerts` | `DISCORD_WEBHOOK_CRITICAL` |
| `fs-human-review` | `DISCORD_WEBHOOK_HUMAN_REVIEW` |
| `fs-daily-brief` | `DISCORD_WEBHOOK_DAILY_BRIEF` |
| `fs-sitrep` | `DISCORD_WEBHOOK_SITREP` |

### Create each webhook

1. Open the target channel in Discord.
2. Select **Edit Channel > Integrations > Webhooks > New Webhook**.
3. Name it for the route, such as `FS Heartbeat`.
4. Copy the webhook URL.
5. Copy `.env.example` to `.env` locally and paste the URL after the matching variable.
6. Leave `ENABLE_DISCORD_SEND=false` while testing payload generation.
7. After dry-run verification, set `ENABLE_DISCORD_SEND=true` deliberately.

Never paste webhook URLs into JSON, docs, screenshots, issues, commits, or chat. Never commit `.env`.

## Routing and safety

- Heartbeats route to `fs-heartbeat-log`; service status routes to `fs-system-status`.
- Agent summaries, errors, and cost warnings route to their matching OPS channels.
- Standard alerts route to `fs-breaking-alerts`.
- Critical alerts route to `fs-critical-alerts` only after they pass review policy.
- Review-gated critical claims route to `fs-human-review` and remain marked `requires_human_review`.
- Daily briefings and situation reports route to `fs-daily-brief` and `fs-sitrep`.
- Payload generation never sends by itself.
- A send requires both the global enable flag and the matching webhook.
- Webhook values are never returned by status endpoints or written to logs.

Generate a safe test payload with `POST /discord/test`. It defaults to dry-run mode. `GET /discord/status` reports only booleans and channel names, never URLs.

## Channel IDs later

The `.env.example` file already contains empty `DISCORD_CHANNEL_*` fields for command, review, monitoring, intel, all region channels, all domain channels, and all DEV/BOT channels. Populate those only when a full Discord bot is implemented. The webhook MVP does not read them.

For a future bot, also add `DISCORD_SERVER_ID`, `DISCORD_APPLICATION_ID`, `DISCORD_PUBLIC_KEY`, and `DISCORD_BOT_TOKEN` locally. Do not obtain or configure a bot token yet unless bot commands are being built.

Suggested bot identities: **FS Watchtower**, **FS Heartbeat**, **FS Briefing**, **FS Alert Router**, and **FS Analyst**.
