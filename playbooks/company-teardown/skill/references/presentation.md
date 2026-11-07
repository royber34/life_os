# Presentation layer

The page is one self-contained HTML file built from `dashboard/bundle.json`. It makes no network requests. Tabs, in order: Overview, So what (the moves, when `prose.moves` is set), Timeline, Go-to-market, AI (only when `prose.ai` is set), Competition, Market (only when `config.market` is set), Deep dive.

## Build steps

```
python -I "<skill>/scripts/build_dashboard.py" assemble "<run>"   # writes dashboard/bundle.json
python -I "<skill>/scripts/build_dashboard.py" validate "<run>"   # lists every problem, exits 1 on any
python -I "<skill>/scripts/build_dashboard.py" build "<run>"      # validates, writes dashboard/index.html, prints the size
python "<skill>/scripts/render_test.py" "<run>/dashboard/index.html" "<run>/dashboard/screens"
```

`assemble` reads `config.json`, `dashboard/prose.json`, `research/merged/*.json`, `verify/*` (optional), the numbered docs 03 to 09 and `research/*/section.md`. Docs are split on H1 and H2. `validate` and `build` also accept a folder holding `bundle-sample.json`.

## Bundle fields

- `meta`: `name`, `lede`, `cutoff`, `data_range` `[first, last]`, `counts` (`events, metrics, gtm, competitors, landscape, library_docs, library_sections, claims`).
- `config`: as in `schemas.md`, plus the optional keys below.
- `prose`: as in `schemas.md`, plus the optional keys below.
- `stats`: `{id: {value, text, fmt, date, missing}}`. Built in: `events_total, metrics_total, gtm_actions, gtm_views_total, competitors_total, landscape_total, lanes_total, docs_total, cutoff`. Also every `config.stats` id, `kpi:<label>` for each KPI, and `last.<metric>`, `max.<metric>` or `sum7.<metric>` when prose uses them.
- `events`: non-metric rows, plus computed `lane_label` and `person_group`.
- `metrics`: `id, date, metric_name, metric_value, metric_unit, person, title, basis, confidence`.
- `gtm`: rows plus computed `row`, the id of the first matching `config.channels` entry.
- `competitors`, `landscape`: as in `schemas.md`.
- `library`: `{id, doc, doc_title, group, doc_order, idx, heading, level, md}`. `doc` is the file stem, or the folder name for a `section.md`.
- `claims`: `{id: {source, status}}`, for cited ids only. `status` is the verdict, or `unchecked`.
- `verification`: null, or the shape below. Null shows "Not verified yet" on Overview.

## Optional keys beyond schemas.md

- `kpis[].note`: caption. `kpis[].metric_high`: shows a low to high range. `fmt` also accepts `compact`.
- `metric_cards[].series[].person`: limits a series to one person. A `range` card has two series, low then high.
- `channels[].color_index`: shares a colour across channels. An entry with both match lists empty catches everything left, so put it last.
- `config.stats[]`: `{id, from, where, since, positive, contains, agg, of, fmt}`. `from` is `events|metrics|gtm|competitors|landscape`. `where` is `{field: [allowed]}`. `positive` names a field that must be above zero. `contains` is `{fields, text}`. `agg` is `count` or `sum:<field>`. `of` divides by another stat id.
- `config.competition.self`: the profile id of the target itself. It's left out of the threat grid and stands out on the map.
- `config.default_period_gtm`: a separate starting period for the Go-to-market tab, useful when most actions are recent.
- `prose.gtm`: `{intro, playbook}` in markdown, shown on the Go-to-market tab.
- `overview.summary[].goto_label`, and `so_what[].goto`, `goto_label`, `group`. `group` puts a heading over cards.
- `goto` is a tab id (`moves, overview, sowhat, timeline, gtm, competition, market, deepdive`) or `doc:<slug>`.

## Moves and bands

`references/moves.md` says what goes in these.

