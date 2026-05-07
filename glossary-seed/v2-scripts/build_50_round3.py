"""Round 3: 50 more v2 terms (626 -> 676).

Usage:
  python build_50_round3.py --validate-only
  python build_50_round3.py --merge
"""
import argparse
import json
import pathlib
import re
import sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
REBUILT = HERE.parent / "rebuilt-v2.json"
OUT_NEW_ONLY = HERE.parent / "new-50-round3.json"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BANNED = ["powerful", "revolutionary", "cutting-edge", "cutting edge",
          "unleash", "seamlessly", "game-changer", "game changer", "groundbreaking"]

TERMS = [
    # 1. majority-voting
    {
        "slug": "majority-voting",
        "title": "Majority Voting",
        "category": "sampling",
        "difficulty_tier": "beginner",
        "tldr": "Aggregating multiple model samples by selecting the most common answer, improving accuracy at the cost of more inference compute.",
        "plain_english": "Sample N answers from a model, count which answer appears most often, return that as the final result. The intuition: if a model gets a question right more often than wrong, sampling many times and voting amplifies the correct answer above noise. It's the simplest form of test-time compute scaling — no verifier needed, just aggregate sampled responses by frequency.",
        "how_it_works": "Run inference N times with non-zero temperature so samples differ. Normalise each output (canonical form for math: extract final number; code: hash the function body; classification: take the predicted label). Count occurrences. Return the highest-count answer. Self-consistency is the canonical implementation for chain-of-thought math: sample 5-40 reasoning paths, extract final answers, vote. Variants weight votes by confidence or select via plurality plus tie-break heuristics.",
        "why_it_matters": "Majority voting consistently lifts accuracy on benchmarks where the model's per-sample correctness rate exceeds 50% — exactly the regime where you want extra compute. It needs no labelled data, no verifier, and no fine-tuning. The downside is N× the cost, so production systems use it selectively (only on hard queries identified by a router).",
        "example": "A team runs a math model on GSM8K. Single-sample accuracy: 72%. Sample 10 paths and vote: 81%. They route easy questions through single-sample (fast) and hard questions through 10-sample voting (slower, more accurate); average per-query cost rises 3× but tail accuracy rises 9 points.",
        "pitfalls": [
            "Tie-breaking: even N can leave ties; pick a deterministic tie-break (e.g. the highest-confidence sample) to avoid non-determinism.",
            "Answer normalisation: '5' and '5.0' should be equivalent; sloppy parsing inflates apparent disagreement.",
            "Diminishing returns: gains plateau past N=20-40 for most tasks; spending beyond that is waste.",
            "Doesn't fix systematic errors: if the model gets a question wrong 60% of the time, voting amplifies the wrong answer."
        ],
        "when_use": "Use when a fast verifier is unavailable but the model's per-sample accuracy is over 50%, especially math, classification, and structured tasks where answers can be normalised.",
        "when_avoid": "Avoid when answers are open-ended (creative writing) or when per-sample accuracy is below 50% (voting amplifies wrong answers).",
        "related_terms": ["self-consistency", "best-of-n", "test-time-compute", "top-k-sampling", "verifier-model", "reasoning-model"],
        "related_tools": [],
        "faq": [
            {"q": "Voting or best-of-N?",
             "a": "Best-of-N picks one sample using a verifier. Voting picks based on frequency without a verifier. If you have a good verifier, best-of-N usually wins; if not, voting is the cheap alternative."},
            {"q": "What N value works best?",
             "a": "5-10 captures most of the benefit on math; 20-40 squeezes the rest. Beyond 40, returns diminish quickly. Tune against your eval."},
            {"q": "Does this work for chat?",
             "a": "Less well — chat answers don't normalise into a single-string vote. Voting works best when answers reduce to a finite set of equivalence classes."},
            {"q": "Self-consistency same as voting?",
             "a": "Self-consistency is voting applied specifically to chain-of-thought reasoning paths. The original paper popularised the term for this use case."}
        ]
    },
    # 2. verifier-model
    {
        "slug": "verifier-model",
        "title": "Verifier Model",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Model that scores whether a candidate answer or reasoning trace is correct, used to drive test-time search like best-of-N or beam-style decoding.",
        "plain_english": "A verifier doesn't generate answers; it judges them. Given a question and a candidate answer, the verifier outputs a score for correctness. Pair a generator with a verifier and you get best-of-N: sample many answers, pick the one the verifier ranks highest. Verifiers can be rule-based (unit tests pass), trained classifiers, or LLM-as-judge prompts. Better verifiers translate directly into better test-time compute scaling.",
        "how_it_works": "Train or build a verifier with (question, answer, correct?) triples. The verifier is typically a smaller model than the generator, with a binary or scalar correctness head. At inference, generate N candidates, score each with the verifier, return the top-scored. Variants: process verifiers score reasoning steps; outcome verifiers score only final answers; learned verifiers use neural networks; rule-based verifiers use code execution or constraint checks.",
        "why_it_matters": "Verifier quality bounds test-time compute scaling. With a perfect verifier, best-of-N reaches Pass@N. With a noisy verifier, it plateaus much earlier. For domains with rule-based verification (math with answer checkers, code with tests), verifiers are cheap and exact. For open-ended domains, learned verifiers approximate human judgment at significant cost.",
        "example": "A math team trains a verifier on 50k (problem, attempted-solution, was-correct) examples from past inference runs. The verifier scores 88% accuracy on a held-out set. Pairing with a generator and N=16 best-of-N raises end-to-end accuracy from 70% to 84% on GSM8K. Total inference cost: 17× a single generation, but eval accuracy rivals frontier models at 1/5 the per-token price.",
        "pitfalls": [
            "Verifier hacking: generators learn to produce outputs the verifier mis-rates as correct; harden verifiers iteratively.",
            "Distribution shift: a verifier trained on one model's outputs degrades on another's; retrain when generators change.",
            "Cost: per-candidate verification adds up; cache scores when prompts repeat.",
            "Calibration: verifier confidence may not align with actual probability of correctness; check before using as a probabilistic signal."
        ],
        "when_use": "Use to scale test-time compute on tasks with verifiable correctness (math, code, structured outputs). Especially valuable for reasoning-heavy domains.",
        "when_avoid": "Avoid when correctness is inherently subjective (creative writing, persona-driven chat) where no good verifier exists.",
        "related_terms": ["best-of-n", "majority-voting", "process-reward-model", "reward-model", "test-time-compute", "evaluation-set"],
        "related_tools": [],
        "faq": [
            {"q": "Verifier or reward model?",
             "a": "Verifiers binary-classify correctness; reward models output continuous preference scores. Both serve similar test-time roles; reward models are common for RLHF training, verifiers for math/code."},
            {"q": "How big should the verifier be?",
             "a": "Smaller than the generator is usually fine — verification is easier than generation. A 7B verifier paired with a 70B generator is a common setup."},
            {"q": "Process or outcome verifier?",
             "a": "Process verifiers score each reasoning step; outcome verifiers only score finals. Process is more sample-efficient; outcome is simpler to train."},
            {"q": "Can I use LLM-as-judge as a verifier?",
             "a": "Yes — that's the cheap baseline. Quality varies; calibrate against a labelled set."}
        ]
    },
    # 3. step-level-reward
    {
        "slug": "step-level-reward",
        "title": "Step-Level Reward",
        "category": "techniques",
        "difficulty_tier": "advanced",
        "tldr": "Per-step correctness signal in chain-of-thought reasoning, used to guide search and reward intermediate progress rather than only final answers.",
        "plain_english": "A reasoning chain has many steps. Outcome rewards score only the final answer — useful but coarse. Step-level rewards score each step: was this step a logical move? Did it advance the solution? Models trained or guided by step-level rewards learn to take productive intermediate steps, not just produce correct finals via lucky paths. The technique underpins much of recent reasoning-model progress.",
        "how_it_works": "Collect or generate (problem, step, label) triples where each step has a correctness or progress label. Train a process reward model (PRM) on these. At inference, the PRM scores each step; search algorithms (beam search, best-of-N at the step level) use these scores to prune unproductive paths. PRMs are typically trained with human-labelled steps or auto-labelled via Monte Carlo rollouts that estimate each step's contribution to final correctness. OpenAI's PRM800K dataset and DeepSeek's process supervision experiments are well-known examples.",
        "why_it_matters": "Outcome-only rewards conflate good reasoning with lucky guesses. Step-level rewards help models develop logical chains where each step contributes to the answer. They're a major lever in reasoning-model training and one reason recent reasoning models reason more reliably than chain-of-thought-prompted base models. They also enable finer-grained search at inference.",
        "example": "A math model trained with step-level rewards solves a multi-step problem. Without step rewards, it sometimes gets the right final answer via wrong intermediate logic. With step rewards, it consistently produces logically sound chains: each step builds on the previous; final answer is correct because reasoning is correct. Held-out accuracy rises 6 points.",
        "pitfalls": [
            "Labelling cost: per-step labels are expensive — each problem produces many steps, all need scoring.",
            "Reward hacking at step level: models learn to produce steps that score well without contributing to answers; periodic re-labelling helps.",
            "Annotator disagreement: what counts as a 'good step' is subjective; calibrate annotators.",
            "Compounding error: small step-level miscalibrations amplify over long chains; monitor end-to-end accuracy."
        ],
        "when_use": "Use for reasoning-heavy tasks where outcome rewards alone don't capture quality: math, code, planning, multi-step research.",
        "when_avoid": "Avoid for short single-step tasks (no useful step structure) or when outcome rewards are clean (passing unit tests covers the signal).",
        "related_terms": ["process-reward-model", "reward-model", "trajectory-reward", "verifier-model", "reasoning-model", "chain-of-thought"],
        "related_tools": [],
        "faq": [
            {"q": "PRM same as step-level reward?",
             "a": "PRM (Process Reward Model) is a model that produces step-level rewards. The terms are often used interchangeably; PRM is the artifact, step-level reward is the signal."},
            {"q": "How are step labels generated?",
             "a": "Three ways: human annotation (expensive but accurate), automated rollouts (estimate each step's contribution by simulating completions), or rule-based (logical-validity checks for math/code)."},
            {"q": "Step or outcome rewards for RL?",
             "a": "Step rewards converge faster but cost more to collect. Outcome rewards are sample-efficient at scale but slow to learn from. Many production setups combine both."},
            {"q": "Does this require annotated data?",
             "a": "For top quality yes, but Monte Carlo step labelling produces useful pseudo-labels without humans. Hybrid approaches stretch annotation budgets."}
        ]
    },
    # 4. trajectory-reward
    {
        "slug": "trajectory-reward",
        "title": "Trajectory Reward",
        "category": "techniques",
        "difficulty_tier": "advanced",
        "tldr": "Aggregated reward over a complete sequence of agent actions, scoring whole trajectories rather than per-step decisions.",
        "plain_english": "Where step-level rewards score one move, trajectory rewards score the whole game: did this multi-step interaction succeed? Useful when intermediate steps don't have clear correctness but the final outcome does. RL training and best-of-trajectory selection at inference both use trajectory rewards. Common examples: did the agent solve the task, did the customer get their issue resolved, did the code compile after all edits.",
        "how_it_works": "Define an outcome: success-or-fail, scalar quality score, or task-completion percentage. Run the agent through a complete trajectory (multi-step interaction). Score the entire trajectory once at the end. Use the score to update the policy (RL), select among multiple trajectories (best-of-trajectory), or train a value function predicting trajectory rewards from intermediate states. Trajectory rewards are sparser than step rewards but cleaner — they directly target what you care about.",
        "why_it_matters": "Trajectory rewards directly optimise for outcomes, not proxies. For agents and multi-turn systems, this matters: a sequence of plausible-looking steps that fails to solve the problem should be penalised as a unit. They're standard in agent RL training and increasingly used in multi-step inference selection. The trade-off: sparse rewards make learning slower than dense step-level signals.",
        "example": "A coding agent attempts a bug fix with a multi-step trajectory: read code, diagnose, edit, run tests, iterate. Trajectory reward: 1 if all tests pass at the end, 0 otherwise. The agent is trained with PPO on these binary signals; over 100k trajectories it learns to spend its steps productively, even when intermediate progress is unclear.",
        "pitfalls": [
            "Sparse signal: binary trajectory rewards make RL hard; intermediate shaping or step-level rewards help.",
            "Credit assignment: which earlier action caused the failure? Hard to disentangle without auxiliary signals.",
            "Compute cost: completing trajectories takes many forward passes; budget runtime per training step.",
            "Reward hacking: agents find sequences that earn the trajectory reward via shortcuts (e.g. trivial test cases); harden the reward."
        ],
        "when_use": "Use for agent training, multi-step task evaluation, and best-of-trajectory inference where outcome correctness is the right success signal.",
        "when_avoid": "Avoid when intermediate steps must each be correct (legal compliance, financial transactions) where step-level signals are essential.",
        "related_terms": ["step-level-reward", "reward-model", "verifier-model", "agent-loop", "rlhf", "best-of-n"],
        "related_tools": [],
        "faq": [
            {"q": "Trajectory or step rewards?",
             "a": "Step is sample-efficient but expensive to label. Trajectory is sparse but easier to define. Combine when possible."},
            {"q": "How long is a typical trajectory?",
             "a": "Depends on task: 5-20 steps for chat agents, dozens for coding agents, hundreds for game-playing or long research. Length affects sparsity of the signal."},
            {"q": "Can I use trajectory rewards for inference selection?",
             "a": "Yes — sample multiple trajectories, score each, pick the best (best-of-trajectory). Common pattern for high-stakes agent decisions."},
            {"q": "Does this scale to long horizons?",
             "a": "Less well — sparse rewards over thousands of steps make credit assignment hard. Auxiliary step rewards or shaped reward functions help on long horizons."}
        ]
    },
    # 5. budget-forcing
    {
        "slug": "budget-forcing",
        "title": "Budget Forcing",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Inference-time control technique that injects 'wait' or 'rethink' tokens to force a reasoning model to spend more compute before finalising an answer.",
        "plain_english": "A reasoning model produces a thinking trace then commits to an answer. Sometimes the trace is too short — the model gives up before reasoning fully. Budget forcing intervenes: when the model tries to end thinking early, the system inserts a continuation token like 'Wait,' or 'Let me reconsider' that forces another round of reasoning. The result: the model uses more thinking tokens than it would have voluntarily, often producing better answers. It's a way to scale test-time compute on top of any reasoning model.",
        "how_it_works": "Detect when the model emits an end-of-thinking token. Instead of accepting it, replace with a continuation phrase ('Wait,', 'Hmm, but,', 'Let me check') and continue generation. After K such interventions, allow the actual end-of-thinking. Variants: continue until N total thinking tokens are spent, or until verifier confidence exceeds a threshold. The technique was popularised by the s1 paper and similar simple-test-time-scaling research, showing that even small models can be coaxed into longer reasoning with measurable accuracy gains.",
        "why_it_matters": "Budget forcing is one of the simplest inference-time tricks for reasoning quality — no training required, just text replacement on the streaming output. It works on any reasoning model that emits end-of-thinking markers. For teams running smaller reasoning models in production, it's a free quality lift; for larger models, it provides explicit compute-vs-quality trade-off control without retraining.",
        "example": "A team runs a 7B reasoning fine-tune. With default thinking budget the model averages 800 reasoning tokens per math query, scoring 64% on a benchmark. With budget forcing capped at 4000 thinking tokens (5× more), accuracy climbs to 78%. They route hard queries through forced budgets while letting easy queries finish naturally.",
        "pitfalls": [
            "Diminishing returns: more thinking past a task-specific threshold doesn't help and may hurt.",
            "Token cost: forced extra thinking is paid in tokens; budget per-query.",
            "Continuation phrase choice: poor phrases ('Continue:') produce worse continuations than natural ones ('Wait,'); experiment.",
            "Doesn't help bad models: a model that never reasons well won't suddenly reason well with more tokens."
        ],
        "when_use": "Use to push reasoning quality on hard queries beyond the model's default thinking effort, especially when test-time compute is cheaper than swapping in a larger model.",
        "when_avoid": "Avoid for fast-response chat or when the model is already over-thinking and the bottleneck is latency rather than accuracy.",
        "related_terms": ["thinking-budget", "test-time-compute", "reasoning-model", "self-refine", "self-reflection-loop", "best-of-n"],
        "related_tools": [],
        "faq": [
            {"q": "Does budget forcing work on any reasoning model?",
             "a": "Any model that emits clear end-of-thinking tokens. Frontier models with hidden reasoning may not expose the necessary handle; open reasoning models work well."},
            {"q": "What continuation phrase works best?",
             "a": "Natural reflective ones: 'Wait,', 'Let me check,', 'Hmm,'. Avoid imperative ('Continue:') which breaks flow. Sweep options on a small eval."},
            {"q": "How is this different from thinking budget?",
             "a": "Thinking budget is a cap. Budget forcing actively pushes the model to use more thinking than it wanted. The two combine: thinking budget caps total spend, forcing ensures full use up to that cap."},
            {"q": "Can it make reasoning worse?",
             "a": "Sometimes — over-long traces wander and confuse simpler models. Tune K (max forced continuations) per workload."}
        ]
    },
    # 6. multi-token-prediction
    {
        "slug": "multi-token-prediction",
        "title": "Multi-Token Prediction",
        "category": "techniques",
        "difficulty_tier": "advanced",
        "tldr": "Training objective where the model predicts multiple future tokens at each position, improving sample efficiency and enabling fast speculative decoding.",
        "plain_english": "Standard language models predict the next token. Multi-token prediction (MTP) trains the model to predict the next N tokens at every position in parallel — the next-token head plus auxiliary heads for tokens N+1, N+2, etc. This denser supervision improves sample efficiency during training and produces better representations. At inference, the auxiliary heads enable speculative decoding without a separate draft model. DeepSeek-V3 used MTP and reported quality and speed gains.",
        "how_it_works": "Add D extra prediction heads to the model (D typically 1-4). At each training step, position t produces predictions for tokens at t+1, t+2, ..., t+D. Loss is computed across all heads; primary loss on t+1, weighted auxiliary losses on the rest. During inference, the primary head still produces the next token but the auxiliary heads can speculatively propose later tokens, validated by the model itself in subsequent forward passes. DeepSeek-V3's MTP was a major architectural choice contributing to its training and inference efficiency.",
        "why_it_matters": "MTP gives free-ish gains on multiple axes. Training: denser supervision per token, better data efficiency. Inference: speculative decoding without a separate draft model. Quality: marginal improvements from the regularisation effect of multiple heads. The combined wins make it an attractive choice for new pretraining runs, and several follow-up papers extended the technique.",
        "example": "A team training a 7B model adopts MTP with D=4 auxiliary heads. Validation loss converges 8% faster than single-token baseline. At inference, the auxiliary heads enable 1.6× speedup via self-speculation, no separate draft needed. Training and serving cost both drop without quality regression.",
        "pitfalls": [
            "Architecture changes: adding heads requires modifying the model structure; not always trivial in existing checkpoints.",
            "Memory overhead: extra heads need parameters and activations; budget GPU memory.",
            "Auxiliary loss weighting: too high distracts from primary objective; too low and benefits vanish; sweep weights.",
            "Inference complexity: self-speculation requires inference-server support; not yet universal."
        ],
        "when_use": "Use for new pretraining runs aiming at training and inference efficiency, especially at non-trivial scale where the engineering effort is amortised.",
        "when_avoid": "Avoid for fine-tuning existing models without MTP heads (no benefit); avoid when inference stack doesn't support self-speculation.",
        "related_terms": ["assisted-generation", "speculative-decoding", "medusa-heads", "eagle-decoding", "pretraining", "compute-optimal-scaling"],
        "related_tools": [],
        "faq": [
            {"q": "How many auxiliary heads?",
             "a": "1-4 is the common range. More heads add cost without proportional gain past 4. DeepSeek-V3 used a single auxiliary depth-1 head."},
            {"q": "Can I add MTP to an existing model?",
             "a": "You can add heads but they need training. Adding without training gives random outputs. Continued pretraining with the new heads is the path."},
            {"q": "MTP same as Medusa?",
             "a": "Medusa adds heads to a frozen base for inference acceleration. MTP trains heads jointly with the base for both training and inference benefits. Related but distinct."},
            {"q": "Does it improve quality?",
             "a": "Marginally — typically 0.5-1.5 points on standard benchmarks. The training-efficiency and inference-speed gains are usually the main motivation."}
        ]
    },
    # 7. cot-faithfulness
    {
        "slug": "cot-faithfulness",
        "title": "Chain-of-Thought Faithfulness",
        "category": "safety",
        "difficulty_tier": "intermediate",
        "tldr": "Property of a chain-of-thought trace that the stated reasoning actually drove the final answer, rather than the answer being decided independently and rationalised.",
        "plain_english": "Chain-of-thought looks like the model's reasoning. Sometimes it's not — the model decides the answer first, then writes a plausible-looking trace as post-hoc rationalisation. Faithful CoT means the steps actually drove the answer; if you change the steps, the answer would change. Unfaithful CoT means the trace is decorative — pretty to read but not causal. Faithfulness matters because we treat traces as evidence the model is reasoning correctly; unfaithful traces hide the actual decision process.",
        "how_it_works": "Test for faithfulness by interventions: corrupt the trace mid-way and check whether the answer changes. If the answer is robust to corruption, the trace wasn't doing the work. Common probes: insert irrelevant filler, swap intermediate conclusions, remove key steps. Faithful chains break under these interventions; unfaithful ones survive. Anthropic and others have published extensive research showing that unfaithful CoT is common, especially under social pressure or when the model has been fine-tuned to produce certain answer formats.",
        "why_it_matters": "We use CoT to debug models, audit reasoning, and build trust. Unfaithful CoT undermines all three: a model that produces good-looking traces while actually deciding via biases is harder to trust than one that's transparently wrong. Faithfulness research is central to interpretability and safety work, and influences how seriously we should take a model's stated reasoning.",
        "example": "Researchers ask a model multiple-choice questions with the correct answer biased in the prompt order ('A' is always correct in 80% of training examples). The model gets the answer right, with chain-of-thought that doesn't mention position bias. Intervention: shuffle answers; the model still picks position A even when the content moves. Conclusion: CoT was rationalising a position-based shortcut, not reasoning.",
        "pitfalls": [
            "Confusing plausible with faithful: a coherent trace isn't proof of faithfulness; intervention tests are required.",
            "Sycophancy under pressure: faithfulness drops when models are pressed to agree with prior turns; multi-turn faithfulness is its own concern.",
            "Faithfulness vs correctness: a faithful trace can lead to wrong answers; an unfaithful trace can lead to right answers. Both matter independently.",
            "Test design: interventions must preserve task semantics, otherwise you measure prompt-sensitivity rather than faithfulness."
        ],
        "when_use": "Use the framing in interpretability work, safety evaluations, and any context where you rely on chain-of-thought for trust or debugging.",
        "when_avoid": "Don't use CoT-as-evidence in regulated decisions without faithfulness testing; the trace may not reflect the actual decision process.",
        "related_terms": ["chain-of-thought", "mechanistic-interpretability", "shortcut-learning", "deceptive-alignment", "red-teaming", "ai-governance"],
        "related_tools": [],
        "faq": [
            {"q": "Are reasoning models more faithful?",
             "a": "Mixed evidence. Reasoning models trained on process rewards tend to be more faithful than CoT-prompted base models, but unfaithfulness still occurs."},
            {"q": "How do I test faithfulness in my system?",
             "a": "Run intervention tests on a sample: corrupt traces, check whether answers change. Stable answers under corruption indicate unfaithfulness."},
            {"q": "Does fine-tuning improve faithfulness?",
             "a": "It can — process supervision tends to help. RLHF without explicit faithfulness signals can hurt because models learn to produce confident-sounding traces."},
            {"q": "Should I use unfaithful traces for debugging?",
             "a": "Cautiously. They may reflect what the model 'wanted to say' rather than what it computed; debug with multiple methods, not traces alone."}
        ]
    },
    # 8. reasoning-trace
    {
        "slug": "reasoning-trace",
        "title": "Reasoning Trace",
        "category": "concepts",
        "difficulty_tier": "intermediate",
        "tldr": "The visible or logged sequence of intermediate steps a model takes between input and final answer, used for debugging, auditing, and training data.",
        "plain_english": "A reasoning trace is the model's working — the chain of intermediate thoughts before the answer. For chat models prompted with chain-of-thought, the trace appears in the output. For reasoning models like o1, R1, and Claude with extended thinking, traces live in dedicated thinking sections, sometimes hidden from users but exposed to APIs. Traces are useful for debugging (where did reasoning fail?), distillation (train smaller models on bigger model's traces), and audits (what did the model 'think' before answering?).",
        "how_it_works": "The model emits intermediate text — calculations, hypotheses, self-corrections — before the final answer. APIs expose traces via dedicated channels (thinking_content for Claude, reasoning_summary for OpenAI, full thinking for many open models). Traces can be parsed, scored (faithfulness, length, error rate), and stored for analysis. For reasoning-distillation, traces become training data: the student learns to produce similar traces. For auditing, stored traces enable post-hoc investigation when answers are wrong.",
        "why_it_matters": "Reasoning traces are the closest thing we have to a model's 'work shown'. They support debugging at scale, enable distillation, and provide partial transparency into model behaviour. As reasoning models become standard, traces are increasingly first-class API objects with their own pricing, latency, and storage characteristics. Understanding traces is part of working with modern LLMs.",
        "example": "A code-generation system saves reasoning traces for every customer query. When a user reports a wrong answer, support pulls the trace and sees the model misread the requirement at step 3, leading to a wrong final solution. The team adds clarification prompts for similar requirements, and the support workflow now uses traces as standard debugging artefacts.",
        "pitfalls": [
            "Trace cost: thinking tokens are billed separately and can dwarf answer tokens; budget per query.",
            "Privacy: traces contain user data and intermediate guesses; treat them with the same care as full conversations.",
            "Faithfulness: traces aren't always causally connected to answers (see CoT faithfulness); use carefully as evidence.",
            "Storage volume: at scale, trace storage becomes a real cost; consider sampling or summarising older traces."
        ],
        "when_use": "Use traces for debugging production issues, distilling reasoning into smaller models, auditing high-stakes outputs, or showing 'work shown' to power users.",
        "when_avoid": "Avoid surfacing raw traces in user-facing UI for casual users (often confusing). Avoid retaining traces indefinitely for privacy.",
        "related_terms": ["reasoning-model", "thinking-budget", "chain-of-thought", "cot-faithfulness", "reasoning-distillation", "ai-observability"],
        "related_tools": [],
        "faq": [
            {"q": "Can I see reasoning traces from o1?",
             "a": "OpenAI exposes a reasoning summary, not the full trace. Other providers (Anthropic, DeepSeek) expose more. Provider-dependent."},
            {"q": "Should I bill users for thinking tokens?",
             "a": "If your provider charges you for them (most do), pass through. Some teams absorb thinking cost as a quality differentiator and only bill answer tokens."},
            {"q": "Are traces safe to log?",
             "a": "Treat as sensitive — they contain user prompts and possibly intermediate sensitive content. Apply the same redaction and retention policies as conversation logs."},
            {"q": "How long is a typical trace?",
             "a": "100-10,000 tokens depending on task. Math and code tasks tend to be longer; chat-style queries shorter."}
        ]
    },
    # 9. parent-child-rag
    {
        "slug": "parent-child-rag",
        "title": "Parent-Child RAG",
        "category": "rag-internals",
        "difficulty_tier": "intermediate",
        "tldr": "Retrieval pattern that searches small focused chunks but returns the larger parent passages around them for richer context to the LLM.",
        "plain_english": "Small chunks (sentences, paragraphs) retrieve more precisely; large chunks (sections, pages) provide better context for generation. Parent-child RAG gives you both: index and search small chunks, but when one matches return the larger parent it lives inside. Precision of small-chunk retrieval, context of large-chunk generation. Avoids the trade-off where small chunks lose context and big chunks dilute relevance.",
        "how_it_works": "At indexing time, split documents into small child chunks for retrieval and store a parent-chunk reference for each. The retriever searches over child embeddings. When a child matches, fetch its parent chunk (or N siblings) and pass to the LLM. Different variants: parent-document retriever (parent is the whole document), small-to-big (multi-level hierarchy), section-as-parent (parent is the section containing the matched paragraph). LangChain and LlamaIndex ship pre-built parent-child retrievers.",
        "why_it_matters": "RAG quality often depends on chunk granularity. Too small and you retrieve a sentence without surrounding context. Too big and the LLM loses focus among irrelevant prose. Parent-child gives the best of both: precise retrieval, rich context, no compromise. For document-heavy RAG (manuals, legal text, research papers), it consistently improves answer quality.",
        "example": "A product-docs assistant indexes chunks of 100 tokens each but stores section-level parents (~1000 tokens). A user asks a specific question; child retrieval finds the precise paragraph; the LLM receives the full section as context. Answer quality is noticeably better than retrieving 1000-token chunks directly because retrieval was precise and context was rich.",
        "pitfalls": [
            "Parent size: too-large parents drown the answer in irrelevant text; cap parent size with section boundaries.",
            "Parent granularity: should parents be sections, paragraphs, or chapters? Depends on document type; benchmark.",
            "Storage overhead: indexing children + storing parent references adds storage; usually negligible vs. quality wins.",
            "Multiple matches: two children may share a parent; deduplicate parent passages before sending to LLM."
        ],
        "when_use": "Use for RAG over structured long documents — manuals, books, legal text, research papers, technical guides — where small-chunk precision and large-chunk context both matter.",
        "when_avoid": "Avoid for very short documents (no parent/child distinction) or when single-chunk retrieval already meets quality.",
        "related_terms": ["parent-document-retriever", "rag", "semantic-chunking", "retrieval", "small-to-big-retrieval", "sentence-window-retrieval"],
        "related_tools": ["langchain", "llamaindex"],
        "faq": [
            {"q": "How big should parents be?",
             "a": "Match natural document structure: section-level (500-2000 tokens) for manuals, paragraph-level for FAQs. Cap to fit LLM context budget."},
            {"q": "Children of what size?",
             "a": "Often 50-200 tokens. Small enough for precise embedding match, large enough to be semantically meaningful."},
            {"q": "Can children overlap parents?",
             "a": "Each child has one parent in the basic pattern. Hierarchical variants allow children to belong to multiple levels of parent."},
            {"q": "Does this combine with reranking?",
             "a": "Yes — rerank at the child level before fetching parents. This is the most common production pattern."}
        ]
    },
    # 10x. colbert-rag
    {
        "slug": "colbert-rag",
        "title": "ColBERT RAG",
        "category": "rag-internals",
        "difficulty_tier": "advanced",
        "tldr": "RAG architecture that uses ColBERT-style late interaction for retrieval, combining strong semantic matching with the efficiency of pre-computed token embeddings.",
        "plain_english": "ColBERT computes a vector per token in each document and per token in each query, then matches token-to-token at search time (late interaction). Compared to single-vector retrieval (one embedding per chunk), it captures finer semantic alignment. Compared to cross-encoders, it's much faster because document tokens are precomputed. ColBERT RAG plugs this retrieval into a generative pipeline, typically as a strong first-stage retriever or a reranker over candidates from a cheaper first stage.",
        "how_it_works": "Index documents with ColBERT or ColBERTv2 to produce per-token embedding sets. At query time, embed the query tokens and compute MaxSim — for each query token, find its highest-similarity document token, sum across query tokens. Top-k documents win. PLAID and other compression techniques shrink storage. Pipelines either use ColBERT as primary retriever (slower but more accurate than dense) or as a reranker over BM25/dense top-100. Vespa, Qdrant (with multi-vector), and dedicated ColBERT serving stacks support production deployment.",
        "why_it_matters": "Single-vector dense retrieval is fast but coarse. Cross-encoders are accurate but slow. ColBERT bridges them: nearly cross-encoder quality at much higher throughput than cross-encoders. For production RAG that cares about retrieval quality on the long tail of queries — legal, medical, technical search — ColBERT-style late interaction is increasingly standard.",
        "example": "A legal-research RAG starts with BM25 + dense retrieval, then re-ranks top-100 candidates with ColBERTv2. Top-10 NDCG climbs 12 points over single-vector retrieval. End-to-end answer quality improves measurably; per-query latency rises ~50ms. The team deploys behind their existing vector store using a ColBERT-aware reranker.",
        "pitfalls": [
            "Storage cost: per-token embeddings inflate index size 30-100×; PLAID and similar compression mitigate.",
            "Tokenizer alignment: query and document must use the same tokenizer; mismatches break MaxSim semantics.",
            "Implementation maturity: vanilla vector DBs don't all support multi-vector retrieval; check.",
            "Cost vs. cross-encoder: at small scale, a cross-encoder reranker may be simpler and almost as good; ColBERT shines at millions-of-docs scale."
        ],
        "when_use": "Use for retrieval-quality-critical RAG over corpora large enough to make cross-encoder reranking too slow; ColBERT bridges speed and quality.",
        "when_avoid": "Avoid for small corpora where cross-encoder reranking is feasible, or when storage budget can't accommodate per-token embeddings.",
        "related_terms": ["late-interaction", "reranking", "rag", "dense-retrieval", "bi-encoder", "cross-encoder"],
        "related_tools": ["vespa", "qdrant"],
        "faq": [
            {"q": "ColBERT or cross-encoder reranker?",
             "a": "ColBERT scales to millions of documents; cross-encoders top out at thousands. For larger corpora, ColBERT wins; for smaller, cross-encoder is simpler."},
            {"q": "What's MaxSim?",
             "a": "The score between a query and a document in ColBERT: for each query token, find the maximum cosine similarity to any document token, then sum across query tokens."},
            {"q": "Does ColBERT replace dense retrieval?",
             "a": "Often complements: dense for first-stage candidate generation, ColBERT for reranking. Sometimes ColBERT is primary if storage permits."},
            {"q": "Is ColBERTv2 the current standard?",
             "a": "Yes — it added denoising and PLAID compression to make production deployment feasible. ColBERTv1 was the research breakthrough; v2 is the production version."}
        ]
    },
    # 11. fusion-decoder
    {
        "slug": "fusion-decoder",
        "title": "Fusion Decoder",
        "category": "rag-internals",
        "difficulty_tier": "advanced",
        "tldr": "RAG architecture where the decoder attends to multiple retrieved passages independently encoded, fusing evidence at decoding time rather than via concatenation.",
        "plain_english": "Standard RAG concatenates retrieved passages into one prompt. Fusion-in-Decoder (FiD) keeps them separate: each passage is encoded independently, and the decoder attends across all of them when generating. The model sees evidence as parallel streams instead of one long stream. This scales better with passage count and reduces interference between unrelated retrievals.",
        "how_it_works": "Encode N retrieved passages separately with the encoder, producing N independent encoded sequences. The decoder uses cross-attention over the union of all encoder outputs at every decoding step. Variants include FiD-Light (compress encoder outputs before decoding), Atlas (joint retrieval+generation training), and modern decoder-only adaptations that simulate FiD via interleaved prompting. Original FiD requires encoder-decoder architecture; many modern decoder-only LLMs approximate the benefit through structured prompting.",
        "why_it_matters": "Concatenation-based RAG hits a wall with large numbers of passages: context bloat, cross-passage interference, attention dilution. FiD scales more gracefully because each passage gets its own encoder pass and the decoder picks what to use. For multi-source synthesis (combining facts from many docs), FiD-style architectures consistently outperform concatenation at high passage counts.",
        "example": "A research-summary system retrieves 20 passages per query. Concatenated, they overflow the context window. With FiD, each encodes separately; the decoder attends across all 20 and produces a coherent multi-source summary. End-to-end quality matches or beats concatenation, and the system handles documents of any length without trimming.",
        "pitfalls": [
            "Architecture lock-in: classical FiD needs encoder-decoder; decoder-only LLMs approximate via prompting tricks but don't get full benefit.",
            "Compute cost: encoding N passages independently is N× the encoder cost vs. one concatenated pass; budget accordingly.",
            "Training: end-to-end training that learns retrieval + generation jointly (Atlas) is expensive; off-the-shelf FiD variants are cheaper.",
            "Modern alternatives: long-context decoder-only models with sparse attention may match FiD without the architectural split."
        ],
        "when_use": "Use for multi-document RAG with many passages per query, especially summary or synthesis tasks where evidence comes from diverse sources.",
        "when_avoid": "Avoid for simple single-passage RAG where concatenation works and the FiD architecture adds complexity without benefit.",
        "related_terms": ["rag", "retrieval", "fid", "encoder-decoder", "context-window", "long-context-benchmark"],
        "related_tools": [],
        "faq": [
            {"q": "FiD same as fusion decoder?",
             "a": "FiD (Fusion-in-Decoder) is the canonical implementation by Izacard & Grave 2021. 'Fusion decoder' is the general pattern; FiD is the specific architecture."},
            {"q": "Does it work with decoder-only LLMs?",
             "a": "Not directly — FiD's mechanism requires separate encoder passes. Decoder-only approximations exist but lack the full benefit."},
            {"q": "How many passages can FiD handle?",
             "a": "Hundreds, in principle. Practical limits come from encoder-pass cost and decoder attention complexity."},
            {"q": "Does this improve hallucination?",
             "a": "Often yes — better evidence integration tends to ground answers more reliably. Combine with faithfulness checks for assurance."}
        ]
    },
    # 12. fid
    {
        "slug": "fid",
        "title": "FiD",
        "category": "rag-internals",
        "difficulty_tier": "advanced",
        "tldr": "Fusion-in-Decoder — encoder-decoder RAG architecture that processes retrieved passages independently then fuses them via decoder cross-attention.",
        "plain_english": "FiD is the canonical implementation of the fusion-decoder pattern. Each retrieved passage gets its own encoder pass; the decoder cross-attends across all encoded passages while generating. Because passages don't interfere during encoding, FiD handles many more passages than concatenation-based RAG, and was state-of-the-art on open-domain QA when introduced. Modern systems often use FiD-Light or decoder-only approximations.",
        "how_it_works": "Given a query and N retrieved passages: prefix each passage with the query, encode each independently to get N hidden states. The decoder generates the answer with cross-attention over the concatenation of all N encoder hidden states. Training uses standard seq2seq loss. FiD-Light reduces decoder cross-attention compute by averaging or selecting subsets of encoder outputs. The Atlas paper extended FiD with joint retrieval+generation training. T5 and Flan-T5 are common encoder-decoder bases for FiD.",
        "why_it_matters": "FiD is a foundational RAG architecture and remains a strong baseline for retrieval-heavy QA systems. It demonstrated that fusing evidence at decode time beats concatenation for multi-source synthesis. Many modern systems descend from FiD's idea even when implemented in decoder-only models. Knowing FiD is part of being literate in RAG architecture choices.",
        "example": "A team building open-domain QA on Wikipedia uses FiD with T5-large. They retrieve 100 passages per query and let the decoder fuse. Performance on Natural Questions matches contemporary state-of-the-art. The ability to use 100 passages without context overflow was the key advantage over concatenation-based baselines.",
        "pitfalls": [
            "Tied to encoder-decoder: FiD assumes T5-style architecture; pure decoder-only LLMs need different tricks.",
            "Encoder-cost scaling: 100 passages = 100 encoder passes; latency and compute scale linearly with N.",
            "Joint training is expensive: Atlas-style retrieval+generation training requires substantial GPU budget.",
            "Out-of-fashion at frontier: long-context decoder-only models have largely supplanted FiD for new systems; FiD remains relevant where encoder-decoder is preferred."
        ],
        "when_use": "Use for encoder-decoder RAG systems with many retrieved passages per query, especially open-domain QA and multi-source synthesis tasks.",
        "when_avoid": "Avoid for decoder-only LLM stacks where you'd need to approximate FiD's mechanics; long-context decoder-only models often serve better.",
        "related_terms": ["fusion-decoder", "rag", "retrieval", "encoder-decoder", "context-window", "long-context-benchmark"],
        "related_tools": [],
        "faq": [
            {"q": "FiD vs RAG-token vs RAG-sequence?",
             "a": "RAG-token marginalises over passages per token; RAG-sequence picks one passage per output. FiD fuses all passages via decoder cross-attention. FiD typically performs best with many passages."},
            {"q": "Is FiD still relevant?",
             "a": "Yes for encoder-decoder stacks. For decoder-only LLMs (most modern), long-context approaches have largely replaced it."},
            {"q": "What base model for FiD?",
             "a": "T5 family is canonical (T5-base, T5-large, Flan-T5). Newer encoder-decoder models work too. Decoder-only models need adaptation."},
            {"q": "Does FiD train end-to-end with retrieval?",
             "a": "Atlas does (jointly trains retriever and generator). Vanilla FiD trains the generator only on labelled (query, retrieved passages, answer) triples."}
        ]
    },
    # 13. metadata-prefiltering
    {
        "slug": "metadata-prefiltering",
        "title": "Metadata Pre-Filtering",
        "category": "rag-internals",
        "difficulty_tier": "intermediate",
        "tldr": "Restricting retrieval to documents matching structured metadata constraints (date, source, customer) before semantic similarity search.",
        "plain_english": "Semantic search alone retrieves anything similar; metadata prefiltering narrows the candidate set first. 'Find docs about pricing where source=helpcenter and updated_after=2025'. The vector search then only considers matching documents. This combines structured and unstructured search, eliminates obviously-wrong matches, and is essential for multi-tenant systems where customers must only see their own data.",
        "how_it_works": "Documents are indexed with metadata fields (source, date, customer_id, language, document_type). At query time, build a metadata filter expression alongside the semantic query. The vector store applies the filter — exact-match, range, or boolean combinations — before similarity scoring, returning only candidates that meet both criteria. Major vector stores (Pinecone, Qdrant, Weaviate, Milvus, pgvector) support metadata filters with varying capabilities. Filter-then-search vs. search-then-filter affects performance; mature stores choose internally.",
        "why_it_matters": "Pure semantic search returns plausible-but-wrong matches when the corpus is heterogeneous. Metadata pre-filtering gives RAG production-grade scoping: per-tenant isolation, recency-weighted retrieval, language-aware search, and source-restricted answers. For B2B SaaS using LLMs over customer data, metadata filters are how you get correctness and isolation guarantees in one mechanism.",
        "example": "A multi-tenant docs assistant has 10M chunks across 1000 customers. Each query is filtered to customer_id and a recency window. Without prefiltering, vector search would return matches across tenants (privacy violation) and surface stale content. With prefiltering, every retrieval is scoped correctly and quality is consistent across tenants.",
        "pitfalls": [
            "Filter selectivity: highly selective filters (one customer of 1000) can underuse the index; tuning per-store may be needed.",
            "Metadata staleness: documents move/update; metadata indexes must keep pace or filter results drift.",
            "Combinator complexity: deep boolean filter trees slow some stores; flatten where possible.",
            "Filter vs scoring trade: rare metadata combos may bypass good cache locality; benchmark."
        ],
        "when_use": "Use for any production RAG with structured corpus dimensions: multi-tenant, time-sensitive, multi-language, multi-source. Essential for B2B and regulated deployments.",
        "when_avoid": "Avoid the framing for tiny single-tenant corpora where metadata adds overhead without operational benefit.",
        "related_terms": ["rag", "retrieval", "vector-database", "metadata-filtering", "time-decay-retrieval", "semantic-chunking"],
        "related_tools": ["pinecone", "qdrant"],
        "faq": [
            {"q": "Pre-filter or post-filter?",
             "a": "Pre-filter (apply metadata first, search after) is usually faster and more correct. Post-filter (search first, drop non-matching) wastes compute on rejects. Most modern stores prefer pre-filter."},
            {"q": "Can I use metadata for ranking, not just filtering?",
             "a": "Yes — many stores support metadata-weighted scoring (boost recent docs, favour authoritative sources). It's a separate mechanism from prefiltering and complements it."},
            {"q": "What metadata fields matter most?",
             "a": "tenant_id, document_type, source, language, recency timestamp, doc-version. Tailor to your domain — legal might add jurisdiction, medical might add specialty."},
            {"q": "Does this work with hybrid search?",
             "a": "Yes — metadata prefiltering is orthogonal to whether you use sparse, dense, or hybrid retrieval. All three benefit from scoping."}
        ]
    },
    # 14. time-decay-retrieval
    {
        "slug": "time-decay-retrieval",
        "title": "Time-Decay Retrieval",
        "category": "rag-internals",
        "difficulty_tier": "intermediate",
        "tldr": "Retrieval scoring that down-weights older documents over time, so freshness contributes alongside semantic similarity to ranking.",
        "plain_english": "In domains where recency matters — news, prices, product info, regulations — semantic similarity isn't enough. Time-decay retrieval adds a freshness signal: older documents lose score over time, so newer relevant docs surface above older ones. The decay rate is a knob: aggressive decay surfaces only recent content; gentle decay still respects older but high-quality docs.",
        "how_it_works": "Each document carries a timestamp. At query time, compute the document's age (days since timestamp). Apply a decay function to the similarity score: score' = score × decay(age). Common decay shapes: exponential (score × exp(-age/τ)), linear, or step function. The decay constant τ depends on domain — news might decay over days, technical docs over years. Combine with metadata prefiltering for hard recency cuts and decay for soft preference.",
        "why_it_matters": "Pure semantic search returns the most-similar doc regardless of age. In fast-moving domains this surfaces stale answers. Time-decay retrieval bakes freshness into ranking without manual filtering, balancing relevance and recency. It's a small change with large quality impact for time-sensitive RAG.",
        "example": "A news-summary RAG retrieves articles about ongoing events. Without decay, a year-old in-depth article ranks above today's update. With exponential decay over 7 days, the new article wins; the old one still appears for queries it uniquely covers. Users see fresh, relevant context.",
        "pitfalls": [
            "Decay rate tuning: too aggressive and good old content disappears; too gentle and stale matches still win; tune per domain.",
            "Mixed-age corpora: hard time floors plus soft decay handle this better than decay alone.",
            "Timestamps quality: decay assumes accurate timestamps; missing or wrong timestamps break ranking; default to 'unknown ⇒ no decay' carefully.",
            "User intent: not all queries want recency; for historical questions, decay actively harms; consider per-query intent classification."
        ],
        "when_use": "Use for time-sensitive corpora — news, prices, product catalogs, regulations, support tickets — where freshness matters alongside relevance.",
        "when_avoid": "Avoid for stable corpora (textbooks, archived legal codes) where age doesn't predict relevance.",
        "related_terms": ["recency-boost", "rag", "retrieval", "metadata-prefiltering", "embedding-drift", "drift-detection"],
        "related_tools": [],
        "faq": [
            {"q": "Decay function shape: exponential or linear?",
             "a": "Exponential (smooth, half-life-based) is the most common. Linear is simpler but creates abrupt cutoffs. Pick by domain dynamics."},
            {"q": "Decay or hard date cutoff?",
             "a": "Decay is softer and preserves older relevant content. Hard cutoffs are simpler and clearer when there's a clear staleness threshold."},
            {"q": "How do I tune the decay constant?",
             "a": "Pick a half-life (when score halves): days for news, months for tech docs, years for legal. Validate on click-through or labelled relevance data."},
            {"q": "Does this hurt long-tail queries?",
             "a": "Possibly — historical queries that genuinely want old docs suffer. Combine with intent classification or per-query decay tuning to mitigate."}
        ]
    },
    # 15. recency-boost
    {
        "slug": "recency-boost",
        "title": "Recency Boost",
        "category": "rag-internals",
        "difficulty_tier": "beginner",
        "tldr": "Search-ranking technique that adds a positive bonus to recently-published documents, complementing semantic relevance with freshness preference.",
        "plain_english": "Where time-decay retrieval down-weights old content, recency boost up-weights new content. Functionally similar but framed positively: 'reward fresh docs' vs 'penalise stale ones'. Used widely in search and RAG for any domain where new is usually better. Often implemented as an additive bonus to similarity score — say, +5% per week of age younger than 30 days, capped after a threshold.",
        "how_it_works": "After computing semantic similarity, apply a recency function: bonus = max(0, threshold_days - age_days) × weight. Add to the similarity score. Variants use multiplicative boosts (similarity × (1 + recency_factor)), step functions (boost up to 7 days, none after), or learned recency-weighted models. The boost shape and magnitude are hyperparameters tuned per domain. Many search platforms (Elastic, Vespa) ship recency-boost primitives.",
        "why_it_matters": "Recency boost is the most user-visible quality lever for time-sensitive content. It's easy to implement, easy to tune, and consistently improves perceived quality on fast-moving topics. The framing 'reward fresh' is more intuitive for product teams than 'penalise old' (decay), even though they're mathematically related.",
        "example": "A help-desk RAG handles tickets where solutions evolve. Without recency boost, retrieval often returns articles from 2022 about a feature that changed in 2025. Adding a boost of +20% for docs newer than 90 days flips the ranking: 2025 articles surface first, 2022 only when no fresh content exists.",
        "pitfalls": [
            "Boost magnitude: too large and recency overrides relevance; too small and it's invisible; calibrate.",
            "Threshold cliff: hard step boosts create unnatural ranking jumps; smooth boosts (graduated) feel more natural.",
            "Gaming: in user-published corpora, sources spam recent dates to game ranking; verify timestamp authenticity.",
            "Older-but-better content disappears: classic posts that remain relevant get demoted; combine with quality signals."
        ],
        "when_use": "Use for any time-sensitive search or RAG corpus where users typically prefer recent content. Default in news, e-commerce, support tickets.",
        "when_avoid": "Avoid when content is timeless (academic papers, foundational documentation) where age doesn't predict utility.",
        "related_terms": ["time-decay-retrieval", "rag", "retrieval", "metadata-prefiltering", "embedding-drift", "drift-detection"],
        "related_tools": [],
        "faq": [
            {"q": "Recency boost or time-decay?",
             "a": "They're often interchangeable mathematically. Boost is more intuitive product framing; decay is more common in academic literature."},
            {"q": "How big should the boost be?",
             "a": "5-30% relative score bump for very recent docs is typical. Tune against user click-through or labelled freshness preferences."},
            {"q": "Does recency boost work with reranking?",
             "a": "Yes — apply at the reranking stage for fine control, or at the initial retrieval scoring stage for cheaper effect."},
            {"q": "What's a reasonable freshness threshold?",
             "a": "Domain-dependent: hours for breaking news, days for product help, weeks for industry trends, months/years for legal/medical reference."}
        ]
    },
    # 16. maximal-marginal-relevance
    {
        "slug": "maximal-marginal-relevance",
        "title": "Maximal Marginal Relevance (MMR)",
        "category": "rag-internals",
        "difficulty_tier": "intermediate",
        "tldr": "Reranking algorithm that balances similarity to query with diversity among results, surfacing varied documents instead of near-duplicates.",
        "plain_english": "Pure relevance retrieval often returns 5 near-duplicate top results — small variants saying the same thing. MMR fixes this by adding a diversity term: each result is scored as relevance to the query minus similarity to already-selected results. The first pick is the most relevant; subsequent picks balance relevance with novelty. Final list covers more aspects of the query.",
        "how_it_works": "Start with N candidate results from retrieval. Iteratively select results: first pick is most relevant. Each subsequent pick maximises λ × similarity(candidate, query) - (1 - λ) × max_similarity(candidate, selected). λ controls the trade-off (1.0 = pure relevance, 0.0 = pure diversity). Stop after K picks. Carbonell & Goldstein 1998 introduced MMR for IR; modern implementations use embedding similarity for both terms.",
        "why_it_matters": "RAG over redundant corpora (multiple docs covering the same topic) returns repetitive context that wastes the LLM's context window. MMR diversifies retrieval so the LLM sees N varied passages instead of N copies of the same idea. Result: better grounded answers for queries that span multiple aspects, reduced hallucination from over-narrow context.",
        "example": "A user asks 'what does this product do?' Top retrieval returns 5 marketing snippets all saying the same thing. With MMR (λ=0.7), top results include marketing, technical specs, customer testimonial, FAQ, and pricing — each adds new info. The LLM-generated answer is more comprehensive.",
        "pitfalls": [
            "λ tuning: too low and irrelevant-but-diverse results contaminate the set; too high and you get duplicates; sweep on validation.",
            "Compute cost: O(N²) similarity comparisons; with hundreds of candidates this matters.",
            "Diversity definition: similarity-based diversity may not match conceptual diversity; consider clustering-based variants for thematic spread.",
            "Hurts narrow queries: when the user really wants one specific thing, MMR returns less-relevant alternatives; intent classification helps."
        ],
        "when_use": "Use for queries that span multiple aspects, retrieval over redundant corpora, or when users want comprehensive answers (research-style queries).",
        "when_avoid": "Avoid for narrow factual queries where one specific answer dominates; pure relevance suffices.",
        "related_terms": ["rag", "retrieval", "reranking", "cluster-retrieval", "rag-fusion", "reciprocal-rank-fusion"],
        "related_tools": ["langchain", "llamaindex"],
        "faq": [
            {"q": "Recommended λ value?",
             "a": "0.5-0.7 is a common starting point. Higher (0.8+) for narrow queries, lower (0.3-0.5) for exploratory or research queries."},
            {"q": "Does MMR work with hybrid retrieval?",
             "a": "Yes — apply MMR to the unified candidate set. Diversity is independent of how candidates were retrieved."},
            {"q": "Can I use MMR for multi-document summarisation?",
             "a": "Yes — that's its original IR use. Pick K diverse passages then summarise. Common pattern in research-heavy applications."},
            {"q": "Is there a learned alternative?",
             "a": "Yes — diversity-aware rerankers and listwise models. MMR remains popular because it's simple and works without training data."}
        ]
    },
    # 17. cluster-retrieval
    {
        "slug": "cluster-retrieval",
        "title": "Cluster Retrieval",
        "category": "rag-internals",
        "difficulty_tier": "advanced",
        "tldr": "Retrieval architecture that pre-clusters documents and routes queries to the most relevant cluster(s), trading some recall for substantial speed and cost gains.",
        "plain_english": "Searching a million-vector index per query is expensive. Cluster retrieval pre-groups documents into clusters (e.g. by k-means on embeddings), then at query time matches the query to a few clusters and only searches within them. Much faster than scanning everything; small recall hit when relevant docs end up in unsearched clusters. IVF (inverted file index) is the canonical implementation.",
        "how_it_works": "Index time: cluster all document embeddings into K centroids (k-means or similar). Each document is associated with its nearest centroid. Query time: compute query embedding, find the M nearest centroids, search only documents in those clusters. K and M trade off speed vs. recall: many small clusters with low M is fast but loses recall; few big clusters with high M is slow but accurate. FAISS, Qdrant, Pinecone, Vespa all implement IVF or related cluster-retrieval patterns.",
        "why_it_matters": "At million-vector and billion-vector scales, cluster retrieval is the difference between practical and impractical search. Modern vector DBs default to IVF or HNSW (graph-based; conceptually related). For most production RAG, you're using cluster retrieval whether you know it or not. Understanding it helps tune the speed-vs-recall trade-off explicitly.",
        "example": "A search platform indexes 50M document embeddings. Brute-force search per query takes 800ms — too slow. With IVF and K=4096 clusters, M=8 probed per query, latency drops to 12ms with recall@10 of 96%. The 4% recall loss is recovered by reranking the top 100 candidates with a cross-encoder.",
        "pitfalls": [
            "Cluster quality: bad clustering puts related docs in different clusters, hurting recall; choose K and clustering algo carefully.",
            "M-tuning: too low M misses relevant clusters; too high defeats the purpose; sweep on a held-out eval.",
            "Static clustering: as docs grow, clusters become unbalanced; periodic reclustering helps.",
            "OOD queries: queries far from any centroid get poor results; combine with fallback strategies."
        ],
        "when_use": "Use for retrieval at scale (>100k vectors) where brute-force is too slow. Modern vector DBs handle this transparently; understanding it helps tune performance.",
        "when_avoid": "Avoid for small indices (<100k vectors) where brute-force is faster than the clustering overhead.",
        "related_terms": ["ivf", "hnsw", "vector-database", "retrieval", "dense-retrieval", "embedding"],
        "related_tools": ["faiss", "qdrant"],
        "faq": [
            {"q": "Cluster retrieval or HNSW?",
             "a": "Both are approximate nearest-neighbour techniques. IVF (cluster) is simpler and uses less memory; HNSW (graph) is faster on most workloads but more memory-heavy. Many systems support both."},
            {"q": "How many clusters?",
             "a": "Roughly sqrt(N) where N is total vectors is a starting heuristic. 4096 clusters for 16M vectors is typical; tune from there."},
            {"q": "How many to probe?",
             "a": "M=8-32 is common. Higher M increases recall and latency. Sweep on your eval set."},
            {"q": "Does product quantization help?",
             "a": "Yes — combines cluster retrieval with compression so each vector takes less memory. IVF+PQ is standard in many vector DBs."}
        ]
    },
    # 18. sparse-vector
    {
        "slug": "sparse-vector",
        "title": "Sparse Vector",
        "category": "rag-internals",
        "difficulty_tier": "intermediate",
        "tldr": "High-dimensional vector with mostly zero entries representing token frequencies or learned activations, used in lexical or hybrid retrieval.",
        "plain_english": "Dense vectors (from neural embeddings) have a value in every dimension. Sparse vectors have a value only in a few dimensions and zeros elsewhere. Classical examples: TF-IDF, BM25 — each dimension is a word, value is its weighted frequency. Modern learned sparse vectors (SPLADE, BM42) extend this with neural networks that learn which dimensions matter. Sparse vectors capture exact-term matches (great for unique names, technical IDs) where dense embeddings struggle.",
        "how_it_works": "Sparse representations encode documents and queries in vocabulary space. Classical lexical: count term frequencies, apply IDF weighting, normalise. Learned sparse: a transformer outputs a sparse activation per token expanded to vocab space (SPLADE, BM42). Search uses inverted indices that map token → posting list of (doc_id, weight) pairs; query terms intersect posting lists efficiently. Modern vector DBs and search platforms (Qdrant, Vespa, Elasticsearch with vector extensions) support sparse vectors alongside dense.",
        "why_it_matters": "Dense embeddings excel at semantic matching but miss exact lexical signals — proper nouns, codes, IDs. Sparse vectors capture these reliably. Hybrid retrieval combining sparse and dense outperforms either alone on diverse query distributions. As learned sparse methods (SPLADE) approach dense quality on semantics while keeping lexical precision, they become viable as primary retrievers.",
        "example": "A legal-search RAG combines BM25 (sparse lexical) and dense semantic retrieval. Queries with case numbers or specific statutes ('USC §1234') get exact matches via BM25 that dense embeddings miss. Conceptual queries leverage dense. Hybrid retrieval gets the best of both, and end-to-end QA accuracy beats either alone.",
        "pitfalls": [
            "Vocabulary out-of-domain: sparse models trained on general text underperform in specialty domains; train on domain text or use BM25.",
            "Vocab size memory: large vocabularies inflate sparse vector dimensions; learned sparse uses sparsity for efficiency.",
            "Hybrid fusion: combining sparse and dense scores requires careful normalisation; reciprocal rank fusion is a common approach.",
            "Tokenizer alignment: sparse and dense tokenizers may differ; ensure consistent processing."
        ],
        "when_use": "Use for retrieval involving exact-term matching (codes, IDs, technical jargon), long-tail queries, or as the lexical component of hybrid retrieval.",
        "when_avoid": "Avoid as the only retriever in pure-semantic domains where dense embeddings already cover queries well.",
        "related_terms": ["sparse-retrieval", "dense-retrieval", "hybrid-search", "embedding", "splade", "rag"],
        "related_tools": ["qdrant"],
        "faq": [
            {"q": "BM25 same as sparse vector?",
             "a": "BM25 is a specific sparse retrieval scoring function. Sparse vector is the data structure; BM25 is one way to score it. Modern learned sparse (SPLADE) replaces BM25 weighting with neural scoring."},
            {"q": "Sparse or dense for production?",
             "a": "Hybrid is the modern default. Sparse for exact-match precision; dense for semantic recall; combine with rank fusion."},
            {"q": "What's SPLADE?",
             "a": "SParse Lexical AnD Expansion — a learned sparse retriever that uses a transformer to produce sparse activations per token. Strong baseline for hybrid retrieval."},
            {"q": "Are sparse vectors stored efficiently?",
             "a": "Yes — inverted indices store only non-zero entries. Per-doc storage is small relative to dense vectors of equivalent dim."}
        ]
    },
    # 19. binary-quantization-embedding
    {
        "slug": "binary-quantization-embedding",
        "title": "Binary Quantization (Embeddings)",
        "category": "rag-internals",
        "difficulty_tier": "advanced",
        "tldr": "Compressing embeddings to 1 bit per dimension by sign-thresholding, enabling fast Hamming-distance search at the cost of small recall loss.",
        "plain_english": "A 1024-dim float embedding takes 4KB. Binary quantize it — keep just the sign bit per dimension — and it takes 128 bytes (32× smaller). Distance becomes Hamming distance, which CPUs compute very fast. You lose some semantic precision but can usually recover most of it with a rescore step on top candidates. For massive indexes, binary quantization is often the difference between fitting in RAM and not.",
        "how_it_works": "For each embedding dimension, output 1 if value > 0 else 0. Stack the bits into a binary vector. At search time, embed the query, binarise it the same way, compute Hamming distance against every binary doc vector — extremely fast with SIMD. Top candidates can optionally be rescored using full-precision vectors to recover quality. Cohere and several embedding providers offer Matryoshka + binary out of the box.",
        "why_it_matters": "Binary embeddings shrink storage and accelerate search dramatically. For billion-scale retrieval, the difference between full-precision and binary determines whether a system is feasible at all. Combined with rescoring for top candidates, modern binary embeddings recover 95%+ of full-precision quality on most evals.",
        "example": "A search platform indexes 100M Cohere embeddings. Full precision (float32, 1024-dim): 400GB. Binary: 12.5GB — fits entirely in RAM on a single server. Search latency drops 10×. Recall@10 with rescoring: 97% of full-precision baseline. The team replaces a multi-server vector DB cluster with one machine and saves significant infrastructure cost.",
        "pitfalls": [
            "Quality loss without rescoring: pure-binary search loses ~5-10% recall; almost-always rescore top-100 with full precision.",
            "Embedding compatibility: not all embedding models binarise gracefully; Matryoshka-trained ones do best.",
            "Asymmetric storage: queries can stay full-precision while docs are binary; some systems exploit this.",
            "Tooling support: not every vector DB supports binary natively; check before adopting."
        ],
        "when_use": "Use for million-to-billion-scale retrieval where storage or speed dominates. Pair with rescoring for quality preservation.",
        "when_avoid": "Avoid for small indexes where full-precision is fast enough, or for embeddings not trained for binary compatibility.",
        "related_terms": ["matryoshka-embeddings", "embedding", "vector-database", "scalar-quantization", "product-quantization", "rag"],
        "related_tools": ["qdrant"],
        "faq": [
            {"q": "How big a quality drop?",
             "a": "Pure binary: 5-10% recall@k drop typically. With rescoring of top candidates: <2% drop, often within noise."},
            {"q": "Does it work with any embedding?",
             "a": "Best with Matryoshka-trained embeddings (OpenAI text-embedding-3, Cohere v3, Nomic Embed). Older embeddings binarise less well."},
            {"q": "Binary or scalar quantization?",
             "a": "Binary: 1 bit per dim, max compression. Scalar: 8-bit or 4-bit per dim, less compression but better quality. Pick by storage budget."},
            {"q": "Combine with HNSW or IVF?",
             "a": "Yes — binary embeddings + HNSW/IVF stack for both speed and storage savings. Most modern vector DBs support combinations."}
        ]
    },
    # 20. scalar-quantization
    {
        "slug": "scalar-quantization",
        "title": "Scalar Quantization",
        "category": "rag-internals",
        "difficulty_tier": "advanced",
        "tldr": "Compressing vector embeddings by reducing each dimension from 32-bit floats to 8-bit or 4-bit integers, balancing storage and quality.",
        "plain_english": "Float32 embeddings are wasteful — most semantic information sits in the rough magnitudes, not the fine bits. Scalar quantization quantises each dimension to 8 bits (256 levels) or 4 bits (16 levels), shrinking storage 4× or 8×. Quality loss is typically small. Less aggressive than binary (1 bit) but preserves more precision; it's the middle ground between full-precision and binary.",
        "how_it_works": "Compute per-vector or per-dimension min/max from a calibration set. Quantise each value to integer representation: q = round((v - min) / (max - min) × (2^bits - 1)). Store the quantised integers plus the scale and zero-point per vector or per dimension. At search time, dequantise inline (or use specialised SIMD kernels that work directly on quantised values). 8-bit (INT8) is the most common; 4-bit (INT4) for more compression.",
        "why_it_matters": "Scalar quantization is the easiest storage win for vector retrieval. 4× compression with negligible quality loss is often free; 8× compression with small loss is acceptable for most production. Combined with cluster retrieval, it scales billion-vector indexes onto single servers. As of 2026, INT8 is standard; INT4 is increasingly common.",
        "example": "A 100M-vector index in float32 takes 400GB. INT8 quantised: 100GB — fits on commodity hardware. INT4: 50GB. Recall@10 with INT8 rescoring: 99% of float32 baseline; INT4: 96%. The team uses INT8 for primary search and full-precision for re-scoring top-100, effectively no quality loss.",
        "pitfalls": [
            "Calibration set size: too-small calibration sets produce bad min/max; use representative samples.",
            "Per-vector vs per-dimension: per-dimension is more accurate; per-vector is simpler but loses precision.",
            "Tooling fragmentation: quantization formats differ across vector DBs; lock in one.",
            "Aggressive quantization: INT4 needs careful evaluation; some embeddings tolerate it poorly."
        ],
        "when_use": "Use as the default storage format for production vector indexes. INT8 is almost-always-correct; INT4 for max compression on tolerant embeddings.",
        "when_avoid": "Avoid only when your embedding model strongly degrades under quantization (rare for modern models).",
        "related_terms": ["binary-quantization-embedding", "product-quantization", "vector-database", "embedding", "matryoshka-embeddings", "quantization"],
        "related_tools": ["qdrant"],
        "faq": [
            {"q": "INT8 or INT4?",
             "a": "INT8 first — 4× compression, near-zero quality cost. INT4 if storage is tight and your model tolerates it."},
            {"q": "Does it slow search?",
             "a": "Often speeds it up — smaller vectors mean better cache utilisation. Modern SIMD kernels work on quantised values directly."},
            {"q": "How is this different from binary?",
             "a": "Binary is 1 bit per dim (most aggressive). Scalar is 8 or 4 bits per dim (less aggressive, more quality)."},
            {"q": "Does scalar quantization work with HNSW?",
             "a": "Yes — combine compression with graph-based search for max speed and storage gains. Standard production pattern."}
        ]
    },
    # 21. ivf
    {
        "slug": "ivf",
        "title": "IVF",
        "category": "rag-internals",
        "difficulty_tier": "advanced",
        "tldr": "Inverted File index — vector retrieval structure that clusters embeddings into Voronoi cells and probes only the most relevant cells per query.",
        "plain_english": "IVF is the most common approximate-nearest-neighbour structure in vector databases alongside HNSW. Documents are partitioned into K cells via clustering. At query time, the query is matched to its nearest M cells and search proceeds only inside those cells. Trades small recall loss for large speedups. Combines naturally with quantization (IVF+PQ, IVF+SQ) for both storage and speed gains.",
        "how_it_works": "Index time: cluster all vectors into K centroids (k-means). Each vector gets assigned to its nearest centroid; the index becomes K posting lists. Query time: compute query embedding, identify the M closest centroids, search the union of their posting lists with full-precision (or quantised) distance computation. K and M tune the speed/recall trade. FAISS pioneered the production-grade implementation; modern stores (Qdrant, Milvus) ship IVF variants out of the box.",
        "why_it_matters": "IVF is foundational to large-scale retrieval. Without it (or HNSW), billion-scale indexes are impossible to serve at acceptable latency. Knowing how IVF works helps tune speed-vs-recall — a critical decision for any production RAG with serious traffic.",
        "example": "A team's 200M-vector RAG runs in float32: brute-force search takes 1.2s per query. With IVF (K=8192, M=16) + INT8 quantization, latency drops to 18ms with recall@10 of 96%. They add a cross-encoder rerank on top-50 candidates to recover the recall gap.",
        "pitfalls": [
            "Cluster imbalance: as vectors are added, some clusters grow disproportionately; periodic rebalancing helps.",
            "K choice: too few clusters means each is large (slow); too many means many empty clusters (wasted memory). sqrt(N) is a starting heuristic.",
            "M tuning: too low (M=1) often misses relevant clusters; too high defeats the point. Sweep on validation.",
            "Cold start: clustering K centroids needs training data; small initial corpora cluster poorly."
        ],
        "when_use": "Use as the default index for any vector store at >100k vectors where latency matters. Almost-always combine with quantization for storage savings.",
        "when_avoid": "Avoid for small indices (<10k vectors) where brute-force suffices, or when HNSW's higher memory cost is acceptable for its slightly higher recall.",
        "related_terms": ["cluster-retrieval", "hnsw", "vector-database", "scalar-quantization", "product-quantization", "retrieval"],
        "related_tools": ["faiss", "qdrant"],
        "faq": [
            {"q": "IVF or HNSW?",
             "a": "HNSW often slightly higher recall and faster on small-to-mid corpora; IVF more memory-efficient and simpler at scale. Many systems support both."},
            {"q": "What's IVF+PQ?",
             "a": "IVF clustering plus Product Quantization on the vectors within each cluster. Combines speed (cluster pruning) and storage (compression). FAISS's most popular config for billion-scale."},
            {"q": "How long does indexing take?",
             "a": "K-means on hundreds of millions of vectors takes minutes to hours; periodic re-clustering is the main maintenance cost."},
            {"q": "Can I add vectors after indexing?",
             "a": "Yes — assign new vectors to existing centroids. Cluster quality drifts over time; re-cluster periodically for best recall."}
        ]
    },
    # 22. colpali
    {
        "slug": "colpali",
        "title": "ColPali",
        "category": "rag-internals",
        "difficulty_tier": "advanced",
        "tldr": "Vision-language retrieval model that applies ColBERT-style late interaction to document images, indexing pages directly without OCR.",
        "plain_english": "Most document RAG runs OCR first then indexes text. ColPali skips OCR: it embeds each page image as a set of patch vectors using a vision-language model, and matches queries against patch sets via late interaction. The result captures layout, tables, and visual content that OCR-based pipelines lose. Especially valuable for PDFs, slides, and scientific papers where structure carries meaning.",
        "how_it_works": "Take a document page image, run it through PaliGemma (or similar VLM) to produce a grid of patch vectors. Each patch becomes a 'token' in a ColBERT-style index. Encode the query as text tokens. At search time, MaxSim between query tokens and document patches scores documents. Top matches return whole pages. Faysse et al. 2024 introduced ColPali; subsequent work (ColQwen, ColInternVL) ported the idea to other VLM bases.",
        "why_it_matters": "OCR fails on complex layouts, charts, and degraded scans. ColPali handles documents visually, capturing structural information OCR loses. For RAG over annual reports, scientific PDFs, and scanned archives, ColPali consistently outperforms OCR + text retrieval. As VLMs improve, ColPali-style direct-image indexing becomes the default for layout-rich corpora.",
        "example": "A finance team builds RAG over 10 years of annual reports (PDFs with tables, charts, footnotes). OCR-based pipeline misses 30% of table cells. ColPali indexes pages as images; retrieval finds correct pages including ones where tables encode key info. End-to-end QA accuracy on 'find the 2022 revenue from segment X' rises 22 points.",
        "pitfalls": [
            "Storage: per-patch embeddings are heavy; compression and PLAID-style techniques mitigate.",
            "Compute: VLM encoding is much more expensive than text embedding; budget GPU time.",
            "VLM choice: quality varies dramatically across base VLMs; ColQwen and ColPali differ measurably.",
            "Page-level only: doesn't natively handle multi-page entities; chunk by page or apply post-hoc grouping."
        ],
        "when_use": "Use for layout-rich document RAG: financial reports, scientific PDFs, slides, scanned archives, technical manuals where structure matters.",
        "when_avoid": "Avoid for plain-text corpora where OCR-based pipelines work fine and ColPali's compute overhead isn't justified.",
        "related_terms": ["late-interaction", "rag", "ocr-llm", "vision-language-model", "multimodal-embedding", "retrieval"],
        "related_tools": [],
        "faq": [
            {"q": "ColPali or OCR + text retrieval?",
             "a": "ColPali wins on layout-rich docs (charts, tables, scans). OCR + text wins on pure-text-and-cost-sensitive workloads. Often deployed together."},
            {"q": "Does ColPali need fine-tuning?",
             "a": "Out-of-the-box checkpoints work for general queries. Domain fine-tuning helps in specialty corpora (medical scans, legal forms)."},
            {"q": "Storage cost vs text-RAG?",
             "a": "5-30× more storage per page than text retrieval. PLAID-style compression brings it to manageable ranges (2-5×)."},
            {"q": "Best VLM base?",
             "a": "PaliGemma (original ColPali), Qwen2-VL (ColQwen), InternVL (ColInternVL). All competitive; pick by ecosystem fit."}
        ]
    },
    # 23. video-llm
    {
        "slug": "video-llm",
        "title": "Video LLM",
        "category": "models",
        "difficulty_tier": "advanced",
        "tldr": "Multimodal model that ingests video frames (or full video clips) alongside text, enabling reasoning over temporal visual content.",
        "plain_english": "An LLM that watches video. Frames are sampled, encoded into the model's embedding space, and the model can answer questions about what happens, summarise sequences, locate events, or compare clips. Earlier systems chunked video into frames and processed each separately; modern video LLMs (Qwen2.5-VL, Gemini 2.5, GPT-4o video) handle longer clips natively, capturing temporal patterns that frame-by-frame processing misses.",
        "how_it_works": "Sample frames from a video at a fixed rate or via keyframe detection. Encode each frame with a vision tower into patch vectors; add temporal positional encodings. The LLM attends across frame patches and text tokens together. For long videos, hierarchical sampling and compressed memory allow processing minutes-to-hours of content. Modern video LLMs use techniques like 3D rotary embeddings and frame-token compression to keep compute tractable.",
        "why_it_matters": "Video is ubiquitous and underutilised in AI workflows. Video LLMs unlock content moderation at scale, automated highlight generation, surveillance/security analysis, sports analytics, and video search. As models improve, video understanding extends to robotics (instructional videos), education (lecture summarisation), and accessibility (described content for visually impaired users).",
        "example": "A sports platform uses Qwen2.5-VL to auto-generate highlight reels. The model watches each game, identifies key moments (goals, assists, controversies), timestamps them, and produces a textual recap. Manual editing time drops 70%; reels publish faster than competitors.",
        "pitfalls": [
            "Frame sampling rate: too coarse misses fast events; too fine balloons compute. Tune per content type.",
            "Long-video memory: hours of footage exceed context windows; hierarchical chunking and summary memory help.",
            "Action recognition limits: subtle motion or off-screen events can confuse models; combine with audio cues for robustness.",
            "Cost: video encoding is expensive; reserve for high-value workflows or use sampled-frame fallbacks."
        ],
        "when_use": "Use for video understanding tasks: content moderation, highlight generation, video search, surveillance analysis, instructional video processing.",
        "when_avoid": "Avoid for tasks solvable by frame-by-frame image processing alone, or when latency budgets can't absorb video LLM compute.",
        "related_terms": ["vision-language-model", "audio-llm", "multimodal-embedding", "ocr-llm", "embodied-ai", "world-model"],
        "related_tools": [],
        "faq": [
            {"q": "Best open-source video LLM?",
             "a": "Qwen2.5-VL and InternVL are widely used in 2026. Gemini 2.5 and GPT-4o lead on hosted side. Pick by deployment constraint."},
            {"q": "How long videos can these handle?",
             "a": "Modern frontier models: hours with hierarchical sampling. Open models: typically minutes; longer requires custom chunking."},
            {"q": "Does it handle audio?",
             "a": "Some do (audio-LLM hybrids); many video-only models drop audio. Check capabilities for your use case."},
            {"q": "Frame sampling rate to use?",
             "a": "1 fps for content-stable footage; 5-10 fps for action-heavy. Many model defaults sample 2-4 fps as a balance."}
        ]
    },
    # 24. odpo
    {
        "slug": "odpo",
        "title": "ODPO",
        "category": "techniques",
        "difficulty_tier": "advanced",
        "tldr": "Online DPO — variant of Direct Preference Optimization that generates preferences from the current policy at each training step instead of using a fixed dataset.",
        "plain_english": "Standard DPO trains on a fixed dataset of preference pairs. The model improves up to the data's quality ceiling, then plateaus. Online DPO (ODPO) fixes this: at each step, sample two responses from the current policy, score them with a judge or reward model, build a preference pair, train. The data adapts as the model improves, capturing failure modes that static datasets can't anticipate.",
        "how_it_works": "Maintain the current policy and a reference policy (frozen). At each step: sample two completions from the policy; rank them with a judge model or reward model; treat the higher-ranked as 'chosen' and lower as 'rejected'. Apply the standard DPO loss to push the policy toward chosen and away from rejected, with a KL penalty against the reference. Iteration replaces or augments fixed-dataset DPO. Several papers (iterative DPO, online DPO, OAIF) explored variants in 2024-2025.",
        "why_it_matters": "Static preference datasets reflect the policy at the time of collection. As the model improves past that, the dataset stops providing useful signal. Online DPO keeps the data fresh and avoids the plateau. For ongoing alignment work, especially with strong judge models or rule-based verifiers, ODPO often outperforms multi-pass static DPO at similar compute.",
        "example": "A team initially does static DPO on 30k human preferences and plateaus at quality X. They switch to ODPO using a strong judge model, training for another 10k steps with on-policy preferences. Quality improves another 4 points on held-out evals — gains the static dataset couldn't provide.",
        "pitfalls": [
            "Judge quality bottleneck: ODPO inherits judge biases; calibrate or use rule-based verifiers when possible.",
            "Compute cost: each step requires sampling responses from the policy; substantially more expensive than static DPO.",
            "Policy collapse: aggressive ODPO can narrow output distribution; KL penalty and replay buffers help.",
            "Drift from initial alignment: long ODPO runs can shift behaviour in unintended ways; monitor capabilities continuously."
        ],
        "when_use": "Use to push past static DPO plateaus, especially with strong judge models or rule-based reward signals.",
        "when_avoid": "Avoid when judge quality is poor (online amplifies its biases) or when compute budget can't absorb the per-step sampling overhead.",
        "related_terms": ["dpo", "iterative-dpo", "rlaif", "reward-model", "preference-data", "rlhf"],
        "related_tools": ["trl"],
        "faq": [
            {"q": "ODPO or PPO?",
             "a": "ODPO is simpler operationally — one model + one judge, no value function. PPO has stronger theory and may handle some failure modes better. ODPO is a popular default for online preference learning."},
            {"q": "Same as iterative DPO?",
             "a": "Closely related. Iterative DPO retrains DPO on freshly-sampled pairs in batches. ODPO updates per-step. The boundary is fuzzy in practice."},
            {"q": "Does it need a reward model?",
             "a": "Either a judge model (LLM-as-judge) or a reward model. Rule-based verifiers (math correctness, code passing tests) work too."},
            {"q": "How many iterations?",
             "a": "Until quality plateaus on held-out eval. Diminishing returns kick in; track and stop when gains shrink below noise."}
        ]
    },
    # 25. rloo
    {
        "slug": "rloo",
        "title": "RLOO",
        "category": "techniques",
        "difficulty_tier": "advanced",
        "tldr": "REINFORCE Leave-One-Out — RL fine-tuning algorithm that uses leave-one-out baselines from grouped samples, simpler and often as effective as PPO.",
        "plain_english": "PPO is the workhorse of RLHF but complicated: needs a value function, careful clipping, KL targets. RLOO simplifies things: sample K completions per prompt, score them, and use the leave-one-out mean as a baseline for each sample's advantage. No value function. No clipping. The simpler training procedure often matches or beats PPO at lower implementation cost.",
        "how_it_works": "For each prompt, sample K completions from the policy. Score each with a reward model. Each completion's advantage is (its reward) - (mean of the other K-1 rewards). Apply a REINFORCE-style policy gradient update with KL regularisation against a reference policy. Compared to PPO, RLOO drops the value model and the clipping ratio. Cohere and several alignment teams use RLOO as a primary fine-tuning algorithm.",
        "why_it_matters": "PPO's complexity makes RLHF training brittle and expensive. RLOO's simpler structure trains faster, has fewer hyperparameters, and on standard benchmarks matches or beats PPO. For teams without dedicated RL engineering capacity, RLOO is a more practical choice. As GRPO and RLOO become more common, PPO is gradually retiring from production RLHF stacks.",
        "example": "A team trains a chat model with RLOO instead of PPO. K=4 samples per prompt, KL coefficient 0.05. Training is 30% faster than their previous PPO run, hyperparameter search is shorter, and final quality is 1 point higher on internal evals. The team standardises on RLOO for future RLHF training.",
        "pitfalls": [
            "K trade-off: too small (K=2) makes baseline noisy; too large (K=16) is expensive. K=4-8 is typical.",
            "KL coefficient sensitivity: too low and the policy drifts; too high and learning stalls; sweep on validation.",
            "All-equal-reward groups: when all samples score equally, advantages are zero and the gradient vanishes; clip or skip.",
            "Reward model quality: like all RL fine-tuning, RLOO inherits reward-model biases; calibrate."
        ],
        "when_use": "Use for RLHF when you want simpler implementation than PPO, want faster training, or have limited RL engineering capacity.",
        "when_avoid": "Avoid when you have a strong value function and PPO infrastructure already, or for tasks where clipping has empirically shown big benefits.",
        "related_terms": ["ppo", "grpo", "dpo", "rlhf", "preference-data", "reward-model"],
        "related_tools": ["trl"],
        "faq": [
            {"q": "RLOO or GRPO?",
             "a": "Both are simpler-than-PPO algorithms. GRPO uses normalised group advantages with clipping; RLOO uses leave-one-out without clipping. Often comparable; pick by ecosystem support."},
            {"q": "Why no value model?",
             "a": "Group statistics provide variance reduction without learning a separate value function. Saves memory and avoids one source of training instability."},
            {"q": "Need a separate reference model?",
             "a": "Yes — KL penalty requires a frozen reference (typically the SFT model before RL). Standard for any RL fine-tuning."},
            {"q": "Does RLOO scale?",
             "a": "Yes — Cohere uses it for production-scale fine-tuning. Compute scales linearly with K and prompt count."}
        ]
    },
    # 26. rejection-sampling-finetuning
    {
        "slug": "rejection-sampling-finetuning",
        "title": "Rejection Sampling Fine-Tuning",
        "category": "techniques",
        "difficulty_tier": "advanced",
        "tldr": "Iterative method that generates many samples from a model, filters them by quality, and fine-tunes on the survivors — bootstrapping the model toward better outputs.",
        "plain_english": "Take a model, generate K candidate responses per prompt, keep only the ones that pass a quality filter (verifier, judge, rule-based check), fine-tune on the kept set. Repeat. Each iteration the model produces better responses, so each round of filtering keeps higher-quality data, which improves the next iteration. Used heavily in math and code where verifiers are cheap; popularised by STaR and Llama 3's training pipeline.",
        "how_it_works": "Round 1: sample K responses per prompt from the base model. Verify each: math correctness, code tests passing, judge model approval. Keep responses that pass. SFT the base model on the kept (prompt, response) pairs. Round 2: use the fine-tuned model from round 1 as the new sampler, repeat. After N rounds (typically 2-5), the model produces high-quality outputs reliably. Llama 3's post-training used multi-round rejection sampling as a major component.",
        "why_it_matters": "Rejection sampling fine-tuning is a high-leverage technique for boosting model capability without external preference data or expensive RLHF. The verifier provides the supervision; the model bootstraps itself. For domains with cheap verification (math, code, structured outputs), it's often the simplest path to substantial quality gains.",
        "example": "A team building a math model starts with a base. Round 1: sample 8 solutions per problem, keep ones the answer-checker accepts (40% pass rate). SFT on kept solutions. Round 2: same model, now 65% pass rate. SFT again. After 3 rounds, the model passes 82% on its training distribution and 78% on held-out — comparable to much larger frontier models on the same benchmark.",
        "pitfalls": [
            "Verifier hacking: models learn to produce outputs that game the verifier; harden iteratively.",
            "Diversity loss: filtered data drifts toward the verifier-friendly distribution; preserve some hard cases.",
            "Compute cost: K samples per prompt × N rounds × full SFT each round adds up; budget accordingly.",
            "Plateau: returns diminish past 3-5 rounds; combining with RL or DPO captures the rest."
        ],
        "when_use": "Use for tasks with cheap verifiers — math, code, structured output, factual QA with answer keys. Especially valuable when starting with a moderately-capable base.",
        "when_avoid": "Avoid for open-ended creative tasks where no good verifier exists; rejection sampling collapses without quality signal.",
        "related_terms": ["fine-tuning", "best-of-n", "verifier-model", "self-rewarding-llm", "iterative-dpo", "star-method"],
        "related_tools": ["trl"],
        "faq": [
            {"q": "Same as STaR?",
             "a": "STaR (Self-Taught Reasoner) is a specific instance — sample reasoning chains, keep ones with correct final answers, fine-tune. Rejection sampling fine-tuning is the broader pattern."},
            {"q": "How many rounds?",
             "a": "2-5 typically. Returns drop after 3; 4-5 is the sweet spot for many setups. Stop when held-out gains shrink."},
            {"q": "Combine with DPO?",
             "a": "Yes — rejection sampling + DPO is a popular pipeline. Rejection sampling provides high-quality positives; DPO adds preference signal for refinement."},
            {"q": "Does this work without a verifier?",
             "a": "Less well — judge models can substitute but quality bottleneck shifts to the judge. Rule-based verifiers stay best when available."}
        ]
    },
    # 27. self-rewarding-llm
    {
        "slug": "self-rewarding-llm",
        "title": "Self-Rewarding LLM",
        "category": "techniques",
        "difficulty_tier": "advanced",
        "tldr": "Training paradigm where the model generates responses and judges them itself, using the self-generated preferences to fine-tune via DPO or similar.",
        "plain_english": "External reward models or judge models cost effort to maintain. Self-rewarding LLMs cut them out: the same model that produces responses also evaluates them, pairing self-judged 'better' and 'worse' responses for DPO training. Quality improves through iteration. Meta's self-rewarding language models paper showed the approach works for several rounds before saturation, suggesting it could scale alignment without external labels.",
        "how_it_works": "Use the current model to generate K responses per prompt. Use the same model with an evaluation prompt to judge those responses, producing rankings. Construct preference pairs from the rankings. Run DPO on the pairs. The updated model is then both better at generating and at judging. Repeat. Variants vary the eval prompt, mix human and self labels, or use external rule-based verifiers as a calibration signal.",
        "why_it_matters": "If self-rewarding works at scale, it's a path to ongoing alignment without expensive human labelling. The risk is feedback-loop pathologies: a model with biases reinforces them when it judges itself. Empirically, self-rewarding produces 2-3 rounds of meaningful improvement before drift; combining with external calibration extends the useful range.",
        "example": "A team starts with an instruction-tuned model. Round 1: model generates and judges; DPO on results lifts a benchmark by 4 points. Round 2: lift by 2 more points. Round 3: lift by 0.5; round 4: regression. They stop at round 3 and combine with human-calibrated DPO for final polish.",
        "pitfalls": [
            "Bias amplification: if the model has subtle biases (length preference, style preference), self-rewarding amplifies them.",
            "Saturation: gains diminish quickly; budget for a small number of rounds.",
            "Adversarial drift: the model can learn to write outputs it judges favourably, decoupling from real quality.",
            "Calibration loss: monitor against a held-out human-labelled set to detect drift early."
        ],
        "when_use": "Use as a complement to human-labelled or rule-verified DPO for cheap additional rounds of alignment, especially in narrow domains.",
        "when_avoid": "Avoid as the only training signal — feedback-loop risks compound. Combine with external calibration for production-grade systems.",
        "related_terms": ["dpo", "rlaif", "iterative-dpo", "rejection-sampling-finetuning", "preference-data", "constitutional-ai"],
        "related_tools": ["trl"],
        "faq": [
            {"q": "Does self-rewarding really work?",
             "a": "For 2-3 rounds in narrow domains, yes — published results consistently show improvement. Beyond that, drift dominates."},
            {"q": "What evaluation prompt to use?",
             "a": "A specific rubric (helpful, accurate, complete) outperforms vague ones (better/worse). Calibrate against human labels."},
            {"q": "Is this safe for chat models?",
             "a": "Risky — self-rewarding can entrench biases. Always re-eval on broad capability and safety benchmarks after each round."},
            {"q": "Same as RLAIF?",
             "a": "Closely related. RLAIF typically uses a different (stronger) AI as judge. Self-rewarding uses the model judging itself. Self-rewarding is a special case of RLAIF."}
        ]
    },
    # 28. iterative-dpo
    {
        "slug": "iterative-dpo",
        "title": "Iterative DPO",
        "category": "techniques",
        "difficulty_tier": "advanced",
        "tldr": "Multi-round DPO pipeline that generates new preferences from each round's policy, refining the model iteratively beyond what static DPO achieves.",
        "plain_english": "Static DPO trains once on a fixed preference dataset. Iterative DPO repeats: after one round of DPO, sample new responses from the trained policy, get new preferences, train again. Each round lets the model encounter and improve on its current failure modes — failure modes static datasets can't capture. Common in modern post-training pipelines for chat models.",
        "how_it_works": "Round 1: standard DPO on initial preference data. Round 2: sample N responses per prompt from round-1 model. Score with judge or reward model to build new preference pairs. Apply DPO. Round 3: use round-2 model as sampler, repeat. Gain typically tapers after 2-4 rounds. Often combined with rejection sampling, online DPO, or RLHF for compounding improvements. Llama 3 and similar production pipelines use iterative DPO as a major post-training component.",
        "why_it_matters": "Static DPO leaves quality on the table because the preference dataset reflects an older version of the model. Iterative DPO captures fresh failure modes and pushes past static plateaus. For production-grade chat models, multi-round DPO is the standard rather than exception.",
        "example": "A team's first DPO round on 50k preferences improves their model by 6 points on a benchmark. Second round, with 30k fresh preferences from the round-1 policy: 3 more points. Third: 1.5 points. Fourth: 0.3 (within noise). They stop at round 3 — total gain 10.5 points from iteration vs. 6 from static.",
        "pitfalls": [
            "Drift compounding: each round shifts the policy; over many rounds, base capabilities can erode.",
            "Cost stacking: each round needs sampling + scoring + training; multi-round budget is significant.",
            "Plateau: gains diminish; stopping at the right round is a tuning decision.",
            "Reward-model freshness: a reward model trained on round-0 outputs may mis-score round-3 outputs; refresh judges along with policy."
        ],
        "when_use": "Use when static DPO has plateaued and additional alignment compute is justified, especially for production chat or instruction-tuned models.",
        "when_avoid": "Avoid for narrow tasks where static DPO already meets quality, or when compute budget is tight.",
        "related_terms": ["dpo", "odpo", "rlhf", "rejection-sampling-finetuning", "preference-data", "self-rewarding-llm"],
        "related_tools": ["trl"],
        "faq": [
            {"q": "Iterative DPO or ODPO?",
             "a": "ODPO updates per step; iterative DPO updates in batches per round. Iterative is more operationally manageable; ODPO is more sample-efficient."},
            {"q": "How many rounds?",
             "a": "2-4 typically. Saturate when gains drop below noise on held-out eval. Llama 3 used 6 rounds at frontier scale."},
            {"q": "Need fresh reward model each round?",
             "a": "Helps a lot — reward models trained on stale outputs mis-score new ones. Frontier teams refresh reward data periodically."},
            {"q": "Combine with rejection sampling?",
             "a": "Yes — rejection sampling provides high-quality positives, DPO uses them for preference learning. Many production pipelines combine the two."}
        ]
    },
    # 29. star-method
    {
        "slug": "star-method",
        "title": "STaR",
        "category": "techniques",
        "difficulty_tier": "advanced",
        "tldr": "Self-Taught Reasoner — fine-tuning method that generates chain-of-thought rationales, keeps ones leading to correct answers, and trains on those rationales.",
        "plain_english": "STaR teaches a model to reason by having it teach itself. The model is asked to solve problems with chain-of-thought. Solutions with correct final answers are kept; their rationales become training data. The fine-tuned model produces better rationales next round. STaR was a key step in showing self-generated reasoning could substantially improve LLM performance on math and reasoning benchmarks.",
        "how_it_works": "Initial round: prompt the base model to solve problems with CoT. For each problem, check if the final answer is correct. Keep (problem, rationale, answer) triples where the answer is correct. SFT on these. The fine-tuned model is better at producing correct rationales; iterate. Variants include a 'rationalisation' step where wrong answers are paired with hints to elicit correct rationales, expanding training coverage.",
        "why_it_matters": "STaR (Zelikman et al. 2022) was a foundational paper for self-improvement in reasoning models. The approach demonstrated that large-scale rationale generation from the model itself can produce reasoning capabilities approaching frontier models, and inspired subsequent work like rejection-sampling fine-tuning, V-STaR, and reasoning-distillation pipelines.",
        "example": "A team applies STaR to a 7B math model. Round 1: 35% of problems are solved correctly with CoT. Train on those rationales. Round 2: 52%. Round 3: 65%. Round 4: 73%. After 4 rounds, the 7B model approaches the accuracy of a 70B base on the same benchmark, at a fraction of inference cost.",
        "pitfalls": [
            "Hard-problem coverage: problems that always fail produce no training data; rationalisation prompts help.",
            "Rationale quality: filtering on final-answer correctness keeps rationales that get the right answer for wrong reasons; combine with process supervision when possible.",
            "Saturation: returns diminish past 3-5 rounds.",
            "Verifier dependency: works only when answer correctness is checkable; pure-CoT tasks need different strategies."
        ],
        "when_use": "Use to bootstrap reasoning capability in math, code, and structured-answer tasks where final-answer verification is cheap.",
        "when_avoid": "Avoid for open-ended or unverifiable tasks where 'correct' is subjective.",
        "related_terms": ["rejection-sampling-finetuning", "fine-tuning", "self-rewarding-llm", "reasoning-model", "reasoning-distillation", "chain-of-thought"],
        "related_tools": ["trl"],
        "faq": [
            {"q": "STaR vs rejection sampling fine-tuning?",
             "a": "STaR specifically targets rationale generation. Rejection sampling fine-tuning is the broader pattern. STaR is a specific instance."},
            {"q": "What's V-STaR?",
             "a": "Variant that adds a verifier model trained on rationale quality, used to filter beyond just correctness. Improves over vanilla STaR on hard problems."},
            {"q": "Does STaR scale to non-math?",
             "a": "Yes — works for any task with verifiable answers. Code, factual QA, classification. Less effective for creative writing."},
            {"q": "How big a jump?",
             "a": "Several papers report 10-30 point gains on math benchmarks for moderately-capable bases. Diminishing returns at frontier model scale."}
        ]
    },
    # 30. spin
    {
        "slug": "spin",
        "title": "SPIN",
        "category": "techniques",
        "difficulty_tier": "advanced",
        "tldr": "Self-Play Fine-Tuning — alignment method where the model competes against its previous version, using DPO to push toward outputs the new model prefers over the old.",
        "plain_english": "SPIN treats fine-tuning as self-play: the current model is the 'opponent' and the next-iteration model is being trained to beat it. Specifically, the new model is trained via DPO with synthetic data generated by the old model, learning to prefer human-style ground-truth responses over the old model's outputs. Each iteration improves; the gap with the old model widens until convergence.",
        "how_it_works": "Round 0: SFT on a labelled dataset to produce M_0. For each prompt: keep the labelled response as 'chosen'; sample an alternative from M_0 as 'rejected'. Train via DPO on these pairs to produce M_1. Now M_1 is better than M_0 on the labelled distribution. Round 1: same process with M_1 as the opponent, train M_2. Iterate. Chen et al. 2024 introduced SPIN; it leverages existing labelled data without requiring fresh human preference annotation.",
        "why_it_matters": "Most alignment methods assume preference data. SPIN works with just supervised labelled data — much more abundant. It demonstrated that meaningful alignment improvements are possible without explicit preference collection, opening cheaper paths for fine-tuning. For teams with labelled data but no preference budget, SPIN is a practical alternative to RLHF or DPO.",
        "example": "A team has 100k labelled (instruction, response) pairs from human writers. Standard SFT gives a baseline. They run SPIN for 4 iterations: each round trains on (label, M_prev sample) DPO pairs. Final model scores 6 points higher than the SFT baseline on a held-out instruction-following eval, without any new preference data.",
        "pitfalls": [
            "Gaming gold labels: model learns to mimic surface features of labels rather than capturing intent; vary samples to avoid mode collapse.",
            "Labelled-data quality dependence: SPIN amplifies existing label quality; bad labels produce a bad model.",
            "Saturation: gains plateau after 3-5 iterations; further iteration over-fits to label style.",
            "Compute: each iteration involves sampling + DPO; multi-round budget is meaningful."
        ],
        "when_use": "Use when you have substantial labelled SFT data but no preference data, and want to push beyond what SFT alone provides.",
        "when_avoid": "Avoid when labels are sparse or noisy (SPIN amplifies noise) or when preference data is available (DPO with that data is usually stronger).",
        "related_terms": ["dpo", "self-rewarding-llm", "rejection-sampling-finetuning", "iterative-dpo", "fine-tuning", "preference-data"],
        "related_tools": ["trl"],
        "faq": [
            {"q": "SPIN or RLHF?",
             "a": "SPIN works without preference data; RLHF needs it. If you have preferences, RLHF or DPO usually wins; if you only have SFT labels, SPIN is the path."},
            {"q": "How many iterations?",
             "a": "3-5 typically. Beyond that, gains shrink and overfitting risk grows."},
            {"q": "Combine with DPO on real preferences?",
             "a": "Yes — SPIN as a warmup, then DPO with real preferences. Common production pattern."},
            {"q": "Does SPIN need a separate judge?",
             "a": "No — labels themselves serve as the gold signal. Saves a major piece of infrastructure compared to RLHF."}
        ]
    },
    # 31. retnet
    {
        "slug": "retnet",
        "title": "RetNet",
        "category": "models",
        "difficulty_tier": "advanced",
        "tldr": "Retentive Network — transformer alternative architecture that combines parallel training with recurrent inference for linear-time sequence processing.",
        "plain_english": "RetNet is one of several efficient sequence models proposed as transformer alternatives. Like Mamba and RWKV, it offers linear-time inference (vs. transformers' quadratic attention) but trains with parallel formulations that exploit GPU hardware. It does this by replacing softmax attention with a 'retention' mechanism that has both parallel and recurrent forms — train one way, infer another. Microsoft Research introduced it in 2023; it's a research-grade architecture with growing implementations.",
        "how_it_works": "Retention replaces attention. Instead of QK^T softmax, RetNet uses a positional decay matrix multiplied with QK^T, with no softmax — a pseudo-linear operation. Parallel form: matrix multiplication for training. Recurrent form: state update for autoregressive inference. Chunked recurrent form: blockwise computation balancing parallelism and memory. The decay structure provides positional information, replacing rotary embeddings. Multiple heads with different decay rates capture different temporal scales.",
        "why_it_matters": "RetNet was one of the early demonstrations that linear-attention-style architectures could match transformers on language modelling. It influenced subsequent models (Mamba, RWKV-7) and contributed to the broader move toward subquadratic alternatives. While not as widely deployed as transformers, RetNet is part of the architectural toolkit; understanding it helps interpret the landscape of efficient models.",
        "example": "A research team benchmarks RetNet 2.7B against a transformer of similar size. Training throughput is comparable. At inference on long sequences, RetNet's per-token cost stays constant while the transformer's grows quadratically. By 16K context, RetNet is 5× faster. They use it for a long-document analysis pipeline where transformer latency was prohibitive.",
        "pitfalls": [
            "Quality on retrieval-heavy tasks: RetNet, like other linear-attention models, can lag transformers on exact in-context retrieval.",
            "Implementation maturity: fewer optimised CUDA kernels than transformers; performance per parameter is less polished.",
            "Tokenizer compatibility: like all alternative architectures, training data and tokenizer choices affect quality more than the architecture alone.",
            "Limited fine-tuning ecosystem: LoRA, quantization, and serving stacks for RetNet lag transformer support."
        ],
        "when_use": "Use for long-context inference workloads where transformer cost is prohibitive and ecosystem support exists for the specific RetNet variant.",
        "when_avoid": "Avoid for general production deployment where transformer-based models with mature tooling meet quality and cost requirements.",
        "related_terms": ["state-space-model", "mamba", "rwkv", "linear-attention", "transformer", "context-window"],
        "related_tools": [],
        "faq": [
            {"q": "RetNet vs Mamba?",
             "a": "Both are subquadratic transformer alternatives. Mamba uses selective state-space; RetNet uses retention. Mamba has more deployed implementations; RetNet has solid research foundations."},
            {"q": "Why both parallel and recurrent forms?",
             "a": "Parallel form trains efficiently on GPUs. Recurrent form serves efficiently in autoregressive inference. Same model, different computation modes for different phases."},
            {"q": "Is RetNet in production anywhere?",
             "a": "Limited deployment. It's mostly a research milestone; Mamba-based and transformer-hybrid models dominate production deployments of efficient architectures."},
            {"q": "Does it support long context?",
             "a": "Yes — that's the main motivation. Constant per-token inference cost makes long contexts much more practical than with transformers."}
        ]
    },
    # 32. griffin
    {
        "slug": "griffin",
        "title": "Griffin",
        "category": "models",
        "difficulty_tier": "advanced",
        "tldr": "Hybrid sequence architecture combining recurrent linear attention layers with sliding-window attention layers, used by Google in RecurrentGemma.",
        "plain_english": "Pure linear-attention models lose some quality vs. softmax attention. Pure transformers cost too much on long contexts. Griffin combines them: most layers use efficient recurrent linear attention; selected layers use sliding-window softmax attention. The hybrid retains transformer quality on retrieval-style tasks while inheriting linear-attention efficiency on long contexts. RecurrentGemma is the open-weights instantiation.",
        "how_it_works": "Griffin layers come in two types. Recurrent layers use a 'real-gated linear recurrent unit' (RG-LRU) — fast linear-time forward pass with input-dependent gating. Local attention layers use sliding-window softmax attention with small windows (e.g. 1024 tokens). The architecture stacks blocks alternating between these layer types, with empirical ratios tuned for the right efficiency-quality balance. Google's Griffin paper (De et al. 2024) showed it matches or beats transformers at small-to-medium scale.",
        "why_it_matters": "Hybrid architectures are increasingly favoured over either pure-transformer or pure-linear designs. Griffin demonstrated a clean recipe for combining the two and influenced subsequent hybrids (Jamba, Zamba, Samba). For practitioners building or fine-tuning models, hybrid architectures are part of the design space — knowing Griffin helps reason about trade-offs.",
        "example": "Google released RecurrentGemma 2B based on Griffin. Compared to Gemma 2B (transformer), RecurrentGemma matches quality on standard benchmarks while running 2× faster on long contexts (16K tokens). The team chose RecurrentGemma for an on-device deployment where long-context efficiency mattered more than peak quality.",
        "pitfalls": [
            "Layer ratio tuning: too many recurrent layers loses retrieval quality; too few loses efficiency benefits.",
            "Implementation complexity: hybrid models require kernels for both layer types; not all inference servers handle them.",
            "Smaller ecosystem than pure transformers: tooling, fine-tuning recipes, and serving stacks lag.",
            "Quality at frontier scale: most published Griffin results are at sub-10B scale; behaviour at frontier sizes less proven."
        ],
        "when_use": "Use for long-context efficiency workloads where you need transformer-quality retrieval but at lower per-token cost. Especially valuable for on-device or mobile deployments.",
        "when_avoid": "Avoid for general production where transformers' larger ecosystem outweighs efficiency benefits.",
        "related_terms": ["mamba", "state-space-model", "linear-attention", "sliding-window-attention", "recurrent-memory-transformer", "transformer"],
        "related_tools": [],
        "faq": [
            {"q": "RecurrentGemma is Griffin?",
             "a": "Yes — RecurrentGemma is Google's open-weights model implementing the Griffin architecture. Available in 2B and 9B sizes."},
            {"q": "Griffin vs Mamba?",
             "a": "Both efficient sequence models. Griffin is hybrid (linear + sliding attention); Mamba is pure SSM. Hybrids tend to retain more retrieval ability; pure SSMs often have stronger throughput at extreme lengths."},
            {"q": "What's RG-LRU?",
             "a": "Real-Gated Linear Recurrent Unit — Griffin's recurrent layer primitive. Linear-time recurrent state with input-dependent gating, similar in spirit to selective SSMs."},
            {"q": "Is Griffin good for chat?",
             "a": "Yes — RecurrentGemma chat fine-tunes work well on standard chat workloads. Long-context efficiency is the differentiator."}
        ]
    },
    # 33. hyena
    {
        "slug": "hyena",
        "title": "Hyena",
        "category": "models",
        "difficulty_tier": "advanced",
        "tldr": "Subquadratic sequence operator built from interleaved long convolutions and gating, offering attention-like quality at linear time complexity.",
        "plain_english": "Hyena replaces self-attention with a stack of long-convolutional layers parameterised implicitly via a small neural network. The convolutions can have arbitrarily long receptive fields (the whole sequence) but compute in O(n log n) via FFT. Combined with input-dependent gating, Hyena layers approximate attention's expressiveness without quadratic cost. It's mostly a research architecture; Stanford and partners showed competitive language modelling results at scale.",
        "how_it_works": "A Hyena layer interleaves: implicit long convolutions (parameterised by a small MLP that produces convolution kernels on the fly), input-dependent gating (multiplicative interaction between input and convolution output), and elementwise nonlinearities. FFT computes convolutions in O(n log n). Stacking multiple Hyena layers builds depth. The architecture has roots in Hyena Hierarchy (Poli et al. 2023) and continues evolving in subsequent papers.",
        "why_it_matters": "Hyena is part of the broader exploration of attention-free architectures. Its specific contribution is showing that long convolutions with implicit parameterisation can match attention quality at much better scaling. While not widely deployed in production, Hyena influences hybrid designs and demonstrates feasibility of attention alternatives. For researchers, it's part of the architectural search space; for practitioners, awareness helps interpret evolving model designs.",
        "example": "A research group benchmarks Hyena 1.3B against a transformer of similar parameters on language modelling. Hyena matches perplexity on standard datasets and shows better long-context scaling (8K, 16K, 64K tokens) where transformers slow significantly. Production adoption is limited; the work informs subsequent hybrid designs.",
        "pitfalls": [
            "Throughput vs theory: in practice, FFT operations have overhead that small-context transformers beat; advantage only kicks in at long contexts.",
            "Limited ecosystem: very few production frameworks support Hyena; tooling and fine-tuning recipes lag.",
            "Implicit conv parameterisation: small neural networks generating large kernels can be brittle to train.",
            "Quality on retrieval: like other attention alternatives, exact in-context retrieval can lag softmax attention."
        ],
        "when_use": "Use the framing in research, in interpreting architectural papers, or when exploring transformer alternatives in long-context scenarios.",
        "when_avoid": "Avoid for production deployment in 2026 — ecosystem support is limited compared to transformers and SSMs.",
        "related_terms": ["state-space-model", "mamba", "linear-attention", "transformer", "retnet", "context-window"],
        "related_tools": [],
        "faq": [
            {"q": "Is Hyena in any production model?",
             "a": "Limited. StripedHyena (Together AI) is one production-scale instance. Most usage is research and architectural experiments."},
            {"q": "Hyena vs Mamba?",
             "a": "Both attention-free. Hyena uses long convolutions; Mamba uses selective state-space. Different mechanisms; both achieve subquadratic complexity."},
            {"q": "What's the receptive field?",
             "a": "Effectively unbounded — the implicit convolution can attend to any prior position. Practical limits come from training context length."},
            {"q": "Why hasn't Hyena taken over?",
             "a": "Implementation maturity, kernel efficiency, and ecosystem investment all favour transformers and SSMs. Hyena's wins are narrower than initially hoped."}
        ]
    },
    # 34. recurrent-memory-transformer
    {
        "slug": "recurrent-memory-transformer",
        "title": "Recurrent Memory Transformer",
        "category": "models",
        "difficulty_tier": "advanced",
        "tldr": "Architecture extending transformers with persistent memory tokens that pass between segments, enabling effectively unbounded context via recurrence.",
        "plain_english": "Standard transformers have a fixed context window. Recurrent Memory Transformer (RMT) adds dedicated memory tokens at the start and end of each segment. After processing a segment, the output memory tokens become the input memory for the next segment, carrying compressed information forward indefinitely. Effectively unbounded context, with the trade-off that the memory must compress whatever was relevant from earlier segments.",
        "how_it_works": "Add M dedicated memory token positions to each input segment. The first segment runs normally; output memory tokens at the end. For segment 2, prepend those output memory tokens as input memory; process; output new memory; repeat. Train end-to-end with backpropagation through time across multiple segments. Bulatov et al. 2022 introduced RMT; it has inspired similar memory-augmented architectures and overlaps with research on context compression.",
        "why_it_matters": "RMT and related memory-augmented transformers offer one path to long-context capabilities without the quadratic cost of pure long attention. They trade exact in-context recall for compressed long-term memory. For some workloads (long conversations, document streams) the compression is acceptable; for others (exact retrieval) it loses too much. As of 2026, RMT-style designs are research-heavy and not widely deployed in production.",
        "example": "A research team trains an RMT-augmented 1B model on a long-document QA task with 100k-token documents. The model processes documents in 2k-token segments, passing 32 memory tokens between segments. End-to-end accuracy matches a transformer with 8k context, and exceeds it for questions requiring information from distant segments — at much lower memory cost than scaling context to 100k.",
        "pitfalls": [
            "Compression loss: memory tokens can't capture everything; exact recall of distant content is lossy.",
            "Training complexity: backprop through multiple segments uses more memory than single-segment training.",
            "Inference state management: serving requires persisting memory across segments; not all inference stacks support this naturally.",
            "Limited ecosystem: tooling lags; fine-tuning and quantization recipes are sparse."
        ],
        "when_use": "Use the framing in research on long-context models, when designing systems that need streaming long-document processing, or in memory-augmented agent designs.",
        "when_avoid": "Avoid for production where simpler approaches (RAG, longer base context) meet requirements with more mature tooling.",
        "related_terms": ["transformer", "context-window", "long-context-benchmark", "memory-augmented-agent", "agent-memory", "linear-attention"],
        "related_tools": [],
        "faq": [
            {"q": "RMT vs RAG for long context?",
             "a": "RAG retrieves relevant chunks per query (no compression but requires retrieval). RMT compresses everything into memory tokens (no retrieval but loses fidelity). Different trade-offs; pick by access pattern."},
            {"q": "Is this in any production model?",
             "a": "Limited. Some research-grade implementations exist; production long-context typically uses other approaches (long native context, RAG, sparse attention)."},
            {"q": "How big should the memory be?",
             "a": "Task-dependent. 16-128 memory tokens is typical in published work. More memory means more capacity but more compute."},
            {"q": "Does this stack with linear attention?",
             "a": "Yes — RMT's memory mechanism is orthogonal to attention type. Combining linear attention with memory tokens is one path to very-long-context models."}
        ]
    },
    # 35. kv-cache-compression
    {
        "slug": "kv-cache-compression",
        "title": "KV Cache Compression",
        "category": "infra",
        "difficulty_tier": "advanced",
        "tldr": "Inference techniques that reduce KV cache size — eviction, quantization, low-rank projection — to fit longer contexts and more concurrent users in GPU memory.",
        "plain_english": "Each token in flight consumes KV cache memory — typically the dominant memory cost during long-context inference. KV cache compression reduces this without changing the model. Methods include quantizing cached values to lower precision, evicting less-important tokens, projecting to lower-dimensional approximations, or merging similar tokens. The result: more concurrent users, longer contexts, lower per-request memory cost.",
        "how_it_works": "Several techniques. (1) Quantization: store K and V as INT8 or INT4 with per-token scales (similar to weight quantization but applied to activations). (2) Token eviction: drop or merge tokens deemed less important by attention-score signals (StreamingLLM, H2O). (3) Low-rank projection: approximate K and V matrices with low-rank decomposition. (4) Compressed memory: replace some prefix tokens with summary tokens. Modern serving stacks (vLLM, SGLang) implement combinations.",
        "why_it_matters": "Long-context inference is gated by KV cache memory. Compression directly translates to more users per GPU, longer contexts at the same cost, or smaller hardware budgets. As context windows grow toward 1M+ tokens, KV cache compression becomes essential — naive caching at million-token contexts is infeasible on any current hardware.",
        "example": "A team serves 70B Llama with 128K context. KV cache at full precision: 64GB per request, fits 1 user per H100. With INT4 KV cache quantization plus H2O eviction (keeping 50% of tokens): 8GB per request, fits 8 concurrent users. Per-request cost drops 8×; quality on long-context evals stays within 1 point of full-precision baseline.",
        "pitfalls": [
            "Quality degradation: aggressive compression hurts long-context retrieval; calibrate per workload.",
            "Eviction policy choice: different policies (LRU, attention-score-based) suit different access patterns.",
            "Implementation complexity: production-grade KV compression requires careful integration with attention kernels.",
            "Streaming break: some compression methods break sliding-window or attention-sink patterns; verify compatibility."
        ],
        "when_use": "Use for any long-context production serving where memory or concurrency is the bottleneck. Standard in modern inference stacks for >32K contexts.",
        "when_avoid": "Avoid for tasks requiring perfect long-range fidelity (e.g. exact citation retrieval over very long documents) where compression loses critical info.",
        "related_terms": ["kv-cache", "kv-cache-quantization", "attention-offloading", "inference-server", "context-window", "long-context-benchmark"],
        "related_tools": ["vllm"],
        "faq": [
            {"q": "Quantization or eviction?",
             "a": "Quantization is lossless-ish (small quality drop, fixed compression). Eviction is task-dependent (could be lossless or lossy). Often combined."},
            {"q": "What's H2O?",
             "a": "Heavy-Hitter Oracle — KV cache eviction policy that keeps tokens with high attention scores from earlier queries. Empirically effective at preserving long-context accuracy."},
            {"q": "Does this work with paged attention?",
             "a": "Yes — KV compression and PagedAttention are orthogonal. Most modern serving stacks combine both."},
            {"q": "Compression for context vs throughput?",
             "a": "Both — same techniques. Smaller per-request KV cache means more concurrent requests and longer per-request contexts."}
        ]
    },
    # 36. kv-cache-quantization
    {
        "slug": "kv-cache-quantization",
        "title": "KV Cache Quantization",
        "category": "infra",
        "difficulty_tier": "advanced",
        "tldr": "Storing keys and values in attention's KV cache as INT8 or INT4 instead of FP16, cutting cache memory 2-4× with small quality cost.",
        "plain_english": "The KV cache holds attention keys and values for every token in flight. At FP16, it's the dominant memory cost on long contexts. KV cache quantization stores these as INT8 (4× compression) or INT4 (8× compression) using per-token scales. Inference math runs in higher precision after dequantizing. Quality drop is typically small; memory savings are substantial. Modern serving stacks (vLLM, TGI, SGLang) implement KV quantization as a config flag.",
        "how_it_works": "After each forward pass, compute per-token K and V activations. Compute a scale per-token (or per-head per-token) from the activation range. Quantize to INT8 or INT4 storing the compressed integers plus the scale. At later attention steps, dequantize on the fly to FP16 for arithmetic. The dequantization overhead is small relative to memory bandwidth savings; net effect is faster end-to-end. Variants store K and V at different precisions (K is more sensitive than V in some setups).",
        "why_it_matters": "KV cache quantization is one of the cheapest, most-impactful inference optimisations for long-context serving. 4× memory savings translate directly to 4× longer contexts or 4× more concurrent users at the same memory budget. Quality cost is typically <1 point on standard benchmarks. As of 2026, KV quantization is standard in production serving stacks.",
        "example": "A team serves Llama 3 70B with 32K context. FP16 KV cache: 32GB per request. INT8 KV: 8GB. INT4 KV: 4GB. They deploy INT8 (safer quality) and double their concurrent-user capacity per GPU. Quality on long-context QA drops 0.4 points — within noise.",
        "pitfalls": [
            "INT4 vs INT8: INT4 doubles savings but quality cost is more variable; benchmark on your eval.",
            "Per-head vs per-token: per-head scales preserve quality better at slight overhead; per-token is simpler.",
            "Outlier sensitivity: K activations sometimes have outliers that quantize poorly; per-channel scaling helps.",
            "Compatibility with prefix caching: some prefix-caching implementations require fixed precision; verify before adopting."
        ],
        "when_use": "Use as default for long-context (>4K) production serving. Almost always a free win for INT8; worth careful eval for INT4.",
        "when_avoid": "Avoid for short-context inference where KV cache size isn't a bottleneck, or for quality-sensitive workloads where any drop is unacceptable.",
        "related_terms": ["kv-cache", "kv-cache-compression", "scalar-quantization", "inference-server", "fp8", "context-window"],
        "related_tools": ["vllm"],
        "faq": [
            {"q": "INT8 or INT4 KV?",
             "a": "INT8 is the safe default — minimal quality cost. INT4 is more aggressive; benchmark before adopting in production."},
            {"q": "Does this slow attention?",
             "a": "Slightly per-op (dequantize) but speeds up overall (less memory bandwidth). Net effect is usually faster."},
            {"q": "Can I quantize K and V differently?",
             "a": "Yes — some setups quantize K at INT4 and V at INT8 or vice versa. K is often more sensitive; preserve V at higher precision."},
            {"q": "Combine with paged attention?",
             "a": "Yes — vLLM supports both together. Standard production configuration."}
        ]
    },
    # 37. attention-offloading
    {
        "slug": "attention-offloading",
        "title": "Attention Offloading",
        "category": "infra",
        "difficulty_tier": "advanced",
        "tldr": "Moving parts of attention computation or KV cache to slower memory tiers (CPU RAM, NVMe) to fit larger models and longer contexts on limited GPU memory.",
        "plain_english": "When models or KV caches don't fit on GPU, attention offloading stores some of them on slower memory — CPU RAM, NVMe SSDs — and pages data in/out as needed. Performance suffers (CPU and disk are slower than GPU memory), but otherwise-impossible workloads become feasible. Useful for serving very large models on smaller hardware or running million-token contexts that exceed GPU memory.",
        "how_it_works": "Several patterns. (1) Layer offloading: keep some layers' weights on CPU; move to GPU when computing. (2) KV cache offloading: store cache for non-active sequences on CPU/NVMe; page in when needed. (3) Attention block offloading: compute attention in chunks, swapping data between GPU and CPU. Modern frameworks (DeepSpeed-Inference, vLLM with PagedAttention extensions, Hugging Face Accelerate) implement variations. Trade-offs depend on PCIe bandwidth, NVMe speed, and computation/communication overlap.",
        "why_it_matters": "Attention offloading lets you run larger models or longer contexts than GPU memory alone would permit. For research or low-volume deployments where peak hardware isn't available, it makes work possible. The cost is significant latency hits — typically 2-10× slower than fully-resident inference — so production trade-offs matter.",
        "example": "A small team runs Llama 3.1 405B for occasional research queries on a single 8×A100 cluster. Without offloading, the model doesn't fit in 640GB VRAM. With CPU offloading via DeepSpeed-Inference, they run inference at ~5 tokens/sec — slow but viable. Useful for offline batch tasks; not for interactive chat.",
        "pitfalls": [
            "Latency: PCIe-limited transfers are slow; budget significant per-token overhead.",
            "Bandwidth bottleneck: poor utilization without computation/communication overlap; modern frameworks help.",
            "Complexity: offloading config has many knobs; profile carefully.",
            "Power: CPU + GPU together draw more power; cooling may matter at scale."
        ],
        "when_use": "Use for offline batch processing or low-throughput interactive use of larger-than-GPU-memory models, especially for research and exploratory work.",
        "when_avoid": "Avoid for high-throughput production serving where latency matters. Smaller fully-resident models are usually a better deployment.",
        "related_terms": ["kv-cache-compression", "kv-cache-quantization", "inference-server", "fsdp", "deepspeed-zero", "cpu-offloading"],
        "related_tools": ["vllm", "deepspeed"],
        "faq": [
            {"q": "How slow is offloading?",
             "a": "Typically 2-10× slower than fully-GPU inference, depending on model size and PCIe topology. Profile your specific setup."},
            {"q": "Layer or KV offloading?",
             "a": "Layer offloading helps when weights don't fit. KV offloading helps when context is too long for VRAM. Often combined."},
            {"q": "NVMe offloading viable?",
             "a": "Yes for very large models on small hardware. PCIe 4.0/5.0 NVMe SSDs are fast enough for offline workloads. Latency is significant."},
            {"q": "Production-grade?",
             "a": "Borderline. Most production systems prefer rightsized hardware to offloading. Some specialty workloads (occasional access to giant models) make it economic."}
        ]
    },
    # 38. flash-decoding
    {
        "slug": "flash-decoding",
        "title": "Flash Decoding",
        "category": "infra",
        "difficulty_tier": "advanced",
        "tldr": "Inference optimization that parallelises attention across the KV cache for long-context decoding, dramatically improving throughput on long-prompt queries.",
        "plain_english": "Standard attention during generation processes one token at a time and attends serially over the full KV cache — slow when the cache is huge. Flash Decoding splits the KV cache into chunks and processes them in parallel, then combines the results. For long contexts (10k+ tokens), this turns sequential attention into a parallel reduction, giving 2-8× decoding speedups. It's a successor to FlashAttention's training optimizations adapted for inference.",
        "how_it_works": "Split the KV cache into chunks (e.g. 1024 tokens each). Compute attention scores per chunk in parallel using FlashAttention kernels. Combine chunk results via log-sum-exp reduction to produce the correct softmax output. Memory access patterns are highly cache-friendly. The Tri Dao team introduced Flash Decoding as part of FlashAttention v2/v3 work; it ships in vLLM and TGI for long-context serving.",
        "why_it_matters": "Long-context inference's per-token cost is dominated by attention over the KV cache. Flash Decoding cuts that cost dramatically by parallelising. For chat agents with long histories, RAG with substantial retrieved context, or coding assistants with whole-file context, the throughput improvement is decisive.",
        "example": "A coding assistant serves Llama 3 70B with 32K-token contexts. Without Flash Decoding: 22 tokens/sec per request. With Flash Decoding: 80 tokens/sec. Per-user latency drops; concurrent users per GPU rise. The team rolls out the optimization and reduces serving cost 3×.",
        "pitfalls": [
            "Implementation needs CUDA: Flash Decoding's speedup comes from custom kernels; non-CUDA backends miss the benefit.",
            "Chunk size tuning: too small wastes overhead; too large loses parallelism.",
            "Compatibility with KV compression: combining with quantization or eviction needs careful kernel support.",
            "Short-context regression: minor overhead on short prompts; gains only emerge at longer contexts."
        ],
        "when_use": "Use as default in long-context serving setups. Built into modern serving stacks (vLLM, TGI) — enable via config.",
        "when_avoid": "Avoid for short-context-only workloads where the optimization adds overhead without proportional gain.",
        "related_terms": ["flash-attention", "kv-cache", "kv-cache-compression", "inference-server", "context-window", "tokens-per-second"],
        "related_tools": ["vllm", "tgi"],
        "faq": [
            {"q": "Flash Decoding vs FlashAttention?",
             "a": "FlashAttention optimises training and full-sequence prefill. Flash Decoding optimises decode-phase attention with one-token queries over long KV caches. They complement."},
            {"q": "Is this on by default?",
             "a": "Recent vLLM and TGI versions enable it for sufficiently long contexts. Check your version's defaults."},
            {"q": "Speedup magnitude?",
             "a": "2-8× on long-context decoding (10k+ tokens). Smaller for short contexts."},
            {"q": "Combine with paged attention?",
             "a": "Yes — they're orthogonal mechanisms. Modern serving stacks combine both."}
        ]
    },
    # 39. sglang-radix-attention
    {
        "slug": "sglang-radix-attention",
        "title": "SGLang Radix Attention",
        "category": "infra",
        "difficulty_tier": "advanced",
        "tldr": "Inference optimization that shares KV cache across requests with common prompt prefixes via a radix tree, dramatically accelerating systems with shared system prompts or templates.",
        "plain_english": "Many production systems share large prompt prefixes — system prompts, few-shot examples, RAG context. Recomputing attention over these for every request wastes compute. RadixAttention (from SGLang) stores common prefixes in a radix tree and reuses their KV cache across all matching requests. Identical prefixes share computation; the only per-request work is the unique suffix. Throughput on prefix-heavy workloads jumps significantly.",
        "how_it_works": "Maintain a radix tree (prefix tree) of seen request prompts, with cached KV blocks attached to nodes. Incoming requests walk the tree to find their longest matching prefix. The matched KV is reused; only the tail (unique part) of the prompt requires fresh computation. Eviction policies (LRU, frequency-based) keep cache size bounded. The RadixAttention paper (Zheng et al. 2024) introduced the structure; SGLang ships it as a primary feature; vLLM also implements prefix caching via similar mechanisms.",
        "why_it_matters": "Prefix sharing is one of the biggest realistic wins in production LLM serving. System prompts, RAG context, few-shot demonstrations, agent instructions — all repeat across many requests. Without prefix caching, each repetition recomputes the same attention. With RadixAttention, repetition is cheap. For SaaS systems with shared templates, throughput gains of 3-10× are common.",
        "example": "A SaaS product uses a 4K-token system prompt across all customer chats. Without prefix caching, each turn re-encodes the system prompt. With SGLang's RadixAttention, the system prompt's KV cache is shared across all sessions. Aggregate GPU time on the system prompt drops 95%; user-perceived latency shrinks; per-request cost falls accordingly.",
        "pitfalls": [
            "Cache eviction tuning: too-small radix tree forces frequent recomputation; too large wastes GPU memory; tune.",
            "Cache invalidation: model swaps invalidate the entire tree; rebuild on deploys.",
            "Per-tenant isolation: in multi-tenant systems, ensure tree partitioning prevents cross-tenant prefix sharing if data is sensitive.",
            "Workload shape: gains depend on prefix repetition rates; uniformly unique prompts see less benefit."
        ],
        "when_use": "Use whenever production traffic has common prompt prefixes: shared system prompts, agent templates, RAG context patterns. SGLang's main differentiator.",
        "when_avoid": "Avoid when traffic has no prefix overlap or when memory budget can't accommodate the prefix cache.",
        "related_terms": ["prefix-caching", "kv-cache", "inference-server", "anthropic-prompt-caching", "prompt-caching", "tokens-per-second"],
        "related_tools": [],
        "faq": [
            {"q": "RadixAttention vs vLLM prefix caching?",
             "a": "Same idea, different implementations. SGLang uses a radix tree explicitly; vLLM uses block-level prefix matching. Both achieve similar results for prefix-sharing workloads."},
            {"q": "How does this interact with prompt caching APIs?",
             "a": "Anthropic's and OpenAI's prompt caching are server-side equivalents. RadixAttention is for self-hosted serving; the API-side caches do similar work for hosted deployments."},
            {"q": "Memory cost?",
             "a": "Prefix-cached KV occupies GPU memory; size budget limits cache capacity. Tune to balance hit rate and concurrent-user count."},
            {"q": "Production-ready?",
             "a": "Yes — SGLang is widely deployed for prefix-heavy workloads. Top open-source serving option for chat-and-agent traffic patterns."}
        ]
    },
    # 40. react
    {
        "slug": "react",
        "title": "ReAct (Reasoning + Acting)",
        "category": "concepts",
        "difficulty_tier": "intermediate",
        "tldr": "Agent prompting pattern that interleaves reasoning steps with tool-call actions, letting the model think between tool invocations and adjust based on results.",
        "plain_english": "ReAct is one of the foundational agent patterns. The model alternates between 'Thought' (a reasoning step about what to do next) and 'Action' (calling a tool). After each action, it observes the result, thinks about it, decides the next action. This interleaved reasoning produces better tool-using behaviour than pure prompt-and-call patterns because the model explicitly reasons between steps rather than committing to a fixed plan upfront.",
        "how_it_works": "Format the prompt with explicit Thought/Action/Observation labels. Each step: model emits a thought ('I need to find X first'), then an action ('search(X)'), receives the observation (search result), continues with the next thought-action-observation cycle. The model decides when to stop ('Final Answer:'). Originally introduced by Yao et al. 2022, ReAct became foundational for tool-using agents and inspired LangChain's agent framework, AutoGen, and many production agent designs.",
        "why_it_matters": "ReAct was the breakthrough that showed LLMs could reliably use tools when given a structured reasoning scaffold. Pre-ReAct, tool-calling agents were brittle; ReAct made them dependable enough for production. Modern reasoning models (o-series, R1) extend ReAct's interleaved-reasoning idea internally. Understanding ReAct is foundational to understanding modern agent design.",
        "example": "A travel agent uses ReAct. User asks 'Find me a flight to Tokyo and a hotel near Shinjuku for 5 days starting Friday.' Thought: 'I need flight options first.' Action: search_flights(Tokyo, Friday). Observation: 12 results. Thought: 'Good options at $850-1200. Let me get hotel.' Action: search_hotels(Shinjuku, Friday, 5 days). Observation: 8 hotels. Thought: 'Synthesise.' Final Answer: presents top combinations.",
        "pitfalls": [
            "Format brittleness: malformed Thought/Action labels break parsing; use structured outputs.",
            "Loop detection: agents can repeat the same action when stuck; add cycle detection.",
            "Verbose traces: ReAct adds tokens for thoughts; budget accordingly.",
            "Reasoning model overlap: native reasoning models do internal ReAct-style thinking; explicit ReAct prompting may be redundant."
        ],
        "when_use": "Use as the default agent pattern for tool-using workflows. Especially valuable when the model needs to adapt its plan based on intermediate results.",
        "when_avoid": "Avoid for single-tool-call workflows where ReAct's overhead isn't justified, or when using reasoning models that handle interleaved reasoning natively.",
        "related_terms": ["ai-agent", "agent-loop", "tool-use", "chain-of-thought", "plan-and-execute", "reflexion"],
        "related_tools": ["langgraph", "autogen"],
        "faq": [
            {"q": "Is ReAct still relevant in 2026?",
             "a": "Conceptually yes — interleaved reasoning + acting underpins modern agents. Implementation has evolved; bare ReAct prompts are less common, but reasoning models embody the principle."},
            {"q": "ReAct vs plan-and-execute?",
             "a": "Plan-and-execute commits to a plan upfront and executes it. ReAct interleaves reasoning and action — adapt as you go. ReAct is more flexible but harder to predict."},
            {"q": "Best when there are many tools?",
             "a": "Yes — ReAct's per-step reasoning helps the model select the right tool. Pair with tool routing for many-tool registries."},
            {"q": "Need a reasoning model?",
             "a": "No — works with chat models. Reasoning models do better in many cases, but ReAct-style prompting works with any tool-using LLM."}
        ]
    },
    # 41. reflexion
    {
        "slug": "reflexion",
        "title": "Reflexion",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Agent self-improvement framework where the agent reflects on past failures, stores those reflections in memory, and uses them to do better on subsequent attempts.",
        "plain_english": "After an agent fails a task, Reflexion asks it: 'why did you fail?' The model produces a reflection — a written analysis of the mistake. That reflection gets stored and shown to the agent on the next attempt at similar tasks. Over many attempts, the agent accumulates a personal lessons-learned memory and improves dramatically without weight updates. Shinn et al. 2023 introduced Reflexion; it works for code, decision-making, and reasoning tasks.",
        "how_it_works": "Run an agent on a task. Evaluate success (test passes, judge approves, etc.). On failure, prompt the agent: 'You failed because... What should you do differently next time?' The agent produces a verbal reflection. Store the reflection in episodic memory. On the next attempt, prepend relevant reflections to the agent's context. Repeat. The agent learns over episodes without fine-tuning. Effective on benchmarks where multiple attempts are allowed.",
        "why_it_matters": "Reflexion shows that LLMs can self-improve through verbal feedback alone — no gradient updates required. The technique is applicable in production: agents that fail can analyse and improve. It's also a cleaner mental model for many self-improvement systems and inspires the broader research line on language-based learning.",
        "example": "A coding agent fails to fix a bug. Reflexion prompts: 'Why did the test fail?' Agent: 'I edited the wrong function — should have looked at call site first.' Stored reflection: 'For ambiguous bug reports, locate the call site before editing.' Next bug: agent reads the reflection, follows it, succeeds. Over 100 attempts, success rate climbs from 30% to 65%.",
        "pitfalls": [
            "Reflection quality: vague reflections ('I should be more careful') don't help; prompt for specific actionable lessons.",
            "Memory bloat: many reflections compete for context; relevance retrieval keeps memory useful.",
            "Hallucinated lessons: agents can invent post-hoc explanations that don't transfer; verify with held-out evals.",
            "Confounds with overall capability: improvements may come from extra attempts more than from reflections; ablate to confirm reflection contributes."
        ],
        "when_use": "Use for repeatable agent tasks where failures can be detected and analysed: coding, structured search, multi-attempt decision making.",
        "when_avoid": "Avoid for one-shot tasks where there's no opportunity for iteration, or for chat where each conversation is unique.",
        "related_terms": ["ai-agent", "agent-loop", "self-reflection-loop", "react", "agent-memory", "critique-loop"],
        "related_tools": ["langgraph"],
        "faq": [
            {"q": "Reflexion or self-refine?",
             "a": "Reflexion learns across episodes via stored reflections; self-refine improves within a single response. They complement: reflect across tasks, refine within."},
            {"q": "Need fine-tuning?",
             "a": "No — Reflexion works at inference with no weight updates. The 'learning' is verbal, in stored reflections."},
            {"q": "How is the reflection memory structured?",
             "a": "Variants exist: append-only log, retrieval-keyed, organised by failure type. Most production setups use retrieval over a categorised store."},
            {"q": "Does it work for non-coding tasks?",
             "a": "Yes — original paper covered decision-making and reasoning. Effective wherever success/failure is measurable and reflections can be specific."}
        ]
    },
    # 42. voyager-agent
    {
        "slug": "voyager-agent",
        "title": "Voyager Agent",
        "category": "concepts",
        "difficulty_tier": "advanced",
        "tldr": "Open-ended embodied agent design that incrementally discovers, codes, and stores reusable skills — exemplified by Wang et al.'s Minecraft-playing Voyager.",
        "plain_english": "Voyager is the canonical example of an LLM-driven open-ended agent that builds its own skill library. Rather than completing one task and stopping, the agent decides what to learn next, codes a new skill in code-form, tests it in the environment, and stores it for later reuse. Over time it accumulates a library of skills that compose into more complex behaviours. Originally demonstrated in Minecraft; the design pattern generalises to any environment with executable code and an exploration goal.",
        "how_it_works": "Three components. (1) Curriculum module: proposes the next skill to learn based on the agent's current capabilities and environment state. (2) Skill library: code-form skills indexed by description, retrievable when needed. (3) Iterative prompting: GPT-4 generates skill code, the environment executes it, errors feed back for refinement. The agent self-organises its learning: new skills build on stored ones, expanding capability over time. Wang et al. 2023's Voyager demonstrated this pattern producing rich Minecraft gameplay without explicit task instructions.",
        "why_it_matters": "Voyager demonstrated that open-ended capability acquisition is feasible with current LLMs. The design pattern — curriculum + skill library + iterative coding — applies beyond Minecraft to robotics, web automation, and game playing. It points toward agents that grow capability autonomously rather than being trained for fixed tasks. Subsequent work has extended Voyager-style agents to other domains.",
        "example": "A research team applies Voyager-style design to web automation. The agent starts with primitives (click, type, navigate) and learns skills like 'fill_login_form' and 'extract_table_data'. Over 1000 hours of exploration, it builds a library of 200+ reusable skills. New tasks are tackled by composing stored skills rather than re-deriving from scratch.",
        "pitfalls": [
            "Skill quality: poorly-tested skills get added to the library and corrupt later attempts; verify before storing.",
            "Curriculum drift: without anchoring to a goal, exploration can wander unproductively.",
            "Cost: continuous LLM-driven skill acquisition is expensive; budget for thousands of LLM calls per session.",
            "Environment specificity: Voyager-style works best in environments with clear executable interfaces and feedback signals."
        ],
        "when_use": "Use the framing for research on open-ended agents, robotics with code-as-policy, or game-playing agents where skill accumulation matters.",
        "when_avoid": "Avoid for narrow production tasks where skill libraries add complexity without clear payoff. Most real applications use simpler agent patterns.",
        "related_terms": ["ai-agent", "embodied-ai", "react", "memory-augmented-agent", "computer-use", "world-model"],
        "related_tools": [],
        "faq": [
            {"q": "Voyager only for Minecraft?",
             "a": "Original paper, yes. The pattern generalises — research has applied it to web tasks, robotics, and other environments. The Minecraft version was the proof-of-concept."},
            {"q": "Need code execution?",
             "a": "Yes — Voyager's skills are code, executed in the environment. Environments without code-as-action need adaptation (e.g. action sequences as JSON skills)."},
            {"q": "Production deployments?",
             "a": "Limited — research-grade. Some inspired production designs use simpler skill libraries. Pure Voyager is rare in production."},
            {"q": "Cost?",
             "a": "Significant — Voyager runs continuously, generating and refining skills. Original paper used GPT-4 over thousands of hours of simulated time."}
        ]
    },
    # 43. browser-use-agent
    {
        "slug": "browser-use-agent",
        "title": "Browser-Use Agent",
        "category": "concepts",
        "difficulty_tier": "intermediate",
        "tldr": "AI agent that operates web browsers to complete tasks — clicking, typing, navigating — via DOM access, visual grounding, or accessibility tree introspection.",
        "plain_english": "Browser-use agents automate web actions: book a flight, fill a form, scrape data, complete a checkout. The agent reads the page (DOM, screenshot, or accessibility tree), reasons about what to do next, and executes browser actions. Modern instances include Anthropic's Computer Use, OpenAI Operator, browser-use (open source), and various RPA-style agents. Hard problems: dynamic pages, anti-bot defences, ambiguous UI, recovery from errors.",
        "how_it_works": "The agent has access to: a browser instance (Playwright, Selenium, or similar), an action interface (click, type, scroll, navigate), and a perception interface (DOM dump, screenshot+coordinates, accessibility tree). At each step: perceive current state, reason about next action via LLM, execute, observe result, continue. Variants differ in perception (vision-only vs DOM vs hybrid) and reasoning depth (fast simple agents vs thinking agents). State management — what page you're on, what you've already filled — is critical and often encoded in prompt context.",
        "why_it_matters": "Most enterprise software lives in web UIs without good APIs. Browser-use agents are how AI bridges to the web's enormous installed base of human-only interfaces. As capabilities improve, they replace RPA tools, automate research workflows, and enable consumer-facing assistant features (Operator-style). Reliability and safety remain hard problems but are improving fast.",
        "example": "A team uses a browser-use agent to automate competitive-research tasks. The agent visits competitor sites, navigates to pricing pages, extracts plan tiers, fills internal CRM forms with the data. Tasks that took 2 hours of manual work complete in 5 minutes. Reliability is ~85% — the agent fails on novel layouts; failures are flagged for human review.",
        "pitfalls": [
            "Anti-bot defenses: CAPTCHA, behavioural fingerprinting, IP filtering — operating browsers at scale gets blocked.",
            "Brittle to UI changes: layouts shift, element IDs change; agents trained on stable patterns break.",
            "Authentication: persistent login state, MFA, OAuth flows complicate agent deployment.",
            "Privacy and trust: browser agents can access sensitive data and take actions; sandboxing and confirmation prompts essential."
        ],
        "when_use": "Use for automating web workflows lacking APIs: competitive research, data extraction, internal-tool automation, customer-facing assistant features over web apps.",
        "when_avoid": "Avoid when an API exists (use the API), when latency matters (browsers are slow), or when actions are high-stakes and reliability isn't yet sufficient.",
        "related_terms": ["computer-use", "gui-grounding", "ai-agent", "vision-language-model", "tool-use", "embodied-ai"],
        "related_tools": [],
        "faq": [
            {"q": "DOM-based or vision-based?",
             "a": "DOM is faster and more reliable when available; vision (screenshot grounding) works on any UI but is slower and noisier. Hybrid approaches are common."},
            {"q": "Is this safe for autonomous use?",
             "a": "Sandboxing, action confirmation for sensitive operations, and rate limiting are essential. Don't run with real-world write permissions without these."},
            {"q": "Best frameworks?",
             "a": "browser-use (open-source, popular in 2026), Anthropic Computer Use SDK, OpenAI Operator, Playwright Browser MCP servers. Choose by deployment constraints."},
            {"q": "Reliability levels?",
             "a": "70-95% on stable workflows depending on design. Frontier models on standard benchmarks (WebArena, OSWorld) reach 30-50% — production tasks are usually narrower and easier."}
        ]
    },
    # 44. memory-augmented-agent
    {
        "slug": "memory-augmented-agent",
        "title": "Memory-Augmented Agent",
        "category": "concepts",
        "difficulty_tier": "intermediate",
        "tldr": "Agent design with persistent memory across sessions — facts, preferences, past failures — enabling personalisation and accumulating context beyond single conversations.",
        "plain_english": "Stateless agents start fresh each session. Memory-augmented agents remember: who you are, what you said before, what you prefer, what failed last time. Memory typically lives in a vector store, a structured database, or both. The agent reads relevant memories before responding and writes new ones during the interaction. Personalised assistants, customer-support agents, and learning-agent systems all benefit.",
        "how_it_works": "Persistent storage holds memories: episodic (specific past events), semantic (facts about the user/world), and procedural (skills/methods). On each turn, retrieve relevant memories — usually via vector similarity over embeddings — and inject into the agent's context. After the turn, extract new memories from the conversation and store them. Frameworks (Mem0, LangGraph memory, Letta) ship memory primitives. Memory hygiene — avoiding stale or contradictory memories — is an ongoing problem.",
        "why_it_matters": "Memory turns chatbots into assistants. Without it, every conversation restarts from zero — frustrating for users, missed context for the system. With memory, agents become continuous — they reference past projects, learn user preferences, avoid repeating past mistakes. For B2C products and personal assistants, memory is increasingly table stakes.",
        "example": "A personal-finance assistant uses a memory-augmented agent. Over weeks, it learns the user's budget categories, recurring expenses, and saving goals. When the user asks 'how am I doing this month?' the assistant pulls relevant memories, references past months, and produces a personalised analysis. Without memory, every interaction would require re-explaining context.",
        "pitfalls": [
            "Stale memories: facts change (user's job, location, preferences); add freshness tracking and update logic.",
            "Contradictory memories: 'user prefers oat milk' vs 'user is allergic to oats'; resolve conflicts or flag.",
            "Privacy: memories are sensitive data; encryption, retention policies, and user-deletion APIs are required.",
            "Memory bloat: too many memories drown the agent; relevance ranking and pruning matter."
        ],
        "when_use": "Use for personalised assistants, multi-session customer support, learning systems, and any agent expected to remember across conversations.",
        "when_avoid": "Avoid for one-shot tasks where no continuity is needed, or where privacy regulations make memory storage too risky.",
        "related_terms": ["agent-memory", "ai-agent", "agent-loop", "rag", "retrieval", "vector-database"],
        "related_tools": ["langgraph"],
        "faq": [
            {"q": "Memory in vector store or DB?",
             "a": "Vector store for semantic retrieval; structured DB for facts and constraints. Most production systems use both."},
            {"q": "How much memory to keep?",
             "a": "Indefinite for personal assistants; bounded with retention for support agents. Match to use case and privacy regulations."},
            {"q": "How is this different from RAG?",
             "a": "RAG retrieves from documents about the world; memory retrieves about the user/agent's history. Mechanisms overlap; purposes differ."},
            {"q": "Does memory hurt latency?",
             "a": "Adds a retrieval step per turn — usually <100ms. Acceptable in most chat use cases."}
        ]
    },
    # 45. mt-bench
    {
        "slug": "mt-bench",
        "title": "MT-Bench",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Multi-turn evaluation benchmark using 80 challenging questions across 8 categories, scored by GPT-4 as judge to test conversational LLM quality.",
        "plain_english": "MT-Bench evaluates chat models on multi-turn conversations. The benchmark has 80 prompts in 8 categories (writing, roleplay, reasoning, math, coding, extraction, STEM, humanities). Each prompt is two turns: the model answers turn 1, gets a follow-up question dependent on turn 1, and answers turn 2. GPT-4 as judge scores the conversation 1-10. The aggregated score is a widely-cited measure of conversational quality.",
        "how_it_works": "LMSYS released MT-Bench in 2023 as part of the Chatbot Arena ecosystem. The 80 questions are fixed; categories cover diverse skills. For each question, run the model in turn 1 (question), record output, then turn 2 (follow-up that depends on turn 1's content), record output. Send the full transcript plus a scoring rubric to GPT-4. GPT-4 outputs a 1-10 score. Aggregate scores across questions; report by category and overall. Score correlates with human preference but with known biases (length, GPT-4 self-preference).",
        "why_it_matters": "MT-Bench is one of the most-cited automatic chat benchmarks. It's cheap to run (160 model calls + 80 judge calls), fast, and reasonably correlated with human judgment. Limitations are known: GPT-4 favours its own style; the 80 questions can be saturated by aggressive optimisation. Newer benchmarks (Arena-Hard, MultiTurn-Bench) build on its template with harder questions.",
        "example": "A team launches a new chat fine-tune. They run MT-Bench: turn 1 score 8.2, turn 2 score 7.8, average 8.0. Compared to the baseline (7.6), the new fine-tune is better. They report the score on the model card alongside human-eval results from internal raters.",
        "pitfalls": [
            "GPT-4 self-bias: GPT-4-style outputs score higher; calibrate when comparing models from different families.",
            "Saturation: top models are clustered around 9; small differences may not be statistically meaningful.",
            "80 questions is narrow: real chat traffic is broader; supplement with other benchmarks.",
            "Length bias: longer responses tend to score higher even when not better; debias or use length-controlled judges."
        ],
        "when_use": "Use as one of several chat benchmarks for new model releases. Cheap and standard; supplement with other metrics.",
        "when_avoid": "Avoid as the only quality measure. Use Arena Elo, internal evals, and human ratings for production decisions.",
        "related_terms": ["arena-hard", "elo-rating-llm", "evaluation-set", "agent-as-judge", "g-eval", "multi-turn-evaluation"],
        "related_tools": [],
        "faq": [
            {"q": "MT-Bench or Arena Elo?",
             "a": "MT-Bench is automatic and cheap; Arena Elo uses real user preferences and is more authoritative for production decisions. Use both."},
            {"q": "Why GPT-4 as judge?",
             "a": "Strongest available judge in 2023 when the benchmark was created. Subsequent versions use newer judges; the framework remains the same."},
            {"q": "Top scores in 2026?",
             "a": "Frontier models cluster around 9.0-9.4. Differentiation at the top is hard via MT-Bench alone."},
            {"q": "Should I tune for MT-Bench?",
             "a": "Tuning specifically for any benchmark causes Goodhart drift. Use it as a sanity check; don't optimise against it directly."}
        ]
    },
    # 46. arena-hard
    {
        "slug": "arena-hard",
        "title": "Arena-Hard",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Curated benchmark of 500 hard prompts derived from Chatbot Arena traffic, designed to differentiate strong chat models that saturate easier benchmarks.",
        "plain_english": "MT-Bench and similar benchmarks saturate as models improve — top models all score similarly. Arena-Hard fixes this by selecting 500 of the hardest prompts from real Chatbot Arena traffic — questions where strong models actually disagree. Scoring uses LLM-as-judge in pairwise comparisons against a baseline (e.g. GPT-4 Turbo). The result is a benchmark that still discriminates among frontier models.",
        "how_it_works": "LMSYS curates Arena-Hard by sampling Chatbot Arena interactions, filtering for prompts where strong models disagreed (signal of difficulty), and quality-checking. The 500 selected prompts cover diverse hard scenarios: tricky reasoning, ambiguous instructions, multi-step requirements. To benchmark a model: get its responses to all 500, get baseline responses (e.g. GPT-4 Turbo), have a strong judge (e.g. GPT-4) compare pairs. Win rate against baseline is the score.",
        "why_it_matters": "Frontier-model evaluation is hard because most benchmarks saturate. Arena-Hard explicitly targets the discriminating tail — questions strong models still get wrong. As of 2026, Arena-Hard is one of the standard reference benchmarks for frontier-grade models alongside Arena Elo and human evals.",
        "example": "A team evaluates a 70B fine-tune. MT-Bench: 8.7 (close to top tier, hard to differentiate). Arena-Hard win rate vs GPT-4-Turbo: 47% (clear sub-frontier signal). They use Arena-Hard for differentiation among strong candidates rather than binary go/no-go.",
        "pitfalls": [
            "Judge bias: the LLM judge has biases; calibrate against human pairs.",
            "Distribution shift: as model capabilities evolve, 'hard' shifts; refresh the benchmark periodically.",
            "Cost: 500 prompts × pairwise comparison = many judge calls; budget per evaluation.",
            "Length bias: longer responses still tend to win; control or use length-debiased judges."
        ],
        "when_use": "Use to differentiate among strong chat models where MT-Bench has saturated. Standard benchmark for frontier model launches.",
        "when_avoid": "Avoid for narrow domain tasks where Arena-Hard's general-purpose distribution doesn't reflect your traffic.",
        "related_terms": ["mt-bench", "elo-rating-llm", "agent-as-judge", "evaluation-set", "preference-data", "g-eval"],
        "related_tools": [],
        "faq": [
            {"q": "Arena-Hard or Arena Elo?",
             "a": "Arena Elo uses real user judgments; Arena-Hard uses LLM-as-judge on curated hard prompts. Both useful; Arena Elo is closer to user preference, Arena-Hard is cheaper to run."},
            {"q": "Why 500 prompts?",
             "a": "Enough for statistical significance; small enough to run cheaply. 500 is the standard size; some custom variants use 1000."},
            {"q": "Can I use a non-GPT-4 judge?",
             "a": "Yes — Claude or strong open models work. Calibrate against human data; different judges have different biases."},
            {"q": "Updated regularly?",
             "a": "LMSYS releases versions periodically as 'hard' shifts. Use the latest for current model comparisons."}
        ]
    },
    # 47. truthfulqa
    {
        "slug": "truthfulqa",
        "title": "TruthfulQA",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Benchmark of 817 questions designed to elicit common misconceptions, testing whether models give truthful answers vs. confidently asserting popular falsehoods.",
        "plain_english": "TruthfulQA probes a specific failure mode: models that learned popular myths from internet text. Each of its 817 questions is constructed so the easy 'parrot the common belief' answer is wrong. A truthful model recognises the trap and gives the correct answer; an untruthful one confidently states the misconception. The benchmark scores both 'truthful' (avoid asserting false things) and 'informative' (don't just refuse) — both matter.",
        "how_it_works": "Questions were hand-designed to target known misconception areas: medicine, law, history, common-sense beliefs. Each has a set of correct and incorrect answers. To benchmark a model: prompt with each question, score the response on truthfulness (does it avoid false claims?) and informativeness (does it actually answer?). Variants score MC1 (single best answer), MC2 (probability mass on correct), and free-form generation with judge models. TruthfulQA was introduced by Lin et al. 2022 and remains widely cited for truthfulness.",
        "why_it_matters": "Confidently wrong answers are dangerous in production. TruthfulQA gives a measurable handle on this specific failure mode. Models can also be evaluated on improvement over training: did a fine-tune introduce more confident wrongness? As of 2026, TruthfulQA is a standard release-eval but somewhat saturated; newer truthfulness probes complement it.",
        "example": "A team launches a chat fine-tune. Pre-fine-tune TruthfulQA score: 51% MC1. Post-fine-tune: 67% MC1. The fine-tune dropped popular-misconception failures substantially, validated against the bench. They publish the score on the model card.",
        "pitfalls": [
            "Memorisation: heavily-cited models may have memorised the benchmark; results inflate.",
            "Coverage: 817 questions cover a slice of misconceptions, not all. Domain-specific truthfulness needs custom evals.",
            "Refusal scoring: models that refuse all questions score 'truthful' but are useless; pair with informativeness.",
            "Static benchmark: misconceptions evolve; refresh."
        ],
        "when_use": "Use as a baseline truthfulness eval for chat and assistant deployments. Standard release-eval.",
        "when_avoid": "Avoid as the only truthfulness measure — supplement with domain-specific factuality evals (medical, legal, financial).",
        "related_terms": ["truthfulness-eval", "hallucination", "evaluation-set", "bias-eval", "red-teaming", "ai-governance"],
        "related_tools": [],
        "faq": [
            {"q": "TruthfulQA or HELM?",
             "a": "TruthfulQA is one specific eval; HELM is a broader benchmark suite that includes truthfulness alongside many other measures."},
            {"q": "Score interpretation?",
             "a": "MC1 above 70% is good for general chat models; below 50% suggests significant misconception issues. Frontier models reach 70-85%."},
            {"q": "Is this contaminated?",
             "a": "Likely — the questions have been public for years and are in many training corpora. Use newer truthfulness benchmarks to complement."},
            {"q": "Does RAG help?",
             "a": "When the corpus is reliable, yes — grounding answers in trustworthy sources improves truthfulness. RAG without quality control may not help."}
        ]
    },
    # 48. per-token-cost
    {
        "slug": "per-token-cost",
        "title": "Per-Token Cost",
        "category": "ops",
        "difficulty_tier": "beginner",
        "tldr": "Pricing unit for LLM API services that charges separately for input and output tokens, typically expressed in dollars per million tokens.",
        "plain_english": "LLM APIs charge by tokens, not requests. Per-token cost is the unit price — usually quoted as 'X dollars per million input tokens' and 'Y dollars per million output tokens'. Input is what you send (prompt + context); output is what the model generates. Output tokens are typically 3-5× more expensive than input. Understanding per-token cost is essential for budgeting, comparing providers, and optimising prompts.",
        "how_it_works": "Each API call returns token counts: input_tokens (prompt and context), output_tokens (generated). Multiply each by the per-token price for your model and sum. Caching, batch APIs, and reasoning tokens have different prices. Aggregate across calls to get total spend. Most providers expose dashboards showing token consumption; some support automatic cost attribution to user/feature dimensions.",
        "why_it_matters": "Per-token cost is the dominant cost driver for AI features at scale. Understanding it lets you compare providers fairly (some cheap on input, expensive on output, vice versa), optimise prompts (shorter is cheaper), and choose models (smaller is cheaper but quality trades off). Per-token economics determine viability of many product features.",
        "example": "A team runs a summarisation feature averaging 5K input tokens and 500 output tokens per request. At GPT-4o pricing ($2.50/M input, $10/M output), each request costs $0.0175. At 100K requests/day, that's $1750/day. They explore alternatives: cheaper model (Haiku at 1/8 the cost), shorter prompts, output caching. Cost drops 70% with minimal quality regression.",
        "pitfalls": [
            "Output cost shock: output is 3-5× more expensive than input; long outputs can dominate spend.",
            "Cached input pricing: many providers charge less for cached prompts; design prompts to leverage caching.",
            "Reasoning token cost: o-series and similar charge for thinking tokens, often at output rates; budget separately.",
            "Hidden tokens: tool-call results, system prompts, retrieved context all count; track carefully."
        ],
        "when_use": "Use the framing constantly when budgeting AI features, comparing providers, and optimising prompts.",
        "when_avoid": "Don't over-optimise for tokens at the expense of quality; quality regressions cost more in user trust than tokens save.",
        "related_terms": ["cost-attribution", "cost-per-query", "token-budget", "anthropic-prompt-caching", "llm-rate-limit", "model-routing"],
        "related_tools": ["langfuse", "helicone"],
        "faq": [
            {"q": "Why output more expensive than input?",
             "a": "Output requires sequential generation (each token depends on prior); input can be processed in parallel. Generation is the compute bottleneck."},
            {"q": "What's a typical $/M token in 2026?",
             "a": "Frontier models: $1-15 input, $5-60 output. Cheap models: $0.10-0.50 input, $0.30-2.00 output. Wide range; check current pricing."},
            {"q": "Cached input cheaper?",
             "a": "Yes — Anthropic, OpenAI, Google all offer cached input at 30-90% discount. Worth exploiting for repeated system prompts."},
            {"q": "Are reasoning tokens billed?",
             "a": "Yes — at output rates typically. Heavy reasoning workloads can cost more than expected; budget thinking tokens explicitly."}
        ]
    },
    # 49. inference-trace
    {
        "slug": "inference-trace",
        "title": "Inference Trace",
        "category": "ops",
        "difficulty_tier": "intermediate",
        "tldr": "Detailed log of an LLM request including prompts, intermediate tool calls, model responses, latency, and tokens — used for debugging, observability, and cost attribution.",
        "plain_english": "An inference trace is everything that happened during a single LLM request: the input prompt, any retrieval calls, the model's response (including thinking traces if available), tool calls and their results, latency at each step, and token counts. Stored properly, traces let you debug failed requests, audit model behaviour, attribute cost, and feed into evaluation pipelines. As LLM systems get more complex (RAG, agents, tool use), traces become essential observability infrastructure.",
        "how_it_works": "A tracing library or LLM gateway intercepts each request. It records: timestamps, inputs/outputs at each stage, tool calls, model parameters (temperature, model version), latency, tokens, errors. Traces are typically structured as nested spans — a root span for the request, children for retrieval, model call, tool invocations. Stored in a tracing backend (Langfuse, Helicone, Phoenix, Arize, Honeycomb, OpenTelemetry-GenAI). Queryable for debugging and attribution; exportable to evaluation pipelines.",
        "why_it_matters": "LLM systems are non-deterministic and complex. Without traces, debugging is guesswork. With traces, you can replay failed requests, identify performance bottlenecks (slow retrievals, expensive thinking traces), attribute costs to features and customers, and build automated evaluation on production traffic. As of 2026, structured tracing via OpenTelemetry-GenAI semantics is becoming standard.",
        "example": "A user reports a wrong answer from the assistant. Engineer pulls the inference trace: sees the retrieval returned 5 irrelevant docs (wrong embedding), the model dutifully synthesised from them, producing a wrong answer. Fix: improve retrieval relevance. Without the trace, the team would have suspected the model and wasted time tuning prompts.",
        "pitfalls": [
            "PII in traces: prompts contain user data; redact and apply retention policies.",
            "Storage cost: at scale, trace volume is significant; sample or aggregate older traces.",
            "Performance overhead: synchronous trace writes slow requests; use async write paths.",
            "Schema fragmentation: different libraries produce different trace shapes; OpenTelemetry-GenAI helps standardise."
        ],
        "when_use": "Use for any production LLM system. Essential for debugging, cost attribution, performance tuning, and quality monitoring.",
        "when_avoid": "Don't skip tracing for prototypes intended to ship. Retrofitting traces is harder than building in from day one.",
        "related_terms": ["ai-observability", "llm-observability", "cost-attribution", "opentelemetry-genai", "reasoning-trace", "model-routing"],
        "related_tools": ["langfuse", "helicone"],
        "faq": [
            {"q": "Trace or log?",
             "a": "Logs are flat events; traces are structured request flows with parent-child relationships. Traces are richer for LLM systems with multi-step pipelines."},
            {"q": "How long to retain?",
             "a": "Active debugging: 7-30 days hot. Audit/eval: longer warm storage. Privacy regulations may set max retention; comply."},
            {"q": "OpenTelemetry-GenAI?",
             "a": "Standardised trace schema for GenAI workloads, extending OpenTelemetry. Adoption is growing; helps avoid vendor lock-in."},
            {"q": "What about thinking tokens?",
             "a": "Trace them as part of the model call, with separate token counts. Important for cost attribution since reasoning tokens are billed."}
        ]
    },
    # 50. json-mode
    {
        "slug": "json-mode",
        "title": "JSON Mode",
        "category": "protocols",
        "difficulty_tier": "intermediate",
        "tldr": "API feature that constrains model output to valid JSON, optionally conforming to a specified schema, eliminating parse-and-retry loops.",
        "plain_english": "Without JSON mode, asking a model for JSON gives 'usually valid JSON' — sometimes with leading text, comments, trailing chatter. Production code spends effort on parsing-and-retrying. JSON mode is the API-side fix: providers force the model to produce valid JSON. Stricter variants (OpenAI's strict mode, Anthropic's tool-use schemas) enforce a JSON Schema, so the output not only parses but matches your expected fields. Eliminates a category of brittleness.",
        "how_it_works": "Two levels. (1) Format mode: provider applies token-level constraints during generation so output is always valid JSON. Open-ended structure; you parse what you need. (2) Schema mode: provider applies tighter constraints to match a JSON Schema you provide. Output keys, types, and required fields are guaranteed. OpenAI's response_format with strict=true, Anthropic's tool-use input schemas, and various provider equivalents implement schema-mode JSON. Local models achieve similar via Outlines, Instructor, or grammar-based decoding.",
        "why_it_matters": "Reliable structured output is essential for any pipeline feeding LLM outputs into typed code. JSON mode replaces brittle parse-and-retry with guaranteed validity. For data extraction, function calling, classification, and agent tool calls, it's standard. The strict-schema variant is dramatically more reliable than free-form 'please output JSON' prompting.",
        "example": "A team extracts contact info from emails. Without JSON mode: ~5% of responses fail parsing (wrong format, extra commentary), requiring retries. With JSON mode + strict schema: 100% parse, fields are guaranteed types. Throughput rises; failure-handling code shrinks; reliability metrics improve.",
        "pitfalls": [
            "Quality cost on complex schemas: very deep or recursive schemas can degrade output; flatten where possible.",
            "Schema authoring: poorly-written schemas (vague descriptions) reduce model accuracy; treat schemas as first-class artefacts.",
            "Provider differences: OpenAI strict mode, Anthropic tool schemas, Gemini schemas all have different feature subsets; abstract over them.",
            "Latency: token-level constraint enforcement adds slight overhead; usually worth the reliability gain."
        ],
        "when_use": "Use for any LLM output that feeds typed code: extractors, classifiers, function calls, agent tools, structured generators.",
        "when_avoid": "Avoid for free-form text outputs (writing, dialogue). Don't force JSON when natural language is the right output format.",
        "related_terms": ["function-schema", "structured-output", "constrained-decoding", "outlines-library", "instructor-library", "tool-use-format"],
        "related_tools": ["instructor", "outlines"],
        "faq": [
            {"q": "Format mode or strict schema?",
             "a": "Strict schema when you have a fixed structure — best reliability. Format mode when structure is variable but you need parseable JSON."},
            {"q": "Does JSON mode hurt quality?",
             "a": "On simple schemas, no measurable loss. On very complex or unusual schemas, sometimes — model can struggle to fit content into the structure. Test on your data."},
            {"q": "Self-hosted models?",
             "a": "Use Outlines, Instructor, or grammar-based decoding to achieve equivalent constraints on local models. Cloud APIs offer it natively."},
            {"q": "Tool calls require JSON mode?",
             "a": "Tool calling is a specific application of strict schema JSON. The provider enforces the tool's parameter schema during generation."}
        ]
    },
]

