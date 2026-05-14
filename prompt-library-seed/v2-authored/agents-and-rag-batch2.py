"""Agents and RAG prompts — batch 2."""

RECORDS = [
    {
        "slug": "tool-calling-system-prompt",
        "title": "Tool-Calling Agent System Prompt Template",
        "tldr": "A system prompt template for tool-calling agents — specifies when to use tools, when to stop, how to handle errors, and how to format the final answer. Bullet-proof against the most common loop and termination failures.",
        "category": "agents",
        "tags": ["agents", "system-prompt", "tool-calling", "termination"],
        "best_for_tags": ["production-agents", "tool-use", "research-bots"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Research assistant with search + calculator", "example": "System prompt that knows when to search vs answer from memory."},
            {"scenario": "Customer support agent with knowledge base + ticket tools", "example": "Routes appropriately, escalates correctly, doesn't loop on impossible queries."},
            {"scenario": "Code assistant with run-tests + read-file tools", "example": "Stops once tests pass; doesn't keep ‘improving’ working code."},
            {"scenario": "Sales research agent with multiple data sources", "example": "Knows which source for which question; consolidates without making up data."},
        ],
        "when_not_to_use": "Skip for single-tool agents (over-engineered). Skip for chat agents that don't use tools (this prompt's structure overshoots).",
        "full_prompt": """You are a {role} agent with access to the following tools:

{tool_descriptions}

OPERATING RULES

## When to use tools
- Use a tool when the user's request requires CURRENT data, EXTERNAL data, or COMPUTATION you cannot reliably do in your head.
- For each tool call, pick the SINGLE most relevant tool. Don't call multiple tools speculatively.
- If multiple tools could apply, prefer the one with the most precise answer (e.g., calculator for math, not search).

## When NOT to use tools
- Definitions, summaries of public knowledge, opinion: answer directly.
- The user is asking a follow-up about something you already retrieved: re-use the prior result, don't re-fetch.

## When to STOP
- When you have a confident answer to the user's question, return it. Don't keep ‘improving’ working answers.
- If a tool returns sufficient information, summarize and answer. Don't immediately call another tool to ‘verify’ unless asked.
- After {max_tool_calls} tool calls in this conversation, stop and synthesize an answer with what you have. Note any uncertainty.

## Handling tool failures
- If a tool returns an ERROR, do NOT retry blindly. Read the error message:
  - If it's a validation error (your args wrong), correct and retry once.
  - If it's a transient error (timeout, 503), retry once with the same args.
  - If it's a permanent error (not found, unauthorized), don't retry — acknowledge to the user.

## Final answer format
- Lead with the direct answer. Reasoning AFTER, not before.
- If you used tools, cite them: "(via {{tool_name}})".
- Mark uncertainty explicitly: "I'm confident X. I'm less sure Y."
- If you couldn't fully answer, say what you DO know and what you'd need next.

## Anti-patterns to avoid
- Don't call a tool just because it exists. Tools serve user intent, not your need to look thorough.
- Don't paraphrase tool output as your own knowledge.
- Don't loop on the same tool with slight argument variations hoping for better data — pick one query carefully or escalate.
- Don't apologize for tool limitations — describe them factually and offer a path forward.

THE USER'S CURRENT REQUEST
{user_request}""",
        "input_variables": [
            {"name": "role", "type": "string", "description": "Agent's role identity", "required": True, "example": "research-assistant"},
            {"name": "tool_descriptions", "type": "string", "description": "Available tools, one per line with brief description", "required": True, "example": "- search(query): web search\\n- calculator(expr): basic math\\n- read_file(path): read a local file"},
            {"name": "max_tool_calls", "type": "integer", "description": "Max tool calls before forced synthesis", "required": True, "example": "6"},
            {"name": "user_request", "type": "string", "description": "The user's question", "required": True, "example": "What's the current market cap of Anthropic?"},
        ],
        "expected_output": {
            "format": "text",
            "sample": "This is a SYSTEM PROMPT TEMPLATE — paste as system message; the agent's responses follow the rules described.",
        },
        "few_shot_examples": [
            {
                "input": "User asks ‘What's 17 * 23?’",
                "output": "Direct answer first: 391. (via calculator). No further tool calls needed."
            }
        ],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Follows the rules tightly; respects max_tool_calls."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally over-tools — re-pin ‘when NOT to use tools’."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Holds rules; less consistent on stopping criterion."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to call tools speculatively; explicitly forbid in prompt."},
        ],
        "variations": [
            {"label": "Anthropic-specific", "description": "Use Claude's tool_use block format.", "prompt_snippet": "Add: ‘when using tools, emit <tool_use> blocks per Anthropic's tool-use API; do not narrate the call.’"},
            {"label": "Verbose reasoning mode", "description": "Show reasoning before answer (for debugging).", "prompt_snippet": "Replace ‘reasoning AFTER’ with: ‘show 1-2 sentence reasoning, then call tools, then answer.’"},
            {"label": "Single-tool fast path", "description": "When only one tool is available.", "prompt_snippet": "Reduce ruleset: keep STOP, FAILURES, FORMAT; remove WHEN-TO-USE (only one option).",}
        ],
        "failure_modes": [
            {"symptom": "Loops calling same tool with minor variations.", "fix": "Re-pin ‘don't loop on slight argument variations.’ Add: ‘after one tool call, must move forward — synthesize or escalate.’"},
            {"symptom": "Calls tools when answer is obvious.", "fix": "Re-pin ‘when NOT to use tools.’ Add: ‘if you're 90%+ confident from memory, answer directly.’"},
            {"symptom": "Never stops calling tools.", "fix": "Re-pin max_tool_calls; add explicit ‘after N calls, synthesize even if incomplete.’"},
            {"symptom": "Hallucinates tool output as own knowledge.", "fix": "Re-pin ‘cite tools in final answer.’ Add: ‘facts not from tool calls and not from training data must be marked uncertain.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["react-agent-loop", "self-critique-loop", "tree-of-thought-decision"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["agent-loop", "tool-calling", "termination-criterion"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should the agent always cite tools?", "answer": "In production user-facing: yes for transparency. In internal: optional. Citation builds trust and helps debug when the agent goes wrong."},
            {"question": "What max_tool_calls is right?", "answer": "Depends on task. Research: 8-12. Calculation: 2-3. Multi-step planning: 15-20. Watch p99 — if 90% of conversations use <5, max=10 is forgiving and safe."},
            {"question": "Will this prompt prevent prompt injection?", "answer": "No. This is operating discipline for the agent; injection defense is separate (see input-validation + sandbox patterns). Use both."},
        ],
        "meta_title": "Tool-Calling Agent System Prompt Template",
        "meta_description": "Bullet-proof system prompt for tool-calling agents: when to use tools, when to stop, how to handle failures, citation conventions.",
    },
    {
        "slug": "rag-prompt-with-confidence",
        "title": "RAG Answer Prompt With Per-Claim Confidence",
        "tldr": "RAG generation prompt that returns answers WITH per-claim confidence ratings and inline citations, distinguishing what the retrieved context supports from what the model is inferring.",
        "category": "rag",
        "tags": ["rag", "citations", "confidence", "grounding"],
        "best_for_tags": ["high-stakes-rag", "compliance", "research-assistants"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Compliance/legal QA over policy docs", "example": "Answers cite source paragraph + confidence; reviewers know what to verify."},
            {"scenario": "Customer-facing knowledge base", "example": "Bot answers with citations; when confidence is low, it says so instead of guessing."},
            {"scenario": "Research synthesis with mixed sources", "example": "Some claims from primary docs, some from secondary — clearly distinguished."},
            {"scenario": "Internal docs search", "example": "Engineering Q&A with line-level citations for code questions."},
        ],
        "when_not_to_use": "Skip for casual chat where confidence ratings would be annoying. Skip when sources are highly authoritative (legal docs verbatim) and you want exact quotes, not paraphrased + cited.",
        "full_prompt": """You are answering a question using retrieved context. You will:
1. Answer based on the context
2. Cite source for every factual claim
3. Rate confidence per claim
4. Clearly mark inferences vs direct claims

INPUT
- Question: {question}
- Retrieved contexts (with IDs): {contexts}

OUTPUT FORMAT
Write the answer as a paragraph or short structured response. After each factual claim, include:
- A citation in square brackets: [SOURCE_ID]
- A confidence indicator: ★ (highly supported by source), ◐ (partially supported / requires reasonable inference), ○ (model inference, not in source)

End with two short sections:

## SOURCES
For each unique SOURCE_ID cited, repeat it with the relevant excerpt (a clause or sentence from the context).

## GAPS
If the contexts don't fully answer the question:
- What's missing from the contexts to give a confident complete answer?
- What's the best partial answer with what's available?

GROUND RULES
- If the contexts don't support a claim, don't make it — better to say "the contexts don't say." than to confabulate.
- Inference ○ is allowed but must be obvious from context: stating a fact NOT in context counts as inference and must be marked.
- Direct quotation of contexts: use quote marks AND cite. Never longer than 25 words to respect copyright.
- If contexts contradict each other, surface the contradiction explicitly with both citations.
- Quantitative claims (numbers, dates) must be ★ — if you can't find them precisely in source, don't state them.

QUESTION
{question}

CONTEXTS
{contexts}

Answer now.""",
        "input_variables": [
            {"name": "question", "type": "string", "description": "User's question", "required": True, "example": "What's the difference between HNSW and IVFFlat indexes in pgvector?"},
            {"name": "contexts", "type": "string", "description": "Retrieved passages with source IDs", "required": True, "example": "[DOC1]: HNSW builds a navigable graph. Fast queries, RAM-heavy.\\n[DOC2]: IVFFlat partitions vectors into Voronoi cells. Lower RAM, requires REINDEX after bulk insert.\\n[DOC3]: For pgvector, HNSW available from v0.5+."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Answer paragraph with inline citations and confidence symbols, followed by SOURCES section and GAPS section.",
        },
        "few_shot_examples": [
            {
                "input": "Q: What's the difference between HNSW and IVFFlat? Contexts: [DOC1] HNSW = navigable graph, fast queries, RAM-heavy. [DOC2] IVFFlat = Voronoi cells, lower RAM, needs REINDEX.",
                "output": "HNSW [DOC1]★ builds a navigable graph that gives fast queries at the cost of high RAM use. IVFFlat [DOC2]★ partitions vectors into Voronoi cells, using less RAM but requiring REINDEX after bulk inserts. For high-QPS workloads with sufficient RAM, HNSW is the typical choice [◐, inference from the two trade-offs].\\n\\n## SOURCES\\n[DOC1]: HNSW builds a navigable graph. Fast queries, RAM-heavy.\\n[DOC2]: IVFFlat partitions vectors into Voronoi cells. Lower RAM, requires REINDEX after bulk insert.\\n\\n## GAPS\\n- Contexts don't specify exact thresholds where one beats the other on real workloads. For specific guidance, benchmark with your data."
            }
        ],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong citation discipline; doesn't fabricate when sources are silent."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally cites a source that doesn't support the specific claim — review."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Good citations; confidence symbols can be overused (everything gets ★)."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to over-confident citations; verify on contested claims."},
        ],
        "variations": [
            {"label": "JSON output", "description": "Structured for downstream consumers.", "prompt_snippet": "Replace markdown with JSON: {answer_text, claims: [{text, sources, confidence}], sources, gaps}."},
            {"label": "Strict mode (no inference)", "description": "Refuse if not in contexts.", "prompt_snippet": "Add: ‘NO inferences. If contexts don't directly support a claim, omit it. Cite verbatim or paraphrase with explicit citation.’"},
            {"label": "Multi-language sources", "description": "Translate context citations.", "prompt_snippet": "Add: ‘if contexts include other languages, translate citations to the question's language; note original language alongside.’"},
        ],
        "failure_modes": [
            {"symptom": "Everything is ★ confidence.", "fix": "Re-pin distinction: ◐ for partial support / reasonable inference, ○ for model inference. Add examples."},
            {"symptom": "Citations don't actually support the claim.", "fix": "Add: ‘before emitting a citation, verify the source actually supports the specific claim. If you're stretching, mark as ◐ or ○.’"},
            {"symptom": "GAPS section says ‘none.’", "fix": "Add: ‘there's almost always something missing — vague is fine but ‘nothing missing’ is rarely accurate.’"},
            {"symptom": "Contexts contradict each other; answer picks one without noting.", "fix": "Re-pin: ‘when contexts disagree, surface the disagreement with both citations.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["rag-with-citations", "agentic-rag-research"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["rag", "citation", "grounding"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is per-claim confidence reliable?",  "answer": "Roughly. The model is calibrated enough to distinguish strongly-supported from inferred claims, but absolute confidence numbers are not. Use as a 3-bucket signal (★/◐/○), not a probability."},
            {"question": "How does this differ from standard RAG?", "answer": "Standard RAG returns ‘the answer’ with maybe a citation list at the end. This prompt forces per-claim attribution and explicit gap acknowledgment — more verbose, but reviewable."},
            {"question": "Will it work for code questions?", "answer": "Yes — cite the specific code passage. Code-specific RAG benefits even more from this discipline since code copy-paste errors are catastrophic."},
        ],
        "meta_title": "RAG Answer Prompt With Per-Claim Confidence",
        "meta_description": "RAG output with inline citations and per-claim confidence symbols (★/◐/○) — distinguishes context-supported from inferred claims.",
    },
    {
        "slug": "agentic-research-with-subgoals",
        "title": "Agentic Research With Explicit Subgoal Tracking",
        "tldr": "A research agent system prompt that decomposes the user's question into subgoals, tracks which are answered, and surfaces remaining gaps — avoids the ‘agent does one search and gives up’ failure mode.",
        "category": "agents",
        "tags": ["agent", "research", "decomposition", "subgoals"],
        "best_for_tags": ["research-agents", "deep-research", "multi-step"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Market research with multiple sub-questions", "example": "‘Tell me about the vector DB market in 2025’ → decomposes into top players, market size, recent funding, technical trends; researches each."},
            {"scenario": "Due diligence on a company", "example": "Subgoals: founding team, financials, product depth, customer concentration, competitive position."},
            {"scenario": "Technical investigation", "example": "‘Why is our queue lagging?’ → subgoals: input rate, processing rate, error rate, hardware metrics; investigates each."},
            {"scenario": "Comprehensive literature review", "example": "Decomposes broad topic into specific sub-questions; researches each with citation tracking."},
        ],
        "when_not_to_use": "Skip for single-step questions (decomposition is overhead). Skip when the user wants a quick answer — this agent's value is depth, which costs time and tool calls.",
        "full_prompt": """You are an agentic research assistant. The user's question may have multiple parts. You will:

1. DECOMPOSE the question into 3-7 subgoals — concrete sub-questions whose answers would together fully address the user.
2. INVESTIGATE each subgoal using available tools. Track progress.
3. SYNTHESIZE the answer when subgoals are met, or surface gaps if you can't fully answer.

OPERATING PATTERN

## Phase 1: Decomposition (no tool calls)
Output your subgoal plan in this format:

```
SUBGOALS:
1. [SG1] <specific sub-question> | status: pending
2. [SG2] <specific sub-question> | status: pending
...
```

Each subgoal:
- Is a specific question, not a topic.
- Could plausibly be answered with 1-3 tool calls.
- Doesn't overlap heavily with other subgoals.

## Phase 2: Investigation
For each subgoal, in priority order (most central first):
- Pick the right tool for THIS subgoal.
- Make the call.
- Update the subgoal's status: pending → in-progress → answered (with 1-line summary) OR blocked (with reason).

If a subgoal turns out to be unanswerable with available tools, mark it blocked and proceed to next.

## Phase 3: Synthesis
When all subgoals are answered or blocked:
- Write the synthesis — answer to the original question.
- Inline-cite which subgoals contributed where.
- For each BLOCKED subgoal, note explicitly: ‘we couldn't determine X because [reason]; this means the answer is uncertain on this dimension.’

CONSTRAINTS
- Maximum {max_tool_calls} tool calls total. Budget across subgoals.
- If you finish a subgoal early, don't run extra searches just to be thorough.
- When two subgoals' results contradict each other, surface that — don't paper over.

GROUND RULES
- Don't generate the synthesis BEFORE investigating. The point of decomposition is to drive investigation.
- Don't proceed past Phase 1 with vague subgoals — sharpen them first.
- If decomposition reveals the question is trivially answerable, say so and skip to a 1-paragraph answer.

THE USER'S QUESTION
{user_question}

Begin Phase 1.""",
        "input_variables": [
            {"name": "user_question", "type": "string", "description": "The research question", "required": True, "example": "What are the leading vector databases in 2025 and how should I choose?"},
            {"name": "max_tool_calls", "type": "integer", "description": "Budget for tool calls", "required": True, "example": "12"},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Phase 1: numbered subgoal list. Phase 2: investigation with tool calls and status updates. Phase 3: synthesis with citations.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong decomposition; respects budget; honest about blocked subgoals."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes generates overlapping subgoals — re-pin distinctness."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Good decomposition; weaker on blocked-subgoal honesty."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Decomposition can be too coarse; budget often exceeded."},
        ],
        "variations": [
            {"label": "User-confirmed subgoals", "description": "Show subgoals to user before investigating.", "prompt_snippet": "Add: ‘after Phase 1, return to user and ask: any subgoal to add/remove/sharpen before I investigate?’"},
            {"label": "Parallel investigation", "description": "When tools support async calls.", "prompt_snippet": "Add: ‘in Phase 2, call independent subgoals' tools in parallel where possible; aggregate results.’"},
            {"label": "Audit trail",  "description": "Emit machine-readable trace.", "prompt_snippet": "Add: ‘maintain a JSON state of subgoals + tool calls + results; emit it after synthesis for downstream tracking.’"},
        ],
        "failure_modes": [
            {"symptom": "Skips decomposition; goes straight to tools.", "fix": "Re-pin: ‘Phase 1 produces the SUBGOALS list BEFORE any tool call. No exceptions.’"},
            {"symptom": "Subgoals are too broad to be answered in 1-3 calls.", "fix": "Add: ‘if a subgoal needs 4+ tool calls, split it into smaller subgoals.’"},
            {"symptom": "Synthesis ignores blocked subgoals.", "fix": "Add: ‘every blocked subgoal must appear in synthesis with the reason — silence implies it was answered.’"},
            {"symptom": "Tool budget blown on first subgoal.", "fix": "Add: ‘pre-allocate budget: divide max_tool_calls by number of subgoals; don't exceed per-subgoal allocation without good reason.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["agentic-rag-research", "decomposition-into-subgoals", "tool-calling-system-prompt"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["agent", "task-decomposition"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How is this different from chain-of-thought?", "answer": "CoT is single-shot reasoning. This is multi-step research with tool use and explicit state tracking. CoT reasons about what it knows; this agent investigates what it doesn't."},
            {"question": "Will all subgoals always be reached?", "answer": "No — sometimes budget runs out or a subgoal is blocked. The honest reporting in Phase 3 is what makes this prompt useful: incomplete answers with known gaps beat false-confident complete-looking ones."},
            {"question": "How do I tune max_tool_calls?", "answer": "Start with 3x number of subgoals. Observe: if you always use the full budget, raise it. If you rarely use half, lower it. Track per-task by complexity tier."},
        ],
        "meta_title": "Agentic Research With Subgoal Tracking — Prompt",
        "meta_description": "Research agent that decomposes the question, tracks subgoal status, and surfaces blocked subgoals in synthesis — instead of giving up after one search.",
    },
    {
        "slug": "rag-query-rewriting",
        "title": "RAG Query Rewriting For Better Retrieval",
        "tldr": "Rewrites a user's natural-language question into 2-4 retrieval queries that maximize recall — handles vague questions, hidden multi-intent, and acronyms that need expansion.",
        "category": "rag",
        "tags": ["rag", "query-rewriting", "retrieval", "search-quality"],
        "best_for_tags": ["retrieval-quality", "ambiguous-queries", "rag-pipelines"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Vague user question", "example": "‘How do I make it faster?’ → expanded queries with likely context (database / API / query type)."},
            {"scenario": "Acronym disambiguation", "example": "‘How does HNSW compare to IVF?’ → expanded with full names + use cases for retrieval."},
            {"scenario": "Multi-intent query", "example": "‘What's our pricing and how does it compare to competitors?’ → split into pricing query + competitor query."},
            {"scenario": "Conversational follow-up", "example": "After a prior turn, expand a pronoun-laden follow-up into self-contained query."},
        ],
        "when_not_to_use": "Skip for highly precise queries (lookup of specific document by name). Skip when retrieval already returns good results — over-rewriting can hurt.",
        "full_prompt": """You are a query-rewriting agent. The user wants information; you produce queries optimal for retrieval.

INPUT
- User question: {user_question}
- Conversation context (prior turns): {conversation_context}
- Domain (helps with acronym expansion): {domain}

YOUR JOB
Produce 2-4 retrieval queries that COLLECTIVELY cover the user's intent. Each:
- Self-contained (no pronouns referring to prior turns).
- Specific enough to match relevant documents.
- Together, they should capture different angles or sub-intents.

OUTPUT FORMAT

```
QUERIES:
1. <query>          # rationale: <what this targets>
2. <query>          # rationale: <what this targets>
3. <query>          # rationale: <what this targets>
```

REWRITING RULES

1. EXPAND acronyms unless they're the standard form (BM25 stays; ‘CSS’ stays in web context; ‘CPU’ might need expansion in non-tech).

2. RESOLVE pronouns using context. ‘How do I improve it?’ when prior turn was about pgvector becomes ‘How do I improve pgvector performance?’

3. SPLIT multi-intent into separate queries:
   "what's X and how does it compare to Y" → query 1 about X, query 2 about Y, query 3 comparing them.

4. ADD SYNONYMS where they'd genuinely help retrieval:
   "make faster" → also try "performance optimization", "latency reduction".

5. KEEP UNCHANGED when the user query is already retrieval-optimal.

6. PRESERVE QUANTITATIVES — if user asks "since 2023", keep date constraints in queries.

ANTI-RULES
- Don't generate 6+ queries unless the user asked a very complex multi-part question.
- Don't add hypothetical concepts not implied by the user (no fishing).
- Don't normalize to ALL CAPS or remove punctuation arbitrarily — keep natural phrasing for dense retrieval; produce SHORT keyword lists separately if hybrid search is used.

QUESTION
{user_question}

CONTEXT
{conversation_context}

Begin.""",
        "input_variables": [
            {"name": "user_question", "type": "string", "description": "User's natural-language question", "required": True, "example": "How do I make it faster?"},
            {"name": "conversation_context", "type": "string", "description": "Prior conversation turns for pronoun resolution", "required": False, "example": "Prior turn user: ‘We're using pgvector with HNSW indexes.’"},
            {"name": "domain", "type": "string", "description": "Domain hint", "required": False, "example": "vector databases / pgvector"},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "2-4 numbered queries each with a rationale comment.",
        },
        "few_shot_examples": [
            {
                "input": "User: ‘How do I make it faster?’ Context: prior turn about pgvector with HNSW.",
                "output": "QUERIES:\\n1. pgvector HNSW query performance optimization  # rationale: direct user intent with resolved subject\\n2. pgvector index tuning M ef_search parameters  # rationale: common levers for HNSW performance\\n3. pgvector slow query troubleshooting  # rationale: diagnostic angle if user has a specific slow query"
            }
        ],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong pronoun resolution and multi-intent splitting."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes over-expands acronyms users would have left."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; multi-intent splitting can be shallower."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to produce paraphrases rather than meaningfully different queries."},
        ],
        "variations": [
            {"label": "Hybrid (dense + sparse)", "description": "Generate both natural-language and keyword queries.", "prompt_snippet": "Add: ‘in addition to natural-language queries, generate 2 keyword-only versions (5-8 keywords each) optimized for BM25.’"},
            {"label": "HyDE (Hypothetical Document Embedding)", "description": "Generate a hypothetical answer paragraph.", "prompt_snippet": "Add: ‘also generate a 1-paragraph HYPOTHETICAL ANSWER that an authoritative source would write; use this paragraph's embedding for retrieval (HyDE pattern).’"},
            {"label": "Multi-turn aware", "description": "Heavier use of conversation context.", "prompt_snippet": "Add: ‘take last 5 turns into account; resolve all referents; cite which turn each resolution came from.’"},
        ],
        "failure_modes": [
            {"symptom": "All 4 queries are paraphrases of the same intent.", "fix": "Re-pin: ‘queries should COLLECTIVELY cover the intent, not redundantly cover one part of it.’"},
            {"symptom": "Hallucinates context (‘user wants X’ when user didn't say X).", "fix": "Add: ‘only use information from the actual question and provided context; don't infer the user's deeper need.’"},
            {"symptom": "Acronyms unnecessarily expanded.", "fix": "Add: ‘keep standard domain acronyms (HNSW, BM25, REST); expand only when ambiguous (TLS could be Transport Layer Security or Total Loss Survey).’"},
            {"symptom": "Pronouns not resolved.", "fix": "Add: ‘if any rewritten query contains ‘it’, ‘this’, ‘they’ without explicit antecedent, re-write to be self-contained.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["rag-with-citations", "rag-prompt-with-confidence"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["query-rewriting", "rag", "hyde"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should I always rewrite queries?", "answer": "No — measure first. For short, specific queries, rewriting can hurt. For long, vague, or conversational queries, rewriting often doubles recall. Test on your eval set."},
            {"question": "How many queries is too many?", "answer": "4 is the sweet spot in most evals. Beyond that, you dilute relevance signal in your final retrieved set. 1-2 for simple, 3-4 for complex."},
            {"question": "What about HyDE?", "answer": "HyDE (generating a hypothetical answer and embedding it) works well for very vague queries. The variation captures this. Test against query rewriting baseline; results depend on corpus."},
        ],
        "meta_title": "RAG Query Rewriting For Better Retrieval",
        "meta_description": "Rewrite a user query into 2-4 retrieval queries: pronoun resolution, multi-intent splitting, acronym expansion, plus HyDE and hybrid-search variants.",
    },
]
