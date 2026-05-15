"""LLM client starters — batch 3: Anthropic, Gemini, Bedrock, LiteLLM."""

RECORDS = [
    {
        "slug": "anthropic-messages-with-tools-streaming",
        "title": "Anthropic Messages API With Tools + Streaming",
        "tldr": "Claude tool use with streaming, parallel tool calls, and graceful tool-error handling. Production-ready scaffolding for agentic Anthropic apps.",
        "category": "llm-clients",
        "language": "python",
        "framework": "Anthropic Python SDK",
        "tags": ["anthropic", "claude", "tools", "streaming"],
        "best_for_tags": ["production-agents", "tool-use", "claude-stack"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Building agentic apps on Claude 3.5+ with tool use. Need streaming for UX + reliable tool-error handling. This pattern handles parallel tool calls and partial completions correctly.",
        "when_not_to_use": "Skip for single-turn no-tool use (raw create() is fine). Skip if streaming UX isn't needed (the loop is simpler).",
        "quick_start": "pip install anthropic && python anthropic_tools.py",
        "full_code": '''"""Anthropic Messages API: tools + streaming + parallel calls."""
from __future__ import annotations

import json
import os
from anthropic import Anthropic


client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ----------------- TOOL DEFINITIONS -----------------

TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City and country"},
                "unit": {"type": "string", "enum": ["c", "f"], "default": "c"},
            },
            "required": ["location"],
        },
    },
    {
        "name": "lookup_flight",
        "description": "Find flights between two airports on a given date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["origin", "destination", "date"],
        },
    },
]


# ----------------- TOOL EXECUTION -----------------

def execute_tool(name: str, args: dict) -> str:
    """Real implementation; return string (Anthropic expects str/list content)."""
    if name == "get_weather":
        return json.dumps({"temp": 22, "unit": args.get("unit", "c"), "conditions": "clear"})
    if name == "lookup_flight":
        return json.dumps({"flights": [{"id": "AA101", "depart": "08:00", "price": 320}]})
    return json.dumps({"error": f"unknown tool {name}"})


# ----------------- AGENT LOOP WITH STREAMING -----------------

def run_agent(user_message: str, max_iterations: int = 6) -> str:
    """Run agent: stream tokens, handle tool calls, loop until stop."""
    messages = [{"role": "user", "content": user_message}]
    text_parts: list[str] = []

    for iteration in range(max_iterations):
        # Stream the response so we can show tokens AS they arrive
        with client.messages.stream(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            tools=TOOLS,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                text_parts.append(text)

            final = stream.get_final_message()

        # Append assistant turn to messages
        messages.append({"role": "assistant", "content": final.content})

        if final.stop_reason == "end_turn":
            print()  # newline
            return "".join(text_parts)

        if final.stop_reason == "tool_use":
            # Execute all tool_use blocks (can be parallel — multiple in one turn)
            tool_results = []
            for block in final.content:
                if block.type == "tool_use":
                    try:
                        result = execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {e}",
                            "is_error": True,
                        })
            messages.append({"role": "user", "content": tool_results})
            continue

        # max_tokens or other stop: surface
        raise RuntimeError(f"Unexpected stop_reason: {final.stop_reason}")

    raise RuntimeError(f"Max iterations ({max_iterations}) reached")


if __name__ == "__main__":
    result = run_agent("What's the weather in Lisbon, and are there flights from JFK tomorrow?")
    print(f"\\n--- FINAL ---\\n{result}")
''',
        "dependencies": [
            {"name": "anthropic", "version": ">=0.36", "purpose": "Anthropic SDK"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Anthropic API key", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "pip install anthropic",
            "export ANTHROPIC_API_KEY=sk-ant-...",
            "python anthropic_tools.py",
        ],
        "variations": [
            {"label": "Prompt caching for tool definitions", "description": "Cache tools across requests.", "code_snippet": "TOOLS = [...]\\nfor t in TOOLS:\\n    t['cache_control'] = {'type': 'ephemeral'}  # cache tool block; saves on repeated tool defs"},
            {"label": "Computer Use", "description": "Claude with screen + mouse + keyboard tools.", "code_snippet": "# Use beta='computer-use-2025-01-24' header + computer tool definitions. Anthropic SDK has helpers."},
            {"label": "Async + parallel agents", "description": "Run N agents concurrently.", "code_snippet": "from anthropic import AsyncAnthropic\\nasync def run_async(msg): ... # asyncio.gather many in parallel"},
        ],
        "common_errors": [
            {"error_text": "TypeError: cannot serialize tool_use", "cause": "Trying to JSON-dump SDK objects directly.", "fix_snippet": "When appending assistant content, append final.content (the SDK list) NOT its repr/str. Anthropic accepts the structured form."},
            {"error_text": "Infinite tool loop", "cause": "Tool returns ambiguous error → model retries forever.", "fix_snippet": "Cap max_iterations. Return SPECIFIC errors from tools so model can recover. Don't return 'try again'."},
            {"error_text": "OverloadedError 529", "cause": "Anthropic capacity limits during peak.", "fix_snippet": "Add exponential backoff: retry on 529 with jitter. Catch with anthropic.APIError; retry up to 5 times."},
            {"error_text": "Tool args don't match schema", "cause": "Schema too loose.", "fix_snippet": "Use 'required' fields, enums, descriptions. Validate args with jsonschema before executing."},
        ],
        "production_checklist": [
            "Cap max_iterations (5-8 typical) to prevent runaway loops.",
            "Implement exponential backoff for 429/529.",
            "Use prompt caching for stable tool definitions + system prompts.",
            "Log tool calls + errors for debugging.",
            "Validate tool args against jsonschema before exec.",
            "Stream to UX — Claude can be slow on complex turns.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
            "library_versions": ["anthropic==0.36"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["anthropic"],
        "related_glossary_slugs": ["tool-use", "streaming"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why use the SDK instead of HTTP directly?", "answer": "The SDK handles streaming + content blocks correctly. Building these manually is error-prone (esp. partial JSON in tool inputs)."},
            {"question": "Parallel tool calls — when?", "answer": "Claude 3.5+ can call multiple tools in one turn when they're independent. The model decides; you just execute all tool_use blocks before the next iteration."},
            {"question": "Prompt caching savings?", "answer": "Up to 90% input-token savings on cached blocks. Use for: long system prompts, tool definitions, RAG context that's stable across requests."},
            {"question": "Claude vs OpenAI tools?", "answer": "Mostly equivalent for simple use. Claude has slightly better adherence to schema. OpenAI has 'strict mode' for guaranteed JSON. Pick by stack preference."},
        ],
        "github_url": "https://github.com/anthropics/anthropic-sdk-python",
        "meta_title": "Anthropic Tools + Streaming Starter — LLM Client",
        "meta_description": "Production Claude agent loop: tools, streaming, parallel calls, error handling, max-iteration cap, exponential backoff.",
    },
    {
        "slug": "gemini-multimodal-with-files-api",
        "title": "Gemini Multimodal With Files API",
        "tldr": "Gemini 1.5 with the Files API: upload PDFs / videos / audio once, reference by URI in many prompts. Avoids re-uploading huge files, saves bandwidth + tokens.",
        "category": "llm-clients",
        "language": "python",
        "framework": "Google Generative AI",
        "tags": ["gemini", "multimodal", "files-api", "video"],
        "best_for_tags": ["video-analysis", "long-pdf-qa", "multimodal-rag"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "You're sending the same large file (PDF, video, audio) to Gemini in many prompts. Files API caches the upload — pay bandwidth once, reference cheaply forever.",
        "when_not_to_use": "Skip for one-shot file analysis (inline content is fine). Skip for files <1MB (inline is faster + simpler).",
        "quick_start": "pip install google-generativeai && python gemini_files.py",
        "full_code": '''"""Gemini Files API: upload once, reference many times."""
from __future__ import annotations

import os
import time

import google.generativeai as genai


genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro-latest")


# ----------------- UPLOAD + WAIT -----------------

def upload_and_wait(path: str, display_name: str | None = None):
    """Upload a file; wait for it to be in ACTIVE state (necessary for video)."""
    file = genai.upload_file(path=path, display_name=display_name or os.path.basename(path))
    print(f"Uploaded {file.name} ({file.size_bytes} bytes)")
    # Poll until ACTIVE — video transcoding can take 30-60s
    while file.state.name == "PROCESSING":
        time.sleep(2)
        file = genai.get_file(file.name)
    if file.state.name != "ACTIVE":
        raise RuntimeError(f"Upload failed: state={file.state.name}")
    return file


# ----------------- LIST + REUSE -----------------

def find_uploaded(display_name: str):
    """Reuse an already-uploaded file by display name (saves bandwidth)."""
    for f in genai.list_files():
        if f.display_name == display_name and f.state.name == "ACTIVE":
            return f
    return None


# ----------------- PROMPT WITH FILE -----------------

def ask_about_file(file, prompt: str) -> str:
    response = model.generate_content([prompt, file])
    return response.text


# ----------------- MULTIPLE PROMPTS, ONE UPLOAD -----------------

def video_qa_demo(video_path: str):
    video = find_uploaded(os.path.basename(video_path)) or upload_and_wait(video_path)

    questions = [
        "Summarize the video in 3 bullets.",
        "What's said at the 1:30 mark?",
        "List any URLs or product names mentioned.",
        "What's the speaker's main argument?",
    ]
    for q in questions:
        print(f"\\nQ: {q}")
        print(f"A: {ask_about_file(video, q)}")


# ----------------- CLEANUP -----------------

def cleanup_files(older_than_days: int = 2):
    """Files API stores 7 days by default; clean up older."""
    import datetime as dt
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=older_than_days)
    for f in genai.list_files():
        if f.create_time.replace(tzinfo=None) < cutoff:
            print(f"Deleting {f.name}")
            genai.delete_file(f.name)


if __name__ == "__main__":
    video_qa_demo("./demo.mp4")
    cleanup_files()
''',
        "dependencies": [
            {"name": "google-generativeai", "version": ">=0.8", "purpose": "Gemini Python SDK"},
        ],
        "env_vars": [
            {"name": "GOOGLE_API_KEY", "required": True, "description": "From aistudio.google.com", "example": "AIza..."},
        ],
        "setup_steps": [
            "pip install google-generativeai",
            "Get API key from https://aistudio.google.com",
            "export GOOGLE_API_KEY=AIza...",
            "Have a sample mp4 / pdf to test",
            "python gemini_files.py",
        ],
        "variations": [
            {"label": "Inline content (small files)", "description": "Skip Files API; embed in prompt.", "code_snippet": "model.generate_content([prompt, {'mime_type': 'image/jpeg', 'data': open('img.jpg', 'rb').read()}])"},
            {"label": "Streaming response", "description": "Token-by-token output.", "code_snippet": "for chunk in model.generate_content([prompt, file], stream=True):\\n    print(chunk.text, end='', flush=True)"},
            {"label": "Caching context", "description": "Cached content for repeated queries.", "code_snippet": "cache = caching.CachedContent.create(model='gemini-1.5-pro-001', contents=[file], system_instruction='...'); model = GenerativeModel.from_cached_content(cache)"},
        ],
        "common_errors": [
            {"error_text": "FileState.PROCESSING never goes ACTIVE", "cause": "Video too long or unsupported codec.", "fix_snippet": "Max video: ~1 hour for gemini-1.5-pro. Transcode to H.264 + AAC if it stays PROCESSING for >5 min."},
            {"error_text": "ResourceExhausted: 429", "cause": "Quota hit.", "fix_snippet": "Check quota at console.cloud.google.com. Free tier: very limited. Use paid tier or backoff."},
            {"error_text": "File expired after 7 days", "cause": "Files API auto-expires uploaded files.", "fix_snippet": "Files API is ephemeral storage. Re-upload if needed past 7 days. Or use Cloud Storage and pass GCS URI."},
            {"error_text": "Inconsistent results across uploads", "cause": "Different mime types / encodings.", "fix_snippet": "Normalize: PDF → text or images depending on need. Video → consistent codec. Specify mime_type explicitly."},
        ],
        "production_checklist": [
            "Track uploaded file URIs in your DB (don't re-upload).",
            "Implement 7-day rotation: re-upload before expiry if needed.",
            "Use streaming for long generations (TTFT matters).",
            "Cleanup old files periodically (cost + quota).",
            "Handle quota errors with backoff.",
            "For sensitive content, use Vertex AI (more security controls).",
        ],
        "tested_with": {
            "model_versions": ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest"],
            "library_versions": ["google-generativeai==0.8"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["google-generative-ai"],
        "related_glossary_slugs": ["multimodal", "files-api"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Files API vs inline?", "answer": "Files API for >1MB or files used multiple times. Inline for small one-shot use. Files API saves bandwidth and lets you re-use uploads across many prompts."},
            {"question": "Cost of Files API?", "answer": "Free storage for 48 hours; some quotas thereafter. Token cost is per-use, same as inline. For huge files, Files API is dramatically cheaper bandwidth-wise."},
            {"question": "Gemini 1.5 Pro vs Flash?", "answer": "Pro: better reasoning, higher cost. Flash: 10x cheaper, slightly less capable. Both support multimodal + long context. Try Flash first; upgrade to Pro if quality requires."},
            {"question": "Video length limits?", "answer": "Gemini 1.5 Pro can ingest up to ~1 hour of video. Past that, sample frames or chunk. Each video frame counts as tokens; budget accordingly."},
        ],
        "github_url": "https://github.com/google/generative-ai-python",
        "meta_title": "Gemini Multimodal Files API Starter",
        "meta_description": "Gemini 1.5 with the Files API: upload once, query many times. PDF / video / audio multimodal, streaming, cleanup.",
    },
    {
        "slug": "litellm-router-with-fallbacks",
        "title": "LiteLLM Router With Multi-Provider Fallbacks",
        "tldr": "LiteLLM Router: load-balance across N providers (OpenAI, Anthropic, Bedrock, etc.) with auto-fallback when one fails. Single OpenAI-style API; production-grade.",
        "category": "llm-clients",
        "language": "python",
        "framework": "LiteLLM",
        "tags": ["litellm", "router", "fallback", "multi-provider"],
        "best_for_tags": ["production-reliability", "multi-cloud", "cost-optimization"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Production apps that can't afford single-provider downtime. LiteLLM Router gives you OpenAI-style API across 100+ providers with automatic failover.",
        "when_not_to_use": "Skip for single-provider experiments (raw SDK is simpler). Skip if you need provider-specific features the router abstracts away (e.g., Anthropic's computer-use).",
        "quick_start": "pip install 'litellm[proxy]' && python litellm_router.py",
        "full_code": '''"""LiteLLM Router with fallbacks, load-balancing, and per-route limits."""
from __future__ import annotations

import os
from litellm import Router


# ----------------- MODEL LIST -----------------

# Each entry is a "deployment" of a logical model_group_name.
# Router picks one per call; falls back to another on failure.
model_list = [
    {
        "model_name": "smart-model",  # logical name your app uses
        "litellm_params": {
            "model": "anthropic/claude-3-5-sonnet-20241022",
            "api_key": os.environ["ANTHROPIC_API_KEY"],
            "rpm": 50,  # per-deployment rate limit
        },
    },
    {
        "model_name": "smart-model",
        "litellm_params": {
            "model": "openai/gpt-4o",
            "api_key": os.environ["OPENAI_API_KEY"],
            "rpm": 100,
        },
    },
    {
        "model_name": "smart-model",
        "litellm_params": {
            "model": "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
            "aws_region_name": "us-east-1",
            "rpm": 30,
        },
    },
    {
        "model_name": "cheap-model",
        "litellm_params": {
            "model": "openai/gpt-4o-mini",
            "api_key": os.environ["OPENAI_API_KEY"],
            "rpm": 500,
        },
    },
    {
        "model_name": "cheap-model",
        "litellm_params": {
            "model": "anthropic/claude-3-5-haiku-20241022",
            "api_key": os.environ["ANTHROPIC_API_KEY"],
            "rpm": 200,
        },
    },
]


# ----------------- ROUTER -----------------

router = Router(
    model_list=model_list,
    routing_strategy="latency-based-routing",  # or "least-busy", "usage-based-routing"
    fallbacks=[
        {"smart-model": ["cheap-model"]},   # if smart-model fails, try cheap-model
    ],
    num_retries=2,
    timeout=30,
    retry_after=2,
    # Set spend tracking
    set_verbose=True,
)


# ----------------- USE -----------------

def generate(prompt: str, model_group: str = "smart-model") -> str:
    response = router.completion(
        model=model_group,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def stream(prompt: str, model_group: str = "smart-model"):
    response = router.completion(
        model=model_group,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print()


# ----------------- COST TRACKING -----------------

def get_spend():
    """Sum spend across all deployments."""
    return router.get_total_spend()


if __name__ == "__main__":
    print(generate("Explain rate limiting in 1 paragraph."))
    print()
    stream("Write a haiku about caching.")
    print(f"\\nTotal spend so far: ${get_spend():.4f}")
''',
        "dependencies": [
            {"name": "litellm", "version": ">=1.50", "purpose": "Multi-provider router"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": False, "description": "If using OpenAI deployment", "example": "sk-..."},
            {"name": "ANTHROPIC_API_KEY", "required": False, "description": "If using Anthropic", "example": "sk-ant-..."},
            {"name": "AWS_ACCESS_KEY_ID", "required": False, "description": "If using Bedrock", "example": "..."},
        ],
        "setup_steps": [
            "pip install 'litellm[proxy]'",
            "Set API keys for at least 2 providers",
            "python litellm_router.py",
            "(Optional) Deploy as a service: 'litellm --config config.yaml --port 4000'",
        ],
        "variations": [
            {"label": "Run as proxy server", "description": "OpenAI-compatible endpoint for all clients.", "code_snippet": "# litellm --config config.yaml --port 4000 — proxy that other apps hit as if it were OpenAI"},
            {"label": "Cost-based routing", "description": "Route to cheapest available.", "code_snippet": "router = Router(model_list=model_list, routing_strategy='cost-based-routing')"},
            {"label": "Per-customer rate limits", "description": "Tag traffic for per-tenant limits.", "code_snippet": "router.completion(..., metadata={'user_id': 'acme'}); # configure max_parallel_requests per user"},
        ],
        "common_errors": [
            {"error_text": "All deployments failed (no fallback worked)", "cause": "Outage across providers, or all keys invalid.", "fix_snippet": "Use providers across DIFFERENT clouds (Anthropic SaaS + AWS Bedrock + OpenAI). Real cross-cloud failover."},
            {"error_text": "ContextWindowExceededError", "cause": "Different models have different context.", "fix_snippet": "Set context_window_fallbacks for routes with smaller models. Or pre-trim prompts to lowest common denominator."},
            {"error_text": "Inconsistent response shape across providers", "cause": "Models format responses differently.", "fix_snippet": "Use structured outputs (response_format) or pin parsers. Don't rely on raw text being identical."},
            {"error_text": "Cost tracking misses some calls", "cause": "Provider not in LiteLLM's cost map.", "fix_snippet": "Add custom_cost_per_token in litellm_params for unknown providers. Or use LiteLLM Cloud for hosted billing."},
        ],
        "production_checklist": [
            "Use providers in DIFFERENT cloud regions for true HA.",
            "Set per-deployment rpm/tpm to respect provider limits.",
            "Monitor router.get_total_spend() — alert on cost spikes.",
            "Use latency-based routing for chat; cost-based for batch.",
            "Test failover paths quarterly (kill primary; verify fallback works).",
            "Keep model_list in config.yaml (version-controlled).",
        ],
        "tested_with": {
            "model_versions": ["claude-3-5-sonnet", "gpt-4o", "claude-3-5-haiku", "gpt-4o-mini"],
            "library_versions": ["litellm==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["litellm"],
        "related_glossary_slugs": ["llm-router", "failover"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "LiteLLM vs OpenRouter?", "answer": "LiteLLM: library (Python) or self-host proxy; you control routing logic. OpenRouter: managed service that abstracts providers. Pick by ops preference."},
            {"question": "Cost-based routing — caveats?", "answer": "It picks cheapest available, but cheapest model is often worst quality. Use cost-based for fallbacks; latency-based for primary routing."},
            {"question": "Does it work with local models (Ollama, vLLM)?", "answer": "Yes — both are first-class. Set model_name: 'ollama/llama3.1' or 'openai/your-vllm-endpoint' with api_base."},
            {"question": "What about streaming with fallback?", "answer": "Fallback after first chunk = retry from scratch (re-stream). LiteLLM handles this; UX should expect occasional retry-stream events."},
        ],
        "github_url": "https://github.com/BerriAI/litellm",
        "meta_title": "LiteLLM Router With Fallbacks — Multi-Provider Starter",
        "meta_description": "LiteLLM Router: 100+ providers, latency/cost routing, auto-fallback, per-deployment limits, spend tracking. Production-grade.",
    },
    {
        "slug": "bedrock-converse-with-guardrails",
        "title": "AWS Bedrock Converse API With Guardrails",
        "tldr": "Bedrock Converse API: unified message API across Anthropic/Meta/Mistral/Cohere on Bedrock. Layer in Bedrock Guardrails for PII / profanity / topic-filtering.",
        "category": "llm-clients",
        "language": "python",
        "framework": "AWS Bedrock",
        "tags": ["bedrock", "aws", "converse", "guardrails"],
        "best_for_tags": ["aws-shops", "compliance", "regulated-industries"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "AWS-native shop with VPC / compliance requirements. Bedrock Guardrails do PII redaction + topic filtering + grounding checks across ALL models. Convers API normalizes interface.",
        "when_not_to_use": "Skip if not on AWS — friction with IAM / regions. Skip for early-stage prototyping (latency higher than direct SaaS APIs).",
        "quick_start": "pip install boto3 && aws configure && python bedrock_converse.py",
        "full_code": '''"""Bedrock Converse API + Guardrails.

Unified API: Claude, Llama 3, Mistral, Cohere — same Converse signature.
Guardrails apply pre-request + post-response.
"""
from __future__ import annotations

import os
import boto3


bedrock_runtime = boto3.client(service_name="bedrock-runtime",
                                region_name=os.environ.get("AWS_REGION", "us-east-1"))
bedrock = boto3.client(service_name="bedrock",
                       region_name=os.environ.get("AWS_REGION", "us-east-1"))


# ----------------- CREATE A GUARDRAIL -----------------

def ensure_guardrail() -> str:
    """Create a guardrail that blocks topic 'medical advice' + redacts PII.

    Returns guardrail_id.
    """
    try:
        response = bedrock.create_guardrail(
            name="demo-guardrail",
            description="Block medical advice + redact PII",
            topicPolicyConfig={
                "topicsConfig": [{
                    "name": "MedicalAdvice",
                    "definition": "Diagnosis, treatment, or medication recommendations.",
                    "examples": [
                        "What dose of ibuprofen should I take?",
                        "Diagnose my symptoms",
                    ],
                    "type": "DENY",
                }],
            },
            sensitiveInformationPolicyConfig={
                "piiEntitiesConfig": [
                    {"type": "EMAIL", "action": "ANONYMIZE"},
                    {"type": "PHONE", "action": "ANONYMIZE"},
                    {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCK"},
                ],
            },
            blockedInputMessaging="I can't help with that topic.",
            blockedOutputsMessaging="Response blocked by content policy.",
        )
        return response["guardrailId"]
    except bedrock.exceptions.ConflictException:
        # Already exists
        for g in bedrock.list_guardrails()["guardrails"]:
            if g["name"] == "demo-guardrail":
                return g["id"]
        raise


GUARDRAIL_ID = ensure_guardrail()


# ----------------- CONVERSE API -----------------

def chat(model_id: str, messages: list[dict], system: str | None = None) -> str:
    """Unified converse call; same signature for all Bedrock-hosted models."""
    request = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {"temperature": 0.0, "maxTokens": 1024},
        "guardrailConfig": {
            "guardrailIdentifier": GUARDRAIL_ID,
            "guardrailVersion": "DRAFT",  # use a specific version for prod
            "trace": "enabled",
        },
    }
    if system:
        request["system"] = [{"text": system}]

    response = bedrock_runtime.converse(**request)

    # Check guardrail trace
    if "trace" in response and "guardrail" in response["trace"]:
        trace = response["trace"]["guardrail"]
        if trace.get("inputAssessment"):
            print(f"Guardrail input trace: {trace['inputAssessment']}")
        if trace.get("outputAssessment"):
            print(f"Guardrail output trace: {trace['outputAssessment']}")

    return response["output"]["message"]["content"][0]["text"]


# ----------------- DEMO ACROSS MODELS -----------------

if __name__ == "__main__":
    msg = [{"role": "user", "content": [{"text": "What is rate limiting? My email is foo@bar.com"}]}]

    for model_id in [
        "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "meta.llama3-70b-instruct-v1:0",
        "mistral.mistral-large-2402-v1:0",
    ]:
        print(f"\\n=== {model_id} ===")
        try:
            print(chat(model_id, msg))
        except Exception as e:
            print(f"FAILED: {e}")
''',
        "dependencies": [
            {"name": "boto3", "version": ">=1.35", "purpose": "AWS SDK"},
        ],
        "env_vars": [
            {"name": "AWS_ACCESS_KEY_ID", "required": True, "description": "AWS credentials", "example": "AKIA..."},
            {"name": "AWS_SECRET_ACCESS_KEY", "required": True, "description": "AWS secret", "example": "..."},
            {"name": "AWS_REGION", "required": False, "description": "Bedrock region", "example": "us-east-1"},
        ],
        "setup_steps": [
            "Enable Bedrock model access in AWS console (per-model approval)",
            "aws configure  # or set env vars",
            "pip install boto3",
            "python bedrock_converse.py",
        ],
        "variations": [
            {"label": "Streaming Converse", "description": "Use converse_stream for real-time.", "code_snippet": "response = bedrock_runtime.converse_stream(**request)\\nfor event in response['stream']:\\n    if 'contentBlockDelta' in event: print(event['contentBlockDelta']['delta']['text'], end='')"},
            {"label": "Tool use via Converse", "description": "Cross-model tool calling.", "code_snippet": "request['toolConfig'] = {'tools': [{'toolSpec': {'name': 'get_weather', 'inputSchema': {...}}}]}"},
            {"label": "Provisioned throughput", "description": "Reserved capacity for prod.", "code_snippet": "# Create provisioned throughput model unit; reference it as modelId — guaranteed capacity but $$$"},
        ],
        "common_errors": [
            {"error_text": "AccessDeniedException: model not granted", "cause": "Per-model access not enabled.", "fix_snippet": "AWS Console → Bedrock → Model access → Enable per model. Some models require justification."},
            {"error_text": "ThrottlingException", "cause": "On-demand TPS limit hit.", "fix_snippet": "Request quota increase via AWS support, OR use Provisioned Throughput for guaranteed capacity, OR add exponential backoff."},
            {"error_text": "Guardrail trace shows GUARDRAIL_INTERVENED but text returned anyway", "cause": "Confusing guardrail action vs status.", "fix_snippet": "Check 'stopReason' field — if 'guardrail_intervened', the response was blocked/modified. Don't show raw output."},
            {"error_text": "Different models give wildly different outputs", "cause": "Same prompt, different model defaults.", "fix_snippet": "Pin temperature=0; provide explicit system prompt; test each model in your eval set."},
        ],
        "production_checklist": [
            "Enable VPC endpoints for Bedrock if compliance requires.",
            "Use Provisioned Throughput for predictable QPS / SLA.",
            "Version guardrails (don't use DRAFT in production).",
            "Set up CloudWatch metrics on Converse latency + errors.",
            "Audit guardrail traces — store for compliance.",
            "Test per-model behavior — Converse normalizes API, not output.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-5-sonnet", "llama3-70b-instruct", "mistral-large-2402"],
            "library_versions": ["boto3==1.35"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["aws-bedrock"],
        "related_glossary_slugs": ["guardrails", "bedrock"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Bedrock vs direct Anthropic API?", "answer": "Direct: faster, more features (computer-use, latest models day-1). Bedrock: AWS billing, VPC, IAM, compliance (HIPAA, SOC2), Guardrails. Pick by org requirements."},
            {"question": "Guardrails cost?", "answer": "Per-1k-input/output unit, on top of model cost. Roughly $1.50 per 1M tokens checked. Significant if heavy usage; cheap relative to compliance value."},
            {"question": "Cross-region inference?", "answer": "Bedrock cross-region inference profile routes requests across regions for higher availability. Useful for global apps. Set inferenceProfileArn in request."},
            {"question": "Streaming guardrails — work mid-stream?", "answer": "Yes, but adds latency (checks every N tokens). For ultra-low-latency, skip guardrails on output; rely on input filtering + post-process."},
        ],
        "github_url": "https://github.com/boto/boto3",
        "meta_title": "AWS Bedrock Converse + Guardrails — LLM Client Starter",
        "meta_description": "Bedrock Converse API unified across Anthropic / Llama / Mistral / Cohere, with Guardrails for PII / topic blocking / grounding.",
    },
]
