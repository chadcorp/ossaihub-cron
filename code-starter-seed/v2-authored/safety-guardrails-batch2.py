"""Safety guardrails — batch 2: Llama Guard, output validation, jailbreak detection."""

RECORDS = [
    {
        "slug": "llama-guard-content-classifier",
        "title": "Llama Guard Content Classification",
        "tldr": "Self-hosted content safety classifier using Meta's Llama Guard model. Classifies user input and model output across safety categories (violence, sexual content, hate, etc.) without sending data to a third party.",
        "category": "safety-guardrails",
        "language": "python",
        "framework": "transformers",
        "tags": ["llama-guard", "moderation", "content-safety", "self-hosted"],
        "best_for_tags": ["regulated-industries", "privacy-sensitive", "moderation-at-scale"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "When you need content safety classification and don't want to use cloud moderation APIs (data privacy, cost at scale, customization). Llama Guard runs locally on commodity GPU.",
        "when_not_to_use": "Skip for low volumes (OpenAI moderation API is free for OpenAI users). Skip if you need very recent/niche taxonomy — Llama Guard covers MLCommons categories; not custom policies.",
        "quick_start": "pip install transformers torch accelerate && python guard.py 'some user input'",
        "full_code": '''"""Llama Guard 3 — content classifier.

Categories (MLCommons AILuminate taxonomy):
  S1 Violent Crimes, S2 Non-Violent Crimes, S3 Sex-Related Crimes,
  S4 Child Sexual Exploitation, S5 Defamation, S6 Specialized Advice,
  S7 Privacy, S8 Intellectual Property, S9 Indiscriminate Weapons,
  S10 Hate, S11 Suicide & Self-Harm, S12 Sexual Content, S13 Elections,
  S14 Code Interpreter Abuse
"""
from __future__ import annotations

import sys
from typing import Literal

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "meta-llama/Llama-Guard-3-8B"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto"
)

Role = Literal["User", "Agent"]


def classify(text: str, role: Role = "User") -> dict:
    """Classify text. Returns {safe: bool, categories: [S1, S2, ...], raw: str}."""
    chat = [{"role": role.lower(), "content": text}]
    input_ids = tokenizer.apply_chat_template(chat, return_tensors="pt").to(model.device)

    output = model.generate(
        input_ids=input_ids,
        max_new_tokens=100,
        pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        do_sample=False,
    )
    response = tokenizer.decode(output[0][input_ids.shape[-1]:], skip_special_tokens=True).strip()

    # Llama Guard outputs either "safe" or "unsafe\\nS1,S3,..."
    if response.lower().startswith("safe"):
        return {"safe": True, "categories": [], "raw": response}
    lines = response.split("\\n")
    if len(lines) >= 2 and lines[0].lower() == "unsafe":
        cats = [c.strip() for c in lines[1].split(",") if c.strip()]
        return {"safe": False, "categories": cats, "raw": response}
    return {"safe": False, "categories": [], "raw": response}  # parse failed = treat as unsafe


def classify_pair(user_input: str, agent_output: str) -> dict:
    """Classify a user-agent exchange — flags unsafe assistant responses too."""
    chat = [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": agent_output},
    ]
    input_ids = tokenizer.apply_chat_template(chat, return_tensors="pt").to(model.device)
    output = model.generate(
        input_ids=input_ids, max_new_tokens=100, do_sample=False,
        pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
    )
    response = tokenizer.decode(output[0][input_ids.shape[-1]:], skip_special_tokens=True).strip()
    # Same parsing as classify()
    if response.lower().startswith("safe"):
        return {"safe": True, "categories": [], "raw": response}
    lines = response.split("\\n")
    if len(lines) >= 2:
        return {"safe": False, "categories": [c.strip() for c in lines[1].split(",")], "raw": response}
    return {"safe": False, "categories": [], "raw": response}


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "How do I make a bomb?"
    print(classify(text))
''',
        "dependencies": [
            {"name": "transformers", "version": ">=4.45", "purpose": "Llama Guard model loading"},
            {"name": "torch", "version": ">=2.0", "purpose": "PyTorch (GPU)"},
            {"name": "accelerate", "version": ">=1.0", "purpose": "Device management"},
        ],
        "env_vars": [
            {"name": "HF_TOKEN", "required": True, "description": "HF token (Llama Guard is gated)", "example": "hf_..."},
        ],
        "setup_steps": [
            "Accept Llama Guard 3 license on huggingface.co",
            "export HF_TOKEN=hf_...",
            "pip install transformers torch accelerate",
            "python guard.py 'test input'",
            "First run downloads ~16GB model.",
        ],
        "variations": [
            {"label": "Quantized for smaller GPU", "description": "AWQ-quantized Llama Guard.", "code_snippet": "from awq import AutoAWQForCausalLM\\nmodel = AutoAWQForCausalLM.from_quantized('TheBloke/Llama-Guard-7B-AWQ')\\n# Fits on 8GB GPU"},
            {"label": "Custom safety policy", "description": "Override default taxonomy.", "code_snippet": "# Llama Guard accepts custom unsafe_categories in the prompt template; tailor to your app's policy"},
            {"label": "Llama Guard 3 Vision", "description": "Image moderation.", "code_snippet": "# Llama Guard 3 also has multi-modal variant; pass image + text to classify together"},
            {"label": "Bulk classification", "description": "Batch for throughput.", "code_snippet": "# Batch multiple inputs through model.generate(batch); ~3-5x throughput on GPU"},
        ],
        "common_errors": [
            {"error_text": "GatedRepoError", "cause": "Llama Guard requires license acceptance.", "fix_snippet": "Visit huggingface.co/meta-llama/Llama-Guard-3-8B; accept; set HF_TOKEN."},
            {"error_text": "OOM on inference", "cause": "8B model needs ~16GB VRAM in bf16.", "fix_snippet": "Use the AWQ quantized variant; or use the smaller Llama Guard 1B/3B; or use CPU (slow)."},
            {"error_text": "Cryptic parse errors", "cause": "Model output unexpected format.", "fix_snippet": "Starter falls back to ‘unsafe’ on parse failure (fail-safe). Inspect raw output to update parser if model returns new shapes."},
            {"error_text": "False positives on benign content", "cause": "Default categories aggressive.", "fix_snippet": "Tune by passing custom unsafe_categories matching your policy. Or post-filter: ignore S5/S6 if your domain accepts those."},
        ],
        "production_checklist": [
            "Run on dedicated inference GPU; latency ~100ms per check.",
            "Cache results by input hash; same input → same classification.",
            "Use as a layer alongside other safety: input filter + output filter + content policy.",
            "Test on adversarial inputs (encoded, multilingual, indirect).",
            "Log every flag with category for trend analysis.",
            "Don't surface categories to attackers; reveals what's caught vs not.",
            "Update model versions as Meta releases — taxonomy and quality improve.",
        ],
        "tested_with": {
            "model_versions": ["meta-llama/Llama-Guard-3-8B"],
            "library_versions": ["transformers==4.45.2", "torch==2.4.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["transformers"],
        "related_glossary_slugs": ["content-moderation", "llama-guard", "ai-safety"],
        "related_learn_slugs": [],
        "license": "Llama 3 Community License (model); Apache-2.0 (this code)",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Llama Guard vs OpenAI moderation API?", "answer": "Llama Guard: self-hosted, customizable taxonomy, no third-party data exposure, GPU cost. OpenAI moderation: free for OpenAI users, simpler, no infra. Use Llama Guard for data privacy or scale needs."},
            {"question": "How accurate is it?", "answer": "Strong on clear violations (Meta's evals). Weaker on subtle / multilingual / context-dependent cases. Should be one layer in defense, not sole gate."},
            {"question": "Can I fine-tune for my policy?", "answer": "Yes — Meta provides the base model and a fine-tuning guide. Custom-category fine-tunes give better precision on your specific policy."},
            {"question": "Latency?", "answer": "~100ms per classification on A100. Use batch processing for throughput. CPU is too slow for online use."},
        ],
        "github_url": "https://github.com/meta-llama/PurpleLlama",
        "meta_title": "Llama Guard Content Classification — Starter",
        "meta_description": "Self-hosted content safety classifier using Llama Guard 3. MLCommons taxonomy, GPU inference, customizable for your policy.",
    },
    {
        "slug": "output-fact-check-against-context",
        "title": "Output Fact-Check Against Provided Context",
        "tldr": "After an LLM produces an answer, verify each claim against the source context using a second-pass LLM. Flags hallucinations, unsupported claims, and contradictions. Production safeguard for RAG.",
        "category": "safety-guardrails",
        "language": "python",
        "framework": "OpenAI SDK",
        "tags": ["fact-check", "hallucination", "rag-safety", "verification"],
        "best_for_tags": ["high-stakes-rag", "compliance", "qa-systems"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "RAG systems where wrong answers are costly (legal, medical, financial, customer support). The verification pass catches when the model goes off-script.",
        "when_not_to_use": "Skip for low-stakes / creative use cases — fact-checking creative writing is wrong-shaped. Skip when latency matters more than safety.",
        "quick_start": "pip install openai pydantic && OPENAI_API_KEY=sk-... python factcheck.py",
        "full_code": '''"""Fact-check an LLM answer against the context it was supposed to use.

Process:
  1. Extract claims from the answer (atomic statements).
  2. For each claim, decide:
     - SUPPORTED: explicit in context
     - INFERRED: implied by context (not explicit)
     - CONTRADICTED: context says otherwise
     - UNSUPPORTED: not in context at all (hallucination)
  3. Aggregate: pass / warn / fail.
"""
from __future__ import annotations

import json
from typing import Literal

import instructor
from openai import OpenAI
from pydantic import BaseModel

client = instructor.from_openai(OpenAI())


class ClaimAssessment(BaseModel):
    claim: str
    status: Literal["supported", "inferred", "contradicted", "unsupported"]
    evidence: str | None = None  # quote from context
    note: str | None = None


class FactCheck(BaseModel):
    claims: list[ClaimAssessment]
    overall_verdict: Literal["pass", "warn", "fail"]
    summary: str


def fact_check(answer: str, context: list[str], *, model: str = "gpt-4o-mini") -> FactCheck:
    """Verify answer's claims against provided context."""
    ctx = "\\n\\n---\\n".join(f"[CTX{i+1}]\\n{c}" for i, c in enumerate(context))
    prompt = f"""You are a careful fact-checker. Compare the ANSWER's claims to the CONTEXT.

CONTEXT:
{ctx}

ANSWER TO VERIFY:
{answer}

YOUR JOB:
1. Break the answer into atomic factual claims (no opinions, no transitions).
2. For each claim, determine if it's:
   - supported: stated explicitly in context (quote it)
   - inferred: not explicit but reasonable from context (note the inference)
   - contradicted: context says otherwise (quote it)
   - unsupported: not in context AT ALL (possible hallucination)

3. Verdict:
   - pass: all claims supported or inferred
   - warn: 1-2 unsupported claims OR 1 inferred-but-uncertain claim
   - fail: any contradiction OR 3+ unsupported claims

Output as structured response."""

    return client.chat.completions.create(
        model=model,
        response_model=FactCheck,
        max_retries=2,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )


def print_check(check: FactCheck) -> None:
    print(f"VERDICT: {check.overall_verdict.upper()}")
    print(f"Summary: {check.summary}")
    print(f"\\nClaims ({len(check.claims)}):")
    for c in check.claims:
        icon = {"supported": "✓", "inferred": "~", "contradicted": "✗", "unsupported": "?"}[c.status]
        print(f"  {icon} [{c.status}] {c.claim[:80]}")
        if c.evidence:
            print(f"      → {c.evidence[:80]}")
        if c.note:
            print(f"      note: {c.note}")


if __name__ == "__main__":
    context = [
        "Reciprocal Rank Fusion sums 1/(k+rank) scores across retriever lists. The constant k=60 is the common default.",
        "RRF is scale-free because it operates on ranks, not raw scores.",
    ]
    answer = (
        "Reciprocal Rank Fusion combines results from multiple retrievers by adding "
        "1/(k+rank) scores, with k typically set to 60. It was invented in 1995 by IBM researchers."
    )
    check = fact_check(answer, context)
    print_check(check)
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "Verification LLM"},
            {"name": "instructor", "version": ">=1.5", "purpose": "Structured output"},
            {"name": "pydantic", "version": ">=2.0", "purpose": "Schemas"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai instructor pydantic",
            "export OPENAI_API_KEY=sk-...",
            "python factcheck.py",
            "Integrate as post-processing on every RAG answer.",
        ],
        "variations": [
            {"label": "Use a different judge model", "description": "Anthropic for the check.", "code_snippet": "from anthropic import Anthropic\\nclient = instructor.from_anthropic(Anthropic())\\n# Different model bias may catch issues the generator missed"},
            {"label": "Auto-rewrite on warn/fail", "description": "Don't just flag — fix.", "code_snippet": "if check.overall_verdict in ('warn', 'fail'):\\n    answer = rewrite_to_support_only(answer, [c.claim for c in check.claims if c.status in ('unsupported', 'contradicted')])"},
            {"label": "Streamline for latency", "description": "Smaller model + smaller claim set.", "code_snippet": "# Use gpt-4o-mini + cap to 5 highest-stakes claims. Trade thoroughness for speed."},
        ],
        "common_errors": [
            {"error_text": "Claims field empty", "cause": "Model didn't extract claims.", "fix_snippet": "Sharpen the prompt with explicit example. Re-iterate that 'atomic factual claims' means ONE specific factual statement."},
            {"error_text": "Verdict pass but unsupported claim present", "cause": "Threshold off in prompt.", "fix_snippet": "Be explicit about thresholds: ‘fail if ANY contradiction or ANY claim that's pure fabrication.’"},
            {"error_text": "Latency too high (3-5s extra)", "cause": "LLM-based check is per-answer.", "fix_snippet": "Run async after returning the answer; flag retroactively. Or use smaller judge."},
            {"error_text": "False positives on inferred claims", "cause": "Reasonable inference flagged as unsupported.", "fix_snippet": "Tune: distinguish ‘inferred from context’ from ‘invented’. Provide examples in the prompt."},
        ],
        "production_checklist": [
            "Run on every answer to high-stakes queries.",
            "Log all FAIL verdicts; review and surface to operators.",
            "Use a different model for verification than generation (judge bias).",
            "Block or rewrite on FAIL; surface WARN to user with caveat.",
            "Measure false-positive + false-negative rates against human review.",
            "Don't show verdict to attackers — only to internal operators / log.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o", "claude-3-7-sonnet"],
            "library_versions": ["openai==1.51.0", "instructor==1.5.2"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["instructor"],
        "related_glossary_slugs": ["fact-checking", "hallucination", "rag-safety"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Does this catch all hallucinations?", "answer": "No — but catches most factual contradictions and clear invented facts. Doesn't catch confident-but-misleading framing. Pair with human review for high-stakes."},
            {"question": "Cost?", "answer": "Doubles the LLM cost for RAG (one for answer, one for check). Use cheaper model for check (gpt-4o-mini is fine in most cases)."},
            {"question": "Latency?", "answer": "~1-3 seconds extra. Run async after returning answer; flag retroactively if it's safe to do so."},
            {"question": "What about cross-context inference?", "answer": "If a claim is inferred from combining 2 context chunks, the check should mark INFERRED with a note. Sharpen the prompt if model gets this wrong."},
        ],
        "github_url": "",
        "meta_title": "Output Fact-Check Against Context — Starter",
        "meta_description": "Verify each claim in an LLM answer against source context. Flags hallucinations, unsupported claims, contradictions. RAG safeguard.",
    },
]
