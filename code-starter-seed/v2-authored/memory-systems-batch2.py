"""Memory-system starters — batch 2: Letta server, episodic SQLite memory, Graphiti temporal graph."""

RECORDS = [
    {
        "slug": "letta-stateful-agent-server",
        "title": "Letta (MemGPT) Stateful Agent With Persistent Memory",
        "tldr": "Run agents server-side with Letta so their memory survives process restarts: editable persona/human memory blocks, archival memory with semantic search, and reconnect-by-id persistence.",
        "category": "memory-systems",
        "language": "python",
        "framework": "Letta",
        "tags": ["letta", "memgpt", "agent-memory", "persistence"],
        "best_for_tags": ["long-lived-agents", "personal-assistants", "stateful-chat"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "You need an agent whose memory outlives a single process: a personal assistant or support bot that remembers a user across sessions. Letta stores agent state server-side and the agent edits its own memory via tools.",
        "when_not_to_use": "Skip for stateless one-shot calls or a single request/response where you control the prompt fully. Skip if you cannot run a Letta server (Docker or pip) alongside your app.",
        "quick_start": "docker run -p 8283:8283 letta/letta:latest && pip install letta-client && python letta_agent.py",
        "full_code": '''"""Letta stateful agent: persistent memory blocks + archival search.

Talks to a running Letta server (docker run letta/letta or `letta server`).
SDK surface evolves — official patterns at docs.letta.com. Each SDK call is
isolated in a small function so a signature change is a one-line fix.
"""
from __future__ import annotations

import os
import sys

from letta_client import Letta


# ----------------- CONFIG -----------------

BASE_URL = os.environ.get("LETTA_BASE_URL", "http://localhost:8283")
# The MODEL BACKEND key is read by the SERVER, not this client. Set it in the
# server's environment (ANTHROPIC_API_KEY or OPENAI_API_KEY) before starting it.
MODEL = os.environ.get("LETTA_MODEL", "anthropic/claude-sonnet-4-5")
EMBED = os.environ.get("LETTA_EMBED", "openai/text-embedding-3-small")


def connect() -> Letta:
    """Connect to the Letta server. Raises if it is not reachable."""
    return Letta(base_url=BASE_URL)


# ----------------- AGENT LIFECYCLE -----------------

def create_agent(client: Letta, user_name: str):
    """Create an agent with editable core-memory blocks (docs.letta.com pattern)."""
    return client.agents.create(
        model=MODEL,
        embedding=EMBED,
        memory_blocks=[
            {"label": "persona", "value": "You are a concise, friendly support agent."},
            {"label": "human", "value": f"The user's name is {user_name}."},
        ],
    )


def chat(client: Letta, agent_id: str, text: str) -> str:
    """Send one user message; return concatenated assistant text."""
    response = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{"role": "user", "content": text}],
    )
    out = []
    for msg in response.messages:
        # Assistant turns surface as message_type == "assistant_message".
        if getattr(msg, "message_type", "") == "assistant_message":
            out.append(getattr(msg, "content", "") or "")
    return "\\n".join(p for p in out if p)


# ----------------- ARCHIVAL MEMORY (semantic recall) -----------------

def remember(client: Letta, agent_id: str, fact: str) -> None:
    """Insert a passage into archival memory (vector-searchable later)."""
    client.agents.passages.create(agent_id=agent_id, text=fact)


def search_memory(client: Letta, agent_id: str, query: str, limit: int = 3):
    """Semantic search over archival memory."""
    return client.agents.passages.search(agent_id=agent_id, query=query, limit=limit)


# ----------------- DEMO -----------------

def main() -> None:
    try:
        client = connect()
    except Exception as exc:  # connection refused if server not up
        print(f"Cannot reach Letta server at {BASE_URL}: {exc}", file=sys.stderr)
        print("Start it: docker run -p 8283:8283 letta/letta:latest", file=sys.stderr)
        sys.exit(1)

    agent = create_agent(client, user_name="Dana")
    print("agent_id:", agent.id)

    print(chat(client, agent.id, "Hi! I prefer answers under two sentences."))
    remember(client, agent.id, "Dana ships a Rust CLI called 'tide' and dislikes verbose output.")

    hits = search_memory(client, agent.id, "what project does the user work on?")
    print("archival hits:", [getattr(h, "text", "") for h in hits])

    # Persistence proof: reconnect by id in a fresh client; state is server-side.
    fresh = connect()
    same = fresh.agents.retrieve(agent_id=agent.id)
    print("reconnected agent persona-bearing agent:", same.id == agent.id)


if __name__ == "__main__":
    main()
''',
        "dependencies": [
            {"name": "letta-client", "version": ">=0.1", "purpose": "Python SDK for the Letta server"},
            {"name": "letta", "version": ">=0.7", "purpose": "The Letta server itself (optional if using the Docker image)"},
        ],
        "env_vars": [
            {"name": "LETTA_BASE_URL", "required": False, "description": "URL of the running Letta server", "example": "http://localhost:8283"},
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Model backend key read by the SERVER (or OPENAI_API_KEY)", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "Start the server: docker run -p 8283:8283 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY letta/letta:latest",
            "Install the client: pip install letta-client",
            "Wait for the server health endpoint (http://localhost:8283) to respond before connecting",
            "Save letta_agent.py and run: python letta_agent.py",
            "Inspect agents in the Letta ADE / web UI if you want a visual view of memory blocks",
        ],
        "variations": [
            {"label": "Docker-compose deployment", "description": "Run server + Postgres so agent state persists on a real database.", "code_snippet": "# docker-compose.yml\\nservices:\\n  letta:\\n    image: letta/letta:latest\\n    ports: ['8283:8283']\\n    environment:\\n      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}\\n      - LETTA_PG_URI=postgresql://letta:letta@db:5432/letta\\n    depends_on: [db]\\n  db:\\n    image: pgvector/pgvector:pg16\\n    environment: { POSTGRES_USER: letta, POSTGRES_PASSWORD: letta, POSTGRES_DB: letta }"},
            {"label": "Multi-user agents", "description": "One agent per user id; route messages by lookup.", "code_snippet": "AGENTS = {}\\ndef agent_for(client, user_id, name):\\n    if user_id not in AGENTS:\\n        AGENTS[user_id] = create_agent(client, name).id\\n    return AGENTS[user_id]  # persist this map in your own DB, keyed by user_id"},
            {"label": "Sleep-time memory editing", "description": "Let the agent reorganize memory in the background between turns.", "code_snippet": "# Enable a sleep-time / background agent so core memory is summarized off the\\n# critical path. See docs.letta.com 'sleep-time agents'; configured at create()\\n# via the agent type, then triggered on idle rather than per user message."},
        ],
        "common_errors": [
            {"error_text": "AttributeError on client.agents.<x>", "cause": "SDK and server versions are out of step; method names moved.", "fix_snippet": "Pin both: letta-client and the server image to a matched release. Check the installed version (pip show letta-client) against docs.letta.com for the exact call name."},
            {"error_text": "Connection refused / max retries exceeded", "cause": "Client connected before the server finished booting.", "fix_snippet": "Poll the server URL until it returns 200 before creating an agent. In Docker, add a healthcheck and depends_on: condition: service_healthy."},
            {"error_text": "Core memory block exceeds limit", "cause": "Writing too much into a persona/human block (blocks are bounded).", "fix_snippet": "Keep core-memory blocks small (identity + key facts). Push bulk facts to archival memory via passages.create — that is the searchable, unbounded store."},
            {"error_text": "Server error: no LLM provider configured", "cause": "Model backend key set on the CLIENT instead of the SERVER.", "fix_snippet": "Set ANTHROPIC_API_KEY (or OPENAI_API_KEY) in the server's environment, not your script. The client never sends model keys."},
        ],
        "production_checklist": [
            "Back the server with Postgres (pgvector), not in-memory, so agent state survives restarts.",
            "Set the model-backend key on the server environment; never ship it in client code.",
            "Persist your own user_id -> agent_id map so you can reconnect deterministically.",
            "Keep core-memory blocks small; route bulk knowledge to archival passages.",
            "Pin letta-client and the server image to a matched version; the SDK surface evolves.",
            "Monitor token spend: each turn may trigger self-directed memory edits that cost tokens.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["letta-client==0.1", "letta==0.7"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["letta", "letta-letta-ai"],
        "related_glossary_slugs": ["memgpt", "agent-memory", "memory-augmented-agent", "context-window"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Letta vs a vector store for memory?", "answer": "A vector store is one piece (archival recall). Letta adds editable core memory the agent rewrites itself, plus server-side state so an agent reconnects by id across restarts. You get the store plus the management loop."},
            {"question": "Where does the model key live?", "answer": "On the SERVER. The client only sends messages; the server calls the model. A 'no provider configured' error almost always means the key is in your script instead of the server environment."},
            {"question": "Core memory vs archival memory?", "answer": "Core memory (persona/human blocks) is always in the context window and is small/bounded. Archival memory is unbounded and retrieved by semantic search only when relevant. Identity goes in core; facts go in archival."},
            {"question": "Is the SDK stable?", "answer": "It is pre-1.0 and method names have moved between releases. Pin letta-client and the server image together, and isolate each SDK call (as this starter does) so a rename is a one-line fix."},
        ],
        "github_url": "https://github.com/letta-ai/letta",
        "meta_title": "Letta (MemGPT) Stateful Agent Starter",
        "meta_description": "Run agents server-side with Letta: persistent memory blocks, archival semantic search, reconnect-by-id. Model key on the server, version-pinning notes.",
    },
    {
        "slug": "agent-episodic-memory-sqlite",
        "title": "Episodic Agent Memory From Scratch (SQLite + Embeddings)",
        "tldr": "The no-framework memory pattern: store episodes in SQLite with an embedding BLOB, recall by cosine similarity times recency decay, and distill old episodes into summaries. Everything inspectable with plain SQL.",
        "category": "memory-systems",
        "language": "python",
        "framework": "none (stdlib + sentence-transformers)",
        "tags": ["memory", "sqlite", "embeddings", "from-scratch"],
        "best_for_tags": ["self-hosted-agents", "local-first", "no-dependencies"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "You want agent memory without a vector DB or framework. Most needs are a table plus an embedding column: store episodes, recall by similarity blended with recency, periodically summarize. Ideal for local-first or single-node agents.",
        "when_not_to_use": "Skip past millions of episodes or high write concurrency from many processes (move to a real vector DB). Skip if you already run a managed memory service you trust.",
        "quick_start": "pip install sentence-transformers numpy anthropic && python episodic_memory.py",
        "full_code": '''"""Episodic agent memory: SQLite + embeddings, recall = similarity x recency.

No vector DB. Embeddings are stored as float32 BLOBs; recall ranks by
cosine_similarity * exp(-age_hours / HALFLIFE). reflect() distills the oldest
episodes into a 'summary' memory via one model call.
"""
from __future__ import annotations

import math
import os
import sqlite3
import time

import numpy as np
from anthropic import Anthropic
from sentence_transformers import SentenceTransformer


# ----------------- CONFIG -----------------

DB_PATH = os.environ.get("MEMORY_DB", "memory.db")
HALFLIFE_HOURS = float(os.environ.get("MEMORY_HALFLIFE_HOURS", "72"))
MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dim; changing this changes the BLOB width

_embedder = SentenceTransformer(MODEL_NAME)
_anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


# ----------------- SCHEMA -----------------

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")  # tolerate concurrent readers/writer
    conn.execute(
        """CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            text TEXT NOT NULL,
            ts REAL NOT NULL,
            kind TEXT NOT NULL DEFAULT 'episode',
            embedding BLOB NOT NULL
        )"""
    )
    return conn


def _embed(text: str) -> np.ndarray:
    vec = _embedder.encode([text], normalize_embeddings=True)[0]
    return vec.astype(np.float32)


# ----------------- WRITE -----------------

def add_episode(conn: sqlite3.Connection, role: str, text: str, kind: str = "episode") -> int:
    emb = _embed(text)
    cur = conn.execute(
        "INSERT INTO episodes (role, text, ts, kind, embedding) VALUES (?,?,?,?,?)",
        (role, text, time.time(), kind, emb.tobytes()),
    )
    conn.commit()
    return int(cur.lastrowid)


# ----------------- RECALL (similarity x recency) -----------------

def recall(conn: sqlite3.Connection, query: str, k: int = 4):
    q = _embed(query)
    now = time.time()
    scored = []
    for row in conn.execute("SELECT id, role, text, ts, embedding FROM episodes"):
        eid, role, text, ts, blob = row
        emb = np.frombuffer(blob, dtype=np.float32)
        if emb.shape != q.shape:
            continue  # dim mismatch from a model change; skip rather than crash
        sim = float(np.dot(q, emb))  # both normalized -> dot == cosine
        age_h = (now - ts) / 3600.0
        score = sim * math.exp(-age_h / HALFLIFE_HOURS)
        scored.append((score, role, text))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:k]


# ----------------- REFLECT (distill old episodes) -----------------

def reflect(conn: sqlite3.Connection, oldest_n: int = 20) -> str | None:
    rows = list(conn.execute(
        "SELECT text FROM episodes WHERE kind='episode' ORDER BY ts ASC LIMIT ?",
        (oldest_n,),
    ))
    if len(rows) < oldest_n:
        return None  # not enough history yet
    joined = "\\n".join(f"- {r[0]}" for r in rows)
    msg = _anthropic.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": f"Summarize these episodes into durable facts:\\n{joined}"}],
    )
    summary = "".join(b.text for b in msg.content if b.type == "text")
    add_episode(conn, role="system", text=summary, kind="summary")
    return summary


# ----------------- DEMO -----------------

def main() -> None:
    conn = connect()
    add_episode(conn, "user", "I'm allergic to peanuts and live in Lisbon.")
    add_episode(conn, "user", "I prefer trains over flights for trips under 6 hours.")
    add_episode(conn, "assistant", "Noted your peanut allergy and rail preference.")

    query = "plan dinner for the user"
    hits = recall(conn, query, k=2)
    context = "\\n".join(f"[{r}] {t}" for _, r, t in hits)
    print("System prompt memory block:\\n", context)
    conn.close()


if __name__ == "__main__":
    main()
''',
        "dependencies": [
            {"name": "sentence-transformers", "version": ">=3.0", "purpose": "Local embeddings (all-MiniLM-L6-v2, 384-dim)"},
            {"name": "numpy", "version": ">=1.26", "purpose": "Cosine similarity over float32 vectors"},
            {"name": "anthropic", "version": ">=0.40", "purpose": "One model call to distill old episodes in reflect()"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Key for the reflect() summarization call", "example": "sk-ant-..."},
            {"name": "MEMORY_DB", "required": False, "description": "SQLite file path", "example": "memory.db"},
            {"name": "MEMORY_HALFLIFE_HOURS", "required": False, "description": "Recency half-life for recall scoring", "example": "72"},
        ],
        "setup_steps": [
            "pip install sentence-transformers numpy anthropic",
            "export ANTHROPIC_API_KEY=sk-ant-...",
            "First run downloads the all-MiniLM-L6-v2 model (~90MB); allow time",
            "Run: python episodic_memory.py",
            "Inspect with any SQLite browser: SELECT role, text, kind FROM episodes;",
        ],
        "variations": [
            {"label": "Indexed ANN with sqlite-vec", "description": "Drop the full-table scan; use a vector index for large stores.", "code_snippet": "import sqlite_vec\\nconn.enable_load_extension(True); sqlite_vec.load(conn)\\nconn.execute('CREATE VIRTUAL TABLE vec_episodes USING vec0(embedding float[384])')\\n# then: SELECT id FROM vec_episodes WHERE embedding MATCH ? ORDER BY distance LIMIT k"},
            {"label": "Hybrid keyword + vector recall", "description": "Blend FTS5 keyword hits with cosine score.", "code_snippet": "conn.execute('CREATE VIRTUAL TABLE ep_fts USING fts5(text, content=episodes)')\\n# rank = 0.5*cosine + 0.5*bm25_normalized; union the two candidate sets before scoring"},
            {"label": "Importance scoring at write time", "description": "Let the model rate salience 1-10 and weight recall by it.", "code_snippet": "# imp = model_rate(text)  # 1..10\\n# store imp column; score = sim * exp(-age/HL) * (imp/10)\\n# keeps a 'remember this' fact alive longer than small talk"},
        ],
        "common_errors": [
            {"error_text": "ValueError: shapes not aligned in np.dot", "cause": "Switched embedding models; stored BLOBs have a different dimension.", "fix_snippet": "Embedding dim is fixed at write time. If you change MODEL_NAME, re-embed every row or version the table. The recall() guard skips mismatched rows so old data does not crash you."},
            {"error_text": "Relevant memory never surfaces", "cause": "Recency decay drowning similarity.", "fix_snippet": "Raise MEMORY_HALFLIFE_HOURS (slower decay) or reduce its weight. Tune so an old, highly-similar fact still beats a recent, off-topic one."},
            {"error_text": "database is locked", "cause": "Concurrent writers without WAL mode.", "fix_snippet": "Keep PRAGMA journal_mode=WAL (set in connect()). For many writer processes, serialize writes through one connection or a queue."},
            {"error_text": "Database file far larger than expected", "cause": "Embeddings stored as TEXT/JSON instead of a BLOB.", "fix_snippet": "Store vec.astype(np.float32).tobytes() in a BLOB column and read back with np.frombuffer. TEXT JSON is roughly 10x the size."},
        ],
        "production_checklist": [
            "Pin the embedding model; changing it silently invalidates every stored vector.",
            "Store vectors as float32 BLOBs (tobytes/frombuffer), never TEXT/JSON.",
            "Enable WAL mode and serialize writes if multiple processes write.",
            "Tune the recency half-life so relevance is not drowned by recency.",
            "Run reflect() on a schedule to cap context growth via summaries.",
            "Add an importance or pinned flag so critical facts are not decayed away.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["sentence-transformers==3.0", "numpy==1.26"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["agent-memory", "embedding", "cosine-similarity", "semantic-search", "memory-augmented-agent"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why not just use a vector DB?", "answer": "For up to ~100k episodes on one node, a SQLite table plus a numpy dot product is simpler, inspectable with plain SQL, and has no service to run. Move to a vector DB when scan time or write concurrency hurts."},
            {"question": "How does recency decay work?", "answer": "Each candidate's cosine similarity is multiplied by exp(-age_hours/halflife). A 72h half-life means a memory's weight halves every 3 days, so recent and relevant beats old and relevant unless similarity is much higher."},
            {"question": "What does reflect() buy me?", "answer": "It collapses many old raw episodes into a few durable summary facts, capping how much history you carry. Run it on a timer or after every N episodes; summaries are stored with kind='summary' so you can weight them differently."},
            {"question": "Cosine vs dot product here?", "answer": "Because vectors are L2-normalized at write and query time, the dot product equals cosine similarity. That lets recall use a single np.dot with no extra normalization per row."},
        ],
        "github_url": "https://github.com/UKPLab/sentence-transformers",
        "meta_title": "Episodic Agent Memory in SQLite Starter",
        "meta_description": "Build agent memory from scratch: SQLite episodes, float32 embedding BLOBs, recall by similarity x recency decay, and reflect() summaries. No vector DB.",
    },
    {
        "slug": "graphiti-temporal-knowledge-memory",
        "title": "Graphiti: Temporal Knowledge-Graph Memory for Agents",
        "tldr": "When 'what changed and when' matters, vector recall is not enough. Graphiti builds a bi-temporal graph from episodes: LLM-extracted entities, edges with valid-from/valid-to, contradictions invalidating old edges.",
        "category": "memory-systems",
        "language": "python",
        "framework": "Graphiti (Zep)",
        "tags": ["graphiti", "knowledge-graph", "temporal", "neo4j"],
        "best_for_tags": ["fact-tracking-agents", "audit-trails", "evolving-state"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "You need memory that tracks how facts change over time and answers point-in-time questions ('who led the team in March?'). Graphiti's bi-temporal edges and contradiction handling fit evolving business state where history matters.",
        "when_not_to_use": "Skip if plain semantic recall over text is enough; the graph and LLM extraction add cost and a Neo4j dependency. Skip for write-heavy ingest where per-episode extraction latency is unacceptable.",
        "quick_start": "docker run -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5 && pip install graphiti-core && python graphiti_memory.py",
        "full_code": '''"""Graphiti temporal-graph memory: entities + time-aware edges from episodes.

Async. Builds indices once, ingests business events that CHANGE over time, then
asks time-aware questions. Extraction defaults to OpenAI (OPENAI_API_KEY).
Calls are isolated; official patterns at help.getzep.com/graphiti.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType


# ----------------- CONFIG -----------------

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")
# OPENAI_API_KEY is read by Graphiti's default extractor LLM + embedder.


def now() -> datetime:
    return datetime.now(timezone.utc)


# ----------------- INGEST -----------------

async def add_event(graphiti: Graphiti, name: str, body: str, when: datetime) -> None:
    """Add one episode; Graphiti extracts entities/relations and time-stamps edges."""
    await graphiti.add_episode(
        name=name,
        episode_body=body,
        source=EpisodeType.text,
        source_description="business event",
        reference_time=when,
    )


# ----------------- RETRIEVE (hybrid: semantic + BM25 + graph) -----------------

async def ask(graphiti: Graphiti, query: str, limit: int = 5):
    """Hybrid search over the temporal graph; returns ranked edges (facts)."""
    results = await graphiti.search(query=query, num_results=limit)
    return [r.fact for r in results]


# ----------------- DEMO -----------------

async def run() -> None:
    graphiti = Graphiti(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        # Run ONCE per database; cheap to call again but required before first search.
        await graphiti.build_indices_and_constraints()

        # A fact that changes over time: Alice's team membership.
        await add_event(graphiti, "hire", "Alice joined the Payments team as an engineer.", now())
        await add_event(graphiti, "transfer", "Alice moved from Payments to the Fraud team.", now())

        # Time-aware answer: the move should invalidate the old edge, not delete it.
        print("Current team:", await ask(graphiti, "Which team is Alice on now?"))
        print("History:", await ask(graphiti, "What teams has Alice been on?"))
    except Exception as exc:
        print(f"Graphiti error (is Neo4j up at {NEO4J_URI}?): {exc}")
        raise
    finally:
        await graphiti.close()  # always release the Neo4j driver


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
''',
        "dependencies": [
            {"name": "graphiti-core", "version": ">=0.5", "purpose": "Bi-temporal knowledge-graph memory engine"},
            {"name": "neo4j", "version": ">=5.0", "purpose": "Graph database backend (run server 5.x via Docker)"},
        ],
        "env_vars": [
            {"name": "NEO4J_URI", "required": False, "description": "Bolt URI of the Neo4j server", "example": "bolt://localhost:7687"},
            {"name": "NEO4J_USER", "required": True, "description": "Neo4j username", "example": "neo4j"},
            {"name": "NEO4J_PASSWORD", "required": True, "description": "Neo4j password", "example": "password"},
            {"name": "OPENAI_API_KEY", "required": True, "description": "Used by Graphiti's default extractor LLM and embedder", "example": "sk-..."},
        ],
        "setup_steps": [
            "Start Neo4j: docker run -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/password neo4j:5",
            "pip install graphiti-core",
            "export OPENAI_API_KEY, NEO4J_USER, NEO4J_PASSWORD",
            "Run once to build indices, then ingest: python graphiti_memory.py",
            "Browse the graph at http://localhost:7474 to see entities and time-stamped edges",
        ],
        "variations": [
            {"label": "FalkorDB backend", "description": "Use FalkorDB instead of Neo4j as the graph store.", "code_snippet": "from graphiti_core.driver.falkordb_driver import FalkorDriver\\ndriver = FalkorDriver(host='localhost', port=6379)\\ngraphiti = Graphiti(graph_driver=driver)  # see help.getzep.com for the current driver API"},
            {"label": "Custom entity types", "description": "Constrain extraction with Pydantic models.", "code_snippet": "from pydantic import BaseModel\\nclass Employee(BaseModel):\\n    title: str | None = None\\nawait graphiti.add_episode(..., entity_types={'Employee': Employee})"},
            {"label": "Community detection", "description": "Periodically build summary 'community' nodes over clusters.", "code_snippet": "await graphiti.build_communities()  # groups related entities into summary nodes for coarse recall"},
        ],
        "common_errors": [
            {"error_text": "ServiceUnavailable / connection refused (bolt)", "cause": "Neo4j container not ready or wrong auth.", "fix_snippet": "Wait for Neo4j to report healthy before connecting; verify NEO4J_AUTH matches NEO4J_USER/PASSWORD. The Bolt port is 7687, the browser is 7474."},
            {"error_text": "Extraction cost spikes on bulk ingest", "cause": "One LLM extraction call per episode at full model price.", "fix_snippet": "Batch related events into fewer, larger episodes and configure a cheaper extractor model. Ingest is the expensive path, not search."},
            {"error_text": "Search is slow or returns nothing", "cause": "Indices/constraints never built.", "fix_snippet": "Call build_indices_and_constraints() once per database before searching. Without it, hybrid retrieval has no indexes to use."},
            {"error_text": "Treating Graphiti as a plain vector DB", "cause": "Expecting raw similarity and ignoring the temporal graph.", "fix_snippet": "Its value is time-aware edges and contradiction handling. Ask point-in-time questions ('team now' vs 'team history'); if you only need similarity, a vector store is simpler."},
        ],
        "production_checklist": [
            "Run build_indices_and_constraints() exactly once per database, before first search.",
            "Pass an explicit reference_time per episode so bi-temporal edges are correct.",
            "Batch ingest and use a cheaper extractor model to control LLM cost.",
            "Always await graphiti.close() to release the Neo4j driver.",
            "Size Neo4j (heap/page cache) for your graph; back it up like any database.",
            "Pin graphiti-core; the driver and search APIs are still evolving.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["graphiti-core==0.5", "neo4j==5.0"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["getzep-graphiti", "zep"],
        "related_glossary_slugs": ["knowledge-graph", "agent-memory", "graph-rag", "hybrid-search"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Graphiti vs a vector store for memory?", "answer": "A vector store answers 'what is similar'. Graphiti answers 'what is true now and what was true then' by keeping time-stamped edges. When a fact changes, it invalidates the old edge with a valid-to timestamp instead of deleting it, preserving history."},
            {"question": "What is bi-temporal?", "answer": "Edges carry two time axes: when the fact was valid in the world (valid-from/valid-to) and when the system learned it. That lets you answer point-in-time queries and audit what the agent knew at a given moment."},
            {"question": "Why does ingest cost more than search?", "answer": "Each episode triggers an LLM call to extract entities and relations, so bulk loading is the expensive path. Batch related events and use a cheaper extractor model; search itself is graph + index lookups."},
            {"question": "Do I have to use Neo4j?", "answer": "Neo4j 5.x is the common backend, but Graphiti also supports FalkorDB via an alternate driver. Pick based on what you already operate; the memory API is the same on top."},
        ],
        "github_url": "https://github.com/getzep/graphiti",
        "meta_title": "Graphiti Temporal Knowledge-Graph Memory Starter",
        "meta_description": "Agent memory that tracks change over time: Graphiti builds a bi-temporal knowledge graph with valid-from/valid-to edges and contradiction handling on Neo4j.",
    },
]