# ─────────────────────────── Generation logic ───────────────────────────

def make_meta_title(title):
    s = f"{title} — Plain-English Definition & Expert Guide | OSS AI Hub"
    return s if len(s) <= 120 else f"{title} — Definition | OSS AI Hub"

def make_meta_description(tldr):
    return tldr[:200] if len(tldr) > 200 else tldr

def make_jsonld(slug, title, tldr):
    return {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "name": title,
        "description": tldr,
        "inDefinedTermSet": "https://ossaihub.com/Glossary",
        "url": f"https://ossaihub.com/glossary/{slug}",
        "termCode": slug,
    }

def make_seo_variations(title, slug):
    return [title.lower(), slug.replace("-", " ")]

def finalise_term(rec):
    rec.setdefault("meta_title", make_meta_title(rec["title"]))
    rec.setdefault("meta_description", make_meta_description(rec["tldr"]))
    rec.setdefault("schema_jsonld", make_jsonld(rec["slug"], rec["title"], rec["tldr"]))
    rec.setdefault("seo_variations", make_seo_variations(rec["title"], rec["slug"]))
    rec.setdefault("rewrite_version", "v2")
    rec.setdefault("rewritten_at", NOW)
    rec.setdefault("short_definition", rec["tldr"])
    rec.setdefault("full_explanation", rec["how_it_works"])
    rec.setdefault("common_misconceptions", "")
    rec.setdefault("related_tools", [])
    return rec

