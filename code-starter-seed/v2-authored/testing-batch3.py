"""Testing starters — batch 3: property-based LLM tests, tool-schema contract tests, prompt mutation eval."""

RECORDS = [
    {
        "slug": "property-based-llm-testing-hypothesis",
        "title": "Property-Based LLM Testing With Hypothesis (Invariants, Not Examples)",
        "tldr": "Example tests only cover inputs you imagined. Define invariants an LLM step must always hold (valid JSON, idempotent, no PII echo) and let Hypothesis generate adversarial cases and shrink failures.",
        "category": "testing",
        "language": "python",
        "framework": "Hypothesis + pytest",
        "tags": ["testing", "hypothesis", "property-based", "pytest", "llm"],
        "best_for_tags": ["ci-quality", "extraction-pipelines", "regression-prevention"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "Testing an LLM step whose output must obey structural rules (parses to a schema, idempotent, leaks no input PII) across inputs you can't enumerate by hand. Hypothesis fuzzes and shrinks to a minimal failing case.",
        "when_not_to_use": "Skip for purely deterministic code that golden tests already pin. Skip when one or two known inputs fully characterize the behavior and generation cost isn't worth it.",
        "quick_start": "pip install hypothesis pytest anthropic && pytest test_extract_props.py -q",
        "full_code": '''"""Property-based tests for an LLM extraction step.

Invariants (must hold for ANY input):
  1. Output always parses to the target schema.
  2. Re-extracting the rendered output is idempotent.
  3. No input PII token appears verbatim in the returned metadata.

Runs in CI WITHOUT an API key: set LLM_STUB=1 (default here) to use a
deterministic local stub. Unset it + set ANTHROPIC_API_KEY for a live run.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

MODEL = "claude-sonnet-4-5"
USE_STUB = os.environ.get("LLM_STUB", "1") == "1"

EMAIL_RE = re.compile(r"[\\w.+-]+@[\\w-]+\\.[\\w.-]+")

# ----------------- SYSTEM UNDER TEST -----------------

_PROMPT = (
    "Extract fields from the text. Return ONLY JSON with keys "
    '"name" (string), "emails" (array of strings), "summary" (string). '
    "Do not include any email address inside summary."
)


def _stub_extract(text: str) -> str:
    """Deterministic stand-in for the model. Same contract as the real call."""
    emails = sorted(set(EMAIL_RE.findall(text)))
    name = (text.strip().split() or [""])[0][:40]
    summary = EMAIL_RE.sub("[redacted]", text).strip()[:120]
    return json.dumps({"name": name, "emails": emails, "summary": summary})


# Cache by input hash so Hypothesis shrinking doesn't re-call the model.
_CACHE: dict[str, dict] = {}


def extract_fields(text: str) -> dict:
    """Call the model (or stub) and parse to a dict. Cached by input hash."""
    key = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if key in _CACHE:
        return _CACHE[key]
    raw = _stub_extract(text) if USE_STUB else _live_extract(text)
    data = json.loads(raw)
    _CACHE[key] = data
    return data


def _live_extract(text: str) -> str:
    import anthropic  # imported lazily so CI needs no key

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=512,
        temperature=0,  # pin: nonzero sampling confounds invariants
        system=_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    return msg.content[0].text


# ----------------- INVARIANTS -----------------

REQUIRED_KEYS = {"name", "emails", "summary"}


def _is_valid_shape(d: dict) -> bool:
    return (
        REQUIRED_KEYS <= d.keys()
        and isinstance(d["name"], str)
        and isinstance(d["emails"], list)
        and all(isinstance(e, str) for e in d["emails"])
        and isinstance(d["summary"], str)
    )


@settings(max_examples=25, deadline=None)  # deadline None: network is slow
@given(st.text(min_size=0, max_size=300))
@example("Ada Lovelace ada@calc.org wrote the first algorithm.")
@example("")  # empty input must still return valid shape
def test_output_always_valid_shape(text: str) -> None:
    assert _is_valid_shape(extract_fields(text))


@settings(max_examples=25, deadline=None)
@given(st.text(min_size=1, max_size=200))
def test_idempotent_on_rendered_output(text: str) -> None:
    first = extract_fields(text)
    rendered = f"{first['name']} {' '.join(first['emails'])} {first['summary']}"
    second = extract_fields(rendered)
    assert second["emails"] == first["emails"]  # structural, not string-equal


@settings(max_examples=40, deadline=None)
@given(email=st.from_regex(r"[a-z]{3,8}@[a-z]{3,8}\\.[a-z]{2,3}", fullmatch=True))
def test_no_pii_echoed_into_summary(email: str) -> None:
    text = f"Contact our lead {email} about the Q3 rollout."
    out = extract_fields(text)
    assert email not in out["summary"]  # PII must not survive into free text


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
''',
        "dependencies": [
            {"name": "hypothesis", "version": ">=6.100", "purpose": "Property-based test generation + shrinking"},
            {"name": "pytest", "version": ">=7.0", "purpose": "Test runner"},
            {"name": "anthropic", "version": ">=0.40", "purpose": "Live LLM calls (optional; stub runs offline)"},
        ],
        "env_vars": [
            {"name": "LLM_STUB", "required": False, "description": "Set to 1 (default) to use the deterministic stub so CI runs without a key. Unset for live calls.", "example": "1"},
            {"name": "ANTHROPIC_API_KEY", "required": False, "description": "Only needed when LLM_STUB is unset, for a live model run.", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "pip install hypothesis pytest anthropic",
            "Save test_extract_props.py",
            "Run offline (stub): pytest test_extract_props.py -q",
            "Live run: unset LLM_STUB; export ANTHROPIC_API_KEY=...; pytest test_extract_props.py -q",
            "On failure, copy the @example Hypothesis prints to pin the minimal repro.",
        ],
        "variations": [
            {"label": "Stateful multi-turn agent", "description": "Drive a conversational agent with a state machine and assert invariants after each turn.", "code_snippet": "from hypothesis.stateful import RuleBasedStateMachine, rule\\nclass AgentMachine(RuleBasedStateMachine):\\n    @rule(msg=st.text())\\n    def send(self, msg): self.history.append(agent_turn(self.history, msg)); assert is_valid(self.history[-1])"},
            {"label": "Metamorphic relation", "description": "Paraphrasing the input should not change the extraction.", "code_snippet": "@given(st.sampled_from(EVAL_INPUTS))\\ndef test_paraphrase_invariant(x):\\n    assert extract_fields(x)['emails'] == extract_fields(paraphrase(x))['emails']"},
            {"label": "Record/replay for deterministic CI", "description": "Cache live responses to disk so CI replays without keys.", "code_snippet": "# Wrap _live_extract: read responses/{hash}.json if present, else call + write. Commit the cassette."},
        ],
        "common_errors": [
            {"error_text": "AssertionError on exact string equality", "cause": "LLM output is nondeterministic, so string-equal properties flake.", "fix_snippet": "Assert structural invariants (parses, key subset, list contents), not raw strings. Pin temperature=0."},
            {"error_text": "Test run is slow / burns tokens", "cause": "Hypothesis calls the live API for every generated example.", "fix_snippet": "Cap settings(max_examples=25) and default LLM_STUB=1 in CI. Reserve live runs for a nightly job."},
            {"error_text": "hypothesis.errors.DeadlineExceeded", "cause": "Network latency exceeds Hypothesis's default per-example deadline.", "fix_snippet": "Set @settings(deadline=None) on tests that make network calls."},
            {"error_text": "Shrinking re-calls the API many times", "cause": "Each shrink step re-invokes the model, multiplying cost on a failure.", "fix_snippet": "Cache by input hash (see _CACHE) so identical inputs hit the model once. Or stub during shrink."},
        ],
        "production_checklist": [
            "Pin temperature=0; sampling noise confounds invariant checks.",
            "Default the stub on in CI; gate live runs behind an explicit env flag.",
            "Cache responses by input hash so shrinking doesn't multiply API cost.",
            "Set deadline=None on any test that hits the network.",
            "Seed @example with known tricky inputs (empty, unicode, injected emails).",
            "Assert structural invariants, never raw output strings.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["hypothesis==6.100", "pytest==8.2", "anthropic==0.40"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["deepeval"],
        "related_glossary_slugs": ["llm-evaluation", "structured-output", "json-schema-enforcement", "faithfulness"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Property tests vs example tests?", "answer": "Example tests check fixed input/output pairs you wrote. Property tests assert a rule (invariant) over generated inputs, so they catch edge cases you never thought to write — empty strings, unicode, injected emails — and shrink any failure to a minimal repro."},
            {"question": "How does this run in CI without an API key?", "answer": "LLM_STUB=1 (the default) routes extract_fields through a deterministic local function with the same contract. The invariants are the same; only the generator changes. Unset the flag plus set ANTHROPIC_API_KEY for a live nightly run."},
            {"question": "Why temperature 0?", "answer": "Nonzero temperature adds sampling noise, which makes idempotence and equality invariants flake intermittently. Pinning to 0 isolates prompt/logic bugs from sampling variance."},
            {"question": "Won't 25 examples miss bugs?", "answer": "Hypothesis biases toward boundary values (empty, max-size, surrogate-pair unicode), so 25 generated cases find more than 25 hand-picked ones. Raise max_examples for the nightly live job; keep it low for fast PR checks."},
        ],
        "github_url": "https://github.com/HypothesisWorks/hypothesis",
        "meta_title": "Property-Based LLM Testing With Hypothesis",
        "meta_description": "Test LLM steps with invariants, not examples: valid JSON, idempotence, no PII echo. Hypothesis generates adversarial cases and shrinks failures. Offline in CI.",
    },
    {
        "slug": "tool-schema-contract-tests",
        "title": "Contract Tests for LLM Tool/Function Schemas",
        "tldr": "Agents break silently when a tool's JSON Schema drifts from its handler. Contract-test the boundary: schemas are valid, required fields exist as properties, handlers accept valid payloads and reject bad ones.",
        "category": "testing",
        "language": "python",
        "framework": "pytest + jsonschema",
        "tags": ["testing", "tool-use", "jsonschema", "pytest", "contract"],
        "best_for_tags": ["agent-tooling", "ci-quality", "regression-prevention"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "You maintain a registry of LLM tools/functions where each schema must match its handler. Contract tests catch schema drift (a required field that no longer exists, a renamed param) in CI before an agent calls it.",
        "when_not_to_use": "Skip for a single hard-coded tool that rarely changes. Skip if you generate schemas directly from typed handlers and already round-trip them in another test.",
        "quick_start": "pip install jsonschema pytest && pytest test_tool_contracts.py -q",
        "full_code": '''"""Contract tests for an LLM tool registry.

Each tool = {name, description, input_schema (JSON Schema), handler}.
These tests fail in CI when a schema drifts from its handler, BEFORE an
agent ever calls the broken tool. No API key or network needed.
"""
from __future__ import annotations

import inspect

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

# ----------------- TOOL REGISTRY (2 sample tools) -----------------


def get_weather(city: str, units: str = "celsius") -> dict:
    if units not in {"celsius", "fahrenheit"}:
        raise ValueError("units must be celsius or fahrenheit")
    return {"city": city, "temp": 21, "units": units}


def create_ticket(title: str, body: str, priority: str = "medium") -> dict:
    if priority not in {"low", "medium", "high"}:
        raise ValueError("invalid priority")
    return {"id": "T-1", "title": title, "priority": priority}


TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather for a city.",
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "city": {"type": "string"},
                "units": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["city"],
        },
        "handler": get_weather,
    },
    {
        "name": "create_ticket",
        "description": "Open a support ticket and return its id.",
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            },
            "required": ["title", "body"],
        },
        "handler": create_ticket,
    },
]

IDS = [t["name"] for t in TOOLS]


# ----------------- HELPERS -----------------

_SAMPLES = {"string": "x", "integer": 1, "number": 1.0, "boolean": True, "array": [], "object": {}}


def _minimal_valid_payload(schema: dict) -> dict:
    """Smallest payload satisfying 'required' using each property's type/enum."""
    props = schema.get("properties", {})
    out = {}
    for key in schema.get("required", []):
        spec = props[key]
        out[key] = spec["enum"][0] if "enum" in spec else _SAMPLES[spec["type"]]
    return out


# ----------------- CONTRACT TESTS -----------------


@pytest.mark.parametrize("tool", TOOLS, ids=IDS)
def test_schema_itself_is_valid(tool: dict) -> None:
    Draft202012Validator.check_schema(tool["input_schema"])  # raises if malformed


@pytest.mark.parametrize("tool", TOOLS, ids=IDS)
def test_required_subset_of_properties(tool: dict) -> None:
    schema = tool["input_schema"]
    props = set(schema.get("properties", {}))
    missing = set(schema.get("required", [])) - props
    assert not missing, f"{tool['name']}: required lists non-existent {missing}"


@pytest.mark.parametrize("tool", TOOLS, ids=IDS)
def test_additional_properties_locked(tool: dict) -> None:
    # Unset additionalProperties lets typo'd args pass silently to the handler.
    assert tool["input_schema"].get("additionalProperties") is False


@pytest.mark.parametrize("tool", TOOLS, ids=IDS)
def test_handler_accepts_minimal_valid_payload(tool: dict) -> None:
    payload = _minimal_valid_payload(tool["input_schema"])
    Draft202012Validator(tool["input_schema"]).validate(payload)
    tool["handler"](**payload)  # must not raise on a schema-valid call


@pytest.mark.parametrize("tool", TOOLS, ids=IDS)
def test_schema_rejects_missing_required(tool: dict) -> None:
    required = tool["input_schema"].get("required", [])
    if not required:
        pytest.skip("no required fields")
    bad = _minimal_valid_payload(tool["input_schema"])
    bad.pop(required[0])
    with pytest.raises(ValidationError):
        Draft202012Validator(tool["input_schema"]).validate(bad)


@pytest.mark.parametrize("tool", TOOLS, ids=IDS)
def test_handler_signature_matches_schema(tool: dict) -> None:
    sig_params = set(inspect.signature(tool["handler"]).parameters)
    schema_params = set(tool["input_schema"].get("properties", {}))
    assert schema_params <= sig_params, f"{tool['name']}: schema has params the handler lacks"


def test_registry_meta() -> None:
    names = [t["name"] for t in TOOLS]
    assert len(names) == len(set(names)), "duplicate tool names"
    for t in TOOLS:
        assert t["description"].strip(), f"{t['name']}: empty description (agents route on it)"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
''',
        "dependencies": [
            {"name": "jsonschema", "version": ">=4.20", "purpose": "JSON Schema validation (Draft 2020-12)"},
            {"name": "pytest", "version": ">=7.0", "purpose": "Test runner + parametrization"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install jsonschema pytest",
            "Save test_tool_contracts.py and point TOOLS at your real registry.",
            "Run: pytest test_tool_contracts.py -q",
            "Wire into CI on every PR that touches tool schemas or handlers.",
        ],
        "variations": [
            {"label": "Schema from a Pydantic model", "description": "Generate the schema from the typed model and assert round-trip.", "code_snippet": "from pydantic import BaseModel\\nclass WeatherArgs(BaseModel):\\n    city: str; units: str = 'celsius'\\nassert WeatherArgs.model_json_schema()['required'] == ['city']"},
            {"label": "Snapshot + diff in CI", "description": "Lock schemas to a snapshot so changes force review.", "code_snippet": "# Use syrupy: assert tool['input_schema'] == snapshot — CI fails on any schema change until the snapshot is updated."},
            {"label": "Export to provider tool format", "description": "Validate against Anthropic/OpenAI tool constraints.", "code_snippet": "anthropic_tool = {'name': t['name'], 'description': t['description'], 'input_schema': t['input_schema']}\\nassert anthropic_tool['input_schema']['type'] == 'object'"},
        ],
        "common_errors": [
            {"error_text": "required references a property that doesn't exist", "cause": "A property was renamed/removed but required wasn't updated — the exact drift this catches.", "fix_snippet": "test_required_subset_of_properties fails. Fix required (or restore the property) so required is a subset of properties."},
            {"error_text": "Typo'd argument passes validation silently", "cause": "additionalProperties is unset, so unknown keys are allowed.", "fix_snippet": "Set additionalProperties: False on every tool schema. test_additional_properties_locked enforces it."},
            {"error_text": "Schema valid but handler raises on a valid payload", "cause": "Handler signature diverged from the schema (renamed/removed param).", "fix_snippet": "test_handler_signature_matches_schema introspects inspect.signature vs schema properties; align them."},
            {"error_text": "enum/format declared but not enforced at call time", "cause": "The schema constrains values but the handler trusts them blindly.", "fix_snippet": "Validate inside the handler too (raise ValueError on bad enum) and/or run Draft202012Validator before dispatch."},
        ],
        "production_checklist": [
            "Set additionalProperties: False on every tool schema.",
            "Assert required is a subset of properties for each tool.",
            "Build a minimal valid payload from the schema and call the handler with it.",
            "Introspect handler signatures against schema properties to catch drift.",
            "Enforce uniqueness of tool names and non-empty descriptions.",
            "Snapshot schemas and review the diff when they change.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["jsonschema==4.22", "pytest==8.2"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["deepeval"],
        "related_glossary_slugs": ["tool-use", "function-calling-schema", "structured-output", "json-schema-enforcement"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why contract-test tools at all?", "answer": "An agent picks a tool from its schema and calls the handler. If the two drift — a required field the handler no longer reads, a renamed param — the agent fails at runtime with a confusing error. Contract tests move that failure to CI."},
            {"question": "jsonschema vs Pydantic for this?", "answer": "jsonschema validates the raw schema dict you ship to the model, which is what the agent actually sees. Pydantic is good when you generate schemas from typed models; then assert the generated schema round-trips. Use whichever matches your source of truth."},
            {"question": "What does additionalProperties: False buy me?", "answer": "Without it, a hallucinated or typo'd argument key (e.g. 'citi' instead of 'city') passes validation and reaches your handler as silent garbage. Locking it makes the model's mistake a validation error you can catch and retry."},
            {"question": "Does this need an API key?", "answer": "No. These tests exercise the schema/handler boundary only — no model call, no network. They run in milliseconds on every PR."},
        ],
        "github_url": "https://github.com/python-jsonschema/jsonschema",
        "meta_title": "Contract Tests for LLM Tool Schemas",
        "meta_description": "Catch tool-schema drift before an agent calls a broken tool: validate schemas, check required vs properties, test handlers. Pytest + jsonschema, no API key.",
    },
]
