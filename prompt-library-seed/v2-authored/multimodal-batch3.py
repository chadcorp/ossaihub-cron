"""Multimodal — batch 3."""

RECORDS = [
    {
        "slug": "chart-extraction-with-uncertainty",
        "title": "Chart Extraction With Uncertainty",
        "tldr": "Extracts data from chart images into a structured table with per-cell confidence and 'unreadable' flags — for slides, papers, and screenshots where raw data isn't available.",
        "category": "multimodal",
        "tags": ["vision", "chart-extraction", "data-recovery", "ocr"],
        "best_for_tags": ["analysts", "researchers", "competitive-intel"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Competitive intelligence", "example": "Competitor's earnings call deck — extract chart values into a spreadsheet."},
            {"scenario": "Academic figure re-analysis", "example": "Paper provides chart but not data; extract values for replication."},
            {"scenario": "Quarterly board prep", "example": "Pull values from last year's deck charts to compare YoY."},
            {"scenario": "Industry-report mining", "example": "Analyst report charts — extract underlying data for model inputs."},
        ],
        "when_not_to_use": "Skip for charts where the data is published separately (cite the source instead). Skip for line charts with >20 data points where pixel-level error accumulates rapidly.",
        "full_prompt": """You are a chart-extraction analyst. Read the image, extract data into a table, attach per-cell confidence, flag what's unreadable.

INPUT
- Chart image: [attached]
- Chart context (caption, source, units): {chart_context}
- Use case (downstream calculation / comparison): {use_case}
- Reliability requirement: {reliability}     (rough / production)

OUTPUT

## 1. Chart anatomy
Before extracting, describe what you see:
- **Chart type:** bar / line / pie / scatter / area / stacked / other
- **Axes:** x = ___, y = ___ (with units)
- **Y-axis scale:** linear / log / truncated (NOT starting at 0) — call this out
- **Series count:** ___
- **Time period / categories:** ___
- **Source / footnote / asterisks:** ___

If chart is unreadable (low res / occluded / 3D distortion), STOP. Tell user why.

## 2. Extracted table
Per data point:
| Series | X-value | Y-value | Confidence | Notes |

Confidence levels:
- **High** — exact value labeled on chart OR major grid intersection.
- **Medium** — readable from axis, no exact label, estimated to within ~3% of axis range.
- **Low** — readable but mid-range between gridlines; ±10% or worse.
- **Unreadable** — too small / occluded / mid-series squeeze.

If chart has data LABELS on bars, treat those as ground truth.

## 3. Caveats this chart embeds
- Truncated y-axis? (starts above 0, visually exaggerates differences)
- Log scale? (visual gap ≠ proportional difference)
- Cumulative vs incremental? (often unclear)
- Sample size / weighting? (footnote-only often)
- Time-period selection bias?
- Stacked confusing absolute vs share?

Flag every visual rhetoric move the chart makes.

## 4. Source-data alternatives
If a higher-fidelity source exists, name where to look:
- "Underlying data likely in [SEC 10-K / investor-day appendix / paper supplement]."
- "If commercial report: [vendor name] sells the data."

## 5. Recommended use
Given extracted confidence + caveats:
- **Safe to use for:** order-of-magnitude estimates, trend direction.
- **Use with caution:** specific values within ±5%.
- **Do NOT use for:** [specific use cases the data won't support].

CRITICAL RULES
- Confidence is HONEST. Don't manufacture decimals you can't read.
- Truncated axes and log scales MUST be called out — they distort interpretation.
- 'Unreadable' is a valid extraction. Don't guess.
- Reliability-production extraction requires high or medium confidence on every cell; flag any low/unreadable.
- Source-data section is REQUIRED when applicable — saves users from extracting what was already published.

CHART CONTEXT
{chart_context}

USE CASE
{use_case}

Begin.""",
        "input_variables": [
            {"name": "chart_context", "type": "string", "description": "Chart caption, source, units", "required": True, "example": "Caption: 'Q3 Revenue by Segment (USD millions)'. Source: Acme Q3 2025 earnings deck slide 14. Units: USD M."},
            {"name": "use_case", "type": "string", "description": "Downstream use", "required": True, "example": "YoY comparison vs same segments in Q3 2024 for competitive briefing."},
            {"name": "reliability", "type": "string", "description": "Reliability requirement", "required": True, "example": "Production — values will be cited in customer-facing report"},
        ],
        "expected_output": {
            "format": "table",
            "sample": "Five sections: chart anatomy, extracted data table with per-cell confidence, embedded caveats (truncation/log/etc.), source-data alternatives, recommended use limits.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at honest confidence ratings + caveat flagging."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good at OCR + axis reading; can over-confident on mid-gridline values."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid for standard charts; weaker on dense scatterplots."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Limited vision compared to peers; not for production extraction."},
        ],
        "variations": [
            {"label": "Multi-chart batch", "description": "Process several charts at once.", "prompt_snippet": "Apply to a slide deck or report PDF. Output one table per chart + a summary of total cells extracted with confidence distribution."},
            {"label": "Strict-confidence mode", "description": "Only emit high-confidence cells.", "prompt_snippet": "Suppress any cell rated Medium / Low / Unreadable. Output blanks with rationale. Used for citation-quality extraction."},
            {"label": "Inverse — chart from data", "description": "Given a chart description and extracted values, propose a chart redesign that's harder to manipulate.", "prompt_snippet": "Output: (1) the original chart's rhetorical moves, (2) a redesign that preserves the truth without the manipulation."},
        ],
        "failure_modes": [
            {"symptom": "Manufactures decimal precision.", "fix": "Re-pin: 'confidence determines precision. Low-confidence cells: round to nearest 10% of axis range. High-confidence: match labeled precision.'"},
            {"symptom": "Misses truncated y-axis.", "fix": "Force: 'inspect y-axis bottom value. If not 0, mark TRUNCATED in caveats. Always.'"},
            {"symptom": "Stacked-bar confusion.", "fix": "Add: 'for stacked bars, distinguish total vs segment. Extract both. Note if labels show only total or only segments.'"},
            {"symptom": "Hallucinates data points beyond visible.", "fix": "Hard rule: 'only extract what's in the image. Off-screen / cropped = unreadable, not extrapolated.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["screenshot-to-spec", "table-extraction-from-pdf", "ui-component-from-screenshot"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["chart-junk", "ocr"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Can it handle 3D / pie charts?", "answer": "Pies yes (with low confidence on similar slices). 3D bars/lines have distorted perspective — confidence drops to Low or worse. Recommend asking for 2D source."},
            {"question": "What about charts in non-English?", "answer": "Numeric values extract fine. Series labels: pass language hint in chart_context. The output uses original language unless you ask for translation."},
            {"question": "Why call out log-scale axes?", "answer": "Equal visual gaps on log charts represent multiplicative, not additive, differences. People routinely misread log charts. Flagging prevents downstream errors."},
            {"question": "Can it OCR handwritten chart labels?", "answer": "Generally no for production use. The OCR confidence is too low. Treat handwritten-label values as Low confidence by default."},
        ],
        "meta_title": "Chart Extraction With Uncertainty — Multimodal Prompt",
        "meta_description": "Extract chart data into a table with per-cell confidence, axis-truncation flags, log-scale callouts, and source-data alternatives.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "video-frame-summarizer",
        "title": "Video Frame Summarizer",
        "tldr": "Reads sampled video frames + transcript and produces a navigable timeline of beats — what's on screen, what's said, and what changes. For tutorials, lectures, and product walkthroughs.",
        "category": "multimodal",
        "tags": ["video", "timeline", "summary", "vision", "transcript"],
        "best_for_tags": ["learners", "educators", "product-teams"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Tutorial video summary", "example": "30-min coding tutorial — output navigable timeline of steps."},
            {"scenario": "Lecture review", "example": "Recorded lecture — outline beats with timestamps for review."},
            {"scenario": "Product walkthrough", "example": "Customer-success records walkthrough; summary becomes the asyncIN-DOCS for new hires."},
            {"scenario": "Meeting recording", "example": "Hour-long all-hands — surface decision points and topic shifts."},
        ],
        "when_not_to_use": "Skip if video is purely visual (mime, music videos) — needs spoken transcript to anchor beats. Skip when full video length > model context (chunk first).",
        "full_prompt": """You are a video-timeline analyst. Build a navigable timeline of beats from sampled frames + transcript.

INPUT
- Sampled frames with timestamps: [attached]
- Transcript with timestamps: {transcript}
- Video purpose: {purpose}
- Audience: {audience}
- Desired output depth: {depth}        (skim / scan / study)

OUTPUT

## 1. Video metadata
- **Duration:** ___
- **Format:** tutorial / lecture / walkthrough / talk / meeting / other
- **Primary speaker(s):** ___
- **On-screen elements:** code editor / slides / shared screen / face-cam / split

## 2. Timeline
| Timestamp | Beat | What's said | What's on screen | Why this matters |

Beats are MEANINGFUL transitions, not every 30 seconds:
- New topic / step
- Major insight or definition
- Screen change (new file, new slide)
- Q&A pivot
- Sub-tutorial within tutorial
- Recap moments

Aim for 1 beat per ~2-5 minutes of video. Long beats get sub-bullets.

## 3. Decision / definition / action list
Extract the high-value items, with timestamps:

**Decisions made:**
- "8:23 — Decided to use Postgres over MongoDB because of relational data."

**Key definitions / concepts:**
- "14:10 — Defines 'eventual consistency' as ___"

**Action items / commitments:**
- "29:45 — Speaker commits to publishing the code repo Friday."

**Resources mentioned:**
- "21:30 — Recommends 'Designing Data-Intensive Applications' book."

## 4. Skip-to-this navigation
For different viewing intents:
- **If you're new to topic:** start at ___ (skip intro + housekeeping).
- **If you only care about decisions:** ___ (timestamps).
- **If you want the deep technical detail:** ___ (specific chapter).
- **If short on time, watch:** [3-5 critical minutes selected for highest density].

## 5. What's NOT in the video
Things the audience MIGHT EXPECT but the video doesn't cover:
- "No deployment instructions — only local dev setup."
- "Doesn't cover the security implications."

Sets expectations honestly.

## 6. Discrepancies
Where transcript and frames disagree:
- "8:50 — speaker says 'click the BLUE button' but on-screen the button is green. Frame at 8:51 shows button is green; speaker likely color-naming error."

These signal edits / accuracy issues / accessibility concerns.

CRITICAL RULES
- Beats are MEANINGFUL transitions, not arbitrary time intervals.
- Decisions / definitions / actions = HIGH-VALUE extracts with exact timestamps.
- Skip-to-this section serves different audiences explicitly.
- Discrepancies between transcript and frames must be flagged.
- NOT-in-video section sets honest expectations.

TRANSCRIPT
{transcript}

PURPOSE
{purpose}

Begin.""",
        "input_variables": [
            {"name": "transcript", "type": "string", "description": "Timestamped transcript", "required": True, "example": "[0:00] Welcome. [0:32] Today we'll cover three things..."},
            {"name": "purpose", "type": "string", "description": "Video purpose", "required": True, "example": "Onboarding tutorial — new engineers learn our deployment pipeline"},
            {"name": "audience", "type": "string", "description": "Audience", "required": True, "example": "Mid-level engineers, first week at the company"},
            {"name": "depth", "type": "string", "description": "Output depth", "required": True, "example": "Study — used as primary onboarding document"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: metadata, beat-aligned timeline table, decisions/definitions/actions list, skip-to-this navigation for different intents, NOT-in-video, transcript/frame discrepancies.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest on beat selection + 'why this matters' annotation."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good with mixed visual + audio data."},
            {"model": "gemini-1.5-pro", "compatibility": "excellent", "notes": "Long-context advantage; handles 1+ hour videos cleanly."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for short videos; thins on long-context discrepancy detection."},
        ],
        "variations": [
            {"label": "Code-tutorial-focused", "description": "Optimize for code tutorials.", "prompt_snippet": "Add a 'code-change diff' column: at each beat, what changed in the editor (file, lines, behavior)."},
            {"label": "Search-index output", "description": "Output as searchable index.", "prompt_snippet": "Output a JSON index: [{timestamp, topic, keywords, summary}]. Use to build a search interface over the video."},
            {"label": "Multi-video synthesis", "description": "Compare 2+ videos on same topic.", "prompt_snippet": "Run on multiple videos covering same topic. Output a cross-video map: where do they agree, disagree, and what does each cover uniquely."},
        ],
        "failure_modes": [
            {"symptom": "Too-frequent or too-sparse beats.", "fix": "Force: 'aim for 1 beat per ~2-5 min for tutorial; 1 per 30s-2min for interview. Re-pin density.'"},
            {"symptom": "Misses decisions / actions buried in casual speech.", "fix": "Add: 'scan for verbs of commitment: \"we\\'ll\", \"I\\'ll\", \"we should\", \"let\\'s\" — these often surface action items.'"},
            {"symptom": "Skip-to-this section is generic.", "fix": "Re-pin: 'each audience-intent links to a SPECIFIC timestamp, not a topic.'"},
            {"symptom": "Misses transcript-frame discrepancies.", "fix": "Force section 6: 'cross-check at least 5 spots where speaker references on-screen elements.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["podcast-show-notes-structured", "research-summary-for-non-experts", "blog-comment-thread-summarizer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["video-summarization", "transcript-mining"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How are frames sampled?", "answer": "Most pipelines sample 1 fps or scene-change-triggered. Pass key timestamps as input. The model uses the sampled frames as anchor points + transcript fills in between."},
            {"question": "What about videos in non-English?", "answer": "Pass the transcript in source language; the prompt outputs in source language by default. For translation, use the translation-of-video prompt first."},
            {"question": "Long videos (2+ hours)?", "answer": "Chunk into 30-min segments, run per-chunk, then synthesize timelines into a master. Gemini long-context can do 1-hour in one pass."},
            {"question": "Can it handle multi-speaker discussions?", "answer": "Yes if transcript has speaker labels. Without speaker labels, attribution accuracy drops. Pre-process with a diarization step if needed."},
        ],
        "meta_title": "Video Frame Summarizer — Multimodal Prompt",
        "meta_description": "Build a navigable timeline from video frames + transcript: beat-aligned summary, decisions/actions list, skip-to-this navigation, discrepancy flags.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "image-accessibility-alt-text",
        "title": "Image Alt-Text For Accessibility",
        "tldr": "Generates alt-text that screen readers can actually use: prioritized information, function-aware (decorative vs informational), respects context, follows WCAG 1.1.1.",
        "category": "multimodal",
        "tags": ["accessibility", "alt-text", "wcag", "vision"],
        "best_for_tags": ["content-teams", "web-dev", "publishers"],
        "difficulty_tier": "beginner",
        "featured": True,
        "use_cases": [
            {"scenario": "CMS bulk alt-text backfill", "example": "10,000 product images missing alt-text — generate accessible descriptions."},
            {"scenario": "Blog post image alt-text", "example": "Hero image, embedded charts, decorative graphics — each gets appropriate alt or empty alt."},
            {"scenario": "Slide-deck export to PDF", "example": "Every slide image gets alt-text before PDF export."},
            {"scenario": "Social media post accessibility", "example": "Twitter/LinkedIn images get alt-text in publishing workflow."},
        ],
        "when_not_to_use": "Skip when the image is purely decorative — output empty alt (alt=\"\") to let screen readers skip it. Skip for complex data charts where a full data-table substitute is needed instead.",
        "full_prompt": """You are an accessibility alt-text writer. Output WCAG-compliant alt-text honoring purpose, function, and context.

INPUT
- Image: [attached]
- Surrounding context (caption, paragraph, page purpose): {context}
- Function of image: {function}        (decorative / informational / functional / complex)
- Brand/style preferences: {style}     (formal / casual / specific terminology)
- Length budget: {length_budget}       (typical: ≤125 chars; tweet alt: ≤1000; complex: long-desc)

OUTPUT

## 1. Function classification
First, classify the image:
- **Decorative** — adds visual interest only; no info loss without it. → alt=""
- **Informational** — conveys info text doesn't otherwise convey. → Short alt.
- **Functional** — image IS a link / button / control. → Alt describes ACTION not appearance.
- **Complex** — chart, diagram, infographic. → Short alt + long-description elsewhere.

If decorative: output alt="" and STOP. Don't write description for screen readers to skip.

## 2. The alt-text
- 1-2 sentences, ≤125 chars (or whatever length_budget specifies)
- LEAD with most important information
- Skip "image of" / "picture of" — screen readers already announce that
- For functional: describe the action, not appearance ("Submit form" not "Blue button")
- For people: use respectful language; don't infer ethnicity / gender / age unless contextually critical
- For text in image: include the text verbatim if it's the primary content
- Don't repeat the caption — alt complements, doesn't duplicate

## 3. (Complex only) Long-description
For charts, diagrams, infographics:
- Short alt (above) summarizes the image
- Long-description = the full content needed for equivalent access
- Format as: table of data points, sequential steps of a diagram, or structured narrative
- Linked from `aria-describedby` or `<details>` element

## 4. Context-fit check
- Does the alt repeat what surrounding paragraph already says? → Trim alt.
- Does the page caption convey the info? → Alt can be shorter.
- Is the image the ONLY source of this info on the page? → Alt MUST be comprehensive.

## 5. Failure mode prevention
Flag if any apply:
- "Decorative being treated as informational — would clutter screen-reader output."
- "Informational treated as decorative — info loss for non-sighted users."
- "Functional treated as informational — user can't tell what clicking does."
- "Sensitive content in image (faces, medical, demographics) — verify before publishing."

## 6. Final output
```html
<img src="..." alt="[the alt text]">
```
For complex images, include long-description structure:
```html
<img src="..." alt="[short summary]" aria-describedby="img-desc-1">
<div id="img-desc-1" hidden>[long description]</div>
```

CRITICAL RULES
- Decorative = empty alt. Period. No "elegant background pattern" — screen readers should SKIP.
- Lead with most important info. Don't bury the lede.
- No "image of" / "picture of" prefixes.
- Functional alt describes ACTION (verb), not appearance (adjective).
- Long-description for complex images is REQUIRED for equivalent access.
- Sensitive content prompts manual review.

CONTEXT
{context}

FUNCTION
{function}

Begin.""",
        "input_variables": [
            {"name": "context", "type": "string", "description": "Surrounding text / page purpose", "required": True, "example": "Blog post about climate change; image is between paragraphs discussing Arctic ice loss."},
            {"name": "function", "type": "string", "description": "Function of image", "required": True, "example": "Informational — image shows ice extent comparison 1984 vs 2024"},
            {"name": "style", "type": "string", "description": "Style preferences", "required": True, "example": "Formal, scientifically precise; uses 'Arctic sea ice' not 'ice up north'"},
            {"name": "length_budget", "type": "string", "description": "Length budget in chars", "required": True, "example": "≤125 chars for short alt; up to 500 chars for long-description"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: function classification (decorative/info/functional/complex), the alt-text, long-description if complex, context-fit check, failure-mode flags, final HTML.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at function classification + sensitivity to context."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can over-describe decorative — re-pin classification gate."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; can mis-classify functional vs informational."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Workable for simple images; weaker on complex chart long-descriptions."},
        ],
        "variations": [
            {"label": "Brand-voice alt-text", "description": "Match a publication's voice.", "prompt_snippet": "Adapt the alt-text to match a specific style guide ({style_guide_url}). Maintain WCAG compliance while applying the voice."},
            {"label": "Multi-language alt-text", "description": "Generate alt in multiple languages.", "prompt_snippet": "Output alt-text in {languages}. Each version follows WCAG + locale conventions; not a literal translation."},
            {"label": "Existing alt audit", "description": "Audit existing alt-text.", "prompt_snippet": "Given EXISTING alt-text + image, output: (1) is the alt accurate? (2) WCAG violations? (3) replacement alt if needed."},
        ],
        "failure_modes": [
            {"symptom": "Treats decorative as informational.", "fix": "Re-pin: 'function classification is the FIRST gate. Decorative = empty alt. No descriptions for pure decoration.'"},
            {"symptom": "Buries the lede.", "fix": "Force: 'first 50 chars must contain the most important info. Don't lead with style description.'"},
            {"symptom": "Includes \"image of\" prefix.", "fix": "Hard rule: 'NEVER prefix with image-of / picture-of / illustration-of. Screen readers already announce image.'"},
            {"symptom": "Functional alt describes appearance.", "fix": "Force: 'functional alt = action verb. Not \"red button\"; instead \"Send message.\"'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["chart-extraction-with-uncertainty", "ui-component-from-screenshot", "screenshot-to-spec"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["wcag", "alt-text"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What's the max alt-text length?", "answer": "WCAG doesn't set a hard cap, but most guidelines suggest ≤125 chars for short alt. Twitter allows 1000. For complex images, use long-description elsewhere."},
            {"question": "How do I know if an image is decorative?", "answer": "Test: cover the image — does the surrounding text still make sense? If yes, decorative (empty alt). If readers lose info, informational (write alt)."},
            {"question": "Do I need alt-text for emoji?", "answer": "Most platforms handle emoji alt-text automatically (Unicode names). For custom emoji or stickers, write alt as you would for any informational image."},
            {"question": "How to handle text-in-image?", "answer": "Include the text verbatim in alt if it's the primary content. Better: avoid text-in-image entirely (it doesn't reflow, doesn't scale, breaks translation)."},
        ],
        "meta_title": "Image Alt-Text For Accessibility — Multimodal Prompt",
        "meta_description": "Generate WCAG-compliant alt-text: function-aware classification, context-fit checks, and long-descriptions for complex images.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "before-after-image-comparison",
        "title": "Before/After Image Comparison",
        "tldr": "Compares two images (before/after, version A/B, original/edit) and surfaces meaningful differences with severity rating — for design review, QA, photo comparison.",
        "category": "multimodal",
        "tags": ["vision", "comparison", "qa", "design-review"],
        "best_for_tags": ["designers", "qa", "researchers"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Design review", "example": "v1 vs v2 of a UI mockup — what changed and is it intentional?"},
            {"scenario": "Visual QA on a release", "example": "Screenshots before vs after deploy — regression detection."},
            {"scenario": "Photo edit verification", "example": "Original vs retouched — what was altered and where it shows."},
            {"scenario": "Research figure comparison", "example": "Same site / sample at two time points — what's the meaningful change."},
        ],
        "when_not_to_use": "Skip when images are radically different (different scenes / domains) — comparison won't be meaningful. Skip when pixel-perfect comparison is needed; use a diff tool.",
        "full_prompt": """You are a visual-comparison analyst. Compare two images, surface meaningful differences, rate severity.

INPUT
- Image A (before / version 1 / original): [attached]
- Image B (after / version 2 / new): [attached]
- Comparison purpose: {purpose}            (design review / QA / verification / research)
- Context: {context}                       (what changed, why, who needs to know)
- Scope: {scope}                           (all changes / specific area / specific dimension)

OUTPUT

## 1. Image pair sanity
- Are the images comparable? (same subject / framing / resolution / aspect)
- If not, what's mismatched and how does it affect comparison validity?

If pair is fundamentally non-comparable: STOP, recommend re-shoot / re-render.

## 2. Difference inventory
Walk through systematically:

### Layout / structure
- Element positions
- Element sizes
- Element addition / removal

### Color / contrast / saturation
- Hue shifts
- Contrast changes
- Saturation / desaturation

### Text content
- Text changes (verbatim diff)
- Typography shifts (font, weight, size)

### Imagery / illustration
- Image content swaps
- Crop / framing changes

### Specific to purpose
- For UI: spacing, alignment, micro-interaction cues.
- For photo: exposure, sharpness, noise.
- For research: subject changes, measurement-relevant shifts.

## 3. Severity rating per difference
For each surfaced diff:
- **Critical** — breaks function or violates a hard spec (color contrast below 4.5:1, removed required CTA).
- **Significant** — meaningful change a reviewer needs to approve.
- **Minor** — small refinement.
- **Trivial** — rendering / format artifact (anti-aliasing, JPEG noise).

| Diff | Location | Type | Severity | Notes |

## 4. Intent inference
For each significant/critical change:
- Likely intentional? (matches purpose / context) — YES with reason.
- Possibly unintentional? — flag for confirmation.
- Definitely unintentional? — escalate as bug / regression.

## 5. What's NOT different
Useful negative space — what STAYED the same:
- Brand elements (logo, primary CTAs).
- Hierarchy / flow.
- Critical functional elements.

If something CRITICAL should have changed but didn't, flag that too.

## 6. Recommended next action
Based on purpose:
- **Approve as-is** — all changes intentional, no regressions.
- **Approve with notes** — minor adjustments to flag back.
- **Request revisions** — list of specific things to fix.
- **Reject / re-do** — major intent mismatch.
- **Escalate** — possibly unintentional change with high impact.

CRITICAL RULES
- Difference inventory is COMPREHENSIVE within scope. Don't skip uncomfortable diffs.
- Severity rating is HONEST — over-rating wastes reviewer time, under-rating ships bugs.
- 'Possibly unintentional' is REQUIRED when ambiguous — don't guess.
- What's-NOT-different section catches missing changes (a real failure mode).

CONTEXT
{context}

PURPOSE
{purpose}

Begin.""",
        "input_variables": [
            {"name": "purpose", "type": "string", "description": "Comparison purpose", "required": True, "example": "Design review — v3 mockup of checkout page vs v2; partner sign-off."},
            {"name": "context", "type": "string", "description": "What changed + why", "required": True, "example": "Designer iterated on v2 feedback: simplify CTA, increase trust signals, fix mobile breakpoint."},
            {"name": "scope", "type": "string", "description": "What to compare", "required": True, "example": "All changes above the fold; ignore footer."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: pair sanity, structured difference inventory by category, severity-rated diff table, intent inference, what's-NOT-different, recommended next action.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at intent inference + honest severity calibration."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong at layout / text diff detection."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; weaker on color/contrast nuance."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple diffs; thins on color/contrast and intent inference."},
        ],
        "variations": [
            {"label": "Pixel-diff inspection", "description": "Tight QA mode.", "prompt_snippet": "Treat every pixel-level diff as significant unless explicitly listed in scope. Used for visual-regression CI gates."},
            {"label": "User-perceptible only", "description": "Focus on what users see.", "prompt_snippet": "Suppress diffs <1% of viewport area or that fall below contrast-perceptibility thresholds. Output 'user-perceptible diffs only.'"},
            {"label": "A/B/C/N-way", "description": "Compare 3+ images.", "prompt_snippet": "Apply to N images. Output a matrix of pairwise diffs + an N-image summary highlighting which variant is the most differentiated."},
        ],
        "failure_modes": [
            {"symptom": "Misses subtle but critical changes.", "fix": "Force category-by-category sweep. Don't allow free-form diff listing — categories enforce coverage."},
            {"symptom": "Over-rates severity.", "fix": "Re-pin: 'severity scale matches WCAG / brand-guide / spec impact. Aesthetic preference = trivial unless it violates a documented rule.'"},
            {"symptom": "Misses unchanged-things-that-should-change.", "fix": "Require section 5: 'name 1-2 things that should have changed given the stated intent. If none, explicitly state.'"},
            {"symptom": "Vague 'looks different' commentary.", "fix": "Force: 'each diff names location (top-left, hero, etc.), type, and severity. No vague \"general feel\" diffs.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["chart-extraction-with-uncertainty", "ui-component-from-screenshot", "screenshot-to-spec"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["visual-regression", "design-qa"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How small a diff is too small?", "answer": "Default: ignore sub-pixel rendering artifacts. For visual regression CI, the pixel-diff variation treats every diff as significant. For design review, the user-perceptible variation suppresses noise."},
            {"question": "Can it tell intentional vs accidental?", "answer": "Only inference, not certainty. The intent inference uses purpose / context to make a calibrated guess + flags 'possibly unintentional' for ambiguous cases."},
            {"question": "What about animations / video?", "answer": "Out of scope — this prompt is for static frames. For animation comparison, sample frames and compare pairwise, then synthesize."},
            {"question": "Color-difference accuracy?", "answer": "Model vision is OK for hue shifts but not for ΔE-quality color matching. For brand-color compliance, use a sampling tool + pass values to a non-vision check."},
        ],
        "meta_title": "Before/After Image Comparison — Multimodal Prompt",
        "meta_description": "Compare two images and surface meaningful differences with severity rating, intent inference, and recommended next-action.",
        "version": "v2.0",
        "release_status": "stable",
    },
]
