"""Analysis prompts — batch 3."""

RECORDS = [
    {
        "slug": "log-pattern-extractor",
        "title": "Log Pattern Extractor From Sample Lines",
        "tldr": "From a sample of log lines, extract recurring patterns: frequent error types, timing patterns, anomalies vs baseline, suspicious clusters. Returns ranked list with example lines per pattern.",
        "category": "analysis",
        "tags": ["log-analysis", "pattern-extraction", "observability", "anomaly"],
        "best_for_tags": ["incident-investigation", "log-mining", "ops"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Investigating a production issue", "example": "Last hour's error logs → top 5 error patterns + likely root cause."},
            {"scenario": "Pre-alerting on noisy services", "example": "Identify dominant error types so on-call can deprioritize the noise."},
            {"scenario": "Post-incident summary", "example": "Extract patterns from the incident window for the postmortem."},
            {"scenario": "Vendor app log audit", "example": "Black-box log sample → understand what the service is doing."},
        ],
        "when_not_to_use": "Skip for high-volume real-time analysis (use a log platform — Datadog, Splunk). Skip when you have proper structured logging — query directly.",
        "full_prompt": """You are analyzing log lines to extract patterns.

INPUT
- Log sample (10-200 lines): {logs}
- Time window the sample covers: {window}
- Service/context: {service}
- Known baseline (optional): {baseline}

OUTPUT

## 1. Pattern inventory
Top 5-10 recurring patterns. For each:

### Pattern N: <short label>
- Frequency: N lines / total
- Template: log shape with variables abstracted (e.g., ‘Connection refused to db-{host}:{port}’)
- 2 example lines (verbatim)
- Severity: error / warning / info
- Possible cause: 1-2 sentence diagnosis

## 2. Anomalies (departures from baseline)
If baseline provided, what's NEW or AMPLIFIED in this sample:
- New patterns not seen in baseline
- Frequencies way up or down

If no baseline, anomalies = unexpected-looking patterns (low frequency but high severity).

## 3. Time clustering
Are patterns clustered in time?
- Burst at HH:MM (5 of 10 errors in 30 seconds)
- Steady throughout
- Periodic (every X minutes)

## 4. Root-cause hypotheses
2-3 plausible root causes for the dominant patterns. For each:
- The hypothesis (specific)
- Evidence in the log sample
- What additional info would confirm / refute

## 5. Recommended next actions
- Immediate: what to check NOW
- Short-term: monitoring to add
- Long-term: how to reduce log noise / improve signal

RULES
- Templates abstract variables ({host}, {user_id}); don't include raw values in template.
- Severity ladder: error (action needed) / warn (notice but not urgent) / info (operational chatter).
- Hypotheses must be falsifiable — give the team something to test.
- Don't invent log lines; only patterns that appear in input.

SAMPLE
{logs}

Begin.""",
        "input_variables": [
            {"name": "logs", "type": "string", "description": "Sample log lines", "required": True, "example": "2024-04-12 10:23:15 ERROR Connection refused to db-prod-1:5432\\n2024-04-12 10:23:16 ERROR Connection refused to db-prod-1:5432\\n..."},
            {"name": "window", "type": "string", "description": "Time window covered", "required": True, "example": "Last 1 hour"},
            {"name": "service", "type": "string", "description": "Service or context", "required": True, "example": "Order processing service, production environment"},
            {"name": "baseline", "type": "string", "description": "What normal looks like", "required": False, "example": "Usually 5-10 errors/hour, mostly retry-related"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Five sections: pattern inventory with templates, anomalies, time clustering, root-cause hypotheses, recommended actions.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on falsifiable hypotheses + honest baselines."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes inflates frequencies — re-pin to actual sample."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; time-clustering can be coarse."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Surface patterns OK; weaker on root-cause hypotheses."},
        ],
        "variations": [
            {"label": "JSON output for automation", "description": "Structured for piping.", "prompt_snippet": "Replace markdown with: ‘output JSON: {patterns: [{template, count, severity, examples}], anomalies, hypotheses}.’"},
            {"label": "Multi-service correlation", "description": "Cross-service patterns.", "prompt_snippet": "Accept logs from multiple services; identify patterns that correlate temporally across services."},
            {"label": "Compare to prior window", "description": "Diff against last hour same-time.", "prompt_snippet": "Accept (current_window, comparison_window); produce diff: new patterns, vanished patterns, frequency changes."},
        ],
        "failure_modes": [
            {"symptom": "Frequencies don't match actual sample.", "fix": "Re-pin: ‘count only lines in the provided sample; don't extrapolate.’"},
            {"symptom": "Hypotheses are generic (‘network issues’).", "fix": "Add: ‘every hypothesis names a specific component/cause and how to verify.’"},
            {"symptom": "Templates include raw values.", "fix": "Add: ‘in templates, replace varying values with {placeholders}; literal values only if they're stable across samples.’"},
            {"symptom": "Time clustering missed.", "fix": "Force: ‘look at the timestamp distribution; bursts of >3 errors within 30 seconds count as cluster.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["root-cause-five-whys", "metric-anomaly-explainer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["log-analysis", "pattern-extraction"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Sample size?", "answer": "50-200 lines is the sweet spot. Fewer = miss patterns. More and the LLM gets noisy; better to extract patterns + drill into specific lines separately."},
            {"question": "How accurate?", "answer": "Reliable for clear recurring patterns. Less reliable for rare-but-important events. Use as triage; verify hypotheses with proper log tools."},
            {"question": "Why not just use a regex / log analyzer?", "answer": "Regex requires you to know what patterns exist. LLM extracts them from semantic content. Best used together: LLM discovers patterns, regex extracts them at scale."},
        ],
        "meta_title": "Log Pattern Extractor From Sample Lines — Prompt",
        "meta_description": "Extract recurring patterns from log samples: templates with placeholders, frequency, time clusters, falsifiable root-cause hypotheses.",
    },
    {
        "slug": "ab-test-result-deep-dive",
        "title": "A/B Test Result Deep-Dive (Beyond p-value)",
        "tldr": "Reads A/B test results and surfaces insights beyond the headline: segment effects, novelty bias, sample-size adequacy, what the metric DOESN'T capture, and recommended action.",
        "category": "analysis",
        "tags": ["ab-test", "experimentation", "statistics", "decision-analysis"],
        "best_for_tags": ["growth", "experimentation", "data-decision"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Significant result — ship or not?", "example": "‘Variant won at p=0.03’ → deeper look at heterogeneity, novelty, costs."},
            {"scenario": "Null result — what now?", "example": "Inconclusive test → was sample size adequate? Were segments differentially affected?"},
            {"scenario": "Conflicting metrics", "example": "Click-through up but downstream conversion down → reconcile."},
            {"scenario": "Pre-decision review", "example": "PM wants to ship; analyst probe for what the headline obscures."},
        ],
        "when_not_to_use": "Skip for simple wins where headline + obvious cost analysis is enough. Skip when you can't access segment-level data — analysis is shallow without it.",
        "full_prompt": """You are an experimentation analyst. Don't just read the headline; surface what it obscures.

INPUT
- Test name and hypothesis: {hypothesis}
- Headline result: {headline}                          (lift %, p-value, sample sizes)
- Segment data (if available): {segment_data}
- Time-series of metric during test: {timeseries}
- Cost/risk considerations: {cost_considerations}

OUTPUT

## 1. Headline restated
The result in one sentence with confidence and effect size honestly stated.

## 2. Statistical adequacy
- Was sample size sufficient for the claimed effect?
- Is the p-value robust (or borderline)?
- Multiple comparisons concern? (Tested many metrics or segments?)
- Sequential testing concern? (Peeked early?)

## 3. Heterogeneity analysis
Did the effect differ across segments?
- Did the win come from one segment dominating? Could be Simpson's paradox.
- Are there segments where the variant LOST?
- Is the effect plausible across all observed segments, or driven by a slice?

## 4. Novelty / decay
- Did the effect change over time during the test?
- Novelty bias suspect (effect strong day 1, fading)?
- Did the test run long enough to see steady-state behavior?

## 5. What the metric doesn't capture
- Downstream effects (retention, LTV, churn)
- Operational cost of the variant (support tickets, ops complexity)
- Brand / trust impact
- Effects on non-tested users (e.g., cross-product effects)

## 6. Recommendation
- Ship / hold / extend / iterate
- If ship: with what monitoring or follow-up tests?
- If hold: what would change the call?
- Confidence in the recommendation (high / medium / low)

## 7. Open questions
2-4 things this analysis can't answer; what data or follow-up would resolve.

RULES
- Don't manufacture issues; if the test is clean, say so plainly.
- Don't say ‘p < 0.05 therefore ship’; consider effect size, cost, side effects.
- Be honest about confidence; ‘medium’ is a valid recommendation.

INPUT DATA

Hypothesis: {hypothesis}
Headline: {headline}
Segments: {segment_data}
Time-series: {timeseries}
Costs/risks: {cost_considerations}

Begin.""",
        "input_variables": [
            {"name": "hypothesis", "type": "string", "description": "Test hypothesis", "required": True, "example": "Adding social proof to checkout will increase completion rate"},
            {"name": "headline", "type": "string", "description": "Headline result", "required": True, "example": "Variant: 4.6% checkout completion vs control 4.2%. Lift +9.5%. p=0.03. n=18000 per arm. 14 days."},
            {"name": "segment_data", "type": "string", "description": "Segment-level results", "required": False, "example": "New users (50%): +18% lift. Returning users (50%): -1% (n.s.). Mobile: +14%. Desktop: +2%."},
            {"name": "timeseries", "type": "string", "description": "Effect over time", "required": False, "example": "Days 1-3: +22%. Days 4-7: +12%. Days 8-14: +5%."},
            {"name": "cost_considerations", "type": "string", "description": "Operational costs of variant", "required": False, "example": "Variant requires nightly batch job to refresh social proof counts; +$200/mo infra cost."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: headline restated, statistical adequacy, heterogeneity, novelty/decay, what's-not-captured, recommendation w/ confidence, open questions.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on novelty/decay detection from time series; honest about open questions."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes over-cautious on shipping recommendations."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid stats; heterogeneity analysis can be light."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Statistical reasoning shallow; verify against domain expert."},
        ],
        "variations": [
            {"label": "Bayesian framing", "description": "Posterior credible intervals, not p-values.", "prompt_snippet": "Add: ‘re-frame the statistical adequacy section using Bayesian thinking — posterior probability variant is best, credible interval on effect.’"},
            {"label": "Sequential test", "description": "Account for peek penalty.", "prompt_snippet": "Add: ‘if test peeked at results before pre-set sample size, the headline p-value is inflated; estimate the deflation needed.’"},
            {"label": "Power retrospective", "description": "Was the test under-powered?", "prompt_snippet": "Add: ‘compute MDE (minimum detectable effect) given final sample size; if observed effect is smaller, the test was likely under-powered to declare a winner with low Type II risk.’"},
        ],
        "failure_modes": [
            {"symptom": "Recommendation is ‘ship if p<0.05’.", "fix": "Re-pin: ‘consider effect size, costs, segment heterogeneity, novelty — not just p-value.’"},
            {"symptom": "Heterogeneity section missing.", "fix": "If segment_data provided, FORCE analysis. If not, say so explicitly."},
            {"symptom": "Confidence not stated.", "fix": "Force: ‘rec must include confidence level; ‘medium’ is acceptable.’"},
            {"symptom": "Open questions vague.", "fix": "Add: ‘open questions are specific things that, if known, would change the recommendation.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["a-b-test-result-interpreter", "cohort-retention-analyzer", "metric-anomaly-explainer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["ab-testing", "experimentation", "statistical-power"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should I use Bayesian or frequentist?", "answer": "Both work. Bayesian framing maps better to ‘should we ship?’ decisions; frequentist with explicit power analysis works too. This prompt is methodology-agnostic but the Bayesian variation goes deeper."},
            {"question": "How do I detect novelty bias?", "answer": "Time-series during the test. If effect is strong week 1 and declining, novelty likely. Re-test in a few months to confirm steady-state effect."},
            {"question": "What's the ‘ship anyway’ threshold?", "answer": "When effect size is large AND cost-of-shipping is low AND no segment lost meaningfully AND time-series doesn't show decay. p<0.05 is necessary but not sufficient."},
        ],
        "meta_title": "A/B Test Result Deep-Dive (Beyond p-value) — Prompt",
        "meta_description": "Analyze A/B tests beyond the headline: statistical adequacy, heterogeneity, novelty decay, what's not captured, confidence in rec.",
    },
]
