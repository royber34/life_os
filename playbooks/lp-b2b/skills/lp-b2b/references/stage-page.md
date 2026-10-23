# Stage 2: page (structure, then copy)

Structure decides whether a cold visitor understands the offer; copy decides whether they believe it and act. Test the structure as plain text on simulated first-time visitors before anything is designed: in one real build, four review rounds with personas briefed on the offer missed that the page asked visitors to choose an option before it said what the product was. The seller saw it in one look when opening the live page as a stranger would.

## Default section order
Change it only with a reason tied to `GOAL.md`, written next to the change.

| # | Section | Job for the cold visitor | Must contain |
|---|---|---|---|
| 1 | First screen | What is this, is it for me, what do I do, what do I risk | The promise (outcome for whom, plain words); who it is for in one line; the button; the risk reversal directly under the button; a short proof line; a small link to prices |
| 2 | Pain | I recognise my situation | Headings that state the pain in the buyer's words, not a topic label |
| 3 | How it works | I can picture it and my part is small | Three steps; "Your part" as one small amount of time next to "Our part"; a labelled example of the output when no client proof exists |
| 4 | Before and after | I see the change | Side by side, the same rows, real numbers |
| 5 | Proof | I believe it | Real people and real numbers; the founders' own story counts |
| 6 | Options | I know what I get, how long, how much, and which is mine | Each option: price, duration, what is included, what you leave with, who it is best for; a recommendation in words; the entry option stands on its own |
| 7 | Risk reversal | It is safe to try | Repeated near the options and the form |
| 8 | FAQ | My specific worry is answered | Objections and detail; detail lives here, never in the first screen |
| 9 | Act | I can do it now, alone | Few fields (two steps if more than four, optional fields last); what happens next in three steps |

Two rules hold whatever the order: the visitor knows what the product is before any option is offered, and every option shows its price and duration where it is chosen.

## Step A: wireframe
1. **Message hierarchy**: one primary message, at most three supporting ones, the top five to eight objections each with the section that answers it. Use the buyer's words from the brief.
2. **Section order** from the table above.
3. **Draft lines per section**: headline, subline, key lines, button labels, visuals in [brackets] with the exact numbers they show. Real wording. Where a fact is missing, write `[MISSING: what]` and the placeholder text that shows until the user supplies it. A placeholder must look like one, and is never worked out from an offhand remark (a "factor of 20" said on a call is not a measured number).
4. **Link preview text**: title and description that make sense to someone seeing them in a chat with no context.
5. Write `02-wireframe.md` (all of the above plus open points) and `02-wireframe-page-text.md` (only what a visitor reads, top to bottom, visuals in [brackets]).
6. **Quick test**: run the `lp-b2b-review` skill in quick mode on `02-wireframe-page-text.md`. Fix every comprehension gap and note what changed.
7. **Gate G2**: show the section order with one line each, the first-screen lines, the link preview, what each test visitor understood and what you fixed, and the open points. Stop and wait.

## Step B: copy (after G2)
1. Write `03-copy.md`: final copy for every section in order; the link preview (title, description, what the preview image says); form fields (label, required or optional, optional last; hidden `page_version` and `source`); button labels; "what happens next" in three steps; the thanks page; footer and legal lines; a list of placeholders still open.
2. When no client proof exists, include a labelled example of the product's output written for a made-up reader in the target group. In testing, the missing example was the blocker every simulated visitor named first.
3. State the client's effort as one small number that survives the reader adding it up.
4. Edit pass for clarity, so-what, proof, specificity and risk. Then run `python -I <lp-b2b-review skill folder>/scripts/lint.py 03-copy.md` and fix every hit.
5. Move on to stage 3. The user approves the copy as part of the rendered page at G4.

## Never
- Offer options or a "which one fits" chooser before the page has said what the product is.
- Add caveats or averages to result numbers, or operational detail.
- Invent customers, testimonials, logos, numbers or portraits.
