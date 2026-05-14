"""Writing/editing prompts — batch 3."""

RECORDS = [
    {
        "slug": "press-release-from-bullet-points",
        "title": "Press Release From Bullet Points",
        "tldr": "Convert bullet-list internal notes into an AP-style press release: headline, dateline, lead, supporting paragraphs, quotes, boilerplate — with a quote-attribution rule that prevents fabrication.",
        "category": "writing-editing",
        "tags": ["press-release", "pr", "media", "writing"],
        "best_for_tags": ["pr-comms", "product-launches", "founder-comms"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Product launch announcement", "example": "Bullet points about launch features → wire-ready release with quotes from named execs."},
            {"scenario": "Funding round", "example": "Round size, lead investor, use-of-funds bullets → standard funding press release."},
            {"scenario": "Partnership announcement", "example": "Co-branded release pulled from internal partnership memo."},
            {"scenario": "Milestone (10k users, etc.)", "example": "Quick distribution-ready release from a single key metric."},
        ],
        "when_not_to_use": "Skip for very narrow trade announcements (better to skip release and do direct outreach). Skip when you're not ready to commit to quote attributions — fabricated quotes are a real risk with AI.",
        "full_prompt": """You are a senior comms professional writing an AP-style press release from internal notes.

INPUT
- Bullet-point notes from the team: {bullets}
- Quotes available (with attribution): {quote_bank}
- Embargo date or "FOR IMMEDIATE RELEASE": {embargo}
- Company boilerplate: {boilerplate}
- Contact info: {contact}
- AP-style or company-style: {style_mode}

OUTPUT — press release in standard format

```
[FOR IMMEDIATE RELEASE | EMBARGOED UNTIL ...]

[HEADLINE — punchy, specific, under 90 chars]

[Subhead — optional, fleshes out the headline]

[CITY, State — Month Day, Year] — [Lead paragraph: who, what, when, where, why in 2-3 sentences. Most newsworthy first.]

[Second paragraph: substance. Specifics. Numbers if available.]

"[Verbatim quote from quote_bank, attributed properly]," said [Name], [Title] of [Company].

[Third paragraph: more context. Customer, market, industry framing.]

[Optional second quote — different speaker, different angle.]

[Final paragraph: forward-looking but not over-promising.]

About [Company]
[Boilerplate from input]

Contact:
[Contact info from input]

###
```

RULES
1. NO FABRICATED QUOTES. Quotes MUST come from quote_bank. If the input has no quotes, write the release WITHOUT quotes and flag in a note at the bottom: "Quote pending from [Role]".
2. SPECIFIC NUMBERS earn the headline. If you have one, use it. ("ACME raises $25M" beats "ACME raises significant Series B".)
3. NO BUZZWORDS in the lead. Save "industry-leading", "transformative", etc. for quotes if you must.
4. INVERTED PYRAMID: most important fact in lead, supporting in body, color at the bottom.
5. DATELINE format: CITY in all caps, comma, state abbreviation, em-dash, date.
6. END with ### (three hashes) — wire convention.

NOTES TO COMPOSE FROM
{bullets}

Begin.""",
        "input_variables": [
            {"name": "bullets", "type": "string", "description": "Bullet-point notes", "required": True, "example": "- Acme launching Pro plan, $49/mo\\n- Adds team features\\n- Available May 14\\n- Founder excited"},
            {"name": "quote_bank", "type": "string", "description": "Available quotes WITH attribution", "required": True, "example": "Jane Doe (CEO): ‘We built this for teams that outgrew our solo plan but aren't ready for enterprise.’"},
            {"name": "embargo", "type": "string", "description": "Embargo / for immediate release", "required": True, "example": "FOR IMMEDIATE RELEASE"},
            {"name": "boilerplate", "type": "string", "description": "Company About paragraph", "required": True, "example": "Acme is a B2B SaaS company founded in 2022..."},
            {"name": "contact", "type": "string", "description": "Press contact info", "required": True, "example": "Press: press@acme.com, Jane Smith (Comms Lead)"},
            {"name": "style_mode", "type": "string", "description": "Style preference", "required": False, "example": "AP-style"},
        ],
        "expected_output": {
            "format": "text",
            "sample": "Wire-format press release with headline, dateline, lead, body, quotes from quote_bank, boilerplate, contact, ###.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Won't fabricate quotes when reminded; tight leads."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally drifts into corporate-speak — re-pin specificity."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; can over-elaborate on metaphors."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Sometimes invents quotes — re-pin no-fabrication rule."},
        ],
        "variations": [
            {"label": "Short-form (300 words)", "description": "Cap length for wire services.", "prompt_snippet": "Add: ‘total length 300 words or less; ruthlessly cut.’"},
            {"label": "Translated variants", "description": "Multi-language releases.", "prompt_snippet": "Add: ‘also produce the release in {target_languages} — preserving quotes verbatim, adapting only the framing.’"},
            {"label": "Embargoed announce kit", "description": "Bundle release + FAQ + boilerplate.", "prompt_snippet": "Add Section: ‘also produce a 5-question reporter FAQ anticipating common journalist asks.’"},
        ],
        "failure_modes": [
            {"symptom": "Quotes fabricated.", "fix": "Re-pin: ‘NEVER write quotes not in quote_bank. If missing, write [Quote pending from Role].’"},
            {"symptom": "Lead buries the news.", "fix": "Add: ‘the lead's first sentence contains the most newsworthy fact; no wind-up.’"},
            {"symptom": "Buzzword-heavy.", "fix": "Add banned word list: revolutionary, transformative, game-changing, unprecedented, paradigm-shifting."},
            {"symptom": "Missing dateline / hashes.", "fix": "Re-pin format; checklist at end of prompt."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["investor-update-monthly", "executive-summary-1-page"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["press-release", "ap-style"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why never fabricate quotes?", "answer": "Quotes are attributed to real people. Inventing them is misrepresentation — legal and ethical exposure. Always flag missing quotes; the CEO can supply later."},
            {"question": "AP style mandatory?", "answer": "Most US press release distributors expect AP. For internal blog announcements, you can relax. Wire services (PR Newswire, Business Wire): AP."},
        ],
        "meta_title": "Press Release From Bullet Points — Prompt",
        "meta_description": "Convert internal bullet notes into AP-style press releases. Strict no-fabricated-quotes rule, dateline format, inverted pyramid.",
    },
    {
        "slug": "research-summary-for-non-experts",
        "title": "Research Paper Summary For Non-Experts",
        "tldr": "Summarize a research paper for a smart but non-specialist audience: the question, the method (without jargon), the finding, why it matters, and what's NOT in the paper that a non-expert might think is.",
        "category": "writing-editing",
        "tags": ["research-summary", "explainer", "academic-translation", "writing"],
        "best_for_tags": ["popular-science", "newsletters", "stakeholder-comms"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Engineer reading ML paper for the team", "example": "GPT-4 architecture paper → 500-word summary for product manager."},
            {"scenario": "Newsletter writer covering science", "example": "JAMA study on a treatment → reader-friendly summary with appropriate caveats."},
            {"scenario": "Policymaker brief", "example": "Climate science paper → policy implications drawn out without overclaiming."},
            {"scenario": "Internal share with leadership", "example": "Technical paper relevant to product → exec summary."},
        ],
        "when_not_to_use": "Skip when the audience IS expert (use a technical summary). Skip for papers you haven't read — the prompt can hallucinate a plausible summary of a fictional paper.",
        "full_prompt": """You are summarizing a research paper for a smart, curious, non-specialist reader.

INPUT
- Paper (full text or detailed extract): {paper}
- Target audience: {audience}
- Length budget: {word_budget} words
- Specific stakeholder questions to address: {stakeholder_questions}

OUTPUT

## 1. The question
What did the paper try to answer? In 1-2 sentences, in plain language. Avoid framing in field-specific jargon.

## 2. The method (lay version)
How did they investigate? Strip the jargon. Don't say "we ran a regression"; say "we looked at how X varies with Y across N cases".
- Sample size or data scale (orders of magnitude is fine)
- Specific comparison or baseline
- Any major caveats about HOW the study was done

## 3. The finding
What they actually found, with the relevant number. Distinguish:
- What they claim
- What the data supports (the conservative reading)
- What's ambiguous

## 4. Why it matters
Specifically WHO this affects and HOW. Avoid "this could revolutionize" abstractions.

## 5. What this paper is NOT
Critical for non-experts. Address 2-3 things a non-expert reader might assume that the paper does not actually establish:
- Causality vs correlation
- Generalizability to other populations
- Practical effect size vs statistical significance
- Long-term vs short-term effects

## 6. Three follow-up questions
What a thoughtful reader should ask next — questions the paper opens but doesn't close.

## 7. Honest confidence
- HIGH: Robust methodology, large sample, replicated literature.
- MEDIUM: Strong study, single-paper, awaiting replication.
- LOW: Preliminary / unusual claim / small sample.

RULES
- Don't oversell. Researchers themselves usually hedge — preserve those hedges.
- Numbers without units are useless. Always include "per X" or comparison anchor.
- If the paper itself is unclear, say so; don't paper over.
- Three banned phrases: "revolutionary", "groundbreaking", "could change everything".

PAPER
{paper}

Begin.""",
        "input_variables": [
            {"name": "paper", "type": "string", "description": "Paper text or detailed extract", "required": True, "example": "[full paper text]"},
            {"name": "audience", "type": "string", "description": "Who's reading", "required": True, "example": "Product manager with technical background but not ML"},
            {"name": "word_budget", "type": "integer", "description": "Target length", "required": True, "example": "500"},
            {"name": "stakeholder_questions", "type": "string", "description": "Specific things audience wants to know", "required": False, "example": "Should we use this method in our product?"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: question, method, finding, why-it-matters, what-this-is-not, follow-up questions, honest confidence rating.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on preserving hedges + honest confidence."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can over-promise — re-pin hedges."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; ‘what this is NOT’ section sometimes thin."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends toward oversell; needs explicit constraint."},
        ],
        "variations": [
            {"label": "Multi-paper synthesis", "description": "Across 3-5 papers.", "prompt_snippet": "Accept multiple papers; produce a meta-summary identifying consensus, contested, and gaps."},
            {"label": "Policy-implication focused", "description": "Translate findings into specific policy recommendations.", "prompt_snippet": "Add Section 8: ‘direct policy implications IF the paper holds up under replication — concrete actions stakeholders could take.’"},
            {"label": "Visual companion", "description": "Suggest a chart.", "prompt_snippet": "Add: ‘suggest one chart from the paper to reproduce (or one to create) that captures the main finding visually.’"},
        ],
        "failure_modes": [
            {"symptom": "Strips important hedges.", "fix": "Re-pin: ‘when the paper hedges, the summary hedges too. Confidence comes from the paper's own language.’"},
            {"symptom": "Causality overclaimed from correlational data.", "fix": "Section 5 must address this explicitly when the method was correlational."},
            {"symptom": "Buzzwords sneak in.", "fix": "Banned word list active; flag and remove."},
            {"symptom": "Reader can't tell what's robust vs preliminary.", "fix": "Confidence rating mandatory; high/medium/low with anchor reasoning."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["literature-review-synthesizer", "literature-review-by-position", "child-explainer-persona"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["academic-paper", "science-communication"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why include ‘what this paper is NOT’?", "answer": "Non-experts routinely over-interpret papers. Explicitly listing what the paper doesn't establish (causality, generalization, long-term) prevents misuse downstream."},
            {"question": "How short is too short?", "answer": "Below 300 words and you've lost the nuance. 500-800 is the sweet spot for a single paper for a non-expert audience."},
        ],
        "meta_title": "Research Paper Summary For Non-Experts — Prompt",
        "meta_description": "Translate research papers for non-specialists: the question, method, finding, what it ISN'T, follow-ups, honest confidence. No oversell.",
    },
    {
        "slug": "blog-comment-thread-summarizer",
        "title": "Comment Thread Summarizer",
        "tldr": "Summarizes a long comment thread (HN, Reddit, blog) into structured takeaways: the dominant positions, the surprising minority view, sources cited by commenters, and what the OP/author didn't address.",
        "category": "writing-editing",
        "tags": ["summarization", "comments", "discussion", "synthesis"],
        "best_for_tags": ["community-management", "research-prep", "newsletter"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "200-comment HN thread", "example": "Long discussion → 5 positions + surprising minority view + cited sources."},
            {"scenario": "Reddit AMA recap", "example": "Big AMA → what audience cared about most + what host evaded."},
            {"scenario": "Blog post engagement review", "example": "Author wants to see what landed; comment thread distilled to themes."},
            {"scenario": "Pre-discussion research", "example": "Before joining a debate, get the lay of the existing discussion."},
        ],
        "when_not_to_use": "Skip for tiny threads (just read them). Skip when individual comments matter more than themes (legal, medical specific cases).",
        "full_prompt": """You are summarizing a comment thread. Extract structure from the chaos.

INPUT
- Source: {source}                              (HN, Reddit, blog, etc.)
- Comment thread (verbatim or detailed): {thread}
- The post being commented on: {original_post}

OUTPUT

## 1. The original post in one sentence
What's the OP arguing or asking?

## 2. Dominant positions (3-5)
The main camps that show up. For each:
- Position in one sentence
- Roughly what % of substantive comments hold this view (rough — don't over-precision)
- Strongest argument for it (quote a representative comment if vivid)
- One illustrative example

## 3. The surprising minority view
A position held by few commenters but worth surfacing — either:
- An expert weighing in with niche knowledge
- A perspective that catches things the majority missed
- A reasoned dissent worth steel-manning

## 4. Sources cited
3-7 specific external links / papers / books cited by commenters. With:
- Source
- What it was cited to support

## 5. What the OP/author didn't address
2-4 things commenters asked or pushed back on that the original post didn't anticipate.

## 6. Tone observations
- Civil / heated / mixed?
- Any patterns in who's commenting (engineers, academics, general audience)?
- Off-topic drift?

## 7. If I joined this discussion
What's the most valuable thing a fresh commenter could add — a perspective or fact missing from the existing thread?

RULES
- Quote rules: short verbatim quotes (under 20 words) with attribution to "a commenter".
- Don't identify usernames by name (privacy + risk).
- Don't summarize troll content or low-effort posts; treat threads as the substantive subset.
- Be honest about your sample — if the input is partial, say so.

ORIGINAL POST: {original_post}

THREAD: {thread}

Begin.""",
        "input_variables": [
            {"name": "source", "type": "string", "description": "Where the thread is hosted", "required": True, "example": "Hacker News"},
            {"name": "thread", "type": "string", "description": "Comment thread text", "required": True, "example": "[comments concatenated or summarized]"},
            {"name": "original_post", "type": "string", "description": "The post being discussed", "required": True, "example": "Why is software so bloated?"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections covering OP, dominant positions, minority view, cited sources, what OP didn't address, tone, what to add.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at surfacing minority views."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; rough percentage estimates can be too confident."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; ‘what OP didn't address’ sometimes shallow."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to flatten distinct positions; specify minimum 3."},
        ],
        "variations": [
            {"label": "Multi-thread", "description": "Same topic across HN + Reddit + Twitter.", "prompt_snippet": "Add: ‘inputs are threads from multiple platforms; compare how the conversation differs by platform.’"},
            {"label": "Argument map", "description": "Output as argument structure.", "prompt_snippet": "Replace positions with argument tree: claim → reasons → counter-reasons → counter-counters."},
            {"label": "Toxicity audit", "description": "Flag if thread is mostly heat, not light.", "prompt_snippet": "Add Section 8: ‘rate productive-discussion ratio 1-10; if low, summarize is mostly bickering, not insight.’"},
        ],
        "failure_modes": [
            {"symptom": "Manufactures consensus that isn't there.", "fix": "Re-pin: ‘if positions are spread thin or contradictory, say so. ‘No clear consensus’ is valid.’"},
            {"symptom": "Identifies usernames.", "fix": "Re-pin: ‘never use specific usernames; always ‘a commenter’ or ‘an engineer commented’.’"},
            {"symptom": "Sample bias — over-quotes top comments.", "fix": "Add: ‘also consider middle-tier and late-thread comments where minority views often live.’"},
            {"symptom": "‘What to add’ is generic.", "fix": "Force: ‘what to add must be specific — name a fact, source, or perspective not present.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["user-research-synthesizer", "thematic-coding-from-transcripts"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["discussion-synthesis"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How long a thread can it summarize?", "answer": "Practical: 200-500 comments fits modern long-context models. Beyond that, sample top + random selection and acknowledge."},
            {"question": "Will the percentages be accurate?", "answer": "Rough estimates only. They're directional, not statistical. Treat as ‘about a quarter of substantive comments’ vs precise percent."},
        ],
        "meta_title": "Comment Thread Summarizer — Prompt",
        "meta_description": "Distill long comment threads into positions, minority view, cited sources, OP gaps, and what a fresh commenter could add.",
    },
    {
        "slug": "internal-memo-from-decision",
        "title": "Internal Memo From a Decision",
        "tldr": "Drafts an internal team memo announcing a decision: context, decision, reasoning, what changes for whom, what's NOT changing, and how people can push back. Anti-‘email blast’ format.",
        "category": "writing-editing",
        "tags": ["internal-comms", "memo", "decisions", "leadership"],
        "best_for_tags": ["leadership", "change-management", "team-comms"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Reorg announcement", "example": "‘We're consolidating teams’ → memo with context, rationale, what changes for whom."},
            {"scenario": "Policy change", "example": "‘Remote work policy is shifting’ → memo with reasoning + dissent path."},
            {"scenario": "Strategic pivot", "example": "‘We're sunsetting product X’ → memo explaining why + customer impact + team plan."},
            {"scenario": "Hire / org change", "example": "‘New VP starting’ → context + reporting changes + onboarding plan."},
        ],
        "when_not_to_use": "Skip for routine ops messages (those go in Slack/standup, not memo). Skip when the decision affects only one person — talk to them directly.",
        "full_prompt": """You are drafting an internal memo from a leader. The decision is made; the memo announces and contextualizes.

INPUT
- Decision: {decision}
- Why this decision (the real reason, not the polished one): {reasoning}
- Audience: {audience}                          (whole company / engineering / specific team)
- What's changing operationally: {changes}
- What's NOT changing (important to call out): {non_changes}
- Effective date: {effective_date}
- Who can answer questions / hear concerns: {contact}

OUTPUT — memo, 300-500 words

## Structure

1. SUBJECT LINE — specific, not "Important Update".

2. OPENING (1-2 sentences). State the decision plainly. No buildup, no "I want to share some news".

3. WHY (1 paragraph). The real reasoning. People can tell when reasoning is pretextual; respect them by being direct. Cite specific drivers if appropriate.

4. WHAT'S CHANGING (bullets or short paragraphs). For each: who's affected, what the change is, effective when.

5. WHAT'S NOT CHANGING (1 paragraph). Anchor the unchanged things explicitly. Reduces anxiety. ("Your role, your manager, and your project assignments remain the same.")

6. WHAT YOU CAN DO (1 short section). 2-3 specific things:
   - Where to ask questions
   - When the next team discussion happens (date, time, channel)
   - How to push back if you disagree

7. CLOSE (1-2 sentences). Honest acknowledgement, no platitudes. ("I know this isn't what some of you would have chosen; I'm available to discuss." beats "Excited about this journey!")

RULES
- Tone: direct, calm, acknowledging. Not corporate, not chummy.
- Be honest about why. Pretextual reasoning ("for strategic alignment") erodes trust.
- Don't ask for "buy-in" performatively. Either you've decided (announce it) or you're consulting (frame as consultation).
- BANNED phrases: "exciting opportunity", "going forward", "moving the needle", "synergies".

Now write the memo.""",
        "input_variables": [
            {"name": "decision", "type": "string", "description": "The decision being announced", "required": True, "example": "Sunsetting the consumer product to focus on B2B"},
            {"name": "reasoning", "type": "string", "description": "Real reasoning (not polished)", "required": True, "example": "B2B revenue is 4x consumer and growing 3x faster. Consumer eats engineering time without proportional return."},
            {"name": "audience", "type": "string", "description": "Who receives the memo", "required": True, "example": "Whole company (40 people)"},
            {"name": "changes", "type": "string", "description": "Operational changes", "required": True, "example": "Consumer engineering team (4 people) shifts to B2B effective June 1. Consumer support continues for current users through end of year then sunsets."},
            {"name": "non_changes", "type": "string", "description": "What stays the same", "required": True, "example": "No layoffs. Compensation unchanged. Reporting structure unchanged."},
            {"name": "effective_date", "type": "string", "description": "Effective when", "required": True, "example": "June 1, 2026"},
            {"name": "contact", "type": "string", "description": "Who hears questions/dissent", "required": True, "example": "CEO direct: 30-min slots Friday afternoon. Or DM with #consumer-pivot channel."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Memo with subject line, opening, why, what's changing, what's not, what you can do, close. 300-500 words.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Direct without corporate fluff."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes adds ‘exciting’ — banned word list helps."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Tends to over-warmth; re-pin direct tone."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Corporate-speak default; needs strong banned word enforcement."},
        ],
        "variations": [
            {"label": "Bad-news variant", "description": "Layoffs / harder messages.", "prompt_snippet": "Add: ‘this is hard news. Lead with the impact on people. Be specific about support (severance, references, transition). Don't sugar-coat.’"},
            {"label": "All-hands followup", "description": "After verbal announcement.", "prompt_snippet": "Add: ‘this memo follows the all-hands; assume people heard the headline. Focus on details + next steps + where to ask.’"},
            {"label": "Public version", "description": "If the decision goes external.", "prompt_snippet": "Add: ‘also produce an external version (customer-facing) that preserves transparency about WHAT changes while protecting internal-specific details.’"},
        ],
        "failure_modes": [
            {"symptom": "Sounds corporate.", "fix": "Banned word list aggressive; rewrite ‘moving forward’ as ‘starting June 1’."},
            {"symptom": "Buries the lead.", "fix": "Re-pin: ‘opening = decision in 1-2 sentences. No buildup.’"},
            {"symptom": "Asks for ‘buy-in’ performatively.", "fix": "Add: ‘either the decision is announced (don't pretend it's open) OR the memo is a consultation (frame explicitly).’"},
            {"symptom": "‘What's NOT changing’ skipped.", "fix": "This section is non-negotiable; reduces anxiety even when changes are major."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["executive-summary-1-page", "meeting-decision-recorder", "investor-update-monthly"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["internal-memo", "change-management"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why include a dissent path?", "answer": "People dissent regardless; making the path explicit means dissent comes to you (where you can engage) instead of into private channels (where it festers). Trust is built by inviting pushback."},
            {"question": "Is 300-500 words enough?", "answer": "For most decisions, yes. Longer memos go unread. If the decision needs more, layer: 500-word memo + linked deep-dive doc."},
        ],
        "meta_title": "Internal Memo From a Decision — Prompt",
        "meta_description": "Draft a 300-500 word internal memo: decision, real reasoning, what changes, what doesn't, how to push back. Direct, no corporate fluff.",
    },
]
