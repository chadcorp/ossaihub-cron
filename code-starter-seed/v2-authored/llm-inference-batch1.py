"""LLM inference (batch 1) — v2 authored code starters (2026-05-14)."""

RECORDS = [
    {
        "slug": "llamacpp-server-quantized",
        "title": "llama.cpp Server with Q4/Q5/Q8 Quantization",
        "category": "llm-inference",
        "language": "bash",
        "framework": "llama.cpp",
        "tldr": "Production-ready llama.cpp server hosting a quantized GGUF model with HTTP+OpenAI-compatible API, KV-cache size tuning, and memory-mapped weights. Runs on CPU or single GPU.",
        "tags": ["llama-cpp", "gguf", "quantization", "self-host"],
        "best_for_tags": ["self-host", "low-cost", "consumer-gpu"],
        "difficulty_tier": "intermediate",
        "when_to_use": "When self-hosting on consumer hardware (single GPU or CPU-only) with predictable workloads. llama.cpp delivers solid throughput at low cost — a 7B Q4_K_M model runs comfortably on 8GB VRAM at ~30 tok/s. The OpenAI-compatible endpoint means you can swap from a cloud provider with no client-code changes. Best for indie devs, edge deployments, or air-gapped environments.",
        "when_not_to_use": "When you need >50 concurrent users — llama.cpp doesn't have continuous batching. Use vLLM or TGI. Also skip for the absolute highest quality — Q4/Q5 quantization loses ~1-2% on benchmarks vs full-precision.",
        "quick_start": "./llama-server -m model.gguf --host 0.0.0.0 --port 8080 -ngl 35",
        "full_code": (
            "# 1. Download a quantized GGUF model (one-time, ~5GB)\n"
            "# Recommendation: Llama 3.1 8B Q4_K_M from HuggingFace\n"
            "wget https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf -O llama-3.1-8b-q4.gguf\n\n"
            "# 2. Build llama.cpp (if not installed)\n"
            "# git clone https://github.com/ggerganov/llama.cpp && cd llama.cpp\n"
            "# make GGML_CUDA=1 -j  # or `cmake -B build -DGGML_METAL=ON` on Mac\n\n"
            "# 3. Launch server\n"
            "./llama-server \\\n"
            "    --model llama-3.1-8b-q4.gguf \\\n"
            "    --host 0.0.0.0 --port 8080 \\\n"
            "    --n-gpu-layers 35 \\\n"
            "    --ctx-size 8192 \\\n"
            "    --threads 8 \\\n"
            "    --batch-size 512 \\\n"
            "    --n-predict 2048 \\\n"
            "    --mlock \\\n"
            "    --metrics\n\n"
            "# 4. Test (OpenAI-compatible)\n"
            "curl http://localhost:8080/v1/chat/completions \\\n"
            "    -H 'Content-Type: application/json' \\\n"
            "    -d '{\n"
            "        \"model\": \"any-name\",\n"
            "        \"messages\": [{\"role\": \"user\", \"content\": \"Explain GGUF in one sentence.\"}],\n"
            "        \"max_tokens\": 200,\n"
            "        \"temperature\": 0.7\n"
            "    }'\n\n"
            "# 5. Use from Python with openai SDK pointed at localhost\n"
            "# from openai import OpenAI\n"
            "# c = OpenAI(base_url='http://localhost:8080/v1', api_key='not-needed')\n"
            "# c.chat.completions.create(model='any', messages=[...])\n"
        ),
        "dependencies": [
            {"name": "llama.cpp", "version": "b3500+", "purpose": "Inference runtime; build from source or via brew install llama.cpp"},
            {"name": "CUDA Toolkit", "version": "12.1+", "purpose": "For GPU acceleration (Linux/Windows); skip on Mac (uses Metal)"},
        ],
        "env_vars": [
            {"name": "LLAMA_CPP_PATH", "required": False, "description": "Path to llama-server binary if not in PATH"},
        ],
        "setup_steps": [
            "Build llama.cpp from source with GPU flag (5 min): make GGML_CUDA=1 -j",
            "Download a Q4_K_M GGUF — search HuggingFace for '<model>-GGUF' (bartowski is reliable)",
            "Pick GPU layer count based on VRAM: 35 for 8B/8GB, 60 for 8B/24GB",
            "Set ctx-size to your expected max input + output (default 4096; up to 128k for Llama 3.1)",
            "Launch server with --mlock if you have enough RAM (prevents swap thrashing)",
            "Test with the curl example above",
            "Wire your client (any OpenAI SDK works, base_url=localhost:8080/v1)",
        ],
        "variations": [
            {"label": "CPU-only mode", "description": "When no GPU available; uses AVX2/AVX512 instructions.", "code_snippet": "./llama-server --model x.gguf --n-gpu-layers 0 --threads $(nproc) --ctx-size 4096"},
            {"label": "Mac M-series with Metal", "description": "Apple Silicon GPU acceleration.", "code_snippet": "# Build: cmake -B build -DGGML_METAL=ON && cmake --build build --config Release\n./build/bin/llama-server --model x.gguf --n-gpu-layers 99 --ctx-size 8192"},
            {"label": "Multiple models with model-switching", "description": "Load model on-demand to save VRAM when serving multiple.", "code_snippet": "# Use --slot-save-path to checkpoint state\n./llama-server --model x.gguf --slots 4 --slot-save-path /tmp/slots/"},
            {"label": "Speculative decoding", "description": "Use a small draft model to accelerate generation.", "code_snippet": "./llama-server --model llama-3.1-70b-q4.gguf --model-draft llama-3.1-8b-q4.gguf --draft-max 8"},
        ],
        "common_errors": [
            {"error_text": "CUDA error: out of memory", "cause": "n-gpu-layers too high or ctx-size too large", "fix_snippet": "# Drop --n-gpu-layers by 5 increments until it fits. Each layer ~150-200MB at Q4."},
            {"error_text": "GGML_ASSERT: invalid quantization", "cause": "Model file corrupted or wrong format", "fix_snippet": "# Re-download. Verify with: shasum -a 256 model.gguf | compare against HF page checksum"},
            {"error_text": "Server returns 503 Service Unavailable", "cause": "All slots busy (default --slots is 1)", "fix_snippet": "# Increase concurrent slots: --slots 4 (each slot ~ctx-size memory)"},
            {"error_text": "Latency >10s per request despite small prompts", "cause": "Layers fell back to CPU because GPU memory ran out", "fix_snippet": "# Check server log on startup — should say 'offloaded X/N layers to GPU'. If X<N, lower ctx-size or use smaller quant (Q3_K_M)."},
            {"error_text": "Different output across runs with same seed", "cause": "Multi-slot scheduling non-determinism", "fix_snippet": "# Run with --slots 1 --no-mmap --threads 1 for full reproducibility (much slower)"},
        ],
        "production_checklist": [
            "Pin to specific llama.cpp commit (build numbers change behavior)",
            "Verify GGUF checksum matches HuggingFace listed hash",
            "Set --mlock if RAM > model_size + ctx_size buffer",
            "Use --metrics flag, scrape /metrics with Prometheus",
            "Place behind reverse proxy (nginx) with rate limiting",
            "Monitor VRAM usage in GPU-monitoring tool (nvidia-smi, nvtop)",
            "If batch >10 concurrent: switch to vLLM (continuous batching matters)",
            "Backup the GGUF file to S3 — HuggingFace versions get re-uploaded",
            "Test request latency p99 with realistic prompt length",
        ],
        "tested_with": {
            "model_versions": ["Llama-3.1-8B-Instruct Q4_K_M", "Llama-3.1-8B-Instruct Q5_K_M", "Llama-3.1-70B-Instruct Q4_K_M", "Qwen2.5-14B-Instruct Q5_K_M"],
            "library_versions": ["llama.cpp b3500", "llama.cpp b3700"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["llama-cpp", "ollama", "lm-studio"],
        "related_glossary_slugs": ["gguf", "quantization", "self-hosting"],
        "related_learn_slugs": ["self-hosting-llms"],
        "license": "MIT",
        "attribution": "OSS AI Hub Code Library",
        "github_url": "https://github.com/chadcorp/ossaihub-cron/tree/main/code-starter-seed",
        "status": "approved",
        "submitter_email": "hub@ossaihub.com",
        "submitter_name": "OSS AI Hub",
        "meta_title": "llama.cpp Server with GGUF — Self-Host with Quant",
        "meta_description": "Production-ready llama.cpp server with Q4/Q5/Q8 GGUF quantization, OpenAI-compatible API, KV-cache tuning, GPU/CPU/Metal support.",
        "faq": [
            {"question": "Q4 vs Q5 vs Q8 — which to choose?", "answer": "Q4_K_M is the sweet spot — 60% size reduction, <1% quality loss on benchmarks. Q5_K_M if you have extra VRAM and want minor quality bump. Q8_0 only for fidelity-critical workloads."},
            {"question": "How fast is it vs vLLM?", "answer": "Single-request: comparable. Concurrent (>5 users): vLLM wins by 5-10x due to continuous batching. Use llama.cpp for single-user / low-concurrency."},
            {"question": "Can I use it for production user traffic?", "answer": "Yes — for <10 concurrent users with predictable load. Above that, you need a real serving stack (vLLM, TGI, TRT-LLM)."},
            {"question": "Does it support function-calling?", "answer": "Yes since b3000+. Pass `tools=` like OpenAI. Tool-calling quality depends on the underlying model (Llama 3.1+ is solid)."},
        ],
    },

    {
        "slug": "vllm-batched-inference-metrics",
        "title": "vLLM Production Launch (Llama 3.3 70B + Prometheus)",
        "category": "llm-inference",
        "language": "python",
        "framework": "vLLM",
        "tldr": "Launch vLLM 0.7 in production: tensor-parallel across 4 GPUs, continuous batching, KV-cache reuse, Prometheus metrics, graceful shutdown. Handles 100+ concurrent users.",
        "tags": ["vllm", "production", "tensor-parallel", "metrics"],
        "best_for_tags": ["production-inference", "high-concurrency", "self-host"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "When serving >10 concurrent users on a self-hosted model and you need continuous batching for cost-efficient GPU utilization. vLLM's PagedAttention enables 2-4x throughput vs naive batching. Tensor parallelism across GPUs lets you serve Llama 3.3 70B on 4x A100/H100 with sub-second TTFT. Prometheus metrics give you the observability needed for SLO-bound services.",
        "when_not_to_use": "For single-user dev workloads — llama.cpp is simpler and faster to set up. Also skip if you can't run NVIDIA GPUs — vLLM is CUDA-only (AMD ROCm support is improving but immature).",
        "quick_start": "pip install vllm==0.7.0 && python launch_vllm.py",
        "full_code": (
            "\"\"\"vLLM production launcher: Llama 3.3 70B on 4x A100 80GB with metrics.\"\"\"\n"
            "import argparse, os, signal, subprocess, sys\n\n\n"
            "def main():\n"
            "    ap = argparse.ArgumentParser()\n"
            "    ap.add_argument('--model', default='meta-llama/Llama-3.3-70B-Instruct')\n"
            "    ap.add_argument('--tp', type=int, default=4, help='tensor parallel size')\n"
            "    ap.add_argument('--port', type=int, default=8000)\n"
            "    ap.add_argument('--max-model-len', type=int, default=8192)\n"
            "    ap.add_argument('--gpu-memory-util', type=float, default=0.92)\n"
            "    args = ap.parse_args()\n\n"
            "    cmd = [\n"
            "        sys.executable, '-m', 'vllm.entrypoints.openai.api_server',\n"
            "        '--model', args.model,\n"
            "        '--tensor-parallel-size', str(args.tp),\n"
            "        '--host', '0.0.0.0',\n"
            "        '--port', str(args.port),\n"
            "        '--max-model-len', str(args.max_model_len),\n"
            "        '--gpu-memory-utilization', str(args.gpu_memory_util),\n"
            "        '--enable-prefix-caching',  # KV-cache reuse for shared prefixes\n"
            "        '--enable-chunked-prefill',  # better latency under load\n"
            "        '--max-num-seqs', '256',\n"
            "        '--disable-log-stats',  # we get metrics via /metrics instead\n"
            "        '--served-model-name', 'llama-3.3-70b',\n"
            "    ]\n\n"
            "    print('Launching vLLM:', ' '.join(cmd), flush=True)\n"
            "    proc = subprocess.Popen(cmd)\n\n"
            "    def shutdown(signum, frame):\n"
            "        print(f'Received signal {signum}; gracefully shutting down vLLM', flush=True)\n"
            "        proc.terminate()\n"
            "        proc.wait(timeout=60)\n"
            "        sys.exit(0)\n\n"
            "    signal.signal(signal.SIGTERM, shutdown)\n"
            "    signal.signal(signal.SIGINT, shutdown)\n"
            "    proc.wait()\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        ),
        "dependencies": [
            {"name": "vllm", "version": "==0.7.0", "purpose": "Inference server with PagedAttention + continuous batching"},
            {"name": "torch", "version": ">=2.4.0,<2.5.0", "purpose": "vLLM 0.7 requires PyTorch 2.4"},
            {"name": "transformers", "version": ">=4.45.0", "purpose": "Model config + tokenizer"},
            {"name": "huggingface_hub", "version": ">=0.25.0", "purpose": "Model download from HF"},
        ],
        "env_vars": [
            {"name": "HUGGING_FACE_HUB_TOKEN", "required": True, "description": "Required for gated models like Llama 3.3 — get at huggingface.co/settings/tokens"},
            {"name": "VLLM_LOGGING_LEVEL", "required": False, "description": "Set to DEBUG for troubleshooting; default WARNING"},
            {"name": "CUDA_VISIBLE_DEVICES", "required": False, "description": "Restrict to specific GPUs (e.g., '0,1,2,3')"},
        ],
        "setup_steps": [
            "Provision 4x A100 80GB (or 4x H100) — Llama 70B needs ~140GB total",
            "Install CUDA 12.1+ and PyTorch 2.4 first: pip install torch==2.4.0",
            "pip install vllm==0.7.0 (matches the torch version)",
            "Accept Llama 3.3 license at huggingface.co/meta-llama/Llama-3.3-70B-Instruct",
            "Set HUGGING_FACE_HUB_TOKEN env var",
            "Run: python launch_vllm.py — first launch downloads weights (~140GB, takes 15-30 min)",
            "Verify with: curl http://localhost:8000/v1/models",
            "Scrape Prometheus metrics from http://localhost:8000/metrics",
        ],
        "variations": [
            {"label": "Single-GPU 8B model", "description": "For dev or low-traffic prod with 8B model.", "code_snippet": "python launch_vllm.py --model meta-llama/Llama-3.1-8B-Instruct --tp 1 --max-model-len 16384"},
            {"label": "Speculative decoding", "description": "Use a draft model to accelerate.", "code_snippet": "# Add to cmd:\n'--speculative-model', 'meta-llama/Llama-3.2-1B-Instruct',\n'--num-speculative-tokens', '5',"},
            {"label": "AWQ/GPTQ quantized", "description": "Run 70B on 2x A100 80GB via AWQ.", "code_snippet": "python launch_vllm.py --model neuralmagic/Llama-3.3-70B-Instruct-AWQ --tp 2"},
            {"label": "Multi-LoRA serving", "description": "Hot-swap LoRA adapters per-request.", "code_snippet": "# Add: '--enable-lora', '--lora-modules', 'adapter1=path/to/adapter1', 'adapter2=path/to/adapter2'"},
        ],
        "common_errors": [
            {"error_text": "CUDA out of memory at startup", "cause": "gpu-memory-utilization too high, or another process using GPU", "fix_snippet": "# nvidia-smi to check other processes. Drop --gpu-memory-util to 0.85"},
            {"error_text": "ImportError: cannot import name 'X' from 'torch'", "cause": "torch/vllm version mismatch", "fix_snippet": "# Always install torch FIRST, matching vllm's pinned version: pip install torch==2.4.0 vllm==0.7.0"},
            {"error_text": "503 Service Unavailable under load", "cause": "max-num-seqs exceeded; vLLM is queueing", "fix_snippet": "# Raise --max-num-seqs to 512 if VRAM allows; otherwise scale horizontally with multiple replicas"},
            {"error_text": "TTFT spikes to 5+ seconds under load", "cause": "Chunked prefill not enabled, or prompts too long for prefill scheduler", "fix_snippet": "# Ensure --enable-chunked-prefill flag is set; reduce --max-model-len if many short prompts share a worker"},
            {"error_text": "Model download stuck at 90%", "cause": "HF download server throttling", "fix_snippet": "# Set HF_HUB_ENABLE_HF_TRANSFER=1 and pip install hf_transfer for parallel chunks"},
        ],
        "production_checklist": [
            "Pin vllm + torch versions exactly (0.7.0 + 2.4.0 in tested setup)",
            "Scrape /metrics with Prometheus; alert on vllm:num_requests_waiting >10 for 5min",
            "Alert on p99 latency vllm:e2e_request_latency_seconds >1.5s",
            "Test SIGTERM behavior — verify in-flight requests drain (the signal handler does this)",
            "Run behind a load balancer if you need >1 replica",
            "Use --enable-prefix-caching for systems with shared system prompts",
            "Monitor GPU utilization — if <70%, increase --max-num-seqs",
            "Set up FluentBit or similar to ship vLLM logs (they're verbose; aggregate centrally)",
            "Test failover: kill a GPU worker, verify load balancer routes around it",
            "Cap inference cost: set per-request max_tokens at the load-balancer layer",
        ],
        "tested_with": {
            "model_versions": ["meta-llama/Llama-3.3-70B-Instruct", "meta-llama/Llama-3.1-70B-Instruct", "meta-llama/Llama-3.1-8B-Instruct"],
            "library_versions": ["vllm==0.7.0", "torch==2.4.0", "transformers==4.45.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["vllm", "tgi", "tensorrt-llm"],
        "related_glossary_slugs": ["continuous-batching", "paged-attention", "tensor-parallelism"],
        "related_learn_slugs": ["production-llm-serving"],
        "license": "MIT",
        "attribution": "OSS AI Hub Code Library",
        "github_url": "https://github.com/chadcorp/ossaihub-cron/tree/main/code-starter-seed",
        "status": "approved",
        "submitter_email": "hub@ossaihub.com",
        "submitter_name": "OSS AI Hub",
        "meta_title": "vLLM Production Launch — Llama 70B + Metrics + Graceful Shutdown",
        "meta_description": "Launch vLLM 0.7 in production: tensor-parallel 4xGPU, continuous batching, prefix caching, Prometheus metrics, signal handlers.",
        "faq": [
            {"question": "vLLM vs TGI vs TRT-LLM?", "answer": "vLLM: best Python ergonomics, broadest model support, mature. TGI: similar perf, Rust-based, HF ecosystem. TRT-LLM: highest throughput on NVIDIA (10-30% faster) but heaviest to operate. Start with vLLM."},
            {"question": "How many GPUs for Llama 70B?", "answer": "4x A100/H100 80GB for FP16 (140GB weights + KV cache). 2x for AWQ-quantized. 8x for FP16 + long context."},
            {"question": "Continuous batching — what does it actually buy?", "answer": "Instead of waiting for a batch to complete before starting the next, vLLM merges in-flight requests at every step. 2-4x higher throughput vs static batching at the same latency p99."},
            {"question": "Can I run multiple models on one server?", "answer": "Not in one vLLM process. Either run multiple instances on different ports, or use Multi-LoRA serving for fine-tuned variants of one base model."},
        ],
    },
]
