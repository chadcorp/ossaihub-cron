"""Cross-check related_terms references for round 4."""
import json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
REBUILT = HERE.parent / "rebuilt-v2.json"
sys.path.insert(0, str(HERE))
from build_50_round4 import TERMS, EXCLUDE_SLUGS

existing = json.loads(REBUILT.read_text(encoding="utf-8"))
existing_slugs = {t["slug"] for t in existing}
kept = [t for t in TERMS if t["slug"] not in EXCLUDE_SLUGS]
new_slugs = {t["slug"] for t in kept}
all_slugs = existing_slugs | new_slugs

dangling = []
for t in kept:
    for r in (t.get("related_terms") or []):
        if r not in all_slugs:
            dangling.append((t["slug"], r))

if dangling:
    seen = set()
    print(f"DANGLING ({len(dangling)} total):")
    for src, ref in dangling:
        seen.add(ref)
        print(f"  {src} -> {ref}")
    print(f"\nUnique missing: {sorted(seen)}")
    sys.exit(1)
print(f"OK — {len(kept)} new terms, all related_terms resolve")
