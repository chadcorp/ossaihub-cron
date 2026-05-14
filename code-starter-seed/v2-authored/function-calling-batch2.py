"""Function calling starters — batch 2: streaming tools, multi-step orchestration."""

RECORDS = [
    {
        "slug": "openai-streaming-tool-calls",
        "title": "OpenAI Streaming With Tool Calls",
        "tldr": "Stream OpenAI responses while handling tool calls mid-stream. Yields partial assistant text + tool-call detection + tool results — UI sees text appear in real-time even when tools are invoked.",
        "category": "function-calling",
        "language": "python",
        "framework": "OpenAI SDK",
        "tags": ["openai", "streaming", "tool-calling", "ui"],
        "best_for_tags": ["chat-ui", "agents", "responsive-experience"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "Building a chat UI where the agent uses tools mid-response. Naïve implementations break streaming — this pattern preserves both streaming text and tool invocation.",
        "when_not_to_use": "Skip for batch/non-UI processing (streaming overhead). Skip for simple single-tool calls where streaming text doesn't matter.",
        "quick_start": "pip install openai && OPENAI_API_KEY=sk-... python streaming_tools.py",
        "full_code": '''"""OpenAI streaming + tool calls.

Stream pattern:
  1. Open stream with tools available
  2. Yield content chunks as they arrive
  3. When tool_call complete, pause stream, run tool, feed result back
  4. Resume stream with tool output appended to conversation
  5. Continue yielding until completion

This is more involved than non-streaming because tool_calls arrive in deltas
that must be assembled.
"""
from __future__ import annotations

import json
import os
from typing import Iterator

from openai import OpenAI

client = OpenAI()


TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    },
}]


def get_weather(location: str) -> dict:
    return {"location": location, "temp": 22, "condition": "sunny"}


TOOL_IMPL = {"get_weather": get_weather}


def stream_with_tools(user_message: str, *, model: str = "gpt-4o-mini") -> Iterator[dict]:
    """Yield events: {'type': 'text', 'content': '...'} or {'type': 'tool_call', 'name': ..., 'args': ..., 'result': ...}."""

    messages: list[dict] = [
        {"role": "user", "content": user_message},
    ]

    for _ in range(5):  # max iterations
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            stream=True,
        )

        # Accumulators
        assistant_text = ""
        tool_calls: list[dict] = []  # built up from deltas

        for chunk in stream:
            delta = chunk.choices[0].delta

            # Text content
            if delta.content:
                assistant_text += delta.content
                yield {"type": "text", "content": delta.content}

            # Tool call deltas (assembled incrementally)
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    # Extend list if needed
                    while len(tool_calls) <= idx:
                        tool_calls.append({"id": "", "name": "", "arguments": ""})
                    if tc_delta.id:
                        tool_calls[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls[idx]["name"] += tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls[idx]["arguments"] += tc_delta.function.arguments

        # Append assistant message
        assistant_msg = {"role": "assistant", "content": assistant_text or None}
        if tool_calls:
            assistant_msg["tool_calls"] = [
                {"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                for tc in tool_calls
            ]
        messages.append(assistant_msg)

        # If no tool calls, we're done
        if not tool_calls:
            return

        # Execute tools and feed results
        for tc in tool_calls:
            try:
                args = json.loads(tc["arguments"])
            except json.JSONDecodeError:
                args = {}
            fn = TOOL_IMPL.get(tc["name"])
            result = fn(**args) if fn else {"error": f"unknown tool {tc['name']}"}
            yield {"type": "tool_call", "name": tc["name"], "args": args, "result": result}
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, default=str),
            })

        # Loop: continue stream until completion without tool_calls


# ----------------- DEMO -----------------

if __name__ == "__main__":
    for event in stream_with_tools("What's the weather in Tokyo? Then summarize."):
        if event["type"] == "text":
            print(event["content"], end="", flush=True)
        elif event["type"] == "tool_call":
            print(f"\\n[tool_call: {event['name']}({event['args']}) → {event['result']}]")
    print()
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai",
            "export OPENAI_API_KEY=sk-...",
            "python streaming_tools.py",
        ],
        "variations": [
            {"label": "Async version", "description": "Use AsyncOpenAI.", "code_snippet": "from openai import AsyncOpenAI\\nclient = AsyncOpenAI()\\nasync for chunk in await client.chat.completions.create(..., stream=True):\\n    ..."},
            {"label": "SSE wrapper for HTTP", "description": "Wrap as Server-Sent Events for a web client.", "code_snippet": "# In FastAPI:\\n@app.post('/chat')\\ndef chat(): return StreamingResponse((f'data: {json.dumps(e)}\\\\n\\\\n' for e in stream_with_tools(msg)), media_type='text/event-stream')"},
            {"label": "Parallel tool execution", "description": "When multiple tool_calls arrive, run in parallel.", "code_snippet": "# Replace sequential for-loop over tool_calls with: results = asyncio.gather(*[run_tool_async(tc) for tc in tool_calls])"},
            {"label": "Vercel AI SDK style", "description": "Same pattern via the Vercel AI SDK.", "code_snippet": "# The Vercel AI SDK (JS/TS) handles this assembly automatically; use streamText with maxToolRoundtrips."},
        ],
        "common_errors": [
            {"error_text": "JSON parse error on tool arguments", "cause": "Stream was cut off mid-JSON.", "fix_snippet": "Verify the stream completed (check finish_reason). If 'length' (max_tokens), increase. If 'stop', JSON should be complete; investigate model output."},
            {"error_text": "Tool calls assembled with wrong arguments", "cause": "Index mismatch on delta accumulation.", "fix_snippet": "Starter handles indices correctly. If you've modified, ensure tool_calls list is sized by delta.index, not appended."},
            {"error_text": "First chunk of text never appears", "cause": "Buffering on client side or print without flush.", "fix_snippet": "Use flush=True on print; in HTTP context, disable buffering on the response."},
            {"error_text": "Infinite tool-call loop", "cause": "Tool returns trigger another tool call.", "fix_snippet": "Cap iterations (starter has 5). Also: check if tool results contain something the model interprets as a new question."},
        ],
        "production_checklist": [
            "Cap iterations; runaway tool loops are common.",
            "Stream chunks immediately; don't buffer client-side.",
            "Test resumption — if connection drops mid-stream, what happens?",
            "Tool errors should surface as 'tool_call' events with error field, not crash the stream.",
            "Log full conversation incl. tool results for debugging.",
            "Test with slow tools: stream should pause cleanly, not error.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["streaming", "tool-calling", "sse"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why is this harder than non-streaming?", "answer": "Tool calls arrive in deltas (name comes first, then arguments piece by piece). You must assemble them before executing. Non-streaming has the complete tool_calls list in one response."},
            {"question": "Does it work with Claude?", "answer": "Same pattern — Anthropic also streams tool_use blocks via deltas. The accumulation logic differs slightly; see the Claude streaming starter."},
            {"question": "Can I show the tool args as they're being typed?", "answer": "Technically yes — but typically you wait for the full args before executing. Showing partial JSON to users tends to confuse more than inform."},
        ],
        "github_url": "",
        "meta_title": "OpenAI Streaming With Tool Calls — Starter",
        "meta_description": "Stream OpenAI responses + handle tool calls mid-stream. Assembles delta tool_calls, pauses for execution, resumes streaming.",
    },
    {
        "slug": "tool-result-validation-loop",
        "title": "Tool Result Validation + Auto-Retry",
        "tldr": "After a tool returns, validate the result against expected schema. If invalid, give the model a corrected re-call prompt. Catches bad arguments + bad tool outputs before they propagate.",
        "category": "function-calling",
        "language": "python",
        "framework": "OpenAI SDK + Pydantic",
        "tags": ["validation", "retry", "tool-calling", "robustness"],
        "best_for_tags": ["production-agents", "reliable-tools", "agent-quality"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "When tool outputs vary in quality (third-party APIs, scraped data) and you want the agent to recover from bad data automatically without crashing the conversation.",
        "when_not_to_use": "Skip when tools are deterministic and trusted. Skip in latency-sensitive paths where the retry overhead matters.",
        "quick_start": "pip install openai pydantic && OPENAI_API_KEY=sk-... python validated_tools.py",
        "full_code": '''"""Tool-call validation loop.

For each tool result:
  1. Validate against expected schema (Pydantic).
  2. If invalid: format error back to model, ask for corrected call.
  3. Retry up to N times.
  4. If still invalid: surface error to user, don't crash.

Useful for tools that:
  - Hit third-party APIs with inconsistent shapes
  - Run user-provided code (e.g., SQL queries)
  - Compute heavily and may run out of time / return partial results
"""
from __future__ import annotations

import json
from typing import Any, Callable

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

client = OpenAI()


# ----------------- TOOL OUTPUT SCHEMAS -----------------

class WeatherResult(BaseModel):
    location: str
    temp_celsius: float = Field(ge=-100, le=100)
    condition: str
    humidity_pct: int | None = Field(default=None, ge=0, le=100)


class SearchResult(BaseModel):
    query: str
    results: list[dict] = Field(min_length=1, max_length=10)


# ----------------- TOOLS (may return inconsistent shapes!) -----------------

def fake_weather(location: str) -> dict:
    """Sometimes returns malformed data."""
    if "moon" in location.lower():
        return {"error": "no weather available on the moon"}
    return {"location": location, "temp_celsius": 22, "condition": "clear", "humidity_pct": 60}


def fake_search(query: str) -> dict:
    """Sometimes empty results."""
    if "kjdfgskldjfg" in query:
        return {"query": query, "results": []}  # invalid: min_length=1
    return {"query": query, "results": [{"title": "result 1"}]}


TOOL_REGISTRY: dict[str, tuple[Callable, type[BaseModel]]] = {
    "get_weather": (fake_weather, WeatherResult),
    "search": (fake_search, SearchResult),
}


# ----------------- VALIDATED EXECUTION -----------------

def execute_with_validation(tool_name: str, args: dict) -> dict:
    """Run tool, validate output. Returns {ok: bool, data: ..., error: ...}."""
    if tool_name not in TOOL_REGISTRY:
        return {"ok": False, "error": f"unknown tool {tool_name}"}
    fn, schema = TOOL_REGISTRY[tool_name]
    try:
        raw = fn(**args)
    except Exception as e:
        return {"ok": False, "error": f"tool execution failed: {e}"}
    try:
        validated = schema(**raw)
        return {"ok": True, "data": validated.model_dump()}
    except ValidationError as e:
        return {"ok": False, "error": f"validation error: {e.errors()}", "raw": raw}


# ----------------- AGENT LOOP WITH RETRY -----------------

TOOL_DEFINITIONS = [
    {"type": "function", "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]},
    }},
    {"type": "function", "function": {
        "name": "search",
        "description": "Search results for a query",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    }},
]


def run_agent(user_message: str, *, max_iters: int = 6, max_retries_per_tool: int = 2) -> str:
    messages = [{"role": "user", "content": user_message}]
    retries: dict[str, int] = {}  # per-tool-call retry count

    for _ in range(max_iters):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOL_DEFINITIONS,
            temperature=0,
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return msg.content

        messages.append(msg.model_dump())
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = execute_with_validation(tc.function.name, args)

            if result["ok"]:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result["data"]),
                })
            else:
                # Track retries for THIS specific tool call
                key = f"{tc.function.name}::{tc.function.arguments}"
                retries[key] = retries.get(key, 0) + 1
                if retries[key] > max_retries_per_tool:
                    # Give up; surface error
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps({
                            "error": "tool repeatedly returned invalid data",
                            "details": result.get("error"),
                        }),
                    })
                else:
                    # Retry by feeding error back
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps({
                            "validation_error": result.get("error"),
                            "raw_output": result.get("raw"),
                            "instruction": "Re-call the tool with corrected arguments OR pick a different tool. If you need user input, ask the user.",
                        }),
                    })
    return "ERROR: max iterations exceeded"


