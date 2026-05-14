"""Evaluation starters — Promptfoo, RAGAS, LLM-as-judge, regression suites."""

RECORDS = [
    {
        "slug": "llm-as-judge-pairwise",
        "title": "LLM-as-Judge Pairwise Evaluator With Position Bias Mitigation",
        "tldr": "Pairwise LLM judge for comparing two model outputs against the same prompt. Mitigates position bias by running both orderings and detecting flips. Includes rubric-based scoring.",
        "category": "evaluation",
        "language": "python",
        "framework": "OpenAI SDK",
        "tags": ["evaluation", "llm-judge", "pairwise", "regression"],
        "best_for_tags": ["prompt-evaluation", "model-comparison", "regression-tests"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When you need to evaluate which of two LLM outputs is better, without ground-truth labels. Useful for prompt iteration (‘did my new prompt do better than the old one?’) and model comparison.",
        "when_not_to_use": "Skip when ground-truth answers exist (use exact-match or numerical metrics). Skip for safety-critical eval — LLM judges have biases and shouldn't be the final word.",
        "quick_start": "pip install openai && OPENAI_API_KEY=sk-... python judge.py",
        "full_code": '''"""Pairwise LLM-as-judge with position bias mitigation.

For each (prompt, response_A, response_B) tuple, we ask the judge twice:
  1. (A, B) -> verdict_1
  2. (B, A) -> verdict_2

If verdicts disagree, that's a 'flip' — judge is order-dependent on this case
and should be treated as a tie.

Returns aggregate win rates across many cases, with confidence intervals.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from typing import Literal

from openai import OpenAI

client = OpenAI()

Verdict = Literal["A", "B", "tie"]

JUDGE_SYSTEM = """You are evaluating two responses to the same prompt.

Use this rubric, in order:
1. CORRECTNESS — does the response actually answer the prompt?
2. COMPLETENESS — does it cover what was asked?
3. CLARITY — is it well-organized and easy to follow?
4. STYLE — appropriate tone and length?

Return exactly: VERDICT: A / B / tie, plus a one-line reason.
A means Response A is better. tie means they're effectively equal."""


@dataclass
class Case:
    prompt: str
    response_a: str
    response_b: str


@dataclass
class Result:
    case_index: int
    verdict_ab: Verdict
    verdict_ba: Verdict
    flipped: bool
    final: Verdict  # tie if flipped, otherwise the consistent verdict


def _judge(prompt: str, first: str, second: str, *, model: str = "gpt-4o-mini") -> Verdict:
    user = f"""PROMPT:
{prompt}

RESPONSE A:
{first}

RESPONSE B:
{second}"""

    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user},
        ],
    )
    text = (resp.choices[0].message.content or "").upper()
    if "VERDICT: A" in text or "VERDICT:A" in text:
        return "A"
    if "VERDICT: B" in text or "VERDICT:B" in text:
        return "B"
    return "tie"


def evaluate(cases: list[Case], *, model: str = "gpt-4o-mini") -> dict:
    results: list[Result] = []
    for i, c in enumerate(cases):
        v1 = _judge(c.prompt, c.response_a, c.response_b, model=model)  # A first
        v2 = _judge(c.prompt, c.response_b, c.response_a, model=model)  # B first
        # Translate v2 back to A/B perspective
        v2_translated: Verdict = {"A": "B", "B": "A", "tie": "tie"}[v2]
        flipped = v1 != v2_translated
        final = "tie" if flipped else v1
        results.append(Result(i, v1, v2_translated, flipped, final))

    # Aggregate
    n = len(results)
    wins_a = sum(1 for r in results if r.final == "A")
    wins_b = sum(1 for r in results if r.final == "B")
    ties = sum(1 for r in results if r.final == "tie")
    flips = sum(1 for r in results if r.flipped)

    # Wilson 95% CI for A's win rate (only over non-tie cases)
    non_tie = wins_a + wins_b
    a_rate = wins_a / non_tie if non_tie else 0.0
    ci_low, ci_high = _wilson_ci(wins_a, non_tie) if non_tie else (0.0, 0.0)

    return {
        "n_cases": n,
        "wins_a": wins_a,
        "wins_b": wins_b,
        "ties": ties,
        "flips_position_bias": flips,
        "a_win_rate_over_non_ties": round(a_rate, 3),
        "ci_95": (round(ci_low, 3), round(ci_high, 3)),
        "verdict": "A is meaningfully better" if ci_low > 0.55 else
                   "B is meaningfully better" if ci_high < 0.45 else
                   "no significant difference",
        "details": [r.__dict__ for r in results],
    }


def _wilson_ci(wins: int, n: int, *, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0, 0)
    p = wins / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0, center - margin), min(1, center + margin))


if __name__ == "__main__":
    cases = [
        Case(
            prompt="Explain Reciprocal Rank Fusion in one paragraph.",
            response_a="RRF combines ranked lists by adding 1/(k+rank) scores.",
            response_b="Reciprocal Rank Fusion (RRF) merges ranking from multiple retrievers. Each document's final score is the sum of 1/(k+rank) across all lists; k is a smoothing constant, often 60. It's robust because it works on ranks rather than raw scores, so heterogeneous retrievers can be fused without normalization."
        ),
    ]
    print(json.dumps(evaluate(cases), indent=2, default=str))
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "Judge LLM client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI API key for judge", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install openai",
            "export OPENAI_API_KEY=sk-...",
            "Build a list[Case] with your prompt and the two responses to compare.",
            "python judge.py",
        ],
        "variations": [
            {
                "label": "Use Claude as judge",
                "description": "Different judge may bias differently.",
                "code_snippet": "# In production, run with two different judges (gpt-4o + claude-3-7-sonnet); only count agreement as 'meaningful'.",
            },
            {
                "label": "Stronger judge",
                "description": "Use gpt-4o for the judge, not -mini.",
                "code_snippet": "evaluate(cases, model='gpt-4o')  # ~2-3x cost, more reliable on subjective rubrics",
            },
            {
                "label": "Custom rubric per task",
                "description": "Different judge prompt for different tasks.",
                "code_snippet": "JUDGE_SYSTEM_CODE = '''You are evaluating code. Rubric: correctness > readability > efficiency. ...'''",
            },
            {
                "label": "Parallel evaluation",
                "description": "Run judgments concurrently with asyncio.",
                "code_snippet": "import asyncio\\nfrom openai import AsyncOpenAI\\n# Use asyncio.gather to run all _judge calls in parallel; respect rate limits.",
            },
        ],
        "common_errors": [
            {
                "error_text": "All verdicts come back as 'tie'",
                "cause": "Rubric not focused enough; judge defaults to safe-tie.",
                "fix_snippet": "Tighten rubric: prefer rubric items the responses MEASURABLY differ on. Add: 'If both responses are competent, pick the one with more concrete detail.'",
            },
            {
                "error_text": "Position bias rate > 30%",
                "cause": "Judge model is too weak to evaluate this task.",
                "fix_snippet": "Switch to gpt-4o or claude-3-7-sonnet as judge. Position bias correlates with judge weakness.",
            },
            {
                "error_text": "Judge keeps disagreeing with humans",
                "cause": "Rubric criteria mismatch human preferences.",
                "fix_snippet": "Calibrate: hand-judge 20 cases, compare to LLM judge. Adjust rubric to match human verdicts; re-run.",
            },
            {
                "error_text": "Cannot parse verdict from judge response",
                "cause": "Judge wrote prose instead of structured output.",
                "fix_snippet": "Add to JUDGE_SYSTEM: 'YOUR LAST LINE MUST BE: VERDICT: A or VERDICT: B or VERDICT: tie'. Or use structured outputs (json_schema).",
            },
        ],
        "production_checklist": [
            "Always run both orderings — never trust a one-shot pairwise judgment.",
            "Use Wilson CI not normal-approximation; small samples need it.",
            "Track flip rate as a quality metric of the judge itself.",
            "Calibrate against a human-judged sample before trusting aggregate results.",
            "Different judge for different task types; one rubric doesn't fit all.",
            "Save raw judge responses for audit — verdicts alone hide why.",
            "Never use the same model as both response generator AND judge for production decisions.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o", "claude-3-7-sonnet"],
            "library_versions": ["openai==1.51.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["promptfoo", "langfuse"],
        "related_glossary_slugs": ["llm-as-judge", "evaluation", "position-bias"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Is LLM-judging reliable?",
                "answer": "Reliable enough to detect large quality differences (10%+ gap in win rate). Less reliable for small differences. Always calibrate against humans for important decisions.",
            },
            {
                "question": "How many cases do I need?",
                "answer": "30 minimum for any meaningful CI. 100+ if you expect small differences. Run preliminary 30; if CI is wide, run more.",
            },
            {
                "question": "Why pairwise vs absolute scoring?",
                "answer": "LLMs are much better at comparing two outputs than at scoring one. Pairwise eliminates calibration drift across rubric items.",
            },
            {
                "question": "Can I use this for A/B testing prompts in production?",
                "answer": "Use it offline against a held-out test set first. In production, use real user metrics — LLM judges are proxies, not ground truth.",
            },
        ],
        "github_url": "",
        "meta_title": "LLM-as-Judge Pairwise Evaluator — Starter",
        "meta_description": "Pairwise LLM judge with position-bias mitigation (both orderings), Wilson CIs, and a flip-rate quality metric for the judge itself.",
    },
    {
        "slug": "ragas-eval-quickstart",
        "title": "RAGAS RAG Evaluation Quickstart",
        "tldr": "Evaluate a RAG pipeline on faithfulness, answer relevance, context precision, and context recall using RAGAS — automated metrics that don't require ground-truth answers.",
        "category": "evaluation",
        "language": "python",
        "framework": "RAGAS",
        "tags": ["ragas", "rag-evaluation", "faithfulness", "metrics"],
        "best_for_tags": ["rag-quality", "regression-suite", "model-comparison"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "After building a RAG pipeline, when you need to track whether changes improve or regress quality. RAGAS gives you reproducible metrics that catch drift over time.",
        "when_not_to_use": "Skip for one-off prototypes — overhead isn't worth it. Skip for streaming chat eval (RAGAS is batch). Skip when you have abundant labeled QA pairs — use straight retrieval metrics (Recall@k).",
        "quick_start": "pip install ragas datasets openai && OPENAI_API_KEY=sk-... python ragas_eval.py",
        "full_code": '''"""RAGAS evaluation: faithfulness, answer relevancy, context precision/recall.

These metrics use LLMs internally (gpt-4o by default). They're sensitive to
the eval model choice — use the strongest model your budget allows for eval,
even if your production RAG uses a smaller one.
"""
from __future__ import annotations

import os

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)


def build_dataset(questions: list[str], answers: list[str], contexts: list[list[str]], ground_truths: list[str]) -> Dataset:
    """RAGAS expects a Dataset with columns: question, answer, contexts, ground_truth.

    contexts is a list of lists — multiple retrieved passages per question.
    """
    return Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })


