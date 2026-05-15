"""Reasoning — batch 3."""

RECORDS = [
    {
        "slug": "argument-steelman-then-counter",
        "title": "Argument Steelman, Then Counter",
        "tldr": "Takes a position, builds the strongest STEELMAN version another rational person could hold, then constructs the counter-argument — forcing intellectual honesty before disagreement.",
        "category": "reasoning",
        "tags": ["debate", "epistemics", "argumentation", "steelman"],
        "best_for_tags": ["analysts", "writers", "leaders"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Internal policy debate", "example": "Team disagrees on a hiring policy — steelman both sides before deciding."},
            {"scenario": "Op-ed prep", "example": "Writer's piece will be attacked — steelman the attack to anticipate."},
            {"scenario": "Negotiation prep", "example": "Steelman the other side's strongest version to avoid weak-arg traps."},
            {"scenario": "PhD defense prep", "example": "Anticipate the strongest committee challenges by steelmanning."},
        ],
        "when_not_to_use": "Skip when the position is genuinely indefensible (factual / ethical absolutes). Don't use it as cover for false-balance on settled questions.",
        "full_prompt": """You are a steelman-then-counter analyst. Build the strongest version of a position another rational person could hold, then construct the strongest counter.

INPUT
- The position: {position}
- Domain / context: {context}
- Audience: {audience}                 (who's hearing this argument)
- Your own current view: {my_view}     (so model knows where you're coming from)
- Stakes: {stakes}                     (decision being made / what changes if argument wins)

OUTPUT

## 1. The position, in its own words
Restate the position so its strongest advocates would accept the restatement.
- Use their VOCABULARY (not your translations).
- Name the IMPLICIT premise (often more controversial than the explicit claim).

If you can't restate it without distortion, STOP. The position isn't well-defined enough to argue against.

## 2. The steelman
The strongest version of this argument. Construct 3-4 supporting pillars:
- **Premise:** what they're assuming and WHY that assumption is reasonable.
- **Evidence:** what real-world data / studies / cases support it. Cite specifics.
- **Mechanism:** the causal / logical chain from premise to conclusion.
- **Counter-pre-rebut:** how the steelman ANTICIPATES and answers the obvious objection.

A good steelman is one a steelman-advocate would ENDORSE as a fair version of their argument. Pass that test.

## 3. The strongest counter
Now attack the steelman — at its STRONGEST point, not its weakest.

- **Where the steelman's strongest pillar fails:** specific premise / evidence / mechanism critique.
- **What the steelman over-claims:** scope it doesn't actually support.
- **Better-fitting alternative explanation:** what fits the data better.
- **Predictive failure:** what should happen under the steelman that doesn't.

Don't strawman. The counter is real argumentation, not name-calling.

## 4. Where the disagreement actually lives
Most arguments aren't about the explicit claim — they're about an underlying ASSUMPTION.
- Name the load-bearing assumption both sides are disagreeing about.
- Is this an empirical disagreement (could be resolved by data)?
- A values disagreement (different priorities)?
- A definitional disagreement (using same word, different meanings)?

## 5. The 'change my mind' test
For BOTH sides:
- What evidence would update the steelman side toward the counter?
- What evidence would update the counter side toward the steelman?

If neither side has a clear answer, this is values-based not evidence-based. Flag.

## 6. Honest verdict
After working through the above:
- Which side does the actual evidence currently support more?
- Where's the legitimate residual uncertainty?
- Where does {my_view} need updating, if anywhere?

The verdict can be 'steelman wins on evidence', 'counter wins', 'genuine tie', or 'wrong question.'

CRITICAL RULES
- The steelman MUST be one its advocates would endorse. If they wouldn't, you're strawmanning.
- The counter attacks the STRONGEST point, not the weakest.
- The 'change my mind' test names CONCRETE evidence, not abstract conditions.
- Honest verdict accepts 'counter wins' or 'I was wrong' as valid outcomes.

POSITION
{position}

Begin.""",
        "input_variables": [
            {"name": "position", "type": "string", "description": "Position to steelman", "required": True, "example": "We should ban smartphone use by under-16s in schools entirely."},
            {"name": "context", "type": "string", "description": "Domain / context", "required": True, "example": "Education-policy debate at school district level"},
            {"name": "audience", "type": "string", "description": "Who hears the argument", "required": True, "example": "School board, parent group, teachers union"},
            {"name": "my_view", "type": "string", "description": "Your current view", "required": True, "example": "I lean toward 'restrict in classrooms but not all-day ban' but feel uncertain."},
            {"name": "stakes", "type": "string", "description": "What changes if argument wins", "required": True, "example": "District-wide policy change; affects 12,000 students; vote in 6 weeks."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: position-restated, 4-pillar steelman, strongest counter, where the real disagreement lives, change-my-mind tests for both sides, honest verdict.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at steelman quality + willingness to render honest verdicts."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; sometimes false-balances when verdict should be clear — re-pin honest-verdict rule."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; can miss the 'load-bearing assumption' in section 4."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Steelman is workable; counter is thinner. Use for first-pass drafts."},
        ],
        "variations": [
            {"label": "Three-way", "description": "Compare 3 positions, not 2.", "prompt_snippet": "Replace 'position vs counter' with 3 distinct positions. Steelman each, identify the assumptions each rejects from the others."},
            {"label": "Time-traveler", "description": "Apply steelman+counter to past decisions.", "prompt_snippet": "Apply to a historical decision; steelman the path NOT taken and counter the path that WAS taken. Used for post-mortems."},
            {"label": "Internal vs external", "description": "Steelman an internal vs external critique.", "prompt_snippet": "Steelman an INTERNAL critic (someone inside the system) vs EXTERNAL critic (outside expert). Surface where the institution defends against external but not internal challenge."},
        ],
        "failure_modes": [
            {"symptom": "Strawmans the position.", "fix": "Re-pin: 'steelman must pass the endorsement test — if the position's advocates would object, you're strawmanning. Re-write with their vocabulary.'"},
            {"symptom": "Attacks the weakest point.", "fix": "Force: 'counter targets the STRONGEST pillar from section 2, not the easiest.'"},
            {"symptom": "False-balance verdict.", "fix": "Re-pin: 'honest verdict accepts \"counter wins\" or \"steelman wins\". Genuine tie only when evidence is actually split.'"},
            {"symptom": "Generic 'change my mind' criteria.", "fix": "Require: 'specific evidence type, source, design. Not \"more research\" — name the study that would update you.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["fermi-estimation", "root-cause-five-whys", "evidence-quality-scorer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["steelman", "epistemics"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is this just rhetoric?", "answer": "No — done right, it changes minds. Most arguments fail because each side caricatures the other. Real steelman + real counter is how disagreements get productive."},
            {"question": "When should I NOT steelman?", "answer": "For positions that are factually false or ethically beyond-pale. Steelmanning vaccine denial or holocaust denial gives false equivalence. Reserve for genuine disagreements where smart people differ."},
            {"question": "What if I can't steelman?", "answer": "Read more from the position's advocates in their own words. If you can only describe the position in YOUR terms, you don't yet understand it well enough to disagree with it."},
            {"question": "Won't this lead to fence-sitting?", "answer": "Only if you stop at section 5. The honest verdict in section 6 is required — you take a position. Steelmanning makes that position better-grounded, not weaker."},
        ],
        "meta_title": "Steelman Then Counter — Reasoning Prompt",
        "meta_description": "Build the strongest version of a position another rational person could hold, then attack it at its strongest point. With honest verdict.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "base-rate-correction-check",
        "title": "Base-Rate Correction Check",
        "tldr": "Catches base-rate-neglect in arguments: surfaces the actual base rate, the conditional probability being conflated, and the correct Bayesian conclusion — for medical, legal, hiring, and risk reasoning.",
        "category": "reasoning",
        "tags": ["bayes", "base-rate", "probability", "epistemics"],
        "best_for_tags": ["analysts", "researchers", "policy"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Medical test result interpretation", "example": "Positive screen for rare condition — true vs false positive."},
            {"scenario": "Hiring 'success pattern' claims", "example": "All 5 top hires went to Ivy schools → does that justify Ivy bias?"},
            {"scenario": "Crime / behavior risk-flagging", "example": "Algorithm flags X% of group; is that signal or just base rate of population?"},
            {"scenario": "Investment / startup pattern matching", "example": "Founders matching 'Stanford CS' have X% success — is that signal or base rate?"},
        ],
        "when_not_to_use": "Skip when there's no probabilistic claim — pure deductive arguments don't need this. Skip when the base rate is genuinely unknowable.",
        "full_prompt": """You are a base-rate inspector. Find the probabilistic claim, surface the relevant base rate, do the Bayesian correction.

INPUT
- The claim or argument: {claim}
- Domain (medicine / hiring / criminal-justice / investing / education / other): {domain}
- Population being talked about: {population}
- Evidence cited (test result, observation, pattern): {evidence}

OUTPUT

## 1. The probabilistic claim
Restate the argument in probabilistic form:
- Probability of (something) given (some evidence) = ?
- What's being implicitly claimed.

If the argument isn't probabilistic at all, STOP and tell the user.

## 2. The base rate
What's the base rate of the thing being claimed, in {population}?
- Cite source (study, official data, plausible estimate).
- If base rate is unknown, give a confidence interval.

This is the BASELINE probability before any evidence.

## 3. The conditional probabilities
- **Sensitivity:** P(evidence | thing-is-true)
- **Specificity:** P(no-evidence | thing-is-false)
- **False positive rate:** P(evidence | thing-is-false) = 1 - specificity.
- **False negative rate:** P(no-evidence | thing-is-true) = 1 - sensitivity.

Source these from study data when possible.

## 4. The Bayesian correction
Apply Bayes:
- P(thing-is-true | evidence) = (sensitivity × base rate) / [(sensitivity × base rate) + (false-positive rate × (1 - base rate))]

Walk through with numbers:
- Base rate: ___
- Sensitivity: ___
- Specificity: ___
- Posterior probability: ___

## 5. The bias surfaced
- Original argument implicitly assumed posterior ≈ sensitivity (e.g., "test is 95% accurate, so 95% chance you have it").
- Correct posterior accounting for base rate: ___
- Difference: ___ (often dramatic for rare conditions or weak evidence).

## 6. The 'when would this matter' check
For what range of base rates does this argument hold?
- "If base rate of X in this population is >30%, the original argument is roughly correct."
- "If base rate is <5%, the original argument overstates by >50%."

This lets the reader decide whether base-rate neglect matters here.

## 7. Decision implications
- If acting on the argument, what's the correct posterior to use?
- What's the cost of acting on the WRONG posterior?
- Where should additional confirmatory evidence be sought?

CRITICAL RULES
- Walk through numbers EXPLICITLY. Don't skip arithmetic — that's where intuition fails.
- Base rate sourced or interval-estimated. Don't make up numbers.
- 'When would this matter' bracket shows where base rate flips the argument.
- Decision implications connect the math to real-world action.

CLAIM
{claim}

EVIDENCE
{evidence}

Begin.""",
        "input_variables": [
            {"name": "claim", "type": "string", "description": "Claim being made", "required": True, "example": "Half our top performers attended top-tier universities, so we should prioritize candidates from top schools."},
            {"name": "domain", "type": "string", "description": "Domain", "required": True, "example": "Tech hiring — software engineering"},
            {"name": "population", "type": "string", "description": "Population", "required": True, "example": "Candidates applying to senior SWE roles in our pipeline"},
            {"name": "evidence", "type": "string", "description": "Evidence", "required": True, "example": "5 of top 10 performers from top-tier universities."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: probabilistic claim restate, base rate with source, conditional probabilities (sens/spec/FPR/FNR), Bayesian correction with numbers, bias surfaced, 'when would this matter' range, decision implications.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong arithmetic + honest about base-rate uncertainty."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; will hallucinate specific numbers if you don't pin sourcing."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; sometimes vague on 'when would this matter' brackets."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Arithmetic accurate; weaker on nuanced bias-surfacing."},
        ],
        "variations": [
            {"label": "Frequency-format", "description": "Use natural frequencies, not probabilities.", "prompt_snippet": "Convert all probabilities to 'X out of 10,000 people' format. Gigerenzer-style — easier to communicate."},
            {"label": "Multi-test", "description": "Compute updated posterior after multiple independent tests.", "prompt_snippet": "Run Bayesian update for SEQUENCE of independent evidence (each test result updates the prior). Show how posterior shifts with each."},
            {"label": "False-positive cost-benefit", "description": "Compute expected cost of acting.", "prompt_snippet": "Add: 'compute expected cost of acting on positive result given posterior, vs expected cost of NOT acting. Show the breakeven base rate.'"},
        ],
        "failure_modes": [
            {"symptom": "Hallucinates base rates.", "fix": "Re-pin: 'base rate MUST be sourced OR given as interval estimate with reasoning. No invented decimals.'"},
            {"symptom": "Skips arithmetic.", "fix": "Force: 'show the numbers. Don't say \"applying Bayes\" — apply Bayes with the specific values.'"},
            {"symptom": "Vague 'matters when base rate is low' commentary.", "fix": "Require: 'specify the range — at base rate X to Y, the argument flips. Numbers.'"},
            {"symptom": "Misses values-based components.", "fix": "Add: 'if disagreement is values-based (false-positive harm vs false-negative harm), surface explicitly. Bayes can't decide values.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["argument-steelman-then-counter", "fermi-estimation", "evidence-quality-scorer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["bayes-theorem", "base-rate-fallacy"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why are base rates so hard?", "answer": "Human intuition uses representativeness, not probability. We see 'top-performer is from top-school' and conclude 'school predicts performance', skipping the base rate of top-school candidates in the applicant pool entirely."},
            {"question": "What if I genuinely don't know the base rate?", "answer": "Use the 'when would this matter' bracket to show under what assumed base rates the argument holds. Forces honest reasoning under uncertainty."},
            {"question": "Is this just statistics?", "answer": "Yes — Bayesian reasoning applied. The value is having a checklist that surfaces the bias systematically, not after-the-fact statistical critique."},
            {"question": "Doesn't this make every argument 'it depends'?", "answer": "It makes you specify WHAT it depends on. That's progress. Bayesian correction often DOES flip conclusions — not always toward uncertainty."},
        ],
        "meta_title": "Base-Rate Correction Check — Reasoning Prompt",
        "meta_description": "Catch base-rate neglect: surface the base rate, conditional probabilities, Bayesian correction with explicit numbers, decision implications.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "second-order-consequences-mapper",
        "title": "Second-Order Consequences Mapper",
        "tldr": "Maps the 2nd and 3rd-order consequences of a decision — who responds, what incentives shift, what equilibria emerge — for policy, product, and people decisions where first-order thinking misses the actual impact.",
        "category": "reasoning",
        "tags": ["systems-thinking", "second-order", "decision-making", "consequences"],
        "best_for_tags": ["executives", "policymakers", "product-leaders"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Product pricing change", "example": "Lower price: 1st-order = more buyers; 2nd = competitor reaction, churn from existing; 3rd = brand-position shift."},
            {"scenario": "HR policy update", "example": "Mandatory office: 1st = compliance; 2nd = attrition of remote talent; 3rd = recruiting pipeline shift."},
            {"scenario": "Public-policy proposal", "example": "Rent control: 1st = stabilized rents; 2nd = supply withdrawal; 3rd = informal-market growth."},
            {"scenario": "Algorithm or moderation change", "example": "Tighten content rules: 1st = less harmful content; 2nd = shift to alternative platforms; 3rd = reduced engagement."},
        ],
        "when_not_to_use": "Skip for genuinely simple decisions (no significant stakeholders react). Skip when you'd be guessing — needs real domain knowledge of how actors respond.",
        "full_prompt": """You are a systems-thinking analyst. Map 2nd and 3rd-order consequences of a decision, including stakeholder responses and equilibrium shifts.

INPUT
- The decision: {decision}
- Context / domain: {context}
- Stakeholders affected: {stakeholders}
- Time horizon: {horizon}            (3 mo / 1 yr / 3 yrs)
- What the decider HOPES will happen (1st-order goal): {hoped_outcome}

OUTPUT

## 1. The 1st-order intended effect
Restate the decision and what the decider EXPECTS will happen:
- Direct mechanism: ___
- Expected magnitude: ___
- Time-to-effect: ___

This is the obvious / intended impact.

## 2. Who responds (stakeholder reaction map)
For each stakeholder in {stakeholders}:
- **Who:** ___
- **Their current incentives:** ___
- **How their incentives SHIFT under the new decision:** ___
- **What they'll do in response (likely + counter-likely action):** ___
- **Time-to-response:** fast (days) / medium (weeks) / slow (months)

A 2nd-order effect = the AGGREGATE of stakeholder responses.

## 3. 2nd-order effects
Now synthesize what happens when stakeholders respond:
- 2nd-order effect 1: ___
- 2nd-order effect 2: ___
- 2nd-order effect 3: ___

For each: how it amplifies, dampens, or REVERSES the 1st-order intended effect.

## 4. 3rd-order effects (equilibrium shifts)
What new equilibrium emerges?
- New steady state: ___ (compared to old equilibrium)
- Who's better off: ___
- Who's worse off: ___
- What's irreversible: ___

3rd-order is the hardest to predict — name your CONFIDENCE level (high / medium / low).

## 5. The 'this could backfire' scenarios
Specific ways the decision could PRODUCE THE OPPOSITE of intended:
- Scenario A: ___ (e.g., 'price cut intended to increase volume actually shrinks because brand becomes a budget-brand')
- Scenario B: ___

Rate likelihood for each: high / medium / low.

## 6. Indicators to watch
What metrics, if observed, indicate the decision is producing 1st vs 2nd vs 3rd order effects?
- Leading indicators (1st-order playing out): ___
- Lagging indicators (2nd-order arriving): ___
- Equilibrium indicators (3rd-order setting in): ___

These let you DIAGNOSE the decision in production.

## 7. Mitigations
For the highest-likelihood backfire scenarios:
- Mitigation 1: ___ (concrete action that reduces 2nd/3rd order downside)
- Mitigation 2: ___

A mitigation should be CONCRETE, not 'monitor closely'.

CRITICAL RULES
- Stakeholder responses are EVIDENCE-BASED (rooted in their actual incentives), not narrative speculation.
- 2nd-order effects can REVERSE 1st-order — be willing to predict that.
- 3rd-order has lower confidence; mark it.
- Backfire scenarios are required — first-order thinking is too rosy.
- Indicators are MEASURABLE; mitigations are CONCRETE.

DECISION
{decision}

Begin.""",
        "input_variables": [
            {"name": "decision", "type": "string", "description": "Decision being made", "required": True, "example": "Move our SaaS pricing from per-seat to usage-based, effective in 90 days."},
            {"name": "context", "type": "string", "description": "Context / domain", "required": True, "example": "B2B SaaS, 800 customers, $40M ARR, competitive market with 3 main alternatives."},
            {"name": "stakeholders", "type": "string", "description": "Stakeholders", "required": True, "example": "Existing customers (heavy + light users), prospects, sales reps (comp plan tied to seats), CS team, competitors, investors."},
            {"name": "horizon", "type": "string", "description": "Time horizon", "required": True, "example": "1 year"},
            {"name": "hoped_outcome", "type": "string", "description": "Hoped 1st-order outcome", "required": True, "example": "Pricing better aligned to value; expand revenue from heavy users; easier to acquire small accounts."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: 1st-order intended effect, stakeholder reaction map, 2nd-order effects, 3rd-order equilibrium shifts (with confidence), backfire scenarios with likelihood, indicators to watch, mitigations.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at backfire scenarios + honest confidence on 3rd-order."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can default to optimism — re-pin backfire requirement."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; weaker on stakeholder incentive precision."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple decisions; thins on 3rd-order analysis."},
        ],
        "variations": [
            {"label": "Pre-mortem-style", "description": "Lead with backfire.", "prompt_snippet": "Reverse the sections: lead with section 5 (backfires) before sections 3-4. Used when the team is in advocacy mode and needs disruption."},
            {"label": "Multi-decision compare", "description": "Compare 2-3 decisions.", "prompt_snippet": "Apply to N candidate decisions. Output a comparison: 2nd-order effects per decision + which has the most resilient 3rd-order equilibrium."},
            {"label": "Reversibility map", "description": "Focus on which 3rd-order shifts are irreversible.", "prompt_snippet": "After section 4, add: 'rank each 3rd-order shift by reversibility (reversible / costly-to-reverse / permanent). Frame the decision through reversibility lens.'"},
        ],
        "failure_modes": [
            {"symptom": "Stakeholder responses are speculation.", "fix": "Re-pin: 'each response anchored in their stated/implied incentives. If you can\\'t name the incentive, you\\'re guessing.'"},
            {"symptom": "2nd-order just describes more 1st-order.", "fix": "Force: '2nd-order = aggregate of stakeholder responses, not direct effect. If you can describe it without naming who responded, it\\'s not 2nd-order.'"},
            {"symptom": "Misses 'reverses intended effect' cases.", "fix": "Add: 'one of the 2nd-order effects must consider whether the decision PRODUCES THE OPPOSITE of intent.'"},
            {"symptom": "Vague indicators ('watch the numbers').", "fix": "Require: 'each indicator is a specific metric + threshold + when to look.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["argument-steelman-then-counter", "go-no-go-decision-meeting-prep", "incident-postmortem-blameless"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["systems-thinking", "second-order-effects"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Isn't this just 'thinking harder'?", "answer": "It's structured thinking. First-order intuition is fast but biased optimistic. The structure forces stakeholder-by-stakeholder reasoning + explicit backfire consideration."},
            {"question": "How confident should I be in 3rd-order predictions?", "answer": "Low-to-medium for complex systems. The value isn't precise prediction — it's surfacing the equilibrium-shift category so you watch for it."},
            {"question": "Can it predict black swans?", "answer": "No — black swans are by definition out-of-distribution. But it surfaces the GREY swans: predictable second-order effects most teams miss."},
            {"question": "Why include mitigations?", "answer": "Decisions get made anyway. Mitigations buy down the downside of the highest-likelihood backfire scenarios. Without them, you've identified risk but not reduced it."},
        ],
        "meta_title": "Second-Order Consequences Mapper — Reasoning Prompt",
        "meta_description": "Map 2nd and 3rd-order consequences: stakeholder responses, equilibrium shifts, backfire scenarios with likelihood, indicators to watch, mitigations.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "analogy-quality-stress-test",
        "title": "Analogy Quality Stress-Test",
        "tldr": "Tests an analogy by mapping where it HOLDS, where it BREAKS, and where it leads readers ASTRAY — for product positioning, public communication, and strategic framing.",
        "category": "reasoning",
        "tags": ["analogy", "framing", "communication", "epistemics"],
        "best_for_tags": ["communicators", "strategists", "founders"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Product positioning", "example": "'We're the Uber for X' — does the analogy actually hold or mislead?"},
            {"scenario": "Public policy framing", "example": "'Internet should be regulated like utilities' — where the analogy works vs breaks."},
            {"scenario": "Strategic positioning memo", "example": "Internal memo uses analogy; stress-test before publishing."},
            {"scenario": "Customer education", "example": "Explaining new product — is the analogy you're using helpful or misleading?"},
        ],
        "when_not_to_use": "Skip when the audience is technical experts who can reason from first principles — analogy hurts precision. Skip when stakes are very high and a literal explanation is feasible.",
        "full_prompt": """You are an analogy stress-tester. Map where an analogy holds, breaks, and misleads.

INPUT
- The analogy: {analogy}                  (typically X is like Y, or X is the Y of Z)
- What it's being used to communicate: {claim_being_made}
- Audience: {audience}
- Stakes (decisions / actions that depend on the analogy): {stakes}

OUTPUT

## 1. The analogy unpacked
Restate the analogy explicitly:
- **Source:** ___ (the familiar thing being mapped FROM)
- **Target:** ___ (the new thing being mapped TO)
- **Implied mapping:** what features of source → target.

Sometimes the analogy is more specific than people realize ('Uber for X' implies marketplace + asymmetric utilization + service-on-demand). Surface what's actually being claimed.

## 2. Where the analogy HOLDS
Specific structural similarities — real, not vague:
- **Mapping 1:** [source feature] ↔ [target feature]. Why it holds: ___
- **Mapping 2:** ___
- **Mapping 3:** ___

These are the parts of the analogy that EARN it.

## 3. Where the analogy BREAKS
Disanalogies — specific features that DON'T map:
- **Break 1:** Source has X; target doesn't. Implication: ___
- **Break 2:** ___
- **Break 3:** ___

Don't soften. The breaks are usually where the analogy LEADS DECISIONS ASTRAY.

## 4. Where the analogy MISLEADS
The most dangerous part. What CONCLUSIONS will the audience draw from the analogy that AREN'T TRUE of the target?
- "If [target] is like [source], audience will assume X. But X is FALSE for target."
- "The analogy implies [strategy] that works for source but FAILS for target because [break]."

These are the analogy's epistemic costs.

## 5. The analogy scorecard
- **Useful for:** [communication situations where the analogy works]
- **Dangerous for:** [communication situations where it misleads]
- **Better analogies if you need one:** [2-3 alternatives + when each is better]
- **Better than analogy entirely:** [literal description if feasible]

## 6. Refinement
If the analogy is mostly useful but has known break points:
- Phrasing that PRESERVES the useful similarities while DISCLAIMING the breaks.
- Example: "X is like Uber-the-app, NOT like Uber-the-business — same on-demand UX, very different unit economics."

## 7. Verdict
- **KEEP** — analogy mostly holds; refine per section 6.
- **REPLACE** — better analogy exists; suggest it.
- **DROP** — analogy is more misleading than useful; recommend literal explanation.

CRITICAL RULES
- Mappings in section 2 are SPECIFIC structural similarities, not vague vibes.
- Breaks in section 3 are HONEST — the goal is finding them, not protecting the analogy.
- Misleads in section 4 are the most important section — that's where decisions go wrong.
- Verdict is willing to say 'DROP' if the analogy hurts more than helps.

ANALOGY
{analogy}

CLAIM
{claim_being_made}

Begin.""",
        "input_variables": [
            {"name": "analogy", "type": "string", "description": "The analogy being tested", "required": True, "example": "Our LLM agent platform is the GitHub for AI agents."},
            {"name": "claim_being_made", "type": "string", "description": "What the analogy communicates", "required": True, "example": "We're the developer-first hub where agents are versioned, shared, forked, and collaborated on."},
            {"name": "audience", "type": "string", "description": "Audience", "required": True, "example": "Developer founders + early-stage VCs"},
            {"name": "stakes", "type": "string", "description": "Decisions that depend on it", "required": True, "example": "Positioning for a Series A pitch + GTM messaging for developer launch."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: analogy unpacked, where it holds (mappings), where it breaks (disanalogies), where it misleads (epistemic costs), scorecard, refinement language, verdict.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at honest breaks + 'misleads' section without softening."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can soft-pedal misleads — re-pin honesty."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; sometimes vague on structural mappings."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple analogies; thins on misleads."},
        ],
        "variations": [
            {"label": "Position-vs-competitor", "description": "Stress-test competitor's analogy.", "prompt_snippet": "Apply to a COMPETITOR's analogy (how they describe themselves). Output: where their analogy works for them, where it WEAKENS them, where you can attack."},
            {"label": "Education metaphor audit", "description": "Apply to teaching metaphors.", "prompt_snippet": "Test a teaching analogy used in onboarding / docs. Surface where learners are likely to TRANSFER the wrong intuition."},
            {"label": "Inverse — analogy generator", "description": "Generate better analogies for a claim.", "prompt_snippet": "Given the CLAIM but no analogy, generate 4-5 candidate analogies + score each on usefulness vs misleading-ness."},
        ],
        "failure_modes": [
            {"symptom": "Vague mappings.", "fix": "Force: 'each mapping names a SPECIFIC feature of source and target. Not \"similar in spirit\".'"},
            {"symptom": "Skips breaks.", "fix": "Re-pin: 'minimum 3 breaks. If genuinely fewer, explain why this analogy is unusually clean.'"},
            {"symptom": "Misleads section is generic.", "fix": "Require: 'specific WRONG inference an audience will draw. Name the wrong conclusion.'"},
            {"symptom": "Verdict avoids DROP.", "fix": "Re-pin: 'DROP is a real option. Many analogies should be retired. Don\\'t protect bad analogies.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["argument-steelman-then-counter", "metaphor-extender", "concept-explainer-with-progressive-depth"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["analogy", "framing"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Aren't analogies necessary for communication?", "answer": "Yes — they're powerful when used well. The point isn't to ban analogies, it's to test them. A stress-tested analogy is stronger; a failed-stress-test analogy is dangerous."},
            {"question": "What if the audience expects the analogy?", "answer": "Use the refinement in section 6 — preserve the useful similarity while disclaiming the breaks. The phrasing 'X is like Y in terms of A, but unlike Y in terms of B' is often the best of both."},
            {"question": "Most common analogy traps?", "answer": "'Uber for X' (usually fails unit economics test). 'GitHub for X' (usually fails network-effect test). 'Netflix for X' (usually fails content-investment test). These get retired most often after stress-testing."},
            {"question": "Can the analogy be useful AND misleading?", "answer": "Often — that's the point of the scorecard. The same analogy can clarify a positioning conversation while misleading a strategy decision. Use case-by-case."},
        ],
        "meta_title": "Analogy Quality Stress-Test — Reasoning Prompt",
        "meta_description": "Test where an analogy holds, breaks, and misleads. With refinement phrasing and keep/replace/drop verdict.",
        "version": "v2.0",
        "release_status": "stable",
    },
]
