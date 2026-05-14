"""Writing & editing prompt library — v2 authored (2026-05-14)."""

RECORDS = [
    {
        "slug": "blog-post-from-outline",
        "title": "Blog Post from Outline (voice-matched + sourced)",
        "category": "writing-editing",
        "tldr": "Expand a bullet-point outline into a 800-1500 word blog post matching a sample-voice. Includes specific examples, real-world numbers, and 'so what' takeaways per section.",
        "tags": ["blog", "long-form", "voice-match"],
        "best_for_tags": ["content-marketing", "blog-writing", "long-form"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "full_prompt": (
            "You write blog posts that don't read like AI wrote them. Voice-match a reference sample. Don't pad. Every section earns its place.\n\n"
            "INPUTS:\n- outline: bullet-point outline (sections + key points)\n- target_length: word count target\n- voice_sample: 1-2 paragraphs from the same author for voice anchor\n- audience: who reads this\n- avoid_phrases: list of phrases the author never uses\n\n"
            "STRUCTURE:\n1. Hook (50-100 words): specific opening — a number, a moment, a contrarian claim. NOT 'In today's fast-paced world...'.\n2. Body sections (per outline bullet): each ends with a 1-sentence 'so what' that ties to the audience's reality.\n3. Examples (every claim): pull from the outline; if outline has no examples, generate concrete ones (named companies, real numbers, specific dates).\n4. Closer (75-150 words): one thought worth taking away, not a recap.\n\n"
            "VOICE-MATCH RULES:\n- Sentence-length variance: match the sample's mix of short + long sentences.\n- Vocabulary: contractions or not? Technical terms or plain? Match.\n- Authority markers (e.g., 'in my experience', 'we shipped X') — preserve or omit based on sample.\n\n"
            "FORBIDDEN (always, even if not in avoid_phrases):\n- 'leverage', 'unlock', 'unleash', 'game-changing', 'next-level', 'in today's fast-paced world'\n- 'Let me show you...', 'Here's the thing:', 'But here's the kicker:'\n- Hashtag-style intro questions ('Tired of X?')\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "outline", "type": "string", "description": "Bullet-point outline", "required": True, "example": "- Why we moved off seat-based pricing\n- The 3 surprises\n- What we'd do differently\n- Concrete metrics 6mo in"},
            {"name": "target_length", "type": "integer", "description": "Word count target", "required": True, "example": "1200"},
            {"name": "voice_sample", "type": "string", "description": "1-2 paragraphs from same author", "required": True, "example": "We don't use the word 'leverage' here. We say 'use'. ..."},
            {"name": "audience", "type": "string", "description": "Who reads this", "required": True, "example": "SaaS founders at $1-10M ARR"},
            {"name": "avoid_phrases", "type": "list[str]", "description": "Phrases the author never uses", "required": False, "example": "['game-changer', 'tech stack']"},
        ],
        "expected_output": {"format": "markdown", "sample": "# Why we killed seat-based pricing (6 months in)\n\nIn April we removed per-seat pricing for accounts above $50k ARR. By October, ARR was up 23% and churn was flat. Here's what surprised us — and what we'd do differently...\n\n## The 3 surprises\n### Surprise 1: Most teams didn't add seats they were 'saving'\n[concrete example with numbers]\n\nSo what: if you're nervous that usage-based will cap revenue, the cap was probably imaginary.\n..."},
        "use_cases": [
            {"scenario": "Founder newsletter weekly post", "example": "Outline of 4 bullets → 1200-word post in author's voice."},
            {"scenario": "Engineering blog drafts", "example": "Lead engineer's outline → polished draft for review."},
            {"scenario": "Ghostwriting series", "example": "Ghostwriter feeds outline + 3 prior posts as voice samples; generates v1 the named author edits."},
            {"scenario": "Case study expansion", "example": "Sales-engineering team has bullet-form case study; this prompt produces the marketing-ready version."},
        ],
        "when_not_to_use": "Don't use for technical reference docs — different prompt territory. Also skip for highly personal essays where the author's specific phrasing is the point.",
        "few_shot_examples": [
            {"input": "outline: '- Moved off K8s after 2 years - Why - What we use now - Lessons'. voice_sample: 'We picked K8s in 2022 because everyone said to. Two years later we ripped it out. Here's what happened.' length: 800. audience: 'eng leaders'",
             "output": "[Direct opener with specific date + claim, body sections each ending with operational lesson, closer that's a single observation worth taking away — not a recap. 820 words, ~12 short and 8 medium sentences matching sample rhythm.]"},
        ],
        "model_compatibility": [
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best at voice-match and avoiding AI clichés."},
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Reliable default for most posts."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Reaches for 'in today's fast-paced world' if not blocked; reinforce forbidden list."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; expect to manually punch up 2-3 sections."},
        ],
        "variations": [
            {"label": "Twitter-thread companion", "description": "Generate a 10-tweet thread summarizing.", "prompt_snippet": "After the post, generate a 10-tweet thread (240 chars each) that pulls the most quotable lines. Tweet 1 hooks, tweet 10 links to the post."},
            {"label": "Newsletter format", "description": "Shorter, more direct.", "prompt_snippet": "Target_length override: 500-700 words. Add a 'TL;DR' at top (2 sentences). Newsletter readers skim."},
            {"label": "SEO-aware", "description": "Hit a target keyword naturally.", "prompt_snippet": "Add INPUT: target_keyword. Use the keyword in title, H2, and 3-5 places in body. Never stuff."},
        ],
        "failure_modes": [
            {"symptom": "Padded sections with no signal", "fix": "Every section needs a 'so what' — if you can't write one, cut the section"},
            {"symptom": "AI clichés slip through ('in this article we'll explore')", "fix": "Forbidden phrases list enforced; reject and rewrite"},
            {"symptom": "Voice drifts to corporate-speak in body", "fix": "Re-check voice_sample mid-draft; rewrite any paragraph that doesn't match rhythm"},
            {"symptom": "Generic examples ('many companies have found that...')", "fix": "Examples must be specific — named, dated, numbered. If outline lacks specifics, generate plausible ones explicitly marked '[example]'"},
        ],
        "tested_with": {"models": ["claude-opus-4", "claude-sonnet-4-5", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["email-thread-respond", "ad-headline-variations", "investor-update-monthly"],
        "related_tool_slugs": ["substack", "ghost", "notion"],
        "related_glossary_slugs": ["voice-and-tone", "long-form-writing"],
        "faq": [
            {"question": "How much voice-match can I expect?", "answer": "~70-85% match on rhythm and vocab choices. Won't catch the author's specific obsessions or running jokes — humans still edit."},
            {"question": "What length is the sweet spot?", "answer": "800-1500 words for blog. <500 is newsletter. >2000 starts losing reader attention without strong narrative."},
            {"question": "Can it write multiple posts in a series?", "answer": "Yes — pass previous_posts as context to maintain voice continuity. Cap at 5 priors (more = context bloat)."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Blog Post from Outline — Voice-Matched, No AI Clichés",
        "meta_description": "Expand a bullet outline to 800-1500 word blog post matching a sample voice. Specific examples, 'so what' per section, forbidden-phrase list.",
    },
    {
        "slug": "email-thread-respond",
        "title": "Email Reply Drafter (tone-matched)",
        "category": "writing-editing",
        "tldr": "Draft an email reply matching the original sender's tone (formal/casual/terse), addressing every question raised, with clear next steps and no fluff openings.",
        "tags": ["email", "tone-match", "productivity"],
        "best_for_tags": ["email", "communication", "productivity"],
        "difficulty_tier": "beginner",
        "full_prompt": (
            "You draft email replies that read like the user wrote them. Match the sender's tone — formal email gets a formal reply, terse Slack-style gets terse. Address every question they asked. No openings like 'Thanks for reaching out!' unless the sample shows that.\n\n"
            "INPUTS:\n- incoming_email: the email being replied to\n- user_voice_sample (optional): 1-2 prior emails the user wrote, to match their voice\n- desired_outcome: what the user wants this reply to achieve\n- constraints (optional): things to mention or avoid (e.g., 'don't commit to a date')\n\n"
            "PROCEDURE:\n1. Identify every question or ask in the incoming email.\n2. Match tone of incoming email:\n   - Formal (Mr/Ms, complete sentences): reply formal\n   - Casual (Hi <first name>, contractions): reply casual\n   - Terse (no greeting, one line): reply terse\n3. Address each question/ask with a direct sentence. No padding.\n4. End with clear next step OR 'no action needed'. Don't end with 'Let me know if you have questions!' unless sample shows that pattern.\n5. Sign-off matches the sample's style.\n\n"
            "RULES:\n- Never open with 'Hope this email finds you well' or 'Thanks for your email'.\n- If user voice unknown, default to: short greeting, direct answers, brief sign-off.\n- 50-200 words for most replies. 200-400 for complex multi-question emails. Never over 400.\n- Don't apologize for delays unless sample shows that pattern.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "incoming_email", "type": "string", "description": "Email being replied to", "required": True, "example": "Hi Jordan, two questions: (1) Can we move our weekly to Tuesdays at 3pm? (2) Did you see my note about the Q3 budget? Thanks, Sam"},
            {"name": "user_voice_sample", "type": "string", "description": "Prior emails from the user", "required": False, "example": "Hey Sarah — yes that works. I'll send the draft Friday. — Jordan"},
            {"name": "desired_outcome", "type": "string", "description": "What this reply should achieve", "required": True, "example": "Accept the Tuesday slot, ask for more time on the budget"},
            {"name": "constraints", "type": "list[str]", "description": "Things to mention or avoid", "required": False, "example": "['Don't commit to a date for the budget review yet']"},
        ],
        "expected_output": {"format": "text", "sample": "Hey Sam — yes Tuesdays at 3pm works. On the Q3 budget: I saw the note but haven't been able to dig in yet. Let me get back to you by end of next week. — Jordan"},
        "use_cases": [
            {"scenario": "Inbox triage automation", "example": "User flags emails for AI draft; this prompt produces drafts in user's voice for one-click send."},
            {"scenario": "Executive assistant workflow", "example": "EA pastes incoming + brief on what to say; gets first draft in exec's voice."},
            {"scenario": "Cold-email follow-up", "example": "Follow-up after first cold email — match the original's tone."},
            {"scenario": "Customer-support escalation reply", "example": "Manager replying to escalated thread — sound human, not corporate."},
        ],
        "when_not_to_use": "Don't use for sensitive HR / legal emails — these need human review for liability. Also skip for emails where the user disagrees with the desired_outcome and is venting (the tone won't be right).",
        "few_shot_examples": [
            {"input": "incoming: 'Where's the data?' (terse). desired: send the link. voice_sample: 'Here. — J'",
             "output": "Here: drive.example.com/q3-data. — J"},
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at tone-match without over-formalizing."},
            {"model": "claude-haiku-4-5", "compatibility": "excellent", "notes": "Recommended for production — fast, cheap, voice-matches well with sample."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Slightly more formal default; reinforce voice rules."},
            {"model": "llama-3.3-70b", "compatibility": "good", "notes": "Workable for casual replies."},
        ],
        "variations": [
            {"label": "No-commit mode", "description": "Acknowledge without committing to anything.", "prompt_snippet": "Constraint added: 'Don't commit to dates, numbers, or decisions. Reply with acknowledgment + offer to follow up.'"},
            {"label": "Multi-language", "description": "Reply in same language as incoming.", "prompt_snippet": "Detect incoming_email language. Reply in same language. Voice rules apply within that language."},
            {"label": "Decline-politely mode", "description": "Say no without being a pushover or apologetic.", "prompt_snippet": "Decline the request directly + offer one alternative if one exists. Don't apologize 3 times. Don't pretend it's a scheduling issue if the answer is just no."},
        ],
        "failure_modes": [
            {"symptom": "Opens with 'Thanks for reaching out!' when sender didn't initiate", "fix": "Drop generic openings; match sample style"},
            {"symptom": "Adds 'Let me know if you have any questions!' to terse replies", "fix": "Match sender's sign-off pattern; terse → terse"},
            {"symptom": "Doesn't answer one of the questions", "fix": "Procedure step 1 — list every question; verify each is addressed"},
            {"symptom": "Padded reply (200 words when 50 would do)", "fix": "Length-cap by complexity of incoming email; default to 'shortest that's complete'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-haiku-4-5", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["support-response-empathetic", "blog-post-from-outline"],
        "related_tool_slugs": ["superhuman", "shortwave"],
        "related_glossary_slugs": ["tone-of-voice", "email-etiquette"],
        "faq": [
            {"question": "How many voice samples do I need?", "answer": "1-3 is plenty. More starts diluting — your voice across many contexts varies."},
            {"question": "Can it handle multi-thread context?", "answer": "Pass the thread as incoming_email; it'll address the latest message but use thread for context."},
            {"question": "What about emojis?", "answer": "Match the sender. If they use 👋 you can use 👋. If they don't, don't add."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Email Reply Drafter — Tone-Matched, Direct, No Fluff",
        "meta_description": "Draft email replies matching sender tone (formal/casual/terse). Address every question. No 'Thanks for reaching out!' openers.",
    },
    {
        "slug": "headline-rewrite-stronger",
        "title": "Headline Rewriter (5x Stronger)",
        "category": "writing-editing",
        "tldr": "Rewrite a weak headline into 5 stronger options across distinct angles (specificity, contrarian, benefit, curiosity, urgency). Surface which one fits which context.",
        "tags": ["headlines", "copy", "rewrite"],
        "best_for_tags": ["copywriting", "headlines", "marketing"],
        "difficulty_tier": "beginner",
        "full_prompt": (
            "You rewrite weak headlines into 5 distinct strong versions. Different angles let the user pick what fits the context.\n\n"
            "INPUTS:\n- weak_headline: the original\n- about: 1-sentence description of what the post/page is\n- audience: who reads this\n- character_limit: max chars (default 70)\n- forbidden_words (optional)\n\n"
            "GENERATE 5 versions, one per angle:\n1. SPECIFIC: replace vague words with concrete numbers/names\n2. CONTRARIAN: take the opposite stance of the obvious framing\n3. BENEFIT-LED: lead with outcome for the reader, not the topic\n4. CURIOSITY: tease without spoiling\n5. URGENT: time/scarcity (only if real)\n\n"
            "FOR EACH: 1-line label + the headline + 1-line 'when this fits' note.\n\n"
            "RULES:\n- Under character_limit each.\n- No 'How to...', 'X tips for...', 'The ultimate guide to...' — these read as listicle clickbait.\n- Don't make every version about you (avoid 'we', 'our' unless natural).\n- Real urgency only — don't invent scarcity.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "weak_headline", "type": "string", "description": "Original headline to rewrite", "required": True, "example": "Why You Should Use Vector Databases for AI Apps"},
            {"name": "about", "type": "string", "description": "What the post is about", "required": True, "example": "Our 6-month experience migrating from Postgres to Qdrant for RAG at 10M vectors"},
            {"name": "audience", "type": "string", "description": "Reader", "required": True, "example": "Engineering leads building RAG"},
            {"name": "character_limit", "type": "integer", "description": "Max chars", "required": False, "example": "70"},
            {"name": "forbidden_words", "type": "list[str]", "description": "Words to avoid", "required": False, "example": "['unleash','revolutionize']"},
        ],
        "expected_output": {"format": "markdown", "sample": "1. **Specific:** \"Why we moved 10M vectors off Postgres after 6 months\"\n   _Best when the audience needs proof you've actually done it._\n\n2. **Contrarian:** \"Postgres + pgvector is fine. Until it isn't.\"\n   _Use when readers are pgvector-loyal and need to be unsettled._\n\n3. **Benefit-led:** \"Cut RAG p99 latency from 850ms to 80ms\"\n   _For latency-sensitive readers; leads with the metric._\n\n4. **Curiosity:** \"The vector-DB choice we wish we'd made 6 months earlier\"\n   _For browse-mode readers; works in newsletters._\n\n5. **Urgent:** \"Five vector DBs to evaluate before your next sprint\"\n   _Only if there's a real timeline pressure for the audience._"},
        "use_cases": [
            {"scenario": "Blog post pre-publish review", "example": "Run on every draft; pick the version that fits the channel (Twitter vs newsletter vs blog)."},
            {"scenario": "Subject line A/B testing", "example": "5 versions become 5 subject-line cohorts."},
            {"scenario": "Landing page hero refresh", "example": "Quarterly hero re-test; rotate one of these in."},
            {"scenario": "Podcast episode titling", "example": "Same episode, 5 angle options; pick what fits show's voice."},
        ],
        "when_not_to_use": "Don't use for regulated industries where every headline needs legal review. Also skip for evergreen academic content where standard descriptive titles are expected.",
        "few_shot_examples": [
            {"input": "weak: 'How to Make a Better Resume'. about: 'data on resume formats that get interviews in tech'. audience: 'job-seekers in tech'",
             "output": "1. Specific: \"7 resume formats we tested across 1,200 tech apps — only 2 worked\"\n2. Contrarian: \"Your resume is fine. Recruiters skip you for a different reason.\"\n3. Benefit: \"Cut your time-to-first-interview in half\"\n4. Curiosity: \"The one resume change that doubled callback rates\"\n5. Urgent: \"Resume changes that matter before May 1 hiring freeze\""},
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at the 5-angle variety without repetition."},
            {"model": "gpt-5", "compatibility": "excellent", "notes": "Strong at specificity + contrarian."},
            {"model": "claude-haiku-4-5", "compatibility": "good", "notes": "Cheap for bulk; sometimes mild."},
            {"model": "llama-3.3-70b", "compatibility": "good", "notes": "Workable; expect to manually punch 1-2."},
        ],
        "variations": [
            {"label": "10 variations", "description": "Double the output across 10 angles.", "prompt_snippet": "Add 5 more angles: data-led, controversial, personal-anecdote, list-style, question-form. 10 total."},
            {"label": "SEO-targeted", "description": "Include target keyword.", "prompt_snippet": "Add INPUT target_keyword. Every variation must include the keyword naturally (not stuffed)."},
            {"label": "Subject-line mode", "description": "Email-specific.", "prompt_snippet": "Character limit 40. Optimize for inbox preview. Lowercase preferred."},
        ],
        "failure_modes": [
            {"symptom": "All 5 variations sound similar", "fix": "5 distinct angles; reject if two are too close"},
            {"symptom": "Defaults to clickbait formulas ('You Won't Believe...')", "fix": "Forbidden patterns list; reject clickbait shapes"},
            {"symptom": "Generic specificity ('5 ways to...')", "fix": "Specificity needs a concrete number/name from the about input"},
            {"symptom": "Over character limit", "fix": "Strict count; regenerate the offending one"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-haiku-4-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["ad-headline-variations", "blog-post-from-outline"],
        "related_tool_slugs": ["copy-ai"],
        "related_glossary_slugs": ["headline-formulas", "copywriting"],
        "faq": [
            {"question": "Which angle usually wins?", "answer": "Specificity for blog/SEO. Curiosity for newsletter. Benefit for landing pages. Contrarian for social. Urgent if there's a real deadline."},
            {"question": "Should I A/B test all 5?", "answer": "No — pick 2-3 you'd actually use, test those. Spreading too thin produces noise."},
            {"question": "What if none of the 5 feel right?", "answer": "Re-run with a sharper 'about' input. Vague inputs produce mediocre headlines."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Headline Rewriter — 5 Stronger Versions, 5 Angles",
        "meta_description": "Turn a weak headline into 5 distinct strong versions across specific/contrarian/benefit/curiosity/urgency. With context fit notes.",
    },
    {
        "slug": "tighten-prose-30pct",
        "title": "Tighten Prose by 30% (preserve meaning)",
        "category": "writing-editing",
        "tldr": "Cut a draft by ~30% without losing any claim or example. Returns the tightened version + a list of every cut and the reason.",
        "tags": ["editing", "tightening", "concision"],
        "best_for_tags": ["editing", "concision", "prose-cleanup"],
        "difficulty_tier": "beginner",
        "full_prompt": (
            "You tighten prose. Remove redundancy, hedging, and padding. Preserve every claim and example.\n\n"
            "INPUTS:\n- draft: the original text\n- target_reduction_pct: how much to cut (default 30%)\n- preserve_voice (bool): if true, match the author's rhythm; if false, aim for maximum density\n\n"
            "PROCEDURE:\n1. Read the draft. Count words.\n2. Cut targets:\n   - Hedging: 'I think', 'it seems', 'arguably', 'perhaps' (remove or commit)\n   - Throat-clearing: 'It's important to note that', 'As we'll see', 'In this section'\n   - Redundant adjectives: 'completely free', 'absolutely critical', 'each and every'\n   - Filler clauses: 'in order to' → 'to'; 'due to the fact that' → 'because'\n   - Repeated points (consolidate into one)\n   - 'There is/are' constructions where direct verb works\n3. Preserve all: claims, examples, numbers, names, conclusions.\n4. Output tightened version + diff showing cuts with 1-line reason per cut.\n\n"
            "RULES:\n- Don't reorganize structure — same paragraphs, same order.\n- Don't change voice (if preserve_voice true).\n- If you can't cut to target without losing signal, output current best + explanation.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "draft", "type": "string", "description": "Original prose", "required": True, "example": "It's important to note that, in our experience, the use of cache has, in many cases, completely eliminated the previously observed latency issues that were affecting our users..."},
            {"name": "target_reduction_pct", "type": "integer", "description": "Target % to cut", "required": False, "example": "30"},
            {"name": "preserve_voice", "type": "boolean", "description": "Keep author's voice", "required": False, "example": "true"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Tightened (32% shorter — 410 → 280 words)\n\nCaching eliminated the latency issues our users hit...\n\n## Cuts\n- 'It's important to note that' → removed (throat-clearing)\n- 'in our experience' → kept once at the top, removed 3 other instances (repeated hedge)\n- 'in many cases' → removed (hedge)\n- 'completely eliminated' → 'eliminated' (redundant intensifier)\n- 'the previously observed latency issues that were affecting' → 'the latency issues' (filler clause)"},
        "use_cases": [
            {"scenario": "Pre-publish blog tighten", "example": "Run on every draft before publishing; typical 25-35% reduction with no signal loss."},
            {"scenario": "Email shortening", "example": "Long reply → tight reply. Cuts hedging that makes emails feel uncertain."},
            {"scenario": "Slack message cleanup", "example": "Long async update → punchy version coworkers will actually read."},
            {"scenario": "Pitch deck slide notes", "example": "Speaker notes too long for screen; cut to deliverable in 30 seconds."},
        ],
        "when_not_to_use": "Don't use for legal/regulatory text where hedging is intentional. Also skip for fiction where rhythm and pacing rely on 'redundancy'.",
        "few_shot_examples": [
            {"input": "draft: 'It is generally believed by many experts that there is a possibility that the use of caching mechanisms could potentially help reduce the latency.' target: 30%",
             "output": "Tightened: 'Caching reduces latency.'\nCuts: 'It is generally believed by many experts that' (throat-clearing), 'there is a possibility' (hedge), 'could potentially' (double hedge), 'the use of...mechanisms' (filler)."},
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at preserving meaning during aggressive cuts."},
            {"model": "claude-haiku-4-5", "compatibility": "excellent", "notes": "Cheap + reliable for production editing pipelines."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong; sometimes too aggressive."},
            {"model": "llama-3.3-70b", "compatibility": "good", "notes": "Workable for English; weaker on subtle hedging cuts."},
        ],
        "variations": [
            {"label": "Aggressive 50%", "description": "When you really need it shorter.", "prompt_snippet": "Target_reduction_pct: 50. Acknowledge some signal loss may occur; flag any cuts that risk meaning."},
            {"label": "Hedge-only", "description": "Only remove hedges, nothing else.", "prompt_snippet": "Only touch hedges and qualifiers. Leave structure and examples untouched."},
            {"label": "Translation-prep", "description": "Pre-tighten before machine translation.", "prompt_snippet": "Optimize for translation: short sentences, no idioms, no 'whose'/'which' clauses. Cuts often >40%."},
        ],
        "failure_modes": [
            {"symptom": "Cuts a claim or example", "fix": "Preservation rule mandatory; if asked to cut and only claims remain, return 'cannot cut further without signal loss'"},
            {"symptom": "Reorders paragraphs", "fix": "Same paragraph order; same paragraph count"},
            {"symptom": "Changes voice (e.g., formalizes casual draft)", "fix": "Preserve_voice flag enforces match"},
            {"symptom": "Doesn't show cuts (just returns shortened version)", "fix": "Always output cut diff for transparency"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-haiku-4-5", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["blog-post-from-outline", "email-thread-respond", "headline-rewrite-stronger"],
        "related_tool_slugs": ["grammarly", "hemingway"],
        "related_glossary_slugs": ["concision", "editing", "prose-style"],
        "faq": [
            {"question": "Is 30% realistic?", "answer": "Yes for first drafts. Edited drafts may only have 10-15% to cut. If a draft has 50% to cut, the draft is in trouble structurally."},
            {"question": "Will it strip my personality?", "answer": "With preserve_voice=true, no. It cuts padding, not personality. Personality lives in word choice and rhythm, not in 'in our experience'."},
            {"question": "Can it tighten code comments?", "answer": "Yes — pass the comment block as draft. Especially good at cutting 'TODO: figure out a better approach maybe'."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Tighten Prose by 30% — Preserve Every Claim",
        "meta_description": "Cut drafts by ~30% without losing claims or examples. Targets hedging, throat-clearing, filler clauses. Diff per cut.",
    },
]
