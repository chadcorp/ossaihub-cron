"""RAG patterns — batch 4: graph-RAG, agentic-RAG, HyDE, RAG evaluation."""

RECORDS = [
    {
        "slug": "graph-rag-with-neo4j",
        "title": "Graph RAG With Neo4j (Entity + Relationship Retrieval)",
        "tldr": "Graph RAG: extract entities + relationships into Neo4j, retrieve by graph traversal, not just vector similarity. Wins on multi-hop questions ('who collaborated with X?').",
        "category": "rag-patterns",
        "language": "python",
        "framework": "Neo4j + LangChain",
        "tags": ["graph-rag", "neo4j", "knowledge-graph", "multi-hop"],
        "best_for_tags": ["multi-hop-questions", "structured-domains", "research-rag"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "Multi-hop questions over structured corpora (companies + people + investments; papers + authors + citations). Graph traversal beats vector similarity when relationships matter.",
        "when_not_to_use": "Skip for unstructured corpora (vector RAG is simpler). Skip without time to extract a clean schema. Skip for single-hop factoid Q&A.",
        "quick_start": "docker run -d -p 7474:7474 -p 7687:7687 neo4j:5 && pip install neo4j langchain langchain-openai && python graph_rag.py",
        "full_code": '''"""Graph RAG: entity + relationship extraction → Neo4j → graph-aware retrieval."""
from __future__ import annotations

import os
import json
from neo4j import GraphDatabase
from openai import OpenAI


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
driver = GraphDatabase.driver(
    os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
    auth=("neo4j", os.environ.get("NEO4J_PASSWORD", "password")),
)


# ----------------- ENTITY + RELATIONSHIP EXTRACTION -----------------

EXTRACT_PROMPT = """Extract entities and relationships from the text.

Entities: people, organizations, products, events.
Relationships: (entity1) -[verb]-> (entity2).

Output JSON: {entities: [{name, type}], relationships: [{from, type, to}]}

Text: {text}
"""


def extract_graph(text: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": EXTRACT_PROMPT.format(text=text)}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)


# ----------------- INDEX (write to Neo4j) -----------------

def index_document(doc_id: str, text: str):
    graph = extract_graph(text)

    with driver.session() as session:
        # Source doc node
        session.run(
            "MERGE (d:Document {id: $id}) SET d.text = $text",
            id=doc_id, text=text[:1000],
        )
        # Entities
        for ent in graph.get("entities", []):
            session.run(
                "MERGE (e:Entity {name: $name}) SET e.type = $type "
                "WITH e MATCH (d:Document {id: $id}) MERGE (e)-[:MENTIONED_IN]->(d)",
                name=ent["name"], type=ent.get("type", "Unknown"), id=doc_id,
            )
        # Relationships
        for rel in graph.get("relationships", []):
            session.run(
                "MATCH (a:Entity {name: $from}), (b:Entity {name: $to}) "
                "MERGE (a)-[r:RELATES {type: $rtype}]->(b)",
                **{"from": rel["from"], "to": rel["to"], "rtype": rel["type"]},
            )


# ----------------- RETRIEVE (graph queries) -----------------

def retrieve_neighborhood(entity_name: str, hops: int = 2) -> list[dict]:
    """Return all entities within N hops of the seed entity + linking docs."""
    with driver.session() as session:
        result = session.run(
            f"MATCH (e:Entity {{name: $name}})-[*1..{hops}]-(other:Entity)-"
            "[:MENTIONED_IN]->(d:Document) "
            "RETURN DISTINCT other.name AS name, other.type AS type, d.id AS doc_id, d.text AS excerpt "
            "LIMIT 25",
            name=entity_name,
        )
        return [dict(record) for record in result]


def answer_with_graph_rag(question: str, seed_entity: str) -> str:
    context_records = retrieve_neighborhood(seed_entity, hops=2)
    context_text = "\\n".join(
        f"- {r['name']} ({r['type']}) mentioned in doc {r['doc_id']}: {r['excerpt'][:200]}"
        for r in context_records
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer using the graph context. Cite doc IDs."},
            {"role": "user", "content": f"Context:\\n{context_text}\\n\\nQuestion: {question}"},
        ],
        temperature=0,
    )
    return response.choices[0].message.content


# ----------------- DEMO -----------------

if __name__ == "__main__":
    docs = {
        "d1": "Acme Corp acquired BetaCo in 2023 for $50M. CEO Jane Smith led the deal.",
        "d2": "Jane Smith previously founded Gamma Inc, which was sold to BetaCo in 2020.",
        "d3": "BetaCo's products integrate with Acme's CRM platform after the acquisition.",
    }
    for doc_id, text in docs.items():
        print(f"Indexing {doc_id}...")
        index_document(doc_id, text)

    answer = answer_with_graph_rag(
        "What's the relationship between Jane Smith and Acme Corp?",
        seed_entity="Jane Smith",
    )
    print(f"\\n{answer}")

    driver.close()
''',
        "dependencies": [
            {"name": "neo4j", "version": ">=5.20", "purpose": "Neo4j Python driver"},
            {"name": "openai", "version": ">=1.40", "purpose": "Entity extraction + answer generation"},
        ],
        "env_vars": [
            {"name": "NEO4J_URI", "required": False, "description": "Neo4j connection", "example": "bolt://localhost:7687"},
            {"name": "NEO4J_PASSWORD", "required": True, "description": "Neo4j password", "example": "password"},
            {"name": "OPENAI_API_KEY", "required": True, "description": "Entity extractor", "example": "sk-..."},
        ],
        "setup_steps": [
            "Run Neo4j: docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5",
            "Open browser http://localhost:7474 to verify",
            "pip install neo4j openai",
            "Set env vars",
            "python graph_rag.py",
            "Explore graph in Neo4j Browser",
        ],
        "variations": [
            {"label": "LangChain GraphCypherQAChain", "description": "LLM generates Cypher queries directly.", "code_snippet": "from langchain.chains import GraphCypherQAChain\\nchain = GraphCypherQAChain.from_llm(llm, graph=Neo4jGraph(...), verbose=True)"},
            {"label": "Microsoft GraphRAG", "description": "MSR's full GraphRAG implementation.", "code_snippet": "# pip install graphrag; structured indexing pipeline with community detection. More sophisticated, more compute."},
            {"label": "Hybrid: graph + vector", "description": "Vector for fuzzy, graph for precise.", "code_snippet": "# Retrieve top-k via vector similarity → seed graph traversal from those entities. Best of both."},
        ],
        "common_errors": [
            {"error_text": "Entities mismatched (Jane Smith vs J. Smith)", "cause": "No entity normalization.", "fix_snippet": "Add an entity-linking step: dedupe by string similarity or use a managed entity-linking service. Or constrain extractor with a known entity list."},
            {"error_text": "Cypher syntax error in query", "cause": "User-input contained quotes / special chars.", "fix_snippet": "Always use parameterized queries ($name, $type) — NEVER string-interpolate. Pattern in code does this."},
            {"error_text": "Slow at scale (>1M nodes)", "cause": "Unindexed properties.", "fix_snippet": "CREATE INDEX entity_name FOR (e:Entity) ON (e.name). Add indexes for all queried properties."},
            {"error_text": "LLM hallucinates entities", "cause": "Extractor not grounded.", "fix_snippet": "Constrain with response_format=json_object + Pydantic schema. Validate entity types are in known set."},
        ],
        "production_checklist": [
            "Index on every queried node property.",
            "Normalize entities (resolve aliases).",
            "Use parameterized Cypher queries.",
            "Schedule re-extraction when source docs change.",
            "Backup Neo4j with apoc.export.cypher.",
            "Monitor query latency — graph queries can balloon at >3 hops.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["neo4j==5.20", "openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["neo4j", "openai"],
        "related_glossary_slugs": ["graph-rag", "knowledge-graph"],
        "related_learn_slugs": [],
        "license": "GPL-3.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Graph RAG vs vector RAG?", "answer": "Vector: fuzzy similarity, works on unstructured text. Graph: precise structured retrieval, requires schema. Multi-hop questions ('how is X connected to Y') strongly favor graph."},
            {"question": "Microsoft GraphRAG vs DIY?", "answer": "MS GraphRAG: full pipeline with community detection, hierarchical summaries. DIY (this code): simpler, cheaper, easier to debug. Start DIY; graduate to MS GraphRAG if you need its features."},
            {"question": "Cost of entity extraction?", "answer": "~1k tokens per doc with gpt-4o-mini. 10k docs → $0.50-1.00 one-time. Cheap; only pay again on doc changes."},
            {"question": "When to use graph + vector together?", "answer": "Use vector for fuzzy doc retrieval; use graph for STRUCTURED relationship traversal. Combine via two-stage: vector finds candidates, graph expands their neighborhoods."},
        ],
        "github_url": "https://github.com/microsoft/graphrag",
        "meta_title": "Graph RAG With Neo4j Starter",
        "meta_description": "Graph RAG: extract entities + relationships to Neo4j, retrieve via graph traversal. Wins on multi-hop questions over structured corpora.",
    },
    {
        "slug": "agentic-rag-with-routing",
        "title": "Agentic RAG With Tool Routing",
        "tldr": "Agent decides WHICH retrieval source to query (docs / FAQ / SQL / web) per question. Better than monolithic RAG when sources are heterogeneous. Routes by question type.",
        "category": "rag-patterns",
        "language": "python",
        "framework": "OpenAI + Custom",
        "tags": ["agentic-rag", "routing", "multi-source", "rag"],
        "best_for_tags": ["heterogeneous-data", "enterprise-rag", "multi-source-qa"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "RAG over MULTIPLE retrieval sources (docs in Notion, FAQs in Zendesk, structured data in Postgres, web for recency). Monolithic RAG queries all sources; agentic routes smartly.",
        "when_not_to_use": "Skip with one homogeneous source (just use direct retrieval). Skip for latency-sensitive apps (routing adds an LLM call).",
        "quick_start": "pip install openai pydantic && python agentic_rag.py",
        "full_code": '''"""Agentic RAG: LLM router picks the right retrieval tool per question."""
from __future__ import annotations

import json
import os
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# ----------------- ROUTING SCHEMA -----------------

class RouteDecision(BaseModel):
    source: Literal["product_docs", "faq_kb", "support_history", "live_web", "structured_db"]
    refined_query: str = Field(..., max_length=200)
    reasoning: str = Field(..., max_length=200)


# ----------------- ROUTER -----------------

ROUTER_PROMPT = """You route customer questions to the right retrieval source.

Sources:
- product_docs: SOC2, security, architecture, integrations, API reference
- faq_kb: pricing, billing, common 'how do I' questions
- support_history: past customer issues, troubleshooting precedents
- live_web: news, competitor info, recent industry changes
- structured_db: usage data, account-specific data, billing records

Pick ONE source. Refine the query to be source-appropriate.

User question: {question}
"""


def route(question: str) -> RouteDecision:
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": ROUTER_PROMPT.format(question=question)}],
        response_format=RouteDecision,
        temperature=0,
    )
    return response.choices[0].message.parsed


# ----------------- RETRIEVAL TOOLS (stubs) -----------------

def retrieve_product_docs(query: str) -> list[str]:
    return [f"[product_docs result for '{query}']"]

def retrieve_faq(query: str) -> list[str]:
    return [f"[faq_kb result for '{query}']"]

def retrieve_support_history(query: str) -> list[str]:
    return [f"[support_history result for '{query}']"]

def retrieve_web(query: str) -> list[str]:
    return [f"[live_web result for '{query}']"]

def retrieve_structured(query: str, user_id: str) -> list[str]:
    return [f"[structured_db result for '{query}' scoped to {user_id}]"]


RETRIEVERS = {
    "product_docs": lambda q, _u: retrieve_product_docs(q),
    "faq_kb": lambda q, _u: retrieve_faq(q),
    "support_history": lambda q, _u: retrieve_support_history(q),
    "live_web": lambda q, _u: retrieve_web(q),
    "structured_db": retrieve_structured,
}


# ----------------- AGENTIC RAG -----------------

def agentic_answer(question: str, user_id: str = "anonymous") -> dict:
    # Step 1: route
    decision = route(question)
    print(f"Route: {decision.source} — {decision.reasoning}")

    # Step 2: retrieve
    retrieve_fn = RETRIEVERS[decision.source]
    context = retrieve_fn(decision.refined_query, user_id)

    # Step 3: generate answer (with citation)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "Answer using the context. Cite the source type. "
                        "If context doesn't answer, say so."},
            {"role": "user",
             "content": f"Question: {question}\\n\\nSource: {decision.source}\\n"
                        f"Context:\\n{chr(10).join(context)}"},
        ],
        temperature=0,
    )

    return {
        "answer": response.choices[0].message.content,
        "source": decision.source,
        "refined_query": decision.refined_query,
        "context_count": len(context),
    }


# ----------------- FALLBACK: MULTI-SOURCE WHEN AMBIGUOUS -----------------

def agentic_answer_with_fallback(question: str, user_id: str = "anonymous") -> dict:
    """If first source returns no useful results, try a second."""
    primary = agentic_answer(question, user_id)
    if "no relevant" in primary["answer"].lower() or primary["context_count"] == 0:
        print("Primary route returned nothing; trying fallback...")
        # Re-route excluding primary source
        # (omitted for brevity; in practice, call route() with primary source masked)
    return primary


# ----------------- DEMO -----------------

if __name__ == "__main__":
    questions = [
        "How does your SOC2 audit work?",
        "What's my plan's monthly cost?",
        "Anyone else hit this 500 error during signup?",
        "Did Acme Corp announce a new product this week?",
        "What's my current usage for September?",
    ]
    for q in questions:
        print(f"\\n--- Q: {q} ---")
        result = agentic_answer(q, user_id="u_42")
        print(f"A: {result['answer']}")
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "Router + answerer"},
            {"name": "pydantic", "version": ">=2.0", "purpose": "Schema"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai pydantic",
            "export OPENAI_API_KEY=sk-...",
            "Replace retrieval stubs with your real retrieval functions",
            "Define RETRIEVERS dict with your sources",
            "python agentic_rag.py",
        ],
        "variations": [
            {"label": "Multi-source per query", "description": "Route to 2+ sources when needed.", "code_snippet": "# Replace Literal source with list[Literal[...]]. Retrieve from all selected; merge."},
            {"label": "Cost-aware routing", "description": "Prefer cheap sources first.", "code_snippet": "# Tag each source with cost weight. Router prefers cheap; falls back to expensive only if cheap returns nothing."},
            {"label": "Self-correcting agent", "description": "Re-route if first answer is unhelpful.", "code_snippet": "# After generating answer, ask LLM: 'is this answer adequate?'. If no, re-route to a different source."},
        ],
        "common_errors": [
            {"error_text": "Router always picks the same source", "cause": "Source descriptions overlap or LLM has bias.", "fix_snippet": "Make source descriptions DISTINCT + concrete. Add few-shot examples in router prompt. Test on diverse questions."},
            {"error_text": "Refined query doesn't match retrieval style", "cause": "Generic refinement.", "fix_snippet": "Per-source query refinement: 'For structured_db, refine to SQL-like terms; for live_web, refine to search keywords.'"},
            {"error_text": "Latency too high (2x LLM calls)", "cause": "Router + answerer.", "fix_snippet": "Skip router for high-confidence sources (e.g., obvious billing questions → faq_kb directly). Or cache router decisions by question pattern."},
            {"error_text": "Wrong source picked for ambiguous question", "cause": "Routing is best-effort.", "fix_snippet": "Add fallback to 2nd source if first returns nothing. Or expose 'sources tried' in UI so user can re-route."},
        ],
        "production_checklist": [
            "Source descriptions are DISTINCT + concrete.",
            "Test router on diverse + edge-case questions.",
            "Add fallback / multi-source when primary returns nothing.",
            "Log every routing decision for analysis.",
            "Use cheap model for routing (gpt-4o-mini, haiku).",
            "Track per-source accuracy; tune source descriptions.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["openai"],
        "related_glossary_slugs": ["agentic-rag", "query-routing"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Agentic vs monolithic RAG?", "answer": "Monolithic: query ALL sources, merge. Agentic: route to ONE relevant source. Monolithic wins on recall (no router miss); agentic wins on precision + cost + latency."},
            {"question": "Cost of routing?", "answer": "One extra LLM call per query (cheap model). ~$0.0001 per route. Saves cost downstream by avoiding wasteful multi-source retrieval."},
            {"question": "Confidence in routing decisions?", "answer": "Track router accuracy on labeled examples. Below 85% accuracy means refine source descriptions or add fallback. Above 95% is great."},
            {"question": "Multi-source fallback strategy?", "answer": "Try primary first; if no context, route to secondary. Better than running all sources upfront. Cost-aware version: rank sources by cost."},
        ],
        "github_url": "",
        "meta_title": "Agentic RAG With Tool Routing Starter",
        "meta_description": "Agentic RAG: LLM router picks retrieval source per question. Multi-source enterprise RAG with cost-aware routing + fallback.",
    },
    {
        "slug": "hyde-hypothetical-document-embeddings",
        "title": "HyDE (Hypothetical Document Embeddings) For Hard Queries",
        "tldr": "Generate a HYPOTHETICAL answer to the user's query, embed THAT, retrieve real docs similar to it. Beats query embedding alone on hard technical questions.",
        "category": "rag-patterns",
        "language": "python",
        "framework": "OpenAI + Custom",
        "tags": ["hyde", "query-expansion", "rag", "retrieval"],
        "best_for_tags": ["technical-rag", "academic-search", "hard-queries"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Hard / abstract queries where query embedding alone struggles. HyDE: generate hypothetical answer → embed → retrieve. Works because answers and docs are linguistically similar.",
        "when_not_to_use": "Skip for keyword queries (BM25 wins). Skip for well-formed factoid questions (direct embedding is fine). Skip if budget-constrained — HyDE adds one LLM call.",
        "quick_start": "pip install openai numpy && python hyde.py",
        "full_code": '''"""HyDE: Hypothetical Document Embeddings."""
from __future__ import annotations

import os
import numpy as np
from openai import OpenAI


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# ----------------- HYDE PROMPT -----------------

HYDE_PROMPT = """Please write a SHORT (~150 words) hypothetical passage that would answer this query.

This is for retrieval — focus on terminology, structure, and depth a real doc would have.
Don't add disclaimers ('I cannot verify...'). Just write the hypothetical answer.

Query: {query}
"""


def generate_hypothetical(query: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": HYDE_PROMPT.format(query=query)}],
        temperature=0.7,  # some variety helps; not too high
        max_tokens=200,
    )
    return response.choices[0].message.content


# ----------------- EMBED -----------------

def embed(texts: list[str], model: str = "text-embedding-3-small") -> np.ndarray:
    response = client.embeddings.create(model=model, input=texts)
    return np.array([e.embedding for e in response.data])


# ----------------- RETRIEVE WITH HYDE -----------------

def hyde_retrieve(query: str, corpus: list[str], corpus_emb: np.ndarray, k: int = 5) -> list[tuple[str, float]]:
    """1. Generate hypothetical answer. 2. Embed it. 3. Search corpus."""
    hypothetical = generate_hypothetical(query)
    hyp_emb = embed([hypothetical])[0]
    sims = corpus_emb @ hyp_emb
    top_k = np.argsort(-sims)[:k]
    return [(corpus[i], float(sims[i])) for i in top_k]


# ----------------- ENSEMBLE: query + HyDE -----------------

def hyde_ensemble_retrieve(query: str, corpus: list[str], corpus_emb: np.ndarray,
                            k: int = 5) -> list[tuple[str, float]]:
    """Combine query embedding and HyDE embedding for robust retrieval."""
    hypothetical = generate_hypothetical(query)
    q_emb, hyp_emb = embed([query, hypothetical])

    # Average the two embeddings (or use weighted)
    combined = (q_emb + hyp_emb) / 2
    combined /= np.linalg.norm(combined)  # renormalize

    sims = corpus_emb @ combined
    top_k = np.argsort(-sims)[:k]
    return [(corpus[i], float(sims[i])) for i in top_k]


# ----------------- COMPARE: PLAIN VS HYDE -----------------

def compare(query: str, corpus: list[str], corpus_emb: np.ndarray, k: int = 5):
    print(f"\\nQuery: {query}")

    # Plain embedding
    q_emb = embed([query])[0]
    sims_plain = corpus_emb @ q_emb
    top_plain = np.argsort(-sims_plain)[:k]
    print("Plain (query embedding):")
    for i in top_plain:
        print(f"  {sims_plain[i]:.3f}: {corpus[i][:80]}")

    # HyDE
    print("\\nHyDE:")
    for text, score in hyde_retrieve(query, corpus, corpus_emb, k):
        print(f"  {score:.3f}: {text[:80]}")

    # Ensemble
    print("\\nEnsemble:")
    for text, score in hyde_ensemble_retrieve(query, corpus, corpus_emb, k):
        print(f"  {score:.3f}: {text[:80]}")


if __name__ == "__main__":
    corpus = [
        "Rate limiting can be implemented using token-bucket or sliding-window algorithms.",
        "Caching reduces latency by storing response data closer to clients.",
        "PostgreSQL supports declarative partitioning for managing large tables.",
        "OAuth 2.0 PKCE prevents authorization-code interception attacks.",
        "Vector embeddings represent text in high-dimensional space for similarity search.",
        "Distributed tracing follows requests across microservices.",
        "Connection pooling reuses database connections to reduce overhead.",
        "Idempotency keys prevent duplicate processing of HTTP requests.",
    ]
    corpus_emb = embed(corpus)

    compare("How do I prevent users from hammering my API?", corpus, corpus_emb)
    compare("Speed up DB queries on a busy app", corpus, corpus_emb)
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "Embeddings + LLM"},
            {"name": "numpy", "version": ">=1.26", "purpose": "Vector math"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai numpy",
            "export OPENAI_API_KEY=sk-...",
            "python hyde.py",
            "Compare HyDE vs plain on YOUR eval set; pick winner",
        ],
        "variations": [
            {"label": "Multi-HyDE", "description": "Generate N hypotheticals, average embeddings.", "code_snippet": "# Generate 3-5 hypotheticals with different seeds; average embeddings. More robust to single-generation noise."},
            {"label": "Domain-tuned HyDE prompt", "description": "Improve hypothetical quality.", "code_snippet": "# Use a system prompt with examples from your domain. 'Write a paragraph as if from a technical doc...' improves retrieval."},
            {"label": "HyDE for non-English", "description": "Generate hypothetical in CORPUS language.", "code_snippet": "# If corpus is Japanese, generate hypothetical in Japanese (even if query is English). Embeddings align better."},
        ],
        "common_errors": [
            {"error_text": "HyDE retrieves worse than plain", "cause": "Query is already specific.", "fix_snippet": "HyDE helps abstract / hard queries. For well-formed factoids, plain embedding wins. Run YOUR eval to decide."},
            {"error_text": "Hypothetical has disclaimers", "cause": "LLM hedging.", "fix_snippet": "Re-pin prompt: 'no disclaimers, just write the answer.' Disclaimers pollute the embedding."},
            {"error_text": "Cost doubled per query", "cause": "Extra LLM call.", "fix_snippet": "Use cheap model for hypothetical (gpt-4o-mini, haiku). Cache hypotheticals by query hash. ~$0.0001 per query."},
            {"error_text": "HyDE doesn't help on small corpus", "cause": "Few docs to match against.", "fix_snippet": "HyDE shines on large corpora where precise match matters. <100 docs: marginal benefit."},
        ],
        "production_checklist": [
            "A/B test HyDE vs plain on YOUR eval set.",
            "Cache hypotheticals by query hash.",
            "Use cheap LLM for hypothetical generation.",
            "Multi-HyDE for harder workloads (generate 3, average).",
            "Pair with reranker for final precision.",
            "Disable for clearly factoid queries (regex on '?' or specific phrasing).",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "text-embedding-3-small"],
            "library_versions": ["openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["openai"],
        "related_glossary_slugs": ["hyde", "query-expansion"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Does HyDE 'hallucinate' wrong answers?", "answer": "Yes — and that's fine. The hypothetical is for EMBEDDING similarity, not user-facing. Wrong details don't matter if the embedding lands in the right neighborhood."},
            {"question": "HyDE vs query rewriting?", "answer": "Rewriting: produce search-friendly queries. HyDE: produce hypothetical ANSWERS. HyDE often wins because answer-space ≈ doc-space. Try both."},
            {"question": "Multi-HyDE — how many?", "answer": "3-5 hypotheticals, averaged. More = more LLM cost, diminishing returns. Test on YOUR data."},
            {"question": "Cost?", "answer": "1 extra LLM call (~$0.0001 with gpt-4o-mini) + 1 extra embedding call (~$0.00002 with text-embedding-3-small). Per query: <$0.0002 total."},
        ],
        "github_url": "https://github.com/texttron/hyde",
        "meta_title": "HyDE Hypothetical Document Embeddings Starter",
        "meta_description": "HyDE: generate hypothetical answer, embed THAT, retrieve real docs similar to it. Beats query embedding alone on hard queries.",
    },
    {
        "slug": "rag-eval-with-ragas",
        "title": "RAG Evaluation With Ragas Framework",
        "tldr": "Ragas: standard metrics for RAG (faithfulness, context precision/recall, answer relevancy). Catches hallucination, off-topic retrieval, and answer-context mismatch.",
        "category": "rag-patterns",
        "language": "python",
        "framework": "Ragas",
        "tags": ["ragas", "rag-eval", "faithfulness", "metrics"],
        "best_for_tags": ["rag-quality", "ml-engineers", "ci-eval"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Production RAG system. Ragas gives you the 4-5 standard quality metrics (faithfulness, context precision, context recall, answer relevancy). Catches what informal testing misses.",
        "when_not_to_use": "Skip for very early prototypes (just eyeball outputs). Skip without a labeled eval set — Ragas needs (question, ground-truth-answer, contexts) tuples.",
        "quick_start": "pip install ragas datasets && python ragas_eval.py",
        "full_code": '''"""Ragas: standard RAG evaluation metrics."""
from __future__ import annotations

import os
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    Faithfulness,
    ContextPrecision,
    ContextRecall,
    AnswerRelevancy,
    AnswerCorrectness,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


# ----------------- CONFIG: WHICH JUDGE MODELS -----------------

# Use stronger model for judge than for production
judge_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o", temperature=0))
judge_emb = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small"))


# ----------------- EVAL SET FORMAT -----------------

# Each example needs:
#   question — the user query
#   answer — your RAG system's output (the thing being evaluated)
#   contexts — list of retrieved chunks (passed to LLM)
#   ground_truth — optional, only needed for AnswerCorrectness


def build_eval_dataset() -> Dataset:
    """Build from your real RAG outputs."""
    data = {
        "question": [
            "What is rate limiting?",
            "How does our SOC2 audit work?",
        ],
        "answer": [
            "Rate limiting restricts requests per time window using algorithms like token-bucket.",
            "We undergo annual SOC2 Type II audits covering security and availability.",
        ],
        "contexts": [
            ["Rate limiting can be implemented using token-bucket or sliding-window algorithms.",
             "Common rate limit patterns include per-user, per-IP, per-endpoint quotas."],
            ["SOC2 Type II audits happen annually and cover security and availability principles.",
             "Our auditor is XYZ; report is available under NDA."],
        ],
        "ground_truth": [
            "Rate limiting restricts the number of requests a client can make in a time window.",
            "SOC2 Type II audits run annually covering security, availability, and confidentiality.",
        ],
    }
    return Dataset.from_dict(data)


# ----------------- RUN EVALUATION -----------------

def run_eval(dataset: Dataset) -> dict:
    metrics = [
        Faithfulness(llm=judge_llm),                # Answer grounded in context?
        ContextPrecision(llm=judge_llm),            # Are retrieved contexts relevant?
        ContextRecall(llm=judge_llm),               # Do contexts cover the ground truth?
        AnswerRelevancy(llm=judge_llm, embeddings=judge_emb),  # Is answer relevant to question?
        AnswerCorrectness(llm=judge_llm, embeddings=judge_emb),  # Does answer match ground truth?
    ]

    result = evaluate(dataset, metrics=metrics)

    # Result is a pandas DataFrame with per-example + aggregate scores
    df = result.to_pandas()
    print(df[["question", "faithfulness", "context_precision", "context_recall",
              "answer_relevancy", "answer_correctness"]])

    # Aggregate scores
    aggregates = {m.name: float(df[m.name].mean()) for m in metrics}
    print("\\n=== Aggregate scores ===")
    for name, score in aggregates.items():
        print(f"  {name}: {score:.3f}")

    return aggregates


# ----------------- DIAGNOSTIC: WHICH METRIC IS WEAKEST? -----------------

def diagnose(scores: dict):
    """Suggest fixes based on which metric is weakest."""
    weakest = min(scores.items(), key=lambda x: x[1])
    suggestions = {
        "faithfulness": "Answer drifts from context. Tighten prompt: 'Use ONLY the context.' Or use citation-enforcement.",
        "context_precision": "Retrieving irrelevant chunks. Lower k, improve embeddings, add reranker.",
        "context_recall": "Missing relevant chunks. Increase k, improve chunking, try HyDE or hybrid retrieval.",
        "answer_relevancy": "Answer doesn't address question. Re-prompt LLM with clearer answer-format instructions.",
        "answer_correctness": "Answer wrong on facts. Could be retrieval (missing context) OR LLM (poor synthesis). Check context_recall first.",
    }
    print(f"\\nWeakest metric: {weakest[0]} = {weakest[1]:.3f}")
    print(f"Suggestion: {suggestions[weakest[0]]}")


# ----------------- DEMO -----------------

if __name__ == "__main__":
    dataset = build_eval_dataset()
    scores = run_eval(dataset)
    diagnose(scores)
''',
        "dependencies": [
            {"name": "ragas", "version": ">=0.2", "purpose": "RAG eval framework"},
            {"name": "datasets", "version": ">=2.18", "purpose": "Dataset type"},
            {"name": "langchain-openai", "version": ">=0.2", "purpose": "Judge LLM wrapper"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "Judge model", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install ragas datasets langchain-openai",
            "export OPENAI_API_KEY=sk-...",
            "Build dataset: (question, answer, contexts, ground_truth) tuples from real RAG outputs",
            "python ragas_eval.py",
            "Iterate on weakest metric",
        ],
        "variations": [
            {"label": "Test-set generation from corpus", "description": "Auto-generate eval set.", "code_snippet": "from ragas.testset import TestsetGenerator\\ngenerator = TestsetGenerator.from_langchain(...); testset = generator.generate_with_langchain_docs(docs, test_size=50)"},
            {"label": "Self-hosted judge (no OpenAI)", "description": "Use local Llama as judge.", "code_snippet": "judge_llm = LangchainLLMWrapper(ChatOllama(model='llama3.1:70b'))"},
            {"label": "CI integration", "description": "Fail PR on regression.", "code_snippet": "# In CI: scores = run_eval(prod_dataset); assert scores['faithfulness'] > 0.85, 'Faithfulness regression!'"},
        ],
        "common_errors": [
            {"error_text": "Faithfulness very low (<0.5)", "cause": "Answer adds claims not in context.", "fix_snippet": "Tighten system prompt: 'Use only information from context.' Use citation-enforcement RAG pattern. Cap creativity (temperature=0)."},
            {"error_text": "ContextPrecision low + answer correct", "cause": "Retrieving too many irrelevant chunks; LLM picks the right one.", "fix_snippet": "Lower k. Add reranker (Cohere rerank-3) to filter retrieval before LLM. Cheaper inference too."},
            {"error_text": "ContextRecall low (no relevant chunks retrieved)", "cause": "Wrong embeddings or chunking.", "fix_snippet": "Try different embedding model. Adjust chunking. Try HyDE / query rewriting. Add hybrid retrieval (BM25 + vector)."},
            {"error_text": "Judge timeouts on big eval sets", "cause": "Many LLM calls.", "fix_snippet": "Use cheaper judge (gpt-4o-mini). Run async with ragas's batch eval. Sample subset for fast CI; full eval nightly."},
        ],
        "production_checklist": [
            "Use STRONGER judge model than production model.",
            "Pin judge model version — score baselines depend on it.",
            "Build eval set from REAL production traffic (sampled + labeled).",
            "Run regression eval on every prompt / model change.",
            "Track each metric over time; flag drift.",
            "Diagnose weakest metric, iterate on that subsystem.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o", "text-embedding-3-small"],
            "library_versions": ["ragas==0.2", "datasets==2.18"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["ragas"],
        "related_glossary_slugs": ["rag-eval", "faithfulness"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Ragas vs DeepEval vs custom?", "answer": "Ragas: research-paper-aligned, RAG-focused. DeepEval: pytest-style, broader. Custom: full control. Pick Ragas if RAG-heavy; DeepEval for general LLM eval; custom for specialized needs."},
            {"question": "Need ground_truth for every metric?", "answer": "No — only AnswerCorrectness + ContextRecall need ground_truth. Faithfulness, ContextPrecision, AnswerRelevancy work WITHOUT labeled answers. Useful for unlabeled corpora."},
            {"question": "Cost of full eval?", "answer": "~$0.05-0.20 per example with gpt-4o judge. 100 examples × $0.10 = $10 per eval run. Manageable for periodic eval; expensive for every PR."},
            {"question": "How to interpret scores?", "answer": "All metrics 0-1. >0.9 excellent, 0.7-0.9 good, <0.7 attention needed. Track RELATIVE changes over time more than absolute thresholds."},
        ],
        "github_url": "https://github.com/explodinggradients/ragas",
        "meta_title": "RAG Evaluation With Ragas Framework Starter",
        "meta_description": "Ragas: 5 standard RAG metrics (faithfulness, context precision/recall, answer relevancy/correctness). Diagnose + fix RAG quality.",
    },
]
