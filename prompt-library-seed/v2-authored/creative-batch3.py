"""Creative — batch 3."""

RECORDS = [
    {
        "slug": "first-line-hook-generator",
        "title": "First-Line Hook Generator (Stop The Scroll)",
        "tldr": "Generates 8 candidate first lines for a piece of writing — each using a different proven hook pattern (anecdote, contrarian claim, specific data, sensory scene, etc.). Marks which works best for the audience and format.",
        "category": "creative",
        "tags": ["hook", "opening", "writing", "copywriting"],
        "best_for_tags": ["content-creators", "founders", "newsletter-writers"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Blog post draft has weak open", "example": "Article reads fine but the open is generic; generate 8 alternative openings to test."},
            {"scenario": "Cold email subject + first line", "example": "Same body, 8 different opening lines for A/B testing."},
            {"scenario": "Social post hook for tweet thread", "example": "First tweet of a thread — make people stop scrolling."},
            {"scenario": "Talk opening at conference", "example": "Spoken-word first line that earns the next 5 minutes of attention."},
        ],
        "when_not_to_use": "Skip for emails to people you know well (over-engineered). Skip for technical reference docs where the opening should just state what the doc is.",
        "full_prompt": """You are generating 8 candidate first lines using different proven hook patterns.

INPUT
- Topic / what the piece is about: {topic}
- Audience: {audience}
- Format: {format}                        (blog post, tweet, cold email, talk, etc.)
- Voice: {voice}                          (matter-of-fact, playful, technical, etc.)
- The piece's THESIS in one sentence: {thesis}

OUTPUT — 8 first lines, each using a different pattern

For each:

### N. <Pattern name>
**Line:** "<the actual first line>"
**Why it works for this audience:** 1 sentence
**Why it might fail:** 1 sentence

PATTERNS (use these 8, in this order)

1. SPECIFIC ANECDOTE — a small moment with sensory detail
   "On Tuesday I watched a Series B founder lose 40 minutes trying to delete a row."

2. CONTRARIAN CLAIM — bold, defensible, surprising
   "Most prompt engineering advice will make your prompts worse."

3. SPECIFIC NUMBER + COUNTER-INTUITIVE — data hook
   "73% of our trial users never see the dashboard, and we like it that way."

4. SENSORY SCENE — drop reader into a moment
   "The Slack message at 11:47 PM was just two words: 'site's down.'"

5. QUESTION WITH STAKES — open question the audience cares about
   "Why does every AI starter project look the same — and what would happen if we stopped copying?"

6. PARADOX / TENSION — two things that should not coexist but do
   "Our best-paid engineer can't deploy code, and that's our most strategic decision in two years."

7. CALLBACK / ESTABLISHED THING — reference a shared assumption, then complicate
   "Everyone says you should write every day. Everyone is wrong."

8. NEAR-FUTURE PROVOCATION — what's coming, what's about to change
   "In six months, half the AI startup wisdom you read this year will be embarrassing."

## After the 8, pick the TOP 2

State your pick + reasoning + recommended A/B test order.

CRITICAL RULES
- Lines must be ≤25 words (most readers see ~20 words before deciding to scroll past).
- NO clichés: "In today's fast-paced world", "Have you ever wondered", "Did you know that".
- Voice match the input; don't impose generic engagement-baity tone if the voice is dry.
- Lines must connect to the THESIS — not bait-and-switch.

TOPIC: {topic}
AUDIENCE: {audience}
FORMAT: {format}
VOICE: {voice}
THESIS: {thesis}

Begin.""",
        "input_variables": [
            {"name": "topic", "type": "string", "description": "What the piece is about", "required": True, "example": "Why RAG systems quietly hallucinate even with good retrieval"},
            {"name": "audience", "type": "string", "description": "Who's reading", "required": True, "example": "Senior engineers who've shipped RAG to production"},
            {"name": "format", "type": "string", "description": "Format/medium", "required": True, "example": "1,500-word blog post for engineering blog"},
            {"name": "voice", "type": "string", "description": "Voice", "required": True, "example": "Direct, slightly contrarian, technical with personality"},
            {"name": "thesis", "type": "string", "description": "The thesis in one sentence", "required": True, "example": "Most RAG hallucinations come from over-confident citations, not retrieval failures."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "8 numbered patterns each with line + why-works + why-fails; final pick of top 2 with A/B test order.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Varied pattern usage; concrete specifics."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can slip into clichés — call out banned phrases."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; sensory scene lines can be generic."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple topics; less depth for technical."},
        ],
        "variations": [
            {"label": "Genre-tuned patterns", "description": "Different patterns by genre (fiction, business, technical, op-ed).", "prompt_snippet": "Add: ‘adapt patterns to genre. Fiction = scene/dialogue; technical = problem statement; op-ed = contrarian/paradox; business = data/anecdote.’"},
            {"label": "Multi-language", "description": "Same hooks across languages.", "prompt_snippet": "Add: ‘produce variants in {target_languages}; some hook patterns translate poorly — flag where literal translation breaks.’"},
            {"label": "Subject + first-line pair", "description": "For emails: matching subject + open.", "prompt_snippet": "Add: ‘also generate the email SUBJECT LINE that matches each first line — strongest hooks pair subject + first line as one move.’"},
        ],
        "failure_modes": [
            {"symptom": "All lines >25 words.", "fix": "Hard cap: ‘≤25 words. The threshold matters: readers decide at the first sentence visible in feed/inbox.’"},
            {"symptom": "Patterns blur (3 ‘contrarian’).", "fix": "Re-pin: ‘use each pattern exactly once; if you can't write a strong contrarian line, return a fallback with reasoning, don't duplicate another pattern.’"},
            {"symptom": "Voice mismatched (added playfulness to dry voice).", "fix": "Add: ‘match the input voice. Adding tone to please readers undermines trust.’"},
            {"symptom": "Bait-and-switch (hook doesn't connect to thesis).", "fix": "Add: ‘every hook must connect to the THESIS in at most 100 words of body. Bait wins clicks once.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["headline-rewrite-stronger", "linkedin-post-narrative-arc", "newsletter-issue-from-week"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["hook", "lead", "copywriting"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Which pattern usually wins?", "answer": "Depends. SPECIFIC ANECDOTE wins for narrative pieces. SPECIFIC NUMBER + COUNTER-INTUITIVE wins for technical/business. CONTRARIAN wins for op-eds. Test in YOUR context."},
            {"question": "Can I mix patterns?", "answer": "Yes — strongest first lines often combine 2 patterns. ‘On Tuesday a Series B founder lost 40 minutes deleting a row. Most of us would be smart to follow his lead.’ (anecdote + contrarian)"},
            {"question": "Does pattern variety matter or just pick favorite?", "answer": "Variety helps you see what's possible. Then specialize. Once you've found the patterns YOUR voice does best, you can skip generation and write directly."},
        ],
        "meta_title": "First-Line Hook Generator (Stop The Scroll)",
        "meta_description": "Generate 8 first-line hooks using proven patterns — anecdote, contrarian, data, sensory scene, paradox, callback, near-future. Audience-matched.",
    },
    {
        "slug": "world-building-internal-consistency-check",
        "title": "Fictional World Internal Consistency Check",
        "tldr": "Audits a fictional world's rules for internal contradictions. For each, propose TIGHTEN (adjust rule) or EXPLOIT (use as plot point) options with severity.",
        "category": "creative",
        "tags": ["worldbuilding", "fiction", "consistency", "fantasy-sf"],
        "best_for_tags": ["novelists", "screenwriters", "game-narrative"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Mid-novel consistency review", "example": "Author has 60k words; magic system rules drifted; audit shows contradictions before they hit the reader."},
            {"scenario": "Pre-publication beta", "example": "Beta readers flagged ‘this doesn't make sense’ moments; this prompt confirms which are real inconsistencies."},
            {"scenario": "World-bible build-out", "example": "World-building doc with 30 rules; audit for emergent contradictions before writing."},
            {"scenario": "Game design narrative", "example": "RPG with crafting + magic + politics systems; player exploits = contradictions to fix."},
        ],
        "when_not_to_use": "Skip for short stories where rules are implicit. Skip for surrealist work where contradiction is the point.",
        "full_prompt": """You are auditing a fictional world for internal consistency. Find contradictions; propose how to handle each.

INPUT
- World rules (magic, tech, social, economic — bullet list): {world_rules}
- Sample scenes or events (showing how rules play out): {sample_scenes}
- Author's intent (one paragraph on what feels right): {author_intent}
- Genre / register: {genre}

OUTPUT

## 1. Rules as stated
List the rules clearly, numbered. (Restate from input — clarifies what we're auditing.)

## 2. Contradictions found
For each contradiction:

### Contradiction N: <one-line label>
- Rules in tension: which numbered rules conflict
- Why it's a contradiction: 2-3 sentences explaining the logical clash
- Manifestation: what scene/event makes the contradiction visible
- Severity: low (background) / medium (readers will notice) / high (breaks immersion or plot)

## 3. Proposed resolutions (per contradiction)
For each contradiction, two options:

### Option A: TIGHTEN
Adjust one rule to resolve the contradiction. Specify:
- Which rule changes + how
- What this changes about the story (consequences)
- Pros / cons

### Option B: EXPLOIT
Embrace the contradiction as a plot/character resource:
- How the inconsistency becomes a plot point
- Which character notices it / uses it
- Pros / cons

## 4. Emergent rules
2-3 rules the author hasn't stated but that EMERGE from the stated rules + sample scenes. Author should make these explicit or risk drift.

## 5. Unanswered questions
Things the rule set doesn't address that the story will eventually need:
- "What happens when a magic-user dies — does their power transfer?"
- "Are there limits on the number of times this technology can fail?"

## 6. Verisimilitude check
2-3 places where the rules feel ‘convenient’ — too easy for the protagonist OR too neat. Mention without rigid prescription.

CRITICAL RULES
- Don't impose YOUR aesthetic. Author intent governs.
- ‘Exploit the contradiction’ is sometimes the right answer (great fiction lives in productive contradiction).
- Don't manufacture contradictions for completeness — only flag genuine logical clashes.
- Severity matters: low-severity ones can be ignored or noted as background; high-severity demand resolution.

WORLD RULES
{world_rules}

SAMPLE SCENES
{sample_scenes}

AUTHOR INTENT
{author_intent}

Audit.""",
        "input_variables": [
            {"name": "world_rules", "type": "string", "description": "Rules of the world", "required": True, "example": "1. Magic costs life-force; using it ages the caster. 2. Only those born under the Twin Moons can use magic. 3. The Empire executes magic users on sight. 4. There's an underground railroad for magic users to escape. 5. The protagonist's mother was a magic user."},
            {"name": "sample_scenes", "type": "string", "description": "Scenes showing rules in action", "required": True, "example": "Scene 3: Protagonist saves a child with a healing spell, ages only slightly. Scene 7: Empire investigates an underground network."},
            {"name": "author_intent", "type": "string", "description": "What the author is going for", "required": True, "example": "Magic is supposed to feel costly and contraband. Empire is brutal but bureaucratic. Protagonist's relationship with magic should be ambivalent."},
            {"name": "genre", "type": "string", "description": "Genre/register", "required": False, "example": "Adult fantasy, gritty register"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: rules as stated, contradictions found with severity, two resolution options per contradiction (TIGHTEN / EXPLOIT), emergent rules, unanswered questions, verisimilitude check.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on logical chains; respects author intent."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can over-prescribe — re-pin author-intent governs."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Holds genre register; verisimilitude check can be soft."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for shallow worlds; thin on emergent rules."},
        ],
        "variations": [
            {"label": "Soft-magic friendly", "description": "When rules are intentionally fuzzy.", "prompt_snippet": "Add: ‘this is soft-magic — fewer hard rules, more vibes. Find inconsistencies that violate ESTABLISHED facts about specific events, not generic rule mismatches.’"},
            {"label": "Sci-fi tech variant", "description": "For sci-fi with technology rules.", "prompt_snippet": "Replace magic-rules with tech-rules; audit same way. Flag where tech violates established physics OR established AI/economic limits."},
            {"label": "Pre-write world-bible", "description": "Build the bible before writing.", "prompt_snippet": "Take rules in draft form; surface implicit rules and unanswered questions before writing chapter 1."},
        ],
        "failure_modes": [
            {"symptom": "Manufactures contradictions to look thorough.", "fix": "Re-pin: ‘only flag genuine logical clashes. ‘Could be a contradiction’ is not a contradiction.’"},
            {"symptom": "Always recommends TIGHTEN.", "fix": "Force both options per contradiction. ‘Exploit’ is often the better answer for fiction."},
            {"symptom": "Doesn't catch author-intent overrides.", "fix": "Add: ‘where intent contradicts a rule, the rule is the problem, not intent.’"},
            {"symptom": "Imposes a foreign aesthetic.", "fix": "Re-pin: ‘author intent governs. Match register.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["story-with-character-arc", "scene-writing-show-dont-tell", "narrative-arc-from-data"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["worldbuilding", "fictional-consistency"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should every contradiction be resolved?", "answer": "No. Low-severity ones can stay (real life has them). Medium-severity ones are flagged for choice. High-severity ones must be resolved before publication."},
            {"question": "What if I LIKE my contradictory rules?", "answer": "Then EXPLOIT them. Make a character notice. Make plot turn on them. Earned contradiction beats sanitized consistency."},
            {"question": "Mid-novel vs pre-novel use?", "answer": "Pre-novel: catches drift before pages are written. Mid-novel: flags what's now hard to retrofit. Both useful; pre-novel cheaper to act on."},
        ],
        "meta_title": "Fictional World Internal Consistency Check — Prompt",
        "meta_description": "Audit a fictional world for internal contradictions. For each, propose TIGHTEN or EXPLOIT options + emergent rules + verisimilitude check.",
    },
    {
        "slug": "podcast-show-notes-structured",
        "title": "Podcast Show Notes Structured",
        "tldr": "Generates podcast show notes from a transcript: TL;DR, 3-5 key takeaways, timestamps, named guests with credentials, links mentioned, and an outline that helps SEO. Tuned for findability.",
        "category": "creative",
        "tags": ["podcast", "show-notes", "summarization", "seo"],
        "best_for_tags": ["podcasters", "creators", "interview-shows"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Per-episode show notes", "example": "60-min transcript → publishable show notes within 10 min."},
            {"scenario": "Searchable episode archive", "example": "Year-end: regenerate show notes for back catalog to improve search."},
            {"scenario": "Newsletter from episode", "example": "Extract 3-bullet email summary from same transcript."},
            {"scenario": "Repurpose for blog post", "example": "Convert episode into 800-word blog format."},
        ],
        "when_not_to_use": "Skip for highly informal/improvised shows where structured notes feel artificial. Skip for episodes without clear takeaways (light banter).",
        "full_prompt": """You are writing show notes for a podcast episode. Useful for listeners + findable by search.

INPUT
- Episode transcript: {transcript}
- Host name + style: {host_info}
- Guest name + credentials: {guest_info}
- Episode topic: {episode_topic}
- Podcast / show context: {show_context}

OUTPUT (publishable show notes, ~400-600 words)

## TITLE
Episode title in <title>: <Guest>: <provocative short hook> — Episode N

## TL;DR (1-2 sentences)
What this episode is about + why someone should listen.

## Guest
- Name + role/credentials
- One specific thing that makes them worth listening to
- (Optional) link to their work / Twitter / website if mentioned

## Key takeaways (3-5 bullets)
Each is a specific INSIGHT, not a topic. With timestamps.
- "Most B2B sales advice is calibrated for >$100k deals — under $20k, the playbook inverts. (12:34)"
- "Their team kills 30% of features within 90 days of launch; this is a designed function, not a failure. (28:12)"
- "Why ‘great writers read widely’ is bad advice for working writers. (41:50)"

## What you'll learn
- 3-5 things listener walks away knowing or doing differently

## Outline (with timestamps)
- 00:00 Cold open / hook
- 02:15 Introductions
- 04:30 [First section]
- 12:00 [Second section]
- ...
- 58:00 Closing / where to find guest

## Mentioned in this episode
Bullet list with hyperlinks (extracted from transcript):
- Books, articles
- Other podcasts / episodes
- Tools, products
- Other people referenced

## Quotes worth pulling
2-3 verbatim quotes (with timestamp) that would work as social posts.

## Subscribe + share
Standard CTA — only 1-2 lines.

CRITICAL RULES
- Takeaways are SPECIFIC INSIGHTS with numbers/specifics. "We discussed X" is not a takeaway; "X usually fails because Y" is.
- Timestamps must be IN the transcript. Don't invent.
- Outline tracks the actual flow — don't impose a stock structure if the episode wandered.
- Quotes are verbatim with attribution. Pull lines that work standalone (don't need context).
- SEO-helpful: title and TL;DR should include the topic + guest name for discoverability.

TRANSCRIPT
{transcript}

Begin show notes.""",
        "input_variables": [
            {"name": "transcript", "type": "string", "description": "Episode transcript with timestamps if possible", "required": True, "example": "[00:00] Host: Welcome back... [01:15] Guest: Yeah so the way we think about this..."},
            {"name": "host_info", "type": "string", "description": "Host info", "required": True, "example": "Chad Anderson, host of OSS AI Hub Podcast, focuses on practical builder stories"},
            {"name": "guest_info", "type": "string", "description": "Guest details", "required": True, "example": "Jane Doe, ex-Google PM, founder of Acme — building AI dev tools"},
            {"name": "episode_topic", "type": "string", "description": "What the episode is about", "required": True, "example": "Why most AI dev tools fail at adoption (and how Acme's avoiding it)"},
            {"name": "show_context", "type": "string", "description": "Show style/context", "required": False, "example": "Weekly podcast, ~45 min episodes, audience = builders + engineers"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Title + TL;DR + guest section + 3-5 takeaways with timestamps + what-you'll-learn + outline with timestamps + mentioned items + 2-3 pullable quotes + subscribe CTA.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on insight-extraction; faithful quotes."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes invents timestamps — re-pin ‘only from transcript.’"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Handles long transcripts well."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for short episodes; thin on insight extraction."},
        ],
        "variations": [
            {"label": "Episode → newsletter", "description": "Bundle: notes + 3-bullet newsletter version.", "prompt_snippet": "Add: ‘also produce a 100-word newsletter version: the single most interesting insight + a link back to the episode.’"},
            {"label": "Episode → blog post", "description": "Convert to long-form blog.", "prompt_snippet": "Add: ‘also produce a 600-word blog post drawing from the episode — different structure than show notes (more narrative, less list-heavy).’"},
            {"label": "Series wrap-up", "description": "Cross-episode synthesis.", "prompt_snippet": "Add: ‘this is episode N of a series; synthesize themes across the series + tease next episode.’"},
        ],
        "failure_modes": [
            {"symptom": "Takeaways are topics not insights.", "fix": "Re-pin: ‘insights have specifics (numbers, names, mechanisms). ‘We discussed pricing strategy’ is not a takeaway.’"},
            {"symptom": "Timestamps invented (not in transcript).", "fix": "Add: ‘every timestamp must appear in the transcript; if not present, omit the timestamp rather than guess.’"},
            {"symptom": "Quotes paraphrased.", "fix": "Re-pin: ‘pullable quotes are verbatim. If not verbatim, label.’"},
            {"symptom": "Outline imposes stock template.", "fix": "Add: ‘outline tracks the ACTUAL flow. Don't insert ‘Introductions / Topic 1 / Topic 2 / Conclusion’ if the episode wandered.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["thematic-coding-from-transcripts", "newsletter-issue-from-week", "executive-summary-1-page"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["podcast", "show-notes"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Do show notes help discoverability?", "answer": "Yes — search engines index the text. Podcast platforms increasingly use show notes for in-app search. Investing here is high-leverage."},
            {"question": "How long should show notes be?", "answer": "400-600 words is the sweet spot. Below 300 = thin, looks lazy. Above 800 = nobody reads, dilutes."},
            {"question": "Should I publish the full transcript too?", "answer": "Yes if your audience appreciates it (SEO boost too). Separate page or scroll below the show notes. Tools like Otter/Descript automate this."},
        ],
        "meta_title": "Podcast Show Notes Structured — Prompt",
        "meta_description": "Generate publishable show notes from a transcript: TL;DR, specific takeaways with timestamps, outline, pullable quotes. SEO-friendly.",
    },
    {
        "slug": "joke-craft-laymans-tweak",
        "title": "Joke Craft: Tighten a Premise",
        "tldr": "Takes a premise or rough joke and applies craft moves: tighten setup, sharpen the turn, find the strongest tag, suggest alternative angles. NOT a joke generator — a tightener for existing material.",
        "category": "creative",
        "tags": ["comedy", "joke", "craft", "humor-writing"],
        "best_for_tags": ["comedians", "speechwriters", "comedic-content"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Stand-up bit polish", "example": "Premise works conceptually; the setup-to-punch ratio is off; this prompt tightens."},
            {"scenario": "Tweet humor", "example": "Rough joke draft → 3 tightened variants for different angles."},
            {"scenario": "Speech opener", "example": "Conference talk needs to open with one good joke; this prompt sharpens it."},
            {"scenario": "Comedy writing room support", "example": "Junior writer brings premise; this prompt models the craft moves a senior writer would make."},
        ],
        "when_not_to_use": "Skip for sensitive material (use a person, not AI). Skip for highly culturally-specific humor — the AI's reference set isn't yours.",
        "full_prompt": """You are tightening a comedic premise via craft moves. NOT generating from scratch — improving what's there.

INPUT
- The premise or rough joke: {premise}
- Format: {format}                                (stand-up, tweet, speech-opener, parody)
- Audience: {audience}
- The comedic angle you're going for: {angle}    (absurdist, observational, self-deprecating, etc.)

OUTPUT

## 1. The premise restated
What's the joke ACTUALLY about underneath the surface? Pin the comic engine.

## 2. Craft analysis of the input
- Setup length: <words / beats>
- Turn or pivot location: where the surprise happens
- Tag (final beat): is it punching, or trailing off?
- Specificity: where is it specific vs generic?

3-5 sentence honest read.

## 3. Three tightened variants

### Variant A: Shorter setup
Cut the warm-up. Get to the turn faster.
- The joke:
- Word count:
- What changed:

### Variant B: Sharper specificity
Replace generic nouns with surprising specific ones.
- The joke:
- What changed:

### Variant C: Stronger tag
Different ending. The last beat lands the hardest.
- The joke:
- What changed:

## 4. Angle alternatives
2 alternative angles the same premise could go:
- "Could lean into self-deprecating — would change the joke to ..."
- "Could lean into absurdist — would change the joke to ..."

## 5. What to test
A/B test order. Which variant first, why.

## 6. What I left ON purpose
2 things you'd be tempted to ‘fix’ but shouldn't:
- Rhythm beats that feel ‘extra’ but earn the timing
- Specificity that seems random but is the joke

CRITICAL RULES
- Don't sanitize. If the joke has edge, preserve it (within audience).
- Specificity > abstraction. ‘A guy at the DMV’ beats ‘someone at a government office’.
- The TURN should be unexpected; if I can predict it, it doesn't land.
- The TAG should escalate or invert — not just restate the turn.
- Don't impose stock comedy templates if the input has a unique structure.

PREMISE: {premise}

Begin craft analysis.""",
        "input_variables": [
            {"name": "premise", "type": "string", "description": "Rough joke or premise", "required": True, "example": "I tried meditation. It's just sitting there silently feeling bad about all the things you should be doing instead."},
            {"name": "format", "type": "string", "description": "Comedic format", "required": True, "example": "Stand-up bit, ~30 seconds"},
            {"name": "audience", "type": "string", "description": "Audience", "required": True, "example": "Late-20s urban professional audience"},
            {"name": "angle", "type": "string", "description": "Comedic angle target", "required": True, "example": "Self-deprecating observational"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: premise restated, craft analysis, 3 tightened variants (shorter / sharper / stronger tag), angle alternatives, A/B order, what-not-to-touch.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "good", "notes": "Decent specificity moves; comedy is hard for LLMs."},
            {"model": "gpt-4o", "compatibility": "good", "notes": "Stronger reference set for current humor; can be too tame."},
            {"model": "gemini-1.5-pro", "compatibility": "fair", "notes": "Often generic comedy outputs."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Faster iteration; less depth."},
        ],
        "variations": [
            {"label": "Rule of three", "description": "Apply rule-of-three structure.", "prompt_snippet": "Add: ‘variant D: rule of three — three items, last one inverts. Apply if the premise has list potential.’"},
            {"label": "Callback setup", "description": "Set up for later callback.", "prompt_snippet": "Add: ‘variant E: setup-for-callback — premise lays groundwork that pays off later. Useful for set/special with multiple bits.’"},
            {"label": "Cross-cultural check", "description": "Flag culture-bound humor.", "prompt_snippet": "Add: ‘flag any reference that wouldn't land outside the specified audience's culture. Helpful for international or mixed audiences.’"},
        ],
        "failure_modes": [
            {"symptom": "Sanitizes edge.", "fix": "Re-pin: ‘preserve edge within audience. ‘Edgier than audience tolerates’ → flag, don't sanitize.’"},
            {"symptom": "All variants are LONGER.", "fix": "Hard rule: ‘at least Variant A is SHORTER than input.’"},
            {"symptom": "Imposes structure not in input.", "fix": "Re-pin: ‘work with the input's structure; don't force rule-of-three on a non-list premise.’"},
            {"symptom": "Specificity moves are random.", "fix": "Add: ‘specific replacements should connect to the premise's underlying observation, not just sound concrete.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["first-line-hook-generator", "headline-rewrite-stronger", "tighten-prose-30pct"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["comedy-writing", "joke-structure"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is AI good at comedy?", "answer": "Mediocre. AI knows joke STRUCTURES but rarely produces fresh material. This prompt uses AI for the CRAFT moves (cut, specific, tag), which it does competently — not for original wit."},
            {"question": "Will it write offensive material?", "answer": "Edge is preserved within audience norms. AI tends to err safe; if you want sharper, push the input premise further; AI will mostly preserve."},
            {"question": "Can it learn my voice?", "answer": "Add 3-5 of your past tightened jokes to the prompt as ‘voice reference’. Output will lean toward your voice. Better than generic but no substitute for your ear."},
        ],
        "meta_title": "Joke Craft: Tighten a Premise — Prompt",
        "meta_description": "Apply craft moves to tighten a rough joke: cut setup, sharpen specificity, find the strongest tag. Three variants + angle alternatives.",
    },
]
