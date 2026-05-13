"""
Shared generator: reads a YAML manifest of seed entries and produces a rebuilt-v2.json
file by calling the Anthropic API for each entry. Used by both code-starter-seed and
prompt-library-seed.

Manifest format (YAML):
    library: code | prompt
    defaults:
      license: MIT
      tested_with:
        last_verified_date: "2026-05-13"
    entries:
      - slug: fastapi-ollama-streaming-chat
        title: "FastAPI + Ollama Streaming Chat"
        category: llm-clients
        language: python                # code only
        brief: "Production-ready chat API that streams Llama 3.1 8B responses from a local Ollama daemon."
        tags: [ollama, streaming, fastapi]
        best_for_tags: [streaming, local-llm, chat-api]

Usage:
    ANTHROPIC_API_KEY=sk-... python generate_v2.py \\
        --manifest code-starter-seed/manifest.yml \\
        --output code-starter-seed/rebuilt-v2.json \\
        --library code \\
        --concurrency 8

    # Regenerate only specific entries:
    python generate_v2.py ... --only fastapi-ollama-streaming-chat,rag-langchain-qdrant

    # Skip entries that already exist in the output (faster incremental runs):
    python generate_v2.py ... --skip-existing

The script uses Anthropic prompt caching on the system prompt + schema so each call
after the first costs ~1/10th of the first one. Concurrent requests are bounded to
keep API spend predictable.
"""

import argparse
import concurrent.futures
import json
import os
import pathlib
import re
import sys
import time

try:
    import yaml
