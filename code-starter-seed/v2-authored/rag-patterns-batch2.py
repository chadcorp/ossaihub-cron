"""RAG pattern starters — batch 2: parent-child chunks, cross-encoder rerank, multi-query."""

RECORDS = [
    {
        "slug": "parent-child-chunks-rag",
        "title": "Parent-Child Chunk Strategy For RAG",
        "tldr": "Retrieve precise small chunks for matching; return their parent paragraph (or section) for context. Solves the recall-vs-context tension in RAG.",
        "category": "rag-patterns",
        "language": "python",
        "framework": "ChromaDB",
        "tags": ["rag", "chunking", "retrieval", "parent-child"],
        "best_for_tags": ["technical-docs", "long-documents", "rag-quality"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "When small chunks give better retrieval precision but the model needs more surrounding context to answer well. Parent-child stores both — search the small, return the large.",
        "when_not_to_use": "Skip for very short documents (chunks naturally fit). Skip when retrieval precision isn't the bottleneck — try plain chunking first.",
        "quick_start": "pip install chromadb && python parent_child.py ingest && python parent_child.py 'your question'",
        "full_code": '''"""Parent-child RAG: search small chunks, return parent paragraphs.

Structure:
  - Each document split into PARENT chunks (~1200 chars, paragraph-level)
  - Each parent split into CHILD chunks (~300 chars, sentence-level)
  - Index CHILDREN (vectors). On query: find best child → return its parent.

Why: search precision benefits from small chunks; LLM answer quality benefits
from more context. Parent-child gives you both.
"""
from __future__ import annotations

import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

PERSIST_DIR = "./pc_chroma"
client = chromadb.PersistentClient(path=PERSIST_DIR)
embedder = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")

# Two collections: children (searched), parents (returned)
children_col = client.get_or_create_collection("children", embedding_function=embedder)
parents_col = client.get_or_create_collection("parents", embedding_function=embedder)


def split_parents(text: str, *, max_chars: int = 1200) -> list[str]:
    """Paragraph-aware split into PARENTS."""
    parts = [p.strip() for p in text.split("\\n\\n") if p.strip()]
    parents = []
    cur = ""
    for p in parts:
        if len(cur) + len(p) + 2 > max_chars and cur:
            parents.append(cur)
            cur = p
        else:
            cur = cur + "\\n\\n" + p if cur else p
    if cur:
        parents.append(cur)
    return parents


def split_children(parent: str, *, max_chars: int = 300) -> list[str]:
    """Sentence-aware split into CHILDREN."""
    import re
    sentences = re.split(r"(?<=[.!?])\\s+", parent)
    chunks = []
    cur = ""
    for s in sentences:
        if len(cur) + len(s) > max_chars and cur:
            chunks.append(cur.strip())
            cur = s
        else:
            cur = cur + " " + s if cur else s
    if cur:
        chunks.append(cur.strip())
    return chunks


def ingest(source: str, text: str) -> None:
    parents = split_parents(text)
    parent_ids = []
    parent_docs = []
    parent_metas = []
    child_ids = []
    child_docs = []
    child_metas = []

    for pi, parent_text in enumerate(parents):
        parent_id = f"{source}::p{pi}"
        parent_ids.append(parent_id)
        parent_docs.append(parent_text)
        parent_metas.append({"source": source, "p_index": pi})

        for ci, child_text in enumerate(split_children(parent_text)):
            child_ids.append(f"{source}::p{pi}::c{ci}")
            child_docs.append(child_text)
            child_metas.append({"source": source, "parent_id": parent_id})

    parents_col.upsert(ids=parent_ids, documents=parent_docs, metadatas=parent_metas)
    children_col.upsert(ids=child_ids, documents=child_docs, metadatas=child_metas)
    print(f"  ingested {source}: {len(parents)} parents, {len(child_docs)} children")


def query(question: str, *, k_children: int = 8, k_parents: int = 3) -> list[dict]:
    """Search children; dedupe by parent; return top parents with context."""
    child_results = children_col.query(query_texts=[question], n_results=k_children)

    # Collect unique parents (keep best-scoring child for each parent)
    parent_seen: dict[str, dict] = {}
    for i, child_id in enumerate(child_results["ids"][0]):
        parent_id = child_results["metadatas"][0][i]["parent_id"]
        if parent_id not in parent_seen:
            parent_seen[parent_id] = {
                "parent_id": parent_id,
                "best_child_score": child_results["distances"][0][i],
                "matching_child_text": child_results["documents"][0][i],
            }

    # Fetch parent text for top N
    top_parent_ids = sorted(
        parent_seen.keys(), key=lambda pid: parent_seen[pid]["best_child_score"]
    )[:k_parents]

    parents = parents_col.get(ids=top_parent_ids)
    out = []
    for i, pid in enumerate(parents["ids"]):
        out.append({
            "parent_id": pid,
            "parent_text": parents["documents"][i],
            "matching_child": parent_seen[pid]["matching_child_text"],
            "score": parent_seen[pid]["best_child_score"],
            "source": parents["metadatas"][i].get("source"),
        })
    return out


if __name__ == "__main__":
    if sys.argv[1:2] == ["ingest"]:
        # Demo data
        ingest("rag-guide", Path("rag.md").read_text() if Path("rag.md").exists() else """
Reciprocal Rank Fusion combines multiple retriever outputs. Each document
gets a score of 1/(k+rank) summed across all retrievers. This is robust to
heterogeneous retrievers because it works on ranks, not raw scores.

HNSW and IVFFlat are two index types for pgvector. HNSW gives faster queries
but uses more RAM. IVFFlat uses less RAM but requires REINDEX after bulk
inserts. For most production workloads under 1M vectors, HNSW is the right
choice.

Chunking strategy matters more than chunk size. Paragraph-aware chunks
outperform fixed-size in retrieval precision because they respect natural
information boundaries.
""")
    else:
        question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How do I choose HNSW vs IVFFlat?"
        for hit in query(question):
            print(f"\\n[{hit['score']:.3f}] {hit['source']}")
            print(f"  matched: {hit['matching_child']}")
            print(f"  parent: {hit['parent_text'][:200]}...")
''',
        "dependencies": [
            {"name": "chromadb", "version": ">=0.5", "purpose": "Vector DB"},
            {"name": "sentence-transformers", "version": ">=3.0", "purpose": "Embeddings"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install chromadb sentence-transformers",
            "python parent_child.py ingest",
            "python parent_child.py 'your question'",
        ],
        "variations": [
            {
                "label": "Hierarchical (3+ levels)",
                "description": "Section → Paragraph → Sentence.",
                "code_snippet": "# Three collections: sentences (searched), paragraphs (returned for context), sections (returned for broader context if needed)",
            },
            {
                "label": "With summary as parent",
                "description": "Search sentences; return LLM-summarized parent for cleaner context.",
                "code_snippet": "# At ingest, generate parent summaries with LLM; store both summary + original. Return summary by default; original on user request.",
            },
            {
                "label": "Async ingestion",
                "description": "Parallel ingest for large corpora.",
                "code_snippet": "import asyncio\\n# Use AsyncOpenAI for embeddings; gather ingests across files",
            },
        ],
        "common_errors": [
            {
                "error_text": "Same parent returned multiple times",
                "cause": "Deduplication logic missing or buggy.",
                "fix_snippet": "Starter dedupes via parent_seen dict. Verify every child has unique parent_id metadata at ingest.",
            },
            {
                "error_text": "Child chunk doesn't match well",
                "cause": "Sentence-level split too fine; matches on common words.",
                "fix_snippet": "Increase child max_chars to ~500 — still smaller than parent but contains more context for matching.",
            },
            {
                "error_text": "Parent context too long",
                "cause": "max_chars on parents set too high.",
                "fix_snippet": "Parent max_chars 800-1500 is typical. Larger parents dilute token budget downstream.",
            },
        ],
        "production_checklist": [
            "Tune child:parent size ratio for your corpus (typically 1:4 to 1:6).",
            "Watch for parents that contain mostly non-content (table of contents, references).",
            "Cache common queries; parent-child adds overhead vs flat.",
            "Test on questions that span paragraph boundaries; sometimes you need adjacent parents too.",
            "Pin embedding model; switching invalidates both collections.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["chromadb==0.5.15", "sentence-transformers==3.2.1"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["chromadb"],
        "related_glossary_slugs": ["chunking", "rag", "retrieval"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why not just use larger chunks?",
                "answer": "Large chunks lower retrieval precision — matching on incidental words instead of the relevant fact. Parent-child preserves precision (small for matching) while delivering context (large for answer generation).",
            },
            {
                "question": "How is this different from LangChain ParentDocumentRetriever?",
                "answer": "Same idea, lower-dependency implementation. LangChain's version supports more retriever backends. This starter is direct ChromaDB; rewrite for Qdrant/Pinecone is mechanical.",
            },
            {
                "question": "What about overlapping parents?",
                "answer": "Standard parent-child uses non-overlapping parents (clean partition of doc). Adding overlap helps when answers span boundaries but doubles storage. Test for your corpus.",
            },
        ],
        "github_url": "",
        "meta_title": "Parent-Child Chunk Strategy for RAG — Starter",
        "meta_description": "Search small chunks for precision, return parent paragraphs for context. Solves the recall vs context tension in RAG.",
    },
    {
        "slug": "multi-query-rag-fusion",
        "title": "Multi-Query Generation + Result Fusion",
        "tldr": "Generate N rephrasings of the user's query, run each through retrieval, fuse the results with RRF. Recovers from poorly-worded queries and captures multi-aspect questions.",
        "category": "rag-patterns",
        "language": "python",
        "framework": "OpenAI + Qdrant",
        "tags": ["rag", "multi-query", "rrf", "query-expansion"],
        "best_for_tags": ["rag-quality", "ambiguous-queries", "production-rag"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "When user queries are short, ambiguous, or multi-part. Single-query retrieval often misses. Multi-query + fusion is a robust default for production RAG.",
        "when_not_to_use": "Skip for highly precise queries (looking up specific named entity). Skip if latency-sensitive — adds 1 LLM call + N retrievals.",
        "quick_start": "pip install openai qdrant-client fastembed && python multi_query.py 'your question'",
        "full_code": '''"""Multi-query RAG: LLM generates 3-4 rephrasings; each retrieves; results fused.

Process:
  1. User asks Q
  2. LLM generates {N} rephrasings of Q
  3. Each rephrasing retrieves top-K from vector DB
  4. Reciprocal Rank Fusion merges into single ranked list
  5. Top-N fused results passed to answer generator
"""
from __future__ import annotations

import json
import sys

from fastembed import TextEmbedding
from openai import OpenAI
from qdrant_client import QdrantClient

oai = OpenAI()
embedder = TextEmbedding("BAAI/bge-small-en-v1.5")
qdrant = QdrantClient(url="http://localhost:6333")

COLLECTION = "docs"


def generate_query_variations(query: str, *, n: int = 4) -> list[str]:
    """Use the LLM to generate N rephrasings."""
    prompt = f"""Generate {n} distinct rephrasings of the user's question. Each:
- Self-contained (no pronouns)
- Captures a different angle or aspect
- Useful for retrieval (not over-elaborated)

User question: {query}

Return JSON: {{"queries": ["q1", "q2", ...]}} """

    resp = oai.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,                # slight variety helps
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    data = json.loads(resp.choices[0].message.content)
    return [query] + data["queries"][:n]  # always include original


def retrieve_for_query(query: str, *, k: int = 8) -> list[dict]:
    """Vector search for one query."""
    qvec = list(embedder.embed([query]))[0]
    hits = qdrant.search(
        collection_name=COLLECTION,
        query_vector=qvec.tolist(),
        limit=k,
    )
    return [{"id": h.id, "score": h.score, "payload": h.payload} for h in hits]


def rrf_fuse(*hit_lists: list[dict], k: int = 10, rrf_k: int = 60) -> list[dict]:
    """Reciprocal Rank Fusion."""
    scores: dict = {}
    payloads: dict = {}
    for lst in hit_lists:
        for rank, hit in enumerate(lst):
            doc_id = hit["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (rrf_k + rank + 1)
            payloads[doc_id] = hit["payload"]
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
    return [{"id": i, "score": s, "payload": payloads[i]} for i, s in ranked]


def multi_query_retrieve(query: str, *, n_variations: int = 4, k_per: int = 8, k_final: int = 10) -> list[dict]:
    variations = generate_query_variations(query, n=n_variations)
    print(f"Variations: {variations}")

    all_hits = [retrieve_for_query(v, k=k_per) for v in variations]
    fused = rrf_fuse(*all_hits, k=k_final)
    return fused


def answer_with_context(query: str, hits: list[dict]) -> str:
    context = "\\n\\n".join(h["payload"].get("text", "") for h in hits)
    resp = oai.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": "Answer based only on the provided context. Cite sources."},
            {"role": "user", "content": f"Context:\\n{context}\\n\\nQuestion: {query}"},
        ],
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "How do I tune retrieval quality?"
    hits = multi_query_retrieve(question)
    print(f"\\n=== TOP {len(hits)} HITS ===")
    for h in hits[:5]:
        print(f"[{h['score']:.4f}] {h['payload'].get('text', '')[:100]}")
    print("\\n=== ANSWER ===")
    print(answer_with_context(question, hits))
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "Query generation + answer"},
            {"name": "qdrant-client", "version": ">=1.12", "purpose": "Vector retrieval"},
            {"name": "fastembed", "version": ">=0.4", "purpose": "Local embeddings"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "docker run -p 6333:6333 qdrant/qdrant",
            "pip install openai qdrant-client fastembed",
            "Ingest some docs into Qdrant first (see ingestion starter)",
            "python multi_query.py 'your question'",
        ],
        "variations": [
            {
                "label": "Step-back prompting",
                "description": "Generate ONE high-level rephrasing as additional retrieval.",
                "code_snippet": "step_back = generate_query_variations(query, n=1, prompt='Reformulate at a higher abstraction level')\\n# Add step_back to variations list before retrieval",
            },
            {
                "label": "HyDE",
                "description": "Generate a hypothetical answer and embed it.",
                "code_snippet": "hypothetical = oai.chat.completions.create(model='gpt-4o-mini', messages=[{'role': 'user', 'content': f'Write a 2-sentence answer to: {query}'}]).choices[0].message.content\\nhyde_hits = retrieve_for_query(hypothetical)",
            },
            {
                "label": "Cross-encoder rerank after fusion",
                "description": "Add a reranker pass for final quality.",
                "code_snippet": "from sentence_transformers import CrossEncoder\\nce = CrossEncoder('BAAI/bge-reranker-base')\\nfused = sorted(fused, key=lambda h: ce.predict([(query, h['payload']['text'])])[0], reverse=True)",
            },
        ],
        "common_errors": [
            {
                "error_text": "Variations are paraphrases (no real diversity)",
                "cause": "Temperature too low or prompt unclear.",
                "fix_snippet": "Increase temperature to 0.5-0.7 for query generation. Add: ‘each variation should capture a different aspect or angle, not just rewords.’",
            },
            {
                "error_text": "Slow latency",
                "cause": "Sequential retrievals + LLM call.",
                "fix_snippet": "Run retrievals in parallel: use asyncio.gather across variations. Saves N-1 round-trips.",
            },
            {
                "error_text": "Fused results worse than single-query",
                "cause": "Bad variations dilute the signal.",
                "fix_snippet": "Validate quality on eval set BEFORE deploying. Sometimes plain retrieval wins; multi-query helps on ambiguous queries specifically.",
            },
            {
                "error_text": "Variations include hallucinated keywords",
                "cause": "LLM imagines context.",
                "fix_snippet": "Tighten prompt: ‘don't add concepts not implied by the user's query.’ Use lower temperature.",
            },
        ],
        "production_checklist": [
            "Cache query variations per query — same input → same variations.",
            "Parallelize the N retrievals; latency adds up serial.",
            "Test on a held-out eval set; multi-query doesn't always win.",
            "Budget LLM cost — query expansion adds calls.",
            "Tune N variations: 2-4 is sweet spot; more dilutes.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["openai==1.51.0", "qdrant-client==1.12.0", "fastembed==0.4.1"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["qdrant", "fastembed"],
        "related_glossary_slugs": ["multi-query", "rrf", "hyde", "query-expansion"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Multi-query vs single-query?",
                "answer": "Multi-query: better on ambiguous/multi-aspect queries, ~30% latency penalty. Single: faster, fine for precise queries. Many production systems use multi-query as default with single-query fallback for hot-path latency.",
            },
            {
                "question": "How many variations?",
                "answer": "3-4 is the sweet spot in published evals. Beyond 5, returns diminish and dilution grows. Include the original query always.",
            },
            {
                "question": "Combine with cross-encoder?",
                "answer": "Yes — multi-query for recall, cross-encoder rerank for precision. Both at once is the strongest pattern (and most expensive).",
            },
        ],
        "github_url": "",
        "meta_title": "Multi-Query Generation + Result Fusion — Starter",
        "meta_description": "Generate N query rephrasings, retrieve each, fuse with RRF. Robust RAG retrieval for ambiguous and multi-aspect queries.",
    },
]
