"""RAG patterns — batch 3: parent-document, contextual-retrieval, hybrid+rerank, query-rewriting."""

RECORDS = [
    {
        "slug": "parent-document-retrieval",
        "title": "Parent-Document Retrieval (Precise Search, Full Context)",
        "tldr": "Embed SMALL chunks for precise retrieval, but return their PARENT documents for full context. Solves the 'chunk too small' vs 'chunk too large' tradeoff.",
        "category": "rag-patterns",
        "language": "python",
        "framework": "LangChain",
        "tags": ["rag", "parent-document", "chunking", "retrieval"],
        "best_for_tags": ["long-documents", "rag-quality", "context-sensitive-qa"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When chunks contain references that only make sense with parent context. Long technical docs, legal contracts, research papers. Embed precisely, return broadly.",
        "when_not_to_use": "Skip for short documents where chunk = doc. Skip when LLM context is tight and you can't afford to send parent docs.",
        "quick_start": "pip install langchain-community langchain-openai chromadb && python parent_retrieval.py",
        "full_code": '''"""Parent-document retrieval: embed small chunks, return parent docs.

Pattern: split a doc into PARENT chunks (1500 tokens). Then split each parent
into CHILD chunks (200 tokens). Embed children. At query time:
- Retrieve top-k children
- Return their parents (deduped)
"""
from __future__ import annotations

from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate


# ----------------- STORES -----------------

# Vector store: holds child-chunk embeddings.
vectorstore = Chroma(
    collection_name="parent_doc_demo",
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
    persist_directory="./chroma_db",
)

# Doc store: holds parent documents (key → full doc).
docstore = InMemoryStore()  # use Redis/Postgres in prod


# ----------------- SPLITTERS -----------------

parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)


# ----------------- RETRIEVER -----------------

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=docstore,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
    search_kwargs={"k": 4},  # top-k CHILDREN; parents will be deduped
)


# ----------------- INGEST -----------------

def ingest(docs_dir: str):
    """Load + index docs. Auto-splits into parents + children + embeds children."""
    loader = DirectoryLoader(docs_dir, glob="**/*.md")
    docs = loader.load()
    retriever.add_documents(docs)
    print(f"Indexed {len(docs)} docs → {vectorstore._collection.count()} child chunks")


# ----------------- QUERY -----------------

def ask(question: str) -> str:
    """Retrieve parents, synthesize answer."""
    parent_docs = retriever.invoke(question)
    print(f"Retrieved {len(parent_docs)} parent docs")

    context = "\\n\\n---\\n\\n".join(d.page_content for d in parent_docs)
    prompt = ChatPromptTemplate.from_template(
        "Answer using only the context. If unknown, say so.\\n\\n"
        "Context:\\n{context}\\n\\nQuestion: {q}\\n\\nAnswer:"
    )
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return llm.invoke(prompt.format_messages(context=context, q=question)).content


if __name__ == "__main__":
    ingest("./docs")
    print(ask("What's the rate limit for the /search endpoint?"))
''',
        "dependencies": [
            {"name": "langchain", "version": ">=0.3", "purpose": "ParentDocumentRetriever"},
            {"name": "langchain-chroma", "version": ">=0.1", "purpose": "Chroma vector store"},
            {"name": "langchain-openai", "version": ">=0.2", "purpose": "Embeddings + LLM"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI access", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install langchain langchain-chroma langchain-openai chromadb",
            "export OPENAI_API_KEY=sk-...",
            "mkdir docs && echo '# Test\\nThe /search endpoint allows 100 RPS.' > docs/api.md",
            "python parent_retrieval.py",
        ],
        "variations": [
            {"label": "Full-document return", "description": "Skip parent splitter; return WHOLE docs.", "code_snippet": "ParentDocumentRetriever(vectorstore=..., docstore=..., child_splitter=child_splitter)  # no parent_splitter → parent=whole doc"},
            {"label": "Redis-backed doc store", "description": "Production-grade persistence.", "code_snippet": "from langchain_community.storage import RedisStore\\ndocstore = RedisStore(client=redis.from_url('redis://localhost'))"},
            {"label": "MultiVector retriever (summaries)", "description": "Embed SUMMARIES, return full docs.", "code_snippet": "# Use MultiVectorRetriever; embed LLM-generated summaries per parent; better recall on synonym queries"},
        ],
        "common_errors": [
            {"error_text": "Children embeddings but no parent lookups", "cause": "Docstore not persistent; lost on restart.", "fix_snippet": "Use RedisStore or PostgreStore — InMemoryStore loses parents when process dies."},
            {"error_text": "Duplicate parents in results", "cause": "Same parent has multiple matching children.", "fix_snippet": "ParentDocumentRetriever auto-dedupes by parent ID. If seeing dupes, check that parent_splitter is set."},
            {"error_text": "Retrieval finds wrong chunk", "cause": "Child too small to capture meaning.", "fix_snippet": "Increase child_splitter chunk_size to 300-400. Smaller isn't always better."},
            {"error_text": "Context too long for LLM", "cause": "Parents too large.", "fix_snippet": "Reduce parent_splitter chunk_size from 1500 → 800. Or set k=2 instead of 4."},
        ],
        "production_checklist": [
            "Use persistent docstore (Redis/Postgres), not in-memory.",
            "Re-index when child or parent splitters change.",
            "Cache vectorstore.persist() after bulk ingest.",
            "Monitor: avg parent count returned, avg context length sent to LLM.",
            "Run eval set: parent-retrieval should beat plain chunk retrieval on context-sensitive queries.",
            "Set search_kwargs['k'] based on context budget, not arbitrary.",
        ],
        "tested_with": {
            "model_versions": ["text-embedding-3-small", "gpt-4o-mini"],
            "library_versions": ["langchain==0.3.10", "chromadb==0.5.20"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["langchain", "chroma"],
        "related_glossary_slugs": ["parent-document-retrieval", "chunking"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why not just embed parents directly?", "answer": "Large chunks dilute embedding precision — too many concepts in one vector. Small chunks embed precisely. Parent retrieval gives precision + context."},
            {"question": "How to size parent vs child?", "answer": "Child: 150-400 tokens (precise embedding). Parent: 800-2000 tokens (full context). Run an eval — your sweet spot depends on doc structure."},
            {"question": "Does this work with hierarchical docs (sections within sections)?", "answer": "Yes — use document metadata (section_id, chapter_id) for retrieval filters. Or use 'small-to-big' multi-level chunking with custom logic."},
            {"question": "Cost implications?", "answer": "More tokens to LLM (parents are bigger than chunks). Budget +30-50% input tokens vs plain retrieval. Quality usually pays for it."},
        ],
        "github_url": "https://github.com/langchain-ai/langchain",
        "meta_title": "Parent-Document Retrieval Starter — RAG Pattern",
        "meta_description": "Embed small child chunks for precision, return parent docs for context. ParentDocumentRetriever with Chroma + LangChain.",
    },
    {
        "slug": "anthropic-contextual-retrieval",
        "title": "Anthropic Contextual Retrieval (49% Better Retrieval)",
        "tldr": "Anthropic's pattern: prepend each chunk with a CONTEXT BLURB describing where it sits in the doc. Embed the contextualized chunk. 49% fewer retrieval failures vs plain chunks.",
        "category": "rag-patterns",
        "language": "python",
        "framework": "Anthropic / LangChain",
        "tags": ["contextual-retrieval", "anthropic", "rag-quality", "embeddings"],
        "best_for_tags": ["high-quality-rag", "long-documents", "technical-content"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "RAG over long technical docs where chunks lose meaning without context (e.g., 'this method requires X' — what's 'this method'?). Anthropic's research shows 49% improvement vs naive chunking.",
        "when_not_to_use": "Skip for short docs or self-contained chunks. Skip if cost of pre-processing is prohibitive (per-chunk LLM call to generate context).",
        "quick_start": "pip install anthropic chromadb && python contextual_retrieval.py",
        "full_code": '''"""Anthropic Contextual Retrieval.

For each chunk, generate a 1-2 sentence CONTEXT BLURB describing where the chunk
sits in the doc. Prepend the blurb to the chunk before embedding.

Source: https://www.anthropic.com/news/contextual-retrieval
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import anthropic
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction


CONTEXT_PROMPT = """Here is a document:

<document>
{doc}
</document>

Here is a chunk from this document:

<chunk>
{chunk}
</chunk>

Please write a SHORT 1-2 sentence context that situates this chunk within the
document. The context should help retrieval — what topic, what subsection,
what's being discussed. Answer ONLY with the context, nothing else."""


client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def generate_context(doc: str, chunk: str) -> str:
    """One LLM call per chunk to produce its context blurb. Use Haiku for cost."""
    resp = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=100,
        messages=[{"role": "user", "content": CONTEXT_PROMPT.format(doc=doc[:8000], chunk=chunk)}],
        # Prompt caching: the doc is repeated for every chunk → cache it.
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )
    return resp.content[0].text


def chunk_document(doc: str, size: int = 500) -> list[str]:
    """Simple word-based chunker; replace with your favorite."""
    words = doc.split()
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size)]


def contextualize_chunks(doc: str, chunks: list[str]) -> list[str]:
    """Generate context for each chunk in parallel; prepend to chunk text."""
    with ThreadPoolExecutor(max_workers=5) as pool:
        contexts = list(pool.map(lambda c: generate_context(doc, c), chunks))
    return [f"{ctx}\\n\\n{chunk}" for ctx, chunk in zip(contexts, chunks)]


# ----------------- INDEX -----------------

chroma = chromadb.PersistentClient(path="./contextual_chroma")
embed_fn = OpenAIEmbeddingFunction(api_key=os.environ["OPENAI_API_KEY"],
                                   model_name="text-embedding-3-small")
collection = chroma.get_or_create_collection("contextual_demo", embedding_function=embed_fn)


def index_document(doc_id: str, doc: str) -> None:
    chunks = chunk_document(doc)
    contextualized = contextualize_chunks(doc, chunks)
    collection.add(
        ids=[f"{doc_id}_{i}" for i in range(len(chunks))],
        documents=contextualized,  # contextualized text for embedding
        metadatas=[{"doc_id": doc_id, "original_chunk": orig} for orig in chunks],
    )


def retrieve(query: str, k: int = 5) -> list[dict]:
    results = collection.query(query_texts=[query], n_results=k)
    return [
        {"context_plus_chunk": d, "original": m["original_chunk"], "doc_id": m["doc_id"]}
        for d, m in zip(results["documents"][0], results["metadatas"][0])
    ]


if __name__ == "__main__":
    sample_doc = open("./long_doc.txt").read()
    index_document("doc1", sample_doc)
    for r in retrieve("how is rate limiting handled?", k=3):
        print(f"--- {r['doc_id']} ---")
        print(r["context_plus_chunk"][:200])
''',
        "dependencies": [
            {"name": "anthropic", "version": ">=0.36", "purpose": "Claude for context generation"},
            {"name": "chromadb", "version": ">=0.5", "purpose": "Vector store"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Claude access", "example": "sk-ant-..."},
            {"name": "OPENAI_API_KEY", "required": True, "description": "Embeddings", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install anthropic chromadb",
            "export ANTHROPIC_API_KEY=... OPENAI_API_KEY=...",
            "Get a long doc; save to ./long_doc.txt",
            "python contextual_retrieval.py",
        ],
        "variations": [
            {"label": "BM25 + contextual", "description": "Hybrid for even bigger lift.", "code_snippet": "# Anthropic's full pattern: contextual embeddings + contextual BM25 + reciprocal rank fusion. Adds another ~20pp on top of contextual embeddings alone."},
            {"label": "Voyager / cohere embeddings", "description": "Better embeddings than text-embedding-3.", "code_snippet": "# Voyager-3-large or cohere-embed-english-v3.0 outperform OpenAI on retrieval — pair with contextual prefix"},
            {"label": "Prompt-caching for full speed", "description": "Cache the doc across all chunks.", "code_snippet": "# Use Anthropic's prompt caching to cache the document content across N chunk calls. Cuts cost 90% on long docs."},
        ],
        "common_errors": [
            {"error_text": "Context cost > value", "cause": "Generating context for every tiny chunk is expensive.", "fix_snippet": "Use Haiku (cheap). Enable prompt-caching. Batch chunks. Only contextualize chunks above N tokens (skip tiny self-contained ones)."},
            {"error_text": "Context blurbs are too generic", "cause": "Prompt is too open-ended.", "fix_snippet": "Refine prompt: ask for the SPECIFIC topic/section/relationship. Provide examples in prompt of good vs bad context."},
            {"error_text": "Retrieval worse than plain chunks", "cause": "Doc is short OR self-contained chunks already.", "fix_snippet": "Pattern works on LONG technical docs. For short docs (<1k tokens), the overhead doesn't pay off."},
            {"error_text": "Embedding includes context but not original retrieved", "cause": "Storing only contextualized text.", "fix_snippet": "Embed contextualized; STORE both. Return ORIGINAL chunk to LLM (context blurb is for retrieval, not for context)."},
        ],
        "production_checklist": [
            "Use Haiku (or comparable cheap model) for context generation.",
            "Enable prompt-caching to cut cost on per-chunk calls.",
            "Run eval set: contextual should beat plain chunks AND hybrid.",
            "Re-index when document structure changes significantly.",
            "Log retrieval failures + iterate prompt for context generation.",
            "Cap context blurb to 1-2 sentences; longer dilutes embedding.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-5-haiku", "text-embedding-3-small"],
            "library_versions": ["anthropic==0.36", "chromadb==0.5.20"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["anthropic", "chroma"],
        "related_glossary_slugs": ["contextual-retrieval", "chunking"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How much does this cost?", "answer": "~$0.001 per chunk with Haiku + prompt caching. For a 1000-chunk corpus, that's $1 one-time pre-processing. Cheap relative to retrieval failure cost."},
            {"question": "How big is the quality lift?", "answer": "Anthropic reported 49% reduction in retrieval failures. In practice, 10-30% better recall@5 is typical on technical doc QA. Run YOUR eval to confirm."},
            {"question": "Why store ORIGINAL chunk?", "answer": "The context blurb helps retrieval but pollutes the context the LLM sees. Embed: contextualized. Return to LLM: original. Best of both."},
            {"question": "Combine with reranking?", "answer": "Yes — Anthropic recommends contextual embeddings + BM25 + RRF + Cohere reranker. Each layer adds ~10-20% lift; stack them all for production-grade retrieval."},
        ],
        "github_url": "https://github.com/anthropics/anthropic-cookbook",
        "meta_title": "Anthropic Contextual Retrieval Starter — 49% Better RAG",
        "meta_description": "Anthropic Contextual Retrieval: per-chunk context blurbs improve retrieval 49%. Haiku + prompt caching keeps cost low. Full implementation.",
    },
    {
        "slug": "hybrid-bm25-vector-rrf",
        "title": "Hybrid BM25 + Vector + RRF Reranking",
        "tldr": "Combine BM25 (keyword) and vector (semantic) retrieval, merge with Reciprocal Rank Fusion. 15-25% better recall than either alone for most workloads.",
        "category": "rag-patterns",
        "language": "python",
        "framework": "Custom",
        "tags": ["hybrid-search", "bm25", "rrf", "reranking"],
        "best_for_tags": ["recall-sensitive", "keyword-heavy-queries", "production-rag"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "RAG where queries mix keyword-search (acronyms, code names, exact phrases) with semantic (paraphrases). Vector-only misses keywords; BM25-only misses synonyms. RRF gets both.",
        "when_not_to_use": "Skip when queries are pure semantic (no proper nouns / codes). Skip if your vector DB already provides hybrid (Weaviate, Qdrant, Pinecone — use built-in).",
        "quick_start": "pip install rank-bm25 chromadb openai && python hybrid_rrf.py",
        "full_code": '''"""Hybrid BM25 + Vector + Reciprocal Rank Fusion.

For when you want recall: 'tell me about the SOC2 audit' should match both
documents mentioning SOC2 (keyword) and documents mentioning compliance
(semantic).
"""
from __future__ import annotations

import os
from collections import defaultdict

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from rank_bm25 import BM25Okapi


# ----------------- DATA STRUCTURES -----------------

# Toy corpus; replace with your real chunks.
DOCS: list[dict] = [
    {"id": "1", "text": "SOC2 audit covers data security controls."},
    {"id": "2", "text": "Vendor compliance review includes security standards."},
    {"id": "3", "text": "Rate limiting prevents API abuse via token buckets."},
    {"id": "4", "text": "Authentication uses OAuth 2.0 PKCE flow."},
]


# ----------------- BM25 INDEX -----------------

def tokenize(text: str) -> list[str]:
    return text.lower().split()


bm25 = BM25Okapi([tokenize(d["text"]) for d in DOCS])


def bm25_retrieve(query: str, k: int = 5) -> list[tuple[str, float]]:
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(zip(DOCS, scores), key=lambda x: x[1], reverse=True)[:k]
    return [(d["id"], s) for d, s in ranked]


# ----------------- VECTOR INDEX -----------------

chroma = chromadb.Client()
embed_fn = OpenAIEmbeddingFunction(api_key=os.environ["OPENAI_API_KEY"],
                                   model_name="text-embedding-3-small")
collection = chroma.get_or_create_collection("hybrid_demo", embedding_function=embed_fn)
collection.add(ids=[d["id"] for d in DOCS], documents=[d["text"] for d in DOCS])


def vector_retrieve(query: str, k: int = 5) -> list[tuple[str, float]]:
    res = collection.query(query_texts=[query], n_results=k)
    return list(zip(res["ids"][0], [1 - dist for dist in res["distances"][0]]))


# ----------------- RECIPROCAL RANK FUSION -----------------

def rrf(rankings: list[list[tuple[str, float]]], k: int = 60) -> list[tuple[str, float]]:
    """Combine multiple rankings via Reciprocal Rank Fusion.

    score(d) = sum over rankings of 1 / (k + rank_in_ranking(d))

    k=60 is the standard hyperparameter (Cormack et al. 2009).
    """
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, (doc_id, _) in enumerate(ranking):
            scores[doc_id] += 1 / (k + rank + 1)  # +1 because rank is 0-indexed
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# ----------------- HYBRID SEARCH -----------------

def hybrid_search(query: str, k: int = 5) -> list[tuple[str, float]]:
    bm25_results = bm25_retrieve(query, k=k * 2)  # over-retrieve, then merge
    vector_results = vector_retrieve(query, k=k * 2)
    return rrf([bm25_results, vector_results])[:k]


# ----------------- (OPTIONAL) RERANKER -----------------

def rerank_with_cohere(query: str, candidates: list[str]) -> list[tuple[str, float]]:
    """Final-pass reranker; Cohere offers a hosted reranker via API."""
    import cohere
    co = cohere.Client(os.environ["COHERE_API_KEY"])
    docs = [next(d["text"] for d in DOCS if d["id"] == cand_id) for cand_id in candidates]
    rerank_resp = co.rerank(query=query, documents=docs, model="rerank-english-v3.0")
    return [(candidates[r.index], r.relevance_score) for r in rerank_resp.results]


if __name__ == "__main__":
    query = "SOC2 compliance"
    print("BM25:", bm25_retrieve(query))
    print("Vector:", vector_retrieve(query))
    print("Hybrid (RRF):", hybrid_search(query))
''',
        "dependencies": [
            {"name": "rank-bm25", "version": ">=0.2", "purpose": "BM25 implementation"},
            {"name": "chromadb", "version": ">=0.5", "purpose": "Vector store"},
            {"name": "cohere", "version": ">=5.0", "purpose": "Optional reranker"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "Embeddings", "example": "sk-..."},
            {"name": "COHERE_API_KEY", "required": False, "description": "Reranker (optional)", "example": "..."},
        ],
        "setup_steps": [
            "pip install rank-bm25 chromadb 'openai>=1.40' cohere",
            "export OPENAI_API_KEY=sk-...",
            "python hybrid_rrf.py",
        ],
        "variations": [
            {"label": "Weighted RRF", "description": "Tilt toward keyword or semantic.", "code_snippet": "# Multiply RRF score by weight per source: bm25 * 0.7 + vector * 1.3 (favors semantic)"},
            {"label": "Built-in hybrid (Weaviate/Qdrant)", "description": "Skip custom RRF; vector DB does it.", "code_snippet": "# Weaviate: coll.query.hybrid(query=q, alpha=0.5) — alpha=0 BM25 only, 1 vector only"},
            {"label": "Three-way: BM25 + dense + colbert", "description": "Add late-interaction model.", "code_snippet": "# Add ColBERT retrieval as a third ranking; RRF over 3 lists. Adds ~5-10pp on hard queries"},
        ],
        "common_errors": [
            {"error_text": "Hybrid worse than vector alone", "cause": "BM25 corpus too small or queries pure semantic.", "fix_snippet": "BM25 needs lexical overlap. If queries are paraphrased far from doc wording, vector wins solo. Run eval."},
            {"error_text": "Memory blow-up with BM25", "cause": "rank-bm25 holds full corpus in memory.", "fix_snippet": "Use Elasticsearch / Tantivy / pyserini for scale. rank-bm25 for prototypes only."},
            {"error_text": "RRF score interpretation", "cause": "RRF scores aren't meaningful (just ordering).", "fix_snippet": "Don't show RRF scores to users. Use them only for ordering. For 'confidence', use a reranker score (Cohere) or LLM judge."},
            {"error_text": "Reranker too slow", "cause": "Calling Cohere/cross-encoder on all hybrid results.", "fix_snippet": "Hybrid top-50 → rerank → take top-10. Don't rerank everything."},
        ],
        "production_checklist": [
            "Use a real BM25 index (Elasticsearch / Tantivy) at scale, not rank-bm25.",
            "Tune RRF k (60 default; higher = more democratic across rankings).",
            "Add a reranker (Cohere / bge-reranker) for final top-10.",
            "Run eval set: measure recall@k for vector / BM25 / hybrid; pick highest.",
            "Cache BM25 index — it's expensive to rebuild on every restart.",
            "For built-in hybrid DBs (Weaviate, Qdrant, Pinecone), use theirs; don't roll your own.",
        ],
        "tested_with": {
            "model_versions": ["text-embedding-3-small", "rerank-english-v3.0"],
            "library_versions": ["rank-bm25==0.2.2", "chromadb==0.5.20"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["chroma", "cohere"],
        "related_glossary_slugs": ["bm25", "reciprocal-rank-fusion"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why RRF instead of weighted sum?", "answer": "RRF works across rankings with different scales (BM25 0-10s, cosine 0-1). Weighted sum requires score normalization. RRF is rank-based, scale-free, simple."},
            {"question": "k=60 in RRF — why?", "answer": "Empirical default from the original paper. Higher k = more democratic. Lower k = top results dominate. 60 works well for most workloads; tune if you have an eval set."},
            {"question": "Does reranking always help?", "answer": "For top-k where k>5, almost always. For k≤3, sometimes the marginal lift isn't worth the latency. Run eval."},
            {"question": "Hybrid for non-English?", "answer": "BM25 needs proper tokenization for non-Latin scripts. Use multilingual tokenizers (e.g., for CJK, use a segmenter first). Vector retrieval is more language-agnostic."},
        ],
        "github_url": "https://github.com/dorianbrown/rank_bm25",
        "meta_title": "Hybrid BM25 + Vector + RRF — RAG Pattern Starter",
        "meta_description": "Hybrid retrieval: BM25 + vector merged via Reciprocal Rank Fusion. 15-25% better recall than either alone. Optional Cohere reranker.",
    },
    {
        "slug": "query-rewriting-and-decomposition",
        "title": "Query Rewriting And Decomposition",
        "tldr": "Pre-retrieval LLM step: rewrite vague queries into 2-3 specific search-friendly queries, OR decompose complex multi-part queries into sub-questions. Helps retrieval hit harder.",
        "category": "rag-patterns",
        "language": "python",
        "framework": "OpenAI / Anthropic",
        "tags": ["query-rewriting", "decomposition", "pre-retrieval", "rag"],
        "best_for_tags": ["complex-questions", "vague-queries", "multi-hop"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When user queries are short, vague, or multi-part. Rewriting expands them into search-friendly forms; decomposition handles multi-hop (e.g., 'compare X and Y' → retrieve X, retrieve Y, merge).",
        "when_not_to_use": "Skip when queries are already well-formed (e.g., from a power-user search box). Skip when latency budget doesn't allow an extra LLM call.",
        "quick_start": "pip install openai && python rewrite_decompose.py",
        "full_code": '''"""Query rewriting + decomposition for RAG."""
from __future__ import annotations

import json
import os
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# ----------------- SCHEMAS -----------------

class RewrittenQueries(BaseModel):
    intent: str  # short interpretation of user intent
    queries: list[str]  # 2-3 specific search queries
    decomposed: bool  # whether the original was a multi-part question


# ----------------- REWRITER + DECOMPOSER -----------------

REWRITE_PROMPT = """You are a query rewriter for a retrieval system.

Given a USER QUERY, output JSON with:
- intent: a 1-sentence interpretation of what the user wants
- queries: a list of 2-3 SPECIFIC, RETRIEVAL-FRIENDLY queries that together cover the intent
- decomposed: true if the original query had multiple distinct sub-questions; false otherwise

Rules:
- If the user query is VAGUE ('how does it work?'), expand to specific concepts.
- If MULTI-PART ('compare A vs B'), DECOMPOSE into separate sub-queries.
- If WELL-FORMED already, return a single query (still in a list).
- Don't add information the user didn't imply.

USER QUERY: {query}
"""


def rewrite(user_query: str) -> RewrittenQueries:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You rewrite queries for retrieval. Output JSON only."},
            {"role": "user", "content": REWRITE_PROMPT.format(query=user_query)},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    data = json.loads(resp.choices[0].message.content)
    return RewrittenQueries(**data)


# ----------------- RETRIEVE + MERGE -----------------

def retrieve(query: str) -> list[str]:
    """Stub — replace with your vector store call."""
    # Return matching chunk IDs / texts
    return [f"chunk-for-'{query[:30]}...'"]


def multi_retrieve(rewritten: RewrittenQueries) -> list[str]:
    """Retrieve for each sub-query; dedupe; return combined chunks."""
    all_chunks: list[str] = []
    seen: set[str] = set()
    for q in rewritten.queries:
        for chunk in retrieve(q):
            if chunk not in seen:
                seen.add(chunk)
                all_chunks.append(chunk)
    return all_chunks


# ----------------- FULL PIPELINE -----------------

def rag_with_rewriting(user_query: str) -> tuple[RewrittenQueries, list[str]]:
    rewritten = rewrite(user_query)
    chunks = multi_retrieve(rewritten)
    return rewritten, chunks


if __name__ == "__main__":
    examples = [
        "how does the security stuff work?",
        "Compare our pricing plans for startups vs enterprise.",
        "What's the rate limit for the /search endpoint?",  # already well-formed
    ]
    for q in examples:
        print(f"\\n=== {q} ===")
        rewritten, chunks = rag_with_rewriting(q)
        print(f"Intent: {rewritten.intent}")
        print(f"Queries: {rewritten.queries}")
        print(f"Decomposed: {rewritten.decomposed}")
        print(f"Chunks: {chunks}")
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "Rewriter LLM"},
            {"name": "pydantic", "version": ">=2.0", "purpose": "Schema validation"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "API key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai pydantic",
            "export OPENAI_API_KEY=sk-...",
            "python rewrite_decompose.py",
            "Replace retrieve() stub with your real vector store",
        ],
        "variations": [
            {"label": "HyDE (Hypothetical Document Embeddings)", "description": "Generate a hypothetical answer; embed THAT.", "code_snippet": "# Ask LLM: 'What might an ideal answer look like?'. Embed the hypothetical answer; retrieve docs similar to it. Often beats query embedding alone."},
            {"label": "Step-back prompting", "description": "Ask abstract question first.", "code_snippet": "# 'What concepts does this question touch?' → answer the abstract question first; use that context to answer the specific question. Helpful for technical depth."},
            {"label": "Multi-query retrieval (LangChain)", "description": "Built-in implementation.", "code_snippet": "from langchain.retrievers.multi_query import MultiQueryRetriever\\nretriever = MultiQueryRetriever.from_llm(retriever=vectorstore.as_retriever(), llm=llm)"},
        ],
        "common_errors": [
            {"error_text": "Rewrites add wrong info", "cause": "LLM hallucinated context.", "fix_snippet": "Pin temperature=0; add to prompt: 'Don't invent information not implied by the original query.'"},
            {"error_text": "Too many sub-queries → cost", "cause": "Decomposition over-aggressive.", "fix_snippet": "Cap to 3 queries. Re-pin prompt: 'Use 1 query if well-formed; only decompose for multi-part questions.'"},
            {"error_text": "Latency bottleneck", "cause": "Rewriter LLM call before retrieval.", "fix_snippet": "Use gpt-4o-mini (faster). Cache by query hash. Or skip rewriting for queries above a length/clarity threshold."},
            {"error_text": "Decomposed queries return same chunks", "cause": "Original query already covered the space.", "fix_snippet": "Dedupe by chunk ID. If 100% overlap, rewriting was wasted — fall back to single-query retrieval next time."},
        ],
        "production_checklist": [
            "Use cheap fast model for rewriting (gpt-4o-mini / haiku).",
            "Cache rewrites by query hash; same query gets same rewrites.",
            "A/B test rewriting on/off on eval set.",
            "Cap sub-queries to 3 to control cost.",
            "Dedupe chunks across sub-queries.",
            "Add a quality gate: skip rewriting if query is already specific (>10 words + has proper noun).",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["openai==1.51", "pydantic==2.9"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["openai", "anthropic"],
        "related_glossary_slugs": ["query-rewriting", "hyde"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Worth the extra LLM call?", "answer": "Depends. For vague/short queries, yes — 10-20% better retrieval. For specific queries, often a wash. A/B test on your eval set."},
            {"question": "HyDE vs query rewriting?", "answer": "HyDE: generate hypothetical answer, embed THAT. Rewriting: produce search-friendly queries. HyDE often wins on technical domains; rewriting wins on broad search. Try both."},
            {"question": "What about translating queries?", "answer": "Useful for cross-lingual retrieval. Rewrite in the corpus language. E.g., user asks in Spanish but corpus is English — translate the query first."},
            {"question": "Cost in production?", "answer": "~$0.0001 per query with gpt-4o-mini. Cached by query hash, even cheaper. Tiny next to retrieval + generation cost downstream."},
        ],
        "github_url": "https://github.com/langchain-ai/langchain",
        "meta_title": "Query Rewriting + Decomposition — RAG Pattern Starter",
        "meta_description": "Pre-retrieval LLM step: rewrite vague queries into specific ones, decompose multi-part queries. Better retrieval, modest extra cost.",
    },
]
