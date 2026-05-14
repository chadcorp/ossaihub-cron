"""Memory systems starters — Mem0, conversation memory, episodic stores."""

RECORDS = [
    {
        "slug": "conversation-memory-summarizer",
        "title": "Conversation Memory With Rolling Summary",
        "tldr": "Long-conversation memory pattern: keep the last N turns verbatim, summarize earlier turns into a running ‘what we've established’ block. Stays under context limit indefinitely.",
        "category": "memory-systems",
        "language": "python",
        "framework": "OpenAI SDK",
        "tags": ["memory", "long-context", "summarization", "conversation"],
        "best_for_tags": ["chat-applications", "long-conversations", "context-management"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Any chat application where conversations may exceed the model's context window (or where cost of sending the full history is undesirable). Pattern keeps the conversation feeling continuous without unbounded growth.",
        "when_not_to_use": "Skip for single-turn or very short interactions. Skip for tasks requiring perfect recall of every exchanged token (legal, compliance) — summarization is lossy.",
        "quick_start": "pip install openai && OPENAI_API_KEY=sk-... python convo_memory.py",
        "full_code": '''"""Rolling-summary conversation memory.

Layout:
  system_prompt + summary_so_far + last_N_verbatim_turns + new_user_message

When the verbatim window exceeds N, oldest turns are merged into summary.
The summary is regenerated with the new content; never grows unbounded.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from openai import OpenAI

client = OpenAI()


@dataclass
class Turn:
    role: Literal["user", "assistant"]
    content: str


@dataclass
class ConversationMemory:
    system_prompt: str
    verbatim_window: int = 8           # keep this many recent turns word-for-word
    summary_so_far: str = ""           # rolling summary of older turns
    turns: list[Turn] = field(default_factory=list)
    max_summary_chars: int = 2000      # cap on summary so it doesn't bloat

    def append(self, role: Literal["user", "assistant"], content: str) -> None:
        self.turns.append(Turn(role=role, content=content))
        self._maybe_summarize()

    def _maybe_summarize(self) -> None:
        """When verbatim turns exceed window, summarize oldest into rolling summary."""
        if len(self.turns) <= self.verbatim_window:
            return
        overflow = self.turns[: -self.verbatim_window]
        self.turns = self.turns[-self.verbatim_window :]

        new_content = "\\n".join(f"{t.role}: {t.content}" for t in overflow)
        prompt = f"""You maintain a running summary of a conversation.

PREVIOUS SUMMARY:
{self.summary_so_far or '(empty)'}

NEW TURNS TO INCORPORATE:
{new_content}

Update the summary to include the new information. Keep it under {self.max_summary_chars} characters.
Preserve:
  - Facts the user shared (preferences, identifiers, decisions)
  - Open questions or commitments
  - Anything the user later referenced ("as I said earlier")
Discard:
  - Pleasantries, filler
  - Old reasoning that's been superseded

Output ONLY the new summary, no preamble."""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        self.summary_so_far = resp.choices[0].message.content.strip()

    def build_messages(self, new_user_message: str) -> list[dict]:
        """Construct the messages array to send to the LLM."""
        msgs: list[dict] = [{"role": "system", "content": self.system_prompt}]
        if self.summary_so_far:
            msgs.append({
                "role": "system",
                "content": f"# Conversation summary so far\\n\\n{self.summary_so_far}",
            })
        for t in self.turns:
            msgs.append({"role": t.role, "content": t.content})
        msgs.append({"role": "user", "content": new_user_message})
        return msgs


# ----------------- USAGE -----------------

def chat_loop():
    memory = ConversationMemory(
        system_prompt="You are a helpful assistant who remembers what the user has shared.",
        verbatim_window=6,
    )
    print("Chat (Ctrl+C to exit)")
    while True:
        try:
            user_msg = input("\\nyou: ").strip()
            if not user_msg:
                continue
            messages = memory.build_messages(user_msg)
            resp = client.chat.completions.create(
                model="gpt-4o-mini", messages=messages, temperature=0.7
            )
            reply = resp.choices[0].message.content
            print(f"\\nbot: {reply}")
            memory.append("user", user_msg)
            memory.append("assistant", reply)
            print(f"\\n(memory: summary={len(memory.summary_so_far)} chars, verbatim={len(memory.turns)} turns)")
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    chat_loop()
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "LLM for both chat and summarization"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai",
            "export OPENAI_API_KEY=sk-...",
            "python convo_memory.py",
            "Try a long conversation; watch the summary grow as verbatim turns get rolled in.",
        ],
        "variations": [
            {
                "label": "Per-user persistent",
                "description": "Save memory to disk per user.",
                "code_snippet": "import json, pathlib\\ndef save(memory, user_id): pathlib.Path(f'memory/{user_id}.json').write_text(json.dumps({'summary': memory.summary_so_far, 'turns': [t.__dict__ for t in memory.turns]}))",
            },
            {
                "label": "Async summarization",
                "description": "Don't block on summary.",
                "code_snippet": "# Summarize in background; if next turn arrives before summary done, use stale summary + extra verbatim turns.",
            },
            {
                "label": "Fact extraction in addition",
                "description": "Pull structured facts alongside summary.",
                "code_snippet": "# Second prompt to extract: {'user_facts': {...}, 'commitments': [...]}\\n# Maintain alongside summary; surface in system prompt for downstream tasks.",
            },
            {
                "label": "Different model for summarization",
                "description": "Use cheaper model for summary, expensive for chat.",
                "code_snippet": "# In _maybe_summarize, use 'gpt-4o-mini' or even local Llama. Chat uses 'gpt-4o'.",
            },
        ],
        "common_errors": [
            {
                "error_text": "Summary forgets important info",
                "cause": "Summarization prompt too aggressive.",
                "fix_snippet": "Tune the summarization prompt to preserve specific categories (preferences, decisions, IDs). Test with a synthetic conversation that includes a fact stated early.",
            },
            {
                "error_text": "Latency spike when window overflows",
                "cause": "Sync summarization blocks the next reply.",
                "fix_snippet": "Use async variation, OR summarize only when window overflows by 2+ (don't summarize every single turn after threshold).",
            },
            {
                "error_text": "Summary grows past max_summary_chars",
                "cause": "Summarizer ignores the limit.",
                "fix_snippet": "Enforce in code: if len(new_summary) > max_summary_chars: truncate or re-summarize. Re-pin the limit in the prompt.",
            },
            {
                "error_text": "User contradicts something in summary",
                "cause": "Stale facts in summary.",
                "fix_snippet": "Add to summarization prompt: ‘when new turns contradict prior summary, the new turns win.’ Or maintain a separate ‘corrections’ log.",
            },
        ],
        "production_checklist": [
            "Persist memory per user; in-memory only fails on process restart.",
            "Set sane max_summary_chars; uncapped summaries balloon token cost.",
            "Cache the summary; only regenerate on window overflow.",
            "Log summary changes for debugging surprise behavior.",
            "Consider: what's lost when summarizing? Test on real conversations.",
            "Run summarizer with deterministic temperature (0) for consistency.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["conversation-memory", "summarization", "context-window"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why summarize instead of just sending the full history?",
                "answer": "Cost + context limits. A 100-turn conversation hits both. Summarization keeps the conversation feeling continuous while staying bounded.",
            },
            {
                "question": "Will summaries lose nuance?",
                "answer": "Yes — that's the trade. For most chat use cases, structural memory is fine; only specific facts and decisions need preservation. For compliance/legal use cases, store full transcripts separately.",
            },
            {
                "question": "How big should verbatim_window be?",
                "answer": "6-12 turns. Smaller = aggressive summarization (cheaper, more loss). Larger = better recall (more tokens, more cost). Tune per app.",
            },
            {
                "question": "How does this compare to Mem0 / Letta?",
                "answer": "Those are richer (structured facts + episodic memory + queries). This is the simple pattern. For complex apps, Mem0/Letta. For most chat: this is sufficient.",
            },
        ],
        "github_url": "",
        "meta_title": "Conversation Memory With Rolling Summary — Starter",
        "meta_description": "Long-conversation memory pattern: keep N recent turns verbatim, summarize older turns into a rolling ‘context so far’ block. Bounded forever.",
    },
    {
        "slug": "mem0-personal-assistant-memory",
        "title": "Mem0 Personal Assistant Memory",
        "tldr": "Use Mem0 to give an assistant per-user memory: stores facts the user shared, retrieves relevant ones per query, with explicit fact-update vs fact-add semantics.",
        "category": "memory-systems",
        "language": "python",
        "framework": "Mem0",
        "tags": ["mem0", "memory", "personal-assistant", "facts"],
        "best_for_tags": ["personal-assistants", "user-preferences", "long-term-memory"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When building a personal assistant that needs to remember facts about the user across sessions — preferences, history, named entities. Mem0 handles the storage and retrieval; you connect it to your LLM.",
        "when_not_to_use": "Skip for stateless apps (Q&A, search). Skip for multi-user / multi-tenant scenarios without proper user isolation (Mem0 supports it, but you need to wire user_id correctly).",
        "quick_start": "pip install mem0ai openai && MEM0_API_KEY=... OPENAI_API_KEY=sk-... python assistant.py",
        "full_code": '''"""Mem0-powered personal assistant.

Pattern:
  1. Before each LLM call, query Mem0 for relevant memories about the user.
  2. Inject memories into system prompt.
  3. After the response, ask Mem0 to update memories based on the conversation.

Mem0 handles:
  - Fact extraction from natural conversation
  - Updates ('user changed their job' overrides old)
  - Vector search to retrieve relevant memories per query
"""
from __future__ import annotations

import os

from mem0 import MemoryClient
from openai import OpenAI

client = OpenAI()
memory = MemoryClient(api_key=os.environ["MEM0_API_KEY"])


SYSTEM_PROMPT = """You are a personal assistant. Use the user's stored memories to provide personalized responses.
If the user shares new information (preferences, plans, facts), the memory layer will store it automatically.
Don't ask the user to repeat things they've already told you."""


def chat(user_id: str, user_message: str) -> str:
    # 1. Retrieve relevant memories
    relevant = memory.search(query=user_message, user_id=user_id, limit=5)
    memory_block = "\\n".join(f"- {m['memory']}" for m in relevant) if relevant else "(none)"

    # 2. Build prompt with memories
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"# Known about this user\\n{memory_block}"},
        {"role": "user", "content": user_message},
    ]

    # 3. Generate response
    resp = client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, temperature=0.7
    )
    assistant_reply = resp.choices[0].message.content

    # 4. Let Mem0 extract any new facts from the conversation
    memory.add(
        messages=[
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_reply},
        ],
        user_id=user_id,
    )

    return assistant_reply


