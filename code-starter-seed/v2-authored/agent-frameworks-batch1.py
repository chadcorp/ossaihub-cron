"""Agent framework starters — LangChain, AutoGen, CrewAI, custom loops."""

RECORDS = [
    {
        "slug": "langchain-tool-calling-agent-with-retries",
        "title": "LangChain Tool-Calling Agent With Retries and Tracing",
        "tldr": "Production-shape LangChain agent: structured tool calling, automatic retry on transient errors, step-level tracing to a JSON log, and a hard step-count budget to prevent runaway loops.",
        "category": "agent-frameworks",
        "language": "python",
        "framework": "LangChain",
        "tags": ["langchain", "agents", "tool-calling", "retries", "tracing"],
        "best_for_tags": ["production-agents", "observability", "research-assistants"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Building an agent that needs to call several tools to complete a task — a research assistant, a data analyst, a code-fix loop. The starter handles the boilerplate (retries, budgets, traces) so you focus on tools.",
        "when_not_to_use": "Skip for simple one-shot LLM calls (just call the model). Skip when you need very tight latency budgets — agent loops add round-trips. Skip for safety-critical decisions; agents amplify errors.",
        "quick_start": "pip install -U langchain langchain-openai langchain-anthropic tenacity && OPENAI_API_KEY=sk-... python agent.py 'Find the latest revenue numbers for X'",
        "full_code": '''"""LangChain tool-calling agent with retries, tracing, and step budget.

Pattern: tool-calling loop with circuit breakers.
- Max step budget prevents runaway loops.
- Transient errors retried with exponential backoff.
- Every step logged as a JSON object you can pipe to Langfuse / Arize / your own.
- Tools are pure functions; testing them in isolation is easy.

Replace the example tools (search, calculator) with your own.
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


# ----------------- TOOLS -----------------

@tool
def web_search(query: str) -> str:
    """Search the web for current information. Returns top 3 results with snippets.

    Args:
        query: Plain English search query.
    """
    # Replace with your real search backend (Tavily, Brave, etc.)
    return json.dumps([
        {"title": f"Result for {query}", "url": "https://example.com", "snippet": "Snippet..."}
    ])


@tool
def calculator(expression: str) -> str:
    """Evaluate a basic math expression. Use for arithmetic the LLM might get wrong.

    Args:
        expression: A Python expression with numbers and operators (+, -, *, /, **).
    """
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "ERROR: only digits and + - * / . ( ) allowed"
    try:
        return str(eval(expression, {"__builtins__": {}}))  # noqa: S307 -- sandboxed
    except Exception as e:
        return f"ERROR: {e}"


TOOLS = [web_search, calculator]


# ----------------- AGENT -----------------

@dataclass
class Step:
    n: int
    role: str            # "thought" | "tool_call" | "tool_result" | "final"
    content: str
    tool_name: str | None = None
    tool_args: dict | None = None
    duration_ms: int = 0


@dataclass
class AgentRun:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    steps: list[Step] = field(default_factory=list)
    final: str | None = None
    error: str | None = None

    def log(self, step: Step) -> None:
        self.steps.append(step)
        # Single JSON line per step — pipe to your observability tool.
        print(json.dumps({
            "run_id": self.run_id,
            "step": step.n,
            "role": step.role,
            "content": step.content[:200],
            "tool_name": step.tool_name,
            "duration_ms": step.duration_ms,
        }), file=sys.stderr)


def _is_transient(e: Exception) -> bool:
    msg = str(e).lower()
    return any(s in msg for s in ("rate", "timeout", "connection", "503", "502"))


class AgentBudgetExceeded(RuntimeError):
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call_llm(llm, messages):
    return llm.invoke(messages)


def run_agent(
    task: str,
    *,
    model: str = "gpt-4o-mini",
    max_steps: int = 10,
    system_prompt: str | None = None,
) -> AgentRun:
    run = AgentRun()
    llm = ChatOpenAI(model=model, temperature=0).bind_tools(TOOLS)
    tools_by_name: dict[str, Callable] = {t.name: t for t in TOOLS}

    messages: list[Any] = [
        SystemMessage(content=system_prompt or (
            "You are a careful researcher. Use tools when you don't know something. "
            "When you have enough info, return the answer directly without tool calls."
        )),
        HumanMessage(content=task),
    ]

    for step_n in range(1, max_steps + 1):
        t0 = time.time()
        try:
            ai_msg: AIMessage = _call_llm(llm, messages)
        except Exception as e:
            run.error = f"LLM call failed at step {step_n}: {e}"
            return run
        dt = int((time.time() - t0) * 1000)

        if not ai_msg.tool_calls:
            run.final = ai_msg.content
            run.log(Step(n=step_n, role="final", content=ai_msg.content, duration_ms=dt))
            return run

        run.log(Step(
            n=step_n, role="thought",
            content=ai_msg.content or "(no text — tool calls only)", duration_ms=dt
        ))
        messages.append(ai_msg)

        for tc in ai_msg.tool_calls:
            t0 = time.time()
            tool_fn = tools_by_name.get(tc["name"])
            if tool_fn is None:
                result = f"ERROR: unknown tool {tc['name']}"
            else:
                try:
                    result = tool_fn.invoke(tc["args"])
                except Exception as e:
                    if _is_transient(e):
                        result = f"TRANSIENT ERROR (retried by LLM if needed): {e}"
                    else:
                        result = f"ERROR: {e}"
            dt = int((time.time() - t0) * 1000)
            run.log(Step(
                n=step_n, role="tool_call",
                content=json.dumps(tc["args"])[:200],
                tool_name=tc["name"], tool_args=tc["args"], duration_ms=dt
            ))
            run.log(Step(n=step_n, role="tool_result", content=str(result)[:200], tool_name=tc["name"]))
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    run.error = f"Step budget {max_steps} exceeded"
    raise AgentBudgetExceeded(run.error)


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "What is 17 * 23?"
    run = run_agent(task)
    print("---\\nFINAL:", run.final or f"ERROR: {run.error}")
''',
        "dependencies": [
            {"name": "langchain", "version": ">=0.3.0", "purpose": "Agent loop, message types"},
            {"name": "langchain-openai", "version": ">=0.2.0", "purpose": "OpenAI chat model binding"},
            {"name": "langchain-anthropic", "version": ">=0.2.0", "purpose": "Anthropic model binding (optional)"},
            {"name": "tenacity", "version": ">=8.0", "purpose": "Retry decorator with exponential backoff"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI API key", "example": "sk-..."},
            {"name": "ANTHROPIC_API_KEY", "required": False, "description": "Anthropic API key (only if switching models)", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "pip install -U langchain langchain-openai langchain-anthropic tenacity",
            "export OPENAI_API_KEY=sk-...",
            "python agent.py 'Find the latest revenue for ACME Corp.'",
            "Pipe stderr to a JSON-line consumer (jq, vector, Langfuse) for traces.",
        ],
        "variations": [
            {
                "label": "Claude variant",
                "description": "Swap to Anthropic Claude for tool calling.",
                "code_snippet": "from langchain_anthropic import ChatAnthropic\\nllm = ChatAnthropic(model='claude-3-7-sonnet-latest', temperature=0).bind_tools(TOOLS)",
            },
            {
                "label": "With circuit breaker per tool",
                "description": "Stop calling a tool after N consecutive failures within a run.",
                "code_snippet": "tool_fails: dict[str, int] = {}\\nif tool_fails.get(tc['name'], 0) >= 3:\\n    result = f'CIRCUIT OPEN for {tc[\\\"name\\\"]}'\\nelse:\\n    try:\\n        result = tool_fn.invoke(tc['args'])\\n        tool_fails[tc['name']] = 0\\n    except Exception as e:\\n        tool_fails[tc['name']] = tool_fails.get(tc['name'], 0) + 1\\n        result = f'ERROR: {e}'",
            },
            {
                "label": "Streaming step events",
                "description": "Yield steps as they happen instead of returning at the end.",
                "code_snippet": "def run_agent_stream(task, **kw):\\n    # Convert run_agent into a generator yielding Step objects after each step.\\n    ...  # Use Python yield in place of run.log.",
            },
        ],
        "common_errors": [
            {
                "error_text": "openai.RateLimitError: Rate limit reached for ...",
                "cause": "OpenAI rate limit hit during the agent's repeated LLM calls.",
                "fix_snippet": "The tenacity retry on _call_llm already retries with exponential backoff. If you're hitting limits consistently, lower max_steps, switch to a model with higher TPM, or add jitter to the wait.",
            },
            {
                "error_text": "AgentBudgetExceeded: Step budget 10 exceeded",
                "cause": "Agent looped without converging within max_steps.",
                "fix_snippet": "Investigate the trace: usually means a tool is returning ambiguous results or the system prompt isn't clear about ‘when to stop’. Add to system prompt: 'When you have a confident answer, return it directly without calling more tools.'",
            },
            {
                "error_text": "ValidationError: 1 validation error for ChatOpenAI ... bind_tools",
                "cause": "Old LangChain version without unified bind_tools().",
                "fix_snippet": "pip install -U 'langchain>=0.3' 'langchain-openai>=0.2'. The unified .bind_tools() API requires recent versions.",
            },
            {
                "error_text": "TypeError: tool() missing required positional argument",
                "cause": "Tool function signature missing type hints or docstring.",
                "fix_snippet": "@tool decorator requires a docstring; argument types must be annotated. The LLM uses the docstring + arg names to decide when to call.",
            },
        ],
        "production_checklist": [
            "Set OPENAI_API_KEY (and ANTHROPIC_API_KEY if used) in your secrets manager, not in code.",
            "Pipe stderr JSON traces to an observability backend (Langfuse, Arize, OpenLLMetry).",
            "Set max_steps based on observed p99 of completing runs; don't leave at 10 in production.",
            "Add per-tool circuit breakers if any tool can fail in correlated ways.",
            "Cache deterministic tool results (e.g., calculator) — even agents call the same expression twice.",
            "Test with a representative eval set; agents drift on prompt changes more than single-shot prompts.",
            "Log full traces only in non-prod; in prod sample or store only failed runs for debugging.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o", "claude-3-7-sonnet"],
            "library_versions": ["langchain==0.3.6", "langchain-openai==0.2.5", "tenacity==8.5.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["langchain", "langfuse"],
        "related_glossary_slugs": ["tool-calling", "agent-loop", "retry-pattern"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why bind_tools instead of OpenAI function calling directly?",
                "answer": "bind_tools normalizes the API across providers (OpenAI, Anthropic, Gemini). Swapping models is a one-liner. The underlying mechanism is still each provider's native tool-calling.",
            },
            {
                "question": "Should I use this or LangGraph?",
                "answer": "LangGraph is better for complex multi-step state machines (router agents, multi-agent coordination). This starter is the right call when the agent is a linear tool-calling loop — most agents in practice.",
            },
            {
                "question": "How do I add memory across runs?",
                "answer": "Persist run_id with the full message list to your store. On the next call with the same conversation_id, prepend the prior messages. For long histories, summarize older turns into a context message.",
            },
            {
                "question": "Why is temperature 0?",
                "answer": "Tool-calling agents benefit from determinism; you want the same input to produce the same tool sequence. Bump to 0.2–0.3 only if you observe the agent getting stuck in identical loops.",
            },
        ],
        "github_url": "https://github.com/langchain-ai/langchain",
        "meta_title": "LangChain Tool-Calling Agent With Retries — Starter",
        "meta_description": "Production-shape LangChain agent: tool calls, retries on transient errors, step-budget circuit breaker, and JSON-line tracing per step.",
    },
    {
        "slug": "autogen-two-agent-handoff",
        "title": "AutoGen Two-Agent Handoff With Strict Termination",
        "tldr": "Two-agent AutoGen pattern: a Planner agent that delegates to a Coder agent and stops the conversation when criteria are met — no infinite ‘okay great, what else?’ loops.",
        "category": "agent-frameworks",
        "language": "python",
        "framework": "AutoGen",
        "tags": ["autogen", "multi-agent", "handoff", "termination"],
        "best_for_tags": ["multi-agent", "code-generation", "task-delegation"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When you want one agent to delegate to a specialist (Planner → Coder, Reviewer → Refactorer) with clear handoff. AutoGen handles message routing; the starter adds firm termination so the loop ends.",
        "when_not_to_use": "Skip if you only need one agent — adds complexity for no benefit. Skip for tightly-coupled multi-step tasks where the agents share a lot of state; a single agent with tools is cleaner.",
        "quick_start": "pip install pyautogen openai && OPENAI_API_KEY=sk-... python two_agent.py",
        "full_code": '''"""AutoGen two-agent handoff pattern with strict termination.

Planner delegates to Coder. Coder responds. Planner checks if done.
The custom termination function ends the conversation cleanly when:
  1. Planner says "DONE" — successful exit.
  2. Max turns exceeded — defensive exit.
  3. Same content seen twice — loop detection.
"""
import os

from autogen import ConversableAgent

CONFIG = {
    "config_list": [{
        "model": "gpt-4o-mini",
        "api_key": os.environ["OPENAI_API_KEY"],
    }],
    "temperature": 0,
}

PLANNER_SYSTEM = """You are a software planner. Given a coding task:
1. Decide what the Coder agent should do.
2. Delegate to it with a concrete request.
3. Review their output.
4. When the task is complete to your standard, reply with exactly: TASK_COMPLETE

Don't write code yourself — that's the Coder's job. Don't loop endlessly; if the Coder can't do it in 3 attempts, say TASK_FAILED with the reason."""

CODER_SYSTEM = """You are a Python coder. When asked to write code:
1. Write the requested code, complete and runnable.
2. Add a short docstring explaining usage.
3. Stop — don't explain at length. The Planner reviews.
If asked to revise, do so. Don't ask clarifying questions unless absolutely needed."""


def is_termination(message: dict) -> bool:
    """Custom termination: planner signals DONE/FAILED, or loop detected."""
    content = (message.get("content") or "").strip().upper()
    return "TASK_COMPLETE" in content or "TASK_FAILED" in content


def run(task: str, max_turns: int = 10):
    planner = ConversableAgent(
        name="Planner",
        system_message=PLANNER_SYSTEM,
        llm_config=CONFIG,
        is_termination_msg=is_termination,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=max_turns,
    )
    coder = ConversableAgent(
        name="Coder",
        system_message=CODER_SYSTEM,
        llm_config=CONFIG,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=max_turns,
    )

    # Loop detection: track last-N messages for duplicates
    seen: dict[str, int] = {}

    def hash_content(c: str) -> str:
        return c.strip().lower()[:200]

    original_send = planner.send

    def send_with_loop_check(message, recipient, request_reply=None, silent=False):
        h = hash_content(message if isinstance(message, str) else message.get("content", ""))
        seen[h] = seen.get(h, 0) + 1
        if seen[h] >= 3:
            print(f"\\n[loop detected — terminating]")
            return False
        return original_send(message, recipient, request_reply=request_reply, silent=silent)

    planner.send = send_with_loop_check

    result = planner.initiate_chat(coder, message=task)
    return result


if __name__ == "__main__":
    task = """Write a Python function `parse_phone(text: str) -> str | None`
that extracts a US phone number from text and returns it in E.164 format,
or None if no valid number found. Include 3 test cases as comments."""
    result = run(task)
    print("---\\nFINAL CHAT HISTORY:")
    for msg in result.chat_history:
        print(f"{msg['name']}: {msg['content'][:200]}")
''',
        "dependencies": [
            {"name": "pyautogen", "version": ">=0.4.0", "purpose": "Multi-agent framework"},
            {"name": "openai", "version": ">=1.40", "purpose": "Underlying LLM client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI API key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install pyautogen openai",
            "export OPENAI_API_KEY=sk-...",
            "python two_agent.py",
            "Watch the back-and-forth; terminates cleanly on TASK_COMPLETE.",
        ],
        "variations": [
            {
                "label": "Three-agent (Planner, Coder, Reviewer)",
                "description": "Add a Reviewer that critiques before TASK_COMPLETE.",
                "code_snippet": "reviewer = ConversableAgent(name='Reviewer', system_message='Critique code for correctness, edge cases, and style.', ...)\\n# Planner delegates to Coder then to Reviewer in sequence.",
            },
            {
                "label": "Group chat manager",
                "description": "Use GroupChatManager for >2 agents with dynamic routing.",
                "code_snippet": "from autogen import GroupChat, GroupChatManager\\ngc = GroupChat(agents=[planner, coder, reviewer], messages=[], max_round=15)\\nmanager = GroupChatManager(groupchat=gc, llm_config=CONFIG)\\nplanner.initiate_chat(manager, message=task)",
            },
            {
                "label": "With code execution",
                "description": "Coder writes and runs code in a sandbox.",
                "code_snippet": "coder = ConversableAgent(\\n    name='Coder',\\n    code_execution_config={'use_docker': True, 'work_dir': '/tmp/coder'},\\n    ...\\n)",
            },
        ],
        "common_errors": [
            {
                "error_text": "ConversableAgent has no attribute is_termination_msg",
                "cause": "Old pyautogen version.",
                "fix_snippet": "pip install -U 'pyautogen>=0.4'",
            },
            {
                "error_text": "openai.APIConnectionError",
                "cause": "Network issue or wrong base_url for non-OpenAI provider.",
                "fix_snippet": "If using a custom provider (Together, Groq), set 'base_url' in the config_list entry. Otherwise check network and OPENAI_API_KEY.",
            },
            {
                "error_text": "Agents keep saying ‘DONE’ without finishing.",
                "cause": "Termination match is too loose; ‘done’ appears in casual replies.",
                "fix_snippet": "Use a sentinel that's unlikely in normal text: TASK_COMPLETE (all caps, underscore). Update is_termination check to require exact match.",
            },
            {
                "error_text": "AutoGen never terminates",
                "cause": "Planner never says TASK_COMPLETE and max_consecutive_auto_reply too high.",
                "fix_snippet": "Lower max_consecutive_auto_reply to 6–8 and inspect why Planner won't sign off. Often the Planner's success criteria are unclear.",
            },
        ],
        "production_checklist": [
            "Never enable Docker code execution without a sandboxed environment.",
            "Set max_consecutive_auto_reply low (5–8); production loops should converge fast or fail fast.",
            "Log every message; AutoGen sessions are valuable forensic data when things go wrong.",
            "Test the termination sentinel doesn't appear in any agent's normal output.",
            "Budget per-message tokens — multi-agent chats balloon context fast.",
            "Use 0 temperature for code-generating agents; bump for ideation agents only.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["pyautogen==0.4.2", "openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["autogen"],
        "related_glossary_slugs": ["multi-agent-system", "termination-condition"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Is two agents better than one?",
                "answer": "Sometimes. For ‘plan then execute’ shapes where the two roles need different system prompts, yes. For most tasks, a single tool-calling agent is simpler and works fine.",
            },
            {
                "question": "How do I prevent infinite ‘great, what else?’ loops?",
                "answer": "The starter has three layers: explicit TASK_COMPLETE sentinel, max_consecutive_auto_reply cap, and content-hash loop detection. Use all three in production."
            },
            {
                "question": "Can the Coder agent run code?",
                "answer": "Yes — via AutoGen's code_execution_config. Always sandbox (Docker). Don't enable in shared environments without isolation.",
            },
            {
                "question": "Why not use LangGraph?",
                "answer": "LangGraph is great for explicit state machines. AutoGen leans into ‘conversational delegation’ — sometimes that maps closer to the actual problem (humans hand off the same way).",
            },
        ],
        "github_url": "https://github.com/microsoft/autogen",
        "meta_title": "AutoGen Two-Agent Handoff With Termination — Starter",
        "meta_description": "Planner-and-Coder AutoGen pattern with strict TASK_COMPLETE termination and loop detection — multi-agent without infinite back-and-forth.",
    },
    {
        "slug": "crewai-sequential-research-pipeline",
        "title": "CrewAI Sequential Research Pipeline",
        "tldr": "CrewAI pattern: Researcher → Analyzer → Writer crew running sequentially on a research topic, with explicit role descriptions, tools per agent, and a shared context dictionary the final Writer consumes.",
        "category": "agent-frameworks",
        "language": "python",
        "framework": "CrewAI",
        "tags": ["crewai", "multi-agent", "research", "sequential"],
        "best_for_tags": ["research-pipelines", "content-generation", "report-writing"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When you have a multi-stage task with handoff between specialists (research → synthesize → write) and you want CrewAI's role-and-goal abstractions to keep responsibilities clear.",
        "when_not_to_use": "Skip when the stages are tightly coupled (each stage needs to call back into previous). Skip when you need streaming output — CrewAI sequential is batch-shaped.",
        "quick_start": "pip install crewai crewai-tools && OPENAI_API_KEY=sk-... python research_crew.py 'Recent advances in 1.5B-parameter local LLMs'",
        "full_code": '''"""CrewAI sequential research pipeline: Researcher -> Analyzer -> Writer.

Each agent has a role, goal, backstory (CrewAI prompts these into the LLM),
and a set of tools. Tasks are sequential; later tasks see earlier tasks'
outputs via CrewAI's automatic context passing.
"""
import os
import sys

from crewai import Agent, Crew, Process, Task
from crewai_tools import SerperDevTool, WebsiteSearchTool


def build_crew(topic: str) -> Crew:
    search_tool = SerperDevTool()        # requires SERPER_API_KEY
    web_search = WebsiteSearchTool()

    researcher = Agent(
        role="Senior Research Analyst",
        goal=f"Find authoritative, recent sources about: {topic}",
        backstory="You are a meticulous researcher. You prefer primary sources, "
                  "favor recent results, and flag any claim you can't cite.",
        tools=[search_tool, web_search],
        verbose=True,
        allow_delegation=False,
        max_iter=8,
    )

    analyzer = Agent(
        role="Technical Analyst",
        goal="Synthesize research into key findings, tensions, and open questions",
        backstory="You distill noisy research into 3–5 clear findings. You "
                  "explicitly flag claims that are contested or thinly supported.",
        tools=[],
        verbose=True,
        allow_delegation=False,
        max_iter=4,
    )

    writer = Agent(
        role="Technical Writer",
        goal="Produce a 600–800 word brief in plain language for engineers",
        backstory="You write for working engineers. No fluff, no hedging beyond "
                  "what the analyst flagged. Inline citations to the researcher's sources.",
        tools=[],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

    research_task = Task(
        description=(
            f"Research the topic: {topic}\\n"
            "Find 5-10 authoritative sources (academic papers, official blogs, "
            "primary documentation). For each source: URL, key claim, date, and "
            "your confidence in it (high/medium/low)."
        ),
        expected_output=(
            "A markdown list of sources. For each: title, URL, date, key claim "
            "(1-2 sentences), confidence rating."
        ),
        agent=researcher,
    )

    analysis_task = Task(
        description=(
            "Read the researcher's sources. Produce 3-5 key findings. "
            "For each finding: state it, cite which sources support it, "
            "note any contradictory sources, and rate confidence (high/medium/low). "
            "Then list 3 open questions the research did NOT resolve."
        ),
        expected_output=(
            "Markdown with two sections: 'Findings' (3-5 bullets with citations) "
            "and 'Open questions' (3 bullets)."
        ),
        agent=analyzer,
        context=[research_task],  # Reads research_task output
    )

    writing_task = Task(
        description=(
            "Write a 600-800 word brief based on the analyst's findings. "
            "Audience: working engineers, not researchers. "
            "Structure: 1) why this matters now (2-3 sentences), 2) findings "
            "(woven into prose, not a bullet list), 3) what's still unclear, "
            "4) one-line takeaway. Cite sources inline as [Source: URL]."
        ),
        expected_output="A 600-800 word markdown brief with inline citations.",
        agent=writer,
        context=[research_task, analysis_task],
    )

    return Crew(
        agents=[researcher, analyzer, writer],
        tasks=[research_task, analysis_task, writing_task],
        process=Process.sequential,
        verbose=True,
    )


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "Recent advances in long-context attention mechanisms"
    crew = build_crew(topic)
    result = crew.kickoff()
    print("\\n=== FINAL BRIEF ===\\n")
    print(result)
''',
        "dependencies": [
            {"name": "crewai", "version": ">=0.70", "purpose": "Multi-agent framework"},
            {"name": "crewai-tools", "version": ">=0.12", "purpose": "Pre-built tool integrations (search, scraping)"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI API key", "example": "sk-..."},
            {"name": "SERPER_API_KEY", "required": True, "description": "Serper search API key (or swap for another search tool)", "example": "..."},
        ],
        "setup_steps": [
            "pip install crewai crewai-tools",
            "export OPENAI_API_KEY=sk-... SERPER_API_KEY=...",
            "python research_crew.py 'Your topic here'",
            "Output streams via verbose=True; final brief printed at end.",
        ],
        "variations": [
            {
                "label": "Hierarchical (manager agent)",
                "description": "Add a manager that decides whether to revisit research after analysis.",
                "code_snippet": "Crew(..., process=Process.hierarchical, manager_llm=ChatOpenAI(model='gpt-4o'))",
            },
            {
                "label": "Local LLM via Ollama",
                "description": "Run with Ollama instead of OpenAI.",
                "code_snippet": "from langchain_ollama import ChatOllama\\nresearcher = Agent(..., llm=ChatOllama(model='llama3.1'))",
            },
            {
                "label": "Async crew",
                "description": "Run independent tasks in parallel where dependencies allow.",
                "code_snippet": "Task(..., async_execution=True)  # CrewAI awaits when context requires it",
            },
        ],
        "common_errors": [
            {
                "error_text": "AuthenticationError: Invalid Serper API key",
                "cause": "Missing or wrong SERPER_API_KEY.",
                "fix_snippet": "Sign up at serper.dev, set SERPER_API_KEY. Or swap SerperDevTool for another search tool (Tavily, Brave).",
            },
            {
                "error_text": "Agents loop on the same research forever",
                "cause": "max_iter too high; researcher keeps trying to find more sources.",
                "fix_snippet": "Lower max_iter on the researcher to 5-8. Tighten the task's expected_output to specify exact number of sources (‘exactly 7 sources’).",
            },
            {
                "error_text": "Context too large after analysis_task",
                "cause": "Researcher returned huge content; full text passed forward.",
                "fix_snippet": "Have the researcher emit summaries, not full pages. Update its expected_output: ‘summary in 2 sentences per source, no full text quoted’.",
            },
            {
                "error_text": "Crew finishes but final brief ignores some findings",
                "cause": "Writer's context window not large enough; CrewAI truncates earlier task outputs.",
                "fix_snippet": "Use a larger-context model for the writer (gpt-4o, claude-3.5-sonnet) or summarize analysis_task output before writing_task.",
            },
        ],
        "production_checklist": [
            "Set verbose=False in production; enable only for debugging.",
            "Cache the researcher's output keyed by topic to avoid re-running for same query.",
            "Set token budget per agent and surface when an agent exceeds it.",
            "Validate the final output structure — CrewAI won't catch a writer who skipped sections.",
            "Run on a low-cost model first (gpt-4o-mini) and escalate per-agent to gpt-4o only where needed.",
            "Persist crew runs to a database with timestamps and inputs for replay.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["crewai==0.76.0", "crewai-tools==0.13.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["crewai"],
        "related_glossary_slugs": ["multi-agent-system", "agent-role"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "When should I use CrewAI vs LangGraph vs AutoGen?",
                "answer": "CrewAI: when role/goal/backstory abstractions map naturally to your task. LangGraph: when you have explicit state machines or routing logic. AutoGen: when conversational delegation between agents is the core pattern. They overlap; pick by team familiarity.",
            },
            {
                "question": "Why sequential and not hierarchical?",
                "answer": "Sequential is predictable and easy to debug. Hierarchical adds a manager that decides routing — powerful but harder to reason about. Start sequential; promote to hierarchical only when you need conditional revisiting.",
            },
            {
                "question": "How do I add a quality check before publishing?",
                "answer": "Add a fourth agent (Editor) with the writer's output as context. Editor's task: ‘review the brief; return APPROVED or specific revisions.’ Loop until APPROVED or N iterations.",
            },
            {
                "question": "Can agents use different models?",
                "answer": "Yes — pass `llm=` to each Agent. Use cheaper models for research/synthesis, premium for the final writer. Significant cost savings on long crews.",
            },
        ],
        "github_url": "https://github.com/crewAIInc/crewAI",
        "meta_title": "CrewAI Sequential Research Pipeline — Starter",
        "meta_description": "Researcher → Analyzer → Writer crew with role-and-goal abstractions, shared context, and tool assignment per agent — ready to extend.",
    },
    {
        "slug": "custom-react-agent-no-framework",
        "title": "Custom ReAct Agent (No Framework)",
        "tldr": "A complete ReAct loop in ~150 lines of plain Python — Thought → Action → Observation cycle with parsing, tool dispatch, and step budget. Useful when you want to understand what frameworks are doing.",
        "category": "agent-frameworks",
        "language": "python",
        "framework": "stdlib",
        "tags": ["react", "agents", "framework-free", "pedagogical"],
        "best_for_tags": ["learning", "minimal-deps", "custom-control"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When you want full control over the agent loop, or you're learning what LangChain/CrewAI abstract away. Also when minimizing dependencies (small Docker images, edge deployments).",
        "when_not_to_use": "Skip in production unless you have a specific reason — frameworks handle edge cases this starter doesn't (multi-tool-call parallel execution, structured tool calling, streaming).",
        "quick_start": "pip install openai && OPENAI_API_KEY=sk-... python react_agent.py 'What is 17 * 23 plus the square root of 144?'",
        "full_code": '''"""A minimal ReAct agent in plain Python.

ReAct loop:
  Thought: <agent reasoning>
  Action: <tool name>[<input>]
  Observation: <tool result>
  ...
  Answer: <final answer>

The agent emits Thought + Action; we parse Action, call the tool, append
Observation, and ask the model to continue. Loop until Answer or step budget.
"""
import json
import os
import re
import sys
from typing import Callable

from openai import OpenAI

client = OpenAI()


# ----------------- TOOLS -----------------

def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "ERROR: only digits and + - * / . ( ) allowed"
    try:
        return str(eval(expression, {"__builtins__": {}}))  # noqa: S307
    except Exception as e:
        return f"ERROR: {e}"


def sqrt(n_str: str) -> str:
    try:
        n = float(n_str)
        return f"{n ** 0.5:.6f}"
    except Exception as e:
        return f"ERROR: {e}"


def lookup_definition(term: str) -> str:
    # Stub: replace with real lookup
    defs = {
        "react": "ReAct = Reason + Act. An LLM pattern where the model interleaves "
                 "thinking with tool calls, observing results before deciding next step.",
    }
    return defs.get(term.lower(), f"No definition found for {term}")


TOOLS: dict[str, Callable[[str], str]] = {
    "calculator": calculator,
    "sqrt": sqrt,
    "lookup_definition": lookup_definition,
}


# ----------------- AGENT -----------------

SYSTEM_PROMPT = """You are a ReAct agent. Reason step-by-step and use tools when needed.

Tools available:
  calculator[<expression>]  - evaluate basic arithmetic
  sqrt[<number>]            - compute square root
  lookup_definition[<term>] - look up a term

Format each step EXACTLY as:
  Thought: <your reasoning>
  Action: tool_name[input]

After you receive an Observation, continue with another Thought + Action OR with:
  Answer: <your final answer>

Do NOT include both Action and Answer in the same step. One or the other.
"""


ACTION_RE = re.compile(r"Action:\\s*(\\w+)\\[(.+?)\\]", re.DOTALL)
ANSWER_RE = re.compile(r"Answer:\\s*(.+)", re.DOTALL)


def parse_step(text: str) -> tuple[str, str | None, str | None]:
    """Returns (role, tool_name_or_answer, input_or_None)."""
    m_a = ANSWER_RE.search(text)
    if m_a:
        return ("answer", m_a.group(1).strip(), None)
    m_t = ACTION_RE.search(text)
    if m_t:
        return ("action", m_t.group(1).strip(), m_t.group(2).strip())
    return ("malformed", text, None)


def run(task: str, *, model: str = "gpt-4o-mini", max_steps: int = 8) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for step in range(1, max_steps + 1):
        resp = client.chat.completions.create(model=model, messages=messages, temperature=0)
        text = resp.choices[0].message.content
        print(f"\\n--- step {step} ---\\n{text}")
        messages.append({"role": "assistant", "content": text})

        role, name_or_answer, tool_input = parse_step(text)
        if role == "answer":
            return name_or_answer
        if role == "malformed":
            messages.append({"role": "user", "content":
                "Your last response didn't follow the format. Please reply with EITHER "
                "‘Thought: ...\\\\nAction: tool[input]’ OR ‘Answer: ...’."})
            continue

        tool_fn = TOOLS.get(name_or_answer)
        if tool_fn is None:
            obs = f"ERROR: unknown tool {name_or_answer}. Available: {list(TOOLS)}"
        else:
            try:
                obs = tool_fn(tool_input)
            except Exception as e:
                obs = f"ERROR: {e}"
        print(f"Observation: {obs}")
        messages.append({"role": "user", "content": f"Observation: {obs}"})

    return f"ERROR: step budget {max_steps} exceeded"


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "What is the square root of (17 * 23 + 144)?"
    print(f"TASK: {task}")
    print(f"\\n=== ANSWER ===\\n{run(task)}")
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "LLM client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI API key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai",
            "export OPENAI_API_KEY=sk-...",
            "python react_agent.py 'Your task here'",
        ],
        "variations": [
            {
                "label": "Add a search tool",
                "description": "Real web search via Tavily.",
                "code_snippet": "from tavily import TavilyClient\\ntv = TavilyClient(api_key=os.environ['TAVILY_API_KEY'])\\nTOOLS['search'] = lambda q: json.dumps(tv.search(q)['results'][:3])",
            },
            {
                "label": "Streaming version",
                "description": "Yield steps as they're generated.",
                "code_snippet": "def run_stream(task):\\n    # use stream=True on the OpenAI call; emit parsed steps as they complete.",
            },
            {
                "label": "Use Anthropic instead",
                "description": "Run with Claude.",
                "code_snippet": "from anthropic import Anthropic\\nclient = Anthropic()\\nresp = client.messages.create(model='claude-3-7-sonnet-latest', system=SYSTEM_PROMPT, messages=messages, max_tokens=1024)\\ntext = resp.content[0].text",
            },
        ],
        "common_errors": [
            {
                "error_text": "Step budget 8 exceeded",
                "cause": "Agent kept calling tools without concluding.",
                "fix_snippet": "Inspect the trace. Usually the agent isn't sure when to STOP. Sharpen the system prompt: ‘When you have enough information for the user's question, write Answer: directly.’",
            },
            {
                "error_text": "Malformed step (no Action or Answer)",
                "cause": "Model wrote free-form text instead of the format.",
                "fix_snippet": "The starter already reminds the model when this happens. If it persists, switch to gpt-4o or add 2-3 worked examples (few-shot) of the format in the system prompt.",
            },
            {
                "error_text": "Tool always returns ‘unknown tool’ for valid names",
                "cause": "Regex doesn't match because model used backticks or extra formatting.",
                "fix_snippet": "Tighten the system prompt to forbid markdown formatting on Action lines. Or expand ACTION_RE to handle ‘Action: `tool[input]`’.",
            },
            {
                "error_text": "Action input has nested brackets and breaks parsing",
                "cause": "ACTION_RE non-greedy match stops at first ].",
                "fix_snippet": "Use Action: tool(input) with parens, or pass JSON inputs: ‘Action: search[{\"query\": \"foo\"}]’ and parse the JSON.",
            },
        ],
        "production_checklist": [
            "Don't deploy this exact code to production — it's pedagogical. Production agents need structured tool calling, parallel tool execution, and richer error handling.",
            "If you do use it, sandbox the calculator (the eval() call is restricted but not bulletproof).",
            "Log every step + observation for debugging; cheap and high-leverage.",
            "Add per-tool timeouts; one slow tool blocks the agent.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["react", "agent-loop", "tool-calling"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why ReAct instead of OpenAI's structured tool calling?",
                "answer": "ReAct is the pattern that frameworks (LangChain, CrewAI) wrap. Understanding it directly helps you debug when frameworks behave strangely. Structured tool calling is better in production — this is a learning artifact.",
            },
            {
                "question": "Can I run this with a local model via Ollama?",
                "answer": "Yes — point the OpenAI client at Ollama's OpenAI-compatible endpoint: OpenAI(base_url='http://localhost:11434/v1', api_key='ollama'). ReAct works well with capable local models (Llama 3.1 8B+).",
            },
            {
                "question": "Why is the format so strict?",
                "answer": "Because we're parsing model output. Stricter format → fewer parse errors. Production agents use tool-calling APIs (JSON-structured) instead of text-format ReAct to eliminate this entirely.",
            },
        ],
        "github_url": "",
        "meta_title": "Custom ReAct Agent in 150 Lines — Starter",
        "meta_description": "Plain-Python ReAct loop with Thought-Action-Observation parsing, step budget, and tool dispatch — no frameworks, the pattern frameworks wrap.",
    },
]
