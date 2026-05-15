"""Testing starters — batch 2: LLM unit tests, snapshot tests, eval-as-test, integration."""

RECORDS = [
    {
        "slug": "llm-unit-test-with-mocks",
        "title": "LLM Unit Test With Mocks (Fast + Deterministic)",
        "tldr": "Test code that calls LLMs without ACTUALLY calling LLMs. Mock the SDK; assert your code's request shape; verify response handling. CI-fast, deterministic.",
        "category": "testing",
        "language": "python",
        "framework": "pytest + unittest.mock",
        "tags": ["pytest", "mock", "unit-test", "llm"],
        "best_for_tags": ["ci-speed", "deterministic-tests", "tdd"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Most of your test suite. LLM unit tests = mock the LLM, test YOUR code. Save real LLM calls for end-to-end / eval tests run nightly.",
        "when_not_to_use": "Skip for evaluation (need real LLM behavior). Skip for testing prompt quality (use a separate eval suite).",
        "quick_start": "pip install pytest && pytest tests/",
        "full_code": '''"""Unit-test LLM code with mocked SDK calls."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from openai import OpenAI


# ----------------- CODE UNDER TEST -----------------

def classify_ticket(client: OpenAI, message: str) -> dict:
    """The function we want to test."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Classify the support ticket. Output JSON."},
            {"role": "user", "content": message},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    import json
    return json.loads(response.choices[0].message.content)


# ----------------- MOCK FIXTURE -----------------

@pytest.fixture
def mock_openai():
    """Returns a mock OpenAI client that returns canned responses."""
    client = MagicMock(spec=OpenAI)
    return client


def make_mock_response(content: str):
    """Helper to construct a mock chat.completions.create return."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = content
    mock_resp.usage.prompt_tokens = 100
    mock_resp.usage.completion_tokens = 50
    return mock_resp


# ----------------- TESTS: REQUEST SHAPE -----------------

def test_classify_uses_correct_model(mock_openai):
    """Verify we call the cheap model."""
    mock_openai.chat.completions.create.return_value = make_mock_response(
        '{"category": "billing", "priority": "high"}'
    )
    classify_ticket(mock_openai, "I want a refund")

    call_args = mock_openai.chat.completions.create.call_args
    assert call_args.kwargs["model"] == "gpt-4o-mini", \\
        "Should use cheap model for classification"


def test_classify_temperature_is_zero(mock_openai):
    """Determinism: temperature=0 always."""
    mock_openai.chat.completions.create.return_value = make_mock_response(
        '{"category": "billing", "priority": "high"}'
    )
    classify_ticket(mock_openai, "test")

    call_args = mock_openai.chat.completions.create.call_args
    assert call_args.kwargs["temperature"] == 0


def test_classify_uses_json_mode(mock_openai):
    """Force JSON output."""
    mock_openai.chat.completions.create.return_value = make_mock_response(
        '{"category": "billing", "priority": "high"}'
    )
    classify_ticket(mock_openai, "test")

    call_args = mock_openai.chat.completions.create.call_args
    assert call_args.kwargs["response_format"] == {"type": "json_object"}


# ----------------- TESTS: RESPONSE HANDLING -----------------

def test_classify_returns_parsed_json(mock_openai):
    mock_openai.chat.completions.create.return_value = make_mock_response(
        '{"category": "billing", "priority": "high"}'
    )
    result = classify_ticket(mock_openai, "I want a refund")
    assert result == {"category": "billing", "priority": "high"}


def test_classify_raises_on_malformed_json(mock_openai):
    import json
    mock_openai.chat.completions.create.return_value = make_mock_response("not valid json")
    with pytest.raises(json.JSONDecodeError):
        classify_ticket(mock_openai, "test")


# ----------------- TESTS: ERROR HANDLING -----------------

def test_classify_propagates_api_errors(mock_openai):
    """If OpenAI errors, our code re-raises (or handles, depending on design)."""
    from openai import APIError
    mock_openai.chat.completions.create.side_effect = APIError("rate limited", request=None, body=None)
    with pytest.raises(APIError):
        classify_ticket(mock_openai, "test")


# ----------------- PARAMETRIZED TESTS -----------------

@pytest.mark.parametrize("message,expected_category", [
    ("I was charged twice", "billing"),
    ("Login is broken", "technical"),
    ("Hi, just saying hello", "general"),
])
def test_classify_routes_correctly(mock_openai, message, expected_category):
    """Mock different responses for different inputs."""
    mock_openai.chat.completions.create.return_value = make_mock_response(
        f'{{"category": "{expected_category}", "priority": "low"}}'
    )
    result = classify_ticket(mock_openai, message)
    assert result["category"] == expected_category


# ----------------- USING patch INSTEAD OF FIXTURE -----------------

@patch("openai.OpenAI")
def test_with_patch(mock_class):
    """Alternative pattern: patch the class itself."""
    instance = mock_class.return_value
    instance.chat.completions.create.return_value = make_mock_response('{"category": "billing"}')

    client = OpenAI()
    result = classify_ticket(client, "test")
    assert result["category"] == "billing"
''',
        "dependencies": [
            {"name": "pytest", "version": ">=7.0", "purpose": "Test runner"},
            {"name": "openai", "version": ">=1.40", "purpose": "Type the mock against real SDK"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install pytest openai",
            "Save tests/test_classify.py",
            "pytest -v",
            "All tests pass without OPENAI_API_KEY set (mocked)",
        ],
        "variations": [
            {"label": "VCR-py for recorded responses", "description": "Record-then-replay HTTP.", "code_snippet": "# pip install vcrpy; @pytest.fixture(autouse=True) def vcr_cassette(): with vcr.use_cassette('cassettes/...'): yield. Records first call; replays after."},
            {"label": "respx for HTTPX mocking", "description": "Mock at HTTP layer.", "code_snippet": "# pip install respx; @respx.mock def test(): respx.post('...').mock(return_value=httpx.Response(200, json={...})). Tests entire stack."},
            {"label": "Snapshot testing with syrupy", "description": "Lock LLM outputs.", "code_snippet": "# pip install syrupy; def test_output(snapshot): assert classify(...) == snapshot. First run records; subsequent runs assert match."},
        ],
        "common_errors": [
            {"error_text": "Mock not being applied", "cause": "Patched wrong module.", "fix_snippet": "Patch where the import happens, not where it's defined. If your_module does 'from openai import OpenAI', patch 'your_module.OpenAI'."},
            {"error_text": "Real API call slipping through", "cause": "Test uses real client instance.", "fix_snippet": "Inject the client (dependency injection) rather than instantiate inside function. Pass mock_openai as parameter."},
            {"error_text": "AttributeError on mock", "cause": "Mock doesn't have the right structure.", "fix_snippet": "Use MagicMock(spec=OpenAI) to enforce structure. Or build the nested mock chain explicitly (mock.chat.completions.create)."},
            {"error_text": "Tests pass locally, fail in CI", "cause": "Hidden env dependency.", "fix_snippet": "Mock everything: OPENAI_API_KEY env, network calls, time. Make sure tests run with no env vars set."},
        ],
        "production_checklist": [
            "Inject LLM clients via DI (constructor / parameter); don't instantiate inside functions.",
            "Test REQUEST SHAPE separately from response handling.",
            "Use parametrize for many inputs / scenarios.",
            "Cover error paths (rate limits, malformed JSON, timeouts).",
            "Run unit tests on every commit; eval tests nightly.",
            "Use respx / VCR for end-to-end scenarios with recorded API responses.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["pytest==7.0", "openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["pytest", "openai"],
        "related_glossary_slugs": ["unit-testing", "mocking"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Unit test LLM behavior?", "answer": "No — that's evaluation. Unit tests verify YOUR code calls the LLM correctly + handles responses. Evaluating prompt quality is a separate suite (Ragas, Promptfoo, etc.)."},
            {"question": "Mock vs VCR vs respx?", "answer": "Mock: fastest, no real call ever. VCR: record-replay; tests integration but stays deterministic. respx: HTTP-level mock; tests SDK behavior. Use mock by default; VCR/respx for integration coverage."},
            {"question": "How to test streaming?", "answer": "Mock with an iterable of mock chunks. Each chunk has .choices[0].delta.content. Iterate and assert concatenated output matches expected."},
            {"question": "Test tool-calling code?", "answer": "Yes — mock the response with tool_calls. Verify your code calls the right tool functions with right args. Then mock tool result and verify next iteration."},
        ],
        "github_url": "",
        "meta_title": "LLM Unit Test With Mocks Starter",
        "meta_description": "Unit test LLM code without calling real APIs. Mock SDK responses, verify request shape, test error paths. CI-fast.",
    },
    {
        "slug": "llm-snapshot-tests-with-syrupy",
        "title": "LLM Snapshot Tests With Syrupy",
        "tldr": "Snapshot tests for LLM outputs: lock the prompt → expected response. On regression (model update, prompt tweak), syrupy diffs the new output against the snapshot. CI-friendly.",
        "category": "testing",
        "language": "python",
        "framework": "syrupy + pytest",
        "tags": ["snapshot", "syrupy", "regression", "testing"],
        "best_for_tags": ["prompt-engineers", "regression-prevention", "deterministic-prompts"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Production prompts where you've achieved 'this is the output we want'. Snapshot tests lock that output; ANY deviation fails CI. Catches silent prompt regressions.",
        "when_not_to_use": "Skip for creative / non-deterministic prompts (temperature > 0). Skip when expected output legitimately changes frequently.",
        "quick_start": "pip install pytest syrupy && pytest --snapshot-update",
        "full_code": '''"""Snapshot tests for LLM outputs using syrupy."""
from __future__ import annotations

import pytest
from syrupy.assertion import SnapshotAssertion


# ----------------- CODE UNDER TEST -----------------

from openai import OpenAI

client = OpenAI()


def extract_invoice(email_text: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",  # Pin specific version for stable snapshots
        messages=[
            {"role": "system", "content": "Extract invoice data. Output JSON: {invoice_number, amount_usd, due_date, line_items}"},
            {"role": "user", "content": email_text},
        ],
        response_format={"type": "json_object"},
        temperature=0,
        seed=42,  # Determinism (best effort)
    )
    import json
    return json.loads(response.choices[0].message.content)


# ----------------- SNAPSHOT TESTS -----------------

# Pinned inputs → snapshot files in __snapshots__/ folder

SAMPLE_EMAILS = [
    "Invoice #INV-2024-0042. Due: 2024-10-15. Total: $1,250.00. Setup fee: $1,000. Hosting: $250.",
    "Hi, please find attached invoice 2024-Q3-007 for $5,432. Net 30, due Nov 1st 2024. Services: Strategy ($3,000), Implementation ($2,432).",
]


@pytest.mark.parametrize("email_text", SAMPLE_EMAILS)
def test_extract_invoice_snapshot(email_text: str, snapshot: SnapshotAssertion):
    """Assert extraction matches recorded snapshot."""
    result = extract_invoice(email_text)
    assert result == snapshot


# ----------------- CUSTOM SERIALIZER (sanitize timestamps, etc.) -----------------

# In a conftest.py:
CONFTEST = """
from syrupy.extensions.json import JSONSnapshotExtension

@pytest.fixture
def snapshot_json(snapshot):
    return snapshot.use_extension(JSONSnapshotExtension)

# Then in test: assert result == snapshot_json
"""


# ----------------- WORKFLOW -----------------

WORKFLOW = """
# First run: record snapshots
pytest --snapshot-update

# Subsequent runs: assert against snapshots
pytest

# If you change the prompt or model and EXPECT new output:
pytest --snapshot-update
# Review the .ambr files in __snapshots__/ for diffs
# Commit if they match what you expect

# CI: detect unintentional changes
pytest                    # fails if snapshots differ
"""


# ----------------- REGRESSION DETECTION -----------------

# After model update or prompt tweak:
# 1. Run tests; they fail on snapshot mismatch
# 2. Inspect git diff of __snapshots__/*.ambr — is the new output BETTER?
# 3. If yes: commit new snapshots + describe change in PR
# 4. If no: prompt regression; fix before merging


# ----------------- ADVANCED: Filter unstable fields -----------------

from syrupy.filters import props


def test_extract_skip_timestamps(snapshot):
    """Snapshot but ignore timestamp fields (often legitimately vary)."""
    result = extract_invoice(SAMPLE_EMAILS[0])
    # Add 'extracted_at' or similar transient fields
    result["_extracted_at"] = "now"
    # Compare excluding _extracted_at
    assert result == snapshot(exclude=props("_extracted_at"))
''',
        "dependencies": [
            {"name": "syrupy", "version": ">=4.0", "purpose": "Snapshot assertions"},
            {"name": "pytest", "version": ">=7.0", "purpose": "Test runner"},
            {"name": "openai", "version": ">=1.40", "purpose": "LLM under test"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "For real calls (snapshot mode)", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install syrupy pytest openai",
            "Save tests; run pytest --snapshot-update to RECORD",
            "Commit snapshots (.ambr files in __snapshots__/)",
            "Future runs: pytest (asserts against snapshots)",
            "On real change: review diff + update snapshots",
        ],
        "variations": [
            {"label": "Single-line snapshots (.amber-single)", "description": "One file per test.", "code_snippet": "# Default behavior; useful for grepping. Default extension is AmberSnapshotExtension."},
            {"label": "JSON snapshots", "description": "Human-readable for structured output.", "code_snippet": "from syrupy.extensions.json import JSONSnapshotExtension\\nassert result == snapshot.use_extension(JSONSnapshotExtension)"},
            {"label": "Image / binary snapshots", "description": "For multimodal outputs.", "code_snippet": "from syrupy.extensions.image import PNGImageSnapshotExtension\\n# Useful for testing generated images / charts"},
        ],
        "common_errors": [
            {"error_text": "Snapshots vary across runs", "cause": "Temperature > 0 or seed not pinned.", "fix_snippet": "Set temperature=0 AND seed= (for OpenAI 4o). Even then, expect occasional flakes — pin model version too."},
            {"error_text": "Snapshot file shows whole nested structure", "cause": "Default AMBR format.", "fix_snippet": "Use JSONSnapshotExtension for cleaner diffs. Or use custom serializer that focuses on stable fields."},
            {"error_text": "Test passes locally, fails in CI", "cause": "Locale / time-zone in output.", "fix_snippet": "Normalize transient fields. Use exclude=props('_timestamp') to skip them. Or scrub before assert."},
            {"error_text": "Hundreds of stale snapshots", "cause": "Tests removed but snapshots remain.", "fix_snippet": "pytest --snapshot-update prunes orphan snapshots. Run periodically to clean up."},
        ],
        "production_checklist": [
            "Pin exact model version (no -latest).",
            "Set temperature=0 + seed for determinism.",
            "Review snapshot diffs CAREFULLY when updating (PR review).",
            "Run snapshot tests only on prompt/model changes (heavy LLM cost on every commit).",
            "Combine with unit tests (fast) for tighter loop.",
            "Document when snapshots WERE deliberately updated in PR.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-2024-08-06"],
            "library_versions": ["syrupy==4.0", "openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["syrupy", "pytest"],
        "related_glossary_slugs": ["snapshot-testing", "regression-prevention"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How is this different from unit tests?", "answer": "Unit tests verify YOUR code is correct given mocked LLM. Snapshots verify the LLM OUTPUT is what you expect given a fixed prompt. Both are valuable; they catch different things."},
            {"question": "What about non-deterministic prompts?", "answer": "Snapshot tests don't work well at temperature > 0. For non-deterministic prompts, use eval frameworks (Ragas, DeepEval) that measure properties not exact equality."},
            {"question": "Cost?", "answer": "Each snapshot run = real LLM call. For 10 snapshot tests: $0.01-0.05 per run. Cheap, but runs on every CI invocation. Mitigate: snapshot tests only on prompt/model changes, not every PR."},
            {"question": "Snapshot file format?", "answer": "AMBR (default), JSON, custom. AMBR is human-readable + git-friendly. Pick based on output shape. JSON is cleaner for structured data."},
        ],
        "github_url": "https://github.com/syrupy-project/syrupy",
        "meta_title": "LLM Snapshot Tests With Syrupy Starter",
        "meta_description": "Snapshot tests for LLM outputs: pin prompt → expected response. Catch silent regressions on model/prompt changes.",
    },
    {
        "slug": "llm-integration-test-with-recorded-vcr",
        "title": "LLM Integration Tests With VCR Cassettes",
        "tldr": "VCR-py: record real LLM HTTP calls once; replay them in CI. Real-world integration tests without per-run LLM cost or flakiness.",
        "category": "testing",
        "language": "python",
        "framework": "vcrpy + pytest",
        "tags": ["vcr", "integration-test", "recorded", "deterministic"],
        "best_for_tags": ["integration-coverage", "ci-cost", "regression-protection"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Integration tests that exercise REAL LLM behavior (not just mocked) but should run deterministically in CI without per-run cost. VCR records once, replays forever.",
        "when_not_to_use": "Skip when output uniqueness matters (each call should be different). Skip when prompts evolve frequently (cassettes go stale).",
        "quick_start": "pip install pytest vcrpy && pytest tests/test_integration.py",
        "full_code": '''"""Integration tests with VCR cassettes."""
from __future__ import annotations

import os
import pytest
import vcr
from openai import OpenAI


# ----------------- VCR FIXTURE -----------------

# Cassettes live in tests/cassettes/*.yaml
# Each cassette records the HTTP request/response of a real call.

vcr_obj = vcr.VCR(
    cassette_library_dir="tests/cassettes",
    record_mode="once",  # Record on first run; replay after
    match_on=["uri", "method", "body"],
    filter_headers=["authorization", "openai-organization"],
    decode_compressed_response=True,
)


@pytest.fixture
def vcr_cassette(request):
    """Auto-load cassette named after the test function."""
    name = f"{request.node.name}.yaml"
    with vcr_obj.use_cassette(name):
        yield


# ----------------- CODE UNDER TEST -----------------

def summarize(text: str, client: OpenAI) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize in one sentence."},
            {"role": "user", "content": text},
        ],
        temperature=0,
        seed=42,
    )
    return response.choices[0].message.content


# ----------------- INTEGRATION TESTS -----------------

@pytest.fixture
def client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "test-key-for-replay"))


def test_summarize_long_text(client, vcr_cassette):
    long_text = (
        "Rate limiting is a strategy for controlling the rate of requests "
        "to an API. Common patterns include token bucket, leaky bucket, "
        "and sliding window. Each has different memory and fairness trade-offs."
    )
    summary = summarize(long_text, client)
    assert len(summary) < len(long_text)
    assert "rate limit" in summary.lower()


def test_summarize_short_text(client, vcr_cassette):
    short_text = "OAuth 2.0 PKCE prevents authorization-code interception."
    summary = summarize(short_text, client)
    assert "OAuth" in summary or "authorization" in summary.lower()


def test_summarize_empty_string(client, vcr_cassette):
    """Edge case — should return something sensible."""
    summary = summarize("", client)
    assert summary  # non-empty (model handles edge case)


# ----------------- WORKFLOW -----------------

WORKFLOW = """
# Record cassettes (run with real API key)
export OPENAI_API_KEY=sk-...
pytest tests/test_integration.py

# First run: cassettes recorded in tests/cassettes/*.yaml
# Subsequent runs: replay; no API calls

# Commit cassettes to git (so CI can replay without keys)
git add tests/cassettes
git commit -m "Add VCR cassettes"

# Re-record (after prompt change):
rm tests/cassettes/test_summarize_long_text.yaml
pytest tests/test_integration.py  # re-records
"""


# ----------------- ADVANCED: ALLOW BODY DRIFT -----------------

# When prompts include dynamic data (timestamps, IDs), bodies don't match.
# Use a request-matcher that ignores certain fields:

custom_vcr = vcr.VCR(
    cassette_library_dir="tests/cassettes",
    record_mode="once",
    match_on=["uri", "method"],   # don't match body
    # ... or write a custom matcher
)


# ----------------- COMMIT CASSETTES TO REPO -----------------

# tests/cassettes/test_summarize_long_text.yaml:
SAMPLE_CASSETTE = """
interactions:
- request:
    body: '{"model": "gpt-4o-mini", "messages": [...], "temperature": 0}'
    headers:
      Content-Type: [application/json]
    method: POST
    uri: https://api.openai.com/v1/chat/completions
  response:
    body:
      string: '{"id": "chatcmpl-...", "choices": [{"message": {"content": "Rate limiting controls request rates via algorithms like token bucket."}}]}'
    headers: {Content-Type: [application/json]}
    status: {code: 200, message: OK}
version: 1
"""
''',
        "dependencies": [
            {"name": "pytest", "version": ">=7.0", "purpose": "Test runner"},
            {"name": "vcrpy", "version": ">=6.0", "purpose": "HTTP request recording"},
            {"name": "openai", "version": ">=1.40", "purpose": "Real LLM client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "Required to RECORD (not REPLAY)", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install pytest vcrpy openai",
            "Set OPENAI_API_KEY env var (for first record)",
            "Run pytest: first run records cassettes",
            "Commit cassettes to git",
            "CI replays cassettes (no API key needed)",
        ],
        "variations": [
            {"label": "Use respx instead", "description": "More Pythonic HTTPX mocking.", "code_snippet": "# pip install respx; @respx.mock def test(): respx.post('...').mock(return_value=httpx.Response(...)). No record/replay; you write fixtures."},
            {"label": "Scrub PII from cassettes", "description": "Don't commit secrets.", "code_snippet": "vcr.VCR(filter_headers=['authorization'], filter_post_data_parameters=['user_email'])"},
            {"label": "Cassette per-class", "description": "Group related tests.", "code_snippet": "@vcr_obj.use_cassette('test_classifier.yaml')\\nclass TestClassifier: ... # all methods share one cassette file"},
        ],
        "common_errors": [
            {"error_text": "Test fails — request body doesn't match cassette", "cause": "Prompt drifted since recording.", "fix_snippet": "Re-record: delete cassette + re-run. Or use match_on=['uri', 'method'] to skip body matching."},
            {"error_text": "API key leaked in cassette", "cause": "Forgot to filter headers.", "fix_snippet": "filter_headers=['authorization', 'openai-organization']. Review cassettes BEFORE git add."},
            {"error_text": "Cassette grows huge over time", "cause": "Multiple recordings stack up.", "fix_snippet": "Use record_mode='once' (records first call, replays after). Delete cassette to force re-record."},
            {"error_text": "Cassettes work locally, fail in CI", "cause": "Different SDK version → different headers.", "fix_snippet": "Pin SDK version (openai==X.Y.Z) in requirements. Cassettes are sensitive to SDK changes."},
        ],
        "production_checklist": [
            "Filter Authorization + other secret headers.",
            "Pin SDK version (cassettes break on SDK header changes).",
            "Review cassettes before committing (no leaked PII / secrets).",
            "Re-record cassettes when prompt changes intentionally.",
            "Pair with unit tests (fast feedback) and snapshot tests (output verification).",
            "Don't commit cassettes with sensitive responses (customer data).",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["vcrpy==6.0", "openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["vcrpy", "pytest"],
        "related_glossary_slugs": ["integration-testing", "vcr"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "VCR vs respx vs mock?", "answer": "Mock: fastest, no real call ever. respx: HTTP-level fixtures, you write them. VCR: record real call once, replay forever. Use VCR for INTEGRATION tests where you want realistic responses; mock for unit tests."},
            {"question": "How to handle dynamic data in prompts?", "answer": "Either (a) strip dynamic fields with match_on=['uri', 'method'], or (b) use custom matcher that ignores transient parts of the body."},
            {"question": "When to re-record?", "answer": "When you've intentionally changed: prompt content, model version, response_format, or other request shape. Don't re-record on every test run."},
            {"question": "Cassettes too big for git?", "answer": "Use git LFS for cassettes. Or store in a separate test-data repo. Most cassettes are small (a few KB); only worry for huge response bodies."},
        ],
        "github_url": "https://github.com/kevin1024/vcrpy",
        "meta_title": "LLM Integration Tests With VCR Cassettes Starter",
        "meta_description": "VCR-py: record real LLM HTTP calls once, replay in CI. Real-world integration tests without per-run cost.",
    },
    {
        "slug": "llm-eval-as-test-with-pytest",
        "title": "LLM Eval-As-Test (Quality Gates In CI)",
        "tldr": "Express LLM quality requirements as pytest assertions: 'answer faithful to context', 'tool call format valid', 'latency under SLA'. Fails CI on regression.",
        "category": "testing",
        "language": "python",
        "framework": "pytest + custom",
        "tags": ["eval", "ci-gate", "quality", "pytest"],
        "best_for_tags": ["production-llm-app", "quality-gates", "ml-engineers"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Production LLM app where prompt/model changes need quality gates. Express requirements as pytest tests; CI fails if quality regresses. Lightweight alternative to dedicated eval frameworks.",
        "when_not_to_use": "Skip for early prototypes (overhead). Skip if you have a dedicated eval suite (Ragas, Promptfoo) — duplication isn't valuable.",
        "quick_start": "pip install pytest openai && pytest tests/test_quality.py",
        "full_code": '''"""LLM eval-as-test: quality requirements expressed as pytest assertions."""
from __future__ import annotations

import json
import os
import time
import pytest
from openai import OpenAI


client = OpenAI()


# ----------------- CODE UNDER TEST -----------------

def answer_with_context(question: str, context: str) -> dict:
    """RAG-style answerer."""
    start = time.time()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer using only the provided context."},
            {"role": "user", "content": f"Context:\\n{context}\\n\\nQuestion: {question}"},
        ],
        temperature=0,
    )
    return {
        "answer": response.choices[0].message.content,
        "latency_s": time.time() - start,
        "tokens": response.usage.completion_tokens,
    }


# ----------------- JUDGE (LLM-as-evaluator) -----------------

def judge_faithful(answer: str, context: str) -> bool:
    """Is the answer grounded in the context?"""
    judge_response = client.chat.completions.create(
        model="gpt-4o",  # stronger model as judge
        messages=[
            {"role": "user", "content": (
                f"Context: {context}\\n\\n"
                f"Answer: {answer}\\n\\n"
                "Is every factual claim in the Answer supported by the Context? "
                "Respond with only 'YES' or 'NO'."
            )},
        ],
        temperature=0,
    )
    return "YES" in judge_response.choices[0].message.content.upper()


def judge_addresses_question(question: str, answer: str) -> bool:
    judge_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": (
                f"Question: {question}\\nAnswer: {answer}\\n\\n"
                "Does the Answer address the Question? Reply 'YES' or 'NO'."
            )},
        ],
        temperature=0,
    )
    return "YES" in judge_response.choices[0].message.content.upper()


# ----------------- EVAL DATASET -----------------

TEST_CASES = [
    {
        "name": "rate_limit_question",
        "context": "The /search endpoint allows 100 requests per second per API key.",
        "question": "What's the rate limit for /search?",
        "expected_keywords": ["100", "RPS", "per second", "second"],
    },
    {
        "name": "soc2_question",
        "context": "SOC2 Type II audits run annually covering security and availability.",
        "question": "How often is the SOC2 audit?",
        "expected_keywords": ["annually", "annual", "year"],
    },
    {
        "name": "out_of_scope",
        "context": "Our pricing tiers are Basic, Pro, Enterprise.",
        "question": "What's your company's stock price?",
        "expected_keywords": ["not", "don't", "outside", "not in context"],
    },
]


# ----------------- TESTS (quality gates) -----------------

@pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: c["name"])
def test_answer_is_relevant(case):
    """Every test case: answer addresses the question."""
    result = answer_with_context(case["question"], case["context"])
    assert judge_addresses_question(case["question"], result["answer"]), \\
        f"Answer didn't address question for {case['name']}: {result['answer']}"


@pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: c["name"])
def test_answer_is_faithful(case):
    """Answer grounded in context."""
    result = answer_with_context(case["question"], case["context"])
    assert judge_faithful(result["answer"], case["context"]), \\
        f"Answer hallucinated for {case['name']}: {result['answer']}"


@pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: c["name"])
def test_contains_expected_keywords(case):
    """At least one expected keyword appears."""
    result = answer_with_context(case["question"], case["context"])
    text = result["answer"].lower()
    assert any(kw.lower() in text for kw in case["expected_keywords"]), \\
        f"Answer for {case['name']} missing expected keywords. Got: {result['answer'][:200]}"


def test_latency_under_sla():
    """P95 latency below 3s."""
    latencies = []
    for case in TEST_CASES:
        result = answer_with_context(case["question"], case["context"])
        latencies.append(result["latency_s"])
    p95 = sorted(latencies)[int(0.95 * len(latencies))]
    assert p95 < 3.0, f"P95 latency {p95}s exceeds 3s SLA"


def test_token_budget():
    """Answers stay concise — under 200 tokens average."""
    tokens = []
    for case in TEST_CASES:
        result = answer_with_context(case["question"], case["context"])
        tokens.append(result["tokens"])
    avg = sum(tokens) / len(tokens)
    assert avg < 200, f"Avg tokens {avg} exceeds 200 budget"
''',
        "dependencies": [
            {"name": "pytest", "version": ">=7.0", "purpose": "Test runner"},
            {"name": "openai", "version": ">=1.40", "purpose": "LLM under test + judge"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "Both for test + judge", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install pytest openai",
            "Define TEST_CASES with question + context + expected_keywords",
            "Run pytest tests/test_quality.py",
            "Use --ignore-glob='*test_quality*' in CI to skip on every PR; run nightly",
        ],
        "variations": [
            {"label": "Statistical pass-rate threshold", "description": "Require X% pass rate, not 100%.", "code_snippet": "# Run N cases; count passes; assert pass_rate > 0.85. Better than all-or-nothing for noisy outputs."},
            {"label": "Cost gate", "description": "Fail if cost-per-query rises.", "code_snippet": "# Track cost = (input_tokens * $in_rate + output_tokens * $out_rate). Assert avg cost < threshold."},
            {"label": "Bias / fairness gate", "description": "Test for biased outputs.", "code_snippet": "# Include sensitive-topic test cases; use LLM judge to detect biased responses. Fail if any case detected."},
        ],
        "common_errors": [
            {"error_text": "Judge LLM inconsistent", "cause": "Non-determinism in judge.", "fix_snippet": "Use temperature=0 + seed in judge. Use stronger judge model (gpt-4o, not mini). Run judge 3x and require majority."},
            {"error_text": "Quality tests flaky in CI", "cause": "Real LLM non-determinism.", "fix_snippet": "Pin model version. seed=42. Use pass-rate threshold (e.g., 85%) instead of all-or-nothing. Or use VCR cassettes for replay."},
            {"error_text": "Latency varies wildly", "cause": "Network / OpenAI variance.", "fix_snippet": "Run latency tests on a dedicated CI runner. Use longer SLA thresholds. Or measure latency separately from quality."},
            {"error_text": "Cost of running quality tests", "cause": "Many cases × 2 LLM calls (test + judge).", "fix_snippet": "Run on every PR vs nightly: per PR = subset of critical cases; nightly = full suite. Cache judge results."},
        ],
        "production_checklist": [
            "Pin model + seed for determinism.",
            "Use STRONGER LLM as judge (gpt-4o judges gpt-4o-mini outputs).",
            "Cover happy path + edge cases + adversarial.",
            "Test latency + cost + quality (not just quality).",
            "Run lightweight subset on every PR; full suite nightly.",
            "Track scores over time — alert on drift, not just regression.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["pytest==7.0", "openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["pytest", "openai"],
        "related_glossary_slugs": ["llm-as-judge", "quality-gate"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Eval-as-test vs dedicated eval framework?", "answer": "Eval-as-test: lightweight, lives with code, fast to add. Dedicated (Ragas, DeepEval, Promptfoo): more metrics, structured reports. Use eval-as-test for CI gates; framework for deep analysis."},
            {"question": "How to handle non-deterministic judge?", "answer": "Three options: (1) Use stronger judge + temp 0. (2) Run N times + majority vote. (3) Use pass-rate threshold across many cases. Option 3 is most robust."},
            {"question": "Cost of running on every PR?", "answer": "10 cases × 2 LLM calls × $0.001 = $0.02 per run. Hundreds of PRs/mo = ~$5/mo. Cheap relative to value."},
            {"question": "What if all tests pass but quality is bad?", "answer": "Test cases are samples. Pair with: random sampling of production traffic + human review. Tests catch known regressions; samples catch unknown."},
        ],
        "github_url": "",
        "meta_title": "LLM Eval-As-Test Starter — Pytest Quality Gates",
        "meta_description": "Express LLM quality requirements as pytest tests: faithful answers, latency SLA, cost budget. CI fails on regression.",
    },
]