def run_eval(dataset: Dataset, *, llm_model: str = "gpt-4o-mini") -> dict:
    from langchain_openai import ChatOpenAI
    from ragas.llms import LangchainLLMWrapper

    llm = LangchainLLMWrapper(ChatOpenAI(model=llm_model, temperature=0))

    result = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,           # Are the answer claims supported by contexts?
            answer_relevancy,       # Does the answer address the question?
            context_precision,      # Are retrieved contexts relevant to the question?
            context_recall,         # Were the needed contexts retrieved?
        ],
        llm=llm,
    )

    return result.to_pandas().to_dict(orient="records")


if __name__ == "__main__":
    # Replace with your actual RAG outputs
    questions = [
        "What is reciprocal rank fusion?",
        "When should I use HNSW vs IVFFlat?",
    ]
    answers = [
        "Reciprocal Rank Fusion combines ranked lists by summing 1/(k+rank) scores.",
        "Use HNSW for faster queries; IVFFlat for lower RAM usage on huge corpora.",
    ]
    contexts = [
        ["RRF: each doc's score = sum(1/(k+rank)) across all retriever output lists. Standard k=60."],
        ["HNSW indexes are fast but RAM-heavy. IVFFlat uses less RAM but slower queries and needs REINDEX after bulk inserts."],
    ]
    ground_truths = [
        "Reciprocal Rank Fusion merges results from multiple retrievers via rank reciprocals.",
        "HNSW for query speed; IVFFlat for memory-constrained large corpora.",
    ]

    ds = build_dataset(questions, answers, contexts, ground_truths)
    rows = run_eval(ds)
    for r in rows:
        print(f"\\nQ: {r['question'][:60]}")
        for k in ("faithfulness", "answer_relevancy", "context_precision", "context_recall"):
            v = r.get(k)
            print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
