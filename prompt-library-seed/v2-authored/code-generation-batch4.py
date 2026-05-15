"""Code generation — batch 4."""

RECORDS = [
    {
        "slug": "test-suite-coverage-gap-finder",
        "title": "Test Suite Coverage Gap Finder",
        "tldr": "Reads a function + its existing tests and identifies coverage gaps: untested branches, edge cases, error paths. Returns specific new test cases to add (with code) — not just ‘add more tests’.",
        "category": "code-generation",
        "tags": ["testing", "coverage", "tdd", "quality"],
        "best_for_tags": ["backend-engineering", "qa", "legacy-code"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "PR review with thin tests", "example": "New code shipped with 2 happy-path tests; this prompt suggests 6 more covering edges."},
            {"scenario": "Legacy function with 30% coverage", "example": "Bring it up to 80% with targeted tests, not bulk-generated nonsense."},
            {"scenario": "Pre-refactor safety net", "example": "Before refactoring complex function, ensure tests cover all current behavior."},
            {"scenario": "Bug-driven test addition", "example": "Bug reported in edge case; this prompt suggests the broader edge-case family to test."},
        ],
        "when_not_to_use": "Skip for simple pure functions (existing tests probably cover what matters). Skip when the code is changing rapidly — invest in tests once design stabilizes.",
        "full_prompt": """You are auditing test coverage for a specific function. Identify gaps, propose specific new tests.

INPUT
- Function under test (full code): {function_code}
- Existing tests for this function: {existing_tests}
- Language / framework: {language}
- Coverage report (if available): {coverage_report}

OUTPUT

## 1. Function's behavioral surface
List every observable behavior:
- Input parameters (types, ranges, optional/required)
- Return values (success cases + error cases)
- Side effects (DB writes, file I/O, external API calls)
- Exceptions raised
- Branches (if/else, switch cases, ternaries)
- Loops (bounded? what termination?)

## 2. What existing tests cover
For each existing test, note what behavior it tests. Highlight overlaps (multiple tests covering same thing) and obvious gaps.

## 3. Coverage gaps (numbered)
For each gap:

### Gap N: <one-line description>
- What behavior is NOT tested
- Why it matters (severity: blocker / major / minor)
- Suggested test (code in {language}):
  ```{language}
  // ...
  ```

Aim for 5-10 high-value gap tests, NOT a generic ‘all branches’ list.

## 4. Property-based test suggestions (if appropriate)
1-3 invariants that should hold across many inputs:
- "For all valid X, fn(X) returns Y in [range]"
- "fn(fn(X)) == fn(X) (idempotence)"
- "Input parity (e.g., sorted input → sorted output)"

Provide as Hypothesis or fast-check pseudocode.

## 5. Tests I'd NOT prioritize
2-3 things that look like gaps but aren't worth testing:
- "Library-internal types (trust the library)"
- "Trivial getters/setters"
- "Mocks that don't reflect real behavior"

## 6. Refactor recommendation (if applicable)
If the function has too many responsibilities to test cleanly, suggest a refactor that would make it testable. Don't propose the refactor as a test — note it explicitly.

CRITICAL RULES
- Suggested tests are RUNNABLE code, not pseudocode.
- Cover edge cases: empty, null, max-size, off-by-one, unicode, timezone, concurrency, error paths.
- Don't manufacture gap tests for completeness — only ones with real value.
- If existing tests are GOOD, say so: section 3 can have ‘no critical gaps; minor edge case test added below.’

FUNCTION
{function_code}

EXISTING TESTS
{existing_tests}

LANGUAGE: {language}

Audit.""",
        "input_variables": [
            {"name": "function_code", "type": "string", "description": "Full function code", "required": True, "example": "def parse_price(s: str) -> float:\\n    s = s.strip().replace('$', '').replace(',', '')\\n    if not s: return 0.0\\n    return float(s)"},
            {"name": "existing_tests", "type": "string", "description": "Existing tests", "required": True, "example": "def test_basic(): assert parse_price('$1,000') == 1000.0\\ndef test_empty(): assert parse_price('') == 0.0"},
            {"name": "language", "type": "string", "description": "Language/framework", "required": True, "example": "Python with pytest"},
            {"name": "coverage_report", "type": "string", "description": "Coverage data if available", "required": False, "example": "Lines covered: 4/6. Missing: lines 5, 6 (error handling)"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: behavioral surface, what's covered, numbered gaps with runnable test code, property-based test suggestions, what-not-to-test, refactor recommendation.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Specific behavioral analysis; runnable test code."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes over-generates edge cases — re-pin ‘high-value only.’"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; property-based suggestions can be weaker."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple functions; thin on complex behavior."},
        ],
        "variations": [
            {"label": "Mutation-tested", "description": "Add mutation testing suggestions.", "prompt_snippet": "Add: ‘suggest 3-5 mutations that would survive existing tests (e.g., flipping > to >=). For each, write the test that would catch it.’"},
            {"label": "Performance test branch", "description": "Tests for performance regressions.", "prompt_snippet": "Add: ‘suggest performance tests for any function with loops or DB calls. Define acceptable bounds (e.g., <100ms for N=1000).’"},
            {"label": "Multi-language", "description": "Java / TypeScript / Go variant.", "prompt_snippet": "Replace pytest with junit/jest/go-test. Adjust syntax in suggested tests."},
        ],
        "failure_modes": [
            {"symptom": "Lists EVERY possible test (low signal).", "fix": "Re-pin: ‘high-value gaps only. 5-10 specific tests > 30 generic ones.’"},
            {"symptom": "Suggested tests are pseudocode, not runnable.", "fix": "Add: ‘every test is runnable in the specified framework. Show real assertion syntax.’"},
            {"symptom": "Misses error paths.", "fix": "Add: ‘error paths (exceptions, error returns) are often the biggest gaps. Explicitly check.’"},
            {"symptom": "Suggests trivial coverage (test getters).", "fix": "Add: ‘what-not-to-test section: trivial accessors, library internals. Don't suggest these.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["code-snippet-with-tests-tdd", "pytest-generator-from-source", "senior-code-reviewer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["test-coverage", "edge-cases"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should I aim for 100% coverage?", "answer": "No — coverage rate is a weak signal. 85% of high-value tests > 100% with bulk-generated low-value tests. Tune for COVERAGE OF FAILURE MODES, not lines."},
            {"question": "Will it understand my framework?", "answer": "Major frameworks (pytest, jest, junit, go-test, rspec): yes. Niche or custom frameworks: provide an example test in the framework so it can match style."},
            {"question": "What about integration tests?", "answer": "This prompt focuses on unit tests. For integration/E2E, use a different prompt with full system context."},
        ],
        "meta_title": "Test Suite Coverage Gap Finder — Prompt",
        "meta_description": "Audit existing tests + identify high-value gaps. Returns runnable test code, property-based suggestions, refactor recommendations if needed.",
    },
    {
        "slug": "code-comment-explainer",
        "title": "Code Comment Explainer (Plain-English Inline)",
        "tldr": "Adds plain-English inline comments to a code block: explains WHY (not just what), notes non-obvious decisions, flags tricky parts. Doesn't comment-pollute trivial lines.",
        "category": "code-generation",
        "tags": ["comments", "documentation", "readability"],
        "best_for_tags": ["legacy-code-onboarding", "tutorials", "teaching"],
        "difficulty_tier": "beginner",
        "featured": False,
        "use_cases": [
            {"scenario": "Onboarding new engineer to a codebase", "example": "Critical algorithm needs annotation; this prompt explains the WHY."},
            {"scenario": "Open-source project tutorial", "example": "Tutorial snippet needs walk-through; inline comments make it self-explanatory."},
            {"scenario": "Code review feedback", "example": "Reviewer wants to flag what's confusing; prompt suggests where comments would help."},
            {"scenario": "Legacy code archaeology", "example": "Old code with no comments; this prompt reconstructs likely INTENT (with caveats)."},
        ],
        "when_not_to_use": "Skip for trivial code (just a few lines). Skip when the code itself should be REFACTORED to not need comments (rename a variable, extract a function).",
        "full_prompt": """You are adding plain-English comments to code. Comments explain WHY, not what.

INPUT
- Code block: {code}
- Language: {language}
- Reader context (who's reading, what they know): {reader_context}
- Comment style: {comment_style}    (per-line / per-block / docstring-only)

OUTPUT

## 1. Annotated code

```{language}
<code with comments inline>
```

Comment rules:
- WHY > WHAT. Don't say "increment counter" for `counter += 1`. Say "track retry attempts" if that's why.
- ONE comment per logical block, not per line.
- Highlight NON-OBVIOUS decisions. ("Using nested loops here because Set lookup would lose ordering required downstream.")
- Flag TRICKY parts. ("Off-by-one is intentional — we want closed-open interval.")
- Mark UNCERTAIN parts. ("Likely-but-not-confirmed: this assumes upstream sorted by date.")

## 2. Summary block (above code)
2-3 lines explaining what the code does at a high level:
```
# This function:
#   - Takes a list of API responses
#   - Filters out failures and dedupes by request_id
#   - Returns a normalized list ready for analytics
```

## 3. Caveats / open questions
2-4 things YOU couldn't determine from the code alone:
- "I assume X means Y; not verified by reading caller context"
- "Magic constant 0.65 looks like a threshold; explanation not in this file"
- "This catches exceptions silently; intentional?"

## 4. Suggested refactors (if applicable)
2-3 places where renaming a variable or extracting a function would REPLACE the need for a comment. Brief — these are observations, not full refactor plans.

CRITICAL RULES
- Don't add comments where code is self-explanatory. (Bad: `# loop through items` above `for item in items:`.)
- Don't comment OVER what the code does — defer to the code where it speaks.
- Be honest about uncertainty: "Likely Y because..." not "Definitely Y."
- Match the host file's existing comment style (Python docstrings vs //, etc.).

CODE
{code}

LANGUAGE: {language}

READER: {reader_context}

Annotate.""",
        "input_variables": [
            {"name": "code", "type": "string", "description": "Code to annotate", "required": True, "example": "def dedupe(items):\\n    seen = set()\\n    out = []\\n    for x in items:\\n        if x.id in seen: continue\\n        seen.add(x.id)\\n        out.append(x)\\n    return out"},
            {"name": "language", "type": "string", "description": "Programming language", "required": True, "example": "Python"},
            {"name": "reader_context", "type": "string", "description": "Reader's context", "required": True, "example": "Junior engineer onboarding, familiar with Python basics but not our codebase"},
            {"name": "comment_style", "type": "string", "description": "Comment style preference", "required": False, "example": "per-block"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Summary block + annotated code with WHY comments + caveats/open-questions + suggested refactors.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong WHY-focus; honest uncertainty."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes adds WHAT-comments — call out."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; refactor suggestions vary."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Tends toward WHAT-comments; reinforce WHY."},
        ],
        "variations": [
            {"label": "Tutorial-mode", "description": "Heavier explanation for teaching.", "prompt_snippet": "Adjust: ‘this is a TUTORIAL audience — beginner. Comment density can be higher; explain idioms and conventions, not just business logic.’"},
            {"label": "Strict-minimal", "description": "Only critical comments.", "prompt_snippet": "Adjust: ‘only comment where code's INTENT is NOT obvious. If the code is self-explanatory, no comment.’"},
            {"label": "Algorithmic deep-dive", "description": "For complex algorithms.", "prompt_snippet": "Add: ‘also produce an Algorithm walkthrough section above the code — describe complexity, invariants, edge case handling.’"},
        ],
        "failure_modes": [
            {"symptom": "Adds comments to every line (noise).", "fix": "Re-pin: ‘ONE comment per logical block. Self-explanatory code = no comment.’"},
            {"symptom": "Comments restate what code does.", "fix": "Add: ‘WHY-comment, not WHAT. ‘# track retries’ not ‘# increment counter.’’"},
            {"symptom": "Doesn't flag uncertainty.", "fix": "Force: ‘when guessing intent, label as guess. ‘Likely X because Y’ not ‘X.’’"},
            {"symptom": "Suggests refactors as comments (wrong layer).", "fix": "Add: ‘refactor suggestions go in Section 4, not in inline comments.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["senior-code-reviewer", "regex-builder-with-explanation"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["code-comments", "documentation"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should comments be added everywhere?", "answer": "No. Code's clarity is its own documentation. Comments shine where intent is non-obvious. The best response to ‘this needs a comment’ is often ‘this needs a refactor.’"},
            {"question": "What if the code's intent is genuinely unclear?", "answer": "Section 3 (caveats) captures this. Comments labeled as guess help readers; bluffing certainty doesn't."},
            {"question": "Will this work for non-English codebases?", "answer": "Match the host language. If file's comments are in another language, suggest matching that — don't switch to English."},
        ],
        "meta_title": "Code Comment Explainer (Plain-English Inline) — Prompt",
        "meta_description": "Add WHY-focused inline comments to code. Highlights non-obvious decisions, flags uncertainty, suggests refactors where comments aren't enough.",
    },
    {
        "slug": "openapi-spec-from-handler",
        "title": "OpenAPI Spec From a Handler Function",
        "tldr": "Reads a request handler (FastAPI / Express / Rails) and generates an OpenAPI 3.1 specification: paths, parameters, request/response schemas, error responses, examples. Flags what it had to infer.",
        "category": "code-generation",
        "tags": ["openapi", "api-docs", "fastapi", "spec-generation"],
        "best_for_tags": ["api-development", "documentation", "sdk-generation"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Auto-generate API docs", "example": "Backend handler exists; this prompt produces OpenAPI for client SDK gen + Swagger UI."},
            {"scenario": "Legacy API documentation", "example": "Documented endpoints retrofit — read 30 handlers, generate the spec."},
            {"scenario": "Public API release prep", "example": "Internal handler → public OpenAPI with proper examples and error responses."},
            {"scenario": "Pre-deploy validation", "example": "Generated spec compared to checked-in spec — diff catches drift."},
        ],
        "when_not_to_use": "Skip when framework auto-generates OpenAPI (FastAPI does much of this natively). Skip for non-REST APIs (gRPC, GraphQL).",
        "full_prompt": """You are generating an OpenAPI 3.1 specification from a handler function.

INPUT
- Handler code: {handler_code}
- Framework: {framework}
- Existing schemas / models referenced: {existing_schemas}
- Auth pattern used: {auth_pattern}
- Sample request / response (if available): {sample_data}

OUTPUT (YAML, OpenAPI 3.1)

```yaml
openapi: 3.1.0
info:
  title: <inferred from handler scope>
  version: <inferred>

paths:
  /<path>:
    <method>:
      summary: <one-line>
      description: |
        <2-3 sentences. What this endpoint does and when to use it.>
      operationId: <camelCase from function name>
      tags:
        - <group from handler module / class>
      parameters:
        - name: <param>
          in: path | query | header
          required: true|false
          schema:
            type: ...
          description: ...
          example: ...
      requestBody:
        required: true|false
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/<Schema>'
            examples:
              normal:
                value: ...
      responses:
        '200':
          description: <successful case>
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/<ResponseSchema>'
              examples:
                ...
        '4xx':
          description: ...
        '5xx':
          description: ...
      security:
        - <auth scheme>

components:
  schemas:
    <RequestSchema>:
      type: object
      required: [...]
      properties: ...
    <ResponseSchema>: ...

  securitySchemes:
    <name>: ...
```

## After the YAML, output:

### Assumptions I had to make
List what was INFERRED vs explicit in the code:
- "Request body schema inferred from Pydantic model `UserCreate` — assumed all fields visible in code are public."
- "Error response shape assumed standard ProblemDetail (RFC 7807) — code shows custom format; please verify."
- "200 examples generated from positive-case dummy data."

### Suggested manual additions
What an automated extractor CAN'T add:
- Rate-limit headers
- Pagination patterns (when handler doesn't expose them clearly)
- Authorization scope details
- Webhook callbacks
- Deprecation notices

CRITICAL RULES
- Don't invent schemas. If the handler references `MyModel` and you don't have its definition, mark it as a stub: `schema: type: object  # NOTE: stub — model definition not in input`.
- Status codes from handler's actual paths — don't add generic ones.
- Examples should be REALISTIC (don't use `string` as a sample value).
- The OpenAPI spec must be VALID YAML — test for syntax errors.

HANDLER
{handler_code}

FRAMEWORK: {framework}

Generate the spec.""",
        "input_variables": [
            {"name": "handler_code", "type": "string", "description": "Handler function code", "required": True, "example": "@router.post('/users')\\ndef create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:\\n    if db.query(User).filter_by(email=payload.email).first():\\n        raise HTTPException(409, 'Email taken')\\n    user = User(**payload.dict())\\n    db.add(user); db.commit()\\n    return UserResponse.from_orm(user)"},
            {"name": "framework", "type": "string", "description": "Framework", "required": True, "example": "FastAPI"},
            {"name": "existing_schemas", "type": "string", "description": "Referenced schemas", "required": False, "example": "class UserCreate(BaseModel): email: EmailStr; password: SecretStr; name: str"},
            {"name": "auth_pattern", "type": "string", "description": "Auth used", "required": False, "example": "JWT bearer token via Depends(auth_required)"},
            {"name": "sample_data", "type": "string", "description": "Sample request/response if available", "required": False, "example": "Example request: {email: 'jane@example.com', password: '...', name: 'Jane'}. Response: {id: 1, email: '...', name: '...', created_at: '2026-05-14T10:00:00Z'}"},
        ],
        "expected_output": {
            "format": "code",
            "sample": "Complete OpenAPI 3.1 YAML + assumptions list + suggested manual additions.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong YAML structure; honest about inferences."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes invents schemas — re-pin ‘stub if not in input.’"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; examples can be unrealistic (default values)."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple handlers; thin on complex schemas."},
        ],
        "variations": [
            {"label": "Multiple handlers → unified spec", "description": "Read 5-10 handlers and merge.", "prompt_snippet": "Accept multiple handler code blocks; produce ONE unified spec with all paths under same `info`."},
            {"label": "GraphQL adaptation", "description": "GraphQL schema instead.", "prompt_snippet": "Replace OpenAPI with GraphQL SDL. Adjust to types + queries + mutations + subscriptions."},
            {"label": "Diff with existing", "description": "Compare to checked-in spec.", "prompt_snippet": "Accept existing spec; produce DIFF — added paths, removed paths, breaking changes. Useful for CI guardrails."},
        ],
        "failure_modes": [
            {"symptom": "Invents schemas not in input.", "fix": "Re-pin: ‘mark unknown schemas as stubs; do NOT fabricate full schemas.’"},
            {"symptom": "YAML syntax errors.", "fix": "Add: ‘test the YAML structurally. Indentation, quotes, $refs valid.’"},
            {"symptom": "Examples are placeholder values.", "fix": "Add: ‘examples must be realistic — use believable values for emails, dates, names, etc.’"},
            {"symptom": "Misses error status codes from raises.", "fix": "Force: ‘every raised HTTPException/error gets a response code in the spec.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["api-design-from-requirements", "code-snippet-with-tests-tdd"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["openapi", "api-spec"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why not use the framework's auto-generation?", "answer": "FastAPI's auto-gen is great but limited (doesn't capture error responses well, examples are bare). This prompt adds the human-quality bits."},
            {"question": "What about schema validation?", "answer": "Run output through `spectral` or `openapi-cli` to lint. AI gets 95% right; lint catches the last 5%."},
            {"question": "Should I commit AI-generated specs?", "answer": "Treat them as drafts. Review carefully. Commit only after running validation + adding manual sections (rate limits, auth scopes, etc.) the AI can't infer."},
        ],
        "meta_title": "OpenAPI Spec From a Handler Function — Prompt",
        "meta_description": "Generate OpenAPI 3.1 spec from a request handler. Paths, schemas, error responses, realistic examples. Marks inferred vs explicit.",
    },
    {
        "slug": "code-modernization-stepwise",
        "title": "Code Modernization Step-By-Step Plan",
        "tldr": "Given a legacy code module and a target modern stack, generates a stepwise migration plan: tests-first, smallest-safe-steps, with PR-sized commits and rollback strategy at each step. NOT a big-bang rewrite.",
        "category": "code-generation",
        "tags": ["modernization", "migration", "refactoring", "legacy"],
        "best_for_tags": ["legacy-systems", "framework-migrations", "tech-debt"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Migrate Python 2 to 3", "example": "Old codebase still on Py2; this prompt sequences the migration."},
            {"scenario": "Switch ORM (SQLAlchemy → Tortoise)", "example": "Multi-week migration with safety steps."},
            {"scenario": "Frontend framework switch (Angular → React)", "example": "Module-by-module migration plan, not big-bang."},
            {"scenario": "On-prem to cloud", "example": "Refactor to remove on-prem assumptions; plan with rollback points."},
        ],
        "when_not_to_use": "Skip for trivial code (just refactor). Skip when team explicitly wants big-bang (you'll be ignored). Skip when no tests exist — write tests FIRST (separate task).",
        "full_prompt": """You are planning a stepwise modernization of a code module. Smallest safe steps; tests first; rollback-friendly.

INPUT
- Current module (source code or summary): {current_module}
- Current stack (language version, framework, deps): {current_stack}
- Target stack: {target_stack}
- Existing tests (coverage % if known): {existing_tests}
- Constraints (deadline, can't break prod, frozen interfaces, etc.): {constraints}

OUTPUT

## 1. Migration philosophy
- Strategy: strangler-fig / parallel-write / incremental-rewrite / full-rewrite
- Rationale: why this approach for THIS situation
- Total estimated effort (in PR-weeks): N

## 2. Pre-migration: safety net
Before ANY migration, what must exist:
- Test coverage threshold: target % before starting (typically >70%)
- Observability: log what users hit, what code paths execute
- Rollback rehearsal: practice rolling back in staging

If safety net is missing, the plan starts with BUILDING THE SAFETY NET.

## 3. Steps (numbered PR-sized commits)

### Step N: <one-line description>
- **What changes**: specific code areas
- **Why this step now**: dependency ordering
- **Test that proves it works**: name the test or describe new tests added
- **Rollback if it fails**: revert the PR? Hide behind feature flag? Restore from backup?
- **Estimated PR size**: small (<200 LOC) / medium (<500) / large (<1000) — large should be split

Aim for 6-15 steps. More = unwieldy. Fewer = steps too large.

## 4. Risk register
3-5 things that could go wrong, ranked by likelihood × impact:
- "DB migration locks table for 10+ min on production size" → mitigation
- "New ORM has different transaction semantics" → mitigation
- "Library X has different default behavior re: nulls" → mitigation

## 5. Compatibility timeline
- When can old code be REMOVED (not just stop being added to)?
- When are users / downstream services migrated off old interface?
- What's the parallel-run period?

## 6. Reality check (skipped steps)
2-3 things people typically skip in modernizations that are mistakes:
- "Skipping the observability step because ‘we'll add it later’ — never happens"
- "Bundling DB migration with code migration in same PR — one fails, both roll back"
- "Not testing rollback path — fails when needed"

CRITICAL RULES
- Tests-first: don't migrate code that's not under test. Step 1-3 usually IS test addition.
- Strangler-fig preferred when interfaces are visible — new code lives alongside old, old gradually deletes.
- Big-bang ONLY when the module is tiny + isolated. Most cases: incremental.
- Each step is INDEPENDENTLY rollback-able. If step 7 breaks, you don't have to roll back 1-6.

MODULE
{current_module}

CURRENT: {current_stack}
TARGET: {target_stack}
CONSTRAINTS: {constraints}

Plan.""",
        "input_variables": [
            {"name": "current_module", "type": "string", "description": "Current module code or summary", "required": True, "example": "auth.py: ~600 LOC, handles JWT signing + session storage + 2FA. Uses PyJWT 1.x + Flask sessions + custom SMS gateway."},
            {"name": "current_stack", "type": "string", "description": "Current stack", "required": True, "example": "Python 3.8, Flask 1.x, PyJWT 1.7, custom SMS gateway"},
            {"name": "target_stack", "type": "string", "description": "Target stack", "required": True, "example": "Python 3.12, FastAPI, PyJWT 2.x, Twilio SDK"},
            {"name": "existing_tests", "type": "string", "description": "Existing test coverage", "required": True, "example": "30% coverage. Happy-path tests for login/logout. No tests for 2FA or session expiry."},
            {"name": "constraints", "type": "string", "description": "Constraints", "required": True, "example": "Auth is hot-path — zero downtime. Production has 10M sessions. PCI compliance — auth changes need security review per step."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: philosophy, safety net, 6-15 numbered steps with size/rollback, risk register, compatibility timeline, reality check.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on dependency ordering and rollback strategies."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can underestimate effort — re-pin honest PR-week estimates."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; risk register can be generic."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple migrations; thin on complex dependency ordering."},
        ],
        "variations": [
            {"label": "Database migration variant", "description": "For DB engine migrations.", "prompt_snippet": "Adjust: ‘DB migrations have unique constraints — dual-write phase, schema evolution, backfill, cutover, cleanup. Step structure reflects this.’"},
            {"label": "Cloud migration variant", "description": "On-prem to cloud.", "prompt_snippet": "Add: ‘include cloud-specific concerns: secrets management migration, networking, observability replacement, cost monitoring during parallel run.’"},
            {"label": "Frontend framework variant", "description": "Angular → React etc.", "prompt_snippet": "Adjust: ‘frontend module-by-module strangler-fig. Old and new live alongside in production. Route-by-route migration.’"},
        ],
        "failure_modes": [
            {"symptom": "Steps too large (PR > 1000 LOC).", "fix": "Re-pin PR size; ‘large’ steps must be split.’"},
            {"symptom": "Skips ‘safety net’ section.", "fix": "Force: ‘migration without tests is rewriting. Make the safety net the first phase.’"},
            {"symptom": "Rollback strategy missing per step.", "fix": "Add: ‘every step states how it rolls back. Without rollback plan, the step isn't ready.’"},
            {"symptom": "Reality-check section generic.", "fix": "Add: ‘reality check references SPECIFIC patterns teams skip in YOUR migration type.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["sql-schema-migration-safe", "test-suite-coverage-gap-finder", "senior-code-reviewer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["strangler-fig", "modernization"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "When is big-bang OK?", "answer": "Module is small (<2000 LOC), well-isolated (clean API boundary), and has thorough tests. Even then, parallel-run for a week before deleting old."},
            {"question": "How long does typical modernization take?", "answer": "1-3 PR-weeks per 1000 LOC of legacy code, depending on test coverage and complexity. Less if well-tested; more if behaviors are emergent."},
            {"question": "Can I parallelize steps?", "answer": "Yes — if steps touch independent areas. Dependency graph in section 3 should make parallelizable steps explicit."},
        ],
        "meta_title": "Code Modernization Step-By-Step Plan — Prompt",
        "meta_description": "Plan a stepwise legacy modernization: safety-net first, 6-15 PR-sized steps, rollback per step, risk register, compatibility timeline.",
    },
]
