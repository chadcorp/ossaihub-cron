"""Evaluation starters — batch 4: prompt regression via mutation sensitivity (paired with testing batch)."""

RECORDS = [
    {
        "slug": "prompt-mutation-eval-sensitivity",
        "title": "Prompt Sensitivity Eval: Mutation Testing for Prompts",
        "tldr": "A prompt that only works with exact wording is fragile. Generate meaning-preserving mutations, measure output stability on a labeled set, and ship the most robust variant — not the one that scored best once.",
        "category": "evaluation",
        "language": "python",
        "framework": "none (eval harness)",
        "tags": ["evaluation", "prompt-engineering", "robustness", "mutation", "regression"],
        "best_for_tags": ["prompt-selection", "ci-gates", "regression-prevention"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "Choosing between prompt variants or guarding a shipped prompt in CI. Mutation testing reveals whether a prompt's score depends on fragile exact wording, so you can ship the robust variant and catch sensitivity regressions.",
        "when_not_to_use": "Skip when you have fewer than ~20 labeled items (variance is meaningless). Skip for open-ended generation where exact/normalized match can't score outputs — use an LLM judge instead.",
        "quick_start": "pip install anthropic && python prompt_sensitivity_eval.py",
        "full_code": '''"""Prompt sensitivity eval via mutation testing.

Apply meaning-preserving mutations to a base prompt, score each on a labeled
set, and report:
  - per-mutation accuracy
  - a sensitivity score = 1 - (stdev / mean) of accuracies (1.0 = rock solid)
  - a FAIL flag if any single mutation drops accuracy > 10 points vs base

Runs in CI WITHOUT a key: LLM_STUB=1 (default) uses a deterministic classifier.
Stdlib only for stats (no numpy) so the harness has one optional dependency.
"""
from __future__ import annotations

import os
import random
import re
import statistics

MODEL = "claude-sonnet-4-5"
USE_STUB = os.environ.get("LLM_STUB", "1") == "1"
DROP_THRESHOLD = 10.0  # percentage points
random.seed(7)  # deterministic mutations/typos for reproducible runs

# ----------------- TASK: sentiment classification -----------------

BASE_PROMPT = (
    "You are a precise classifier.\\n"
    "- Read the review.\\n"
    "- Reply with exactly one word: positive, negative, or neutral.\\n"
    "Return only the label, lowercase, no punctuation."
)

EVAL_SET = [  # >= 20 items; below ~20 the sensitivity variance is just noise
    ("Absolutely loved it, would buy again.", "positive"),
    ("Terrible quality, broke on day one.", "negative"),
    ("It arrived. Does the job, nothing special.", "neutral"),
    ("Best purchase I have made all year!", "positive"),
    ("Waste of money, do not recommend.", "negative"),
    ("Fine for the price I suppose.", "neutral"),
    ("The support team was rude and unhelpful.", "negative"),
    ("Exceeded every expectation, five stars.", "positive"),
    ("Meh. It is okay, I guess.", "neutral"),
    ("Stopped working after a week, very disappointed.", "negative"),
    ("Delightful, exactly what I wanted.", "positive"),
    ("Average product, average experience.", "neutral"),
    ("Crashes constantly, total garbage.", "negative"),
    ("Highly recommend to anyone on the fence.", "positive"),
    ("Neither good nor bad, just there.", "neutral"),
    ("Refund requested, awful from start to finish.", "negative"),
    ("So happy with this, worth every penny.", "positive"),
    ("It works. Not thrilled, not upset.", "neutral"),
    ("Cheaply made and overpriced.", "negative"),
    ("A genuine joy to use every day.", "positive"),
]

# ----------------- MUTATORS (meaning-preserving) -----------------

_SYN = {"precise": "exact", "Read": "Look at", "Reply": "Respond", "Return": "Output"}


def add_trailing_space(p: str) -> str: return p + "   "
def lowercase_first(p: str) -> str: return p[:1].lower() + p[1:]
def add_polite_prefix(p: str) -> str: return "Please, if you would be so kind:\\n" + p


def shuffle_bulleted_instructions(p: str) -> str:
    lines = p.split("\\n")
    bullets = [i for i, ln in enumerate(lines) if ln.startswith("- ")]
    picked = [lines[i] for i in bullets]
    random.shuffle(picked)
    for slot, ln in zip(bullets, picked):
        lines[slot] = ln
    return "\\n".join(lines)


def inject_typos(p: str, rate: float = 0.03) -> str:
    out = list(p)
    for i, ch in enumerate(out):
        if ch.isalpha() and random.random() < rate:
            out[i] = ch + ch  # double a letter; preserves readability
    return "".join(out)


def swap_synonyms(p: str) -> str:
    for word, syn in _SYN.items():
        p = re.sub(rf"\\b{word}\\b", syn, p)
    return p


MUTATORS = {
    "base": lambda p: p,
    "trailing_space": add_trailing_space,
    "lowercase_first": lowercase_first,
    "polite_prefix": add_polite_prefix,
    "shuffle_bullets": shuffle_bulleted_instructions,
    "typos": inject_typos,
    "synonyms": swap_synonyms,
}

# ----------------- MODEL CALL -----------------

_LABELS = ("positive", "negative", "neutral")
_NEG = {"terrible", "broke", "waste", "rude", "garbage", "awful", "cheaply", "overpriced",
        "disappointed", "refund", "crashes", "do not"}
_POS = {"loved", "best", "exceeded", "recommend", "happy", "worth", "joy", "delightful", "five stars"}


def _stub_classify(prompt: str, review: str) -> str:
    """Deterministic stand-in; same I/O contract as the live model."""
    low = review.lower()
    if any(t in low for t in _NEG):
        return "negative"
    if any(t in low for t in _POS):
        return "positive"
    return "neutral"


def _live_classify(prompt: str, review: str) -> str:
    import anthropic  # lazy import so CI needs no key

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=8,
        temperature=0,  # pin: sampling noise would masquerade as prompt sensitivity
        system=prompt,
        messages=[{"role": "user", "content": review}],
    )
    return msg.content[0].text.strip().lower()


def classify(prompt: str, review: str) -> str:
    raw = _stub_classify(prompt, review) if USE_STUB else _live_classify(prompt, review)
    raw = raw.strip().lower()
    return next((lab for lab in _LABELS if lab in raw), "neutral")  # normalize


# ----------------- SCORING + REPORT -----------------


def accuracy(prompt: str) -> float:
    correct = sum(classify(prompt, text) == gold for text, gold in EVAL_SET)
    return 100.0 * correct / len(EVAL_SET)


def run() -> dict:
    scores = {name: accuracy(mut(BASE_PROMPT)) for name, mut in MUTATORS.items()}
    base = scores["base"]
    values = list(scores.values())
    mean = statistics.fmean(values)
    stdev = statistics.pstdev(values)
    sensitivity = 1.0 - (stdev / mean) if mean else 0.0
    worst_name = min(scores, key=scores.get)
    worst_drop = base - scores[worst_name]
    failed = worst_drop > DROP_THRESHOLD

    print(f"{'mutation':<18} accuracy")
    for name, acc in scores.items():
        print(f"{name:<18} {acc:5.1f}")
    print(f"\\nmean={mean:.1f}  stdev={stdev:.1f}  sensitivity={sensitivity:.3f}")
    print(f"worst: {worst_name} (drop {worst_drop:.1f} pts vs base)")
    print("RESULT:", "FAIL (brittle prompt)" if failed else "PASS (robust)")
    return {"scores": scores, "sensitivity": sensitivity, "failed": failed}


if __name__ == "__main__":
    result = run()
    raise SystemExit(1 if result["failed"] else 0)
''',
        "dependencies": [
            {"name": "anthropic", "version": ">=0.40", "purpose": "Live model calls (optional; the stub runs offline)"},
        ],
        "env_vars": [
            {"name": "LLM_STUB", "required": False, "description": "Set to 1 (default) to use the deterministic classifier so CI runs without a key. Unset for live calls.", "example": "1"},
            {"name": "ANTHROPIC_API_KEY", "required": False, "description": "Only needed when LLM_STUB is unset, for a live model run.", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "pip install anthropic",
            "Save prompt_sensitivity_eval.py and replace EVAL_SET with >= 20 labeled items.",
            "Run offline (stub): python prompt_sensitivity_eval.py",
            "Live run: unset LLM_STUB; export ANTHROPIC_API_KEY=...; python prompt_sensitivity_eval.py",
            "Wire into CI: the script exits 1 when a mutation drops accuracy past the threshold.",
        ],
        "variations": [
            {"label": "LLM-as-judge scoring", "description": "For open-ended tasks, score with a judge instead of exact match.", "code_snippet": "def score(out, gold):\\n    verdict = judge(f'Does this answer match the reference? {out} vs {gold}. Reply yes/no.')\\n    return verdict.strip().lower().startswith('yes')"},
            {"label": "A/B two candidate prompts", "description": "Run both prompts through the same mutation suite; pick the higher sensitivity.", "code_snippet": "a = {n: accuracy(m(PROMPT_A)) for n,m in MUTATORS.items()}\\nb = {n: accuracy(m(PROMPT_B)) for n,m in MUTATORS.items()}\\nwinner = 'A' if statistics.pstdev(a.values()) < statistics.pstdev(b.values()) else 'B'"},
            {"label": "CI regression gate", "description": "Fail the build if sensitivity falls below a pinned threshold.", "code_snippet": "MIN_SENSITIVITY = 0.92\\nresult = run()\\nassert result['sensitivity'] >= MIN_SENSITIVITY, f\\\"prompt got brittle: {result['sensitivity']:.3f}\\\""},
        ],
        "common_errors": [
            {"error_text": "A mutation changes the score because it changed the MEANING", "cause": "A mutator that flips intent (e.g. negation) is not meaning-preserving.", "fix_snippet": "Keep mutators to whitespace/politeness/order/typos/synonyms. Eyeball a few mutated prompts to confirm intent is intact."},
            {"error_text": "Valid paraphrases scored as wrong", "cause": "Exact-match scoring punishes correct answers worded differently.", "fix_snippet": "Normalize before comparing (lowercase, strip, map to a label), or use an LLM judge for open-ended outputs."},
            {"error_text": "Sensitivity score swings run to run", "cause": "Too few eval items, so variance is noise.", "fix_snippet": "Use >= 20 labeled items. The more items, the more stable the per-mutation accuracy and the sensitivity score."},
            {"error_text": "Mutations look like they change the prompt but accuracy is identical", "cause": "temperature > 0 masks prompt sensitivity with sampling variance.", "fix_snippet": "Pin temperature=0 so differences reflect the prompt wording, not the sampler. Also seed any randomized mutator."},
        ],
        "production_checklist": [
            "Pin temperature=0 so sensitivity reflects wording, not sampling noise.",
            "Use >= 20 labeled eval items so variance is meaningful.",
            "Keep every mutator meaning-preserving; review a sample of outputs.",
            "Seed RNG so typo/shuffle mutations are reproducible across runs.",
            "Normalize outputs (or use a judge) before scoring matches.",
            "Gate CI on the sensitivity score and the per-mutation drop threshold.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["anthropic==0.40"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["promptfoo", "promptfoo-promptfoo"],
        "related_glossary_slugs": ["prompt-engineering", "llm-evaluation", "llm-as-judge", "prompt-rewriting", "regression-task"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How is this different from a normal eval?", "answer": "A normal eval scores one prompt on a set. Mutation testing scores many meaning-preserving variants and looks at the variance. A prompt that scores 95% on the exact wording but 70% with a trailing space or a synonym is fragile, and a single-shot eval never sees that."},
            {"question": "What's the sensitivity score?", "answer": "1 - (stdev / mean) of the per-mutation accuracies. 1.0 means every mutation scored identically (robust); lower means wording matters too much. It's a single comparable number for A/B-ing prompts or gating CI."},
            {"question": "Which mutations should I include?", "answer": "Only meaning-preserving ones: whitespace, politeness prefixes, reordering independent bullet instructions, light typos, and synonym swaps. Anything that could flip intent (negation, dropping a constraint) invalidates the measurement."},
            {"question": "Does it run in CI without a key?", "answer": "Yes. LLM_STUB=1 (default) routes through a deterministic classifier with the same contract, so the harness, scoring, and exit-code gate all run offline. Flip the flag plus set ANTHROPIC_API_KEY for a real model measurement."},
        ],
        "github_url": "https://github.com/promptfoo/promptfoo",
        "meta_title": "Prompt Sensitivity Eval: Mutation Testing",
        "meta_description": "Find fragile prompts: apply meaning-preserving mutations, measure stability, ship the robust variant. Sensitivity score + CI gate. Runs offline via a stub.",
    },
]
