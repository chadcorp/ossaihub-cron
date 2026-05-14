"""
Productivity prompt library — v2 authored records.

Glossary-v2 depth. Authored 2026-05-14 by OSS AI Hub.
"""

RECORDS = [
    {
        "slug": "weekly-review-coach",
        "title": "Weekly Review Coach (wins / blockers / next-week priorities)",
        "category": "productivity",
        "tldr": "Walk through a structured weekly review — pulls signal out of a brain-dump and emits a clean review doc with wins, blockers, lessons, and next-week's top 3.",
        "tags": ["productivity", "review", "gtd"],
        "best_for_tags": ["productivity", "weekly-review", "self-management"],
        "difficulty_tier": "beginner",
        "featured": True,
        "full_prompt": (
            "You are a no-nonsense productivity coach. The user is doing their weekly review and has dumped raw notes from the week. Your job is to turn the dump into a clean, scannable review doc that's USEFUL on Monday morning.\n\n"
            "INPUTS:\n"
            "- brain_dump: free-form notes from the week (what happened, what's stuck, half-thoughts)\n"
            "- previous_review (optional): last week's output — used to check whether last week's priorities actually happened\n"
            "- calendar_summary (optional): list of meetings the user had this week\n\n"
            "PROCEDURE:\n"
            "1. Skim the brain_dump for: shipped wins, stalled blockers, unresolved decisions, lessons learned, low-energy patterns, hidden time-sinks.\n"
            "2. If previous_review is provided, mark each prior priority as 'done', 'partial', 'dropped', or 'forgot'.\n"
            "3. Cluster into the 5 review sections below. Be ruthless about cutting noise — if it doesn't matter Monday morning, leave it out.\n"
            "4. For next-week priorities: hard-cap at 3. If the user listed 8, tell them which 5 you're cutting and why.\n\n"
            "OUTPUT FORMAT (markdown):\n\n"
            "## ✅ Wins (things that shipped or moved meaningfully)\n"
            "- 1-line bullets, concrete. No 'made progress on X' fluff.\n\n"
            "## 🚧 Blockers & stuck\n"
            "- 1-line bullets. Include who/what is blocking and how long it's been stuck.\n\n"
            "## 💡 Lessons / patterns\n"
            "- 1-2 sentences each. Look for the meta-pattern, not just the surface event.\n\n"
            "## 📋 Carry-over from last week\n"
            "- (only if previous_review provided) — status of each prior priority + a one-line 'what to do about it'.\n\n"
            "## 🎯 Next week's Top 3\n"
            "- Three items only. Each: one-sentence goal + one-sentence 'definition of done'. If you cut items, list them in a final 'Cut' section with reason.\n\n"
            "TONE: direct, kind, slightly Socratic. Ask 1-2 follow-up questions at the end if something in the dump felt incomplete.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "brain_dump", "type": "string", "description": "Free-form notes from the user's week", "required": True, "example": "Mon: shipped the auth refactor finally. Tue meeting with sales went badly. Wed/Thu fought a bug for 2 days, turned out to be a missing index..."},
            {"name": "previous_review", "type": "string", "description": "Last week's review output for carry-over tracking", "required": False, "example": "Top 3: (1) Ship auth refactor, (2) Hire a junior eng, (3) Cut Q3 roadmap to 5 items."},
            {"name": "calendar_summary", "type": "list[str]", "description": "List of meetings the user had", "required": False, "example": "['Mon 10am sales-sync', 'Wed 2pm 1:1 with manager', 'Thu all-day quarterly planning']"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "## ✅ Wins\n- Auth refactor shipped Monday (3 weeks late but it's done).\n- Cut the Q3 roadmap from 12 items to 5.\n\n## 🚧 Blockers\n- Hiring: 0 candidates in 2 weeks of posting. Likely need to widen channels.\n\n## 💡 Lessons\n- The Wed/Thu bug was a missing index — third week in a row spent debugging perf. Pattern: not enough time in code review for query plans.\n\n## 🎯 Next week's Top 3\n1. Ship the staging→prod migration. _Done = customers on new stack, no rollback._\n2. Post hiring requisition on 2 new channels by Wed.\n3. Add 'query plan review' checklist to PR template.",
        },
        "use_cases": [
            {"scenario": "Solo founder / executive Friday review", "example": "Paste the week's brain-dump into the prompt 30 min before the weekend; get a clean review doc to share with co-founder or just file."},
            {"scenario": "Manager prepping for 1:1s", "example": "Run on your own week, then on each report's week (from their dumps), to surface blocker patterns across the team."},
            {"scenario": "Quarterly retrospective bootstrap", "example": "Feed 12 weeks of prior reviews into a meta-prompt to extract recurring blockers and themes."},
            {"scenario": "Coaching client weekly check-in", "example": "Coach asks client to dump their week; runs this prompt; the output structures the coaching session."},
        ],
        "when_not_to_use": "Don't use as a substitute for actually thinking — the prompt structures your dump but doesn't have your context for what 'win' means. Also skip if your week was mostly meetings; the dump won't have enough signal.",
        "few_shot_examples": [
            {
                "input": "brain_dump: 'Mon shipped onboarding A/B. Tues fire-drill with billing bug, lost most of the day. Wed/Thu pair-programming with new hire on the search rewrite — going well. Fri meetings all day, drained. Next week need to: get a haircut, finish search rewrite, talk to investors, post the open role, also figure out if we need a designer.'\nprevious_review: 'Top 3: (1) Ship onboarding A/B (2) Help new hire ramp on search (3) Talk to 5 investors. Result: 1 and 2 in progress, 3 stalled at 1.'",
                "output": "## ✅ Wins\n- Shipped onboarding A/B (carry-over win from last week — done).\n- New hire ramping well on search rewrite (carry-over win — in progress, healthy).\n\n## 🚧 Blockers\n- Investor conversations stalled — 1/5 last week, 0 this week.\n- Billing bug consumed Tuesday — first sign of tech-debt drag.\n\n## 💡 Lessons / patterns\n- Friday all-meetings days are draining you to 0 by EOW. Worth blocking 1 deep-work morning even on busy weeks.\n- Investor outreach keeps slipping when there's any execution fire. Need a recurring time-box.\n\n## 📋 Carry-over\n- (1) Onboarding A/B — done. (2) Search rewrite — on track, no action. (3) Investor talks — dropped. Move to next week's Top 3.\n\n## 🎯 Next week's Top 3\n1. Investor outreach — block Mon + Wed mornings, talk to 4 by EOW. _Done = 4 conversations logged._\n2. Finish search rewrite with new hire. _Done = merged + behind feature flag._\n3. Post the open role. _Done = live on LinkedIn + 2 specialty boards._\n\n## Cut (and why)\n- 'Get a haircut' — not Top-3 material.\n- 'Figure out if we need a designer' — needs more thinking; add to a 'pending decisions' doc, don't surface as priority.\n\n## Follow-up questions\n- The billing bug on Tuesday — is there a debt-tracker for those, or are they ad-hoc?\n- Investor outreach has slipped 2 weeks in a row — is the bottleneck pipeline (who to contact) or time (when to contact)?",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best balance — surfaces patterns without being preachy. Good at cutting the Top-N ruthlessly."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Deeper pattern recognition; preferred when feeding 4+ weeks of history."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Slightly more verbose; lower the word cap if outputs feel bloated."},
            {"model": "llama-3.3-70b", "compatibility": "good", "notes": "Solid for self-hosted; less nuanced on cutting decisions — expect to re-prompt 'cut harder'."},
        ],
        "variations": [
            {"label": "Daily-review mode", "description": "Shorter, end-of-day version.", "prompt_snippet": "Override sections: just '✅ shipped', '🚧 stuck', '🎯 tomorrow's top 1'. Cap output at 100 words."},
            {"label": "Team weekly review", "description": "Roll up multiple individual reviews into a team view.", "prompt_snippet": "INPUTS change: `team_reviews` = list of {name, review_text}. Output adds a 'Team patterns' section showing blockers/lessons that appeared in 2+ reviews."},
            {"label": "OKR-aligned mode", "description": "Force alignment to quarterly OKRs.", "prompt_snippet": "Pass `quarterly_okrs` as input. Each win/blocker/priority must reference which OKR it serves. If something doesn't map to an OKR, flag it in a 'Off-OKR work' section."},
            {"label": "No-coach mode", "description": "Strip the Socratic questions for users who just want the structured output.", "prompt_snippet": "Remove the 'TONE' line and the 'Follow-up questions' section entirely."},
        ],
        "failure_modes": [
            {"symptom": "Generates 8 'wins' from a dump that had 2 real wins — pads the section to look balanced", "fix": "cap explicitly: 'List 0-5 wins. If there were fewer, list fewer.'"},
            {"symptom": "Treats every meeting as a blocker when the user vented about meeting-load", "fix": "instruct 'A meeting is a blocker only if it stopped a deliverable, not if it was just tiring.'"},
            {"symptom": "Repeats lessons learned across weeks (because the underlying pattern hasn't changed). Useful but feels stale", "fix": "when previous_review is provided, prefer to escalate 'this lesson is recurring — what blocks acting on it?' over restating"},
            {"symptom": "Cuts items the user really cared about", "fix": "always show the 'Cut' section with reasons; the user can override"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b", "anthropic==0.39.0", "openai==1.50.0"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["priority-matrix-eisenhower", "standup-update-formatter", "oneonone-agenda-builder", "meeting-decision-recorder"],
        "related_tool_slugs": ["notion", "obsidian", "linear", "things"],
        "related_glossary_slugs": ["gtd", "okrs", "weekly-review"],
        "faq": [
            {"question": "How long should my brain-dump be?", "answer": "200-1500 words. Less and there's no signal; more and you're avoiding the actual review work."},
            {"question": "Should I run this myself or have my assistant run it?", "answer": "You. The dump is private and the act of dumping IS the review — outsourcing it skips the value."},
            {"question": "What if I had a bad week and don't want to look at it?", "answer": "The prompt will still surface 2-3 wins from a bad week if any exist. If literally nothing went well, the output's 'Lessons' section is your gold — that's where the leverage is."},
        ],
        "license": "CC-BY-4.0",
        "attribution": "OSS AI Hub Prompt Library",
        "status": "approved",
        "submitter_email": "hub@ossaihub.com",
        "submitter_name": "OSS AI Hub",
        "meta_title": "Weekly Review Coach Prompt — Wins, Blockers, Top 3",
        "meta_description": "Turn a weekly brain-dump into a clean, scannable review doc. Surfaces wins, blockers, lessons, and next week's top 3 with carry-over tracking.",
    },

    {
        "slug": "priority-matrix-eisenhower",
        "title": "Eisenhower Matrix Sorter (urgent × important)",
        "category": "productivity",
        "tldr": "Sort a messy task list into the 4-quadrant urgent × important matrix with reasoning per task. Flags tasks that are actually masking other tasks.",
        "tags": ["prioritization", "eisenhower-matrix", "task-management"],
        "best_for_tags": ["prioritization", "task-triage", "decision-support"],
        "difficulty_tier": "beginner",
        "featured": False,
        "full_prompt": (
            "You are a sharp executive coach helping the user prioritize a task list using the Eisenhower matrix (urgent × important). Default behavior: be skeptical of urgency — most things feel urgent but aren't.\n\n"
            "INPUTS:\n"
            "- tasks: list of task descriptions (one per line, or as a JSON array)\n"
            "- context (optional): role / current goals / known deadlines\n\n"
            "PROCEDURE for each task:\n"
            "1. IMPORTANCE: ask 'If I never did this, what's the worst outcome 30 days from now?' — if the answer is 'real consequence' → important. If 'meh' → not important.\n"
            "2. URGENCY: ask 'Does this have an external hard deadline within 72 hours?' — true → urgent. False → not urgent. (Self-imposed deadlines don't count.)\n"
            "3. MASKING CHECK: ask 'Is this task a stand-in for a bigger task the user is avoiding?' — if yes, note it.\n\n"
            "OUTPUT (markdown):\n\n"
            "## Q1 — Urgent + Important (DO NOW)\n"
            "- Each: task + 1-sentence why it's both.\n\n"
            "## Q2 — Important + Not Urgent (SCHEDULE)\n"
            "- This is the highest-leverage quadrant. If it's empty, that's a problem — flag it.\n\n"
            "## Q3 — Urgent + Not Important (DELEGATE / BATCH)\n"
            "- Each: task + suggested handling (delegate to whom, or batch into a 30-min block).\n\n"
            "## Q4 — Not Urgent + Not Important (DROP)\n"
            "- Each: task + 1-line 'why this should be dropped' so the user can argue back if they disagree.\n\n"
            "## 🪞 Masking patterns\n"
            "- Tasks that are stand-ins for bigger work the user is avoiding. 1-2 sentences each.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "tasks", "type": "list[str]", "description": "Tasks to sort", "required": True, "example": "['Reply to 47 emails', 'Q4 planning offsite prep', 'Update LinkedIn profile', 'Call mom', 'Fix the deploy script', 'Review hiring scorecards']"},
            {"name": "context", "type": "string", "description": "User's role + current goals + active deadlines", "required": False, "example": "Engineering manager, 8-person team. Q4 OKRs: ship search v2, hire 2 mid-level. Q4 review with VP in 2 weeks."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "## Q1 — Urgent + Important\n- **Review hiring scorecards** — 2 interviews tomorrow, real consequence if you go in cold.\n\n## Q2 — Important + Not Urgent\n- **Q4 planning offsite prep** — 2 weeks out but the offsite is the leverage point for the whole quarter.\n- **Fix the deploy script** — no deadline, but it's slowing every deploy by 10 min × 5 deploys/week × 8 people.\n\n## Q3 — Urgent + Not Important\n- **Reply to 47 emails** — batch into a 45-min block; delegate any that should go to your EA.\n\n## Q4 — Drop\n- **Update LinkedIn profile** — not driving any current outcome.\n\n## 🪞 Masking patterns\n- 'Reply to 47 emails' is masking the fact that you've been avoiding the hiring scorecard review (which felt heavier). Sorting email feels like work.",
        },
        "use_cases": [
            {"scenario": "Monday morning kickstart", "example": "Dump your inbox + to-do app + post-its into the prompt; get a clean Q1-Q4 plan for the week."},
            {"scenario": "Pre-1:1 prep with a direct report", "example": "Have your report dump their list before the 1:1; the matrix becomes the conversation guide."},
            {"scenario": "End-of-quarter cleanup", "example": "Sort your 'someday/maybe' list; everything that's still in Q4 after 90 days gets archived."},
            {"scenario": "Calendar audit", "example": "Treat next week's recurring meetings as 'tasks'. The Q4 column reveals meetings you should drop."},
        ],
        "when_not_to_use": "Don't use for genuinely complex projects with many sub-tasks — the matrix flattens hierarchy. Break the project into sub-tasks first. Also useless if your context is incomplete (e.g., the model doesn't know which deadlines are real).",
        "few_shot_examples": [
            {
                "input": "tasks: ['Write blog post on new feature', 'Update team OKRs (overdue 2 weeks)', 'Reply to investor intro email (8 hours old)', 'Schedule physical exam', 'Quarterly performance reviews (due in 2 days)', 'Refactor old onboarding code', 'Slack engineering channel about deploy etiquette']\ncontext: 'CTO at Series-A startup, 12 eng team, fundraising in 2 months'",
                "output": "## Q1 — Urgent + Important\n- **Quarterly performance reviews** — hard deadline 2 days, direct impact on retention.\n- **Reply to investor intro email** — fundraising window matters; 24h response time is the norm.\n\n## Q2 — Important + Not Urgent\n- **Update team OKRs** — overdue 2 weeks; the longer it slips the more team drifts.\n- **Write blog post on new feature** — marketing leverage for the fundraise.\n\n## Q3 — Urgent + Not Important\n- **Slack about deploy etiquette** — feels urgent but it's a 5-min message; batch into your next Slack-block.\n\n## Q4 — Drop\n- **Refactor old onboarding code** — no current goal points to it. Re-evaluate after fundraise.\n- **Schedule physical exam** — important for you personally but not work-prioritization scope; move to personal list.\n\n## 🪞 Masking patterns\n- The blog post is sitting in Q2 but it's been there 3 weeks. That's a Q2 → Q1 escalation signal — you've been avoiding it. Block 90 minutes Monday morning before email.",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best for the urgency-skepticism — won't auto-mark everything urgent."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Slightly more lenient on urgency; counterbalance by adding 'Be skeptical of urgency' to context."},
            {"model": "claude-haiku-4-5", "compatibility": "good", "notes": "Cheap + fast for repeated daily sorts."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; masking-pattern detection is weaker."},
        ],
        "variations": [
            {"label": "ICE/RICE scoring instead", "description": "Use Impact × Confidence × Ease scoring for product prioritization.", "prompt_snippet": "Replace the urgent×important matrix with ICE scoring (each task: impact 1-10, confidence 1-10, ease 1-10, score=I×C×E). Output sorted list with reasoning per axis."},
            {"label": "Time-budgeted mode", "description": "User has N hours this week; prompt fills time-budget by quadrant.", "prompt_snippet": "Add input `hours_available` (e.g., 30). Output a time-budget: 'Q1: 8h, Q2: 14h, Q3: 6h batched, Q4: 0h.' Justify the Q2 allocation if it's <40% of total."},
            {"label": "No-coach mode", "description": "Strip the masking-patterns section.", "prompt_snippet": "Remove the 'MASKING CHECK' step from PROCEDURE and the '🪞 Masking patterns' output section. Useful when the user wants pure sorting."},
        ],
        "failure_modes": [
            {"symptom": "Marks everything Q1 when context lacks deadlines", "fix": "provide context with at least one explicit hard deadline so the model has an anchor"},
            {"symptom": "Drops genuinely important Q4-looking items (e.g., personal health)", "fix": "instruct 'When in doubt, move to Q2 not Q4.'"},
            {"symptom": "Masking-pattern detection produces false positives that feel preachy", "fix": "cap masking observations at 2 per run; only surface if the pattern is concrete"},
            {"symptom": "Treats self-imposed deadlines as urgent", "fix": "explicit rule in PROCEDURE — 'self-imposed deadlines don't count for urgency'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-haiku-4-5", "llama-3.3-70b", "anthropic==0.39.0", "openai==1.50.0"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["weekly-review-coach", "standup-update-formatter", "oneonone-agenda-builder"],
        "related_tool_slugs": ["todoist", "things", "linear", "notion"],
        "related_glossary_slugs": ["prioritization", "time-management", "eisenhower-matrix"],
        "faq": [
            {"question": "What if Q2 is huge?", "answer": "That's actually the point of the matrix — Q2 is the highest-leverage quadrant. If Q2 has 10 items, you need to schedule blocks, not delegate them away."},
            {"question": "How often should I re-sort?", "answer": "Weekly for full lists; daily for 'today's tasks' which is just a 5-item version. Re-sorting more often than daily is a procrastination signal."},
            {"question": "What if I disagree with the model's sorting?", "answer": "Override it — the model has no skin in your day. The value is the questions it forces you to ask, not the answers."},
        ],
        "license": "CC-BY-4.0",
        "attribution": "OSS AI Hub Prompt Library",
        "status": "approved",
        "submitter_email": "hub@ossaihub.com",
        "submitter_name": "OSS AI Hub",
        "meta_title": "Eisenhower Matrix Prompt — Sort Tasks by Urgency × Importance",
        "meta_description": "Sort your task list into 4 quadrants with reasoning per task. Flags 'masking' tasks (busy-work standing in for harder work). Skeptical of urgency by default.",
    },

    {
        "slug": "standup-update-formatter",
        "title": "Daily Standup Update Formatter (Yesterday / Today / Blockers)",
        "category": "productivity",
        "tldr": "Convert raw EOD/EOM notes into a clean, 90-second standup update. Cuts filler, surfaces real blockers, and matches your team's preferred format.",
        "tags": ["standup", "team-comms", "format"],
        "best_for_tags": ["standup", "async-update", "team-communication"],
        "difficulty_tier": "beginner",
        "featured": False,
        "full_prompt": (
            "You write standup updates that the rest of the team will actually read. Default format: Yesterday / Today / Blockers. 3 bullets per section, hard cap.\n\n"
            "INPUTS:\n"
            "- raw_notes: free-form notes about what you did + plan to do + what's stuck\n"
            "- team_format (optional): override the default Y/T/B with your team's variant (e.g., 'Shipped / Working on / Need help with')\n"
            "- audience_size (optional): if >10, be tighter; if <5, can include more nuance\n\n"
            "RULES:\n"
            "- 3 bullets per section, hard cap. If you have 5 things, pick the 3 that matter to the audience.\n"
            "- Each bullet 1 line. If you can't say it in 1 line, you're conflating two things.\n"
            "- 'Blockers' means OTHERS need to act. If only you can unblock you, it goes in 'Today' as a task.\n"
            "- Don't pad. If you have 0 blockers, say '- none.' Don't invent friction.\n"
            "- No filler phrases ('just wanted to update', 'making progress on', 'getting ready to').\n\n"
            "OUTPUT FORMAT:\n\n"
            "**Yesterday**\n"
            "- bullet\n"
            "- bullet\n"
            "- bullet\n\n"
            "**Today**\n"
            "- bullet\n"
            "- bullet\n"
            "- bullet\n\n"
            "**Blockers**\n"
            "- bullet (with @ mention of who needs to act if known)\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "raw_notes", "type": "string", "description": "Free-form notes about your day", "required": True, "example": "Finished the auth PR review for Alice. Wrote the design doc for caching, sent to team. Tried to debug the flaky test for an hour, no progress. Today: continue debugging, also have the 1:1 with Bob. Need DB credentials for staging, asked Sam yesterday no response."},
            {"name": "team_format", "type": "string", "description": "Override the Y/T/B section names", "required": False, "example": "Shipped / Working / Need help"},
            {"name": "audience_size", "type": "integer", "description": "Team size receiving the update", "required": False, "example": "8"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "**Yesterday**\n- Reviewed Alice's auth PR — merged with 2 minor comments.\n- Caching design doc sent to team for async review (link).\n- Spent 1h on the flaky billing test; no repro yet.\n\n**Today**\n- Continue the flaky test investigation (instrumenting CI).\n- 1:1 with Bob (career-conv slot).\n- Review the 2 caching-doc comments if they come in.\n\n**Blockers**\n- @sam — still need staging DB creds (asked Tuesday).",
        },
        "use_cases": [
            {"scenario": "Async Slack standup channel", "example": "Engineer pastes raw notes; bot formats and posts to #standup. Whole team reads in 90 seconds."},
            {"scenario": "Weekly status email to manager", "example": "Use this prompt at end of week; merge 5 daily standups into a weekly summary by feeding all 5 in."},
            {"scenario": "Onboarding template", "example": "New hires often over-share or under-share in standup. This prompt is their starting template for the first 30 days."},
            {"scenario": "Cross-timezone handoffs", "example": "EOD update in the prompt; teammate in the other timezone reads it as their morning context."},
        ],
        "when_not_to_use": "Don't use for incident reports or post-mortems — those need a different structure. Also skip when standup is verbal (the polish disappears in speech anyway).",
        "few_shot_examples": [
            {
                "input": "raw_notes: 'spent half the day in a meeting hell, kicked off the design doc but didnt finish. fought a typescript build issue for an hour, fixed it. have the eng all-hands today + need to finish the design doc + also need someone to review my PR from monday'",
                "output": "**Yesterday**\n- Drafted the search-rewrite design doc (60% done).\n- Fixed a typescript build error blocking the auth branch.\n- (Most of the day was meeting-heavy — light on shipped output.)\n\n**Today**\n- Finish the design doc, send for review by EOD.\n- Eng all-hands at 2pm.\n\n**Blockers**\n- Need a reviewer on my Monday PR (link).",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at cutting filler without losing signal."},
            {"model": "claude-haiku-4-5", "compatibility": "excellent", "notes": "Recommended for production — fast, cheap, format-stable."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Tends to over-format with sub-bullets; instruct 'no sub-bullets' explicitly."},
            {"model": "llama-3.3-70b", "compatibility": "good", "notes": "Workable for self-hosted teams."},
        ],
        "variations": [
            {"label": "Weekly version", "description": "Roll up 5 days into a weekly update.", "prompt_snippet": "INPUTS: instead of daily, take 5 daily_notes. OUTPUT sections: 'This week: shipped' / 'Next week: focus' / 'Open blockers'. Cap 5 bullets per section."},
            {"label": "Slack-emoji mode", "description": "Add status emojis your team uses.", "prompt_snippet": "Prefix bullets with team-specific emojis: ✅ shipped, 🚧 in progress, 🛑 blocked. Be consistent within a section."},
            {"label": "Manager-summary mode", "description": "For when you're consolidating 8 reports' standups into 1.", "prompt_snippet": "INPUTS: list of {person, raw_notes}. OUTPUT: aggregated team standup with 'Wins (across team)', 'In-flight', 'Cross-team blockers' sections; each bullet credits the relevant person."},
        ],
        "failure_modes": [
            {"symptom": "Includes filler bullets to hit '3 bullets per section'", "fix": "hard rule 'less than 3 is fine, padding is forbidden.'"},
            {"symptom": "Treats personal blockers as team blockers", "fix": "definition in RULES — 'blocker = someone else must act.'"},
            {"symptom": "Sub-bullets explode the readability", "fix": "explicit 'no sub-bullets' rule"},
            {"symptom": "Over-honest dumps (e.g., 'I procrastinated today')", "fix": "instruct 'Frame the day in terms of outcomes, not feelings.'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-haiku-4-5", "gpt-5", "llama-3.3-70b", "anthropic==0.39.0", "openai==1.50.0"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["weekly-review-coach", "priority-matrix-eisenhower", "oneonone-agenda-builder"],
        "related_tool_slugs": ["slack", "notion", "linear"],
        "related_glossary_slugs": ["async-communication", "standup", "team-coordination"],
        "faq": [
            {"question": "How long should my raw notes be?", "answer": "30 seconds of typing. If you're writing 5 paragraphs, you're using the wrong tool."},
            {"question": "Can I run this on someone else's notes?", "answer": "Yes, but the result will read in their voice; if you're consolidating reports' standups, use the Manager-summary variant explicitly."},
            {"question": "What if my team uses a non-standard format?", "answer": "Pass it as `team_format`. The prompt adapts the section names and rules accordingly."},
        ],
        "license": "CC-BY-4.0",
        "attribution": "OSS AI Hub Prompt Library",
        "status": "approved",
        "submitter_email": "hub@ossaihub.com",
        "submitter_name": "OSS AI Hub",
        "meta_title": "Daily Standup Update Formatter — 90-Second Y/T/B",
        "meta_description": "Convert raw EOD notes into a clean standup update. 3 bullets per section, no filler, real blockers only, async-friendly format.",
    },
]