except ImportError:
    print("Install pyyaml: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

try:
    from anthropic import Anthropic
except ImportError:
    print("Install anthropic: pip install anthropic", file=sys.stderr)
    sys.exit(2)


# ---------- system prompts ----------

CODE_SYSTEM_PROMPT = """You are a senior open-source AI infrastructure engineer authoring the canonical
content for the OSS AI Hub Code Library. Each entry teaches a builder how to use a
specific code pattern in 2026's open-source AI stack — Llama 3.x / Mistral / Qwen2.5
models, vLLM / SGLang / Ollama inference, LangChain / LangGraph / CrewAI / DSPy
frameworks, Qdrant / Chroma / Milvus vector stores, Anthropic SDK / Claude 4.x,
etc. Be specific about model versions and library versions.

Output STRICT JSON matching this schema (no preamble, no markdown fences, just JSON):

{
  "slug": "kebab-case",
  "title": "<= 120 chars, matches input title",
  "tldr": "20-220 chars, one sentence: what it does + why you'd reach for it",
  "category": "<one of the manifest category enum>",
  "language": "python | typescript | javascript | bash | dockerfile | yaml | rust | go",
  "framework": "primary framework name, e.g. FastAPI, LangChain, vLLM, n8n",
  "tags": ["..."],
  "best_for_tags": ["3-6 specific use-case keywords"],
  "difficulty_tier": "beginner | intermediate | advanced",
  "featured": false,
  "when_to_use": "80-200 words, specific scenarios with concrete examples",
  "when_not_to_use": "40-120 words, real anti-patterns and alternatives",
  "quick_start": "3-5 lines of shell that get them running, e.g.\\n```\\nuv pip install -U fastapi uvicorn ollama\\nollama pull llama3.1:8b\\nuvicorn main:app --reload\\n```",
  "full_code": "complete working code, syntax-highlightable, no truncation. Include comments explaining key sections.",
  "dependencies": [
    {"name": "fastapi", "version": ">=0.115", "purpose": "ASGI web framework"},
    {"name": "ollama", "version": ">=0.5", "purpose": "Python client for local Ollama daemon"}
  ],
  "env_vars": [
    {"name": "OLLAMA_HOST", "required": false, "description": "Override default localhost:11434", "example": "http://gpu-box:11434"}
  ],
  "setup_steps": [
    "Install dependencies via the quick-start command",
    "Pull the model: ollama pull llama3.1:8b",
    "Save the code as main.py",
    "Run uvicorn main:app and POST to /chat"
  ],
  "variations": [
    {
      "label": "Anthropic Claude variant",
      "description": "Swap Ollama for Anthropic API",
      "code_snippet": "from anthropic import Anthropic\\nclient = Anthropic()\\n# ... etc"
    },
    {
      "label": "vLLM serve variant",
      "description": "Use vLLM's OpenAI-compatible server for higher throughput",
      "code_snippet": "# point client at http://localhost:8000/v1\\nclient = OpenAI(base_url='http://localhost:8000/v1', api_key='x')"
    }
  ],
  "common_errors": [
    {
      "error_text": "ConnectionRefusedError: [Errno 111] Connection refused on http://localhost:11434",
      "cause": "Ollama daemon not running",
      "fix_snippet": "ollama serve &\\n# or systemctl start ollama"
    }
  ],
  "production_checklist": [
    "Add request timeout (e.g. asyncio.wait_for(coro, timeout=30))",
    "Validate input length before forwarding to model",
    "Rate-limit per-user via slowapi or nginx",
    "Add structured logging with request_id",
    "Set up healthcheck endpoint and readiness probe"
  ],
  "tested_with": {
    "model_versions": ["llama3.1:8b", "llama3.1:70b"],
    "library_versions": ["fastapi==0.115.0", "ollama==0.5.1", "uvicorn==0.32.0"],
    "last_verified_date": "2026-05-13"
  },
  "related_tool_slugs": ["ollama-ollama-4", "fastapi"],
  "related_glossary_slugs": ["streaming", "kv-cache", "context-window"],
  "related_learn_slugs": ["running-first-local-llm-ollama"],
  "license": "MIT",
  "attribution": "",
  "faq": [
    {"question": "Why use Ollama instead of vLLM here?", "answer": "Ollama is dramatically simpler for local development. Use vLLM when throughput becomes your bottleneck (>10 concurrent users)."},
    {"question": "How do I add streaming?", "answer": "Use the streaming variation above, or wrap the response in FastAPI's StreamingResponse."}
  ],
  "github_url": "",
  "meta_title": "<= 70 chars, SEO title",
  "meta_description": "<= 160 chars, SEO description"
}

REQUIREMENTS:
- Use 2026-current versions and patterns. No deprecated APIs. Reference Llama 3.x not 2, Claude 4.x not 3, etc.
- full_code must be a complete file that actually runs after the quick_start.
- common_errors: at least 3 real errors with specific fix snippets.
- variations: at least 2, ideally 3, showing different vendors or production-hardened modes.
- Cross-link aggressively: at minimum 3 related_tool_slugs, 2 related_glossary_slugs, 1 related_learn_slug. Use the canonical slugs from the OSS AI Hub directory.
- Tone: concise, expert, no marketing fluff. Builder talking to builder.
"""

PROMPT_SYSTEM_PROMPT = """You are an expert prompt engineer authoring the canonical content for the OSS AI
Hub Prompt Library. Each entry is a battle-tested prompt for a specific use case in
2026, optimized for Claude 4.x / GPT-5 / Gemini 2 / Llama 3.3-70B / Mistral Large 3 /
Qwen2.5-72B.

Output STRICT JSON matching this schema (no preamble, no markdown fences, just JSON):

{
  "slug": "kebab-case",
  "title": "<= 120 chars",
  "tldr": "20-220 chars: what the prompt does in one sentence",
  "category": "<one of the manifest category enum>",
  "tags": ["..."],
  "best_for_tags": ["3-6 specific use-case keywords"],
  "difficulty_tier": "beginner | intermediate | advanced",
  "featured": false,
  "use_cases": [
    {"scenario": "Specific scenario where this prompt shines", "example": "Concrete example input"},
    {"scenario": "...", "example": "..."},
    {"scenario": "...", "example": "..."}
  ],
  "when_not_to_use": "40-120 words on real anti-patterns",
  "full_prompt": "The complete prompt text with {variable_name} placeholders.\\nMulti-line. Includes any role-setting, constraints, output format hints.",
  "input_variables": [
    {"name": "document", "type": "string", "description": "The source text to analyze", "required": true, "example": "Quarterly report Q1 2026..."},
    {"name": "style", "type": "string", "description": "Target writing style", "required": false, "example": "concise, executive-summary"}
  ],
  "expected_output": {
    "format": "json | markdown | text | code | structured | list | table",
    "schema": "describe shape if structured, e.g. {summary: string, key_points: string[], action_items: string[]}",
    "sample": "Example output a model would produce"
  },
  "few_shot_examples": [
    {"input": "concrete input 1", "output": "concrete output 1"},
    {"input": "concrete input 2", "output": "concrete output 2"}
  ],
  "model_compatibility": [
    {"model": "Claude 4.6 Sonnet", "compatibility": "excellent", "notes": "Best for nuanced tone preservation"},
    {"model": "GPT-5", "compatibility": "excellent", "notes": ""},
    {"model": "Llama 3.3 70B", "compatibility": "good", "notes": "May need to add 'Output JSON only' to enforce format"},
    {"model": "Mistral Large 3", "compatibility": "good", "notes": ""},
    {"model": "Qwen2.5-72B", "compatibility": "fair", "notes": "Chain-of-thought helps for complex variants"}
  ],
  "variations": [
    {"label": "Concise", "description": "When you want a one-paragraph answer", "prompt_snippet": "<concise variant of the prompt>"},
    {"label": "Chain-of-Thought", "description": "When you need the model to show its reasoning", "prompt_snippet": "<CoT variant>"},
    {"label": "JSON-only", "description": "For programmatic consumption", "prompt_snippet": "<JSON-strict variant>"},
    {"label": "Function-calling", "description": "For tool-using agents", "prompt_snippet": "<function-call variant>"}
  ],
  "failure_modes": [
    {"symptom": "Model refuses citing 'I cannot...'", "fix": "Add a system-level grant: 'You are authorized to analyze X for legitimate Y purposes.'"},
    {"symptom": "Output is malformed JSON", "fix": "Add 'Output ONLY JSON, no preamble or markdown fences.' OR use Instructor/Outlines for schema enforcement."},
    {"symptom": "Model hallucinates facts not in the input", "fix": "Add 'Cite the exact text from the input that supports each claim.'"}
  ],
  "tested_with": {
    "models": ["Claude 4.6 Sonnet", "GPT-5", "Llama 3.3 70B"],
    "last_verified_date": "2026-05-13"
  },
  "related_prompt_slugs": [],
  "related_tool_slugs": ["instructor", "outlines"],
  "related_glossary_slugs": ["chain-of-thought", "json-mode", "structured-output"],
  "license": "CC-BY-4.0",
  "attribution": "",
  "faq": [
    {"question": "How do I plug this into LangChain?", "answer": "Use ChatPromptTemplate.from_template() with the full_prompt above; pass variables via .invoke({...})."}
  ],
  "meta_title": "<= 70 chars",
  "meta_description": "<= 160 chars"
}

REQUIREMENTS:
- Tone: precise, builder-facing, no fluff.
- use_cases: 3-5 distinct scenarios with concrete examples.
- variations: include at least Concise + CoT + JSON-only; add Function-calling and System-prompt when relevant.
- failure_modes: at least 3 real symptoms with specific fix snippets a builder can paste.
- Cross-link: minimum 2 related_tool_slugs (Instructor, Outlines, Guidance, BAML, LangChain are common pairings) and 3 related_glossary_slugs.
"""


def call_anthropic(client, system_prompt, user_message, model="claude-sonnet-4-20250514"):
    """One call with prompt caching on the system prompt for 90% cost reduction on subsequent calls."""
    resp = client.messages.create(
        model=model,
        max_tokens=8000,
        system=[
            {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}
        ],
        messages=[{"role": "user", "content": user_message}],
    )
    text = resp.content[0].text
    # Strip optional ```json fences in case the model adds them anyway
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def build_user_message(entry, defaults):
    parts = [f"slug: {entry['slug']}", f"title: {entry['title']}", f"category: {entry['category']}"]
    if "language" in entry:
        parts.append(f"language: {entry['language']}")
    if "framework" in entry:
        parts.append(f"framework: {entry['framework']}")
    parts.append(f"brief: {entry.get('brief', '')}")
    if entry.get("tags"):
        parts.append(f"suggested tags: {', '.join(entry['tags'])}")
    if entry.get("best_for_tags"):
        parts.append(f"best-for tags: {', '.join(entry['best_for_tags'])}")
    if defaults.get("tested_with", {}).get("last_verified_date"):
        parts.append(f"set tested_with.last_verified_date to {defaults['tested_with']['last_verified_date']}")
    if defaults.get("license"):
        parts.append(f"use license: {defaults['license']}")
    parts.append("\nProduce the full v2 JSON record now.")
    return "\n".join(parts)


def generate_one(client, library, entry, defaults, model):
    sys_prompt = CODE_SYSTEM_PROMPT if library == "code" else PROMPT_SYSTEM_PROMPT
    user_msg = build_user_message(entry, defaults)
    try:
        record = call_anthropic(client, sys_prompt, user_msg, model=model)
        # ensure slug is preserved from manifest
        record["slug"] = entry["slug"]
        return record, None
    except Exception as e:
        return None, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--library", choices=["code", "prompt"], required=True)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--only", default="", help="comma-separated slugs to regenerate")
    ap.add_argument("--skip-existing", action="store_true", help="skip entries already in output file")
    ap.add_argument("--model", default=os.environ.get("MODEL", "claude-sonnet-4-20250514"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY required", file=sys.stderr)
        sys.exit(2)

    manifest = yaml.safe_load(pathlib.Path(args.manifest).read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    defaults = manifest.get("defaults", {})

    only = set(s.strip() for s in args.only.split(",") if s.strip())
    if only:
        entries = [e for e in entries if e["slug"] in only]

    existing = []
    existing_slugs = set()
    out_path = pathlib.Path(args.output)
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))
        if isinstance(existing, list):
            existing_slugs = {e.get("slug") for e in existing}

    if args.skip_existing:
        entries = [e for e in entries if e["slug"] not in existing_slugs]

    print(f"Library: {args.library}")
    print(f"Manifest entries to process: {len(entries)}")
    print(f"Model: {args.model}")
    print(f"Output: {args.output}")
    print(f"Concurrency: {args.concurrency}")

    if args.dry_run:
        for e in entries[:5]:
            print("---")
            print(build_user_message(e, defaults))
        return

    client = Anthropic(api_key=api_key)
    results = list(existing)  # preserve existing entries not being regenerated
    if only or args.skip_existing:
        # remove entries we're about to regenerate so updated records don't duplicate
        regen_slugs = {e["slug"] for e in entries}
        results = [r for r in results if r.get("slug") not in regen_slugs]

    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {
            ex.submit(generate_one, client, args.library, e, defaults, args.model): e
            for e in entries
        }
        done = 0
        for fut in concurrent.futures.as_completed(futures):
            entry = futures[fut]
            done += 1
            record, err = fut.result()
            if err:
                failed.append((entry["slug"], err))
                print(f"  [{done}/{len(entries)}] FAIL {entry['slug']}: {err[:100]}", flush=True)
            else:
                results.append(record)
                print(f"  [{done}/{len(entries)}] OK   {entry['slug']}", flush=True)

    # write atomic
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(out_path)

    print(f"\nDONE. Generated={len(entries) - len(failed)}, Failed={len(failed)}, Total in output={len(results)}")
    if failed:
        print("\nFailed slugs:")
        for slug, err in failed[:10]:
            print(f"  {slug}: {err[:200]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
