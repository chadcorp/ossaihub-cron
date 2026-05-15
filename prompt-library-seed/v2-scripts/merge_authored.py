"""
Merge v2-authored/*.py files into rebuilt-v2.json.

Each authored file exports RECORDS = [...] — full v2 records (glossary depth).
This script:
  - Loads all RECORDS from v2-authored/*.py
  - Preserves legacy entries from existing rebuilt-v2.json for slugs that don't
    yet have an authored version (we're gradually replacing the weak templated
    records as we author rich ones)
  - Authored entries WIN over legacy entries with the same slug
  - Validates the merged output against _schema.json
  - Writes rebuilt-v2.json
  - Prints a summary of authored vs legacy counts

Usage:
  py -3 merge_authored.py
  py -3 merge_authored.py --strict  # fail if any legacy record has invalid v2 shape
"""

import argparse
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent  # prompt-library-seed
AUTHORED_DIR = ROOT / "v2-authored"
LEGACY_PATH = ROOT / "rebuilt-v2.json"
SCHEMA_PATH = ROOT / "_schema.json"
OUTPUT_PATH = ROOT / "rebuilt-v2.json"


def load_authored() -> list[dict]:
    """Load every RECORDS list from v2-authored/*.py."""
    out: list[dict] = []
    for py_file in sorted(AUTHORED_DIR.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        records = getattr(mod, "RECORDS", None)
        if records is None:
            print(f"  WARN: {py_file.name} has no RECORDS export, skipping", file=sys.stderr)
            continue
        if not isinstance(records, list):
            print(f"  ERROR: {py_file.name} RECORDS is not a list", file=sys.stderr)
            sys.exit(1)
        out.extend(records)
        print(f"  + {py_file.name}: {len(records)} records")
    return out


def load_legacy() -> list[dict]:
    if not LEGACY_PATH.exists():
        return []
    return json.loads(LEGACY_PATH.read_text(encoding="utf-8"))


def is_thick(r: dict) -> bool:
    """v2 depth = 3+ use_cases AND 3+ failure_modes AND 2+ faq AND 2+ variations.

    Records that don't meet this bar are considered legacy thin and DROPPED from merge.
    This is the quality gate that prevents resurrected legacy from drifting into the public site.
    """
    return (
        len(r.get("use_cases") or []) >= 3
        and len(r.get("failure_modes") or []) >= 3
        and len(r.get("faq") or []) >= 2
        and len(r.get("variations") or []) >= 2
    )


def merge(authored: list[dict], legacy: list[dict]) -> list[dict]:
    """Authored wins over legacy by slug; legacy slugs without authored version pass through
    ONLY IF they pass the thickness quality gate."""
    authored_slugs = {r["slug"] for r in authored if r.get("slug")}
    out = list(authored)
    skipped_thin = 0
    for r in legacy:
        if r.get("slug") in authored_slugs:
            continue
        if not is_thick(r):
            skipped_thin += 1
            continue
        out.append(r)
    if skipped_thin:
        print(f"  filtered {skipped_thin} legacy thin records (failed quality gate)")
    return out


def validate(records: list[dict], strict: bool = False) -> int:
    try:
        from jsonschema import Draft7Validator
    except ImportError:
        print("  jsonschema not installed; skipping validation", file=sys.stderr)
        return 0
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    v = Draft7Validator(schema)
    bad = 0
    for r in records:
        errors = sorted(v.iter_errors(r), key=lambda e: e.path)
        if errors:
            bad += 1
            if strict or bad <= 5:
                for e in errors[:2]:
                    print(f"  INVALID {r.get('slug','?')}: at {list(e.path)} ({e.validator}): {e.message[:120]}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="Fail on any invalid record")
    args = ap.parse_args()

    print("Loading authored records:")
    authored = load_authored()

    print(f"Loading legacy records from {LEGACY_PATH.name}:")
    legacy = load_legacy()
    print(f"  legacy: {len(legacy)} records")

    merged = merge(authored, legacy)
    print(f"Merged: {len(merged)} total ({len(authored)} authored + {len(merged) - len(authored)} legacy carry-over)")

    print("Validating against _schema.json:")
    bad = validate(merged, strict=args.strict)
    print(f"  invalid: {bad} / {len(merged)}")
    if args.strict and bad:
        print("STRICT: aborting on invalid records", file=sys.stderr)
        sys.exit(1)

    OUTPUT_PATH.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"Wrote {OUTPUT_PATH.name} ({size_kb:.1f} kB)")


if __name__ == "__main__":
    main()
