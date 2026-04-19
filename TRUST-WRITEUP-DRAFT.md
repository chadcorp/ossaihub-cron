# How We Rebuilt OSS AI Hub's Data Layer — And Why We're Telling You

*A confession, an engineering story, and a promise.*

---

## What the directory is

OSS AI Hub is a curated catalog of open-source AI tools — 1,351 of them at the time of writing, across 15 categories from LLMs and agent frameworks to robotics simulators and MCP infrastructure. The promise to a developer landing on the site is simple: *these tools are real, the numbers are accurate, and the links work.*

For a while, that promise was partly theater. This post explains what was wrong, how we found out, and what we did to fix it. It also lays out what's still broken, because we'd rather you hear that from us than discover it yourself.

---

## The problem

Two days ago, the directory had problems we're not proud of.

- **9 tools with fabricated star counts** (~70,000 stars in aggregate) pointing at GitHub URLs that didn't exist. Some pointed at org pages with no repo. One claimed to be a "breakout 2026 autonomous agent" with 360,000 stars — a tool nobody had ever heard of, because it had never been written.
- **140 duplicate rows.** AutoGPT appeared twice with conflicting star counts. Dify appeared three times. LangFlow twice. The leaderboard rendered these as separate ranked entries, making the same tool compete against itself.
- **Severe cross-category drift.** Ollama is legitimately listed in 5 categories (LLMs, AI Coding, MLOps, AI DevOps, Mobile). Its star count drifted across those rows: **166,825 / 164,000 / 169,383 / 95,000 / 0**. Same tool. Five different "truths."
- **~275 dead links.** GitHub URLs pointing at repos that had been renamed, deleted, or made private — but still clickable on our site, still showing stale star counts, still being recommended.
- **"Trusted by 12,400+ developers • Meta, Hugging Face, NVIDIA"** on the homepage. No evidence. No citation. Classic directory theater.
- **Inconsistent top-line numbers.** The page title said "1,600+ tools." The hero said "1,544+." The banner said "1,500+." The database actually had 1,536. Four numbers, zero of them right.

If a developer landed on the site and spot-checked two tools against GitHub, odds were decent they'd catch one of them wrong. That's the kind of first impression you don't get a second chance at.

---

## The troubleshooting

We sat down and treated the site the way a developer auditing it for the first time would. Pretending to be an outsider is the only way to catch what you've stopped seeing.

**Step one was a page-by-page audit.** Homepage, leaderboard, category pages, tool detail pages, stack builder, prompts library, blog, submit flow. We logged every inconsistency: numbers that didn't match, badges that shouldn't be there, placeholder text that had leaked into production (one blog post had the literal string `**Slug suggestion**: nvidia-nemoclaw-safe-local-agents-2026` showing as its tag), install commands that didn't work (`pip install n8n` for a Node.js-only tool), tools categorized wrong (n8n filed under "LLMs & Foundation Models").

**Step two was rigorous data analysis** of the raw tool export. We grouped every row by normalized github_url (lowercase, strip trailing slash, strip `.git`) and found the shape of the damage:

- 1,536 total rows, but only 1,164 unique GitHub URLs
- 85 "legitimate" groups (same tool, different categories)
- 140 "true duplicate" groups (same tool, same category, different star counts — classic staleness)
- 11 rows with null licenses, 5 with null GitHub URLs, 4 more with GitHub "org-only" URLs (no repo path)

**Step three was tracing the root cause.** The answer had two parts:

1. **Discovery tools hallucinated.** When new tools came in via AI-assisted scraping, a small percentage were fabricated — plausible-sounding repos that didn't actually exist. Manual curation caught the obvious ones. It didn't scale. Errors compounded with every batch.
2. **The data layer had no heartbeat.** Star counts, fork counts, last-commit dates — all static fields written once and never refreshed. Every few weeks, someone would ask for a "star count refresh" and the numbers would get updated manually, but within a week they'd drift again. There was no scheduled job pulling from GitHub. Accuracy wasn't broken in one big way; it was broken every day, slowly.

That second finding was the important one. A directory without a live data pipeline isn't a broken directory — it's a *snapshot*. Nobody said that out loud, but the incentives were shaped around it.

---

## The solution

We rebuilt the data layer from the outside in. Four pieces.

### 1. An external nightly refresh job

