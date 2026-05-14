"""Analysis prompts — batch 2."""

RECORDS = [
    {
        "slug": "root-cause-five-whys",
        "title": "Root-Cause Analysis Via Five Whys (Sharpened)",
        "tldr": "Modern Five Whys: each ‘why’ must surface a concrete evidence claim, not speculation. Ends with one root cause + one fix that addresses it + the deferred-but-real causes that fix won't touch.",
        "category": "analysis",
        "tags": ["root-cause", "incident-review", "five-whys", "postmortem"],
        "best_for_tags": ["incident-postmortem", "process-improvement", "engineering"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Production incident postmortem", "example": "‘Why did the API outage last 47 minutes?’ — 5 levels deep, each tied to actual evidence."},
            {"scenario": "Recurring user complaint", "example": "‘Why do users keep churning at month 2?’ — surfaces upstream causes beyond ‘onboarding bad.’"},
            {"scenario": "Missed deadline", "example": "‘Why did we miss the Q3 launch?’ — distinguishes scope creep from estimation drift from prioritization."},
            {"scenario": "Quality regression", "example": "‘Why did defect rate triple after the refactor?’"},
        ],
        "when_not_to_use": "Skip when the root cause is genuinely a single technical bug (just fix it). Skip for complex systems where multiple causes interact — use a more sophisticated method like Cynefin or fault tree analysis.",
        "full_prompt": """You are facilitating a Five Whys root-cause analysis. Standard Five Whys is sloppy — yours will be sharper.

RULES
1. Each ‘why’ must surface a CONCRETE evidence claim, not speculation. If you don't have evidence, say so and mark the link as unverified.
2. After Why #5 (or earlier if you hit bedrock), name the ROOT CAUSE explicitly.
3. Avoid the trap of assigning blame ("Sarah forgot..."). The Why chain should surface the SYSTEM that allowed the failure, not the person at the end.
4. If at any Why you can identify multiple parent causes, branch — note the branch and follow the most causally significant one. Don't pretend Five Whys is linear.

INPUT
- The problem to analyze: {problem}
- Known facts (timeline, evidence, what's confirmed): {known_facts}

OUTPUT

## Problem
Restate in one sentence.

## Why 1: <why did X happen?>
- Answer: <answer based on facts>
- Evidence: <specific data, log, observation>
- Confidence: high / medium / low

## Why 2: <why did the answer to Why 1 happen?>
... same pattern ...

(repeat up to Why 5, or stop earlier if bedrock reached)

## Root cause
The single sentence identifying the root cause. Phrased as: "The system permits / fails to prevent / does not detect..."

## Fix that addresses the root cause
What specifically to change. Concrete. Owner. ETA.

## Causes the fix does NOT address
2-3 contributing factors surfaced by the Why chain that the proposed fix leaves alone. Honest about scope.

## Branching causes (if any)
At any Why where you saw multiple parent causes, note the alternate branch you didn't follow and why.

KEY DISTINCTIONS
- People's actions are evidence, not causes. (‘Sarah merged without review’ is data; ‘our process didn't require reviews on critical paths’ is a cause.)
- Recurring failures point to systemic causes; one-offs may legitimately be ‘bad luck’ — but check the rate, not the single instance.

Begin the Whys.""",
        "input_variables": [
            {"name": "problem", "type": "string", "description": "What went wrong", "required": True, "example": "Our checkout flow had a 47-minute outage on March 12 affecting ~$80k in revenue."},
            {"name": "known_facts", "type": "string", "description": "Timeline + evidence", "required": True, "example": "Deploy at 14:03. First alerts 14:08 (error rate). Rolled back at 14:51. Cause: new code called a deprecated downstream API. Deprecation announcement existed; not seen by deploying engineer."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "5 (or fewer) Why levels each with answer + evidence + confidence; then root cause, fix, unaddressed causes, branching causes.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at distinguishing evidence from speculation; honest about confidence."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally jumps to systemic causes too fast — re-pin evidence requirement."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; tends to be soft on blame distinction — restate explicitly."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Standard Five Whys without the sharpening; needs constant re-pinning."},
        ],
        "variations": [
            {"label": "Branched tree", "description": "Track multiple parent causes at every level.", "prompt_snippet": "Replace linear chain with: ‘at each Why, list ALL plausible parents; explore the top 2. Output is a tree, not a line.’"},
            {"label": "Adversarial pair", "description": "Two analyses, one each from a different stakeholder.", "prompt_snippet": "Run analysis twice: once as the on-call engineer, once as the customer. Note where Why chains diverge."},
            {"label": "Pre-mortem variant", "description": "Apply to a hypothetical future failure.", "prompt_snippet": "Use this BEFORE incidents: ‘assume X system will fail next quarter; do Five Whys to surface causes now.’"},
        ],
        "failure_modes": [
            {"symptom": "Each Why is speculation without evidence.", "fix": "Re-pin: ‘every Why has an Evidence row; if you can't cite a fact, mark confidence LOW and ask for missing data.’"},
            {"symptom": "Chain stops at ‘human error’.", "fix": "Add: ‘human error is data, not cause. The next Why is: why did the system allow this human error to cause this outcome?’"},
            {"symptom": "Root cause is a buzzword (‘culture problem’).", "fix": "Force: ‘root cause must be a concrete mechanism or absence (no monitoring, no escalation policy, etc.).’"},
            {"symptom": "Fix is too narrow.", "fix": "Re-pin: ‘fix must address the root cause stated, not just the immediate trigger.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["devils-advocate-pre-mortem", "metric-anomaly-explainer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["root-cause-analysis", "postmortem"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why is Five Whys often criticized?", "answer": "Because most users do it shallow: speculation chains with no evidence. The sharpening rules in this prompt (evidence required, confidence rated, branching allowed) address those failure modes."},
            {"question": "Always 5 levels?", "answer": "No. Stop when you hit bedrock (a fact / decision / constraint that genuinely doesn't have a meaningful ‘why’). Often that's 3 levels. Sometimes 7."},
            {"question": "What if multiple events caused it?", "answer": "Use the branched variation. Real incidents usually have multiple parent causes at each level — pretending it's linear hides this."},
        ],
        "meta_title": "Root-Cause Analysis Via Sharpened Five Whys",
        "meta_description": "Modern Five Whys: evidence required at every level, branching for multiple causes, explicit root + fix + what fix doesn't address.",
    },
    {
        "slug": "data-quality-audit-prompt",
        "title": "Data Quality Audit From Schema and Samples",
        "tldr": "Audits a dataset for quality issues: missingness, duplicates, type drift, encoding errors, semantic drift, outliers. Returns a triage list with severity + recommended action per issue.",
        "category": "analysis",
        "tags": ["data-quality", "audit", "etl", "data-engineering"],
        "best_for_tags": ["data-engineering", "ml-prep", "warehouse-migration"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Pre-ML training data audit", "example": "Identify quality issues before training; avoids garbage-in-garbage-out."},
            {"scenario": "ETL output validation", "example": "Run on each daily output; catch drift before downstream consumers do."},
            {"scenario": "Vendor data ingestion", "example": "Quality check on partner-supplied dataset before integration."},
            {"scenario": "Warehouse migration QA", "example": "Compare expected vs actual after migration; flag anomalies."},
        ],
        "when_not_to_use": "Skip when the source already has a quality framework (Great Expectations, dbt tests). Use those tools instead — this is for ad-hoc audits or initial assessment.",
        "full_prompt": """You are a data quality auditor. Examine the schema + sample to identify quality issues.

INPUT
- Schema: {schema}
- Sample rows (first N rows or representative slice): {sample}
- Domain context: {domain_context}                     (what this data represents, business rules)
- Acceptance criteria: {acceptance_criteria}           (what ‘good enough’ looks like)

OUTPUT

## Inventory
- Total rows in sample: N
- Columns: list with type observed (which may differ from declared)

## Issues found
For each issue:
- Severity: blocker / major / minor / informational
- Column(s) affected
- Description: what's wrong, with example values from the sample
- Likely cause (best guess)
- Recommended action
- Verification: how to confirm the fix worked

Group by severity, blockers first.

### Categories to check
1. MISSINGNESS — nulls, empty strings, ‘N/A’, ‘null’ as strings, sentinel values (1900-01-01, 999)
2. DUPLICATES — exact dupes, fuzzy dupes (same entity, different formatting)
3. TYPE DRIFT — declared INT, observed strings? Mixed date formats?
4. ENCODING — UTF-8 issues, mojibake (Ã©, Ã±), HTML entities in plain-text fields
5. RANGE / DOMAIN — values outside expected (negative ages, future birthdates, currencies that don't match country)
6. CONSISTENCY — same entity represented multiple ways (USA / U.S.A. / United States)
7. SEMANTIC DRIFT — field meaning differs from name (column ‘email’ contains usernames)
8. OUTLIERS — extreme values that may be errors or genuine
9. RELATIONSHIP INTEGRITY — foreign keys pointing to non-existent rows, broken hierarchies
10. CONSTRAINTS — NOT NULL violated, uniqueness violated, business rule violated

## Caveats
- This is a SAMPLE audit. Issues you flag may be sample artifacts. Specify which findings need verification on the full dataset.
- Note any issue type you couldn't check (e.g., FK integrity without the parent table).

## Recommended next steps
3-5 specific actions to take, ordered by leverage:
1. Most impactful fix
2. Quick wins
3. Long-term schema/process changes if patterns suggest them

SCHEMA
{schema}

SAMPLE
{sample}

DOMAIN CONTEXT
{domain_context}

Now audit.""",
        "input_variables": [
            {"name": "schema", "type": "string", "description": "Column names + declared types", "required": True, "example": "id BIGINT, email VARCHAR(255), country VARCHAR(2), signed_up DATE, plan VARCHAR(20)"},
            {"name": "sample", "type": "string", "description": "Representative rows", "required": True, "example": "1,foo@bar.com,US,2024-01-15,Pro\\n2,'',U.S.A,15/03/2024,pro\\n3,bad@@@@,Mexico,2099-01-01,PRO"},
            {"name": "domain_context", "type": "string", "description": "What the data represents", "required": True, "example": "User signups for B2B SaaS, signed_up is when account created, country is ISO 3166-1 alpha-2."},
            {"name": "acceptance_criteria", "type": "string", "description": "Quality threshold", "required": False, "example": "<2% missing on critical fields (email, country, signed_up), all country codes valid ISO."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Inventory, issues grouped by severity, caveats, recommended next steps.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on cross-row consistency checks and semantic drift detection."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally misses subtle encoding issues — paste raw bytes if suspect."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; encoding analysis can be shallower."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Catches obvious issues; less reliable on semantic drift."},
        ],
        "variations": [
            {"label": "SQL output", "description": "Emit SQL queries to verify on full dataset.", "prompt_snippet": "Add: ‘for each Issue, emit the SQL query that would count occurrences on the full dataset (Postgres syntax).’"},
            {"label": "Great Expectations YAML", "description": "Emit as Great Expectations expectation suite.", "prompt_snippet": "Replace markdown output with: ‘output as Great Expectations expectation suite YAML — one expectation per issue.’"},
            {"label": "Compare against prior audit", "description": "Trend analysis.", "prompt_snippet": "Accept previous audit results; diff against current; flag new issues, fixed issues, regressed issues."},
        ],
        "failure_modes": [
            {"symptom": "All issues marked ‘major’.", "fix": "Add severity ladder anchors: ‘blocker = downstream consumers fail; major = wrong analysis; minor = cosmetic; informational = note only.’"},
            {"symptom": "Generic recommendations.", "fix": "Force: ‘each recommendation cites specific columns and proposed action; no general ‘improve data hygiene.’’"},
            {"symptom": "Misses encoding issues.", "fix": "Add explicit check: ‘look for mojibake patterns (Ã©, Ã±), HTML entities in plain-text columns, double-encoded UTF-8.’"},
            {"symptom": "Sample artifacts presented as confirmed issues.", "fix": "Add: ‘every issue has a Verification step that says how to confirm on full dataset.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["a-b-test-result-interpreter", "metric-anomaly-explainer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["data-quality", "etl"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How big a sample is enough?", "answer": "Depends on issue type. For schema-level issues, 100 rows is fine. For rare anomalies, you need stratified samples or full-dataset SQL. The prompt flags what needs verification beyond sample."},
            {"question": "Will it find ALL issues?", "answer": "No — model can miss subtle domain-specific issues (e.g., ‘users sometimes input phone numbers in the email field’). Use as a first pass; the recommended next steps should include domain-expert review."},
            {"question": "What about PII risk?", "answer": "Don't paste actual PII into a prompt. Use a representative synthetic sample or redacted version. The prompt analyzes structure; values matter for spot-checks but not exhaustive scans."},
        ],
        "meta_title": "Data Quality Audit From Schema and Samples",
        "meta_description": "Audit a dataset for missingness, duplicates, type drift, encoding errors, semantic drift, and outliers — with severity-ranked triage list.",
    },
    {
        "slug": "competitive-feature-matrix",
        "title": "Competitive Feature Matrix With Differentiation",
        "tldr": "Builds a feature matrix comparing your product to 3-5 competitors, then explicitly identifies what's TABLE STAKES, what's DIFFERENTIATED, and what's MISSING from your product — not just feature lists.",
        "category": "analysis",
        "tags": ["competitive-analysis", "feature-matrix", "differentiation", "product"],
        "best_for_tags": ["product-marketing", "sales-enablement", "strategy"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Pre-launch competitive positioning", "example": "Compare against 4 competitors; identify the differentiated feature to lead with."},
            {"scenario": "Sales enablement deck", "example": "Build competitive section with table-stakes / differentiated / gap call-outs."},
            {"scenario": "Roadmap prioritization", "example": "Identify gaps that are blocking deals — those go above competitive parity features."},
            {"scenario": "M&A target evaluation", "example": "Compare target's capabilities to portfolio."},
        ],
        "when_not_to_use": "Skip when you're the category creator (no real competitors yet) — use a JTBD analysis instead. Skip when competitors are too varied to compare on the same axes.",
        "full_prompt": """You are a product strategist building a competitive feature matrix.

INPUT
- Your product: {your_product}
- Competitors (3-5): {competitors}
- Categories of features to evaluate: {feature_categories}
- Target buyer / use case: {target}

OUTPUT

## Step 1: Feature axes
List 8-15 specific features (not categories) that map to buyer needs. Each is a granular capability you can answer yes/no/partial for each product.

## Step 2: The matrix
For each feature × product cell, mark:
- ✓ : Has it, robust implementation
- ⚠ : Has it, with limitations (specify in 1 line)
- ✗ : Does not have it
- ? : Unclear from public information

| Feature | Your Product | Competitor 1 | Competitor 2 | ... |

## Step 3: Categorization
Group features by competitive status:

### TABLE STAKES (everyone has, you must)
Features where everyone marks ✓. These don't differentiate but their absence is disqualifying.

### DIFFERENTIATED (you ✓, competitors ⚠ or ✗)
Features where you have an edge. For each: 1 sentence on the buyer benefit.

### GAPS (competitors ✓, you ⚠ or ✗)
Features where competitors lead. For each: severity (deal-breaker / nice-to-have / niche) + the typical buyer reaction.

### CONTESTED (mixed across all)
Features where the field is uneven and the buyer's choice depends on which they prioritize.

## Step 4: Strategic implications
3-5 implications for product strategy:
- Which gaps would close the most deals (prioritize by deal impact, not engineering ease)
- Which differentiations to lean into in marketing
- Which competitor moves to watch (if a competitor closes one of YOUR differentiations, what changes?)

CRITICAL RULES
- Specify SOURCES (or mark UNVERIFIED). Don't fabricate features from competitor pages you can't access.
- A feature is differentiated only if it's a meaningful difference for the BUYER. ‘We use Rust, they use Python’ is rarely differentiation.
- Be honest about gaps. Sales teams need real data, not the rosy version.

KNOWN INFORMATION
{your_product}

{competitors}

Begin.""",
        "input_variables": [
            {"name": "your_product", "type": "string", "description": "Your product capabilities (be specific)", "required": True, "example": "OSS AI Hub: directory of 1800+ OSS AI tools, includes glossary, cost calculator, academy, paid Pro tier."},
            {"name": "competitors", "type": "string", "description": "Competitor list with what each does", "required": True, "example": "1. Awesome lists on GitHub (free, no curation) 2. Hugging Face Hub (model-focused, no glossary) 3. Y Combinator's Startup library 4. Stack Overflow's Collectives"},
            {"name": "feature_categories", "type": "string", "description": "Categories to evaluate", "required": False, "example": "Curation quality, search, glossary, learning paths, cost tools, community features"},
            {"name": "target", "type": "string", "description": "Target buyer", "required": True, "example": "Engineering managers at small-to-mid-sized AI startups evaluating tools"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Feature axes, matrix table, 4 categorization sections (table stakes, differentiated, gaps, contested), strategic implications.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on honest gap identification; doesn't whitewash."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can hallucinate features on competitors without explicit source data."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid baseline; differentiations can be too generous to you."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Surface-level; needs detailed input on each competitor to avoid hallucination."},
        ],
        "variations": [
            {"label": "Two-product head-to-head", "description": "Deep dive on one rival.", "prompt_snippet": "Replace 3-5 competitors with: ‘one main competitor’. Add: ‘50% of analysis is the head-to-head; the matrix is fewer columns but more rows.’"},
            {"label": "Price-included matrix", "description": "Add cost dimensions.", "prompt_snippet": "Add Cost Dimensions section: pricing model, entry tier, enterprise tier, hidden costs (overage, support). Add ‘best value tier’ analysis per buyer segment."},
            {"label": "From buyer interviews", "description": "Use buyer-stated needs instead of feature lists.", "prompt_snippet": "Replace feature axes with: ‘JTBDs the buyer expressed in interviews; rate each product against each JTBD.’"},
        ],
        "failure_modes": [
            {"symptom": "Marks every competitor ✗ on your differentiations to make you look good.", "fix": "Re-pin: ‘differentiation requires evidence; mark ⚠ instead of ✗ when unsure.’"},
            {"symptom": "Gaps section is empty.", "fix": "Add: ‘every competitive product has gaps. If yours is short, you're either kidding yourself or undefined as a product. Identify at minimum 3 gaps.’"},
            {"symptom": "Features are technical (databases, languages).", "fix": "Re-pin: ‘features should map to buyer needs, not engineering choices. ‘Search by X’ is a feature; ‘uses Elasticsearch’ is not.’"},
            {"symptom": "Strategic implications are generic.", "fix": "Force: ‘each implication names a specific product or marketing action with a 90-day horizon.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["competitive-landscape-mapper", "vendor-comparison-builder", "strategic-tradeoff-analyzer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["competitive-analysis", "feature-matrix"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How accurate is competitor information?", "answer": "Only as accurate as your inputs. Provide specific source data — competitor pages, demos, conversations. Without that, the model fills gaps with plausible-but-wrong assumptions."},
            {"question": "Should the sales team see all of this?", "answer": "Yes — the gap section especially. Salespeople need to know real weaknesses to handle them; surprise gaps in calls are worse than known gaps."},
            {"question": "How often should I refresh?", "answer": "Quarterly minimum. Set up alerts on competitors' product pages so changes are visible; refresh the matrix when a competitor ships a major feature."},
        ],
        "meta_title": "Competitive Feature Matrix With Differentiation",
        "meta_description": "Build a feature matrix with explicit table-stakes / differentiated / gap classification — honest competitive analysis for product and sales.",
    },
    {
        "slug": "weekly-metrics-narrative",
        "title": "Weekly Metrics Narrative (Not a Dashboard)",
        "tldr": "Turns weekly metrics into a 200-word narrative: what moved, why (with hypotheses), what to watch next, what NOT to celebrate. Anti-dashboard format — designed to be read, not skimmed.",
        "category": "analysis",
        "tags": ["metrics", "weekly-update", "narrative", "data-storytelling"],
        "best_for_tags": ["startup-ops", "weekly-cadence", "founder-updates"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Founder's weekly metrics email", "example": "Convert dashboard screenshot + raw numbers into 200-word narrative for team or investors."},
            {"scenario": "Manager's team update", "example": "Engineering metrics → narrative the team will actually read."},
            {"scenario": "Customer success weekly", "example": "Health-score changes → story-driven update."},
            {"scenario": "Product weekly experiment recap", "example": "A/B test status + funnel metrics → narrative with hypotheses."},
        ],
        "when_not_to_use": "Skip for compliance/regulatory reports — they need structure. Skip when stakeholders explicitly want dashboards.",
        "full_prompt": """You are turning weekly metrics into a narrative. Not a dashboard, not bullets — a piece that gets read.

INPUT
- This week's metrics: {this_week_metrics}
- Last week's metrics for context: {last_week_metrics}
- Business goals this quarter: {goals}
- Audience: {audience}

OUTPUT — 200 ± 20 WORDS

## Structure
Paragraph 1 (~50 words): What MOVED this week. The 1-2 metric changes that matter most. Not all of them — the ones worth noting.

Paragraph 2 (~80 words): What likely DROVE the movement. Hypotheses, marked as hypotheses (‘probably because…’, ‘consistent with…’). Connect to actions taken (launches, campaigns, hires, outages).

Paragraph 3 (~40 words): What to WATCH next week. What signal would confirm or refute the hypothesis. Specific.

Paragraph 4 (~30 words): What NOT to celebrate (or what's troubling that nobody is talking about). The honest paragraph.

RULES
- One specific number per paragraph minimum.
- No bullet points. No ‘in conclusion.’
- No vanity metrics unless tied to a real business question.
- Hypotheses marked clearly so the reader doesn't mistake them for facts.
- The ‘don't celebrate’ paragraph is non-negotiable. There's always something.
- Tone: confident in the data, humble about causation.

BANNED PHRASES
- "Crushing it"
- "Continued growth"
- "Strong week"
- "All metrics are up"
- "More to come"

INPUT DATA

This week:
{this_week_metrics}

Last week (for context):
{last_week_metrics}

Quarterly goals:
{goals}

Now write the narrative.""",
        "input_variables": [
            {"name": "this_week_metrics", "type": "string", "description": "Key metrics for the week", "required": True, "example": "DAU 12.3k (+8% w/w), trial→paid 4.2% (-0.3pp), MRR $42k (+$1.8k), support tickets 87 (+15)"},
            {"name": "last_week_metrics", "type": "string", "description": "Previous week's numbers", "required": True, "example": "DAU 11.4k, trial→paid 4.5%, MRR $40.2k, support 76"},
            {"name": "goals", "type": "string", "description": "Quarterly goals", "required": True, "example": "MRR $60k by Q3 end, trial→paid >5%, support volume flat"},
            {"name": "audience", "type": "string", "description": "Who reads this", "required": True, "example": "Founder weekly to team of 12"},
        ],
        "expected_output": {
            "format": "text",
            "sample": "4-paragraph 200-word narrative covering moved/drove/watch/don't-celebrate.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on the ‘don't celebrate’ paragraph; doesn't sugarcoat."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes pads to 250+ words — re-pin word count."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Holds structure; ‘don't celebrate’ tends to be soft."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Defaults to bullet-heavy format; needs reminder."},
        ],
        "variations": [
            {"label": "Investor version", "description": "Slightly more polished tone.", "prompt_snippet": "Adjust audience handling: ‘for investors, lead with the moved/drove paragraphs in business-impact framing; keep the don't-celebrate paragraph but make it about risks rather than internal drama.’"},
            {"label": "With chart suggestion", "description": "Suggest one chart to attach.", "prompt_snippet": "Add: ‘end with a one-sentence note suggesting the one chart that would best support the narrative.’"},
            {"label": "Cumulative quarter view", "description": "Connect to quarterly progress.", "prompt_snippet": "Add: ‘paragraph 2 also notes how this week's movement affects quarterly goal trajectory.’"},
        ],
        "failure_modes": [
            {"symptom": "200 words turns into 400.", "fix": "Hard cap with explicit ‘200 ± 20 words; trim until you fit.’"},
            {"symptom": "‘Don't celebrate’ paragraph skipped or soft.", "fix": "Add: ‘this paragraph is mandatory; if you genuinely can't find anything, name the metric you DON'T have visibility into.’"},
            {"symptom": "Hypotheses presented as facts.", "fix": "Re-pin: ‘hypotheses explicitly marked (‘probably’, ‘consistent with’, ‘suggests’); reserve declarative phrasing for confirmed facts.’"},
            {"symptom": "Bullet points sneak in.", "fix": "Add: ‘no bullets; this is prose. If you reach for bullets, the prose has failed.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["investor-update-monthly", "newsletter-issue-from-week"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["narrative-metrics", "data-storytelling"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why narrative instead of dashboard?", "answer": "Dashboards get skimmed; narratives get read. The narrative forces the writer to pick what matters — which is itself useful for the writer."},
            {"question": "What if there's no ‘don't celebrate’?", "answer": "There is. Either a metric isn't moving as fast as needed, or there's a metric you're not watching that probably matters. The paragraph being uncomfortable is the point."},
            {"question": "Can I run this on a daily cadence?", "answer": "Skip daily — too much noise. Weekly is the sweet spot. Daily metrics belong on a dashboard; narrative-form output is for the cadence where you can detect actual signal."},
        ],
        "meta_title": "Weekly Metrics Narrative — Prompt",
        "meta_description": "Turn weekly metrics into a 200-word narrative: what moved, why, what to watch, what NOT to celebrate. Anti-dashboard, designed to be read.",
    },
]
