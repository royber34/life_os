---
name: linkedin-profile-tov-analyzer
description: Analyzes a person's LinkedIn posts and produces an evidence-cited tone-of-voice profile where every trait is backed by a verbatim quote and a frequency count. Use when the user wants to analyze their LinkedIn voice, audit their writing style, extract their tone of voice, figure out how they write, or build a reusable voice profile to feed a ghostwriting or post-writing workflow. Triggers include "analyze my LinkedIn voice", "what is my writing style", "audit my tone of voice", "extract my voice", "build a voice profile", "analyze these posts", or handing over a LinkedIn data export. Works from a LinkedIn data export or pasted posts. Never scrapes.
---

# LinkedIn Profile Tone-of-Voice Analyzer

Turns a person's own LinkedIn posts into an **evidence-cited voice profile**: a structured analysis where every claimed trait is tied to a verbatim quote and how often it occurs, plus a machine-readable `voice-profile.json` that the `linkedin-postwriter-guideline-writer` skill (or any downstream writer) can consume.

This skill produces analysis. It does not write posts and does not scrape LinkedIn.

## Operating principles

1. **Evidence over assertion.** Every trait you report must cite at least one verbatim quote from the corpus and state how often the pattern occurs (for example "opens with a one-line result in 7 of 12 posts"). No claim without a quote. This is the bar that separates this skill from generic "mimic my tone" tools.
2. **Frequency-gated.** Better no rule than a rule built on a single occurrence. Only promote a pattern to a "trait" if it appears in roughly a third of posts or at least 3 times. One-offs go in an "observed once" note, never as a rule.
3. **Surface uncertainty, never fake confidence.** Set a confidence tier from corpus size (the stylometry script computes it). If the corpus is thin, say so plainly and offer to gather more before asserting firm rules. No silent failures.
4. **Separate voice from tone, and name distinct registers.** Voice is the stable personality; tone shifts by context. Many writers have 2+ registers (for example a first-person story register and a promo/announcement register). Identify them separately; do not average them into mush.
5. **Own data, own session.** Collect from the user's own logged-in LinkedIn session (Claude-driven browser, the default), their export, or pasted posts. Never use third-party scrapers or unauthenticated crawling. See `references/ingestion.md`.
6. **No em-dash characters in any output** this skill produces. Use commas, colons, parentheses, or a spaced hyphen. Hyphens and en-dashes in number ranges are fine.
7. **Privacy.** The posts are the user's data. Analyze locally; do not send the corpus anywhere.

## Pre-conditions

Confirm before starting:

- The user wants to analyze a profile they own (or have explicit rights to). State this is for their own data.
- The user can provide posts via one of the ingestion paths in `references/ingestion.md`.

If neither is true, stop and explain the ingestion options.

## Phase 1: Gather the corpus

**Goal:** Collect as many of the user's posts as possible into one file the script can read, and report the real counts.

**Target corpus size:** Aim for at least the **12 most recent posts** for enough variation. More is better (8 is the floor for "moderate" confidence, 20+ reaches "strong", under 8 stays "low"). LinkedIn's feed is virtualized and its export is rate-limited, so you will often capture fewer than 12. That is acceptable: take what renders, and **report the real counts** (step 4). Never silently imply the corpus is bigger than it is.

**Steps:**

1. Ask one scoping question: does the user care which posts performed well (engagement-weighting)? If yes, note that neither browser capture nor the export carries reaction/comment counts, so they may want to point out their best posts.

2. **Primary method: Claude collects from the user's own logged-in browser session** (full detail in `references/ingestion.md`). Using a connected browser tool on the user's authenticated session:
   - Navigate to `https://www.linkedin.com/in/<handle>/recent-activity/all/`.
   - Read rendered posts with the page-text tool; scroll incrementally and click "Show more results" to load more (the feed is virtualized: only a few render at a time).
   - For a repost, capture only the user's own commentary, not the reposted body.
   - Skip "Boost"-only stubs that do not hydrate and any deleted posts. Capture every post that renders as real text.

