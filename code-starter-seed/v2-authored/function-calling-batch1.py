"""Function/tool calling starters — OpenAI, Anthropic, JSON schema validation."""

RECORDS = [
    {
        "slug": "openai-function-calling-parallel",
        "title": "OpenAI Parallel Function Calling With Validation",
        "tldr": "OpenAI's parallel tool calling pattern with Pydantic-validated arguments, automatic retry on validation failures, and explicit handling of the ‘no tool needed’ case. ~100 lines of production-grade scaffolding.",
        "category": "function-calling",
        "language": "python",
        "framework": "OpenAI SDK",
        "tags": ["openai", "function-calling", "parallel", "pydantic"],
        "best_for_tags": ["production-tools", "structured-actions", "agents"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When you need the model to call one or more tools per turn with strict argument validation. Pydantic schemas catch type mismatches before your tool functions run.",
        "when_not_to_use": "Skip for simple yes/no decisions (just use response_format=json_object). Skip if your provider isn't OpenAI-compatible; Anthropic uses a similar but distinct API.",
        "quick_start": "pip install openai pydantic && OPENAI_API_KEY=sk-... python parallel_tools.py",
        "full_code": '''"""Parallel function calling with Pydantic validation.

OpenAI may return multiple tool_calls in one assistant message. We:
  1. Validate each call's arguments against a Pydantic schema.
  2. Dispatch to the matching Python function.
  3. Return results in matching tool_call_id order.
  4. Let the model continue until it stops calling tools (final answer).
"""
from __future__ import annotations

import json
import os
from typing import Any, Callable

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

client = OpenAI()


# ---- Tool schemas (Pydantic) ----

class GetWeatherArgs(BaseModel):
    location: str = Field(description="City and country, e.g., 'Lisbon, PT'")
    unit: str = Field(default="celsius", description="celsius or fahrenheit")


class SearchProductsArgs(BaseModel):
    query: str = Field(description="Search keywords")
    max_price: float | None = Field(default=None, description="Max price filter")
    in_stock_only: bool = Field(default=True)


# ---- Tool implementations ----

def get_weather(args: GetWeatherArgs) -> dict:
    # Stub: replace with real API call
    return {"location": args.location, "temp": 22, "unit": args.unit, "condition": "clear"}


def search_products(args: SearchProductsArgs) -> list[dict]:
    # Stub
    return [{"name": "Widget Pro", "price": 19.99, "in_stock": True}]


# ---- Tool registry ----

TOOLS: dict[str, tuple[type[BaseModel], Callable]] = {
    "get_weather": (GetWeatherArgs, get_weather),
    "search_products": (SearchProductsArgs, search_products),
}


def pydantic_to_openai_tool(name: str, schema_cls: type[BaseModel], description: str) -> dict:
    """Convert a Pydantic model to OpenAI tool format."""
    schema = schema_cls.model_json_schema()
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": schema,
        },
    }


TOOL_DESCRIPTIONS = {
    "get_weather": "Get current weather for a city. Use only when the user asks about weather.",
    "search_products": "Search the product catalog. Use when the user wants to find/buy something.",
}


def build_tool_specs() -> list[dict]:
    return [
        pydantic_to_openai_tool(name, schema_cls, TOOL_DESCRIPTIONS[name])
        for name, (schema_cls, _) in TOOLS.items()
    ]


# ---- Main loop ----

def chat(user_message: str, *, model: str = "gpt-4o-mini", max_iters: int = 5) -> str:
    messages: list[dict] = [
        {"role": "system", "content": "You are a helpful assistant. Use tools when relevant."},
        {"role": "user", "content": user_message},
    ]
    tools = build_tool_specs()

    for it in range(max_iters):
        resp = client.chat.completions.create(
            model=model, messages=messages, tools=tools, temperature=0
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            return msg.content

        # Append assistant's tool-call message
        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
        })

        # Dispatch all tool calls (parallel-call shape)
        for tc in msg.tool_calls:
            name = tc.function.name
            schema_cls, fn = TOOLS.get(name, (None, None))
            if not schema_cls:
                tool_result = {"error": f"Unknown tool: {name}"}
            else:
                try:
                    args = schema_cls.model_validate_json(tc.function.arguments)
                    tool_result = fn(args)
                except ValidationError as e:
                    tool_result = {"error": "ValidationError", "details": e.errors()}
                except Exception as e:
                    tool_result = {"error": str(e)}

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(tool_result, default=str),
            })

    return "ERROR: max iterations exceeded"


if __name__ == "__main__":
    print(chat("What's the weather in Tokyo and Lisbon? Also find me widgets under $30."))
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI client"},
            {"name": "pydantic", "version": ">=2.0", "purpose": "Schema validation"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI API key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai pydantic",
            "export OPENAI_API_KEY=sk-...",
            "python parallel_tools.py",
        ],
        "variations": [
            {
                "label": "Streaming with tool calls",
                "description": "Stream the assistant's reply; assemble tool_calls from deltas.",
                "code_snippet": "stream = client.chat.completions.create(..., stream=True)\\nfor chunk in stream:\\n    if chunk.choices[0].delta.tool_calls:\\n        # accumulate; emit on chunk.choices[0].finish_reason='tool_calls'",
            },
            {
                "label": "Strict mode",
                "description": "Enable strict JSON schema enforcement.",
                "code_snippet": "tool_spec['function']['strict'] = True\\n# Then parameters must use additionalProperties=False and required for all fields.",
            },
            {
                "label": "Force a specific tool",
                "description": "Make the model call a particular tool.",
                "code_snippet": "tool_choice={'type': 'function', 'function': {'name': 'get_weather'}}",
            },
            {
                "label": "Disable parallel calls",
                "description": "Some models / cases benefit from sequential.",
                "code_snippet": "parallel_tool_calls=False",
            },
        ],
        "common_errors": [
            {
                "error_text": "openai.BadRequestError: Invalid 'tools[0].function.parameters'",
                "cause": "Pydantic schema includes Python-specific types (e.g., 'date', custom classes) not in JSON Schema.",
                "fix_snippet": "Use only JSON-Schema-compatible types: str, int, float, bool, list, dict, datetime as ISO string. Add json_schema_extra hints where needed.",
            },
            {
                "error_text": "ValidationError: location is required",
                "cause": "Model called the tool without all required args.",
                "fix_snippet": "Starter returns the validation error to the model; it usually retries correctly. If persistent, sharpen tool descriptions to make required args obvious.",
            },
            {
                "error_text": "Tool result not appearing in final answer",
                "cause": "Forgot to append role=tool with tool_call_id matching.",
                "fix_snippet": "Each tool_call needs a corresponding tool message with matching tool_call_id BEFORE the next API call.",
            },
            {
                "error_text": "Model never calls the tool",
                "cause": "Description doesn't make it clear when to use this tool.",
                "fix_snippet": "Improve description: include 'Use when the user asks about X' and 'Do not use when ...'. Specific guidance beats abstract.",
            },
        ],
        "production_checklist": [
            "Add timeouts to tool function calls; one slow tool blocks the whole reply.",
            "Validate ALL tool inputs with Pydantic — don't trust the model's JSON.",
            "Set max_iters based on observed p99 of converging conversations.",
            "Cache deterministic tools (same input → same output) per conversation.",
            "Log tool name + arg hash for every call; tool selection drift is the most common production bug.",
            "Use 'strict' mode in OpenAI tool schemas when supported; it eliminates malformed JSON.",
            "Test with fast and slow models; tool behavior shifts between gpt-4o-mini and gpt-4o.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["openai==1.51.0", "pydantic==2.9.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["function-calling", "tool-use", "json-schema"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "What's parallel function calling?",
                "answer": "The model can return multiple tool_calls in a single response. The starter dispatches all of them and feeds all results back together — fewer round-trips than sequential.",
            },
            {
                "question": "Pydantic or raw JSON schema?",
                "answer": "Pydantic for both validation and schema generation. Less duplication; one source of truth for tool args.",
            },
            {
                "question": "When should I use strict mode?",
                "answer": "When malformed JSON has been a problem. Strict mode (with required+additionalProperties=False) eliminates most issues. It's more restrictive on what schemas are allowed.",
            },
            {
                "question": "How is this different from LangChain's bind_tools?",
                "answer": "Same underlying OpenAI API. This starter is closer to the metal — fewer dependencies, less indirection. Use it when you want full control or are minimizing deps.",
            },
        ],
        "github_url": "https://github.com/openai/openai-python",
        "meta_title": "OpenAI Parallel Function Calling Starter",
        "meta_description": "Production-shape OpenAI tool calling: parallel dispatch, Pydantic-validated args, validation-error retries, strict mode hook.",
    },
    {
        "slug": "anthropic-tool-use-claude",
        "title": "Anthropic Claude Tool Use With Streaming",
        "tldr": "Claude's tool-use pattern with streaming — handles tool_use blocks and tool_result blocks correctly, supports parallel tool calls in a single response, and streams the assistant's text as it arrives.",
        "category": "function-calling",
        "language": "python",
        "framework": "Anthropic SDK",
        "tags": ["anthropic", "claude", "tool-use", "streaming"],
        "best_for_tags": ["claude-agents", "streaming-ui", "tool-use"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When building with Claude and need tool use plus a responsive UI. Streaming lets you show text as Claude reasons, then pause and dispatch tools.",
        "when_not_to_use": "Skip for batch processing where streaming is overhead. Skip if you need OpenAI-compatible API; Claude's response shape differs significantly.",
        "quick_start": "pip install anthropic && ANTHROPIC_API_KEY=sk-ant-... python claude_tools.py",
        "full_code": '''"""Claude tool use with streaming.

Differences vs OpenAI:
  - Tools defined as {'name', 'description', 'input_schema'} (not nested 'function').
  - Assistant response has 'content' as a list of blocks (text + tool_use).
  - Tool results passed in a user message with content=[{'type': 'tool_result', ...}].
"""
from __future__ import annotations

import json
import os
from typing import Any, Callable

from anthropic import Anthropic

client = Anthropic()

TOOLS_SCHEMA = [
    {
        "name": "get_weather",
        "description": "Get current weather for a city. Use only when the user asks about weather.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City and country"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"},
            },
            "required": ["location"],
        },
    },
    {
        "name": "search_products",
        "description": "Search the product catalog.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_price": {"type": "number"},
                "in_stock_only": {"type": "boolean", "default": True},
            },
            "required": ["query"],
        },
    },
]


