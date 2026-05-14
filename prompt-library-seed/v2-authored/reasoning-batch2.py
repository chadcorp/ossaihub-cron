"""Reasoning prompts — batch 2."""

RECORDS = [
    {
        "slug": "fermi-estimation",
        "title": "Fermi Estimation From Sparse Data",
        "tldr": "Estimate quantities via Fermi decomposition — break the unknown into knowable factors, surface assumptions, produce a calibrated range, not a single point.",
        "category": "reasoning",
        "tags": ["fermi-estimation", "reasoning", "decomposition", "uncertainty"],
        "best_for_tags": ["product-strategy", "sizing", "investment-decisions"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Market sizing for a feature", "example": "‘How many enterprises would buy this?’ → decomposed estimate with 5 assumptions explicit."},
            {"scenario": "Infrastructure capacity", "example": "‘How many GPUs do we need for serving 50M users?’ — Fermi from traffic patterns."},
            {"scenario": "Revenue impact projection", "example": "‘If we launched this, what's expected MRR uplift?’ → decomposed with ranges."},
            {"scenario": "Interview prep", "example": "Mock cases: ‘How many tennis balls fit in a 747?’ practice rigor."},
        ],
        "when_not_to_use": "Skip when actual data exists (use it). Skip for one-of-a-kind situations where decomposition introduces more uncertainty than it removes. Skip when stakeholders demand a single point estimate; Fermi is honest about ranges.",
        "full_prompt": """You are a Fermi-estimation expert. The user has a quantity to estimate. Decompose it and produce a calibrated estimate.

INPUT
- The quantity to estimate: {quantity}
- Available context / data: {available_data}
- The decision this estimate informs: {decision_context}

OUTPUT

## 1. Decomposition
Express the unknown as a PRODUCT of factors, each more knowable than the whole.

Example:
  Annual coffee shop revenue =
    (cafes in city) × (avg revenue per cafe) × 1 year

  ALL of these factors are individually easier to estimate than ‘annual coffee shop revenue’ directly.

Choose your decomposition; aim for 3-7 factors. Too few = unhelpfully coarse. Too many = false precision.

## 2. Estimate each factor
For each factor:
- Best guess (geometric mean of plausible range)
- Low estimate (10th percentile — ‘it's unlikely to be lower than this’)
- High estimate (90th percentile)
- Source / reasoning (cite if from data; mark as gut if not)

## 3. Combine
- Best estimate: product of factor best-guesses
- Range: product of lows × product of highs (rough; or use log-normal math for sophistication)

## 4. Sensitivity analysis
Which factor's range dominates the uncertainty? If one factor swings the result by 10x and others by 2x, it's the bottleneck factor — that's where to invest in better data.

## 5. Sanity checks
- Compare against any related known number ("US GDP is ~$25T; my estimate must be smaller").
- Compare against bounds ("there are only 8B people on Earth; my estimate must be lower").
- Compare against analogous quantities ("similar product class X did roughly Y").

## 6. The honest answer
- Best estimate (single number with appropriate sig figs — usually 1-2)
- Range (with confidence level)
- One-line summary the user can quote
- Two-line caveat about what you DON'T know

## 7. How to halve the uncertainty
What ONE piece of data would most reduce the range? (Often the sensitivity-dominant factor.)

RULES
- Decompose into KNOWABLE factors. ‘Adoption rate’ isn't knowable; ‘users who saw feature X in past 30 days’ might be.
- Round aggressively — false precision is worse than acknowledged uncertainty.
- When using gut estimates, label them explicitly.
- Don't be afraid of wide ranges; ‘$1M-$100M’ honest beats ‘$8M’ pretend-precise.

QUANTITY
{quantity}

Begin.""",
        "input_variables": [
            {"name": "quantity", "type": "string", "description": "What to estimate", "required": True, "example": "Annual market size for AI-powered legal research tools in the US"},
            {"name": "available_data", "type": "string", "description": "Known data / context", "required": True, "example": "There are ~1.3M lawyers in the US. Top legal-tech vendors charge $150-500/seat/month. Adoption of new legal tech tends to be 5-15% in 2-3 years."},
            {"name": "decision_context", "type": "string", "description": "What decision uses this estimate", "required": True, "example": "Whether to invest $5M Series A in building this product"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: decomposition, factor-by-factor estimates, combination, sensitivity, sanity checks, honest answer, how-to-halve-uncertainty.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong decompositions; honest about uncertainty."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can be over-confident — re-pin range honesty."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; sensitivity analysis sometimes shallow."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Decomposes but ranges can be too narrow."},
        ],
        "variations": [
            {"label": "Two-by-two scenario", "description": "Best/worst case + base case.", "prompt_snippet": "Replace ranges with: ‘pessimistic / base / optimistic scenarios; each is a full decomposition.’ Surface 3 numbers."},
            {"label": "Log-normal combination", "description": "More rigorous range math.", "prompt_snippet": "Add: ‘compute range using log-normal: ln(estimate) = sum of ln(factors); range = exp(ln_best ± 1.65·sqrt(sum of factor variances)).’"},
            {"label": "Triangulation", "description": "Multiple decompositions for cross-check.", "prompt_snippet": "Add: ‘also produce a SECOND decomposition using different factors; if estimates diverge significantly, surface why.’"},
        ],
        "failure_modes": [
            {"symptom": "Decomposition reuses the unknown.", "fix": "Re-pin: ‘each factor must be more knowable than the whole.’ Reject decompositions where ‘adoption rate’ is a factor without further decomposition."},
            {"symptom": "Ranges artificially narrow.", "fix": "Add: ‘low estimate should be roughly 10% likely; high estimate roughly 90%. If your range covers only ‘probable’ values, widen it.’"},
            {"symptom": "Sanity checks omitted.", "fix": "Force: ‘at least 2 sanity checks comparing to known bounds or analogs.’"},
            {"symptom": "False precision (estimate to 3 sig figs).", "fix": "Add: ‘round to 1-2 significant figures; precision should match confidence.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["market-sizing-fermi", "decomposition-into-subgoals"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["fermi-estimation", "decomposition"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Aren't Fermi estimates inaccurate?", "answer": "They're honest — explicitly uncertain rather than falsely precise. A well-decomposed Fermi estimate with a 3x range is more useful for decisions than a single number that's secretly a guess."},
            {"question": "When are they NOT useful?", "answer": "When real data exists. Don't Fermi-estimate ‘our company's MRR’ when you can pull the actual number. Use Fermi for forward-looking or external questions."},
            {"question": "How do I get better at this?", "answer": "Practice on knowables (‘how many cars on the highway right now?’) then check actuals. Track your range hit rate — if 90% confidence intervals miss 50% of the time, you're overconfident."},
        ],
        "meta_title": "Fermi Estimation From Sparse Data — Prompt",
        "meta_description": "Decompose unknowns into knowable factors, produce calibrated range estimates, identify dominant uncertainty. Honest sizing, not false precision.",
    },
    {
        "slug": "second-order-thinking",
        "title": "Second-Order Thinking Probe",
        "tldr": "Pushes the user past first-order analysis (immediate effects) into second-order (consequences of the consequences) — for strategic decisions where the obvious answer is wrong because everyone else thought of it first.",
        "category": "reasoning",
        "tags": ["second-order", "strategy", "decision-making", "reasoning"],
        "best_for_tags": ["strategic-decisions", "market-thinking", "competitive-strategy"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Pricing change decision", "example": "First-order: ‘raise price 30% → revenue up 25%.’ Second-order: ‘competitors notice; price war; net revenue down 15% in 18 months.’"},
            {"scenario": "Hiring strategy", "example": "First: ‘aggressive hiring will speed shipping.’ Second: ‘team coordination overhead; ship velocity per engineer falls; culture dilution.’"},
            {"scenario": "Feature launch impact", "example": "First: ‘users will love feature X.’ Second: ‘power users will use it to spam; cost spikes.’"},
            {"scenario": "Investment thesis", "example": "First: ‘this category is hot.’ Second: ‘that's why a hundred competitors entered; margins will compress.’"},
        ],
        "when_not_to_use": "Skip for execution decisions (just do them). Skip when the first-order analysis is already specific enough — over-thinking is its own failure mode.",
        "full_prompt": """You are a strategic thinking coach. The user proposes a decision based on first-order effects. You'll push to second-order.

INPUT
- The decision being considered: {decision}
- The user's first-order analysis (immediate expected effects): {first_order}
- Time horizon: {horizon}
- Domain (helps you draw on analogous patterns): {domain}

OUTPUT

## 1. Acknowledge the first-order
Restate the user's first-order analysis. Note where it seems right (don't strawman).

## 2. Second-order chain
For 3-5 effects, ask ‘and then what?’

### Effect chain N
- First-order: <user's claim or implied>
- Second-order: what does this CAUSE to happen?
- Third-order (if relevant): what does THAT then cause?
- Specific actors involved (not ‘the market’; specific stakeholder groups)
- Timing: this kicks in around <when>

## 3. Counter-moves and reactions
The decision creates incentives for others. Who responds and how?
- Competitors: how does this change their best move?
- Customers (different segments): different reactions, named
- Suppliers / regulators: any structural shifts?
- Internal team: morale, incentives, focus changes

## 4. ‘Why doesn't everyone already do this?’
The Buffett question. If second-order analysis says this is great, ask:
- Has someone tried this before? What happened?
- What's the actual barrier — capital, knowledge, time, or just no one's thought of it?
- If the answer is ‘no one's thought of it,’ be skeptical. Often the second-order is why it's avoided.

## 5. Reframe
Given the second-order analysis, is the decision still right?
- Yes — but with adjusted expectations or sequencing
- Conditionally — with prerequisites met
- Probably not — second-order dominates
- Same direction but different approach to capture upside while mitigating second-order

## 6. Leading indicators of second-order kicking in
Specific things to watch for that would confirm or refute the second-order chain.

RULES
- Second-order isn't second-guessing. The first-order may still be right; this stresses-tests it.
- Specific actors over abstractions. ‘Pro-tier customers’ beats ‘users.’
- Timing matters. Second-order in 6 months is different from second-order in 5 years.
- When second-order is ambiguous, surface that — don't manufacture confident chains.

DECISION
{decision}

FIRST-ORDER ANALYSIS
{first_order}

Begin.""",
        "input_variables": [
            {"name": "decision", "type": "string", "description": "The decision being considered", "required": True, "example": "Raise our annual plan price from $99 to $129"},
            {"name": "first_order", "type": "string", "description": "The user's immediate analysis", "required": True, "example": "Most existing customers will absorb the increase; revenue per customer rises 30%; some marginal customers churn but net positive."},
            {"name": "horizon", "type": "string", "description": "Time frame", "required": True, "example": "12-24 months"},
            {"name": "domain", "type": "string", "description": "Industry/context", "required": False, "example": "B2B SaaS, mid-market, competitive segment"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: acknowledge first-order, effect chains, counter-moves, ‘why doesn't everyone do this?’, reframe, leading indicators.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on competitive reaction analysis; doesn't manufacture chains."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally projects too far — re-pin specificity."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; ‘why doesn't everyone do this’ can be soft."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Surface-level second-order; needs explicit ‘specific actors’ direction."},
        ],
        "variations": [
            {"label": "Adversarial expert", "description": "Steelmanned opposition.", "prompt_snippet": "Add: ‘also: write a 200-word critique from a thoughtful skeptic; what would they say is the real first-order miss?’"},
            {"label": "Pre-mortem variant", "description": "Combine with imagining failure.", "prompt_snippet": "Add: ‘then imagine this decision failed; write 3 most likely causes referencing the second-order chains.’"},
            {"label": "Game-theoretic", "description": "More formal multi-actor reasoning.", "prompt_snippet": "Add: ‘where multiple actors interact, sketch payoff matrices or sequential-game trees for the key interactions.’"},
        ],
        "failure_modes": [
            {"symptom": "Second-order chains are vague (‘the market reacts’).", "fix": "Re-pin: ‘specific actors, specific reactions, specific timing.’"},
            {"symptom": "Strawmans the first-order.", "fix": "Add: ‘acknowledge what the first-order gets right before challenging it.’"},
            {"symptom": "‘Why doesn't everyone do this?’ skipped.", "fix": "Force: ‘if you don't address this question, you've assumed the second-order doesn't matter without evidence.’"},
            {"symptom": "Conclusion is ‘yes, do it’ without modification.", "fix": "Add: ‘even a ‘proceed’ conclusion should specify what the second-order changes about HOW to proceed.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["devils-advocate-pre-mortem", "first-principles-rebuilder", "strategic-tradeoff-analyzer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["second-order-thinking", "counter-positioning"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "When is second-order analysis worth the time?", "answer": "When the decision is large, hard to reverse, or sets precedent. Daily ops decisions: skip. Pricing changes, major hires, market entry: essential."},
            {"question": "Doesn't this lead to analysis paralysis?", "answer": "Cap it: max 3 levels deep. The point is to surface the most important second-order, not to map every branch."},
            {"question": "What if my industry is too unique for analogies?", "answer": "Few industries are that unique. Look at adjacent markets that have gone through similar transitions; you'll find precedent."},
        ],
        "meta_title": "Second-Order Thinking Probe — Prompt",
        "meta_description": "Push past first-order analysis to second-order consequences: specific actors, timing, counter-moves, and the ‘why doesn't everyone do this’ check.",
    },
]
