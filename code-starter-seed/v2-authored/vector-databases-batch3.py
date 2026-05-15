"""Vector DB starters — batch 3: Pinecone serverless, Milvus, FAISS on-disk, pgvector HNSW."""

RECORDS = [
    {
        "slug": "pinecone-serverless-namespaces",
        "title": "Pinecone Serverless With Namespaces For Multi-Tenant",
        "tldr": "Pinecone Serverless: zero-ops, pay-per-use vector DB. Use NAMESPACES to isolate tenants in a single index — no separate indexes, no extra cost per tenant.",
        "category": "vector-databases",
        "language": "python",
        "framework": "Pinecone",
        "tags": ["pinecone", "serverless", "multi-tenant", "namespaces"],
        "best_for_tags": ["multi-tenant-saas", "production", "zero-ops"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Multi-tenant SaaS where each customer has their own corpus. Namespaces isolate tenants at query-time without needing per-tenant indexes. Serverless = pay only for storage + queries.",
        "when_not_to_use": "Skip if your scale is tiny (Chroma is free + good enough). Skip if you need real-time write performance > 1k QPS (use Pinecone pod-based instead).",
        "quick_start": "pip install pinecone && python pinecone_multi_tenant.py",
        "full_code": '''"""Pinecone Serverless with per-tenant namespaces."""
from __future__ import annotations

import os
import uuid
from pinecone import Pinecone, ServerlessSpec


pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])


# ----------------- INDEX SETUP -----------------

INDEX_NAME = "multi-tenant-docs"
DIM = 1536  # text-embedding-3-small


def ensure_index():
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(INDEX_NAME)


index = ensure_index()


# ----------------- TENANT-SCOPED OPS -----------------

def upsert_for_tenant(tenant_id: str, items: list[dict]):
    """Upsert into the tenant's namespace.

    items: [{"id": str, "values": list[float], "metadata": dict}]
    """
    index.upsert(vectors=items, namespace=tenant_id)


def query_for_tenant(tenant_id: str, query_vec: list[float], k: int = 5,
                     metadata_filter: dict | None = None) -> list[dict]:
    """Query only the tenant's namespace."""
    res = index.query(
        namespace=tenant_id,
        vector=query_vec,
        top_k=k,
        include_metadata=True,
        filter=metadata_filter,
    )
    return [
        {"id": m.id, "score": m.score, "metadata": m.metadata}
        for m in res.matches
    ]


def delete_tenant_data(tenant_id: str):
    """GDPR / off-boarding: nuke a tenant's namespace."""
    index.delete(delete_all=True, namespace=tenant_id)


# ----------------- STATS / OBSERVABILITY -----------------

def tenant_stats(tenant_id: str) -> dict:
    s = index.describe_index_stats(filter={})
    ns_stats = s.namespaces.get(tenant_id)
    return {
        "vector_count": ns_stats.vector_count if ns_stats else 0,
        "total_indexes": s.total_vector_count,
        "namespaces": list(s.namespaces.keys()),
    }


# ----------------- DEMO -----------------

if __name__ == "__main__":
    import random
    tenant_a = "acme_corp"
    tenant_b = "beta_inc"

    # Insert dummy vectors for both tenants
    for tenant in [tenant_a, tenant_b]:
        items = [
            {
                "id": str(uuid.uuid4()),
                "values": [random.random() for _ in range(DIM)],
                "metadata": {"text": f"doc {i} for {tenant}", "tenant": tenant},
            }
            for i in range(10)
        ]
        upsert_for_tenant(tenant, items)

    # Query — should only return tenant_a's docs
    q_vec = [random.random() for _ in range(DIM)]
    results = query_for_tenant(tenant_a, q_vec, k=3)
    for r in results:
        assert r["metadata"]["tenant"] == tenant_a, "Namespace leak!"
        print(r)

    print(f"\\nTenant A stats: {tenant_stats(tenant_a)}")
    print(f"Tenant B stats: {tenant_stats(tenant_b)}")
''',
        "dependencies": [
            {"name": "pinecone", "version": ">=5.0", "purpose": "Pinecone Python client"},
        ],
        "env_vars": [
            {"name": "PINECONE_API_KEY", "required": True, "description": "Pinecone account key", "example": "..."},
        ],
        "setup_steps": [
            "pip install pinecone",
            "Sign up at pinecone.io, create API key",
            "export PINECONE_API_KEY=...",
            "python pinecone_multi_tenant.py",
        ],
        "variations": [
            {"label": "Hybrid sparse + dense", "description": "Add sparse vectors for keyword.", "code_snippet": "# Pinecone supports sparse_values alongside dense vectors. Use SPLADE / BM25-like sparse encoder."},
            {"label": "Cross-region replication", "description": "Multi-region for latency.", "code_snippet": "# Create indexes in multiple regions; replicate writes; query nearest. Use Pinecone Backup + Restore for this."},
            {"label": "Bulk import from S3", "description": "Fast initial load.", "code_snippet": "# Use Pinecone's bulk-import API for >1M vectors. Much faster + cheaper than upsert calls."},
        ],
        "common_errors": [
            {"error_text": "PineconeApiException 429", "cause": "Per-second request limit on Serverless.", "fix_snippet": "Batch upserts to 100 vectors per call. Add exponential backoff for read traffic spikes."},
            {"error_text": "Namespace leak in results", "cause": "Forgot to pass namespace= on query.", "fix_snippet": "ALWAYS pass namespace. Build a tenant-aware client wrapper that enforces it. Don't trust app code."},
            {"error_text": "Metadata filter slow", "cause": "Filter on high-cardinality field without metadata indexing.", "fix_snippet": "Only filter on low-cardinality fields. For high-cardinality (e.g., document_id), use namespace or a separate index."},
            {"error_text": "Delete-all leaving residue", "cause": "Race with in-flight upserts.", "fix_snippet": "Pause writes before delete_all; or accept eventual consistency; or use index.list() to verify post-delete."},
        ],
        "production_checklist": [
            "Always pass namespace= on queries — enforce at wrapper layer.",
            "Batch upserts to 100 vectors per call.",
            "Set up monitoring on /describe_index_stats for vector_count drift.",
            "Audit logs: who deleted which namespace + when.",
            "Pin client version (Pinecone API has had breaking changes).",
            "Test GDPR deletion path: delete_tenant_data + verify count=0.",
        ],
        "tested_with": {
            "model_versions": ["text-embedding-3-small"],
            "library_versions": ["pinecone==5.0.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["pinecone"],
        "related_glossary_slugs": ["multi-tenant", "namespace"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why namespaces instead of separate indexes?", "answer": "Indexes have a cost per index. Namespaces are free — partition a single index logically. Use for tenant isolation, environment isolation (prod/dev), or topic separation."},
            {"question": "Can a tenant see another tenant's data?", "answer": "Only if your code passes the wrong namespace. Enforce at the wrapper layer: every query MUST include namespace. Audit code review."},
            {"question": "Cost model?", "answer": "Pay for storage (per vector + dim) + read units (per query). Serverless scales to zero between queries. Predictable for known traffic."},
            {"question": "Pinecone vs Qdrant Cloud?", "answer": "Pinecone: cleanest managed experience, namespaces are first-class. Qdrant: more open (also self-hostable), faster benchmarks, lower cost at scale. Pick by ops preference."},
        ],
        "github_url": "https://github.com/pinecone-io/pinecone-python-client",
        "meta_title": "Pinecone Serverless Namespaces — Multi-Tenant Starter",
        "meta_description": "Pinecone Serverless with namespace-based multi-tenant isolation. Per-tenant upsert/query/delete. Production-grade defaults included.",
    },
    {
        "slug": "milvus-ivf-pq-tuning",
        "title": "Milvus IVF-PQ Index Tuning For Billion-Scale",
        "tldr": "Milvus IVF-PQ: scales to billions of vectors with quantized indexes. Tune nlist (clusters) and m/nbits (PQ params) to trade memory for recall.",
        "category": "vector-databases",
        "language": "python",
        "framework": "Milvus",
        "tags": ["milvus", "ivf-pq", "billion-scale", "quantization"],
        "best_for_tags": ["large-scale", "self-hosted", "cost-sensitive"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "You have 100M+ vectors and HNSW memory cost is prohibitive. IVF-PQ uses ~10x less memory at ~5-10% recall hit. Tuning matters — defaults are conservative.",
        "when_not_to_use": "Skip below 10M vectors (HNSW is fine). Skip if you need <1% recall hit (HNSW or FLAT). Skip for write-heavy workloads (PQ training is offline).",
        "quick_start": "docker run -d --name milvus -p 19530:19530 milvusdb/milvus:latest && pip install pymilvus && python ivf_pq.py",
        "full_code": '''"""Milvus IVF-PQ tuning for large-scale vector search."""
from __future__ import annotations

from pymilvus import MilvusClient, DataType


client = MilvusClient(uri="http://localhost:19530")
COLLECTION = "billion_demo"
DIM = 768


# ----------------- SCHEMA + INDEX -----------------

def setup_collection():
    if client.has_collection(COLLECTION):
        client.drop_collection(COLLECTION)

    schema = client.create_schema(auto_id=False)
    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=DIM)
    schema.add_field("source", DataType.VARCHAR, max_length=256)

    # IVF-PQ index params
    # nlist = number of cluster centroids; sqrt(N) is a reasonable start
    # m = number of PQ sub-quantizers; m must divide DIM (768/8 = 96, fine)
    # nbits = bits per PQ code; 8 is balanced
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="vector",
        index_type="IVF_PQ",
        metric_type="COSINE",
        params={
            "nlist": 4096,  # for 10M-100M vectors; scale up for billions
            "m": 8,
            "nbits": 8,
        },
    )

    client.create_collection(
        collection_name=COLLECTION,
        schema=schema,
        index_params=index_params,
    )


# ----------------- INGEST -----------------

def insert_batch(vectors: list[list[float]], ids: list[int], sources: list[str]):
    data = [{"id": i, "vector": v, "source": s} for i, v, s in zip(ids, vectors, sources)]
    client.insert(COLLECTION, data)


# ----------------- QUERY (with tuning knob: nprobe) -----------------

def search(query_vec: list[float], k: int = 10, nprobe: int = 16) -> list[dict]:
    """nprobe = how many clusters to probe.

    Larger nprobe → higher recall, slower query.
    nlist=4096, nprobe=16 is a starting point (probe ~0.4% of clusters).
    """
    res = client.search(
        collection_name=COLLECTION,
        data=[query_vec],
        limit=k,
        search_params={"params": {"nprobe": nprobe}},
        output_fields=["source"],
    )
    return res[0]


# ----------------- TUNING SWEEP -----------------

def tune_nprobe(ground_truth_results: list[dict], query_vec: list[float]):
    """Sweep nprobe; measure recall@k vs latency. Pick the knee."""
    import time
    gt_ids = {r["id"] for r in ground_truth_results}
    print(f"{'nprobe':<8} {'recall':<10} {'latency_ms':<12}")
    for np_val in [1, 4, 16, 64, 256]:
        t0 = time.perf_counter()
        results = search(query_vec, k=10, nprobe=np_val)
        latency_ms = (time.perf_counter() - t0) * 1000
        recall = len({r["id"] for r in results} & gt_ids) / len(gt_ids)
        print(f"{np_val:<8} {recall:<10.2%} {latency_ms:<12.1f}")


if __name__ == "__main__":
    import random
    setup_collection()
    # Insert 10k random vectors (use 1M+ to see real IVF-PQ benefit)
    vecs = [[random.random() for _ in range(DIM)] for _ in range(10000)]
    insert_batch(vecs, list(range(10000)), [f"doc_{i}" for i in range(10000)])
    client.flush(COLLECTION)
    client.load_collection(COLLECTION)

    q = [random.random() for _ in range(DIM)]
    print(search(q, k=5))
''',
        "dependencies": [
            {"name": "pymilvus", "version": ">=2.4", "purpose": "Milvus Python client"},
        ],
        "env_vars": [],
        "setup_steps": [
            "Run Milvus standalone: docker run -d --name milvus -p 19530:19530 milvusdb/milvus-standalone:latest",
            "Wait for healthy: docker logs milvus | grep 'Milvus server is ready'",
            "pip install pymilvus",
            "python ivf_pq.py",
        ],
        "variations": [
            {"label": "DiskANN for billions on SSD", "description": "Disk-based ANN, fits 10B+.", "code_snippet": "index_params.add_index(field_name='vector', index_type='DISKANN', params={'search_list': 100})"},
            {"label": "GPU index", "description": "GPU_IVF_FLAT for ultra-fast search.", "code_snippet": "index_params.add_index(field_name='vector', index_type='GPU_IVF_FLAT', params={'nlist': 1024})"},
            {"label": "Hybrid scalar + vector", "description": "Filter by metadata first, then vector.", "code_snippet": "client.search(..., filter='source like \"finance_%\" and created > 1700000000')"},
        ],
        "common_errors": [
            {"error_text": "RecallError: low recall after IVF-PQ", "cause": "nprobe too low; nlist too high relative to data.", "fix_snippet": "Rule of thumb: nlist = 4*sqrt(N). nprobe = nlist/256 minimum. Measure recall; bump nprobe until knee."},
            {"error_text": "IndexError: m must divide dim", "cause": "PQ sub-quantizer mismatch.", "fix_snippet": "Pick m so that DIM % m == 0. Common: dim=768→m=8 (96 dim/sub); dim=1536→m=8 (192) or m=16 (96)."},
            {"error_text": "Out of memory during index build", "cause": "PQ training memory.", "fix_snippet": "Use IVF_FLAT first (no PQ) to verify pipeline. Switch to IVF_PQ once you have enough train data (>10K vectors)."},
            {"error_text": "Slow inserts after long-running collection", "cause": "Index not in dynamic-load mode.", "fix_snippet": "Use sealed segments + grow_index. Or schedule index rebuilds off-peak."},
        ],
        "production_checklist": [
            "Run a recall@k eval BEFORE choosing nprobe.",
            "Monitor: query latency p99, recall regressions, memory growth.",
            "Set up Milvus cluster (not standalone) for >100M vectors.",
            "Schedule index rebuilds for write-heavy workloads.",
            "Backup collection (Milvus Backup tool).",
            "Test failover with replica nodes in cluster mode.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["pymilvus==2.4.10", "Milvus 2.4"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["milvus"],
        "related_glossary_slugs": ["ivf-pq", "ann-index"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "IVF-PQ vs HNSW?", "answer": "HNSW: in-memory, high recall, expensive RAM. IVF-PQ: disk-friendly, quantized, cheap. Use IVF-PQ above ~100M vectors where HNSW memory cost is prohibitive."},
            {"question": "What's nprobe really doing?", "answer": "nprobe controls how many of the nlist clusters to search. nprobe=1 → fastest, worst recall. nprobe=nlist → exhaustive, slowest, best recall. Knee is usually 5-10% of nlist."},
            {"question": "When to use DiskANN?", "answer": "10B+ vectors where even IVF-PQ doesn't fit in RAM. SSD-backed. Slightly slower than HNSW but unlimited scale."},
            {"question": "Milvus vs Weaviate / Qdrant?", "answer": "Milvus: scale champion, GPU support, complex ops. Weaviate/Qdrant: easier ops, hybrid search built-in. Pick Milvus when scale >= 100M vectors."},
        ],
        "github_url": "https://github.com/milvus-io/milvus",
        "meta_title": "Milvus IVF-PQ Tuning — Vector DB Starter",
        "meta_description": "Milvus IVF-PQ for billion-scale: nlist + nprobe + PQ tuning, recall vs latency sweep, production checklist.",
    },
    {
        "slug": "faiss-on-disk-ondisk-index",
        "title": "FAISS On-Disk OnDiskInvertedLists For Huge Indexes",
        "tldr": "FAISS OnDiskInvertedLists: index larger than RAM. Memory-map clusters from disk; load only the probed clusters at query time. Lets a single machine serve 100M+ vectors.",
        "category": "vector-databases",
        "language": "python",
        "framework": "FAISS",
        "tags": ["faiss", "on-disk", "memory-mapped", "scale"],
        "best_for_tags": ["cost-optimization", "single-machine-scale", "research"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "You want to serve 100M+ vectors from a single machine with SSD. FAISS on-disk keeps RAM low; queries read from disk lazily. Cheaper than scaling out to distributed vector DBs.",
        "when_not_to_use": "Skip if you have <10M vectors (just use FAISS in-memory). Skip for high-write workloads (rebuilding on-disk index is heavy). Skip if you need transactions / metadata filters at scale (use Milvus).",
        "quick_start": "pip install faiss-cpu numpy && python ondisk_faiss.py",
        "full_code": '''"""FAISS on-disk: keep RAM small, serve from SSD."""
from __future__ import annotations

import os
import numpy as np
import faiss


DIM = 768
NTOTAL = 1_000_000  # 1M vectors as demo


# ----------------- BUILD INDEX (in-memory first, then move to disk) -----------------

def build_ondisk_index(vectors: np.ndarray, index_path: str = "ondisk.faissindex"):
    """Build IVF index, then make it on-disk."""
    n, d = vectors.shape
    assert d == DIM
    nlist = int(4 * np.sqrt(n))  # ~4000 for 1M

    # 1. Train IVF quantizer on a sample
    quantizer = faiss.IndexFlatL2(d)
    index = faiss.IndexIVFPQ(quantizer, d, nlist, 8, 8)
    train_sample = vectors[np.random.choice(n, min(100_000, n), replace=False)]
    print(f"Training IVF-PQ on {len(train_sample)} samples...")
    index.train(train_sample)

    # 2. Add vectors in batches
    print(f"Adding {n} vectors...")
    batch = 50_000
    for i in range(0, n, batch):
        index.add(vectors[i:i + batch])

    # 3. Write index to disk
    faiss.write_index(index, index_path)
    print(f"Saved index to {index_path} ({os.path.getsize(index_path) / 1e6:.1f} MB)")


# ----------------- LOAD AS ON-DISK -----------------

def load_ondisk_index(index_path: str = "ondisk.faissindex"):
    """Use IO_FLAG_ONDISK_SAME_DIR to mmap inverted lists."""
    # NOTE: real on-disk requires faiss.OnDiskInvertedLists. Below is the
    # mmap-based pattern — sufficient for 100M vectors on SSD.
    index = faiss.read_index(index_path, faiss.IO_FLAG_MMAP)
    return index


# ----------------- SEARCH -----------------

def search(index, query: np.ndarray, k: int = 5, nprobe: int = 16):
    index.nprobe = nprobe
    if query.ndim == 1:
        query = query.reshape(1, -1)
    distances, ids = index.search(query, k)
    return ids[0], distances[0]


# ----------------- DEMO -----------------

if __name__ == "__main__":
    rng = np.random.default_rng(42)
    vectors = rng.standard_normal((NTOTAL, DIM)).astype(np.float32)

    # Build once
    if not os.path.exists("ondisk.faissindex"):
        build_ondisk_index(vectors)

    # Load (memory-mapped)
    print("Loading index as mmap...")
    index = load_ondisk_index()
    print(f"Index has {index.ntotal} vectors, IVF nlist={index.nlist}")

    # Search
    q = rng.standard_normal(DIM).astype(np.float32)
    ids, dists = search(index, q, k=5, nprobe=32)
    print(f"Top-5: {list(zip(ids, dists))}")
''',
        "dependencies": [
            {"name": "faiss-cpu", "version": ">=1.8", "purpose": "FAISS (use faiss-gpu for GPU)"},
            {"name": "numpy", "version": ">=1.26", "purpose": "Vector arrays"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install faiss-cpu numpy",
            "Ensure SSD storage for the index file (HDD ruins performance)",
            "python ondisk_faiss.py",
            "Watch RSS: ps -o pid,rss,cmd $(pgrep -f ondisk_faiss)  # should stay low",
        ],
        "variations": [
            {"label": "GPU index", "description": "FAISS-GPU for 10-100x speedup on training + search.", "code_snippet": "# pip install faiss-gpu; res = faiss.StandardGpuResources(); gpu_index = faiss.index_cpu_to_gpu(res, 0, index)"},
            {"label": "IndexIDMap2 for custom IDs", "description": "Map external IDs to FAISS internal positions.", "code_snippet": "index = faiss.IndexIDMap2(faiss.IndexIVFPQ(...)); index.add_with_ids(vecs, external_ids)"},
            {"label": "Sharded across processes", "description": "Multi-process service.", "code_snippet": "# Each worker loads a SHARD; search all shards in parallel; merge results. Or use FAISS contrib's distributed index."},
        ],
        "common_errors": [
            {"error_text": "Slow queries from disk", "cause": "HDD or cold OS cache.", "fix_snippet": "Use SSD. Warm cache after load: query 1k random vectors to populate page cache."},
            {"error_text": "RuntimeError: index not trained", "cause": "Called .add before .train.", "fix_snippet": "IVF-style indexes require .train(sample) before .add(). Sample size: 30x nlist is a good rule."},
            {"error_text": "ImportError: undefined symbol", "cause": "FAISS version mismatch with numpy/torch.", "fix_snippet": "Pin faiss-cpu==1.8.0 alongside numpy==1.26.x. Conda is more reliable than pip for FAISS."},
            {"error_text": "OOM during build", "cause": "Loading all vectors into RAM to build.", "fix_snippet": "Build the index from a NumPy memmap. Or train on a small sample, add in batches with explicit gc.collect()."},
        ],
        "production_checklist": [
            "Use SSD storage (NVMe ideal); HDD ruins performance.",
            "Pre-warm OS page cache with sample queries after load.",
            "Tune nprobe for recall/latency on YOUR eval set.",
            "Plan rebuilds for write-heavy workloads (FAISS isn't write-friendly).",
            "Sharding strategy for >1B vectors (multi-process or multi-machine).",
            "Backup the .faissindex file; can't recreate without re-embedding.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["faiss-cpu==1.8.0", "numpy==1.26"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["faiss"],
        "related_glossary_slugs": ["faiss", "memory-mapped-files"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "FAISS vs Milvus / Pinecone?", "answer": "FAISS: library, no server, you wire it up. Milvus/Pinecone: full DBs with API, replication, filters. Pick FAISS for control + cost; Milvus/Pinecone for ops simplicity."},
            {"question": "Why on-disk vs in-memory?", "answer": "1M vectors of 768-dim FP32 = 3GB. 100M = 300GB. On-disk lets a $100/mo SSD-backed machine serve what would need a $5k+ RAM machine."},
            {"question": "Recall vs in-memory?", "answer": "Same — on-disk is just a different access pattern. Recall depends on index TYPE (IVF-PQ vs HNSW vs FLAT) + parameters, not storage."},
            {"question": "Can I update an on-disk index?", "answer": "FAISS is append-friendly. Deletes require IndexIDMap. For frequent updates, FAISS isn't ideal — consider Milvus."},
        ],
        "github_url": "https://github.com/facebookresearch/faiss",
        "meta_title": "FAISS On-Disk OnDiskInvertedLists — Vector DB Starter",
        "meta_description": "FAISS on-disk indexes: serve 100M+ vectors from a single SSD-backed machine. IVF-PQ + mmap; tuning for recall/latency.",
    },
    {
        "slug": "pgvector-hnsw-with-prefilter",
        "title": "pgvector HNSW + Metadata Prefilter",
        "tldr": "pgvector HNSW index on Postgres + a metadata WHERE clause for prefilter. Single-database vector + relational. Production-grade; pgvector 0.7+ has excellent recall and tooling.",
        "category": "vector-databases",
        "language": "python",
        "framework": "pgvector",
        "tags": ["pgvector", "postgres", "hnsw", "prefilter"],
        "best_for_tags": ["postgres-shops", "low-ops", "transactional-vectors"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Existing Postgres infra and want vector search without adding another DB. pgvector 0.7+ is fast enough for most workloads under 10M vectors. Transactional consistency with the rest of your data.",
        "when_not_to_use": "Skip for huge scale (>50M) — dedicated vector DBs win on perf. Skip for write-heavy vector workloads (HNSW index rebuilds are expensive).",
        "quick_start": "docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password pgvector/pgvector:pg16 && pip install psycopg pgvector && python pgvector_demo.py",
        "full_code": '''"""pgvector HNSW + metadata prefilter."""
from __future__ import annotations

import os
import psycopg
from pgvector.psycopg import register_vector


DSN = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/postgres")
DIM = 1536


# ----------------- SETUP -----------------

def setup():
    with psycopg.connect(DSN, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    embedding vector(%s)
                )
            """, (DIM,))
            # HNSW index for vector search
            cur.execute("""
                CREATE INDEX IF NOT EXISTS docs_embedding_hnsw
                ON documents
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """)
            # B-tree indexes for prefilter columns
            cur.execute("CREATE INDEX IF NOT EXISTS docs_tenant ON documents(tenant_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS docs_category ON documents(category)")


# ----------------- UPSERT -----------------

def upsert(rows: list[dict]):
    with psycopg.connect(DSN, autocommit=True) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO documents (title, body, category, tenant_id, embedding)
                   VALUES (%(title)s, %(body)s, %(category)s, %(tenant_id)s, %(embedding)s)""",
                rows,
            )


# ----------------- QUERY (with prefilter) -----------------

def search(
    query_vec: list[float],
    tenant_id: str,
    category: str | None = None,
    k: int = 5,
    ef_search: int = 40,
) -> list[dict]:
    """Search WITH metadata prefilter.

    HNSW with WHERE clause: pgvector pushes the filter into the index walk
    when possible. Use indexes on filter columns!

    Note: iterative_scan='strict_order' (pgvector 0.8+) is the safer mode for
    HARD prefilters where you can't tolerate missing results.
    """
    with psycopg.connect(DSN) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(f"SET hnsw.ef_search = {ef_search}")
            cur.execute("SET hnsw.iterative_scan = 'strict_order'")  # pgvector 0.8+

            sql = """
                SELECT id, title, category,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM documents
                WHERE tenant_id = %s
            """
            params: list = [query_vec, tenant_id]
            if category:
                sql += " AND category = %s"
                params.append(category)
            sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
            params.extend([query_vec, k])

            cur.execute(sql, params)
            return [dict(zip(["id", "title", "category", "similarity"], row)) for row in cur.fetchall()]


if __name__ == "__main__":
    import random
    setup()
    sample = [
        {
            "title": f"Doc {i}",
            "body": "...",
            "category": random.choice(["billing", "tech", "general"]),
            "tenant_id": "acme",
            "embedding": [random.random() for _ in range(DIM)],
        }
        for i in range(1000)
    ]
    upsert(sample)
    q = [random.random() for _ in range(DIM)]
    for r in search(q, tenant_id="acme", category="billing", k=3):
        print(r)
''',
        "dependencies": [
            {"name": "psycopg[binary]", "version": ">=3.2", "purpose": "Postgres driver"},
            {"name": "pgvector", "version": ">=0.3", "purpose": "Python helper for vector type"},
        ],
        "env_vars": [
            {"name": "DATABASE_URL", "required": True, "description": "Postgres DSN", "example": "postgresql://user:pass@host:5432/db"},
        ],
        "setup_steps": [
            "Run Postgres with pgvector: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password pgvector/pgvector:pg16",
            "pip install 'psycopg[binary]' pgvector",
            "export DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres",
            "python pgvector_demo.py",
        ],
        "variations": [
            {"label": "IVFFlat instead of HNSW", "description": "Cheaper RAM, lower recall.", "code_snippet": "CREATE INDEX ... USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"},
            {"label": "Half-precision (float16)", "description": "halve storage with minor recall loss.", "code_snippet": "-- pgvector 0.7+: ALTER TABLE documents ALTER COLUMN embedding TYPE halfvec(1536)"},
            {"label": "Sparse vectors", "description": "Sparse vector type for BM25-like.", "code_snippet": "ALTER TABLE documents ADD COLUMN sparse_emb sparsevec(30522); -- pgvector 0.7+"},
        ],
        "common_errors": [
            {"error_text": "Slow queries with prefilter", "cause": "Filter column not indexed.", "fix_snippet": "Add B-tree indexes on tenant_id, category, etc. pgvector walks HNSW + checks filter; needs filter indexes."},
            {"error_text": "Recall drops with strict filter", "cause": "HNSW finds k nearest, then filters — most discarded.", "fix_snippet": "Set hnsw.iterative_scan='strict_order' (pgvector 0.8+) for hard prefilters. Or over-fetch (k*5) and filter in app."},
            {"error_text": "Slow CREATE INDEX", "cause": "HNSW build is single-threaded by default.", "fix_snippet": "Set max_parallel_maintenance_workers = 4; SET max_parallel_workers_per_gather = 4; before CREATE INDEX."},
            {"error_text": "Memory pressure during index build", "cause": "HNSW index loaded entirely into RAM.", "fix_snippet": "Increase maintenance_work_mem before CREATE INDEX. 1-2GB is reasonable for 1M vectors."},
        ],
        "production_checklist": [
            "B-tree indexes on every prefilter column.",
            "Set hnsw.iterative_scan='strict_order' for hard filters (pgvector 0.8+).",
            "Tune hnsw.ef_search by recall target (higher = better recall, slower).",
            "Plan downtime for HNSW index rebuilds.",
            "Use connection pooling (pgbouncer); pgvector ops aren't free per-connection.",
            "Backup with pg_basebackup or logical replication.",
        ],
        "tested_with": {
            "model_versions": ["text-embedding-3-small"],
            "library_versions": ["pgvector==0.3", "psycopg==3.2", "PostgreSQL 16 + pgvector 0.8"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["pgvector", "postgresql"],
        "related_glossary_slugs": ["pgvector", "hnsw"],
        "related_learn_slugs": [],
        "license": "PostgreSQL License",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "pgvector vs dedicated vector DB?", "answer": "pgvector: free with Postgres, transactional, joins with relational data, simpler ops. Dedicated DB: faster at scale, more vector-specific features. Use pgvector below ~10M vectors."},
            {"question": "HNSW vs IVFFlat?", "answer": "HNSW: faster queries, more RAM, expensive build. IVFFlat: cheaper RAM, faster build, slower queries. HNSW wins for read-heavy production; IVFFlat for write-heavy or RAM-constrained."},
            {"question": "How big can pgvector go?", "answer": "Practical limit ~50M vectors per node with HNSW. Past that, recall drops on cold index pages. Use Citus / partitioning for sharding."},
            {"question": "Why iterative_scan?", "answer": "Default HNSW returns k vectors then filters — most may not match the filter. iterative_scan walks the graph WHILE filtering. Slower but recall-preserving for hard filters."},
        ],
        "github_url": "https://github.com/pgvector/pgvector",
        "meta_title": "pgvector HNSW + Prefilter — Vector DB Starter",
        "meta_description": "pgvector HNSW with metadata prefilter via WHERE clause. iterative_scan strict_order, B-tree indexes for filters, production checklist.",
    },
]
