"""
Push code-starter rebuilt-v2 entries to Base44 via /functions/upsertCodeStarter.

Mirrors the proven glossary-seed/v2-scripts/push_v2.py pattern:
  - Chunks 10 records/request
  - 12s sleep between chunks (stays under Base44's per-fn 100 req/min ceiling)
  - 5xx + 429 retry with exponential backoff + jitter
  - Idempotent — re-runs just update existing slugs

Usage:
  API_KEY=$TOOLS_UPSERT_API_KEY python push_v2.py [--file ../rebuilt-v2.json]
  API_KEY=... DRY_RUN=true python push_v2.py --only fastapi-ollama-chat,rag-langchain

Env:
  API_KEY           required (TOOLS_UPSERT_API_KEY from GitHub secrets)
  UPSERT_URL        override default endpoint
  CHUNK             default 10
  INTER_BATCH_MS    default 12000
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

DEFAULT_URL = "https://base44.app/api/apps/69a91ff6770c8ca0347ae03d/functions/upsertCodeStarter"


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
                base_wait = 30.0 if is_rate else 1.0
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
    """Map v2 record to the BaseCode entity field shape.

    Critical mapping (entity has BOTH legacy v1 fields and new v2 fields):
      - rec.dependencies (v2: array of {name,version,purpose})
        -> entity.dependencies_v2 = unchanged
        -> entity.dependencies (legacy v1, array of strings) = [d.name for d in v2]
      - rec.full_code  -> entity.code (legacy field is 'code')
                          + keep full_code mirrored for templates that read it
      - All other v2 fields pass through as-is (tldr, when_to_use, etc.).
      - Force status=approved and archived=false so records are publicly visible.
    """
    # Pass-through fields (exist on the entity with matching names)
    allowed = {
        "slug", "title", "tldr", "category", "language", "framework", "tags",
        "best_for_tags", "difficulty_tier", "featured",
        "when_to_use", "when_not_to_use", "quick_start",
        "env_vars", "setup_steps", "variations",
        "common_errors", "production_checklist", "tested_with",
        "related_tool_slugs", "related_glossary_slugs", "related_learn_slugs",
        "license", "attribution", "github_url",
        "meta_title", "meta_description", "faq",
        "description",
    }
    out = {k: v for k, v in rec.items() if k in allowed}

    # Map full_code -> legacy 'code' field + keep full_code
    if rec.get("full_code"):
        out["code"] = rec["full_code"]
        out["full_code"] = rec["full_code"]

    # Map v2 dependencies (objects) -> dependencies_v2; legacy dependencies (strings)
    deps_v2 = rec.get("dependencies") or []
    if deps_v2 and isinstance(deps_v2, list) and isinstance(deps_v2[0], dict):
        out["dependencies_v2"] = deps_v2
        out["dependencies"] = [d.get("name") for d in deps_v2 if d.get("name")]
    elif deps_v2:
        # Already strings
        out["dependencies"] = deps_v2

    # tldr mirrors into description for legacy templates
    if out.get("tldr") and not out.get("description"):
        out["description"] = out["tldr"]

    # Default these so records are publicly visible
    out.setdefault("status", "approved")
    out.setdefault("archived", False)
    out.setdefault("submitter_email", "seed@ossaihub.com")
    out.setdefault("submitter_name", "OSS Hub")

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=str(pathlib.Path(__file__).parent.parent / "rebuilt-v2.json"))
    ap.add_argument("--only", default="", help="comma-separated slug subset")
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
    print(f"Items: {len(items)}, chunk={args.chunk}, inter-batch={args.inter_batch_ms}ms")

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
