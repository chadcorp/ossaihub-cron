"""
Merge per-category rebuilt-v2/*.json into a single rebuilt-v2.json at the root.

Usage:
  python merge_v2.py [--in rebuilt-v2] [--out rebuilt-v2.json] [--legacy legacy-glossary.json]

Behavior:
  - Deduplicates by slug (last one wins).
  - If --legacy is provided, emits a parallel legacy-glossary.json snapshot of
    the v1 fields from the current live glossary — so rollback is cheap.
  - Writes stats to stdout.
"""

import argparse
import json
import pathlib
import sys
from collections import Counter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", default=str(pathlib.Path(__file__).parent.parent / "rebuilt-v2"))
    ap.add_argument("--out", default=str(pathlib.Path(__file__).parent.parent / "rebuilt-v2.json"))
    ap.add_argument("--legacy", default="")
    ap.add_argument("--live", default=str(pathlib.Path(__file__).parent.parent.parent.parent / "glossary_live.json"))
    args = ap.parse_args()

    in_dir = pathlib.Path(args.in_dir)
    out_file = pathlib.Path(args.out)

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

    merged = sorted(seen.values(), key=lambda x: (x.get("category", ""), x["slug"]))
    out_file.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")

    cats = Counter(r.get("category", "?") for r in merged)
    print(f"Merged {len(files)} files -> {out_file}")
    print(f"Total unique slugs: {len(merged)}")
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
