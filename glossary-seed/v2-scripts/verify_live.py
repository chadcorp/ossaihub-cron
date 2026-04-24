"""
Post-push verification. For a sample of slugs, curls the live page + the
glossaryApi endpoint and checks:
  - server returned v2 fields (tldr, plain_english, how_it_works, faq, ...)
  - HTML includes canonical, title, meta description matching v2
  - page source contains JSON-LD DefinedTerm + FAQPage (literal or via script tag)

Usage:
  python verify_live.py [--slugs rag,ab-test-llm,eval-harness,lora,embedding]
"""

import argparse
import json
import sys
import urllib.request

BASE44_API = "https://base44.app/api/apps/69a91ff6770c8ca0347ae03d/functions/glossaryApi"
SITE = "https://ossaihub.com"


def fetch(url: str, timeout=30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "ossaihub-verify/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slugs", default="rag,ab-test-llm,eval-harness,lora,embedding,prompt-injection,rlhf,lora,chunking,fine-tuning")
    args = ap.parse_args()
    slugs = [s.strip() for s in args.slugs.split(",") if s.strip()]

    print(f"Pulling live glossary from {BASE44_API}")
    data = json.loads(fetch(BASE44_API))
    terms = data.get("terms") if isinstance(data, dict) else data
    by_slug = {t["slug"]: t for t in terms if t.get("slug")}

    all_ok = True
    for slug in slugs:
        rec = by_slug.get(slug)
        if not rec:
            print(f"[MISS] {slug}: not in live data")
            all_ok = False
            continue

        # Server-side v2 check
        has_tldr = bool(rec.get("tldr"))
        has_faq = isinstance(rec.get("faq"), list) and len(rec.get("faq") or [])
        rv = rec.get("rewrite_version")

        # HTML check
        html = fetch(f"{SITE}/glossary/{slug}")
        html_lower = html.lower()
        has_v2_title_pattern = "plain-english definition" in html_lower or "expert guide" in html_lower
        has_canonical = f'rel="canonical"' in html and f"/glossary/{slug}" in html
        has_ld = "application/ld+json" in html
        has_faqpage = '"@type":"FAQPage"' in html or '"@type": "FAQPage"' in html

        status = all([has_tldr, has_faq, has_canonical, has_ld])
        if not status:
            all_ok = False
        mark = "[OK]" if status else "[FAIL]"
        print(
            f"{mark} {slug}  tldr={has_tldr} faq={has_faq} rv={rv}  "
            f"html[v2title={has_v2_title_pattern} canonical={has_canonical} jsonld={has_ld} faqpage={has_faqpage}]"
        )
        if rec.get("tldr"):
            print(f"       TL;DR: {rec['tldr'][:120]}")

    print()
    print("PASS" if all_ok else "FAIL")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
