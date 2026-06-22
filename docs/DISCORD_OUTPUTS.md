# Watchtower Outputs and Routing

FeintSignal uses all 32 channels without treating every channel as an alert feed. Nine operational routes prefer webhooks; the other destinations use Watchtower's bot token and configured channel IDs. A failed webhook can fall back to Watchtower in the same channel.

## Output matrix

| Channel group | Output | Cadence |
| --- | --- | --- |
| `fs-command-center` | Command summary, FEINTCON, active-event and alert counts | Once daily |
| `fs-watchlist` | Operator-maintained priorities | Human-owned; no automatic posts |
| `fs-operator-notes` | Operator context and decisions | Human-owned; no automatic posts |
| OPS channels | Heartbeat, run result, system posture, errors, AI usage | Hourly or once daily by purpose |
| ALERTS channels | Threshold-qualified standard and critical alerts | Once per event level; repost only on escalation |
| INTEL channels | Daily brief, SITREP, and neutral/left/center/right framing | Once daily |
| REGIONS channels | Regional digest plus matching alert fanout | Daily digest; immediate alert fanout |
| DOMAINS channels | Domain digest plus matching alert fanout | Daily digest; immediate alert fanout |
| `fs-bot-errors` | Watchtower-specific delivery/runtime errors | On error |
| `fs-raw-logs` | Compact pipeline telemetry, never credentials or article dumps | Hourly when enabled |
| `fs-dev-notes` | Release and implementation notes | Manual only |

Critical alerts additionally fan out to `fs-global`. Category aliases consolidate into the established server taxonomy: geopolitics uses `fs-politics`, disaster and health use `fs-disasters-health`, and all other dashboard categories map directly to their matching domain.

## Noise controls

- The persisted alert ledger records each event, destination, and highest delivered level for seven days.
- Repeated hourly sightings do not repost. A standard alert may post again only if it becomes critical.
- Daily outputs use independent date keys, so a partial delivery can recover without duplicating successful channels.
- `DISCORD_MAX_FANOUT_PER_RUN` caps secondary alert messages.
- All messages disable automatic mention parsing.
- Embed fields and total characters are clipped below Discord's limits.

## Capability gates

```dotenv
ENABLE_DISCORD_SEND=true
ENABLE_DISCORD_FANOUT=true
ENABLE_DISCORD_DIGESTS=true
ENABLE_DISCORD_RAW_LOGS=true
DISCORD_MAX_FANOUT_PER_RUN=24
```

The template defaults every gate to `false`. The local FeintSignal `.env` enables them deliberately. Watchlist and operator-note channels remain human-owned regardless of these gates.

## Safe verification

```powershell
python scripts/send_test_discord.py --list
python scripts/send_test_discord.py domain_terrorism --dry-run
python scripts/send_test_discord.py system_status
```

A whole-server connectivity test is deliberately harder to trigger:

```powershell
python scripts/send_test_discord.py --all --confirm-all
```

That command sends one clearly labeled connectivity message to every destination. It never releases queued news alerts.
