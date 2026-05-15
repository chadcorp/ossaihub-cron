"""Production patterns — batch 2: multi-tenant isolation, prompt versioning, SLA monitoring, canary deploys."""

RECORDS = [
    {
        "slug": "multi-tenant-llm-isolation",
        "title": "Multi-Tenant LLM Isolation (Quotas + Data Isolation)",
        "tldr": "Multi-tenant LLM app pattern: per-tenant rate limit, cost budget, data isolation in retrieval, and tenant-scoped audit log. Production must-haves.",
        "category": "production",
        "language": "python",
        "framework": "FastAPI + Redis",
        "tags": ["multi-tenant", "isolation", "quotas", "production"],
        "best_for_tags": ["saas", "b2b", "regulated-industries"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "Multi-tenant SaaS LLM app. Each customer needs: isolated data, separate rate limits, separate budgets, audit trail. Skip these and you'll have a security incident.",
        "when_not_to_use": "Skip for single-tenant apps. Skip for prototypes (overhead). Skip if your LLM is purely user-facing with no per-customer state.",
        "quick_start": "pip install fastapi redis 'uvicorn[standard]' && python multi_tenant_llm.py",
        "full_code": '''"""Multi-tenant LLM service with quotas + isolation + audit."""
from __future__ import annotations

import json
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Header
from pydantic import BaseModel
import redis.asyncio as aioredis


REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")


# ----------------- TENANT CONFIG -----------------

TENANTS = {
    "acme_corp": {
        "rpm": 100,
        "tpm": 100_000,
        "daily_budget_usd": 50.0,
        "allowed_models": ["gpt-4o-mini", "gpt-4o"],
        "data_namespace": "acme",
    },
    "demo_user": {
        "rpm": 10,
        "tpm": 5_000,
        "daily_budget_usd": 1.0,
        "allowed_models": ["gpt-4o-mini"],
        "data_namespace": "demo",
    },
}


# ----------------- LIFESPAN -----------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = aioredis.from_url(REDIS_URL)
    yield
    await app.state.redis.close()


app = FastAPI(lifespan=lifespan)


# ----------------- AUTH + TENANT RESOLUTION -----------------

async def get_tenant(authorization: str | None = Header(None)) -> dict:
    """Map bearer token → tenant config."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.removeprefix("Bearer ")

    # Real: lookup token → tenant in DB. Stub:
    token_map = {"acme_token_123": "acme_corp", "demo_token_456": "demo_user"}
    tenant_id = token_map.get(token)
    if not tenant_id:
        raise HTTPException(403, "Invalid token")
    return {"tenant_id": tenant_id, **TENANTS[tenant_id]}


# ----------------- RATE LIMIT (sliding window) -----------------

async def enforce_rate_limit(tenant: dict, app: FastAPI):
    redis = app.state.redis
    now = int(time.time())
    rpm_key = f"rl:rpm:{tenant['tenant_id']}:{now // 60}"
    pipe = redis.pipeline()
    pipe.incr(rpm_key)
    pipe.expire(rpm_key, 120)
    count, _ = await pipe.execute()
    if count > tenant["rpm"]:
        raise HTTPException(429, f"Rate limit exceeded ({tenant['rpm']} rpm)")


# ----------------- BUDGET CHECK -----------------

async def enforce_budget(tenant: dict, app: FastAPI):
    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")
    key = f"cost:daily:{tenant['tenant_id']}:{today}"
    spent = float(await app.state.redis.get(key) or 0)
    if spent >= tenant["daily_budget_usd"]:
        raise HTTPException(402, f"Daily budget ${tenant['daily_budget_usd']:.2f} exhausted")


# ----------------- DATA ISOLATION (retrieval namespace) -----------------

def retrieve(query: str, namespace: str) -> list[str]:
    """Stub — replace with vector store call SCOPED to the tenant's namespace."""
    # E.g., Pinecone: index.query(namespace=namespace, ...)
    # NEVER allow cross-namespace queries.
    return [f"[doc in {namespace} matching '{query}']"]


# ----------------- AUDIT LOG -----------------

async def audit_log(app: FastAPI, tenant_id: str, action: str, details: dict):
    entry = {
        "tenant_id": tenant_id,
        "ts": int(time.time()),
        "action": action,
        **details,
    }
    # Real: write to Postgres / Loki / Splunk. Stub:
    await app.state.redis.xadd(f"audit:{tenant_id}", {"data": json.dumps(entry)})


# ----------------- ENDPOINT -----------------

class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-4o-mini"


@app.post("/chat")
async def chat(request: Request, body: ChatRequest, tenant: dict = Depends(get_tenant)):
    # 1. Model allowed?
    if body.model not in tenant["allowed_models"]:
        raise HTTPException(403, f"Model {body.model} not allowed for tenant")

    # 2. Rate limit
    await enforce_rate_limit(tenant, request.app)

    # 3. Budget
    await enforce_budget(tenant, request.app)

    # 4. Data isolation (retrieval scoped to namespace)
    context = retrieve(body.message, namespace=tenant["data_namespace"])

    # 5. Call LLM (stub)
    response_text = f"[response using {body.model} with context: {context}]"

    # 6. Increment counters
    # Real: compute actual cost from token usage
    estimated_cost = 0.001
    await request.app.state.redis.incrbyfloat(
        f"cost:daily:{tenant['tenant_id']}:" + time.strftime("%Y-%m-%d"),
        estimated_cost,
    )

    # 7. Audit
    await audit_log(request.app, tenant["tenant_id"], "chat",
                    {"model": body.model, "cost_usd": estimated_cost})

    return {"response": response_text, "cost_usd": estimated_cost}


# ----------------- USAGE ENDPOINT (transparency for tenant) -----------------

@app.get("/usage")
async def usage(request: Request, tenant: dict = Depends(get_tenant)):
    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")
    spent = float(await request.app.state.redis.get(
        f"cost:daily:{tenant['tenant_id']}:{today}"
    ) or 0)
    return {
        "tenant_id": tenant["tenant_id"],
        "spent_today_usd": spent,
        "budget_usd": tenant["daily_budget_usd"],
        "remaining_usd": max(0, tenant["daily_budget_usd"] - spent),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
        "dependencies": [
            {"name": "fastapi[standard]", "version": ">=0.115", "purpose": "Web framework"},
            {"name": "redis", "version": ">=5.0", "purpose": "Counters + audit"},
            {"name": "uvicorn[standard]", "version": ">=0.30", "purpose": "ASGI server"},
        ],
        "env_vars": [
            {"name": "REDIS_URL", "required": True, "description": "Redis connection", "example": "redis://localhost:6379"},
        ],
        "setup_steps": [
            "pip install 'fastapi[standard]' redis 'uvicorn[standard]'",
            "Run Redis",
            "Replace TENANTS stub with real tenant DB lookup",
            "Wire retrieve() to your vector store with namespace=tenant",
            "uvicorn multi_tenant_llm:app --host 0.0.0.0 --port 8000",
        ],
        "variations": [
            {"label": "Token bucket rate limit", "description": "Smoother than sliding-window.", "code_snippet": "# Use Redis Lua script for atomic token-bucket: refill at rate, consume per-request. More natural for bursty traffic."},
            {"label": "Per-user within tenant", "description": "Two-level isolation.", "code_snippet": "# Key: f'cost:daily:{tenant_id}:{user_id}:{date}'. Layer per-user budget INSIDE per-tenant budget."},
            {"label": "Audit to Loki / S3", "description": "Persist audit logs.", "code_snippet": "# Replace XADD with: write to Loki via Promtail, or batched JSONL to S3. Required for compliance."},
        ],
        "common_errors": [
            {"error_text": "Cross-tenant data leak", "cause": "Forgot namespace= on vector store query.", "fix_snippet": "Enforce at wrapper layer: every retrieval function REQUIRES namespace param. Code review for any call missing it."},
            {"error_text": "Rate limit too tight", "cause": "Bursty traffic patterns.", "fix_snippet": "Use token bucket instead of sliding window. Allow short bursts; enforce average rate."},
            {"error_text": "Budget race condition", "cause": "Multiple workers check then increment.", "fix_snippet": "INCRBYFLOAT first (atomic); check if exceeded; refund if needed. Or use Redis Lua for atomic check-and-increment."},
            {"error_text": "Auth check missing on /usage endpoint", "cause": "Forgot Depends(get_tenant).", "fix_snippet": "EVERY endpoint should have Depends(get_tenant). Audit code review checklist."},
        ],
        "production_checklist": [
            "Every endpoint requires tenant authentication.",
            "Retrieval scoped to tenant namespace — enforce at wrapper.",
            "Rate limits per tenant, with sensible bursts.",
            "Budgets daily AND monthly, soft + hard caps.",
            "Audit log every action (write somewhere durable).",
            "Tenant config in DB, not code (so non-eng can adjust).",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["fastapi==0.115", "redis==5.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["fastapi", "redis"],
        "related_glossary_slugs": ["multi-tenant", "rate-limiting"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Hardest part of multi-tenant LLM?", "answer": "Data isolation. One forgotten 'namespace=' in retrieval = cross-tenant leak. Enforce at wrapper level; never trust calling code."},
            {"question": "How to handle a noisy tenant?", "answer": "Per-tenant rate limit catches sustained noise. Per-tenant budget catches expensive noise. Together: noisy tenant degrades only themselves."},
            {"question": "Audit log retention?", "answer": "90 days minimum for compliance. 1 year for SOC2. 7 years for regulated industries (financial, healthcare). Compute storage budget accordingly."},
            {"question": "Where store tenant config?", "answer": "Database (Postgres). Cache hot lookups in Redis. Don't put in code — non-eng need to adjust tenant limits without deploys."},
        ],
        "github_url": "",
        "meta_title": "Multi-Tenant LLM Isolation Starter",
        "meta_description": "Multi-tenant LLM: per-tenant rate limit, cost budget, data isolation, audit log. FastAPI + Redis production pattern.",
    },
    {
        "slug": "prompt-versioning-with-rollback",
        "title": "Prompt Versioning With Instant Rollback",
        "tldr": "Treat prompts like code: version them, A/B test new versions, instant-rollback when they regress. Pattern works with any LLM provider; Redis-backed for sub-ms reads.",
        "category": "production",
        "language": "python",
        "framework": "Redis + Custom",
        "tags": ["prompt-versioning", "rollback", "ab-testing", "production"],
        "best_for_tags": ["prompt-engineering", "production-llm-app", "team-workflows"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Production LLM app with multiple prompts. Allows: rollback bad prompts in seconds (no deploy), A/B test new versions, audit who changed what.",
        "when_not_to_use": "Skip for single-prompt apps (just hardcode it). Skip if your prompt-changes are tied to model deployments anyway.",
        "quick_start": "pip install redis && python prompt_registry.py",
        "full_code": '''"""Prompt versioning + rollback registry."""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Literal

import redis


redis_client = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))


# ----------------- DATA STRUCTURES -----------------

@dataclass
class PromptVersion:
    name: str
    version: int           # monotonically increasing
    template: str
    model: str
    temperature: float
    max_tokens: int
    created_at: int        # unix ts
    created_by: str
    notes: str = ""

    @property
    def hash(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:8]


# ----------------- STORAGE -----------------

def _key_active(name: str) -> str: return f"prompt:active:{name}"
def _key_version(name: str, v: int) -> str: return f"prompt:v:{name}:{v}"
def _key_history(name: str) -> str: return f"prompt:history:{name}"


def publish(prompt: PromptVersion) -> None:
    """Save a new version + mark as active."""
    pipe = redis_client.pipeline()
    pipe.set(_key_version(prompt.name, prompt.version), json.dumps(asdict(prompt)))
    pipe.set(_key_active(prompt.name), prompt.version)
    pipe.zadd(_key_history(prompt.name), {str(prompt.version): prompt.created_at})
    pipe.execute()
    print(f"✅ Published {prompt.name} v{prompt.version} (hash {prompt.hash})")


def get_active(name: str) -> PromptVersion:
    v = int(redis_client.get(_key_active(name)) or 0)
    if v == 0:
        raise ValueError(f"No active version of {name}")
    raw = redis_client.get(_key_version(name, v))
    return PromptVersion(**json.loads(raw))


def list_versions(name: str) -> list[PromptVersion]:
    versions = redis_client.zrevrange(_key_history(name), 0, -1)
    return [PromptVersion(**json.loads(redis_client.get(_key_version(name, int(v)))))
            for v in versions]


# ----------------- ROLLBACK (instant) -----------------

def rollback(name: str, to_version: int) -> None:
    """Switch active to a prior version. No deploy."""
    if not redis_client.exists(_key_version(name, to_version)):
        raise ValueError(f"Version {to_version} of {name} doesn't exist")
    redis_client.set(_key_active(name), to_version)
    print(f"⏪ Rolled back {name} to v{to_version}")


# ----------------- A/B TESTING (route % to new version) -----------------

def get_for_user(name: str, user_id: str, ab_pct: int = 0,
                 new_version: int | None = None) -> PromptVersion:
    """If ab_pct > 0, route ab_pct % of users to new_version (stable per user).

    Sticky routing: same user always gets same version during the experiment.
    """
    if ab_pct > 0 and new_version is not None:
        bucket = int(hashlib.sha256(user_id.encode()).hexdigest()[:8], 16) % 100
        if bucket < ab_pct:
            raw = redis_client.get(_key_version(name, new_version))
            return PromptVersion(**json.loads(raw))
    return get_active(name)


# ----------------- USE IT -----------------

def render(name: str, user_id: str, variables: dict) -> dict:
    """Render the active prompt with variables; return prompt + config."""
    prompt = get_for_user(name, user_id, ab_pct=10, new_version=2)  # 10% to v2
    rendered = prompt.template
    for k, v in variables.items():
        rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
    return {
        "prompt": rendered,
        "model": prompt.model,
        "temperature": prompt.temperature,
        "max_tokens": prompt.max_tokens,
        "version": prompt.version,
        "hash": prompt.hash,
    }


# ----------------- DEMO -----------------

if __name__ == "__main__":
    publish(PromptVersion(
        name="classify",
        version=1,
        template="Classify the customer message: {{message}}",
        model="gpt-4o-mini",
        temperature=0.0,
        max_tokens=200,
        created_at=int(time.time()),
        created_by="alice@example.com",
        notes="Initial version",
    ))

    publish(PromptVersion(
        name="classify",
        version=2,
        template="You are a support classifier. Classify: {{message}}. Output JSON.",
        model="gpt-4o-mini",
        temperature=0.0,
        max_tokens=200,
        created_at=int(time.time()),
        created_by="bob@example.com",
        notes="Improved JSON output",
    ))

    # A/B test
    for user in ["u1", "u2", "u3", "u4", "u5"]:
        r = render("classify", user, {"message": "I want a refund"})
        print(f"{user}: v{r['version']} hash={r['hash']}")

    # Bad version → rollback
    rollback("classify", to_version=1)

    # All users now on v1
    print("After rollback:")
    for user in ["u1", "u2", "u3"]:
        r = render("classify", user, {"message": "I want a refund"})
        print(f"{user}: v{r['version']}")
''',
        "dependencies": [
            {"name": "redis", "version": ">=5.0", "purpose": "Prompt registry store"},
        ],
        "env_vars": [
            {"name": "REDIS_URL", "required": True, "description": "Redis", "example": "redis://localhost:6379"},
        ],
        "setup_steps": [
            "pip install redis",
            "Run Redis",
            "Publish initial versions of each prompt",
            "Wire render() into your LLM call sites",
            "Build a small admin UI for non-eng to publish + rollback",
        ],
        "variations": [
            {"label": "PostgreSQL backend", "description": "Audit trail in SQL.", "code_snippet": "# Store versions in Postgres; Redis is cache. Postgres for queries / audit; Redis for sub-ms reads."},
            {"label": "Use Langfuse prompt management", "description": "Managed solution.", "code_snippet": "# from langfuse import Langfuse; prompt = langfuse.get_prompt('classify'). Same versioning, hosted."},
            {"label": "Auto-rollback on regression", "description": "Connect to eval metrics.", "code_snippet": "# If eval score for new version drops > threshold, auto-call rollback(). Pair with regression eval CI."},
        ],
        "common_errors": [
            {"error_text": "Active version pointer stale", "cause": "Multiple writers race.", "fix_snippet": "Use Redis WATCH/MULTI/EXEC or Lua script to atomically check current + set new. Or accept eventual consistency (most cases fine)."},
            {"error_text": "A/B test users flip between versions", "cause": "Routing not sticky.", "fix_snippet": "Hash user_id, modulo 100. Same user always gets same bucket. NEVER use random.random() — flips per request."},
            {"error_text": "Rollback didn't take effect", "cause": "Cached at higher layer.", "fix_snippet": "Disable caching for prompt config OR cache with short TTL (1 min). Rollback should propagate in seconds."},
            {"error_text": "Lost old versions after restart", "cause": "Used in-memory Redis (volatile).", "fix_snippet": "Persist Redis AOF or use Postgres backend. In-memory is fine for cache; not for source-of-truth."},
        ],
        "production_checklist": [
            "Persistent storage (Postgres) — Redis is cache.",
            "Audit log every publish + rollback (who, when, why).",
            "Sticky A/B routing (hash user_id, not random).",
            "Tie to regression eval: auto-rollback on metric drop.",
            "Build admin UI for non-eng — prompt iterations are PM-driven.",
            "Test rollback path in CI — should switch in <5s.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["redis==5.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["redis", "langfuse"],
        "related_glossary_slugs": ["prompt-engineering", "ab-testing"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why version prompts?", "answer": "Prompts ARE code. Code is versioned. Prompt changes can regress quality silently. Versioning + audit + rollback = production discipline."},
            {"question": "Build vs use Langfuse?", "answer": "Build: full control, custom UI. Langfuse: managed, built-in eval integration. Pick by team size — solo: Langfuse; bigger teams: build for fit."},
            {"question": "How fast should rollback be?", "answer": "<10 seconds. The point of versioning is INSTANT recovery. If rollback requires deploy, you've just rebuilt deploy machinery."},
            {"question": "Auto-rollback safe?", "answer": "Only with confidence intervals. A 2pp metric drop in 5 minutes could be noise. Auto-rollback after 3 consecutive checks, or use Bayesian framework. Otherwise: alerts to humans."},
        ],
        "github_url": "",
        "meta_title": "Prompt Versioning With Rollback Starter",
        "meta_description": "Treat prompts like code: version, A/B test, rollback in seconds. Redis-backed registry with sticky routing.",
    },
    {
        "slug": "llm-sla-monitoring-alerts",
        "title": "LLM SLA Monitoring + Alerting (Latency / Error / Cost)",
        "tldr": "Production SLA monitoring for LLM APIs: latency p50/p95/p99, error rate, cost-per-request. Prometheus + Grafana + Alertmanager. Catch degradation before customers do.",
        "category": "production",
        "language": "python",
        "framework": "Prometheus + Custom",
        "tags": ["sla", "monitoring", "alerts", "prometheus"],
        "best_for_tags": ["production", "sre", "team-discipline"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Production LLM apps where you've made SLA commitments to customers. Track latency / error / cost; alert when SLO budgets burn. Standard SRE practice for LLM workloads.",
        "when_not_to_use": "Skip for prototypes (overhead). Skip if you're using a managed observability tool that does this (Helicone, LangSmith have dashboards).",
        "quick_start": "pip install prometheus-client && python sla_metrics.py",
        "full_code": '''"""LLM SLA metrics: latency, errors, cost. Prometheus-exposed."""
from __future__ import annotations

import os
import time
import contextlib
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from openai import OpenAI


# ----------------- METRICS -----------------

REQUEST_LATENCY = Histogram(
    "llm_request_duration_seconds",
    "LLM request latency in seconds",
    labelnames=["model", "tenant", "status"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
)

REQUEST_COUNT = Counter(
    "llm_requests_total",
    "Total LLM requests",
    labelnames=["model", "tenant", "status"],
)

TOKEN_COUNT = Counter(
    "llm_tokens_total",
    "Total tokens (input + output)",
    labelnames=["model", "tenant", "type"],  # type = input | output
)

COST_USD = Counter(
    "llm_cost_usd_total",
    "Total cost in USD",
    labelnames=["model", "tenant"],
)

ERROR_COUNT = Counter(
    "llm_errors_total",
    "LLM errors by type",
    labelnames=["model", "error_type"],
)

INFLIGHT = Gauge(
    "llm_inflight_requests",
    "Currently in-flight LLM requests",
    labelnames=["model"],
)


# ----------------- WRAPPER -----------------

client = OpenAI()


@contextlib.contextmanager
def track_request(model: str, tenant: str):
    INFLIGHT.labels(model=model).inc()
    start = time.time()
    status = "success"
    try:
        yield
    except Exception as e:
        status = "error"
        ERROR_COUNT.labels(model=model, error_type=type(e).__name__).inc()
        raise
    finally:
        elapsed = time.time() - start
        REQUEST_LATENCY.labels(model=model, tenant=tenant, status=status).observe(elapsed)
        REQUEST_COUNT.labels(model=model, tenant=tenant, status=status).inc()
        INFLIGHT.labels(model=model).dec()


def chat_with_metrics(prompt: str, model: str, tenant: str) -> str:
    with track_request(model=model, tenant=tenant):
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )

        # Token + cost tracking
        TOKEN_COUNT.labels(model=model, tenant=tenant, type="input").inc(response.usage.prompt_tokens)
        TOKEN_COUNT.labels(model=model, tenant=tenant, type="output").inc(response.usage.completion_tokens)

        # Cost lookup (simplified)
        cost = (response.usage.prompt_tokens * 0.00015 +
                response.usage.completion_tokens * 0.0006) / 1000
        COST_USD.labels(model=model, tenant=tenant).inc(cost)

        return response.choices[0].message.content


# ----------------- ALERT RULES (Prometheus) -----------------

ALERT_RULES = """
# Save as prometheus/llm-alerts.yml
groups:
- name: llm_sla
  interval: 30s
  rules:
  - alert: LLMHighErrorRate
    expr: |
      sum(rate(llm_requests_total{status="error"}[5m])) by (model)
        / sum(rate(llm_requests_total[5m])) by (model) > 0.05
    for: 3m
    labels:
      severity: warning
    annotations:
      summary: "LLM error rate > 5% for model {{ $labels.model }}"

  - alert: LLMLatencyHigh
    expr: |
      histogram_quantile(0.95,
        sum(rate(llm_request_duration_seconds_bucket[5m])) by (model, le)
      ) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "LLM p95 latency > 10s for {{ $labels.model }}"

  - alert: LLMCostSpike
    expr: |
      sum(rate(llm_cost_usd_total[1h])) by (tenant)
        > 5
        and sum(rate(llm_cost_usd_total[1h] offset 1h)) by (tenant) < 1
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "5x cost spike for tenant {{ $labels.tenant }}"

  - alert: LLMNoTraffic
    expr: |
      sum(rate(llm_requests_total[10m])) by (model) == 0
        and sum(rate(llm_requests_total[10m] offset 1h)) by (model) > 1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "No LLM traffic for {{ $labels.model }} but baseline was active"
"""


# ----------------- RUN -----------------

if __name__ == "__main__":
    start_http_server(9090)  # Prometheus scrapes here
    print("Metrics on :9090/metrics. Generate load via chat_with_metrics().")
    while True:
        try:
            chat_with_metrics("Test", model="gpt-4o-mini", tenant="demo")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)