Every night at 06:17 UTC, a GitHub Actions workflow runs in a public repo — [chadcorp/ossaihub-cron](https://github.com/chadcorp/ossaihub-cron). It:

- Fetches the full directory from our own public JSON endpoint
- Queries GitHub's GraphQL API in batches of 100 for live star counts, fork counts, last-commit timestamps, archive state, and license info
- Automatically flags any repo GitHub reports as `NOT_FOUND` (renamed/deleted) so it disappears from discovery
- Skips repos already flagged, so rate-limit budget is spent on what actually needs updating
- Posts batched updates back to our database with retry on transient failures

We put the job outside the app on purpose. If the app changes, the data layer doesn't. The script is short, readable, and public — you can go look at it right now.

### 2. A four-gate validator for every new submission

Every candidate tool — whether community-submitted or surfaced by our daily discovery pipeline — passes four independent gates before reaching the directory:

1. **GitHub URL uniqueness** (normalized: lowercase, no trailing slash, no `.git` suffix) — can't match an existing record
2. **Slug uniqueness** — can't conflict with an existing slug
3. **Fuzzy name match** — catches "HuggingFace Transformers" vs "Hugging Face Transformers" before they both land in the directory
4. **GitHub repository must exist and meet quality bars:** ≥500 stars, committed to within the last 180 days, non-null license, not archived on GitHub

Gates 1–3 kill duplicates at the door. Gate 4 is an unfakeable source of truth — if a candidate's github_url 404s, it's rejected. Hallucinations have nowhere to land.

### 3. Multi-row updates for legitimate cross-category listings

Some tools genuinely belong in multiple categories — Ollama is a runtime AND a deployment tool AND a coding helper AND a mobile-capable model server. Keeping those as separate rows is legitimate. Letting their star counts drift apart is not.

We rewrote the upsert logic so that a single refresh call finds every row matching a normalized github_url and updates them all in one transaction. Ollama's 5 category rows now refresh together. Same tool, same number, everywhere it appears.

### 4. Cleanup of every identified trust leak

In parallel with the infrastructure work, we made the visible fixes:

- Deleted 9 tools with invalid/missing GitHub URLs
- Removed fabricated social proof from the homepage
- Removed "enterprise" badges on MIT-licensed open-source projects
- Fixed the leaderboard and homepage ranked views so cross-category tools dedupe before ranking (AutoGPT, Hugging Face Transformers, and Ollama now appear exactly once, ranked by their unified star count)
- Reconciled every tool-count claim on the site against the live database

---

## The numbers, before and after

| Measurement | Before | After |
|---|---|---|
| Total tool records | 1,536 | 1,351 |
| True duplicate groups | 140 | 0 |
| Tools with invalid or missing GitHub URLs | 9 | 0 |
| Known hallucinated/fabricated tools | at least 5 | 0 |
| Dead GitHub links visible on the site | ~275 | 0 (all archived out of discovery) |
| Cross-category records with drifted star counts | ~85 groups | 0 |
| Homepage tool-count claim vs database | off by 249 | exact match |
| Automated nightly data refresh | none | live at 06:17 UTC daily |

Click any tool on the site and the GitHub link goes to a real, live repository. Its star count matches GitHub within the last 24 hours. Tomorrow night, it updates again.

---

## What's still broken

The secret weapon of any honest post-mortem is naming what's not fixed yet:

- **85 tools are legitimately listed in 2–5 categories each.** The current schema uses one row per `(tool, category)` pair — 1,351 rows for ~1,164 unique tools. A cleaner shape is a single row per tool with a `categories: string[]` array. Planned, not shipped. Functionally the data is now correct; structurally it could be leaner.
- **License strings are inconsistent.** "Apache 2.0" (54 tools) and "Apache-2.0" (579 tools) should be one value. Same with BSD variants. Cosmetic, but careless-looking. Normalization is next on the list.
- **Community-estimated benchmarks still exist on some tool pages** where the project didn't publish official numbers. They're labeled as estimates, but we'd rather have contributor-verified benchmarks with "Verified Use" badges tied to GitHub identity. That's a bigger lift.
- **Discovery isn't autonomous.** Every day, candidates are surfaced and a human reviews each one against the four-gate validator before anything reaches the directory. This is the expensive way. We're keeping it that way. Speed at the cost of accuracy isn't a trade we're willing to make.

---

## How we'll keep it honest

Three numbers will live on a public `/data-health` page (shipping soon):

- **Staleness** — percentage of tools whose star count differs from GitHub's current value by more than 5%. Target: under 1%.
- **Dead-link rate** — percentage of tool detail pages whose GitHub link returns 404. Target: 0%.
- **Duplicate rate** — true-duplicate groups in the directory. Target: 0.

If any of those numbers drift, the cron will catch it, and the page will show it. We'd rather you see the problem forming than find out about it from an angry post.

The cron repo is public: [github.com/chadcorp/ossaihub-cron](https://github.com/chadcorp/ossaihub-cron). The script is 150 lines. If you find a bug, open an issue.

---

## How you can help

- **Submit a tool you actually use.** The four-gate validator means low-effort submissions are fine — we catch most errors automatically before the queue reaches a human reviewer.
- **Tell us when we're wrong.** If a tool on the site is stale, dead, or miscategorized — flag it. A "Report inaccuracy" link is coming to every tool detail page.
- **Star the cron repo** if the approach is useful for your own directory projects. Steal it. That's why it's public.

The directory exists for developers who don't have time to vet 1,500 GitHub repos a week. Our job is to do that vetting honestly. The work above is the receipts.

— The OSS AI Hub Team

---

*If you've been burned by directories before: we get it. This post is the apology in advance. The metrics are the proof.*
