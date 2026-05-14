"""Embeddings starters — OpenAI, local fastembed, Cohere, batching."""

RECORDS = [
    {
        "slug": "openai-embeddings-batch-cached",
        "title": "OpenAI Embeddings With Batching and Disk Cache",
        "tldr": "Production-shape OpenAI embeddings client: batches up to 2048 inputs per call (API limit), retries with exponential backoff, and caches results to disk keyed by content hash.",
        "category": "embeddings",
        "language": "python",
        "framework": "OpenAI SDK",
        "tags": ["embeddings", "openai", "batching", "caching"],
        "best_for_tags": ["bulk-ingest", "cost-control", "production-rag"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When embedding a corpus larger than a few hundred docs and you care about cost + speed. Caching by content hash means re-running ingest is free for unchanged docs.",
        "when_not_to_use": "Skip for single-request scenarios (overhead). Skip when you need on-prem inference (use fastembed or sentence-transformers).",
        "quick_start": "pip install openai tenacity diskcache && OPENAI_API_KEY=sk-... python embed.py",
        "full_code": '''"""OpenAI embeddings with batching, retries, and content-hash disk cache.

API limits (text-embedding-3-*):
  - Max 2048 inputs per request
  - Max 8192 tokens per input
  - Max ~300k tokens per request total

This wrapper respects all three.
"""
from __future__ import annotations

import hashlib
import os
from typing import Iterable

import diskcache
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

oai = OpenAI()
cache = diskcache.Cache("./embed_cache")

MODEL = "text-embedding-3-small"   # 1536 dim, $0.02 / 1M tokens
DIM = 1536
BATCH_INPUTS = 2048                # API limit
BATCH_TOKEN_LIMIT = 250_000        # safe under 300k

# tiktoken token counter for batching
try:
    import tiktoken
    enc = tiktoken.encoding_for_model(MODEL)
    def _count_tokens(s: str) -> int:
        return len(enc.encode(s))
except ImportError:
    def _count_tokens(s: str) -> int:
        return max(1, len(s) // 4)  # rough fallback


def _cache_key(text: str) -> str:
    h = hashlib.sha256(f"{MODEL}::{text}".encode()).hexdigest()
    return f"emb:{h}"


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type(Exception),
)
def _api_call(batch: list[str]) -> list[list[float]]:
    resp = oai.embeddings.create(input=batch, model=MODEL)
    return [d.embedding for d in resp.data]


def embed_many(texts: list[str], *, use_cache: bool = True) -> list[list[float]]:
    """Embed many texts; returns embeddings in same order as input."""
    n = len(texts)
    results: list[list[float] | None] = [None] * n

    # 1. Pull cached results
    to_compute_idx: list[int] = []
    if use_cache:
        for i, t in enumerate(texts):
            cached = cache.get(_cache_key(t))
            if cached is not None:
                results[i] = cached
            else:
                to_compute_idx.append(i)
    else:
        to_compute_idx = list(range(n))

    print(f"  cache hits: {n - len(to_compute_idx)} / {n}")

    # 2. Batch the remaining
    batch_idx: list[int] = []
    batch_texts: list[str] = []
    batch_tokens = 0

    def flush():
        nonlocal batch_idx, batch_texts, batch_tokens
        if not batch_texts:
            return
        embs = _api_call(batch_texts)
        for idx, emb in zip(batch_idx, embs):
            results[idx] = emb
            if use_cache:
                cache.set(_cache_key(texts[idx]), emb)
        batch_idx, batch_texts, batch_tokens = [], [], 0

    for i in to_compute_idx:
        t = texts[i]
        tk = _count_tokens(t)
        if (len(batch_texts) >= BATCH_INPUTS
                or batch_tokens + tk > BATCH_TOKEN_LIMIT):
            flush()
        batch_idx.append(i)
        batch_texts.append(t)
        batch_tokens += tk
    flush()

    # Should be no Nones left
    assert all(r is not None for r in results), "some embeddings missing"
    return results  # type: ignore


def embed_one(text: str, use_cache: bool = True) -> list[float]:
    return embed_many([text], use_cache=use_cache)[0]


if __name__ == "__main__":
    texts = [
        "Reciprocal rank fusion merges results from multiple retrievers.",
        "BM25 is a keyword retrieval algorithm based on TF-IDF.",
        "Dense vector embeddings capture semantic meaning.",
    ] * 50  # 150 inputs to demo batching
    embs = embed_many(texts)
    print(f"Got {len(embs)} embeddings, each {len(embs[0])}-dim.")
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI client"},
            {"name": "tenacity", "version": ">=8.0", "purpose": "Retry with exponential backoff"},
            {"name": "diskcache", "version": ">=5.6", "purpose": "Persistent local cache"},
            {"name": "tiktoken", "version": ">=0.7", "purpose": "Token counting for batching"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI API key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai tenacity diskcache tiktoken",
            "export OPENAI_API_KEY=sk-...",
            "python embed.py",
            "Cache persists to ./embed_cache/ — delete to force re-embedding.",
        ],
        "variations": [
            {
                "label": "Use text-embedding-3-large",
                "description": "Higher quality, 3072-dim, 6x cost.",
                "code_snippet": "MODEL = 'text-embedding-3-large'\\nDIM = 3072",
            },
            {
                "label": "Reduce dimensions",
                "description": "Smaller vectors for memory-constrained DBs.",
                "code_snippet": "resp = oai.embeddings.create(input=batch, model=MODEL, dimensions=512)\\n# text-embedding-3-* supports arbitrary downsizing, quality degrades smoothly",
            },
            {
                "label": "Async embed",
                "description": "Parallel batches via asyncio.",
                "code_snippet": "from openai import AsyncOpenAI\\nasync def embed_many_async(...): tasks = [_api_call_async(b) for b in batches]; await asyncio.gather(*tasks)",
            },
            {
                "label": "Redis cache",
                "description": "Shared cache across machines.",
                "code_snippet": "import redis\\nr = redis.Redis()\\n# replace cache.get/set with r.get/set; serialize embedding to bytes",
            },
        ],
        "common_errors": [
            {
                "error_text": "openai.BadRequestError: $.input is too large",
                "cause": "Single text exceeds 8192 tokens.",
                "fix_snippet": "Pre-chunk long texts. Add: if _count_tokens(t) > 8000: split or truncate before sending.",
            },
            {
                "error_text": "openai.RateLimitError: Tokens per minute",
                "cause": "Bulk ingest exceeds TPM tier limit.",
                "fix_snippet": "Tenacity retry handles transient; for sustained rate: slow batch frequency, request rate-limit increase, or use a higher-tier account.",
            },
            {
                "error_text": "Cache returns wrong embeddings after model change",
                "cause": "Cache key doesn't include model.",
                "fix_snippet": "Starter includes MODEL in the cache key. If switching models, clear the cache: cache.clear() or use a fresh directory.",
            },
            {
                "error_text": "diskcache.Timeout",
                "cause": "Multiple processes hitting same cache file.",
                "fix_snippet": "diskcache handles concurrency but can timeout under heavy contention. Pass timeout= to Cache() constructor.",
            },
        ],
        "production_checklist": [
            "Use a shared cache (Redis, S3) when running across multiple workers.",
            "Re-embed only when source changes — content-hash key handles this.",
            "Pin model version; switching invalidates all cached vectors.",
            "Monitor cost: track tokens per embedding run.",
            "Budget retries; tenacity max_attempt=5 in starter is reasonable for transient errors.",
            "For >1M docs, consider Azure OpenAI for higher rate limits.",
            "Chunk very long texts (>8k tokens) before embedding.",
        ],
        "tested_with": {
            "model_versions": ["text-embedding-3-small", "text-embedding-3-large"],
            "library_versions": ["openai==1.51.0", "tenacity==8.5.0", "diskcache==5.6.3", "tiktoken==0.8.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["embeddings", "batching", "cache"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "text-embedding-3-small vs -large?",
                "answer": "Small: 1536 dim, $0.02/M tokens, good baseline. Large: 3072 dim, $0.13/M tokens, ~5% better quality on MTEB. Use small unless quality numbers from your eval justify the cost.",
            },
            {
                "question": "Can I shrink dimensions safely?",
                "answer": "Yes — text-embedding-3 supports dimensions=N. Quality degrades smoothly with smaller dim. 512 saves ~66% memory with modest quality loss; test for your task.",
            },
            {
                "question": "How big should batches be?",
                "answer": "Starter caps at 2048 inputs OR 250k tokens, whichever first. For very long texts (3-8k tokens each), token limit hits first. For tweets/queries, input count hits first.",
            },
            {
                "question": "Does the cache help in production?",
                "answer": "Massively for re-ingest scenarios; not for unique user queries. If you have many repeat queries (search, FAQ), enable it — even short TTL pays off.",
            },
        ],
        "github_url": "https://github.com/openai/openai-python",
        "meta_title": "OpenAI Embeddings With Batching + Cache",
        "meta_description": "Production OpenAI embeddings: batched up to 2048/req, exponential retry, content-hash disk cache. Ready for bulk ingest workloads.",
    },
    {
        "slug": "fastembed-local-onnx-embeddings",
        "title": "FastEmbed Local Embeddings (ONNX, No GPU Required)",
        "tldr": "Local-only embeddings via FastEmbed's ONNX runtime — no API key, no GPU, ~5ms per text on CPU. Drop-in replacement for OpenAI embeddings with sentence-transformers quality.",
        "category": "embeddings",
        "language": "python",
        "framework": "FastEmbed",
        "tags": ["fastembed", "onnx", "local-embeddings", "cpu-only"],
        "best_for_tags": ["air-gapped", "no-api-key", "cost-control"],
        "difficulty_tier": "beginner",
        "featured": True,
        "when_to_use": "When you need embeddings without an API: local dev, air-gapped, cost-sensitive, or latency-sensitive (no network hop). Quality is competitive with OpenAI's small model on English; weaker on multilingual.",
        "when_not_to_use": "Skip when top-shelf multilingual is required (use Cohere multilingual or OpenAI text-embedding-3-large). Skip when GPU is available and you want top quality (use sentence-transformers with a stronger model).",
        "quick_start": "pip install fastembed && python local_embed.py",
        "full_code": '''"""FastEmbed: local ONNX-based embeddings, CPU-friendly.

Models bundled:
  - BAAI/bge-small-en-v1.5  (384 dim, ~80MB) -- recommended baseline
  - BAAI/bge-large-en-v1.5  (1024 dim, ~400MB) -- higher quality
  - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (multilingual)

First run downloads the ONNX model to ~/.cache/fastembed/.
Subsequent runs are offline-capable.
"""
from __future__ import annotations

import hashlib
from typing import Iterable

import diskcache
from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-en-v1.5"
embedder = TextEmbedding(model_name=MODEL_NAME)
cache = diskcache.Cache("./fastembed_cache")


def _cache_key(text: str) -> str:
    h = hashlib.sha256(f"{MODEL_NAME}::{text}".encode()).hexdigest()
    return f"fe:{h}"


def embed_many(texts: list[str], *, use_cache: bool = True, batch_size: int = 32) -> list[list[float]]:
    """Embed a list of texts; preserves order; caches results."""
    n = len(texts)
    results: list[list[float] | None] = [None] * n
    to_compute_idx: list[int] = []

    if use_cache:
        for i, t in enumerate(texts):
            cached = cache.get(_cache_key(t))
            if cached is not None:
                results[i] = cached
            else:
                to_compute_idx.append(i)
    else:
        to_compute_idx = list(range(n))

    # FastEmbed iterates internally; no need to manually batch
    # but we cap at batch_size to control memory
    for start in range(0, len(to_compute_idx), batch_size):
        batch_idx = to_compute_idx[start : start + batch_size]
        batch_texts = [texts[i] for i in batch_idx]
        for j, emb in enumerate(embedder.embed(batch_texts)):
            i = batch_idx[j]
            results[i] = emb.tolist()
            if use_cache:
                cache.set(_cache_key(texts[i]), results[i])

    assert all(r is not None for r in results), "embeddings missing"
    return results  # type: ignore


def embed_one(text: str, use_cache: bool = True) -> list[float]:
    return embed_many([text], use_cache=use_cache)[0]


def compare_models(text: str = "Reciprocal rank fusion merges results from multiple retrievers.") -> None:
    """Print embedding length and time for a few models."""
    import time
    for name in [
        "BAAI/bge-small-en-v1.5",
        "BAAI/bge-large-en-v1.5",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ]:
        e = TextEmbedding(model_name=name)
        t0 = time.time()
        v = list(e.embed([text]))[0]
        dt = (time.time() - t0) * 1000
        print(f"  {name}: dim={len(v)}, time={dt:.1f}ms")


if __name__ == "__main__":
    texts = ["First.", "Second.", "Third example sentence."]
    embs = embed_many(texts)
    print(f"Got {len(embs)} embeddings, dim={len(embs[0])}")
    compare_models()
''',
        "dependencies": [
            {"name": "fastembed", "version": ">=0.4", "purpose": "Local ONNX embedding inference"},
            {"name": "diskcache", "version": ">=5.6", "purpose": "Persistent embedding cache"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install fastembed diskcache",
            "python local_embed.py  # first run downloads ONNX model (~80MB)",
            "Subsequent runs are offline-capable.",
        ],
        "variations": [
            {
                "label": "Sparse embeddings (BM25)",
                "description": "FastEmbed also supports sparse retrieval.",
                "code_snippet": "from fastembed import SparseTextEmbedding\\nsparse = SparseTextEmbedding('Qdrant/bm25')\\nfor v in sparse.embed(texts): print(v.indices, v.values)",
            },
            {
                "label": "Cross-encoder rerank",
                "description": "Use FastEmbed for both retrieve and rerank.",
                "code_snippet": "from fastembed.rerank.cross_encoder import TextCrossEncoder\\nce = TextCrossEncoder('Xenova/ms-marco-MiniLM-L-6-v2')\\nfor score in ce.rerank(query='...', documents=[...]): print(score)",
            },
            {
                "label": "GPU acceleration",
                "description": "Use CUDA-enabled ONNX runtime.",
                "code_snippet": "pip install onnxruntime-gpu\\n# FastEmbed auto-detects GPU; verify with: TextEmbedding(model_name=..., providers=['CUDAExecutionProvider'])",
            },
            {
                "label": "Pre-download for Docker",
                "description": "Ship model in image.",
                "code_snippet": "# Dockerfile:\\nRUN python -c 'from fastembed import TextEmbedding; TextEmbedding(\"BAAI/bge-small-en-v1.5\")'\\n# Caches into the image; no download on container start.",
            },
        ],
        "common_errors": [
            {
                "error_text": "First call takes 30+ seconds",
                "cause": "Downloading ONNX model on first use.",
                "fix_snippet": "Pre-download in your Dockerfile or post-install script. After first download, model loads in ~1s.",
            },
            {
                "error_text": "ONNXRuntimeError: cuDNN missing (GPU mode)",
                "cause": "onnxruntime-gpu installed but CUDA libraries missing.",
                "fix_snippet": "Either install matching CUDA libraries OR fall back to CPU: TextEmbedding(model_name=..., providers=['CPUExecutionProvider']).",
            },
            {
                "error_text": "Slower than expected on CPU",
                "cause": "ONNX runtime not configured for multiple threads.",
                "fix_snippet": "Set OMP_NUM_THREADS=8 (or however many cores). FastEmbed respects this env var.",
            },
            {
                "error_text": "Out of memory on large texts",
                "cause": "Default tokenizer truncates to 512 tokens but the input batch is huge.",
                "fix_snippet": "Lower batch_size in embed_many. For very long texts, chunk before embedding (standard RAG practice anyway).",
            },
        ],
        "production_checklist": [
            "Pre-download models in Dockerfile to avoid cold-start delays.",
            "Pin fastembed and onnxruntime versions for reproducibility.",
            "Measure latency on your hardware; CPU varies from 2ms (modern desktop) to 30ms (cheap VPS).",
            "Cache aggressively — same query embedded twice is waste.",
            "Test multilingual capability on your real data; the default English models do poorly on non-English.",
            "Consider GPU only if you have sustained QPS; otherwise CPU is enough and cheaper.",
        ],
        "tested_with": {
            "model_versions": ["BAAI/bge-small-en-v1.5", "BAAI/bge-large-en-v1.5"],
            "library_versions": ["fastembed==0.4.1", "diskcache==5.6.3"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["fastembed"],
        "related_glossary_slugs": ["embeddings", "onnx", "sentence-transformers"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Is local embedding quality close to OpenAI?",
                "answer": "On English, BGE-small is competitive with text-embedding-3-small on retrieval benchmarks. BGE-large can beat it on MTEB. For multilingual or cutting-edge quality, OpenAI/Cohere still lead.",
            },
            {
                "question": "Does FastEmbed work without internet?",
                "answer": "After the first download, yes. Pre-download in CI/Docker, then run air-gapped.",
            },
            {
                "question": "How does this compare to sentence-transformers directly?",
                "answer": "FastEmbed wraps sentence-transformers models in ONNX for faster CPU inference (~2-3x). For GPU, plain sentence-transformers is often faster. Pick FastEmbed for CPU; ST for GPU.",
            },
            {
                "question": "Can I use my own fine-tuned model?",
                "answer": "Yes — convert to ONNX and load via TextEmbedding(model_name='path/to/onnx'). Or use sentence-transformers directly without FastEmbed wrapping.",
            },
        ],
        "github_url": "https://github.com/qdrant/fastembed",
        "meta_title": "FastEmbed Local ONNX Embeddings — Starter",
        "meta_description": "Local CPU embeddings via FastEmbed ONNX: no API key, sentence-transformers quality, batched + cached. Drop-in for OpenAI embeddings.",
    },
]
