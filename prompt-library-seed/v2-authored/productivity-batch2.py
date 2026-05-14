"""Productivity prompts — batch 2."""

RECORDS = [
    {
        "slug": "inbox-zero-triage",
        "title": "Inbox Triage With Reply Drafts",
        "tldr": "Reads a batch of unread emails and produces a triage decision per message: archive, reply, delegate, schedule. For ‘reply’ items, drafts a concise response that the user can edit and send.",
        "category": "productivity",
        "tags": ["email", "triage", "productivity", "inbox-zero"],
        "best_for_tags": ["executives", "founders", "consultants"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Morning inbox sweep", "example": "60 unreads → triage list with 12 archives, 8 replies drafted, 3 to delegate, 4 to schedule."},
            {"scenario": "Post-vacation catchup", "example": "Hundreds of emails compressed into action list."},
            {"scenario": "Weekly review", "example": "Run on snoozed/follow-up folder to surface what's still actionable."},
            {"scenario": "Delegated inbox support", "example": "EA generates first-pass triage; principal reviews and approves."},
        ],
        "when_not_to_use": "Skip for sensitive / legal / HR emails — those need human judgment. Skip when each email is genuinely complex (long deals, executive matters) — case-by-case beats batch.",
        "full_prompt": """You are triaging emails. Each gets a decision and, where relevant, a reply draft.

INPUT
- A list of unread emails (sender, subject, snippet): {emails}
- About the user: {user_context}                       (role, preferences, what they typically reply to)
- Available time: {minutes}                            (how much triage time today)
- Constraints (sender domains to always handle differently, banned phrases, etc.): {constraints}

OUTPUT — one entry per email:

### Email N
- **From / Subject**: <from / subject>
- **Decision**: archive / reply / delegate / schedule / read-later
- **Why**: 1 line — what made you choose this decision
- **If REPLY**: draft a 1-3 sentence response below
- **If DELEGATE**: who and what to forward
- **If SCHEDULE**: when (today/this-week/next-week/never) and what to do then

Then at the end:

## Summary
- Archives: N
- Replies drafted: N
- Delegated: N
- Scheduled: N

## Time-check
Estimated minutes to review + send the drafts. Flag if it exceeds {minutes}.

## Three you should look at FIRST
The three highest-leverage items — important decisions, time-sensitive, or strategic.

## What I'd NOT do without confirming
2-4 items where my decision is uncertain — surface these so the user catches mistakes.

DECISION HEURISTICS
- Archive: newsletters/notifications with no action; FYI threads where user isn't the decision-maker.
- Reply: directly addressed, expected response, < 2 min to draft.
- Delegate: actionable but not by this user; tag a role (EA, sales rep, support lead).
- Schedule: needs thought / longer response / right context; assign a time block.
- Read-later: useful but not urgent; goes to read-later list.

DRAFT GUIDELINES
- 1-3 sentences when possible.
- Match register of the sender's email.
- Don't promise anything beyond what user_context supports.
- Don't open with ‘Thanks for reaching out.’ Use a concrete acknowledgment.
- Sign-off matches user's typical style (the constraints field may specify).

CRITICAL RULES
- NEVER mark something as ‘send draft directly’ — every draft requires human review.
- Flag suspicious emails (phishing, spam) but don't auto-archive without flagging.
- For threads where you can't tell context, lean toward read-later or surface in ‘look at first.’

EMAILS
{emails}

Begin.""",
        "input_variables": [
            {"name": "emails", "type": "string", "description": "Unread emails list (from, subject, snippet)", "required": True, "example": "1. From: alice@bigco.com Subject: Q3 review meeting Snippet: Hey, do you have time...\\n2. From: noreply@github.com Subject: PR #234 review requested..."},
            {"name": "user_context", "type": "string", "description": "About the user", "required": True, "example": "CEO of 30-person SaaS company. Replies fast to customers + investors. Prefers concise. Delegates internal ops to EA."},
            {"name": "minutes", "type": "integer", "description": "Available triage time", "required": True, "example": "20"},
            {"name": "constraints", "type": "string", "description": "Special handling rules", "required": False, "example": "investors@... always reply same-day. Press inquiries always delegate to comms@. Family emails never auto-drafted."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Per-email triage with decision/why/draft (if reply); summary with counts; top-3 priorities; uncertain-items list.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on judgment calls; surfaces uncertainty honestly."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; reply drafts can be over-polite — re-pin user voice."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; ‘uncertain items’ section often empty — force minimum 2."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Defaults to ‘archive everything’; needs balanced triage examples."},
        ],
        "variations": [
            {"label": "VIP-aware", "description": "Always escalate from VIP senders.", "prompt_snippet": "Add: ‘from VIP list = always Reply or Schedule, never Archive. VIP list: {names_or_domains}.’"},
            {"label": "Time-of-day aware", "description": "Triage differently morning vs end-of-day.", "prompt_snippet": "Add: ‘if morning, drafts can be longer; if end-of-day, ultra-concise replies and aggressive schedule-for-tomorrow.’"},
            {"label": "Multi-language", "description": "Handle non-English emails.", "prompt_snippet": "Add: ‘detect language; draft reply in same language as sender; flag if user_context doesn't include speakers of that language.’"},
        ],
        "failure_modes": [
            {"symptom": "Drafts are templates / sound formulaic.", "fix": "Re-pin user voice; require concrete acknowledgment in each draft, not ‘Thanks for reaching out.’"},
            {"symptom": "Marks important emails as archive.", "fix": "Add: ‘when uncertain, lean toward Reply or Schedule; archiving is irreversible.’"},
            {"symptom": "Drafts promise meetings / commitments.", "fix": "Add: ‘don't accept meetings, agree to deadlines, or commit dollars in drafts. Surface those for user.’"},
            {"symptom": "No uncertain-items flagged.", "fix": "Force minimum 2 in section — every batch has edge cases."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["email-thread-respond", "weekly-review-coach"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["inbox-zero", "email-triage"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should AI auto-send any of these?", "answer": "Never. Drafts are starting points; the user reviews and sends. Auto-send introduces too many failure modes: tone mismatch, factual errors, missed context."},
            {"question": "How does it know what's important?", "answer": "From user_context. Be specific: ‘I prioritize customers, investors, and direct reports; I deprioritize newsletters, recruiting outreach.’ Vague context produces vague triage."},
            {"question": "What about Gmail integration?", "answer": "This prompt produces decisions; integration is downstream. Connect to Gmail API to actually archive/move based on the decisions, with human-in-the-loop for replies."},
        ],
        "meta_title": "Inbox Triage With Reply Drafts — Prompt",
        "meta_description": "Triage unread emails into archive/reply/delegate/schedule with reply drafts. Includes uncertain-items flag and time-check.",
    },
    {
        "slug": "weekly-priorities-from-vague-list",
        "title": "Weekly Priorities From a Vague TODO List",
        "tldr": "Takes a messy TODO list and turns it into a structured weekly plan with sharp priorities, time estimates, and ‘what won't get done’ — forcing realistic capacity acknowledgment.",
        "category": "productivity",
        "tags": ["priorities", "weekly-planning", "todo", "capacity"],
        "best_for_tags": ["weekly-planning", "individual-productivity", "managers"],
        "difficulty_tier": "beginner",
        "featured": True,
        "use_cases": [
            {"scenario": "Sunday-night weekly planning", "example": "Brain-dump 30 items → 5 priorities + day allocation + explicit deferral list."},
            {"scenario": "Manager weekly setup", "example": "Direct reports' goals + your priorities → coherent week."},
            {"scenario": "Solopreneur week design", "example": "Sales, build, marketing, ops items balanced by available focused hours."},
            {"scenario": "Post-vacation reset", "example": "Backlog → realistic restart plan."},
        ],
        "when_not_to_use": "Skip when the list is short (< 8 items — just decide). Skip when external constraints (boss said do X) dominate — those go first, not negotiable.",
        "full_prompt": """You are a senior coach helping someone plan a realistic week.

INPUT
- TODO list (likely messy): {todo_list}
- Available focused hours this week (after meetings/interruptions): {focus_hours}
- Standing commitments / blocks: {standing_commitments}
- The person's ‘one thing’ — if they get nothing else done, this matters: {one_thing}

OUTPUT

## 1. Sharpening
Rewrite each TODO into action language. ‘Email vendor’ becomes ‘Reply to vendor's Q3 quote with our counter or accept by EOD Tuesday.’ Vague items get rejected back with a question.

## 2. Time estimate per item
Realistic estimate. Use bands: <30min, 30-90min, 2-4hr, half-day, full-day.

## 3. The week's PRIORITIES (3-5)
What WILL get done. Sort by:
- Strategic importance (does it move ‘one thing’?)
- Time-sensitivity
- Effort × impact

Each priority gets a day allocation: Mon AM, Tue PM, etc.

## 4. The ‘won't get done’ list
2-5 items being intentionally deferred. For each:
- Why it's being cut
- When it actually gets done (next week / next month / never)

This list is non-negotiable — if you can't cut anything, you're lying about capacity.

## 5. Defensible day plan
| Day | AM block | PM block |
Each block is one ITEM, not a list. Multitasking is decline; the week works best with single-focused blocks.

## 6. What to RENEGOTIATE
If the input shows over-commitment, identify 1-2 things the person should renegotiate (push deadline, get help, reduce scope). With suggested phrasing.

## 7. Friday check
The one question to ask Friday afternoon to know if this was a good week.

RULES
- Focus_hours is the binding constraint. If estimates exceed focus_hours, items get cut to fit. No magic.
- ‘One thing’ gets a slot before anything else.
- Reject vague items rather than do them — return them to the user with a clarifying question.
- Don't add tasks that aren't in the list.

INPUT

TODO list:
{todo_list}

Focus hours:
{focus_hours}

Standing commitments:
{standing_commitments}

One thing:
{one_thing}

Now plan.""",
        "input_variables": [
            {"name": "todo_list", "type": "string", "description": "Messy brain-dumped TODO list", "required": True, "example": "Reply to Bob. Q3 plan. Hire 2 engineers. Fix invoicing bug. Write blog post. Review specs. Coffee with Sarah. Update onboarding. Call accountant."},
            {"name": "focus_hours", "type": "integer", "description": "Available focused work hours this week", "required": True, "example": "18"},
            {"name": "standing_commitments", "type": "string", "description": "Recurring blocks / meetings", "required": False, "example": "All-hands Monday 10-11, 1:1s Tuesday afternoon, customer calls every morning 9-10"},
            {"name": "one_thing", "type": "string", "description": "The most important thing", "required": True, "example": "Ship the new onboarding flow"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: sharpened list, time estimates, 3-5 priorities, won't-get-done list, day plan grid, renegotiate items, Friday check question.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Honest about capacity; cuts confidently."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes lists too many priorities — re-pin 3-5 cap."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; won't-get-done list can be soft."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Tends to keep everything; explicit cut-discipline reminder needed."},
        ],
        "variations": [
            {"label": "Team variant", "description": "Plan across a team.", "prompt_snippet": "Add: ‘inputs include team members + their capacity. Output assigns items to people, not just to days.’"},
            {"label": "Sprint-shaped", "description": "Two-week sprint.", "prompt_snippet": "Replace ‘week’ with ‘sprint’; double focus_hours; structure priorities as sprint goals."},
            {"label": "With energy mapping", "description": "Match items to energy levels.", "prompt_snippet": "Add: ‘categorize each item as deep-focus / shallow / social; match to typical energy patterns (deep AM, social PM).’"},
        ],
        "failure_modes": [
            {"symptom": "Plans 30+ hours into 18 focus hours.", "fix": "Re-pin: ‘sum of estimates ≤ focus_hours; cut to fit.’"},
            {"symptom": "Vague items pass through unchanged.", "fix": "Add: ‘any item that's a noun or verb fragment gets rejected back as a clarifying question.’"},
            {"symptom": "‘Won't get done’ is empty.", "fix": "Force: ‘at minimum 2 items must be cut; if list fits in focus_hours, capacity was probably overstated.’"},
            {"symptom": "Day plan has 5 things per block.", "fix": "Add: ‘ONE item per block; multitasking is the enemy of getting anything done.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["weekly-review-coach", "priority-matrix-eisenhower", "standup-update-formatter"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["weekly-planning", "time-blocking"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What if focus_hours is wrong?", "answer": "Most people overestimate. Track for 2-3 weeks; you'll find your actual number. The plan only works if focus_hours is true."},
            {"question": "Should ‘one thing’ change weekly?", "answer": "Yes — it's the most important thing THIS week. The strategic ‘north star’ is monthly/quarterly. Weekly ‘one thing’ is the lever you're pulling now."},
            {"question": "What about urgent surprises?", "answer": "Plans break; that's life. Re-plan mid-week if a real emergency hits. But ‘fire-drill’ as default state means plan isn't sticking — fix the deeper cause."},
        ],
        "meta_title": "Weekly Priorities From a Vague TODO List — Prompt",
        "meta_description": "Turn messy TODOs into a realistic weekly plan: priorities, day blocks, explicit ‘won't get done’ list, Friday check question.",
    },
]
