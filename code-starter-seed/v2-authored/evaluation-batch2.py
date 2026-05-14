"""Evaluation starters — batch 2: braintrust, deepeval, custom scorers."""

RECORDS = [
    {
        "slug": "braintrust-online-eval-experiment",
        "title": "Braintrust Online Eval Experiment",
        "tldr": "Run an evaluation experiment in Braintrust: log inputs/outputs/scores, compare experiments side-by-side, track quality regressions over time with one decorator.",
        "category": "evaluation",
        "language": "python",
        "framework": "Braintrust",
        "tags": ["braintrust", "evaluation", "experiment-tracking", "regression"],
        "best_for_tags": ["llm-eval", "experiment-tracking", "ci-eval"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When iterating on prompts/models and need experiment-level tracking — compare ‘prompt v3’ to ‘prompt v2’ on the same dataset, with diff-style review.",
        "when_not_to_use": "Skip for one-off evals (use Promptfoo or pytest). Skip for very private data — Braintrust is cloud (or self-host).",
        "quick_start": "pip install braintrust openai && BRAINTRUST_API_KEY=... python eval.py",
        "full_code": '''"""Braintrust evaluation experiment.

Pattern:
  - Define a Task (the thing under test): your prompt or function.
  - Define Scorers: how to grade outputs (exact match, LLM-as-judge, etc.).
  - Run on a Dataset: list of {input, expected} pairs.
  - Braintrust logs, scores, and surfaces regressions vs prior experiments.
"""
from __future__ import annotations

import os

from braintrust import Eval, init_logger
from autoevals import Factuality, LevenshteinScorer

logger = init_logger(project="ossaihub-prompts")


# ----------------- TASK -----------------

def my_summarizer(input: str) -> str:
    """The thing under test — usually wraps your LLM call."""
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": "Summarize in exactly 2 sentences."},
            {"role": "user", "content": input},
        ],
    )
    return resp.choices[0].message.content


# ----------------- DATASET -----------------

DATASET = [
    {
        "input": "Reciprocal rank fusion combines ranked lists from multiple retrievers. Each document's final score is the sum of 1/(k+rank) across all input lists. The constant k smooths the early-rank dominance.",
        "expected": "Reciprocal rank fusion sums 1/(k+rank) scores across retrievers to merge ranked lists. The k constant prevents top-ranked items from dominating.",
    },
    {
        "input": "HNSW indexes provide fast query times for high-dimensional vector search but require significant RAM. IVFFlat is the alternative when memory matters more than latency.",
        "expected": "HNSW gives fast vector search but uses lots of RAM. IVFFlat trades query speed for lower memory.",
    },
]


# ----------------- SCORERS -----------------

# Built-in: factuality LLM-judge, levenshtein distance, ...
# Custom: define your own

def length_check(input, output, expected):
    """Custom scorer: penalize if output is way longer than expected."""
    ratio = len(output) / max(len(expected), 1)
    return 1.0 if 0.5 <= ratio <= 2.0 else 0.5


# ----------------- RUN EVAL -----------------

Eval(
    name="summarizer-v1",
    data=lambda: DATASET,
    task=lambda input, *args: my_summarizer(input),
    scores=[
        Factuality,                       # autoevals built-in LLM judge
        LevenshteinScorer,                # text similarity to expected
        length_check,                     # custom
    ],
    experiment_name="prompt-v3-with-temp-0",   # name the experiment
    metadata={"prompt_version": "v3", "model": "gpt-4o-mini"},
)
# Output: Braintrust dashboard URL where you can browse, compare, and diff.
''',
        "dependencies": [
            {"name": "braintrust", "version": ">=0.0.150", "purpose": "Evaluation framework + dashboard"},
            {"name": "autoevals", "version": ">=0.0.50", "purpose": "Built-in scorers (LLM-judge etc.)"},
            {"name": "openai", "version": ">=1.40", "purpose": "Task LLM"},
        ],
        "env_vars": [
            {"name": "BRAINTRUST_API_KEY", "required": True, "description": "Braintrust API key", "example": "..."},
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "Sign up at braintrust.dev (free tier).",
            "pip install braintrust autoevals openai",
            "export BRAINTRUST_API_KEY=... OPENAI_API_KEY=sk-...",
            "python eval.py",
            "Open dashboard URL printed in output.",
        ],
        "variations": [
            {
                "label": "Self-hosted",
                "description": "Run Braintrust on your own infra.",
                "code_snippet": "# Use Braintrust's self-hosting via Docker; same SDK API, different endpoint URL.",
            },
            {
                "label": "CI integration",
                "description": "Fail CI on regression.",
                "code_snippet": "# Use braintrust eval CLI: braintrust eval my_eval.py --fail-on-regression\\n# Threshold per-scorer for what counts as regression",
            },
            {
                "label": "Production logging (not eval)",
                "description": "Log live traffic for later analysis.",
                "code_snippet": "from braintrust import wrap_openai\\nclient = wrap_openai(OpenAI())  # auto-logs every chat call",
            },
        ],
        "common_errors": [
            {
                "error_text": "BraintrustError: API key not configured",
                "cause": "Env var missing.",
                "fix_snippet": "export BRAINTRUST_API_KEY=... before running. Or pass api_key=... to init_logger.",
            },
            {
                "error_text": "Dataset items missing expected field",
                "cause": "Scorers that need expected (e.g., Levenshtein) fail.",
                "fix_snippet": "Either: provide expected in dataset, OR use scorers that don't need it (Factuality on context alone).",
            },
            {
                "error_text": "Eval is slow",
                "cause": "LLM-judge scorers call LLMs per item.",
                "fix_snippet": "Set max_concurrency in Eval; or use simpler scorers (Levenshtein doesn't call LLM).",
            },
            {
                "error_text": "Can't compare experiments",
                "cause": "Different experiment_name uses different versions of dataset.",
                "fix_snippet": "Pin dataset (don't shuffle). Use experiment naming convention with versions.",
            },
        ],
        "production_checklist": [
            "Pin dataset; don't shuffle between runs.",
            "Use experiment_name with version + git commit for traceability.",
            "Set scorer thresholds; track regressions automatically.",
            "Run in CI on prompt PRs; surface diffs in review.",
            "Keep separate experiments for dev/staging/prod.",
            "Mask PII in dataset; Braintrust logs raw inputs.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["braintrust==0.0.150", "autoevals==0.0.50"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["braintrust"],
        "related_glossary_slugs": ["llm-evaluation", "experiment-tracking"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Braintrust vs Langfuse vs Promptfoo?", "answer": "Braintrust: best for systematic experiments + dataset evaluation. Langfuse: best for tracing/observability. Promptfoo: best for prompt regression in CI. Different stages of the pipeline."},
            {"question": "Self-host?", "answer": "Yes — Braintrust offers self-hosted via Docker for teams with privacy requirements."},
            {"question": "Can I use autoevals separately?", "answer": "Yes — autoevals is the open-source scorer library; runs independently of Braintrust dashboard. Just import scorers and use them directly."},
            {"question": "Cost?", "answer": "Braintrust free tier covers small teams. Storage + scoring LLM calls scale with usage. Most cost is the scoring LLM, not the platform."},
        ],
        "github_url": "https://github.com/braintrustdata/braintrust",
        "meta_title": "Braintrust Online Eval Experiment — Starter",
        "meta_description": "Run a Braintrust eval: dataset, task, scorers (factuality / similarity / custom), experiment tracking, regression alerts.",
    },
    {
        "slug": "deepeval-llm-test-cases",
        "title": "DeepEval Pytest-Style LLM Testing",
        "tldr": "Treat LLM outputs as testable units with DeepEval — pytest-compatible test cases for relevance, faithfulness, hallucination, bias. Run in CI like any other test suite.",
        "category": "evaluation",
        "language": "python",
        "framework": "DeepEval + pytest",
        "tags": ["deepeval", "pytest", "testing", "llm-test"],
        "best_for_tags": ["ci-testing", "regression", "deterministic-evals"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "When you want LLM eval to feel like normal testing — pytest fixtures, parameterize, assert. DeepEval bridges eval metrics into a familiar test framework.",
        "when_not_to_use": "Skip for exploratory eval (use Promptfoo or notebooks). Skip for purely retrieval-quality metrics (RAGAS is more focused).",
        "quick_start": "pip install deepeval pytest && OPENAI_API_KEY=sk-... pytest tests/test_llm.py -v",
        "full_code": '''"""DeepEval pytest tests.

Each test asserts that an LLM output meets quality bars:
  - Answer relevancy (does it answer the question?)
  - Faithfulness (claims supported by context?)
  - Hallucination (claims fabricated?)
  - Custom metrics (your own)
"""
from __future__ import annotations

import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric,
    GEval,
)
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


# ----------------- TEST CASES -----------------

@pytest.fixture
def rag_relevancy():
    return AnswerRelevancyMetric(threshold=0.7, model="gpt-4o-mini")


@pytest.fixture
def rag_faithfulness():
    return FaithfulnessMetric(threshold=0.8, model="gpt-4o-mini")


@pytest.fixture
def custom_brevity():
    return GEval(
        name="Brevity",
        criteria="Evaluation criteria: the response should be under 100 words. Score 1 if under 100, 0 if over.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.5,
        model="gpt-4o-mini",
    )


# ----------------- TESTS -----------------

def test_rag_answer_relevancy(rag_relevancy):
    """The answer should address the question."""
    test_case = LLMTestCase(
        input="What is reciprocal rank fusion?",
        actual_output="Reciprocal rank fusion sums 1/(k+rank) scores across retrievers to merge ranked lists.",
        retrieval_context=[
            "RRF combines ranked results from multiple retrievers via sum of reciprocals."
        ],
    )
    assert_test(test_case, [rag_relevancy])


def test_rag_faithfulness(rag_faithfulness):
    """The answer must be supported by the retrieval context."""
    test_case = LLMTestCase(
        input="What's the formula for RRF?",
        actual_output="RRF score = sum across retrievers of 1/(k+rank), where k is a smoothing constant.",
        retrieval_context=[
            "RRF formula: score(d) = Σ 1/(k+r) where r is rank of doc d in each retriever's list."
        ],
    )
    assert_test(test_case, [rag_faithfulness])


@pytest.mark.parametrize("question,answer", [
    ("Define embedding.", "An embedding is a dense vector that captures semantic meaning."),
    ("Define vector database.", "A vector database stores embeddings and supports similarity search."),
])
def test_definitions_are_brief(question, answer, custom_brevity):
    test_case = LLMTestCase(input=question, actual_output=answer)
    assert_test(test_case, [custom_brevity])


def test_no_hallucination_simple():
    """Detect fabricated facts."""
    metric = HallucinationMetric(threshold=0.5, model="gpt-4o-mini")
    test_case = LLMTestCase(
        input="What year was Anthropic founded?",
        actual_output="Anthropic was founded in 2021.",
        context=["Anthropic is an AI safety company founded in 2021 by former OpenAI researchers."],
    )
    assert_test(test_case, [metric])
''',
        "dependencies": [
            {"name": "deepeval", "version": ">=1.0", "purpose": "LLM testing framework"},
            {"name": "pytest", "version": ">=8.0", "purpose": "Test runner"},
            {"name": "openai", "version": ">=1.40", "purpose": "Underlying judge LLM"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key for judges", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install deepeval pytest openai",
            "export OPENAI_API_KEY=sk-...",
            "pytest tests/test_llm.py -v",
        ],
        "variations": [
            {"label": "CI integration", "description": "Run on every PR.", "code_snippet": "# .github/workflows/llm-eval.yml: pytest tests/test_llm.py --json-report"},
            {"label": "Synthetic data generation", "description": "DeepEval generates test cases.", "code_snippet": "from deepeval.synthesizer import Synthesizer\\ndataset = Synthesizer().generate(documents=['my_doc.pdf'])"},
            {"label": "Conversation-level metrics", "description": "Evaluate multi-turn dialogues.", "code_snippet": "from deepeval.test_case import ConversationalTestCase\\n# Eval an entire conversation, not just one turn"},
        ],
        "common_errors": [
            {"error_text": "Test marked as passed but metric is borderline", "cause": "Threshold too lenient.", "fix_snippet": "Tune threshold per metric; 0.7-0.8 is typical for relevancy/faithfulness."},
            {"error_text": "Different scores across runs", "cause": "Judge non-determinism.", "fix_snippet": "Use temperature=0 in the metric's underlying LLM call. Pin judge model version."},
            {"error_text": "GEval criteria vague produces unreliable scores", "cause": "GEval needs precise criteria.", "fix_snippet": "Make criteria specific: ‘Score 1 if X, 0 if Y.’ Vague criteria → noisy results."},
        ],
        "production_checklist": [
            "Run in CI on prompt/model changes; gate merges.",
            "Pin judge model version; results drift across versions.",
            "Track test pass rates over time; sudden drops = regressions.",
            "Use deterministic scorers (similarity, exact match) where possible; cheaper, more reliable.",
            "Synthetic data for breadth, real cases for ground truth.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["deepeval==1.0.0", "pytest==8.3.3"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["deepeval"],
        "related_glossary_slugs": ["llm-evaluation", "regression-testing"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "DeepEval vs RAGAS vs Promptfoo?", "answer": "DeepEval: pytest-style integration. RAGAS: RAG-specific metrics. Promptfoo: YAML-driven matrix testing. Pick by where it fits in your existing workflow."},
            {"question": "Custom metrics?", "answer": "GEval lets you write criteria in natural language; useful for domain-specific quality bars not covered by built-ins."},
            {"question": "Cost?", "answer": "Each metric calls a judge LLM per test case. Use gpt-4o-mini for judges in CI; reserve gpt-4o for high-stakes."},
        ],
        "github_url": "https://github.com/confident-ai/deepeval",
        "meta_title": "DeepEval Pytest-Style LLM Testing — Starter",
        "meta_description": "Pytest-compatible LLM eval with DeepEval: relevancy, faithfulness, hallucination, custom GEval metrics. CI-ready.",
    },
]
