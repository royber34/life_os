---
name: lp-b2b-review
description: Reviews a B2B sales landing page the way a buyer arriving cold from a link sees it, using a panel of fresh simulated visitors who know nothing about the seller (first-time visitors like the ideal customer, a skeptic burnt by the alternative, the people a link gets forwarded to when a company buys), plus a claims-and-legal read and a designer pass. Scores a short rubric with a quote per line, writes a fix list that respects the seller's own decisions, says when to stop iterating, and judges the page against its goal. Quick mode tests draft text before design; full mode reviews a built page or a live URL; ab mode compares two versions blind. Use whenever the user asks to review, rate, test, red-team or sanity-check a landing page, sales page, offer page or waitlist page, asks whether a cold lead would get it, whether it is ready to go live, or which version is better.
---

# lp-b2b-review

Judge a sales page the way the person it is for will meet it: a stranger who got a link, opens it on a phone, has never heard of the seller, and decides in seconds whether to keep reading.

This skill exists because the usual review setups miss exactly that. In one real build, four review rounds with ten personas who had all been briefed on the seller and the offer missed that the page asked visitors to choose an option before it said what the product was. The seller saw it in one look when opening the live page as a stranger would. Reviewers also kept reopening decisions the seller had already made, a designer removed the before-and-after the seller had approved, and the team chased score changes that were inside the noise between identical runs.

## Read first
- If there is a project folder (from the `lp-b2b` skill): `GOAL.md`, `decisions.md` (its never-on-the-page list and accepted gaps are closed topics) and `STATE.md`.
- If not: write a three-line goal yourself (who lands, how they arrive, the one action) from the page and what the user told you, show it in one line, and continue unless they correct it. Put the review files in a `review/` folder next to the page or where the user says.
- `references/rubric.md` before scoring and `references/personas.md` before writing persona packs.

Every output opens with the goal in one line.

## Modes

| Mode | Input | Panel | When |
|---|---|---|---|
| quick | draft page text | 3 cold visitors | before design; comprehension only |
| full | a built page (local file or URL) | 3 cold visitors, 1 skeptic, forwarded roles if a company buys, claims-and-legal read, designer | after a build, before going live |
| ab | two pages | 4 judges who never saw either page, order flipped | before publishing a new version, or "which is better" |

## Personas (once per project, reused across rounds)
Write the packs into `review/personas/` following `references/personas.md`. The rule that matters most: no reviewer knows the seller, the offer's history or the brief. A reviewer who knows the offer scores comprehension too high.

## Quick mode
1. Make sure the input holds only what a visitor reads (no internal notes). If not, extract that text first.
2. Run the three cold visitors in parallel as fresh subagents with `references/prompts/visitor-quick.md` (a cheaper model is fine for visitors). If subagents are unavailable, run them one after another and keep each read clean.
3. Summarise in `review/quick/summary.md` and in the chat: per visitor, did they get what it is, who it is for, what they get, how long, how much and what happens next; the gaps more than one visitor named; the top edits; questions only the seller can answer.

## Full mode
1. **Capture**: `python -I scripts/capture.py <url or file:///...> review/capture-<version>/`. It loads lazy images, opens collapsed FAQ answers, shoots phone (390 px) and desktop (1440 px), saves the link-preview text and image, and warns about images that did not load, elements past the screen edge and text covered by a fixed bar. Check every warning against the screenshots; each one caught a real defect before.
2. **Lint**: `python -I scripts/lint.py review/capture-<version>/page-text.txt`. Hits go into the fix list.
3. **Panel**, in parallel, each a fresh subagent that reads only its prompt, its persona and the capture folder: the cold visitors and the skeptic with `references/prompts/visitor-full.md`; forwarded roles (if any) with the same prompt; `references/prompts/compliance.md`; `references/prompts/designer.md`, naming any element the seller has locked.
4. **Scoreboard**: `python -I scripts/scoreboard.py review/round-<N>/`.
5. **Check before you act**: a finding about a number, a quote or the law must cite its source; check claims about what the seller said against the inputs before accepting them.
6. **Fix list**: `review/round-<N>/fix-brief.md` from `references/fix-brief-template.md`: A fixes within the seller's decisions, ranked by effect on the goal; B limits caused by the seller's decisions or by facts only the seller can supply (recorded once, not reopened); C rejected findings with the reason; D questions for the seller. Requests for caveats, operational detail or never-on-the-page items go to C. Requests for real proof (photos, names, profile links, real numbers) go to B.
7. **Apply or hand back**: if you are also building the page, apply the A list (see edit discipline), recapture as the next version and note what changed. Otherwise hand the list back.
8. **Verdict**: `review/round-<N>/verdict.md`: the stop-rule check with evidence, then one short paragraph each on how well the page makes the visitor understand, believe, feel safe and act alone, then the recommendation.
9. If the `cold-eye-review` skill is installed, run it once on the final version before showing the user.

### Edit discipline
Only changes that improve the page. Copy changes by at most 20 percent per round. "No change" is a valid answer. Elements the seller locked stay (they may look better, never disappear). A reviewer's wish never becomes a new section without the seller's yes.

### Stop rule
Stop when all three hold: (a) every cold visitor answers what it is, who it is for, what they get, how long, how much and what happens next correctly; (b) no cold visitor or skeptic names a blocker that a page change within the seller's decisions could still fix; (c) no claims-or-legal blocker a page change can fix (facts only the seller can supply go on their list and don't keep the loop running). The seller's decisions may limit commercial and disclosure lines; structure and comprehension are never limited. Score changes under 2 points are noise. Hard cap: two full rounds after the first build, then stop with a recommendation.

## ab mode
1. Capture both pages into separate folders.
2. Build neutral folders per judge (`review/ab/q1/A`, `q1/B`, ...) with the screenshots, `page-text.txt`, the link-preview text (title, description) and image. Remove anything that reveals which page is which (URLs, version names). Flip the order between judges. Keep the key in `review/ab-key.txt`, outside their folders.
3. Run four judges in parallel with `references/prompts/judge-ab.md` (use a strong model). Each scores each page as if it were the only one they saw.
4. `python -I scripts/scoreboard.py review/ab/ --key review/ab-key.txt`. Report per-page averages, preferences and where each page wins. Read the pattern, not the decimals: four simulated judges, and a seat can flip between identical runs.

## What the user sees
In the chat, short: the verdict against the goal, the scoreboard, the fixes applied, the list only the seller can answer, the stop recommendation, the phone first screen, and the file paths.

## Never
- Give reviewers the brief, the decisions file or earlier scores (the claims-and-legal read gets the decisions file only to respect closed topics).
- Reopen a decision the seller made or a gap they accepted.
- Chase a score target; a "9 out of 10 from everyone" rule proved unreachable under the seller's own decisions.
- Remove a locked element, add caveats to numbers, or ask for payment terms or legal entity details on the page.
- Publish, push or send anything.
