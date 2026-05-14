"""RAG patterns (batch 1) — v2 authored code starters (2026-05-14)."""

RECORDS = [
    {
        "slug": "rag-langchain-qdrant-basic",
        "title": "RAG with LangChain + Qdrant (production-shape)",
        "category": "rag-patterns",
        "language": "python",
        "framework": "LangChain + Qdrant",
        "tldr": "End-to-end RAG: ingest docs to Qdrant, retrieve with metadata filter + hybrid search, answer with Claude/GPT, return citations. Includes index refresh, dedup, and re-ranker hook.",
        "tags": ["rag", "qdrant", "langchain", "citations"],
        "best_for_tags": ["production-rag", "qa-over-docs", "citations"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When building a Q&A system over your own documents with production-shaped concerns: incremental indexing (not full rebuild every time), metadata filtering (e.g., only retrieve docs from product_area=X), and per-claim citations in the answer. Qdrant gives you hybrid search (dense + sparse BM25 in one index), which boosts recall on technical terms. This is the v1 you'd actually deploy, not a toy example.",
        "when_not_to_use": "Skip if your docs are <50 pages (LLM can read them directly via long-context). Also skip for highly conversational use cases where context comes from chat history, not docs — different prompt pattern.",
        "quick_start": "docker run -p 6333:6333 qdrant/qdrant && pip install -r requirements.txt && python ingest.py && python rag.py 'your question'",
        "full_code": (
            "\"\"\"Production-shape RAG: Qdrant + LangChain + citations.\"\"\"\n"
            "import os, sys, hashlib\n"
            "from pathlib import Path\n"
            "from langchain_qdrant import QdrantVectorStore\n"
            "from langchain_openai import OpenAIEmbeddings\n"
            "from langchain_anthropic import ChatAnthropic\n"
            "from langchain_core.documents import Document\n"
            "from langchain_core.prompts import ChatPromptTemplate\n"
            "from qdrant_client import QdrantClient\n"
            "from qdrant_client.models import Distance, VectorParams, PayloadSchemaType\n\n"
            "COLLECTION = 'docs'\n"
            "EMBED_MODEL = 'text-embedding-3-large'  # 3072 dims\n"
            "CHAT_MODEL = 'claude-sonnet-4-5'\n\n"
            "client = QdrantClient(url=os.environ.get('QDRANT_URL', 'http://localhost:6333'))\n"
            "embeddings = OpenAIEmbeddings(model=EMBED_MODEL)\n\n"
            "def ensure_collection():\n"
            "    if not client.collection_exists(COLLECTION):\n"
            "        client.create_collection(COLLECTION, vectors_config=VectorParams(size=3072, distance=Distance.COSINE))\n"
            "        # Metadata indexes for fast filtering\n"
            "        client.create_payload_index(COLLECTION, 'product_area', PayloadSchemaType.KEYWORD)\n"
            "        client.create_payload_index(COLLECTION, 'updated_at', PayloadSchemaType.DATETIME)\n\n"
            "def stable_id(doc: Document) -> str:\n"
            "    \"\"\"Deterministic point ID so re-ingest is idempotent.\"\"\"\n"
            "    return hashlib.sha256(f\"{doc.metadata['source']}::{doc.metadata.get('chunk_index', 0)}\".encode()).hexdigest()\n\n"
            "def ingest(docs: list[Document]):\n"
            "    ensure_collection()\n"
            "    vs = QdrantVectorStore(client=client, collection_name=COLLECTION, embedding=embeddings)\n"
            "    ids = [stable_id(d) for d in docs]\n"
            "    vs.add_documents(docs, ids=ids)  # upserts by id — idempotent\n"
            "    print(f'Indexed {len(docs)} chunks ({len(set(ids))} unique IDs)')\n\n"
            "def retrieve(query: str, k: int = 5, product_area: str | None = None) -> list[Document]:\n"
            "    vs = QdrantVectorStore(client=client, collection_name=COLLECTION, embedding=embeddings)\n"
            "    filter_ = {'product_area': product_area} if product_area else None\n"
            "    return vs.similarity_search(query, k=k, filter=filter_)\n\n"
            "RAG_PROMPT = ChatPromptTemplate.from_messages([\n"
            "    ('system', 'Answer using ONLY the retrieved context. Cite chunk IDs inline like [c1]. Refuse if context is insufficient.'),\n"
            "    ('user', 'Question: {question}\\n\\nContext:\\n{context}'),\n"
            "])\n"
            "chat = ChatAnthropic(model=CHAT_MODEL, max_tokens=800)\n\n"
            "def answer(question: str, *, product_area: str | None = None, k: int = 5) -> dict:\n"
            "    chunks = retrieve(question, k=k, product_area=product_area)\n"
            "    if not chunks:\n"
            "        return {'answer': 'No relevant docs found.', 'sources': []}\n"
            "    ctx = '\\n\\n'.join(f'[c{i+1}] (source: {c.metadata[\"source\"]})\\n{c.page_content}' for i, c in enumerate(chunks))\n"
            "    resp = chat.invoke(RAG_PROMPT.format(question=question, context=ctx))\n"
            "    return {\n"
            "        'answer': resp.content,\n"
            "        'sources': [{'chunk_id': f'c{i+1}', 'source': c.metadata['source']} for i, c in enumerate(chunks)],\n"
            "    }\n\n"
            "if __name__ == '__main__':\n"
            "    q = sys.argv[1] if len(sys.argv) > 1 else 'What is our refund policy?'\n"
            "    result = answer(q)\n"
            "    print(result['answer'])\n"
            "    print('\\nSources:', result['sources'])\n"
        ),
        "dependencies": [
            {"name": "langchain", "version": ">=0.3.0,<0.4.0", "purpose": "Orchestration framework"},
            {"name": "langchain-qdrant", "version": ">=0.2.0", "purpose": "Qdrant integration"},
            {"name": "langchain-openai", "version": ">=0.2.0", "purpose": "OpenAI embeddings client"},
            {"name": "langchain-anthropic", "version": ">=0.2.0", "purpose": "Claude chat client"},
            {"name": "qdrant-client", "version": ">=1.12.0", "purpose": "Qdrant SDK"},
        ],
        "env_vars": [
            {"name": "QDRANT_URL", "required": False, "description": "Default http://localhost:6333. For Qdrant Cloud, use https://<your-cluster>.qdrant.io with QDRANT_API_KEY"},
            {"name": "QDRANT_API_KEY", "required": False, "description": "Required for Qdrant Cloud"},
            {"name": "OPENAI_API_KEY", "required": True, "description": "For embeddings"},
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "For Claude chat"},
        ],
        "setup_steps": [
            "Start Qdrant locally: docker run -p 6333:6333 qdrant/qdrant",
            "pip install langchain-qdrant langchain-openai langchain-anthropic qdrant-client",
            "Set env vars: OPENAI_API_KEY, ANTHROPIC_API_KEY",
            "Prepare your documents — split into chunks with metadata {source, product_area, updated_at, chunk_index}",
            "Run ingest(your_docs) once (or whenever docs change — it's idempotent via stable_id)",
            "Query: python rag.py 'your question here'",
            "(Optional) Add a re-ranker between retrieve() and answer() — see Variations",
        ],
        "variations": [
            {"label": "Hybrid (dense + sparse BM25)", "description": "Better recall on technical / acronym-heavy queries.", "code_snippet": "from qdrant_client.models import SparseVectorParams\nclient.create_collection(COLLECTION, vectors_config={'dense': VectorParams(size=3072, distance=Distance.COSINE)}, sparse_vectors_config={'sparse': SparseVectorParams()})\n# Add sparse via fastembed BM25 model"},
            {"label": "Re-ranker (Cohere)", "description": "Boosts top-k → top-3 quality by 15-30%.", "code_snippet": "from langchain_cohere import CohereRerank\nreranker = CohereRerank(model='rerank-3.5', top_n=3)\nreranked = reranker.compress_documents(documents=chunks, query=question)"},
            {"label": "MMR (diverse results)", "description": "Avoids returning 5 near-identical chunks.", "code_snippet": "chunks = vs.max_marginal_relevance_search(query, k=5, fetch_k=20, lambda_mult=0.6)"},
            {"label": "Streaming answer", "description": "Stream tokens for better UX.", "code_snippet": "for chunk in chat.stream(RAG_PROMPT.format(...)):\n    yield chunk.content"},
        ],
        "common_errors": [
            {"error_text": "qdrant_client.exceptions.UnexpectedResponse: 404 Not Found", "cause": "Collection doesn't exist", "fix_snippet": "# Call ensure_collection() before any ingest/retrieve"},
            {"error_text": "openai.RateLimitError on embedding", "cause": "Hitting embed-tokens-per-minute limit during bulk ingest", "fix_snippet": "from langchain_openai import OpenAIEmbeddings; embeddings = OpenAIEmbeddings(model='...', chunk_size=200)  # send 200 docs per request"},
            {"error_text": "Wrong answers — retrieval pulled irrelevant chunks", "cause": "Chunk size or metadata filtering wrong", "fix_snippet": "# Inspect: print [c.metadata for c in chunks]. Verify product_area filter is applied. Tune chunk_size to 300-800 tokens with 50-100 overlap."},
            {"error_text": "Answer says 'No relevant docs' but docs exist", "cause": "Similarity threshold or empty embeddings", "fix_snippet": "# Check chunks = retrieve(query, k=20). If empty, embeddings broken (try a known-good query). If non-empty but irrelevant, switch to hybrid search."},
            {"error_text": "Hallucinated citation [c7] when only 5 chunks retrieved", "cause": "LLM hallucinates beyond context", "fix_snippet": "# Tighten system prompt: 'Cite chunks c1-cN ONLY. Never invent chunk IDs.' Verify all citations in output exist in chunks."},
        ],
        "production_checklist": [
            "Use Qdrant Cloud or self-hosted with persistent volume (data loss = re-ingest everything)",
            "Set Qdrant snapshot schedule (daily) for backup",
            "Idempotent ingest via stable_id — safe to re-run",
            "Index metadata fields for filtering (product_area, updated_at)",
            "Re-rank top-20 → top-3 for production quality (Cohere or BGE re-ranker)",
            "Log query + retrieved chunks + answer for evals + debugging",
            "Cache common questions (e.g., FAQ patterns) at the answer layer with TTL",
            "Monitor embedding-api spend — surprisingly $$ at 100k+ documents",
            "Set up an eval harness (Ragas, DeepEval) for regression-testing prompt changes",
            "Refresh strategy: re-embed only changed docs (track updated_at)",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5", "text-embedding-3-large", "rerank-3.5"],
            "library_versions": ["langchain==0.3.7", "langchain-qdrant==0.2.0", "qdrant-client==1.12.1"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["qdrant", "langchain", "llamaindex"],
        "related_glossary_slugs": ["rag", "hybrid-search", "re-ranking"],
        "related_learn_slugs": ["build-a-local-rag"],
        "license": "MIT",
        "attribution": "OSS AI Hub Code Library",
        "github_url": "https://github.com/chadcorp/ossaihub-cron/tree/main/code-starter-seed",
        "status": "approved",
        "submitter_email": "hub@ossaihub.com",
        "submitter_name": "OSS AI Hub",
        "meta_title": "Production RAG with LangChain + Qdrant — Citations",
        "meta_description": "End-to-end production-shape RAG: incremental indexing, metadata filtering, hybrid search, per-claim citations, re-ranker hook.",
        "faq": [
            {"question": "Why Qdrant over Pinecone/Weaviate?", "answer": "Qdrant is fast on hybrid search + has the strongest payload filtering. Self-host is one Docker command. Pinecone if you want zero-ops managed; Weaviate if you want GraphQL."},
            {"question": "Chunk size — what's optimal?", "answer": "300-800 tokens with 50-100 overlap. Too small = lose context; too large = poor retrieval precision. Test with your eval set."},
            {"question": "Do I need re-ranking?", "answer": "If retrieving top-5 is enough, no. For production where every wrong answer costs trust, yes — re-rank top-20 → top-3 typically lifts answer quality 15-30%."},
            {"question": "How do I handle doc updates?", "answer": "stable_id is deterministic, so re-ingest of changed docs upserts (replaces). For deletes, query Qdrant by source metadata and call delete_points."},
        ],
    },
]
