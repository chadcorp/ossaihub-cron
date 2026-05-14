"""LLM inference starters — batch 2: TGI, TensorRT-LLM, dynamic batching."""

RECORDS = [
    {
        "slug": "tgi-server-with-quantization",
        "title": "Text Generation Inference Server (Quantized)",
        "tldr": "Hugging Face TGI server config for serving quantized LLMs with continuous batching, streaming, and tool-call output. Production-grade alternative to vLLM with different operational profile.",
        "category": "llm-inference",
        "language": "bash",
        "framework": "TGI",
        "tags": ["tgi", "inference", "quantization", "production"],
        "best_for_tags": ["self-hosted", "huggingface-models", "production-inference"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "When self-hosting an open-source LLM (Llama, Mistral) and you want HF's official inference server. TGI handles continuous batching, AWQ/GPTQ quantization, and streaming out of the box.",
        "when_not_to_use": "Skip when vLLM works for you (similar performance, sometimes simpler). Skip for serverless-friendly setups — TGI is a long-running server, not on-demand.",
        "quick_start": "docker run --gpus all -p 8080:80 -v $PWD/data:/data ghcr.io/huggingface/text-generation-inference:latest --model-id mistralai/Mistral-7B-Instruct-v0.3 --quantize awq",
        "full_code": '''#!/bin/bash
# TGI server: Mistral 7B Instruct, AWQ-quantized, streaming, continuous batching.

# Hardware: 1x A10G 24GB or any GPU with ≥16GB after quantization

docker run --gpus all -d \\
  --name tgi-mistral \\
  -p 8080:80 \\
  -v "$PWD/data:/data" \\
  -e HF_TOKEN="$HF_TOKEN" \\
  ghcr.io/huggingface/text-generation-inference:latest \\
  --model-id mistralai/Mistral-7B-Instruct-v0.3 \\
  --quantize awq \\
  --max-input-length 4096 \\
  --max-total-tokens 8192 \\
  --max-batch-prefill-tokens 16384 \\
  --max-concurrent-requests 128

# ---- Python client (uses TGI's OpenAI-compatible endpoint) ----

# pip install openai
# python -c "
# from openai import OpenAI
# c = OpenAI(base_url='http://localhost:8080/v1', api_key='dummy')
# resp = c.chat.completions.create(
#   model='tgi',
#   messages=[{'role':'user','content':'Explain RAG in one paragraph.'}],
#   stream=True
# )
# for chunk in resp:
#   delta = chunk.choices[0].delta.content or ''
#   print(delta, end='', flush=True)
# "

# ---- Tool calling (Mistral supports tool_use) ----
# Use the same OpenAI client; pass `tools=[...]` per OpenAI's spec. TGI translates.
''',
        "dependencies": [
            {"name": "docker", "version": ">=24.0", "purpose": "Container runtime"},
            {"name": "openai (client)", "version": ">=1.40", "purpose": "Client SDK; TGI is OpenAI-compatible"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": False, "description": "HF token for gated models", "example": "hf_..."},
        ],
        "setup_steps": [
            "Install Docker with NVIDIA Container Toolkit.",
            "docker pull ghcr.io/huggingface/text-generation-inference:latest",
            "Run the docker command above; wait for the model to load (1-3 min first time).",
            "Test: curl http://localhost:8080/health",
            "Use any OpenAI-compatible client pointing at http://localhost:8080/v1",
        ],
        "variations": [
            {
                "label": "GPTQ quantization",
                "description": "Alternative quantization with different speed/quality tradeoff.",
                "code_snippet": "--quantize gptq  # requires GPTQ-quantized model weights on HF",
            },
            {
                "label": "Tensor parallelism (multi-GPU)",
                "description": "Split model across GPUs.",
                "code_snippet": "--num-shard 2  # number of GPUs to use\\n# Adjust max-input-length / max-batch-prefill-tokens for multi-GPU memory",
            },
            {
                "label": "Speculative decoding",
                "description": "Draft model + main model for speed.",
                "code_snippet": "--speculate 4  # draft 4 tokens at a time, verify with main model",
            },
            {
                "label": "Kubernetes deployment",
                "description": "Deploy via HF's helm chart.",
                "code_snippet": "helm install tgi huggingface/text-generation-inference --values values.yaml\\n# Use the official chart; configure GPU node selector, autoscaling, ingress.",
            },
        ],
        "common_errors": [
            {
                "error_text": "AssertionError: total max-batch-prefill-tokens too large",
                "cause": "Memory math doesn't work for your GPU.",
                "fix_snippet": "Lower max-batch-prefill-tokens. For A10G 24GB with 7B AWQ: 16384 works; for 13B AWQ: try 8192.",
            },
            {
                "error_text": "Model loading takes 5+ min on first run",
                "cause": "Downloading from HF and converting.",
                "fix_snippet": "Pre-download weights to the mounted /data volume. Set HF_TOKEN if model is gated.",
            },
            {
                "error_text": "Streaming chunks arrive in big bursts",
                "cause": "Continuous batching can briefly batch your tokens with others.",
                "fix_snippet": "Normal under load. If you need real-time, reduce max-concurrent-requests; trade throughput for latency.",
            },
            {
                "error_text": "Tool calls return as text, not structured",
                "cause": "Model doesn't natively output tool_calls structure.",
                "fix_snippet": "TGI requires model that supports tool calling (Mistral Instruct, Llama 3.1 Instruct, etc.). Verify model is on TGI's supported list.",
            },
        ],
        "production_checklist": [
            "Pin TGI image version; don't run :latest in production.",
            "Set max-concurrent-requests below your GPU memory ceiling (tested under load).",
            "Health-check via /health endpoint; integrate with your load balancer.",
            "Stream-aware clients only; non-streaming dramatically reduces throughput.",
            "Monitor GPU memory + queue depth.",
            "Use a dedicated GPU node pool in Kubernetes.",
            "Plan model upgrades carefully — quantization may differ across releases.",
        ],
        "tested_with": {
            "model_versions": ["mistralai/Mistral-7B-Instruct-v0.3", "meta-llama/Llama-3.1-8B-Instruct"],
            "library_versions": ["TGI 2.4+"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["text-generation-inference"],
        "related_glossary_slugs": ["awq", "continuous-batching", "tgi"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "TGI vs vLLM?",
                "answer": "Both excellent. TGI: HF-aligned, smoother for HF models, official tool-call support. vLLM: slightly faster on most benchmarks, more flexible API. Pick by team familiarity.",
            },
            {
                "question": "AWQ vs GPTQ vs bitsandbytes?",
                "answer": "AWQ: best speed + quality balance; needs AWQ-quantized weights. GPTQ: older, broad support, similar quality. bitsandbytes: easiest setup but slower than AWQ. AWQ is the default recommendation in 2025.",
            },
            {
                "question": "What's max throughput?",
                "answer": "~3000 tokens/sec on A10G with 7B AWQ at high concurrency. Higher with multi-GPU tensor parallelism. Measure for your model + GPU combo.",
            },
            {
                "question": "Can I run multiple models on one TGI instance?",
                "answer": "No — one model per server. Run multiple TGI containers and route via a proxy (LiteLLM proxy is common).",
            },
        ],
        "github_url": "https://github.com/huggingface/text-generation-inference",
        "meta_title": "Text Generation Inference Server (Quantized) — Starter",
        "meta_description": "HF TGI server config: AWQ quantization, continuous batching, OpenAI-compatible endpoint, tool calling. Production-grade self-hosted LLM.",
    },
    {
        "slug": "dynamic-batching-with-asyncio",
        "title": "Dynamic Batching For LLM Calls (asyncio)",
        "tldr": "Collect requests over a small time window and batch them into single API calls. Trades a few ms of latency for significant cost + throughput gains when running many concurrent prompts.",
        "category": "llm-inference",
        "language": "python",
        "framework": "asyncio + OpenAI",
        "tags": ["batching", "asyncio", "throughput", "cost-optimization"],
        "best_for_tags": ["bulk-jobs", "background-processing", "cost-sensitive"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "When you have many concurrent independent LLM calls (background processing, bulk classification). Dynamic batching collects them over a small window and submits as one API request when possible.",
        "when_not_to_use": "Skip for user-facing chat (latency matters). Skip for providers that don't support batching natively — single API can't batch chat completions; you'd need multiple async calls.",
        "quick_start": "pip install openai asyncio && python batcher.py",
        "full_code": '''"""Dynamic batching for embeddings — single endpoint, many inputs.

Pattern:
  - Coroutines submit individual texts to a batcher
  - Batcher accumulates for up to {max_wait_ms} OR {max_batch_size}
  - Then flushes to OpenAI embeddings endpoint (which natively batches up to 2048)
  - Returns embeddings to original callers in order
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from openai import AsyncOpenAI


@dataclass
class PendingRequest:
    text: str
    future: asyncio.Future


class EmbedBatcher:
    def __init__(
        self,
        client: AsyncOpenAI,
        *,
        model: str = "text-embedding-3-small",
        max_batch_size: int = 256,
        max_wait_ms: int = 50,
    ):
        self.client = client
        self.model = model
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self._queue: list[PendingRequest] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task | None = None

    async def embed(self, text: str) -> list[float]:
        """Submit one text; await embedding. Batcher handles the rest."""
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        async with self._lock:
            self._queue.append(PendingRequest(text=text, future=future))
            should_flush_now = len(self._queue) >= self.max_batch_size

            # Schedule flush if not already scheduled
            if not should_flush_now and (self._flush_task is None or self._flush_task.done()):
                self._flush_task = asyncio.create_task(self._delayed_flush())

        if should_flush_now:
            await self._flush()

        return await future

    async def _delayed_flush(self):
        await asyncio.sleep(self.max_wait_ms / 1000)
        await self._flush()

    async def _flush(self):
        async with self._lock:
            if not self._queue:
                return
            batch = self._queue
            self._queue = []

        try:
            resp = await self.client.embeddings.create(
                input=[r.text for r in batch],
                model=self.model,
            )
            for r, emb in zip(batch, resp.data):
                if not r.future.done():
                    r.future.set_result(emb.embedding)
        except Exception as e:
            for r in batch:
                if not r.future.done():
                    r.future.set_exception(e)


# ----------------- DEMO -----------------

async def main():
    client = AsyncOpenAI()
    batcher = EmbedBatcher(client, max_batch_size=64, max_wait_ms=50)

    texts = [
        "Reciprocal rank fusion combines retriever results.",
        "BM25 is a keyword retrieval algorithm.",
        "Dense embeddings capture semantic meaning.",
    ] * 50  # 150 inputs

    # Launch all embeds concurrently — the batcher collects them
    results = await asyncio.gather(*[batcher.embed(t) for t in texts])
    print(f"Got {len(results)} embeddings, dim={len(results[0])}")


if __name__ == "__main__":
    asyncio.run(main())
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "AsyncOpenAI"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai",
            "export OPENAI_API_KEY=sk-...",
            "python batcher.py",
            "Monitor latency overhead: typically 5-50ms added per request, but 5-20x throughput improvement.",
        ],
        "variations": [
            {
                "label": "Embedding model auto-batch",
                "description": "OpenAI embeddings natively batch up to 2048; raise max_batch_size.",
                "code_snippet": "batcher = EmbedBatcher(..., max_batch_size=2000)",
            },
            {
                "label": "Concurrent batches",
                "description": "Run multiple batches in parallel when one is full while another fills.",
                "code_snippet": "# When max_batch_size hit, fire-and-forget the flush; allow next batch to start filling immediately.",
            },
            {
                "label": "Priority queue",
                "description": "User-facing > background.",
                "code_snippet": "# Use a priority field on PendingRequest; user-facing gets flushed at smaller batch sizes for lower latency.",
            },
            {
                "label": "Chat completion batching (via multiple async calls)",
                "description": "Chat doesn't natively batch.",
                "code_snippet": "# For chat, use asyncio.Semaphore to bound concurrency; each call is its own request. ‘Batching’ here = controlled concurrency.",
            },
        ],
        "common_errors": [
            {
                "error_text": "Future never resolves",
                "cause": "Flush task error swallowed.",
                "fix_snippet": "Add error handling in _flush; set_exception on futures when batch fails. Starter does this.",
            },
            {
                "error_text": "Memory grows unbounded",
                "cause": "Submissions faster than flush rate.",
                "fix_snippet": "Add backpressure: if queue exceeds 2x max_batch_size, raise instead of accepting. Or add a semaphore on .embed() calls.",
            },
            {
                "error_text": "Latency higher than expected",
                "cause": "max_wait_ms too high.",
                "fix_snippet": "Tune: 25-50ms is sweet spot for embeddings. Lower for chat-style use.",
            },
            {
                "error_text": "Batches always max_wait timeout, never max_batch_size",
                "cause": "Concurrency too low to fill batches.",
                "fix_snippet": "Either lower max_batch_size to match real concurrency, or lower max_wait_ms; or accept the smaller batches (still better than no batching).",
            },
        ],
        "production_checklist": [
            "Test under realistic concurrency; batching benefit scales non-linearly.",
            "Monitor batch size distribution — if average batch is small, tune max_wait_ms.",
            "Set backpressure to prevent OOM under load spike.",
            "Surface errors per-request even if batch failed.",
            "Cache common inputs upstream of batcher.",
            "Track latency: p50 should rise only by max_wait_ms; p99 should be flat.",
        ],
        "tested_with": {
            "model_versions": ["text-embedding-3-small", "text-embedding-3-large"],
            "library_versions": ["openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["dynamic-batching", "throughput-optimization", "asyncio"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Does this work for chat completions?",
                "answer": "OpenAI chat API doesn't natively batch (one prompt per call). For chat, use asyncio.gather with Semaphore for controlled concurrency. The starter is for embeddings, which DO batch.",
            },
            {
                "question": "How does this compare to OpenAI's Batch API?",
                "answer": "OpenAI Batch API: 24-hour async processing, 50% discount. This starter: real-time-ish (~50ms added latency). Use Batch API for non-urgent bulk; dynamic batching for online with high concurrency.",
            },
            {
                "question": "Works with other providers?",
                "answer": "Anthropic embeddings/chat: limited native batching. Cohere embeddings: native batching (up to 96). Adapt accordingly.",
            },
            {
                "question": "When NOT to batch?",
                "answer": "User-facing chat where every ms counts. Cases where you have <2 concurrent requests on average (no real batching opportunity). Mixed-priority workloads without separation.",
            },
        ],
        "github_url": "",
        "meta_title": "Dynamic Batching For LLM Calls — Starter",
        "meta_description": "Coalesce concurrent embedding requests into batches. 5-20x throughput improvement with 25-50ms latency cost. asyncio-based.",
    },
]
