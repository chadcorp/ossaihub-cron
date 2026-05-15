"""Function-calling starters — batch 3: parallel tools, structured retry, JSON-mode strict, multi-tool reasoning."""

RECORDS = [
    {
        "slug": "openai-parallel-tool-calls",
        "title": "OpenAI Parallel Tool Calls (Concurrent Execution)",
        "tldr": "GPT-4o emits multiple tool calls in ONE response when they're independent. Execute them concurrently for lower latency. Pattern + safety rails for production.",
        "category": "function-calling",
        "language": "python",
        "framework": "OpenAI Python SDK",
        "tags": ["openai", "parallel-tools", "function-calling", "concurrency"],
        "best_for_tags": ["agent-latency", "io-bound-tools", "production"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Your tools are mostly I/O (DB queries, API calls). Parallel execution can halve agent latency vs sequential. GPT-4o emits parallel calls when it recognizes independence.",
        "when_not_to_use": "Skip when tools depend on each other's results (set parallel_tool_calls=false). Skip if tools are CPU-heavy on the same machine (just thrashes).",
        "quick_start": "pip install openai && python parallel_tools.py",
        "full_code": '''"""OpenAI parallel tool calls + concurrent execution."""
from __future__ import annotations

import asyncio
import json
import os
from openai import AsyncOpenAI


client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])


# ----------------- TOOL IMPLEMENTATIONS (async I/O) -----------------

async def get_weather(location: str) -> dict:
    """Stub — pretend this is a real async HTTP call."""
    await asyncio.sleep(0.5)
    return {"location": location, "temp_c": 22, "conditions": "clear"}


async def get_air_quality(location: str) -> dict:
    await asyncio.sleep(0.4)
    return {"location": location, "aqi": 35, "category": "good"}


async def get_traffic(origin: str, destination: str) -> dict:
    await asyncio.sleep(0.6)
    return {"origin": origin, "destination": destination, "minutes": 18, "incidents": 0}


TOOL_REGISTRY = {
    "get_weather": get_weather,
    "get_air_quality": get_air_quality,
    "get_traffic": get_traffic,
}


# ----------------- TOOL DEFINITIONS -----------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location.",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_air_quality",
            "description": "Get current air quality index for a location.",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_traffic",
            "description": "Get traffic conditions between two locations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                },
                "required": ["origin", "destination"],
            },
        },
    },
]


# ----------------- EXECUTE PARALLEL -----------------

async def execute_tool_call(call) -> dict:
    """Execute one tool call; return {tool_call_id, content}."""
    name = call.function.name
    try:
        args = json.loads(call.function.arguments)
        fn = TOOL_REGISTRY.get(name)
        if not fn:
            return {"tool_call_id": call.id, "content": f"Unknown tool: {name}"}
        result = await fn(**args)
        return {"tool_call_id": call.id, "content": json.dumps(result)}
    except Exception as e:
        return {"tool_call_id": call.id, "content": f"Error: {e}"}


async def execute_parallel(tool_calls) -> list[dict]:
    """Run all tool calls concurrently."""
    return await asyncio.gather(*[execute_tool_call(c) for c in tool_calls])


# ----------------- AGENT LOOP -----------------

async def agent(user_message: str, max_iterations: int = 5):
    messages = [{"role": "user", "content": user_message}]

    for _ in range(max_iterations):
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
            parallel_tool_calls=True,  # default; set False to force sequential
            temperature=0.0,
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            return msg.content

        print(f"Executing {len(msg.tool_calls)} tool calls in parallel...")
        results = await execute_parallel(msg.tool_calls)
        for r in results:
            messages.append({"role": "tool", **r})

    return "Max iterations reached"


# ----------------- DEMO -----------------

if __name__ == "__main__":
    import time
    start = time.time()
    result = asyncio.run(agent(
        "What's the weather, air quality, and traffic from SFO to downtown San Francisco? Compare."
    ))
    print(f"\\nResult: {result}")
    print(f"Total: {time.time() - start:.2f}s")
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI SDK with parallel tools"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai",
            "export OPENAI_API_KEY=sk-...",
            "python parallel_tools.py",
            "Compare with parallel_tool_calls=False to see latency diff",
        ],
        "variations": [
            {"label": "Sequential when tools depend", "description": "Some workflows need ordering.", "code_snippet": "# Set parallel_tool_calls=False to force one tool at a time. Useful when tool B depends on tool A's output."},
            {"label": "With timeouts per tool", "description": "Cap each tool independently.", "code_snippet": "async def with_timeout(call):\\n    return await asyncio.wait_for(execute_tool_call(call), timeout=5)"},
            {"label": "Structured outputs (strict mode)", "description": "Guaranteed JSON-schema-conformant tool args.", "code_snippet": "TOOLS[0]['function']['strict'] = True  # OpenAI strict mode; args validated against schema before delivery"},
        ],
        "common_errors": [
            {"error_text": "Tool calls returned in wrong order", "cause": "Mismatched tool_call_id.", "fix_snippet": "Always pair tool result with its call's id. The order of 'tool' role messages doesn't matter; pairing does."},
            {"error_text": "Race condition on shared state", "cause": "Tools mutating same DB row in parallel.", "fix_snippet": "Tools should be PURE / IDEMPOTENT. If they must mutate, use DB-level locking. Or set parallel_tool_calls=False."},
            {"error_text": "Cost spike from parallel calls", "cause": "More tools called per turn.", "fix_snippet": "Each tool result goes back to model — more input tokens. Acceptable for IO-bound tools; surprise if you didn't expect parallel."},
            {"error_text": "One slow tool delays all others", "cause": "asyncio.gather waits for all.", "fix_snippet": "Set per-tool timeout. Or use asyncio.wait with FIRST_COMPLETED if you can act on partial results."},
        ],
        "production_checklist": [
            "Tools should be idempotent — parallel calls might retry.",
            "Set per-tool timeout to prevent one slow tool blocking all.",
            "Set parallel_tool_calls=False for tools with hidden dependencies.",
            "Monitor: avg tools per turn, parallel-execution latency vs sequential.",
            "Use strict mode (function strict: true) for guaranteed JSON args.",
            "Log all tool calls + results for debugging.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o", "gpt-4o-mini"],
            "library_versions": ["openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["openai"],
        "related_glossary_slugs": ["parallel-tool-calling", "function-calling"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "When does GPT-4o emit parallel calls?", "answer": "When it identifies independent tools. E.g., 'weather + traffic' are independent; 'login then fetch' is sequential. You can't FORCE parallel; you can DISABLE it."},
            {"question": "Same tool called multiple times in parallel?", "answer": "Yes — common for batch lookups. E.g., get_weather(SFO), get_weather(NYC), get_weather(SEA) all parallel. Make sure your tool implementation is reentrant."},
            {"question": "Anthropic / Gemini parallel tools?", "answer": "Anthropic: yes (since Claude 3.5). Gemini: limited support. Pattern works similarly across; check provider docs for parallel_tool_calls equivalent."},
            {"question": "Worth the complexity?", "answer": "Yes for I/O-heavy tools. 5 sequential 500ms tools = 2.5s. 5 parallel = 500ms. Halves typical agent latency. For CPU tools, less benefit (GIL)."},
        ],
        "github_url": "https://github.com/openai/openai-python",
        "meta_title": "OpenAI Parallel Tool Calls Starter",
        "meta_description": "OpenAI GPT-4o parallel tool calls with async concurrent execution. Halve agent latency. Production-grade safety rails.",
    },
    {
        "slug": "structured-outputs-strict-mode",
        "title": "OpenAI Structured Outputs (Strict JSON Schema)",
        "tldr": "OpenAI strict mode: guarantee LLM output matches a JSON schema. No more JSON-parse failures, no more 'forgot a field' errors. Pydantic-friendly.",
        "category": "function-calling",
        "language": "python",
        "framework": "OpenAI Python SDK",
        "tags": ["structured-output", "json-schema", "openai", "strict"],
        "best_for_tags": ["data-extraction", "production-reliability", "schema-driven"],
        "difficulty_tier": "beginner",
        "featured": True,
        "when_to_use": "Whenever you need GUARANTEED JSON output from an LLM. Forms, data extraction, classifications, structured tool args. Strict mode replaces hand-rolled JSON repair loops.",
        "when_not_to_use": "Skip for free-form text generation (no schema needed). Skip if you need fields the model can't reliably extract — strict only validates SHAPE, not CORRECTNESS.",
        "quick_start": "pip install openai pydantic && python strict_outputs.py",
        "full_code": '''"""OpenAI Structured Outputs in strict mode.

Two ways:
1. With response_format and a Pydantic model (for plain responses).
2. With tools and strict=true (for function-call-style outputs).
"""
from __future__ import annotations

import os
from enum import Enum
from typing import Literal
from openai import OpenAI
from pydantic import BaseModel, Field


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# ----------------- WAY 1: response_format with Pydantic -----------------

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TicketClassification(BaseModel):
    """Schema for support ticket classification."""
    category: Literal["billing", "technical", "general", "feedback"]
    priority: Priority
    summary: str = Field(..., max_length=200)
    requires_human: bool
    suggested_response: str = Field(..., max_length=500)


def classify_ticket(message: str) -> TicketClassification:
    """Guaranteed: response matches TicketClassification schema. No JSON-parse needed."""
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Classify the customer support ticket."},
            {"role": "user", "content": message},
        ],
        response_format=TicketClassification,
        temperature=0,
    )
    return response.choices[0].message.parsed  # already a TicketClassification instance


# ----------------- WAY 2: tools with strict=True -----------------

EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_invoice",
        "strict": True,  # strict mode
        "description": "Extract structured invoice data from email text.",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_number": {"type": "string"},
                "amount_usd": {"type": "number"},
                "due_date": {"type": "string", "description": "YYYY-MM-DD"},
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "amount_usd": {"type": "number"},
                        },
                        "required": ["description", "amount_usd"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["invoice_number", "amount_usd", "due_date", "line_items"],
            "additionalProperties": False,  # strict mode requires this
        },
    },
}