3. **Optional reliability upgrade (recommend if capture is thin or the user wants the fullest read):** the LinkedIn data export. Settings -> Data privacy -> Download my data -> **Request new archive** -> tick the **Posts/Shares** file (emailed in minutes; LinkedIn rate-limits requests to about one per 2 hours). Returns the full history as `Shares.csv`. Optional, not required.

4. Normalize the corpus into one input file (`Shares.csv`, a `.jsonl` with `text` fields, or a `.txt` with posts separated by a line of `---`), and record three counts: **attempted** (entries found), **captured** (rendered as usable text), **used** (after dropping repost bodies, stubs, duplicates).

**Gate:** Report to the user: posts attempted, captured, used, and the confidence tier that the "used" count implies. Confirm before measuring.

## Phase 2: Measure the objective layer

**Goal:** Compute the reproducible, countable metrics so the analysis is grounded, not impressionistic.

**Steps:**

1. Run the bundled script from this skill's directory:
   `python scripts/stylometry.py <corpus-file> --out voice-metrics.json`
   (use `python3` if `python` is not on PATH).
2. Read the resulting metrics: sentence length mean and burstiness (stdev), point-of-view ratios, punctuation density (note the em-dash and exclamation rates), emoji and hashtag usage, contraction rate, lexical richness, and the list of first lines (hooks).
3. Read the `confidence` tier the script reports. If it is "low" (under 8 posts), tell the user the analysis will be provisional and ask whether to proceed or gather more posts.

**Gate:** Metrics produced and confidence tier surfaced to the user. If confidence is low, get explicit go-ahead to continue.

## Phase 3: Extract the four voice layers

**Goal:** Read the posts and build the interpretive profile, every trait quote-backed and frequency-gated.

**Steps:**

1. Read `references/voice-taxonomy.md` for the four layers and exactly what to extract in each:
   - **Layer 1: Tone position** (the four NN/G spectra, plus whether tone shifts by context).
   - **Layer 2: Stylometric fingerprint** (from the script metrics, interpreted).
   - **Layer 3: Lexical signature** (signature phrases, preferred and avoided words, contractions, hedging vs assertion).
   - **Layer 4: Stance and rhetoric** (humour type, warmth vs authority, storyteller vs explainer, and an explicit anti-voice list).
2. Read the actual posts (not just the metrics). For every trait, pull a verbatim quote and count how many posts show it. Apply the frequency gate.
3. Identify the distinct registers and which is the person's strongest / most authentic.
4. Build the hook inventory: list the real opening lines and classify the patterns the writer actually uses.

**Gate:** None internal; proceed to assemble once every intended trait has a quote and a frequency.

## Phase 4: Assemble the outputs

**Goal:** Produce both a human report and a machine profile.

**Steps:**

1. Write `analysis.md` using `templates/analysis-template.md`. Fill every section; where evidence is thin, say so rather than padding.
2. Write `voice-profile.json` conforming to `templates/voice-profile.schema.json`. This is the hand-off artifact for the guideline-writer skill.
3. Keep the script's `voice-metrics.json` alongside both as the raw evidence.

**Gate:** Show the user `analysis.md`. They confirm it sounds like them before the profile is treated as final.

## Phase 5: Self-verify

Before declaring done, check:

- Does every asserted trait have at least one verbatim quote and a frequency? Remove or downgrade any that do not.
- Are the corpus counts reported (attempted, captured, used), and the confidence tier stated and honored (no firm rules on a thin corpus)?
- Are distinct registers separated rather than averaged?
- Is there an explicit anti-voice ("this is NOT how they sound") section?
- Zero em-dash characters in the output?

Report what you could and could not establish. If the corpus was too small for a given layer, say so.

## What this skill does NOT do

- **Does not scrape LinkedIn** or use third-party scrapers. Own data via export or paste only.
- **Does not write posts.** That is the `linkedin-postwriter-guideline-writer` skill (which consumes this skill's `voice-profile.json`).
- **Does not judge engagement or quality** unless the user supplies performance data; by default it analyzes voice, not what "won".
- **Does not invent traits.** If the corpus does not show a pattern, it does not go in the profile.
- **Does not run on a schedule.** Invoke it when you want a fresh voice read (for example after a deliberate style shift).
