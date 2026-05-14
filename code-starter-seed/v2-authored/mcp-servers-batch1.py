"""MCP server starters — FastMCP, custom tools, OAuth."""

RECORDS = [
    {
        "slug": "fastmcp-tool-server-stdio",
        "title": "FastMCP Tool Server Over Stdio",
        "tldr": "Minimal MCP (Model Context Protocol) server exposing tools to Claude Desktop / Cursor / any MCP client over stdio. Type-hinted tools become callable from the host LLM in under 50 lines.",
        "category": "mcp-servers",
        "language": "python",
        "framework": "FastMCP",
        "tags": ["mcp", "fastmcp", "tools", "claude-desktop"],
        "best_for_tags": ["claude-desktop", "ide-integrations", "local-tools"],
        "difficulty_tier": "beginner",
        "featured": True,
        "when_to_use": "When you want Claude Desktop, Cursor, or another MCP client to call your custom tools — file ops, database queries, API wrappers — without writing client-side glue code.",
        "when_not_to_use": "Skip when your tools are HTTP-callable and the LLM can call them directly. Skip for production APIs serving many users (MCP is for single-user IDE-style integrations, not multi-tenant servers).",
        "quick_start": "pip install fastmcp && python my_mcp.py  # then configure Claude Desktop to run this",
        "full_code": '''"""FastMCP server exposing a few tools over stdio.

Run via stdio so MCP clients (Claude Desktop, Cursor) can spawn it.
Configure the client to launch this script; the protocol handshake is automatic.

Example Claude Desktop config (~/.../claude_desktop_config.json):
{
  "mcpServers": {
    "ossaihub-tools": {
      "command": "python",
      "args": ["/abs/path/to/my_mcp.py"]
    }
  }
}
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

# Create the server. The name appears in the MCP client's tool list.
mcp = FastMCP("ossaihub-tools")


@mcp.tool()
def now_utc() -> str:
    """Return the current UTC time in ISO 8601 format.

    The LLM will use this when the user asks ‘what time is it’ or needs a fresh
    timestamp for a record.
    """
    return datetime.now(timezone.utc).isoformat()


@mcp.tool()
def read_text_file(path: str, *, max_chars: int = 5000) -> str:
    """Read a text file from the local filesystem.

    Args:
        path: Absolute or relative path to a text file.
        max_chars: Maximum characters to return (truncate from the end).

    Returns:
        The file contents (possibly truncated). Errors return an "ERROR: ..." string.
    """
    try:
        p = Path(path).expanduser().resolve()
        # Soft sandbox: only allow paths under the user's home dir
        home = Path.home().resolve()
        if home not in p.parents and p != home:
            return f"ERROR: refusing to read outside home dir ({p})"
        text = p.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_chars:
            text = text[:max_chars] + f"\\n... [truncated, {len(text)} total chars]"
        return text
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def append_to_log(message: str, *, log_path: str = "~/mcp_demo.log") -> str:
    """Append a message to a log file. Returns 'ok' or 'ERROR: ...'."""
    try:
        p = Path(log_path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} {message}\\n")
        return "ok"
    except Exception as e:
        return f"ERROR: {e}"


@mcp.resource("file://{path}")
def file_resource(path: str) -> str:
    """Expose any file as a readable resource.

    The MCP client can ‘attach’ this resource to a conversation; the LLM
    sees the content without needing a separate tool call.
    """
    return read_text_file(path)


@mcp.prompt("daily-standup")
def daily_standup_prompt(yesterday: str = "", today: str = "", blockers: str = "") -> str:
    """A reusable prompt template the MCP client can offer the user."""
    return (
        "Write a 3-bullet daily standup update:\\n"
        f"- Yesterday: {yesterday or '(fill in)'}\\n"
        f"- Today: {today or '(fill in)'}\\n"
        f"- Blockers: {blockers or '(none)'}"
    )


if __name__ == "__main__":
    mcp.run()  # stdio by default
''',
        "dependencies": [
            {"name": "fastmcp", "version": ">=2.0", "purpose": "MCP server framework"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install fastmcp",
            "Save as my_mcp.py and chmod +x.",
            "Add to Claude Desktop config (see docstring).",
            "Restart Claude Desktop; the tool list should now include now_utc / read_text_file / append_to_log.",
            "Ask Claude: 'What's the current UTC time?' to verify.",
        ],
        "variations": [
            {
                "label": "HTTP/SSE transport",
                "description": "Serve over HTTP for remote clients.",
                "code_snippet": "mcp.run(transport='sse', host='0.0.0.0', port=8000)\\n# Client config uses 'url': 'http://host:8000/sse'",
            },
            {
                "label": "Async tool",
                "description": "Long-running tools.",
                "code_snippet": "@mcp.tool()\\nasync def slow_lookup(query: str) -> dict:\\n    async with httpx.AsyncClient() as c:\\n        r = await c.get(...); return r.json()",
            },
            {
                "label": "Tool with rich return",
                "description": "Return structured content.",
                "code_snippet": "from mcp.types import TextContent, ImageContent\\n@mcp.tool()\\ndef chart() -> list:\\n    return [TextContent('caption'), ImageContent(data=b64, mime_type='image/png')]",
            },
            {
                "label": "Auth-wrapped tools",
                "description": "Restrict by env-supplied token.",
                "code_snippet": "@mcp.tool()\\ndef sensitive_op(query: str) -> str:\\n    if not os.environ.get('MCP_TOKEN') == EXPECTED:\\n        return 'ERROR: unauthorized'\\n    return ...",
            },
        ],
        "common_errors": [
            {
                "error_text": "Claude Desktop says ‘server failed to start’",
                "cause": "Python not on PATH or script path wrong.",
                "fix_snippet": "Use absolute python path in command: '/usr/bin/python3' or '/opt/homebrew/bin/python'. Absolute script path in args.",
            },
            {
                "error_text": "Tool list is empty in Claude Desktop",
                "cause": "Server crashed during startup.",
                "fix_snippet": "Run the script manually: `python my_mcp.py`; it should hang waiting for stdin. Check Claude Desktop logs (~/Library/Logs/Claude/mcp-*.log on macOS).",
            },
            {
                "error_text": "Tool returns ERROR for legitimate file reads",
                "cause": "Sandbox in read_text_file rejects path.",
                "fix_snippet": "Adjust the sandbox check; for production set a strict allowlist of base paths.",
            },
            {
                "error_text": "JSON parse error in client logs",
                "cause": "Stray print() in tool code went to stdout (conflicts with stdio protocol).",
                "fix_snippet": "Never print to stdout from an MCP server using stdio transport. Log to stderr (logging module) or to a file. Stdout is reserved for the protocol.",
            },
        ],
        "production_checklist": [
            "Never let tools execute arbitrary code from arguments without sandboxing.",
            "Set strict path allowlists for filesystem tools.",
            "Log to stderr or a file, never stdout (stdio transport).",
            "Validate every tool input — the LLM can pass malformed/malicious args.",
            "Document tool behavior in the docstring; the LLM uses it to decide when to call.",
            "For HTTP transport, add auth (env-supplied token at minimum).",
            "Pin fastmcp version; protocol is still evolving.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-7-sonnet (via Claude Desktop)"],
            "library_versions": ["fastmcp==2.2.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["fastmcp"],
        "related_glossary_slugs": ["mcp", "model-context-protocol", "tool-server"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "What is MCP?",
                "answer": "Model Context Protocol — an open spec from Anthropic that lets LLM hosts (Claude Desktop, Cursor) call out to external tool servers via stdio or HTTP. Standardizes the ‘give the LLM access to local tools’ pattern.",
            },
            {
                "question": "How is this different from OpenAI function calling?",
                "answer": "Function calling is in-API; the developer defines tools in each call. MCP is a separate process the host LLM connects to — multiple hosts can share the same server.",
            },
            {
                "question": "Can I use this with non-Claude clients?",
                "answer": "Yes — Cursor, Cline, Continue, and others support MCP. The server doesn't know which client connected.",
            },
            {
                "question": "Is FastMCP the official SDK?",
                "answer": "It's a popular community wrapper around the official Python SDK; lower boilerplate. The official anthropic/mcp Python SDK works too if you prefer no extra dependencies.",
            },
        ],
        "github_url": "https://github.com/jlowin/fastmcp",
        "meta_title": "FastMCP Tool Server Over Stdio — Starter",
        "meta_description": "Build an MCP server exposing tools to Claude Desktop, Cursor, etc. — type-hinted Python functions become callable LLM tools in <50 lines.",
    },
    {
        "slug": "mcp-server-http-with-auth",
        "title": "MCP Server Over HTTP With Bearer Auth",
        "tldr": "MCP server transport over HTTP/SSE with bearer-token auth — useful for shared internal tools accessed by multiple developers' MCP clients without per-machine setup.",
        "category": "mcp-servers",
        "language": "python",
        "framework": "FastMCP",
        "tags": ["mcp", "http", "auth", "sse", "shared-tools"],
        "best_for_tags": ["team-tools", "remote-mcp", "shared-services"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When several team members need access to the same MCP tools (DB queries, internal APIs) — host once over HTTP, distribute the URL + token, no per-laptop install needed.",
        "when_not_to_use": "Skip for tools that need local filesystem or hardware (USB, webcam) — stdio + local server is the right pattern there.",
        "quick_start": "pip install fastmcp uvicorn && MCP_TOKEN=secret python http_mcp.py",
        "full_code": '''"""MCP server over HTTP with simple bearer-token auth.

Clients (Claude Desktop, Cursor) connect via 'url': 'http://host:port/sse'
and 'headers': {'Authorization': 'Bearer ...'} in their config.

This pattern is for internal shared tools — for production multi-tenant
servers, use a real auth provider (Auth0, your IdP, OAuth).
"""
from __future__ import annotations

import json
import os
from typing import Callable

from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

EXPECTED_TOKEN = os.environ.get("MCP_TOKEN", "")


class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next: Callable):
        if request.url.path.startswith("/healthz"):
            return await call_next(request)
        auth = request.headers.get("Authorization", "")
        if not EXPECTED_TOKEN or auth != f"Bearer {EXPECTED_TOKEN}":
            return Response("unauthorized", status_code=401)
        return await call_next(request)


mcp = FastMCP("internal-tools")


@mcp.tool()
def query_db(sql: str) -> str:
    """Run a SELECT against the analytics warehouse. Read-only.

    Args:
        sql: SQL statement. Must be a SELECT. Other statements are rejected.

    Returns:
        Tab-separated result rows.
    """
    if not sql.lstrip().lower().startswith("select"):
        return "ERROR: only SELECT statements allowed"
    # Replace with real warehouse client (BigQuery, Snowflake, etc.)
    return "id\\tname\\n1\\tAcme\\n2\\tWidget Co"


@mcp.tool()
def fetch_user(user_id: str) -> dict:
    """Fetch a user record by ID from the internal API.

    Args:
        user_id: The user's UUID.

    Returns:
        User dict, or {"error": "..."} if not found.
    """
    # Replace with real API call
    return {"id": user_id, "name": "Jane", "email": "jane@example.com", "plan": "pro"}


def build_app():
    # FastMCP's SSE transport returns a Starlette app
    app = mcp.sse_app()
    # Wrap with auth middleware
    app.add_middleware(BearerAuthMiddleware)
    return app


if __name__ == "__main__":
    import uvicorn

    if not EXPECTED_TOKEN:
        print("ERROR: set MCP_TOKEN env var")
        raise SystemExit(2)

    uvicorn.run(build_app(), host="0.0.0.0", port=8000)
''',
        "dependencies": [
            {"name": "fastmcp", "version": ">=2.0", "purpose": "MCP server"},
            {"name": "uvicorn", "version": ">=0.30", "purpose": "ASGI server"},
            {"name": "starlette", "version": ">=0.40", "purpose": "Used for middleware"},
        ],
        "env_vars": [
            {"name": "MCP_TOKEN", "required": True, "description": "Bearer token clients must present", "example": "long-random-string"},
        ],
        "setup_steps": [
            "pip install fastmcp uvicorn starlette",
            "Generate a token: openssl rand -hex 32",
            "export MCP_TOKEN=<the token>",
            "python http_mcp.py",
            "Configure Claude Desktop: {'mcpServers':{'internal':{'url':'http://host:8000/sse','headers':{'Authorization':'Bearer <token>'}}}}",
        ],
        "variations": [
            {
                "label": "JWT auth (Auth0 / your IdP)",
                "description": "Validate JWTs instead of static tokens.",
                "code_snippet": "from jose import jwt\\nclaims = jwt.decode(token, public_key, algorithms=['RS256'], audience='mcp')",
            },
            {
                "label": "Per-user tool access",
                "description": "Restrict tools based on caller identity.",
                "code_snippet": "request.state.user = claims['sub']\\n# In tool: if mcp.context.request.state.user not in ALLOWED: raise PermissionError",
            },
            {
                "label": "Behind a reverse proxy",
                "description": "Use Caddy/Nginx for TLS.",
                "code_snippet": "# Caddy: yourhost { reverse_proxy /sse* localhost:8000 }\\n# uvicorn listens on localhost only, TLS terminates at the proxy.",
            },
            {
                "label": "Streaming HTTP (no SSE)",
                "description": "MCP supports streamable HTTP as alternative to SSE.",
                "code_snippet": "app = mcp.streamable_http_app()\\n# Client config 'transport': 'streamable_http'",
            },
        ],
        "common_errors": [
            {
                "error_text": "401 unauthorized when client tries to connect",
                "cause": "Token mismatch or missing.",
                "fix_snippet": "Verify Authorization header is 'Bearer <token>' (exact spelling, single space). Check MCP_TOKEN matches what's in the client config.",
            },
            {
                "error_text": "CORS preflight fails",
                "cause": "Browser-based MCP clients hit CORS.",
                "fix_snippet": "Add CORSMiddleware with explicit allow_origins. For internal use, set to your team's domains; don't '*'.",
            },
            {
                "error_text": "SSE connection drops after 60s",
                "cause": "Reverse proxy timeout.",
                "fix_snippet": "Configure proxy timeout: nginx `proxy_read_timeout 86400s` or Caddy `transport http { read_timeout 24h }`.",
            },
            {
                "error_text": "Tool runs but client doesn't receive output",
                "cause": "Tool yielded incomplete content blocks.",
                "fix_snippet": "Ensure tool return type matches signature (str or list[TextContent]). Check fastmcp logs on the server.",
            },
        ],
        "production_checklist": [
            "Always use TLS in production; bearer tokens over HTTP are sniffable.",
            "Rotate tokens periodically; distribute via 1Password or similar.",
            "Add rate limiting per-token (slowapi or your reverse proxy).",
            "Log every tool call with token-id (not the raw token) for audit.",
            "Use OAuth2/OIDC for human users; bearer tokens are fine for machine-to-machine.",
            "Test with a non-admin token to verify privilege boundaries.",
            "Pin fastmcp version; transport spec is still evolving.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-7-sonnet (via Claude Desktop)"],
            "library_versions": ["fastmcp==2.2.0", "uvicorn==0.32.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["fastmcp"],
        "related_glossary_slugs": ["mcp", "sse", "bearer-auth"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why not just use a REST API?",
                "answer": "MCP gives you tool discovery, structured returns, prompt templates, and resources in one protocol. REST is fine if your LLM client can call REST directly — MCP shines when the client is a host (Claude Desktop) that needs uniform tool access.",
            },
            {
                "question": "How do I run this in Kubernetes?",
                "answer": "Standard FastAPI/Starlette deployment. Expose port 8000, terminate TLS at ingress, mount secrets for MCP_TOKEN. Health check at /healthz (bypasses auth in the starter).",
            },
            {
                "question": "Can multiple users share one token?",
                "answer": "Don't — tokens should be per-user for audit and revocation. Use a real auth provider (Auth0, Okta) for production.",
            },
            {
                "question": "SSE vs streamable HTTP?",
                "answer": "SSE is older, widely supported, works through most proxies. Streamable HTTP (newer MCP) is more efficient. Test which your clients support — Claude Desktop supports both.",
            },
        ],
        "github_url": "https://github.com/jlowin/fastmcp",
        "meta_title": "MCP Server Over HTTP With Bearer Auth — Starter",
        "meta_description": "Internal MCP server with HTTP/SSE transport and bearer-token auth — shared team tools, no per-machine install.",
    },
]
