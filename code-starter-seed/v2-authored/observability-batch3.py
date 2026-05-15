"""Observability starters — batch 3: Helicone, Traceloop, custom OTel, cost tracking."""

RECORDS = [
    {
        "slug": "helicone-proxy-llm-observability",
        "title": "Helicone Proxy LLM Observability (Drop-In)",
        "tldr": "Helicone: change one URL in your OpenAI client and get logging, caching, retries, cost tracking, rate-limiting for free. Drop-in observability with no code change.",
        "category": "observability",
        "language": "python",
        "framework": "Helicone",
        "tags": ["helicone", "proxy", "observability", "cost-tracking"],
        "best_for_tags": ["minimal-code-change", "managed-observability", "production"],
        "difficulty_tier": "beginner",
        "featured": True,
        "when_to_use": "Want LLM observability NOW without instrumenting code. Change OpenAI/Anthropic base URL to Helicone's proxy → automatic traces + costs + caching.",
        "when_not_to_use": "Skip if you want self-hosted observability (use Langfuse OSS instead). Skip for SaaS-averse environments — your prompts go through Helicone.",
        "quick_start": "Sign up at helicone.ai → change OpenAI base_url to Helicone proxy",
        "full_code": '''"""Helicone proxy: drop-in observability for OpenAI / Anthropic / generic."""
from __future__ import annotations

import os
from openai import OpenAI


# ----------------- WAY 1: OPENAI VIA HELICONE PROXY -----------------

client = OpenAI(
    base_url="https://oai.helicone.ai/v1",  # Helicone proxy URL
    api_key=os.environ["OPENAI_API_KEY"],
    default_headers={
        "Helicone-Auth": f"Bearer {os.environ['HELICONE_API_KEY']}",

        # Metadata for filtering / grouping in dashboard
        "Helicone-User-Id": "user_123",
        "Helicone-Session-Id": "session_abc",
        "Helicone-Property-Feature": "checkout",
        "Helicone-Property-Tenant": "acme-corp",

        # Enable caching (free tier 1k cache hits/mo)
        "Helicone-Cache-Enabled": "true",
        "Helicone-Cache-Bucket-Max-Size": "5",
        "Helicone-Cache-Seed": "v1",  # bump to invalidate

        # Per-user rate limit (set in Helicone dashboard)
        "Helicone-RateLimit-Policy": "10;w=60;u=cents;s=user",  # 10 cents/min per user

        # Retry policy
        "Helicone-Retry-Enabled": "true",
        "Helicone-Retry-Num": "3",
        "Helicone-Retry-Factor": "2",
    },
)


def chat(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


# ----------------- WAY 2: ANTHROPIC VIA HELICONE -----------------

from anthropic import Anthropic

anthropic_client = Anthropic(
    base_url="https://anthropic.helicone.ai",
    api_key=os.environ["ANTHROPIC_API_KEY"],
    default_headers={
        "Helicone-Auth": f"Bearer {os.environ['HELICONE_API_KEY']}",
    },
)


def chat_anthropic(prompt: str) -> str:
    response = anthropic_client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ----------------- WAY 3: GENERIC HTTP (any LLM) -----------------

import httpx


async def custom_llm(prompt: str) -> str:
    """Wrap any LLM API by proxying through Helicone."""
    async with httpx.AsyncClient() as http:
        r = await http.post(
            "https://gateway.helicone.ai/v1/chat/completions",
            headers={
                "Helicone-Auth": f"Bearer {os.environ['HELICONE_API_KEY']}",
                "Helicone-Target-URL": "https://api.your-llm.com/v1/chat/completions",
                "Authorization": f"Bearer {os.environ['YOUR_LLM_KEY']}",
                "Content-Type": "application/json",
            },
            json={"prompt": prompt, "model": "your-model"},
        )
        return r.json()["choices"][0]["message"]["content"]


# ----------------- VIEW IN HELICONE DASHBOARD -----------------

DASHBOARD = "https://us.helicone.ai/requests"


if __name__ == "__main__":
    print(chat("What's the rate limit pattern?"))
    print(chat_anthropic("Same question, different model."))
    print(f"\\nView traces: {DASHBOARD}")
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI client (Helicone is a proxy)"},
            {"name": "anthropic", "version": ">=0.36", "purpose": "Anthropic via Helicone"},
            {"name": "httpx", "version": ">=0.27", "purpose": "Custom HTTP proxying"},
        ],
        "env_vars": [
            {"name": "HELICONE_API_KEY", "required": True, "description": "From helicone.ai dashboard", "example": "sk-helicone-..."},
            {"name": "OPENAI_API_KEY", "required": False, "description": "Original OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "Sign up at helicone.ai (free tier: 100k requests/mo)",
            "Generate API key in dashboard",
            "Change base_url and add Helicone-Auth header",
            "Run any LLM call — view in dashboard within seconds",
        ],
        "variations": [
            {"label": "Self-host Helicone", "description": "OSS version for control.", "code_snippet": "# git clone github.com/Helicone/helicone; docker-compose up. Same SDK pattern, swap base_url to your domain."},
            {"label": "Prompt templating + versioning", "description": "Track prompts in Helicone.", "code_snippet": "# Helicone-Prompt-Id header registers the template; versions are auto-tracked. Useful for prompt-engineering workflows."},
            {"label": "Async with httpx", "description": "Same proxy works for async.", "code_snippet": "from openai import AsyncOpenAI\\nasync_client = AsyncOpenAI(base_url='https://oai.helicone.ai/v1', ...)"},
        ],
        "common_errors": [
            {"error_text": "401 Unauthorized", "cause": "Helicone-Auth header missing or wrong.", "fix_snippet": "Header is 'Helicone-Auth: Bearer sk-helicone-...'. Note 'Bearer' prefix. Use exact header name."},
            {"error_text": "Higher latency than direct API", "cause": "Helicone adds ~50ms.", "fix_snippet": "Free tier is shared infrastructure. Pro tier has dedicated regions / sub-10ms overhead. Or self-host."},
            {"error_text": "Cache not hitting", "cause": "Different request body each time.", "fix_snippet": "Same prompt + same params → cache hit. Set Helicone-Cache-Seed: 'vN' to invalidate cache batches."},
            {"error_text": "Tracking missing user info", "cause": "Forgot to set Helicone-User-Id.", "fix_snippet": "Pass Helicone-User-Id on every request. Per-user analytics + rate limiting depend on it."},
        ],
        "production_checklist": [
            "Tag requests with Helicone-User-Id + Property-* for filtering.",
            "Set per-user rate limits via Helicone-RateLimit-Policy.",
            "Enable caching for repetitive queries.",
            "Monitor: cost-per-user, error rates, latency by model.",
            "Set up Slack / email alerts for cost spikes in dashboard.",
            "For sensitive workloads, self-host Helicone.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "claude-3-5-haiku"],
            "library_versions": ["openai==1.51", "anthropic==0.36"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["helicone", "openai"],
        "related_glossary_slugs": ["llm-proxy", "observability"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Helicone vs LangSmith vs Langfuse?", "answer": "Helicone: drop-in proxy, no code change, automatic. LangSmith: deeper LangChain integration. Langfuse: OSS, self-hostable, decorator-based. Helicone wins on ZERO code change."},
            {"question": "Privacy concerns?", "answer": "Self-host Helicone for full control. SaaS option has SOC2; prompts are stored encrypted. For PII, scrub client-side before sending."},
            {"question": "Cost?", "answer": "Free tier: 100k requests/mo, generous. Pro: $50+/mo unlimited. Self-host: free, your own infra. Compare to LangSmith Plus ($39/mo)."},
            {"question": "Does it slow my app?", "answer": "Free tier: +50-100ms typical. Pro: <30ms. Self-hosted: depends on your infra. For latency-critical apps, self-host or use async."},
        ],
        "github_url": "https://github.com/Helicone/helicone",
        "meta_title": "Helicone Proxy LLM Observability Starter",
        "meta_description": "Helicone proxy for LLM observability: change one URL, get logging + caching + retries + cost tracking. No code change.",
    },
    {
        "slug": "traceloop-openllmetry-cost-tracking",
        "title": "OpenLLMetry Cost Tracking With OTel",
        "tldr": "Traceloop OpenLLMetry: OpenTelemetry-native LLM observability. Auto-instruments OpenAI / Anthropic / LangChain. Pipe traces to ANY OTel backend (Honeycomb, Datadog, Jaeger).",
        "category": "observability",
        "language": "python",
        "framework": "Traceloop OpenLLMetry",
        "tags": ["opentelemetry", "traceloop", "cost-tracking", "vendor-neutral"],
        "best_for_tags": ["otel-shops", "vendor-neutral", "production"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Already have OpenTelemetry infrastructure (Honeycomb, Datadog, Grafana Tempo). Want LLM traces in the same backend as your service traces. OpenLLMetry is the standard.",
        "when_not_to_use": "Skip for greenfield projects without OTel — adopt a managed LLM-specific tool (Langfuse, Helicone) first. Skip for tiny apps (overhead).",
        "quick_start": "pip install traceloop-sdk && set env vars && Traceloop.init()",
        "full_code": '''"""OpenLLMetry: OpenTelemetry-native LLM tracing + cost tracking."""
from __future__ import annotations

import os
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import task, workflow


# ----------------- INIT (auto-instruments OpenAI, Anthropic, etc.) -----------------

Traceloop.init(
    app_name="my-llm-app",
    api_endpoint=os.environ.get("TRACELOOP_BASE_URL", "https://api.traceloop.com"),
    api_key=os.environ.get("TRACELOOP_API_KEY"),
    disable_batch=False,  # batch spans for efficiency
)


# ----------------- AUTO-INSTRUMENTED LLM CALLS -----------------

# After Traceloop.init(), all OpenAI / Anthropic / LangChain calls are traced automatically.

from openai import OpenAI
client = OpenAI()


@task(name="classify_ticket")
def classify(message: str) -> str:
    """Decorated task — surfaces as a span in the trace."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Classify: {message}"}],
    )
    return response.choices[0].message.content


@task(name="suggest_response")
def suggest_response(classification: str, message: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Reply to {classification} message: {message}"}],
    )
    return response.choices[0].message.content


# ----------------- WORKFLOW (groups tasks into a parent span) -----------------

@workflow(name="handle_ticket")
def handle_ticket(message: str) -> dict:
    """Workflow groups all child tasks under one parent span."""
    classification = classify(message)
    response = suggest_response(classification, message)
    return {"classification": classification, "response": response}


# ----------------- ADD METADATA TO SPANS -----------------

from traceloop.sdk.tracing.context_manager import set_association_properties


def handle_with_metadata(message: str, user_id: str, session_id: str):
    set_association_properties({
        "user_id": user_id,
        "session_id": session_id,
        "tier": "pro",  # custom attributes
    })
    return handle_ticket(message)


# ----------------- EXPORT TO YOUR OTEL BACKEND -----------------

# To export to Honeycomb / Datadog / etc., set OpenTelemetry env vars BEFORE Traceloop.init():
#
#   export OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io
#   export OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=$HONEYCOMB_KEY"
#   export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
#
# Or to Traceloop's hosted backend:
#   export TRACELOOP_API_KEY=tl_...


if __name__ == "__main__":
    result = handle_with_metadata(
        "Hi, I was charged twice for September.",
        user_id="u_123",
        session_id="s_abc",
    )
    print(result)
    print("\\nView traces in your OTel backend (Honeycomb / Traceloop dashboard / etc.)")
''',
        "dependencies": [
            {"name": "traceloop-sdk", "version": ">=0.20", "purpose": "OpenLLMetry SDK"},
            {"name": "openai", "version": ">=1.40", "purpose": "LLM client (auto-instrumented)"},
        ],
        "env_vars": [
            {"name": "TRACELOOP_API_KEY", "required": False, "description": "Traceloop hosted backend", "example": "tl_..."},
            {"name": "OTEL_EXPORTER_OTLP_ENDPOINT", "required": False, "description": "Generic OTel backend URL", "example": "https://api.honeycomb.io"},
        ],
        "setup_steps": [
            "pip install traceloop-sdk openai",
            "Decide backend: Traceloop hosted OR generic OTel (Honeycomb, Datadog, Jaeger)",
            "Set env vars",
            "Call Traceloop.init() once at app startup",
            "Decorate workflows with @workflow and tasks with @task",
        ],
        "variations": [
            {"label": "Async OpenAI", "description": "Same instrumentation works for async.", "code_snippet": "from openai import AsyncOpenAI\\nclient = AsyncOpenAI()  # auto-traced"},
            {"label": "Without Traceloop SDK", "description": "Use raw OpenTelemetry SDK directly.", "code_snippet": "# from openllmetry.instrumentation.openai import OpenAIInstrumentor\\n# OpenAIInstrumentor().instrument()  # OpenLLMetry instrumentation libs are OSS"},
            {"label": "Custom span attributes", "description": "Add domain-specific attrs.", "code_snippet": "from opentelemetry import trace\\nspan = trace.get_current_span()\\nspan.set_attribute('custom.attr', 'value')"},
        ],
        "common_errors": [
            {"error_text": "Traces not appearing", "cause": "Backend endpoint wrong.", "fix_snippet": "Check OTEL_EXPORTER_OTLP_ENDPOINT. Run with TRACELOOP_DEBUG=true to see what's being sent. Verify headers (auth)."},
            {"error_text": "Auto-instrumentation missing OpenAI calls", "cause": "Traceloop.init() called AFTER OpenAI import.", "fix_snippet": "Call Traceloop.init() FIRST, before importing openai. Or use explicit OpenAIInstrumentor().instrument()."},
            {"error_text": "Span performance overhead", "cause": "Sync export.", "fix_snippet": "Use disable_batch=False (batched export). For very high QPS, lower sample rate via OTEL_TRACES_SAMPLER."},
            {"error_text": "Cost metric missing", "cause": "Model not in cost map.", "fix_snippet": "Custom model? Set TRACELOOP_TRACK_TOKENS=true; emit usage manually if needed. Standard OpenAI/Anthropic models are auto-priced."},
        ],
        "production_checklist": [
            "Initialize ONCE at app startup, before LLM imports.",
            "Use @workflow / @task for logical grouping.",
            "Add user_id / session_id via set_association_properties.",
            "Set OTel sampling rate for high QPS apps (1% sampling is plenty).",
            "Pin Traceloop + OpenTelemetry versions (rapid evolution).",
            "Monitor span ingestion rate at your OTel backend.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["traceloop-sdk==0.20", "openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["traceloop-openllmetry", "opentelemetry"],
        "related_glossary_slugs": ["opentelemetry", "tracing"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "OpenLLMetry vs proprietary tools?", "answer": "OpenLLMetry: vendor-neutral, OpenTelemetry standard, works with any OTel backend. Proprietary (Helicone, LangSmith): more polished UI, opinionated. Pick OpenLLMetry if you already use OTel."},
            {"question": "Traceloop SDK vs raw OTel?", "answer": "Traceloop SDK: convenience layer (decorators, defaults). Raw OTel + OpenLLMetry instrumentation libs: more control, less magic. Both produce the same traces."},
            {"question": "Cost?", "answer": "Traceloop hosted backend: free tier 10k traces/mo, then ~$0.10/1k. Self-host with Jaeger / Tempo: free + ops cost. Honeycomb/Datadog: per their pricing."},
            {"question": "Privacy — does it log prompts?", "answer": "Yes by default. Set TRACELOOP_TRACK_PROMPTS=false to log metadata only. For sensitive prompts, scrub before sending or self-host."},
        ],
        "github_url": "https://github.com/traceloop/openllmetry",
        "meta_title": "OpenLLMetry Cost Tracking With OTel Starter",
        "meta_description": "OpenLLMetry: OpenTelemetry-native LLM observability. Auto-instrument OpenAI/Anthropic/LangChain. Send traces to Honeycomb/Datadog/Jaeger.",
    },
    {
        "slug": "langfuse-self-hosted-llm-traces",
        "title": "Langfuse Self-Hosted LLM Traces (Open Source)",
        "tldr": "Langfuse: self-hostable, OSS LLM observability with traces, evals, datasets, prompt versioning. Docker-compose up + decorate your code. Full data control.",
        "category": "observability",
        "language": "python",
        "framework": "Langfuse",
        "tags": ["langfuse", "self-hosted", "oss", "observability"],
        "best_for_tags": ["data-control", "compliance", "production"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Compliance-sensitive shop that needs LLM observability with data-control. Langfuse OSS runs in your VPC. Comparable feature set to LangSmith / Helicone hosted.",
        "when_not_to_use": "Skip for solo / hobby (Langfuse hosted free tier is plenty). Skip for teams without infra capacity to maintain it.",
        "quick_start": "docker compose up -d # from langfuse repo && pip install langfuse",
        "full_code": '''"""Langfuse self-hosted: full LLM observability stack."""
from __future__ import annotations

import os
from langfuse.decorators import observe, langfuse_context
from langfuse.openai import openai  # drop-in replacement


# ----------------- SETUP (env vars) -----------------

# os.environ["LANGFUSE_HOST"] = "http://localhost:3000"  # self-hosted
# os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-..."
# os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-..."


# ----------------- @observe DECORATOR (single line) -----------------

@observe(name="classify_ticket")
def classify(message: str) -> str:
    """Decorated functions show as spans in Langfuse."""
    response = openai.chat.completions.create(  # langfuse.openai wraps it
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Classify: {message}"}],
        temperature=0,
    )
    return response.choices[0].message.content


@observe(name="generate_response")
def respond(classification: str, message: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Reply to {classification}: {message}"}],
    )
    return response.choices[0].message.content


# ----------------- TRACE WITH METADATA -----------------

@observe(name="ticket_pipeline")
def handle_ticket(message: str, user_id: str, session_id: str) -> dict:
    # Attach metadata to the trace
    langfuse_context.update_current_trace(
        user_id=user_id,
        session_id=session_id,
        tags=["production", "tier:pro"],
        metadata={"source": "web"},
    )

    classification = classify(message)
    response = respond(classification, message)

    # Manual scoring (for offline eval)
    langfuse_context.score_current_trace(
        name="quality",
        value=0.9,
        comment="LGTM (auto-scored)",
    )

    return {"classification": classification, "response": response}


# ----------------- PROMPT VERSIONING (Langfuse-managed) -----------------

from langfuse import Langfuse

langfuse = Langfuse()  # uses env vars


def get_prompt(name: str = "classify-v1") -> str:
    """Pull a prompt from Langfuse — versioned, can be edited in UI."""
    return langfuse.get_prompt(name).prompt


# Push a prompt programmatically (or in the UI)
def push_prompt():
    langfuse.create_prompt(
        name="classify-v1",
        prompt="Classify the customer message: {{message}}",
        labels=["production"],
        config={"model": "gpt-4o-mini", "temperature": 0},
    )


# ----------------- DATASET (for eval) -----------------

def create_eval_dataset():
    langfuse.create_dataset(name="classify-eval-set")
    examples = [
        {"input": {"message": "I want a refund"}, "expected": {"category": "billing"}},
        {"input": {"message": "App is broken"}, "expected": {"category": "technical"}},
    ]
    for ex in examples:
        langfuse.create_dataset_item(
            dataset_name="classify-eval-set",
            input=ex["input"],
            expected_output=ex["expected"],
        )


# ----------------- DEMO -----------------

if __name__ == "__main__":
    result = handle_ticket(
        "I was charged $99 twice last month, please refund.",
        user_id="u_42",
        session_id="s_xyz",
    )
    print(result)
    print("\\nView traces: http://localhost:3000 (or your Langfuse host)")
''',
        "dependencies": [
            {"name": "langfuse", "version": ">=2.50", "purpose": "Langfuse SDK"},
        ],
        "env_vars": [
            {"name": "LANGFUSE_HOST", "required": True, "description": "Langfuse server URL", "example": "http://localhost:3000"},
            {"name": "LANGFUSE_PUBLIC_KEY", "required": True, "description": "Public key from project settings", "example": "pk-lf-..."},
            {"name": "LANGFUSE_SECRET_KEY", "required": True, "description": "Secret key", "example": "sk-lf-..."},
            {"name": "OPENAI_API_KEY", "required": True, "description": "Underlying LLM", "example": "sk-..."},
        ],
        "setup_steps": [
            "Self-host: git clone github.com/langfuse/langfuse && docker compose up -d",
            "Create project in Langfuse UI, copy keys",
            "Export LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY",
            "pip install langfuse",
            "Replace `from openai import OpenAI` with `from langfuse.openai import openai`",
        ],
        "variations": [
            {"label": "Langfuse Cloud (managed)", "description": "Skip Docker; use hosted.", "code_snippet": "# Sign up at cloud.langfuse.com, free tier 50k traces/mo. Set LANGFUSE_HOST=https://cloud.langfuse.com"},
            {"label": "LangChain integration", "description": "Auto-trace LangChain.", "code_snippet": "from langfuse.callback import CallbackHandler\\nllm = ChatOpenAI(callbacks=[CallbackHandler()])"},
            {"label": "Async client", "description": "AsyncIO patterns.", "code_snippet": "from langfuse.openai import AsyncOpenAI; async_client = AsyncOpenAI(); # full instrumented async"},
        ],
        "common_errors": [
            {"error_text": "Traces not appearing in UI", "cause": "Wrong host or key.", "fix_snippet": "Verify env vars; LANGFUSE_HOST should NOT have trailing slash. langfuse.flush() at app exit to push buffered traces."},
            {"error_text": "@observe decorator missing imports", "cause": "Old SDK or wrong package.", "fix_snippet": "pip install -U langfuse>=2.50. from langfuse.decorators import observe (singular). Old syntax langfuse_observability is deprecated."},
            {"error_text": "High memory usage", "cause": "Buffer not flushing.", "fix_snippet": "Set LANGFUSE_FLUSH_INTERVAL=1.0 for faster flushing. Or call langfuse.flush() periodically in long-running services."},
            {"error_text": "DB grows quickly", "cause": "All traces stored.", "fix_snippet": "Self-hosted: configure data retention policy. Sample non-error traces. Aggressive cleanup of old traces."},
        ],
        "production_checklist": [
            "Run Langfuse in same VPC as your app (low latency).",
            "Backup Langfuse Postgres + ClickHouse regularly.",
            "Set retention policy (90 days typical).",
            "Sample non-error traces if QPS high (1-10%).",
            "Use Langfuse prompt-versioning to track prompt changes.",
            "Run Langfuse evals on subset of production traces.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["langfuse==2.50"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["langfuse"],
        "related_glossary_slugs": ["langfuse", "self-hosted-observability"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Langfuse vs LangSmith?", "answer": "Langfuse: OSS, self-hostable, framework-agnostic. LangSmith: managed SaaS, deep LangChain integration. Pick Langfuse for data-control needs."},
            {"question": "Self-host requirements?", "answer": "Docker compose: Postgres + ClickHouse + Langfuse app. ~4GB RAM for small workloads. K8s helm chart available for scale."},
            {"question": "Cost of Cloud?", "answer": "Free: 50k traces/mo. Pro: $50+/mo. Team: $250+/mo. Includes evals + prompt management."},
            {"question": "Migrate from LangSmith?", "answer": "Both use similar trace schemas. Langfuse has a LangSmith importer. The Decorator API is comparable; instrumentation is similar effort."},
        ],
        "github_url": "https://github.com/langfuse/langfuse",
        "meta_title": "Langfuse Self-Hosted LLM Traces Starter",
        "meta_description": "Langfuse self-hosted: OSS LLM observability with traces, evals, datasets, prompt versioning. Docker compose + decorator-based instrumentation.",
    },
    {
        "slug": "llm-cost-budget-with-alerts",
        "title": "Per-Tenant LLM Cost Budget With Alerts",
        "tldr": "Track LLM cost per tenant in real-time. Hard cap (block) + soft cap (alert). Pairs with any LLM provider. Don't get surprised by a $10k Anthropic bill.",
        "category": "observability",
        "language": "python",
        "framework": "Redis + Custom",
        "tags": ["cost-tracking", "budgets", "alerting", "multi-tenant"],
        "best_for_tags": ["multi-tenant-saas", "cost-control", "production"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Multi-tenant LLM app where tenants can burn through cost. This pattern caps cost per tenant per period + alerts when approaching the cap. Saves you from surprise bills.",
        "when_not_to_use": "Skip for single-tenant apps. Skip if you're using a provider with built-in budgets (most SaaS LLMs have account-level caps; this adds per-tenant).",
        "quick_start": "pip install redis litellm && python cost_budget.py",
        "full_code": '''"""Per-tenant LLM cost budget with Redis counters + alerts."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime

import redis
from litellm import cost_per_token, completion


redis_client = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))


