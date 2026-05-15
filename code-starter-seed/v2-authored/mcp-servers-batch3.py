"""MCP server starters — batch 3: TS client, resources+prompts, stdio-to-HTTP bridge, inspector testing."""

RECORDS = [
    {
        "slug": "mcp-typescript-client",
        "title": "MCP TypeScript Client: Connect to Any MCP Server",
        "tldr": "Build a TypeScript client that connects to MCP servers via stdio or HTTP, lists their tools, and calls them. Foundation for embedding MCP into Node-based agent frameworks.",
        "category": "mcp-servers",
        "language": "typescript",
        "framework": "@modelcontextprotocol/sdk",
        "tags": ["mcp", "typescript", "client", "sdk"],
        "best_for_tags": ["node-apps", "mcp-integration", "agent-tooling"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Building a Node.js / Bun / TS agent app that needs MCP server integration. The official TS SDK gives you typed access to any MCP server's tools / resources / prompts.",
        "when_not_to_use": "Skip if your stack is purely Python (use the Python MCP SDK). Skip for simple one-off scripts where direct HTTP is easier than the MCP abstraction.",
        "quick_start": "npm i @modelcontextprotocol/sdk && tsx mcp_client.ts",
        "full_code": '''/**
 * MCP TypeScript client: connect, discover tools, call them.
 *
 * Works with stdio (subprocess) or HTTP (SSE) transports.
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";


// ----------------- CONNECT (stdio) -----------------

async function connectStdio(command: string, args: string[]) {
  const transport = new StdioClientTransport({ command, args });
  const client = new Client(
    { name: "demo-client", version: "1.0.0" },
    { capabilities: { tools: {}, resources: {}, prompts: {} } }
  );
  await client.connect(transport);
  return client;
}


// ----------------- CONNECT (HTTP/SSE) -----------------

async function connectHttp(url: string) {
  const transport = new SSEClientTransport(new URL(url));
  const client = new Client(
    { name: "demo-client", version: "1.0.0" },
    { capabilities: {} }
  );
  await client.connect(transport);
  return client;
}


// ----------------- DISCOVER + CALL -----------------

async function discover(client: Client) {
  const tools = await client.listTools();
  console.log("Tools:");
  for (const t of tools.tools) {
    console.log(`  - ${t.name}: ${t.description}`);
  }

  const resources = await client.listResources();
  console.log(`Resources: ${resources.resources.length}`);

  const prompts = await client.listPrompts();
  console.log(`Prompts: ${prompts.prompts.length}`);
}


async function callTool(client: Client, name: string, args: Record<string, unknown>) {
  const result = await client.callTool({ name, arguments: args });
  if (result.isError) {
    throw new Error(`Tool error: ${JSON.stringify(result.content)}`);
  }
  return result.content;
}


// ----------------- ROBUSTNESS -----------------

async function callToolWithRetry(
  client: Client,
  name: string,
  args: Record<string, unknown>,
  maxRetries = 3
) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await callTool(client, name, args);
    } catch (e) {
      if (attempt === maxRetries) throw e;
      const backoff = 1000 * Math.pow(2, attempt);
      console.error(`Attempt ${attempt + 1} failed; retrying in ${backoff}ms`);
      await new Promise((r) => setTimeout(r, backoff));
    }
  }
}


// ----------------- DEMO -----------------

async function main() {
  // Stdio example — launch a server subprocess
  const stdioClient = await connectStdio("npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]);
  await discover(stdioClient);
  const result = await callToolWithRetry(stdioClient, "list_directory", { path: "/tmp" });
  console.log("Files:", result);
  await stdioClient.close();

  // HTTP example
  // const httpClient = await connectHttp("http://localhost:3000/sse");
  // await discover(httpClient);
}

main().catch(console.error);
''',
        "dependencies": [
            {"name": "@modelcontextprotocol/sdk", "version": ">=1.0", "purpose": "Official MCP TS SDK"},
            {"name": "tsx", "version": ">=4.0", "purpose": "Run TS files directly"},
        ],
        "env_vars": [],
        "setup_steps": [
            "npm init -y && npm i @modelcontextprotocol/sdk",
            "npm i -D tsx typescript @types/node",
            "Save mcp_client.ts",
            "npx tsx mcp_client.ts",
        ],
        "variations": [
            {"label": "Stream tool results", "description": "Long-running tool with progress events.", "code_snippet": "// Use client.callTool({ name, arguments }, { signal }) and listen for progress notifications via client.notification('progress', handler)"},
            {"label": "Multiple server connections", "description": "Aggregate tools across servers.", "code_snippet": "const clients = await Promise.all([connectStdio(...), connectHttp(...)]); // pool, route by tool name"},
            {"label": "TypeScript types from server schema", "description": "Generate types from tool input_schema.", "code_snippet": "// Use json-schema-to-typescript or zod-from-json-schema to generate types from the listTools() response"},
        ],
        "common_errors": [
            {"error_text": "EPIPE / connection closed", "cause": "Server subprocess crashed.", "fix_snippet": "Wrap client.close() in finally. Capture subprocess stderr to debug. Add health check (callTool with a known-good ping)."},
            {"error_text": "Tool args fail server validation", "cause": "Schema mismatch.", "fix_snippet": "After listTools(), validate args against the input_schema BEFORE callTool. Use ajv or zod-from-json-schema."},
            {"error_text": "SSE connection times out", "cause": "Server doesn't keep-alive.", "fix_snippet": "Add keep-alive heartbeats from server (every 25s). On client, configure SSE retry policy."},
            {"error_text": "Server requires auth header", "cause": "Production MCP HTTP servers require bearer tokens.", "fix_snippet": "Pass headers to SSEClientTransport: new SSEClientTransport(url, { requestInit: { headers: { Authorization: `Bearer ${token}` }}})"},
        ],
        "production_checklist": [
            "Connection pooling: reuse clients, don't recreate per call.",
            "Catch + retry transient errors with exponential backoff.",
            "Validate tool args against schema client-side first.",
            "Log all tool calls + responses for debugging.",
            "Pin MCP SDK version; protocol evolves.",
            "Use HTTP transport (not stdio) for distributed deployments.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["@modelcontextprotocol/sdk==1.0", "Node.js 20"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["mcp"],
        "related_glossary_slugs": ["mcp", "tool-use"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "MCP vs OpenAI tools?", "answer": "MCP is a protocol; tools are a feature. MCP lets ANY LLM client connect to ANY tool server. OpenAI tools is OpenAI-specific. MCP wraps tools + resources + prompts in a discoverable protocol."},
            {"question": "Why TypeScript client?", "answer": "Node.js apps (e.g., Claude Desktop, Cursor, Continue) embed TS code. The official MCP SDK is TS-first. Use this for Cursor extensions, custom IDE plugins, agent frameworks."},
            {"question": "Stdio vs HTTP transport?", "answer": "Stdio: server is a subprocess; simple ops, no auth needed (local trust). HTTP: distributed, needs auth, scalable. Use stdio for desktop/local; HTTP for prod/multi-tenant."},
            {"question": "How discover MCP servers?", "answer": "No central registry yet (early protocol). Discoverable via documented stdio commands or HTTP URLs. The Anthropic MCP marketplace is emerging."},
        ],
        "github_url": "https://github.com/modelcontextprotocol/typescript-sdk",
        "meta_title": "MCP TypeScript Client Starter",
        "meta_description": "Connect to MCP servers from TypeScript: stdio + HTTP transports, tool discovery, retry, auth, production-grade defaults.",
    },
    {
        "slug": "mcp-server-resources-and-prompts",
        "title": "MCP Server With Resources + Prompts (Full Spec)",
        "tldr": "MCP server that exposes TOOLS, RESOURCES (read-only data refs), and PROMPTS (reusable templates). Used by Claude Desktop and Cursor for richer agent experiences.",
        "category": "mcp-servers",
        "language": "python",
        "framework": "mcp Python SDK",
        "tags": ["mcp", "resources", "prompts", "claude-desktop"],
        "best_for_tags": ["claude-desktop", "cursor", "internal-tooling"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Building MCP servers for Claude Desktop / Cursor / Continue. Tools alone are limiting; resources give the model passive context, prompts give reusable templates. Full MCP server > tools-only.",
        "when_not_to_use": "Skip for stdio-only agent integrations that just need tool-calling. Skip if your data fits cleanly as tool outputs (no need for resources abstraction).",
        "quick_start": "pip install mcp && python full_mcp_server.py",
        "full_code": '''"""Full MCP server: tools + resources + prompts."""
from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, ImageContent


mcp = FastMCP("docs-and-tools")


# ----------------- TOOLS -----------------

@mcp.tool()
def search_docs(query: str, limit: int = 5) -> str:
    """Search internal documentation by keyword."""
    # Replace with real search
    return json.dumps([
        {"title": f"Doc on {query}", "url": "/docs/example", "excerpt": "..."},
    ][:limit])


@mcp.tool()
def create_ticket(title: str, body: str, priority: str = "medium") -> str:
    """Create a new support ticket. Returns ticket ID."""
    # Replace with real ticket-creation call
    return json.dumps({"ticket_id": "T-12345", "status": "created"})


# ----------------- RESOURCES (read-only data the model can browse) -----------------

DOCS_DIR = Path("./docs")  # adjust to your real docs folder


@mcp.resource("docs://index")
def docs_index() -> str:
    """The full doc index (list of available docs)."""
    if not DOCS_DIR.exists():
        return "No docs available"
    return "\\n".join(f"- {p.relative_to(DOCS_DIR)}" for p in DOCS_DIR.rglob("*.md"))


@mcp.resource("docs://{path}")
def doc_content(path: str) -> str:
    """Read a specific doc by path."""
    target = DOCS_DIR / path
    if not target.is_file() or not target.suffix == ".md":
        return f"Not found: {path}"
    # Security: ensure path doesn't escape DOCS_DIR
    if DOCS_DIR.resolve() not in target.resolve().parents:
        raise ValueError("Path traversal blocked")
    return target.read_text()


@mcp.resource("config://current")
def current_config() -> str:
    """Expose runtime config (read-only)."""
    return json.dumps({"env": "prod", "version": "1.4.0"})


# ----------------- PROMPTS (reusable templates the model can invoke) -----------------

@mcp.prompt()
def write_pr_description(diff_summary: str, ticket_id: str) -> str:
    """Generate a PR description from a diff summary + ticket."""
    return f"""Write a clean PR description for:

Ticket: {ticket_id}
Diff summary: {diff_summary}

Format:
## What changed
## Why
## How to test
## Risks"""


@mcp.prompt()
def triage_ticket(ticket_text: str) -> list:
    """Triage a customer support ticket — returns multi-message conversation."""
    return [
        {"role": "user", "content": {"type": "text", "text": f"Triage this:\\n\\n{ticket_text}"}},
        {"role": "assistant", "content": {"type": "text", "text": "I'll classify category + priority, then suggest a response."}},
    ]


# ----------------- RUN -----------------

if __name__ == "__main__":
    # Stdio mode for Claude Desktop / Cursor
    mcp.run(transport="stdio")
''',
        "dependencies": [
            {"name": "mcp", "version": ">=1.0", "purpose": "Official MCP Python SDK"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install mcp",
            "Save full_mcp_server.py",
            "Test directly: python full_mcp_server.py (will hang waiting for stdio)",
            "Add to Claude Desktop config: ~/.../claude/claude_desktop_config.json",
            'Config: {"mcpServers": {"docs": {"command": "python", "args": ["/abs/path/full_mcp_server.py"]}}}',
        ],
        "variations": [
            {"label": "HTTP transport (multi-tenant)", "description": "Serve over HTTP/SSE instead of stdio.", "code_snippet": "from mcp.server.fastmcp.server import http_server\\nhttp_server(mcp, host='0.0.0.0', port=8000)"},
            {"label": "Image resources", "description": "Expose images / files as resources.", "code_snippet": "@mcp.resource('images://{name}')\\ndef get_image(name: str) -> bytes: return Path(f'./images/{name}').read_bytes()  # MCP handles base64"},
            {"label": "Prompt with args", "description": "Parameterized prompts.", "code_snippet": "@mcp.prompt()\\ndef code_review(file_path: str, language: str = 'python') -> str: return f'Review {file_path}, lang={language}'"},
        ],
        "common_errors": [
            {"error_text": "Resource URI not matching", "cause": "Wrong scheme/path format.", "fix_snippet": "Resource URIs use scheme://path. Match the decorator pattern exactly. For dynamic paths, use {placeholder} syntax."},
            {"error_text": "Path traversal vulnerability", "cause": "Resource handler doesn't sanitize input.", "fix_snippet": "Always resolve + check that the resolved path is INSIDE the allowed root. See the doc_content example."},
            {"error_text": "Claude Desktop doesn't see server", "cause": "Config error or path wrong.", "fix_snippet": "Use absolute paths in claude_desktop_config.json. Restart Claude Desktop after config changes. Check stderr in /var/log or Console.app."},
            {"error_text": "Resources too large for context", "cause": "Returning megabytes of data.", "fix_snippet": "Resources should be small-to-medium. For large data, use a TOOL that the model invokes when needed, not a passive resource."},
        ],
        "production_checklist": [
            "Sanitize all resource path inputs (path-traversal protection).",
            "Add request-level rate limiting at the transport layer.",
            "Authenticate (HTTP transport): use OAuth or API key.",
            "Log every tool call / resource read for audit.",
            "Document resources + prompts in README so users discover them.",
            "Version the server (semver) — protocol additions could break clients.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["mcp==1.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["mcp", "claude-desktop"],
        "related_glossary_slugs": ["mcp", "resources"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Tools vs resources?", "answer": "Tools: model EXPLICITLY calls them. Resources: model can BROWSE them as passive context. Use tools for actions; resources for read-only data the model wants to consult."},
            {"question": "When use prompts?", "answer": "Reusable templates for common tasks. Users invoke them by name. Good for: 'review code', 'write PR description', 'triage ticket'. Avoid for one-off prompts."},
            {"question": "Resources size limit?", "answer": "Practical limit ~50KB per resource (Claude Desktop UX). Past that, the resource gets unwieldy. Break large data into multiple resources."},
            {"question": "Claude Desktop vs HTTP transport?", "answer": "Desktop: stdio, local trust, no auth. HTTP: networked, needs auth, multi-user. Pick based on deployment model."},
        ],
        "github_url": "https://github.com/modelcontextprotocol/python-sdk",
        "meta_title": "MCP Server With Resources + Prompts Starter",
        "meta_description": "Full MCP server: tools + resources (read-only data) + prompts (templates). Claude Desktop integration, security best practices.",
    },
    {
        "slug": "mcp-stdio-to-http-bridge",
        "title": "MCP stdio-to-HTTP Bridge",
        "tldr": "Wrap a stdio-based MCP server in an HTTP/SSE endpoint. Lets you deploy local stdio servers as networked services without rewriting them.",
        "category": "mcp-servers",
        "language": "python",
        "framework": "FastAPI + mcp",
        "tags": ["mcp", "bridge", "stdio", "http"],
        "best_for_tags": ["mcp-deployment", "self-hosted", "multi-tenant-mcp"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "You have a stdio MCP server (e.g., filesystem, git, db) and want to expose it as a networked service for multi-user / cloud use. The bridge spawns subprocesses per client connection.",
        "when_not_to_use": "Skip for simple local use (just use stdio directly). Skip if you can rewrite the server to native HTTP (better perf, easier ops).",
        "quick_start": "pip install mcp fastapi 'uvicorn[standard]' && python mcp_bridge.py",
        "full_code": '''"""MCP stdio→HTTP bridge.

Each client SSE connection spawns a stdio MCP server subprocess.
The bridge translates JSON-RPC over HTTP/SSE ↔ stdio.
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import StreamingResponse


# Configuration: which stdio command to bridge
STDIO_COMMAND = os.environ.get("MCP_STDIO_CMD", "npx -y @modelcontextprotocol/server-filesystem /tmp")


# Per-connection state: subprocess + queues
SESSIONS: dict[str, dict] = {}


# ----------------- SUBPROCESS MANAGEMENT -----------------

async def spawn_stdio_server() -> asyncio.subprocess.Process:
    cmd = STDIO_COMMAND.split()
    return await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@asynccontextmanager
async def session_lifespan(app: FastAPI):
    yield
    # On shutdown: clean up all sessions
    for sid, s in list(SESSIONS.items()):
        try:
            s["proc"].terminate()
            await s["proc"].wait()
        except Exception:
            pass
        SESSIONS.pop(sid, None)


app = FastAPI(lifespan=session_lifespan)


# ----------------- AUTH (minimal example) -----------------

def authenticate(authorization: str | None) -> str:
    """Map bearer token → tenant_id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.removeprefix("Bearer ")
    # Replace with real auth lookup
    if token == "demo-token":
        return "demo-tenant"
    raise HTTPException(403, "Invalid token")


# ----------------- SSE ENDPOINT (server → client events) -----------------

@app.get("/sse")
async def sse(authorization: str | None = Header(None)):
    tenant = authenticate(authorization)
    session_id = str(uuid.uuid4())

    proc = await spawn_stdio_server()
    SESSIONS[session_id] = {"proc": proc, "tenant": tenant}

    async def event_stream():
        # Send the endpoint URL the client should POST messages to
        yield f"event: endpoint\\ndata: /messages/{session_id}\\n\\n"

        # Pipe stdio.stdout to SSE
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                # MCP stdio is JSON-RPC, one msg per line
                yield f"event: message\\ndata: {line.decode().strip()}\\n\\n"
        finally:
            proc.terminate()
            SESSIONS.pop(session_id, None)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ----------------- POST ENDPOINT (client → server messages) -----------------

@app.post("/messages/{session_id}")
async def post_message(session_id: str, request: Request):
    if session_id not in SESSIONS:
        raise HTTPException(404, "Session not found")
    body = await request.body()
    proc = SESSIONS[session_id]["proc"]
    # Write line-delimited JSON-RPC to subprocess stdin
    proc.stdin.write(body + b"\\n")
    await proc.stdin.drain()
    return {"ok": True}


# ----------------- HEALTH -----------------

@app.get("/health")
async def health():
    return {"ok": True, "active_sessions": len(SESSIONS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
        "dependencies": [
            {"name": "mcp", "version": ">=1.0", "purpose": "MCP SDK (for types)"},
            {"name": "fastapi[standard]", "version": ">=0.115", "purpose": "HTTP + SSE server"},
            {"name": "uvicorn[standard]", "version": ">=0.30", "purpose": "ASGI server"},
        ],
        "env_vars": [
            {"name": "MCP_STDIO_CMD", "required": True, "description": "Command to spawn the stdio MCP server", "example": "npx -y @modelcontextprotocol/server-filesystem /tmp"},
        ],
        "setup_steps": [
            "pip install mcp 'fastapi[standard]' 'uvicorn[standard]'",
            "Set MCP_STDIO_CMD to your target stdio server command",
            "Run: uvicorn mcp_bridge:app --host 0.0.0.0 --port 8000",
            "Test: curl -H 'Authorization: Bearer demo-token' http://localhost:8000/sse",
        ],
        "variations": [
            {"label": "Process pooling", "description": "Reuse subprocesses across sessions (lower cold-start).", "code_snippet": "# Maintain a pool of pre-warm subprocesses; assign per session; recycle after N requests"},
            {"label": "Multi-server bridge", "description": "Route to different stdio servers by URL path.", "code_snippet": "# /sse/filesystem → filesystem server; /sse/git → git server. Per-path STDIO_COMMAND map."},
            {"label": "Bridge with sandboxing", "description": "Run stdio server in Docker.", "code_snippet": "# STDIO_COMMAND='docker run --rm -i mcp-fs-server'. Isolates per-tenant subprocess in container."},
        ],
        "common_errors": [
            {"error_text": "Subprocess hangs on stdin write", "cause": "Buffer not flushed; line not newline-terminated.", "fix_snippet": "Always append \\\\n to messages. Call await proc.stdin.drain() after write."},
            {"error_text": "Memory growth over time", "cause": "Subprocesses not cleaned up on disconnect.", "fix_snippet": "Ensure finally: proc.terminate() in event_stream. Add a periodic janitor task to kill orphan subprocesses."},
            {"error_text": "SSE disconnects randomly", "cause": "Proxy / browser timeout.", "fix_snippet": "Send heartbeat every 25s: yield ': keepalive\\\\n\\\\n'. Configure proxies (nginx) with proxy_buffering off + long timeouts."},
            {"error_text": "Tenant A's data leaking to Tenant B", "cause": "Subprocess shared across sessions.", "fix_snippet": "ONE subprocess per session. Don't pool across tenants. Even within tenant, isolate by user."},
        ],
        "production_checklist": [
            "Per-session subprocess isolation (no pooling across tenants).",
            "Real authentication (OAuth / JWT, not 'demo-token').",
            "SSE keepalive heartbeats.",
            "Subprocess resource limits (memory, CPU).",
            "Cleanup orphans (janitor task).",
            "Monitor: active sessions, subprocess CPU/memory, disconnect rate.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["fastapi==0.115", "uvicorn==0.30"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["mcp", "fastapi"],
        "related_glossary_slugs": ["mcp", "sse"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why bridge instead of rewriting to HTTP?", "answer": "Rewriting is cleaner long-term. Bridging is faster short-term — lets you deploy existing stdio servers without modification. Use bridge for prototyping; rewrite for production scale."},
            {"question": "Performance vs native HTTP?", "answer": "Bridge adds ~5-10ms latency per message. For tools (call rate <10/sec per session), negligible. For high-throughput, native HTTP wins."},
            {"question": "How does Claude Desktop use SSE?", "answer": "Desktop primarily uses stdio. SSE is for remote MCP — used by cloud-hosted MCP servers and the Anthropic MCP marketplace."},
            {"question": "Authentication patterns?", "answer": "Bearer token in Authorization header is simplest. Production: OAuth 2.0 client credentials, mutual TLS, or signed JWTs. Map tokens to tenant for multi-tenant isolation."},
        ],
        "github_url": "https://github.com/modelcontextprotocol/python-sdk",
        "meta_title": "MCP stdio-to-HTTP Bridge Starter",
        "meta_description": "Wrap stdio MCP servers in HTTP/SSE for networked deployment. Per-session subprocess isolation, auth, tenant separation.",
    },
    {
        "slug": "mcp-server-testing-with-inspector",
        "title": "MCP Server Testing With Inspector + Pytest",
        "tldr": "Two-layer MCP server testing: (1) MCP Inspector for interactive QA, (2) pytest with the MCP SDK client for automated regression tests. Catches protocol + logic bugs before deploy.",
        "category": "mcp-servers",
        "language": "python",
        "framework": "mcp Python SDK + pytest",
        "tags": ["mcp", "testing", "pytest", "inspector"],
        "best_for_tags": ["mcp-server-developers", "ci-quality", "regression-prevention"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Authoring an MCP server. Use Inspector during dev to test interactively; use pytest for CI to catch regressions. Both rely on the same MCP client protocol.",
        "when_not_to_use": "Skip for one-off MCP scripts (overhead). Skip for purely manual testing — Inspector alone is fine for hobby use.",
        "quick_start": "pip install mcp pytest pytest-asyncio && pytest test_mcp_server.py",
        "full_code": '''"""MCP server testing: pytest harness using the SDK client."""
from __future__ import annotations

import pytest
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVER_CMD = "python"
SERVER_ARGS = ["./full_mcp_server.py"]  # path to your MCP server


# ----------------- FIXTURE: CONNECTED CLIENT -----------------

@pytest.fixture
async def mcp_client():
    params = StdioServerParameters(command=SERVER_CMD, args=SERVER_ARGS)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


# ----------------- TESTS: DISCOVERY -----------------

@pytest.mark.asyncio
async def test_lists_expected_tools(mcp_client):
    tools = await mcp_client.list_tools()
    names = {t.name for t in tools.tools}
    assert "search_docs" in names
    assert "create_ticket" in names


@pytest.mark.asyncio
async def test_tool_schemas_valid(mcp_client):
    tools = await mcp_client.list_tools()
    for tool in tools.tools:
        assert tool.description, f"{tool.name} missing description"
        assert tool.inputSchema, f"{tool.name} missing inputSchema"
        # Pydantic / jsonschema check
        assert tool.inputSchema.get("type") == "object"


@pytest.mark.asyncio
async def test_lists_resources(mcp_client):
    resources = await mcp_client.list_resources()
    uris = {r.uri for r in resources.resources}
    assert any("docs://" in str(u) for u in uris)


# ----------------- TESTS: TOOL EXECUTION -----------------

@pytest.mark.asyncio
async def test_search_docs_returns_results(mcp_client):
    result = await mcp_client.call_tool("search_docs", {"query": "rate limit", "limit": 3})
    assert not result.isError
    # result.content is a list of content blocks
    text = "".join(c.text for c in result.content if c.type == "text")
    assert text  # non-empty


@pytest.mark.asyncio
async def test_invalid_args_handled(mcp_client):
    result = await mcp_client.call_tool("search_docs", {})  # missing query
    # Server should return isError or raise a clear validation error
    assert result.isError or "required" in str(result.content).lower()


@pytest.mark.asyncio
async def test_create_ticket_priority_enum(mcp_client):
    # Should accept valid priorities
    for p in ["low", "medium", "high"]:
        r = await mcp_client.call_tool("create_ticket", {"title": "test", "body": "...", "priority": p})
        assert not r.isError


# ----------------- TESTS: RESOURCES -----------------

@pytest.mark.asyncio
async def test_resource_read(mcp_client):
    content = await mcp_client.read_resource("docs://index")
    assert content.contents
    assert content.contents[0].text is not None


# ----------------- TESTS: PROMPTS -----------------

@pytest.mark.asyncio
async def test_prompt_with_args(mcp_client):
    prompts = await mcp_client.list_prompts()
    names = {p.name for p in prompts.prompts}
    if "write_pr_description" in names:
        result = await mcp_client.get_prompt("write_pr_description", {
            "diff_summary": "Added auth flow",
            "ticket_id": "T-123",
        })
        assert result.messages


# ----------------- INTERACTIVE: MCP INSPECTOR -----------------

INSPECTOR_INSTRUCTIONS = """
For interactive testing (during development):

1. Install: npm install -g @modelcontextprotocol/inspector
2. Run: npx @modelcontextprotocol/inspector python ./full_mcp_server.py
3. Browser opens at http://localhost:5173
4. Test tools, resources, prompts interactively
5. View JSON-RPC traffic in the inspector log
"""

if __name__ == "__main__":
    print(INSPECTOR_INSTRUCTIONS)
''',
        "dependencies": [
            {"name": "mcp", "version": ">=1.0", "purpose": "MCP SDK"},
            {"name": "pytest", "version": ">=7.0", "purpose": "Test runner"},
            {"name": "pytest-asyncio", "version": ">=0.23", "purpose": "Async test support"},
        ],
        "env_vars": [],
        "setup_steps": [
            "pip install mcp pytest pytest-asyncio",
            "npm install -g @modelcontextprotocol/inspector  # for interactive testing",
            "Set SERVER_ARGS path to your MCP server",
            "pytest test_mcp_server.py -v",
            "(Interactive) npx @modelcontextprotocol/inspector python ./your_server.py",
        ],
        "variations": [
            {"label": "Snapshot testing", "description": "Lock tool schemas.", "code_snippet": "# Use syrupy or jsondiff: snapshot the listTools() response; fail CI if schema changes unexpectedly"},
            {"label": "HTTP server tests", "description": "Test HTTP/SSE servers.", "code_snippet": "# Replace stdio_client with sse_client(URL). Same client interface; different transport."},
            {"label": "Property-based tests", "description": "Fuzz tool args with Hypothesis.", "code_snippet": "from hypothesis import given\\n@given(query=st.text())\\nasync def test_search_does_not_crash(mcp_client, query): ..."},
        ],
        "common_errors": [
            {"error_text": "RuntimeError: event loop closed", "cause": "Fixture cleanup runs after loop closes.", "fix_snippet": "Use pytest-asyncio's loop_scope='session' for shared loop. Or use module-scoped client fixture."},
            {"error_text": "Tests pass locally, fail in CI", "cause": "MCP server subprocess doesn't have deps in CI.", "fix_snippet": "Install server deps in CI workflow. Pin Python version. Use --tb=long for clearer error trace."},
            {"error_text": "Inspector doesn't connect", "cause": "Wrong command path.", "fix_snippet": "Use absolute path: npx @modelcontextprotocol/inspector $(pwd)/server.py. Or use venv-relative Python."},
            {"error_text": "Tool tests slow (subprocess startup)", "cause": "Fresh subprocess per test.", "fix_snippet": "Module-scope the fixture if tests don't mutate server state. Or use a long-lived test server."},
        ],
        "production_checklist": [
            "Snapshot tool / resource / prompt schemas — flag breaking changes.",
            "Test invalid-args / edge cases (empty strings, very long strings).",
            "Run inspector before manual deploy — catch obvious bugs.",
            "Run pytest in CI on every PR touching server code.",
            "Include adversarial inputs (path-traversal, SQL-like).",
            "Test both stdio + HTTP transports if you support both.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["mcp==1.0", "pytest-asyncio==0.23"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["mcp"],
        "related_glossary_slugs": ["mcp", "testing"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Inspector vs pytest?", "answer": "Inspector: interactive, exploratory, no setup. Pytest: automated, CI-friendly, regression prevention. Use both — Inspector for dev, pytest for protection."},
            {"question": "How to test against real LLMs?", "answer": "End-to-end test: spin up your server + connect a real LLM. Slow + flaky. Reserve for nightly. Use mocked tool outputs for fast unit tests."},
            {"question": "Snapshot testing — when?", "answer": "When tool schemas are part of your public API. A schema change can break clients. Snapshot the listTools/listResources/listPrompts responses; review diffs."},
            {"question": "Where's Inspector hosted?", "answer": "Locally — Inspector is a Node CLI that runs a local web UI + connects to your MCP server. No data leaves your machine."},
        ],
        "github_url": "https://github.com/modelcontextprotocol/inspector",
        "meta_title": "MCP Server Testing With Inspector + Pytest Starter",
        "meta_description": "Two-layer MCP server testing: Inspector for interactive QA, pytest with MCP SDK client for automated regression tests in CI.",
    },
]
