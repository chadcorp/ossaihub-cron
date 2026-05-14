"""Research prompt library — v2 authored (2026-05-14)."""

RECORDS = [
    {
        "slug": "literature-review-synthesizer",
        "title": "Literature Review Synthesizer (claim + evidence + gap)",
        "category": "research",
        "tldr": "Synthesize 5-30 papers into a literature review with claim-evidence-gap structure, conflicting findings flagged, and an explicit 'what we don't know yet' section.",
        "tags": ["literature-review", "research", "synthesis"],
        "best_for_tags": ["academic", "research", "meta-analysis"],
        "difficulty_tier": "advanced",
        "full_prompt": (
            "You synthesize academic literature for researchers. Be rigorous about claim → evidence → gap structure; surface conflicting findings explicitly; don't paper over uncertainty.\n\n"
            "INPUTS:\n"
            "- papers: list of {citation, abstract, key_findings, methodology, sample_size, year, doi (optional)}\n"
            "- research_question: the question this review answers\n"
            "- scope_filters (optional): year range, methodology types, sample types\n\n"
            "PROCEDURE:\n"
            "1. For each paper, extract: central claim, evidence type (RCT/observational/meta-analysis/theoretical), strength of evidence (strong/moderate/weak based on sample + methodology).\n"
            "2. Cluster papers into 3-6 thematic claims relevant to research_question.\n"
            "3. For each theme: list supporting papers, conflicting papers (if any), and the gap (what neither side has answered).\n"
            "4. Rank themes by evidence strength + relevance to research_question.\n"
            "5. Surface 'orphan findings' — interesting results from a single paper that don't fit themes but matter.\n"
            "6. End with 'What we don't know yet' — 3-5 explicit unanswered questions, each tied to a specific limitation in the existing literature.\n\n"
            "OUTPUT FORMAT (markdown): Research question · 3-6 thematic claims (each: synthesis + evidence + gap) · Conflicting findings · Orphan findings · Unanswered questions · Methodology note (search strategy).\n\n"
            "CITATION FORMAT: (Author year, paper #N from input). Don't invent citations.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "papers", "type": "list[Paper]", "description": "5-30 papers with metadata + findings", "required": True, "example": "[{citation:'Smith 2023', abstract:'...', key_findings:['X increases Y by 30%'], methodology:'RCT n=240', sample_size:240, year:2023}]"},
            {"name": "research_question", "type": "string", "description": "What this review answers", "required": True, "example": "Does spaced repetition improve long-term retention in adult learners?"},
            {"name": "scope_filters", "type": "ScopeFilter", "description": "Filters to apply", "required": False, "example": "{year_range:'2018-2025', methodology_types:['RCT','meta-analysis'], sample_min:100}"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Research question\nDoes spaced repetition improve long-term retention in adult learners?\n\n## Theme 1: Spaced retrieval beats massed practice for declarative knowledge\nSupported by 7 papers (5 RCT, 2 meta-analyses). Effect size d=0.45-0.78 across studies.\n- Smith 2023 (RCT, n=240): +30% retention at 30 days\n- Jones 2022 (meta, k=18): d=0.65 [0.52, 0.78]\n**Gap:** All studies measure 30-day retention; none measure 1-year+\n\n## Theme 2: Effect size depends on initial encoding quality\n[..]\n\n## Conflicting findings\n- Wong 2024 found NO effect at small sample (n=42). Likely underpowered, but worth noting.\n\n## What we don't know yet\n1. Does the effect persist past 6 months? No studies in the 6mo-2yr window.\n2. Does it work for procedural skills? All studies measure declarative.\n3. Optimal spacing interval for adults >50? All samples skew 18-30."},
        "use_cases": [
            {"scenario": "PhD literature review", "example": "Student has 30 papers in Zotero; feeds metadata + key findings; gets the v1 chapter."},
            {"scenario": "Industry research report", "example": "Analyst writing a market report on 'AI in healthcare'; synthesizes 20 vendor case studies + 10 academic papers."},
            {"scenario": "Pre-grant proposal", "example": "Need the 'state of the field' section quickly; this prompt produces the structure to refine."},
            {"scenario": "Meta-analysis prep", "example": "Before running a quantitative meta-analysis, this prompt surfaces which themes have enough studies to pool."},
        ],
        "when_not_to_use": "Don't use as substitute for reading papers — the prompt synthesizes what you tell it. Bad inputs → bad output. Also skip for fields where 'consensus' shifts often (active controversies).",
        "few_shot_examples": [
            {
                "input": "Research question: 'Does intermittent fasting improve metabolic markers?' 5 papers: 3 RCT (positive), 1 meta (mixed), 1 observational (negative).",
                "output": "## Theme 1: Short-term metabolic improvement (12 weeks)\nAll 3 RCTs showed improvements in fasting glucose and HDL. Effect size moderate.\n**Gap:** None measured beyond 12 weeks.\n\n## Conflicting findings\nObservational study (Lee 2024, n=8000) found null effect. Likely confounded by self-selection — IF adherers may differ on lifestyle factors.\n\n## What we don't know yet\n1. Does the effect persist past 12 weeks (likely adaptation)?\n2. Does it work without caloric restriction (3/3 RCTs included caloric deficit)?\n3. Long-term cardiovascular events — no studies have follow-up >1 year.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best for nuanced 'gap' identification."},
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Reliable default."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Sometimes papers over the gap section."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; verify gap claims manually."},
        ],
        "variations": [
            {"label": "Conflicting-only mode", "description": "Show only where studies disagree.", "prompt_snippet": "Skip theme synthesis. Output only conflicting-findings section + analysis of why studies disagree (methodology, sample, definition)."},
            {"label": "Methodology-focused", "description": "Group by study type.", "prompt_snippet": "Cluster by methodology (RCT vs observational vs meta-analysis). Compare across — RCTs say X, observational says Y; what does the asymmetry suggest?"},
            {"label": "Quick-summary mode", "description": "1-paragraph summary, no themes.", "prompt_snippet": "Output: 1-paragraph synthesis (3-5 sentences) + bullet list of 3 unanswered questions. For executive readers."},
        ],
        "failure_modes": [
            {"symptom": "Invents citations not in input", "fix": "Strict rule: only cite papers from the input list, by paper # if needed"},
            {"symptom": "Glosses over conflicting findings ('most studies agree...')", "fix": "Conflicting findings get their own section; never bury them"},
            {"symptom": "Vague gaps ('more research needed')", "fix": "Gaps must be specific: 'No study measures past 12 weeks' not 'long-term unclear'"},
            {"symptom": "Treats all studies as equal weight", "fix": "Evidence strength column required; weak studies don't overrule strong studies in the synthesis"},
        ],
        "tested_with": {"models": ["claude-opus-4", "claude-sonnet-4-5", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["user-research-synthesizer", "meeting-decision-recorder"],
        "related_tool_slugs": ["zotero", "mendeley", "notionai"],
        "related_glossary_slugs": ["literature-review", "meta-analysis", "systematic-review"],
        "faq": [
            {"question": "How many papers minimum?", "answer": "5 is the floor for thematic clustering. <5 = just summarize each individually."},
            {"question": "How do I extract key_findings from papers?", "answer": "Paste the abstract + your reading notes. Don't paste full papers — context wastes."},
            {"question": "Can it find papers for me?", "answer": "No — this is synthesis only. Use a separate retrieval step (Google Scholar, Semantic Scholar) first."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Literature Review Synthesizer — Claim, Evidence, Gap",
        "meta_description": "Synthesize 5-30 papers into themed review with conflicting findings flagged and explicit 'what we don't know yet' section.",
    },

    {
        "slug": "interview-guide-builder",
        "title": "User-Interview Guide Builder",
        "category": "research",
        "tldr": "Build a 45-min user-interview guide with warm-up, core questions (open + follow-up), task scenarios, and exit. Calibrated to research question + participant type.",
        "tags": ["interview-guide", "user-research", "qualitative"],
        "best_for_tags": ["user-research", "interview", "discovery"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You build interview guides for qualitative user research. Good guides extract real signal in 45 minutes; bad guides extract opinions on hypothetical features.\n\n"
            "INPUTS:\n"
            "- research_question: what you want to learn\n"
            "- participant_profile: who you're talking to (role, context, why they're relevant)\n"
            "- duration_minutes: 30 / 45 / 60 (default 45)\n"
            "- interview_mode: in-person | video | phone (affects question types)\n"
            "- hypothesis_to_test (optional): specific belief you want to challenge\n\n"
            "STRUCTURE (45 min):\n"
            "1. WARM-UP (5 min): low-stakes context questions; build rapport. NOT 'tell me about yourself' — too vague.\n"
            "2. CONTEXT (10 min): the participant's day/workflow/situation relevant to the research_question. Specifics, not generalizations.\n"
            "3. PROBE (15 min): the moments where research_question applies. Use 'tell me about the last time...' framing.\n"
            "4. PROVOCATION (10 min): optional artifact/scenario/concept to react to. NOT a feature pitch.\n"
            "5. EXIT (5 min): what they wanted to tell you but you didn't ask; permission to follow up.\n\n"
            "QUESTION CRAFT RULES:\n"
            "- Open questions only ('how', 'what', 'tell me about'), no closed yes/no.\n"
            "- Anchor in specific past behavior ('the last time X happened'), not hypotheticals ('would you ever X').\n"
            "- Each main question has 2-3 follow-up probes ('and then?', 'what happened next?', 'why did you decide that?').\n"
            "- No leading questions ('don't you think X would be useful?').\n"
            "- One question per turn; no compound ('how do you X and why?').\n\n"
            "OUTPUT: markdown with sections + question numbering + estimated time per section + 'reminders for the interviewer' (anti-bias notes).\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "research_question", "type": "string", "description": "What you want to learn", "required": True, "example": "How do engineering managers decide which dev tools to adopt for their team?"},
            {"name": "participant_profile", "type": "string", "description": "Who you're talking to", "required": True, "example": "Engineering managers at 50-500 person SaaS companies who have adopted 2+ new dev tools in the past 6 months."},
            {"name": "duration_minutes", "type": "integer", "description": "Interview length", "required": True, "example": "45"},
            {"name": "interview_mode", "type": "string", "description": "in-person | video | phone", "required": True, "example": "video"},
            {"name": "hypothesis_to_test", "type": "string", "description": "Belief to challenge", "required": False, "example": "EMs decide based on team request rather than independent research"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Warm-up (5 min)\n1. Walk me through how this past week has looked for you so far.\n   - Probe: anything that took more time than you expected?\n\n## Context (10 min)\n2. Tell me about the dev tools your team uses day-to-day. Which ones do you not think about anymore vs the ones that are still 'new'?\n   - Probe: how did the 'old' ones get there?\n   - Probe: what about the 'new' ones — what's new about them?\n\n## Probe (15 min)\n3. Tell me about the last time your team adopted a new dev tool. Walk me through how that happened, from the first time someone mentioned it to the point where it was in production.\n   - Probe: who first brought it up?\n   - Probe: what happened between then and the decision?\n   - Probe: did anyone push back?\n\n## Reminders for the interviewer\n- Don't pitch your own product\n- Silence is OK — let them fill it\n- 'Why' too many times = interrogation; rotate with 'tell me more', 'and then?'"},
        "use_cases": [
            {"scenario": "Pre-product-launch discovery", "example": "Team building a new product; this prompt generates the guide for 15 customer-discovery interviews."},
            {"scenario": "Churn-reason research", "example": "Past customers who left; guide focuses on the decision moment + alternatives considered."},
            {"scenario": "Pricing research", "example": "Guide probes value perception without pitching specific prices."},
            {"scenario": "Junior researcher training", "example": "Junior writes their own guide, then runs this prompt; diff is the learning."},
        ],
        "when_not_to_use": "Don't use for quantitative surveys (different prompt). Also skip for highly compliance-bound contexts where every question needs IRB review.",
        "few_shot_examples": [
            {
                "input": "RQ: 'Why do indie devs choose Substack over Buttondown for newsletters?'. Participant: 'indie devs with 100-10000 subscribers'. Duration: 30. Mode: video.",
                "output": "## Warm-up (3 min)\n1. How's your newsletter going lately?\n\n## Context (7 min)\n2. Walk me through the last newsletter you sent — from idea to send.\n   - Probe: what tools did you touch?\n\n## Probe (15 min)\n3. Tell me about choosing your newsletter platform originally. What made you pick the one you use?\n   - Probe: what else did you consider?\n   - Probe: was there a specific moment when you decided?\n4. Have you ever considered switching? Tell me about that moment.\n   - Probe: what made you stay (or switch)?\n\n## Exit (5 min)\n5. What didn't I ask that I should have?",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at avoiding leading questions."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Sometimes injects hypothetical 'would you...' questions; reinforce the rule."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Preferred for nuanced research (e.g., emotional / political topics)."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; expect to revise 2-3 questions per guide."},
        ],
        "variations": [
            {"label": "Diary-study mode", "description": "Multi-day async questions instead of single interview.", "prompt_snippet": "Replace 45-min structure with: 5 daily prompts over 7 days, each asking participant to record one specific moment relevant to research_question."},
            {"label": "Group / focus-group", "description": "6-person focus group, 90 min.", "prompt_snippet": "Adjust for group dynamics: include 'go around the room' moments, surface disagreement intentionally, less 1:1 probing."},
            {"label": "Field-observation guide", "description": "Ride-along / shadowing.", "prompt_snippet": "Replace interview questions with observation prompts: 'What does the participant do without being asked?', 'Where do they get stuck?', 'What workarounds appear?'"},
        ],
        "failure_modes": [
            {"symptom": "Leading questions ('Don't you think X would be helpful?')", "fix": "Forbid in question craft rules; reject leading phrasings"},
            {"symptom": "Hypothetical instead of past behavior", "fix": "Anchor every probe in 'the last time' or 'a specific instance', never 'would you ever'"},
            {"symptom": "Yes/no questions instead of open", "fix": "Open-only rule; transform 'do you X?' to 'tell me about how you X'"},
            {"symptom": "Over-scripted, no room for emergent topics", "fix": "Time-box sections; explicitly tell interviewer 'follow the participant if they go somewhere unexpected'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-opus-4", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["user-research-synthesizer", "support-ticket-triage"],
        "related_tool_slugs": ["dovetail", "userinterviews", "lookback"],
        "related_glossary_slugs": ["qualitative-research", "interview-guide", "discovery-research"],
        "faq": [
            {"question": "How many interviews do I need?", "answer": "5-8 for early discovery (themes saturate fast). 12-20 for product validation. >20 = consider survey for breadth."},
            {"question": "How long is too long?", "answer": "45 min is the sweet spot. 60+ min = participants degrade. 30 min = enough for focused topics."},
            {"question": "Should I record?", "answer": "Yes — with consent. Transcription + AI summary saves 5x synthesis time. But recording can affect what participants share; mention recording at warm-up."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "User Interview Guide Builder — 45-Min Structured",
        "meta_description": "Build interview guides with warm-up, context, probe, provocation, exit. Past-behavior anchors, anti-bias rules built in.",
    },

    {
        "slug": "competitive-teardown",
        "title": "Competitive Teardown (feature + positioning + pricing)",
        "category": "research",
        "tldr": "Deep-dive on a single competitor: product surfaces, positioning claims, pricing tiers, sales motion, recent changes. Builds the dossier you'd need to compete.",
        "tags": ["competitive", "teardown", "intel"],
        "best_for_tags": ["competitive-intel", "product-marketing", "sales-enablement"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You build a competitive teardown — a single-competitor dossier deep enough to brief a new salesperson. Be evidence-based; flag where you're inferring vs citing.\n\n"
            "INPUTS:\n"
            "- competitor: {name, url, founding_year, est_revenue, est_employees, funding_stage}\n"
            "- evidence: list of {source, date, content_summary} from website / docs / blog / G2 reviews / customer-call notes\n"
            "- our_company_context: how we compete (positioning + segment overlap)\n\n"
            "STRUCTURE (each section: claim + evidence + confidence):\n"
            "1. POSITIONING: their elevator pitch (in their words). Who they target. What they avoid.\n"
            "2. PRODUCT SURFACES: top 5-7 features they emphasize publicly. What's MISSING that we'd expect.\n"
            "3. PRICING & PACKAGING: tier structure, anchor prices, free tier (if any), enterprise gates.\n"
            "4. SALES MOTION: PLG / sales-led / hybrid. Trial vs demo. Self-serve vs gated.\n"
            "5. STRENGTHS (against us): 3-5 areas where they have real advantage.\n"
            "6. WEAKNESSES (we should attack): 3-5 areas where we win.\n"
            "7. RECENT MOMENTUM: hiring, launches, fundraise, customer-logo growth (last 6 months).\n"
            "8. CUSTOMER VOICE: 3-5 representative quotes from reviews — balanced positive/negative.\n\n"
            "EVIDENCE RULES:\n"
            "- Every claim cites the input source by index.\n"
            "- Inferences are tagged 'INFERRED' with confidence (low/med/high).\n"
            "- Never fabricate quotes or stats.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "competitor", "type": "CompetitorProfile", "description": "Basic competitor metadata", "required": True, "example": "{name:'Acme Analytics', url:'acme.com', founding_year:2019, est_revenue:'$15M ARR', est_employees:75, funding_stage:'Series B'}"},
            {"name": "evidence", "type": "list[Evidence]", "description": "Source material — website, docs, reviews, calls", "required": True, "example": "[{source:'acme.com homepage', date:'2026-05-13', content_summary:'Headline: ...'}]"},
            {"name": "our_company_context", "type": "string", "description": "How we compete", "required": True, "example": "We target the same mid-market segment with usage-based pricing vs their seat-based."},
        ],
        "expected_output": {"format": "markdown", "sample": "## 1. POSITIONING\n**Claim:** 'The analytics platform built for product teams who hate dashboards.' [source #1]\n**Target:** PMs and growth at Series-B+ SaaS [#1, #4]\n**Avoid:** Enterprise BI use case — explicitly steered away from in pricing page FAQ [#2]\n**Confidence:** high\n\n## 5. STRENGTHS (against us)\n1. Native Salesforce sync [#3] — we don't have this. (high)\n2. INFERRED: faster onboarding (1-line setup per docs) [#5, INFERRED med]\n3. Stronger PM-community presence (3 conferences sponsored in 6 months) [#7]\n\n## 6. WEAKNESSES (we should attack)\n1. No usage-based pricing — costs scale linearly with seats [#2]\n2. No self-serve enterprise tier; gated by sales [#2]\n3. G2 reviews flag slow support response (3/5 negative quotes mention) [#8]\n\n## CUSTOMER VOICE\n> 'Game-changer for our PM team. Setup was 10 minutes.' (G2 reviewer, May 2026) [#8]\n> 'Pricing scales painfully — we added 10 seats and bill jumped $4k/mo.' (G2 reviewer, April 2026) [#8]"},
        "use_cases": [
            {"scenario": "Sales onboarding", "example": "New AE needs to know top 3 competitors; this prompt produces the dossier for each."},
            {"scenario": "Battle-card creation", "example": "Sales-enablement extracts the strengths/weaknesses sections into a 1-pager battle card."},
            {"scenario": "Pre-fundraise diligence", "example": "Investor due-diligence requires competitive landscape; teardowns of top 3 competitors anchor the response."},
            {"scenario": "Competitive watch", "example": "Quarterly re-run with refreshed evidence; momentum section highlights what's changed."},
        ],
        "when_not_to_use": "Don't use without real evidence input — the prompt won't fabricate intel. Also skip for stealth competitors (no public surface to scrape).",
        "few_shot_examples": [
            {
                "input": "Competitor: vector-db company. Evidence: 3 sources (homepage, pricing page, G2 reviews). Our context: open-source self-hostable.",
                "output": "## 1. POSITIONING\n'Production-ready vector search at enterprise scale.' Targets ML teams at >500-person companies [#1]. Avoids hobbyist use case [INFERRED med — no community/free tier prominently shown].\n\n## 3. PRICING & PACKAGING\nFree dev tier (1M vectors). Pro $99/mo (10M vectors). Enterprise 'contact us' [#2].\n\n## 6. WEAKNESSES (we should attack)\n1. Closed-source — self-host requires enterprise tier [#2]\n2. G2 reviews flag lock-in concern: 'data export is JSON-only, slow' [#3]",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at evidence-vs-inference discipline."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Preferred for $1M+ competitive deals."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong structure; sometimes weakens the 'INFERRED' tagging."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; verify every claim against evidence input."},
        ],
        "variations": [
            {"label": "Pricing-only teardown", "description": "Deep on packaging.", "prompt_snippet": "Focus all sections on pricing/packaging. Add 'price-per-value' analysis (cost per 1k requests, per seat, per anything) for cross-tier comparison."},
            {"label": "Sales-call-style", "description": "Tone shifts to 'how to handle in sales calls'.", "prompt_snippet": "Reframe strengths/weaknesses as 'objection-handling cheat-sheet': for each competitor strength, the line our AE should use; for each weakness, the question that exposes it."},
            {"label": "Multi-competitor batch", "description": "Loop over 3-5 competitors.", "prompt_snippet": "INPUT becomes list of competitors. Output per-competitor teardown + cross-competitor comparison table at the end."},
        ],
        "failure_modes": [
            {"symptom": "Fabricates quotes from G2 / customer calls", "fix": "Quotes must come from evidence input, with source index; otherwise mark 'no customer voice in inputs'"},
            {"symptom": "Confuses inference with fact", "fix": "INFERRED tag mandatory; confidence rating per inferred claim"},
            {"symptom": "Generic strengths/weaknesses ('they have good UX')", "fix": "Each must reference a specific evidence point; vague claims rejected"},
            {"symptom": "Outdated info passed off as current", "fix": "Surface evidence date per claim; flag any claim older than 6 months as 'stale, refresh'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["competitive-landscape-mapper", "vendor-comparison-builder", "rfp-response-builder"],
        "related_tool_slugs": ["klue", "crayon", "g2"],
        "related_glossary_slugs": ["competitive-intel", "battle-card", "positioning"],
        "faq": [
            {"question": "How fresh should evidence be?", "answer": "<6 months for product/pricing; <3 months for momentum signals. Stale evidence misleads."},
            {"question": "Where do I source evidence?", "answer": "Homepage, pricing page, docs, G2/Capterra reviews, Glassdoor (sales-motion hints), LinkedIn (hiring), Wellfound (engineering blog)."},
            {"question": "Can it scrape the competitor's site?", "answer": "No — it synthesizes evidence you provide. Pair with a scraper if you need automation."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Competitive Teardown — Evidence-Based Dossier",
        "meta_description": "Single-competitor deep dive: positioning, pricing, sales motion, strengths/weaknesses, customer voice. Evidence-cited, inference-tagged.",
    },

    {
        "slug": "market-sizing-fermi",
        "title": "Market Sizing via Fermi Estimation",
        "category": "research",
        "tldr": "Build a TAM/SAM/SOM estimate via explicit Fermi chains. Each assumption is named, sourced (or flagged as estimate), and sensitivity-tested.",
        "tags": ["market-sizing", "tam-sam-som", "fermi"],
        "best_for_tags": ["market-research", "fundraising", "go-to-market"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You build market-size estimates using Fermi-style chains. The output looks rigorous because every assumption is named — not because you used pretty numbers.\n\n"
            "INPUTS:\n"
            "- product: 1-paragraph description of what's being sold\n"
            "- buyer_definition: who the buyer is (role, company size, geography)\n"
            "- price_point: what they'd pay (annual or one-time)\n"
            "- known_anchors: list of {claim, source} for anchors (e.g., '300k US engineering managers', BLS 2024)\n\n"
            "PROCEDURE:\n"
            "1. TAM (Total Addressable Market) — every buyer who could plausibly use this. Use Fermi chain: starting universe × narrowing factor × narrowing factor → buyers; × price → $ TAM.\n"
            "2. SAM (Serviceable Addressable Market) — TAM restricted to geographies/segments you actually serve.\n"
            "3. SOM (Serviceable Obtainable Market) — SAM × realistic share you can capture in N years.\n"
            "4. For every multiplication, name the source: cited / industry estimate / your assumption.\n"
            "5. Sensitivity test: what's the TAM if each assumption shifts ±20%? Flag the assumption that matters most.\n"
            "6. Add a 'reality check' section: similar companies and what they actually captured, as a sanity check.\n\n"
            "OUTPUT FORMAT: markdown with TAM chain (each line: 'X × Y = Z, source: ...'), SAM, SOM, sensitivity table, reality check.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "product", "type": "string", "description": "What's being sold", "required": True, "example": "Self-hosted analytics for SaaS companies, drop-in alternative to PostHog/Mixpanel"},
            {"name": "buyer_definition", "type": "string", "description": "Buyer role, company size, geography", "required": True, "example": "Engineering lead at a SaaS company with 10-500 employees in North America + Europe"},
            {"name": "price_point", "type": "string", "description": "Annual contract value or one-time price", "required": True, "example": "$3,000 / year average"},
            {"name": "known_anchors", "type": "list[Anchor]", "description": "Cited starting numbers", "required": False, "example": "[{claim:'30,000 SaaS companies in NA+EU at 10-500 employees', source:'Crunchbase 2025 SaaS report'}]"},
        ],
        "expected_output": {"format": "markdown", "sample": "## TAM (Fermi chain)\n- 30,000 SaaS companies in NA+EU (10-500 employees) — Crunchbase 2025\n- × 70% have at least 1 product/analytics tool in budget — industry estimate\n- = 21,000 buyers\n- × $3,000 ACV = **$63M TAM**\n\n## SAM\n- Restrict to English-speaking + SOC2-ready = 75% of TAM\n- = **$47M SAM**\n\n## SOM (3-year)\n- Realistic share: 2% (your assumption; sanity-check: PostHog at year-3 captured ~3% of TAM)\n- = **$940k SOM by year 3**\n\n## Sensitivity (±20%)\n| Assumption | Low | Base | High |\n|---|---|---|---|\n| Buyer count | 16,800 | 21,000 | 25,200 |\n| ACV | $2,400 | $3,000 | $3,600 |\n| Share % | 1.6% | 2% | 2.4% |\n| → SOM | $645k | $940k | $1,361k |\n\nThe ACV is the most-sensitive lever — small ACV changes move SOM more than buyer count.\n\n## Reality check\n- PostHog: $15M ARR at year 5 (~$70M TAM × 21% share — likely they're now expanding TAM definition).\n- Plausible: matches the order of magnitude."},
        "use_cases": [
            {"scenario": "Pitch-deck market-size slide", "example": "Founder needs the TAM slide; this prompt builds the chain that holds up to investor scrutiny."},
            {"scenario": "Strategic-planning sizing", "example": "Internal: 'How big can this product line be?' — chain reveals if the answer justifies investment."},
            {"scenario": "Geo expansion decision", "example": "Re-run with different geo restrictions to compare expansion priorities."},
            {"scenario": "Pricing experimentation", "example": "Sensitivity table shows whether ACV move from $3k → $6k materially changes SOM."},
        ],
        "when_not_to_use": "Don't use as the only basis for an investment decision — Fermi is order-of-magnitude, not precision. Also skip for very early markets (no comparable anchors).",
        "few_shot_examples": [
            {
                "input": "Product: 'AI-powered legal contract review for SMBs'. Buyer: 'GC or office manager at US companies 50-500 employees'. Price: $5k/yr. Anchors: '120k US companies in that range'.",
                "output": "## TAM\n- 120,000 US companies (50-500 employees) — Census 2024\n- × 60% have legal/compliance budget — industry estimate\n- = 72,000 buyers\n- × $5,000 ACV = **$360M TAM**\n\n## SAM\n- Restrict to companies using e-signature (proxy for digital-doc maturity) = 80%\n- = **$288M SAM**\n\n## SOM (3-year)\n- 1.5% share (legal tech adoption is slow)\n- = **$4.3M SOM**\n\n## Sensitivity\nMost sensitive: budget penetration (60%) — if actually 40%, TAM drops to $240M.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at distinguishing cited vs estimated anchors."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Reliable arithmetic; sometimes invents anchor sources."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Use for fundraise-grade decks."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; check each anchor manually."},
        ],
        "variations": [
            {"label": "Top-down version", "description": "Start from total industry spend and slice down.", "prompt_snippet": "Override Fermi chain: start from industry-spend total (e.g., '$5B US legal-tech spend'), narrow by segment, then by product type."},
            {"label": "Bottoms-up version", "description": "Start from per-customer detail and multiply up.", "prompt_snippet": "Build from typical customer: one team buys, what they pay, multiply by buyer count. Reveals unit economics vs total-pie framing."},
            {"label": "Geographic breakout", "description": "Per-region SOM.", "prompt_snippet": "Split SAM and SOM by region (NA / EU / APAC / LATAM). Surface which region is most underserved relative to TAM."},
        ],
        "failure_modes": [
            {"symptom": "Invents source citations", "fix": "Strict rule: sources must come from known_anchors input or be tagged 'estimate'"},
            {"symptom": "Multiplies through several speculative assumptions to reach a pretty number", "fix": "Every assumption requires explicit confidence (cited/industry-estimate/our-assumption); the sensitivity table surfaces the cost"},
            {"symptom": "Skips reality check", "fix": "Mandatory section — list at least 2 comparable companies and what they actually captured"},
            {"symptom": "Confuses TAM with revenue potential year 1", "fix": "TAM/SAM/SOM/Year-1 are distinct; always clarify the time horizon for SOM"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-opus-4", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["competitive-landscape-mapper", "investor-update-monthly", "strategic-tradeoff-analyzer"],
        "related_tool_slugs": ["crunchbase", "statista", "pitchbook"],
        "related_glossary_slugs": ["tam-sam-som", "fermi-estimation", "market-sizing"],
        "faq": [
            {"question": "Investor doesn't believe the TAM number?", "answer": "Walk them through the chain. Every assumption is named; they can challenge any one. The sensitivity table shows you've already thought about it."},
            {"question": "What's a realistic 3-year SOM?", "answer": "Depends on category maturity. New categories: 0.5-2%. Established: 2-5%. Replacement plays: 1-3%. Don't claim >10% in 3 years unless you have evidence."},
            {"question": "Should I use top-down or bottom-up?", "answer": "Both. They should converge within ±2x; if they don't, one is wrong."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Market Sizing via Fermi — TAM/SAM/SOM with Sensitivity",
        "meta_description": "Build TAM/SAM/SOM with explicit Fermi chains, sourced assumptions, and sensitivity analysis. Survives investor scrutiny.",
    },
]
