"""Creative prompts — batch 2."""

RECORDS = [
    {
        "slug": "metaphor-extender",
        "title": "Metaphor Extender With Coherence Check",
        "tldr": "Takes a metaphor and extends it through 4-6 implications, flagging which extensions break the metaphor's logic. Used for writing, branding, and pedagogy that needs sustained imagery.",
        "category": "creative",
        "tags": ["metaphor", "creative-writing", "rhetoric", "branding"],
        "best_for_tags": ["essay-writing", "brand-language", "teaching"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Essay with central metaphor", "example": "‘Code is a garden’ → extend through pruning, weeds, seasons, soil — flag where metaphor breaks down."},
            {"scenario": "Brand naming and tagline", "example": "Metaphor ‘our product is the rails’ → extended implications for taglines and features."},
            {"scenario": "Teaching a concept", "example": "‘Backpressure is like a kinked hose’ → multiple specific implications students can grasp."},
            {"scenario": "Pitch deck recurring imagery", "example": "Extend a single anchoring metaphor across the deck rather than mixing."},
        ],
        "when_not_to_use": "Skip for technical documentation where precision beats imagery — metaphors mislead. Skip when the source metaphor is itself bad — extending it just amplifies the badness.",
        "full_prompt": """You are extending a metaphor. The goal is sustained imagery, not just a one-line analogy.

INPUT
- Core metaphor: {metaphor}
- The thing being described: {target}
- Where this will be used: {context}                     (essay, brand language, lesson, etc.)

OUTPUT

## Step 1: Restate
One sentence: what's the core claim of this metaphor? (E.g., ‘Code is a garden’ asserts that code requires ongoing tending, has natural growth patterns, and has weeds — things that creep in and choke value.)

## Step 2: 4-6 extensions
Each extension takes the metaphor further:

### Extension N: <one-line claim using the metaphor's language>
- What it implies about {target}: 1-2 sentences making the implication concrete.
- Where it RINGS TRUE: a specific example or observation that fits.
- Where it BREAKS DOWN: the limit of this implication. Be honest — every extension has a snapping point.

Examples for ‘code is a garden’:
- "Pruning matters more than planting" → most engineering value is in removal/refactoring, not addition. Rings true when seeing dead code accumulate. Breaks down when shipping greenfield — no garden to prune yet.

## Step 3: Coherence audit
- Is the metaphor SUSTAINED or does it slip? (E.g., ‘code is a garden where you build skyscrapers’ slips.)
- Are any extensions inconsistent with each other?
- Is there ONE extension that's particularly load-bearing — if it breaks, the whole metaphor breaks?

## Step 4: When NOT to use this metaphor
2-3 cases:
- Audiences it confuses
- Aspects of {target} it obscures
- Adjacent metaphors that compete

## Step 5: Tagline-ready phrasings (if context warrants)
2-4 phrases that ride the extended metaphor — for repeated brand or rhetorical use.

RULES
- Every extension must be DERIVABLE from the metaphor's logic, not a stretch.
- Specific imagery beats abstract correspondence.
- When the metaphor breaks down, name it — sustained metaphors are useful precisely because their limits are known.
- Avoid mixed metaphors absolutely.

Begin.""",
        "input_variables": [
            {"name": "metaphor", "type": "string", "description": "The source metaphor", "required": True, "example": "Code is a garden"},
            {"name": "target", "type": "string", "description": "What's being described", "required": True, "example": "Software engineering practice"},
            {"name": "context", "type": "string", "description": "How the metaphor will be used", "required": True, "example": "Essay for senior engineers about technical debt"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Five steps: restate, extensions with implications + breaks, coherence audit, when not to use, tagline-ready phrasings.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on sustained imagery and honest breakdown points."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally mixes metaphors — re-pin coherence."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; ‘where it breaks down’ often too soft."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to literal extensions rather than imaginative; needs more push."},
        ],
        "variations": [
            {"label": "Counter-metaphor", "description": "Propose an alternative metaphor.", "prompt_snippet": "Add Step 6: ‘Propose ONE alternative metaphor that captures aspects the original misses. Compare strengths.’"},
            {"label": "Visual companion", "description": "Suggest one image per extension.", "prompt_snippet": "Add: ‘for each extension, sketch one mental image (text description) that would illustrate it.’"},
            {"label": "Brand vocabulary", "description": "Extract reusable terms.", "prompt_snippet": "Add: ‘extract 5-10 reusable terms from the metaphor that could become brand-specific vocabulary.’"},
        ],
        "failure_modes": [
            {"symptom": "Extensions don't actually follow the metaphor's logic.", "fix": "Re-pin: ‘each extension must be derivable from the metaphor itself, not from the target.’"},
            {"symptom": "‘Where it breaks down’ sections are missing or vague.", "fix": "Force: ‘every extension has a snap point; if you can't find it, the extension is too vague.’"},
            {"symptom": "Mixed metaphors in extensions.", "fix": "Add: ‘all extensions live inside the original metaphor's world. No outside imagery.’"},
            {"symptom": "Tagline phrasings sound corporate.", "fix": "Add: ‘taglines lead with a verb or noun from the metaphor's domain; avoid abstract business words.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["voice-cloner-from-samples", "headline-rewrite-stronger"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["metaphor", "rhetoric"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why include where it breaks down?", "answer": "Sustained metaphors persuade by their consistency. Knowing where one breaks lets you stop just short — readers feel the metaphor's coherence rather than spotting the seam."},
            {"question": "How is this different from ‘give me an analogy’?", "answer": "Analogy is one-shot. Extended metaphor is sustained: multiple implications, each tested for fit. Useful when the metaphor is doing real work across a piece."},
            {"question": "Can I use this for poetry?", "answer": "Poetry doesn't need the breakdown section as a feature — poets often LIVE in metaphor's productive break. Use the extensions; skip the coherence audit."},
        ],
        "meta_title": "Metaphor Extender With Coherence Check — Prompt",
        "meta_description": "Extend a metaphor through 4-6 implications, honest about where each one breaks. For essays, branding, and teaching that needs sustained imagery.",
    },
    {
        "slug": "scene-writing-show-dont-tell",
        "title": "Scene Writing: Show, Don't Tell",
        "tldr": "Converts a told paragraph (‘She was nervous’) into a shown scene with specific sensory detail, action, and dialogue — preserving the emotional beat without naming it.",
        "category": "creative",
        "tags": ["fiction", "show-dont-tell", "creative-writing", "craft"],
        "best_for_tags": ["novelists", "screenwriters", "narrative-marketing"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Novel revision pass", "example": "Pass a chapter through this; identifies told moments and proposes shown alternatives."},
            {"scenario": "Screenwriting", "example": "Action lines that show character via behavior, not parentheticals."},
            {"scenario": "Brand storytelling", "example": "Customer testimonial from ‘they were thrilled’ to a specific scene."},
            {"scenario": "Memoir / personal essay", "example": "Replace abstract feeling-words with grounded moments."},
        ],
        "when_not_to_use": "Skip when ‘told’ is the right choice — pacing, summary, exposition. Showing every moment slows narrative. Skip for instructional or analytical writing.",
        "full_prompt": """You are revising prose from TOLD to SHOWN.

INPUT
- The told passage: {passage}
- The emotional beat / state that needs to come through (without being named): {beat}
- Genre / register: {register}                        (literary, thriller, romance, etc.)
- Length budget (words): {word_budget}

OUTPUT

## Step 1: Identify what's told
Quote the abstract / state-naming words from the original (‘She was nervous’, ‘He felt angry’, ‘It was beautiful’). These are the things you'll show instead.

## Step 2: Sensory inventory
What 3-5 senses or details would a person in this state notice or do? List them concretely:
- Sight (small specific things — not ‘she looked around’)
- Touch (object in hand, fabric texture, temperature)
- Sound (one specific sound, not ‘noises’)
- Smell / taste (sparingly — too much gets purple)
- Internal sensation (breath, heart, muscle tension — pick ONE, not all)

## Step 3: Action and dialogue
1-2 specific actions the character takes that reveal the state. 1-2 lines of dialogue that imply but don't state.

## Step 4: The rewrite
Compose the revised scene. Constraints:
- {word_budget} words max.
- The original told state-words DO NOT appear in the rewrite. (No ‘nervous’, ‘angry’, ‘beautiful’, etc.)
- One specific concrete detail per paragraph.
- Don't pile sensory details — pick 2-3 that earn their place.

## Step 5: What's preserved, what's traded
- The beat that survives the rewrite.
- The aspects the original explicitly said that the rewrite leaves to inference (and why that's better).

CRITICAL RULES
- SHOW means specific concrete sensory + action + dialogue.
- TELL means abstract / state / category words.
- The reader should arrive at the emotion themselves, not be told it.
- Don't over-correct: ‘He laughed bitterly’ is still telling (‘bitterly’ does the work). ‘He laughed once, short, then looked at the floor’ shows.

PASSAGE
{passage}

EMOTIONAL BEAT
{beat}

Begin.""",
        "input_variables": [
            {"name": "passage", "type": "string", "description": "The told passage to revise", "required": True, "example": "Sarah was nervous about the interview. She felt scared and unsure."},
            {"name": "beat", "type": "string", "description": "What emotional state to convey without naming", "required": True, "example": "Pre-interview nerves combined with imposter syndrome — she feels she doesn't deserve to be there"},
            {"name": "register", "type": "string", "description": "Genre/register", "required": True, "example": "Literary fiction"},
            {"name": "word_budget", "type": "integer", "description": "Target length in words", "required": False, "example": "150"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Five steps: identify told words, sensory inventory, action/dialogue, the rewrite, what's preserved/traded.",
        },
        "few_shot_examples": [
            {
                "input": "Told: ‘Sarah was nervous about the interview.’ Beat: imposter syndrome.",
                "output": "(Step 4 rewrite): Sarah pressed her thumbnail into the corner of her resume, where she'd already worn a small crescent into the paper. Across the waiting room, a man in a charcoal suit was reading something on his phone with a kind of easy practice she hadn't seen in herself. Her name on the printed list — Sarah Chen, 10:30 AM — looked typed in. The other names looked written.\\n\\n(Step 5): Preserved: pre-interview tension + imposter feeling. Traded: explicit naming. The reader infers ‘nervous’ from the dented paper, and ‘imposter’ from the way her name ‘looked typed.’"
            }
        ],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong concrete imagery; doesn't smuggle state-words back in."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes slips ‘carefully’ / ‘nervously’ adverbs in — re-pin."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; can over-pile sensory details."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Often retains adverb tells; tighten prompt."},
        ],
        "variations": [
            {"label": "Multi-beat scene", "description": "Show multiple emotional shifts in one scene.", "prompt_snippet": "Replace single beat with: ‘arc of beats — opening state, mid-scene shift, ending state. Show each transition.’"},
            {"label": "Dialogue-heavy", "description": "Show via dialogue only.", "prompt_snippet": "Constrain to: ‘only dialogue + minimal action beats; no narration of internal state.’"},
            {"label": "Genre-specific tics", "description": "Match genre's specific show-techniques.", "prompt_snippet": "Add: ‘use techniques characteristic of {register} — e.g., thriller leans on sensory tension; literary leans on the specific small object.’"},
        ],
        "failure_modes": [
            {"symptom": "Rewrite contains state-words (‘nervously’, ‘carefully’).", "fix": "Re-pin: ‘banned adverbs ending in -ly that carry the original's state; verbs without modifiers do more work.’"},
            {"symptom": "Sensory overload (5+ details per paragraph).", "fix": "Add: ‘2-3 concrete details per paragraph max. Each one earns its place.’"},
            {"symptom": "Purple prose / metaphor stack.", "fix": "Add: ‘restraint. The reader fills in — if you crowd them, you tell instead of show.’"},
            {"symptom": "Loses the beat entirely.", "fix": "Add: ‘before final output, verify the rewrite still conveys the beat in step 1; if not, adjust details until it does.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["story-with-character-arc", "dialogue-natural-back-and-forth", "tighten-prose-30pct"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["show-dont-tell", "craft-fiction"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is show-don't-tell always better?", "answer": "No. Telling moves the story along when nothing important is happening. The rule is for emotional beats and key moments — places where the reader should arrive at the feeling themselves, not be told."},
            {"question": "How do I know when to use which?", "answer": "If a paragraph could be summarized without losing anything, it's probably fine to tell. If summarizing loses what matters, show. The state of NERVOUS-AND-IMPOSTER is the wrong thing to summarize."},
            {"question": "Can this be overdone?", "answer": "Absolutely. Some prose styles (Hemingway) lean show; others (Eliot) lean tell. Find your register; don't dogmatically convert."},
        ],
        "meta_title": "Scene Writing: Show, Don't Tell — Prompt",
        "meta_description": "Convert a told paragraph to a shown scene: identify state-words, build sensory inventory, rewrite with specific detail, preserve the beat.",
    },
    {
        "slug": "tagline-from-positioning",
        "title": "Tagline From Brand Positioning",
        "tldr": "Generates 8 candidate taglines from brand positioning, scored across memorability, specificity, differentiation, and ownership. Filters for ‘could anyone else say this?’ test.",
        "category": "creative",
        "tags": ["tagline", "branding", "copywriting", "positioning"],
        "best_for_tags": ["startups", "brand-launch", "rebrand"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Startup naming sprint", "example": "Brand positioning → 8 candidate taglines, scored. Pick top 2 for testing."},
            {"scenario": "Rebrand", "example": "Existing positioning vs proposed new tagline — see if it earns the shift."},
            {"scenario": "Campaign-specific tagline", "example": "Launch campaign needs a sub-tagline. Same prompt, scoped to campaign."},
            {"scenario": "Internal vs external testing", "example": "Generate 8; pick top 3 for A/B test on landing page."},
        ],
        "when_not_to_use": "Skip when positioning isn't sharp — vague positioning produces vague taglines, no matter how many candidates. Fix positioning first.",
        "full_prompt": """You are a senior copywriter. Generate taglines from brand positioning.

INPUT
- Brand: {brand}
- One-line positioning: {positioning}
- Target customer: {target}
- Single most important differentiator: {differentiator}
- Brand voice notes: {voice}
- Banned tactics (cliches, competitor terms, etc.): {banned}

OUTPUT — 8 CANDIDATE TAGLINES

For each:

### {N}. <tagline>

**Score (1-5 each):**
- Memorability: would someone repeat it after one exposure?
- Specificity: does it say something specific to THIS brand, or could it apply to many?
- Differentiation: does it claim the actual differentiator?
- Ownability: ‘could competitor X say this with a straight face?’ If yes, score low.

**Why it works:**
1-2 sentences on the move it makes.

**Failure mode:**
1 sentence on what it sacrifices.

## Final ranking
List the 8 by total score descending. Then identify:
- The two to A/B test (highest scoring + most differentiated)
- The one to NEVER ship (lowest score; explain why it's a trap)

ANTI-PATTERNS — score these low automatically
- ‘[Verb] better’ / ‘[Adjective]er’ (faster, smarter, easier) — vague comparative.
- Three-word abstract phrases (Innovate. Inspire. Transform.) — corporate poetry.
- Customer-hero phrasing if the customer isn't actually the hero (it's the product).
- Buzzwords: synergy, leverage (verb), unlock (verb), game-changing, seamless.
- ‘The [X] for [Y]’ unless the X is genuinely novel.

CRITERIA REMINDERS
- A great tagline is SHORT (1-7 words usually), SAYS something (not just feels something), and is OWNABLE (only your brand could say this convincingly).
- Specificity > cleverness. ‘Just Do It’ is specific to athletes' resistance; clever puns rarely hit.
- The differentiator should be IN the tagline, not lurking behind it.

POSITIONING
{positioning}

DIFFERENTIATOR
{differentiator}

Begin.""",
        "input_variables": [
            {"name": "brand", "type": "string", "description": "Brand name", "required": True, "example": "OSS AI Hub"},
            {"name": "positioning", "type": "string", "description": "Brand positioning statement", "required": True, "example": "A curated directory of open-source AI tools, glossary, and learning paths for builders evaluating the ecosystem."},
            {"name": "target", "type": "string", "description": "Target customer", "required": True, "example": "Engineering managers + indie developers evaluating AI tools for adoption"},
            {"name": "differentiator", "type": "string", "description": "Main differentiator", "required": True, "example": "Curation + accuracy of metadata at scale (the cleanest data on OSS AI)"},
            {"name": "voice", "type": "string", "description": "Voice constraints", "required": False, "example": "Confident, no buzzwords, slightly contrarian to AI hype"},
            {"name": "banned", "type": "string", "description": "Banned tactics", "required": False, "example": "Avoid ‘discover’, ‘unleash’, ‘unlock’; competitor uses ‘all-in-one’ — we don't"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "8 numbered taglines each scored on 4 dimensions with why-it-works + failure-mode; final ranking + A/B test picks.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on the ownability test; honest about failure modes."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally produces 3-word abstract triplets — reject and re-pin anti-patterns."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; tends toward feel-good language — re-pin specificity."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Falls into clichés; explicit ban list essential."},
        ],
        "variations": [
            {"label": "Single-tagline deep dive", "description": "Pick one and stress-test.", "prompt_snippet": "Replace 8 candidates with: ‘ONE tagline you love; deep dive — show 5 variations, A/B-test reasons, longevity scenarios, what changes when company evolves.’"},
            {"label": "Verb-first variants", "description": "Action-oriented.", "prompt_snippet": "Add: ‘all 8 candidates start with a verb that does work, not a corporate verb like ‘empower.’’"},
            {"label": "Internal/external pair", "description": "Generate both customer-facing and internal-rally taglines.", "prompt_snippet": "Add: ‘also generate 3 internal taglines — what the team says to themselves, may not be customer-facing.’"},
        ],
        "failure_modes": [
            {"symptom": "Taglines pass the ‘competitor could say it’ test (low ownability).", "fix": "Re-pin: ‘run the test on every candidate; if a top-2 competitor could say it, score ownability ≤2.’"},
            {"symptom": "Abstract triplets (Verb. Verb. Verb.).", "fix": "Banned-tactic list active; add ‘any 3-word triplet auto-scores 1 on memorability + specificity.’"},
            {"symptom": "Final ranking buries the differentiator.", "fix": "Add: ‘the top-2 picks must claim the differentiator; if they don't, the differentiator is wrong or the taglines miss it.’"},
            {"symptom": "‘Why it works’ is generic.", "fix": "Force: ‘specific to THIS tagline; the move it makes; what it's NOT saying as much as what it is.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["headline-rewrite-stronger", "ad-headline-variations", "pricing-page-rewriter"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["tagline", "positioning", "brand-voice"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How many candidates is enough?", "answer": "8 is the sweet spot. Fewer and you don't see the range. More and quality drops — generating 30 produces 22 dud variations."},
            {"question": "Should we test with users?", "answer": "Always. Internal favorite often doesn't survive contact with the actual market. A/B on landing-page conversion or unaided recall after a week."},
            {"question": "What about descriptors / sub-taglines?", "answer": "Different prompt — taglines are short; descriptors carry the explanation. Use the descriptor variation for landing-page hero copy below the main tagline."},
        ],
        "meta_title": "Tagline From Brand Positioning — Prompt",
        "meta_description": "Generate 8 candidate taglines scored on memorability, specificity, differentiation, ownability — with anti-patterns list and A/B test picks.",
    },
    {
        "slug": "narrative-arc-from-data",
        "title": "Narrative Arc From Data",
        "tldr": "Turns a dataset into a narrative arc: protagonist, obstacle, escalation, turn, resolution. For data-driven storytelling — research write-ups, case studies, business stories.",
        "category": "creative",
        "tags": ["narrative", "data-storytelling", "case-study", "structure"],
        "best_for_tags": ["case-studies", "data-journalism", "business-storytelling"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Customer case study", "example": "Numbers + before/after → story with protagonist, obstacle, escalation, resolution. Not a bullet list."},
            {"scenario": "Annual report narrative", "example": "Quarterly metrics → arc that gives the year shape."},
            {"scenario": "Research findings", "example": "Study data → story-shaped article instead of methods-results-discussion grind."},
            {"scenario": "Internal retrospective", "example": "Project metrics → narrative the team can reference."},
        ],
        "when_not_to_use": "Skip when audience needs the raw data (analysts, scientists) — narrative obscures methodology. Skip for compliance reports where shape isn't the point.",
        "full_prompt": """You are a data storyteller. Turn the data into a NARRATIVE ARC.

INPUT
- Dataset summary: {data_summary}
- The audience: {audience}
- The ‘so what?’ — why this story matters: {so_what}
- Length: {length_words} words

OUTPUT — STORY STRUCTURE

## 1. Find the PROTAGONIST
Who or what is the main subject? (A customer? A product? A metric? A team?)
- Specifically: name the protagonist.
- Goal: what were they trying to achieve?
- Stakes: what happens if they fail / succeed?

## 2. The OBSTACLE
The condition or problem the data reveals.
- What was the protagonist up against?
- Use a specific data point to anchor it (‘churn was 38% before’).

## 3. ESCALATION
What got worse or what was tried that didn't work?
- 1-2 specific moments / data points showing the situation tightening.

## 4. The TURN
What changed? The pivot point.
- The decision, intervention, insight that shifted things.
- Anchor with date / data inflection.

## 5. RESOLUTION
Where the data lands now.
- The outcome metric or state.
- What it implies — but don't over-claim; data has limits.

## 6. THE LESSON
1-2 sentences. What does this story teach the audience?

## 7. WRITE THE NARRATIVE
Compose the actual narrative — {length_words} words. Constraints:
- One specific number per beat.
- Protagonist appears in concrete terms (named, specific role).
- Open in scene if appropriate; not in summary.
- Don't dump the data; let it land at moments of greatest meaning.
- Close with the lesson but don't title-card it.

CRITICAL RULES
- Don't invent data not in the summary. If you need a beat the data doesn't support, name what's missing in section 6.
- Don't soften when data is hard. ‘38% churn’ is more truthful than ‘significant churn.’
- The lesson is implied, not announced. ‘Onboarding matters’ is too abstract; ‘what shipped: a 3-day onboarding sequence; what changed: the slope of the retention curve’ is the lesson grounded in fact.

DATASET
{data_summary}

‘SO WHAT?’
{so_what}

Begin.""",
        "input_variables": [
            {"name": "data_summary", "type": "string", "description": "Summary of the dataset / metrics", "required": True, "example": "Acme SaaS: Q1 churn 38%, Q2 onboarding redesign shipped, Q3 churn 22%, Q4 churn 14%."},
            {"name": "audience", "type": "string", "description": "Who reads this", "required": True, "example": "Product leadership at peer companies"},
            {"name": "so_what", "type": "string", "description": "Why the story matters", "required": True, "example": "Onboarding investments compound; the curve takes 6 months to bend"},
            {"name": "length_words", "type": "integer", "description": "Target words", "required": False, "example": "400"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: protagonist, obstacle, escalation, turn, resolution, lesson, and the written narrative.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on grounded narrative without over-claiming."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes over-dramatizes — re-pin restraint."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid arc; can blur escalation and resolution timing."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Defaults to telling-not-showing; sharpen with specifics."},
        ],
        "variations": [
            {"label": "Multi-protagonist", "description": "When the story has co-protagonists.", "prompt_snippet": "Add: ‘the story may have two protagonists (team A vs team B, or customer vs product). Track both arcs and show their interaction.’"},
            {"label": "Anti-success story", "description": "When the data shows failure.", "prompt_snippet": "Add: ‘this is a failure story — be honest about what didn't work; the lesson is in the failure mode, not a turnaround.’"},
            {"label": "Three-act structure", "description": "Acts I/II/III explicit.", "prompt_snippet": "Replace 5-beat structure with explicit Act 1/2/3 — setup, confrontation, resolution. Same content; different scaffolding.’"},
        ],
        "failure_modes": [
            {"symptom": "Reads like a press release, not a story.", "fix": "Re-pin: ‘open in scene, ground in specifics, restraint over hyperbole.’"},
            {"symptom": "Numbers feel slapped in.", "fix": "Add: ‘numbers land at moments where they change the story’s meaning; don't list them.’"},
            {"symptom": "Lesson is title-carded.", "fix": "Add: ‘the lesson is implied by where the story ends — never written as a moral.’"},
            {"symptom": "Invented data.", "fix": "Add: ‘if you need a beat the data doesn't support, surface it as missing — don't invent.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["story-with-character-arc", "investor-update-monthly", "weekly-metrics-narrative"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["narrative-arc", "data-storytelling"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "When does data merit narrative vs dashboard?", "answer": "When the data has a SHAPE worth communicating: a change over time, a cause-effect, a turn. Static snapshots don't have an arc; trends and decisions do."},
            {"question": "How do I avoid the ‘before/after’ cliché?", "answer": "Don't structure it as before/after. Structure as protagonist-pursuing-goal hits obstacle, escalates, decides, lands somewhere. The change is implicit."},
            {"question": "Can this be misused?", "answer": "Yes — narrative can dress up weak data. The honest-about-limits rule (don't invent, don't over-claim) is the guardrail. Always tie back to specific numbers."},
        ],
        "meta_title": "Narrative Arc From Data — Prompt",
        "meta_description": "Turn data into a narrative arc: protagonist, obstacle, escalation, turn, resolution. For case studies, research write-ups, business stories.",
    },
]
