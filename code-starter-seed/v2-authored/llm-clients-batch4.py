"""LLM client starters — batch 4: Mistral, Groq, Replicate, OpenRouter."""

RECORDS = [
    {
        "slug": "mistral-le-platform-chat",
        "title": "Mistral La Plateforme Chat + Function Calling",
        "tldr": "Mistral La Plateforme: official SaaS API for Mistral models (Large, Codestral, Pixtral). Function calling, JSON mode, function calling. EU-hosted (good for EU compliance).",
        "category": "llm-clients",
        "language": "python",
        "framework": "Mistral AI SDK",
        "tags": ["mistral", "european", "function-calling", "json-mode"],
        "best_for_tags": ["eu-compliance", "european-data-residency", "cost-effective"],
        "difficulty_tier": "beginner",
        "featured": False,
        "when_to_use": "EU-based shop needing data residency. Mistral La Plateforme hosts in EU; competitive pricing. Mistral Large competitive with GPT-4o on many tasks at lower cost.",
        "when_not_to_use": "Skip for US-only workloads (OpenAI / Anthropic are more established). Skip for cutting-edge frontier features (Mistral often a step behind).",
        "quick_start": "pip install mistralai && python mistral_demo.py",
        "full_code": '''"""Mistral La Plateforme: chat, function calling, JSON mode."""
from __future__ import annotations

import os
import json
from mistralai import Mistral


client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])


# ----------------- BASIC CHAT -----------------

def chat(prompt: str, model: str = "mistral-large-latest") -> str:
    response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return response.choices[0].message.content


# ----------------- STREAMING -----------------

def chat_stream(prompt: str, model: str = "mistral-large-latest"):
    for chunk in client.chat.stream(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    ):
        delta = chunk.data.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print()


# ----------------- JSON MODE -----------------

def chat_json(prompt: str) -> dict:
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": "Output JSON only."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)


# ----------------- FUNCTION CALLING -----------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "unit": {"type": "string", "enum": ["c", "f"]},
                },
                "required": ["location"],
            },
        },
    },
]


def execute_tool(name: str, args: dict) -> str:
    if name == "get_weather":
        return json.dumps({"temp": 22, "conditions": "clear"})
    return json.dumps({"error": "unknown tool"})


def chat_with_tools(prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]

    for _ in range(5):
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = response.choices[0].message
        messages.append({"role": "assistant", "content": msg.content or "",
                         "tool_calls": msg.tool_calls})

        if not msg.tool_calls:
            return msg.content

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            result = execute_tool(call.function.name, args)
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "name": call.function.name, "content": result})
    return "Max iterations"


# ----------------- CODESTRAL FOR CODE -----------------

def code_complete(prompt: str) -> str:
    """Codestral: Mistral's code-specialized model."""
    response = client.chat.complete(
        model="codestral-latest",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return response.choices[0].message.content


# ----------------- PIXTRAL FOR IMAGES -----------------

def vision(prompt: str, image_url: str) -> str:
    """Pixtral: Mistral's multi-modal model."""
    response = client.chat.complete(
        model="pixtral-12b-2409",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": image_url},
            ],
        }],
    )
    return response.choices[0].message.content


# ----------------- DEMO -----------------

if __name__ == "__main__":
    print(chat("Explain caching in 3 sentences."))
    print()
    chat_stream("Write a haiku about Mistral.")
    print(chat_with_tools("What's the weather in Paris in Celsius?"))
    print(code_complete("Write a Python function to merge two sorted lists."))
''',
        "dependencies": [
            {"name": "mistralai", "version": ">=1.0", "purpose": "Mistral Python SDK"},
        ],
        "env_vars": [
            {"name": "MISTRAL_API_KEY", "required": True, "description": "From console.mistral.ai", "example": "..."},
        ],
        "setup_steps": [
            "Sign up at mistral.ai (EU-hosted)",
            "pip install mistralai",
            "export MISTRAL_API_KEY=...",
            "python mistral_demo.py",
        ],
        "variations": [
            {"label": "Local via Ollama", "description": "Run Mistral models locally.", "code_snippet": "ollama pull mistral:7b; from openai import OpenAI; client = OpenAI(base_url='http://localhost:11434/v1')"},
            {"label": "Azure AI Studio", "description": "Mistral models on Azure.", "code_snippet": "# Azure AI Studio hosts Mistral; use Azure OpenAI SDK with deployment name pointing to Mistral"},
            {"label": "Mistral on AWS Bedrock", "description": "Mistral Large + 7B on Bedrock.", "code_snippet": "# Use boto3 bedrock-runtime invoke_model with model_id='mistral.mistral-large-2402-v1:0'"},
        ],
        "common_errors": [
            {"error_text": "Rate limit on free tier", "cause": "Mistral free tier is generous but limited.", "fix_snippet": "Upgrade to paid tier. Or batch + exponential backoff. Rate limit info in error headers."},
            {"error_text": "Tool call ID mismatch", "cause": "Forgot tool_call_id in response.", "fix_snippet": "Each tool result MUST include tool_call_id matching the call. Use call.id from the request."},
            {"error_text": "JSON mode produces text", "cause": "Missing system prompt directive.", "fix_snippet": "Always include 'output JSON only' in system prompt with response_format. Mistral hews to system instructions."},
            {"error_text": "Inconsistent output across regions", "cause": "EU vs US endpoints sometimes differ.", "fix_snippet": "Pin region in API base_url. Mistral has EU + US endpoints."},
        ],
        "production_checklist": [
            "Use EU endpoint if EU data residency required.",
            "Pin model version (e.g., mistral-large-2407 instead of -latest).",
            "Implement exponential backoff for rate limits.",
            "Validate tool args with jsonschema before executing.",
            "Cache stable system prompts (Mistral supports prompt-caching-like prefix caching).",
            "Monitor usage at console.mistral.ai dashboard.",
        ],
        "tested_with": {
            "model_versions": ["mistral-large-2407", "codestral-2405", "pixtral-12b-2409"],
            "library_versions": ["mistralai==1.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["mistral-ai"],
        "related_glossary_slugs": ["function-calling", "json-mode"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Mistral vs GPT-4o vs Claude?", "answer": "Mistral Large: competitive on most tasks, cheaper, EU-hosted. GPT-4o: best on average, frontier features first. Claude: strong on reasoning + writing. Pick by domain + compliance."},
            {"question": "Codestral worth it for code?", "answer": "Specialized on code; often beats general models on FIM (fill-in-middle), syntax-correct generations. Lower cost than GPT-4o. Worth trying for coding agents."},
            {"question": "EU data residency?", "answer": "La Plateforme hosts in EU (France). No data leaves EU. Good for GDPR-strict workloads. SOC2 Type II + ISO 27001 certified."},
            {"question": "Cost?", "answer": "Mistral Large: ~$2/1M in, $6/1M out. GPT-4o: $2.50/$10. Claude 3.5 Sonnet: $3/$15. Mistral wins on cost for many use cases."},
        ],
        "github_url": "https://github.com/mistralai/client-python",
        "meta_title": "Mistral La Plateforme Chat Starter",
        "meta_description": "Mistral La Plateforme: EU-hosted LLM SaaS with function calling, JSON mode, Codestral (code), Pixtral (vision).",
    },
    {
        "slug": "groq-fast-inference-api",
        "title": "Groq Lightning-Fast LPU Inference",
        "tldr": "Groq: custom LPU (Language Processing Unit) hardware. 500+ tok/s on Llama-3.1 70B (vs 30 tok/s typical). For real-time apps where latency wins.",
        "category": "llm-clients",
        "language": "python",
        "framework": "Groq SDK",
        "tags": ["groq", "lpu", "low-latency", "fast-inference"],
        "best_for_tags": ["realtime-apps", "voice-agents", "latency-critical"],
        "difficulty_tier": "beginner",
        "featured": True,
        "when_to_use": "Real-time apps where every 100ms matters (voice agents, interactive code assist). Groq's LPU is 10-20x faster than GPU inference for compatible models.",
        "when_not_to_use": "Skip for batch workloads (latency advantage wasted). Skip for fine-tuned models (Groq hosts a fixed catalog). Skip for non-Groq-supported models (Mistral, Claude, GPT-4 not available).",
        "quick_start": "pip install groq && python groq_demo.py",
        "full_code": '''"""Groq: fast inference via custom LPU hardware."""
from __future__ import annotations

import os
import time
from groq import Groq


client = Groq(api_key=os.environ["GROQ_API_KEY"])


# ----------------- BASIC CHAT -----------------

def chat(prompt: str, model: str = "llama-3.3-70b-versatile") -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content


# ----------------- STREAMING (Groq shines here) -----------------

def chat_stream_with_timing(prompt: str, model: str = "llama-3.3-70b-versatile"):
    """Measure time-to-first-token and tokens-per-second."""
    start = time.time()
    first_token_at = None
    token_count = 0

    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        max_tokens=300,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            if first_token_at is None:
                first_token_at = time.time() - start
            token_count += 1
            print(delta, end="", flush=True)

    total_time = time.time() - start
    print(f"\\n\\n--- Stats ---")
    print(f"Time to first token: {first_token_at:.3f}s")
    print(f"Total time: {total_time:.3f}s")
    print(f"Tokens: {token_count}")
    print(f"Tokens/sec: {token_count / total_time:.0f}")


# ----------------- FUNCTION CALLING -----------------

import json

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the product catalog.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
]


def chat_with_tools(prompt: str):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )
    msg = response.choices[0].message
    if msg.tool_calls:
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            # Execute + reply (simplified)
            print(f"Tool call: {call.function.name}({args})")
    return msg.content


# ----------------- SPEECH-TO-TEXT (Whisper) -----------------

def transcribe(audio_path: str) -> str:
    """Groq also hosts Whisper at LPU speed — 100x real-time."""
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            file=(audio_path, f.read()),
            model="whisper-large-v3",
            language="en",
            response_format="text",
        )
    return result


# ----------------- DEMO -----------------

if __name__ == "__main__":
    print(chat("Explain caching in 3 sentences."))
    print()
    chat_stream_with_timing("Write a 200-word explanation of distributed tracing.")
    # Compare to a typical OpenAI streaming: ~30-50 tok/s
    # Groq Llama-3.3-70B: 200-300+ tok/s
''',
        "dependencies": [
            {"name": "groq", "version": ">=0.11", "purpose": "Groq Python SDK"},
        ],
        "env_vars": [
            {"name": "GROQ_API_KEY", "required": True, "description": "From console.groq.com", "example": "gsk_..."},
        ],
        "setup_steps": [
            "Sign up at groq.com (free tier generous)",
            "pip install groq",
            "export GROQ_API_KEY=gsk_...",
            "python groq_demo.py",
            "Watch tokens/sec — Groq is dramatically faster than GPU",
        ],
        "variations": [
            {"label": "OpenAI-compatible base URL", "description": "Use OpenAI client with Groq.", "code_snippet": "from openai import OpenAI; client = OpenAI(base_url='https://api.groq.com/openai/v1', api_key=os.environ['GROQ_API_KEY'])"},
            {"label": "Voice agents", "description": "Pair with Whisper + TTS.", "code_snippet": "# STT: groq.audio.transcriptions.create(...). LLM: groq.chat... TTS: external. Whole loop in <1s."},
            {"label": "Batched inference", "description": "Multiple prompts in parallel.", "code_snippet": "# Use Groq's Batch API (recent feature) for offline batch processing at lower cost"},
        ],
        "common_errors": [
            {"error_text": "Model not found", "cause": "Model retired / renamed.", "fix_snippet": "Check https://console.groq.com/docs/models for current catalog. Groq retires older models regularly."},
            {"error_text": "Rate limit 429 quickly", "cause": "Free tier rate limit.", "fix_snippet": "Free tier: 30 RPM, 6k tokens/min. Upgrade to dev tier for higher. Exponential backoff helps."},
            {"error_text": "Tokens/sec lower than advertised", "cause": "Short outputs hit fixed overhead.", "fix_snippet": "Groq's advantage compounds with output length. For 50-token outputs, gain is modest. For 500+ tokens, massive."},
            {"error_text": "Context limit lower than expected", "cause": "Groq variants have lower max-context.", "fix_snippet": "Check exact context for chosen model. Llama-3.3 on Groq: 131k context. Mixtral: 32k. Verify before assuming."},
        ],
        "production_checklist": [
            "Use Groq for latency-critical paths only.",
            "Pair with regular OpenAI / Anthropic for fallback.",
            "Pin model version (catalog churns).",
            "Track tokens/sec — alert if degrading.",
            "Free tier good for prototyping; dev tier for production.",
            "OpenAI-compatible endpoint: drop-in for any OpenAI app.",
        ],
        "tested_with": {
            "model_versions": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "whisper-large-v3"],
            "library_versions": ["groq==0.11"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["groq"],
        "related_glossary_slugs": ["lpu", "fast-inference"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why so fast?", "answer": "Custom LPU hardware optimized for transformer inference. ~10-20x faster than equivalent GPU. Trade-off: fixed model catalog (no fine-tune hosting)."},
            {"question": "Available models?", "answer": "Llama-3.1/3.3 family, Mixtral 8x7B, Gemma 2, Whisper. Frontier models (GPT-4o, Claude) NOT available. Check current catalog."},
            {"question": "Cost vs OpenAI?", "answer": "Groq llama-3.3-70b: ~$0.59/1M in, $0.79/1M out. GPT-4o: $2.50/$10. Groq is dramatically cheaper for capable models."},
            {"question": "Production-grade SLA?", "answer": "Dev tier has SLA (99.9%). Free tier doesn't. For production, use dev tier + fallback path (OpenAI / Anthropic) on outage."},
        ],
        "github_url": "https://github.com/groq/groq-python",
        "meta_title": "Groq Lightning-Fast LPU Inference Starter",
        "meta_description": "Groq LPU: 200-500+ tok/s on Llama-3 70B. For real-time apps, voice agents, latency-critical inference.",
    },
    {
        "slug": "replicate-model-marketplace",
        "title": "Replicate Model Marketplace (Images, Speech, Custom)",
        "tldr": "Replicate: API for thousands of OSS models (image gen, speech, embeddings, custom). Per-prediction billing; no infra. Best for: ad-hoc model use beyond text LLMs.",
        "category": "llm-clients",
        "language": "python",
        "framework": "Replicate",
        "tags": ["replicate", "image-generation", "speech", "marketplace"],
        "best_for_tags": ["multi-modal-apps", "rapid-experimentation", "image-pipelines"],
        "difficulty_tier": "beginner",
        "featured": False,
        "when_to_use": "Want to use OSS models beyond text (Flux for images, Whisper for speech, MusicGen for audio) without hosting. Replicate handles all infra; pay per prediction.",
        "when_not_to_use": "Skip for text-only chat workloads (OpenAI / Anthropic / Groq cheaper + faster). Skip for high QPS — Replicate has cold-start latency.",
        "quick_start": "pip install replicate && python replicate_demo.py",
        "full_code": '''"""Replicate: ad-hoc model marketplace."""
from __future__ import annotations

import os
import replicate


# Set REPLICATE_API_TOKEN; library uses it automatically


# ----------------- IMAGE GENERATION (Flux) -----------------

def generate_image(prompt: str) -> str:
    """Returns URL of generated image."""
    output = replicate.run(
        "black-forest-labs/flux-schnell",  # fast variant
        input={
            "prompt": prompt,
            "go_fast": True,
            "megapixels": "1",
            "num_outputs": 1,
            "aspect_ratio": "1:1",
            "output_format": "webp",
            "output_quality": 80,
        },
    )
    return output[0]


# ----------------- SPEECH-TO-TEXT -----------------

def transcribe(audio_url_or_file) -> dict:
    """Whisper-large via Replicate."""
    return replicate.run(
        "openai/whisper:8099696689d249cf8b122d833c36ac3f75505c666a395ca40ef26f68e7d3d16e",
        input={
            "audio": audio_url_or_file,
            "model": "large-v3",
            "language": "en",
        },
    )


# ----------------- IMAGE-TO-TEXT (BLIP) -----------------

def caption_image(image_url: str) -> str:
    return replicate.run(
        "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
        input={"image": image_url, "task": "image_captioning"},
    )


# ----------------- BACKGROUND REMOVAL -----------------

def remove_background(image_url: str) -> str:
    return replicate.run(
        "lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1",
        input={"image": image_url},
    )


# ----------------- ASYNC PREDICTIONS (for slow models) -----------------

def generate_async(prompt: str):
    """Some models are slow; use async + webhook for production."""
    prediction = replicate.predictions.create(
        model="black-forest-labs/flux-pro",  # high quality, slow
        input={"prompt": prompt, "aspect_ratio": "16:9"},
        webhook="https://yourapp.com/webhooks/replicate",
        webhook_events_filter=["completed"],
    )
    return prediction.id  # poll or wait for webhook


def wait_for_prediction(prediction_id: str):
    """Sync wait — for non-webhook flows."""
    prediction = replicate.predictions.get(prediction_id)
    prediction.wait()  # blocks until done
    return prediction.output


# ----------------- CUSTOM MODELS (your own pushed model) -----------------

# After pushing via cog push:
def use_custom(input_data: dict) -> dict:
    return replicate.run(
        "your-username/your-model:latest-hash",
        input=input_data,
    )


# ----------------- DEMO -----------------

if __name__ == "__main__":
    # Generate an image
    img_url = generate_image("a cyberpunk city skyline at sunset, neon, rainy")
    print(f"Generated: {img_url}")

    # Caption it
    caption = caption_image(img_url)
    print(f"Caption: {caption}")
''',
        "dependencies": [
            {"name": "replicate", "version": ">=1.0", "purpose": "Replicate Python SDK"},
        ],
        "env_vars": [
            {"name": "REPLICATE_API_TOKEN", "required": True, "description": "From replicate.com", "example": "r8_..."},
        ],
        "setup_steps": [
            "Sign up at replicate.com (free tier with $)",
            "pip install replicate",
            "export REPLICATE_API_TOKEN=r8_...",
            "Browse https://replicate.com/explore for models",
            "Run python replicate_demo.py",
        ],
        "variations": [
            {"label": "Streaming output", "description": "Stream text models (Llama on Replicate).", "code_snippet": "for event in replicate.stream('meta/llama-3-8b-instruct', input={'prompt': '...'}): print(event, end='')"},
            {"label": "Deploy custom model with Cog", "description": "Push your own model.", "code_snippet": "# pip install cog; cog init; write predict.py; cog push r8.im/username/model. Then call via replicate.run()"},
            {"label": "Webhooks for long-running", "description": "Async with callback.", "code_snippet": "# predictions.create(..., webhook=URL, webhook_events_filter=['completed']) — Replicate POSTs to URL when done"},
        ],
        "common_errors": [
            {"error_text": "Cold start 10-30s", "cause": "Rare model on cold container.", "fix_snippet": "Popular models stay warm. For rare models, expect cold start. Use deployments (paid) to keep specific models warm."},
            {"error_text": "Cost surprise", "cause": "Per-second billing on slow models.", "fix_snippet": "Check model card for prediction cost. Image models ~$0.001-0.01 per. Slow models can add up — monitor."},
            {"error_text": "Model version pinning", "cause": "Used model name without :hash.", "fix_snippet": "For production, ALWAYS pin :hash (immutable). 'salesforce/blip' uses latest; bumps could break."},
            {"error_text": "Output URL expires", "cause": "Replicate-hosted output URLs are temporary.", "fix_snippet": "Download outputs immediately for permanent storage (S3 / GCS). Don't rely on Replicate URLs long-term."},
        ],
        "production_checklist": [
            "Pin model versions by :hash for reproducibility.",
            "Download outputs immediately; don't link to Replicate URLs.",
            "Use webhooks for long-running predictions.",
            "Set max-prediction-time to prevent runaway cost.",
            "For high QPS, use deployments to keep models warm.",
            "Monitor cost dashboard — per-prediction adds up.",
        ],
        "tested_with": {
            "model_versions": ["flux-schnell", "whisper-large-v3", "blip"],
            "library_versions": ["replicate==1.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["replicate"],
        "related_glossary_slugs": ["model-marketplace", "image-generation"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Replicate vs HuggingFace Inference?", "answer": "Replicate: marketplace UX, custom-model push via Cog, per-prediction billing. HF: free models + paid Inference Endpoints. Replicate is better for one-off use; HF for fine-tuning workflows."},
            {"question": "Cost of generating 1000 images?", "answer": "Flux-schnell: ~$3 (1000 × $0.003). Flux-pro: ~$50. Compare to OpenAI DALL-E 3: ~$40. Replicate often cheaper for image gen."},
            {"question": "Self-host Cog models?", "answer": "Yes — Cog containers are standard Docker. Run anywhere. Push to Replicate for managed; or run locally / Kubernetes."},
            {"question": "Privacy?", "answer": "Replicate logs predictions + inputs. For sensitive data, use cog locally OR pay for enterprise tier with data retention controls."},
        ],
        "github_url": "https://github.com/replicate/replicate-python",
        "meta_title": "Replicate Model Marketplace Starter",
        "meta_description": "Replicate: API for thousands of OSS models (Flux, Whisper, MusicGen, custom). Per-prediction billing, async webhooks, Cog deploy.",
    },
    {
        "slug": "openrouter-multi-model-gateway",
        "title": "OpenRouter Multi-Model Gateway",
        "tldr": "OpenRouter: one API key, 100+ models from all providers (OpenAI, Anthropic, Google, Mistral, OSS). OpenAI-compatible. Routes to cheapest provider per model. No re-engineering.",
        "category": "llm-clients",
        "language": "python",
        "framework": "OpenRouter",
        "tags": ["openrouter", "multi-provider", "gateway", "cost-routing"],
        "best_for_tags": ["multi-model-experiments", "cost-optimization", "indie-developers"],
        "difficulty_tier": "beginner",
        "featured": False,
        "when_to_use": "Want access to many models with one API key + one bill. OpenRouter is a billing/proxy layer over major providers. Good for experiments, indie apps, multi-provider apps.",
        "when_not_to_use": "Skip for high-traffic prod (extra hop adds latency + margin). Skip if you need provider-specific features OpenRouter abstracts away (cache, batch, specific tool features).",
        "quick_start": "pip install openai && python openrouter_demo.py",
        "full_code": '''"""OpenRouter: one key for 100+ models via OpenAI-compatible API."""
from __future__ import annotations

import os
from openai import OpenAI


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://yourapp.com",     # for rankings + analytics
        "X-Title": "Your App Name",
    },
)


# ----------------- USE ANY MODEL BY ID -----------------

MODELS = {
    "smart": "anthropic/claude-3.5-sonnet",
    "fast": "google/gemini-flash-1.5",
    "cheap": "openai/gpt-4o-mini",
    "code": "anthropic/claude-3.5-sonnet",
    "local-ish": "meta-llama/llama-3.3-70b-instruct",      # routed to fastest provider
}


def chat(prompt: str, model: str = "anthropic/claude-3.5-sonnet") -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


# ----------------- ROUTING PREFERENCES -----------------

def chat_with_routing(prompt: str, model: str = "meta-llama/llama-3.3-70b-instruct") -> str:
    """OpenRouter can pick among providers for a model; configure preferences."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        extra_body={
            "provider": {
                "order": ["Groq", "Together", "Fireworks"],  # try in order
                "allow_fallbacks": True,
                "data_collection": "deny",                    # privacy
                # "ignore": ["DeepInfra"],
            },
            "transforms": ["middle-out"],  # context-window compression
        },
    )
    return response.choices[0].message.content


# ----------------- FUNCTION CALLING (works across providers) -----------------

import json

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_time",
        "description": "Get current UTC time.",
        "parameters": {"type": "object", "properties": {}},
    },
}]


def execute_tool(name: str, args: dict) -> str:
    if name == "get_time":
        from datetime import datetime
        return datetime.utcnow().isoformat()
    return f"unknown tool {name}"


def chat_with_tools(prompt: str, model: str = "openai/gpt-4o-mini") -> str:
    messages = [{"role": "user", "content": prompt}]
    for _ in range(5):
        response = client.chat.completions.create(
            model=model, messages=messages, tools=TOOLS,
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            return msg.content
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            result = execute_tool(call.function.name, args)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})


# ----------------- COST + USAGE -----------------

def get_credits() -> dict:
    """Check remaining OpenRouter credits."""
    import requests
    r = requests.get(
        "https://openrouter.ai/api/v1/auth/key",
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
    )
    return r.json()


# ----------------- DEMO -----------------

if __name__ == "__main__":
    print("Smart:", chat("Explain rate limiting.", model=MODELS["smart"])[:200])
    print("Fast:", chat("Same question.", model=MODELS["fast"])[:200])
    print("Cheap:", chat("Same question.", model=MODELS["cheap"])[:200])

    print("\\nWith routing:")
    print(chat_with_routing("What's caching?"))

    print("\\nCredits:", get_credits())
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "OpenRouter is OpenAI-compatible"},
        ],
        "env_vars": [
            {"name": "OPENROUTER_API_KEY", "required": True, "description": "From openrouter.ai", "example": "sk-or-..."},
        ],
        "setup_steps": [
            "Sign up at openrouter.ai; add credits ($10 minimum)",
            "pip install openai",
            "export OPENROUTER_API_KEY=sk-or-...",
            "Browse models at openrouter.ai/models",
            "Run python openrouter_demo.py",
        ],
        "variations": [
            {"label": "Auto-route to cheapest", "description": "Let OpenRouter pick provider.", "code_snippet": "# Use 'openrouter/auto' or set provider preferences with 'cheap_first': true"},
            {"label": "Per-request fallbacks", "description": "Try multiple models on failure.", "code_snippet": "extra_body={'models': ['openai/gpt-4o', 'anthropic/claude-3-5-sonnet']}  # tries in order"},
            {"label": "Activity log + analytics", "description": "OpenRouter dashboard tracks every call.", "code_snippet": "# View at openrouter.ai/activity. Per-model cost, latency, error rate. Free dashboard with usage."},
        ],
        "common_errors": [
            {"error_text": "Credits exhausted mid-flight", "cause": "Forgot to top up.", "fix_snippet": "Use the auth/key endpoint to check credits programmatically. Alert at 20% remaining. Auto-top-up via Stripe."},
            {"error_text": "Provider not available", "cause": "Specific provider down.", "fix_snippet": "Set allow_fallbacks=true so OpenRouter routes to alternate provider. Most models have 3-5 providers."},
            {"error_text": "Tool calling format mismatch across providers", "cause": "Different providers handle tool calls slightly differently.", "fix_snippet": "OpenRouter normalizes most. For edge cases, stick to one provider or test across them."},
            {"error_text": "Higher latency than direct API", "cause": "Extra proxy hop.", "fix_snippet": "OpenRouter adds 50-100ms. For latency-critical paths, use direct provider. For experimentation / multi-model, OpenRouter trade-off is fine."},
        ],
        "production_checklist": [
            "Monitor credits + auto-top-up via Stripe.",
            "Set HTTP-Referer + X-Title for proper attribution.",
            "Allow fallbacks for resilience.",
            "Pin model + provider for production paths.",
            "Test tool calling across providers before relying.",
            "For privacy-sensitive workloads, set data_collection: deny.",
        ],
        "tested_with": {
            "model_versions": ["claude-3.5-sonnet", "gpt-4o-mini", "llama-3.3-70b-instruct"],
            "library_versions": ["openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["openrouter"],
        "related_glossary_slugs": ["llm-gateway", "multi-provider"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "OpenRouter vs LiteLLM?", "answer": "OpenRouter: SaaS gateway with one bill. LiteLLM: library / self-hosted proxy. OpenRouter: simplest UX. LiteLLM: more control + no per-request markup."},
            {"question": "Markup over direct provider?", "answer": "OpenRouter: ~5% markup vs direct. In exchange: one key, one bill, easy switching, activity dashboard. Worth it for indie / experimentation."},
            {"question": "Latency overhead?", "answer": "+50-100ms vs direct provider. For chat: negligible. For agents with many calls: adds up. Use direct for hot paths."},
            {"question": "Data privacy?", "answer": "Set data_collection: deny. OpenRouter doesn't log content (only metadata). For strict requirements, audit their privacy docs + DPA."},
        ],
        "github_url": "",
        "meta_title": "OpenRouter Multi-Model Gateway Starter",
        "meta_description": "OpenRouter: 100+ LLM models via one OpenAI-compatible API. Provider routing, fallbacks, activity dashboard.",
    },
]
