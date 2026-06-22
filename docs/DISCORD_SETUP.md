# FeintSignal Command Center

Discord is the mobile alert layer for FeintSignal. The current MVP sends outbound webhook payloads only. It does not require a Discord bot, server ID, or channel IDs, and sending remains disabled until `ENABLE_DISCORD_SEND=true` and the selected webhook is configured.

The planned FeintSignal Discord bot is named **Watchtower**. Its name is configured now, but the bot runtime and interactive commands remain disabled until the application credentials are added and that phase is implemented.

## Server creation checklist

Create these categories and text channels in order:

- **FEINTSIGNAL COMMAND**: `fs-command-center`, `fs-watchlist`, `fs-operator-notes`
- **FEINTSIGNAL OPS**: `fs-heartbeat-log`, `fs-system-status`, `fs-agent-runs`, `fs-error-log`, `fs-cost-control`
- **FEINTSIGNAL ALERTS**: `fs-breaking-alerts`, `fs-critical-alerts`
- **FEINTSIGNAL INTEL**: `fs-daily-brief`, `fs-sitrep`, `fs-bias-framing`
- **FEINTSIGNAL REGIONS**: `fs-global`, `fs-north-america`, `fs-latin-america`, `fs-europe`, `fs-middle-east`, `fs-africa`, `fs-asia-pacific`
- **FEINTSIGNAL DOMAINS**: `fs-cyber`, `fs-conflict`, `fs-politics`, `fs-economy`, `fs-energy-supplychain`, `fs-disasters-health`, `fs-organized-crime`, `fs-terrorism`, `fs-tech-ai`
- **FEINTSIGNAL DEV/BOT**: `fs-bot-errors`, `fs-raw-logs`, `fs-dev-notes`

The machine-readable copy, purposes, environment-variable names, and future ID fields live in `config/discord_channels.json`.

## Webhooks needed now

Create webhooks only for these nine channels:

| Channel | Local `.env` variable |
| --- | --- |
| `fs-heartbeat-log` | `DISCORD_WEBHOOK_HEARTBEAT` |
| `fs-system-status` | `DISCORD_WEBHOOK_SYSTEM_STATUS` |
| `fs-agent-runs` | `DISCORD_WEBHOOK_AGENT_RUNS` |
| `fs-error-log` | `DISCORD_WEBHOOK_ERRORS` |
| `fs-cost-control` | `DISCORD_WEBHOOK_COST_CONTROL` |
| `fs-breaking-alerts` | `DISCORD_WEBHOOK_BREAKING` |
| `fs-critical-alerts` | `DISCORD_WEBHOOK_CRITICAL` |
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
- Critical alerts route directly to `fs-critical-alerts` after meeting the corroboration and score thresholds.
- Daily briefings and situation reports route to `fs-daily-brief` and `fs-sitrep`.
- Payload generation never sends by itself.
- A send requires both the global enable flag and the matching webhook.
- Webhook values are never returned by status endpoints or written to logs.
- Pipeline runs dispatch eligible alerts plus heartbeat and agent-run summaries through those gates.
- The daily briefing route sends at most once per briefing date after a successful delivery.
- Scheduler failures generate a safe error payload for `fs-error-log`, still subject to the same gates.

Generate a safe test payload with `POST /discord/test`. It defaults to dry-run mode. `GET /discord/status` reports only booleans and channel names, never URLs. The dashboard Discord panel shows all nine routes and exposes the same dry-run test.

## Channel IDs later

The `.env.example` file contains one `DISCORD_SERVER_ID` field, all nine `DISCORD_WEBHOOK_*` fields, and a unique `DISCORD_CHANNEL_*` field for every one of the 32 channels. The channel IDs are grouped by the same seven Discord categories used by the server. Populate them when the full Discord bot is implemented; the webhook MVP does not read channel IDs.

For a future bot, also add `DISCORD_SERVER_ID`, `DISCORD_APPLICATION_ID`, `DISCORD_PUBLIC_KEY`, and `DISCORD_BOT_TOKEN` locally. Do not obtain or configure a bot token yet unless bot commands are being built.

Suggested bot identities: **FS Watchtower**, **FS Heartbeat**, **FS Briefing**, **FS Alert Router**, and **FS Analyst**.
