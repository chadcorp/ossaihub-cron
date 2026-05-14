"""Research prompts — batch 2."""

RECORDS = [
    {
        "slug": "user-interview-question-guide",
        "title": "User Interview Question Guide From Research Goal",
        "tldr": "Builds a 30-45 minute user interview guide from a research goal: opener, 3-4 thematic sections, behavior-first questions, and a ‘red-flag’ list of questions to NOT ask.",
        "category": "research",
        "tags": ["user-research", "interviews", "discovery", "qualitative"],
        "best_for_tags": ["product-research", "user-discovery", "jtbd"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Pre-feature user discovery", "example": "‘Do our power users want collaboration features?’ → 40-min guide focused on workflow, not features."},
            {"scenario": "Churn diagnosis", "example": "Talk to 8 churned customers; consistent guide surfaces patterns."},
            {"scenario": "Buyer-persona refinement", "example": "Validate hypothesized persona via questions that probe motivations."},
            {"scenario": "Pricing research", "example": "Willingness-to-pay without asking ‘how much would you pay?’"},
        ],
        "when_not_to_use": "Skip for usability testing (different format — task-based, not conversational). Skip for quantitative research (use surveys).",
        "full_prompt": """You are a user research lead designing an interview guide.

INPUT
- Research goal: {research_goal}
- Target participant: {target_participant}
- Interview length: {interview_length_minutes}
- Interview format: {format}                  (video, phone, in-person)
- What you already know (don't re-ask): {known_context}

OUTPUT

## 1. Opening (5 min)
- Welcome line + setup permissions (recording, confidentiality).
- ‘About me’ — researcher's brief intro.
- Throwaway warm-up question to ease the participant in.

## 2. Context & background (5-10 min)
3-5 questions establishing the participant's situation. NOT about your product yet:
- Their role / company / day-to-day
- The general problem space they live in

## 3. The heart (50-60% of interview)
3-4 thematic sections. Each has 2-4 questions. Sections should map to the research goal but not lead the participant.

Question patterns to use:
- "Walk me through the last time you [activity]." (behavioral specifics)
- "What were you doing right before this?"
- "What did you do next?"
- "Tell me about a time when this didn't work."

Patterns to AVOID:
- "Would you use a feature that...?" (hypothetical → unreliable)
- "Do you like X?" (yes/no, low signal)
- "How important is X to you on a scale of 1-10?" (Likert questions hide actual behavior)
- "Don't you think...?" (leading)

## 4. Specific probes (15-20% of interview)
2-4 questions that test specific hypotheses you have. Frame them as opens, not closeds.

## 5. Closing (5 min)
- "What didn't I ask about that I should have?"
- "Who else should I talk to?"
- Compensation / next steps.

## 6. Red-flag questions to NOT ask
A list of questions a researcher might be tempted to ask but shouldn't:
- Anything that hints at your hypothesis
- Anything that puts the participant in a hypothetical
- Anything with corporate jargon they wouldn't use
- Anything that's secretly a sales question

## 7. Listening cues
3-5 things to listen FOR during the interview:
- Specific phrases that reveal underlying frames ("I just need to..." vs "I really want to...")
- Workarounds the participant has invented
- Moments where they get specific without being asked

## 8. After-interview synthesis prompts
3-4 questions to answer immediately after the interview ends:
- What surprised me?
- What contradicted my assumptions?
- What did they NOT say that I expected?

RULES
- Total questions ~12-18 for a 45-min interview. More than that, you're rushing.
- Behavioral over hypothetical (3-to-1 ratio at minimum).
- Specific recent moments over generalizations ("last time" > "usually").
- Open-ended over yes/no.
- Don't lead the witness. The participant should not be able to guess what answer you want.

Begin.""",
        "input_variables": [
            {"name": "research_goal", "type": "string", "description": "What you're trying to learn", "required": True, "example": "Understand how data engineers currently handle pipeline incident response; identify the biggest unmet need."},
            {"name": "target_participant", "type": "string", "description": "Who you're interviewing", "required": True, "example": "Senior data engineers at companies 50-500 employees, on call rotation"},
            {"name": "interview_length_minutes", "type": "integer", "description": "Length in minutes", "required": True, "example": "45"},
            {"name": "format", "type": "string", "description": "Interview format", "required": False, "example": "Video, recorded with consent"},
            {"name": "known_context", "type": "string", "description": "What you already know — don't re-ask", "required": False, "example": "They use Datadog + PagerDuty; we know that already from surveys."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "8 sections: opening, context, heart (themes + questions), probes, closing, red-flag questions, listening cues, after-interview prompts.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on behavior-first phrasing; identifies leading questions accurately."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes slips into Likert-scale questions — re-pin avoidance."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; ‘red-flag questions’ section can be generic."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Defaults to hypothetical phrasing; needs explicit anti-pattern reminder."},
        ],
        "variations": [
            {"label": "Diary study follow-up", "description": "After diary collection.", "prompt_snippet": "Add: ‘interview is post-diary; questions probe specific entries from their diary, not general behavior.’"},
            {"label": "Multi-stakeholder", "description": "Interview 2 people from same org.", "prompt_snippet": "Add: ‘design for two participants from same org (e.g., engineer + manager); add comparative questions revealing perspective differences.’"},
            {"label": "JTBD-focused", "description": "Jobs-to-be-done framework.", "prompt_snippet": "Frame all thematic sections around JTBD: triggering event, prior attempts, struggles, hire/fire moments."},
        ],
        "failure_modes": [
            {"symptom": "Hypothetical questions ‘Would you use...’", "fix": "Re-pin: ‘behavioral, past-tense, specific. No hypotheticals.’"},
            {"symptom": "Too many questions for the time slot.", "fix": "Add: ‘count questions; max 1 per 2.5 minutes of interview length.’"},
            {"symptom": "Leading questions.", "fix": "Add: ‘red-flag questions section must flag anything that hints at your hypothesis.’"},
            {"symptom": "Skips listening cues.", "fix": "Force section 7 to be concrete: name 3-5 specific phrases/behaviors to listen for."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["user-research-synthesizer", "interviewer-persona-deep-questions"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["user-research", "qualitative-research", "jtbd"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why no Likert questions?", "answer": "Likert scales feel scientific but mostly capture self-report bias. Behavioral questions ‘walk me through the last time’ reveal what people actually do — different from what they think they do."},
            {"question": "How many interviews until I have signal?", "answer": "Classic answer is 5-8 for qualitative saturation per persona. For complex behaviors, 10-15. If everyone says different things at 8, your participants aren't uniform — consider segmenting."},
            {"question": "Should I share the guide with participants in advance?", "answer": "Generally no — it shapes their answers. Share the broad topic and time, not the specific questions."},
        ],
        "meta_title": "User Interview Question Guide From Research Goal",
        "meta_description": "Build a 30-45 min interview guide: opener, themed sections with behavioral questions, listening cues, and red-flag questions to NOT ask.",
    },
    {
        "slug": "literature-review-by-position",
        "title": "Literature Review By Position (Not By Source)",
        "tldr": "Reframes a literature review around POSITIONS / arguments, not sources. Each section is a claim with supporting + opposing sources, gaps, and an honest takeaway about what the field actually knows.",
        "category": "research",
        "tags": ["literature-review", "synthesis", "academic", "research"],
        "best_for_tags": ["thesis-writing", "research-synthesis", "field-mapping"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Thesis chapter on a contested topic", "example": "10+ sources on ‘does X cause Y’ — synthesize by position, not by paper."},
            {"scenario": "Industry analyst report", "example": "‘What's the state of vector databases in 2025?’ — surface positions, not just summarize papers."},
            {"scenario": "Pre-research framing", "example": "Before doing primary research, map the existing debate to find genuine gaps."},
            {"scenario": "Policy memo", "example": "Position-based review serves decision-making better than chronological summary."},
        ],
        "when_not_to_use": "Skip for topics with consensus (just cite the consensus). Skip when sources are too few (need 5+ to identify positions). Skip for systematic reviews requiring strict PRISMA methodology.",
        "full_prompt": """You are a research synthesizer. You'll build a literature review BY POSITION, not by source.

INPUT
- Research question: {research_question}
- Sources (papers, articles, reports): {sources}
- Audience (academic / practitioner / policy): {audience}

OUTPUT

## 1. The question
Restate the research question; identify 3-5 sub-questions if it has multiple parts.

## 2. Map of positions
For each sub-question, identify the 2-5 distinct POSITIONS that exist in the literature.

A position is a defensible answer or stance, not a source. Multiple sources may share a position. Some sources may straddle positions.

For each position:
### Position N: <one-sentence claim>
- Sources defending this position: cite each with 1-line summary.
- Strongest argument for: what makes this position compelling?
- Weakest spot: where does this position have gaps or contradictions?
- Sources challenging or qualifying: cite each.

## 3. Where the field agrees (consensus)
2-4 specific claims most positions accept.

## 4. Where the field disagrees (live debate)
2-4 specific claims where positions diverge sharply. Be specific — "they disagree about X mechanism, not Y outcome."

## 5. Gaps the literature doesn't address
3-5 questions that NONE of the positions answer or even ask. These are publishable / actionable.

## 6. Honest takeaway
What does the field actually know about {research_question}? Phrase as a researcher would: confidence levels per claim.
- "Well-established: ..."
- "Probable but contested: ..."
- "Unknown: ..."

## 7. For the reader's next step
If audience is practitioner: which position is most usable today?
If academic: what's the publishable opening?
If policy: what's the defensible-now claim that won't be contradicted soon?

RULES
- Cite specific sources; never say "many studies" or "research shows" without citing.
- A position is what the AUTHORS argue — don't invent positions sources don't actually hold.
- When sources disagree, name the disagreement explicitly; don't paper over.
- Honest about confidence — don't pretend more is known than is.
- If a position has only one source supporting it, say so — that's information.

SOURCES
{sources}

Begin.""",
        "input_variables": [
            {"name": "research_question", "type": "string", "description": "The question being reviewed", "required": True, "example": "Does retrieval-augmented generation reduce hallucinations in domain-specific LLM applications?"},
            {"name": "sources", "type": "string", "description": "List of sources with brief summaries", "required": True, "example": "1. Lewis et al. 2020: introduces RAG; claims hallucination reduction. 2. Mialon et al. 2023: argues RAG only helps when retrieved context is genuinely relevant..."},
            {"name": "audience", "type": "string", "description": "Reader type", "required": True, "example": "Practitioners (ML engineers deciding whether to use RAG)"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: question, position map, consensus, disagreements, gaps, honest takeaway, reader's next step.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on distinguishing positions from sources; honest about confidence."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes invents positions sources don't actually hold."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; gaps section can be generic."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Defaults to source-by-source summary; needs explicit reframing."},
        ],
        "variations": [
            {"label": "Field map", "description": "Add a 2x2 positioning chart.", "prompt_snippet": "Add: ‘output a 2x2 chart positioning each source on two dimensions; label axes from the field's tensions.’"},
            {"label": "Timeline view", "description": "Track positions over time.", "prompt_snippet": "Add: ‘also note how positions have evolved — which claims have weakened, which strengthened, since first proposed.’"},
            {"label": "Pre-research framing", "description": "What study would resolve open questions.", "prompt_snippet": "After section 5 (gaps), add: ‘for each gap, propose the SPECIFIC study that would resolve it — design, measure, expected effect size.’"},
        ],
        "failure_modes": [
            {"symptom": "Output is source-by-source summary.", "fix": "Re-pin: ‘POSITIONS, not papers. A position is a claim; multiple papers share one position.’"},
            {"symptom": "Invents positions sources don't hold.", "fix": "Add: ‘every position must cite sources that actually defend it; if no real source defends a position, it's not a position in the literature.’"},
            {"symptom": "Confidence levels missing.", "fix": "Force section 6 explicit ladder: well-established / probable but contested / unknown."},
            {"symptom": "Gaps section is generic.", "fix": "Add: ‘gaps must be specific questions or claims, not topic areas (‘more research needed on X’ doesn't count).’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["literature-review-synthesizer", "competitive-teardown"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["literature-review", "synthesis", "epistemology"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Position vs claim — what's the difference?", "answer": "A position is a defensible stance someone in the field actively defends. A claim is a single statement. A position has supporting arguments and known critics; an isolated claim doesn't."},
            {"question": "How many sources is enough?", "answer": "5-8 minimum for position-based synthesis; <5 and you're really doing a paper review, not a literature review. 15-25 is a thorough review chapter."},
            {"question": "What if all sources agree?", "answer": "Then the field has consensus on that question. Move to the unanswered question downstream — that's where the live debate is."},
        ],
        "meta_title": "Literature Review By Position (Not By Source)",
        "meta_description": "Synthesize literature by POSITIONS, not sources: map debates, identify consensus + disagreement + gaps, honest takeaway with confidence levels.",
    },
    {
        "slug": "research-protocol-from-question",
        "title": "Research Protocol From a Question",
        "tldr": "Designs a complete research protocol: hypotheses, variables, methodology selection, sample size, threats to validity, and timeline. Calibrated for industry research, not academic.",
        "category": "research",
        "tags": ["research-protocol", "methodology", "experiment-design", "validity"],
        "best_for_tags": ["industry-research", "ux-research", "applied-research"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Pre-research planning", "example": "Question is broad; protocol surfaces methodology choice, sample size, and what we can/can't claim."},
            {"scenario": "Multi-method study", "example": "Interviews + survey + behavioral data — protocol coordinates them."},
            {"scenario": "Vendor research project", "example": "External research firm sees a clear protocol; reduces scope creep and ambiguity."},
            {"scenario": "Pre-funding research design", "example": "Investor / leadership wants confidence in methodology before approving research budget."},
        ],
        "when_not_to_use": "Skip for very small exploratory studies (just do them). Skip for academic publication targets — those need stricter protocols (IRB, pre-registration, PRISMA where relevant).",
        "full_prompt": """You are designing a research protocol for an industry research question.

INPUT
- Research question: {research_question}
- Stakeholder context (what decision this informs): {decision_context}
- Time/budget constraints: {constraints}
- Available data sources: {available_data}
- Team capacity: {team_capacity}

OUTPUT — protocol document

## 1. Refined research question(s)
Sharpen the input question. If it's compound, split. If it's ambiguous, propose 2-3 alternative phrasings and note the differences in what they'd reveal.

## 2. Hypotheses
Specific testable claims (or expected patterns). Each:
- Null: what would have to be true for the hypothesis to be FALSE?
- Alternative: what we expect to find.
- Direction: does the hypothesis predict an effect direction, or just non-zero?

## 3. Methodology choice
Select the right method(s) and JUSTIFY:
- Quant survey: large N, generalizable, weak on why.
- Qual interview: small N, deep on why, weak on prevalence.
- Behavioral data: actual behavior, biased by what's instrumented.
- A/B experiment: causal claim, requires control.
- Mixed-methods: most informative, costliest.

Pick ONE primary method; secondary if budget allows.

## 4. Variables
- Independent (what we manipulate or compare).
- Dependent (what we measure).
- Confounders (what could distort the relationship).
- Mitigation for top 2-3 confounders.

## 5. Sample
- Who: target population.
- How many: sample size calculation (or stated rationale if statistical math doesn't apply).
- How recruited: source + filters.
- Sampling biases this introduces and mitigations.

## 6. Instruments / protocol
For each method:
- Interview guide / survey / logging spec / experiment design.
- Estimated time per participant.
- Pilot strategy (1-3 pilot runs before full).

## 7. Analysis plan
PRE-COMMIT to:
- The analyses to run (don't fish post hoc).
- The threshold for ‘meaningful effect.’
- What we'll do if results are null.

## 8. Threats to validity
Three buckets:
- Internal: does our design support causal claims?
- External: will findings generalize beyond our sample?
- Construct: are we measuring what we think we are?
2-3 specific threats per bucket + mitigation.

## 9. Timeline + cost
- Calendar weeks
- People-time
- Direct costs (incentives, tools, vendors)

## 10. What this research CANNOT tell us
3-5 specific limits of the protocol. Important for stakeholders to know upfront.

RULES
- Industry-grade rigor, not academic. We're informing decisions, not publishing.
- Be honest about what's achievable in the time/budget given.
- Pre-commit analysis plan to prevent post-hoc fishing.
- Address validity threats specifically, not generically.

Begin.""",
        "input_variables": [
            {"name": "research_question", "type": "string", "description": "Research question", "required": True, "example": "Does showing product onboarding videos increase 30-day retention?"},
            {"name": "decision_context", "type": "string", "description": "What decision this informs", "required": True, "example": "Whether to invest engineering + production resources in building an onboarding video system."},
            {"name": "constraints", "type": "string", "description": "Time/budget limits", "required": True, "example": "8 weeks total, $15k budget, 1 researcher full-time"},
            {"name": "available_data", "type": "string", "description": "Data sources we already have", "required": False, "example": "User sign-up + retention data going back 18 months. CSAT surveys quarterly. Can deploy in-app surveys."},
            {"name": "team_capacity", "type": "string", "description": "Who's doing the work", "required": False, "example": "1 senior UX researcher, part-time analyst (10 hrs/week)"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "10 sections covering questions, hypotheses, methodology, variables, sample, instruments, analysis plan, validity threats, timeline/cost, limits.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on methodology justification and pre-commitment discipline."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes overstates sample-size confidence."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; validity threats can be generic."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Methodology selection sometimes lazy; needs explicit comparison."},
        ],
        "variations": [
            {"label": "RCT-specific", "description": "Random controlled trial design.", "prompt_snippet": "Add: ‘design as a proper RCT — random assignment, control group, pre-registration of analysis plan. Specify randomization mechanism.’"},
            {"label": "Diary study", "description": "Multi-day participant logs.", "prompt_snippet": "Replace single-instrument with: ‘14-day diary study with daily prompts + 2 deep-dive interviews per participant.’"},
            {"label": "Combined quant + qual", "description": "Mixed-methods design.", "prompt_snippet": "Add: ‘mixed-methods: quant survey to N=300 + qual interviews with N=12 outliers. Integration plan for combining findings.’"},
        ],
        "failure_modes": [
            {"symptom": "Methodology selected without justification.", "fix": "Re-pin: ‘methodology section must compare 2+ options and explain choice; not just propose one.’"},
            {"symptom": "Analysis plan vague.", "fix": "Add: ‘list the specific tests/comparisons before starting; vagueness invites post-hoc fishing.’"},
            {"symptom": "Validity threats are clichés.", "fix": "Force specificity: ‘each threat must be SPECIFIC to this design — what exactly could distort what here.’"},
            {"symptom": "‘CANNOT tell us’ section empty.", "fix": "Add: ‘every protocol has limits; list at least 3 specific things this design can't determine.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["go-to-market-experiment-design", "user-interview-question-guide"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["research-protocol", "validity", "methodology"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Industry vs academic protocols?", "answer": "Industry serves decisions; academic serves publications. Industry can afford lower N if directional answer is enough; academic needs power for inferential statistics. The prompt is industry-tuned."},
            {"question": "What if budget is too small for the right method?", "answer": "Protocol surfaces that. Better to know upfront that available budget supports only directional qual than to do an under-powered quant study."},
            {"question": "Should I pre-register?", "answer": "For high-stakes industry research with public commitments (papers, regulatory filings): yes. For internal product decisions: pre-commit to stakeholders (less formal) but don't publicly register."},
        ],
        "meta_title": "Research Protocol From a Question — Prompt",
        "meta_description": "Full research protocol: hypotheses, methodology, variables, sample size, validity threats, analysis plan, timeline. Industry-grade rigor.",
    },
    {
        "slug": "thematic-coding-from-transcripts",
        "title": "Thematic Coding From Qualitative Transcripts",
        "tldr": "Codes qualitative transcripts (interviews, support tickets, reviews) into themes with frequency, exemplar quotes, and distinguishes saturated themes from singletons that might still matter.",
        "category": "research",
        "tags": ["thematic-analysis", "qualitative", "coding", "synthesis"],
        "best_for_tags": ["user-research-synthesis", "interview-analysis", "qualitative"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Synthesizing 8 user interviews", "example": "Find recurring themes + the powerful singletons that hint at edge segments."},
            {"scenario": "Quarterly support ticket review", "example": "100+ tickets coded; themes feed into product backlog and KB priorities."},
            {"scenario": "App store review analysis", "example": "Code 200 reviews into themes; track which themes shift over versions."},
            {"scenario": "Open-ended survey responses", "example": "Code free-text answers from 500-person survey."},
        ],
        "when_not_to_use": "Skip for tiny samples (<5 transcripts) — manual reading is fine. Skip when you need quantification — thematic coding shows what's there, not how prevalent at scale.",
        "full_prompt": """You are coding qualitative transcripts into themes. Goal: surface what's actually being said, not what you expect to find.

INPUT
- Transcripts (interviews / tickets / reviews): {transcripts}
- Research question or analytical lens: {research_question}
- Audience for the analysis: {audience}

PROCESS

## Pass 1: Open coding
Read each transcript. Tag every interesting unit (a sentence or two that says something specific). Don't try to be tidy yet.

Output a TAG LIST with:
- Tag name (short, descriptive)
- Definition (1 line)
- Count: how many transcripts contained it
- Exemplar quote (verbatim, attributed to transcript-N)

You should have 30-80 tags after this pass.

## Pass 2: Theme clustering
Group related tags into themes. A theme:
- Captures a meaningful pattern across multiple transcripts.
- Has a clear name (avoid generic ‘user satisfaction’).
- Distinguishable from other themes — orthogonal.

For each theme:

### Theme N: <name>
- Definition: 1-2 sentences capturing the underlying pattern.
- Tags included: list which open-coding tags this theme rolls up.
- Frequency: in how many transcripts does this theme appear?
- Saturation: did new tags stop appearing in this theme after the 5th transcript? (Saturated themes are robust; thin themes need more data.)
- Two exemplar quotes (verbatim): show the range.

Aim for 5-9 themes. Fewer = too coarse. More = clustering hasn't done its job.

## Pass 3: Singletons that matter
Identify 2-4 SINGLETON tags (appeared in 1-2 transcripts) that might still be important — usually surface edge segments or weak signals worth following up.

For each singleton:
- The tag and quote.
- Why it might matter (compelling, unexpected, hints at unmet need).

## Pass 4: What's NOT here
3-4 things you EXPECTED to find based on the research question but didn't see in the data:
- Did participants not mention X?
- Are there obvious themes that didn't actually emerge?
- This is information — sometimes the loudest finding is the silence.

## Pass 5: Synthesis paragraph
2-3 sentence summary of what these transcripts collectively say. Honest about confidence given sample size.

RULES
- Exemplar quotes are VERBATIM (minus PII).
- A theme requires support from at least 3 transcripts unless explicitly flagged as ‘thin.’
- Don't smooth disagreement — if transcripts contradict each other, that's a theme of its own.
- Resist confirmation: themes should emerge from data, not from your research question.

TRANSCRIPTS
{transcripts}

Begin Pass 1.""",
        "input_variables": [
            {"name": "transcripts", "type": "string", "description": "Transcripts of interviews / tickets / reviews", "required": True, "example": "Transcript 1: [interview...]\\nTranscript 2: [interview...]"},
            {"name": "research_question", "type": "string", "description": "Analytical lens", "required": True, "example": "Why do data engineers churn from our product after month 2?"},
            {"name": "audience", "type": "string", "description": "Who will read the analysis", "required": False, "example": "Product team + leadership for retention strategy meeting"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Five passes: open codes (30-80 tags), themes (5-9 with definitions/exemplars), singletons-that-matter, what's-not-here, synthesis paragraph.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on emergent themes; doesn't over-fit to the research question."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes confirmation-biased to research question."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; singleton identification can be shallow."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to produce 3-4 broad themes; needs explicit minimum count."},
        ],
        "variations": [
            {"label": "Codebook-driven", "description": "Use pre-defined codes.", "prompt_snippet": "Add: ‘also code against this PROVIDED codebook: {existing_codes}. Note where data fits or contradicts the codebook.’"},
            {"label": "Comparative", "description": "Two groups of transcripts.", "prompt_snippet": "Replace single set with: ‘group A vs group B transcripts; show themes unique to each plus shared themes.’"},
            {"label": "Frequency table", "description": "Quantified theme presence.", "prompt_snippet": "Add: ‘output a final table: themes × transcripts, marking presence/absence per cell.’"},
        ],
        "failure_modes": [
            {"symptom": "5 themes that are basically the same.", "fix": "Re-pin: ‘themes must be orthogonal; if you can't differentiate, collapse.’"},
            {"symptom": "Exemplar quotes paraphrased.", "fix": "Add: ‘quotes are VERBATIM; if you can't quote, the theme isn't well-supported by the data.’"},
            {"symptom": "Confirmation bias toward research question.", "fix": "Add: ‘open coding pass treats research question as one lens among many; don't filter out tags that don't fit.’"},
            {"symptom": "‘What's NOT here’ section empty.", "fix": "Force: ‘what's expected but absent is itself a finding; list 3-4 specifically.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["user-research-synthesizer", "user-interview-question-guide"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["thematic-analysis", "qualitative-coding"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How many transcripts is enough?", "answer": "5-8 for qualitative saturation per segment. If you have 3 segments (e.g., users, churned users, never-converts), aim for 5-8 each. Below that, treat findings as directional."},
            {"question": "Saturated vs thin themes?", "answer": "Saturated = new transcripts stop adding new content within the theme. Thin = only 2-3 transcripts contain the theme. Saturated themes are robust; thin ones are flagged for further data collection."},
            {"question": "What about negative cases?", "answer": "When transcripts contradict the dominant theme, the contradiction is a theme. Don't average it away — name it explicitly."},
        ],
        "meta_title": "Thematic Coding From Qualitative Transcripts — Prompt",
        "meta_description": "Code qualitative transcripts into themes via 5-pass process: open codes, theme clustering, singletons-that-matter, what's-not-here, synthesis.",
    },
]
