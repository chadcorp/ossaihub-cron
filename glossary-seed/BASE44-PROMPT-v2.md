# Base44 Prompt — Glossary v2 Schema + UI + Upsert + JSON-LD (bundled)

Paste this into the Base44 chat for the OSS AI Hub app. Single bundled prompt
(per the bundled-prompt workflow). After Base44 publishes, the cron pushes
526 v2-enriched glossary entries that depend on these new fields and the new
`upsertGlossaryTerm` function.

CRITICAL: after Publish, re-check the diff on the /glossary/{slug} page before
accepting — Base44 has auto-modified useSEO handlers mid-deploy before
(2026-04-23). Verify the page renders all 10 sections AND JSON-LD scripts
appear in page source before closing the loop.

---

```
Rebuild the glossary into the v2 schema — snippet-ready TL;DR, scannable
sections, FAQ schema, upsert endpoint, and rich JSON-LD. Four blocks below:
apply together, publish together. The cron depends on all four shipping at once.

BLOCK 1 — EXTEND the GlossaryTerm entity with these NEW fields (preserve all
existing fields; do not rename or drop anything — old entries roll back cleanly):

  - tldr (string, ≤200 chars) — ONE-sentence plain-English answer to "what is X";
    reused verbatim as <meta name="description">. If null, fall back to
    short_definition.
  - plain_english (long text) — 2-3 sentences, zero undefined jargon.
  - how_it_works (long text) — mechanics in 3-6 sentences or a bullet paragraph.
  - example (long text) — one concrete scenario, ideally with real
    company/team/numbers.
  - pitfalls (array of strings) — 2-4 specific pitfalls.
  - when_use (string) — one-sentence decision rule.
  - when_avoid (string) — one-sentence decision rule.
  - faq (array of { q: string, a: string } objects) — 3-5 real-search-query
    Q&A pairs; powers FAQPage JSON-LD.
  - meta_title (string, ≤90 chars) — rendered into <title>.
  - meta_description (string, ≤155 chars) — rendered into <meta name="description">.
  - schema_jsonld (object) — pre-built { DefinedTerm, FAQPage } JSON-LD. If
    null, the page builds it dynamically from tldr + faq.
  - rewrite_version (string) — "v1" | "v2"; defaults to "v1" for legacy rows.

Keep these v1 fields intact — they are the fallback when v2 fields are null:
  short_definition, full_explanation, why_it_matters, common_misconceptions,
  code_example, related_terms, related_tools, related_prompts, seo_variations,
  difficulty_tier, upvotes, comment_count, view_count, status.

BLOCK 2 — RENDER the /glossary/{slug} detail page in this exact order. Each
section must skip itself silently if its v2 field is null/empty AND the v1
fallback is also empty (no empty headers).

  1. <h1>{title}</h1>
  2. Badges row: category, difficulty_tier, and a "v2" rewrite-version chip if
     rewrite_version === "v2" (small, muted, dev-only).
  3. "TL;DR" h2 → render tldr (v2). Fall back to short_definition if null.
     Snippet-first styling: large text, generous line-height, no surrounding
     decoration that would confuse Google's snippet picker.
  4. "In Plain English" h2 → render plain_english (v2).
     Fall back: if null, use the first 2 sentences of full_explanation.
  5. "How It Works" h2 → render how_it_works (v2) as paragraph(s) (split on \n\n).
     Fall back: use full_explanation.
  6. "Why It Matters" h2 → render why_it_matters (unchanged field).
  7. "Example in Practice" h2 → render example (v2). SKIP section if null.
  8. "Common Pitfalls" h2 → render pitfalls (v2) as <ul><li>. SKIP if empty.
     v1 fallback: if common_misconceptions is non-null, render it here as a
     single highlighted callout instead.
  9. "When to Use / When to Avoid" h2 → two-column layout:
        ✓ When to Use: {when_use}
        ✗ When to Avoid: {when_avoid}
     SKIP section if both null.
  10. "Code Example" h2 → render code_example in a Prism.js code block. SKIP
      if null. (Preserve existing behavior.)
  11. "Related Terms" h2 → chips linking to /glossary/{related_slug} for each
      entry in related_terms. Fetch title + tldr (or short_definition) per
      target and show tldr in muted text on hover/expand.
  12. "Related Tools" h2 → existing card rendering, preserved.
  13. "Related Prompts" — preserved; render only if non-empty.
  14. "FAQ" h2 → render faq (v2) as <details><summary> accordion. SKIP if
      empty. Each Q is <summary>; A is the expanded body.
  15. Previous / Next nav within same category — preserved.

Add a new badge + announcement block above the fold on /glossary/{slug}:
  "Updated 2026-04-24 — rewritten for v2 plain-English format."
  Only show if rewrite_version === "v2" AND updated_date within 60 days.
  Muted, small, dismissable.

BLOCK 3 — UPGRADE JSON-LD on the detail page. Emit THREE <script type="application/ld+json">
blocks in this order:

  a) DefinedTerm (required, uses v2 tldr for description):
     {
       "@context": "https://schema.org",
       "@type": "DefinedTerm",
       "name": title,
       "description": tldr || short_definition,
       "inDefinedTermSet": "https://ossaihub.com/Glossary",
       "url": "https://ossaihub.com/glossary/{slug}",
       "termCode": slug
     }

  b) FAQPage (required if faq has ≥1 entry — otherwise skip the block entirely):
     {
       "@context": "https://schema.org",
       "@type": "FAQPage",
       "mainEntity": faq.map(q => ({
         "@type": "Question",
         "name": q.q,
         "acceptedAnswer": { "@type": "Answer", "text": q.a }
       }))
     }

  c) BreadcrumbList (new, helps Google understand site hierarchy):
     {
       "@context": "https://schema.org",
       "@type": "BreadcrumbList",
       "itemListElement": [
         { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://ossaihub.com/" },
         { "@type": "ListItem", "position": 2, "name": "Glossary", "item": "https://ossaihub.com/Glossary" },
         { "@type": "ListItem", "position": 3, "name": title, "item": "https://ossaihub.com/glossary/{slug}" }
       ]
     }

If schema_jsonld is non-null on the entity, prefer it verbatim for DefinedTerm
and FAQPage (the cron pre-builds these) — only synthesize locally when null.

ON the /Glossary INDEX page only, add a fourth block:
  DefinedTermSet:
  {
     "@context": "https://schema.org",
     "@type": "DefinedTermSet",
     "@id": "https://ossaihub.com/Glossary",
     "name": "OSS AI Hub AI Glossary",
     "description": "Plain-English definitions of every term in modern AI — rewritten for rookies and experts.",
     "url": "https://ossaihub.com/Glossary",
     "hasDefinedTerm": glossary.map(t => ({
       "@type": "DefinedTerm",
       "name": t.title,
       "termCode": t.slug,
       "url": "https://ossaihub.com/glossary/" + t.slug
     }))
  }

Also update the dynamic <title> and <meta name="description"> on detail pages:
  <title>{meta_title || title + " — Plain-English Definition & Expert Guide | OSS AI Hub"}</title>
  <meta name="description" content="{meta_description || tldr || short_definition}">
  <meta property="og:title" content="same as title">
  <meta property="og:description" content="same as description">
  <link rel="canonical" href="https://ossaihub.com/glossary/{slug}">

These MUST populate inline in index.html (client-side useSEO hook + the inline
seed-from-data-attributes pattern from the 2026-04-23 canonical fix). Do NOT
rely solely on useEffect — Google's initial parse can miss it.

Also UPDATE the inline index.html script's `route === 'glossary'` branch to
match the v2 pattern — the existing branch emits a generic "AI Glossary" title
which Google sometimes wins over the React-upgraded title. Change to:

  } else if (route === 'glossary' && seg) {
    title = humanize(seg) + ' — Plain-English Definition & Expert Guide | OSS AI Hub';
    desc = 'Plain-English definition of ' + humanize(seg) + '. Expert guide with examples, pitfalls, decision rules, and FAQ. Built for open-source AI practitioners on OSS AI Hub.';
  }

The React useSEO hook then overrides with the real v2 tldr/meta_description
once glossaryApi data loads. Keep both so crawlers see a good title on the
initial HTML parse AND the real term-specific meta after React hydrates.

BLOCK 4 — CREATE a new PUBLIC function /functions/upsertGlossaryTerm:
  - POST only. Require API_KEY header (same TOOLS_UPSERT_API_KEY as toolsUpsert).
  - Body: { items: [ { slug, ...anyV2Field } ] }.
  - For each item, match by slug (unique). If row exists: UPDATE only the
    fields present in the payload (DO NOT clobber existing fields with
    undefined/null). If no row: CREATE new with status="approved", upvotes=0,
    comment_count=0, view_count=0, rewrite_version=item.rewrite_version||"v1".
  - When item.tldr is set AND item.short_definition is absent, also copy
    item.tldr into short_definition (back-compat for cards).
  - When item.how_it_works is set AND item.full_explanation is absent, copy
    how_it_works into full_explanation (same reason).
  - Process in chunks of 25 with Promise.allSettled and 500ms intra-batch
    delay. Return:
       { rows_updated, rows_created, rows_failed, errors: [{slug, message}] }
  - Rate-limit at the function level: 100 requests/minute per IP. If over,
    return 429 with { error: "rate_limited", retry_after_s: N }.

Verify after publish:

  curl -X POST https://base44.app/api/apps/69a91ff6770c8ca0347ae03d/functions/upsertGlossaryTerm \
    -H "Content-Type: application/json" -H "API_KEY: $KEY" \
    -d '{"items":[{"slug":"rag","tldr":"v2 smoke test","rewrite_version":"v2"}]}'
  expects: { "rows_updated": 1, "rows_created": 0, "rows_failed": 0 }

Then visit https://ossaihub.com/glossary/rag and confirm:
  - <title> ends with "— Plain-English Definition & Expert Guide | OSS AI Hub"
  - TL;DR section shows "v2 smoke test"
  - <meta name="description"> equals "v2 smoke test"
  - Three <script type="application/ld+json"> blocks in <head>: DefinedTerm,
    FAQPage (if faq populated), BreadcrumbList
  - Canonical link = https://ossaihub.com/glossary/rag

Final: update the sitemap. /functions/generateSitemap should already emit
/glossary/{slug} for every approved term — but set priority=0.8 (up from 0.7)
and changefreq=weekly for rows with rewrite_version="v2" and updated_date
within 90 days; the v1 rows stay at 0.7 + monthly.

Publish everything.
```

