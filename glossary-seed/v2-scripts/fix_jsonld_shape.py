"""
One-time fixer for rebuilt-v2.json.

The rewriter emitted schema_jsonld as {"DefinedTerm": {...}, "FAQPage": {...}},
but Base44's detail-page render injects schema_jsonld verbatim as a single
<script type="application/ld+json"> block — which gives a body with no
top-level @type and breaks Google's parser.

Flatten so schema_jsonld IS the DefinedTerm (with @context + @type present).
FAQPage gets synthesized at render time from the faq field (already working).

Usage:
  python fix_jsonld_shape.py [--file ../rebuilt-v2.json] [--out same]
"""

import argparse
import json
import pathlib


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=str(pathlib.Path(__file__).parent.parent / "rebuilt-v2.json"))
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    p = pathlib.Path(args.file)
    arr = json.loads(p.read_text(encoding="utf-8"))
    fixed = 0
    for rec in arr:
        jsonld = rec.get("schema_jsonld")
        if isinstance(jsonld, dict) and "DefinedTerm" in jsonld and "@type" not in jsonld:
            rec["schema_jsonld"] = jsonld["DefinedTerm"]
            fixed += 1

    out = pathlib.Path(args.out) if args.out else p
    out.write_text(json.dumps(arr, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Flattened schema_jsonld on {fixed}/{len(arr)} records -> {out}")


if __name__ == "__main__":
    main()
