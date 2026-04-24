# Base44 Prompt — Glossary Rebuild Schema + UI + Upsert

Paste this into the Base44 chat for the OSS AI Hub app. Single bundled prompt
(per the bundled-prompt workflow preference). After Base44 publishes, the cron
will push 526 enriched glossary entries that depend on these new fields.

---

```
Update GlossaryTerm entity, render new sections on the detail page, and add an upsert function. Three blocks below — apply all together and publish.

BLOCK 1 — ADD 3 NEW FIELDS to the existing GlossaryTerm entity (preserve all existing fields):
  - how_to_think_about_it (long text, nullable) — 80–120 word mental model / analogy section
  - see_it_in_practice (long text, nullable) — 50–100 word concrete example, optional per term
  - related_terms_explained (array of objects, nullable) — each item is { "slug": "...", "connection": "..." } where connection is a 1-sentence explanation of how that related term connects to this term

Do NOT remove or rename any existing fields. The cron will keep populating short_definition, full_explanation, why_it_matters, related_terms (slugs only — kept for backward compat), code_example, common_misconceptions, seo_variations.

BLOCK 2 — UPDATE the /glossary/{slug} detail page render order to:
  1. H1 = title
  2. Badges row: category, difficulty_tier
  3. "Plain English Definition" h2 → render short_definition
  4. "What It Actually Means" h2 → render full_explanation as paragraphs (split on \n\n)
  5. "Why It Matters" h2 → render why_it_matters
  6. "How To Think About It" h2 → render how_to_think_about_it (skip section if field is null/empty)
  7. "See It In Practice" h2 → render see_it_in_practice (skip section if field is null/empty)
  8. "Code Example" → render code_example as Prism.js syntax-highlighted block (skip if null)
  9. "Common Misconceptions" → highlighted callout if common_misconceptions is non-null (deprecated, kept for old entries)
  10. "Related Terms" → if related_terms_explained is non-empty, render as a list where each row shows the linked term title + the connection sentence in muted text below. If related_terms_explained is empty BUT related_terms (slug array) is non-empty, fall back to the existing chip rendering. Always link to /glossary/{related_slug}.
  11. "Related Tools" → cards linking to /tool/{slug}, fetched from Tool entity (preserve existing render).
  12. "Related Prompts" → only render section if non-empty (preserve existing).
  13. Previous / Next within same category (preserve existing).

Add JSON-LD on the detail page: keep the existing DefinedTerm + FAQPage blocks. ADD a third block — DefinedTermSet pointer — only on the index /Glossary page.

BLOCK 3 — CREATE a new public function /functions/upsertGlossaryTerm:
  - POST, body = { items: [ { slug, title?, category?, difficulty_tier?, short_definition?, full_explanation?, why_it_matters?, how_to_think_about_it?, see_it_in_practice?, related_terms_explained?, related_terms?, related_tools?, code_example?, common_misconceptions?, seo_variations? } ] }
  - Match each item by slug (unique). If exists: UPDATE only the fields present in the payload (do not clobber existing fields with undefined/null). If not exists: CREATE new GlossaryTerm with status="approved", upvotes=0, comment_count=0, view_count=0.
  - Require API_KEY header (same TOOLS_UPSERT_API_KEY as toolsUpsert).
  - Process in chunks of 50 with Promise.allSettled and 500ms inter-chunk delay (same pattern as toolsUpsert).
  - Return JSON: { rows_updated, rows_created, rows_failed, errors: [{slug, message}] }

Verify after publish:
  curl -X POST https://base44.app/api/apps/69a91ff6770c8ca0347ae03d/functions/upsertGlossaryTerm \
    -H "Content-Type: application/json" -H "API_KEY: $KEY" \
    -d '{"items":[{"slug":"rag","how_to_think_about_it":"smoke-test value"}]}'
  expects { rows_updated: 1, rows_created: 0, rows_failed: 0 }

Then visit https://ossaihub.com/glossary/rag and confirm the "How To Think About It" section renders the smoke-test text.

Publish.
```

---

## Why bundled

Per the Base44 build-workflow preference: bundled prompts > sequential
single-step prompts. All three blocks share the same rebuild context, the
upsert function depends on the schema, and the UI renders the new fields. Asking
Base44 to land them as one PR cuts review/publish overhead and keeps state
consistent.

## What this enables

Once published:
1. Cron pushes the 526 enriched JSON entries via `upsertGlossaryTerm`.
2. New `how_to_think_about_it` + `see_it_in_practice` + `related_terms_explained`
   render automatically on every detail page.
3. Old fields (short_definition, full_explanation, why_it_matters) get
   rewritten to match the new prompt's voice.
4. Existing related_terms (slug-only array) preserved as fallback for any term
   the cron hasn't touched yet.
