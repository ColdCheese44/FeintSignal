# API and credential requirements

## Obtain now

The local MVP needs no paid data or AI API. It runs on bundled mock data.

For Discord delivery, create the ten channel webhooks listed in `DISCORD_SETUP.md`. Webhook URLs are Discord credentials even though they are not conventional API keys. Store them only in local `.env`.

## Obtain only when enabling the feature

- **One LLM provider key**: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`. The MVP does not call either provider while `ENABLE_LLM=false`, and an LLM adapter is not implemented yet.
- **Discord bot credentials**: application ID, public key, and bot token. These are not needed for webhook-only outbound posting and no bot runtime exists yet.
- **Live-source credentials**: none are currently supported. The live collector intentionally stops if `ENABLE_LIVE_RESEARCH=true`; do not purchase or add a news API until that collector is selected and implemented. Keyless RSS or GDELT ingestion can be evaluated first.

## Always required locally

- Discord server and channel IDs are identifiers, not API credentials. They are optional for the current webhook MVP and have organized placeholders in `.env.example` for the future bot phase.
- Keep all capability gates false until the corresponding integration is implemented and tested.