def get_weather(location: str, unit: str = "celsius") -> dict:
    return {"location": location, "temp": 22, "unit": unit, "condition": "clear"}


def search_products(query: str, max_price: float | None = None, in_stock_only: bool = True):
    return [{"name": "Widget Pro", "price": 19.99, "in_stock": True}]


TOOLS: dict[str, Callable] = {
    "get_weather": get_weather,
    "search_products": search_products,
}


def chat(user_message: str, *, model: str = "claude-3-7-sonnet-latest", max_iters: int = 5) -> str:
    messages: list[dict] = [{"role": "user", "content": user_message}]

    for _ in range(max_iters):
        print("\\n--- assistant ---")
        assistant_content: list[dict] = []  # We'll reconstruct from stream events.
        with client.messages.stream(
            model=model,
            max_tokens=1024,
            tools=TOOLS_SCHEMA,
            messages=messages,
        ) as stream:
            for event in stream:
                if event.type == "content_block_start":
                    block = event.content_block
                    if block.type == "tool_use":
                        print(f"\\n[tool_use: {block.name}]", end=" ", flush=True)
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": {},  # Filled in delta events
                        })
                    else:
                        assistant_content.append({"type": "text", "text": ""})
                elif event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        assistant_content[-1]["text"] += delta.text
                        print(delta.text, end="", flush=True)
                    elif delta.type == "input_json_delta":
                        # tool input arrives as partial JSON
                        existing = assistant_content[-1].get("_partial_json", "")
                        assistant_content[-1]["_partial_json"] = existing + delta.partial_json
            # finalize tool_use inputs
            for block in assistant_content:
                if block["type"] == "tool_use" and "_partial_json" in block:
                    try:
                        block["input"] = json.loads(block["_partial_json"])
                    except json.JSONDecodeError:
                        block["input"] = {}
                    block.pop("_partial_json", None)

        messages.append({"role": "assistant", "content": assistant_content})

        tool_use_blocks = [b for b in assistant_content if b["type"] == "tool_use"]
        if not tool_use_blocks:
            # No more tool calls; assistant finalized.
            return "".join(b["text"] for b in assistant_content if b["type"] == "text")

        # Dispatch tools, build tool_result content
        tool_results = []
        for block in tool_use_blocks:
            fn = TOOLS.get(block["name"])
            try:
                result = fn(**block["input"]) if fn else {"error": f"Unknown tool {block['name']}"}
            except Exception as e:
                result = {"error": str(e)}
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block["id"],
                "content": json.dumps(result, default=str),
            })

        messages.append({"role": "user", "content": tool_results})

    return "ERROR: max iters exceeded"


