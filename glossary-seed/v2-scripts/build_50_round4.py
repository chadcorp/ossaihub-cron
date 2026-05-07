"""Round 4: 50 more v2 terms (676 -> 726).

Usage:
  python build_50_round4.py --validate-only
  python build_50_round4.py --merge
"""
import argparse, json, pathlib, re, sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
REBUILT = HERE.parent / "rebuilt-v2.json"
OUT_NEW_ONLY = HERE.parent / "new-50-round4.json"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BANNED = ["powerful", "revolutionary", "cutting-edge", "cutting edge",
          "unleash", "seamlessly", "game-changer", "game changer", "groundbreaking"]

TERMS = [
    # 1. temperature-sampling
    {
        "slug": "temperature-sampling",
        "title": "Temperature Sampling",
        "category": "sampling",
        "difficulty_tier": "beginner",
        "tldr": "Decoding strategy that scales the model's logits by 1/T before softmax — higher T flattens the distribution for more diverse output, lower T sharpens it.",
        "plain_english": "Temperature is the simplest knob for controlling LLM output randomness. Divide the logits by T before softmax. T=1 is the model's natural distribution. T=0 is greedy (always pick the most likely token). T=0.7 is mildly diverse — production default for chat. T>1 gets creative-and-weird. The trade-off is determinism vs. diversity, and almost every API exposes temperature as the primary creativity dial.",
        "how_it_works": "After the model produces logits z for each candidate token, scaled logits become z/T. Softmax converts to probabilities; sampling proceeds normally. Lower T amplifies the highest logits (sharp distribution); higher T flattens (uniform-like). T=0 reduces to argmax (greedy decoding). Combined with top-k or top-p filtering, temperature controls the shape of the sampling distribution within the filter.",
        "why_it_matters": "Temperature is the most common parameter tuned in LLM applications. Wrong T makes outputs feel boring, too random, or inconsistent. For factual tasks, low T (0.0-0.3); for creative writing, mid T (0.7-1.2); for brainstorming, higher T (1.0-1.5). Combined with top-p, it shapes the model's voice in ways structural changes can't.",
        "example": "A coding assistant runs at T=0.0 (greedy) for syntax-perfect output. A creative-writing tool runs at T=0.9 plus top-p=0.95 for varied prose without going off the rails. A brainstorm feature uses T=1.2 with top-p=0.95 to surface unusual combinations. Each setting is calibrated to the task.",
        "pitfalls": [
            "T=1.5+ produces gibberish on most models; cap to safe values.",
            "Greedy isn't deterministic across providers due to floating-point ordering — only reliably reproducible at T=0 with seed support.",
            "High T amplifies hallucination — model wanders to less-likely-but-plausible-sounding tokens; pair with retrieval for factual tasks.",
            "Combined effects: T and top-p interact — high T with low top-p is conservative-creative; low T with high top-p is the opposite. Calibrate together."
        ],
        "when_use": "Use as your primary creativity knob whenever output style or variability matters — set per task class.",
        "when_avoid": "Don't change T without measuring effect on a held-out eval; small T changes can shift quality in non-obvious ways.",
        "related_terms": ["nucleus-sampling", "top-k-sampling", "top-p-sampling", "min-p-sampling", "logit-bias", "greedy-decoding"],
        "related_tools": [],
        "faq": [
            {"q": "Best temperature for chat?",
             "a": "0.7 is a common default. Lower (0.3-0.5) for support and factual tasks; higher (0.8-1.0) for casual conversation."},
            {"q": "What's T=0?",
             "a": "Greedy decoding — always pick the highest-logit token. Reproducible (with seed) but can produce repetitive output and miss creative moves."},
            {"q": "Temperature or top-p?",
             "a": "Both — they work together. T shapes the distribution; top-p truncates. Common chat settings: T=0.7, top-p=0.95."},
            {"q": "Is T affecting tool calling?",
             "a": "Use T=0 for tool calling — you want deterministic argument generation. Higher T introduces argument variations that break downstream parsing."}
        ]
    },
    # 2. nucleus-sampling
    {
        "slug": "nucleus-sampling",
        "title": "Nucleus Sampling",
        "category": "sampling",
        "difficulty_tier": "intermediate",
        "tldr": "Decoding strategy that sums probability mass top-down until reaching threshold p, sampling only from the smallest token set above that mass.",
        "plain_english": "Nucleus sampling — also called top-p sampling — picks the smallest set of tokens whose combined probability exceeds p (commonly 0.9 or 0.95). The model samples from this dynamic set instead of all tokens or a fixed top-k. The key advantage: the size of the sample pool adapts. When the model is confident (one token has 95% mass), the pool stays tiny. When uncertain (many similar-likelihood tokens), the pool grows to include the diverse alternatives.",
        "how_it_works": "Sort tokens by descending probability. Walk down the list, accumulating probability mass. Stop when cumulative mass exceeds p. Renormalise the kept tokens and sample. The 'nucleus' refers to this top portion of the probability distribution. Holtzman et al. 2019 introduced it as a fix for repetition issues in greedy/beam search and bland output in pure top-k. Nearly all chat APIs expose top_p as a parameter.",
        "why_it_matters": "Nucleus sampling produces more natural, varied output than fixed top-k. For chat, creative writing, and general generation, it's the de facto standard. The adaptiveness — large pool when needed, narrow when confident — produces output that's coherent without being repetitive. Combined with temperature, it gives fine-grained control over generation behaviour.",
        "example": "A storytelling app uses top_p=0.95 plus T=0.9. When the story reaches a clear next word ('he opened the'), the nucleus is small — likely something like 'door' or 'window'. When the story reaches a creative crossroads ('she felt'), the nucleus expands — many emotion words have similar probability. Output adapts naturally.",
        "pitfalls": [
            "Very low p (0.5-0.7) reduces diversity to near-greedy; too high (0.99) lets in low-probability noise.",
            "Streaming compatibility: top-p needs full distribution access; not a problem in modern stacks but matters for some custom decoders.",
            "Repetition: top-p alone doesn't prevent loops; pair with repetition penalty if needed.",
            "Floating-point ordering: identical p and seeds across runs can give different outputs due to precision; use seed + deterministic kernels for reproducibility."
        ],
        "when_use": "Use top-p as the main alternative or complement to temperature for chat, creative, and general-purpose generation.",
        "when_avoid": "Don't combine top-p with too-low T (output collapses) or too-high T (defeats truncation purpose); calibrate together.",
        "related_terms": ["top-p-sampling", "top-k-sampling", "temperature-sampling", "min-p-sampling", "typical-sampling", "greedy-decoding"],
        "related_tools": [],
        "faq": [
            {"q": "Top-p or top-k?",
             "a": "Top-p adapts to distribution shape; top-k uses a fixed pool size. Top-p is generally preferred for natural text. Some pipelines combine both."},
            {"q": "Recommended top_p?",
             "a": "0.9-0.95 is standard. Higher allows more diversity; lower restricts output to high-confidence tokens."},
            {"q": "Does top-p affect determinism?",
             "a": "At T=0 (greedy), top-p has no effect. At higher T, top-p with the same seed should reproduce — modulo numerical-precision quirks."},
            {"q": "Same as nucleus sampling?",
             "a": "Yes — 'nucleus sampling' was the original name (Holtzman 2019); 'top-p' is the API parameter name. Identical concept."}
        ]
    },
    # 3. min-new-tokens
    {
        "slug": "min-new-tokens",
        "title": "Min New Tokens",
        "category": "sampling",
        "difficulty_tier": "beginner",
        "tldr": "Generation parameter that forces the model to emit at least N tokens before allowing the end-of-sequence token, preventing premature stopping.",
        "plain_english": "Some prompts cause the model to stop too early — emitting EOS after just a few tokens. min-new-tokens prevents this by suppressing the EOS token until at least N new tokens have been generated. Useful when you need substantive responses (summaries, explanations) and want a hard floor on length. Works alongside max-new-tokens, which sets the ceiling.",
        "how_it_works": "During decoding, track tokens generated. If tokens-generated < min_new_tokens, set the logit for EOS (and possibly stop sequences) to -infinity, forcing the model to pick a non-stopping token. Once min_new_tokens is reached, EOS becomes available. Implemented as a logit warping step before softmax in most inference servers. Cheap to apply; useful when prompts produce inconsistent lengths.",
        "why_it_matters": "When a model repeatedly produces too-short outputs, min-new-tokens is a quick fix. For pipelines requiring minimum length (summaries that need to be ≥100 tokens, explanations that need at least a paragraph), it provides a hard guarantee without prompt engineering. Avoid it as a quality fix though — too-short output usually signals a deeper prompt or model issue.",
        "example": "A summarisation pipeline finds that 15% of summaries truncate after 20 tokens (model decided the input was too short to summarise). The team sets min_new_tokens=80. Now every summary has substance; the model elaborates rather than terminating early. Quality on long inputs unchanged; short inputs get fuller summaries.",
        "pitfalls": [
            "Forced length doesn't equal quality: models forced past their natural stopping point can produce filler text or hallucinate.",
            "Combined with stop sequences: min_new_tokens may suppress stop sequences too; verify behaviour for your stack.",
            "Prompt-engineering substitute: better prompts often solve too-short outputs without forcing length.",
            "Reasoning traces: in reasoning models, min_new_tokens applied to the answer separately from thinking tokens is provider-specific."
        ],
        "when_use": "Use to enforce minimum output length when the model's natural stopping is unreliably short.",
        "when_avoid": "Avoid as a quality lever — it produces fluff. Fix prompts or change models if outputs are short for the wrong reasons.",
        "related_terms": ["stop-sequence", "token-budget", "logit-bias", "temperature-sampling", "thinking-budget", "greedy-decoding"],
        "related_tools": ["vllm"],
        "faq": [
            {"q": "How do I pick min_new_tokens?",
             "a": "Match the floor of expected response length. For summaries: 80-150. For explanations: 100-300. Set based on what 'too short' means in your task."},
            {"q": "Does it work with stop sequences?",
             "a": "Most inference servers suppress stop sequences too while min_new_tokens is in effect. Verify with your specific stack."},
            {"q": "Token-cost implications?",
             "a": "Forcing min length increases output tokens consumed. Budget for the floor, not the average."},
            {"q": "Better than 'be detailed' in prompt?",
             "a": "Hard guarantee where prompt engineering is suggestion. Use when reliability matters; use prompts for nuance."}
        ]
    },
    # 4. beam-width
    {
        "slug": "beam-width",
        "title": "Beam Width",
        "category": "sampling",
        "difficulty_tier": "intermediate",
        "tldr": "Beam search hyperparameter controlling how many candidate sequences are kept at each decoding step; larger widths trade compute for higher-likelihood output.",
        "plain_english": "Beam search keeps the top-N sequences at each generation step instead of committing to one. Beam width is N. Width=1 is greedy. Width=4-8 is typical for translation and structured output. Higher width finds higher-likelihood completions but costs more compute and risks finding short, repetitive outputs that score high but aren't useful. Modern chat uses sampling instead of beam search; beam width matters mainly for translation, code completion, and domains where structured optimum-finding helps.",
        "how_it_works": "At each step, expand each of N current beams to all possible next tokens, score, keep the top-N by total log-likelihood. Repeat until all beams hit EOS or max length. Length-penalty adjusts scores to prevent short-bias. Diverse beam search adds penalties between beams to prevent collapse. Beam width is the trade-off knob: larger covers more search space at higher compute. For language generation, beam search has fallen out of favour for nucleus sampling; for translation it remains standard.",
        "why_it_matters": "Beam search is the canonical structured-decoding strategy for tasks with a clear 'best' answer (translation, transcription, code). Beam width tuning balances quality against compute. For chat and creative generation, beam search produces stilted output (always picks the most-likely tokens), which is why temperature/nucleus dominate there. Knowing beam width helps reason about decoding trade-offs.",
        "example": "A machine-translation system uses beam_width=5 with length penalty α=0.6. Larger beams beyond 5 don't improve BLEU measurably and double compute. The team standardises on width=5 for production. For latency-critical use cases they fall back to greedy (width=1).",
        "pitfalls": [
            "Beam-search degeneracy: large widths in language modelling often produce repetitive, generic outputs ('the the the').",
            "Length bias: longer sequences accumulate more log-likelihood; without length penalty, short outputs dominate.",
            "Diversity loss: all N beams converge to similar content; diverse beam search adds inter-beam penalties.",
            "Compute scaling: each step does N × |vocab| candidate evaluations; large widths get expensive."
        ],
        "when_use": "Use beam search with width 4-8 for translation, transcription, code completion, structured generation where finding the highest-likelihood completion matters.",
        "when_avoid": "Avoid beam search for chat and creative writing — sampling produces better output. Avoid wide beams for free-form generation (degeneracy).",
        "related_terms": ["beam-search", "greedy-decoding", "temperature-sampling", "nucleus-sampling", "top-k-sampling", "self-consistency"],
        "related_tools": [],
        "faq": [
            {"q": "Standard beam width?",
             "a": "5 for translation, 1-3 for code completion, 4-6 for transcription. Sweep on validation if quality matters."},
            {"q": "Beam search for chat?",
             "a": "Generally no — produces too-generic output. Use sampling. Beam search shines on tasks with deterministic-ish best answers."},
            {"q": "Diverse beam search?",
             "a": "Variant that adds penalties between beams to keep them different. Useful when you want N varied alternatives, not the top-N near-identical ones."},
            {"q": "Length penalty?",
             "a": "Score is divided by length^α. α=0.6-1.0 is typical; corrects for bias toward short sequences in beam search."}
        ]
    },
    # 5. stop-sequence
    {
        "slug": "stop-sequence",
        "title": "Stop Sequence",
        "category": "sampling",
        "difficulty_tier": "beginner",
        "tldr": "Inference parameter specifying strings that should terminate generation when emitted, preventing the model from continuing past a useful endpoint.",
        "plain_english": "When you ask a model to fill a template, you often want it to stop generating once it reaches a specific marker — like '\\n\\nUser:' (so it doesn't roleplay both sides) or '```' (to end a code block). Stop sequences let you specify these termination markers. The model generates until one matches, then stops. Cheap, reliable way to enforce structural boundaries on output.",
        "how_it_works": "Provide a list of stop strings to the API. The inference server monitors generated tokens and matches against stop sequences after each token. When a match is detected, the response truncates (typically excluding the stop string itself). Multiple stop sequences can match independently. Most providers support 4 stop sequences per request as a typical max.",
        "why_it_matters": "Stop sequences enforce structural correctness in scaffolded prompts and tool-calling formats. Without them, models often continue generating past the useful response — adding spurious commentary, hallucinating user follow-ups, or running until max-tokens. They're the simplest way to make output bounds reliable.",
        "example": "A team builds a Q&A system with prompts like 'Q: ... A: ...'. They set stop=['\\nQ:'] so the model can't generate the next question itself. Without the stop sequence, models occasionally produced 'A: blah\\nQ: random follow-up' which broke downstream parsing. Adding it eliminates the issue.",
        "pitfalls": [
            "Tokenization quirks: some stop strings tokenise differently than expected; verify with the model's tokenizer.",
            "Streaming display: stop sequences may include partial tokens; flush carefully to avoid display artefacts.",
            "Greedy match: if multiple stops are possible, the first matched wins — may not always be intended.",
            "Multi-token stops: only stops that align to token boundaries reliably trigger; sub-token stops can be unreliable."
        ],
        "when_use": "Use whenever you need bounded output: scaffolded prompts, tool-call formats, code blocks, structured templates.",
        "when_avoid": "Avoid in free-form chat where natural model termination is preferable.",
        "related_terms": ["logit-bias", "min-new-tokens", "token-budget", "tool-use-format", "json-mode", "temperature-sampling"],
        "related_tools": [],
        "faq": [
            {"q": "How many stops can I set?",
             "a": "Typically 4 per request across major APIs. Pick the most-likely first."},
            {"q": "Will the stop string appear in output?",
             "a": "Usually no — providers truncate before the stop. Some include a trailing fragment; check provider docs."},
            {"q": "Stop sequence vs EOS token?",
             "a": "EOS is the model's natural end-token. Stop sequences are user-specified termination strings. Both can trigger termination independently."},
            {"q": "Can I use regex?",
             "a": "Most providers don't support regex in stop sequences. Use exact strings; multiple stops cover variations."}
        ]
    },
    # 6. query-routing
    {
        "slug": "query-routing",
        "title": "Query Routing",
        "category": "rag-internals",
        "difficulty_tier": "intermediate",
        "tldr": "Pattern where an upstream classifier or LLM directs each query to the most appropriate downstream pipeline — RAG, model, agent, or tool — based on intent or content.",
        "plain_english": "Not every query needs the same treatment. A factual question might use RAG; a math problem might use a reasoning model; small talk goes to a cheap chat model. Query routing classifies the incoming query and dispatches to the right pipeline. The result: better quality, lower cost, and faster responses because each query uses the optimal path.",
        "how_it_works": "An incoming query passes through a router — a small classifier, a fast LLM, or rule-based logic — that outputs a route label (e.g. 'support', 'sales', 'research'). The system then dispatches to the corresponding pipeline. Routers can be trained on labelled query → route data, prompted with route descriptions, or use embedding similarity against route exemplars. Often combined with adaptive RAG (route by query complexity) and tool routing (route to agents with different tool registries).",
        "why_it_matters": "Single-pipeline systems waste resources on simple queries and underserve complex ones. Query routing lets you serve a portfolio: cheap path for chitchat, expensive path for hard reasoning, specialty path for sensitive data. Total cost drops; quality on the tail rises. For production deployments with mixed traffic, routing is a major lever.",
        "example": "A B2B support assistant routes incoming queries: greeting/chitchat → cheap chat (15% of traffic), product question → RAG over docs (60%), billing → CRM-tool agent (15%), escalation → human handoff (10%). Average per-query cost drops 70% vs. always-using-RAG, while quality on each segment matches a dedicated specialty system.",
        "pitfalls": [
            "Router miscalibration: wrong routes degrade quality on the misrouted segment; calibrate against labelled traffic.",
            "Latency: extra hop adds 50-200ms; budget against UX SLAs.",
            "Drift: traffic patterns shift; retrain or refresh routes periodically.",
            "Cold start: edge categories with little training data route poorly; default-route conservative for those."
        ],
        "when_use": "Use for production systems with mixed query types and meaningful traffic where heterogeneous treatment justifies routing complexity.",
        "when_avoid": "Avoid for narrow homogeneous workloads where one pipeline suffices.",
        "related_terms": ["adaptive-rag", "tool-router", "model-routing", "load-balancer-llm", "agentic-rag", "rag"],
        "related_tools": [],
        "faq": [
            {"q": "Classifier or LLM router?",
             "a": "Classifier for established routes (cheap, fast). LLM router for complex or evolving routing logic (more flexible). Many systems combine."},
            {"q": "How many routes typical?",
             "a": "3-10 in most production. Beyond that, routing accuracy drops; use hierarchical routing or multi-stage classification."},
            {"q": "Router training data?",
             "a": "Labelled (query, route) pairs. Start with a few hundred manually labelled; grow as traffic accumulates."},
            {"q": "Combine with adaptive RAG?",
             "a": "Yes — route to RAG path, then within RAG decide single-pass vs multi-step. Compositional routing layers."}
        ]
    },
    # 7. retrieval-grader
    {
        "slug": "retrieval-grader",
        "title": "Retrieval Grader",
        "category": "rag-internals",
        "difficulty_tier": "intermediate",
        "tldr": "LLM-driven module that assesses whether retrieved passages are relevant to a query, filtering or escalating before generation.",
        "plain_english": "Retrieval doesn't always return useful results — semantic similarity can match topics that aren't actually relevant. A retrieval grader (small LLM or fine-tuned classifier) reads each retrieved passage with the query and labels it 'relevant' or 'not relevant'. Irrelevant passages are dropped or trigger fallback strategies (web search, refusal, agentic search). Result: cleaner context for generation, fewer hallucinations grounded in unrelated text.",
        "how_it_works": "After retrieval, each top-k passage is sent to a grader with a prompt like 'Does this passage answer the query? Output yes/no plus a brief reason.' The grader (often a smaller fast model or fine-tuned classifier) returns a label. Passages graded relevant are used; irrelevant ones are dropped. If too few remain, the system falls back — query rewriting, web search, or refusal. CRAG and similar pipelines use this pattern explicitly.",
        "why_it_matters": "RAG quality is bottlenecked by retrieval. Adding a grader improves answer faithfulness because the LLM only sees passages that actually help. The cost is one extra LLM call per passage but smaller models suffice. For production RAG where wrong answers carry real cost, graders are increasingly standard.",
        "example": "A docs-RAG team adds a small fine-tuned grader. Retrieval returns top-10 passages; grader keeps 3-5 on average. End-to-end answer faithfulness rises 12 points; hallucinations attributable to irrelevant context drop substantially. Per-query cost rises modestly; quality wins justify it.",
        "pitfalls": [
            "Grader miscalibration: too strict drops good passages; too lenient defeats the purpose. Tune on labelled set.",
            "Cost: per-passage grading adds compute; cap k or use cheap graders.",
            "Latency: extra hop per query; use parallel grading or fast models.",
            "Grader-LLM mismatch: grader's relevance judgments may not match what the generator needs; co-tune on end-to-end quality."
        ],
        "when_use": "Use for RAG where retrieval recall is high but precision is mixed, especially in regulated or quality-critical domains.",
        "when_avoid": "Avoid when retrieval is already at-ceiling quality, when latency budget can't absorb grading, or when corpus is small enough to consume directly.",
        "related_terms": ["corrective-rag", "rag", "retrieval", "document-grading", "reranking", "query-rewriting"],
        "related_tools": [],
        "faq": [
            {"q": "Grader vs reranker?",
             "a": "Grader is binary (relevant/not); reranker outputs continuous scores. Both filter irrelevant content; graders are simpler and easier to fine-tune."},
            {"q": "What model size for grader?",
             "a": "Small fine-tuned (T5-small, BERT-base) or fast LLMs (Haiku, GPT-4o-mini). Bigger doesn't help much for binary relevance."},
            {"q": "Can I use the same model as generator?",
             "a": "Yes for prototyping. For production, separate grader is cheaper and more reliable per dollar."},
            {"q": "Grader fails — what now?",
             "a": "Fallback strategies: query rewriting, web search, refusal-with-explanation. Without fallback, low-relevance retrievals still feed generation."}
        ]
    },
    # 8. query-decomposition
    {
        "slug": "query-decomposition",
        "title": "Query Decomposition",
        "category": "rag-internals",
        "difficulty_tier": "intermediate",
        "tldr": "Breaking a complex multi-part question into smaller sub-questions, retrieving for each, then synthesising answers — improving recall on compositional queries.",
        "plain_english": "Compound questions like 'compare the pricing of plans X, Y, Z' are hard for single-shot retrieval. Query decomposition splits them: retrieve about plan X, plan Y, plan Z separately, then have the LLM synthesise the comparison. Each sub-query gets focused, high-relevance retrieval; the synthesis combines them. This pattern handles questions that single-shot RAG fundamentally can't answer.",
        "how_it_works": "An LLM decomposer takes the user query and outputs N sub-queries. The retriever runs on each sub-query, gathering passages per sub-query. A synthesis LLM call combines the per-sub-query passages into a final answer. Common in agentic RAG and explicit decomposition pipelines (DSPy, LangChain). Decomposition can be flat (one round of N sub-queries) or recursive (sub-queries themselves get decomposed further).",
        "why_it_matters": "Single-shot RAG fails on compositional queries — questions that require evidence from multiple distinct topics. Decomposition unlocks them at the cost of more LLM calls per query. For research, comparison, multi-fact synthesis, and any question that mixes multiple sub-topics, decomposition is often the decisive technique.",
        "example": "A user asks 'compare cancellation policies of Netflix, Disney+, and Apple TV.' Single retrieval mixes all three; the LLM produces a confused answer. With decomposition: 3 sub-queries (one per service), 3 retrieval passes, 1 synthesis call. Each retrieval returns the right policy; synthesis produces a clean comparison table. Quality dramatically better; cost ~4× single-shot.",
        "pitfalls": [
            "Over-decomposition: simple queries get split unnecessarily, adding cost without benefit.",
            "Under-decomposition: complex queries get split too coarsely, missing useful structure.",
            "Synthesis errors: the synthesizer may misalign sub-query results, especially for contradictory evidence.",
            "Cost: N+1 LLM calls per query; budget per use case."
        ],
        "when_use": "Use for compositional questions, comparisons, multi-fact synthesis, and any query where single-shot retrieval clearly under-performs.",
        "when_avoid": "Avoid for simple single-topic queries, latency-critical paths, or budget-constrained workloads where the cost multiplier doesn't justify quality gains.",
        "related_terms": ["agentic-rag", "task-decomposition", "rag", "retrieval", "multi-hop-retrieval", "query-rewriting"],
        "related_tools": ["langgraph", "llamaindex"],
        "faq": [
            {"q": "How many sub-queries?",
             "a": "2-5 covers most decomposable questions. Beyond that, compute and synthesis complexity climb fast."},
            {"q": "When does single-shot suffice?",
             "a": "Single-topic factual queries, well-formulated questions, and small focused corpora — single retrieval often works."},
            {"q": "Can the model decompose itself?",
             "a": "Yes — most modern implementations use an LLM call for decomposition. Smaller fast models often suffice for the decomposer step."},
            {"q": "Combine with reranking?",
             "a": "Yes — decompose, retrieve per sub-query, rerank within each, synthesise. Multi-stage RAG with high quality."}
        ]
    },
    # 9. multi-hop-retrieval
    {
        "slug": "multi-hop-retrieval",
        "title": "Multi-Hop Retrieval",
        "category": "rag-internals",
        "difficulty_tier": "intermediate",
        "tldr": "Iterative retrieval pattern where information from one round is used to formulate the next, enabling answers that require chaining multiple facts.",
        "plain_english": "Some questions need information that builds on itself. 'Who is the CEO of the company that makes the AI tool used most by Fortune 500 companies?' First find the most-used tool, then find its company, then find the CEO. Multi-hop retrieval explicitly chains: retrieve to get partial info, use that to formulate the next retrieval, repeat. Each hop narrows the answer.",
        "how_it_works": "An agent (or scripted pipeline) iterates: retrieve for the current sub-question, extract partial answer, formulate next sub-question using the result, retrieve again. Continue until the original question is answerable. Stopping rules: answer found, max hops reached, no new info per hop. Multi-hop QA benchmarks (HotpotQA, 2WikiMultiHopQA) test this capability. Modern implementations layer agents over RAG to handle iterative retrieval.",
        "why_it_matters": "Static single-shot RAG can't answer questions requiring chained inference across documents. Multi-hop unlocks compositional fact retrieval — graph-structured questions, transitive relations, lookup-then-lookup patterns. For research, knowledge-base QA, and complex factual queries, it's the difference between feasible and not.",
        "example": "A research assistant gets 'When did the founder of the company behind PostgreSQL graduate?' Hop 1: retrieve PostgreSQL → founders. Hop 2: retrieve founder bio → graduation year. Final answer ties them together. Single-shot retrieval would return either fact but rarely both with linkage; multi-hop chains them.",
        "pitfalls": [
            "Error propagation: a wrong hop poisons subsequent ones; verify intermediate results.",
            "Hop budget: capped iterations may cut off legitimate complex questions; tune.",
            "Cost: each hop is retrieval + LLM; multi-hop budgets several × single-shot.",
            "Diminishing returns: most queries don't need >2 hops; routing simple ones avoids overuse."
        ],
        "when_use": "Use for factual multi-step questions: graph-walking, transitive lookups, compositional research queries.",
        "when_avoid": "Avoid for simple lookups, summarisation, or open-ended generation where multi-hop overhead doesn't pay off.",
        "related_terms": ["agentic-rag", "query-decomposition", "rag", "retrieval", "react", "reflexion"],
        "related_tools": ["langgraph"],
        "faq": [
            {"q": "How many hops typically?",
             "a": "1-3 hops handle most multi-hop questions. Cap at 5 to prevent runaway."},
            {"q": "Multi-hop or decomposition?",
             "a": "Decomposition is parallel (independent sub-queries); multi-hop is sequential (each depends on prior). Different patterns for different questions."},
            {"q": "Does it work for unstructured text?",
             "a": "Yes — most multi-hop QA benchmarks use unstructured text. Knowledge graphs help but aren't required."},
            {"q": "Need a reasoning model?",
             "a": "Reasoning models do better at planning the next hop. Chat models work with explicit prompting (ReAct-style)."}
        ]
    },
    # 10. noise-augmented-rag
    {
        "slug": "noise-augmented-rag",
        "title": "Noise-Augmented RAG",
        "category": "rag-internals",
        "difficulty_tier": "advanced",
        "tldr": "RAG training technique that adds irrelevant or distracting passages to retrieved context during fine-tuning, teaching the model to filter noise robustly.",
        "plain_english": "RAG models are usually trained with clean, relevant retrieval results. In production, retrieval includes noise — irrelevant passages that share keywords. Noise-augmented training adds this noise during fine-tuning: include 1-3 distractor passages alongside relevant ones, with the model trained to ignore noise. Result: a model robust to imperfect retrieval, less likely to confidently cite irrelevant content.",
        "how_it_works": "Build a fine-tuning dataset where each example's context includes both relevant passages and deliberately added irrelevant ones (random, topical-but-wrong, adversarial). Labels the model on producing the correct answer despite the noise. Training teaches the model to recognise and ignore distractors. RAFT (Retrieval-Augmented Fine-Tuning) by Microsoft and similar techniques operationalize this. Variants vary noise ratio and distractor selection strategy.",
        "why_it_matters": "Production retrieval is noisy. Models trained only on clean context confidently cite distractor passages and hallucinate. Noise-augmented training produces models that work better with real retrievers — they grade context implicitly, ignoring noise rather than synthesising from it. For deployment over imperfect indexes, this technique gives meaningful quality lift.",
        "example": "A team fine-tunes a 7B model on RAG examples mixing 1 correct + 2 distractor passages. Compared to clean-only training, the resulting model maintains accuracy when retrieval includes 2-3 distractors per query. End-to-end production accuracy with the team's actual retriever rises 8 points.",
        "pitfalls": [
            "Wrong distractor type: random noise teaches different robustness than topical-wrong distractors; use realistic noise.",
            "Noise ratio: too clean teaches nothing; too noisy degrades signal. 30-50% relevant, rest noise is a common balance.",
            "Distribution shift: model trained on one noise distribution may underperform on others.",
            "Compute: more context per example costs more training compute."
        ],
        "when_use": "Use when fine-tuning RAG-specific models for deployment over imperfect retrievers. Especially valuable for production systems with measured retrieval-noise rates.",
        "when_avoid": "Avoid for clean-corpus deployments where retrieval is reliable, or when fine-tuning isn't an option.",
        "related_terms": ["rag", "fine-tuning", "retrieval", "retrieval-grader", "corrective-rag", "adversarial-robustness"],
        "related_tools": [],
        "faq": [
            {"q": "What's RAFT?",
             "a": "Retrieval-Augmented Fine-Tuning — Microsoft's specific recipe for noise-augmented RAG training. Includes both clean and noisy examples; specific noise ratios."},
            {"q": "Can I use it without fine-tuning?",
             "a": "Inference-time effects are limited. Real benefits come from training the model to handle noise; runtime prompting only goes so far."},
            {"q": "Distractor selection?",
             "a": "Best from same retriever the model will see in production — surfaces realistic noise. Random distractors teach generic robustness."},
            {"q": "How much noise?",
             "a": "30-50% irrelevant context per training example is a common balance. Sweep on validation against your production noise levels."}
        ]
    },
    # 11. document-grading
    {
        "slug": "document-grading",
        "title": "Document Grading",
        "category": "rag-internals",
        "difficulty_tier": "intermediate",
        "tldr": "Scoring full documents for relevance to a query (vs. passage-level grading), used as a coarse first filter before chunk-level retrieval and reranking.",
        "plain_english": "Before searching individual chunks, you can score whole documents for relevance — does this whole doc seem related to the query? Document grading filters to a smaller candidate set before expensive chunk-level processing. Useful when corpora are large and many docs are clearly off-topic. Combine with chunk retrieval for two-stage scoping: relevant docs first, relevant chunks within them second.",
        "how_it_works": "Each document gets a relevance score for each query. Score sources: document-level embedding similarity, BM25 over the full doc, document metadata match, or a small classifier scoring (query, document_summary). Top-K documents proceed to chunk-level retrieval; rest are filtered out. Hierarchical RAG architectures explicitly use this two-stage approach. Document scoring is faster and cheaper than scoring all chunks across the corpus.",
        "why_it_matters": "For large corpora (millions of documents), exhaustive chunk retrieval is expensive. Document grading reduces the search space dramatically — score 1M docs, keep top 100, then chunk-search just those. Combined with metadata pre-filtering, the candidate set shrinks several orders of magnitude before chunk-level work begins. Practical for enterprise RAG.",
        "example": "A legal-research RAG indexes 50M case documents (each 100+ chunks). Searching all chunks per query is infeasible. Document grader scores docs by query similarity, keeps top 200 docs (~20K chunks). Chunk retrieval and reranking proceed within these. Total candidates per query drop 99.6%; latency stays under 200ms.",
        "pitfalls": [
            "Coarse filtering: docs whose relevant chunk lives among irrelevant content may be filtered out incorrectly; combine with chunk-level fallback.",
            "Score aggregation: how to score a document made of many chunks? Mean, max, top-K average — each has trade-offs.",
            "Cost-quality tension: aggressive document filtering loses recall; calibrate with your eval set.",
            "Document-length bias: short docs score differently than long ones; normalise carefully."
        ],
        "when_use": "Use for large-corpus RAG (>100K documents) where exhaustive chunk search is too expensive, especially with hierarchical retrieval architectures.",
        "when_avoid": "Avoid for small corpora where chunk-level search is fast enough; the extra stage adds complexity without payoff.",
        "related_terms": ["rag", "retrieval", "metadata-prefiltering", "retrieval-grader", "parent-child-rag", "cluster-retrieval"],
        "related_tools": [],
        "faq": [
            {"q": "Document grading or chunk retrieval?",
             "a": "Both — document for coarse filter, chunk for precise match. Two-stage retrieval handles large corpora at acceptable cost."},
            {"q": "How to score document-level relevance?",
             "a": "Embedding similarity on document summary, BM25 over full text, or aggregate of chunk scores (max/mean). Sweep against eval."},
            {"q": "How aggressive can the filter be?",
             "a": "Tune by recall@k on a held-out eval. Filtering 99% of corpus is achievable when coarse signal is strong (clear topic match)."},
            {"q": "Combine with metadata prefiltering?",
             "a": "Yes — metadata first (hard filter), then document grading (soft filter), then chunk retrieval. Three-stage scoping."}
        ]
    },
    # 12. rag-evaluation
    {
        "slug": "rag-evaluation",
        "title": "RAG Evaluation",
        "category": "rag-internals",
        "difficulty_tier": "intermediate",
        "tldr": "Practice of measuring RAG-specific quality dimensions: retrieval recall, context relevance, answer faithfulness, and end-to-end correctness.",
        "plain_english": "RAG has more failure modes than vanilla LLMs — wrong retrieval, irrelevant context, hallucinated synthesis. RAG evaluation breaks down quality into measurable components: did retrieval find the right docs (recall)? Are the retrieved passages relevant (precision)? Does the answer use the passages faithfully (faithfulness)? Is the final answer correct (accuracy)? Frameworks like RAGAS, TruLens, Phoenix, and DeepEval automate these checks.",
        "how_it_works": "Build a labelled eval set — ideally (query, correct_answer, list_of_correct_documents). For each query, run RAG and measure: recall@k (did retrieval find the labelled correct docs?), context relevance (judge model rates retrieved passages 1-5), faithfulness (does the answer cite actually-supporting passages?), and answer correctness (vs. labelled). Aggregate per-metric scores. Common frameworks ship pre-built scorers; teams add domain-specific metrics. Run on every model/prompt change.",
        "why_it_matters": "RAG quality depends on multiple stages — measuring just the final answer hides where things break. Component-level evaluation tells you whether retrieval, context relevance, or synthesis is the bottleneck, so you can prioritise improvements. Without it, RAG tuning becomes guesswork.",
        "example": "A team's RAG accuracy stalls at 65%. Component eval reveals: retrieval recall is 78% (rooms to improve), context relevance is 82%, faithfulness is 91%, answer correctness given correct context is 88%. Conclusion: improving retrieval is the highest-leverage fix. They invest in better embeddings; recall climbs to 89% and end-to-end accuracy to 78%.",
        "pitfalls": [
            "Labelled eval data: building gold-standard (query, doc, answer) labels takes effort; undersampled evals are noisy.",
            "Judge bias: faithfulness and relevance judges have biases; calibrate against humans.",
            "Domain drift: evals built on training-time corpora may not predict production traffic quality.",
            "Single metric optics: aggregate scores hide component issues; report per-stage."
        ],
        "when_use": "Use as standard practice for any production RAG. Run before major changes, periodically against drift, and after each component swap.",
        "when_avoid": "Don't skip eval for prototypes that ship — RAG without measurement degrades silently.",
        "related_terms": ["rag", "evaluation-set", "faithfulness", "retrieval-grader", "g-eval", "deepeval"],
        "related_tools": ["promptfoo", "deepeval"],
        "faq": [
            {"q": "Best framework for RAG eval?",
             "a": "RAGAS for component scores, DeepEval for end-to-end, TruLens for tracing + eval. Pick by integration; many teams use multiple."},
            {"q": "How big an eval set?",
             "a": "Start with 50-100 labelled queries; grow as you discover failure modes. Beyond ~500, returns diminish unless stratified."},
            {"q": "Evaluate against gold answers or judge?",
             "a": "Gold answers (exact-match or fuzzy) are most reliable. Judge models supplement when gold answers aren't available, with calibration."},
            {"q": "Production traffic eval?",
             "a": "Sample live queries, score with judge models, alert on drift. Complements offline eval set against shifting traffic."}
        ]
    },
    # 13. long-context-rag
    {
        "slug": "long-context-rag",
        "title": "Long-Context RAG",
        "category": "rag-internals",
        "difficulty_tier": "intermediate",
        "tldr": "RAG architecture variants designed to operate effectively over very long retrieved contexts (50K+ tokens), addressing attention dilution and lost-in-the-middle issues.",
        "plain_english": "Modern LLMs accept 100K+ token contexts. Long-context RAG retrieves dozens or hundreds of passages instead of just a few, leveraging the larger context window. The catch: more context doesn't always mean better answers — models miss information buried in the middle ('lost in the middle'), and attention dilutes across many passages. Long-context RAG techniques address these issues with structuring, ordering, and hierarchical synthesis.",
        "how_it_works": "Three patterns. (1) Pack-and-pray: retrieve many passages, concatenate, hope for the best — works but loses recall on middle content. (2) Re-ranked ordering: place most-relevant passages at start and end (model's high-attention zones). (3) Hierarchical: chunk-level retrieval feeds doc-level summarisation, then synthesis over the summaries. Modern systems combine: retrieve more, rerank for ordering, structure with delimiters or summaries.",
        "why_it_matters": "Long-context windows opened up new RAG architectures, but naive use leaves quality on the table. Long-context RAG techniques recover that quality. For technical Q&A, multi-document synthesis, and complex research queries, leveraging the full window with proper structuring outperforms classic short-context RAG.",
        "example": "A research assistant retrieves 50 passages per query, packs into 80K-token context. Pack-and-pray accuracy: 71%. Re-ordered (top by reranker first/last, middle truncated to summaries): 79%. Hierarchical (per-doc summaries → final synthesis): 82%. The team adopts hierarchical for high-value queries.",
        "pitfalls": [
            "Cost: long-context inference is expensive; budget per query tier.",
            "Lost in the middle: bury critical info at the middle of long context, model misses it; reorder for attention.",
            "Latency: 80K-token prompts process slower; budget accordingly or stream prefill.",
            "Diminishing returns: beyond a corpus-specific threshold, more context doesn't help; benchmark to find your sweet spot."
        ],
        "when_use": "Use when retrieval recall is high but per-passage relevance is mixed, or when synthesis benefits from broad context (research, multi-doc QA).",
        "when_avoid": "Avoid for narrow factual queries where short-context RAG suffices; the long-context cost rarely pays off.",
        "related_terms": ["rag", "context-window", "long-context-benchmark", "fid", "attention-sink", "kv-cache-compression"],
        "related_tools": [],
        "faq": [
            {"q": "Just dump everything into context?",
             "a": "Doesn't always work — attention dilutes. Order, structure, or hierarchically summarise for best results."},
            {"q": "How much context is too much?",
             "a": "Test on your task. Quality often plateaus or drops past 50-100K tokens depending on model."},
            {"q": "Combine with reranking?",
             "a": "Yes — rerank top-K for ordering even if you keep all of them. Best content at start/end."},
            {"q": "Hierarchical summarisation cost?",
             "a": "Multiple LLM calls (summary per doc + synthesis). Several × single-pass cost; reserve for high-value queries."}
        ]
    },
    # 14. warmup-schedule
    {
        "slug": "warmup-schedule",
        "title": "Warmup Schedule",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Learning-rate schedule that gradually increases the LR from a small value to its peak over the first N steps, stabilising training before main learning begins.",
        "plain_english": "Starting training at full learning rate often causes instability — gradients are wild early on, big steps push weights into bad regions. Warmup ramps up the LR slowly: maybe 0.0 → peak over the first 1-2% of training steps. By the time real learning starts, the optimizer state has stabilised. Most modern LLM training recipes use linear or cosine warmup; it's the difference between converging and diverging on large training runs.",
        "how_it_works": "For warmup_steps W, scale the LR by min(1.0, current_step / W). At step 0, LR is 0; at step W, it's the full configured peak. After warmup, transition into the main schedule (cosine decay, linear decay, constant). Common warmup is 1-3% of total training steps for pretraining; ~100 steps for fine-tuning. Implemented as a learning-rate scheduler in PyTorch/JAX trainers.",
        "why_it_matters": "LLM pretraining at scale is brittle. Warmup is one of the cheapest stabilisation techniques — it has minimal effect on total training time but dramatically reduces divergence risk. Required for Adam-family optimizers in particular due to their dependence on running statistics that need accumulation. Skip warmup at your training-run's peril.",
        "example": "A team trains a 7B model for 1M steps. Without warmup, step 50 hits a NaN — gradients diverged. With 2000-step linear warmup, training proceeds smoothly. Final model quality is identical; warmup cost was negligible relative to the run.",
        "pitfalls": [
            "Too-short warmup: instability still possible; default to 1-3% of total steps.",
            "Too-long warmup: wastes early training time at low LR.",
            "Mismatch with optimizer: AdamW needs warmup more than SGD does; tune per optimizer.",
            "Distributed training: warmup affects effective LR across replicas — verify scaling."
        ],
        "when_use": "Use for any LLM pretraining or large fine-tuning run. Standard practice; not optional at scale.",
        "when_avoid": "Avoid only for tiny fine-tunes (few hundred steps) where warmup is negligible — use a constant low LR instead.",
        "related_terms": ["cosine-schedule", "adamw", "fine-tuning", "pretraining", "annealing-phase", "fsdp"],
        "related_tools": ["accelerate", "deepspeed"],
        "faq": [
            {"q": "How long should warmup be?",
             "a": "1-3% of total training steps for pretraining. ~100-500 steps for fine-tuning."},
            {"q": "Linear or cosine warmup?",
             "a": "Linear is most common and works well. Cosine warmup is rarer but smooths the transition more."},
            {"q": "Skip warmup for fine-tuning?",
             "a": "Risky. Even short fine-tunes benefit from a few hundred warmup steps; cheap insurance."},
            {"q": "Affects final quality?",
             "a": "Indirectly — by preventing divergence and stabilising early training. Final quality is similar with vs. without warmup if both runs converge."}
        ]
    },
    # 15. cosine-schedule
    {
        "slug": "cosine-schedule",
        "title": "Cosine Schedule",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Learning-rate schedule that decays the LR following a cosine curve from peak to a small minimum, used as the default for modern LLM pretraining.",
        "plain_english": "After warmup, the learning rate needs to decay — going slower as training progresses helps converge to a flat minimum. Cosine schedule decays following half a cosine curve: starts at peak, smoothly drops to ~10% of peak (or to zero) by the end. The smooth shape outperforms linear or step schedules empirically; nearly every modern LLM pretraining recipe uses cosine.",
        "how_it_works": "After warmup_steps, lr(t) = min_lr + (peak_lr - min_lr) × 0.5 × (1 + cos(π × (t - warmup) / (total - warmup))). At t=warmup, factor=1, lr=peak. At t=total, factor=0, lr=min. Smoothly interpolates following cosine. Variants: cosine with restarts (LR resets to peak periodically), cosine to constant after a fraction of total. PyTorch's CosineAnnealingLR and CosineAnnealingWarmRestarts implement these; HuggingFace transformers ships cosine schedulers as defaults.",
        "why_it_matters": "Cosine is the empirical winner for pretraining LR schedules. The smooth decay reaches better minima than abrupt step decay; the long high-LR plateau early on lets the model explore broadly. For pretraining especially, cosine produces meaningfully better final models than alternatives at the same compute. Knowing why and when to use cosine is part of training literacy.",
        "example": "A team trains a 13B model for 10M steps. Schedule: 200K warmup → cosine decay from 3e-4 to 3e-5 over the remaining 9.8M steps. The cosine curve reaches lower training loss than linear or step decays at the same compute; final eval scores 1.5 points higher.",
        "pitfalls": [
            "End point: decay-to-zero loses some final-stage learning; min_lr=10% of peak is a safer default.",
            "Total steps must be known: cosine needs to know the schedule length; restart strategies handle uncertain durations.",
            "Continued pretraining: when extending training, cosine has 'ended' and re-warming is needed; consider step-rewarming.",
            "Non-pretraining tasks: cosine may not be optimal for all fine-tunes; linear or constant sometimes better."
        ],
        "when_use": "Use as the default LR schedule for LLM pretraining and large fine-tuning runs.",
        "when_avoid": "Avoid for very short fine-tunes (constant LR is simpler) or when training duration isn't predetermined (use restart variants).",
        "related_terms": ["warmup-schedule", "adamw", "fine-tuning", "pretraining", "annealing-phase", "compute-optimal-scaling"],
        "related_tools": ["accelerate"],
        "faq": [
            {"q": "Min LR value?",
             "a": "10% of peak is common. Decay-to-zero is less common in modern recipes."},
            {"q": "Cosine or linear decay?",
             "a": "Cosine almost always for pretraining — empirically better. Linear or constant for short fine-tunes."},
            {"q": "Restarts?",
             "a": "Cosine with warm restarts periodically resets LR to peak. Useful for very long runs or when training plateaus; rarely used in pretraining."},
            {"q": "How does this interact with warmup?",
             "a": "Warmup → cosine decay sequentially. Warmup brings LR to peak; cosine takes it back down. Standard pattern."}
        ]
    },
    # 16. adamw
    {
        "slug": "adamw",
        "title": "AdamW",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Adam optimizer variant with decoupled weight decay, the default optimizer for LLM pretraining and fine-tuning since 2018.",
        "plain_english": "Adam combined momentum (smoothed gradients) with adaptive learning rates per parameter. Original Adam treated weight decay as part of the gradient, which interacted badly with adaptive learning. AdamW decouples weight decay — applies it directly to weights as a separate step, not folded into the gradient. The decoupling makes regularisation work as intended; AdamW outperforms Adam on most tasks. Today, virtually every LLM is trained with AdamW.",
        "how_it_works": "Each step: compute gradient g. Update first moment m = β₁m + (1-β₁)g (momentum). Update second moment v = β₂v + (1-β₂)g² (variance). Compute bias-corrected estimates. Update parameter: θ = θ - lr × m̂/(√v̂ + ε) - lr × wd × θ. The last term is weight decay applied directly. β₁=0.9, β₂=0.95 (or 0.999), wd=0.1, ε=1e-8 are common LLM defaults. Loshchilov & Hutter 2017 introduced AdamW; it became standard for transformer training.",
        "why_it_matters": "AdamW is the workhorse optimizer of modern deep learning. Knowing how it works helps tune training (learning rate, weight decay, β values) and diagnose convergence issues. Specific details (bias correction, decoupled decay) explain behaviours like training instability when β₂ is too low or generalisation gaps when weight decay is wrong.",
        "example": "A team training a 7B model uses AdamW with lr=3e-4, wd=0.1, β₁=0.9, β₂=0.95. They sweep wd: 0.01 underfits; 0.1 optimal; 0.5 hurts convergence. The optimizer's stable behaviour across hyperparameter ranges is a major reason AdamW dominates.",
        "pitfalls": [
            "β₂ too low: training instability when running variance estimate is noisy; default 0.95-0.99 for LLMs.",
            "Weight decay miscalibration: too high regularises away learning; too low loses generalisation; default 0.1 for LLMs.",
            "Bias correction with restarts: resuming training with optimizer state needs careful bias-correction handling.",
            "Memory cost: AdamW stores two extra tensors per parameter (m, v); 8B params + AdamW state ≈ 24B-equivalent memory."
        ],
        "when_use": "Use as the default optimizer for any LLM pretraining or fine-tuning. Almost-always the right choice.",
        "when_avoid": "Avoid only when reproducing legacy Adam-trained results exactly, or in research exploring optimizer alternatives (Shampoo, Lion).",
        "related_terms": ["fine-tuning", "warmup-schedule", "cosine-schedule", "fsdp", "mixed-precision", "fp8"],
        "related_tools": ["accelerate", "deepspeed"],
        "faq": [
            {"q": "AdamW vs Adam?",
             "a": "AdamW decouples weight decay; Adam folds it into the gradient. AdamW generalises better; modern training defaults to AdamW."},
            {"q": "Weight decay for LLMs?",
             "a": "0.1 is common for pretraining. Lower (0.01) for fine-tuning to preserve base capabilities. Sweep on validation."},
            {"q": "Memory cost?",
             "a": "Two extra tensors per parameter (m, v). With FP32 optimizer state, 8 bytes/param overhead. Mixed precision optimizer state lowers this."},
            {"q": "Newer optimizers?",
             "a": "Shampoo, Lion, Sophia have shown promise. AdamW remains default; alternatives are research-or-specialty."}
        ]
    },
    # 17. domain-adaptive-pretraining
    {
        "slug": "domain-adaptive-pretraining",
        "title": "Domain-Adaptive Pretraining",
        "category": "techniques",
        "difficulty_tier": "advanced",
        "tldr": "Continued pretraining on domain-specific corpus to specialise a base model — closely related to continued-pretraining but specifically targeting a narrow vocabulary and style.",
        "plain_english": "Domain-adaptive pretraining (DAPT) is a focused form of continued pretraining: take a base model and run it on tens-to-hundreds of billions of tokens from a single domain (legal, medical, code) to absorb that domain's vocabulary, conventions, and reasoning patterns. Output: a 'medical Llama' or 'legal Mistral' that beats general-purpose bases on domain-specific tasks. Pre-cursor to task fine-tuning.",
        "how_it_works": "Start from a strong general base. Curate a domain-specific corpus (legal cases, medical papers, codebases). Continue pretraining with next-token prediction, often at lower LR than original pretraining and mixed with 5-30% general data to preserve broad capabilities. Train for 1-3 epochs over the domain corpus. The result is a base model with shifted distribution — outputs sound more like the domain. Subsequent task fine-tuning then targets specific behaviours.",
        "why_it_matters": "Off-the-shelf bases underperform in domains with specialised vocabulary or conventions. DAPT closes the gap at moderate cost — typically 1-5% of original pretraining compute. For legal, medical, financial, or code applications, DAPT followed by task fine-tuning consistently beats fine-tuning alone. As open-source bases proliferate, DAPT is a high-leverage specialisation step.",
        "example": "A medical-AI startup takes Llama 3 8B and DAPT on 50B tokens of clinical notes and medical literature. The DAPTed model scores 8 points higher on medical Q&A vs. directly fine-tuning Llama 3 on the same task data. Total DAPT cost: ~$30K compute. Subsequent fine-tunes on clinical workflows benefit from the domain-shifted base.",
        "pitfalls": [
            "Catastrophic forgetting: aggressive DAPT erodes general capabilities; mix in general data and lower LR.",
            "Tokenizer mismatch: domain has terms tokenised inefficiently; consider vocabulary extension before DAPT.",
            "Data quality: noisy domain data produces a noisier model; curate aggressively.",
            "Compute: 50B-token DAPT runs aren't cheap; budget realistically."
        ],
        "when_use": "Use for narrow professional domains where vocabulary and conventions diverge from general internet text: legal, medical, finance, scientific, code.",
        "when_avoid": "Avoid when general bases handle the domain adequately, when no large unlabelled corpus exists, or when fine-tuning alone meets quality.",
        "related_terms": ["continued-pretraining", "fine-tuning", "data-mixture", "catastrophic-forgetting", "knowledge-distillation", "annealing-phase"],
        "related_tools": [],
        "faq": [
            {"q": "DAPT or fine-tuning?",
             "a": "DAPT for absorbing a domain. Fine-tuning for task behaviour. Use both: DAPT first, then task fine-tune."},
            {"q": "How much domain data?",
             "a": "10B tokens for noticeable effect; 50-100B for serious adaptation; 100B+ approaches near-from-scratch costs."},
            {"q": "Mix with general data?",
             "a": "Yes — 10-30% general data preserves broad capabilities. Pure-domain DAPT narrows the model dangerously."},
            {"q": "Same as continued pretraining?",
             "a": "DAPT is one specific instance of continued pretraining. CPT is broader (any continued unsupervised training); DAPT specifically targets domain shift."}
        ]
    },
    # 18. annealing-phase
    {
        "slug": "annealing-phase",
        "title": "Annealing Phase",
        "category": "techniques",
        "difficulty_tier": "advanced",
        "tldr": "Final stage of LLM pretraining where data quality is upgraded and learning rate is lowered, sharpening the model on high-quality examples.",
        "plain_english": "Modern LLM training often has phases: bulk pretraining on web-scale mixed-quality data, then an 'annealing' phase at the end on smaller-but-cleaner data with reduced learning rate. The annealing phase polishes the model — focuses on high-signal examples to sharpen capabilities and reduce noise from the bulk corpus. Llama 3 and similar production models attribute meaningful gains to careful annealing.",
        "how_it_works": "Train for most steps on the broad mixed corpus with cosine LR. In the last 10-30% of training, switch to a curated dataset of high-quality, often instruction-style data while continuing to lower LR. The model overfits less on web noise and absorbs proportionally more signal from clean data. Annealing data composition is a major lever; teams iterate on it. Hugging Face's training cookbook and Meta's Llama 3 paper describe variations.",
        "why_it_matters": "The bulk corpus contains noise and repetition; annealing on clean data is an efficient way to extract the last quality from a fixed compute budget. It bridges pretraining and fine-tuning — annealing effectively pre-trains the model on instruction-following style without separate SFT. For open-source training teams, careful annealing is one of the highest-leverage decisions.",
        "example": "A team's pretraining run is 10T tokens. Bulk phase: 8.5T tokens on mixed web. Annealing phase: 1.5T tokens on curated mix (textbooks, code, math, clean dialogue) with LR linearly decreasing to 1% of peak. Eval scores at end of annealing are 4 points higher than would result from continuing the bulk run for the same compute.",
        "pitfalls": [
            "Annealing data quality: bad annealing data hurts more than helps because it's seen at high signal.",
            "Length: too short annealing has no effect; too long over-fits to clean data.",
            "Recipe sensitivity: composition and order of annealing data matters significantly; iterate.",
            "Training-eval mismatch: annealing changes capability profile; eval set must reflect post-annealing behaviour."
        ],
        "when_use": "Use as a standard component of frontier-quality LLM pretraining pipelines, especially for open-source models targeting top quality.",
        "when_avoid": "Avoid for small or early-stage training runs where bulk pretraining hasn't saturated and additional bulk data would help more.",
        "related_terms": ["pretraining", "warmup-schedule", "cosine-schedule", "data-mixture", "fine-tuning", "domain-adaptive-pretraining"],
        "related_tools": [],
        "faq": [
            {"q": "How long should annealing be?",
             "a": "10-30% of total training. Llama 3 used larger annealing fractions; smaller models often use 10-20%."},
            {"q": "What data for annealing?",
             "a": "Highest-quality available: textbooks, structured docs, instruction-tuned data, math, code. The team's curation choices matter most."},
             {"q": "LR during annealing?",
             "a": "Continue cosine decay or step down. End-LR around 1-10% of peak."},
             {"q": "Skip annealing?",
             "a": "Possible but leaves quality on the table. Frontier models do annealing because it's worth the engineering."}
        ]
    },
    # 19. ifeval
    {
        "slug": "ifeval",
        "title": "IFEval",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Instruction-Following Evaluation benchmark testing whether models obey verifiable formatting and constraint instructions like 'use 3 bullet points' or 'no commas'.",
        "plain_english": "Many LLM failures happen on simple structural compliance — 'reply in 3 sentences', 'no proper nouns', 'JSON only'. IFEval tests these directly: each prompt contains verifiable constraints; the model's output is automatically checked. Strict and loose modes report different compliance levels. IFEval became a popular leaderboard alongside MMLU because it surfaces a class of failures that subjective benchmarks miss.",
        "how_it_works": "541 prompts (in v1) each containing 1-3 verifiable instructions: 'respond in exactly N sentences', 'must include keyword X', 'must not include keyword Y', 'all uppercase'. After the model responds, automated checkers verify each constraint. Strict mode requires all constraints satisfied; loose mode counts each. Released by Google research; widely used on HuggingFace's Open LLM Leaderboard.",
        "why_it_matters": "IFEval is the cheapest standard benchmark for instruction-following. It complements quality-focused benchmarks (MMLU, MT-Bench) with a structural-compliance angle. Models that score high on IFEval are better at following arbitrary user instructions in production. For chat-product launches, IFEval scores predict UX quality on real-world structural prompts.",
        "example": "A team launches a new fine-tune. MMLU comparable to baseline; MT-Bench up 0.2. IFEval-strict drops 6 points. Investigation: the fine-tune trained on data without diverse formatting demands; the model now ignores compliance instructions. They retrain with format-conditioned examples; IFEval-strict recovers.",
        "pitfalls": [
            "Surface-level compliance: IFEval verifies structural correctness, not quality of content within the structure.",
            "Saturated at top: frontier models reach 85%+ IFEval; differentiation among top models is small.",
            "Limited domain: 541 instructions cover a slice of formatting patterns; production traffic is broader.",
            "Loose vs strict: report both; strict is harder and more meaningful, loose shows partial-compliance distribution."
        ],
        "when_use": "Use as a standard instruction-following eval for chat models. Run on every release alongside quality benchmarks.",
        "when_avoid": "Avoid as the only eval — IFEval's narrow scope misses content-quality regressions.",
        "related_terms": ["evaluation-set", "mt-bench", "elo-rating-llm", "g-eval", "agent-as-judge", "multi-turn-evaluation"],
        "related_tools": [],
        "faq": [
            {"q": "IFEval-strict score interpretation?",
             "a": "70%+ for strong models. Frontier models hit 85-90%. Below 60% indicates instruction-following weaknesses."},
            {"q": "IFEval for instruction tuning?",
             "a": "Yes — common metric for instruction-tuned model quality. Track during fine-tune development."},
            {"q": "Update frequency?",
             "a": "v1 released 2023; v2 and variants extend coverage. Use latest for current model comparisons."},
            {"q": "Helpful for production?",
             "a": "Predicts compliance with real user instructions. Production teams add domain-specific instruction tests on top."}
        ]
    },
    # 20. bbh
    {
        "slug": "bbh",
        "title": "BIG-Bench Hard (BBH)",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Subset of 23 BIG-Bench tasks that earlier models found particularly hard, used to track reasoning improvements in modern LLMs.",
        "plain_english": "BIG-Bench has 200+ tasks; many became saturated as models improved. BBH (BIG-Bench Hard) curates the 23 hardest where pre-PaLM models struggled. The tasks span logical reasoning, multi-step inference, formal language understanding. Modern frontier models score well above human baseline on BBH, but it remains a useful sub-benchmark for tracking reasoning capability across model versions.",
        "how_it_works": "23 tasks include: tracking shuffled objects, logical deductions, navigate (spatial reasoning), word-sorting, dyck languages (balanced parens), formal fallacies. Each task has held-out evaluation sets with exact-match scoring. BBH usually evaluated with chain-of-thought (CoT-BBH) since plain prompting underperforms. Reported as average accuracy across the 23 tasks. Suzgun et al. 2022 introduced BBH.",
        "why_it_matters": "BBH targets reasoning specifically — algorithms, deduction, multi-step inference. As MMLU becomes saturated, BBH provides better differentiation among strong models. It's standard on the Open LLM Leaderboard and frequently cited in model release announcements. Reasoning model improvements (o-series, R1) show clearly on BBH.",
        "example": "A team benchmarks their fine-tune. BBH (CoT) score: 67.3. Baseline: 64.1. Modest gain but in a discriminating-among-strong-models regime. They report it alongside MMLU and IFEval for a balanced picture.",
        "pitfalls": [
            "Contamination risk: BBH problems have been public for years; verify model hasn't memorised.",
            "CoT vs no-CoT: dramatic difference (~15 points); always specify which mode.",
            "Cherry-picking: 23 tasks are diverse; some models excel on subsets; report aggregate plus per-task.",
            "Saturation by frontier: top models score 80+; further improvement is marginal."
        ],
        "when_use": "Use to evaluate reasoning capability in chat or reasoning model releases. Standard on the Open LLM Leaderboard.",
        "when_avoid": "Avoid as a sole reasoning eval; supplement with math (GSM8K), code (HumanEval), and general-reasoning benchmarks.",
        "related_terms": ["evaluation-set", "humaneval", "reasoning-model", "mmlu-pro", "chain-of-thought", "ifeval"],
        "related_tools": [],
        "faq": [
            {"q": "Why CoT on BBH?",
             "a": "Many BBH tasks require multi-step reasoning; CoT prompting gives much better results than direct answer."},
            {"q": "BBH vs MMLU?",
             "a": "MMLU tests knowledge; BBH tests reasoning. Both useful; emphasise BBH for reasoning model evaluation."},
            {"q": "Is BBH saturated?",
             "a": "Top frontier models score 80+; differentiation among the best is small. Newer benchmarks (HLE, GPQA-Diamond) push beyond."},
            {"q": "Per-task reporting?",
             "a": "Recommended for diagnostic purposes. Aggregate scores hide where a model is strong vs. weak."}
        ]
    },
    # 21. mbpp
    {
        "slug": "mbpp",
        "title": "MBPP",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Mostly Basic Python Problems — code-generation benchmark of 974 entry-level Python tasks with unit tests, used alongside HumanEval for code model evaluation.",
        "plain_english": "MBPP is one of the standard code-generation benchmarks. 974 problems, each described in 1-2 sentences with 3-4 hidden unit tests. The model writes Python code; the tests run; pass/fail per problem aggregates to MBPP score. Problems are entry-level (basic algorithms, list manipulation, string parsing) compared to HumanEval's slightly harder set. Together they form the most-cited code-LLM benchmarks.",
        "how_it_works": "Each problem has a description, a function signature, 1-3 visible test cases, and 3-4 hidden tests. Models receive the description (sometimes with test cases as few-shot) and must produce the function. Hidden tests run; all-pass = 1, any-fail = 0 per problem. Aggregate gives Pass@1 score. Variants: MBPP+ (extended tests), MBPP-Plus (more challenging), DS-1000 (data-science focused). Modern code models report MBPP alongside HumanEval as standard.",
        "why_it_matters": "MBPP is a stable, well-tested code benchmark. Its specific role is evaluating basic Python competence — necessary if not sufficient. Combined with HumanEval (slightly harder) and SWE-Bench (real-world repo problems), MBPP gives a graduated view of code-model capability. For tracking improvements across versions, MBPP scores are reproducible and well-understood.",
        "example": "A code-model team reports: HumanEval Pass@1 78.0, MBPP Pass@1 73.5. Both indicate strong basic-Python capability. They also report SWE-Bench Verified (much harder) at 22% to show the gap between toy benchmarks and real-world bug fixing.",
        "pitfalls": [
            "Saturation: top models score 90+ on MBPP; for state-of-the-art comparison, supplement with harder benchmarks.",
            "Contamination: MBPP is in many training corpora; verify cleanliness when evaluating new models.",
            "Test-suite limits: hidden tests are imperfect; some incorrect code passes (test-suite bypass).",
            "Pass@1 vs Pass@k: report multiple K values for full picture."
        ],
        "when_use": "Use as a baseline code benchmark alongside HumanEval. Standard on code-LLM leaderboards.",
        "when_avoid": "Avoid relying solely on MBPP for production decisions — supplement with realistic codebase benchmarks like SWE-Bench.",
        "related_terms": ["humaneval", "swe-bench", "evaluation-set", "pass-at-k", "best-of-n", "g-eval"],
        "related_tools": [],
        "faq": [
            {"q": "MBPP or HumanEval?",
             "a": "Both — they're complementary. HumanEval is slightly harder. Reporting both is standard."},
            {"q": "MBPP+?",
             "a": "Variant with more thorough tests. Catches code that passes original MBPP tests by accident. Recommended for serious evaluation."},
            {"q": "Saturation?",
             "a": "Top models score 90+. For state-of-the-art differentiation, use SWE-Bench, LiveCodeBench, or BigCodeBench."},
            {"q": "Is MBPP only Python?",
             "a": "Yes. For multi-language coding, use BigCodeBench or HumanEval-X."}
        ]
    },
    # 22. hellaswag
    {
        "slug": "hellaswag",
        "title": "HellaSwag",
        "category": "techniques",
        "difficulty_tier": "beginner",
        "tldr": "Commonsense reasoning benchmark of 70K multiple-choice scenarios where the model must pick the most sensible continuation of a real-world description.",
        "plain_english": "HellaSwag tests common-sense by giving a partial situation ('A man is grilling burgers in his backyard. He...') and four continuations. One is what a human would expect; three are adversarial — plausible-looking but wrong. The model picks one. Originally created to be hard for 2019-era models (BERT scored ~50%); modern LLMs near-saturate it (95%+). Still appears on leaderboards as a common-sense baseline.",
        "how_it_works": "Each example: a context sentence + 4 continuation candidates, one correct. Models score each candidate (likelihood) and pick the highest. Candidates are constructed via 'adversarial filtering' — automated probes that pick continuations human-easy but model-hard. Test set: 10K examples. Released by Zellers et al. 2019; remains a standard benchmark on the Open LLM Leaderboard.",
        "why_it_matters": "HellaSwag is one of the original commonsense LLM benchmarks. Its scores are familiar to the community and tracked across model versions. While saturated for frontier models, it's still informative for smaller and older bases. As of 2026 it's part of the standard benchmark grid even though differentiation has narrowed.",
        "example": "A team trains a 7B base. HellaSwag: 78.3. Compared to Llama 3 8B (80.4), the team's model is close but slightly below. They use HellaSwag alongside MMLU and BBH for a multi-faceted view of base-model capability.",
        "pitfalls": [
            "Saturation: top models score 90+; not useful for state-of-the-art comparison.",
            "Contamination: 7-year-old benchmark in many pretraining corpora; recent results may be inflated.",
            "MC-only: tests classification, not generation; doesn't predict generation quality.",
            "Adversarial filtering bias: continuations were tuned against 2019 models; modern models may exploit residual patterns."
        ],
        "when_use": "Use as one of several base-model benchmarks for tracking commonsense reasoning. Standard on the Open LLM Leaderboard.",
        "when_avoid": "Don't use HellaSwag as a primary differentiator among modern frontier models — saturated.",
        "related_terms": ["evaluation-set", "winogrande", "natural-questions", "ifeval", "bbh", "mmlu-pro"],
        "related_tools": [],
        "faq": [
            {"q": "HellaSwag scoring?",
             "a": "Multiple-choice accuracy, typically reported with 0-shot. Higher is better; top models near 96%."},
            {"q": "Still relevant?",
             "a": "For small or older models yes; for frontier models, mostly historical reference."},
            {"q": "What does it actually measure?",
             "a": "Commonsense plausibility — picking the human-expected continuation. Surface pattern recognition rather than deep reasoning."},
            {"q": "Combine with what?",
             "a": "MMLU (knowledge), BBH (reasoning), GSM8K (math), HumanEval (code). Standard 5-7 benchmark grid for base models."}
        ]
    },
    # 23. winogrande
    {
        "slug": "winogrande",
        "title": "Winogrande",
        "category": "techniques",
        "difficulty_tier": "beginner",
        "tldr": "Winograd-style commonsense reasoning benchmark with 44K binary-choice problems, testing pronoun resolution requiring world knowledge.",
        "plain_english": "Winograd Schema problems are sentences where pronoun resolution depends on knowing how the world works. 'The trophy didn't fit in the suitcase because it was too big — what was too big?' Humans answer 'trophy' instantly; models need real understanding of size/containers. Winogrande extends the original Winograd schemas to 44K examples constructed adversarially. It's a standard reasoning benchmark.",
        "how_it_works": "Each example: a fill-in-the-blank sentence with two candidate pronoun referents. Model picks one based on which makes sense in context. Adversarial construction (AfLite filter) removes superficially-cued examples to focus on genuine commonsense. Released by Sakaguchi et al. 2019. Evaluated 0-shot or few-shot; reported on the Open LLM Leaderboard alongside HellaSwag and MMLU.",
        "why_it_matters": "Winogrande tests a specific kind of commonsense reasoning that requires knowing world dynamics. It's complementary to HellaSwag (continuations) and MMLU (knowledge). Frontier models reach 85-90%; smaller models score lower, providing differentiation. As a standard benchmark, it's part of the picture for evaluating new bases.",
        "example": "A team's 7B base scores 73.2 on Winogrande. Llama 3 8B: 76.8. Smaller gap than on harder reasoning benchmarks. Used as a commonsense check alongside HellaSwag.",
        "pitfalls": [
            "Saturation at top: frontier models near 90%; differentiation narrow.",
            "Contamination: public benchmark in many training sets.",
            "Limited reasoning depth: pronoun resolution is one slice of commonsense.",
            "Style sensitivity: prompts and few-shot choices affect scores noticeably."
        ],
        "when_use": "Use as a standard commonsense benchmark in the open-LLM evaluation grid for base models.",
        "when_avoid": "Don't use as primary differentiator among strong models; supplement with harder reasoning evals.",
        "related_terms": ["hellaswag", "evaluation-set", "natural-questions", "ifeval", "bbh", "mmlu-pro"],
        "related_tools": [],
        "faq": [
            {"q": "Winogrande or original Winograd Schemas?",
             "a": "Winogrande extends to 44K examples for statistical power. Original Winograd had ~150 examples; both are commonsense pronoun-resolution."},
            {"q": "Score interpretation?",
             "a": "70-80% solid; 85-90% frontier-level. Below 60% indicates significant commonsense gaps."},
            {"q": "Few-shot or 0-shot?",
             "a": "Both reported; 5-shot is common on the Open LLM Leaderboard. Compare on the same few-shot setting."},
            {"q": "Still differentiates?",
             "a": "Among small-to-mid models, yes. Among frontier, less. Use as part of a benchmark suite."}
        ]
    },
    # 24. natural-questions
    {
        "slug": "natural-questions",
        "title": "Natural Questions",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Open-domain question-answering benchmark with 300K+ real Google search queries paired with Wikipedia-grounded answers, used for QA and RAG evaluation.",
        "plain_english": "Natural Questions (NQ) collects real-world Google queries. Each query is paired with a Wikipedia article and either a 'long answer' (paragraph) or 'short answer' (span) within it. Benchmarking systems answer the query using only Wikipedia. Pure-LLM mode tests world knowledge; RAG mode tests retrieval+synthesis. NQ is a foundational open-domain QA benchmark.",
        "how_it_works": "300K+ training queries, 8K dev queries, hidden test set. Each query has a corresponding Wikipedia page; annotators identify long-answer paragraphs and short-answer spans. Evaluation: F1 over predicted vs. annotated answer spans for short answers, exact-match for long. RAG systems retrieve from Wikipedia; closed-book systems must answer from parametric knowledge alone. Released by Google research (Kwiatkowski et al. 2019).",
        "why_it_matters": "NQ tests real-world QA at scale with grounded answers. RAG models report NQ scores to demonstrate retrieval+synthesis quality. Closed-book scores show parametric knowledge. The ~300K training set is also widely used for retriever fine-tuning. Standard reference benchmark for open-domain QA research and production RAG.",
        "example": "A RAG team builds a Wikipedia QA system. NQ-open Pass@1 (RAG): 52.3 with their retriever + GPT-4. Closed-book GPT-4: 38. The 14-point lift quantifies the value of retrieval in their system.",
        "pitfalls": [
            "Wikipedia-only: NQ uses Wikipedia as truth; for non-Wikipedia domains the benchmark is less applicable.",
            "Annotation noise: long-answer paragraphs sometimes contain irrelevant text alongside the answer.",
            "Span-overlap scoring: F1 over answer spans is brittle to paraphrases and minor wording shifts.",
            "Ageing: the original Wikipedia dump is from 2018; some queries' correct answers have shifted since."
        ],
        "when_use": "Use for open-domain QA system evaluation, RAG benchmarking against Wikipedia, and retriever fine-tuning data.",
        "when_avoid": "Avoid for non-Wikipedia domains where the benchmark assumptions don't apply.",
        "related_terms": ["evaluation-set", "rag", "retrieval", "rag-evaluation", "humaneval", "ifeval"],
        "related_tools": [],
        "faq": [
            {"q": "NQ-open vs NQ-full?",
             "a": "Open: any-context retrieval allowed. Full: original benchmark with single Wikipedia article per query. Open is more challenging."},
            {"q": "RAG-mode scoring?",
             "a": "Same F1/exact-match; RAG systems first retrieve, then read. Reported alongside retrieval recall metrics."},
            {"q": "Used for retriever training?",
             "a": "Yes — 300K training queries with positive doc labels are widely used to fine-tune dense retrievers."},
            {"q": "Still relevant?",
             "a": "Yes — standard reference for open-domain QA. Newer benchmarks (TriviaQA-FilterQA, MultiHop-RAG) supplement."}
        ]
    },
    # 25. agent-protocol
    {
        "slug": "agent-protocol",
        "title": "Agent Protocol",
        "category": "protocols",
        "difficulty_tier": "intermediate",
        "tldr": "Standard for inter-agent communication and tool invocation, defining message formats, capabilities, and discovery so agents from different vendors can interoperate.",
        "plain_english": "As multi-agent systems grow, vendor-specific message formats limit interoperability. Agent protocols define standardised ways for agents to communicate: how to declare capabilities, how to send/receive task requests, how to call tools, how to handle handoffs. Examples: A2A (Agent-to-Agent) protocol, MCP (Model Context Protocol) for tool exposure, OpenAI Assistant API conventions. Standardisation enables cross-vendor agent ecosystems.",
        "how_it_works": "Protocols define: (1) capability declarations (what an agent can do), (2) message schemas (request/response formats), (3) discovery mechanisms (find agents by capability), (4) authentication (who can call whom), (5) error handling. Agents implementing the protocol can call each other regardless of underlying LLM or framework. MCP focuses on tool exposure; A2A on inter-agent collaboration. Multiple competing protocols exist; convergence is incomplete.",
        "why_it_matters": "Without protocols, every agent integration is bespoke. With them, agents become composable building blocks. As more frontier labs and infrastructure providers ship agent platforms, protocol standardisation is the difference between an integration nightmare and a thriving ecosystem. Adoption is accelerating in 2025-2026 driven by MCP, A2A, and similar efforts.",
        "example": "A team builds a customer-service workflow combining: their own intent agent, a third-party CRM agent (vendor A), and a billing agent (vendor B). Without a shared protocol, gluing these would require custom translation layers. With A2A protocol support, the agents discover and call each other directly. Total integration work: hours instead of weeks.",
        "pitfalls": [
            "Protocol fragmentation: multiple competing standards (MCP, A2A, OpenAI Assistants); pick the dominant one in your ecosystem.",
            "Versioning: protocols evolve; backward-compatibility decisions matter.",
            "Capability lying: agents declaring capabilities they can't actually deliver; verify in production.",
            "Authentication: cross-vendor agent calls span trust boundaries; secure carefully."
        ],
        "when_use": "Use protocol-aware design for multi-vendor agent systems, agent marketplaces, or workflows expected to outlive any single vendor.",
        "when_avoid": "Avoid premature standardisation for single-team in-house agents where protocol overhead exceeds integration benefit.",
        "related_terms": ["mcp", "a2a-protocol", "tool-use-protocol", "agent-orchestrator", "ai-agent", "function-schema"],
        "related_tools": [],
        "faq": [
            {"q": "MCP or A2A?",
             "a": "MCP for tool exposure (model talks to tools). A2A for agent-to-agent collaboration. Different scopes; can coexist."},
            {"q": "Standardisation status?",
             "a": "Active in 2026 with major labs proposing protocols. Convergence not yet complete; expect continued evolution."},
            {"q": "Build my own?",
             "a": "Avoid for cross-vendor work. Use existing protocols; contribute to standards if you have specific needs."},
            {"q": "Authentication?",
             "a": "OAuth-style or API-key based depending on protocol. Cross-organisation calls need careful trust handling."}
        ]
    },
    # 26. agent-state-machine
    {
        "slug": "agent-state-machine",
        "title": "Agent State Machine",
        "category": "concepts",
        "difficulty_tier": "intermediate",
        "tldr": "Agent design where execution flow is modelled as a finite-state machine — explicit states, transitions, and stopping conditions instead of free-form looping.",
        "plain_english": "Free-form agent loops are hard to predict and audit. State-machine agents structure execution as named states with explicit transitions: 'gather_info' → 'plan' → 'execute' → 'verify' → 'done'. Each state has clear entry conditions, behaviour, and exit logic. Predictability and observability improve dramatically; debugging becomes 'which state failed' rather than 'where did the agent wander'. LangGraph and similar frameworks make state machines first-class agent constructs.",
        "how_it_works": "Define states (nodes) with execution logic per state. Define transitions (edges) with conditions specifying when to move from one state to another. The agent runs a state, evaluates transitions, moves to the next state. Stopping conditions are explicit (terminal state, error, budget). Tools, prompts, and tool sets can be scoped per-state — a 'gather_info' state has different tools than 'verify'. LangGraph compiles graph definitions into runnable agents; state machines also implement well in plain code with framework-free implementations.",
        "why_it_matters": "Production agent systems benefit from predictability. State-machine agents are easier to test (test each state independently), debug (inspect transition history), and modify (add states without rewriting). For workflows with clear stages, state-machine design beats prompt-everything approaches. As agent systems mature, state-machine patterns become more common.",
        "example": "A customer-service agent uses 5 states: triage, info_gather, action_resolve, verify, escalate. Each state has its own prompt and tool set. Transitions are guards on agent output: 'if intent is technical, go to action_resolve'. Debugging a failed conversation is 'agent looped between info_gather and action_resolve' rather than 'agent went off-track somewhere'.",
        "pitfalls": [
            "Over-structuring: very-rigid states limit creative problem-solving; balance against free-form needs.",
            "Transition complexity: many states with many transitions becomes a maintenance burden.",
            "LLM in transitions: using an LLM to decide transitions adds cost; rule-based where possible.",
            "Edge cases: real workflows have unexpected paths; ensure fallback or open-state handling."
        ],
        "when_use": "Use for production agents with clear-stage workflows: support, onboarding, structured research, transactional flows.",
        "when_avoid": "Avoid for genuinely open-ended exploration where state structure constrains useful behaviour.",
        "related_terms": ["agent-orchestrator", "ai-agent", "agent-loop", "finite-state-agent", "react", "plan-and-execute"],
        "related_tools": ["langgraph"],
        "faq": [
            {"q": "State machine vs ReAct?",
             "a": "ReAct interleaves reasoning and action freely. State machine constrains flow to defined stages. State machines are more predictable; ReAct is more flexible. Often combined: each state is a ReAct mini-loop."},
            {"q": "How many states?",
             "a": "3-10 typical for production. Beyond 15-20, complexity becomes hard to maintain; consider sub-machines."},
            {"q": "Test individual states?",
             "a": "Yes — that's a major benefit. Mock state inputs, test exit transitions, much easier than testing full agent loops."},
            {"q": "LangGraph?",
             "a": "Most-cited Python framework for state-machine agents. Provides graph compilation, tracing, and serialization. Strong choice in 2026."}
        ]
    },
    # 27. tool-use-protocol
    {
        "slug": "tool-use-protocol",
        "title": "Tool-Use Protocol",
        "category": "protocols",
        "difficulty_tier": "intermediate",
        "tldr": "Standardised format and lifecycle for an LLM to invoke external functions — covering schema declaration, call serialization, response handling, and error semantics.",
        "plain_english": "When an LLM calls a function, both sides need to agree on a contract: how to declare the function, how to call it, what shape the response takes, what errors look like. Tool-use protocols formalise this. Examples: OpenAI's tool-calling format, Anthropic's tool_use blocks, Model Context Protocol (MCP) for external tools, Google's function declarations. Each has slight variations; abstraction layers (LangChain, LiteLLM) normalise across them.",
        "how_it_works": "Provider exposes tool-calling API: client passes tool schemas (name, description, parameters JSON schema); model returns tool_call blocks containing function name and serialized arguments; client executes the function; result is sent back to the model in a tool_result message. Variations: parallel calls (multiple tools at once), strict mode (schema enforcement), tool selection control (auto/required/none). MCP standardises tool exposure across providers via a server-client architecture.",
        "why_it_matters": "Tool-use protocols are the contract that makes agents work. Inconsistent or poorly-specified protocols cause silent failures; well-designed ones enable reliable tool registries. Provider-specific formats lock you in; standards-based protocols (MCP) preserve portability. Knowing the protocol semantics for your chosen provider is essential for production agent reliability.",
        "example": "A team's agent uses LangChain to abstract over OpenAI and Anthropic tool-calling protocols. The same tool registry works on both. When OpenAI introduces strict mode, the abstraction layer enables it without changing tool definitions. The team avoids vendor lock-in.",
        "pitfalls": [
            "Provider differences: OpenAI's strict mode, Anthropic's parallel calls, Google's function declarations all differ subtly; handle each.",
            "Schema strictness: vague schemas confuse models; specific descriptions and enums improve accuracy.",
            "Error handling: tool failures need to feed back to the model gracefully, not crash the agent.",
            "Streaming: tool calls in streaming responses arrive in chunks; assemble carefully."
        ],
        "when_use": "Use whenever connecting LLMs to external functions or APIs. Standard pattern for any tool-using system.",
        "when_avoid": "Avoid bespoke parsing of tool calls — use provider SDKs and abstraction layers (LangChain, LiteLLM, Instructor) for reliability.",
        "related_terms": ["function-schema", "tool-use", "tool-router", "mcp", "agent-protocol", "tool-use-format"],
        "related_tools": ["instructor", "outlines"],
        "faq": [
            {"q": "OpenAI or Anthropic format?",
             "a": "Both are de facto standards. Use abstraction layers to support both without duplicating code."},
            {"q": "MCP relevance?",
             "a": "MCP standardises tool exposure between LLMs and tool servers. Growing adoption in 2026 for cross-vendor tool registries."},
            {"q": "Strict mode tradeoffs?",
             "a": "Strict mode guarantees schema compliance but slightly reduces capability on complex schemas. Default to strict for production."},
            {"q": "Parallel tool calls?",
             "a": "Anthropic and recent OpenAI versions support multiple simultaneous tool calls. Useful for independent operations; needs orchestration on the application side."}
        ]
    },
    # 28. agent-evaluation
    {
        "slug": "agent-evaluation",
        "title": "Agent Evaluation",
        "category": "techniques",
        "difficulty_tier": "intermediate",
        "tldr": "Practice of measuring agent quality across success rate, efficiency, robustness, and trajectory quality — beyond just final-answer correctness.",
        "plain_english": "Agents are harder to evaluate than chat models. Final-answer correctness misses trajectory quality (did the agent take a sensible path?), efficiency (how many steps?), robustness (does it recover from errors?), and tool-use accuracy (did it call the right tools with right args?). Agent evaluation breaks down these dimensions. Frameworks like AgentBench, WebArena, OS-World, and τ-bench provide standard scenarios; custom evals layer on top.",
        "how_it_works": "Define a scenario set with task descriptions and success criteria. Run the agent on each scenario; capture: final outcome (success/fail/timeout), trajectory (every action and observation), tool-call accuracy (right tools, right arguments), step count (efficiency), recovery from injected errors (robustness). Aggregate per-dimension. Public benchmarks (WebArena, OS-World, AgentBench) provide standard scenarios; production teams add domain-specific evals.",
        "why_it_matters": "Agent quality has multiple dimensions; single-number scores hide important trade-offs. A high-success-rate agent that takes 50 steps for what should take 5 is wasteful even if 'correct'. Agent evaluation surfaces these issues so teams can prioritise fixes. As agent systems get more complex, structured evaluation is the difference between confident deployment and rolling roulette.",
        "example": "A team's coding agent has success rate 68% on SWE-Bench Verified. Trajectory analysis shows: average 23 steps per task (high), 12% of failures are recoverable retries (potential improvement), tool-call argument accuracy is 87% (room to improve). They prioritise tool-call accuracy fixes; success rate climbs to 74%.",
        "pitfalls": [
            "Definition of success: what counts as solving a task is subjective; rubric carefully.",
            "Trajectory length cost: capping steps too aggressively rewards giving up; reward correct termination.",
            "Sandbox infrastructure: realistic agent eval needs realistic environments; expensive to maintain.",
            "Eval drift: as agents improve, scenarios that were hard become easy; refresh benchmarks."
        ],
        "when_use": "Use for any production agent system. Standard practice from prototype to production.",
        "when_avoid": "Don't skip agent evaluation for production systems — issues show up after launch worse than during dev.",
        "related_terms": ["evaluation-set", "ai-agent", "agent-as-judge", "agent-benchmark", "trajectory-reward", "agent-loop"],
        "related_tools": [],
        "faq": [
            {"q": "Public benchmarks?",
             "a": "WebArena, OS-World, AgentBench, τ-bench, SWE-Bench. Each targets different agent capabilities; use the relevant ones for your domain."},
            {"q": "Trajectory analysis tools?",
             "a": "Langfuse, Phoenix, Arize AI all support agent trace analysis. Visualisation helps identify patterns."},
            {"q": "Custom evals?",
             "a": "Yes — production agents need domain-specific evals. Build representative scenarios from real user requests."},
            {"q": "Success rate benchmark?",
             "a": "Domain-dependent. SWE-Bench Verified frontier ~50%; WebArena ~30%; structured business workflows often 70-90%."}
        ]
    },
    # 29. finite-state-agent
    {
        "slug": "finite-state-agent",
        "title": "Finite-State Agent",
        "category": "concepts",
        "difficulty_tier": "intermediate",
        "tldr": "Specific agent design where execution proceeds through a strictly enumerable set of states with deterministic transitions — maximum predictability over flexibility.",
        "plain_english": "Where state-machine agents allow LLM-driven transitions, finite-state agents go further: every transition is rule-based and deterministic. The LLM's role is constrained to the state-specific behaviour; flow control is fully scripted. Highly auditable, testable, and fail-safe — the agent literally cannot enter an unintended state. Useful for compliance-sensitive workflows, regulated environments, and safety-critical paths.",
        "how_it_works": "Enumerate every possible state (typically <20). Define explicit transition rules (rule-based, no LLM): 'if classification=technical_issue → go to state B'. The LLM operates within states (generate response, classify input, extract entity) but never decides flow. Easy to audit: full state graph visible. Easy to test: every transition is deterministic. Trade-off: cannot handle out-of-distribution inputs gracefully — falls back to default state or escalation.",
        "why_it_matters": "For regulated industries (finance, healthcare, legal), unpredictable agents are unshippable. Finite-state agents eliminate flow-control unpredictability. The LLM's creative work happens within scoped states; the workflow itself is contractual. As AI deployments enter heavily-regulated contexts, finite-state agents become the default pattern.",
        "example": "A bank deploys a fraud-investigation agent for customer disputes. 8 finite states: triage, identity-verify, transaction-detail, witness-collect, decision, communicate, archive, escalate. Every transition is rule-based. Auditors can verify the agent never makes payouts without going through identity-verify. Compliance signs off; deployment proceeds.",
        "pitfalls": [
            "Inflexibility: real-world conversations don't always fit pre-defined states; default-to-escalation prevents disasters.",
            "State proliferation: complex workflows tempt teams into many states; consolidate where possible.",
            "Out-of-distribution: novel inputs that don't trigger any transition need explicit handling.",
            "Maintenance: changing the state graph in production requires careful versioning and rollout."
        ],
        "when_use": "Use for compliance-critical, regulated, or safety-sensitive workflows where predictable flow is more important than flexibility.",
        "when_avoid": "Avoid for open-ended exploration, creative tasks, or workflows where the right path is genuinely unpredictable.",
        "related_terms": ["agent-state-machine", "ai-agent", "agent-orchestrator", "agent-loop", "react", "ai-governance"],
        "related_tools": ["langgraph"],
        "faq": [
            {"q": "Finite-state vs state-machine agent?",
             "a": "Finite-state is strict variant of state-machine: deterministic transitions only. State-machine allows LLM-driven transitions. Different points on the predictability-flexibility curve."},
            {"q": "Auditability?",
             "a": "Complete — every state and transition is enumerable. Auditors can verify behavior without running the agent."},
            {"q": "Performance vs flexible agents?",
             "a": "Lower task-completion ceiling on novel inputs; higher reliability on in-distribution inputs."},
            {"q": "Compliance benefits?",
             "a": "Significant — predictable flow simplifies regulatory review. Often the difference between deployable and not in heavily-regulated industries."}
        ]
    },
    # 30. safety-classifier
    {
        "slug": "safety-classifier",
        "title": "Safety Classifier",
        "category": "safety",
        "difficulty_tier": "intermediate",
        "tldr": "Lightweight model that scores user inputs and model outputs for harm categories (toxicity, illicit content, PII), gating risky content before display or processing.",
        "plain_english": "A safety classifier is a smaller specialised model that decides 'is this content harmful?' on inputs and outputs. Compared to relying solely on the main LLM's safety training, classifiers add a defense layer: if the classifier flags content, the system blocks, redacts, or escalates. Classifiers are cheap (small models), fast, and easier to update than fine-tuning the main model. Standard component of production safety stacks.",
        "how_it_works": "Train a small classifier (often a fine-tuned BERT-class or distilled LLM) on labelled examples of harmful and safe content across categories: hate, harassment, sexual, self-harm, violence, illegal advice, PII. Categories vary by deployment. Production pipelines call the classifier on user input before LLM, on LLM output before user, or both. Threshold-based decisions: above-threshold blocks, between thresholds escalates, below-threshold allows. Continuous retraining on new attack patterns keeps classifiers current.",
        "why_it_matters": "LLMs ship with safety training but it's not foolproof; jailbreaks bypass it. Safety classifiers add a separate, easier-to-update defense. They also let you enforce policies independent of the model — block specific topics for compliance, even if the model would happily produce them. For consumer products, regulated industries, and youth-facing applications, classifiers are essential infrastructure.",
        "example": "A consumer chat product runs every user message through a safety classifier. Harmful inputs (5%) trigger refusal templates and don't reach the LLM. LLM outputs are also classified; flagged outputs are replaced with safe fallbacks. Combined, the system maintains low harmful-output rate even when the underlying LLM has occasional safety failures.",
        "pitfalls": [
            "False positives: classifiers refuse legitimate content; calibrate thresholds and provide override paths.",
            "Coverage gaps: novel attack patterns slip through; ongoing retraining required.",
            "Latency: per-message classification adds cost; balance against safety needs.",
            "Multilingual: classifiers trained on English perform worse on other languages; localise."
        ],
        "when_use": "Use for any consumer-facing or regulated production deployment. Layer safety classifiers between users and LLMs in both directions.",
        "when_avoid": "Avoid only for internal-only deployments where users are pre-vetted and policy enforcement isn't required.",
        "related_terms": ["content-filter-llm", "moderation-api", "jailbreak-classifier", "prompt-injection-defense", "red-teaming", "ai-governance"],
        "related_tools": [],
        "faq": [
            {"q": "Build or buy?",
             "a": "OpenAI's Moderation API and similar are good baselines. Custom classifiers help for domain-specific policies; combine with off-the-shelf for breadth."},
            {"q": "Multiple classifiers?",
             "a": "Yes — different classifiers for different harm categories often outperform a single multi-class classifier. Compose results into a final decision."},
            {"q": "Does this slow inference?",
             "a": "Adds 10-50ms per direction. Acceptable in most chat workloads; budget carefully for latency-tight paths."},
            {"q": "Retraining frequency?",
             "a": "Monthly to quarterly for high-traffic products. New attack patterns emerge continuously; staleness creates gaps."}
        ]
    },
    # 31. content-filter-llm
    {
        "slug": "content-filter-llm",
        "title": "Content Filter (LLM)",
        "category": "safety",
        "difficulty_tier": "beginner",
        "tldr": "System layer that screens text content (user input or model output) against a policy, blocking or modifying disallowed material before it reaches its destination.",
        "plain_english": "A content filter sits between LLM output and the end user, or between user input and the LLM. Its job: spot disallowed content. Filters can be rule-based (regex, keyword lists), classifier-based (safety classifiers), or LLM-as-judge (asking another model to evaluate). Multiple layers are common: block obvious bad content cheaply with rules, send borderline to a classifier, escalate truly ambiguous cases to an LLM judge.",
        "how_it_works": "Define filtering rules per direction (input vs output). Layer 1: rule-based exact matches (specific URLs, banned keywords) — fast and cheap. Layer 2: classifier-based for nuance (toxicity, hate, PII). Layer 3: LLM-judge for grey areas (intent assessment, contextual judgement). Filters return verdicts: allow, block, redact, escalate. Production systems log decisions for audit and continuous improvement. False-positive minimisation matters as much as false-negative.",
        "why_it_matters": "Content filters are the final mile of safety. They enforce specific policies independent of the model's training, can be updated faster than retraining, and provide a clear audit trail. For consumer products, B2B SaaS, and regulated workloads, filters are baseline infrastructure. Cumulative impact of a strong filter stack often exceeds what the underlying LLM contributes to safety.",
        "example": "A team deploys a B2B chat assistant with content filtering: input filter blocks PII (regex on emails/SSNs), classifier scores toxicity (>0.8 blocked), LLM judge evaluates ambiguous cases. Output filter blocks model leakage of input PII and ensures responses don't include disallowed content. Audit logs show 99.7% of filter decisions are uncontroversial; 0.3% feed back into rule refinement.",
        "pitfalls": [
            "False positives: aggressive filters refuse legitimate queries; calibrate carefully.",
            "Policy drift: enforcement should match policy; mismatches create user trust issues.",
            "Ageing rules: keyword lists go stale; refresh periodically.",
            "Latency: stacking filters adds milliseconds; optimise for fast paths."
        ],
        "when_use": "Use for any production deployment serving non-trusted users. Standard infrastructure for chat, assistants, and any LLM-output-to-user pipeline.",
        "when_avoid": "Avoid heavy filtering for internal-only deployments where users are vetted and safety constraints can be relaxed.",
        "related_terms": ["safety-classifier", "moderation-api", "jailbreak-classifier", "prompt-injection-defense", "red-teaming", "ai-governance"],
        "related_tools": [],
        "faq": [
            {"q": "Layered filters?",
             "a": "Yes — fast rules → classifier → LLM judge in escalating order. Reserve expensive checks for ambiguous cases."},
            {"q": "Audit logging?",
             "a": "Essential. Filter decisions need to be reviewable for both regulatory and continuous-improvement reasons."},
            {"q": "Filter direction?",
             "a": "Both — input filtering catches abuse attempts; output filtering catches model failures. Need both for robust safety."},
            {"q": "Override paths?",
             "a": "Provide for legitimate exceptions: customer support escalations, research access, etc. Track usage to detect abuse."}
        ]
    },
    # 32. moderation-api
    {
        "slug": "moderation-api",
        "title": "Moderation API",
        "category": "safety",
        "difficulty_tier": "beginner",
        "tldr": "Vendor-provided endpoint that classifies text against harm categories — provides a quick way to add safety checks without training custom classifiers.",
        "plain_english": "OpenAI Moderation API, Anthropic's safety endpoints, Google Perspective API, AWS Comprehend Toxicity — these are turnkey moderation services. Pay per request; get back category scores (hate, harassment, sexual, self-harm, etc.). They're the easiest way to bolt safety onto an LLM application without building classifiers in-house. Free or cheap; coverage and accuracy vary by provider and category.",
        "how_it_works": "Send text to the API; receive category scores. Each provider has its own categories and threshold semantics. OpenAI's Moderation API is free and supports 11 categories. Perspective API supports many languages and dialects. AWS Comprehend covers PII detection alongside toxicity. Production systems often query multiple APIs and combine results, or layer them with custom domain-specific classifiers. Latency typically 50-200ms; throughput limits apply.",
        "why_it_matters": "Moderation APIs let small teams add safety checks immediately without ML expertise. They're not perfect — gaps and biases are real — but they're substantially better than no filtering. For early-stage products, MVPs, or non-safety-critical deployments, a moderation API plus prompt-level safety is often enough. Larger systems combine with custom layers.",
        "example": "A startup launches a chat product. Day 1: integrate OpenAI Moderation API on input and output. Cost: <$50/month for early traffic. Coverage caught 99% of obvious harm with no custom training. As the team grows, they add a custom domain-specific classifier alongside the moderation API for industry-specific policies.",
        "pitfalls": [
            "Provider gaps: each API has weak categories; cross-check critical categories with multiple APIs.",
            "Multilingual: English coverage is best; other languages weaker. Pick provider matching your language mix.",
            "False positives: thresholds need calibration; default settings often over-block.",
            "Privacy: sending content to external APIs has privacy and compliance implications; check vendor terms."
        ],
        "when_use": "Use as the fastest path to baseline safety for any new product. Especially valuable for early-stage teams without ML capacity.",
        "when_avoid": "Don't rely solely on moderation APIs for high-stakes deployments — supplement with domain-specific classifiers and policies.",
        "related_terms": ["content-filter-llm", "safety-classifier", "jailbreak-classifier", "ai-governance", "red-teaming", "prompt-injection-defense"],
        "related_tools": [],
        "faq": [
            {"q": "OpenAI Moderation free?",
             "a": "Yes for omni-moderation-latest. No-cost-baseline for many products. Newer text-moderation-stable also free."},
            {"q": "Multilingual support?",
             "a": "Perspective API has strong multilingual; OpenAI is mainly English. Pick provider matching your traffic."},
            {"q": "Real-time?",
             "a": "Latency typically 50-200ms. Acceptable for most chat workloads; cache when possible for repeated content."},
            {"q": "Custom categories?",
             "a": "APIs use fixed categories. Custom policies need custom classifiers; combine API + custom."}
        ]
    },
    # 33. llm-firewall
    {
        "slug": "llm-firewall",
        "title": "LLM Firewall",
        "category": "safety",
        "difficulty_tier": "intermediate",
        "tldr": "Security layer between application and LLM that enforces input/output policies — blocking prompt injection, data exfiltration, and disallowed content patterns.",
        "plain_english": "Web apps have firewalls; LLM apps need them too. An LLM firewall sits between the application and the model, enforcing security policies: detect prompt-injection attempts, block sensitive-data exfiltration in outputs, prevent disallowed instructions from reaching the model, log everything for audit. Examples include Lakera Guard, Protect AI, NVIDIA NeMo Guardrails. As LLM adoption grows in enterprise, LLM firewalls become baseline infrastructure.",
        "how_it_works": "All LLM traffic flows through the firewall. Input checks: prompt-injection signature matching, PII detection, policy compliance, rate limiting per user. Output checks: PII leakage, prohibited content, jailbreak detection in responses. Firewall actions: allow, block, redact, escalate, alert. Modern firewalls use combinations of regex, classifiers, and LLM judges. Audit logs feed compliance reporting and incident response. Often combined with broader observability (Langfuse, Helicone) for unified visibility.",
        "why_it_matters": "LLM-specific attack vectors (prompt injection, jailbreaks, data exfiltration) need LLM-specific defenses. Generic web firewalls don't understand LLM threats. Dedicated LLM firewalls provide policy enforcement, audit trails, and consistent defense across teams using multiple LLMs. For enterprise deployments and regulated industries, LLM firewalls are required infrastructure.",
        "example": "An enterprise team rolls out an internal AI assistant. Lakera Guard sits between the application and OpenAI: blocks 200+ known prompt-injection patterns, redacts PII in inputs, scans outputs for company-confidential leakage. Audit log captures every blocked event. Compliance team reviews monthly; quarterly penetration tests validate.",
        "pitfalls": [
            "False positives: aggressive blocking refuses legitimate queries; calibrate.",
            "Performance: every request through the firewall adds latency; optimise critical paths.",
            "Coverage: novel attack patterns slip through; combine with continuous threat monitoring.",
            "Cost: dedicated firewall services have per-request fees; budget."
        ],
        "when_use": "Use for enterprise LLM deployments, regulated industries, or any system where LLM-specific attacks have meaningful business impact.",
        "when_avoid": "Avoid for prototypes or internal-only systems where overhead exceeds risk reduction.",
        "related_terms": ["safety-classifier", "content-filter-llm", "moderation-api", "prompt-injection-defense", "red-teaming", "ai-governance"],
        "related_tools": [],
        "faq": [
            {"q": "Lakera Guard or Protect AI?",
             "a": "Both are reputable. Lakera focuses on prompt-injection defense; Protect AI broader security. Pick by feature match."},
            {"q": "DIY or commercial?",
             "a": "Commercial faster to deploy; DIY for unique policies. Many teams combine: commercial for breadth, custom rules for specifics."},
            {"q": "Performance impact?",
             "a": "10-50ms typical. Optimise hot paths; aggressive checks only on suspicious traffic."},
            {"q": "Audit logging?",
             "a": "Essential — most firewalls log all decisions. Required for compliance reporting in regulated industries."}
        ]
    },
    # 34. jailbreak-classifier
    {
        "slug": "jailbreak-classifier",
        "title": "Jailbreak Classifier",
        "category": "safety",
        "difficulty_tier": "intermediate",
        "tldr": "Specialised classifier trained to detect jailbreak attempts in user prompts — patterns trying to bypass model safety training.",
        "plain_english": "Jailbreak attempts have recognisable patterns: roleplay framings ('pretend you have no restrictions'), authority claims ('I'm a security researcher'), encoded payloads (Base64, leetspeak), context manipulation. A jailbreak classifier learns these patterns and flags suspicious inputs before they reach the LLM. It's a complement to general safety classifiers — specifically tuned for adversarial inputs trying to bypass safety.",
        "how_it_works": "Train a binary or multi-label classifier on labelled jailbreak vs benign prompts. Training data comes from public jailbreak corpora (e.g. JailbreakBench, AdvBench), red-team logs, and curated examples. Inference: classify each input; flag above threshold. Production usage: block, redact, or route to a hardened pipeline. Continuously retrain as new jailbreak patterns emerge — adversaries iterate, so classifier must too.",
        "why_it_matters": "Generic safety classifiers miss jailbreak-specific patterns. Dedicated jailbreak classifiers add defense-in-depth: even if the LLM's training fails on a novel attack, the classifier may still catch it. For consumer-facing products and high-traffic deployments, jailbreak classifiers reduce successful attacks substantially. Combined with prompt-injection defenses, they form the input-side safety layer.",
        "example": "A team adds a jailbreak classifier in front of their chat product. Initial deployment catches 87% of known jailbreaks. Over 6 months they retrain on new patterns from production logs and red-team exercises. Catch rate climbs to 94%. Successful jailbreaks become rare and easier to triage when they occur.",
        "pitfalls": [
            "Adversarial robustness: attackers adapt to classifiers; continuous retraining required.",
            "False positives: aggressive classifiers refuse roleplay queries that aren't jailbreaks; calibrate.",
            "Multilingual gaps: classifiers trained on English jailbreaks miss attacks in other languages.",
            "Encoding evasion: Base64 or homoglyph attacks bypass surface-level classifiers; combine with decoding-aware checks."
        ],
        "when_use": "Use for high-traffic consumer-facing LLM products, especially with general-purpose models exposed to broad audiences.",
        "when_avoid": "Avoid for narrow trusted-user deployments where jailbreak risk is low and classifier overhead isn't justified.",
        "related_terms": ["safety-classifier", "content-filter-llm", "prompt-injection-defense", "jailbreaking", "red-teaming", "moderation-api"],
        "related_tools": [],
        "faq": [
            {"q": "Public jailbreak datasets?",
             "a": "JailbreakBench, AdvBench, and curated red-team logs from major providers are common training sources. Check licenses."},
            {"q": "Retraining frequency?",
             "a": "Monthly for high-traffic products. Adversaries iterate; staleness creates exposure."},
            {"q": "Catch rate target?",
             "a": "Aim for 90%+ on known patterns; novel attacks always slip through. Combine with downstream defenses."},
            {"q": "Off-the-shelf?",
             "a": "Lakera Guard, Protect AI, and others ship jailbreak detection. Faster than custom; less domain-specific."}
        ]
    },
    # 35. prefill-step
    {
        "slug": "prefill-step",
        "title": "Prefill Step",
        "category": "infra",
        "difficulty_tier": "advanced",
        "tldr": "First phase of LLM inference where the entire prompt is processed in parallel to populate the KV cache before sequential decode begins.",
        "plain_english": "LLM inference has two phases. Prefill: take the full prompt, run it through the model, compute attention over the whole sequence, store keys and values in cache. This step is compute-heavy but parallelisable. Decode: generate one token at a time, each attending to the cache. Decode is memory-bandwidth-bound. Prefill is fast on GPUs (parallel) but expensive in compute; decode is slow per token but low compute per step. Understanding both phases is essential for optimising inference.",
        "how_it_works": "Prefill processes N input tokens in a single forward pass. Each token attends to all earlier tokens; attention is computed in parallel over the sequence (but linearly across layers). Output of prefill: a KV cache containing one (K, V) pair per token per attention head per layer. Decode then begins, attending into this cache. Prefill cost: O(N²) attention compute. Decode cost: O(N) attention compute per token, O(M) tokens. For long prompts (RAG context, long chats), prefill dominates total inference time.",
        "why_it_matters": "Prefill optimisation is increasingly important as context windows grow. Long-context inference (50K+ tokens) is dominated by prefill compute. Optimisations like FlashAttention (parallel within a sequence), chunked prefill (split long prefill into blocks), and prefix caching (reuse prefill across requests) all target this phase. For production serving, balancing prefill and decode workloads is a major architectural concern.",
        "example": "A team profiles their chat serving. Average request: 4K-token prompt + 200-token response. Prefill time: 800ms (compute-bound). Decode time: 600ms (200 tokens × 3ms each). Total: 1.4s. They enable prefix caching: 80% of prefill time saved on repeated system prompts. Per-request latency drops to 800ms.",
        "pitfalls": [
            "Long-prompt latency: prefill is sequential per request; long prompts mean long time-to-first-token.",
            "Memory: prefill produces large KV cache; long contexts require careful budgeting.",
            "Batch effects: mixing prefill and decode in a batch is complex; modern serving stacks (vLLM continuous batching) handle this.",
            "Compute vs bandwidth: prefill is compute-bound, decode is bandwidth-bound; different optimisation targets."
        ],
        "when_use": "Use the framing when reasoning about inference latency, optimising serving infrastructure, or designing for long-context workloads.",
        "when_avoid": "There's no good 'avoid' — prefill is a fundamental phase of any transformer inference.",
        "related_terms": ["decode-step", "kv-cache", "prefix-caching", "chunked-prefill", "flash-attention", "tokens-per-second"],
        "related_tools": ["vllm"],
        "faq": [
            {"q": "Prefill or decode bottleneck?",
             "a": "Long prompts: prefill. Long generation: decode. Most chat is decode-dominated; long-context RAG is prefill-dominated."},
            {"q": "How to speed up prefill?",
             "a": "FlashAttention for compute, prefix caching for repeated prefixes, chunked prefill to overlap with decode."},
            {"q": "Prefill cost growth?",
             "a": "Quadratic in context length for standard attention. Linear for sliding-window or linear-attention models."},
            {"q": "TTFT?",
             "a": "Time-to-first-token = prefill time + first-token decode. Prefill dominates for long prompts; decode for short."}
        ]
    },
    # 36. decode-step
    {
        "slug": "decode-step",
        "title": "Decode Step",
        "category": "infra",
        "difficulty_tier": "advanced",
        "tldr": "Second phase of LLM inference where output tokens are generated one at a time, each attending to the KV cache built during prefill.",
        "plain_english": "Decode is the slow part of inference. After prefill builds the KV cache, decode generates output tokens one at a time. Each token: attend to all cached K/V, compute logits, sample, append to context, repeat. The model runs forward pass per token — much smaller compute than prefill but sequential and memory-bandwidth-bound. Decode latency is what users perceive as 'tokens per second' in streaming.",
        "how_it_works": "Each decode step: compute Q for the new token from its embedding, retrieve K/V from cache (no recomputation), attention only between Q and the cached K/V, output logit, sample next token, append to KV cache for the next step. Compute is small per step (~1/N of prefill per layer); the bottleneck is reading the KV cache from GPU memory. Decode latency scales with cache size. Speculative decoding (predict multiple tokens, verify in parallel) is the main optimisation.",
        "why_it_matters": "Decode latency translates directly to user-perceived speed. Long contexts make decode slower (larger KV cache to read). Speculative decoding, KV cache compression, and quantization all target decode performance. For chat and streaming UX, decode optimisation matters more than prefill optimisation. Throughput in production serving is bounded by decode efficiency.",
        "example": "A coding assistant has 8K-token contexts and 500-token outputs. Prefill: 200ms. Decode: 500 tokens × 4ms = 2s. Speculative decoding (assisted generation) with a small draft model accepts 3 tokens per round; effective decode rate becomes 500/3 = 167 rounds × 5ms = 835ms. Total inference: 1s vs 2.2s. User-perceived speed doubles.",
        "pitfalls": [
            "Memory bandwidth: decode reads KV cache every token; large caches dominate latency.",
            "Long contexts: more cache to read = slower per-token; optimization needs grow with context.",
            "Batching: continuous batching across requests helps; serial decode wastes GPU.",
            "Streaming overhead: token-by-token streaming has per-token overhead; trade vs. throughput."
        ],
        "when_use": "Use the framing for reasoning about user-perceived latency, throughput optimisation, and cost per token.",
        "when_avoid": "There's no good 'avoid' — decode is fundamental to transformer inference.",
        "related_terms": ["prefill-step", "kv-cache", "speculative-decoding", "tokens-per-second", "flash-decoding", "lookahead-decoding"],
        "related_tools": ["vllm"],
        "faq": [
            {"q": "Why is decode slow?",
             "a": "Sequential dependency (each token needs prior tokens) and memory-bandwidth-bound (reading KV cache). Compute is fast but data movement bottlenecks."},
            {"q": "Speculative decoding helps?",
             "a": "Yes — generates multiple candidate tokens at once and verifies in parallel. 1.5-4× speedup typically."},
            {"q": "How to improve decode throughput?",
             "a": "KV compression, speculative decoding, continuous batching, FlashDecoding for long contexts."},
            {"q": "Tokens per second target?",
             "a": "30-100+ tok/s for chat UX on 7B models; 5-20 tok/s for 70B. Hardware and optimisation dependent."}
        ]
    },
    # 37. prefill-decode-disaggregation
    {
        "slug": "prefill-decode-disaggregation",
        "title": "Prefill-Decode Disaggregation",
        "category": "infra",
        "difficulty_tier": "advanced",
        "tldr": "Inference architecture that runs prefill and decode phases on separate hardware optimised for each — compute-heavy GPUs for prefill, memory-bandwidth-rich for decode.",
        "plain_english": "Prefill is compute-bound; decode is memory-bandwidth-bound. Running both on the same GPU sometimes wastes resources — fast compute idles during decode, fast bandwidth wastes during prefill. Disaggregation splits the phases: prefill on compute-optimised pools, decode on bandwidth-optimised pools, with KV cache transferred between them. Recent papers (DistServe, Splitwise) showed substantial throughput gains. Production deployment is increasing.",
        "how_it_works": "When a request arrives, prefill workers process the prompt and produce a KV cache. The cache is transferred (over fast interconnect) to decode workers, which generate the output token-by-token. Each phase runs on hardware tuned for its workload. The transfer is the critical engineering — KV cache is large, must move quickly. NVLink, RDMA, or specialty interconnects are typical. Schedulers route prefill and decode requests separately based on current load.",
        "why_it_matters": "At sufficient scale, disaggregation cuts inference cost meaningfully — 30-50% reductions reported in recent papers. As context windows grow and prefill becomes more compute-intensive, the case for disaggregation strengthens. Frontier inference systems (OpenAI, Anthropic, DeepSeek) likely use disaggregation in production; open-source serving (vLLM, SGLang) is adding support.",
        "example": "A team operating their own GPU cluster benchmarks prefill-decode disaggregation. With colocated prefill+decode: 100 req/s per 8×H100. Disaggregated (4 prefill + 4 decode units): 145 req/s. Per-request cost drops 30%. They migrate to disaggregated architecture for high-traffic chat workloads.",
        "pitfalls": [
            "Interconnect bandwidth: KV cache transfer can dominate latency without sufficient bandwidth (NVLink, InfiniBand).",
            "Scheduling complexity: balancing prefill vs decode load across pools is non-trivial.",
            "Cache transfer overhead: each request pays cost of moving KV; not always net positive.",
            "Implementation maturity: disaggregation in open-source serving is still nascent; production-grade implementations are rare."
        ],
        "when_use": "Use for high-scale self-hosted inference where utilisation matters and engineering capacity exists for advanced architecture.",
        "when_avoid": "Avoid for small deployments where colocation is simpler and gains don't justify complexity.",
        "related_terms": ["prefill-step", "decode-step", "kv-cache", "inference-server", "vllm", "tokens-per-second"],
        "related_tools": ["vllm"],
        "faq": [
            {"q": "Open-source disaggregation?",
             "a": "DistServe and Splitwise are reference implementations. vLLM and SGLang are adding production-grade support; check current versions."},
            {"q": "Hardware requirements?",
             "a": "Fast interconnect (NVLink, InfiniBand) is critical. Without it, transfer overhead negates benefits."},
            {"q": "When does disaggregation pay off?",
             "a": "High utilisation, mixed workload (some long prompts, some short), large clusters. Small deployments rarely benefit."},
            {"q": "Compute hierarchy?",
             "a": "Prefill prefers high-FLOPs GPUs (H100, B200). Decode prefers high-bandwidth (or large memory). Disaggregation lets you use different hardware for each."}
        ]
    },
    # 38. model-parallelism
    {
        "slug": "model-parallelism",
        "title": "Model Parallelism",
        "category": "infra",
        "difficulty_tier": "advanced",
        "tldr": "Distributed-training and inference technique that splits a single model's parameters across multiple GPUs, enabling models too large for one device.",
        "plain_english": "Data parallelism replicates the model across GPUs and splits data. Model parallelism splits the model itself across GPUs — different layers or different parts of each layer on different GPUs. Required when the model is too big for one GPU's memory. Modern training of frontier models combines model parallelism with data parallelism (3D parallelism) for both memory and throughput.",
        "how_it_works": "Two main forms. Tensor parallelism: split each layer's weights across GPUs (e.g. each GPU holds half of attention's Q matrix). Forward and backward passes coordinate across devices via collective operations (all-reduce, all-gather). Pipeline parallelism: split layers across GPUs (GPU 0 holds layers 1-8, GPU 1 holds 9-16). Activations flow through the pipeline. Megatron-LM, DeepSpeed, FSDP support various combinations. Choosing the parallelism strategy depends on model size, GPU count, and interconnect topology.",
        "why_it_matters": "Model parallelism is the difference between training/serving a 70B model on 4 GPUs (impossible without parallelism) and possible. Frontier models require sophisticated parallelism strategies — often combinations of tensor + pipeline + data + sequence parallelism. Understanding which axis to parallelise is essential for any serious LLM infrastructure work.",
        "example": "A team trains a 30B model on 8×A100 (640GB total VRAM). The model itself needs ~120GB; one GPU can't hold it. They use tensor parallelism (degree 4) for forward/backward and data parallelism (degree 2) across the resulting 2 groups. Total throughput is 60% of theoretical peak; without parallelism, training would be impossible.",
        "pitfalls": [
            "Communication overhead: collectives across GPUs add cost; faster interconnect (NVLink) crucial.",
            "Strategy choice: wrong parallelism degrees waste GPUs; profile and tune.",
            "Pipeline bubbles: imbalanced layer distribution leaves GPUs idle; balance carefully.",
            "Implementation complexity: model parallelism code is harder to debug than vanilla DDP."
        ],
        "when_use": "Use whenever a model exceeds single-GPU memory: training large models, serving frontier-scale models.",
        "when_avoid": "Avoid for small models that fit on one GPU; vanilla DDP or FSDP are simpler and cheaper.",
        "related_terms": ["fsdp", "tensor-parallelism", "pipeline-parallelism", "data-parallelism", "sequence-parallelism", "deepspeed-zero"],
        "related_tools": ["deepspeed"],
        "faq": [
            {"q": "Tensor or pipeline parallelism?",
             "a": "Tensor for compute scaling within a layer. Pipeline for memory across layers. Combine for large models."},
            {"q": "FSDP relation?",
             "a": "FSDP shards parameters/gradients/optimizer state across data parallel ranks. Different from model parallelism but sometimes used together."},
            {"q": "Strategy for 70B?",
             "a": "Common: tensor parallel 4-8 within a node, pipeline 2-4 across nodes, data parallel for batch. Tuned per cluster topology."},
            {"q": "Beginner-friendly framework?",
             "a": "Hugging Face Accelerate handles common patterns. Pure model parallelism still requires deeper engineering."}
        ]
    },
    # 39. sequence-parallelism
    {
        "slug": "sequence-parallelism",
        "title": "Sequence Parallelism",
        "category": "infra",
        "difficulty_tier": "advanced",
        "tldr": "Parallelism axis that splits a single long sequence across multiple GPUs, distributing attention computation and KV cache for very long contexts.",
        "plain_english": "Long-context training and inference push memory and compute beyond a single GPU even with model parallelism. Sequence parallelism splits the sequence dimension: different chunks of the sequence go to different GPUs, each computing its share of attention and feeding results back. Recent work (Ulysses, Ring Attention) demonstrates training and serving at million-token contexts via sequence parallelism. Becoming standard for frontier-scale long-context work.",
        "how_it_works": "Split a sequence of length N across P GPUs, each holding N/P tokens' KV. Attention requires all-to-all communication: each GPU's Q must attend to all K/V across GPUs. Different schemes (Ring Attention, Ulysses) trade off communication patterns. Activations are sharded along the sequence dimension instead of (or in addition to) the model-parallel dimensions. Frameworks like Megatron, DeepSpeed-Ulysses, and recent vLLM/SGLang versions implement variants.",
        "why_it_matters": "Million-token contexts are infeasible on single GPUs because of KV cache memory. Sequence parallelism is the path to longer contexts at production scale. As context windows grow, sequence parallelism joins tensor and pipeline parallelism as a baseline frontier-scale technique.",
        "example": "A team trains a model with 1M token context on 32×H100. Full KV cache wouldn't fit on one GPU. With sequence parallelism (degree 8) combined with tensor parallelism (degree 4), each GPU holds 1/32 of the sequence's KV. Training proceeds; throughput is significantly lower than short-context but the alternative is impossible.",
        "pitfalls": [
            "Communication-heavy: all-to-all collectives across many GPUs; interconnect quality matters.",
            "Implementation maturity: less mature than tensor/pipeline parallelism; bug-prone.",
            "Compute-comm balance: must match parallelism degree to hardware; poor matches slow training significantly.",
            "Inference patterns: sequence parallelism for inference is newer than for training; framework support limited."
        ],
        "when_use": "Use for very long context training (>100K tokens) and frontier-scale long-context inference. Combine with other parallelism axes.",
        "when_avoid": "Avoid for short contexts where simpler parallelism suffices.",
        "related_terms": ["model-parallelism", "tensor-parallelism", "pipeline-parallelism", "data-parallelism", "fsdp", "context-window"],
        "related_tools": ["deepspeed"],
        "faq": [
            {"q": "Ring Attention?",
             "a": "Specific sequence-parallel attention algorithm where K/V flow in a ring across GPUs. Used for 1M+ token training."},
            {"q": "Ulysses-style?",
             "a": "DeepSpeed-Ulysses uses all-to-all communication for sequence parallelism. Trade-offs different from ring attention; both viable."},
            {"q": "Inference support?",
             "a": "Limited but growing. vLLM and SGLang have early sequence-parallel inference; production usage still rare."},
            {"q": "How does this combine with tensor parallelism?",
             "a": "Compositionally — different axes. Tensor splits within a layer; sequence splits across the sequence. Can multiply for total memory savings."}
        ]
    },
    # 40. vision-encoder
    {
        "slug": "vision-encoder",
        "title": "Vision Encoder",
        "category": "models",
        "difficulty_tier": "intermediate",
        "tldr": "Component of a vision-language model that converts images into embedding sequences the LLM backbone can attend to alongside text.",
        "plain_english": "A vision-language model needs to turn images into something the language transformer can understand. The vision encoder does that: takes a pixel image, runs it through a vision transformer (ViT), produces a sequence of patch embeddings. These embeddings are projected (often via a small MLP) into the language model's token embedding space and concatenated with text tokens. The LLM then attends across both. Quality of the vision encoder strongly influences VLM performance.",
        "how_it_works": "Image is split into patches (e.g. 14×14 pixels). Each patch is linearly projected to a vector and gets a positional encoding. A vision transformer processes these patches with self-attention, producing a sequence of patch-level vectors. A projection module (linear layer or small MLP) maps these to the LLM's embedding dimension. The result is concatenated with text embeddings before LLM processing. Common encoders: CLIP-ViT, SigLIP, EVA-CLIP, NaViT, InternViT. Higher-quality vision encoders generally produce better VLMs.",
        "why_it_matters": "Vision encoder choice often limits VLM performance more than the language backbone. Switching to a better encoder can dramatically improve capabilities. As VLMs proliferate, vision encoder selection and fine-tuning become standard architecture decisions. Understanding the encoder helps debug when 'why isn't this VLM seeing the chart correctly?'",
        "example": "A team builds a custom VLM. With CLIP-ViT-L: 71% on VQA-v2. Switching to SigLIP-SO400M: 78% on VQA-v2 with same LLM and same fine-tuning data. The vision encoder upgrade alone added 7 points; further gains came from joint fine-tuning.",
        "pitfalls": [
            "Resolution: CLIP-style encoders work at 224x224 or 336x336; high-resolution images get downscaled; details lost.",
            "Aspect ratio: fixed aspect ratios discard image structure; NaViT and similar handle variable shapes better.",
            "Patch size trade-off: smaller patches more detail but more tokens.",
            "Encoder freeze vs. tune: training fine-tunes encoder + LLM jointly; freezing encoder loses some capability."
        ],
        "when_use": "Use the framing when designing or selecting VLMs, debugging vision quality, or comparing different VLM architectures.",
        "when_avoid": "Avoid debugging encoder choice for users — they care about end-to-end quality, not encoder details.",
        "related_terms": ["vision-language-model", "multimodal-embedding", "modality-bridge", "ocr-llm", "video-llm", "transformer"],
        "related_tools": [],
        "faq": [
            {"q": "Best vision encoder in 2026?",
             "a": "SigLIP-2, InternViT, and EVA-CLIP-2 are leading options. NaViT for variable resolutions. Pick by VLM compatibility."},
            {"q": "How many image tokens?",
             "a": "256-1024 per image is typical. Higher-resolution encoders use more tokens; balance accuracy and prompt size."},
            {"q": "Freeze or fine-tune?",
             "a": "Joint training usually wins. Freeze for fast iteration in early development; tune for production quality."},
            {"q": "Multi-resolution?",
             "a": "NaViT-style native multi-resolution helps. Otherwise crop or downscale to encoder's expected size."}
        ]
    },
    # 41. modality-bridge
    {
        "slug": "modality-bridge",
        "title": "Modality Bridge",
        "category": "models",
        "difficulty_tier": "intermediate",
        "tldr": "Architecture component that aligns embeddings from different modalities (vision, audio, text) into a shared space the LLM backbone can process.",
        "plain_english": "Multimodal models need their LLM backbone to understand non-text inputs. The modality bridge converts vision-encoder outputs (or audio, video) into the LLM's token-embedding space. Common bridges: linear projection (simple, fast), MLP (small neural net for transformation), Q-former (cross-attention learning compressed image representations). Bridge quality strongly affects multimodal performance — a strong vision encoder paired with a poor bridge underperforms.",
        "how_it_works": "After the vision encoder produces image patch embeddings (e.g. 1024 patches × 1024 dim), the bridge projects them to the LLM's embedding dim (e.g. 4096) and optionally compresses the count. Linear bridge: single matrix multiplication. MLP bridge: 2-3 layer feed-forward. Q-former (BLIP-2): learnable query tokens that cross-attend to image features, producing fixed-length compressed representation. Resampler: similar to Q-former with different attention patterns. LLaVA uses MLP; Qwen2-VL uses MLP with positional encoding tricks; BLIP-2 uses Q-former.",
        "why_it_matters": "The bridge is the alignment point between vision and language. Bridge design affects how much vision info reaches the LLM, how compressed it gets, and how well it integrates with text. As VLMs evolve, bridge sophistication grows — early models used simple projections; modern ones use learned compression mechanisms. For VLM design, bridge architecture is a critical choice.",
        "example": "A team builds a custom VLM. With linear bridge: 71% on VQA. Switching to a 2-layer MLP bridge: 73%. Adding Q-former with 32 learnable queries: 76%, but with 1/32 the image tokens — much faster inference. Trade-off between compression and quality.",
        "pitfalls": [
            "Compression vs. quality: aggressive compression loses fine details; calibrate against eval.",
            "Training stability: learned bridges (Q-former) need careful initialization.",
            "Token count budget: image tokens count against LLM context; balance image fidelity with text room.",
            "Overfitting: bridge can overfit to training distribution; verify generalisation."
        ],
        "when_use": "Use the framing when designing or selecting VLMs, optimising image-token cost, or debugging multimodal quality.",
        "when_avoid": "Avoid focusing on bridge details when end-to-end quality is the goal — encoder, bridge, and backbone all matter.",
        "related_terms": ["vision-encoder", "vision-language-model", "multimodal-embedding", "video-llm", "ocr-llm", "transformer"],
        "related_tools": [],
        "faq": [
            {"q": "Linear, MLP, or Q-former?",
             "a": "MLP is the modern default — better than linear, simpler than Q-former. Q-former for aggressive compression."},
            {"q": "Image token count budget?",
             "a": "256-1024 typical. Q-former-style compression to 32-128 saves prompt budget at quality cost."},
            {"q": "Training joint or separate?",
             "a": "Joint training of bridge + LLM is standard. Bridge usually trains faster than encoder or backbone."},
            {"q": "Multi-resolution support?",
             "a": "Some bridges (especially with positional encoding tricks) handle variable image sizes. Linear bridges don't naturally."}
        ]
    },
    # 42. vibe-coding
    {
        "slug": "vibe-coding",
        "title": "Vibe Coding",
        "category": "concepts",
        "difficulty_tier": "beginner",
        "tldr": "Workflow style where developers code primarily by describing intent in natural language and accepting LLM-generated implementations with minimal manual editing.",
        "plain_english": "'Vibe coding' was coined by Andrej Karpathy in early 2025 to describe a software development workflow centred on LLM collaboration: developer describes what they want in natural language, the LLM produces code, the developer reviews at a high level and accepts. Less typing, more directing. The term captured a real shift in how skilled developers work with capable AI coding assistants — you tell the AI the vibe, it produces the code.",
        "how_it_works": "Developer uses an AI-coding tool (Cursor, Windsurf, Claude Code, Codeium) and describes the change at a high level: 'add a search filter to the user list', 'refactor this function to use async iterators', 'fix the rate-limit handling'. The LLM produces the implementation. The developer reviews diffs at the file level, runs tests, accepts or asks for refinements. Coding is more like specifying and reviewing than typing. Works best with strong frontier models on familiar codebases; weaker models or unusual code require more manual intervention.",
        "why_it_matters": "Vibe coding represents a real productivity shift for developers using strong AI coding assistants. Time-to-implement for common tasks drops dramatically. The skill set evolves: less syntax memorisation, more architectural thinking, better at specifying requirements clearly. For engineering organisations, the practice changes how junior and senior developers contribute, how code review works, and how skills are valued.",
        "example": "A senior engineer uses Cursor in 'agent mode' to add a feature. Total typing: maybe 50 words across 30 minutes. The agent reads the codebase, plans, edits files, runs tests. The engineer reviews changes, asks for adjustments ('use async/await pattern matching the file above'), confirms. Feature ships in time it would have taken to write the spec the old way.",
        "pitfalls": [
            "Quality drift: accepting code without close review introduces subtle bugs; review remains essential.",
            "Skill atrophy: relying entirely on AI to write code can erode independent skills; balance.",
            "Codebase familiarity: works best on well-understood codebases; unfamiliar areas need more manual scrutiny.",
            "Bias toward common patterns: AI gravitates to typical solutions, missing optimal alternatives in unusual contexts."
        ],
        "when_use": "Use as a productivity multiplier for known patterns, refactors, glue code, and routine feature work — wherever specification is clearer than implementation.",
        "when_avoid": "Avoid for novel algorithm design, security-sensitive code, performance-critical hot paths, and anywhere the AI's training distribution is weak.",
        "related_terms": ["computer-use", "ai-agent", "browser-use-agent", "code-interpreter", "tool-use", "react"],
        "related_tools": [],
        "faq": [
            {"q": "Where did the term come from?",
             "a": "Andrej Karpathy popularised 'vibe coding' in early 2025 tweets describing his workflow with Cursor's agent mode."},
            {"q": "Same as agent coding?",
             "a": "Closely related — agent coding emphasises the AI's autonomous execution; vibe coding emphasises the developer's high-level direction. They overlap heavily."},
            {"q": "Replaces engineers?",
             "a": "No — multiplies productive engineers, especially senior ones who specify well. Junior development changes; broader engineering function stays critical."},
            {"q": "Best tools for vibe coding?",
             "a": "Cursor, Windsurf, Claude Code, GitHub Copilot Workspace as of 2026. Pick by workflow fit; all support agent-style assistance."}
        ]
    },
    # 43. prompt-registry
    {
        "slug": "prompt-registry",
        "title": "Prompt Registry",
        "category": "ops",
        "difficulty_tier": "intermediate",
        "tldr": "Versioned store of production prompts with metadata, A/B tests, and rollout controls — treating prompts as first-class deployable artefacts.",
        "plain_english": "Production prompts are code: they affect output, they evolve, they break things when wrong. A prompt registry treats them with the discipline of code: every prompt has a name, version, metadata (model, temperature, max tokens), test history, and deploy controls. Teams can A/B test new versions, roll back if quality drops, and audit changes. Tools like LangSmith, Helicone, Langfuse, PromptLayer ship registries.",
        "how_it_works": "Prompts are stored in a centralised repository with metadata: name, version, template variables, default model parameters, test cases, ownership. Application code references prompts by name and version (or 'latest stable'). A control plane manages deploys: which version goes to production, A/B splits, gradual rollout, instant rollback. Evaluation hooks run prompts against eval sets on every change. Audit trail captures who changed what when.",
        "why_it_matters": "Prompts in code make iteration painful — every change requires a deploy, A/B tests are hard, rollbacks are stressful. Registries decouple prompt iteration from code deployment, enabling product managers and prompt engineers to ship improvements faster. For organisations with multiple LLM features, registries are baseline infrastructure.",
        "example": "A team manages 80 production prompts across 12 products. With a registry: prompt engineer updates a summarisation prompt, runs eval suite, A/B tests 10% traffic, monitors metrics, ramps to 100% — all without code deploy. Total time from prompt idea to full rollout: hours. Without a registry, the same change would require code review, deploy windows, manual A/B setup — days.",
        "pitfalls": [
            "Versioning discipline: ad-hoc updates without versioning loses rollback ability.",
            "Latency: registry lookups per request add cost; cache aggressively.",
            "Drift: prompts drift from code expectations; type checks and template validation help.",
            "Access control: prompt registries enable broad collaboration but can expose sensitive prompts; audit access."
        ],
        "when_use": "Use for production LLM systems with multiple prompts, multiple products, or non-engineer prompt iterators.",
        "when_avoid": "Avoid for single-prompt prototypes; the overhead exceeds benefit for tiny systems.",
        "related_terms": ["prompt-versioning", "evaluation-pipeline", "ai-observability", "gradual-rollout", "canary-deployment-llm", "model-routing"],
        "related_tools": ["langfuse", "helicone"],
        "faq": [
            {"q": "Build or buy a registry?",
             "a": "Buy for fast start (Helicone, Langfuse, LangSmith all ship registries). Build for unique workflows after the off-the-shelf hits limits."},
            {"q": "Who manages prompts?",
             "a": "Often product managers, prompt engineers, or domain experts — the registry decouples this from engineering."},
            {"q": "Eval integration?",
             "a": "Critical — registries should run prompts against eval sets automatically. Block deploys on quality regressions."},
            {"q": "A/B testing built-in?",
             "a": "Most modern registries support A/B traffic split. Cohort tracking and metric collection are also typically included."}
        ]
    },
    # 44. prompt-versioning
    {
        "slug": "prompt-versioning",
        "title": "Prompt Versioning",
        "category": "ops",
        "difficulty_tier": "beginner",
        "tldr": "Practice of treating prompt edits like code commits — each version has a unique identifier, change history, and the ability to roll back.",
        "plain_english": "Prompts evolve. Without versioning, you can't tell which version produced last week's results, can't roll back if a change regresses quality, and can't A/B test old vs. new. Prompt versioning gives each prompt edit a unique version ID, stores the diff history, and tags versions for environments (staging, production). Production code references specific versions; rolling back means pointing at an older version. Combined with a prompt registry, it's the foundation of managed prompt deployment.",
        "how_it_works": "Each prompt edit creates a new version with metadata: version ID (semver or hash), timestamp, author, change reason, parent version. Versions are immutable once published. Application code references either a specific version ('@v2.1.0') or an alias ('@latest-stable'). Rolling back is updating the alias. Diff views show what changed between versions. Test history attaches to versions: each version has eval scores, A/B test results, and production metrics. Tools (LangSmith, Helicone, Langfuse) ship versioning natively.",
        "why_it_matters": "Without versioning, prompt iteration is risky — changes ship and you can't easily undo. Versioning gives the same safety net as code deployment: roll back if needed, audit what changed, compare versions on metrics. For production LLM systems, versioning is baseline operational hygiene.",
        "example": "A summarisation prompt regresses on production traffic — user thumbs-down rate doubles. Engineering checks versioning: yesterday's deploy was @v3.4.1. Roll back to @v3.4.0: thumbs-down returns to baseline within 5 minutes. Without versioning, the team would need to reconstruct the previous prompt from git history (if it existed) and redeploy — much slower.",
        "pitfalls": [
            "Drift between code and registry: stale references break production; CI checks for unknown versions.",
            "Aliases can mask issues: 'latest-stable' updates change behaviour invisibly; track changes.",
            "Storage growth: every edit creates a version; old versions accumulate; archival policy needed.",
            "Branching/merging: complex multi-team workflows need branching primitives most registries don't fully support."
        ],
        "when_use": "Use for any production LLM system with non-trivial prompts. Standard hygiene.",
        "when_avoid": "Avoid only for single-prompt prototypes that won't see production.",
        "related_terms": ["prompt-registry", "evaluation-pipeline", "ai-observability", "gradual-rollout", "canary-deployment-llm", "data-flywheel"],
        "related_tools": ["langfuse"],
        "faq": [
            {"q": "Semver or hashes?",
             "a": "Semver for human-readable. Hashes for unique identification. Many registries use both."},
            {"q": "How granular?",
             "a": "Per-prompt versioning. Sub-prompt versions (system message, examples) sometimes versioned separately."},
            {"q": "Rollback speed?",
             "a": "Should be instant — just update the alias. Slow rollback defeats the purpose."},
            {"q": "Migration from code-stored prompts?",
             "a": "Extract prompts to a registry, replace literals with version references. One-time work; pays off immediately."}
        ]
    },
    # 45. evaluation-pipeline
    {
        "slug": "evaluation-pipeline",
        "title": "Evaluation Pipeline",
        "category": "ops",
        "difficulty_tier": "intermediate",
        "tldr": "Automated workflow that runs LLM systems against eval sets on every change, computing quality metrics and gating deploys on regressions.",
        "plain_english": "Continuous integration for LLM systems. An evaluation pipeline is the automated step in CI that runs your prompts, agents, or fine-tunes against eval sets after every change — model swap, prompt update, code change. It computes quality metrics (accuracy, latency, cost), compares to baselines, and blocks deploys on regressions. Without it, quality degrades silently between releases.",
        "how_it_works": "On each change (or scheduled), the pipeline: (1) fetches the system under test (current code, current prompts, current model), (2) runs against the eval set, (3) computes metrics per dimension (accuracy, faithfulness, latency, cost), (4) compares against baseline (last green run), (5) reports diff and pass/fail decision. CI integrates with the pipeline as a required check; deploys gate on it. Tools (Promptfoo, DeepEval, Langfuse, custom) ship pipelines or integrate with CI providers.",
        "why_it_matters": "Manual evaluation doesn't scale. As LLM systems grow more complex (RAG, agents, multi-step), regressions are easy to introduce and hard to spot. Automated pipelines catch regressions at PR time, before users see them. They also let teams iterate confidently — change prompts, model, or code knowing eval will catch problems.",
        "example": "A team's chat product has 200-question eval set. Every PR triggers the pipeline: run the assistant against all 200 questions, score against gold answers and judge model. Block merge on >2% accuracy regression. Over a year, the pipeline catches 14 regressions before they shipped — each was a quick fix-and-retry rather than a customer-impacting incident.",
        "pitfalls": [
            "Eval-set staleness: pipelines optimise for the eval set; refresh periodically and add adversarial examples.",
            "Compute cost: large eval sets per PR are expensive; sample for fast PRs, full run on merge.",
            "Flakiness: non-deterministic outputs cause false alarms; use multiple seeds and tolerance ranges.",
            "Goodhart: over-reliance on the pipeline can blind teams to issues outside the eval set."
        ],
        "when_use": "Use for any production LLM system. Critical for systems with multiple iterators (engineers, prompt managers, ML).",
        "when_avoid": "Don't skip for production deployments; manual eval is unreliable at scale.",
        "related_terms": ["evaluation-set", "ai-observability", "rag-evaluation", "prompt-versioning", "gradual-rollout", "agent-evaluation"],
        "related_tools": ["promptfoo", "deepeval"],
        "faq": [
            {"q": "Promptfoo, DeepEval, custom?",
             "a": "Promptfoo for prompt-focused; DeepEval for RAG/agents; custom for unusual eval logic. Mix as needed."},
            {"q": "Eval-set size?",
             "a": "100-1000 questions typical. Bigger is more reliable but slower; sample for fast feedback during PRs."},
            {"q": "What metrics?",
             "a": "Per task: accuracy, faithfulness, format compliance, latency, cost. Track trends over time, not just absolute."},
            {"q": "Blocking vs warning?",
             "a": "Block significant regressions; warn on minor ones. Calibrate thresholds against noise floor."}
        ]
    },
    # 46. gradual-rollout
    {
        "slug": "gradual-rollout",
        "title": "Gradual Rollout",
        "category": "ops",
        "difficulty_tier": "beginner",
        "tldr": "Deployment strategy that ramps a new version's traffic share from 0% to 100% over time, monitoring metrics for regressions before full exposure.",
        "plain_english": "Big-bang deploys are risky. Gradual rollout starts the new version at 1% of traffic, watches metrics, ramps to 5%, 25%, 100% over hours or days. If metrics regress at any stage, rollback is fast and bounded — only that small percentage of users was affected. Combined with feature flags and canary testing, it's how mature teams ship LLM changes safely.",
        "how_it_works": "Configure the new version (model, prompt, code) but route traffic via a control: feature flag, A/B router, or load-balancer rule. Start at small percentage (1-5%). Monitor business and quality metrics: thumbs-up/down, latency, error rate, cost. If green for a fixed bake period (hours to a day), ramp up. Stages typically: 1% → 5% → 25% → 50% → 100%. Each stage can take minutes (low-risk changes) or days (high-risk). Automated rollback triggers on metric breaches.",
        "why_it_matters": "LLM changes can degrade quality in non-obvious ways — hallucination rate up, user satisfaction down, cost spike. Gradual rollout limits blast radius and provides observability. For production systems with real users, gradual rollout is the standard safe-deploy pattern. Combined with eval pipelines, it's defense-in-depth: eval catches obvious issues; rollout catches subtle ones.",
        "example": "A team rolls out a new chat fine-tune. Stage 1: 1% traffic for 4 hours — green. Stage 2: 5% for 4 hours — slight cost increase but acceptable. Stage 3: 25% for 24 hours — caught: response length increased 15% (cost up), but thumbs-up rate also up. Decision: continue, accept cost in exchange for quality. Stage 4: 100% over 12 hours.",
        "pitfalls": [
            "Bake time too short: subtle regressions take days to surface; don't rush stages.",
            "Sample size: 1% of small traffic isn't statistically significant; size stages to your traffic.",
            "Cohort consistency: same user should hit same version within a session; sticky routing.",
            "Metric latency: some quality signals (thumbs-up) take time to accumulate; align bake periods."
        ],
        "when_use": "Use for any production deploy with non-trivial risk: model swaps, major prompt changes, agent architecture updates, fine-tune releases.",
        "when_avoid": "Avoid for trivial low-risk changes (typo fixes); overhead exceeds benefit.",
        "related_terms": ["canary-deployment-llm", "shadow-deployment-llm", "ai-observability", "evaluation-pipeline", "prompt-versioning", "data-flywheel"],
        "related_tools": [],
        "faq": [
            {"q": "Stages typical?",
             "a": "1% → 5% → 25% → 50% → 100% is common. Adjust to traffic volume and risk tolerance."},
            {"q": "Bake period per stage?",
             "a": "Hours for low-risk, days for high-risk. Match the time it takes for relevant metrics to accumulate."},
            {"q": "Automated rollback?",
             "a": "Yes — trigger on metric breaches automatically. Faster than manual response; prevents bad versions from ramping."},
            {"q": "Same as canary?",
             "a": "Closely related. Canary is the first small slice; gradual rollout is the multi-stage ramp. Canary is part of gradual rollout."}
        ]
    },
    # 47. olmo
    {
        "slug": "olmo",
        "title": "OLMo",
        "category": "models",
        "difficulty_tier": "intermediate",
        "tldr": "Allen Institute for AI's fully open-source LLM family — releases include weights, training code, training data, and full reproducibility documentation.",
        "plain_english": "Most 'open-source' LLMs release only weights. OLMo (Open Language Model) goes further: AI2 publishes the model weights, training code, training data (Dolma corpus), checkpoints, and detailed methodology. Researchers can reproduce results, study training dynamics, and inspect what the model learned. Since the original OLMo, OLMo-2 and subsequent versions have continued the radical-transparency stance. For research and trust-sensitive deployments, OLMo is uniquely auditable.",
        "how_it_works": "AI2 releases the full training pipeline: Dolma dataset (~3T tokens of curated web/books/code/papers), training code (PyTorch + Megatron-style parallelism), every intermediate checkpoint, full training logs, evaluation scripts, and reproducibility documentation. Anyone with sufficient compute can retrain. The trained models (1B, 7B, 13B variants) are competitive with similarly-sized open models. Reasoning and instruction-tuned variants are also released.",
        "why_it_matters": "Most open-weight models are black boxes — you have weights but no way to study how they got there. OLMo enables genuine research: studying training dynamics, attribution of capabilities to specific data, replication of results. For regulated industries that need to know what their model was trained on, OLMo's transparency is uniquely valuable. It also serves as a reference implementation for the open-source community.",
        "example": "A research group studies emergent capabilities. Using OLMo's published checkpoints (every 1B tokens during training), they trace when math reasoning ability appears, correlate it with specific training data shifts, and publish findings. This kind of analysis is impossible with closed-weights models or partially-open ones.",
        "pitfalls": [
            "Quality vs. closed-data competitors: OLMo's data is fully transparent, which excludes some sources used by closed models; quality slightly lower at same scale.",
            "Training compute: reproducing OLMo requires substantial GPU resources; cost-prohibitive for most.",
            "Documentation drift: as the AI2 team releases new versions, older tooling can break.",
            "Limited fine-tunes: ecosystem of OLMo-based fine-tunes is smaller than Llama or Mistral."
        ],
        "when_use": "Use for research, education, regulated deployments requiring full data transparency, or as reference implementation for understanding LLM training.",
        "when_avoid": "Avoid for production where slight quality differences vs. Llama/Mistral matter and full transparency isn't required.",
        "related_terms": ["pretraining", "data-mixture", "fine-tuning", "open-weights-vs-open-source", "ai-governance", "datasheet"],
        "related_tools": [],
        "faq": [
            {"q": "OLMo or Llama?",
             "a": "Llama for production quality and ecosystem. OLMo for transparency, research, and regulated deployments."},
            {"q": "Dolma dataset?",
             "a": "AI2's curated 3T-token corpus released alongside OLMo. Used to train OLMo; available for other open training projects."},
            {"q": "OLMo-2?",
             "a": "Updated release with better quality, refined dataset, and continued transparency. Recommended over OLMo-1 for new work."},
            {"q": "Full reproducibility?",
             "a": "Yes — with sufficient compute. AI2 has demonstrated reruns producing similar results; the closest the community has to reproducible LLM training."}
        ]
    },
    # 48. gpt-oss
    {
        "slug": "gpt-oss",
        "title": "GPT-OSS",
        "category": "models",
        "difficulty_tier": "intermediate",
        "tldr": "OpenAI's open-weights model family released in 2025, providing GPT-line technology under permissive licensing for self-hosting and research.",
        "plain_english": "GPT-OSS is OpenAI's open-weights release — weights downloadable, runnable locally, with a permissive license. Unlike OpenAI's API models (GPT-4, GPT-5), GPT-OSS lets you self-host, fine-tune, study internals. Quality is positioned between mainstream Llama-tier open models and frontier API models. The release marked a significant shift: OpenAI joining Meta, Google, Mistral, and DeepSeek in the open-weights landscape.",
        "how_it_works": "OpenAI publishes weights for one or more sizes (typically 7B-70B range), with documentation covering architecture, training data summaries (often less detailed than fully-open releases like OLMo), and fine-tuning recipes. The license permits commercial use within stated terms. Inference works in standard stacks (vLLM, TGI, llama.cpp). Fine-tuning ecosystem grows rapidly post-release. Smoke-tests and red-team reports often accompany the release for transparency.",
        "why_it_matters": "An OpenAI open release substantially shifted competitive dynamics. Other labs face pressure to match; downstream developers gain a new option. For self-hosting, regulated industries, and academic research, GPT-OSS is a viable alternative to API-locked models. Fine-tunes targeting specific domains have become widespread; the ecosystem matures rapidly.",
        "example": "A regulated industry team needs to keep customer data on-premises. Pre-GPT-OSS: choose Llama or DeepSeek for self-hosting. Post-release: also evaluate GPT-OSS — quality benchmarks indicate it matches their needs. They fine-tune on internal data and deploy on internal GPU clusters; data never leaves their environment.",
        "pitfalls": [
            "License terms: permissive but with stated boundaries (commercial use, attribution, model-weights distribution); read carefully.",
            "Less transparent than fully-open: training data summaries are typical rather than full datasets.",
            "Smaller than frontier API models: GPT-OSS is designed for self-hosting and is not necessarily the highest-quality OpenAI model.",
            "Fine-tuning ecosystem maturity: lags Llama which has had years of community work."
        ],
        "when_use": "Use for self-hosted deployments where OpenAI-line technology is preferred, regulated environments needing on-prem, or research on OpenAI architectures.",
        "when_avoid": "Avoid when API-tier quality is essential or when Llama/DeepSeek/Qwen meet needs at lower licensing complexity.",
        "related_terms": ["fine-tuning", "open-weights-vs-open-source", "ai-model-license", "inference-server", "olmo", "ai-governance"],
        "related_tools": ["vllm"],
        "faq": [
            {"q": "GPT-OSS sizes?",
             "a": "Varies by release; typical range 7B-70B. Check current AAP-OSS announcements for specific sizes."},
            {"q": "GPT-OSS or Llama?",
             "a": "Compare on your eval. Both are strong; ecosystem and license terms differ. Pick by deployment fit."},
             {"q": "Commercial use OK?",
             "a": "Per license terms; typically yes within stated boundaries. Legal review for your use case is prudent."},
             {"q": "Fine-tuning?",
             "a": "Standard PyTorch/Hugging Face workflows. Quality depends on data and recipe; expect ongoing community refinement."}
        ]
    },
    # 49. airgapped-llm
    {
        "slug": "airgapped-llm",
        "title": "Air-Gapped LLM",
        "category": "infra",
        "difficulty_tier": "intermediate",
        "tldr": "LLM deployment on a network with no external connectivity — required for classified, regulated, or maximally-sensitive environments.",
        "plain_english": "Some environments can't connect to external APIs at all: classified government, healthcare cloud-prohibited, financial high-security. Air-gapped LLMs run entirely on isolated hardware, often a private network with no internet access. Models, weights, and inference infrastructure are imported via secure media; once running, no data flows out. Deploying LLMs in these contexts requires self-hosted open-weights models, careful supply-chain validation, and offline capability.",
        "how_it_works": "Choose an open-weights model (Llama, Mistral, GPT-OSS, OLMo). Validate supply chain: signed checkpoints, content hashes, threat-model the model itself. Transfer to air-gapped network via approved media (one-way diodes, signed USB drives). Deploy inference stack (vLLM, TGI) in the isolated environment. Updates require a manual transfer process. Monitoring and logging stay within the air-gapped network. Fine-tuning happens on-premises with on-premises data.",
        "why_it_matters": "Many high-stakes deployments cannot use cloud APIs — regulatory, security, or contractual reasons. Air-gapped deployment is the only path for these. As LLMs become essential, the demand for air-gapped solutions grows. Industries and governments have built specialised practices and certified hardware around air-gapped AI deployment.",
        "example": "A defence contractor builds an internal coding assistant for classified projects. They cannot use cloud APIs. They deploy a Llama 70B fine-tune on an air-gapped GPU cluster, with code coming in and answers going out through a one-way data diode. Updates require physical media transfer through approved processes. The system passes security audit because no data ever crossed boundaries.",
        "pitfalls": [
            "Update friction: model and infrastructure updates require approved transfer; lag behind public state-of-the-art.",
            "Monitoring opacity: external observability tools usually unavailable; rely on on-prem stacks.",
            "Supply-chain risk: backdoored model weights are a real threat in air-gapped contexts; verification is critical.",
            "Cost: dedicated hardware, manual processes, security infrastructure all add up."
        ],
        "when_use": "Use for classified, defence, regulated healthcare, financial-high-security, or contractually-isolated deployments where external connectivity is prohibited.",
        "when_avoid": "Avoid for normal commercial deployments where managed services or hybrid cloud are operationally simpler and policy-permitted.",
        "related_terms": ["ai-governance", "open-weights-vs-open-source", "inference-server", "olmo", "gpt-oss", "ai-model-license"],
        "related_tools": ["vllm"],
        "faq": [
            {"q": "Best model for air-gapped?",
             "a": "Llama, Mistral, Qwen, OLMo, GPT-OSS — any open-weights model. Pick by quality, license, and supply-chain verification feasibility."},
            {"q": "Update cadence?",
             "a": "Weeks to months typical. Manual processes, security review, and certification slow updates significantly."},
            {"q": "Supply-chain validation?",
             "a": "Critical — verify weights via cryptographic signatures, hash content, and run safety tests before deployment."},
            {"q": "Monitoring options?",
             "a": "On-prem only — Langfuse self-hosted, Phoenix self-hosted, Prometheus + Grafana for infrastructure metrics."}
        ]
    },
    # 50. extended-context
    {
        "slug": "extended-context",
        "title": "Extended Context",
        "category": "concepts",
        "difficulty_tier": "intermediate",
        "tldr": "Practice of training or extending models to handle context windows substantially longer than their pretraining context, via position encoding tricks and continued training.",
        "plain_english": "Pretraining context windows are typically 4K-32K tokens. Extended context pushes beyond — 128K, 1M, even 10M tokens. The challenge: position embeddings and attention patterns trained for shorter context don't naturally generalise. Extended context techniques include RoPE scaling (NTK-aware, YaRN), position interpolation, continued pretraining on longer sequences, and architectural changes for sparse/sliding attention. Modern models (Claude 3.5 Sonnet, Llama 3.1 405B) ship with extended context as a primary feature.",
        "how_it_works": "Several techniques. (1) Position interpolation: stretch position indices so a model trained on 4K tokens treats 128K positions as similar. (2) NTK-aware scaling: adjust RoPE frequency base to handle longer sequences. (3) YaRN: combines interpolation with frequency-dependent scaling. (4) Continued pretraining: fine-tune on long-sequence data with the new positional setting. (5) Architectural: sliding-window attention, sparse attention, or SSM components for sub-quadratic scaling at long context. Production models combine techniques.",
        "why_it_matters": "Long context unlocks workloads that were previously infeasible: full-document analysis, multi-hour video understanding, codebase-wide reasoning, long-conversation memory. Extended-context capabilities are increasingly differentiating; users expect 100K+ context as table stakes for premium models. Knowing the techniques helps teams choose models, fine-tune for longer context, or extend their own bases.",
        "example": "A team takes Llama 3 8B (8K native context) and extends to 128K via YaRN scaling + continued pretraining on a 50B-token long-context corpus. Performance on long-context evals (NIAH, RULER) holds well; inference cost grows but stays manageable with KV compression. The 16× context extension cost ~$5K compute; the resulting model handles document workloads the base couldn't touch.",
        "pitfalls": [
            "Lost-in-the-middle: longer contexts often miss information in the middle; benchmark this specifically.",
            "Memory cost: KV cache scales linearly with context; long contexts require kv-cache compression for production serving.",
            "Quality vs. length: extending too aggressively without continued training degrades quality at the long end.",
            "Eval coverage: standard benchmarks don't test 100K+ context; use NIAH, RULER, or custom evals."
        ],
        "when_use": "Use the framing when working with long-document workloads, multi-document RAG, long-conversation assistants, or research on long-context capabilities.",
        "when_avoid": "Avoid for short-context tasks where extending adds complexity and cost without benefit.",
        "related_terms": ["context-window", "long-context-benchmark", "rope", "kv-cache-compression", "attention-sink", "long-context-rag"],
        "related_tools": [],
        "faq": [
            {"q": "Best extension technique?",
             "a": "YaRN combined with continued pretraining is the modern default. Pure interpolation works for modest extensions."},
            {"q": "How much continued pretraining?",
             "a": "Tens of billions of tokens for serious extension. Smaller fine-tunes give partial extension; quality varies."},
            {"q": "Lost-in-the-middle?",
             "a": "Real phenomenon. Models miss info buried in long contexts. Mitigations: ordering by relevance, hierarchical summarisation, attention-sink retention."},
            {"q": "Cost of long-context inference?",
             "a": "Significant. Per-request memory and compute scale with context length. KV compression and quantization are essential for production."}
        ]
    },
]

