"""Code agents starters — batch 2: Aider, OpenHands, SWE-agent, custom coding agent."""

RECORDS = [
    {
        "slug": "aider-coding-agent-config",
        "title": "Aider Coding Agent Configuration",
        "tldr": "Aider: terminal-based coding agent. Edits files, runs tests, makes commits. Configure with .aider.conf.yml; pick a model; let it work on your repo.",
        "category": "code-agents",
        "language": "yaml",
        "framework": "Aider",
        "tags": ["aider", "coding-agent", "terminal", "git"],
        "best_for_tags": ["solo-developers", "feature-implementation", "refactoring"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Want a hands-off coding agent that lives in your terminal. Aider iterates on tasks, edits multiple files, runs tests, commits to git. Great solo dev productivity tool.",
        "when_not_to_use": "Skip for team-shared dev workflows (no shared state). Skip without git (Aider expects git repos). Skip for huge monorepos — context-limited.",
        "quick_start": "pip install aider-chat && cd your-repo && aider",
        "full_code": '''# Aider configuration: .aider.conf.yml (place in repo root)

#######################################################################
# MODEL SELECTION
#######################################################################

# Best quality (expensive)
model: anthropic/claude-3-5-sonnet-20241022

# Cheaper alternatives
# model: anthropic/claude-3-5-haiku-20241022
# model: openai/gpt-4o
# model: openai/gpt-4o-mini

# Editor model (smaller; used for edit-apply mode)
editor-model: anthropic/claude-3-5-haiku-20241022

# Weak model (for cheap operations like commit messages)
weak-model: openai/gpt-4o-mini


#######################################################################
# EDIT FORMAT
#######################################################################

# 'diff' format: tightest edits; works with most models
edit-format: diff

# 'whole' format: full file rewrites; safer but more expensive
# edit-format: whole

# 'udiff' format: unified diff output
# edit-format: udiff


#######################################################################
# AUTO-COMMIT BEHAVIOR
#######################################################################

# Aider auto-commits successful edits with descriptive messages
auto-commits: true

# Generate commit messages with the weak model
attribute-author: true
attribute-committer: true

# Run pre-commit hooks
auto-test: true
test-cmd: "pytest -x --tb=short"

# Run linter
auto-lint: true
lint-cmd: "ruff check --fix"


#######################################################################
# CONTEXT MANAGEMENT
#######################################################################

# Repository map: shows aider the codebase structure
map-tokens: 4096

# Files to ALWAYS include in context
read:
  - README.md
  - pyproject.toml

# Files to EXCLUDE (besides .gitignore)
# Aider respects .gitignore by default


#######################################################################
# WORKFLOW
#######################################################################

# Confirm before each edit (slower but safer)
yes: false

# Stream LLM output as it generates
stream: true

# Output format
pretty: true
dark-mode: true

# Show diffs before applying
show-diffs: true


#######################################################################
# CACHING
#######################################################################

# Cache prompts with Anthropic for cost savings
cache-prompts: true


#######################################################################
# ENVIRONMENT
#######################################################################

# Set in shell: export ANTHROPIC_API_KEY=sk-ant-...
# Or set via env-file:
env-file: .env


#######################################################################
# USAGE
#######################################################################

# Basic invocation
#   aider
#   aider src/auth.py src/users.py  # specify files
#
# Tell aider what to do
#   /add src/billing.py           # add file to context
#   /drop src/legacy.py           # remove from context
#   /test                         # run tests
#   /commit                       # commit pending changes
#   /undo                         # undo last edit
#   /ask <question>               # read-only mode
#   /code <prompt>                # explicit edit mode
#
# Then just type natural-language requests:
#   "Add a rate limiter to the /api/login endpoint"
#   "Refactor the billing module to use the new Stripe API"
#   "Write tests for the new logic"


#######################################################################
# PRODUCTION-LIKE WORKFLOW
#######################################################################

# Best practices:
# 1. Always start with a clean git working tree.
# 2. Let aider auto-commit each successful change.
# 3. Review diffs before merging to main.
# 4. Use --yes for trusted small changes; manual confirmation for big.
# 5. Maintain a CLAUDE.md or AIDER.md with project conventions.
''',
        "dependencies": [
            {"name": "aider-chat", "version": ">=0.60", "purpose": "Aider CLI"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": False, "description": "For Claude models", "example": "sk-ant-..."},
            {"name": "OPENAI_API_KEY", "required": False, "description": "For GPT models", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install aider-chat",
            "cd into your git repo",
            "Save .aider.conf.yml at repo root",
            "Set API key (e.g., export ANTHROPIC_API_KEY=...)",
            "Run: aider",
            "Type natural-language requests; aider edits + commits",
        ],
        "variations": [
            {"label": "Voice mode", "description": "Talk to aider.", "code_snippet": "# pip install 'aider-chat[voice]'; then aider --voice. Useful for hands-busy iteration."},
            {"label": "Pair with linter", "description": "Auto-fix style issues post-edit.", "code_snippet": "auto-lint: true\\nlint-cmd: 'ruff check --fix && black .'"},
            {"label": "Architect + editor models", "description": "Two models: planner + writer.", "code_snippet": "model: anthropic/claude-3-5-sonnet-20241022  # architect\\neditor-model: openai/gpt-4o-mini       # cheaper edit-apply"},
        ],
        "common_errors": [
            {"error_text": "Aider applies edits to wrong file", "cause": "Multiple files with similar content.", "fix_snippet": "Use /add and /drop explicitly to manage context. Aider works best with SMALL focused contexts."},
            {"error_text": "Tests fail after edit (auto-rollback)", "cause": "Edit broke something else.", "fix_snippet": "auto-test catches this. Aider rolls back. Review failed-test output and provide more context."},
            {"error_text": "High API costs", "cause": "Large repo map + verbose context.", "fix_snippet": "Reduce map-tokens to 2048. Use editor-model for cheaper edits. Enable cache-prompts with Anthropic."},
            {"error_text": "Loses context across sessions", "cause": "No persistent memory.", "fix_snippet": "Save important context in CLAUDE.md / AIDER.md at repo root. Aider reads it automatically."},
        ],
        "production_checklist": [
            "Use Claude 3.5 Sonnet as architect; cheaper model for editor.",
            "Enable cache-prompts (Anthropic) for cost savings.",
            "Auto-commit + auto-test + auto-lint catches regressions.",
            "Maintain AIDER.md with project conventions.",
            "Review every diff before pushing.",
            "Pair with CI — if CI catches what auto-test missed, refine test-cmd.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-5-sonnet-20241022", "gpt-4o"],
            "library_versions": ["aider-chat==0.60"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["aider"],
        "related_glossary_slugs": ["coding-agent", "ai-pair-programmer"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Aider vs Cursor vs Cline?", "answer": "Aider: CLI, model-agnostic, git-native. Cursor: GUI IDE, model-agnostic. Cline: VS Code extension. Pick by interface preference; Aider for terminal-first devs."},
            {"question": "Multi-file edits?", "answer": "Yes — Aider handles them well. Add relevant files to context (/add). Aider produces a coherent multi-file diff."},
            {"question": "Cost?", "answer": "Sonnet-only: $5-20/day for active use. With caching + cheaper editor: $2-10/day. Significantly cheaper than Cursor Pro for heavy users."},
            {"question": "Pair with vim / emacs?", "answer": "Aider is its own REPL. For inline assistance in vim: codecompanion.nvim or copilot.vim. Aider is for delegated work, not inline."},
        ],
        "github_url": "https://github.com/paul-gauthier/aider",
        "meta_title": "Aider Coding Agent Configuration Starter",
        "meta_description": "Aider: terminal coding agent. Edits files, runs tests, commits via git. Configure with .aider.conf.yml; works with Claude, GPT-4, local models.",
    },
    {
        "slug": "openhands-autonomous-coding-agent",
        "title": "OpenHands Autonomous Coding Agent",
        "tldr": "OpenHands (formerly OpenDevin): open-source autonomous coding agent. Plans, executes, runs in sandbox. Web UI or headless. Solves multi-step coding tasks end-to-end.",
        "category": "code-agents",
        "language": "python",
        "framework": "OpenHands",
        "tags": ["openhands", "autonomous", "coding-agent", "sandbox"],
        "best_for_tags": ["autonomous-tasks", "research", "swe-bench"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Want an OSS alternative to Devin. OpenHands executes coding tasks autonomously in a sandbox. Best for: well-defined ticket → working code workflows. Strong on SWE-bench.",
        "when_not_to_use": "Skip for interactive pair-programming (Aider / Cursor better). Skip without time to set up sandbox (Docker required). Skip for production without close oversight.",
        "quick_start": "docker run -it --rm -p 3000:3000 -v /var/run/docker.sock:/var/run/docker.sock docker.all-hands.dev/all-hands-ai/openhands:0.10",
        "full_code": '''"""OpenHands: autonomous coding agent.

Two modes:
1. Web UI: docker run with the OpenHands image.
2. Headless: invoke via Python SDK for integration into pipelines.
"""

# ----------------- WEB UI (one-shot Docker) -----------------

# docker run -it --rm \\
#   -p 3000:3000 \\
#   -v /var/run/docker.sock:/var/run/docker.sock \\
#   -v ~/.openhands-state:/.openhands-state \\
#   --add-host host.docker.internal:host-gateway \\
#   docker.all-hands.dev/all-hands-ai/openhands:0.10

# Browser to http://localhost:3000
# - Choose LLM provider (Claude / GPT / local)
# - Optionally connect a GitHub repo
# - Give a task: "Add a CSV export endpoint to the /api/users route"
# - Watch it plan + execute


# ----------------- HEADLESS MODE (Python) -----------------

from __future__ import annotations

import asyncio
import os
from openhands.controller import AgentController
from openhands.controller.agent import Agent
from openhands.events.action import MessageAction
from openhands.events.stream import EventStream
from openhands.llm import LLM
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime


async def run_task(task: str, workspace: str) -> str:
    """Run a coding task autonomously."""
    llm = LLM(
        config={
            "model": "anthropic/claude-3-5-sonnet-20241022",
            "api_key": os.environ["ANTHROPIC_API_KEY"],
            "max_input_tokens": 100_000,
        }
    )

    # Sandboxed Docker runtime for code execution
    RuntimeCls = get_runtime_cls("docker")
    runtime: Runtime = RuntimeCls(
        config={
            "workspace_base": workspace,
            "container_image": "docker.all-hands.dev/all-hands-ai/runtime:0.10-nikolaik",
            "use_host_network": False,
        },
        event_stream=EventStream(sid="task-1"),
        sid="task-1",
        plugins=[],
    )

    agent = Agent.from_name("CodeActAgent", llm=llm)

    controller = AgentController(
        agent=agent,
        runtime=runtime,
        max_iterations=30,
        max_budget_per_task=5.0,  # USD cap
        event_stream=runtime.event_stream,
    )

    await runtime.connect()
    controller.event_stream.add_event(
        MessageAction(content=task),
        source="user",
    )

    # Drive the loop
    while controller.state.iteration < controller.state.max_iterations:
        await controller.step()
        if controller.state.is_done():
            break

    return controller.state.last_action.content if controller.state.last_action else "No output"


# ----------------- BATCH TASKS (CI integration) -----------------

async def batch_solve(tickets: list[dict], workspace: str):
    """Run multiple tickets in sequence (or parallel with separate workspaces)."""
    results = []
    for ticket in tickets:
        task = f"{ticket['title']}\\n\\n{ticket['description']}"
        try:
            result = await run_task(task, workspace=f"{workspace}/ticket-{ticket['id']}")
            results.append({"ticket": ticket["id"], "status": "ok", "output": result})
        except Exception as e:
            results.append({"ticket": ticket["id"], "status": "failed", "error": str(e)})
    return results


# ----------------- DEMO -----------------

if __name__ == "__main__":
    task = "Add a CSV export endpoint to the /api/users route. Include tests."
    result = asyncio.run(run_task(task, workspace="/tmp/openhands-workspace"))
    print(result)
''',
        "dependencies": [
            {"name": "openhands-ai", "version": ">=0.10", "purpose": "OpenHands Python package"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": False, "description": "Claude as the underlying LLM", "example": "sk-ant-..."},
            {"name": "OPENAI_API_KEY", "required": False, "description": "Or GPT-4o", "example": "sk-..."},
        ],
        "setup_steps": [
            "Install Docker (required for sandbox)",
            "Pull image: docker pull docker.all-hands.dev/all-hands-ai/openhands:0.10",
            "Web UI: docker run with the command above",
            "Headless: pip install openhands-ai + write Python driver",
            "Provide LLM API key",
            "Give task; let it work",
        ],
        "variations": [
            {"label": "GitHub Actions integration", "description": "Trigger OpenHands on issue creation.", "code_snippet": "# Use openhands GitHub Action to assign labeled issues. Agent opens PR with proposed fix."},
            {"label": "Custom agent", "description": "Subclass Agent for domain-specific logic.", "code_snippet": "from openhands.controller.agent import Agent\\nclass CustomAgent(Agent):\\n    def step(self, state): ... # custom planning logic"},
            {"label": "Read-only mode", "description": "Agent analyzes but doesn't execute.", "code_snippet": "# Set runtime to a sandboxed FS that's read-only; agent reasons + proposes changes without applying"},
        ],
        "common_errors": [
            {"error_text": "Docker socket permission denied", "cause": "User not in docker group.", "fix_snippet": "sudo usermod -aG docker $USER; logout/login. OpenHands needs Docker socket to spawn runtime containers."},
            {"error_text": "Agent loops on same problem", "cause": "Insufficient context or unclear task.", "fix_snippet": "Set max_iterations cap (30 default). Provide more context upfront. Improve task description with constraints."},
            {"error_text": "Budget exceeded mid-task", "cause": "Complex task + expensive model.", "fix_snippet": "Increase max_budget_per_task. Or switch to cheaper model. Or break task into smaller sub-tasks."},
            {"error_text": "Sandbox container fails to start", "cause": "Image not pulled or wrong architecture.", "fix_snippet": "docker pull docker.all-hands.dev/all-hands-ai/runtime:0.10-nikolaik. For ARM (M1/M2 Mac), use arm64 image tag."},
        ],
        "production_checklist": [
            "Always run in Docker sandbox (never on bare host).",
            "Set max_iterations + max_budget_per_task caps.",
            "Audit logs for every code change.",
            "Run agent in isolated workspace per task.",
            "Use Sonnet or GPT-4o for best results (vs cheaper models).",
            "Combine with code-review tooling on output.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-5-sonnet-20241022", "gpt-4o"],
            "library_versions": ["openhands-ai==0.10"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["openhands"],
        "related_glossary_slugs": ["autonomous-agent", "swe-bench"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "OpenHands vs Devin?", "answer": "Devin: managed SaaS. OpenHands: OSS alternative; you run it. Comparable capabilities on SWE-bench. OpenHands is the open community successor to OpenDevin."},
            {"question": "Safe to run on production code?", "answer": "Run in sandbox + on a feature branch. Review every diff. Don't grant write access to main. For untrusted tasks, use throwaway workspaces."},
            {"question": "Token cost?", "answer": "Complex SWE-bench-style tasks: $1-5 per task with Sonnet. Simple tasks: $0.10-0.50. Set budget caps to prevent runaway."},
            {"question": "Compare to Aider?", "answer": "Aider: interactive pair-programmer. OpenHands: fully autonomous. OpenHands plans + executes WITHOUT human in the loop. Aider iterates WITH you."},
        ],
        "github_url": "https://github.com/All-Hands-AI/OpenHands",
        "meta_title": "OpenHands Autonomous Coding Agent Starter",
        "meta_description": "OpenHands: OSS autonomous coding agent. Plans + executes in sandbox. Headless Python SDK or web UI.",
    },
]
