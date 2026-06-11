"""Code-agent starters — batch 3: E2B sandboxed executor, tree-sitter repo map, CI PR review agent."""

RECORDS = [
    {
        "slug": "e2b-sandboxed-code-agent",
        "title": "Sandboxed Code Agent With E2B (Execute, Observe, Iterate)",
        "tldr": "Never exec model-generated code on your host. E2B gives a cloud micro-VM per session: the agent writes code, runs it in the sandbox, reads stdout/stderr, and fixes its own errors in a bounded loop.",
        "category": "code-agents",
        "language": "python",
        "framework": "E2B + Anthropic",
        "tags": ["e2b", "sandbox", "code-agent", "anthropic"],
        "best_for_tags": ["code-execution", "data-analysis-agents", "untrusted-code"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Your agent needs to run code it just wrote (data analysis, scripting, calculations) and you cannot trust it on your host. E2B isolates each session in a cloud micro-VM, so a bad script affects only the sandbox.",
        "when_not_to_use": "Skip if the model only needs to return code for a human to run. Skip for offline/air-gapped setups where a cloud sandbox is not allowed (use a local Docker executor with the same interface).",
        "quick_start": "pip install e2b-code-interpreter anthropic && python e2b_agent.py",
        "full_code": '''"""Sandboxed code agent: write -> run in E2B -> read output -> fix -> repeat.

The model never touches your host. Code runs in an E2B micro-VM; the agent
loops up to MAX_ITERS, feeding execution errors back until the task succeeds.
"""
from __future__ import annotations

import os
import re
import sys

from anthropic import Anthropic
from e2b_code_interpreter import Sandbox


# ----------------- CONFIG -----------------

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
E2B_API_KEY = os.environ.get("E2B_API_KEY", "")  # read by Sandbox() from env
MAX_ITERS = 5
SANDBOX_TIMEOUT = 120  # seconds the sandbox stays alive

client = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM = (
    "You write Python to solve the task. Return ONLY a single fenced python code "
    "block, no prose. If given an error, fix the code and return the full block again."
)


# ----------------- CODE EXTRACTION -----------------

_FENCE = re.compile(r"```(?:python)?\\s*(.*?)```", re.DOTALL)


def extract_code(text: str) -> str:
    """Pull the python out of a markdown fence; fall back to the raw text."""
    m = _FENCE.search(text)
    return (m.group(1) if m else text).strip()


# ----------------- MODEL TURN -----------------

def write_code(task: str, last_error: str | None) -> str:
    prompt = task if last_error is None else f"{task}\\n\\nThe previous code failed:\\n{last_error}\\nFix it."
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return extract_code("".join(b.text for b in msg.content if b.type == "text"))


# ----------------- SANDBOX EXECUTION -----------------

def run_in_sandbox(sbx: Sandbox, code: str) -> tuple[bool, str]:
    """Execute code; return (ok, detail). Exceptions land in execution.error,
    prints land in execution.logs.stdout — they are NOT the same channel."""
    execution = sbx.run_code(code)
    if execution.error is not None:
        # name + value + traceback of an uncaught exception inside the sandbox
        return False, f"{execution.error.name}: {execution.error.value}"
    stdout = "".join(execution.logs.stdout)
    stderr = "".join(execution.logs.stderr)
    detail = stdout + (f"\\n[stderr] {stderr}" if stderr else "")
    return True, detail.strip()


# ----------------- AGENT LOOP -----------------

def solve(task: str) -> str:
    sbx = Sandbox(timeout=SANDBOX_TIMEOUT)
    try:
        # Demonstrate file IO into/out of the sandbox.
        sbx.files.write("/tmp/seed.txt", "10\\n20\\n30\\n")

        last_error: str | None = None
        for attempt in range(1, MAX_ITERS + 1):
            code = write_code(task, last_error)
            ok, detail = run_in_sandbox(sbx, code)
            if ok:
                print(f"[attempt {attempt}] success")
                return detail
            print(f"[attempt {attempt}] error: {detail}", file=sys.stderr)
            last_error = detail
        return f"Failed after {MAX_ITERS} attempts. Last error: {last_error}"
    finally:
        sbx.kill()  # ALWAYS release the sandbox or you leak (and pay for) it


def main() -> None:
    if not (ANTHROPIC_API_KEY and E2B_API_KEY):
        print("Set ANTHROPIC_API_KEY and E2B_API_KEY", file=sys.stderr)
        sys.exit(1)
    result = solve("Read /tmp/seed.txt, sum the integers, and print the total.")
    print("RESULT:\\n", result)


if __name__ == "__main__":
    main()
''',
        "dependencies": [
            {"name": "e2b-code-interpreter", "version": ">=1.0", "purpose": "Cloud sandbox with code execution (Sandbox, run_code, files)"},
            {"name": "anthropic", "version": ">=0.40", "purpose": "Model that writes and repairs the code"},
        ],
        "env_vars": [
            {"name": "E2B_API_KEY", "required": True, "description": "E2B API key; read from env by Sandbox()", "example": "e2b_..."},
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Anthropic API key for the coding model", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "Create an E2B account and get an API key from e2b.dev",
            "pip install e2b-code-interpreter anthropic",
            "export E2B_API_KEY=e2b_... and ANTHROPIC_API_KEY=sk-ant-...",
            "Run: python e2b_agent.py",
            "Confirm each run ends with sbx.kill() (no lingering sandboxes in the E2B dashboard)",
        ],
        "variations": [
            {"label": "Persistent sandbox across turns", "description": "Keep one sandbox alive for a multi-turn session instead of per call.", "code_snippet": "sbx = Sandbox(timeout=300)\\nsandbox_id = sbx.sandbox_id  # persist this\\n# later turn: sbx = Sandbox.connect(sandbox_id)  # reuse state/files across requests"},
            {"label": "Install packages at runtime", "description": "Let the agent add dependencies inside the sandbox.", "code_snippet": "sbx.commands.run('pip install pandas')\\n# then run_code that imports pandas; installs live only in this sandbox"},
            {"label": "Local Docker fallback executor", "description": "Same write/run/observe interface without a cloud sandbox.", "code_snippet": "# def run_local(code): return subprocess.run(['docker','run','--rm','-i','python:3.12','python','-c',code], capture_output=True, text=True, timeout=60)\\n# wrap to return (ok, stdout/stderr) like run_in_sandbox"},
        ],
        "common_errors": [
            {"error_text": "Sandbox closed / timeout mid-task", "cause": "Default sandbox lifetime is short for long agent loops.", "fix_snippet": "Pass Sandbox(timeout=...) for a longer life, or call sbx.set_timeout(...) to extend it during a run. Match the timeout to your worst-case loop."},
            {"error_text": "Bill higher than expected; many live sandboxes", "cause": "Sandboxes not killed; they bill while alive.", "fix_snippet": "Always sbx.kill() in a finally block (as shown). Audit the E2B dashboard for orphans and add a cap on concurrent sandboxes."},
            {"error_text": "SyntaxError running model output", "cause": "Code still wrapped in markdown fences.", "fix_snippet": "Strip the ```python ... ``` fence before run_code (see extract_code). Also instruct the model to return only a code block."},
            {"error_text": "Error not detected; agent thinks it passed", "cause": "Reading stderr instead of execution.error.", "fix_snippet": "Uncaught exceptions appear in execution.error (name/value/traceback), not logs.stderr. Check execution.error first; logs hold prints, not the failure."},
        ],
        "production_checklist": [
            "Always kill sandboxes in a finally block; they bill while alive.",
            "Cap the agent loop iterations so a stuck task cannot run forever.",
            "Check execution.error for failures; logs.stdout/stderr are not the error channel.",
            "Strip markdown fences from model output before executing.",
            "Set per-sandbox timeouts sized to the task; extend deliberately, not by default.",
            "Limit concurrent sandboxes and monitor spend in the E2B dashboard.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["e2b-code-interpreter==1.0", "anthropic==0.40"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["e2b", "e2b-e2b-dev"],
        "related_glossary_slugs": ["code-sandbox", "e2b-sandbox", "code-interpreter", "agent-loop", "agentic-ai"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why E2B instead of exec() locally?", "answer": "Model-generated code can delete files, exfiltrate data, or hang your process. E2B runs it in an isolated cloud micro-VM, so the blast radius is one disposable sandbox, not your host."},
            {"question": "execution.error vs logs.stderr?", "answer": "An uncaught exception in the sandbox populates execution.error (name, value, traceback). Anything the code prints goes to logs.stdout/stderr. Branch on execution.error for success/failure, then read logs for detail."},
            {"question": "How do I keep state across turns?", "answer": "Reuse one sandbox: save sbx.sandbox_id and reconnect with Sandbox.connect(id) on the next turn. Files and installed packages persist for that sandbox's lifetime, so the agent builds on prior steps."},
            {"question": "Can I run this offline?", "answer": "Not with E2B (it is a cloud service). For air-gapped use, swap run_in_sandbox for a local Docker executor that returns the same (ok, detail) tuple; the agent loop is unchanged."},
        ],
        "github_url": "https://github.com/e2b-dev/E2B",
        "meta_title": "Sandboxed Code Agent With E2B Starter",
        "meta_description": "Run agent-written code safely: E2B micro-VM per session, write-run-observe-fix loop, file IO, and always-kill cleanup. Anthropic model writes the code.",
    },
    {
        "slug": "tree-sitter-repo-map",
        "title": "Repo Map With tree-sitter: Codebase Context for Agents",
        "tldr": "Agents can't read a whole repo. The aider-style fix is a ranked symbol map: parse every file's definitions and references with tree-sitter, rank files by reference connectivity, and render a token-budgeted outline.",
        "category": "code-agents",
        "language": "python",
        "framework": "tree-sitter",
        "tags": ["tree-sitter", "repo-map", "context", "static-analysis"],
        "best_for_tags": ["swe-agents", "code-context", "large-repos"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Your coding agent needs whole-repo context but the codebase is far larger than the context window. A ranked symbol map gives the model a compact outline of where definitions live, so it reads structure instead of raw files.",
        "when_not_to_use": "Skip for tiny repos that fit in context (just paste the files). Skip if you only operate on one file at a time and never need cross-file structure.",
        "quick_start": "pip install tree-sitter tree-sitter-python && python repo_map.py ./your_project",
        "full_code": '''"""Repo map with tree-sitter: rank files by reference connectivity, render an outline.

Parse each .py file's definitions (functions/classes), count references to names
defined elsewhere, score files by how often they are referenced, and emit a
token-budgeted map the agent reads instead of full source.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor


# ----------------- PARSER (tree-sitter 0.23+ API) -----------------

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

# Capture definition names and every identifier reference.
DEF_QUERY = Query(PY_LANGUAGE, """
(function_definition name: (identifier) @def)
(class_definition name: (identifier) @def)
""")
REF_QUERY = Query(PY_LANGUAGE, "(identifier) @ref")

CHARS_PER_TOKEN = 4  # rough budget heuristic
MAX_FILE_BYTES = 200_000  # skip huge generated files


# ----------------- EXTRACTION -----------------

def parse_file(path: Path):
    """Return (defs, refs) for one file. node.text is BYTES — decode it."""
    src = path.read_bytes()
    tree = parser.parse(src)
    defs, refs = set(), set()
    for _, nodes in QueryCursor(DEF_QUERY).captures(tree.root_node).items():
        for n in nodes:
            defs.add(n.text.decode("utf-8", "replace"))
    for _, nodes in QueryCursor(REF_QUERY).captures(tree.root_node).items():
        for n in nodes:
            refs.add(n.text.decode("utf-8", "replace"))
    return defs, refs


# ----------------- RANK + RENDER -----------------

def build_map(root: Path, token_budget: int = 1024) -> str:
    file_defs: dict[Path, set] = {}
    file_refs: dict[Path, set] = {}
    for path in root.rglob("*.py"):
        if path.stat().st_size > MAX_FILE_BYTES:
            continue  # skip generated/vendored bloat
        try:
            file_defs[path], file_refs[path] = parse_file(path)
        except Exception as exc:  # unparseable file shouldn't kill the whole map
            print(f"skip {path}: {exc}", file=sys.stderr)

    # PageRank-lite: a file's score = how many OTHER files reference its defs.
    referenced_by = defaultdict(int)
    for path, defs in file_defs.items():
        for other, refs in file_refs.items():
            if other != path and defs & refs:
                referenced_by[path] += 1

    ranked = sorted(file_defs, key=lambda p: referenced_by[p], reverse=True)

    lines, used = [], 0
    for path in ranked:
        names = sorted(file_defs[path])
        if not names:
            continue
        rel = path.relative_to(root)
        line = f"{rel}: " + ", ".join(names[:12])
        if used + len(line) > token_budget * CHARS_PER_TOKEN:
            break  # respect the token budget
        lines.append(line)
        used += len(line)
    return "\\n".join(lines)


# ----------------- CLI -----------------

def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python repo_map.py <dir> [token_budget]", file=sys.stderr)
        sys.exit(1)
    root = Path(sys.argv[1])
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
    print(build_map(root, budget))


if __name__ == "__main__":
    main()
''',
        "dependencies": [
            {"name": "tree-sitter", "version": ">=0.23", "purpose": "Parsing runtime (Language/Parser/Query/QueryCursor)"},
            {"name": "tree-sitter-python", "version": ">=0.23", "purpose": "Compiled Python grammar wheel"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install tree-sitter tree-sitter-python  (keep core and grammar on matched 0.23+ versions)",
            "Save repo_map.py",
            "Run on a project: python repo_map.py ./your_project",
            "Tune the token budget: python repo_map.py ./your_project 2048",
            "Feed the printed map into your agent's system prompt as repo context",
        ],
        "variations": [
            {"label": "Multiple languages", "description": "Add grammar wheels and route by file extension.", "code_snippet": "import tree_sitter_javascript as tsjs\\nJS = Language(tsjs.language())\\n# pick PY_LANGUAGE vs JS by path.suffix; keep a separate DEF_QUERY per grammar"},
            {"label": "Signatures + docstring line", "description": "Show call signatures, not just names.", "code_snippet": "# extend DEF_QUERY to capture (parameters) @params and the first\\n# (expression_statement (string)) @doc under the body, then render 'def f(params)  # doc'"},
            {"label": "JSON output for the harness", "description": "Emit structured data instead of text.", "code_snippet": "import json\\nprint(json.dumps({str(p.relative_to(root)): sorted(d) for p, d in file_defs.items()}, indent=2))"},
        ],
        "common_errors": [
            {"error_text": "TypeError: Language() argument / Query() signature", "cause": "tree-sitter core and grammar wheels on mismatched versions; the API changed at 0.22/0.23.", "fix_snippet": "Pin both to >=0.23 and matched: pip install 'tree-sitter>=0.23' 'tree-sitter-python>=0.23'. Language(tspython.language()) and Query(LANG, src) are the 0.23 forms."},
            {"error_text": "TypeError: can't concat str to bytes", "cause": "node.text is bytes, not str.", "fix_snippet": "Decode it: n.text.decode('utf-8', 'replace'). All node text from tree-sitter is bytes."},
            {"error_text": "Nested defs missing from the map", "cause": "Walking node.children only catches top-level definitions.", "fix_snippet": "Use a Query (as here) or recurse the tree; queries match definitions at any depth, unlike a shallow children loop."},
            {"error_text": "Map dominated by one generated file", "cause": "A huge auto-generated module out-references everything.", "fix_snippet": "Skip by size (MAX_FILE_BYTES) and by glob (exclude migrations/, *_pb2.py, build/). Generated files crowd out the signal."},
        ],
        "production_checklist": [
            "Pin tree-sitter and every grammar wheel to matched >=0.23 versions.",
            "Decode node.text from bytes everywhere before string ops.",
            "Use queries (not shallow child walks) so nested definitions are captured.",
            "Exclude generated/vendored files by size and glob before ranking.",
            "Enforce the token budget when rendering so the map fits the model.",
            "Cache the map and invalidate per changed file rather than re-parsing the repo each call.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["tree-sitter==0.23", "tree-sitter-python==0.23"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["aider", "aider-paul-gauthier"],
        "related_glossary_slugs": ["context-engineering", "swe-agent", "agentic-ai", "context-window", "token-budget"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why a repo map instead of embeddings?", "answer": "A symbol map gives the model exact structure (which file defines what, what is central) deterministically and cheaply, with no index to maintain. Embeddings retrieve similar text; the map shows the skeleton an agent needs to navigate."},
            {"question": "How does the ranking work?", "answer": "Each file scores by how many other files reference the names it defines, a PageRank-lite signal for centrality. High-connectivity files (core modules) surface first and get the token budget; leaf files drop off when the budget runs out."},
            {"question": "Why pin tree-sitter and the grammar together?", "answer": "The core API changed around 0.22/0.23 and grammar wheels are ABI-coupled to the runtime. A mismatch throws on Language() or Query(). Pin both to the same >=0.23 line to avoid the most common breakage."},
            {"question": "Is node.text a string?", "answer": "No, it is bytes. Always decode with .decode('utf-8', 'replace') before concatenating or comparing as text; forgetting this is the second most common tree-sitter error after version drift."},
        ],
        "github_url": "https://github.com/tree-sitter/py-tree-sitter",
        "meta_title": "tree-sitter Repo Map for Agents Starter",
        "meta_description": "Give coding agents whole-repo context: parse defs/refs with tree-sitter, rank files by connectivity, render a token-budgeted symbol map. Aider-style.",
    },
    {
        "slug": "pr-review-agent-github-actions",
        "title": "PR Review Agent in GitHub Actions (Diff-Aware, Inline Comments)",
        "tldr": "A CI reviewer that comments inline. On pull_request, fetch the diff, chunk it per file, get structured findings as JSON, and post one review with inline comments via the REST API. Severity gate: request changes on high.",
        "category": "code-agents",
        "language": "python",
        "framework": "GitHub Actions + Anthropic",
        "tags": ["github-actions", "pr-review", "ci", "structured-output"],
        "best_for_tags": ["ci-automation", "code-review", "team-workflows"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "You want automated first-pass code review on every PR with comments anchored to the changed lines, not a wall of text. Runs in GitHub Actions, reads the diff, and posts a single structured review.",
        "when_not_to_use": "Skip if you only need a chat summary (no inline anchoring). Skip on huge generated PRs where per-line review adds noise; gate those out or review only source files.",
        "quick_start": "Add ANTHROPIC_API_KEY secret, drop review.py + workflow, open a PR",
        "full_code": '''"""PR review agent for GitHub Actions: diff -> structured findings -> inline review.

Reads the Actions context from env, fetches the PR diff, asks the model for a
strict JSON array of findings, and posts ONE review with inline comments.
Only comments on lines present in the diff (the API rejects others).
"""
from __future__ import annotations

import json
import os
import re
import sys

import requests
from anthropic import Anthropic

API = "https://api.github.com"
TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]          # "owner/name"
PR_NUMBER = os.environ["PR_NUMBER"]
MAX_COMMENTS = 15
SKIP = ("lock", "vendor/", "dist/", ".min.")

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}


# ----------------- FETCH DIFF -----------------

def get_diff() -> str:
    r = requests.get(
        f"{API}/repos/{REPO}/pulls/{PR_NUMBER}",
        headers={**HEADERS, "Accept": "application/vnd.github.v3.diff"},
        timeout=30,
    )
    r.raise_for_status()
    return r.text


def split_per_file(diff: str) -> dict[str, str]:
    """Split a unified diff into {path: hunk_text}, skipping noisy files."""
    files, current, buf = {}, None, []
    for line in diff.splitlines(keepends=True):
        if line.startswith("diff --git"):
            if current and not any(s in current for s in SKIP):
                files[current] = "".join(buf)
            m = re.search(r" b/(\\S+)", line)
            current, buf = (m.group(1) if m else None), []
        buf.append(line)
    if current and not any(s in current for s in SKIP):
        files[current] = "".join(buf)
    return files


# ----------------- MODEL: STRUCTURED FINDINGS -----------------

INSTRUCTION = (
    "Review this diff hunk. Return ONLY a JSON array. Each item: "
    '{"line": <int new-file line number>, "severity": "low|medium|high", '
    '"issue": "<what>", "suggestion": "<fix>"}. Empty array if no issues. No prose.'
)


def find_issues(path: str, hunk: str) -> list[dict]:
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1200,
        messages=[{"role": "user", "content": f"{INSTRUCTION}\\n\\nFile: {path}\\n{hunk}"}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text")
    return parse_findings(text)


def parse_findings(text: str) -> list[dict]:
    """json.loads with one repair attempt (extract the array substring)."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\\[.*\\]", text, re.DOTALL)
        if not m:
            return []
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return []


# ----------------- POST REVIEW -----------------

def post_review(comments: list[dict], counts: dict[str, int]) -> None:
    event = "REQUEST_CHANGES" if counts.get("high") else "COMMENT"
    body = f"Automated review: {counts.get('high',0)} high, {counts.get('medium',0)} medium, {counts.get('low',0)} low."
    payload = {"event": event, "body": body, "comments": comments[:MAX_COMMENTS]}
    r = requests.post(
        f"{API}/repos/{REPO}/pulls/{PR_NUMBER}/reviews",
        headers=HEADERS, json=payload, timeout=30,
    )
    if r.status_code >= 300:
        print(f"review POST failed {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    print(f"posted {event} with {len(payload['comments'])} comments")


# ----------------- MAIN -----------------

def main() -> None:
    files = split_per_file(get_diff())
    comments, counts = [], {"low": 0, "medium": 0, "high": 0}
    for path, hunk in files.items():
        for f in find_issues(path, hunk):
            sev = f.get("severity", "low")
            counts[sev] = counts.get(sev, 0) + 1
            # 'side': RIGHT anchors to the new (head) version of the file.
            comments.append({
                "path": path,
                "line": int(f["line"]),
                "side": "RIGHT",
                "body": f"**[{sev}]** {f.get('issue','')}\\n\\nSuggestion: {f.get('suggestion','')}",
            })
    if not comments:
        print("no findings")
        return
    post_review(comments, counts)


if __name__ == "__main__":
    main()
''',
        "dependencies": [
            {"name": "requests", "version": ">=2.31", "purpose": "GitHub REST API calls (diff fetch + review post)"},
            {"name": "anthropic", "version": ">=0.40", "purpose": "Model that produces structured findings"},
        ],
        "env_vars": [
            {"name": "GITHUB_TOKEN", "required": True, "description": "Provided automatically by Actions; needs pull-requests: write", "example": "${{ secrets.GITHUB_TOKEN }}"},
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Repo secret for the review model", "example": "sk-ant-..."},
            {"name": "GITHUB_REPOSITORY", "required": True, "description": "owner/name, set by Actions", "example": "octocat/hello-world"},
            {"name": "PR_NUMBER", "required": True, "description": "Pull request number from the event payload", "example": "42"},
        ],
        "setup_steps": [
            "Add ANTHROPIC_API_KEY as a repository secret",
            "Commit review.py to the repo",
            "Add the workflow (see the variation) with permissions: pull-requests: write",
            "Pass PR_NUMBER via env: ${{ github.event.pull_request.number }}",
            "Open a PR and watch the Actions run post an inline review",
        ],
        "variations": [
            {"label": "The workflow YAML", "description": "Trigger on PRs with the right permissions and secrets.", "code_snippet": "name: pr-review\\non: { pull_request: {} }\\npermissions: { contents: read, pull-requests: write }\\njobs:\\n  review:\\n    runs-on: ubuntu-latest\\n    steps:\\n      - uses: actions/checkout@v4\\n      - uses: actions/setup-python@v5\\n        with: { python-version: '3.12' }\\n      - run: pip install requests anthropic\\n      - run: python review.py\\n        env:\\n          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}\\n          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}\\n          PR_NUMBER: ${{ github.event.pull_request.number }}"},
            {"label": "Incremental review", "description": "Only review commits pushed since the last review.", "code_snippet": "# GET /repos/{repo}/pulls/{n}/reviews, find your bot's latest submitted_at,\\n# then diff against that commit's SHA instead of the full PR diff"},
            {"label": "Inject org conventions", "description": "Feed a CONVENTIONS.md so reviews match house style.", "code_snippet": "rules = open('CONVENTIONS.md').read()\\n# prepend rules to INSTRUCTION so findings cite your style guide, not generic advice"},
        ],
        "common_errors": [
            {"error_text": "422 Unprocessable Entity on review POST", "cause": "Commenting on a line not present in the diff.", "fix_snippet": "Only post comments on lines that appear in the diff hunk (added/changed). Validate each finding's line against the parsed hunk before adding it."},
            {"error_text": "Model returns prose around the JSON", "cause": "Output not strictly a JSON array.", "fix_snippet": "Keep the strict instruction, then json.loads with a regex fallback that extracts the [...] substring and one retry (see parse_findings)."},
            {"error_text": "Token limit / truncated review on big PRs", "cause": "Whole diff sent at once.", "fix_snippet": "Chunk per file, skip lockfiles/vendored, and cap total comments (MAX_COMMENTS). Large diffs must be split or the model truncates."},
            {"error_text": "403 Resource not accessible by integration", "cause": "Workflow lacks pull-requests: write permission.", "fix_snippet": "Add permissions: { pull-requests: write } to the workflow (or job). The default GITHUB_TOKEN is read-only for many events."},
        ],
        "production_checklist": [
            "Grant the workflow pull-requests: write; the default token is often read-only.",
            "Only comment on lines present in the diff or the API returns 422.",
            "Chunk per file and skip lockfiles/vendored/min files before review.",
            "Cap total inline comments so large PRs do not flood the author.",
            "Parse model JSON defensively (strict instruction + extraction + one retry).",
            "Gate severity: request changes on high, comment otherwise; keep the bot non-blocking elsewhere.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["requests==2.31", "anthropic==0.40"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["github-mcp-server"],
        "related_glossary_slugs": ["agentic-ai", "structured-output", "swe-agent", "json-mode"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why inline comments over a summary?", "answer": "Inline comments anchor each finding to the exact changed line, so authors fix issues in context. A summary forces them to map prose back to code. This posts one review with positioned comments via the reviews endpoint."},
            {"question": "Why do I get 422 errors?", "answer": "GitHub rejects review comments on lines that are not part of the diff. Only comment on added/changed lines, use side 'RIGHT' for the head version, and validate each line against the parsed hunk before posting."},
            {"question": "How do I stop it flooding huge PRs?", "answer": "Chunk the diff per file, skip lockfiles and vendored/minified files, and cap MAX_COMMENTS (15 here). For generated-heavy PRs, review only source paths or gate the workflow off."},
            {"question": "What permissions does the workflow need?", "answer": "pull-requests: write so the GITHUB_TOKEN can post a review; contents: read to check out code. Without the write scope you get 403 'Resource not accessible by integration'."},
        ],
        "github_url": "https://github.com/anthropics/anthropic-sdk-python",
        "meta_title": "PR Review Agent in GitHub Actions Starter",
        "meta_description": "Automated diff-aware PR review in CI: fetch the diff, structured JSON findings, inline comments via REST, severity gate. Runs in GitHub Actions.",
    },
]
