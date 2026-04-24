"""
Rewrite every OSS AI Hub glossary term into v2 schema (TL;DR + 10 sections + JSON-LD).

Input: glossary_live.json (snapshot from /functions/glossaryApi)
Output: one JSON file per category in rebuilt-v2/, each an array of v2 term objects.

Design:
- Drives Claude (Anthropic API) with a strict per-term prompt.
- Concurrent workers (default 4) with exponential backoff on 429/5xx.
- Resumable: skips terms already present in the per-category output file.
- Self-validating: every record must contain all v2 fields or it's marked failed.
- Emits schema_jsonld (DefinedTerm + FAQPage) inline so Base44 just needs to
  stringify it into a <script type="application/ld+json"> block.

Usage:
  ANTHROPIC_API_KEY=$CLAUDE_CODE_OAUTH_TOKEN \\
  python rewrite_v2.py --input ../../../glossary_live.json --out ../rebuilt-v2 [--only slug1,slug2] [--workers 4]

Env:
  ANTHROPIC_API_KEY  required (accepts sk-ant-api or OAuth sk-ant-oat)
  MODEL              default claude-opus-4-7 (claude-sonnet-4-6 for cheap runs)
  MAX_RETRIES        default 5
"""

import argparse
import concurrent.futures as cf
import json
import os
import pathlib
import random
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = os.environ.get("MODEL", "claude-opus-4-7")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "5"))
SITE_ORIGIN = "https://ossaihub.com"


# ---------- v2 Prompt (canonical source of truth) ----------

SYSTEM_PROMPT = """You are a senior AI engineer writing the best AI-glossary entries on the internet for ossaihub.com, a trust-first open-source AI resource.

Audience: rookies finish the first 3 sections and get it; experts skim the rest and nod. Google rewards you because the TL;DR is snippet-ready, the FAQ is schema-ready, and the structure is scannable.

Voice: practitioner-to-practitioner. Active voice, second person, present tense. Specific, not generic. Concede tradeoffs openly. No hype. No filler.

Banned words: "powerful", "revolutionary", "cutting-edge", "unleash", "leverage", "seamlessly", "robust solution", "game-changer", "harness".

Banned patterns:
- Starting a sentence with "In the field of AI..."
- "It is important to note that..."
- "This groundbreaking technology..."
- Listing features like marketing copy
- Restating the previous section
- Defining jargon with other jargon

Rules:
- TL;DR ≤25 words, plain English, snippet-target
- "In Plain English" has ZERO undefined technical terms
- "How It Works" is concrete mechanics — not abstractions
- "Example in Practice" uses real names/companies/numbers when possible
- "Common Pitfalls" is where experts nod — specificity required
- "When to Use / When to Avoid" is a paired decision rule
- FAQ questions are REAL search queries, not internal restatements
- Related Terms must be in the provided valid-slug list; never invent slugs

You return ONE json object per term — no prose before or after, no markdown fences."""