''',
        "dependencies": [
            {"name": "ragas", "version": ">=0.2", "purpose": "RAG evaluation framework"},
            {"name": "datasets", "version": ">=2.18", "purpose": "Dataset wrapper RAGAS expects"},
            {"name": "openai", "version": ">=1.40", "purpose": "Underlying LLM for eval"},
            {"name": "langchain-openai", "version": ">=0.2", "purpose": "LangChain LLM wrapper"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI API key for eval LLM", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install ragas datasets openai langchain-openai",
            "export OPENAI_API_KEY=sk-...",
            "Capture (question, answer, contexts, ground_truth) tuples from your RAG.",
            "python ragas_eval.py",
        ],
        "variations": [
            {
                "label": "Without ground truths",
                "description": "Skip context_recall (needs ground_truth) for unlabeled eval.",
                "code_snippet": "evaluate(dataset=ds, metrics=[faithfulness, answer_relevancy, context_precision], llm=llm)\\n# Omit context_recall when no ground truth available",
            },
            {
                "label": "Custom metrics",
                "description": "Define your own LLM-judged metric.",
                "code_snippet": "from ragas.metrics import Metric\\nclass DomainAccuracy(Metric):\\n    name = 'domain_accuracy'\\n    # implement _ascore using self.llm",
            },
            {
                "label": "Local LLM as eval model",
                "description": "Run RAGAS with Ollama-served Llama.",
                "code_snippet": "from langchain_ollama import ChatOllama\\nllm = LangchainLLMWrapper(ChatOllama(model='llama3.1:70b'))\\n# Smaller models give noisier metrics; use 70B+ for usable signal.",
            },
            {
                "label": "Save eval results to disk",
                "description": "Track metrics over time.",
                "code_snippet": "result.to_pandas().to_csv(f'evals/{datetime.now().isoformat()}.csv', index=False)\\n# diff against prior runs to detect regressions",
            },
        ],
        "common_errors": [
            {
                "error_text": "TimeoutError during eval",
                "cause": "RAGAS makes many LLM calls per row.",
                "fix_snippet": "Reduce dataset size for iterative testing. For full eval, run async / increase timeout. Use a faster eval model (gpt-4o-mini) for development.",
            },
            {
                "error_text": "Faithfulness scores are all 1.0",
                "cause": "Eval model can't distinguish supported from unsupported claims (often gpt-3.5 or smaller local models).",
                "fix_snippet": "Use gpt-4o or claude-3-7-sonnet as eval LLM. Smaller models give uninformative scores.",
            },
            {
                "error_text": "context_recall: ground_truth column missing",
                "cause": "Forgot to provide ground_truth.",
                "fix_snippet": "context_recall requires ground_truth. Either provide it or omit the metric.",
            },
            {
                "error_text": "RAGAS scores conflict with human judgment",
                "cause": "Metrics misalign with your quality bar.",
                "fix_snippet": "RAGAS metrics are proxies. Run a calibration pass: 20 hand-judged samples, compute RAGAS vs human score; trust RAGAS only on metrics that correlate.",
            },
        ],
        "production_checklist": [
            "Use a stronger eval model than your RAG generation model (smaller eval = noisier metrics).",
            "Build a stable test set with diverse query types; don't shuffle between eval runs.",
            "Store eval results with timestamps + commit hashes for regression tracking.",
            "Set fail thresholds in CI (e.g., faithfulness < 0.85 fails the build).",
            "Cache embeddings + retrieval results during eval iterations; only re-run generation.",
            "Sample 5-10 outputs and read them; metrics can drift from human judgment.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["ragas==0.2.4", "datasets==3.0.1", "langchain-openai==0.2.5"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["ragas"],
        "related_glossary_slugs": ["rag-evaluation", "faithfulness", "answer-relevancy"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why these four metrics?",
                "answer": "They cover the RAG quality matrix: retrieval (context_precision/recall) and generation (faithfulness/answer_relevancy). Skipping any of the four leaves a known failure mode unmeasured.",
            },
            {
                "question": "Does RAGAS work without ground truths?",
                "answer": "Yes for faithfulness, answer_relevancy, and context_precision. context_recall requires ground truth. Most teams start without and add ground truth incrementally.",
            },
            {
                "question": "How expensive is a full eval run?",
                "answer": "~5-20 LLM calls per row depending on metrics. 100 rows with all 4 metrics ≈ $1-5 with gpt-4o-mini. Budget accordingly.",
            },
            {
                "question": "When should I use this vs Promptfoo?",
                "answer": "RAGAS is RAG-specific with established metrics. Promptfoo is general prompt eval with broader features (assertions, model comparison, web UI). They're complementary.",
            },
        ],
        "github_url": "https://github.com/explodinggradients/ragas",
        "meta_title": "RAGAS RAG Evaluation Quickstart — Starter",
        "meta_description": "Automated RAG eval with faithfulness, answer relevancy, context precision/recall — track quality over time without manual labels.",
    },
    {
        "slug": "promptfoo-regression-suite",
        "title": "Promptfoo Regression Test Suite",
        "tldr": "YAML-config prompt regression testing with assertions (exact match, contains, semantic similarity, LLM-rubric, latency). Runs across multiple models and providers in parallel — perfect for CI.",
        "category": "evaluation",
        "language": "yaml",
        "framework": "Promptfoo",
        "tags": ["promptfoo", "regression-tests", "ci", "model-comparison"],
        "best_for_tags": ["regression-suite", "ci-cd", "prompt-iteration"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "When iterating prompts in a repo and you need to know: ‘did this change break anything?’ — CI-friendly, multi-provider, assertion-rich.",
        "when_not_to_use": "Skip for one-off testing — overhead of YAML config isn't worth it. Use Promptfoo when you have a STABLE prompt that changes regularly.",
        "quick_start": "npm install -g promptfoo && promptfoo init && promptfoo eval",
        "full_code": '''# promptfooconfig.yaml
