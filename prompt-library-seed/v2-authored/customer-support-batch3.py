"""Customer support prompts — batch 3."""

RECORDS = [
    {
        "slug": "ticket-deflection-faq-suggestion",
        "title": "Ticket Deflection: Suggest Existing FAQ",
        "tldr": "Match an incoming ticket against existing FAQ articles and suggest the top 1-3 that likely answer it. Deflect or route to a rep with the rejected FAQs noted.",
        "category": "customer-support",
        "tags": ["deflection", "faq", "self-service", "routing"],
        "best_for_tags": ["help-center", "ticket-deflection", "scale"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Pre-submit deflection", "example": "User typing ticket; auto-suggest 3 FAQs matching their query. Deflects 30-50% of common questions."},
            {"scenario": "Auto-reply with suggestions", "example": "Ticket submitted; auto-reply within 30s with top 3 FAQs + 'reply if these don't solve it'."},
            {"scenario": "Triage with prior knowledge", "example": "Rep sees ticket WITH the FAQs the user already saw and rejected; skips the obvious answer."},
            {"scenario": "Knowledge gap discovery", "example": "Tickets where NO FAQ matched well = candidate topics for new FAQ articles."},
        ],
        "when_not_to_use": "Skip for emotional or escalated tickets (auto-suggest feels dismissive). Skip when the FAQ library is thin (irrelevant suggestions hurt trust).",
        "full_prompt": """You are matching a customer ticket against existing FAQ articles. Suggest the top 1-3 that likely answer the question.

INPUT
- Customer's ticket text: {ticket}
- Available FAQ articles (id, title, summary): {faq_index}
- Customer tier (if known): {tier}

OUTPUT (JSON)
{
  "suggested_faqs": [
    {"id": "faq-id", "title": "...", "match_confidence": 0.0-1.0, "why_it_matches": "1 line explanation"},
    ...
  ],
  "no_good_match": true|false,
  "if_no_match_route_to": "billing | technical | account | retention | other",
  "tone_signal": "neutral | frustrated | confused | escalated",
  "deflection_recommended": true|false
}

RULES
1. Suggest at most 3 FAQs, ranked by match_confidence (highest first).
2. Only suggest FAQs with confidence > 0.5. If nothing crosses that, set no_good_match=true and skip the array.
3. NEVER suggest a generic "contact support" FAQ — defeats the purpose.
4. Match on UNDERLYING question, not surface keywords. ("My card was declined" might match "Why was my payment refused" even though different words.)
5. tone_signal: detect emotional state. If escalated → deflection_recommended=false (route to human immediately, don't try FAQ).
6. why_it_matches: must reference SPECIFIC overlap between ticket and FAQ. Vague matching is worse than no suggestion.

ANTI-PATTERNS
- Suggesting tangentially-related FAQs to inflate hit rate
- Ignoring tone (an angry customer doesn't want self-help links)
- Recommending deflection when the question is account-specific (which FAQ can't answer)

TICKET
{ticket}

FAQ INDEX
{faq_index}

Output JSON only.""",
        "input_variables": [
            {"name": "ticket", "type": "string", "description": "Customer's ticket text", "required": True, "example": "I tried to upgrade to Pro last night but my card got declined three times. I called my bank — they say everything's fine on their end. What's wrong?"},
            {"name": "faq_index", "type": "string", "description": "List of FAQ articles with id, title, summary", "required": True, "example": "faq-001: 'Why was my payment declined?' — Common reasons + retry steps. faq-002: 'How to upgrade plans' — UI walkthrough..."},
            {"name": "tier", "type": "string", "description": "Customer tier", "required": False, "example": "Pro trial"},
        ],
        "expected_output": {
            "format": "json",
            "schema": "{ suggested_faqs[], no_good_match, if_no_match_route_to, tone_signal, deflection_recommended }",
            "sample": "{\n  \"suggested_faqs\": [\n    {\"id\":\"faq-001\",\"title\":\"Why was my payment declined?\",\"match_confidence\":0.87,\"why_it_matches\":\"Ticket describes card decline despite bank confirming OK — FAQ covers exactly this case (3DS friction, AVS mismatch).\"}\n  ],\n  \"no_good_match\": false,\n  \"if_no_match_route_to\": \"billing\",\n  \"tone_signal\": \"frustrated\",\n  \"deflection_recommended\": true\n}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong tone detection; honest about no-good-match."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can over-suggest weak matches — re-pin >0.5 threshold."},
            {"model": "gpt-4o-mini", "compatibility": "good", "notes": "Cheap option for high-volume; verify on edge cases."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Fast + cheap; weaker on tone nuance."},
        ],
        "variations": [
            {"label": "Multi-language", "description": "Match across languages.", "prompt_snippet": "Add: ‘ticket may be in any language; FAQs may be in different language. Cross-language match is allowed; note language pair in why_it_matches.’"},
            {"label": "Account-context aware", "description": "Include account state in match.", "prompt_snippet": "Add input: account_state (plan, last_activity, recent_errors). Suggest FAQs that match BOTH ticket + account context."},
            {"label": "A/B test suggestions", "description": "Surface 2 distinct angle suggestions.", "prompt_snippet": "Always return at least 2 suggestions IF the ticket is ambiguous; mark angle (e.g., 'billing-angle', 'auth-angle')."},
        ],
        "failure_modes": [
            {"symptom": "Suggests generic FAQ that doesn't actually answer.", "fix": "Re-pin: ‘why_it_matches must reference SPECIFIC overlap; vague match is rejected.’"},
            {"symptom": "Recommends deflection on escalated tickets.", "fix": "Add: ‘if tone_signal=escalated, deflection_recommended must be false.’"},
            {"symptom": "Confidence always >0.7.", "fix": "Add: ‘confidence below 0.5 → skip the FAQ entirely; calibration test: half your suggestions should be 0.5-0.8 range.’"},
            {"symptom": "Misses account-specific questions.", "fix": "Add: ‘if ticket references customer-specific account state (\"my account\", \"my plan\"), FAQ can't answer alone — set deflection_recommended=false.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gpt-4o-mini", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["support-ticket-triage", "support-knowledge-base-article-from-resolution", "support-macro-from-recurring-tickets"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["ticket-deflection", "self-service"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Won't customers just bypass the suggestions?", "answer": "30-50% of common questions deflect. Heavy-context or angry tickets won't. That's fine — humans handle those. The deflection saves rep capacity for tickets that genuinely need a person."},
            {"question": "What confidence threshold for auto-display?", "answer": "0.7+ for auto-reply suggestions; 0.5+ for the rep's reference view. Tune from your match-vs-helpful-rate data after a month."},
            {"question": "How does this beat keyword search?", "answer": "Underlying-question matching catches paraphrases keyword search misses. Combine: keyword search for fast filter, this prompt for ranking + tone gate."},
        ],
        "meta_title": "Ticket Deflection: Suggest Existing FAQ — Prompt",
        "meta_description": "Match incoming tickets to existing FAQ articles with confidence + tone gating. Auto-deflect 30-50% of common questions safely.",
    },
    {
        "slug": "vip-customer-escalation-protocol",
        "title": "VIP Customer Escalation Protocol",
        "tldr": "Drafts an escalation handoff when a VIP customer's issue exceeds the front-line rep's authority — preserves context, names the request, attaches the relevant account history, and signals urgency without theatrics.",
        "category": "customer-support",
        "tags": ["escalation", "vip", "handoff", "high-touch"],
        "best_for_tags": ["enterprise-support", "account-management", "retention"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Enterprise account stuck on a problem >24h", "example": "Front-line rep can't unblock; this prompt builds the escalation packet for the named CSM/AM."},
            {"scenario": "Multi-stakeholder issue", "example": "Customer's IT, security, and procurement all involved; one well-structured escalation summarizes for the receiving team."},
            {"scenario": "Pre-renewal friction", "example": "Customer with renewal in 30 days hits an issue; route to retention BEFORE it becomes a churn risk."},
            {"scenario": "Executive complaint", "example": "C-level customer escalates publicly (Twitter, LinkedIn); this prompt drafts the internal handoff to the exec sponsor."},
        ],
        "when_not_to_use": "Skip for ordinary tickets — escalation overhead is wasted. Skip when the receiving team is unclear (figure that out FIRST). Skip when issue is genuinely unresolvable (set expectations honestly instead).",
        "full_prompt": """You are drafting a VIP escalation packet. The receiver is a named CSM/AM/exec who's busy and needs to act fast.

INPUT
- Customer details: {customer_info}                (account name, primary contact, tier, ARR if known)
- Issue summary (from prior tickets/conversation): {issue_summary}
- What's already been tried: {prior_attempts}
- What we need from the receiver: {requested_action}
- Internal context (politics, history): {internal_context}
- Receiver's role: {receiver_role}

OUTPUT (escalation packet, ~250-400 words)

## Subject line
- Format: `[ESCALATION] <Customer> — <specific issue> — needs <action> by <when>`
- Specific. NOT "Urgent: please help".

## TL;DR (2 sentences)
What's the situation and what's the ask.

## Account context (bullets)
- Account name + tier + ARR
- Primary contact + recent interactions
- Renewal date (if relevant)
- Any prior escalations (relevant pattern?)

## What's happening
3-5 sentence narrative. Time-stamped. What changed, who's involved, where we are now.

## What we've tried
Numbered list. Each: what was attempted, what was the response, why it didn't resolve. Be honest — receiver can tell when escalation skipped steps.

## What we're asking
Specific. Examples:
- "Approve refund of $X" (with reasoning)
- "Have engineering investigate bug ID Y"
- "Call the customer at <phone> by <time>"
- "Sign off on credit/concession"

## Risk if not actioned by
Specific timing + specific risk. ("If not resolved by EOD Friday, customer threatens public review/legal action/non-renewal.")

## What I've already prepared
Anything ready to ship the moment the receiver approves. ("Refund authorization drafted, awaiting your sign-off.")

CRITICAL RULES
- Tone: matter-of-fact, no panic. VIP escalations DO need to flow but theatrics undermine credibility.
- Don't blame other teams in the writeup; describe what happened, not who failed.
- Estimate the receiver's TIME COST. If your ask costs them 30 min, name that explicitly so they can plan.
- If the customer's request is unreasonable, say so plainly + recommend a reasonable counter.

ESCALATION INPUTS
{customer_info}

{issue_summary}

{prior_attempts}

{requested_action}

{internal_context}

Now draft the packet.""",
        "input_variables": [
            {"name": "customer_info", "type": "string", "description": "Customer account details", "required": True, "example": "Acme Corp — Enterprise tier — $240k ARR — Primary contact Jane Doe (VP Eng), renewal 2026-06-15"},
            {"name": "issue_summary", "type": "string", "description": "What's happening", "required": True, "example": "API rate limiting impacting their production traffic. Started 4 days ago. Severity 1 from their side."},
            {"name": "prior_attempts", "type": "string", "description": "What's been tried", "required": True, "example": "1. Increased rate limits manually 2x. 2. Engineering investigated; suspect a config drift on their tenant. 3. Customer's own debugging suggests cache invalidation issue."},
            {"name": "requested_action", "type": "string", "description": "What we need from receiver", "required": True, "example": "Engineering manager approval to do a tenant-specific config reset (requires ops change window)."},
            {"name": "internal_context", "type": "string", "description": "Politics/history", "required": False, "example": "This customer's renewal is contingent on the platform performing reliably. CSM mentioned hesitation in last call."},
            {"name": "receiver_role", "type": "string", "description": "Receiver's role", "required": True, "example": "VP of Engineering"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Subject + TL;DR + account context + narrative + tried-list + ask + risk + prepared.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Matter-of-fact tone holds; no theatrics."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes adds unnecessary urgency words — call out the no-theatrics rule."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; receiver-cost estimate often missing."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for routine escalations; thin on internal-context nuance."},
        ],
        "variations": [
            {"label": "Multi-receiver", "description": "Same packet to CSM + AM + exec.", "prompt_snippet": "Add: ‘also produce a 50-word version for the exec sponsor (skim-friendly) + a 30-word Slack-style alert for the on-call.’"},
            {"label": "Customer-facing companion", "description": "Draft the customer-facing message in parallel.", "prompt_snippet": "Add Section: ‘also draft the message we'll send to the CUSTOMER acknowledging escalation — same facts, different tone (reassuring not internal).’"},
            {"label": "Templates by trigger", "description": "Pre-formatted by trigger.", "prompt_snippet": "Add: ‘categorize trigger (technical / billing / contract / public-complaint); each has a slightly different structure — apply the matching template.’"},
        ],
        "failure_modes": [
            {"symptom": "Theatrical urgency (multiple ‘URGENT’, all-caps).", "fix": "Re-pin: ‘no theatrics; the structured format is the urgency signal.’"},
            {"symptom": "Blames other teams.", "fix": "Add: ‘describe what happened, not who failed. Receiver can read between the lines.’"},
            {"symptom": "Ask is vague (‘please help’).", "fix": "Force: ‘ask must be specific: approve X, call Y, decide Z — with timing.’"},
            {"symptom": "Receiver's time-cost not estimated.", "fix": "Add: ‘name the receiver's time cost so they can plan; ‘30 min review’ or ‘1 quick call’ etc.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["escalation-classifier", "billing-dispute-deescalation", "support-csat-recovery-response"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["escalation", "enterprise-support"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "When is escalation premature?", "answer": "When obvious next steps in the front-line process haven't been tried. Receiver shouldn't have to ask ‘did you check X yet?’ — the tried-list must show due diligence."},
            {"question": "Should every VIP escalate?", "answer": "No. VIPs get faster service, not auto-escalation. Escalate when the resolution genuinely requires authority/expertise beyond front-line."},
            {"question": "What if the receiver doesn't respond?", "answer": "Set a clear secondary contact + escalation-of-escalation path BEFORE you need it. ‘If you can't action by Friday EOD, this goes to <named exec> per our SLA.’"},
        ],
        "meta_title": "VIP Customer Escalation Protocol — Prompt",
        "meta_description": "Draft a VIP escalation packet: subject, TL;DR, account context, what's tried, specific ask, risk-if-not-actioned. No theatrics.",
    },
    {
        "slug": "support-chatbot-handoff-to-human",
        "title": "Chatbot Handoff To Human (With Context)",
        "tldr": "Generates the bridge message + structured handoff context when a support chatbot decides to escalate to a human rep — what's been tried, customer's actual question, signals the rep should know.",
        "category": "customer-support",
        "tags": ["chatbot", "handoff", "context-transfer", "ai-support"],
        "best_for_tags": ["chatbot-builders", "support-automation", "rep-tooling"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Chatbot detects emotional escalation", "example": "Customer types in caps + 'I want to cancel' → bot routes to human with full conversation summary + escalation flag."},
            {"scenario": "Bot can't answer after 3 attempts", "example": "Asked 3 clarifying questions, still doesn't understand → escalate with what it DID figure out."},
            {"scenario": "Account-specific question outside bot's knowledge", "example": "Bot recognizes 'this needs account-level access' → route with the account ID and inferred intent."},
            {"scenario": "VIP customer detected", "example": "Bot detects high-value account; route to senior rep with full chat history + LTV signal."},
        ],
        "when_not_to_use": "Skip when the bot doesn't have account context (handoff signals will be weak). Skip for purely synchronous chat where the human is always present.",
        "full_prompt": """You are a chatbot deciding to hand off to a human rep. Generate the bridge message + structured context packet.

INPUT
- Full chat transcript so far: {transcript}
- Reason for handoff: {handoff_reason}                (one of: cant_resolve, emotional, account_specific, vip, explicit_request, complex)
- Customer account info (if available): {account_info}
- Expected wait time for human: {wait_seconds}

OUTPUT (two parts)

## Part 1: Message TO THE CUSTOMER

A short (1-3 sentence) bridge:
- Acknowledge the limit. Don't apologize for the bot — describe what's happening.
- Tell them what's next. Specific. ("Connecting you to a billing specialist — usually ~3 min wait.")
- DON'T over-promise. Don't say "they'll fix it right away" — they might escalate further.

NEVER:
- Use "Let me transfer you" (bot can't, you're a bot)
- Apologize for "any inconvenience" (cliché)
- Make the customer re-explain ("they'll have all my context, right?")

## Part 2: Context packet FOR THE REP

```
[HANDOFF PACKET — generated <timestamp>]
Reason: <handoff_reason from input>
Customer: <name + tier + LTV signal>
Channel: <chat>
Conversation summary (3 bullets):
- <key thing customer said>
- <what bot tried>
- <where it broke down>

Customer's CURRENT specific ask:
<one-sentence as the bot understands it>

What bot already verified:
- <e.g., "Confirmed account exists and is active">
- <e.g., "Pulled latest invoice — was charged $X on date Y">

What bot did NOT verify:
- <e.g., "Did not confirm if 3DS challenge was completed">
- <e.g., "Account permissions not checked">

Tone signal:
<neutral | frustrated | confused | escalated | satisfied-but-stuck>

Recommended rep action:
<specific: e.g., "Verify 3DS challenge logs; offer payment retry">

Things to NOT do:
<e.g., "Don't re-ask for invoice details — customer already provided">
```

RULES
- Conversation summary must be FACTS from the transcript, not paraphrase.
- 'Customer's CURRENT specific ask' should be REVISED — the customer's question may have evolved during the chat. Capture the LATEST.
- 'Things to NOT do' is for protecting customer experience: skip steps the bot already covered.

TRANSCRIPT
{transcript}

REASON: {handoff_reason}

Begin.""",
        "input_variables": [
            {"name": "transcript", "type": "string", "description": "Chat transcript so far", "required": True, "example": "Bot: How can I help? User: I was charged twice last month. Bot: Let me look... Yes I see two charges of $99 on April 12 and April 13. User: I never bought twice. Why?"},
            {"name": "handoff_reason", "type": "string", "description": "Why escalating", "required": True, "example": "account_specific"},
            {"name": "account_info", "type": "string", "description": "Account info if available", "required": False, "example": "Jane Doe, Pro plan, signed up 2023-04. LTV $4,500. No prior chargebacks."},
            {"name": "wait_seconds", "type": "integer", "description": "Expected wait", "required": False, "example": "180"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Part 1: customer bridge message. Part 2: structured handoff packet with reason, summary bullets, current ask, verified, not-verified, tone, recommended action, things-not-to-do.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Honest about what bot didn't verify; helpful summaries."},
            {"model": "gpt-4o-mini", "compatibility": "good", "notes": "Cheap + fast; sometimes paraphrases instead of facts. Pin verbatim quotes for summary."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can be over-polite in customer bridge — call out plainness rule."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Fast handoff packet generation."},
        ],
        "variations": [
            {"label": "Phone-call handoff", "description": "Handoff to a phone agent.", "prompt_snippet": "Adjust Part 1: ‘ask if they prefer phone or continued chat; if phone, capture number + best time.’"},
            {"label": "Async-email handoff", "description": "When no rep is available immediately.", "prompt_snippet": "Adjust wait_seconds handling: if >15min, offer email follow-up with explicit time window."},
            {"label": "Multi-language", "description": "Translate context for receiving rep.", "prompt_snippet": "Add: ‘bot may operate in customer's language; packet must be in REP's working language (English default).’"},
        ],
        "failure_modes": [
            {"symptom": "Customer bridge is bot-apologetic (‘Sorry I couldn't help...’).", "fix": "Re-pin: ‘describe what's happening, don't apologize for being a bot.’"},
            {"symptom": "Conversation summary is paraphrase, missing facts.", "fix": "Add: ‘summary bullets must be from transcript — paraphrase OK but key facts (numbers, dates, names) verbatim.’"},
            {"symptom": "‘Things to NOT do’ section empty.", "fix": "Force: ‘list at least 2 things the bot covered so the rep doesn't redo them. Empty section = packet not helpful.’"},
            {"symptom": "Customer's current ask doesn't match what they LAST said.", "fix": "Add: ‘the ask is the LATEST customer position, not initial. Conversations evolve.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gpt-4o-mini", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["support-ticket-triage", "support-response-empathetic", "escalation-classifier"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["chatbot-handoff", "human-in-the-loop"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How much should the packet say?", "answer": "Enough that the rep doesn't have to re-read the transcript for routine cases. ~200 words. Long transcripts get summarized; key facts stay verbatim."},
            {"question": "Should the customer see the packet?", "answer": "No — internal-only. The customer sees Part 1 (bridge message) only. Part 2 is rep-side context."},
            {"question": "What if the bot is confident about the answer?", "answer": "Then don't hand off. This prompt's whole purpose is for cases where bot judgement says ‘human needed.’ Tune the trigger criteria upstream."},
        ],
        "meta_title": "Chatbot Handoff To Human (With Context) — Prompt",
        "meta_description": "Generate bridge message + structured handoff packet when a bot escalates to a human rep. Verbatim facts + tone signal + recommended action.",
    },
    {
        "slug": "post-incident-customer-comms",
        "title": "Post-Incident Customer Communication",
        "tldr": "After an outage or service incident, drafts a post-mortem customer email: what happened in plain English, what we did, who was affected, what we're doing to prevent recurrence, and the credit policy.",
        "category": "customer-support",
        "tags": ["post-incident", "customer-comms", "outage", "transparency"],
        "best_for_tags": ["enterprise-comms", "incident-response", "trust"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Production outage > 1 hour", "example": "API down 90 min affecting Pro+ customers; this prompt drafts the customer email + status page entry."},
            {"scenario": "Data integrity incident", "example": "Some records were corrupted; need to communicate scope honestly without panic."},
            {"scenario": "Security incident disclosure", "example": "Suspicious activity detected; tight legal/comms requirements but customers need to know."},
            {"scenario": "Performance degradation", "example": "Not an outage, but observable slowdown affecting some users — communicate proactively before complaints pile up."},
        ],
        "when_not_to_use": "Skip for sub-1-minute blips affecting nobody. Skip when legal/security require special handling (use a templated comms approval process instead).",
        "full_prompt": """You are drafting a post-incident customer communication. Honesty over PR-speak.

INPUT
- Incident facts: {incident_facts}              (duration, impact, what broke)
- Affected customer segment: {affected_segment}  (Pro+ / specific region / specific feature users / all)
- Timeline: {timeline}                          (when started, when detected, when mitigated, when fully resolved)
- Root cause (technical, in plain English): {root_cause}
- Action taken: {actions_taken}
- Prevention plan: {prevention}
- Credit / make-good policy: {credit_policy}
- Tone: {tone}                                  (matter-of-fact, mostly low-key / regulated-industry-formal / startup-personal)

OUTPUT — email body, ~250-400 words

## Structure

1. Subject line: `[Action item: nothing] <Service name> incident on <date> — what happened`
   - Including ‘nothing for you to do’ if true reduces panic
   - Be specific: "<date>" not "recent"

2. Opening (1 sentence). What happened, when, who saw it.
   "On <date> from <time> to <time> UTC, our API returned 500 errors for ~12% of requests, affecting customers on Pro and Enterprise tiers in the EU region."

3. WHAT HAPPENED (1 paragraph). The technical story in PLAIN ENGLISH. No jargon if avoidable. If jargon necessary, define inline.
   - Bad: "Our k8s control plane experienced a leader election failure."
   - Better: "Our service-routing layer (the part that decides which server handles each request) got stuck choosing between two servers, causing some requests to timeout."

4. WHAT WE DID (numbered list, 3-5 items).
   - Specific actions, in order. Include detection time, mitigation time.
   - "10:42 UTC — our automated alerts fired. 10:51 UTC — engineer on call confirmed the issue and started failover. 11:13 UTC — full service restored."

5. WHAT WE'RE DOING (numbered list, 2-4 items).
   - Specific PREVENTION actions, with owners and rough timelines.
   - "Adding multi-leader fallback (eng owns; ETA next week)" not "improving reliability."

6. WHAT THIS MEANS FOR YOU
   - Was YOUR data affected? Be specific.
   - Are credits being applied? Be specific.
   - Do you need to take action? Be specific (usually nothing, sometimes "rotate your API keys", etc.).

7. Close (1 sentence). Honest acknowledgment. NO apology for the apology.

CRITICAL RULES
- NO marketing language. Banned: "incident", "challenge", "opportunity to improve". Use: "outage", "failure", "bug".
- Specify TIMES in UTC, not "morning" or "earlier today".
- If you don't know something, say so. "We're still investigating why X" beats "We've fully understood the issue" when it's not true.
- Credits: state the policy upfront. If automatic, say so. If by request, say so. Never bury this.
- If there was DATA LOSS, say it directly in section 6. Don't hide.

INCIDENT FACTS
{incident_facts}

TIMELINE
{timeline}

ROOT CAUSE
{root_cause}

Now draft.""",
        "input_variables": [
            {"name": "incident_facts", "type": "string", "description": "What happened", "required": True, "example": "API 500 errors. ~12% of requests. EU region. Pro+ customers."},
            {"name": "affected_segment", "type": "string", "description": "Who was affected", "required": True, "example": "Pro and Enterprise customers in EU region"},
            {"name": "timeline", "type": "string", "description": "Timeline UTC", "required": True, "example": "Started 10:30, detected 10:42, mitigation 10:51, fully restored 11:13"},
            {"name": "root_cause", "type": "string", "description": "Root cause plain English", "required": True, "example": "Service-routing layer entered split-brain after a network partition; chose between two leaders, causing request timeouts."},
            {"name": "actions_taken", "type": "string", "description": "What we did", "required": True, "example": "Failover to backup region, manual leader override, validated, switched back when healthy."},
            {"name": "prevention", "type": "string", "description": "Prevention plan", "required": True, "example": "Multi-leader resilience (eng team, ETA next week); chaos test for network partitions (monthly thereafter)."},
            {"name": "credit_policy", "type": "string", "description": "Credit/make-good", "required": True, "example": "Automatic credit equal to 2x downtime applied to all affected Pro/Enterprise customers' next invoice."},
            {"name": "tone", "type": "string", "description": "Tone preference", "required": False, "example": "matter-of-fact, startup-personal"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Subject line + 6-7 sections covering opening, what-happened plain English, what-we-did, what-we're-doing, what-it-means-for-you, close. 250-400 words.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Resists PR-speak; honest tone."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes drifts to ‘incident’ / ‘challenge’ — re-pin banned words."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; plain-English translation of root cause can be shallow."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for short outages; less precision on complex root causes."},
        ],
        "variations": [
            {"label": "Status-page version", "description": "Shorter version for status page.", "prompt_snippet": "Add: ‘also produce a 100-word version for the public status page — same facts, more compressed.’"},
            {"label": "Enterprise sla-bound", "description": "For contracts with formal SLA.", "prompt_snippet": "Add: ‘include explicit SLA calculation: was SLA breached? If yes, link to credit-claim form.’"},
            {"label": "Multi-incident week", "description": "If multiple incidents related.", "prompt_snippet": "Add: ‘if this is incident #2+ in a week, acknowledge the pattern explicitly in the opening.’"},
        ],
        "failure_modes": [
            {"symptom": "Hides scope of impact.", "fix": "Re-pin: ‘state who was affected, specifically. Hiding impact destroys trust faster than the outage did.’"},
            {"symptom": "PR-speak (‘incident’, ‘challenge’).", "fix": "Banned word list active. ‘Outage’, ‘bug’, ‘failure’ — describe what it was."},
            {"symptom": "Prevention is vague (‘we will improve reliability’).", "fix": "Force: ‘specific action + owner + ETA. ‘Improve reliability’ is not a prevention plan.’"},
            {"symptom": "Buries credit policy.", "fix": "Add: ‘credit policy goes in section 6, stated plainly. Never an afterthought.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["billing-dispute-deescalation", "internal-memo-from-decision"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["post-incident", "transparency"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should we wait until fully resolved?", "answer": "No — communicate ASAP, then update. Customers want to know during the outage. Initial message can be 'we see it, here's what we know so far'; full post-incident later."},
            {"question": "What if legal won't let us be specific?", "answer": "Then there are different templates. This prompt is for normal commercial outages. Security incidents, regulated industries: use a comms approval template + legal review."},
            {"question": "Will credits actually retain customers?", "answer": "Credits buy short-term goodwill. The PREVENTION-CREDIBILITY is what retains. Specific named-engineer-owned prevention beats $1000 of credits."},
        ],
        "meta_title": "Post-Incident Customer Communication — Prompt",
        "meta_description": "Draft post-outage email: plain-English root cause, timeline, what-we-did, prevention plan, credit policy. Honest over PR-speak.",
    },
]