''',
        "dependencies": [
            {"name": "prometheus-client", "version": ">=0.20", "purpose": "Prometheus metrics"},
            {"name": "openai", "version": ">=1.40", "purpose": "LLM client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "LLM access", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install prometheus-client openai",
            "Run Prometheus pointing at :9090/metrics",
            "Configure Alertmanager with the rules in ALERT_RULES",
            "Set up Grafana dashboard using the metric names",
            "Test alerts: induce errors / high latency / cost spike",
        ],
        "variations": [
            {"label": "OpenTelemetry instead", "description": "Use OTel metrics for vendor-neutral.", "code_snippet": "# Replace prometheus-client with opentelemetry-api + metric reader to Prometheus/Honeycomb/Datadog"},
            {"label": "Service-mesh layer", "description": "Sidecar collects metrics.", "code_snippet": "# Istio / Linkerd auto-collect HTTP metrics. Less granular than in-app; works for any service without code change."},
            {"label": "SLO burn-rate alerts", "description": "Multi-window burn-rate alerting.", "code_snippet": "# Track error budget burn (1h vs 6h vs 24h windows). Page only when burning too fast across windows. Reduces noise."},
        ],
        "common_errors": [
            {"error_text": "Metrics cardinality explosion", "cause": "User IDs / request IDs as labels.", "fix_snippet": "Labels should be LOW-cardinality (model, tenant, status). NEVER user_id, request_id. Use exemplars or logs for high-cardinality."},
            {"error_text": "Alerts firing constantly (false positives)", "cause": "Thresholds too tight.", "fix_snippet": "Use burn-rate alerts (multi-window). Increase 'for: 5m' delays. Alert on USER IMPACT (error %, latency) not RAW metrics."},
            {"error_text": "Cost metric inaccurate vs invoice", "cause": "Hardcoded prices stale.", "fix_snippet": "Use LiteLLM cost_per_token (auto-updated). Reconcile monthly against provider invoice."},
            {"error_text": "Inflight gauge stuck high", "cause": "Exception path missed dec().", "fix_snippet": "Use contextmanager pattern (try/finally always runs). The track_request decorator in this code handles this correctly."},
        ],
        "production_checklist": [
            "Low-cardinality labels only.",
            "Latency p50/p95/p99 (not just average).",
            "Error rate by type (rate-limit, timeout, refusal, etc.).",
            "Cost per tenant + per model.",
            "Burn-rate alerts (multi-window) over raw thresholds.",
            "Runbook linked from each alert (what to do).",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["prometheus-client==0.20"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["prometheus", "grafana"],
        "related_glossary_slugs": ["sla", "slo"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What's a good LLM SLO?", "answer": "Depends on use case. Chat: p95 < 5s, error rate < 1%. Batch: p95 < 60s. Set conservatively first; tighten as you learn workload."},
            {"question": "Burn-rate alerting vs threshold?", "answer": "Threshold: 'error rate > 5%' fires every blip. Burn-rate: 'burning error budget faster than sustainable' fires only on real degradation. Burn-rate reduces alert fatigue."},
            {"question": "Tracing vs metrics?", "answer": "Both. Metrics: aggregates, dashboard, alerts. Traces: per-request detail, debugging. Use OpenLLMetry/Helicone for traces; this pattern for metrics."},
            {"question": "How many SLOs?", "answer": "3-5 max. Latency, error rate, availability cover most cases. Each extra SLO = more cognitive load + more alert noise."},
        ],
        "github_url": "https://github.com/prometheus/client_python",
        "meta_title": "LLM SLA Monitoring + Alerts Starter",
        "meta_description": "Production LLM SLA monitoring: latency, errors, cost via Prometheus. Burn-rate alerts. Multi-tenant labels.",
    },
    {
        "slug": "canary-deploy-prompt-changes",
        "title": "Canary Deploy For Prompt Changes",
        "tldr": "Roll out prompt changes gradually: 1% → 5% → 25% → 100%. Auto-pause if error rate or quality score regresses. Limits blast radius of bad prompts.",
        "category": "production",
        "language": "python",
        "framework": "Custom + Redis",
        "tags": ["canary", "deploy", "prompt", "production"],
        "best_for_tags": ["production-llm-app", "risk-management", "team-discipline"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Production LLM with measurable quality / error metrics. Canary lets you test new prompts on a slice of traffic with auto-revert if metrics regress.",
        "when_not_to_use": "Skip without an automated quality metric (canary needs auto-evaluable signal). Skip for very-low-traffic apps (canary stages need enough volume to be significant).",
        "quick_start": "pip install redis && python canary_deploy.py",
        "full_code": '''"""Canary deploy for prompt versions with auto-revert."""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime

