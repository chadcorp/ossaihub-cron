"""Vector DB starters — batch 4: Qdrant cluster, Turbopuffer, redis-vl, Marqo."""

RECORDS = [
    {
        "slug": "qdrant-cluster-with-payload-filter",
        "title": "Qdrant Cluster With Payload Filtering",
        "tldr": "Qdrant cluster: horizontal scale via sharding + replication. Payload-indexed filters keep queries fast at scale. Native gRPC + REST. Production-grade.",
        "category": "vector-databases",
        "language": "python",
        "framework": "Qdrant",
        "tags": ["qdrant", "cluster", "filtering", "production"],
        "best_for_tags": ["production", "large-scale", "filtered-search"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "Production vector search at scale (10M+ vectors) with rich metadata filtering. Qdrant's payload index makes filter-then-search fast. Cluster mode for HA + horizontal scale.",
        "when_not_to_use": "Skip for <1M vectors (pgvector / Chroma simpler). Skip if you don't need filtering (FAISS is faster pure-vector). Skip without ops capacity to run a cluster.",
        "quick_start": "docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant && pip install qdrant-client",
        "full_code": '''"""Qdrant cluster: sharding, replication, payload filters, named vectors."""
from __future__ import annotations

import os
from qdrant_client import QdrantClient, models


client = QdrantClient(
    url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
    api_key=os.environ.get("QDRANT_API_KEY"),  # required for cloud / production
    prefer_grpc=True,  # faster than HTTP
)


# ----------------- COLLECTION (sharded + replicated) -----------------

COLLECTION = "documents"
DIM = 1536


def setup_collection():
    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(
            size=DIM,
            distance=models.Distance.COSINE,
            on_disk=False,                          # in-memory for speed
            hnsw_config=models.HnswConfigDiff(m=16, ef_construct=200),
            quantization_config=models.ScalarQuantization(  # 4x storage saving
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8,
                    always_ram=True,
                )
            ),
        ),
        shard_number=3,                              # horizontal sharding
        replication_factor=2,                        # HA
        write_consistency_factor=2,                  # writes must hit 2 replicas
        on_disk_payload=False,
    )

    # Payload indexes — critical for fast filtering
    client.create_payload_index(COLLECTION, "tenant_id", models.KeywordIndexParams(type="keyword"))
    client.create_payload_index(COLLECTION, "category", models.KeywordIndexParams(type="keyword"))
    client.create_payload_index(COLLECTION, "published_at", models.IntegerIndexParams(type="integer"))


# ----------------- UPSERT -----------------

def upsert(points: list[dict]):
    """points: [{id, vector, payload}]"""
    client.upsert(
        collection_name=COLLECTION,
        points=[
            models.PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
            for p in points
        ],
        wait=True,  # wait for write to be acknowledged
    )


# ----------------- SEARCH WITH FILTER -----------------

def search(query_vec: list[float], tenant_id: str, category: str | None = None,
           after_timestamp: int | None = None, k: int = 5):
    """Search WITH metadata filters."""
    filter_conditions = [
        models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id)),
    ]
    if category:
        filter_conditions.append(
            models.FieldCondition(key="category", match=models.MatchValue(value=category))
        )
    if after_timestamp:
        filter_conditions.append(
            models.FieldCondition(key="published_at", range=models.Range(gte=after_timestamp))
        )

    return client.search(
        collection_name=COLLECTION,
        query_vector=query_vec,
        query_filter=models.Filter(must=filter_conditions),
        limit=k,
        with_payload=True,
        score_threshold=0.5,  # filter out poor matches
    )


# ----------------- HYBRID: vector + sparse (BM25-like) -----------------

def search_hybrid(query_vec: list[float], sparse_vec: dict[int, float],
                  tenant_id: str, k: int = 5):
    """Hybrid search using named vectors (dense + sparse)."""
    return client.query_points(
        collection_name=COLLECTION,
        prefetch=[
            models.Prefetch(query=query_vec, using="dense", limit=k * 2),
            models.Prefetch(query=sparse_vec, using="sparse", limit=k * 2),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),  # Reciprocal Rank Fusion
        limit=k,
        query_filter=models.Filter(must=[
            models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id))
        ]),
    )


# ----------------- SCROLL (pagination) -----------------

def scroll_all(tenant_id: str):
    """Iterate all points for a tenant — useful for migrations / re-indexing."""
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION,
            scroll_filter=models.Filter(must=[
                models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id))
            ]),
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        if not points:
            break
        yield from points
        if offset is None:
            break


# ----------------- DEMO -----------------

if __name__ == "__main__":
    import random
    setup_collection()

    sample = [
        {
            "id": i,
            "vector": [random.random() for _ in range(DIM)],
            "payload": {
                "tenant_id": "acme",
                "category": random.choice(["billing", "tech", "general"]),
                "published_at": 1700000000 + i * 86400,
                "text": f"Document {i}",
            },
        }
        for i in range(100)
    ]
    upsert(sample)

    query = [random.random() for _ in range(DIM)]
    results = search(query, tenant_id="acme", category="tech", k=3)
    for r in results:
        print(f"  {r.score:.3f}: {r.payload['text']}")
''',
        "dependencies": [
            {"name": "qdrant-client", "version": ">=1.12", "purpose": "Qdrant Python client"},
        ],
        "env_vars": [
            {"name": "QDRANT_URL", "required": False, "description": "Qdrant cluster URL", "example": "https://...qdrant.io"},
            {"name": "QDRANT_API_KEY", "required": False, "description": "API key for cloud", "example": "..."},
        ],
        "setup_steps": [
            "Run local: docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant",
            "Or sign up at qdrant.tech (cloud)",
            "pip install qdrant-client",
            "Set env vars",
            "python qdrant_demo.py",
        ],
        "variations": [
            {"label": "Disk-based collection", "description": "Cheaper, slower queries.", "code_snippet": "VectorParams(..., on_disk=True); on_disk_payload=True. Used for huge collections that don't fit in RAM."},
            {"label": "Binary quantization", "description": "32x smaller; minor recall loss.", "code_snippet": "quantization_config=BinaryQuantization(binary=BinaryQuantizationConfig(always_ram=True))"},
            {"label": "Multi-vector points", "description": "Per-point multiple embeddings.", "code_snippet": "vectors_config={'title': VectorParams(size=...), 'body': VectorParams(size=...)} # named vectors per point"},
        ],
        "common_errors": [
            {"error_text": "Slow filtering", "cause": "Missing payload index.", "fix_snippet": "Create payload index for every filtered field via create_payload_index. Without index, filter is full-scan."},
            {"error_text": "WriteConsistencyError", "cause": "Replicas not all healthy.", "fix_snippet": "Lower write_consistency_factor to 1 for availability (over consistency). Or wait for replica recovery."},
            {"error_text": "Cluster reshard takes hours", "cause": "Sharding designed for upfront, not online.", "fix_snippet": "Plan shard_number at collection creation. Changing later requires recreate + reindex."},
            {"error_text": "Memory blow-up over time", "cause": "HNSW indexes grow.", "fix_snippet": "Monitor segment count. Run optimizer: client.update_collection_aliases(...). Or schedule re-indexing during low-traffic."},
        ],
        "production_checklist": [
            "Payload indexes on every filter field.",
            "Shard count = expected size / 1M (e.g., 10M vectors → 10 shards).",
            "Replication factor 2+ for HA.",
            "Use gRPC (prefer_grpc=True) over HTTP for perf.",
            "Quantize (scalar or binary) for storage savings.",
            "Backup with snapshot API; test restore.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["qdrant-client==1.12", "Qdrant 1.12"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["qdrant"],
        "related_glossary_slugs": ["qdrant", "vector-search"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Qdrant vs Weaviate vs Milvus?", "answer": "Qdrant: Rust, fast, good filtering. Weaviate: schema-first, GraphQL. Milvus: scale champion (1B+). Pick Qdrant for filtered-search at moderate scale; Milvus for huge scale; Weaviate for schema-first GraphQL flows."},
            {"question": "Cloud vs self-host?", "answer": "Cloud: managed, free tier, fast to start. Self-host: data control, cheaper at scale. Both run same software."},
            {"question": "How big can collection get?", "answer": "Single-node: ~50M vectors with HNSW. Cluster: billions. Past 50M single-node, shard."},
            {"question": "Schema?", "answer": "Schemaless payloads (any JSON). Define payload indexes for fields you filter on. More flexible than Weaviate, less rigid."},
        ],
        "github_url": "https://github.com/qdrant/qdrant",
        "meta_title": "Qdrant Cluster With Payload Filter Starter",
        "meta_description": "Qdrant cluster: sharding, replication, payload-indexed filters, HNSW + scalar quantization, hybrid sparse+dense search.",
    },
    {
        "slug": "turbopuffer-serverless-vector-search",
        "title": "Turbopuffer Serverless Vector Search",
        "tldr": "Turbopuffer: object-storage-backed vector DB. Pay per query + GB-stored, no servers. Cold queries are slower; warm queries fast. Cheap for sporadic / multi-tenant workloads.",
        "category": "vector-databases",
        "language": "python",
        "framework": "Turbopuffer",
        "tags": ["turbopuffer", "serverless", "object-storage", "multi-tenant"],
        "best_for_tags": ["multi-tenant", "sporadic-traffic", "cost-sensitive"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Multi-tenant SaaS where each tenant has sparse vector workloads. Pay-per-query model wins over always-on databases. Cold queries ~200ms; warm queries <50ms.",
        "when_not_to_use": "Skip for steady high-QPS (always-on DB is cheaper). Skip for very low latency (<50ms p99) — cold queries hit object-storage latency.",
        "quick_start": "pip install turbopuffer && python turbopuffer_demo.py",
        "full_code": '''"""Turbopuffer: serverless vector search backed by object storage."""
from __future__ import annotations

import os
import turbopuffer as tpuf


tpuf.api_key = os.environ["TURBOPUFFER_API_KEY"]


# ----------------- NAMESPACE PER TENANT -----------------

def get_namespace(tenant_id: str):
    """Each tenant gets a namespace — fully isolated."""
    return tpuf.Namespace(tenant_id)


# ----------------- UPSERT -----------------

def upsert_docs(tenant_id: str, docs: list[dict]):
    """docs: [{id, vector, attributes (any JSON-like)}]"""
    ns = get_namespace(tenant_id)
    ns.upsert(
        ids=[d["id"] for d in docs],
        vectors=[d["vector"] for d in docs],
        attributes={
            "title": [d["title"] for d in docs],
            "category": [d["category"] for d in docs],
            "created_at": [d["created_at"] for d in docs],
        },
        distance_metric="cosine_distance",
        schema={
            "title": "string",
            "category": "string",
            "created_at": "uint",
        },
    )


# ----------------- QUERY WITH FILTERS -----------------

def search(tenant_id: str, query_vec: list[float], category: str | None = None,
           k: int = 10):
    ns = get_namespace(tenant_id)
    filters = []
    if category:
        filters.append(["category", "Eq", category])
    return ns.query(
        vector=query_vec,
        top_k=k,
        filters=filters if filters else None,
        include_attributes=["title", "category"],
        include_vectors=False,
    )


# ----------------- BM25 + VECTOR HYBRID -----------------

def search_hybrid(tenant_id: str, query_text: str, query_vec: list[float], k: int = 10):
    """Turbopuffer supports full-text + vector via separate calls + RRF."""
    ns = get_namespace(tenant_id)

    # Full-text result (BM25)
    bm25 = ns.query(
        rank_by=("title", "BM25", query_text),
        top_k=k * 2,
    )
    # Vector result
    vec = ns.query(vector=query_vec, top_k=k * 2)

    # Reciprocal Rank Fusion in application
    from collections import defaultdict
    rrf_scores = defaultdict(float)
    for r in (bm25, vec):
        for rank, item in enumerate(r):
            rrf_scores[item.id] += 1.0 / (60 + rank + 1)
    return sorted(rrf_scores.items(), key=lambda x: -x[1])[:k]


# ----------------- BULK OPERATIONS -----------------

def list_tenants() -> list[str]:
    """Enumerate all namespaces (tenants)."""
    return [ns.name for ns in tpuf.Namespace.list()]


def delete_tenant(tenant_id: str):
    """GDPR / offboarding: nuke a tenant's namespace."""
    get_namespace(tenant_id).delete_all()


# ----------------- DEMO -----------------

if __name__ == "__main__":
    import random
    DIM = 1536
    sample = [
        {
            "id": str(i),
            "vector": [random.random() for _ in range(DIM)],
            "title": f"Document {i}",
            "category": random.choice(["billing", "tech", "general"]),
            "created_at": 1700000000 + i,
        }
        for i in range(50)
    ]
    upsert_docs("acme", sample)

    query = [random.random() for _ in range(DIM)]
    for r in search("acme", query, category="tech", k=3):
        print(f"  {r.dist:.3f}: {r.attributes['title']}")
''',
        "dependencies": [
            {"name": "turbopuffer", "version": ">=0.5", "purpose": "Turbopuffer Python SDK"},
        ],
        "env_vars": [
            {"name": "TURBOPUFFER_API_KEY", "required": True, "description": "From turbopuffer.com", "example": "tpuf-..."},
        ],
        "setup_steps": [
            "Sign up at turbopuffer.com (free tier: 100k vectors)",
            "pip install turbopuffer",
            "export TURBOPUFFER_API_KEY=tpuf-...",
            "python turbopuffer_demo.py",
        ],
        "variations": [
            {"label": "Multi-region", "description": "Pick region for residency.", "code_snippet": "tpuf.api_base_url = 'https://api.turbopuffer.com'  # us-central; or eu-central for EU residency"},
            {"label": "Streaming bulk insert", "description": "Large initial loads.", "code_snippet": "# Use batches of 1000-10000; turbopuffer handles concurrent uploads"},
            {"label": "Custom distance metric", "description": "Beyond cosine.", "code_snippet": "ns.upsert(..., distance_metric='euclidean_squared')  # or 'dot_product'"},
        ],
        "common_errors": [
            {"error_text": "First query slow (~200ms)", "cause": "Cold namespace.", "fix_snippet": "Pre-warm critical tenants with a dummy query. Or accept cold latency as part of serverless model."},
            {"error_text": "Schema mismatch on upsert", "cause": "Different attribute types across upserts.", "fix_snippet": "Define schema on first upsert; subsequent upserts must match. Or use schemaless mode (less optimized)."},
            {"error_text": "BM25 not finding obvious matches", "cause": "Index not yet built.", "fix_snippet": "BM25 index builds async after upsert. Wait a few seconds or use ns.refresh(). For instant search, fall back to vector."},
            {"error_text": "Per-tenant cost adds up", "cause": "Many small tenants.", "fix_snippet": "Use single namespace with tenant_id as filter. Trades isolation for cost. Pick based on workload."},
        ],
        "production_checklist": [
            "Use per-tenant namespaces for isolation OR tenant_id filter for cost.",
            "Define schema for filtered/sorted attributes.",
            "Pre-warm critical tenants periodically.",
            "Monitor: cold query rate, p99 latency.",
            "Backup: export to your own storage periodically.",
            "Use BM25 + vector hybrid for best recall.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["turbopuffer==0.5"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["turbopuffer"],
        "related_glossary_slugs": ["serverless-vector-db", "multi-tenant"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Turbopuffer vs Pinecone Serverless?", "answer": "Both: serverless, pay-per-use. Turbopuffer: object-storage-backed (cheaper at scale), Rust-built. Pinecone: more mature, broader ecosystem. Pick by cost + features."},
            {"question": "How serverless really?", "answer": "TRUE serverless: scales to zero. No idle cost. Cold queries hit object storage (~200ms). Warm queries cached locally (<50ms). Trade-off: latency variability."},
            {"question": "Best for what use case?", "answer": "Multi-tenant SaaS with sparse per-tenant traffic. E.g., 10k tenants, each making 100 queries/day. Always-on DBs would cost 100x more."},
            {"question": "Replication / SLA?", "answer": "Replicated across regions in same continent. SLA: see docs. For STRICT availability, run a backup on a different provider."},
        ],
        "github_url": "https://github.com/turbopuffer/turbopuffer-py",
        "meta_title": "Turbopuffer Serverless Vector Search Starter",
        "meta_description": "Turbopuffer: serverless vector DB on object storage. Pay-per-query, scale to zero, per-tenant namespaces, hybrid BM25 + vector.",
    },
    {
        "slug": "redis-vl-vector-search",
        "title": "Redis VL: Vector Search In Redis",
        "tldr": "Redis VL (redis-vector-library): use Redis Stack for vector + structured search. If you already have Redis, free vector store, no new DB. HNSW + flat indexes.",
        "category": "vector-databases",
        "language": "python",
        "framework": "Redis VL",
        "tags": ["redis", "vector-search", "redis-vl", "hybrid"],
        "best_for_tags": ["redis-shops", "small-mid-scale", "low-ops"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Already running Redis Stack for cache / pub-sub. Adding vector search lets you skip introducing a new DB. Good fit up to ~10M vectors.",
        "when_not_to_use": "Skip past 50M vectors (dedicated vector DBs scale better). Skip if not on Redis Stack (need RediSearch module). Skip for sparse Top-K (Redis SET ops are better than vector for some workloads).",
        "quick_start": "docker run -d -p 6379:6379 redis/redis-stack:latest && pip install redisvl && python redis_vl_demo.py",
        "full_code": '''"""Redis VL: vector + structured search using Redis Stack."""
from __future__ import annotations

import os
import numpy as np
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery, FilterQuery, RangeQuery
from redisvl.query.filter import Tag, Num


# ----------------- INDEX SCHEMA -----------------

schema = {
    "index": {
        "name": "docs-idx",
        "prefix": "doc:",
        "key_separator": ":",
        "storage_type": "json",  # or "hash"
    },
    "fields": [
        {"name": "title", "type": "text"},
        {"name": "category", "type": "tag"},
        {"name": "tenant_id", "type": "tag"},
        {"name": "created_at", "type": "numeric"},
        {
            "name": "embedding",
            "type": "vector",
            "attrs": {
                "dims": 1536,
                "algorithm": "hnsw",
                "distance_metric": "cosine",
                "datatype": "float32",
            },
        },
    ],
}


index = SearchIndex.from_dict(
    schema,
    redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379"),
)


# ----------------- INDEX SETUP -----------------

def setup():
    if not index.exists():
        index.create()
    print(f"Index: {index.name}, fields: {[f['name'] for f in schema['fields']]}")


# ----------------- LOAD DATA -----------------

def load(docs: list[dict]):
    index.load(docs)


# ----------------- VECTOR SEARCH -----------------

def search(query_vec: np.ndarray, tenant_id: str, category: str | None = None, k: int = 5):
    filter_expr = Tag("tenant_id") == tenant_id
    if category:
        filter_expr = filter_expr & (Tag("category") == category)

    query = VectorQuery(
        vector=query_vec.tolist(),
        vector_field_name="embedding",
        return_fields=["title", "category"],
        num_results=k,
        filter_expression=filter_expr,
    )
    return index.query(query)


# ----------------- TEXT-ONLY FILTER QUERY (no vector) -----------------

def filter_only(tenant_id: str, category: str):
    query = FilterQuery(
        return_fields=["title", "category"],
        filter_expression=(Tag("tenant_id") == tenant_id) & (Tag("category") == category),
    )
    return index.query(query)


# ----------------- DEMO -----------------

if __name__ == "__main__":
    setup()

    import random
    docs = [
        {
            "id": f"d{i}",
            "title": f"Document {i}",
            "category": random.choice(["billing", "tech", "general"]),
            "tenant_id": "acme",
            "created_at": 1700000000 + i * 86400,
            "embedding": np.random.random(1536).astype(np.float32).tobytes(),
        }
        for i in range(100)
    ]
    load(docs)

    query_vec = np.random.random(1536).astype(np.float32)
    for r in search(query_vec, tenant_id="acme", category="tech", k=3):
        print(f"  {r['vector_distance']:.4f}: {r['title']}")
''',
        "dependencies": [
            {"name": "redisvl", "version": ">=0.3", "purpose": "Redis Vector Library"},
            {"name": "redis", "version": ">=5.0", "purpose": "Redis driver"},
            {"name": "numpy", "version": ">=1.26", "purpose": "Vectors"},
        ],
        "env_vars": [
            {"name": "REDIS_URL", "required": False, "description": "Redis connection", "example": "redis://localhost:6379"},
        ],
        "setup_steps": [
            "Run Redis Stack: docker run -d -p 6379:6379 redis/redis-stack:latest",
            "pip install redisvl redis numpy",
            "python redis_vl_demo.py",
            "Check Redis Insight at http://localhost:8001 for UI",
        ],
        "variations": [
            {"label": "Flat index for small datasets", "description": "Exact search if <100k vectors.", "code_snippet": "embedding field: 'algorithm': 'flat'  # exact, no HNSW overhead, fine up to ~100k"},
            {"label": "Use semantic-cache decorator", "description": "Cache LLM responses by query similarity.", "code_snippet": "from redisvl.extensions.llmcache import SemanticCache; cache = SemanticCache(name='llm', redis_url=...); cache.store(prompt, response)"},
            {"label": "Streamlined upserts", "description": "Pipelined writes.", "code_snippet": "# index.load supports concurrent writes; use chunks of 1000 for throughput"},
        ],
        "common_errors": [
            {"error_text": "WRONGTYPE error on load", "cause": "Storage type mismatch (json vs hash).", "fix_snippet": "Schema's storage_type must match how you load. For JSON storage, fields are JSONPath. For Hash, use HSET-compatible flat dicts."},
            {"error_text": "Filter query slow", "cause": "Tag/numeric field not indexed.", "fix_snippet": "Add field to schema 'fields'. Index must be recreated when schema changes (or use alter)."},
            {"error_text": "OOM on huge collection", "cause": "All vectors in Redis RAM.", "fix_snippet": "Redis is in-memory. Plan RAM: vectors_count × dim × 4 bytes. Use HNSW (less RAM than flat) or shard via Redis Cluster."},
            {"error_text": "Hash vs JSON output confusion", "cause": "Different return formats.", "fix_snippet": "Hash storage returns flat dicts; JSON returns nested. Pick at schema creation; can't swap easily."},
        ],
        "production_checklist": [
            "Use Redis Stack (or Redis 8+) — vanilla Redis doesn't have RediSearch.",
            "Use HNSW for >100k vectors.",
            "Add Tag indexes on every filtered field.",
            "Persist: enable Redis AOF for durability.",
            "Backup: BGSAVE + offsite RDB dumps.",
            "For >10M vectors, consider Redis Cluster or dedicated vector DB.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["redisvl==0.3", "Redis Stack 7"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["redis"],
        "related_glossary_slugs": ["vector-search", "redis-vl"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Redis VL vs dedicated vector DB?", "answer": "Redis VL: piggyback on Redis you already have. Dedicated DB: purpose-built, better at scale. Use Redis VL if you're already Redis-heavy AND <10M vectors."},
            {"question": "Vector dims limit?", "answer": "Up to 32k dims per vector. Typical is 768-1536. Storage scales linearly with dim."},
            {"question": "Semantic cache use case?", "answer": "Built-in SemanticCache decorator: cache LLM responses; future queries with similar embeddings reuse. ~30-70% cache hits typical for chat applications."},
            {"question": "Redis Cloud?", "answer": "Redis Cloud has managed Redis Stack tiers. Works with redisvl out of the box. Higher cost than self-host but zero ops."},
        ],
        "github_url": "https://github.com/redis/redis-vl-python",
        "meta_title": "Redis VL Vector Search Starter",
        "meta_description": "Redis Stack + redisvl: vector + structured search in Redis. HNSW, tag/numeric filters, semantic cache. Skip a new DB.",
    },
    {
        "slug": "marqo-managed-vector-search",
        "title": "Marqo Managed Vector Search With Multi-Modal",
        "tldr": "Marqo: open-source vector search with built-in embedding generation. Index text + images + structured data in one API. Avoids the 'embed separately, store separately' dance.",
        "category": "vector-databases",
        "language": "python",
        "framework": "Marqo",
        "tags": ["marqo", "multi-modal", "vector-search", "managed-embeddings"],
        "best_for_tags": ["multi-modal", "rapid-prototyping", "e-commerce"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Multi-modal search (text + images) where you want embedding generation handled BY the DB. Cleaner than embedding separately + storing. Good for e-commerce product search.",
        "when_not_to_use": "Skip if you already have an embedding pipeline (extra abstraction adds friction). Skip for extremely large scale (>50M docs) — dedicated solutions scale better.",
        "quick_start": "docker run --name marqo -d -p 8882:8882 marqoai/marqo:latest && pip install marqo",
        "full_code": '''"""Marqo: integrated vector + embedding generation + multi-modal."""
from __future__ import annotations

import os
import marqo


mq = marqo.Client(url=os.environ.get("MARQO_URL", "http://localhost:8882"))


INDEX_NAME = "products"


# ----------------- CREATE INDEX -----------------

def setup_index():
    if INDEX_NAME in [i.index_name for i in mq.get_indexes().get("results", [])]:
        return
    mq.create_index(
        INDEX_NAME,
        settings_dict={
            "type": "unstructured",
            # Multi-modal: text + image via CLIP-like model
            "model": "open_clip/ViT-B-32/laion2b_s34b_b79k",
            "treatUrlsAndPointersAsImages": True,
            "normalizeEmbeddings": True,
        },
    )


# ----------------- INGEST (with embedding auto-generation) -----------------

def add_products(products: list[dict]):
    """Marqo generates embeddings server-side from designated fields."""
    mq.index(INDEX_NAME).add_documents(
        products,
        tensor_fields=["title", "description", "image_url"],  # which fields to embed
        client_batch_size=100,
    )


# ----------------- SEARCH (text or image) -----------------

def search_text(query: str, k: int = 5):
    return mq.index(INDEX_NAME).search(query, limit=k)


def search_image(image_url: str, k: int = 5):
    """Multi-modal: search with an image."""
    return mq.index(INDEX_NAME).search(image_url, limit=k)


def search_combined(text_weight: float, image_url: str, text: str, k: int = 5):
    """Weighted combination of text + image queries."""
    return mq.index(INDEX_NAME).search(
        q={text: text_weight, image_url: 1 - text_weight},
        limit=k,
    )


# ----------------- FILTERED SEARCH -----------------

def search_with_filter(query: str, category: str, min_price: float, k: int = 5):
    return mq.index(INDEX_NAME).search(
        query,
        filter_string=f"category:({category}) AND price:[{min_price} TO *]",
        limit=k,
    )


# ----------------- DEMO -----------------

if __name__ == "__main__":
    setup_index()

    sample_products = [
        {
            "_id": "p1",
            "title": "Wireless Headphones",
            "description": "Noise-cancelling over-ear headphones with 40h battery.",
            "image_url": "https://example.com/headphones.jpg",
            "category": "audio",
            "price": 299.99,
        },
        {
            "_id": "p2",
            "title": "Mechanical Keyboard",
            "description": "Tactile switches, RGB backlight, USB-C.",
            "image_url": "https://example.com/keyboard.jpg",
            "category": "peripherals",
            "price": 149.99,
        },
    ]
    add_products(sample_products)

    # Text search
    for r in search_text("noise-cancelling audio")["hits"]:
        print(f"  {r['_score']:.3f}: {r['title']}")

    # Filter search
    for r in search_with_filter("typing accessory", "peripherals", 100)["hits"]:
        print(f"  {r['title']}")
''',
        "dependencies": [
            {"name": "marqo", "version": ">=3.0", "purpose": "Marqo Python client"},
        ],
        "env_vars": [
            {"name": "MARQO_URL", "required": False, "description": "Marqo server URL", "example": "http://localhost:8882"},
        ],
        "setup_steps": [
            "Run server: docker run --name marqo -d -p 8882:8882 marqoai/marqo:latest",
            "pip install marqo",
            "Create index with multi-modal model",
            "Add documents — embeddings generated server-side",
            "Search by text or image URL",
        ],
        "variations": [
            {"label": "Custom embedding model", "description": "Use HF model.", "code_snippet": "settings_dict={'model': 'hf/all-MiniLM-L6-v2'}; loads sentence-transformers model"},
            {"label": "Structured index", "description": "Predefined schema.", "code_snippet": "create_index(..., settings_dict={'type': 'structured', 'allFields': [{'name': 'title', 'type': 'text'}, ...]})"},
            {"label": "Marqo Cloud", "description": "Managed hosting.", "code_snippet": "mq = marqo.Client(url='https://api.marqo.ai', api_key='...')  # managed cloud"},
        ],
        "common_errors": [
            {"error_text": "Image URL not loaded", "cause": "Marqo couldn't download.", "fix_snippet": "Verify URL is public (Marqo fetches server-side). For private images: pre-encode + send embeddings directly."},
            {"error_text": "Model download slow on first index", "cause": "Open-CLIP model is large.", "fix_snippet": "First-time: 5-10 min. Cache to host volume (-v marqo_data:/data) to persist across restarts."},
            {"error_text": "Memory growth over time", "cause": "Marqo holds many indexes.", "fix_snippet": "Delete unused indexes. Use Marqo Cloud for scale. Self-host: monitor RAM, restart if necessary."},
            {"error_text": "Filter syntax mismatch", "cause": "Lucene-like syntax.", "fix_snippet": "Marqo uses Lucene query syntax for filters: 'field:value AND otherfield:[min TO max]'. Not standard JSON filter."},
        ],
        "production_checklist": [
            "Use Marqo Cloud for production unless heavy ops capacity.",
            "Pin model version (changing model needs full re-index).",
            "Mount /data volume for model + index persistence.",
            "Test filter syntax (Lucene quirks).",
            "Pre-warm by adding sample data to keep model loaded.",
            "Monitor RAM — Marqo is memory-heavy.",
        ],
        "tested_with": {
            "model_versions": ["open_clip/ViT-B-32"],
            "library_versions": ["marqo==3.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["marqo"],
        "related_glossary_slugs": ["multi-modal-search", "marqo"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Marqo vs Qdrant + CLIP?", "answer": "Marqo: integrated (DB + embedding + multi-modal). Qdrant: bring-your-own embeddings. Marqo is faster to start; Qdrant is more flexible at scale."},
            {"question": "Multi-modal benefit?", "answer": "Search by text OR image with SAME index. E-commerce: search product images by description. News: search articles by accompanying image. Avoids parallel infra."},
            {"question": "Cost?", "answer": "Self-host: free + hosting cost. Marqo Cloud: starts ~$50/mo. Compare to: separate embedding API + separate vector DB which is usually cheaper at scale."},
            {"question": "When NOT to use Marqo?", "answer": "If you have an existing embedding pipeline (extra abstraction). If you need ultra-scale (>50M docs). For pure text RAG, leaner DBs are simpler."},
        ],
        "github_url": "https://github.com/marqo-ai/marqo",
        "meta_title": "Marqo Multi-Modal Vector Search Starter",
        "meta_description": "Marqo: integrated DB + embedding generation + multi-modal. Search text or images with one API. Self-host or cloud.",
    },
]
