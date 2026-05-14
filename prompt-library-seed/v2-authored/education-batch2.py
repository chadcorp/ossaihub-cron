"""Education prompts — batch 2."""

RECORDS = [
    {
        "slug": "feynman-explanation-test",
        "title": "Feynman Explanation Test",
        "tldr": "Convert your tentative understanding of a topic into a Feynman-style explanation, then identify the gaps in your own understanding via the test of explaining it simply.",
        "category": "education",
        "tags": ["learning", "feynman", "self-test", "comprehension"],
        "best_for_tags": ["self-study", "concept-mastery", "exam-prep"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Self-checking new material", "example": "After reading a chapter on transformers, write your explanation; this prompt finds the gaps."},
            {"scenario": "Before a high-stakes presentation", "example": "Identify weak spots in your explanation before the audience does."},
            {"scenario": "Tutor preparation", "example": "Tutor uses to spot which concepts they themselves don't fully grasp."},
            {"scenario": "Documentation review", "example": "Run on your draft docs; find the assumptions you're making the reader can't follow."},
        ],
        "when_not_to_use": "Skip for memorization (facts, dates) — Feynman is about understanding, not recall. Skip for highly technical detail-level review (use a checklist).",
        "full_prompt": """You are a Feynman-style learning coach. The user has tried to explain a topic in their own words. You'll evaluate that explanation, identify gaps, and prompt them to fix the weak spots.

INPUT
- Topic: {topic}
- The user's attempted explanation: {user_explanation}
- Their audience for the explanation (informs vocabulary): {audience}

OUTPUT

## 1. What's clearly grasped
2-4 specific things the user explained accurately. Be specific — quote phrases from their explanation.

## 2. Spots where understanding is shaky
For each:
- Quote: the specific sentence/phrase that signals shakiness
- Symptom of the shakiness: jargon used without owning the concept / leap that skips a step / metaphor that doesn't quite work / hedging that hides not-knowing
- What this suggests they don't fully understand
- A clarifying question that would force them to confront the gap

3-5 spots. Prefer surface-level shakiness over deep — those are easier to fix.

## 3. Audience-fit check
- Does their explanation match the stated audience?
- Specific terms that are too jargon-heavy or too vague for that audience.

## 4. The Feynman test
Three things they should now try to explain (in their head or aloud) to deepen understanding:
- The hardest sub-concept embedded in the topic
- A counter-example or edge case
- Why the obvious-alternative-explanation is wrong

## 5. Suggested next study move
One specific action: re-read X, work through Y problem, explain Z to someone.

RULES
- Be specific. ‘You don't fully understand X’ is useless; ‘You said X is because of Y, but you didn't say WHY Y leads to X’ is useful.
- Don't grade or score; this is diagnostic.
- Don't supply the answer to the gap — pose the question. The user does the work.
- When the explanation IS solid, say so clearly; don't manufacture weaknesses.

USER'S EXPLANATION
{user_explanation}

Begin.""",
        "input_variables": [
            {"name": "topic", "type": "string", "description": "Topic being explained", "required": True, "example": "How attention mechanisms work in transformers"},
            {"name": "user_explanation", "type": "string", "description": "The user's draft explanation", "required": True, "example": "Attention lets a model focus on the most relevant tokens..."},
            {"name": "audience", "type": "string", "description": "Who they're explaining to", "required": True, "example": "Smart non-ML engineer"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Five sections: what's grasped, shaky spots with diagnostic questions, audience-fit, Feynman test, next study move.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Surfaces genuine gaps without manufacturing them."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally too generous — re-pin specificity."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Holds structure; diagnostic questions can be generic."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Surface critique; needs reminder to quote phrases."},
        ],
        "variations": [
            {"label": "Iterative", "description": "User refines explanation; re-run.", "prompt_snippet": "After Section 5, add: ‘When user resubmits a revised explanation, compare to previous version and note what's improved and what's still shaky.’"},
            {"label": "Multi-audience", "description": "Test the same explanation across 2-3 audiences.", "prompt_snippet": "Add: ‘also evaluate fit for an EXPERT audience and a NOVICE audience; note where adjustments needed.’"},
            {"label": "With self-grade", "description": "User self-grades; compare to AI assessment.", "prompt_snippet": "Add: ‘ask the user to self-grade 1-5 on each section before showing results; flag where their self-grade differs from observed shakiness.’"},
        ],
        "failure_modes": [
            {"symptom": "Manufactures gaps where explanation is solid.", "fix": "Add: ‘if explanation is solid, say so plainly; don't generate fake critique.’"},
            {"symptom": "Provides the answer instead of the question.", "fix": "Re-pin: ‘pose a clarifying question; don't supply the answer.’"},
            {"symptom": "Vague feedback (‘this is unclear’).", "fix": "Force quoting: ‘every gap cites a specific phrase from the user's explanation.’"},
            {"symptom": "Audience mismatch ignored.", "fix": "Add: ‘flag at least 2 specific vocabulary choices that don't match audience.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["socratic-tutor", "concept-map-builder", "study-guide-from-chapter"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["feynman-technique", "active-learning"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How is this different from a tutor?", "answer": "A tutor explains; this prompts you to find your own gaps. Better for long-term retention because YOU do the work of fixing the understanding."},
            {"question": "When do I know I've passed the Feynman test?", "answer": "When you can explain the concept to a smart non-expert, answer their follow-up questions, and articulate WHY adjacent explanations are wrong. Iteration until that point."},
            {"question": "Can this work for math/code?", "answer": "Yes — paste your explanation alongside any equations or code snippets. The prompt finds where your verbal explanation glosses what your equation actually does."},
        ],
        "meta_title": "Feynman Explanation Test — Prompt",
        "meta_description": "Test your explanation of a concept: cite shaky phrases, pose diagnostic questions, identify what's grasped vs not. Active-learning tool.",
    },
    {
        "slug": "spaced-repetition-flashcard-set",
        "title": "Spaced-Repetition Flashcards From Material",
        "tldr": "Generates 20-40 flashcards from notes/textbook/lecture transcript, optimized for spaced-repetition systems (Anki / RemNote): one concept per card, atomic questions, no compound cards.",
        "category": "education",
        "tags": ["flashcards", "spaced-repetition", "anki", "memory"],
        "best_for_tags": ["exam-prep", "memorization", "self-study"],
        "difficulty_tier": "beginner",
        "featured": True,
        "use_cases": [
            {"scenario": "Build flashcards from lecture notes", "example": "Two hours of class notes → 30 atomic cards ready to import into Anki."},
            {"scenario": "Convert textbook chapter to cards", "example": "Chapter on photosynthesis → cards covering definitions, mechanisms, edge cases."},
            {"scenario": "Onboarding documentation", "example": "Company docs → cards new hires use to learn the stack."},
            {"scenario": "Language vocabulary", "example": "Vocabulary list → bidirectional cards (target → English and English → target)."},
        ],
        "when_not_to_use": "Skip for material best learned through doing (programming, art). Skip for understanding-heavy concepts — cards good for facts, weaker for concepts requiring synthesis.",
        "full_prompt": """You are creating spaced-repetition flashcards from study material. Output cards optimized for Anki / RemNote / similar SRS.

INPUT
- Material to convert: {material}
- Target audience: {audience}
- Card count target: {n_cards}
- Card style preference: {style}             (basic Q&A / cloze deletion / image occlusion / mixed)

OUTPUT

For each card, format as:

### Card N

**Front:** <question or prompt>
**Back:** <answer>
**Tags:** <comma-separated tags for category / topic>
**Type:** basic | cloze | image_description

If cloze: front contains {{c1::hidden}} placeholders; back duplicates with the hidden parts marked.

PRINCIPLES (the SRS-Optimal rules)

1. ONE FACT PER CARD. Bad: ‘Define HNSW and IVFFlat’. Good: ‘What does HNSW stand for?’ + ‘What's the main tradeoff of HNSW?’ as two cards.

2. ATOMIC. Each card has ONE specific answer. ‘Discuss the strengths and weaknesses of...’ is not a card.

3. CONTEXT FREE. The front should make sense without the source material. Bad: ‘What's the answer from chapter 3?’ Good: ‘What's the formula for reciprocal rank fusion?’

4. SHORT ANSWERS. If the back exceeds 2 sentences, the card is probably too big — split.

5. BIDIRECTIONAL where useful. Definitions: term → definition AND definition → term.

6. SPECIFIC OVER GENERAL. ‘List the steps of photosynthesis’ is bad; ‘What's the immediate product of the light-dependent reactions?’ is better.

7. AVOID OPTIONAL CONTEXT. ‘Sometimes...’, ‘In some cases...’ — these make the card untestable.

8. CLOZE for relationships and formulas. ‘RRF score = sum of {{c1::1/(k+rank)}}’ works well as cloze.

OUTPUT FORMAT
After all cards, include:
- Total card count
- Tags used (for organizing in SRS)
- A 2-3 line "study order" suggestion (which tag to learn first)
- A list of facts in the material you did NOT make cards from (and why — too contextual / too synthetic / etc.)

MATERIAL
{material}

Begin.""",
        "input_variables": [
            {"name": "material", "type": "string", "description": "Source material to convert", "required": True, "example": "[textbook chapter / lecture notes / article]"},
            {"name": "audience", "type": "string", "description": "Card user (sets vocabulary level)", "required": True, "example": "Engineering bootcamp student"},
            {"name": "n_cards", "type": "integer", "description": "Target number of cards", "required": True, "example": "30"},
            {"name": "style", "type": "string", "description": "Card style preference", "required": False, "example": "Mix of basic Q&A and cloze deletion"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "N numbered cards with Front/Back/Tags/Type fields; then summary section with counts, tags, study order, omitted-facts list.",
        },
        "few_shot_examples": [
            {
                "input": "Material on RRF; n_cards=3",
                "output": "### Card 1\\n**Front:** What does RRF stand for in retrieval systems?\\n**Back:** Reciprocal Rank Fusion\\n**Tags:** rag, retrieval, acronyms\\n**Type:** basic\\n\\n### Card 2\\n**Front:** RRF score = sum of {{c1::1/(k+rank)}} across retrievers, where k is a {{c2::smoothing constant}}.\\n**Back:** RRF score = sum of 1/(k+rank) across retrievers, where k is a smoothing constant.\\n**Tags:** rag, retrieval, formulas\\n**Type:** cloze"
            }
        ],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong atomicity; respects single-fact rule."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally creates compound cards — re-pin one-fact rule."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; cloze formatting sometimes off."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to multi-fact cards; iterate or use stricter prompt."},
        ],
        "variations": [
            {"label": "Image cloze", "description": "Generate cards referencing diagrams.", "prompt_snippet": "Add: ‘for any diagram-related facts, output as image_description type with a 1-line description of what should be on the card image.’"},
            {"label": "Language vocabulary", "description": "Bidirectional language cards.", "prompt_snippet": "Add: ‘for each vocabulary item, produce TWO cards: front=target-language term back=translation, and front=translation back=target-language term.’"},
            {"label": "Anki CSV output", "description": "Direct import format.", "prompt_snippet": "Replace markdown with: ‘output as CSV: front,back,tags,type — ready to import into Anki via File → Import.’"},
        ],
        "failure_modes": [
            {"symptom": "Compound cards (multiple facts).", "fix": "Re-pin: ‘ONE fact per card; split if needed.’"},
            {"symptom": "Context-dependent fronts (‘what's mentioned above?’).", "fix": "Add: ‘every card front must be answerable without the source material visible.’"},
            {"symptom": "Long answers (>2 sentences).", "fix": "Add: ‘back is at most 2 sentences; split otherwise.’"},
            {"symptom": "Omitted-facts list missing.", "fix": "Force: ‘list at minimum 3 facts you chose NOT to card; explain why (synthetic / contextual / too easy).’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["study-guide-from-chapter", "feynman-explanation-test"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["spaced-repetition", "flashcard", "atomic-card"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How many cards from one chapter?", "answer": "Quality > quantity. 20-40 atomic cards per textbook chapter. More than 60 and you're carding inconsequential details; fewer than 15 and you're missing testable facts."},
            {"question": "Cloze vs basic?", "answer": "Cloze for formulas, lists, and relationships. Basic for definitions, single facts, and Q&A patterns. Mix for variety in review."},
            {"question": "Will AI cards work as well as hand-made?", "answer": "Close. AI cards are atomic and well-structured. They miss your personal mnemonics and emphasis — manually adjust 10-20% of cards to match how you think."},
        ],
        "meta_title": "Spaced-Repetition Flashcards From Material — Prompt",
        "meta_description": "Convert study material into 20-40 atomic flashcards optimized for SRS: one fact per card, cloze for formulas, context-free fronts.",
    },
]
