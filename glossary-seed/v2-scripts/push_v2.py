"""
Push rebuilt-v2 glossary entries to Base44 via /functions/upsertGlossaryTerm.

Reads rebuilt-v2.json (merged output). Chunks 25/request, 8s between chunks to
stay below Base44's rate-limit ceiling (same pattern as refresh-stars). Retries
5xx + 500-wrapped 429s. Idempotent — re-runs just update.

Usage:
  API_KEY=$TOOLS_UPSERT_API_KEY python push_v2.py [--file ../rebuilt-v2.json]
  API_KEY=... DRY_RUN=true python push_v2.py --only ab-test-llm,eval-harness

Env:
  API_KEY           required (TOOLS_UPSERT_API_KEY from GitHub secrets)
  UPSERT_URL        override default endpoint
  CHUNK             default 25
  INTER_BATCH_MS    default 8000
  DRY_RUN           "true" to skip actual POST
"""

import argparse
import json
import os
import pathlib
import random
import sys
import time
import urllib.error
import urllib.request

DEFAULT_URL = "https://base44.app/api/apps/69a91ff6770c8ca0347ae03d/functions/upsertGlossaryTerm"


def post_with_retry(url, api_key, body_bytes, attempts=10):
    last = ""
    last_status = 0
    for i in range(attempts):
        req = urllib.request.Request(
            url,
            data=body_bytes,
            headers={"Content-Type": "application/json", "API_KEY": api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.status, json.loads(r.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as e:
            last_status = e.code
            last = ""
            try:
                last = e.read().decode("utf-8")[:500]
            except Exception:
                pass
            is_rate = e.code == 429 or "429" in last or "rate limit" in last.lower()
            if 500 <= e.code < 600 or e.code == 429:
                base_wait = 20.0 if is_rate else 1.0
                wait = min(120.0, base_wait * (1.7 ** i)) + random.uniform(0, 1)
                print(f"  retry {i+1}/{attempts} in {wait:.1f}s ({e.code}{' rate-limit' if is_rate else ''}) body={last[:150]}", flush=True)
                time.sleep(wait)
                continue
            raise RuntimeError(f"{e.code}: {last}")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            wait = min(30.0, 1.0 * (2 ** i)) + random.uniform(0, 1)
            time.sleep(wait)
    raise RuntimeError(f"{last_status} after {attempts} retries. Last: {last}")


def sanitize_for_upsert(rec):
    """Return only v2 fields the upsert function cares about. Drop internal meta."""
    allowed = {
        "slug", "title", "category", "difficulty_tier",
        "tldr", "plain_english", "how_it_works", "why_it_matters",
        "example", "pitfalls", "when_use", "when_avoid",
        "related_terms", "related_tools", "related_prompts",
        "faq", "meta_title", "meta_description", "seo_variations",
        "schema_jsonld",
        # legacy compatibility — keep short_definition in sync with tldr so
        # any v1-only code paths still show something
        "short_definition", "full_explanation", "common_misconceptions",
    }
    out = {k: v for k, v in rec.items() if k in allowed}
    # back-compat aliases: mirror tldr into short_definition so v1 card renders still work
    if "tldr" in out and "short_definition" not in out:
        out["short_definition"] = out["tldr"]
    if "how_it_works" in out and "full_explanation" not in out:
        # join how_it_works + why_it_matters so legacy readers get content
        out["full_explanation"] = out["how_it_works"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=str(pathlib.Path(__file__).parent.parent / "rebuilt-v2.json"))
    ap.add_argument("--only", default="", help="comma-separated slug subset")
    # Chunk size × rate per chunk must stay under Base44's per-IP ceiling
    # (prompt specified 100 req/min at the function level). 10 items @ 12s =
    # 50 req/min, well under.
    ap.add_argument("--chunk", type=int, default=int(os.environ.get("CHUNK", "10")))
    ap.add_argument("--inter-batch-ms", type=int, default=int(os.environ.get("INTER_BATCH_MS", "12000")))
    ap.add_argument("--dry-run", action="store_true", default=os.environ.get("DRY_RUN", "").lower() == "true")
    ap.add_argument("--url", default=os.environ.get("UPSERT_URL", DEFAULT_URL))
    args = ap.parse_args()

    api_key = os.environ.get("API_KEY") or os.environ.get("TOOLS_UPSERT_API_KEY")
    if not api_key:
        print("ERROR: API_KEY env var required", file=sys.stderr)
        sys.exit(2)

    items = json.loads(pathlib.Path(args.file).read_text(encoding="utf-8"))
    if not isinstance(items, list):
        print("ERROR: file must be a JSON array", file=sys.stderr)
        sys.exit(2)

    only = set(s.strip() for s in args.only.split(",") if s.strip())
    if only:
        items = [x for x in items if x.get("slug") in only]

    items = [sanitize_for_upsert(x) for x in items if x.get("slug")]

    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Endpoint: {args.url}")
    print(f"Pushing {len(items)} items in chunks of {args.chunk}, delay {args.inter_batch_ms}ms")

    totals = {"sent": 0, "updated": 0, "created": 0, "failed": 0, "errors": []}
    total_batches = (len(items) + args.chunk - 1) // args.chunk

    for i in range(0, len(items), args.chunk):
        chunk = items[i : i + args.chunk]
        batch_num = i // args.chunk + 1
        if args.dry_run:
            print(f"[DRY] batch {batch_num}/{total_batches}: {len(chunk)} items (first: {chunk[0]['slug']})", flush=True)
            totals["sent"] += len(chunk)
        else:
            # Send + handle per-item rate-limit retries up to 3 times.
            # Base44 returns 200 with rows_failed+errors=[{...Rate limit exceeded}].
            to_send = list(chunk)
            attempts_per_chunk = 4
            for try_i in range(attempts_per_chunk):
                body = json.dumps({"items": to_send}).encode("utf-8")
                status, resp = post_with_retry(args.url, api_key, body)
                rows_failed = resp.get("rows_failed", 0)
                errs = resp.get("errors") or []
                rate_limited = [e for e in errs if isinstance(e, dict) and "rate limit" in str(e.get("message","")).lower()]
                # Credit what succeeded
                totals["updated"] += resp.get("rows_updated", 0)
                totals["created"] += resp.get("rows_created", 0)
                print(
                    f"  batch {batch_num}/{total_batches} try {try_i+1}: sent={len(to_send)} updated={resp.get('rows_updated','?')} "
                    f"created={resp.get('rows_created',0)} failed={rows_failed} rate_limited={len(rate_limited)}",
                    flush=True,
                )
                if rows_failed == 0:
                    break
                # Only retry the rate-limited slugs; treat other errors as permanent failures
                retry_slugs = {e.get("slug") for e in rate_limited if e.get("slug")}
                perm_errors = [e for e in errs if e.get("slug") not in retry_slugs]
                totals["errors"].extend(perm_errors)
                if not retry_slugs:
                    totals["failed"] += rows_failed
                    break
                if try_i == attempts_per_chunk - 1:
                    totals["failed"] += len(retry_slugs)
                    totals["errors"].extend(rate_limited)
                    break
                to_send = [r for r in chunk if r.get("slug") in retry_slugs]
                # Back off before retrying the rate-limited subset
                wait_s = 30 * (try_i + 1)
                print(f"  waiting {wait_s}s before retrying {len(to_send)} rate-limited slugs", flush=True)
                time.sleep(wait_s)
            totals["sent"] += len(chunk)
        if i + args.chunk < len(items):
            time.sleep(args.inter_batch_ms / 1000)

    print("\n--- TOTALS ---")
    for k in ("sent", "updated", "created", "failed"):
        print(f"{k:<8}: {totals[k]}")
    if totals["errors"]:
        print(f"errors (first 10):")
        for e in totals["errors"][:10]:
            print(f"  - {json.dumps(e)}")

    # Fail loudly so GH Actions surfaces real failures (mirrors refresh-stars guardrail)
    if not args.dry_run and totals["failed"] > max(5, int(len(items) * 0.02)):
        print("Too many failures — flagging build red.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