# ─────────────────────────── Generation logic ───────────────────────────

def make_meta_title(title):
    s = f"{title} — Plain-English Definition & Expert Guide | OSS AI Hub"
    return s if len(s) <= 120 else f"{title} — Definition | OSS AI Hub"

def make_meta_description(tldr):
    return tldr[:200] if len(tldr) > 200 else tldr

def make_jsonld(slug, title, tldr):
    return {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "name": title,
        "description": tldr,
        "inDefinedTermSet": "https://ossaihub.com/Glossary",
        "url": f"https://ossaihub.com/glossary/{slug}",
        "termCode": slug,
    }

def make_seo_variations(title, slug):
    return [title.lower(), slug.replace("-", " ")]

def finalise_term(rec):
    rec.setdefault("meta_title", make_meta_title(rec["title"]))
    rec.setdefault("meta_description", make_meta_description(rec["tldr"]))
    rec.setdefault("schema_jsonld", make_jsonld(rec["slug"], rec["title"], rec["tldr"]))
    rec.setdefault("seo_variations", make_seo_variations(rec["title"], rec["slug"]))
    rec.setdefault("rewrite_version", "v2")
    rec.setdefault("rewritten_at", NOW)
    rec.setdefault("short_definition", rec["tldr"])
    rec.setdefault("full_explanation", rec["how_it_works"])
    rec.setdefault("common_misconceptions", "")
    rec.setdefault("related_tools", [])
    return rec