# ----------------- BUDGET CONFIG -----------------

@dataclass
class TenantBudget:
    tenant_id: str
    daily_soft_cap_usd: float       # alert at this point
    daily_hard_cap_usd: float       # block at this point
    monthly_hard_cap_usd: float


BUDGETS: dict[str, TenantBudget] = {
    "acme_corp": TenantBudget("acme_corp", daily_soft_cap_usd=10.0,
                              daily_hard_cap_usd=20.0, monthly_hard_cap_usd=500.0),
    "demo_user": TenantBudget("demo_user", daily_soft_cap_usd=0.5,
                              daily_hard_cap_usd=1.0, monthly_hard_cap_usd=10.0),
}


# ----------------- BUDGET CHECK + INCREMENT -----------------

class BudgetExceeded(Exception):
    pass


def _bucket_key(tenant_id: str, period: str) -> str:
    if period == "daily":
        return f"cost:daily:{tenant_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
    elif period == "monthly":
        return f"cost:monthly:{tenant_id}:{datetime.utcnow().strftime('%Y-%m')}"
    raise ValueError(period)


def get_spend(tenant_id: str, period: str = "daily") -> float:
    key = _bucket_key(tenant_id, period)
    val = redis_client.get(key)
    return float(val) if val else 0.0


def check_budget(tenant_id: str) -> None:
    """Raise BudgetExceeded if over hard cap. Side-effect: log soft-cap warning."""
    budget = BUDGETS.get(tenant_id)
    if not budget:
        raise ValueError(f"Unknown tenant {tenant_id}")

    daily = get_spend(tenant_id, "daily")
    monthly = get_spend(tenant_id, "monthly")

    if daily >= budget.daily_hard_cap_usd:
        raise BudgetExceeded(f"Daily cap ${budget.daily_hard_cap_usd:.2f} hit (${daily:.2f})")
    if monthly >= budget.monthly_hard_cap_usd:
        raise BudgetExceeded(f"Monthly cap ${budget.monthly_hard_cap_usd:.2f} hit")

    if daily >= budget.daily_soft_cap_usd:
        notify_soft_cap(tenant_id, daily, budget.daily_soft_cap_usd)


