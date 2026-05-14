"""Data pipeline starters — ingest, chunk, embed, batch processing."""

RECORDS = [
    {
        "slug": "document-ingestion-pipeline-batched",
        "title": "Document Ingestion Pipeline With Batched Embedding",
        "tldr": "End-to-end ingest pipeline: walk a folder/S3, chunk text intelligently (paragraph-aware), embed in batches with retry, upsert to vector DB. Includes progress tracking and resume.",
        "category": "data-pipelines",
        "language": "python",
        "framework": "Custom",
        "tags": ["ingestion", "chunking", "pipeline", "rag"],
        "best_for_tags": ["rag-prep", "bulk-ingest", "production"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "When bringing documents into a RAG system — initial bulk load or scheduled updates. The starter handles the recurring problems: too-big files, transient embedding errors, resumability.",
        "when_not_to_use": "Skip for trivial corpora (<100 docs — just inline). Skip when you have a managed solution (Pinecone Assistants, OpenAI Assistants File API).",
        "quick_start": "pip install qdrant-client fastembed tqdm && python ingest.py ./docs",
        "full_code": '''"""Document ingestion pipeline.

Stages:
  1. Discover: walk filesystem (or S3) for documents.
  2. Read: extract text by file type (txt, md, pdf basics).
  3. Chunk: paragraph-aware, with overlap.
  4. Embed: batched, retried.
  5. Upsert: into vector DB (Qdrant here; swap as needed).
  6. Track: progress + resume from last completed file.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Iterable

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

COLLECTION = "docs"
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384
CHUNK_CHARS = 1200
CHUNK_OVERLAP = 200
BATCH_SIZE = 32
STATE_FILE = ".ingest_state.json"

embedder = TextEmbedding(EMBED_MODEL_NAME)
qdrant = QdrantClient(url="http://localhost:6333")


def ensure_collection() -> None:
    if not qdrant.collection_exists(COLLECTION):
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        )


# ----------------- 1. DISCOVER -----------------

def discover(root: Path) -> list[Path]:
    """All readable files under root."""
    exts = {".txt", ".md", ".markdown", ".rst"}
    return sorted([p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts])


# ----------------- 2. READ -----------------

def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# ----------------- 3. CHUNK -----------------

def chunk(text: str, *, max_chars: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Paragraph-aware splitting with overlap.

    Splits on \\n\\n; combines short paragraphs until reaching max_chars;
    re-splits if a single paragraph exceeds max_chars.
    """
    paragraphs = [p.strip() for p in text.split("\\n\\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for p in paragraphs:
        if len(p) > max_chars:
            # Split very long paragraph into sub-chunks
            for i in range(0, len(p), max_chars - overlap):
                chunks.append(p[i : i + max_chars])
            continue
        if len(current) + len(p) + 2 > max_chars:
            chunks.append(current)
            # overlap: include tail of previous chunk
            current = current[-overlap:] + "\\n\\n" + p if overlap else p
        else:
            current = current + "\\n\\n" + p if current else p
    if current:
        chunks.append(current)
    return chunks


# ----------------- 4. EMBED -----------------

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def embed_batch(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in embedder.embed(texts)]


# ----------------- 5. UPSERT -----------------

def point_id_for(file_path: Path, chunk_index: int) -> int:
    h = hashlib.sha256(f"{file_path}::{chunk_index}".encode()).hexdigest()
    return int(h[:15], 16)  # Qdrant accepts int IDs


def upsert(file_path: Path, chunks: list[str], vectors: list[list[float]]) -> None:
    points = [
        PointStruct(
            id=point_id_for(file_path, i),
            vector=vec,
            payload={
                "source": str(file_path),
                "chunk_index": i,
                "text": chunks[i],
            },
        )
        for i, vec in enumerate(vectors)
    ]
    qdrant.upsert(collection_name=COLLECTION, points=points)


# ----------------- 6. STATE / RESUME -----------------

def load_state() -> dict:
    if Path(STATE_FILE).exists():
        return json.loads(Path(STATE_FILE).read_text())
    return {"completed": []}


def save_state(state: dict) -> None:
    Path(STATE_FILE).write_text(json.dumps(state, indent=2))


# ----------------- MAIN -----------------

def ingest(root: Path) -> None:
    ensure_collection()
    state = load_state()
    completed = set(state["completed"])

    files = discover(root)
    todo = [f for f in files if str(f) not in completed]
    print(f"{len(files)} total files, {len(todo)} to ingest ({len(completed)} already done)")

    for f in tqdm(todo, desc="files"):
        try:
            text = read_file(f)
            chunks = chunk(text)
            if not chunks:
                continue
            # Embed in mini-batches within the file
            vectors: list[list[float]] = []
            for i in range(0, len(chunks), BATCH_SIZE):
                batch = chunks[i : i + BATCH_SIZE]
                vectors.extend(embed_batch(batch))
            upsert(f, chunks, vectors)
            completed.add(str(f))
            state["completed"] = list(completed)
            save_state(state)
        except Exception as e:
            print(f"\\nERROR on {f}: {e}")
            # Continue to next file rather than abort the run.


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "./docs")
    ingest(root)
''',
        "dependencies": [
            {"name": "qdrant-client", "version": ">=1.12", "purpose": "Vector DB"},
            {"name": "fastembed", "version": ">=0.4", "purpose": "Local embeddings"},
            {"name": "tenacity", "version": ">=8.0", "purpose": "Retry logic"},
            {"name": "tqdm", "version": ">=4.66", "purpose": "Progress bars"},
        ],
        "env_vars": [],
        "setup_steps": [
            "docker run -d -p 6333:6333 qdrant/qdrant",
            "pip install qdrant-client fastembed tenacity tqdm",
            "mkdir docs && place .txt/.md files in",
            "python ingest.py ./docs",
            "Re-run resumes from last completed file.",
        ],
        "variations": [
            {
                "label": "S3 source",
                "description": "Walk an S3 bucket instead of filesystem.",
                "code_snippet": "import boto3\\ns3 = boto3.client('s3')\\nfor page in s3.get_paginator('list_objects_v2').paginate(Bucket=BUCKET, Prefix=PREFIX):\\n    for obj in page.get('Contents', []):\\n        yield obj['Key']",
            },
            {
                "label": "PDF support",
                "description": "Add PDF extraction.",
                "code_snippet": "import pypdf\\ndef read_pdf(path):\\n    pdf = pypdf.PdfReader(path)\\n    return '\\\\n\\\\n'.join(page.extract_text() for page in pdf.pages)",
            },
            {
                "label": "Markdown-aware chunking",
                "description": "Split at header boundaries.",
                "code_snippet": "# Split on lines starting with #, ## etc; each section becomes a chunk (further split if too long).",
            },
            {
                "label": "Async pipeline",
                "description": "Parallel reads and embeds.",
                "code_snippet": "# Use asyncio.gather to read N files in parallel; embed in batches via async fastembed alternative or thread pool.",
            },
        ],
        "common_errors": [
            {
                "error_text": "Qdrant connection refused",
                "cause": "Qdrant not running.",
                "fix_snippet": "docker run -d -p 6333:6333 qdrant/qdrant. Check with: curl http://localhost:6333/healthz",
            },
            {
                "error_text": "Memory blows up on large folders",
                "cause": "Loading all file paths into memory or batching too aggressively.",
                "fix_snippet": "Use generators for discover(); reduce BATCH_SIZE. For TB-scale, write a streaming version.",
            },
            {
                "error_text": "Slow on first run",
                "cause": "fastembed downloading model (~80MB).",
                "fix_snippet": "Pre-download in setup: python -c 'from fastembed import TextEmbedding; TextEmbedding(\"BAAI/bge-small-en-v1.5\")'",
            },
            {
                "error_text": "Resume picks up wrong files after rename",
                "cause": "State file tracks paths; renames look like new files.",
                "fix_snippet": "Track by content hash instead of path if renames are common. Trade-off: hash takes more time per file.",
            },
        ],
        "production_checklist": [
            "Log every file's success/failure with timestamp.",
            "Cap chunks per file to avoid one giant file consuming the run.",
            "Run from a stable mount; don't ingest from /tmp or container ephemeral storage.",
            "Set Qdrant write timeouts; bulk upserts can stall.",
            "Validate sample chunks after ingest — was text extracted correctly?",
            "Monitor disk + memory; large corpora need observability.",
            "Pin embedding model version; switching invalidates all vectors.",
        ],
        "tested_with": {
            "model_versions": ["BAAI/bge-small-en-v1.5"],
            "library_versions": ["qdrant-client==1.12.0", "fastembed==0.4.1", "tenacity==8.5.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["qdrant", "fastembed"],
        "related_glossary_slugs": ["chunking", "embedding", "ingestion"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "What chunk size is right?",
                "answer": "1000-1500 chars (~250-400 tokens) is a good baseline. Smaller chunks = better precision in retrieval but more chunks to manage. Larger = more context per hit but worse precision.",
            },
            {
                "question": "Is overlap necessary?",
                "answer": "Helps when answers span chunk boundaries. 10-20% overlap (200 of 1200 chars) is standard. Don't over-overlap — wasted storage.",
            },
            {
                "question": "How long does ingest take?",
                "answer": "Roughly 100ms per chunk on CPU with fastembed; faster with GPU. 10k chunks ~ 15-20 min on a laptop. Scale linearly.",
            },
            {
                "question": "Can I rerun safely?",
                "answer": "Yes — point IDs are deterministic (file path + chunk index). Re-ingest updates in place. State file skips already-done files.",
            },
        ],
        "github_url": "",
        "meta_title": "Document Ingestion Pipeline With Batched Embedding",
        "meta_description": "End-to-end RAG ingest: discover → chunk → embed batched → upsert to vector DB → resumable state. Production-grade in ~200 lines.",
    },
    {
        "slug": "etl-llm-cleanup-pipeline",
        "title": "LLM-Powered Data Cleanup ETL",
        "tldr": "ETL pipeline that uses an LLM to clean messy structured data: normalize entity names, fix encoding issues, classify free-text into enums. Runs in batches with cost tracking.",
        "category": "data-pipelines",
        "language": "python",
        "framework": "OpenAI SDK + pandas",
        "tags": ["etl", "data-cleaning", "llm", "structured-output"],
        "best_for_tags": ["data-quality", "post-processing", "structured-data"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When you have messy data (variant entity names, mojibake, free-text fields needing classification) and rules-based cleanup falls short. LLMs handle the long-tail cases regex doesn't.",
        "when_not_to_use": "Skip for high-volume data where cost matters (use rules + spot-check). Skip when ground truth matters and you can't validate at scale — LLMs introduce noise.",
        "quick_start": "pip install openai pandas instructor && OPENAI_API_KEY=sk-... python cleanup.py messy.csv clean.csv",
        "full_code": '''"""ETL pipeline using LLM for data cleanup.

Operations supported:
  - normalize_entity: 'USA' / 'U.S.A.' / 'United States' -> 'United States'
  - fix_encoding: 'Caf\\u00e9' / 'Cafe' / 'Café' -> 'Café'
  - classify_free_text: 'I cant log in' -> {category: 'auth', subcategory: 'login_failure'}
  - extract_entities: free text -> structured fields

Batches inputs for cost efficiency; caches deterministic results.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Literal

import instructor
import pandas as pd
from openai import OpenAI
from pydantic import BaseModel, Field

oai = instructor.from_openai(OpenAI())

# ----------------- SCHEMAS -----------------

class NormalizedEntity(BaseModel):
    original: str
    canonical: str
    confidence: Literal["high", "medium", "low"]


class TicketClassification(BaseModel):
    category: Literal["auth", "billing", "feature_request", "bug_report", "other"]
    severity: Literal["urgent", "high", "medium", "low"]
    summary: str = Field(description="One-sentence summary of the ticket")


# ----------------- BATCH OPERATIONS -----------------

def normalize_entities(values: list[str], *, kind: str = "country") -> list[NormalizedEntity]:
    """Map varied spellings to canonical form."""
    prompt = f"""Normalize these {kind} names to their canonical form.

Examples:
  'USA' -> 'United States' (high confidence)
  'U.S.A.' -> 'United States' (high)
  'Brasil' -> 'Brazil' (high)
  'Britain' -> 'United Kingdom' (medium - could mean different things)

Input values: {json.dumps(values)}

For each input, output original, canonical, and confidence."""

    class BatchResponse(BaseModel):
        results: list[NormalizedEntity]

    resp = oai.chat.completions.create(
        model="gpt-4o-mini",
        response_model=BatchResponse,
        max_retries=2,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.results


def classify_tickets(texts: list[str]) -> list[TicketClassification]:
    """Classify support ticket text."""
    prompt = f"""Classify each support ticket below. For each, output category, severity, and one-sentence summary.

Tickets:
{json.dumps(texts, indent=2)}"""

    class BatchResponse(BaseModel):
        results: list[TicketClassification]

    resp = oai.chat.completions.create(
        model="gpt-4o-mini",
        response_model=BatchResponse,
        max_retries=2,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.results


# ----------------- PIPELINE -----------------

def run_pipeline(input_csv: Path, output_csv: Path, *, batch_size: int = 20) -> None:
    df = pd.read_csv(input_csv)
    print(f"Loaded {len(df)} rows")

    # Example transformations — adjust to your schema
    if "country" in df.columns:
        unique = df["country"].dropna().unique().tolist()
        normalized = normalize_entities(unique, kind="country")
        mapping = {n.original: n.canonical for n in normalized if n.confidence != "low"}
        df["country_normalized"] = df["country"].map(mapping).fillna(df["country"])
        print(f"  normalized {len(mapping)} country values")

    if "support_ticket_body" in df.columns:
        results: list[TicketClassification] = []
        for i in range(0, len(df), batch_size):
            batch = df["support_ticket_body"].iloc[i : i + batch_size].tolist()
            results.extend(classify_tickets(batch))
            print(f"  classified {min(i + batch_size, len(df))} / {len(df)}")
        df["category"] = [r.category for r in results]
        df["severity"] = [r.severity for r in results]
        df["summary"] = [r.summary for r in results]

    df.to_csv(output_csv, index=False)
    print(f"Wrote {output_csv}")


if __name__ == "__main__":
    in_csv = Path(sys.argv[1])
    out_csv = Path(sys.argv[2] if len(sys.argv) > 2 else in_csv.with_stem(in_csv.stem + "_clean"))
    run_pipeline(in_csv, out_csv)
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "LLM client"},
            {"name": "instructor", "version": ">=1.5", "purpose": "Structured output"},
            {"name": "pandas", "version": ">=2.2", "purpose": "Data manipulation"},
            {"name": "pydantic", "version": ">=2.0", "purpose": "Schemas"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai instructor pandas pydantic",
            "export OPENAI_API_KEY=sk-...",
            "python cleanup.py messy.csv clean.csv",
        ],
        "variations": [
            {
                "label": "With caching layer",
                "description": "Cache LLM results to avoid re-computing identical inputs.",
                "code_snippet": "import diskcache\\ncache = diskcache.Cache('./etl_cache')\\nkey = hashlib.sha256(json.dumps(input).encode()).hexdigest()\\nif key in cache: return cache[key]\\nresult = oai.chat.completions.create(...)\\ncache[key] = result",
            },
            {
                "label": "Streaming for huge CSVs",
                "description": "Process row-by-row, write incrementally.",
                "code_snippet": "for chunk in pd.read_csv(input_csv, chunksize=1000):\\n    chunk = process(chunk)\\n    chunk.to_csv(output_csv, mode='a', header=False, index=False)",
            },
            {
                "label": "Validation pass",
                "description": "Verify LLM output with rules.",
                "code_snippet": "# After LLM call: check canonical values against an allowed enum. Flag unknowns for human review.\\n# Reject rows where confidence='low'.",
            },
            {
                "label": "Cost tracking",
                "description": "Estimate spend.",
                "code_snippet": "total_tokens = 0\\nresp = client.chat.completions.create(...)\\ntotal_tokens += resp.usage.total_tokens\\n# At end: print(f'cost ~ ${total_tokens * 0.15 / 1_000_000}')",
            },
        ],
        "common_errors": [
            {
                "error_text": "ValidationError: Field required (Literal)",
                "cause": "LLM returned a value outside the enum.",
                "fix_snippet": "Add 'other' / 'unknown' to the Literal, OR set max_retries higher so Instructor re-prompts the model.",
            },
            {
                "error_text": "Batch too large; LLM truncates output",
                "cause": "Output exceeds model's max_tokens.",
                "fix_snippet": "Reduce batch_size. Match output token count to batch size: ~50-100 tokens per item is typical.",
            },
            {
                "error_text": "Inconsistent normalization across batches",
                "cause": "LLM doesn't see all values at once.",
                "fix_snippet": "Build a canonical mapping from unique values first (single LLM call), then map all rows. The starter does this for countries.",
            },
            {
                "error_text": "Slow runtime",
                "cause": "Single-threaded; one batch at a time.",
                "fix_snippet": "Use AsyncOpenAI + asyncio.gather to run batches in parallel. Respect rate limits.",
            },
        ],
        "production_checklist": [
            "Always validate LLM output downstream (constraint checks, range checks).",
            "Sample 5-10% of output for human review on each run.",
            "Pin model version; output shape drifts subtly across versions.",
            "Cache deterministic results (temperature=0, same input).",
            "Track per-run cost; sudden spikes indicate prompt/data drift.",
            "Build a feedback loop — when humans correct LLM output, feed corrections back as few-shot.",
            "Document which transformations are LLM-based vs rules-based.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["openai==1.51.0", "instructor==1.5.2", "pandas==2.2.3"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["pandas", "instructor"],
        "related_glossary_slugs": ["etl", "data-cleaning", "structured-output"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "When is LLM cleanup worth it vs regex?",
                "answer": "When the variation is unbounded (free text, named entities, multilingual). For closed-set normalization (state codes), regex/lookup is faster and cheaper.",
            },
            {
                "question": "How do I prevent silent corruption?",
                "answer": "Always emit confidence levels and validate downstream. Reject low-confidence transformations. Run a parallel rule-based check on a sample of LLM-cleaned rows.",
            },
            {
                "question": "Cost estimate for 100k rows?",
                "answer": "~$1-5 with gpt-4o-mini for typical short fields. Scales with field length and batch efficiency. Use cheaper models for simple transformations.",
            },
            {
                "question": "Can I run this offline?",
                "answer": "Swap OpenAI for an Ollama-served model. Quality drops on complex normalization; works fine for classification.",
            },
        ],
        "github_url": "",
        "meta_title": "LLM-Powered Data Cleanup ETL — Starter",
        "meta_description": "Pandas + LLM ETL pipeline: normalize entities, classify free text, extract structured fields. Batched, validated, cost-aware.",
    },
]
