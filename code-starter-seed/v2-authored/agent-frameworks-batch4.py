"""Agent framework starters — batch 4: CrewAI, AutoGen, Mastra (TS), Strands."""

RECORDS = [
    {
        "slug": "crewai-multi-agent-team",
        "title": "CrewAI Multi-Agent Team",
        "tldr": "CrewAI: define agents with roles, give them tools + goals, they collaborate. Hierarchical or sequential workflows. Easiest framework for 'team of specialists' patterns.",
        "category": "agent-frameworks",
        "language": "python",
        "framework": "CrewAI",
        "tags": ["crewai", "multi-agent", "team", "specialists"],
        "best_for_tags": ["business-workflows", "research-teams", "rapid-prototyping"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Multi-step workflows that decompose naturally into roles (researcher + writer + editor, or planner + executor + reviewer). CrewAI's role-based abstraction makes this clean.",
        "when_not_to_use": "Skip for single-agent tasks (use a raw SDK). Skip for production with strict latency budgets — CrewAI is heavier than LangGraph for simple chains.",
        "quick_start": "pip install crewai 'crewai[tools]' && python crew_demo.py",
        "full_code": '''"""CrewAI: roles + goals + tools = collaborating crew."""
from __future__ import annotations

import os
from crewai import Agent, Crew, Task, Process
from crewai_tools import SerperDevTool, WebsiteSearchTool


# ----------------- TOOLS -----------------

search_tool = SerperDevTool()  # needs SERPER_API_KEY
website_tool = WebsiteSearchTool()


# ----------------- AGENTS (with roles + goals + backstories) -----------------

researcher = Agent(
    role="Senior Market Research Analyst",
    goal="Find recent, accurate information about {topic} from credible sources",
    backstory=(
        "You're known for thorough research. You cite sources, "
        "cross-check claims, and never make up information."
    ),
    tools=[search_tool, website_tool],
    verbose=True,
    max_iter=8,
    allow_delegation=False,
)

analyst = Agent(
    role="Strategic Analyst",
    goal="Extract insights and patterns from research findings",
    backstory=(
        "You synthesize research into actionable insights. You're skeptical "
        "of single-source claims and surface counter-evidence."
    ),
    tools=[],
    verbose=True,
    allow_delegation=False,
)

writer = Agent(
    role="Executive Brief Writer",
    goal="Produce a 1-page executive brief from analysis findings",
    backstory=(
        "You write for time-poor executives. Lead with the recommendation; "
        "support with the strongest evidence; never bury the lede."
    ),
    tools=[],
    verbose=True,
)


# ----------------- TASKS -----------------

research_task = Task(
    description=(
        "Research {topic}. Find: (1) recent developments, (2) credible sources, "
        "(3) opposing viewpoints. Output as structured notes with citations."
    ),
    expected_output="Markdown research notes with 8-15 cited findings",
    agent=researcher,
)

analysis_task = Task(
    description=(
        "Analyze the research notes. Surface: (1) key insights, (2) contradictions, "
        "(3) risks, (4) opportunities. Quantify where possible."
    ),
    expected_output="Markdown analysis with insights + risks + opportunities sections",
    agent=analyst,
    context=[research_task],
)

writing_task = Task(
    description=(
        "Produce a 1-page executive brief based on the analysis. Format: "
        "Recommendation (1 sentence) → 3 supporting findings → 3 risks → next steps."
    ),
    expected_output="A 1-page markdown executive brief",
    agent=writer,
    context=[analysis_task],
    output_file="brief.md",
)


# ----------------- CREW -----------------

crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, writing_task],
    process=Process.sequential,  # or Process.hierarchical with a manager agent
    verbose=True,
    memory=True,                  # short-term + long-term memory
)


# ----------------- RUN -----------------

if __name__ == "__main__":
    result = crew.kickoff(inputs={"topic": "AI agent observability tools in 2025"})
    print(result)
''',
        "dependencies": [
            {"name": "crewai", "version": ">=0.80", "purpose": "CrewAI framework"},
            {"name": "crewai-tools", "version": ">=0.20", "purpose": "Built-in tools"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "Default LLM", "example": "sk-..."},
            {"name": "SERPER_API_KEY", "required": False, "description": "For SerperDevTool web search", "example": "..."},
        ],
        "setup_steps": [
            "pip install crewai 'crewai[tools]'",
            "export OPENAI_API_KEY=sk-...",
            "export SERPER_API_KEY=...  # for web search tool",
            "python crew_demo.py",
            "Output saved to brief.md",
        ],
        "variations": [
            {"label": "Hierarchical manager", "description": "Manager agent delegates tasks dynamically.", "code_snippet": "manager = Agent(role='Project Manager', ...)\\ncrew = Crew(agents=[...], tasks=[...], process=Process.hierarchical, manager_agent=manager)"},
            {"label": "Custom tool", "description": "Wrap your own function.", "code_snippet": "from crewai.tools import tool\\n@tool('Description here')\\ndef my_tool(arg: str) -> str: return f'result for {arg}'"},
            {"label": "Different LLMs per agent", "description": "Cost optimization.", "code_snippet": "from crewai import LLM\\nresearcher = Agent(role=..., llm=LLM(model='gpt-4o-mini'))\\nwriter = Agent(role=..., llm=LLM(model='gpt-4o'))"},
        ],
        "common_errors": [
            {"error_text": "Agent doesn't use the tool", "cause": "Tool description too vague.", "fix_snippet": "Make tool descriptions ACTION-oriented. 'Search the web' beats 'Web tool'. The agent reads tool descriptions to decide when to use them."},
            {"error_text": "Tasks run in wrong order", "cause": "context= not set.", "fix_snippet": "Each downstream task needs context=[upstream_task]. CrewAI uses this to pass outputs forward."},
            {"error_text": "Agent infinite loops", "cause": "max_iter too high or task underspecified.", "fix_snippet": "Cap max_iter (5-8 typical). Make task expected_output concrete. Force the agent to commit to an output."},
            {"error_text": "Memory leak across runs", "cause": "memory=True keeps state.", "fix_snippet": "Memory persists across crew.kickoff(). For independent runs, set memory=False or use separate Crew instances."},
        ],
        "production_checklist": [
            "Concrete role + goal + backstory per agent (vague = bad output).",
            "Tool descriptions are ACTION-oriented for clarity.",
            "Task expected_output forces structured outputs.",
            "Cap max_iter to prevent runaway.",
            "Use cheaper LLMs for ancillary agents.",
            "Persist outputs (output_file=) for downstream consumption.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["crewai==0.80"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["crewai"],
        "related_glossary_slugs": ["multi-agent", "agent-role"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "CrewAI vs LangGraph?", "answer": "CrewAI: role-based, more opinionated, easier for business workflows. LangGraph: graph-based, more flexible, better for complex state. Pick CrewAI for team-of-specialists; LangGraph for state machines."},
            {"question": "Sequential vs hierarchical?", "answer": "Sequential: tasks run in order; clean for pipelines. Hierarchical: manager agent decides what's next; useful when task sequence is unknown upfront. Sequential is more predictable."},
            {"question": "How big can a crew get?", "answer": "Practical limit ~5-7 agents. Past that, coordination cost dominates. For larger workflows, decompose into sub-crews."},
            {"question": "Cost?", "answer": "Each agent + tool call is an LLM call. A 3-agent crew with research / analyze / write might be 15-30 LLM calls = $0.10-0.50 per run with gpt-4o-mini. Plan budgets accordingly."},
        ],
        "github_url": "https://github.com/joaomdmoura/crewai",
        "meta_title": "CrewAI Multi-Agent Team Starter",
        "meta_description": "CrewAI: role-based multi-agent workflows. Researcher + analyst + writer crews, tools, sequential/hierarchical processes.",
    },
    {
        "slug": "autogen-conversational-agents",
        "title": "AutoGen Conversational Multi-Agent",
        "tldr": "Microsoft AutoGen 0.4: conversational multi-agent where agents talk to each other in turns. Built-in user-proxy, group chat, and code execution. Strong for problem-solving teams.",
        "category": "agent-frameworks",
        "language": "python",
        "framework": "AutoGen",
        "tags": ["autogen", "multi-agent", "conversational", "microsoft"],
        "best_for_tags": ["problem-solving", "code-execution", "research"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Multi-agent problem-solving where agents need to TALK to each other in turns. AutoGen's GroupChat + reply mechanics handle this cleanly. Great for code-heavy workflows.",
        "when_not_to_use": "Skip for simple linear pipelines (CrewAI / LangGraph simpler). Skip if you need TYPED structured outputs throughout (AutoGen is conversation-text-first).",
        "quick_start": "pip install 'autogen-agentchat==0.4.*' 'autogen-ext[openai]' && python autogen_demo.py",
        "full_code": '''"""AutoGen 0.4: conversational multi-agent solving a task together."""
from __future__ import annotations

import asyncio
import os

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.models.openai import OpenAIChatCompletionClient


# ----------------- MODEL CLIENT -----------------

model = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=os.environ["OPENAI_API_KEY"],
)


# ----------------- AGENTS -----------------

planner = AssistantAgent(
    name="planner",
    model_client=model,
    system_message=(
        "You're a senior engineer. Break tasks into concrete steps. "
        "For each step, specify what code (if any) needs to be written and what output is expected. "
        "When the task is complete, write APPROVE."
    ),
)

coder = AssistantAgent(
    name="coder",
    model_client=model,
    system_message=(
        "You write Python code in fenced ```python blocks. "
        "Each block is a complete, self-contained script that prints its output. "
        "Wait for execution results before continuing. Be terse."
    ),
)

# Executor runs code (must be in a sandbox for production!)
executor = CodeExecutorAgent(
    name="executor",
    code_executor=LocalCommandLineCodeExecutor(work_dir="./tmp"),  # ⚠️ sandbox for prod
)


# ----------------- TEAM -----------------

team = RoundRobinGroupChat(
    participants=[planner, coder, executor],
    termination_condition=MaxMessageTermination(15) | TextMentionTermination("APPROVE"),
)


# ----------------- RUN -----------------

async def main():
    task = "Compute the 100th prime number. Write a Python script, run it, print the result."
    await Console(team.run_stream(task=task))


if __name__ == "__main__":
    asyncio.run(main())
''',
        "dependencies": [
            {"name": "autogen-agentchat", "version": ">=0.4", "purpose": "AutoGen 0.4 main package"},
            {"name": "autogen-ext[openai]", "version": ">=0.4", "purpose": "OpenAI model client extension"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install 'autogen-agentchat==0.4.*' 'autogen-ext[openai]'",
            "export OPENAI_API_KEY=sk-...",
            "mkdir tmp  # code execution workdir",
            "python autogen_demo.py",
            "Console UI streams the conversation",
        ],
        "variations": [
            {"label": "Sandboxed code execution", "description": "Docker instead of LocalCommandLineCodeExecutor.", "code_snippet": "from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor\\nexecutor = CodeExecutorAgent(name='exec', code_executor=DockerCommandLineCodeExecutor(image='python:3.12'))"},
            {"label": "Human-in-the-loop", "description": "Pause for human approval.", "code_snippet": "from autogen_agentchat.agents import UserProxyAgent\\nhuman = UserProxyAgent('human')\\nteam = RoundRobinGroupChat([planner, coder, human, executor], ...)"},
            {"label": "Selector group chat", "description": "Smart speaker selection.", "code_snippet": "from autogen_agentchat.teams import SelectorGroupChat\\nteam = SelectorGroupChat(participants=[...], model_client=model, selector_prompt='Pick the next speaker')"},
        ],
        "common_errors": [
            {"error_text": "Code execution refused / no output", "cause": "Code blocks not in expected ```python format.", "fix_snippet": "Re-pin coder agent's system prompt: 'always use ```python fences for code blocks.' Without fences, executor skips."},
            {"error_text": "Infinite back-and-forth between agents", "cause": "No termination condition.", "fix_snippet": "Always set termination_condition. MaxMessageTermination + TextMentionTermination('APPROVE') is a robust default."},
            {"error_text": "Sandbox escape concerns", "cause": "LocalCommandLineCodeExecutor runs on host.", "fix_snippet": "Use DockerCommandLineCodeExecutor in production. LocalCommand only for trusted dev / experiments."},
            {"error_text": "AutoGen 0.2 vs 0.4 confusion", "cause": "Different APIs.", "fix_snippet": "Use 0.4 (current). pip install 'autogen-agentchat==0.4.*'. 0.2 'pyautogen' is legacy."},
        ],
        "production_checklist": [
            "ALWAYS sandbox code execution (Docker, not local).",
            "Cap conversation length with MaxMessageTermination.",
            "Add explicit termination signal (APPROVE / DONE / [END]).",
            "Pin AutoGen 0.4.x version (rapid evolution).",
            "Log all conversations for debugging.",
            "Use HumanInTheLoop for sensitive actions.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o"],
            "library_versions": ["autogen-agentchat==0.4"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["autogen"],
        "related_glossary_slugs": ["multi-agent", "code-execution"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "AutoGen vs CrewAI?", "answer": "AutoGen: conversational, code-execution-strong, Microsoft. CrewAI: role-based, business-workflow-strong. AutoGen for problem-solving with code; CrewAI for structured pipelines."},
            {"question": "AutoGen 0.2 vs 0.4?", "answer": "0.4 is the current version (autogen-agentchat). 0.2 (pyautogen) is legacy / abandoned. New projects: use 0.4."},
            {"question": "How is code execution safe?", "answer": "It isn't, by default. LocalCommandLineCodeExecutor runs on YOUR machine. For untrusted tasks, ALWAYS use DockerCommandLineCodeExecutor (or E2B / Modal sandbox)."},
            {"question": "Best for what use cases?", "answer": "Code-heavy problem solving (data analysis, debugging, simulations). Less ideal for typed structured outputs or strict latency SLAs."},
        ],
        "github_url": "https://github.com/microsoft/autogen",
        "meta_title": "AutoGen Conversational Multi-Agent Starter",
        "meta_description": "AutoGen 0.4: conversational multi-agent with code execution, group chat, human-in-loop. Microsoft's framework.",
    },
    {
        "slug": "mastra-typescript-agent-framework",
        "title": "Mastra TypeScript Agent Framework",
        "tldr": "Mastra: TypeScript-first agent framework with tools, workflows, RAG, evals built in. The 'Pydantic-AI for the JS world'. Fast, typed, production-friendly.",
        "category": "agent-frameworks",
        "language": "typescript",
        "framework": "Mastra",
        "tags": ["mastra", "typescript", "agents", "workflows"],
        "best_for_tags": ["typescript-stack", "node-apps", "fast-dx"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "TS/JS stack building agents. Mastra has the LangChain feature set but with native TS types + a CLI for scaffolding. Cleaner than wrapping Python frameworks via APIs.",
        "when_not_to_use": "Skip if Python is your stack (use Pydantic-AI). Skip for production scale beyond Node — for high QPS, Python ecosystems are more battle-tested.",
        "quick_start": "npm create mastra@latest && cd my-mastra && npm run dev",
        "full_code": '''/**
 * Mastra agent with tools + RAG + workflow.
 *
 * Project structure:
 *   src/mastra/index.ts      <- this file
 *   src/mastra/agents/
 *   src/mastra/tools/
 *   src/mastra/workflows/
 */
import { Mastra } from "@mastra/core";
import { Agent } from "@mastra/core/agent";
import { createTool } from "@mastra/core/tools";
import { Workflow, Step } from "@mastra/core/workflows";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";


// ----------------- TOOL (typed with Zod) -----------------

const searchWeb = createTool({
  id: "search-web",
  description: "Search the web for recent information.",
  inputSchema: z.object({
    query: z.string(),
    limit: z.number().default(5),
  }),
  outputSchema: z.object({
    results: z.array(z.object({
      title: z.string(),
      url: z.string(),
      snippet: z.string(),
    })),
  }),
  execute: async ({ context }) => {
    // Stub — replace with real search call
    return {
      results: [
        { title: `Stub: ${context.query}`, url: "https://example.com", snippet: "..." },
      ].slice(0, context.limit),
    };
  },
});


// ----------------- AGENT -----------------

const researchAgent = new Agent({
  name: "research-agent",
  instructions: `You research topics and produce concise summaries.
Use the search-web tool for recent info. Cite sources by URL.`,
  model: openai("gpt-4o-mini"),
  tools: { searchWeb },
});


// ----------------- WORKFLOW (multi-step pipeline) -----------------

const researchStep = new Step({
  id: "research",
  inputSchema: z.object({ topic: z.string() }),
  outputSchema: z.object({ summary: z.string() }),
  execute: async ({ context }) => {
    const { topic } = context.triggerData;
    const result = await researchAgent.generate(
      `Research: ${topic}. Use the search-web tool. Output a 200-word summary.`,
    );
    return { summary: result.text };
  },
});

const evalStep = new Step({
  id: "evaluate",
  inputSchema: z.object({ summary: z.string() }),
  outputSchema: z.object({ score: z.number(), notes: z.string() }),
  execute: async ({ context }) => {
    const { summary } = context.getStepResult("research");
    // LLM-as-judge eval
    const eval_ = await researchAgent.generate(
      `Rate this summary 1-5 on clarity + citations:\\n${summary}\\nOutput JSON: {score, notes}`,
    );
    return JSON.parse(eval_.text);
  },
});

const researchWorkflow = new Workflow({
  name: "research-workflow",
  triggerSchema: z.object({ topic: z.string() }),
}).step(researchStep).then(evalStep).commit();


// ----------------- MASTRA APP -----------------

export const mastra = new Mastra({
  agents: { researchAgent },
  workflows: { researchWorkflow },
});


// ----------------- RUN -----------------

// Local dev: npm run dev launches a UI to test agents/workflows
// Server: mastra exposes /api/agents/* + /api/workflows/* automatically

// Programmatic use:
async function main() {
  const { runId, start } = researchWorkflow.createRun();
  const result = await start({ triggerData: { topic: "MCP servers 2025" } });
  console.log(result);
}

main();
''',
        "dependencies": [
            {"name": "@mastra/core", "version": ">=0.5", "purpose": "Mastra framework"},
            {"name": "@ai-sdk/openai", "version": ">=1.0", "purpose": "OpenAI provider"},
            {"name": "zod", "version": ">=3.23", "purpose": "Schema validation"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI", "example": "sk-..."},
        ],
        "setup_steps": [
            "npm create mastra@latest",
            "Pick your provider (OpenAI / Anthropic / Google)",
            "cd my-mastra-app && npm run dev",
            "Open http://localhost:4111 — interactive playground",
            "Edit src/mastra/agents/, tools/, workflows/",
        ],
        "variations": [
            {"label": "RAG with vector store", "description": "Built-in vector store integrations.", "code_snippet": "import { PgVector } from '@mastra/pg';\\nconst vectorStore = new PgVector(process.env.DATABASE_URL);\\nawait vectorStore.upsert('docs', embeddings);"},
            {"label": "Eval framework", "description": "Built-in evals.", "code_snippet": "import { AnswerRelevancyMetric } from '@mastra/evals';\\nconst metric = new AnswerRelevancyMetric();\\nconst score = await metric.measure(input, output);"},
            {"label": "Memory + threads", "description": "Conversational memory.", "code_snippet": "import { Memory } from '@mastra/memory';\\nconst memory = new Memory({ storage: new PostgresStore(...) });\\nresearchAgent.memory = memory;"},
        ],
        "common_errors": [
            {"error_text": "Schema validation fails", "cause": "LLM output doesn't match Zod schema.", "fix_snippet": "Use generate({ output: schema }) for guaranteed structured output. Mastra wraps Vercel AI SDK's structured-output mode."},
            {"error_text": "Workflow steps not running in order", "cause": "Missing .then() chain.", "fix_snippet": "Workflow API: .step(A).then(B).then(C).commit(). Without .then, steps run in parallel."},
            {"error_text": "Dev playground shows blank", "cause": "Port collision or mastra config wrong.", "fix_snippet": "Check port 4111. Verify export named 'mastra' in entry file. Restart dev server."},
            {"error_text": "TypeScript inference broken", "cause": "Mixing Zod versions.", "fix_snippet": "Pin zod version across project. Mastra needs zod ^3.23+. Older versions break inference."},
        ],
        "production_checklist": [
            "Use Zod schemas everywhere — types end-to-end.",
            "Pin Mastra + Vercel AI SDK versions.",
            "Use Memory + threads for multi-turn conversations.",
            "Add observability via @mastra/integrations (Langfuse, etc.).",
            "Deploy as Node.js server (Mastra exposes API routes).",
            "Test workflows end-to-end before shipping.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["@mastra/core==0.5", "Node.js 20"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["mastra"],
        "related_glossary_slugs": ["agent-framework", "typed-agent"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Mastra vs LangChain.js?", "answer": "Mastra: newer, TypeScript-native, cleaner abstractions. LangChain.js: older, bigger ecosystem, more integrations. Pick Mastra for new TS projects; LangChain for ecosystem needs."},
            {"question": "Mastra vs Vercel AI SDK?", "answer": "Mastra is BUILT ON Vercel AI SDK. Mastra adds agents, workflows, memory, evals, RAG. Use AI SDK alone for simple chat; Mastra for agent systems."},
            {"question": "Production-ready?", "answer": "Yes, but young (v0.5). API surface evolving. Pin versions. Most stable: agents + tools + workflows. Less stable: RAG primitives, evals."},
            {"question": "Hosting?", "answer": "Standard Node.js — Vercel, Railway, Render, Cloud Run, AWS Lambda. Mastra exposes API routes; deploy like any Node app."},
        ],
        "github_url": "https://github.com/mastra-ai/mastra",
        "meta_title": "Mastra TypeScript Agent Framework Starter",
        "meta_description": "Mastra: TypeScript-first agent framework with typed tools, workflows, RAG, evals, memory. The TS-native LangChain alternative.",
    },
    {
        "slug": "react-agent-from-scratch",
        "title": "ReAct Agent From Scratch (Educational)",
        "tldr": "Build a ReAct (Reason+Act) agent without a framework: 200 lines, no dependencies beyond an LLM client. Educational — understand what frameworks abstract.",
        "category": "agent-frameworks",
        "language": "python",
        "framework": "Custom",
        "tags": ["react", "agent", "from-scratch", "educational"],
        "best_for_tags": ["learning", "understanding-frameworks", "minimal-deps"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Want to understand HOW agent frameworks work under the hood. Or building a custom framework. Or the constraint set rules out using a framework.",
        "when_not_to_use": "Skip for production — use a framework (Pydantic-AI, CrewAI, LangGraph). Skip for complex agents — frameworks handle a lot of edge cases.",
        "quick_start": "pip install openai && python react_agent.py",
        "full_code": '''"""ReAct agent from scratch.

The loop:
  while not done:
    1. Reason: think about what to do
    2. Act: call a tool OR produce a final answer
    3. Observe: get tool result
    4. Repeat
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Any

from openai import OpenAI


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# ----------------- TOOLS (just python functions with docstrings) -----------------

def web_search(query: str) -> str:
    """Search the web. Args: query (str). Returns: top results as string."""
    return f"[stub web results for '{query}']"


def calculator(expression: str) -> str:
    """Evaluate a math expression. Args: expression (e.g., '2 + 2'). Returns: result."""
    try:
        return str(eval(expression, {"__builtins__": {}}))  # toy sandbox
    except Exception as e:
        return f"Error: {e}"


def current_time() -> str:
    """Get current UTC time. No args."""
    from datetime import datetime
    return datetime.utcnow().isoformat()


TOOLS: dict[str, Callable] = {
    "web_search": web_search,
    "calculator": calculator,
    "current_time": current_time,
}


# ----------------- PROMPT -----------------

REACT_PROMPT = """You are a ReAct agent. You can use these tools:

{tool_descriptions}

Format EXACTLY like this:

Thought: [your reasoning about what to do]
Action: tool_name(args as JSON)
Observation: [the tool's result will be inserted here]
... (repeat Thought/Action/Observation as needed)
Thought: I have enough info to answer.
Final Answer: [your answer]

Task: {task}
"""


def tool_descriptions() -> str:
    return "\\n".join(
        f"- {name}: {fn.__doc__.strip()}"
        for name, fn in TOOLS.items()
    )


# ----------------- AGENT LOOP -----------------

ACTION_PATTERN = re.compile(r"Action:\\s*(\\w+)\\((.*?)\\)\\s*(?=\\n|$)", re.DOTALL)
FINAL_PATTERN = re.compile(r"Final Answer:\\s*(.*)", re.DOTALL)


def parse_action(text: str) -> tuple[str, dict] | None:
    match = ACTION_PATTERN.search(text)
    if not match:
        return None
    name = match.group(1).strip()
    args_str = match.group(2).strip()
    # Parse args: try JSON; fallback to single-string arg
    try:
        if args_str.startswith("{"):
            args = json.loads(args_str)
        else:
            args = json.loads(f'{{"_arg": {args_str}}}')
    except json.JSONDecodeError:
        args = {"_arg": args_str.strip('"\\'')}
    return name, args


def execute_tool(name: str, args: dict) -> str:
    fn = TOOLS.get(name)
    if not fn:
        return f"Error: unknown tool {name}"
    try:
        # Convert _arg back to positional if it was the only key
        if list(args.keys()) == ["_arg"]:
            return fn(args["_arg"])
        return fn(**args)
    except Exception as e:
        return f"Error: {e}"


def run(task: str, max_iterations: int = 10) -> str:
    prompt = REACT_PROMPT.format(tool_descriptions=tool_descriptions(), task=task)
    history = ""

    for iteration in range(max_iterations):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt + history}],
            stop=["Observation:"],  # let us inject observations
            temperature=0,
        )
        thought_action = response.choices[0].message.content
        print(f"\\n--- Iteration {iteration + 1} ---")
        print(thought_action)
        history += thought_action

        # Check for final answer
        final = FINAL_PATTERN.search(thought_action)
        if final:
            return final.group(1).strip()

        # Parse + execute action
        parsed = parse_action(thought_action)
        if not parsed:
            history += "\\nThought: I should re-read the format instructions and emit a proper Action.\\n"
            continue

        name, args = parsed
        result = execute_tool(name, args)
        history += f"\\nObservation: {result}\\n"
        print(f"Observation: {result}")

    return "Max iterations reached without final answer"


# ----------------- DEMO -----------------

if __name__ == "__main__":
    answer = run("What's 17% of 1284, and what's the current UTC time?")
    print(f"\\n=== FINAL ===\\n{answer}")
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "LLM client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai",
            "export OPENAI_API_KEY=sk-...",
            "python react_agent.py",
            "Trace the agent's reasoning — see how frameworks abstract this",
        ],
        "variations": [
            {"label": "JSON-tool-call instead of text parsing", "description": "Use native tool-calling.", "code_snippet": "# Instead of parsing 'Action: ...' from text, use openai's tools= parameter. Faster + more reliable; less educational."},
            {"label": "Add tool retries on error", "description": "Graceful failure.", "code_snippet": "# In execute_tool, on Error: append to history and let LLM retry. Cap retries to prevent loops."},
            {"label": "Streaming with structured stops", "description": "Stream up to Observation marker.", "code_snippet": "# Use streaming + parse_action on each chunk; stop early when 'Final Answer:' detected."},
        ],
        "common_errors": [
            {"error_text": "Model doesn't follow ReAct format", "cause": "System prompt unclear.", "fix_snippet": "Pin format with examples (few-shot). Newer models (gpt-4o, claude-3.5) follow ReAct format well; smaller models may need more examples."},
            {"error_text": "Action parsing fails on complex args", "cause": "Regex limited.", "fix_snippet": "Use structured outputs (response_format) or JSON-mode + native tool-calling. ReAct via text parsing is fragile."},
            {"error_text": "Agent loops forever", "cause": "No final answer detected.", "fix_snippet": "Cap max_iterations. Force FINAL marker. Use stop sequences to break model out of the format."},
            {"error_text": "Tool arg mismatch", "cause": "Free-form args don't match function signature.", "fix_snippet": "Use JSON-schema for tool args. Validate before calling. Better: use native tool-calling instead of text-parsed ReAct."},
        ],
        "production_checklist": [
            "DON'T use this in production — use a framework.",
            "If you must: use native tool-calling, not text parsing.",
            "Cap max_iterations.",
            "Validate tool args against schemas.",
            "Log every iteration for debugging.",
            "Add tool execution timeout.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["openai"],
        "related_glossary_slugs": ["react", "agent"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why build from scratch?", "answer": "Educational. Once you see the ReAct loop in 200 lines, framework magic disappears. You'll make better choices about which framework features matter."},
            {"question": "Is ReAct the only agent pattern?", "answer": "Common but not only. Alternatives: Plan-and-Execute, ReWoo (reasoning-without-observation), tool-augmented chain-of-thought. Modern frameworks support multiple."},
            {"question": "Text-parsed ReAct vs native tool-calling?", "answer": "Native is more reliable + cheaper. Text-parsed ReAct is what's in the literature. Modern models support tool-calling; use that for production."},
            {"question": "When does ReAct fail?", "answer": "Long horizons (10+ steps): context grows, reasoning drifts. Complex tool dependencies: ReAct is sequential. Use Plan-and-Execute or LangGraph for these cases."},
        ],
        "github_url": "",
        "meta_title": "ReAct Agent From Scratch Starter",
        "meta_description": "Build a ReAct agent without a framework: 200 lines, no deps beyond OpenAI client. Educational — see what frameworks abstract.",
    },
]
