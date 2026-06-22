# API and credential requirements

## Configured now

- **Anthropic**: `ANTHROPIC_API_KEY` is configured and `LLM_PROVIDER=anthropic` selects it for evidence-bound briefing synthesis. The default model is `claude-sonnet-4-6`.
- **OpenAI**: `OPENAI_API_KEY` is configured and its model catalog authenticates, but generation currently returns `insufficient_quota`. Keep `LLM_PROVIDER=anthropic` until OpenAI API billing or credits are available. The configured OpenAI model is `gpt-5-mini`.
- **Discord**: Watchtower's application ID, public key, bot token, server ID, all 32 channel IDs, and nine outbound webhook routes are configured locally.
- **Live news**: the balanced default collector uses keyless RSS feeds, so no news API subscription is required.

All values remain in ignored local `.env`. Run `python scripts/check_integrations.py --live` for a read-only credential, model-catalog, and Discord-access check; the report never prints tokens, IDs, keys, or webhook URLs. Catalog access confirms authentication, not generation quota.

## No additional API required for the next phase

The current collection, Anthropic synthesis, dashboard, scheduler, and webhook delivery do not need another credential. Add OpenAI API credits only if OpenAI fallback is desired. Optional paid news/search APIs can be evaluated later only if the keyless source set develops a measurable coverage gap.

## Runtime notes

- `ENABLE_LLM=true` permits a single bounded provider request over the top `LLM_MAX_EVENTS` signals. Provider failure preserves the deterministic briefing.
- `ENABLE_LIVE_RESEARCH=true` permits the allowlisted RSS collector.
- `ENABLE_DISCORD_SEND=false` still prevents all outbound Discord messages. Turn it on only when automatic mobile posting is desired.
- Watchtower's bot token is used for outbound posts to bot-first channels. A persistent Discord Gateway connection is still deferred until interactive slash commands are implemented.
