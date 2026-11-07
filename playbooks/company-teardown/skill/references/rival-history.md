# Rival history

This workstream collects up to 10 years of comparable attention data for the target and its main rivals. It feeds the rivals-over-time charts at the top of the Competition tab (`prose.compare`, format in `references/presentation.md`). It runs in S3b, after the competitor workstream has named the rivals.

Everything here measures attention, not sales, and the page says so.

## Scope

- **Brands:** the target plus four to six rivals from `06-competition.md`, or from the competitor workstream's rows. Pick the rivals a buyer would weigh up, plus one larger player for scale. A rival whose name covers far more than the product (a conglomerate or a whole retailer) can join only the charts where its term or page is specific enough.
- **Window:** 120 months, ending with the last full month. Keep shorter series and say where they start.
- **Folder:** `research/wN-rival-history/` with the usual files, plus `series.csv` and `indicators.json`.

## Indicators, in order of value

| Indicator | Source | Cost | Use when |
|---|---|---|---|
| Search interest, target market | Google Trends on treg (`serpapi.x.google-trends`, `date=all`) | About USD 0.015 per request | Always |
| Wikipedia page views | Wikimedia REST pageviews API, per article, monthly | Free | The brands have their own articles |
| Search visits, paid visits and ranked terms (vendor estimates) | SpyFu domain overview on treg (`spyfu.google.domain.overview`, 120 months) | About USD 0.10 per domain | The brands have their own domains |
| Community talk | Reddit, through the free Arctic Shift archive | Free | Consumer brands with an active category forum |
| YouTube search interest | Google Trends with `gprop=youtube` | About USD 0.015 per request | Products people research on video |

For other target types, pick series that exist for every rival with five or more years of history and one method throughout. Examples are GitHub stars and forks, package downloads, app-store rank histories and job-post counts. Apply the same checks.

Check treg's catalog first for anything newer. No free source gave usable multi-year counts for news, TikTok, Instagram or forums outside Reddit in the first run: GDELT refused calls, and Trends' news property returned zeros. Say so on the page if they're still missing.

## Collecting each one

**Search interest.**
- Choose one term per brand that means the brand. Use the bare name where it's distinctive, and the name plus the product word where the bare name is a common word or a place.
- Test ambiguous terms against a Trends related-queries pull before using them.
- Put up to five terms in one request, so they share a scale. Join requests by rescaling on one anchor term present in each, and record the factors.
- Note where each line is a different kind of term, since a bare name catches more than a name plus a product word. Lines then show direction better than size.

**Wikipedia.** Use the article for the brand or product line, not the parent company, where one exists. Note when an article starts, or when it was a redirect, since views jump at that point.

**Vendor estimates.**
- Use one vendor for every brand, and never mix vendors in one chart.
- Look for jumps that hit many brands in the same month. They are usually method changes. Cut those months, or cut the window to start after them, and say so in the chart's note.
- Leave out any brand whose domain covers far more than the product.

**Reddit.**
- Find the category's main forum, not a brand's own forum, which leans to that brand.
- Count posts with the brand in the title, month by month, from `arctic-shift.photon-reddit.com/api/posts/search` (`subreddit`, `title`, `after`, `before`, `limit=100`, `sort=asc`, paging with `after` set to the last `created_utc`).
- The counting endpoint (`/posts/search/aggregate`) times out on long spans with a title filter. Listing posts one month at a time works. Check the two against each other on months where both exist.
- Fetch the forum's total posts per month, one month per request. Chart posts per 10,000 forum posts, since forums grow a lot.
- The title filter matches whole words. Combine a brand's spellings (with a hyphen, a space or neither), dedupe by post id, and keep only titles that match a strict pattern.
- Read about 25 random titles per brand by hand and record precision in `precision.csv`.
- Never use site-wide bare words. A brand named after a common word or a sport is mostly about that word.
- Be polite: one request at a time, a short gap, retries with backoff, and a generic User-Agent.

**YouTube search interest.** Use the same terms as for search interest. Show yearly means, since small terms round to whole numbers each month.

## Files

- `series.csv`: `date` (`YYYY-MM`), `brand`, `indicator`, `value`, `unit`, `geo`, `source`, `vendor_estimate`. Leave missing months missing; never interpolate.
- `indicators.json`: per indicator, what it measures, unit, geo, source, the term or page per brand, window, whether it's comparable across brands, and its limits.
- `claims.jsonl`: every number the page will cite, such as changes over the window, ratios between brands and coverage facts.
- `calls.jsonl` and `raw/`, as for any workstream.

## Checks

Before plotting, check each series:
- Recompute from raw files.
- Look for method jumps.
- Test term ambiguity.
- Divide community counts by community growth.

Then give every cited claim to a fresh verifier. The verifier recomputes from raw, re-fetches a few free data points, reads its own sample of titles, and tests whether the story holds with a different base year.

Compare blocks of years, such as the first three against the last three, rather than two single years. One base year can flip the story, for example when it was a peak for the target.

## Writing the charts

- Show by default the two or three charts that are complete for most brands, and leave the rest one click away.
- Switch on by default the brands that matter most, and leave large or partly comparable ones off.
- Each chart's `what` says in plain words what was counted. Its `note` gives the main finding with citations, then the limits a reader needs: different term types, method cuts, missing brands, partial years and precision.
- Shade months that look unreliable and leave them out of the scale, instead of deleting them.
- Use `step: "year"` for small counts.
- The section's `intro` states the two or three findings that hold across charts, and says these measure attention, not sales.
- Add one Competition top panel for the clearest finding, linking to the charts with `goto: "id:competition/compare"`.
