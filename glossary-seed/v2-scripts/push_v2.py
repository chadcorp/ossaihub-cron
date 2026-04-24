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
            if 500 <= e.code < 600:
                is_rate = "429" in last
                base_wait = 15.0 if is_rate else 1.0
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
    ap.add_argument("--chunk", type=int, default=int(os.environ.get("CHUNK", "25")))
    ap.add_argument("--inter-batch-ms", type=int, default=int(os.environ.get("INTER_BATCH_MS", "8000")))
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
            body = json.dumps({"items": chunk}).encode("utf-8")
            status, resp = post_with_retry(args.url, api_key, body)
            totals["sent"] += len(chunk)
            totals["updated"] += resp.get("rows_updated", 0)
            totals["created"] += resp.get("rows_created", 0)
            totals["failed"] += resp.get("rows_failed", 0)
            if isinstance(resp.get("errors"), list):
                totals["errors"].extend(resp["errors"])
            print(
                f"  batch {batch_num}/{total_batches}: sent={len(chunk)} updated={resp.get('rows_updated','?')} "
                f"created={resp.get('rows_created',0)} failed={resp.get('rows_failed',0)}",
                flush=True,
            )
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
