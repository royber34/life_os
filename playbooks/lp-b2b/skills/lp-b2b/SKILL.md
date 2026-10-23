---
name: lp-b2b
description: Builds a B2B sales landing page that gets a business buyer to act (order, request a start, book, sign up or join a waitlist) without a sales call. Starts by asking the key questions (the page's goal and one action, the offer, the ideal customer and how they arrive, prices, risk reversal, proof) or reads the call notes, transcripts or offer docs the user hands over, then writes the structure and wording, tests them on simulated first-time visitors, builds one static HTML page with a working form and link preview, and walks through a go-live checklist. Stops for the user's approval at five gates and never publishes on its own. Use when the user wants a landing page, sales page, offer page, order page or waitlist page for a B2B product or service, says "build me a landing page", or asks where their landing page project stands or what comes next.
---

# lp-b2b

You build a sales page that a stranger can act on alone. Picture the visitor: they got a link in a LinkedIn message, a cold email or a forwarded WhatsApp, they open it on a phone between two meetings, they have never heard of the seller, and they decide in seconds whether to keep reading. Everything in this skill serves that person.

Keep it simple. One page, one action, plain words. Don't build anything the user didn't ask for.

## How the work is staged

| Stage | You produce | Gate (the user approves before you go on) |
|---|---|---|
| 1 Brief | `GOAL.md`, `brief.md`, `decisions.md`, questions with defaults | G1: the goal and the answers |
| 2 Page | section order and wireframe text, tested on cold visitors; then the final copy | G2: the wireframe |
| 3 Build | two first-screen design directions; one static page with form, link preview, thanks page | G3: the design direction |
| 4 Review | a panel of simulated first-time visitors, a fix list, one or two fix rounds | G4: the rendered page and the verdict |
| 5 Go live | the go-live checklist; deploy only when the user says so | G5: each publish |

Stage 2 instructions are in `references/stage-page.md`, stage 3 and 5 in `references/stage-build.md`. Stage 4 uses the `lp-b2b-review` skill. Read a stage's file when you reach it.

Keep the state in `STATE.md` (template in `references/templates.md`): which gates passed, with the user's words and the date. When the user comes back ("continue my landing page", "where are we"), read `STATE.md`, say in three lines where things stand, and name the next step. Never start a stage before the previous gate is recorded; building on a version nobody approved is the most common way these projects waste days.

## The goal comes first
Every project starts with `GOAL.md`: one paragraph of at most 120 words on who lands (how they arrive, on what device, what they know), the one action, and what they must understand, believe and feel to take it without a call. Every stage output opens with the goal in one line and how the stage serves it. The review judges the page against `GOAL.md` before anything else. If a stage drifts from the goal, stop and say so.

## Stage 1: Brief

1. **Find or make the project folder.** Use the folder the session runs in if it is empty or already holds this project; otherwise create `landing-page/` inside it. Save anything the user hands over (call transcripts, notes, an offer doc, an old page) to `inputs/` and read it in full.
2. **Ask the key questions** in `references/brief-questions.md`, but only what the inputs do not already answer: at most seven questions, in two or three rounds, plain language, each with a default the user can accept with "yes". Wait for the answers before writing the files. If the user says "go with your defaults", or is not there to answer (an unattended run), write the files on the defaults, mark each one as a default, and stop at G1 with the questions listed.
3. **Extract from the inputs**, each with its source (file, timestamp copied exactly): the offer as it will be sold; every decision the user or their team made, in their words; every number, with what it is (one example or an average, which period, whose result); the buyer's pain in the buyer's own words, kept apart from what the seller says about themselves; the proof that exists and the proof that doesn't.
4. **Buyer voice.** If only the sellers speak in the inputs, say so, and offer one short research pass (posts and comments by people in the target group, reviews of the alternative they use today) to collect the buyer's own words. A page built only on the seller's story tends to describe the pain in the seller's words, and buyers notice.
5. **Write the files** from `references/templates.md`: `GOAL.md`, `brief.md`, `decisions.md` (decisions, a "never on the page" list, gaps the user accepts), `STATE.md`.
6. **Gate G1.** Show the goal paragraph, the answers and defaults, what proof is missing, and the next step. Stop and wait.

## Rules for every stage
- The writing and claim rules in `references/style.md` apply to every word you write.
- Never invent customers, testimonials, logos, user counts, results or portraits. A clearly labelled example of the product's output is fine.
- The user signs in, pays and connects accounts. You publish, push or send a test request through a live form only after the user says yes to that step.
- Show results in the chat, short, with the file paths underneath; don't make the user open files to see what you did.
