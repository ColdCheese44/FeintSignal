# FeintSignal Command Center

Discord is the mobile dissemination layer for FeintSignal. Nine operational routes prefer webhooks, while Watchtower uses its bot token and channel IDs for the remaining destinations. Sending remains controlled by `ENABLE_DISCORD_SEND`.

The FeintSignal Discord bot is named **Watchtower**. Outbound bot delivery is active; a persistent Discord Gateway process and interactive slash commands are intentionally deferred.

## Recommended Watchtower permissions

For an informational text bot, keep the role narrowly scoped:

- Required: **View Channels**, **Send Messages**, **Embed Links**, **Read Message History**, and **Use Slash Commands**.
- Optional: **Attach Files** for future reports and **Add Reactions** for lightweight controls.
- Enable thread permissions only when a thread-based feature is implemented.
- Remove TTS, voice, soundboard, embedded activities, polls, external emoji/sticker, server-insight, moderation, role, channel-management, and webhook-management permissions. They are not used by FeintSignal.

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

## Webhook-first routes

These nine channels prefer webhooks and fall back to Watchtower when the bot channel is configured:

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
6. Use `python scripts/send_test_discord.py <route> --dry-run` before enabling delivery.
7. Set `ENABLE_DISCORD_SEND=true` deliberately after verification.

Never paste webhook URLs into JSON, docs, screenshots, issues, commits, or chat. Never commit `.env`.

## Routing and safety

- Heartbeats route to `fs-heartbeat-log`; service status routes to `fs-system-status`.
- Agent summaries, errors, and cost warnings route to their matching OPS channels.
- Standard alerts route to `fs-breaking-alerts`.
- Critical alerts route directly to `fs-critical-alerts` after meeting the corroboration and score thresholds.
- Alerts fan out once to their matching region and domain; critical alerts also reach `fs-global`.
- Daily briefings, situation reports, bias framing, regional digests, and domain digests populate the intelligence channels once per day.
- Payload generation never sends by itself.
- A send requires the global enable flag plus a matching webhook or Watchtower bot destination.
- Webhook values are never returned by status endpoints or written to logs.
- Pipeline runs dispatch eligible alerts plus heartbeat and agent-run summaries through those gates.
- The daily briefing route sends at most once per briefing date after a successful delivery.
- Scheduler failures generate a safe error payload for `fs-error-log`, still subject to the same gates.

Generate a safe test payload with `POST /discord/test`. It defaults to dry-run mode. `GET /discord/status` reports transport readiness for all 32 destinations without returning URLs, IDs, or tokens. The full output matrix and noise controls are documented in [DISCORD_OUTPUTS.md](DISCORD_OUTPUTS.md).

## Bot identity and channel IDs

The `.env.example` file contains one `DISCORD_SERVER_ID` field, all nine `DISCORD_WEBHOOK_*` fields, and a unique `DISCORD_CHANNEL_*` field for every one of the 32 channels. The local `.env` now has these identifiers populated. The status API reports configuration counts only and never returns the values.

`DISCORD_APPLICATION_ID`, `DISCORD_PUBLIC_KEY`, and `DISCORD_BOT_TOKEN` are configured locally. The token now supports outbound delivery to bot-first channels; the application ID and public key remain ready for the future interactive-command phase.

Suggested bot identities: **FS Watchtower**, **FS Heartbeat**, **FS Briefing**, **FS Alert Router**, and **FS Analyst**.
