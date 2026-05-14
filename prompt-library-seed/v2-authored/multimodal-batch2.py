"""Multimodal prompts — batch 2."""

RECORDS = [
    {
        "slug": "ui-component-from-screenshot",
        "title": "UI Component From Screenshot",
        "tldr": "Reads a UI screenshot and generates the HTML/CSS or React component implementing it — including responsive considerations, semantic HTML, and accessibility hooks.",
        "category": "multimodal",
        "tags": ["ui", "screenshot-to-code", "vision", "frontend"],
        "best_for_tags": ["frontend-prototyping", "design-handoff", "html-css"],
        "difficulty_tier": "advanced",
        "featured": True,
        "use_cases": [
            {"scenario": "Designer hands engineer a screenshot", "example": "Mockup PNG → React + Tailwind component starter, ready to wire up state."},
            {"scenario": "Competitive UI inspiration", "example": "Inspect a competitor's UI; generate similar React component for your design system."},
            {"scenario": "Legacy screenshot to modern stack", "example": "Old app screenshot → modern Next.js + Tailwind rebuild starter."},
            {"scenario": "Component library scaffolding", "example": "Generate all 12 components from Figma screenshots in one pass."},
        ],
        "when_not_to_use": "Skip for highly interactive components (animation, complex state) — generated code is starting point, not finished. Skip when design system constraints aren't known to AI.",
        "full_prompt": """You are a senior frontend engineer. The screenshot is a UI component. Generate the implementation.

INPUT (provided as image)
- A UI screenshot
- Design system / framework preferences: {framework_prefs}    (e.g., React+Tailwind, vanilla HTML/CSS, SwiftUI)
- Component name: {component_name}
- Notes from designer: {designer_notes}

OUTPUT

## 1. Visual breakdown
- Identified elements (title, body, button, etc.)
- Layout: stack / grid / flex
- Spacing observations (gaps, padding — coarse estimates)
- Color observations (background, accent, text)
- Typography observations (size, weight)

## 2. Semantic structure
HTML structure choice with rationale:
- Which element wraps the whole thing? (article, section, div, custom)
- What landmarks? (header, main, nav, footer)
- ARIA roles if non-trivial

## 3. The code
Full component code in {framework_prefs}. Include:
- All visible content (use placeholder data, label as placeholder)
- Tailwind / CSS classes for spacing, color, typography
- ARIA attributes for accessibility
- Mobile-responsive considerations (Tailwind sm:/md:/lg:)

## 4. Stuff to wire up
Things the screenshot shows but the code doesn't fully implement:
- Click handlers (named, but stubbed)
- State (mark with TODO and shape)
- Data sources (mark as props with type)

## 5. Accessibility audit
- Color contrast estimate (pass/uncertain/fail WCAG AA — be honest)
- Keyboard navigation considerations
- Screen reader notes

## 6. What I might have gotten wrong
3-5 specific things in the screenshot that I'm uncertain about:
- Spacing that's hard to read precisely
- Whether the icon is decorative vs functional
- Hover/focus states (not visible in static screenshot)
- Conditional content (might appear in other states)

RULES
- The screenshot is one snapshot; many UI behaviors are invisible (hover, focus, disabled). Note them.
- Use semantic HTML — don't div-everything.
- Tailwind classes match what's visible; don't add unrequested decoration.
- Honest about uncertainty — code is starter, not final.

Now generate.""",
        "input_variables": [
            {"name": "framework_prefs", "type": "string", "description": "Framework + design system", "required": True, "example": "React + TypeScript + Tailwind CSS"},
            {"name": "component_name", "type": "string", "description": "Component name", "required": True, "example": "UserProfileCard"},
            {"name": "designer_notes", "type": "string", "description": "Any context from designer", "required": False, "example": "Hover state shows edit button. Mobile: stack vertically."},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Six sections: visual breakdown, semantic structure, the code, what-to-wire-up TODOs, accessibility audit, uncertainty notes.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Strong on semantic HTML and honest uncertainty notes."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good code generation; can be over-confident on pixel-perfect spacing."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Solid; accessibility section sometimes thin."},
            {"model": "llama-3.2-vision", "compatibility": "fair", "notes": "Coarser code generation; useful for layout sketch only."},
        ],
        "variations": [
            {"label": "shadcn/ui components", "description": "Use shadcn primitives.", "prompt_snippet": "Add: ‘build using shadcn/ui primitives — Button, Card, Avatar, etc. — not raw HTML.’"},
            {"label": "Vue 3 / SwiftUI / Jetpack Compose", "description": "Different framework.", "prompt_snippet": "Set framework_prefs accordingly. Adjust ARIA → platform a11y conventions (SwiftUI: accessibilityLabel etc.)"},
            {"label": "Storybook + component", "description": "Also generate a Storybook story.", "prompt_snippet": "Add Section 7: ‘Storybook story file with 2-3 variants of the component.’"},
        ],
        "failure_modes": [
            {"symptom": "Spacing values fabricated as precise (e.g., padding: 17px).", "fix": "Re-pin: ‘use Tailwind scale (p-2, p-3, p-4) or round to nearest 4px; don't claim pixel-perfect.’"},
            {"symptom": "All elements div-soup.", "fix": "Force semantic: ‘use article / section / header / nav appropriately; explain choice in section 2.’"},
            {"symptom": "Missing accessibility considerations.", "fix": "Force section 5 to be non-empty with specific contrast/keyboard notes."},
            {"symptom": "Uncertainty section empty.", "fix": "Add: ‘every screenshot has hidden behaviors. List at minimum 3.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3.2-vision"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["screenshot-bug-report-builder", "code-snippet-with-tests-tdd"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["multimodal", "frontend-codegen"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Will it match my design system?", "answer": "Generic Tailwind/React, yes. Custom design system, no — pass your conventions in framework_prefs (‘use our Button component from @ourorg/ui’)."},
            {"question": "Pixel-perfect output?", "answer": "Don't expect it. Vision LLMs estimate spacing/color coarsely. Use generated code as scaffolding; designer + developer refine."},
            {"question": "Multiple states (hover, error, etc.)?", "answer": "Run multiple screenshots through the prompt; manually merge into a stateful component. Or provide all-states screenshot if your design tool supports it."},
        ],
        "meta_title": "UI Component From Screenshot — Prompt",
        "meta_description": "Generate React/HTML components from UI screenshots: semantic structure, Tailwind classes, ARIA, responsive considerations, uncertainty notes.",
    },
    {
        "slug": "video-frame-narrative",
        "title": "Video Frame Narrative",
        "tldr": "From 5-15 extracted video frames, produce a narrative description of what's happening: scene transitions, actions, key moments. Useful for video summarization and accessibility.",
        "category": "multimodal",
        "tags": ["video", "vision", "narrative", "accessibility"],
        "best_for_tags": ["video-summarization", "video-accessibility", "content-moderation"],
        "difficulty_tier": "advanced",
        "featured": False,
        "use_cases": [
            {"scenario": "Tutorial video summarization", "example": "10 frames → narrative: ‘instructor introduces the topic, demonstrates setup, runs the example, shows results.’"},
            {"scenario": "Long-form video → highlights", "example": "Sample frames every 30s → narrative; pick key moments for clip extraction."},
            {"scenario": "Accessibility audio description", "example": "Generate text description for screen reader / visually impaired user."},
            {"scenario": "Content moderation for video", "example": "Spot-check frames; flag concerning patterns; route for human review."},
        ],
        "when_not_to_use": "Skip when audio is available (transcribe audio for richer info). Skip for very fast-changing video (frame sampling misses critical moments).",
        "full_prompt": """You are describing a video from sampled frames.

INPUT (frames provided as images, in time order)
- Number of frames: {n_frames}
- Time interval between frames: {interval_seconds}
- Optional caption / audio transcript: {audio_or_caption}

OUTPUT

## 1. Per-frame observations
For each frame:
- Frame N (~time T):
  - Setting / location
  - Visible actors (1-3 sentences)
  - Action in progress (verb-driven, what's HAPPENING)
  - Notable on-screen text (verbatim)

Keep each frame's description tight (3-5 sentences max).

## 2. Scene transitions
Where do scenes change? Identify transition points and what changed (location, actor, time-of-day, mood).

## 3. Narrative summary
2-4 paragraphs describing what's happening as a story. Include:
- Setup (what we start with)
- Development (what changes / progresses)
- Resolution (where it ends)

## 4. Notable moments
3-5 frames worth highlighting:
- Frame N: what makes it notable
- For each, a 1-line accessibility description suitable for audio narration

## 5. What I don't see
Things this analysis CAN'T determine from frames alone:
- Audio content (unless caption provided)
- Inter-frame motion (only sampled positions, not trajectories)
- Content between sampled frames
- Subtle expressions or details not visible at this resolution

RULES
- Describe what's THERE, not what you imagine. ‘A person is holding a clipboard’ — observed. ‘They look frustrated’ — inferred, mark as inferred.
- Don't identify specific named individuals.
- Use time references (~3s, ~17s) so readers can find moments in the source video.
- Verb-driven: ‘a hand reaches for the keyboard’ beats ‘there is a hand near a keyboard.’

Now describe.""",
        "input_variables": [
            {"name": "n_frames", "type": "integer", "description": "Number of frames", "required": True, "example": "8"},
            {"name": "interval_seconds", "type": "number", "description": "Seconds between frames", "required": True, "example": "5"},
            {"name": "audio_or_caption", "type": "string", "description": "Optional audio transcript / caption", "required": False, "example": "Instructor explaining how to set up the database"},
        ],
        "expected_output": {
            "format": "markdown",
            "sample": "Five sections: per-frame observations, scene transitions, narrative summary, notable moments, what's-not-seen list.",
        },
        "few_shot_examples": [],
        "model_compatibility": [
            {"model": "claude-3-7-sonnet", "compatibility": "excellent", "notes": "Honest about inference vs observation."},
            {"model": "gpt-4o", "compatibility": "excellent", "notes": "Very good; occasionally over-narrative."},
            {"model": "gemini-1.5-pro", "compatibility": "good", "notes": "Handles longer frame sequences well."},
            {"model": "llama-3.2-vision", "compatibility": "fair", "notes": "Coarser scene understanding."},
        ],
        "variations": [
            {"label": "Audio-fusion", "description": "Combine with audio transcript.", "prompt_snippet": "Add: ‘interleave frame observations with audio timeline; show alignment between visual and spoken content.’"},
            {"label": "Chapter markers", "description": "Suggest chapter cut points.", "prompt_snippet": "Add: ‘suggest 3-7 chapter markers with timestamps + titles based on scene transitions.’"},
            {"label": "Moderation-only", "description": "Flag concerning content quickly.", "prompt_snippet": "Replace narrative with: ‘per-frame: any safety concerns (violence, sexual content, minors in sensitive context); rate concern level per frame.’"},
        ],
        "failure_modes": [
            {"symptom": "Frames described in isolation; no narrative.", "fix": "Re-pin Section 3 mandatory; refer to specific frames in the narrative."},
            {"symptom": "Identifies specific named people.", "fix": "Re-pin: ‘never identify named individuals; describe by role/appearance.’"},
            {"symptom": "Over-imaginative inference.", "fix": "Add: ‘mark every inference clearly; rule of thumb — if I removed the frame, would my claim still seem true? If yes, it's inference, not observation.’"},
            {"symptom": "Notable-moments section misses obvious ones.", "fix": "Add: ‘the most notable moments are usually scene transitions, peak emotional moments, or new on-screen text appearances.’"},
        ],
        "tested_with": {"models": ["claude-3-7-sonnet", "gpt-4o", "gemini-1.5-pro", "llama-3.2-vision"], "last_verified_date": "2026-05-13"},
        "related_prompt_slugs": ["image-description-alt-text", "subtitle-translator-with-timing"],
        "related_tool_slugs": [],
        "related_glossary_slugs": ["video-understanding", "frame-sampling"],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "How many frames is right?", "answer": "5-15. Fewer misses transitions; more dilutes narrative. For 5-min video: 8-12 frames at ~30s intervals. For 30-min: extract scene-change frames specifically."},
            {"question": "Why not just process the whole video?", "answer": "Video models exist (Gemini, GPT-4o with video) but costlier. Frame sampling is a good cost-quality balance for many tasks."},
            {"question": "Will it work for slow video (lectures, talks)?", "answer": "Yes — frames at 30-60s intervals suffice. For fast video (sports, action), need much denser sampling or a true video model."},
        ],
        "meta_title": "Video Frame Narrative — Prompt",
        "meta_description": "Turn sampled video frames into narrative: per-frame observations, scene transitions, story summary, notable moments, honesty about gaps.",
    },
]
