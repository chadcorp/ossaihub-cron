"""Code generation prompt library — v2 authored (2026-05-14)."""

RECORDS = [
    {
        "slug": "senior-code-reviewer",
        "title": "Senior Code Reviewer (security + perf + style)",
        "category": "code-generation",
        "tldr": "Acts as a staff engineer reviewing a pull request. Flags security issues, performance regressions, race conditions, and style violations with line refs + suggested fixes.",
        "tags": ["code-review", "security", "performance"], "best_for_tags": ["pr-review", "security-audit"],
        "difficulty_tier": "intermediate", "featured": True,
        "full_prompt": (
            "You are a staff-level engineer reviewing a pull request. Be direct, specific, and prioritize. Don't list every nit — focus on what would matter in production.\n\n"
            "INPUTS:\n- diff: unified diff or file contents\n- language: primary language\n- context (optional): what the PR is supposed to do\n\n"
            "REVIEW IN THIS ORDER (stop early if no findings in a category):\n"
            "1. SECURITY: injection (SQL, command, HTML), auth bypass, secrets in code, unsafe deserialization, IDOR.\n"
            "2. PERFORMANCE REGRESSIONS: N+1 queries, O(n²) loops on hot paths, unnecessary allocations in tight loops, blocking I/O on event loop.\n"
            "3. CONCURRENCY: races, double-free, lock ordering, missing atomics, async without timeout.\n"
            "4. CORRECTNESS BUGS: off-by-one, null/undefined slips, untested error paths, broken contracts.\n"
            "5. STYLE / MAINTAINABILITY: only if quick to fix. Skip bikeshedding.\n\n"
            "FORMAT EACH FINDING:\n- Severity: 🔴 critical / 🟠 major / 🟡 minor\n- Location: file:line\n- Issue: 1-2 sentences\n- Fix: code snippet of the recommended change\n\n"
            "End with: SHIP / FIX FIRST / REJECT summary verdict.\n\nBegin."
        ),
        "input_variables": [
            {"name": "diff", "type": "string", "description": "Unified diff or file contents under review", "required": True, "example": "diff --git a/auth.py b/auth.py\n@@ -45,7 +45,9 @@\n+def login(req):\n+    user = User.query.filter_by(name=req.username).first()..."},
            {"name": "language", "type": "string", "description": "Primary language", "required": True, "example": "Python"},
            {"name": "context", "type": "string", "description": "What this PR does", "required": False, "example": "Adds username/password login. Will be deployed behind a feature flag."},
        ],
        "expected_output": {"format": "markdown", "sample": "## SECURITY\n🔴 **auth.py:48** — SQL injection via raw `username` interpolation\nFix:\n```python\nuser = User.query.filter_by(name=req.username).first()  # parameterized via ORM\n```\n\n## PERFORMANCE\n🟠 **auth.py:52** — Calling `bcrypt.check_password` inside a loop without rate limiting\n\n## VERDICT\nFIX FIRST — security issue must resolve before merge."},
        "use_cases": [
            {"scenario": "PR review automation", "example": "GitHub Action runs this on every PR; output posted as a review comment."},
            {"scenario": "Pre-merge gate", "example": "If any 🔴 finding, block merge until resolved."},
            {"scenario": "Junior dev coaching", "example": "Junior writes their own review, then compares with this output as a check."},
            {"scenario": "Security audit sprints", "example": "Run on the last 30 days of merged PRs to find latent issues."},
        ],
        "when_not_to_use": "Don't use for novel security-critical code without a human senior reviewer. The prompt finds known patterns; novel attacks need human creativity.",
        "few_shot_examples": [
            {
                "input": "Diff adds `db.exec(\"SELECT * FROM users WHERE id=\" + user_id)`. Language: Python.",
                "output": "🔴 **db.py:12** — SQL injection via string concatenation\n```python\ndb.exec('SELECT * FROM users WHERE id=?', (user_id,))\n```\nVERDICT: FIX FIRST",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best for combined security + perf reviews."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Use for high-stakes infra PRs."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong on style; sometimes over-flags minors."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable on standard patterns; weaker on novel framework idioms."},
        ],
        "variations": [
            {"label": "Security-only", "description": "Skip perf/style.", "prompt_snippet": "Only run section 1 (Security). Skip everything else."},
            {"label": "Diff-only mode", "description": "Don't read full file context.", "prompt_snippet": "Treat diff as the entire scope — don't request file context. Faster but misses cross-file issues."},
            {"label": "Auto-fix suggester", "description": "Generate inline patches.", "prompt_snippet": "For each 🔴 + 🟠, output a `git apply`-compatible patch block."},
        ],
        "failure_modes": [
            {"symptom": "Lists every minor style nit", "fix": "PROCEDURE step 5 has 'skip bikeshedding' rule; reinforce as 'minors only if fix is <5 lines'"},
            {"symptom": "Misses framework-specific security (Django CSRF, Rails strong params)", "fix": "Pass language + framework explicitly; prompt asks for framework-aware patterns"},
            {"symptom": "False positives on safe patterns", "fix": "Each finding needs concrete reasoning, not pattern-matching alone"},
            {"symptom": "Doesn't surface what the PR is supposed to DO", "fix": "Always ask for context input; if missing, infer from commit message before reviewing"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["refactor-to-pattern", "pytest-generator-from-source", "jest-generator-typescript"],
        "related_tool_slugs": ["github-copilot", "semgrep", "snyk"],
        "related_glossary_slugs": ["code-review", "static-analysis", "sql-injection"],
        "faq": [
            {"question": "Should this replace human reviewers?", "answer": "No — augment. The prompt finds known patterns fast; humans catch context."},
            {"question": "Can it review large diffs?", "answer": "Up to ~3000 lines reliably. For larger, split by directory or commit."},
            {"question": "Does it generate test cases?", "answer": "No — pair with the pytest-generator or jest-generator prompts."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Senior Code Reviewer Prompt — Security, Perf, Verdict",
        "meta_description": "Staff-engineer-level code review. Prioritized findings (critical/major/minor), inline fix snippets, ship/fix-first verdict.",
    },

    {
        "slug": "refactor-to-pattern",
        "title": "Refactor to Design Pattern (named, behavior-preserving)",
        "category": "code-generation",
        "tldr": "Refactor legacy code to a named design pattern (Strategy, Adapter, Observer, etc.) while preserving behavior. Output: full refactored code + diff + reasoning per change.",
        "tags": ["refactor", "patterns", "design"], "best_for_tags": ["refactoring", "design-patterns"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You refactor code to apply a named design pattern. Preserve all existing behavior — every public method signature, every observable side effect.\n\n"
            "INPUTS:\n- code: original code\n- target_pattern: name of pattern to apply (Strategy, Adapter, Observer, Factory, etc.)\n- language: target language\n- preserve_constraints (optional): public API parts that MUST not change\n\n"
            "PROCEDURE:\n1. Read the code; identify which sections fit the pattern.\n2. Refactor while preserving behavior — same inputs produce same outputs, same side effects, same exception types.\n3. List every public-API change explicitly. If unavoidable, document a migration shim.\n4. Output: the refactored code, a unified diff vs original, and a 'why this is now a Strategy/Adapter/etc.' explanation per major change.\n\n"
            "BEHAVIOR-PRESERVATION CHECKLIST (verify each):\n- Public method signatures unchanged (or migration shim provided)\n- Return types unchanged\n- Exception types thrown match original\n- Side effects (logs, DB writes, network calls) in same order\n- Performance not regressed by more than 10%\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "code", "type": "string", "description": "Original code to refactor", "required": True, "example": "class PaymentProcessor:\n    def process(self, type, amount): ..."},
            {"name": "target_pattern", "type": "string", "description": "Named pattern", "required": True, "example": "Strategy"},
            {"name": "language", "type": "string", "description": "Programming language", "required": True, "example": "Python"},
            {"name": "preserve_constraints", "type": "list[str]", "description": "Public API parts that must not change", "required": False, "example": "['PaymentProcessor.process(type, amount) signature', 'PaymentError exception']"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Refactored code\n```python\nclass PaymentStrategy(ABC):\n    def execute(self, amount): ...\nclass StripeStrategy(PaymentStrategy): ...\nclass PaymentProcessor:\n    def __init__(self): self._strategies = {'stripe': StripeStrategy(), ...}\n    def process(self, type, amount): return self._strategies[type].execute(amount)\n```\n\n## Why this is now a Strategy\nEach payment type was a giant if/elif in original; now each is a class. New types added without touching PaymentProcessor.\n\n## Behavior preservation\n✓ `process(type, amount)` signature unchanged\n✓ PaymentError still thrown on unsupported type\n⚠️ Side effect: log line wording changed ('processing stripe' → 'StripeStrategy.execute(...)')"},
        "use_cases": [
            {"scenario": "Legacy modernization", "example": "Old class with 12 conditionals → Strategy pattern with 12 classes."},
            {"scenario": "Codebase consistency", "example": "Team standardized on Observer for events; refactor existing pub-sub code to match."},
            {"scenario": "Test-isolation prep", "example": "Refactor to Adapter so external services can be mocked at the seam."},
            {"scenario": "Onboarding ramp", "example": "Junior dev needs to learn patterns; refactor real code together, with this prompt as the model."},
        ],
        "when_not_to_use": "Don't use to over-engineer simple code. If the conditional has 2-3 branches, don't introduce 3 classes. Patterns are for ≥5 branches or anticipated growth.",
        "few_shot_examples": [
            {
                "input": "code: `def render(report_type, data): if report_type=='pdf': ...; elif report_type=='csv': ...; elif report_type=='html': ...`. pattern: Strategy.",
                "output": "## Refactored\n```python\nclass ReportRenderer(ABC):\n    @abstractmethod\n    def render(self, data): ...\nclass PDFRenderer(ReportRenderer): ...\nclass CSVRenderer(ReportRenderer): ...\nclass HTMLRenderer(ReportRenderer): ...\n\nRENDERERS = {'pdf': PDFRenderer(), 'csv': CSVRenderer(), 'html': HTMLRenderer()}\ndef render(report_type, data): return RENDERERS[report_type].render(data)\n```\n\n## Behavior preserved\n`render('pdf', data)` works identically.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at behavior-preservation discipline."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Use for large-class refactors."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong at pattern application; verify side-effect preservation."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; expect to manually re-test."},
        ],
        "variations": [
            {"label": "Test-coverage retained", "description": "Output also the test changes.", "prompt_snippet": "Refactor must include test updates: existing tests should pass; add tests covering new abstraction seams."},
            {"label": "Incremental migration", "description": "Refactor in multiple commits.", "prompt_snippet": "Output as 3-5 commit-sized steps, each behavior-preserving, that incrementally arrive at the final pattern."},
            {"label": "Explain-only mode", "description": "Don't refactor, just explain how the pattern would apply.", "prompt_snippet": "Skip the refactored code; output only the pattern-fit analysis and migration plan. Useful for design-review discussions."},
        ],
        "failure_modes": [
            {"symptom": "Changes public method signatures", "fix": "Preservation checklist mandatory; document migration shim if change unavoidable"},
            {"symptom": "Introduces pattern where it doesn't fit (over-engineering)", "fix": "Reject if conditional <5 branches and no anticipated growth"},
            {"symptom": "Loses error types (raises generic Exception instead of original specific type)", "fix": "Behavior preservation includes exception types; verify each except path"},
            {"symptom": "Misses side-effect order changes", "fix": "Behavior preservation includes side-effect order; trace through with example inputs"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["senior-code-reviewer", "pytest-generator-from-source"],
        "related_tool_slugs": ["github-copilot", "cursor"],
        "related_glossary_slugs": ["design-patterns", "refactoring", "strategy-pattern"],
        "faq": [
            {"question": "Which patterns work best with this prompt?", "answer": "Strategy, Adapter, Observer, Factory, Decorator. Patterns with clear named structure work. Avoid for 'general cleanup' — too vague."},
            {"question": "How do I verify behavior preserved?", "answer": "Run your existing test suite. If you don't have tests, generate them first with the pytest-generator prompt, THEN refactor."},
            {"question": "Will it match my codebase's style?", "answer": "Pass 2-3 representative class examples as context; the prompt will match imports, naming conventions, error handling style."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Refactor to Design Pattern — Behavior-Preserving",
        "meta_description": "Refactor legacy code to Strategy/Adapter/Observer/Factory while preserving behavior. Full code, diff, reasoning, preservation checklist.",
    },

    {
        "slug": "pytest-generator-from-source",
        "title": "Pytest Generator from Source Code",
        "category": "code-generation",
        "tldr": "Read a Python module, generate pytest cases covering happy path + edge cases + error cases. Uses parametrize for thoroughness, fixtures for setup, marks for slow/integration.",
        "tags": ["pytest", "test-gen", "python"], "best_for_tags": ["test-coverage", "pytest"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You generate pytest test suites for Python code. Aim for ~80% line coverage on the first run; structure tests so they fail loudly with actionable messages.\n\n"
            "INPUTS:\n- source_code: the Python module being tested\n- testing_style (optional): unit / integration / both (default unit)\n- existing_tests (optional): tests already written, to avoid duplicating\n\n"
            "FOR EACH PUBLIC FUNCTION / METHOD, GENERATE:\n1. Happy-path test (1-2 cases): expected input → expected output\n2. Edge cases (2-4 cases): empty input, max/min boundary, unicode, None, very large\n3. Error cases (2-3 cases): expected exception types for invalid inputs\n4. Use `@pytest.mark.parametrize` when 3+ cases share structure\n5. Use fixtures for shared setup (don't repeat)\n6. Mark slow tests `@pytest.mark.slow`, integration tests `@pytest.mark.integration`\n\n"
            "TEST QUALITY RULES:\n- One assert per test (or assert grouped)\n- Test name describes the case ('test_<func>_<scenario>_<expected>')\n- Use `assert x == y, f\"context\"` so failures show inputs\n- Mock external dependencies (DB, HTTP) — don't make tests flaky\n\n"
            "OUTPUT: full pytest file + 1-line coverage estimate + list of any cases you couldn't test (e.g., requires external service).\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "source_code", "type": "string", "description": "Python module to test", "required": True, "example": "def calculate_discount(price, percent): if percent < 0 or percent > 100: raise ValueError; return price * (1 - percent / 100)"},
            {"name": "testing_style", "type": "string", "description": "unit | integration | both", "required": False, "example": "unit"},
            {"name": "existing_tests", "type": "string", "description": "Existing test file content (don't duplicate)", "required": False, "example": "def test_calculate_discount_happy(): assert calculate_discount(100, 10) == 90"},
        ],
        "expected_output": {"format": "code", "sample": "import pytest\nfrom pricing import calculate_discount\n\nclass TestCalculateDiscount:\n    @pytest.mark.parametrize('price,percent,expected', [(100, 10, 90.0), (50, 0, 50.0), (200, 100, 0.0), (99.99, 50, 49.995)])\n    def test_calculate_discount_valid(self, price, percent, expected):\n        assert calculate_discount(price, percent) == pytest.approx(expected), f'price={price} pct={percent}'\n\n    @pytest.mark.parametrize('percent', [-1, 101, 150])\n    def test_calculate_discount_invalid_percent_raises(self, percent):\n        with pytest.raises(ValueError):\n            calculate_discount(100, percent)\n\n    def test_calculate_discount_zero_price(self):\n        assert calculate_discount(0, 50) == 0\n\n# Coverage estimate: ~95%\n# Cases not testable: none — pure function"},
        "use_cases": [
            {"scenario": "Brownfield test bootstrapping", "example": "Module with 0% coverage; this prompt produces v1 tests for review."},
            {"scenario": "Pre-refactor safety net", "example": "Generate tests, then refactor; tests must still pass."},
            {"scenario": "Code-coverage gap filling", "example": "Coverage report shows uncovered branches; pass those to the prompt for targeted tests."},
            {"scenario": "TDD-from-spec", "example": "Pass the spec/docstring; prompt generates tests that the implementation must pass."},
        ],
        "when_not_to_use": "Don't use as a substitute for thinking about edge cases — the prompt catches common ones, misses domain-specific. Always review.",
        "few_shot_examples": [
            {
                "input": "code: `def parse_date(s): return datetime.strptime(s, '%Y-%m-%d')`",
                "output": "@pytest.mark.parametrize('s,expected', [('2026-05-14', datetime(2026,5,14)), ('2000-01-01', datetime(2000,1,1))])\ndef test_parse_date_valid(s, expected):\n    assert parse_date(s) == expected\n\n@pytest.mark.parametrize('s', ['', 'not-a-date', '2026/05/14', '14-05-2026', '2026-13-01'])\ndef test_parse_date_invalid_raises(s):\n    with pytest.raises(ValueError):\n        parse_date(s)",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at edge-case coverage."},
            {"model": "gpt-5", "compatibility": "excellent", "notes": "Strong on parametrize structure."},
            {"model": "claude-haiku-4-5", "compatibility": "good", "notes": "Cheap for bulk generation across many modules."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; expect to add 1-2 cases manually."},
        ],
        "variations": [
            {"label": "Property-based mode", "description": "Use hypothesis for property tests.", "prompt_snippet": "Use hypothesis (st.integers, st.text) for ranged inputs. Property: round-trip identity, idempotence, etc."},
            {"label": "Integration tests", "description": "Test with real dependencies.", "prompt_snippet": "Skip mocks. Mark every test @pytest.mark.integration. Assume real DB/HTTP available via fixtures."},
            {"label": "Coverage-targeted mode", "description": "Hit uncovered branches.", "prompt_snippet": "Pass uncovered_lines as input. Generate tests that specifically exercise those lines."},
        ],
        "failure_modes": [
            {"symptom": "Misses important edge case (negative numbers, unicode, None)", "fix": "Edge case checklist mandatory; reject test files lacking boundary cases"},
            {"symptom": "Tests with multiple unrelated asserts", "fix": "One concern per test; split when in doubt"},
            {"symptom": "Mocks that hide real bugs", "fix": "Mock only EXTERNAL dependencies (network, DB, filesystem); never mock the unit under test"},
            {"symptom": "Test names don't describe the case", "fix": "Naming convention: test_<func>_<scenario>_<expected>; reject 'test_1', 'test_works'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-haiku-4-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["jest-generator-typescript", "senior-code-reviewer", "refactor-to-pattern"],
        "related_tool_slugs": ["pytest", "hypothesis", "coverage-py"],
        "related_glossary_slugs": ["pytest", "tdd", "parametrize"],
        "faq": [
            {"question": "How much coverage will I get?", "answer": "60-85% on a first pass for typical pure-function code. <50% for complex stateful code (needs more context)."},
            {"question": "Can it figure out my custom fixtures?", "answer": "Yes if you pass conftest.py in existing_tests. Otherwise it'll create new ones (which you can merge)."},
            {"question": "Will it generate flaky tests?", "answer": "Mocks external deps by default to avoid flakiness. If you want real dependencies, use the integration-mode variation."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Pytest Generator from Source — Edge Cases + Parametrize",
        "meta_description": "Generate pytest tests covering happy path, edge cases, error cases. Parametrize, fixtures, marks, ~80% coverage v1.",
    },

    {
        "slug": "sql-query-from-natural-language",
        "title": "SQL Query from Natural Language (schema-aware)",
        "category": "code-generation",
        "tldr": "Generate SQL from natural language given a schema. Distinguishes ambiguous questions, surfaces likely interpretations, returns parameterized + explained queries.",
        "tags": ["sql", "nl2sql", "data-query"], "best_for_tags": ["sql-generation", "analytics", "self-service"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You translate natural-language questions to SQL given a schema. Be transparent about ambiguity — many questions have 2-3 valid interpretations.\n\n"
            "INPUTS:\n- schema: table definitions with column names + types + foreign keys\n- question: natural-language question\n- dialect: postgres | mysql | sqlite | bigquery | snowflake\n- known_filters (optional): e.g., 'tenant_id is always 42'\n\n"
            "PROCEDURE:\n1. Parse the question for: entity (which tables), metric (count/sum/avg/etc.), filter (when/where conditions), grouping (per X), ordering.\n2. Identify AMBIGUITIES: 'recent' = 7d? 30d? 'user' = signup row? row+active flag? List them.\n3. Pick the most likely interpretation; produce SQL.\n4. If ambiguous: produce the primary SQL + a 1-line note 'or interpreted as: <alternative>'.\n5. Use parameters not interpolation. Include LIMIT 100 on exploratory queries; remove only when user asks for full results.\n6. Add a 1-line natural-language summary of what the SQL does (sanity check the user can verify).\n\n"
            "OUTPUT: SQL block + ambiguity note + result summary in 1 line.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "schema", "type": "string", "description": "Table definitions", "required": True, "example": "users(id, email, created_at, tenant_id); orders(id, user_id FK users, amount, created_at, status)"},
            {"name": "question", "type": "string", "description": "Natural-language question", "required": True, "example": "How much revenue did our 10 biggest customers generate last quarter?"},
            {"name": "dialect", "type": "string", "description": "SQL dialect", "required": True, "example": "postgres"},
            {"name": "known_filters", "type": "list[str]", "description": "Default filters", "required": False, "example": "['status != deleted']"},
        ],
        "expected_output": {"format": "code", "sample": "-- Top 10 customers by revenue, last quarter\nSELECT u.email, SUM(o.amount) AS revenue\nFROM users u\nJOIN orders o ON o.user_id = u.id\nWHERE o.created_at >= date_trunc('quarter', NOW()) - INTERVAL '3 months'\n  AND o.created_at < date_trunc('quarter', NOW())\n  AND o.status != 'deleted'\nGROUP BY u.id, u.email\nORDER BY revenue DESC\nLIMIT 10;\n-- Ambiguity: 'last quarter' = previous full calendar quarter (not last 3 months rolling). Switch if needed.\n-- Returns: 10 rows of (email, revenue)."},
        "use_cases": [
            {"scenario": "Self-serve analytics", "example": "PM asks a question in chat; this prompt turns it into SQL for review before running on prod."},
            {"scenario": "Junior analyst training", "example": "Junior writes their SQL; prompt's output is the check."},
            {"scenario": "Data team triage", "example": "Slack-bot intercepts data requests; this prompt produces a draft + asks for confirmation before executing."},
            {"scenario": "Migration to new BI tool", "example": "Translate questions from old tool's saved-query library to fresh SQL in new dialect."},
        ],
        "when_not_to_use": "Don't run output on production without review — even good SQL can be expensive or wrong on edge data. Always preview LIMIT first.",
        "few_shot_examples": [
            {
                "input": "schema: users(id, signup_date). question: 'How many users signed up this week?'",
                "output": "SELECT COUNT(*) FROM users WHERE signup_date >= date_trunc('week', NOW());\n-- Ambiguity: 'this week' = current calendar week (Mon-Sun). Alt: last 7 days rolling.\n-- Returns: 1 row, count of signups this week.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at surfacing ambiguity."},
            {"model": "gpt-5", "compatibility": "excellent", "notes": "Reliable across dialects."},
            {"model": "claude-haiku-4-5", "compatibility": "good", "notes": "Cheap for routine queries."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable for simple JOINs; complex CTEs may fail."},
        ],
        "variations": [
            {"label": "Explain-only", "description": "Translate question to SQL plan, no execution.", "prompt_snippet": "Output: query plan + estimated cost (LOW/MED/HIGH based on table sizes). Useful for cost-controlled environments."},
            {"label": "Multi-dialect", "description": "Generate the same query for 2-3 dialects.", "prompt_snippet": "Output 1 query per dialect in tabbed format. Highlight differences (e.g., date_trunc vs DATE_TRUNC)."},
            {"label": "Strict mode", "description": "Refuse to execute if ambiguous.", "prompt_snippet": "If ambiguity detected, output 'CLARIFY: <question>' instead of SQL. Don't pick an interpretation."},
        ],
        "failure_modes": [
            {"symptom": "Picks wrong interpretation silently", "fix": "Ambiguity must be surfaced; if 2+ valid readings, both shown"},
            {"symptom": "Uses string interpolation instead of params", "fix": "Always parameterize; never embed user input in WHERE strings"},
            {"symptom": "Missing LIMIT on exploratory query", "fix": "Default LIMIT 100; only remove on explicit user request"},
            {"symptom": "Schema confusion (joins wrong tables)", "fix": "Always cite the foreign key path in comments; user verifies"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-haiku-4-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["a-b-test-result-interpreter", "metric-anomaly-explainer"],
        "related_tool_slugs": ["dbt", "metabase", "querybook"],
        "related_glossary_slugs": ["sql", "nl2sql", "ambiguity-resolution"],
        "faq": [
            {"question": "Can I trust the SQL on production?", "answer": "Review every query before running. The prompt is 95% accurate on syntactic correctness, less on business semantics."},
            {"question": "What if my schema is huge (200+ tables)?", "answer": "Pass only the relevant subset. Auto-pruning to relevant tables is a separate prompt task."},
            {"question": "Can it write CTEs and window functions?", "answer": "Yes — Claude Sonnet 4.5 and GPT-5 both handle complex CTEs reliably. Llama is weaker here."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "SQL from Natural Language Prompt — Schema-Aware, Ambiguity-Honest",
        "meta_description": "Translate NL questions to parameterized SQL with explicit ambiguity surfacing, LIMIT defaults, multi-dialect support.",
    },

    {
        "slug": "jest-generator-typescript",
        "title": "Jest Test Generator (TypeScript, with mocks)",
        "category": "code-generation",
        "tldr": "Generate Jest test suites for TypeScript code. Type-aware mocks via jest.Mocked<T>, describe/it nesting, beforeEach for setup, snapshots only where appropriate.",
        "tags": ["jest", "typescript", "test-gen"], "best_for_tags": ["test-coverage", "jest", "typescript"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You generate Jest test suites for TypeScript. Aim for ~80% coverage on first pass. Type-aware everything; don't use `any` in tests.\n\n"
            "INPUTS:\n- source: TypeScript module\n- testing_style: unit | integration\n- existing_tests (optional): avoid duplicating\n- mock_strategy: jest.mock | __mocks__ folder | manual (default jest.mock)\n\n"
            "STRUCTURE:\n- One describe per public function/method\n- Nested describes for grouped scenarios (e.g., 'when authenticated')\n- beforeEach for shared setup\n- afterEach if cleanup needed\n- Type mocks with jest.Mocked<T> or as jest.MockedFunction<typeof fn>\n\n"
            "TEST CASES (per function):\n1. Happy path: 1-2\n2. Edge cases: 2-4 (boundary, empty, unicode, null/undefined)\n3. Error paths: 2-3 (expected thrown errors)\n4. Async behavior: resolve/reject paths if Promise-returning\n\n"
            "ANTI-PATTERNS TO AVOID:\n- Snapshot tests for non-UI output (brittle)\n- Mocking the unit under test\n- Testing implementation details (private methods)\n- Using `any` type\n\n"
            "OUTPUT: full .test.ts file + 1-line coverage estimate.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "source", "type": "string", "description": "TypeScript module to test", "required": True, "example": "export async function fetchUser(id: string): Promise<User> { ... }"},
            {"name": "testing_style", "type": "string", "description": "unit | integration", "required": False, "example": "unit"},
            {"name": "existing_tests", "type": "string", "description": "Existing tests to avoid duplicating", "required": False, "example": ""},
            {"name": "mock_strategy", "type": "string", "description": "jest.mock | __mocks__ | manual", "required": False, "example": "jest.mock"},
        ],
        "expected_output": {"format": "code", "sample": "import { fetchUser } from './user';\nimport { db } from './db';\njest.mock('./db');\nconst mockDb = db as jest.Mocked<typeof db>;\n\ndescribe('fetchUser', () => {\n  beforeEach(() => jest.clearAllMocks());\n\n  describe('when user exists', () => {\n    it('returns the user record', async () => {\n      mockDb.query.mockResolvedValue([{ id: '1', name: 'Alice' }]);\n      await expect(fetchUser('1')).resolves.toEqual({ id: '1', name: 'Alice' });\n    });\n  });\n\n  describe('when user does not exist', () => {\n    it('throws NotFoundError', async () => {\n      mockDb.query.mockResolvedValue([]);\n      await expect(fetchUser('999')).rejects.toThrow(NotFoundError);\n    });\n  });\n});\n// Coverage estimate: ~90%"},
        "use_cases": [
            {"scenario": "Brownfield TypeScript test bootstrapping", "example": "Module with 0% coverage; v1 tests for review."},
            {"scenario": "React component testing (with RTL)", "example": "Pair with React Testing Library prompt for component tests; this one handles utilities."},
            {"scenario": "API contract testing", "example": "Generate tests that mock fetch/axios and verify request shapes."},
            {"scenario": "CI gate", "example": "Run on every PR to surface missing tests for new code."},
        ],
        "when_not_to_use": "Don't use for React component rendering — different prompt. Also skip for performance benchmarks (Jest is wrong tool).",
        "few_shot_examples": [
            {
                "input": "source: `export function slugify(s: string): string { return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''); }`",
                "output": "describe('slugify', () => {\n  it.each([\n    ['Hello World', 'hello-world'],\n    ['  spaces  ', 'spaces'],\n    ['café', 'caf'],  // Latin-1 not preserved\n    ['', ''],\n    ['---', ''],\n  ])('slugify(%j) → %j', (input, expected) => {\n    expect(slugify(input)).toBe(expected);\n  });\n});",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at type-safe mocks."},
            {"model": "gpt-5", "compatibility": "excellent", "notes": "Strong at describe/it nesting."},
            {"model": "claude-haiku-4-5", "compatibility": "good", "notes": "Cheap for routine modules."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; type strictness occasionally slips."},
        ],
        "variations": [
            {"label": "Vitest mode", "description": "Use Vitest instead of Jest.", "prompt_snippet": "Replace `jest.mock` with `vi.mock`, `jest.fn()` with `vi.fn()`, etc. Output Vitest-compatible test file."},
            {"label": "Testing Library mode", "description": "For React components.", "prompt_snippet": "Pair source with React Testing Library: use `render`, `screen`, `userEvent`. Test by user-observable behavior, not implementation."},
            {"label": "Coverage-gap targeted", "description": "Hit specific uncovered branches.", "prompt_snippet": "Pass `uncovered_lines` from coverage report; generate only tests for those lines."},
        ],
        "failure_modes": [
            {"symptom": "Uses `any` in mock types", "fix": "Type-safety rule: always use jest.Mocked<T> or jest.MockedFunction<typeof fn>"},
            {"symptom": "Snapshot tests for arbitrary objects", "fix": "Snapshots only for UI renders; for objects use explicit assertions"},
            {"symptom": "Forgets to reset mocks between tests", "fix": "Always include beforeEach(() => jest.clearAllMocks()) at describe level"},
            {"symptom": "Tests pass even when implementation is buggy", "fix": "Add 1-2 'should fail' cases to verify the tests actually catch bugs"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-haiku-4-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["pytest-generator-from-source", "senior-code-reviewer"],
        "related_tool_slugs": ["jest", "vitest", "testing-library"],
        "related_glossary_slugs": ["jest", "typescript", "mocking"],
        "faq": [
            {"question": "Jest or Vitest?", "answer": "Vitest if you're on Vite. Jest if you're on Webpack/Next.js or migrating older code. Use the Vitest-mode variation if needed."},
            {"question": "Should I use snapshots?", "answer": "Only for React components and stable visual output. Object snapshots break too easily."},
            {"question": "How do I test code that calls external APIs?", "answer": "Use jest.mock for fetch/axios. For integration tests, use msw (Mock Service Worker) or nock."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Jest Test Generator (TypeScript) — Type-Safe Mocks",
        "meta_description": "Generate Jest tests for TypeScript with jest.Mocked<T>, beforeEach setup, describe/it nesting. No `any`, no brittle snapshots.",
    },
]