def get_all_memories(user_id: str) -> list[dict]:
    """For debugging or user-facing ‘what do you know about me?’."""
    return memory.get_all(user_id=user_id)


def delete_memory(memory_id: str) -> None:
    """User-initiated forgetting."""
    memory.delete(memory_id=memory_id)


if __name__ == "__main__":
    user_id = "user_demo_1"

    # Session 1
    print(chat(user_id, "Hi! I'm Jane. I'm a software engineer and I'm vegan."))
    print(chat(user_id, "Tomorrow is my birthday."))

    # Pretend session ended; new session
    print("\\n--- new session ---")
    print(chat(user_id, "Suggest a celebratory meal for tomorrow."))
    # Should suggest a vegan birthday meal — uses both stored memories.

    # User wants to see what's stored
    print("\\n--- memories ---")
    for m in get_all_memories(user_id):
        print(f"- {m.get('memory')}")
''',
        "dependencies": [
            {"name": "mem0ai", "version": ">=0.1.40", "purpose": "Memory layer"},
            {"name": "openai", "version": ">=1.40", "purpose": "Underlying LLM"},
        ],
        "env_vars": [
            {"name": "MEM0_API_KEY", "required": True, "description": "Mem0 API key (or self-host)", "example": "mem0-..."},
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "Sign up at mem0.ai or self-host.",
            "pip install mem0ai openai",
            "export MEM0_API_KEY=... OPENAI_API_KEY=sk-...",
            "python assistant.py",
            "Watch memories accumulate across sessions.",
        ],
        "variations": [
            {
                "label": "Self-hosted with Qdrant + Postgres",
                "description": "No managed service.",
                "code_snippet": "from mem0 import Memory\\nmemory = Memory.from_config({\\n  'vector_store': {'provider': 'qdrant', 'config': {'host': 'localhost', 'port': 6333}},\\n  'graph_store': {'provider': 'neo4j', 'config': {...}},\\n  'llm': {'provider': 'openai', 'config': {'model': 'gpt-4o-mini'}}\\n})",
            },
            {
                "label": "Memory categories",
                "description": "Categorize memories at write.",
                "code_snippet": "memory.add(messages=..., user_id=user_id, metadata={'category': 'preferences'})\\nrelevant = memory.search(query=..., user_id=..., filters={'category': 'preferences'})",
            },
            {
                "label": "Agent memory (team / project)",
                "description": "Team-scoped, not just user.",
                "code_snippet": "memory.add(messages=..., agent_id='team_acme', user_id=user_id)\\n# Retrieves both user-specific and team-shared memories",
            },
            {
                "label": "Memory expiration",
                "description": "Stale memories auto-delete.",
                "code_snippet": "memory.add(..., metadata={'expires_at': '2026-12-31T00:00:00Z'})\\n# Custom cron or middleware removes expired entries.",
            },
        ],
        "common_errors": [
            {
                "error_text": "Memory layer extracts wrong facts",
                "cause": "User said 'I might be vegan' — got stored as 'user is vegan'.",
                "fix_snippet": "Tune the extraction prompt or post-process. Add user-facing review: surface new memories, let user confirm/edit before persisting.",
            },
            {
                "error_text": "Latency spikes",
                "cause": "Search + add both make LLM calls.",
                "fix_snippet": "Run memory.add() async in the background after responding. Cache memory.search() for common queries.",
            },
            {
                "error_text": "Memories contradict each other",
                "cause": "User changes their mind; old memory not superseded.",
                "fix_snippet": "Mem0 handles updates; verify it's working. Check memory.get_all() periodically for stale contradictions; can prune manually.",
            },
            {
                "error_text": "Privacy concerns",
                "cause": "PII stored in cloud memory service.",
                "fix_snippet": "Self-host Mem0 with your own vector + graph store. Or restrict what kinds of memories can be stored (filter PII before memory.add).",
            },
        ],
        "production_checklist": [
            "Set user_id consistently — confused user IDs = leaked memories.",
            "Show users what's stored (transparency); let them delete.",
            "Audit memory contents periodically for stale or wrong facts.",
            "Run memory.add async; don't block the user's response.",
            "Self-host if you handle sensitive PII.",
            "Test ‘forget me’ flow end-to-end before promising privacy guarantees.",
            "Cache common memory searches to control LLM cost.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["mem0ai==0.1.45", "openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["mem0"],
        "related_glossary_slugs": ["memory-system", "personal-assistant", "long-term-memory"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Mem0 vs Letta vs raw vector store?",
                "answer": "Mem0: opinionated, fact extraction built-in. Letta (MemGPT): more agent-focused, multi-tier memory. Raw vector store: full control, more glue code. Pick based on whether you want batteries-included.",
            },
            {
                "question": "How do I handle ‘forget me’ requests?",
                "answer": "memory.delete_all(user_id=...) removes all entries for that user. Audit downstream consumers (cached searches, derived data) to ensure no leftover state.",
            },
            {
                "question": "Will it work across multiple agents?",
                "answer": "Yes — Mem0 supports user_id + agent_id scopes. Same user, different agents = different memory views. Or shared memory by agent_id.",
            },
            {
                "question": "What about cost?",
                "answer": "Mem0 makes LLM calls for fact extraction and search. ~2-3x per turn vs without memory. Cheaper than re-sending full history every turn for long conversations.",
            },
        ],
        "github_url": "https://github.com/mem0ai/mem0",
        "meta_title": "Mem0 Personal Assistant Memory — Starter",
        "meta_description": "Per-user memory for chat agents: store facts the user shares, retrieve relevant ones per query, update vs add semantics handled by Mem0.",
    },
]
