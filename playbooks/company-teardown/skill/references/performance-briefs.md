# Agent briefs: moves pass and performance pass

Use these in S3b, with the common brief in `references/agent-brief-common.md` pasted first. Replace the brackets. These briefs produced the most useful findings on the first consumer run, so keep their rules on denominators, saved files and proxies.

Add to every brief:

> Your folder is `research/<ws>`, with claim prefix `<prefix>`. Spend cap: USD [cap], at most USD 0.30 per call. Build tidy files with one row per ad, post or video, and compute from them with a saved script. Every count has a denominator and a date. Save every 10 calls. Stop at [limit] tool calls. Log calls in `calls.jsonl` with exactly these keys: ts, ws, endpoint, provider_served, price, purpose, status, hit, claim_ids. Save every paid response in `raw/` where the tool allows it. Where it doesn't, say so, and keep the call id. Don't turn relative dates into exact ones. Engagement, ratings, search and run length are proxies, and don't show sales. Say that once, and never claim a sales effect. Write section.md starting with "Read for action": at most 12 sentences, each a measured pattern with count, denominator, date and citation. Write descriptively, with no recommendations. No em-dash characters.

## W9 and up: moves pass

Pick what the target needs. Typical agents:

**Channel and paid placement.** Who holds the marketplace offers and paid slots on the brand's name, category terms and rivals. Read live results at least twice with a tool that returns real results, and compare a second vendor. Classify the target's and rivals' live ads by a stated rule, giving counts and dates. Say what can't be seen, such as who pays.

**Owned surface and demand.** Search demand and rank by term, and an audit of public pages by template: what's stated and what's absent. Save page text. Record refusals, and never work around them.

**Benchmarks.** Primary filings for peers' marketing share and margins, published fee schedules, regulatory or tariff changes that hit this business directly, and market data, each with an exact source and date. Don't model the target's sales.

## Performance pass

**Own performance.** Parse ended and live ads, and classify each by angle with a stated first-match rule: discount, mission or cause, credibility, function, category, launch, gift, perks, and anything specific to the target. Compute angle, format and landing page counts, using only ended ads for run length, since ages of live ads reflect launch batches. Pull 100 or more social posts across 12 months, with median engagement by theme and format and the best and worst ten. For video, compute views per year since upload by theme. Build a dated offer calendar from page captures and public archives, against the search index in the same weeks and at rivals. Show demand beside attention by product line. For marketplaces, show ratings and price by line and band. For earned media, show reach by type and whether sponsored.

**Rival benchmark.** The same measures for four to six rivals, using the same angle labels, so each pattern compares with the target. Add terms: warranty, shipping, returns, financing, discount programmes and trials. Add partnerships, creators and which channels each is active on. Say what couldn't be read, such as catalogue ads with template copy.

**Buyer and channel voice.** Code at least 150 comments or reviews by a stated rule: reasons, who they are, complaints, what they compared it with and which won, wording they use, and stage (before or after purchase). Report counts by source with denominators, and name any source that invites critics. Then the channel: partner or door mix by type and region, a sample of partner sites for price and message, specialist and institutional routes, public procurement records, and trade events with dates. Software targets: integrations, marketplaces, resellers, review sites, community and sales-led signals.

**Campaign impact.** Inventory every dated metric, and say whether each is a real measure or a vendor model. List 15 to 30 dated campaigns with start date, precision and source, and flag dates that are only capture dates. Buy search series with controls at the needed grain, keeping scales comparable. Write `study.json`, and run `python -I "<skill>/scripts/campaign_impact.py" "<run>/research/<ws>/study.json"`. Check `references/insights.md` for the data the study needs before buying any. Report how many readings were tested, by verdict and type, how many chance alone would produce, overlaps, and how large a move the normal range can see.

### study.json

```json
{"campaigns":[{"id":"c01","name":"","type":"product_launch","start":"YYYY-MM-DD","precision":"day|month|year","event_id":"","source":"","claim_id":null,"note":""}],
 "metrics":[{"id":"search_weekly","label":"","unit":"index","cadence":"weekly|monthly","adjust":"full|seasonal",
   "pulls":[{"id":"main","series_id":"search_weekly_main","label":"","own":[["YYYY-MM-DD",0]],"controls":{"rival name":[["YYYY-MM-DD",0]]},"controls_weekly":false}]}]}
```

Use `adjust: seasonal` where the controls aren't a fair comparison, such as vendor click models. Monthly dates are `YYYY-MM`. Set `controls_weekly` when monthly metrics use weekly control series. At least three controls are needed for a control adjustment.

## Verifiers for these rows

Give them `references/verification.md`'s brief, plus: "You may read the tidy files, raw files and scripts of each workstream, and any older file they draw on. Recompute counts and medians. Trace at least five rows back to raw. Re-code a small sample, and report disagreement. Re-run the study arithmetic. Re-run about one market-data row in four through the data tool, and treat a moved snapshot as partly right, with both values." Check moves-pass rows with a random sample of 20 per workstream using `sample --second-ws <ws> --second-n 20`. Check performance-pass rows in full.

## Review panel

See `references/review-panel.md`.