REQUIRED_FIELDS = [
    "slug", "title", "category", "difficulty_tier",
    "tldr", "plain_english", "how_it_works", "why_it_matters",
    "example", "pitfalls", "when_use", "when_avoid",
    "related_terms", "faq", "meta_title", "meta_description",
]

def validate_terms(terms, existing_slugs):
    errors = []
    seen = set()
    for rec in terms:
        slug = rec.get("slug", "?")
        for f in REQUIRED_FIELDS:
            if not rec.get(f):
                errors.append(f"{slug}: missing or empty {f}")
        if not SLUG_RE.match(slug):
            errors.append(f"{slug}: bad slug shape")
        if slug in seen:
            errors.append(f"{slug}: duplicate within batch")
        seen.add(slug)
        if slug in existing_slugs:
            errors.append(f"{slug}: collides with existing slug")
        if len(rec.get("tldr", "").split()) > 30:
            errors.append(f"{slug}: tldr > 30 words")
        p = rec.get("pitfalls", [])
        if not (2 <= len(p) <= 4):
            errors.append(f"{slug}: pitfalls count {len(p)} not in 2-4")
        f = rec.get("faq", [])
        if not (3 <= len(f) <= 5):
            errors.append(f"{slug}: faq count {len(f)} not in 3-5")
        for i, qa in enumerate(f):
            if not qa.get("q") or not qa.get("a"):
                errors.append(f"{slug}: faq[{i}] missing q or a")
        mt = rec.get("meta_title", "")
        if len(mt) > 120:
            errors.append(f"{slug}: meta_title len {len(mt)} > 120")
        md = rec.get("meta_description", "")
        if len(md) > 200:
            errors.append(f"{slug}: meta_description len {len(md)} > 200")
        body = " ".join(str(rec.get(k, "")) for k in ("tldr", "plain_english", "how_it_works", "why_it_matters", "example", "when_use", "when_avoid")).lower()
        for bw in BANNED:
            if bw in body:
                errors.append(f"{slug}: contains banned word '{bw}'")
    return errors

