"""Analysis prompt library — v2 authored (2026-05-14)."""

RECORDS = [
    {
        "slug": "a-b-test-result-interpreter",
        "title": "A/B Test Result Interpreter (statistical + practical)",
        "category": "analysis",
        "tldr": "Given A/B test data (conversion rates, sample sizes, CI), produce plain-English interpretation, distinguish statistical vs practical significance, recommend ship/extend/kill.",
        "tags": ["a-b-test", "statistics", "experimentation"],
        "best_for_tags": ["experimentation", "growth", "stats"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "full_prompt": (
            "You interpret A/B test results for product/growth teams. Be rigorous about stats and brutal about practical significance — most 'wins' don't matter at the business level.\n\n"
            "INPUTS:\n"
            "- variants: list of {label, sample_size, conversion_count, conversion_rate}\n"
            "- baseline_label: which variant is control\n"
            "- primary_metric: name + unit (e.g., 'signup_rate', 'pp')\n"
            "- guardrail_metrics (optional): secondary metrics with their deltas\n"
            "- business_context: minimum lift threshold to bother shipping (e.g., '0.5pp absolute or 5% relative')\n"
            "- test_duration_days, run_start_date, run_end_date\n\n"
            "PROCEDURE:\n"
            "1. Compute relative + absolute lift per variant vs baseline.\n"
            "2. Compute z-test 2-proportion confidence interval at 95%. State CI bounds.\n"
            "3. Distinguish statistical significance (CI excludes zero) from practical significance (lift > business threshold).\n"
            "4. Check guardrails: any negative delta? Any sample-size imbalance >5%?\n"
            "5. Recommend: SHIP / EXTEND / KILL / INCONCLUSIVE — with reasoning.\n"
            "6. List confounders: novelty effect (was duration <14d?), seasonality, segment effects (if data provided).\n\n"
            "OUTPUT FORMAT: markdown — Headline (1 sentence), Numbers table, Significance verdict, Guardrail check, Recommendation, Confounders, Open questions.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "variants", "type": "list[Variant]", "description": "Each variant's sample + conversions", "required": True, "example": "[{label:'Control', sample_size:12450, conversion_count:1245, conversion_rate:10.0}, {label:'B-new-cta', sample_size:12380, conversion_count:1361, conversion_rate:11.0}]"},
            {"name": "baseline_label", "type": "string", "description": "Control variant", "required": True, "example": "Control"},
            {"name": "primary_metric", "type": "string", "description": "Metric being optimized", "required": True, "example": "signup_rate (pp)"},
            {"name": "business_context", "type": "string", "description": "Lift threshold to bother shipping", "required": True, "example": "Min 5% relative lift to ship."},
            {"name": "guardrail_metrics", "type": "list[Guardrail]", "description": "Secondary metrics to check", "required": False, "example": "[{name:'7-day-retention', control:0.62, variant:0.58, delta_significant:true}]"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Headline\nVariant B beat Control by +1.0pp absolute (10.0% lift), statistically significant, but watch the 7-day retention guardrail.\n\n## Numbers\n| Variant | N | Conversions | Rate | Δ abs | Δ rel | 95% CI (Δ abs) |\n|---|---|---|---|---|---|---|\n| Control | 12,450 | 1,245 | 10.0% | — | — | — |\n| B-new-cta | 12,380 | 1,361 | 11.0% | +1.0pp | +10.0% | [+0.2pp, +1.8pp] |\n\n## Significance\n- Statistical: ✅ CI excludes 0\n- Practical: ✅ +10% relative exceeds your 5% threshold\n\n## Guardrails ⚠️\n- 7-day retention dropped 0.62 → 0.58 (-4pp). Significant.\n\n## Recommendation: EXTEND\nThe primary-metric win is real, but retention guardrail is concerning. Extend by 2 weeks to confirm retention isn't a novelty artifact. If retention recovers → SHIP. If sustained → KILL despite the conversion win."},
        "use_cases": [
            {"scenario": "Weekly experiment review", "example": "Product team's experiment review meeting; this prompt produces the v1 decision memo for each test."},
            {"scenario": "Junior PM training", "example": "PM proposes ship/kill; prompt's recommendation is the check. Diff is the learning."},
            {"scenario": "Marketing campaign A/B", "example": "Email subject-line test results; quick verdict on whether to scale."},
            {"scenario": "Pricing experiment", "example": "Long-running pricing test; the prompt distinguishes novelty effect from durable lift."},
        ],
        "when_not_to_use": "Don't use for multi-armed bandits or sequential testing — those need different stats. Also skip when sample size <500 per arm; results are too noisy.",
        "few_shot_examples": [
            {
                "input": "variants: Control 8500/850 (10.0%), B 8200/873 (10.6%). Min lift: 5% rel. Duration: 7 days. No guardrail signals.",
                "output": "## Headline\nVariant B beat Control by +0.6pp absolute (+6% relative); statistically marginal, practically thin.\n\n## Numbers\n| Variant | N | Conv | Rate | Δ abs | Δ rel | 95% CI |\n|---|---|---|---|---|---|---|\n| Control | 8,500 | 850 | 10.0% | — | — | — |\n| B | 8,200 | 873 | 10.6% | +0.6pp | +6.0% | [-0.1pp, +1.3pp] |\n\n## Significance\n- Statistical: ⚠️ CI includes 0 (just barely)\n- Practical: marginal (+6% just clears your 5% threshold)\n\n## Recommendation: EXTEND\n7 days is too short — likely novelty effect. Extend 2 weeks and re-evaluate.\n\n## Confounders\n- Test duration 7 days is below the 14-day novelty-effect threshold.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strong at the statistical vs practical distinction."},
            {"model": "gpt-5", "compatibility": "excellent", "notes": "Reliable CI computation."},
            {"model": "claude-haiku-4-5", "compatibility": "good", "notes": "Cheap for batch interpretation of many tests."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Stats can drift; verify CI manually."},
        ],
        "variations": [
            {"label": "Bayesian framing", "description": "Use posterior probability instead of frequentist CI.", "prompt_snippet": "Replace CI with 'P(B > Control) = X%' framing. Use Beta priors with sample = pseudo-counts (5,5)."},
            {"label": "Segment-aware", "description": "Drill into segment-level lift.", "prompt_snippet": "Add INPUT: segment_breakdown (variant × segment matrix). Output per-segment lift; flag Simpson's paradox if overall lift sign differs from segment-level signs."},
            {"label": "Multiple-test correction", "description": "When running 5+ tests in parallel.", "prompt_snippet": "Apply Bonferroni or BH correction. Reduce effective alpha to 0.05/n_tests; recompute CI bounds."},
        ],
        "failure_modes": [
            {"symptom": "Conflates statistical significance with practical significance", "fix": "Always report both separately; require lift exceeds business_context threshold for 'SHIP' recommendation"},
            {"symptom": "Ignores guardrail metrics", "fix": "Hard rule: any significant guardrail regression → recommendation is EXTEND minimum, not SHIP"},
            {"symptom": "Misses sample-size imbalance >5% (assignment bug)", "fix": "Check N delta; if >5%, flag 'assignment imbalance — debug before trusting results'"},
            {"symptom": "Doesn't account for short-duration novelty effect", "fix": "Flag tests <14 days as 'novelty risk' in Confounders"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-haiku-4-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["support-ticket-triage", "strategic-tradeoff-analyzer"],
        "related_tool_slugs": ["statsig", "growthbook", "amplitude"],
        "related_glossary_slugs": ["statistical-significance", "confidence-interval", "ab-testing"],
        "faq": [
            {"question": "What's a 'practical significance' threshold?", "answer": "Depends on the metric. For top-of-funnel: 5-10% relative lift. For revenue: 1-2% can matter at scale. Set it in business_context."},
            {"question": "How do I handle ties?", "answer": "If CI includes 0 and lift < 1.5× business threshold: INCONCLUSIVE. Re-run with more data or kill."},
            {"question": "Can it do sequential / Bayesian?", "answer": "Frequentist by default. Use the Bayesian-framing variation for that style."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "A/B Test Result Interpreter — Statistical + Practical",
        "meta_description": "Interpret A/B test results with CI, guardrail checks, novelty-effect flags, and SHIP/EXTEND/KILL recommendation.",
    },

    {
        "slug": "cohort-retention-analyzer",
        "title": "Cohort Retention Analyzer",
        "category": "analysis",
        "tldr": "Given cohort retention data (signup-month × week-N), find the inflection point, classify retention curve shape (smiling/flat/leaky), and recommend the next intervention.",
        "tags": ["retention", "cohorts", "growth"],
        "best_for_tags": ["retention-analysis", "growth", "cohort-analysis"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You analyze cohort retention tables for product/growth teams. Cohort retention = % of users from signup-cohort N still active in week K.\n\n"
            "INPUTS:\n"
            "- cohort_table: 2D array — cohort_label (signup month) × week_number → retention %\n"
            "- product_type: 'transactional' | 'habit-forming' | 'b2b-tool' | 'social'\n"
            "- benchmark_target_w8_retention (optional): your target W8 retention %\n"
            "- product_changes: list of changes by date (helps explain cohort shifts)\n\n"
            "PROCEDURE:\n"
            "1. For each cohort, identify the W1, W4, W8, W12 retention values.\n"
            "2. Classify the curve shape:\n"
            "   - SMILING: drops then rises (sign of habit formation)\n"
            "   - FLAT: stabilizes after initial drop (sticky)\n"
            "   - LEAKY: declines continuously\n"
            "   - CLIFF: sharp drop at specific week (e.g., trial expiry)\n"
            "3. Compare cohorts: is later-cohort retention better/worse/same?\n"
            "4. Cross-reference product_changes — did a known change correlate with a cohort shift?\n"
            "5. Recommend the highest-leverage intervention: onboarding fix? activation moment? feature launch?\n\n"
            "OUTPUT FORMAT: markdown with shape verdict, cohort comparison, intervention recommendation, what data to gather next.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "cohort_table", "type": "matrix", "description": "Retention % per cohort × week_number", "required": True, "example": "{2026-01: [100, 65, 48, 38, 32, 30, 30, 29], 2026-02: [100, 70, 52, 41, 35, 33, 32, 31], ...}"},
            {"name": "product_type", "type": "string", "description": "Product category for benchmark context", "required": True, "example": "habit-forming"},
            {"name": "product_changes", "type": "list[Change]", "description": "Product changes with dates", "required": False, "example": "[{date:'2026-02-15', change:'shipped self-serve onboarding'}]"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Curve shape: SMILING for Feb+ cohorts\n\nFeb cohort: 70→52→41→35→33→32→**31% at W8**, then rising to 33% at W12. Classic smiling curve — habit formation kicking in by W10.\n\n## Cohort comparison\n- Jan: W8 retention 29% (LEAKY shape)\n- Feb: W8 retention 31% (SMILING shape — first cohort to show it)\n- Mar: W8 retention 34% (SMILING, steeper)\n\nThe Feb 15 onboarding ship correlates with the shape change. Likely causal.\n\n## Recommendation\nDouble down on activation. Mar cohort suggests the onboarding ship is driving real retention. Next intervention: identify the activation event that distinguishes Mar-cohort survivors from churners — likely a habit-forming action in W1-W3."},
        "use_cases": [
            {"scenario": "Monthly retention review", "example": "First Monday of every month, run on the prior month's cohort table; the recommendation goes into the team's growth review."},
            {"scenario": "Feature launch impact", "example": "Big feature shipped 2 months ago — did the cohort that experienced it from day 1 retain better than older cohorts?"},
            {"scenario": "Onboarding A/B follow-up", "example": "After an onboarding A/B test ends, follow up at W8 to see if the conversion lift translated to retention lift."},
            {"scenario": "Churn root-cause", "example": "Retention is dropping; this prompt helps distinguish 'we're acquiring worse users' from 'the product is leaking value'."},
        ],
        "when_not_to_use": "Don't use for transactional / one-time-purchase products — retention curves there are meaningless. Also skip if cohorts have <500 users (noise dominates).",
        "few_shot_examples": [
            {
                "input": "3 cohorts (Jan/Feb/Mar 2026), each 8 weeks. W8 retention: 22%/24%/23%. product_type: b2b-tool. Changes: 'Feb 1: new pricing tier launched'.",
                "output": "## Curve shape: FLAT across all cohorts (mid-20s W8 retention)\n\nNo material change between Jan, Feb, Mar. New pricing tier (Feb 1) didn't move retention — it may have affected acquisition mix, not value capture.\n\n## Cohort comparison\nW1: 65% / 67% / 64% — basically flat\nW4: 38% / 39% / 37% — flat\nW8: 22% / 24% / 23% — flat\n\n## Recommendation\nRetention is the bottleneck, not pricing. For a B2B tool, 23% W8 is below typical benchmark (35-50%). Focus on:\n1. Identify the 'aha' moment — what does the 23% surviving cohort have in common in W1?\n2. Get more users to that moment within first 7 days.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at distinguishing flat-but-fine from flat-and-bad."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong on the curve-shape classification."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Preferred when 10+ cohorts are in scope."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Sometimes misses subtle smile inflections."},
        ],
        "variations": [
            {"label": "Segmented cohort", "description": "Split by user segment (free vs paid, plan size, etc.).", "prompt_snippet": "Add INPUT: segment_cohort_tables = dict of {segment_name: cohort_table}. Output per-segment shape + cross-segment comparison."},
            {"label": "Revenue-retention", "description": "Retention by dollar, not by user count.", "prompt_snippet": "INPUT becomes revenue-cohort table (MRR retained per cohort). Output includes NDR (net dollar retention) computation per cohort."},
            {"label": "Survival-analysis framing", "description": "Use median-time-to-churn instead of W-N retention.", "prompt_snippet": "Compute Kaplan-Meier-style median lifetime per cohort. Compare cohort lifetime distributions."},
        ],
        "failure_modes": [
            {"symptom": "Calls a 1-2pp difference 'a meaningful improvement' when cohort size is small", "fix": "Require cohort size >500 for trend claims; otherwise flag 'noisy — wait for more data'"},
            {"symptom": "Attributes correlation to causation when a product change happens to align", "fix": "Explicit caveat in recommendation: 'correlation noted, causation requires controlled test'"},
            {"symptom": "Generic 'improve onboarding' recommendations", "fix": "Recommendation must be specific to the cohort curve shape (e.g., 'flat → activation moment', 'cliff → fix the cliff trigger')"},
            {"symptom": "Misses the smiling-curve inflection (looks at W8 only, not W10-12)", "fix": "Procedure step 1 requires W1, W4, W8, W12; classification can't be done on 1 data point"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-opus-4", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["a-b-test-result-interpreter", "support-ticket-triage"],
        "related_tool_slugs": ["amplitude", "mixpanel", "heap"],
        "related_glossary_slugs": ["cohort-analysis", "retention", "ndr"],
        "faq": [
            {"question": "What's a good W8 retention?", "answer": "Depends on product type. Habit-forming consumer: 30-40%. B2B tool: 50-70%. Transactional: 5-15% is fine. Pass product_type to anchor."},
            {"question": "How do I get the cohort table?", "answer": "Amplitude / Mixpanel / Heap export the retention chart as CSV. For SQL: GROUP BY signup_month, week_since_signup."},
            {"question": "Can it compare us to industry benchmarks?", "answer": "It can flag if you're below typical (e.g., 23% W8 for a B2B tool is sub-benchmark), but won't quote specific competitor data — that's opaque."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Cohort Retention Analyzer — Curve Shape + Intervention",
        "meta_description": "Classify cohort retention curves (smiling / flat / leaky / cliff), compare cohorts, cross-reference product changes, recommend next intervention.",
    },

    {
        "slug": "funnel-dropoff-diagnoser",
        "title": "Funnel Drop-off Diagnoser",
        "category": "analysis",
        "tldr": "Given a funnel (steps + counts), identify the worst drop-off, hypothesize 3-5 likely causes (ranked by likelihood × leverage), and suggest a diagnostic test for each.",
        "tags": ["funnel", "conversion", "drop-off"],
        "best_for_tags": ["funnel-analysis", "conversion", "growth"],
        "difficulty_tier": "beginner",
        "full_prompt": (
            "You diagnose funnel drop-offs for product/growth teams. Don't just point at the worst step — propose causes ranked by likelihood × leverage, and suggest the cheapest diagnostic test for each.\n\n"
            "INPUTS:\n"
            "- funnel: ordered list of {step_name, step_count, expected_conversion_to_next (optional)}\n"
            "- product_context: brief description (what is the user doing)\n"
            "- recent_changes: list of recent changes near the funnel\n"
            "- segment_filter (optional): which segment this funnel represents\n\n"
            "PROCEDURE:\n"
            "1. Compute conversion % per step (count[i+1] / count[i]).\n"
            "2. Compare actual vs expected_conversion_to_next where provided.\n"
            "3. Identify the WORST step (lowest conversion, or biggest gap vs expected).\n"
            "4. For that step, hypothesize 3-5 likely causes:\n"
            "   - User-side: confusion, missing info, wrong moment, friction (form length, email confirm)\n"
            "   - Tech-side: broken state, slow load, mobile-only bug\n"
            "   - Mismatch-side: wrong audience reached that step, expectations set elsewhere\n"
            "5. Rank by likelihood × leverage (high-likelihood + high-leverage at top).\n"
            "6. For each cause, suggest the cheapest diagnostic — usually a session replay, a survey, or an A/B test.\n\n"
            "OUTPUT: markdown — Funnel table, Worst step verdict, Ranked causes, Diagnostic plan, What we DON'T know.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "funnel", "type": "list[FunnelStep]", "description": "Ordered funnel steps with counts", "required": True, "example": "[{step:'Land', count:10000}, {step:'Signup-Start', count:3200}, {step:'Signup-Complete', count:1100}, {step:'Activate', count:680}]"},
            {"name": "product_context", "type": "string", "description": "Brief context", "required": True, "example": "B2B SaaS signup → email verify → set up workspace → invite teammate"},
            {"name": "recent_changes", "type": "list[Change]", "description": "Changes that touch the funnel", "required": False, "example": "[{date:'2026-05-01', change:'added required field email-domain-verify on Signup-Complete'}]"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Funnel\n| Step | Count | → Conv | Expected | Δ |\n|---|---|---|---|---|\n| Land | 10,000 | 32% | 30-40% | ✅ |\n| Signup-Start | 3,200 | 34% | 60% | ❌ -26pp |\n| Signup-Complete | 1,100 | 62% | 70% | ⚠️ -8pp |\n| Activate | 680 | — | — | — |\n\n## Worst step: Signup-Start → Signup-Complete (34% vs expected 60%)\nLost ~835 users at this step.\n\n## Ranked causes\n1. **(High likelihood × high leverage)** — May 1 added required email-domain-verify. Likely culprit; users abandon when form gets longer. Diagnostic: revert for 1 cohort, measure Δ.\n2. **(Medium × high)** — Mobile users may be hitting form-field issues. Diagnostic: device-split the funnel.\n3. **(Medium × medium)** — Email verify step may be marking common providers as personal/business mismatch. Diagnostic: check error-message rate.\n\n## What we DON'T know\n- Whether the 26pp drop is uniform across segments — pass segment_filter next run."},
        "use_cases": [
            {"scenario": "Weekly funnel review", "example": "Run on the prior week's funnel; recommendations feed Monday's experiment-planning meeting."},
            {"scenario": "Post-launch regression check", "example": "After a flow change, the funnel diagnoser confirms whether the change helped or hurt — and where exactly."},
            {"scenario": "Mobile vs desktop split", "example": "Run twice — once for mobile, once for desktop. Diff highlights mobile-only bugs."},
            {"scenario": "Onboarding intervention", "example": "When activation rate slips, this prompt narrows the cause to a specific step within the activation flow."},
        ],
        "when_not_to_use": "Don't use for funnels with <500 users at the top — small N causes false positives. Also skip if step-level event tracking is unreliable (instrument first, diagnose second).",
        "few_shot_examples": [
            {
                "input": "Funnel: Land 50k → Signup 12k → Verify 8k → Activate 2.5k. context: 'consumer mobile app'. recent_changes: []",
                "output": "## Funnel\n| Step | Count | → Conv | Notes |\n|---|---|---|---|\n| Land | 50,000 | 24% | |\n| Signup | 12,000 | 67% | OK |\n| Verify | 8,000 | 31% | ⚠️ worst step |\n| Activate | 2,500 | — | |\n\n## Worst step: Verify → Activate (31%)\nLost ~5,500 users.\n\n## Ranked causes\n1. **High × high** — Activation event likely requires action that mobile users aren't aware of. Diagnostic: session replay 20 users who verified but didn't activate.\n2. **Medium × high** — Email verify cycle (push to email, click link, return) breaks mobile flow. Diagnostic: in-app verification A/B vs email-link.\n3. **Low × high** — Activation requires permission grant (notif/camera/etc.) that mobile users decline. Diagnostic: check OS-level permission grant rate.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strong at the likelihood × leverage ranking."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Reliable funnel arithmetic."},
            {"model": "claude-haiku-4-5", "compatibility": "good", "notes": "Cheap for routine weekly reviews."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; expect to manually re-rank causes."},
        ],
        "variations": [
            {"label": "Segmented funnel", "description": "Per-segment drop-off comparison.", "prompt_snippet": "Add INPUT: segment_funnels = dict. Output per-segment funnel + cross-segment delta. Flag segments with >10pp delta from average."},
            {"label": "Revenue funnel", "description": "Money-weighted instead of user-weighted.", "prompt_snippet": "Each step has dollar value attached; compute dollar drop-off, not user drop-off."},
            {"label": "Cohort-stitched funnel", "description": "Track the same users across the funnel over time.", "prompt_snippet": "Funnel input becomes longitudinal: each step is 'users who reached step N within X days of signup'."},
        ],
        "failure_modes": [
            {"symptom": "Names the lowest-conversion step without considering whether that's expected (e.g., Land → Signup is naturally low)", "fix": "Compare to expected_conversion_to_next where provided; flag biggest negative delta vs expected"},
            {"symptom": "Generic causes ('improve UX')", "fix": "Each cause must be specific enough to test with one of: session replay, survey, A/B"},
            {"symptom": "Suggests expensive diagnostics first (4-week A/B) when a 30-min session replay would do", "fix": "Order diagnostics cheap → expensive; always prefer qualitative for first investigation"},
            {"symptom": "Doesn't connect recent_changes to current drop", "fix": "Always check recent_changes; if any change touches the worst step within 30 days, it's the #1 hypothesis"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-haiku-4-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["cohort-retention-analyzer", "a-b-test-result-interpreter"],
        "related_tool_slugs": ["amplitude", "mixpanel", "fullstory"],
        "related_glossary_slugs": ["funnel-analysis", "conversion-rate", "drop-off"],
        "faq": [
            {"question": "How many steps in a funnel?", "answer": "5-7 is the sweet spot. <3 = not useful, >10 = arithmetic of noise."},
            {"question": "What if I don't have expected conversions?", "answer": "The prompt will infer from the worst observed step. Better to ballpark expected (e.g., '50-60% for our category') — guides the diagnosis."},
            {"question": "How do I get session replays?", "answer": "FullStory, LogRocket, PostHog. Filter to users who hit the worst step and didn't proceed; watch 10-20 of them."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Funnel Drop-off Diagnoser — Causes Ranked by Leverage",
        "meta_description": "Diagnose funnel drop-offs. Ranks causes by likelihood × leverage, suggests cheapest diagnostic per cause.",
    },

    {
        "slug": "user-research-synthesizer",
        "title": "User Research Synthesizer (themes from transcripts)",
        "category": "analysis",
        "tldr": "Synthesize 10-30 user-interview transcripts into themes ranked by frequency × intensity, with verbatim quotes and recommended product responses.",
        "tags": ["user-research", "synthesis", "qualitative"],
        "best_for_tags": ["user-research", "interview-synthesis", "qualitative"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You synthesize user research interviews. Be ruthless about signal — most interviews have 1-2 themes worth surfacing, not 10.\n\n"
            "INPUTS:\n"
            "- transcripts: list of {participant_id, role, interview_date, transcript_text}\n"
            "- research_question: what you were trying to learn\n"
            "- segments (optional): how to slice participants (e.g., 'new users vs power users')\n\n"
            "PROCEDURE:\n"
            "1. Read every transcript; tag each statement with theme + sentiment.\n"
            "2. Cluster themes (5-10 distinct ones across 10-30 interviews is normal; if you have 30+ themes, you're too granular).\n"
            "3. Rank themes by: frequency (# of participants mentioning) × intensity (how strongly worded / repeated by same participant).\n"
            "4. For each top-5 theme: 1-sentence theme statement, 2-3 verbatim quotes (with participant_id), # of participants, recommended product response.\n"
            "5. Surface UNEXPECTED themes — things you weren't asking about but multiple participants raised. These are often the highest-value findings.\n"
            "6. List 'individual outlier insights' — striking quotes from 1 participant that don't form a theme but are worth tracking.\n\n"
            "OUTPUT FORMAT: markdown — Executive summary (4 sentences), Top 5 themes (each with quotes + count + recommendation), Unexpected findings, Individual outliers, Methodology note.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "transcripts", "type": "list[Transcript]", "description": "Interview transcripts with metadata", "required": True, "example": "[{participant_id:'P1', role:'CTO at 200-eng startup', interview_date:'2026-05-01', transcript_text:'...'}]"},
            {"name": "research_question", "type": "string", "description": "What you were trying to learn", "required": True, "example": "Why do engineering managers churn from our product within 90 days?"},
            {"name": "segments", "type": "list[str]", "description": "Optional participant segments", "required": False, "example": "['churned within 30 days', 'churned 30-90 days']"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Executive summary\n12 interviews with eng managers who churned within 90 days. Dominant theme: onboarding hand-off to team failed (10/12). Secondary theme: report features didn't justify cost above $99/mo (7/12). Unexpected: 5/12 mentioned 'I forgot we were paying for it'.\n\n## Top 5 themes\n\n### 1. Team-onboarding gap (10/12)\nIndividuals onboarded fine but couldn't transfer the value to their team.\n> \"I got it. My team didn't.\" — P3\n> \"We needed templates to share, not just the empty workspace.\" — P7\n**Recommendation:** Ship team-templates + invite-with-context flow.\n\n### 2. Cost-justification at scale (7/12)\nValue clear at individual use; harder to articulate to budget approvers.\n> \"My boss asked what we get for $5k/yr — I couldn't answer\" — P9\n..."},
        "use_cases": [
            {"scenario": "Quarterly user-research synthesis", "example": "10-30 interviews completed; this prompt produces the v1 findings memo for the team."},
            {"scenario": "Pre-roadmap input", "example": "Synthesize the last 3 months of interviews to anchor the next quarter's roadmap discussion."},
            {"scenario": "Sales-team training", "example": "Synthesize churn interviews into objection-themes; sales team gets the verbatim quotes to handle in calls."},
            {"scenario": "Hypothesis vs reality check", "example": "Compare team's pre-research hypotheses against what the prompt surfaces; the deltas are where the team's mental model was wrong."},
        ],
        "when_not_to_use": "Don't use for <5 interviews — clustering is unreliable. Also skip if transcripts are heavily moderator-led (you're surfacing the moderator's beliefs, not the participants').",
        "few_shot_examples": [
            {
                "input": "5 churn interviews. research_question: 'why did mid-market customers churn after their first renewal?'",
                "output": "## Executive summary\n5 mid-market churn interviews. Dominant theme: feature parity vs cheaper competitor (4/5). All 5 said 'we use 20% of features'.\n\n## Top 3 themes\n\n### 1. Feature-utilization gap (5/5)\nAll 5 participants felt they were paying for 5× the features they used.\n> \"We used 4 of 20 features. Why are we on the top tier?\" — P2\n> \"Cheaper tools do the 4 things we actually need.\" — P5\n**Recommendation:** Investigate a lighter tier with the 4-5 most-used features at $X/mo.\n\n### 2. Renewal trigger (4/5)\nRenewal forced a re-evaluation that didn't happen mid-year.\n> \"Honestly we wouldn't have looked at alternatives if not for the renewal email.\" — P3\n**Recommendation:** Mid-year value-recap emails reduce renewal-time surprise.\n\n### 3. Sales relationship gap (3/5)\nNo named CSM since onboarding 11 months prior.\n> \"I forgot who our rep was.\" — P4\n**Recommendation:** Quarterly check-ins post-onboarding through year 1.\n\n## Individual outliers\n- P1: \"Switched after a bad outage — your status page said up, but our app was down.\" (Trust issue, distinct from value perception.)",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at theme clustering without over-granularizing."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Use for 20+ transcripts where nuance matters."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong at extracting quotes; sometimes over-clusters themes."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable for first pass; verify ranking manually."},
        ],
        "variations": [
            {"label": "Quote-only mode", "description": "Skip recommendations, output just clustered quotes.", "prompt_snippet": "OUTPUT: per theme, list 3-5 verbatim quotes with participant_id. No 'recommended product response' section."},
            {"label": "Hypothesis-test mode", "description": "Test 3-5 pre-defined hypotheses against transcripts.", "prompt_snippet": "INPUT: hypotheses = list. Output: per-hypothesis 'supported / refuted / mixed' verdict + quotes."},
            {"label": "Segment-comparison", "description": "Theme differences across segments.", "prompt_snippet": "Run synthesis per segment; output cross-segment 'shared themes' vs 'segment-specific themes'."},
        ],
        "failure_modes": [
            {"symptom": "Over-clusters into 15+ themes (each with 1-2 participants)", "fix": "Hard cap at top 5-7 themes; require 3+ participants to elevate a 'theme'"},
            {"symptom": "Quotes are paraphrased, not verbatim", "fix": "Quote = exact text in transcript or it doesn't count; use ellipses for trimming but no paraphrase"},
            {"symptom": "Misses unexpected themes (only finds what research_question pointed at)", "fix": "Explicit step 5 — scan for themes that don't map to research_question"},
            {"symptom": "Generic recommendations ('improve onboarding')", "fix": "Recommendation must reference the specific theme finding (e.g., 'team-onboarding gap → ship team-templates')"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["a-b-test-result-interpreter", "cohort-retention-analyzer"],
        "related_tool_slugs": ["dovetail", "notion", "airtable"],
        "related_glossary_slugs": ["user-research", "qualitative-analysis", "thematic-coding"],
        "faq": [
            {"question": "Should I trim transcripts before feeding?", "answer": "Light trim only — remove pure moderator filler ('uh-huh', 'right'). Keep all participant responses; the prompt needs context."},
            {"question": "What's the right interview count?", "answer": "Synthesis works at 8-30 transcripts. <8 = single-person bias. >30 = consider segmentation."},
            {"question": "Can it handle multi-language?", "answer": "Yes if you feed transcripts as-is. Themes will be in the dominant language; verbatim quotes preserve original language."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "User Research Synthesizer — Themes from Transcripts",
        "meta_description": "Synthesize 10-30 interviews into ranked themes with verbatim quotes, unexpected findings, and product recommendations.",
    },

    {
        "slug": "metric-anomaly-explainer",
        "title": "Metric Anomaly Explainer",
        "category": "analysis",
        "tldr": "When a key metric spikes or drops, generate 5-8 hypotheses ranked by likelihood, suggest 1-line diagnostics per hypothesis, and recommend the order to investigate.",
        "tags": ["anomaly", "metric", "incident"],
        "best_for_tags": ["metric-monitoring", "incident-response", "data-analysis"],
        "difficulty_tier": "beginner",
        "full_prompt": (
            "You explain metric anomalies. When a number moves unexpectedly, generate hypotheses ranked by likelihood × cheapness-to-verify, so the on-call analyst investigates cheap-and-likely first.\n\n"
            "INPUTS:\n"
            "- metric: {name, current_value, baseline_value, time_period, direction (up|down|spike|drop)}\n"
            "- context: {related_systems, recent_deploys, recent_marketing_pushes, day_of_week, holiday_flag}\n"
            "- known_dependencies: list of upstream signals that could cause this metric to move\n\n"
            "PROCEDURE:\n"
            "1. Generate 5-8 hypotheses across categories:\n"
            "   - Tracking: instrumentation broken, event-rename, double-counting\n"
            "   - Acquisition: campaign launched/paused, viral moment, referral source change\n"
            "   - Product: deploy near the change, feature flag, UX shift\n"
            "   - External: holiday, weather, news event, third-party outage\n"
            "   - Composition: user-mix shifted (e.g., free-trial spam)\n"
            "2. Rank each by likelihood × cheapness-to-verify.\n"
            "3. For each, give a 1-line diagnostic (e.g., 'Check the events-renamed log').\n"
            "4. Recommend investigation order — cheapest first.\n\n"
            "OUTPUT FORMAT: markdown — Anomaly summary, Hypothesis table, Recommended investigation sequence, What we'd need to rule each in/out.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "metric", "type": "MetricAnomaly", "description": "Metric details + direction", "required": True, "example": "{name:'daily_signups', current_value:540, baseline_value:1200, time_period:'May 13 2026', direction:'drop'}"},
            {"name": "context", "type": "Context", "description": "Surrounding context", "required": True, "example": "{related_systems:['marketing site', 'signup-api'], recent_deploys:['2026-05-13 14:00: signup-api v2.4'], recent_marketing_pushes:[], day_of_week:'Friday', holiday_flag:false}"},
            {"name": "known_dependencies", "type": "list[str]", "description": "Upstream signals that affect this metric", "required": False, "example": "['marketing-site CTR', 'email-deliverability', 'referral programs']"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Anomaly\ndaily_signups: 1,200 → 540 (-55%) on May 13, Friday. Direction: drop.\n\n## Hypotheses (ranked)\n| # | Hypothesis | Likelihood | Cheap to verify? | Diagnostic |\n|---|---|---|---|---|\n| 1 | signup-api v2.4 deploy broke event tracking | HIGH | yes | Check if signup_success events still firing; compare counts in app logs vs analytics |\n| 2 | signup-api v2.4 broke the form (real drop) | HIGH | yes | Open the signup page in incognito; complete a signup |\n| 3 | Tracking pixel removed from marketing site | MEDIUM | yes | Check pixel deploy log |\n| 4 | Email-deliverability issue (signup confirmation) | MEDIUM | med | Check email-bounce rate from last 24h |\n| 5 | Search-engine deindexing / Google update | LOW | med | Check Search Console |\n\n## Investigation sequence\n1. Verify event firing (5 min)\n2. Manually complete a signup (2 min)\n3. Check the deploy diff for signup-api v2.4 (10 min)\n4. If steps 1-3 clean: check pixel + email deliverability"},
        "use_cases": [
            {"scenario": "Daily metric monitor", "example": "Cron monitors key metrics; on >3-sigma deviation, fires this prompt with the relevant context; output goes to #data-alerts."},
            {"scenario": "Post-deploy regression check", "example": "After every deploy, check metrics 60 min later; this prompt diagnoses any movement."},
            {"scenario": "Marketing campaign retrospective", "example": "Campaign ended yesterday; metric moved; this prompt distinguishes campaign effect from other causes."},
            {"scenario": "Junior analyst training", "example": "Analyst proposes hypotheses; prompt's ranking is the check."},
        ],
        "when_not_to_use": "Don't use for normal day-to-day metric fluctuation (<2-sigma). Also skip when context is missing — the prompt's value comes from cross-referencing the metric with deploys/marketing/external events.",
        "few_shot_examples": [
            {
                "input": "metric: 'free_trial_starts' down from 80/day → 12/day on May 14. context: no deploys, no marketing changes, day_of_week:Saturday",
                "output": "## Anomaly\nfree_trial_starts: 80 → 12 (-85%) on May 14, Saturday.\n\n## Hypotheses\n| # | Hypothesis | Likelihood | Diagnostic |\n|---|---|---|---|\n| 1 | Tracking: free_trial_start event renamed or broken | HIGH | Check events received vs DB row inserted |\n| 2 | Acquisition: top ad campaign auto-paused (budget cap) | HIGH | Check ad-platform spend logs |\n| 3 | External: search algorithm update | MEDIUM | Check Search Console impression count |\n| 4 | Saturday seasonality + small base = noise | LOW | Compare to last 4 Saturdays |\n\n## Investigation sequence\n1. Check ad-platform spend for the last 24h (5 min)\n2. Check event-receive vs row-write reconciliation (10 min)\n3. If both clean: pull 4-week Saturday baseline",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strong at the cheapness-to-verify ranking."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Reliable hypothesis generation."},
            {"model": "claude-haiku-4-5", "compatibility": "good", "notes": "Cheap for daily anomaly checks."},
            {"model": "llama-3.3-70b", "compatibility": "good", "notes": "Workable for self-hosted alerts."},
        ],
        "variations": [
            {"label": "Spike-only mode", "description": "When metrics jump up unexpectedly.", "prompt_snippet": "Skew hypotheses toward viral moment, ad-spend ramp, double-counting, leak from competitor's outage."},
            {"label": "Multi-metric correlation", "description": "When several metrics move together.", "prompt_snippet": "INPUT becomes list of {metric, direction}. Output focuses on shared upstream causes (tracking infra, auth system, payment provider)."},
            {"label": "Hypothesis-elimination tracker", "description": "Multi-turn use — narrow hypotheses as you investigate.", "prompt_snippet": "Add INPUT: ruled_out = list of {hypothesis, evidence}. Skip ruled-out hypotheses in next round; deepen remaining."},
        ],
        "failure_modes": [
            {"symptom": "Top hypothesis is 'data is wrong' without specifying which event", "fix": "Tracking hypothesis must name a specific event/pipeline (e.g., 'signup_success event')"},
            {"symptom": "Ignores recent_deploys correlation", "fix": "Any deploy within 24h of metric movement is automatically a top-3 hypothesis"},
            {"symptom": "Hypotheses are too broad ('something broke')", "fix": "Every hypothesis needs a specific verifiable claim, not 'something'"},
            {"symptom": "No ranking — just lists hypotheses", "fix": "Force the table to include likelihood + cheapness columns explicitly"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-haiku-4-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["funnel-dropoff-diagnoser", "a-b-test-result-interpreter"],
        "related_tool_slugs": ["amplitude", "datadog", "anomalo"],
        "related_glossary_slugs": ["anomaly-detection", "monitoring", "root-cause-analysis"],
        "faq": [
            {"question": "How sensitive should the alert threshold be?", "answer": "3-sigma is industry standard. Tune down for high-noise metrics (4-sigma) or up for high-value ones (2.5-sigma)."},
            {"question": "Should the prompt suggest a fix?", "answer": "No — it suggests diagnostics. Fixes need human judgment on tradeoffs."},
            {"question": "Can it run on multiple metrics at once?", "answer": "Yes — use the 'Multi-metric correlation' variation. Especially useful when a tracking pipeline breaks affecting 5+ metrics simultaneously."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Metric Anomaly Explainer — Ranked Hypotheses + Diagnostics",
        "meta_description": "When a metric moves unexpectedly, generate ranked hypotheses with cheap diagnostics for each. Investigate cheap-and-likely first.",
    },
]
