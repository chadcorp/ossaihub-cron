"""Observability starters — Langfuse, OpenLLMetry, custom tracing."""

RECORDS = [
    {
        "slug": "langfuse-tracing-decorator",
        "title": "Langfuse Tracing With Decorator + Manual Spans",
        "tldr": "Wire Langfuse into any Python LLM app via the @observe decorator for top-level traces, plus manual spans for fine-grained sub-steps (retrieval, reranking, tool calls).",
        "category": "observability",
        "language": "python",
        "framework": "Langfuse",
        "tags": ["langfuse", "tracing", "observability", "llm-ops"],
        "best_for_tags": ["production-llm", "debugging", "cost-tracking"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When you've shipped LLM features to users and need to debug failures, track latency/cost, and analyze quality offline. Langfuse handles trace storage + UI; you instrument.",
        "when_not_to_use": "Skip for local dev (just log to stderr). Skip for purely batch pipelines where you don't need per-request introspection.",
        "quick_start": "pip install langfuse openai && LANGFUSE_PUBLIC_KEY=... LANGFUSE_SECRET_KEY=... python traced_app.py",
        "full_code": '''"""Langfuse-traced RAG pipeline.

Top-level @observe gives you one trace per user query.
Nested @observe (with default 'span' kind) shows up as child spans.
Manual `langfuse_context.update_current_observation` lets you attach
inputs/outputs, metadata, scores, and token usage.
"""
from __future__ import annotations

import os
from typing import Any

from langfuse.decorators import langfuse_context, observe
from langfuse.openai import openai   # patched OpenAI client — auto-logs LLM calls


@observe()  # default kind is "span"; use kind="generation" for LLM calls if not using patched client
def retrieve(query: str, k: int = 3) -> list[dict]:
    """Pretend retrieval — replace with your real vector DB call."""
    results = [
        {"id": "d1", "text": "Document about retrieval-augmented generation.", "score": 0.92},
        {"id": "d2", "text": "Document about chain-of-thought prompting.", "score": 0.78},
        {"id": "d3", "text": "Document about tool calling.", "score": 0.71},
    ][:k]
    # Attach observability metadata
    langfuse_context.update_current_observation(
        input={"query": query, "k": k},
        output={"hits": results},
        metadata={"retriever": "fake_top_k"},
    )
    return results


@observe()
def rerank(query: str, hits: list[dict]) -> list[dict]:
    """Pretend rerank by reversing — placeholder for cross-encoder."""
    reranked = list(reversed(hits))
    langfuse_context.update_current_observation(
        input={"query": query, "hits": hits},
        output={"reranked": reranked},
    )
    return reranked


@observe()
def build_prompt(query: str, hits: list[dict]) -> str:
    context = "\\n\\n".join(f"[{h['id']}] {h['text']}" for h in hits)
    return f"Context:\\n{context}\\n\\nQuestion: {query}\\nAnswer:"


@observe()
def call_llm(prompt: str) -> str:
    # The patched openai client auto-creates a GENERATION observation.
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


@observe()
def answer_with_rag(query: str) -> str:
    """Top-level function — becomes one trace in Langfuse."""
    hits = retrieve(query)
    reranked = rerank(query, hits)
    prompt = build_prompt(query, reranked)
    answer = call_llm(prompt)

    # Attach a quality score (could be from llm-judge, user thumb up, etc.)
    langfuse_context.update_current_observation(
        input={"query": query},
        output={"answer": answer},
    )
    langfuse_context.score_current_trace(
        name="self-faithfulness-stub",
        value=0.85,
        comment="Stub score — wire to your real evaluator.",
    )
    return answer


if __name__ == "__main__":
    print(answer_with_rag("What is RAG and when do I use it?"))
    # Flush before exit so traces ship.
    langfuse_context.flush()
''',
        "dependencies": [
            {"name": "langfuse", "version": ">=2.50", "purpose": "Tracing SDK and decorator"},
            {"name": "openai", "version": ">=1.40", "purpose": "LLM client (langfuse patches it)"},
        ],
        "env_vars": [
            {"name": "LANGFUSE_PUBLIC_KEY", "required": True, "description": "Public key from Langfuse project", "example": "pk-lf-..."},
            {"name": "LANGFUSE_SECRET_KEY", "required": True, "description": "Secret key from Langfuse project", "example": "sk-lf-..."},
            {"name": "LANGFUSE_HOST", "required": False, "description": "Self-hosted URL (default https://cloud.langfuse.com)", "example": "https://langfuse.mycompany.com"},
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI API key", "example": "sk-..."},
        ],
        "setup_steps": [
            "Sign up at langfuse.com (or self-host).",
            "Create a project, copy the public + secret keys.",
            "pip install langfuse openai",
            "export LANGFUSE_PUBLIC_KEY=... LANGFUSE_SECRET_KEY=... OPENAI_API_KEY=...",
            "python traced_app.py",
            "View traces in the Langfuse UI.",
        ],
        "variations": [
            {
                "label": "Anthropic instead of OpenAI",
                "description": "Langfuse has a similar wrapper for Anthropic.",
                "code_snippet": "from langfuse.anthropic import anthropic\\nclient = anthropic.Anthropic()  # auto-logs calls",
            },
            {
                "label": "Manual span without decorator",
                "description": "When you can't add a decorator (third-party code).",
                "code_snippet": "from langfuse import Langfuse\\nlf = Langfuse()\\ntrace = lf.trace(name='rag-pipeline')\\nspan = trace.span(name='retrieve', input={...})\\n# ... do work ...\\nspan.end(output={...})",
            },
            {
                "label": "Attach user/session IDs",
                "description": "For multi-user systems.",
                "code_snippet": "langfuse_context.update_current_trace(user_id=user_id, session_id=session_id, tags=['production'])",
            },
            {
                "label": "Custom scores from offline eval",
                "description": "Backfill quality scores after the fact.",
                "code_snippet": "from langfuse import Langfuse\\nlf = Langfuse()\\nlf.score(trace_id='...', name='faithfulness', value=0.9)",
            },
        ],
        "common_errors": [
            {
                "error_text": "Traces missing in UI",
                "cause": "Process exited before background queue flushed.",
                "fix_snippet": "Call langfuse_context.flush() before exit. For long-running services this auto-flushes; CLI scripts must flush explicitly.",
            },
            {
                "error_text": "401 Unauthorized when sending traces",
                "cause": "Wrong key pair or wrong host.",
                "fix_snippet": "Public + secret keys must match the same project. If self-hosting, set LANGFUSE_HOST.",
            },
            {
                "error_text": "Some LLM calls don't appear as generations",
                "cause": "Not using the patched langfuse.openai client.",
                "fix_snippet": "Import: `from langfuse.openai import openai`. Or wrap with manual generation: trace.generation(name=..., model=..., input=..., output=..., usage=...).",
            },
            {
                "error_text": "PII appears in traces",
                "cause": "Default behavior logs all inputs/outputs.",
                "fix_snippet": "Mask PII before passing to traced functions, OR use langfuse_context.update_current_observation(input='[REDACTED]') for sensitive spans.",
            },
        ],
        "production_checklist": [
            "Set up separate Langfuse projects for dev/staging/prod.",
            "Tag traces with environment, version, feature_flag for filtering.",
            "Sample in high-traffic environments (1% of traces) if cost is a concern.",
            "Mask PII before tracing — Langfuse stores raw inputs/outputs.",
            "Use Langfuse's auto-cost calculation by enabling model pricing in project settings.",
            "Set up trace-based eval datasets to track quality over time.",
            "Configure async flushing; never let trace shipping block user-facing latency.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["langfuse==2.55.0", "openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["langfuse"],
        "related_glossary_slugs": ["llm-observability", "tracing", "span"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Langfuse vs OpenLLMetry?",
                "answer": "Langfuse: opinionated for LLM apps, rich UI, eval/dataset integration. OpenLLMetry: OpenTelemetry-based, integrates with existing observability stacks (Datadog, Honeycomb). Different fits.",
            },
            {
                "question": "Does Langfuse track cost?",
                "answer": "Yes — configure model pricing in the project settings; Langfuse computes USD per trace from token counts. Useful for cost-per-user analysis.",
            },
            {
                "question": "Can I self-host?",
                "answer": "Yes — Langfuse is open source. Run via Docker Compose for trial, or use their Kubernetes setup for production.",
            },
            {
                "question": "How does it integrate with frameworks (LangChain, LlamaIndex)?",
                "answer": "Direct integrations exist. For LangChain: `from langfuse.callback import CallbackHandler` → add to LLM. For LlamaIndex: similar callback.",
            },
        ],
        "github_url": "https://github.com/langfuse/langfuse",
        "meta_title": "Langfuse Tracing With Decorator — Starter",
        "meta_description": "Wire Langfuse into a Python LLM app: @observe decorators, patched OpenAI client, manual spans, quality scores, and PII masking.",
    },
    {
        "slug": "openllmetry-traces-to-otel-backend",
        "title": "OpenLLMetry — LLM Traces to Any OpenTelemetry Backend",
        "tldr": "Auto-instrument LLM calls with OpenLLMetry; ship traces to Datadog, Honeycomb, Jaeger, or any OTEL backend. Zero code change to your LLM calls — just initialize once.",
        "category": "observability",
        "language": "python",
        "framework": "OpenLLMetry",
        "tags": ["openllmetry", "opentelemetry", "tracing", "ddtrace"],
        "best_for_tags": ["enterprise-observability", "otel-stack", "datadog"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When your org already has OpenTelemetry infrastructure (Datadog, Honeycomb, etc.) and you want LLM traces to flow into the same pipeline as everything else.",
        "when_not_to_use": "Skip if you want LLM-specific UI features (eval datasets, prompt management) — Langfuse or Arize is a better fit. Skip for tiny apps; OTEL setup overhead isn't worth it.",
        "quick_start": "pip install traceloop-sdk openai && TRACELOOP_API_KEY=... python app.py",
        "full_code": '''"""OpenLLMetry: zero-code-change LLM observability via OpenTelemetry.

Initialize Traceloop once at app startup; OpenAI/Anthropic/Cohere/Bedrock
calls auto-emit OTEL spans with full token-level detail.

Export to:
  - Traceloop Cloud (managed)
  - Any OTEL Collector (Datadog, Honeycomb, Jaeger, ...)
"""
from __future__ import annotations

import os

from openai import OpenAI
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import task, workflow


# 1. INITIALIZE (once, at app startup)
# Option A: Traceloop Cloud
Traceloop.init(
    app_name="ossaihub-rag-service",
    api_key=os.environ.get("TRACELOOP_API_KEY"),  # for managed cloud
    disable_batch=False,  # batch to reduce overhead in prod
)

# Option B: Direct to any OTEL backend (Datadog, Honeycomb, etc.)
# from opentelemetry.sdk.trace.export import BatchSpanProcessor
# from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
# Traceloop.init(
#     app_name="ossaihub-rag-service",
#     exporter=OTLPSpanExporter(endpoint="http://collector:4317", insecure=True),
# )

client = OpenAI()


# 2. WRAP TOP-LEVEL FUNCTIONS WITH @workflow

@workflow(name="answer_question")
def answer(query: str) -> str:
    """Top-level entry point — becomes a single workflow span."""
    hits = retrieve(query)
    return generate(query, hits)


@task(name="retrieve")
def retrieve(query: str) -> list[str]:
    """Sub-step — child span of the workflow."""
    # Replace with real vector DB
    return [
        "RAG retrieves relevant context to ground LLM answers.",
        "Faithfulness measures whether the answer is supported by context.",
    ]


@task(name="generate")
def generate(query: str, hits: list[str]) -> str:
    """Auto-instrumented — OpenAI call appears as a child generation span."""
    context = "\\n".join(hits)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": "Answer based only on the provided context."},
            {"role": "user", "content": f"Context:\\n{context}\\n\\nQuestion: {query}"},
        ],
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    print(answer("What does RAG do?"))
    # Spans auto-flush on process exit when not disabled
''',
        "dependencies": [
            {"name": "traceloop-sdk", "version": ">=0.30", "purpose": "OpenLLMetry SDK (auto-instrumentation)"},
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI client (auto-instrumented)"},
        ],
        "env_vars": [
            {"name": "TRACELOOP_API_KEY", "required": False, "description": "Traceloop Cloud API key (only if using managed)", "example": "tl-..."},
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
            {"name": "OTEL_EXPORTER_OTLP_ENDPOINT", "required": False, "description": "Direct OTEL endpoint if not using Traceloop Cloud", "example": "http://otel-collector:4317"},
        ],
        "setup_steps": [
            "pip install traceloop-sdk openai",
            "Choose backend: Traceloop Cloud or self-hosted OTEL collector.",
            "Set env vars accordingly.",
            "Initialize Traceloop.init() at app startup.",
            "Run your app — traces appear in your backend.",
        ],
        "variations": [
            {
                "label": "Datadog exporter",
                "description": "Send to Datadog directly.",
                "code_snippet": "Traceloop.init(app_name='...', exporter=OTLPSpanExporter(endpoint='https://trace.agent.datadoghq.com'), headers={'dd-api-key': os.environ['DD_API_KEY']})",
            },
            {
                "label": "Honeycomb",
                "description": "Send to Honeycomb.",
                "code_snippet": "Traceloop.init(app_name='...', exporter=OTLPSpanExporter(endpoint='https://api.honeycomb.io/v1/traces', headers={'x-honeycomb-team': os.environ['HONEYCOMB_KEY']}))",
            },
            {
                "label": "Local Jaeger",
                "description": "Self-host Jaeger for local dev.",
                "code_snippet": "# docker run -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one\\nTraceloop.init(app_name='...', api_endpoint='http://localhost:4317')",
            },
            {
                "label": "Disable batching in development",
                "description": "See traces immediately.",
                "code_snippet": "Traceloop.init(app_name='...', disable_batch=True)",
            },
        ],
        "common_errors": [
            {
                "error_text": "No spans appearing in backend",
                "cause": "Process exits before batch flush, or wrong endpoint.",
                "fix_snippet": "Set disable_batch=True for short scripts. For long-running, ensure graceful shutdown so OTEL flushes.",
            },
            {
                "error_text": "Workflow has no child spans for LLM call",
                "cause": "OpenAI client created before Traceloop.init().",
                "fix_snippet": "Always call Traceloop.init() FIRST. Then import/instantiate the OpenAI client.",
            },
            {
                "error_text": "Token usage missing from spans",
                "cause": "Streaming mode without proper aggregation.",
                "fix_snippet": "OpenLLMetry handles streaming; ensure traceloop-sdk >= 0.30. For older versions, switch to non-streaming or upgrade.",
            },
            {
                "error_text": "OTLPError: failed to export spans",
                "cause": "Collector not reachable or wrong auth headers.",
                "fix_snippet": "Test endpoint with curl; confirm headers match backend expectations.",
            },
        ],
        "production_checklist": [
            "Set OTEL_TRACES_SAMPLER and rates in high-traffic systems to control cost.",
            "Use resource attributes (env, version, service.name) for filtering in backend.",
            "Mask sensitive prompt content via Traceloop's content masking config.",
            "Test trace flow end-to-end before depending on it for prod debugging.",
            "Pin traceloop-sdk version; OTEL semantics evolve.",
            "If using Datadog/Honeycomb, set up retention and cost alerts — LLM spans are voluminous.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["traceloop-sdk==0.30.1", "openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["openllmetry", "datadog"],
        "related_glossary_slugs": ["opentelemetry", "tracing", "observability"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Do I need Traceloop Cloud?",
                "answer": "No — OpenLLMetry is open source. Traceloop Cloud is a managed option; you can ship straight to any OTEL backend you already run.",
            },
            {
                "question": "What's instrumented automatically?",
                "answer": "OpenAI, Anthropic, Cohere, Bedrock, Replicate, Together, Vertex, Mistral, and major frameworks (LangChain, LlamaIndex, Haystack). Token counts, model name, and full request/response captured.",
            },
            {
                "question": "How does it compare to Langfuse?",
                "answer": "OpenLLMetry: fits existing OTEL pipelines, language-agnostic. Langfuse: LLM-specific UI, eval/dataset features. Pick based on whether you want a unified observability stack or LLM-specific tooling.",
            },
            {
                "question": "Is it production-grade?",
                "answer": "Yes — used at scale at multiple companies. Be careful with sampling and PII; defaults are verbose.",
            },
        ],
        "github_url": "https://github.com/traceloop/openllmetry",
        "meta_title": "OpenLLMetry to OpenTelemetry Backend — Starter",
        "meta_description": "Auto-instrument LLM calls with OpenLLMetry; ship traces to Datadog, Honeycomb, Jaeger, or any OTEL backend with zero code change.",
    },
    {
        "slug": "stderr-jsonl-trace-poor-mans-observability",
        "title": "Stderr JSON-Lines Tracing (Poor Man's Observability)",
        "tldr": "Zero-dependency LLM tracing: emit one JSON object per event to stderr, pipe to your existing log pipeline (Vector, Fluentbit, CloudWatch). Costs nothing, integrates everywhere.",
        "category": "observability",
        "language": "python",
        "framework": "stdlib",
        "tags": ["jsonl", "tracing", "minimal-deps", "logging"],
        "best_for_tags": ["minimal-overhead", "existing-log-pipeline", "small-team"],
        "difficulty_tier": "beginner",
        "featured": False,
        "when_to_use": "When you have an existing log pipeline (CloudWatch, Loki, Datadog logs) and don't want a separate observability tool. JSON-lines is the lingua franca; everything reads it.",
        "when_not_to_use": "Skip when you need an interactive trace UI (use Langfuse). Skip if you don't have a log pipeline already — you're recreating it.",
        "quick_start": "python traced_app.py 2> traces.jsonl",
        "full_code": '''"""Zero-dep LLM tracing: structured JSON-lines on stderr.

Each event = one JSON object on stderr. Pipe to your log pipeline.

events:
  - llm.call.start: input, model, params
  - llm.call.end: output, tokens, duration_ms, cost_est
  - tool.call.start / .end
  - error: any failure with context
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

client = OpenAI()


# ----------------- TRACER -----------------

@dataclass
class Tracer:
    """Threadlocal-friendly tracer; flushes to stderr on each event."""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span: str | None = None

    def emit(self, **kw) -> None:
        record = {
            "ts": time.time(),
            "trace_id": self.trace_id,
            "parent_span": self.parent_span,
            **kw,
        }
        sys.stderr.write(json.dumps(record, default=str) + "\\n")
        sys.stderr.flush()

    @contextmanager
    def span(self, name: str, **attrs):
        span_id = str(uuid.uuid4())[:8]
        prev = self.parent_span
        self.parent_span = span_id
        t0 = time.time()
        self.emit(event="span.start", span=span_id, name=name, **attrs)
        try:
            yield span_id
            self.emit(event="span.end", span=span_id, name=name,
                      duration_ms=int((time.time() - t0) * 1000))
        except Exception as e:
            self.emit(event="span.error", span=span_id, name=name,
                      error=str(e), duration_ms=int((time.time() - t0) * 1000))
            raise
        finally:
            self.parent_span = prev


# ----------------- COST TABLE (per 1M tokens) -----------------

COST_PER_M = {
    "gpt-4o": {"in": 2.50, "out": 10.00},
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
    "gpt-4-turbo": {"in": 10.00, "out": 30.00},
}


def _cost_est(model: str, usage: Any) -> float:
    base = next((v for k, v in COST_PER_M.items() if model.startswith(k)), None)
    if not base or not usage:
        return 0.0
    return base["in"] * usage.prompt_tokens / 1_000_000 + base["out"] * usage.completion_tokens / 1_000_000


# ----------------- TRACED LLM WRAPPER -----------------

def traced_chat(tracer: Tracer, model: str, messages: list[dict], **params) -> str:
    with tracer.span("llm.call", model=model, prompt_tokens_estimate=sum(len(m["content"]) // 4 for m in messages)):
        t0 = time.time()
        try:
            resp = client.chat.completions.create(model=model, messages=messages, **params)
        except Exception as e:
            tracer.emit(event="llm.call.failure", model=model, error=str(e))
            raise
        text = resp.choices[0].message.content
        cost = _cost_est(model, resp.usage)
        tracer.emit(
            event="llm.call.metrics",
            model=model,
            prompt_tokens=resp.usage.prompt_tokens,
            completion_tokens=resp.usage.completion_tokens,
            total_tokens=resp.usage.total_tokens,
            cost_usd_est=round(cost, 6),
            duration_ms=int((time.time() - t0) * 1000),
        )
        return text


# ----------------- APP -----------------

def rag_answer(query: str, tracer: Tracer | None = None) -> str:
    tracer = tracer or Tracer()
    with tracer.span("rag.answer", query=query):
        with tracer.span("rag.retrieve"):
            hits = ["RAG retrieves grounding context.", "Faithfulness checks support."]
            tracer.emit(event="retrieve.metrics", n_hits=len(hits))

        with tracer.span("rag.generate"):
            context = "\\n".join(hits)
            answer = traced_chat(
                tracer, "gpt-4o-mini",
                [
                    {"role": "system", "content": "Answer using only the context."},
                    {"role": "user", "content": f"Context:\\n{context}\\n\\nQ: {query}"},
                ],
                temperature=0,
            )
            return answer


if __name__ == "__main__":
    print(rag_answer("What does RAG do?"))
    print(f"\\n(Traces written to stderr. Try: python {sys.argv[0]} 2> traces.jsonl)", file=sys.stderr)
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai",
            "export OPENAI_API_KEY=sk-...",
            "python traced_app.py 2> traces.jsonl",
            "cat traces.jsonl | jq '.event' | sort | uniq -c   # quick summary",
            "Pipe traces to your existing logging (Vector, Fluentbit, etc.).",
        ],
        "variations": [
            {
                "label": "AsyncIO version",
                "description": "Same pattern for async OpenAI client.",
                "code_snippet": "@contextmanager → @asynccontextmanager; AsyncOpenAI client",
            },
            {
                "label": "Datadog logs",
                "description": "DD reads JSON logs natively.",
                "code_snippet": "# Configure DD agent log collection on stderr; spans auto-correlate via trace_id field if you add 'dd.trace_id'.",
            },
            {
                "label": "Add quality score",
                "description": "Attach an offline score to a trace.",
                "code_snippet": "tracer.emit(event='quality.score', metric='faithfulness', value=0.92, judge='gpt-4o')",
            },
            {
                "label": "Sample at 10%",
                "description": "Reduce volume in production.",
                "code_snippet": "import random\\nif random.random() < 0.1: tracer.emit(...)  # 10% sample",
            },
        ],
        "common_errors": [
            {
                "error_text": "Traces interleave from multiple requests",
                "cause": "Single global tracer in concurrent code.",
                "fix_snippet": "Create a Tracer per request. Pass tracer through the call chain (or use contextvars for implicit threading).",
            },
            {
                "error_text": "Stderr is buffered; events appear late",
                "cause": "Python buffers stderr in some configs.",
                "fix_snippet": "Starter calls sys.stderr.flush() per event. If you still see buffering, run with python -u (unbuffered) or set PYTHONUNBUFFERED=1.",
            },
            {
                "error_text": "Cost estimate is wrong",
                "cause": "COST_PER_M table stale.",
                "fix_snippet": "Update from OpenAI's pricing page; consider auto-fetching, or use a library like litellm.completion_cost.",
            },
            {
                "error_text": "Trace files too large to grep",
                "cause": "Verbose tracing in production without rotation.",
                "fix_snippet": "Rotate via logrotate or shipping to a log backend. Don't keep weeks of traces on local disk.",
            },
        ],
        "production_checklist": [
            "Ship traces to a structured log pipeline (CloudWatch, Loki, Datadog).",
            "Sample at high QPS to control cost (1-10%).",
            "Include version/env tags so you can filter regressions.",
            "Don't include PII in event fields without scrubbing.",
            "Set a max field length to avoid 100KB-long content blobs.",
            "Watch for cost drift via dashboards on cost_usd_est aggregation.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["structured-logging", "tracing"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Is this enough for production?",
                "answer": "For most teams, yes — at small scale. You miss UI features (eval datasets, trace browsing), but you get the data flowing into your existing pipeline. Graduate to Langfuse/Arize when UI value justifies the dependency.",
            },
            {
                "question": "How do I correlate with HTTP traces?",
                "answer": "Include the request's trace_id (from your framework's middleware) in the Tracer constructor. Then your LLM events join with HTTP events on trace_id in your log backend.",
            },
            {
                "question": "Why JSON-lines instead of OTEL?",
                "answer": "Zero dependency, runs anywhere. OTEL is more powerful but adds a dependency and learning curve. Use JSONL when you want simplicity; OTEL when you need the ecosystem.",
            },
            {
                "question": "Can I add custom events?",
                "answer": "Yes — call tracer.emit(event='my.custom.event', **whatever_fields). The shape is free-form; you decide your schema.",
            },
        ],
        "github_url": "",
        "meta_title": "Stderr JSON-Lines LLM Tracing — Starter",
        "meta_description": "Zero-dependency LLM observability: JSON events to stderr, pipe to any log pipeline. Spans, costs, errors — no SaaS required.",
    },
]
