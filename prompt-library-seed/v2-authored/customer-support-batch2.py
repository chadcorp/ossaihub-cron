"""Customer support prompts — batch 2."""

RECORDS = [
    {
        "slug": "support-macro-from-recurring-tickets",
        "title": "Support Macro From Recurring Tickets",
        "tldr": "Reads 5-15 similar support tickets and produces a reusable macro: the core message, three voice variants (formal/neutral/friendly), variables to fill in, and the edge cases the macro shouldn't be used for.",
        "category": "customer-support",
        "tags": ["macros", "templates", "support-ops", "scaling"],
        "best_for_tags": ["support-team-scaling", "knowledge-base", "automation"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Building macros for new product launch", "example": "After launch, 50 tickets ask the same thing — author one macro from those tickets."},
            {"scenario": "Onboarding new support reps", "example": "Existing macros + new tickets → updated macro library."},
            {"scenario": "Multi-channel deployment", "example": "Single macro authored once, three voice variants for email/chat/community forum."},
            {"scenario": "Quarterly macro audit", "example": "Review which existing macros are getting edited heavily — re-author with current voice."},
        ],
        "when_not_to_use": "Skip for single-instance issues — macros are for recurring. Skip for high-stakes situations (refunds, cancellations) — those need human judgment, not templates.",
        "full_prompt": """You are a senior support ops manager. You're authoring a reusable macro from recent similar tickets.

INPUT
- A set of recent tickets that look similar: {ticket_samples}
- Brand voice notes: {voice_notes}
- Constraints (what you can and can't promise): {policy_constraints}

OUTPUT

## 1. The recurring question
One sentence: what are these tickets ACTUALLY asking? (Not the surface words — the underlying need.)

## 2. Core message
The 1-2 sentence answer all variants will share. Plain, no voice tone yet.

## 3. Variables to fill in
List the placeholders the rep will substitute:
- {customer_name}
- {specific_thing_they_asked_about}
- etc.

## 4. Three voice variants

### Formal variant (~60-80 words)
For: emails to enterprise customers, post-incident communications.
Tone: measured, no contractions, slightly more structured.

### Neutral variant (~50-70 words)
For: standard email and ticketing tool replies.
Tone: clear, warm-but-businesslike, contractions OK.

### Friendly variant (~40-60 words)
For: in-app chat, community forums.
Tone: contractions, casual, an emoji is fine if culturally appropriate.

Each variant uses the same variables in the same positions, so reps can switch by channel without re-authoring.

## 5. When NOT to use this macro
3-5 cases where the macro would feel canned or harmful:
- Customer is angry — needs acknowledgment first
- Issue has unusual context that doesn't fit the standard answer
- Customer is on a different plan / segment than typical
- Escalation criteria met (named in policy)
- ...

## 6. Related macros and escalation paths
Macros for adjacent issues; when to route to engineering / billing / retention.

RULES
- Macros are STARTING POINTS for reps. They should always personalize.
- Don't promise anything outside the policy_constraints.
- If the recurring tickets reveal a product issue, FLAG IT in section 5 (this macro is paper over a real fix needed).
- Never include "I understand your frustration" or "Thanks for reaching out" as openers — too template-y; let rep choose.

RECENT TICKETS
{ticket_samples}

Begin.""",
        "input_variables": [
            {"name": "ticket_samples", "type": "string", "description": "5-15 similar support tickets (with redacted PII)", "required": True, "example": "Ticket 1: ‘Hi, my API keys aren't working after the upgrade...’\\nTicket 2: ‘API authentication broke when I upgraded to Pro plan...’"},
            {"name": "voice_notes", "type": "string", "description": "Brand voice guidance", "required": True, "example": "Warm but professional. Never apologize before acknowledging the issue. Avoid corporate-speak."},
            {"name": "policy_constraints", "type": "string", "description": "What can/can't be promised", "required": True, "example": "Cannot promise refund timing under 5 days. Cannot escalate to specific engineers by name. Can offer free migration help on enterprise plans only."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: recurring question, core message, variables, three voice variants, when NOT to use, related macros/escalation.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on the ‘underlying need’ distillation; voice variants stay distinct."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes friendly variant slips toward template-y openers — re-pin banned phrases."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; ‘when NOT to use’ section can be soft."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Variants can sound similar; require explicit voice differences (contractions, emoji, length)."},
        ],
        "variations": [
            {"label": "Multi-language", "description": "Generate macros in multiple languages.", "prompt_snippet": "Add: ‘produce the three voice variants in English + {target_languages}; preserve meaning, not literal translation.’"},
            {"label": "With chat-specific snippets", "description": "Pre-written chat shortcuts.", "prompt_snippet": "Add Section 7: ‘3-5 quick chat snippets (under 20 words each) for live chat — acknowledgment, hold, escalation.’"},
            {"label": "Product-issue flag", "description": "Surface when macros cover product gaps.", "prompt_snippet": "Add: ‘if the recurring issue indicates a product problem, write a 2-sentence summary suitable for engineering/product backlog.’"},
        ],
        "failure_modes": [
            {"symptom": "All three voice variants sound the same.", "fix": "Re-pin distinctness: formal=no contractions, friendly=contractions+emoji-ok. Show specific differences."},
            {"symptom": "Macro promises something outside policy.", "fix": "Add: ‘before final output, verify every promise is in policy_constraints; remove or soften violators.’"},
            {"symptom": "‘When NOT to use’ is empty or generic.", "fix": "Add: ‘at minimum 3 specific cases; ‘complicated situations’ doesn't count.’"},
            {"symptom": "Macro hides a product bug.", "fix": "Add: ‘if the recurring issue is actually a product problem, flag it in a separate ‘Product issue surfaced’ section.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["faq-from-tickets", "support-ticket-triage", "support-response-empathetic"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["support-macro", "knowledge-base"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should reps always use the macro verbatim?", "answer": "No — macros are starting points. The friendly variant especially expects reps to personalize the opener and closer. Verbatim macros sound robotic."},
            {"question": "How often should I refresh macros?", "answer": "Quarterly minimum. When product/policy changes, immediately. When CSAT drops on a macro-heavy issue type, immediately audit."},
            {"question": "When does the macro hide a product problem?", "answer": "If reps are sending the same macro 50+ times/week, fix the product. Macros that scale support volume on a recurring bug are technical debt with a smile."},
        ],
        "meta_title": "Support Macro From Recurring Tickets — Prompt",
        "meta_description": "Generate a reusable support macro from 5-15 similar tickets: core message + three voice variants + when NOT to use + escalation paths.",
    },
    {
        "slug": "support-knowledge-base-article-from-resolution",
        "title": "KB Article From a Solved Ticket",
        "tldr": "Turns a single solved support ticket into a public-facing knowledge base article — strips PII, generalizes to the audience, adds prerequisites, troubleshooting flowchart, and ‘still stuck?’ escalation.",
        "category": "customer-support",
        "tags": ["knowledge-base", "documentation", "support", "self-service"],
        "best_for_tags": ["help-center", "documentation", "deflection"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Convert top-volume tickets into self-serve articles", "example": "Solved ticket about API key rotation → KB article that deflects future tickets on this topic."},
            {"scenario": "Edge-case captures", "example": "Senior rep solves a tricky integration issue → article captures the solution before tribal knowledge fades."},
            {"scenario": "Sprint-cadence KB updates", "example": "Weekly: turn 3-5 solved tickets into KB articles."},
            {"scenario": "Localization seed", "example": "English article first, then translate; this prompt makes the English crisp enough to translate well."},
        ],
        "when_not_to_use": "Skip for one-off issues (article won't be useful). Skip when the solution involves internal admin actions only — those aren't user-visible.",
        "full_prompt": """You are converting a solved support ticket into a public knowledge-base article.

INPUT
- The solved ticket (rep + customer exchange, redacted of PII): {ticket}
- The resolution that worked: {resolution}
- Target audience: {audience}                          (free-tier users / power users / admins / developers)
- Product context: {product_context}

OUTPUT

## Article structure

### Title
A how-to question phrased the way a user would search:
- "How do I rotate my API keys?" (not "API key rotation procedure")
- "Why am I seeing rate limit errors?" (not "Rate limiting troubleshooting guide")

### TL;DR (1-2 sentences)
The one-paragraph answer for users who only read the top.

### Prerequisites
What the user must already have or know to follow the steps.
- Account / plan requirements
- Permissions / role
- Existing setup (e.g., "you've already created an API key")

### Steps
Numbered. Each step:
- One concrete action
- The expected result (so user knows it worked)
- A screenshot suggestion in [brackets] (you can't generate the screenshot but mark where one should go)

If steps branch (e.g., "if you're on the Pro plan, go to X; otherwise Y"), use sub-numbering.

### Troubleshooting
2-4 things that go wrong + how to recognize + how to fix:

| Symptom | Likely cause | Fix |

### Still stuck?
Direct escalation: how to contact support, what info to include.

### Related articles
2-4 adjacent articles users might also need.

RULES
- Strip ALL PII from the original ticket (names, emails, account IDs, etc.).
- Generalize the resolution — the original ticket had ONE customer's situation; the article serves many.
- Steps must be ordered correctly; users follow them top-to-bottom.
- Don't include internal jargon or tool names users wouldn't know.
- Tone matches help-center conventions: warm, direct, not chatty.
- Each step has a SUCCESS criterion (how the user knows they did it right).

INPUT

Ticket:
{ticket}

Resolution that worked:
{resolution}

Audience:
{audience}

Product context:
{product_context}

Begin.""",
        "input_variables": [
            {"name": "ticket", "type": "string", "description": "The full solved ticket exchange (PII redacted)", "required": True, "example": "[Customer]: My API keys broke after I upgraded plans. [Rep]: Let me check... I see your plan changed. Try regenerating from Settings → API Keys → Regenerate. [Customer]: That worked, thanks!"},
            {"name": "resolution", "type": "string", "description": "The specific resolution steps that worked", "required": True, "example": "Plan change voids existing keys. Customer needs to regenerate from Settings → API Keys → Regenerate. New keys take ~30 sec to propagate."},
            {"name": "audience", "type": "string", "description": "Who reads the article", "required": True, "example": "Developers using our API"},
            {"name": "product_context", "type": "string", "description": "Product info needed for the article", "required": False, "example": "B2B SaaS API platform. Plans: Free, Pro, Enterprise. Plan changes regenerate API keys for security."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Title, TL;DR, prerequisites, numbered steps with success criteria, troubleshooting table, still-stuck contact, related articles.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong PII stripping and accurate generalization."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally leaves overly specific phrasing — re-pin generalization."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; troubleshooting table can be thin."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Sometimes leaves PII; double-check before publishing."},
        ],
        "variations": [
            {"label": "Video-script companion", "description": "Produce a 60-second video script alongside.", "prompt_snippet": "Add: ‘also output a 60-second video script (5-7 spoken sentences) covering the same steps for users who prefer video.’"},
            {"label": "Multi-difficulty", "description": "Produce beginner + advanced versions.", "prompt_snippet": "Add: ‘in addition, produce an ‘advanced’ version that compresses the steps for power users who already know the basics.’"},
            {"label": "Schema.org HowTo markup", "description": "Generate JSON-LD for SEO.", "prompt_snippet": "Add: ‘also output Schema.org HowTo JSON-LD block for SEO.’"},
        ],
        "failure_modes": [
            {"symptom": "PII leaks into the article.", "fix": "Re-pin: ‘strip ALL PII; if a name/email/ID appears in output, that's a P0 bug.’"},
            {"symptom": "Steps assume the user already knows X.", "fix": "Force prerequisites section to be specific — what plan, what role, what existing setup."},
            {"symptom": "Title is wordy.", "fix": "Add: ‘title is the question a user would type into search — short and natural.’"},
            {"symptom": "Article duplicates an existing one.", "fix": "Before generating, ask: ‘provide existing KB articles for this product area; merge or supersede rather than duplicating.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["faq-from-tickets", "support-macro-from-recurring-tickets"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["knowledge-base", "self-service"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Will the article actually deflect tickets?", "answer": "Only if it's discoverable (SEO + in-app help search) and accurate. Track deflection by tagging tickets that ‘found this article first’ vs ‘didn't find it.’"},
            {"question": "How long should articles be?", "answer": "As short as the answer allows. Most issues are 5-10 step articles. If yours is 30+ steps, probably 3 articles."},
            {"question": "Localization?", "answer": "Translate after the English is solid. Use the localized-translation prompt; preserve step numbering and screenshot markers across languages."},
        ],
        "meta_title": "KB Article From a Solved Ticket — Prompt",
        "meta_description": "Turn a solved support ticket into a public KB article: TL;DR, prerequisites, numbered steps with success criteria, troubleshooting, escalation.",
    },
    {
        "slug": "support-csat-recovery-response",
        "title": "CSAT-Recovery Response After Bad Score",
        "tldr": "Drafts a low-CSAT recovery message: acknowledges without grovelling, asks one diagnostic question, frames for relationship recovery — not score reversal.",
        "category": "customer-support",
        "tags": ["csat", "customer-recovery", "support", "retention"],
        "best_for_tags": ["retention", "post-resolution", "feedback-loop"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Auto-trigger after low CSAT survey", "example": "Customer leaves 2/5 → personalized recovery message within 24 hours."},
            {"scenario": "Manager review of low-scored interactions", "example": "Manager drafts the follow-up before deciding to handle directly."},
            {"scenario": "Bulk recovery campaign post-incident", "example": "After widespread outage with CSAT drops, base recovery template + personalized hooks."},
            {"scenario": "Account manager outreach", "example": "AM informed of low CSAT; sends a thoughtful follow-up message."},
        ],
        "when_not_to_use": "Skip when the customer explicitly asked for no follow-up. Skip when the underlying issue is unresolved — fix the issue first, message after. Don't message a customer whose anger you'd amplify.",
        "full_prompt": """You are drafting a CSAT-recovery response to a customer who left a low score.

INPUT
- Customer name / role: {customer_name_role}
- The interaction context: {interaction_context}
- Customer's CSAT score + comment (if any): {score_comment}
- What you've learned about why: {known_or_inferred_cause}
- Account/relationship context: {account_context}
- Brand voice constraints: {voice_notes}

OUTPUT — ONE MESSAGE, 100-150 WORDS

## Structure

1. OPENING (1 sentence). Name the score. Don't grovel; acknowledge it.
   Bad: "I'm so sorry to see you weren't happy!"
   Good: "I saw your 2/5 on Thursday's ticket and wanted to follow up directly."

2. ACKNOWLEDGMENT (1-2 sentences). Specifically what you understand was frustrating. Be concrete; vague apology reads template.

3. ONE DIAGNOSTIC QUESTION (1 sentence). What you actually need to know to make it right. Open-ended; not "did we resolve it?" — something that surfaces real diagnosis.

4. WHAT WE'RE DOING (1-2 sentences). Something CONCRETE. Not "we take feedback seriously" — a specific action you're taking now, even if it's just "I've passed your note to the support lead who reviewed Thursday's case."

5. CLOSING (1 sentence). An offer of next step. Reply, call, escalation path. No "have a great day" filler.

RULES
- Don't ask the customer to update the CSAT score. Score is downstream of the experience.
- Don't promise something you can't deliver.
- Match their register: angry & concise? Mirror it. Polite & detailed? Mirror it.
- Use their name once, naturally — not three times.
- 100-150 words. Long messages signal corporate-process; short signals attention.

BANNED PHRASES (these mark CSAT-recovery messages as automated):
- "Thanks for your valuable feedback"
- "I'm really sorry to hear"
- "We take this very seriously"
- "Your satisfaction is our top priority"
- "Please give us another chance"

INPUT
Customer: {customer_name_role}
Context: {interaction_context}
Score & comment: {score_comment}
Known cause: {known_or_inferred_cause}
Account context: {account_context}
Voice: {voice_notes}

Now write the message.""",
        "input_variables": [
            {"name": "customer_name_role", "type": "string", "description": "Customer name + role/title", "required": True, "example": "Jane Doe, Director of Data Engineering at Acme Corp"},
            {"name": "interaction_context", "type": "string", "description": "What the ticket was about", "required": True, "example": "Reported API rate-limiting issues; took 3 days to resolve due to misrouted ticket."},
            {"name": "score_comment", "type": "string", "description": "Score and customer's written comment", "required": True, "example": "2/5. Comment: ‘took way too long to get answers’"},
            {"name": "known_or_inferred_cause", "type": "string", "description": "Why the experience was bad", "required": True, "example": "Ticket misrouted to wrong team for 48 hours; customer received boilerplate replies during that time."},
            {"name": "account_context", "type": "string", "description": "Account / relationship info", "required": False, "example": "Enterprise customer, $80k ARR, renewal in 4 months, primary contact for past 2 years."},
            {"name": "voice_notes", "type": "string", "description": "Voice constraints", "required": False, "example": "Direct, no corporate-speak. We can offer a 20-min call with the engineering lead. Cannot offer credits or refunds."},
        ],
        "expected_output": {
            "format": "text",
            "sample": "100-150 word message with opening, acknowledgment, one diagnostic question, concrete action, closing offer.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong avoidance of banned phrases; concrete actions, not platitudes."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can slip into ‘sincere apologies for...’ — re-pin banned phrases."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; sometimes asks for score update — explicitly forbid."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Defaults to over-apologetic; needs constant pinning."},
        ],
        "variations": [
            {"label": "Manager-from", "description": "Sent from a manager, not the original rep.", "prompt_snippet": "Add: ‘this is from the support manager, not the original rep. Tone: I read your interaction directly and want to make sure we got it right.’"},
            {"label": "With concession", "description": "Includes an actual offered concession.", "prompt_snippet": "Add: ‘include one concrete concession (credit, dedicated point of contact, expedited escalation) — name it specifically.’"},
            {"label": "Post-major-incident", "description": "After a widespread issue.", "prompt_snippet": "Add: ‘context is a multi-customer incident; acknowledge it was systemic, share the actual root cause briefly, share what's changed.’"},
        ],
        "failure_modes": [
            {"symptom": "Asks customer to update CSAT score.", "fix": "Re-pin: ‘never ask for score update; that's a process problem masquerading as customer recovery.’"},
            {"symptom": "Generic ‘we take this seriously’ language.", "fix": "Banned-phrases list active; tighten if needed."},
            {"symptom": "Multiple questions in the message.", "fix": "Add: ‘exactly ONE diagnostic question. The customer is already frustrated — don't add cognitive load.’"},
            {"symptom": "Message is 250+ words.", "fix": "Hard cap 100-150. Long apologies feel corporate."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["support-response-empathetic", "escalation-classifier"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["csat", "customer-recovery"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Will this fix the score?", "answer": "No, and don't expect it to. The goal is relationship, not metric. If you fix the underlying issue, future scores will reflect it."},
            {"question": "Should we always reach out on low CSAT?", "answer": "On low scores from accounts that matter (paid, multi-month tenure): yes. On free-tier or one-off complaints: don't waste rep time."},
            {"question": "What about customers who left no comment?", "answer": "Lead with the diagnostic question — ‘we got a low score with no comment; we'd genuinely like to know what we missed.’ Often surfaces the real issue."},
        ],
        "meta_title": "CSAT-Recovery Response After Bad Score — Prompt",
        "meta_description": "Draft a 100-150 word recovery message: acknowledge without grovelling, ask one diagnostic question, name a concrete action.",
    },
    {
        "slug": "billing-dispute-deescalation",
        "title": "Billing Dispute De-Escalation Response",
        "tldr": "Drafts a response to a billing dispute that acknowledges the charge issue, explains the policy concisely, and offers a clear next-step path — without sounding defensive or robotic.",
        "category": "customer-support",
        "tags": ["billing", "dispute", "de-escalation", "policy"],
        "best_for_tags": ["billing-support", "retention", "policy-explanation"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Customer disputes a charge they didn't recognize", "example": "Most likely they forgot a renewal — response explains kindly without making them feel stupid."},
            {"scenario": "Refund request outside policy window", "example": "Acknowledge the request, explain the window, offer an alternative (credit, prorated)."},
            {"scenario": "Duplicate charge appeared", "example": "Verify, refund, explain why duplicates happen, prevent escalation to chargeback."},
            {"scenario": "Plan-tier confusion", "example": "Customer thought they were on a cheaper plan; explain billing, offer to apply downgrade going forward."},
        ],
        "when_not_to_use": "Skip when the dispute is clearly fraud (escalate to security). Skip when customer is in legal/chargeback territory — that needs legal/finance review, not a recovery message.",
        "full_prompt": """You are responding to a billing dispute. Goal: resolve the issue, preserve the relationship, avoid chargeback.

INPUT
- Customer message: {customer_message}
- Account billing history (relevant facts): {billing_facts}
- Policy that applies: {applicable_policy}
- What you can offer: {available_remedies}                  (refund, credit, plan change, etc. — your authority)
- Brand voice constraints: {voice_notes}

OUTPUT — ONE EMAIL, 150-200 WORDS

## Structure

1. OPEN with acknowledgment of the specific charge / event. Don't start with "Thanks for your message." Start with the facts.
2. SHARE WHAT YOU SEE in the account — neutral, specific. ("On April 12, we processed your annual renewal of $599 against the card ending 4242.")
3. EXPLAIN the policy in 1-2 sentences. Not legalese — the human version.
4. ACKNOWLEDGE the discomfort. ("I get that an unexpected charge is jarring.") Brief; one line max.
5. OFFER the path forward. Name the specific remedy you can extend. If none available, offer the next-best (e.g., credit on next renewal, plan change going forward).
6. CLOSE with one clear next step. ("Reply with ‘yes, refund’ and I'll process today" or "Want me to switch you to Pro Monthly going forward?")

RULES
- Don't apologize for the policy. The policy exists; explain it without defensiveness.
- Don't blame the customer ("you should have known the renewal date").
- Don't promise something outside available_remedies.
- Be specific with numbers and dates from billing_facts.
- Match tone to message: angry customer gets shorter, sharper response. Confused customer gets gentler.
- Never include "I understand this can be frustrating" as a standalone. Acknowledge the specific frustration.

BANNED PHRASES
- "We appreciate your business"
- "Please note that"
- "Per our terms of service"
- "Unfortunately, our policy is"
- "As a one-time courtesy"

INPUT

Customer message:
{customer_message}

Billing facts:
{billing_facts}

Policy:
{applicable_policy}

Available remedies:
{available_remedies}

Voice:
{voice_notes}

Now write the email.""",
        "input_variables": [
            {"name": "customer_message", "type": "string", "description": "The customer's billing dispute", "required": True, "example": "Hi - I just saw a $599 charge on my card from your company. I don't recognize it. Please refund immediately."},
            {"name": "billing_facts", "type": "string", "description": "Relevant billing history", "required": True, "example": "Customer signed up April 12 2024 on annual plan ($599/year). Auto-renewal April 12 2026. Renewal notice email sent April 5 2026. Card ending 4242."},
            {"name": "applicable_policy", "type": "string", "description": "Relevant policy", "required": True, "example": "Annual plan auto-renews unless canceled before renewal date. Refund window is 7 days from renewal charge for plan-tier downgrades."},
            {"name": "available_remedies", "type": "string", "description": "What can be offered", "required": True, "example": "Full refund if within 7 days (currently day 5). Plan change to monthly going forward. Cannot prorate."},
            {"name": "voice_notes", "type": "string", "description": "Voice constraints", "required": False, "example": "Direct, no defensiveness. We absolutely want to honor the refund — don't make them feel bad about it."},
        ],
        "expected_output": {
            "format": "text",
            "sample": "150-200 word email with 6 sections: acknowledge, share facts, explain policy briefly, brief empathy, offer path, clear next step.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on the ‘policy without defensiveness’ balance."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes opens with ‘Thank you for reaching out’ — call out banned phrase list."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; tends to under-explain remedies — re-pin specificity."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Defaults to formal corporate tone; needs explicit voice direction."},
        ],
        "variations": [
            {"label": "Chargeback-imminent variant", "description": "When customer threatened chargeback.", "prompt_snippet": "Add: ‘customer mentioned chargeback. Lead with the remedy, not the policy. Don't reference chargeback in your reply — just resolve.’"},
            {"label": "Enterprise customer", "description": "For B2B with account manager.", "prompt_snippet": "Add: ‘this is enterprise with named account manager. Cc the AM. Tone is more measured; offer a 15-min call to discuss going forward.’"},
            {"label": "Post-refund follow-up", "description": "After refund processed.", "prompt_snippet": "Replace structure with: ‘refund already issued; this is the confirmation message. Confirm refund details, summarize what happened, share how we'll prevent it next time.’"},
        ],
        "failure_modes": [
            {"symptom": "Defensive about policy.", "fix": "Add: ‘policy is information; share it without justifying or apologizing.’"},
            {"symptom": "Blames customer ‘you should have’.", "fix": "Re-pin: ‘never frame as customer's fault, even if technically true.’"},
            {"symptom": "Offers something outside available_remedies.", "fix": "Add: ‘before sending, verify every offer is in available_remedies; remove violators.’"},
            {"symptom": "Closes without clear next step.", "fix": "Force: ‘the close must contain a specific instruction or question that drives the next reply.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["refund-policy-decision", "escalation-classifier"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["billing-dispute", "chargeback"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What if I can't offer ANY remedy?", "answer": "Then the email is harder. Explain the policy clearly without apology, offer the closest-adjacent help (account credit, plan optimization, future check-in). Don't fake remedies you don't have."},
            {"question": "When to escalate vs respond?", "answer": "Escalate: amount > $X (your threshold), chargeback mentioned, customer is enterprise, or policy is ambiguous. Otherwise respond directly."},
            {"question": "How fast should this go out?", "answer": "Same business day if possible. Billing disputes intensify with time and can spiral to chargebacks. Speed matters more than polish."},
        ],
        "meta_title": "Billing Dispute De-Escalation Response — Prompt",
        "meta_description": "Draft a 150-200 word billing dispute reply: acknowledge specific charge, explain policy without defensiveness, offer concrete remedy with next step.",
    },
]