if __name__ == "__main__":
    print("\\n=== final ===")
    print(chat("What's the weather in Tokyo? And find widgets under $30."))
''',
        "dependencies": [
            {"name": "anthropic", "version": ">=0.39", "purpose": "Anthropic SDK"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Anthropic API key", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "pip install anthropic",
            "export ANTHROPIC_API_KEY=sk-ant-...",
            "python claude_tools.py",
        ],
        "variations": [
            {
                "label": "Tool choice forced",
                "description": "Require a specific tool.",
                "code_snippet": "tool_choice={'type': 'tool', 'name': 'get_weather'}",
            },
            {
                "label": "Disable parallel tools",
                "description": "Force sequential tool calls.",
                "code_snippet": "tool_choice={'type': 'auto', 'disable_parallel_tool_use': True}",
            },
            {
                "label": "With prompt caching",
                "description": "Cache TOOLS_SCHEMA + system prompt for cost savings.",
                "code_snippet": "system=[{'type': 'text', 'text': 'You are...', 'cache_control': {'type': 'ephemeral'}}]",
            },
            {
                "label": "Synchronous (no streaming)",
                "description": "If you don't need to show progress.",
                "code_snippet": "resp = client.messages.create(model=..., tools=..., messages=..., max_tokens=...)\\nassistant_content = [b.model_dump() for b in resp.content]",
            },
        ],
        "common_errors": [
            {
                "error_text": "BadRequestError: tool_use_id ... does not match",
                "cause": "tool_result has wrong tool_use_id.",
                "fix_snippet": "Every tool_use block returned by Claude has an 'id'. The corresponding tool_result must use that exact id in 'tool_use_id'.",
            },
            {
                "error_text": "BadRequestError: input_schema is not valid JSON Schema",
                "cause": "Schema uses unsupported keywords (e.g., 'definitions').",
                "fix_snippet": "Use a subset: type, properties, required, enum, default, description, items. Don't use $ref or definitions.",
            },
            {
                "error_text": "Tool input is empty / partial JSON in stream",
                "cause": "Forgot to accumulate input_json_delta events.",
                "fix_snippet": "Starter handles this; the key is parsing the assembled partial_json string when content_block_stop arrives (or after the stream ends).",
            },
            {
                "error_text": "Model returns plain text instead of using tools",
                "cause": "Tool descriptions vague or system prompt encourages explanation.",
                "fix_snippet": "Sharpen tool descriptions. System prompt: 'When a tool can answer the question, use it; do not explain what you would do — just do it.'",
            },
        ],
        "production_checklist": [
            "Use prompt caching on TOOLS_SCHEMA — Claude charges full price every call without it.",
            "Stream in UI-facing flows; batch in pipelines.",
            "Validate tool_use.input with Pydantic before dispatching (Claude can produce arg drift).",
            "Set max_tokens per response; Claude doesn't auto-cap.",
            "Use claude-3-haiku for simple tools; claude-3-7-sonnet for complex reasoning. Cost difference is significant.",
            "Log every tool_use block; tool selection is where most issues happen.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-7-sonnet-latest", "claude-3-5-haiku-latest"],
            "library_versions": ["anthropic==0.39.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["anthropic"],
        "related_glossary_slugs": ["tool-use", "function-calling", "streaming"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why is the response shape different from OpenAI?",
                "answer": "Claude uses content blocks (text, tool_use, image) as a typed array; OpenAI uses string content + separate tool_calls. Claude's model maps better to multi-modal inputs.",
            },
            {
                "question": "How do I pass tool errors back?",
                "answer": "Wrap the error in the tool_result content; add 'is_error': True to the tool_result block for explicit signaling. Claude will try to recover or ask the user.",
            },
            {
                "question": "Does Claude support strict mode like OpenAI?",
                "answer": "Not currently. Validate with Pydantic on your side. Claude's tool-use is generally robust without strict mode.",
            },
            {
                "question": "Can I mix tools and vision in the same call?",
                "answer": "Yes. Include image blocks in the user message alongside text; Claude can both read images and call tools in the same turn.",
            },
        ],
        "github_url": "https://github.com/anthropics/anthropic-sdk-python",
        "meta_title": "Anthropic Claude Tool Use with Streaming",
        "meta_description": "Claude tool_use pattern with streaming: assemble tool_use blocks from delta events, dispatch, and continue. Production-shape.",
    },
    {
        "slug": "instructor-structured-extraction",
        "title": "Structured Extraction With Instructor (Pydantic + Retry)",
        "tldr": "Use the `instructor` library to coerce LLM output into Pydantic models with automatic retries on validation failure. Cleaner than raw JSON mode for any non-trivial schema.",
        "category": "function-calling",
        "language": "python",
        "framework": "Instructor",
        "tags": ["instructor", "pydantic", "structured-output", "extraction"],
        "best_for_tags": ["data-extraction", "structured-output", "retries"],
        "difficulty_tier": "beginner",
        "featured": True,
        "when_to_use": "Whenever you need the LLM output as a specific Pydantic model — extraction tasks, classifier output, multi-field structured responses. Instructor handles validation + retries.",
        "when_not_to_use": "Skip for streaming text output (instructor streams partial models, but most consumers want the final). Skip when you need very tight control over prompt structure.",
        "quick_start": "pip install instructor openai && OPENAI_API_KEY=sk-... python extract.py",
        "full_code": '''"""Structured extraction with Instructor.

- Pydantic schema = response format.
- Instructor auto-retries on ValidationError (up to max_retries times).
- Works across providers (OpenAI, Anthropic, Gemini, Ollama, ...) — same code,
  swap client.
"""
from __future__ import annotations