REQUIRED_FIELDS = [
    "slug", "title", "category", "difficulty_tier",
    "tldr", "plain_english", "how_it_works", "why_it_matters",
    "example", "pitfalls", "when_use", "when_avoid",
    "related_terms", "faq", "meta_title", "meta_description",
]

def validate_terms(terms, existing_slugs):
    errors = []
    seen = set()
    for rec in terms:
        slug = rec.get("slug", "?")
        for f in REQUIRED_FIELDS:
            if not rec.get(f):
                errors.append(f"{slug}: missing or empty {f}")
        if not SLUG_RE.match(slug):
            errors.append(f"{slug}: bad slug shape")
        if slug in seen:
            errors.append(f"{slug}: duplicate within batch")
        seen.add(slug)
        if slug in existing_slugs:
            errors.append(f"{slug}: collides with existing slug")
        if len(rec.get("tldr", "").split()) > 30:
            errors.append(f"{slug}: tldr > 30 words")
        p = rec.get("pitfalls", [])
        if not (2 <= len(p) <= 4):
            errors.append(f"{slug}: pitfalls count {len(p)} not in 2-4")
        f = rec.get("faq", [])
        if not (3 <= len(f) <= 5):
            errors.append(f"{slug}: faq count {len(f)} not in 3-5")
        for i, qa in enumerate(f):
            if not qa.get("q") or not qa.get("a"):
                errors.append(f"{slug}: faq[{i}] missing q or a")
        mt = rec.get("meta_title", "")
        if len(mt) > 120:
            errors.append(f"{slug}: meta_title len {len(mt)} > 120")
        md = rec.get("meta_description", "")
        if len(md) > 200:
            errors.append(f"{slug}: meta_description len {len(md)} > 200")
        body = " ".join(str(rec.get(k, "")) for k in ("tldr", "plain_english", "how_it_works", "why_it_matters", "example", "when_use", "when_avoid")).lower()
        for bw in BANNED:
            if bw in body:
                errors.append(f"{slug}: contains banned word '{bw}'")
    return errors