if __name__ == "__main__":
    # Normal case
    print(run_agent("What's the weather in Tokyo?"))
    # Error case — moon
    print(run_agent("What's the weather on the moon?"))
    # Empty result
    print(run_agent("Search for kjdfgskldjfg"))
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI client"},
            {"name": "pydantic", "version": ">=2.0", "purpose": "Tool output validation"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai pydantic",
            "export OPENAI_API_KEY=sk-...",
            "python validated_tools.py",
        ],
        "variations": [
            {"label": "Custom recovery prompts", "description": "Per-tool retry instructions.", "code_snippet": "# Map tool_name → retry_instruction; surface specific guidance for known failure modes."},
            {"label": "Validation alongside execution", "description": "Trigger validation in parallel.", "code_snippet": "# For slow tools, validate the schema in a separate worker; main loop can continue."},
            {"label": "Schema evolution", "description": "Accept old + new schemas.", "code_snippet": "# Try new_schema first; if fails, try old_schema; mark as deprecated."},
        ],
        "common_errors": [
            {"error_text": "Infinite retry loop", "cause": "Tool always returns invalid; model can't fix it.", "fix_snippet": "max_retries_per_tool caps it. After cap, surface error to user — don't keep retrying."},
            {"error_text": "ValidationError too cryptic for the model", "cause": "Pydantic errors are verbose.", "fix_snippet": "Format the error: extract field path + expected type; pass that. Model handles concrete error messages better."},
            {"error_text": "Model keeps making the same wrong call", "cause": "Error message not informative enough.", "fix_snippet": "Include `raw_output` so model sees what came back, not just that it was wrong. Often the model adjusts its NEXT tool choice based on this."},
            {"error_text": "Validation succeeds but semantics wrong", "cause": "Pydantic checks types, not meaning.", "fix_snippet": "Add custom validators (@field_validator) for semantic checks. Or do a second LLM validation pass for tools where it matters."},
        ],
        "production_checklist": [
            "Define schemas for every tool output; treat them as contracts.",
            "Cap retries; bound the cost.",
            "Log all validation failures; they show where tools or schemas need updating.",
            "Surface unrecoverable errors to user cleanly — don't crash the conversation.",
            "Test with deliberately-broken tools to verify recovery.",
            "Version schemas; tool updates may break them.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["openai==1.51.0", "pydantic==2.9.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["tool-validation", "agent-recovery"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why validate tool outputs?", "answer": "Real tools fail in surprising ways: third-party API returns null fields, scrapers get blocked, calculations overflow. Validation catches this BEFORE bad data corrupts the agent's reasoning."},
            {"question": "Doesn't this make agents brittle?", "answer": "Opposite — agents without validation silently propagate garbage. With it, garbage gets a clear error path. The agent (or user) sees the failure and can adapt."},
            {"question": "Cost of validation?", "answer": "Pydantic validation: microseconds. Retry loops: more LLM calls. The cost is in the retry, not the validation itself. Cap retries low (2-3)."},
        ],
        "github_url": "",
        "meta_title": "Tool Result Validation + Auto-Retry — Starter",
        "meta_description": "Validate tool outputs against Pydantic schemas; auto-retry with error feedback on failure. Robust agents that recover from bad tool data.",
    },
]
