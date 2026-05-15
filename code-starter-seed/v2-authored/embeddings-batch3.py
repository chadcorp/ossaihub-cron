"""Embedding starters — batch 3: matryoshka, batched async, evaluation, voyage."""

RECORDS = [
    {
        "slug": "matryoshka-embeddings-truncation",
        "title": "Matryoshka Embeddings (Truncate For Speed + Storage)",
        "tldr": "Matryoshka embeddings (e.g., text-embedding-3-large) let you TRUNCATE the vector to fewer dimensions without re-embedding. 1536 → 512 dims saves 3x storage + RAM with minor recall loss.",
        "category": "embeddings",
        "language": "python",
        "framework": "OpenAI / sentence-transformers",
        "tags": ["matryoshka", "embeddings", "dimension-reduction", "openai"],
        "best_for_tags": ["storage-cost", "ram-constraint", "large-corpora"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Large-scale embedding storage. Truncate matryoshka embeddings to fewer dimensions for cheaper storage / faster ANN. The model was trained for this — recall stays close.",
        "when_not_to_use": "Skip for non-matryoshka models (truncation destroys recall). Skip when storage / RAM isn't a constraint. Skip if you need every last % of recall.",
        "quick_start": "pip install openai numpy && python matryoshka.py",
        "full_code": '''"""Matryoshka embeddings: truncate-then-normalize for storage savings."""
from __future__ import annotations

import os
import numpy as np
from openai import OpenAI


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def embed_matryoshka(texts: list[str], target_dim: int = 512,
                     model: str = "text-embedding-3-large") -> np.ndarray:
    """Get embeddings; truncate to target_dim (server-side, normalized)."""
    response = client.embeddings.create(
        model=model,
        input=texts,
        dimensions=target_dim,
    )
    return np.array([e.embedding for e in response.data])


def sweep_dimensions(texts: list[str], queries: list[str]):
    """Compare recall@5 across truncated dims vs full-dim baseline."""
    full_dim = embed_matryoshka(texts, target_dim=3072)
    full_queries = embed_matryoshka(queries, target_dim=3072)

    full_sims = full_queries @ full_dim.T
    ground_truth_per_q = [np.argsort(-row)[:5].tolist() for row in full_sims]

    for dim in [256, 512, 768, 1024, 1536, 3072]:
        trunc_corpus = embed_matryoshka(texts, target_dim=dim)
        trunc_queries = embed_matryoshka(queries, target_dim=dim)
        trunc_sims = trunc_queries @ trunc_corpus.T

        recalls = []
        for i, gt in enumerate(ground_truth_per_q):
            top_k = np.argsort(-trunc_sims[i])[:5].tolist()
            recalls.append(len(set(top_k) & set(gt)) / 5)

        storage_kb = (len(texts) * dim * 4) / 1024
        print(f"dim={dim:>4} | recall@5 vs 3072: {np.mean(recalls):.3f} | storage: {storage_kb:.1f} KB")


def hierarchical_search(query: str, texts: list[str], k_initial: int = 50, k_final: int = 10):
    """Two-pass: small-dim for initial recall, full-dim for final precision."""
    small_corpus = embed_matryoshka(texts, target_dim=256)
    small_query = embed_matryoshka([query], target_dim=256)
    small_sims = (small_query @ small_corpus.T).flatten()
    candidates_idx = np.argsort(-small_sims)[:k_initial]

    candidate_texts = [texts[i] for i in candidates_idx]
    full_corpus = embed_matryoshka(candidate_texts, target_dim=3072)
    full_query = embed_matryoshka([query], target_dim=3072)
    full_sims = (full_query @ full_corpus.T).flatten()
    final_local = np.argsort(-full_sims)[:k_final]
    return [(candidates_idx[i], full_sims[i]) for i in final_local]


if __name__ == "__main__":
    corpus = [
        "Rate limiting prevents API abuse.",
        "Caching reduces latency by storing responses.",
        "OAuth 2.0 is the standard for authentication flows.",
        "PostgreSQL is a relational database.",
        "Vector databases store high-dimensional embeddings.",
    ]
    queries = ["How do I limit requests?", "Speed up my API"]
    sweep_dimensions(corpus, queries)

    print("\\nHierarchical search:")
    for idx, sim in hierarchical_search("speed up my API", corpus, k_final=3):
        print(f"  {sim:.3f}: {corpus[idx][:60]}")
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI embedding API"},
            {"name": "numpy", "version": ">=1.26", "purpose": "Vector math"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai numpy",
            "export OPENAI_API_KEY=sk-...",
            "python matryoshka.py",
            "Run sweep_dimensions on your corpus to find the right truncation",
        ],
        "variations": [
            {"label": "Local matryoshka (Nomic-embed)", "description": "OSS model with matryoshka support.", "code_snippet": "from sentence_transformers import SentenceTransformer\\nmodel = SentenceTransformer('nomic-ai/nomic-embed-text-v1.5', truncate_dim=512)"},
            {"label": "PCA on non-matryoshka", "description": "Approximate dimension reduction for non-matryoshka models.", "code_snippet": "# Train PCA on your corpus; apply to all embeds. Lossy but works for any model."},
            {"label": "Quantize after truncate", "description": "Combine for max compression.", "code_snippet": "# Truncate to 512, then quantize to int8 (1/4 storage). Use FAISS IndexBinaryFlat or pgvector halfvec."},
        ],
        "common_errors": [
            {"error_text": "Recall drops sharply at low dim", "cause": "Non-matryoshka model.", "fix_snippet": "Truncation only works for models TRAINED with matryoshka loss. text-embedding-3, nomic-embed-text-v1.5, mxbai-embed-large. Most older models DON'T."},
            {"error_text": "Vectors not L2-normalized after truncation", "cause": "Forgot to renormalize.", "fix_snippet": "OpenAI handles via 'dimensions' parameter. Manual: emb = emb[:dim]; emb /= np.linalg.norm(emb)."},
            {"error_text": "Re-ranker doesn't beat single-pass", "cause": "k_initial too small.", "fix_snippet": "Set k_initial high enough for recall (typically 5-10x final k)."},
            {"error_text": "Cost not lower as expected", "cause": "OpenAI charges per token, not dim.", "fix_snippet": "Matryoshka saves STORAGE/RAM/query-time, not embedding cost. Cost is fixed per token."},
        ],
        "production_checklist": [
            "Verify your model supports matryoshka before truncating.",
            "Run recall@k sweep on YOUR data; don't trust benchmarks.",
            "Re-embed at full dim if you change truncation target.",
            "Combine with int8 quantization for max compression.",
            "Use hierarchical search for biggest wins on large corpora.",
            "Document target_dim in your vector schema / model card.",
        ],
        "tested_with": {
            "model_versions": ["text-embedding-3-large"],
            "library_versions": ["openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["openai", "nomic-embed"],
        "related_glossary_slugs": ["matryoshka-embeddings", "dimension-reduction"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How much recall is lost?", "answer": "For matryoshka models, 1536→512 typically loses 2-5pp recall@10. 1536→256 can lose 10-15pp. Sweep YOUR data to find acceptable tradeoff."},
            {"question": "Matryoshka vs binary quantization?", "answer": "Matryoshka: trade DIMS for accuracy. Binary: trade PRECISION (1 bit/dim) for storage. Combine: truncate then binary-quantize for 32x compression."},
            {"question": "When is hierarchical search worth it?", "answer": "Large corpora (>1M vectors) where full-dim search is expensive. Small-dim ANN narrows fast; full-dim re-ranks for precision. ~10x speedup typical."},
            {"question": "Which models support matryoshka?", "answer": "OpenAI text-embedding-3 family, nomic-embed-text-v1.5, mxbai-embed-large-v1, snowflake-arctic-embed-l. Check model card."},
        ],
        "github_url": "https://github.com/openai/openai-python",
        "meta_title": "Matryoshka Embeddings Truncation Starter",
        "meta_description": "Truncate matryoshka embeddings (text-embedding-3) for 3x storage savings: dimension-sweep recall test + hierarchical search.",
    },
    {
        "slug": "batched-async-embeddings-pipeline",
        "title": "Batched Async Embeddings Pipeline",
        "tldr": "Embed 100k+ documents efficiently: batch by tokens, parallelize with asyncio, retry transient errors, checkpoint progress. Pattern handles real-world corpora.",
        "category": "embeddings",
        "language": "python",
        "framework": "OpenAI + asyncio",
        "tags": ["embeddings", "batch", "async", "ingestion"],
        "best_for_tags": ["large-corpora", "ingestion-pipelines", "data-engineering"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Embedding hundreds of thousands or millions of documents. Sequential calls take days; this pattern does it in hours. Includes checkpointing so failures don't lose progress.",
        "when_not_to_use": "Skip for small corpora (<10k docs; sync is fine). Skip if you can use OpenAI Batch API for cheaper non-real-time embedding.",
        "quick_start": "pip install openai tiktoken tqdm && python batch_embed.py --input docs.jsonl",
        "full_code": '''"""Batched async embedding pipeline with checkpointing."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

import numpy as np
import tiktoken
from openai import AsyncOpenAI
from tqdm import tqdm


client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
encoder = tiktoken.encoding_for_model("text-embedding-3-small")

MAX_TOKENS_PER_BATCH = 8000
MAX_CONCURRENT_REQUESTS = 10
MAX_DOC_TOKENS = 8000


def batch_by_tokens(docs: list[dict], max_tokens: int = MAX_TOKENS_PER_BATCH):
    """Group docs into batches each under max_tokens."""
    batches: list[list[dict]] = []
    current: list[dict] = []
    current_tokens = 0
    for doc in docs:
        n = len(encoder.encode(doc["text"]))
        if n > MAX_DOC_TOKENS:
            doc["text"] = encoder.decode(encoder.encode(doc["text"])[:MAX_DOC_TOKENS])
            n = MAX_DOC_TOKENS
        if current_tokens + n > max_tokens:
            if current:
                batches.append(current)
            current, current_tokens = [], 0
        current.append(doc)
        current_tokens += n
    if current:
        batches.append(current)
    return batches


async def embed_batch(batch: list[dict], semaphore: asyncio.Semaphore,
                      model: str = "text-embedding-3-small") -> list[dict]:
    async with semaphore:
        for attempt in range(5):
            try:
                response = await client.embeddings.create(
                    model=model,
                    input=[d["text"] for d in batch],
                )
                for d, e in zip(batch, response.data):
                    d["embedding"] = e.embedding
                return batch
            except Exception as e:
                if attempt == 4:
                    print(f"FAIL batch (ids={[d['id'] for d in batch]}): {e}")
                    for d in batch:
                        d["embedding"] = None
                    return batch
                await asyncio.sleep(2 ** attempt)


def load_checkpoint(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()
    with output_path.open() as f:
        return {json.loads(line)["id"] for line in f}


def append_checkpoint(output_path: Path, batch: list[dict]):
    with output_path.open("a") as f:
        for d in batch:
            f.write(json.dumps(d) + "\\n")


async def run(input_path: Path, output_path: Path):
    docs = [json.loads(line) for line in input_path.read_text().splitlines() if line.strip()]
    done = load_checkpoint(output_path)
    todo = [d for d in docs if d["id"] not in done]
    print(f"Total: {len(docs)}, done: {len(done)}, todo: {len(todo)}")

    batches = batch_by_tokens(todo)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    pbar = tqdm(total=len(todo))
    tasks = [embed_batch(batch, semaphore) for batch in batches]
    for task in asyncio.as_completed(tasks):
        batch = await task
        append_checkpoint(output_path, batch)
        pbar.update(len(batch))
    pbar.close()


def to_npz(output_path: Path, npz_path: Path):
    embeddings, ids = [], []
    with output_path.open() as f:
        for line in f:
            d = json.loads(line)
            if d.get("embedding"):
                ids.append(d["id"])
                embeddings.append(d["embedding"])
    np.savez(npz_path, embeddings=np.array(embeddings), ids=np.array(ids))
    print(f"Saved {npz_path}: {len(ids)} embeddings")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="embeddings.jsonl")
    parser.add_argument("--npz", default="embeddings.npz")
    args = parser.parse_args()
    asyncio.run(run(Path(args.input), Path(args.output)))
    to_npz(Path(args.output), Path(args.npz))
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "Async client"},
            {"name": "tiktoken", "version": ">=0.7", "purpose": "Token counting"},
            {"name": "numpy", "version": ">=1.26", "purpose": "Array packing"},
            {"name": "tqdm", "version": ">=4.66", "purpose": "Progress bar"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai tiktoken numpy tqdm",
            "Prepare JSONL: {id, text} per line",
            "python batch_embed.py --input docs.jsonl --output embeddings.jsonl --npz embeddings.npz",
            "Resume on crash: re-run; skips already-embedded IDs",
        ],
        "variations": [
            {"label": "OpenAI Batch API (50% cheaper)", "description": "Non-real-time, batched async API.", "code_snippet": "# Upload JSONL via client.files.create; create batch via client.batches.create(endpoint='/v1/embeddings'). 24h SLA. Half cost."},
            {"label": "Multi-provider failover", "description": "Fall back between embedding providers.", "code_snippet": "# Try OpenAI first; if 429s, switch to Voyage/Cohere. Useful for huge ingest jobs."},
            {"label": "Streaming to vector DB", "description": "Insert as you go.", "code_snippet": "# In append_checkpoint: also call vector_db.upsert(batch). Data is queryable as soon as embedded."},
        ],
        "common_errors": [
            {"error_text": "RateLimit 429 even with retry", "cause": "Per-minute / per-day quota.", "fix_snippet": "Reduce MAX_CONCURRENT_REQUESTS. Watch retry-after headers. Request quota increase via OpenAI dashboard."},
            {"error_text": "Embedding pipeline hangs", "cause": "Asyncio deadlock or stuck connection.", "fix_snippet": "Add timeout to embed_batch: asyncio.wait_for(... , timeout=60). Logs identify which batch is hanging."},
            {"error_text": "Out of memory on large corpora", "cause": "Loading all docs into memory.", "fix_snippet": "Stream docs line-by-line. Tasks generated lazily."},
            {"error_text": "Mismatched IDs vs embeddings on resume", "cause": "Crash mid-batch.", "fix_snippet": "Checkpoint per-batch (atomic file append). Pattern in code handles this."},
        ],
        "production_checklist": [
            "Token-based batching (not count-based).",
            "Checkpoint after every batch.",
            "Concurrent requests bounded by semaphore.",
            "Exponential backoff on transient errors.",
            "Use Batch API for non-real-time ingest (50% cheaper).",
            "Pack NPZ for fast load downstream.",
        ],
        "tested_with": {
            "model_versions": ["text-embedding-3-small"],
            "library_versions": ["openai==1.51", "tiktoken==0.7"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["openai", "tiktoken"],
        "related_glossary_slugs": ["embeddings", "batch-processing"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Real-time vs Batch API?", "answer": "Real-time (this code): seconds; full price. Batch API: 24-hour SLA; 50% off. Use Batch for ingest, real-time for query embeddings."},
            {"question": "Why batch by tokens, not count?", "answer": "Token limits are per-request, not per-document. 50 long docs > 8k tokens fails; 200 short docs < 8k succeeds. Batch by tokens for max throughput."},
            {"question": "How many concurrent requests?", "answer": "OpenAI Tier 4: 30 concurrent works well. Lower tiers: 5-10. Watch for 429s; reduce until stable."},
            {"question": "Checkpointing — JSONL or DB?", "answer": "JSONL is simple, append-only safe. NPZ at end for fast loading. DB checkpoint is overkill for typical ingest."},
        ],
        "github_url": "",
        "meta_title": "Batched Async Embeddings Pipeline Starter",
        "meta_description": "Embed 100k+ docs efficiently: token-based batching, async parallelism, retry, checkpointing for crash recovery, NPZ output.",
    },
    {
        "slug": "embedding-quality-evaluation",
        "title": "Embedding Quality Evaluation (BEIR-Style)",
        "tldr": "Evaluate embedding models on YOUR data: build a (query, relevant_doc) pairs set, measure recall@k / MRR / nDCG. Pick the model that wins on YOUR domain, not arXiv benchmarks.",
        "category": "embeddings",
        "language": "python",
        "framework": "Custom + sentence-transformers",
        "tags": ["embedding-eval", "recall", "mrr", "ndcg"],
        "best_for_tags": ["model-selection", "ml-engineers", "rag-quality"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Choosing between embedding models for YOUR corpus. arXiv benchmarks (MTEB) are useful starting points but not ground truth for YOUR domain. Build a 100-200 pair eval set.",
        "when_not_to_use": "Skip for one-off experiments (just pick the popular model). Skip without ANY labeled data (need at least 50 (query, doc) pairs).",
        "quick_start": "pip install sentence-transformers numpy && python embed_eval.py",
        "full_code": '''"""Evaluate multiple embedding models on YOUR (query, relevant-doc) pairs."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# ----------------- EVAL SET FORMAT -----------------

# Each line in eval_set.jsonl is:
#   {"query": "how to limit api requests", "relevant_doc_ids": ["doc_3", "doc_7"]}
# Corpus is a separate JSONL: {"id": "doc_3", "text": "..."}


# ----------------- LOAD -----------------

def load_corpus(path: Path) -> tuple[list[str], list[str]]:
    """Returns (ids, texts) in parallel arrays."""
    ids, texts = [], []
    with path.open() as f:
        for line in f:
            d = json.loads(line)
            ids.append(d["id"])
            texts.append(d["text"])
    return ids, texts


def load_eval_set(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f]


# ----------------- METRICS -----------------

def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    top_k = retrieved_ids[:k]
    return len(set(top_k) & relevant_ids) / max(len(relevant_ids), 1)


def mrr(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """Mean Reciprocal Rank: 1 / position-of-first-relevant."""
    for i, rid in enumerate(retrieved_ids):
        if rid in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Normalized Discounted Cumulative Gain."""
    dcg = sum(
        (1 if rid in relevant_ids else 0) / math.log2(i + 2)
        for i, rid in enumerate(retrieved_ids[:k])
    )
    ideal_dcg = sum(1 / math.log2(i + 2) for i in range(min(len(relevant_ids), k)))
    return dcg / ideal_dcg if ideal_dcg else 0.0


# ----------------- EVAL ONE MODEL -----------------

def evaluate_model(model_name: str, corpus_ids: list[str], corpus_texts: list[str],
                   eval_set: list[dict]) -> dict:
    print(f"\\nEvaluating {model_name}...")
    model = SentenceTransformer(model_name, trust_remote_code=True)

    corpus_emb = model.encode(corpus_texts, show_progress_bar=True, convert_to_numpy=True,
                              normalize_embeddings=True)
    query_emb = model.encode([e["query"] for e in eval_set], show_progress_bar=True,
                             convert_to_numpy=True, normalize_embeddings=True)

    metrics = {"recall@1": [], "recall@5": [], "recall@10": [], "mrr": [], "ndcg@10": []}
    for i, ex in enumerate(eval_set):
        sims = corpus_emb @ query_emb[i]
        ranked = np.argsort(-sims)
        ranked_ids = [corpus_ids[j] for j in ranked]
        relevant = set(ex["relevant_doc_ids"])

        metrics["recall@1"].append(recall_at_k(ranked_ids, relevant, 1))
        metrics["recall@5"].append(recall_at_k(ranked_ids, relevant, 5))
        metrics["recall@10"].append(recall_at_k(ranked_ids, relevant, 10))
        metrics["mrr"].append(mrr(ranked_ids, relevant))
        metrics["ndcg@10"].append(ndcg_at_k(ranked_ids, relevant, 10))

    return {k: float(np.mean(v)) for k, v in metrics.items()}


# ----------------- COMPARE -----------------

def compare_models(corpus_path: Path, eval_set_path: Path, models: list[str]):
    corpus_ids, corpus_texts = load_corpus(corpus_path)
    eval_set = load_eval_set(eval_set_path)
    print(f"Corpus: {len(corpus_ids)} docs; Eval: {len(eval_set)} queries")

    results = {}
    for m in models:
        results[m] = evaluate_model(m, corpus_ids, corpus_texts, eval_set)

    # Pretty-print
    print(f"\\n{'Model':<50} {'R@1':>6} {'R@5':>6} {'R@10':>6} {'MRR':>6} {'nDCG@10':>8}")
    for m, scores in results.items():
        print(f"{m:<50} {scores['recall@1']:>.3f} {scores['recall@5']:>.3f} "
              f"{scores['recall@10']:>.3f} {scores['mrr']:>.3f} {scores['ndcg@10']:>.3f}")


if __name__ == "__main__":
    compare_models(
        corpus_path=Path("./corpus.jsonl"),
        eval_set_path=Path("./eval_set.jsonl"),
        models=[
            "sentence-transformers/all-MiniLM-L6-v2",
            "BAAI/bge-base-en-v1.5",
            "BAAI/bge-large-en-v1.5",
            "intfloat/e5-large-v2",
            "mixedbread-ai/mxbai-embed-large-v1",
        ],
    )
''',
        "dependencies": [
            {"name": "sentence-transformers", "version": ">=3.0", "purpose": "Run local embedding models"},
            {"name": "numpy", "version": ">=1.26", "purpose": "Vector math"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install sentence-transformers numpy",
            "Build eval_set.jsonl: 100-200 (query, relevant_doc_ids) pairs from YOUR domain",
            "Build corpus.jsonl: all docs as (id, text)",
            "python embed_eval.py",
            "Pick winner by R@5 or MRR per your priority",
        ],
        "variations": [
            {"label": "OpenAI / Cohere via API", "description": "Eval API-based models too.", "code_snippet": "# Replace SentenceTransformer with API call (openai.embeddings.create / cohere.embed). Same metric code applies."},
            {"label": "MTEB benchmark", "description": "Use the standard MTEB suite.", "code_snippet": "# pip install mteb; from mteb import MTEB; MTEB(tasks=['MSMARCO', 'NQ']).run(model)"},
            {"label": "Cost-vs-quality plot", "description": "Trade quality and cost.", "code_snippet": "# Compute cost-per-query for each model (API: per-token; local: GPU-cost-per-call). Plot R@5 vs cost."},
        ],
        "common_errors": [
            {"error_text": "Eval set too small (n<50)", "cause": "Metrics noisy.", "fix_snippet": "Build 100-200 pairs minimum. For statistically meaningful diffs (3pp+), need 200+. Use bootstrap CI."},
            {"error_text": "Eval set has same examples as training data", "cause": "Embedding model 'sees' eval as training.", "fix_snippet": "Use queries / docs NOT scraped from public web (private docs). Or use the MTEB held-out tasks."},
            {"error_text": "OOM loading large corpus", "cause": "Encoding all at once.", "fix_snippet": "Stream encoding: batch_size=32 in model.encode. Or chunk corpus into N pieces, encode each."},
            {"error_text": "Embed model from HF requires trust_remote_code", "cause": "Some models have custom code.", "fix_snippet": "Set trust_remote_code=True in SentenceTransformer init. Review the model's HF page for what code runs."},
        ],
        "production_checklist": [
            "Build eval set from YOUR domain, not public datasets.",
            "Include hard negatives in eval (similar-but-wrong docs).",
            "Test multiple metrics: recall@k, MRR, nDCG — they tell different stories.",
            "Compare API vs OSS models (cost vs quality).",
            "Bootstrap CIs — 3pp diff at n=100 is noise; not signal.",
            "Re-run yearly — new models come out constantly.",
        ],
        "tested_with": {
            "model_versions": ["bge-large-en-v1.5", "mxbai-embed-large-v1"],
            "library_versions": ["sentence-transformers==3.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["sentence-transformers", "mteb"],
        "related_glossary_slugs": ["embedding-evaluation", "mrr"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why not just trust MTEB?", "answer": "MTEB benchmarks GENERAL English. Your domain may be biomedical / legal / code. Models that top MTEB sometimes underperform on niche domains. Build your own eval."},
            {"question": "How many queries in eval set?", "answer": "100-200 minimum for stable metrics. 500+ for confident model selection. Each query needs at least 1 relevant doc labeled."},
            {"question": "Hard negatives — how to find?", "answer": "Use a baseline model to retrieve top-k for each query; label false positives as hard negatives. Or use BM25 high-score-low-relevance docs."},
            {"question": "Best embedding model right now?", "answer": "For English: bge-large-en-v1.5, mxbai-embed-large, text-embedding-3-large. For multilingual: BGE-M3, Cohere v3 multilingual. Run YOUR eval; trust YOUR data."},
        ],
        "github_url": "https://github.com/embeddings-benchmark/mteb",
        "meta_title": "Embedding Quality Evaluation Starter",
        "meta_description": "Evaluate embedding models on YOUR data: recall@k / MRR / nDCG metrics. Pick the model that wins on YOUR domain, not arXiv benchmarks.",
    },
    {
        "slug": "voyage-ai-domain-specialized-embed",
        "title": "Voyage AI Domain-Specialized Embeddings",
        "tldr": "Voyage AI: domain-tuned embedding models (voyage-law, voyage-finance, voyage-code, voyage-3). Outperforms general models on these domains. API-based, drop-in.",
        "category": "embeddings",
        "language": "python",
        "framework": "Voyage AI",
        "tags": ["voyage", "domain-specialized", "embeddings", "legal-finance-code"],
        "best_for_tags": ["legal-tech", "fintech", "code-search"],
        "difficulty_tier": "beginner",
        "featured": False,
        "when_to_use": "RAG in a SPECIFIC domain (legal, finance, code, multilingual). Voyage models trained on that domain often beat general-purpose embeddings by 5-15pp recall.",
        "when_not_to_use": "Skip for general-purpose RAG (text-embedding-3 is fine + cheaper). Skip if data-residency matters (Voyage is SaaS).",
        "quick_start": "pip install voyageai && python voyage_demo.py",
        "full_code": '''"""Voyage AI embeddings: domain-specialized + general."""
from __future__ import annotations

import os
import voyageai
import numpy as np


vo = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])


# ----------------- AVAILABLE MODELS -----------------

MODELS = {
    "general": "voyage-3",                  # default; competitive vs OpenAI
    "general-large": "voyage-3-large",       # better quality, higher cost
    "code": "voyage-code-3",                 # code retrieval
    "law": "voyage-law-2",                   # legal documents
    "finance": "voyage-finance-2",           # financial documents
    "multilingual": "voyage-multilingual-2", # 25+ languages
}


# ----------------- EMBED DOCUMENTS -----------------

def embed_docs(texts: list[str], model: str = "voyage-3") -> np.ndarray:
    """input_type='document' for indexable content."""
    response = vo.embed(
        texts=texts,
        model=model,
        input_type="document",
    )
    return np.array(response.embeddings)


def embed_query(text: str, model: str = "voyage-3") -> np.ndarray:
    """input_type='query' for queries."""
    response = vo.embed(
        texts=[text],
        model=model,
        input_type="query",
    )
    return np.array(response.embeddings[0])


# ----------------- RERANK -----------------

def rerank(query: str, candidates: list[str], top_k: int = 5,
           model: str = "rerank-2"):
    """Voyage rerank for final-pass precision."""
    result = vo.rerank(
        query=query,
        documents=candidates,
        model=model,
        top_k=top_k,
    )
    return [(r.document, r.relevance_score) for r in result.results]


# ----------------- DOMAIN-SPECIFIC PIPELINE -----------------

def legal_search(query: str, corpus: list[str], k: int = 5):
    """Use voyage-law-2 + rerank-2 for legal documents."""
    corpus_emb = embed_docs(corpus, model="voyage-law-2")
    q_emb = embed_query(query, model="voyage-law-2")
    sims = (corpus_emb @ q_emb)

    # Initial top-25
    top_25_idx = np.argsort(-sims)[:25]
    candidates = [corpus[i] for i in top_25_idx]

    # Rerank top-5
    return rerank(query, candidates, top_k=k)


def code_search(query: str, corpus: list[str], k: int = 5):
    """Use voyage-code-3 for code retrieval."""
    corpus_emb = embed_docs(corpus, model="voyage-code-3")
    q_emb = embed_query(query, model="voyage-code-3")
    sims = (corpus_emb @ q_emb)
    return sorted(zip(corpus, sims), key=lambda x: -x[1])[:k]


# ----------------- DEMO -----------------

if __name__ == "__main__":
    legal_corpus = [
        "Section 230 immunity protects platforms from user content liability.",
        "GDPR Article 17 requires data deletion within 30 days.",
        "PCI-DSS compliance requires encryption at rest for cardholder data.",
        "FERPA limits disclosure of student education records.",
    ]
    print("Legal search:")
    for doc, score in legal_search("what's the deletion timeline under European privacy law?", legal_corpus, k=2):
        print(f"  {score:.3f}: {doc}")
''',
        "dependencies": [
            {"name": "voyageai", "version": ">=0.3", "purpose": "Voyage AI Python SDK"},
            {"name": "numpy", "version": ">=1.26", "purpose": "Vector math"},
        ],
        "env_vars": [
            {"name": "VOYAGE_API_KEY", "required": True, "description": "From dashboard.voyageai.com", "example": "..."},
        ],
        "setup_steps": [
            "Sign up at voyageai.com",
            "pip install voyageai numpy",
            "export VOYAGE_API_KEY=...",
            "python voyage_demo.py",
        ],
        "variations": [
            {"label": "Hybrid: voyage-3 + bm25", "description": "Pair with BM25 for legal/finance.", "code_snippet": "# Combine voyage embeddings with BM25 via RRF; legal terminology often needs keyword match too"},
            {"label": "Voyage on AWS Bedrock", "description": "Use via Bedrock.", "code_snippet": "# Voyage models available on Bedrock for AWS-native shops; same model IDs"},
            {"label": "Compare with general models", "description": "Quantify the domain lift.", "code_snippet": "# Run YOUR eval set with voyage-3 vs voyage-law-2; legal-specific often 5-15pp better"},
        ],
        "common_errors": [
            {"error_text": "input_type missing", "cause": "Voyage requires it.", "fix_snippet": "ALWAYS pass input_type='document' or 'query'. Voyage's asymmetric encoder requires the hint."},
            {"error_text": "Wrong model for domain", "cause": "Using voyage-3 on legal corpus.", "fix_snippet": "Use the SPECIFIC model: voyage-law-2 for legal, voyage-code-3 for code. The lift over general is what you're paying for."},
            {"error_text": "Cost higher than expected", "cause": "Specialized models cost more.", "fix_snippet": "voyage-law-2 ~$0.12/1M tokens vs $0.10 for general. For 5-15pp lift, usually worth it. Compare on YOUR eval."},
            {"error_text": "Rate limit hit during ingest", "cause": "Free tier has tight limits.", "fix_snippet": "Pay tier removes; or batch + retry. Voyage docs list current rate limits per tier."},
        ],
        "production_checklist": [
            "Pick the SPECIFIC domain model for your data.",
            "Set input_type correctly per call.",
            "Pair with rerank-2 for final-pass precision.",
            "Benchmark vs general model on YOUR data.",
            "Pin SDK version.",
            "Monitor cost per query (specialized > general).",
        ],
        "tested_with": {
            "model_versions": ["voyage-3", "voyage-law-2", "voyage-code-3", "rerank-2"],
            "library_versions": ["voyageai==0.3"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["voyage-ai"],
        "related_glossary_slugs": ["domain-specialized-embedding", "reranking"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Voyage vs OpenAI vs Cohere?", "answer": "Voyage: domain-specialized leader, slightly higher cost. OpenAI: cheap, broad, slightly behind on specialized. Cohere: multilingual leader. Pick by domain + cost."},
            {"question": "When does domain-tuning matter?", "answer": "Strongest lift on legal, finance, biomedical, code. General domains (news, blogs): general models are fine. Run YOUR eval — sometimes the lift is bigger or smaller than expected."},
            {"question": "Voyage-3 free tier?", "answer": "50M free tokens for new accounts. Generous for prototypes. Production: paid tier, but cost is comparable to OpenAI."},
            {"question": "Compatible with rerank-1?", "answer": "Yes — rerank-1 and rerank-2 both work with Voyage embeddings. rerank-2 is newer + multilingual. Use it for new projects."},
        ],
        "github_url": "https://github.com/voyage-ai/voyageai-python",
        "meta_title": "Voyage AI Domain-Specialized Embeddings Starter",
        "meta_description": "Voyage AI: domain-tuned embeddings for legal / finance / code. 5-15pp recall lift vs general models on these domains.",
    },
]