import redis


redis_client = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))


# ----------------- CANARY CONFIG -----------------

CANARY_STAGES = [1, 5, 25, 100]  # % of traffic
STAGE_DURATION_SECONDS = 600     # 10 min per stage (typical: 1-24 hours)
ERROR_RATE_THRESHOLD = 0.05      # 5% error rate → revert
QUALITY_REGRESSION_THRESHOLD = 0.05  # 5pp quality drop → revert


@dataclass
class CanaryStatus:
    prompt_name: str
    candidate_version: int
    baseline_version: int
    current_pct: int            # current stage
    stage_started_at: int
    state: str                  # "rolling" | "paused" | "promoted" | "reverted"


# ----------------- ROUTING -----------------

def route_request(prompt_name: str, user_id: str) -> int:
    """Return version to use for this request."""
    status_raw = redis_client.get(f"canary:status:{prompt_name}")
    if not status_raw:
        return _get_stable_version(prompt_name)

    status = CanaryStatus(**json.loads(status_raw))
    if status.state != "rolling":
        return _get_stable_version(prompt_name)

    # Sticky routing: same user → same version
    bucket = int(hashlib.sha256(user_id.encode()).hexdigest()[:8], 16) % 100
    return status.candidate_version if bucket < status.current_pct else status.baseline_version


