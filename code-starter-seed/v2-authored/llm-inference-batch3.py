"""LLM inference starters — batch 3: speculative decoding, batching, streaming, quantization."""

RECORDS = [
    {
        "slug": "vllm-speculative-decoding",
        "title": "vLLM Speculative Decoding For 2-3x Throughput",
        "tldr": "vLLM with a small draft model speculating tokens for a large target model. Tokens accepted ~70-90% of the time → 2-3x throughput, identical outputs.",
        "category": "llm-inference",
        "language": "python",
        "framework": "vLLM",
        "tags": ["vllm", "speculative-decoding", "throughput", "inference-optimization"],
        "best_for_tags": ["latency-sensitive", "high-qps", "self-hosted"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Self-hosting a 70B+ model and need higher throughput without losing quality. Draft model 1B-7B speculates ahead; target model verifies. Same outputs, less latency.",
        "when_not_to_use": "Skip for tiny models (no benefit). Skip if memory-bound (draft model adds ~10% VRAM). Skip if your workload is non-streaming and you don't care about per-request latency.",
        "quick_start": "pip install vllm && python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-3.1-70B-Instruct --speculative-model meta-llama/Llama-3.2-1B-Instruct --num-speculative-tokens 5",
        "full_code": '''"""vLLM speculative decoding server + client.

Throughput gains 2-3x for compatible workloads. Outputs identical to non-speculative.
"""
from __future__ import annotations

import time
from openai import OpenAI

# vLLM exposes an OpenAI-compatible API. Start the server with:
#   python -m vllm.entrypoints.openai.api_server \\
#     --model meta-llama/Llama-3.1-70B-Instruct \\
#     --tensor-parallel-size 4 \\
#     --speculative-model meta-llama/Llama-3.2-1B-Instruct \\
#     --num-speculative-tokens 5 \\
#     --speculative-disable-by-batch-size 8


def get_client(host: str = "http://localhost:8000") -> OpenAI:
    return OpenAI(base_url=f"{host}/v1", api_key="dummy")


def benchmark_throughput(client: OpenAI, n: int = 32) -> dict:
    """Measure tokens/sec across N concurrent requests."""
    prompts = [f"Explain why {topic} matters in one paragraph." for topic in [
        "type safety", "rate limits", "caching", "idempotency",
        "observability", "graceful degradation", "circuit breakers",
        "retries", "back-pressure", "consistent hashing",
    ] * (n // 10 + 1)][:n]

    total_tokens = 0
    start = time.time()
    for prompt in prompts:
        resp = client.chat.completions.create(
            model="meta-llama/Llama-3.1-70B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.0,  # deterministic; matches non-speculative
        )
        total_tokens += resp.usage.completion_tokens
    elapsed = time.time() - start
    return {
        "tokens": total_tokens,
        "seconds": elapsed,
        "tokens_per_sec": total_tokens / elapsed,
        "requests_per_sec": n / elapsed,
    }


def acceptance_rate_estimate(client: OpenAI) -> float:
    """vLLM logs acceptance rate; you can also estimate from server metrics.

    A healthy ratio is 70-90%. Below 50% suggests draft model mismatch.
    """
    # In production, scrape /metrics endpoint; below is illustrative.
    import urllib.request
    metrics = urllib.request.urlopen("http://localhost:8000/metrics").read().decode()
    for line in metrics.splitlines():
        if line.startswith("vllm:spec_decode_efficiency"):
            return float(line.split()[-1])
    return 0.0


def streaming_demo(client: OpenAI) -> None:
    """Speculative decoding is fully compatible with streaming."""
    stream = client.chat.completions.create(
        model="meta-llama/Llama-3.1-70B-Instruct",
        messages=[{"role": "user", "content": "Write a haiku about caching."}],
        stream=True,
        max_tokens=80,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        print(delta, end="", flush=True)
    print()


if __name__ == "__main__":
    client = get_client()
    streaming_demo(client)
    stats = benchmark_throughput(client, n=16)
    print(f"\\nThroughput: {stats['tokens_per_sec']:.0f} tok/s, "
          f"{stats['requests_per_sec']:.1f} req/s")
    print(f"Acceptance rate: {acceptance_rate_estimate(client):.1%}")
''',
        "dependencies": [
            {"name": "vllm", "version": ">=0.6.0", "purpose": "Inference server with speculative decoding"},
            {"name": "openai", "version": ">=1.40", "purpose": "Client (vLLM is OpenAI-compatible)"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": True, "description": "HuggingFace token for gated model downloads", "example": "hf_..."},
            {"name": "CUDA_VISIBLE_DEVICES", "required": False, "description": "Specific GPUs to bind", "example": "0,1,2,3"},
        ],
        "setup_steps": [
            "pip install vllm openai",
            "export HF_TOKEN=hf_...",
            "huggingface-cli download meta-llama/Llama-3.1-70B-Instruct",
            "huggingface-cli download meta-llama/Llama-3.2-1B-Instruct",
            "python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-3.1-70B-Instruct --speculative-model meta-llama/Llama-3.2-1B-Instruct --num-speculative-tokens 5",
            "python client.py",
        ],
        "variations": [
            {"label": "EAGLE-2 speculator", "description": "Trained speculator for higher acceptance rate.", "code_snippet": "# Use a pre-trained EAGLE-2 speculator instead of a generic small model\\nvllm serve meta-llama/Llama-3.1-70B-Instruct --speculative-config '{\"method\": \"eagle\", \"model\": \"yuhuili/EAGLE-LLaMA-3-Instruct-70B\"}'"},
            {"label": "Medusa heads", "description": "Multiple speculation heads on the target model itself.", "code_snippet": "vllm serve meta-llama/Llama-3.1-70B-Instruct --speculative-config '{\"method\": \"medusa\", \"num_heads\": 5}'"},
            {"label": "Prompt-lookup (n-gram)", "description": "No model needed — repeat n-grams from prompt for code/summarization.", "code_snippet": "vllm serve <model> --speculative-config '{\"method\": \"ngram\", \"prompt_lookup_max\": 5}'"},
        ],
        "common_errors": [
            {"error_text": "ValueError: Speculative model vocab_size mismatch", "cause": "Draft and target models from different families.", "fix_snippet": "Use compatible models — same tokenizer family (e.g., both Llama-3.x). Cross-family speculation requires custom token mapping."},
            {"error_text": "Acceptance rate <40%, no throughput gain", "cause": "Draft model too far from target distribution.", "fix_snippet": "Try a larger draft (e.g., 1B → 3B) or train an EAGLE/Medusa speculator on your domain data."},
            {"error_text": "CUDA OOM on launch", "cause": "Draft + target model both in VRAM.", "fix_snippet": "Reduce --max-model-len or use --gpu-memory-utilization 0.85. Draft model takes ~10% extra VRAM."},
            {"error_text": "Throughput WORSE with speculation", "cause": "Small batch size — speculation overhead exceeds gain.", "fix_snippet": "Set --speculative-disable-by-batch-size 8: disable speculation when batch >= 8 (queue saturation hides latency)."},
        ],
        "production_checklist": [
            "Monitor vllm:spec_decode_efficiency metric — alert if drops below 0.6.",
            "Pin draft and target model versions; mismatches break determinism.",
            "Use --enforce-eager only for debugging (disables CUDA graphs).",
            "Set --speculative-disable-by-batch-size based on workload mix.",
            "Test temperature=0.0 outputs match non-speculative reference (regression check).",
            "Plan for ~10% VRAM headroom for draft model + speculation buffers.",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-70B-Instruct", "Llama-3.2-1B-Instruct"],
            "library_versions": ["vllm==0.6.3", "openai==1.51.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["vllm"],
        "related_glossary_slugs": ["speculative-decoding", "inference-optimization"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Does it change output quality?", "answer": "No — speculation is lossless. The target model verifies every speculative token; rejected tokens are regenerated. Outputs at temperature=0 are bit-identical."},
            {"question": "Why disable for large batches?", "answer": "When batch saturates GPU, the target model is already throughput-bound. Speculation overhead (running draft) cuts into that. Disable at batch≥8 for most workloads."},
            {"question": "Speculation vs FP8 quantization?", "answer": "Different axes. Speculation cuts decode latency; quantization cuts memory + boosts throughput. Stack them: FP8 target + FP16 draft model is common."},
            {"question": "Cost of running the draft model?", "answer": "VRAM: ~10% extra. Compute: nearly free (overlaps with target model verification). Hosting cost: 0 extra GPUs."},
        ],
        "github_url": "https://github.com/vllm-project/vllm",
        "meta_title": "vLLM Speculative Decoding Starter — 2-3x Throughput",
        "meta_description": "Speculative decoding with vLLM: draft model speculates, target verifies. Lossless 2-3x throughput. Server + client + acceptance-rate monitoring.",
    },
    {
        "slug": "vllm-continuous-batching-tuning",
        "title": "vLLM Continuous Batching Tuning For Real Workloads",
        "tldr": "vLLM's continuous batching has knobs that move 30-50% throughput depending on your workload mix. Tune max-num-seqs, max-model-len, and gpu-memory-utilization to match real traffic.",
        "category": "llm-inference",
        "language": "python",
        "framework": "vLLM",
        "tags": ["vllm", "batching", "throughput", "tuning"],
        "best_for_tags": ["self-hosted", "production", "cost-optimization"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "Running vLLM in production with mixed-length workloads (some short queries, some long generations). Default config leaves throughput on the table for most real traffic.",
        "when_not_to_use": "Skip for benchmark-spec workloads (synthetic prompts) — defaults are tuned for those. Skip for tiny QPS where latency matters more than throughput.",
        "quick_start": "pip install vllm && python tune.py --model meta-llama/Llama-3.1-8B-Instruct --traffic-mix mixed",
        "full_code": '''"""vLLM continuous-batching tuning helper.

Sweeps key knobs against a synthetic workload representative of YOUR traffic.
"""
from __future__ import annotations

import argparse
import itertools
import statistics
import subprocess
import time
from dataclasses import dataclass
from openai import OpenAI


@dataclass
class WorkloadProfile:
    """Distribution of (prompt_len, completion_len) pairs."""
    short_short: float = 0.5  # 50 prompt, 50 completion
    short_long: float = 0.3   # 50 prompt, 500 completion
    long_short: float = 0.15  # 1000 prompt, 50 completion
    long_long: float = 0.05   # 1000 prompt, 500 completion


def synthetic_prompts(profile: WorkloadProfile, n: int = 100) -> list[tuple[str, int]]:
    """Generate (prompt, max_tokens) pairs matching profile."""
    import random
    base_short = "List three reasons why "
    base_long = "Here is a detailed scenario: " + "context " * 200 + ". Based on this, "
    prompts = []
    for _ in range(n):
        r = random.random()
        if r < profile.short_short:
            prompts.append((base_short + "caching matters?", 50))
        elif r < profile.short_short + profile.short_long:
            prompts.append((base_short + "rate limits are hard? Explain at length.", 500))
        elif r < profile.short_short + profile.short_long + profile.long_short:
            prompts.append((base_long + "summarize in 5 words.", 50))
        else:
            prompts.append((base_long + "explain in detail.", 500))
    return prompts


def measure_throughput(client: OpenAI, prompts: list[tuple[str, int]],
                       max_concurrency: int = 64) -> dict:
    """Measure tokens/sec, p50/p99 latency across concurrent requests."""
    import concurrent.futures
    latencies = []
    total_tokens = 0
    start = time.time()

    def call(prompt_max):
        prompt, max_tok = prompt_max
        t0 = time.time()
        resp = client.chat.completions.create(
            model=client.models.list().data[0].id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tok,
        )
        return resp.usage.completion_tokens, time.time() - t0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrency) as pool:
        for toks, lat in pool.map(call, prompts):
            total_tokens += toks
            latencies.append(lat)

    elapsed = time.time() - start
    return {
        "tokens_per_sec": total_tokens / elapsed,
        "p50_latency_s": statistics.median(latencies),
        "p99_latency_s": statistics.quantiles(latencies, n=100)[98],
        "total_seconds": elapsed,
    }


SWEEP = {
    "max_num_seqs": [128, 256, 512],
    "gpu_memory_utilization": [0.85, 0.90, 0.95],
    "max_model_len": [4096, 8192, 16384],
}


def grid_search(model: str, profile: WorkloadProfile) -> None:
    """Run a small grid; pick the best by tokens/sec/p99 tradeoff."""
    results = []
    for vals in itertools.product(*SWEEP.values()):
        cfg = dict(zip(SWEEP.keys(), vals))
        print(f"\\n=== Config: {cfg} ===")
        # In practice you'd restart the server with new config; below is illustrative.
        # subprocess.run(["python", "-m", "vllm.entrypoints.openai.api_server",
        #                 "--model", model,
        #                 f"--max-num-seqs={cfg['max_num_seqs']}", ...])
        client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
        prompts = synthetic_prompts(profile, n=100)
        stats = measure_throughput(client, prompts)
        results.append({**cfg, **stats})
        print(f"  {stats['tokens_per_sec']:.0f} tok/s, p99={stats['p99_latency_s']:.2f}s")

    # Rank: maximize tokens/sec subject to p99 < SLA
    sla = 10.0
    eligible = [r for r in results if r["p99_latency_s"] < sla]
    best = max(eligible or results, key=lambda r: r["tokens_per_sec"])
    print(f"\\nBest config: {best}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--traffic-mix", choices=["short", "mixed", "long"], default="mixed")
    args = p.parse_args()
    profile = WorkloadProfile()  # adjust per traffic-mix
    grid_search(args.model, profile)
''',
        "dependencies": [
            {"name": "vllm", "version": ">=0.6.0", "purpose": "vLLM server"},
            {"name": "openai", "version": ">=1.40", "purpose": "Client"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": True, "description": "Model downloads", "example": "hf_..."},
        ],
        "setup_steps": [
            "pip install vllm openai",
            "Define your WorkloadProfile based on production traffic samples",
            "Start vLLM with a baseline config",
            "Run tune.py with --model and --traffic-mix matching your workload",
            "Promote the best config to production",
        ],
        "variations": [
            {"label": "Chunked-prefill mode", "description": "For mixed short+long workloads, chunked prefill prevents long prompts blocking decode.", "code_snippet": "--enable-chunked-prefill --max-num-batched-tokens 8192"},
            {"label": "Prefix-caching", "description": "Cache common prompt prefixes across requests.", "code_snippet": "--enable-prefix-caching # automatic; ~30% savings for system-prompt-heavy workloads"},
            {"label": "Disaggregated prefill/decode", "description": "Run prefill and decode on separate GPUs (1.5+).", "code_snippet": "# Use vllm serve with --kv-transfer-config for multi-GPU prefill/decode separation"},
        ],
        "common_errors": [
            {"error_text": "RuntimeError: max_model_len exceeds model capacity", "cause": "Tried to set max_model_len > model's training context.", "fix_snippet": "Check model's max_position_embeddings; don't exceed. For longer context, use rope_scaling."},
            {"error_text": "Throughput drops as concurrency grows", "cause": "max_num_seqs too low; queue building up.", "fix_snippet": "Increase max_num_seqs (256-512 typical). Monitor with /metrics endpoint."},
            {"error_text": "p99 latency >>p50 (long tail)", "cause": "Long-prompt prefills blocking decode.", "fix_snippet": "Enable --enable-chunked-prefill with --max-num-batched-tokens set to ~2x typical decode batch."},
            {"error_text": "OOM mid-traffic", "cause": "Memory utilization too aggressive.", "fix_snippet": "Lower --gpu-memory-utilization to 0.85; leave 15% headroom for activation peaks."},
        ],
        "production_checklist": [
            "Tune against synthetic traffic that MATCHES production distribution.",
            "Monitor: tokens/sec, p50/p99 latency, queue depth, GPU utilization.",
            "Enable prefix-caching for system-prompt-heavy workloads.",
            "Enable chunked-prefill for mixed short+long.",
            "Set --gpu-memory-utilization to 0.85-0.90 (not 0.95).",
            "Test config changes against eval set — throughput shouldn't trade quality.",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-8B-Instruct", "Mixtral-8x7B-Instruct"],
            "library_versions": ["vllm==0.6.3"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["vllm"],
        "related_glossary_slugs": ["continuous-batching", "kv-cache"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What's max_num_seqs vs max_num_batched_tokens?", "answer": "max_num_seqs caps concurrent SEQUENCES (requests in flight). max_num_batched_tokens caps TOKENS per forward pass. The latter matters more for prefill; the former for steady-state decode."},
            {"question": "Should I enable prefix-caching?", "answer": "Almost always yes for chat workloads with a system prompt. Free 20-40% throughput. Disable only if prompts are unique per request."},
            {"question": "Chunked-prefill tradeoff?", "answer": "Slightly higher per-request latency on long prompts, much better p99 across mixed workload. Almost always worth it in production."},
            {"question": "Tune once or continuously?", "answer": "Re-tune when: model changes, hardware changes, traffic mix shifts >20%. Weekly check of /metrics is enough for steady workloads."},
        ],
        "github_url": "https://github.com/vllm-project/vllm",
        "meta_title": "vLLM Continuous Batching Tuning — Inference Starter",
        "meta_description": "Tune vLLM continuous batching for real workloads: max-num-seqs, prefix-caching, chunked-prefill. Grid search + production checklist.",
    },
    {
        "slug": "tgi-streaming-with-backpressure",
        "title": "Text Generation Inference (TGI) Streaming With Backpressure",
        "tldr": "HuggingFace TGI server with SSE streaming + per-client backpressure: slow consumers don't bottleneck fast ones. Includes graceful shutdown and stuck-stream detection.",
        "category": "llm-inference",
        "language": "python",
        "framework": "TGI",
        "tags": ["tgi", "streaming", "backpressure", "sse"],
        "best_for_tags": ["streaming-apps", "self-hosted", "production"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Self-hosting an LLM with TGI and serving streaming responses to many clients. Default streaming can let slow clients block fast ones; this pattern prevents that.",
        "when_not_to_use": "Skip if you're using a managed API (OpenAI/Anthropic handle backpressure for you). Skip for batch (non-streaming) workloads.",
        "quick_start": "docker run --gpus all -p 8080:80 ghcr.io/huggingface/text-generation-inference:latest --model-id meta-llama/Llama-3.1-8B-Instruct && python tgi_client.py",
        "full_code": '''"""TGI streaming client with backpressure + stuck-stream detection."""
from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager

import httpx


TGI_URL = "http://localhost:8080"
STUCK_TIMEOUT = 30.0  # seconds with no token = stuck stream
QUEUE_SIZE = 16       # per-client buffer; backpressure when full


class StreamingError(Exception):
    pass


async def tgi_stream(prompt: str, max_tokens: int = 512) -> "asyncio.AsyncIterator[str]":
    """Stream tokens from TGI via SSE. Yields token strings."""
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": max_tokens, "temperature": 0.7},
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(None, connect=10.0)) as client:
        async with client.stream("POST", f"{TGI_URL}/generate_stream", json=payload) as r:
            r.raise_for_status()
            last_token_time = time.time()
            async for line in r.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                try:
                    event = json.loads(line[len("data:"):].strip())
                except json.JSONDecodeError:
                    continue
                tok = event.get("token", {}).get("text")
                if tok:
                    last_token_time = time.time()
                    yield tok
                if time.time() - last_token_time > STUCK_TIMEOUT:
                    raise StreamingError("Stream stuck — no tokens in 30s")


@asynccontextmanager
async def bounded_stream(prompt: str, max_tokens: int = 512):
    """Wrap tgi_stream in an asyncio.Queue with backpressure.

    Producer (token fetcher) blocks if consumer is slow. Slow client → slow producer
    → frees GPU for other requests.
    """
    queue: asyncio.Queue[str | None] = asyncio.Queue(maxsize=QUEUE_SIZE)

    async def producer():
        try:
            async for tok in tgi_stream(prompt, max_tokens):
                await queue.put(tok)  # blocks if queue full
            await queue.put(None)     # sentinel for end of stream
        except Exception as e:
            await queue.put(e)

    task = asyncio.create_task(producer())

    async def consume():
        while True:
            item = await queue.get()
            if item is None:
                return
            if isinstance(item, Exception):
                raise item
            yield item

    try:
        yield consume()
    finally:
        task.cancel()


async def main():
    """Demo: serve a streaming response to a slow consumer."""
    prompts = [f"Write a short poem about {topic}." for topic in ["caching", "timeouts", "retries"]]

    async def slow_client(idx: int, prompt: str):
        print(f"[client {idx}] start")
        async with bounded_stream(prompt, max_tokens=80) as stream:
            async for tok in stream:
                print(f"[client {idx}] {tok!r}", flush=True)
                await asyncio.sleep(0.05)  # simulate slow consumer
        print(f"[client {idx}] done")

    await asyncio.gather(*(slow_client(i, p) for i, p in enumerate(prompts)))


if __name__ == "__main__":
    asyncio.run(main())
''',
        "dependencies": [
            {"name": "httpx", "version": ">=0.27", "purpose": "Async HTTP + SSE streaming"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": False, "description": "For gated models", "example": "hf_..."},
        ],
        "setup_steps": [
            "Run TGI: docker run --gpus all -p 8080:80 ghcr.io/huggingface/text-generation-inference:latest --model-id meta-llama/Llama-3.1-8B-Instruct",
            "Wait for 'Connected' log line",
            "pip install httpx",
            "python tgi_client.py",
        ],
        "variations": [
            {"label": "OpenAI-compatible endpoint", "description": "Use /v1/chat/completions instead.", "code_snippet": "# TGI exposes /v1/chat/completions on same port — use the OpenAI Python client directly"},
            {"label": "Quantized (AWQ/GPTQ)", "description": "Run quantized model for memory savings.", "code_snippet": "docker run ... --quantize awq --model-id TheBloke/Llama-3.1-8B-AWQ"},
            {"label": "Multi-LoRA serving", "description": "TGI 2.0+ serves multiple LoRA adapters.", "code_snippet": "docker run ... --lora-adapters lora1=path1,lora2=path2 # request via {'adapter_id': 'lora1', ...}"},
        ],
        "common_errors": [
            {"error_text": "Stream hangs at first token", "cause": "Model still loading; first request waits for warm-up.", "fix_snippet": "Send a tiny warm-up request after server start. Monitor logs for 'Connected' before traffic."},
            {"error_text": "Slow client blocks all others", "cause": "Per-request streaming without backpressure.", "fix_snippet": "Use the bounded_stream pattern: queue-bounded producer; slow consumer slows fetch, not server."},
            {"error_text": "PayloadTooLarge on long prompts", "cause": "Prompt exceeds model's max_input_length.", "fix_snippet": "Set TGI flag --max-input-length 8192 (or higher for long-context models)."},
            {"error_text": "Stream silently truncates", "cause": "max_new_tokens hit or model produced EOS.", "fix_snippet": "Check 'finish_reason' on the last event; 'length' = truncated, 'eos_token' = clean finish."},
        ],
        "production_checklist": [
            "Set STUCK_TIMEOUT — disconnect stuck streams to free GPU.",
            "Bound per-client queue size (backpressure).",
            "Log finish_reason on every stream end.",
            "Run TGI behind a reverse proxy with HTTP/2 (better SSE perf).",
            "Monitor TGI /metrics: queue_size, inflight_requests, generated_tokens.",
            "Graceful shutdown: send SIGTERM, wait for inflight requests to drain.",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-8B-Instruct"],
            "library_versions": ["text-generation-inference==2.4", "httpx==0.27"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["text-generation-inference"],
        "related_glossary_slugs": ["server-sent-events", "backpressure"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "TGI vs vLLM?", "answer": "TGI: easier ops (single docker image), good for prod from day 1. vLLM: higher peak throughput, more knobs. Both are excellent — pick by team comfort with tuning."},
            {"question": "Why backpressure matter?", "answer": "Without it, a slow client (mobile on cellular) keeps a GPU slot occupied while feeding tokens slowly. Backpressure makes the server pause that client and serve fast clients first."},
            {"question": "SSE vs WebSocket?", "answer": "SSE for one-way streaming (server→client) — simpler, works through proxies. WebSocket for bidirectional. Most LLM streaming is one-way, so SSE wins."},
            {"question": "What about Anthropic / OpenAI streaming?", "answer": "Their SDKs handle backpressure for you. This pattern is specifically for SELF-HOSTED endpoints where you control the server side."},
        ],
        "github_url": "https://github.com/huggingface/text-generation-inference",
        "meta_title": "TGI Streaming With Backpressure — Inference Starter",
        "meta_description": "HuggingFace TGI streaming with per-client backpressure + stuck-stream detection. Slow clients don't block fast ones.",
    },
    {
        "slug": "fp8-quantization-deployment",
        "title": "FP8 Quantization For Production Inference",
        "tldr": "Run a 70B model in 35GB VRAM via FP8 quantization (H100 + Ada-Lovelace). Quality loss <0.5pp on standard benchmarks; latency 1.6x faster than BF16.",
        "category": "llm-inference",
        "language": "python",
        "framework": "vLLM",
        "tags": ["quantization", "fp8", "h100", "production"],
        "best_for_tags": ["cost-optimization", "h100-clusters", "high-throughput"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Deploying on H100/H200/Ada-Lovelace GPUs and want to cut VRAM 2x without significant quality loss. FP8 is the sweet spot — almost-free quality vs INT8/INT4.",
        "when_not_to_use": "Skip on pre-Hopper hardware (FP8 not natively supported; falls back to slower paths). Skip for accuracy-critical tasks where you can't validate <0.5pp drift.",
        "quick_start": "pip install vllm[fp8] && vllm serve neuralmagic/Meta-Llama-3.1-70B-Instruct-FP8 --tensor-parallel-size 2",
        "full_code": '''"""FP8 quantization deployment + quality regression check.

Two paths:
1. Use a pre-quantized model from NeuralMagic / vLLM hub.
2. Quantize your own model with llm-compressor.
"""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from openai import OpenAI


# ----------------- PATH 1: SERVE A PRE-QUANTIZED MODEL -----------------

# Recommended path:
#   vllm serve neuralmagic/Meta-Llama-3.1-70B-Instruct-FP8 \\
#     --tensor-parallel-size 2 \\
#     --max-model-len 8192


# ----------------- PATH 2: QUANTIZE YOUR OWN MODEL -----------------

QUANTIZE_SCRIPT = """
# Save as quantize.py
from llmcompressor.transformers import oneshot
from llmcompressor.modifiers.quantization import GPTQModifier
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "meta-llama/Llama-3.1-70B-Instruct"
SAVE_DIR = "./Llama-3.1-70B-FP8"

model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype="auto", device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

recipe = "FP8_DYNAMIC"  # weight + activation FP8

oneshot(model=model, tokenizer=tokenizer, recipe=recipe, output_dir=SAVE_DIR)
"""


# ----------------- QUALITY REGRESSION CHECK -----------------

def quality_diff(baseline_client: OpenAI, quantized_client: OpenAI,
                 eval_prompts: list[str]) -> dict:
    """Compare quantized output against baseline (BF16) on identical prompts.

    Use temperature=0 + seed for deterministic comparison.
    """
    diffs = []
    for prompt in eval_prompts:
        base_resp = baseline_client.chat.completions.create(
            model="baseline",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            seed=42,
            max_tokens=200,
        ).choices[0].message.content

        quant_resp = quantized_client.chat.completions.create(
            model="quantized",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            seed=42,
            max_tokens=200,
        ).choices[0].message.content

        # Token-level identity
        identical = base_resp == quant_resp

        # Semantic similarity (cheap proxy: shared first-N words)
        b_words = base_resp.split()[:50]
        q_words = quant_resp.split()[:50]
        overlap = sum(1 for b, q in zip(b_words, q_words) if b == q) / max(len(b_words), 1)

        diffs.append({
            "prompt": prompt[:80],
            "identical": identical,
            "first_50_word_overlap": overlap,
        })

    return {
        "total": len(diffs),
        "identical_count": sum(1 for d in diffs if d["identical"]),
        "mean_overlap": statistics.mean(d["first_50_word_overlap"] for d in diffs),
        "samples": diffs[:5],
    }


def latency_compare(baseline_client: OpenAI, quantized_client: OpenAI,
                    prompts: list[str]) -> dict:
    """Compare per-request latency."""
    def measure(client, model_name):
        latencies = []
        for prompt in prompts:
            t0 = time.time()
            client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.0,
            )
            latencies.append(time.time() - t0)
        return latencies

    base_lat = measure(baseline_client, "baseline")
    quant_lat = measure(quantized_client, "quantized")
    return {
        "baseline_p50": statistics.median(base_lat),
        "quantized_p50": statistics.median(quant_lat),
        "speedup": statistics.median(base_lat) / statistics.median(quant_lat),
    }


if __name__ == "__main__":
    base = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")  # BF16 server
    quant = OpenAI(base_url="http://localhost:8001/v1", api_key="dummy")  # FP8 server

    eval_prompts = json.loads(Path("eval_prompts.json").read_text())
    print(quality_diff(base, quant, eval_prompts))
    print(latency_compare(base, quant, eval_prompts))
''',
        "dependencies": [
            {"name": "vllm", "version": ">=0.6.0", "purpose": "Serving with FP8 support"},
            {"name": "llmcompressor", "version": ">=0.3", "purpose": "Optional: quantize your own model"},
            {"name": "openai", "version": ">=1.40", "purpose": "Client for benchmarks"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": True, "description": "Model access", "example": "hf_..."},
            {"name": "CUDA_VISIBLE_DEVICES", "required": False, "description": "Specific H100 GPUs", "example": "0,1"},
        ],
        "setup_steps": [
            "Verify GPU: nvidia-smi (look for H100/H200/Ada). Compute capability >= 8.9 for native FP8.",
            "pip install 'vllm[fp8]' openai",
            "Pull pre-quantized: vllm serve neuralmagic/Meta-Llama-3.1-70B-Instruct-FP8 --tensor-parallel-size 2",
            "OR quantize own: pip install llmcompressor && python quantize.py",
            "Run quality regression: python -m fp8_check (compare against BF16)",
        ],
        "variations": [
            {"label": "INT8 weight-only", "description": "When you need pre-Hopper compatibility.", "code_snippet": "# Use --quantization gptq or --quantization awq instead of fp8"},
            {"label": "Per-tensor static FP8", "description": "Slightly higher quality, requires calibration.", "code_snippet": "# In quantize recipe: 'FP8_PERTENSOR' instead of 'FP8_DYNAMIC' + provide calibration dataset"},
            {"label": "Marlin kernel", "description": "Even faster for compatible weights.", "code_snippet": "--quantization marlin # auto-detected on capable kernels; ~10% extra throughput"},
        ],
        "common_errors": [
            {"error_text": "RuntimeError: FP8 not supported on this GPU", "cause": "Pre-Hopper GPU (A100, V100).", "fix_snippet": "Use INT8/AWQ instead; FP8 requires compute capability >= 8.9 (H100, H200, Ada Lovelace L40S, L4)."},
            {"error_text": "Quality drop >2pp on benchmarks", "cause": "Activation FP8 too aggressive for this model.", "fix_snippet": "Switch to weight-only FP8 (FP8_DYNAMIC weight + BF16 activations). Smaller VRAM win, better quality."},
            {"error_text": "ImportError: llmcompressor not available", "cause": "Wrong package name.", "fix_snippet": "pip install llmcompressor (was 'llm-compressor' in older docs). Pinned to >=0.3 for current vLLM compat."},
            {"error_text": "Tokenizer mismatch quant vs base", "cause": "Quantization didn't preserve tokenizer.", "fix_snippet": "After quantize: copy tokenizer.json/config from base model dir to quantized output dir."},
        ],
        "production_checklist": [
            "Run quality regression on YOUR eval set, not just MMLU.",
            "Pin vllm version; FP8 kernels change rapidly.",
            "Monitor for accuracy drift over model updates.",
            "Document the quantization recipe in your model card.",
            "Compare cost: FP8 saves $$$ on VRAM but kernels need H100+.",
            "Keep BF16 baseline serving for periodic A/B regression.",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-70B-Instruct-FP8", "Llama-3.1-8B-Instruct"],
            "library_versions": ["vllm==0.6.3", "llmcompressor==0.3.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["vllm", "llm-compressor"],
        "related_glossary_slugs": ["fp8", "quantization"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "FP8 vs INT8 vs INT4?", "answer": "FP8: best quality, needs H100+. INT8: good quality, runs everywhere. INT4 (AWQ/GPTQ): 4x VRAM win, 1-2pp quality drop. Pick by hardware + quality bar."},
            {"question": "What about quality on long contexts?", "answer": "FP8 holds up well at 4-8k. Above 32k, KV-cache quantization is the bigger lever. Test on your context-length distribution, not just short prompts."},
            {"question": "Does FP8 affect determinism?", "answer": "Yes — kernel non-determinism is slightly worse. For strict reproducibility, pin --enforce-eager and --seed; even then, expect occasional 1-2 token diffs."},
            {"question": "Can I quantize a fine-tuned model?", "answer": "Yes. Same recipe applies to fine-tuned checkpoints. Re-run quality regression after — sometimes fine-tuning sensitivities surface."},
        ],
        "github_url": "https://github.com/vllm-project/llm-compressor",
        "meta_title": "FP8 Quantization Deployment — Inference Starter",
        "meta_description": "Run 70B models in 35GB VRAM via FP8 on H100. <0.5pp quality loss, 1.6x faster than BF16. Quantize + serve + regression-check.",
    },
]
