---
name: linkedin-postwriter-guideline-writer
description: Turns a person's voice profile into a long-form, agent-executable LinkedIn copywriting guideline that fuses their evidence-derived voice with universal LinkedIn writing principles, hard anti-AI-tell bans, and a built-in self-check. Use when the user wants to create a voice/style guide, a ghostwriting brief, or a copywriter guideline so an agent can write LinkedIn posts that sound exactly like them. Triggers include "write my voice guideline", "create a style guide for my posts", "build a ghostwriting brief", "make a guideline so an agent writes like me", "turn my voice profile into rules". Consumes a voice-profile.json from the linkedin-profile-tov-analyzer skill (or an equivalent analysis). If no profile exists, it points the user to run the analyzer first.
---

# LinkedIn Post-Writer Guideline Writer

Turns a voice profile into a durable, **agent-executable guideline**: the document a copywriter agent follows to write posts indistinguishable from the person's own. The edge over generic "ghostwriter" prompts: the guideline is **falsifiable**. It fuses (1) the person's evidence-derived voice, (2) universal LinkedIn writing principles, (3) a hard anti-AI-tell ban list, and (4) a self-check the drafting agent must pass.

This skill writes the guideline. A separate, optional step uses the guideline to write actual posts.

## Operating principles

1. **Voice first, rules second.** The guideline is built on the person's actual voice profile, not on generic best practice. Generic principles (hooks, length, CTA) are the supporting layer, never the substitute. If a universal principle conflicts with the person's real voice, the voice wins and you note the exception.
2. **Every voice rule traces to evidence.** Pull voice rules from the profile's quoted traits. Do not invent voice rules the profile does not support.
3. **The bans are non-negotiable and explicit.** The anti-AI-tell list (negation-reframe first) is stated loudly, with surface forms and rewrites, so an agent cannot miss it. See `references/ai-tells-banlist.md`.
4. **Make the self-check falsifiable.** Ship a checklist of pass/fail items plus the bundled `lint_post.py` scan, not vibes. The lint is an assist; human judgment overrides it.
5. **Density, not blanket, on the em-dash.** Ban the em-dash character in output, but frame other "tells" as density/context checks so the guideline does not flatten genuine voice.
6. **No em-dash characters in any output** this skill produces. Use commas, colons, parentheses, or a spaced hyphen.
7. **Generic and shareable.** Produce a guideline for whoever's profile is supplied. Nothing in the skill is specific to one person.

## Pre-conditions

Confirm before starting:

- A voice profile exists. Ideally a `voice-profile.json` from `linkedin-profile-tov-analyzer`. If the user has only a written analysis, that is acceptable input. If neither exists, **stop and recommend running `linkedin-profile-tov-analyzer` first** (the guideline is only as good as the profile under it).

## Phase 1: Load the voice profile

**Steps:**

1. Read the supplied `voice-profile.json` (or analysis). Extract: the one-line voice, the registers (and which is primary), tone position, stylometric fingerprint, lexical signature, stance and rhetoric, the hook inventory, and the anti-voice list.
2. If the profile's confidence is "low", warn that the guideline will inherit that uncertainty, and keep voice rules softer (fewer absolutes).

**Gate:** Confirm which register the guideline should primarily serve (a person may want a guideline for one register, for example their first-person story voice, not their promo voice).

## Phase 2: Map voice to guideline sections

**Steps (read `references/guideline-structure.md` for the full anatomy):**

1. **Voice in one sentence:** carry over from the profile.
2. **Core voice principles:** convert the profile's strongest stance/rhetoric traits into 5 to 7 imperative principles, each grounded in a profile quote.
3. **Post anatomy:** build the person's actual structure (from their hook inventory and rhythm), not a generic template.
4. **Hook formulas:** derive from the hook patterns the profile says they actually use, with their real examples as models.
5. **Lexicon:** use the profile's preferred words and signature phrases as the "use" list; the avoided words and anti-voice as the "ban" list.
6. **Micro-mechanics:** set punctuation, emoji, hashtag, paragraph, and number rules from the stylometric fingerprint (for example "spaced hyphen, never em-dash"; "bullets only when listing points, glyph X"; "3 hashtags").

## Phase 3: Inject the universal layers

**Steps:**

1. Add the **LinkedIn writing principles** from `references/linkedin-writing-principles.md` (hook-for-the-fold, dwell time and comments over likes, no links in the body, length band, structures, single specific CTA). Mark the algorithm stats as directional, not official.
2. Add the **anti-AI-tell ban list** from `references/ai-tells-banlist.md` as a loud, top-level section. The negation-reframe is ban number one, with enumerated surface forms and positive rewrites.
3. Reconcile conflicts: if a universal rule contradicts the person's real voice, keep the voice and note it.

## Phase 4: Prove it with samples

**Steps:**

1. Write 2 to 3 sample posts in the person's voice, on topics they actually write about, applying the full guideline.
2. These samples are the proof the guideline works. If you cannot write a convincing sample, the guideline has a gap, fix it.

## Phase 5: Build the self-check

**Steps (see `references/self-check-protocol.md`):**

1. Add the "Is this them?" checklist (pass/fail items: hook is a felt outcome, numbers carry claims, no em-dash, no negation-reframe, bullets conditional, 3 hashtags, single CTA, paragraphs under 3 sentences, reads peer-to-peer).
2. Document the lint: `python scripts/lint_post.py <draft.txt>` (use `python3` if needed), and state clearly it is advisory, not a gate.
3. Run the lint on your own Phase 4 samples and confirm they pass (or fix them). This is the skill eating its own dog food.

## Phase 6: Self-review and assemble

**Steps:**

1. Read the full guideline as the person: would they believe an agent following this wrote their posts? Fix anything off.
2. If the user has a recipient-POV review skill (for example cold-eye-review), offer to run the samples through it. This is optional, not required: the self-check in Phase 5 is native and sufficient.
3. Assemble the final `guideline.md` using `templates/guideline-template.md`.

**Gate:** Show the user the guideline and the samples. They confirm it sounds like them before it is treated as final.

## What this skill does NOT do

- **Does not analyze the voice.** It consumes a profile from `linkedin-profile-tov-analyzer`. Garbage profile in, garbage guideline out.
- **Does not auto-reject posts.** The lint is advisory; the human or drafting agent decides.
- **Does not publish or post anything.** It produces a guideline (and sample posts), nothing more.
- **Does not invent voice traits** the profile does not support.
- **Does not depend on any private skill.** The self-check is native; cold-eye-review is an optional enhancement if present.