# Test that your customer support prompt holds quality across model/provider changes.
description: "Customer support reply quality regression suite"

# Tested across multiple providers — flag any divergence
providers:
  - openai:gpt-4o-mini
  - openai:gpt-4o
  - anthropic:claude-3-5-haiku-latest
  - anthropic:claude-3-7-sonnet-latest

# The prompt under test (could also be a file)
prompts:
  - id: "support-v3"
    raw: |
      You are a customer support agent for Acme SaaS.
      Tone: warm, direct, never condescending. Match the customer's energy.
      If unsure, defer to escalation rather than guessing.

      Customer message: {{message}}

      Reply in 60-120 words. Format: greeting, acknowledgment, action, close.

# Test cases — vary by message types you'll see in production
tests:
  - description: "Refund request with calm tone"
    vars:
      message: "Hi, I was charged twice for last month's subscription. Could you refund the duplicate? My account email is jane@example.com."
    assert:
      - type: contains
        value: "jane@example.com"
      - type: javascript
        value: |
          const wordCount = output.split(/\\s+/).length;
          return wordCount >= 50 && wordCount <= 130 ? true : `word count ${wordCount} out of 50-130`;
      - type: llm-rubric
        value: "Reply acknowledges the duplicate charge, indicates next steps (refund or investigation), and does not promise anything outside policy."
      - type: not-contains
        value: "I apologize for"  # banned filler phrase

  - description: "Angry customer threatening cancellation"
    vars:
      message: "This is the THIRD time your stupid software lost my data. I'm done. Cancel everything and refund the last 6 months or I'm calling my lawyer."
    assert:
      - type: llm-rubric
        value: "Reply takes the data loss seriously, doesn't dismiss anger, offers a concrete next step (escalation, investigation). Does NOT immediately agree to 6-month refund (out of policy)."
      - type: not-contains
        value: "I understand your frustration"  # cliche
      - type: similar
        value: "I can connect you with our retention team to review the data-loss incidents and discuss appropriate compensation."
        threshold: 0.6  # cosine similarity to ideal response

  - description: "Technical question outside agent's lane"
    vars:
      message: "Can you change the API rate limit on my account to 10,000 requests per minute?"
    assert:
      - type: llm-rubric
        value: "Reply defers to engineering/escalation; does NOT promise rate limit changes."
      - type: contains-any
        value: ["engineering", "escalat", "ticket"]

