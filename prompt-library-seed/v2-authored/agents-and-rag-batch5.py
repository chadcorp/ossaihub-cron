"""Agents & RAG — batch 5."""

RECORDS = [
    {
        "slug": "agent-tool-discovery-and-selection",
        "title": "Agent Tool Discovery And Selection",
        "tldr": "Designs the tool catalog an agent needs for a task: surveys available tools, scores fit, identifies gaps, recommends a minimal set with fallback paths and failure modes for each tool.",
        "category": "agents",
        "tags": ["agents", "tools", "tool-use", "design"],
        "best_for_tags": ["ai-engineers", "platform-teams"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "New agent capability planning", "example": "Want agent to do 'research a competitor' — which tools to give it?"},
            {"scenario": "Tool-catalog audit", "example": "Existing agent has 40 tools; audit which it actually needs."},
            {"scenario": "Cross-team agent integration", "example": "Multiple teams' tools merging into one agent platform; rationalize the set."},
            {"scenario": "Cost / latency optimization", "example": "Agent slow + expensive; identify which tools to replace with cheaper alternatives."},
        ],
        "when_not_to_use": "Skip when the task is purely one-tool (no real selection needed). Skip when tools are still being scoped — use after tools exist or are concretely planned.",
        "full_prompt": """You are a tool-catalog designer. Choose tools for an agent: minimum viable set, fallbacks, failure modes.

INPUT
- The task / goal: {task_goal}
- Available tools (with name, what they do, latency, cost): {available_tools}
- Performance targets: {performance}      (latency, cost, accuracy)
- Constraints: {constraints}              (no external API, must be deterministic, etc.)
- Existing agent context (prior tools, current behavior): {existing_context}

OUTPUT

## 1. Task decomposition
Break the task into MINIMAL operations:
- Op 1: ___ (input → output)
- Op 2: ___

The set of ops is the spec for tool selection.

## 2. Tool-to-op mapping
For each op, candidate tools:
| Op | Candidate tool | Fit (1-5) | Latency | Cost | Notes |

Mark gaps where no available tool fits well.

## 3. Recommended set
The MINIMAL tools that cover all ops:
- **Tool A** — used for ___ . Justification: best fit + lowest latency.
- **Tool B** — used for ___ . Justification.
- ...

Fewer tools is better (cognitive load on the model + tool-selection latency). Add only if op truly needs it.

## 4. Fallback paths
For each tool, what if it fails?
- **If Tool A times out:** retry once / fall back to Tool A' / surface error to user.
- **If Tool A returns nothing:** check via Tool B / try different query.
- **If Tool A returns hallucination-prone output:** validate via Tool C / require source citation.

## 5. Tool-selection prompt fragments
Help the model PICK the right tool reliably. Output draft system-prompt language:
- "Use Tool A when: ___"
- "Use Tool B when: ___"
- "Don't use Tool C unless: ___"

Specific, observable conditions. Not "use when appropriate."

## 6. Gaps
Where no available tool fits an op:
- **Op missing tool:** ___
- **Workaround:** ___
- **Recommendation:** build / buy / out-of-scope.

## 7. Failure-mode catalog
For each recommended tool:
- **Most common failure mode:** ___
- **Detection:** how agent knows the tool failed.
- **Mitigation:** what to do.

## 8. Cost / latency budget
Rough budget for one task run:
- Tool A: ~$0.001 + 200ms
- Tool B: ~$0.005 + 500ms
- LLM call: ~$0.02 + 1500ms
- **Total: ~$0.026 + 2.2s**

If exceeds performance target, recommend tool replacement.

CRITICAL RULES
- Minimal set. Don't add tools that aren't needed.
- Tool-selection prompt fragments are SPECIFIC + OBSERVABLE.
- Fallback paths for every tool. Tools fail; agents need recovery.
- Cost/latency budget calculated. Performance targets enforced.
- Gaps explicitly named — agent designer needs to know what to build.

TASK GOAL
{task_goal}

AVAILABLE TOOLS
{available_tools}

Begin.""",
        "input_variables": [
            {"name": "task_goal", "type": "string", "description": "Task / goal", "required": True, "example": "Research a competitor: pull website + 10K filings + recent news, produce a 1-page brief."},
            {"name": "available_tools", "type": "string", "description": "Available tools with metadata", "required": True, "example": "web_search (~$0.005, 800ms), web_fetch (~$0, 1500ms), file_search (free, 200ms), sec_edgar_lookup (free, 1000ms), summarize_long_doc (LLM, $0.02, 2000ms)..."},
            {"name": "performance", "type": "string", "description": "Performance targets", "required": True, "example": "Latency < 30s end-to-end, cost < $0.10/run, accuracy: 95% factual on key claims."},
            {"name": "constraints", "type": "string", "description": "Constraints", "required": True, "example": "External APIs OK. No PII storage. Must show sources for every claim."},
            {"name": "existing_context", "type": "string", "description": "Existing agent state", "required": False, "example": "Agent currently has 12 tools; only 3-4 typically used per run. Rationalize."},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Eight sections: task decomposition, tool-to-op mapping, minimal recommended set with justification, fallback paths, prompt fragments for tool selection, gaps, failure-mode catalog, cost/latency budget.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at minimal-set discipline + fallback design."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; good at tool-selection prompt fragments."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; sometimes verbose tool descriptions."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple agents; thins on multi-fallback design."},
        ],
        "variations": [
            {"label": "Cost-optimization focus", "description": "Tight cost budget.", "prompt_snippet": "Prioritize: replace expensive LLM tools with cheaper deterministic alternatives where accuracy allows. Output cost-delta per replacement."},
            {"label": "Reliability focus", "description": "Optimize for reliability.", "prompt_snippet": "Prioritize: every tool has a fallback. Acceptable to use more tools if reliability improves. Latency budget relaxed."},
            {"label": "Multi-agent extension", "description": "Distribute tools across agents.", "prompt_snippet": "If multiple specialist agents, allocate tools per specialist + define handoff tool. Use with agent-handoff prompt."},
        ],
        "failure_modes": [
            {"symptom": "Recommends too many tools.", "fix": "Re-pin: 'minimal set. Each tool justified by an op only it can do.'"},
            {"symptom": "Vague tool-selection rules.", "fix": "Force: 'observable conditions. \"Use A when input is HTML\" not \"use A when appropriate.\"'"},
            {"symptom": "Missing fallback paths.", "fix": "Hard rule: 'every tool has at least one fallback. Failing tool without fallback = task failure.'"},
            {"symptom": "Cost/latency not totaled.", "fix": "Add: 'per-run total computed + compared to performance target.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["tool-calling-system-prompt", "agent-cost-aware-tool-selection", "rag-document-router"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["agent", "tool-use"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why minimal-set?", "answer": "Each extra tool adds: cognitive load for the LLM (mis-selection), latency for tool-selection, cost for tool descriptions in context. Smaller catalogs perform better."},
            {"question": "When to add a redundant tool?", "answer": "When the primary tool has known failure modes you can't recover from internally (e.g., external API unreliable). Redundancy is intentional, not default."},
            {"question": "How to maintain the tool-selection prompt over time?", "answer": "Treat it as code. Version it, test it (with eval set), update when tools change. The selection prompt is the agent's most-impactful surface."},
            {"question": "Multi-tool handling — parallel or sequential?", "answer": "If tools are independent, prefer parallel calls. If sequential dependency, model handles it. Specify in tool-selection prompts."},
        ],
        "meta_title": "Agent Tool Discovery And Selection — Agent Prompt",
        "meta_description": "Design an agent's tool catalog: minimal viable set, fallback paths, selection prompt fragments, cost/latency budget, failure-mode catalog.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "rag-chunking-strategy-picker",
        "title": "RAG Chunking Strategy Picker",
        "tldr": "Picks a chunking strategy for a RAG corpus based on document type, query patterns, and retrieval performance — recommends size, overlap, hierarchy, and chunking method with eval criteria.",
        "category": "rag",
        "tags": ["rag", "chunking", "retrieval", "design"],
        "best_for_tags": ["ai-engineers", "search-teams"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "New RAG project", "example": "Building a docs Q&A; how to chunk the docs corpus."},
            {"scenario": "RAG quality issue", "example": "Retrieval irrelevant; rethink chunking strategy."},
            {"scenario": "Multi-corpus RAG", "example": "Docs + tickets + chat-logs; each may need different chunking."},
            {"scenario": "Hybrid retrieval design", "example": "BM25 + embeddings + reranker; chunking interacts with all three."},
        ],
        "when_not_to_use": "Skip when corpus is tiny (<100 docs) — just embed at document level. Skip without evaluation data — design without measurement is guesswork.",
        "full_prompt": """You are a RAG chunking-strategy designer. Pick chunking based on document type, queries, retrieval evidence.

INPUT
- Corpus description (doc types, average length, structure): {corpus}
- Query patterns (examples + frequency): {queries}
- Retrieval model + embedding model: {retrieval_stack}
- Reranker (if any): {reranker}
- Eval data available: {eval_data}
- Performance targets: {targets}        (recall@k, MRR, p95 latency, etc.)

OUTPUT

## 1. Corpus profile
- **Doc types:** ___ (e.g., 'long PDFs', 'short FAQ entries', 'API reference')
- **Structure:** flat / hierarchical / mixed.
- **Average doc length:** ___ tokens.
- **Length distribution:** ___ (uniform / long-tail).

## 2. Query profile
- **Query types:** factoid / definition / how-to / comparison / multi-hop.
- **Average query length:** ___ tokens.
- **Query specificity:** high / medium / low.

## 3. Chunking strategy recommendation

### Chunk size
- **Recommended:** ___ tokens (typical range 200-800).
- **Why:** balances retrieval precision vs context completeness for these query types.

### Overlap
- **Recommended:** ___ tokens (typical 20-50, sometimes 0).
- **Why:** preserves cross-chunk context for spanning information.

### Chunking method
- **Fixed-size:** simple; good for homogeneous corpora.
- **Sentence-boundary:** preserves syntactic units.
- **Semantic-similarity:** group sentences by topic similarity.
- **Recursive structure:** preserve document hierarchy (sections / subsections).
- **Layout-aware (for PDFs):** preserve tables, lists, code blocks.
- **Document-as-chunk (for small docs):** no chunking.

**Recommend:** [method] + reasoning.

### Hierarchy
- **Flat chunks:** simple; good for short queries.
- **Parent-child:** retrieve child chunks; expand to parent for context (helps multi-hop).
- **Multi-level summaries:** embed both chunks AND summaries; retrieve both.

**Recommend:** [hierarchy approach].

### Metadata to attach per chunk
- doc_id, doc_title, section, source_url, last_modified, doc_type, etc.

## 4. Special-case handling
- **Tables:** how chunked (HTML row-wise vs whole-table vs Markdown).
- **Code blocks:** keep intact (don't split mid-function).
- **Lists:** chunk per item OR keep whole list together.
- **Headers:** include heading context in each chunk's metadata.
- **Footnotes / endnotes:** attach to referring chunk.

## 5. Evaluation plan
- **Recall@k:** does the right chunk appear in top-k?
- **MRR:** how high does it rank?
- **Faithfulness:** does the response cite the right chunk?
- **Answerability:** does k chunks contain enough info to answer?

Concrete eval set + sampling plan.

## 6. Failure modes to watch
- **Too small chunks:** loses cross-sentence context.
- **Too large chunks:** dilutes relevance.
- **No overlap:** misses spanning information.
- **Wrong metadata:** filtering / reranking fails.
- **Mismatched embedding-corpus:** model was trained on different distribution.

For each: how to detect, how to fix.

## 7. Iteration plan
- **A/B alternative strategies** to test.
- **Most-likely improvement:** ___ (try first).
- **Cost of re-chunking:** ___ (time to re-embed corpus).

CRITICAL RULES
- Chunk size + overlap justified, not defaulted to '500/50' without reason.
- Special cases (tables, code, lists) addressed explicitly.
- Eval plan defined BEFORE choosing strategy. Strategy without measurement is guess.
- Failure modes named — each with detect + fix.

CORPUS
{corpus}

QUERIES
{queries}

Begin.""",
        "input_variables": [
            {"name": "corpus", "type": "string", "description": "Corpus description", "required": True, "example": "Mixed: 200 API ref pages (~1000 tokens each, structured), 500 tutorials (~3000 tokens, prose), 50 long whitepapers (~10000 tokens, sections + figures)."},
            {"name": "queries", "type": "string", "description": "Query patterns", "required": True, "example": "60% factoid ('how to authenticate', 'what's the rate limit'); 25% how-to ('integrate X with Y'); 15% comparison ('X vs Y')."},
            {"name": "retrieval_stack", "type": "string", "description": "Retrieval + embedding", "required": True, "example": "Hybrid: BM25 + text-embedding-3-large. Vector DB: pgvector. K=8 initial retrieve."},
            {"name": "reranker", "type": "string", "description": "Reranker", "required": False, "example": "Cohere rerank-multilingual-v2 reranks top-8 to top-3 for context."},
            {"name": "eval_data", "type": "string", "description": "Eval data available", "required": True, "example": "200 labeled (query, ideal-chunk) pairs from user logs."},
            {"name": "targets", "type": "string", "description": "Performance targets", "required": True, "example": "Recall@5 ≥ 90%, MRR ≥ 0.6, p95 retrieval latency < 200ms."},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Seven sections: corpus profile, query profile, chunking strategy (size/overlap/method/hierarchy/metadata), special-case handling (tables/code/lists), evaluation plan, failure modes, iteration plan.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at honest 'measure first' framing + special-case nuance."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; sometimes defaults to 500/50 — re-pin justification."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; long-context advantage for evaluating multi-doc-type corpora."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for single doc-type; thins on multi-corpus design."},
        ],
        "variations": [
            {"label": "Code-heavy corpus", "description": "Code-aware chunking.", "prompt_snippet": "Special handling: AST-aware code chunking. Preserve function boundaries. Embed code separately from prose. Use different retrieval for code vs prose queries."},
            {"label": "Multi-modal corpus", "description": "Mixed text + images / charts.", "prompt_snippet": "Special handling: figures / charts get their own chunks with caption embeddings. Text-image alignment in retrieval."},
            {"label": "Quality-debug variation", "description": "Diagnose existing RAG.", "prompt_snippet": "Given an EXISTING chunking strategy + reported quality issues, diagnose. Recommend chunking changes that target the specific issue."},
        ],
        "failure_modes": [
            {"symptom": "Default chunk size without justification.", "fix": "Re-pin: 'every parameter (size, overlap, method) must justify why for THIS corpus + queries. Not industry default.'"},
            {"symptom": "Missing special-case handling.", "fix": "Force section 4: 'tables, code, lists each explicitly addressed.'"},
            {"symptom": "No eval plan.", "fix": "Hard rule: 'choosing chunking without eval is guessing. Section 5 required.'"},
            {"symptom": "Recommends one strategy for all doc types.", "fix": "Add: 'multi-corpus may need multi-strategy. Don\\'t over-collapse.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["rag-document-router", "rag-eval-with-judge-and-citations", "agent-tool-discovery-and-selection"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["rag", "chunking"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why so much measurement focus?", "answer": "Chunking choices interact with embedding model + reranker + query distribution. Industry defaults (500/50) don't work for every corpus. Measure first, then commit to a strategy."},
            {"question": "When to use parent-child chunking?", "answer": "When questions span paragraphs (multi-hop) or context matters beyond single chunk. Retrieve precise children; expand to parent for context. Costs 2-3x storage."},
            {"question": "Re-chunking cost — when worth it?", "answer": "If quality lift is >10pp on recall, usually worth it. Less than that, look at reranker / query rewriting first. Re-embedding is expensive."},
            {"question": "How to handle very-long documents (100k+)?", "answer": "Hierarchical: chunk into 800-token blocks, but ALSO embed section-level summaries. Retrieve blocks for facts, summaries for synthesis questions."},
        ],
        "meta_title": "RAG Chunking Strategy Picker — RAG Prompt",
        "meta_description": "Choose chunking strategy for a RAG corpus: size, overlap, method, hierarchy, special-case handling, evaluation plan, failure-mode detection.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "agent-budget-aware-planner",
        "title": "Agent Budget-Aware Planner",
        "tldr": "Plans an agent task within explicit budget (cost / latency / token / step) — surfaces tradeoffs, picks the right tier of intelligence for each step, halts when budget exhausted with partial-result handoff.",
        "category": "agents",
        "tags": ["agents", "budget", "cost-control", "planning"],
        "best_for_tags": ["platform-teams", "ai-engineers"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Customer-facing chatbot", "example": "Each query has $0.05 budget; plan steps within budget."},
            {"scenario": "Long research task", "example": "$5 budget per research run; plan exploration vs synthesis allocation."},
            {"scenario": "Batch agent runs", "example": "10k runs at $0.10 each; budget enforcement at scale."},
            {"scenario": "Production safety brake", "example": "Hard cap to prevent runaway agent costs."},
        ],
        "when_not_to_use": "Skip for one-off interactive agent use (no budget). Skip when budgets aren't measurable (no token / cost tracking infrastructure).",
        "full_prompt": """You are an agent task planner. Plan within budget: cost / latency / steps. Surface tradeoffs. Halt if exhausted.

INPUT
- Task / goal: {task}
- Budget (cost USD, latency seconds, max steps, max tokens): {budget}
- Available tools + per-call costs: {tools_with_costs}
- Available LLM tiers + per-token costs: {llm_tiers}
- Constraints (must do X, can skip Y): {constraints}
- Tolerance for partial results: {partial_results_ok}

OUTPUT

## 1. Budget breakdown
- **Cost:** $___ total
- **Latency:** ___ seconds total
- **Steps:** ___ max
- **Tokens:** ___ max

## 2. Plan
Step-by-step:
| Step | Action | Tool / LLM | Estimated cost | Estimated latency | Why this tier |

For each step, choose the CHEAPEST sufficient option:
- Deterministic? Use a deterministic tool.
- Simple LLM op? Use the cheapest tier (e.g., haiku, gpt-4o-mini).
- Complex reasoning? Use the more expensive tier (e.g., sonnet, gpt-4o).
- Use the most-expensive tier (opus, gpt-4 turbo) only when reasoning is critical.

## 3. Running budget tracker
After each step, show remaining:
- Step 1: $0.02 spent / $0.05 budget. 60% remaining.
- Step 2: $0.04 / $0.05. 20% remaining.
- ...

When < 20% remaining: hard-stop unless completion needs final synthesis.

## 4. Budget-violation escape paths
What to do if budget is exhausted before task complete:
- **Partial-result mode:** return what you have + flag completeness.
- **Halt + escalate:** kick to human / higher budget loop.
- **Downgrade and continue:** use cheaper tier to finish.
- **Refuse + explain:** "task can't be completed within budget" + reason.

For this task, recommend which path.

## 5. Tradeoff surface
Where budget forced tradeoffs:
- "Used GPT-4o-mini for summary instead of sonnet — saved $0.01, but synthesis quality lower."
- "Skipped fact-check step — saved $0.005, but accuracy lower."
- "Used 1 retrieval call instead of 2 — saved $0.001, but recall lower."

Surface so caller can decide if budget should be raised.

## 6. Quality gates
Min-quality criteria for proceeding:
- "If retrieval recall < 60%, halt and escalate."
- "If LLM confidence < 0.7, request human review."
- "If output fails schema validation, retry once then halt."

## 7. Observability hooks
Logging / metrics emitted:
- Cost spend per step.
- Latency per step.
- Step that triggered budget concern (if any).
- Quality-gate failures.

This feeds dashboards + per-tenant cost tracking.

CRITICAL RULES
- Cheapest sufficient tier per step. Expensive tiers reserved for genuine reasoning.
- Running budget tracker is REQUIRED — agent can detect approaching limits.
- Budget-violation escape paths defined BEFORE the task runs.
- Tradeoffs surfaced so caller can adjust budget if needed.

TASK
{task}

BUDGET
{budget}

Begin.""",
        "input_variables": [
            {"name": "task", "type": "string", "description": "Agent task", "required": True, "example": "Research three competitors and produce a 1-page comparative brief with sources."},
            {"name": "budget", "type": "string", "description": "Budget", "required": True, "example": "$0.25 cost, 30 second latency, 8 max steps, 40k tokens"},
            {"name": "tools_with_costs", "type": "string", "description": "Tools + costs", "required": True, "example": "web_search ($0.005, 800ms), web_fetch (free, 1500ms), pdf_extract (free, 500ms), summarize_long ($0.02, 2s), gen_brief ($0.05, 5s)..."},
            {"name": "llm_tiers", "type": "string", "description": "LLM tiers", "required": True, "example": "haiku ($0.0003/1k in, $0.0015/1k out, 1s), sonnet ($0.003/1k in, $0.015/1k out, 2s), opus ($0.015/1k in, $0.075/1k out, 5s)"},
            {"name": "constraints", "type": "string", "description": "Constraints", "required": True, "example": "Must cite sources. Can skip non-essential context. Quality > speed within budget."},
            {"name": "partial_results_ok", "type": "string", "description": "Partial results OK?", "required": True, "example": "Yes — partial brief with 2 of 3 competitors better than nothing."},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Seven sections: budget breakdown, step-by-step plan with tier choice, running budget tracker, budget-violation escape paths, tradeoff surface, quality gates, observability hooks.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at tier-selection discipline + honest tradeoff surfacing."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; can over-spec tier — re-pin 'cheapest sufficient.'"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; sometimes weaker on multi-step cost arithmetic."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple plans; thins on multi-tier optimization."},
        ],
        "variations": [
            {"label": "Latency-priority", "description": "Optimize latency over cost.", "prompt_snippet": "Re-rank tier selection: prefer faster tiers even at higher cost. Used for real-time chat applications."},
            {"label": "Cost-priority", "description": "Optimize cost over latency.", "prompt_snippet": "Re-rank tier selection: prefer cheapest tier even with higher latency. Used for batch background runs."},
            {"label": "Cost-cap with overflow", "description": "Hard cost cap + overflow.", "prompt_snippet": "When budget is exceeded, instead of halt, route to a separate 'overflow' budget pool with stricter caps. Surfaces overflow rate for capacity planning."},
        ],
        "failure_modes": [
            {"symptom": "Uses most-expensive tier by default.", "fix": "Re-pin: 'cheapest tier per step that can do the work. Expensive only for genuine complex reasoning.'"},
            {"symptom": "No running tracker.", "fix": "Hard rule: 'after each step, show remaining budget. Without it, agent doesn\\'t know when to stop.'"},
            {"symptom": "Tradeoffs hidden.", "fix": "Force section 5: 'list 2-3 explicit tradeoffs the budget forced. Caller decides if budget should change.'"},
            {"symptom": "No escape paths.", "fix": "Add: 'section 4 mandatory. Agent without budget-violation handling will overrun silently.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["agent-cost-aware-tool-selection", "agent-tool-discovery-and-selection", "rag-document-router"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["agent", "cost-control"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How to set the right budget?", "answer": "Start with: total run cost / acceptable margin × safety factor (2-3x). Tune from production data. Most teams start too high and tighten."},
            {"question": "What about latency budgets in batch?", "answer": "Batch jobs care about throughput, not per-run latency. Cost budgets dominate. Use the cost-priority variation."},
            {"question": "Can agents self-adjust budget?", "answer": "Within a run, no — that's the point of a budget. Across runs, yes — meta-loop adjusts budgets based on observed cost-quality curves."},
            {"question": "What's a good cost-per-step distribution?", "answer": "Power-law: most steps cheap (deterministic + small LLM), a few steps expensive (reasoning + large LLM). If your distribution is flat, you're over-spending on cheap steps."},
        ],
        "meta_title": "Agent Budget-Aware Planner — Agent Prompt",
        "meta_description": "Plan agent tasks within cost / latency / step budget: tier-aware step selection, running budget tracker, escape paths, tradeoff surfacing.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "rag-source-citation-enforcer",
        "title": "RAG Source Citation Enforcer",
        "tldr": "Forces a RAG response to cite sources properly: claim-by-claim citation, no extrapolation beyond cited text, explicit 'unknown' for missing info — for high-trust environments (legal, medical, compliance).",
        "category": "rag",
        "tags": ["rag", "citation", "grounding", "trust"],
        "best_for_tags": ["legal-tech", "healthcare-ai", "compliance"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Legal-research assistant", "example": "Every claim must cite the source case / statute."},
            {"scenario": "Medical-info bot", "example": "Each medical statement must cite the source guideline."},
            {"scenario": "Compliance Q&A", "example": "Every policy claim cites the source regulation / internal policy."},
            {"scenario": "Customer-facing FAQ bot", "example": "Answers cite the FAQ source — auditable."},
        ],
        "when_not_to_use": "Skip for casual / creative queries — citation discipline hurts UX. Skip when there's no underlying source corpus to cite.",
        "full_prompt": """You are a RAG source-citation enforcer. Force claim-by-claim citation; refuse extrapolation; say 'unknown' when sources don't support.

INPUT
- User query: {query}
- Retrieved chunks (with chunk IDs + content): {retrieved_chunks}
- Required citation density: {citation_density}    (high / medium / low)
- Audience: {audience}
- Critical: ambiguity tolerance: {tolerance}        (zero / low / medium)

OUTPUT

## 1. Query parse
- What's the user actually asking?
- What kind of claim (definitional / procedural / regulatory / clinical)?
- Multi-part question? List sub-questions.

## 2. Source assessment
For each retrieved chunk:
- Chunk ID: ___
- What it says (1 sentence): ___
- Relevance to query (high / medium / low / off-topic): ___
- Specific lines / sentences that answer sub-questions: ___

If NO chunk is relevant: STOP. Output 'I don't have sources to answer this question. [Optional: suggest next steps.]'

## 3. Answer with claim-by-claim citations
Structure the response so every claim has [source-id] attached:

Example format:
> Acme requires SOC2 compliance for vendors handling customer data [chunk-7]. The compliance review must complete within 90 days of vendor selection [chunk-7, chunk-12]. Failure to comply blocks deployment [chunk-12].

Citation rules:
- EVERY factual claim has a citation.
- Multi-source claims cite all sources.
- Direct quotes use quotation marks + citation.
- If a claim is INFERRED from a source (not stated literally), label as 'inferred from [chunk-X]'.

## 4. Unsupported claims
What you would have said but DON'T have sources for:
- "Common practice is X but no chunk states this."
- "The user might be asking about Y, but Y isn't in retrieved chunks."

Flag these as 'unknown' or 'out of scope of provided sources'.

## 5. Confidence per sub-question
| Sub-question | Answer | Citations | Confidence |
|---|---|---|---|

Confidence:
- **Sourced:** direct quote / paraphrase.
- **Inferred:** logical inference from cited material.
- **Partial:** some aspect sourced, others not.
- **Unsupported:** no source covers this.

## 6. Information gaps
What additional retrieval / sources would HELP answer this fully:
- "If we had chunk on [topic], we could address X."
- "User might need policy from [external source] for full context."

This feeds back to retrieval improvement.

## 7. Caveats for audience
- "These chunks are from [date]; policy may have changed."
- "Chunks cover [scope]; if user is asking outside scope, escalate."
- "For [audience], add: 'consult [expert type] for personalized advice' if applicable."

CRITICAL RULES
- EVERY factual claim has a citation. Uncited claim = unsourced.
- NO extrapolation beyond what cited chunks say.
- 'Unknown' / 'out of scope' is a valid answer when sources don't support.
- Inferred ≠ sourced. Label clearly.
- Information gaps surfaced for retrieval improvement.

RETRIEVED CHUNKS
{retrieved_chunks}

QUERY
{query}

Begin.""",
        "input_variables": [
            {"name": "query", "type": "string", "description": "User query", "required": True, "example": "What's our vendor SOC2 review process and timeline?"},
            {"name": "retrieved_chunks", "type": "string", "description": "Retrieved chunks with IDs", "required": True, "example": "chunk-7: 'All vendors handling customer data must hold SOC2 Type II certification...'; chunk-12: 'Vendor compliance review must complete within 90 days of selection. Non-compliance blocks deployment to production.'"},
            {"name": "citation_density", "type": "string", "description": "Required citation density", "required": True, "example": "High — every factual sentence cited"},
            {"name": "audience", "type": "string", "description": "Audience", "required": True, "example": "Internal procurement team — needs auditable answer"},
            {"name": "tolerance", "type": "string", "description": "Ambiguity tolerance", "required": True, "example": "Low — better to say unknown than guess"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: query parse, per-chunk source assessment, answer with claim-by-claim citations, unsupported claims flagged, per-sub-question confidence, info gaps for retrieval, audience caveats.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at refusing to extrapolate + clean inferred/sourced separation."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; can drift toward extrapolation — re-pin no-extrapolation rule."},
            {"model": "gemini-1.5-pro", "compatibility": "excellent", "notes": "Strong long-context for multi-chunk citation."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple Q&A; citation discipline drops on complex multi-chunk queries."},
        ],
        "variations": [
            {"label": "Footnote-style citations", "description": "Output with numbered footnotes.", "prompt_snippet": "Replace inline [chunk-X] with numbered superscript footnotes. Output footnote list at bottom with chunk content quoted."},
            {"label": "Confidence-only output", "description": "Just confidence rating + sources.", "prompt_snippet": "Skip prose answer. Output: confidence rating + citations + 'unknown' for unsupported. Used for downstream pipelines."},
            {"label": "Multi-source synthesis", "description": "Compare conflicting sources.", "prompt_snippet": "If chunks disagree, output: 'Source A says X [chunk-7]. Source B says Y [chunk-12]. The disagreement: ___. Resolution requires: ___.'"},
        ],
        "failure_modes": [
            {"symptom": "Claims without citation.", "fix": "Hard rule: 'every factual sentence has [chunk-X]. Uncited claim is unsourced and must be flagged or removed.'"},
            {"symptom": "Extrapolates beyond sources.", "fix": "Re-pin: 'do not infer beyond what chunks state. If user wants X and chunks cover Y, say so explicitly.'"},
            {"symptom": "Confuses inferred and sourced.", "fix": "Force: 'inferred claims labeled as such. Not the same as direct citation.'"},
            {"symptom": "Refuses everything.", "fix": "Re-pin: 'if chunks ARE relevant, answer. Refusal is for genuinely unsupported claims, not low-confidence answers.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["rag-eval-with-judge-and-citations", "rag-chunking-strategy-picker", "evidence-quality-scorer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["rag", "citation"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why so strict on citation?", "answer": "In high-trust domains (legal, medical, compliance), un-cited claims are liability. Forcing citation makes the answer AUDITABLE — the user can verify every claim against the source."},
            {"question": "Won't this hurt UX?", "answer": "For high-trust use cases, citation IS the UX. The user wants to see sources. For casual chat, use a different prompt without citation enforcement."},
            {"question": "What about inferred answers?", "answer": "Label them. 'Inferred from [chunk-X]' tells the reader the chunk doesn't literally say this; you inferred. They can verify the inference is reasonable."},
            {"question": "How to handle conflicting sources?", "answer": "Use the multi-source-synthesis variation. Surface the disagreement explicitly; let the user resolve it. Don't hide conflicts."},
        ],
        "meta_title": "RAG Source Citation Enforcer — RAG Prompt",
        "meta_description": "Force claim-by-claim citation in RAG responses: no extrapolation, explicit 'unknown' for unsupported claims, per-sub-question confidence.",
        "version": "v2.0",
        "release_status": "stable",
    },
]