def _get_stable_version(prompt_name: str) -> int:
    return int(redis_client.get(f"prompt:active:{prompt_name}") or 1)


# ----------------- METRICS PER VERSION -----------------

def record_outcome(prompt_name: str, version: int, success: bool, quality_score: float):
    """Track per-version outcomes for canary decision."""
    today = datetime.utcnow().strftime("%Y-%m-%d-%H")  # hourly buckets
    key_base = f"canary:metrics:{prompt_name}:{version}:{today}"
    pipe = redis_client.pipeline()
    pipe.incr(f"{key_base}:total")
    if not success:
        pipe.incr(f"{key_base}:errors")
    pipe.incrbyfloat(f"{key_base}:quality_sum", quality_score)
    for k in [f"{key_base}:total", f"{key_base}:errors", f"{key_base}:quality_sum"]:
        pipe.expire(k, 86400)
    pipe.execute()


def get_metrics(prompt_name: str, version: int, hours: int = 1) -> dict:
    """Aggregate last N hours."""
    total = errors = 0
    quality_sum = 0.0
    for h in range(hours):
        bucket = (datetime.utcnow().timestamp() // 3600 - h) * 3600
        ts = datetime.utcfromtimestamp(bucket).strftime("%Y-%m-%d-%H")
        key_base = f"canary:metrics:{prompt_name}:{version}:{ts}"
        total += int(redis_client.get(f"{key_base}:total") or 0)
        errors += int(redis_client.get(f"{key_base}:errors") or 0)
        quality_sum += float(redis_client.get(f"{key_base}:quality_sum") or 0)
    return {
        "total": total,
        "error_rate": errors / total if total else 0,
        "avg_quality": quality_sum / total if total else 0,
    }


# ----------------- AUTO-PROMOTE / REVERT -----------------

def evaluate_canary(prompt_name: str) -> str:
    """Decide: promote / pause / revert. Called every minute."""
    status_raw = redis_client.get(f"canary:status:{prompt_name}")
    if not status_raw:
        return "no_canary"
    status = CanaryStatus(**json.loads(status_raw))

    if status.state != "rolling":
        return status.state

    cand = get_metrics(prompt_name, status.candidate_version)
    base = get_metrics(prompt_name, status.baseline_version)

    # Need enough volume to decide
    if cand["total"] < 30:
        return "rolling"

    # Auto-revert checks
    if cand["error_rate"] > ERROR_RATE_THRESHOLD:
        _set_state(status, "reverted")
        alert(f"REVERTED {prompt_name} v{status.candidate_version}: error rate {cand['error_rate']:.1%}")
        return "reverted"
    if base["avg_quality"] - cand["avg_quality"] > QUALITY_REGRESSION_THRESHOLD:
        _set_state(status, "reverted")
        alert(f"REVERTED {prompt_name} v{status.candidate_version}: quality regression")
        return "reverted"

    # Auto-promote if stage duration elapsed
    if time.time() - status.stage_started_at > STAGE_DURATION_SECONDS:
        next_pct = next((p for p in CANARY_STAGES if p > status.current_pct), None)
        if next_pct is None:
            # Final stage cleared — promote to stable
            redis_client.set(f"prompt:active:{prompt_name}", status.candidate_version)
            _set_state(status, "promoted")
            alert(f"PROMOTED {prompt_name} v{status.candidate_version}")
            return "promoted"
        status.current_pct = next_pct
        status.stage_started_at = int(time.time())
        redis_client.set(f"canary:status:{prompt_name}", json.dumps(status.__dict__))
        alert(f"ADVANCED {prompt_name} v{status.candidate_version} to {next_pct}%")

    return "rolling"


def _set_state(status: CanaryStatus, state: str):
    status.state = state
    redis_client.set(f"canary:status:{status.prompt_name}", json.dumps(status.__dict__))


def alert(msg: str):
    print(f"[CANARY ALERT] {msg}")


# ----------------- START CANARY -----------------

def start_canary(prompt_name: str, candidate_version: int):
    baseline = _get_stable_version(prompt_name)
    status = CanaryStatus(
        prompt_name=prompt_name,
        candidate_version=candidate_version,
        baseline_version=baseline,
        current_pct=CANARY_STAGES[0],
        stage_started_at=int(time.time()),
        state="rolling",
    )
    redis_client.set(f"canary:status:{prompt_name}", json.dumps(status.__dict__))
    print(f"Started canary {prompt_name}: v{baseline} → v{candidate_version} (start at {CANARY_STAGES[0]}%)")


if __name__ == "__main__":
    start_canary("classify", candidate_version=2)
    # In production: cronjob calls evaluate_canary every minute
    while True:
        state = evaluate_canary("classify")
        if state in ("promoted", "reverted"):
            print(f"Final state: {state}")
            break
        time.sleep(60)
''',
        "dependencies": [
            {"name": "redis", "version": ">=5.0", "purpose": "Canary state + metrics"},
        ],
        "env_vars": [
            {"name": "REDIS_URL", "required": True, "description": "Redis", "example": "redis://localhost:6379"},
        ],
        "setup_steps": [
            "pip install redis",
            "Wire route_request() into your LLM call sites",
            "Wire record_outcome() to capture success + quality post-LLM",
            "Schedule evaluate_canary() every minute (cron / k8s CronJob)",
            "Set up alert() to Slack / PagerDuty",
        ],
        "variations": [
            {"label": "Bayesian decision", "description": "Statistical confidence in promotion.", "code_snippet": "# Replace threshold check with Bayesian A/B test. Promote when P(candidate > baseline) > 0.95. More robust."},
            {"label": "Manual gates between stages", "description": "Human approval at each stage.", "code_snippet": "# Add 'paused' state at each stage; require manual API call to advance. Slower but safer."},
            {"label": "Multi-metric SLOs", "description": "Beyond error rate + quality.", "code_snippet": "# Include latency, cost, user-satisfaction in decision matrix. Weight each by importance."},
        ],
        "common_errors": [
            {"error_text": "Canary 'works' but quality score is uninformative", "cause": "Auto-quality score doesn't reflect user value.", "fix_snippet": "Use multiple signals: LLM judge + thumbs-up rate + downstream conversion. Single signal is brittle."},
            {"error_text": "Volume too low to decide", "cause": "Small app, first stage takes hours to get N=30.", "fix_snippet": "Lower MIN_SAMPLES or increase first-stage % (e.g., start at 10% instead of 1%). Tradeoff: blast radius."},
            {"error_text": "Reverts too aggressive", "cause": "Threshold too tight.", "fix_snippet": "Use confidence intervals. Don't revert on noisy signal. Require 3-5 consecutive evaluations showing regression."},
            {"error_text": "Canary state inconsistent across replicas", "cause": "Local caching beats Redis.", "fix_snippet": "Don't cache canary state locally (or cache with very short TTL). Read from Redis on each request."},
        ],
        "production_checklist": [
            "Use sticky routing (hash user_id) — same user, same version.",
            "Minimum volume per stage before deciding.",
            "Auto-revert on error spike OR quality regression.",
            "Alert team on every state change.",
            "Audit log: who started canary, when, decisions made.",
            "Manual override: stop / force-promote / force-revert.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["redis==5.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["redis"],
        "related_glossary_slugs": ["canary-deployment", "feature-flag"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How long to keep each stage?", "answer": "Depends on volume + risk. Chat apps: 30 min - 2 hours per stage. Batch jobs: longer. Use enough volume that metrics are stable (~1000 samples per arm minimum)."},
            {"question": "When auto-revert vs alert humans?", "answer": "Auto-revert for CLEAR signals (error rate 2x baseline). Alert + wait for SUBTLE signals (small quality drift). Tune by team comfort."},
            {"question": "Canary vs A/B test?", "answer": "Canary: rolling deploy with safety. A/B: extended experiment for decision-making. Canary's goal is safe rollout; A/B's is which-is-better."},
            {"question": "Multiple concurrent canaries?", "answer": "Possible but tricky — different prompts can interact. Better: serialize canaries per service. Run multiple in parallel only if FULLY independent."},
        ],
        "github_url": "",
        "meta_title": "Canary Deploy For Prompt Changes Starter",
        "meta_description": "Canary deploy LLM prompt changes: gradual % rollout, auto-revert on error/quality regression, sticky routing, audit log.",
    },
]
