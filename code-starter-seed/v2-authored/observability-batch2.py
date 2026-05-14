"""Observability starters — batch 2: Arize Phoenix, simple metrics."""

RECORDS = [
    {
        "slug": "arize-phoenix-tracing",
        "title": "Arize Phoenix Local LLM Tracing",
        "tldr": "Trace LLM calls locally with Arize Phoenix — runs entirely on your machine, OTEL-based, free. Visualize spans, debug agents, and capture eval datasets without a SaaS dependency.",
        "category": "observability",
        "language": "python",
        "framework": "Arize Phoenix",
        "tags": ["phoenix", "arize", "tracing", "local"],
        "best_for_tags": ["local-dev", "debugging-agents", "self-hosted-obs"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When you want LLM tracing on your laptop for dev/debugging without sending data anywhere. Phoenix runs locally, has a great UI, captures everything via OpenTelemetry.",
        "when_not_to_use": "Skip for production multi-user tracing (use Langfuse / Arize Cloud / Datadog). Skip if you don't want a separate UI process.",
        "quick_start": "pip install arize-phoenix openinference-instrumentation-openai && python -c 'import phoenix as px; px.launch_app()' && python traced.py",
        "full_code": '''"""Arize Phoenix local tracing.

Launches a local UI (default http://localhost:6006) that shows every traced
LLM call, agent step, and chain run. Uses OpenTelemetry under the hood.
"""
from __future__ import annotations

import os

import phoenix as px
from openinference.instrumentation.openai import OpenAIInstrumentor
from openai import OpenAI


# 1. Launch Phoenix locally (one-time, in your dev script or notebook)
session = px.launch_app()
print(f"Phoenix UI: {session.url}")

# 2. Instrument OpenAI client (auto-traces all calls)
OpenAIInstrumentor().instrument()

client = OpenAI()


# 3. Use OpenAI as normal — all calls auto-traced

def summarize(text: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": "Summarize in 2 sentences."},
            {"role": "user", "content": text},
        ],
    )
    return resp.choices[0].message.content


def multi_step_agent(question: str) -> str:
    # Each LLM call appears as a span in Phoenix
    sub_questions = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Decompose: {question}"}],
    ).choices[0].message.content

    answers = []
    for sq in sub_questions.split("\\n"):
        if sq.strip():
            ans = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": sq}],
            ).choices[0].message.content
            answers.append(ans)

    final = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Original question: {question}\\n\\nSub-answers:\\n{chr(10).join(answers)}\\n\\nSynthesize."
        }],
    ).choices[0].message.content

    return final


if __name__ == "__main__":
    # Single call
    print(summarize("Reciprocal rank fusion combines retriever results via 1/(k+rank) summation."))

    # Multi-step
    print(multi_step_agent("What's the difference between RAG and fine-tuning?"))

    # Open the Phoenix UI to inspect traces
    print(f"\\nView traces at: {session.url}")
    input("Press Enter to close...")  # keep Phoenix running
''',
        "dependencies": [
            {"name": "arize-phoenix", "version": ">=4.36", "purpose": "Phoenix tracing UI + storage"},
            {"name": "openinference-instrumentation-openai", "version": ">=0.1", "purpose": "OpenAI auto-instrumentation"},
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install arize-phoenix openinference-instrumentation-openai openai",
            "export OPENAI_API_KEY=sk-...",
            "python traced.py — opens Phoenix UI at http://localhost:6006",
            "Browse spans, filter by token count, latency, errors.",
        ],
        "variations": [
            {"label": "Anthropic instrumentation", "description": "Same pattern for Claude.", "code_snippet": "from openinference.instrumentation.anthropic import AnthropicInstrumentor\\nAnthropicInstrumentor().instrument()"},
            {"label": "LangChain instrumentation", "description": "Auto-trace LangChain.", "code_snippet": "from openinference.instrumentation.langchain import LangChainInstrumentor\\nLangChainInstrumentor().instrument()"},
            {"label": "Export to Arize Cloud", "description": "Production tier.", "code_snippet": "# Set ARIZE_API_KEY env var; spans auto-flow to Arize Cloud for team-shared analytics."},
            {"label": "Capture eval dataset", "description": "Export traces as eval cases.", "code_snippet": "spans_df = px.Client().get_spans_dataframe()\\n# Filter for high-quality cases; export as JSONL for fine-tuning or eval baselines."},
        ],
        "common_errors": [
            {"error_text": "Phoenix UI shows no traces", "cause": "Instrumentor() not called before client.", "fix_snippet": "Call OpenAIInstrumentor().instrument() BEFORE creating the OpenAI() client."},
            {"error_text": "Port 6006 already in use", "cause": "Another process (TensorBoard, prior Phoenix).", "fix_snippet": "px.launch_app(port=6007). Or kill the conflicting process."},
            {"error_text": "Traces appear but spans are empty", "cause": "Streaming responses; spans need explicit handling.", "fix_snippet": "Phoenix supports streaming via OpenInference; ensure latest openinference-instrumentation version."},
            {"error_text": "Database lock errors in long sessions", "cause": "SQLite backend.", "fix_snippet": "For long sessions: PHOENIX_SQL_DATABASE_URL=postgresql://... to use Postgres backend."},
        ],
        "production_checklist": [
            "Phoenix local is for dev; use Phoenix Cloud or Langfuse for production.",
            "Mask PII before tracing if traces contain user data.",
            "Set sampling for high-volume — don't trace every prod request to local Phoenix.",
            "Persist datasets you'd want to keep; SQLite database is at ~/.phoenix/.",
            "Pin versions; instrumentation packages evolve.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["arize-phoenix==4.36.0", "openinference-instrumentation-openai==0.1.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["arize-phoenix"],
        "related_glossary_slugs": ["tracing", "opentelemetry", "observability"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Phoenix vs Langfuse?", "answer": "Phoenix: best for local dev + open evaluation tooling, simple to start. Langfuse: better for production team workflows, more polished. Both OTEL-based, similar concepts."},
            {"question": "Can Phoenix scale to production?", "answer": "Arize Cloud is the production version; Phoenix local is for dev. Self-host Phoenix is possible but Cloud is the supported production path."},
            {"question": "Where are traces stored locally?", "answer": "SQLite in ~/.phoenix/. For team-shared local: point PHOENIX_SQL_DATABASE_URL at a shared Postgres."},
            {"question": "Can I export traces to my eval workflow?", "answer": "Yes — phoenix.Client().get_spans_dataframe() returns pandas DF. Filter, label, export as eval dataset."},
        ],
        "github_url": "https://github.com/Arize-ai/phoenix",
        "meta_title": "Arize Phoenix Local LLM Tracing — Starter",
        "meta_description": "Local LLM tracing UI: launch Phoenix on your machine, auto-instrument OpenAI/Anthropic/LangChain, OTEL-based, free.",
    },
]
