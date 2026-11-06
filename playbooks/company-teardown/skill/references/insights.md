# Go-to-market insights and campaign impact

Listing activity is not insight. A marketing or sales head needs to learn what has worked, what hasn't and where the openings are, by channel, angle, offer, format, product, timing, audience and sales route. On the first consumer run, the reader rejected a page that had this activity listed and judged the so whats thin.

## Performance pass (S3b)

Run after the first check, within the data budget. S3b sets the agent limit. Full briefs are in `references/performance-briefs.md`. Save tidy files with one row per ad, post or video, and compute from them with saved scripts.

1. **Own performance:** ended and live ads with a stated angle rule, 100 or more social posts by theme and format, video views per year since upload, a dated offer calendar from page captures, and demand against attention by product line.
2. **Rival benchmark:** the same measures for four to six rivals, so every pattern can be compared.
3. **Buyer and channel voice:** at least 150 coded comments with reasons, complaints, stage and comparisons, plus door mix, partner pricing and message, and institutional routes.
4. **Campaign impact:** a before-and-after study for each dated campaign against each key metric, net of the same weeks a year earlier and of rival or category controls. Set a normal range from placebo windows, and state how many results chance alone would produce.

Have fresh verifiers check every row in full, and let them read the tidy and raw files. Give them the older files they'll need too, or they will mark good rows unsupported.

## Writing the insights

`prose.gtm.insights` opens the Go-to-market tab, with the full activity record kept below it. For each lens, write three columns: working, not working or unproven, and opportunity. Each item has:

- `title`: the finding, as a claim.
- `evidence`: counts, denominators and rival comparison.
- `use`: what it suggests, in the voice set out in `references/moves.md`.
- `measure`: for opportunities, what a test could watch, and what result would argue against it.
- `proof`: how strong it is.

Add a possible campaign brief, a dated 12-month calendar, and whichever field tables fit: for consumer brands a price ladder by channel, objections, sell-in outline, territory table and target doors; for software plans and packaging, free-to-paid signals, self-host against cloud, objections, and target integrations or segments.

## Fitting this to the target

The lenses and connections change by target type. Keep the three columns and the voice.

| Target | Lenses | Campaign metrics | Data connections |
|---|---|---|---|
| Consumer brand | Channels, angles, offers, formats, products, timing, audience, sales and dealers | Search, modelled clicks, ratings, social | Ad accounts, store and marketplace back ends, CRM, orders and sell-through, service, finance |
| Public repo or developer tool | Channels, angles, launches, formats, pricing, audience, community, integrations | Stars, downloads, search, docs traffic, social | Product analytics, billing, CRM, ad accounts, community, support |
| Private B2B or software | Channels, angles, pricing and packaging, formats, segments, sales motion, partners | Search, review counts, job posts, web traffic | CRM, marketing automation, product analytics, billing, ad accounts, call recordings |
| Listed company | One unit: channels, segments, pricing, geography, partners, capital use | Reported segment figures, search, analyst commentary | Management accounts, CRM, ad accounts, by unit |

Where a lens has no evidence, leave it out and say so in the limits. Comparison sites replace marketplaces for software, and partners replace dealers.

## Campaign impact

Write `study.json` as `references/performance-briefs.md` sets out, and run `scripts/campaign_impact.py`, which writes `campaign_impact.jsonl` and `series.json` in the workstream folder. List views in `config.impact.views`. The page shows campaigns on the metric's timeline with a verdict colour, a before-and-after panel, a table per metric and a summary by campaign type.

**Check the study's needs before buying data.** Weekly tests need 8 weeks before and after, plus a year earlier, so about two years of data, three controls for the control adjustment, and 20 placebo windows. A 12-month pull gives "not measurable" on every row. When controls move outside their normal range, the study reports a category shock and declines to read the row, even if the net looks large, because the adjustment can't be trusted. Results don't enter the ledger by themselves: write the ones the page cites as claims in that workstream's `claims.jsonl`.

**State how large an effect the test can see.** On the first run the normal range ran as wide as +44%, so "within noise" meant "no large effect", and the first draft overclaimed that campaigns only maintain the brand. Say the size of what can't be seen, and say what internal data would settle it.

## The So what tab

Moves first, then opportunities, then what's working and what isn't, then the evidence, SWOT, crossings and competing readings. It replaces separate Moves and So what tabs, which overlapped.

## Data connections

`prose.overview.connections` lists the connections and data that would turn these signals into measured results, in the order that matters for the priority moves: what each adds, what it settles and which moves it firms up. Fit it to the target. Consumer brands usually need ad accounts, marketplace and store back ends, a CRM or field tool, order and sell-through systems, service records and finance. Software targets need the product analytics, billing, CRM and ad accounts.

## Review

The review panel in `references/review-panel.md` includes a CMO and a head of sales. Have them test each lens. Ask what the evidence holds that the page missed.
