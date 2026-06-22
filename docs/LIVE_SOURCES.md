# Live Source Collection

FeintSignal includes a keyless RSS collector behind `ENABLE_LIVE_RESEARCH`.
The default registry is `config/live_sources.json`; mock collection remains the
repository default.

## Balanced defaults

| Collection bucket | Feed |
| --- | --- |
| Left | The Guardian World |
| Center | BBC World |
| Right | Fox News World |
| International | Al Jazeera |
| Official | UN News |
| Specialist | ReliefWeb Updates |
| Specialist | BleepingComputer |

These buckets provide collection diversity. They are not article-level ideology
labels, truth judgments, or permanent reliability rankings. All non-official
defaults share the same structural reliability baseline; UN News uses the
official-source baseline.

## Behavior

- Each feed is fetched independently with redirects, a timeout, and a bounded item limit.
- A failed or malformed feed is skipped without stopping healthy feeds.
- If every enabled feed fails, the pipeline fails visibly instead of silently substituting mock data.
- RSS and Atom are supported.
- Article URL, publication time, publisher identity, source type, perspective bucket, and independence group are preserved.
- Topic and region are inferred deterministically from conservative keyword maps.
- Duplicate suppression and the existing scoring pipeline run after collection.
- Discord delivery remains controlled separately by `ENABLE_DISCORD_SEND`.

## Enabling locally

1. Keep `ENABLE_DISCORD_SEND=false`.
2. Run the live collector smoke test.
3. Set `ENABLE_LIVE_RESEARCH=true` only after the smoke test passes.
4. Run the pipeline and inspect the dashboard before enabling any outbound delivery.
