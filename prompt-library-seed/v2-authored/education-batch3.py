"""Education — batch 3."""

RECORDS = [
    {
        "slug": "code-walkthrough-for-learner",
        "title": "Code Walkthrough For A Learner",
        "tldr": "Walks a learner through a piece of code line-by-line at their current level: explains every non-obvious decision, calls out idioms, suggests learning detours, and ends with a small exercise.",
        "category": "education",
        "tags": ["teaching", "code-walkthrough", "learning", "onboarding"],
        "best_for_tags": ["bootcamps", "self-study", "junior-onboarding"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Bootcamp lesson on real-world code", "example": "Instructor takes production code; this prompt builds the walkthrough."},
            {"scenario": "Junior engineer onboarding", "example": "First-day repo walkthrough — instead of throwing them at the docs."},
            {"scenario": "Tutorial writing", "example": "Build a written tutorial from working code with explanatory voice."},
            {"scenario": "Self-study", "example": "Found an open-source project worth understanding; walkthrough deepens learning."},
        ],
        "when_not_to_use": "Skip for trivial code (10 lines). Skip when the learner is already at the level of the code — wastes their time.",
        "full_prompt": """You are walking a learner through code at their current level. Explain non-obvious decisions; teach idioms; suggest detours.

INPUT
- Code: {code}
- Language: {language}
- Learner's current level: {learner_level}        (beginner / intermediate / advanced)
- What learner knows / doesn't know: {learner_context}
- Goal: {goal}                                     (just understand / be able to modify / reproduce from scratch)

OUTPUT

## 1. Pre-flight
Before reading line 1, what should the learner know:
- 3-5 concepts that must be familiar
- For each: 1-line refresher or link to docs

## 2. The walkthrough (line-by-line)

For each line or block:
```{language}
<line of code>
```
**What this does (in plain English):**
**Why this approach (vs alternatives):**
**Idiom / pattern (if applicable):**

Only include the "why" and "idiom" sections when there's a non-obvious choice or genuine pattern to teach. Trivial lines get just "what this does."

## 3. Learning detours (2-4)
At specific lines, suggest a SIDE EXPLORATION the learner could take:
- "When we reach line 23 with the `defaultdict`, that's a Python idiom worth a detour: [docs link / explanation]. Comes up everywhere; come back when you've internalized."

These are OPTIONAL — explicitly marked, learner can skip.

## 4. Common confusion
2-3 places in this code that learners typically get stuck:
- "Line 45 looks like recursion but isn't — it's iterative because..."
- "The `_` in `_var` is a Python convention not a language feature."

## 5. Exercise
A SMALL exercise the learner does to test understanding. NOT a homework assignment — a 10-15 min thing:
- "Modify the function to also handle X case. The change is small but requires understanding line 60."

## 6. Where this code falls short
For HONEST learning: places where production code has flaws you wouldn't teach in isolation:
- "This skips error handling for brevity. In real production, lines 30-32 would need try/except."
- "The naming is okay but not great; `process` is vague."

CRITICAL RULES
- Match learner's level. If beginner, don't introduce idioms without explanation. If advanced, don't over-explain trivial lines.
- ONE concept per walkthrough block. Don't pile on.
- Detours are OPT-IN; mark them clearly.
- Honest about flaws — learners trust calibrated explanations more.
- Exercise is SOLVABLE in 15 min, not a take-home.

CODE
{code}

Begin.""",
        "input_variables": [
            {"name": "code", "type": "string", "description": "Code to walk through", "required": True, "example": "def find_duplicates(items):\\n    seen = set()\\n    dupes = set()\\n    for item in items:\\n        if item in seen:\\n            dupes.add(item)\\n        seen.add(item)\\n    return dupes"},
            {"name": "language", "type": "string", "description": "Language", "required": True, "example": "Python"},
            {"name": "learner_level", "type": "string", "description": "Learner level", "required": True, "example": "Beginner (3 months of Python)"},
            {"name": "learner_context", "type": "string", "description": "Specific gaps + knowledge", "required": True, "example": "Knows lists and dicts. Hasn't used sets. Comfortable with for-loops."},
            {"name": "goal", "type": "string", "description": "Learning goal", "required": True, "example": "Be able to write similar utility functions"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: pre-flight concepts, line-by-line walkthrough, learning detours, common confusion, exercise, where this code falls short.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Calibrates to level; honest about flaws."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can over-explain trivial lines — re-pin level matching."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; detours can be generic."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple walkthroughs."},
        ],
        "variations": [
            {"label": "Video-script companion", "description": "Generate video-script walkthrough.", "prompt_snippet": "Add: ‘produce a parallel video script — spoken voice walkthrough with pauses, ~5 min length.’"},
            {"label": "Multi-language", "description": "Same code, multiple languages.", "prompt_snippet": "Run walkthrough first for primary language; then highlight what changes in {alt_language}."},
            {"label": "Diff walkthrough", "description": "Walk through a PR diff.", "prompt_snippet": "Walk through the BEFORE/AFTER code in a PR diff. Explain why each change was made + what risk it addresses."},
        ],
        "failure_modes": [
            {"symptom": "Over-explains trivial lines.", "fix": "Re-pin: ‘only explain non-obvious decisions. Trivial = ‘what this does’ only.’"},
            {"symptom": "Doesn't match learner level.", "fix": "Add: ‘every concept assumed must be in learner_context. Otherwise, refresher needed.’"},
            {"symptom": "Exercise is take-home-sized.", "fix": "Force: ‘exercise solvable in 15 min. If bigger, split or simplify.’"},
            {"symptom": "Glosses over real flaws in code.", "fix": "Force section 6: ‘at least 2 real flaws or shortcuts noted. Honest learners trust calibrated voices.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["code-comment-explainer", "socratic-tutor", "feynman-explanation-test"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["teaching-code", "tutorial"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How long should walkthroughs be?", "answer": "Aim for 5-15 min total reading. Beyond 15 min, learners zone out. Long code = multiple sessions, not one giant walkthrough."},
            {"question": "Should I solve the exercise myself first?", "answer": "Yes if you're using this for someone else's learning. Otherwise the prompt suggests an exercise but you should verify it's well-sized."},
            {"question": "What about teaching architecture?", "answer": "This prompt is for code-level. For architecture, use a different prompt focused on system diagrams and design decisions."},
        ],
        "meta_title": "Code Walkthrough For A Learner — Prompt",
        "meta_description": "Walk a learner through code at their level: non-obvious decisions, idioms, optional detours, an exercise, and honest notes on code flaws.",
    },
    {
        "slug": "quiz-with-distractor-analysis",
        "title": "Quiz Generator With Distractor Analysis",
        "tldr": "Generates multiple-choice quiz questions where each WRONG answer is a real misconception students hold. Includes ‘what the student who picks this answer believes’ — turns the quiz into a diagnostic tool.",
        "category": "education",
        "tags": ["quiz", "assessment", "distractors", "misconception"],
        "best_for_tags": ["teachers", "training", "self-assessment"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Chapter-end quiz", "example": "Create 10 MCQ questions where wrong answers diagnose specific misconceptions."},
            {"scenario": "Training certification", "example": "Cert exam questions; wrong answers reveal what each candidate misunderstands."},
            {"scenario": "Self-assessment for adult learners", "example": "After learning, take quiz; wrong answers diagnose where to study more."},
            {"scenario": "Pre-class diagnostic", "example": "Before teaching topic, quiz to surface what students think they know — and what they get wrong."},
        ],
        "when_not_to_use": "Skip for material with no clear right/wrong (subjective topics). Skip when MCQ format is wrong for the skill (writing, reasoning beyond recall).",
        "full_prompt": """You are writing multiple-choice quiz questions. Wrong answers are REAL misconceptions students hold, not random nonsense.

INPUT
- Topic: {topic}
- Learning level: {level}            (beginner / intermediate / advanced)
- Source material (textbook chunk / article / curriculum): {source_material}
- Number of questions: {num_questions}
- Bloom's level: {bloom_level}        (knowledge / comprehension / application / analysis / synthesis / evaluation)

OUTPUT

For each question:

### Q<N>. <Question text>

A. <option A>
B. <option B>
C. <option C>
D. <option D>

**Correct: <letter>**

**Distractor diagnoses:**
- A: <if student picks A, they believe X> (severity: minor / major)
- B: <if student picks B, they believe X> (severity)
- C: <if student picks C, they believe X> (severity)
- (skip diagnosis for the correct answer)

**Why this question matters:** 1-line on what the question is really testing.

**Common student trap:** the most-picked WRONG answer + why students fall for it.

OUTPUT GUIDELINES

- All 4 options should be PLAUSIBLE on first read.
- Distractors are real misconceptions — NOT obviously wrong joke answers.
- ‘None of the above’ / ‘All of the above’ are LAST-RESORT — only when genuinely the best option.
- Severity:
  - MINOR: a wording error or surface mistake; easy to correct with one sentence
  - MAJOR: a fundamental misunderstanding; needs re-teaching the concept

## After the questions:

### Distribution check
- Are correct answers spread across A/B/C/D? (Test-takers gaming will fail.)
- Difficulty distribution: how many recall vs apply vs synthesize?

### What this quiz misses
2-3 important aspects of {topic} NOT covered by these questions. Useful for instructor follow-up.

CRITICAL RULES
- Distractors must be DIAGNOSTIC. A wrong answer that nobody picks reveals nothing.
- For each distractor, you should be able to name a real misconception. If you can't, that distractor is filler — replace it.
- Test {bloom_level} — don't ask recall questions when you meant application.
- Plain language. ‘Above-grade-level’ wording inflates difficulty without testing understanding.

SOURCE MATERIAL
{source_material}

Begin.""",
        "input_variables": [
            {"name": "topic", "type": "string", "description": "Quiz topic", "required": True, "example": "Photosynthesis: light-dependent reactions"},
            {"name": "level", "type": "string", "description": "Learning level", "required": True, "example": "High school biology, intermediate"},
            {"name": "source_material", "type": "string", "description": "Source content", "required": True, "example": "Light-dependent reactions occur in the thylakoid. Electrons from water are excited by light energy and pass through the electron transport chain. ATP and NADPH are produced..."},
            {"name": "num_questions", "type": "integer", "description": "Number of questions", "required": True, "example": "5"},
            {"name": "bloom_level", "type": "string", "description": "Bloom's level", "required": True, "example": "comprehension"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "N numbered questions with 4 options, correct answer, per-distractor misconception diagnosis, why-it-matters, common-trap. Then distribution check + what-quiz-misses.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Distractors map to real misconceptions; calibrated severity."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can produce nonsense distractors — re-pin diagnostic value."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; can drift from specified Bloom level."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for routine recall questions; thin on application/synthesis."},
        ],
        "variations": [
            {"label": "Scenario-based", "description": "Questions framed in real-world scenarios.", "prompt_snippet": "Adjust: ‘each question presents a scenario; the question asks for the right action / conclusion. Tests application not recall.’"},
            {"label": "Short-answer hybrid", "description": "Convert to fill-in-blank or short-answer with rubric.", "prompt_snippet": "Replace MCQ with short-answer; provide rubric for grading and common wrong-answer patterns."},
            {"label": "Adaptive ladder", "description": "Easy → hard ladder; skip-ahead on correct.", "prompt_snippet": "Generate 3 difficulty levels of the SAME concept; learner advances on correct, falls back on wrong."},
        ],
        "failure_modes": [
            {"symptom": "Distractors are obviously wrong (filler).", "fix": "Re-pin: ‘each distractor maps to a real misconception. Filler = replace.’"},
            {"symptom": "Correct answer is longest / most detailed.", "fix": "Add: ‘balance answer lengths. Distractors and correct should be similar in length.’"},
            {"symptom": "Tests recall when synthesis was asked.", "fix": "Re-pin Bloom level; ensure questions match the level."},
            {"symptom": "‘What this misses’ empty.", "fix": "Force: ‘every quiz has gaps. List 2-3 aspects not covered. Instructor needs this.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["spaced-repetition-flashcard-set", "study-guide-from-chapter", "concept-map-builder"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["assessment", "distractor", "blooms-taxonomy"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why diagnose distractors?", "answer": "An MCQ where every wrong answer reveals a specific misconception is a DIAGNOSTIC — the instructor learns what to re-teach. Without diagnosis, it's just ‘they got it wrong.’"},
            {"question": "How many questions per quiz?", "answer": "5-10 for in-class quiz; 20-30 for chapter test. Spread Bloom levels across the quiz."},
            {"question": "Will distractors actually reflect real misconceptions?", "answer": "AI extrapolates from common patterns. Real classroom data is better. Use this as a starting point; refine based on what your students actually pick."},
        ],
        "meta_title": "Quiz Generator With Distractor Analysis — Prompt",
        "meta_description": "Generate MCQ questions where each wrong answer diagnoses a specific student misconception. Severity + common-trap + what-quiz-misses.",
    },
    {
        "slug": "concept-explainer-with-progressive-depth",
        "title": "Concept Explainer With Progressive Depth",
        "tldr": "Explains a concept at FIVE escalating depths: one-line, paragraph, detailed (1 page), with-math/code, expert-deep-dive. Learner can stop at the depth that suits them.",
        "category": "education",
        "tags": ["explainer", "progressive-depth", "teaching", "learning"],
        "best_for_tags": ["docs", "onboarding", "self-paced-learning"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Concept in onboarding docs", "example": "Most readers want 1-line; some want depth; this prompt covers both efficiently."},
            {"scenario": "Self-study material", "example": "Learner picks depth based on time/curiosity; stops when satisfied."},
            {"scenario": "Glossary entry", "example": "Replaces flat glossary with progressive entries."},
            {"scenario": "Internal wiki entry", "example": "Wiki entry that scales to reader expertise level."},
        ],
        "when_not_to_use": "Skip when audience is uniform (single-depth explanation fits). Skip for trivial concepts (5 depths is overkill for ‘what is a variable’).",
        "full_prompt": """You are explaining a concept at FIVE escalating depths. Each level builds on the previous; reader can stop where it satisfies them.

INPUT
- Concept: {concept}
- Domain context: {domain}
- Typical reader: {reader}

OUTPUT

## Depth 1 — Single sentence
A complete answer in ONE sentence. Plain language. No jargon. (~30 words)

## Depth 2 — Short paragraph
3-5 sentences. Adds context, motivation, one anchor example. (~80-120 words)

## Depth 3 — Detailed explanation
Single page (~400 words). Includes:
- Why it exists / what problem it solves
- How it works at a structural level (not implementation detail)
- One worked example
- Common misconceptions

## Depth 4 — With math / code
Same content but with the formal layer:
- Equations if applicable (LaTeX or plain math)
- Code example if applicable (~30 lines)
- Algorithmic complexity / performance characteristics if relevant
- Key parameter discussions

## Depth 5 — Expert deep-dive
- Variations and edge cases
- Trade-offs vs alternatives
- Open research questions / known limitations
- 2-3 ‘further reading’ pointers with specific titles or paper IDs

EACH DEPTH STANDS ALONE — a reader stopping at Depth 2 should have a complete-feeling answer, even if shallow.

EACH DEPTH BUILDS ON THE PREVIOUS — Depth 3 doesn't repeat Depth 2 verbatim, it elaborates.

CRITICAL RULES
- No jargon until Depth 3 (and define on first use)
- Math/code only at Depth 4+ (don't intimidate early)
- Depth 5 is HONEST about open questions; don't pretend the field is solved
- If a depth doesn't add value for this concept (e.g., no math applicable), say so explicitly rather than padding

CONCEPT
{concept}

DOMAIN: {domain}
READER: {reader}

Now produce all 5 depths.""",
        "input_variables": [
            {"name": "concept", "type": "string", "description": "Concept to explain", "required": True, "example": "Reciprocal rank fusion"},
            {"name": "domain", "type": "string", "description": "Domain context", "required": True, "example": "Information retrieval / RAG"},
            {"name": "reader", "type": "string", "description": "Reader profile", "required": True, "example": "Engineer with general programming background, new to RAG"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Five sections labeled Depth 1-5. Each progressively deeper. Each stands alone. Depth 4 has math/code if applicable. Depth 5 has further reading.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong calibration at each depth."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; depth 1 sometimes over-jargony — re-pin no-jargon."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; expert-depth varies in honesty about open questions."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for shallow concepts; thin at depth 5."},
        ],
        "variations": [
            {"label": "Visual companion", "description": "Suggest a diagram at each depth.", "prompt_snippet": "Add: ‘at each depth, suggest one visual element (diagram, chart, example) that would help. Describe what it'd show.’"},
            {"label": "Interactive exercises", "description": "Add ‘try it’ at each depth.", "prompt_snippet": "Add: ‘at each depth, suggest one quick exercise (under 5 min) the reader does to test understanding before going deeper.’"},
            {"label": "Glossary mode", "description": "More compact for glossary use.", "prompt_snippet": "Compress depths: 1 + 2 + 3 only, shorter at each level. Skip math/code/expert."},
        ],
        "failure_modes": [
            {"symptom": "Jargon at Depth 1.", "fix": "Re-pin: ‘plain language. If you need a term, save it for Depth 3+.’"},
            {"symptom": "Depths repeat each other.", "fix": "Add: ‘each depth ELABORATES, doesn't restate. Don't include Depth 2 verbatim inside Depth 3.’"},
            {"symptom": "Depth 5 pretends everything is settled.", "fix": "Re-pin: ‘list 1-2 open questions or known limitations at expert depth. Honesty distinguishes deep from showy.’"},
            {"symptom": "Padding when a depth doesn't apply.", "fix": "Add: ‘if math/code doesn't apply, SAY SO — don't pad with irrelevant equations.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["feynman-explanation-test", "child-explainer-persona", "research-summary-for-non-experts"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["progressive-disclosure", "explainer"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why 5 depths and not 3?", "answer": "5 levels lets you cover a wider audience efficiently — from someone who heard the word in a meeting (Depth 1) to someone implementing it (Depth 4) to someone designing the next version (Depth 5)."},
            {"question": "Are progressive explainers always better?", "answer": "When audience is mixed, yes. When audience is uniform (e.g., you KNOW your readers are senior engineers), single-depth explanation is more efficient."},
            {"question": "Can I use this for non-technical concepts?", "answer": "Yes. Depth 4's math/code becomes ‘formal definition / examples from practice’ for non-technical topics. Same structure."},
        ],
        "meta_title": "Concept Explainer With Progressive Depth — Prompt",
        "meta_description": "Explain a concept at 5 escalating depths: one-line, paragraph, detailed, with-math/code, expert. Reader stops at the depth that suits them.",
    },
    {
        "slug": "weekly-study-plan",
        "title": "Weekly Study Plan Generator",
        "tldr": "Builds a 7-day study plan for a learner: realistic time budget per day, mix of read/practice/test, rest day, weekly check-in. Tuned for adult learners who often over-commit.",
        "category": "education",
        "tags": ["study-plan", "self-study", "weekly", "schedule"],
        "best_for_tags": ["self-learners", "exam-prep", "career-switching"],
        "difficulty_tier": "beginner",
        "featured": False,
        "use_cases": [
            {"scenario": "Adult learning new skill", "example": "Engineer learning ML; 8-week plan; build the first week."},
            {"scenario": "Cert exam in 30 days", "example": "AWS cert in a month; week-by-week with practice mix."},
            {"scenario": "Career switch prep", "example": "Designer switching to data analyst; weekly study schedule for 12 weeks."},
            {"scenario": "Language learning maintenance", "example": "Maintaining fluency; structured weekly plan beats ad-hoc."},
        ],
        "when_not_to_use": "Skip for casual interest (no deadline, no commitment — flexible learning). Skip when the learner explicitly wants intensive bootcamp pace (use a different prompt).",
        "full_prompt": """You are building a 1-week study plan. Realistic over ambitious — adult learners over-commit.

INPUT
- Topic / skill being learned: {topic}
- Learner's available study hours per week: {hours_per_week}
- Current level: {current_level}
- Goal / target end-state: {goal}
- Learner constraints (no time on M/W, kids on weekends, etc.): {constraints}
- Resources available (book, course, tutor, peers): {resources}

OUTPUT

## 1. Reality check
Before the plan, calibrate:
- Stated hours per week: {hours_per_week}
- Realistic hours per week: <typically 60-70% of stated; adult learners over-estimate>
- Adjusted budget: <what we plan against>
- Note: this prompt plans for the ADJUSTED budget. Stated → adjusted prevents the common ‘fall off the plan in week 2’ failure.

## 2. The week (Mon-Sun)

For each day:
| Day | Time block | Activity | Type | Resource |
|---|---|---|---|---|

Types:
- READ (passive intake)
- PRACTICE (active doing)
- TEST (self-quiz, sample problems)
- REVIEW (re-visit prior material)
- REST (intentional pause)

Constraints:
- One REST day (no study) — yes, this is on the plan
- READ + PRACTICE ratio: ~1:2 (more doing than reading)
- TEST blocks at least 2x per week
- No single block over 90 min for adults

## 3. Weekly check-in
A 15-min self-evaluation, recommended for end of Sunday:
- What did I actually do (not what I planned)?
- What stuck vs what didn't?
- What's the lightest version of next week if I'm behind?

## 4. ‘If I miss a day’ rule
The ONE rule for what to do if a day slips. Specific. Examples:
- "If Tue is missed, skip ahead — don't try to make it up. Make-up = guilt = giving up."
- "If 2+ days missed in a week, REDUCE next week's plan, don't extend."

## 5. Anti-burnout signals
2-3 signals that mean ‘adjust the plan’:
- "Cancelling 2 study blocks in a row = stop and re-plan, don't push through."
- "Reading without retention for 30 min = switch to practice or rest."

CRITICAL RULES
- The REST day is non-negotiable.
- No block over 90 min (cognitive science).
- ADJUSTED budget, not stated. Over-commitment is the #1 failure mode.
- 1:2 read-to-practice ratio. Adult learners default to passive intake.
- Make-up rule is ‘skip ahead, don't make up.’ Falling behind compounds otherwise.

TOPIC
{topic}

HOURS/WEEK: {hours_per_week}
LEVEL: {current_level}
GOAL: {goal}

Build the week.""",
        "input_variables": [
            {"name": "topic", "type": "string", "description": "Topic / skill", "required": True, "example": "Linear algebra (specifically: enough for ML — vectors, matrices, eigenvalues)"},
            {"name": "hours_per_week", "type": "integer", "description": "Stated hours/week available", "required": True, "example": "10"},
            {"name": "current_level", "type": "string", "description": "Current level", "required": True, "example": "Calculus background, no formal linear algebra"},
            {"name": "goal", "type": "string", "description": "End-state goal", "required": True, "example": "Understand papers using SVD and PCA; implement simple matrix ops"},
            {"name": "constraints", "type": "string", "description": "Schedule constraints", "required": False, "example": "No time M/W evenings (kids). 2-hour blocks on weekends."},
            {"name": "resources", "type": "string", "description": "Resources available", "required": False, "example": "3Blue1Brown video series, Strang textbook, peer study group on Fridays"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "5 sections: reality check, 7-day plan table, weekly check-in, miss-a-day rule, anti-burnout signals.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Realistic about adult learner over-commitment."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes plans 60-min blocks that should be 45 — re-pin cognitive limits."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; rest-day discipline can be soft."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple topics."},
        ],
        "variations": [
            {"label": "4-week milestone plan", "description": "Plan whole month not just week.", "prompt_snippet": "Extend: ‘output 4 weeks with monthly milestone. Adjust difficulty curve.’"},
            {"label": "Skill ladder", "description": "What comes before vs after this skill.", "prompt_snippet": "Add: ‘sketch the SKILL LADDER — what prerequisites and what's next after this goal.’"},
            {"label": "Group study variant", "description": "When studying with others.", "prompt_snippet": "Add: ‘include 1-2 group sessions per week (peer study, discussion); designed to test what's solo-stuck.’"},
        ],
        "failure_modes": [
            {"symptom": "Plans full stated hours (over-commits).", "fix": "Re-pin: ‘ADJUSTED budget = 60-70% of stated. Adults over-estimate. Planning to stated hours = falling off plan.’"},
            {"symptom": "No rest day.", "fix": "Re-pin: ‘1 rest day is non-negotiable. Cognitive science.’"},
            {"symptom": "All reading, no practice.", "fix": "Re-pin: ‘read-to-practice ratio 1:2. Adults default to passive intake.’"},
            {"symptom": "‘Make up missed time’ in plan.", "fix": "Re-pin: ‘missed days are SKIPPED, not made up. Make-up creates guilt spiral.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["weekly-priorities-from-vague-list", "study-guide-from-chapter", "lesson-plan-90-min"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["study-plan", "spaced-practice"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why ADJUSTED budget instead of stated?", "answer": "Adult learners reliably overestimate available time. Planning to the full stated budget guarantees falling off — and falling off triggers guilt and quitting. Plan smaller, exceed if possible."},
            {"question": "Will the plan really work?", "answer": "If followed for 4 weeks consistently, yes. If you skip the rest day or push through anti-burnout signals, no — sustainability matters more than intensity."},
            {"question": "What about exam-prep with hard deadline?", "answer": "Same principles. If the deadline forces unsustainable plan, reduce scope of the goal OR push the deadline. Burnout > behind schedule."},
        ],
        "meta_title": "Weekly Study Plan Generator — Prompt",
        "meta_description": "7-day study plan with adjusted-budget calibration, rest day, read-to-practice 1:2 ratio, miss-a-day skip rule, anti-burnout signals.",
    },
]
