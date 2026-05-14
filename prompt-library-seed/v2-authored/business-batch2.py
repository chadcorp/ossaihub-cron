"""Business prompts — batch 2."""

RECORDS = [
    {
        "slug": "hiring-rubric-builder",
        "title": "Hiring Rubric Builder For A Role",
        "tldr": "Builds a hiring rubric for a specific role: 4-6 dimensions with anchored levels (1-4 each), interview questions per dimension, and a calibration question to prevent rubric drift across interviewers.",
        "category": "business",
        "tags": ["hiring", "interviewing", "rubric", "calibration"],
        "best_for_tags": ["recruiting", "interview-design", "hiring-managers"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "New role's first interview loop", "example": "‘Senior Backend Engineer’ → rubric with 5 dimensions, anchored 1-4 with specific examples, sample interview questions."},
            {"scenario": "Calibration across multiple interviewers", "example": "Each interviewer sees the same rubric anchors; ‘scored 3 on system design’ means the same thing."},
            {"scenario": "Promotion criteria", "example": "Same rubric structure for internal promotions, anchors recalibrated for the level."},
            {"scenario": "Hiring panel debrief sheet", "example": "Rubric becomes the debrief structure — each interviewer scores then panel discusses."},
        ],
        "when_not_to_use": "Skip for purely vibes-based hires (founder-led, friend hires). Skip for very specialized senior roles where you'd rather have unstructured deep conversations with 2-3 candidates.",
        "full_prompt": """You are designing a hiring rubric for a specific role. The rubric will be used by multiple interviewers to evaluate candidates consistently.

INPUT
- Role: {role}
- Level: {level}                    (e.g., L3 / Senior / Staff)
- Team context: {team_context}
- What success looks like in this role (6-12 months in): {success_picture}

OUTPUT

## Rubric dimensions (4-6)
Each dimension is a CAPABILITY, not a topic. Examples of capabilities:
- "Reduces ambiguous problems to actionable steps"
- "Communicates trade-offs to non-technical stakeholders"
- "Handles disagreement with peers productively"
Bad (these are topics):
- "Python" (you can be a strong or weak Python user — what's the capability?)
- "Communication" (too vague)

For each dimension:

### Dimension N: <capability>

| Level 1 (does not meet) | Level 2 (developing) | Level 3 (meets) | Level 4 (exceeds) |
|---|---|---|---|
| Anchor with concrete behavior | Anchor | Anchor | Anchor |

The Level-3 anchor is what you'd expect from a "meets bar" candidate. Level-4 is rare.

## Interview questions per dimension
2-3 questions per dimension, designed to elicit evidence at multiple levels.

Each question:
- Open-ended (no yes/no).
- Past-experience focused ("Tell me about a time when..." > "How would you...").
- Has a probing follow-up ("What did you try first? What did you change?")

## Calibration scenario
ONE common interview scenario with three candidate answers labeled with their score on this dimension. Used to calibrate interviewers before live interviews.

## Decision rule
How to combine dimension scores into a hire/no-hire decision:
- Minimum threshold per dimension (e.g., no Level 1 anywhere, at least one Level 4)
- How to weight dimensions if they conflict
- When to call a tie

## Anti-bias notes
3-4 specific biases this rubric is vulnerable to + a guardrail for each:
- "Cultural fit" without concrete behavior anchors → bias toward similar candidates. Guardrail: require behavioral examples.
- Etc.

RULES
- Dimensions should be ORTHOGONAL — a strong candidate could excel in one and not another.
- Anchors are observable behaviors, not feelings ("I felt they understood" doesn't count).
- Don't include "passion" / "drive" / "ownership" as a top-level dimension — too vague. Break into observable behaviors.

ROLE
{role}

CONTEXT
{team_context}

SUCCESS PICTURE
{success_picture}

Begin.""",
        "input_variables": [
            {"name": "role", "type": "string", "description": "Job title and seniority", "required": True, "example": "Senior Backend Engineer"},
            {"name": "level", "type": "string", "description": "Career level", "required": True, "example": "L5 / Senior, 5-8 years experience"},
            {"name": "team_context", "type": "string", "description": "About the team", "required": True, "example": "8-person engineering team, scaling from 100k to 1M users, mostly Python/Postgres/AWS"},
            {"name": "success_picture", "type": "string", "description": "What success in this role looks like", "required": True, "example": "By month 6, has shipped a major feature solo, is the go-to person for one subsystem, has trained one junior on it."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "4-6 dimensions, each with a 4-level anchor table + interview questions; plus calibration scenario, decision rule, anti-bias notes.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on concrete behavior anchors and identifying real biases."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes anchors are too generic — re-pin ‘observable behavior’."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Holds the structure; anti-bias section can be cliché."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to use vague dimensions; explicitly forbid in prompt."},
        ],
        "variations": [
            {"label": "Take-home variant", "description": "Replace one interview question with a take-home rubric.", "prompt_snippet": "Add: ‘for the technical dimension, propose a 2-hour take-home with a separate rubric for scoring the submission.’"},
            {"label": "Pair-interview rubric", "description": "Rubric for pair-programming interviews.", "prompt_snippet": "Add Dimension: ‘ability to think aloud during problem-solving’; include guidance for pair interviewers to score this in real-time."},
            {"label": "Reference check rubric", "description": "Extend to back-channel references.", "prompt_snippet": "Add Section: ‘reference check questions that probe each dimension; how to score what references say.’"},
        ],
        "failure_modes": [
            {"symptom": "Dimensions like ‘Python skills’ instead of capabilities.", "fix": "Re-pin: ‘dimensions are CAPABILITIES, not skills or topics.’"},
            {"symptom": "Anchors are feelings (‘seemed confident’).", "fix": "Add: ‘every anchor is an observable behavior or artifact; if it requires inference, rewrite.’"},
            {"symptom": "Decision rule is vague (‘discuss at debrief’).", "fix": "Add: ‘decision rule must be testable — given X scores, the answer is Y; given Z scores, the answer is W.’"},
            {"symptom": "Anti-bias section is generic.", "fix": "Add: ‘each bias must reference a SPECIFIC dimension or anchor that's vulnerable; generic ‘watch for bias’ doesn't count.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["okr-quarterly-drafter", "weekly-review-coach"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["hiring-rubric", "calibration", "structured-interviewing"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How many dimensions is right?", "answer": "4-6. Fewer and you miss important angles. More and interviewers lose track and lean on gut. The starter caps at 6 deliberately."},
            {"question": "Should I share the rubric with candidates?", "answer": "The dimensions and questions — yes (transparency builds trust, prep helps both sides). The anchors and decision rule — typically no (gives away the test)."},
            {"question": "What about culture fit?", "answer": "Avoid ‘culture fit’ as a dimension — it's where most bias hides. If something specific about your culture matters (high autonomy, async, etc.), make it an explicit capability with anchors."},
        ],
        "meta_title": "Hiring Rubric Builder For A Role — Prompt",
        "meta_description": "Build a structured hiring rubric: 4-6 capability dimensions with anchored 1-4 levels, interview questions, calibration scenario, decision rule.",
    },
    {
        "slug": "fundraise-pitch-deck-outline",
        "title": "Fundraise Pitch Deck Outline (Seed to Series A)",
        "tldr": "Outlines a fundraise pitch deck (10-14 slides) tailored to stage. Each slide includes its job-to-be-done, the question it answers, what to put on it, and the trap to avoid.",
        "category": "business",
        "tags": ["fundraising", "pitch-deck", "founders", "investor-relations"],
        "best_for_tags": ["seed-stage", "series-a", "founder-fundraising"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "First-time founder building seed deck", "example": "Get a slide-by-slide outline calibrated for seed (vs Series A, which needs different evidence)."},
            {"scenario": "Series A prep", "example": "Outline tuned for Series A: metrics weight more, vision still matters, board materials maturity."},
            {"scenario": "Pivot announcement to existing investors", "example": "Special-case version focused on what changed and what's preserved."},
            {"scenario": "Sales deck → investor deck conversion", "example": "Identify what to add and what to cut when adapting sales material."},
        ],
        "when_not_to_use": "Skip for highly unusual fundraises (rolling SAFE, bridge round, deep-tech with 7-year horizons) — those have non-standard narratives. Use this for typical Seed/A patterns.",
        "full_prompt": """You are an experienced fundraiser advising on a pitch deck. Output a slide-by-slide outline tailored to the stage.

INPUT
- Round being raised: {round}                     (e.g., "Seed $3M", "Series A $12M")
- Company stage and metrics: {stage_metrics}
- Sector: {sector}
- Founder narrative summary: {founder_narrative}
- Investor type targeted: {investor_type}         (e.g., "Tier 1 sector-specialist VC", "Strategic", "Generalist")

OUTPUT — slide-by-slide outline

For each slide:

## Slide N: <slide name>

- **Job to be done**: What this slide must accomplish in the investor's mind.
- **Question it answers**: The specific question an investor would ask if you didn't put this slide.
- **What to put on it**: 3-5 specific elements (not just ‘the team’; specifically: ‘photo + 3-bullet credibility + the one experience that maps to this company’).
- **Trap to avoid**: The most common failure mode of this slide.

STANDARD SEED DECK (~12-14 SLIDES)
1. Title (company name + one-line + raise + your name)
2. Problem (real pain, real audience, real evidence)
3. Solution (with one screenshot or product moment, not a description)
4. Why now (what changed that makes this possible / urgent)
5. Market (TAM/SAM/SOM done credibly, not Excel-fantasy)
6. Product (1-2 slides showing what it actually does)
7. Traction (numbers honestly; if early, the early signals you DO have)
8. Business model (how you make money, unit economics if known)
9. Competition (matrix or 2x2 — not "we have no competitors")
10. Go-to-market (how you reach customers; first 100 won, plan for next 1000)
11. Team (team is product at seed; show why this team for this problem)
12. The ask + use of funds (specific milestones the money buys)
13. Vision (where this goes if it works)
14. Appendix (waiting in the wings if asked)

ADJUSTMENTS BY STAGE
- Seed: heavy on team + why-now + market + early signal. Light on metrics.
- Series A: heavier on traction (retention, revenue, unit economics). Vision still matters but evidence weighs more.
- Series B+: enterprise sales motion, defensibility, scaling levers.

INVESTOR TYPE ADJUSTMENTS
- Sector specialist: assume domain context; lean into nuance.
- Generalist: more sector-context slides; less assumed knowledge.
- Strategic: include strategic fit + integration narrative.

CRITICAL RULES
- Each slide does ONE thing. Don't combine.
- Investor reads top to bottom, no skipping. Order is part of the argument.
- If you don't have a number for a slide, don't make one up — acknowledge and frame around qualitative evidence.

NOW PRODUCE THE OUTLINE FOR {round}.""",
        "input_variables": [
            {"name": "round", "type": "string", "description": "Round and amount", "required": True, "example": "Series A, $12M target"},
            {"name": "stage_metrics", "type": "string", "description": "Where the company is now", "required": True, "example": "B2B SaaS, $1.4M ARR, growing 18% MoM, 8 enterprise customers, 24-month runway pre-raise"},
            {"name": "sector", "type": "string", "description": "Sector / category", "required": True, "example": "Developer tools for data engineering"},
            {"name": "founder_narrative", "type": "string", "description": "Founder origin + insight", "required": True, "example": "Two ex-Snowflake engineers; built an internal tool there for 4 years that this company productizes. Insight: every data team rebuilds the same wrapper."},
            {"name": "investor_type", "type": "string", "description": "Type of investor", "required": False, "example": "Tier 1 enterprise-software-specialist VC"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "12-14 slides, each with: job-to-be-done, question, what to put, trap to avoid. Stage-adjusted.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on stage-specific calibration; identifies real traps."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes generic on ‘traps to avoid.’"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid structure; traps section can be cliché."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Doesn't differentiate stages well; needs explicit prompting."},
        ],
        "variations": [
            {"label": "Memo-first variant", "description": "Optimize for memo-reading investors (Coatue, Tiger).", "prompt_snippet": "Add: ‘also output a 2-page memo version: prose-driven, deck visuals optional, suitable for investors who prefer reading to slides.’"},
            {"label": "Pre-mortem the deck", "description": "Identify what makes investors pass.", "prompt_snippet": "After outline, add: ‘5 most likely reasons an investor passes on this deck — and the slide that should preempt each.’"},
            {"label": "Founder strengths emphasis", "description": "Lead with what makes this team unbeatable on this problem.", "prompt_snippet": "Move team slide earlier (slide 3-4) if founder narrative is the strongest asset; adjust subsequent slides accordingly."},
        ],
        "failure_modes": [
            {"symptom": "Generic ‘traps to avoid’.", "fix": "Re-pin: ‘traps must be specific to this slide and this company stage; ‘too much text’ doesn't count.’"},
            {"symptom": "Slide 9 says ‘we have no competitors.’", "fix": "Add explicit guidance: ‘if you genuinely have no competitors, you have no market. Reframe as ‘adjacent solutions our buyers currently use’ — there's always something.’"},
            {"symptom": "Stage adjustments not applied.", "fix": "Add: ‘before output, state the stage explicitly; every slide's content should reflect this stage.’"},
            {"symptom": "Vision slide is corporate-speak.", "fix": "Add: ‘vision must be SPECIFIC — a world where X happens because we exist. Avoid ‘change the world’ unless the company actually does.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["investor-update-monthly", "competitive-feature-matrix", "executive-summary-1-page"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["pitch-deck", "fundraise"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should I customize per investor?", "answer": "The deck stays mostly the same; the conversation customizes. Customize: opening line, the example you walk through, the metric you emphasize. Don't rebuild the deck."},
            {"question": "How long is too long?", "answer": "12-14 slides + appendix. 20+ is usually padding or a confused argument. If you can't fit your pitch in 14, you don't have clarity yet."},
            {"question": "Use a template or build from scratch?", "answer": "Build from scratch — templates leak through. The outline this prompt gives you is the bones; the visual presentation is your work."},
        ],
        "meta_title": "Fundraise Pitch Deck Outline (Seed to Series A)",
        "meta_description": "Slide-by-slide deck outline: job-to-be-done, question answered, what to put, trap to avoid. Stage-tuned (seed/A) and investor-type-aware.",
    },
    {
        "slug": "go-to-market-experiment-design",
        "title": "Go-To-Market Experiment Design",
        "tldr": "Design a single GTM experiment with a falsifiable hypothesis, leading indicators, kill criterion, and sample-size justification. Anti-fishing — forces commitment to a specific bet.",
        "category": "business",
        "tags": ["gtm", "experiments", "growth", "hypothesis"],
        "best_for_tags": ["startup-growth", "marketing-experiments", "channel-tests"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Testing a new acquisition channel", "example": "‘Should we invest in LinkedIn ads?’ → 2-week structured experiment with success and kill criteria."},
            {"scenario": "Pricing experiment", "example": "Test new packaging tier on subset of trials; success = 15%+ upgrade rate; kill = <5% or any unforeseen churn."},
            {"scenario": "Sales motion change", "example": "Test free trial vs demo-led for SMB segment; clear leading indicators."},
            {"scenario": "Content marketing test", "example": "Test long-form blog vs short-form social for B2B audience; measure properly."},
        ],
        "when_not_to_use": "Skip when the experiment is too cheap to design (just try it). Skip when the company can't actually pull the trigger fast — design without execution is theater.",
        "full_prompt": """You are designing a GTM experiment. The point is to LEARN, not to feel productive.

INPUT
- The bet you want to test: {bet}
- Current company stage / size: {stage}
- What you know already (existing data): {prior_data}
- Resources committable: {resources}        (people, dollars, weeks)

OUTPUT

## 1. Hypothesis (falsifiable)
One sentence in the form: "We believe X will produce Y because Z."
- X = specific action
- Y = measurable outcome with a number and time-bound
- Z = the causal mechanism

Bad: "We think LinkedIn ads will help us grow."
Good: "We believe spending $5k on LinkedIn ads targeting Director-level data engineers will generate 30+ qualified leads in 2 weeks, because we have evidence this audience converts at 3% on cold outreach."

## 2. Leading indicators (visible in days, not weeks)
3-5 metrics that, if they move, predict success early. For each:
- Metric
- What ‘on track’ looks like at day 3 and day 7

## 3. Lagging indicators (the actual proof)
1-3 metrics that constitute final success. With:
- Target threshold to call SUCCESS.
- Threshold to call FAILURE.
- ‘Inconclusive’ zone between.

## 4. Kill criterion
Specific signal that we should stop early. NOT just ‘if it's not working’ — a concrete number or observation.

## 5. Sample size justification
Why is the proposed scale big enough to see a real signal? Either:
- Statistical: minimum sample size for 80% power at expected effect size.
- Empirical: similar tests historically gave clear signal at this scale.
- Pragmatic: smallest budget that's larger than a noise threshold.

## 6. Cost & timeline
- Total spend
- People-time required
- Calendar weeks
- Opportunity cost (what we're NOT doing while running this)

## 7. Decision criteria after
Three outcomes pre-committed:
- If SUCCESS: what do we do next (scale up, productize, hire)?
- If FAILURE: what do we kill?
- If INCONCLUSIVE: what's the next experiment to disambiguate?

## 8. What this experiment won't tell us
2-3 things people will be tempted to read into the results that this design CAN'T prove. Honesty here prevents over-extrapolation.

ANTI-FISHING RULE
If after running this experiment we'd need to re-interpret to call it a ‘win’, the hypothesis was wrong. Pre-commit to the criteria before starting.

THE BET TO TEST
{bet}

Begin design.""",
        "input_variables": [
            {"name": "bet", "type": "string", "description": "The GTM bet to test", "required": True, "example": "We should run LinkedIn ads to acquire enterprise leads."},
            {"name": "stage", "type": "string", "description": "Company stage", "required": True, "example": "Seed-stage, $400k ARR, 4 customers"},
            {"name": "prior_data", "type": "string", "description": "What we know", "required": True, "example": "3% conversion on cold email to director-level. Some inbound leads from blog content. No paid ads tried yet."},
            {"name": "resources", "type": "string", "description": "What we can commit", "required": True, "example": "$5k budget, 1 marketing hire 50% time, 2 weeks"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Eight sections: hypothesis, leading indicators, lagging indicators, kill criterion, sample size, cost, decision criteria, won't-tell-us.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong falsifiable hypotheses and honest won't-tell-us."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally over-confident on sample-size math."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; kill criterion can be vague — re-pin."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Defaults to vague hypotheses; needs explicit form."},
        ],
        "variations": [
            {"label": "Multi-armed bandit variant", "description": "When testing several variations at once.", "prompt_snippet": "Replace single-hypothesis with 3-4 hypothesis variants; describe how to allocate budget across arms (e.g., Thompson sampling) and when to declare a winner."},
            {"label": "Holdout-group design", "description": "Compare treatment to no-treatment.", "prompt_snippet": "Add: ‘design with a true holdout group — what percentage of audience gets no treatment? How will randomization be ensured?’"},
            {"label": "Sequential analysis", "description": "For long-running experiments.", "prompt_snippet": "Add: ‘design as a sequential test — check thresholds at days 3, 7, 14; stop early if you cross a pre-set significance boundary.’"},
        ],
        "failure_modes": [
            {"symptom": "Hypothesis is vague (‘LinkedIn ads will help us grow’).", "fix": "Re-pin form: ‘we believe X will produce Y because Z.’ All three required."},
            {"symptom": "Kill criterion is ‘if it's not working.’", "fix": "Add: ‘kill criterion must be a SPECIFIC number or observation; vague ‘not working’ doesn't count.’"},
            {"symptom": "Won't-tell-us is empty.", "fix": "Add: ‘every experiment has limits; if you can't list any, you haven't thought hard enough about what the data CAN'T support.’"},
            {"symptom": "Decision criteria all say ‘discuss internally.’", "fix": "Force pre-commitment: ‘if SUCCESS, we will SPECIFICALLY do X. Names the action.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["a-b-test-result-interpreter", "decomposition-into-subgoals", "okr-quarterly-drafter"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["gtm-experiment", "hypothesis-driven-development"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What if the experiment is too small to be statistically significant?", "answer": "Then call it an exploratory test, not a decision-making experiment. Use it to learn — don't pretend it proves things it can't."},
            {"question": "What about confounders?", "answer": "Section 8 (won't-tell-us) is where to surface confounders. ‘LinkedIn ads ran while we also launched a feature — improvement may be either.’"},
            {"question": "Should the team see all sections before starting?", "answer": "Yes. Pre-commitment is the point. Section 7 (decision criteria) is especially important — people rationalize after; pre-commitment prevents that."},
        ],
        "meta_title": "Go-To-Market Experiment Design — Prompt",
        "meta_description": "Falsifiable GTM experiment design with leading indicators, kill criterion, sample-size justification, and pre-committed decision rules.",
    },
    {
        "slug": "customer-segmentation-from-data",
        "title": "Customer Segmentation From Behavioral Data",
        "tldr": "Builds segmentation from customer behavioral data (usage, purchase, retention patterns). Names segments by JOB-TO-BE-DONE, not demographics. Includes the questions data alone can't answer.",
        "category": "business",
        "tags": ["segmentation", "customer-analysis", "jtbd", "growth"],
        "best_for_tags": ["product-marketing", "growth-strategy", "retention"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Pre-pricing change", "example": "Segment customers by usage patterns to ensure new pricing doesn't hurt high-value segments."},
            {"scenario": "Product roadmap prioritization", "example": "Identify the segment driving retention vs growth; build for them differently."},
            {"scenario": "Messaging differentiation", "example": "Build separate landing pages or onboarding for distinct segments."},
            {"scenario": "Churn risk targeting", "example": "Identify high-risk segments and tailor saves/retention campaigns."},
        ],
        "when_not_to_use": "Skip when customer base is small (<200) — segmentation is statistically noisy. Skip for one-time purchase products where retention isn't a variable.",
        "full_prompt": """You are segmenting a customer base from behavioral data. Output JTBD-named segments, not demographic clusters.

INPUT
- Customer count: {n_customers}
- Time window of data: {time_window}
- Available data fields: {fields}
- Business question this segmentation answers: {business_question}

OUTPUT

## Step 1: Behavioral dimensions
Pick 3-5 dimensions of behavior visible in the data. Each is a SPECTRUM, not a category:
- "Frequency of use: rarely / weekly / daily / multiple times daily"
- "Breadth of features used: 1-2 / 3-5 / 6+"
- "Time to first value: same day / week / month+"

NOT dimensions:
- "Industry" (demographic, not behavioral)
- "Company size" (demographic)

## Step 2: Hypothesize segments
Sketch 3-5 segments — each occupies a corner or edge of the dimensional space. For each:

### Segment N: <name>
- **Job to be done** (their core "I want to ___ when ___"): the JTBD they're hiring your product for.
- **Behavioral signature**: their position on each dimension.
- **Estimated size**: rough % of customer base.
- **Lifetime value pattern**: are they high-LTV, low-LTV, or unknown?
- **Retention pattern**: do they stick, churn, oscillate?

Bad segment names: "Power Users", "Enterprise". (Don't tell you why they use the product.)
Good segment names: "Daily Decision-Makers" (job: support recurring decisions); "Quarterly Reporters" (job: produce periodic reports).

## Step 3: Validation questions
What questions would the team need to answer to confirm these segments are real?
- Interview candidates (which customers? what to ask?)
- Data analyses to run (correlations, cohort comparisons)
- A/B tests that would prove segment-level different response to messaging

## Step 4: What data alone can't tell us
3-5 things the data CANNOT reveal that you'd need to confirm before betting on segmentation:
- Causality (does feature X drive retention, or do retainers happen to use X?)
- Intent (do they renew because they love it or because they're locked in?)
- Future behavior changes
- Edge segments (rare types that don't show up at scale)

## Step 5: Action implications
For each segment, the 1-2 PRODUCT/MARKETING actions if this segmentation holds:
- Product: feature priorities differ?
- Marketing: messaging differs?
- Pricing: packaging implications?

RULES
- Segments must be MUTUALLY EXCLUSIVE — every customer fits one primary segment.
- Segments should be ACTIONABLE — if knowing the segment doesn't change anything you'd do, it's not useful.
- Don't over-fit to current product. Future product strategy might support new segments.

INPUT DATA SUMMARY
{data_summary}

Begin.""",
        "input_variables": [
            {"name": "n_customers", "type": "integer", "description": "Approximate customer count", "required": True, "example": "1200"},
            {"name": "time_window", "type": "string", "description": "Period covered by data", "required": True, "example": "Past 12 months"},
            {"name": "fields", "type": "string", "description": "What fields are available", "required": True, "example": "sign_up_date, plan, MRR, last_login, weekly_active_days, features_used (list), support_tickets_count, churn_date_or_null"},
            {"name": "business_question", "type": "string", "description": "What this segmentation should answer", "required": True, "example": "Why is overall retention 70% but some cohorts retain 90%? Where do we invest to expand the strong cohort?"},
            {"name": "data_summary", "type": "string", "description": "Summary stats or distributions if available", "required": False, "example": "Median weekly_active_days = 2.3, p90 = 5.0, distribution bimodal..."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Five steps: dimensions, hypothesized segments with JTBD names, validation questions, what-data-cant-tell, action implications.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong JTBD naming and honest data-limitation acknowledgment."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; segment names sometimes drift toward marketing labels."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; can over-segment (8+ segments without need)."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Defaults to demographic categories; needs explicit JTBD focus."},
        ],
        "variations": [
            {"label": "RFM segmentation", "description": "Classical Recency-Frequency-Monetary.", "prompt_snippet": "Replace dimensional approach with: ‘pure RFM scoring — segment by tercile of each, label resulting cells.’ Simpler but less actionable."},
            {"label": "Cohort-based view", "description": "Segment by sign-up cohort rather than current state.", "prompt_snippet": "Add: ‘also segment customers by cohort (month of sign-up) and report which cohorts show the strongest patterns.’"},
            {"label": "Multi-product segmentation", "description": "When you sell multiple products.", "prompt_snippet": "Add: ‘segments may differ by product; produce segmentation per product as well as cross-product.’"},
        ],
        "failure_modes": [
            {"symptom": "Segments are demographic labels (‘SMB’, ‘Enterprise’).", "fix": "Re-pin: ‘behavioral, not demographic.’ Demographics may correlate with segments but aren't the segment."},
            {"symptom": "Too many segments (8+).", "fix": "Add: ‘3-5 segments. If you can't fit, your dimensions are wrong or you're overfitting.’"},
            {"symptom": "Action implications are generic (‘personalize messaging’).", "fix": "Add: ‘actions must be specific — name a feature, a pricing change, a campaign.’"},
            {"symptom": "What-data-can't-tell is empty.", "fix": "Add: ‘data never tells you intent or causality without validation. Name at minimum 3 unknowns.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["cohort-retention-analyzer", "competitive-feature-matrix"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["segmentation", "jtbd", "customer-analytics"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why JTBD names?", "answer": "Demographic labels (‘SMB’) make you build for a category that doesn't exist. JTBD names (‘Quarterly Reporters’) tell you what your product needs to do, and reveal who else in adjacent segments has the same job."},
            {"question": "Should I validate before acting?", "answer": "Always. Section 3 (validation questions) is the bridge. Acting on a hypothesized segmentation that turns out wrong is more expensive than a 2-week validation pass."},
            {"question": "What if my segments overlap heavily?", "answer": "Then your dimensions aren't well-chosen, or you genuinely have fewer segments than you thought. Don't force separation — collapse and try different dimensions."},
        ],
        "meta_title": "Customer Segmentation From Behavioral Data",
        "meta_description": "Build segments from behavioral data with JTBD names, hypothesized segments, validation questions, and honest data-limitation acknowledgment.",
    },
]
