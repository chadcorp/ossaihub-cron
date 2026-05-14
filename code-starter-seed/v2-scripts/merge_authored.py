"""
Merge v2-authored/*.py files into rebuilt-v2.json for code-starter-seed.
Same shape as prompt-library-seed merger — authored RECORDS win by slug; legacy
records pass through; output validated against _schema.json.
"""

import argparse, importlib.util, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent  # code-starter-seed
AUTHORED_DIR = ROOT / "v2-authored"
LEGACY_PATH = ROOT / "rebuilt-v2.json"
SCHEMA_PATH = ROOT / "_schema.json"
OUTPUT_PATH = ROOT / "rebuilt-v2.json"


def load_authored() -> list[dict]:
    out: list[dict] = []
    for py_file in sorted(AUTHORED_DIR.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        records = getattr(mod, "RECORDS", None)
        if records is None:
            print(f"  WARN: {py_file.name} has no RECORDS export", file=sys.stderr)
            continue
        out.extend(records)
        print(f"  + {py_file.name}: {len(records)} records")
    return out


def load_legacy() -> list[dict]:
    if not LEGACY_PATH.exists():
        return []
    return json.loads(LEGACY_PATH.read_text(encoding="utf-8"))


def merge(authored: list[dict], legacy: list[dict]) -> list[dict]:
    authored_slugs = {r["slug"] for r in authored if r.get("slug")}
    out = list(authored)
    for r in legacy:
        if r.get("slug") in authored_slugs:
            continue
        out.append(r)
    return out


def validate(records: list[dict], strict: bool = False) -> int:
    try:
        from jsonschema import Draft7Validator
    except ImportError:
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
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    print("Loading authored:")
    authored = load_authored()
    print(f"Loading legacy: {LEGACY_PATH.name}")
    legacy = load_legacy()
    print(f"  legacy: {len(legacy)}")
    merged = merge(authored, legacy)
    print(f"Merged: {len(merged)} ({len(authored)} authored + {len(merged) - len(authored)} legacy carry-over)")
    bad = validate(merged, strict=args.strict)
    print(f"  invalid: {bad} / {len(merged)}")
    if args.strict and bad:
        sys.exit(1)
    OUTPUT_PATH.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.name} ({OUTPUT_PATH.stat().st_size/1024:.1f} kB)")


if __name__ == "__main__":
    main()
