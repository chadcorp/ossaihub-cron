"""Creative prompt library — v2 authored (2026-05-14)."""

RECORDS = [
    {
        "slug": "story-with-character-arc",
        "title": "Short Story with Explicit Character Arc",
        "category": "creative",
        "tldr": "Generate a short story (800-1500 words) with explicit 3-act structure, named character arc (want→learn→change), and a satisfying ending that lands the arc.",
        "tags": ["fiction", "story", "arc"],
        "best_for_tags": ["fiction", "short-story", "creative-writing"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You write short fiction with structure. Most AI-written stories are atmospheric mush; you do the opposite — explicit arc, named conflict, earned resolution.\n\n"
            "INPUTS:\n"
            "- premise: 1-2 sentence story seed\n"
            "- protagonist: {name, age, occupation, want, secret_fear}\n"
            "- setting: time + place + 1-2 sensory anchors\n"
            "- length_target: word count (default 1000)\n"
            "- tone: literary | thriller | comedy | quiet | other\n\n"
            "STRUCTURE (3-act):\n"
            "1. ACT 1 (25%): Establish protagonist's want + flaw. End with the inciting incident.\n"
            "2. ACT 2 (50%): Pursuit of want. Escalating obstacles. Midpoint reversal — what they thought they wanted isn't enough. Lowest point at 75%.\n"
            "3. ACT 3 (25%): Acts on what they learned. Resolution lands the arc — not the want.\n\n"
            "CRAFT RULES:\n"
            "- Open with action or specific image, never a weather report or 'X always wondered'.\n"
            "- Dialogue does double duty — reveals character AND advances plot.\n"
            "- One sensory anchor per scene; reuse it for resonance at climax.\n"
            "- The protagonist must CHOOSE at the climax; coincidence isn't an ending.\n"
            "- End on an image, not an explanation. Trust the reader.\n\n"
            "FORBIDDEN: 'In a world where...', 'Little did they know', 'She felt a chill', 'Suddenly...', shrugging, sighing, 'looked at each other and nodded'.\n\n"
            "Begin the story."
        ),
        "input_variables": [
            {"name": "premise", "type": "string", "description": "1-2 sentence story seed", "required": True, "example": "A 60-year-old apiarist discovers her bees have stopped pollinating her late husband's roses."},
            {"name": "protagonist", "type": "Protagonist", "description": "Character spec", "required": True, "example": "{name:'Marta', age:60, occupation:'retired biology teacher / apiarist', want:'to keep the roses alive through the anniversary', secret_fear:'that grief has made her irrelevant'}"},
            {"name": "setting", "type": "string", "description": "Time + place + sensory anchors", "required": True, "example": "Northern Vermont, late October. Sensory anchors: woodsmoke, frost on the kitchen window."},
            {"name": "length_target", "type": "integer", "description": "Word count target", "required": False, "example": "1200"},
            {"name": "tone", "type": "string", "description": "literary | thriller | comedy | quiet", "required": True, "example": "quiet"},
        ],
        "expected_output": {"format": "text", "sample": "Marta found the dead bee on her husband's pillow.\n\nIt was the third one this week, and the roses outside had stopped opening...\n\n[1100 words, ending with Marta lifting a single rose to the kitchen window, watching the frost retreat from where her breath touched the glass]"},
        "use_cases": [
            {"scenario": "Newsletter weekly fiction", "example": "Substack publisher writes a 1000-word story per week; this prompt produces the v1 from a premise."},
            {"scenario": "Writing-group warmups", "example": "Pass a writing-prompt to the group + this prompt's output; discuss what worked/didn't."},
            {"scenario": "Submission package", "example": "Generate 3 versions of a story with different tones (literary/quiet/thriller) — pick the one that lands."},
            {"scenario": "Anthology contribution", "example": "Theme-specific anthology open call; this prompt drafts a candidate quickly."},
        ],
        "when_not_to_use": "Don't use for novel-length work (loses cohesion past ~3000 words). Also skip for highly experimental fiction — the rigid 3-act structure is the wrong tool.",
        "few_shot_examples": [
            {
                "input": "premise: 'A junior nurse discovers her supervisor is falsifying time-of-death records.' protagonist: {Lila, 26, ICU nurse 8mo into job, wants to keep her job, fears she's not tough enough}. tone: thriller. length: 1200",
                "output": "[Opens on Lila finding a discrepancy in the chart — bed 12 timestamp is wrong by 14 minutes. Act 1: she confronts the supervisor obliquely, gets brushed off. Inciting incident: the patient's family asks about exact time. Act 2: Lila investigates 3 more charts, finds 2 more discrepancies. Midpoint reversal: she realizes the supervisor isn't covering errors — she's covering for someone else. Lowest point: Lila realizes the someone else is her own mentor on the unit. Act 3: Lila reports both, knowing it ends her standing on the unit. Final image: she walks past the supervisor in the hallway and doesn't look away.]",
            }
        ],
        "model_compatibility": [
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best for literary tone and earned-arc endings."},
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strong default; especially good at thriller pacing."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Reliable structure; sometimes over-tells the theme at the climax."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Structure holds; prose can be flat."},
        ],
        "variations": [
            {"label": "Flash fiction (300 words)", "description": "Compressed arc.", "prompt_snippet": "length_target: 300. Skip explicit acts; one inciting incident → one decision → final image."},
            {"label": "POV shift", "description": "Second person or epistolary.", "prompt_snippet": "POV: 2nd person ('You found the dead bee...') or epistolary (letters/emails between two characters). Adjust dialogue rules accordingly."},
            {"label": "Genre-rule strict", "description": "Hard genre conventions.", "prompt_snippet": "Append genre conventions: mystery requires a fair-play clue trail; romance requires an emotional turning point at the midpoint; horror requires escalating dread, not a sudden monster."},
        ],
        "failure_modes": [
            {"symptom": "Atmospheric opening with no action", "fix": "Forbidden-opens rule enforced — always open with concrete action or specific image"},
            {"symptom": "Coincidence ending (deus ex machina)", "fix": "Climax must be a CHOICE by protagonist; coincidence is disqualifying"},
            {"symptom": "Tells the theme at the end ('She had finally learned that...')", "fix": "End on image, not explanation; trust the reader"},
            {"symptom": "Dialogue is pure plot delivery, no character voice", "fix": "Each character must speak differently; reread dialogue with character names removed — can you tell who's who?"},
        ],
        "tested_with": {"models": ["claude-opus-4", "claude-sonnet-4-5", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["dialogue-natural-back-and-forth", "worldbuilding-coherent", "poem-with-form-constraint"],
        "related_tool_slugs": ["scrivener", "obsidian"],
        "related_glossary_slugs": ["three-act-structure", "character-arc", "show-dont-tell"],
        "faq": [
            {"question": "How specific should the premise be?", "answer": "Specific enough that two writers given the same premise would write different stories. 'A nurse discovers fraud' is too vague; 'A junior nurse finds her supervisor falsifies TOD records' is right."},
            {"question": "Should the protagonist always change?", "answer": "Yes — that's the difference between a story and an anecdote. Even a tragedy ends with the protagonist understanding what they couldn't change."},
            {"question": "Can it write a series?", "answer": "Not cohesively past 3 stories with the same protagonist. Use the WORLDBUILDING prompt for shared-universe consistency."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Short Story with Character Arc — 3-Act, Earned Ending",
        "meta_description": "Generate short fiction with explicit 3-act structure, named character arc, and a chosen (not coincidental) resolution.",
    },

    {
        "slug": "dialogue-natural-back-and-forth",
        "title": "Natural Dialogue Between Characters",
        "category": "creative",
        "tldr": "Write naturalistic dialogue between 2-4 characters with distinct voices, subtext, interruptions, and forward narrative momentum.",
        "tags": ["dialogue", "fiction", "voice"],
        "best_for_tags": ["dialogue", "screenwriting", "fiction"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You write dialogue that sounds real, not AI-clean. Real people interrupt, contradict themselves, deflect, and rarely answer the question asked.\n\n"
            "INPUTS:\n"
            "- characters: list of {name, voice_signature (3-5 word descriptor), agenda (what they want from this conversation), secret (what they're not saying)}\n"
            "- setting: where + when (1 sentence)\n"
            "- inciting_question: what kicks off the conversation\n"
            "- desired_outcome: what should be revealed or shifted by end\n\n"
            "CRAFT RULES:\n"
            "- Each character gets a distinct voice — rhythm, vocabulary, contraction usage. The reader should know who's talking without name tags.\n"
            "- Real dialogue has subtext: what's said ≠ what's meant. Surface 2-3 instances.\n"
            "- People interrupt. Use em-dashes for cut-offs.\n"
            "- People rarely answer the question. They deflect, ask their own question, change subject.\n"
            "- Action beats > dialogue tags. Use 'She picked up the menu' not 'she said annoyed'.\n"
            "- One character's silence can be the loudest beat.\n\n"
            "FORBIDDEN: 'They looked at each other and laughed', 'He sighed deeply', 'She rolled her eyes', monologues longer than 4 sentences, mutual agreement before page 2.\n\n"
            "OUTPUT: dialogue with sparse action beats. No prose-style narration.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "characters", "type": "list[Character]", "description": "2-4 characters with voice + agenda + secret", "required": True, "example": "[{name:'Dad', voice:'short sentences, deflects with questions', agenda:'find out if she's drinking again', secret:'he's been drinking too'}, {name:'Daughter', voice:'long sentences with parentheticals, hyper-articulate', agenda:'borrow $400', secret:'she's been sober 90 days and is terrified to ask for help'}]"},
            {"name": "setting", "type": "string", "description": "Where + when", "required": True, "example": "A diner, 11pm on a Tuesday."},
            {"name": "inciting_question", "type": "string", "description": "Opening question or premise", "required": True, "example": "She asks how his week was."},
            {"name": "desired_outcome", "type": "string", "description": "What should shift by the end", "required": True, "example": "By the end, both have asked for help without using the words 'help' or 'sober'."},
        ],
        "expected_output": {"format": "text", "sample": "DAUGHTER  How was your week?\n\nDAD  (stirring his coffee)  Long. You?\n\nDAUGHTER  Same. I—\n\nDAD  You eat? You should eat.\n\nShe looks at the menu. Doesn't pick it up.\n\nDAUGHTER  Dad. About rent—\n\nDAD  You need money.\n\nDAUGHTER  Not a lot.\n\nDAD  How much.\n\n[Subtext: the silence before 'Not a lot' is the entire conversation about her sobriety]"},
        "use_cases": [
            {"scenario": "Screenplay scene drafting", "example": "Screenwriter has the beats but needs the dialogue; this prompt produces v1 with character voice intact."},
            {"scenario": "Stuck novel scene", "example": "Novelist knows characters need to argue but can't hear them; this prompt cracks open the voices."},
            {"scenario": "Podcast script", "example": "2-host interview format with distinct voices; this prompt drafts the back-and-forth before recording."},
            {"scenario": "Game-narrative branching", "example": "RPG dialogue with multiple character agendas — useful for branching responses."},
        ],
        "when_not_to_use": "Don't use for purely informational dialogue (e.g., textbook examples). Also skip for monologues — different prompt territory.",
        "few_shot_examples": [
            {
                "input": "characters: [{name:'Maya', voice:'precise, scientist', agenda:'fire her chief of staff', secret:'she's wrong about why'}, {name:'Sam', voice:'storyteller, deflective', agenda:'keep his job', secret:'he already accepted another offer'}]. setting: 'CEO office, 4pm Friday.' inciting: Maya: 'Sit down, Sam.'",
                "output": "MAYA  Sit down, Sam.\n\nSAM  (he sits, but leaves the door open)  Crazy week, huh.\n\nMAYA  Close the door.\n\nHe gets up. Closes the door. Sits again.\n\nSAM  So what's—\n\nMAYA  When did you know.\n\nSAM  Know what.\n\nA pause.\n\nMAYA  The board call. Wednesday. You knew Wednesday morning what they were going to ask.\n\nSAM  Maya—\n\nMAYA  Don't.\n\nSAM  (after a beat)  Tuesday night.\n\nMAYA  Why didn't you—\n\nSAM  Because I wasn't sure you'd take the answer.\n\nShe looks at him for a long time.\n\nMAYA  I'm letting you go.\n\nSAM  Okay.\n\nMAYA  ... Okay?\n\nSAM  (smiling for the first time)  Okay.\n\nMAYA  You already—\n\nSAM  Tuesday morning.\n\n[Subtext: Maya thinks she's firing Sam for disloyalty; Sam already had his exit. Neither says it.]",
            }
        ],
        "model_compatibility": [
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best at subtext and voice differentiation."},
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Reliable default; pacing strong."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Sometimes over-resolves the tension; instruct 'leave subtext unspoken'."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Voices can collapse to similar; explicit voice_signature helps."},
        ],
        "variations": [
            {"label": "Argument", "description": "Conflict-driven; tension rises.", "prompt_snippet": "Both characters want incompatible things; conversation escalates. End on the line that makes reconciliation impossible (or one character backing down)."},
            {"label": "Reunion", "description": "After long absence.", "prompt_snippet": "Characters haven't spoken in 5+ years. Both have changed but are pretending they haven't. Subtext is the unchanged thing one of them desperately wants to know."},
            {"label": "Power asymmetry", "description": "Boss/employee, parent/child, etc.", "prompt_snippet": "Show the asymmetry through silences, interruption patterns, who picks up the check (action beats). Never state 'he was her boss'."},
        ],
        "failure_modes": [
            {"symptom": "All characters sound the same", "fix": "Require voice_signature input; test by removing name tags and checking if speakers are still identifiable"},
            {"symptom": "Everyone answers questions directly", "fix": "Real dialogue is deflective; require 3+ instances where a character changes subject instead of answering"},
            {"symptom": "On-the-nose subtext ('I'm not really angry about the dishes')", "fix": "Subtext is what's NOT said; characters should never state their hidden agenda explicitly"},
            {"symptom": "Mutual agreement too quickly", "fix": "Block resolution before page 2; introduce a new obstacle before harmony"},
        ],
        "tested_with": {"models": ["claude-opus-4", "claude-sonnet-4-5", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["story-with-character-arc", "worldbuilding-coherent"],
        "related_tool_slugs": ["scrivener", "finaldraft"],
        "related_glossary_slugs": ["subtext", "dialogue", "voice"],
        "faq": [
            {"question": "How long should dialogue scenes be?", "answer": "Most scenes work at 300-600 words. >800 starts to feel like a stage play; <200 doesn't earn the tension."},
            {"question": "How do I make my own characters distinct?", "answer": "Write each character's voice_signature in 5 words. If two characters share the descriptor, the prompt won't differentiate."},
            {"question": "Can it write inner monologue?", "answer": "Not well — use a different prompt. This one is built for spoken dialogue with action beats."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Natural Dialogue Prompt — Subtext, Interruption, Voice",
        "meta_description": "Generate dialogue with distinct character voices, subtext, interruptions, and forward momentum. No mutual nodding.",
    },

    {
        "slug": "worldbuilding-coherent",
        "title": "Coherent Worldbuilding from a Seed",
        "category": "creative",
        "tldr": "Build a coherent fictional setting from one seed concept — geography, factions, economy, conflicts, daily life — that holds together logically across 8-12 dimensions.",
        "tags": ["worldbuilding", "fiction", "speculative"],
        "best_for_tags": ["worldbuilding", "rpg", "speculative-fiction"],
        "difficulty_tier": "intermediate",
        "full_prompt": (
            "You build fictional worlds that hold together logically. The classic AI failure mode is decoration without consequence — pretty details that contradict each other. You don't do that.\n\n"
            "INPUTS:\n"
            "- seed: 1-2 sentence concept (e.g., 'A post-water-scarcity Mediterranean')\n"
            "- scope: novel | short-story | rpg-campaign | game-setting\n"
            "- tone: hopeful | bleak | satirical | grounded\n"
            "- existing_constraints (optional): things already established that future details must respect\n\n"
            "BUILD ACROSS 10 DIMENSIONS — each must respect the others:\n"
            "1. PHYSICAL: geography, climate, biome, what's scarce\n"
            "2. POLITICAL: who rules, how succession works, where legitimacy comes from\n"
            "3. ECONOMIC: what's exchanged, currency, top exports/imports\n"
            "4. SOCIAL: classes, family structures, marginalized groups, mobility\n"
            "5. RELIGIOUS / IDEOLOGICAL: belief systems, who they exclude, public rituals\n"
            "6. TECHNOLOGICAL: dominant tech, who controls it, what's still impossible\n"
            "7. DAILY LIFE: a typical morning for a commoner, a noble, a marginalized person\n"
            "8. CONFLICTS: 2-3 ongoing tensions (between factions, within factions, with environment)\n"
            "9. HISTORY: 3 events in the past 200 years that shaped the present\n"
            "10. LANGUAGE/NAMING: naming conventions for places, people, key concepts\n\n"
            "COHERENCE RULES:\n"
            "- The scarcity in (1) must drive the economy (3) and conflicts (8).\n"
            "- Tech (6) must explain or constrain politics (2).\n"
            "- Religion (5) must reflect the climate (1) or scarcity (1).\n"
            "- If two dimensions contradict, flag it explicitly and propose resolution.\n\n"
            "OUTPUT: markdown with 10 numbered sections, then a 'Coherence check' section listing 3-5 ways the dimensions reinforce each other.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "seed", "type": "string", "description": "1-2 sentence world concept", "required": True, "example": "A post-water-scarcity Mediterranean basin, 200 years after the last river dried."},
            {"name": "scope", "type": "string", "description": "novel | short-story | rpg-campaign | game-setting", "required": True, "example": "rpg-campaign"},
            {"name": "tone", "type": "string", "description": "hopeful | bleak | satirical | grounded", "required": True, "example": "grounded"},
            {"name": "existing_constraints", "type": "list[str]", "description": "Established facts to respect", "required": False, "example": "['No magic', 'Ancient seawater desalination ruins exist but no one knows how they worked']"},
        ],
        "expected_output": {"format": "markdown", "sample": "## 1. Physical\nThe Mediterranean basin, 200 years post-rivers. The sea remains (saltwater); freshwater comes only from dew-condensers, desalination ruins (rare working ones), and underground aquifers depleting at 2× recharge.\n\n## 2. Political\nThree dominant powers, each anchored on a working desalination ruin: Marseilles Confederacy (largest), Cyprus Compact (oldest), and the Naples Free Cities (most fragmented). Succession in all three is technical — you inherit power by maintaining the desalination plant your faction depends on...\n\n## Coherence check\n- Scarcity (water) → currency (water-credits) ✓\n- Working desal sites → political legitimacy ✓\n- Religion centered on rain-myths reflects climate (1) and shapes ritual life (7) ✓"},
        "use_cases": [
            {"scenario": "RPG campaign prep", "example": "GM has a seed; this prompt builds the world in 10 minutes that holds up over a 50-session campaign."},
            {"scenario": "Novel pre-writing", "example": "Author has a concept; runs this before chapter 1 so future details don't contradict."},
            {"scenario": "Game-design pitch", "example": "Indie team has a setting idea; this prompt produces the world-bible for the design doc."},
            {"scenario": "Sequel/shared universe consistency", "example": "Existing world has 5 books; pass existing_constraints from book 1-5 to keep book 6 coherent."},
        ],
        "when_not_to_use": "Don't use for realism-grounded contemporary fiction — the dimensions over-engineer. Also skip when the goal is intentionally surreal or absurdist; coherence is the wrong target.",
        "few_shot_examples": [
            {
                "input": "seed: 'A lunar colony where children outnumber adults 4:1 because the founders all died young'. scope: novel. tone: hopeful.",
                "output": "## 1. Physical\nMoon, low-gravity habitat on Sea of Tranquility. ~6,000 people, 4,800 under 18. Air is recycled; food is hydroponic; the surface is lethal for >15 minutes.\n\n## 2. Political\nGovernance by Council of Sixteen — elected by population aged 14+. Decisions binding for 7-year terms (the orbital period of resupply contracts).\n\n## 8. Conflicts\n- Generational: the Founders' Children (now 18-25) vs the Second Wave (5-14). Founders' Children remember the dying; Second Wave only knows the colony as 'home'.\n- External: Earth resupply has been late by 9 months. Stockpile holds 14 months. Council is rationing publicly but the Founders' Children remember the last famine.\n- Internal/factional: who controls the surface excursion permits — 4 deaths last year, all under 20.\n\n## Coherence check\n- High child:adult ratio → schools are central institutions → Council governance reflects this ✓\n- Air recycling tech is everywhere → maintenance skill = political power ✓\n- Founders dying young → all current leadership is grief-shaped ✓",
            }
        ],
        "model_compatibility": [
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Best for novel-scope worlds where coherence over 100k words matters."},
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Strong default; fast for RPG-scope."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Good at the breadth; sometimes over-decorates."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Workable; expect to manually check coherence across dimensions."},
        ],
        "variations": [
            {"label": "Single-dimension deep-dive", "description": "Pick one dimension and go 5x deeper.", "prompt_snippet": "Replace the 10-dimension scan with: pick one dimension (e.g., economic) and produce 10 sub-aspects (currency, taxation, labor, trade, etc.) at the same depth."},
            {"label": "Magic-system constrained", "description": "Hard-magic with rules and costs.", "prompt_snippet": "Add dimension #11 MAGIC SYSTEM: source, cost, who can wield, public attitude toward, what it can't do. Apply Sanderson's 3 laws (limits > powers, costs > abilities, established before resolution)."},
            {"label": "Hard-sci-fi grounded", "description": "Constrain by real physics.", "prompt_snippet": "Add constraint: all tech must be derivable from current physics (no FTL, no AGI, no faster-than-light comms). Force the worldbuilding to grapple with light-lag, energy budget, etc."},
        ],
        "failure_modes": [
            {"symptom": "Decorations contradict each other (e.g., 'rare water' world with rivers in every map)", "fix": "Coherence check section is mandatory; surface contradictions explicitly"},
            {"symptom": "Politics doesn't connect to physical (Why does X faction rule? Because the seed says so)", "fix": "Each political claim must trace back to a physical or economic root"},
            {"symptom": "All factions feel the same (no real difference in values)", "fix": "Force conflicts (8) to surface real value differences, not just territorial disputes"},
            {"symptom": "Religion is decoration only (mentioned but doesn't shape behavior)", "fix": "Daily-life dimension (7) must show religious practice in concrete actions"},
        ],
        "tested_with": {"models": ["claude-opus-4", "claude-sonnet-4-5", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["story-with-character-arc", "dialogue-natural-back-and-forth", "brainstorm-divergent"],
        "related_tool_slugs": ["worldanvil", "obsidian"],
        "related_glossary_slugs": ["worldbuilding", "coherence", "speculative-fiction"],
        "faq": [
            {"question": "How big should the world be?", "answer": "Scope-dependent. RPG: 1 region + 3 factions. Novel: 1 country + 5 factions. Short story: 1 city + 2 factions. Don't over-build."},
            {"question": "What if I want a deliberately incoherent world?", "answer": "Different tool. This prompt is built for coherence; flip to the brainstorm-divergent prompt if you want absurd."},
            {"question": "How do I keep coherence across many sessions?", "answer": "Store the output as your 'world-bible'; pass relevant sections as existing_constraints when generating new content."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Coherent Worldbuilding Prompt — 10 Dimensions, Coherence Check",
        "meta_description": "Build fictional worlds that hold together — geography, politics, economy, religion, daily life — with explicit coherence checks.",
    },

    {
        "slug": "ad-headline-variations",
        "title": "Ad Headline Variations (10 styles, 1 offer)",
        "category": "creative",
        "tldr": "Generate 10 ad headlines for the same offer in 10 distinct styles (curiosity, urgency, contrarian, social proof, etc.) — ready to A/B test.",
        "tags": ["ads", "copy", "marketing"],
        "best_for_tags": ["ad-copy", "marketing", "ab-testing"],
        "difficulty_tier": "beginner",
        "full_prompt": (
            "You generate ad headlines for the same offer in 10 distinct styles. Output is meant to be A/B tested — each headline takes a real swing, none should be hedged.\n\n"
            "INPUTS:\n"
            "- offer: what you're selling (1-2 sentences)\n"
            "- target_audience: who buys (1 sentence)\n"
            "- unique_angle: what's different vs competitors\n"
            "- character_limit: max length per headline (e.g., 90 for Google Ads, 40 for Twitter)\n"
            "- forbidden_words (optional): brand-voice exclusions\n\n"
            "GENERATE EXACTLY 10 HEADLINES, ONE IN EACH STYLE:\n"
            "1. CURIOSITY: cliffhanger that demands the click\n"
            "2. URGENCY: time/quantity pressure (only if real — no fake scarcity)\n"
            "3. SOCIAL PROOF: number/customer/credibility anchor\n"
            "4. CONTRARIAN: counter to the obvious belief in the category\n"
            "5. QUESTION: pose the buyer's real worry\n"
            "6. BENEFIT-FIRST: lead with the outcome, not the feature\n"
            "7. METAPHOR: surprising analogy\n"
            "8. SPECIFICITY: oddly precise number\n"
            "9. NEGATIVE: lead with the pain you remove\n"
            "10. INSIDER: speak to the buyer like a peer who knows\n\n"
            "EACH HEADLINE:\n"
            "- Under character_limit\n"
            "- Reads like real copy, not category-speak\n"
            "- Has a clear hook\n"
            "- Could stand alone without supporting copy\n\n"
            "OUTPUT FORMAT: numbered list with style label and 1-line 'why this might work' note.\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "offer", "type": "string", "description": "What you're selling", "required": True, "example": "OSS AI Hub: a free, audited directory of 2,300+ open-source AI tools with VRAM/cost calculators."},
            {"name": "target_audience", "type": "string", "description": "Who buys", "required": True, "example": "Developers + AI engineers comparing tools before adopting."},
            {"name": "unique_angle", "type": "string", "description": "Differentiator", "required": True, "example": "Daily audit catches dead repos; we don't list zombies."},
            {"name": "character_limit", "type": "integer", "description": "Max headline length", "required": True, "example": "60"},
            {"name": "forbidden_words", "type": "list[str]", "description": "Brand-voice exclusions", "required": False, "example": "['revolutionary', 'unleash', 'next-gen']"},
        ],
        "expected_output": {"format": "markdown", "sample": "1. **Curiosity:** \"The 47 dead AI tools your search results won't tell you about.\"\n   _Hooks search-fatigue; the number teases an audit._\n\n2. **Urgency:** \"Audited daily. Every dead repo flagged before you waste a sprint.\"\n   _Real urgency — sprint time is the buyer's currency._\n\n3. **Social proof:** \"2,300+ tools. 2,300+ daily audits. Trusted by 80k devs/week.\"\n   _Triple-stack of numbers builds credibility fast._\n\n... [7 more]"},
        "use_cases": [
            {"scenario": "Google Ads campaign launch", "example": "Need 10 headline variants to fill RSAs; this prompt generates them in 30 seconds."},
            {"scenario": "Cold email subject-line A/B", "example": "Same offer, 5 cold-email cohorts × 2 subject styles each."},
            {"scenario": "Landing page hero testing", "example": "Quarterly hero-headline refresh; pick the top 3 from this prompt's output to A/B test."},
            {"scenario": "Sales-page split test", "example": "Long-form sales page; test the top 3 from this output as the primary hook above the fold."},
        ],
        "when_not_to_use": "Don't use for regulated industries (pharma, finance) where every claim needs legal review. Also skip when the offer is wrong — no headline saves a bad offer.",
        "few_shot_examples": [
            {
                "input": "offer: 'Self-hosted analytics that respects user privacy'. target_audience: 'Privacy-conscious SaaS founders'. unique_angle: 'No cookies, GDPR-by-default, runs on your infra'. character_limit: 70.",
                "output": "1. **Curiosity:** \"What if your analytics didn't need a cookie banner?\" — Hooks the GDPR pain point.\n2. **Urgency:** \"The cookie consent law tightens in Q3. Self-host before then.\" — Real regulatory deadline.\n3. **Social proof:** \"Self-hosted by 2,400 SaaS founders. Zero cookies, full GDPR.\"\n4. **Contrarian:** \"Stop renting analytics from companies that resell your data.\"\n5. **Question:** \"Tired of explaining your GDPR posture to enterprise prospects?\"\n6. **Benefit-first:** \"Drop your cookie banner. Keep your analytics. Self-hosted.\"\n7. **Metaphor:** \"Privacy isn't a feature. It's the foundation. Self-host your analytics.\"\n8. **Specificity:** \"60-second install. Zero cookies. 73% lower bounce on EU traffic.\"\n9. **Negative:** \"No cookies. No data resale. No more privacy-policy rewrites.\"\n10. **Insider:** \"You know your competitor's analytics provider reads your traffic too, right?\"",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at headline-style variety without repetition."},
            {"model": "gpt-5", "compatibility": "excellent", "notes": "Strong at specificity + contrarian styles."},
            {"model": "claude-haiku-4-5", "compatibility": "good", "notes": "Cheap for bulk generation."},
            {"model": "llama-3.3-70b", "compatibility": "good", "notes": "Workable; expect to manually punch up 1-2."},
        ],
        "variations": [
            {"label": "Style-multiplier", "description": "Generate 3 variants per style (30 total).", "prompt_snippet": "Per style, generate 3 distinct headlines instead of 1. Use case: deep A/B testing."},
            {"label": "Twitter-thread starter", "description": "Each headline is the opening line of a thread.", "prompt_snippet": "Each headline must work as Tweet 1 of a thread — implies a thread continuation."},
            {"label": "Email-subject mode", "description": "Subject lines, not display ads.", "prompt_snippet": "Optimize for inbox: under 40 chars, lowercase preferred, no caps-lock URGENCY."},
        ],
        "failure_modes": [
            {"symptom": "All headlines sound similar despite different style labels", "fix": "Each style has a distinct hook mechanism; reject duplicates by structure"},
            {"symptom": "Vague benefits ('Get more done')", "fix": "Specificity rule — every headline must reference offer-specific detail"},
            {"symptom": "Fake urgency ('Limited time!') when there's none", "fix": "Urgency must be real (regulatory date, real cohort cap, sunset feature)"},
            {"symptom": "Over character limit", "fix": "Strict count — if over, regenerate that one style"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "gpt-5", "claude-haiku-4-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["brainstorm-divergent", "pricing-page-rewriter"],
        "related_tool_slugs": ["googleads", "linkedinads", "metaads"],
        "related_glossary_slugs": ["ad-copy", "ab-testing", "headline-formulas"],
        "faq": [
            {"question": "Which style usually wins?", "answer": "Depends on funnel stage. Cold: curiosity / contrarian. Warm: social proof / specificity. Hot: benefit-first / urgency (if real)."},
            {"question": "Should I run all 10 in production?", "answer": "No — pick top 3 (your gut + the most-different from each other). Test those head-to-head."},
            {"question": "Can it write LinkedIn ads?", "answer": "Yes; pass character_limit: 150 and target_audience reflecting LinkedIn's pro context."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Ad Headline Variations Prompt — 10 Styles, A/B-Ready",
        "meta_description": "Generate 10 ad headlines for the same offer in 10 distinct styles (curiosity, urgency, contrarian, social proof). A/B-ready, no fake urgency.",
    },

    {
        "slug": "brainstorm-divergent",
        "title": "Divergent Brainstorm (50+ ideas, no judgment)",
        "category": "creative",
        "tldr": "Generate 50+ wildly varied ideas around a seed concept — including deliberately impractical / weird ones — without filtering. For ideation phase only.",
        "tags": ["brainstorm", "ideation", "divergent-thinking"],
        "best_for_tags": ["brainstorming", "ideation", "creative-process"],
        "difficulty_tier": "beginner",
        "full_prompt": (
            "You're in pure divergent mode. NO judgment, NO filtering, NO 'this might not work' caveats. Generate quantity, variety, weirdness. The user will filter later.\n\n"
            "INPUTS:\n"
            "- seed: the topic / problem / opportunity\n"
            "- target_count: 50 default (range 20-100)\n"
            "- domain_constraints (optional): if user wants to stay within certain dimensions\n"
            "- weirdness_dial: 1-10 (1 = safe practical, 10 = absurdist; default 7)\n\n"
            "STRUCTURE — generate 5 ideas in each of 10 lenses:\n"
            "1. PRACTICAL: the obvious approach\n"
            "2. INVERT: do the opposite of the obvious\n"
            "3. ANALOGY: borrow from a different domain (biology, military, art)\n"
            "4. EXTREME: at 10x scale, 10x cheap, 10x weird\n"
            "5. CONSTRAINT: with one resource removed (no budget, no team, no time)\n"
            "6. SEGMENT: solving for one underserved subgroup\n"
            "7. COMBINE: cross with an unrelated trend / product\n"
            "8. HISTORICAL: how would [historical era] approach this?\n"
            "9. ABSURD: deliberately impractical (these often spark adjacent good ones)\n"
            "10. META: change the problem definition itself\n\n"
            "RULES:\n"
            "- Number every idea\n"
            "- 1-2 sentences each; no over-explaining\n"
            "- No idea is 'too dumb' to write — weirdness opens adjacent practical ideas\n"
            "- Don't pre-evaluate; the user will pick the 5 to develop\n\n"
            "Begin."
        ),
        "input_variables": [
            {"name": "seed", "type": "string", "description": "Topic / problem / opportunity to brainstorm", "required": True, "example": "How to increase developer engagement in our open-source community"},
            {"name": "target_count", "type": "integer", "description": "Number of ideas (default 50, range 20-100)", "required": False, "example": "50"},
            {"name": "domain_constraints", "type": "list[str]", "description": "Stay within these dimensions if specified", "required": False, "example": "['no paid acquisition', 'no new product features in scope']"},
            {"name": "weirdness_dial", "type": "integer", "description": "1-10 weirdness slider", "required": False, "example": "7"},
        ],
        "expected_output": {"format": "markdown", "sample": "## PRACTICAL (5)\n1. Weekly contributor spotlight email\n2. \"First PR\" labeled issues with hand-holding mentor\n3. Quarterly virtual hackathon\n4. ...\n\n## INVERT (5)\n6. Charge people to NOT contribute (the inverse — what would make people fight for the privilege?)\n7. Anti-onboarding: deliberately bad first-time experience to filter for grit\n...\n\n## ABSURD (5)\n46. Send every contributor a physical mood ring that changes color based on commit velocity\n47. Replace the README with a riddle\n..."},
        "use_cases": [
            {"scenario": "Strategy offsite pre-work", "example": "Run this on each big strategic question 1 week before the offsite; team votes on top 10 to develop."},
            {"scenario": "Stuck-on-a-problem unstick", "example": "Founder stuck on a churn problem; runs at weirdness 8; the 'absurd' bucket sparks one adjacent practical idea."},
            {"scenario": "Marketing campaign ideation", "example": "Quarterly marketing brainstorm; this prompt produces 50 raw ideas → team picks 3 to test."},
            {"scenario": "Product feature divergence", "example": "Before convergent prioritization, this prompt opens the space wider."},
        ],
        "when_not_to_use": "Don't use when you're in convergent mode (picking among defined options). Also skip for problems with hard regulatory constraints — divergent generates ideas you can't ship anyway.",
        "few_shot_examples": [
            {
                "input": "seed: 'reduce no-show rate for free trial signups'. weirdness: 6. target_count: 30.",
                "output": "## PRACTICAL (3)\n1. Email reminder 24h after signup if not activated\n2. Calendar invite to a 15-min onboarding call\n3. SMS reminder for users who opt in\n\n## INVERT (3)\n4. Charge $5 refundable deposit at trial signup; refund on first action\n5. Limit trial to 100/day with a waitlist (signals scarcity)\n6. Don't send any reminders — let the engaged self-select\n\n## ANALOGY (3)\n7. Gym-class model: pre-commit to a specific 30-min slot at signup\n8. Restaurant model: hold a 'reservation' for first session\n9. Yoga-studio model: package 5 sessions, lose them if unused (creates urgency)\n\n## ABSURD (3)\n10. Send a physical chocolate bar with the activation code embedded\n11. Make the trial activation require a karaoke video\n12. Hire a person to call each signup at 9pm on day 1 just to say 'we noticed you signed up' — creepy or magical?\n\n[continue through other lenses for 30 total]",
            }
        ],
        "model_compatibility": [
            {"model": "claude-sonnet-4-5", "compatibility": "excellent", "notes": "Best at hitting weirdness dial without descending into nonsense."},
            {"model": "claude-opus-4", "compatibility": "excellent", "notes": "Preferred at weirdness 8-10 where edge ideas matter."},
            {"model": "gpt-5", "compatibility": "good", "notes": "Strong at quantity; sometimes refuses absurd ideas."},
            {"model": "llama-3.3-70b", "compatibility": "fair", "notes": "Works; expect more clustering than variety."},
        ],
        "variations": [
            {"label": "Single-lens deep", "description": "One lens, 50 ideas inside it.", "prompt_snippet": "Override: instead of 10 lenses × 5 ideas, pick ONE lens (e.g., 'analogy from biology') and produce 50 ideas all within that frame."},
            {"label": "Team-brainstorm split", "description": "Split into 5 imaginary characters with different perspectives.", "prompt_snippet": "Imagine 5 advisors at the table: a contrarian, a frugal CFO, a creative director, a UX-skeptic, a 12-year-old. 10 ideas from each (50 total)."},
            {"label": "Anti-brainstorm", "description": "What would make this WORSE? Inverted creativity surfaces blind spots.", "prompt_snippet": "Generate 50 ways to make the seed problem worse. Then for each, ask: 'What's the inverse? Is anyone accidentally doing the bad thing today?'"},
        ],
        "failure_modes": [
            {"symptom": "All ideas cluster in 'practical' lens", "fix": "Force the 10-lens structure; each lens must produce 5 ideas, including absurd"},
            {"symptom": "Pre-judges ideas ('this won't scale')", "fix": "Strict no-evaluation rule; ideas only, evaluation comes in a different prompt"},
            {"symptom": "Repeats ideas across lenses", "fix": "Each idea should map to ONE lens; if it fits two, pick the more distinctive one"},
            {"symptom": "Weirdness dial ignored — everything is safe even at 8", "fix": "At weirdness ≥7, at least 5 ideas should be clearly impractical-as-stated"},
        ],
        "tested_with": {"models": ["claude-sonnet-4-5", "claude-opus-4", "gpt-5", "llama-3.3-70b"], "last_verified_date": "2026-05-14"},
        "related_prompt_slugs": ["story-with-character-arc", "ad-headline-variations", "strategic-tradeoff-analyzer"],
        "related_tool_slugs": ["miro", "figjam"],
        "related_glossary_slugs": ["divergent-thinking", "ideation", "design-thinking"],
        "faq": [
            {"question": "How do I pick the best ideas after?", "answer": "Different prompt — use the priority-matrix-eisenhower or strategic-tradeoff-analyzer. Brainstorm is opening; those two are closing."},
            {"question": "What's the right weirdness dial?", "answer": "Default 6-7 for product, 8-9 for marketing, 3-4 for compliance-bound. Higher dial = more 'why didn't we think of that' moments."},
            {"question": "Should I share the raw 50 with my team?", "answer": "Share the LENS structure with attribution to each lens. Sharing all 50 unfiltered creates noise; sharing the structure invites them to add their own."},
        ],
        "license": "CC-BY-4.0", "attribution": "OSS AI Hub", "status": "approved",
        "submitter_email": "hub@ossaihub.com", "submitter_name": "OSS AI Hub",
        "meta_title": "Divergent Brainstorm Prompt — 50+ Ideas, 10 Lenses",
        "meta_description": "Generate 50+ wildly varied ideas around a seed concept. No judgment, structured by 10 lenses. Weirdness dial 1-10.",
    },
]
