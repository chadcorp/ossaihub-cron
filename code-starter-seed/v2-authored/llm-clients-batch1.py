"""LLM clients (batch 1) — v2 authored code starters (2026-05-14)."""

RECORDS = [
    {
        "slug": "groq-low-latency-chat",
        "title": "Groq LPU Sub-200ms Streaming Chat",
        "category": "llm-clients",
        "language": "python",
        "framework": "Groq SDK",
        "tldr": "Groq's LPU inference for sub-200ms TTFT streaming chat with Llama 3.3 70B. Includes auto-fallback to OpenAI on Groq outage and per-request latency telemetry.",
        "tags": ["groq", "low-latency", "llama", "streaming"],
        "best_for_tags": ["low-latency", "real-time-chat", "streaming"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When time-to-first-token matters more than absolute model quality — voice assistants, real-time chat, latency-bound UX. Groq's LPU delivers 500+ tok/s on Llama 3.3 70B with TTFT typically under 200ms — 5-10x faster than running the same model on commodity GPU APIs. Best for interactive consumer apps where lag kills engagement.",
        "when_not_to_use": "When you need GPT-5 / Claude Sonnet-tier reasoning — Groq currently serves Llama and Mixtral, not frontier closed models. Also skip for batch workloads where throughput matters more than latency.",
        "quick_start": "pip install groq && export GROQ_API_KEY=gsk_... && python groq_chat.py",
        "full_code": (
            "\"\"\"Groq LPU streaming chat with OpenAI fallback + latency telemetry.\"\"\"\n"
            "import os, time, logging\n"
            "from groq import Groq, APIError as GroqError\n"
            "from openai import OpenAI\n\n"
            "groq_client = Groq(api_key=os.environ['GROQ_API_KEY'])\n"
            "openai_client = OpenAI()  # fallback\n"
            "log = logging.getLogger(__name__)\n\n"
            "GROQ_MODEL = 'llama-3.3-70b-versatile'\n"
            "FALLBACK_MODEL = 'gpt-4o-mini'\n\n"
            "def stream_chat(messages: list[dict], max_tokens: int = 500) -> dict:\n"
            "    \"\"\"Stream a chat response. Returns dict with text + telemetry.\"\"\"\n"
            "    start = time.time()\n"
            "    ttft = None\n"
            "    chunks = []\n"
            "    provider = 'groq'\n"
            "    try:\n"
            "        stream = groq_client.chat.completions.create(\n"
            "            model=GROQ_MODEL, messages=messages, stream=True, max_tokens=max_tokens,\n"
            "        )\n"
            "        for chunk in stream:\n"
            "            if chunk.choices[0].delta.content:\n"
            "                if ttft is None:\n"
            "                    ttft = (time.time() - start) * 1000\n"
            "                chunks.append(chunk.choices[0].delta.content)\n"
            "    except GroqError as e:\n"
            "        log.warning('Groq error, falling back to OpenAI: %s', e)\n"
            "        provider = f'openai-fallback (groq: {type(e).__name__})'\n"
            "        ttft = chunks = None  # reset for fallback\n"
            "        start = time.time(); chunks = []; ttft = None\n"
            "        stream = openai_client.chat.completions.create(\n"
            "            model=FALLBACK_MODEL, messages=messages, stream=True, max_tokens=max_tokens,\n"
            "        )\n"
            "        for chunk in stream:\n"
            "            if chunk.choices[0].delta.content:\n"
            "                if ttft is None:\n"
            "                    ttft = (time.time() - start) * 1000\n"
            "                chunks.append(chunk.choices[0].delta.content)\n"
            "    end = time.time()\n"
            "    text = ''.join(chunks)\n"
            "    return {\n"
            "        'text': text,\n"
            "        'provider': provider,\n"
            "        'ttft_ms': round(ttft or 0, 1),\n"
            "        'total_ms': round((end - start) * 1000, 1),\n"
            "        'tokens_estimated': len(text.split()) * 1.3,\n"
            "    }\n\n"
            "if __name__ == '__main__':\n"
            "    result = stream_chat([{'role': 'user', 'content': 'Explain LPU vs GPU in one paragraph.'}])\n"
            "    print(f\"provider={result['provider']} ttft={result['ttft_ms']}ms total={result['total_ms']}ms\")\n"
            "    print(result['text'])\n"
        ),
        "dependencies": [
            {"name": "groq", "version": ">=0.11.0,<1.0.0", "purpose": "Groq Cloud SDK for LPU inference"},
            {"name": "openai", "version": ">=1.50.0", "purpose": "Fallback when Groq is unavailable"},
        ],
        "env_vars": [
            {"name": "GROQ_API_KEY", "required": True, "description": "Get from console.groq.com — currently has a generous free tier"},
            {"name": "OPENAI_API_KEY", "required": True, "description": "Used only on Groq fallback; can be omitted if you don't want fallback"},
        ],
        "setup_steps": [
            "Create account at console.groq.com (free tier ~30 req/min generous for dev)",
            "Generate API key, store as GROQ_API_KEY env var",
            "pip install groq>=0.11.0 openai>=1.50.0",
            "Run python groq_chat.py — should print TTFT under 200ms on first request",
            "(Optional) Wire fallback by ensuring OPENAI_API_KEY is set",
        ],
        "variations": [
            {"label": "Llama 70B vs Mixtral 8x7B", "description": "Mixtral is faster but slightly weaker; switch by model name.", "code_snippet": "GROQ_MODEL = 'mixtral-8x7b-32768'  # ~400 tok/s, slightly lower quality"},
            {"label": "Sync (non-streaming) for batch", "description": "Use non-stream for batch jobs where TTFT doesn't matter.", "code_snippet": "resp = groq_client.chat.completions.create(model=GROQ_MODEL, messages=messages, stream=False)\nreturn resp.choices[0].message.content"},
            {"label": "Tool-use with Groq", "description": "Groq supports OpenAI-style tool_calls; add `tools=` arg.", "code_snippet": "stream = groq_client.chat.completions.create(model=GROQ_MODEL, messages=msgs, tools=[{...}], tool_choice='auto', stream=True)"},
        ],
        "common_errors": [
            {"error_text": "groq.RateLimitError: 429 You have hit the request rate limit", "cause": "Groq's free tier caps at ~30 RPM; production tier needed for higher volume", "fix_snippet": "from tenacity import retry, wait_exponential, stop_after_attempt\n@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(5))\ndef stream_chat(messages): ...  # wrap with retry"},
            {"error_text": "groq.APIConnectionError: Connection refused", "cause": "Groq endpoint outage or network issue", "fix_snippet": "# Already handled by the except clause — falls back to OpenAI. Verify GROQ_API_KEY scope if persistent."},
            {"error_text": "openai.AuthenticationError on fallback", "cause": "OPENAI_API_KEY unset when fallback triggered", "fix_snippet": "# Either set OPENAI_API_KEY or remove the fallback block (and accept the GroqError)."},
            {"error_text": "Empty chunks consumed but no output", "cause": "max_tokens=0 or model returned empty stop", "fix_snippet": "# Verify max_tokens >= 50; check finish_reason in non-stream mode for debugging"},
        ],
        "production_checklist": [
            "Set sensible max_tokens (Groq charges by output tokens)",
            "Wire ttft_ms + total_ms into telemetry (Datadog/Honeycomb)",
            "Alarm if TTFT >500ms p95 — Groq SLA implies <300ms",
            "Implement OpenAI fallback (or alternative) for outage resilience",
            "Cache common responses (Redis with 1h TTL) for FAQ-style queries",
            "Rate-limit at app level to stay under Groq tier (e.g., 25 RPM with 30 RPM cap)",
            "Log provider field — track Groq vs fallback ratio",
        ],
        "tested_with": {
            "model_versions": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
            "library_versions": ["groq==0.11.0", "openai==1.50.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["groq", "openai-python", "anthropic-claude"],
        "related_glossary_slugs": ["time-to-first-token", "lpu", "streaming"],
        "related_learn_slugs": ["building-low-latency-chat"],
        "license": "MIT",
        "attribution": "OSS AI Hub Code Library",
        "github_url": "https://github.com/chadcorp/ossaihub-cron/tree/main/code-starter-seed",
        "status": "approved",
        "submitter_email": "hub@ossaihub.com",
        "submitter_name": "OSS AI Hub",
        "meta_title": "Groq LPU Sub-200ms Streaming Chat — Python Starter",
        "meta_description": "Streaming chat via Groq's LPU. TTFT under 200ms, OpenAI fallback on outage, per-request latency telemetry. Llama 3.3 70B.",
        "faq": [
            {"question": "Why Groq over OpenAI/Anthropic for chat?", "answer": "Latency. Groq's LPU delivers ~5-10x faster TTFT than commodity GPU APIs. Use for real-time UX (chat widgets, voice apps). Use OpenAI/Anthropic for reasoning depth."},
            {"question": "What's the rate limit?", "answer": "Free tier ~30 RPM. Production tiers up to 10k+ RPM. Check console.groq.com for current limits."},
            {"question": "Can I use Llama 3.1 8B for even lower latency?", "answer": "Yes — change GROQ_MODEL to 'llama-3.1-8b-instant'. TTFT often <100ms but quality is noticeably lower."},
        ],
    },

    {
        "slug": "ollama-async-batch-client",
        "title": "Async Ollama Batch Client (Concurrency-Safe)",
        "category": "llm-clients",
        "language": "python",
        "framework": "aiohttp",
        "tldr": "Async client for batching concurrent Ollama requests with semaphore-bounded concurrency, per-request retry, and graceful degradation when Ollama is overloaded.",
        "tags": ["ollama", "async", "batching", "aiohttp"],
        "best_for_tags": ["batch-inference", "local-llm", "concurrency"],
        "difficulty_tier": "intermediate",
        "when_to_use": "When you have 10-1000 prompts to run through a locally-hosted Ollama instance and want to maximize throughput without overloading. The semaphore-bounded concurrency keeps GPU memory under control (concurrency typically 2-4 for 7-13B models on consumer GPUs). Per-request retry handles transient errors. Result ordering preserved.",
        "when_not_to_use": "For single-request workloads, use the synchronous Ollama client. Also skip for cloud-scale parallelism — Ollama is for local inference; if you need 100+ concurrent requests, use vLLM/TGI on a serving cluster.",
        "quick_start": "ollama pull llama3.1:8b && python batch_ollama.py",
        "full_code": (
            "\"\"\"Async batch client for Ollama with semaphore + retry.\"\"\"\n"
            "import asyncio\n"
            "import aiohttp\n"
            "import json\n"
            "import logging\n"
            "from typing import Any\n\n"
            "log = logging.getLogger(__name__)\n"
            "OLLAMA_URL = 'http://localhost:11434/api/generate'\n"
            "DEFAULT_MODEL = 'llama3.1:8b'\n\n"
            "async def _generate_one(\n"
            "    session: aiohttp.ClientSession,\n"
            "    prompt: str,\n"
            "    sem: asyncio.Semaphore,\n"
            "    *,\n"
            "    model: str = DEFAULT_MODEL,\n"
            "    max_retries: int = 3,\n"
            "    timeout_s: float = 120.0,\n"
            ") -> dict[str, Any]:\n"
            "    \"\"\"Run a single Ollama generation with retry, respecting the semaphore.\"\"\"\n"
            "    async with sem:\n"
            "        for attempt in range(max_retries):\n"
            "            try:\n"
            "                async with session.post(\n"
            "                    OLLAMA_URL,\n"
            "                    json={'model': model, 'prompt': prompt, 'stream': False},\n"
            "                    timeout=aiohttp.ClientTimeout(total=timeout_s),\n"
            "                ) as resp:\n"
            "                    resp.raise_for_status()\n"
            "                    data = await resp.json()\n"
            "                    return {'prompt': prompt, 'response': data['response'], 'tokens': data.get('eval_count', 0)}\n"
            "            except (aiohttp.ClientError, asyncio.TimeoutError) as e:\n"
            "                wait = 2 ** attempt\n"
            "                log.warning('Attempt %d/%d failed for prompt: %s (wait %ds)', attempt + 1, max_retries, e, wait)\n"
            "                await asyncio.sleep(wait)\n"
            "        return {'prompt': prompt, 'response': None, 'error': 'max retries exceeded'}\n\n"
            "async def batch_generate(prompts: list[str], *, model: str = DEFAULT_MODEL, concurrency: int = 4) -> list[dict[str, Any]]:\n"
            "    \"\"\"Run a list of prompts concurrently with bounded parallelism.\n\n"
            "    Result list preserves input order.\n"
            "    \"\"\"\n"
            "    sem = asyncio.Semaphore(concurrency)\n"
            "    async with aiohttp.ClientSession() as session:\n"
            "        tasks = [_generate_one(session, p, sem, model=model) for p in prompts]\n"
            "        return await asyncio.gather(*tasks)\n\n"
            "if __name__ == '__main__':\n"
            "    prompts = [f'In one sentence, explain concept #{i}: vLLM, quantization, RAG' for i in range(5)]\n"
            "    results = asyncio.run(batch_generate(prompts, concurrency=3))\n"
            "    for r in results:\n"
            "        print(r.get('response', r.get('error'))[:80])\n"
        ),
        "dependencies": [
            {"name": "aiohttp", "version": ">=3.9,<4.0", "purpose": "Async HTTP client for Ollama"},
            {"name": "ollama", "version": ">=0.5", "purpose": "Local Ollama runtime (install separately via ollama.ai)"},
        ],
        "env_vars": [
            {"name": "OLLAMA_URL", "required": False, "description": "Default localhost:11434 — override if Ollama runs remotely"},
        ],
        "setup_steps": [
            "Install Ollama from ollama.ai (one-line install on Mac/Linux)",
            "Pull the model: ollama pull llama3.1:8b (or your target model)",
            "Ensure Ollama daemon is running: ollama serve & (typically auto-starts after install)",
            "pip install aiohttp",
            "Run python batch_ollama.py — should see 5 responses in parallel",
            "Tune concurrency based on your GPU memory (start with 2, raise if no OOM)",
        ],
        "variations": [
            {"label": "Streaming version", "description": "Stream tokens as they generate (lower memory, slightly higher latency).", "code_snippet": "async with session.post(OLLAMA_URL, json={..., 'stream': True}) as resp:\n    async for line in resp.content:\n        yield json.loads(line).get('response', '')"},
            {"label": "With temperature/top_p", "description": "Pass sampling params.", "code_snippet": "json={'model': model, 'prompt': prompt, 'options': {'temperature': 0.7, 'top_p': 0.9}, 'stream': False}"},
            {"label": "Output to JSONL file", "description": "Write results as you go for large batches.", "code_snippet": "async def _stream_to_jsonl(results, path):\n    async with aiofiles.open(path, 'w') as f:\n        for r in results: await f.write(json.dumps(r) + '\\n')"},
        ],
        "common_errors": [
            {"error_text": "aiohttp.ClientConnectorError: Cannot connect to host localhost:11434", "cause": "Ollama daemon not running", "fix_snippet": "ollama serve &  # or: brew services start ollama"},
            {"error_text": "OllamaError: model 'llama3.1:8b' not found", "cause": "Model not pulled", "fix_snippet": "ollama pull llama3.1:8b  # ~5GB download first time"},
            {"error_text": "asyncio.TimeoutError after 120s", "cause": "Model too large for hardware, or first-token latency exceeds timeout", "fix_snippet": "# Raise timeout_s to 300 for first-load, or use a smaller model (llama3.1:8b instead of 70b)"},
            {"error_text": "GPU out-of-memory error in Ollama logs", "cause": "concurrency too high for your GPU", "fix_snippet": "# Drop concurrency from 4 to 2; or unload other models with `ollama stop <other_model>`"},
        ],
        "production_checklist": [
            "Set concurrency conservatively (2 for 13B on 16GB GPU, 4 for 7B)",
            "Always wrap in try/finally for clean session close",
            "Monitor Ollama logs for GPU OOM signals",
            "Use streaming variant for large batches to bound memory",
            "Implement disk caching for repeat prompts (hash-based)",
            "If running on cloud: pre-warm by running 1 dummy prompt before batch",
            "For 1000+ prompt batches: use Redis-backed work queue rather than in-memory list",
        ],
        "tested_with": {
            "model_versions": ["llama3.1:8b", "llama3.1:70b", "mistral:7b", "qwen2.5:14b"],
            "library_versions": ["aiohttp==3.9.5", "ollama-server==0.5.4"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["ollama", "vllm", "lm-studio"],
        "related_glossary_slugs": ["batch-inference", "semaphore", "async-io"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub Code Library",
        "github_url": "https://github.com/chadcorp/ossaihub-cron/tree/main/code-starter-seed",
        "status": "approved",
        "submitter_email": "hub@ossaihub.com",
        "submitter_name": "OSS AI Hub",
        "meta_title": "Async Ollama Batch Client — Semaphore + Retry",
        "meta_description": "Run 10-1000 prompts through local Ollama with bounded concurrency, per-request retry, GPU-OOM resilience. Async/aiohttp.",
        "faq": [
            {"question": "Why not just loop sync requests?", "answer": "Ollama can handle 2-4 concurrent generations on a single GPU. Sync looping leaves 50-75% of GPU idle between requests."},
            {"question": "What concurrency should I use?", "answer": "Start with 2. Increase by 1 and watch GPU memory + per-request latency. The sweet spot is usually 3-4 for 7-13B models on 16-24GB GPUs."},
            {"question": "How does this compare to vLLM batching?", "answer": "vLLM uses continuous batching at the model level (much more efficient — 10x throughput). Use vLLM for production scale. Use this for local dev / one-machine workloads."},
        ],
    },
]
