# Templates

## Project folder
```
<project>/
  STATE.md         gates passed (with the user's words and date), versions, next step
  GOAL.md          the paragraph everything is judged against
  brief.md         offer, buyers, pain in their words, proof, constraints, build size
  decisions.md     decisions with words and source, never-on-the-page list, accepted gaps, defaults
  inputs/          what the user handed over, unchanged
  02-wireframe.md and 02-wireframe-page-text.md
  03-copy.md
  site/            index.html, thanks/index.html, assets/, _directions/, build-report.md
  review/          personas, captures, review rounds (written by lp-b2b-review)
```

Every file except GOAL.md opens with a line `Goal: <one line from GOAL.md>`, so each stage's output is read against it.

## GOAL.md
```
# GOAL
<One paragraph of at most 120 words (the short lines below don't count): what the offer is in one sentence; who lands, how they arrive, on what device, what they know before the click; what they must understand, believe and feel; the one action and what counts as success.>

- Who lands: <segments> | <channel> | <device> | <what they know already>
- The one action: <what they do> | success: <the event you can count>
- Understand: what this is, who it is for, what they get, over how long, for how much, what happens after they act
- Believe: <in this offer's terms>
- Feel: <recognised, relieved, safe to act alone: in this offer's terms>
- Page type: sell now | order request | demand test (shows the finished offer; the signup is the signal; nothing invented)
```

## brief.md
1. The offer as it will be sold: what, for whom, what is included, the client's effort as one small number, the seller's work, options with price and duration, risk reversal.
2. Buyers: segments; who decides, who signs, who gets the link forwarded (only where a company buys).
3. Pain in the buyer's words (quotes with source), then what the sellers say about themselves, kept separate.
4. How visitors arrive; the link preview as the first thing they see.
5. Proof that exists (with what each number is) and proof that doesn't.
6. Constraints: brand, domain, language, currency, legal market, host.
7. Build size, with the reason.

## decisions.md
```
## Decisions
| ID | Decision | In their words | Source | Date |
## Never on the page (the user's own items; the defaults in style.md apply anyway)
| ID | Item | Why |
## Accepted gaps (limits the user accepts; reviewers don't reopen them)
| ID | Gap | What it limits |
## Defaults (not confirmed by the user)
| ID | Default | Used because |
```

## STATE.md
```
# STATE: <project>
Goal: <one line>
| Stage | Status | Gate | User's words | Date |
| 1 brief | | G1 | | |
| 2 page | | G2 | | |
| 3 build | | G3 | | |
| 4 review | | G4 | | |
| 5 go live | | G5 | | |
Versions: live <v or none> | preview <v or none>
Open: <missing facts and questions>
Next: <one line>
```