import os
from typing import Literal

import instructor
from openai import OpenAI
from pydantic import BaseModel, Field, EmailStr, field_validator


# ---- Define the target shape ----

class Address(BaseModel):
    street: str
    city: str
    state: str = Field(description="2-letter US state code")
    zip_code: str

    @field_validator("state")
    @classmethod
    def state_uppercase(cls, v: str) -> str:
        v = v.upper()
        if len(v) != 2:
            raise ValueError("state must be a 2-letter code")
        return v


class Customer(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    address: Address | None = None
    customer_type: Literal["individual", "business"] = "individual"
    notes: str | None = Field(default=None, description="Anything the system should know")


# ---- Set up Instructor ----

client = instructor.from_openai(OpenAI())


def extract_customer(unstructured_text: str) -> Customer:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=Customer,
        max_retries=3,
        messages=[
            {"role": "system", "content":
                "Extract customer details from the user's message. "
                "Leave fields null if not mentioned. Do not invent values."},
            {"role": "user", "content": unstructured_text},
        ],
    )


if __name__ == "__main__":
    text = """Hey, can you set up an account for Acme Corp?
    Main contact is Jane Doe (jane@acme.example). They're at
    123 Main St, Springfield IL, 62701. Phone is 555-0100.
    Note: they need NET-60 payment terms."""
    cust = extract_customer(text)
    print(cust.model_dump_json(indent=2))
