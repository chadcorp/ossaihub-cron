"""
Re-run the rewriter for every slug in _failures.jsonl. Clears the file on
success. Same env and model as the main run.

Usage:
  ANTHROPIC_API_KEY=... python retry_failures.py [--model claude-haiku-4-5-20251001]
"""

import argparse
import json
import os
import pathlib
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(pathlib.Path(__file__).parent.parent / "rebuilt-v2"))
    ap.add_argument("--input", default=str(pathlib.Path(__file__).parent.parent.parent.parent / "glossary_live.json"))
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()

    fail_path = pathlib.Path(args.out) / "_failures.jsonl"
    if not fail_path.exists() or fail_path.stat().st_size == 0:
        print("No failures file — nothing to retry.")
        return 0

    slugs = []
    seen = set()
    for line in fail_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            s = entry.get("slug")
            if s and s not in seen:
                slugs.append(s)
                seen.add(s)
        except json.JSONDecodeError:
            pass

    if not slugs:
        print("Failures file is empty.")
        return 0

    print(f"Retrying {len(slugs)} failed slugs: {slugs[:10]}{'...' if len(slugs)>10 else ''}")

    # Move old failures aside before re-run so we can diff
    backup = fail_path.with_suffix(".prev.jsonl")
    fail_path.rename(backup)

    script = pathlib.Path(__file__).parent / "rewrite_v2.py"
    cmd = [
        sys.executable, str(script),
        "--input", args.input,
        "--out", args.out,
        "--workers", str(args.workers),
        "--model", args.model,
        "--only", ",".join(slugs),
        "--force",
    ]
    print("Running:", " ".join(cmd))
    rc = subprocess.run(cmd, check=False).returncode
    print(f"Exit: {rc}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