def user_prompt(term: dict, valid_slugs: set) -> str:
    """Build the per-term user prompt."""
    valid_related = [s for s in (term.get("related_terms") or []) if s in valid_slugs]
    existing_tools = term.get("related_tools") or []

    return f"""Rewrite this glossary term into the v2 schema. Return ONE valid JSON object — no markdown, no preamble, no trailing text.

INPUT TERM (v1):
{json.dumps({
    "title": term.get("title"),
    "slug": term.get("slug"),
    "category": term.get("category"),
    "difficulty_tier": term.get("difficulty_tier"),
    "short_definition": term.get("short_definition"),
    "full_explanation": term.get("full_explanation"),
    "why_it_matters": term.get("why_it_matters"),
    "common_misconceptions": term.get("common_misconceptions"),
    "code_example": term.get("code_example"),
    "existing_related_terms": valid_related,
    "existing_related_tools": existing_tools,
    "seo_variations": term.get("seo_variations") or [],
}, indent=2)}

VALID related-term slugs (pick 3–6 that actually connect, at least one cross-category when accurate):
{json.dumps(sorted(valid_slugs)[:800])}

OUTPUT JSON SHAPE (all fields required except where noted):
{{
  "slug": "<existing slug — do not change>",
  "title": "<existing title — do not change unless obviously wrong>",
  "category": "<existing category>",
  "difficulty_tier": "<beginner|intermediate|advanced>",
  "tldr": "<ONE sentence, ≤25 words, plain English, answers 'what is X'; reused as meta description>",
  "plain_english": "<2–3 sentences, analogy or everyday framing, ZERO undefined jargon>",
  "how_it_works": "<3–6 sentences OR bullet-style paragraph, concrete mechanics — inputs, outputs, steps>",
  "why_it_matters": "<2–3 sentences tying to a business/engineering outcome; NOT a summary of how_it_works>",
  "example": "<one concrete scenario with real company/team/numbers where possible; 2–4 sentences>",
  "pitfalls": ["<pitfall 1 — specific, one sentence>", "<pitfall 2>", "<optional pitfall 3>", "<optional pitfall 4>"],
  "when_use": "<one sentence decision rule: use this when X, Y, or Z>",
  "when_avoid": "<one sentence decision rule: avoid when A, B, or C>",
  "related_terms": ["<slug>", "<slug>", ...],
  "related_tools": {json.dumps(existing_tools)},
  "faq": [
    {{"q": "<real search query 1 — e.g. 'What is X?'>", "a": "<1–2 sentences>"}},
    {{"q": "<question 2 — often comparative, e.g. 'Is X the same as Y?'>", "a": "..."}},
    {{"q": "<question 3 — often practical, e.g. 'How long does X take?' or 'Does X work for Y?'>", "a": "..."}}
  ],
  "meta_title": "<{term.get('title','')} — Plain-English Definition & Expert Guide | OSS AI Hub>",
  "meta_description": "<TL;DR verbatim OR a ≤155-char polish of it>",
  "seo_variations": {json.dumps(term.get('seo_variations') or [])}
}}

Length budget: TL;DR ≤25 words, each major section ≤80 words, total body 350–550 words.

Hard constraints:
- Use the exact slug {json.dumps(term.get('slug'))}.
- Use the exact category {json.dumps(term.get('category'))}.
- Related-term slugs must come ONLY from the valid list above.
- FAQ must contain 3–5 entries and every question must be phrased as a real user would search it.
- No banned words. No marketing tone.
- If the term is inherently abstract, the example may be a workflow/scenario rather than a company name — but it MUST be concrete.

Return the JSON object only."""


# ---------- HTTP helpers ----------

def call_claude(api_key: str, model: str, system: str, user: str, max_tokens: int = 4000) -> str:
    """Call Anthropic API, return text. Raises on unrecoverable errors."""
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode("utf-8")

    last_err = None
    for attempt in range(MAX_RETRIES):
        req = urllib.request.Request(
            API_URL,
            data=body,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode("utf-8"))
                parts = data.get("content") or []
                for p in parts:
                    if p.get("type") == "text":
                        return p["text"]
                raise RuntimeError(f"No text in response: {data}")
        except urllib.error.HTTPError as e:
            status = e.code
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")[:500]
            except Exception:
                pass
            last_err = f"HTTP {status}: {err_body}"
            retriable = status in (429, 500, 502, 503, 504, 529)
            if not retriable or attempt == MAX_RETRIES - 1:
                raise RuntimeError(last_err)
            wait = min(60.0, 2.0 * (2 ** attempt)) + random.uniform(0, 1)
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = f"NETWORK: {e!r}"
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(last_err)
            wait = min(60.0, 2.0 * (2 ** attempt)) + random.uniform(0, 1)
            time.sleep(wait)
    raise RuntimeError(last_err or "exhausted retries")


# ---------- Parsing / validation ----------

JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json(text: str) -> dict:
    """Best-effort JSON extraction from a model response."""
    stripped = text.strip()
    # Try direct parse first
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    # Strip markdown fences
    m = JSON_FENCE.search(stripped)
    if m:
        return json.loads(m.group(1))
    # Find first {...} block
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(stripped[start : end + 1])
    raise ValueError(f"Could not extract JSON from: {stripped[:200]}")


