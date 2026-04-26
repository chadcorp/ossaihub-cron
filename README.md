# ossaihub-cron

External data pipeline for [OSS AI Hub](https://ossaihub.com). Runs as free GitHub Actions crons so Base44 stays out of the data-freshness business.

## Jobs

| Job | Schedule (UTC) | Calls | Purpose |
|---|---|---|---|
| Refresh stars | 06:17 daily | `refresh-stars.mjs` | GH stars / forks / last-commit / archive flips for every tool |
| Enrich descriptions | 07:43 daily | `enrichBacklog` (Base44 server-side fn) | Backfills `long_description` from GitHub READMEs for tools that lack one. Server-side to dodge Base44's silent-403 upsert rate-limit. |
| Discover tools | 04:23 daily | `discover-tools.mjs` | Category-driven search for new OSS AI tools |
| Weekly digest | 09:37 Sun | `generate-weekly-digest.mjs` | Curated weekly highlights |
| Glossary v2 push | manual | `glossary-seed/v2-scripts/push_v2.py` | One-shot: pushes a pre-built `rebuilt-v2.json` to Base44 (rewrites are seeded manually, not by cron) |
| Repair enrichment | manual | `repair-urls.txt` | Re-fetch + re-normalize specific flagged URLs |
| Archive tools | manual | one-off | Bulk archive flips |

## Secrets required

Set in **Settings → Secrets and variables → Actions**:

| Name | Where it comes from | Used by |
|---|---|---|
| `GH_READONLY_TOKEN` | github.com/settings/tokens → fine-grained token, public-repo read, 90-day expiry. (Or use the auto-provided `secrets.GITHUB_TOKEN`.) | refresh-stars |
| `BASE44_UPSERT_URL` | The URL Base44 generated when it created the Tool upsert endpoint | refresh-stars |
| `TOOLS_UPSERT_API_KEY` | The random string you pasted into the Base44 secret field | refresh-stars, enrich-descriptions, glossary-v2-push |
| `DISCOVERY_SECRET`, `DISCOVERY_ENDPOINT` | Base44 discovery function + its secret | discover-tools |

## Manual run

Actions tab → pick the workflow → Run workflow.

- **Enrich descriptions** has three dispatch inputs (`limit`, `iterations`, `sleep_seconds`) for tuning a one-shot drain.

## Schedules — why these times

- 04:23 discover-tools first so any new tools land in the table before stars-refresh runs.
- 06:17 stars-refresh so archive-flips land before enrichment touches descriptions.
- 07:43 enrichment runs ~90 minutes later to avoid colliding with the stars upsert's tail of retries.
- All intentionally off-the-hour to dodge common cron collisions.

## Glossary v2 runbook

The v2 format (TL;DR + 10 sections + FAQ schema) is seeded manually — Claude
rewrites terms in conversation, the operator runs the push workflow.

Files:
- `glossary-seed/v2-scripts/merge_v2.py` — collapses per-category files into `rebuilt-v2.json`
- `glossary-seed/v2-scripts/validate_v2.py` — schema + banned-word + related-slug checks
- `glossary-seed/v2-scripts/push_v2.py` — chunked POST to `/functions/upsertGlossaryTerm`
- `glossary-seed/BASE44-PROMPT-v2.md` — one-time schema / function / UI prompt

Workflows:
- `glossary-v2-push.yml` — manual dispatch, validates + pushes `rebuilt-v2.json`

To push a fresh batch:
1. `gh workflow run glossary-v2-push.yml -f dry_run=true` — validate payload
2. `gh workflow run glossary-v2-push.yml` — push entries
3. Spot-check https://ossaihub.com/glossary/rag — expect 3 JSON-LD blocks and
   the v2 "TL;DR" / "In Plain English" sections rendering.

### Rate-limit notes (hard-won)
- Base44's `upsertGlossaryTerm` enforces 100 req/min/IP per the v2 prompt
  spec. `push_v2.py` defaults to 10 items × 12s = ~50 req/min to stay under.
- `schema_jsonld` must be a single schema.org object (flat, with @context +
  @type at top level) — Base44 injects it verbatim into one <script> tag,
  so a wrapper like `{DefinedTerm: {...}, FAQPage: {...}}` breaks Google's
  parse. `fix_jsonld_shape.py` flattens if the generator emits the wrapper.
