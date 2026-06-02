# The four-layer voice taxonomy

Extract these four layers. Layers 1, 3, and 4 are interpretive: every trait must carry a verbatim quote and a frequency. Layer 2 is computed by `scripts/stylometry.py`; your job is to interpret it.

Frequency gate for every interpretive trait: it appears in roughly a third of posts, or at least 3 times. One-offs go in an "observed once" note, not as a rule.

## Layer 1: Tone position (the stable spectra)

Place the writer on each of the four Nielsen Norman Group tone dimensions, as a 1 to 5 point, with a quote that shows it:

- Formal (1) to Casual (5)
- Serious (1) to Funny (5)
- Respectful (1) to Irreverent (5)
- Matter-of-fact (1) to Enthusiastic (5)

Then note: does tone stay flat across posts, or shift by content type (for example warmer in personal stories, drier in analysis)? Name the shift if there is one.

## Layer 2: Stylometric fingerprint (computed, then interpreted)

From `voice-metrics.json`, interpret and report:

- **Sentence length and burstiness.** Mean words per sentence, and the stdev. High stdev means the writer mixes long and short for rhythm; low stdev means uniform cadence. Burstiness is itself an anti-AI signal.
- **Point of view.** The I / we / you / they ratios. Is this an "I" storyteller, a "we" company voice, or a "you"-directed teacher?
- **Punctuation habits.** Em-dash, exclamation, ellipsis, comma, colon density per 1000 words. Flag signature habits (for example heavy colon use to pivot setup to payoff).
- **Lexical richness.** Type-token ratio and hapax rate: plain and repetitive, or wide-ranging vocabulary.
- **Emoji and hashtags.** Count, which emoji recur, how many hashtags and which.
- **Contraction rate.** A casual/formal signal.

## Layer 3: Lexical signature (the recognizable surface)

- **Signature phrases and verbal tics:** exact recurring phrases, with frequency.
- **Preferred words and avoided words:** what they reach for; what they conspicuously never use.
- **Hedging vs assertion:** "I think / maybe / probably" vs "is / always / never". Quote both if both appear.
- **Contractions, slang, jargon level, profanity tolerance.**
- **Number habits:** do they quantify with specific figures, multiples, percentages?
- **Formatting idiosyncrasies:** emoji bullets, line-break rhythm, one-line paragraphs.

## Layer 4: Stance and rhetoric (the personality)

- **Humour type:** dry/wry vs broad, or none. Quote it.
- **Warmth vs authority; opinion-forward vs neutral; storyteller vs explainer.**
- **Signature rhetorical moves:** before/after contrast, aphoristic punch lines, admitting what failed, a question close. Quote each.
- **Hook inventory:** list the real first lines from `hooks_first_lines` and classify the patterns the writer actually uses (result-first, provocative consequence, stat-led, contrarian, story-open).
- **Anti-voice (required):** an explicit "this is NOT how they sound" list. Name the registers, tones, and constructions that would read as an impostor.

## Registers

Most writers have more than one register. Identify each (for example "first-person operator story" vs "newsletter/promo"), describe how they differ, and say which is the strongest and most authentic. Do not average them into one bland profile.
