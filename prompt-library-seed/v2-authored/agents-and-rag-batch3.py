"""Agents and RAG prompts — batch 3."""

RECORDS = [
    {
        "slug": "agent-with-self-reflection-step",
        "title": "Agent With Built-In Self-Reflection",
        "tldr": "Agent system prompt that adds an explicit ‘pause and check yourself’ step after each major action. Catches reasoning errors before they compound across multiple agent turns.",
        "category": "agents",
        "tags": ["agent", "self-reflection", "metacognition", "agent-quality"],
        "best_for_tags": ["complex-agents", "multi-step", "high-stakes-agents"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Research agent making multiple tool calls", "example": "After each tool result, agent pauses: ‘did I get what I needed? what's still missing?’ Prevents tunnel vision."},
            {"scenario": "Coding agent before committing", "example": "Before final answer, agent reviews: ‘does this fully address the user's request? Any edge cases I missed?’"},
            {"scenario": "Customer-facing agent", "example": "Before sending reply, agent checks: ‘is this helpful, accurate, on-policy?’"},
            {"scenario": "Decision-support agent", "example": "Before recommending, agent enumerates: ‘what did I assume? Where am I uncertain?’"},
        ],
        "when_not_to_use": "Skip for simple agents where reflection is overhead. Skip for latency-critical paths — reflection doubles or triples token use.",
        "full_prompt": """You are an agent with explicit self-reflection. After each significant step, you pause and check yourself.

INPUT
- Your role: {role}
- Available tools: {tools}
- The user's request: {user_request}

OPERATING PATTERN

For each major step:
1. ACT (call a tool, write a piece of output, make a decision).
2. CHECK YOURSELF — produce a brief reflection in this format:

```
REFLECTION:
- Did this step actually advance toward the user's goal? (yes / no / partially — explain)
- Did I assume anything that could be wrong? (list assumptions)
- What am I uncertain about?
- What's the most likely failure mode of my last step?
- Should I revise course or continue?
```

3. ACT AGAIN based on the reflection.

REFLECTION DEPTH GUIDE
- After tool calls: 1-2 sentence reflection
- After completing a major sub-goal: 3-5 sentence reflection
- Before final answer to user: full 5-bullet reflection

WHEN TO BREAK THE PATTERN
- Very short, obvious tasks: one reflection at the end is enough.
- Reflection is producing nothing new (3 reflections in a row say the same thing): you're stuck — escalate or ask user.
- Pattern feels like theater: skip it; reflection should generate insight, not be a checkbox.

THE WIN CONDITION
The user's request is fulfilled with high confidence. Your last reflection should confirm:
- The answer addresses what was actually asked (not what's easy to answer)
- You've handled the obvious edge cases
- Remaining uncertainty is explicitly flagged

USER REQUEST
{user_request}

Begin.""",
        "input_variables": [
            {"name": "role", "type": "string", "description": "Agent role", "required": True, "example": "Research assistant"},
            {"name": "tools", "type": "string", "description": "Available tools", "required": True, "example": "- search(query): web search\\n- read_url(url): fetch and parse a URL\\n- calculator(expr): math"},
            {"name": "user_request", "type": "string", "description": "User's request", "required": True, "example": "Estimate the addressable market for AI-powered legal research tools in the US."},
        ],
        "expected_output": {
            "format": "text",
            "sample": "Interleaved ACT and REFLECTION blocks; final answer with full reflection.",
        },
        "few_shot_examples": [
            {
                "input": "Role: research assistant. User: ‘What's the population of Lisbon?’",
                "output": "ACT: Call search('population of Lisbon')\\n\\nREFLECTION:\\n- Step advanced goal: yes, found current population estimate.\\n- Assumptions: none significant.\\n- Uncertainty: source date — population estimates vary year-to-year.\\n- Failure mode: out-of-date number.\\n- Continue: yes, return answer with year of source.\\n\\nFinal: Lisbon proper has approximately 545,000 (2023 estimate); metro area ~2.9M."
            }
        ],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Reflections are substantive, not checkbox."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes reflection becomes repetitive — call out the ‘theater’ trigger."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Holds pattern; reflections shallow without prompting depth."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Frequently skips reflection; needs constant re-pinning."},
        ],
        "variations": [
            {"label": "Two-model reflection", "description": "Different model critiques.", "prompt_snippet": "Add: ‘reflections are produced by a SECOND LLM call — different model — to avoid blind spots.’"},
            {"label": "Reflection-only at end", "description": "Single reflection before final answer.", "prompt_snippet": "Simpler: ‘act without per-step reflection, but BEFORE final answer, produce full reflection and revise if needed.’"},
            {"label": "Visible vs hidden reflections", "description": "Show user only act outputs.", "prompt_snippet": "Add: ‘reflections are internal — produce them but don't show to user; influence next action only.’"},
        ],
        "failure_modes": [
            {"symptom": "Reflections are theater (‘yes I did the thing’).", "fix": "Re-pin: ‘reflection must surface ONE non-obvious thing per cycle, or it's not earning its keep.’"},
            {"symptom": "Pattern doubles latency without value.", "fix": "Use the ‘reflection-only at end’ variant for simple tasks. Or detect when reflections are repetitive and skip."},
            {"symptom": "Reflections leak into user-visible output as noise.", "fix": "Use the ‘visible vs hidden’ variation; suppress reflection blocks from user view."},
            {"symptom": "Agent uses reflection as procrastination (never commits).", "fix": "Add: ‘after 3 reflection cycles without progress, COMMIT to the best current answer and surface uncertainty rather than reflecting more.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["self-critique-loop", "tool-calling-system-prompt", "tree-of-thought-decision"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["self-reflection", "metacognition"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Does reflection actually improve agent quality?", "answer": "On complex multi-step tasks: yes (papers + practical evals show meaningful gains). On simple tasks: it's overhead. Add it where compounding errors are costly."},
            {"question": "Cost?", "answer": "Roughly 30-80% more tokens per task. Reserve for high-stakes paths; use simpler agents for low-stakes."},
            {"question": "Should the user see reflections?", "answer": "Usually no. Reflections are internal scaffolding; raw reflections in chat reads weird. Surface only the final answer."},
        ],
        "meta_title": "Agent With Built-In Self-Reflection — Prompt",
        "meta_description": "Agent pattern with explicit ‘check yourself’ after each step: assumptions, uncertainty, failure modes. Catches reasoning errors before they compound.",
    },
    {
        "slug": "rag-context-compressor",
        "title": "RAG Context Compressor",
        "tldr": "Given the user's question + retrieved chunks, compress the chunks into only the relevant sentences before passing to the answer generator. Cuts token cost 50-80% with minimal quality loss.",
        "category": "rag",
        "tags": ["rag", "compression", "token-optimization", "relevance-filter"],
        "best_for_tags": ["cost-optimization", "high-volume-rag", "long-context"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Reduce token cost on high-volume RAG", "example": "Retrieve 10 chunks (5000 tokens) → compress to relevant sentences (1200 tokens) → pass to generator."},
            {"scenario": "Long-context generation that needs focus", "example": "Compressed input means the answer model focuses on key facts, not noise."},
            {"scenario": "Multi-document synthesis", "example": "20 chunks across 5 docs → compressed cross-doc summary."},
            {"scenario": "Citation prep", "example": "Compression step also identifies WHICH chunk each kept sentence came from, simplifying citation."},
        ],
        "when_not_to_use": "Skip when chunks are already small and tight. Skip when the answer model has ample context window AND budget — compression adds latency.",
        "full_prompt": """You are a context compressor for a RAG pipeline. The user's question is provided alongside retrieved chunks. Extract ONLY the sentences relevant to answering.

INPUT
- User question: {question}
- Retrieved chunks (with source IDs): {chunks}

OUTPUT (JSON)

{
  "compressed_context": [
    {
      "source_id": "CHK_1",
      "relevant_sentences": [
        "Sentence verbatim from chunk that is relevant to the question.",
        "Another verbatim sentence."
      ],
      "why_relevant": "1-line note on what this contributes"
    },
    ...
  ],
  "skipped_chunks": [
    {"source_id": "CHK_3", "reason": "off-topic / duplicate / no specific fact addressing question"}
  ],
  "info_likely_missing": [
    "Aspects of the question that don't appear answered in any chunk."
  ]
}

RULES

1. VERBATIM. Sentences must appear exactly in the source chunk (apart from quoted-mark normalization). Don't paraphrase.

2. RELEVANT MEANS: directly addresses the question OR provides essential context for sentences that do.

3. NO PADDING. If a sentence is interesting but doesn't help answer the specific question, skip it.

4. PRESERVE CITATIONS. Every sentence is tagged with source_id so the downstream answer model can cite.

5. SURFACE GAPS. ‘info_likely_missing’ lists what the question asks but the chunks don't answer — useful signal for the answer model.

6. DEDUP. If two chunks say the same thing, include it once and note ‘duplicate in CHK_X’ in why_relevant.

7. AGGRESSIVE compression for tangential content. Even a high-relevance chunk often has 1-2 sentences carrying the weight.

QUESTION
{question}

CHUNKS
{chunks}

Output JSON only.""",
        "input_variables": [
            {"name": "question", "type": "string", "description": "User's question", "required": True, "example": "How does HNSW differ from IVFFlat in pgvector?"},
            {"name": "chunks", "type": "string", "description": "Retrieved chunks with source IDs", "required": True, "example": "CHK_1: [text]\\nCHK_2: [text]\\n..."},
        ],
        "expected_output": {
            "format": "json",
            "schema": "{ compressed_context: [{source_id, relevant_sentences, why_relevant}], skipped_chunks, info_likely_missing }",
            "sample": "{\n  \"compressed_context\": [{\"source_id\":\"CHK_1\",\"relevant_sentences\":[\"HNSW indexes use a navigable small-world graph.\"], \"why_relevant\":\"defines HNSW\"}],\n  \"skipped_chunks\": [...],\n  \"info_likely_missing\": [...]\n}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at distinguishing relevant from interesting; cites accurately."},
            {"model": "gpt-4o-mini", "compatibility": "excellent", "notes": "Great for this task — cheaper than 4o, compression doesn't need top-tier reasoning."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; overkill for pure compression."},
            {"model": "llama-3-70b-instruct", "compatibility": "good", "notes": "Solid; occasionally paraphrases instead of quoting verbatim."},
        ],
        "variations": [
            {"label": "Aggressive token-budget mode", "description": "Hard token cap on output.", "prompt_snippet": "Add: ‘output must fit within {max_tokens} tokens total. Drop more aggressively if needed.’"},
            {"label": "Per-claim extraction", "description": "Extract atomic facts.", "prompt_snippet": "Add: ‘also output a flat list of atomic claims (single facts) with source_id; useful for fact-checking the answer downstream.’"},
            {"label": "Multi-question compression", "description": "Compress for several queries at once.", "prompt_snippet": "Accept list of questions; produce per-question compressed_context, with shared chunks appearing in each."},
        ],
        "failure_modes": [
            {"symptom": "Sentences paraphrased, not verbatim.", "fix": "Re-pin: ‘exact quotes from source; if no exact sentence works, mark as needing inference downstream rather than rewriting.’"},
            {"symptom": "Too aggressive — drops needed context.", "fix": "Add: ‘include 1-2 supporting sentences for context, not just the headline fact.’"},
            {"symptom": "‘Skipped chunks’ section empty.", "fix": "Add: ‘every chunk gets a status — either content kept or reason for skip; no chunk is invisible.’"},
            {"symptom": "‘Info likely missing’ section empty.", "fix": "Add: ‘unless every aspect of the question is answered, list at least one missing piece. ‘Nothing missing’ is rare.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o-mini", "gpt-4o", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["rag-with-citations", "rag-query-rewriting", "rag-prompt-with-confidence"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["context-compression", "rag-optimization"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Does compression hurt answer quality?", "answer": "Usually no, sometimes improves (less noise). Run paired evals: same question, full vs compressed context. If compression hurts more than 5%, your compressor is too aggressive."},
            {"question": "Which model to use for compression?", "answer": "Use a small/cheap model. Compression doesn't need top-tier reasoning. gpt-4o-mini / claude-3-5-haiku perform similarly to bigger models on this task and cost 10x less."},
            {"question": "When does this beat reranking?", "answer": "Reranking REORDERS chunks; compression KEEPS only relevant content. They compose: rerank then compress. Compression has bigger token savings."},
        ],
        "meta_title": "RAG Context Compressor — Prompt",
        "meta_description": "Compress retrieved RAG chunks to only the relevant sentences. 50-80% token savings, source IDs preserved for citation, gaps surfaced.",
    },
]