```json
{"moves":{
  "headlines":[{"value":"24 of 24","label":"markdown with citations","kind":"Measured|Public record|Vendor estimate|Assumed model|Judgement|Mixed"}],
  "partner_label":"optional name for the partner section, such as Dealers or Integrations",
  "answer":{"heading":"","body":"markdown","top3":"markdown","rules_note":"","first":"optional list of dates that bear on these areas"},
  "rules":[{"if":"","then":"","moves":["m1"]}],
  "swot":{"strengths":[{"point":"","so_what":"","kind":"Measured","evidence":"strong|medium|thin"}],"weaknesses":[],"opportunities":[],"threats":[]},
  "crossings":[{"pair":"Strength x opportunity","text":"markdown","moves":["m1"]}],
  "when_order":["optional list giving the order of when values"],
  "items":[{"id":"m1","short":"3 or 4 words","priority":true,"trigger":"required when priority","money":"optional","type":"find_out|double_down|quick_win|dealer|budget|bet","channel":"","when":"","depends":"","title":"","what":"","why":"","impact":1,"effort":1,
    "confidence":"high|medium|low","check_first":null,"test":"","watch":"","if_wrong":"",
    "from":"budget moves only","to":"budget moves only","goto":null,"goto_label":null}],
  "data_request":[{"data":"","holder":"","decides":""}],
  "limits":"markdown"},
 "bands":{"overview":"","sowhat":"","timeline":"","gtm":"","competition":"","deepdive":""}}
```

All of `headlines`, `answer.body`, `rules`, `swot`, `items`, `data_request`, `opportunities`, `working` and `not_working` are required once `prose.moves` exists. `when` values are short timing groups, such as Time-sensitive or Near term, and never assign work. The validator rejects an incomplete move, a bad type, confidence or score, a budget move with no `from` and `to`, an empty SWOT quadrant, a crossing that names a missing move, fewer than 3 headlines, a priority move with no trigger, and second person in the moves text. Priority moves show as cards. The rest stay on the page in an expanded view, and a jump to one opens it. Older bundles with no `prose.moves` still build and open on Overview.

## Plain fields on a move

Each move should carry `found`, `matters` and `idea`. The card shows these three, with `what`, `why`, `money`, `trigger`, `check_first`, `test`, `watch` and `if_wrong` in a fold. A move without `found` falls back to `what`. Rules are in `references/moves.md`.

## Insights, impact and connections

- `prose.gtm.insights`: `{heading, summary, stats[], brief{heading,note,rows}, lenses[{id,label,intro,working[],not[],open[]}], tables[{id,title,note,columns,rows}]}`. Items are `{title, evidence, use, measure, proof}`. Opens the Go-to-market tab.
- `prose.gtm.impact_intro` and `config.impact.views[{id,label,metric,series,controls}]`, where `metric` is a study metric id, `series` is its `series_id`, and `controls` are the generated names in `series.json`, in the form `control_<name>_<pull id>` with spaces as underscores. Any `research/*/campaign_impact.jsonl` with its `series.json` is read into `bundle.impact`, and only the listed series go into the page.
- `scripts/campaign_impact.py` produces the study files. See `references/performance-briefs.md`.
- `prose.overview.connections`: `{heading, intro, rows[{tool, adds, settles, moves}]}`.
- `prose.moves.opportunities`, `working`, `not_working`: items are `{title, evidence, use, proof, moves[]}`.

A section with `hidden` in its markup never draws, since the runtime skips hidden parents. Unhide it at load time, as `moves.js` and `impact.js` do.

## Top of each tab

`prose.top.<tab>` opens a tab. Readers decide here whether to go further, so write it last, and keep it visual. The old `bands` text moves into a small fold beneath.

