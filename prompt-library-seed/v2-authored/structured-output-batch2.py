"""Structured output — batch 2."""

RECORDS = [
    {
        "slug": "json-from-unstructured-text",
        "title": "JSON From Unstructured Text",
        "tldr": "Extracts structured JSON from messy text inputs: emails, contracts, receipts, support tickets. Schema-conformant with per-field confidence and 'missing/unclear' handling.",
        "category": "structured-output",
        "tags": ["json", "extraction", "schema", "parsing"],
        "best_for_tags": ["data-engineering", "ops", "rpa"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Email-to-CRM extraction", "example": "Sales rep forwards email; extract contact, company, intent into Salesforce-ready JSON."},
            {"scenario": "Receipt parsing", "example": "Photo receipt OCR → JSON for expense system."},
            {"scenario": "Contract data extraction", "example": "PDF contract → JSON of party names, dates, amounts, key clauses."},
            {"scenario": "Support ticket triage", "example": "Free-form ticket → JSON {category, priority, suggested_team, summary}."},
        ],
        "when_not_to_use": "Skip when source has multiple records jumbled — extract one record at a time. Skip when source quality is too low (illegible OCR, garbled text) — pre-process first.",
        "full_prompt": """You are a JSON extractor. Convert unstructured text into schema-conformant JSON with confidence and missing-data handling.

INPUT
- Source text: {source_text}
- Target JSON schema (with required / optional fields, types, constraints): {schema}
- Field-level inference rules: {inference_rules}     (e.g., 'if date is relative like \"yesterday\", interpret relative to today {today_date}')
- Edge-case handling: {edge_cases}                   (e.g., 'if multiple addresses, take billing; if currency ambiguous, default USD')

OUTPUT

## 1. Pre-extraction inventory
Before producing JSON, list:
- **Fields directly extractable:** ___
- **Fields inferable** (e.g., implicit from context): ___
- **Fields uncertain:** ___
- **Fields missing entirely:** ___
- **Fields that have MULTIPLE plausible values:** ___

## 2. Extracted JSON
```json
{
  "field_1": "value",
  "field_2": 123,
  "field_3": null,            // missing
  "_meta": {
    "extracted_at": "<ISO timestamp>",
    "confidence": "high|medium|low|partial"
  }
}
```

Validate against schema. If a required field is missing or unclear:
- For required: emit null + flag in confidence + provide reason.
- For optional: omit or emit null per schema convention.

## 3. Per-field confidence
For each non-null field:
| Field | Value | Confidence | Source span | Note |

Confidence levels:
- **High** — extracted verbatim from source.
- **Medium** — inferred from clear context.
- **Low** — inferred from ambiguous context; reviewer should check.
- **Defaulted** — used edge-case rule because value absent.

## 4. Discrepancies & ambiguities
Things in source that DIDN'T fit the schema cleanly:
- Multiple plausible values: which one chosen + reasoning.
- Out-of-schema info: what was discarded (not silently — listed).
- Schema fields with no source data: listed.

## 5. Recommended next action
- **Approved** — all required fields high/medium confidence; safe to use.
- **Review** — at least one low-confidence or defaulted field; human should verify.
- **Reject** — required field missing or extraction quality too low; needs better source or schema redesign.

## 6. Suggested schema refinements
If extracting THIS shape of source repeatedly reveals schema gaps:
- "Schema doesn't have field for [thing seen in source]. Consider adding."
- "Schema's [field X] is too narrow for variation seen in source."

CRITICAL RULES
- Schema-conformant. Don't invent fields not in schema.
- Confidence per field is HONEST. Don't mark Medium when source actually says Low-confidence info.
- Missing-required → null + confidence note + reason. Don't make up.
- Discrepancies section catches what schema fails to capture — feeds back to schema design.
- JSON is VALID JSON, parseable.

SOURCE
{source_text}

SCHEMA
{schema}

Begin.""",
        "input_variables": [
            {"name": "source_text", "type": "string", "description": "Unstructured source", "required": True, "example": "Hi Mark, just chatted with Sarah from Acme Health (acmehealth.io). They're 200 employees, looking for SOC2-compliant data warehouse. Budget around $50-80k/yr. Want a demo next Tuesday."},
            {"name": "schema", "type": "string", "description": "Target JSON schema", "required": True, "example": "{ contact_name: string!, company_name: string!, company_domain: string!, employees: int, budget_min_usd: int, budget_max_usd: int, requirements: string[], demo_requested: bool, demo_date: ISO-date|null }"},
            {"name": "inference_rules", "type": "string", "description": "Field-level inference rules", "required": False, "example": "If 'next Tuesday' mentioned, resolve to actual date relative to today's date. Currency default USD if symbol absent."},
            {"name": "edge_cases", "type": "string", "description": "Edge-case handling", "required": False, "example": "Budget range with 'around' → both min and max set. SOC2 → requirements list includes 'soc2_compliance'."},
        ],
        "expected_output": {
            "format": "json",
            "sample": "Six sections: pre-extraction inventory, extracted JSON, per-field confidence table, discrepancies/ambiguities, recommended next action, suggested schema refinements.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at honest confidence + schema discipline."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; supports JSON-schema-constrained decoding for production."},
            {"model": "gemini-1.5-pro", "compatibility": "excellent", "notes": "Strong long-document extraction; good schema adherence."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Solid for simple schemas; thins on complex nested schemas."},
        ],
        "variations": [
            {"label": "Strict-JSON mode", "description": "JSON-only output, no markdown sections.", "prompt_snippet": "Skip all markdown sections. Output ONLY the JSON with a _meta block containing confidence and extraction notes. Used for production pipelines."},
            {"label": "Multi-record split", "description": "Source contains multiple records.", "prompt_snippet": "Source may contain multiple records (multiple line items, multiple parties). Output a JSON array. First detect record boundaries; then extract each."},
            {"label": "Schema-evolved", "description": "Update schema as you extract.", "prompt_snippet": "If source reveals patterns the schema doesn't capture, propose schema additions in section 6 with proposed field name, type, and example values."},
        ],
        "failure_modes": [
            {"symptom": "Invents fields not in schema.", "fix": "Hard rule: 'schema is authoritative. Out-of-schema info goes to discrepancies section, not JSON.'"},
            {"symptom": "Confidence inflation.", "fix": "Re-pin: 'High = verbatim quote. Medium = clear inference. Low = ambiguous. Defaulted = filled via edge-rule. Don\\'t soften.'"},
            {"symptom": "Makes up data for required fields.", "fix": "Force: 'required field missing → null + reason in confidence note. NEVER fabricate.'"},
            {"symptom": "Invalid JSON output.", "fix": "Add: 'validate JSON parseability before output. Escape strings properly. No trailing commas.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["table-extraction-from-pdf", "chart-extraction-with-uncertainty", "ticket-deflection-faq-suggestion"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["structured-output", "json-extraction"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What about JSON-mode / function-calling?", "answer": "If your model supports schema-constrained decoding, use it — it's more reliable. This prompt's value is the confidence/discrepancy layer ON TOP of the JSON, useful with or without constrained decoding."},
            {"question": "Why per-field confidence?", "answer": "Downstream systems need to know what's safe to act on. A high-confidence email gets auto-routed; a low-confidence one routes to human review. The metadata enables that decision."},
            {"question": "Performance on long documents?", "answer": "Use chunking + a synthesis pass for documents >32k tokens. For very-long contracts, extract per-section then merge."},
            {"question": "Can I trust the 'high confidence' label?", "answer": "Generally yes when extraction is verbatim. Spot-check 1-2% of high-confidence outputs to validate. Low-confidence labels are where review is mandatory."},
        ],
        "meta_title": "JSON From Unstructured Text — Structured Output Prompt",
        "meta_description": "Extract schema-conformant JSON from messy text. Per-field confidence, missing-data handling, discrepancies, recommended next action.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "structured-decision-tree-output",
        "title": "Structured Decision Tree Output",
        "tldr": "Generates a navigable decision tree as structured data — for diagnosis, troubleshooting, eligibility checks, recommendation flows. Includes paths, leaf actions, and edge-case handling.",
        "category": "structured-output",
        "tags": ["decision-tree", "diagnosis", "recommendation", "workflow"],
        "best_for_tags": ["product-teams", "support", "ops"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Support troubleshooting flow", "example": "Customer issue → triage tree → branches to known fixes."},
            {"scenario": "Eligibility / qualification", "example": "Loan eligibility → questions → branches to qualified/not-qualified with reasons."},
            {"scenario": "Product recommendation", "example": "Buyer questions → branches to product recommendations based on use case."},
            {"scenario": "Clinical / diagnostic guidance", "example": "Symptom-to-likely-cause tree (not diagnosis, but ranked considerations)."},
        ],
        "when_not_to_use": "Skip for genuinely probabilistic decisions (use a model, not a tree). Skip when answers depend on continuous variables more than discrete branches.",
        "full_prompt": """You are a decision-tree generator. Produce a structured tree with branches, conditions, leaf actions, and edge-case handling.

INPUT
- Decision domain: {domain}
- Goal of the tree: {goal}                      (diagnose / qualify / recommend / troubleshoot)
- Input variables (what user answers): {inputs}
- Output options at leaves: {outputs}           (the set of conclusions / actions)
- Constraints / rules: {rules}                  (must-cover edge cases, regulatory rules, etc.)
- Audience using the tree: {audience}

OUTPUT

## 1. Tree spec
- **Goal:** ___
- **Input variables:** list with types and valid values.
- **Output set:** discrete leaf options.
- **Depth target:** typically 3-5 levels.
- **Default branching:** binary unless inputs are categorical with >2 values.

## 2. The tree (structured)

```yaml
tree:
  root:
    question: "[the first question]"
    type: yes_no | choice | numeric_range
    branches:
      yes:
        question: "[next question if yes]"
        branches:
          yes:
            leaf:
              action: "[concrete action]"
              reasoning: "[why this path leads here]"
              confidence: high | medium | low
          no:
            ...
      no:
        ...
```

Each node has either `branches` (interior) or `leaf` (terminal). Every path must terminate at a leaf.

## 3. Path inventory
Enumerate every distinct path from root to leaf:
| Path | Conditions | Leaf action | Coverage notes |
|---|---|---|---|

Ensure:
- All input combinations have a leaf.
- No two paths produce contradictory leaves for compatible inputs.

## 4. Edge cases
- **Missing data:** what happens when user can't / won't answer a question.
- **Out-of-range:** what happens for inputs outside expected values.
- **Multi-true:** when multiple branches' conditions hold (priority logic).
- **None-true:** when no branch matches (default path).

## 5. Edge-leaf set
For edge cases, what leaves exist:
- "Unable to determine — route to human." (with conditions)
- "Multiple possible outcomes — present alternatives." (with which)

## 6. Validation rules
Ensure tree is sound:
- **Completeness:** every input combination has a path.
- **Determinism (when intended):** same inputs → same leaf.
- **Probabilistic mode (when intended):** explicit weights at leaves.
- **No dead branches:** every question's branches are reachable.

## 7. Visualization-friendly output
A flat text format suitable for tools like Mermaid:

```mermaid
flowchart TD
    root[First question] -->|Yes| q1[Next question]
    root -->|No| leaf1[Action A]
    q1 -->|Yes| leaf2[Action B]
    q1 -->|No| leaf3[Action C]
```

CRITICAL RULES
- Every path terminates at a leaf. No dangling branches.
- Edge cases are NAMED and routed (missing data, out-of-range, multi-true, none-true).
- Coverage section ensures all input combinations are reachable.
- Validation rules check completeness + determinism.

DOMAIN
{domain}

INPUTS
{inputs}

OUTPUTS
{outputs}

Begin.""",
        "input_variables": [
            {"name": "domain", "type": "string", "description": "Decision domain", "required": True, "example": "Customer-support troubleshooting for SaaS login issues"},
            {"name": "goal", "type": "string", "description": "Tree goal", "required": True, "example": "Triage login issue to root cause + suggest action"},
            {"name": "inputs", "type": "string", "description": "Input variables", "required": True, "example": "Did you get an error message? (yes/no/maybe). What kind of error? (password / locked / 2FA / 500-server). When did it start? (today / yesterday / weeks ago)."},
            {"name": "outputs", "type": "string", "description": "Output options at leaves", "required": True, "example": "Reset password / Unlock account / Verify 2FA / Escalate to engineering / Check status page / Contact support"},
            {"name": "rules", "type": "string", "description": "Constraints / rules", "required": True, "example": "If user says '500-server' error, ALWAYS check status page first. If account-locked, never reset password (security risk)."},
            {"name": "audience", "type": "string", "description": "Audience using tree", "required": True, "example": "Tier-1 support agent + self-service users"},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Seven sections: tree spec, YAML-formatted tree, exhaustive path inventory, edge case handling, edge-leaf set, validation rules, Mermaid visualization-friendly output.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest on path completeness + edge-case identification."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; good Mermaid output."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; can shorten tree depth — re-pin target depth."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Works for simple trees (depth ≤3); thins on complex multi-input combinations."},
        ],
        "variations": [
            {"label": "Probabilistic leaves", "description": "Leaves are weighted recommendations.", "prompt_snippet": "Leaves return RANKED list of options with probability weights. Used when path doesn't deterministically pick one outcome."},
            {"label": "Bot-conversation flow", "description": "Output as chatbot conversation flow.", "prompt_snippet": "Convert tree to chatbot dialog format: USER says X → BOT asks Y. Used to drive a conversation engine."},
            {"label": "JSON-only mode", "description": "JSON output for systems.", "prompt_snippet": "Skip Mermaid; output ONLY structured JSON tree consumable by a state machine."},
        ],
        "failure_modes": [
            {"symptom": "Dangling branches.", "fix": "Hard rule: 'every branch has either child nodes or leaf. Validator section catches dangling.'"},
            {"symptom": "Missing edge cases.", "fix": "Force section 4: 'all 4 edge categories (missing / out-of-range / multi-true / none-true) addressed.'"},
            {"symptom": "Tree too deep.", "fix": "Re-pin: 'target depth 3-5 levels. Past 5, users abandon. Consolidate or split into multiple trees.'"},
            {"symptom": "Contradictory leaves for compatible paths.", "fix": "Add: 'path inventory checks all combinations. Highlight any where same inputs lead to different leaves (logic bug).'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["json-from-unstructured-text", "ticket-deflection-faq-suggestion", "post-incident-customer-comms"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["decision-tree", "rule-engine"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "When should I use a decision tree vs an LLM directly?", "answer": "Tree when decisions follow rules and you need auditability. LLM directly when reasoning is fuzzy or training data is too varied. Trees are cheap to run, easy to audit, hard to misuse."},
            {"question": "How deep can a tree get?", "answer": "Past 5 levels, user abandonment goes up sharply. If logic needs more depth, split into multiple trees or convert to a rule engine."},
            {"question": "Can the tree update from feedback?", "answer": "Trees are static; updating means re-running this prompt with new rules. For frequently-changing logic, use a rule engine + this prompt to generate initial tree."},
            {"question": "What about probabilistic outcomes?", "answer": "Use the probabilistic-leaves variation — each leaf returns a ranked list with weights instead of single action. Useful for diagnosis-style outputs."},
        ],
        "meta_title": "Structured Decision Tree Output — Structured Output Prompt",
        "meta_description": "Generate navigable decision trees with branches, leaf actions, edge-case handling, validation, and Mermaid-ready visualization.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "rubric-scoring-with-rationale",
        "title": "Rubric Scoring With Rationale",
        "tldr": "Scores an artifact against a rubric — outputs per-criterion score, evidence quote, and weighted total. For essays, code reviews, candidate screens, vendor evals.",
        "category": "structured-output",
        "tags": ["scoring", "rubric", "evaluation", "structured"],
        "best_for_tags": ["hr-recruiting", "education", "vendor-eval"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Candidate take-home eval", "example": "Score code submission against rubric (code-quality, testing, design)."},
            {"scenario": "Student essay grading first-pass", "example": "Score essay against rubric (thesis, evidence, organization, writing)."},
            {"scenario": "Vendor RFP scoring", "example": "Score vendor responses against weighted criteria with evidence."},
            {"scenario": "Internal proposal review", "example": "Score project proposal against organization's standard rubric."},
        ],
        "when_not_to_use": "Skip when subject-matter expertise required AND model isn't trained for it. Skip for high-stakes legal/medical scoring without expert review.",
        "full_prompt": """You are a rubric scorer. Score an artifact per-criterion with evidence + weighted total.

INPUT
- The artifact (essay, code, proposal, response): {artifact}
- The rubric (list of criteria with descriptors and weights): {rubric}
- Score scale: {scale}                  (e.g., '1-4 with descriptors' or '0-100')
- Calibration anchors: {anchors}        (examples of what 2 vs 3 vs 4 looks like)
- Context (artifact purpose, evaluator audience): {context}

OUTPUT

## 1. Rubric parse
Restate criteria + weights for transparency. If anything is ambiguous in rubric, flag it before scoring.

## 2. Per-criterion scoring

For each criterion:

### Criterion: [name]
- **Weight:** ___%
- **Score:** N / max
- **Descriptor matched:** "___" (which rubric level)
- **Evidence quotes from artifact:**
  > "..." (passage 1)
  > "..." (passage 2)
- **Where it falls short of next level up:** ___
- **Confidence:** high / medium / low

Repeat for all criteria.

## 3. Weighted total
Show the math:
- Criterion 1: score × weight = ___
- ...
- Total: ___

If scale needs normalizing (e.g., out of 100), show conversion.

## 4. Banded interpretation
Map total to band per rubric:
- Excellent (≥90): ___
- Strong (80-89): ___
- Adequate (70-79): ___
- Below standard (<70): ___

Where does this artifact fall?

## 5. Reviewer-eyes-on items
Things a human reviewer should DOUBLE-CHECK:
- Low-confidence scores.
- Criteria where evidence was ambiguous.
- Criteria where artifact intentionally bent the rubric (creative response, etc.).

## 6. Improvement notes (if requested)
For each criterion that scored below max:
- "To move from [current level] to [next level], the artifact would need: ___"

CONCRETE not generic.

## 7. Calibration check
- Does this score feel consistent with the anchor examples in {anchors}?
- If artifact is at the boundary between levels, which way did you lean and why?

CRITICAL RULES
- Per-criterion score MUST have evidence quote from artifact. No score without quote.
- Confidence is HONEST. If you're uncertain, label it.
- Weighted total math is SHOWN explicitly.
- Improvement notes are CONCRETE — what to change, not 'improve overall'.
- Calibration check ties score to anchor examples.

ARTIFACT
{artifact}

RUBRIC
{rubric}

Begin.""",
        "input_variables": [
            {"name": "artifact", "type": "string", "description": "Artifact to score", "required": True, "example": "Candidate's take-home: 300-line Python solution to a fraud-detection challenge with tests and a README..."},
            {"name": "rubric", "type": "string", "description": "Scoring rubric", "required": True, "example": "Criteria: (1) Code quality 30% (1-4); (2) Algorithm choice 25%; (3) Test coverage 20%; (4) Documentation 15%; (5) Edge cases 10%."},
            {"name": "scale", "type": "string", "description": "Score scale", "required": True, "example": "1-4 with descriptors at each level"},
            {"name": "anchors", "type": "string", "description": "Calibration anchors", "required": False, "example": "Anchor example: Solution at score 3 has tests but inconsistent style. Score 4 has tests + style + edge cases."},
            {"name": "context", "type": "string", "description": "Artifact purpose", "required": True, "example": "Mid-level engineer screen at fintech; this is take-home #2; passing score for advance = weighted total ≥ 75%."},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Seven sections: rubric parse, per-criterion scoring with evidence quotes, weighted total math, banded interpretation, reviewer eyes-on items, concrete improvement notes, calibration check.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at honest confidence + calibration discipline."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; can compress score range — re-pin: 'use full range honestly.'"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; sometimes weaker on confidence flagging."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Works for clear rubrics; thins on edge cases and calibration nuance."},
        ],
        "variations": [
            {"label": "Multi-grader synthesis", "description": "Synthesize multiple graders.", "prompt_snippet": "Given N independent rubric scores for same artifact, synthesize agreement / disagreement. Surface where graders disagreed significantly."},
            {"label": "Batch artifact scoring", "description": "Score a batch + rank.", "prompt_snippet": "Score multiple artifacts against same rubric. Output a ranked list + flag any near-band-boundary calls."},
            {"label": "Self-grading", "description": "Author scores own artifact.", "prompt_snippet": "Used by an author to self-score before submitting. Honest improvement notes are the highest-value output."},
        ],
        "failure_modes": [
            {"symptom": "Scores without evidence quote.", "fix": "Hard rule: 'every score has at least one evidence quote from artifact. No quote = no score.'"},
            {"symptom": "Compresses scores toward middle.", "fix": "Re-pin: 'use full score range. If artifact truly is 1 or 4, score accordingly. Don\\'t soften.'"},
            {"symptom": "Vague improvement notes.", "fix": "Force: 'each improvement note specifies CONCRETE change needed to move up one level. Not \"improve quality\".'"},
            {"symptom": "Ignores weights.", "fix": "Add: 'weighted total math shown explicitly. Don\\'t just emit a final number.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["quiz-with-distractor-analysis", "hiring-rubric-builder", "test-suite-coverage-gap-finder"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["rubric", "scoring"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Can the model grade as reliably as a human?", "answer": "For well-specified rubrics with calibration anchors, often comparable to a single human grader. Always use as a first-pass with human review for high-stakes scoring (hiring, grades, contracts)."},
            {"question": "What if rubric criteria overlap?", "answer": "Surface in section 1 — flag the overlap. Either ask user to refine rubric or score on the most-specific criterion to avoid double-counting."},
            {"question": "How to handle creative responses that don't fit rubric?", "answer": "Use the 'creative response' note in section 5 — score per rubric but flag for human reviewer. Don't penalize for divergence; surface for judgment."},
            {"question": "Why both confidence and reviewer-eyes-on?", "answer": "Confidence is per-score; eyes-on is the digest a human reviewer reads first. Low-confidence + ambiguous-evidence + boundary-calls all surface to eyes-on."},
        ],
        "meta_title": "Rubric Scoring With Rationale — Structured Output Prompt",
        "meta_description": "Score artifacts against a rubric: per-criterion evidence quotes, weighted totals, banded interpretation, improvement notes, calibration check.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "structured-changelog-from-diff",
        "title": "Structured Changelog From Diff",
        "tldr": "Reads a code diff (PR or commits) and emits a structured changelog: categorized changes, breaking changes flagged, migration notes, user-facing vs internal — with semver suggestion.",
        "category": "structured-output",
        "tags": ["changelog", "release-notes", "semver", "structured"],
        "best_for_tags": ["devrel", "library-maintainers", "release-managers"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Open-source library release", "example": "30 PRs landed this release; auto-draft a CHANGELOG.md entry."},
            {"scenario": "SaaS internal release notes", "example": "Engineering ship-list for ops/CS team — what changed, what to know."},
            {"scenario": "API release", "example": "API version bump; structured changelog feeds docs + customer migration guide."},
            {"scenario": "Single-PR release-note", "example": "Per-PR template for release-note label; aggregated into version notes."},
        ],
        "when_not_to_use": "Skip for purely internal refactor releases (no user-facing impact). Skip when diffs are too large (>10k lines) to summarize meaningfully — chunk by feature first.",
        "full_prompt": """You are a changelog writer. Read a diff and emit structured release notes — categorized, breaking-change-flagged, semver-suggested.

INPUT
- Diff (commits, PR descriptions, code changes): {diff}
- Prior version: {prior_version}
- Audience: {audience}                    (library users / API consumers / end-users / internal team)
- Project conventions: {conventions}      (e.g., 'Keep a Changelog format', 'semver-strict')
- Public surface: {public_surface}        (what counts as a breaking change — exported types, API endpoints, UI strings)

OUTPUT

## 1. Diff overview
- **Total commits / PRs:** ___
- **Files touched:** ___
- **Areas affected:** ___ (e.g., 'auth, billing, internal-tooling')
- **Largest individual change:** ___

## 2. Categorized changes

### Breaking changes
- **What broke:** ___ (with code example: before / after)
- **Migration:** ___ (concrete steps; often a code-snippet diff)
- **Severity:** critical (silent break) / loud (compile error) / minor.

### Added features
- "[feature name]: ___" (with 1-2 line description)

### Changes (non-breaking enhancements)
- ___

### Deprecations
- "[thing]: now deprecated. Will be removed in v___. Use [replacement] instead."

### Bug fixes
- ___

### Performance
- ___ (with measurement if available)

### Security
- ___ (with CVE if applicable; treat as elevated priority)

### Internal (not user-facing)
- ___ (terse; one line each)

## 3. Suggested semver
- **Major** — breaking changes present.
- **Minor** — non-breaking additions / changes.
- **Patch** — bug fixes only.

Justify: "Recommend MINOR bump because no breaking changes; new features in auth and billing."

## 4. Migration guide (if breaking)
For each breaking change:
- **Code search pattern:** how to grep your codebase for the pattern that breaks.
- **Before:** [code example]
- **After:** [code example]
- **Automation possible:** can a codemod / regex auto-migrate? Yes/no/partial.

## 5. Release-note draft (audience-appropriate)
The actual user-facing copy:

```markdown
# v[next-version] — YYYY-MM-DD

## ⚠️ Breaking changes
- ...

## ✨ Added
- ...

## 🔧 Changed
- ...

## 🐛 Fixed
- ...

[Full notes link / contributors line / etc.]
```

Length appropriate for audience. Internal release-notes are shorter; library changelog is exhaustive.

## 6. Communication checklist
- Did breaking changes go to deprecation cycle FIRST (typically 1 minor version ahead)? If not, flag.
- Are there migration scripts that should ship with this release?
- Is there a customer / user comms requiring outreach beyond changelog?
- Does the upgrade guide need updating?

## 7. Out-of-scope from changelog
What was IN the diff but should NOT be in changelog:
- Internal refactors not changing public surface.
- Tests, CI, docs-only changes (unless audience cares).

CRITICAL RULES
- Breaking changes are FLAGGED LOUDLY and include migration.
- Semver suggestion is JUSTIFIED.
- Migration includes searchable patterns (code-grep clues).
- Release-note draft is audience-appropriate, not just engineering-dump.
- Deprecation cycle check (breaking changes should usually be pre-announced).

DIFF
{diff}

Begin.""",
        "input_variables": [
            {"name": "diff", "type": "string", "description": "Diff / commit list", "required": True, "example": "12 commits since v2.3.4:\\n- feat(auth): add OAuth2 support (#412)\\n- breaking(api): rename /users/me to /me (#415)\\n- fix(billing): off-by-one in invoice number (#420)..."},
            {"name": "prior_version", "type": "string", "description": "Prior version", "required": True, "example": "v2.3.4"},
            {"name": "audience", "type": "string", "description": "Audience", "required": True, "example": "Library users (mid-senior devs using our SDK)"},
            {"name": "conventions", "type": "string", "description": "Project conventions", "required": True, "example": "Keep a Changelog format; semver-strict; deprecation cycle = 1 minor before removal"},
            {"name": "public_surface", "type": "string", "description": "Public surface definition", "required": True, "example": "All exported types/functions in @acme/sdk + REST API endpoints under /v2/."},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Seven sections: diff overview, categorized changes by type, semver suggestion, migration guide, audience-tuned release-note draft, communication checklist, out-of-scope items.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at breaking-change detection + honest migration guidance."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; can soft-pedal breaking changes — re-pin loud-flagging rule."},
            {"model": "gemini-1.5-pro", "compatibility": "excellent", "notes": "Long-context advantage for large diffs."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Works for small diffs; thins on multi-PR synthesis."},
        ],
        "variations": [
            {"label": "Customer-facing only", "description": "Strip engineering-internal items.", "prompt_snippet": "Suppress internal-only changes. Output only what end-users / customers care about. Used for customer release email."},
            {"label": "Migration-script generator", "description": "Output codemod scaffolding.", "prompt_snippet": "For each breaking change, draft a codemod / regex / jscodeshift script that auto-migrates the pattern. Skip if can't be automated."},
            {"label": "Multi-version range", "description": "Cumulative changelog.", "prompt_snippet": "Generate cumulative changelog for v2.3.4 → v2.5.0 (multiple intermediate versions). Used for users upgrading multiple versions at once."},
        ],
        "failure_modes": [
            {"symptom": "Misses breaking changes.", "fix": "Force: 'any change to public_surface = potential breaking. Re-check section 2.A against public_surface definition.'"},
            {"symptom": "Vague migration notes.", "fix": "Re-pin: 'migration must include before/after code or grep pattern. Generic guidance unacceptable.'"},
            {"symptom": "Wrong semver suggestion.", "fix": "Hard rule: 'breaking present → MAJOR. New features only → MINOR. Bug fix only → PATCH. Justification matches.'"},
            {"symptom": "Release notes too engineering-dense for audience.", "fix": "Add: 'audience-appropriate tone. Library users want code examples; end users want plain-English impact.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["code-modernization-stepwise", "openapi-spec-from-handler", "internal-memo-from-decision"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["semver", "changelog"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should I auto-publish what this generates?", "answer": "No — always review. The prompt does the structure + first-pass categorization; humans do the final wording for tone and accuracy."},
            {"question": "How does it detect breaking changes?", "answer": "It uses public_surface to scope. Changes inside that surface are breaking; outside is internal. Provide an accurate public_surface for accurate flagging."},
            {"question": "Can it work from just commit messages?", "answer": "Partially. Conventional Commits (feat:, fix:, breaking:) work well. Free-form commit messages give weaker output — feed PR descriptions too if available."},
            {"question": "What about pre-release / canary versions?", "answer": "Use the multi-version-range variation. Suggested semver becomes -alpha.N / -beta.N / -rc.N per your project conventions."},
        ],
        "meta_title": "Structured Changelog From Diff — Release Prompt",
        "meta_description": "Generate structured release notes from a diff: categorized changes, breaking-change flags, migration guide, audience-tuned draft, semver suggestion.",
        "version": "v2.0",
        "release_status": "stable",
    },
]
