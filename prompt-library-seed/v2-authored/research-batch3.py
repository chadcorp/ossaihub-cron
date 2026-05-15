"""Research — batch 3."""

RECORDS = [
    {
        "slug": "literature-review-gap-finder",
        "title": "Literature Review Gap-Finder",
        "tldr": "Reads a small corpus of papers/sources, maps what each one CLAIMS vs ASSUMES vs LEAVES UNADDRESSED, then surfaces real research gaps — not just unread papers.",
        "category": "research",
        "tags": ["research", "literature-review", "gap-analysis", "academic"],
        "best_for_tags": ["phd-students", "rd-teams", "consultants"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "PhD lit-review chapter", "example": "8-12 papers on graph neural networks for fraud detection — what gaps justify the dissertation."},
            {"scenario": "R&D landscape scan", "example": "Industry team scoping a new feature — what's published vs what's unsolved."},
            {"scenario": "Consulting whitespace map", "example": "Sector study — where the field's actual blind spots sit, not just buzzwords."},
            {"scenario": "Grant proposal positioning", "example": "Position a grant against gaps the reviewers will recognize."},
        ],
        "when_not_to_use": "Skip when corpus exceeds ~15 papers — the model will skim. Skip when you haven't read the papers yourself — you can't validate the gaps.",
        "full_prompt": """You are a research-gap analyst. You map what a corpus CLAIMS, ASSUMES, and LEAVES UNADDRESSED — then surface gaps worth pursuing.

INPUT
- Topic / question: {topic}
- Papers / sources (title + key claims for each): {sources}
- My current angle (if any): {my_angle}
- Audience: {audience}                (dissertation committee / industry team / grant reviewers)

OUTPUT

## 1. Claims map
For each source, in 1-2 sentences:
- **What it CLAIMS** (the headline result)
- **What it ASSUMES** (the unstated premise — domain, data, model, time period)
- **What it LEAVES UNADDRESSED** (what the paper does NOT say it can do)

Be precise. "Leaves unaddressed" is NOT "didn't cite my favorite paper." It's the actual scope boundary.

## 2. Convergence vs divergence
- Where do the sources AGREE? (3-5 points)
- Where do they DISAGREE — and on what? (3-5 points, name the sources)
- Where do they TALK PAST each other? (different problem definitions disguised as same)

## 3. Gap surface
Now the real gaps — categorized:

### Type A: Empirical gaps
Things the field claims but hasn't tested rigorously. Cite which source(s) make the claim untested.

### Type B: Method gaps
Methods that exist but haven't been applied to this domain. Be specific about which method + which sub-problem.

### Type C: Definitional gaps
Where the field uses a term loosely and a sharper definition would unlock progress.

### Type D: Scale gaps
Where results hold at small scale but haven't been shown at production / population scale.

For each gap: rate **research-worthiness** (high / medium / low) with one-sentence justification.

## 4. Anti-gaps (DON'T pursue)
2-3 things that LOOK like gaps but aren't worth pursuing:
- "Combining X and Y" — sounds novel, but X and Y combine trivially.
- "Replication of [paper] in [adjacent domain]" — already done in [other paper].

This section protects the reader from chasing fool's gold.

## 5. My angle check
Given {my_angle}, where does it sit on the gap surface?
- Gap type it fills: ___
- Risk it's already been solved (cite the closest related work): ___
- 1-2 adjustments that would make it stronger.

If no angle was provided, suggest the 2-3 most promising angles ordered by research-worthiness.

CRITICAL RULES
- Be SPECIFIC about which sources make which claim. Vague gaps are useless.
- "Leaves unaddressed" is scope, not failure. Don't strawman papers.
- Anti-gaps section is REQUIRED — protects user from wasted PhD years.
- For each gap, name a tractable next step.

SOURCES
{sources}

Begin.""",
        "input_variables": [
            {"name": "topic", "type": "string", "description": "Research topic / question", "required": True, "example": "Graph neural networks for transaction fraud detection in small-merchant payments"},
            {"name": "sources", "type": "string", "description": "List of papers with title + key claims", "required": True, "example": "(1) Smith 2024: GNN beats XGBoost on fraud F1 by 4pp using merchant graph. (2) Lee 2023: graph methods overfit on small-merchant tail..."},
            {"name": "my_angle", "type": "string", "description": "User's current research angle (optional)", "required": False, "example": "Use temporal graph attention to handle merchant-onboarding cold-start"},
            {"name": "audience", "type": "string", "description": "Target audience", "required": True, "example": "PhD dissertation committee — comp sci"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Five sections: claims map per source, convergence/divergence, four-type gap surface with rated worthiness, anti-gaps to avoid, user-angle check.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at scope-boundary precision; willing to call anti-gaps."},
            {"model": "gpt-4o", "compatibility": "good", "notes": "Solid; tends to be overly polite on anti-gaps — re-pin."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Good with long source lists; weaker on anti-gaps."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for <8 sources; thins out on Type B/D gaps."},
        ],
        "variations": [
            {"label": "Industry whitespace map", "description": "Replace 'research-worthiness' with 'commercial-viability'.", "prompt_snippet": "Swap the rating axis in section 3 from research-worthiness to commercial-viability (high / medium / low) with revenue path."},
            {"label": "Single-paper deep critique", "description": "One paper, deep gap analysis.", "prompt_snippet": "Skip sections 1-2. Run sections 3-4 against a single paper at depth — every gap traced to a specific section/figure."},
            {"label": "Funding-aligned framing", "description": "Match a specific funding call.", "prompt_snippet": "Add: re-frame Type A-D gaps against the priorities of {funding_call}. Drop gaps the call won't fund."},
            {"label": "Pre-registered study", "description": "Output a pre-registration template.", "prompt_snippet": "After section 5, output a 1-page pre-registration template: hypothesis, design, analysis plan, anti-gap defense."},
        ],
        "failure_modes": [
            {"symptom": "Gaps are vague ('more work needed in X').", "fix": "Demand: 'each gap must name a tractable next experiment with measurable outcome.'"},
            {"symptom": "Anti-gaps section is empty.", "fix": "Force: 'minimum 2 anti-gaps with citation of the closest related work that makes them dead.'"},
            {"symptom": "Strawmans the papers.", "fix": "Add: 'leaves unaddressed is scope, not failure. Quote the abstract or claim if borderline.'"},
            {"symptom": "Convergence/divergence is bland summary.", "fix": "Require: 'each agreement/disagreement names the source IDs and the specific claim text.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["research-summary-for-non-experts", "competitor-feature-shipped-analysis", "fermi-estimation"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["literature-review", "research-gap"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Will it hallucinate citations?", "answer": "Only if you ask it to. Feed real source text + claims; don't ask it to invent papers. The prompt operates on what you provide."},
            {"question": "How many sources is too many?", "answer": "8-12 is the sweet spot. Past 15, the model skims. Either pre-cluster sources or run the prompt per cluster and synthesize."},
            {"question": "Why anti-gaps?", "answer": "Most lit-reviews surface fake gaps that look novel but are already-done or trivially-combined. The anti-gaps section forces honesty about which gaps are real."},
            {"question": "Can I use this for grant proposals?", "answer": "Yes — use the funding-aligned variation. It'll re-frame gaps against the call's priorities and drop the ones the call won't fund."},
        ],
        "meta_title": "Literature Review Gap-Finder — Research Prompt",
        "meta_description": "Map what a research corpus claims, assumes, and leaves unaddressed. Surface real gaps with research-worthiness ratings and an anti-gaps section.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "evidence-quality-scorer",
        "title": "Evidence-Quality Scorer",
        "tldr": "Rates a body of evidence on study design, sample, methods, conflicts, and replication — assigns a tiered confidence rating + tells you what would move it up or down.",
        "category": "research",
        "tags": ["research", "evidence-rating", "epistemics", "fact-checking"],
        "best_for_tags": ["journalists", "policy", "evidence-based-medicine"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Journalism fact-check", "example": "A nutrition claim circulating online — rate the underlying evidence."},
            {"scenario": "Policy evidence review", "example": "Briefing memo needs an evidence confidence rating before publication."},
            {"scenario": "Medical evidence appraisal", "example": "Clinical decision support — what's the actual strength of the recommendation."},
            {"scenario": "Investor due-diligence", "example": "Startup pitches a clinical claim; rate the evidence cited."},
        ],
        "when_not_to_use": "Skip for opinion / theoretical work — needs empirical evidence to rate. Skip when the model can't actually access the underlying studies (it can only rate what you tell it).",
        "full_prompt": """You are an evidence appraiser. Rate a body of evidence — design, sample, methods, conflicts, replication — then issue a tiered confidence rating.

INPUT
- Claim being evaluated: {claim}
- Evidence available (study by study with key details): {evidence}
- Domain: {domain}              (medicine / nutrition / education / economics / social-science / engineering)

OUTPUT

## 1. Claim restate
Restate the claim in PRECISE terms. If the original claim is vague, sharpen it. Note ambiguities.

## 2. Per-study appraisal
For each study:
- **Design:** RCT / cohort / cross-sectional / case-control / observational / experimental / mechanistic / animal / in-vitro / opinion
- **Sample size:** n = ___ ; representative of {domain}? (yes / no / unclear)
- **Method strength:** strong / adequate / weak (with 1-sentence reason)
- **Conflicts:** funding source, author conflicts, pre-registration status
- **Effect size:** numeric if available; otherwise qualitative (large / moderate / small / null)
- **Independent replication:** yes (cite) / no / mixed

## 3. Body-of-evidence patterns
Step back from individual studies:
- Does the effect REPLICATE across labs / settings?
- Do effect sizes SHRINK as study quality improves? (decline-effect = red flag)
- Are there OBVIOUS confounders that consistently apply?
- Is there a known PUBLICATION-BIAS pattern in this sub-field?

## 4. Confidence rating
Issue ONE of these tiers:
- **Robust** — RCTs or strong quasi-experimental, multiple labs, large effects survive quality controls.
- **Provisional** — Good direction-of-effect evidence; needs more replication or larger n.
- **Suggestive** — Pattern in data but mechanism unclear or replication mixed.
- **Inconclusive** — Conflicting findings across solid studies.
- **Weak** — Small n, single lab, observational, OR pre-clinical only.
- **Effectively no evidence** — Anecdote, opinion, mechanistic-only, or known-fraudulent corpus.

State the rating + 1-2 sentences on WHY.

## 5. What would move this rating
- ↑ Move UP to next tier: ___ (concrete: 'a pre-registered RCT with n>500 in non-Western sample').
- ↓ Move DOWN: ___ (e.g., 'failed pre-registered replication').

## 6. Common misuses of this evidence
- Where this evidence is OFTEN over-claimed: ___
- Where it's correctly used: ___
- 1-line headline a journalist could write that the evidence WOULDN'T support.

CRITICAL RULES
- A single RCT is not 'Robust' on its own. Robust requires REPLICATION across labs/settings.
- Sample size matters but representativeness matters more. n=10000 in one country is still WEIRD-sample.
- Mechanism plausibility ≠ evidence. Mechanism is a story, not a result.
- Conflicts don't auto-disqualify, but DO downgrade if not mitigated by pre-reg.
- If evidence is thin, say 'Weak' or 'Effectively no evidence' — don't soften.

EVIDENCE
{evidence}

Begin.""",
        "input_variables": [
            {"name": "claim", "type": "string", "description": "The claim being evaluated", "required": True, "example": "Intermittent fasting causes more fat loss than standard caloric restriction at the same total calories."},
            {"name": "evidence", "type": "string", "description": "Available studies with key details", "required": True, "example": "(1) Trepanowski 2017 RCT n=100 1yr: null. (2) Sutton 2018 RCT n=8 cross-over: TRF improved insulin sensitivity. (3) 6 observational cohort studies: positive effect..."},
            {"name": "domain", "type": "string", "description": "Domain", "required": True, "example": "nutrition / metabolic-health"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: precise claim restate, per-study appraisal table, body-of-evidence patterns, tiered rating, what would move it, common misuses.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Willing to issue 'Weak' or 'Effectively no evidence' ratings without softening."},
            {"model": "gpt-4o", "compatibility": "good", "notes": "Tends to soften ratings; re-pin: 'rate honestly even if rating is weak.'"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Strong on body-of-evidence patterns; can be vague on effect-size."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable but loses nuance on conflicts and decline-effect."},
        ],
        "variations": [
            {"label": "GRADE-aligned", "description": "Output in GRADE framework.", "prompt_snippet": "Map the confidence tier to GRADE (High / Moderate / Low / Very Low) and explain the GRADE downgrade reasons (RoB, inconsistency, indirectness, imprecision, publication bias)."},
            {"label": "Layperson summary", "description": "Plain-language summary of the rating.", "prompt_snippet": "After section 4, add a 'For a non-expert reader' paragraph in plain English — what the rating means without jargon."},
            {"label": "Domain-specific checks", "description": "Add domain checks.", "prompt_snippet": "For {domain}, add field-specific quality checks (e.g., for nutrition: 24-hour-recall vs biomarkers; for medicine: ITT vs per-protocol)."},
        ],
        "failure_modes": [
            {"symptom": "Over-rates evidence to seem balanced.", "fix": "Re-pin: 'rate based on evidence quality, not on social acceptability. Weak is weak.'"},
            {"symptom": "Ignores conflicts of interest.", "fix": "Force: 'each study MUST have funding source + author-conflict disclosure noted.'"},
            {"symptom": "Single-study Robust ratings.", "fix": "Hard rule: 'Robust requires independent replication across labs. One RCT = at most Provisional.'"},
            {"symptom": "Bland 'more research needed' conclusions.", "fix": "Require section 5 to specify 'a pre-registered study of design X with n>Y in population Z'."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["literature-review-gap-finder", "research-summary-for-non-experts", "fact-check-with-source-grading"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["evidence-rating", "grade-framework"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Will it hallucinate the GRADE rating?", "answer": "Only if you feed thin evidence. The prompt operates on what you give it. Don't ask it to rate a claim with no studies attached."},
            {"question": "Why isn't 'one big RCT' Robust?", "answer": "Single-lab effects often fail replication. Robust evidence survives across teams, populations, and settings. One trial buys you Provisional at best."},
            {"question": "What's 'decline-effect'?", "answer": "When effect sizes shrink as study quality improves — common in nutrition and psychology. It's a red flag that early excitement won't hold up."},
            {"question": "Can I use this for legal cases?", "answer": "It can scaffold the analysis, but legal admissibility (Daubert, Frye) has specific tests. Use the output as a draft for an expert witness, not the witness."},
        ],
        "meta_title": "Evidence-Quality Scorer — Research Prompt",
        "meta_description": "Rate evidence on design, sample, methods, conflicts, and replication. Issues a tiered confidence rating plus what would move it up or down.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "interview-transcript-theme-coder",
        "title": "Interview Transcript Theme Coder",
        "tldr": "Codes qualitative interview transcripts into themes with grounded quotes, frequency counts, and disconfirming evidence — outputs an audit trail an academic reviewer would accept.",
        "category": "research",
        "tags": ["qualitative", "interviews", "coding", "ethnography"],
        "best_for_tags": ["ux-researchers", "qual-academics", "policy-research"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "UX research synthesis", "example": "12 user interviews about a new checkout flow — extract themes with quote evidence."},
            {"scenario": "Qualitative academic study", "example": "20 ethnographic interviews — first-pass open coding before axial coding."},
            {"scenario": "Customer Voice synthesis", "example": "Customer-success team has 30 churn-interview transcripts; extract churn themes."},
            {"scenario": "Policy-research field interviews", "example": "Field interviews with case workers — surface barriers in a benefits-program rollout."},
        ],
        "when_not_to_use": "Skip when you haven't read the transcripts yourself — you need to validate themes against your domain knowledge. Skip for >20 transcripts in one pass; chunk it.",
        "full_prompt": """You are a qualitative research coder. Extract themes from transcripts with grounded evidence, frequency, and disconfirming cases.

INPUT
- Research question: {research_question}
- Transcripts (numbered, with participant ID): {transcripts}
- Coding approach: {coding_approach}        (open / axial / deductive-with-codebook / inductive)
- Existing codebook (if any): {codebook}

OUTPUT

## 1. Code list
Extract codes — short labels for concepts that recur. For each code:
- **Code:** short label
- **Definition:** 1 sentence
- **Inclusion criteria:** what counts
- **Exclusion criteria:** what doesn't (the boundary)

## 2. Theme map
Group related codes into themes. For each theme:
- **Theme name:** 2-4 words
- **Codes included:** ___
- **Frequency:** mentioned by N of M participants
- **Strength:** strong (multiple participants, multiple incidents per) / moderate (multiple participants, single incidents) / weak (few participants)

## 3. Grounded quotes
For each theme, provide 2-3 verbatim quotes with participant IDs:
> "P03: [quote]"
> "P07: [quote]"

CRITICAL: Quotes must be VERBATIM from input transcripts. If a quote doesn't exist literally, REPHRASE as paraphrase and label '(paraphrase, P03)'.

## 4. Disconfirming evidence
For each theme, what's the COUNTER-EVIDENCE in the transcripts?
- "Theme: 'users want speed.' Disconfirming: P05 explicitly said speed wasn't an issue, accuracy was."

If no disconfirming evidence exists, say so EXPLICITLY: "No disconfirming evidence in this corpus. Treat with caution — possible sampling effect."

## 5. Unique outliers
Participants who didn't fit any theme — what did they say? They might be:
- Edge cases worth a follow-up interview
- Signals of an emerging theme that didn't reach saturation
- Random noise

Label which.

## 6. Saturation check
Did the LAST 2-3 transcripts add new codes?
- If yes: saturation NOT reached, more transcripts needed.
- If no: saturation likely reached for this research question.

## 7. Reviewer audit trail
Things an academic / methodology reviewer would ask:
- "How did you decide what counts as theme X vs Y?"
- "Why did you treat P05 as outlier vs revising theme?"
- "What's the inter-rater reliability with the codebook?"

Answer each with the decisions you made.

CRITICAL RULES
- Quotes are VERBATIM or labeled paraphrase. NEVER invent dialogue.
- Frequency is COUNTED accurately. Don't inflate.
- Disconfirming evidence section is REQUIRED — confirmation bias is the #1 qual-research failure.
- Saturation check is HONEST: if you'd add new codes from one more transcript, say not-reached.
- Outliers are not noise by default — they're potential leads.

TRANSCRIPTS
{transcripts}

Begin.""",
        "input_variables": [
            {"name": "research_question", "type": "string", "description": "Research question driving the coding", "required": True, "example": "Why do small-business owners abandon our onboarding flow at step 4?"},
            {"name": "transcripts", "type": "string", "description": "Numbered transcripts with participant IDs", "required": True, "example": "P01: ...; P02: ...; P03: ..."},
            {"name": "coding_approach", "type": "string", "description": "Coding approach", "required": True, "example": "Inductive open coding"},
            {"name": "codebook", "type": "string", "description": "Existing codebook (optional)", "required": False, "example": "(none for first pass)"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: code list with inclusion/exclusion, theme map with frequency, grounded quotes, disconfirming evidence, outliers, saturation check, reviewer audit trail.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest on disconfirming evidence + reviewer audit; respects verbatim rule."},
            {"model": "gpt-4o", "compatibility": "good", "notes": "Solid; may invent quotes — re-pin verbatim rule + check."},
            {"model": "gemini-1.5-pro", "compatibility": "excellent", "notes": "Long context advantage; handles 15+ transcripts cleanly."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for <8 short transcripts. Disconfirming section thins out."},
        ],
        "variations": [
            {"label": "Codebook-deductive", "description": "Apply existing codebook.", "prompt_snippet": "Use the provided codebook strictly. New codes proposed only when existing ones don't fit — flag as proposed additions, not free codes."},
            {"label": "Multi-coder reliability", "description": "Produce 2 independent codings.", "prompt_snippet": "Code the transcripts TWICE under independent assumptions. Then run inter-coder agreement (% match) and surface disagreements for human resolution."},
            {"label": "Story-tier synthesis", "description": "Output stories + themes.", "prompt_snippet": "After section 7, output 3 representative participant stories (composite, anonymized) — used in stakeholder readouts."},
        ],
        "failure_modes": [
            {"symptom": "Invents quotes.", "fix": "Hard rule: 'every quote must be traceable to the input by surface text. Otherwise label paraphrase.' Run a verbatim check pass."},
            {"symptom": "Skips disconfirming section.", "fix": "Force: 'section 4 must have at least one entry per theme OR explicitly state \"no disconfirming evidence\" with sampling caveat.'"},
            {"symptom": "Inflates frequency counts.", "fix": "Require: 'frequency = count of distinct participants who explicitly mentioned. Mark inferred mentions separately.'"},
            {"symptom": "Treats outliers as noise.", "fix": "Re-pin: 'outliers are leads, not noise. Label which category each falls in.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["user-feedback-theme-extractor", "research-summary-for-non-experts", "competitor-feature-shipped-analysis"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["qualitative-coding", "thematic-analysis"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is this a replacement for human coding?", "answer": "No. It's a first-pass scaffold. Humans validate themes, check verbatim accuracy, and resolve outlier interpretation. The audit trail makes that easier."},
            {"question": "How many transcripts per pass?", "answer": "Up to ~15 for thorough coding. Gemini long-context can handle more for synthesis, but accuracy of disconfirming evidence drops past 20."},
            {"question": "Inter-rater reliability?", "answer": "Use the multi-coder variation to get a baseline. Real IRR requires independent human coders; the model can flag disagreements for human review."},
            {"question": "Can I use it for sensitive interviews?", "answer": "Yes if transcripts are pre-anonymized. Don't paste raw identifiable data; PII strip first."},
        ],
        "meta_title": "Interview Transcript Theme Coder — Qualitative Research Prompt",
        "meta_description": "Code interview transcripts into themes with grounded quotes, frequency counts, disconfirming evidence, and a reviewer audit trail.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "research-protocol-pre-mortem",
        "title": "Research Protocol Pre-Mortem",
        "tldr": "Reads a planned research protocol and surfaces what's most likely to break — sampling, instruments, attrition, analysis assumptions, ethics — BEFORE you collect data.",
        "category": "research",
        "tags": ["research-design", "pre-mortem", "methods", "study-planning"],
        "best_for_tags": ["academics", "ux-research", "clinical-trials"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Dissertation proposal defense prep", "example": "Submit protocol; pre-mortem surfaces what committee will challenge."},
            {"scenario": "Clinical trial protocol review", "example": "Before IRB submission, run the pre-mortem to catch protocol flaws."},
            {"scenario": "UX research planning", "example": "Before booking 20 user interviews, sanity-check the recruiting + script."},
            {"scenario": "Grant-funded study planning", "example": "Funded study about to launch — last-chance pre-mortem before sunk-cost kicks in."},
        ],
        "when_not_to_use": "Skip after data collection has started — most fixes require pre-data changes. Skip for very early ideation; use it after the protocol is real but pre-launch.",
        "full_prompt": """You are a research-methods skeptic. Your job is to find the most likely failure modes in a planned protocol BEFORE data collection.

INPUT
- Research question: {research_question}
- Hypothesis (if any): {hypothesis}
- Protocol (design, sampling, instruments, analysis plan): {protocol}
- Resources / constraints: {constraints}
- Domain: {domain}

OUTPUT

## 1. Protocol restate (in your words)
Restate the protocol in 5-8 bullets to confirm understanding. If anything's ambiguous, flag it here — ambiguity is its own risk.

## 2. The 7-failure pre-mortem
For each of the following, rate **likelihood (high / medium / low)** and **impact (kills-study / partial / minor)**, with a 2-3 sentence diagnosis.

### A. Sampling failure
What's the chance the sample won't represent the target population?
- Self-selection bias? Convenience sample dressed as random? WEIRD-sample creep?

### B. Instrument failure
Will the measurement instruments capture what you think they capture?
- Construct validity? Order effects? Reactivity? Translation / cultural fit?

### C. Attrition failure
Who will drop out and what's the differential effect?
- Long protocols, sensitive topics, low incentive → asymmetric attrition.

### D. Analysis-plan failure
Is the analysis pre-specified, and is it the RIGHT analysis?
- Garden of forking paths? Multiple comparisons? Wrong statistical test for the design?

### E. Ethical / consent failure
What's the chance you'll fail IRB / ethics review or harm participants?
- Vulnerable populations, deception, data security, withdrawal mechanism.

### F. Power / detection failure
With the planned sample size and effect size, what power do you have?
- Underpowered to detect the effect you care about?
- Powered for the wrong effect (e.g., main effect when interaction is theoretical interest)?

### G. Generalization failure
Even if it works, will it generalize beyond your sample?
- Single site, single cohort, single time point. What's the external-validity story?

## 3. The 'most likely failure' diagnosis
Pick the SINGLE highest-risk failure mode from the 7. State it in 1 sentence.

## 4. Pre-data fixes
For each failure scored high-likelihood OR high-impact, propose CONCRETE pre-data fixes:
- "Stratify sample on X to fix sampling failure"
- "Add pilot of 10 to test instrument before main study"
- "Pre-register analysis plan to fix garden-of-forking-paths"

Each fix names the COST (time, money, scope) honestly.

## 5. The 'kill criteria'
What result, observed mid-study, would tell you to STOP and re-design?
- "If attrition >40% by week 4, halt and redesign."
- "If pilot inter-rater reliability <0.7, re-train coders before main coding."

These are GO/NO-GO checks the study commits to in advance.

## 6. Committee / reviewer attack surface
Top 3 questions a hostile reviewer will ask. Don't answer them — surface them so the researcher answers BEFORE submission.

CRITICAL RULES
- Be SKEPTICAL. The goal is to find what breaks, not to validate the protocol.
- Rate honestly. If sampling is fine, say 'low likelihood, minor impact.' Don't manufacture risks.
- Every high-impact failure MUST have a pre-data fix proposed.
- Kill criteria are CONCRETE numbers, not vibes.

PROTOCOL
{protocol}

Begin.""",
        "input_variables": [
            {"name": "research_question", "type": "string", "description": "Research question", "required": True, "example": "Does a 6-week mindfulness app reduce self-reported anxiety in college students relative to a journaling control?"},
            {"name": "hypothesis", "type": "string", "description": "Hypothesis if formal", "required": False, "example": "App group will show ≥1.5 point reduction on GAD-7 vs control at 6wk."},
            {"name": "protocol", "type": "string", "description": "Protocol details", "required": True, "example": "Design: RCT 1:1, n=120 college freshmen, recruited via campus poster + email. Instrument: GAD-7 baseline + 6wk + 12wk follow-up. Analysis: ITT t-test of change scores..."},
            {"name": "constraints", "type": "string", "description": "Resources / constraints", "required": True, "example": "$8k budget, 1 PhD-student researcher, 9-mo dissertation timeline."},
            {"name": "domain", "type": "string", "description": "Domain", "required": True, "example": "Clinical psychology / wellness intervention"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: protocol restate, 7-failure pre-mortem with likelihood/impact, single highest risk, pre-data fixes with cost, kill criteria, committee attack surface.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest on garden-of-forking-paths + power analysis nuance."},
            {"model": "gpt-4o", "compatibility": "good", "notes": "Solid; can soft-pedal high-risk findings — re-pin skeptic framing."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Long protocol context handled well; weaker on kill criteria specificity."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple protocols; thins on multi-arm trials."},
        ],
        "variations": [
            {"label": "IRB-focused", "description": "Lean into ethics + consent risks.", "prompt_snippet": "Weight section E (Ethical/consent) heavier. Add an IRB-narrative draft for the highest-risk consent / withdrawal failure modes."},
            {"label": "Quant power analysis", "description": "Output a power calc.", "prompt_snippet": "In section F, run a back-of-envelope power calc with the planned n and effect size; show MDE."},
            {"label": "Qual-research pre-mortem", "description": "Reframe for qualitative.", "prompt_snippet": "Replace sections D and F with: 'Saturation risk' (will you reach theme saturation in planned n?) and 'Reflexivity risk' (where does the researcher's positionality bias themes?)."},
        ],
        "failure_modes": [
            {"symptom": "Validates the protocol instead of attacking it.", "fix": "Re-pin: 'pretend you're the harshest reviewer on the dissertation committee. Steelman every failure mode.'"},
            {"symptom": "Vague pre-data fixes.", "fix": "Force: 'each fix names a CONCRETE change + the cost in time/money/scope.'"},
            {"symptom": "Kill criteria are vibes ('if it's not working').", "fix": "Demand: 'kill criteria specify a metric + threshold + decision rule.'"},
            {"symptom": "Misses power-analysis problems.", "fix": "Add: 'state the MDE given the planned n and alpha; flag if MDE > realistic effect.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["evidence-quality-scorer", "literature-review-gap-finder", "go-no-go-decision-meeting-prep"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["pre-registration", "internal-validity"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "When in the process should I run this?", "answer": "After the protocol is real but BEFORE recruitment opens. Late enough for the design to be concrete; early enough to actually fix what breaks."},
            {"question": "Does it replace IRB review?", "answer": "No — IRB has formal authority. This is a pre-IRB sanity check to fix problems you'd otherwise be asked to fix during review."},
            {"question": "Can I trust the power calc?", "answer": "Treat it as directional. Run a real power calc (G*Power, R pwr package) before final commitment. The variation flag surfaces order-of-magnitude problems."},
            {"question": "Why so much focus on kill criteria?", "answer": "Studies without pre-committed kill criteria suffer sunk-cost bias. Pre-commitment makes mid-study honesty cheaper."},
        ],
        "meta_title": "Research Protocol Pre-Mortem — Methods Prompt",
        "meta_description": "Pre-mortem a research protocol across 7 failure modes with pre-data fixes and kill criteria — before data collection starts.",
        "version": "v2.0",
        "release_status": "stable",
    },
]