def extract_invoice(email_text: str) -> dict:
    """Strict tool call: args guaranteed to match schema."""
    import json
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Extract invoice data from emails."},
            {"role": "user", "content": email_text},
        ],
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "function", "function": {"name": "extract_invoice"}},
        temperature=0,
    )
    call = response.choices[0].message.tool_calls[0]
    return json.loads(call.function.arguments)


# ----------------- DEMO -----------------

if __name__ == "__main__":
    ticket = classify_ticket(
        "Hi, I was charged $99 twice in September for my subscription. Please refund one."
    )
    print(f"Category: {ticket.category}")
    print(f"Priority: {ticket.priority}")
    print(f"Summary: {ticket.summary}")
    print(f"Requires human: {ticket.requires_human}")
    print(f"Suggested reply: {ticket.suggested_response}\\n")

    invoice = extract_invoice(
        "Invoice #INV-2024-0042. Due: 2024-10-15. Total: $1,250. Line items: Setup $1,000, Hosting $250."
    )
    print(f"Extracted: {invoice}")
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI SDK with structured outputs"},
            {"name": "pydantic", "version": ">=2.0", "purpose": "Schema definitions"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install 'openai>=1.40' pydantic",
            "export OPENAI_API_KEY=sk-...",
            "python strict_outputs.py",
        ],
        "variations": [
            {"label": "Nested + recursive schemas", "description": "Strict supports deeply nested.", "code_snippet": "# Recursive types via refs; e.g. tree-structured data. Use Pydantic + .model_json_schema()"},
            {"label": "Streaming structured outputs", "description": "Stream + parse incrementally.", "code_snippet": "with client.beta.chat.completions.stream(...) as s:\\n    for event in s:\\n        if event.type == 'content.delta': print(event.parsed)  # partial valid object"},
            {"label": "Anthropic equivalent", "description": "Claude tool use with strict-ish schemas.", "code_snippet": "# Anthropic doesn't have official 'strict mode'; use prompt engineering + jsonschema validation post-hoc. Or use Instructor library which adds retry-on-validation."},
        ],
        "common_errors": [
            {"error_text": "Refusal: model couldn't generate matching output", "cause": "Schema impossible (e.g., requires field model can't infer).", "fix_snippet": "Check response.choices[0].message.refusal. Loosen schema (make field optional). Or rephrase prompt to enable inference."},
            {"error_text": "additionalProperties: false required", "cause": "Strict mode mandates closed objects.", "fix_snippet": "Every object schema needs additionalProperties: false. EVERY level — nested too. Use Pydantic to auto-generate."},
            {"error_text": "Required fields missing post-validation", "cause": "Strict mode requires ALL fields in 'required'.", "fix_snippet": "In strict mode, EVERY field must be in 'required'. For optional fields, use null union: {type: ['string', 'null']}."},
            {"error_text": "Slow first response (model warm-up)", "cause": "Strict mode compiles schema on first use.", "fix_snippet": "First call per schema is ~1s slower. Subsequent calls are normal speed. Pre-warm in production startup."},
        ],
        "production_checklist": [
            "Use strict mode for all extraction / classification tasks.",
            "Define schemas with Pydantic — easier to maintain + validate.",
            "Set additionalProperties: false at EVERY nested level.",
            "Use Literal / Enum for closed sets (categories, statuses).",
            "Handle refusal case — model may refuse on adversarial input.",
            "Pin model version — schema compilation behavior can change.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-2024-08-06", "gpt-4o-mini"],
            "library_versions": ["openai==1.51", "pydantic==2.9"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["openai", "pydantic"],
        "related_glossary_slugs": ["structured-output", "json-schema"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is strict mode really 100%?", "answer": "On supported models (gpt-4o-2024-08-06+), yes — output is GUARANTEED to match schema. The model can still REFUSE (returns null + refusal field), but it can't return malformed JSON."},
            {"question": "Performance impact?", "answer": "First call per schema ~1s slower (compile). Subsequent calls nearly identical to non-strict. Worth it for the reliability."},
            {"question": "Pydantic .parse vs raw schema?", "answer": ".parse is cleaner — gives you typed objects directly. Raw schema is needed if working outside Python. Both have same guarantees."},
            {"question": "What if I need free-form text WITH structure?", "answer": "Use response_format with a schema that has 'text': string + structured metadata fields. Get both."},
        ],
        "github_url": "https://github.com/openai/openai-python",
        "meta_title": "OpenAI Structured Outputs Strict Mode Starter",
        "meta_description": "OpenAI strict mode: guaranteed JSON-schema-conformant outputs. Pydantic integration, tools with strict=true, no more parse failures.",
    },
    {
        "slug": "tool-call-retry-with-validation",
        "title": "Tool Call Retry With Schema Validation",
        "tldr": "When non-strict-mode models return malformed tool args, retry with the error message in context. 3-tier retry: schema-validate → repair-prompt → fallback.",
        "category": "function-calling",
        "language": "python",
        "framework": "Custom + Pydantic",
        "tags": ["retry", "validation", "tool-use", "robustness"],
        "best_for_tags": ["non-openai-models", "claude", "open-source-llms"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Using Claude / Llama / Mistral or any model without strict mode. They sometimes emit JSON with subtle errors. This pattern self-heals by retrying with the validation error as context.",
        "when_not_to_use": "Skip if using OpenAI strict mode (no need). Skip for non-critical tools (just log + skip).",
        "quick_start": "pip install anthropic pydantic jsonschema && python tool_retry.py",
        "full_code": '''"""Tool-call retry with validation; works with any tool-calling model."""
from __future__ import annotations

import json
import os
from typing import Any
from anthropic import Anthropic
from pydantic import BaseModel, ValidationError


client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ----------------- TOOL ARG SCHEMA -----------------

class SearchArgs(BaseModel):
    query: str
    max_results: int = 10
    filters: dict[str, str] | None = None


# ----------------- TOOL DEFINITION (sent to model) -----------------

SEARCH_TOOL = {
    "name": "search",
    "description": "Search the knowledge base.",
    "input_schema": SearchArgs.model_json_schema(),
}


# ----------------- VALIDATE + RETRY -----------------

def validate_args(raw_args: dict) -> tuple[SearchArgs | None, str | None]:
    """Return (parsed, error). On success: (parsed, None). On failure: (None, error_msg)."""
    try:
        return SearchArgs(**raw_args), None
    except ValidationError as e:
        # Format clear error for the model
        details = []
        for err in e.errors():
            loc = ".".join(str(p) for p in err["loc"])
            details.append(f"  {loc}: {err['msg']} (got: {err.get('input', 'N/A')})")
        return None, "Validation errors:\\n" + "\\n".join(details)


def call_with_retry(prompt: str, max_retries: int = 3) -> SearchArgs:
    """Call model; if tool args invalid, retry with error in context."""
    messages = [{"role": "user", "content": prompt}]

    for attempt in range(max_retries + 1):
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            tools=[SEARCH_TOOL],
            messages=messages,
        )

        # Find the tool_use block
        tool_use = next((b for b in response.content if b.type == "tool_use"), None)
        if not tool_use:
            raise RuntimeError("Model didn't use the tool")

        parsed, error = validate_args(tool_use.input)
        if parsed is not None:
            print(f"✅ Valid on attempt {attempt + 1}")
            return parsed

        if attempt == max_retries:
            raise RuntimeError(f"Failed after {max_retries + 1} attempts. Last error: {error}")

        # Repair-prompt the model with the error
        print(f"⚠️  Attempt {attempt + 1} invalid: {error[:100]}")
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": f"Your tool args failed validation:\\n{error}\\n\\nPlease retry with corrected args.",
                "is_error": True,
            }],
        })

    raise RuntimeError("Unreachable")


# ----------------- DEMO -----------------

if __name__ == "__main__":
    result = call_with_retry(
        "Search for 'rate limiting best practices' — return 5 results filtered to recent docs."
    )
    print(f"Parsed args: {result.model_dump()}")
''',
        "dependencies": [
            {"name": "anthropic", "version": ">=0.36", "purpose": "Claude SDK"},
            {"name": "pydantic", "version": ">=2.0", "purpose": "Schema validation"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Anthropic key", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "pip install anthropic pydantic",
            "export ANTHROPIC_API_KEY=sk-ant-...",
            "python tool_retry.py",
        ],
        "variations": [
            {"label": "With Instructor library", "description": "Library does the retry for you.", "code_snippet": "# pip install instructor; instructor.from_anthropic(client) → .messages.create with response_model=SearchArgs. Retries auto."},
            {"label": "Per-field repair", "description": "Only repair invalid fields, keep valid.", "code_snippet": "# Track which fields validated; in retry-prompt include only the invalid ones for repair. Faster + more accurate."},
            {"label": "Fallback to default args", "description": "After N retries, use safe defaults.", "code_snippet": "try: result = call_with_retry(...)\\nexcept RuntimeError: result = SearchArgs(query=user_query, max_results=5)"},
        ],
        "common_errors": [
            {"error_text": "Infinite retry loop", "cause": "Model keeps making the same error.", "fix_snippet": "Cap max_retries (3-5). Include FULL error context in repair prompt. If still failing, fall back to defaults."},
            {"error_text": "Repair-prompt too long", "cause": "Each retry adds tokens.", "fix_snippet": "Limit retries to 3. Drop old history per retry; keep only system + latest user prompt + latest tool call attempt."},
            {"error_text": "Validates but semantically wrong", "cause": "Schema doesn't check business rules.", "fix_snippet": "Add validators to Pydantic (model_validator) for cross-field constraints. e.g., 'max_results > 0', 'date ranges valid'."},
            {"error_text": "Different errors each retry", "cause": "Non-determinism.", "fix_snippet": "Set temperature=0 in retries. Or pin random seed if model supports it."},
        ],
        "production_checklist": [
            "Cap max_retries to avoid runaway cost.",
            "Log every retry + reason — surface patterns.",
            "Add custom validators for business rules (not just schema).",
            "Have a fallback for when retries fail (defaults, human, error).",
            "Pin temperature=0 for deterministic retries.",
            "Consider Instructor library — handles this pattern out-of-the-box.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-5-sonnet-20241022"],
            "library_versions": ["anthropic==0.36", "pydantic==2.9"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["anthropic", "instructor"],
        "related_glossary_slugs": ["tool-use", "validation"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why not just use Instructor?", "answer": "Instructor does this pattern out-of-the-box (and adds more). Use it for production. The code in this starter is for understanding what's happening under the hood."},
            {"question": "How does it compare to OpenAI strict mode?", "answer": "OpenAI strict: no retry needed; guaranteed first time. This pattern: works with ANY model. For non-OpenAI, this is the only way to get reliable structured tool calls."},
            {"question": "Cost of retries?", "answer": "Each retry is a full LLM call. 1 retry typical, 2-3 occasionally. Budget ~1.5x cost vs no-retry. For cheap models (haiku), negligible."},
            {"question": "What about partial repair?", "answer": "Yes — see variations. If 4/5 fields are valid, include only the bad one in repair prompt. Smaller context = faster + cheaper retries."},
        ],
        "github_url": "https://github.com/jxnl/instructor",
        "meta_title": "Tool Call Retry With Validation Starter",
        "meta_description": "Self-healing tool calls: validate against schema, retry with error context for non-strict models (Claude, Llama, Mistral).",
    },
    {
        "slug": "multi-tool-reasoning-chain",
        "title": "Multi-Tool Reasoning Chain (Plan-And-Execute)",
        "tldr": "Agent plans a multi-step tool sequence FIRST, then executes. Better than greedy one-step-at-a-time for complex tasks where order matters and steps can be planned upfront.",
        "category": "function-calling",
        "language": "python",
        "framework": "OpenAI / Anthropic",
        "tags": ["plan-and-execute", "reasoning", "multi-tool", "agents"],
        "best_for_tags": ["complex-tasks", "ordered-workflows", "research-agents"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Complex tasks with 4+ steps where step order matters and steps depend on each other. Planning upfront often beats greedy execution for these. Combines well with ReAct for re-planning.",
        "when_not_to_use": "Skip for simple 1-2 step tasks (overhead). Skip for unpredictable environments where the plan won't survive contact with reality (use pure ReAct).",
        "quick_start": "pip install openai pydantic && python plan_execute.py",
        "full_code": '''"""Plan-and-Execute pattern: model produces a plan; executor runs it; re-plan if needed."""
from __future__ import annotations

import json
import os
from openai import OpenAI
from pydantic import BaseModel, Field


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# ----------------- PLAN SCHEMA -----------------

class PlanStep(BaseModel):
    step_number: int
    tool: str
    args: dict
    expected_outcome: str = Field(..., max_length=200)
    depends_on: list[int] = Field(default_factory=list)


class Plan(BaseModel):
    goal: str = Field(..., max_length=200)
    steps: list[PlanStep]
    final_synthesis: str = Field(..., max_length=200)


# ----------------- TOOLS (stub) -----------------

def search(query: str) -> str:
    return f"[stub search results for '{query}']"


def fetch_url(url: str) -> str:
    return f"[stub content of {url}]"


def summarize(text: str) -> str:
    return f"[stub summary: {text[:50]}...]"


TOOLS = {"search": search, "fetch_url": fetch_url, "summarize": summarize}


TOOL_SCHEMAS = [
    {"name": "search", "description": "Web search.", "input": {"query": "string"}},
    {"name": "fetch_url", "description": "Fetch a URL.", "input": {"url": "string"}},
    {"name": "summarize", "description": "Summarize text.", "input": {"text": "string"}},
]


# ----------------- PLAN -----------------

def make_plan(user_goal: str) -> Plan:
    """LLM generates the full execution plan upfront."""
    tools_str = json.dumps(TOOL_SCHEMAS, indent=2)
    prompt = f"""Goal: {user_goal}

Available tools:
{tools_str}

Produce a STEP-BY-STEP plan. Each step uses one tool. Steps can depend on prior steps (reference outputs).
Output JSON matching the Plan schema."""

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You produce step-by-step plans for agent execution."},
            {"role": "user", "content": prompt},
        ],
        response_format=Plan,
        temperature=0,
    )
    return response.choices[0].message.parsed


# ----------------- EXECUTE -----------------

def execute_plan(plan: Plan) -> dict:
    """Run the plan; pass outputs forward via dependencies."""
    outputs: dict[int, str] = {}

    for step in plan.steps:
        print(f"\\n--- Step {step.step_number}: {step.tool} ---")
        print(f"Expected: {step.expected_outcome}")

        # Resolve {step_N} placeholders in args from prior outputs
        resolved_args = {}
        for k, v in step.args.items():
            if isinstance(v, str) and v.startswith("{step_") and v.endswith("}"):
                ref = int(v[6:-1])
                resolved_args[k] = outputs.get(ref, v)
            else:
                resolved_args[k] = v

        # Execute
        fn = TOOLS.get(step.tool)
        if not fn:
            outputs[step.step_number] = f"Error: unknown tool {step.tool}"
            continue
        try:
            result = fn(**resolved_args)
            outputs[step.step_number] = result
            print(f"Output: {result[:100]}")
        except Exception as e:
            outputs[step.step_number] = f"Error: {e}"
            print(f"FAILED: {e}")

    return outputs


# ----------------- SYNTHESIZE FINAL -----------------

def synthesize(plan: Plan, outputs: dict) -> str:
    context = "\\n".join(f"Step {i}: {o}" for i, o in outputs.items())
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"Synthesize the final answer for: {plan.goal}"},
            {"role": "user", "content": f"Step outputs:\\n{context}\\n\\nFinal synthesis goal: {plan.final_synthesis}"},
        ],
        temperature=0,
    )
    return response.choices[0].message.content


# ----------------- DEMO -----------------

if __name__ == "__main__":
    goal = "Research the top 3 papers on retrieval-augmented generation from 2024 and produce a 100-word summary of common themes."
    plan = make_plan(goal)
    print(f"PLAN: {plan.model_dump_json(indent=2)}")

    outputs = execute_plan(plan)
    final = synthesize(plan, outputs)
    print(f"\\n=== FINAL ===\\n{final}")
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "Planning + synthesis LLM"},
            {"name": "pydantic", "version": ">=2.0", "purpose": "Plan schema"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install 'openai>=1.40' pydantic",
            "export OPENAI_API_KEY=sk-...",
            "Replace stub tools with real ones",
            "python plan_execute.py",
        ],
        "variations": [
            {"label": "Re-plan on failure", "description": "If a step fails, re-plan rest.", "code_snippet": "# After step failure: call make_plan again with updated context. Used for unpredictable environments."},
            {"label": "Parallel-where-possible", "description": "Execute independent steps in parallel.", "code_snippet": "# Use depends_on graph; topo-sort; asyncio.gather for steps without deps. Halves latency for fan-out tasks."},
            {"label": "Plan validation pass", "description": "LLM checks own plan before executing.", "code_snippet": "# After make_plan: ask LLM 'is this plan sound? what's missing?' — refine before execute. Catches obvious errors cheap."},
        ],
        "common_errors": [
            {"error_text": "Plan steps reference non-existent outputs", "cause": "Model hallucinated dependency.", "fix_snippet": "Validate depends_on refs against step_number list before executing. Raise + re-plan."},
            {"error_text": "Plan is too long (15+ steps)", "cause": "Goal too broad.", "fix_snippet": "Cap plan length (e.g., max_steps=8 in prompt). For longer tasks, decompose into sub-goals; plan each."},
            {"error_text": "Args don't match tool signature", "cause": "Schema only describes; doesn't enforce.", "fix_snippet": "Use Pydantic per-tool args. Validate before execution. Or use OpenAI tools API with strict mode for the plan-emission step."},
            {"error_text": "Plan optimistic; reality fails halfway", "cause": "Plan didn't account for failures.", "fix_snippet": "Either re-plan on failure OR include fallback steps in plan. Or use ReAct for more interactive control."},
        ],
        "production_checklist": [
            "Validate plan before execution (depends_on refs, tool names, args).",
            "Cap plan length to prevent runaway.",
            "Log each step + output for debugging.",
            "Have a re-plan mechanism for failures.",
            "For unpredictable environments, prefer ReAct over plan-and-execute.",
            "Synthesize final answer with FULL step outputs in context.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o", "gpt-4o-mini"],
            "library_versions": ["openai==1.51", "pydantic==2.9"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["openai", "langgraph"],
        "related_glossary_slugs": ["plan-and-execute", "react"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Plan-and-execute vs ReAct?", "answer": "ReAct: greedy, one step at a time, reactive. Plan-and-execute: full plan upfront, sequential. P&E better for predictable tasks; ReAct for exploratory."},
            {"question": "How big should plans get?", "answer": "5-8 steps typical. Past 12, the plan becomes unreliable. Decompose into sub-goals or use a hierarchical planner."},
            {"question": "Can plans be revised mid-execution?", "answer": "Yes — re-planning is a known pattern (Plan-and-Solve, ReWoo). On failure or surprise, generate a new plan from current state."},
            {"question": "Compare to LangGraph?", "answer": "LangGraph is more general (any state machine). Plan-and-Execute is a specific PATTERN you can implement in LangGraph (one planner node, one executor node, one synthesis node)."},
        ],
        "github_url": "",
        "meta_title": "Multi-Tool Reasoning Chain Starter — Plan And Execute",
        "meta_description": "Plan-and-Execute agent pattern: model produces multi-step plan, executor runs it with dependencies, synthesis LLM produces final answer.",
    },
]
