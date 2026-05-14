"""Structured output prompts."""

RECORDS = [
    {
        "slug": "json-schema-from-examples",
        "title": "JSON Schema From Example Outputs",
        "tldr": "Reverse-engineers a JSON Schema from 3-5 example outputs you've already seen — including edge cases (null, missing fields, varying types). Useful for retrofitting validation onto unstructured LLM output.",
        "category": "structured-output",
        "tags": ["json-schema", "validation", "structured-output", "reverse-engineering"],
        "best_for_tags": ["api-design", "validation", "post-hoc-typing"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Adding validation to existing LLM endpoint", "example": "5 examples of past outputs → JSON Schema + Pydantic class."},
            {"scenario": "Reverse-engineering external API response", "example": "Vendor returns JSON with no schema; sample → schema → typed client."},
            {"scenario": "Documenting agent output", "example": "Agent produces ad-hoc JSON; formalize the shape."},
            {"scenario": "Migration prep", "example": "Old API output samples → schema → strict validation in new version."},
        ],
        "when_not_to_use": "Skip when an authoritative schema already exists. Skip when examples are too few or too uniform — you'll miss the edge cases the schema needs.",
        "full_prompt": """You are inferring a JSON Schema from example outputs.

INPUT
- 3-10 example JSON outputs (real, from production if possible): {examples}
- The PURPOSE of this data (so you can name fields well): {purpose}
- Strictness level: {strictness}    (loose: many fields optional / strict: all fields required by default)

OUTPUT

## 1. Observed shape
For each field that appears across examples:
- Field name + path
- Observed types: list (e.g., string, integer, null)
- Required across all examples? Or sometimes missing?
- Sample values (3-5 actual values seen)

## 2. JSON Schema (Draft 7)
Full schema with:
- type, properties, required
- Constraints inferred from examples (min/max for numbers, enums for strings if values look bounded, format for date/email patterns)
- additionalProperties: false if strict / true if loose

## 3. Pydantic class
Same shape, but as Python Pydantic. Use:
- Optional[X] | None for optional fields
- Literal[...] for tight enums
- EmailStr, datetime, etc. for known formats

## 4. Edge cases the schema captures
Bullet list of cases this schema handles correctly (null in field X, etc.)

## 5. Edge cases the schema MIGHT NOT capture
Honest list of what's unclear:
- Field X is always integer in examples — but could it ever be float?
- Field Y is always present — but could it be missing in cases not in samples?
- Constraints I inferred (min/max) — are they real or sample artifacts?

## 6. Recommendations
- Things you'd ask the data producer to confirm before trusting strict validation
- Where to relax strictness given uncertainty

RULES
- Don't invent fields not in examples.
- When type varies (string sometimes, null sometimes), output as `type: ['string', 'null']`.
- Enum candidates: if a string field has ≤5 distinct values across examples, propose it as an enum AND flag for confirmation.
- For dates / emails / URLs: detect by pattern and add format keyword.

EXAMPLES
{examples}

PURPOSE
{purpose}

Begin.""",
        "input_variables": [
            {"name": "examples", "type": "string", "description": "3-10 example JSON outputs", "required": True, "example": "[{\"id\":1,\"name\":\"alice\",\"plan\":\"pro\",\"created_at\":\"2024-01-15T10:00:00Z\"},{\"id\":2,\"name\":null,\"plan\":\"free\",\"created_at\":\"2024-02-01T08:00:00Z\"}]"},
            {"name": "purpose", "type": "string", "description": "What this data represents", "required": True, "example": "User signup events for our B2B SaaS"},
            {"name": "strictness", "type": "string", "description": "How strict to make the schema", "required": False, "example": "strict"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: observed shape, JSON Schema, Pydantic class, edge cases captured, edge cases uncertain, recommendations.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on type inference and honest about uncertainty."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes over-strict — re-pin loose option."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; enum candidates often under-flagged."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Schema often misses optional fields; verify."},
        ],
        "variations": [
            {"label": "OpenAPI emit", "description": "Emit as OpenAPI 3.1 component schema.", "prompt_snippet": "Add: ‘also output as OpenAPI 3.1 schema in YAML, suitable for paste into an OpenAPI spec.’"},
            {"label": "TypeScript types", "description": "Emit TypeScript interfaces.", "prompt_snippet": "Add: ‘also emit TypeScript interfaces with appropriate union types and optional fields.’"},
            {"label": "Validation rules", "description": "Add semantic validation hints.", "prompt_snippet": "Add: ‘suggest semantic validation rules the schema can't capture (e.g., ‘end_date must be after start_date’) — for application code, not JSON Schema.’"},
        ],
        "failure_modes": [
            {"symptom": "Inferred constraints are sample artifacts.", "fix": "Re-pin: ‘flag every constraint as ‘inferred from samples; verify against domain knowledge.’ Don't claim min/max as truth.’"},
            {"symptom": "Misses null where some examples have null.", "fix": "Add: ‘any field with null in any example must allow null in the schema.’"},
            {"symptom": "Enum from coincidence (3 samples happen to share values).", "fix": "Add: ‘only propose enum if ≥3 distinct values AND domain knowledge suggests it's bounded; otherwise propose as string with examples.’"},
            {"symptom": "Strict mode rejects valid data.", "fix": "Run schema against held-out examples; relax fields that reject. Default to loose; tighten incrementally.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["structured-extraction-from-docs", "json-output-strict", "data-quality-audit-prompt"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["json-schema", "structured-output", "validation"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How many examples do I need?", "answer": "3-5 minimum; 8-12 is much better. Single examples produce overly-narrow schemas. Examples should include edge cases (null, missing, max/min)."},
            {"question": "Strict or loose?", "answer": "Start loose, tighten over time. Strict from day 1 rejects valid edge cases you didn't see. Loose lets data in; you can analyze actuals and tighten."},
            {"question": "What if the schema needs to change?", "answer": "Version it (schema_v1.json, schema_v2.json). Don't silently evolve; that breaks downstream consumers."},
        ],
        "meta_title": "JSON Schema From Example Outputs — Prompt",
        "meta_description": "Reverse-engineer a JSON Schema from 3-10 example outputs. Includes Pydantic class + honest edge-case uncertainty list.",
    },
    {
        "slug": "extraction-with-confidence-per-field",
        "title": "Field-Level Confidence Extraction",
        "tldr": "Extracts structured fields from unstructured text with per-field confidence (high/medium/low). Useful for any extraction where downstream code needs to know what to trust.",
        "category": "structured-output",
        "tags": ["extraction", "confidence", "validation", "ner"],
        "best_for_tags": ["data-extraction", "trust-aware-pipelines", "human-in-loop"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Resume parsing", "example": "Extract candidate name + email + phone + experience; flag low-confidence for human review."},
            {"scenario": "Invoice extraction", "example": "Vendor + total + line items with confidence; auto-process high-confidence, route others to AP team."},
            {"scenario": "Medical note extraction", "example": "Symptoms + medications + dosages; never auto-accept low confidence."},
            {"scenario": "Compliance form processing", "example": "Field-level confidence drives review queue prioritization."},
        ],
        "when_not_to_use": "Skip for highly structured input (parse, don't extract). Skip when downstream doesn't use the confidence — adds overhead with no benefit.",
        "full_prompt": """You are an extraction agent. For each field, return a value AND a confidence rating.

INPUT
- Unstructured source text: {source_text}
- Fields to extract (with descriptions): {fields_spec}
- Domain rules / formats: {domain_rules}

OUTPUT (one JSON object)

For each field:
- value: the extracted value (or null if not present)
- confidence: high / medium / low
- evidence: the verbatim text span supporting the extraction (or null if inferred)
- reason_if_low_or_medium: 1-line explanation of the uncertainty

Plus:
- overall_confidence: high / medium / low
- ambiguities: list of cases where you made a judgment call

CONFIDENCE LADDER
- HIGH: value is verbatim in source (or trivially normalized — "John Smith" → "Smith, John"); no plausible alternative.
- MEDIUM: value is in source but requires inference (e.g., date format conversion); OR has a plausible alternative interpretation.
- LOW: value is inferred from indirect cues; OR multiple plausible values exist; OR source is ambiguous.
- NULL: field not present in source.

RULES
- Don't invent values. If field isn't in source, value=null and confidence is irrelevant.
- Evidence must be EXACT quote from source. If extracted value is normalized, evidence is the source form.
- For numbers / dates: HIGH only if exact match; MEDIUM if format-converted; LOW if inferred from context.
- For names: HIGH if explicitly stated; MEDIUM if implied; LOW if inferred from email/handle.
- For categorical fields with constrained values: if source value doesn't match a category exactly, confidence ≤ MEDIUM.

SOURCE
{source_text}

FIELDS TO EXTRACT
{fields_spec}

DOMAIN RULES
{domain_rules}

Output JSON only.""",
        "input_variables": [
            {"name": "source_text", "type": "string", "description": "Unstructured text to extract from", "required": True, "example": "Hi, this is Jane Doe from Acme Corp (jane@acme.com). I'd like to discuss the $599 charge from April 12."},
            {"name": "fields_spec", "type": "string", "description": "Fields with descriptions", "required": True, "example": "name: full customer name. email: contact email. company: customer's company. amount_disputed: dollar amount in question. date_of_charge: when the charge happened (YYYY-MM-DD)."},
            {"name": "domain_rules", "type": "string", "description": "Domain-specific extraction rules", "required": False, "example": "Dates in source may be ambiguous (12/04 could be Dec 4 or April 12 depending on locale). Mark as MEDIUM unless context clarifies."},
        ],
        "expected_output": {
            "format": "json",
            "schema": "{ field1: {value, confidence, evidence, reason_if_low_or_medium}, ..., overall_confidence, ambiguities[] }",
            "sample": "{\n  \"name\": {\"value\": \"Jane Doe\", \"confidence\": \"high\", \"evidence\": \"Jane Doe from Acme Corp\"},\n  \"date_of_charge\": {\"value\": \"2024-04-12\", \"confidence\": \"medium\", \"reason_if_low_or_medium\": \"April 12 mentioned without year; assumed current year\"}\n}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Honest about confidence; cites evidence accurately."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes over-confident — re-pin definitions."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; ‘evidence’ field sometimes paraphrased."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to defaults toward ‘medium’; sharpen ladder."},
        ],
        "variations": [
            {"label": "With re-extraction on low confidence", "description": "Two-pass: extract → re-prompt for low-confidence fields.", "prompt_snippet": "After first extraction, for any field with confidence=low, run a second prompt focused on JUST that field with the surrounding context highlighted."},
            {"label": "Schema-aware confidence", "description": "Reduce confidence when value violates schema constraints.", "prompt_snippet": "Add: ‘if extracted value violates a domain constraint (e.g., date in future, negative amount), max confidence is LOW regardless of evidence.’"},
            {"label": "Multi-document", "description": "Extract from a set of docs and reconcile.", "prompt_snippet": "Accept N documents; produce one consolidated extraction with confidence reflecting agreement across docs."},
        ],
        "failure_modes": [
            {"symptom": "Everything is HIGH confidence.", "fix": "Re-pin ladder; require LOW for any inferred value, MEDIUM for any format conversion."},
            {"symptom": "Evidence doesn't actually support the extraction.", "fix": "Add: ‘evidence must be a verbatim span from source; if you can't quote it, value should be null or confidence LOW.’"},
            {"symptom": "Misses partial matches (extracted name vs surname only in source).", "fix": "Add: ‘extract what you can; if only partial info available, value is the partial, evidence is the source span, confidence MEDIUM.’"},
            {"symptom": "Ambiguities list always empty.", "fix": "Force: ‘every extraction has at least one judgment call; list it.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["structured-extraction-from-docs", "json-output-strict", "receipt-invoice-line-item-extractor"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["extraction", "confidence", "structured-output"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is per-field confidence reliable?", "answer": "Distinguishes strongly-grounded extractions from inferred ones reasonably well. Treat as 3-bucket signal (high/medium/low), not as a probability."},
            {"question": "How do I use confidence downstream?", "answer": "Auto-accept HIGH. Route MEDIUM to confirmation flow. Always human-review LOW. Calibrate thresholds based on cost of wrong vs cost of human time."},
            {"question": "What about cross-field consistency?", "answer": "Add a final validation pass — e.g., if email domain doesn't match company, lower both confidences. The model often gets fields right individually but misses cross-field signals."},
        ],
        "meta_title": "Field-Level Confidence Extraction — Prompt",
        "meta_description": "Extract structured fields with per-field confidence + evidence + reason for uncertainty. Drives human-in-the-loop workflows.",
    },
]
