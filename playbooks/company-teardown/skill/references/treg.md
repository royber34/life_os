# Data tools: treg first, free sources where better

[treg](https://treg.to) reaches thousands of third-party data APIs through one MCP connection, billed per call. If it is not connected, the run still works on free sources and web search, with less depth on social, SEO, ads and enrichment. Say so at G0.

Check for it by looking for tools named `mcp__treg__*`, which may need loading with ToolSearch first.

## Discover at run time

The catalog changes, so never hardcode endpoint ids. In the probe:

1. Run `my_tools`. The team's own connected keys win over the catalog and are not metered.
2. Run `balance`, and record it in `run.json`.
3. For each need below that fits the target, run `catalog_search` in plain task words, read the `verdict`, then `catalog_get` on the top result.
4. Write `treg-plan.json`, one row per need:

```json
{"need":"founder X posts","endpoint":"","provider_rank":[],"price":0,"works_rate":0,"samples":0,"own_key":false,"chosen_at":"YYYY-MM-DD"}
```

**Needs:** company firmographics; similar companies; company search in a category; funding rounds; partners, customers and investors; headcount history; job posts; company news; news search; tech stack; SEC filings; SEO overview; ranked keywords; backlinks and referring domains; keyword trends; web traffic; AI-answer mentions; X posts and X search; LinkedIn posts and employees; YouTube channel videos and captions; Instagram posts; TikTok posts; TikTok Shop products; Meta ad library; Reddit search and comments; Trustpilot reviews; Amazon product detail and reviews; App Store reviews; patents; page extract; web search.

If search finds nothing, record "none", go to a free source, and consider `catalog_request` to file the gap.

## Choosing and calling

- Prefer endpoints with a `works` rate of at least 0.7 and at least 50 samples. Below that, use only with a second source.
- **Routed endpoints** (`treg.<capability>`) try several providers. Set `X-Treg-Route-Max-Cost` to `0.10`. For enrichment, set `X-Treg-Route-Waterfall: 0` unless you record why you need it on, since each provider that bills a miss adds cost.
- Record which provider served each call. It is named in the response.
- A status 200 can still be a miss, such as a null name. Log it as `hit:false`, do not retry the same provider, try one alternative from the plan, then write "not found".
- On an endpoint failure, search again once, and record the swap.
- Spend caps come from `run.json`: per run, per agent and per call. Default ceiling is USD 0.30 per call. Check `catalog_get` before bulk calls.
- If a call result invites a review, use `review` honestly after using the result.

## Search result pages

Check that a search endpoint returns real Google results before trusting its ranks. In the first consumer run, one routed endpoint returned unrelated pages (Netflix, Red Hat), and a vendor's rank model showed rank 1 on terms where DataForSEO live reads showed the domain absent. Prefer a live results endpoint with Google links and People Also Ask blocks, read each key term twice, and treat a vendor's rank database as a model.

## Cross-check

A paid result is one vendor's reading. When it becomes a load-bearing claim, confirm it elsewhere:

| Data | Check against |
|---|---|
| Tech stack | Live response headers, page source |
| Headcount | LinkedIn page, company statements |
| Funding | Press release, filing, investor page |
| Traffic and SEO | A second provider, and treat both as estimates |
| Follower or engagement counts | The public page, with the date observed |

## Where each is better

**Use free sources for:** GitHub API, PyPI stats, npm, Wayback CDX, SEC EDGAR, Hacker News Algolia, company registers, recall and regulator databases, trademark registers, the target's own pages.

**Use treg for:** X (plain fetches are blocked), YouTube captions, SEO and backlinks, ad libraries, enrichment, reviews, news search, Amazon and social platforms.

## Reconciling spend

The balance is shared, so one agent cannot tell its own spend from the balance alone. Agents log calls. The orchestrator records the balance before and after each wave, and `cost_report.py` compares the two and prints the gap.
