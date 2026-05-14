"""MCP server starters — batch 2: database + search."""

RECORDS = [
    {
        "slug": "mcp-database-readonly",
        "title": "Read-Only Database MCP Server",
        "tldr": "MCP server exposing SQL-against-your-database as a tool — but SELECT-only, with row-limit caps, schema introspection, and query timeout. Lets Claude Desktop query your data safely.",
        "category": "mcp-servers",
        "language": "python",
        "framework": "FastMCP",
        "tags": ["mcp", "database", "sql", "read-only"],
        "best_for_tags": ["data-exploration", "claude-desktop-data", "safe-query"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When you want Claude (Desktop, Cursor) to be able to query your database without trusting it to mutate. Read-only contracts + introspection tools + timeouts make it safe.",
        "when_not_to_use": "Skip for production write operations (let humans do it). Skip for high-PII data without auth (this is a per-developer tool, not multi-tenant).",
        "quick_start": "pip install fastmcp psycopg && DATABASE_URL=... python db_mcp.py",
        "full_code": '''"""Read-only Postgres MCP server."""
from __future__ import annotations

import os
import re

import psycopg
from fastmcp import FastMCP

DB_URL = os.environ["DATABASE_URL"]
MAX_ROWS = 100
QUERY_TIMEOUT_S = 10

mcp = FastMCP("readonly-postgres")


# Block dangerous statements; only SELECT and WITH
ALLOWED_PREFIXES = ("SELECT", "WITH", "EXPLAIN")
DANGEROUS_PATTERNS = re.compile(
    r"\\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|COPY|VACUUM)\\b",
    re.IGNORECASE,
)


def _validate(sql: str) -> tuple[bool, str]:
    sql_clean = sql.strip()
    if not sql_clean:
        return False, "empty query"
    first_word = sql_clean.split()[0].upper()
    if first_word not in ALLOWED_PREFIXES:
        return False, f"only {ALLOWED_PREFIXES} allowed; got {first_word}"
    if DANGEROUS_PATTERNS.search(sql_clean):
        return False, "query contains forbidden statement type"
    if "--" in sql_clean or ";" in sql_clean.rstrip(";"):
        # naive guard against statement-stacking; allow single trailing ;
        if ";" in sql_clean[:-1] if sql_clean.endswith(";") else ";" in sql_clean:
            return False, "multiple statements not allowed"
    return True, "ok"


@mcp.tool()
def list_tables() -> list[dict]:
    """List all user tables in the database.

    Returns: list of {schema, table, comment} dicts.
    """
    sql = """
    SELECT table_schema, table_name, obj_description((table_schema||'.'||table_name)::regclass) as comment
    FROM information_schema.tables
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_name
    """
    with psycopg.connect(DB_URL, connect_timeout=5) as conn:
        rows = conn.execute(sql).fetchall()
    return [{"schema": r[0], "table": r[1], "comment": r[2]} for r in rows]


@mcp.tool()
def describe_table(table_name: str) -> dict:
    """Return columns + types for a table.

    Args:
        table_name: Format 'schema.table' or just 'table' (defaults to public).
    """
    if "." in table_name:
        schema, table = table_name.split(".", 1)
    else:
        schema, table = "public", table_name

    sql = """
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = %s AND table_name = %s
    ORDER BY ordinal_position
    """
    with psycopg.connect(DB_URL, connect_timeout=5) as conn:
        rows = conn.execute(sql, (schema, table)).fetchall()
    return {
        "schema": schema,
        "table": table,
        "columns": [
            {"name": r[0], "type": r[1], "nullable": r[2] == "YES", "default": r[3]}
            for r in rows
        ],
    }


@mcp.tool()
def query(sql: str, *, max_rows: int = 50) -> dict:
    """Execute a SELECT query. Read-only; capped to {max_rows}.

    Args:
        sql: SQL SELECT statement. INSERT/UPDATE/DELETE etc. are rejected.
        max_rows: Max rows to return (capped at 100).
    """
    ok, reason = _validate(sql)
    if not ok:
        return {"error": reason}

    max_rows = min(max_rows, MAX_ROWS)

    try:
        with psycopg.connect(DB_URL, connect_timeout=5) as conn:
            conn.execute(f"SET statement_timeout = {QUERY_TIMEOUT_S * 1000}")
            cur = conn.execute(sql)
            rows = cur.fetchmany(max_rows)
            columns = [desc.name for desc in cur.description] if cur.description else []
            truncated = cur.fetchone() is not None
        return {
            "columns": columns,
            "rows": [list(r) for r in rows],
            "row_count": len(rows),
            "truncated": truncated,
        }
    except psycopg.errors.QueryCanceled:
        return {"error": f"query exceeded {QUERY_TIMEOUT_S}s timeout"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


if __name__ == "__main__":
    mcp.run()
''',
        "dependencies": [
            {"name": "fastmcp", "version": ">=2.0", "purpose": "MCP server"},
            {"name": "psycopg[binary]", "version": ">=3.2", "purpose": "Postgres client"},
        ],
        "env_vars": [
            {"name": "DATABASE_URL", "required": True, "description": "Postgres URL (use READ-ONLY role!)", "example": "postgresql://readonly_user:pw@host:5432/db"},
        ],
        "setup_steps": [
            "Create a READ-ONLY Postgres role: CREATE ROLE mcp_reader LOGIN PASSWORD '...' NOSUPERUSER; GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_reader;",
            "pip install fastmcp psycopg[binary]",
            "export DATABASE_URL=postgresql://mcp_reader:...@host/db",
            "python db_mcp.py",
            "Configure Claude Desktop to launch this script.",
        ],
        "variations": [
            {"label": "MySQL variant", "description": "Same pattern, MySQL.", "code_snippet": "import pymysql\\n# Adjust list_tables / describe_table SQL to MySQL information_schema variants"},
            {"label": "Multi-DB", "description": "Multiple connections selectable per query.", "code_snippet": "@mcp.tool()\\ndef query(sql: str, db: str): conn = DB_MAP[db]; ..."},
            {"label": "Query plan", "description": "Expose EXPLAIN as a separate tool.", "code_snippet": "@mcp.tool()\\ndef explain(sql: str): return query(f'EXPLAIN ANALYZE {sql}')"},
        ],
        "common_errors": [
            {"error_text": "Permission denied for table X", "cause": "Read-only role doesn't have SELECT on all tables.", "fix_snippet": "GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_reader; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mcp_reader;"},
            {"error_text": "Query takes too long", "cause": "Big table without LIMIT.", "fix_snippet": "Starter has statement_timeout. Encourage the LLM (system prompt) to always add LIMIT."},
            {"error_text": "SQL injection?", "cause": "Tool takes raw SQL.", "fix_snippet": "Read-only role + validate() + statement_timeout = defense in depth. NEVER expose this with a write-capable role."},
            {"error_text": "Connection pool exhausted", "cause": "Each tool call opens new conn.", "fix_snippet": "Use psycopg_pool.ConnectionPool for shared pooling. Especially if running as HTTP MCP."},
        ],
        "production_checklist": [
            "ALWAYS use a read-only Postgres role; never expose a superuser.",
            "Set query timeout (starter does 10s).",
            "Cap max_rows (starter at 100).",
            "If multi-tenant, enforce tenant filter at role level (RLS).",
            "Log every query for audit; this is YOUR DATA being queried.",
            "Don't expose this MCP server publicly; per-developer or trusted network only.",
            "Pin DATABASE_URL via env, not config file; rotate periodically.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-7-sonnet (via Claude Desktop)"],
            "library_versions": ["fastmcp==2.2.0", "psycopg==3.2.3"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["fastmcp", "postgres"],
        "related_glossary_slugs": ["mcp", "read-only-role", "sql-safety"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why read-only at the role level too?", "answer": "Defense in depth. SQL validation can be bypassed (encoding tricks, statement stacking). A read-only role makes it impossible for the database to execute mutations even if SQL parsing fails."},
            {"question": "Can I add custom tools?", "answer": "Yes — @mcp.tool() any function. Useful: get_recent_activity, search_users, etc. — specific tools the model uses instead of writing raw SQL."},
            {"question": "What about complex queries?", "answer": "The LLM writes them via the query() tool. Complex JOINs work; let the LLM use describe_table first to learn schema."},
            {"question": "Is this safe for production data?", "answer": "Per-developer, read-only role, with audit logs: yes. Multi-tenant or untrusted users: build a more constrained interface (specific tools, not raw SQL)."},
        ],
        "github_url": "https://github.com/jlowin/fastmcp",
        "meta_title": "Read-Only Database MCP Server — Starter",
        "meta_description": "MCP server exposing SQL to Claude/Cursor — read-only validation + statement timeout + row caps + schema introspection.",
    },
]
