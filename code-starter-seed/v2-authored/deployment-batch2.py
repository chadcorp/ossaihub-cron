"""Deployment starters — batch 2: Vercel, FastAPI, K8s."""

RECORDS = [
    {
        "slug": "fastapi-streaming-llm-service",
        "title": "FastAPI Streaming LLM Service With Auth + Rate Limit",
        "tldr": "Production FastAPI service for LLM streaming: bearer auth, per-user rate limit (slowapi), SSE-compatible streaming, health endpoints, structured logging. Deploy-ready.",
        "category": "deployment",
        "language": "python",
        "framework": "FastAPI",
        "tags": ["fastapi", "streaming", "auth", "rate-limit", "production"],
        "best_for_tags": ["api-services", "saas-backend", "production-llm"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Building a public-facing or internal API that proxies LLM calls. Pattern handles the common production needs: auth, rate limiting, streaming, observability — without inventing them.",
        "when_not_to_use": "Skip for simple proof-of-concepts (use a serverless function). Skip when you want managed infrastructure (Vercel AI SDK + Edge functions).",
        "quick_start": "pip install fastapi uvicorn[standard] slowapi openai && uvicorn app:app --reload",
        "full_code": '''"""FastAPI LLM streaming service.

Routes:
  POST /chat   — streaming chat completion (SSE)
  GET  /healthz — liveness
  GET  /readyz  — readiness (verifies OpenAI is reachable)
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import AsyncIterator

import openai
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logging.basicConfig(level="INFO", format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')
log = logging.getLogger("llm-svc")

VALID_TOKENS = set(os.environ.get("VALID_TOKENS", "").split(","))  # comma-separated
client = openai.AsyncOpenAI()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="LLM Service")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ----------------- AUTH -----------------

async def require_token(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if VALID_TOKENS and token not in VALID_TOKENS:
        raise HTTPException(401, "invalid token")
    return token


# ----------------- STREAMING CHAT -----------------

async def event_stream(prompt: str, user_token: str) -> AsyncIterator[str]:
    start = time.time()
    tokens_streamed = 0
    try:
        stream = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                tokens_streamed += 1
                yield f"data: {json.dumps({'delta': content})}\\n\\n"
        yield "data: [DONE]\\n\\n"
    except Exception as e:
        log.error(f"stream error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\\n\\n"
    finally:
        log.info(f"stream done; user={user_token[:8]} tokens={tokens_streamed} duration_ms={int((time.time()-start)*1000)}")


@app.post("/chat")
@limiter.limit("30/minute")
async def chat(request: Request, body: dict, token: str = Depends(require_token)):
    prompt = body.get("prompt") or body.get("message")
    if not prompt:
        raise HTTPException(400, "missing prompt")
    if len(prompt) > 8000:
        raise HTTPException(400, "prompt too long (max 8000 chars)")
    return StreamingResponse(event_stream(prompt, token), media_type="text/event-stream")


# ----------------- HEALTH -----------------

@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.get("/readyz")
async def readyz():
    try:
        await client.models.list()  # cheap call to verify
        return {"ok": True}
    except Exception as e:
        raise HTTPException(503, f"upstream unhealthy: {e}")
''',
        "dependencies": [
            {"name": "fastapi", "version": ">=0.115", "purpose": "Web framework"},
            {"name": "uvicorn[standard]", "version": ">=0.32", "purpose": "ASGI server"},
            {"name": "slowapi", "version": ">=0.1", "purpose": "Rate limiting"},
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
            {"name": "VALID_TOKENS", "required": True, "description": "Comma-separated bearer tokens for clients", "example": "tok1,tok2,tok3"},
        ],
        "setup_steps": [
            "pip install fastapi uvicorn[standard] slowapi openai",
            "export OPENAI_API_KEY=sk-... VALID_TOKENS=tok1,tok2",
            "uvicorn app:app --reload",
            "curl -X POST http://localhost:8000/chat -H 'Authorization: Bearer tok1' -d '{\"prompt\":\"hi\"}'",
        ],
        "variations": [
            {"label": "Per-user rate limit", "description": "Limit by token, not IP.", "code_snippet": "limiter = Limiter(key_func=lambda req: req.headers.get('authorization', 'anon'))"},
            {"label": "Redis-backed limit", "description": "Shared across multiple instances.", "code_snippet": "limiter = Limiter(key_func=..., storage_uri='redis://localhost:6379')"},
            {"label": "WebSocket variant", "description": "Stream over WebSocket.", "code_snippet": "@app.websocket('/chat-ws')\\nasync def chat_ws(ws: WebSocket): await ws.accept(); ..."},
            {"label": "OpenTelemetry instrumentation", "description": "Auto-trace requests.", "code_snippet": "from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor\\nFastAPIInstrumentor.instrument_app(app)"},
        ],
        "common_errors": [
            {"error_text": "EventStream cut off at proxy", "cause": "Reverse proxy buffering.", "fix_snippet": "Nginx: proxy_buffering off; proxy_read_timeout 86400; Caddy: similar. Most cloud LBs (ALB) need extra config for SSE."},
            {"error_text": "RateLimitExceeded JSON malformed", "cause": "Default slowapi response is text.", "fix_snippet": "Wrap with custom exception handler that returns JSON: {error: 'rate_limit', retry_after: ...}."},
            {"error_text": "Memory grows on long-running server", "cause": "Open connections not closed properly.", "fix_snippet": "Ensure event_stream's try/finally covers all paths. Test by killing client mid-stream; server should clean up."},
            {"error_text": "All clients getting 401", "cause": "VALID_TOKENS env empty or wrong format.", "fix_snippet": "Verify VALID_TOKENS is set; format is comma-separated. Or temporarily disable auth check to test other code."},
        ],
        "production_checklist": [
            "Run behind a reverse proxy with TLS (Caddy / Nginx / cloud LB).",
            "Configure proxy for SSE (disable buffering, long timeouts).",
            "Store auth tokens in a secret manager, not env directly in shared environments.",
            "Set per-token rate limits, not just IP (IPs can be shared NATs).",
            "Log structured JSON (starter does this); pipe to your log backend.",
            "Healthz vs readyz: liveness probes hit healthz; readiness hits readyz.",
            "Use uvicorn workers + gunicorn for horizontal scaling.",
            "Test under load: streaming connections hold resources; cap concurrent connections.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["fastapi==0.115.0", "uvicorn==0.32.0", "slowapi==0.1.9", "openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["fastapi"],
        "related_glossary_slugs": ["sse", "rate-limiting", "bearer-auth"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "SSE vs WebSocket?", "answer": "SSE for one-way server-to-client streaming (which chat usually is). WebSocket for bidirectional. SSE is simpler and works through more proxies."},
            {"question": "Why slowapi vs starlette-rate-limiter?", "answer": "slowapi is the standard FastAPI rate limiter; well-maintained, drop-in. Other options exist; slowapi is the simplest first choice."},
            {"question": "Can this run in serverless?", "answer": "Streaming in Lambda is supported but tricky (response streaming limits). Easier on Vercel Edge or Cloud Run. The starter assumes long-running container."},
        ],
        "github_url": "",
        "meta_title": "FastAPI Streaming LLM Service — Starter",
        "meta_description": "Production FastAPI: bearer auth, slowapi rate limit, SSE streaming, structured logs, health/ready endpoints. Deploy-ready.",
    },
    {
        "slug": "kubernetes-llm-service-manifest",
        "title": "Kubernetes LLM Service Manifest",
        "tldr": "Kubernetes Deployment + Service + HPA for an LLM-backed FastAPI service. Includes resource requests/limits, GPU node selector hint, secrets via External Secrets reference, and graceful shutdown.",
        "category": "deployment",
        "language": "yaml",
        "framework": "Kubernetes",
        "tags": ["kubernetes", "deployment", "hpa", "gpu"],
        "best_for_tags": ["self-hosted", "kubernetes", "production"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "When deploying a containerized LLM service to a Kubernetes cluster — your own or a managed one (EKS / GKE / AKS). The starter has the production hygiene defaults.",
        "when_not_to_use": "Skip for serverless-first stacks (Modal, Vercel, Cloud Run). Skip when your team doesn't run Kubernetes — the operational overhead is real.",
        "quick_start": "kubectl apply -f deployment.yaml",
        "full_code": '''# deployment.yaml — production LLM service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-svc
  labels: { app: llm-svc, env: prod }
spec:
  replicas: 2
  selector:
    matchLabels: { app: llm-svc }
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0       # zero-downtime rolls
      maxSurge: 1
  template:
    metadata:
      labels: { app: llm-svc, env: prod }
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
    spec:
      terminationGracePeriodSeconds: 60   # let in-flight streams finish
      containers:
        - name: app
          image: ghcr.io/yourorg/llm-svc:v1.4.2   # pinned digest in prod
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
              name: http
          env:
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef: { name: llm-svc-secrets, key: openai-key }
            - name: VALID_TOKENS
              valueFrom:
                secretKeyRef: { name: llm-svc-secrets, key: bearer-tokens }
          resources:
            requests: { cpu: "500m", memory: "512Mi" }
            limits:   { cpu: "2",    memory: "2Gi" }
          startupProbe:
            httpGet: { path: /healthz, port: http }
            failureThreshold: 30
            periodSeconds: 2
          readinessProbe:
            httpGet: { path: /readyz, port: http }
            periodSeconds: 10
          livenessProbe:
            httpGet: { path: /healthz, port: http }
            periodSeconds: 30
            failureThreshold: 3
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 15"]   # let LB drain
---
apiVersion: v1
kind: Service
metadata:
  name: llm-svc
spec:
  type: ClusterIP
  selector: { app: llm-svc }
  ports:
    - port: 80
      targetPort: 8000
      name: http
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-svc
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-svc
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 70 }
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300       # avoid flapping
---
# For GPU workloads — uncomment + tune
# spec.template.spec:
#   nodeSelector:
#     accelerator: nvidia-a10g
#   tolerations:
#     - key: nvidia.com/gpu
#       operator: Exists
#   containers:
#     - resources:
#         limits:
#           nvidia.com/gpu: 1
''',
        "dependencies": [
            {"name": "kubectl", "version": ">=1.28", "purpose": "Kubernetes CLI"},
            {"name": "metrics-server", "version": ">=0.7", "purpose": "Required for HPA"},
        ],
        "env_vars": [],
        "setup_steps": [
            "Build + push the Docker image (see dockerfile-llm-fastapi-prod starter).",
            "Create the secret: kubectl create secret generic llm-svc-secrets --from-literal=openai-key=sk-... --from-literal=bearer-tokens=tok1,tok2",
            "kubectl apply -f deployment.yaml",
            "kubectl get pods -w  # watch rollout",
            "kubectl port-forward svc/llm-svc 8080:80  # test locally",
        ],
        "variations": [
            {"label": "External Secrets (Vault/AWS Secrets Manager)", "description": "Don't store secrets in K8s.", "code_snippet": "# Use ExternalSecret resource pointing at Vault / Secrets Manager. Secret is synced into K8s for the pod to consume."},
            {"label": "GPU node pool", "description": "For self-hosted LLMs.", "code_snippet": "# Add nodeSelector + tolerations + nvidia.com/gpu limit (commented in main YAML)"},
            {"label": "VPA for sizing", "description": "Vertical Pod Autoscaler.", "code_snippet": "# Install VPA; add VerticalPodAutoscaler resource targeting this deployment.\\n# Use 'Off' mode initially; tune from VPA's recommendations."},
            {"label": "PodDisruptionBudget", "description": "Protect during cluster maintenance.", "code_snippet": "apiVersion: policy/v1\\nkind: PodDisruptionBudget\\nspec:\\n  minAvailable: 1\\n  selector: { matchLabels: { app: llm-svc } }"},
        ],
        "common_errors": [
            {"error_text": "Pod stuck in CrashLoopBackOff", "cause": "App crashes on startup.", "fix_snippet": "kubectl logs pod/...  Check missing env vars or unreachable upstream. Often: secret not created."},
            {"error_text": "HPA not scaling", "cause": "metrics-server not installed or pod resources not defined.", "fix_snippet": "kubectl get apiservices | grep metrics  → must show True. Verify resources.requests is set on the container."},
            {"error_text": "Rolling update drops requests", "cause": "maxUnavailable too aggressive or graceful shutdown not honored.", "fix_snippet": "Set maxUnavailable: 0. Add preStop hook (starter has it). Implement signal handling in your app (uvicorn handles SIGTERM)."},
            {"error_text": "Streams cut at 60s", "cause": "Default load-balancer timeout.", "fix_snippet": "Configure ingress/LB for long timeouts. AWS ALB: idle_timeout=3600. GCP: backend service timeout."},
        ],
        "production_checklist": [
            "Pin image to digest (sha256:...), not tag.",
            "Set resource requests/limits — don't run without.",
            "Ingress with TLS termination.",
            "PodDisruptionBudget set.",
            "Secrets via External Secrets, not raw kubectl create secret.",
            "Network policies limiting pod-to-pod traffic.",
            "Monitor: kube-state-metrics + Prometheus.",
            "Backup: not critical for stateless service; ensure secrets are reproducible.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["kubernetes==1.30+"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["kubernetes", "hpa", "deployment-strategy"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why preStop sleep 15?", "answer": "When pod is terminated, K8s removes it from Service endpoints AND sends SIGTERM. The sleep gives the load balancer time to drain before the app shuts down — avoids dropped requests."},
            {"question": "HPA on CPU enough?", "answer": "For most LLM proxies (I/O bound), CPU works. For embedding or local inference services, use custom metrics (queue depth, GPU utilization)."},
            {"question": "GPU scheduling?", "answer": "Install nvidia device plugin; use nodeSelector and nvidia.com/gpu limit. GPU nodes are expensive — use taints + tolerations to reserve them."},
        ],
        "github_url": "",
        "meta_title": "Kubernetes LLM Service Manifest — Starter",
        "meta_description": "Production K8s manifest for LLM-backed service: Deployment, Service, HPA, startup/ready/liveness probes, graceful shutdown, secrets ref.",
    },
]
