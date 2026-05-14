"""Business prompt library — v2 authored (2026-05-14)."""

RECORDS = [
    {
        "slug": "strategic-tradeoff-analyzer",
        "title": "Strategic Tradeoff Analyzer (multi-option matrix)",
        "category": "business",
        "tldr": "Given 2-4 strategic options, build an explicit tradeoff matrix across cost, time, risk, optionality, opportunity cost. Returns a ranked recommendation with reasoning per axis.",
        "tags": ["strategy", "tradeoffs", "decision-making"],
        "best_for_tags": ["strategy", "decision-support", "executive"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "full_prompt": (
            "You are a senior strategy consultant building a decision memo. The user has 2-4 strategic options and needs an honest tradeoff analysis before committing.\n\n"
            "INPUTS:\n"
            "- options: list of {label, description, est_cost_usd (optional), est_time_weeks (optional)}\n"
            "- context: business situation (stage, revenue, team size, constraints)\n"
            "- decision_criteria (optional): user's stated priorities (e.g., 'speed over cost')\n\n"
            "PROCEDURE:\n"
            "1. For each option, score 1-5 (with 1-sentence justification) on:\n"
            "   - Cost (capital + opex; lower = better)\n"
            "   - Time-to-value (faster = better)\n"
            "   - Execution risk (lower = better)\n"
            "   - Optionality preserved (more = better)\n"
            "   - Strategic fit (higher = better)\n"
            "2. Compute weighted score using decision_criteria; if none provided, weight equally.\n"
            "3. Rank options. If top 2 are within 0.3 points, declare 'too close to call' and surface what would tip the balance.\n"
            "4. For the recommended option, write 3-5 sentences of 'why this'. For the runner-up, write 1-2 sentences of 'when this would have won'.\n\n"
            "OUTPUT FORMAT: markdown with:\n"
            "- Matrix table (options × axes, each cell '<score>: <reason>')\n"
            "- Weighted total row\n"
            "- 'Recommendation' section\n"
            "- 'What would change my mind' section (2-3 trigger events)\n"
            "- 'Open questions' section if information is missing\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "options", "type": "list[Option]", "description": "2-4 strategic options with labels + descriptions", "required": True, "example": "[{label: 'Build', description: 'In-house team builds it in 6 months', est_cost_usd: 800000}, {label: 'Buy', description: 'Acquire CompetitorCo for $4M', est_cost_usd: 4000000}, ...]"},
            {"name": "context", "type": "string", "description": "Business situation context", "required": True, "example": "Series B SaaS, 40 engineers, $10M ARR, 18 months runway, need to win the enterprise segment."},
            {"name": "decision_criteria", "type": "string", "description": "User's stated priorities", "required": False, "example": "Speed over cost — must ship by Q3 board meeting."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "| Option | Cost | Time | Risk | Optionality | Fit | **Weighted** |\n|---|---|---|---|---|---|---|\n| Build | 3: $800k in-house | 2: 6mo | 3: known team | 5: own the IP | 5: core to thesis | **3.6** |\n| Buy | 1: $4M | 5: instant | 2: integration risk | 2: locked in | 4: adjacent | **2.8** |\n\n## Recommendation: Build\nDespite the longer timeline, building preserves optionality and aligns with the core thesis...\n\n## What would change my mind\n- If Q3 board deadline becomes a hard gate → Buy wins.\n- If acquihire pool dries up in 6mo → Buy gets harder later.\n\n## Open questions\n- What's the actual integration cost for Buy? Estimate excluded.",
        },
        "use_cases": [
            {"scenario": "Build-vs-buy decisions", "example": "VP Eng deciding whether to build internal observability or buy Datadog. Feed both as options."},
            {"scenario": "Market-entry sequencing", "example": "Three geographic markets, two product lines, time to pick one to lead with."},
            {"scenario": "Pricing model shift", "example": "Move from seat-based to usage-based or stay? Both come with risk profiles to surface."},
            {"scenario": "Hire-vs-contract", "example": "Senior engineer FT vs contractor for 6 months vs hire abroad — three options with different risk surfaces."},
        ],
        "when_not_to_use": "Don't use for binary 'yes/no' decisions — the matrix overhead is wasted. Also skip for purely creative/aesthetic decisions where the axes don't apply.",
        "few_shot_examples": [
            {
                "input": "options: [{label:'Hire senior eng (FT)', desc:'New full-time hire, $200k all-in, ramp 3 months', cost:200000}, {label:'Senior contractor (6mo)', desc:'$240k contract, ramp 2 weeks', cost:240000}]. context: 'Series A startup, 5 eng team, need to ship platform v2 by Q2 board meeting (5 months out)'",
                "output": "| Option | Cost | Time | Risk | Optionality | Fit | **Weighted** |\n|---|---|---|---|---|---|---|\n| Hire FT | 4: $200k+ramp | 2: 3mo ramp | 3: hire risk | 4: long-term value | 4: core team | **3.4** |\n| Contractor | 2: $240k | 5: 2wk ramp | 3: contractor leverage limited | 2: leaves in 6mo | 3: external | **3.0** |\n\n## Recommendation: Hire FT\nThe 5-month Q2 deadline makes time look like the deciding factor, but the contractor's 2-week ramp only buys you ~2.5 months of incremental velocity vs FT (3mo ramp). Meanwhile, you get a permanent multiplier on team capacity past the Q2 milestone.\n\n## What would change my mind\n- If Q2 is a hard contractual gate (not just a board check-in), the time delta matters more.\n- If hiring market is broken in your geo (e.g., zero candidates in 30 days), contractor as bridge while you keep recruiting.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Balances rigor with brevity. Won't pad cells with fluff."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Preferred for high-stakes (M&A, geographic expansion) where nuance matters."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong on the matrix structure; sometimes vague on 'what would change my mind'."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable for self-hosted; expect to manually sharpen 1-2 cells."},
        ],
        "variations": [
            {"label": "Weighted custom-axes", "description": "Override the 5 default axes for domain-specific ones (e.g., for M&A: cultural fit, regulatory, talent retention).", "prompt_snippet": "INPUTS addition: `axes` = list of {name, weight, direction (higher_better|lower_better)}. Override default 5-axis set."},
            {"label": "Sensitivity analysis", "description": "Show how the ranking flips under different criteria weights.", "prompt_snippet": "Add OUTPUT section 'Sensitivity': for each weight combination in {speed-heavy, cost-heavy, risk-averse}, which option wins."},
            {"label": "Brutal-honest mode", "description": "Strip diplomatic hedging.", "prompt_snippet": "TONE override: 'Be direct. Don't say \"both have merits\" when the matrix clearly favors one.'"},
        ],
        "failure_modes": [
            {"symptom": "Averages cells into mush (every option scores 3-3.5)", "fix": "Force scores to span 1-5 — instruct 'use the full range; if everything is a 3, you're not differentiating'"},
            {"symptom": "Hedges the recommendation ('either could work')", "fix": "Mandate a recommendation; only allow 'too close to call' when scores are within 0.3 points"},
            {"symptom": "Ignores stated decision_criteria when weighting", "fix": "Echo the criteria explicitly at the top of the output and reference them in the weighted score calc"},
            {"symptom": "Invents costs/timelines not in inputs", "fix": "Rule: 'If a field is missing, list it under Open Questions rather than estimating'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["vendor-comparison-builder", "investor-update-monthly", "meeting-decision-recorder"],
        "related_tool_slugs": ["notion", "linear"],
        "related_glossary_slugs": ["decision-matrix", "opportunity-cost", "strategic-planning"],
        "faq": [
            {"question": "How is this different from a SWOT?", "answer": "SWOT is per-option introspection; this matrix is cross-option comparison. Use SWOT to think about ONE option deeply, this prompt to choose AMONG options."},
            {"question": "Can it handle >4 options?", "answer": "Technically yes, but humans can't keep >4 options in working memory. Pre-cull to 3-4 before running."},
            {"question": "What if I don't trust the AI's risk scoring?", "answer": "Override — pass `axes` with your own weights and instruct 'score per criterion only, no recommendation'. Make the call yourself."},
        ],
        "license": "CC-BY-4.0",
        "attribution": "OSS AI Hub Prompt Library",
        "status": "approved",
        "submitter_email": "hub@ossaihub.com",
        "submitter_name": "OSS AI Hub",
        "meta_title": "Strategic Tradeoff Analyzer — Multi-Option Decision Matrix",
        "meta_description": "Compare 2-4 strategic options across cost / time / risk / optionality / fit. Weighted scores + recommendation + 'what would change my mind'.",
    },

    {
        "slug": "vendor-comparison-builder",
        "title": "Vendor Comparison Builder (procurement-grade)",
        "category": "business",
        "tldr": "Compare N vendors across price, features, security, integration, support, lock-in. Outputs procurement-grade matrix with recommendation + red flags.",
        "tags": ["vendor", "procurement", "rfp"],
        "best_for_tags": ["procurement", "vendor-selection", "rfp"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You are a procurement analyst building a vendor comparison for a buying decision. Be skeptical — vendors over-promise. Compare on what actually matters operationally.\n\n"
            "INPUTS:\n"
            "- vendors: list of {name, pricing_summary, feature_list, security_compliance, integration_options, support_sla, contract_terms, sample_customer_logos}\n"
            "- requirements: list of must-haves and nice-to-haves with priority\n"
            "- buyer_context: {company_size, regulated_industry (bool), budget_usd_annual, decision_timeline_weeks}\n\n"
            "PROCEDURE:\n"
            "1. Score each vendor 1-5 (with evidence) on: Pricing fit, Feature coverage (vs requirements), Security posture, Integration ease, Support quality, Contract flexibility (vs lock-in).\n"
            "2. Flag RED FLAGS: missing compliance docs, opaque pricing, single point of failure (one CEO/no team), no public customer logos, mid-year price hike clauses, sub-3-month notice for cancellation.\n"
            "3. Flag GREEN FLAGS: public security audits, transparent pricing page, customer logos in your size range, named support engineer, month-to-month option, data export guarantee.\n"
            "4. Rank vendors. Annotate top 3 with 'best for X' (best-value, best-features, best-security).\n\n"
            "OUTPUT FORMAT: markdown with feature-matrix table + Red/Green flags section + 'Recommended for <buyer profile>' + 'Open questions to send each vendor'.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "vendors", "type": "list[VendorProfile]", "description": "Vendor data — pricing, features, compliance, integrations", "required": True, "example": "[{name:'Acme Analytics', pricing_summary:'$2k/mo seat-based...', feature_list:[...], ...}, ...]"},
            {"name": "requirements", "type": "list[Requirement]", "description": "Must-haves and nice-to-haves with priorities", "required": True, "example": "[{name:'SOC2', priority:'must'}, {name:'Slack integration', priority:'must'}, {name:'On-prem option', priority:'nice'}]"},
            {"name": "buyer_context", "type": "BuyerContext", "description": "Who's buying", "required": True, "example": "{company_size:'500-employee mid-market', regulated_industry:false, budget_usd_annual:120000, decision_timeline_weeks:4}"},
        ],
        "expected_output": {"format": "markdown", "sample": "| Vendor | Pricing | Features | Security | Integration | Support | Lock-in | **Score** |\n|---|---|---|---|---|---|---|---|\n| Acme | 3: seat-based, 30% above budget | 4: covers 8/10 musts | 5: SOC2+ISO27001 | 3: REST only | 4: named CSM | 3: 12mo min | **3.7** |\n\n## 🚩 Red flags\n- Beta-Co has no SOC2 (claims 'in progress' for 18mo)\n\n## 🟢 Green flags\n- Acme has public security audit posted at trust.acme.com"},
        "use_cases": [
            {"scenario": "RFP shortlist evaluation", "example": "5 vendors responded to RFP; this prompt produces the shortlist memo for the steering committee."},
            {"scenario": "Annual contract renewal review", "example": "Compare current vendor against 2 challengers before signing the renewal."},
            {"scenario": "Tools consolidation", "example": "You have 4 overlapping tools; this prompt surfaces which 2 cover 80% of needs."},
            {"scenario": "Procurement audit", "example": "Run quarterly on top-10 vendors by spend to surface contract-renewal risks."},
        ],
        "when_not_to_use": "Don't use when you can't get pricing details — opaque vendors will skew the scoring. Also skip for hardware vendors (different evaluation framework).",
        "few_shot_examples": [
            {
                "input": "3 CRM vendors (Salesforce, HubSpot, Pipedrive) for 50-person sales team, $100k/yr budget, no regulated industry, 6-week timeline. Must-have: Outlook sync, Salesforce migration path, role-based permissions.",
                "output": "| Vendor | Pricing | Features | Security | Integration | Support | Lock-in | **Score** |\n|---|---|---|---|---|---|---|---|\n| Salesforce | 1: $75k+ for tier needed | 5: feature ceiling | 5: enterprise SSO | 3: complex | 3: tiered | 1: 3yr min | **3.0** |\n| HubSpot | 4: $48k mid-tier | 4: covers needs | 4: SOC2 | 5: Outlook native | 5: chat + named CSM | 4: annual | **4.3** |\n| Pipedrive | 5: $25k | 3: lighter | 4: SOC2 | 4: Outlook ok | 4: email | 5: monthly | **4.2** |\n\n## Recommendation: HubSpot for this buyer\nBest balance of budget headroom (52% under budget) + feature coverage. Salesforce is overkill; Pipedrive is light on permissions for a 50-seat team.\n\n## 🚩 Red flags\n- Salesforce 3-year min lock-in is a procurement-committee blocker per your context.\n\n## Open questions to send each vendor\n- HubSpot: confirm role-based permissions cover sales-rep vs SDR distinction (priority 'must').\n- Pipedrive: what's the Salesforce-data-import path for our existing 18k contacts?",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strong at red-flag detection from vendor marketing language."},
            {"model": "gpt-5", "compatibility": "excellent", "notes": "Slightly better at structured matrix output."},
            {"model": "claude-opus-4", "compatibility": "good", "notes": "Use for high-stakes (>$500k/yr) decisions."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable but expect to manually sharpen red flags."},
        ],
        "variations": [
            {"label": "Single-axis sensitivity", "description": "Show how the winner changes if one axis (e.g., budget) shifts.", "prompt_snippet": "Add output: 'Sensitivity: if budget drops 30%, which vendor wins? If security weight doubles, which?'"},
            {"label": "Procurement-package mode", "description": "Output ready-to-send to the procurement team.", "prompt_snippet": "Add sections: 'Negotiation levers per vendor', 'Reference checks needed', 'Contract redlines to request'."},
            {"label": "Open-source-aware", "description": "Include the option 'self-host open-source equivalent' as an implicit option.", "prompt_snippet": "If any vendor's category has a credible OSS alternative, add it as a final 'OSS path' row with TCO estimate (engineering hours + infra)."},
        ],
        "failure_modes": [
            {"symptom": "Takes vendor marketing claims at face value", "fix": "Instruct: 'Evidence only — vendor claims without public proof score lower'"},
            {"symptom": "Misses lock-in clauses in contract terms", "fix": "Explicit check: 'Read contract_terms for: minimum commit, auto-renewal, price-hike caps, data-export guarantee'"},
            {"symptom": "Recommends the most-feature vendor regardless of budget fit", "fix": "Hard rule: if pricing is >120% of budget, that vendor cannot be 'recommended' even if highest scored"},
            {"symptom": "Skips integration depth check (just checks if integration exists)", "fix": "Score integration 5 only if 'native' (not 'via Zapier'). Webhook-only = 3 max."},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-opus-4", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["strategic-tradeoff-analyzer", "rfp-response-builder", "meeting-decision-recorder"],
        "related_tool_slugs": ["airtable", "notion"],
        "related_glossary_slugs": ["vendor-lock-in", "tco", "rfp"],
        "faq": [
            {"question": "How do I get the input vendor data?", "answer": "Send each vendor an RFP with structured response template; paste each response as a vendor entry."},
            {"question": "Should I share this with the vendors?", "answer": "No — it's an internal comparison memo. If asked, share the criteria you used, not the scoring."},
            {"question": "Can it score against OSS alternatives?", "answer": "Yes — use the 'Open-source-aware' variation. The TCO calc is rough but useful for the buy-vs-self-host conversation."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub Prompt Library", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Vendor Comparison Builder — Procurement-Grade Matrix",
        "meta_description": "Compare N vendors across price, features, security, integration, support, lock-in. Red/green flags + recommendation per buyer profile.",
    },

    {
        "slug": "meeting-decision-recorder",
        "title": "Meeting Decision Recorder (decisions ≠ actions ≠ discussion)",
        "category": "business",
        "tldr": "From meeting notes, separate DECISIONS (with rationale + reversal cost) from action items and discussion. Maintains a permanent decision log for the team.",
        "tags": ["decisions", "meeting-notes", "documentation"],
        "best_for_tags": ["decision-tracking", "meeting-notes", "team-coordination"],
        "difficulty_tier": "beginner",
        "full_prompt": (
            "You extract DECISIONS from messy meeting notes. Decisions ≠ action items ≠ discussion. Be strict about the difference.\n\n"
            "DEFINITIONS:\n"
            "- DECISION: a binding choice between alternatives. Has an owner, a date, a reversal cost (cheap/medium/expensive).\n"
            "- ACTION ITEM: a task someone will do. Not a decision unless the act of doing it constitutes a choice.\n"
            "- DISCUSSION: explored but unresolved. Not a decision; surface to the next agenda.\n\n"
            "INPUTS:\n"
            "- meeting_notes: raw notes (transcript, Zoom AI summary, hand-written)\n"
            "- meeting_metadata: {date, attendees, meeting_title}\n"
            "- prior_decisions (optional): list of recent decisions for context (avoids re-recording the same)\n\n"
            "PROCEDURE:\n"
            "1. Identify every candidate decision. For each, check: was a choice made between named alternatives, with an owner?\n"
            "2. For each confirmed decision, record: title (1 line), context (1-2 sentences), decision (1 sentence), alternatives considered, rationale (1-2 sentences), owner, reversal cost (cheap/medium/expensive).\n"
            "3. Separately list action items: {who, what, when}.\n"
            "4. Separately list discussion items that need follow-up: {topic, why unresolved, next agenda}.\n"
            "5. Cross-reference prior_decisions: flag any new decision that contradicts a prior one.\n\n"
            "OUTPUT FORMAT (markdown sections): 'Decisions made' (numbered, full structure), 'Action items' (table: who/what/when), 'Open for next meeting' (bulleted), 'Contradictions with prior decisions' (only if any).\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "meeting_notes", "type": "string", "description": "Raw meeting notes — transcript, AI summary, or written notes", "required": True, "example": "Discussed pricing changes. Sarah proposed moving to usage-based. After 20min debate, agreed to stay seat-based for 2025, revisit Q1 2026. Action: Sarah to draft 2026 pricing memo by Feb 1..."},
            {"name": "meeting_metadata", "type": "MeetingMeta", "description": "Date, attendees, title", "required": True, "example": "{date:'2026-05-14', attendees:['Sarah','Tom','Maya'], meeting_title:'Q2 pricing review'}"},
            {"name": "prior_decisions", "type": "list[Decision]", "description": "Recent decisions for context", "required": False, "example": "[{title:'Pricing model 2025', decision:'Stay seat-based through 2025', date:'2025-12-01'}]"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Decisions made\n\n### 1. Pricing model for 2026\n- **Context:** Sales pushing usage-based, Eng concerned about complexity.\n- **Decision:** Stay seat-based through Q1 2026; revisit Q2 with usage data.\n- **Alternatives considered:** Move to usage-based now; hybrid model.\n- **Rationale:** Insufficient usage data to model revenue impact of switch.\n- **Owner:** Sarah\n- **Reversal cost:** medium (annual contracts will renew on current model)\n\n## Action items\n| Who | What | When |\n|---|---|---|\n| Sarah | Draft 2026 pricing memo with usage-data analysis | Feb 1 |\n\n## Open for next meeting\n- Hybrid model: nobody had a clear preference. Needs Maya's customer-conversation summary first."},
        "use_cases": [
            {"scenario": "Weekly leadership team meetings", "example": "Run on the meeting's AI-transcript output; the decision log becomes the team's source of truth."},
            {"scenario": "Async-decision review", "example": "After a long Slack thread, paste the thread + ask: 'Did we actually decide anything?'"},
            {"scenario": "Onboarding senior hires", "example": "Give them the last 6 months of decisions to ramp on team context faster than reading every meeting note."},
            {"scenario": "Decision contradiction audit", "example": "Run monthly with prior_decisions populated; flag where the team is unintentionally reversing itself."},
        ],
        "when_not_to_use": "Don't use for brainstorming sessions (no decisions expected). Also skip if the notes are too sparse — 'discussed pricing, agreed to revisit' isn't enough to extract a decision.",
        "few_shot_examples": [
            {
                "input": "Notes: 'Talked about hiring. Need senior eng + designer. Sarah will post the eng role this week. Designer — Tom thinks contract first, Maya wants FT. Punted to next week. Also: agreed we will NOT hire a PM in Q2 even if revenue grows — Sarah locked this.'",
                "output": "## Decisions made\n\n### 1. No PM hire in Q2 regardless of revenue\n- **Context:** Recurring debate; revenue growth often triggers premature PM hiring.\n- **Decision:** No PM hire in Q2.\n- **Alternatives considered:** Hire if revenue >$X (specific target not set in meeting).\n- **Rationale:** [missing — note in next meeting]\n- **Owner:** Sarah\n- **Reversal cost:** cheap (decision can be revisited any time)\n\n## Action items\n| Who | What | When |\n|---|---|---|\n| Sarah | Post senior eng role | This week |\n\n## Open for next meeting\n- Designer hiring model: contract-first (Tom) vs FT (Maya). Both need to bring 1 example from similar-stage company.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strong at the decision vs action vs discussion distinction; rarely conflates."},
            {"model": "claude-haiku-4-5", "compatibility": "good", "notes": "Cheap enough to run on every meeting; occasional miss on subtle decisions."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Tends to over-classify action items as decisions. Tighten with: 'an action item is NOT a decision unless...'."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; expect manual review pass on important meetings."},
        ],
        "variations": [
            {"label": "Decision log append-only", "description": "Output JSON to append to a permanent decision log (Notion DB, etc.).", "prompt_snippet": "OUTPUT format: JSON array of decisions only. Skip actions/discussion sections."},
            {"label": "Reversal-cost focus", "description": "Highlight 'expensive' reversal decisions explicitly.", "prompt_snippet": "Add at top of output: '⚠️ Hard-to-reverse decisions in this meeting: <count>'. List them first."},
            {"label": "Stakeholder notification draft", "description": "Generate stakeholder emails for each decision.", "prompt_snippet": "Add 'Stakeholder comms' section: 1-paragraph email per decision, addressed to non-attendees who need to know."},
        ],
        "failure_modes": [
            {"symptom": "Classifies action items as decisions", "fix": "Reinforce definition; reject any item missing 'choice between alternatives'"},
            {"symptom": "Records 'we discussed X' as a decision", "fix": "Discussion without a binding choice goes to 'Open for next meeting'"},
            {"symptom": "Misses decisions buried in long transcripts", "fix": "Pre-summarize transcripts >5k tokens by extracting candidate-decision sentences first"},
            {"symptom": "Doesn't flag contradictions with prior_decisions", "fix": "Add an explicit check step before output: 'Compare every new decision against prior_decisions list'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-haiku-4-5", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["weekly-review-coach", "oneonone-agenda-builder", "strategic-tradeoff-analyzer"],
        "related_tool_slugs": ["notion", "obsidian", "linear"],
        "related_glossary_slugs": ["decision-log", "meeting-notes", "async-communication"],
        "faq": [
            {"question": "What's a 'reversal cost'?", "answer": "Cheap = can flip in a week with no public impact. Medium = month-scale, some stakeholder comms. Expensive = quarter-scale, signed contracts, or public commitments."},
            {"question": "Should every meeting produce decisions?", "answer": "No — many meetings are status updates or brainstorms. The prompt will return an empty Decisions section, which is honest."},
            {"question": "How do I use this with Zoom's AI summary?", "answer": "Paste the AI summary as meeting_notes. Caveat: AI summaries miss subtle decisions; if attendee count is high, also paste the chat transcript."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub Prompt Library", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Meeting Decision Recorder — Extract Decisions from Notes",
        "meta_description": "Separate decisions from action items and discussion. Maintains a permanent decision log with rationale + reversal cost per decision.",
    },

    {
        "slug": "investor-update-monthly",
        "title": "Monthly Investor Update Drafter (honest + scannable)",
        "category": "business",
        "tldr": "Draft a monthly investor update: KPIs with deltas, wins, challenges, asks. ~400 words, scannable, honest about misses without spinning.",
        "tags": ["investor", "update", "fundraising"],
        "best_for_tags": ["fundraising", "investor-relations", "monthly-update"],
        "difficulty_tier": "beginner",
        "full_prompt": (
            "You draft monthly investor updates for early-stage founders. Tone: confident, honest, scannable. No corporate-speak. No spin on misses.\n\n"
            "INPUTS:\n"
            "- month_label: 'May 2026'\n"
            "- kpis: list of {name, current_value, prior_value, unit, target (optional)}\n"
            "- wins: 2-5 things that shipped or moved\n"
            "- challenges: 1-3 honest misses or risks\n"
            "- asks: 1-3 specific requests from investors (intros, hires, expertise)\n"
            "- context (optional): stage, runway, prior-month update for continuity\n\n"
            "STRUCTURE:\n"
            "1. **TL;DR** — 2 sentences. What moved this month + one ask.\n"
            "2. **Numbers** — KPI table with delta vs prior month, color-coded (📈 / 📉 / ➡️).\n"
            "3. **Wins** — bullets, concrete (no 'made progress on X').\n"
            "4. **Challenges** — bullets, name the thing honestly. Add 1-line 'what we're doing about it' each.\n"
            "5. **Asks** — bullets, specific. 'Intro to <name>' not 'help with sales'.\n"
            "6. **Runway / cash** — 1-line if disclosed in inputs.\n\n"
            "RULES:\n"
            "- 350-450 words total. Investors skim.\n"
            "- Use 'we' not 'I' even if it's a solo founder.\n"
            "- Never use: 'rest assured', 'going forward', 'leveraged', 'doubled down', 'pivoted'.\n"
            "- Misses go in Challenges, never reframed as Wins.\n"
            "- Asks should be answerable in 30 seconds by the investor.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "month_label", "type": "string", "description": "The month being reported", "required": True, "example": "May 2026"},
            {"name": "kpis", "type": "list[KPI]", "description": "Monthly KPIs with prior values", "required": True, "example": "[{name:'MRR', current:42000, prior:38500, unit:'USD'}, {name:'Active accounts', current:127, prior:115, unit:'count'}]"},
            {"name": "wins", "type": "list[str]", "description": "2-5 shipping/momentum bullets", "required": True, "example": "['Shipped self-serve onboarding', 'Closed Acme Corp ($24k ACV)', 'Hired senior eng (starts June 1)']"},
            {"name": "challenges", "type": "list[str]", "description": "1-3 honest misses or risks", "required": True, "example": "['Churn ticked up to 3.2% from 2.1%', 'Q2 hiring slower than plan — 1 of 3 roles filled']"},
            {"name": "asks", "type": "list[str]", "description": "1-3 specific investor requests", "required": True, "example": "['Intro to Head of RevOps at <company>', 'Intro to a designer agency that has worked with B2B SaaS at $50k-200k ACV']"},
            {"name": "context", "type": "string", "description": "Stage / runway / prior-update continuity", "required": False, "example": "Series A, 14mo runway, raising in 6-8mo"},
        ],
        "expected_output": {"format": "markdown", "sample": "## OSS AI Hub — May 2026 update\n\n**TL;DR:** MRR grew 9% MoM to $42k; closed Acme as our first $24k ACV deal. Asking for intros to design agencies (see below).\n\n## Numbers\n| Metric | May | Apr | Δ |\n|---|---|---|---|\n| MRR | $42,000 | $38,500 | 📈 +9% |\n| Active accounts | 127 | 115 | 📈 +10% |\n| Churn | 3.2% | 2.1% | 📉 +1.1pp |\n\n## Wins\n- Shipped self-serve onboarding — first 12 self-serve signups closed without sales.\n- Closed Acme Corp ($24k ACV).\n- Hired senior eng, starts June 1.\n\n## Challenges\n- Churn ticked up to 3.2% from 2.1%. Root cause: 2 customers downsized after acquihires. Not a product issue, but we're adding pre-acquihire signal-tracking.\n- Q2 hiring slower than plan: 1 of 3 roles filled. Designer search is the bottleneck.\n\n## Asks\n- Intro to a design agency with B2B SaaS experience at $50k–200k ACV range. We've talked to 3, all priced at enterprise.\n- Intro to Head of RevOps at <name>.\n\nRunway: 14 months. Raising in 6-8 months."},
        "use_cases": [
            {"scenario": "Monthly investor email", "example": "Founder fills in inputs at month-end; output goes directly to investor mailing list."},
            {"scenario": "Board pre-read", "example": "Run before quarterly board meeting; the update is the 1-pager attached to the calendar invite."},
            {"scenario": "Internal team alignment", "example": "Same content sent to team as 'where we stand'; investor and team versions diverge only in the Asks section."},
            {"scenario": "Pre-fundraise prep", "example": "Run on the last 12 months of inputs to surface the narrative arc for the deck."},
        ],
        "when_not_to_use": "Don't use the same prompt for board updates with corporate-governance reporting — those need more structure. Also skip for first-month-of-company updates; there's not enough signal yet.",
        "few_shot_examples": [
            {
                "input": "month: April 2026, kpis: [{MRR, 38500, 35000, USD}, {accounts, 115, 102, count}, {churn, 2.1%, 1.8%, pct}]. wins: ['Beta launched to 30 customers', 'Series A term sheet signed']. challenges: ['Sales cycle still 6+ weeks for enterprise — too slow']. asks: ['Intro to RevOps-savvy advisor']",
                "output": "## OSS AI Hub — April 2026 update\n\n**TL;DR:** Term sheet signed (announcing in May). Beta opened to 30 customers; sales cycle is the constraint to unlock.\n\n## Numbers\n| Metric | Apr | Mar | Δ |\n|---|---|---|---|\n| MRR | $38,500 | $35,000 | 📈 +10% |\n| Active accounts | 115 | 102 | 📈 +13% |\n| Churn | 2.1% | 1.8% | ➡️ +0.3pp |\n\n## Wins\n- Series A term sheet signed (announcing in May update).\n- Beta launched to 30 customers — 24 active in week 1.\n\n## Challenges\n- Enterprise sales cycle is 6+ weeks (target: 3). Root cause: procurement + security review. Hiring a RevOps lead to shorten the procurement-side timeline.\n\n## Asks\n- Intro to a RevOps-savvy advisor who has shortened enterprise sales cycles at Series A → Series B stage.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best balance of concision + honesty. Won't reframe misses."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Slightly more verbose; force the 350-450 word cap."},
            {"model": "claude-haiku-4-5", "compatibility": "good", "notes": "Cheap monthly run; verify the asks are specific enough."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable for self-hosted; tone often skews formal."},
        ],
        "variations": [
            {"label": "Pre-raise tightening", "description": "When raising in <3 months, tone shifts to narrative + traction.", "prompt_snippet": "Add a 'Why now' section above Numbers — 2-3 sentences on the market moment. Tighten Challenges to '... here's what we're doing' (no dwelling)."},
            {"label": "Down-round / hard month", "description": "When KPIs slipped, lean into honesty.", "prompt_snippet": "TL;DR override: lead with the miss. 'Tough month — MRR down 4%; here's what changed and what we're doing.' Investors respect honesty over spin."},
            {"label": "Email-formatted output", "description": "Output as a ready-to-send email with subject line.", "prompt_snippet": "Wrap in: 'Subject: <Company> <Month> update — <one-line headline>'. Add 'Hi <investors>,' opener and signature block."},
        ],
        "failure_modes": [
            {"symptom": "Spins misses as wins ('we learned valuable lessons')", "fix": "Forbid the phrases listed in RULES; reject any 'silver lining' framing of a miss"},
            {"symptom": "Asks are too generic ('help with growth')", "fix": "Require asks to be answerable in 30 seconds — name a person or company"},
            {"symptom": "Goes over word count (600+ words)", "fix": "Strict 350-450 cap; if going over, drop the second-tier win, not the challenge"},
            {"symptom": "KPI deltas wrong direction (e.g., reports churn down when up)", "fix": "Add explicit check: 'If higher_is_worse for metric, invert delta direction'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-haiku-4-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["strategic-tradeoff-analyzer", "weekly-review-coach", "rfp-response-builder"],
        "related_tool_slugs": ["notion", "stripe"],
        "related_glossary_slugs": ["mrr", "runway", "investor-update"],
        "faq": [
            {"question": "How honest is too honest?", "answer": "Investors prefer 'we missed X, here's what we're doing' over 'great month!' Use the prompt's rules — they're calibrated to investor norms."},
            {"question": "Should I CC the team on this?", "answer": "Yes, after sending — keeps them aligned on the public story. Don't BCC investors on team updates though."},
            {"question": "What if my numbers look terrible?", "answer": "Use the 'Down-round / hard month' variation. Investors are 10× more freaked by a missing update than by an honest tough month."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub Prompt Library", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Monthly Investor Update Prompt — Honest, Scannable, 400 Words",
        "meta_description": "Draft monthly investor updates with KPIs, wins, honest challenges, and specific asks. No corporate-speak, no spin on misses.",
    },

    {
        "slug": "rfp-response-builder",
        "title": "RFP Response Builder (capability-mapped)",
        "category": "business",
        "tldr": "Generate a structured RFP response from a question list + your company capability deck. Maps each requirement to a capability with citations and surfaces gaps.",
        "tags": ["rfp", "sales", "proposals"],
        "best_for_tags": ["sales", "rfp", "enterprise-sales"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You build enterprise RFP responses for a B2B SaaS vendor. The buyer asked dozens of questions; you have a capability deck and prior RFP answers. Your job: map each requirement to a capability with citations, surface gaps honestly, and produce responses that pass a procurement review.\n\n"
            "INPUTS:\n"
            "- rfp_questions: structured list — [{section, question_id, question_text, criticality (must|should|nice)}]\n"
            "- capability_library: list of {capability_name, evidence_links, security_docs, customer_proof}\n"
            "- prior_rfp_answers (optional): list of {question_pattern, prior_answer} for reuse\n"
            "- company_context: {industry_specialization, customer_size_focus, competitive_differentiators}\n\n"
            "PROCEDURE:\n"
            "1. For each question, find the best-matching capability. If multiple match, pick the one with strongest evidence.\n"
            "2. Draft an answer (2-5 sentences) with: (a) direct answer, (b) supporting evidence (cite capability_name + evidence_link), (c) customer proof if available.\n"
            "3. If no capability matches, mark the question 'GAP' and note: 'partial coverage via <closest>', or 'true gap — recommend roadmap discussion'.\n"
            "4. For 'must' criticality questions, never bluff — if GAP, be explicit.\n"
            "5. Reuse prior_rfp_answers verbatim where the question_pattern matches, then adapt to this RFP's tone.\n\n"
            "OUTPUT FORMAT: markdown with sections matching RFP sections. Each question: '**Q (criticality):** ...' / '**A:** ...' / '**Evidence:** ...' / Gap badge if applicable.\n\n"
            "Append a SUMMARY at top: total questions, # answered fully, # partial gaps, # true gaps, % must-criticality covered.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "rfp_questions", "type": "list[Question]", "description": "Structured RFP questions with sections and criticality", "required": True, "example": "[{section:'Security', question_id:'S-12', question_text:'Describe your SOC 2 compliance program', criticality:'must'}]"},
            {"name": "capability_library", "type": "list[Capability]", "description": "Your company's capabilities with evidence", "required": True, "example": "[{capability_name:'SOC2 Type II', evidence_links:['trust.example.com/soc2'], security_docs:['SOC2-2026-report.pdf'], customer_proof:'Used by 12 Fortune-500 customers'}]"},
            {"name": "prior_rfp_answers", "type": "list[PriorAnswer]", "description": "Reusable answers from prior RFPs", "required": False, "example": "[{question_pattern:'SOC 2 compliance', prior_answer:'We maintain SOC 2 Type II...'}]"},
            {"name": "company_context", "type": "CompanyContext", "description": "Industry + customer-size + differentiators", "required": True, "example": "{industry_specialization:'healthcare SaaS', customer_size_focus:'mid-market 200-5000 employees', competitive_differentiators:['HIPAA-native', 'no-PHI-in-logs']}"},
        ],
        "expected_output": {"format": "markdown", "sample": "## SUMMARY\n- Total questions: 47\n- Answered fully: 41\n- Partial gaps: 4\n- True gaps: 2\n- Must-criticality coverage: 96% (24 of 25)\n\n## Security\n\n**Q (must):** Describe your SOC 2 compliance program.\n**A:** We maintain SOC 2 Type II, audited annually by Schellman. Report covers Security, Availability, and Confidentiality TSCs. Current report dated Jan 2026, next audit Jan 2027.\n**Evidence:** trust.example.com/soc2 · SOC2-2026-Schellman-report.pdf · Used by 12 Fortune-500 customers including Acme, Beta, Gamma.\n\n**Q (must):** Do you support BYOK (bring your own key) for encryption?\n**A:** ⚠️ **PARTIAL GAP** — We support AWS KMS customer-managed keys. True BYOK with HSM is on the H1 2027 roadmap.\n**Evidence:** docs.example.com/security/encryption · BYOK roadmap"},
        "use_cases": [
            {"scenario": "Enterprise RFP response in 24h", "example": "Sales team receives 47-question RFP Friday, response due Monday. This prompt produces the v1 in <1 hour for SE review."},
            {"scenario": "Capability-deck audit", "example": "Run with last 5 RFPs as input; surface which capabilities show up most often and which evidence links are missing."},
            {"scenario": "Gap-to-roadmap signal", "example": "Aggregate 'true gap' markers across 20 RFPs to identify the top 5 capabilities to build next."},
            {"scenario": "Sales onboarding", "example": "New AE gets the prior_rfp_answers library; the prompt becomes their cheat sheet."},
        ],
        "when_not_to_use": "Don't use for RFPs requiring legal-document attachments (MSA, DPA) — those need lawyer review, not prompt-based generation. Also skip for RFPs without structured questions (paragraphs of prose).",
        "few_shot_examples": [
            {
                "input": "3 questions on Security section: 'SOC 2?', 'GDPR compliance?', 'Pen-test schedule?'. capability_library has SOC2 + GDPR but no pen-test history.",
                "output": "## Security\n\n**Q (must):** SOC 2 compliance?\n**A:** SOC 2 Type II, audited annually by Schellman, current report dated Jan 2026.\n**Evidence:** trust.example.com/soc2\n\n**Q (must):** GDPR compliance?\n**A:** Fully GDPR-compliant. EU data residency available, DPA template at legal.example.com/dpa, Data Protection Officer: dpo@example.com.\n**Evidence:** legal.example.com/gdpr · DPA-template-v3.pdf\n\n**Q (must):** Pen-test schedule?\n**A:** ⚠️ **GAP** — We do not currently run scheduled third-party pen-tests. Internal security review is annual; external pen-test is on the H2 2026 roadmap. Happy to discuss the timeline.\n**Evidence:** N/A — recommend roadmap conversation",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at the gap-honesty calibration; won't bluff on must-criticality."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Preferred for $500k+ RFPs where precision matters."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong at the structured output; sometimes hedges gaps as 'partial' when they're true gaps."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable for self-hosted; expect manual review of every 'gap' label."},
        ],
        "variations": [
            {"label": "Compliance-only mode", "description": "Filter to security/compliance questions only.", "prompt_snippet": "Filter rfp_questions to section in {security, compliance, privacy}. Skip other sections."},
            {"label": "Win-themes mode", "description": "After answers, generate 3 'win themes' to thread through the cover letter.", "prompt_snippet": "Add a final section: 'Top 3 win themes for cover letter' — derived from capability_library + company_context's competitive_differentiators."},
            {"label": "Multi-language", "description": "Localize for non-English RFPs.", "prompt_snippet": "Output in same language as rfp_questions. Keep capability_name in English (preserves traceability)."},
        ],
        "failure_modes": [
            {"symptom": "Bluffs on capabilities not in the library", "fix": "Hard rule: 'If capability_name not in input library, mark GAP. Never invent.'"},
            {"symptom": "Generic answers without evidence links", "fix": "Every answer must cite at least one evidence_link or customer_proof from input"},
            {"symptom": "Treats 'must' and 'nice' questions identically", "fix": "Criticality must inform the depth — must = 3-5 sentences, nice = 1-2 sentences"},
            {"symptom": "Misses cross-section consistency (says 'no PHI' in security, then 'we log PHI' in audit-trail section)", "fix": "Run a final consistency pass: 'Check that capability claims don't contradict across sections'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["vendor-comparison-builder", "strategic-tradeoff-analyzer", "investor-update-monthly"],
        "related_tool_slugs": ["loopio", "notion", "ironcladhq"],
        "related_glossary_slugs": ["rfp", "procurement", "sales-engineering"],
        "faq": [
            {"question": "How do I build the capability_library?", "answer": "Start with your top 5 RFPs from last year. Extract every distinct capability mentioned, with its evidence link. Maintain as a Notion database; update quarterly."},
            {"question": "Should I send the raw prompt output?", "answer": "No — always SE-review. The prompt's v1 is 90% there; the 10% is product-nuance the prompt can't know."},
            {"question": "How do I handle questions about future roadmap items?", "answer": "Be specific. 'On the H2 2026 roadmap' is acceptable; 'we're considering' is not. Procurement reviewers can sniff vagueness."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub Prompt Library", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "RFP Response Builder — Capability-Mapped, Gap-Honest",
        "meta_description": "Generate structured RFP responses with capability citations, evidence links, and explicit gap markers for must-criticality questions.",
    },

    {
        "slug": "okr-quarterly-drafter",
        "title": "OKR Quarterly Drafter (objectives + measurable key results)",
        "category": "business",
        "tldr": "Convert raw quarterly priorities into well-formed OKRs: 3-5 objectives, each with 2-4 measurable key results, time-bound and grading-ready.",
        "tags": ["okrs", "planning", "quarterly"],
        "best_for_tags": ["okr", "planning", "team-alignment"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You convert messy quarterly priorities into well-formed OKRs that pass a 'can I grade this' test.\n\n"
            "DEFINITIONS (strict):\n"
            "- OBJECTIVE: qualitative, ambitious, time-bound, memorable. Inspires.\n"
            "- KEY RESULT: quantitative, measurable, has a baseline + target, has an owner. Provable.\n"
            "- ANTI-PATTERN: 'KR' that is actually a task. ('Launch X' is a task, not a KR. 'Achieve N users for X by Q-end' is a KR.)\n\n"
            "INPUTS:\n"
            "- raw_priorities: free-form list of what the team wants to accomplish this quarter\n"
            "- team_context: {role, team_size, prior_quarter_okr_score, current_metrics_baseline}\n"
            "- timeframe: {quarter_label, start_date, end_date}\n\n"
            "PROCEDURE:\n"
            "1. Cluster raw_priorities into 3-5 themes. Each theme becomes an Objective.\n"
            "2. For each Objective, derive 2-4 Key Results from the raw text:\n"
            "   - Pull a metric (or invent one if implied)\n"
            "   - Set a baseline (from current_metrics_baseline)\n"
            "   - Set a stretch target (50% probability of hitting — should not be sandbagged)\n"
            "   - Assign an owner (from raw text if named; otherwise '<role>')\n"
            "3. Validate every KR: can it be graded 0-1.0 at Q-end? If no, reframe or drop.\n"
            "4. Add a 'WHAT DIDN'T MAKE IT' section with priorities that aren't on this quarter's OKRs — and why.\n\n"
            "OUTPUT FORMAT: markdown with Objectives numbered, KRs lettered, each KR shown as 'Metric: baseline → target. Owner: X.' Stretch annotation if applicable.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "raw_priorities", "type": "string", "description": "Free-form list of what the team wants to accomplish", "required": True, "example": "Ship search v2, hire 2 mid-level eng, reduce churn, launch enterprise tier, get to $1M ARR, fix the onboarding mess, write a book about scaling..."},
            {"name": "team_context", "type": "TeamContext", "description": "Role, team size, prior OKR score, current metrics", "required": True, "example": "{role:'CEO', team_size:18, prior_quarter_okr_score:0.65, current_metrics_baseline:{ARR:850000, churn:3.2, eng_team_size:8}}"},
            {"name": "timeframe", "type": "Timeframe", "description": "Quarter dates", "required": True, "example": "{quarter_label:'Q3 2026', start_date:'2026-07-01', end_date:'2026-09-30'}"},
        ],
        "expected_output": {"format": "markdown", "sample": "# Q3 2026 OKRs\n\n## Objective 1: Cross the $1M ARR line by Q3 close\n- **KR 1a:** ARR $850k → $1.05M. Owner: CEO. Stretch: $1.1M.\n- **KR 1b:** Churn 3.2% → 2.0%. Owner: Head of CS.\n- **KR 1c:** Enterprise pipeline coverage 2× → 3× quota. Owner: Sales.\n\n## Objective 2: Ship search v2 to general availability\n- **KR 2a:** Search v2 % of total queries served: 0% → 50%. Owner: Eng lead.\n- **KR 2b:** Search p99 latency: 800ms → 200ms. Owner: Eng lead.\n\n## What didn't make it (and why)\n- 'Launch enterprise tier': sequenced after we hit $1M ARR (Q4 candidate).\n- 'Write a book': not Q-scope; move to personal projects list."},
        "use_cases": [
            {"scenario": "Leadership planning session", "example": "Founders drop raw priorities into the prompt at end of planning offsite; OKR doc is published by Monday."},
            {"scenario": "OKR cascade", "example": "Company OKRs go in as input; the prompt drafts team-level OKRs that ladder up. Repeat per team."},
            {"scenario": "Quarterly retrospective", "example": "Pass last quarter's OKRs + actuals; prompt grades each and proposes next-quarter adjustments."},
            {"scenario": "Anti-pattern cleanup", "example": "Existing OKRs feel like a task list; this prompt re-frames the 'tasks-as-KRs' into proper KRs."},
        ],
        "when_not_to_use": "Don't use for OKRs at the individual-contributor level — better to use personal goal frameworks. Also skip for early-stage startups (<5 people); OKR overhead exceeds the benefit.",
        "few_shot_examples": [
            {
                "input": "raw_priorities: 'ship search rewrite, hire designer, reduce p99 latency, fix the deploy pain, talk to 50 customers'. context: 'VP Eng, 12 eng team, last quarter OKR score 0.7, current p99: 850ms, deploys take 45min'",
                "output": "## Objective 1: Ship search rewrite to GA quality\n- **KR 1a:** Search v2 query share 0% → 75% by Q-end. Owner: Search lead.\n- **KR 1b:** Search p99 latency 850ms → 250ms. Owner: Search lead.\n\n## Objective 2: Cut engineering friction\n- **KR 2a:** Deploy time 45min → 12min. Owner: Platform lead.\n- **KR 2b:** Deploy failure rate 8% → 2%. Owner: Platform lead.\n\n## Objective 3: Build customer-discovery muscle\n- **KR 3a:** 50 customer conversations completed, summarized in shared doc. Owner: VP Eng.\n- **KR 3b:** 3 product-direction decisions traceable to customer-conversation insights. Owner: VP Eng.\n\n## What didn't make it\n- 'Hire designer' — not engineering scope; flagged to CEO for company-level OKR.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strong at the task-vs-KR distinction; rarely lets task-shaped KRs through."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Preferred for company-level OKRs at >100-person scale."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Slightly more lenient on task-shaped KRs; reinforce the anti-pattern rule."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable for first draft; expect to manually tighten KR ownership."},
        ],
        "variations": [
            {"label": "Mid-quarter rewrite", "description": "When OKRs are clearly off-track at mid-quarter, propose revisions.", "prompt_snippet": "Add input `current_okr_scores`. Output: per-OKR 'keep / adjust target / drop' recommendation with reasoning."},
            {"label": "Cascade-aware", "description": "Ensure team OKRs ladder to company OKRs.", "prompt_snippet": "Add input `company_okrs`. Every team Objective must reference which company Objective it serves."},
            {"label": "Stretch-only mode", "description": "All KRs at 50% probability (ambitious).", "prompt_snippet": "Hard rule: every KR target must be at 50% confidence, not 80% confidence (sandbagged)."},
        ],
        "failure_modes": [
            {"symptom": "KRs are tasks in disguise ('Launch X' instead of 'X reaches N users')", "fix": "Anti-pattern rule in PROCEDURE step 3; every KR must include a measurable metric"},
            {"symptom": "Too many objectives (8-10)", "fix": "Hard cap at 5 objectives; force prioritization with 'what didn't make it' section"},
            {"symptom": "Sandbagged targets (last quarter's actual = next quarter's target)", "fix": "Stretch annotation forces explicit reflection; prompt asks 'is this a 50% probability target or 80%?'"},
            {"symptom": "Missing owners ('TBD' or 'team')", "fix": "Every KR requires a named owner or specific role; reject 'team' as too diffuse"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["weekly-review-coach", "investor-update-monthly", "strategic-tradeoff-analyzer"],
        "related_tool_slugs": ["lattice", "ally", "notion"],
        "related_glossary_slugs": ["okrs", "kpi", "quarterly-planning"],
        "faq": [
            {"question": "How is this different from KPIs?", "answer": "KPIs are ongoing metrics you watch. OKRs are quarterly ambitions with stretch targets. KPIs are speedometer; OKRs are destination."},
            {"question": "Should every team have OKRs?", "answer": "No. OKRs work best for teams shipping cross-functional outcomes. Pure infra/maintenance teams often do better with SLAs."},
            {"question": "What's a good OKR score?", "answer": "0.6-0.7 is healthy — means you set ambitious targets and hit most. >0.85 = you sandbagged. <0.4 = either misaligned plan or external shock."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub Prompt Library", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "OKR Quarterly Drafter Prompt — Objectives + Measurable KRs",
        "meta_description": "Convert raw priorities into well-formed OKRs. 3-5 objectives, 2-4 measurable key results each, baseline + target + owner, grading-ready.",
    },

    {
        "slug": "competitive-landscape-mapper",
        "title": "Competitive Landscape Mapper (positioning + whitespace)",
        "category": "business",
        "tldr": "Map 5-15 competitors on a 2-axis positioning grid, identify whitespace opportunities, surface emerging threats and dying players.",
        "tags": ["competitive-analysis", "positioning", "market"],
        "best_for_tags": ["strategy", "positioning", "market-analysis"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You are a competitive-intel analyst building a positioning landscape. Be specific about axes — vague axes ('quality', 'innovation') produce useless maps.\n\n"
            "INPUTS:\n"
            "- competitors: list of {name, segment, est_revenue (optional), funding_stage, pricing_model, primary_users, last_major_release_date, momentum_signals}\n"
            "- our_company: {name, current_position, target_segment}\n"
            "- axes (optional): user-provided positioning axes. If not provided, you propose 2 axes that meaningfully differentiate.\n\n"
            "PROCEDURE:\n"
            "1. If axes not provided: propose 2 axes that span the landscape (e.g., 'price' × 'flexibility', not 'good' × 'cheap'). Justify the axes.\n"
            "2. Place each competitor on the 2x2 grid with reasoning (1-2 sentences per placement).\n"
            "3. Identify the 4 quadrants. Each quadrant: 'crowded' / 'whitespace' / 'dying' / 'emerging'.\n"
            "4. Flag EMERGING THREATS: any competitor with strong momentum_signals in your target quadrant.\n"
            "5. Flag DYING PLAYERS: any competitor with no major_release in 12+ months OR stale_pricing OR contracting headcount.\n"
            "6. Surface WHITESPACE: which quadrant has the fewest players and matches your target_segment?\n"
            "7. Position us. Are we in a crowded quadrant? Could we move? At what cost?\n\n"
            "OUTPUT FORMAT: markdown with ASCII grid + per-competitor placement + quadrant summary + recommendations.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "competitors", "type": "list[Competitor]", "description": "5-15 competitor profiles", "required": True, "example": "[{name:'Acme', segment:'enterprise', est_revenue:'$30M ARR', funding_stage:'Series C', pricing_model:'seat-based', last_major_release_date:'2026-03-15', momentum_signals:['hired 12 eng in 90 days', 'partnership with AWS announced']}]"},
            {"name": "our_company", "type": "OurCompany", "description": "Our positioning + target", "required": True, "example": "{name:'OSS AI Hub', current_position:'mid-market, free + open-source', target_segment:'developer-first, individual + small teams'}"},
            {"name": "axes", "type": "list[str]", "description": "Two positioning axes (optional)", "required": False, "example": "['pricing model: per-seat → usage-based', 'flexibility: prescriptive → configurable']"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Axes\n- **X:** pricing model (per-seat → usage-based)\n- **Y:** flexibility (prescriptive → configurable)\n\n## Grid\n```\nConfigurable │ [Self-host OSS]      │ [Custom-build platforms]\n             │ • Us            • Foo │ • BarPlatform\n─────────────┼──────────────────────┼────────────────────────\n             │ • Acme (declining)   │ • BigCo (entrenched)\nPrescriptive │ [Vertical SaaS]      │ [Enterprise suites]\n             │ Per-seat            Usage-based\n```\n\n## Quadrant summary\n- **Configurable × Per-seat (us + Foo):** ⚠️ Emerging. Foo's GitHub stars grew 4× in 90 days.\n- **Configurable × Usage-based (BarPlatform):** Whitespace. Only 1 player.\n- **Prescriptive × Per-seat (Acme):** Dying. No release in 14 months.\n\n## Recommendations\n- Defend against Foo (configurable per-seat) — they have 30 days of momentum on us.\n- Whitespace in Configurable × Usage-based; question whether it matches our developer-first segment."},
        "use_cases": [
            {"scenario": "Annual strategy planning", "example": "Refresh the landscape every January with the prior year's competitor moves; informs the year's positioning shifts."},
            {"scenario": "New-market entry", "example": "Before entering a new segment, run the landscape on incumbents. Where's the whitespace?"},
            {"scenario": "Fundraising deck", "example": "Investors want to see the landscape. The grid + whitespace claim grounds the 'why us' slide."},
            {"scenario": "Competitive review", "example": "Quarterly check-in: who's gaining momentum? Who's dying? Where should we shift?"},
        ],
        "when_not_to_use": "Don't use for highly fragmented markets (50+ competitors) — a 2-axis grid oversimplifies. Use a tier-based segmentation instead. Also skip in monopoly markets where one player dominates.",
        "few_shot_examples": [
            {
                "input": "competitors: 6 vector DB players: Pinecone, Weaviate, Qdrant, Milvus, Chroma, pgvector. our_company: OSS AI Hub directory. axes: ['hosted → self-host', 'specialist → general-purpose']",
                "output": "## Grid\n```\nGeneral-purpose │ • pgvector              │ (whitespace)\n                │   (Postgres extension)  │\n────────────────┼─────────────────────────┼────────────────────\nSpecialist      │ • Qdrant • Weaviate     │ • Pinecone\n                │ • Milvus • Chroma       │   (managed)\n                │   Self-host             │  Hosted\n```\n\n## Quadrant summary\n- **Specialist × Self-host (4 players):** Crowded. Qdrant + Weaviate are gaining; Milvus is enterprise-skewed; Chroma is dev-friendly.\n- **General-purpose × Self-host (1 player):** Whitespace-ish. pgvector dominates because Postgres is everywhere.\n- **Specialist × Hosted (1 player):** Pinecone owns this corner.\n- **General-purpose × Hosted:** True whitespace. Any cloud provider could fill this with a managed Postgres + pgvector tier.\n\n## Emerging threats\n- Qdrant momentum (5x GitHub stars in 12mo).\n\n## Recommendations\n- We're a directory, not a vector DB — our 'positioning' here is informational. Useful to surface this grid in our `/vector-databases` category page so users can self-navigate.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at proposing specific axes (avoids 'good vs bad' framing)."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Preferred for >10 competitors or when the market is technical/nuanced."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong matrix output; sometimes vague on momentum signals."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; manual review of placements expected."},
        ],
        "variations": [
            {"label": "Threat-only mode", "description": "Skip placement; just surface threats.", "prompt_snippet": "Skip steps 2-3. Run only step 4 (emerging threats) + step 5 (dying players). Output prioritized threat list."},
            {"label": "Whitespace-search mode", "description": "Optimize for finding gaps.", "prompt_snippet": "Run with 3 different axis pairs (cost×flex, segment×depth, OSS×managed). Surface the whitespace that appears in 2+ of the maps."},
            {"label": "Investor-deck format", "description": "Output ready for slide.", "prompt_snippet": "Output: 1 slide title ('The landscape, May 2026'), 1 grid, 3-bullet 'why we win in this corner', no other prose."},
        ],
        "failure_modes": [
            {"symptom": "Picks vague axes ('quality', 'innovation')", "fix": "Reject axes that aren't measurable; require axes to span a real spectrum like 'pricing model' or 'deployment model'"},
            {"symptom": "Places all competitors in same quadrant", "fix": "Force the axes to differentiate; if grid is unbalanced, propose alternative axes"},
            {"symptom": "Misses emerging threats from absence of momentum_signals input", "fix": "If momentum_signals not provided for a competitor, surface 'data gap — recommend manual check'"},
            {"symptom": "Recommends moving us to a crowded quadrant", "fix": "Recommendation must factor in cost of repositioning; default is defend current position unless whitespace × match-segment"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["strategic-tradeoff-analyzer", "vendor-comparison-builder", "okr-quarterly-drafter"],
        "related_tool_slugs": ["airtable", "notion"],
        "related_glossary_slugs": ["positioning", "competitive-analysis", "whitespace"],
        "faq": [
            {"question": "How many competitors should I include?", "answer": "5-12 is the sweet spot. <5 = too sparse for a 2x2; >15 = the grid becomes unreadable. Filter to credible threats only."},
            {"question": "How do I source momentum_signals?", "answer": "Track 3 signals quarterly: hiring (LinkedIn), product releases (changelogs/blog), public mentions (G2/HN). 10 minutes per competitor."},
            {"question": "Should I share this with the team?", "answer": "Yes, but quarterly — not weekly. Competitive obsession kills focus."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub Prompt Library", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Competitive Landscape Mapper — Positioning Grid + Whitespace",
        "meta_description": "Map 5-15 competitors on a positioning grid. Identify whitespace, emerging threats, dying players. Specific axes only — no 'good vs bad'.",
    },

    {
        "slug": "pricing-page-rewriter",
        "title": "Pricing Page Rewriter (conversion-focused)",
        "category": "business",
        "tldr": "Rewrite a SaaS pricing page for clarity and conversion: tier labels, anchor pricing, feature differentiation, and a 'right one for you' guide.",
        "tags": ["pricing", "saas", "conversion"],
        "best_for_tags": ["pricing-strategy", "conversion", "marketing"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You rewrite SaaS pricing pages for clarity and conversion. The current page is buried in features or confusing on price. Your job: tier-by-tier rewrite that helps the right buyer self-select.\n\n"
            "INPUTS:\n"
            "- current_tiers: list of {tier_name, price, included_features, target_user}\n"
            "- value_metric: the unit your pricing scales on (seats, requests, GB, etc.)\n"
            "- positioning_axes: 1-2 differentiators you want to lean into\n"
            "- competitor_anchors: 2-3 competitor prices for context\n\n"
            "FOR EACH TIER, generate:\n"
            "1. **Tier label** — 1-2 words, evocative, not generic ('Solo' not 'Starter').\n"
            "2. **Best-for line** — 'For <persona> who need <outcome>'. 12-18 words.\n"
            "3. **Price + value metric** — '$X / <unit> / month'. If usage-based, give a 'typical bill' example.\n"
            "4. **Top 3 features** — what users actually buy this tier FOR. Not 12 features.\n"
            "5. **Limit / upgrade trigger** — 1 line: when do you outgrow this tier?\n"
            "6. **CTA** — verb-led: 'Start Solo' not 'Get Started'.\n\n"
            "ALSO GENERATE:\n"
            "- 'Which is right for you' — 3-question flow that maps to a tier.\n"
            "- 'FAQ' — 4-6 pricing-specific Qs (annual discount, refund policy, can-I-change-tiers, what-counts-as-a-seat).\n"
            "- Anchor: a 'Most popular' badge on one tier. Justify which.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "current_tiers", "type": "list[Tier]", "description": "Current pricing tiers with features", "required": True, "example": "[{tier_name:'Free', price:'$0', included_features:['100 requests/mo','community support'], target_user:'individual devs'}]"},
            {"name": "value_metric", "type": "string", "description": "Pricing unit", "required": True, "example": "API requests per month"},
            {"name": "positioning_axes", "type": "list[str]", "description": "1-2 differentiators", "required": True, "example": "['open-source-first', 'no per-seat tax']"},
            {"name": "competitor_anchors", "type": "list[CompetitorPrice]", "description": "2-3 competitor prices for context", "required": False, "example": "[{name:'Competitor X', tier:'Pro', price:'$99/mo for 10k requests'}]"},
        ],
        "expected_output": {"format": "markdown", "sample": "## Solo\n*For solo devs and indie hackers who need to ship without a credit card commitment.*\n\n**$0 forever** — first 1,000 requests/mo, then $0.01/request\n\n- Full API access (no feature flags)\n- 10 saved stacks\n- Community Discord\n\n> Outgrowing Solo? You'll know when you hit 10k requests/mo or want SSO.\n\n[Start Solo →]\n\n---\n\n## Builder ⭐ Most popular\n*For small teams shipping AI features who need usage-based pricing without per-seat tax.*\n\n**$0.005/request** (typical bill at 50k req/mo: $250)\n\n..."},
        "use_cases": [
            {"scenario": "Pricing page redesign", "example": "Marketing + product run this on the current pricing page; outputs tier-by-tier rewrite for designer."},
            {"scenario": "Tier consolidation", "example": "Going from 5 tiers to 3 — this prompt suggests which features collapse where."},
            {"scenario": "Annual-discount communication", "example": "Add 'annual-discount-mode' variation; tightens the annual savings story."},
            {"scenario": "Competitive repositioning", "example": "When a competitor raises prices, run this to surface where to anchor against them."},
        ],
        "when_not_to_use": "Don't use for B2B contract pricing (negotiated, not page-based). Also skip for very early stage (<$10k MRR) — your pricing page matters less than conversations.",
        "few_shot_examples": [
            {
                "input": "current_tiers: 3 tiers [Free, Pro $29, Enterprise 'contact us']. value_metric: 'API requests'. positioning_axes: ['open-source', 'no per-seat']. competitor_anchors: [{Acme, Pro, $99/mo 50k req}]",
                "output": "## Solo\n*For indie devs and weekend builders who want to ship without committing a credit card.*\n\n**Free forever** — 5,000 requests/mo. Then $0.005/request, no caps.\n\n- All features (no enterprise gate)\n- 5 saved stacks\n- Community Discord\n\n> Outgrowing Solo? You'll know when you cross 5k req/mo regularly.\n\n[Start Solo →]\n\n---\n\n## Builder ⭐ Most popular\n*For startups shipping AI in production who want predictable bills without per-seat tax.*\n\n**$29/mo** — 50,000 requests included, then $0.003/request. (Acme charges $99 for 50k — same features.)\n\n- Production SLA (99.9% uptime)\n- Unlimited team seats\n- Email + chat support (12-hour response)\n\n> Outgrowing Builder? When you hit 500k req/mo or need SOC2 reports.\n\n[Start Builder →]\n\n---\n\n## Enterprise\n*For organizations with security review, custom contracts, or >500k requests/mo.*\n\n**Custom pricing** — usage-based with annual commits. Includes SSO, SOC2 reports, custom DPAs, named support engineer.\n\n[Book a 15-min call →]\n\n---\n\n## Which is right for you?\n1. Shipping in production with paying customers? → **Builder**.\n2. Just exploring or hobbyist? → **Solo**.\n3. Need SSO, SOC2, or DPA? → **Enterprise**.\n\n## FAQ\n- **Is there an annual discount?** Yes — 20% off if you prepay 12 months on Builder.\n- **What counts as a 'request'?** Each API call counts as 1. Batched calls count as 1 even if multiple records.\n- **Can I change tiers?** Anytime, mid-month. We prorate.\n- **Refund policy?** 30-day full refund on Builder, no questions asked.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at the tier-label evocativeness; will push back on generic names like 'Starter/Pro/Enterprise'."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong on conversion patterns; sometimes plays it safe on tier names."},
            {"model": "claude-haiku-4-5", "compatibility": "good", "notes": "Cheap for iterating on tier labels; verify the FAQ answers manually."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; expect generic CTAs that need sharpening."},
        ],
        "variations": [
            {"label": "Annual-only discount lean", "description": "Position annual as the default.", "prompt_snippet": "Show annual price prominently with monthly as a 'less commit' option. Discount: 17-25% off."},
            {"label": "Open-source / paid hybrid", "description": "When the product has an OSS edition.", "prompt_snippet": "Add a 'Self-hosted (OSS)' tier above Solo. Free, with link to repo. Comparison row: 'managed vs self-hosted'."},
            {"label": "Anti-Acme positioning", "description": "Sharpen against a specific competitor.", "prompt_snippet": "Each tier includes a comparison line: 'Acme's <equivalent tier> is $X for fewer requests' or 'Acme charges per-seat — we don't'."},
        ],
        "failure_modes": [
            {"symptom": "Tier names are generic ('Starter/Pro/Business/Enterprise')", "fix": "Forbid the generic-quartet; require evocative names that match the persona"},
            {"symptom": "12-bullet feature lists per tier", "fix": "Hard cap: 3 features per tier. The rest go in a comparison table elsewhere."},
            {"symptom": "Vague CTAs ('Get Started')", "fix": "Verb-led tier-specific: 'Start Solo', 'Try Builder for 14 days', 'Book Enterprise call'"},
            {"symptom": "Anchor competitor pricing is wrong", "fix": "Pull from competitor_anchors only; don't infer prices the input doesn't have"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-haiku-4-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["competitive-landscape-mapper", "investor-update-monthly", "strategic-tradeoff-analyzer"],
        "related_tool_slugs": ["stripe", "chargebee", "paddle"],
        "related_glossary_slugs": ["pricing-strategy", "value-metric", "saas-pricing"],
        "faq": [
            {"question": "Should I anchor against competitors on the page?", "answer": "Sparingly — one comparison line per tier max. More than that feels defensive. The grid in your strategic memo can be more aggressive."},
            {"question": "How often should I rewrite pricing?", "answer": "Major rewrite every 12-18 months. Small tweaks (anchor, FAQ) quarterly. Never rewrite in the middle of a fundraise."},
            {"question": "What if my value_metric is wrong?", "answer": "That's a bigger problem than the page. Use the 'Strategic tradeoff analyzer' prompt first to think through usage-based vs per-seat vs tiered."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub Prompt Library", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Pricing Page Rewriter Prompt — Conversion-Focused Tiers",
        "meta_description": "Rewrite SaaS pricing for clarity + conversion. Tier-by-tier with evocative labels, anchor pricing, top-3 features each, and a 'right one for you' guide.",
    },
]