- `headline`: one plain sentence under 20 words, stating the main so what.
- `points[]`: usually four, at most five, each with:
  - `so`: the takeaway in a few words. This line is what the reader remembers.
  - `value`: the number or short quote.
  - `viz`: optional, one of `dots{n,d}`, `pips{n,names}`, `bars{rows[{label,value,text,focus}],max}`, `range{lo,hi,min,max,min_label,max_label,assumed}` or `share{part,whole}`.
  - `label`: says exactly what was counted, in words a stranger follows, with citations. It shows above the picture.
  - `means`: one or two sentences on what the number means for the business, and how far it can be trusted. Every number the reader sees needs this.
  - `kind`: such as Measured, Estimate, Public record, or Method. Every number needs a citation, unless the kind is Method.
  - `goto` and `goto_label`: `move:<id>`, `part:<id>`, `tab:<tab>`, `doc:<slug>` or `id:<tab>/<element id>`.
- `doors[]`: chips to the next layer, `{label,goto}`. Leave these out if the tab already has filter chips.

Test: each panel has to answer "what am I looking at, what was counted, what do I take away?" by itself. Never use shorthand that depends on knowing how the research was run. "Buyer names it" failed this: the reader couldn't tell that it meant AI answers to questions that mention the brand. Row stats and signal titles follow the same test, so they're sentences and never labels.

Write `value` and `label` so they read as one sentence: "0 of 3 | repair questions are answered on the warranty page". Don't compare unlike things, such as answers to different questions, in one chart. Prefer a plain number to an obscure rate, and name any company the first time it appears.

Rules: no gauges for judgement scores, since they make a judgement look measured. Use `assumed: true` for modelled ranges, which draws a dashed bar. A single fact can stay as text with no chart. Don't use alarm colours, since the evidence rarely supports alarm.

## Rows, not cards

Moves and AI findings are one-line rows that open on click, so a reader scans the list in seconds and nothing is lost. Each row shows the title, a short `stat` with its citation, impact and effort pips, and timing. Main areas also show `idea`, because a reader who sees only titles doesn't get the point. Everything else sits in the row. Further moves sit in a visible fold right under the main ones, named with their count, since a chip alone was easy to miss. Sections below the list stay closed, with counts in their titles. The SWOT goes on the Overview, above the trust section: its points show, and each so what opens on click.

## Rivals over time

`prose.compare` is optional, and adds a chart section at the top of the Competition tab, with one shared time axis.

- `heading`, `intro`, `default_from` (`YYYY-MM`).
- `brands[{id,label,focus,on}]`: mark the target with `focus: true`.
- `indicators[{id,label,short,what,note,on}]`: `what` says in plain words what's measured, and `note` holds limits and citations. Use one source per indicator, and never mix vendors. Set `on` for the charts shown first.
- `series.<indicator>.<brand>`: `[["YYYY-MM", value], ...]`. A missing month stays missing. It breaks the line, so a gap never reads as a trend. An indicator with `step: "year"` holds one value per year, dated `YYYY-07`: use it for small counts, where single months are noise.

An indicator may carry `shade[{from,to,label}]`, for months that look unreliable: they stay visible and are left out of the scale. Check series before plotting: put terms in one Trends request or rescale on a shared anchor, cut months where a vendor's method changed, and leave out any brand whose domain covers far more than the product. Readers click chips to add or remove charts and brands. They can switch between actual values and change since the start.

Community history, for consumer brands:

- **Reddit:** count posts with the brand in the title inside the category's main forum (r/ebikes for e-bikes, say), month by month, using the free Arctic Shift archive (`arctic-shift.photon-reddit.com/api/posts/search`).
  - Listing posts one month at a time works where its counting endpoint times out. Check the two methods against each other on months where both exist.
  - Fetch the forum's total posts one month per request. Plot posts per 10,000, since forums grow a lot.
  - Read about 25 random titles per brand by hand to check precision. Combine spellings, such as e-bike, e bike and ebike.
  - Never use site-wide bare words: a brand named after a common word or a sport is mostly about that word.
  - Compare three-year blocks, because one base year can flip the story.
- **YouTube:** Google Trends with `gprop=youtube` gives 10 years of search interest. Show yearly means, since small terms round to whole numbers.

