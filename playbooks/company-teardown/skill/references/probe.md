# The probe

One agent, about 30 to 40 tool calls, under USD 0.50. It answers: what does this company expose, so what can a full run establish, and what will it cost?

## Surfaces to test, in order

Write one row per surface to `probe.json`: `{"surface","found":true,"url","size_hint","basis"}`.

| Surface | How | Size hint |
|---|---|---|
| Public code | GitHub org and repo search; commits, first commit, docs folder | Commit count, doc count |
| Packages | PyPI, npm | Monthly downloads |
| Public metrics or status page | Site navigation, `/status`, `/rankings`, `/changelog`, `/stats` | What it publishes, how far back |
| Filings and registers | SEC EDGAR, local company registers, Form D | Filing count, latest date |
| Wayback depth | CDX API on home, pricing, careers, product pages | Snapshots and first date |
| Founder and brand accounts | X, YouTube, LinkedIn, Instagram, TikTok | Followers, post count |
| Hiring | Careers page, job post data | Open roles |
| Customer voice | Trustpilot, app stores, Reddit, Amazon reviews, G2 | Review counts |
| Paid and organic marketing | Meta ad library, SEO overview, backlinks | Active ads, keyword count |
| Retail and marketplace | Amazon listings, retailer pages, TikTok Shop | SKUs and retailers found |
| Press and funding | News search, financing events | Article and round counts |
| Headcount | Workforce data | Latest figure and trend |
| Legal pages | Terms, privacy, DPA, subprocessors, security | Which exist, and which return 404 |

A 404 on a legal page is a finding, so record it. For a service that needs sign-in, record "not reachable" and move on.

## Pick the target type

| Type | Signal | Lead workstreams |
|---|---|---|
| `public_repo` | Public repo with real history | All eight, W1 and W5 led by the repo |
| `private` | No repo, no filings | W1 from Wayback and press, W7, W8 |
| `listed` | Files publicly | W2 and W4 led by filings. Ask the user to narrow the scope before G1 |
| `consumer` | Sells physical goods or a consumer brand | W7 leads, then W3 and W5 with the product module |

A company can mix types. Say so and combine the modules from `references/targets.md`. For software, also check docs and API reference, integrations, community, self-hosting, licence and forks, and skip retail.

## Output

`probe.json`, `treg-plan.json` (see `references/treg.md`), ten real sample events in the event schema from different lanes, and a draft of `01-probe.md` with:

1. **What it is**, in two sentences, with sources.
2. **Surface table**: found, size, and how useful it looks.
3. **Modules chosen**, and any dropped with the reason.
4. **Expectation line**, word for word from `references/targets.md`, then adjusted upward or downward with a reason drawn from the surface sizes. Put the estimate in `probe.json` as `expected_rows`.
5. **What this run will not establish.**
6. **Cost:** data spend, tool calls, active time.

If the target is unclear, ambiguous or too thin to justify a full run, say so plainly and recommend probe-only or a narrower question.
