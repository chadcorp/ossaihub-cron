# ossaihub-cron

External data pipeline for [OSS AI Hub](https://ossaihub.com). Runs as free GitHub Actions crons so Base44 stays out of the data-freshness business.

## Jobs

| Job | Schedule (UTC) | Script | Purpose |
|---|---|---|---|
| Refresh stars | 06:17 daily | `refresh-stars.mjs` | GH stars / forks / last-commit / archive flips for every tool |
| Enrich descriptions | 07:43 daily | `enrich-descriptions.mjs` | Backfills `long_description` from GitHub READMEs for tools that lack one |
| Glossary v2 nightly | 08:34 daily | `glossary-seed/v2-scripts/rewrite_v2.py` + `push_v2.py` | Rewrites any new/missing glossary term into v2 snippet-ready format and pushes to `upsertGlossaryTerm` |
| Discover tools | (separate workflow) | `discover-tools.mjs` | Nightly category-driven search for new OSS AI tools |
| Weekly digest | (separate workflow) | `generate-weekly-digest.mjs` | Curated weekly highlights |

## Secrets required

Set in **Settings → Secrets and variables → Actions**:

| Name | Where it comes from | Used by |
|---|---|---|
| `GH_READONLY_TOKEN` | github.com/settings/tokens → fine-grained token, public-repo read, 90-day expiry. (Or use the auto-provided `secrets.GITHUB_TOKEN`.) | refresh-stars, enrich-descriptions |
| `BASE44_UPSERT_URL` | The URL Base44 generated when it created the Tool upsert endpoint | refresh-stars, enrich-descriptions |
| `TOOLS_UPSERT_API_KEY` | The random string you pasted into the Base44 secret field | refresh-stars, enrich-descriptions, **glossary-v2-push**, **glossary-v2-nightly** |
| `ANTHROPIC_API_KEY` | api.anthropic.com key (or OAuth token with Claude Code scope) | glossary-v2-nightly |
| `DISCOVERY_SECRET`, `DISCOVERY_ENDPOINT` | Base44 discovery function + its secret | discover-tools |

## Manual run

Actions tab → pick the workflow → Run workflow.

- **Enrich descriptions** has two dispatch inputs:
  - `dry_run` — `true` logs what would change without writing to Base44.
  - `max_per_run` — raise for a one-shot backfill (default 80; 175 tools clears in ~3 nightly runs at the default).

## Prerequisite for `enrich-descriptions.mjs`

The script filters unenriched tools client-side by reading `long_description` from the `toolsApiJson` Base44 function response. If the field isn't exposed there, the script aborts with an explicit error before hitting GitHub. To enable:

- Ensure the `toolsApiJson` function includes `long_description` in its returned shape (and `status` so we can filter to `approved`).

## Schedules — why these times

- 06:17 stars first so archive-flips land before anything else touches the table.
- 07:43 enrichment runs ~90 minutes later to avoid colliding with the stars upsert's tail of retries.
- 08:34 glossary v2 rewrites pull the latest snapshot and fill in any term missing v2 fields. Runs after stars + enrichment so related_tools references are against a fresh tools table.
- All intentionally off-the-hour to dodge common cron collisions.

## Glossary v2 runbook

The v2 format (TL;DR + 10 sections + FAQ schema) is built from the live
glossary. See `glossary-seed/BASE44-PROMPT-v2.md` for the one-time schema
prompt that must be published on Base44 before the push workflow can write.

Files:
- `glossary-seed/v2-scripts/rewrite_v2.py` — per-term Anthropic-API rewriter (concurrent, resumable)
- `glossary-seed/v2-scripts/merge_v2.py` — collapses per-category files into `rebuilt-v2.json`
- `glossary-seed/v2-scripts/validate_v2.py` — schema + banned-word + related-slug checks
- `glossary-seed/v2-scripts/push_v2.py` — chunked POST to `/functions/upsertGlossaryTerm`
- `glossary-seed/BASE44-PROMPT-v2.md` — one-time schema / function / UI prompt

Workflows:
- `glossary-v2-push.yml` — manual dispatch, validates + pushes `rebuilt-v2.json`
- `glossary-v2-nightly.yml` — 08:34 UTC daily: pulls snapshot, rewrites any new slug, commits, pushes

First run, after pasting the v2 Base44 prompt and clicking Publish:
1. `gh workflow run glossary-v2-push.yml -f dry_run=true` — validate payload
2. `gh workflow run glossary-v2-push.yml` — push all 526 entries
3. Spot-check https://ossaihub.com/glossary/rag — expect 3 JSON-LD blocks and
   the v2 "TL;DR" / "In Plain English" sections rendering.
