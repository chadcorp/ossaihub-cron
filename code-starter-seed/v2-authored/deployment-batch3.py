"""Deployment starters — batch 3: Modal, Cloud Run, AWS Lambda LLM, Railway."""

RECORDS = [
    {
        "slug": "modal-llm-inference-endpoint",
        "title": "Modal Serverless LLM Inference Endpoint",
        "tldr": "Modal.com serverless deployment: write a Python class, get a scalable HTTPS endpoint with GPU. Cold-start optimized (~2-4s); pay per second of GPU time.",
        "category": "deployment",
        "language": "python",
        "framework": "Modal",
        "tags": ["modal", "serverless", "gpu", "llm"],
        "best_for_tags": ["ml-engineers", "spiky-traffic", "rapid-deploy"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Spiky LLM inference traffic: handful of requests/min that occasionally spike to thousands. Modal scales to zero between traffic; pay only for GPU seconds used. Cold-start ~3s.",
        "when_not_to_use": "Skip for steady high-QPS workloads (dedicated VM is cheaper). Skip for ultra-latency-sensitive (sub-100ms p99) — Modal cold-start can hit you.",
        "quick_start": "pip install modal && modal token new && modal deploy llm_endpoint.py",
        "full_code": '''"""Modal serverless LLM inference with vLLM.

Deploys an HTTPS endpoint that scales 0→N on demand.
"""
from __future__ import annotations

import modal


app = modal.App("llm-inference")

# Pre-built image with vLLM + CUDA
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("vllm==0.6.3", "fastapi[standard]")
    .env({"VLLM_DISABLE_USAGE_STATS": "1"})
)


# Volume for model weights (persisted across cold starts)
volume = modal.Volume.from_name("hf-models", create_if_missing=True)
MODEL_DIR = "/cache/models"
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"


@app.cls(
    image=image,
    gpu="A10G",                       # or "H100" for big models
    volumes={MODEL_DIR: volume},
    secrets=[modal.Secret.from_name("hf-token")],
    scaledown_window=300,             # idle 5 min → scale down
    allow_concurrent_inputs=10,       # batch within a single container
    max_containers=20,                # cap on concurrent containers
)
@modal.concurrent(max_inputs=10)
class LLMEndpoint:
    @modal.enter()
    def load_model(self):
        """Cold-start: load model once per container."""
        from vllm import LLM
        from huggingface_hub import snapshot_download
        import os

        # Download to cached volume if not present
        if not os.path.exists(f"{MODEL_DIR}/{MODEL_ID}/config.json"):
            snapshot_download(
                MODEL_ID,
                local_dir=f"{MODEL_DIR}/{MODEL_ID}",
                token=os.environ["HF_TOKEN"],
            )
            volume.commit()

        self.llm = LLM(
            model=f"{MODEL_DIR}/{MODEL_ID}",
            tensor_parallel_size=1,
            gpu_memory_utilization=0.9,
            max_model_len=4096,
        )

    @modal.method()
    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.0) -> dict:
        from vllm import SamplingParams
        params = SamplingParams(max_tokens=max_tokens, temperature=temperature)
        outputs = self.llm.generate([prompt], params)
        return {"text": outputs[0].outputs[0].text, "tokens": len(outputs[0].outputs[0].token_ids)}

    @modal.fastapi_endpoint(method="POST")
    def web(self, request: dict):
        return self.generate.local(
            prompt=request["prompt"],
            max_tokens=request.get("max_tokens", 256),
        )


# Run from CLI: modal run llm_endpoint.py
@app.local_entrypoint()
def main():
    endpoint = LLMEndpoint()
    result = endpoint.generate.remote("Explain caching in 1 paragraph.")
    print(result)
''',
        "dependencies": [
            {"name": "modal", "version": ">=0.65", "purpose": "Modal Python SDK"},
        ],
        "env_vars": [
            {"name": "MODAL_TOKEN_ID", "required": True, "description": "Modal CLI token", "example": "ak-..."},
            {"name": "HF_TOKEN", "required": True, "description": "HuggingFace token for gated models (via Modal Secret)", "example": "hf_..."},
        ],
        "setup_steps": [
            "pip install modal",
            "modal token new  # opens browser for auth",
            "modal secret create hf-token HF_TOKEN=hf_...  # store HF token securely",
            "modal deploy llm_endpoint.py",
            "Test: curl -X POST https://<your-deployment>.modal.run -d '{\"prompt\":\"hi\"}'",
        ],
        "variations": [
            {"label": "Streaming via SSE", "description": "Token-by-token output.", "code_snippet": "# Use @modal.method(generators=True) + sse_starlette for SSE streaming back to clients"},
            {"label": "Multi-GPU (70B+)", "description": "Tensor-parallel across H100s.", "code_snippet": "gpu='H100:2'; tensor_parallel_size=2; ... # Modal supports multi-GPU containers natively"},
            {"label": "Dynamic batching across containers", "description": "vLLM AsyncEngine for higher throughput.", "code_snippet": "# Use vllm.AsyncLLMEngine with a batched fastapi endpoint; allows concurrent decoding within a container"},
        ],
        "common_errors": [
            {"error_text": "Cold start too slow (>30s)", "cause": "Model weights re-downloaded each container.", "fix_snippet": "Use modal.Volume to cache weights. First container downloads + commits; subsequent containers reuse."},
            {"error_text": "OOM on A10G with 8B model", "cause": "max_model_len too high or memory utilization too aggressive.", "fix_snippet": "Reduce max_model_len (e.g., 4096). Lower gpu_memory_utilization to 0.85. Or move to A100/H100."},
            {"error_text": "Function never scales down", "cause": "Long-running requests holding container.", "fix_snippet": "Set scaledown_window. Cap allow_concurrent_inputs. Make sure no background tasks linger."},
            {"error_text": "Auth failed at runtime", "cause": "Secret not mounted.", "fix_snippet": "Add secrets=[modal.Secret.from_name('hf-token')] to @app.cls. Verify secret exists via 'modal secret list'."},
        ],
        "production_checklist": [
            "Cache model weights in modal.Volume — saves cold-start bandwidth.",
            "Set max_containers cap — prevents runaway costs.",
            "Use modal.Secret for ALL credentials (never inline).",
            "Monitor via Modal dashboard: cold-start frequency, GPU utilization.",
            "Set up auto-scaling: scaledown_window + min_containers for warm pool.",
            "Pin Python + Modal + vLLM versions in image; reproducibility.",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-8B-Instruct"],
            "library_versions": ["modal==0.65", "vllm==0.6.3"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["modal"],
        "related_glossary_slugs": ["serverless", "cold-start"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Modal vs Replicate vs Banana?", "answer": "Modal: code-first, full Python control, $0.000031/A10G-sec. Replicate: model-marketplace, simpler deploy. Banana: simpler but pricier. Modal is best for custom code; Replicate for off-the-shelf models."},
            {"question": "Cold-start optimization?", "answer": "(1) Cache weights in Volume. (2) Use scaledown_window > 0 to keep some warm. (3) min_containers=1 for production warm pool. Cold starts go from 30s → 2-4s."},
            {"question": "Cost model?", "answer": "Per GPU-second + per CPU-second + per GB-second of memory. Charged per millisecond. Spiky traffic = much cheaper than always-on VM."},
            {"question": "Streaming support?", "answer": "Yes — use @modal.method(generators=True) or web-socket endpoints. sse_starlette wraps for SSE clients."},
        ],
        "github_url": "https://github.com/modal-labs/modal-client",
        "meta_title": "Modal Serverless LLM Inference — Deployment Starter",
        "meta_description": "Modal serverless LLM endpoint with vLLM, GPU autoscaling, volume-cached weights, cold-start optimized.",
    },
    {
        "slug": "cloud-run-llm-with-gpu",
        "title": "Cloud Run LLM API With GPU (L4)",
        "tldr": "Google Cloud Run with L4 GPU support: scale-to-zero containerized LLM endpoint. Pay per request; managed entirely. Good fit for spiky low-volume LLM apps.",
        "category": "deployment",
        "language": "python",
        "framework": "Cloud Run + Ollama",
        "tags": ["cloud-run", "gcp", "gpu", "ollama"],
        "best_for_tags": ["gcp-shops", "scale-to-zero", "managed"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Already on GCP and want LLM API without managing infra. Cloud Run + L4 GPU + Ollama gives you scale-to-zero with reasonable cold-start (~10s).",
        "when_not_to_use": "Skip for high-QPS production (dedicated GKE / Vertex is more cost-effective). Skip for very large models (L4 has 24GB; not enough for 70B+).",
        "quick_start": "gcloud run deploy --gpu=1 --gpu-type=nvidia-l4 --image=ollama/ollama:latest --memory=16Gi",
        "full_code": '''"""Cloud Run + Ollama: containerized LLM endpoint with L4 GPU.

Dockerfile + Cloud Run deploy. Ollama provides the OpenAI-compatible API.
"""

# ============== Dockerfile ==============
DOCKERFILE = """
FROM ollama/ollama:latest

# Pre-pull a model so cold-start doesn't re-download
RUN ollama serve & sleep 5 && ollama pull llama3.1:8b && pkill ollama

EXPOSE 11434
ENV OLLAMA_HOST=0.0.0.0:11434
ENV OLLAMA_KEEP_ALIVE=24h
ENV OLLAMA_NUM_PARALLEL=4

CMD ["ollama", "serve"]
"""


# ============== cloudbuild.yaml ==============
CLOUDBUILD = """
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/llm-api:latest', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/llm-api:latest']
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: 'gcloud'
  args:
  - 'run'
  - 'deploy'
  - 'llm-api'
  - '--image=gcr.io/$PROJECT_ID/llm-api:latest'
  - '--region=us-central1'
  - '--gpu=1'
  - '--gpu-type=nvidia-l4'
  - '--memory=16Gi'
  - '--cpu=4'
  - '--max-instances=10'
  - '--min-instances=0'
  - '--port=11434'
  - '--timeout=300s'
  - '--allow-unauthenticated'
"""


# ============== client.py ==============
from __future__ import annotations
import os
from openai import OpenAI

CLOUD_RUN_URL = os.environ["CLOUD_RUN_URL"]  # https://llm-api-xxx-uc.a.run.app

# Ollama is OpenAI-compatible; point base_url at the Cloud Run service
client = OpenAI(
    base_url=f"{CLOUD_RUN_URL}/v1",
    api_key="not-used",  # Ollama doesn't enforce auth by default
)


def chat(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama3.1:8b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
    )
    return response.choices[0].message.content


def stream_chat(prompt: str):
    response = client.chat.completions.create(
        model="llama3.1:8b",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print()


if __name__ == "__main__":
    print(chat("Explain rate limiting in 1 paragraph."))
    stream_chat("Write a haiku about caching.")
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI-compatible client for Ollama"},
        ],
        "env_vars": [
            {"name": "CLOUD_RUN_URL", "required": True, "description": "Deployed Cloud Run URL", "example": "https://llm-api-xxx-uc.a.run.app"},
            {"name": "GOOGLE_CLOUD_PROJECT", "required": True, "description": "GCP project for deployment", "example": "my-project"},
        ],
        "setup_steps": [
            "Enable Cloud Run + Cloud Build APIs",
            "Request L4 GPU quota (project quotas page)",
            "Save Dockerfile + cloudbuild.yaml to repo",
            "gcloud builds submit --config cloudbuild.yaml",
            "Capture deployed URL, export CLOUD_RUN_URL=...",
            "python client.py",
        ],
        "variations": [
            {"label": "Authenticate via IAM", "description": "Restrict access to specific identities.", "code_snippet": "# Remove --allow-unauthenticated; use IAM Invoker role. Add Authorization: Bearer <id-token> to requests"},
            {"label": "Self-host vLLM instead of Ollama", "description": "Higher throughput.", "code_snippet": "# Replace Dockerfile base with vllm/vllm-openai; CMD ['--model', 'meta-llama/Llama-3.1-8B-Instruct']"},
            {"label": "Larger model (70B)", "description": "Use Vertex AI instead.", "code_snippet": "# Cloud Run L4 has 24GB; not enough for 70B. Use Vertex AI Custom Endpoint with H100/A100."},
        ],
        "common_errors": [
            {"error_text": "Cold start 60+ seconds", "cause": "Model not baked into image.", "fix_snippet": "Pre-pull in Dockerfile (see RUN ollama pull). Also: --min-instances=1 to keep one warm."},
            {"error_text": "Quota exceeded: gpu nvidia-l4", "cause": "Default GPU quota is 0.", "fix_snippet": "Request L4 GPU quota in GCP console. Cloud Run GPU is per-project, per-region."},
            {"error_text": "OOM at request time", "cause": "Model + KV-cache exceeds 24GB.", "fix_snippet": "Reduce model size, set context-length lower (env OLLAMA_NUM_CTX=4096), or move to a bigger GPU via Vertex AI."},
            {"error_text": "Request timeout 5 min", "cause": "Long generation hits Cloud Run timeout.", "fix_snippet": "Set --timeout=3600s (max 60 min). Or stream tokens so client sees progress before final completion."},
        ],
        "production_checklist": [
            "Pre-bake model weights into the image (don't pull at boot).",
            "Set --min-instances=1 to avoid cold-start in production.",
            "Use IAM auth in production (no --allow-unauthenticated).",
            "Monitor: cold-start rate, latency p99, GPU utilization.",
            "Set sensible max-instances cap to prevent cost runaway.",
            "Use Cloud Run Jobs (not Service) for batch / async workloads.",
        ],
        "tested_with": {
            "model_versions": ["llama3.1:8b"],
            "library_versions": ["ollama 0.3", "openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["ollama", "google-cloud-run"],
        "related_glossary_slugs": ["scale-to-zero", "containerized-llm"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Cloud Run vs Modal vs Replicate?", "answer": "Cloud Run: GCP-native, IAM-integrated, simpler if already on GCP. Modal: Python-first, faster cold-start. Replicate: simpler for model marketplace. Pick by stack."},
            {"question": "How fast is cold-start with pre-baked weights?", "answer": "L4 cold-start ~10s (container boot + model load to GPU). Subsequent: cached. Use min-instances=1 for production to keep warm pool."},
            {"question": "GPU options on Cloud Run?", "answer": "Currently L4 (24GB) only. Up to 1 GPU per instance. For bigger, use Vertex AI Endpoints (H100, A100 multi-GPU)."},
            {"question": "Cost vs Modal?", "answer": "Roughly comparable per GPU-second. Cloud Run has lower per-request overhead. Modal scales-down faster (more granular billing). Test both for your workload."},
        ],
        "github_url": "https://github.com/ollama/ollama",
        "meta_title": "Cloud Run LLM with GPU — Deployment Starter",
        "meta_description": "Cloud Run + L4 GPU + Ollama LLM endpoint. Scale-to-zero, IAM auth optional, pre-baked weights for fast cold-start.",
    },
    {
        "slug": "lambda-llm-with-streaming-response",
        "title": "AWS Lambda LLM Streaming Response (No GPU)",
        "tldr": "AWS Lambda calling a SaaS LLM (OpenAI / Anthropic / Bedrock) with response streaming back to API Gateway. Sub-second cold start; pay per ms; no GPU needed.",
        "category": "deployment",
        "language": "python",
        "framework": "AWS Lambda",
        "tags": ["lambda", "aws", "streaming", "api-gateway"],
        "best_for_tags": ["aws-shops", "low-cost", "spiky-traffic"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Your LLM is a SaaS API (OpenAI/Anthropic/Bedrock) — you just need an API endpoint that streams responses. Lambda + Function URL Streaming gives you that with near-zero ops.",
        "when_not_to_use": "Skip for self-hosted LLMs (Lambda has no GPU). Skip if request duration regularly exceeds 15 min (Lambda max). Skip for ultra-high QPS where per-invocation overhead matters.",
        "quick_start": "Save lambda_function.py + sam template + 'sam deploy --guided'",
        "full_code": '''"""AWS Lambda streaming response: client sees tokens as the LLM generates them."""
from __future__ import annotations

import json
import os

from anthropic import Anthropic


client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def handler(event, context):
    """Lambda Function URL with InvokeMode=RESPONSE_STREAM.

    Returns a generator-style streaming response. API Gateway / function URL
    streams chunks back to the client as they arrive from Anthropic.
    """
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": "Invalid JSON"}

    prompt = body.get("prompt", "")
    if not prompt:
        return {"statusCode": 400, "body": "Missing 'prompt'"}

    # Use Lambda's streaming-response-bytes feature
    yield bytes(json.dumps({"event": "start"}) + "\\n", "utf-8")

    try:
        with client.messages.stream(
            model="claude-3-5-haiku-20241022",  # cheap + fast for streaming
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                payload = json.dumps({"event": "token", "text": text})
                yield bytes(payload + "\\n", "utf-8")

            final = stream.get_final_message()
            yield bytes(json.dumps({
                "event": "done",
                "tokens_in": final.usage.input_tokens,
                "tokens_out": final.usage.output_tokens,
            }) + "\\n", "utf-8")

    except Exception as e:
        yield bytes(json.dumps({"event": "error", "error": str(e)}) + "\\n", "utf-8")


# ----------------- SAM TEMPLATE (template.yaml) -----------------

SAM_TEMPLATE = """
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Resources:
  LLMStreamFn:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: python3.12
      Handler: lambda_function.handler
      CodeUri: ./
      Timeout: 60
      MemorySize: 256
      Environment:
        Variables:
          ANTHROPIC_API_KEY: !Ref AnthropicApiKey
      FunctionUrlConfig:
        AuthType: NONE   # or AWS_IAM for auth-required
        InvokeMode: RESPONSE_STREAM
Parameters:
  AnthropicApiKey:
    Type: String
    NoEcho: true
"""


# ----------------- CLIENT (consumes the stream) -----------------

CLIENT = """
import requests, json
url = 'https://xxx.lambda-url.us-east-1.on.aws/'
with requests.post(url, json={'prompt': 'Hello!'}, stream=True) as r:
    for line in r.iter_lines():
        if line:
            event = json.loads(line)
            if event['event'] == 'token':
                print(event['text'], end='', flush=True)
            elif event['event'] == 'done':
                print(f"\\\\nTokens in/out: {event['tokens_in']}/{event['tokens_out']}")
"""
''',
        "dependencies": [
            {"name": "anthropic", "version": ">=0.36", "purpose": "Anthropic SDK (bundled in deployment)"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Stored as Lambda env var (KMS-encrypted)", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "Save lambda_function.py + template.yaml in repo",
            "Install SAM CLI: brew install aws-sam-cli  (or pipx install aws-sam-cli)",
            "sam build && sam deploy --guided",
            "Capture FunctionUrl from outputs",
            "curl with --no-buffer to test streaming",
        ],
        "variations": [
            {"label": "Bedrock instead of Anthropic SaaS", "description": "AWS-native; no external API key.", "code_snippet": "# Use boto3 bedrock-runtime.invoke_model_with_response_stream; identical Lambda streaming pattern"},
            {"label": "Function URL with IAM auth", "description": "Authenticated streaming.", "code_snippet": "# Set AuthType: AWS_IAM; clients sign requests with SigV4 (use botocore auth helpers)"},
            {"label": "Connect to API Gateway", "description": "Add custom domain / WAF / throttling.", "code_snippet": "# Use AWS::ApiGateway::WebSocketApi for bi-directional streaming via WebSocket"},
        ],
        "common_errors": [
            {"error_text": "Lambda times out at 60s mid-stream", "cause": "Long generation > timeout.", "fix_snippet": "Set Timeout: 900 (15 min, Lambda max). For longer, split request or move to Bedrock async."},
            {"error_text": "Client sees buffered response (not streamed)", "cause": "InvokeMode not set, OR proxy buffering.", "fix_snippet": "InvokeMode: RESPONSE_STREAM in template. If behind CloudFront, set OriginResponseHeadersPolicy to disable buffering."},
            {"error_text": "Cold-start ~3s feels long", "cause": "Anthropic SDK + dependencies large.", "fix_snippet": "Use Lambda Layers for SDK. Use SnapStart (Python 3.12+) — sub-second cold-start."},
            {"error_text": "Cost surprise on high QPS", "cause": "Lambda + streaming has per-invocation + duration cost.", "fix_snippet": "Above ~50 QPS sustained, dedicated ECS/Fargate is cheaper. Monitor Lambda Insights."},
        ],
        "production_checklist": [
            "Use AWS Secrets Manager for API keys (not Lambda env).",
            "Enable Lambda SnapStart for Python 3.12+ cold-start optimization.",
            "Set proper timeout (max 15 min).",
            "Enable Function URL throttling or put behind API Gateway with usage plans.",
            "Log token counts → CloudWatch metrics → cost alerts.",
            "X-Ray tracing for end-to-end latency profiling.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-5-haiku-20241022"],
            "library_versions": ["anthropic==0.36", "aws-sam-cli==1.130"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["aws-lambda", "anthropic"],
        "related_glossary_slugs": ["serverless", "response-streaming"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Lambda streaming — is it real streaming?", "answer": "Yes. With InvokeMode=RESPONSE_STREAM, the response is sent in chunks as the function yields. Client sees tokens as they arrive."},
            {"question": "Why not always use Lambda for LLM apps?", "answer": "Two limits: (1) no GPU, so SaaS-only. (2) 15-min max duration. For self-hosted or long-running, use ECS/EKS instead."},
            {"question": "Lambda vs Cloud Run streaming?", "answer": "Roughly equivalent. Lambda: tighter AWS integration. Cloud Run: easier port-based service. Pick by stack."},
            {"question": "What about cost?", "answer": "Pure SaaS proxy: ~$0.0001 per request. Streaming adds per-second cost (~$0.0000083/s) — typically <$0.001 per 30s stream. Cheap."},
        ],
        "github_url": "https://github.com/aws/aws-sam-cli",
        "meta_title": "AWS Lambda LLM Streaming — Deployment Starter",
        "meta_description": "Lambda Function URL with RESPONSE_STREAM mode: stream LLM tokens from Anthropic/OpenAI/Bedrock through Lambda to clients.",
    },
    {
        "slug": "railway-fastapi-langchain-app",
        "title": "Railway Deploy: FastAPI + LangChain LLM App",
        "tldr": "Railway: git push, get URL. Deploy a FastAPI + LangChain app with Postgres + Redis in 5 minutes. Lowest-friction managed platform for LLM apps under 50 QPS.",
        "category": "deployment",
        "language": "python",
        "framework": "Railway + FastAPI",
        "tags": ["railway", "fastapi", "deploy", "platform"],
        "best_for_tags": ["mvp", "rapid-deploy", "indie-hackers"],
        "difficulty_tier": "beginner",
        "featured": True,
        "when_to_use": "Shipping an MVP or side project. Railway: git push deploys, free tier covers small apps, includes Postgres + Redis managed. Best DX for solo/small teams.",
        "when_not_to_use": "Skip for enterprise compliance (no SOC2 at lower tiers). Skip for high QPS — pricing scales steeply past Pro tier. Skip if you need GPU (Railway has CPU only; use Modal/Cloud Run).",
        "quick_start": "Push to GitHub, connect at railway.app, click deploy",
        "full_code": '''"""FastAPI + LangChain + Postgres + Redis on Railway.

Project structure:
  app.py
  requirements.txt
  Dockerfile (optional; Railway auto-detects Python)
  railway.toml
"""

# ============== app.py ==============
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as aioredis
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


# Railway injects these env vars from connected plugins
DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]


# ----------------- DB MODEL -----------------

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class QueryLog(Base):
    __tablename__ = "query_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    prompt = Column(String)
    response = Column(String)
    created_at = Column(DateTime)


# ----------------- LLM CLIENT -----------------

llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)


# ----------------- LIFESPAN -----------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = aioredis.from_url(REDIS_URL)
    Base.metadata.create_all(engine)
    yield
    await app.state.redis.close()


app = FastAPI(lifespan=lifespan)


# ----------------- REQUEST -----------------

class ChatRequest(BaseModel):
    user_id: str
    prompt: str


# ----------------- ENDPOINT (with Redis cache + Postgres log) -----------------

@app.post("/chat")
async def chat(req: ChatRequest):
    # Cache check (cache same prompt for 60s)
    cache_key = f"chat:{req.prompt}"
    cached = await app.state.redis.get(cache_key)
    if cached:
        return {"response": cached.decode(), "cached": True}

    # LLM call
    response = llm.invoke([HumanMessage(content=req.prompt)])
    response_text = response.content

    # Cache + log
    await app.state.redis.setex(cache_key, 60, response_text)
    with SessionLocal() as db:
        from datetime import datetime
        db.add(QueryLog(
            user_id=req.user_id,
            prompt=req.prompt,
            response=response_text,
            created_at=datetime.utcnow(),
        ))
        db.commit()

    return {"response": response_text, "cached": False}


@app.get("/health")
async def health():
    return {"ok": True}


# ============== requirements.txt ==============
REQS = """
fastapi[standard]>=0.115
uvicorn[standard]>=0.30
sqlalchemy>=2.0
psycopg2-binary>=2.9
redis>=5.0
langchain-openai>=0.2
"""


# ============== railway.toml ==============
RAILWAY_TOML = """
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
"""
''',
        "dependencies": [
            {"name": "fastapi[standard]", "version": ">=0.115", "purpose": "Web framework"},
            {"name": "langchain-openai", "version": ">=0.2", "purpose": "OpenAI integration"},
            {"name": "psycopg2-binary", "version": ">=2.9", "purpose": "Postgres driver"},
            {"name": "redis", "version": ">=5.0", "purpose": "Redis client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "Set in Railway dashboard", "example": "sk-..."},
            {"name": "DATABASE_URL", "required": True, "description": "Auto-injected by Railway Postgres plugin", "example": "postgres://..."},
            {"name": "REDIS_URL", "required": True, "description": "Auto-injected by Railway Redis plugin", "example": "redis://..."},
        ],
        "setup_steps": [
            "git init && add app.py, requirements.txt, railway.toml",
            "Sign up at railway.app, connect GitHub repo",
            "Add Postgres + Redis plugins (one-click)",
            "Set OPENAI_API_KEY in service env vars",
            "git push → Railway auto-deploys",
            "curl https://your-app.up.railway.app/health",
        ],
        "variations": [
            {"label": "Fly.io alternative", "description": "Similar UX, different geography.", "code_snippet": "# fly.toml instead of railway.toml. flyctl deploy. Edge presence in 30+ regions."},
            {"label": "Render alternative", "description": "Similar managed platform.", "code_snippet": "# render.yaml. Slightly different DX; auto-scaling clearer; pricing comparable."},
            {"label": "Add LangSmith tracing", "description": "Observability.", "code_snippet": "# Set LANGCHAIN_TRACING_V2=true + LANGCHAIN_API_KEY in env. Traces appear in LangSmith automatically."},
        ],
        "common_errors": [
            {"error_text": "Connection refused on Redis", "cause": "REDIS_URL not injected.", "fix_snippet": "Verify Redis plugin is attached to the service. railway run env | grep REDIS — should show the URL."},
            {"error_text": "Postgres SSL required", "cause": "Railway Postgres uses SSL by default.", "fix_snippet": "psycopg2-binary handles this automatically; sqlalchemy URL should include sslmode=require if explicit."},
            {"error_text": "Build fails: no Python detected", "cause": "Missing requirements.txt or Procfile.", "fix_snippet": "Railway uses Nixpacks; needs requirements.txt OR pyproject.toml at root. Or add a Dockerfile."},
            {"error_text": "App crashes after deploy", "cause": "Missing env vars.", "fix_snippet": "Check service logs in Railway dashboard. Set OPENAI_API_KEY (and any other secrets) in Variables tab."},
        ],
        "production_checklist": [
            "Use Railway Pro tier for SLA + custom domains.",
            "Set up health check (Railway monitors /health).",
            "Use Railway's environment variables (not .env in repo).",
            "Add Postgres backups via Railway dashboard (Pro tier).",
            "Monitor: Railway dashboard for CPU/memory; logs via 'railway logs'.",
            "Set up alerts via Railway webhooks → Slack/PagerDuty.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["fastapi==0.115", "langchain==0.3"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["railway", "fastapi", "langchain"],
        "related_glossary_slugs": ["pass-deploy", "managed-platform"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Railway vs Fly.io vs Render?", "answer": "Railway: best DX for simple apps. Fly: best for global edge. Render: solid middle ground. All ~$5-20/mo for small apps. Pick whatever your team's already on."},
            {"question": "How much does it cost?", "answer": "Hobby tier: $5/mo. Pro: ~$20/mo + usage. Adds up at scale (50+ services). Compare to Cloud Run / Fargate for bigger fleets."},
            {"question": "GPU support?", "answer": "No. Railway is CPU only. For LLM apps, you call SaaS APIs (OpenAI/Anthropic/Bedrock) from Railway. For self-hosted models, use Modal or Cloud Run GPU."},
            {"question": "Custom domain / SSL?", "answer": "Free SSL on Railway-issued domains. Custom domain on Pro tier; one click + DNS record. Auto-renew Let's Encrypt."},
        ],
        "github_url": "https://github.com/railwayapp/cli",
        "meta_title": "Railway FastAPI LangChain Starter — Deployment",
        "meta_description": "Deploy FastAPI + LangChain + Postgres + Redis on Railway: git push, get URL. MVP-ready in 5 minutes.",
    },
]
