"""
Merge per-category rebuilt-v2/*.json into a single rebuilt-v2.json at the root.

Usage:
  python merge_v2.py [--in rebuilt-v2] [--out rebuilt-v2.json] [--legacy legacy-glossary.json]

Behavior:
  - Deduplicates by slug (last one wins).
  - Sanitizes each record:
      * strips related_terms not present in live_slugs (dangling references
        are a common Haiku hallucination)
      * removes banned marketing words from copy fields
      * truncates meta_title to 120 chars, meta_description to 200 chars
  - If --legacy is provided, emits a parallel legacy-glossary.json snapshot of
    the v1 fields from the current live glossary — so rollback is cheap.
  - Writes stats to stdout.
"""

import argparse
import json
import pathlib
import re
import sys
from collections import Counter

BANNED_PATTERNS = [
    re.compile(r"\bpowerful\b", re.IGNORECASE),
    re.compile(r"\brevolutionary\b", re.IGNORECASE),
    re.compile(r"\bcutting[- ]edge\b", re.IGNORECASE),
    re.compile(r"\bunleash\b", re.IGNORECASE),
    re.compile(r"\bseamlessly\b", re.IGNORECASE),
    re.compile(r"\bgame[- ]changer\b", re.IGNORECASE),
    re.compile(r"\bgroundbreaking\b", re.IGNORECASE),
]

REPLACEMENTS = {
    "powerful": "strong",
    "revolutionary": "significant",
    "cutting-edge": "modern",
    "cutting edge": "modern",
    "unleash": "enable",
    "seamlessly": "cleanly",
    "game-changer": "major improvement",
    "game changer": "major improvement",
    "groundbreaking": "notable",
}

COPY_FIELDS = (
    "tldr", "plain_english", "how_it_works", "why_it_matters",
    "example", "when_use", "when_avoid",
)


def sanitize_record(rec: dict, live_slugs: set) -> tuple:
    """Return (sanitized_rec, issues_fixed) tuple."""
    fixed = []
    # Strip dangling related_terms
    related = rec.get("related_terms") or []
    if live_slugs:
        cleaned = [s for s in related if s in live_slugs]
        if len(cleaned) != len(related):
            dangling = [s for s in related if s not in live_slugs]
            fixed.append(f"stripped_related={dangling}")
            rec["related_terms"] = cleaned

    # Remove banned words from copy
    for f in COPY_FIELDS:
        val = rec.get(f)
        if not isinstance(val, str):
            continue
        new_val = val
        for bad, good in REPLACEMENTS.items():
            new_val = re.sub(rf"\b{re.escape(bad)}\b", good, new_val, flags=re.IGNORECASE)
        if new_val != val:
            fixed.append(f"banned_in_{f}")
            rec[f] = new_val

    # Clamp meta_title / meta_description
    mt = rec.get("meta_title", "")
    if mt and len(mt) > 120:
        rec["meta_title"] = mt[:117].rstrip() + "..."
        fixed.append(f"meta_title_truncated:{len(mt)}->120")
    md = rec.get("meta_description", "")
    if md and len(md) > 200:
        rec["meta_description"] = md[:197].rstrip() + "..."
        fixed.append(f"meta_description_truncated:{len(md)}->200")

    # Also re-sync schema_jsonld description to tldr (if tldr was modified)
    jsonld = rec.get("schema_jsonld") or {}
    if isinstance(jsonld, dict) and isinstance(jsonld.get("DefinedTerm"), dict):
        jsonld["DefinedTerm"]["description"] = rec.get("tldr", jsonld["DefinedTerm"].get("description", ""))

    return rec, fixed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", default=str(pathlib.Path(__file__).parent.parent / "rebuilt-v2"))
    ap.add_argument("--out", default=str(pathlib.Path(__file__).parent.parent / "rebuilt-v2.json"))
    ap.add_argument("--legacy", default="")
    ap.add_argument("--live", default=str(pathlib.Path(__file__).parent.parent.parent.parent / "glossary_live.json"))
    args = ap.parse_args()

    in_dir = pathlib.Path(args.in_dir)
    out_file = pathlib.Path(args.out)

    # Build live-slug index for dangling-reference stripping
    live_slugs = set()
    live_path = pathlib.Path(args.live)
    if live_path.exists():
        live = json.loads(live_path.read_text(encoding="utf-8"))
        terms = live.get("terms") if isinstance(live, dict) else live
        live_slugs = {t["slug"] for t in terms if t.get("slug")}

    seen = {}
    files = sorted(p for p in in_dir.glob("*.json") if not p.name.startswith("_"))
    per_file = []
    for p in files:
        try:
            arr = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"SKIP {p.name}: {e}", file=sys.stderr)
            continue
        if not isinstance(arr, list):
            continue
        before = len(seen)
        for rec in arr:
            if isinstance(rec, dict) and rec.get("slug"):
                seen[rec["slug"]] = rec
        per_file.append((p.name, len(arr), len(seen) - before))

    # Sanitize every merged record
    fix_counter = Counter()
    for slug, rec in seen.items():
        _, fixed = sanitize_record(rec, live_slugs)
        for f in fixed:
            key = f.split(":", 1)[0]
            fix_counter[key] += 1

    merged = sorted(seen.values(), key=lambda x: (x.get("category", ""), x["slug"]))
    out_file.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")

    cats = Counter(r.get("category", "?") for r in merged)
    print(f"Merged {len(files)} files -> {out_file}")
    print(f"Total unique slugs: {len(merged)}")
    if fix_counter:
        print("Sanitization fixes:")
        for k, v in fix_counter.most_common():
            print(f"  {k}: {v}")
    for name, n_in, n_added in per_file:
        print(f"  {name}: {n_in} records, +{n_added} new")
    print(f"Categories: {dict(cats)}")

    # Legacy snapshot for rollback
    if args.legacy:
        live_path = pathlib.Path(args.live)
        if live_path.exists():
            live = json.loads(live_path.read_text(encoding="utf-8"))
            terms = live.get("terms") if isinstance(live, dict) else live
            legacy = [
                {k: t.get(k) for k in (
                    "slug", "title", "category", "difficulty_tier",
                    "short_definition", "full_explanation", "why_it_matters",
                    "common_misconceptions", "code_example",
                    "related_terms", "related_tools", "related_prompts",
                    "seo_variations",
                )}
                for t in terms
            ]
            pathlib.Path(args.legacy).write_text(json.dumps(legacy, indent=2), encoding="utf-8")
            print(f"Legacy snapshot: {args.legacy} ({len(legacy)} entries)")


if __name__ == "__main__":
    main()