REQUIRED_FIELDS = [
    "slug", "title", "category", "difficulty_tier",
    "tldr", "plain_english", "how_it_works", "why_it_matters",
    "example", "pitfalls", "when_use", "when_avoid",
    "related_terms", "related_tools", "faq",
    "meta_title", "meta_description",
]

BANNED_WORDS = [
    "powerful", "revolutionary", "cutting-edge", "unleash",
    "seamlessly", "game-changer", "game changer",
]


def validate_record(rec: dict, expected_slug: str) -> list:
    """Return list of validation issues (empty == valid)."""
    issues = []
    for f in REQUIRED_FIELDS:
        if f not in rec:
            issues.append(f"missing:{f}")
        elif rec[f] in (None, "", [], {}):
            if f not in ("related_tools", "related_terms", "pitfalls", "faq"):
                issues.append(f"empty:{f}")

    if rec.get("slug") != expected_slug:
        issues.append(f"slug_mismatch:{rec.get('slug')}!={expected_slug}")

    tldr = rec.get("tldr", "")
    wc = len(tldr.split())
    if wc > 30:
        issues.append(f"tldr_too_long:{wc}")

    pitfalls = rec.get("pitfalls") or []
    if not isinstance(pitfalls, list) or not (2 <= len(pitfalls) <= 4):
        issues.append(f"pitfalls_count:{len(pitfalls) if isinstance(pitfalls, list) else 'not_list'}")

    faq = rec.get("faq") or []
    if not isinstance(faq, list) or not (3 <= len(faq) <= 5):
        issues.append(f"faq_count:{len(faq) if isinstance(faq, list) else 'not_list'}")
    else:
        for i, q in enumerate(faq):
            if not isinstance(q, dict) or not q.get("q") or not q.get("a"):
                issues.append(f"faq_shape:{i}")

    lower_body = " ".join(str(rec.get(k, "")) for k in (
        "tldr", "plain_english", "how_it_works", "why_it_matters", "example",
    )).lower()
    for bw in BANNED_WORDS:
        if bw in lower_body:
            issues.append(f"banned:{bw}")

    return issues


def build_jsonld(rec: dict) -> dict:
    """Generate DefinedTerm + FAQPage JSON-LD blocks."""
    slug = rec["slug"]
    url = f"{SITE_ORIGIN}/glossary/{slug}"
    return {
        "DefinedTerm": {
            "@context": "https://schema.org",
            "@type": "DefinedTerm",
            "name": rec["title"],
            "description": rec["tldr"],
            "inDefinedTermSet": f"{SITE_ORIGIN}/Glossary",
            "url": url,
            "termCode": slug,
        },
        "FAQPage": {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": q["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": q["a"]},
                }
                for q in (rec.get("faq") or [])
            ],
        },
    }


# ---------- Pipeline ----------

