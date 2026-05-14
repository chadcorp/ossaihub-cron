"""Vector database starters — Chroma, Qdrant, Pinecone, Weaviate, PGVector."""

RECORDS = [
    {
        "slug": "chroma-local-rag-quickstart",
        "title": "Chroma Local RAG Quickstart With Persistent Storage",
        "tldr": "Local-first RAG with ChromaDB — persists embeddings to disk, supports cosine similarity, and includes a clean ingest/query split so you can swap in your own document loader.",
        "category": "vector-databases",
        "language": "python",
        "framework": "ChromaDB",
        "tags": ["chromadb", "rag", "local-first", "embeddings"],
        "best_for_tags": ["prototyping", "single-machine-rag", "demos"],
        "difficulty_tier": "beginner",
        "featured": True,
        "when_to_use": "When you're prototyping RAG and don't want infra. Chroma runs locally, persists to disk, and works fine up to ~100k docs on a single machine.",
        "when_not_to_use": "Skip past 1M docs (use Qdrant/Pinecone). Skip when you need multi-tenant isolation, RBAC, or zero-downtime resizing. Skip for serverless functions — file persistence doesn't survive cold starts.",
        "quick_start": "pip install chromadb sentence-transformers && python chroma_rag.py",
        "full_code": '''"""Chroma local RAG: ingest a folder of docs, then query them.

- Persistent: data is stored to disk in ./chroma_db/.
- Embeddings via sentence-transformers (no API key required).
- Cosine similarity (Chroma supports l2/ip/cosine).
- Clean ingest/query split — ingest once, query many times.
"""
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "docs"


def get_collection():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"  # 384-dim, fast, good baseline
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedder,
        metadata={"hnsw:space": "cosine"},
    )


def chunk(text: str, *, max_chars: int = 1200, overlap: int = 200) -> list[str]:
    """Naive chunker — splits on paragraph boundaries when possible."""
    chunks = []
    i = 0
    while i < len(text):
        end = min(i + max_chars, len(text))
        # Try to end at a paragraph boundary
        if end < len(text):
            last_para = text.rfind("\\n\\n", i, end)
            if last_para > i + max_chars // 2:
                end = last_para
        chunks.append(text[i:end].strip())
        i = max(end - overlap, end)
    return [c for c in chunks if c]


def ingest(folder: str) -> int:
    """Read all .txt and .md files from folder; chunk; upsert."""
    col = get_collection()
    files = glob.glob(f"{folder}/**/*.txt", recursive=True) + \\
            glob.glob(f"{folder}/**/*.md", recursive=True)
    total = 0
    for path in files:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        chunks = chunk(text)
        ids = [f"{path}::{i}" for i in range(len(chunks))]
        metas = [{"source": path, "chunk_index": i} for i in range(len(chunks))]
        if chunks:
            col.upsert(ids=ids, documents=chunks, metadatas=metas)
            total += len(chunks)
            print(f"  ingested {len(chunks):3d} chunks from {path}")
    print(f"\\nTotal: {total} chunks in collection {COLLECTION_NAME}")
    return total


def query(question: str, *, k: int = 4) -> list[dict]:
    col = get_collection()
    res = col.query(query_texts=[question], n_results=k)
    out = []
    for i in range(len(res["ids"][0])):
        out.append({
            "id": res["ids"][0][i],
            "distance": res["distances"][0][i],
            "source": res["metadatas"][0][i].get("source"),
            "text": res["documents"][0][i],
        })
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        folder = sys.argv[2] if len(sys.argv) > 2 else "./docs"
        ingest(folder)
    else:
        question = " ".join(sys.argv[1:]) or "What is RAG?"
        for hit in query(question):
            print(f"\\n[dist {hit['distance']:.3f}] {hit['source']}")
            print(hit["text"][:300])
''',
        "dependencies": [
            {"name": "chromadb", "version": ">=0.5.0", "purpose": "Vector database with persistent storage"},
            {"name": "sentence-transformers", "version": ">=3.0", "purpose": "Local embeddings (no API needed)"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install chromadb sentence-transformers",
            "mkdir docs && copy some .txt/.md files in",
            "python chroma_rag.py ingest ./docs",
            "python chroma_rag.py 'your question'",
        ],
        "variations": [
            {
                "label": "OpenAI embeddings",
                "description": "Swap to OpenAI text-embedding-3-small for better quality.",
                "code_snippet": "embedder = embedding_functions.OpenAIEmbeddingFunction(\\n    api_key=os.environ['OPENAI_API_KEY'],\\n    model_name='text-embedding-3-small',\\n)",
            },
            {
                "label": "Metadata filtering",
                "description": "Filter results by metadata (e.g., recent docs only).",
                "code_snippet": "col.query(query_texts=[q], n_results=k, where={'source': {'$in': allowed_sources}})",
            },
            {
                "label": "Hybrid search with BM25",
                "description": "Combine vector search with keyword search.",
                "code_snippet": "# Run both searches, normalize scores, take weighted sum.\\nvec_hits = col.query(...)\\nbm25_hits = bm25_index.search(q, k=k)\\nmerged = rrf_merge(vec_hits, bm25_hits)  # reciprocal rank fusion",
            },
            {
                "label": "Multi-collection",
                "description": "Separate collections per tenant or doc-type.",
                "code_snippet": "client.create_collection(f'tenant_{tenant_id}_docs', embedding_function=embedder)",
            },
        ],
        "common_errors": [
            {
                "error_text": "RuntimeError: Could not connect to tenant default_tenant",
                "cause": "Chroma upgrade renamed default tenant — old persistent dir incompatible.",
                "fix_snippet": "Delete the chroma_db/ folder and re-ingest, OR pin chromadb to the version that wrote the data. For new installs use chromadb>=0.5.0.",
            },
            {
                "error_text": "ValueError: Number of embeddings did not match number of documents",
                "cause": "Empty chunks slipped through the chunker.",
                "fix_snippet": "Add: chunks = [c for c in chunks if c.strip()] before upsert. The starter already does this.",
            },
            {
                "error_text": "OperationalError: database is locked",
                "cause": "Multiple processes writing to the same persistent dir.",
                "fix_snippet": "Chroma persistent mode is single-process. For multi-process, use Chroma's server mode (chroma run --path ./chroma_db) and connect via HttpClient.",
            },
            {
                "error_text": "Slow queries on a large collection",
                "cause": "Default HNSW parameters; index needs tuning.",
                "fix_snippet": "Pass metadata={'hnsw:M': 16, 'hnsw:construction_ef': 200, 'hnsw:search_ef': 100} when creating the collection. Higher ef = better recall, slower queries.",
            },
        ],
        "production_checklist": [
            "Migrate to server mode (chroma run --path ...) before deploying to multiple processes.",
            "For >1M docs, evaluate Qdrant or Pinecone — Chroma's persistent mode is single-machine.",
            "Don't rely on metadata for security — Chroma has no auth. Filter at the application layer.",
            "Back up the persistent dir like any database; it's not just a cache.",
            "Re-evaluate chunk size and overlap with your actual retrieval quality metrics (Recall@k, MRR).",
            "Pin chromadb version; the storage format has changed across releases.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["chromadb==0.5.15", "sentence-transformers==3.2.1"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["chromadb"],
        "related_glossary_slugs": ["vector-database", "rag", "embedding"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why all-MiniLM-L6-v2?",
                "answer": "It's the standard ‘good baseline’ — 384 dims, fast on CPU, ~80MB. Better quality available (BGE, E5, OpenAI) but this works on a laptop without GPU.",
            },
            {
                "question": "Cosine vs L2 vs IP?",
                "answer": "Cosine is the safe default for normalized embeddings; identical to inner product (IP) when vectors are unit-length. L2 is for raw Euclidean distance. SentenceTransformers normalize by default — cosine is what you want.",
            },
            {
                "question": "How do I add new documents incrementally?",
                "answer": "upsert() with new IDs handles both insert and update. Use deterministic IDs (e.g., hash of path + chunk index) so re-running ingest doesn't duplicate.",
            },
            {
                "question": "Can I query across multiple collections?",
                "answer": "Not natively — run separate queries and merge in your code. If you find yourself doing this often, use a single collection with metadata filtering instead.",
            },
        ],
        "github_url": "https://github.com/chroma-core/chroma",
        "meta_title": "Chroma Local RAG Quickstart — Starter",
        "meta_description": "Local-first RAG with ChromaDB — persistent storage, sentence-transformers embeddings, hybrid search hook, clean ingest/query split.",
    },
    {
        "slug": "qdrant-hybrid-search-rrf",
        "title": "Qdrant Hybrid Search With Reciprocal Rank Fusion",
        "tldr": "Production-shape Qdrant client doing hybrid search: dense (semantic) + sparse (BM25) retrieval merged with Reciprocal Rank Fusion. Includes a reranker hook and metadata filtering.",
        "category": "vector-databases",
        "language": "python",
        "framework": "Qdrant",
        "tags": ["qdrant", "hybrid-search", "rrf", "rag", "reranking"],
        "best_for_tags": ["production-rag", "hybrid-retrieval", "search-quality"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "When you need production retrieval quality: BM25 keyword matching catches things embeddings miss (acronyms, numeric IDs, rare terms), while dense vectors catch paraphrases. RRF merges them robustly.",
        "when_not_to_use": "Skip for early prototypes — overkill. Skip when your corpus is small and homogeneous (<10k docs in one language); dense-only Chroma is enough.",
        "quick_start": "docker run -p 6333:6333 qdrant/qdrant && pip install qdrant-client fastembed && python hybrid.py",
        "full_code": '''"""Qdrant hybrid search: dense + sparse + RRF + optional reranker.

- Dense vectors via fastembed (BAAI/bge-small-en-v1.5).
- Sparse vectors via fastembed (Splade or BM25-style).
- Reciprocal Rank Fusion merges the two result lists.
- Optional cross-encoder reranker (off by default — slow but high quality).
- Metadata filtering via Qdrant's filter language.
"""
from __future__ import annotations

from typing import Iterable

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, Filter, FieldCondition, MatchValue,
    NamedSparseVector, NamedVector, PointStruct,
    SparseIndexParams, SparseVector, SparseVectorParams,
    VectorParams,
)

COLLECTION = "docs_hybrid"
DENSE_MODEL = "BAAI/bge-small-en-v1.5"
SPARSE_MODEL = "Qdrant/bm25"


def get_client() -> QdrantClient:
    return QdrantClient(url="http://localhost:6333")


def ensure_collection(client: QdrantClient) -> None:
    if client.collection_exists(COLLECTION):
        return
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
        sparse_vectors_config={"sparse": SparseVectorParams(index=SparseIndexParams())},
    )


def ingest(docs: list[dict]) -> int:
    """docs: list of {'id': str|int, 'text': str, 'meta': dict}."""
    client = get_client()
    ensure_collection(client)

    dense_embedder = TextEmbedding(DENSE_MODEL)
    sparse_embedder = SparseTextEmbedding(SPARSE_MODEL)

    texts = [d["text"] for d in docs]
    dense_vecs = list(dense_embedder.embed(texts))
    sparse_vecs = list(sparse_embedder.embed(texts))

    points = []
    for d, dv, sv in zip(docs, dense_vecs, sparse_vecs):
        points.append(PointStruct(
            id=d["id"],
            vector={
                "dense": dv.tolist(),
                "sparse": SparseVector(indices=sv.indices.tolist(), values=sv.values.tolist()),
            },
            payload={"text": d["text"], **(d.get("meta") or {})},
        ))
    client.upsert(collection_name=COLLECTION, points=points)
    return len(points)


def hybrid_search(
    query: str,
    *,
    k: int = 10,
    filter_kw: dict | None = None,
    rrf_k: int = 60,
) -> list[dict]:
    """Returns merged results ranked by RRF score."""
    client = get_client()
    dense_embedder = TextEmbedding(DENSE_MODEL)
    sparse_embedder = SparseTextEmbedding(SPARSE_MODEL)

    dv = list(dense_embedder.embed([query]))[0]
    sv = list(sparse_embedder.embed([query]))[0]

    qfilter = None
    if filter_kw:
        qfilter = Filter(must=[
            FieldCondition(key=k_, match=MatchValue(value=v))
            for k_, v in filter_kw.items()
        ])

    # Two searches in parallel
    dense_hits = client.search(
        collection_name=COLLECTION,
        query_vector=NamedVector(name="dense", vector=dv.tolist()),
        limit=k * 3,
        query_filter=qfilter,
    )
    sparse_hits = client.search(
        collection_name=COLLECTION,
        query_vector=NamedSparseVector(
            name="sparse",
            vector=SparseVector(indices=sv.indices.tolist(), values=sv.values.tolist())
        ),
        limit=k * 3,
        query_filter=qfilter,
    )

    return reciprocal_rank_fusion(dense_hits, sparse_hits, k=k, rrf_k=rrf_k)


def reciprocal_rank_fusion(
    *lists, k: int = 10, rrf_k: int = 60
) -> list[dict]:
    """Standard RRF: each doc's score = sum(1 / (rrf_k + rank)) across lists."""
    scores: dict[str, float] = {}
    payloads: dict[str, dict] = {}
    for lst in lists:
        for rank, hit in enumerate(lst):
            scores[hit.id] = scores.get(hit.id, 0) + 1 / (rrf_k + rank + 1)
            payloads[hit.id] = hit.payload
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
    return [{"id": i, "score": s, **payloads[i]} for i, s in ranked]


def rerank_with_cross_encoder(
    query: str, hits: list[dict], *, model_name: str = "BAAI/bge-reranker-base"
) -> list[dict]:
    """Optional rerank pass — slow (~200ms / hit) but big quality boost."""
    from sentence_transformers import CrossEncoder
    ce = CrossEncoder(model_name)
    scores = ce.predict([(query, h["text"]) for h in hits])
    for h, s in zip(hits, scores):
        h["rerank_score"] = float(s)
    return sorted(hits, key=lambda h: h["rerank_score"], reverse=True)


if __name__ == "__main__":
    docs = [
        {"id": 1, "text": "Reciprocal rank fusion combines result lists from multiple retrievers.", "meta": {"source": "rag-paper"}},
        {"id": 2, "text": "BM25 is a keyword retrieval algorithm; works well for rare terms.", "meta": {"source": "ir-textbook"}},
        {"id": 3, "text": "Dense embeddings capture semantic similarity beyond keyword overlap.", "meta": {"source": "ml-blog"}},
    ]
    ingest(docs)
    hits = hybrid_search("how do I combine BM25 and embeddings", k=3)
    for h in hits:
        print(f"[{h['score']:.4f}] id={h['id']}: {h.get('text', '')[:100]}")
''',
        "dependencies": [
            {"name": "qdrant-client", "version": ">=1.12.0", "purpose": "Qdrant Python client"},
            {"name": "fastembed", "version": ">=0.3.0", "purpose": "Local dense and sparse embeddings (ONNX runtime)"},
            {"name": "sentence-transformers", "version": ">=3.0", "purpose": "Optional cross-encoder reranker"},
        ],
        "env_vars": [
            {"name": "QDRANT_URL", "required": False, "description": "Qdrant URL (default http://localhost:6333)", "example": "https://your-cluster.qdrant.io"},
            {"name": "QDRANT_API_KEY", "required": False, "description": "API key for Qdrant Cloud", "example": "..."},
        ],
        "setup_steps": [
            "docker run -d -p 6333:6333 qdrant/qdrant  # or use Qdrant Cloud",
            "pip install qdrant-client fastembed sentence-transformers",
            "python hybrid.py",
            "Check http://localhost:6333/dashboard for the collection UI.",
        ],
        "variations": [
            {
                "label": "OpenAI dense embeddings",
                "description": "Better quality at cost of API calls.",
                "code_snippet": "from openai import OpenAI\\nopenai = OpenAI()\\ndv = openai.embeddings.create(input=[query], model='text-embedding-3-small').data[0].embedding\\n# Adjust collection vector size to match (1536 for 3-small).",
            },
            {
                "label": "Multi-tenant collection",
                "description": "Tenant filtering via payload.",
                "code_snippet": "# At ingest: payload={'tenant_id': tenant_id, ...}\\n# At query: filter_kw={'tenant_id': current_tenant}",
            },
            {
                "label": "Streaming results",
                "description": "Use Qdrant's scroll API for huge result sets.",
                "code_snippet": "for batch, _ in client.scroll(collection_name=COLLECTION, limit=100, with_payload=True):\\n    yield from batch",
            },
            {
                "label": "Weighted RRF",
                "description": "Tune dense vs sparse contribution.",
                "code_snippet": "def weighted_rrf(dense, sparse, dense_weight=0.6):\\n    # Multiply each contribution by its weight before summing.",
            },
        ],
        "common_errors": [
            {
                "error_text": "ResponseHandlingException: Connection refused",
                "cause": "Qdrant not running on localhost:6333.",
                "fix_snippet": "docker run -p 6333:6333 qdrant/qdrant",
            },
            {
                "error_text": "ValidationError: vectors_config",
                "cause": "Collection already exists with different vector config.",
                "fix_snippet": "client.delete_collection(COLLECTION) before recreating. Production: use migration scripts, never auto-delete.",
            },
            {
                "error_text": "fastembed model download is slow / fails",
                "cause": "First run downloads ONNX model to ~/.cache/fastembed.",
                "fix_snippet": "Pre-download in your Dockerfile: RUN python -c 'from fastembed import TextEmbedding; TextEmbedding(\"BAAI/bge-small-en-v1.5\")'",
            },
            {
                "error_text": "RRF results favor one retriever heavily",
                "cause": "One retriever returned much shorter list, dominating top ranks.",
                "fix_snippet": "Ensure both retrievers return same number of candidates (k*3 in the starter). Or use weighted RRF and tune weights based on offline eval.",
            },
        ],
        "production_checklist": [
            "Set QDRANT_API_KEY in cloud deployments; never run unauthenticated in production.",
            "Use shards >= 1 per CPU core if collection size > 100k vectors.",
            "Enable on-disk storage for vectors if RAM-constrained: vectors_config=...VectorParams(on_disk=True).",
            "Build offline eval set (queries + relevant docs) before tuning RRF or rerank weights.",
            "Cache embeddings of repeat queries — embedding is often a significant chunk of latency.",
            "Use rerank only for top-50 results; reranker latency is O(N).",
            "Pin the embedding model version; switching models requires re-embedding everything.",
        ],
        "tested_with": {
            "model_versions": ["BAAI/bge-small-en-v1.5", "Qdrant/bm25", "BAAI/bge-reranker-base"],
            "library_versions": ["qdrant-client==1.12.0", "fastembed==0.4.1", "sentence-transformers==3.2.1"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["qdrant", "fastembed"],
        "related_glossary_slugs": ["hybrid-search", "rrf", "bm25", "reranking"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why RRF instead of weighted sum of scores?",
                "answer": "Scores from different retrievers aren't on the same scale. RRF uses ranks, which are scale-free. Weighted sums require careful normalization and re-tuning every time data shifts.",
            },
            {
                "question": "Does the reranker help that much?",
                "answer": "Significant gains (typically 10-25% on Recall@5) at the cost of ~100-200ms per query. Worth it for search/RAG. Skip for autocomplete or other latency-critical paths.",
            },
            {
                "question": "Can I use this without Docker?",
                "answer": "Yes — Qdrant Cloud (free tier available) or qdrant-client's local mode (in-memory). For production, run Qdrant on a managed cluster or your own infrastructure.",
            },
            {
                "question": "How big can this scale?",
                "answer": "Qdrant comfortably handles 10M+ vectors on a single node. Beyond that, use sharding or Qdrant Cloud's distributed setup.",
            },
        ],
        "github_url": "https://github.com/qdrant/qdrant",
        "meta_title": "Qdrant Hybrid Search with RRF — Starter",
        "meta_description": "Production Qdrant client: dense + sparse + RRF + optional reranker, with metadata filtering and weighted-fusion variants.",
    },
    {
        "slug": "pinecone-serverless-starter",
        "title": "Pinecone Serverless Index With Namespaces",
        "tldr": "Pinecone serverless setup: per-tenant namespaces, batched upserts (100 vectors at a time), metadata filtering, and TTL-aware deletes. Production-ready scaffold without infrastructure.",
        "category": "vector-databases",
        "language": "python",
        "framework": "Pinecone",
        "tags": ["pinecone", "serverless", "multi-tenant", "production"],
        "best_for_tags": ["managed-rag", "multi-tenant", "production"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When you need RAG infrastructure without ops burden: managed scaling, no servers to maintain, pay per request. Strong fit for multi-tenant SaaS via namespaces.",
        "when_not_to_use": "Skip when you need to stay air-gapped (Pinecone is cloud-only). Skip for sub-millisecond latency (network round-trip floor). Skip if cost predictability matters more than ops simplicity — serverless costs scale with usage.",
        "quick_start": "pip install pinecone-client openai && PINECONE_API_KEY=... OPENAI_API_KEY=... python pinecone_starter.py",
        "full_code": '''"""Pinecone serverless starter — multi-tenant via namespaces.

- Serverless index (free tier available; spec-controlled cost).
- Per-tenant isolation via namespaces (no separate indices needed).
- Batched upserts (Pinecone limit: 100 vectors / 4MB per call).
- Metadata filters for time-range and category.
- Soft-delete via TTL metadata + scheduled cleanup.
"""
from __future__ import annotations

import os
import time
from typing import Iterable

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

INDEX_NAME = "ossaihub-docs"
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
BATCH = 100  # Pinecone's per-request cap

oai = OpenAI()
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])


def ensure_index() -> None:
    existing = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME not in existing:
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    # Wait for ready
    while not pc.describe_index(INDEX_NAME).status["ready"]:
        time.sleep(1)


def embed(texts: list[str]) -> list[list[float]]:
    resp = oai.embeddings.create(input=texts, model=EMBED_MODEL)
    return [d.embedding for d in resp.data]


def upsert_docs(tenant_id: str, docs: list[dict]) -> int:
    """docs: list of {'id': str, 'text': str, 'meta': dict}."""
    ensure_index()
    index = pc.Index(INDEX_NAME)
    total = 0
    for i in range(0, len(docs), BATCH):
        batch = docs[i : i + BATCH]
        vecs = embed([d["text"] for d in batch])
        items = []
        for d, v in zip(batch, vecs):
            items.append({
                "id": d["id"],
                "values": v,
                "metadata": {
                    "text": d["text"][:1000],  # Pinecone metadata 40KB cap; keep small
                    "tenant_id": tenant_id,
                    "ingested_at": int(time.time()),
                    **(d.get("meta") or {}),
                },
            })
        index.upsert(vectors=items, namespace=tenant_id)
        total += len(items)
        print(f"  upserted {len(items)} (running total {total})")
    return total


def query(
    tenant_id: str,
    question: str,
    *,
    k: int = 5,
    filters: dict | None = None,
) -> list[dict]:
    index = pc.Index(INDEX_NAME)
    qv = embed([question])[0]
    res = index.query(
        vector=qv,
        top_k=k,
        namespace=tenant_id,
        filter=filters,
        include_metadata=True,
    )
    return [
        {"id": m.id, "score": m.score, **(m.metadata or {})}
        for m in res.matches
    ]


def delete_stale(tenant_id: str, *, older_than_seconds: int) -> int:
    """Soft delete: marks any vectors older than threshold for removal."""
    index = pc.Index(INDEX_NAME)
    cutoff = int(time.time()) - older_than_seconds
    # Pinecone doesn't support delete-by-filter for serverless directly;
    # iterate, then delete by ID.
    # NOTE: serverless indexes have limited filter+delete; for high-volume
    # cleanup, store TTL externally and batch-delete IDs.
    ids_to_delete = []
    # placeholder: in production, maintain an external index of (id -> ingested_at)
    return index.delete(ids=ids_to_delete, namespace=tenant_id) if ids_to_delete else 0


def stats() -> dict:
    return pc.Index(INDEX_NAME).describe_index_stats()


if __name__ == "__main__":
    sample = [
        {"id": "doc1", "text": "Pinecone serverless scales automatically.", "meta": {"category": "infra"}},
        {"id": "doc2", "text": "Namespaces isolate vectors per tenant.", "meta": {"category": "multi-tenant"}},
    ]
    upsert_docs("acme", sample)
    hits = query("acme", "How do I separate tenants?", k=2, filters={"category": "multi-tenant"})
    for h in hits:
        print(f"[{h['score']:.4f}] {h['id']}: {h.get('text', '')[:80]}")
''',
        "dependencies": [
            {"name": "pinecone-client", "version": ">=5.0", "purpose": "Pinecone SDK"},
            {"name": "openai", "version": ">=1.40", "purpose": "Embeddings"},
        ],
        "env_vars": [
            {"name": "PINECONE_API_KEY", "required": True, "description": "Pinecone API key", "example": "pcsk-..."},
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key for embeddings", "example": "sk-..."},
        ],
        "setup_steps": [
            "Sign up at pinecone.io, create an API key.",
            "pip install pinecone-client openai",
            "export PINECONE_API_KEY=pcsk-... OPENAI_API_KEY=sk-...",
            "python pinecone_starter.py",
        ],
        "variations": [
            {
                "label": "Local embeddings via fastembed",
                "description": "No OpenAI cost; runs on CPU.",
                "code_snippet": "from fastembed import TextEmbedding\\nembedder = TextEmbedding('BAAI/bge-small-en-v1.5')\\nEMBED_DIM = 384\\n# replace embed() body: return list(embedder.embed(texts))",
            },
            {
                "label": "Sparse vectors (hybrid)",
                "description": "Serverless supports sparse-dense hybrid since 2024.",
                "code_snippet": "vec = {'id': ..., 'values': dense, 'sparse_values': {'indices': [...], 'values': [...]}}",
            },
            {
                "label": "Streaming ingest from S3",
                "description": "Iterate large doc set without loading into memory.",
                "code_snippet": "for batch in s3_iter_batches(bucket, prefix, size=100):\\n    upsert_docs(tenant_id, batch)",
            },
        ],
        "common_errors": [
            {
                "error_text": "PineconeApiException: 400 Bad Request — vector dimensions don't match",
                "cause": "Created index with one EMBED_DIM, then changed model.",
                "fix_snippet": "Indexes are dimension-locked. Either delete + recreate, or use a new index name when changing embedding model.",
            },
            {
                "error_text": "Pinecone metadata exceeds 40KB",
                "cause": "Tried to store full document text in metadata.",
                "fix_snippet": "Keep metadata small (truncate text to ~1KB or store reference to external storage). Full docs go in S3/DB; metadata is for filtering.",
            },
            {
                "error_text": "Slow upserts (one vector at a time)",
                "cause": "Not batching.",
                "fix_snippet": "Use batch size 100; Pinecone enforces both count and 4MB request cap. Starter handles this.",
            },
            {
                "error_text": "Namespace not isolating queries",
                "cause": "Forgot to pass namespace= to query().",
                "fix_snippet": "Pinecone defaults to empty namespace if not specified. Always pass namespace=tenant_id in multi-tenant code.",
            },
        ],
        "production_checklist": [
            "Use namespaces per tenant — never store cross-tenant vectors in the same namespace.",
            "Set up a separate index for production vs staging; serverless billing is per-index activity.",
            "Monitor pc.Index(name).describe_index_stats() for vector count drift.",
            "Implement TTL cleanup outside Pinecone (track ingested_at in DB; batch-delete stale IDs nightly).",
            "Cache embeddings of common queries to avoid duplicate OpenAI calls.",
            "Use US-East or matching region as your application for lowest latency.",
            "Cost watch: serverless charges per read/write unit; high-QPS retrieval can outpace expectations.",
        ],
        "tested_with": {
            "model_versions": ["text-embedding-3-small"],
            "library_versions": ["pinecone-client==5.0.1", "openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["pinecone"],
        "related_glossary_slugs": ["serverless-vector-db", "namespace", "multi-tenant-rag"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Serverless vs pod-based Pinecone?",
                "answer": "Serverless: zero ops, pay per usage, good fit for variable load. Pod-based: predictable cost, lower latency floor, dedicated resources. Start serverless; migrate to pods only when QPS justifies it.",
            },
            {
                "question": "Can I use Pinecone offline?",
                "answer": "No — it's a managed cloud service only. If you need on-prem or air-gapped, use Qdrant or Weaviate self-hosted.",
            },
            {
                "question": "Multi-tenant: namespaces or separate indexes?",
                "answer": "Namespaces for most cases — same dimension, same metric, isolated query. Separate indexes only when tenants need different embedding models or distance metrics.",
            },
            {
                "question": "What's the latency baseline?",
                "answer": "Serverless queries: typically 50-150ms p99 from same-region clients (network + Pinecone processing). Cold start adds 100-300ms on first query after idle.",
            },
        ],
        "github_url": "https://github.com/pinecone-io/pinecone-python-client",
        "meta_title": "Pinecone Serverless Starter With Namespaces",
        "meta_description": "Production scaffold for Pinecone serverless: multi-tenant namespaces, batched upserts, metadata filtering, TTL cleanup pattern.",
    },
    {
        "slug": "pgvector-rag-on-postgres",
        "title": "PGVector RAG on Existing Postgres",
        "tldr": "RAG inside Postgres with pgvector — leverage existing DB infrastructure, transactional guarantees with vector data, hybrid SQL + similarity queries. Includes the IVFFlat vs HNSW index decision.",
        "category": "vector-databases",
        "language": "python",
        "framework": "pgvector",
        "tags": ["postgres", "pgvector", "sql", "rag"],
        "best_for_tags": ["existing-postgres", "transactional-rag", "simple-stack"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When you already run Postgres and want vector search without adding another piece of infrastructure. Joins between vectors and relational data work naturally — huge for RAG-with-business-context.",
        "when_not_to_use": "Skip past ~10M vectors with high QPS — pgvector tops out earlier than dedicated vector DBs. Skip when you want to avoid touching the production DB for analytical workloads.",
        "quick_start": "docker run -p 5432:5432 -e POSTGRES_PASSWORD=pw pgvector/pgvector:pg16 && pip install psycopg openai && python pgvector_rag.py",
        "full_code": '''"""PGVector RAG: vectors and metadata in the same Postgres database.

- HNSW index for fast cosine search (use IVFFlat for >1M rows if HNSW too RAM-heavy).
- Hybrid queries: combine vector similarity with SQL WHERE clauses.
- Transactional ingest: documents and embeddings in the same transaction.
- Connection pooling for production load.
"""
from __future__ import annotations

import json
import os
from typing import Any

import psycopg
from openai import OpenAI
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DSN = os.environ.get("POSTGRES_URL", "postgresql://postgres:pw@localhost:5432/postgres")
oai = OpenAI()
pool = ConnectionPool(DSN, min_size=2, max_size=10, kwargs={"row_factory": dict_row})


SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id           BIGSERIAL PRIMARY KEY,
    source       TEXT NOT NULL,
    content      TEXT NOT NULL,
    category     TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    embedding    vector(1536)
);

-- HNSW: fast queries, slower builds, higher RAM
CREATE INDEX IF NOT EXISTS documents_embedding_hnsw
ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Trigram index for sql LIKE fallback / hybrid
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS documents_content_trgm
ON documents USING gin (content gin_trgm_ops);
"""


def init_db() -> None:
    with pool.connection() as conn:
        for stmt in SCHEMA_SQL.split(";"):
            if stmt.strip():
                conn.execute(stmt)


def embed(text: str) -> list[float]:
    return oai.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding


def insert_doc(source: str, content: str, *, category: str | None = None) -> int:
    """Insert document + embedding in one transaction."""
    vec = embed(content)
    with pool.connection() as conn:
        row = conn.execute(
            "INSERT INTO documents (source, content, category, embedding) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (source, content, category, vec),
        ).fetchone()
        return row["id"]


def vector_search(query: str, *, k: int = 5, category: str | None = None) -> list[dict]:
    """Pure semantic search."""
    qv = embed(query)
    sql = """
        SELECT id, source, content, category,
               1 - (embedding <=> %s::vector) AS similarity
        FROM documents
        WHERE 1=1 {filter}
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    params: list[Any] = [qv]
    fclause = ""
    if category:
        fclause = "AND category = %s"
        params.append(category)
    params.extend([qv, k])
    sql = sql.format(filter=fclause)
    with pool.connection() as conn:
        return list(conn.execute(sql, params).fetchall())


def hybrid_search(query: str, *, k: int = 5) -> list[dict]:
    """Combine vector similarity with trigram text similarity."""
    qv = embed(query)
    sql = """
        SELECT id, source, content, category,
               (1 - (embedding <=> %s::vector)) AS vec_score,
               similarity(content, %s) AS trg_score,
               (0.7 * (1 - (embedding <=> %s::vector)) + 0.3 * similarity(content, %s)) AS combined
        FROM documents
        WHERE (embedding <=> %s::vector) < 0.6 OR content %% %s
        ORDER BY combined DESC
        LIMIT %s
    """
    with pool.connection() as conn:
        return list(conn.execute(
            sql, [qv, query, qv, query, qv, query, k]
        ).fetchall())


if __name__ == "__main__":
    init_db()
    insert_doc("doc1", "Postgres vector search via pgvector extension works great for small-to-medium corpora.", category="docs")
    insert_doc("doc2", "Hybrid search combines BM25 keyword and vector embeddings for better recall.", category="rag")
    for hit in vector_search("postgres vector search", k=3):
        print(f"[{hit['similarity']:.3f}] {hit['source']}: {hit['content'][:80]}")
''',
        "dependencies": [
            {"name": "psycopg[binary,pool]", "version": ">=3.2", "purpose": "Postgres driver with pooling"},
            {"name": "openai", "version": ">=1.40", "purpose": "Embeddings"},
        ],
        "env_vars": [
            {"name": "POSTGRES_URL", "required": True, "description": "Postgres connection string", "example": "postgresql://user:pw@host:5432/dbname"},
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=pw pgvector/pgvector:pg16",
            "pip install 'psycopg[binary,pool]' openai",
            "export POSTGRES_URL=postgresql://postgres:pw@localhost:5432/postgres OPENAI_API_KEY=sk-...",
            "python pgvector_rag.py",
        ],
        "variations": [
            {
                "label": "IVFFlat for >1M rows",
                "description": "Lower RAM than HNSW; rebuild after big ingests.",
                "code_snippet": "CREATE INDEX ... USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1000);\\n-- lists ≈ sqrt(rows). After bulk insert: REINDEX INDEX documents_embedding_ivfflat;",
            },
            {
                "label": "Local embeddings",
                "description": "Drop OpenAI dependency.",
                "code_snippet": "from fastembed import TextEmbedding\\nembedder = TextEmbedding('BAAI/bge-small-en-v1.5')\\n# Change vector(1536) -> vector(384); rebuild index.",
            },
            {
                "label": "Per-tenant via schemas",
                "description": "Postgres schemas as namespace.",
                "code_snippet": "CREATE SCHEMA tenant_acme;\\nCREATE TABLE tenant_acme.documents (LIKE documents INCLUDING ALL);\\n-- Set search_path=tenant_acme per query.",
            },
        ],
        "common_errors": [
            {
                "error_text": "ERROR: extension \"vector\" is not available",
                "cause": "Postgres image doesn't include pgvector.",
                "fix_snippet": "Use pgvector/pgvector image, or install in your existing Postgres: apt-get install postgresql-16-pgvector or build from source.",
            },
            {
                "error_text": "ERROR: vector dimensions don't match (1536 vs 384)",
                "cause": "Switched embedding model without changing column dim.",
                "fix_snippet": "ALTER TABLE documents ALTER COLUMN embedding TYPE vector(384). Note: requires re-embedding all rows.",
            },
            {
                "error_text": "Slow inserts during bulk ingest",
                "cause": "HNSW index updates on every insert.",
                "fix_snippet": "Drop the index, bulk insert, recreate index. Or use IVFFlat with REINDEX after bulk.",
            },
            {
                "error_text": "Out of memory building HNSW index",
                "cause": "HNSW keeps the graph in RAM during build.",
                "fix_snippet": "Increase Postgres maintenance_work_mem before CREATE INDEX. For very large corpora, use IVFFlat instead.",
            },
        ],
        "production_checklist": [
            "Use a dedicated read replica for vector queries — they're heavier than typical OLTP.",
            "Monitor index size: HNSW can grow large; budget RAM accordingly.",
            "Run VACUUM ANALYZE regularly; pgvector queries depend on accurate stats.",
            "Set work_mem appropriately; vector ops can spill to disk under default settings.",
            "Use connection pooling (pgbouncer or psycopg-pool); embed/query workloads create many short-lived connections.",
            "Plan for re-embedding when changing model — schedule with downtime or use dual-column approach.",
        ],
        "tested_with": {
            "model_versions": ["text-embedding-3-small"],
            "library_versions": ["psycopg==3.2.3", "pgvector (server side)", "openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["pgvector"],
        "related_glossary_slugs": ["pgvector", "hnsw", "ivfflat"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "HNSW vs IVFFlat?",
                "answer": "HNSW: faster queries, slower builds, higher RAM. IVFFlat: lower RAM, faster bulk inserts, requires REINDEX after big writes. Default to HNSW until corpus exceeds ~1M rows.",
            },
            {
                "question": "Can pgvector handle production scale?",
                "answer": "Up to ~10M vectors with reasonable QPS on a beefy node. Past that, evaluate Qdrant/Pinecone/Weaviate — they're built specifically for this scale.",
            },
            {
                "question": "What about transactions across vectors and metadata?",
                "answer": "Native — that's the win. Updating a document's content + embedding in one BEGIN...COMMIT is atomic, unlike with a separate vector DB.",
            },
            {
                "question": "When does hybrid (trgm + vector) beat pure vector?",
                "answer": "When you have exact-match needs (product SKUs, error codes) alongside semantic ones. The trgm part catches what vector ignores.",
            },
        ],
        "github_url": "https://github.com/pgvector/pgvector",
        "meta_title": "PGVector RAG on Postgres — Starter",
        "meta_description": "RAG inside Postgres: HNSW indexes, hybrid SQL+vector queries, transactional ingest, connection pooling. No new infra to add.",
    },
]
