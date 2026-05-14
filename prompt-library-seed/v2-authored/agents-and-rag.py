"""Agents + RAG prompt library — v2 authored (2026-05-14)."""

RECORDS = [
    {
        "slug": "react-agent-loop",
        "title": "ReAct Agent Loop (Thought / Action / Observation)",
        "category": "agents",
        "tldr": "Run a ReAct-style agent loop with explicit Thought → Action → Observation cycles. Includes hard iteration cap, tool-error recovery, and FinalAnswer guard.",
        "tags": ["react", "agents", "reasoning"], "best_for_tags": ["tool-using-agent", "reasoning-loop"],
        "difficulty_tier": "advanced",
        "full_prompt": (
            "You are a ReAct agent. You answer the user's question by interleaving Thought (reasoning) and Action (tool calls), observing each result before continuing.\n\n"
            "AVAILABLE TOOLS (you'll be told which apply):\n{tool_descriptions}\n\n"
            "FORMAT for every step:\n"
            "Thought: <one sentence — what's the next subgoal?>\n"
            "Action: <tool_name>(<args>)\n"
            "(system fills in Observation)\n"
            "...repeat...\n"
            "When you have enough info:\n"
            "Thought: I have what I need.\n"
            "FinalAnswer: <answer the user's question, citing observations>\n\n"
            "RULES:\n"
            "1. Max {max_iter} iterations. If you hit it without an answer, output 'FinalAnswer: I couldn't determine X after {max_iter} steps. Best guess: Y because Z.'\n"
            "2. Don't loop on the same Action with the same args — if a tool gave an empty result, try a different tool or refine the args.\n"
            "3. If a tool errors, your next Thought addresses the error explicitly.\n"
            "4. Never invent an Observation. Wait for the system to provide it.\n"
            "5. FinalAnswer must reference at least one Observation as evidence; if you can't, say 'I cannot answer with available tools.'\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "user_question", "type": "string", "description": "The question to answer", "required": True, "example": "What's the current weather in Paris and is it suitable for outdoor running?"},
            {"name": "tool_descriptions", "type": "string", "description": "Available tool list with signatures", "required": True, "example": "weather(city) → returns temp_c, conditions, humidity\nair_quality(city) → returns aqi"},
            {"name": "max_iter", "type": "integer", "description": "Hard iteration cap", "required": True, "example": "8"},
        ],
        "expected_output": {"format": "text", "sample": "Thought: I need weather data for Paris.\nAction: weather('Paris')\nObservation: {temp_c: 14, conditions: 'cloudy', humidity: 78}\n\nThought: Suitable for running depends also on air quality.\nAction: air_quality('Paris')\nObservation: {aqi: 42}\n\nThought: 14°C, cloudy, AQI 42 — comfortable + clean air.\nFinalAnswer: Paris is currently 14°C, cloudy, with AQI 42 (good air quality). Suitable for outdoor running — light jacket recommended."},
        "use_cases": [
            {"scenario": "Tool-using assistants", "example": "Customer-support bot has tools for order lookup, refund, escalate; this loop drives the multi-step resolution."},
            {"scenario": "Research-task automation", "example": "Agent runs web_search + read_url + summarize tools to answer multi-hop questions."},
            {"scenario": "DevOps automation", "example": "Tools: check_status, restart_service, page_oncall; agent chooses sequence based on incident state."},
            {"scenario": "Code-agent", "example": "Tools: read_file, write_file, run_test; agent fixes bugs by editing + testing."},
        ],
        "when_not_to_use": "Don't use for single-shot tasks where one tool call suffices. Also skip when latency matters more than reasoning (chat-completion mode is faster).",
        "few_shot_examples": [
            {
                "input": "user_question: 'Did the deploy succeed?' tools: check_deploy_status(env) → {status, last_run_at}. max_iter: 4.",
                "output": "Thought: I need the deploy status for the current env.\nAction: check_deploy_status('production')\nObservation: {status: 'failed', last_run_at: '2026-05-14T16:30Z'}\n\nThought: It failed; the user probably wants the failure reason.\nAction: get_deploy_log('production', 'last')\nObservation: 'Error: missing env var DATABASE_URL'\n\nFinalAnswer: No — production deploy failed at 16:30 UTC. Cause: missing env var DATABASE_URL. Re-run after setting it.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at ReAct discipline — doesn't skip Thought, doesn't loop."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Preferred for 4+ step chains."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong; occasionally invents Observations — explicit rule needed."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Loops without strict iteration cap; enforce max_iter strictly."},
        ],
        "variations": [
            {"label": "Plan-first", "description": "Generate a plan before acting.", "prompt_snippet": "Before first Thought, output 'Plan:' with 2-4 bullets of intended subgoals. Then execute Thought/Action loop."},
            {"label": "Reflection-step", "description": "After every 3 iterations, reflect.", "prompt_snippet": "Every 3 iterations, emit 'Reflection: <what's working, what's not, should we change approach?>'."},
            {"label": "Multi-agent", "description": "Delegate to specialized sub-agents.", "prompt_snippet": "Treat sub-agents as tools. Each has its own ReAct loop; this top-level agent orchestrates."},
        ],
        "failure_modes": [
            {"symptom": "Invents Observation content (hallucinated tool output)", "fix": "Strict rule — wait for system to provide Observation; never fabricate"},
            {"symptom": "Loops on the same Action with no progress", "fix": "Rule 2 — refine args or switch tools after empty result"},
            {"symptom": "FinalAnswer without referencing any Observation", "fix": "FinalAnswer must cite ≥1 Observation; otherwise 'cannot answer'"},
            {"symptom": "Skips Thought, goes straight to Action", "fix": "Every Action requires a Thought preceding it; reject malformed steps"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["chain-of-thought", "self-critique-loop"],
        "related_tool_slugs": ["langchain", "langgraph", "smolagents"],
        "related_glossary_slugs": ["react", "agent", "tool-use"],
        "faq": [
            {"question": "What's max_iter for production?", "answer": "5-8 for most tasks. >10 = either task is too complex or tools are wrong abstraction."},
            {"question": "Should I show the loop to users?", "answer": "Stream Thoughts to power users (debugging value). For end users, show only FinalAnswer + 'thinking...' indicator."},
            {"question": "How do I handle tool errors?", "answer": "Tool returns an error in Observation; the next Thought addresses it. The prompt's rule 3 enforces this."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "ReAct Agent Loop Prompt — Thought/Action/Observation",
        "meta_description": "Run a ReAct-style agent loop with strict format, max-iter cap, tool-error recovery, no-hallucination guards.",
    },

    {
        "slug": "self-critique-loop",
        "title": "Self-Critique Loop (draft → critique → revise)",
        "category": "agents",
        "tldr": "Three-pass loop: draft answer, critique it against explicit criteria, revise. Improves quality 20-40% on complex tasks at 3x token cost.",
        "tags": ["self-critique", "reflection", "quality"], "best_for_tags": ["quality-improvement", "long-form-tasks"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You produce high-quality output via 3-pass self-critique. Each pass has a strict role.\n\n"
            "INPUTS:\n- task: what to produce\n- quality_criteria: 3-5 explicit dimensions (e.g., 'factual accuracy', 'specificity', 'no hallucinated citations')\n\n"
            "PASS 1 — DRAFT:\nProduce the best answer you can in one shot. Don't second-guess; flow.\n\n"
            "PASS 2 — CRITIQUE:\nReview your own draft against each quality_criteria. For each criterion: 'Pass / Fail / Partial' with 1-2 sentences of evidence. List the top 3 specific issues to fix.\n\n"
            "PASS 3 — REVISE:\nProduce a revised version that addresses every issue from PASS 2. Don't add new issues. If a critique was wrong, note 'PASS 2 was incorrect: ...'.\n\n"
            "OUTPUT FORMAT:\n## Draft\n[full draft]\n\n## Critique\n[criterion-by-criterion analysis]\n\n## Revised\n[final answer]\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "task", "type": "string", "description": "The task to produce output for", "required": True, "example": "Write a 200-word product update announcing our new export feature"},
            {"name": "quality_criteria", "type": "list[str]", "description": "Explicit quality dimensions", "required": True, "example": "['No marketing jargon', 'Specific about the user benefit', 'Mention the technical limit', 'Under 200 words']"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Draft\nWe're thrilled to announce... [marketing-ish 220 words]\n\n## Critique\n- No marketing jargon: Fail. 'Thrilled' is jargon.\n- Specific benefit: Partial. Says 'faster exports' but no numbers.\n- Technical limit: Fail. Doesn't mention the 10k-row cap.\n- Under 200 words: Fail (220).\n\nIssues: thrilled, no number, no cap.\n\n## Revised\nExports are now 4x faster. New behavior: rows stream as they're generated; first results visible in <3s for tables up to 10,000 rows. Larger tables still batch — we're working on lifting the cap... [195 words]"},
        "use_cases": [
            {"scenario": "Long-form content polish", "example": "Blog post drafts; the critique catches what the first pass misses."},
            {"scenario": "Specification writing", "example": "Engineering RFC; critique against 'clarity, completeness, falsifiability'."},
            {"scenario": "Marketing copy", "example": "Critique against 'no jargon, specific number, single call-to-action'."},
            {"scenario": "Email drafts (high-stakes)", "example": "Investor email or sensitive customer reply; revise pass tightens tone."},
        ],
        "when_not_to_use": "Don't use for short / simple outputs (1-line summaries) — overhead exceeds value. Also skip when latency matters more than quality.",
        "few_shot_examples": [
            {
                "input": "task: 'Write a tweet announcing a 50% off sale this weekend'. criteria: ['Under 240 chars', 'Specific discount amount', 'Clear deadline', 'No hashtag spam']",
                "output": "## Draft\n🎉 BIG SAVINGS THIS WEEKEND! Don't miss out! #sale #deals #discount\n\n## Critique\n- Char count: Pass (~70).\n- Specific discount: Fail. Doesn't say 50%.\n- Clear deadline: Partial. 'This weekend' is vague.\n- Hashtag spam: Fail. 3 hashtags = spammy.\n\n## Revised\n50% off, Friday 6pm to Sunday midnight (PT). No code needed. Link in bio.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at honest self-critique; doesn't sandbag the 'Fail' verdicts."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Use when stakes are high and depth matters."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Sometimes the critique is too lenient; instruct 'be harsh'."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; revisions can be incremental rather than substantive."},
        ],
        "variations": [
            {"label": "Adversarial critique", "description": "Critique as a hostile reviewer.", "prompt_snippet": "PASS 2 override: Adopt a hostile-reviewer persona. Find every possible issue. Steelman the worst-case critique."},
            {"label": "N-pass refinement", "description": "Add a 4th and 5th pass for stubborn issues.", "prompt_snippet": "Add PASS 4: critique the revision against the same criteria. If any still fail, PASS 5 revise. Cap at 5 passes."},
            {"label": "Two-model dialog", "description": "Use a different model for critique vs draft.", "prompt_snippet": "Note: this requires orchestration outside the prompt. Draft with Claude Sonnet 4.5; critique with GPT-5 (different blind spots); revise with Sonnet."},
        ],
        "failure_modes": [
            {"symptom": "Critique is too gentle, all 'Pass' marks", "fix": "Instruct 'be harsh — find at least 1 issue per criterion'"},
            {"symptom": "Revision introduces new issues not flagged", "fix": "PASS 3 rule: 'don't add new issues'; if you do, flag them"},
            {"symptom": "Revision incremental, not substantive", "fix": "If revision is <30% different from draft, it didn't actually address critiques; require visible rewrites"},
            {"symptom": "Loops on same issue across multiple passes", "fix": "Cap passes; if same issue persists after 3 revises, escalate to human"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["react-agent-loop", "chain-of-thought"],
        "related_tool_slugs": ["langchain", "dspy"],
        "related_glossary_slugs": ["reflection", "self-critique", "chain-of-thought"],
        "faq": [
            {"question": "How much does self-critique help?", "answer": "20-40% quality lift on complex tasks (long-form writing, code generation, multi-criteria outputs). Diminishing returns past 2 passes for simple tasks."},
            {"question": "Is it worth 3x cost?", "answer": "For high-stakes one-shots: yes. For bulk runs: no — train a better single-pass prompt instead."},
            {"question": "Can I skip the draft and just critique?", "answer": "No — the critique needs something concrete to react to. 'Critique without draft' produces vague generic advice."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Self-Critique Loop Prompt — Draft, Critique, Revise",
        "meta_description": "Three-pass quality improvement: draft, critique against explicit criteria, revise. 20-40% quality lift on long-form tasks.",
    },

    {
        "slug": "rag-with-citations",
        "title": "RAG with Inline Citations + Confidence",
        "category": "rag",
        "tldr": "Answer questions from retrieved context with sentence-level citations [doc:N]. Refuses to answer if context insufficient. Confidence score per claim.",
        "tags": ["rag", "citations", "grounding"], "best_for_tags": ["rag", "qa-over-docs", "knowledge-base"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You answer questions from retrieved context. Every claim cites which retrieved chunk supports it. Refuse to answer if context is insufficient.\n\n"
            "INPUTS:\n- question: user's question\n- retrieved_chunks: list of {chunk_id, source_doc, content, retrieval_score}\n- refuse_threshold: float (default 0.6) — if best chunk score < threshold, refuse\n\n"
            "PROCEDURE:\n1. Check: do retrieved chunks contain enough info to answer?\n   - If best chunk score < refuse_threshold OR question requires info not in any chunk → refuse.\n2. Compose answer using ONLY content from retrieved chunks.\n3. After every claim, insert [chunk_id] citing the chunk that supports it.\n4. If a claim is supported by multiple chunks, cite all.\n5. If parts of the question can be answered and parts cannot, answer the answerable parts; explicitly note what's not in the context.\n6. End with a 'Confidence' line: 0.0-1.0 for the answer overall.\n\n"
            "REFUSAL FORMAT:\n'I can't answer this from the available sources. The retrieved documents cover [X, Y] but not [Z]. Try searching for: [suggestion].'\n\n"
            "NEVER:\n- Combine context info with your training data\n- Cite a chunk you didn't use\n- Fabricate chunk_ids\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "question", "type": "string", "description": "User's question", "required": True, "example": "What's our refund policy for annual plans?"},
            {"name": "retrieved_chunks", "type": "list[Chunk]", "description": "Retrieved chunks from your RAG retriever", "required": True, "example": "[{chunk_id:'c1', source_doc:'pricing.md', content:'Annual plans: refundable within 60 days...', retrieval_score:0.87}]"},
            {"name": "refuse_threshold", "type": "float", "description": "Minimum chunk score to attempt answer", "required": False, "example": "0.6"},
        ],
        "expected_output": {"format": "markdown", "sample": "Annual plans are refundable within 60 days of purchase [c1]. After 60 days, refunds are at our discretion and require manager approval [c1]. Monthly plans follow a separate policy not covered in the retrieved docs.\n\nConfidence: 0.85"},
        "use_cases": [
            {"scenario": "Internal documentation Q&A", "example": "Employee asks 'what's our PTO policy?'; retriever pulls handbook chunks; this prompt answers with citations."},
            {"scenario": "Customer support knowledge base", "example": "Customer asks question; retriever pulls KB articles; agent reviews cited answer before sending."},
            {"scenario": "Compliance Q&A", "example": "Regulatory questions answered against the policy library; citations let auditors trace claims."},
            {"scenario": "Code documentation", "example": "'How do I use feature X?'; retrieve docs; answer with citations to the relevant doc sections."},
        ],
        "when_not_to_use": "Don't use when retrieval quality is poor (better to invest in retriever first). Also skip when answer needs reasoning beyond what's in chunks.",
        "few_shot_examples": [
            {
                "input": "question: 'Does our app support SSO?'. chunks: [{c1: 'SAML SSO available on Enterprise plan. Setup via /security/sso.', score:0.91}, {c2: 'Free plan: email/password only.', score:0.78}]",
                "output": "Yes — SAML SSO is available on the Enterprise plan and is configured at /security/sso [c1]. SSO is not available on the Free plan, which uses email/password only [c2].\n\nConfidence: 0.90",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at refusal discipline — won't fill gaps with training data."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Use when chunks are long/nuanced."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong citations; sometimes leaks training data; explicit rule needed."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; verify citations point to real content (not fabricated)."},
        ],
        "variations": [
            {"label": "Citation-format URL", "description": "Citations as URLs not chunk_ids.", "prompt_snippet": "Replace [c1] with the source_doc URL. Useful when output goes to end users who need clickable refs."},
            {"label": "Multi-language answer", "description": "Answer in user's language even if chunks are in another.", "prompt_snippet": "Detect question language. Translate the answer; preserve citations as chunk_ids."},
            {"label": "Stricter refusal", "description": "Tighten threshold; refuse more often.", "prompt_snippet": "refuse_threshold: 0.8. Better to refuse than to answer marginally — preserves trust."},
        ],
        "failure_modes": [
            {"symptom": "Combines retrieved context with training data", "fix": "Explicit rule + system reminder; if answer references X not in chunks, refuse"},
            {"symptom": "Cites chunks but answer doesn't actually use them", "fix": "Citations must be content-substantive, not decorative"},
            {"symptom": "Refuses too readily (every question)", "fix": "Calibrate refuse_threshold; 0.6 default for most use cases"},
            {"symptom": "Hallucinates chunk_ids", "fix": "Verify chunk_ids exist in input before citing"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["self-critique-loop", "react-agent-loop"],
        "related_tool_slugs": ["langchain", "llamaindex", "haystack"],
        "related_glossary_slugs": ["rag", "citations", "grounding"],
        "faq": [
            {"question": "What if chunks contradict each other?", "answer": "Output both with separate citations; flag the contradiction. Don't silently pick one."},
            {"question": "How many chunks should I retrieve?", "answer": "5-15 typically. <5 = low recall; >15 = context bloat + slower."},
            {"question": "Does confidence reflect retrieval quality?", "answer": "Roughly — but it primarily reflects how well chunks answer the question. Re-rank chunks before this prompt for best results."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "RAG with Inline Citations + Refusal Guard",
        "meta_description": "Answer from retrieved chunks with per-claim citations, refuses on insufficient context, confidence score per answer.",
    },

    {
        "slug": "agentic-rag-research",
        "title": "Agentic RAG — Multi-Hop Research with Tool-Use",
        "category": "rag",
        "tldr": "Multi-hop research agent: decompose question, retrieve+answer subquestions, synthesize. Handles 'compare X and Y across Z dimensions' style queries that simple RAG can't.",
        "tags": ["agentic-rag", "multi-hop", "research"], "best_for_tags": ["research-agent", "complex-rag"],
        "difficulty_tier": "advanced",
        "full_prompt": (
            "You answer complex research questions that require multi-hop retrieval. Decompose first, retrieve per sub-question, synthesize.\n\n"
            "INPUTS:\n- question: user's complex question\n- tools: retrieve(query, k=5), read_url(url), summarize(text), compare(items, dimensions)\n- max_subquestions: cap (default 5)\n\n"
            "PROCEDURE:\n1. DECOMPOSE: break the question into 2-5 sub-questions. Each sub-question is answerable by retrieval.\n2. For each sub-question, run retrieve(); if needed, follow up with read_url() on top results.\n3. Answer each sub-question independently with citations.\n4. SYNTHESIZE: combine sub-answers into the final answer. Surface contradictions across sources.\n5. Confidence per claim + overall.\n\n"
            "AVOID:\n- Decomposing into >5 sub-questions (over-engineers simple questions)\n- Running redundant retrievals (cache sub-answers)\n- Synthesizing without citations from each sub-answer\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "question", "type": "string", "description": "Complex research question", "required": True, "example": "How do Pinecone and Qdrant compare on pricing, scaling limits, and SDK quality?"},
            {"name": "tools", "type": "list[str]", "description": "Available tool names", "required": True, "example": "['retrieve', 'read_url', 'summarize']"},
            {"name": "max_subquestions", "type": "integer", "description": "Decomposition cap", "required": False, "example": "5"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Decomposition\n1. Pinecone pricing tiers\n2. Qdrant pricing tiers\n3. Pinecone scaling limits\n4. Qdrant scaling limits\n5. SDK quality (both)\n\n## Sub-answers\n**1. Pinecone pricing:** Free tier 100k vectors; Standard $70/mo + usage [src1]. **2. Qdrant pricing:** Free Cloud 1GB; paid tier $50/mo + usage [src2]. ...\n\n## Synthesis\nPinecone is more expensive at low volume but includes a managed serverless tier [src1]. Qdrant offers self-host as an option (Pinecone doesn't) [src2]. SDK quality is comparable; Qdrant has stronger TypeScript support [src3].\n\nConfidence: 0.83"},
        "use_cases": [
            {"scenario": "Vendor comparison research", "example": "Sales-engineering needs apples-to-apples comparison across 3-5 vendors."},
            {"scenario": "Technical due-diligence", "example": "Investor researching a stack: agent compares competitors on 5 dimensions."},
            {"scenario": "Buying decisions", "example": "Procurement team's vendor matrix is built from this prompt's output."},
            {"scenario": "Literature synthesis (smaller scale)", "example": "5-10 papers, 3-4 cross-cutting questions; produces comparative analysis."},
        ],
        "when_not_to_use": "Don't use for simple lookups (single retrieve+answer is enough). Also skip when there are no retrieval sources — different prompt territory.",
        "few_shot_examples": [
            {
                "input": "question: 'Which is faster: pgvector with HNSW or Qdrant on 10M vectors?'. tools: retrieve, read_url. max_subqs: 3.",
                "output": "## Decomposition\n1. pgvector HNSW benchmarks at 10M vectors\n2. Qdrant benchmarks at 10M vectors\n3. Methodology comparison (apples to apples?)\n\n## Sub-answers\n**1. pgvector HNSW:** ~80ms p99 at 10M, single instance [src1]. **2. Qdrant:** ~12ms p99 at 10M [src2]. **3. Methodology:** src1 used m=16 ef=200; src2 used m=64 ef=512. Higher accuracy config in src2 actually disadvantages it but it still wins.\n\n## Synthesis\nQdrant is 5-7x faster at 10M-vector scale based on these benchmarks. pgvector is simpler operationally but slower at scale.\n\nConfidence: 0.75 (methodology differences could swing the comparison)",
            }
        ],
        "model_compatibility": [
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best at decomposition discipline and contradiction-surfacing."},
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strong default; faster than Opus."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Reliable; occasionally over-decomposes."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable for 2-3 sub-questions; degrades at 5."},
        ],
        "variations": [
            {"label": "Iterative-retrieval", "description": "Each sub-answer can trigger follow-up retrievals.", "prompt_snippet": "Allow sub-questions to spawn child sub-questions (max depth 2). Useful when initial retrieval reveals more questions."},
            {"label": "Cross-source-only", "description": "Force comparison across 2+ sources per claim.", "prompt_snippet": "Reject claims supported by only 1 source unless explicitly single-source-verifiable."},
            {"label": "Disagreement-focused", "description": "Highlight where sources disagree.", "prompt_snippet": "After synthesis, add 'Contradictions found' section listing every claim where 2+ sources disagreed + analysis of why."},
        ],
        "failure_modes": [
            {"symptom": "Over-decomposes (5+ sub-Qs for a simple question)", "fix": "Cap at max_subquestions; merge sub-Qs that share answers"},
            {"symptom": "Synthesizes without citations", "fix": "Synthesis must thread the citations from sub-answers; no new claims without sources"},
            {"symptom": "Buries contradictions", "fix": "Disagreement-focused variation forces surfacing; otherwise weight the contradiction explicitly in confidence"},
            {"symptom": "Redundant retrievals (same query twice)", "fix": "Cache sub-answers; reject duplicate queries with empty results"},
        ],
        "tested_with": {"models": ["claude-opus-4", "claude-sonnet-4-5", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["rag-with-citations", "react-agent-loop"],
        "related_tool_slugs": ["langgraph", "llamaindex", "haystack"],
        "related_glossary_slugs": ["agentic-rag", "multi-hop-retrieval", "decomposition"],
        "faq": [
            {"question": "When is agentic RAG worth it vs simple RAG?", "answer": "When the question needs 2+ retrievals to answer. Comparative questions, multi-entity questions, anything with 'and how does that compare to'."},
            {"question": "Latency impact?", "answer": "3-5x slower than single-shot RAG. Worth it for complex questions where simple RAG produces wrong/incomplete answers."},
            {"question": "Cost impact?", "answer": "Roughly 5x. Each sub-question is its own retrieve+generate. Use cheaper model (Haiku) for sub-answers, Sonnet/Opus for synthesis."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Agentic RAG — Multi-Hop Research with Synthesis",
        "meta_description": "Decompose complex questions, retrieve per sub-question, synthesize with cross-source citations and contradiction-surfacing.",
    },

    {
        "slug": "chain-of-thought",
        "title": "Chain-of-Thought Reasoning (explicit steps)",
        "category": "reasoning",
        "tldr": "Solve multi-step problems by working through explicit reasoning chains. Verifies each step before proceeding. Best for math, logic, multi-constraint problems.",
        "tags": ["reasoning", "chain-of-thought", "math"], "best_for_tags": ["reasoning", "math-problems", "logic"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You solve problems by working through explicit reasoning chains. Don't skip steps; verify each before proceeding.\n\n"
            "INPUTS:\n- problem: the problem to solve\n- domain: math | logic | code | mixed (helps calibrate verification)\n\n"
            "STRUCTURE:\n1. UNDERSTAND: restate the problem in your own words. Identify what's being asked + what's given.\n2. PLAN: outline the approach in 2-4 steps. Don't commit to numbers yet.\n3. EXECUTE: work through each step. After each, ask: 'does this make sense?' If not, back up.\n4. VERIFY: check the answer against the problem. Plug it back in. Common-sense check.\n5. ANSWER: state the final answer in 1 line.\n\n"
            "RULES:\n- One reasoning step per paragraph; never combine.\n- If you spot an error mid-chain, stop and back up.\n- Numbers: show arithmetic, don't just state results.\n- Verify at the end — never skip the check.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "problem", "type": "string", "description": "The problem to solve", "required": True, "example": "A train leaves City A at 60mph at 2pm. Another leaves City B at 75mph at 3pm heading toward A. Cities are 300mi apart. When do they meet?"},
            {"name": "domain", "type": "string", "description": "math | logic | code | mixed", "required": True, "example": "math"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Understand\nTwo trains heading toward each other. Train A: starts 2pm from City A at 60mph. Train B: starts 3pm from City B at 75mph. Cities 300mi apart. Find meet time.\n\n## Plan\n1. Train A travels alone from 2pm to 3pm — calculate distance covered.\n2. From 3pm, both trains travel toward each other — calculate closing rate.\n3. Find when they cover remaining distance together.\n\n## Execute\nStep 1: From 2pm to 3pm, Train A covers 60mph × 1hr = 60mi. Remaining distance = 300 - 60 = 240mi.\nStep 2: From 3pm, closing speed = 60 + 75 = 135mph.\nStep 3: Time to cover 240mi = 240 / 135 ≈ 1.778 hours = 1hr 47min.\n\n## Verify\nMeet at 3pm + 1hr 47min = 4:47pm. Train A traveled 2hr 47min × 60mph = 167mi. Train B traveled 1hr 47min × 75mph = 133mi. Total: 167 + 133 = 300mi ✓\n\n## Answer\n4:47pm"},
        "use_cases": [
            {"scenario": "Math problem solving", "example": "Word problems where chain-of-thought halves error rate vs zero-shot."},
            {"scenario": "Logic puzzles", "example": "Multi-constraint problems (zebra puzzles, scheduling)."},
            {"scenario": "Code debugging", "example": "Walking through suspect code paths to find the bug."},
            {"scenario": "Decision analysis", "example": "Weighing options with explicit pro/con chains."},
        ],
        "when_not_to_use": "Don't use for simple lookups or single-step tasks — overhead exceeds value. Also skip for tasks requiring creativity (CoT can flatten creative output).",
        "few_shot_examples": [
            {
                "input": "problem: 'If a shirt was $40 with 20% discount, what's the final price after 8% tax?' domain: math",
                "output": "## Execute\nStep 1: Discount = $40 × 0.20 = $8. Price after discount = $40 - $8 = $32.\nStep 2: Tax = $32 × 0.08 = $2.56.\nStep 3: Final = $32 + $2.56 = $34.56.\n\n## Verify\n$40 × 0.80 × 1.08 = $32 × 1.08 = $34.56 ✓\n\n## Answer\n$34.56",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strong on math + logic chains."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Use for deep chains (10+ steps)."},
            {"model": "gpt-5", "compatibility": "excellent", "notes": "Reliable across domains."},
            {"model": "llama-3.3-70b", "compatibility": "good", "notes": "Workable for shallow chains; verify arithmetic."},
        ],
        "variations": [
            {"label": "Tree-of-thought", "description": "Explore multiple reasoning branches.", "prompt_snippet": "Instead of one chain, generate 3 candidate approaches. Evaluate each; pick the most promising; continue from there."},
            {"label": "Self-consistency", "description": "Generate 5 chains; majority-vote.", "prompt_snippet": "Generate 5 independent chains. The final answer is whichever appears most often across chains. Useful for ambiguous problems."},
            {"label": "Verify-only", "description": "Pre-existing answer; verify or debunk.", "prompt_snippet": "Skip Execute step. INPUT includes a proposed answer. Output: chain that either confirms or finds the flaw."},
        ],
        "failure_modes": [
            {"symptom": "Skips verify step (math errors slip through)", "fix": "Verify is mandatory; plug answer back in"},
            {"symptom": "Combines reasoning steps, hides errors", "fix": "One step per paragraph rule; force explicitness"},
            {"symptom": "Confidently wrong on tricky arithmetic", "fix": "Show all arithmetic; for complex numbers, use a calculator tool if available"},
            {"symptom": "Doesn't back up when error spotted", "fix": "If verify fails, RESTART from Plan with the issue noted"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["self-critique-loop", "react-agent-loop", "agentic-rag-research"],
        "related_tool_slugs": ["dspy", "langchain"],
        "related_glossary_slugs": ["chain-of-thought", "tree-of-thought", "self-consistency"],
        "faq": [
            {"question": "When does CoT help vs hurt?", "answer": "Helps: math, logic, multi-step decision. Hurts: creative writing (flattens), simple lookups (overhead)."},
            {"question": "Should I show CoT to end users?", "answer": "No — show the answer. CoT is for the model's reasoning, not the user's reading."},
            {"question": "Latency impact?", "answer": "2-3x slower than zero-shot. Worth it on problems where zero-shot accuracy is <80%."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Chain-of-Thought Prompt — Explicit Reasoning with Verify",
        "meta_description": "Solve multi-step problems with explicit reasoning chains. Step-by-step structure, mandatory verify, math/logic/code domains.",
    },
]
