"""Translation prompts — going beyond literal word-for-word, with localization & register."""

RECORDS = [
    {
        "slug": "localized-translation-with-register",
        "title": "Localized Translation With Register Match",
        "tldr": "Translates text while preserving register (formal/casual/technical), localizing idioms and references for the target market — not a literal word-for-word translation.",
        "category": "translation",
        "tags": ["translation", "localization", "register", "idioms"],
        "best_for_tags": ["marketing", "product-content", "ux-strings"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "use_cases": [
            {"scenario": "Marketing copy", "example": "Translate product launch announcement EN → JA preserving the warm but professional tone."},
            {"scenario": "Product UX strings", "example": "Translate error messages EN → DE, keeping concise but polite German register for system messages."},
            {"scenario": "Customer support replies", "example": "Translate support email EN → FR while matching the original's apologetic but solution-focused tone."},
            {"scenario": "Help center articles", "example": "Translate documentation EN → ES-MX, replacing US-specific examples with regionally relevant ones."},
        ],
        "when_not_to_use": "Skip for legal contracts, regulatory text, or anything where word-for-word fidelity matters more than naturalness — use a certified translator with legal expertise.",
        "full_prompt": """You are a professional translator and localizer. Translate the source text into the target language with attention to register and locale.

INPUT
- Source text: {source_text}
- Source language: {source_language}
- Target language + locale: {target_language_locale}     (e.g., "Japanese (ja-JP)", "Spanish (es-MX)")
- Register: {register}                                    (formal / casual / technical / marketing-warm / etc.)
- Audience: {audience}                                    (e.g., "B2B SaaS buyers", "Mobile app users 18-35")
- Brand voice notes: {brand_voice_notes}                  (optional: any phrases to preserve or avoid)

YOUR JOB
1. Translate for MEANING, not word-for-word. The goal is the same emotional and informational effect on the reader.
2. Localize:
   - Idioms → equivalent target-language idioms or rewrite if no equivalent exists.
   - Cultural references (sports teams, holidays, food) → swap for regionally relevant ones if the original purpose was illustration.
   - Units, dates, currencies → convert to local conventions.
   - Honorifics & politeness markers → match what the audience expects in the target language.
3. Preserve register strictly. A formal source becomes formal target — not casual.
4. Keep brand-specific terms (product names, taglines) untranslated unless they're already known in localized form.

OUTPUT
First emit the translation cleanly (no commentary inline).

Then below, in a "Translator notes" section, list:
- Idioms/references you swapped and why.
- Anything you couldn't translate without losing meaning — explain the tradeoff.
- Any place where the source itself is ambiguous and you chose one interpretation.

Now translate.""",
        "input_variables": [
            {"name": "source_text", "type": "string", "description": "Text to translate", "required": True, "example": "Welcome aboard! Let's get you set up."},
            {"name": "source_language", "type": "string", "description": "Language of the source", "required": True, "example": "English (en-US)"},
            {"name": "target_language_locale", "type": "string", "description": "Target language and locale", "required": True, "example": "Japanese (ja-JP)"},
            {"name": "register", "type": "string", "description": "Tone/formality to preserve", "required": True, "example": "warm but professional"},
            {"name": "audience", "type": "string", "description": "Who's reading", "required": True, "example": "B2B SaaS buyers"},
            {"name": "brand_voice_notes", "type": "string", "description": "Brand-specific phrases or rules", "required": False, "example": "Never translate ‘OSS AI Hub’; use polite 'です/ます' forms; avoid casual 'よね'"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Translated text in target language, followed by a ‘Translator notes’ section listing idiom swaps, ambiguities, and tradeoffs.",
        },
        "few_shot_examples": [
            {
                "input": "EN → JA-JP, formal-warm B2B. Source: ‘Welcome aboard! Let's get you set up.’",
                "output": "ようこそお越しくださいました。さっそく初期設定を進めていきましょう。\n\nTranslator notes:\n- ‘Welcome aboard!’ → ‘ようこそお越しくださいました。’ The nautical idiom doesn't carry; substituted a warm-formal welcome phrase common in JP onboarding.\n- ‘Let's get you set up’ → ‘初期設定を進めていきましょう’ — preserves the collaborative ‘together’ feel via the volitional ましょう."
            }
        ],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong register preservation and useful translator notes."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good across major language pairs; weaker on rare locales."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Strong for European languages; can be too literal in Asian language pairs."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Decent for high-resource languages; significantly weaker for low-resource."},
        ],
        "variations": [
            {"label": "Marketing-only", "description": "More aggressive localization for marketing copy.", "prompt_snippet": "Add: ‘rewrite headlines for the target market — direct translation is usually wrong for ad copy.’"},
            {"label": "UI-strings batch", "description": "Translate many short strings with consistency.", "prompt_snippet": "Accept JSON object of strings; preserve keys; ensure consistent terminology across strings."},
            {"label": "Back-translation check", "description": "Self-verify by back-translating.", "prompt_snippet": "After translating, back-translate to source language and flag any meaning drift."},
        ],
        "failure_modes": [
            {"symptom": "Translation is word-for-word.", "fix": "Re-pin: ‘translate for meaning, not lexical match. If a literal translation reads stilted, rewrite.’"},
            {"symptom": "Register mismatch (casual translation of formal source).", "fix": "Add: ‘register match is mandatory; if uncertain, lean MORE formal in JP, KR, DE.’"},
            {"symptom": "Cultural reference dropped without substitute.", "fix": "Add: ‘when a reference doesn't carry, substitute an equivalent or rewrite the sentence — don't omit silently.’"},
            {"symptom": "Translator notes are generic (‘adapted for target audience’).", "fix": "Add: ‘notes must cite specific source phrases and the choices you made.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["voice-cloner-from-samples", "tighten-prose-30pct", "email-thread-respond"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["translation", "localization", "register"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Will this replace human translators?", "answer": "For low-stakes content, often yes. For brand-defining content, marketing campaigns, or legal copy: pair with a native-speaking reviewer."},
            {"question": "Does it handle right-to-left languages?", "answer": "Yes for Arabic and Hebrew; spot-check the punctuation and number direction in mixed-content sentences."},
            {"question": "How do I keep terminology consistent across a long document?", "answer": "Pass a glossary in brand_voice_notes; for very long documents, translate section by section and re-paste the glossary each time."},
        ],
        "meta_title": "Localized Translation With Register Match — Prompt",
        "meta_description": "Translate for meaning and locale — not word-for-word. Preserves register, swaps idioms, converts units, and flags ambiguities.",
    },
    {
        "slug": "back-translation-quality-check",
        "title": "Back-Translation Quality Check",
        "tldr": "Takes a translated text + the original, back-translates the target to the source language, and reports specific meaning drift, ambiguities, and untranslatables — a fast QA pass before publishing.",
        "category": "translation",
        "tags": ["translation", "qa", "back-translation", "quality"],
        "best_for_tags": ["translation-review", "vendor-qa", "localization"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "use_cases": [
            {"scenario": "Reviewing vendor translation", "example": "Vendor delivered Japanese translation — back-translate to English and flag meaning drift before paying."},
            {"scenario": "AI-translated content quality gate", "example": "Run AI translation through this check before publishing to catch confident-but-wrong translations."},
            {"scenario": "Marketing localization sign-off", "example": "Confirm the localized headline still hits the intended emotional beat."},
            {"scenario": "Documentation update", "example": "Source doc updated; check the existing translation against new source to find drift."},
        ],
        "when_not_to_use": "Skip for highly culturally-specific content — back-translation will always look ‘wrong’ even when the localization is correct. Use a native reviewer there.",
        "full_prompt": """You are a back-translation QA reviewer. Given a source text and its translation, evaluate quality.

INPUT
- Source language: {source_language}
- Target language: {target_language}
- Source text: {source_text}
- Translation: {translation}

YOUR PROCESS
1. Translate the {target_language} text back to {source_language} as literally as possible (not idiomatically — preserve the structure to expose differences).
2. Compare the back-translation to the original source. Find:
   - Meaning drift: places where the back-translation says something materially different.
   - Tone drift: register changed (e.g., formal source became casual).
   - Omissions: information present in source but missing from translation.
   - Additions: information in translation that wasn't in source.
   - Cultural localization: cases where the translation diverged from source intentionally to fit the target market — call these out as ‘intentional adaptation’ not errors.
3. For each finding, cite:
   - Source phrase (verbatim)
   - Translation phrase (verbatim)
   - Back-translation phrase (verbatim)
   - One-line classification: drift | tone | omission | addition | intentional-adaptation
   - Severity: blocker | major | minor

OUTPUT
## Back-translation
The literal back-translation.

## Findings
A table with rows: source | translation | back-translation | classification | severity.

## Verdict
One of: ready to publish | minor fixes needed | revision needed | major rework.

## Recommended fixes
For any blocker or major finding: a suggested correction in the target language.

Be specific and precise. Generic feedback is useless for translation QA.""",
        "input_variables": [
            {"name": "source_language", "type": "string", "description": "Original language", "required": True, "example": "English"},
            {"name": "target_language", "type": "string", "description": "Translated-to language", "required": True, "example": "Japanese"},
            {"name": "source_text", "type": "string", "description": "Original text", "required": True, "example": "Welcome aboard! Let's get you set up."},
            {"name": "translation", "type": "string", "description": "The translation to QA", "required": True, "example": "ようこそ!設定を始めましょう。"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Back-translation paragraph, findings table, verdict line, and recommended fixes for blockers/majors.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Honest about intentional localization vs error."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Strong; sometimes over-flags intentional adaptation."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid for European pairs; weaker for nuance in Asian languages."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Useful for spot-checks; back-translations can be sloppy on rare locales."},
        ],
        "variations": [
            {"label": "Multi-target batch", "description": "Same source, multiple target translations.", "prompt_snippet": "Accept N translations; emit findings table per target plus a comparison of which target is best."},
            {"label": "Sentence-level fingerprint", "description": "Score each sentence separately.", "prompt_snippet": "Add: ‘score each sentence 0–10 on fidelity; output bar chart in markdown.’"},
            {"label": "Vendor scoreboard", "description": "Aggregate quality across translations.", "prompt_snippet": "Accept multiple files from a vendor; emit summary scoreboard."},
        ],
        "failure_modes": [
            {"symptom": "Flags all localization as ‘drift’.", "fix": "Re-pin ‘intentional adaptation’ category and define it explicitly."},
            {"symptom": "Back-translation is too idiomatic (hides differences).", "fix": "Add: ‘back-translation must be literal/word-for-word, not natural — the goal is to expose structure differences.’"},
            {"symptom": "Verdict always ‘revision needed’ on stylistic differences.", "fix": "Add severity ladder examples: cosmetic tone shifts ≠ blockers."},
            {"symptom": "Recommended fixes are vague.", "fix": "Force concrete proposed replacement text in target language for every blocker/major."},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["localized-translation-with-register"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["translation-qa", "back-translation"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Is back-translation a reliable QA method?", "answer": "It catches meaning drift and omissions reliably. It does NOT catch register issues or idiomatic naturalness — those need a native reviewer."},
            {"question": "Can I use one model for translation and another for back-translation?", "answer": "Yes — and you should, when stakes are high. Different model biases surface different issues."},
            {"question": "How fast is this in practice?", "answer": "A 500-word document takes ~30 seconds with Sonnet/4o. Use for last-mile QA, not as the only review."},
        ],
        "meta_title": "Back-Translation Quality Check — Prompt",
        "meta_description": "Back-translate a translation and surface meaning drift, omissions, register changes, and intentional localization — fast translation QA pass.",
    },
    {
        "slug": "transliteration-name-spelling",
        "title": "Name and Brand Transliteration",
        "tldr": "Transliterates names and brand terms between writing systems with multiple acceptable variants ranked by frequency — for documents, business cards, and account setup.",
        "category": "translation",
        "tags": ["transliteration", "names", "branding", "writing-systems"],
        "best_for_tags": ["international-business", "branding", "localization"],
        "difficulty_tier": "beginner",
        "featured": False,
        "use_cases": [
            {"scenario": "Business cards for international clients", "example": "Transliterate ‘Chad Anderson’ into Katakana, Hangul, and Cyrillic — get ranked variants."},
            {"scenario": "Brand expansion to new market", "example": "Decide between transliterating brand name or using English-as-foreign-luxury convention in JA/CN."},
            {"scenario": "Document preparation for visa/legal", "example": "Consistent transliteration of names across documents."},
            {"scenario": "Voice assistant pronunciation hint", "example": "Get phonetic guides for non-native speakers."},
        ],
        "when_not_to_use": "Skip for legal documents requiring official transliteration (passport-aligned spellings) — use the form the official document uses.",
        "full_prompt": """You are a transliteration specialist. Given a source name (or brand term), produce transliterations across the requested writing systems.

INPUT
- Source: {source}
- Source language/script: {source_language_script}
- Target scripts: {target_scripts}                  (e.g., ["Katakana (Japanese)", "Hangul (Korean)", "Cyrillic (Russian)", "Simplified Chinese characters"])
- Use case: {use_case}                              (e.g., "business card", "brand name for marketing", "legal document")

OUTPUT
For each target script:

### {script}
- Primary transliteration: {variant}
- Alternates (if multiple are widely accepted): list with one-line note on usage
- Pronunciation guide for source-language speakers: e.g., "Kuh-NEE-luh"
- Notes:
  - Any character that has multiple valid choices (e.g., Cyrillic 'и' vs 'й')
  - Cultural connotations of specific characters chosen (especially Chinese: some characters carry connotations that affect brand fit)
  - Whether the brand convention in this market is to transliterate at all, or to keep the English form as a brand asset

CRITICAL FOR CHINESE TRANSLITERATION
For brand names entering Chinese markets, evaluate:
- Phonetic match
- Character meaning (the chosen characters should have positive or neutral connotations)
- Visual aesthetic

End with a single RECOMMENDATION for each market: transliterate, partial transliterate, or keep English.""",
        "input_variables": [
            {"name": "source", "type": "string", "description": "Name or term to transliterate", "required": True, "example": "OSS AI Hub"},
            {"name": "source_language_script", "type": "string", "description": "Source script", "required": True, "example": "Latin (English)"},
            {"name": "target_scripts", "type": "string", "description": "Comma-separated target scripts", "required": True, "example": "Katakana, Hangul, Simplified Chinese, Cyrillic"},
            {"name": "use_case", "type": "string", "description": "How the transliteration will be used", "required": True, "example": "Brand name for marketing in JP, KR, CN, RU markets"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "One section per target script with primary, alternates, pronunciation, notes, and a market-level recommendation.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on character connotation analysis for Chinese."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally misses regional alternates."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; weaker on Chinese brand fit analysis."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Adequate for common names; weaker on rare characters."},
        ],
        "variations": [
            {"label": "Phonetic-only", "description": "Skip the brand fit analysis.", "prompt_snippet": "Omit character connotations; output only phonetic transliteration + alternates."},
            {"label": "Cross-system table", "description": "Single table across all scripts.", "prompt_snippet": "Replace per-script sections with a single comparison table: source | script | primary | alternates | notes."},
            {"label": "Brand-fit deep dive", "description": "Chinese only, full brand analysis.", "prompt_snippet": "Focus on Chinese: produce 3 candidate transliterations, each with character meaning, market positioning, and risk."},
        ],
        "failure_modes": [
            {"symptom": "Only one variant given when multiple are standard.", "fix": "Add: ‘when more than one is in active use, list all and note when each is preferred.’"},
            {"symptom": "Missed character connotations in Chinese.", "fix": "Re-pin Chinese-specific rule; require explicit meaning gloss per character."},
            {"symptom": "Transliteration that's phonetically right but visually clunky.", "fix": "Add: ‘for brand use, optimize for visual + phonetic; for legal use, optimize for phonetic alignment to passport/ID.’"},
            {"symptom": "Mixed script transliteration (some hiragana, some katakana).", "fix": "Add: ‘use the script that's culturally expected for the entity type (foreign brands = katakana; foreign person names = katakana; native concepts = mix accordingly).’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["localized-translation-with-register"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["transliteration", "writing-system"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why are there multiple correct transliterations?", "answer": "Different romanization/transliteration systems exist (Hepburn vs Kunrei-shiki for Japanese, Pinyin vs Wade-Giles for Chinese). Default to the most widely used in the target market today."},
            {"question": "Should my brand always transliterate?", "answer": "No. Many global brands (Apple, Google, Sony) use English in some markets as a luxury/foreign-modern signal. Use the recommendation to decide per market."},
            {"question": "How do I avoid offensive character choices in Chinese?", "answer": "Always validate with a native speaker. The model catches most issues but Chinese character connotations are dense; a final human check is essential for brand launches."},
        ],
        "meta_title": "Name and Brand Transliteration — Prompt",
        "meta_description": "Transliterate names and brand terms across writing systems with ranked variants, pronunciation guides, and brand-fit analysis for Chinese.",
    },
    {
        "slug": "subtitle-translator-with-timing",
        "title": "Subtitle Translator With Timing-Aware Compression",
        "tldr": "Translates subtitles (SRT/VTT) into a target language while compressing each line to fit the on-screen reading time — preserves meaning while respecting the 17–21 characters-per-second rule.",
        "category": "translation",
        "tags": ["subtitles", "translation", "video", "localization", "accessibility"],
        "best_for_tags": ["video-localization", "education-content", "yt-creators"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "YouTube creator localizing videos", "example": "Translate English SRT → Japanese SRT respecting 17 chars/sec reading speed."},
            {"scenario": "Online course platform", "example": "Localize 20 hours of lectures; subtitle file generated per language."},
            {"scenario": "Documentary localization", "example": "Preserve dramatic timing of original; compress translation to fit cuts."},
            {"scenario": "Conference talk subtitle prep", "example": "Live-captioned talk → polished bilingual subtitles."},
        ],
        "when_not_to_use": "Skip for dubbing or voiceover — those require lip-sync and voice acting considerations the subtitle prompt isn't built for.",
        "full_prompt": """You are a subtitle translator. Translate SRT/VTT subtitles into the target language WITHOUT exceeding on-screen reading speed.

INPUT
- Source subtitles: {srt_or_vtt}
- Source language: {source_language}
- Target language: {target_language}
- Reading speed cap: {chars_per_second} characters per second (default 17)
- Max chars per line: {max_chars_per_line} (default 42)
- Max lines per cue: 2

YOUR RULES
1. Each cue keeps its timing. You do NOT split or merge cues.
2. Each cue's translation must fit within (cue_duration_seconds * chars_per_second).
3. If a literal translation would exceed the budget:
   - Compress: cut filler ("you know", "basically", "um"), tighten phrasing, use shorter synonyms.
   - If still over budget after compression, sacrifice nuance to keep core meaning.
4. Two-line cues: break at a natural pause point. Avoid splitting noun phrases.
5. Preserve emphasis cues: italics in source → italics in target.

OUTPUT
Return the translated SRT/VTT in valid format. Below the file, in a "Compression notes" section, list any cue where compression sacrificed meaning, with:
- Cue number
- Original (translated literally) — what it would have said
- Final (compressed) — what it actually says
- What was lost

Begin.""",
        "input_variables": [
            {"name": "srt_or_vtt", "type": "string", "description": "SRT or VTT subtitle file contents", "required": True, "example": "1\n00:00:01,000 --> 00:00:04,000\nWelcome to today's lecture on neural networks.\n"},
            {"name": "source_language", "type": "string", "description": "Source language", "required": True, "example": "English"},
            {"name": "target_language", "type": "string", "description": "Target language", "required": True, "example": "Japanese"},
            {"name": "chars_per_second", "type": "integer", "description": "Reading speed cap", "required": False, "example": "17"},
            {"name": "max_chars_per_line", "type": "integer", "description": "Max chars per displayed line", "required": False, "example": "42"},
        ],
        "expected_output": {
            "format": "text",
            "sample": "Translated SRT/VTT file in target language, followed by a Compression notes section.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong at respecting timing budget; useful compression notes."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally exceeds chars/sec on long cues — verify."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; struggles with two-line break decisions in Asian languages."},
            {"model": "llama-3-70b-instruct", "compatibility": "fair", "notes": "Acceptable for short videos; consistency issues on long files."},
        ],
        "variations": [
            {"label": "Educational content", "description": "Preserve technical terms unchanged.", "prompt_snippet": "Add: ‘technical terms appearing in slides or chyrons remain in original language with localized explanation below if space allows.’"},
            {"label": "Forced narratives only", "description": "Translate only forced narratives.", "prompt_snippet": "Filter input to only cues marked as forced (on-screen text translations); skip dialogue."},
            {"label": "Multi-language batch", "description": "Same source → multiple target languages.", "prompt_snippet": "Generate target SRTs for {languages}; each respects its own char/sec norm."},
        ],
        "failure_modes": [
            {"symptom": "Exceeds chars/sec on dense cues.", "fix": "Re-pin and add ‘verify cue_duration_seconds * chars_per_second BEFORE emitting; if over, compress further.’"},
            {"symptom": "Splits noun phrases across lines awkwardly.", "fix": "Add: ‘line break must be at a natural pause; if no good break exists, rewrite to two shorter sentences.’"},
            {"symptom": "Loses meaning entirely on compression.", "fix": "Force compression notes; tune chars/sec up if too aggressive."},
            {"symptom": "Breaks SRT format.", "fix": "Add: ‘output must validate as SRT — cue numbers, timestamps in HH:MM:SS,mmm --> HH:MM:SS,mmm, blank line between cues.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3-70b-instruct"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["localized-translation-with-register", "back-translation-quality-check"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["subtitle", "video-localization"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why 17 chars per second?", "answer": "Netflix's research-based standard for sustained reading comfort. BBC uses 15 for kids' content; tech/gaming creators sometimes push to 20."},
            {"question": "Does this work for any language pair?", "answer": "Yes, but the char/sec budget should adjust: Chinese/Japanese readers are slower per character, so use lower caps (8–10 for kanji-heavy text)."},
            {"question": "Can I run this on a 2-hour film?", "answer": "Yes, but chunk by scene to avoid context loss. Concatenate the SRTs back at the end."},
        ],
        "meta_title": "Subtitle Translator With Timing-Aware Compression",
        "meta_description": "Translate SRT/VTT subtitles into a target language while respecting reading-speed caps and on-screen line limits — Netflix-grade subtitle output.",
    },
]
