"""Code generation prompts — batch 3."""

RECORDS = [
    {
        "slug": "dockerfile-optimizer",
        "title": "Dockerfile Optimizer",
        "tldr": "Reviews a Dockerfile and proposes a multi-stage, layer-cached, security-hardened rewrite — with each change explained and the size/speed impact estimated.",
        "category": "code-generation",
        "tags": ["docker", "optimization", "devops"],
        "best_for_tags": ["containers", "ci-cd", "image-size"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Bloated production image", "example": "1.5GB image → 300MB through multi-stage + slim base."},
            {"scenario": "Slow CI builds", "example": "Reorder COPY/RUN for better layer caching → 5x faster rebuilds."},
            {"scenario": "Security audit", "example": "Drop root, pin base image digests, remove unnecessary packages."},
            {"scenario": "New engineer onboarding", "example": "Junior wrote a Dockerfile; review + teach via the suggested rewrite."},
        ],
        "when_not_to_use": "Skip for Dockerfiles already well-optimized (diminishing returns). Skip for highly specialized base images (GPU/ML) where the prompt may not know the constraints.",
        "full_prompt": """You are a senior DevOps engineer optimizing a Dockerfile. Output a rewritten version with explanations.

INPUT
- Original Dockerfile: {dockerfile}
- Application context: {app_context}     (language, runtime requirements, etc.)
- Goals (size / speed / security / all): {goals}

OUTPUT

## 1. Analysis of original
- Estimated image size (rough)
- Layer caching efficiency: poor / fair / good
- Security issues: list (running as root, unpinned base, etc.)
- Build performance: any slow layers

## 2. Proposed rewrite
The new Dockerfile, full content, with inline comments where I made non-obvious changes.

## 3. Changes explained
For each meaningful change:
- What changed
- Why
- Expected impact (size MB delta, build time delta, security improvement)

## 4. What I didn't change
2-3 things that look suboptimal but are actually intentional or context-dependent. Why I left them alone.

## 5. Tests to run
Commands to verify the rewrite works:
- docker build with timing
- docker run with healthcheck
- docker scan / trivy for vulnerabilities

OPTIMIZATIONS TO CONSIDER (apply when relevant)
- Multi-stage build (build deps separate from runtime)
- Pin base image digest (FROM image@sha256:...)
- Use slim/alpine base for runtime
- Order COPY/RUN for max layer cache (deps before code)
- Cache mounts: RUN --mount=type=cache,target=/root/.cache/pip
- Non-root user (USER appuser)
- HEALTHCHECK
- Combine RUN apt-get update && apt-get install ... && rm /var/lib/apt/lists/*
- Don't run apt update without install in same RUN (cache invalidation pain)
- COPY --chown=appuser to avoid extra chown layer

ORIGINAL DOCKERFILE
{dockerfile}

Begin.""",
        "input_variables": [
            {"name": "dockerfile", "type": "string", "description": "Original Dockerfile content", "required": True, "example": "FROM python:3.11\\nRUN apt-get update && apt-get install -y curl\\nCOPY . /app\\nWORKDIR /app\\nRUN pip install -r requirements.txt\\nCMD ['python', 'app.py']"},
            {"name": "app_context", "type": "string", "description": "What the app is", "required": True, "example": "Python FastAPI service serving HTTP API"},
            {"name": "goals", "type": "string", "description": "Optimization priorities", "required": False, "example": "Size + security; speed less critical"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Five sections: analysis, rewritten Dockerfile with comments, changes explained, what-not-changed, tests to run.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong multi-stage refactors; honest about size estimates."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes adds unnecessary tools."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; security section sometimes shallow."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Misses multi-stage opportunities; needs explicit prompt."},
        ],
        "variations": [
            {"label": "BuildKit features", "description": "Use modern BuildKit primitives.", "prompt_snippet": "Add: ‘use BuildKit features: --mount=type=cache, --mount=type=secret for build-time secrets, heredoc-style RUN.’"},
            {"label": "GPU image", "description": "NVIDIA base.", "prompt_snippet": "Add: ‘base image must be NVIDIA CUDA-compatible (nvidia/cuda); optimize accordingly.’"},
            {"label": "Distroless final stage", "description": "Smallest possible runtime.", "prompt_snippet": "Add: ‘final stage uses gcr.io/distroless/python3-debian12 or equivalent; preserve compatibility.’"},
        ],
        "failure_modes": [
            {"symptom": "Suggests features that break in production (e.g., distroless without testing).", "fix": "Add: ‘only suggest changes you'd recommend confidently; mark experimental ones.’"},
            {"symptom": "Size estimates fabricated.", "fix": "Add: ‘size estimates marked ‘approximate’; flag where you genuinely don't know.’"},
            {"symptom": "Misses layer-caching opportunities.", "fix": "Re-pin: ‘review COPY/RUN ordering specifically for cache hits.’"},
            {"symptom": "Security hardening skipped.", "fix": "Force: ‘non-root user, pinned base, no apt cache, HEALTHCHECK — list each that applies.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["senior-code-reviewer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["docker", "image-optimization", "layer-cache"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Does this guarantee smaller images?", "answer": "Usually significantly smaller (50-80% reduction is common). But verify with docker images and trivy scan after applying."},
            {"question": "Does the rewrite still work?", "answer": "Should — but always test. Multi-stage refactors can subtly break if a binary moves between stages. Run integration tests on the new image."},
            {"question": "Distroless: always better?", "answer": "Smaller and more secure, but harder to debug (no shell). For mature applications: yes. For services that need shell access for debugging: stick with -slim variants."},
        ],
        "meta_title": "Dockerfile Optimizer — Prompt",
        "meta_description": "Review and rewrite Dockerfiles: multi-stage, layer-cache, non-root, pinned base. Each change explained with size/speed/security impact.",
    },
    {
        "slug": "test-data-generator",
        "title": "Test Data Generator (Realistic + Edge Cases)",
        "tldr": "Generates test data for any schema: a realistic set, plus a curated set of edge cases (boundary values, malformed inputs, Unicode, etc.). Far better coverage than naive Faker output.",
        "category": "code-generation",
        "tags": ["test-data", "edge-cases", "fixtures", "testing"],
        "best_for_tags": ["test-fixtures", "qa", "schema-validation"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Backend API testing", "example": "User schema → 10 realistic + 15 edge-case payloads including null fields, max-length strings, Unicode."},
            {"scenario": "Data pipeline validation", "example": "ETL input schema → adversarial test data (malformed dates, mixed encodings)."},
            {"scenario": "Onboarding test data for staging", "example": "Multi-table schema → realistic linked records that look like production."},
            {"scenario": "Property-based testing seed", "example": "Generate edge-case set; convert to Hypothesis strategies."},
        ],
        "when_not_to_use": "Skip when you have anonymized production samples (they're better). Skip for security-sensitive data — don't generate fake PII for security testing without controls.",
        "full_prompt": """You are generating test data for a schema. Output a realistic set AND a curated edge-case set.

INPUT
- Schema (Pydantic / JSON Schema / TypeScript type): {schema}
- Realistic record count: {n_realistic}
- Edge-case categories to cover: {edge_categories}     (boundary, malformed, unicode, performance, etc.)
- Domain context (informs realistic distributions): {domain}

OUTPUT

## 1. Realistic set ({n_realistic} records)
Records that look like normal production data. Diverse but plausible:
- Mix of values within typical ranges
- Variation in optional fields (some have them, some don't)
- Plausible relationships between fields
- Locale variation if applicable (names, dates, currencies)

## 2. Edge cases (5-15)
Each edge case targets one specific failure mode:

### Edge case N: <name>
- Records: 1-3 records demonstrating the case
- Category: boundary / malformed / unicode / null / extreme / etc.
- What this tests: what should the system DO with this input?
- Expected outcome: pass / reject with specific error / sanitize

Categories to consider:
- BOUNDARY: min/max values, empty strings, 0, negative
- NULL/MISSING: required fields missing, optional fields null
- TYPE COERCION: numbers as strings, dates in odd formats
- UNICODE: emoji, RTL text, control chars, surrogate pairs
- LENGTH: empty, 1-char, max-length, max+1
- INJECTION: SQL/HTML/script injection patterns (testing sanitization)
- ENCODING: mojibake (Ã©), HTML entities, mixed encodings
- TIME: leap days, timezone edges, far-past / far-future
- DUPLICATES: identical records, same email different case

## 3. Output format
- JSON array (default) or
- CSV (if requested)
- Python list of dicts (if requested)

## 4. Test coverage notes
What this data set doesn't cover (things you'd want production traffic or specialized tooling for):
- Race conditions, concurrency
- Time-evolving data (records that change over a period)
- Privacy/PII edge cases that need real samples
- Performance under load (need stress-test tooling)

RULES
- Don't use real PII; even ‘realistic’ data must be synthetic.
- Edge cases must be DIFFERENT from each other; don't generate 5 variants of the same null-field case.
- Domain awareness: dates for a French app should be DD/MM/YYYY in some samples.
- Mark dangerous edge cases (injection patterns) so they don't end up in production by mistake.

Begin.""",
        "input_variables": [
            {"name": "schema", "type": "string", "description": "Schema definition", "required": True, "example": "User: {id: int, email: str, name: str, created_at: datetime, plan: Literal['free', 'pro'], settings: dict | None}"},
            {"name": "n_realistic", "type": "integer", "description": "Number of realistic records", "required": True, "example": "10"},
            {"name": "edge_categories", "type": "string", "description": "Categories of edge cases", "required": False, "example": "boundary, null, unicode, injection"},
            {"name": "domain", "type": "string", "description": "Context for distributions", "required": True, "example": "B2B SaaS users; English-speaking primarily; some international"},
        ],
        "expected_output": {
            "format": "json",
            "sample": "JSON object: {realistic: [...], edge_cases: [{name, records, category, tests, expected}], coverage_notes: [...]}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on diverse realistic distributions + creative edge cases."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes edge cases overlap — re-pin distinctness."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; injection cases sometimes weak."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Realistic OK; edge cases shallow."},
        ],
        "variations": [
            {"label": "Hypothesis strategies", "description": "Generate Python Hypothesis strategies instead of data.", "prompt_snippet": "Add: ‘also output corresponding Hypothesis strategies (st.text(), st.integers(min_value=...), etc.) for property-based testing.’"},
            {"label": "Faker-compatible", "description": "Use Faker library conventions.", "prompt_snippet": "Add: ‘include the Faker locale and provider that would generate equivalent realistic values, for reproducibility.’"},
            {"label": "Multi-table", "description": "Generate linked records across tables.", "prompt_snippet": "Accept multiple schemas; generate linked data (users + orders + addresses) maintaining FK consistency."},
        ],
        "failure_modes": [
            {"symptom": "Edge cases all variants of ‘null’.", "fix": "Re-pin categories list; require coverage of at least 5 distinct categories."},
            {"symptom": "Realistic data unrealistic (everyone named ‘John Doe’).", "fix": "Add: ‘diversity in realistic set — names, locales, plan distributions, registration dates spread across years.’"},
            {"symptom": "Includes real PII patterns by accident.", "fix": "Add: ‘never use real email domains or known names; use example.com / generic placeholders.’"},
            {"symptom": "Injection samples too realistic (could harm if used directly).", "fix": "Add: ‘injection samples must be clearly marked as test data; flag any that look like a real attack payload.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["json-schema-from-examples", "code-snippet-with-tests-tdd"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["test-data", "fixtures", "edge-cases"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How does this beat Faker?", "answer": "Faker produces realistic distributions but no curated edge cases. This prompt explicitly generates boundary/malformed/Unicode/injection cases, with reasoning about what they test."},
            {"question": "Can I use this in CI?", "answer": "Generate once, commit the fixture. Don't regenerate per CI run — non-determinism breaks tests."},
            {"question": "What about privacy?", "answer": "Generated data is synthetic. Still: review before sharing or putting in non-private environments — model might inadvertently produce realistic-looking real names."},
        ],
        "meta_title": "Test Data Generator (Realistic + Edge Cases) — Prompt",
        "meta_description": "Generate test data: realistic distributions + curated edge cases (boundary, null, Unicode, injection). Far better than Faker.",
    },
]