EXCLUDE_SLUGS = set()  # filled by direct check after first validate failure

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--emit-only", action="store_true")
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()
    if not (args.merge or args.emit_only or args.validate_only):
        print("Pick --merge, --emit-only, or --validate-only", file=sys.stderr); sys.exit(2)
    if not REBUILT.exists():
        print(f"ERROR: {REBUILT} not found", file=sys.stderr); sys.exit(2)

    existing = json.loads(REBUILT.read_text(encoding="utf-8"))
    existing_slugs = {t.get("slug") for t in existing if t.get("slug")}

    kept = [t for t in TERMS if t["slug"] not in EXCLUDE_SLUGS]
    if len(kept) != 50:
        print(f"ERROR: expected 50 net-new, got {len(kept)} (TERMS={len(TERMS)}, excluded={len(EXCLUDE_SLUGS)})", file=sys.stderr); sys.exit(2)

    finalised = [finalise_term(dict(t)) for t in kept]
    errors = validate_terms(finalised, existing_slugs)
    if errors:
        print(f"VALIDATION FAILED — {len(errors)} issues:")
        for e in errors[:30]:
            print(f"  {e}")
        sys.exit(1)
    print(f"VALIDATION OK — {len(finalised)} new terms, no dupes against {len(existing_slugs)} existing")

    if args.validate_only:
        return

    if args.emit_only:
        OUT_NEW_ONLY.write_text(json.dumps(finalised, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {len(finalised)} terms to {OUT_NEW_ONLY}")
        return

    if args.merge:
        merged = existing + finalised
        REBUILT.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Merged: {len(existing)} existing + {len(finalised)} new = {len(merged)} total")
        OUT_NEW_ONLY.write_text(json.dumps(finalised, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Also wrote new-only file to {OUT_NEW_ONLY}")

if __name__ == "__main__":
    main()



