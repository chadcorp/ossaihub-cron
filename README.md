# ossaihub-cron

Daily refresh of GitHub stars / forks / last-commit for every tool in [OSS AI Hub](https://ossaihub.com) via a free GitHub Actions cron.

## Secrets required

Set in **Settings → Secrets and variables → Actions**:

| Name | Where it comes from |
|---|---|
| `GH_READONLY_TOKEN` | github.com/settings/tokens → fine-grained token, public-repo read, 90-day expiry |
| `BASE44_UPSERT_URL` | The URL Base44 generated when it created the Tool upsert endpoint |
| `TOOLS_UPSERT_API_KEY` | The random string you pasted into the Base44 secret field |

## Manual run

Actions tab → "Refresh OSS AI Hub GitHub stars" → Run workflow.

## Schedule

06:17 UTC daily. Adjust `cron:` in `.github/workflows/refresh-stars.yml` if you want a different time.
