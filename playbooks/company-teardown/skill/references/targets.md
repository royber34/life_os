# Target types: substitutes and honest expectations

These substitutes, apart from the public repo case, were written before being run on every type. Treat row counts as rough guides, and adjust from the probe.

## Public repo (software or developer tool)

**Expectation line:** "Expect 500 to 1,500 dated rows, pivots with stated reasons, per-person team history and a cost basis if config is public. Revenue and user counts stay estimates."

- History and pivots: commits, migrations, design docs, changelog. Clone blobless and run git with `-c gc.auto=0`; export the tree once for read-only use.
- Economics: price and cost config, billing commits.
- Team: commit authors, areas touched by month. Do not republish email addresses.
- Traction: stars, forks, package downloads, public metrics pages, serial IDs as an upper bound (labelled inference).

**Lanes and families:** feature, tech (`product`); gtm, growth_metric (`growth`); pricing, business_model (`money`); team, funding (`people`); legal, incident (`risk`); pivot, inflection (`turning_point`). A lane left with no rows can be dropped from `config.json`.

**Channels:** website, docs, changelog, blog, github, x, linkedin, youtube, reddit, hackernews, product_hunt, review_site, community, newsletter, marketplace, partner, google_ads, event. Hacker News points and similar go in `likes`, with a note, since bubbles size on `views`.

**If the repo closed, forked or was renamed:** follow redirects, for example `curl -L`, and check whether the name now points to a fork. Date the change as a turning point, treat history after it as the fork's, and say which stars, commits and releases belong to whom. Treat the target as `public_repo` up to that date and `private` after it. Combine modules for the mixed case, and record `public_repo` as the main type in `run.json`.

**GitHub limits:** dated star history needs a login, so use public alternatives such as package downloads, releases and commits, and say so. Controls are other packages in the same category. Tools can disagree about a page, so test an important surface with a second reader before calling it absent.

## Private company, no repo

**Expectation line:** "Expect 100 to 400 dated rows, with revenue and headcount as ranges and more than half of the economics as inference. Interviews with former staff or customers would add the most depth."

- History: Wayback across home, pricing, careers and docs; changelog and status pages; founder posts and podcasts; press.
- Team: LinkedIn and enrichment data; job posts as a dated signal of strategy.
- Traction: search and traffic estimates, review counts, customer logos over time, hiring velocity.
- Economics: public pricing, vendor list prices, subprocessors page, tech stack headers.
- Entity and legal: company registers, trademarks, patents, Form D or local equivalents, terms history.

**Lanes:** same as public repo, with `tech` often thin.

## Listed company

**Expectation line:** "Facts are abundant and scope is the constraint. Narrow to one business unit or question first. Expect several hundred rows, most of them primary-sourced."

- Annual and quarterly filings, earnings transcripts, investor decks, segment data.
- Team becomes executive changes and organisation announcements. Funding becomes capital allocation and M&A.
- Add analyst commentary (labelled secondary), regulator filings, patents and litigation.
- Audited numbers make the checks easier, so spend them on segment claims and management statements.

**Lanes:** growth_metric, segment, business_model, pricing, product, leadership, capital, gtm, legal, incident, pivot, inflection.

## Consumer brand

**Expectation line:** "Expect 150 to 500 dated rows, rich evidence on marketing and customer voice, thin evidence on economics. Revenue, margin and repeat rate stay ranges unless filed, and retail performance is rarely public."

W5 becomes the **product and claims module**, and W7 leads:

| Question | Where |
|---|---|
| Range and launches | Wayback of shop and collection pages, sitemaps, press, retailer pages |
| Price | Unit price, pack sizes, subscriptions and bundles, price changes over time |
| Marketplace | Amazon listing, rating, review count and best-seller rank snapshots; TikTok Shop |
| Retail | Stockist pages, retailer listings, announcements. Report as presence, not sales |
| Ads | Meta ad library: active count, creative themes, duration as a rough signal of what works |
| Social | Instagram, TikTok, YouTube: cadence, engagement, creators and affiliates |
| Search | Brand and category trends, ranked keywords, backlinks, PR hits |
| Customer voice | Amazon and Trustpilot reviews, Reddit threads: themes, with counts |
| Claims and regulation | The claims made on the product and page, and the rule set that applies (for example cosmetics, supplements, food, medical devices). Cite the regulator, and state that this is not legal advice |
| Product substance | Ingredient lists, patents, cited studies. Check whether a cited study exists and says what is claimed |
| Risk | Recall databases, regulator warning letters, class actions, trademark registers |
| Economics | Label as inference: price and likely COGS range, average order, any filed accounts, import records if reachable |

Many of these registers are free public sites and not in a data router, so go to them directly.

**Lanes and families:** product, retail (`product`); pricing, pivot (`money`, with pivot's phases as bands); campaign, brand, growth_metric (`growth`); team, funding (`people`); legal, incident (`risk`); inflection (`turning_point`).

**Channels:** website, amazon, tiktok_shop, retail, meta_ads, google_ads, instagram, tiktok, youtube, influencer, pr, seo_page, reddit, email, event.

## Any type

- Say what depends on what. If a section rests mainly on one vendor's estimate, the page says so.
- A wider range is a correct result. Do not narrow estimates to look finished.
- Ask whether the company name collides with anything, and filter it out (an unrelated package, a common word, a trade term).
