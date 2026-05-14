"""Vector DB starters — batch 2: Weaviate, lance/lancedb."""

RECORDS = [
    {
        "slug": "weaviate-hybrid-named-vectors",
        "title": "Weaviate Hybrid Search With Named Vectors",
        "tldr": "Weaviate v1.24+ named vectors: store multiple embeddings per object (semantic + keyword + image), search across them in a hybrid query. Schema-first, GraphQL-native.",
        "category": "vector-databases",
        "language": "python",
        "framework": "Weaviate",
        "tags": ["weaviate", "named-vectors", "hybrid-search", "multi-modal"],
        "best_for_tags": ["multi-modal-rag", "rich-search", "schema-first"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "When you need multiple vector representations per object (e.g., title-only vector + full-text vector + image vector) AND structured filtering. Weaviate's schema-first approach + named vectors fits this.",
        "when_not_to_use": "Skip for simple single-vector use cases (Qdrant or Chroma simpler). Skip if you don't want a heavy database — Weaviate runs as a service.",
        "quick_start": "docker run -p 8080:8080 -p 50051:50051 cr.weaviate.io/semitechnologies/weaviate:latest && pip install weaviate-client && python weaviate_demo.py",
        "full_code": '''"""Weaviate v4 client: hybrid search with named vectors.

Each object has TWO vectors (title vs full text); query can target either or both.
"""
from __future__ import annotations

import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Configure, DataType, Property


client = weaviate.connect_to_local()  # default localhost:8080


# ----------------- SCHEMA -----------------

def ensure_collection():
    if client.collections.exists("Article"):
        return
    client.collections.create(
        name="Article",
        properties=[
            Property(name="title", data_type=DataType.TEXT),
            Property(name="body", data_type=DataType.TEXT),
            Property(name="category", data_type=DataType.TEXT),
            Property(name="published_at", data_type=DataType.DATE),
        ],
        vectorizer_config=[
            Configure.NamedVectors.text2vec_openai(
                name="title_vector",
                source_properties=["title"],
            ),
            Configure.NamedVectors.text2vec_openai(
                name="body_vector",
                source_properties=["body"],
            ),
        ],
    )


# ----------------- INGEST -----------------

def ingest(articles: list[dict]) -> int:
    coll = client.collections.get("Article")
    with coll.batch.dynamic() as batch:
        for a in articles:
            batch.add_object(properties=a)
    return len(articles)


# ----------------- QUERIES -----------------

def hybrid_query(query: str, *, target_vector: str = "body_vector", limit: int = 5):
    """Hybrid (BM25 + vector) search against a specific named vector."""
    coll = client.collections.get("Article")
    return coll.query.hybrid(
        query=query,
        target_vector=target_vector,
        limit=limit,
        return_metadata=wvc.query.MetadataQuery(score=True),
    ).objects


def filtered_query(query: str, category: str, limit: int = 5):
    """Hybrid + metadata filter."""
    coll = client.collections.get("Article")
    return coll.query.hybrid(
        query=query,
        target_vector="body_vector",
        filters=wvc.query.Filter.by_property("category").equal(category),
        limit=limit,
    ).objects


def cross_vector_query(query: str, limit: int = 5):
    """Query both vectors; weight differently."""
    coll = client.collections.get("Article")
    # Search title_vector first (broad recall)
    title_hits = coll.query.near_text(query=query, target_vector="title_vector", limit=limit * 2).objects
    # Then body_vector
    body_hits = coll.query.near_text(query=query, target_vector="body_vector", limit=limit * 2).objects
    # Merge by RRF in application code
    return title_hits + body_hits  # simplified; real version does RRF dedup


if __name__ == "__main__":
    ensure_collection()
    sample = [
        {"title": "Reciprocal Rank Fusion", "body": "RRF merges ranked lists from retrievers...", "category": "rag", "published_at": "2024-01-15T00:00:00Z"},
        {"title": "HNSW vs IVFFlat", "body": "HNSW gives faster queries...", "category": "infra", "published_at": "2024-02-10T00:00:00Z"},
    ]
    ingest(sample)

    for hit in hybrid_query("how do I combine retrievers"):
        print(f"  {hit.properties.get('title')}: score={hit.metadata.score}")

    client.close()
''',
        "dependencies": [
            {"name": "weaviate-client", "version": ">=4.7", "purpose": "Weaviate v4 Python client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "For text2vec_openai vectorizer", "example": "sk-..."},
        ],
        "setup_steps": [
            "docker run -d -p 8080:8080 -p 50051:50051 -e OPENAI_APIKEY=$OPENAI_API_KEY cr.weaviate.io/semitechnologies/weaviate:latest",
            "pip install weaviate-client",
            "export OPENAI_API_KEY=sk-...",
            "python weaviate_demo.py",
            "Browse http://localhost:8080/v1/meta",
        ],
        "variations": [
            {"label": "Weaviate Cloud", "description": "Managed; no self-host.", "code_snippet": "client = weaviate.connect_to_weaviate_cloud(cluster_url='...', auth_credentials=weaviate.auth.AuthApiKey('...'))"},
            {"label": "Local embeddings (no OpenAI)", "description": "Use text2vec-transformers for self-contained.", "code_snippet": "# Run weaviate with TRANSFORMERS_INFERENCE_API; replace vectorizer with text2vec_transformers"},
            {"label": "Image vector", "description": "Multi-modal collection.", "code_snippet": "Configure.NamedVectors.multi2vec_clip(name='image_vector', image_fields=['image'])"},
        ],
        "common_errors": [
            {"error_text": "WeaviateConnectionError: failed to connect", "cause": "Weaviate not running or wrong port.", "fix_snippet": "Verify: curl http://localhost:8080/v1/meta. Adjust connect_to_local() port if you mapped differently."},
            {"error_text": "Vectorizer not configured", "cause": "OPENAI_APIKEY not passed to Weaviate at startup.", "fix_snippet": "When starting docker: -e OPENAI_APIKEY=$OPENAI_API_KEY. Vectorizers run inside Weaviate, need the key."},
            {"error_text": "v4 vs v3 client confusion", "cause": "Old documentation uses v3 syntax.", "fix_snippet": "Pin weaviate-client>=4.0; v3 syntax (client.data_object.create) is removed. Use collections.get(...) pattern."},
            {"error_text": "Batch upload silently dropping objects", "cause": "Errors in batch not surfaced.", "fix_snippet": "After batch context exits, check batch.failed_objects; log and retry."},
        ],
        "production_checklist": [
            "Use Weaviate Cloud or replicated cluster for production HA.",
            "Set up backups (Weaviate has built-in backup module).",
            "Monitor schema migrations; classes are append-only for properties.",
            "Use client.close() to clean up gRPC connections.",
            "Pin client version + Weaviate version compatibility.",
            "Test multi-tenant isolation via tenant property if used.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["weaviate-client==4.9.0", "Weaviate server 1.27"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["weaviate"],
        "related_glossary_slugs": ["named-vectors", "hybrid-search"],
        "related_learn_slugs": [],
        "license": "BSD-3-Clause",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Weaviate vs Qdrant?", "answer": "Weaviate: schema-first, named vectors, GraphQL native. Qdrant: schema-loose, faster perf benchmarks, payload filtering. Pick by team preference; both are production-grade."},
            {"question": "Why named vectors?", "answer": "Different aspects of an object benefit from different vectorizations. Title vs body, English vs other languages, text vs image — named vectors let one object hold multiple representations."},
            {"question": "Can I do this in Qdrant?", "answer": "Yes — Qdrant supports multiple vectors per point. Different ergonomics. Weaviate's vectorizer integration is built-in; Qdrant's is application-level."},
            {"question": "GraphQL vs REST vs gRPC?", "answer": "v4 client uses gRPC by default (fastest). GraphQL still available for ad-hoc queries via browser. REST for legacy. gRPC for app code."},
        ],
        "github_url": "https://github.com/weaviate/weaviate",
        "meta_title": "Weaviate Hybrid Search With Named Vectors — Starter",
        "meta_description": "Multiple vectors per object (title + body + image), hybrid BM25+vector search, schema-first. Weaviate v4 client.",
    },
    {
        "slug": "lancedb-embedded-vector-store",
        "title": "LanceDB Embedded Vector Store (No Server)",
        "tldr": "LanceDB stores vectors in a columnar Parquet/Lance format on disk — no server, no Docker. Great for embedded apps, desktop tools, and serverless functions where a stateful server isn't an option.",
        "category": "vector-databases",
        "language": "python",
        "framework": "LanceDB",
        "tags": ["lancedb", "embedded", "serverless", "no-ops"],
        "best_for_tags": ["desktop-apps", "serverless", "embedded-rag"],
        "difficulty_tier": "beginner",
        "featured": False,
        "when_to_use": "When you need vector search but can't or don't want to run a server. Reads from disk (or S3), works in AWS Lambda, ships with a desktop app. Files are Parquet-compatible.",
        "when_not_to_use": "Skip for high-write workloads (Lance format optimized for read). Skip for very high QPS (no shared index across requests). Skip when you need a queryable API for non-Python consumers.",
        "quick_start": "pip install lancedb && python lance_demo.py",
        "full_code": '''"""LanceDB embedded vector store.

Files: ./data/lancedb/<table>.lance
No server. Just import and read/write.
"""
from __future__ import annotations

import lancedb
import pyarrow as pa
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("all-MiniLM-L6-v2")


def get_db(path: str = "./data/lancedb"):
    return lancedb.connect(path)


def ensure_table(db) -> "lancedb.Table":
    if "documents" in db.table_names():
        return db.open_table("documents")
    schema = pa.schema([
        pa.field("id", pa.int64()),
        pa.field("text", pa.string()),
        pa.field("source", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), 384)),  # all-MiniLM-L6-v2 is 384 dims
    ])
    return db.create_table("documents", schema=schema)


def ingest(rows: list[dict]) -> int:
    db = get_db()
    table = ensure_table(db)
    # Embed
    texts = [r["text"] for r in rows]
    vectors = embedder.encode(texts).tolist()
    for r, v in zip(rows, vectors):
        r["vector"] = v
    table.add(rows)
    return len(rows)


def query(question: str, *, k: int = 5, filter_source: str | None = None):
    db = get_db()
    table = db.open_table("documents")
    qvec = embedder.encode([question])[0].tolist()
    search = table.search(qvec).limit(k)
    if filter_source:
        search = search.where(f"source = '{filter_source}'")
    return search.to_pandas()


def create_index():
    """Build an ANN index for faster queries on large tables."""
    db = get_db()
    table = db.open_table("documents")
    table.create_index(
        vector_column_name="vector",
        index_type="IVF_PQ",                # alternatives: IVF_HNSW_SQ, FLAT
        num_partitions=256,
        num_sub_vectors=96,
    )


if __name__ == "__main__":
    ingest([
        {"id": 1, "text": "Reciprocal rank fusion combines retriever lists.", "source": "rag.md"},
        {"id": 2, "text": "HNSW is fast but RAM-heavy.", "source": "vectors.md"},
        {"id": 3, "text": "Embedded vector stores skip the server.", "source": "infra.md"},
    ])
    print(query("how do I merge retrievers?"))
''',
        "dependencies": [
            {"name": "lancedb", "version": ">=0.13", "purpose": "Embedded vector store"},
            {"name": "pyarrow", "version": ">=17.0", "purpose": "Schema definitions (LanceDB internals)"},
            {"name": "sentence-transformers", "version": ">=3.0", "purpose": "Local embeddings"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install lancedb sentence-transformers pyarrow",
            "python lance_demo.py",
            "Data persists to ./data/lancedb/",
        ],
        "variations": [
            {"label": "S3 backing", "description": "Store data on S3 instead of local disk.", "code_snippet": "db = lancedb.connect('s3://my-bucket/lancedb/', storage_options={'aws_access_key_id': '...', 'aws_secret_access_key': '...'})"},
            {"label": "Hybrid search", "description": "Add full-text search alongside vector.", "code_snippet": "table.create_fts_index(['text'])  # full-text search\\n# Then: table.search(query='...', query_type='hybrid')"},
            {"label": "AWS Lambda deployment", "description": "Ship LanceDB in a Lambda layer.", "code_snippet": "# Bundle lancedb + sentence-transformers in a Lambda layer (~200MB).\\n# Use S3 for table storage; Lambda has read-only filesystem except /tmp."},
            {"label": "Versioning", "description": "Time-travel queries.", "code_snippet": "table.checkout(version=3)  # query previous version of data\\ntable.list_versions()  # see history"},
        ],
        "common_errors": [
            {"error_text": "ValueError: Vector dimensions don't match", "cause": "Schema fixed at 384; switching embedding model.", "fix_snippet": "Either re-create table with new dim, or use a fresh table per model. Schema is immutable for vector column dimensions."},
            {"error_text": "Slow queries on large tables", "cause": "No ANN index.", "fix_snippet": "Call table.create_index() once after substantial ingest. IVF_PQ is the safe default."},
            {"error_text": "ImportError: No module named 'pyarrow'", "cause": "Optional dep missing.", "fix_snippet": "pip install pyarrow. LanceDB schema definitions require it."},
            {"error_text": "Data not visible across processes", "cause": "Each process opens its own connection.", "fix_snippet": "Normal — LanceDB is file-based. Just open the same path; latest writes are visible to all readers."},
        ],
        "production_checklist": [
            "For serverless (Lambda), pre-bake the dependency layer (lancedb + embedder).",
            "Use S3 backing for distributed access; local disk for single-process.",
            "Build ANN index after bulk ingest; queries without are linear scan.",
            "Snapshot tables periodically (Lance versioning is built in).",
            "Pin lancedb version; storage format has evolved.",
            "For high-write workloads, consider Qdrant/Pinecone instead.",
        ],
        "tested_with": {
            "model_versions": ["all-MiniLM-L6-v2"],
            "library_versions": ["lancedb==0.13.0", "pyarrow==17.0.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["lancedb"],
        "related_glossary_slugs": ["embedded-vector-store", "lance-format"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "LanceDB vs SQLite vector extension?", "answer": "LanceDB: purpose-built for vectors, ANN indexes, version control. SQLite + vector: minimal addition to existing SQLite. For pure vector workloads, LanceDB. For mixed SQL + vector, SQLite extension wins simplicity."},
            {"question": "Can I run this in the browser?", "answer": "Not directly — Python only. For browser, LanceDB has a Rust core; community ports for WASM exist but aren't production-grade yet."},
            {"question": "Schema migration?", "answer": "Add columns: yes via Lance's schema evolution. Change vector dim: no, recreate table. Plan dimensions carefully upfront."},
            {"question": "Why Lance format?", "answer": "Columnar, optimized for ML workloads, Parquet-compatible. Lets you read with pandas/Spark/DuckDB without LanceDB. Vector queries need LanceDB's index reader."},
        ],
        "github_url": "https://github.com/lancedb/lancedb",
        "meta_title": "LanceDB Embedded Vector Store — Starter",
        "meta_description": "Embedded vector DB with no server: Lance/Parquet format on disk or S3, ANN indexes, versioning. Great for Lambda + desktop apps.",
    },
]
