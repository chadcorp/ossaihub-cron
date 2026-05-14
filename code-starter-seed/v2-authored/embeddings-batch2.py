"""Embeddings starters — batch 2: Cohere, Voyage, hybrid sparse-dense."""

RECORDS = [
    {
        "slug": "cohere-multilingual-embed-rerank",
        "title": "Cohere Multilingual Embed + Rerank",
        "tldr": "Cohere's embed-multilingual-v3 + rerank-multilingual-v3 — strongest off-the-shelf option for multilingual RAG (100+ languages). Drop-in alternative to OpenAI for non-English content.",
        "category": "embeddings",
        "language": "python",
        "framework": "Cohere SDK",
        "tags": ["cohere", "multilingual", "embedding", "reranker"],
        "best_for_tags": ["multilingual-rag", "non-english", "production-rag"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When your RAG content includes non-English languages and OpenAI embeddings underperform. Cohere's multilingual models are SOTA for mixed-language corpora.",
        "when_not_to_use": "Skip for English-only when OpenAI / fastembed work fine. Skip when you're already deep in Voyage / OpenAI ecosystem and the multilingual gains aren't critical.",
        "quick_start": "pip install cohere && COHERE_API_KEY=... python multilingual.py",
        "full_code": '''"""Cohere multilingual embeddings + reranker.

Pattern:
  1. Embed docs in any of 100+ languages with embed-multilingual-v3.0
  2. Query in any language; retrieve.
  3. Rerank with rerank-multilingual-v3.0 for highest precision.
"""
from __future__ import annotations

import os

import cohere

co = cohere.ClientV2(os.environ["COHERE_API_KEY"])


def embed_docs(texts: list[str]) -> list[list[float]]:
    """Embed documents. input_type='search_document' is required for asymmetric models."""
    resp = co.embed(
        model="embed-multilingual-v3.0",
        texts=texts,
        input_type="search_document",
        embedding_types=["float"],
    )
    return resp.embeddings.float_


def embed_query(query: str) -> list[float]:
    """Embed query. input_type='search_query' (different from doc!)."""
    resp = co.embed(
        model="embed-multilingual-v3.0",
        texts=[query],
        input_type="search_query",
        embedding_types=["float"],
    )
    return resp.embeddings.float_[0]


def rerank(query: str, docs: list[str], *, top_n: int = 5) -> list[dict]:
    """Rerank docs by relevance to query. Works cross-lingually."""
    resp = co.rerank(
        model="rerank-multilingual-v3.0",
        query=query,
        documents=docs,
        top_n=top_n,
    )
    return [{"index": r.index, "score": r.relevance_score, "text": docs[r.index]} for r in resp.results]


def full_pipeline(query: str, doc_corpus: list[str], *, k_dense: int = 20, k_rerank: int = 5) -> list[dict]:
    """Dense retrieval → rerank → final top-K."""
    import numpy as np

    doc_vecs = embed_docs(doc_corpus)
    q_vec = embed_query(query)

    # Cosine sim
    doc_arr = np.array(doc_vecs)
    q_arr = np.array(q_vec)
    scores = doc_arr @ q_arr / (np.linalg.norm(doc_arr, axis=1) * np.linalg.norm(q_arr))
    top_indices = np.argsort(scores)[::-1][:k_dense]

    # Rerank the top-k_dense
    candidates = [doc_corpus[i] for i in top_indices]
    reranked = rerank(query, candidates, top_n=k_rerank)
    # Re-map indices to original corpus
    for r in reranked:
        r["original_index"] = int(top_indices[r["index"]])
    return reranked


if __name__ == "__main__":
    docs = [
        "Reciprocal Rank Fusion combines multiple ranked lists.",
        "La Réciproque Rank Fusion combine plusieurs listes classées.",        # FR
        "Reciprocal Rank Fusion 是一种合并排序列表的方法。",                # ZH
        "Vector databases store embeddings for similarity search.",
        "Las bases de datos vectoriales almacenan embeddings.",               # ES
    ]
    # Query in French; should still retrieve EN content
    results = full_pipeline("Comment fusionner des résultats de plusieurs moteurs de recherche?", docs)
    for r in results:
        print(f"[{r['score']:.3f}] {r['text']}")
''',
        "dependencies": [
            {"name": "cohere", "version": ">=5.11", "purpose": "Cohere SDK v2"},
            {"name": "numpy", "version": ">=1.26", "purpose": "Cosine similarity"},
        ],
        "env_vars": [
            {"name": "COHERE_API_KEY", "required": True, "description": "Cohere API key", "example": "..."},
        ],
        "setup_steps": [
            "Sign up at cohere.com; generate API key.",
            "pip install cohere numpy",
            "export COHERE_API_KEY=...",
            "python multilingual.py",
        ],
        "variations": [
            {"label": "Embed with dimensions config", "description": "Reduce dimension for storage.", "code_snippet": "# Cohere embed supports compressed embeddings; pass output_dimension=256 or 512 for smaller vectors"},
            {"label": "Use the English-only models", "description": "If multilingual not needed.", "code_snippet": "model='embed-english-v3.0'  # smaller, faster, equal quality on English"},
            {"label": "Bedrock-hosted Cohere", "description": "AWS deployment.", "code_snippet": "# Use AWS Bedrock for Cohere; same models, AWS-hosted, BAA-eligible"},
        ],
        "common_errors": [
            {"error_text": "TooManyRequestsError", "cause": "Cohere rate limits.", "fix_snippet": "Implement exponential retry; batch embeddings (up to 96 inputs per call)."},
            {"error_text": "Wrong input_type produces poor retrieval", "cause": "Asymmetric models — query and doc need different input_type.", "fix_snippet": "ALWAYS use input_type='search_query' for queries, 'search_document' for docs at index time."},
            {"error_text": "Empty embedding array", "cause": "Old SDK or response format change.", "fix_snippet": "ClientV2 returns resp.embeddings.float_ (note trailing underscore). Older SDK had different shape."},
            {"error_text": "Rerank scores all close to 0", "cause": "Query and docs unrelated; normal.", "fix_snippet": "Rerank returns relative ranks; absolute scores often low when nothing's a good match. Use rank order, not threshold on score."},
        ],
        "production_checklist": [
            "Cache embeddings; Cohere bills per character.",
            "Batch embed calls (up to 96 inputs).",
            "Use rerank as a final precision boost, not for initial retrieval.",
            "Monitor cost by token; multilingual content has different cost profile.",
            "For high-volume, consider Bedrock-hosted Cohere (different pricing tier).",
        ],
        "tested_with": {
            "model_versions": ["embed-multilingual-v3.0", "rerank-multilingual-v3.0"],
            "library_versions": ["cohere==5.11.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["cohere"],
        "related_glossary_slugs": ["multilingual-embedding", "reranker"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Cohere vs OpenAI for multilingual?", "answer": "Cohere wins on multilingual retrieval evals (especially Asian languages). OpenAI text-embedding-3 is competitive on European; weaker on others."},
            {"question": "Always rerank?", "answer": "Rerank gives 10-25% precision boost over pure dense. Cost: ~$1 per 1k reranks. Worth it for search/RAG; skip for autocomplete-style latency-critical paths."},
            {"question": "Voyage vs Cohere?", "answer": "Voyage: top quality for English, financial/legal specialty models. Cohere: top multilingual, mature SDK. Both excellent; pick by language mix."},
        ],
        "github_url": "https://github.com/cohere-ai/cohere-python",
        "meta_title": "Cohere Multilingual Embed + Rerank — Starter",
        "meta_description": "Multilingual RAG with Cohere: embed-multilingual-v3 + rerank-multilingual-v3. Cross-lingual retrieval (query EN, find FR/ZH content).",
    },
]
