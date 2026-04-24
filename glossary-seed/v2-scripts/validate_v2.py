"""
Validate rebuilt-v2.json. Fails non-zero if any record is malformed, which
gates the Push workflow in CI.

Checks:
  - all required v2 fields present and non-empty (pitfalls 2-4, faq 3-5)
  - slug matches kebab-case regex
  - tldr ≤ 30 words
  - no banned marketing words in any copy field
  - related_terms are subset of live slugs (no dangling references)
  - schema_jsonld has DefinedTerm + FAQPage shape
  - meta_title / meta_description within char limits

Usage:
  python validate_v2.py --file ../rebuilt-v2.json [--live ../../../glossary_live.json]
"""

import argparse
import json
import pathlib
import re
import sys
from collections import Counter

REQUIRED = [
    "slug", "title", "category", "difficulty_tier",
    "tldr", "plain_english", "how_it_works", "why_it_matters",
    "example", "pitfalls", "when_use", "when_avoid",
    "related_terms", "faq", "meta_title", "meta_description",
    "schema_jsonld",
]

BANNED = [
    "powerful", "revolutionary", "cutting-edge", "cutting edge",
    "unleash", "seamlessly", "game-changer", "game changer",
    "groundbreaking",
]

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--live", default="")
    ap.add_argument("--max-errors", type=int, default=10, help="print at most N error contexts")
    args = ap.parse_args()

    arr = json.loads(pathlib.Path(args.file).read_text(encoding="utf-8"))
    if not isinstance(arr, list):
        print("FAIL: not a JSON array", file=sys.stderr)
        sys.exit(1)

    live_slugs = set()
    if args.live and pathlib.Path(args.live).exists():
        live = json.loads(pathlib.Path(args.live).read_text(encoding="utf-8"))
        terms = live.get("terms") if isinstance(live, dict) else live
        live_slugs = {t["slug"] for t in terms if t.get("slug")}

    errors = []
    counter = Counter()

    for rec in arr:
        if not isinstance(rec, dict) or "slug" not in rec:
            errors.append(("?", ["not_a_dict_or_missing_slug"]))
            continue
        slug = rec["slug"]
        issues = []

        # required fields
        for f in REQUIRED:
            if f not in rec or rec[f] in (None, "", [], {}):
                if f in ("related_terms",) and isinstance(rec.get(f), list):
                    if not rec[f]:
                        issues.append(f"empty:{f}")
                else:
                    issues.append(f"missing_or_empty:{f}")

        # slug shape
        if not SLUG_RE.match(slug):
            issues.append(f"bad_slug_shape")

        # word counts
        tldr = rec.get("tldr", "")
        if len(tldr.split()) > 30:
            issues.append(f"tldr_too_long:{len(tldr.split())}w")

        # pitfalls count
        pitfalls = rec.get("pitfalls") or []
        if not isinstance(pitfalls, list) or not (2 <= len(pitfalls) <= 4):
            issues.append(f"pitfalls_count:{len(pitfalls) if isinstance(pitfalls, list) else 'not_list'}")

        # faq count
        faq = rec.get("faq") or []
        if not isinstance(faq, list) or not (3 <= len(faq) <= 5):
            issues.append(f"faq_count:{len(faq) if isinstance(faq, list) else 'not_list'}")
        else:
            for i, qa in enumerate(faq):
                if not isinstance(qa, dict) or not qa.get("q") or not qa.get("a"):
                    issues.append(f"faq_shape[{i}]")

        # char caps
        mt = rec.get("meta_title", "")
        if len(mt) > 120:
            issues.append(f"meta_title_len:{len(mt)}")
        md = rec.get("meta_description", "")
        if len(md) > 200:
            issues.append(f"meta_description_len:{len(md)}")

        # banned words
        body = " ".join(
            str(rec.get(k, ""))
            for k in ("tldr", "plain_english", "how_it_works", "why_it_matters", "example", "when_use", "when_avoid")
        ).lower()
        for bw in BANNED:
            if bw in body:
                issues.append(f"banned:{bw}")

        # related_terms subset check
        if live_slugs:
            dangling = [s for s in (rec.get("related_terms") or []) if s not in live_slugs]
            if dangling:
                issues.append(f"dangling_related:{dangling[:3]}")

        # schema_jsonld shape
        jsonld = rec.get("schema_jsonld") or {}
        if not isinstance(jsonld, dict) or "DefinedTerm" not in jsonld:
            issues.append("jsonld_missing_DefinedTerm")
        if isinstance(jsonld, dict) and "FAQPage" in jsonld:
            mainEntity = jsonld["FAQPage"].get("mainEntity") or []
            if not mainEntity:
                issues.append("jsonld_FAQPage_empty")

        if issues:
            errors.append((slug, issues))
            for iss in issues:
                counter[iss.split(":", 1)[0]] += 1

    print(f"Validated {len(arr)} records.")
    print(f"Errors: {len(errors)}")
    if counter:
        print("Issue breakdown:")
        for k, v in counter.most_common():
            print(f"  {k}: {v}")

    if errors:
        print(f"\nFirst {args.max_errors} bad records:")
        for slug, iss in errors[: args.max_errors]:
            print(f"  {slug}: {iss}")
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
