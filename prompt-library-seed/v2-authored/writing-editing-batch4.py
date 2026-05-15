"""Writing & editing — batch 4."""

RECORDS = [
    {
        "slug": "blog-post-from-loose-notes",
        "title": "Blog Post From Loose Notes",
        "tldr": "Turns a messy notes-dump into a publishable blog post — identifies the through-line, builds structure, preserves the writer's voice, and flags weak parts that need the author's judgment.",
        "category": "writing-editing",
        "tags": ["blog", "writing", "outlining", "drafting"],
        "best_for_tags": ["technical-writers", "founders", "consultants"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Engineer's tech blog post", "example": "Notes from an incident → publishable post."},
            {"scenario": "Founder thought piece", "example": "Slack-thread musings → structured essay."},
            {"scenario": "Conference-talk to blog", "example": "Talk notes → blog version of the same content."},
            {"scenario": "Consultant case study", "example": "Project notes → polished case-study post."},
        ],
        "when_not_to_use": "Skip when notes are too thin (no real argument or content). Skip for highly literary/personal essays where voice nuance matters more than structure.",
        "full_prompt": """You are a blog-post drafter. Turn loose notes into a publishable post — identify through-line, build structure, preserve voice.

INPUT
- Loose notes: {notes}
- Author's voice samples (3-5 paragraphs from prior writing): {voice_samples}
- Target audience: {audience}
- Target length: {length}                 (e.g., '800-1200 words')
- Publication context: {publication_context}    (personal blog / company blog / Medium / Substack)
- Constraints: {constraints}              (must-include claims, links, can/can't say)

OUTPUT

## 1. Through-line discovery
What's the SINGLE argument or insight in these notes?
- **Claim:** ___ (in 1 sentence)
- **Why it matters:** ___ (1 sentence)
- **Why now:** ___ (timing relevance)

If the notes don't have a single through-line, suggest 2-3 candidate angles + ask the author to pick.

## 2. Structure
Standard 5-block structure (adapt as needed):
- **Hook:** specific moment / observation / surprise
- **Stakes:** why this matters / who cares
- **Argument:** the through-line, fleshed out (this is the body)
- **Counterpoint:** strongest objection + your response
- **Payoff:** what reader walks away with — actionable or perspective-shifting

For each block: 1-2 sentence summary.

## 3. Draft
Write the full draft. Match the voice samples (cadence, vocabulary, sentence-rhythm).

CRITICAL: do NOT add claims that aren't in the notes. If you need filler, mark it [AUTHOR: ADD EXAMPLE HERE].

Section headers help but aren't always necessary.

## 4. Voice fidelity scorecard
Against voice samples:
- **Sentence length:** matches / drifts (longer / shorter)?
- **Vocabulary register:** matches / drifts?
- **Use of contractions, em-dashes, parentheticals:** matches?
- **Self-reference patterns:** matches?

Flag any drift.

## 5. Weak parts
Sections the author should personally rewrite:
- Where the prompt is filling gaps the author should fill.
- Where the original notes' insight is THIN and needs the author's expert depth.
- Where claims need verification.

Marked clearly with [AUTHOR: ___] tags in the draft.

## 6. Cut candidates
What was in the notes but cut from the draft:
- Tangents not serving the through-line.
- Repeated points consolidated.
- Filler / setup the author can re-add if desired.

## 7. SEO + sharing notes (optional)
- **Suggested title:** ___ (2-3 options)
- **Subtitle:** ___
- **Tweet thread hook:** ___ (first tweet for the post)
- **LinkedIn lead-in:** ___

CRITICAL RULES
- Preserve VOICE. Don't sanitize the author's edges.
- Don't invent CLAIMS not in the notes. Flag gaps with [AUTHOR: ___].
- Through-line is ONE thing. Multi-thread notes get reduced.
- Weak-parts section is honest — author should see where the draft is thin.

NOTES
{notes}

Begin.""",
        "input_variables": [
            {"name": "notes", "type": "string", "description": "Loose notes", "required": True, "example": "(1) Spent 6mo trying X. (2) Realized halfway that the underlying assumption was wrong — orgs CAN't onboard async, they need a forcing function. (3) Pivoted. (4) Surprising fact: even small orgs (3-5 ppl) need this..."},
            {"name": "voice_samples", "type": "string", "description": "Prior writing samples", "required": True, "example": "[Paste 3-5 paragraphs of prior author writing here]"},
            {"name": "audience", "type": "string", "description": "Target audience", "required": True, "example": "Founders + early-stage operators; familiar with startup concepts"},
            {"name": "length", "type": "string", "description": "Target length", "required": True, "example": "1000-1400 words"},
            {"name": "publication_context", "type": "string", "description": "Where it's publishing", "required": True, "example": "Personal Substack — Wednesday cadence; engaged subscriber base of ~5k founders"},
            {"name": "constraints", "type": "string", "description": "Constraints", "required": False, "example": "Don't name specific companies; link to my prior post on async-onboarding."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: through-line discovery, 5-block structure, full draft with [AUTHOR] tags, voice fidelity scorecard, weak parts to rewrite, cut candidates, SEO + sharing notes.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at voice-match + honest weak-parts flagging."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; voice-match good when given 3+ samples."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; can over-formalize voice — re-pin samples."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Workable for straightforward drafts; voice fidelity slightly weaker."},
        ],
        "variations": [
            {"label": "Newsletter format", "description": "Tune for newsletter cadence.", "prompt_snippet": "Format for newsletter: subject line + preview text + scannable mid-section + clear CTA. Optimize for inbox-skimming readers."},
            {"label": "Twitter-thread version", "description": "Convert to thread.", "prompt_snippet": "Output the same through-line as a 12-15 tweet thread. Each tweet stands alone but compounds. End with link to long-form."},
            {"label": "Multi-CTA piece", "description": "Lead-gen post.", "prompt_snippet": "Add 2-3 unobtrusive CTAs to the draft (newsletter signup, product, related-post). Spaced naturally."},
        ],
        "failure_modes": [
            {"symptom": "Sanitizes voice.", "fix": "Re-pin: 'voice samples are authoritative. If author uses em-dashes, swear words, sentence fragments — preserve.'"},
            {"symptom": "Invents claims.", "fix": "Hard rule: 'claims must trace to notes. Otherwise [AUTHOR: ADD EXAMPLE HERE] tag.'"},
            {"symptom": "Multi-threaded draft.", "fix": "Force: 'one through-line. If notes have multiple, surface candidates and stop. Don\\'t merge incompatible insights.'"},
            {"symptom": "Weak-parts section missing.", "fix": "Require: 'minimum 2 weak parts flagged for author rewrite, OR explicit statement \"all sections are author-quality.\"'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["press-release-from-bullet-points", "first-line-hook-generator", "internal-memo-from-decision"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["voice", "longform-writing"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why match voice instead of polishing?", "answer": "Polished writing all sounds the same. The author's edges (specific phrasings, em-dash habits, sentence rhythms) are what makes the post feel theirs. Sanitizing kills the brand."},
            {"question": "What if my notes are too thin?", "answer": "The prompt will flag — section 1 asks for through-line. If there isn't one, you have a few paragraphs of musing, not a post. Either add more thinking or pick a smaller scope."},
            {"question": "[AUTHOR: ___] tags — how to handle?", "answer": "Treat them as required-fills before publishing. The prompt is honest about where it filled gaps the author should fill. Don't publish with tags intact."},
            {"question": "Voice-match accuracy?", "answer": "Strong for sentence-cadence + vocabulary. Weaker for genuinely unique style (someone who writes like Annie Dillard). For high-stakes voice posts, treat the output as scaffolding."},
        ],
        "meta_title": "Blog Post From Loose Notes — Writing Prompt",
        "meta_description": "Turn messy notes into a publishable blog post: through-line discovery, structure, voice-preserving draft, honest weak-parts flagging.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "executive-summary-from-long-doc",
        "title": "Executive Summary From Long Doc",
        "tldr": "Distills a long document (50+ pages) into a 1-page exec summary: decisions needed, key findings, supporting data points, risks. Calibrated to reader's role and time.",
        "category": "writing-editing",
        "tags": ["summary", "executive", "longform", "distillation"],
        "best_for_tags": ["managers", "executives", "consultants"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Board memo from long analysis", "example": "20-page research → 1-page board summary."},
            {"scenario": "Consulting deliverable", "example": "Full report → executive summary for C-suite."},
            {"scenario": "RFP response cover", "example": "100-page proposal → 1-page exec cover."},
            {"scenario": "Vendor RFP analysis", "example": "8 vendor responses (40 pages each) → exec recommendation."},
        ],
        "when_not_to_use": "Skip when source is incoherent — summary inherits the incoherence. Skip when reader specifically needs to engage with all detail.",
        "full_prompt": """You are an executive-summary writer. Distill a long doc into a 1-page summary calibrated to the reader's role and time.

INPUT
- Source document: {source_doc}
- Reader role / role-specific concerns: {reader_role}
- Decisions reader needs to make: {decisions_needed}
- Time budget reader has: {time_budget}            (3 min / 10 min / 30 min)
- Source document length: {source_length}
- Specific questions reader brought: {reader_questions}

OUTPUT

## 1. The 30-second version
3-5 sentences. Top line + critical data point + decision required. Reader could stop here and have the gist.

## 2. The 3-minute version (the executive summary)

**Recommendation:** ___ (the bottom line, stated)

**Decisions you need to make:**
- Decision 1: ___ (options: A / B / C)
- Decision 2: ___

**What we found:**
- Finding 1: ___ (supporting data: ___)
- Finding 2: ___
- Finding 3: ___

**Why this matters:**
- Strategic implication: ___
- Financial implication: ___
- Operational implication: ___

**Risks:**
- Risk 1 (likelihood / impact): ___
- Risk 2: ___

**Next steps:**
- Step 1 (owner, by when): ___
- Step 2: ___

## 3. The 10-minute version (deeper detail)
For readers who want more without reading the whole doc:
- Per-finding 1-paragraph deeper explanation.
- Methodology / data caveats.
- Alternative interpretations considered.

## 4. Reader-specific calibration
Given {reader_role}:
- Concerns this reader will have FIRST: ___
- Numbers this reader cares MOST about: ___
- Decisions this reader is uniquely positioned to make: ___

Restructure section 2 so those bubble to the top.

## 5. Questions you'll be asked
3-5 questions a sharp reader will ask after reading. Don't answer them in the summary — surface so author can prep.
- "Why didn't you also look at X?"
- "What's the confidence on Y?"

## 6. What we cut
- Major topics in source NOT in summary + reason.
- Where the source is uncertain — handled how in summary.

This lets reader trust they're getting the right things.

## 7. Appendix anchor (if needed)
"For more detail, see source doc sections: ___, ___."

Specific section pointers for follow-up reading.

CRITICAL RULES
- 30-second version is GENUINELY 30 seconds — 3-5 sentences max.
- Recommendation is STATED. Don't bury the lede.
- Risks are NUMBERED with likelihood/impact, not 'risks exist.'
- Cuts are explicit — reader trusts what's there because they see what was dropped.
- Reader-specific calibration changes priority order.

SOURCE
{source_doc}

Begin.""",
        "input_variables": [
            {"name": "source_doc", "type": "string", "description": "Source long document", "required": True, "example": "[15-page market analysis covering...]"},
            {"name": "reader_role", "type": "string", "description": "Reader role + concerns", "required": True, "example": "CFO — concerned with revenue impact, capital efficiency, payback period"},
            {"name": "decisions_needed", "type": "string", "description": "Decisions reader makes", "required": True, "example": "Approve / hold / reject the proposed market expansion budget of $4M."},
            {"name": "time_budget", "type": "string", "description": "Time reader has", "required": True, "example": "10 minutes between meetings"},
            {"name": "source_length", "type": "string", "description": "Source length", "required": True, "example": "15 pages with 4 data appendices"},
            {"name": "reader_questions", "type": "string", "description": "Questions reader brought", "required": False, "example": "What's the payback timeline? What's the worst-case downside if expansion underperforms?"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: 30-second version, 3-minute exec summary with recommendation/decisions/findings/risks/next-steps, 10-minute deeper detail, reader-specific calibration, questions you'll be asked, what we cut, appendix anchors.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at honest 'what we cut' + bottom-line discipline."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong; can bury the lede — re-pin 'recommendation upfront.'"},
            {"model": "gemini-1.5-pro", "compatibility": "excellent", "notes": "Long-context advantage; can summarize 50+ page docs in one pass."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Works for shorter source docs; thins on 50+ page synthesis."},
        ],
        "variations": [
            {"label": "Multi-stakeholder versions", "description": "Different summaries per role.", "prompt_snippet": "Output 3 versions calibrated to 3 different reader roles. Each restructures priorities for that role."},
            {"label": "Slide-version", "description": "Output as slide.", "prompt_snippet": "Convert summary to a single slide: title = recommendation, body = key findings + risks, footer = next steps. 7±2 bullets max."},
            {"label": "Brief for time-poor reader", "description": "Ultra-short.", "prompt_snippet": "Skip sections 3-7. Output only sections 1-2 + the 30-second version 30 seconds. For 2-minute readers."},
        ],
        "failure_modes": [
            {"symptom": "Buries the recommendation.", "fix": "Re-pin: 'recommendation is stated in 30-second version + restated in 3-min. No \"based on analysis...\" hedging.'"},
            {"symptom": "Vague risks.", "fix": "Force: 'risks numbered with likelihood + impact. Generic \"market risk\" not allowed.'"},
            {"symptom": "Includes everything.", "fix": "Hard rule: 'cuts section is required. If you can\\'t name what was cut, you didn\\'t actually summarize.'"},
            {"symptom": "Reader-specific calibration ignored.", "fix": "Require: 'reorder section 2 so reader\\'s top concerns appear first.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["blog-post-from-loose-notes", "internal-memo-from-decision", "research-summary-for-non-experts"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["executive-summary", "distillation"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why 30-second + 3-min + 10-min?", "answer": "Different readers have different time. Some scan, some read, some engage. The tiered structure lets each reader get what they need without the author writing three versions."},
            {"question": "Won't burying-the-lede happen anyway?", "answer": "If the prompt is run correctly, no. The 30-second version is enforced to lead with recommendation. Run it and CHECK the first sentence — that's the test."},
            {"question": "How accurate is the 'what we cut' section?", "answer": "It surfaces major topic cuts. Sub-cuts within sections are harder to enumerate. For high-stakes summaries, validate cuts against the source's table of contents."},
            {"question": "Can I trust the data points?", "answer": "The prompt extracts; you verify. Always spot-check key numbers against source. Don't ship an exec summary without verifying its statistics."},
        ],
        "meta_title": "Executive Summary From Long Doc — Writing Prompt",
        "meta_description": "Distill long documents into 1-page exec summaries: 30-sec / 3-min / 10-min tiers, reader calibration, risks, honest cuts, appendix anchors.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "feedback-letter-balanced-tough",
        "title": "Feedback Letter — Balanced And Tough",
        "tldr": "Drafts a feedback letter that is honest about problems, acknowledges strengths, and gives clear path forward — without being either sugar-coated OR brutal. For performance, peer review, manuscript feedback.",
        "category": "writing-editing",
        "tags": ["feedback", "performance-management", "peer-review"],
        "best_for_tags": ["managers", "writers", "editors", "peer-reviewers"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Quarterly performance feedback", "example": "Manager → report; one weak area, several strengths, clear development path."},
            {"scenario": "Peer-review of a draft", "example": "Reviewer → author; mix of structural and detail feedback."},
            {"scenario": "Manuscript feedback to writer", "example": "Editor → writer; needs revision but worth revising."},
            {"scenario": "Mentor feedback to mentee", "example": "Mentor → mentee; honest critique calibrated to the relationship."},
        ],
        "when_not_to_use": "Skip when the relationship can't bear honesty (very new / no trust). Skip when feedback is mostly admin (no real growth content). Use a different format for those.",
        "full_prompt": """You are a feedback drafter. Honest about problems; acknowledges strengths; clear path forward. No sugar-coating, no brutality.

INPUT
- Recipient context: {recipient}        (relationship, role, history)
- Subject of feedback: {subject}        (work product, performance period, manuscript)
- Strengths to acknowledge: {strengths}
- Problems to address: {problems}       (with severity / examples)
- Desired outcome: {outcome}            (improved next iteration / clarity about path / decision-relevant input)
- Relationship state: {relationship}    (new / established / strained / coaching)

OUTPUT

## 1. Stance check
Before writing:
- Are problems FACTUAL (observable behavior / artifact)? Or opinion?
- Have strengths been EARNED or are they obligatory padding?
- Is desired outcome ACTIONABLE by the recipient?

If problems are opinion-only or outcome isn't actionable, recommend NOT sending the letter — find a different format (1:1, doc comments, conversation).

## 2. Structural design
Choose a structure based on relationship + content:
- **Sandwich (acknowledge → critique → encourage):** safe; good for new relationships.
- **SBI (Situation / Behavior / Impact):** behavioral feedback.
- **What-worked / what-didn't / what-next:** work-product feedback.
- **Critique-led with explicit support frame:** when relationship is strong and recipient values directness.

Pick + justify.

## 3. The draft
Write the letter. Properties:
- **Honest about problems.** Specific. Observable. Not labeling ('you're disorganized') — describing behavior ('three of the four deliverables this quarter missed deadline by >1 week').
- **Strengths acknowledged.** Specific, not generic ('You write well' → 'Your section on X clarified what no other doc had — it became the doc the team referenced.')
- **Path forward.** Concrete action recipient can take. Time-bound if appropriate.
- **Tone matches relationship.** Warm for established + coaching. Crisper for new/professional-distance.

## 4. Tone-and-fairness check
Read the draft. Score:
- **Honesty:** does it actually surface the problem? Or hint at it?
- **Specificity:** does it cite examples?
- **Fairness:** does it acknowledge strengths in proportion?
- **Action-orientation:** can the recipient act on it?
- **Calibration:** does the tone match the relationship + content severity?

Flag anything off-balance.

## 5. Anticipated reactions
- What will the recipient feel reading this? (defensive / motivated / hurt / clarified)
- What will they likely respond with?
- What's the worst-case reaction and is it tolerable?
- What's the best-case reaction?

## 6. What you might re-write
After section 5 reflection: re-write the 1-2 sections where the anticipated reaction suggests the framing needs tuning.

## 7. Follow-up plan
- Will there be a conversation about this? When?
- What's the next interaction that depends on this feedback?
- How will you know the feedback landed (or didn't)?

CRITICAL RULES
- Problems are FACTUAL (observable, citeable).
- Strengths are EARNED (specific, not generic).
- Path-forward is ACTIONABLE.
- Tone matches relationship; don't write strained letters in coaching-relationship tone.
- Anticipated-reactions section is the gut-check; rewrite if landing badly.

INPUTS
Recipient: {recipient}
Subject: {subject}
Strengths: {strengths}
Problems: {problems}
Outcome: {outcome}

Begin.""",
        "input_variables": [
            {"name": "recipient", "type": "string", "description": "Recipient context", "required": True, "example": "Direct report — 18 months tenure, mid-level engineer, generally strong but coasting last 2 quarters."},
            {"name": "subject", "type": "string", "description": "Subject of feedback", "required": True, "example": "Q2 performance review."},
            {"name": "strengths", "type": "string", "description": "Strengths to acknowledge", "required": True, "example": "Code quality consistently high. Mentors 2 junior engineers well — their reviews praise this. Calm in incident-response."},
            {"name": "problems", "type": "string", "description": "Problems to address", "required": True, "example": "Velocity dropped ~30% in Q2 (data from sprint metrics). Initiated zero new projects (vs 2-3 historically). Missed 2 of 3 stretch goals from Q1. No off-team visibility — hasn't presented in months."},
            {"name": "outcome", "type": "string", "description": "Desired outcome", "required": True, "example": "Either re-engage at senior level (which is path to staff in 12-18mo), or have an honest conversation about whether the role still fits."},
            {"name": "relationship", "type": "string", "description": "Relationship state", "required": True, "example": "Established 18 months, trust solid, hasn\\'t had a hard feedback conversation in 6 months."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: stance check, chosen structure with justification, full draft letter, tone-and-fairness scorecard, anticipated reactions, rewrites based on anticipation, follow-up plan.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest balance of honesty + warmth; willing to recommend NOT sending."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can soften too much — re-pin 'observable, citeable.'"},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; sometimes formal-corporate when relationship is coaching."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Workable; less nuanced tone-calibration."},
        ],
        "variations": [
            {"label": "Manuscript-edit feedback", "description": "For writers.", "prompt_snippet": "Tune for written-work feedback. Lead with structural critique then detail-level. Map every critique to a specific passage or paragraph."},
            {"label": "Code-review-as-letter", "description": "Standalone code review.", "prompt_snippet": "Tune for code-review feedback in PR context. Lead with overall approach assessment, then file-by-file specifics, then style nitpicks."},
            {"label": "Termination-adjacent", "description": "Performance improvement.", "prompt_snippet": "When feedback may lead to PIP or separation, calibrate: HR review required, document everything, name expectations + measurable bar."},
        ],
        "failure_modes": [
            {"symptom": "Vague problems ('you need to step up').", "fix": "Re-pin: 'problems are observable + citeable. Replace labels with described behavior.'"},
            {"symptom": "Generic strengths.", "fix": "Force: 'strengths name specific instance / specific behavior / specific impact. \"Good engineer\" doesn\\'t count.'"},
            {"symptom": "No actionable path forward.", "fix": "Require: 'path forward names concrete action recipient can take. Without it, feedback is venting.'"},
            {"symptom": "Tone mismatched to relationship.", "fix": "Add: 'tone-and-fairness check explicitly addresses calibration. Strained relationships get crisper tone; coaching relationships warmer.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["delegation-decision-framework", "vip-customer-escalation-protocol", "incident-postmortem-blameless"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["radical-candor", "feedback"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is written feedback always right?", "answer": "No. For first-time hard feedback, often conversation first → letter follow-up. The prompt can recommend skipping the letter (section 1 stance check)."},
            {"question": "What if the recipient pushes back?", "answer": "Anticipated-reactions section preps you. If reaction is defensive, lean on the observable facts. If reaction is constructive, build on the path-forward."},
            {"question": "Performance-review use?", "answer": "Yes, with HR alignment if formal. The structure is the same; the formality of language adjusts. Section 7 follow-up plan becomes development-plan timeline."},
            {"question": "How honest is too honest?", "answer": "Honesty is calibrated to relationship + outcome. If the relationship can't bear the truth needed, the prompt recommends a different format. The dial is in section 4."},
        ],
        "meta_title": "Feedback Letter — Balanced and Tough — Writing Prompt",
        "meta_description": "Draft balanced feedback: honest problems with examples, earned strengths, actionable path forward. Tone calibrated to relationship.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "rewrite-for-non-native-readers",
        "title": "Rewrite For Non-Native Readers",
        "tldr": "Rewrites copy for non-native English speakers without dumbing it down: simpler syntax, common vocabulary, fewer idioms, no cultural specificity — preserves tone and meaning.",
        "category": "writing-editing",
        "tags": ["accessibility", "rewriting", "plain-english", "global-audience"],
        "best_for_tags": ["devrel", "support", "global-marketing"],
        "difficulty_tier": "beginner",
        "featured": False,
        "use_cases": [
            {"scenario": "Documentation for global audience", "example": "Technical docs read by engineers worldwide — many ESL."},
            {"scenario": "Support content for non-native speakers", "example": "Help center optimized for clear comprehension."},
            {"scenario": "Global marketing email", "example": "Email goes to 40+ countries; remove idioms / cultural references."},
            {"scenario": "International team comms", "example": "Internal docs for distributed team where English is 2nd-3rd language for many."},
        ],
        "when_not_to_use": "Skip for literary writing where idiom and rhythm are the point. Skip when the audience is primarily native speakers — over-simplification feels patronizing.",
        "full_prompt": """You are a clarity rewriter. Rewrite for non-native English readers: simpler syntax, common vocabulary, fewer idioms, no cultural specificity. Preserve tone + meaning.

INPUT
- Source text: {source_text}
- Target reader level: {reader_level}      (CEFR B1 / B2 / C1)
- Domain: {domain}                          (technical / marketing / support / general)
- Preserve technical terms: {preserve_terms}
- Tone to preserve: {tone}                  (formal / friendly / authoritative / playful)

OUTPUT

## 1. Source diagnosis
What makes the source harder for non-native readers:
- **Idioms / phrasal verbs:** "make do", "hold off", "kick around" — flag list.
- **Long / nested sentences:** sentences >25 words OR with 3+ clauses.
- **Cultural references:** Super Bowl, IRS, Thanksgiving — flag list.
- **Rare / register-specific vocabulary:** words that are easier but less common.
- **Passive constructions:** where active would be clearer.
- **Pronoun ambiguity:** 'it' / 'they' with unclear referent.

## 2. The rewrite
Output rewritten text. Properties:
- Sentences 15-20 words typical, 25 max.
- Common vocabulary (Word Frequency List or General Service List).
- No idioms unless explained.
- No cultural specificity without context.
- Pronouns near their referent.
- Active voice unless passive is genuinely clearer.
- Numbers as digits, not words.
- Consistent terminology — same concept, same word.

PRESERVE: tone (formal/friendly/etc.), technical terms (per {preserve_terms}), meaning, intent.

## 3. Change log
Diff key changes:
| Original | Rewritten | Reason |
|---|---|---|

## 4. Vocabulary substitutions
List replaced words:
- "leverage" → "use"
- "ascertain" → "find out"
- "facilitate" → "help"
- "subsequently" → "then"

These are common upgrades worth knowing for future writing.

## 5. Sentences split
Long sentences split into shorter ones:
- Original: [long sentence]
- Split: [two shorter sentences]
- Why: clarity for readers parsing English as L2.

## 6. Tone preservation check
Did the rewrite preserve the original tone?
- **Formal source → formal rewrite:** check.
- **Friendly source → friendly rewrite:** check.
- **Authoritative → authoritative:** check.

If tone drifted, flag and re-tune. Simpler ≠ casual.

## 7. Reader-test gotchas
Things even the rewrite might trip non-native readers on:
- Multi-word verbs that look like one verb ('check out', 'set up' — easy if explicit, hard if 'I'll check out the situation').
- Negation ambiguity ('not infrequent').
- Numbers vs ordinals.
- Time phrases ('biweekly' — every 2 weeks OR twice per week?).

CRITICAL RULES
- Simpler ≠ patronizing. Don't drop concepts; simplify expression.
- Tone preserved. Casual sources stay casual; formal stays formal.
- Idioms removed OR explained — don't silently drop nuance.
- Technical terms (from preserve_terms) stay as-is.
- Change log shows the work — author can adopt the rewrite or accept partial.

SOURCE
{source_text}

Begin.""",
        "input_variables": [
            {"name": "source_text", "type": "string", "description": "Source text", "required": True, "example": "We need to circle back on the customer feedback ASAP. Once we've gotten our heads around what they're seeing, we can hammer out a plan to push the release through next sprint."},
            {"name": "reader_level", "type": "string", "description": "Target reader level", "required": True, "example": "CEFR B2 — independent users, comfortable with everyday topics + own field"},
            {"name": "domain", "type": "string", "description": "Domain", "required": True, "example": "Internal team comms (technical product team)"},
            {"name": "preserve_terms", "type": "string", "description": "Technical terms to preserve", "required": False, "example": "release, sprint, customer feedback, deployment"},
            {"name": "tone", "type": "string", "description": "Tone to preserve", "required": True, "example": "Direct, slightly casual, action-oriented"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: source diagnosis (idioms/cultural/long-sentences), the rewrite, change-log diff, vocabulary substitution list, sentences-split log, tone preservation check, reader-test gotchas to watch.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at tone preservation while simplifying."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; can over-simplify — re-pin tone preservation."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; weaker on idiom detection."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Works well; idiom detection slightly weaker."},
        ],
        "variations": [
            {"label": "Multi-level output", "description": "Three versions at different levels.", "prompt_snippet": "Output 3 versions: CEFR B1, B2, C1. Reader picks the right level. Each preserves tone."},
            {"label": "Bilingual annotation", "description": "Annotate idioms in target language.", "prompt_snippet": "Add inline annotations in target language for any preserved idioms or technical terms. Format: 'rollout (= the launch of a feature)'."},
            {"label": "Simplification audit", "description": "Audit existing simplified text.", "prompt_snippet": "Given EXISTING simplified text, audit: idioms missed, sentences still too long, tone drift, vocabulary still too rare."},
        ],
        "failure_modes": [
            {"symptom": "Sounds patronizing.", "fix": "Re-pin: 'tone preservation. Simpler ≠ kid-talk. Match formal-source tone in formal-rewrite.'"},
            {"symptom": "Tone drift.", "fix": "Force section 6: 'tone check against source. If drift, re-tune.'"},
            {"symptom": "Idioms silently dropped.", "fix": "Add: 'idioms removed get LISTED in section 1. Either remove + explain or remove + paraphrase, not silent drop.'"},
            {"symptom": "Loses precision in technical content.", "fix": "Hard rule: 'preserve_terms stay verbatim. Technical concepts maintain precision; expression simplifies.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["marketing-copy-localization", "technical-doc-translation-with-terms", "concept-explainer-with-progressive-depth"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["plain-language", "cefr"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How is this different from translation?", "answer": "Translation = different language. This = same language, simplified syntax/vocabulary. Use this when audience reads English as L2/L3 but doesn't want translated."},
            {"question": "Won't native speakers find it bland?", "answer": "Possibly — that's why it's for global audiences specifically. For mixed audiences, lean toward B2-C1 (less simplification, still cleaner)."},
            {"question": "CEFR levels — what do they mean?", "answer": "B1 = independent traveler-level, B2 = comfortable everyday + own field, C1 = effective for complex topics. Most professional docs target B2."},
            {"question": "Can it handle slang / jargon?", "answer": "Domain-specific jargon preserves via preserve_terms. Slang gets removed/replaced unless it's also widely-known internationally (which is rare)."},
        ],
        "meta_title": "Rewrite For Non-Native Readers — Writing Prompt",
        "meta_description": "Rewrite text for non-native English readers: simpler syntax, common vocabulary, fewer idioms, preserved tone and meaning.",
        "version": "v2.0",
        "release_status": "stable",
    },
]
