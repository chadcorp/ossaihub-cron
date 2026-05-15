"""Analysis prompts — batch 4."""

RECORDS = [
    {
        "slug": "incident-postmortem-blameless",
        "title": "Blameless Incident Postmortem",
        "tldr": "Generates a postmortem report from incident notes: timeline, contributing factors (not 'root cause'), what worked, what didn't, action items with owners. Blameless framing — focuses on systems not people.",
        "category": "analysis",
        "tags": ["postmortem", "incident", "blameless", "sre"],
        "best_for_tags": ["engineering", "sre", "ops"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "After every production outage", "example": "Notes + timeline → structured postmortem in 30 min instead of 3 hours."},
            {"scenario": "Multi-team incident", "example": "Several teams contributed; this prompt synthesizes without finger-pointing."},
            {"scenario": "Near-miss documentation", "example": "Caught a problem before it hit users; still valuable to document the contributing factors."},
            {"scenario": "Pattern surfacing", "example": "Quarterly review of multiple postmortems to find systemic patterns."},
        ],
        "when_not_to_use": "Skip for trivial incidents (5-min blip nobody noticed). Skip when you don't yet have basic facts — gather facts first.",
        "full_prompt": """You are writing a blameless incident postmortem. Structure facts, learn systemically, no naming-and-shaming.

INPUT
- Incident summary (one paragraph): {incident_summary}
- Timeline (raw timestamped notes): {timeline_notes}
- People involved (roles, not names): {people_roles}
- Impact (users affected, duration, severity): {impact}
- What worked (response): {what_worked}
- What didn't work: {what_didnt}
- Existing process / runbook: {existing_process}

OUTPUT STRUCTURE

# Postmortem: <Incident name> — <date>

## Summary (3 sentences)
What happened. Severity. Resolution time.

## Timeline (UTC)
| Time | Event | Action taken |
|---|---|---|
| 10:30 | Spike in 500 errors | Auto-alert fired |
| 10:42 | On-call paged | Investigation begins |
| ... | ... | ... |

Format raw timeline notes into this table. Each row is one observable event or response.

## Impact
- Users affected: <number or %>
- Duration of degraded service: <minutes>
- Revenue impact: <if measurable>
- SLA breach: <yes/no, by how much>
- Reputational impact: <observable signals, e.g., support tickets, social>

## Contributing factors (NOT "root cause" — multi-factor)
Most incidents have multiple contributing factors. List 2-5:

### Factor N: <one-line description>
- What it is
- How it contributed to this incident
- How long it had existed before this incident (latent or new?)
- What systems / processes touched it

## What worked
2-4 things. Specific. With names of mechanisms (not people).
- "Auto-rollback fired correctly when error rate crossed 5%."
- "On-call response within 8 min of page (SLA: 15 min)."

## What didn't work
2-4 things. Honest. No blame — focus on system behavior.
- "Alert fired but didn't include the affected region, slowing initial diagnosis."
- "Runbook for this scenario was 18 months old; outdated tools."

## Counterfactuals (what would have helped)
What changes to systems or processes — IF in place BEFORE — would have prevented or reduced this?
2-4 specific things, even if some are expensive.

## Action items
| Action | Owner (role) | Priority | Target date | Status |
|---|---|---|---|---|

- Priority: P0 (do this week), P1 (this month), P2 (this quarter)
- Owner is ROLE not person (or team)
- Status starts as "open"

## Lessons (for future similar incidents)
2-3 generalizable lessons — patterns you'd want a future engineer to remember.

CRITICAL RULES
- Use ROLES not names: "the on-call engineer", "the deploying team", "the customer-facing CS lead".
- Don't speculate about intent. ("X engineer should have noticed Y" is blame. "The alerting system did not surface Y; engineer was monitoring different metric" is fact.)
- "Root cause" mentality leads to single-culprit blame. List CONTRIBUTING FACTORS as a graph.
- Action items must have owners (role) and dates. Open-ended action items don't get done.

INPUTS

INCIDENT: {incident_summary}

TIMELINE: {timeline_notes}

IMPACT: {impact}

WHAT WORKED: {what_worked}

WHAT DIDN'T: {what_didnt}

Now draft the postmortem.""",
        "input_variables": [
            {"name": "incident_summary", "type": "string", "description": "One-paragraph summary", "required": True, "example": "API 500 errors for 43 min affecting 12% of Pro+ requests in EU region. Root cause: split-brain in routing service after network partition."},
            {"name": "timeline_notes", "type": "string", "description": "Raw timestamped notes", "required": True, "example": "10:30 errors start; 10:42 alert fires; 10:51 on-call investigates; 11:00 identifies routing issue; 11:13 mitigated"},
            {"name": "people_roles", "type": "string", "description": "Roles involved", "required": True, "example": "On-call engineer (platform); Senior platform engineer; Incident commander (eng manager); CS lead"},
            {"name": "impact", "type": "string", "description": "Impact details", "required": True, "example": "~12% of EU Pro+ requests failed; 43 min duration; SLA breached (5min target); ~$8k revenue impact; 6 customers filed tickets"},
            {"name": "what_worked", "type": "string", "description": "Response that worked", "required": True, "example": "Auto-alert fired in 12 min of incident start. Rollback playbook executed cleanly. CS comms went out within 30 min."},
            {"name": "what_didnt", "type": "string", "description": "Response that didn't work", "required": True, "example": "Network partition wasn't in pager runbook — engineer had to read source. Alert didn't include region tag — took 8 min to localize."},
            {"name": "existing_process", "type": "string", "description": "Existing runbook/process", "required": False, "example": "Standard incident response (Severity 1 = page lead + auto-CS-notify)"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Postmortem with summary, UTC timeline table, impact, contributing factors, what-worked, what-didn't, counterfactuals, action items table, lessons.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Blameless framing holds; specific contributing factors."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes drifts to single-root-cause — re-pin multi-factor."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; counterfactuals section can be generic."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple incidents; thin on systemic analysis."},
        ],
        "variations": [
            {"label": "Five-whys appendix", "description": "Run Five Whys on the worst contributing factor.", "prompt_snippet": "Add Appendix: ‘Five Whys analysis on the worst contributing factor (highest customer impact). Use the evidence-required pattern.’"},
            {"label": "Multi-incident pattern surfacer", "description": "When >1 similar incidents.", "prompt_snippet": "Add: ‘this is incident N of type X. Compare to prior incidents (provided); identify pattern that's NOT being addressed by accumulated action items.’"},
            {"label": "Customer-facing version", "description": "Sanitize for external sharing.", "prompt_snippet": "Add Section: ‘also produce a customer-facing version — same facts but no internal team names, no security-sensitive infra details.’"},
        ],
        "failure_modes": [
            {"symptom": "Names individuals (blame).", "fix": "Re-pin: ‘ROLES not names — ‘the on-call engineer’ not ‘Alice.’’"},
            {"symptom": "Single root cause framing.", "fix": "Add: ‘every incident has MULTIPLE contributing factors. List at minimum 2.’"},
            {"symptom": "Action items lack owner/date.", "fix": "Force: ‘every action item has owner (role) and target date. ‘Investigate further’ without owner is not an action item.’"},
            {"symptom": "Counterfactuals are obvious / cheap.", "fix": "Add: ‘list counterfactuals even if EXPENSIVE — the goal is to surface ideas, not pre-filter by feasibility.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["root-cause-five-whys", "post-incident-customer-comms"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["postmortem", "blameless-culture"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why blameless?", "answer": "Postmortems that name individuals create incentives to hide future incidents. Systems-focused postmortems surface contributing factors that can be fixed. Long-term incident rate drops with blameless cultures."},
            {"question": "How fast after the incident?", "answer": "Draft within 48 hours while details are fresh. Review meeting within a week. Action items reviewed at sprint or quarterly intervals."},
            {"question": "What if a person genuinely made a mistake?", "answer": "Describe the action without naming. ‘A config change was deployed without the canary check; the deploy tooling didn't enforce canary by default.’ The system allowed the mistake."},
        ],
        "meta_title": "Blameless Incident Postmortem — Prompt",
        "meta_description": "Structured incident postmortem: timeline, contributing factors (multi-cause), what worked/didn't, action items with owners. Blameless framing.",
    },
    {
        "slug": "user-feedback-theme-extractor",
        "title": "User Feedback Theme Extractor",
        "tldr": "Reads a batch of user feedback (reviews, survey responses, support tickets, NPS comments) and extracts themes with frequency, sentiment, and representative quotes. Distinguishes signal from noise.",
        "category": "analysis",
        "tags": ["user-feedback", "themes", "sentiment", "voice-of-customer"],
        "best_for_tags": ["product", "research", "vocs"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Weekly review of new feedback", "example": "200 NPS comments → 8 themes ranked by frequency + sentiment."},
            {"scenario": "Pre-release feedback synthesis", "example": "Beta users gave 150 comments; this prompt surfaces what's about to ship as feedback."},
            {"scenario": "App store review monitoring", "example": "App store + Reddit + Twitter mentions → themes + trend (vs last month)."},
            {"scenario": "Customer interview synthesis", "example": "20 customer interview transcripts → recurring themes + outliers worth attention."},
        ],
        "when_not_to_use": "Skip for tiny samples (<20 — just read them). Skip when feedback is already structured (closed-form questions; use stats instead).",
        "full_prompt": """You are extracting themes from user feedback. Signal over noise; specific over generic.

INPUT
- Feedback items (each: source, content, optional metadata like rating/segment): {feedback_items}
- Domain context: {domain}
- Compare-to (optional, prior batch results): {compare_to}

OUTPUT

## 1. Themes (5-12)
Each theme:

### Theme N: <2-5 word label>
- Frequency: <count> / <total>
- Sentiment: positive / negative / mixed / neutral (with breakdown if relevant)
- What customers are saying (1-2 sentences synthesizing the pattern)
- 2-3 representative VERBATIM quotes (with source attribution)
- Severity (for negatives): blocker / major / minor / annoyance
- Likely cause / addressable through: <product / pricing / docs / support / nothing>

## 2. Surprising minority view
1-2 things from a small number of feedback items but worth attention:
- Could be early signal of emerging issue
- Could be edge-case but high-stakes user
- Could be insight the majority missed

## 3. What feedback is NOT telling you
2-3 things people aren't talking about that you'd expect:
- Could be silent satisfaction
- Could be users who already left
- Could be a feature whose USERS aren't in this feedback channel

## 4. Trend vs prior batch (if compare_to provided)
- Themes that grew (with magnitude)
- Themes that shrank
- New themes
- Vanished themes

## 5. Top 3 actionable insights
What product/team should DO with this. Specific, prioritized.

CRITICAL RULES
- VERBATIM quotes — never paraphrase. Sources attributed (anonymized OK: ‘a Pro-tier user’, ‘an enterprise customer’).
- THEMES are PATTERNS, not single complaints. A theme needs at least 3 distinct feedback items unless flagged as surprising-minority.
- Sentiment is data, not opinion. Count the directional language.
- Don't manufacture themes to hit a number — if there are only 5 real ones, return 5.

FEEDBACK ITEMS
{feedback_items}

DOMAIN
{domain}

Begin.""",
        "input_variables": [
            {"name": "feedback_items", "type": "string", "description": "Feedback items list", "required": True, "example": "[NPS, 8] ‘The dashboard is slow to load — 5+ seconds.’\\n[review, 3 stars] ‘Crashes when I try to upload PDFs over 50MB.’\\n[ticket, support] ‘The export feature is great when it works.’\\n..."},
            {"name": "domain", "type": "string", "description": "Product domain", "required": True, "example": "B2B SaaS document automation tool"},
            {"name": "compare_to", "type": "string", "description": "Prior batch summary", "required": False, "example": "Last month's themes: slow dashboard (12), pdf upload errors (8), missing export formats (6)"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "5-12 themes with frequency/sentiment/verbatim quotes/severity. Minority view. What's-not-said. Trend (if compare-to). Top 3 actions.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong verbatim discipline; honest about minority-vs-pattern threshold."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes paraphrases — re-pin verbatim."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; minority view section often thin."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for routine synthesis; less depth on what's-not-said."},
        ],
        "variations": [
            {"label": "Quant-leaning", "description": "Emphasize counts and distributions.", "prompt_snippet": "Add: ‘include a frequency distribution chart description for each theme; %positive vs %negative split.’"},
            {"label": "Segment-aware", "description": "Themes per segment (paid vs free, mobile vs desktop, etc.).", "prompt_snippet": "Add: ‘if segment metadata available, surface themes that are SEGMENT-SPECIFIC; flag when a theme is concentrated in one segment.’"},
            {"label": "Action-only", "description": "Skip themes section, just output prioritized actions.", "prompt_snippet": "Replace themes section with: ‘Top 5 actions, prioritized by (frequency × severity × addressability).’"},
        ],
        "failure_modes": [
            {"symptom": "Paraphrased quotes (not verbatim).", "fix": "Re-pin: ‘quotes are verbatim. If source ambiguous, mark [paraphrased].’"},
            {"symptom": "Themes invented to hit 10.", "fix": "Add: ‘if there are 4 real themes, return 4. Don't manufacture filler.’"},
            {"symptom": "‘What's not said’ section empty.", "fix": "Force: ‘every feedback batch has notable silences; surface 2-3.’"},
            {"symptom": "Top 3 actions are vague (‘improve performance’).", "fix": "Add: ‘each action specifies WHAT to change + WHO owns + by WHEN. Vague actions don't ship.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["thematic-coding-from-transcripts", "review-pattern-finder"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["voice-of-customer", "thematic-analysis"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How many feedback items is enough?", "answer": "20+ for rough patterns; 100+ for confident frequencies. Below 20, every item is a potential theme — too much noise."},
            {"question": "Will it bias toward complaints?", "answer": "Slightly — negative feedback is more linguistically distinct. Balance via segment metadata (ratings) and explicit positive theme search."},
            {"question": "How often to run?", "answer": "Weekly for active feedback channels (in-product, NPS). Monthly for slow channels (reviews). Quarterly for full-org synthesis."},
        ],
        "meta_title": "User Feedback Theme Extractor — Prompt",
        "meta_description": "Extract themes from user feedback: frequency, sentiment, verbatim quotes, severity, what's NOT said, trend vs prior batch, prioritized actions.",
    },
    {
        "slug": "product-metric-tree-builder",
        "title": "Product Metric Tree From a North-Star Goal",
        "tldr": "Decomposes a north-star metric into a tree of input metrics, leading indicators, and lagging measures. Each branch shows the causal logic, the lever, and the team that owns it.",
        "category": "analysis",
        "tags": ["metrics", "tree", "kpis", "product-strategy"],
        "best_for_tags": ["product", "growth", "leadership"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Setting up product analytics", "example": "‘Increase weekly active users’ → tree of inputs (acquisition + activation + retention) → leading indicators per branch."},
            {"scenario": "Diagnosing why a metric isn't moving", "example": "Revenue flat for Q. Tree decomposition surfaces which input is the bottleneck."},
            {"scenario": "Aligning teams to a shared north star", "example": "Each team sees where their work feeds into the tree."},
            {"scenario": "Onboarding new PM", "example": "Quick orientation on what we measure + why."},
        ],
        "when_not_to_use": "Skip when the metric is already simple and unambiguous. Skip when teams resist measurement (then fix culture first, not the tree).",
        "full_prompt": """You are decomposing a north-star metric into a tree of contributing metrics, leading indicators, and team ownership.

INPUT
- North-star metric: {north_star}
- Business context: {business_context}
- Team structure: {team_structure}
- Time horizon: {time_horizon}

OUTPUT

## Level 0: North Star
- Metric: <north_star>
- Definition: how it's measured (be specific)
- Cadence: how often it's reviewed
- Owner: which executive
- Lagging indicator (how much it lags from causes): <e.g., 3 months>

## Level 1: Primary inputs (3-5)
Each: a metric that DIRECTLY contributes to the north star.

### Input N: <metric name>
- Causal logic: how this drives north star (in 1 sentence)
- Cadence: daily / weekly / monthly
- Owner: team or role
- Healthy range: what the metric should be
- Current state: <if known>

## Level 2: Sub-inputs (per primary input)
Each primary input gets 2-4 sub-inputs.

Same structure (metric, causal logic, cadence, owner, healthy range).

## Level 3: Leading indicators
For each Level-2 sub-input, list 1-2 LEADING indicators — signals visible BEFORE the sub-input moves.

Example: if sub-input is "activated users in week 1", a leading indicator could be "% completed onboarding step 3 in hour 1".

## Levers (decision points)
For each branch, identify the LEVERS the team can pull. A lever is something concrete they can DO that moves the metric.
- Bad lever: "improve UX"
- Good lever: "reduce onboarding from 6 to 3 steps"

3-7 levers across the tree.

## Anti-metrics (what should NOT move)
2-3 metrics that, if they move in the WRONG direction, indicate gaming. Example: increasing DAU by trade-off-against retention.

## Conflicts
Where do two branches conflict? Example: "growth team's referral campaign + retention team's onboarding revamp may compete for activation funnel attention."

CRITICAL RULES
- Every metric has an OWNER (role/team) and a CADENCE. Without ownership, metrics drift.
- Leading indicators are the highest-leverage view — invest in instrumenting them.
- Anti-metrics keep the team honest. ‘Move metric X without moving anti-metric Y.’

NORTH STAR: {north_star}

CONTEXT: {business_context}

TEAMS: {team_structure}

Build the tree.""",
        "input_variables": [
            {"name": "north_star", "type": "string", "description": "North-star metric", "required": True, "example": "Weekly Active Users (WAU) of paid customers"},
            {"name": "business_context", "type": "string", "description": "Business model context", "required": True, "example": "B2B SaaS, $30k average ACV, freemium model, primary value is dashboard usage"},
            {"name": "team_structure", "type": "string", "description": "Team org", "required": True, "example": "Growth team (acquisition + activation), Product team (core experience), CS team (retention + expansion), Engineering (platform)"},
            {"name": "time_horizon", "type": "string", "description": "Time horizon for the tree", "required": True, "example": "Quarterly, with weekly reviews"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Level 0 north star definition; Level 1 primary inputs (3-5); Level 2 sub-inputs (2-4 per); Level 3 leading indicators; levers; anti-metrics; conflicts.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong causal logic; surfaces conflicts honestly."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can over-decompose (5+ levels) — cap at 3."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; leading indicators sometimes too generic."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple trees."},
        ],
        "variations": [
            {"label": "Numeric tree", "description": "Include actual numbers / formulas.", "prompt_snippet": "Add: ‘include a numeric formula: north star = f(input_1, input_2). Provide elasticity estimates if available.’"},
            {"label": "Rebuild from existing dashboard", "description": "Audit existing metrics into tree shape.", "prompt_snippet": "Accept a list of current dashboard metrics; place them in the tree; flag metrics that don't fit anywhere (probably vanity)."},
            {"label": "Counter-metric stress-test", "description": "Imagine teams gaming each branch.", "prompt_snippet": "After each branch, write: ‘How could a team game this metric without genuine improvement? What anti-metric prevents it?’"},
        ],
        "failure_modes": [
            {"symptom": "Tree has no ownership.", "fix": "Re-pin: ‘every metric has owner + cadence. Skip if either is missing.’"},
            {"symptom": "Leading indicators are lagging.", "fix": "Add: ‘leading = visible BEFORE the parent metric moves; ‘weekly retention rate’ is NOT leading for weekly retention.’"},
            {"symptom": "Anti-metrics section empty.", "fix": "Force: ‘every metric tree has gaming risks; identify at least 2 anti-metrics.’"},
            {"symptom": "Levers are vague (‘improve X’).", "fix": "Add: ‘lever names a CONCRETE action a team can take this quarter. ‘Improve onboarding’ is not a lever; ‘reduce onboarding steps from 6 to 3’ is.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["okr-quality-audit", "metric-anomaly-explainer", "ab-test-result-deep-dive"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["north-star-metric", "leading-indicator", "metric-tree"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How deep should the tree go?", "answer": "3 levels is usually right. Level 0 = north star, Level 1 = drivers, Level 2 = drivers-of-drivers, Level 3 = leading indicators. Beyond 3 levels, you're over-fitting."},
            {"question": "How often update?", "answer": "Annually for the structure; weekly for the values. The shape is stable; the numbers move."},
            {"question": "What if teams disagree on causal logic?", "answer": "That's productive. Map the conflicting causal models; run experiments to disambiguate. Disagreement on causal logic > consensus on wrong logic."},
        ],
        "meta_title": "Product Metric Tree From a North-Star Goal",
        "meta_description": "Decompose a north-star metric into inputs, leading indicators, owners, levers, anti-metrics. 3-level tree with explicit causal logic.",
    },
    {
        "slug": "competitor-feature-shipped-analysis",
        "title": "Competitor Just Shipped a Feature — Analysis",
        "tldr": "When a competitor releases a feature, this prompt analyzes: what they shipped, what it means strategically, our options (build/buy/ignore/reposition), and a recommendation with 7-day action items.",
        "category": "analysis",
        "tags": ["competitive-intelligence", "react", "feature-launches"],
        "best_for_tags": ["product-leaders", "founders", "exec-staff"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Big competitor announces", "example": "Slack launches huddles → analyze + decide our response within a week."},
            {"scenario": "Adjacent space encroachment", "example": "A neighbor space added our flagship feature; do we react?"},
            {"scenario": "Funding-fueled launch", "example": "Well-funded startup ships big push; analyze whether to ignore or counter."},
            {"scenario": "Open-source clone of paid feature", "example": "OSS project replicates our paid feature; pricing/positioning implications?"},
        ],
        "when_not_to_use": "Skip for tiny competitive moves with low market impact. Skip when YOU are about to launch the same thing — race to ship, don't write reports.",
        "full_prompt": """You are analyzing a competitive feature launch. Structured analysis → strategic recommendation.

INPUT
- Competitor: {competitor_name}
- Feature shipped: {feature_description}
- Source / how we learned: {source}
- Our product: {our_product}
- Our existing capabilities in this area: {our_capability}
- Our customers' likely reaction: {customer_signal}
- Our resources for a response: {resources}

OUTPUT

## 1. What they shipped (3 sentences)
- Feature in plain English
- What it does for THEIR users
- Quality signal (polished, beta, AI-generated marketing language?)

## 2. Strategic implications
Why does this matter to US specifically?
- Does it commoditize one of our differentiators?
- Does it open a new buyer persona?
- Does it expand the competitor's footprint into our territory?
- Does it signal a strategic pivot?

3-5 specific implications.

## 3. Customer impact prediction
What will OUR customers think?
- Pro-tier customers: <reaction>
- Enterprise customers: <reaction>
- Free-tier customers: <reaction>
- Specific segments at churn risk: <name>

## 4. Options (with cost / time / risk)

### Option A: BUILD (we ship competing feature)
- What we'd need
- Estimated time + cost
- Risk: shipped late, watered-down, opportunity-cost
- When this is right

### Option B: BUY (acquire / partner)
- Candidates
- Estimated cost
- Risk: integration, culture fit, lost focus
- When this is right

### Option C: IGNORE (do nothing, watch)
- What signals would trigger reconsideration
- Risk: market shifts while we wait
- When this is right

### Option D: REPOSITION (change positioning to avoid head-to-head)
- New positioning angle
- What changes in marketing/sales narrative
- Risk: confuses our market, looks defensive
- When this is right

## 5. Recommendation
- Option choice
- Confidence (high / medium / low)
- One-sentence rationale
- Top risk + mitigation

## 6. 7-day action items
What we DO this week. Specific. Owners. Outcomes by Friday.

CRITICAL RULES
- Don't manufacture urgency. Sometimes the right answer is genuinely IGNORE.
- Strategic implications must be SPECIFIC to our positioning, not generic competitive analysis.
- Each option must have honest tradeoffs — no obvious-winner setup.
- 7-day items: even an IGNORE recommendation has actions (monitor, brief sales, etc.).

Now analyze.""",
        "input_variables": [
            {"name": "competitor_name", "type": "string", "description": "Competitor name", "required": True, "example": "Notion"},
            {"name": "feature_description", "type": "string", "description": "What they shipped", "required": True, "example": "AI-generated meeting notes — recording + transcription + auto-summary + action items"},
            {"name": "source", "type": "string", "description": "Source of info", "required": True, "example": "Notion's blog announcement + Hacker News thread"},
            {"name": "our_product", "type": "string", "description": "Our product positioning", "required": True, "example": "AI-powered project management for product teams"},
            {"name": "our_capability", "type": "string", "description": "What we have here today", "required": True, "example": "We don't have native meeting capture; users export from Zoom/Otter and paste into our doc."},
            {"name": "customer_signal", "type": "string", "description": "Customer reaction signals", "required": True, "example": "Several customers have asked for ‘all-in-one’ over the past quarter; 2 enterprise prospects mentioned Notion in their evaluation."},
            {"name": "resources", "type": "string", "description": "Resources available", "required": True, "example": "$200k unallocated budget. 2 eng + 1 designer could be reallocated. 4-month window before our planned launch wave."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: what they shipped, strategic implications, customer impact prediction, 4 options with tradeoffs, recommendation w/ confidence, 7-day action items.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Doesn't manufacture urgency; honest tradeoffs."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes recommends BUILD by default — re-pin ‘ignore is valid.’"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; option tradeoffs can be uneven."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for routine moves; thin on positioning nuance."},
        ],
        "variations": [
            {"label": "Two-competitor sandwich", "description": "When two competitors ship similar.", "prompt_snippet": "Add: ‘competitor B also shipped similar; analyze the pattern — what's the market signal?’"},
            {"label": "OSS-replica variant", "description": "When OSS replicates paid feature.", "prompt_snippet": "Focus options on PRICING and POSITIONING responses, not building. OSS doesn't compete on velocity."},
            {"label": "First-mover catch-up", "description": "We had it first; they did it better.", "prompt_snippet": "Add focus on FOLLOW-UP investment: do we double down or concede the lead?"},
        ],
        "failure_modes": [
            {"symptom": "Recommends BUILD by default.", "fix": "Re-pin: ‘IGNORE is often correct. Build only when option-tradeoff analysis genuinely favors it.’"},
            {"symptom": "Strategic implications are generic (‘market shifting’).", "fix": "Force: ‘each implication names a specific aspect of OUR positioning.’"},
            {"symptom": "Action items vague.", "fix": "Add: ‘every 7-day item has owner + outcome. ‘Investigate further’ isn't an item.’"},
            {"symptom": "Customer impact prediction is one-size-fits-all.", "fix": "Re-pin: ‘different segments react differently. Per-segment specificity.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["competitive-feature-matrix", "competitive-landscape-mapper", "devils-advocate-pre-mortem"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["competitive-intelligence", "strategic-response"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How fast should we respond?", "answer": "Decision in a week; action depending on option. BUILD: months. REPOSITION: weeks. IGNORE: ongoing monitoring. Acting too fast wastes resources; too slow leaks market position."},
            {"question": "Does this work for AI feature launches?", "answer": "Yes — AI features are competitor moves like any other. Stay focused on what it means for YOUR positioning, not generic ‘AI is hot.’"},
            {"question": "What if customers explicitly ask for the competitor's feature?", "answer": "That shifts toward BUILD but not automatically. Some asks are ‘we want X for completeness’ (won't drive churn), others are ‘we'll leave without X’ (drive churn). Separate the two."},
        ],
        "meta_title": "Competitor Feature Launch Analysis — Prompt",
        "meta_description": "Structured response to a competitor feature launch: implications, customer impact, build/buy/ignore/reposition options, recommendation, 7-day actions.",
    },
]
