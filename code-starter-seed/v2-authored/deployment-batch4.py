"""Deployment starters — batch 4: Kubernetes, BentoML, Fly.io, HuggingFace Spaces."""

RECORDS = [
    {
        "slug": "kubernetes-vllm-deployment",
        "title": "Kubernetes vLLM Deployment With HPA",
        "tldr": "Production K8s deployment for vLLM: GPU node pool, HorizontalPodAutoscaler on GPU utilization, PVC for model weights, readiness probes. The 'serious' self-hosted LLM stack.",
        "category": "deployment",
        "language": "yaml",
        "framework": "Kubernetes",
        "tags": ["kubernetes", "vllm", "hpa", "production"],
        "best_for_tags": ["production-scale", "self-hosted", "enterprise"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Production LLM service expected to run 24/7 with auto-scaling. Kubernetes + vLLM + HPA gives reliable scale-up/down. Best when you already operate K8s clusters.",
        "when_not_to_use": "Skip for prototypes (Modal / Cloud Run is faster). Skip without K8s expertise (operational complexity outweighs benefits at small scale).",
        "quick_start": "kubectl apply -f vllm-deployment.yaml",
        "full_code": '''# Kubernetes manifests for vLLM with autoscaling
# Save as vllm-deployment.yaml

# ----------------- NAMESPACE -----------------
apiVersion: v1
kind: Namespace
metadata:
  name: llm-serving

---
# ----------------- SECRET (HF token) -----------------
apiVersion: v1
kind: Secret
metadata:
  name: hf-token
  namespace: llm-serving
type: Opaque
stringData:
  token: "REPLACE_WITH_HF_TOKEN"

---
# ----------------- PVC (model weights cache) -----------------
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-cache
  namespace: llm-serving
spec:
  accessModes: [ReadWriteMany]
  resources:
    requests:
      storage: 200Gi
  storageClassName: efs-sc          # use ReadWriteMany-capable SC

---
# ----------------- DEPLOYMENT -----------------
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-llama-8b
  namespace: llm-serving
spec:
  replicas: 2                       # min instances
  selector:
    matchLabels: {app: vllm-llama-8b}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0             # zero downtime
  template:
    metadata:
      labels: {app: vllm-llama-8b}
    spec:
      nodeSelector:
        node.kubernetes.io/instance-type: g5.xlarge   # A10G GPU
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
      containers:
        - name: vllm
          image: vllm/vllm-openai:v0.6.3
          imagePullPolicy: IfNotPresent
          args:
            - "--model"
            - "meta-llama/Llama-3.1-8B-Instruct"
            - "--port"
            - "8000"
            - "--max-model-len"
            - "8192"
            - "--gpu-memory-utilization"
            - "0.90"
            - "--enable-prefix-caching"
          env:
            - name: HUGGING_FACE_HUB_TOKEN
              valueFrom:
                secretKeyRef: {name: hf-token, key: token}
            - name: HF_HOME
              value: /cache
          ports:
            - containerPort: 8000
              name: http
          resources:
            requests:
              memory: 16Gi
              cpu: "4"
              nvidia.com/gpu: 1
            limits:
              memory: 32Gi
              nvidia.com/gpu: 1
          volumeMounts:
            - name: model-cache
              mountPath: /cache
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 120  # vLLM cold-start
            periodSeconds: 10
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 180
            periodSeconds: 30
            failureThreshold: 5
          lifecycle:
            preStop:
              exec:
                command: ["sleep", "30"]   # graceful drain
      terminationGracePeriodSeconds: 60
      volumes:
        - name: model-cache
          persistentVolumeClaim:
            claimName: model-cache

---
# ----------------- SERVICE -----------------
apiVersion: v1
kind: Service
metadata:
  name: vllm-llama-8b
  namespace: llm-serving
spec:
  type: ClusterIP
  selector: {app: vllm-llama-8b}
  ports:
    - port: 80
      targetPort: 8000

---
# ----------------- HPA (autoscale on GPU utilization via custom metric) -----------------
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm-llama-8b
  namespace: llm-serving
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm-llama-8b
  minReplicas: 2
  maxReplicas: 10
  metrics:
    # Scale on queue depth (custom metric from vLLM /metrics)
    - type: Pods
      pods:
        metric:
          name: vllm_num_requests_running
        target:
          type: AverageValue
          averageValue: "10"        # scale up if avg > 10 in-flight per pod
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies: [{type: Percent, value: 100, periodSeconds: 60}]
    scaleDown:
      stabilizationWindowSeconds: 300
      policies: [{type: Percent, value: 50, periodSeconds: 60}]

---
# ----------------- INGRESS (with rate limiting) -----------------
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vllm-llama-8b
  namespace: llm-serving
  annotations:
    nginx.ingress.kubernetes.io/proxy-buffering: "off"   # streaming
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/limit-rps: "100"
spec:
  ingressClassName: nginx
  tls:
    - hosts: [llm.example.com]
      secretName: llm-tls
  rules:
    - host: llm.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: vllm-llama-8b
                port:
                  number: 80
''',
        "dependencies": [],
        "env_vars": [
            {"name": "HF_TOKEN", "required": True, "description": "Stored in K8s Secret", "example": "hf_..."},
        ],
        "setup_steps": [
            "Provision K8s cluster with GPU node pool (EKS / GKE / AKS)",
            "Install NVIDIA device plugin, cert-manager, nginx-ingress",
            "Replace HF token in vllm-deployment.yaml",
            "kubectl apply -f vllm-deployment.yaml",
            "Wait for pods Ready; test via ingress",
            "Set up prometheus-adapter for custom metrics (HPA needs it)",
        ],
        "variations": [
            {"label": "KEDA for queue-based scaling", "description": "Scale on external queue depth.", "code_snippet": "# Install KEDA; ScaledObject pointing at SQS/Redis queue. Scale to zero when no traffic."},
            {"label": "GKE Autopilot", "description": "GCP managed K8s, less ops.", "code_snippet": "# Autopilot handles node pools automatically; specify GPU type via nodeSelector + tolerations as usual"},
            {"label": "Kustomize overlay per env", "description": "Dev/staging/prod with shared base.", "code_snippet": "# base/, overlays/dev/, overlays/prod/ with kustomization.yaml. Patch replicas + resources per env."},
        ],
        "common_errors": [
            {"error_text": "Pod stuck in ImagePullBackOff", "cause": "vLLM image too large or registry slow.", "fix_snippet": "Pre-pull on nodes via DaemonSet or use a local mirror. vLLM images are ~10GB."},
            {"error_text": "HPA not scaling", "cause": "Custom metric not exposed.", "fix_snippet": "Install prometheus-adapter; verify metric available via 'kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/'. Without it, HPA can only use CPU/memory."},
            {"error_text": "Pod kills before request completes", "cause": "No graceful drain.", "fix_snippet": "Add preStop sleep + terminationGracePeriodSeconds. Set drain logic in vLLM (it supports graceful shutdown via SIGTERM)."},
            {"error_text": "Model download per pod (slow + bandwidth)", "cause": "No shared PVC.", "fix_snippet": "Use ReadWriteMany PVC (EFS, GCS Fuse, Azure Files). All pods share the cache; first pod downloads, rest read from cache."},
        ],
        "production_checklist": [
            "Shared PVC for model weights (avoid re-download per pod).",
            "Readiness probe respects vLLM warm-up (~2 min for 8B).",
            "PreStop drain so in-flight requests finish.",
            "Custom metric scaling (queue depth) not just CPU/memory.",
            "Ingress with proxy buffering OFF for streaming.",
            "Resource limits + Pod Disruption Budget.",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-8B-Instruct"],
            "library_versions": ["vllm 0.6.3", "Kubernetes 1.30"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["kubernetes", "vllm"],
        "related_glossary_slugs": ["kubernetes", "horizontal-pod-autoscaler"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "K8s vs Modal vs Cloud Run for LLMs?", "answer": "K8s: full control, cluster-level ops. Modal/Cloud Run: managed, less control. K8s pays off above ~$5k/mo in spend or with existing K8s expertise."},
            {"question": "Scale-to-zero on K8s?", "answer": "Vanilla HPA: no. Use KEDA for scale-to-zero. Or Cluster Autoscaler to decommission GPU nodes when no pods need them."},
            {"question": "Cost vs Cloud Run / Modal?", "answer": "K8s: $0.30/hr per A10G ($220/mo per always-on pod). Modal: pay-per-second of usage. K8s cheaper for steady high traffic; serverless for spiky."},
            {"question": "GPU sharing?", "answer": "MIG (NVIDIA Multi-Instance GPU) lets one A100/H100 host multiple smaller pods. Good for many small models. Configure via NVIDIA device plugin."},
        ],
        "github_url": "https://github.com/kubernetes/kubernetes",
        "meta_title": "Kubernetes vLLM Deployment Starter",
        "meta_description": "Production K8s for vLLM: HPA, shared PVC, readiness/liveness probes, graceful drain, ingress with streaming support.",
    },
    {
        "slug": "bentoml-model-serving",
        "title": "BentoML LLM Model Serving",
        "tldr": "BentoML: package model + code into a 'Bento', deploy locally / Docker / K8s / BentoCloud. Python-first; abstracts ops. Good for ML teams without devops.",
        "category": "deployment",
        "language": "python",
        "framework": "BentoML",
        "tags": ["bentoml", "model-serving", "deployment", "packaging"],
        "best_for_tags": ["ml-teams", "python-first", "model-zoo"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "ML team without dedicated devops, packaging multiple model variants. BentoML abstracts Docker / K8s; you write Python services. Deploy anywhere.",
        "when_not_to_use": "Skip if you have devops team + standard K8s patterns (vLLM directly is simpler). Skip for ultra-high QPS — BentoML adds Python overhead.",
        "quick_start": "pip install bentoml && bentoml deploy ./service.py",
        "full_code": '''"""BentoML LLM service: package + serve."""
from __future__ import annotations

import os
from typing import AsyncGenerator
import bentoml
from openai import AsyncOpenAI


# ----------------- SERVICE -----------------

@bentoml.service(
    name="llm-service",
    resources={"cpu": "2", "memory": "4Gi"},
    traffic={"timeout": 300, "concurrency": 16},
)
class LLMService:
    def __init__(self):
        # Initialize once per worker
        self.client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    @bentoml.api
    async def chat(self, prompt: str, model: str = "gpt-4o-mini",
                   max_tokens: int = 512) -> dict:
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return {
            "response": response.choices[0].message.content,
            "tokens": response.usage.completion_tokens,
        }

    @bentoml.api
    async def stream(self, prompt: str, model: str = "gpt-4o-mini") -> AsyncGenerator[str, None]:
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=512,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


# ----------------- SERVE LOCALLY -----------------

# bentoml serve service:LLMService --port 3000

# ----------------- BUILD A BENTO (deployable artifact) -----------------

BENTOFILE = """
# bentofile.yaml
service: "service:LLMService"
labels:
  team: ml-platform
include:
  - "*.py"
python:
  packages:
    - openai>=1.40
    - pydantic>=2.0
"""


# ----------------- DEPLOY TARGETS -----------------

# 1. Local:           bentoml serve service:LLMService
# 2. Containerize:    bentoml containerize llm-service:latest
# 3. BentoCloud:      bentoml deploy llm-service --cluster aws-prod
# 4. Kubernetes:      bentoml yatai-deployment-controller (yatai operator)


# ----------------- CLIENT -----------------

CLIENT = """
# Programmatic client (BentoML generates one)
from bentoml.client import SyncHTTPClient
client = SyncHTTPClient('http://localhost:3000')
result = client.chat(prompt='Hello, world!')
print(result)
"""
''',
        "dependencies": [
            {"name": "bentoml", "version": ">=1.3", "purpose": "BentoML framework"},
            {"name": "openai", "version": ">=1.40", "purpose": "LLM client (could be any)"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "If proxying OpenAI", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install bentoml openai",
            "Save service.py",
            "Test locally: bentoml serve service:LLMService",
            "Build: bentoml build (creates a Bento artifact)",
            "Deploy: bentoml containerize OR bentoml deploy to BentoCloud",
        ],
        "variations": [
            {"label": "Local model serving (transformers)", "description": "Wrap a local model.", "code_snippet": "@bentoml.service\\nclass LocalLLM:\\n    def __init__(self):\\n        from transformers import pipeline\\n        self.pipe = pipeline('text-generation', model='gpt2')\\n    @bentoml.api\\n    def gen(self, prompt: str) -> str: return self.pipe(prompt)[0]['generated_text']"},
            {"label": "Multi-model service", "description": "Multiple endpoints, different models.", "code_snippet": "@bentoml.service\\nclass MultiLLM:\\n    @bentoml.api\\n    def gpt4(self, ...): ...\\n    @bentoml.api\\n    def haiku(self, ...): ..."},
            {"label": "vLLM in BentoML", "description": "Wrap vLLM with BentoML for managed ops.", "code_snippet": "# bentoml-vllm extension: @bentoml.service with vLLM AsyncEngine inside __init__"},
        ],
        "common_errors": [
            {"error_text": "Slow worker startup", "cause": "Model load in __init__.", "fix_snippet": "Initialize model in __init__ — runs once per worker, not per request. Use @bentoml.service(workers=N) to parallelize cold starts."},
            {"error_text": "Memory leaks over time", "cause": "Async loop accumulating tasks.", "fix_snippet": "Ensure async generators close properly. Use bentoml's built-in lifespan hooks for cleanup."},
            {"error_text": "Container too large", "cause": "Including dev deps.", "fix_snippet": "Use docker_options.distro slim. Pin python.packages tightly. Exclude .pyc, __pycache__, tests."},
            {"error_text": "BentoCloud auth fails", "cause": "Token not set.", "fix_snippet": "bentoml cloud login; verify with bentoml cloud current-user. Pin SDK version matching BentoCloud server."},
        ],
        "production_checklist": [
            "Use async APIs for I/O-bound services.",
            "Set workers based on CPU + model load time.",
            "Define resources= so K8s can right-size.",
            "Set traffic.concurrency to control per-pod parallelism.",
            "Use BentoCloud or Yatai for managed K8s deploy.",
            "Monitor: BentoML exposes Prometheus metrics by default.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["bentoml==1.3"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["bentoml"],
        "related_glossary_slugs": ["model-serving", "bento"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "BentoML vs vLLM directly?", "answer": "vLLM: high-throughput inference server. BentoML: model serving framework (can wrap vLLM). Use BentoML when packaging matters; vLLM directly when raw throughput matters."},
            {"question": "BentoCloud vs self-host?", "answer": "BentoCloud: managed, pay-per-use, fast deploys. Self-host (K8s via Yatai): more control, cheaper at scale. Pick by ops capacity."},
            {"question": "Vs FastAPI / Flask?", "answer": "BentoML adds: model packaging, build-once-deploy-anywhere, model registry. FastAPI: just the web framework. BentoML is FastAPI + ML lifecycle tools."},
            {"question": "Multi-model serving?", "answer": "Yes — multiple @bentoml.api methods on one service, OR multiple services in one Bento. Helpful for serving classifier + LLM together."},
        ],
        "github_url": "https://github.com/bentoml/BentoML",
        "meta_title": "BentoML LLM Model Serving Starter",
        "meta_description": "BentoML: Python-first model serving framework. Package as Bento, deploy locally / Docker / K8s / BentoCloud. Async-native.",
    },
    {
        "slug": "fly-io-llm-edge-deployment",
        "title": "Fly.io Edge LLM Deployment",
        "tldr": "Fly.io: deploy your LLM app to 30+ regions with one config. Anycast routing puts users on the nearest edge. Good for global apps where latency-to-LLM-API is a factor.",
        "category": "deployment",
        "language": "bash",
        "framework": "Fly.io",
        "tags": ["fly-io", "edge", "global", "deployment"],
        "best_for_tags": ["global-apps", "low-latency", "indie-developers"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Globally-distributed users + LLM SaaS proxy. Fly's edge presence makes the proxy fast everywhere; the underlying LLM API call goes to the nearest provider region.",
        "when_not_to_use": "Skip for single-region apps (Railway/Render are simpler). Skip for self-hosted LLMs (Fly has limited GPU support; not designed for it).",
        "quick_start": "brew install flyctl && flyctl auth login && flyctl launch",
        "full_code": '''# Fly.io LLM proxy with multi-region deployment
# Save as fly.toml

app = "my-llm-proxy"
primary_region = "iad"     # primary (closest to OpenAI us-east)

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "stop"     # scale to zero when idle
  auto_start_machines = true
  min_machines_running = 0        # cold-start trade-off
  processes = ["app"]

  [[http_service.checks]]
    interval = "30s"
    grace_period = "5s"
    method = "GET"
    path = "/health"
    timeout = "5s"

[[vm]]
  size = "shared-cpu-1x"
  memory = "512mb"

# ----------------- DOCKERFILE -----------------

# # Save as Dockerfile alongside fly.toml
# FROM python:3.12-slim
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]


# ----------------- MAIN.PY (FastAPI LLM proxy) -----------------

# from fastapi import FastAPI
# from openai import AsyncOpenAI
# import os
#
# app = FastAPI()
# client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
#
# @app.post("/chat")
# async def chat(body: dict):
#     resp = await client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=body["messages"],
#     )
#     return {"response": resp.choices[0].message.content}
#
# @app.get("/health")
# def health():
#     return {"ok": True}


# ----------------- DEPLOY COMMANDS -----------------

# flyctl auth login
# flyctl launch                       # create app, generate fly.toml
# flyctl secrets set OPENAI_API_KEY=sk-...
# flyctl deploy
#
# # Add regions
# flyctl scale count 1 --region iad
# flyctl scale count 1 --region ams   # Amsterdam (EU)
# flyctl scale count 1 --region syd   # Sydney (APAC)
#
# # Now traffic routes to nearest region automatically
''',
        "dependencies": [],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "Set via flyctl secrets", "example": "sk-..."},
        ],
        "setup_steps": [
            "brew install flyctl (macOS) or curl -L fly.io/install.sh (linux)",
            "flyctl auth login",
            "Create fly.toml + Dockerfile + main.py",
            "flyctl launch (auto-creates app)",
            "flyctl secrets set OPENAI_API_KEY=sk-...",
            "flyctl deploy",
            "Add regions: flyctl scale count 1 --region <region>",
        ],
        "variations": [
            {"label": "Postgres on Fly (managed)", "description": "Co-locate DB.", "code_snippet": "flyctl postgres create --name mydb --region iad; flyctl postgres attach --app my-llm-proxy mydb"},
            {"label": "Redis cache via Upstash", "description": "Edge-friendly Redis.", "code_snippet": "# Add to fly.toml: [env] UPSTASH_REDIS_URL = '...'. Upstash has Fly integration."},
            {"label": "GPU machines (limited)", "description": "Fly has A10 / L40s in some regions.", "code_snippet": "# [[vm]] size = 'a10' . Limited availability; check fly.io/docs/gpus before relying"},
        ],
        "common_errors": [
            {"error_text": "Cold start ~5s per region", "cause": "auto_stop_machines + min_machines_running = 0.", "fix_snippet": "Set min_machines_running = 1 per region for always-warm. Costs ~$2/mo per always-on Machine."},
            {"error_text": "Multi-region routing not working", "cause": "Only deployed to one region.", "fix_snippet": "flyctl scale count N --region <region> per region. Verify: flyctl status. Anycast IP works only with multi-region."},
            {"error_text": "Deploy fails: image too large", "cause": "Dockerfile pulls big deps.", "fix_snippet": "Use python:3.12-slim (not python:3.12). Multi-stage build. Cache pip via requirements.txt."},
            {"error_text": "Secret not in container", "cause": "Set after deploy without redeploy.", "fix_snippet": "After flyctl secrets set, redeploy with flyctl deploy. Secrets are baked into the running machines."},
        ],
        "production_checklist": [
            "Multi-region deploy for global users.",
            "Set min_machines_running for latency-critical paths.",
            "Health checks for auto-recovery.",
            "Secrets via flyctl, never in repo / Dockerfile.",
            "Slim base image (python:3.12-slim).",
            "Monitor: flyctl logs, flyctl status; Prometheus via fly_app_metrics.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["flyctl==0.3"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["fly-io", "fastapi"],
        "related_glossary_slugs": ["edge-deployment", "anycast"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Fly vs Railway vs Render?", "answer": "Fly: global edge, slightly less polished UX. Railway: simplest DX. Render: middle ground. For multi-region needs, Fly wins. For single-region MVP, Railway / Render are easier."},
            {"question": "Cost?", "answer": "Hobby tier: $5/mo. Pay-per-resource: $2/mo per always-on shared CPU. 3 regions × 24/7 ~$6/mo. Spike pricing for traffic."},
            {"question": "GPU support?", "answer": "Limited — A10 / L40s in select regions. For real GPU LLM hosting, Modal / Cloud Run are better. Fly is great for LLM-PROXY (SaaS APIs) not LLM-SERVING."},
            {"question": "Database options?", "answer": "Fly Postgres (managed), Upstash Redis (integration), connect to any external. Co-locating DB with Fly app keeps query latency low."},
        ],
        "github_url": "https://github.com/superfly/flyctl",
        "meta_title": "Fly.io Edge LLM Deployment Starter",
        "meta_description": "Fly.io: multi-region LLM proxy deployment. Edge presence in 30+ regions, auto-stop/start, anycast routing.",
    },
    {
        "slug": "huggingface-spaces-gradio-llm",
        "title": "HuggingFace Spaces Gradio LLM Demo",
        "tldr": "HF Spaces: free-tier hosting for Gradio demos. Best for: research demos, shareable prototypes, public-facing tools. Free CPU, optional GPU.",
        "category": "deployment",
        "language": "python",
        "framework": "Gradio + HF Spaces",
        "tags": ["huggingface", "gradio", "spaces", "demos"],
        "best_for_tags": ["research", "demos", "public-prototypes"],
        "difficulty_tier": "beginner",
        "featured": False,
        "when_to_use": "Building a shareable LLM demo. HF Spaces: free CPU tier, integrated with HF model hub, automatic HTTPS, easy to share. Best PoC/demo path.",
        "when_not_to_use": "Skip for production traffic (rate limits, no SLA). Skip for private apps (Spaces are public by default; PRO/private requires paid).",
        "quick_start": "Create Space at huggingface.co/new-space, choose Gradio SDK, push app.py",
        "full_code": '''"""HuggingFace Spaces Gradio LLM demo."""
from __future__ import annotations

import os
import gradio as gr
from huggingface_hub import InferenceClient


# Use HF Inference API (free tier; rate-limited)
client = InferenceClient(
    model="meta-llama/Llama-3.1-8B-Instruct",
    token=os.environ.get("HF_TOKEN"),
)


# ----------------- CHAT FUNCTION -----------------

def chat(message: str, history: list[tuple[str, str]], temperature: float = 0.7,
         max_tokens: int = 512) -> str:
    """Gradio's chat interface calls this with current message + history."""
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    for user_msg, bot_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": bot_msg})
    messages.append({"role": "user", "content": message})

    response = ""
    for chunk in client.chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
    ):
        token = chunk.choices[0].delta.content or ""
        response += token
        yield response  # streaming


# ----------------- UI -----------------

with gr.Blocks(theme=gr.themes.Soft(), title="LLM Chat Demo") as demo:
    gr.Markdown("# LLM Chat Demo")
    gr.Markdown("Free HF Inference API — rate-limited.")

    chatbot = gr.ChatInterface(
        fn=chat,
        chatbot=gr.Chatbot(height=400),
        additional_inputs=[
            gr.Slider(minimum=0, maximum=2, value=0.7, step=0.1, label="Temperature"),
            gr.Slider(minimum=64, maximum=2048, value=512, step=64, label="Max Tokens"),
        ],
        examples=[
            ["What's caching?"],
            ["Explain rate limiting in 3 sentences."],
            ["Write a haiku about deadlines."],
        ],
    )


# ----------------- LAUNCH -----------------

if __name__ == "__main__":
    demo.launch()


# ============== FILES FOR HF SPACE ==============

# README.md (required, with metadata header)
README = """
---
title: LLM Chat Demo
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# LLM Chat Demo

Chat with Llama-3.1-8B via HuggingFace Inference API.
"""

# requirements.txt
REQS = """
gradio==4.44.0
huggingface-hub>=0.25
"""
''',
        "dependencies": [
            {"name": "gradio", "version": ">=4.44", "purpose": "UI framework"},
            {"name": "huggingface-hub", "version": ">=0.25", "purpose": "HF Inference API client"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": False, "description": "Set via Space secrets (for higher rate limits)", "example": "hf_..."},
        ],
        "setup_steps": [
            "Sign in at huggingface.co",
            "huggingface.co/new-space → SDK: Gradio, hardware: CPU basic (free)",
            "Clone the empty Space repo",
            "Add app.py + requirements.txt + README.md (with metadata)",
            "git push — Space auto-builds + deploys",
            "Set HF_TOKEN in Space settings for higher rate limits",
        ],
        "variations": [
            {"label": "GPU Space (Inference Endpoints)", "description": "Pay for dedicated GPU.", "code_snippet": "# Space settings → hardware → T4 / A10 / A100. ~$0.50-3/hr. Use local model via transformers."},
            {"label": "ZeroGPU (free GPU sometimes)", "description": "HF's free GPU pool for PRO accounts.", "code_snippet": "# Add @spaces.GPU decorator: @spaces.GPU(duration=30) def chat(...): ..."},
            {"label": "Multi-model demo", "description": "Compare outputs side-by-side.", "code_snippet": "# Use gr.Row() with two ChatInterfaces, different models. Useful for model evaluation."},
        ],
        "common_errors": [
            {"error_text": "Inference API 429 rate limit", "cause": "Free tier limit.", "fix_snippet": "Set HF_TOKEN in Space secrets (paid token has higher limits). Or use PRO account. Or rotate models that have higher quota."},
            {"error_text": "Space stuck in 'Building'", "cause": "requirements.txt error.", "fix_snippet": "Check Space's Logs tab. Common: typo in requirements, missing dep, version mismatch. Restart build after fix."},
            {"error_text": "Streaming not working", "cause": "Old gradio.", "fix_snippet": "Use gradio>=4.0 for streaming yields. Use ChatInterface (not Chatbot directly) for built-in streaming."},
            {"error_text": "Space goes to sleep", "cause": "Free tier auto-sleeps after inactivity.", "fix_snippet": "PRO subscription keeps Spaces awake. Or set up a cron to ping (against ToS for some plans)."},
        ],
        "production_checklist": [
            "Use HF_TOKEN secrets, never inline.",
            "Free tier: expect rate limits + sleeps.",
            "Pin gradio + huggingface-hub versions.",
            "README metadata correct (sdk, sdk_version).",
            "For real prod, use HF Inference Endpoints (dedicated, $$$).",
            "Track usage to avoid surprise rate-limit periods.",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-8B-Instruct"],
            "library_versions": ["gradio==4.44"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["huggingface", "gradio"],
        "related_glossary_slugs": ["gradio", "huggingface-spaces"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Spaces vs Streamlit Cloud?", "answer": "Spaces: HF-integrated, better for ML demos. Streamlit Cloud: better for general data apps. Both have free tiers; pick by ecosystem."},
            {"question": "GPU options?", "answer": "T4 ($0.40/hr), A10 ($1.50/hr), A100 ($3-4/hr). Paid tier. PRO accounts get ZeroGPU pool (free, time-limited)."},
            {"question": "Private Spaces?", "answer": "PRO tier ($9/mo) or Enterprise. Private Spaces only visible to specified users / org."},
            {"question": "When NOT to use Spaces?", "answer": "Production SaaS (SLA-required), private apps (need paid), high traffic (rate limits hurt UX). For these, real cloud hosting wins."},
        ],
        "github_url": "https://github.com/gradio-app/gradio",
        "meta_title": "HuggingFace Spaces Gradio LLM Demo Starter",
        "meta_description": "HuggingFace Spaces: free Gradio LLM demos with streaming, examples, model selector. Best for research demos + shareable prototypes.",
    },
]
