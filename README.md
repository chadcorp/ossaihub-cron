# ossaihub-cron

External data pipeline for [OSS AI Hub](https://ossaihub.com). Runs as free GitHub Actions crons so Base44 stays out of the data-freshness business.

## Jobs

| Job | Schedule (UTC) | Script | Purpose |
|---|---|---|---|
| Refresh stars | 06:17 daily | `refresh-stars.mjs` | GH stars / forks / last-commit / archive flips for every tool |
| Enrich descriptions | 07:43 daily | `enrich-descriptions.mjs` | Backfills `long_description` from GitHub READMEs for tools that lack one |
| Discover tools | (separate workflow) | `discover-tools.mjs` | Nightly category-driven search for new OSS AI tools |
| Weekly digest | (separate workflow) | `generate-weekly-digest.mjs` | Curated weekly highlights |

## Secrets required

Set in **Settings → Secrets and variables → Actions**:

| Name | Where it comes from | Used by |
|---|---|---|
| `GH_READONLY_TOKEN` | github.com/settings/tokens → fine-grained token, public-repo read, 90-day expiry. (Or use the auto-provided `secrets.GITHUB_TOKEN`.) | refresh-stars, enrich-descriptions |
| `BASE44_UPSERT_URL` | The URL Base44 generated when it created the Tool upsert endpoint | refresh-stars, enrich-descriptions |
| `TOOLS_UPSERT_API_KEY` | The random string you pasted into the Base44 secret field | refresh-stars, enrich-descriptions |
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
- Both intentionally off-the-hour to dodge common cron collisions.
