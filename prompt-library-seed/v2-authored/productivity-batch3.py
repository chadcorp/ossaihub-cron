"""Productivity — batch 3."""

RECORDS = [
    {
        "slug": "weekly-review-friday-shutdown",
        "title": "Weekly Review — Friday Shutdown",
        "tldr": "End-of-week ritual that captures progress, surfaces stuck-points, plans next-week's three priorities, and CLOSES the loop on open commitments so Monday morning isn't archaeology.",
        "category": "productivity",
        "tags": ["gtd", "weekly-review", "shutdown", "planning"],
        "best_for_tags": ["knowledge-workers", "managers", "ic-engineers"],
        "difficulty_tier": "beginner",
        "featured": True,
        "use_cases": [
            {"scenario": "Engineering manager Friday close", "example": "Reviews team standup notes, pulls own commitments, plans Monday's first hour."},
            {"scenario": "Senior IC weekly close", "example": "Triages own inbox, decides what's actually shipping next week."},
            {"scenario": "Consultant client-week review", "example": "End of client week — captures deliverables-status, open follow-ups, next-week's billable plan."},
            {"scenario": "Founder weekly close", "example": "Triages 80 open threads down to the 3 that move the company."},
        ],
        "when_not_to_use": "Skip when you've been heads-down for 2+ weeks — do a full quarterly review instead. Skip when current week's fires are still actively burning; the shutdown shouldn't be theater.",
        "full_prompt": """You are a weekly shutdown coach. Run a calibrated Friday close that captures, decides, and CLOSES open loops.

INPUT
- This week's calendar / commitments hit: {week_summary}
- Outstanding tasks / threads: {open_threads}
- Roles I'm carrying right now: {roles}              (e.g., 'IC engineer', 'manager of 3', 'parent of 2')
- Energy right now (1-10): {energy}
- Constraints next week: {constraints}              (e.g., 'PTO Tue', 'all-hands Wed', '2 deep-work blocks')

OUTPUT

## 1. The truthful week recap (3 bullets max)
- What ACTUALLY shipped this week (not what was planned).
- What slipped — and the real reason (not the polite reason).
- The single highest-leverage thing I did, even if small.

## 2. Open-loop sweep
List EVERY open thread + suggested next action:
| Thread | Status | Next action | Owner | Due |
|---|---|---|---|---|

Categorize each:
- **Close now** — 2-min action, do it Friday.
- **Schedule** — needs a calendar block.
- **Delegate** — pass it, with the right context.
- **Drop** — explicit decision NOT to do. (This is the most important column.)

## 3. The 'commitments to others' check
Things I told someone I'd do this week and didn't:
- For each: send a short message Friday rescheduling or closing. NEVER leave a Monday-morning surprise.

## 4. Next week — three priorities (no more)
Pick THREE. Not five. Not ten. Three.
- Priority 1: ___ (must-ship)
- Priority 2: ___ (high-value)
- Priority 3: ___ (high-leverage but not urgent)

For each, name:
- Concrete artifact (PR / doc / decision) that proves it's done.
- Time estimate vs available time.
- The single thing that could block it.

## 5. The Monday-morning hour
What ARE you doing in your first 60 minutes Monday? Be specific.
- Open file: ___
- First action: ___
- Slack first: ___ (or not)

This eliminates Monday-morning archaeology.

## 6. Recovery / rest plan
- Two non-work commitments this weekend (be honest).
- Sunday-evening setup, if any (anti-anxiety move, NOT pre-work).

## 7. One question to mull
A real question — strategic / career / personal — to let your subconscious work on over the weekend. Not 'should I quit my job'-sized; one well-defined puzzle.

CRITICAL RULES
- Be HONEST about slipped tasks. The shutdown only works if it's truthful.
- THREE priorities. Hard cap. If everything's a priority, nothing is.
- Drop column is mandatory. Not dropping things is how weeks pile up.
- Commitments-to-others check prevents Monday surprises.
- Recovery plan is part of the shutdown, not separate.

INPUTS
Week summary: {week_summary}
Open threads: {open_threads}
Roles: {roles}
Energy: {energy}
Constraints: {constraints}

Begin.""",
        "input_variables": [
            {"name": "week_summary", "type": "string", "description": "What happened this week", "required": True, "example": "Shipped auth flow refactor, two 1:1s, sprint planning, two interview rounds, escalation thread with vendor."},
            {"name": "open_threads", "type": "string", "description": "Outstanding tasks / commitments", "required": True, "example": "(1) finish security review for X feature, (2) reply to candidate Maya, (3) write team-update for VP, (4) book Q3 offsite venue..."},
            {"name": "roles", "type": "string", "description": "Roles in play this week", "required": True, "example": "Eng manager of 4 + tech lead on Project Phoenix + interview-loop coordinator"},
            {"name": "energy", "type": "string", "description": "Energy (1-10)", "required": True, "example": "4 / 10 — Fri exhausted, Q2 was heavy"},
            {"name": "constraints", "type": "string", "description": "Next-week constraints", "required": True, "example": "Tue PTO, all-hands Wed PM, Friday off-site morning"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: truthful recap, open-loop sweep table, commitments-to-others check, three priorities (capped), Monday-morning hour plan, recovery plan, one question to mull.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest on honesty about slips + ruthless 'drop' column."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can pad to 5+ priorities — re-pin hard cap of 3."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; weaker on the introspective 'one question to mull'."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Works well — this prompt is structure-heavy, not deep-reasoning."},
        ],
        "variations": [
            {"label": "Manager weekly", "description": "Adds team-leverage section.", "prompt_snippet": "Add section: 'Where did I unblock vs block my team this week? What's my team's #1 blocker next week, and what can I move?'"},
            {"label": "Founder weekly", "description": "Strategic + tactical.", "prompt_snippet": "Add a 'metric-of-the-week' that I committed to last week, what it did, and what I'm tracking next week. One number only."},
            {"label": "Two-week sprint close", "description": "Bi-weekly version.", "prompt_snippet": "Run this against TWO weeks of inputs. Add a 'sprint retro' bullet: what to keep / change / drop in the next sprint."},
        ],
        "failure_modes": [
            {"symptom": "More than 3 priorities.", "fix": "Hard rule: 'three. If forced to add a fourth, drop one. Output explicit drop with reason.'"},
            {"symptom": "Recap is sanitized.", "fix": "Re-pin: 'slipped section must name the real reason (overcommitted / not motivated / blocked / scope creep) — not the polite reason.'"},
            {"symptom": "No 'drop' column entries.", "fix": "Require: 'minimum 2 items in drop column. If truly none, state explicit reasoning.'"},
            {"symptom": "Monday-hour plan is vague.", "fix": "Force: 'first action = open this specific file / send this specific message / start this specific timer.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["inbox-zero-triage", "okr-quality-audit", "weekly-study-plan"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["gtd", "weekly-review"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How long should this take?", "answer": "20-30 minutes the first time, 12-15 once it's habit. Past 40 min, you're overthinking — close it and move."},
            {"question": "What if my week was a disaster?", "answer": "Run it anyway. The 'why it slipped' bullets are highest value on bad weeks — pattern-detection compounds."},
            {"question": "Does the 'one question' really help?", "answer": "Mileage varies. Some weeks it produces a Monday insight; some weeks nothing. The cost is low; the upside is real on big decisions."},
            {"question": "Three priorities feels too few.", "answer": "That's the point. Past 3, completion rate drops sharply. If 3 feels impossible, your problem is over-commitment, not the cap."},
        ],
        "meta_title": "Weekly Review — Friday Shutdown Prompt",
        "meta_description": "End-of-week ritual: truthful recap, open-loop sweep, three priorities, Monday-morning hour plan, recovery plan, and one strategic question.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "meeting-agenda-with-decisions",
        "title": "Meeting Agenda With Decisions",
        "tldr": "Generates an agenda built around DECISIONS, not topics. Names the decision, the inputs, the decider, and the time budget. Skips meetings that should be docs.",
        "category": "productivity",
        "tags": ["meetings", "agenda", "decision-making", "productivity"],
        "best_for_tags": ["managers", "founders", "pms"],
        "difficulty_tier": "beginner",
        "featured": True,
        "use_cases": [
            {"scenario": "Weekly leadership sync", "example": "Replace 'topics' format with 'decisions to make this week.'"},
            {"scenario": "Cross-team coordination", "example": "PMs gathering 4 teams — what 2-3 decisions justify the meeting."},
            {"scenario": "1:1 prep", "example": "Manager prepping 1:1 — convert vague topics into decisions or coaching outcomes."},
            {"scenario": "Cross-functional planning kickoff", "example": "Quarterly planning — name the 5 decisions, who decides each, what inputs are required pre-meeting."},
        ],
        "when_not_to_use": "Skip for purely social meetings (1:1s with rapport-building, team lunches). Skip for status-only meetings that should be Slack updates — the prompt will tell you so.",
        "full_prompt": """You are a meeting-design coach. Build an agenda around DECISIONS, not topics. Cancel the meeting if it shouldn't exist.

INPUT
- Meeting purpose (rough): {purpose}
- Attendees (name + role): {attendees}
- Time budget: {time_budget}
- Pre-reads available: {pre_reads}
- Decisions / outcomes wanted: {desired_outcomes}
- History: prior meeting outcomes / blockers: {history}

OUTPUT

## 1. Meeting check — does this meeting need to exist?
Run this filter FIRST. Return one of:
- **PROCEED** — there are real decisions; meeting is justified.
- **REPLACE WITH DOC** — it's status / FYI; propose async write-up instead with template.
- **REPLACE WITH 2-PERSON SYNC** — only 2 of the attendees needed; others can read notes.
- **POSTPONE** — required inputs not ready; meeting will be theater.

If anything other than PROCEED: explain why + propose alternative. STOP. Don't write the agenda.

## 2. Decisions list (PROCEED only)
For each decision (target 2-4, NOT 8):
- **Decision:** stated as a binary or pick-one (not a vague question).
- **Inputs needed:** pre-read items / data points required to decide.
- **Decider:** ONE name. (RACI: who calls it.)
- **Time budget:** minutes.
- **Pre-work:** what attendees MUST review pre-meeting.

## 3. The agenda (decision-led)
[5 min] **Frame** — Why we're here. The 2-4 decisions on the table.

[X min] **Decision 1:** [framed as binary]
- Background (2 sentences max, since pre-read covered it)
- Inputs / open questions
- Voice from each attendee (capped 2 min each)
- DECIDER: ___ calls it.
- Decision: __________________

[repeat for decisions 2-4]

[5 min] **Decisions recap + owners** — Each decision restated + who owns the action by when.

[5 min buffer]

Total: ___ min. Compare against time_budget. If over, cut a decision.

## 4. Pre-read packet
A 1-page pre-read for attendees:
- Context: 3-5 bullets
- For each decision: the FRAMING (what's being decided), the OPTIONS (2-3), and the RECOMMENDATION (if any).
- Required by: 24h before meeting.

## 5. What this meeting will NOT do
Explicit anti-scope:
- Won't decide [thing] — that's a separate meeting / different decider.
- Won't rehash [past decision] — closed.
- Won't replace [doc / async channel].

This prevents scope creep.

## 6. Cancellation criteria
If [X] happens before the meeting, CANCEL it:
- "If the pre-read isn't done by 24h before, meeting becomes 30-min doc review instead."
- "If decider can't attend, postpone — no proxy-deciding."

CRITICAL RULES
- Meeting check is FIRST. Don't write an agenda for a meeting that should be a doc.
- Each decision has ONE decider, not a vote.
- Time budget is HONEST. Better to cut a decision than blow the time.
- Pre-read is mandatory. No pre-read = no meeting.
- Anti-scope section prevents the meeting from sprawling.

INPUTS
Purpose: {purpose}
Attendees: {attendees}
Time budget: {time_budget}
Desired outcomes: {desired_outcomes}

Begin.""",
        "input_variables": [
            {"name": "purpose", "type": "string", "description": "Rough meeting purpose", "required": True, "example": "Decide whether to ship Project Phoenix beta to 5 customers Friday vs. delay another sprint."},
            {"name": "attendees", "type": "string", "description": "Name + role of each attendee", "required": True, "example": "Sara (VP Eng, decider), Mark (TL Phoenix), Jess (PM), Devon (CS), Pat (Security)"},
            {"name": "time_budget", "type": "string", "description": "Time budget", "required": True, "example": "45 min"},
            {"name": "pre_reads", "type": "string", "description": "Pre-reads available", "required": False, "example": "Test pass-rate report, customer-readiness checklist, security-review draft"},
            {"name": "desired_outcomes", "type": "string", "description": "Decisions wanted", "required": True, "example": "(1) ship Friday yes/no, (2) which 5 customers, (3) rollback plan owner"},
            {"name": "history", "type": "string", "description": "Prior context", "required": False, "example": "Beta date already slipped twice; CS pressure to ship; security concerns last meeting."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: meeting check (proceed/replace/postpone), decisions list (2-4 max), decision-led agenda, pre-read packet, anti-scope, cancellation criteria.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest on 'replace with doc' calls; ruthless about cancellation."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; tends to default to PROCEED — re-pin meeting-check filter."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; weaker on anti-scope specificity."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Works well — structure-heavy, low-reasoning."},
        ],
        "variations": [
            {"label": "1:1 prep", "description": "Reframe as 1:1 prep, not meeting design.", "prompt_snippet": "Replace 'decider' with 'coaching outcome'. Decisions section becomes 'what does this person need from this 1:1 — career / unblock / feedback / signal-check?'"},
            {"label": "Board / exec readout", "description": "Optimize for board cadence.", "prompt_snippet": "Frame the meeting around 3 decisions board needs to make + 5-min Q&A per. Pre-read becomes board memo (1-page summary + 2-page detail)."},
            {"label": "Async-first replacement", "description": "Output a doc, not an agenda.", "prompt_snippet": "Skip the agenda. Output a 1-page async-decision doc the decider can read + comment on. Comment thread = meeting."},
        ],
        "failure_modes": [
            {"symptom": "Approves meetings that should be docs.", "fix": "Re-pin: 'meeting check is the FIRST gate. Status-only or one-voice meetings = REPLACE WITH DOC. Default to skepticism.'"},
            {"symptom": "Vague decisions ('discuss roadmap').", "fix": "Force: 'each decision must be a binary or pick-one. \"Discuss\" is not a decision.'"},
            {"symptom": "More than 4 decisions in a 45-min meeting.", "fix": "Hard cap: 'max 1 decision per 15 min of meeting time. Exceed = cut decisions or extend.'"},
            {"symptom": "Anti-scope section is generic.", "fix": "Require: 'each anti-scope bullet names a specific topic this meeting will NOT cover, with where it should go instead.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["go-no-go-decision-meeting-prep", "okr-quality-audit", "internal-memo-from-decision"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["decision-doc", "raci"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Won't this kill some meetings I need?", "answer": "Yes — that's the point. Most weekly meetings could be a Slack thread + Loom + 15-min sync of the actual deciders. The filter is brutal because meeting bloat is the norm."},
            {"question": "Why one decider per decision?", "answer": "Group voting causes 'consensus theater' where nobody owns the call. One decider = clear accountability + faster meetings. Inputs come from everyone; the call comes from one person."},
            {"question": "What about brainstorming meetings?", "answer": "Different format — don't run this prompt for them. This is for decision meetings. Brainstorms have their own structure (silent → diverge → converge)."},
            {"question": "Can the decider be 'the group'?", "answer": "Only for explicitly chartered groups (a board, a committee with voting rules). Otherwise no — 'the group decides' usually means 'nothing gets decided.'"},
        ],
        "meta_title": "Meeting Agenda With Decisions — Productivity Prompt",
        "meta_description": "Build a meeting agenda around decisions, not topics. Cancel meetings that should be docs. Each decision has a decider, inputs, time budget.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "calendar-audit-by-energy",
        "title": "Calendar Audit By Energy Type",
        "tldr": "Audits last 2 weeks of calendar by energy type (deep / shallow / draining / generative) and time-of-day. Surfaces structural mismatches and concrete rearrangements.",
        "category": "productivity",
        "tags": ["calendar", "audit", "energy-management", "scheduling"],
        "best_for_tags": ["knowledge-workers", "managers", "creatives"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Manager calendar audit", "example": "Booked solid; identify which meetings to cut/move/redesign by energy type."},
            {"scenario": "IC engineer audit", "example": "Deep work scattered into 30-min slots between meetings — surface the wasted hours."},
            {"scenario": "Founder audit", "example": "Reactive day = no strategic work; rearrange to defend AM deep blocks."},
            {"scenario": "Creative / writer audit", "example": "Generative work mixed with admin; sort by energy and consolidate."},
        ],
        "when_not_to_use": "Skip if your job is fully reactive (some support / on-call roles). Skip without 2+ weeks of historical calendar data — n=1 week is noise.",
        "full_prompt": """You are a calendar-energy auditor. Sort 2 weeks of calendar by energy type and time-of-day, surface mismatches, propose concrete moves.

INPUT
- Last 2 weeks of calendar events (date, time, duration, title, attendees, my role): {calendar_events}
- My natural energy curve: {energy_curve}     (e.g., 'peak focus 8-11am, slump 1-3pm, second-wind 4-6pm')
- Job-shape constraints: {job_constraints}    (on-call rotation, mandatory standups, etc.)
- My deep-work targets: {deep_work_target}    (hours/week)

OUTPUT

## 1. Energy classification
For each event, tag energy type:
- **Deep** — needs sustained focus (>45 min, low context-switching). Coding, writing, design, analysis.
- **Shallow** — reactive / coordination. Slack triage, quick decisions, async-replacements.
- **Generative** — creative output. Strategy, brainstorm, design exploration.
- **Draining** — emotionally heavy. Hard 1:1s, customer escalations, firefights.
- **Recovery** — needed buffer. Lunch break, walks, recovery time between draining events.

Output a table:
| Day | Time | Title | Duration | Energy type | My natural energy at this time |

## 2. Mismatch surface
Where does the calendar fight the natural energy curve?
- "Deep work scheduled 1-3pm during slump (5 instances) — predicted output drop."
- "Draining 1:1s back-to-back 3-5pm — no recovery between."
- "Generative brainstorm sessions scheduled Friday 4pm — generally late-week energy crash."

Quantify: how many hours/week are mis-matched?

## 3. Hidden costs
Things the calendar isn't tracking that bleed energy:
- Context-switching tax: number of distinct topics per day.
- Meeting buffers: meetings starting :00 with no transition time.
- Late-running meetings consuming break time (look for back-to-back ≥30 min).

## 4. Rearrangement plan
Concrete moves. Don't propose 'block deep work' — propose SPECIFIC moves:
- "Move Tue 1pm engineering review to Wed 2pm (after deep-work block ends naturally)."
- "Consolidate three 30-min 1:1s scheduled Tue/Wed/Thu into a single 90-min block Wed morning."
- "Decline recurring 'weekly sync' Friday 4pm — replace with async Friday-morning update."

For each move:
- What energy it fixes.
- Who's impacted + how to communicate the move.
- 1-line script to send.

## 5. The 'protected hours' commit
Based on the audit, commit:
- Deep-work block: ___ days/week, ___ to ___ time. Inviolable except for [criterion].
- Recovery slots: ___.
- Office hours / open-door time: ___ (so people know where to find you).

These go on the calendar AS EVENTS with names. Not 'free time' — booked.

## 6. The 'cut, keep, redesign' list
For each recurring meeting:
- **Cut:** decline / cancel.
- **Keep:** working as-is.
- **Redesign:** keep but change format (async, shorter, less frequent).

Be honest. A 'redesign every recurring meeting' suggestion is real most of the time.

CRITICAL RULES
- Energy types are EVIDENCE-BASED — judge by event content, not your mood.
- Mismatch quantified in hours/week, not vibes.
- Rearrangement moves are SPECIFIC (date, time, owner, comms script).
- Protected hours are CALENDAR EVENTS, not aspirations.
- 'Cut / keep / redesign' applies to recurring meetings — be ruthless.

CALENDAR
{calendar_events}

Begin.""",
        "input_variables": [
            {"name": "calendar_events", "type": "string", "description": "2 weeks of calendar events", "required": True, "example": "Mon 9-10 standup (7 ppl), Mon 10-11 1:1 with Mark, Mon 11-12 design review, Mon 12-1 lunch, Mon 1-2 cross-team sync (4 teams), Mon 2-3 deep work, Mon 3-4 customer call..."},
            {"name": "energy_curve", "type": "string", "description": "Natural energy pattern", "required": True, "example": "Peak focus 8-11am, slump 12-2pm, second-wind 4-6pm, low after 7pm"},
            {"name": "job_constraints", "type": "string", "description": "Job-shape constraints", "required": True, "example": "On-call rotation 1 wk/mo, mandatory daily standup 9:30am, weekly leadership 1pm Tue."},
            {"name": "deep_work_target", "type": "string", "description": "Deep-work hours/week target", "required": True, "example": "12 hrs/week in 2-3 hr blocks"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: energy classification table, mismatch surface with hours quantified, hidden costs, rearrangement plan with comms scripts, protected-hours commitment, recurring meeting cut/keep/redesign list.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at honest energy classification + ruthless cut decisions."},
            {"model": "gpt-4o", "compatibility": "good", "notes": "Solid; tends to be polite ('redesign' default) — re-pin cut/keep/redesign honesty."},
            {"model": "gemini-1.5-pro", "compatibility": "excellent", "notes": "Strong on 2-week pattern detection across structured events."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for one week of calendar; thins on cross-week patterns."},
        ],
        "variations": [
            {"label": "Team calendar audit", "description": "Audit a team's collective calendar.", "prompt_snippet": "Replace 'my' with 'the team's'. Surface meeting-load per person, meeting-overlap inefficiencies, meeting-free days at team level."},
            {"label": "Pre-quarter reset", "description": "Quarterly planning reset.", "prompt_snippet": "Audit last quarter (12 weeks) instead of 2. Surface trends not weeks; recommend a fresh quarter calendar template."},
            {"label": "Async-first redesign", "description": "Optimize for async work.", "prompt_snippet": "Tilt the cut/redesign list toward 'replace with async update'. Score every recurring meeting on async-feasibility."},
        ],
        "failure_modes": [
            {"symptom": "Vague rearrangements ('protect more deep work').", "fix": "Force: 'each move = specific date + time + who's affected + 1-line comms script.'"},
            {"symptom": "Too polite on recurring meetings.", "fix": "Re-pin: 'cut / keep / redesign — assume 30-50% of recurring meetings should be cut or redesigned. Default to ruthless.'"},
            {"symptom": "Misses context-switching tax.", "fix": "Add: 'count distinct topics per day. Highlight days with >5 topic-switches as flagged.'"},
            {"symptom": "Protected hours are aspirations.", "fix": "Require: 'protected hours go on calendar as named events with hold criterion. Not abstract zones.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["weekly-review-friday-shutdown", "meeting-agenda-with-decisions", "inbox-zero-triage"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["deep-work", "energy-management"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How do I export 2 weeks of calendar for input?", "answer": "Most calendar tools export ICS or CSV. Paste in just title + time + duration; the prompt doesn't need attendees / location for energy classification."},
            {"question": "What if I can't control most meetings?", "answer": "The cut/keep/redesign list still works — the cuts get proposed to whoever owns them. Even partial wins (1-2 cuts/quarter) compound."},
            {"question": "Why energy classification vs just task type?", "answer": "Task type ('coding', 'meeting') hides cost. A 1:1 with a high-trust report is cheap; a 1:1 with a struggling report is expensive. Energy captures the real cost."},
            {"question": "How often should I run this?", "answer": "Quarterly is the sweet spot. Monthly is too noisy; annual is too late. Quarterly aligns with planning cycles."},
        ],
        "meta_title": "Calendar Audit By Energy — Productivity Prompt",
        "meta_description": "Audit 2 weeks of calendar by energy type and natural-energy curve. Surface mismatches, propose specific rearrangements, commit protected hours.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "delegation-decision-framework",
        "title": "Delegation Decision Framework",
        "tldr": "Walks through whether to do, delegate, defer, or drop a specific task — naming the right delegatee, the brief, the success criteria, and how to NOT take it back.",
        "category": "productivity",
        "tags": ["delegation", "management", "decision-making", "leadership"],
        "best_for_tags": ["managers", "founders", "tech-leads"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "New manager learning to delegate", "example": "Has a list of 8 things they're doing themselves — which should go to which report."},
            {"scenario": "Founder bottleneck audit", "example": "Founder doing 12 hats; which can go to the first 3 hires."},
            {"scenario": "Tech lead delegating to senior IC", "example": "Specific feature work that should go to senior engineer with clear scope."},
            {"scenario": "Quarterly capacity reset", "example": "Manager reset — what tasks belong to the manager vs the team."},
        ],
        "when_not_to_use": "Skip when the team doesn't have anyone with capacity OR capability — delegation theater is worse than self-doing. Skip when the task is irreducibly the leader's (firing, hiring decisions, hard 1:1s).",
        "full_prompt": """You are a delegation coach. Walk a leader through do / delegate / defer / drop on a specific task.

INPUT
- The task: {task}                     (concrete, not 'manage the team')
- Why I'm currently doing it: {current_reason}
- Team / reports available: {team_members}    (name, role, current load, capability for this)
- My time cost if I do it: {my_time_cost}
- Stakes if it goes wrong: {stakes}    (revenue / reputation / safety / morale)
- Time horizon: {horizon}              (this week / this quarter / ongoing)

OUTPUT

## 1. Honest task analysis
- Is this work IRREDUCIBLE to me? (firing, hiring final-call, hard 1:1s, vision-setting → usually yes; everything else → usually no)
- Am I doing it because it's MINE or because nobody else CAN?
- What's my SUNK-COST attachment to it?

If irreducible: STOP here, recommend keep + add 'why irreducible' explanation. Skip rest.

## 2. The 4-quadrant call
Place this task in one of:

- **DO** — irreducible OR stakes too high to delegate AND no one ready.
- **DELEGATE** — someone is ready (or close); benefits compound for them.
- **DEFER** — important but not now; will be a delegate-candidate in N weeks.
- **DROP** — looked important; isn't actually moving the needle. Kill it.

Justify the call in 2-3 sentences.

## 3. (DELEGATE only) Pick the person
For each candidate in {team_members}:
- Capability fit: ___
- Capacity: ___
- Growth value for them: ___
- Risk: ___

Pick ONE. State why over the others.

If NOBODY is fit:
- Closest candidate + 'stretch with safety net' plan.
- OR explicit decision: 'no one ready; this becomes DO until [hiring / development milestone].'

## 4. (DELEGATE only) The delegation brief
A 1-page brief the delegatee gets:
- **What:** the task, in one sentence.
- **Why it matters:** business / team impact.
- **Definition of done:** concrete artifact / outcome.
- **Decision authority:** what they can decide vs check with me on.
- **Resources:** budget, people, time.
- **Check-ins:** when, what they bring, what I give.
- **Failure modes I'm watching for:** 2-3 specific risks.
- **What success looks like at 30 days / 60 days.**

## 5. The 'don't take it back' commitment
The #1 failure of delegation is the manager taking it back at the first wobble.
- What's the FIRST wobble I'll be tempted to take this back on?
- What's my pre-committed response (coach vs rescue)?
- Who reminds me if I start re-absorbing?

## 6. (DROP only) The drop narrative
- Who needs to know it's dropped.
- 1-line message to send.
- What might break and how I'll know.

## 7. Calendar / system update
What changes immediately:
- Calendar invite ___ moved to delegatee.
- Doc owner changed to ___.
- Slack channel ownership ___.

If nothing changes systems-wise, the delegation didn't really happen.

CRITICAL RULES
- Be HONEST about ego-attachment. Many 'irreducible' tasks aren't.
- One delegatee, not a committee. (Co-ownership = no ownership.)
- Don't-take-it-back commitment is REQUIRED — it's where delegations die.
- Drop is a real option. Most overcommitted managers have 2-3 things on this list.

TASK
{task}

Begin.""",
        "input_variables": [
            {"name": "task", "type": "string", "description": "The specific task being considered", "required": True, "example": "Owning the weekly customer-success digest — pulling data, writing summary, sending to leadership."},
            {"name": "current_reason", "type": "string", "description": "Why I'm currently doing it", "required": True, "example": "Started it 9 months ago; nobody else has the context; I'm comfortable with it."},
            {"name": "team_members", "type": "string", "description": "Team / reports + capability", "required": True, "example": "Maya (Sr CS Manager — strong writing, full load), Devon (CS analyst — growth role, has time), Pat (Ops — overloaded)"},
            {"name": "my_time_cost", "type": "string", "description": "Time it costs me", "required": True, "example": "3-4 hrs / week"},
            {"name": "stakes", "type": "string", "description": "Stakes if it goes wrong", "required": True, "example": "Internal-only; mild reputation impact if late or sloppy; no revenue impact."},
            {"name": "horizon", "type": "string", "description": "Time horizon", "required": True, "example": "Ongoing — recurring weekly task"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: irreducibility check, 4-quadrant call, person picked, full delegation brief, don't-take-it-back commitment, drop narrative (if drop), calendar/system updates.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest on ego-attachment honesty + delegation brief quality."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can soft-pedal irreducibility test — re-pin."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; sometimes vague on don't-take-it-back commitment."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Works well — structure-heavy; weaker on nuanced person selection."},
        ],
        "variations": [
            {"label": "Batch delegation", "description": "Run on a list of tasks.", "prompt_snippet": "Run sections 1-2 against a LIST of tasks. Output a portfolio view: do / delegate / defer / drop counts + total time freed."},
            {"label": "Founder-specific", "description": "Founder bottleneck audit.", "prompt_snippet": "Add irreducibility test specifically for founder tasks (board, fundraise, hiring senior, top-customer relationships). Default toward 'delegate everything else.'"},
            {"label": "Promotion-engine variant", "description": "Frame as growth opportunity.", "prompt_snippet": "Re-frame section 3: for each candidate, rate this as a promotion-track stretch task. Pick the candidate where this is most career-positive."},
        ],
        "failure_modes": [
            {"symptom": "Recommends 'do' too often.", "fix": "Re-pin: 'irreducibility test is strict. Default to delegate. \"Nobody else can\" is usually \"nobody else has the context — I can fix that.\"'"},
            {"symptom": "Vague delegation brief.", "fix": "Force: 'each brief section has a concrete example, not a placeholder. Definition of done = specific artifact.'"},
            {"symptom": "No don't-take-it-back commitment.", "fix": "Require: 'pre-commit the first wobble + the coach-not-rescue response. Otherwise this delegation will fail.'"},
            {"symptom": "Skips system updates.", "fix": "Force section 7: 'if calendar / doc-owner / channel-owner doesn't change, the delegation isn't real.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["weekly-review-friday-shutdown", "calendar-audit-by-energy", "okr-quality-audit"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["delegation", "raci"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What if my team is too junior?", "answer": "Then 'stretch with safety net' is the path — pick the closest candidate, define the safety net (your check-ins, escape valve, rollback plan). Don't use junior-ness as a permanent excuse to keep tasks."},
            {"question": "What's a 'stretch with safety net' plan?", "answer": "Pair the new owner with you for the first 2-3 cycles. They do the work; you review BEFORE it goes out. Iteration 1 = lots of review; iteration 3 = light touch."},
            {"question": "How do I know I'm taking it back too much?", "answer": "Pre-committed response. The first time you'd otherwise step in, ask yourself: am I coaching or rescuing? Rescuing = stop. Track frequency."},
            {"question": "What if the delegatee fails?", "answer": "Then you learn something — about their fit, the brief quality, your check-in cadence. Failed delegation is data, not proof that you should do everything yourself."},
        ],
        "meta_title": "Delegation Decision Framework — Productivity Prompt",
        "meta_description": "Walk through do / delegate / defer / drop for a specific task: irreducibility check, person fit, delegation brief, don't-take-it-back commitment.",
        "version": "v2.0",
        "release_status": "stable",
    },
]
