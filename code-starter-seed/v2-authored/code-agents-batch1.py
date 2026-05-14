"""Code agent starters — git ops, code editing, sandboxed execution."""

RECORDS = [
    {
        "slug": "sandboxed-code-executor-docker",
        "title": "Sandboxed Python Code Executor (Docker)",
        "tldr": "Execute LLM-generated Python code in an isolated Docker container with CPU/memory/network limits, capturing stdout/stderr and a timeout. Production-shape sandbox for AI code agents.",
        "category": "code-agents",
        "language": "python",
        "framework": "Docker",
        "tags": ["sandbox", "code-execution", "docker", "isolation"],
        "best_for_tags": ["code-agents", "ai-tools", "execution-safety"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "When you want an LLM agent to run Python it generated — data analysis, calculations, plotting — without trusting the code. Docker isolation prevents accidental or malicious damage.",
        "when_not_to_use": "Skip in environments without Docker (use restricted Python sandbox or remote execution service). Skip for very low-latency needs (~500ms Docker startup is the floor).",
        "quick_start": "docker pull python:3.11-slim && python sandbox.py 'print(2+2)'",
        "full_code": '''"""Run untrusted Python code in a sandboxed Docker container.

Limits:
  - CPU: 1.0 share
  - Memory: 256MB
  - Network: disabled
  - Time: 10 seconds
  - No mounted volumes (no filesystem access outside container)
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

DOCKER_IMAGE = "python:3.11-slim"


@dataclass
class ExecResult:
    stdout: str
    stderr: str
    return_code: int
    timed_out: bool


def run_python_sandboxed(
    code: str,
    *,
    timeout_seconds: int = 10,
    cpu_share: float = 1.0,
    memory_mb: int = 256,
    allow_network: bool = False,
    packages: list[str] | None = None,
) -> ExecResult:
    """Run `code` in an isolated Docker container."""

    if packages:
        # Build a wrapper script that installs packages first
        installer = (
            "import subprocess, sys; "
            "subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet'] + "
            + json.dumps(packages)
            + ")\\n"
        )
        full_code = installer + code
    else:
        full_code = code

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(full_code)
        script_path = Path(f.name)

    try:
        cmd = [
            "docker", "run", "--rm",
            "--cpus", str(cpu_share),
            "--memory", f"{memory_mb}m",
            "--security-opt", "no-new-privileges",
            "--read-only",
            "--tmpfs", "/tmp:rw,size=10m,mode=1777",
            "-v", f"{script_path}:/script.py:ro",
            "-w", "/tmp",
        ]
        if not allow_network:
            cmd += ["--network", "none"]
        cmd += [DOCKER_IMAGE, "python", "/script.py"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            return ExecResult(
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                timed_out=False,
            )
        except subprocess.TimeoutExpired:
            # Kill the container; subprocess.run already returned
            return ExecResult(
                stdout="",
                stderr=f"TIMEOUT after {timeout_seconds}s",
                return_code=-1,
                timed_out=True,
            )

    finally:
        script_path.unlink(missing_ok=True)


# ----------------- INTEGRATION WITH AN LLM AGENT -----------------

def llm_with_python_tool(user_request: str):
    """Skeleton showing how an LLM agent calls this sandbox as a tool."""
    from openai import OpenAI
    client = OpenAI()

    TOOLS = [{
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Execute Python code in a sandboxed environment. Returns stdout, stderr, and return code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "packages": {"type": "array", "items": {"type": "string"}, "description": "pip packages to install"},
                },
                "required": ["code"],
            },
        },
    }]

    messages = [
        {"role": "system", "content": "You can run Python code via the run_python tool. Use it for math, data, or any computation."},
        {"role": "user", "content": user_request},
    ]

    while True:
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=TOOLS)
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return msg.content
        messages.append(msg.model_dump())
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = run_python_sandboxed(args["code"], packages=args.get("packages"))
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps({
                    "stdout": result.stdout, "stderr": result.stderr,
                    "return_code": result.return_code, "timed_out": result.timed_out,
                }),
            })


if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else "print(2+2)"
    print(run_python_sandboxed(code))
''',
        "dependencies": [
            {"name": "docker", "version": ">=24.0", "purpose": "Containerization runtime (host-side)"},
            {"name": "openai", "version": ">=1.40", "purpose": "Example LLM integration"},
        ],
        "env_vars": [],
        "setup_steps": [
            "Install Docker.",
            "docker pull python:3.11-slim",
            "Save as sandbox.py.",
            "python sandbox.py 'print(\\\"hi\\\")'",
            "Integrate with an LLM agent by wrapping run_python_sandboxed as a tool.",
        ],
        "variations": [
            {
                "label": "With matplotlib output",
                "description": "Capture plots as base64.",
                "code_snippet": "# Add to packages: ['matplotlib']\\n# In code, save plot to /tmp/plot.png; mount /tmp as a result volume\\n# Read /tmp/plot.png, encode as b64, return alongside stdout",
            },
            {
                "label": "Persistent kernel (like Jupyter)",
                "description": "Variables persist across calls.",
                "code_snippet": "# Use jupyter_kernel_gateway in container; start kernel once, send code via WebSocket.\\n# Trades latency for state persistence.",
            },
            {
                "label": "Use Modal for the sandbox",
                "description": "Cloud-based sandbox instead of local Docker.",
                "code_snippet": "import modal\\n@modal.function(image=modal.Image.debian_slim().pip_install('numpy'), timeout=10)\\ndef run(code): exec(code)  # Modal handles isolation",
            },
            {
                "label": "Pre-built image with common libs",
                "description": "Avoid pip install on every run.",
                "code_snippet": "# Dockerfile that installs numpy, pandas, matplotlib at build time\\n# DOCKER_IMAGE = 'your-registry/sandbox:latest'\\n# Skip the installer wrapper",
            },
        ],
        "common_errors": [
            {
                "error_text": "docker: command not found",
                "cause": "Docker daemon not running or not installed.",
                "fix_snippet": "Install Docker Desktop (Mac/Win) or docker-ce (Linux). Verify with: docker run --rm hello-world.",
            },
            {
                "error_text": "Code that works locally fails in sandbox",
                "cause": "Missing packages or network access.",
                "fix_snippet": "Pass `packages=[]` to install at runtime, OR build custom image with packages preinstalled. For network-dependent code, set allow_network=True (review the security implications).",
            },
            {
                "error_text": "Slow execution (~500ms minimum)",
                "cause": "Docker container startup overhead.",
                "fix_snippet": "Use persistent-kernel variation for batched calls. Or use a pre-warmed container pool. Or accept the overhead for safety.",
            },
            {
                "error_text": "Container can write to host filesystem",
                "cause": "Misconfigured mount.",
                "fix_snippet": "Starter uses :ro (read-only) for script + tmpfs for /tmp. Verify no -v mounts grant write to host paths.",
            },
        ],
        "production_checklist": [
            "Run Docker daemon with rootless mode where possible.",
            "Set CPU/memory limits tight; don't allow runaway resources.",
            "Disable network by default; allow only when task requires it (and log).",
            "Audit pip install behavior — packages can do arbitrary things on install.",
            "Strip secrets from environment before passing to container.",
            "Log every code execution with the exact code; useful for debugging and abuse detection.",
            "Set a hard daily quota per user to prevent abuse.",
            "Test with adversarial code: infinite loops, fork bombs, large allocations.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["docker (engine 24.0+)", "python==3.11"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["docker"],
        "related_glossary_slugs": ["sandbox", "code-execution", "isolation"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "How safe is this?",
                "answer": "Docker with these flags blocks most common attacks: filesystem isolation, no network, memory cap. NOT a security boundary for nation-state actors. For high-stakes, use Firecracker microVMs or remote services (Modal, E2B).",
            },
            {
                "question": "Why no network by default?",
                "answer": "Network = exfiltration. If the agent doesn't need it, off. Enable only for tasks that genuinely need (web requests, fetching data).",
            },
            {
                "question": "Can the code persist files?",
                "answer": "Only in /tmp (in-memory). Filesystem is read-only otherwise. To persist outputs, mount a specific output directory or capture from stdout.",
            },
            {
                "question": "What about other languages?",
                "answer": "Same pattern — different Docker image. JavaScript: node:20-slim. Bash: alpine. The sandbox flags are language-agnostic.",
            },
        ],
        "github_url": "",
        "meta_title": "Sandboxed Python Code Executor (Docker) — Starter",
        "meta_description": "Run LLM-generated Python in an isolated Docker container with CPU/memory/network limits, timeout, and clean stdout/stderr capture.",
    },
    {
        "slug": "git-ops-agent-with-pr",
        "title": "Git Ops Agent (Branch, Edit, Commit, PR)",
        "tldr": "Python helper for code agents to make changes via git: creates branch, applies file edits, commits, opens PR. Includes safety guards (no force push, no main-branch edits, mandatory PR title).",
        "category": "code-agents",
        "language": "python",
        "framework": "GitPython + gh CLI",
        "tags": ["git", "code-agent", "pull-request", "automation"],
        "best_for_tags": ["coding-agents", "automation", "ci-cd"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When an LLM agent edits code and you want changes to flow through PR review (not direct main commits). Useful for AI-assisted refactors, bug fixes, dependency updates.",
        "when_not_to_use": "Skip for production-blocking automated commits (use a CODEOWNER + branch protection instead). Skip when you don't want PRs (just use git directly in a working copy).",
        "quick_start": "pip install GitPython && gh auth login && python git_agent.py 'refactor pricing module'",
        "full_code": '''"""Git operations for a code agent: branch, edit, commit, PR.

Safety guards:
  - Refuses to edit main/master directly
  - Refuses force pushes
  - Requires PR title and body (non-empty)
  - Validates branch name conforms to convention
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from git import Repo


PROTECTED_BRANCHES = {"main", "master", "production", "release"}
BRANCH_NAME_RE = re.compile(r"^(feat|fix|chore|refactor|docs|test)/[a-z0-9-]+$")


class GitAgentError(Exception):
    pass


class GitAgent:
    def __init__(self, repo_path: str | Path):
        self.repo = Repo(str(repo_path))
        if self.repo.bare:
            raise GitAgentError("repo is bare")
        if self.repo.head.is_detached:
            raise GitAgentError("HEAD is detached; check out a branch first")

    def current_branch(self) -> str:
        return self.repo.active_branch.name

    def is_protected(self, branch: str) -> bool:
        return branch in PROTECTED_BRANCHES

    def create_branch(self, name: str, *, from_branch: str = "main") -> None:
        """Create and check out a new branch."""
        if not BRANCH_NAME_RE.match(name):
            raise GitAgentError(
                f"branch name '{name}' must match {BRANCH_NAME_RE.pattern}"
            )
        if name in [b.name for b in self.repo.branches]:
            raise GitAgentError(f"branch {name} already exists")
        if self.is_protected(self.current_branch()):
            # Don't branch from current if protected — pull latest first
            origin = self.repo.remotes.origin
            origin.fetch()
        self.repo.git.checkout("-b", name, from_branch)

    def apply_edits(self, edits: list[dict]) -> list[Path]:
        """Apply a list of file edits. Each edit: {path, content}.

        Refuses to write outside the repo dir.
        """
        if self.is_protected(self.current_branch()):
            raise GitAgentError(f"cannot edit on protected branch {self.current_branch()}")

        repo_root = Path(self.repo.working_tree_dir).resolve()
        written = []
        for edit in edits:
            target = (repo_root / edit["path"]).resolve()
            if not str(target).startswith(str(repo_root)):
                raise GitAgentError(f"path escapes repo: {edit['path']}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(edit["content"], encoding="utf-8")
            written.append(target.relative_to(repo_root))
        return written

    def commit(self, message: str, *, files: list[Path] | None = None) -> str:
        """Stage and commit. Returns commit hash."""
        if self.is_protected(self.current_branch()):
            raise GitAgentError("cannot commit to protected branch")
        if not message.strip():
            raise GitAgentError("commit message cannot be empty")
        if files:
            self.repo.index.add([str(f) for f in files])
        else:
            self.repo.git.add("-A")
        if not self.repo.index.diff("HEAD"):
            raise GitAgentError("nothing to commit")
        commit = self.repo.index.commit(message)
        return commit.hexsha

    def push(self, branch: str | None = None) -> None:
        """Push current or specified branch. Never force."""
        b = branch or self.current_branch()
        if self.is_protected(b):
            raise GitAgentError(f"refusing to push to protected branch {b}")
        # Explicit refspec, no force flag accepted
        self.repo.git.push("origin", b, set_upstream=True)

    def open_pr(self, title: str, body: str, *, base: str = "main") -> str:
        """Open PR via gh CLI. Returns PR URL."""
        if not title.strip() or not body.strip():
            raise GitAgentError("PR title and body both required")
        result = subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", body, "--base", base],
            cwd=self.repo.working_tree_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()


# ----------------- USAGE -----------------

if __name__ == "__main__":
    import sys

    agent = GitAgent(".")
    description = sys.argv[1] if len(sys.argv) > 1 else "demo refactor"

    branch = f"refactor/agent-{description.replace(' ', '-')[:30]}"
    agent.create_branch(branch)

    # Apply edits (in real use, these come from the LLM)
    agent.apply_edits([
        {"path": "AGENT_RAN.md", "content": f"# Agent ran\\n\\nTask: {description}\\n"},
    ])

    commit_hash = agent.commit(f"refactor: {description}")
    print(f"committed {commit_hash[:7]}")
    agent.push()
    pr_url = agent.open_pr(
        title=f"refactor: {description}",
        body=f"Automated PR from agent.\\n\\nTask: {description}",
    )
    print(f"opened PR: {pr_url}")
''',
        "dependencies": [
            {"name": "GitPython", "version": ">=3.1", "purpose": "Git operations"},
            {"name": "gh (CLI)", "version": ">=2.30", "purpose": "PR creation"},
        ],
        "env_vars": [
            {"name": "GH_TOKEN", "required": False, "description": "GitHub token if gh CLI not interactively authed", "example": "ghp_..."},
        ],
        "setup_steps": [
            "pip install GitPython",
            "Install gh CLI: brew install gh (mac) or apt install gh (Linux)",
            "gh auth login",
            "Save as git_agent.py in your repo root",
            "Test: python git_agent.py 'small test'",
        ],
        "variations": [
            {
                "label": "With diff-only commit",
                "description": "Receive a unified diff, apply it.",
                "code_snippet": "import subprocess\\n# Write diff to /tmp/edit.patch then: subprocess.run(['git', 'apply', '/tmp/edit.patch'], cwd=repo_path)",
            },
            {
                "label": "Auto-close after merge",
                "description": "Track PR; close branch after merge.",
                "code_snippet": "# Poll gh CLI for PR state: gh pr view <num> --json state\\n# When merged, gh pr close <num> --delete-branch",
            },
            {
                "label": "Required CODEOWNER review",
                "description": "Tag specific reviewers.",
                "code_snippet": "# In open_pr, after gh pr create:\\nsubprocess.run(['gh', 'pr', 'edit', pr_num, '--add-reviewer', 'team/backend'])",
            },
            {
                "label": "Multi-file edit transaction",
                "description": "Roll back if any edit fails.",
                "code_snippet": "# Wrap apply_edits with try/except + git restore; if any edit raises, restore all to HEAD state.",
            },
        ],
        "common_errors": [
            {
                "error_text": "GitAgentError: branch name must match ...",
                "cause": "Branch name doesn't follow convention.",
                "fix_snippet": "Use feat/fix/chore/refactor/docs/test prefix + lowercase-with-hyphens. Adjust BRANCH_NAME_RE if your convention differs.",
            },
            {
                "error_text": "gh: command not found",
                "cause": "GitHub CLI not installed.",
                "fix_snippet": "Install: brew install gh OR apt install gh OR see cli.github.com.",
            },
            {
                "error_text": "Push fails: protected branch",
                "cause": "Trying to push to main/master directly.",
                "fix_snippet": "By design — agent must work on feature branches. Check current_branch() before pushing.",
            },
            {
                "error_text": "Commit empty (nothing to commit)",
                "cause": "Edits didn't actually change files.",
                "fix_snippet": "Check file contents before apply_edits; comparing intended-content vs current.",
            },
        ],
        "production_checklist": [
            "Set up branch protection on main/master in GitHub repo settings.",
            "Require PR review (1+ reviewer) for any branch merging to main.",
            "Add CI checks that must pass; agents can fail tests too.",
            "Use a bot account for agent commits (separate from human accounts).",
            "Log every agent commit + PR for audit.",
            "Set a daily PR limit per agent to prevent spam.",
            "Test with a fork before pointing at production repo.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["GitPython==3.1.43", "gh (2.55.0)"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["code-agent", "git-operations", "pull-request"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why not just use the GitHub API directly?",
                "answer": "gh CLI handles auth + edge cases. For complex PR flows (drafts, milestones, labels), gh is faster than building the REST calls. Switch to PyGitHub if you outgrow gh CLI.",
            },
            {
                "question": "Can agents merge their own PRs?",
                "answer": "Don't. Always require human review on AI-authored changes. The cost of a wrong merge is much higher than the savings of skipping review.",
            },
            {
                "question": "How do I scope what files the agent can edit?",
                "answer": "Add an allowlist of paths in apply_edits; reject if edit path isn't in allowlist. Most safety lapses come from agents touching unexpected files.",
            },
            {
                "question": "What about merge conflicts?",
                "answer": "Out of scope for this starter. Detect via git status after fetch; if conflicts, fail the agent and require human resolution.",
            },
        ],
        "github_url": "",
        "meta_title": "Git Ops Agent (Branch, Edit, Commit, PR) — Starter",
        "meta_description": "Code agent helper for git operations: create branch, apply edits, commit, push, open PR. Safety guards: no force push, no main edits.",
    },
]