''',
        "dependencies": [
            {"name": "instructor", "version": ">=1.5", "purpose": "Structured output for LLM responses"},
            {"name": "openai", "version": ">=1.40", "purpose": "Underlying client (or anthropic, etc.)"},
            {"name": "pydantic", "version": ">=2.0", "purpose": "Schema definitions"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI API key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install instructor openai pydantic",
            "export OPENAI_API_KEY=sk-...",
            "python extract.py",
        ],
        "variations": [
            {
                "label": "Anthropic instead of OpenAI",
                "description": "Same code, different client.",
                "code_snippet": "from anthropic import Anthropic\\nclient = instructor.from_anthropic(Anthropic())\\n# rest unchanged",
            },
            {
                "label": "Streaming partial models",
                "description": "Get partial fills as they generate.",
                "code_snippet": "for partial in client.chat.completions.create_partial(model=..., response_model=Customer, messages=...):\\n    print(partial.model_dump())",
            },
            {
                "label": "List of items",
                "description": "Extract a list of records.",
                "code_snippet": "from typing import Iterable\\nfor item in client.chat.completions.create_iterable(model=..., response_model=LineItem, messages=...):\\n    process(item)",
            },
            {
                "label": "Local LLM via Ollama",
                "description": "Use a self-hosted model.",
                "code_snippet": "client = instructor.from_openai(OpenAI(base_url='http://localhost:11434/v1', api_key='ollama'), mode=instructor.Mode.JSON)\\n# Smaller models may need higher max_retries.",
            },
        ],
        "common_errors": [
            {
                "error_text": "InstructorRetryException: Max retries exceeded",
                "cause": "Model can't satisfy the schema (validator too strict or context insufficient).",
                "fix_snippet": "Inspect the last attempt's output. Common: 1) relax validators, 2) make schema fields Optional, 3) give the model more context in the system prompt.",
            },
            {
                "error_text": "ValidationError: value_error.email",
                "cause": "Source text has malformed email.",
                "fix_snippet": "Either accept str | None and validate downstream, or sharpen the system prompt: ‘leave email null if no clear valid email present.’",
            },
            {
                "error_text": "Schema fields unfilled when info is present",
                "cause": "System prompt too lax; model is conservative.",
                "fix_snippet": "Add explicit instruction: ‘fill every field for which evidence exists in the source.’ Use Field(description=...) to hint at what counts as evidence.",
            },
            {
                "error_text": "Schema with deeply nested models fails for small models",
                "cause": "Smaller models struggle with multi-level nesting.",
                "fix_snippet": "Flatten the schema for smaller models, or switch to a stronger model. Use the largest model your latency/cost budget allows for complex extraction.",
            },
        ],
        "production_checklist": [
            "Pin instructor and openai versions — both evolve quickly.",
            "Log every retry; recurring retries on the same shape signals schema/prompt mismatch.",
            "Set max_retries based on stakes; 1 for non-critical, 3 for important, 5 for must-extract.",
            "Use validators (field_validator) to catch obvious errors without LLM round-trips.",
            "For list extraction, prefer create_iterable to streaming — easier to handle partial results.",
            "Test the schema with edge cases: empty strings, mixed languages, redacted PII.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o", "claude-3-7-sonnet"],
            "library_versions": ["instructor==1.5.2", "openai==1.51.0", "pydantic==2.9.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["instructor"],
        "related_glossary_slugs": ["structured-output", "function-calling", "pydantic"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Instructor vs raw OpenAI JSON mode?",
                "answer": "Instructor wraps JSON mode + Pydantic + automatic retry. Raw JSON mode requires you to manage all three manually. Instructor wins for any non-trivial schema.",
            },
            {
                "question": "Does it work with local models?",
                "answer": "Yes — via Ollama's OpenAI-compatible API. Smaller models need higher max_retries and simpler schemas; larger ones (Llama 3.1 70B) work nearly as well as gpt-4o.",
            },
            {
                "question": "What about provider lock-in?",
                "answer": "Instructor wraps OpenAI, Anthropic, Gemini, Cohere, Groq, Ollama, etc. Your schema code stays the same; you swap the client.",
            },
            {
                "question": "Can I use this for classification?",
                "answer": "Yes — Literal[...] types are perfect for classification. response_model=Category where Category: Literal['a', 'b', 'c'].",
            },
        ],
        "github_url": "https://github.com/jxnl/instructor",
        "meta_title": "Structured Extraction with Instructor — Starter",
        "meta_description": "Pydantic-based LLM extraction with automatic validation retries — clean schema → guaranteed structured output across providers.",
    },
    {
        "slug": "json-mode-with-schema-validation",
        "title": "Pure JSON Mode With Schema Validation",
        "tldr": "Minimal-dependency structured output: use OpenAI's response_format=json_object plus a jsonschema validator. Same effect as Instructor in 30 lines, no extra library.",
        "category": "function-calling",
        "language": "python",
        "framework": "OpenAI SDK + jsonschema",
        "tags": ["json-mode", "structured-output", "validation"],
        "best_for_tags": ["minimal-deps", "no-framework", "simple-extraction"],
        "difficulty_tier": "beginner",
        "featured": False,
        "when_to_use": "When you want JSON output, have a JSON Schema already, and don't want to add Pydantic + Instructor. Common in services where the schema lives in a config file already.",
        "when_not_to_use": "Skip for complex nested schemas — Pydantic/Instructor's better validators and retry logic pay off. Skip when you need streaming partial structured output.",
        "quick_start": "pip install openai jsonschema && OPENAI_API_KEY=sk-... python json_mode.py",
        "full_code": '''"""Pure JSON mode with jsonschema validation and manual retries.

This is the lowest-dependency way to get structured output.
For complex schemas or rich validation, use Instructor instead.
"""
from __future__ import annotations