def increment_spend(tenant_id: str, cost_usd: float) -> None:
    pipe = redis_client.pipeline()
    daily_key = _bucket_key(tenant_id, "daily")
    monthly_key = _bucket_key(tenant_id, "monthly")
    pipe.incrbyfloat(daily_key, cost_usd)
    pipe.expire(daily_key, 86400 * 2)        # auto-expire 2 days
    pipe.incrbyfloat(monthly_key, cost_usd)
    pipe.expire(monthly_key, 86400 * 35)     # auto-expire ~1 month later
    pipe.execute()


# ----------------- WRAP LLM CALL -----------------

def llm_call(tenant_id: str, model: str, messages: list[dict], **kwargs) -> str:
    check_budget(tenant_id)  # raises if over hard cap

    response = completion(model=model, messages=messages, **kwargs)
    usage = response.usage

    # Compute cost using LiteLLM's cost map
    input_cost, output_cost = cost_per_token(
        model=model,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
    )
    total = input_cost + output_cost

    increment_spend(tenant_id, total)

    return response.choices[0].message.content


# ----------------- ALERTING -----------------

def notify_soft_cap(tenant_id: str, current: float, threshold: float):
    """Hit Slack / PagerDuty / email — once per day per tenant."""
    flag_key = f"soft_cap_alerted:{tenant_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
    if redis_client.setnx(flag_key, "1"):
        redis_client.expire(flag_key, 86400)
        # Send actual alert here
        print(f"⚠️  SOFT CAP HIT: {tenant_id} at ${current:.2f} (threshold ${threshold:.2f})")
        # Example: requests.post(SLACK_WEBHOOK, json={"text": f"..."})


