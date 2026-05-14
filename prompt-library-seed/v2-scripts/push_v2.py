"""
Push prompt rebuilt-v2 entries to Base44 via /functions/upsertPrompt.

Mirrors glossary-seed/v2-scripts/push_v2.py and code-starter-seed/v2-scripts/push_v2.py.
  - Chunks 10 records/request
  - 12s sleep between chunks
  - 5xx + 429 retry with backoff
  - Idempotent — re-runs update by slug

Usage:
  API_KEY=$TOOLS_UPSERT_API_KEY python push_v2.py [--file ../rebuilt-v2.json]
  API_KEY=... DRY_RUN=true python push_v2.py --only json-extractor,sql-to-text
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

DEFAULT_URL = "https://base44.app/api/apps/69a91ff6770c8ca0347ae03d/functions/upsertPrompt"


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
            # 403 from Base44/Cloudflare is silent rate limit (HTML challenge page); treat as retryable.
            is_cf_block = e.code == 403 and ("<!DOCTYPE html>" in last or "cloudflare" in last.lower())
            is_rate = e.code == 429 or is_cf_block or "429" in last or "rate limit" in last.lower()
            if 500 <= e.code < 600 or e.code == 429 or is_cf_block:
                base_wait = 30.0 if is_rate else 1.0   # longer base for CF 403s
                wait = min(180.0, base_wait * (1.7 ** i)) + random.uniform(0, 3)
                tag = "cf-block" if is_cf_block else ("rate-limit" if is_rate else "")
                print(f"  retry {i+1}/{attempts} in {wait:.1f}s ({e.code} {tag}) body={last[:150]}", flush=True)
                time.sleep(wait)
                continue
            raise RuntimeError(f"{e.code}: {last}")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            wait = min(30.0, 1.0 * (2 ** i)) + random.uniform(0, 1)
            time.sleep(wait)
    raise RuntimeError(f"{last_status} after {attempts} retries. Last: {last}")


def sanitize_for_upsert(rec):
    """Return only v2 fields upsertPrompt accepts."""
    allowed = {
        "slug", "title", "tldr", "category", "tags", "best_for_tags",
        "difficulty_tier", "featured",
        "use_cases", "when_not_to_use", "full_prompt",
        "input_variables", "expected_output", "few_shot_examples",
        "model_compatibility", "variations", "failure_modes", "tested_with",
        "related_prompt_slugs", "related_tool_slugs", "related_glossary_slugs",
        "license", "attribution", "faq",
        "meta_title", "meta_description",
        # back-compat
        "description", "prompt_text",
    }
    out = {k: v for k, v in rec.items() if k in allowed}
    if "tldr" in out and "description" not in out:
        out["description"] = out["tldr"]
    if "full_prompt" in out and "prompt_text" not in out:
        out["prompt_text"] = out["full_prompt"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=str(pathlib.Path(__file__).parent.parent / "rebuilt-v2.json"))
    ap.add_argument("--only", default="")
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
    only = set(s.strip() for s in args.only.split(",") if s.strip())
    if only:
        items = [x for x in items if x.get("slug") in only]
    items = [sanitize_for_upsert(x) for x in items if x.get("slug")]

    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'} | Items: {len(items)} | chunk={args.chunk}")
    if args.dry_run:
        print(json.dumps(items[:2], indent=2)[:800])
        return

    chunks = [items[i:i + args.chunk] for i in range(0, len(items), args.chunk)]
    total_ok = 0
    total_failed = 0
    for ci, chunk in enumerate(chunks, 1):
        body = json.dumps({"records": chunk}).encode("utf-8")
        try:
            status, resp = post_with_retry(args.url, api_key, body)
            ok = resp.get("upserted", len(chunk)) if isinstance(resp, dict) else len(chunk)
            total_ok += ok
            print(f"chunk {ci}/{len(chunks)} -> HTTP {status} upserted={ok}", flush=True)
        except Exception as e:
            total_failed += len(chunk)
            print(f"chunk {ci}/{len(chunks)} FAILED: {e}", file=sys.stderr, flush=True)
        if ci < len(chunks):
            time.sleep(args.inter_batch_ms / 1000.0)

    print(f"\nDONE. upserted={total_ok} failed={total_failed}")
    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