# Optional: run against your CI on push
# defaultTest:
#   threshold: 0.7  # 70% of assertions must pass

# Output formats: write HTML for browse, JSON for CI parsing
outputPath: "./promptfoo-results.json"
''',
        "dependencies": [
            {"name": "promptfoo", "version": ">=0.96", "purpose": "Prompt regression test runner (npm package, runs the YAML)"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Anthropic key", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "npm install -g promptfoo  # or: npx promptfoo@latest",
            "Save the YAML as promptfooconfig.yaml",
            "export OPENAI_API_KEY=sk-... ANTHROPIC_API_KEY=sk-ant-...",
            "promptfoo eval  # runs all tests",
            "promptfoo view  # opens browser UI",
        ],
        "variations": [
            {
                "label": "Test custom HTTP endpoint",
                "description": "Test your deployed service.",
                "code_snippet": "providers:\\n  - id: my-prod-api\\n    config:\\n      url: https://api.acme.com/v1/chat\\n      method: POST\\n      headers: { Authorization: 'Bearer {{env.MY_API_TOKEN}}' }\\n      body: '{ \\\"message\\\": \\\"{{message}}\\\" }'",
            },
            {
                "label": "CSV-driven test cases",
                "description": "Pull test cases from a spreadsheet.",
                "code_snippet": "tests: file://tests.csv  # columns: message,expected_keywords",
            },
            {
                "label": "Threshold-based pass/fail",
                "description": "Set CI failure threshold.",
                "code_snippet": "defaultTest:\\n  threshold: 0.75  # CI fails if <75% pass\\n# Combine with `promptfoo eval --share` to get a shareable link",
            },
            {
                "label": "Red-team variant",
                "description": "Adversarial test cases.",
                "code_snippet": "redteam:\\n  plugins:\\n    - harmful\\n    - politics\\n    - jailbreak\\n# Generates adversarial inputs automatically",
            },
        ],
        "common_errors": [
            {
                "error_text": "Error: No assertion passed",
                "cause": "Strict threshold + flaky assertions.",
                "fix_snippet": "Use type: llm-rubric for subjective quality; use type: similar with threshold ≈0.6 for ideal responses; pin temperature 0 for determinism.",
            },
            {
                "error_text": "Provider not initialized: anthropic",
                "cause": "ANTHROPIC_API_KEY not set.",
                "fix_snippet": "export ANTHROPIC_API_KEY=sk-ant-... before running.",
            },
            {
                "error_text": "Tests pass locally but fail in CI",
                "cause": "Non-deterministic output (temperature > 0 or model version drift).",
                "fix_snippet": "Pin temperature: 0 in provider config; pin model versions explicitly (gpt-4o-mini-2024-07-18); add similarity thresholds rather than exact matches.",
            },
            {
                "error_text": "LLM-rubric assertions are flaky",
                "cause": "Judge model interprets rubric differently across runs.",
                "fix_snippet": "Switch judge to gpt-4o (set in eval-llm.provider). Tighten rubric language to remove ambiguity. Run N=3 and require all to pass.",
            },
        ],
        "production_checklist": [
            "Run on every PR via GitHub Actions; fail the build on threshold drops.",
            "Pin model versions (not just families) for reproducibility.",
            "Store eval results JSON in your repo or artifact store for trend tracking.",
            "Use llm-rubric judiciously; exact-match and contains are cheaper and more reliable.",
            "Include adversarial cases (red-team) once per release cycle.",
            "Review failing cases before bumping thresholds; bumping silently is how regressions hide.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o", "claude-3-7-sonnet", "claude-3-5-haiku"],
            "library_versions": ["promptfoo==0.96.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["promptfoo"],
        "related_glossary_slugs": ["prompt-evaluation", "regression-testing", "llm-rubric"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Promptfoo vs RAGAS?",
                "answer": "Promptfoo is general prompt eval — works on chat, completion, function calling, any output. RAGAS is RAG-specific. Use both: Promptfoo for general regression, RAGAS for RAG-specific metrics.",
            },
            {
                "question": "Do I need ground truths?",
                "answer": "No — llm-rubric assertions evaluate quality without them. But if you have them, exact-match and similarity assertions are cheaper and more reliable.",
            },
            {
                "question": "How do I integrate with CI?",
                "answer": "Run `promptfoo eval --output results.json` in your CI. Set thresholds in defaultTest. Fail the build on threshold breach. Promptfoo emits standard exit codes.",
            },
            {
                "question": "Can it test agents?",
                "answer": "Yes — define a custom provider that runs your agent loop and returns the final answer. Test multi-step agent quality the same way you test prompts.",
            },
        ],
        "github_url": "https://github.com/promptfoo/promptfoo",
        "meta_title": "Promptfoo Regression Test Suite — Starter",
        "meta_description": "YAML-config prompt regression tests with assertions, multi-provider, LLM-rubric judging — ready for CI.",
    },
]
