"""Agents and RAG — batch 4."""

RECORDS = [
    {
        "slug": "rag-document-router",
        "title": "RAG Document Router (Which Index to Query)",
        "tldr": "Routes a user query to the right document index/collection: legal-docs vs product-docs vs support-tickets etc. Outputs the chosen index plus a confidence + fallback chain.",
        "category": "rag",
        "tags": ["rag", "router", "retrieval", "multi-index"],
        "best_for_tags": ["multi-corpus-rag", "enterprise-rag", "production"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Multi-knowledge-base RAG", "example": "User asks about pricing → route to commerce-docs; about API errors → route to engineering-docs; about company history → route to corporate-wiki."},
            {"scenario": "Tiered retrieval cost", "example": "Cheap small index first; if low confidence, fall back to expensive large index."},
            {"scenario": "Permission-aware routing", "example": "Internal vs external docs; route based on user's role + query content."},
            {"scenario": "Multilingual routing", "example": "Detect language, route to the right language-specific index."},
        ],
        "when_not_to_use": "Skip for single-index RAG (overhead, no benefit). Skip when query categories aren't crisply separable — router can't fix overlapping corpora.",
        "full_prompt": """You are a query router for a multi-index RAG system. Pick the right index for this query.

INPUT
- User query: {query}
- Available indexes (each: name, description, sample-questions): {indexes}
- User context (role, permissions, prior turns): {user_context}

OUTPUT (JSON)

{
  "primary_index": "<index_name>",
  "primary_confidence": 0.0-1.0,
  "fallback_indexes": ["index_b", "index_c"],
  "reasoning": "1-2 sentence explanation",
  "should_fan_out": true|false,
  "rewrite_if_routed_to_index": "<optional rewritten query>",
  "permissions_concern": null | "<explanation>"
}

RULES

1. primary_index: the SINGLE best match.
2. primary_confidence:
   - >0.8 = strong, unambiguous match
   - 0.5-0.8 = plausible but multiple indexes could apply
   - <0.5 = poor match overall (consider should_fan_out=true)
3. fallback_indexes: 1-3 other indexes likely to also have relevant content. Order by relevance.
4. should_fan_out: TRUE if the query likely spans multiple indexes (e.g., ‘Are our prices in compliance with our SLA?’ touches both pricing AND compliance).
5. rewrite_if_routed_to_index: if the chosen index has different terminology, rewrite the query in that vocabulary. Example: user asks ‘what's our coverage’ → routing to legal-docs → rewrite to ‘what does our liability policy cover’.
6. permissions_concern: if the query content suggests the user is asking something they shouldn't have access to (e.g., a customer asking for internal-only info), flag it. Don't block — just signal.

ANTI-PATTERNS
- Don't route to an index based on KEYWORD MATCH alone. ‘Refund’ in the query might mean billing, legal, or product question depending on context.
- Don't pick an index just because the user's prior turn was about that topic. Check the CURRENT query intent.
- Don't fan out unnecessarily — multiplies retrieval cost.

QUERY: {query}

INDEXES:
{indexes}

Output JSON only.""",
        "input_variables": [
            {"name": "query", "type": "string", "description": "User's question", "required": True, "example": "How do I cancel my subscription if I'm under an annual contract?"},
            {"name": "indexes", "type": "string", "description": "Available indexes with descriptions", "required": True, "example": "billing-docs: customer-facing billing FAQs, refund policies, plan changes. product-docs: how to use features. legal-docs: terms of service, contracts. support-tickets: solved tickets with resolutions."},
            {"name": "user_context", "type": "string", "description": "User role/permissions/recent turns", "required": False, "example": "Authenticated customer, Pro tier, prior turn was about pricing"},
        ],
        "expected_output": {
            "format": "json",
            "schema": "{ primary_index, primary_confidence, fallback_indexes, reasoning, should_fan_out, rewrite_if_routed_to_index, permissions_concern }",
            "sample": "{\n  \"primary_index\": \"billing-docs\",\n  \"primary_confidence\": 0.85,\n  \"fallback_indexes\": [\"legal-docs\", \"support-tickets\"],\n  \"reasoning\": \"Cancellation under contract straddles billing operations and legal terms; billing handles the routine path.\",\n  \"should_fan_out\": true,\n  \"rewrite_if_routed_to_index\": null,\n  \"permissions_concern\": null\n}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong intent inference; honest about ambiguous queries (sets should_fan_out)."},
            {"model": "gpt-4o-mini", "compatibility": "excellent", "notes": "Routing doesn't need top-tier reasoning; mini is great for high-volume."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; overkill for pure routing."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Fast, cheap; occasional miss on ambiguous queries."},
        ],
        "variations": [
            {"label": "With learned routing", "description": "Use historical query-index hit rates.", "prompt_snippet": "Add: ‘per-index historical hit rate (queries successfully answered from this index) as input. Bias toward higher-hit-rate indexes when confidence is similar.’"},
            {"label": "Cost-aware routing", "description": "Pick cheaper index when match is decent.", "prompt_snippet": "Add: ‘each index has a cost rating; if confidence on cheap index > 0.7, prefer it over expensive even if expensive scores 0.8.’"},
            {"label": "Permission-strict", "description": "Hard block on permission-mismatched indexes.", "prompt_snippet": "Add: ‘some indexes are role-restricted; never route to an index the user doesn't have permission for; reroute to closest accessible alternative.’"},
        ],
        "failure_modes": [
            {"symptom": "Routes based on keyword match, not intent.", "fix": "Re-pin: ‘consider what the user actually needs answered, not the surface words.’"},
            {"symptom": "Never sets should_fan_out=true.", "fix": "Add: ‘ambiguous queries are common; fan-out for queries touching multiple domains is the right call ~20% of the time.’"},
            {"symptom": "Confidence inflation.", "fix": "Add: ‘calibration test: 30% of queries should be confidence 0.5-0.8; if all >0.8, you're overclaiming.’"},
            {"symptom": "Ignores user context.", "fix": "Add: ‘user_context informs which indexes are even accessible; honor that.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o-mini", "gpt-4o", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["rag-query-rewriting", "rag-with-citations", "rag-context-compressor"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["query-routing", "multi-index-rag"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why route instead of fan-out always?", "answer": "Cost. Fan-out queries all indexes; routing queries one. With smart routing, you save 60-80% of retrieval cost on clear-intent queries while preserving recall via fallback chain."},
            {"question": "What if the wrong index is picked?", "answer": "Detect via post-retrieval signals: if top-K results all have low relevance scores, retry with fallback_indexes. Build the retry loop in your RAG framework, not in the router."},
            {"question": "Use a small model for this?", "answer": "Yes. Routing is a classification task; cheap models handle it well. gpt-4o-mini or claude-3-5-haiku saves cost without quality loss."},
        ],
        "meta_title": "RAG Document Router — Prompt",
        "meta_description": "Route queries to the right RAG index: primary + confidence + fallback chain + fan-out signal + permission flag. Cheap-model friendly.",
    },
    {
        "slug": "agent-handoff-between-specialists",
        "title": "Multi-Agent Handoff Between Specialists",
        "tldr": "Orchestrator prompt for handing off mid-task between specialist agents (researcher → writer → critic). Each agent sees the full context, the previous agent's output, and what's expected from them.",
        "category": "agents",
        "tags": ["multi-agent", "handoff", "specialists", "orchestration"],
        "best_for_tags": ["agent-pipelines", "specialized-tasks", "complex-workflows"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Research-write-critique pipeline", "example": "Research agent gathers facts → Writer agent drafts → Critic agent reviews. Each gets the full prior context."},
            {"scenario": "Customer support escalation", "example": "Tier-1 bot → Tier-2 specialist → Human supervisor. Each handoff preserves what's been tried."},
            {"scenario": "Code review pipeline", "example": "Coder agent → Tester agent → Security reviewer. Each adds findings, none undo prior work."},
            {"scenario": "Sales qualification", "example": "Lead-screening agent → SDR agent → AE agent. Context carries through."},
        ],
        "when_not_to_use": "Skip for single-agent tasks (overhead). Skip when the agents would benefit more from being tools the orchestrator calls vs full conversational agents.",
        "full_prompt": """You are managing a multi-agent handoff. The current agent is finishing; the next specialist takes over.

INPUT
- Current task: {task}
- Current agent's role: {current_role}
- Current agent's output: {current_output}
- Next agent's role: {next_role}
- Pipeline state so far (what's been tried, decided, contributed): {pipeline_state}

OUTPUT — handoff packet, ~150-300 words

## 1. STATE SO FAR (machine-readable summary)
```
Task: <restated>
Current state: <e.g., research_complete, draft_v1_complete, review_in_progress>
Previous agents (in order):
- <role>: <one-line contribution>
- <role>: <one-line contribution>
Decisions made: <list>
Constraints: <list>
Open questions: <list>
```

## 2. WHAT {next_role} INHERITS
- The output from current agent (full or compressed if huge — note compression).
- Tools available to next agent.
- Time/budget remaining for this task.

## 3. WHAT {next_role} IS EXPECTED TO PRODUCE
Specific deliverable. Format. Quality bar.
Example: "Draft 600-word brief in markdown; max 3 inline citations; no marketing language."

## 4. WHAT {next_role} SHOULD NOT DO
- Don't redo work already done (specifies what NOT to redo)
- Don't undo decisions (lists locked decisions)
- Don't expand scope (states what's out of scope)

## 5. WARNINGS / WATCH-FOR
Things the next agent should know that aren't in the formal state:
- Edge cases discovered
- Tool failures encountered
- User clarifications received mid-flight

## 6. ESCALATION RULES
When should next agent NOT just continue? Examples:
- If a new constraint emerges that contradicts a prior decision → escalate to orchestrator
- If tool budget exceeds plan → escalate
- If output diverges from the format spec → escalate

CRITICAL RULES
- Don't paraphrase the previous agent's output. Preserve verbatim or note clearly that you compressed.
- WATCH-FOR section captures TACIT knowledge that won't auto-transfer.
- Next agent should be able to start work immediately without re-reading the full conversation.

TASK: {task}
CURRENT ROLE: {current_role}
NEXT ROLE: {next_role}

Now build the handoff packet.""",
        "input_variables": [
            {"name": "task", "type": "string", "description": "Overall task", "required": True, "example": "Write a research brief on vector database trends for the engineering team"},
            {"name": "current_role", "type": "string", "description": "Current agent's role", "required": True, "example": "researcher"},
            {"name": "current_output", "type": "string", "description": "Current agent's final output", "required": True, "example": "[Research findings: 12 papers found, 3 contradictions, summary attached]"},
            {"name": "next_role", "type": "string", "description": "Next agent's role", "required": True, "example": "writer"},
            {"name": "pipeline_state", "type": "string", "description": "Pipeline state", "required": True, "example": "Task started 30min ago. User clarified audience = senior engineers. Decided to skip startup-only papers."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: state, inherits, expected, should-not-do, warnings, escalation rules. 150-300 words.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on the ‘shouldn't redo’ list — surfaces what's locked."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can be verbose — re-pin word count."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; warning section sometimes thin."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for shallow handoffs; deep multi-agent flows need stronger model."},
        ],
        "variations": [
            {"label": "Async-handoff", "description": "Next agent isn't immediately available.", "prompt_snippet": "Add: ‘if handoff is async (next agent not running yet), include a wake-up trigger and what state it needs to find ready.’"},
            {"label": "Backtrack-handoff", "description": "Handoff back to a previous agent.", "prompt_snippet": "Add: ‘if next_role was already in pipeline, this is a backtrack — note WHY backtrack and what new info exists.’"},
            {"label": "Human handoff", "description": "Next agent is human, not LLM.", "prompt_snippet": "Add: ‘if next agent is human, packet must be human-friendly: prose, not pure structured. Bullet rules still apply.’"},
        ],
        "failure_modes": [
            {"symptom": "Paraphrases previous output (loses fidelity).", "fix": "Re-pin: ‘preserve verbatim or note compression. Don't paraphrase silently.’"},
            {"symptom": "‘Should not do’ section is empty.", "fix": "Force: ‘every handoff has locked decisions; list at least 2 don't-redo and 1 don't-undo.’"},
            {"symptom": "Watch-for section is generic.", "fix": "Add: ‘watch-for is tacit, mid-task knowledge — at minimum 2 specifics or note ‘none surfaced.’"},
            {"symptom": "Escalation rules absent.", "fix": "Force: ‘every handoff has cases where the next agent should NOT just proceed. List at least 2.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["tool-calling-system-prompt", "agentic-research-with-subgoals", "agent-with-self-reflection-step"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["multi-agent-system", "agent-handoff"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "When does handoff beat just doing it all in one agent?", "answer": "When specialists have meaningfully different capabilities (research model vs writing model) or when context compression helps (researcher has lots of context the writer doesn't need)."},
            {"question": "Cost?", "answer": "Each handoff is an extra LLM call to construct the packet. ~1k tokens. Worth it for tasks > 5k tokens overall."},
            {"question": "How does this differ from a chain?", "answer": "Chain is one-shot per agent. Handoff packets capture state, decisions, warnings — the structure that prevents agents from undoing each other's work."},
        ],
        "meta_title": "Multi-Agent Handoff Between Specialists — Prompt",
        "meta_description": "Orchestrate handoffs between agents: state summary, inherits, expected output, locked decisions, watch-for, escalation rules.",
    },
    {
        "slug": "agent-cost-aware-tool-selection",
        "title": "Cost-Aware Tool Selection",
        "tldr": "Agent system prompt that adds cost-awareness to tool selection: prefer cheaper tools when sufficient, escalate to expensive only when needed. Includes a token budget per task.",
        "category": "agents",
        "tags": ["agents", "cost-optimization", "tool-selection", "budget"],
        "best_for_tags": ["production-agents", "cost-control", "scaled-agents"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Search agent with multiple search providers", "example": "Free search first (Tavily basic); only call premium (Tavily Pro) if results insufficient."},
            {"scenario": "Model tiering agent", "example": "Use Haiku for routine; escalate to Sonnet for complex; escalate to Opus only when explicitly hard."},
            {"scenario": "Browsing agent", "example": "Try cached page first; only fetch live if cache stale or missing."},
            {"scenario": "Compute-heavy tool", "example": "Estimate before running; ask user if cost > $1 / call."},
        ],
        "when_not_to_use": "Skip when cost is negligible (small one-shot agents). Skip when latency matters more than cost — cheaper tools are often slower.",
        "full_prompt": """You are a cost-aware agent. Tool selection considers BOTH capability AND cost.

INPUT
- User request: {request}
- Available tools (each with cost rating): {tools_with_cost}
- Task budget (max USD or tokens): {budget}
- User priority (cost / quality / latency / balanced): {priority}

OPERATING RULES

## Cost ladder
For each task, classify the SUFFICIENT capability tier:
- TIER 1 (cheap): basic lookups, single-document queries, classification
- TIER 2 (medium): multi-source synthesis, reasoning chains, structured extraction
- TIER 3 (expensive): novel reasoning, long-context analysis, complex creative work

Start at TIER 1. ESCALATE only when:
- Tool returned insufficient signal (score below threshold)
- Task explicitly requires capability beyond Tier 1
- User explicitly asked for high quality

## Budget enforcement
- Track cumulative cost in this conversation.
- If approaching {budget} * 0.8, simplify approach (truncate context, drop optional steps).
- If exceeding {budget} * 1.0, STOP and synthesize with what you have. Tell the user.
- NEVER silently exceed budget; surface and ask if user wants to extend.

## Tool selection rubric
For each tool call:
1. What's the MINIMAL tier that could plausibly answer this step?
2. Does the cheaper version have known failure modes for this query type? (If yes, skip up a tier.)
3. Estimate cost. Compare to remaining budget.
4. Call. If insufficient → escalate to next tier ONCE before giving up.

## Anti-patterns
- Calling Tier 3 for routine tasks ("just to be safe")
- Calling Tier 1 for tasks known to need Tier 3 (wastes a round-trip)
- Ignoring budget until exceeded — surface ahead

## Final answer
Always include cost summary: how much was spent, on what tier of tools.

USER REQUEST
{request}

AVAILABLE TOOLS (with cost):
{tools_with_cost}

BUDGET: {budget}
PRIORITY: {priority}

Begin.""",
        "input_variables": [
            {"name": "request", "type": "string", "description": "User's request", "required": True, "example": "Find me 3 recent papers on retrieval augmented generation"},
            {"name": "tools_with_cost", "type": "string", "description": "Tools with cost ratings", "required": True, "example": "search_basic ($0.001/call, top-10 results). search_premium ($0.05/call, top-50 + summaries). read_url ($0/call). summarize_with_haiku ($0.0001). summarize_with_sonnet ($0.003)."},
            {"name": "budget", "type": "string", "description": "Max budget", "required": True, "example": "$0.50 per task"},
            {"name": "priority", "type": "string", "description": "Priority axis", "required": True, "example": "balanced"},
        ],
        "expected_output": {
            "format": "text",
            "sample": "Agent reasoning + tool calls + escalation decisions + final answer with cost summary.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on stair-step escalation; respects budget."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally jumps to expensive tools — re-pin tier-1 default."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; budget tracking can drift on long tasks."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Cheap option for orchestrator on routine tasks."},
        ],
        "variations": [
            {"label": "Hard-cap mode", "description": "Refuse to escalate beyond budget.", "prompt_snippet": "Add: ‘when budget exhausted, the agent STOPS — does not ask user to extend; just returns with what's gathered. Caller decides whether to continue.’"},
            {"label": "User-quote-then-confirm", "description": "Quote estimated cost; confirm with user.", "prompt_snippet": "Add: ‘at start, estimate total cost; if > $X, ask user to confirm before proceeding.’"},
            {"label": "Cost-amortized cache", "description": "Cache + reuse to amortize cost.", "prompt_snippet": "Add: ‘before any tool call, check cache (slug + args). If hit, free. Cache TTL per tool type (search=1h, embed=permanent).’"},
        ],
        "failure_modes": [
            {"symptom": "Goes straight to expensive tools by default.", "fix": "Re-pin tier-1 default; require evidence-of-insufficiency before escalation."},
            {"symptom": "Exceeds budget silently.", "fix": "Add: ‘BEFORE each call, check cumulative cost. If exceeds budget, STOP — no exceptions.’"},
            {"symptom": "Final answer lacks cost summary.", "fix": "Force: ‘ALWAYS end with cost line: ‘Spent $X across N tool calls, mostly Tier Y.’’"},
            {"symptom": "Cheap tool fails, doesn't escalate.", "fix": "Add: ‘if Tier 1 result has score < threshold OR contains ‘insufficient data’, retry with Tier 2.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["tool-calling-system-prompt", "agentic-research-with-subgoals", "agent-with-self-reflection-step"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["cost-aware-agents", "model-tiering"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How much does cost-awareness save?", "answer": "30-70% on production agent costs when there's meaningful tier separation. Less when most queries need top-tier capability anyway."},
            {"question": "Latency cost?", "answer": "Slightly slower for tasks that escalate (extra round-trip), faster for tasks that don't (cheap tools faster). Net: similar or slightly better latency."},
            {"question": "Should we display cost to users?", "answer": "Internal agents: yes, helps monitoring. User-facing: usually no, but expose option ('show cost') for power users."},
        ],
        "meta_title": "Cost-Aware Tool Selection — Prompt",
        "meta_description": "Agent system prompt with tier-based tool selection: prefer cheaper tools, escalate only when needed, hard budget enforcement.",
    },
    {
        "slug": "rag-eval-with-judge-and-citations",
        "title": "RAG Evaluation: LLM Judge With Citation Verification",
        "tldr": "Evaluates a RAG answer against the question + retrieved chunks. Checks: answer relevance, faithfulness (every claim cited or marked as inference), and verifies that each citation actually supports the claim.",
        "category": "rag",
        "tags": ["rag-eval", "llm-judge", "faithfulness", "citation-verification"],
        "best_for_tags": ["rag-quality", "evaluation", "compliance"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Pre-deploy RAG eval", "example": "Run on 50 held-out QA pairs before shipping. Reject deploy if faithfulness < 90%."},
            {"scenario": "Post-prod monitoring", "example": "Sample 1% of production RAG answers; judge them; alert on faithfulness drift."},
            {"scenario": "Per-customer audit", "example": "Compliance customer wants proof RAG isn't hallucinating; this prompt generates the audit trail."},
            {"scenario": "Comparing RAG variants", "example": "A/B testing prompt-with-confidence vs basic-RAG; same judge against same dataset."},
        ],
        "when_not_to_use": "Skip when stakes are casual (chat assistant). Skip when ground-truth answers exist — use exact-match or semantic similarity instead.",
        "full_prompt": """You are an evaluator for a RAG answer. Three checks: relevance, faithfulness, citation accuracy.

INPUT
- Question: {question}
- Retrieved chunks (each with id + content): {chunks}
- RAG-generated answer (with inline citations): {answer}
- Citation format: {citation_format}                 (e.g., [chunk_id] or [doc:page] etc.)

OUTPUT (JSON)

```
{
  "answer_relevance": 0.0-1.0,
  "answer_relevance_reasoning": "1-2 sentences",
  "faithfulness": 0.0-1.0,
  "claims": [
    {
      "claim_text": "verbatim from answer",
      "claim_type": "factual | inference | summary",
      "citation": "<chunk_id>" | null,
      "citation_supports_claim": true | false | "partial",
      "supporting_chunk_quote": "verbatim quote from cited chunk" | null,
      "hallucination_risk": "low | medium | high"
    }
  ],
  "uncited_factual_claims": ["claim 1", "claim 2"],
  "fabricated_citations": ["[wrong_id_1]", ...],
  "overall_grade": "A | B | C | F",
  "blocker_issues": ["..."]
}
```

EVALUATION RULES

### Answer relevance
- 1.0: Directly answers the question, no off-topic.
- 0.7: Answers but with irrelevant additions.
- 0.4: Partially answers OR answers a similar but different question.
- 0.1: Off-topic or refusal when chunks should have allowed an answer.

### Faithfulness
- Decompose answer into atomic claims.
- For each factual claim, verify whether a cited chunk contains supporting text.
- Inferences are allowed but must be marked (and not exceed ~20% of claims).
- Uncited factual claims = potential hallucination. Flag them.
- Fabricated citations (citing chunk IDs not in input) = automatic F.

### Citation verification
- For each citation, locate the supporting passage in the cited chunk.
- ‘citation_supports_claim’ = true only if the chunk actually contains text that justifies the claim.
- ‘partial’ if the chunk is related but doesn't fully support.
- ‘false’ if the chunk is unrelated or actively contradicts.

### Overall grade
- A: relevance > 0.9, faithfulness > 0.95, all citations verified
- B: relevance > 0.7, faithfulness > 0.8, mostly verified citations
- C: relevance > 0.5 OR faithfulness > 0.6 — usable with caveats
- F: hallucination present (uncited factual claims OR fabricated citations OR factually wrong info presented confidently)

### Blocker issues
List any A→F downgrade reasons explicitly:
- "Citation [chunk_5] doesn't actually support the claim that X"
- "Answer states the dosage as 10mg but cited chunk says 5mg"
- "Cited [chunk_99] which is not in the retrieved chunks"

QUESTION: {question}

CHUNKS:
{chunks}

ANSWER:
{answer}

Output JSON only.""",
        "input_variables": [
            {"name": "question", "type": "string", "description": "Question asked", "required": True, "example": "What's the difference between HNSW and IVFFlat in pgvector?"},
            {"name": "chunks", "type": "string", "description": "Retrieved chunks with ids", "required": True, "example": "[chunk_1]: HNSW indexes use a navigable small-world graph...\\n[chunk_2]: IVFFlat partitions vectors into Voronoi cells..."},
            {"name": "answer", "type": "string", "description": "RAG-generated answer with citations", "required": True, "example": "HNSW uses a graph structure [chunk_1] giving fast queries at memory cost. IVFFlat uses Voronoi partitioning [chunk_2]..."},
            {"name": "citation_format", "type": "string", "description": "Citation format used", "required": False, "example": "[chunk_id]"},
        ],
        "expected_output": {
            "format": "json",
            "schema": "{ answer_relevance, faithfulness, claims[], uncited_factual_claims[], fabricated_citations[], overall_grade, blocker_issues[] }",
            "sample": "{\n  \"answer_relevance\": 0.95,\n  \"faithfulness\": 0.92,\n  \"claims\": [...],\n  \"uncited_factual_claims\": [],\n  \"fabricated_citations\": [],\n  \"overall_grade\": \"A\",\n  \"blocker_issues\": []\n}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong citation verification; catches partial support."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can be over-strict on inference vs factual claim boundary."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Handles long contexts well; sometimes misses subtle citation mismatches."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for high-volume sampling; verify hard cases with stronger model."},
        ],
        "variations": [
            {"label": "Pairwise judge", "description": "Compare two RAG answers head-to-head.", "prompt_snippet": "Accept TWO answers (variant A + variant B) for the same question/chunks; output: which is better, faithfulness comparison, where they disagree."},
            {"label": "Score-only fast mode", "description": "Just the numeric score, skip per-claim breakdown.", "prompt_snippet": "Skip the claims[] array; output only relevance + faithfulness + grade. Useful for high-volume monitoring."},
            {"label": "With ground truth", "description": "Compare against an expert-written answer.", "prompt_snippet": "Add input: expert_answer. Add output: agreement_with_expert (0-1), key_differences[]."},
        ],
        "failure_modes": [
            {"symptom": "Grades A on answers with uncited factual claims.", "fix": "Re-pin: ‘uncited factual claims = automatic max grade B.’"},
            {"symptom": "Misses fabricated citations.", "fix": "Add: ‘FIRST step: verify every cited chunk_id appears in the chunks input. Any not-found = automatic F.’"},
            {"symptom": "Citation_supports_claim always true.", "fix": "Add: ‘calibration test: ~15% of citations should be ‘partial’ in real eval. If everything is ‘true’, you're not verifying.’"},
            {"symptom": "Overall grade doesn't match relevance + faithfulness numbers.", "fix": "Re-pin grade ladder explicitly."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["rag-with-citations", "rag-prompt-with-confidence", "llm-as-judge-pairwise"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["rag-evaluation", "faithfulness", "llm-as-judge"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is LLM-judging reliable?", "answer": "For structural checks (citations exist, claims have support), yes. For nuanced quality (this answer is BETTER than that), it's noisier. Use this prompt for the structural checks; pair with humans for subjective grades."},
            {"question": "Cost?", "answer": "~5-10x the original RAG cost (judge processes question + chunks + answer). Worth it for pre-deploy eval. For prod monitoring, sample 1-5%."},
            {"question": "Can the judge be fooled?", "answer": "Sometimes — confident wrong answers can pass. Mitigation: use different judge model than the answer model. Use ground truth where available."},
        ],
        "meta_title": "RAG Eval: LLM Judge With Citation Verification",
        "meta_description": "Evaluate RAG answers for relevance, faithfulness, and citation accuracy. Catches uncited claims and fabricated chunk IDs.",
    },
]