EXCLUDE_SLUGS = set()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--emit-only", action="store_true")
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()
    if not (args.merge or args.emit_only or args.validate_only):
        print("Pick --merge, --emit-only, or --validate-only", file=sys.stderr); sys.exit(2)
    if not REBUILT.exists():
        print(f"ERROR: {REBUILT} not found", file=sys.stderr); sys.exit(2)

    existing = json.loads(REBUILT.read_text(encoding="utf-8"))
    existing_slugs = {t.get("slug") for t in existing if t.get("slug")}

    kept = [t for t in TERMS if t["slug"] not in EXCLUDE_SLUGS]
    if len(kept) != 50:
        print(f"ERROR: expected 50, got {len(kept)} (TERMS={len(TERMS)}, excluded={len(EXCLUDE_SLUGS)})", file=sys.stderr); sys.exit(2)

    finalised = [finalise_term(dict(t)) for t in kept]
    errors = validate_terms(finalised, existing_slugs)
    if errors:
        print(f"VALIDATION FAILED — {len(errors)} issues:")
        for e in errors[:30]:
            print(f"  {e}")
        sys.exit(1)
    print(f"VALIDATION OK — {len(finalised)} new terms, no dupes against {len(existing_slugs)} existing")

    if args.validate_only:
        return

    if args.emit_only:
        OUT_NEW_ONLY.write_text(json.dumps(finalised, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {len(finalised)} terms to {OUT_NEW_ONLY}")
        return

    if args.merge:
        merged = existing + finalised
        REBUILT.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Merged: {len(existing)} existing + {len(finalised)} new = {len(merged)} total")
        OUT_NEW_ONLY.write_text(json.dumps(finalised, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Also wrote new-only file to {OUT_NEW_ONLY}")

if __name__ == "__main__":
    main()

