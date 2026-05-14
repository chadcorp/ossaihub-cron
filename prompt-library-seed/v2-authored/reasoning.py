"""Reasoning prompts — structured thinking, tree-of-thought, self-consistency, decomposition."""

RECORDS = [
    {
        "slug": "tree-of-thought-decision",
        "title": "Tree-of-Thought Decision Explorer",
        "tldr": "Forces the model to branch out 3 candidate approaches, evaluate each on stated criteria, prune the weakest, and commit to a recommendation — better than single-path reasoning for high-stakes decisions.",
        "category": "reasoning",
        "tags": ["reasoning", "tree-of-thought", "decision-making", "structured-thinking"],
        "best_for_tags": ["architecture-decisions", "strategy", "hard-tradeoffs"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Architecture choice", "example": "‘Should we use Postgres, DynamoDB, or a vector DB for this workload?’ — branch each, evaluate on 5 criteria, prune, commit."},
            {"scenario": "Strategic positioning", "example": "‘Three ways to position the product against the incumbent’ — explore each before picking."},
            {"scenario": "Difficult hiring decision", "example": "‘Three plausible candidates for this Director role’ — branch evaluation across the same criteria."},
            {"scenario": "Algorithmic problem solving", "example": "‘Three approaches to deduplicating 100M records’ — compare on memory, accuracy, latency."},
        ],
        "when_not_to_use": "Skip for trivial decisions (the structure adds overhead that's not worth it). Skip when there's already a clear obvious choice — the model will fabricate alternatives to justify the structure.",
        "full_prompt": """You are a structured-reasoning assistant. The user has a decision to make. You will:

1. Generate THREE candidate approaches (branches). If only two are credible, say so and explain.
2. Evaluate each branch on the user-stated criteria.
3. Prune the weakest branch with a clear reason.
4. Compare the remaining two head-to-head.
5. Commit to ONE recommendation with the rationale.

STRUCTURE

## Decision
Restate the decision in one sentence.

## Criteria
List the 3–6 criteria the user named (or that you've inferred — mark inferred ones with [i]). Weight if specified.

## Branch A
- Description (2–3 sentences)
- How it fares on each criterion (one line each, with concrete reasoning)
- One thing this branch is uniquely good at
- One thing this branch is uniquely bad at

## Branch B
Same shape.

## Branch C
Same shape.

## Pruning
State which branch you're cutting and why. The reason must reference a SPECIFIC criterion, not vague intuition.

## Head-to-head: remaining two
- Where they tie
- Where one clearly beats the other
- What would have to be true for the worse option to actually be better

## Recommendation
ONE branch, with:
- The decision in one sentence
- The single strongest reason
- The biggest risk and how you'd monitor for it

RULES
- Don't invent fake branches just to fit three. If only two are credible, drop to two.
- Don't hedge in the recommendation. Pick one.
- Cite criteria explicitly; reasoning must connect to them.

DECISION
{decision}

CRITERIA AND CONTEXT
{criteria_and_context}

Now reason.""",
        "input_variables": [
            {"name": "decision", "type": "string", "description": "The decision to make", "required": True, "example": "Choose a vector database for our RAG system supporting ~5M docs and 1k QPS"},
            {"name": "criteria_and_context", "type": "string", "description": "Criteria the user cares about and relevant context", "required": True, "example": "Criteria: latency at scale, ops burden, cost, hybrid search support. Context: 3-person team, no dedicated infra eng, AWS-native preferred."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six headed sections covering Decision, Criteria, three Branches, Pruning, Head-to-head, and Recommendation.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at pruning honestly and committing to a recommendation."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally hedges in the recommendation — re-pin ‘pick one.’"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Holds the structure; recommendations sometimes weak — ask for ‘strongest single reason’."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Branches often overlap (3 variants of the same idea); ask for ‘meaningfully distinct branches’."},
        ],
        "variations": [
            {"label": "Self-consistency", "description": "Run the same prompt N times and surface where reasoning agreed.", "prompt_snippet": "Run N=5 times. Then summarize: which branch won most often, where reasoning converged, where it diverged."},
            {"label": "Adversarial branch", "description": "Add a fourth ‘intentionally contrarian’ branch.", "prompt_snippet": "Add: ‘include a fourth branch that's intentionally contrarian — the option a smart skeptic would defend.’"},
            {"label": "With pre-mortem", "description": "Combines pre-mortem on the recommendation.", "prompt_snippet": "Add: ‘after the recommendation, write a 100-word pre-mortem on how this decision goes wrong.’"},
        ],
        "failure_modes": [
            {"symptom": "Three branches are variants of the same idea.", "fix": "Re-pin: ‘branches must be meaningfully distinct — different in approach, not just configuration.’"},
            {"symptom": "Recommendation hedges (‘could go either way’).", "fix": "Add: ‘pick one. If you genuinely can't, say so — but don't hedge if you can.’"},
            {"symptom": "Pruning is vague.", "fix": "Add: ‘pruning reason must cite a specific criterion and the branch's performance on it.’"},
            {"symptom": "Made-up criteria sneak in.", "fix": "Add explicit [i] marking for inferred criteria and ask user to confirm before final reasoning."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["strategic-tradeoff-analyzer", "devils-advocate-pre-mortem", "vendor-comparison-builder"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["tree-of-thought", "structured-reasoning"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How is this different from a generic ‘compare options’ prompt?", "answer": "It forces pruning and a single committed recommendation. Generic compare-prompts produce balanced summaries; this produces a decision."},
            {"question": "What if I really do have only one credible option?", "answer": "Skip this prompt — you don't need branching. Use a pre-mortem on the single option instead."},
            {"question": "Will the recommendation always be right?", "answer": "No — it's a structured second opinion. Validate against context the model can't have (team dynamics, recent failures, contractual constraints)."},
        ],
        "meta_title": "Tree-of-Thought Decision Explorer — Prompt",
        "meta_description": "Branch three approaches, evaluate on stated criteria, prune the weakest, and commit to a recommendation — structured decisions beat single-path reasoning.",
    },
    {
        "slug": "self-consistency-vote",
        "title": "Self-Consistency Voting on Hard Answers",
        "tldr": "Asks the model the same question N independent times, then meta-reasons over the answers — surfaces where reasoning converges (high confidence) vs diverges (the answer is unstable).",
        "category": "reasoning",
        "tags": ["self-consistency", "reasoning", "voting", "uncertainty"],
        "best_for_tags": ["hard-problems", "ambiguous-questions", "answer-stability"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Hard math problem", "example": "Run 5 separate reasoning passes; if 5/5 agree, high confidence. If 3/2 split, surface the disagreement."},
            {"scenario": "Strategic judgment call", "example": "‘Will this product land in this market?’ — run 7 passes, see where reasoning aligns and diverges."},
            {"scenario": "Legal/policy interpretation", "example": "Multiple passes of statutory interpretation, then synthesize where they agree."},
            {"scenario": "Diagnostic reasoning", "example": "Differential diagnosis — multiple reasoning paths from same symptoms."},
        ],
        "when_not_to_use": "Skip for factual lookups (the answer is either right or wrong). Skip when latency or cost matter — this prompt uses N× tokens for one answer.",
        "full_prompt": """You are running a self-consistency check. The user has a hard question.

PROCESS
1. Answer the question {n_runs} times independently. Each pass must reason from scratch — do not reference earlier passes.
2. After all passes, perform a META-ANALYSIS:

   a. Count: how many passes reached each conclusion?
   b. Reasoning agreement: when conclusions agree, do they agree for the SAME reasons or different reasons? (Agreement on the answer but disagreement on why is a yellow flag.)
   c. Disagreement nature: when conclusions disagree, what's the crux? Different facts? Different value-weights? Different domain knowledge?

3. Output the synthesis:

   ## Convergence
   The most common answer + how many passes reached it.

   ## Reasoning fingerprint
   Do passes agree on WHY? Note the dominant reasoning path.

   ## Where reasoning diverged
   Specific crux of disagreement, if any.

   ## Confidence verdict
   - HIGH: same answer, same reasoning, all passes.
   - MODERATE: same answer, different reasoning — answer is right but the rationale is unstable.
   - LOW: split answers OR same answer for unrelated reasons.

   ## Final answer
   Single committed answer if HIGH or MODERATE. If LOW, say "this question is unstable in this model; gather more facts."

QUESTION
{question}

RELEVANT CONTEXT
{context}

Begin the {n_runs} passes now. Number each pass clearly.""",
        "input_variables": [
            {"name": "question", "type": "string", "description": "The hard question", "required": True, "example": "Given quarterly revenue of $4M growing 30% QoQ and 80% gross margin, what's a defensible 12-month forward ARR estimate?"},
            {"name": "n_runs", "type": "integer", "description": "Number of independent reasoning passes", "required": True, "example": "5"},
            {"name": "context", "type": "string", "description": "Background context for the question", "required": False, "example": "B2B SaaS, mid-market, churn rate not yet stable"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "N numbered reasoning passes, then a meta-analysis with convergence, reasoning fingerprint, divergence, confidence, and final answer.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Reasoning passes are genuinely independent; meta-analysis sharp."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; passes occasionally echo earlier ones — emphasize ‘from scratch’."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Holds the structure; meta-analysis sometimes shallow."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Passes drift toward the same answer; useful as smoke test only."},
        ],
        "variations": [
            {"label": "Cross-model voting", "description": "Same question across different models.", "prompt_snippet": "Replace N self-consistency passes with: ‘query 3 different models (Sonnet, 4o, Gemini); synthesize.’ (Requires running prompt against each model and pasting results.)"},
            {"label": "Temperature-only", "description": "Same model, different temperatures.", "prompt_snippet": "Run N=5 at temperatures 0.0, 0.3, 0.7, 1.0, 1.3; flag answers that change with temperature."},
            {"label": "Devil's advocate pass", "description": "One pass argues against the others.", "prompt_snippet": "Add: ‘after N passes, run a final ADVERSARY pass that argues the case AGAINST the convergent answer.’"},
        ],
        "failure_modes": [
            {"symptom": "Passes echo each other (false convergence).", "fix": "Re-pin ‘each pass from scratch’; consider running passes in separate sessions and pasting all answers in for meta-analysis only."},
            {"symptom": "Meta-analysis is just ‘all passes agreed’.", "fix": "Add: ‘meta-analysis must distinguish answer-agreement from reasoning-agreement.’"},
            {"symptom": "Confidence verdict always HIGH.", "fix": "Add: ‘confidence requires same answer + same dominant reasoning path; otherwise MODERATE.’"},
            {"symptom": "Final answer dropped when LOW confidence.", "fix": "Add: ‘even at LOW, surface the answer the most passes reached; just label its instability.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["tree-of-thought-decision", "chain-of-thought"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["self-consistency", "model-confidence"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What's a good N?", "answer": "3 for cheap smoke tests, 5 for serious checks, 7 if cost is fine and the question is critical. More than 7 has diminishing returns."},
            {"question": "Is this the same as ‘chain of thought’?", "answer": "No. Chain of thought = one path with reasoning. Self-consistency = multiple paths + voting. They compose well: use chain-of-thought WITHIN each pass."},
            {"question": "Why care about reasoning agreement vs answer agreement?", "answer": "If the answer is right but the reasoning is unstable, the answer is probably an artifact — change the question slightly and the model breaks. Reasoning agreement is the trustworthier signal."},
        ],
        "meta_title": "Self-Consistency Voting on Hard Answers — Prompt",
        "meta_description": "Run N independent reasoning passes on a hard question; meta-analyze convergence to distinguish stable answers from artifacts of one reasoning path.",
    },
    {
        "slug": "decomposition-into-subgoals",
        "title": "Goal Decomposition Into Falsifiable Subgoals",
        "tldr": "Takes a big fuzzy goal and decomposes it into 5–8 falsifiable subgoals — each measurable, each with the leading indicator that proves or disproves it.",
        "category": "reasoning",
        "tags": ["decomposition", "planning", "goal-setting", "reasoning"],
        "best_for_tags": ["strategy", "okrs", "ambitious-goals"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Yearly product goal", "example": "‘Become the default RAG database for B2B mid-market.’ Decompose into 5–8 falsifiable subgoals with leading indicators."},
            {"scenario": "Research project plan", "example": "‘Show that this approach beats baselines’ → decomposed into 6 subgoals each with a falsifiable check."},
            {"scenario": "Career goal", "example": "‘Become a Staff Engineer in 18 months’ → decomposed into observable, falsifiable steps."},
            {"scenario": "Health goal", "example": "‘Run a marathon in 6 months’ → decomposed into training subgoals with weekly checks."},
        ],
        "when_not_to_use": "Skip for goals that are already concrete (‘ship feature X by date Y’). Use it only when the goal is fuzzy enough that you can't tell yet whether you're making progress.",
        "full_prompt": """You are a strategy decomposer. The user has a big, fuzzy goal. Decompose it into FALSIFIABLE subgoals.

RULES FOR FALSIFIABLE SUBGOALS
1. Each subgoal must have a clear ‘failed / on-track / succeeded’ judgment available within {timeframe}.
2. Each subgoal includes:
   - One-line goal statement (not aspiration — outcome).
   - Measurement: how to know.
   - Leading indicator: what early signal predicts success here?
   - Anti-signal: what observation would prove this subgoal is failing?
   - Owner: who's accountable (role, not name).
   - First action: the FIRST concrete thing someone does this week.

3. 5–8 subgoals. Too few → the parent goal is still fuzzy. Too many → can't focus.
4. Subgoals must be DISTINCT — no two should measure the same underlying thing in different words.
5. End with an ANTI-GOAL section: 3 plausible things the team might pursue that LOOK like progress but actually aren't (vanity metrics, defensive moves, scope sprawl).

INPUT
- Parent goal: {parent_goal}
- Timeframe: {timeframe}
- Team / resources: {resources}

Decompose now.""",
        "input_variables": [
            {"name": "parent_goal", "type": "string", "description": "The big fuzzy goal", "required": True, "example": "Become the default RAG database for B2B mid-market companies"},
            {"name": "timeframe", "type": "string", "description": "Time horizon for the decomposition", "required": True, "example": "12 months"},
            {"name": "resources", "type": "string", "description": "Team and resource context", "required": True, "example": "8-person engineering team, $4M annual budget, no dedicated marketing yet"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "5–8 numbered subgoals each with statement, measurement, leading indicator, anti-signal, owner, first action; ends with anti-goal section.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on the falsifiability constraint; useful anti-goal section."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes subgoals overlap — re-pin distinctness."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Subgoals can be too aspirational (not falsifiable); re-emphasize the criterion."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to write subgoals as activities, not outcomes; needs reminder."},
        ],
        "variations": [
            {"label": "Weekly cadence", "description": "Add a week-by-week check-in cadence.", "prompt_snippet": "Add: ‘for each subgoal, propose the weekly check-in question that surfaces drift fast.’"},
            {"label": "OKR-formatted", "description": "Convert to OKR structure.", "prompt_snippet": "Restructure as: 1 Objective + 3–5 Key Results derived from subgoals. Each KR is a falsifiable subgoal."},
            {"label": "Pre-mortem appended", "description": "End with a pre-mortem on the whole goal.", "prompt_snippet": "After anti-goals, write a 150-word pre-mortem on how the parent goal still fails even if all subgoals succeed."},
        ],
        "failure_modes": [
            {"symptom": "Subgoals are activities, not outcomes (‘write content’ vs ‘publish content that drives 5k qualified visits’).", "fix": "Re-pin: ‘subgoals are outcomes, not actions.’"},
            {"symptom": "Leading indicators are lagging.", "fix": "Add: ‘leading indicator must be observable BEFORE the outcome is known — within first 30% of the timeframe.’"},
            {"symptom": "Anti-goals are clichés (‘don't chase vanity metrics’).", "fix": "Add: ‘anti-goals must be plausible specific moves your team might actually make — name the thing.’"},
            {"symptom": "Owner is ‘the team’.", "fix": "Add: ‘owner is a role, not a group. If two roles share, name both and the integration point.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["okr-quarterly-drafter", "strategic-tradeoff-analyzer", "devils-advocate-pre-mortem"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["falsifiability", "leading-indicator", "okr"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What if no leading indicator exists?", "answer": "Then the subgoal isn't well-formed yet. Either find a leading indicator (even a noisy one) or rewrite the subgoal."},
            {"question": "Should every subgoal be quantitative?", "answer": "Ideally yes — but a qualitative ‘failed / on-track / succeeded’ judgment is okay if the judge is named and the criterion is described."},
            {"question": "How often should we revisit?", "answer": "At the leading-indicator cadence. Monthly for 12-month subgoals; weekly for quarterly ones. Don't wait for the end to learn you were off-track."},
        ],
        "meta_title": "Goal Decomposition Into Falsifiable Subgoals",
        "meta_description": "Decompose a fuzzy goal into 5–8 falsifiable subgoals with leading indicators, anti-signals, and the first action — plus the anti-goals to avoid.",
    },
    {
        "slug": "first-principles-rebuilder",
        "title": "First-Principles Rebuilder",
        "tldr": "Strips a complex topic to its first principles, then rebuilds the standard explanation — surfaces which parts of the conventional wisdom are load-bearing and which are vestigial.",
        "category": "reasoning",
        "tags": ["first-principles", "reasoning", "deconstruction", "analysis"],
        "best_for_tags": ["learning", "innovation", "strategy"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Learning a new field", "example": "‘What's actually true about how transformers work, stripping the metaphors?’"},
            {"scenario": "Challenging an industry assumption", "example": "‘Why do SaaS companies all price per seat? What's load-bearing here?’"},
            {"scenario": "Innovation framing", "example": "‘What does a CRM HAVE to do? What's vestigial that we could drop?’"},
            {"scenario": "Re-evaluating a personal belief", "example": "‘Why do I think product-led growth is right for this business?’"},
        ],
        "when_not_to_use": "Skip for topics where conventional wisdom is well-tested and the cost of deviating is high (medicine, structural engineering). First-principles thinking in these domains needs domain expertise, not just framework.",
        "full_prompt": """You are a first-principles rebuilder. The user has a topic where ‘everyone knows’ how it works. You'll deconstruct.

PROCESS

## Step 1: State the conventional wisdom
Summarize the dominant explanation or practice in 3–5 sentences. Use the field's actual vocabulary.

## Step 2: Strip to first principles
Identify the underlying truths that the conventional wisdom is built ON. These should be:
- Facts that can't be argued (physics, math, fundamental constraints).
- Trade-offs that genuinely exist (you can't have X and Y simultaneously).
- Goals that are real (what the system is trying to accomplish).

5–10 principles. Number them.

## Step 3: Rebuild the conventional wisdom from those principles
Show, step by step, how a reasonable person starting from the principles would arrive at the conventional wisdom. Use specifically the principles you listed.

## Step 4: Identify the load-bearing parts
Which of the conventional wisdom's elements follow NECESSARILY from the principles? These are the load-bearing parts — change these and the whole thing breaks.

## Step 5: Identify the vestigial parts
Which elements of the conventional wisdom are habits, conventions, or path-dependence — they could be different without violating the principles?

## Step 6: Where could it actually differ?
Given the vestigial parts, what's a meaningfully different design that still satisfies the principles?

TOPIC
{topic}

GROUND RULES
- Don't be contrarian for sport. If the conventional wisdom IS load-bearing all the way down, say so.
- Cite the principle each conclusion rests on. Vague rebuilding ("based on user needs...") is not first-principles.
- When you spot a vestige, explain how it became that way (path-dependence, historical constraint, etc.).

Now rebuild.""",
        "input_variables": [
            {"name": "topic", "type": "string", "description": "Concept, practice, or system to deconstruct", "required": True, "example": "Why SaaS companies price per seat"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six numbered steps: conventional wisdom, principles, rebuild, load-bearing, vestigial, and where it could differ.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Honest about what's actually load-bearing; doesn't manufacture contrarian takes."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally over-claims something is vestigial — sanity-check by domain experts."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Strong on stating principles; weaker on the path-dependence analysis."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to be contrarian for sport; constrain explicitly."},
        ],
        "variations": [
            {"label": "Domain-cross-pollination", "description": "Borrow principles from another domain.", "prompt_snippet": "Add Step 7: ‘what principle from another domain ({other_domain}) might also apply here? How would the system look if it did?’"},
            {"label": "Adversarial expert", "description": "Defend the conventional wisdom.", "prompt_snippet": "After Step 6, write a 200-word defense of the conventional wisdom from a domain expert who thinks the rebuild is naive."},
            {"label": "Just principles", "description": "Drop the rebuild; output principles only.", "prompt_snippet": "Run only Steps 1 and 2."},
        ],
        "failure_modes": [
            {"symptom": "‘Principles’ are still high-level assumptions, not bedrock.", "fix": "Re-pin: ‘principles must be facts you can't argue against, or genuine trade-offs that exist.’"},
            {"symptom": "Vestigial-vs-load-bearing call is wrong.", "fix": "Add: ‘when calling something vestigial, propose the specific alternative and show it satisfies all principles.’"},
            {"symptom": "Contrarian for the sake of it.", "fix": "Add: ‘if conventional wisdom IS load-bearing, say so. Validating is a valid conclusion.’"},
            {"symptom": "Path-dependence explanations are speculative.", "fix": "Add: ‘when explaining how a vestige formed, name the historical moment or constraint that anchored it.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["devils-advocate-pre-mortem", "strategic-tradeoff-analyzer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["first-principles", "path-dependence"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is this the same as ‘think different’?", "answer": "No. ‘Think different’ assumes the conventional wisdom is wrong. This prompt explicitly preserves conventional wisdom when it's load-bearing — the point is to know WHICH parts are load-bearing."},
            {"question": "How is this useful in practice?", "answer": "When you're about to make a change in a complex system — knowing which conventions are load-bearing tells you where you can innovate safely vs where you'll cause a cascade."},
            {"question": "Will it work on technical topics?", "answer": "Yes — and it's often most valuable there. Physical and mathematical constraints make ‘bedrock principles’ easier to identify."},
        ],
        "meta_title": "First-Principles Rebuilder — Prompt",
        "meta_description": "Strip a topic to bedrock principles, then rebuild the conventional wisdom — surface what's load-bearing and what's vestigial path-dependence.",
    },
    {
        "slug": "analogical-reasoning-cross-domain",
        "title": "Cross-Domain Analogical Reasoning",
        "tldr": "Finds 3 deep analogies from other domains for a given problem, surfaces what each domain SOLVED that the user's domain hasn't yet — and which solution patterns might transfer.",
        "category": "reasoning",
        "tags": ["analogy", "reasoning", "cross-domain", "innovation"],
        "best_for_tags": ["product-design", "research", "strategy"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Product design challenge", "example": "‘How do we onboard users to a complex tool?’ → analogies from cooking school, flight training, video games."},
            {"scenario": "Engineering pattern transfer", "example": "‘How do we handle backpressure in our pipeline?’ → analogies from traffic systems, hydraulics, supply chains."},
            {"scenario": "Strategic positioning", "example": "‘How do we differentiate as a late entrant in a crowded market?’ → analogies from automotive history (Tesla, Toyota), beverage (RedBull)."},
            {"scenario": "Research method transfer", "example": "‘Statistical methods from epidemiology applied to user research.’"},
        ],
        "when_not_to_use": "Skip when the problem is novel enough that no domain has solved it. Skip when you need correctness more than creativity — analogies are great for hypothesis generation, weak for proof.",
        "full_prompt": """You are a cross-domain analogical reasoner. The user has a problem. You'll find three deep analogies from other domains.

PROCESS

## Step 1: Restate the problem at its core
Strip the problem to its underlying structure (3–5 sentences). What is it FUNDAMENTALLY about? (E.g., ‘onboarding a user to a complex tool’ → ‘moving someone from no-context to productive-context with limited time and attention’.)

## Step 2: Find three analogies
Three problems from THREE DIFFERENT DOMAINS that share this underlying structure. For each:

### Analogy {1, 2, 3}: {domain} — {problem from that domain}

- Why it's analogous: 2–3 sentences mapping the structural similarity.
- How {domain} has solved it: real solutions used in that domain (cite specific methods, traditions, tools).
- What's clever about their solution: the non-obvious move.
- What's domain-specific that wouldn't transfer: be honest about limits.

## Step 3: Synthesis — solution patterns that might transfer
Looking across all three analogies, what 2–3 SOLUTION PATTERNS show up consistently? List them. For each, propose how it might apply to the user's actual problem.

## Step 4: Tests
For each transferred pattern, propose the SMALLEST experiment that would falsify whether the analogy holds for the user's context.

RULES
- Analogies from three DIFFERENT domains — not three flavors of the same domain.
- Cite specific solutions used in those domains (named methods, real practices). Vague analogies are useless.
- Be honest about transfer limits. Half the value of cross-domain analogy is knowing what DOESN'T transfer.

PROBLEM
{problem}

CONTEXT (user's domain, constraints)
{context}

Now reason analogically.""",
        "input_variables": [
            {"name": "problem", "type": "string", "description": "The problem to find analogies for", "required": True, "example": "How do we onboard users to our complex AI analytics tool — they currently churn in the first session."},
            {"name": "context", "type": "string", "description": "Domain and constraints", "required": True, "example": "B2B SaaS, sold to data analysts, product is dense, average session length 4 minutes"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Four steps: restated problem, three analogies in different domains, synthesis with transferable patterns, and falsifying tests.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Surfaces unexpected but apt analogies; honest about transfer limits."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes picks three analogies that are too similar — re-pin ‘different domains’."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Tends toward science/engineering analogies; ask explicitly for art/culture/history options."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Surface-level analogies; useful as a brainstorm input but verify the deep structure."},
        ],
        "variations": [
            {"label": "Single deep analogy", "description": "One analogy, much deeper.", "prompt_snippet": "Replace three-analogy structure with: ‘find ONE analogy and go 5x deeper on what transfers and what doesn't.’"},
            {"label": "Time-shift analogy", "description": "Same domain, different era.", "prompt_snippet": "Find analogies from the same domain at a different time (e.g., 1990s software for today's AI startups)."},
            {"label": "Failed analogy", "description": "Include one that LOOKS analogous but isn't.", "prompt_snippet": "Add a fourth ‘false analogy’ section that looks superficially similar but breaks at the structural level — explain why."},
        ],
        "failure_modes": [
            {"symptom": "Three analogies from same domain (e.g., three sports).", "fix": "Re-pin: ‘three different domains — science/engineering/business/art/biology/history/sport.’"},
            {"symptom": "Analogies are clichés (‘like a chef in a kitchen’).", "fix": "Add: ‘analogies must be specific enough to cite real practitioners/methods/dates.’"},
            {"symptom": "Transfer claims are too confident.", "fix": "Force the ‘doesn't transfer’ section to be at least 2 sentences for each analogy."},
            {"symptom": "Synthesis patterns are generic.", "fix": "Add: ‘patterns must be specific moves the user could try in 2 weeks, not abstract principles.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["first-principles-rebuilder", "tree-of-thought-decision"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["analogical-reasoning", "cross-domain-transfer"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Aren't analogies just storytelling?", "answer": "Surface analogies are. DEEP analogies — where the underlying structure matches — generate testable hypotheses. The ‘falsifying test’ step turns analogies into experiments."},
            {"question": "How do I know if an analogy is deep?", "answer": "Test: if you swap the surface details for new ones, does the explanation still work? If yes, the structure is shared — that's deep."},
            {"question": "Can the model make up analogies?", "answer": "It can — and sometimes does, especially with rare domains. The mitigation is the requirement to cite specific named methods or practitioners in each domain; if the model can't, the analogy is probably hallucinated."},
        ],
        "meta_title": "Cross-Domain Analogical Reasoning — Prompt",
        "meta_description": "Find three analogies from different domains for your problem — extract transferable solution patterns and design experiments to test which one applies.",
    },
]
