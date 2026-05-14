"""LLM client starters — batch 2: multi-provider, fallback, streaming."""

RECORDS = [
    {
        "slug": "litellm-multi-provider-router",
        "title": "LiteLLM Multi-Provider Router With Fallback",
        "tldr": "Use LiteLLM to call OpenAI, Anthropic, Gemini, Bedrock, Together, etc. through a single interface, with automatic fallback when the primary provider fails or rate-limits.",
        "category": "llm-clients",
        "language": "python",
        "framework": "LiteLLM",
        "tags": ["litellm", "multi-provider", "fallback", "routing"],
        "best_for_tags": ["high-availability", "cost-optimization", "provider-agnostic"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When you want one client to call any provider — and especially when you want automatic failover during outages. LiteLLM speaks OpenAI's API surface; production code only changes provider strings.",
        "when_not_to_use": "Skip when you only use one provider and won't switch (adds dependency for no benefit). Skip if you need provider-specific features the abstraction hides.",
        "quick_start": "pip install litellm && OPENAI_API_KEY=... ANTHROPIC_API_KEY=... python router.py",
        "full_code": '''"""LiteLLM router: call any provider, fallback automatically.

Patterns covered:
  1. Direct call — provider in model string
  2. Cost-aware routing — try cheap model, fall back to better one
  3. Outage failover — provider A → provider B → provider C
"""
from __future__ import annotations

import os

import litellm
from litellm import completion, Router


# ----------------- PATTERN 1: Direct call -----------------

def direct_call(prompt: str, model: str = "gpt-4o-mini") -> str:
    """LiteLLM accepts model strings: 'openai/gpt-4o', 'anthropic/claude-3-7-sonnet-latest', 'gemini/gemini-1.5-pro', 'bedrock/anthropic.claude-3-sonnet-20240229', etc."""
    resp = completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return resp.choices[0].message.content


# ----------------- PATTERN 2: Router with fallbacks -----------------

# Router maintains a model list with priority + fallback chains
router = Router(
    model_list=[
        {
            "model_name": "smart-agent",
            "litellm_params": {
                "model": "openai/gpt-4o-mini",
                "api_key": os.environ.get("OPENAI_API_KEY"),
            },
        },
        {
            "model_name": "smart-agent",        # same logical name = pool
            "litellm_params": {
                "model": "anthropic/claude-3-5-haiku-latest",
                "api_key": os.environ.get("ANTHROPIC_API_KEY"),
            },
        },
        {
            "model_name": "smart-agent",
            "litellm_params": {
                "model": "gemini/gemini-1.5-flash",
                "api_key": os.environ.get("GEMINI_API_KEY"),
            },
        },
    ],
    fallbacks=[
        {"smart-agent": ["smart-agent"]},  # within pool, try next on failure
    ],
    num_retries=2,
    timeout=30,
    routing_strategy="simple-shuffle",      # or "least-busy", "latency-based", "usage-based"
)


def routed_call(prompt: str) -> str:
    """Route 'smart-agent' across the pool with automatic failover."""
    resp = router.completion(
        model="smart-agent",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


# ----------------- PATTERN 3: Cost-aware tiered fallback -----------------

def tiered_call(prompt: str, *, tier_started: str = "cheap") -> tuple[str, str]:
    """Try cheap model first; escalate to expensive if it 'fails' (defined as: too short response or explicit refusal).

    Returns (response, which_model_succeeded).
    """
    tiers = ["openai/gpt-4o-mini", "openai/gpt-4o", "anthropic/claude-3-7-sonnet-latest"]
    for model in tiers:
        try:
            resp = completion(model=model, messages=[{"role": "user", "content": prompt}], temperature=0)
            content = resp.choices[0].message.content or ""
            # Heuristic: response under 20 chars and contains 'sorry' or 'cannot' -> escalate
            if len(content) < 20 and ("sorry" in content.lower() or "cannot" in content.lower()):
                continue
            return content, model
        except Exception as e:
            print(f"{model} failed: {e}")
            continue
    return "ALL TIERS FAILED", "none"


# ----------------- PATTERN 4: Cost tracking -----------------

def call_with_cost(prompt: str, model: str = "gpt-4o-mini") -> dict:
    resp = completion(model=model, messages=[{"role": "user", "content": prompt}])
    cost = litellm.completion_cost(completion_response=resp)
    return {
        "content": resp.choices[0].message.content,
        "model": resp.model,
        "tokens": resp.usage.total_tokens,
        "cost_usd": cost,
    }


if __name__ == "__main__":
    print("---- direct ----")
    print(direct_call("What is RAG?"))

    print("\\n---- routed (with fallback) ----")
    print(routed_call("What is RAG?"))

    print("\\n---- tiered ----")
    response, model = tiered_call("Explain attention in one paragraph")
    print(f"{model}: {response[:100]}...")

    print("\\n---- with cost ----")
    info = call_with_cost("hello")
    print(info)
''',
        "dependencies": [
            {"name": "litellm", "version": ">=1.50", "purpose": "Multi-provider LLM client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": False, "description": "OpenAI key", "example": "sk-..."},
            {"name": "ANTHROPIC_API_KEY", "required": False, "description": "Anthropic key", "example": "sk-ant-..."},
            {"name": "GEMINI_API_KEY", "required": False, "description": "Gemini key", "example": "AIza..."},
        ],
        "setup_steps": [
            "pip install litellm",
            "Set env vars for the providers you want available.",
            "python router.py",
            "Inspect litellm logs to verify routing decisions.",
        ],
        "variations": [
            {
                "label": "Local Ollama in the fallback chain",
                "description": "Add local model as last resort.",
                "code_snippet": "{'model_name': 'smart-agent', 'litellm_params': {'model': 'ollama/llama3.1', 'api_base': 'http://localhost:11434'}}",
            },
            {
                "label": "Latency-based routing",
                "description": "Route to fastest responder.",
                "code_snippet": "routing_strategy='latency-based'  # LiteLLM tracks per-model latency",
            },
            {
                "label": "LiteLLM proxy",
                "description": "Run as a standalone proxy server.",
                "code_snippet": "litellm --model gpt-4o --port 4000\\n# Any OpenAI-compatible client can now hit http://localhost:4000",
            },
            {
                "label": "Cost cap per request",
                "description": "Reject requests exceeding budget.",
                "code_snippet": "completion(..., max_tokens=500, mock_response='', cost_threshold=0.01)",
            },
        ],
        "common_errors": [
            {
                "error_text": "AuthenticationError: api_key not set",
                "cause": "Env var missing for that provider.",
                "fix_snippet": "Set OPENAI_API_KEY / ANTHROPIC_API_KEY / etc. for each provider in your fallback chain.",
            },
            {
                "error_text": "All fallback providers fail",
                "cause": "Network issue or all credentials wrong.",
                "fix_snippet": "Check `litellm._turn_on_debug()` for detailed error per provider. Include at least one local fallback (Ollama) for full outage resilience.",
            },
            {
                "error_text": "Cost calculation wrong",
                "cause": "Pricing data stale.",
                "fix_snippet": "Upgrade litellm regularly; or override with custom prices in completion_cost call.",
            },
            {
                "error_text": "Routing biased toward one provider",
                "cause": "simple-shuffle has memory between calls within a process.",
                "fix_snippet": "Use 'least-busy' for true round-robin under load; 'simple-shuffle' is fine for low QPS.",
            },
        ],
        "production_checklist": [
            "Pin LiteLLM version; provider abstractions shift.",
            "Test failover by killing each provider in turn.",
            "Track which provider served which request for cost analysis.",
            "Set per-provider timeouts; slow primary shouldn't block falling back.",
            "Use the proxy mode if multiple services need the same routing config.",
            "Monitor cost via completion_cost; surprises happen with provider price changes.",
            "Test prompt portability — providers respond differently; outputs differ subtly.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "claude-3-5-haiku", "gemini-1.5-flash"],
            "library_versions": ["litellm==1.50.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["litellm"],
        "related_glossary_slugs": ["provider-routing", "fallback", "litellm"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Does LiteLLM lock me in?",
                "answer": "Less than going single-provider. API shape is OpenAI's — switching from LiteLLM to OpenAI SDK is a small change. The value is in unified syntax across providers.",
            },
            {
                "question": "Performance overhead?",
                "answer": "Minimal — LiteLLM is a thin client wrapper. Routing decisions add a few ms; HTTP calls dominate.",
            },
            {
                "question": "How do I get LiteLLM proxy in production?",
                "answer": "Run as a service (Docker). Frontends point to it. Centralized routing, caching, rate limits, observability all in one place.",
            },
            {
                "question": "Does it support tool/function calling?",
                "answer": "Yes — same API as OpenAI tools. LiteLLM translates per provider. Verify with the specific feature you need; nuances differ.",
            },
        ],
        "github_url": "https://github.com/BerriAI/litellm",
        "meta_title": "LiteLLM Multi-Provider Router — Starter",
        "meta_description": "Call OpenAI, Anthropic, Gemini, Bedrock through one client; automatic fallback on failure; cost tracking; latency-based routing.",
    },
    {
        "slug": "gemini-grounded-search",
        "title": "Gemini With Grounded Web Search",
        "tldr": "Use Gemini 1.5/2.0 with grounding enabled — model answers grounded in fresh web search results, with citations. Built-in alternative to RAG for general-knowledge queries.",
        "category": "llm-clients",
        "language": "python",
        "framework": "Google GenAI SDK",
        "tags": ["gemini", "grounding", "search", "citations"],
        "best_for_tags": ["current-events", "fact-checking", "no-rag"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When you need answers grounded in current information without building your own RAG. Gemini's native grounding hits Google Search and returns citations.",
        "when_not_to_use": "Skip for private/internal data (Gemini grounding goes to public web). Skip when you need precise control over sources — citations are Google-chosen.",
        "quick_start": "pip install google-genai && GOOGLE_API_KEY=... python grounded.py 'latest revenue for company X'",
        "full_code": '''"""Gemini with grounded web search.

The model is allowed to perform Google searches as a tool; responses
come back with grounding metadata listing the sources.
"""
from __future__ import annotations

import os
import sys

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


def grounded_answer(query: str, *, model: str = "gemini-1.5-pro-latest") -> dict:
    """Returns dict with answer text + citations."""
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()  # enables grounded search
    )

    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        temperature=0,
    )

    response = client.models.generate_content(
        model=model,
        contents=query,
        config=config,
    )

    # Extract citations from grounding metadata
    citations = []
    if response.candidates and response.candidates[0].grounding_metadata:
        meta = response.candidates[0].grounding_metadata
        if meta.grounding_chunks:
            for chunk in meta.grounding_chunks:
                if chunk.web:
                    citations.append({
                        "title": chunk.web.title,
                        "url": chunk.web.uri,
                    })

    return {
        "answer": response.text,
        "citations": citations,
        "search_queries_used": (
            meta.web_search_queries if response.candidates and response.candidates[0].grounding_metadata else []
        ),
    }


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "What are the most recent OSS AI tools released in 2026?"
    result = grounded_answer(query)
    print("\\n=== ANSWER ===")
    print(result["answer"])
    print("\\n=== CITATIONS ===")
    for c in result["citations"]:
        print(f"- {c['title']}: {c['url']}")
    print("\\n=== SEARCH QUERIES USED ===")
    for q in result["search_queries_used"]:
        print(f"- {q}")
''',
        "dependencies": [
            {"name": "google-genai", "version": ">=0.3", "purpose": "Google Generative AI SDK"},
        ],
        "env_vars": [
            {"name": "GOOGLE_API_KEY", "required": True, "description": "Google API key with Generative AI enabled", "example": "AIza..."},
        ],
        "setup_steps": [
            "Sign up at ai.google.dev; create API key.",
            "pip install google-genai",
            "export GOOGLE_API_KEY=AIza...",
            "python grounded.py 'your query'",
        ],
        "variations": [
            {
                "label": "Vertex AI version",
                "description": "Use Google Cloud's Vertex AI instead of consumer API.",
                "code_snippet": "client = genai.Client(vertexai=True, project='your-project', location='us-central1')",
            },
            {
                "label": "With output schema",
                "description": "Structured output + grounding.",
                "code_snippet": "config = types.GenerateContentConfig(tools=[grounding_tool], response_mime_type='application/json', response_schema=YourSchema)",
            },
            {
                "label": "Multi-turn",
                "description": "Keep conversation context with grounding.",
                "code_snippet": "chat = client.chats.create(model='gemini-1.5-pro-latest', config=config)\\nresp = chat.send_message(query)",
            },
        ],
        "common_errors": [
            {
                "error_text": "PermissionDenied: grounding not available",
                "cause": "API key doesn't have grounding feature, or wrong tier.",
                "fix_snippet": "Check ai.google.dev to ensure grounding is enabled for your project. May require paid tier.",
            },
            {
                "error_text": "Empty citations despite grounded query",
                "cause": "Model answered from training data (didn't need search).",
                "fix_snippet": "Not an error — Gemini decides when to search. If you always want search, prepend ‘Use web search to find:’ to query.",
            },
            {
                "error_text": "Cost higher than expected",
                "cause": "Grounded calls cost extra (Google Search API charge).",
                "fix_snippet": "Track grounded vs non-grounded usage. Use grounding only for queries that need fresh info; cache results.",
            },
            {
                "error_text": "Stale citations (linked page changed)",
                "cause": "Citations are URLs at time of search; pages change.",
                "fix_snippet": "Capture key info from citations into your own store with timestamps. URLs are evidence, not permanent records.",
            },
        ],
        "production_checklist": [
            "Cache grounded responses; same query within minutes shouldn't re-search.",
            "Display citations to users; transparency matters.",
            "Filter citations through allowlists if you need source quality control.",
            "Set timeouts; grounding adds latency.",
            "Monitor grounding cost separately from base model cost.",
            "Handle empty-citations gracefully (model answered without search).",
            "For private data, use RAG instead — grounding is public web only.",
        ],
        "tested_with": {
            "model_versions": ["gemini-1.5-pro-latest", "gemini-2.0-flash-exp"],
            "library_versions": ["google-genai==0.3.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["google-genai"],
        "related_glossary_slugs": ["grounding", "rag", "citation"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Gemini grounding vs custom RAG?",
                "answer": "Grounding: zero setup, public web only, fresh. Custom RAG: setup overhead, your data + controllable sources. Use both — grounding for general knowledge, RAG for your domain.",
            },
            {
                "question": "Is OpenAI's web_search comparable?",
                "answer": "OpenAI added web_search tool in 2024. Similar concept; different implementation. Gemini's tighter integration with Google Search has stronger results for general queries; OpenAI's is improving.",
            },
            {
                "question": "Can I limit search to certain sites?",
                "answer": "Not directly via the API. Workaround: prompt the model to focus on certain domains (‘prioritize results from .gov and .edu’). Imperfect but helps.",
            },
            {
                "question": "Cost per query?",
                "answer": "Gemini API costs plus the grounding fee. Roughly 2-3x non-grounded cost. Check ai.google.dev/pricing for current rates.",
            },
        ],
        "github_url": "https://github.com/googleapis/python-genai",
        "meta_title": "Gemini With Grounded Web Search — Starter",
        "meta_description": "Gemini with Google Search grounding: answers backed by fresh web results, citations in metadata. Native alternative to RAG for public knowledge.",
    },
]
