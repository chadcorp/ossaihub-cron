"""Writing/editing prompts — batch 2."""

RECORDS = [
    {
        "slug": "newsletter-issue-from-week",
        "title": "Newsletter Issue From The Week's Notes",
        "tldr": "Drafts a newsletter issue from raw weekly notes — picks the 2-3 strongest threads, finds the through-line, and lands one specific takeaway readers can act on Monday.",
        "category": "writing-editing",
        "tags": ["newsletter", "synthesis", "writing", "weekly-digest"],
        "best_for_tags": ["newsletter-writers", "founders", "creators"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Founder's weekly note to investors", "example": "Past 7 days of notes (Slack, calls, decisions) → one synthesized 800-word note with a clear thesis."},
            {"scenario": "Creator's weekly Substack", "example": "Raw notes from links, books, conversations → newsletter that has a point, not just a list."},
            {"scenario": "Team weekly digest", "example": "Engineering team's week of work → digest framed for product/leadership readers."},
            {"scenario": "Personal weekly review newsletter", "example": "Journal + screenshots → reader-friendly version with one concrete takeaway."},
        ],
        "when_not_to_use": "Skip when you actually need a roundup of links (use a curation prompt). Skip when the week didn't have a real through-line — forcing one is how newsletters get bad.",
        "full_prompt": """You are drafting one issue of a weekly newsletter from the writer's raw notes. The goal is NOT a roundup; it's a piece with a point.

WHAT YOU GET
- Notes from the past week: meetings, articles read, decisions, observations, sketches of arguments.

WHAT YOU PRODUCE

## Step 1: Find the through-line
Read all the notes. What's the ONE thread that connects 2-3 of the strongest items? Don't pick the biggest news — pick the most cohesive idea. State it in one sentence.

## Step 2: Draft the issue
Length: {target_word_count} words. Structure:

1. OPENING (50-100 words). State the through-line — not as a thesis statement, but as a vivid moment or observation from the week. Don't bury the lead, but don't announce it either.

2. BODY (60% of word count). Develop the through-line using 2-3 specific moments from the notes. For each: concrete detail, what made it stick, what it implies.

3. THE TURN (10-15% of words). Where you complicate or push back on your own opening. Newsletters that don't earn this feel like LinkedIn posts.

4. CLOSING (1 short paragraph). The thing reader could DO on Monday. Specific. Concrete.

## Step 3: Subject line
3 candidates. Each:
- A specific noun, not a category.
- A real promise, not a tease.
- Under 60 characters.

VOICE NOTES
- Specific over general (one named person beats "people"; one Tuesday morning beats "this week").
- One idea well-developed beats three ideas mentioned.
- The reader is busy and smart — write for that.

CONSTRAINTS
- Use only what's in the notes. Don't invent supporting details.
- Don't write "delve", "dive into", "in today's fast-paced world", or any tone-marker of AI-written content.
- If two items in the notes contradict, name the contradiction explicitly.

RAW NOTES
{raw_notes}

Begin with Step 1.""",
        "input_variables": [
            {"name": "raw_notes", "type": "string", "description": "Unstructured week notes", "required": True, "example": "Mon: call w/ Anita, talked about pricing experiment. Article: 'Why SaaS is hard now' (NYT). Wed: shipped feature. Realized our docs are stale..."},
            {"name": "target_word_count", "type": "integer", "description": "Target newsletter length", "required": False, "example": "800"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Through-line statement, then drafted issue with opening, body, turn, closing — plus 3 subject lines.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Best at finding the actual through-line; doesn't force coherence on disparate notes."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Strong; sometimes pads body length — re-pin word count."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Often turns ‘the turn’ into a generic pivot; ask for genuine complication."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Falls into roundup format; needs constant reminder to find single thread."},
        ],
        "variations": [
            {"label": "Single-link expansion", "description": "Expand one strong link into the issue.", "prompt_snippet": "Replace through-line step with: ‘pick the single most resonant link/conversation; write the entire issue using that as the spine.’"},
            {"label": "Photo-led", "description": "Open with the week's strongest visual.", "prompt_snippet": "Add: ‘open with a description of one image/moment from the week; let it anchor the through-line.’"},
            {"label": "Q&A from a real reader", "description": "Frame around a reader's question.", "prompt_snippet": "Add: ‘open with a reader's question from this week; treat the issue as your considered answer.’"},
        ],
        "failure_modes": [
            {"symptom": "Output is a roundup with bullets instead of an issue.", "fix": "Re-pin ‘not a roundup; one through-line’ and require ‘the turn’ paragraph explicitly."},
            {"symptom": "Through-line is generic (‘people are anxious’).", "fix": "Add: ‘through-line must reference at least 2 specific items from the notes.’"},
            {"symptom": "Closing CTA is vague (‘think about how this applies’).", "fix": "Add: ‘closing names ONE concrete action the reader can take by next week.’"},
            {"symptom": "Tone reads AI.", "fix": "Add banned phrases list including ‘in today's fast-paced world’, ‘delve’, ‘dive deep’, ‘unlock’ (verb), ‘game-changer’."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["voice-cloner-from-samples", "blog-post-from-outline", "tighten-prose-30pct"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["narrative-arc", "through-line"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why force ‘the turn’?", "answer": "Without it, newsletters read as one-take pronouncements. The turn signals to readers you've sat with the idea long enough to see its other side."},
            {"question": "What if my week genuinely was a roundup?", "answer": "Then write a roundup honestly. Don't manufacture a thesis when there isn't one — readers smell it."},
            {"question": "How is this different from a blog post?", "answer": "Newsletter = intimate voice, time-bound, one idea. Blog post = standalone, evergreen, can be longer and more structured. The opening especially differs — newsletters open in scene; posts often open in argument."},
        ],
        "meta_title": "Newsletter Issue From The Week's Notes — Prompt",
        "meta_description": "Draft a newsletter issue with a real through-line: pick 2-3 strongest threads, develop them, add the turn, land one concrete takeaway.",
    },
    {
        "slug": "linkedin-post-narrative-arc",
        "title": "LinkedIn Post With Narrative Arc",
        "tldr": "Turns a single insight into a LinkedIn post that actually has a story arc — setup, complication, turn, payoff — not a listicle, not a humble-brag.",
        "category": "writing-editing",
        "tags": ["linkedin", "social-writing", "narrative", "personal-brand"],
        "best_for_tags": ["founders", "consultants", "creators"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Founder writing about a lesson learned", "example": "Real moment from the company → 5-paragraph LinkedIn post that builds toward the lesson, not announces it."},
            {"scenario": "Consultant sharing a framework", "example": "Apply the framework to a real client scenario; let the story carry the framework."},
            {"scenario": "Employee announcing a milestone (job change, anniversary)", "example": "Personal but not cringey — anchored in specifics."},
            {"scenario": "Engineer reflecting on a project shipped", "example": "Technical context made readable; honest about what went wrong."},
        ],
        "when_not_to_use": "Skip for sales posts (use a dedicated sales hook prompt). Skip when you don't have a real moment to anchor in — without specifics, the post will read fake.",
        "full_prompt": """You are drafting a LinkedIn post that has a real narrative arc — not a listicle, not a humble-brag.

INPUT
- The CORE INSIGHT you want to land: {insight}
- The REAL MOMENT it came from (specific time, specific person, specific decision): {moment}
- AUDIENCE: {audience}
- VOICE NOTES (banned phrases, preferred tone): {voice_notes}

STRUCTURE — 5 short paragraphs, 8-15 words each opening, build longer
1. OPENING SCENE (1-2 short sentences). Drop the reader into the specific moment. No setup, no "Last week, I was thinking about..." — just into the room.
2. COMPLICATION. Something that didn't go as expected. A reaction you didn't anticipate. A constraint that wasn't supposed to bind.
3. THE PIVOT (1 sentence). The shift in your thinking. Often: "And then it hit me." (but don't say that.)
4. THE INSIGHT. The thing you now know. Phrased as something the reader can take, not as a declaration about you.
5. CLOSING. Either: a question that invites genuine response (not "What do you think?"), or a single sentence that doubles back to paragraph 1 differently.

FORMAT RULES
- 1500 characters max (LinkedIn hides past this in feed).
- Short paragraphs. White space matters in social feeds.
- One specific person mentioned by role (not name, unless you have permission).
- One specific number if relevant.
- NO bullet points. NO emojis (unless audience explicitly expects them).
- NO "I learned..." / "Here are 3 things..." openings.

BANNED PHRASES (these mark posts as low-effort)
"In today's fast-paced..."
"Game-changer"
"I'm humbled"
"Excited to share"
"Let's dive in"
"Here's the thing"
"Game on"
"Crushing it"

Now draft the post.""",
        "input_variables": [
            {"name": "insight", "type": "string", "description": "The core idea to land", "required": True, "example": "Customer support reveals what your product actually is, not what you think it is"},
            {"name": "moment", "type": "string", "description": "The specific real situation", "required": True, "example": "Tuesday: support agent escalated a refund request that I realized signaled a real product gap we'd been ignoring"},
            {"name": "audience", "type": "string", "description": "Who reads this", "required": True, "example": "B2B SaaS founders + early-stage product leads"},
            {"name": "voice_notes", "type": "string", "description": "Tone/banned phrases", "required": False, "example": "Direct, slightly self-deprecating. Never use ‘grateful’ or ‘humbled’."},
        ],
        "expected_output": {
            "format": "text",
            "sample": "5-paragraph LinkedIn post under 1500 chars with opening scene, complication, pivot, insight, and closing.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on narrative arc; resists banned phrases when listed."},
            {"model": "gpt-4o", "compatibility": "good", "notes": "Sometimes slips into ‘Here's what I learned’ structure; re-pin."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Tends toward overly polished tone; ask for ‘slightly unfinished feeling’."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Defaults to listicle; needs constant reminder."},
        ],
        "variations": [
            {"label": "Carousel adaptation", "description": "Adapt to 6-slide carousel.", "prompt_snippet": "Replace 5-paragraph structure with: ‘5-6 slides, each with a short title and 1-2 sentences. Slide 1 = opening scene; slide 6 = closing.’"},
            {"label": "Story plus framework", "description": "End by extracting a 3-point framework.", "prompt_snippet": "Add after Insight paragraph: ‘then 3 bullets distilling the framework — short labels with a clause each.’"},
            {"label": "Audience-specific reframe", "description": "Same insight, multiple audiences.", "prompt_snippet": "Add: ‘also draft a 100-word version for {alt_audience} adjusting voice and stakes accordingly.’"},
        ],
        "failure_modes": [
            {"symptom": "Opens with ‘Last week, I learned...’", "fix": "Re-pin: ‘open in the specific scene, not in a frame about the scene.’"},
            {"symptom": "Insight is announced too early.", "fix": "Add: ‘the insight appears in paragraph 4 — earlier kills the arc.’"},
            {"symptom": "Closing is ‘What do you think?’", "fix": "Add: ‘closing question must be specific enough that not everyone could answer it the same way.’"},
            {"symptom": "Reads as humble-brag.", "fix": "Add: ‘the protagonist of the story is NOT you. The insight emerges from the situation, not from your cleverness.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["headline-rewrite-stronger", "voice-cloner-from-samples"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["narrative-arc", "social-writing"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should I include hashtags?", "answer": "1-3 specific ones max. 5+ generic hashtags (#leadership #growth) hurts more than helps. Leave room for the post to breathe."},
            {"question": "What about emojis?", "answer": "Depends on your audience. Tech founders / consultants: avoid. Marketing / creators: sparingly. Match what already works for you, not what's trending."},
            {"question": "How is this different from blog writing?", "answer": "LinkedIn rewards micro-arcs in 5 paragraphs. Blogs can be 5x longer. The opening matters more on LinkedIn — feed scrolling means you have 2 seconds."},
        ],
        "meta_title": "LinkedIn Post With Narrative Arc — Prompt",
        "meta_description": "5-paragraph LinkedIn post anchored in a real moment: opening scene, complication, pivot, insight, closing. Banned-phrases list included.",
    },
    {
        "slug": "executive-summary-1-page",
        "title": "One-Page Executive Summary",
        "tldr": "Compresses a long document (proposal, report, deck) into a one-page executive summary: situation, key findings, recommendation, and the 3 questions a CEO will ask.",
        "category": "writing-editing",
        "tags": ["executive-summary", "synthesis", "compression", "business-writing"],
        "best_for_tags": ["board-prep", "deal-summaries", "report-summaries"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "30-page proposal → 1 page for the partner", "example": "Compress vendor proposal to one page that surfaces tradeoffs, not just specs."},
            {"scenario": "Research report for the C-suite", "example": "Q3 market analysis (50 pages) → 1-page exec summary with explicit recommendation."},
            {"scenario": "Board meeting prep", "example": "Past month's product work compressed for board package."},
            {"scenario": "Deal memo", "example": "M&A target analysis → 1 page focused on the few things that matter for the go/no-go."},
        ],
        "when_not_to_use": "Skip when the audience needs the full context (e.g., due diligence). Skip when the document is itself an executive summary — compressing twice loses meaning.",
        "full_prompt": """You are compressing a long document into a one-page executive summary.

INPUT
- Full document (or detailed summary of it): {document}
- Audience and decision they're making: {audience_and_decision}

OUTPUT — ONE PAGE STRUCTURE

# {document_title} — Executive Summary

## Situation
3-5 sentences. What is this document about, why it exists, what decision it informs. Frame for the audience's actual concern.

## Key findings (3-5 bullets)
Each bullet is a complete sentence stating one finding with the evidence in parens. NOT topic headers.
Example: "Customer churn dropped 23% post-feature-X, but only for accounts with >5 seats — suggesting feature is enterprise-relevant only."

## Recommendation
One paragraph with the recommendation stated upfront, then the reasoning. If alternatives were considered, mention them. If the recommendation is conditional, name the condition.

## What we don't know
2-3 things that remain uncertain. This signals intellectual honesty AND surfaces what the decision depends on.

## Questions the CEO will ask
3 questions you predict they'll ask, with one-line answers. Pick questions you can answer; if they'd ask one you can't, note it explicitly.

## Reading guide
A one-line "read pages X-Y for the full reasoning on the key finding."

RULES
- ONE PAGE. About 500 words. Cut anything that doesn't drive toward the decision.
- No background information unless it directly affects the recommendation.
- Numbers > adjectives. "23%" not "significant".
- Don't restate obvious facts the audience already knows.
- Hedge LESS, not more, than the underlying document — the audience needs a position to react to.

DOCUMENT
{document}

AUDIENCE & DECISION
{audience_and_decision}

Now write the summary.""",
        "input_variables": [
            {"name": "document_title", "type": "string", "description": "Title of the doc being summarized", "required": True, "example": "Q3 Market Analysis: Mid-Market Vector DB Opportunity"},
            {"name": "document", "type": "string", "description": "Full document or detailed summary", "required": True, "example": "[paste the full report]"},
            {"name": "audience_and_decision", "type": "string", "description": "Who's reading and what they're deciding", "required": True, "example": "CEO + board. Decision: greenlight $4M investment in mid-market sales team."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six headed sections totaling ~500 words: situation, findings, recommendation, unknowns, predicted questions, reading guide.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at compression and at predicting CEO questions."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally bloats recommendation paragraph."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Strong on findings; recommendation can be wishy-washy — re-pin ‘commit to one position’."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to restate the whole document; needs aggressive cap on word count."},
        ],
        "variations": [
            {"label": "Two-version", "description": "Generate both a 1-page and a 1-paragraph TL;DR.", "prompt_snippet": "Add: ‘also write a 50-word TL;DR for use in email subject preview / Slack DM.’"},
            {"label": "Decision matrix-led", "description": "Open with a 4-cell decision matrix.", "prompt_snippet": "Replace Situation section with: ‘a 2x2 matrix of options with 1-line characterization each, then the recommendation references the matrix.’"},
            {"label": "Risk-focused", "description": "Emphasize risks over opportunities.", "prompt_snippet": "Add new section before Recommendation: ‘TOP RISKS: 3 risks with severity and mitigation each.’"},
        ],
        "failure_modes": [
            {"symptom": "Two pages instead of one.", "fix": "Hard cap: ‘exactly 500 words ± 10%; trim until you fit.’"},
            {"symptom": "Findings are topic headers, not findings.", "fix": "Re-pin: ‘each finding is a complete sentence stating an insight, not a label.’"},
            {"symptom": "Recommendation hedges.", "fix": "Add: ‘state the recommendation in one declarative sentence at the start of the paragraph. Then defend.’"},
            {"symptom": "‘What we don't know’ is missing or generic.", "fix": "Force: ‘at least 2 specific unknowns; vague ones (‘we need more data’) don't count.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["meeting-decision-recorder", "investor-update-monthly", "strategic-tradeoff-analyzer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["executive-summary", "compression"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why include ‘what we don't know’?", "answer": "Two reasons: signals epistemic honesty (executives trust it more), and surfaces what additional work would close the decision gap."},
            {"question": "How do I handle multiple recommendations?", "answer": "Pick one primary recommendation. Mention 1-2 alternates briefly in the recommendation paragraph; don't equally weight."},
            {"question": "What if the document is itself a summary?", "answer": "Don't summarize a summary. Either present the original summary as-is, or expand a section and summarize that."},
        ],
        "meta_title": "One-Page Executive Summary — Prompt",
        "meta_description": "Compress a long document to one page: situation, findings, recommendation, unknowns, predicted CEO questions, reading guide. ~500 words.",
    },
    {
        "slug": "rewrite-for-different-audience",
        "title": "Rewrite Same Content For Different Audience",
        "tldr": "Re-versions the same content for a different audience — adjusts vocabulary, examples, stakes, length — while preserving the core argument. Useful for cross-functional comms.",
        "category": "writing-editing",
        "tags": ["rewriting", "audience-adaptation", "translation", "communication"],
        "best_for_tags": ["cross-functional-comms", "internal-comms", "documentation"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Engineering RFC → product update for execs", "example": "Same proposal, different framing: technical RFC becomes 2-paragraph email for the leadership team."},
            {"scenario": "Customer-facing announcement from internal change-log", "example": "Internal release notes → customer-friendly email."},
            {"scenario": "Research finding → ELI5 for company-wide all-hands", "example": "ML research result → accessible 5-minute talk."},
            {"scenario": "Investor update → team update", "example": "Same numbers, different stakes and tone for the team."},
        ],
        "when_not_to_use": "Skip when the original was already audience-targeted (you'll dilute it). Skip when the audiences need different INFORMATION, not different FRAMING — that's editing, not re-versioning.",
        "full_prompt": """You are rewriting the same content for a different audience. The argument stays the same; the framing changes.

INPUT
- Original content: {original}
- Original audience: {original_audience}
- New audience: {new_audience}
- New audience's core concern: {their_concern}
- New stake (what they care about): {stake}

YOUR PROCESS

## Step 1: Extract the core argument
In one sentence, what is the original ARGUING? (Not just ‘about’ — what's the position?)

## Step 2: Re-frame
- Vocabulary: replace jargon with terms the new audience uses. If your new audience uses different jargon, use theirs.
- Examples: swap or remove examples that won't land. Add examples relevant to {new_audience}.
- Stakes: lead with what the new audience cares about ({stake}), not what the original led with.
- Length: usually shorter for executives, longer for newcomers. Default: 40-60% of original.

## Step 3: Write the new version
Headline + content. Use the new audience's expected format (email if they're execs, doc if engineers, slide bullets if it's for a meeting).

## Step 4: What's lost
2-3 bullets: things the original conveyed that the new version can't. Useful to either accept the loss or to attach as appendix.

CRITICAL CONSTRAINTS
- Preserve the core argument exactly. If the original says X, the new version says X (in different words).
- Don't invent new claims the original didn't make.
- Don't soften the argument unless the new audience is genuinely sensitive — most audiences want directness.
- If the original is wrong about something, flag it; don't silently fix it.

ORIGINAL CONTENT
{original}

Now do Steps 1-4.""",
        "input_variables": [
            {"name": "original", "type": "string", "description": "The original content", "required": True, "example": "[paste the original]"},
            {"name": "original_audience", "type": "string", "description": "Who it was for", "required": True, "example": "Senior engineers on the platform team"},
            {"name": "new_audience", "type": "string", "description": "Who the new version is for", "required": True, "example": "CTO + 2-3 engineering directors"},
            {"name": "their_concern", "type": "string", "description": "What new audience cares about", "required": True, "example": "Cost, scaling risk, team-impact"},
            {"name": "stake", "type": "string", "description": "What makes this matter to them", "required": True, "example": "$X spend over 12 months, plus delivery risk on Q3 roadmap"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Steps 1-4: core argument in one sentence, re-framing notes, the rewritten content, and a ‘what's lost’ bullets list.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at preserving the argument while changing register."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can over-soften for non-technical audiences — re-pin directness."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Handles vocabulary swap well; weaker on adjusting stakes."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to rephrase rather than re-frame; needs explicit step 1."},
        ],
        "variations": [
            {"label": "Multi-audience same call", "description": "Generate 3 versions for 3 audiences.", "prompt_snippet": "Accept list of audiences; produce one re-version each plus comparison table."},
            {"label": "Slide-format output", "description": "Output as slide bullets.", "prompt_snippet": "Replace prose output with: ‘5-7 slides, each with title + 2-4 bullets.’"},
            {"label": "Tone audit before rewrite", "description": "Diagnose tone of original first.", "prompt_snippet": "Add Step 0: ‘Diagnose original tone: register, certainty, formality. Then in Step 2 explicitly note what changes.’"},
        ],
        "failure_modes": [
            {"symptom": "New version has a different argument.", "fix": "Re-pin: ‘same argument, different framing’ and add ‘before writing, paste the one-sentence argument; verify the new version says the same thing.’"},
            {"symptom": "Over-softened (executive version doesn't take a position).", "fix": "Add: ‘the new audience wants the call; soften the JUSTIFICATION wording, not the recommendation itself.’"},
            {"symptom": "Vocabulary swap is mechanical.", "fix": "Add: ‘use the NEW audience's natural terms even if they're imprecise from the original's view; that's the point.’"},
            {"symptom": "‘What's lost’ is generic.", "fix": "Add: ‘each loss must cite a specific phrase or example from the original.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["executive-summary-1-page", "tighten-prose-30pct"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["audience-awareness", "translation"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "When should I lengthen vs shorten?", "answer": "Lengthen for less-familiar audiences (more context). Shorten for senior audiences (less context, more conclusion). Default to shortening; over-explanation is the more common error."},
            {"question": "How do I avoid the new version sounding patronizing?", "answer": "Don't define terms the new audience knows. Don't over-justify. Don't say ‘in simple terms’ — just BE simple."},
            {"question": "What if the original is technically wrong?", "answer": "Flag it in Step 1 (‘core argument is X, but I notice claim Y is unsupported in the original’). Don't silently fix — that's a separate decision."},
        ],
        "meta_title": "Rewrite Same Content For Different Audience — Prompt",
        "meta_description": "Re-version content for a new audience: same argument, different vocabulary/examples/stakes. Plus a ‘what's lost’ list to capture compression tradeoffs.",
    },
]
