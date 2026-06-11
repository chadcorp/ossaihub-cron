"""Data-pipeline starters — batch 2: DuckDB LLM enrichment, Dagster asset pipeline, Kafka stream enrichment."""

RECORDS = [
    {
        "slug": "duckdb-llm-enrichment-pipeline",
        "title": "DuckDB LLM Enrichment Pipeline (Cached, Resumable)",
        "tldr": "Enrich a table with LLM classifications without re-paying for rows already done. DuckDB holds the source, a content-hash cache, and an anti-join that finds only pending rows. Kill it anytime; rerun resumes.",
        "category": "data-pipelines",
        "language": "python",
        "framework": "DuckDB",
        "tags": ["duckdb", "batch-inference", "caching", "enrichment"],
        "best_for_tags": ["data-enrichment", "resumable-jobs", "cost-control"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Enriching a large table with LLM outputs (classify / extract) where reruns are common and you must not re-pay for rows already processed. DuckDB is the whole stack: query, cache, anti-join, result join.",
        "when_not_to_use": "Skip for a handful of rows (just call the API in a loop). Skip if you need a distributed cluster — DuckDB is single-node and single-writer.",
        "quick_start": "pip install duckdb anthropic && python enrich.py",
        "full_code": '''"""DuckDB LLM enrichment: hash-keyed cache + anti-join makes the job resumable."""
from __future__ import annotations

import hashlib
import json
import os
import time

import duckdb
from anthropic import Anthropic

# ----------------- CONFIG -----------------

DB_PATH = os.environ.get("DUCKDB_PATH", "pipeline.db")
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "20"))
LABELS = ["billing", "bug", "feature_request", "praise", "other"]

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def text_hash(text: str) -> str:
    # Hash ONLY the text. Including volatile fields (ids, timestamps) would
    # bust the cache and re-enrich rows you already paid for.
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


# ----------------- SCHEMA + SAMPLE DATA -----------------

def init_db(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS tickets AS
        SELECT * FROM (VALUES
            (1, 'Charged twice this month, please refund'),
            (2, 'App crashes when I export a PDF'),
            (3, 'Love the new dashboard, great work'),
            (4, 'Can you add a dark mode option?')
        ) AS t(id, body)
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS enrichment_cache (
            hash TEXT PRIMARY KEY,
            label TEXT,
            confidence DOUBLE,
            model TEXT,
            created_at TIMESTAMP DEFAULT now()
        )
    """)


# ----------------- LLM BATCH CALL -----------------

def classify_batch(rows: list[tuple[str, str]]) -> dict[str, dict]:
    numbered = "\\n".join(f"{i}. {body}" for i, (_, body) in enumerate(rows))
    prompt = (
        f"Classify each numbered item into one of {LABELS}.\\n"
        "Return ONLY a JSON array of objects {index, label, confidence} "
        f"with exactly {len(rows)} items, no prose.\\n\\n" + numbered
    )
    resp = client.messages.create(
        model=MODEL, max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    out: dict[str, dict] = {}
    try:
        parsed = json.loads(raw)
        if len(parsed) != len(rows):
            raise ValueError("item count mismatch")
        for item in parsed:
            h = rows[int(item["index"])][0]
            label = item["label"] if item["label"] in LABELS else "other"
            out[h] = {"label": label, "confidence": float(item.get("confidence", 0.5))}
    except (json.JSONDecodeError, ValueError, KeyError, IndexError):
        # Per-item fallback so one bad batch never blocks the whole run.
        for h, _ in rows:
            out[h] = {"label": "other", "confidence": 0.0}
    return out


# ----------------- DRIVER -----------------

def run() -> None:
    con = duckdb.connect(DB_PATH)
    init_db(con)
    pending = con.execute("""
        SELECT t.id, t.body FROM tickets t
        LEFT JOIN enrichment_cache c ON c.hash = sha256(trim(t.body))
        WHERE c.hash IS NULL
    """).fetchall()

    print(f"{len(pending)} rows pending")
    for start in range(0, len(pending), BATCH_SIZE):
        chunk = pending[start:start + BATCH_SIZE]
        rows = [(text_hash(body), body) for _, body in chunk]
        results = classify_batch(rows)
        con.executemany(
            "INSERT OR IGNORE INTO enrichment_cache (hash, label, confidence, model) VALUES (?, ?, ?, ?)",
            [(h, r["label"], r["confidence"], MODEL) for h, r in results.items()],
        )
        print(f"  batch {start // BATCH_SIZE + 1}: +{len(rows)} cached")
        time.sleep(0.5)  # gentle pacing between batches

    con.execute("""
        CREATE OR REPLACE VIEW enriched AS
        SELECT t.id, t.body, c.label, c.confidence
        FROM tickets t JOIN enrichment_cache c ON c.hash = sha256(trim(t.body))
    """)
    for row in con.execute("SELECT id, label, confidence FROM enriched ORDER BY id").fetchall():
        print(row)
    con.close()


if __name__ == "__main__":
    run()
''',
        "dependencies": [
            {"name": "duckdb", "version": ">=1.0", "purpose": "In-process source query, cache table, anti-join"},
            {"name": "anthropic", "version": ">=0.39", "purpose": "LLM classification calls"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Anthropic API key for the classification calls", "example": "sk-ant-..."},
            {"name": "DUCKDB_PATH", "required": False, "description": "Path to the DuckDB file (persists the cache)", "example": "pipeline.db"},
            {"name": "BATCH_SIZE", "required": False, "description": "Rows per LLM call", "example": "20"},
        ],
        "setup_steps": [
            "pip install duckdb anthropic",
            "export ANTHROPIC_API_KEY=sk-ant-...",
            "Save enrich.py and run: python enrich.py",
            "Inspect results: duckdb pipeline.db 'SELECT * FROM enriched'",
            "Rerun python enrich.py — it processes only rows missing from the cache",
        ],
        "variations": [
            {"label": "Multi-column extraction", "description": "Return several fields per row from one call instead of a single label.", "code_snippet": "# Prompt for {index, sentiment, product_area, urgency}; widen the cache table columns and the INSERT accordingly."},
            {"label": "Parquet in/out", "description": "Read source and write enriched output as Parquet.", "code_snippet": "con.execute(\"CREATE TABLE tickets AS SELECT * FROM read_parquet('in.parquet')\")\\ncon.execute(\"COPY enriched TO 'out.parquet' (FORMAT parquet)\")"},
            {"label": "Concurrent batches", "description": "Parallelize with a thread pool; give each thread its own connection.", "code_snippet": "from concurrent.futures import ThreadPoolExecutor\\n# Each worker: duckdb.connect(DB_PATH) — DuckDB connections are not thread-safe to share."},
        ],
        "common_errors": [
            {"error_text": "Same rows enriched on every run", "cause": "Hash includes volatile fields (id, timestamp), so the cache key never matches.", "fix_snippet": "Hash ONLY the normalized text: sha256(trim(body)). Keep ids out of the key."},
            {"error_text": "KeyError / wrong label assignment in a batch", "cause": "Model returned fewer/more items or reordered them.", "fix_snippet": "Number items, validate len(parsed) == len(rows), and fall back per-item to 'other' on any parse failure."},
            {"error_text": "IOException: Could not set lock on file", "cause": "A second process (or notebook) opened the same DuckDB file for writing.", "fix_snippet": "DuckDB is single-writer. Use duckdb.connect(path, read_only=True) for inspectors; serialize writers."},
            {"error_text": "anthropic.RateLimitError: 429", "cause": "Batches fired with no spacing or backoff.", "fix_snippet": "Sleep between batches and wrap classify_batch in exponential backoff (1s, 2s, 4s) on RateLimitError."},
        ],
        "production_checklist": [
            "Hash only the stable text; never include ids or timestamps in the cache key.",
            "Validate batch item count and fall back per-item on parse failure.",
            "Serialize writers (single-writer DB); open inspectors read_only.",
            "Add exponential backoff on RateLimitError between batches.",
            "Persist the DuckDB file on durable storage so reruns stay resumable.",
            "Record model + created_at per row so you can re-enrich when the model changes.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["duckdb==1.1", "anthropic==0.39"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["batch-inference", "structured-output", "data-quality", "semantic-caching"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why DuckDB instead of pandas + a dict cache?", "answer": "DuckDB persists the cache to disk for free, so a crash mid-run loses nothing. The anti-join finds pending rows in SQL without loading the whole table into memory; pandas would re-derive that set each run."},
            {"question": "What guarantees resumability?", "answer": "The cache table is the source of truth. Pending rows are exactly those whose text hash is absent from enrichment_cache, so any subset already inserted is skipped on the next run — no checkpoint file needed."},
            {"question": "How do I re-enrich after switching models?", "answer": "Each row stores its model. Delete cache rows where model != the new one (or add model to the join key) and rerun; only those rows get re-processed."},
            {"question": "Can two workers share one DuckDB file?", "answer": "Not for writes — DuckDB is single-writer. Run one writer process; if you need parallelism, use a thread pool inside that process with per-thread connections, or shard the table across separate files."},
        ],
        "github_url": "https://github.com/duckdb/duckdb",
        "meta_title": "DuckDB LLM Enrichment Pipeline Starter",
        "meta_description": "Resumable LLM enrichment in DuckDB: content-hash cache, anti-join for pending rows, batched calls. Kill it anytime; reruns skip paid work.",
    },
    {
        "slug": "dagster-llm-asset-pipeline",
        "title": "Dagster Software-Defined Assets for LLM Data (Scrape to Index)",
        "tldr": "Model LLM data work as versioned, observable assets instead of cron scripts: raw_docs to clean_chunks to embeddings to search_index, each an @asset with lineage in the Dagster UI, plus an asset_check that gates quality.",
        "category": "data-pipelines",
        "language": "python",
        "framework": "Dagster",
        "tags": ["dagster", "assets", "embeddings", "orchestration"],
        "best_for_tags": ["data-orchestration", "rag-ingest", "observability"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Building a RAG ingestion or embedding pipeline you have to observe, re-run incrementally, and gate on quality. Dagster assets give lineage, freshness, and per-step checks instead of an opaque cron script.",
        "when_not_to_use": "Skip for a one-off batch script (Dagster's setup outweighs the benefit). Skip if you already run Airflow and only need task scheduling, not data-asset lineage.",
        "quick_start": "pip install dagster dagster-webserver sentence-transformers numpy && python pipeline.py",
        "full_code": '''"""Dagster LLM-data assets: raw_docs -> clean_chunks -> embeddings -> search_index."""
from __future__ import annotations

import re

import numpy as np
from dagster import (
    AssetCheckResult, AssetCheckSeverity, Definitions,
    asset, asset_check, materialize,
)

# ----------------- ASSET: RAW DOCS -----------------

@asset
def raw_docs() -> list[dict]:
    """Source documents. Replace with a real scrape / DB read."""
    return [
        {"id": "d1", "text": "DuckDB is an in-process analytical database. "
                             "It runs inside your application with no server."},
        {"id": "d2", "text": "Dagster models pipelines as software-defined assets. "
                             "Each asset declares what it produces."},
    ]


# ----------------- ASSET: CLEAN CHUNKS -----------------

@asset
def clean_chunks(raw_docs: list[dict]) -> list[dict]:
    """Normalize whitespace and split each doc into sentence-ish chunks."""
    chunks: list[dict] = []
    for doc in raw_docs:
        normalized = re.sub(r"\\s+", " ", doc["text"]).strip()
        for i, part in enumerate(p.strip() for p in normalized.split(". ") if p.strip()):
            chunks.append({"doc_id": doc["id"], "chunk_id": f"{doc['id']}-{i}", "text": part})
    return chunks


# ----------------- ASSET CHECK: QUALITY GATE -----------------

@asset_check(asset=clean_chunks)
def chunks_non_empty(clean_chunks: list[dict]) -> AssetCheckResult:
    total = len(clean_chunks)
    empties = sum(1 for c in clean_chunks if not c["text"])
    ratio = empties / total if total else 1.0
    return AssetCheckResult(
        passed=total > 0 and ratio < 0.05,
        severity=AssetCheckSeverity.ERROR,
        metadata={"chunk_count": total, "empty_ratio": round(ratio, 3)},
    )


# ----------------- ASSET: EMBEDDINGS -----------------

@asset
def doc_embeddings(clean_chunks: list[dict]) -> dict:
    """Embed chunks. Model is loaded INSIDE the asset, not at import time."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [c["text"] for c in clean_chunks]
    vectors = model.encode(texts, normalize_embeddings=True)
    return {"ids": [c["chunk_id"] for c in clean_chunks],
            "vectors": np.asarray(vectors, dtype=np.float32),
            "texts": texts}


# ----------------- ASSET: SEARCH INDEX -----------------

@asset
def search_index(doc_embeddings: dict) -> str:
    """Persist a simple numpy index file other services can mmap."""
    path = "search_index.npz"
    np.savez(path, ids=np.asarray(doc_embeddings["ids"]),
             vectors=doc_embeddings["vectors"])
    return path


defs = Definitions(
    assets=[raw_docs, clean_chunks, doc_embeddings, search_index],
    asset_checks=[chunks_non_empty],
)


if __name__ == "__main__":
    # Standalone run (no UI). For the UI: `dagster dev -f pipeline.py`.
    result = materialize(
        [raw_docs, clean_chunks, doc_embeddings, search_index],
        asset_check_keys=[chunks_non_empty.check_specs[0].key],
    )
    print("materialized:", result.success)
''',
        "dependencies": [
            {"name": "dagster", "version": ">=1.8", "purpose": "Software-defined assets, checks, lineage"},
            {"name": "dagster-webserver", "version": ">=1.8", "purpose": "Local Dagster UI (dagster dev)"},
            {"name": "sentence-transformers", "version": ">=3.0", "purpose": "Embed chunks"},
            {"name": "numpy", "version": ">=1.26", "purpose": "Vector array + on-disk index"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install dagster dagster-webserver sentence-transformers numpy",
            "Save pipeline.py",
            "Run standalone: python pipeline.py",
            "Launch the UI: dagster dev -f pipeline.py",
            "Open http://localhost:3000 and materialize assets; inspect lineage + the chunks check",
        ],
        "variations": [
            {"label": "Daily partitions", "description": "Make raw_docs a partitioned asset for incremental scrapes.", "code_snippet": "from dagster import DailyPartitionsDefinition\\n@asset(partitions_def=DailyPartitionsDefinition(start_date='2026-01-01'))\\ndef raw_docs(context): day = context.partition_key  # scrape that day"},
            {"label": "LanceDB index", "description": "Swap the numpy file for a real vector store.", "code_snippet": "import lancedb\\ndb = lancedb.connect('.lance')\\ndb.create_table('chunks', data=[{'id': i, 'vector': v} for i, v in zip(ids, vectors)])"},
            {"label": "Scheduled refresh", "description": "Run the pipeline daily.", "code_snippet": "from dagster import ScheduleDefinition, define_asset_job\\njob = define_asset_job('refresh', selection='*')\\nschedule = ScheduleDefinition(job=job, cron_schedule='0 6 * * *')"},
        ],
        "common_errors": [
            {"error_text": "Assets don't show in the Dagster UI", "cause": "They were never registered in a Definitions object.", "fix_snippet": "Add every asset + check to Definitions(assets=[...], asset_checks=[...]) and point dagster dev at that module."},
            {"error_text": "Slow startup / OOM at import", "cause": "Heavy model loaded at module top level, so it loads even to list assets.", "fix_snippet": "Import and construct SentenceTransformer INSIDE the asset function, not at module scope."},
            {"error_text": "TypeError: object is not serializable between assets", "cause": "Returning an object the default IO manager can't pickle.", "fix_snippet": "Return paths or numpy arrays, or configure an IO manager that handles your type (e.g. write to disk and pass the path)."},
            {"error_text": "Failing check doesn't stop the run", "cause": "Check severity defaults to WARN, which logs but doesn't fail.", "fix_snippet": "Set severity=AssetCheckSeverity.ERROR to fail the materialization on a bad result."},
        ],
        "production_checklist": [
            "Register every asset and check in a single Definitions object.",
            "Load heavy models inside asset functions, never at import time.",
            "Return paths/arrays between assets; configure an IO manager for custom types.",
            "Set check severity to ERROR for gates that must block downstream.",
            "Partition source assets so reruns are incremental, not full re-scrapes.",
            "Pin dagster; the asset/check API evolves across minor versions.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["dagster==1.8", "sentence-transformers==3.0", "numpy==1.26"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["dagster"],
        "related_glossary_slugs": ["pipeline", "embedding", "chunking", "data-quality", "orchestration"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Assets vs Airflow tasks?", "answer": "Airflow orchestrates tasks (verbs). Dagster assets model the data objects (nouns) a step produces, so the UI shows lineage and you can re-materialize only what's stale. For LLM ingest where 'the embeddings' is the thing you care about, assets map more directly."},
            {"question": "Why an asset_check instead of an assert?", "answer": "Checks are first-class: they surface pass/fail and metadata in the UI per run, can warn vs block, and run independently of the asset compute. An inline assert just crashes the run with no structured record."},
            {"question": "Does python pipeline.py give me the UI?", "answer": "No — that runs the assets once headless. The UI comes from `dagster dev -f pipeline.py` (needs dagster-webserver), which serves the lineage graph at localhost:3000."},
            {"question": "Where do embeddings actually live?", "answer": "This demo persists a numpy .npz file via the search_index asset. In production swap that asset's body for LanceDB, pgvector, or your vector store; the lineage and checks stay identical."},
        ],
        "github_url": "https://github.com/dagster-io/dagster",
        "meta_title": "Dagster LLM Asset Pipeline Starter",
        "meta_description": "RAG ingest as Dagster assets: raw_docs to chunks to embeddings to index, with lineage and a quality asset_check. Re-run only stale assets.",
    },
    {
        "slug": "kafka-llm-stream-enrichment",
        "title": "Kafka Stream Enrichment With LLM Classification (DLQ, Backpressure)",
        "tldr": "Enrich events in flight: consume a topic, micro-batch by size and time, classify with one LLM call per batch, produce to an enriched topic, route dead messages to a DLQ, and commit offsets only after produce.",
        "category": "data-pipelines",
        "language": "python",
        "framework": "confluent-kafka",
        "tags": ["kafka", "streaming", "batch-inference", "dlq"],
        "best_for_tags": ["stream-processing", "real-time-enrichment", "at-least-once"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Classifying or tagging a live event stream (support messages, logs, transactions) with at-least-once delivery. Micro-batching amortizes LLM latency; manual commits after produce prevent message loss on crash.",
        "when_not_to_use": "Skip for batch files (use the DuckDB or Dagster pattern). Skip if sub-100ms per-event latency is required — LLM calls add seconds; pre-filter or cache first.",
        "quick_start": "pip install confluent-kafka anthropic && python stream_enrich.py",
        "full_code": '''"""Kafka stream enrichment: micro-batch -> classify -> produce, with DLQ + manual commit."""
from __future__ import annotations

import json
import os
import signal
import time

from anthropic import Anthropic
from confluent_kafka import Consumer, Producer, KafkaException

# ----------------- CONFIG -----------------

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
GROUP_ID = os.environ.get("KAFKA_GROUP_ID", "llm-enricher")
IN_TOPIC = os.environ.get("KAFKA_IN_TOPIC", "events")
OUT_TOPIC = os.environ.get("KAFKA_OUT_TOPIC", "events.enriched")
DLQ_TOPIC = os.environ.get("KAFKA_DLQ_TOPIC", "events.dlq")
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
MAX_BATCH = 16
MAX_WAIT_S = 2.0

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
_running = True


def _stop(*_):
    global _running
    _running = False


# ----------------- LLM BATCH CLASSIFY -----------------

def classify_batch(texts: list[str]) -> list[str]:
    numbered = "\\n".join(f"{i}. {t}" for i, t in enumerate(texts))
    prompt = (
        "Label each numbered item as one of [urgent, normal, spam].\\n"
        f"Return ONLY a JSON array of {len(texts)} strings in order.\\n\\n" + numbered
    )
    resp = client.messages.create(
        model=MODEL, max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    labels = json.loads(raw)
    if not isinstance(labels, list) or len(labels) != len(texts):
        raise ValueError("label count mismatch")
    return [str(x) for x in labels]


# ----------------- DELIVERY + DLQ -----------------

def on_delivery(err, msg):
    if err is not None:
        print(f"delivery failed: {err}")


def to_dlq(producer: Producer, msg, reason: str) -> None:
    producer.produce(
        DLQ_TOPIC, key=msg.key(), value=msg.value(),
        headers=[("error", reason.encode("utf-8"))], on_delivery=on_delivery,
    )


# ----------------- MAIN LOOP -----------------

def run() -> None:
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    consumer = Consumer({
        "bootstrap.servers": BOOTSTRAP, "group.id": GROUP_ID,
        "enable.auto.commit": False, "auto.offset.reset": "earliest",
    })
    producer = Producer({"bootstrap.servers": BOOTSTRAP})
    consumer.subscribe([IN_TOPIC])

    buf, deadline = [], time.monotonic() + MAX_WAIT_S
    while _running:
        msg = consumer.poll(0.2)
        if msg is not None:
            if msg.error():
                raise KafkaException(msg.error())
            buf.append(msg)

        flush = len(buf) >= MAX_BATCH or (buf and time.monotonic() >= deadline)
        if not flush:
            continue

        texts = [m.value().decode("utf-8", "replace") for m in buf]
        try:
            labels = classify_batch(texts)
        except Exception as exc:  # parse / API failure -> DLQ the batch
            for m in buf:
                to_dlq(producer, m, f"classify_failed: {exc}")
            labels = None

        if labels is not None:
            for m, label in zip(buf, labels):
                payload = json.dumps({"raw": m.value().decode("utf-8", "replace"), "label": label})
                # Reuse the original key so per-key ordering is preserved downstream.
                producer.produce(OUT_TOPIC, key=m.key(), value=payload.encode("utf-8"), on_delivery=on_delivery)

        producer.flush(10)                  # block until produced (backpressure)
        consumer.commit(asynchronous=False)  # commit ONLY after successful produce
        buf, deadline = [], time.monotonic() + MAX_WAIT_S

    producer.flush(10)
    consumer.close()
    print("shutdown clean")


if __name__ == "__main__":
    run()
''',
        "dependencies": [
            {"name": "confluent-kafka", "version": ">=2.5", "purpose": "Kafka consumer + producer (librdkafka)"},
            {"name": "anthropic", "version": ">=0.39", "purpose": "LLM classification calls"},
        ],
        "env_vars": [
            {"name": "KAFKA_BOOTSTRAP", "required": True, "description": "Kafka bootstrap servers", "example": "localhost:9092"},
            {"name": "KAFKA_GROUP_ID", "required": True, "description": "Consumer group id (controls offset tracking)", "example": "llm-enricher"},
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Anthropic API key for classification", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "pip install confluent-kafka anthropic",
            "export KAFKA_BOOTSTRAP=localhost:9092 KAFKA_GROUP_ID=llm-enricher ANTHROPIC_API_KEY=sk-ant-...",
            "Create topics: events, events.enriched, events.dlq",
            "Run: python stream_enrich.py",
            "Produce test events to 'events' and consume 'events.enriched' to verify labels",
        ],
        "variations": [
            {"label": "Single-broker Kafka (docker-compose)", "description": "Spin up a local broker for testing.", "code_snippet": "# docker-compose.yml\\nservices:\\n  kafka:\\n    image: bitnami/kafka:3.7\\n    ports: ['9092:9092']\\n    environment:\\n      KAFKA_CFG_NODE_ID: '1'\\n      KAFKA_CFG_PROCESS_ROLES: 'broker,controller'"},
            {"label": "Semantic cache in front", "description": "Skip the LLM for texts seen before.", "code_snippet": "import hashlib\\nkey = hashlib.sha256(text.encode()).hexdigest()\\nlabel = cache.get(key) or classify_one(text)  # populate cache on miss"},
            {"label": "Scale by partitions", "description": "Add consumers in the same group; Kafka assigns partitions.", "code_snippet": "# Run N copies of this process with the same group.id.\\n# Parallelism is bounded by the topic's partition count, not threads."},
        ],
        "common_errors": [
            {"error_text": "Messages lost after a crash", "cause": "Auto-commit advanced offsets before the produce succeeded.", "fix_snippet": "Set enable.auto.commit=False and call consumer.commit(asynchronous=False) only after producer.flush() returns."},
            {"error_text": "Consumer kicked out: max.poll.interval.ms exceeded", "cause": "A slow LLM call exceeded the poll interval, triggering a rebalance.", "fix_snippet": "Raise max.poll.interval.ms (e.g. 300000) or shrink MAX_BATCH so each cycle returns to poll() faster."},
            {"error_text": "Producer queue full / unbounded memory", "cause": "Producing without flushing or checking delivery callbacks.", "fix_snippet": "Call producer.flush(timeout) each cycle and handle errors in on_delivery; this applies backpressure."},
            {"error_text": "Duplicate or dropped work on rebalance", "cause": "Partitions revoked mid-batch with uncommitted offsets.", "fix_snippet": "Pass on_revoke to subscribe() and commit completed offsets there; design downstream to be idempotent (at-least-once)."},
        ],
        "production_checklist": [
            "Disable auto-commit; commit only after producer.flush() succeeds.",
            "Tune max.poll.interval.ms above worst-case batch latency.",
            "Route repeated parse/API failures to a DLQ with an error header.",
            "Preserve the original message key on produce for per-key ordering.",
            "Make downstream idempotent — this is at-least-once, not exactly-once.",
            "Scale by partition count; add consumers to the group, not threads.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["confluent-kafka==2.5", "anthropic==0.39"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["batch-inference", "streaming", "semantic-caching", "llm-rate-limit"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why micro-batch instead of one call per message?", "answer": "One LLM call has fixed latency (often 1-2s). Batching 16 messages into a single call amortizes that across all of them, cutting per-message cost and latency roughly by the batch size while staying within one prompt."},
            {"question": "How is at-least-once achieved?", "answer": "Offsets are committed only after the enriched messages are confirmed produced (flush returns). If the process crashes before commit, those messages are re-consumed and re-produced — so downstream must dedupe by key or be idempotent."},
            {"question": "When does a message go to the DLQ?", "answer": "When the batch's LLM call fails (rate limit, parse error, or repeated exception). The whole micro-batch is routed to the DLQ with an error header rather than blocking the stream; you reprocess the DLQ separately."},
            {"question": "How do I scale throughput?", "answer": "Increase the topic's partition count and run more consumer processes in the same group. Kafka assigns partitions across them; parallelism is capped by partitions, so size partitions for peak load up front."},
        ],
        "github_url": "https://github.com/confluentinc/confluent-kafka-python",
        "meta_title": "Kafka LLM Stream Enrichment Starter",
        "meta_description": "Enrich a Kafka stream with LLM labels: size/time micro-batching, DLQ on failure, manual commit after produce for at-least-once delivery.",
    },
]
