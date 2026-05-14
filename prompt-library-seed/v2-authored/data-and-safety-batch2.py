"""Data and safety prompts — batch 2."""

RECORDS = [
    {
        "slug": "policy-compliance-checker",
        "title": "Policy Compliance Checker",
        "tldr": "Takes a piece of content and checks it against a stated policy (style guide, compliance rules, brand guidelines). Returns specific violations with the rule cited and the fix.",
        "category": "safety",
        "tags": ["compliance", "policy", "content-review", "safety"],
        "best_for_tags": ["compliance-review", "style-guide", "regulated-industries"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Marketing copy review against brand guidelines", "example": "Blog post against brand voice guide → list of brand violations + suggested fixes."},
            {"scenario": "Compliance content check", "example": "Financial product description against regulatory rules → flagged claims."},
            {"scenario": "PR/internal docs against style guide", "example": "Press release against company style guide → consistency violations."},
            {"scenario": "User-generated content moderation", "example": "Forum posts against community rules with cited rule + action."},
        ],
        "when_not_to_use": "Skip for high-stakes legal review — augment, don't replace human reviewers. Skip when the policy is itself ambiguous — fix the policy first or LLM compliance will be inconsistent.",
        "full_prompt": """You are a compliance reviewer. Check the content against the stated policy.

INPUT
- The content: {content}
- The policy / rules: {policy}
- Severity ladder (what counts as blocker vs nit): {severity_ladder}

OUTPUT

## 1. Verdict
- PASS: no issues found
- PASS WITH NITS: minor issues only
- REVISIONS NEEDED: at least one MAJOR issue
- BLOCKED: at least one BLOCKER

## 2. Findings (sorted by severity)
For each issue:

### {Severity}: <one-line summary>
- **Rule cited**: exact rule from policy (verbatim, with section/number if applicable)
- **Location in content**: quote the offending span
- **Why it violates**: 1-2 sentences explaining the conflict
- **Suggested fix**: specific rewrite or change

## 3. Rules NOT violated
Quick confirmation that the content correctly adheres to 2-3 specific high-stakes rules. This builds confidence in the review.

## 4. Edge cases the policy doesn't cover
Cases the content has that the policy is silent on. Surface for human judgment — don't flag as violations.

## 5. Recommendations
- If REVISIONS NEEDED or BLOCKED: prioritized fix list (do blockers first)
- If PASS WITH NITS: optional improvements
- If PASS: any preventative suggestions for future content

RULES
- Don't flag what the policy doesn't address. If a rule isn't stated, it isn't a violation.
- Cite RULES verbatim — vague paraphrases hide bad reasoning.
- For BLOCKER claims, double-check: is this actually a rule, or your interpretation?
- Empty findings list is a valid output — don't manufacture issues.

CONTENT
{content}

POLICY
{policy}

SEVERITY LADDER
{severity_ladder}

Begin.""",
        "input_variables": [
            {"name": "content", "type": "string", "description": "The content to review", "required": True, "example": "Our new product is the BEST in the industry, guaranteed to double your revenue overnight!"},
            {"name": "policy", "type": "string", "description": "The policy / rules to check against", "required": True, "example": "1. No superlative claims ('best', 'top'). 2. No guarantees of specific financial outcomes. 3. Brand tone: confident but measured."},
            {"name": "severity_ladder", "type": "string", "description": "How to classify severity", "required": True, "example": "BLOCKER: legal/compliance violations. MAJOR: brand voice or factual issues. NIT: stylistic preferences."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Five sections: verdict, sorted findings with rule + location + fix, rules-NOT-violated confirmation, edge cases, prioritized recommendations.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on citing rules verbatim and distinguishing policy from interpretation."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes invents rules — re-pin ‘only what's in the policy.’"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; ‘rules not violated’ section often empty — force."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Over-flags; needs explicit ‘only the stated rules’ reminder."},
        ],
        "variations": [
            {"label": "Per-rule audit", "description": "Walk through every rule in order.", "prompt_snippet": "Replace ‘findings sorted by severity’ with: ‘for each rule in policy, in order: PASS / FLAG / EDGE CASE.’"},
            {"label": "Rewrite mode", "description": "Output a compliant rewrite alongside.", "prompt_snippet": "Add Section 6: ‘rewritten version of content that addresses all blockers + majors; preserve voice as much as possible.’"},
            {"label": "Multi-policy", "description": "Check against multiple policies.", "prompt_snippet": "Accept multiple policies; produce findings keyed by which policy each violation is from."},
        ],
        "failure_modes": [
            {"symptom": "Flags issues that aren't actually in the policy.", "fix": "Re-pin: ‘only flag what's STATED in the policy. Verify each finding cites verbatim rule.’"},
            {"symptom": "Empty ‘rules not violated’ section.", "fix": "Force: ‘confirm at least 2-3 rules the content correctly adheres to.’"},
            {"symptom": "Misses egregious violations.", "fix": "Run twice with different framings; alert if results differ. Or use stricter judge model."},
            {"symptom": "Severity all marked MAJOR.", "fix": "Re-pin ladder with examples for each level; force distribution check."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["content-moderation", "pii-redactor", "refund-policy-decision"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["compliance", "policy-enforcement"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Replace human review entirely?", "answer": "No — augment. LLM catches obvious violations; humans handle judgment calls, novel cases, and final accountability. Especially for legal/regulated content."},
            {"question": "Calibration?", "answer": "Sample 20 cases; hand-grade. Compare to LLM verdict. Refine the policy if LLM and humans disagree on what the policy says (often the policy is the unclear part)."},
            {"question": "Can this work for non-text policies?", "answer": "Yes — image/code compliance follows same pattern. Adjust prompt to call out the appropriate medium ('check this code against our security policy')."},
        ],
        "meta_title": "Policy Compliance Checker — Prompt",
        "meta_description": "Check content against stated policy: cite the rule, locate the violation, suggest a fix. Severity ladder + rules-not-violated confirmation.",
    },
    {
        "slug": "harmful-output-pre-check",
        "title": "Pre-Output Harmful Content Check",
        "tldr": "Before sending an LLM's response to a user, run it through a quick safety check: detects PII leaks, harmful advice, hallucinated facts in cited form, and policy-violating content. Returns block/warn/pass.",
        "category": "safety",
        "tags": ["safety", "output-validation", "moderation", "pre-output"],
        "best_for_tags": ["user-facing-llm", "safety-pipelines", "content-moderation"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Pre-send filter on chat responses", "example": "Before showing user, run LLM output through this check; block if it leaks PII or makes harmful claims."},
            {"scenario": "Post-generation cleanup in pipelines", "example": "Background generation job — every output passes the check before being stored."},
            {"scenario": "Customer-facing AI assistant", "example": "Hard safety bar — block harmful advice; warn on uncertain factual claims."},
            {"scenario": "Audit pass on existing content", "example": "Run on a corpus of stored AI responses to find what slipped through."},
        ],
        "when_not_to_use": "Skip for trusted internal contexts (engineering tools, research). Skip when the user-base is sophisticated and pre-filtering is patronizing. Skip when latency matters more than risk.",
        "full_prompt": """You are a safety checker. Review the LLM output and decide if it's safe to send to the user.

INPUT
- The LLM output being checked: {output}
- Context (what was asked, who's the user, domain): {context}
- Allowed content classes: {allowed_classes}     (some apps allow content others don't)
- Hard-blocked content classes: {blocked_classes}

OUTPUT (one JSON object)

{
  "verdict": "pass" | "warn" | "block",
  "reasons": [
    {
      "category": "pii-leak" | "harmful-advice" | "false-confidence" | "policy-violation" | "off-topic" | "other",
      "severity": "info" | "warn" | "block",
      "evidence": "verbatim quote from output",
      "explanation": "1-line why this is a concern"
    }
  ],
  "sanitized_version_if_warn": "optional rewritten content with warn-level issues removed",
  "confidence": "high" | "medium" | "low"
}

CATEGORIES TO CHECK

1. PII-LEAK: contains email, phone, SSN, credit card, API key, or other PII that shouldn't be in this response.
2. HARMFUL-ADVICE: medical / legal / financial advice presented authoritatively without disclaimer. Self-harm content. Dangerous DIY (electrical, chemical, etc.) without safety context.
3. FALSE-CONFIDENCE: specific factual claims (numbers, dates, names) the model is likely guessing. Especially: "studies show", "Dr. Smith proved", specific years/percentages.
4. POLICY-VIOLATION: content violating {blocked_classes}.
5. OFF-TOPIC: response not related to user's question — possibly a model hijack or context confusion.

RULES
- BLOCK if any reason is severity=block.
- WARN if multiple severity=warn reasons OR one info+ ambiguous case.
- PASS if no concerns or only severity=info reasons.
- Don't invent issues; if output looks clean, say so with confidence=high.
- 'False confidence' is hard — require AT LEAST a specific claim (number/date/proper noun) AND no source cited; not all confident statements are false.

OUTPUT
{output}

CONTEXT
{context}

Output JSON only.""",
        "input_variables": [
            {"name": "output", "type": "string", "description": "The LLM's generated response", "required": True, "example": "Sure! Your account number is 1234-5678-9012, and you can email Bob at bob@company.com to update it."},
            {"name": "context", "type": "string", "description": "What was asked and who's asking", "required": True, "example": "User asked how to update their billing info. Consumer app, anonymous users."},
            {"name": "allowed_classes", "type": "string", "description": "Content classes acceptable in this context", "required": False, "example": "Account-level help (with proper auth). Generic guidance."},
            {"name": "blocked_classes", "type": "string", "description": "Hard-blocked classes", "required": True, "example": "Other-user PII. Medical advice. Legal advice. API keys / passwords."},
        ],
        "expected_output": {
            "format": "json",
            "schema": "{ verdict, reasons[], sanitized_version_if_warn, confidence }",
            "sample": "{\n  \"verdict\": \"block\",\n  \"reasons\": [{\"category\": \"pii-leak\", \"severity\": \"block\", \"evidence\": \"account number is 1234-5678-9012\", \"explanation\": \"Account number disclosed without auth verification\"}],\n  \"confidence\": \"high\"\n}",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on subtle false-confidence detection."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; sometimes over-blocks — calibrate severity."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; false-confidence detection weaker."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Use stronger judge for safety-critical paths."},
        ],
        "variations": [
            {"label": "Llama Guard hybrid", "description": "Cheap first-pass + LLM-judge for ambiguous.", "prompt_snippet": "Add: ‘run cheaper safety classifier (Llama Guard) first; only invoke this LLM judge if classifier returns ambiguous result.’"},
            {"label": "Domain-specific", "description": "Healthcare / finance specific.", "prompt_snippet": "Add: ‘context is healthcare; flag any specific medical advice as block unless disclaimer present. Flag dosage / treatment specifics regardless of disclaimer.’"},
            {"label": "Block reasons surfaced to user", "description": "User-friendly block messages.", "prompt_snippet": "Add: ‘also produce user_message field — friendly explanation of why the response was blocked, without revealing the exact rule.’"},
        ],
        "failure_modes": [
            {"symptom": "Misses subtle PII (account IDs, internal references).", "fix": "Add: ‘PII includes account numbers, customer IDs, internal employee names — not just emails/phones.’"},
            {"symptom": "Over-blocks neutral content.", "fix": "Tighten BLOCK criteria; ensure reasons must include verbatim evidence."},
            {"symptom": "Misses confident hallucinations.", "fix": "Add: ‘specific factual claims with no source = warn at minimum.’"},
            {"symptom": "Latency too high for inline use.", "fix": "Use Llama Guard variation as first-pass; only invoke LLM judge on uncertain cases.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["prompt-injection-detector", "pii-redactor", "content-moderation"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["safety-pipeline", "output-validation"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Replace model's own safety?", "answer": "No — defense in depth. Model's safety + this judge + structural guards (limited tools, sandboxes). One layer fails; rest hold."},
            {"question": "Latency cost?", "answer": "100-500ms per check. Use hybrid (fast classifier + LLM judge on ambiguous) for production. Or run in background for non-critical paths."},
            {"question": "False-positive cost?", "answer": "High — users frustrated. Tune severity carefully; bias toward warn (rewrite-and-send) over block. Reserve block for genuine harm."},
        ],
        "meta_title": "Pre-Output Harmful Content Check — Prompt",
        "meta_description": "Pre-send safety check: PII leaks, harmful advice, false confidence, policy violations. Returns verdict + sanitized version + confidence.",
    },
]
