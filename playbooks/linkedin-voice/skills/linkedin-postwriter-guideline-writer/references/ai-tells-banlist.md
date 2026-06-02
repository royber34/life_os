# Anti-AI-tell ban list

These patterns make text read as machine-written. The guideline must state them loudly. Reference catalogue: Wikipedia "Signs of AI writing".

## BAN 1 (top priority): the negation-reframe

The single most recognizable AI tell. Banned shape: negate one thing, then assert another in its place, in one sentence or across two.

Surface forms (the shape is banned, not just these strings):
- "It's not X, it's Y."
- "It wasn't X. It was Y."
- "This isn't X. It's Y." (for example "This isn't gospel. It's what's worked for me.")
- "Not just X, but Y."
- "This isn't about X, it's about Y."
- "The point isn't X. It's Y."
- "X? No. Y."
- "Less X, more Y" (as a reframe).

Detection: scan every sentence AND every adjacent sentence pair for a negated claim followed by an asserted alternative.
Fix: make the positive claim directly. If a caveat is needed, state it plainly and let it stand alone.
- Bad: "This isn't gospel. It's what's worked for me."
- Good: "This is just what's worked for me so far. Your setup is different."

## BAN 2: em-dash characters

LLMs deploy em-dashes far more, and more formulaically, than typical human prose. This guideline bans the em-dash character outright; use a spaced hyphen ' - '. (Note: for general editing the rule is density-based, but for this voice the character is simply out.)

## The rest (avoid)

- **Filler openers:** "In today's fast-paced world / landscape / realm / tapestry."
- **Empty meta-hedging:** "It's worth noting", "It's important to note."
- **AI vocabulary cluster:** delve, leverage, seamless, robust, elevate, enhance, crucial, pivotal, underscore, foster, showcase. One is coincidence; a cluster is a strong tell.
- **Rule-of-three padding:** reflexive triplets of adjectives or phrases used to look comprehensive.
- **Vague attribution / hedging:** "experts argue", "observers note", "some sources say."
- **Uniform listicle cadence:** every bullet a bold label plus a same-length clause.
- **Emoji-as-bullets** (rocket, check, lightbulb leading each line) used as formatting markup.
- **Tilde approximations** in prose ("~5 years", "~$10k"). Write "about" or the plain number.
- **Title-Case Headers** (capitalizing every word).
- **Procedural openers:** "Let's dive in", "Let's explore."
- **Over-summarizing closers:** "In conclusion", "In summary", "Despite its challenges."
- **Engagement bait:** "Agree?", "Thoughts?", "Comment YES if..." LinkedIn demotes detected bait.

## Caveat for the guideline author

Frame these as judgment-assisted, not absolute, except the negation-reframe, em-dash, tilde, body-link, and engagement-bait bans, which are hard. The `lint_post.py` script catches the mechanical subset; it will false-positive on the negation-reframe heuristic, so a human verifies. The goal is to remove tells without flattening the person's real voice.

Sources: Wikipedia "Signs of AI writing"; Beutler Ink "How to Spot AI Writing"; commentary on the em-dash as an AI signature (treat density, not the mark itself, as the general tell).
