"""Translation — batch 2."""

RECORDS = [
    {
        "slug": "marketing-copy-localization",
        "title": "Marketing Copy Localization (Not Just Translation)",
        "tldr": "Localizes marketing copy across cultures: preserves the FUNCTIONAL goal (CTA / persuasion), adapts the cultural references, flags untranslatable concepts, surfaces legal/sensitivity risks.",
        "category": "translation",
        "tags": ["localization", "marketing", "cross-cultural", "translation"],
        "best_for_tags": ["marketers", "saas-international", "ecommerce"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Landing page localization", "example": "US English homepage → JP Japanese; hero, CTAs, social proof adapted."},
            {"scenario": "Ad campaign localization", "example": "Facebook ad copy for 6 markets; same campaign, locally-resonant variants."},
            {"scenario": "Email-marketing localization", "example": "Lifecycle email translated AND culturally adapted (greeting formality, urgency norms)."},
            {"scenario": "Product-naming check", "example": "Localizing a product name — flag if it means something embarrassing in target language."},
        ],
        "when_not_to_use": "Skip for legal / medical / technical content where literal accuracy matters more than cultural fit. Use a domain-specialist translator. Don't use for high-stakes brand names without human review.",
        "full_prompt": """You are a localization writer. Adapt marketing copy for a target market — preserving FUNCTIONAL goal while adapting cultural fit.

INPUT
- Source copy: {source_copy}
- Source language / market: {source_market}     (e.g., 'en-US, B2B SaaS')
- Target language / market: {target_market}     (e.g., 'ja-JP, business tools')
- Copy purpose: {purpose}                       (CTA, awareness, conversion, retention, brand-launch)
- Brand voice: {brand_voice}
- Legal / regulatory constraints: {legal}       (GDPR, advertising-rules, claim restrictions)

OUTPUT

## 1. Source decomposition
- What's the FUNCTIONAL goal of this copy? (drive sign-up / set tone / convey value-prop)
- What's the IMPLICIT cultural assumption baked in? (US tendency toward urgency, individual-success framing, etc.)
- What's the explicit value-prop?
- What's the social-proof scaffold (testimonials, brands, numbers)?

## 2. Localized copy
Output the localized version. NOT a literal translation — a functionally equivalent version that lands in {target_market}.

Output BOTH:
- The localized copy (in target language).
- A back-translation to source language (so the reviewer can see what you wrote).

## 3. What changed and why
For each meaningful change:
- **Original:** ___
- **Localized:** ___
- **Cultural reason:** ___ (formality level, urgency norms, individualism vs collectivism, indirectness)
- **Functional preservation:** how the change preserves the original GOAL.

## 4. Untranslatable concepts
Concepts that don't map cleanly:
- Source concept: ___
- Why it doesn't translate: ___
- Localization strategy: replace / explain / drop / substitute different concept.

## 5. Cultural / legal risk flags
- **Cultural risk:** ___ (gestures, holiday references, color symbolism, religious references)
- **Legal / regulatory:** ___ (claim restrictions, GDPR-required language, ad rules)
- **Brand-trademark conflict:** does the localized name / phrase conflict with existing local brand?

For each: severity (block / flag / informational).

## 6. A/B-test recommendations
2-3 variants to test in market:
- Variant A: closer to source style
- Variant B: deeper localization
- Variant C: alternative framing

For each: what hypothesis it tests.

## 7. Reviewer checklist
What should a native-speaker reviewer specifically check:
- Formality level appropriate for {target_market} business norm?
- Idioms / expressions read as natural?
- CTA verb feels right (push vs pull cultures use different verbs)?
- Any phrasing that sounds 'translated'?

CRITICAL RULES
- Preserve FUNCTION, not form. Literal translation often kills CTA performance.
- Back-translation is REQUIRED so non-target-language reviewers can validate.
- Cultural / legal risk flags must be SPECIFIC, not generic.
- Untranslatable concepts get a strategy (replace / explain / drop / substitute), not a literal translation.
- Native-speaker review is REQUIRED before publishing — this prompt scaffolds, doesn't replace.

SOURCE
{source_copy}

Begin.""",
        "input_variables": [
            {"name": "source_copy", "type": "string", "description": "Source copy", "required": True, "example": "Stop wasting time on manual reports. Acme automates your entire reporting workflow in 5 minutes. Trusted by 10,000+ teams. Start free trial."},
            {"name": "source_market", "type": "string", "description": "Source language / market", "required": True, "example": "en-US, B2B SaaS audience (mid-market ops teams)"},
            {"name": "target_market", "type": "string", "description": "Target language / market", "required": True, "example": "ja-JP, B2B SaaS audience (large-enterprise operations)"},
            {"name": "purpose", "type": "string", "description": "Copy purpose", "required": True, "example": "Conversion: hero copy on landing page, primary CTA to start trial"},
            {"name": "brand_voice", "type": "string", "description": "Brand voice", "required": True, "example": "Direct, confident, slightly playful. Anti-corporate."},
            {"name": "legal", "type": "string", "description": "Legal constraints", "required": True, "example": "JP ad regulations require backing for any '#1' claim; '10,000+ teams' is verifiable globally so OK."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: source decomposition, localized copy + back-translation, what changed and why, untranslatable concepts strategy, cultural/legal risk flags, A/B-test recommendations, reviewer checklist.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on cultural-fit nuance + honest about untranslatable concepts."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong on common pairs (en→es, en→fr, en→ja, en→de). Less on rarer pairs."},
            {"model": "gemini-1.5-pro", "compatibility": "excellent", "notes": "Strong multilingual; good at long-form localization."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for simple copy + common languages; thins on cultural-risk surfacing."},
        ],
        "variations": [
            {"label": "Six-market batch", "description": "Localize for 6 markets at once.", "prompt_snippet": "Apply to a LIST of target markets. Output one localized version per market + a cross-market comparison highlighting which framings worked uniformly vs which required market-specific re-framing."},
            {"label": "Transcreation mode", "description": "Heavy creative liberty.", "prompt_snippet": "Allow significant creative deviation from source — preserve only the FUNCTIONAL goal. Output 3 wildly different variants in target market that test different cultural angles."},
            {"label": "QA / back-check", "description": "Audit an existing localization.", "prompt_snippet": "Given source + existing localization, audit: where does the localization preserve function? Where does it drift? Cultural / legal issues missed?"},
        ],
        "failure_modes": [
            {"symptom": "Literal translation, not localization.", "fix": "Re-pin: 'preserve FUNCTION not form. A localized line might share zero words with the source.'"},
            {"symptom": "Misses cultural risk.", "fix": "Force section 5: 'minimum 2 cultural-risk callouts unless none truly apply (explicit statement of why).'"},
            {"symptom": "Back-translation matches source too closely.", "fix": "If back-translation = source, you over-translated. Re-do with more cultural adaptation."},
            {"symptom": "Vague untranslatable strategies.", "fix": "Require: 'each untranslatable concept gets one of: replace / explain / drop / substitute. With reasoning.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["press-release-from-bullet-points", "first-line-hook-generator", "before-after-image-comparison"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["localization", "transcreation"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Replaces a human translator?", "answer": "No — scaffolds work for a human native-speaker reviewer. The structure surfaces what a reviewer should check; speed-to-draft improves, final polish stays human."},
            {"question": "Why both localized AND back-translation?", "answer": "Back-translation lets a non-target-language reviewer (marketer, legal) validate without speaking the target language. Catches drift before publish."},
            {"question": "How do I pick A/B variants?", "answer": "Variant A (close to source) and Variant B (deep localization) bracket the spectrum. Variant C tests a counter-intuitive angle. Pick 2 to run; if budget allows 3rd, include C."},
            {"question": "What about right-to-left languages?", "answer": "The prompt handles the text; visual/layout adjustments (Arabic, Hebrew) need a separate design pass. Flag in the reviewer checklist."},
        ],
        "meta_title": "Marketing Copy Localization — Translation Prompt",
        "meta_description": "Localize marketing copy across cultures: preserve function, adapt cultural fit, flag legal/sensitivity risk, A/B variants for testing.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "technical-doc-translation-with-terms",
        "title": "Technical Doc Translation With Term Glossary",
        "tldr": "Translates technical documentation with a CONSISTENT terminology glossary, preserves code/identifiers untranslated, and surfaces target-language convention differences (units, examples, locale data).",
        "category": "translation",
        "tags": ["technical-writing", "translation", "documentation", "glossary"],
        "best_for_tags": ["devrel", "technical-writers", "saas-international"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "API docs localization", "example": "REST API docs translated to ja/de/es with consistent term usage and code blocks preserved."},
            {"scenario": "User-facing help center", "example": "Help articles localized; UI strings + technical terms aligned with product translations."},
            {"scenario": "SDK / library README", "example": "OSS library README translated; code examples adapted for locale conventions."},
            {"scenario": "Tutorial / quickstart", "example": "Quickstart guide localized; date / number / currency formats adapted."},
        ],
        "when_not_to_use": "Skip for legal contracts (use specialized translator). Skip for materials with regulatory implications (medical, financial — need certified translation).",
        "full_prompt": """You are a technical translator. Translate technical docs with a CONSISTENT term glossary; preserve code; adapt locale conventions.

INPUT
- Source doc: {source_doc}
- Source language: {source_lang}
- Target language: {target_lang}
- Existing term glossary (translated terms in target language): {existing_glossary}
- Product / domain context: {product_context}
- Reader profile: {reader_profile}        (e.g., 'mid-senior developers, intermediate {target_lang} fluency')

OUTPUT

## 1. Pre-translation glossary
Identify ALL technical terms in source. For each:
- **Source term:** ___
- **Translation in {target_lang}:** ___ (or 'keep in English — common practice in {target_lang} dev community')
- **Context where it appears:** ___
- **Alternatives considered:** ___ (and why rejected)

Reuse existing_glossary entries. NEW terms flagged for human-glossary-team review.

## 2. Code / identifier preservation rules
- Variable names, function names, class names: NEVER translate.
- Code comments: TRANSLATE.
- String literals in code: do NOT translate unless explicit instruction (could break tests / functionality).
- File paths, URLs, command names: NEVER translate.
- Error messages quoted from source: KEEP source + add target translation in parens if helpful.

## 3. Locale-convention adaptations
- **Dates:** {source_lang} format → {target_lang} format (e.g., MM/DD/YYYY → DD.MM.YYYY)
- **Numbers:** thousands separator + decimal point
- **Currency:** if domain uses currency, adjust
- **Examples:** if source uses culturally-specific examples (US names, US-only services), adapt
- **Units:** imperial vs metric

## 4. The translated document
Output the full translation. Maintain:
- Heading hierarchy
- Code blocks (verbatim)
- Links (translate link text; keep URLs; flag if URL should localize to {target_lang} version)
- Callouts and admonitions (translate body; keep type indicator)

## 5. Style notes for {target_lang}
Conventions specific to {target_lang} technical writing:
- Formal vs informal pronoun choice (for languages that distinguish).
- Active vs passive voice norms.
- Sentence-length expectations.
- Code-comment style.
- Numbered vs bulleted list conventions.

## 6. Terms flagged for review
Terms where the translation is uncertain or where consistency with other docs may matter:
- **Term + my translation + reasoning + what to verify.**

## 7. Untranslated and why
List anything KEPT in source language deliberately:
- Brand names, product names (per brand guide).
- Industry-standard terms used in {target_lang} dev community (e.g., 'API', 'webhook').
- Acronyms standardized internationally.

CRITICAL RULES
- Code / identifiers NEVER translated.
- Glossary CONSISTENT — same source term = same target translation throughout document.
- Locale conventions adapted (dates, numbers, examples).
- New terms flagged for human glossary-team validation.
- Style matches {target_lang} technical-writing norms, not literal source style.

SOURCE
{source_doc}

Begin.""",
        "input_variables": [
            {"name": "source_doc", "type": "string", "description": "Source document", "required": True, "example": "# Quickstart\\n\\nThis guide walks you through setting up Acme API in under 5 minutes...\\n\\n```python\\nfrom acme import Client\\nclient = Client(api_key=\"sk_...\")\\nresult = client.run()\\n```"},
            {"name": "source_lang", "type": "string", "description": "Source language", "required": True, "example": "en-US"},
            {"name": "target_lang", "type": "string", "description": "Target language", "required": True, "example": "ja-JP"},
            {"name": "existing_glossary", "type": "string", "description": "Existing translated terms", "required": False, "example": "client → クライアント; webhook → keep English; rate-limit → レート制限"},
            {"name": "product_context", "type": "string", "description": "Product / domain", "required": True, "example": "Acme SaaS — billing / payment automation for SMB e-commerce"},
            {"name": "reader_profile", "type": "string", "description": "Reader profile", "required": True, "example": "Mid-senior backend devs, native Japanese speakers comfortable reading English code"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: pre-translation glossary, code preservation rules, locale-convention adaptations, full translated doc, target-language style notes, flagged-for-review terms, untranslated terms with reasoning.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong consistency + honest flagging of new terms."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong for major pairs; can over-translate technical terms — re-pin keep-in-English rule for common dev terms."},
            {"model": "gemini-1.5-pro", "compatibility": "excellent", "notes": "Strong on long documents; handles glossary consistency well."},
            {"model": "claude-3-5-haiku", "compatibility": "good", "notes": "Workable; consistency slightly lower across long docs."},
        ],
        "variations": [
            {"label": "Multi-doc consistency", "description": "Translate a SET of docs with shared glossary.", "prompt_snippet": "Apply across multiple docs. Build a master glossary from doc 1; apply consistently across all subsequent docs. Output a final consolidated glossary."},
            {"label": "Glossary-only output", "description": "Just build the term glossary.", "prompt_snippet": "Skip the translation. Output ONLY the term glossary (source term → target translation + context). Used to prep before bulk translation."},
            {"label": "Translation review", "description": "Audit existing translation.", "prompt_snippet": "Given source + existing translation, audit: glossary inconsistencies, code-block accidents, locale conventions missed, style issues."},
        ],
        "failure_modes": [
            {"symptom": "Translates code identifiers.", "fix": "Hard rule: 'no translation of variable / function / class names. Code blocks copied verbatim except for COMMENTS.'"},
            {"symptom": "Inconsistent term translation.", "fix": "Force: 'glossary built FIRST. Once a term is translated, it stays translated the same way throughout.'"},
            {"symptom": "Misses locale conventions.", "fix": "Re-pin: 'dates, numbers, currency, examples MUST adapt to target locale. Flag every conversion.'"},
            {"symptom": "Over-translates dev jargon.", "fix": "Add: 'check existing target-language dev community usage. \"API\", \"webhook\", \"endpoint\" usually stay English in JP / DE / FR dev docs.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["marketing-copy-localization", "openapi-spec-from-handler", "code-comment-explainer"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["i18n", "technical-translation"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Should I translate API endpoint names?", "answer": "No. Endpoint paths, parameter names, header names stay in source. Only translate the descriptive prose AROUND them."},
            {"question": "What about error messages?", "answer": "Keep source error string + add target-language description in parens. Devs need to be able to grep for the literal error string in code/logs."},
            {"question": "How to handle ambiguous tech terms?", "answer": "Flag in section 6. Common cases: 'token' (auth token vs lexer token), 'context' (request context vs ML context), 'event' (DOM event vs message bus). Disambiguate before bulk translation."},
            {"question": "How do I keep glossary consistent across translators?", "answer": "Use this prompt with existing_glossary populated from a single source of truth (Crowdin, Smartling, internal glossary doc). All translators / all runs pull from the same."},
        ],
        "meta_title": "Technical Doc Translation With Terms — Translation Prompt",
        "meta_description": "Translate technical docs with consistent term glossary, preserved code blocks, and locale-convention adaptations.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "tone-preserving-translation",
        "title": "Tone-Preserving Translation",
        "tldr": "Translates while preserving the SPECIFIC tone (formal / playful / urgent / academic) of the source — by first naming the tone, then matching it in the target language's tone-register, not literal word choice.",
        "category": "translation",
        "tags": ["translation", "tone", "voice", "register"],
        "best_for_tags": ["writers", "marketers", "brand-teams"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Brand-voice translation", "example": "Acme's playful tone → ja/de/es; each language has different 'playful' register."},
            {"scenario": "Email-newsletter translation", "example": "Casual, mid-friend newsletter — needs to feel casual in target, not corporate-translated."},
            {"scenario": "Customer service script", "example": "Empathetic, calm tone → preserved across languages even when literal phrasing changes."},
            {"scenario": "Op-ed / blog translation", "example": "Author's distinct voice preserved across translation."},
        ],
        "when_not_to_use": "Skip for purely informational content (FAQs, terms-of-service) — tone matters less. Use the standard translation prompt instead.",
        "full_prompt": """You are a tone-preserving translator. Name the source tone, then match its FUNCTIONAL equivalent in the target language.

INPUT
- Source text: {source_text}
- Source language: {source_lang}
- Target language: {target_lang}
- Tone-relevant context: {context}        (publication, brand voice, intended reader)
- Critical phrases to keep: {keep_phrases} (e.g., brand-specific lines, slogans)

OUTPUT

## 1. Tone profile
Name the source tone across these axes:
- **Formality:** 1 (street casual) - 10 (academic / legal)
- **Energy / urgency:** 1 (calm / reflective) - 10 (urgent / shouty)
- **Warmth:** 1 (cold / clinical) - 10 (warm / intimate)
- **Authority:** 1 (deferential) - 10 (authoritative / expert)
- **Humor:** 1 (none) - 10 (joke-heavy)

Then in 2-3 sentences, characterize the OVERALL tone. (e.g., 'mid-formal mid-warm authoritative-but-not-arrogant tone of an experienced technical writer addressing peers.')

## 2. Target-language tone-register equivalent
The target language has its OWN tone scales. How does the target-language tone-register map?
- Equivalent {target_lang} register: ___
- Specific markers in {target_lang} that convey this tone (verb forms, pronouns, sentence rhythms, vocabulary register): ___
- What a {target_lang} native would write if they were producing this voice fresh: ___

## 3. The translation
Output the translated text. Calibrated to the target-language register, NOT the source-language register applied literally.

If multiple sentences should fundamentally change structure to match target-language tone, do so.

Critical phrases from {keep_phrases} retained verbatim or as agreed.

## 4. Tone-fidelity scorecard
For each axis from section 1, score the translation:
- Formality: target-language equivalent of source — match / drift up / drift down (with reason)
- Energy: ___
- Warmth: ___
- Authority: ___
- Humor: ___

If drift was intentional (e.g., target-language doesn't have an equivalent humor register), explain.

## 5. Phrases that LOST tone
Lines where the literal meaning translated but the TONE didn't carry. For each:
- Source: ___ (with tone signal: 'this is wry')
- Literal translation: ___ (would lose: ___)
- Tone-preserving translation: ___ (matches via: ___)

This is the most important section — surfaces where literal translation would have failed.

## 6. Phrases that GAINED meaning
Target-language phrases that carry extra associations the source didn't have:
- "[chosen target phrase] in {target_lang} can also imply ___; ensure that's acceptable."

Flag for reviewer.

## 7. Voice-test
Read the translation in the target-language reader's head. Does it sound TRANSLATED or NATIVE? If translated, flag the giveaways:
- Word-by-word literal stretches.
- Sentence rhythms not natural in {target_lang}.
- Mixed-register slips.

CRITICAL RULES
- Tone profile is NAMED EXPLICITLY before translation begins.
- Translation matches target-language tone-register, not literal source phrasing.
- Lost-tone phrases section is REQUIRED — usually the highest-value edit notes.
- Voice-test catches translationese.

SOURCE
{source_text}

Begin.""",
        "input_variables": [
            {"name": "source_text", "type": "string", "description": "Source text", "required": True, "example": "Look — your inbox isn't going to clear itself. We built this thing because watching smart people drown in email was getting frankly embarrassing."},
            {"name": "source_lang", "type": "string", "description": "Source language", "required": True, "example": "en-US"},
            {"name": "target_lang", "type": "string", "description": "Target language", "required": True, "example": "de-DE"},
            {"name": "context", "type": "string", "description": "Context", "required": True, "example": "Marketing email; B2B software audience; brand voice is direct and slightly cheeky"},
            {"name": "keep_phrases", "type": "string", "description": "Phrases to keep verbatim", "required": False, "example": "Brand name 'Acme' stays; tagline 'work smarter, not harder' has a localized version already approved"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Seven sections: source tone profile, target-language register equivalent, the translation, tone-fidelity scorecard per axis, lost-tone phrases with fixes, gained-meaning warnings, voice-test for translationese.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest at tone profiling + honest about lost-tone phrases."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong on common pairs; can default to mid-formal."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; weaker on humor-register matching."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for plain tones; humor / wry / sarcastic registers drop quality noticeably."},
        ],
        "variations": [
            {"label": "Style-matching to author", "description": "Match a specific author's style.", "prompt_snippet": "Given a target-language AUTHOR sample, calibrate translation to that author's voice. Output translation + which voice-tics from the author you used."},
            {"label": "Multi-tone exploration", "description": "Three variants at different tone levels.", "prompt_snippet": "Output the translation 3 ways: most-faithful-to-source-tone, mid-adapted, most-native-feeling. Used to pick the right balance."},
            {"label": "Brand-voice consistency", "description": "Match a documented brand voice.", "prompt_snippet": "Given a brand-voice doc in {target_lang}, calibrate translation. Audit drift from brand voice in translation."},
        ],
        "failure_modes": [
            {"symptom": "Translation reads 'translated.'", "fix": "Re-pin: 'voice-test in section 7. If sentence rhythm or word-choice feels word-by-word, restructure for target-language natural flow.'"},
            {"symptom": "Drift to mid-formal default.", "fix": "Force: 'tone scorecard with reasons. If drift was unintentional, restate target register and retranslate.'"},
            {"symptom": "Misses humor / wry tones.", "fix": "Add: 'humor markers in source — sarcasm, understatement, wry observation — need EQUIVALENT in {target_lang}, not literal. Flag if {target_lang} doesn\\'t have a clean equivalent.'"},
            {"symptom": "Loses brand-specific phrasing.", "fix": "Respect keep_phrases list rigorously. Don't paraphrase what should be verbatim."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["marketing-copy-localization", "press-release-from-bullet-points", "first-line-hook-generator"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["register", "voice"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why name tone explicitly?", "answer": "Tone is the first thing literal translation loses. Naming it forces the model to CONSIDER it instead of optimizing for word-equivalence. The tone profile becomes the target."},
            {"question": "What if the source uses sarcasm and target language doesn't?", "answer": "Use the closest equivalent register (irony, understatement) and flag in section 5. Sometimes the right answer is to restructure the message entirely with the same INTENT."},
            {"question": "Can I trust the voice-test?", "answer": "Use it as a smoke test, not a final check. A native speaker reviewer is the gold standard. The voice-test catches obvious translationese before a human reviews."},
            {"question": "What's the worst-case for this prompt?", "answer": "Very domain-specific brand voices the model hasn't seen examples of. Mitigate by passing a brand-voice doc + sample paragraphs of approved {target_lang} brand voice as input."},
        ],
        "meta_title": "Tone-Preserving Translation — Translation Prompt",
        "meta_description": "Translate while preserving source tone: explicit tone profiling, target-language register matching, lost-tone fix notes, voice-test.",
        "version": "v2.0",
        "release_status": "stable",
    },
    {
        "slug": "subtitle-translation-with-timing",
        "title": "Subtitle Translation With Timing",
        "tldr": "Translates subtitles respecting line-length, reading-speed, and timing constraints. Handles overlaps, splits, and culturally-specific dialogue with notes for the editor.",
        "category": "translation",
        "tags": ["subtitles", "translation", "video", "accessibility"],
        "best_for_tags": ["video-teams", "content-creators", "localization"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Tutorial video subtitles", "example": "30-min coding tutorial; subtitles in 5 languages with proper timing."},
            {"scenario": "Marketing video", "example": "60-sec product video → 8 languages of subtitles + on-screen text captions."},
            {"scenario": "Podcast → video clip", "example": "Audio clip turned into video; subtitles translate for new market."},
            {"scenario": "Interview / documentary", "example": "Long-form interview subtitles preserving speaker tone and timing."},
        ],
        "when_not_to_use": "Skip when timing data isn't available — you'd just be doing text translation. Skip for hard-of-hearing CAPTIONS (need different conventions: sound effects, music notes).",
        "full_prompt": """You are a subtitle translator. Translate respecting line-length, reading-speed, and timing constraints.

INPUT
- Source subtitles (SRT or VTT format with timestamps): {source_subtitles}
- Source language: {source_lang}
- Target language: {target_lang}
- Reading-speed target: {reading_speed}            (default 17 CPS — characters per second)
- Line-length max: {line_length_max}              (default 42 chars for most platforms)
- Lines per cue max: {lines_per_cue}              (default 2)
- Content context (genre, audience): {content_context}

OUTPUT

## 1. Translation constraints
Establish:
- Max characters per line: ___
- Max characters per cue (line × lines_per_cue): ___
- Reading-speed target (chars per second): ___
- Min cue duration: 1.0s (standard floor)
- Min gap between cues: 0.12s

## 2. The translated subtitles
Output in SRT or VTT format matching source. For each cue:

```
NN
HH:MM:SS,mmm --> HH:MM:SS,mmm
[translated line 1]
[translated line 2 if needed]
```

CRITICAL: text fits within line + cue limits. If translation is longer than fits:
- Condense (preserve MEANING, drop redundancy).
- Split across cues if natural.
- DO NOT extend cue duration.

## 3. Condensation log
Where you condensed:
- **Source:** [full source line]
- **Target (condensed):** ___
- **What was cut:** ___
- **Reason:** length constraint / reading-speed constraint.

## 4. Cultural notes for editor
- Idioms / jokes / references that don't translate directly — what choice was made.
- On-screen text mentioned by speaker (signs, screen text) — flag for graphic localization team.
- Pronouns where source ambiguity needs target-language resolution.

## 5. Timing adjustments suggested
If timing needs adjustment for {target_lang}:
- "{target_lang} averages 10-15% LONGER text for same meaning. Cue N may need extension."
- "Speaker pace is fast at NN:NN; consider re-timing this section."

For each: timestamp + proposed change.

## 6. Quality checks
- **Reading speed:** any cue >17 CPS? List with cue numbers.
- **Line length:** any line >42 chars? List.
- **Cue duration:** any cue <1.0s OR >7s? List.
- **Two-line wrap:** does each two-line cue split at natural language boundary (not mid-phrase)?

## 7. Editor sign-off checklist
- All cues fit reading-speed + line-length.
- Cultural notes reviewed.
- On-screen text flagged.
- Speakers consistent (same character → same gendered pronouns / verb endings).
- Tone matches source (formal/informal register consistent).

CRITICAL RULES
- Reading speed + line length are HARD constraints. Condense rather than extending duration.
- Condensation log is REQUIRED — editor needs to validate what was cut.
- Cue boundaries respect language: don't split mid-phrase across cues if avoidable.
- Pronoun ambiguity in source resolved with translator note (not assumed).

SOURCE
{source_subtitles}

Begin.""",
        "input_variables": [
            {"name": "source_subtitles", "type": "string", "description": "Source SRT/VTT subtitles", "required": True, "example": "1\\n00:00:00,000 --> 00:00:02,500\\nWelcome back to the channel.\\n\\n2\\n00:00:02,500 --> 00:00:05,000\\nToday we're talking about\\nthe brand new release."},
            {"name": "source_lang", "type": "string", "description": "Source language", "required": True, "example": "en-US"},
            {"name": "target_lang", "type": "string", "description": "Target language", "required": True, "example": "es-419 (Latin American Spanish)"},
            {"name": "reading_speed", "type": "string", "description": "Reading-speed target (CPS)", "required": False, "example": "17 CPS (Netflix standard)"},
            {"name": "line_length_max", "type": "string", "description": "Line-length max", "required": False, "example": "42 chars (YouTube / Netflix)"},
            {"name": "lines_per_cue", "type": "string", "description": "Lines per cue max", "required": False, "example": "2"},
            {"name": "content_context", "type": "string", "description": "Content context", "required": True, "example": "Tech YouTube channel, casual tone, audience 25-45"},
        ],
        "expected_output": {
            "format": "structured",
            "sample": "Seven sections: constraints, translated SRT/VTT, condensation log per cue cut, cultural notes for editor, timing adjustments suggested, automated quality checks, editor sign-off checklist.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strongest on condensation choices + cultural notes; respects constraints."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very strong on common pairs; can over-extend cue duration — re-pin hard constraint."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid for long videos; consistency strong."},
            {"model": "claude-3-5-haiku", "compatibility": "fair", "notes": "Workable for short subtitle files; thins on cultural-note quality."},
        ],
        "variations": [
            {"label": "Hard-of-hearing captions", "description": "Output captions, not subtitles.", "prompt_snippet": "Switch output to hard-of-hearing captions: include speaker labels, sound effects ([door creaks]), music ([emotional swell])."},
            {"label": "Forced-narrative subs", "description": "Output only foreign-language / on-screen text.", "prompt_snippet": "Output forced subtitles: only translate foreign-language passages or on-screen text. Skip dialogue already in target language."},
            {"label": "Multi-platform export", "description": "Different platforms have different rules.", "prompt_snippet": "Output 3 variants tuned for: Netflix (42 chars / 17 CPS), YouTube (33 chars), TikTok (no formal constraints but 25 CPS recommended)."},
        ],
        "failure_modes": [
            {"symptom": "Lines exceed length cap.", "fix": "Hard rule: 'check every line. If over cap, condense or split. Don\\'t emit lines over cap.'"},
            {"symptom": "Reading speed too high.", "fix": "Force: 'compute CPS = chars/duration for each cue. If >17 CPS, condense source meaning until under.'"},
            {"symptom": "Missing condensation log.", "fix": "Re-pin: 'every condensed cue logged with source/target/what-was-cut/why.'"},
            {"symptom": "Cultural references translated literally.", "fix": "Add: 'reference NOT recognizable in target culture? Substitute or annotate as translator note. Flag for editor.'"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "claude-3-5-haiku"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["video-frame-summarizer", "marketing-copy-localization", "tone-preserving-translation"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["subtitling", "captioning"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why 17 CPS?", "answer": "Netflix's standard for adult content. Children's content uses 12-14. Sports / breaking-news can go to 21. 17 is the safe default."},
            {"question": "How long should a cue stay on screen?", "answer": "Min 1.0s, max ~7s. Below 1s readers miss it; above 7s they read it twice and disengage. Most cues 2-4s."},
            {"question": "When to split a cue?", "answer": "When two-line cue would exceed 42 chars per line. Split at natural language boundary (clause, breath). Never mid-word, mid-name, or mid-quotation."},
            {"question": "What about song lyrics in subtitles?", "answer": "Wrap in italics + ♪ markers if instrumentals matter. Translate songs if narratively essential, otherwise indicate ♪ [song title or mood]. Confirm with publisher for copyright."},
        ],
        "meta_title": "Subtitle Translation With Timing — Translation Prompt",
        "meta_description": "Translate subtitles respecting line-length, reading-speed, and timing. Condensation log + cultural notes + quality checks for the editor.",
        "version": "v2.0",
        "release_status": "stable",
    },
]
