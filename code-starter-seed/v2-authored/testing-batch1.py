"""Testing starters — pytest patterns, LLM mocking, snapshot tests."""

RECORDS = [
    {
        "slug": "pytest-mocking-openai-calls",
        "title": "Pytest: Mocking OpenAI Calls With Realistic Fixtures",
        "tldr": "Mock OpenAI / Anthropic API calls in pytest using respx (httpx) or monkeypatching — without changing your production code. Includes fixtures for chat, embeddings, and streaming responses.",
        "category": "testing",
        "language": "python",
        "framework": "pytest + respx",
        "tags": ["pytest", "mocking", "openai", "testing"],
        "best_for_tags": ["unit-tests", "ci-friendly", "deterministic-tests"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When testing LLM-using code in CI without hitting real APIs (cost + flakiness + latency). Especially useful for testing error paths, retry logic, and edge-case responses.",
        "when_not_to_use": "Skip for integration tests where you DO want to call real APIs (in a separate suite gated by a flag). Skip for one-shot smoke tests of model behavior.",
        "quick_start": "pip install pytest respx httpx && pytest tests/test_llm.py -v",
        "full_code": '''"""Pytest fixtures for mocking OpenAI calls.

We use respx (httpx mock) so the OpenAI client's HTTP layer is intercepted —
no monkey-patching the SDK itself. Production code stays untouched.
"""
from __future__ import annotations

import json
import pytest
import respx
from httpx import Response


# ----------------- FIXTURES -----------------

@pytest.fixture
def mock_chat_completion():
    """Returns a function that creates a mocked OpenAI chat completion response."""
    def _make(content: str, *, model: str = "gpt-4o-mini", prompt_tokens: int = 50, completion_tokens: int = 30):
        return {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1700000000,
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
    return _make


@pytest.fixture
def mock_embedding():
    """Returns a function that creates a mocked OpenAI embeddings response."""
    def _make(*, n_inputs: int, dim: int = 1536):
        return {
            "object": "list",
            "model": "text-embedding-3-small",
            "data": [
                {"object": "embedding", "embedding": [0.1] * dim, "index": i}
                for i in range(n_inputs)
            ],
            "usage": {"prompt_tokens": n_inputs * 10, "total_tokens": n_inputs * 10},
        }
    return _make


@pytest.fixture
def mock_tool_call_completion():
    """Returns a function for chat completions that include tool calls."""
    def _make(tool_name: str, tool_args: dict, *, content: str | None = None):
        return {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1700000000,
            "model": "gpt-4o-mini",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": [{
                        "id": "call_test_123",
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(tool_args),
                        },
                    }],
                },
                "finish_reason": "tool_calls",
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
        }
    return _make


# ----------------- TESTS -----------------

@respx.mock
def test_chat_returns_expected_content(mock_chat_completion):
    """Production code under test."""
    from openai import OpenAI
    client = OpenAI(api_key="test-key")

    respx.post("https://api.openai.com/v1/chat/completions").respond(
        json=mock_chat_completion("Hello, world!")
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "say hi"}],
    )
    assert resp.choices[0].message.content == "Hello, world!"
    assert resp.usage.total_tokens == 80


@respx.mock
def test_embedding_returns_correct_dim(mock_embedding):
    from openai import OpenAI
    client = OpenAI(api_key="test-key")

    respx.post("https://api.openai.com/v1/embeddings").respond(
        json=mock_embedding(n_inputs=3, dim=1536)
    )

    resp = client.embeddings.create(input=["a", "b", "c"], model="text-embedding-3-small")
    assert len(resp.data) == 3
    assert len(resp.data[0].embedding) == 1536


@respx.mock
def test_tool_call_response(mock_tool_call_completion):
    from openai import OpenAI
    client = OpenAI(api_key="test-key")

    respx.post("https://api.openai.com/v1/chat/completions").respond(
        json=mock_tool_call_completion("get_weather", {"location": "Tokyo"})
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "weather"}],
        tools=[{"type": "function", "function": {"name": "get_weather", "parameters": {}}}],
    )
    tc = resp.choices[0].message.tool_calls[0]
    assert tc.function.name == "get_weather"
    assert json.loads(tc.function.arguments)["location"] == "Tokyo"


@respx.mock
def test_retry_on_rate_limit():
    """First call gets 429; second succeeds. Production code should retry."""
    from openai import OpenAI
    client = OpenAI(api_key="test-key", max_retries=3)

    route = respx.post("https://api.openai.com/v1/chat/completions")
    route.side_effect = [
        Response(429, headers={"retry-after": "1"}, json={"error": "rate_limited"}),
        Response(200, json={
            "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-mini",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }),
    ]
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
    )
    assert resp.choices[0].message.content == "ok"
    assert route.call_count == 2  # first failed, second succeeded
''',
        "dependencies": [
            {"name": "pytest", "version": ">=8.0", "purpose": "Test framework"},
            {"name": "respx", "version": ">=0.21", "purpose": "Mock httpx-based clients"},
            {"name": "httpx", "version": ">=0.27", "purpose": "Underlying HTTP client OpenAI uses"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install pytest respx httpx openai",
            "Save tests in tests/test_llm.py",
            "Run: pytest tests/test_llm.py -v",
            "No OPENAI_API_KEY needed (test-key works for mocked calls).",
        ],
        "variations": [
            {
                "label": "Streaming response mock",
                "description": "Mock a streamed chat completion.",
                "code_snippet": "# respx supports streaming; mock the SSE response:\\nrespx.post(...).respond(stream=[\\n  'data: {\"choices\":[{\"delta\":{\"content\":\"Hello\"}}]}\\\\n\\\\n',\\n  'data: {\"choices\":[{\"delta\":{\"content\":\" world\"}}]}\\\\n\\\\n',\\n  'data: [DONE]\\\\n\\\\n',\\n])",
            },
            {
                "label": "Async tests",
                "description": "Mock AsyncOpenAI.",
                "code_snippet": "@pytest.mark.asyncio\\n@respx.mock\\nasync def test_async_chat():\\n    from openai import AsyncOpenAI\\n    client = AsyncOpenAI(api_key='test-key')\\n    respx.post(...).respond(json=...)\\n    resp = await client.chat.completions.create(...)",
            },
            {
                "label": "Anthropic mock",
                "description": "Same pattern, different URL.",
                "code_snippet": "respx.post('https://api.anthropic.com/v1/messages').respond(json={'id': 'msg_test', 'type': 'message', 'role': 'assistant', 'content': [{'type': 'text', 'text': 'hi'}], 'model': 'claude-3-5-haiku-latest', 'stop_reason': 'end_turn', 'usage': {'input_tokens': 10, 'output_tokens': 5}})",
            },
            {
                "label": "Recording real responses",
                "description": "Use VCR to record once, replay on subsequent runs.",
                "code_snippet": "# pip install vcrpy\\nimport vcr\\n@vcr.use_cassette('cassettes/test_chat.yaml')\\ndef test_chat(): ...  # First run hits real API and records; subsequent replay.",
            },
        ],
        "common_errors": [
            {
                "error_text": "AssertionError: respx call not matched",
                "cause": "URL or method mismatch.",
                "fix_snippet": "Verify exact URL — OpenAI client uses https://api.openai.com/v1/.... Use respx.post() or respx.get() matching the SDK's actual request method.",
            },
            {
                "error_text": "Connection refused or timeout",
                "cause": "respx didn't intercept; real network call attempted.",
                "fix_snippet": "Decorate every test with @respx.mock (not just module-level). Or use respx as a pytest fixture: @pytest.fixture(autouse=True) -> respx_mock = respx.mock(); respx_mock.start(); yield; respx_mock.stop().",
            },
            {
                "error_text": "AsyncMock not being awaited",
                "cause": "Async test without @pytest.mark.asyncio.",
                "fix_snippet": "Install pytest-asyncio. Decorate async tests with @pytest.mark.asyncio. Configure mode in pyproject.toml: [tool.pytest.ini_options] asyncio_mode = 'auto'.",
            },
            {
                "error_text": "Tests pass locally, fail in CI with ‘module not found’",
                "cause": "Local has API keys set; mocks bypassed.",
                "fix_snippet": "Ensure tests don't depend on env vars to ‘decide’ whether to mock. Always mock in unit tests; gate real-API integration tests behind a separate marker (@pytest.mark.integration).",
            },
        ],
        "production_checklist": [
            "Separate unit tests (mocked) from integration tests (real API) via pytest markers.",
            "Run unit tests on every push; integration tests on a slower cadence.",
            "Cap test runtime: a unit test hitting the network is broken.",
            "Use deterministic fixtures — random embeddings break similarity tests.",
            "Cover error paths: 429, 500, network failure, malformed response.",
            "Test the wrapping logic, not the SDK itself — don't test ‘OpenAI returned content’; test ‘our retry logic ran’.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["pytest==8.3.3", "respx==0.21.1", "httpx==0.27.2", "openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["pytest"],
        "related_glossary_slugs": ["mocking", "unit-testing", "integration-testing"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why respx and not unittest.mock?",
                "answer": "respx mocks at the HTTP layer; your production code uses the SDK normally. unittest.mock would patch SDK methods, but breaks if you change SDK versions and tests can't catch SDK errors. respx is more robust.",
            },
            {
                "question": "Should I record real responses or hand-craft mocks?",
                "answer": "Hand-craft for unit tests (you control all paths). Record (VCR) for tricky edge cases or initial test setup. Hand-crafted is more maintainable long-term.",
            },
            {
                "question": "Do I still need integration tests?",
                "answer": "Yes — at least one per major LLM path, run nightly or on release branches. Unit tests prove your code; integration tests prove the SDK + LLM still works as expected.",
            },
            {
                "question": "How do I test prompt quality?",
                "answer": "That's evaluation, not unit testing. Use RAGAS / Promptfoo / llm-as-judge for prompt quality. Keep unit tests focused on code logic.",
            },
        ],
        "github_url": "https://github.com/lundberg/respx",
        "meta_title": "Pytest Mocking OpenAI Calls — Starter",
        "meta_description": "Mock OpenAI/Anthropic API calls with respx in pytest. Realistic fixtures for chat, embeddings, tool calls, retries — production code untouched.",
    },
    {
        "slug": "snapshot-tests-for-llm-outputs",
        "title": "Snapshot Tests For LLM Outputs (Approval Testing)",
        "tldr": "Approval-testing pattern for LLM outputs: save the first ‘known good’ output to a snapshot file, then fail tests when output drifts. Includes human-review gating for legitimate changes.",
        "category": "testing",
        "language": "python",
        "framework": "pytest + syrupy",
        "tags": ["snapshot-testing", "regression", "approval-testing", "llm"],
        "best_for_tags": ["prompt-regression", "non-deterministic-outputs", "high-stakes-prompts"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When you have prompts whose outputs you've manually verified as good and you want to catch unintentional drift (model upgrade, prompt edit, fixture change). Pair with temperature=0.",
        "when_not_to_use": "Skip when outputs are genuinely non-deterministic (creative writing). Skip when you have ground-truth labels (use direct assertions).",
        "quick_start": "pip install pytest syrupy && pytest --snapshot-update  # first run; then commit __snapshots__",
        "full_code": '''"""Snapshot testing for LLM outputs.

Pattern:
  1. First run: pytest --snapshot-update → saves current outputs to __snapshots__/
  2. CI runs: pytest → compares against saved; fails if changed.
  3. Legitimate change: review diff manually, run pytest --snapshot-update,
     commit the new snapshot.

Pair with temperature=0 to remove noise. The snapshot tests then catch:
  - Model version drift
  - Prompt template changes
  - Fixture changes
"""
from __future__ import annotations

import pytest
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.json import JSONSnapshotExtension


# Production function under test
def summarize(text: str, *, model: str = "gpt-4o-mini") -> dict:
    """Real implementation calls OpenAI; we mock it in test."""
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": "Summarize in exactly 3 sentences."},
            {"role": "user", "content": text},
        ],
    )
    return {
        "model": model,
        "summary": resp.choices[0].message.content,
        "input_chars": len(text),
        "tokens": resp.usage.total_tokens,
    }


@pytest.fixture
def snapshot_json(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Use JSON snapshot extension — cleaner diffs than default."""
    return snapshot.use_extension(JSONSnapshotExtension)


TEST_CASES = [
    {"id": "short_news", "text": "OpenAI announced a new model called o2 on Tuesday."},
    {"id": "technical_paper", "text": "Reciprocal rank fusion (RRF) combines results from multiple retrievers via 1/(k+rank) scoring."},
    {"id": "ambiguous", "text": "The plant was magnificent."},
]


@pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: c["id"])
def test_summary_snapshot(case, snapshot_json, monkeypatch):
    """Snapshot the structured output."""
    # In a real test, we'd mock OpenAI here. For the snapshot to be stable,
    # we provide a deterministic mock per test case.
    def fake_chat(self, **kwargs):
        # Return a deterministic answer per case
        canned = {
            "short_news": "OpenAI launched a new model called o2 on Tuesday. The release marks their latest in 2025. Details on capabilities and pricing were limited.",
            "technical_paper": "Reciprocal rank fusion is a method for combining ranked lists. Each document gets a score of 1/(k+rank) summed across retrievers. It's scale-free and robust to heterogeneous retrievers.",
            "ambiguous": "The plant was magnificent. No further details are provided. The sentence could refer to either a factory or vegetation.",
        }
        from types import SimpleNamespace
        msg = SimpleNamespace(content=canned[case["id"]])
        choice = SimpleNamespace(message=msg, finish_reason="stop", index=0)
        usage = SimpleNamespace(total_tokens=80)
        return SimpleNamespace(choices=[choice], usage=usage)

    # Patch only for this test
    from openai.resources.chat.completions import Completions
    monkeypatch.setattr(Completions, "create", fake_chat)

    result = summarize(case["text"])

    # Strip non-deterministic fields if any (timestamps, IDs)
    snapshot_data = {k: v for k, v in result.items() if k != "tokens"}
    # tokens can vary slightly; check it's within range separately
    assert 20 <= result["tokens"] <= 200

    assert snapshot_data == snapshot_json
''',
        "dependencies": [
            {"name": "pytest", "version": ">=8.0", "purpose": "Test framework"},
            {"name": "syrupy", "version": ">=4.6", "purpose": "Snapshot testing for pytest"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install pytest syrupy",
            "Add tests/test_summary_snapshot.py",
            "First run: pytest --snapshot-update",
            "Review and commit __snapshots__/ directory.",
            "Subsequent runs: pytest (compares to saved snapshots).",
            "When intentionally changing: pytest --snapshot-update, review diff, commit.",
        ],
        "variations": [
            {
                "label": "Snapshot the prompt template, not the output",
                "description": "Catch unintentional prompt edits.",
                "code_snippet": "def test_prompt_template_unchanged(snapshot):\\n    from app.prompts import SUMMARIZER_PROMPT\\n    assert SUMMARIZER_PROMPT == snapshot",
            },
            {
                "label": "Selective field comparison",
                "description": "Compare only stable fields.",
                "code_snippet": "# Filter out non-deterministic fields:\\nstable = {k: v for k, v in result.items() if k not in ('tokens', 'request_id', 'timestamp')}\\nassert stable == snapshot",
            },
            {
                "label": "Semantic similarity check instead of exact",
                "description": "Allow surface drift in wording.",
                "code_snippet": "from sentence_transformers import util\\nold_emb = embed(snapshot.read())\\nnew_emb = embed(result['summary'])\\nassert util.cos_sim(old_emb, new_emb) > 0.9",
            },
            {
                "label": "Visual diff in CI",
                "description": "GitHub Actions diff comment.",
                "code_snippet": "# In CI: when snapshot fails, post the diff as PR comment for reviewer.\\n# Reviewer decides: regression or intentional.",
            },
        ],
        "common_errors": [
            {
                "error_text": "Snapshot file missing",
                "cause": "First run after writing test, --snapshot-update not used.",
                "fix_snippet": "Run pytest --snapshot-update once; commit __snapshots__/.",
            },
            {
                "error_text": "Snapshot diff is huge for tiny prompt change",
                "cause": "Real LLM output is non-deterministic even at temp=0.",
                "fix_snippet": "Pin model version, temperature=0, seed if supported. Mock the LLM for snapshot tests (as in the starter). Use semantic similarity variant for genuinely non-deterministic outputs.",
            },
            {
                "error_text": "Snapshot tests fail in CI but pass locally",
                "cause": "Locale, line endings, or whitespace differences.",
                "fix_snippet": "Normalize before snapshot: strip whitespace, sort dicts. Add .gitattributes for consistent line endings.",
            },
            {
                "error_text": "Snapshot file is unreadable in PR review",
                "cause": "Default syrupy format is dense.",
                "fix_snippet": "Use JSONSnapshotExtension (starter does this) — gives line-by-line diffs in JSON.",
            },
        ],
        "production_checklist": [
            "Commit snapshots; treat as part of the codebase.",
            "Snapshot review in PRs: any change to __snapshots__/ requires explicit reviewer attention.",
            "Pair with model version pinning; otherwise model upgrades constantly fail snapshots.",
            "For genuinely non-deterministic outputs, use semantic similarity variation.",
            "Set up CI to comment on PR with snapshot diff for easier review.",
            "Keep snapshots focused on stable contracts (structure, key facts), not full prose.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["pytest==8.3.3", "syrupy==4.7.2"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["snapshot-testing", "approval-testing", "regression"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "When does this beat traditional assertion testing?",
                "answer": "When the ‘correct’ output is hard to write as a clean assertion but easy to recognize. Snapshot tests are approval-by-review — humans agree once, machine catches drift forever.",
            },
            {
                "question": "Doesn't this just rubber-stamp wrong outputs?",
                "answer": "If you accept a bad snapshot, yes. The discipline: don't run --snapshot-update without reading the diff carefully. Treat updates as code reviews.",
            },
            {
                "question": "How is this different from Jest snapshot tests?",
                "answer": "Same pattern; syrupy is the Python equivalent. Works the same way — first run records, subsequent compare.",
            },
            {
                "question": "Can I snapshot real (non-mocked) LLM outputs?",
                "answer": "Only with pinned model version + temperature=0 + integration test marker. Even then, expect occasional drift requiring update. For unit tests, mock the LLM.",
            },
        ],
        "github_url": "https://github.com/syrupy-project/syrupy",
        "meta_title": "Snapshot Tests For LLM Outputs — Starter",
        "meta_description": "Approval testing for LLM outputs with syrupy: save known-good output, fail on drift, review legitimate changes. Plus semantic-similarity variant.",
    },
]
