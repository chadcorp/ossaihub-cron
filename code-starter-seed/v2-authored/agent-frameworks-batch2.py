"""Agent framework starters — batch 2: LangGraph, OpenAI Assistants."""

RECORDS = [
    {
        "slug": "langgraph-state-machine-agent",
        "title": "LangGraph State-Machine Agent",
        "tldr": "Build an explicit state-machine agent in LangGraph: nodes for steps, edges with conditional routing, persistent state across turns. Better for complex multi-step flows than linear tool-calling loops.",
        "category": "agent-frameworks",
        "language": "python",
        "framework": "LangGraph",
        "tags": ["langgraph", "state-machine", "agents", "routing"],
        "best_for_tags": ["complex-agents", "explicit-control", "checkpointing"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "When the agent's flow has explicit states/routing (e.g., classify → research → write → critique → finalize) and a linear tool loop doesn't fit. LangGraph makes the state machine explicit and inspectable.",
        "when_not_to_use": "Skip for simple tool-calling agents (use LangChain's bind_tools). Skip when you don't need explicit state — overhead vs simpler patterns.",
        "quick_start": "pip install langgraph langchain-openai && OPENAI_API_KEY=sk-... python graph_agent.py",
        "full_code": '''"""LangGraph state-machine agent.

Flow:
  START → classify → (research | direct_answer | escalate) → finalize → END

Each node updates the shared state. Edges check state to decide routing.
"""
from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver


# ----------------- STATE -----------------

class AgentState(TypedDict):
    user_question: str
    intent: str | None              # classified by router
    research_notes: list[str]
    answer: str | None
    needs_escalation: bool
    iterations: int


# ----------------- LLM -----------------

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# ----------------- NODES -----------------

def classify_intent(state: AgentState) -> dict:
    """Decide if this is a question for research, direct answer, or escalation."""
    q = state["user_question"]
    resp = llm.invoke([
        {"role": "system", "content": "Classify the user's question as one of: simple, needs_research, needs_human. Output one word."},
        {"role": "user", "content": q},
    ])
    intent = resp.content.strip().lower()
    return {"intent": intent}


def research(state: AgentState) -> dict:
    """Do (fake) research; in real use, this calls tools."""
    q = state["user_question"]
    resp = llm.invoke([
        {"role": "system", "content": "Imagine you researched this question; produce 2-3 bullet notes."},
        {"role": "user", "content": q},
    ])
    notes = [line.strip() for line in resp.content.split("\\n") if line.strip()]
    return {"research_notes": state["research_notes"] + notes, "iterations": state["iterations"] + 1}


def direct_answer(state: AgentState) -> dict:
    resp = llm.invoke([
        {"role": "system", "content": "Answer directly and concisely."},
        {"role": "user", "content": state["user_question"]},
    ])
    return {"answer": resp.content}


def synthesize(state: AgentState) -> dict:
    notes = "\\n".join(state["research_notes"])
    resp = llm.invoke([
        {"role": "system", "content": "Synthesize an answer using these research notes."},
        {"role": "user", "content": f"Question: {state['user_question']}\\n\\nNotes:\\n{notes}"},
    ])
    return {"answer": resp.content}


def escalate(state: AgentState) -> dict:
    return {"answer": "Escalated to human review.", "needs_escalation": True}


# ----------------- ROUTING -----------------

def route_after_classify(state: AgentState) -> Literal["research", "direct_answer", "escalate"]:
    if "research" in state["intent"]:
        return "research"
    if "human" in state["intent"]:
        return "escalate"
    return "direct_answer"


def route_after_research(state: AgentState) -> Literal["research", "synthesize"]:
    # Could loop research if needed; we'll synthesize after 1 round
    if state["iterations"] >= 1:
        return "synthesize"
    return "research"


# ----------------- BUILD GRAPH -----------------

graph = StateGraph(AgentState)
graph.add_node("classify_intent", classify_intent)
graph.add_node("research", research)
graph.add_node("direct_answer", direct_answer)
graph.add_node("synthesize", synthesize)
graph.add_node("escalate", escalate)

graph.add_edge(START, "classify_intent")
graph.add_conditional_edges("classify_intent", route_after_classify)
graph.add_conditional_edges("research", route_after_research)
graph.add_edge("direct_answer", END)
graph.add_edge("synthesize", END)
graph.add_edge("escalate", END)

# Compile with checkpointing — state persists across invocations
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)


# ----------------- USAGE -----------------

def run(question: str, thread_id: str = "demo") -> str:
    initial_state: AgentState = {
        "user_question": question,
        "intent": None,
        "research_notes": [],
        "answer": None,
        "needs_escalation": False,
        "iterations": 0,
    }
    config = {"configurable": {"thread_id": thread_id}}
    final = app.invoke(initial_state, config=config)
    return final["answer"]


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "What is RAG and when do I use it?"
    print(run(q))
''',
        "dependencies": [
            {"name": "langgraph", "version": ">=0.2", "purpose": "State-machine framework"},
            {"name": "langchain-openai", "version": ">=0.2", "purpose": "OpenAI LLM"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install langgraph langchain-openai",
            "export OPENAI_API_KEY=sk-...",
            "python graph_agent.py 'your question'",
        ],
        "variations": [
            {
                "label": "Persistent state (Postgres)",
                "description": "Replace MemorySaver with PostgresSaver.",
                "code_snippet": "from langgraph.checkpoint.postgres import PostgresSaver\\ncheckpointer = PostgresSaver(conn_string='postgresql://...')",
            },
            {
                "label": "Human-in-the-loop",
                "description": "Pause for human approval at a node.",
                "code_snippet": "app = graph.compile(checkpointer=checkpointer, interrupt_before=['escalate'])\\n# Then `app.invoke()` returns; human reviews; `app.invoke(None, config)` resumes.",
            },
            {
                "label": "Streaming events",
                "description": "Yield state updates as they happen.",
                "code_snippet": "for event in app.stream(initial_state, config):\\n    print(event)",
            },
            {
                "label": "Subgraphs",
                "description": "Compose multiple graphs.",
                "code_snippet": "# A research subgraph can be a node in the parent graph.\\nparent_graph.add_node('research_phase', research_subgraph)",
            },
        ],
        "common_errors": [
            {
                "error_text": "TypeError: 'NoneType' object is not subscriptable",
                "cause": "State key accessed before being set.",
                "fix_snippet": "Initialize all fields in initial_state; use Optional[X] = None for fields populated later. TypedDict guards type, not presence.",
            },
            {
                "error_text": "Cycle detected: research → research → ...",
                "cause": "Routing function never returns END or non-research target.",
                "fix_snippet": "Add a max-iteration check in the routing function: return 'synthesize' if state['iterations'] >= MAX.",
            },
            {
                "error_text": "Thread state persists between unrelated calls",
                "cause": "Same thread_id for different conversations.",
                "fix_snippet": "Use unique thread_id per user/conversation. Or call app.delete_state(config) when conversation ends.",
            },
            {
                "error_text": "Node updates don't accumulate",
                "cause": "Returned dict overwrites; need to use list-accumulating annotation.",
                "fix_snippet": "For list fields, use: Annotated[list[str], operator.add] in TypedDict. Then returning {'notes': [new]} appends.",
            },
        ],
        "production_checklist": [
            "Use a real checkpointer (Postgres, Redis); MemorySaver is for dev.",
            "Set thread_id per conversation; never share state inadvertently.",
            "Add max-iteration guards on any cyclic edge.",
            "Test each node in isolation (it's just a function taking/returning dict).",
            "Visualize the graph: app.get_graph().draw_ascii() for debugging.",
            "Pin LangGraph version; API still evolving.",
            "Log state at each node transition for debugging.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["langgraph==0.2.50", "langchain-openai==0.2.5"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["langgraph"],
        "related_glossary_slugs": ["state-machine", "agent-graph", "checkpointing"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "LangGraph vs LangChain agents?",
                "answer": "LangChain agents: linear tool-calling loops. LangGraph: explicit state machines with routing. Use LangGraph when the flow isn't ‘keep calling tools until done’.",
            },
            {
                "question": "When is the state-machine overhead worth it?",
                "answer": "When you have distinct phases (classify-research-write-critique), human-in-the-loop pauses, or branching logic. For simple agents, linear is simpler.",
            },
            {
                "question": "Can I visualize the graph?",
                "answer": "Yes — app.get_graph().draw_ascii() for terminal; app.get_graph().draw_png() for image. Helpful when reasoning about complex flows.",
            },
            {
                "question": "Multi-agent with LangGraph?",
                "answer": "Yes — multiple agents as subgraphs, or one graph with multiple LLM-role nodes. LangGraph is well-suited for multi-agent patterns.",
            },
        ],
        "github_url": "https://github.com/langchain-ai/langgraph",
        "meta_title": "LangGraph State-Machine Agent — Starter",
        "meta_description": "Explicit state-machine agent in LangGraph: nodes, conditional routing, checkpointing, human-in-the-loop. For complex multi-step flows.",
    },
    {
        "slug": "openai-assistants-api-quickstart",
        "title": "OpenAI Assistants API Quickstart",
        "tldr": "Set up an OpenAI Assistant with file search, code interpreter, and persistent threads. Stateful agent without managing context — OpenAI handles threads, tools, and retrieval.",
        "category": "agent-frameworks",
        "language": "python",
        "framework": "OpenAI Assistants",
        "tags": ["openai-assistants", "agent", "stateful", "file-search"],
        "best_for_tags": ["managed-agents", "file-qa", "code-interpreter"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When you want a stateful agent without managing conversation context yourself. Especially good for file-Q&A (built-in retrieval) and code execution (built-in interpreter).",
        "when_not_to_use": "Skip for non-OpenAI workloads (locked in). Skip when you need full control over retrieval, tools, or prompts — Assistants are opinionated.",
        "quick_start": "pip install openai && OPENAI_API_KEY=sk-... python assistant.py",
        "full_code": '''"""OpenAI Assistants API: stateful agent with file search + code interpreter.

Workflow:
  1. Create assistant (one-time setup)
  2. Upload files for retrieval
  3. Create thread (per user/conversation)
  4. Add user message
  5. Run the assistant
  6. Poll until complete
  7. Read messages
"""
from __future__ import annotations

import time

from openai import OpenAI

client = OpenAI()


# ----------------- 1. CREATE ASSISTANT (one-time) -----------------

def create_assistant():
    assistant = client.beta.assistants.create(
        name="OSS AI Hub Research Helper",
        instructions=(
            "You help users navigate AI tooling. Use file_search to find info in our knowledge base. "
            "Use code_interpreter for any calculations or chart generation."
        ),
        model="gpt-4o",
        tools=[
            {"type": "file_search"},
            {"type": "code_interpreter"},
        ],
    )
    return assistant


# ----------------- 2. UPLOAD FILES + ATTACH TO VECTOR STORE -----------------

def attach_files(assistant_id: str, file_paths: list[str]):
    # Create a vector store
    vs = client.beta.vector_stores.create(name="ossaihub-kb")

    # Upload files
    file_streams = [open(p, "rb") for p in file_paths]
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vs.id, files=file_streams,
    )
    print(f"Upload status: {file_batch.status}; files: {file_batch.file_counts}")

    # Attach vector store to assistant
    client.beta.assistants.update(
        assistant_id=assistant_id,
        tool_resources={"file_search": {"vector_store_ids": [vs.id]}},
    )
    return vs.id


# ----------------- 3-7. RUN A CONVERSATION -----------------

def chat(assistant_id: str, user_message: str, thread_id: str | None = None) -> tuple[str, str]:
    """Send a message, run assistant, return (response_text, thread_id)."""
    if thread_id is None:
        thread = client.beta.threads.create()
        thread_id = thread.id

    client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=user_message
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )

    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread_id, order="desc", limit=1)
        msg = messages.data[0]
        content = msg.content[0].text.value if msg.content else "(empty)"
        return content, thread_id

    return f"[run ended: {run.status}]", thread_id


# ----------------- USAGE -----------------

if __name__ == "__main__":
    assistant = create_assistant()
    print(f"Assistant: {assistant.id}")

    # Optional: attach files
    # attach_files(assistant.id, ["docs/intro.md", "docs/architecture.md"])

    # Conversation
    thread_id = None
    for q in ["What is RAG?", "How does it differ from fine-tuning?"]:
        response, thread_id = chat(assistant.id, q, thread_id)
        print(f"\\nQ: {q}\\nA: {response}")
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "Assistants API"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai",
            "export OPENAI_API_KEY=sk-...",
            "python assistant.py",
            "Save assistant.id; reuse across runs (don't re-create).",
        ],
        "variations": [
            {
                "label": "Streaming responses",
                "description": "Stream the run's output.",
                "code_snippet": "with client.beta.threads.runs.stream(thread_id=tid, assistant_id=aid) as stream:\\n    for event in stream:\\n        if event.event == 'thread.message.delta':\\n            print(event.data.delta.content[0].text.value, end='')",
            },
            {
                "label": "Custom tools",
                "description": "Add function calling.",
                "code_snippet": "tools=[{'type': 'function', 'function': {'name': 'get_weather', 'description': '...', 'parameters': {...}}}]\\n# Then handle requires_action in run polling loop",
            },
            {
                "label": "Multi-user thread isolation",
                "description": "Per-user threads.",
                "code_snippet": "# Store thread_id per user in your DB. Always pass user's thread_id; never share.",
            },
        ],
        "common_errors": [
            {
                "error_text": "Run never completes (status stuck on in_progress)",
                "cause": "Tool function requires action.",
                "fix_snippet": "Use create_and_poll() for simple cases; for function tools, poll manually and handle status='requires_action' by submitting tool outputs.",
            },
            {
                "error_text": "Files not appearing in file search",
                "cause": "Vector store not attached to assistant or run.",
                "fix_snippet": "Verify assistant.tool_resources.file_search.vector_store_ids; or pass tool_resources per-run for thread-specific files.",
            },
            {
                "error_text": "Costs blowing up",
                "cause": "Assistants store conversation history, retrievals — billed per token.",
                "fix_snippet": "Periodically delete old threads; cap thread length; consider per-conversation cleanup.",
            },
            {
                "error_text": "Code interpreter output not accessible",
                "cause": "Outputs are attached as files.",
                "fix_snippet": "Check message.attachments for files generated by code interpreter; download via client.files.content(file_id).",
            },
        ],
        "production_checklist": [
            "Reuse assistant.id; don't create new ones per request.",
            "Per-user thread_id; isolate properly.",
            "Cap thread length; old threads inflate costs.",
            "Test file_search quality on your data — it's a black box.",
            "Pin OpenAI SDK; Assistants API has evolved across versions.",
            "Plan for non-completion: status can stick on requires_action, expired, etc.",
            "Cost monitor: Assistants bill differently from chat completions.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o", "gpt-4o-mini"],
            "library_versions": ["openai==1.51.0 (Assistants v2)"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["openai-assistants", "thread", "file-search"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Assistants API vs Chat Completions + RAG?",
                "answer": "Assistants: managed retrieval + state + tools, less control. Chat + RAG: more setup, more control, provider-agnostic. Assistants if you're OpenAI-only and want fast setup; Chat + RAG for production-grade control.",
            },
            {
                "question": "Is it production-ready?",
                "answer": "Yes — but the black-box file_search means you can't easily tune retrieval. For high-stakes RAG, custom retrieval beats Assistants' built-in.",
            },
            {
                "question": "Cost model?",
                "answer": "Pay for: model tokens (same as chat), file_search storage + queries, code interpreter sessions. Tends to be 2-3x chat-only for the same conversation. Measure for your use case.",
            },
            {
                "question": "Can I switch to Anthropic?",
                "answer": "Not directly — Assistants is OpenAI-specific. Migration means rebuilding with Anthropic-native or via a framework (LangChain, LangGraph) that wraps both.",
            },
        ],
        "github_url": "https://github.com/openai/openai-python",
        "meta_title": "OpenAI Assistants API Quickstart — Starter",
        "meta_description": "Stateful OpenAI Assistants with file search + code interpreter + persistent threads. Managed agent without context juggling.",
    },
]
