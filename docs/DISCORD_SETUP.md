# Discord Setup

Discord delivery is **OFF by default** and is layered behind multiple gates.
FeintSignal generates alert payloads regardless, so you can inspect exactly what
*would* be sent without sending anything.

## Safety gates (all must pass to send)

1. `ENABLE_DISCORD_SEND=true`
2. The target channel's webhook env var is set (e.g. `DISCORD_WEBHOOK_BREAKING`)
3. The alert does **not** require human review (or has been approved)

If any gate fails, `discord_service.send` returns a status like
`{"sent": false, "reason": "discord_send_disabled"}` and nothing leaves your
machine.

## Channels

| Logical channel | Env var | Purpose |
|---|---|---|
| `heartbeat` | `DISCORD_WEBHOOK_HEARTBEAT` | Liveness pings |
| `breaking` | `DISCORD_WEBHOOK_BREAKING` | Standard/critical alerts |
| `daily_briefing` | `DISCORD_WEBHOOK_DAILY_BRIEFING` | Daily summary |
| `system_status` | `DISCORD_WEBHOOK_SYSTEM_STATUS` | Config/gate/error status |

## Configuring (locally only)

1. Copy `.env.example` to `.env` (never commit `.env`).
2. Paste your webhook URLs into the corresponding variables.
3. Set `ENABLE_DISCORD_SEND=true` **only when you intend to send**.

> Webhook URLs are secrets. FeintSignal never prints, logs, returns, or renders
> them — `config/discord_channels.json` stores only env-var *names*, never URLs.

## Testing without sending

```
POST /discord/test   { "channel": "system_status", "dry_run": true }
```

Returns the generated payload with `sent: false`. The bottom drawer's **Discord**
panel shows which channels are configured and how many alerts are pending /
awaiting review.
