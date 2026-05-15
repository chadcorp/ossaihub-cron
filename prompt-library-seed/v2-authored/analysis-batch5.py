"""Analysis — batch 5."""

RECORDS = [
    {
        "slug": "funnel-drop-off-diagnoser",
        "title": "Funnel Drop-Off Diagnoser",
        "tldr": "Reads funnel data (cohorts, segments, time-windows) + qualitative context to surface WHERE users drop off, WHO drops at each stage, and the MOST LIKELY CAUSES — with proposed experiments to test each cause.",
        "category": "analysis",
        "tags": ["funnel", "analytics", "growth", "cro"],
        "best_for_tags": ["pm", "growth", "analytics-teams"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Onboarding funnel debug", "example": "New-user activation 35%; surface which step is the leak."},
            {"scenario": "Checkout funnel", "example": "Cart-to-purchase 28%; segment by traffic source to find the leak."},
            {"scenario": "Trial-to-paid conversion", "example": "Trial converts 12%; analyze cohorts."},
            {"scenario": "Feature-adoption funnel", "example": "New feature: discovery → click → use → habit; find drop-off."},
        ],
        "when_not_to_use": "Skip without per-stage data — funnels need step-level metrics. Skip with too little volume (n<500 per stage) — analysis is noise.",
        "full_prompt": """You are a funnel-drop-off analyst. Find WHERE users leak, WHO leaks at each stage, and the MOST LIKELY CAUSES.

INPUT
- Funnel definition (ordered stages with criteria): {funnel_stages}
- Funnel data (counts per stage, optionally segmented): {funnel_data}
- Time window: {time_window}
- Segments available (source, plan, geo, device, etc.): {segments}
- Qualitative context (user feedback, support tickets, recent changes): {context}

OUTPUT

## 1. Funnel overview
- **Stage counts:** ___
- **Stage-over-stage conversion rates:** ___
- **Overall conversion (top → bottom):** ___
- **Biggest absolute drop:** ___
- **Biggest relative drop (% of previous step):** ___

## 2. Per-stage leak diagnosis
For each stage with notable drop:

### Stage N: [name] (___% conversion)
- **Who drops here:** segment breakdown — which segments worse than average?
- **Likely causes (3-5 hypotheses):**
  - Cause 1: ___ (mechanism: ___)
  - Cause 2: ___
- **Most-likely cause (with reasoning):** ___
- **Evidence supporting:** ___ (data + qualitative)
- **Evidence against:** ___ (counter-evidence)

## 3. Segment analysis
For each segment dimension, where the leak is worst:
| Segment | Stage where leak is worst | Conversion vs average | Likely cause |

## 4. The highest-leverage fix
Rank fixes by:
- Impact (users affected × conversion lift)
- Cost (engineering / design time)
- Risk (could backfire)

Top 3 fixes ranked.

## 5. Experiment design
For each top-3 fix:
- **Hypothesis:** ___
- **Treatment:** ___
- **Control:** ___
- **Sample size needed (rough):** ___
- **MDE (min detectable effect):** ___
- **Risk of harm to other metrics:** ___

## 6. What I'd watch for if running the experiment
- Leading indicators that suggest the experiment is working before final read-out.
- Reasons the experiment could mislead (selection effect, novelty, gaming).
- Decision criteria for SHIP / KILL / EXTEND.

## 7. The 'don't fix the wrong thing' check
Common funnel-analysis pitfalls:
- **Optimizing the easiest stage** (e.g., signup) when downstream stages are the real bottleneck.
- **Fixing for biggest absolute drop** when the upstream stage is the volume problem.
- **Improving conversion** at the cost of downstream quality (high-conversion + low-retention).

For THIS funnel, where could the wrong-thing-fixed-here happen?

CRITICAL RULES
- Diagnosis is EVIDENCE-BASED (data + qualitative). Not vibes.
- Segment analysis is REQUIRED — average hides patterns.
- 'Don't fix the wrong thing' check is required — funnel optimization without product-quality lens fails.
- Experiment design is concrete (hypothesis + treatment + size).

FUNNEL DATA
{funnel_data}

CONTEXT
{context}

Begin.""",
        "input_variables": [
            {"name": "funnel_stages", "type": "string", "description": "Funnel stages", "required": True, "example": "(1) Landing visit (2) Signup form view (3) Account created (4) Connected first integration (5) First action completed (6) Returned day-2"},
            {"name": "funnel_data", "type": "string", "description": "Stage counts (optionally segmented)", "required": True, "example": "Stage counts last 30d: 50000 → 12000 → 8000 → 4000 → 2400 → 1100. Segmented by source: organic 35% activation, paid 18%, referral 41%."},
            {"name": "time_window", "type": "string", "description": "Time window", "required": True, "example": "Last 30 days (Apr 14 - May 13)"},
            {"name": "segments", "type": "string", "description": "Segments available", "required": True, "example": "Traffic source (organic / paid / referral / direct), device (mobile / desktop), plan (free / pro), geo (US / EU / APAC)"},
            {"name": "context", "type": "string", "description": "Qualitative context", "required": True, "example": "Support tickets last 30d show: 23% mention 'integration not working', 12% 'don't know what to do after signup', 8% 'pricing unclear before paywall'. Recent change: redesigned signup form on Apr 28."},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Seven sections: funnel overview, per-stage leak diagnosis with hypotheses, segment analysis, ranked highest-leverage fixes, experiment design, leading-indicator watching, 'don't fix the wrong thing' check.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at honest causal hypotheses + experiment design quality."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; can default to 'add tooltip' fixes — re-pin highest-leverage rule."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; segment analysis sometimes weaker."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Workable for simple funnels; thins on multi-segment analysis."},
        ],
        "variations": [
            {"label": "Mobile-vs-desktop split", "description": "Mobile-specific funnel.", "prompt_snippet": "Treat mobile and desktop as separate funnels. Each gets its own diagnosis. Surface where they diverge significantly."},
            {"label": "Cohort-comparison", "description": "Compare cohorts over time.", "prompt_snippet": "Compare current cohort to prior month / quarter. Surface stages where conversion has DEGRADED + correlate with shipped changes."},
            {"label": "Pre-experiment forecast", "description": "Forecast experiment impact.", "prompt_snippet": "Given a proposed fix, forecast: expected lift, sample size needed, time-to-significance. Surface if experiment is feasible within available volume."},
        ],
        "failure_modes": [
            {"symptom": "Defaults to obvious fixes ('add tooltip').", "fix": "Re-pin: 'highest-leverage = biggest impact × lowest cost. Tooltips rarely are. Stretch.'"},
            {"symptom": "Misses segment patterns.", "fix": "Force section 3: 'segment analysis on at least 2 dimensions. Average hides specifics.'"},
            {"symptom": "Vague hypotheses.", "fix": "Require: 'each hypothesis has a mechanism — WHY users drop. Not \"because confusing.\"'"},
            {"symptom": "Skips 'don't fix wrong thing' check.", "fix": "Hard rule: 'section 7 required. Funnel optimization can hurt quality / retention.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["user-feedback-theme-extractor", "product-metric-tree-builder", "incident-postmortem-blameless"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["conversion-funnel", "cohort-analysis"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How much data do I need?", "answer": "Per stage, n≥500 for stable rates. Below that, segment analysis is unreliable. Use a longer time window or aggregate cohorts."},
            {"question": "Will it suggest tracking implementation?", "answer": "Surfaces gaps in section 6 (what would help to know). For tracking implementation prompts, use a separate analytics-events prompt."},
            {"question": "Can it tell ME the cause?", "answer": "It surfaces hypotheses. Causes are confirmed by experiments. The prompt's value is generating testable hypotheses, not declaring the cause."},
            {"question": "What if the funnel is changing?", "answer": "Cohort-comparison variation. Separates secular trends from intervention effects. Critical when product is iterating fast."},
        ],
        "meta_title": "Funnel Drop-Off Diagnoser — Analysis Prompt",
        "meta_description": "Diagnose funnel drop-offs: per-stage leak analysis, segment patterns, ranked highest-leverage fixes, experiment design, 'don't fix wrong thing' check.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "ab-test-result-interpretation",
        "title": "A/B Test Result Interpretation",
        "tldr": "Reads A/B test results and tells you whether the lift is real, what the practical impact is, what to watch for in long-term, and whether to ship — accounting for statistical AND practical significance.",
        "category": "analysis",
        "tags": ["ab-testing", "experimentation", "statistics", "decision-making"],
        "best_for_tags": ["growth", "pm", "data-science"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Read out a feature A/B test", "example": "Treatment lifted activation 2.1pp, p<0.05 — ship or not?"},
            {"scenario": "Multi-metric interpretation", "example": "Primary metric won; secondary metric lost; what does the data say?"},
            {"scenario": "Mixed results across segments", "example": "Lifted desktop, lost mobile; ship segmented or not?"},
            {"scenario": "Null result interpretation", "example": "No significant difference; was the test underpowered or is the effect zero?"},
        ],
        "when_not_to_use": "Skip when the test wasn't randomized properly (selection bias). Skip when sample size is tiny (n<500/arm) — statistical inference is noise. Use a different framing.",
        "full_prompt": """You are an A/B test interpreter. Tell me whether the lift is real, what the practical impact is, whether to ship.

INPUT
- Test design (control / treatment / randomization unit): {design}
- Primary metric + result: {primary_metric}      (lift, p-value, CI, n per arm)
- Secondary / guardrail metrics: {secondary_metrics}
- Test duration: {duration}
- Segment results: {segment_results}
- Practical-significance threshold: {practical_threshold}    (smallest effect that matters)

OUTPUT

## 1. Test soundness check
Before interpreting result:
- **Randomization unit:** user / session / cookie. Correct for test purpose?
- **Sample size per arm:** ___ (target: balanced ±5%)
- **Test duration:** captured weekly seasonality? Pre-launch novelty?
- **SRM (sample ratio mismatch):** if observed n differs from expected allocation, flag.
- **Pre-registered metrics:** primary + guardrails declared upfront?

If serious flaws: STOP. Address before interpretation.

## 2. Primary metric: real lift?
- Observed lift: ___
- 95% CI: [___, ___]
- p-value: ___
- **Statistically significant?** yes / no.
- **Practically significant?** lift vs {practical_threshold}.
- **Both / one / neither?**

Recommendation:
- Stat-sig + practical-sig: lift is real and matters.
- Stat-sig + NOT practical-sig: lift is real but small — ship if cheap.
- NOT stat-sig + practical-sig point estimate: underpowered or null effect — extend or kill.
- NOT stat-sig + small point estimate: probably null.

## 3. Secondary / guardrail metrics
For each:
- Direction (lifted / lost / null): ___
- Stat-sig + practical-sig?
- Concerning movement? (e.g., engagement up, churn up = winning the wrong customers)

## 4. Segment analysis
Where the lift was strong vs weak:
| Segment | Lift | Stat-sig | Notes |

Heterogeneity check:
- Is the lift driven by one segment only?
- Did any segment LOSE?
- Multiple-testing correction needed if checking many segments.

## 5. Long-term concerns
- **Novelty effect:** could lift fade as users habituate? (Check post-week-1 vs week-4 data.)
- **Selection effect:** did the treatment select different users? (Compare baseline characteristics.)
- **Network effects:** did treatment users spill onto control users?
- **Long-term harm:** could short-term win cause long-term loss (over-promotion → churn)?

## 6. Ship decision
- **SHIP** — lift is real, practical, no concerning secondary moves, no long-term concerns.
- **SHIP WITH MONITORING** — looks good, but watch for ___.
- **PARTIAL SHIP** — winning segment only.
- **EXTEND** — underpowered; need more data.
- **KILL** — null effect or concerning secondary moves.
- **HOLD FOR FOLLOW-UP** — need more analysis before deciding.

State recommendation + 1-paragraph reasoning.

## 7. Open questions / follow-up tests
- What would you want to know that this test didn't answer?
- What's the next test if you SHIP?
- What's the next test if you KILL?

CRITICAL RULES
- Test-soundness check is FIRST. Don't interpret a broken test.
- Statistical significance ≠ practical significance. Address both.
- Guardrails matter — winning primary while losing secondary is often net negative.
- Long-term concerns are LIVE — short-term lift can disguise long-term loss.
- Ship recommendation is CONCRETE (ship / extend / kill), with reasoning.

TEST DESIGN
{design}

PRIMARY METRIC
{primary_metric}

Begin.""",
        "input_variables": [
            {"name": "design", "type": "string", "description": "Test design", "required": True, "example": "User-level randomization, 50/50 split, control = current signup, treatment = simplified signup. Pre-registered: primary = D1 activation, guardrails = D7 retention + paid conversion."},
            {"name": "primary_metric", "type": "string", "description": "Primary metric result", "required": True, "example": "D1 activation: control 28.2% (n=12,500), treatment 30.3% (n=12,481). Lift 2.1pp (+7.4% relative), 95% CI [0.8, 3.4], p=0.002."},
            {"name": "secondary_metrics", "type": "string", "description": "Secondary metrics", "required": True, "example": "D7 retention: control 14.2%, treatment 13.1%. Lift -1.1pp, 95% CI [-2.1, -0.1], p=0.04. Paid conversion: control 3.1%, treatment 3.0%. p=0.62 (null)."},
            {"name": "duration", "type": "string", "description": "Test duration", "required": True, "example": "21 days. 3 full weeks; covers weekly seasonality."},
            {"name": "segment_results", "type": "string", "description": "Segment breakdowns", "required": True, "example": "By source: organic +3.2pp, paid +0.4pp (NS), referral +5.1pp. By device: desktop +2.8pp, mobile +0.9pp (NS)."},
            {"name": "practical_threshold", "type": "string", "description": "Practical significance threshold", "required": True, "example": "Smallest effect we'd ship for: +1pp absolute D1 activation."},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Seven sections: test soundness check, primary metric interpretation (stat + practical), secondary metrics, segment analysis, long-term concerns, ship decision with reasoning, open questions/follow-up tests.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest on guardrail interpretation + honest 'kill' / 'extend' recommendations."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong on statistical reasoning."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; sometimes vague on long-term concerns."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for single-metric simple tests; thins on multi-metric / segment analysis."},
        ],
        "variations": [
            {"label": "Bayesian update", "description": "Report probability of effect.", "prompt_snippet": "Convert to Bayesian framing: probability that effect ≥ {practical_threshold}, expected loss if shipping a null treatment, expected gain if killing a real lift."},
            {"label": "Multi-test correction", "description": "Adjust for multiple comparisons.", "prompt_snippet": "If many subgroup / metric checks, apply Bonferroni or BH correction. Surface adjusted p-values. Note false-discovery risk."},
            {"label": "Quasi-experiment / observational", "description": "For non-randomized data.", "prompt_snippet": "Re-frame for quasi-experiment (DID, propensity-matching). Add: parallel trends check, balance check, sensitivity analysis."},
        ],
        "failure_modes": [
            {"symptom": "Conflates stat-sig with ship-worthy.", "fix": "Re-pin: 'practical significance is separate. Tiny lifts at p<0.001 may not be worth shipping.'"},
            {"symptom": "Ignores guardrails.", "fix": "Force: 'guardrail movement is part of decision. Primary up + guardrail down often = net negative.'"},
            {"symptom": "Misses long-term concerns.", "fix": "Add: 'section 5 mandatory. Short-term lift can hide long-term harm.'"},
            {"symptom": "Vague ship recommendation.", "fix": "Hard rule: 'recommendation is one of SHIP / SHIP-WITH-MONITORING / PARTIAL-SHIP / EXTEND / KILL / HOLD. With reasoning.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["funnel-drop-off-diagnoser", "base-rate-correction-check", "go-no-go-decision-meeting-prep"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["ab-testing", "statistical-significance"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What's a 'practical' significance threshold?", "answer": "The smallest effect worth the cost / risk of shipping. Often expressed as 'we'd ship if lift ≥ X%'. Pre-register it; otherwise it's post-hoc rationalization."},
            {"question": "What about under-powered tests?", "answer": "Underpowered tests can show 'null' that's actually a real effect we couldn't detect. Section 5 flags this. Extend or run a follow-up with bigger sample."},
            {"question": "How to handle SRM (sample ratio mismatch)?", "answer": "SRM = randomization broke. Investigate (bot traffic, instrumentation bug, eligibility logic) before interpreting. Don't read a broken test."},
            {"question": "What about novelty effects?", "answer": "Compare lift week 1 vs week 4. If lift fades, novelty. Fix: longer tests, hold-out groups for long-term measurement."},
        ],
        "meta_title": "A/B Test Result Interpretation — Analysis Prompt",
        "meta_description": "Interpret A/B test results: stat + practical significance, guardrails, segments, long-term concerns, concrete ship decision.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "cohort-retention-analyzer",
        "title": "Cohort Retention Analyzer",
        "tldr": "Reads cohort retention curves + cross-cohort comparisons to surface what's improving, regressing, and where the inflection points are — with hypotheses for product / lifecycle interventions.",
        "category": "analysis",
        "tags": ["retention", "cohorts", "lifecycle", "analytics"],
        "best_for_tags": ["growth", "pm", "lifecycle-marketing"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Quarterly retention review", "example": "12 cohorts of new users — surface retention trends."},
            {"scenario": "Post-feature retention impact", "example": "Did the shipped feature improve retention of subsequent cohorts?"},
            {"scenario": "Lifecycle-stage diagnosis", "example": "Where do users drop most — d1, d7, d30, d90?"},
            {"scenario": "Multi-segment retention compare", "example": "Free vs Pro retention shapes."},
        ],
        "when_not_to_use": "Skip without monthly cohorts of meaningful size (n≥1000). Skip for short product lifetimes (<6 months) — cohorts haven't matured.",
        "full_prompt": """You are a cohort retention analyst. Surface what's improving, regressing, and where the inflection points are.

INPUT
- Retention data (cohorts × days, % retained): {retention_matrix}
- Cohort definitions (month, source, segment): {cohort_definitions}
- Lifecycle stage milestones: {lifecycle_milestones}     (e.g., D1, D7, D30, D90, D180)
- Product / lifecycle changes timeline: {changes_timeline}
- Target audience for analysis: {audience}              (PM / lifecycle-marketing / exec)

OUTPUT

## 1. Cohort overview
- **Cohorts analyzed:** ___ (n cohorts × range of n users)
- **Retention milestones tracked:** D1, D7, D30, D90.
- **Most-recent cohort with mature data:** ___

## 2. Curve shape analysis
- **D1 → D7 drop:** ___pp (the 'gets it' drop).
- **D7 → D30 drop:** ___pp (the 'habit formed' drop).
- **D30 → D90 drop:** ___pp (the 'value sustained' drop).
- **D90 → D180:** ___pp (the 'long-term value' drop).

Where's the BIGGEST drop? That's the highest-leverage lifecycle stage.

## 3. Cross-cohort trends
For each milestone (D1, D7, D30, D90):
- **Trend over cohorts:** improving / flat / regressing.
- **Magnitude:** ___pp change per quarter.
- **Inflection points:** which cohort showed the biggest change + why? (correlate with changes_timeline).

## 4. Segment retention patterns
For each segment dimension:
| Segment | D1 | D7 | D30 | D90 | Notable pattern |

Surface segments with:
- Best retention (study these).
- Worst retention (these are the leverage).
- Recent change in retention (cohort-by-cohort).

## 5. Intervention hypotheses
For the BIGGEST lifecycle drop, hypothesize 3-5 interventions:
- **D1 drop:** onboarding clarity, first-action quality, expectation-setting.
- **D7 drop:** habit triggers, value-recognition, second-session hooks.
- **D30 drop:** depth-of-use, integration into workflow, network effects.
- **D90+:** long-term value, pricing fit, alternative platforms.

For each: mechanism + expected impact.

## 6. The 'survivorship bias' check
Late-stage retention (D90, D180) is dominated by the users who stayed. Don't draw conclusions about the cohort from late-stage data:
- "D90 retention 25% — but D90 users are not representative of the cohort."

Surface where survivorship bias would mislead.

## 7. Recommended next analysis
- What deeper questions emerged?
- What data we'd need to test the hypotheses.
- Pre-vs-post comparisons that would clarify cause.

CRITICAL RULES
- Curve-shape analysis named — not just numbers.
- Cross-cohort trends correlated with shipped changes (timeline).
- Segment analysis surfaces leverage segments (best to learn from, worst to fix).
- Survivorship bias check — late-stage cohorts mislead.
- Hypotheses are MECHANISTIC, not generic.

DATA
{retention_matrix}

CHANGES TIMELINE
{changes_timeline}

Begin.""",
        "input_variables": [
            {"name": "retention_matrix", "type": "string", "description": "Retention data (cohorts × days)", "required": True, "example": "Cohort Jan-2026: D1=42%, D7=18%, D30=11%, D90=7%. Feb-2026: D1=45%, D7=22%, D30=14%, D90=8%. ..."},
            {"name": "cohort_definitions", "type": "string", "description": "Cohort definitions", "required": True, "example": "Cohort = month of signup. Average cohort size: 6500 users. Segmented by source (organic / paid / referral) and plan (free / pro)."},
            {"name": "lifecycle_milestones", "type": "string", "description": "Lifecycle milestones", "required": True, "example": "D1 (first session done), D7 (habit formed), D30 (value-recognized), D90 (long-term active), D180 (sticky)"},
            {"name": "changes_timeline", "type": "string", "description": "Product changes timeline", "required": True, "example": "Feb 2026: new onboarding flow shipped. Apr 2026: pricing increased on Pro tier."},
            {"name": "audience", "type": "string", "description": "Audience", "required": True, "example": "PM + lifecycle-marketing — need actionable hypotheses for next sprint"},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Seven sections: cohort overview, curve-shape analysis with named drops, cross-cohort trends, segment patterns, intervention hypotheses with mechanism, survivorship-bias check, recommended next analysis.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at honest survivorship-bias surfacing + mechanistic hypotheses."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; can default to generic interventions — re-pin mechanism rule."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; handles long cohort tables well."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for single-segment cohorts; thins on multi-segment + survivorship analysis."},
        ],
        "variations": [
            {"label": "Subscription-business focus", "description": "Lean into MRR retention.", "prompt_snippet": "Add: MRR retention (not just user retention) — gross dollar retention, net dollar retention, expansion revenue from existing cohorts."},
            {"label": "Habit-mechanism focus", "description": "Hooks-style framing.", "prompt_snippet": "Add: hooks model. For each lifecycle drop, name the missing hook (trigger / action / variable reward / investment). Suggests intervention design."},
            {"label": "Cohort-vintage comparison", "description": "Compare cohorts vs benchmark.", "prompt_snippet": "Add: benchmark from prior-year same-month cohort. Surfaces seasonal vs structural trend."},
        ],
        "failure_modes": [
            {"symptom": "Vague intervention hypotheses.", "fix": "Re-pin: 'each intervention names the MECHANISM (why it would change retention). Not \"add tooltip.\"'"},
            {"symptom": "Misses survivorship bias.", "fix": "Force section 6: 'late-stage cohort data is biased toward survivors. Surface this for D90+ analysis.'"},
            {"symptom": "No timeline correlation.", "fix": "Add: 'cross-cohort changes correlate to shipped features / lifecycle changes. Inflections matter.'"},
            {"symptom": "Optimizes wrong lifecycle stage.", "fix": "Hard rule: 'identify the BIGGEST drop in section 2. Hypotheses target that, not the easiest stage to nudge.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["funnel-drop-off-diagnoser", "product-metric-tree-builder", "user-feedback-theme-extractor"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["cohort-analysis", "retention-curve"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How many cohorts to compare?", "answer": "Minimum 6 cohorts to see trend. 12+ gives noise-resistance. Past 24 cohorts, the early ones may not be comparable to current ones (product shifted)."},
            {"question": "Why focus on biggest drop?", "answer": "Highest leverage. 1pp improvement at D1 affects everyone; 1pp at D90 affects only survivors. Fix the biggest first."},
            {"question": "How to test intervention hypotheses?", "answer": "A/B test the intervention with new cohorts. Use the AB test interpretation prompt to read out. Don't conclude from one cohort moving."},
            {"question": "What's a 'good' retention curve?", "answer": "Domain-specific. For B2B SaaS: D30 retention 50%+ is strong. For consumer: 20-30%. For social: 30-40%. Benchmark within category, not across."},
        ],
        "meta_title": "Cohort Retention Analyzer — Analysis Prompt",
        "meta_description": "Analyze cohort retention curves: lifecycle drops named, cross-cohort trends, segment patterns, mechanistic intervention hypotheses, survivorship-bias check.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "kpi-anomaly-investigator",
        "title": "KPI Anomaly Investigator",
        "tldr": "Investigates a KPI anomaly: separates real signal from noise, traces upstream causes through metric trees, rules out artifacts (instrumentation, seasonality), proposes the next 3 checks.",
        "category": "analysis",
        "tags": ["anomaly", "kpi", "diagnosis", "investigation"],
        "best_for_tags": ["analytics-teams", "ops", "data-engineering"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Daily metric drop alert", "example": "Signup down 22% yesterday — real?"},
            {"scenario": "Surprise positive spike", "example": "Activation up 15% — real or instrumentation?"},
            {"scenario": "Quarterly review anomaly", "example": "Q2 churn jumped; investigate before exec review."},
            {"scenario": "Cross-metric divergence", "example": "Revenue flat but signups up — what's compensating?"},
        ],
        "when_not_to_use": "Skip when the anomaly is well-understood (known holiday, deploy known to affect metric). Skip without metric-tree context — anomaly investigation needs upstream visibility.",
        "full_prompt": """You are a KPI anomaly investigator. Separate signal from noise; trace upstream causes; rule out artifacts.

INPUT
- Anomaly: which KPI, when, magnitude: {anomaly}
- Baseline (typical range / seasonality): {baseline}
- Metric tree (upstream / downstream metrics): {metric_tree}
- Recent changes / deploys / events: {recent_changes}
- Available data slices: {available_data}
- Stakes / urgency: {stakes}

OUTPUT

## 1. Anomaly characterization
- **Metric:** ___
- **Direction:** up / down
- **Magnitude:** ___ % vs baseline.
- **Duration:** one-day spike / multi-day trend / step-change.
- **Statistical significance vs natural variance:** is this outside 3σ of baseline?

If within natural variance: STOP. Recommend monitoring, not investigating.

## 2. Artifact ruleouts
First, rule out instrumentation / measurement issues:

| Artifact | Check | Status |
|---|---|---|
| Instrumentation change | Did tracking change in last 7 days? | clear / suspect |
| Backfill / re-processing | Has data been reprocessed? | clear / suspect |
| Pipeline bug | Is the metric pipeline healthy? | clear / suspect |
| Sampling | Did sampling rate change? | clear / suspect |
| Seasonality | Match same period last year / week? | clear / suspect |
| Data cutoff | Is the period complete? | complete / partial |

If any 'suspect': pause investigation, validate measurement.

## 3. Cause hypotheses
Walk the metric tree upstream:
- **Upstream metric 1:** [name] — moved how much? Could it explain the anomaly?
- **Upstream metric 2:** ___
- ...

For each upstream that moved:
- Mechanism connecting it to the KPI.
- Magnitude explained (e.g., '40% of the change explained by upstream A').

## 4. External / world events
- Holiday, news event, weather, competitor action?
- Industry-wide trend (check via external benchmarks if possible)?
- Marketing campaign / PR (planned or unplanned)?

## 5. Internal events
- Recent deploys (date range matches anomaly window?)
- Pricing / packaging changes.
- Marketing-spend changes.
- Lifecycle-comms changes.

Correlate to anomaly timing.

## 6. The leading hypothesis
After ruleouts + cause analysis:
- **Leading hypothesis:** ___
- **Evidence supporting:** ___
- **Evidence against:** ___
- **Confidence:** high / medium / low.

If LOW confidence: don't commit to it yet. List the top 2 hypotheses.

## 7. Next 3 checks
Specific, actionable:
1. ___ (will confirm/refute leading hypothesis)
2. ___
3. ___

Each check: how to run, expected outcome, time to do.

## 8. Communication
- **Stakeholders to notify:** ___
- **Communication template:** factual, what we know vs don't know, when we'll have an update.
- **Don't say:** speculation that could move stock / cause panic / create unnecessary work.

CRITICAL RULES
- Artifact ruleouts FIRST. Most anomalies are measurement, not reality.
- Upstream metric tracing — explain magnitude, not just direction.
- Leading hypothesis HAS confidence rating.
- Next-3-checks are CONCRETE, time-boxed.
- Communication template prevents speculation panic.

ANOMALY
{anomaly}

METRIC TREE
{metric_tree}

Begin.""",
        "input_variables": [
            {"name": "anomaly", "type": "string", "description": "Anomaly description", "required": True, "example": "D1 activation dropped from 28% to 22% yesterday (May 12), a 21% relative drop."},
            {"name": "baseline", "type": "string", "description": "Baseline + seasonality", "required": True, "example": "D1 activation has been 27-29% for 60 days. Monday-Wednesday slightly higher than weekend. No prior anomalies this size in 6 months."},
            {"name": "metric_tree", "type": "string", "description": "Metric tree", "required": True, "example": "D1 activation = users completing first action / total D0 signups. Upstream: signup volume (was 14k, normal), signup source mix (organic 60%, paid 30%, referral 10%), onboarding-flow completion rate (typically 78%)."},
            {"name": "recent_changes", "type": "string", "description": "Recent changes", "required": True, "example": "May 11 14:00 UTC: deployed onboarding A/B test (50/50). May 12 09:00 UTC: marketing started new paid campaign."},
            {"name": "available_data", "type": "string", "description": "Available data slices", "required": True, "example": "Available: source, device, plan, geo, signup-cohort, A/B test arm."},
            {"name": "stakes", "type": "string", "description": "Stakes", "required": True, "example": "Exec sync tomorrow morning; CRO is going to ask."},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Eight sections: anomaly characterization, artifact ruleouts table, cause hypotheses via metric tree, external events, internal events, leading hypothesis with confidence, next 3 checks, stakeholder communication template.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at calibrated confidence + ruleout discipline."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; can jump to causes — re-pin artifact ruleouts first."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; sometimes weaker on external-event hypotheses."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Workable; thins on complex metric trees."},
        ],
        "variations": [
            {"label": "Production-monitoring", "description": "Production-alert-driven.", "prompt_snippet": "Output a runbook entry: SEV level, who to page, what to check, what to communicate. Used as an incident-response template."},
            {"label": "Pre-board-meeting", "description": "Polish for exec consumption.", "prompt_snippet": "Output the artifact-ruleout summary + leading hypothesis only. Skip technical detail. Used for exec board prep where time is tight."},
            {"label": "Multi-anomaly correlation", "description": "Investigate multiple anomalies together.", "prompt_snippet": "Given N anomalies in similar time window, surface: are they correlated? Is there a common cause? Or independent?"},
        ],
        "failure_modes": [
            {"symptom": "Skips artifact ruleouts.", "fix": "Hard rule: 'section 2 first. Most anomalies are measurement, not reality.'"},
            {"symptom": "Jumps to favorite cause.", "fix": "Re-pin: 'all upstream metrics traced. Show magnitude explained, not just direction.'"},
            {"symptom": "Vague next-checks.", "fix": "Force: 'each check has how-to-run + expected outcome + time-to-complete.'"},
            {"symptom": "Communicates speculation as fact.", "fix": "Require section 8 template: 'what we know vs don\\'t know. When we\\'ll have an update.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["funnel-drop-off-diagnoser", "cohort-retention-analyzer", "incident-postmortem-blameless"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["anomaly-detection", "metric-tree"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What's the most common cause of false anomalies?", "answer": "Instrumentation. New deploys often change measurement before changing the underlying metric. Always rule out before investigating causes."},
            {"question": "How quickly should I communicate?", "answer": "Communicate WHAT YOU KNOW within hours; commit to update timing. Speculation gets quoted; facts get trusted."},
            {"question": "What if anomaly is within natural variance?", "answer": "Section 1 surfaces this. Don't investigate noise. Update monitoring thresholds if false positives are too frequent."},
            {"question": "How to know when to stop investigating?", "answer": "When the leading hypothesis is high-confidence + further checks won't change the action. Most investigations should resolve in <1 week."},
        ],
        "meta_title": "KPI Anomaly Investigator — Analysis Prompt",
        "meta_description": "Investigate KPI anomalies: artifact ruleouts, upstream cause tracing, external/internal event correlation, leading hypothesis with confidence.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "win-loss-pattern-extractor",
        "title": "Win/Loss Pattern Extractor",
        "tldr": "Reads a batch of won + lost deals (or won/lost campaigns) and extracts patterns: what wins look like, what loses, where the data is thin, what to test next.",
        "category": "analysis",
        "tags": ["sales", "win-loss", "pattern-analysis", "go-to-market"],
        "best_for_tags": ["sales-leadership", "marketing", "pm"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Quarterly win/loss review", "example": "Last quarter's 40 deals (24 won, 16 lost) — what patterns?"},
            {"scenario": "Campaign performance review", "example": "10 marketing campaigns — which worked, why."},
            {"scenario": "RFP pattern study", "example": "30 RFP responses last year — common loss-reasons."},
            {"scenario": "Funnel-stage loss analysis", "example": "Deals lost in late-stage vs early-stage — different patterns?"},
        ],
        "when_not_to_use": "Skip with too few deals (n<15) — patterns are anecdotal. Skip without sufficient deal-context (need notes, stage, ICP fit, source).",
        "full_prompt": """You are a win/loss pattern analyst. Extract patterns from a batch of won + lost deals.

INPUT
- Deal records (won + lost) with context: {deals}
- Each deal includes: ICP fit, stage where won/lost, sales-cycle length, ACV, source, competitors mentioned, key objections, notes.
- Period: {period}
- Specific questions being asked: {questions}

OUTPUT

## 1. Sample summary
- **Total deals:** ___ (won: ___ / lost: ___)
- **Average deal size:** ___ (won) vs ___ (lost)
- **Average sales-cycle:** ___ (won) vs ___ (lost)
- **Period:** ___

## 2. Win patterns
What characterizes a WIN:
- **ICP fit:** what % were ideal-fit?
- **Source pattern:** which sources convert best?
- **Engagement signals:** demos, POCs, exec involvement?
- **Common objection-handling:** how were the top 3 objections addressed?
- **Competitor presence:** wins against who? lost-to whom in close 2nd?
- **Time-to-close:** are quick wins different from slow wins?

## 3. Loss patterns
What characterizes a LOSS:
- **Stage lost at:** early (discovery) / mid (POC) / late (decision)
- **Loss reasons cited:** ranked by frequency.
- **Loss reasons UNDER-cited but suggested by data:** patterns sales reps may not have noticed.
- **Competitive losses:** what beats us?
- **'No decision' losses:** how often is the loss to STATUS QUO?

## 4. Differentiated insights
What's DIFFERENT between wins and losses (controlling for size, source, etc.):
- "Wins had 3+ stakeholder engagement; losses averaged 1.5."
- "Wins mentioned security concerns and we addressed them in pre-demo; losses ran demo first."
- "Losses that came back later as wins shared this pattern: ___"

## 5. ICP refinement signals
- **Where ICP definition is too LOOSE:** segments winning but not in ICP.
- **Where ICP definition is too TIGHT:** ideal-ICP losing for non-ICP reasons.
- **Recommended ICP refinements:** ___

## 6. Sales-process pivots
Based on patterns:
- **What to do MORE of:** ___ (concrete behavior)
- **What to STOP doing:** ___
- **What to TEST:** ___ (specific change for next quarter)

## 7. Data gaps
- What we couldn't analyze because data was thin.
- What we'd want recorded going forward (e.g., 'capture competitor name on every loss').

## 8. The 'hindsight bias' check
Common pitfalls when reading win/loss:
- **Mistaking correlation for causation:** "all wins had POCs" might mean POC works OR might mean only high-confidence deals get POCs.
- **Survivorship bias:** wins still in pipeline are over-represented if you cherry-pick.
- **Salesperson narrative:** loss-reasons cited by reps are often face-saving.

For THIS analysis, where could hindsight bias mislead?

CRITICAL RULES
- Patterns are EVIDENCE-BASED (data + notes), not narrative-driven.
- Differentiated insights highlight what's TRULY different between wins/losses.
- 'No decision' losses (loss to status quo) tracked — often largest bucket.
- Hindsight-bias check surfaces interpretation errors.
- Recommendations are CONCRETE — test-able next sprint.

DEALS
{deals}

Begin.""",
        "input_variables": [
            {"name": "deals", "type": "string", "description": "Deal records", "required": True, "example": "40 deals last quarter. Won (24): Acme - $80k ACV, sourced inbound, fintech, 3-stakeholder, 45-day cycle. Lost (16): BetaCo - $40k attempted, lost at POC to competitor X. ..."},
            {"name": "period", "type": "string", "description": "Period", "required": True, "example": "Q1 2026 (Jan-Mar)"},
            {"name": "questions", "type": "string", "description": "Specific questions", "required": False, "example": "Why are we losing late-stage deals to competitor X? Is our mid-market ICP definition wrong?"},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Eight sections: sample summary, win patterns, loss patterns, differentiated insights, ICP refinement signals, sales-process pivots, data gaps, hindsight-bias check.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest on hindsight-bias surfacing + honest differentiated insights."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; can take rep narratives at face value — re-pin bias check."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Long-context advantage for 40+ deal corpora."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Workable for 20-30 deals; thins on larger corpora and pattern detection."},
        ],
        "variations": [
            {"label": "Lost-deals deep dive", "description": "Focus only on losses.", "prompt_snippet": "Skip win sections. Deep analysis of losses only: where lost, why cited, why ACTUALLY lost, what would have changed it."},
            {"label": "Competitor-specific", "description": "Beat competitor X.", "prompt_snippet": "Filter to deals where competitor X was mentioned. Surface patterns where we win vs lose against them specifically."},
            {"label": "Segment-narrowed", "description": "Specific segment.", "prompt_snippet": "Filter to a specific segment (size / industry / geo). Pattern-find within. Used when overall patterns hide segment-specific dynamics."},
        ],
        "failure_modes": [
            {"symptom": "Takes loss reasons at face value.", "fix": "Re-pin: 'loss reasons cited by reps are often face-saving. Cross-check with DATA where possible.'"},
            {"symptom": "Misses 'no decision' losses.", "fix": "Force: 'no-decision losses tracked separately. They\\'re often largest bucket, and the framing is different.'"},
            {"symptom": "Generic recommendations.", "fix": "Hard rule: 'each pivot is CONCRETE behavior. Not \"emphasize ROI\" — say \"in discovery, ask buyer to share their internal ROI calc on existing solution.\"'"},
            {"symptom": "Skips hindsight-bias check.", "fix": "Add: 'section 8 mandatory. Pattern analysis without bias-check is just storytelling.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["sales-objection-handling-playbook", "competitor-feature-shipped-analysis", "user-feedback-theme-extractor"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["win-loss-analysis", "icp"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How many deals to make this useful?", "answer": "Minimum 15-20 for noisy signal; 40+ for confident patterns. Below 15, treat output as hypotheses to validate later, not conclusions."},
            {"question": "What about deals still in pipeline?", "answer": "Exclude — they're not yet won/lost. Their inclusion biases toward optimism (active deals overrepresented vs final outcomes)."},
            {"question": "Why so much focus on hindsight bias?", "answer": "Win/loss patterns tell stories. Stories are persuasive. But the most common error is concluding 'X causes wins' when X just correlates. The bias check forces honest interpretation."},
            {"question": "Should I share with sales reps?", "answer": "Yes — but focus on the BEHAVIORAL recommendations (section 6), not the loss-reason ranking (section 3). Reps respond to actionable behavior changes."},
        ],
        "meta_title": "Win/Loss Pattern Extractor — Analysis Prompt",
        "meta_description": "Extract patterns from won + lost deals: win/loss characteristics, differentiated insights, ICP refinement, concrete sales-process pivots, bias check.",
        "version": "v2.0",
        "release_status": "stable",
    },
]
