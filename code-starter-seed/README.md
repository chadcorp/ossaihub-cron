# OSS AI Hub Code Library — Source

This directory is the **canonical source** of every Code Starter in the OSS AI Hub Code Library at https://ossaihub.com/resources/code.

## Why this lives in a public repo

We publish the library content openly for the same reason we publish our cron pipeline: **trust is plumbing**. You can audit what's in the library, propose new starters, fix bad code, and watch the changes flow to production via GitHub Actions.

## How it works

```
manifest.yml                   ← human-curated list of starters (slug + title + brief)
        │
        ▼
[Generate workflow]            ← calls Anthropic API once per entry, fills the v2 schema
        │
        ▼
rebuilt-v2.json                ← machine-generated, committed to repo, hand-editable
        │
        ▼
[Push workflow]                ← validates + chunks + POSTs to Base44 /functions/upsertCodeStarter
        │
        ▼
ossaihub.com/code/{slug}       ← live on the site
```

## Add a new code starter

1. Edit `manifest.yml`. Append an entry under the appropriate category:
   ```yaml
   - slug: your-kebab-case-slug
     title: "Your Starter Title"
     category: one-of-the-20-enums-in-_schema.json
     language: python
     framework: FastAPI
     brief: "One or two sentences describing what this starter does."
     tags: [tag1, tag2]
     best_for_tags: [use-case-1, use-case-2]
   ```

2. Run the **Code Starter v2 — Generate** workflow (Actions tab → Run workflow). Optionally set `only_slugs: your-slug` to generate just yours.

3. The workflow will commit `rebuilt-v2.json` with your entry filled in by Claude using the v2 schema (TL;DR, when-to-use, full code, dependencies, env vars, setup steps, variations, common errors, production checklist, tested-with, related tools/glossary/learn, FAQ).

4. The push to `main` triggers the **Code Starter v2 — Push** workflow, which validates the JSON against `_schema.json` and POSTs to Base44. Within ~2 minutes it's live at `https://ossaihub.com/code/your-slug`.

## Edit an existing entry by hand

You can edit `rebuilt-v2.json` directly (find your slug in the array). Push to `main`; the Push workflow syncs the change. Keep edits aligned with the schema in `_schema.json` — CI will reject any drift.

## Regenerate from scratch

Run **Generate** with `skip_existing: false` to regenerate every entry. Useful when prompting changes upstream.

## Secrets the workflows need

- `ANTHROPIC_API_KEY` — for the generator
- `TOOLS_UPSERT_API_KEY` — for pushing to Base44 (re-uses the existing secret already used by glossary-v2-push)

## Schema

See `_schema.json` for the canonical v2 record shape. Every record on `main` must validate against it.

## Why JSON instead of Markdown?

JSON gives us atomic field updates (e.g. just regenerating `common_errors` for an entry), structured cross-linking (`related_tool_slugs` arrays), and CI-grade validation. Markdown would be friendlier to read but lossy under automation.
