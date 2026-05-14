"""Multimodal prompts — image, OCR, chart-reading, screenshot description, diagrams."""

RECORDS = [
    {
        "slug": "screenshot-bug-report-builder",
        "title": "Screenshot Bug Report Builder",
        "tldr": "Reads a screenshot of a UI bug and emits a complete bug report: what's wrong, expected vs. observed, where exactly on the screen, reproduction steps, and severity rationale.",
        "category": "multimodal",
        "tags": ["vision", "bug-report", "qa", "screenshot", "multimodal"],
        "best_for_tags": ["qa-teams", "support-triage", "internal-bugs"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Customer sends screenshot of broken page", "example": "Get back a structured bug report with severity rationale instead of forwarding the screenshot to engineering with ‘pls help’."},
            {"scenario": "QA engineer batch-processing test failures", "example": "20 failure screenshots → 20 structured reports overnight."},
            {"scenario": "Internal user reporting a glitch on Slack", "example": "Drop screenshot into a bot; bot files structured Linear ticket."},
            {"scenario": "PM reviewing release candidate", "example": "Annotated visual diff produces a clean punch list of issues."},
        ],
        "when_not_to_use": "Skip when the bug is non-visual (race conditions, performance, backend). The screenshot won't show what matters and the report will fabricate plausible-sounding but wrong details.",
        "full_prompt": """You are a senior QA engineer reading a screenshot of a UI bug. Produce a bug report.

OUTPUT STRUCTURE

## Summary (one sentence)
What's wrong, plainly.

## Expected behavior
What the UI should show or do based on visible context (form labels, button text, surrounding state).

## Observed behavior
What it's actually showing. Be specific about element location ("the third row of the table", "the button labeled 'Save'").

## Severity
Choose: blocker | major | minor | cosmetic. Justify in one sentence.

## Reproduction (guesses)
3–5 plausible steps to reproduce. Mark any step you're uncertain about with [?].

## Visual coordinates
Approximate location of the bug on the screen (top-left / center / etc.) and any annotations a developer should look at first.

## What I CAN'T tell from this screenshot
Be explicit about gaps: device/browser, console state, network, what the user did before this point. List them.

## Suggested triage owner
Frontend / backend / design / unclear — based only on what's visible.

RULES
- Do NOT invent error messages or fields not visible in the screenshot.
- If you read text from the UI, use exact quotes in quotation marks.
- If the screenshot is ambiguous, say so — don't smooth it over.

USER NOTE (optional)
{user_note}

Now describe the bug.""",
        "input_variables": [
            {"name": "user_note", "type": "string", "description": "Optional context from the reporter", "required": False, "example": "Happens after I click ‘Save’ on the second tab"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Headed sections including expected/observed, severity with justification, repro guesses with [?] markers, and explicit ‘can't tell’ section.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at locating elements precisely and refusing to fabricate non-visible details."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally guesses at error codes — re-pin the ‘no inventing’ rule."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Handles dense screenshots well; can miss subtle visual cues (overlapping elements)."},
            {"model": "llama-3.2-vision", "compatibility": "fair", "notes": "Coarser localization; useful for obvious bugs, not edge cases."},
        ],
        "variations": [
            {"label": "Linear-ready", "description": "Emit as a Linear-formatted markdown ticket.", "prompt_snippet": "Wrap output in Linear ticket fields: title, description, labels (suggested), priority (mapped from severity)."},
            {"label": "Multi-screenshot batch", "description": "Several screenshots at once.", "prompt_snippet": "Accept N screenshots in order; emit one report per screenshot plus a final ‘common root cause?’ note."},
            {"label": "Annotated overlay", "description": "Suggest annotations.", "prompt_snippet": "Add: ‘suggest 1–3 arrow/box overlays a designer should add before sharing with engineering.’"},
        ],
        "failure_modes": [
            {"symptom": "Invents error messages not in the screenshot.", "fix": "Re-pin ‘exact quotes only; if text isn't visible, don't reference it.’"},
            {"symptom": "Severity always ‘major’.", "fix": "Show severity ladder with specific anchor examples and ask the model to map this case to the closest anchor."},
            {"symptom": "Repro steps too confident.", "fix": "Add ‘every step marked [?] until verified; first turn produces guesses, not facts.’"},
            {"symptom": "Misreads UI element type (button vs link).", "fix": "Add: ‘describe each element by what you see, not what it functionally is.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3.2-vision"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["support-ticket-triage", "structured-extraction-from-docs"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["multimodal", "vision-models", "bug-triage"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Will it leak sensitive info from the screenshot?", "answer": "If the screenshot includes PII, the model will repeat what it sees. Redact before sending or use a PII redaction pass first."},
            {"question": "Can it tell whether it's a frontend or backend bug?", "answer": "Often — by visible cues like ‘500 error’ vs UI alignment. But it should mark its certainty; treat as a triage hint, not a final answer."},
            {"question": "What if the screenshot is low resolution?", "answer": "Output will mark visual coordinates as approximate and call out anything illegible. Re-shoot if critical details are blurred."},
        ],
        "meta_title": "Screenshot Bug Report Builder — Prompt",
        "meta_description": "Turn a UI screenshot into a structured bug report with expected vs observed, severity rationale, and an explicit ‘can't tell from this’ list.",
    },
    {
        "slug": "chart-extractor-to-table",
        "title": "Chart-to-Table Data Extractor",
        "tldr": "Reads a chart image (bar, line, pie, scatter) and outputs the underlying data as a structured table — with explicit notes on values it couldn't read precisely.",
        "category": "multimodal",
        "tags": ["chart", "data-extraction", "vision", "ocr", "multimodal"],
        "best_for_tags": ["research", "competitive-intel", "data-recovery"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Research paper chart without underlying data", "example": "Extract the bar chart from a 2023 NeurIPS paper into a CSV-ready table for re-analysis."},
            {"scenario": "Competitor's earnings deck", "example": "Pull revenue chart values from a PDF screenshot into a spreadsheet."},
            {"scenario": "Slide deck data recovery", "example": "Source file lost; chart in old slide is the only record. Recover values."},
            {"scenario": "Industry report charts", "example": "Pull data from charts in PDF reports for citation and further analysis."},
        ],
        "when_not_to_use": "Skip when precise values matter (financial reporting, regulatory filings) — chart extraction has 1–5% error baseline. Use only when ‘close enough’ is fine.",
        "full_prompt": """You are a chart-to-data extractor. Read the chart image and emit the underlying data.

OUTPUT FORMAT
```
chart_type: bar | line | pie | scatter | stacked-bar | other
title: as shown
x_axis: { label, units, scale: linear|log|categorical, range }
y_axis: { label, units, scale, range }
series:
  - name: ...
    points: [{x: ..., y: ..., notes?: ...}, ...]
notes:
  - any axis-label readings you're uncertain about
  - any data points that overlap or are hard to read
  - any legend ambiguity
confidence_overall: high | medium | low
```

RULES
1. Read axis labels exactly. If you can't read them, mark "[unreadable]" — don't guess.
2. For each data point, give your best read. If estimating between gridlines, mark with ~ (e.g., "~42").
3. If a chart has multiple series, identify each by legend color/pattern. If the legend is unclear, note it.
4. If gridlines aren't visible, your estimates will be coarser — say so in notes.
5. Never invent precision. "150" is a claim of accuracy; "~150" admits estimation.

OPTIONAL HELP
{additional_context}

Now extract.""",
        "input_variables": [
            {"name": "additional_context", "type": "string", "description": "Optional caption, paper context, or units hint", "required": False, "example": "Chart is from Q3 2024 earnings, units are millions USD"},
        ],
        "expected_output": {
            "format": "structured",
            "schema": "YAML-like structure: chart_type, title, x_axis, y_axis, series with points, notes, confidence_overall",
            "sample": "chart_type: bar\ntitle: Revenue by Quarter\nx_axis: { label: Quarter, units: -, scale: categorical, range: Q1–Q4 }\n...",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at axis reading and at marking uncertain values with ~."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; on dense scatter plots, sometimes drops outliers."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid on bar/line; weaker on scatter."},
            {"model": "llama-3.2-vision", "compatibility": "fair", "notes": "Useful for general shape; precise values often off by 10–20%."},
        ],
        "variations": [
            {"label": "CSV-only", "description": "Output just CSV.", "prompt_snippet": "Replace structured output with: ‘output CSV only, with a header row and one row per data point. Estimated values prefixed with ~.’"},
            {"label": "Critique the chart", "description": "Note presentation issues.", "prompt_snippet": "Add: ‘then write 3 bullets on what makes this chart hard to read (truncated axes, missing units, color-on-color, etc.).’"},
            {"label": "Multi-chart batch", "description": "Process N charts.", "prompt_snippet": "Accept multiple chart images; emit one structured table per chart with a shared run summary at the end."},
        ],
        "failure_modes": [
            {"symptom": "Output claims precision it can't have (no ~ on estimated values).", "fix": "Re-pin ‘~ for any value not on a labeled gridline.’"},
            {"symptom": "Invents axis labels.", "fix": "Add: ‘if axis text is unreadable, write [unreadable]; never guess.’"},
            {"symptom": "Misses outliers on dense scatter.", "fix": "Add: ‘call out the highest, lowest, and 3 most-isolated points explicitly.’"},
            {"symptom": "Legend mismatch (wrong series labeled).", "fix": "Add: ‘read the legend last, after points; then assign series; flag any color overlap.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3.2-vision"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["structured-extraction-from-docs", "metric-anomaly-explainer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["ocr", "multimodal", "data-extraction"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How accurate is the extraction?", "answer": "On clean bar/line charts with gridlines, 95%+. On scatter plots or unclear legends, 80–90%. Always validate critical values against the chart visually."},
            {"question": "Will it work with handwritten charts?", "answer": "Better than you'd think — but handwritten axes are often the failure point. Add high-quality OCR pre-pass if axis labels are crucial."},
            {"question": "Can I extract from a screenshot of a Tableau dashboard?", "answer": "Yes, but if you can get to the raw data via the tool's export, that's always cleaner. Use vision extraction when raw data isn't available."},
        ],
        "meta_title": "Chart-to-Table Data Extractor — Prompt",
        "meta_description": "Read a chart image (bar, line, scatter, pie) and emit the underlying data as a structured table — with explicit uncertainty markers on estimated values.",
    },
    {
        "slug": "image-description-alt-text",
        "title": "Image Alt-Text and Long Description",
        "tldr": "Generates accessibility-grade alt text (concise, max 125 chars) plus a long description for complex images — calibrated for screen-reader use, not Pinterest captions.",
        "category": "multimodal",
        "tags": ["accessibility", "alt-text", "a11y", "vision", "screen-reader"],
        "best_for_tags": ["accessibility", "content-publishing", "a11y-audit"],
        "difficulty_tier": "beginner",
        "featured": True,
        "use_cases": [
            {"scenario": "Blog publisher adding alt to images", "example": "Bulk-process post images; get back alt text + extended descriptions where the image is informational, not decorative."},
            {"scenario": "Accessibility audit of existing site", "example": "Check existing alt text; flag the ones that say ‘image’, ‘photo of’, or are decorative-only."},
            {"scenario": "Academic figure accessibility", "example": "Generate long descriptions for complex figures in research papers."},
            {"scenario": "Product catalog", "example": "Generate alt text that captures product attributes a buyer needs, not just visual appearance."},
        ],
        "when_not_to_use": "Skip for purely decorative images — alt should be empty (alt=\"\"). Skip when the image's role on the page is ambiguous — clarify with the publisher first.",
        "full_prompt": """You are an accessibility specialist writing alt text and long descriptions.

OUTPUT
```
purpose: informational | functional | decorative
alt_text: <= 125 characters, no "image of" / "photo of" prefix
long_description: present only if image is informational AND alt text can't carry all the meaning
context_check: a one-line check: "what does a screen-reader user need to know that a sighted user gets from this image?"
```

RULES FOR ALT TEXT
- Describe what the image MEANS in context, not what it visually shows. ("Diagram of authentication flow" beats "screenshot with arrows.")
- Skip "image of", "picture of", "screenshot of" — assistive tech announces these.
- Include words that capture function if the image is a button or link.
- Decorative images get alt="" (literally empty quotes, not "decorative image").
- If the image has text on it, transcribe the text fully unless a long description follows.

RULES FOR LONG DESCRIPTION
- Only include when:
  1. The image is informational (chart, diagram, complex photo).
  2. Alt text can't fit the meaning.
- Long description: 1–4 paragraphs. Describe spatial relationships, key data, and what a sighted user would conclude.
- Don't add interpretation a sighted user wouldn't also infer.

CONTEXT (page topic, caption, surrounding text)
{context}

Now describe the image.""",
        "input_variables": [
            {"name": "context", "type": "string", "description": "Surrounding context: page topic, caption, why the image is on the page", "required": False, "example": "Blog post about OAuth flows; this image is meant to clarify the authorization code grant"},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "purpose: informational\nalt_text: Authorization code OAuth flow with client redirect to provider then token exchange\nlong_description: ...\ncontext_check: ...",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at the meaning-vs-appearance distinction."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally adds ‘image showing...’ — call it out."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Good baseline; sometimes misses functional purpose."},
            {"model": "llama-3.2-vision", "compatibility": "fair", "notes": "Tends toward visual description; needs explicit ‘meaning not appearance’ reminder."},
        ],
        "variations": [
            {"label": "WCAG-2.2 audit", "description": "Audit existing alt.", "prompt_snippet": "Accept current alt as input; output: pass/fail, why, and a fixed version."},
            {"label": "Localized", "description": "Multiple languages.", "prompt_snippet": "Emit alt + long description in {languages}; preserve meaning, not literal word-for-word."},
            {"label": "Product catalog", "description": "Capture purchase-relevant attributes.", "prompt_snippet": "Add: ‘include attributes a buyer would search for (color, material, size shown).’"},
        ],
        "failure_modes": [
            {"symptom": "Alt text starts with ‘image of’.", "fix": "Re-pin: ‘never prefix with image/photo/screenshot of.’"},
            {"symptom": "Decorative images get long alt text.", "fix": "Add: ‘if purpose=decorative, alt_text is the literal string “” (empty).’"},
            {"symptom": "Alt text describes pixels, not meaning.", "fix": "Add: ‘if you removed this image, what would a sighted reader miss? Describe THAT.’"},
            {"symptom": "Long description duplicates alt.", "fix": "Add: ‘long description must add information beyond the alt text — if not, omit.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3.2-vision"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["screenshot-bug-report-builder", "chart-extractor-to-table"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["accessibility", "alt-text", "wcag"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should every image have alt text?", "answer": "Every image needs the alt ATTRIBUTE — but for decorative images, the value is empty (alt=\"\"). Missing-attribute is a fail; empty value is the right answer for decoration."},
            {"question": "Is AI alt text legally compliant?", "answer": "It can satisfy WCAG when the meaning is captured. Always have a human review for high-stakes images (instructional content, ecommerce, government)."},
            {"question": "What's the 125 char limit about?", "answer": "Screen readers handle longer, but most accessibility guides cap at ~125 for usability — past that, use long description."},
        ],
        "meta_title": "Image Alt-Text and Long Description — Prompt",
        "meta_description": "Generate WCAG-grade alt text and long descriptions for images — calibrated for screen readers, not Pinterest captions.",
    },
    {
        "slug": "diagram-to-architecture-doc",
        "title": "Architecture Diagram to Written Doc",
        "tldr": "Reads an architecture diagram and produces a written architecture description: components, flows, trust boundaries, failure modes implied by the topology, and open questions a reviewer should ask.",
        "category": "multimodal",
        "tags": ["architecture", "documentation", "diagram", "vision", "engineering"],
        "best_for_tags": ["design-review", "onboarding-docs", "audit"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "New hire onboarding", "example": "Existing whiteboard photo → readable architecture doc the new engineer can read solo."},
            {"scenario": "Pre-design-review prep", "example": "Author drafts diagram; AI emits a doc that surfaces flows and asks questions the review committee will ask."},
            {"scenario": "Audit / compliance", "example": "Extract trust boundaries from a diagram for security review."},
            {"scenario": "Retrofit docs for legacy system", "example": "Tribal-knowledge whiteboard photos → searchable written docs."},
        ],
        "when_not_to_use": "Skip when the diagram is purely illustrative (marketing). Skip when the diagram lacks labels — without labels, the output is creative writing, not documentation.",
        "full_prompt": """You are a staff engineer reading an architecture diagram. Write the architecture doc.

OUTPUT STRUCTURE

## Overview
3–5 sentences. What this system does (per the diagram).

## Components
For each labeled component:
- Name
- Type (service / database / queue / client / external system / etc.)
- Stated responsibility (only from labels — not invented)

## Flows
Each labeled flow (or arrow), in order if order is visible:
- From → To
- Trigger (request / event / scheduled)
- Data summary (per labels)
- Sync vs async (if labeled or inferable)

## Trust boundaries
Where does authority change hands? (Internal/external, public/private VPC, tenant boundaries.) Flag any boundary you SEE but don't see auth on.

## Failure modes implied by the topology
3–6 failure modes that follow from this shape (single-points-of-failure, retry storms, fanout amplification, etc.). Tied to specific components.

## Open questions for the author
5–10 questions a reviewer should ask — gaps in the diagram that the doc can't answer.

RULES
- Use only what's labeled. Don't invent components, technologies, or data types.
- If a component is unlabeled, call it "[unlabeled component, top-right]" and describe its role from connections.
- Distinguish what the diagram TELLS you vs what it IMPLIES.

ADDITIONAL CONTEXT (optional)
{context}

Write the doc.""",
        "input_variables": [
            {"name": "context", "type": "string", "description": "Optional surrounding context: team, system age, constraints", "required": False, "example": "Internal data platform serving ~100M events/day, mostly batch with one streaming path"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six headed sections covering Overview, Components, Flows, Trust Boundaries, Failure Modes Implied, Open Questions.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at extracting flows in order and distinguishing what's labeled from what's implied."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally invents component types — re-pin ‘only labels.’"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; weaker on identifying trust boundaries if they're implicit."},
            {"model": "llama-3.2-vision", "compatibility": "fair", "notes": "Good for high-level overview; misses small labels."},
        ],
        "variations": [
            {"label": "Risk-focused", "description": "Open questions oriented around risk.", "prompt_snippet": "Add: ‘open questions cluster into security risks, reliability risks, scaling risks, ops risks.’"},
            {"label": "Onboarding-friendly", "description": "Add glossary for new readers.", "prompt_snippet": "Add: ‘include a glossary of acronyms and product names visible in the diagram, with a one-line definition each.’"},
            {"label": "Diff against current docs", "description": "Compare two diagrams.", "prompt_snippet": "Accept two diagrams (current + proposed); emit a diff doc highlighting added/removed/changed components and flows."},
        ],
        "failure_modes": [
            {"symptom": "Invents component types (says ‘Kafka’ when the diagram just shows a queue).", "fix": "Re-pin: ‘only use technology names that are LITERALLY printed on the diagram.’"},
            {"symptom": "Conflates labeled facts with implied risks.", "fix": "Add explicit ‘TELLS / IMPLIES’ labeling in flows and failure modes."},
            {"symptom": "Doc is too short / too long.", "fix": "Set explicit target lengths per section."},
            {"symptom": "Missed trust boundaries.", "fix": "Add: ‘list every line that crosses a labeled boundary even if no auth is shown — flag missing auth explicitly.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3.2-vision"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["screenshot-bug-report-builder", "senior-code-reviewer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["architecture-diagram", "trust-boundary"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Will it work with hand-drawn whiteboard photos?", "answer": "Yes if labels are legible. Glare and bad angles hurt — re-take if the model can't read component names."},
            {"question": "Does it understand which technologies imply which failure modes?", "answer": "Generally, yes (e.g., ‘this Kafka stream has a single consumer’ → ‘lag risk’). But it's a starting point — your team's knowledge of the actual system fills the gaps."},
            {"question": "Can it generate a diagram from a doc?", "answer": "That's a separate prompt. This one goes diagram → doc. The reverse direction is doable but should ideally be done by a developer with the actual codebase."},
        ],
        "meta_title": "Architecture Diagram to Written Doc — Prompt",
        "meta_description": "Read an architecture diagram and emit a structured doc: components, flows, trust boundaries, failure modes, and the questions a reviewer should ask.",
    },
    {
        "slug": "receipt-invoice-line-item-extractor",
        "title": "Receipt and Invoice Line-Item Extractor",
        "tldr": "OCRs a receipt or invoice image and emits structured line items: vendor, date, line item descriptions, quantities, unit prices, totals, taxes, currency — with confidence flags on hard-to-read fields.",
        "category": "multimodal",
        "tags": ["ocr", "receipt", "invoice", "expense", "extraction"],
        "best_for_tags": ["expense-reporting", "bookkeeping", "ap-automation"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Expense report automation", "example": "Photo of restaurant receipt → structured fields ready for expense submission."},
            {"scenario": "Accounts payable", "example": "Vendor invoice PDF → line items for QuickBooks / Xero import."},
            {"scenario": "Small business bookkeeping", "example": "Monthly receipts → CSV for tax prep."},
            {"scenario": "Mobile reimbursement app", "example": "Snap photo of taxi receipt; app pre-fills expense form."},
        ],
        "when_not_to_use": "Skip for high-volume production AP — purpose-built OCR services (Veryfi, Mindee, AWS Textract) have higher accuracy and lower latency. Use this for ad hoc or low-volume needs.",
        "full_prompt": """You are an OCR + structured extraction agent for receipts and invoices.

OUTPUT JSON
{
  "document_type": "receipt | invoice | other",
  "vendor": {
    "name": "...",
    "address": "...",
    "phone": "...",
    "tax_id": "..."
  },
  "date": "YYYY-MM-DD",
  "invoice_or_receipt_number": "...",
  "line_items": [
    {
      "description": "...",
      "quantity": "...",
      "unit_price": "...",
      "amount": "...",
      "confidence": "high | medium | low",
      "notes": "any unclear bits"
    }
  ],
  "subtotal": "...",
  "tax": [
    {"label": "...", "rate": "...", "amount": "..."}
  ],
  "tip": "...",
  "total": "...",
  "currency": "USD | EUR | ...",
  "payment_method": "card-last4 | cash | check# | bank-transfer | other",
  "issues": ["list any field that's unclear or that you couldn't read"]
}

RULES
- Use null for fields not present.
- For any numeric field where you're under 90% confident, mark the line item confidence as medium or low.
- Currency: detect from symbols or labels; if ambiguous, say "ambiguous".
- Dates: prefer the document's date over a date implied by another field.
- Do NOT compute totals from line items if the document shows a printed total — report what's printed.
- If subtotal + tax + tip != total, surface the discrepancy in issues.

Now extract.""",
        "input_variables": [],
        "expected_output": {
            "format": "json",
            "schema": "{ document_type, vendor, date, line_items[], subtotal, tax[], total, currency, ... }",
            "sample": "{\n  \"document_type\": \"receipt\",\n  \"vendor\": { \"name\": \"Olive Grove Cafe\", ... },\n  \"line_items\": [...]\n}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong reading; faithful to printed values."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally normalizes currency formats — confirm raw values match."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Works well on printed receipts; weaker on faded thermal paper."},
            {"model": "llama-3.2-vision", "compatibility": "fair", "notes": "Adequate for clear receipts; cross-validate against printed total."},
        ],
        "variations": [
            {"label": "QuickBooks-ready CSV", "description": "Output as QB-compatible CSV.", "prompt_snippet": "Replace JSON with QB-formatted CSV: Date, Vendor, Account (suggested), Amount, Memo, Tax."},
            {"label": "Multi-receipt batch", "description": "Process several receipts.", "prompt_snippet": "Accept multiple receipts; output as array; flag any that share a vendor/date for dedup."},
            {"label": "Itemized for tax category", "description": "Categorize line items.", "prompt_snippet": "Add: ‘per line item, suggest a tax category (Meals, Travel, Office Supplies, etc.) with one-line rationale.’"},
        ],
        "failure_modes": [
            {"symptom": "Sums don't add up.", "fix": "Re-pin: ‘never compute; report printed values. If they don't match, list discrepancy in issues.’"},
            {"symptom": "Wrong currency on international receipt.", "fix": "Add: ‘look for explicit currency code or symbol; if neither, say ambiguous.’"},
            {"symptom": "Tax row mis-attributed.", "fix": "Add: ‘capture each tax line separately with its label (GST, VAT, sales tax) and rate if shown.’"},
            {"symptom": "Faded thermal paper produces empty fields.", "fix": "Pre-process image (auto-contrast) or escalate to a dedicated OCR service for production use."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3.2-vision"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["structured-extraction-from-docs", "json-output-strict"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["ocr", "structured-extraction"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How accurate is this vs a dedicated OCR service?", "answer": "For typed receipts: ~95% across vendor, date, total. For thermal paper or handwriting: variable. Dedicated services often hit 98–99% with handling of structured templates."},
            {"question": "Does it handle handwritten amounts?", "answer": "Sometimes. Flag handwritten fields explicitly and treat them as low confidence."},
            {"question": "Will it leak the data?", "answer": "Depends on which model and how you call it. Use private endpoints (Anthropic / OpenAI enterprise, Vertex private) for PII."},
        ],
        "meta_title": "Receipt and Invoice Line-Item Extractor — Prompt",
        "meta_description": "OCR receipts and invoices into structured fields with confidence flags — vendor, date, line items, taxes, totals, currency. Ad hoc-grade accuracy.",
    },
]
