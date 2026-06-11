"""Data-extraction + structured-output + RAG/agent prompts — June batch."""

RECORDS = [
    {
        "slug": "contract-key-terms-extractor",
        "title": "Contract Key-Terms Extractor",
        "tldr": "Extract deal terms from a contract — parties, dates, renewal, payment, liability cap, termination, governing law — each with a verbatim quote, clause ref, and confidence; flags missing clauses, never infers.",
        "category": "data-extraction",
        "tags": ["contracts", "extraction", "legal-ops", "structured-output", "grounding"],
        "best_for_tags": ["legal-ops", "procurement", "founders"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Vendor MSA review", "example": "Pull liability cap, auto-renewal, and termination-for-convenience from a 30-page SaaS MSA before signing."},
            {"scenario": "Contract repository back-fill", "example": "Extract the same 12 fields across 200 legacy agreements into one table for a CLM migration."},
            {"scenario": "Renewal triage", "example": "Find auto-renewal + notice-window clauses so you flag contracts that lapse if not actioned in 30 days."},
            {"scenario": "Diligence data room", "example": "Summarize assignment / change-of-control terms across a target's customer contracts for an acquisition."},
        ],
        "when_not_to_use": "This is an extraction aid, not legal advice — do not use it to decide whether to sign, to assess enforceability, or in place of a qualified attorney. Skip on scanned contracts until OCR'd to clean text, and skip when the governing language is one the model handles poorly.",
        "full_prompt": """You are a contract analyst. Extract a fixed set of deal terms from the contract below. Every value must be grounded in the text — quote it, cite the clause, and rate confidence. You do not give legal advice and you never infer terms that are not written.

INPUT
- Contract text (full agreement, including exhibits if provided): {contract_text}
- Term checklist (the fields to extract; if blank, use the DEFAULT set): {term_checklist}

DEFAULT term checklist (use when {term_checklist} is empty):
parties, effective_date, initial_term, renewal_terms, auto_renewal, notice_period, payment_terms, fees, late_fees, liability_cap, indemnification, termination_for_cause, termination_for_convenience, governing_law, venue, assignment, change_of_control, confidentiality_term, warranty, sla

OUTPUT — return ONE JSON object, no prose outside it:

{
  "document_label": "<short name if present, else 'untitled'>",
  "terms": [
    {
      "field": "liability_cap",
      "status": "found | not_found | ambiguous",
      "value": "<normalized value, e.g. 'Fees paid in trailing 12 months'; null if not_found>",
      "source_quote": "<verbatim span copied from the contract; null if not_found>",
      "clause_ref": "<Section 9.2 / Exhibit B / page label; null if unknown>",
      "confidence": 0.0,
      "note": "<only when ambiguous or status needs explaining; else ''>"
    }
  ],
  "missing_standard_clauses": ["<checklist field with status not_found>"],
  "redlines_worth_a_human_look": ["<term that is unusual, one-sided, or carries a non-obvious risk — describe, do NOT advise>"],
  "extraction_caveats": ["<e.g. 'defined terms resolved from Section 1', 'two payment schedules — listed both'>"]
}

RULES FOR EACH FIELD
- status="found" REQUIRES a non-null source_quote copied verbatim. No quote -> status cannot be "found".
- Resolve defined terms (e.g. "Provider", "the Term") against the definitions section before reporting a value.
- If two clauses conflict or a term appears in multiple places, status="ambiguous", list both in note, and lower confidence.
- value is NORMALIZED (a liability cap of "the greater of $50,000 or fees paid" stays faithful but readable); source_quote stays VERBATIM.
- confidence: 0.9+ explicit single clause; 0.6-0.8 inferred from defined terms or split across clauses; <0.6 ambiguous.

CRITICAL RULES
- This is extraction, NOT legal advice. Never state whether a term is enforceable, fair, or safe to sign. "redlines_worth_a_human_look" only DESCRIBES; it does not recommend.
- NEVER invent a value. If the contract is silent, status="not_found", value=null, and the field goes in missing_standard_clauses.
- Do not paraphrase inside source_quote — copy the exact words, including any typos.
- Output valid JSON only. No markdown fences, no commentary before or after.

CONTRACT
{contract_text}

CHECKLIST
{term_checklist}

Begin.""",
        "input_variables": [
            {"name": "contract_text", "type": "string", "description": "The full contract text, including exhibits/schedules if available. Must be machine-readable text (OCR scanned PDFs first).", "required": True, "example": "MASTER SERVICES AGREEMENT. This Agreement is entered into as of March 1, 2026 ('Effective Date') by and between Acme Inc. ('Provider') and BetaCo LLC ('Customer'). 1. DEFINITIONS... 4. FEES. Customer shall pay $12,000/month... 9. LIMITATION OF LIABILITY. In no event shall Provider's aggregate liability exceed the fees paid in the trailing twelve (12) months..."},
            {"name": "term_checklist", "type": "string", "description": "Comma-separated list of fields to extract. Leave empty to use the prompt's default 20-field checklist.", "required": False, "example": "parties, effective_date, liability_cap, auto_renewal, notice_period, termination_for_convenience, governing_law"},
        ],
        "expected_output": {
            "format": "json",
            "sample": "{\"document_label\":\"Master Services Agreement\",\"terms\":[{\"field\":\"liability_cap\",\"status\":\"found\",\"value\":\"Provider aggregate liability capped at fees paid in trailing 12 months\",\"source_quote\":\"In no event shall Provider's aggregate liability exceed the fees paid in the trailing twelve (12) months\",\"clause_ref\":\"Section 9\",\"confidence\":0.95,\"note\":\"\"},{\"field\":\"auto_renewal\",\"status\":\"not_found\",\"value\":null,\"source_quote\":null,\"clause_ref\":null,\"confidence\":0.0,\"note\":\"\"}],\"missing_standard_clauses\":[\"auto_renewal\",\"sla\"],\"redlines_worth_a_human_look\":[\"Mutual indemnification is absent; only Customer indemnifies Provider\"],\"extraction_caveats\":[\"'Provider' resolved from Section 1\"]}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Most disciplined about marking 'not_found' instead of guessing, and copies source_quote verbatim including odd wording. Reliable JSON."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best at resolving defined terms across long agreements and spotting conflicting clauses for the 'ambiguous' status."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong extraction; occasionally paraphrases inside source_quote — re-pin the verbatim rule. Use JSON/structured-output mode."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable on short contracts; tends to drift to advice in 'redlines' and may infer silent terms — keep the no-advice + not_found rules loud and chunk long docs."},
        ],
        "variations": [
            {"label": "Single-clause focus", "description": "Pull one clause family with full context.", "prompt_snippet": "Ignore the checklist. Extract ONLY the {target_clause} family (every related sub-clause, definition, exception, and cross-reference). Return the same per-term JSON for each fragment found."},
            {"label": "Compare two contracts", "description": "Diff the same terms across two agreements.", "prompt_snippet": "You are given CONTRACT_A and CONTRACT_B. Extract the checklist for both, then add a 'deltas' array naming each field where the terms materially differ, with both source_quotes. Still no advice."},
            {"label": "CSV row mode", "description": "One flat row for a spreadsheet import.", "prompt_snippet": "After the JSON, also emit a single CSV row with columns = checklist fields, values = the normalized value or empty string for not_found. No quotes, no confidence — that row feeds a repository import."},
        ],
        "failure_modes": [
            {"symptom": "Invents a plausible value for a term the contract never states.", "fix": "Re-pin: 'status=found REQUIRES a verbatim source_quote. Silent term -> not_found + value=null + add to missing_standard_clauses.'"},
            {"symptom": "Paraphrases the clause inside source_quote.", "fix": "Add: 'source_quote is copied character-for-character, including typos. value is the place to normalize, not source_quote.'"},
            {"symptom": "Slips into legal advice ('this cap is unfavorable, renegotiate').", "fix": "Re-pin the CRITICAL RULE: 'redlines_worth_a_human_look DESCRIBES only. Never say enforceable / fair / safe / should.'"},
            {"symptom": "Wraps the JSON in markdown fences or adds a preamble.", "fix": "End with: 'Output valid JSON only — no ``` fences, no text before or after the object.'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-06-10"},
        "related_prompt_slugs": ["structured-extraction-from-docs", "extraction-with-confidence-per-field", "rag-source-citation-enforcer"],
        "related_glossary_slugs": ["structured-output", "grounding", "hallucination", "attribution-citation"],
        "related_tool_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is this a substitute for a lawyer reviewing the contract?", "answer": "No. It is an extraction and triage aid. It surfaces where terms are, quotes them, and flags gaps — it does not assess enforceability, fairness, or whether to sign. Treat 'redlines_worth_a_human_look' as a reading list for a qualified attorney, not as advice."},
            {"question": "How do I trust the values without re-reading the whole contract?", "answer": "Every 'found' value carries a verbatim source_quote and a clause_ref, so you spot-check the quote against the named section rather than re-reading. Anything below ~0.8 confidence or marked 'ambiguous' is where a human should look first."},
            {"question": "What about scanned PDFs?", "answer": "Run OCR to clean text first. The verbatim-quote rule depends on accurate input characters; OCR noise produces garbled quotes and lower confidence. The prompt cannot fix bad source text."},
            {"question": "Can it handle defined terms like 'Provider' or 'the Term'?", "answer": "Yes — it resolves defined terms against the definitions section before reporting a value, and notes that resolution in extraction_caveats. If a definition is missing or circular, it lowers confidence and marks the field ambiguous."},
        ],
        "meta_title": "Contract Key-Terms Extractor — Data Extraction Prompt",
        "meta_description": "Extract deal terms from contracts with verbatim quotes, clause refs, and confidence. Flags missing clauses, never infers. Extraction aid, not legal advice.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "resume-to-structured-profile",
        "title": "Resume to Structured Candidate Profile",
        "tldr": "Turn a resume/CV into a clean JSON profile: roles with ISO dates and computed tenure, deduped skills, education, flagged gaps, and a seniority estimate with reasoning — only job-relevant facts, no identity signals.",
        "category": "data-extraction",
        "tags": ["recruiting", "extraction", "hr-tech", "structured-output", "bias-guardrail"],
        "best_for_tags": ["recruiters", "hr-tech", "hiring-managers"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "ATS intake normalization", "example": "Convert 500 inbound resumes into a uniform JSON schema for filtering by skill and tenure."},
            {"scenario": "Shortlist prep", "example": "Pull roles, total relevant experience, and skill match for a backend role from 40 CVs."},
            {"scenario": "Gap-aware screening", "example": "Surface employment gaps neutrally so a recruiter can ask about them rather than silently down-rank."},
            {"scenario": "Skills inventory", "example": "Build a deduped, canonicalized skills table across a candidate pool to see coverage."},
        ],
        "when_not_to_use": "Do not use the seniority estimate or any output as an automated reject/accept decision — it is a structuring aid for a human reviewer. Skip when local hiring law restricts algorithmic screening, and never feed it to rank candidates on protected attributes.",
        "full_prompt": """You are a resume parser for a hiring team. Convert the resume below into a structured candidate profile. Extract only job-relevant facts. Ignore and never record name-derived ethnicity, gender, age, photo, marital status, or other identity signals.

INPUT
- Resume / CV text: {resume_text}
- Target role being screened for: {target_role}

OUTPUT — return ONE JSON object, no prose outside it:

{
  "contact": { "email": "<or null>", "phone": "<or null>", "location_city_region": "<or null>", "links": ["<portfolio/github/linkedin urls>"] },
  "roles": [
    {
      "title": "<as written>",
      "company": "<as written>",
      "start": "YYYY-MM | YYYY | null",
      "end": "YYYY-MM | YYYY | present | null",
      "months": 0,
      "relevant_to_target": "high | medium | low",
      "highlights": ["<verbatim or lightly trimmed bullet>"]
    }
  ],
  "total_experience_months": 0,
  "relevant_experience_months": 0,
  "skills": [ { "skill": "<canonical name>", "evidence": "role/section it came from" } ],
  "education": [ { "credential": "", "institution": "", "year": "YYYY | null" } ],
  "gaps": [ { "from": "YYYY-MM", "to": "YYYY-MM", "months": 0, "note": "neutral description, no inference of cause" } ],
  "seniority_estimate": { "level": "junior | mid | senior | lead | unclear", "reasoning": "<2-3 sentences citing tenure, scope, leadership signals>" },
  "extraction_caveats": ["<e.g. 'dates given as years only', 'two overlapping roles kept separate'>"]
}

NORMALIZATION RULES
- Dates -> ISO. "Mar 2022" -> "2022-03"; a year-only date stays "2022" and is noted in caveats.
- months = full months between start and end (end="present" -> count to today's month). Overlapping roles are NOT double-counted in total_experience_months.
- Skills are CANONICALIZED and DEDUPED: "ReactJS", "React.js", "React" -> one entry "React". "JS" -> "JavaScript". Keep evidence pointing to where it appeared.
- relevant_to_target and relevant_experience_months are judged against {target_role}, not against general prestige.
- gaps: any span > 3 months between roles. Describe the span only; never infer the reason (no "likely caregiving/unemployment").

CRITICAL RULES
- BIAS GUARDRAIL: extract only job-relevant facts. Do not record or reason from name, gender, age, nationality, photo, or marital status. If the resume states age/DOB, omit it and note 'identity fields omitted by policy' in caveats.
- The seniority_estimate is an ESTIMATE WITH REASONING for a human, not a decision. Never output a hire/reject recommendation.
- Never invent skills, employers, or dates. Unknown -> null and a caveat.
- Output valid JSON only — no markdown fences, no text outside the object.

RESUME
{resume_text}

TARGET ROLE
{target_role}

Begin.""",
        "input_variables": [
            {"name": "resume_text", "type": "string", "description": "Plain-text resume or CV. Strip out photos/headers; OCR if it came from a scanned PDF.", "required": True, "example": "Jordan Lee — jordan@email.com — github.com/jlee\\nSenior Backend Engineer, Northwind (Mar 2022 - present): led migration to event-driven services, mentored 3 engineers.\\nBackend Engineer, Acme (Jun 2019 - Feb 2022): built billing API in Python/Django.\\nB.S. Computer Science, State University, 2019. Skills: Python, Django, React.js, PostgreSQL, AWS."},
            {"name": "target_role", "type": "string", "description": "The role being screened for, used to judge relevance and seniority. Include level + core stack if known.", "required": True, "example": "Senior Backend Engineer — Python services, distributed systems, AWS; team-lead potential"},
        ],
        "expected_output": {
            "format": "json",
            "sample": "{\"contact\":{\"email\":\"jordan@email.com\",\"phone\":null,\"location_city_region\":null,\"links\":[\"github.com/jlee\"]},\"roles\":[{\"title\":\"Senior Backend Engineer\",\"company\":\"Northwind\",\"start\":\"2022-03\",\"end\":\"present\",\"months\":51,\"relevant_to_target\":\"high\",\"highlights\":[\"led migration to event-driven services\",\"mentored 3 engineers\"]}],\"total_experience_months\":84,\"relevant_experience_months\":84,\"skills\":[{\"skill\":\"Python\",\"evidence\":\"Acme + Northwind roles\"},{\"skill\":\"React\",\"evidence\":\"skills line\"}],\"education\":[{\"credential\":\"B.S. Computer Science\",\"institution\":\"State University\",\"year\":\"2019\"}],\"gaps\":[],\"seniority_estimate\":{\"level\":\"senior\",\"reasoning\":\"7 years, ownership of a service migration, and mentoring three engineers indicate senior with lead trajectory.\"},\"extraction_caveats\":[\"identity fields omitted by policy\"]}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at neutral gap notes and skill canonicalization without inventing skills. Honors the identity-omission rule consistently."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Strongest seniority reasoning tied to concrete scope/tenure signals; handles overlapping roles without double-counting."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Accurate dates and arithmetic; can inflate seniority on buzzwords — re-pin 'judge scope, not prestige'. Use structured-output mode."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Fine on simple resumes; weaker at deduping skill variants and may infer gap causes — keep the canonicalization and neutral-gap rules loud."},
        ],
        "variations": [
            {"label": "Skills-match only", "description": "Score against a required-skills list.", "prompt_snippet": "After the profile, add a 'match' object scoring each skill in {required_skills} as present/absent with evidence, plus a coverage percentage. Still no hire/reject verdict."},
            {"label": "Anonymized output", "description": "Blind-screening mode.", "prompt_snippet": "Replace contact with a generated candidate_id and drop all links that reveal identity. Output is for blind review; only role/skill/education facts remain."},
            {"label": "Table mode", "description": "Flat rows for a spreadsheet.", "prompt_snippet": "Also emit a markdown table: one row per role (title, company, start, end, months, relevance) and a one-row summary (total months, relevant months, seniority)."},
        ],
        "failure_modes": [
            {"symptom": "Double-counts overlapping roles, inflating total experience.", "fix": "Re-pin: 'overlapping date ranges are merged for total_experience_months; show each role separately but do not sum overlapping months.'"},
            {"symptom": "Lists React, ReactJS, and React.js as three skills.", "fix": "Add a canonicalization map to the prompt: 'collapse variants to one canonical name; keep a single entry with combined evidence.'"},
            {"symptom": "Infers a reason for an employment gap.", "fix": "Re-pin: 'gaps describe the span only. Never state or guess a cause.'"},
            {"symptom": "Outputs a hire/reject recommendation.", "fix": "Hard rule: 'seniority_estimate is an estimate with reasoning for a human. No recommendation, no ranking against other candidates.'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-06-10"},
        "related_prompt_slugs": ["structured-extraction-from-docs", "json-output-strict", "extraction-with-confidence-per-field"],
        "related_glossary_slugs": ["structured-output", "named-entity-recognition", "hallucination"],
        "related_tool_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Does this make hiring decisions?", "answer": "No. It structures a resume and gives a seniority estimate with reasoning for a human reviewer. It deliberately produces no hire/reject verdict and no ranking on protected attributes. Using it to auto-screen may also conflict with local hiring law — keep a human in the loop."},
            {"question": "How does the bias guardrail actually work?", "answer": "The prompt instructs the model to extract only job-relevant facts and to omit name-derived ethnicity/gender, age, photo, and marital status, noting the omission in caveats. It is a mitigation, not a guarantee — review outputs and pair with your own fairness checks."},
            {"question": "How are employment gaps handled?", "answer": "Any inter-role span over three months is listed with from/to/months and a neutral description. The prompt explicitly forbids guessing the cause, so a recruiter can ask about it rather than silently penalize the candidate."},
            {"question": "Why canonicalize skills?", "answer": "So 'React', 'React.js', and 'ReactJS' don't fragment your filters. Each canonical skill keeps an evidence pointer to where it appeared, so you can verify it wasn't padded into a skills list without backing experience."},
        ],
        "meta_title": "Resume to Structured Candidate Profile — Extraction Prompt",
        "meta_description": "Parse resumes into JSON: ISO dates, computed tenure, deduped skills, neutral gap flags, seniority with reasoning. Bias-guarded, human-in-the-loop.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "email-action-item-extractor",
        "title": "Email Thread to Action Items",
        "tldr": "Read an email thread and extract action items — task, owner resolved from signatures, due date resolved against today, blocking flag, source quote — plus decisions and open questions, with 'unassigned' when unclear.",
        "category": "data-extraction",
        "tags": ["email", "productivity", "action-items", "extraction", "structured-output"],
        "best_for_tags": ["operators", "project-managers", "founders"],
        "difficulty_tier": "beginner",
        "featured": False,
        "use_cases": [
            {"scenario": "Inbox to task list", "example": "Turn a 12-message vendor thread into a checklist of who owes what by when."},
            {"scenario": "Meeting follow-up email", "example": "Extract the commitments and decisions from a recap email into a tracker."},
            {"scenario": "Handoff capture", "example": "Pull every 'can you...' and 'I'll...' from a project thread before someone goes on leave."},
            {"scenario": "Open-question surfacing", "example": "List unanswered questions in a long thread so nothing is dropped before a deadline."},
        ],
        "when_not_to_use": "Skip when the thread is purely social or informational with no commitments — it will manufacture tasks. Skip when relative dates can't be anchored because {today} is unknown or the thread spans an ambiguous timezone.",
        "full_prompt": """You are an assistant that turns an email thread into a clean, de-duplicated action list. Extract only real commitments and asks. Resolve owners and dates from the text. When you cannot resolve something, say so rather than guessing.

INPUT
- Email thread (oldest to newest, with sender names/signatures if present): {email_thread}
- Today's date (anchor for relative dates): {today}

OUTPUT — return ONE JSON object, no prose outside it:

{
  "action_items": [
    {
      "task": "<imperative phrasing, e.g. 'Send revised SOW to BetaCo'>",
      "owner": "<person resolved from text/signature, or 'unassigned'>",
      "owner_basis": "<how owner was resolved: 'said \\"I'll\\"', 'assigned to X', 'unclear'>",
      "due": "YYYY-MM-DD | null",
      "due_basis": "<e.g. 'EOD Friday -> 2026-06-12', 'next week (ambiguous)', 'none stated'>",
      "blocking": true,
      "blocks_what": "<what is blocked, or ''>",
      "source_quote": "<verbatim line the item came from>"
    }
  ],
  "decisions_made": [ { "decision": "", "source_quote": "" } ],
  "open_questions": [ { "question": "", "asked_by": "", "directed_to": "<person or 'thread'>" } ],
  "extraction_caveats": ["<e.g. 'timezone unstated for deadlines', 'two people named Chris'>"]
}

RESOLUTION RULES
- OWNER: resolve from "I'll / I can / I will" (-> the sender of that message), explicit assignment ("Sam, can you..."), or signature. If genuinely unclear, owner="unassigned" and owner_basis explains why. Never assign by guess.
- DUE: resolve relative dates against {today}. "Friday" / "EOD Tomorrow" / "next Tuesday" -> an ISO date; show the resolution in due_basis. If a relative date is ambiguous (e.g. "next week" with no day), due=null and note the ambiguity. No deadline stated -> due=null.
- BLOCKING: true only if the text indicates one item gates another or a deadline; name what's blocked.
- DE-DUPE: if the same task is restated across messages, keep ONE item (the most specific phrasing) and reflect the latest owner/date.

CRITICAL RULES
- Only extract genuine commitments, asks, decisions, and questions. Do NOT invent tasks from pleasantries or FYIs.
- Every action_item and decision carries a verbatim source_quote. No quote -> drop it.
- Do not guess owners or dates. Unresolved -> 'unassigned' / null with a basis note.
- Output valid JSON only — no markdown fences, no text outside the object.

THREAD
{email_thread}

TODAY
{today}

Begin.""",
        "input_variables": [
            {"name": "email_thread", "type": "string", "description": "The email or full thread text, oldest message first, ideally with sender names and signatures so owners can be resolved.", "required": True, "example": "From Sam (Mon): Team, we need the revised SOW out before BetaCo's review. From Priya (Mon): I'll send it by EOD Friday. From Sam (Tue): Great. Chris, can you confirm the pricing table by Wednesday so Priya isn't blocked? — Sam"},
            {"name": "today", "type": "string", "description": "Today's date as an anchor for resolving relative dates like 'Friday' or 'tomorrow'. ISO format recommended.", "required": True, "example": "2026-06-10 (Tuesday)"},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "{\"action_items\":[{\"task\":\"Send revised SOW to BetaCo\",\"owner\":\"Priya\",\"owner_basis\":\"said 'I'll send it'\",\"due\":\"2026-06-13\",\"due_basis\":\"EOD Friday -> 2026-06-13\",\"blocking\":false,\"blocks_what\":\"\",\"source_quote\":\"I'll send it by EOD Friday.\"},{\"task\":\"Confirm pricing table\",\"owner\":\"Chris\",\"owner_basis\":\"assigned by Sam\",\"due\":\"2026-06-11\",\"due_basis\":\"Wednesday -> 2026-06-11\",\"blocking\":true,\"blocks_what\":\"Priya's SOW\",\"source_quote\":\"Chris, can you confirm the pricing table by Wednesday\"}],\"decisions_made\":[],\"open_questions\":[],\"extraction_caveats\":[\"timezone unstated for deadlines\"]}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Reliable owner resolution from 'I'll' vs assignment, and honest 'unassigned' when unclear. Good relative-date arithmetic."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best at de-duping the same task restated across a long thread and tracking who the latest owner is."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong; sometimes over-extracts FYIs as tasks — re-pin 'genuine commitments only'. Dates accurate."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Handles short threads; can mis-anchor relative dates and guess owners — keep {today} explicit and the no-guess rule loud."},
        ],
        "variations": [
            {"label": "My-tasks filter", "description": "Only items owned by one person.", "prompt_snippet": "After extraction, filter action_items to those owned by {me} (and include 'unassigned' items where {me} is the likely owner, flagged as needs-confirmation)."},
            {"label": "Calendar-ready", "description": "Emit due items as events.", "prompt_snippet": "For every action_item with a non-null due, also emit an 'events' array: {title, date, owner}. Skip items with null due."},
            {"label": "Slack digest", "description": "Human-readable summary.", "prompt_snippet": "After the JSON, write a short plain-text digest grouped by owner, with due dates, suitable for pasting into a channel. Mark blockers with a leading '!'."},
        ],
        "failure_modes": [
            {"symptom": "Manufactures tasks out of greetings or FYIs.", "fix": "Re-pin: 'extract only genuine commitments/asks/decisions/questions. A line with no commitment produces no item.'"},
            {"symptom": "Guesses an owner when the thread is ambiguous.", "fix": "Add: 'owner=unassigned with owner_basis when resolution is not explicit. Never assign by guess.'"},
            {"symptom": "Mis-resolves 'next week' to a specific wrong date.", "fix": "Re-pin: 'ambiguous relative dates -> due=null and note the ambiguity in due_basis. Only resolve dates you can pin from {today}.'"},
            {"symptom": "Lists the same task three times because it was repeated in the thread.", "fix": "Add: 'de-dupe restated tasks to one item using the most specific phrasing and the latest owner/date.'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-06-10"},
        "related_prompt_slugs": ["structured-extraction-from-docs", "meeting-decision-recorder", "inbox-zero-triage"],
        "related_glossary_slugs": ["structured-output", "named-entity-recognition"],
        "related_tool_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How does it decide who owns a task?", "answer": "It resolves owners from explicit signals: 'I'll / I will' maps to that message's sender, 'Sam, can you...' assigns to Sam, and signatures disambiguate. When none of those apply, the owner is 'unassigned' with a basis note — it does not guess."},
            {"question": "What if a deadline says 'Friday' with no date?", "answer": "It resolves relative dates against the {today} you provide and shows the math in due_basis ('EOD Friday -> 2026-06-13'). Genuinely ambiguous phrases like 'next week' become due=null with a note, so you don't get a confidently wrong date."},
            {"question": "Will it pick up decisions, not just tasks?", "answer": "Yes — decisions_made and open_questions are separate sections, each decision backed by a verbatim quote. That separates 'we agreed X' from 'someone will do X' and surfaces unanswered questions before a deadline."},
            {"question": "Why does every item need a source quote?", "answer": "It keeps the extractor honest. If a task can't be tied to a verbatim line in the thread, the prompt drops it — which is how it avoids inventing commitments that nobody actually made."},
        ],
        "meta_title": "Email Thread to Action Items — Extraction Prompt",
        "meta_description": "Extract action items from email threads: owner, due date resolved against today, blockers, source quotes, plus decisions and open questions.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "citation-reference-extractor",
        "title": "Academic Citation/Reference Extractor",
        "tldr": "Parse a messy bibliography or reference list into normalized records — authors, year, title, venue, DOI/URL, type — handling mixed APA/MLA/Chicago styles, flagging incomplete entries, and never inventing a DOI.",
        "category": "data-extraction",
        "tags": ["citations", "academic", "bibliography", "extraction", "structured-output"],
        "best_for_tags": ["researchers", "librarians", "grad-students"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Reference-manager import", "example": "Convert a pasted references section into structured records for Zotero/BibTeX."},
            {"scenario": "Mixed-style cleanup", "example": "Normalize a list where some entries are APA, some MLA, some half-formatted."},
            {"scenario": "Completeness audit", "example": "Flag which references are missing a year, venue, or DOI before submitting a manuscript."},
            {"scenario": "Reformat to one style", "example": "Output every reference rendered in a single target style for a journal's requirements."},
        ],
        "when_not_to_use": "Skip when you need DOIs or metadata verified against a live database — this normalizes what's written, it does not look anything up. Skip on OCR'd scans until the text is clean, since broken characters corrupt author and title parsing.",
        "full_prompt": """You are a bibliography parser. Convert the reference text below into normalized records. Parse mixed citation styles. Flag anything incomplete. Never fabricate identifiers.

INPUT
- Reference / bibliography text (may mix APA, MLA, Chicago, or be half-formatted): {reference_text}
- Output style preference (target style to also render, or 'none'): {output_style}

OUTPUT — return ONE JSON object, no prose outside it:

{
  "references": [
    {
      "raw": "<the original entry, verbatim>",
      "type": "journal-article | book | book-chapter | conference-paper | report | webpage | thesis | preprint | unknown",
      "authors": ["Family, Given", "..."],
      "year": "YYYY | null",
      "title": "<article/chapter/book title>",
      "venue": "<journal / book / conference / publisher; null if absent>",
      "volume_issue_pages": "<e.g. '12(3), 45-67'; null>",
      "doi": "<as written, e.g. '10.1000/xyz'; null if not present>",
      "url": "<as written; null>",
      "detected_style": "apa | mla | chicago | mixed | unknown",
      "completeness": "complete | missing_fields",
      "missing": ["<field names that are absent, e.g. 'year', 'doi'>"]
    }
  ],
  "rendered": [ { "raw": "<original>", "as_style": "<output_style or omitted>", "text": "<reference rendered in the target style>" } ],
  "parse_caveats": ["<e.g. 'one entry merged two references — split', 'et al. expanded only where authors listed'>"]
}

PARSING RULES
- authors: parse into "Family, Given" where possible. Keep "et al." as a final list element ONLY if the source truncates authors — do not invent the hidden names.
- year: 4-digit publication year. "n.d." or absent -> null and add 'year' to missing.
- doi/url: copy EXACTLY as written. If a DOI is not in the text, doi=null. NEVER construct or guess a DOI or URL.
- detected_style is a best-effort label per entry; "mixed" if the list is inconsistent.
- If {output_style} is a real style, render each parsable reference in 'rendered'; if 'none', omit the rendered array.

CRITICAL RULES
- NEVER fabricate a DOI, URL, page range, or author name. Absent identifier -> null + listed in missing. This is the whole point of the tool.
- raw must be the verbatim original entry so a human can verify the parse.
- Mark completeness="missing_fields" whenever any of {authors, year, title, venue} is absent.
- Output valid JSON only — no markdown fences, no text outside the object.

REFERENCES
{reference_text}

OUTPUT STYLE
{output_style}

Begin.""",
        "input_variables": [
            {"name": "reference_text", "type": "string", "description": "The reference list or bibliography as text. May be inconsistently formatted or mix citation styles.", "required": True, "example": "Smith, J. (2021). Attention and memory. Journal of Cognition, 12(3), 45-67. https://doi.org/10.1000/abc\\nDoe, A. and Lee, B. Machine learning basics. MIT Press, 2019.\\nGarcia M. \"Deep nets.\" Proc. NeurIPS 2022."},
            {"name": "output_style", "type": "string", "description": "Target citation style to also render entries in (apa, mla, chicago), or 'none' to skip rendering.", "required": True, "example": "apa"},
        ],
        "expected_output": {
            "format": "json",
            "sample": "{\"references\":[{\"raw\":\"Smith, J. (2021). Attention and memory. Journal of Cognition, 12(3), 45-67. https://doi.org/10.1000/abc\",\"type\":\"journal-article\",\"authors\":[\"Smith, J.\"],\"year\":\"2021\",\"title\":\"Attention and memory\",\"venue\":\"Journal of Cognition\",\"volume_issue_pages\":\"12(3), 45-67\",\"doi\":\"10.1000/abc\",\"url\":\"https://doi.org/10.1000/abc\",\"detected_style\":\"apa\",\"completeness\":\"complete\",\"missing\":[]},{\"raw\":\"Garcia M. \\\"Deep nets.\\\" Proc. NeurIPS 2022.\",\"type\":\"conference-paper\",\"authors\":[\"Garcia, M.\"],\"year\":\"2022\",\"title\":\"Deep nets\",\"venue\":\"NeurIPS\",\"volume_issue_pages\":null,\"doi\":null,\"url\":null,\"detected_style\":\"mla\",\"completeness\":\"missing_fields\",\"missing\":[\"doi\"]}],\"rendered\":[],\"parse_caveats\":[\"styles inconsistent across list\"]}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Cleanly separates verbatim raw from parsed fields and reliably returns doi=null instead of constructing one."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best at disambiguating mixed styles per-entry and splitting accidentally merged references."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong author/venue parsing; has been observed to 'helpfully' synthesize a DOI — keep the never-fabricate rule first and verify outputs."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Handles tidy APA lists; struggles with MLA/Chicago and truncated author lists — chunk long lists and re-check missing-field flags."},
        ],
        "variations": [
            {"label": "BibTeX output", "description": "Emit importable BibTeX.", "prompt_snippet": "In addition to the JSON, emit a 'bibtex' array: one @article/@book/@inproceedings entry per parsable reference, with a generated cite key 'familyYear'. Leave fields blank rather than inventing them."},
            {"label": "Verify-checklist", "description": "Produce a to-verify list.", "prompt_snippet": "Add a 'needs_verification' array listing every reference where year, doi, or venue is missing, with a one-line note on what a human should look up."},
            {"label": "Single-style normalize", "description": "Force one consistent style.", "prompt_snippet": "Ignore per-entry detected_style. Render ALL references in {output_style} in 'rendered', flag any that cannot be fully rendered due to missing fields, and list what's missing."},
        ],
        "failure_modes": [
            {"symptom": "Constructs a DOI that looks plausible but is fabricated.", "fix": "Re-pin the CRITICAL RULE: 'absent DOI/URL -> null, added to missing. Never construct identifiers — that defeats the tool.'"},
            {"symptom": "Expands 'et al.' into invented author names.", "fix": "Add: 'keep \\'et al.\\' as a final element when the source truncates authors. Do not invent hidden names.'"},
            {"symptom": "Merges two references into one record.", "fix": "Add: 'if an entry contains two distinct works, split into two records and note it in parse_caveats.'"},
            {"symptom": "Drops the original text so the parse can't be checked.", "fix": "Require: 'raw must hold the verbatim original entry for every record.'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-06-10"},
        "related_prompt_slugs": ["structured-extraction-from-docs", "json-schema-from-examples", "literature-review-synthesizer"],
        "related_glossary_slugs": ["structured-output", "hallucination", "named-entity-recognition"],
        "related_tool_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Will it verify the DOIs are real?", "answer": "No. It normalizes what's written and copies DOIs/URLs exactly as they appear; if one is absent it returns null and flags it. Verification against a live database (Crossref, etc.) is a separate step — the prompt's job is to never fabricate one."},
            {"question": "How does it cope with a list that mixes APA, MLA, and Chicago?", "answer": "It labels detected_style per entry (and 'mixed' for the list) and parses fields regardless of style. If you set output_style, it also re-renders each parsable entry in that single target style."},
            {"question": "What happens to incomplete references?", "answer": "They're kept, marked completeness='missing_fields', and the absent fields are listed in 'missing'. That gives you an audit of exactly which entries need a year, venue, or DOI before submission."},
            {"question": "Why keep the raw text in every record?", "answer": "So you can verify the parse at a glance. Author and title parsing on messy input is error-prone; pairing the structured fields with the verbatim original lets a human catch mistakes quickly."},
        ],
        "meta_title": "Academic Citation/Reference Extractor — Extraction Prompt",
        "meta_description": "Parse messy bibliographies into normalized records: authors, year, venue, DOI. Handles mixed APA/MLA/Chicago, flags gaps, never invents DOIs.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "event-timeline-extractor",
        "title": "Event Timeline Extractor",
        "tldr": "Turn a narrative — incident writeup, history, deposition — into an ordered timeline: absolute timestamp resolved against an anchor date, actor, event, source quote, and certainty, handling partial dates explicitly.",
        "category": "data-extraction",
        "tags": ["timeline", "extraction", "incident", "chronology", "structured-output"],
        "best_for_tags": ["sre", "analysts", "investigators"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Incident chronology", "example": "Build a minute-by-minute timeline from an outage writeup for the postmortem."},
            {"scenario": "Case-file sequencing", "example": "Order events from interview notes that reference 'the next morning' and 'two days later'."},
            {"scenario": "Project history", "example": "Reconstruct decision and milestone dates from a long status-update document."},
            {"scenario": "Deposition summary", "example": "Sequence who did what when from a narrative statement, flagging uncertain dates."},
        ],
        "when_not_to_use": "Skip when no anchor date exists and the text uses only relative references — timestamps can't be resolved. Treat the output as a drafting aid, not a verified record of fact; certainty flags are the model's estimate, not evidence.",
        "full_prompt": """You are a timeline analyst. Extract every datable event from the narrative below into a single ordered chronology. Resolve relative dates against the anchor. Be explicit about ambiguity and never invent precision the text does not support.

INPUT
- Document text (narrative, report, statement, notes): {document_text}
- Anchor date (the reference point for relative expressions): {anchor_date}

OUTPUT — emit a markdown table, then a short notes block.

TABLE columns:
| # | timestamp | granularity | actor | event | certainty | source_quote |

- timestamp: absolute, ISO where possible (YYYY-MM-DD, add THH:MM if the text gives a time). Resolve "the next morning", "two days later", "by Friday" against {anchor_date} and any already-established date in the narrative.
- granularity: exact | day | approximate | range. Use "range" for "sometime between X and Y" (put the range in timestamp). Use "approximate" for "around noon" / "early March".
- actor: who did it (person, system, team) or "unspecified".
- event: a terse factual description.
- certainty: high (date stated) | medium (resolved from a clear relative reference) | low (vague/contradentary).
- source_quote: the verbatim phrase the event and its timing came from.

After the table, add:

NOTES
- Ordering decisions: how you sequenced events that shared a date or had only relative ordering.
- Ambiguities: any date you could not pin (and why it stays approximate/range/low).
- Conflicts: places where the narrative gives inconsistent timing.
- Unresolvable: events mentioned with no usable time reference (listed, placed at the end, certainty=low).

RESOLUTION RULES
- Chain relative dates: once a date is established, "the following week" is computed from it, not from {anchor_date}, unless the text re-anchors.
- Do NOT fabricate a clock time when only a day is given (granularity=day, not THH:MM).
- If two events are ordered only relative to each other ("after the deploy, alerts fired") with no clock, keep their order and mark both certainty=medium or low.

CRITICAL RULES
- Every row has a verbatim source_quote. No quote -> the event does not go in the table.
- Never invent precision: a vague date stays approximate/range, never a false exact timestamp.
- Surface conflicts in NOTES rather than silently picking one.
- The table is ORDERED earliest to latest; unresolvable events go last.

DOCUMENT
{document_text}

ANCHOR DATE
{anchor_date}

Begin.""",
        "input_variables": [
            {"name": "document_text", "type": "string", "description": "The narrative text to extract a timeline from. Can mix absolute and relative date references.", "required": True, "example": "On June 3 at 14:10 the deploy went out. The next morning, users reported slow logins. Two days later we rolled back, and alerts cleared within the hour. Sometime the following week we shipped the proper fix."},
            {"name": "anchor_date", "type": "string", "description": "The reference date for resolving relative expressions like 'the next morning' or 'two days later'. ISO format recommended.", "required": True, "example": "2026-06-03 (the deploy date referenced as the document's starting point)"},
        ],
        "expected_output": {
            "format": "table",
            "sample": "| # | timestamp | granularity | actor | event | certainty | source_quote |\\n|---|---|---|---|---|---|---|\\n| 1 | 2026-06-03T14:10 | exact | deploy system | Deploy released | high | \"On June 3 at 14:10 the deploy went out\" |\\n| 2 | 2026-06-04 | day | users | Slow logins reported | medium | \"The next morning, users reported slow logins\" |\\n| 3 | 2026-06-05 | day | ops team | Rolled back; alerts cleared | medium | \"Two days later we rolled back, and alerts cleared within the hour\" |\\n| 4 | 2026-06-08/2026-06-12 | range | team | Proper fix shipped | low | \"Sometime the following week we shipped the proper fix\" |\\n\\nNOTES\\n- Ordering: row 3 chained from row 1 (June 3 + 2 days).\\n- Ambiguities: row 4 is a week range, no day given.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strong at chaining relative dates correctly and refusing to invent clock times when only a day is stated."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best at surfacing timing conflicts in NOTES and reasoning about relative-only ordering without forcing false timestamps."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Accurate date math; occasionally upgrades 'around noon' to an exact time — re-pin the granularity rule."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Fine on short, mostly-absolute narratives; loses the chain on multi-hop relative dates and may drop the source_quote — keep both rules loud."},
        ],
        "variations": [
            {"label": "JSON timeline", "description": "Machine-readable instead of a table.", "prompt_snippet": "Instead of a markdown table, return a JSON array of event objects with the same fields (timestamp, granularity, actor, event, certainty, source_quote) plus a 'notes' object."},
            {"label": "Multi-source merge", "description": "Reconcile two accounts.", "prompt_snippet": "You are given SOURCE_A and SOURCE_B describing the same events. Build one merged timeline, tag each row with its source(s), and flag in NOTES where the two accounts disagree on timing."},
            {"label": "Gap finder", "description": "Highlight missing intervals.", "prompt_snippet": "After the table, add a 'gaps' section listing notable unexplained time spans between consecutive events (e.g. 'no activity recorded for ~6 hours between rows 2 and 3')."},
        ],
        "failure_modes": [
            {"symptom": "Invents an exact clock time from a day-only reference.", "fix": "Re-pin: 'granularity=day means no THH:MM. Never fabricate a time the text doesn't give.'"},
            {"symptom": "Resolves a long relative chain off the anchor instead of the prior event.", "fix": "Add: 'chain relative dates from the most recently established date; only use {anchor_date} when nothing closer exists or the text re-anchors.'"},
            {"symptom": "Silently picks one side of a timing conflict.", "fix": "Require: 'inconsistent timing is reported in NOTES > Conflicts, not resolved by guessing.'"},
            {"symptom": "Includes events without a supporting quote.", "fix": "Hard rule: 'no verbatim source_quote -> the event is excluded from the table.'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-06-10"},
        "related_prompt_slugs": ["structured-extraction-from-docs", "incident-postmortem-blameless", "log-pattern-extractor"],
        "related_glossary_slugs": ["structured-output", "named-entity-recognition", "grounding"],
        "related_tool_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How does it handle 'two days later' or 'the next morning'?", "answer": "It chains relative expressions: once a date is established in the narrative, subsequent relatives are computed from the most recent date, falling back to your anchor_date only when nothing closer exists. The resolution shows up via the certainty='medium' flag and the source_quote."},
            {"question": "What if a date is genuinely vague?", "answer": "It stays vague. 'Early March' becomes granularity='approximate', 'sometime between X and Y' becomes granularity='range' with the range in the timestamp, and certainty drops to low. The prompt is explicitly barred from inventing false precision."},
            {"question": "Can I trust the timeline as a factual record?", "answer": "Treat it as a drafting aid. The certainty column is the model's estimate from the text, not independent verification, and every row carries a quote so a human can confirm it against the source. Conflicts are surfaced in NOTES rather than silently resolved."},
            {"question": "What about events with no usable date?", "answer": "They're still captured, placed at the end of the ordered table with certainty=low, and called out under NOTES > Unresolvable — so a mention with no time reference isn't lost, but also isn't given a fabricated slot in the sequence."},
        ],
        "meta_title": "Event Timeline Extractor — Data Extraction Prompt",
        "meta_description": "Build an ordered timeline from any narrative: absolute timestamps from relative dates, actor, event, source quote, certainty. Handles ambiguity explicitly.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "messy-text-to-clean-table",
        "title": "Messy Text to Clean Table",
        "tldr": "Turn unstructured blobs — listings, forum posts, spec dumps — into a clean table: infer a schema, apply it consistently, normalize units/currencies/booleans, one row per entity, leaving empty cells rather than guessing.",
        "category": "data-extraction",
        "tags": ["table", "normalization", "extraction", "data-cleaning", "structured-output"],
        "best_for_tags": ["analysts", "ops", "founders"],
        "difficulty_tier": "beginner",
        "featured": True,
        "use_cases": [
            {"scenario": "Listings to spreadsheet", "example": "Paste 30 marketplace listings and get columns for price, location, beds, and area."},
            {"scenario": "Forum-post comparison", "example": "Turn a thread of 'my rig' posts into a table of CPU, GPU, RAM, and price."},
            {"scenario": "Spec-sheet roundup", "example": "Normalize five vendor spec blurbs into one comparable table with consistent units."},
            {"scenario": "Contact harvesting", "example": "Extract name, company, email, and role from a block of signatures into rows."},
        ],
        "when_not_to_use": "Skip when the entities aren't comparable enough to share columns — forcing one schema onto unlike items produces a sparse, misleading table. Skip when source values must be preserved exactly (legal/financial records) since normalization rewrites units and formats.",
        "full_prompt": """You are a data-structuring assistant. Convert the messy text below into one clean table. Infer a consistent schema, apply it to every entity, and normalize values. When a value is absent, leave the cell empty — do not guess.

INPUT
- Raw text (unstructured; may contain many entities): {raw_text}
- Desired columns (use these if given; otherwise INFER a schema and state it): {desired_columns}

OUTPUT

1) SCHEMA (state it before the table)
- Columns (in order): ___
- One row = one ___ (name the entity type).
- Normalization decisions:
  - Units: ___ (e.g. all areas in m2, all prices in USD).
  - Booleans: yes/no -> true/false.
  - Dates: -> YYYY-MM-DD.
  - Multi-value cells: ___ (e.g. semicolon-separated).

2) TABLE (markdown)
| col1 | col2 | ... |
- One row per entity. Same columns for every row.
- Empty value -> "" (empty), never a guess or "N/A" unless the source literally says N/A.
- Verbatim identifiers (names, SKUs) preserved; measurements normalized to the chosen unit.

3) NOTES
- Ambiguous parses (and how you resolved them).
- Entities you split or merged (e.g. one post listed two items).
- Values you normalized and the original (e.g. "1,200 sqft -> 111.5 m2").
- Rows with low confidence (mostly-empty or hard-to-parse).

NORMALIZATION RULES
- Pick ONE unit per dimension across the whole table and convert everything to it; show conversions in NOTES.
- Currency: pick one (prefer the dominant one in the text); note assumed currency if symbols are missing.
- Don't collapse distinct entities into one row, and don't split one entity across rows.

CRITICAL RULES
- The schema is CONSISTENT: every row has the same columns, even if some cells are empty.
- Empty cell = "" not a fabricated value. Never invent a price, spec, or date that isn't in the text.
- State the inferred schema BEFORE the table so it can be checked.
- If the entities are too heterogeneous to share one schema, say so in NOTES and propose splitting into multiple tables instead of forcing a bad fit.

RAW TEXT
{raw_text}

DESIRED COLUMNS
{desired_columns}

Begin.""",
        "input_variables": [
            {"name": "raw_text", "type": "string", "description": "The unstructured text to convert into a table. Often a paste of multiple listings, posts, or specs.", "required": True, "example": "2BR apt downtown, 1200 sqft, $2,300/mo, parking incl. // Studio near park, 480 sq ft, 1600 a month, no parking. // 3 bedroom, 95 sqm, EUR 1,900, pets ok."},
            {"name": "desired_columns", "type": "string", "description": "Comma-separated columns you want. Leave empty to let the prompt infer a schema and report it.", "required": False, "example": "type, area_m2, price_usd_per_month, parking, pets_allowed"},
        ],
        "expected_output": {
            "format": "table",
            "sample": "SCHEMA\\n- Columns: type, area_m2, price_usd_month, parking, pets\\n- One row = one rental listing.\\n- Areas -> m2; prices -> USD; parking/pets -> true/false.\\n\\n| type | area_m2 | price_usd_month | parking | pets |\\n|---|---|---|---|---|\\n| 2BR | 111.5 | 2300 | true |  |\\n| studio | 44.6 | 1600 | false |  |\\n| 3BR | 95 |  | true | true |\\n\\nNOTES\\n- '1200 sqft -> 111.5 m2'; '480 sq ft -> 44.6 m2'.\\n- Row 3 price was EUR 1,900 -> left price_usd_month empty (no FX rate assumed); original noted here.\\n- pets unknown for rows 1-2 -> empty.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Reliable schema consistency and honest empty cells; shows unit conversions in NOTES instead of silently changing numbers."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best at inferring a sensible schema from heterogeneous text and recommending a table split when entities don't fit one shape."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong normalization; sometimes fills empty cells with 'N/A' or a guess — re-pin the empty-cell rule. Good unit math."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable for small, uniform blobs; column drift and inconsistent units appear on larger inputs — give explicit desired_columns and chunk."},
        ],
        "variations": [
            {"label": "CSV output", "description": "Emit raw CSV for import.", "prompt_snippet": "After the markdown table, also emit valid CSV (RFC 4180): header row of the schema columns, one row per entity, empty fields blank, values quoted only if they contain commas."},
            {"label": "Strict schema", "description": "Reject rows that don't fit.", "prompt_snippet": "Use ONLY {desired_columns}; do not add columns. Any entity that lacks a value for a required column still gets a row with empty cells, and is listed in NOTES as incomplete. Never add ad-hoc columns."},
            {"label": "Dedupe entities", "description": "Collapse repeats.", "prompt_snippet": "If the same entity appears more than once, merge into one row using the most complete values, and note the merge (and any conflicting values) in NOTES."},
        ],
        "failure_modes": [
            {"symptom": "Different rows have different columns.", "fix": "Re-pin: 'state the schema first, then every row uses exactly those columns — empty cells allowed, missing columns not.'"},
            {"symptom": "Fills blank cells with guessed values or 'N/A'.", "fix": "Add: 'absent value -> empty string. Only write N/A if the source literally says N/A. Never infer a price/spec/date.'"},
            {"symptom": "Mixes units in one column (sqft and m2).", "fix": "Add: 'choose one unit per dimension for the whole table; convert all values to it and list conversions in NOTES.'"},
            {"symptom": "Forces unlike entities into one sparse table.", "fix": "Require: 'if entities are too heterogeneous, say so in NOTES and propose splitting into multiple tables rather than one bad fit.'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-06-10"},
        "related_prompt_slugs": ["json-from-unstructured-text", "structured-extraction-from-docs", "json-schema-from-examples"],
        "related_glossary_slugs": ["structured-output", "named-entity-recognition"],
        "related_tool_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What if I don't know what columns I want?", "answer": "Leave desired_columns empty and the prompt infers a schema from the entities, then states it before the table so you can adjust. If you do know your columns, pass them and use the Strict-schema variation to prevent ad-hoc columns from appearing."},
            {"question": "Why are some cells empty instead of filled?", "answer": "Because the source didn't state a value. The prompt is explicitly barred from guessing prices, specs, or dates — an empty cell is the honest signal that you need the data elsewhere, which is far safer than a confident fabrication."},
            {"question": "How does unit normalization work?", "answer": "It picks one unit per dimension (e.g. all areas in m2, all prices in USD) and converts every value to it, listing each conversion in NOTES with the original. Where it can't convert safely — like a foreign currency with no rate — it leaves the cell empty and explains."},
            {"question": "What if the blob has two different kinds of thing?", "answer": "It will tell you. Rather than cramming unlike entities into one sparse table, it recommends splitting into multiple tables in NOTES, so you get clean comparable rows instead of a mostly-empty grid."},
        ],
        "meta_title": "Messy Text to Clean Table — Data Extraction Prompt",
        "meta_description": "Convert unstructured text into a clean table: inferred consistent schema, normalized units/currencies/booleans, one row per entity, empty cells never guessed.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "structured-edit-json-patch",
        "title": "Structured Document Edit via JSON Patch",
        "tldr": "Given a JSON document and an edit instruction, return RFC 6902 JSON Patch ops — not the whole document — so changes are minimal and auditable; validates paths exist and refuses ops that break a provided schema.",
        "category": "structured-output",
        "tags": ["json-patch", "rfc-6902", "structured-output", "editing", "validation"],
        "best_for_tags": ["developers", "platform-teams", "automation"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Config edits", "example": "Apply 'set timeout to 30 and remove the deprecated retries flag' as a reviewable patch."},
            {"scenario": "LLM-driven updates", "example": "Let a model edit a settings document while keeping a diff a human can approve."},
            {"scenario": "Bulk field updates", "example": "Add a 'region' field to several nested service objects without rewriting the file."},
            {"scenario": "Safe partial writes", "example": "Change one value deep in a large JSON blob and emit only the op that changed."},
        ],
        "when_not_to_use": "Skip when the consumer can't apply a JSON Patch (then ask for the full updated document instead). Do not auto-apply patches to production data without human review or schema validation — a wrong path or value can corrupt state.",
        "full_prompt": """You are a precise JSON editor. Given a document and an instruction, output ONLY the RFC 6902 JSON Patch that performs the edit — the minimal set of operations, every path validated. You do not rewrite the whole document.

INPUT
- JSON document (the current state): {json_document}
- Edit instruction (natural language): {edit_instruction}
- Optional JSON Schema the result must still satisfy ('none' if not provided): {result_schema}

OUTPUT — return ONE JSON object, no prose outside it:

{
  "patch": [
    { "op": "add | remove | replace | move | copy | test", "path": "/json/pointer", "value": <only for add/replace/test>, "from": "/pointer (move/copy only)" }
  ],
  "rationale": "<one line per op: what it does and why>",
  "validation": {
    "paths_exist": true,
    "schema": "satisfied | would_violate | not_provided",
    "violations": ["<if would_violate: which constraint and which op>"]
  },
  "refused": ["<any requested change you did NOT emit, with the reason>"]
}

PATCH RULES
- Use JSON Pointer paths (RFC 6901). Array append uses "/-". Escape "/" as "~1" and "~" as "~0" in keys.
- Prefer "replace" over remove+add for an existing key. Use "remove" only to delete. Use "move"/"copy" for relocation, not delete+add.
- Emit the MINIMAL ops: do not touch fields the instruction doesn't change.
- For a "replace" or "remove", the target path MUST already exist in {json_document}; if it doesn't, do not emit the op — list it under "refused".
- For "add" into a parent, the PARENT path must exist.

VALIDATION
- Before emitting, mentally apply the patch and check it against {result_schema} if provided. If any op would violate the schema (wrong type, removes a required field, breaks an enum), DO NOT emit that op — record it in "refused" and set schema="would_violate".
- Set paths_exist=false and refuse ops whose target/parent path is missing.

CRITICAL RULES
- Output a PATCH, never the full document. The point is a minimal, auditable diff.
- Never emit an op against a non-existent path, and never produce a result that violates {result_schema}. Refuse and explain instead.
- Do not guess values the instruction doesn't specify; if the instruction is ambiguous about a value, refuse that op with a clarifying note.
- Output valid JSON only — no markdown fences, no text outside the object.

DOCUMENT
{json_document}

INSTRUCTION
{edit_instruction}

SCHEMA
{result_schema}

Begin.""",
        "input_variables": [
            {"name": "json_document", "type": "string", "description": "The current JSON document to edit, as a JSON string. Patch paths are validated against this.", "required": True, "example": "{\"service\":{\"timeout\":15,\"retries\":3,\"deprecated_flag\":true},\"regions\":[\"us\"]}"},
            {"name": "edit_instruction", "type": "string", "description": "A natural-language description of the change to make.", "required": True, "example": "Set the service timeout to 30, delete deprecated_flag, and add 'eu' to regions."},
            {"name": "result_schema", "type": "string", "description": "Optional JSON Schema the edited document must still satisfy. Pass 'none' to skip schema validation.", "required": False, "example": "{\"type\":\"object\",\"properties\":{\"service\":{\"required\":[\"timeout\"]}}}"},
        ],
        "expected_output": {
            "format": "json",
            "sample": "{\"patch\":[{\"op\":\"replace\",\"path\":\"/service/timeout\",\"value\":30},{\"op\":\"remove\",\"path\":\"/service/deprecated_flag\"},{\"op\":\"add\",\"path\":\"/regions/-\",\"value\":\"eu\"}],\"rationale\":\"replace timeout (key exists); remove deprecated_flag; append 'eu' to regions array\",\"validation\":{\"paths_exist\":true,\"schema\":\"satisfied\",\"violations\":[]},\"refused\":[]}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Reliable RFC 6902 ops and JSON Pointer escaping; consistently refuses ops against missing paths instead of inventing them."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best at the mental schema check before emitting and at choosing replace vs move/copy correctly on nested structures."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong patch generation; can over-emit ops touching unchanged fields — re-pin 'minimal ops'. Honors JSON-only output well."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Handles flat documents; struggles with deep pointers, '/-' append, and tilde-escaping — validate paths and keep edits shallow."},
        ],
        "variations": [
            {"label": "JSON Merge Patch", "description": "RFC 7386 instead of 6902.", "prompt_snippet": "Output an RFC 7386 JSON Merge Patch instead: a partial object where set-to-null means delete. Note the tradeoff (merge patch cannot target array elements precisely)."},
            {"label": "Dry-run preview", "description": "Show the resulting document too.", "prompt_snippet": "After the patch object, add 'preview': the full document AS IT WOULD LOOK after applying the patch, so a reviewer can eyeball the end state alongside the diff."},
            {"label": "Batch instructions", "description": "Multiple edits, grouped.", "prompt_snippet": "The instruction contains several changes. Group the emitted ops by which instruction clause they satisfy in 'rationale', and refuse per-clause so one bad clause doesn't block the others."},
        ],
        "failure_modes": [
            {"symptom": "Returns the whole edited document instead of a patch.", "fix": "Re-pin: 'output is the RFC 6902 patch array only — the minimal diff, not the document. Use the dry-run variation if a preview is needed.'"},
            {"symptom": "Emits an op against a path that doesn't exist.", "fix": "Add: 'replace/remove require the target path to already exist; add requires the parent to exist. Otherwise refuse and explain — never create the path silently.'"},
            {"symptom": "Touches fields the instruction didn't mention.", "fix": "Re-pin: 'minimal ops — do not modify anything outside the requested change.'"},
            {"symptom": "Produces a result that breaks the schema (e.g. removes a required field).", "fix": "Require: 'apply the patch mentally against {result_schema} first; any violating op goes to refused with schema=would_violate.'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-06-10"},
        "related_prompt_slugs": ["json-output-strict", "json-schema-from-examples", "structured-decision-tree-output"],
        "related_glossary_slugs": ["structured-output", "json-schema-enforcement", "json-mode", "strict-mode"],
        "related_tool_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why a patch instead of the full updated document?", "answer": "A minimal RFC 6902 patch is auditable — a reviewer sees exactly what changed and nothing else, and you avoid the risk of the model silently rewriting unrelated fields. If your consumer can't apply patches, use the dry-run variation to also get the previewed end state."},
            {"question": "What stops it from corrupting the document?", "answer": "Two guards: it refuses ops whose target or parent path doesn't exist (no silent path creation), and it mentally applies the patch against your result_schema and refuses any op that would violate it. Both refusals are reported with reasons rather than executed."},
            {"question": "Does it handle nested paths and arrays?", "answer": "Yes — it uses JSON Pointer (RFC 6901), '/-' to append to arrays, and tilde-escaping for keys containing '/' or '~'. Deep edits work, though smaller open models are less reliable on tricky pointers, so validate before applying."},
            {"question": "Can I run several edits at once?", "answer": "Yes. Put multiple changes in the instruction; the Batch-instructions variation groups the emitted ops by clause and refuses per-clause, so one ambiguous or invalid change doesn't block the valid ones."},
        ],
        "meta_title": "Structured Document Edit via JSON Patch — Prompt",
        "meta_description": "Edit JSON with RFC 6902 patches: minimal, auditable diffs. Validates paths exist, refuses schema-violating ops, never rewrites the whole document.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "form-filling-with-citations",
        "title": "Source-Grounded Form Filler",
        "tldr": "Fill a form or schema using only facts found in the supplied sources — every filled field carries a source span, unfound fields become null/'missing', nothing fabricated. The anti-hallucination structured-output pattern.",
        "category": "structured-output",
        "tags": ["grounding", "structured-output", "citations", "rag", "extraction"],
        "best_for_tags": ["rag-builders", "ops", "compliance"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Intake form from documents", "example": "Populate a customer-onboarding schema from uploaded PDFs, citing where each value came from."},
            {"scenario": "Grounded data entry", "example": "Fill a product record from a spec sheet so every field links to a source line."},
            {"scenario": "Compliance questionnaire", "example": "Answer a vendor security form strictly from the provided policy docs, leaving unknowns blank."},
            {"scenario": "RAG output with provenance", "example": "Return a structured answer where each field is traceable to a retrieved chunk."},
        ],
        "when_not_to_use": "Skip when fields require judgment or computation beyond what the sources state — this fills facts, it doesn't reason new conclusions. Don't treat 'missing' as 'false'; absence in the sources is not evidence of a negative.",
        "full_prompt": """You are a grounded form-filler. Populate the target form using ONLY facts stated in the source documents. Every filled field cites its source span. If a field's value is not in the sources, leave it null and mark it missing. You never fabricate.

INPUT
- Target form / schema (fields to fill, with types/notes): {form_schema}
- Source documents (the ONLY allowed source of facts): {source_documents}

OUTPUT — return ONE JSON object, no prose outside it:

{
  "fields": [
    {
      "name": "<field name from the schema>",
      "value": <filled value, or null>,
      "status": "filled | missing | ambiguous",
      "source_doc": "<which document, e.g. 'doc 2' or a title; null if missing>",
      "source_span": "<verbatim quote supporting the value; null if missing>",
      "confidence": 0.0,
      "note": "<only for ambiguous/missing explanation; else ''>"
    }
  ],
  "unfilled_required": ["<required field names left missing>"],
  "conflicts": ["<field where two sources disagree, with both spans>"],
  "out_of_scope_requests": ["<any field that asks for judgment/computation the sources don't directly support>"]
}

FILLING RULES
- A field is "filled" ONLY if a verbatim source_span supports it. No span -> status="missing", value=null.
- source_span is copied verbatim from the named source_doc. Paraphrase belongs in note, never in source_span.
- If two sources give different values, status="ambiguous", list both in conflicts, pick none (or the explicitly more authoritative one if the schema says which).
- Respect the field's type: a date field gets an ISO date drawn from the source; a boolean only if the source clearly states it.
- confidence: 0.9+ explicit single source; 0.6-0.8 inferred wording/units; below that -> ambiguous or missing.

CRITICAL RULES
- ONLY use the provided sources. Do not use outside or prior knowledge to fill a field. If it's not in the sources, it's missing.
- NEVER fabricate a value or a citation. A missing field is null + status="missing", added to unfilled_required if required.
- "missing" means "not stated in the sources", NOT "false". Do not infer a negative from absence.
- Fields requiring judgment/computation beyond the sources go in out_of_scope_requests, not guessed.
- Output valid JSON only — no markdown fences, no text outside the object.

FORM SCHEMA
{form_schema}

SOURCE DOCUMENTS
{source_documents}

Begin.""",
        "input_variables": [
            {"name": "form_schema", "type": "string", "description": "The target form or schema: field names, types, and which are required. Can be a JSON schema or a labeled list.", "required": True, "example": "{\"company_name\":{\"type\":\"string\",\"required\":true},\"incorporation_date\":{\"type\":\"date\",\"required\":true},\"employee_count\":{\"type\":\"integer\",\"required\":false},\"soc2_certified\":{\"type\":\"boolean\",\"required\":false}}"},
            {"name": "source_documents", "type": "string", "description": "The documents the model is allowed to draw facts from. Label them so citations can reference them.", "required": True, "example": "doc 1 (overview): Acme Inc. was incorporated on 2018-04-12 and is headquartered in Denver. doc 2 (security): Acme maintains a SOC 2 Type II report renewed annually."},
        ],
        "expected_output": {
            "format": "json",
            "sample": "{\"fields\":[{\"name\":\"company_name\",\"value\":\"Acme Inc.\",\"status\":\"filled\",\"source_doc\":\"doc 1\",\"source_span\":\"Acme Inc. was incorporated on 2018-04-12\",\"confidence\":0.97,\"note\":\"\"},{\"name\":\"incorporation_date\",\"value\":\"2018-04-12\",\"status\":\"filled\",\"source_doc\":\"doc 1\",\"source_span\":\"incorporated on 2018-04-12\",\"confidence\":0.97,\"note\":\"\"},{\"name\":\"employee_count\",\"value\":null,\"status\":\"missing\",\"source_doc\":null,\"source_span\":null,\"confidence\":0.0,\"note\":\"not stated in sources\"},{\"name\":\"soc2_certified\",\"value\":true,\"status\":\"filled\",\"source_doc\":\"doc 2\",\"source_span\":\"maintains a SOC 2 Type II report\",\"confidence\":0.9,\"note\":\"\"}],\"unfilled_required\":[],\"conflicts\":[],\"out_of_scope_requests\":[]}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strongest at refusing to fill from outside knowledge and distinguishing 'missing' from 'false'. Verbatim spans stay verbatim."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best at catching cross-document conflicts and routing judgment fields to out_of_scope_requests instead of guessing."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong grounding; occasionally backfills a well-known fact from training data — re-pin 'only the provided sources'. Use structured-output mode."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Honors grounding on short source sets; with many docs it may mis-cite which doc a span came from — keep sources clearly labeled and few."},
        ],
        "variations": [
            {"label": "Confidence threshold", "description": "Only fill above a bar.", "prompt_snippet": "Only set status='filled' when confidence >= {min_confidence}; below it, mark the field 'missing' with a note 'below confidence threshold' so downstream automation never acts on weak fills."},
            {"label": "Chunk-id citations", "description": "Cite retrieval chunk IDs.", "prompt_snippet": "Sources arrive as {id, text} chunks. Set source_doc to the chunk id and keep source_span verbatim, so the citation is machine-traceable back to the retrieval index."},
            {"label": "Reviewer worklist", "description": "Surface what a human must do.", "prompt_snippet": "After the JSON, output a short worklist: required fields still missing, conflicts to resolve, and out-of-scope items needing a human decision — ordered by blocking impact."},
        ],
        "failure_modes": [
            {"symptom": "Fills a field from training-data knowledge not in the sources.", "fix": "Re-pin: 'only the provided sources may fill a field. Well-known facts not in the sources are still missing.'"},
            {"symptom": "Treats a missing field as false.", "fix": "Add: 'missing = not stated. Never infer a negative (false/none) from absence; leave it missing.'"},
            {"symptom": "Paraphrases inside source_span so the citation can't be checked.", "fix": "Add: 'source_span is verbatim from source_doc. Any paraphrase goes in note.'"},
            {"symptom": "Guesses a value when two sources disagree.", "fix": "Require: 'conflicting sources -> status=ambiguous, both spans in conflicts, pick none unless the schema names an authority.'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-06-10"},
        "related_prompt_slugs": ["rag-source-citation-enforcer", "extraction-with-confidence-per-field", "structured-extraction-from-docs"],
        "related_glossary_slugs": ["grounding", "hallucination", "structured-output", "attribution-citation"],
        "related_tool_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How is this different from a normal extraction prompt?", "answer": "It's grounding-first: every filled field must carry a verbatim source span from the supplied documents, and anything not stated becomes null/missing rather than guessed. It's designed as the anti-hallucination pattern for structured output, so each value is traceable."},
            {"question": "Why does it leave fields blank instead of being helpful?", "answer": "Because 'helpful' guesses are exactly what cause hallucinations in form-filling. A 'missing' status is honest signal that the sources don't contain the fact — far safer for compliance or downstream automation than a confident but unsupported value."},
            {"question": "Does 'missing' mean the answer is no?", "answer": "No. 'Missing' means the sources don't state it. The prompt explicitly forbids inferring a negative from absence, so a missing soc2_certified field is unknown, not false. Resolve it with a human or more sources."},
            {"question": "What happens when sources disagree?", "answer": "The field is marked 'ambiguous', both conflicting spans are listed under conflicts, and the model picks neither — unless your schema names an authoritative source. That surfaces the disagreement for a human instead of silently choosing one."},
        ],
        "meta_title": "Source-Grounded Form Filler — Structured Output Prompt",
        "meta_description": "Fill forms from documents with per-field source citations. Unfound fields stay null/missing, conflicts surfaced, nothing fabricated. Anti-hallucination pattern.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "entity-relationship-graph-builder",
        "title": "Entity-Relationship Graph Builder",
        "tldr": "Turn text into knowledge-graph triples — subject, predicate, object — with entity types, canonical IDs (coreference resolved), a source span per edge, dedupe, and confidence, ready to import into a graph database.",
        "category": "structured-output",
        "tags": ["knowledge-graph", "triples", "ner", "structured-output", "graph-rag"],
        "best_for_tags": ["data-engineers", "rag-builders", "researchers"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Graph DB seeding", "example": "Extract company/person/product triples from filings to load into Neo4j."},
            {"scenario": "GraphRAG prep", "example": "Build an entity graph from a document set to power graph-based retrieval."},
            {"scenario": "Org-relationship mapping", "example": "Map who reports to whom and who owns what from a set of bios and memos."},
            {"scenario": "Coref-resolved extraction", "example": "Resolve 'the company', 'it', and 'Acme' to one node before forming edges."},
        ],
        "when_not_to_use": "Skip when relationships need verification against ground truth — extracted triples reflect what the text asserts, including its errors. For a single flat record per entity, a row/JSON extractor is simpler than a graph.",
        "full_prompt": """You are a knowledge-graph builder. Extract entities and the relationships between them from the text below as triples ready for a graph database. Resolve coreferences, canonicalize entity IDs, dedupe edges, and ground every edge in a source span.

INPUT
- Text: {text}
- Allowed entity types (restrict extraction to these; if empty, infer types): {entity_types}

OUTPUT — return ONE JSON object, no prose outside it:

{
  "entities": [
    { "id": "<canonical_snake_id, e.g. acme_inc>", "label": "<surface name>", "type": "<one of {entity_types} or inferred>", "aliases": ["<other surface forms / pronouns resolved to this entity>"] }
  ],
  "relationships": [
    {
      "subject": "<entity id>",
      "predicate": "<canonical_verb_phrase, e.g. acquired, reports_to, located_in>",
      "object": "<entity id OR a literal value>",
      "object_is_literal": false,
      "source_span": "<verbatim text the edge came from>",
      "confidence": 0.0
    }
  ],
  "unresolved_mentions": ["<a mention you could not confidently attach to an entity>"],
  "build_caveats": ["<e.g. 'pronoun \\"they\\" ambiguous between two orgs', 'predicate normalized acquired/bought -> acquired'>"]
}

GRAPH RULES
- CANONICAL IDS: one id per real-world entity. "Acme", "Acme Inc.", "the company", and "it" (when referring to Acme) all resolve to a single entity; record the surface forms in aliases.
- COREFERENCE: resolve pronouns and definite descriptions to their entity before forming edges. If a pronoun is genuinely ambiguous, do NOT force an edge — note it in build_caveats and/or unresolved_mentions.
- PREDICATES: normalize to a consistent verb phrase (snake_case). Merge synonyms ("bought" -> "acquired"). Keep direction meaningful (subject acquired object).
- DEDUPE: identical (subject, predicate, object) triples appear once. If the same edge is stated twice, keep one and you may raise confidence.
- object_is_literal=true when the object is a value (a date, money, place name not modeled as a node) rather than an entity id.
- Restrict entity types to {entity_types} when provided; drop or note entities outside the allowed types.

CRITICAL RULES
- Every relationship has a verbatim source_span. No span -> no edge.
- Do NOT invent entities or relationships not supported by the text. Asserted-in-text only.
- One canonical id per entity — getting coreference right is the whole value; do not create duplicate nodes for the same thing.
- Output valid JSON only — no markdown fences, no text outside the object.

TEXT
{text}

ENTITY TYPES
{entity_types}

Begin.""",
        "input_variables": [
            {"name": "text", "type": "string", "description": "The source text to extract a knowledge graph from. Prose with named entities and relationships works best.", "required": True, "example": "Acme Inc., founded in Denver, acquired Beta Labs in 2024. Its CEO, Dana Cruz, previously led Gamma Corp. The company now employs 400 people."},
            {"name": "entity_types", "type": "string", "description": "Comma-separated allowed entity types to restrict extraction. Leave empty to let the model infer types.", "required": False, "example": "organization, person, location, product"},
        ],
        "expected_output": {
            "format": "json",
            "sample": "{\"entities\":[{\"id\":\"acme_inc\",\"label\":\"Acme Inc.\",\"type\":\"organization\",\"aliases\":[\"Acme\",\"the company\",\"Its\"]},{\"id\":\"beta_labs\",\"label\":\"Beta Labs\",\"type\":\"organization\",\"aliases\":[]},{\"id\":\"dana_cruz\",\"label\":\"Dana Cruz\",\"type\":\"person\",\"aliases\":[\"CEO\"]},{\"id\":\"denver\",\"label\":\"Denver\",\"type\":\"location\",\"aliases\":[]}],\"relationships\":[{\"subject\":\"acme_inc\",\"predicate\":\"located_in\",\"object\":\"denver\",\"object_is_literal\":false,\"source_span\":\"Acme Inc., founded in Denver\",\"confidence\":0.95},{\"subject\":\"acme_inc\",\"predicate\":\"acquired\",\"object\":\"beta_labs\",\"object_is_literal\":false,\"source_span\":\"acquired Beta Labs in 2024\",\"confidence\":0.97},{\"subject\":\"dana_cruz\",\"predicate\":\"ceo_of\",\"object\":\"acme_inc\",\"object_is_literal\":false,\"source_span\":\"Its CEO, Dana Cruz\",\"confidence\":0.93}],\"unresolved_mentions\":[],\"build_caveats\":[\"'Its' resolved to acme_inc\"]}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strong coreference resolution to a single canonical id and disciplined source spans per edge."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best at predicate normalization and not duplicating nodes for the same entity across a long passage."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Good triple extraction; sometimes creates 'acme' and 'acme_inc' as two nodes — re-pin the one-id rule and provide entity_types."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Extracts obvious triples but coreference and dedupe degrade on longer text — restrict entity_types, keep passages short, and verify node uniqueness."},
        ],
        "variations": [
            {"label": "Cypher output", "description": "Emit Neo4j import statements.", "prompt_snippet": "In addition to the JSON, emit Cypher MERGE statements: MERGE nodes by id with label/type, then MERGE relationships with the predicate as the type. Use parameters, no literal injection."},
            {"label": "Schema-constrained", "description": "Restrict predicates too.", "prompt_snippet": "Only use predicates from this allowed list: {allowed_predicates}. Any relationship that doesn't map to one is dropped and noted in build_caveats — keep the graph schema closed."},
            {"label": "Incremental merge", "description": "Extend an existing graph.", "prompt_snippet": "You are given an existing 'entities' list. Reuse those ids for matching entities (don't mint new ids for things already present) and only add new entities/edges, flagging any id collisions."},
        ],
        "failure_modes": [
            {"symptom": "Creates two nodes ('acme', 'acme_inc') for the same entity.", "fix": "Re-pin: 'one canonical id per real-world entity; surface variants go in aliases, not as new nodes.'"},
            {"symptom": "Forces an edge from an ambiguous pronoun.", "fix": "Add: 'ambiguous pronoun -> do not form the edge; record it in unresolved_mentions/build_caveats.'"},
            {"symptom": "Uses inconsistent predicates (bought, acquired, purchased).", "fix": "Add: 'normalize predicates to one canonical snake_case verb; merge synonyms and note the mapping.'"},
            {"symptom": "Invents a relationship the text doesn't state.", "fix": "Hard rule: 'every edge needs a verbatim source_span; no span means the edge is not asserted and must be dropped.'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-06-10"},
        "related_prompt_slugs": ["structured-extraction-from-docs", "json-from-unstructured-text", "concept-map-builder"],
        "related_glossary_slugs": ["knowledge-graph", "named-entity-recognition", "structured-output", "graph-rag"],
        "related_tool_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What makes the output importable into a graph DB?", "answer": "Entities have stable canonical ids, types, and aliases; relationships are (subject id, predicate, object) triples with a literal flag and a source span. That maps directly to nodes and edges — and the Cypher variation emits MERGE statements for Neo4j."},
            {"question": "Why is coreference resolution emphasized so much?", "answer": "Because a graph is only useful if 'Acme', 'the company', and 'it' all point to one node. If the model mints a separate node per surface form, your graph fragments and queries miss connections. The one-canonical-id rule is the core of the prompt's value."},
            {"question": "Will it verify the relationships are true?", "answer": "No. It extracts what the text asserts, including any errors the source contains. Each edge carries a verbatim span so you can check the claim against the text, but verification against ground truth is a separate step."},
            {"question": "How do I keep the graph schema closed?", "answer": "Pass entity_types to restrict node types, and use the Schema-constrained variation to restrict predicates to an allowed list. Anything that doesn't fit is dropped and noted, so you don't get a sprawling ad-hoc schema."},
        ],
        "meta_title": "Entity-Relationship Graph Builder — Structured Output Prompt",
        "meta_description": "Extract knowledge-graph triples from text: canonical entity ids, coreference resolved, source span per edge, dedupe, confidence. Graph-DB import ready.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "agent-tool-error-recovery",
        "title": "Agent Tool-Error Recovery Controller",
        "tldr": "A controller for a failed agent tool call: given the error and history, it decides retry-as-is, retry-with-fixed-args, try-alternate-tool, ask-user, or abort — with a backoff note, anti-loop cap, and a rationale.",
        "category": "agents",
        "tags": ["agents", "tool-use", "error-recovery", "controller", "structured-output"],
        "best_for_tags": ["agent-builders", "platform-teams", "automation"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "API rate-limit handling", "example": "A tool returns 429 — decide to back off and retry-as-is with a delay, not switch tools."},
            {"scenario": "Bad-argument repair", "example": "A call failed validation — emit retry-with-fixed-args using corrected parameters."},
            {"scenario": "Tool fallback", "example": "Primary search API is down — try-alternate-tool with an equivalent search."},
            {"scenario": "Loop breaking", "example": "The same call failed three times identically — abort instead of looping forever."},
        ],
        "when_not_to_use": "Skip for one-shot calls with no fallback and no retry budget — the decision is trivially abort or ask-user. Treat its choice as advisory; a human or policy layer should gate destructive retries (payments, deletes) before the harness executes.",
        "full_prompt": """You are the error-recovery controller for a tool-using agent. A tool call just failed. Decide the single next action the harness should take. Be decisive, avoid loops, and output a structured decision the harness can execute directly.

INPUT
- Failed tool name: {tool_name}
- Error payload (status/message/body the tool returned): {error_payload}
- The arguments that were sent: {sent_args}
- Recent attempt history (prior calls + outcomes for this task): {attempt_history}
- Available alternate tools: {alternate_tools}
- Retry budget remaining (max attempts for this step): {retry_budget}

OUTPUT — return ONE JSON object, no prose outside it:

{
  "diagnosis": "<one line: what kind of failure this is — transient | bad_args | auth | not_found | rate_limit | tool_down | permanent | unknown>",
  "decision": "retry_as_is | retry_with_fixed_args | try_alternate_tool | ask_user | abort",
  "fixed_args": <object, only for retry_with_fixed_args; else null>,
  "alternate_tool": "<tool name, only for try_alternate_tool; else null>",
  "backoff": { "should_wait": false, "seconds": 0, "reason": "<e.g. 'honor Retry-After header', 'exponential 2^attempt'>" },
  "user_question": "<only for ask_user: the single clarifying question; else null>",
  "rationale": "<one line a human can audit>",
  "stop_condition_hit": false
}

DECISION RULES
- transient / rate_limit / tool_down (5xx, 429, timeout): retry_as_is WITH backoff. For 429 honor Retry-After if present; else exponential (2^attempt, capped). After repeated failures, escalate to try_alternate_tool or abort.
- bad_args (4xx validation, schema error, missing/typed field): retry_with_fixed_args — emit the corrected arguments in fixed_args. Only fix what the error indicates; don't blindly resend.
- auth (401/403): do NOT retry blindly. ask_user (re-auth/permission) or abort; never loop on auth failures.
- not_found / permanent (404 on a required resource, unsupported operation): try_alternate_tool if a real equivalent exists in {alternate_tools}; otherwise abort or ask_user. Do not retry_as_is.
- ANTI-LOOP: if {attempt_history} shows the SAME tool+args failed with the SAME error >= 2 times, do not retry_as_is again — change the arguments, switch tools, ask the user, or abort. Set stop_condition_hit=true.
- BUDGET: if {retry_budget} <= 0, you may only ask_user or abort.

CRITICAL RULES
- Exactly ONE decision. Populate only the field that decision needs (fixed_args / alternate_tool / user_question); others null.
- Detect repeated identical failures and STOP — never recommend an action that re-creates a known-failing call. Set stop_condition_hit when you break a loop or hit budget.
- Do not invent an alternate tool that isn't in {alternate_tools}.
- For destructive operations, prefer ask_user over an automatic retry.
- Output valid JSON only — no markdown fences, no text outside the object.

FAILED TOOL
{tool_name}

ERROR PAYLOAD
{error_payload}

Begin.""",
        "input_variables": [
            {"name": "tool_name", "type": "string", "description": "The name of the tool/function whose call failed.", "required": True, "example": "search_web"},
            {"name": "error_payload", "type": "string", "description": "What the tool returned on failure: HTTP status, error message, and/or response body.", "required": True, "example": "HTTP 429 Too Many Requests. Retry-After: 8. body: {\"error\":\"rate limit exceeded\"}"},
            {"name": "sent_args", "type": "string", "description": "The arguments that were sent in the failed call, as JSON or a labeled list.", "required": False, "example": "{\"query\":\"q3 revenue\",\"max_results\":50}"},
            {"name": "attempt_history", "type": "string", "description": "Recent prior calls and their outcomes for this task, so the controller can detect loops.", "required": False, "example": "attempt 1: search_web(q3 revenue) -> 429; attempt 2: search_web(q3 revenue) -> 429"},
            {"name": "alternate_tools", "type": "string", "description": "Available fallback tools the controller may switch to.", "required": False, "example": "search_news, internal_kb_search"},
            {"name": "retry_budget", "type": "string", "description": "Remaining retry attempts allowed for this step.", "required": False, "example": "1"},
        ],
        "expected_output": {
            "format": "json",
            "sample": "{\"diagnosis\":\"rate_limit\",\"decision\":\"retry_as_is\",\"fixed_args\":null,\"alternate_tool\":null,\"backoff\":{\"should_wait\":true,\"seconds\":8,\"reason\":\"honor Retry-After header\"},\"user_question\":null,\"rationale\":\"429 with Retry-After 8; one budget left so wait and retry once before falling back\",\"stop_condition_hit\":false}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Decisive single-action output and reliable loop detection from attempt_history; honors Retry-After and budget cleanly."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best at correct fixed_args repair (changing only what the error indicates) and at choosing ask_user over risky auto-retries."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong diagnosis; can over-favor retry_as_is on 4xx — re-pin the bad_args rule. JSON-only output reliable in structured mode."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Handles clear cases (429, 401); weaker loop detection and may suggest an alternate tool not in the list — keep anti-loop + 'no invented tools' rules loud."},
        ],
        "variations": [
            {"label": "Strict no-LLM-args", "description": "Controller can't fabricate args.", "prompt_snippet": "For retry_with_fixed_args, fixed_args may only DROP or CORRECT fields present in {sent_args} based on the error. Never add new fields the error didn't reference; if a required field's value is unknown, switch to ask_user."},
            {"label": "Severity + paging", "description": "Add ops escalation.", "prompt_snippet": "Add a 'severity' field (low/medium/high) and an 'escalate' boolean. Set escalate=true for repeated tool_down or auth failures so the harness can page an operator instead of looping."},
            {"label": "ReAct-step format", "description": "Emit as a thought/action step.", "prompt_snippet": "Wrap the decision as a ReAct step: a short 'thought' (the diagnosis + why), then 'action' = the decision and its single populated field. Keep it parseable by the agent loop."},
        ],
        "failure_modes": [
            {"symptom": "Retries the identical failing call forever.", "fix": "Re-pin the ANTI-LOOP rule: 'same tool+args+error >= 2 times -> never retry_as_is again; change args, switch, ask, or abort, and set stop_condition_hit=true.'"},
            {"symptom": "Blindly retries a 401/403 auth error.", "fix": "Add: 'auth failures never retry_as_is — ask_user to re-auth or abort.'"},
            {"symptom": "Suggests an alternate tool that doesn't exist.", "fix": "Hard rule: 'alternate_tool must be a member of {alternate_tools}; if none fits, abort or ask_user.'"},
            {"symptom": "Resends all original args on a bad_args error without fixing them.", "fix": "Require: 'retry_with_fixed_args must emit corrected arguments addressing the validation error, not a blind resend.'"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-06-10"},
        "related_prompt_slugs": ["react-agent-loop", "tool-calling-system-prompt", "agent-tool-discovery-and-selection"],
        "related_glossary_slugs": ["tool-use", "agent-loop", "agentic-ai", "function-calling"],
        "related_tool_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How does it avoid infinite retry loops?", "answer": "It reads attempt_history and, if the same tool+args produced the same error two or more times, it refuses to recommend retry_as_is again — switching arguments, trying an alternate tool, asking the user, or aborting, and setting stop_condition_hit=true. It also stops when retry_budget hits zero."},
            {"question": "How should backoff be applied?", "answer": "The controller emits a backoff object; your harness enforces the wait. For 429s it honors a Retry-After header when present and otherwise suggests capped exponential backoff (2^attempt). It does not sleep itself — it tells the harness how long to wait and why."},
            {"question": "Can it execute the retry itself?", "answer": "No, and that's intentional. It returns a single structured decision (with corrected args or an alternate tool) for your harness to execute, keeping a clean audit point. For destructive operations it prefers ask_user so a human gates the action."},
            {"question": "What if no alternate tool is available?", "answer": "It won't invent one. If {alternate_tools} has no real equivalent for a not_found/permanent failure, it aborts or asks the user rather than fabricating a tool name — which keeps the harness from calling something that doesn't exist."},
        ],
        "meta_title": "Agent Tool-Error Recovery Controller — Agents Prompt",
        "meta_description": "Controller for failed agent tool calls: decides retry, fix-args, alternate-tool, ask-user, or abort with backoff and anti-loop caps. Structured, harness-ready.",
        "version": "v2.0",
        "release_status": "stable",
    },
]
