# Moves: turning research into identified areas

Research says what is true. This stage sets out what it points to, and it opens the page. A teardown that stops at findings has failed, even when every fact checks out.

Written after the first consumer run, whose reader said: "a bunch of information listed but no real useful presentation", missing the SWOT, what to double down on, the quick wins and how budget could be spent better. Its advice had shrunk to "pull your internal numbers", which was accurate and useless.

## The rule that makes this possible

**Evidence strength and advice strength are separate.** Weak evidence blocks a claim of fact. It does not block naming an area when the step is cheap and reversible. Weigh it by the cost of being wrong:

| Evidence | Move is cheap and reversible | Move is costly or hard to undo |
|---|---|---|
| Strong | State it plainly | State it, with what it would take |
| Thin | Frame it as a test, labelled thin | Frame it as a test, with the result that would justify more |

Stay specific, so a move can't fit any other brand. Say what the area is, how sure the evidence is, and what would prove it wrong. The verification label stays on the facts, and each move carries its own confidence.

## Voice

Go straight into what was found. Set out identified areas and why they matter, and let someone who knows the business draw the conclusion.

- Never say who the page is for, describe the team, or assign owners.
- Don't sequence the reader's work or give deadlines: no "first", "this week", "should", "must" or "needs to", and no imperative verbs. Dates appear only as facts that bear on an area.
- Use "this points to", "worth examining", "one option is", "a test could compare" and "internal data would show", with variety. Stay specific: neutral must not mean vague.
- Move titles are noun phrases naming the area.

The first consumer run's owner called reader statements and "the first job for the company is" presumptuous. A reader inside the company won't take instructions from an outside page. The validator rejects second person and the worst of these phrases in `prose.moves`.

Tailor the emphasis to the G0 decision, without saying so on the page.

## How to rank

Never rank a move first because it's loud or cheap. Ask what it does for the business, and what it unlocks. When public evidence can't show whether the business is healthy, the leading areas are usually the cheap checks that decide the bigger ones. Say which moves depend on which. On the first consumer run the reviewer rejected a service-first opening for this reason: the run's own analysis said nothing showed service cost sales.

## Moves pass (S3b)

Run the performance pass in `references/insights.md` too. Most runs hold specific gaps that were never turned into actions, plus a few missing facts that decide them. List what would make a move specific, then run a small research pass with at most three agents and 40% of the unspent data budget, using `references/performance-briefs.md`. Folders are `w9-*` and up, with claim ids like `w9-c1`. Typical items:

- **Consumer brands:** who holds the marketplace offers and paid slots on the brand's name, rival ad mix, store page audit, search demand and rank by term, and listed peers' marketing share of sales.
- **Software and B2B:** pricing page and packaging audit, search demand and rank, rival positioning, public win and loss signals, and peers' sales and marketing share of revenue.
- **Any target:** macro changes that hit this business directly, such as tariffs or regulation, since the first pass often misses them.

New claims join the ledger through `ledger.py merge`. Anything a move rests on must be checked. The main error rate doesn't cover these rows, so also draw a random sample per workstream, with `ledger.py sample "<run>" --seed <n> --second-ws <ws> --second-n 20`, using fresh verifiers. `report` then publishes their own rate as a finding, and the Moves tab should state it.

## 09-moves.md and prose.moves

Write `09-moves.md` for reading and `prose.moves` for the page, from the same text. The page opens on the identified areas, and `references/insights.md` gives the tab's full order.

