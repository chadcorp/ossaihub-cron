"""Business prompts — batch 3."""

RECORDS = [
    {
        "slug": "board-update-monthly",
        "title": "Monthly Board Update Draft",
        "tldr": "Drafts a structured monthly board update: TL;DR with the one number that matters, what changed, asks for the board, risks. ~600 words. Calibrated for startup boards, not corporate.",
        "category": "business",
        "tags": ["board-update", "investor-comms", "startup", "monthly"],
        "best_for_tags": ["founders", "ceos", "board-prep"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "First-time founder monthly cadence", "example": "Establish the rhythm; consistent format makes board members faster readers."},
            {"scenario": "Pre-board-meeting prep", "example": "Send the written update 48h before the meeting; meeting is for discussion, not status."},
            {"scenario": "Async-only board", "example": "When you don't have monthly meetings, the written update IS the board interaction."},
            {"scenario": "Board change", "example": "New board members coming in; consistent format helps them onboard."},
        ],
        "when_not_to_use": "Skip for boards expecting formal corporate format (heavy GAAP, audited financials). Skip for IPO-track companies — those need fully-templated formats per SEC.",
        "full_prompt": """You are drafting a monthly startup board update. ~600 words. Honest over polished.

INPUT
- Reporting month: {month}
- Headline metric (the ONE number that matters this month): {headline_metric}
- Changes from last month (raw notes): {changes_notes}
- Key wins (raw notes): {wins_notes}
- Key challenges / misses (raw notes): {misses_notes}
- Asks for the board (what you need): {board_asks}
- Risks (what could go wrong in next 60 days): {risks_notes}
- Runway / financial state: {financial_state}
- Hiring update: {hiring}

OUTPUT STRUCTURE

## 1. Subject line
`<Company> board update — <Month Year> — <one-phrase headline>`

Headline example: "first $1M ARR month, churn ticked up", "Q3 plan landing, two key hires made", "tough month, here's what we're doing".

## 2. TL;DR (4-5 bullets max)
- The ONE NUMBER that matters this month
- Up or down from last month
- One headline win
- One headline concern
- One thing you need the board to do

## 3. The numbers (5-8 metrics)
Each: name | this month | last month | trend | 1-line context.
Numbers I expect to see: ARR or MRR, growth rate, runway months, cash on hand, headcount, new logos, churn.

## 4. What's working
2-3 paragraphs. SPECIFIC wins with numbers/named customers. Avoid 'momentum' and 'traction' as standalone words.

## 5. What's not working
2-3 paragraphs. Honest about misses. State the missed target + reason + what you're doing.
HARD RULE: never spin a miss into a win.

## 6. The asks
Numbered list. Examples:
- "Intro to 3 CISOs at $100M+ companies — we're in evaluation with 2, would help with 3 more."
- "Approve hiring backfill for Head of Sales (departed last month) — proposed comp band attached."
- "Feedback on attached competitive positioning deck."
Each ask is specific + actionable + has a timeline.

## 7. Risks (60-day window)
3-5 specific risks + mitigation in 1 line each.
Bad: "Macro environment uncertainty"
Good: "Our top 3 customers all renewing in next 60 days; if any churn, ARR drops 14%. Mitigation: weekly check-ins with each, retention bonus for CS lead."

## 8. Hiring / team
Who joined, who left, what's open. Don't hide departures.

## 9. Financial state
Cash on hand, runway months, burn rate. If raising soon, note timing.

## 10. Closing (1-2 sentences)
Honest mood. "Solid month, on plan." "Tough month, see misses section, we have a plan." Don't fake.

RULES
- Numbers > adjectives. "23% MoM growth" not "strong growth".
- If a metric moved >20%, EXPLAIN it. Either it's a real change or a measurement change.
- Banned phrases: "crushing it", "lots of momentum", "exciting things on the horizon", "going forward".
- Board members read 5-10 of these a month. CONSISTENT FORMAT lets them skim.

INPUTS

Month: {month}
Headline: {headline_metric}
Wins: {wins_notes}
Misses: {misses_notes}
Asks: {board_asks}
Risks: {risks_notes}
Financial: {financial_state}
Hiring: {hiring}

Now draft.""",
        "input_variables": [
            {"name": "month", "type": "string", "description": "Reporting month", "required": True, "example": "April 2026"},
            {"name": "headline_metric", "type": "string", "description": "The ONE number", "required": True, "example": "ARR crossed $5M (+18% MoM)"},
            {"name": "changes_notes", "type": "string", "description": "Raw notes on changes", "required": False, "example": "Launched analytics dashboard. Lost a Fortune 500 deal at last second. Hired VP Product."},
            {"name": "wins_notes", "type": "string", "description": "Wins", "required": True, "example": "Closed 4 enterprise deals incl Acme ($240k). Reduced cloud cost 31%."},
            {"name": "misses_notes", "type": "string", "description": "Misses + reasons", "required": True, "example": "Missed lead gen goal (180 SQLs vs 250 target) due to mid-month content pause."},
            {"name": "board_asks", "type": "string", "description": "What you need", "required": True, "example": "Intro to enterprise CISOs. Sign-off on $500k marketing reallocation. Feedback on the attached pricing v3 deck."},
            {"name": "risks_notes", "type": "string", "description": "Risks 60d", "required": True, "example": "Three top-10 accounts renew in May. Engineering bottleneck on new feature."},
            {"name": "financial_state", "type": "string", "description": "Cash + runway", "required": True, "example": "Cash: $14.2M. Runway: 19 months. Burn: $740k/mo."},
            {"name": "hiring", "type": "string", "description": "Hiring news", "required": True, "example": "Added VP Product (Jane Doe, ex-Stripe). Two engineering roles open."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Subject + TL;DR + 5-8 metrics + working + not-working + asks + risks + hiring + financial + close. ~600 words.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Resists spin; consistent structure."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes adds ‘momentum’/'traction' — call out banned words."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; risks section can be generic — re-pin specificity."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for short routine updates; thin nuance."},
        ],
        "variations": [
            {"label": "Crisis variant", "description": "Hard month / hard news.", "prompt_snippet": "Add: ‘this is a tough month — lead with the harm + plan; don't sugar-coat. Asks should focus on near-term survival actions.’"},
            {"label": "Fundraise-pending", "description": "When raising in next 60-90d.", "prompt_snippet": "Add Section after Financial: ‘Fundraise status — target raise, lead progress, timeline, what board members can help with.’"},
            {"label": "Multi-year context", "description": "Add YoY comparison.", "prompt_snippet": "In ‘The numbers’ table, add YoY column (same month last year) alongside MoM."},
        ],
        "failure_modes": [
            {"symptom": "Misses spun as wins.", "fix": "Re-pin: ‘never spin. Acknowledge misses directly; the ‘what we're doing’ is the redemption, not framing.’"},
            {"symptom": "Vague asks (‘any introductions appreciated’).", "fix": "Force specificity: ‘ask names role + segment + reason + timing. Vague asks get ignored.’"},
            {"symptom": "Risks are clichés (‘market uncertainty’).", "fix": "Force: ‘every risk names a specific event + likelihood + impact + mitigation. No macro hand-waving.’"},
            {"symptom": "Format drifts month-to-month.", "fix": "Use this prompt EVERY month with same sections. Consistency lets board skim.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["investor-update-monthly", "executive-summary-1-page", "fundraise-pitch-deck-outline"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["board-update", "startup-comms"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How is this different from an investor update?", "answer": "Board update is for ACTIVE board members (more strategic asks, more honesty about misses). Investor update is for SHAREHOLDERS broadly (more polished, less in the weeds)."},
            {"question": "Length?", "answer": "600 words is the sweet spot. Under 400, you're hiding things. Over 1,000, board members skim and miss the point."},
            {"question": "When to send?", "answer": "Same day each month (e.g., 5th of next month). Predictability matters."},
        ],
        "meta_title": "Monthly Board Update Draft — Prompt",
        "meta_description": "Draft a startup monthly board update: TL;DR, numbers, what's working, what's not, specific asks, real risks, hiring, financial. ~600 words.",
    },
    {
        "slug": "sales-objection-handling-playbook",
        "title": "Sales Objection Handling Playbook",
        "tldr": "Generates a playbook for a specific sales objection: the underlying concern, three response angles (acknowledge / reframe / proof), proof points to gather, and when to walk away.",
        "category": "business",
        "tags": ["sales", "objection-handling", "enablement", "playbook"],
        "best_for_tags": ["sales-teams", "enablement", "founder-led-sales"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "New rep onboarding", "example": "Top 10 objections each get a playbook; rep practices before going live."},
            {"scenario": "Objection pattern emerging", "example": "‘Build vs buy’ pushback rising; build the playbook before it kills the quarter."},
            {"scenario": "Competitive deal-loss review", "example": "Lost to competitor on [reason]; build the response for next time."},
            {"scenario": "Founder-led sales discipline", "example": "Founder is winging it; this prompt forces them to structure their best responses."},
        ],
        "when_not_to_use": "Skip for objections that mask a real product gap (build the product first). Skip when the objection is genuinely ‘we don't need this’ — qualifying out is correct.",
        "full_prompt": """You are building a sales objection handling playbook. The goal: rep can respond confidently, not script-recite.

INPUT
- The specific objection: {objection}
- Customer segment: {segment}
- What we sell: {product_summary}
- Top 2 competitors: {competitors}
- Existing proof points / customers: {proof_assets}

OUTPUT

## 1. The actual concern behind the objection
What's the customer REALLY worried about? Objections are often coded.
- "It's too expensive" might mean: ROI unclear / budget cycle / competitor cheaper / authority not committed.
- "We're not ready" might mean: not their priority / fear of switching cost / no internal champion yet.

State 2-3 plausible underlying concerns. Indicate which is most common in {segment}.

## 2. Three response angles (NOT scripts)
For each angle, give the rep:
- What to do (action, not words)
- Sample phrasing (1-2 sentences they can adapt)
- When to use this angle (signals to listen for)

### Angle A: ACKNOWLEDGE
The honest yes. Where the objection IS valid. Don't deflect.

### Angle B: REFRAME
Where the customer is comparing to the wrong baseline. Shift the frame.

### Angle C: PROOF
Where data settles it. Specific customer, specific result, specific situation matching theirs.

## 3. Proof points to ALWAYS have ready for this objection
- 1-2 customer stories with specifics (name with permission, role, outcome with number)
- 1 ROI calculation (anchor for "expensive" objections)
- 1 implementation timeline (for "we're not ready" objections)

If proof_assets is thin, NOTE the gap explicitly.

## 4. When to walk away
A list of disqualifying signals. If you see these, this is not the right deal:
- E.g., "Budget cycle is 9+ months away with no flex"
- E.g., "No identified user pain — being shopped for vague modernization"
- E.g., "Competitor already chosen, just doing diligence"

3-5 signals. Specific.

## 5. Trap responses to AVOID
What new reps reach for that BACKFIRES:
- "Let me put together a custom proposal" (extends sales cycle, sounds desperate)
- "We can give you a discount" (signals price was the only lever, weakens future negotiations)
- "Let me check with my manager" (when not necessary — burns authority)

3-5 traps with WHY they backfire.

## 6. After the call: follow-up template
The brief follow-up that should go out within 2h. Specific to this objection. Includes:
- Quote of the objection back to them (acknowledges you heard)
- The single best proof point
- A specific next step

CRITICAL RULES
- Sample phrasings are conversational, not corporate.
- Proof points must be SPECIFIC (named, numbered) or marked as gap.
- Walking away IS a successful outcome on bad-fit deals.
- Don't manufacture confidence — if the objection is valid, name what would change it.

OBJECTION: {objection}

PRODUCT: {product_summary}

Now build the playbook.""",
        "input_variables": [
            {"name": "objection", "type": "string", "description": "Specific objection", "required": True, "example": "Your pricing is 2x what [Competitor X] charges"},
            {"name": "segment", "type": "string", "description": "Customer segment", "required": True, "example": "Mid-market B2B SaaS (200-2000 employees)"},
            {"name": "product_summary", "type": "string", "description": "What you sell", "required": True, "example": "Customer data platform — unifies marketing/sales/product event streams"},
            {"name": "competitors", "type": "string", "description": "Top competitors", "required": True, "example": "Segment, Rudderstack"},
            {"name": "proof_assets", "type": "string", "description": "Existing proof", "required": True, "example": "Acme Inc case study (43% data quality lift). 3 named customers willing to take ref calls. ROI calculator with industry benchmarks."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: actual concern, 3 angles (acknowledge/reframe/proof), proof points, walk-away signals, traps to avoid, follow-up template.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on the ‘actual concern’ layer; honest about disqualifying signals."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can produce corporate-speak phrasings — call out conversational tone."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; ‘trap responses’ section sometimes generic."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for routine objections; thin on nuance."},
        ],
        "variations": [
            {"label": "Multi-objection bundle", "description": "Build playbooks for top 10 objections at once.", "prompt_snippet": "Accept a list of objections; produce one playbook each. Then meta-analyze: which objections cluster around the same underlying concern?"},
            {"label": "Role-play training script", "description": "Convert to practice script.", "prompt_snippet": "Add: ‘also produce a role-play script where the trainer asks the objection in 3 different ways (mild, firm, hostile) and the rep practices each response angle.’"},
            {"label": "Competitive-specific", "description": "Tied to a specific competitor.", "prompt_snippet": "Add: ‘competitor-specific section — what tradeoffs THEY make that we don't; how to surface those without disparaging.’"},
        ],
        "failure_modes": [
            {"symptom": "Sample phrasings sound corporate.", "fix": "Re-pin: ‘conversational. ‘What I'm hearing is...’ not ‘I understand your concern about pricing.’’"},
            {"symptom": "Proof points are unsourced/vague.", "fix": "Add: ‘proof must be specific (named customer + specific outcome). If you don't have it, label as gap; don't invent.’"},
            {"symptom": "Walk-away section empty.", "fix": "Force: ‘good salespeople walk away from bad-fit deals; list 3-5 disqualifying signals.’"},
            {"symptom": "Traps are generic (‘don't be pushy’).", "fix": "Add: ‘traps must reference SPECIFIC moves new reps make + the second-order cost.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["competitive-feature-matrix", "customer-segmentation-from-data"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["objection-handling", "sales-enablement"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should I script the responses?", "answer": "No — sample phrasings, not scripts. Reps who recite scripts sound robotic. The playbook gives them confident handles; the words emerge in conversation."},
            {"question": "How often update?", "answer": "When the underlying-concern landscape shifts (new competitor, new product launch, new buyer persona). Otherwise once a year as a refresh."},
            {"question": "What if every deal hits the same objection?", "answer": "Then the objection points at a product/positioning gap. Build the playbook AND raise the strategic issue with product."},
        ],
        "meta_title": "Sales Objection Handling Playbook — Prompt",
        "meta_description": "Build a structured objection-handling playbook: underlying concern, 3 response angles, proof points, walk-away signals, traps to avoid.",
    },
    {
        "slug": "okr-quality-audit",
        "title": "OKR Quality Audit",
        "tldr": "Reviews a set of OKRs and flags vague objectives, sandbagged key results, activity-disguised-as-outcome, missing leading indicators. Returns specific rewrite suggestions per OKR.",
        "category": "business",
        "tags": ["okrs", "goal-setting", "review", "leadership"],
        "best_for_tags": ["okr-leads", "managers", "exec-staff"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Quarterly OKR review before announcement", "example": "Draft OKRs from each team → audit before locking → fix vague ones."},
            {"scenario": "Onboarding manager to OKR culture", "example": "New manager submits first OKRs; audit teaches OKR discipline."},
            {"scenario": "Mid-quarter check-in", "example": "OKRs that looked solid now look fake — audit identifies which got sandbagged."},
            {"scenario": "OKR retrospective", "example": "At quarter end, audit reveals which OKRs were poorly written vs which were genuinely missed."},
        ],
        "when_not_to_use": "Skip when the team isn't using OKRs (don't impose). Skip for OKRs already approved and in-flight — audit then is too late.",
        "full_prompt": """You are auditing a set of OKRs. Apply the OKR discipline: outcomes over activities, specific over vague, falsifiable over fuzzy.

INPUT
- The OKRs (objective + 3-5 key results each): {okrs}
- Team / function context: {team_context}
- Quarter / time horizon: {time_horizon}

OUTPUT

For each OKR, output:

## OKR <number>: <objective>

### Objective audit
- VAGUE / SPECIFIC: rate 1-5
- ASPIRATIONAL or DELIVERABLE: which is intended?
- One-line critique
- Suggested rewrite (if needed)

### Key Results audit
For each KR:
- KR text
- Type: OUTCOME / OUTPUT / ACTIVITY (with definition: outcome=result for customers/business; output=thing we ship; activity=thing we do)
- MEASURABLE? Yes / No / Soft (subjective)
- AMBITION: sandbag / appropriate / moonshot — based on what's known about base rate
- LEADING INDICATOR: present or missing? (Without one, you can't course-correct mid-quarter)
- Suggested rewrite

### Overall OKR grade
- A: outcome-focused, measurable, ambitious-but-achievable, leading indicators included
- B: minor issues
- C: vague or activity-disguised
- F: fundamentally broken (not actually an OKR)

### Top recommendation for this OKR
One sentence the team should act on.

## Cross-OKR observations
After all individual audits:
- Patterns across OKRs (e.g., everything is output, no real outcomes)
- Conflicting / overlapping OKRs across teams (if visible)
- Missing OKRs — important things this team is doing that aren't reflected
- Capacity check: how realistic is this load given team size?

PRINCIPLES TO APPLY
- OUTCOMES > OUTPUTS > ACTIVITIES. Most failing OKRs hide activities as KRs.
- AMBITION: a sandbagged OKR demoralizes; a moonshot OKR teaches nothing if missed. Sweet spot is ~70% confidence.
- LEADING INDICATORS: every KR needs at least one observable signal you'll see BEFORE the deadline that tells you it's on track.
- FALSIFIABILITY: if you can't tell at end-of-quarter whether the KR was hit, it's not a KR.

BANNED PHRASES IN KRs (auto-mark as ACTIVITY):
- "Launch X" (when launching IS the outcome, no further measure)
- "Improve X" (no number — vague)
- "Drive growth" / "Drive engagement" (verbs without nouns)
- "Achieve N customer satisfaction" (without defining how measured)

OKRs TO AUDIT
{okrs}

CONTEXT
{team_context}

Begin.""",
        "input_variables": [
            {"name": "okrs", "type": "string", "description": "OKRs in any format", "required": True, "example": "Objective: Become category leader in mid-market data privacy. KR1: Sign 12 new mid-market customers. KR2: Launch SOC2 Type II. KR3: Hit $3M new ARR. KR4: Maintain NPS > 50."},
            {"name": "team_context", "type": "string", "description": "Team info", "required": True, "example": "Sales + marketing team, 8 people, $2M ARR last quarter, mid-market segment ($50k-$250k deals)"},
            {"name": "time_horizon", "type": "string", "description": "Quarter", "required": True, "example": "Q3 2026 (Jul-Sep)"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Per-OKR audit with objective/KR grades + rewrites; cross-OKR observations + patterns + recommendations.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Honest about sandbagged ambition + activity-disguised-as-outcome."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can rubber-stamp objectives — re-pin specific critique requirement."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; cross-OKR observations sometimes shallow."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for routine reviews."},
        ],
        "variations": [
            {"label": "Cross-team coordination check", "description": "Audit OKRs from multiple teams for alignment.", "prompt_snippet": "Add: ‘accept OKRs from 2+ teams; check for explicit alignment (team A's KR depends on team B's KR? Is that named?) and conflicting goals (A wants growth, B wants quality cap — surface tension).’"},
            {"label": "OKR coach mode", "description": "Output as Socratic questions, not directives.", "prompt_snippet": "Instead of rewrites, output the THREE QUESTIONS the OKR owner should answer about each KR before locking it. Forces self-discovery."},
            {"label": "Mid-quarter re-grade", "description": "Audit OKRs at mid-quarter with actuals.", "prompt_snippet": "Accept actuals at mid-quarter; per-KR mark: on-track / off-track / dead. Critique the original OKR quality with hindsight."},
        ],
        "failure_modes": [
            {"symptom": "Lets ‘launch X’ pass as a KR.", "fix": "Re-pin: ‘launching is an output. Outcome KR specifies what happens AFTER launch (adoption, revenue, retention).’"},
            {"symptom": "Doesn't flag missing leading indicators.", "fix": "Force: ‘every KR section MUST address leading indicator presence/absence.’"},
            {"symptom": "Vague ‘B’ grade without specific critique.", "fix": "Add: ‘every grade below A has a specific critique that the owner can act on.’"},
            {"symptom": "Patterns section empty.", "fix": "Force: ‘even when individual OKRs are solid, cross-OKR patterns (all-outcomes, all-activities, conflicting) deserve commentary.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["okr-quarterly-drafter", "decomposition-into-subgoals"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["okr", "leading-indicator"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Will the team accept the feedback?", "answer": "Depends on framing. Audit results presented as ‘here's how to make these stronger’ go better than ‘these are bad.’ The prompt focuses on specific rewrites, which makes feedback actionable not personal."},
            {"question": "What's the right number of OKRs?", "answer": "3-5 per team, 3-5 KRs per objective. Below that, you're losing scope. Above that, focus disappears."},
            {"question": "Should OKRs cascade?", "answer": "Loosely. Team OKRs should support company OKRs, but verbatim cascading produces fake-aligned theater. Pattern: company OKRs set direction; team OKRs commit to deliverables."},
        ],
        "meta_title": "OKR Quality Audit — Prompt",
        "meta_description": "Audit OKRs for vagueness, sandbagged ambition, activity-disguised-as-outcome, missing leading indicators. Per-OKR rewrites + cross-team patterns.",
    },
    {
        "slug": "go-no-go-decision-meeting-prep",
        "title": "Go/No-Go Decision Meeting Prep",
        "tldr": "Prepares a 1-page brief for a go/no-go meeting: the decision, the criteria, the data, the recommendation, the asks. Forces the team to commit to criteria BEFORE seeing the data.",
        "category": "business",
        "tags": ["decision-making", "meeting-prep", "go-no-go", "leadership"],
        "best_for_tags": ["product-launches", "investment-decisions", "ship-decisions"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Pre-launch readiness review", "example": "Should we launch Friday? Criteria + data + recommendation in one page."},
            {"scenario": "Major investment", "example": "Should we hire 5 sales reps next quarter? Same structure."},
            {"scenario": "Project kill decision", "example": "Project X has been struggling. Should we kill it? Structured analysis avoids sunk-cost reasoning."},
            {"scenario": "Vendor selection", "example": "After RFP and evals, the go/no-go on chosen vendor."},
        ],
        "when_not_to_use": "Skip for trivial decisions. Skip when criteria genuinely can't be defined upfront (then it's an exploratory meeting, not a go/no-go).",
        "full_prompt": """You are preparing a 1-page brief for a go/no-go decision meeting.

INPUT
- The decision: {decision}
- Criteria the team COMMITTED to upfront (before seeing data): {criteria}
- Data / status against each criterion: {data}
- Decision-maker(s): {decision_makers}
- Meeting time: {meeting_time}

OUTPUT (1 page, ~500 words)

## DECISION: <one sentence>

## TL;DR
- Recommendation (go / no-go / conditional-go / delay)
- Confidence (high / medium / low)
- Single strongest reason

## Criteria scorecard
| Criterion | Threshold | Actual | Status |
|---|---|---|---|

Each criterion gets ✓ (met) / ⚠ (partial) / ✗ (missed). Status reasoning in 1 line per row.

## What's going right
2-3 specific things. With numbers.

## What's not going right
2-3 specific things. With numbers. HARD RULE: don't downplay.

## What we don't know
2-4 specific things the data doesn't tell us. Important for honest decisions.

## Recommendation
One paragraph. The path forward, with confidence + reasoning.

If GO: what changes? Who owns the next 7 days?
If NO-GO: what triggers a re-evaluation? When?
If CONDITIONAL-GO: what conditions, by when, owned by whom?
If DELAY: what would change to enable a go? Expected timing of re-decision?

## Asks for the decision-maker
3 specific asks:
- A decision (go/no-go) by <when>
- Approval of contingency plan (if go)
- Sign-off on what happens to people/budget if no-go

## What this brief is NOT
- Not a sales pitch
- Not the place for the FULL data dump (link to appendix)
- Not where you discover criteria mid-stream (those were locked upfront)

CRITICAL RULES
- The criteria in section 2 must match the criteria in section 1 input — no shifting goalposts.
- If actual data missed a threshold, mark ✗ honestly. Don't fudge.
- The recommendation should NOT be ‘defer to discussion.’ Have a point of view.
- One page total. Discipline.

INPUTS

DECISION: {decision}
CRITERIA: {criteria}
DATA: {data}

Now draft.""",
        "input_variables": [
            {"name": "decision", "type": "string", "description": "The decision", "required": True, "example": "Launch new pricing tier on May 21"},
            {"name": "criteria", "type": "string", "description": "Pre-committed criteria", "required": True, "example": "1. Customer comms approved by legal. 2. Pricing page deployed and tested. 3. Sales team trained (>80% pass quiz). 4. No critical bugs unresolved (<3). 5. CFO sign-off on revenue forecast impact."},
            {"name": "data", "type": "string", "description": "Status per criterion", "required": True, "example": "1. Legal approved 5/14. 2. Page deployed staging, prod awaiting final review. 3. 6 of 8 reps passed (75%). 4. 2 critical bugs in queue; ETA fix 5/19. 5. CFO sign-off pending revised forecast."},
            {"name": "decision_makers", "type": "string", "description": "Who decides", "required": True, "example": "CEO + CFO + VP Product"},
            {"name": "meeting_time", "type": "string", "description": "Meeting datetime", "required": True, "example": "May 20, 9am PT (30 min)"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "1-page brief: decision, TL;DR with recommendation, criteria scorecard table, what's right, what's not, what we don't know, recommendation, 3 asks.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Refuses to shift goalposts; honest about missed thresholds."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes hedges recommendation — re-pin ‘have a point of view.’"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; ‘what we don't know’ section often soft."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for routine decisions."},
        ],
        "variations": [
            {"label": "Pre-mortem appended", "description": "Add 100-word pre-mortem.", "prompt_snippet": "Add: ‘after recommendation, write a 100-word pre-mortem: assume the go-decision led to failure 90 days from now. What broke?’"},
            {"label": "Reversibility analysis", "description": "How reversible is this decision?", "prompt_snippet": "Add Section: ‘REVERSIBILITY — one-way door / two-way door. If one-way, are we sure? If two-way, what's our pre-committed reversal trigger?’"},
            {"label": "Stakeholder veto check", "description": "Surface dissent before the meeting.", "prompt_snippet": "Add: ‘list which stakeholders have expressed concerns + what those concerns are. Don't surprise them in the meeting.’"},
        ],
        "failure_modes": [
            {"symptom": "Goalposts shift between criteria and scorecard.", "fix": "Re-pin: ‘scorecard criteria are VERBATIM from the input criteria. Don't add, don't reword.’"},
            {"symptom": "Recommendation is ‘defer to discussion.’", "fix": "Add: ‘the brief MUST have a point of view. Discussion happens, but you state the recommendation.’"},
            {"symptom": "‘What we don't know’ skipped.", "fix": "Force: ‘every decision has unknowns. List 2-4 specifically. ‘We know everything’ is rarely true.’"},
            {"symptom": "Brief is 3 pages.", "fix": "Hard cap: ‘1 page or it's not a go/no-go brief. Link to appendix for detail.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["strategic-tradeoff-analyzer", "executive-summary-1-page", "devils-advocate-pre-mortem"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["decision-meeting", "reversibility"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why commit to criteria upfront?", "answer": "Post-hoc criteria become justifications. Upfront criteria force honest evaluation. The discipline is harder than it looks; most teams need a few iterations."},
            {"question": "What if criteria themselves were wrong?", "answer": "Flag it. ‘Criterion 3 turned out not to measure what we thought; recommend deferring the decision while we figure out the right criterion.’ That's better than fake passing."},
            {"question": "How long do these meetings take?", "answer": "20-30 min if the brief is good. The brief did the work. Meeting is for the decision + immediate next steps."},
        ],
        "meta_title": "Go/No-Go Decision Meeting Prep — Prompt",
        "meta_description": "1-page brief for go/no-go meetings: decision, pre-committed criteria scorecard, what's right/wrong, recommendation with confidence. No goalpost shifting.",
    },
]
