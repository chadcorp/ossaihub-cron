"""Deployment starters — Modal, FastAPI, Docker, serverless."""

RECORDS = [
    {
        "slug": "modal-llm-serverless-deploy",
        "title": "Modal Serverless LLM Service With GPU",
        "tldr": "Deploy an LLM-backed FastAPI service to Modal in one file. GPU autoscaling, secrets management, request-scoped cold-start optimization, and 0.5s warm starts.",
        "category": "deployment",
        "language": "python",
        "framework": "Modal",
        "tags": ["modal", "serverless", "gpu", "fastapi", "deployment"],
        "best_for_tags": ["self-hosted-llm", "side-projects", "low-traffic-services"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When deploying a small-to-medium LLM service and you don't want to manage Kubernetes. Modal handles GPU provisioning, scaling, and secrets — you write the function.",
        "when_not_to_use": "Skip for very-high-QPS production (Modal cold starts add 5-15s on a new container; warm containers are fast but capacity isn't unlimited). Skip when you need on-prem.",
        "quick_start": "pip install modal && modal token new && modal deploy app.py",
        "full_code": '''"""Modal serverless service: FastAPI + Llama 3.1 via vLLM.

Run locally:    modal serve app.py
Deploy:         modal deploy app.py
URL after deploy: in the Modal dashboard.

Cost notes:
  - GPU billed per second of use; auto-shuts down after idle period.
  - Container start can be slow (model download); we pre-cache via volume.
"""
from __future__ import annotations

import modal

app = modal.App("ossaihub-llm-service")

# Persistent volume for model weights (avoids re-downloading on each start)
volume = modal.Volume.from_name("hf-cache", create_if_missing=True)

# Container image: install deps inside Modal's build system
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "vllm==0.6.2",
        "fastapi==0.115.0",
        "pydantic==2.9.0",
    )
    .env({"HF_HOME": "/cache/huggingface"})
)

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"


@app.cls(
    image=image,
    gpu="A10G",                           # 24GB VRAM, fits 8B model in fp16
    volumes={"/cache": volume},
    secrets=[modal.Secret.from_name("hf-token")],   # HF token in dashboard
    container_idle_timeout=60 * 5,        # keep warm 5 min after last request
    timeout=60 * 10,                      # max single request 10 min
)
class LlamaService:
    @modal.enter()
    def load_model(self):
        """Run once per container — loads model into GPU memory."""
        from vllm import LLM, SamplingParams
        self.llm = LLM(
            model=MODEL_NAME,
            dtype="float16",
            max_model_len=4096,
            gpu_memory_utilization=0.85,
        )
        self.default_params = SamplingParams(temperature=0.7, top_p=0.9, max_tokens=512)
        print("Model loaded.")

    @modal.method()
    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        from vllm import SamplingParams
        params = SamplingParams(temperature=temperature, top_p=0.9, max_tokens=max_tokens)
        result = self.llm.generate([prompt], params)
        return result[0].outputs[0].text


# Web endpoint — FastAPI-like via @modal.fastapi_endpoint
@app.function(image=image)
@modal.fastapi_endpoint(method="POST", docs=True)
def chat(prompt: str, max_tokens: int = 512) -> dict:
    """POST /chat with body {prompt, max_tokens}."""
    service = LlamaService()
    output = service.generate.remote(prompt, max_tokens)
    return {"prompt": prompt, "response": output}


# Local CLI test
@app.local_entrypoint()
def main(prompt: str = "Explain attention in one paragraph."):
    service = LlamaService()
    print(service.generate.remote(prompt))
''',
        "dependencies": [
            {"name": "modal", "version": ">=0.66", "purpose": "Modal CLI + Python SDK"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": True, "description": "Hugging Face token (set as Modal secret, not env)", "example": "hf_..."},
        ],
        "setup_steps": [
            "pip install modal",
            "modal token new  # authenticate",
            "modal secret create hf-token HF_TOKEN=hf_...  # for gated models",
            "modal serve app.py  # local dev with hot reload",
            "modal deploy app.py  # production",
        ],
        "variations": [
            {
                "label": "vLLM with bigger model on A100",
                "description": "Llama 3.1 70B requires more VRAM.",
                "code_snippet": "gpu='A100-80GB'\\nMODEL_NAME = 'meta-llama/Llama-3.1-70B-Instruct'\\n# Or use 4x A10G via gpu='A10G:4' + tensor_parallel_size=4",
            },
            {
                "label": "Streaming responses",
                "description": "Stream tokens via SSE.",
                "code_snippet": "@modal.method()\\nasync def generate_stream(self, prompt):\\n    async for token in self.llm.async_generate(...):\\n        yield token",
            },
            {
                "label": "Multi-GPU tensor parallelism",
                "description": "Split model across GPUs.",
                "code_snippet": "@app.cls(gpu='A10G:2', ...)\\n# In load_model: LLM(model=..., tensor_parallel_size=2)",
            },
            {
                "label": "Always-warm container",
                "description": "Eliminate cold starts (costs more).",
                "code_snippet": "@app.cls(..., keep_warm=1)  # one always-warm replica",
            },
        ],
        "common_errors": [
            {
                "error_text": "modal.exception.ExecutionError: insufficient GPU memory",
                "cause": "Model + KV cache exceeds GPU VRAM.",
                "fix_snippet": "Lower max_model_len (smaller context) OR use smaller model OR upgrade GPU. A10G = 24GB, A100 = 40/80GB.",
            },
            {
                "error_text": "Cold start takes 90+ seconds",
                "cause": "Model weights downloaded on every cold container.",
                "fix_snippet": "Volume mount /cache (starter does this). HF cache persists across containers. Verify volume is properly mounted.",
            },
            {
                "error_text": "huggingface_hub.errors.GatedRepoError",
                "cause": "Llama 3.1 requires accepting license on HF Hub.",
                "fix_snippet": "Visit HF model page, accept license, then set HF_TOKEN secret on Modal.",
            },
            {
                "error_text": "Endpoint URL returns 404 after deploy",
                "cause": "Function not properly exposed.",
                "fix_snippet": "Confirm @modal.fastapi_endpoint decorator and @app.function on the right function. Check `modal app list` to see deployed endpoints.",
            },
        ],
        "production_checklist": [
            "Set keep_warm if you need consistent <1s response time.",
            "Use Modal Secrets, not env vars in code, for HF_TOKEN / API keys.",
            "Monitor cost in Modal dashboard; GPU minutes add up.",
            "Pre-download models to volume in a build step, not on first request.",
            "Set request timeout; LLM generation can run away.",
            "Use Modal's built-in metrics or wire to your observability stack.",
            "Test cold-start latency; warm-start latency; concurrency limits.",
        ],
        "tested_with": {
            "model_versions": ["meta-llama/Llama-3.1-8B-Instruct"],
            "library_versions": ["modal==0.66.0", "vllm==0.6.2"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["modal", "vllm"],
        "related_glossary_slugs": ["serverless", "gpu-inference", "vllm"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Modal vs Replicate vs RunPod?",
                "answer": "Modal: best DX for Python-centric deploys. Replicate: best for one-shot model hosting with a model registry. RunPod: cheapest raw GPU but more DIY. For custom LLM services, Modal wins on iteration speed.",
            },
            {
                "question": "How much does this cost?",
                "answer": "Llama 3.1 8B on A10G: ~$0.001/sec when running, $0 when idle. A 1k-prompt batch typically runs ~30-60s — pennies per batch. Always-warm is more expensive (~$1.50/hr per replica).",
            },
            {
                "question": "Can I use this for production?",
                "answer": "For low-to-medium QPS, absolutely. For high-QPS or strict latency SLAs, evaluate dedicated infrastructure (Bedrock, Together, Anyscale) — Modal's cold starts and capacity limits can bite.",
            },
            {
                "question": "How do I add authentication?",
                "answer": "Wrap the fastapi_endpoint with auth middleware via Modal's @web_endpoint, or proxy through your own service. Modal also supports API key headers natively.",
            },
        ],
        "github_url": "https://github.com/modal-labs/modal-examples",
        "meta_title": "Modal Serverless LLM Service With GPU",
        "meta_description": "Deploy a Llama 3.1 service to Modal in one file: FastAPI endpoint, GPU autoscaling, HF cache volume, secrets management.",
    },
    {
        "slug": "dockerfile-llm-fastapi-prod",
        "title": "Production Dockerfile for LLM FastAPI Service",
        "tldr": "Multi-stage Dockerfile for a Python LLM service: layered for fast rebuilds, non-root user, healthcheck endpoint, pre-cached embedding model, and gunicorn+uvicorn workers for concurrency.",
        "category": "deployment",
        "language": "dockerfile",
        "framework": "Docker + FastAPI",
        "tags": ["docker", "fastapi", "production", "deployment"],
        "best_for_tags": ["self-hosted", "kubernetes", "ci-cd"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When deploying a Python LLM service to your own infrastructure (K8s, ECS, plain VM) and you want a clean, production-quality container.",
        "when_not_to_use": "Skip for prototyping (Modal/Replicate are faster). Skip for very large model weights — image size becomes painful; mount weights via volume instead.",
        "quick_start": "docker build -t llm-svc . && docker run -p 8000:8000 --env-file .env llm-svc",
        "full_code": '''# syntax=docker/dockerfile:1.7

# -------- STAGE 1: Build dependencies --------
FROM python:3.11-slim AS builder

WORKDIR /build

# Build deps for native packages (psycopg, numpy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY pyproject + lock first for cached layer
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# -------- STAGE 2: Runtime --------
FROM python:3.11-slim AS runtime

# Non-root user
RUN useradd -m -u 1000 -s /bin/bash app
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/app/.local
ENV PATH="/home/app/.local/bin:$PATH"

# Pre-cache embedding model (skips runtime download)
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')" \\
    || echo "fastembed not in deps; skipping pre-cache"

# App code last (changes most often -> last layer)
COPY --chown=app:app app/ ./app/

USER app

# Healthcheck — service must expose GET /healthz
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \\
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz', timeout=2)" || exit 1

EXPOSE 8000

# gunicorn + uvicorn workers: good baseline for I/O-bound LLM proxies
# Tune --workers based on CPU; -k uvicorn.workers.UvicornWorker for ASGI
CMD ["gunicorn", "app.main:app", \\
     "--workers", "2", \\
     "--worker-class", "uvicorn.workers.UvicornWorker", \\
     "--bind", "0.0.0.0:8000", \\
     "--timeout", "120", \\
     "--access-logfile", "-", \\
     "--error-logfile", "-"]
''',
        "dependencies": [
            {"name": "docker", "version": ">=24.0", "purpose": "Build & run the container"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": False, "description": "If your app talks to OpenAI", "example": "sk-..."},
            {"name": "LOG_LEVEL", "required": False, "description": "Logging level", "example": "info"},
        ],
        "setup_steps": [
            "Create requirements.txt with your Python deps.",
            "Place app code in app/ directory with main.py exposing FastAPI app.",
            "Add a /healthz endpoint returning {'ok': True}.",
            "docker build -t llm-svc .",
            "docker run -p 8000:8000 --env-file .env llm-svc",
        ],
        "variations": [
            {
                "label": "GPU variant",
                "description": "Base image with CUDA.",
                "code_snippet": "FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04 AS runtime\\n# Then install Python and your deps on top. Run with docker run --gpus all.",
            },
            {
                "label": "Distroless final stage",
                "description": "Smaller image, no shell (harder to debug).",
                "code_snippet": "FROM gcr.io/distroless/python3-debian12 AS runtime\\nCOPY --from=builder /root/.local /home/app/.local\\nCOPY --chown=nonroot:nonroot app/ /app/\\nCMD [\"-m\", \"app.main\"]",
            },
            {
                "label": "Buildkit cache mount",
                "description": "Speed up pip installs.",
                "code_snippet": "RUN --mount=type=cache,target=/root/.cache/pip pip install --user -r requirements.txt",
            },
            {
                "label": "Volume-mounted model",
                "description": "Don't bake weights into image.",
                "code_snippet": "# Instead of pre-cache: docker run -v /host/models:/cache/models ...\\n# App reads model from /cache/models at startup.",
            },
        ],
        "common_errors": [
            {
                "error_text": "Healthcheck always failing",
                "cause": "App hasn't started or /healthz path missing.",
                "fix_snippet": "Add to FastAPI: @app.get('/healthz'); def healthz(): return {'ok': True}. Increase --start-period if your app does heavy startup (model loading).",
            },
            {
                "error_text": "Image is huge (>5GB)",
                "cause": "Including model weights, NLP corpora, or build-time tooling.",
                "fix_snippet": "Mount model weights as volume. Use multi-stage build (starter does this). Use python:slim, not full python image.",
            },
            {
                "error_text": "Permission denied writing to /app",
                "cause": "App needs to write but runs as non-root.",
                "fix_snippet": "Use chown=app:app for any writable directories. Better: write only to /tmp or a mounted volume that you control permissions on.",
            },
            {
                "error_text": "Pre-cache step fails in build",
                "cause": "No internet during build, or model not in deps yet.",
                "fix_snippet": "The starter uses || to make this non-fatal. For strict builds, install fastembed earlier in requirements.txt.",
            },
        ],
        "production_checklist": [
            "Pin all Python versions, base image digests, and apt packages.",
            "Run as non-root user (starter does).",
            "Set memory and CPU limits in your orchestrator (K8s requests/limits).",
            "Log to stdout/stderr; don't write log files inside the container.",
            "Configure healthcheck and readiness probes appropriately.",
            "Use a vulnerability scanner (Trivy, Grype) on every push.",
            "Sign images (Cosign) and verify in deployment.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["python==3.11", "fastapi==0.115.0", "gunicorn==23.0.0", "uvicorn==0.32.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["docker", "fastapi", "production-deployment"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "How many workers should I use?",
                "answer": "For LLM proxy (I/O-bound): 2-4 workers per CPU core. For CPU-heavy embedding inference: 1 worker per core. Test with load to find the right number for your workload.",
            },
            {
                "question": "Should I include model weights in the image?",
                "answer": "Small (~80MB): yes, simpler deploy. Large (>500MB): no, mount as volume or download on startup with a cache layer.",
            },
            {
                "question": "Why gunicorn + uvicorn vs just uvicorn?",
                "answer": "gunicorn manages worker processes (restarts on crash, handles SIGTERM gracefully). uvicorn handles the ASGI protocol. Together they give you both reliability and async performance.",
            },
            {
                "question": "Can I use this with Kubernetes?",
                "answer": "Yes — pair with a Deployment, Service, and Ingress. The healthcheck maps to readiness/liveness probes. Set resource requests/limits explicitly.",
            },
        ],
        "github_url": "",
        "meta_title": "Production Dockerfile for LLM FastAPI Service",
        "meta_description": "Multi-stage Dockerfile: layered deps, non-root, healthcheck, pre-cached embeddings, gunicorn+uvicorn workers. Production-grade Python container.",
    },
]