---

## Why bundled

Per the Base44 build-workflow preference: bundled prompts > sequential
single-step prompts. All four blocks share the same rebuild context, the
upsert function depends on the entity fields, the detail render depends on
both, and the JSON-LD depends on all of them. Asking Base44 to land them as
one PR cuts review/publish overhead and keeps state consistent — the last
time the v1.5 prompt was run piecemeal, entity fields landed without the
upsert function and the cron couldn't push. Don't repeat that.

## What this enables

Once published + verified:
1. Cron pushes 526 enriched v2 JSON entries via `upsertGlossaryTerm`.
2. Every detail page renders the full 10-section structure with JSON-LD.
3. Google gets FAQPage + DefinedTerm + BreadcrumbList schema — all three are
   rich-result eligible.
4. Old v1 rows keep rendering (fallback chain) until the cron reaches them.
5. Rollback is cheap: flip `rewrite_version=v1` on any row and the page falls
   back to short_definition/full_explanation/why_it_matters.

## Verification checklist (run these in order)

1. Paste this prompt into Base44, click Publish (per the publish-required memory).
2. Wait ~2 min for the deploy to propagate to the custom domain.
3. Run the curl smoke test in BLOCK 4 — expects `rows_updated: 1`.
4. Open https://ossaihub.com/glossary/rag, view source, confirm 3 JSON-LD blocks + canonical + <title>.
5. Re-check the Base44 useSEO diff (2026-04-23 saw auto-edit mid-deploy).
6. Only then trigger the cron workflow `seed-glossary-v2.yml` to push all 526.
