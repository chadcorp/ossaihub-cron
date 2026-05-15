"""LLM inference starters — batch 4: Ollama production, llama.cpp server, SGLang, MLX."""

RECORDS = [
    {
        "slug": "ollama-production-deployment",
        "title": "Ollama Production Deployment (Concurrent Models)",
        "tldr": "Ollama in production: keep multiple models loaded, serve concurrent users, custom Modelfiles, env tuning. Self-hosted LLM with the simplest ops story.",
        "category": "llm-inference",
        "language": "bash",
        "framework": "Ollama",
        "tags": ["ollama", "production", "self-hosted", "deployment"],
        "best_for_tags": ["self-hosted", "rapid-deploy", "indie-developers"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Self-hosting LLMs with minimum ops complexity. Ollama wraps llama.cpp with a clean HTTP API + model management. Good fit for solo / small-team production under 50 QPS.",
        "when_not_to_use": "Skip for high QPS (vLLM has higher throughput). Skip for cluster deployments (Ollama is single-node; use Ollama + load balancer if you need scale-out).",
        "quick_start": "curl -fsSL https://ollama.com/install.sh | sh && ollama pull llama3.1:8b && ollama serve",
        "full_code": '''# Ollama production deployment configuration
# Save as deploy/ollama-prod.sh

#!/bin/bash
set -euo pipefail

# ----------------- INSTALL -----------------
# curl -fsSL https://ollama.com/install.sh | sh


# ----------------- ENV TUNING (set in systemd unit) -----------------

# Keep multiple models loaded simultaneously
export OLLAMA_MAX_LOADED_MODELS=3

# Allow concurrent requests per model
export OLLAMA_NUM_PARALLEL=4

# How long to keep idle models in memory
export OLLAMA_KEEP_ALIVE=15m

# GPU memory utilization
export OLLAMA_GPU_OVERHEAD=512  # MB reserved per GPU

# Bind to all interfaces (be sure to add auth in front!)
export OLLAMA_HOST=0.0.0.0:11434

# Disable telemetry
export OLLAMA_NOPRUNE=true


# ----------------- PULL MODELS -----------------

ollama pull llama3.1:8b              # general purpose
ollama pull llama3.1:70b-instruct-q4_K_M  # bigger; quantized
ollama pull qwen2.5-coder:7b         # for code tasks
ollama pull nomic-embed-text         # embeddings


# ----------------- CUSTOM MODEL (Modelfile) -----------------

cat > Modelfile.support <<'EOF'
FROM llama3.1:8b
PARAMETER temperature 0.2
PARAMETER num_ctx 8192
PARAMETER repeat_penalty 1.1
SYSTEM """You are Acme Support Bot. Answer in 50 words or less.
Always cite the documentation URL if relevant.
If you don't know, say 'I'll connect you with a human.'"""
EOF
ollama create support-bot -f Modelfile.support


# ----------------- SYSTEMD UNIT (linux) -----------------

cat > /etc/systemd/system/ollama.service <<'EOF'
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
Environment=OLLAMA_HOST=0.0.0.0:11434
Environment=OLLAMA_MAX_LOADED_MODELS=3
Environment=OLLAMA_NUM_PARALLEL=4
Environment=OLLAMA_KEEP_ALIVE=15m
User=ollama
Group=ollama
Restart=on-failure
RestartSec=3
LimitNOFILE=65536

[Install]
WantedBy=default.target
EOF

systemctl daemon-reload
systemctl enable --now ollama


# ----------------- HEALTH CHECK -----------------

cat > /usr/local/bin/ollama-health.sh <<'EOF'
#!/bin/bash
curl -sf http://localhost:11434/api/tags > /dev/null
EOF
chmod +x /usr/local/bin/ollama-health.sh


# ----------------- NGINX REVERSE PROXY WITH AUTH -----------------

cat > /etc/nginx/sites-available/ollama <<'EOF'
upstream ollama {
    server 127.0.0.1:11434;
}

server {
    listen 443 ssl http2;
    server_name llm.example.com;

    ssl_certificate /etc/letsencrypt/live/llm.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/llm.example.com/privkey.pem;

    # Basic auth (or use OAuth2 proxy for SSO)
    auth_basic "Ollama";
    auth_basic_user_file /etc/nginx/.htpasswd;

    # Disable buffering for streaming
    proxy_buffering off;
    proxy_cache off;
    proxy_request_buffering off;
    proxy_http_version 1.1;

    location / {
        proxy_pass http://ollama;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
EOF


# ----------------- USAGE FROM CLIENTS -----------------

echo "Test:"
echo "curl https://llm.example.com/api/chat -u user:pass -d '{ \\\"model\\\": \\\"support-bot\\\", \\\"messages\\\": [{\\\"role\\\": \\\"user\\\", \\\"content\\\": \\\"How do I reset my password?\\\"}] }'"
''',
        "dependencies": [
            {"name": "ollama", "version": ">=0.3", "purpose": "Ollama server"},
        ],
        "env_vars": [
            {"name": "OLLAMA_HOST", "required": False, "description": "Bind address", "example": "0.0.0.0:11434"},
            {"name": "OLLAMA_NUM_PARALLEL", "required": False, "description": "Concurrent per model", "example": "4"},
        ],
        "setup_steps": [
            "Install: curl -fsSL https://ollama.com/install.sh | sh",
            "Pull models: ollama pull llama3.1:8b",
            "Customize via Modelfile + ollama create",
            "Configure systemd unit + env vars",
            "Set up nginx + auth in front",
            "Monitor /api/tags for health",
        ],
        "variations": [
            {"label": "Docker deployment", "description": "Containerize Ollama.", "code_snippet": "# docker run -d --gpus all -v ollama:/root/.ollama -p 11434:11434 ollama/ollama; mount /root/.ollama as volume for model persistence"},
            {"label": "Kubernetes with GPU", "description": "K8s deployment.", "code_snippet": "# Use ollama/ollama image with nvidia-runtime; PVC for /root/.ollama; resource requests: nvidia.com/gpu: 1"},
            {"label": "Load balancer (multiple Ollama nodes)", "description": "Scale horizontally.", "code_snippet": "# nginx least_conn upstream across 3 Ollama nodes; sticky sessions via consistent hashing for model affinity"},
        ],
        "common_errors": [
            {"error_text": "Model not found after install", "cause": "Ollama running as different user.", "fix_snippet": "Models live in /usr/share/ollama/.ollama (system) or ~/.ollama (user). Verify OLLAMA_MODELS env var if customized."},
            {"error_text": "VRAM exhausted with multiple models", "cause": "OLLAMA_MAX_LOADED_MODELS too high.", "fix_snippet": "Each loaded model uses VRAM. 8B Q4 ~5GB; 70B Q4 ~40GB. Calculate: total_vram > sum of loaded models + headroom."},
            {"error_text": "Streaming slow through proxy", "cause": "Nginx buffering.", "fix_snippet": "Set proxy_buffering off + proxy_cache off (in the location block). Critical for SSE/streaming."},
            {"error_text": "Cold start on first request slow", "cause": "Model load.", "fix_snippet": "Pre-warm: 'curl -X POST localhost:11434/api/generate -d {model:llama3.1:8b}' on startup. Keeps model in memory; OLLAMA_KEEP_ALIVE controls how long."},
        ],
        "production_checklist": [
            "Reverse proxy with TLS + auth (basic / OAuth / mTLS).",
            "Disable proxy buffering for streaming.",
            "Pre-warm models on startup.",
            "Monitor VRAM utilization (especially with multiple models).",
            "Set systemd Restart=on-failure.",
            "Backup ~/.ollama/models if you have custom models.",
        ],
        "tested_with": {
            "model_versions": ["llama3.1:8b", "qwen2.5-coder:7b"],
            "library_versions": ["ollama 0.3"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["ollama"],
        "related_glossary_slugs": ["self-hosted-llm", "ollama"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Ollama vs vLLM?", "answer": "Ollama: easier ops, multi-model, slower throughput. vLLM: tuned for max throughput, single-model-per-server. Use Ollama for varied workloads + low ops; vLLM for high-QPS single-model serving."},
            {"question": "Concurrent users — how many?", "answer": "Depends on model size + GPU. Llama-3.1-8B on RTX 4090: ~5-10 concurrent at acceptable latency. 70B Q4 on H100: ~3-5 concurrent. Tune OLLAMA_NUM_PARALLEL."},
            {"question": "Can it run without GPU?", "answer": "Yes — falls back to CPU. ~10-30 tok/s for 8B on a modern CPU. Acceptable for low-volume internal tools."},
            {"question": "Custom fine-tuned models?", "answer": "Convert to GGUF (llama.cpp format) + import via Modelfile. Or use ollama create with a base model + LoRA adapter."},
        ],
        "github_url": "https://github.com/ollama/ollama",
        "meta_title": "Ollama Production Deployment Starter",
        "meta_description": "Ollama in production: concurrent models, custom Modelfiles, systemd, nginx + auth, env tuning. Self-hosted LLM with simple ops.",
    },
    {
        "slug": "llama-cpp-server-with-grammar",
        "title": "llama.cpp Server With Constrained Output (Grammar)",
        "tldr": "llama.cpp server with GBNF grammar: force model output to match a strict grammar (JSON, SQL, custom DSL). Guaranteed structured output without strict-mode model.",
        "category": "llm-inference",
        "language": "bash",
        "framework": "llama.cpp",
        "tags": ["llama-cpp", "grammar", "gbnf", "structured-output"],
        "best_for_tags": ["edge-deployment", "constrained-output", "no-cloud"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Self-hosting on a single machine and need GUARANTEED structured output (JSON, SQL, custom DSL). llama.cpp's grammar constrains decoding to match a GBNF grammar exactly.",
        "when_not_to_use": "Skip if using OpenAI strict mode (works without local hosting). Skip for free-form generation. Skip if your model already produces clean structured output.",
        "quick_start": "git clone llama.cpp; make; ./llama-server -m model.gguf --grammar-file json.gbnf",
        "full_code": '''# llama.cpp server with GBNF grammar for guaranteed structured output

# ----------------- BUILD llama.cpp WITH GPU SUPPORT -----------------

# git clone https://github.com/ggerganov/llama.cpp
# cd llama.cpp
# CUDA: cmake -B build -DGGML_CUDA=ON && cmake --build build --config Release -j
# Metal (Apple): cmake -B build -DGGML_METAL=ON && cmake --build build --config Release -j

# Download a GGUF model
# huggingface-cli download bartowski/Llama-3.1-8B-Instruct-GGUF \\
#   Llama-3.1-8B-Instruct-Q4_K_M.gguf --local-dir ./models


# ----------------- GBNF GRAMMARS -----------------

# json.gbnf — built-in; constrains output to valid JSON
# Available at: llama.cpp/grammars/json.gbnf

# Custom grammar for a specific JSON schema
cat > ticket.gbnf <<'EOF'
root ::= "{" ws "\"category\":" ws category "," ws "\"priority\":" ws priority "," ws "\"summary\":" ws string "}" ws
category ::= "\"billing\"" | "\"technical\"" | "\"general\""
priority ::= "\"low\"" | "\"medium\"" | "\"high\""
string ::= "\"" ([^"\\] | "\\" .){1,500} "\""
ws ::= ([ \t\n] ws)?
EOF

# Custom grammar for SQL-like DSL
cat > query.gbnf <<'EOF'
root ::= "SELECT " columns " FROM " table where? ";"
columns ::= column ("," ws column)*
column ::= [a-z_]+
table ::= [a-z_]+
where ::= " WHERE " condition
condition ::= column ws "=" ws value
value ::= "'" [^']* "'" | [0-9]+
ws ::= " "*
EOF


# ----------------- START SERVER WITH GRAMMAR -----------------

./llama-server \\
    --model ./models/Llama-3.1-8B-Instruct-Q4_K_M.gguf \\
    --port 8080 \\
    --n-gpu-layers 999 \\
    --ctx-size 4096 \\
    --n-parallel 4 \\
    --cont-batching \\
    --grammar-file ./ticket.gbnf \\
    --threads 8


# ----------------- CLIENT USAGE -----------------

# The server exposes an OpenAI-compatible API
# pip install openai

cat > client.py <<'EOF'
from openai import OpenAI
import json

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-used",
)

# Server-side grammar enforces structure
response = client.chat.completions.create(
    model="local",
    messages=[
        {"role": "user", "content": "Classify: I was charged twice in September."},
    ],
    temperature=0,
)

# Output is GUARANTEED to match the grammar
data = json.loads(response.choices[0].message.content)
print(data)  # {"category": "billing", "priority": "high", "summary": "..."}
EOF


# ----------------- PER-REQUEST GRAMMAR (no server restart) -----------------

cat > per_request.sh <<'EOF'
#!/bin/bash
# Pass grammar in the request body — overrides server default

GRAMMAR_JSON=$(jq -Rs . < ticket.gbnf)

curl http://localhost:8080/completion \\
  -d "{
    \"prompt\": \"Classify: I want a refund.\",
    \"grammar\": $GRAMMAR_JSON,
    \"n_predict\": 200,
    \"temperature\": 0
  }"
EOF

chmod +x per_request.sh
''',
        "dependencies": [
            {"name": "llama.cpp", "version": "latest", "purpose": "C++ inference server"},
        ],
        "env_vars": [],
        "setup_steps": [
            "Clone llama.cpp; build with GPU support",
            "Download GGUF model from HuggingFace",
            "Author GBNF grammar matching your schema",
            "Start server with --grammar-file",
            "Hit OpenAI-compatible /v1/chat/completions endpoint",
        ],
        "variations": [
            {"label": "Auto-generate grammar from JSON schema", "description": "Use json-schema-to-gbnf tool.", "code_snippet": "# python -m llama_cpp_python.tools.json_schema_to_gbnf schema.json > out.gbnf"},
            {"label": "OpenAI-compatible Python", "description": "Use llama-cpp-python's server.", "code_snippet": "# pip install 'llama-cpp-python[server]'; python -m llama_cpp.server --model model.gguf --grammar json.gbnf"},
            {"label": "Streaming + grammar", "description": "Stream tokens that match grammar.", "code_snippet": "# Add 'stream': true to request; tokens stream but ALL conform to grammar; final output is valid"},
        ],
        "common_errors": [
            {"error_text": "Grammar parse error", "cause": "Malformed GBNF.", "fix_snippet": "Test grammar with llama.cpp's --grammar-check flag. GBNF is sensitive to whitespace + escape chars."},
            {"error_text": "Output halts mid-generation", "cause": "Grammar terminates the generation early.", "fix_snippet": "Grammar with root ::= ... ends generation when matched. Ensure grammar matches FULL desired output, not just prefix."},
            {"error_text": "Slow generation with grammar", "cause": "Grammar masks every token.", "fix_snippet": "Grammar adds 10-30% latency. Acceptable for structured output. For free-form output, disable grammar."},
            {"error_text": "Tokens look valid but JSON parser fails", "cause": "Grammar allowed near-valid JSON.", "fix_snippet": "Use built-in json.gbnf which is well-tested. Custom grammars need careful testing on edge cases."},
        ],
        "production_checklist": [
            "Test grammar on diverse outputs (edge cases).",
            "Use built-in json.gbnf when output is JSON-shaped.",
            "Monitor generation time impact of grammar.",
            "Cache compiled grammars in server for performance.",
            "Document the grammar version alongside model.",
            "Pair with downstream JSON-schema validation for defense-in-depth.",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-8B-Instruct-Q4_K_M"],
            "library_versions": ["llama.cpp (build 3700+)"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["llama-cpp"],
        "related_glossary_slugs": ["gbnf", "constrained-decoding"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Grammar vs strict mode (OpenAI)?", "answer": "Same end goal; different mechanism. Strict mode: provider enforces server-side. Grammar (llama.cpp): you enforce client-side with GBNF. Both produce guaranteed structured output."},
            {"question": "GBNF vs JSON Schema?", "answer": "GBNF: grammar-level constraint (low-level, flexible). JSON Schema: type-level constraint (higher-level, easier). Some tools auto-convert JSON Schema → GBNF; lossy for advanced features."},
            {"question": "Performance overhead?", "answer": "10-30% slower than ungrammar-constrained generation. For most apps, acceptable. For latency-critical, run benchmarks."},
            {"question": "Multi-language grammars?", "answer": "Yes — GBNF can describe any context-free grammar. Define grammars for SQL, regex, custom DSLs. Useful for code generation pipelines."},
        ],
        "github_url": "https://github.com/ggerganov/llama.cpp",
        "meta_title": "llama.cpp Server With Grammar Starter",
        "meta_description": "llama.cpp + GBNF grammars: force model output to match strict structure (JSON, SQL, DSL). Self-hosted constrained decoding.",
    },
    {
        "slug": "sglang-fast-structured-inference",
        "title": "SGLang For Fast Structured Inference",
        "tldr": "SGLang: faster than vLLM for structured outputs (JSON schemas, regex constraints, multi-turn chains) due to RadixAttention + token-level constraint optimization.",
        "category": "llm-inference",
        "language": "python",
        "framework": "SGLang",
        "tags": ["sglang", "structured-output", "fast-inference", "constraints"],
        "best_for_tags": ["json-extraction", "production-rag", "throughput"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "Production workloads with heavy structured outputs (JSON extraction, classification, multi-turn agents). SGLang is often 2-5x faster than vLLM for these patterns.",
        "when_not_to_use": "Skip for free-form chat (vLLM is comparable, more mature). Skip if you don't have time to learn SGLang's DSL (Python-embedded, but distinct).",
        "quick_start": "pip install 'sglang[all]' && python -m sglang.launch_server --model meta-llama/Llama-3.1-8B-Instruct",
        "full_code": '''"""SGLang: fast structured inference with JSON-schema constraints."""
from __future__ import annotations

import sglang as sgl
from sglang import function, gen, system, user, assistant


# ----------------- SETUP -----------------

sgl.set_default_backend(sgl.RuntimeEndpoint("http://localhost:30000"))


# ----------------- JSON-CONSTRAINED GENERATION -----------------

TICKET_SCHEMA = """{
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["billing", "technical", "general"]},
        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        "summary": {"type": "string", "maxLength": 200},
        "next_action": {"type": "string"}
    },
    "required": ["category", "priority", "summary", "next_action"]
}"""


@function
def classify_ticket(s, message: str):
    s += system("Classify customer support tickets. Output JSON.")
    s += user(f"Ticket: {message}")
    s += assistant(gen("output", max_tokens=300, temperature=0,
                       json_schema=TICKET_SCHEMA))


# ----------------- MULTI-TURN WITH BRANCHING -----------------

@function
def multi_turn(s, question: str):
    """SGLang shines on multi-turn with prefix sharing via RadixAttention."""
    s += system("Answer in 50 words or less.")
    s += user(question)
    s += assistant(gen("first_response", max_tokens=200))

    # Branch — explore multiple follow-ups; RadixAttention caches the prefix
    forks = s.fork(3)
    for i, f in enumerate(forks):
        f += user(f"Now expand on point {i + 1}.")
        f += assistant(gen("follow_up", max_tokens=150))

    # Could merge / pick best, etc.


# ----------------- REGEX-CONSTRAINED GEN -----------------

@function
def extract_email(s, text: str):
    """Force output to match an email regex."""
    s += user(f"What email is mentioned in: {text}")
    s += assistant(gen("email", regex=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"))


# ----------------- BATCH PROCESSING -----------------

def process_batch(messages: list[str]) -> list[dict]:
    """Process many tickets in parallel; SGLang batches them efficiently."""
    states = classify_ticket.run_batch(
        [{"message": m} for m in messages],
        max_new_tokens=300,
    )
    return [s["output"] for s in states]


# ----------------- RUN -----------------

if __name__ == "__main__":
    # Single ticket
    state = classify_ticket.run(message="I was charged twice in September. Please refund.")
    print(state["output"])

    # Batch
    results = process_batch([
        "I was charged twice in September.",
        "Login button doesn't work — getting 500 error.",
        "Just checking in!",
    ])
    for r in results:
        print(r)

    # Email extraction with regex constraint
    email_state = extract_email.run(text="Reach me at jane.smith@example.com for follow-up.")
    print(email_state["email"])
''',
        "dependencies": [
            {"name": "sglang", "version": ">=0.3", "purpose": "SGLang runtime + DSL"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": True, "description": "Model downloads", "example": "hf_..."},
        ],
        "setup_steps": [
            "pip install 'sglang[all]'",
            "Launch server: python -m sglang.launch_server --model meta-llama/Llama-3.1-8B-Instruct --port 30000",
            "Wait for 'server is fired up' log",
            "Run client script",
        ],
        "variations": [
            {"label": "Multi-GPU tensor-parallel", "description": "Scale across GPUs.", "code_snippet": "python -m sglang.launch_server --model ... --tp 4  # tensor-parallel size 4"},
            {"label": "Quantized model", "description": "FP8 / INT4 for memory.", "code_snippet": "python -m sglang.launch_server --model ... --quantization fp8  # H100; or awq for older GPUs"},
            {"label": "OpenAI-compatible API", "description": "Drop-in OpenAI replacement.", "code_snippet": "# SGLang server exposes /v1/chat/completions; use openai client with base_url='http://localhost:30000/v1'"},
        ],
        "common_errors": [
            {"error_text": "ImportError flashinfer", "cause": "Missing CUDA wheel.", "fix_snippet": "Install matching CUDA wheel: pip install flashinfer-python -i https://flashinfer.ai/whl/cu121/torch2.4/. Match your CUDA version."},
            {"error_text": "Server hangs on first request", "cause": "Warm-up.", "fix_snippet": "First request triggers CUDA-graph capture (~30s). Pre-warm at startup with a dummy request."},
            {"error_text": "JSON schema not respected", "cause": "Older SGLang versions or invalid schema.", "fix_snippet": "Upgrade to >=0.3. Test schema is valid JSON Schema Draft 7. Use additionalProperties: false."},
            {"error_text": "Slower than expected", "cause": "Not using RadixAttention features.", "fix_snippet": "Use s.fork() for branching workloads, and reuse prefixes (system prompts) across requests. That's where SGLang wins."},
        ],
        "production_checklist": [
            "Use RadixAttention (default) — biggest perf advantage.",
            "Batch via run_batch for parallel inference.",
            "Pin SGLang + CUDA + flashinfer versions.",
            "Monitor GPU utilization (should be 80-95% under load).",
            "Quantize models (FP8 / AWQ) if memory-constrained.",
            "Pre-warm CUDA graphs at startup.",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-8B-Instruct"],
            "library_versions": ["sglang==0.3"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["sglang", "vllm"],
        "related_glossary_slugs": ["radix-attention", "structured-output"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "SGLang vs vLLM?", "answer": "vLLM: more mature, broader model support, simpler. SGLang: faster for structured outputs + multi-turn (RadixAttention). Pick SGLang for JSON-heavy / agentic workloads."},
            {"question": "OpenAI-compatible?", "answer": "Yes — SGLang exposes /v1/chat/completions. You can use openai Python client with base_url. JSON schema via response_format works."},
            {"question": "Production-ready?", "answer": "Yes, used by major orgs. Newer than vLLM but stable. Pin version. CUDA version matching is the main pain point."},
            {"question": "Multi-modal support?", "answer": "Yes — supports Llava, Qwen-VL, and others. Multi-modal inference is a strong SGLang differentiator."},
        ],
        "github_url": "https://github.com/sgl-project/sglang",
        "meta_title": "SGLang Fast Structured Inference Starter",
        "meta_description": "SGLang: faster than vLLM for structured outputs + multi-turn. JSON-schema constraints, regex constraints, RadixAttention caching.",
    },
    {
        "slug": "mlx-llm-on-apple-silicon",
        "title": "MLX LLM Inference On Apple Silicon",
        "tldr": "MLX: Apple's ML framework, optimized for Apple Silicon (M1/M2/M3/M4). Run quantized Llama-3 / Mistral on Mac at usable speeds. Lower power, no GPU rental.",
        "category": "llm-inference",
        "language": "python",
        "framework": "MLX",
        "tags": ["mlx", "apple-silicon", "metal", "local"],
        "best_for_tags": ["mac-developers", "edge-inference", "privacy-conscious"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Developing on Apple Silicon and want LOCAL LLM inference at reasonable speed. MLX is faster than llama.cpp on Mac for most models. Privacy + offline + zero-cost.",
        "when_not_to_use": "Skip for non-Mac. Skip for very large models (32GB unified memory limits practical model size to ~30B). Skip for production scale (consumer Macs aren't servers).",
        "quick_start": "pip install mlx-lm && python -m mlx_lm.generate --model mlx-community/Llama-3.1-8B-Instruct-4bit --prompt 'Hello'",
        "full_code": '''"""MLX LLM inference on Apple Silicon: load, generate, server."""
from __future__ import annotations

import argparse
import mlx.core as mx
from mlx_lm import load, generate, stream_generate


# ----------------- LOAD MODEL -----------------

# Pre-quantized models for Mac:
#   mlx-community/Llama-3.1-8B-Instruct-4bit       (~4GB)
#   mlx-community/Mistral-7B-Instruct-v0.3-4bit    (~4GB)
#   mlx-community/Qwen2.5-Coder-7B-Instruct-4bit   (~4GB)
#   mlx-community/Llama-3.1-70B-Instruct-4bit      (~40GB, M2 Ultra / M3 Max only)

MODEL = "mlx-community/Llama-3.1-8B-Instruct-4bit"


def get_model():
    """Load model + tokenizer once."""
    model, tokenizer = load(MODEL)
    return model, tokenizer


# ----------------- ONE-SHOT GENERATION -----------------

def chat_once(prompt: str) -> str:
    model, tokenizer = get_model()
    messages = [{"role": "user", "content": prompt}]
    formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    response = generate(model, tokenizer, prompt=formatted, max_tokens=512, temp=0.0)
    return response


# ----------------- STREAMING -----------------

def chat_stream(prompt: str):
    model, tokenizer = get_model()
    messages = [{"role": "user", "content": prompt}]
    formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    for token in stream_generate(model, tokenizer, prompt=formatted, max_tokens=512):
        print(token, end="", flush=True)
    print()


# ----------------- BENCHMARK -----------------

def benchmark():
    import time
    model, tokenizer = get_model()
    prompts = ["Explain caching.", "What's an LLM?", "Write a haiku."]
    total_tokens = 0
    start = time.time()
    for p in prompts:
        messages = [{"role": "user", "content": p}]
        formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        response = generate(model, tokenizer, prompt=formatted, max_tokens=200)
        total_tokens += len(tokenizer.encode(response))
    elapsed = time.time() - start
    print(f"Generated {total_tokens} tokens in {elapsed:.1f}s = {total_tokens/elapsed:.0f} tok/s")


# ----------------- SIMPLE HTTP SERVER (OpenAI-compatible) -----------------

# pip install mlx-lm[server]
# python -m mlx_lm.server --model mlx-community/Llama-3.1-8B-Instruct-4bit --port 8080
# Then use the OpenAI client with base_url=http://localhost:8080/v1


# ----------------- CLI -----------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default="Hello, world!")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--bench", action="store_true")
    args = parser.parse_args()

    if args.bench:
        benchmark()
    elif args.stream:
        chat_stream(args.prompt)
    else:
        print(chat_once(args.prompt))
''',
        "dependencies": [
            {"name": "mlx-lm", "version": ">=0.18", "purpose": "MLX LLM convenience layer"},
        ],
        "env_vars": [],
        "setup_steps": [
            "Ensure macOS 14+ and Apple Silicon Mac",
            "pip install mlx-lm",
            "python -m mlx_lm.generate --model mlx-community/Llama-3.1-8B-Instruct-4bit --prompt 'Hello'",
            "For server: pip install 'mlx-lm[server]' && python -m mlx_lm.server",
        ],
        "variations": [
            {"label": "Convert HF model to MLX", "description": "Use models not on mlx-community.", "code_snippet": "from mlx_lm import convert\\nconvert.convert(hf_path='meta-llama/Llama-3.1-8B-Instruct', mlx_path='./out', quantize=True, q_bits=4)"},
            {"label": "LoRA fine-tuning on Mac", "description": "MLX supports LoRA training.", "code_snippet": "# python -m mlx_lm.lora --model ... --train --data ./data.jsonl --lora-layers 16"},
            {"label": "Multi-model server", "description": "Swap models via HTTP request.", "code_snippet": "# mlx-lm.server accepts 'model' param per request; swaps loaded model on demand. Slow first call after swap."},
        ],
        "common_errors": [
            {"error_text": "OOM on 70B model", "cause": "Insufficient unified memory.", "fix_snippet": "70B 4-bit needs ~40GB unified RAM. M2 Ultra (64GB) or M3 Max (36GB) only. Use 8B or 13B on smaller Macs."},
            {"error_text": "Slow generation (5 tok/s on M2)", "cause": "First-call warm-up.", "fix_snippet": "First request always slow (model load + Metal kernel compile). Steady-state: 30-50 tok/s for 8B on M2 Pro."},
            {"error_text": "ImportError: mlx not found", "cause": "Wrong Python (x86 Rosetta).", "fix_snippet": "Use NATIVE arm64 Python: 'arch -arm64 python -m venv venv'. MLX requires arm64 Python on Apple Silicon."},
            {"error_text": "Performance worse than llama.cpp Metal", "cause": "Older MLX version.", "fix_snippet": "Upgrade mlx-lm. MLX has been catching up + surpassing llama.cpp for many models on recent versions."},
        ],
        "production_checklist": [
            "Mac Studio / Mac Pro for production workloads (steadier power).",
            "Pre-load model at server start.",
            "Use quantized 4-bit models for memory efficiency.",
            "Profile actual tok/s; benchmarks vary by quantization.",
            "Apple Silicon is consumer hw — don't expect H100 throughput.",
            "Cache models on local SSD; symlink mlx-lm model dir.",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-8B-Instruct-4bit"],
            "library_versions": ["mlx-lm==0.18"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["mlx"],
        "related_glossary_slugs": ["apple-silicon", "quantization"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "MLX vs llama.cpp on Mac?", "answer": "MLX is now generally faster on Apple Silicon (better Metal kernels). llama.cpp Metal backend still works. MLX has lower API friction for Python."},
            {"question": "What can a Mac realistically run?", "answer": "M1 Pro (16GB): up to 7B 4-bit. M2 Max (32GB): up to 13B 4-bit or 70B 2-bit (slow). M3 Max (36-128GB): up to 70B 4-bit. Real-world tok/s varies."},
            {"question": "Production on Mac?", "answer": "For internal tools / small teams: yes. For external SaaS scale: no — Macs aren't designed for 24/7 inference. Use Modal / Cloud Run for production."},
            {"question": "Fine-tuning on Mac?", "answer": "LoRA fine-tuning works on Apple Silicon via MLX. Slower than NVIDIA but viable for small datasets + 7B models. Full fine-tuning of 70B not practical."},
        ],
        "github_url": "https://github.com/ml-explore/mlx-examples",
        "meta_title": "MLX LLM On Apple Silicon Starter",
        "meta_description": "Run quantized LLMs on M1/M2/M3 Macs with MLX: faster than llama.cpp on Apple Silicon, OpenAI-compatible server, LoRA fine-tuning.",
    },
]
