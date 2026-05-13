# OSS AI Hub Prompt Library — Source

This directory is the **canonical source** of every prompt in the OSS AI Hub Prompt Library at https://ossaihub.com/resources/prompts.

## Why this is public

Trust is plumbing. You can audit what's in the library, propose new prompts, fix bad ones, and watch the changes flow to production via GitHub Actions. Same pattern as our daily tool-audit cron.

## How it works

```
manifest.yml                   ← human-curated list of prompts (slug + title + brief)
        │
        ▼
[Generate workflow]            ← calls Anthropic API to fill the v2 schema per entry
        │
        ▼
rebuilt-v2.json                ← machine-generated, committed to repo, hand-editable
        │
        ▼
[Push workflow]                ← validates + chunks + POSTs to Base44 /functions/upsertPrompt
        │
        ▼
ossaihub.com/prompts/{slug}    ← live on the site
```

## Add a new prompt

1. Edit `manifest.yml`. Append an entry under the appropriate category:
   ```yaml
   - slug: your-kebab-case-slug
     title: "Your Prompt Title"
     category: one-of-the-18-enums-in-_schema.json
     brief: "One or two sentences describing what this prompt does."
     tags: [tag1, tag2]
     best_for_tags: [use-case-1, use-case-2]
   ```

2. Run **Prompt Library v2 — Generate** in the Actions tab. The workflow calls Claude using the v2 system prompt and commits `rebuilt-v2.json` with your entry filled in.

3. Push to `main` triggers **Prompt Library v2 — Push** which validates against `_schema.json` and POSTs to Base44.

## v2 schema (what every prompt entry contains)

- TL;DR (one sentence)
- Use cases (3-5 specific scenarios with examples)
- When NOT to use
- Full prompt (with `{variables}` highlighted)
- Input variables (name, type, description, required, example)
- Expected output (format + sample)
- Few-shot examples
- Model compatibility matrix (Claude 4, GPT-5, Gemini 2, Llama 3.3, Mistral Large 3, Qwen2.5 — with per-model notes)
- Variations (Concise / Chain-of-Thought / JSON-only / System-prompt / Function-calling)
- Failure modes + fixes
- Tested with (model versions, date)
- Related prompts, tools, glossary terms
- FAQ

See `_schema.json` for the full validation schema.

## Secrets

- `ANTHROPIC_API_KEY` — for generation
- `TOOLS_UPSERT_API_KEY` — for pushing to Base44
