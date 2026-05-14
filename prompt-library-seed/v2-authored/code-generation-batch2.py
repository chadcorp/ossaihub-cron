"""Code generation prompts — batch 2."""

RECORDS = [
    {
        "slug": "api-design-from-requirements",
        "title": "REST API Design From Requirements",
        "tldr": "Designs a clean REST API from product requirements: resource model, endpoint paths, request/response shapes, error formats, and the questions the design surfaces but doesn't answer.",
        "category": "code-generation",
        "tags": ["api-design", "rest", "openapi", "architecture"],
        "best_for_tags": ["backend-development", "api-first", "platform-engineering"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "New product feature needing API surface", "example": "‘Users need to manage saved searches with sharing’ → REST API with /users/{id}/saved-searches, /shares, etc."},
            {"scenario": "Migration from RPC to REST", "example": "Legacy ad-hoc endpoints → clean resource-based REST design."},
            {"scenario": "Pre-build review", "example": "Backend lead drafts requirements; AI proposes design; team reviews before coding."},
            {"scenario": "API consistency audit", "example": "Multiple endpoints exist; AI proposes a re-design unifying patterns."},
        ],
        "when_not_to_use": "Skip for highly RPC-shaped operations (use gRPC or RPC). Skip for WebSocket / real-time domains where REST is wrong from the start.",
        "full_prompt": """You are a senior API designer. From the requirements, design a REST API.

OUTPUT

## 1. Resource model
What are the nouns? List 4-8 resources with:
- Resource name (singular)
- Identity (UUID? slug? composite?)
- Key fields (just names + types, not full schema)
- Relationships to other resources

## 2. Endpoints
For each resource, list the operations needed (not just full CRUD by default — only what requirements imply).

Format: `METHOD /path/with/{params}` -- brief description.

Include:
- Standard CRUD where needed
- Collection vs item endpoints
- Sub-resource endpoints for relationships
- Action endpoints for state transitions (POST /orders/{id}/cancel, not PATCH with state field)

## 3. Request / response shapes
For 3-5 key endpoints, show the JSON shape (don't bloat — just structure). Include:
- Pagination shape (limit/offset OR cursor)
- Filter/sort query params
- Error response shape (consistent across endpoints)

## 4. Status codes
Map the API's outcomes to HTTP status codes. Highlight non-obvious choices.

## 5. Auth model
What identity flows through? OAuth scopes? API keys with permissions? Tenant scoping?

## 6. Versioning strategy
URL-path versioning (/v1/), header (Accept: application/vnd.api+json;v=1), or no versioning yet?

## 7. Open questions
5-8 things the requirements don't answer that will affect the design.
- Naming choices that have implications
- Edge cases not covered
- Permission boundaries unclear
- Pagination performance assumptions

RULES
- Be Richardson-Maturity-Level-2 by default (resources + verbs). Use hypermedia (HATEOAS) only if explicitly required.
- Names should be consistent: plural for collections (/users), singular for items (/users/{id}).
- Use action endpoints for state transitions, not state-field PATCH (e.g., POST /orders/{id}/refund, not PATCH /orders/{id} {status: 'refunded'}).
- Error response: one consistent shape with code, message, optional details.

REQUIREMENTS
{requirements}

Begin.""",
        "input_variables": [
            {"name": "requirements", "type": "string", "description": "Product requirements / user stories for the API", "required": True, "example": "Users can create saved searches, share them with teammates with view/edit permissions, and receive notifications when others edit."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections covering resources, endpoints, request/response shapes, status codes, auth, versioning, and open questions.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on resource modeling; surfaces real edge cases."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes over-uses generic CRUD when action endpoints fit better."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; open questions can be generic — ask for ‘specific to these requirements’."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Cookie-cutter CRUD; needs explicit ‘only what requirements imply’ reminder."},
        ],
        "variations": [
            {"label": "OpenAPI YAML output", "description": "Emit as OpenAPI 3.1 spec.", "prompt_snippet": "Replace markdown output with: ‘output as OpenAPI 3.1 YAML, capturing all the endpoints, schemas, and security definitions.’"},
            {"label": "gRPC variant", "description": "Same requirements → gRPC service definition.", "prompt_snippet": "Replace REST design with: ‘design as a gRPC service: services, methods, message types, error model, streaming where appropriate.’"},
            {"label": "Public-API-first", "description": "Emphasize developer experience.", "prompt_snippet": "Add: ‘design as if this is a public API — naming consistency, helpful errors, and pagination matter more than internal convenience.’"},
        ],
        "failure_modes": [
            {"symptom": "Generic CRUD for every resource.", "fix": "Re-pin: ‘only the operations requirements imply; sub-resources and actions where they fit naturally.’"},
            {"symptom": "Inconsistent naming (mix of plural / singular).", "fix": "Add: ‘consistency check: every collection plural, every item URL has /{id}.’"},
            {"symptom": "State changes via PATCH instead of action endpoints.", "fix": "Add: ‘for state transitions, prefer POST /resource/{id}/action over PATCH /resource/{id} {state: ...}.’"},
            {"symptom": "Error shape inconsistent.", "fix": "Force a single error shape definition and require all error examples conform."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["senior-code-reviewer", "refactor-to-pattern"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["rest", "api-design", "openapi"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why action endpoints over state-field PATCH?", "answer": "Action endpoints encode intent clearly (POST /orders/{id}/cancel), allow side effects (notifications, idempotency), and make permission boundaries explicit. PATCH with state mixes data update and behavior change."},
            {"question": "Should I version from day 1?", "answer": "Yes if external. Internal APIs can start without versioning, but adding it later is painful. Default to /v1/ in path for clarity."},
            {"question": "How big should an endpoint count be?", "answer": "Resist endpoint sprawl. <30 endpoints for a focused product. If you're at 100+, you probably have multiple services hiding in one API."},
        ],
        "meta_title": "REST API Design From Requirements — Prompt",
        "meta_description": "Design a REST API from product requirements: resources, endpoints, schemas, error format, auth, versioning, and the open questions a team will hit.",
    },
    {
        "slug": "regex-builder-with-explanation",
        "title": "Regex Builder With Plain-English Explanation",
        "tldr": "Builds a regex from a plain-English description, returns it with breakdown of every group, test cases that should and shouldn't match, and a maintenance-friendly verbose-mode version.",
        "category": "code-generation",
        "tags": ["regex", "pattern-matching", "validation", "parsing"],
        "best_for_tags": ["text-processing", "data-validation", "log-parsing"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Validate email but only specific domains", "example": "‘Match emails ending in @acme.com or @subsidiary.acme.com’ → regex + 5 should-match, 5 shouldn't-match examples."},
            {"scenario": "Parse log lines", "example": "Apache log line format → regex with named groups for timestamp, IP, method, URL."},
            {"scenario": "Find phone numbers in messy text", "example": "‘US phone numbers in any common format’ → regex with breakdown + edge cases."},
            {"scenario": "Validate input with project-specific format", "example": "‘Match our internal ticket IDs like INT-12345’ → regex with verbose-mode commentary."},
        ],
        "when_not_to_use": "Skip for parsing structured formats — use a real parser (HTML, JSON, CSV). Regex for HTML is famously bad. Skip when you need recursive parsing (regex can't handle balanced parens).",
        "full_prompt": """You are a regex builder. Build a regex from the plain-English description.

OUTPUT

## 1. Regex
The regex itself, single line, between forward slashes with any flags.
```
/pattern/flags
```

## 2. Verbose-mode version
Same regex with comments and whitespace (Python re.VERBOSE / Perl /x), so future maintainers can understand it.
```python
pattern = re.compile(r'''
    ^                  # start of line
    (?P<group_name>...) # what this group captures
    ...
''', re.VERBOSE)
```

## 3. Breakdown
For each capturing group, named or numbered:
- What it matches
- Examples of what it catches

For each non-trivial token (lookaheads, quantifiers, character classes):
- What it does
- Why it's in the pattern

## 4. Test cases

### Should match (5+)
Concrete strings that match. Show what each capture group captures.

### Should NOT match (5+)
Concrete strings that look like they might match but shouldn't. Explain why.

## 5. Edge cases to consider
3-5 cases the requester might want to think about:
- Internationalization (Unicode in email local parts? non-ASCII names?)
- Whitespace handling
- Case sensitivity
- Newline handling

## 6. When this regex is wrong
2-3 patterns of inputs where this regex will fail or be misleading. Honest about limits.

RULES
- Default to PCRE syntax; specify the flavor if it matters (Python re, JavaScript, POSIX ERE).
- Default to non-greedy quantifiers when matching ‘until a delimiter’.
- Prefer named groups for anything that will be extracted.
- Don't write 200-character one-liners — if it gets long, break out the verbose version and recommend using it.
- Catastrophic backtracking: if the pattern could be vulnerable (nested quantifiers), flag it.

DESCRIPTION
{description}

LANGUAGE/FLAVOR (default: PCRE / Python re)
{language_flavor}

Now build the regex.""",
        "input_variables": [
            {"name": "description", "type": "string", "description": "What the regex should match", "required": True, "example": "Match URLs that start with http or https, optionally with www, ending in any TLD, capturing the host and path."},
            {"name": "language_flavor", "type": "string", "description": "Regex flavor", "required": False, "example": "Python re"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: regex one-liner, verbose version, breakdown, test cases (should/shouldn't match), edge cases, when this regex is wrong.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong test cases including tricky negative ones."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally produces over-permissive patterns."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid baseline; edge cases section can be generic."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Useful for simple patterns; verify carefully on complex ones."},
        ],
        "variations": [
            {"label": "Multi-language emit", "description": "Output regex in multiple language flavors.", "prompt_snippet": "Add: ‘also provide the regex adjusted for: JavaScript, Go (RE2), POSIX ERE — note where syntax differs.’"},
            {"label": "Catastrophic backtracking check", "description": "Specifically audit for ReDoS.", "prompt_snippet": "Add Step 7: ‘ReDoS audit — identify any nested quantifiers, alternations, or repeats that could cause catastrophic backtracking. Propose a safe rewrite.’"},
            {"label": "Replace with parser when wrong", "description": "Suggest non-regex alternatives.", "prompt_snippet": "Add: ‘if the right tool is a parser (HTML, JSON, etc.), say so and link to the appropriate library instead of pretending regex fits.’"},
        ],
        "failure_modes": [
            {"symptom": "Regex is over-permissive (matches strings it shouldn't).", "fix": "Re-pin: ‘run mental test against each Shouldn't-Match example before emitting.’"},
            {"symptom": "Tests don't actually exercise the edge cases mentioned.", "fix": "Add: ‘test cases must include at least one for each edge case mentioned in Section 5.’"},
            {"symptom": "Verbose version is just the regex with line breaks, no comments.", "fix": "Add: ‘each non-trivial line in verbose version has a comment explaining what it does.’"},
            {"symptom": "Vulnerable to catastrophic backtracking.", "fix": "Use the dedicated variation; otherwise add: ‘before emitting, check for nested quantifiers like (a+)+ or (a|aa)+; rewrite to avoid them.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["structured-extraction-from-docs"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["regex", "pattern-matching"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why both compact and verbose versions?", "answer": "Compact for one-liner use (config files, short scripts). Verbose for code that lives — future maintainers (including you) will thank you for inline comments."},
            {"question": "Can the model write SAFE regex for untrusted input?", "answer": "It can flag catastrophic-backtracking patterns when asked. Don't trust untrusted-input regex without explicit ReDoS check + timeout in your matching code."},
            {"question": "What about Unicode?", "answer": "Specify in the description if you need Unicode-aware matching. \\\\w means different things in different regex flavors — call out the flavor in the input."},
        ],
        "meta_title": "Regex Builder With Plain-English Explanation",
        "meta_description": "Build a regex with verbose-mode version, group-by-group breakdown, positive/negative test cases, edge cases, and limits.",
    },
    {
        "slug": "sql-schema-migration-safe",
        "title": "Safe SQL Schema Migration",
        "tldr": "Generates a forward + rollback SQL migration with safety analysis: lock impact, replication delay, downtime risk, and the exact steps to roll forward without breaking running queries.",
        "category": "code-generation",
        "tags": ["sql", "migration", "schema-change", "postgres"],
        "best_for_tags": ["production-databases", "zero-downtime", "schema-evolution"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Add NOT NULL column to a 50M-row table", "example": "Generate online-safe migration with default backfill, then NOT NULL constraint set."},
            {"scenario": "Rename a column without breaking deploys", "example": "Multi-stage migration: add new, dual-write, backfill, drop old — staged across releases."},
            {"scenario": "Change a column type", "example": "Same multi-stage pattern: add new column, dual-write/migrate, switch reads, drop old."},
            {"scenario": "Add an index on a hot table", "example": "CREATE INDEX CONCURRENTLY with monitoring guidance + rollback if it fails partway."},
        ],
        "when_not_to_use": "Skip for small/dev databases where direct ALTER is fine. Skip when you're not running Postgres or MySQL — syntax and locking behavior differ in other engines.",
        "full_prompt": """You are a database engineer writing a production migration. The team runs Postgres / MySQL on a busy table.

INPUT
- Desired schema change: {change}
- Database engine: {engine}
- Table size (approx rows): {table_size}
- Write load: {write_load}
- Replication setup: {replication}                  (single primary / streaming replicas / read replicas / multi-region)

OUTPUT

## 1. Risk assessment
- Lock impact: which lock type is acquired by each step? For how long?
- Replication delay: will this cause lag on replicas?
- Downtime: any blocking writes / blocking reads?
- Rollback risk: what makes this hard to undo?

## 2. Staged migration plan
The safe path. Usually multiple deploys, NOT one big ALTER. For each stage:
- Stage N: SQL to run + when (deploy boundary, after monitoring window, etc.).
- What the application code looks like during this stage (dual-write? feature flag? old or new column?).
- How to verify before moving to next stage.

## 3. Forward SQL
The exact SQL for each stage. Use the engine's online-safe primitives:
- Postgres: ADD COLUMN with default (PG11+), CREATE INDEX CONCURRENTLY, NOT VALID + VALIDATE for constraints
- MySQL: ALGORITHM=INPLACE, LOCK=NONE where supported; INSTANT for 8.0+

## 4. Rollback SQL
For each stage, the reverse. If a stage is one-way (e.g., dropping a column), say so explicitly and propose a different path that's reversible.

## 5. Monitoring during the migration
- Specific metrics to watch (active queries, replication lag, lock-wait time, table bloat).
- Specific alerts that should trigger pause.
- How long to wait between stages.

## 6. Pre-flight checklist
- Backup confirmed within X hours.
- Replica lag baseline measured.
- Application code deployed compatible with both schemas.
- Maintenance window booked (or "no window needed because online" justified).

RULES
- Default to ONLINE / non-blocking when possible.
- If a NOT NULL is required, use the multi-stage pattern (add column nullable + default → backfill → NOT NULL).
- If renaming, never just RENAME — use add new, dual-write, backfill, switch reads, drop old.
- For huge tables, CREATE INDEX CONCURRENTLY; never plain CREATE INDEX in production.
- Be explicit about lock types in Postgres (ACCESS EXCLUSIVE vs SHARE UPDATE EXCLUSIVE).

Now write the migration.""",
        "input_variables": [
            {"name": "change", "type": "string", "description": "Schema change requested", "required": True, "example": "Add a NOT NULL column 'preferences' (JSONB) to users with default '{}'"},
            {"name": "engine", "type": "string", "description": "Database engine + version", "required": True, "example": "Postgres 15"},
            {"name": "table_size", "type": "string", "description": "Approximate row count", "required": True, "example": "50M rows"},
            {"name": "write_load", "type": "string", "description": "Write QPS or pattern", "required": True, "example": "~500 writes/sec sustained"},
            {"name": "replication", "type": "string", "description": "Replica topology", "required": False, "example": "1 primary, 2 streaming replicas, 1 used for analytics"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: risk, staged plan, forward SQL, rollback SQL, monitoring, pre-flight checklist.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on multi-stage patterns and on naming actual lock types."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally proposes single-step ALTER for large tables — call it out."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Strong on Postgres specifics; weaker on MySQL nuances."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to skip the staged pattern; needs reminder for online safety."},
        ],
        "variations": [
            {"label": "pt-online-schema-change wrapped", "description": "For MySQL, propose pt-osc command.", "prompt_snippet": "Add: ‘if engine is MySQL and table is large, propose pt-online-schema-change command with appropriate options.’"},
            {"label": "gh-ost variant", "description": "For MySQL with replicas.", "prompt_snippet": "Add: ‘if engine is MySQL with read replicas, propose gh-ost configuration with replica-cut-over option.’"},
            {"label": "Rails / Django migration code", "description": "Wrap SQL in framework migration.", "prompt_snippet": "Add: ‘also emit the staged migrations as Django migration files (or Rails ActiveRecord migrations) where each stage is a separate migration class.’"},
        ],
        "failure_modes": [
            {"symptom": "Single-step ALTER on a huge table.", "fix": "Re-pin staged pattern; add table-size-based guard: ‘>10M rows or >100 writes/sec mandates staged.’"},
            {"symptom": "Rollback for irreversible step (DROP COLUMN) marked ‘easy’.", "fix": "Add: ‘DROP is one-way; rollback requires the column to still be in the previous deploy. State the constraint explicitly.’"},
            {"symptom": "Missing CONCURRENTLY on index.", "fix": "Add: ‘CREATE INDEX without CONCURRENTLY is a production outage; never emit it for active tables.’"},
            {"symptom": "Lock type isn't named.", "fix": "Add: ‘every step names the lock type acquired and its duration estimate.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["sql-query-from-natural-language", "senior-code-reviewer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["online-schema-change", "lock-type"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is the multi-stage pattern always necessary?", "answer": "For large active tables, yes. For small or low-write tables, a single ALTER inside a transaction is fine. The prompt's table-size + write-load inputs drive this decision."},
            {"question": "What about Postgres ADD COLUMN with default in PG11+?", "answer": "PG11+ doesn't rewrite the table when adding a column with a non-volatile default — fast. But NOT NULL on the new column still needs the multi-stage pattern."},
            {"question": "Can I skip the monitoring section?", "answer": "Don't. The most common cause of online-migration outages is moving to the next stage before the current one has actually finished propagating."},
        ],
        "meta_title": "Safe SQL Schema Migration — Prompt",
        "meta_description": "Generate staged online-safe migrations with forward + rollback SQL, lock analysis, monitoring guidance, and a pre-flight checklist.",
    },
    {
        "slug": "code-snippet-with-tests-tdd",
        "title": "Code Snippet With TDD Tests First",
        "tldr": "Writes test cases FIRST, then implementation that passes them — including edge cases and error paths. Output is shaped for ‘copy into a real repo and refactor’ rather than ‘demo code.’",
        "category": "code-generation",
        "tags": ["tdd", "test-first", "python", "implementation"],
        "best_for_tags": ["test-coverage", "tdd-workflow", "robust-code"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Greenfield utility function", "example": "‘Write a function to parse a phone number into E.164 format.’ Get back tests for happy path + edge cases + the implementation."},
            {"scenario": "Adding a new method to an existing class", "example": "Specify the existing class shape; AI writes the new method + its tests."},
            {"scenario": "Bug fix with regression test", "example": "Describe the bug; AI writes a failing test that reproduces it, then the fix."},
            {"scenario": "Library function for production code", "example": "Robust with type hints, docstrings, and tests — copy-into-codebase-ready."},
        ],
        "when_not_to_use": "Skip for one-off scripts where tests aren't worth it. Skip for highly stateful code where the test setup IS the hard part — write the integration test by hand.",
        "full_prompt": """You are writing production-quality code using TDD. Tests FIRST, then implementation.

INPUT
- Function/method signature (with types): {signature}
- Behavior description: {behavior}
- Language: {language}
- Test framework: {test_framework}                  (pytest / jest / etc.)

OUTPUT

## Step 1: Tests
Write the tests FIRST, before any implementation. Cover:
- Happy path (1-2 cases)
- Edge cases (empty input, max size, boundary values, etc.)
- Error paths (invalid input, malformed data) — what exception or return value?
- Real-world weird cases (Unicode in inputs, very long strings, etc.)

8-15 test cases total. Each test:
- Descriptive name (`test_returns_none_for_empty_string`, not `test_1`)
- One assertion focus per test
- Clear input → expected output

## Step 2: Implementation
Write the function. Constraints:
- Type hints on every parameter and return.
- Docstring with one-line summary + Args/Returns/Raises sections.
- Internal validation matches the test cases.
- Style: clean, readable, comment ONLY for non-obvious decisions.

## Step 3: Pre-flight
A short section noting:
- Any test case where the implementation is doing something tricky (worth a comment in code).
- Any external dependency that should be passed in (don't hardcode http clients, file paths, etc.).
- Any case the tests didn't cover but production code should — call it out so the user can decide whether to add the test.

RULES
- Tests are the spec. Implementation must pass all of them.
- Don't catch and re-raise without adding info; let exceptions propagate unless you're translating to a domain-specific error.
- No print() or logging in the function unless explicitly requested.
- Tests use clear AAA pattern: Arrange, Act, Assert (or G-W-T: Given, When, Then).

Now write tests, then implementation, then pre-flight.""",
        "input_variables": [
            {"name": "signature", "type": "string", "description": "Function signature with types", "required": True, "example": "def parse_phone(text: str) -> str | None"},
            {"name": "behavior", "type": "string", "description": "What the function does", "required": True, "example": "Extracts the first valid US phone number from text and returns it in E.164 format (+1XXXXXXXXXX). Returns None if no valid number found."},
            {"name": "language", "type": "string", "description": "Programming language", "required": True, "example": "Python"},
            {"name": "test_framework", "type": "string", "description": "Test framework to use", "required": True, "example": "pytest"},
        ],
        "expected_output": {
            "format": "code",
            "sample": "Test block first (8-15 tests), then the implementation, then a short pre-flight note section.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong test coverage and honest pre-flight notes."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally writes implementation that subtly fails a test it wrote — sanity check by running."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; tests sometimes have weaker edge cases."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Happy-path heavy; explicitly request edge cases and error paths."},
        ],
        "variations": [
            {"label": "Property-based tests", "description": "Add Hypothesis tests for invariants.", "prompt_snippet": "Add: ‘also add 2-3 Hypothesis property-based tests for invariants (idempotency, monotonicity, etc.).’"},
            {"label": "Mutation-tested", "description": "Suggest mutations that should fail.", "prompt_snippet": "Add: ‘list 3 small mutations of the implementation (off-by-one, wrong operator, etc.) that the tests would catch — proves coverage isn't shallow.’"},
            {"label": "Async version", "description": "Async function and tests.", "prompt_snippet": "Replace function with async def; tests use pytest-asyncio. Make sure all assertions are inside `async def test_*`."},
        ],
        "failure_modes": [
            {"symptom": "Implementation doesn't pass own tests.", "fix": "Re-pin: ‘before final output, mentally run every test against the implementation; if any fails, rewrite.’"},
            {"symptom": "Tests are too coupled (changing implementation breaks all of them).", "fix": "Add: ‘tests assert on observable behavior, not internal implementation details.’"},
            {"symptom": "No edge-case coverage.", "fix": "Add: ‘list at minimum: empty/null, boundary value, max size, unicode, malformed input.’"},
            {"symptom": "Implementation has print() / debug code.", "fix": "Re-pin: ‘no print() or logging unless requested; tests assert on returns, not side effects.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["pytest-generator-from-source", "senior-code-reviewer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["tdd", "unit-testing"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why tests first?", "answer": "Forces the model to commit to a behavior contract before implementation. Implementation drift (where the function does ‘mostly what you wanted, except…’) becomes visible immediately."},
            {"question": "Should I trust the tests are complete?", "answer": "No — review them. The model writes thorough tests but won't always know your domain's edge cases. Add ones it missed."},
            {"question": "How do I integrate with existing code?", "answer": "Paste the surrounding context in `behavior`: ‘this is a method on Class X which has attributes A, B, C.’ The model will fit conventions."},
        ],
        "meta_title": "Code Snippet With TDD Tests First — Prompt",
        "meta_description": "Write tests FIRST, then the implementation that passes them — happy path, edge cases, errors. Includes a pre-flight note for missed cases.",
    },
]
