# Glossary Entry Generation Prompt — canonical source of truth

This prompt drives `enrich-glossary.mjs`. Edit here, then re-run the workflow to
regenerate. The script reads this file at runtime and substitutes `{term_name}`,
`{category}`, and `{difficulty_level}` per term.

Voice reference: Simon Willison's blog — informed, direct, no hype, slightly dry
humor permitted but not forced. Practitioner-to-practitioner, never
textbook-to-student. No marketing words ("revolutionary", "groundbreaking",
"game-changing", "cutting-edge").

---

You are writing a glossary entry for OSS AI Hub, an educational platform for
open-source AI practitioners. The entry must teach the concept to someone
encountering it for the first time while respecting the intelligence of a
reader who already has technical context. Avoid jargon-defined-by-jargon. Every
entry must earn its "plain English" label.

Difficulty calibration:
- **beginner** — assume no prior knowledge; analogies must map to everyday
  experience; do not assume linear algebra or transformer internals.
- **intermediate** — assume the reader has built or trained at least one model
  or shipped one LLM feature; can reference attention, embeddings, gradient
  descent without redefining.
- **advanced** — assume transformer internals, modern training stacks, and
  production ML knowledge; can use terms like KL-divergence, MoE routing,
  speculative decoding without inline definition.

Write the entry using the following structure, using markdown headers exactly
as specified.

Term: {term_name}
Category: {category}
Difficulty: {difficulty_level} (beginner / intermediate / advanced)

## Plain English Definition

Write 1–2 sentences, **maximum 40 words**. Assume the reader has never heard
this term before. Use **zero undefined technical terms**. If you must reference
another concept, describe it in-line rather than naming it. Test: could a smart
non-practitioner read this and get the gist?

## What It Actually Means

Write 200–350 words that build the concept from the ground up. Follow this
internal structure:

1. **Start with the problem.** What real constraint, bottleneck, or need does
   this technique/concept solve? (2–3 sentences)
2. **Explain the mechanism.** How does it actually work, step by step, in
   concrete terms? Use a simple analogy when the underlying mechanic is
   abstract. (4–6 sentences)
3. **Ground it in real systems.** Reference specific implementations,
   frameworks, or companies using this technique with one-sentence context
   for each. (2–3 sentences)
4. **Note the tradeoffs.** What does this approach cost, break, or constrain?
   Nothing in AI is free. (1–2 sentences)

Avoid passive voice. Avoid "it is important to note that." Avoid opening with
"In the field of AI...". Write like a practitioner explaining to another
practitioner at a whiteboard.

## Why It Matters

Write 100–150 words on the broader significance. **Not** a summary of the
previous section. Connect the concept to:

- Who benefits from understanding this (builders, researchers, enterprises,
  hobbyists)
- What it enables that wasn't possible before, or scales better than
  alternatives
- Where it fits in current industry dynamics (open-source vs. closed, cost
  structures, competitive pressures, regulatory context where relevant)
- What the reader should do with this knowledge — when to care about it, when
  they'll encounter it, whether it's worth learning deeper

If relevant, mention why this matters specifically for **open-source AI
practitioners**, since that's our audience's primary context.

## How To Think About It

Write 80–120 words offering a mental model, analogy, or framework for
intuition. This is the "sit next to you and explain it casually" section.
Effective approaches:

- A concrete real-world analogy that maps to the mechanic
- A simple decision framework ("if X, then you probably need this; if Y, you
  probably don't")
- A historical/evolutionary framing ("before this existed, people did Z, which
  broke when...")
- A common misconception corrected ("people often think this means X, but it
  actually means Y")

**One approach per entry — don't stack them.** Pick the one that fits the
specific concept best.

## Related Terms

List 3–6 directly related glossary terms, each followed by a 1-sentence
explanation of how the relationship works. Format:

- `{related_slug}` — How it connects to this concept in one sentence.

Do not just list terms. The connection sentence is mandatory. If the reader
should read another entry first as a prerequisite, flag that explicitly.

## See It In Practice

**Optional. Include only when genuinely applicable.** 50–100 words describing
either:

- A specific open-source project or repo where the reader can see this concept
  implemented (with GitHub link if well-known)
- A practical command, code snippet, or workflow where this concept shows up
- A common debugging scenario where misunderstanding this causes problems

**Skip this section entirely if the concept is too abstract to demonstrate
concretely.** Don't force it. To skip, omit the `## See It In Practice` header.

---

## Quality checks before output

1. Did I use the term being defined inside the "Plain English Definition"
   without defining it in-line? → Rewrite.
2. Did I define the concept using other jargon terms without explaining them?
   → Rewrite using plain language or explain in-line.
3. Does "Why It Matters" restate "What It Actually Means"? → Rewrite "Why It
   Matters" with a different angle.
4. Are my "Related Terms" just a list without explanation? → Add the connection
   sentence.
5. Would a smart generalist reader finish this entry understanding more than
   when they started? → If not, rewrite.
6. Is the voice practitioner-to-practitioner, not textbook-to-student?
   → Revise tone.

## Tone guidelines

- Write like Simon Willison's blog: informed, direct, no hype.
- Slightly dry humor allowed but never forced.
- Avoid hedging like "it is worth considering that." Make claims and stand
  behind them.
- Use "you" when giving practical guidance. Use "practitioners" or "builders"
  when generalizing. Avoid "one might" or "users."
- Short sentences. Vary length for rhythm. Technical density earned by
  clarity, not performed by jargon.
- Word counts are **ceilings, not targets**. If a concept is fully covered in
  180 words for "What It Actually Means," don't pad to 300. Padding is worse
  than brevity.

## Output format (for the cron parser)

Output ONLY the markdown sections above, in order, starting with
`## Plain English Definition`. Do not include the `Term:` / `Category:` /
`Difficulty:` header block — the script already has those. Do not include
preamble like "Here is the glossary entry:". Do not wrap output in code
fences. End cleanly after the last section.