def rewrite_one(term: dict, valid_slugs: set, api_key: str, model: str) -> dict:
    """Rewrite one term. Returns dict with either record or error."""
    slug = term["slug"]
    try:
        text = call_claude(api_key, model, SYSTEM_PROMPT, user_prompt(term, valid_slugs))
        rec = extract_json(text)
        issues = validate_record(rec, slug)
        if issues:
            # Retry once with a self-correction instruction if a fixable subset
            fixable = [i for i in issues if not i.startswith("slug_mismatch")]
            if fixable:
                retry_prompt = (
                    user_prompt(term, valid_slugs)
                    + "\n\nThe previous response had these issues — fix them and return corrected JSON only: "
                    + ", ".join(fixable)
                )
                text = call_claude(api_key, model, SYSTEM_PROMPT, retry_prompt)
                rec = extract_json(text)
                issues = validate_record(rec, slug)

        if issues:
            return {"ok": False, "slug": slug, "issues": issues, "raw": text[:800]}

        rec["schema_jsonld"] = build_jsonld(rec)
        rec["rewrite_version"] = "v2"
        rec["rewritten_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return {"ok": True, "slug": slug, "record": rec}
    except Exception as e:
        return {"ok": False, "slug": slug, "issues": [f"exception:{type(e).__name__}"], "error": str(e)[:500]}


def load_done(out_dir: pathlib.Path) -> dict:
    """Load per-category output files -> slug -> record dict (for resume)."""
    done = {}
    for p in out_dir.glob("*.json"):
        if p.name.endswith(".failed.json"):
            continue
        try:
            arr = json.loads(p.read_text(encoding="utf-8"))
            for rec in arr:
                if isinstance(rec, dict) and rec.get("slug"):
                    done[rec["slug"]] = rec
        except Exception:
            pass
    return done


def write_category(out_dir: pathlib.Path, category: str, records: list):
    out_dir.mkdir(parents=True, exist_ok=True)
    records = sorted(records, key=lambda r: r["slug"])
    (out_dir / f"{category}.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def append_failure(out_dir: pathlib.Path, entry: dict):
    fp = out_dir / "_failures.jsonl"
    with fp.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="glossary_live.json path")
    ap.add_argument("--out", required=True, help="output directory (rebuilt-v2)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", default="", help="comma-separated slugs to include")
    ap.add_argument("--category", default="", help="only process this category")
    ap.add_argument("--limit", type=int, default=0, help="cap total terms processed (debug)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--force", action="store_true", help="re-rewrite even if already present")
    args = ap.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if not api_key:
        print("ERROR: need ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN", file=sys.stderr)
        sys.exit(2)

    in_path = pathlib.Path(args.input)
    out_dir = pathlib.Path(args.out)
    data = json.loads(in_path.read_text(encoding="utf-8"))
    terms = data["terms"] if isinstance(data, dict) and "terms" in data else data
    if not isinstance(terms, list):
        print("ERROR: input is not a list of terms", file=sys.stderr)
        sys.exit(2)

    valid_slugs = {t["slug"] for t in terms if t.get("slug")}

    # Filters
    only = set(s.strip() for s in args.only.split(",") if s.strip())
    if only:
        terms = [t for t in terms if t.get("slug") in only]
    if args.category:
        terms = [t for t in terms if t.get("category") == args.category]

    done = {} if args.force else load_done(out_dir)
    todo = [t for t in terms if t["slug"] not in done]
    if args.limit:
        todo = todo[: args.limit]

    print(f"Model: {args.model}")
    print(f"Input total: {len(terms)} | already done: {len(done)} | to rewrite: {len(todo)}")
    if not todo:
        print("Nothing to do.")
        return

    by_category = defaultdict(list)
    for rec in done.values():
        by_category[rec.get("category", "uncategorized")].append(rec)

    # Concurrent rewrite with rolling flush per category
    failures = 0
    successes = 0
    t0 = time.time()

    def flush(cat):
        write_category(out_dir, cat, by_category[cat])

    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(rewrite_one, t, valid_slugs, api_key, args.model): t for t in todo}
        flush_every = max(5, len(todo) // 40)  # flush ~40 times total
        processed = 0
        for fut in cf.as_completed(futures):
            t = futures[fut]
            processed += 1
            res = fut.result()
            slug = res["slug"]
            if res["ok"]:
                rec = res["record"]
                cat = rec.get("category", "uncategorized")
                by_category[cat] = [r for r in by_category[cat] if r["slug"] != slug]
                by_category[cat].append(rec)
                successes += 1
                if processed % flush_every == 0:
                    flush(cat)
                    elapsed = time.time() - t0
                    rate = processed / elapsed if elapsed else 0
                    eta = (len(todo) - processed) / rate if rate else 0
                    print(f"[{processed}/{len(todo)}] ok={successes} fail={failures} rate={rate:.2f}/s eta={eta:.0f}s last={slug}", flush=True)
            else:
                failures += 1
                append_failure(out_dir, {"slug": slug, "title": t.get("title"), **{k: v for k, v in res.items() if k != 'record'}})
                print(f"[{processed}/{len(todo)}] FAIL {slug}: {res.get('issues')}", flush=True)

    # Final flush for every touched category
    for cat in by_category:
        flush(cat)

    print(f"\nDONE. ok={successes} fail={failures} elapsed={time.time()-t0:.1f}s")
    print(f"Output: {out_dir}")


if __name__ == "__main__":
    main()