# ----------------- DEMO -----------------

if __name__ == "__main__":
    try:
        for i in range(5):
            result = llm_call(
                tenant_id="demo_user",
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Iteration {i}: explain caching."}],
            )
            print(f"[{i}] OK; spent: ${get_spend('demo_user'):.4f}")
            time.sleep(0.1)
    except BudgetExceeded as e:
        print(f"Blocked: {e}")
''',
        "dependencies": [
            {"name": "redis", "version": ">=5.0", "purpose": "Counters + alerting flag"},
            {"name": "litellm", "version": ">=1.50", "purpose": "Universal LLM + cost lookup"},
        ],
        "env_vars": [
            {"name": "REDIS_URL", "required": True, "description": "Redis connection", "example": "redis://localhost:6379"},
            {"name": "OPENAI_API_KEY", "required": True, "description": "Provider key for LLM", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install redis litellm",
            "Run Redis: docker run -d -p 6379:6379 redis:7",
            "Define BUDGETS dict for your tenants",
            "Wire llm_call() into your application code",
            "Connect notify_soft_cap to Slack/PagerDuty/email",
        ],
        "variations": [
            {"label": "Per-feature budget", "description": "Budget per FEATURE within a tenant.", "code_snippet": "# Bucket key: f'cost:daily:{tenant_id}:{feature}'. Separate budgets per use case (search, summarize, chat)."},
            {"label": "Rolling-window budget", "description": "Last-hour or last-7-day window.", "code_snippet": "# Use Redis sorted set with timestamps. ZADD on each call; ZREMRANGEBYSCORE old entries. Sum recent."},
            {"label": "Soft fail (warn user)", "description": "Instead of blocking, surface warning to user.", "code_snippet": "# Replace 'raise BudgetExceeded' with: return {'error': 'usage_cap_reached', 'reset_at': end_of_day}. App handles UX."},
        ],
        "common_errors": [
            {"error_text": "Redis race condition on increment", "cause": "Multiple workers updating simultaneously.", "fix_snippet": "INCRBYFLOAT is atomic in Redis. The pattern works under concurrency. Verify with redis-cli MONITOR if suspicious."},
            {"error_text": "Cost off vs provider billing", "cause": "LiteLLM cost map slightly out of date.", "fix_snippet": "Pin LiteLLM version. Compare monthly counters vs actual invoice. Adjust hard caps with 5-10% buffer."},
            {"error_text": "Alert flood (re-alerting every call)", "cause": "Forgot the SETNX flag.", "fix_snippet": "Use SETNX with daily expiry. notify_soft_cap pattern in the code prevents floods."},
            {"error_text": "Hard cap blocks legitimate burst", "cause": "Cap too aggressive.", "fix_snippet": "Soft + hard caps with buffer between (e.g., soft=$10, hard=$20). Allow short bursts; alert on soft to investigate."},
        ],
        "production_checklist": [
            "Monthly + daily caps (different rates of growth).",
            "Soft cap (alert) + hard cap (block) layered.",
            "Per-tenant + per-feature budgets if multi-feature app.",
            "Alert deduplication (SETNX flag per day).",
            "Audit log: every block, every alert, every increment.",
            "Daily reconciliation against provider billing.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["redis==5.0", "litellm==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["litellm", "redis"],
        "related_glossary_slugs": ["cost-tracking", "rate-limiting"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Soft vs hard caps?", "answer": "Soft cap: alert internally, keep serving. Hard cap: block requests. Both exist to give you time to investigate before customers lose service."},
            {"question": "Per-tenant vs per-user?", "answer": "Depends on your SaaS model. Tenant (org) typical for B2B; user typical for consumer. Can layer: per-user inside per-tenant."},
            {"question": "Counter precision concerns?", "answer": "Redis INCRBYFLOAT uses floats; tiny rounding errors at scale. For STRICT accuracy, store cents (int) instead of dollars (float)."},
            {"question": "What about retries / failed calls?", "answer": "Failed calls (cost=0 from provider) don't increment. Successful retries DO. Pattern naturally tracks actual spend."},
        ],
        "github_url": "",
        "meta_title": "Per-Tenant LLM Cost Budget Starter",
        "meta_description": "Real-time LLM cost tracking per tenant: soft + hard caps, Redis counters, alert dedup, LiteLLM cost lookup. Prevent surprise bills.",
    },
]
