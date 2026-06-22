# API and credential requirements

## Obtain now

The local MVP needs no paid data or AI API. It runs on bundled mock data.

For Discord delivery, create the nine channel webhooks listed in `DISCORD_SETUP.md`. Webhook URLs are Discord credentials even though they are not conventional API keys. Store them only in local `.env`.

## Obtain only when enabling the feature

- **One or both LLM provider keys**: `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY`. A future `dual` mode can use both for failover or cross-model comparison, but the MVP does not call either provider while `ENABLE_LLM=false`, and an LLM adapter is not implemented yet.
- **Watchtower Discord bot credentials**: application ID, public key, and bot token. These are not needed for webhook-only outbound posting and no bot runtime exists yet.
- **Live-source credentials**: none are needed for the balanced default RSS collection. The allowlisted feeds are configured in `config/live_sources.json` and remain inactive while `ENABLE_LIVE_RESEARCH=false`.

## Always required locally

- Discord server and 32 channel IDs are identifiers, not API credentials. They are optional for the current webhook MVP and have organized placeholders in `.env.example` for the future bot phase.
- Keep all capability gates false until the corresponding integration is implemented and tested.
