"""Cross-check that every related_terms entry in new terms resolves to a real slug
(existing 526 + new 50).
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REBUILT = HERE.parent / "rebuilt-v2.json"

# Import TERMS from build script
sys.path.insert(0, str(HERE))
from build_50_new import TERMS

existing = json.loads(REBUILT.read_text(encoding="utf-8"))
existing_slugs = {t["slug"] for t in existing}
new_slugs = {t["slug"] for t in TERMS}
all_slugs = existing_slugs | new_slugs

dangling = []
for t in TERMS:
    for r in (t.get("related_terms") or []):
        if r not in all_slugs:
            dangling.append((t["slug"], r))

if dangling:
    print(f"DANGLING related_terms ({len(dangling)} total):")
    seen = set()
    for src, ref in dangling:
        seen.add(ref)
        print(f"  {src} -> {ref}")
    print(f"\nUnique missing slugs: {sorted(seen)}")
    sys.exit(1)
else:
    print(f"OK — all related_terms across {len(TERMS)} new terms resolve to existing or new slugs")
