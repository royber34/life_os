# Self-check protocol

The guideline must ship with a self-check so the drafting agent can verify its own output. Two layers: a human-judgment checklist, and a mechanical lint. The lint assists; it never decides.

## Layer 1: the "Is this them?" checklist

Embed this in every guideline. A draft passes only if all are true:

- [ ] Hook (line 1) is a felt outcome the reader cares about, not an insider metric.
- [ ] Concrete numbers carry the claims where numbers exist.
- [ ] One honest caveat / admitted limitation is present (if the person's voice includes that move).
- [ ] Zero em-dash characters; zero "~" approximations; zero "not X, it's Y" reframes (scan sentence pairs).
- [ ] Bullets only if there are genuine points to list, with the person's bullet glyph.
- [ ] At most 3 hashtags, in the person's style; no invented trendy tags.
- [ ] No URL in the body (link in first comment, or comment-to-send CTA).
- [ ] One CTA, specific, no engagement bait.
- [ ] No paragraph longer than 2 sentences.
- [ ] Reads peer-to-peer in the person's register, not generic or guru.
- [ ] Matches the person's anti-voice list (none of the banned constructions present).

## Layer 2: the mechanical lint

Run the bundled script on any draft:

`python scripts/lint_post.py <draft.txt>`  (use `python3` if `python` is not on PATH)
`python scripts/lint_post.py <draft.txt> --json`  for structured output.

It flags: em-dash characters, "~" approximations, candidate negation-reframes, body URLs, more than 3 hashtags, exclamation marks, paragraphs over 2 sentences, and AI-tell buzzwords.

Severity: "blocker" (em-dash, tilde, negation-reframe candidate, body link) vs "flag" (hashtags, exclamation, paragraph length, buzzword).

Important: the negation-reframe and em-dash checks WILL false-positive. The lint is an assist. A human or the drafting agent makes the final call and may override any finding with reason. Nothing auto-rejects.

## Layer 3 (optional): recipient-POV review

If the user has a recipient-POV review skill (for example cold-eye-review), the sample posts can be run through it for a "would the person believe they wrote this" pass. This is an enhancement, not a requirement. The guideline's own checklist plus the lint are sufficient on their own.