No free source gave multi-year counts for news, TikTok, Instagram or forums outside Reddit (GDELT refused calls, and Trends' news property returned zeros), so say so on the page rather than leave a chart out silently.

## AI tab

`prose.ai` is optional. When present, the AI tab appears after Go-to-market.

- `heading`, `body`, `stats[{value,label}]`, `score_tables[]`.
- `parts[{id,title,intro,findings[{title,found,matters,idea}],swot{strengths,weaknesses,opportunities,threats},tables[]}]`, normally `offsite`, `technical` and `content`.
- `uses{title,intro,items[],tables[]}`. Each item has `top`, `title`, `idea`, `effort`, `impact`, `evidence`, `gap`, `comparables`, `tools`, `data`, `risks`, `test`. All are shown as inferred. Items with `top` show first, and the rest fold away.
- A table is `{id,title,note,columns,rows}`, and cells may hold citations.

## Verification block

`bundle.verification` is null, or `{label, claims_total, checked, random_checked, load_bearing_checked, counts, wrong_rate, wrong_rate_ci, unreachable, workstreams, cutoff}`. `assemble` builds it from what `ledger.py report` writes to `verify/report.json`, and takes `checked` and `counts` from `verdicts.jsonl`. If only `verdicts.jsonl` exists, the block shows counts under the label "partial: no report written".

## Market rows

`config.market.supply[]`: `id, name, provider_org, domain, subcategory, what, access_tier, fit, fit_reason, api, auth, pricing_model, price_points, rate_limits, commercial_use, resale_allowed, scale, url, terms_url, notes, confidence, sources[]`. `domain`, `access_tier` and `fit` are ids from `domains`, `tiers` and `fits`, each a list of `{id, label}`.

`config.market.demand[]`: `id, segment, examples, size_estimate, size_basis, annual_budget, current_tools, jobs_to_be_done, pains, channels, wtp, buying_process, confidence, sources[]`, `key_supply[]` (supply ids) and a numeric `priority_score` from 0 to 5.

## What config controls

Title and lede, periods, lanes and their colour family, people and team sub-rows, KPIs, metric cards and their default state, response curves, channels, competitor groups, score axes and rubrics, coverage components, and the Market tab. Markup holds none of these.

Rules worth knowing:

- Period id `all` always spans the true data range, whatever its dates say.
- Family `turning_point` draws diamonds and the dashed rules on charts.
- A lane of family `people` with two or more named people splits into sub-rows. `founder` and `core` people get their own row.
- Phase bands come from `kind:"span"` rows in lane `pivot` with a title starting `Phase `.
- The dashed rules on "What it moved" mark the top tenth of actions by views.
- Go-to-market rows dated on the cutoff have an unknown real start, so they sit in a band labelled "Seen on read date", and never pile up on one date.

Text tokens: `{{stat:id}}`, `{{kpi:label}}` and `[c:id]`. All bundle text goes through `textContent` or the markdown renderer, which links only http(s).

## What the validator rejects

Any lane, channel, metric name, group, score id, doc slug or claim id referenced but absent. Bad dates, unresolved tokens, U+2014, phrases listed in `BANNED_PHRASES`, a partial market block, output over 5 MB. A KPI or stat with no value fails too. Config lanes and channels with no rows only warn.

## Reading the render report

`render-report.md` has one row per check, with pass or FAIL, and the script exits non-zero on any failure.

- Counts compare the page with `meta.counts`. SVG marks may differ by 1% or 1 mark. Everything else is exact.
- Separation checks show that Timeline search, sort, confidence and zoom leave the other tabs alone.
- "Reset all restores every default" compares live params with the defaults.
- "No missing markers" fails if a value renders as `missing: ...` on any tab.
- The network checks fail on any console error, failed request or request to another host.

`screens/` holds every tab at 1440 and 390 wide, tiled if tall, plus Timeline in dark. Look at them: passing checks do not prove a page reads well. Long tabs stop at six tiles.

## Publishing, optional

`dashboard/index.html` works when opened directly, emailed or hosted anywhere. To publish it as a private claude.ai Artifact, publish that one file as a plain page. Treat the result as private until you choose to share the link, and check the bundle holds nothing you would not share.