import json
import os

from jsonschema import Draft7Validator
from openai import OpenAI

client = OpenAI()

# Define your JSON Schema (could load from file)
INVOICE_SCHEMA = {
    "type": "object",
    "required": ["vendor", "total", "currency", "line_items"],
    "additionalProperties": False,
    "properties": {
        "vendor": {"type": "string"},
        "invoice_date": {"type": "string", "format": "date"},
        "total": {"type": "number"},
        "currency": {"type": "string", "enum": ["USD", "EUR", "GBP", "JPY", "CAD"]},
        "line_items": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["description", "amount"],
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "amount": {"type": "number"},
                },
            },
        },
    },
}

validator = Draft7Validator(INVOICE_SCHEMA)


def extract(text: str, *, max_retries: int = 3) -> dict:
    messages = [
        {"role": "system", "content":
            "You extract invoice data into JSON matching this schema:\\n"
            + json.dumps(INVOICE_SCHEMA, indent=2)
            + "\\n\\nReturn ONLY valid JSON, no prose."},
        {"role": "user", "content": text},
    ]

    last_error = None
    for attempt in range(max_retries):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
        raw = resp.choices[0].message.content
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            last_error = f"JSON parse error: {e}"
        else:
            errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
            if not errors:
                return data
            last_error = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:3])

        # Retry with feedback
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": f"That output failed validation: {last_error}. "
                       f"Return JSON matching the schema."
        })

    raise RuntimeError(f"Failed to produce valid JSON after {max_retries} retries: {last_error}")