1. **Identified areas.** A short statement of what the evidence shows and which areas stand out, plus the three with the most leverage.
2. **Headline findings and how numbers could change the reading.** Three to six hard facts, each with a value, a line of meaning and a source kind, sharpest number included. Then rules: if internal numbers show this, it would suggest that, with illustrative thresholds. Optional dates that bear on the areas.
3. **SWOT.** Three to five points per quadrant, each with its so what, its source kind (`Measured`, `Public record`, `Vendor estimate`, `Assumed model`, `Judgement`, `Mixed`) and evidence strength (`strong`, `medium`, `thin`).  The page shows strength only when it isn't medium. A point with no consequence gets cut. Strengths and weaknesses are inside the company, opportunities and threats outside.
4. **Crossings.** Pair inside and outside points: a strength aimed at an opportunity, a weakness exposed to a threat. Each crossing names the moves it leads to. This step is what turns the SWOT into action, so a move with no crossing or evidence behind it gets cut.
5. **Moves, 10 to 18 in all, with about 8 marked `priority` and a named top three.** The others sit in an expanded view, so nothing is lost. Priority moves carry a `trigger`, saying what result would change the reading. Add a `money` line wherever a dollar illustration is possible, labelled by its assumptions, such as a sensitivity per 5% price change or a cost ceiling per order. Each has a `short` name, `channel`, `when` and `depends`, since the page has a one-screen plan built from them. Walk through every channel and ask who is missing a move: on the first run nobody noticed dealers until review.
   - `find_out`: cheap checks that gate larger moves. Include what public data already allows, such as matching sellers against a public dealer list.
   - `double_down`: what looks like it works. Grade by revealed behaviour, such as an ad kept running for months, a format still drawing views, or a page carrying traffic, and say that this is proxy evidence.
   - `quick_win`: specific gaps, cheap to fix or check. Name the exact page, term or listing.
   - `dealer`, for dealers or the equivalent partner channel, named through `partner_label`: areas acting on that channel, including what other areas do to it.
   - `budget`: `from` and `to`, with what would prove it wrong. Direction only unless real spend is public. Never invent a dollar split. Do give test shares, breakeven figures from labelled assumptions, and sales budget lines such as co-op. Count discounts as spend.
   - `bet`: decisions with real cost or margin at stake, with the options and trade-offs.

   Say what a test needs before it can be read, such as a minimum number of orders, and what happens if it can't be read in time. Every move has: `what`, `why` with citations, `impact` and `effort` (1 to 5, relative judgement), `confidence`, `check_first` (legal or data, if any), `test`, `watch` (the number to look at), `if_wrong`, 
6. **Opportunities, what's working, and what isn't.** `prose.moves.opportunities`, `working` and `not_working`, each with `title`, `evidence`, `use` (labelled So what), `proof` and the `moves` it links to. The page shows them in that order after the moves.
7. **One data request.** Everything only the company holds, in one list, with who holds it and what it decides.
8. **Limits.** What only internal data can settle, and which moves it would change, plus what was cut and why.

## Bands on the evidence tabs

`prose.bands` adds a short so-what at the top of each evidence tab: at most three sentences saying what that tab means for the moves, with citations. Each tab should answer "why am I looking at this?" before showing data. Keep `04-so-what.md` for interpretation and competing readings, and move action advice out of it into Moves.

## Review

The red-team agent in `references/verification.md` also attacks the moves:

> For each move: Does the evidence say what the move claims? Is it specific to this company? Would it hurt anything else in the list? Is the impact rating inflated? What would a sceptical operator in this industry say? Which obvious moves are missing, and which should be cut? Is any move really a finding with a verb attached?

Fix the must-fix list, then have the reviewer re-read the fixes.

## Common failures

- A vague area: "the discount strategy". Name the specific gap, and the threshold that would matter.
- Everything rated high impact. If more than a third are 4 or 5, re-rate them against each other.
- Moves that depend on data nobody outside has, with no test to get it.
- Confidence that reads as a claim about facts. Confidence rates the move, and source kind describes the fact.
- Discounts counted as a cost without asking whether the compare-at price was really charged.
- Ad age read as performance. Ages of live ads show when they launched, and ads from the same batch look the same whatever their theme.
- Rank or sponsor claims taken from one tool. Re-read with a second one, since a routed search tool returned non-Google results and a vendor's rank model didn't reproduce. On Amazon, Sponsored Products need Featured Offer eligibility, so ask who could be paying before suggesting a change.
- Sequence conflicts: a page publishing a turnaround before the ticket data exists, or an ad promising what the page says is unproven.
- Generic advice that fits any brand. If you could swap the company name and it still reads true, cut it.
- Dollar figures with no real spend behind them.
- Legal-sensitive moves without `check_first`, such as claims, licences and regulated wording. This is research, and it is not legal advice.
