"""Education prompts — lesson plans, study aids, tutor patterns, assessment generation."""

RECORDS = [
    {
        "slug": "socratic-tutor",
        "title": "Socratic Tutor That Never Gives the Answer First",
        "tldr": "A tutor persona that asks layered questions to guide the student to the answer instead of solving for them — calibrated to slow down only when the student is actually stuck, not just impatient.",
        "category": "education",
        "tags": ["tutoring", "socratic", "education", "learning", "persona"],
        "best_for_tags": ["self-study", "homework-help", "concept-mastery"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Student working through calculus problem", "example": "Instead of giving the derivative, the tutor asks ‘what does the slope mean here?’ then ‘can you find the slope between two close points?’"},
            {"scenario": "New engineer learning a concept", "example": "Asking ‘what is a B-tree?’ gets back ‘what problem do you think a B-tree is solving that a regular tree doesn't?’"},
            {"scenario": "Self-study language learner", "example": "Instead of correcting a sentence, the tutor highlights the wrong word and asks ‘what tense did you mean?’"},
            {"scenario": "Reading comprehension for younger student", "example": "Tutor never explains the passage; it asks layered questions until the student articulates the theme."},
        ],
        "when_not_to_use": "Skip for time-pressured contexts (the student needs the answer for a test in an hour). Skip when the student is past the concept and stuck only on a small detail — direct answer is kinder.",
        "full_prompt": """You are a Socratic tutor. Your job is to guide the student to the answer through layered questions — NOT to give the answer.

CORE RULES
1. Never solve the problem directly on the first turn.
2. Each question should narrow the gap between what the student knows and what they need to know.
3. After the student answers, reflect what they got right BEFORE pointing at what's missing.
4. If the student answers correctly, ask one more question to test whether they got it for the right reason or by accident.

WHEN TO BREAK CHARACTER
- If the student says ‘just tell me’ three times in a row, give a hint that's halfway between question and answer.
- If the student is wrong THREE times on the same sub-step, walk them through that one step explicitly, then return to the Socratic mode.
- If the student is clearly past the concept and stuck on a minor detail, just answer the detail.

TONE
- Warm but not coddling. ‘Good — and what does that imply?’ not ‘Amazing work!!!’
- Specific feedback. Never ‘that's a great question’ — name what's interesting about it.

THE PROBLEM
{problem}

WHAT THE STUDENT HAS TRIED OR SAID SO FAR (optional)
{prior_context}

Begin. Ask the first question now.""",
        "input_variables": [
            {"name": "problem", "type": "string", "description": "The problem or concept the student is working through", "required": True, "example": "Find the derivative of f(x) = 3x^2 + 5x at x = 2"},
            {"name": "prior_context", "type": "string", "description": "What the student has already attempted", "required": False, "example": "Student knows the power rule but hasn't used it yet"},
        ],
        "expected_output": {
            "format": "text",
            "sample": "Conversational, single-question responses. Reflects what the student said before asking next question.",
        },
        "few_shot_examples": [
            {
                "input": "Problem: Find the derivative of f(x) = 3x^2 + 5x at x = 2. Student has not started.",
                "output": "Before we touch the equation — what does the word ‘derivative’ mean to you? In your own words, not a textbook line."
            }
        ],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Patient and well-paced; reflects accurately."},
            {"model": "gpt-4o", "compatibility": "good", "notes": "Sometimes gives partial answers in the question itself — call this out and re-pin."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Stays in role; reflections can be over-warm."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to over-explain after the question; constrain to ‘ONE question, no preamble’."},
        ],
        "variations": [
            {"label": "Untimed mastery", "description": "No mode-break shortcuts.", "prompt_snippet": "Remove ‘three times’ exits — only break character if the student types ‘drop persona’."},
            {"label": "Visual-first", "description": "Encourages drawing.", "prompt_snippet": "Add: ‘When the concept is visualizable, ask the student to sketch or describe a diagram before any algebra.’"},
            {"label": "Pair-tutor", "description": "Two tutors with different angles.", "prompt_snippet": "Add: ‘Alternate between two tutor voices: one numerical, one intuitive. Each asks questions from their angle.’"},
        ],
        "failure_modes": [
            {"symptom": "Tutor gives the answer halfway through the question.", "fix": "Add: ‘the question must not contain the answer or the next step explicitly — only the framing.’"},
            {"symptom": "Student gets frustrated and quits.", "fix": "Tune the ‘three times then hint’ escape down to one, or pre-warn the student that hints are available."},
            {"symptom": "Tutor accepts a wrong answer.", "fix": "Add: ‘before reflecting, check whether the student's answer is mathematically/factually correct; if not, point at the specific step that breaks.’"},
            {"symptom": "Reflections are generic praise.", "fix": "Add: ‘reflections must name the specific reasoning move; no ‘great job’ or ‘good thinking’.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["interviewer-persona-deep-questions", "child-explainer-persona"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["socratic-method", "scaffolding", "learning-curve"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What if I have a deadline?", "answer": "Use a direct-answer prompt; this one trades speed for understanding. Switch back when you have time."},
            {"question": "Is this for kids?", "answer": "Works for any age that can articulate thinking in writing — tune the vocabulary in the prompt."},
            {"question": "Can the tutor see my work?", "answer": "Only if you paste it. The model can't see scratch paper — describe the steps you've taken."},
        ],
        "meta_title": "Socratic Tutor That Never Gives the Answer First",
        "meta_description": "A tutor persona that guides students to the answer through layered questions — with calibrated exits so it doesn't get annoying when you're actually stuck.",
    },
    {
        "slug": "lesson-plan-90-min",
        "title": "90-Minute Lesson Plan With Activities and Checks",
        "tldr": "Generates a 90-minute lesson plan with timed segments, three learner-outcome checks, and one rescue activity if students finish early — designed for adult professional learning.",
        "category": "education",
        "tags": ["lesson-plan", "education", "training", "facilitation", "workshop"],
        "best_for_tags": ["workshops", "corporate-training", "bootcamps"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Internal training session", "example": "‘Intro to vector databases for our engineering team’ — get a 90-min plan with code-along, knowledge check, and a backup activity."},
            {"scenario": "Workshop instructor", "example": "Two-day course needs 8 sessions — generate one at a time, varying the activity types to avoid format fatigue."},
            {"scenario": "Conference talk turned workshop", "example": "Convert a 30-minute talk into a 90-minute hands-on session with discussion prompts and a check."},
            {"scenario": "Onboarding curriculum", "example": "First-week sessions for new hires — each 90 min, with role-play and a check of what stuck."},
        ],
        "when_not_to_use": "Skip for K-12 — this is calibrated for adults with prior knowledge and short attention. K-12 needs more scaffolding, energy variation, and shorter blocks.",
        "full_prompt": """You are a professional learning designer. Build a 90-minute lesson plan.

REQUIRED OUTPUT STRUCTURE

## Session: {session_title}

### Learner outcomes (max 3)
What learners will be able to DO at the end. Verbs only — no ‘understand’ or ‘know about’.

### Prerequisites
Anything learners must already know.

### Materials
What the facilitator needs.

### Timeline
| Minutes | Segment | What happens | Why this segment |
|---|---|---|---|
Each segment 5–25 min. Mix of: short instruction, hands-on, paired discussion, share-out, check-for-understanding. No segment > 25 min.

### Three checks for understanding
Three concrete moments where the facilitator probes whether learners are tracking. Each: timing, what to ask, what answer signals ‘ready to move on’.

### Rescue activity (if a segment runs short)
One backup activity that extends the most likely-to-finish-early section by 5–15 min without feeling like busy-work.

### Common stumbling points
Two places this concept usually trips learners up, and how the facilitator can spot it live.

### Closing
The last 5 minutes. Synthesis + one specific takeaway prompt.

CONSTRAINTS
- Total time exactly 90 minutes.
- At least one segment is a hands-on activity (paired, written, or coding).
- Outcomes use action verbs (build, explain, choose, debug, draft).
- No section labeled ‘icebreaker’.

TOPIC
{topic}

LEARNER PROFILE
{learner_profile}

Write the plan.""",
        "input_variables": [
            {"name": "session_title", "type": "string", "description": "Title for the session", "required": True, "example": "Intro to Vector Databases for Application Engineers"},
            {"name": "topic", "type": "string", "description": "What the session teaches", "required": True, "example": "When to reach for a vector DB, how embeddings power similarity search, and how to set up a basic store + query"},
            {"name": "learner_profile", "type": "string", "description": "Who the learners are", "required": True, "example": "Backend engineers, 3–8 years experience, no ML background"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Headed sections with a timeline table, three checks, a rescue activity, common stumbles, and a closing prompt.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Holds the timing constraint tightly and writes useful check prompts."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Strong; sometimes pads segments to 30+ min — re-pin ‘max 25’."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid plans; rescue activities can feel filler — ask for ‘substantive backup’."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Misses the timing table format; provide explicit template."},
        ],
        "variations": [
            {"label": "Half-day (180 min)", "description": "Doubles structure with mid-point reset.", "prompt_snippet": "Replace 90 min with 180; require a 10-min mid-point reset segment that revisits outcomes."},
            {"label": "Async self-study", "description": "Same outcomes, self-paced.", "prompt_snippet": "Replace timeline with self-paced modules; checks become self-tests."},
            {"label": "Series of 5", "description": "Plan a 5-session arc.", "prompt_snippet": "Add: ‘then sketch sessions 2–5: each session's outcomes and how it builds on this one.’"},
        ],
        "failure_modes": [
            {"symptom": "Outcomes use ‘understand’ or ‘be familiar with’.", "fix": "Re-pin: ‘action verbs only — build, choose, debug, explain, draft.’"},
            {"symptom": "Timeline adds to more than 90 min.", "fix": "Add: ‘sum the minutes column; it must equal 90.’"},
            {"symptom": "Hands-on segment is contrived.", "fix": "Add: ‘the hands-on segment must produce an artifact learners can keep (code, doc, decision matrix) — no pretend activities.’"},
            {"symptom": "Checks are yes/no questions.", "fix": "Add: ‘each check probes a specific skill; expected answer includes a concrete example.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["socratic-tutor", "okr-quarterly-drafter"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["instructional-design", "learning-outcome"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How long should I spend reviewing the AI's plan?", "answer": "Plan on 30–45 minutes for first review: tighten one segment, adapt one check to your actual examples, sanity-check timing against your group."},
            {"question": "Can I run this remotely?", "answer": "Yes — but call it out in the learner profile so the model picks remote-friendly activities (chat threads, breakout pairs)."},
            {"question": "Will the rescue activity feel like filler?", "answer": "Only if you let it. Tune the prompt: ‘rescue activity must produce something learners reference in the closing.’"},
        ],
        "meta_title": "90-Minute Lesson Plan Generator — Prompt",
        "meta_description": "Generate 90-minute professional learning plans with timed segments, three checks, a rescue activity, and a closing — calibrated for adults.",
    },
    {
        "slug": "study-guide-from-chapter",
        "title": "Study Guide From Textbook Chapter",
        "tldr": "Turns a textbook chapter into a study guide: key concepts, definitions, worked examples, practice problems with answers, and a 5-question self-test that mirrors typical exam framing.",
        "category": "education",
        "tags": ["study-guide", "exam-prep", "summarization", "education"],
        "best_for_tags": ["self-study", "exam-prep", "tutoring"],
        "difficulty_tier": "beginner",
        "featured": True,
        "use_cases": [
            {"scenario": "Student prepping for exam", "example": "Paste chapter on photosynthesis — get back study guide with 5 self-test questions framed like the actual exam."},
            {"scenario": "Teacher building review materials", "example": "Compress chapter to one-page study guide for student handouts."},
            {"scenario": "Adult learner returning to school", "example": "Get back a study guide that re-explains concepts the textbook glossed over."},
            {"scenario": "Group study session", "example": "Generate quiz questions with answer keys for a study group."},
        ],
        "when_not_to_use": "Skip for primary-source texts (literature, history primary docs) — the model will reduce voice and nuance that matter. Use chapter summarization carefully.",
        "full_prompt": """You are a study guide builder. From the chapter content provided, produce a complete study guide.

STRUCTURE

## Chapter summary
3–5 sentences. What this chapter is fundamentally about.

## Key concepts (5–10)
Each: name, one-line definition in the student's voice (not the textbook's), and one concrete example.

## Worked examples (2–3)
Pick the most teaching examples from the chapter or invent one in the same shape. Walk through step-by-step, narrating the reasoning at each step.

## Practice problems (5–8)
Mix of difficulty. Include the answer below each, separated by a folded toggle (or `<details>` block). Mark each problem ‘easy/medium/hard’.

## Self-test (5 questions)
Five questions that mirror how an exam would frame the material — including at least one that's a small twist on what the chapter directly taught. Answers in a separate ‘answer key’ section.

## ‘If you only remember three things’
Three takeaways. These are what to memorize if exam is tomorrow.

CHAPTER CONTENT
{chapter_text}

GRADE LEVEL OR COURSE LEVEL
{level}

Write the study guide.""",
        "input_variables": [
            {"name": "chapter_text", "type": "string", "description": "The chapter text or detailed summary", "required": True, "example": "Photosynthesis is the process by which green plants..."},
            {"name": "level", "type": "string", "description": "Grade or course level", "required": True, "example": "High school biology, 11th grade"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six headed sections including practice problems with toggled answers and a self-test mirroring exam framing.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on the ‘in the student's voice’ definitions and at writing convincing exam-style questions."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes the practice problems are too easy — ask for ‘mixed difficulty including one twist’."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; can be overly literal to the textbook — ask for ‘re-explain in plain language’."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Answer keys occasionally wrong on the harder questions; have a teacher verify."},
        ],
        "variations": [
            {"label": "Flashcard-only", "description": "Output just front/back flashcards.", "prompt_snippet": "Replace all sections with: ‘flashcards in front | back format, 20–30 cards.’"},
            {"label": "Pictorial-heavy", "description": "More diagrams + analogies.", "prompt_snippet": "Add: ‘for each key concept, suggest one diagram and describe what it would show.’"},
            {"label": "Spaced-review", "description": "5/15/30-day review prompts.", "prompt_snippet": "Add: ‘end with a 5-day, 15-day, and 30-day review prompt (3–5 questions each) for spaced retrieval.’"},
        ],
        "failure_modes": [
            {"symptom": "Practice problems are all easy.", "fix": "Force ‘at least 2 medium and 1 hard, with at least one twist not in the chapter.’"},
            {"symptom": "Definitions read exactly like the textbook.", "fix": "Add ‘re-explain each in plain student-voice language; avoid the textbook's exact wording.’"},
            {"symptom": "Answer keys are wrong on harder questions.", "fix": "Have a teacher verify; add ‘mark any answer you're less than 90% sure of as needing verification.’"},
            {"symptom": "Self-test questions are recall-only.", "fix": "Add: ‘at least 2 of 5 questions require applying the concept to a new situation, not just recall.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["literature-review-synthesizer", "socratic-tutor"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["spaced-repetition", "retrieval-practice"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Will the answer keys be 100% correct?", "answer": "For STEM, near-100% on easy/medium; have a teacher verify hard problems. For humanities, the ‘answer’ is usually a range — discuss with peers."},
            {"question": "Can I use this for AP/IB?", "answer": "Yes, but specify the exam in the level field; question framing differs by exam tradition."},
            {"question": "Does this work for a whole textbook?", "answer": "Chapter-at-a-time. Pasting an entire textbook at once flattens the material — go chapter by chapter."},
        ],
        "meta_title": "Study Guide From Textbook Chapter — Prompt",
        "meta_description": "Turn any textbook chapter into a study guide: key concepts, worked examples, practice problems with answers, and a 5-question exam-style self-test.",
    },
    {
        "slug": "concept-map-builder",
        "title": "Concept Map Builder From Reading",
        "tldr": "Reads a chapter or article and outputs a concept map as a structured list: nodes, relations between them, and a hierarchy showing which ideas are central and which are supporting.",
        "category": "education",
        "tags": ["concept-map", "knowledge-graph", "education", "visual-thinking"],
        "best_for_tags": ["self-study", "knowledge-capture", "reviewing"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Student reviewing complex chapter", "example": "Get back a concept map showing photosynthesis at the center, light-dependent and light-independent reactions as primary children, and key molecules as supporting nodes."},
            {"scenario": "Researcher synthesizing a literature set", "example": "Five papers in — concept map shows shared concepts, contested concepts, and unique-to-one-paper concepts."},
            {"scenario": "Engineer learning a new system", "example": "Documentation overload — concept map distills the architecture into 12 nodes with relations."},
            {"scenario": "Author planning a book", "example": "Convert outline into concept map to spot ideas that don't connect."},
        ],
        "when_not_to_use": "Skip when the source is narrative (story, history) — concept maps flatten causal sequence into spatial relations and lose ‘what happened next’ structure.",
        "full_prompt": """You are a concept-map builder. Read the source text and emit a structured concept map.

OUTPUT FORMAT
Return JSON in this shape:
{
  "central_concept": "string",
  "nodes": [
    {"id": "n1", "label": "concept name", "tier": "central | primary | supporting | example", "definition": "one-line, in student voice"}
  ],
  "edges": [
    {"from": "n1", "to": "n2", "relation": "causes | enables | is-a | part-of | contrasts-with | depends-on | example-of"}
  ],
  "open_questions": [
    "questions the text doesn't fully answer (used as study prompts)"
  ]
}

CONSTRAINTS
- 8–18 nodes total. More is noisy.
- Every node has at least one edge.
- Relations come from the closed list above — don't invent new ones.
- Definitions are <20 words, in plain language.
- Central concept = the single idea the text is fundamentally about.

SOURCE TEXT
{text}

Emit the JSON now.""",
        "input_variables": [
            {"name": "text", "type": "string", "description": "Source text to map", "required": True, "example": "Photosynthesis is the process by which..."},
        ],
        "expected_output": {
            "format": "json",
            "schema": "{ central_concept, nodes[], edges[], open_questions[] }",
            "sample": "{\n  \"central_concept\": \"Photosynthesis\",\n  \"nodes\": [{...}],\n  \"edges\": [{...}],\n  \"open_questions\": [...]\n}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at picking the central concept correctly; relations are accurate."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally generates 25+ nodes — re-pin the 18 cap."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid structure; sometimes mixes tier classification."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "JSON sometimes malformed; validate before rendering."},
        ],
        "variations": [
            {"label": "Mermaid output", "description": "Emit as Mermaid diagram syntax.", "prompt_snippet": "Replace JSON shape with: ‘output as a Mermaid graph TD diagram.’"},
            {"label": "Compare two sources", "description": "Map across two texts.", "prompt_snippet": "Accept text_a and text_b; emit nodes tagged with origin (both/a-only/b-only) and edges showing where they agree/disagree."},
            {"label": "With study prompts", "description": "Auto-generate study questions per node.", "prompt_snippet": "Add: ‘for each primary-tier node, also emit one study question that requires combining it with another node.’"},
        ],
        "failure_modes": [
            {"symptom": "Too many nodes (>20).", "fix": "Tighten cap and add ‘collapse overlapping nodes into one with multiple labels.’"},
            {"symptom": "Relations invented outside the closed list.", "fix": "Re-paste the closed-list relations explicitly and reject other types."},
            {"symptom": "Central concept is a vague theme rather than a specific idea.", "fix": "Add: ‘central concept must be a noun phrase, not a theme.’"},
            {"symptom": "Edges are all ‘part-of’.", "fix": "Add: ‘at least 3 different relation types must appear; if not, reconsider the structure.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["study-guide-from-chapter", "literature-review-synthesizer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["concept-map", "knowledge-graph"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How do I visualize the JSON?", "answer": "Use the Mermaid variant for inline diagrams, or feed the JSON to any graph library (vis-network, cytoscape) for interactive views."},
            {"question": "Will the model agree with my teacher's mapping?", "answer": "Often, but not always. Use the AI map as a study scaffold; reconcile with the official one by noting differences — that's often where understanding gets deeper."},
            {"question": "Can I extend an existing map?", "answer": "Yes — paste your current map and ask the model to add nodes from a new source while marking which are new vs existing."},
        ],
        "meta_title": "Concept Map Builder From Reading — Prompt",
        "meta_description": "Read a chapter or article and emit a structured concept map: nodes, typed relations, and open questions — ready to visualize or study from.",
    },
    {
        "slug": "exam-question-writer",
        "title": "Exam Question Writer With Rubric",
        "tldr": "Generates exam questions at a specified Bloom's level (recall/apply/analyze/evaluate/create) with answer keys, rubrics, and distractor analysis for multiple choice — calibrated for fair, non-trick questions.",
        "category": "education",
        "tags": ["assessment", "exam", "rubric", "blooms", "education"],
        "best_for_tags": ["teachers", "trainers", "certification-prep"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Teacher building chapter test", "example": "‘Photosynthesis, 10 questions, mostly apply-level, 3 multiple choice + 4 short answer + 3 explanation’ — get back questions with rubrics."},
            {"scenario": "Corporate certification builder", "example": "Compliance training questions with answer key and reasoning for each distractor."},
            {"scenario": "Bootcamp instructor", "example": "Weekly assessment for cohort — apply-level coding questions with point-by-point rubric."},
            {"scenario": "Adaptive learning platform", "example": "Generate question bank tagged by Bloom's level for spaced practice."},
        ],
        "when_not_to_use": "Skip when high-stakes (board exams, formal certification) without expert review — even strong AI question writing needs subject-matter verification.",
        "full_prompt": """You are an exam question writer. Generate questions per the spec.

INPUT
- Topic: {topic}
- Number of questions: {n_questions}
- Mix by Bloom's level: {bloom_mix}              (e.g., "3 recall, 4 apply, 3 analyze")
- Question types: {types}                        (e.g., "multiple choice, short answer, explanation")
- Target audience: {audience}                    (e.g., "11th grade biology")
- Time budget: {time_per_question} per question

PER QUESTION, OUTPUT
1. Question number, type, Bloom's level.
2. Question text. (Single, unambiguous.)
3. For multiple choice:
   - Four options, labeled A–D.
   - Mark the correct answer.
   - For each WRONG option: one sentence on what a student who picks it is confused about (distractor analysis). Avoid silly distractors — every wrong option should be plausibly tempting.
4. For short answer / explanation:
   - Rubric with 2–4 levels (e.g., excellent / partial / minimal / off-track) — what each level includes.
   - Sample answer at ‘excellent’ level.

CONSTRAINTS
- No trick questions. The goal is to measure understanding, not catch students.
- No ‘all of the above’ or ‘none of the above’ unless the topic genuinely warrants it.
- Vocabulary matched to audience.

Write the questions now.""",
        "input_variables": [
            {"name": "topic", "type": "string", "description": "Subject of the questions", "required": True, "example": "Photosynthesis"},
            {"name": "n_questions", "type": "integer", "description": "Total number of questions", "required": True, "example": "10"},
            {"name": "bloom_mix", "type": "string", "description": "Distribution across Bloom's levels", "required": True, "example": "3 recall, 4 apply, 3 analyze"},
            {"name": "types", "type": "string", "description": "Question types", "required": True, "example": "multiple choice, short answer, explanation"},
            {"name": "audience", "type": "string", "description": "Who is being tested", "required": True, "example": "11th grade biology"},
            {"name": "time_per_question", "type": "string", "description": "Time budget per question", "required": False, "example": "3 minutes"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Numbered questions with type/level header, question, options or rubric, answer/sample answer, and distractor analysis or rubric levels.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong distractor analysis; rubric levels are useful."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally slips into trick questions — re-pin the constraint."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Question quality good; rubrics sometimes generic — ask for ‘what makes each level distinct.’"},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Bloom's classification often wrong; verify each question's level."},
        ],
        "variations": [
            {"label": "Coding test variant", "description": "Code-by-hand or fix-the-bug questions.", "prompt_snippet": "Replace types with: ‘code-by-hand, fix-the-bug, predict-output, refactor.’ Add: ‘include starter code where relevant.’"},
            {"label": "Case-study assessment", "description": "Multi-part scenario.", "prompt_snippet": "Replace with: ‘one extended case study followed by 5 questions of increasing Bloom's level on it.’"},
            {"label": "Equity-audited", "description": "Cultural neutrality check.", "prompt_snippet": "Add: ‘flag any question whose framing requires culturally specific knowledge unrelated to the topic and revise.’"},
        ],
        "failure_modes": [
            {"symptom": "Distractors are silly (one obvious wrong answer).", "fix": "Add: ‘each wrong option must reflect a real, common student misconception.’"},
            {"symptom": "Apply/analyze questions are actually recall.", "fix": "Re-pin Bloom's definitions and require ‘apply’ questions to use a new context not covered in the source."},
            {"symptom": "Rubrics are vague (‘shows good understanding’).", "fix": "Add: ‘each rubric level names a specific element that must be present at that level.’"},
            {"symptom": "Bias in cultural references.", "fix": "Use the equity-audited variation or add explicit ‘flag and revise culturally specific framing.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["study-guide-from-chapter", "lesson-plan-90-min"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["blooms-taxonomy", "rubric"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Will AI-written questions be valid?", "answer": "For formative assessment, generally yes. For summative/high-stakes, require expert review of each question and rubric."},
            {"question": "How do I avoid the model being biased toward certain answers?", "answer": "Run the rubric back through and ask the model to grade three sample student answers blindly — biased rubrics surface as inconsistent grading."},
            {"question": "Can I cycle the same questions across years?", "answer": "Don't — students share answer keys. Regenerate annually with the same topic + Bloom's mix; the model will produce structurally similar but different surface questions."},
        ],
        "meta_title": "Exam Question Writer With Rubric — Prompt",
        "meta_description": "Generate exam questions by Bloom's level with rubrics, sample answers, and distractor analysis for multiple choice. Calibrated for fair, non-trick assessment.",
    },
]