if __name__ == "__main__":
    text = """Invoice from Acme Corp, 2026-05-10. Subtotal $234.50.
    1 widget at $19.99, 2 thingamajigs at $107.25 each."""
    print(json.dumps(extract(text), indent=2))
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI client"},
            {"name": "jsonschema", "version": ">=4.20", "purpose": "JSON Schema Draft 7 validator"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI API key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai jsonschema",
            "export OPENAI_API_KEY=sk-...",
            "python json_mode.py",
        ],
        "variations": [
            {
                "label": "Use response_format with strict json_schema",
                "description": "OpenAI's enforced structured outputs (gpt-4o+ models).",
                "code_snippet": "response_format={\\n    'type': 'json_schema',\\n    'json_schema': {'name': 'invoice', 'schema': INVOICE_SCHEMA, 'strict': True}\\n}\\n# When strict=True, model guarantees valid JSON matching schema.",
            },
            {
                "label": "Load schema from file",
                "description": "Schema lives outside code.",
                "code_snippet": "INVOICE_SCHEMA = json.loads(Path('schemas/invoice.schema.json').read_text())",
            },
            {
                "label": "With Anthropic",
                "description": "Anthropic doesn't have JSON mode; use a system-prompted equivalent.",
                "code_snippet": "client.messages.create(model='claude-3-7-sonnet-latest', system='Return only valid JSON...', messages=...)\\n# parse + validate same as starter.",
            },
        ],
        "common_errors": [
            {
                "error_text": "json.JSONDecodeError",
                "cause": "Model returned markdown-wrapped JSON or partial output.",
                "fix_snippet": "Strip markdown fences: raw = raw.strip().removeprefix('```json').removesuffix('```'). For gpt-4o, use the strict json_schema variant to eliminate this entirely.",
            },
            {
                "error_text": "jsonschema validation: ['line_items']: too few items",
                "cause": "Model didn't extract line items from the source text.",
                "fix_snippet": "Either relax minItems or improve prompt: ‘list every individual charge as a line item, even if the source only shows a total.’",
            },
            {
                "error_text": "Validation: enum mismatch on currency",
                "cause": "Source text used a currency outside the enum.",
                "fix_snippet": "Either expand the enum or treat unrecognized currency as ‘USD’ with a flag in another field. Don't widen the enum globally for a single edge case.",
            },
            {
                "error_text": "Model output uses null when schema disallows it",
                "cause": "Schema specifies a type but model wrote null.",
                "fix_snippet": "Use type: ['string', 'null'] explicitly in JSON Schema to allow null.",
            },
        ],
        "production_checklist": [
            "If using gpt-4o+, prefer json_schema strict mode — eliminates parse failures.",
            "Version your schemas; changes can silently break downstream consumers.",
            "Log the raw model output on validation failure; needed for debugging schema drift.",
            "Cap max_retries — don't loop infinitely on impossible schemas.",
            "Make validation errors specific in the retry message; ‘invalid’ alone isn't helpful.",
            "Test the schema against real source text variations; cover edge cases.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["openai==1.51.0", "jsonschema==4.23.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["json-mode", "structured-output", "json-schema"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "When should I use json_schema strict mode vs json_object?",
                "answer": "Strict json_schema (gpt-4o+) GUARANTEES valid output matching schema — no parse/validation retries needed. json_object only guarantees valid JSON, not matching shape. Use strict mode when available.",
            },
            {
                "question": "Why not just always use Instructor?",
                "answer": "If your schema already exists as JSON Schema (e.g., OpenAPI spec, JSON file in repo), instructor requires translating to Pydantic. Pure JSON mode skips that step.",
            },
            {
                "question": "Can I stream partial JSON?",
                "answer": "Technically yes (stream + concat), but parsing partials requires a streaming JSON parser. Use Instructor's create_partial if you need streaming structured output.",
            },
            {
                "question": "How do I handle multi-language extraction?",
                "answer": "Schema doesn't change — but make the system prompt explicit about source language(s). The model handles translation+extraction in one call when prompted.",
            },
        ],
        "github_url": "",
        "meta_title": "Pure JSON Mode With Schema Validation — Starter",
        "meta_description": "Minimal-dependency structured output: OpenAI JSON mode + jsonschema validation + retry-with-feedback. ~30 lines, no Pydantic.",
    },
]
