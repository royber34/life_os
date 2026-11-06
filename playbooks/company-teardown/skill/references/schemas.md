# Schemas

Every data file is JSONL (one JSON object per line) with all keys present and `null` where a value does not apply, unless marked otherwise. Dates are `YYYY-MM-DD`. The scripts check keys, enums, dates and ids, and fail loudly on a mismatch. Length limits are guidance.

## Run folder

```
teardown-<slug>/
  RUN.md  run.json  heartbeat.log
  00-brief.md  01-probe.md  probe.json  treg-plan.json  sample-events.jsonl  config.json
  02-coverage.md
  03-overview.md  04-so-what.md  05-gtm.md  06-competition.md  07-deep-dive.md  08-decision-memo.md  09-moves.md  [09-lens.md]
  research/<ws>/  section.md  events.jsonl  claims.jsonl  calls.jsonl  progress.jsonl  raw/  [gtm_actions.jsonl profiles.jsonl landscape.jsonl pricing_history.jsonl people.jsonl]
  research/merged/  events.json  metrics.json  gtm.json  competitors.json  landscape.json
  verify/  ledger.jsonl  sample.jsonl  sample-meta.json  batch-v*.jsonl  batch-delta.jsonl  verdicts.jsonl  corrections.jsonl  report.md  report.json  synthesis-review.md
  dashboard/  prose.json  bundle.json  index.html  screens/ (screenshots and render-report.md)
  raw-research-README.md  cost-report.md
```

`<ws>` is one of `w1-timeline, w2-economics, w3-traction, w4-legal, w5-product, w6-team, w7-gtm, w8-competitors`, plus `w9-*` and up for the moves pass.

## run.json

```json
{"slug":"acme","target":"Acme Inc","domain":"acme.com","target_type":"public_repo|private|listed|consumer",
 "mode":"probe|full|refresh","stage":"S0","cutoff_date":"YYYY-MM-DD","treg_available":true,
 "gates":{"G0":{"passed":false,"words":null,"date":null},"G1":{},"G2":{},"G3":{},"G4":{}},
 "budgets":{"treg_usd_cap":5,"treg_usd_per_call":0.30,"wallclock_min_cap":240,"agent_cap":12},
 "balance_checks":[{"label":"before-w1","usd":9.65}],
 "workstreams":{"w1-timeline":{"status":"pending|running|stalled|done|failed","agent_id":null,"started":null,"resumes":0}}}
```

## events.jsonl

One row per dated fact. Every event row is also a claim and is checked by the verifier.

```json
{"id":"w1-12","date":"2026-08-11","date_end":null,"date_precision":"day|week|month|year",
 "lane":"feature","kind":"event|span|metric","title":"max 80 chars","detail":"1 to 3 sentences",
 "metric_name":null,"metric_value":null,"metric_unit":null,
 "person":null,"function":null,
 "basis":"fact|inference","confidence":"high|medium|low","source":"URL, or repo:path@commit, or commit:hash",
 "source_kind":"primary|secondary|aggregator","load_bearing":false,"tags":[]}
```

- `lane` must be listed in `config.json` under `lanes`.
- Phase bands on the timeline come from `kind:"span"` rows with lane `pivot` and a title starting `Phase `.
- A metric series is many rows with `kind:"metric"`, same `metric_name` in snake_case.
- Inference rows state their reasoning in `detail` and put the fact rows they rest on in `tags` as `rests-on:<id>`.

## claims.jsonl

Numbers, dates, names, quotes and attributions in a `section.md` or a profile that are not already event rows. Cite them inline in prose as `[c:w3-c7]`; cite event rows as `[c:w1-12]`.

```json
{"id":"w3-c7","text":"the claim as one sentence","type":"number|date|quote|attribution|existence",
 "value":"what must match, or null","source":"URL or repo path","source_kind":"primary|secondary|aggregator",
 "basis":"fact|inference","confidence":"high|medium|low","load_bearing":false}
```

Flag `load_bearing:true` for anything in a key-numbers table, a phase boundary, a revenue or user estimate, a legal exposure, or a competitor threat rating.

## calls.jsonl

One row per paid or metered call.

```json
{"ts":"ISO 8601","ws":"w7-gtm","endpoint":"treg.x.user.posts","provider_served":"anyapi",
 "price":0.0005,"purpose":"founder timeline","status":200,"hit":true,"claim_ids":[]}
```

## progress.jsonl

Appended after each finished item and before the next starts: `{"ts":"ISO 8601","item":"pricing page history","n":3,"rows":14}`.

`heartbeat.log` has one line per item at the run root: `ISO-8601 <ws> <n> <item>`.

## gtm_actions.jsonl (w7)

Ids use the form `w7-g<n>`, so they cannot collide with the event ids `w7-<n>`.

```json
{"id":"w7-g3","date":"2026-08-11","time_utc":null,
 "channel":"x|youtube|linkedin|instagram|tiktok|tiktok_shop|amazon|retail|meta_ads|google_ads|influencer|pr|product_hunt|review_site|docs|changelog|blog|podcast|hackernews|reddit|community|newsletter|email|website|seo_page|agent_seo|marketplace|github|partner|referral|pricing_hook|event|other",
 "actor":"handle or name","format":"video|thread|post|reply|page|listing|repo|ad|email|talk|podcast|article|launch|program|other",
 "title":"max 100 chars","hook":"max 25 words, paraphrase","cta":null,"asset_url":null,"linked_product":null,
 "views":null,"likes":null,"reposts":null,"replies":null,"bookmarks":null,"metrics_observed_at":null,
 "lift_metric":null,"lift_before":null,"lift_after":null,"lift_window":null,
 "basis":"fact|inference","confidence":"high|medium|low","source":"URL","source_kind":"primary|secondary|aggregator","load_bearing":false,"notes":null}
```

## profiles.jsonl (w8: top 15 to 25 competitors)

```json
{"id":"w8-p1","name":"","short_name":"max 18 chars","org":"","group":"id from config.competition.groups",
 "hq":null,"founded":null,"ownership":"private_vc|public|nonprofit|academic|government|big_tech_unit|open_source_project|bootstrapped|family",
 "overall":"2 to 3 sentences: what it is and why it matters here",
 "business_model":"","pricing":"","size":"","revenue":"","traction":"","funding":"",
 "positioning":"","positioning_line":"max 12 words","icp":"","gtm":"","moat":"","weaknesses":"",
 "recent_moves":[{"date":"YYYY-MM-DD","event":"","source":"URL"}],
 "scores":{"<score id from config>":0},
 "threat_level":"high|medium|low","threat_why":"","partner_level":"high|medium|low|none","partner_shape":null,"partner_why":null,
 "coverage":{"<component id from config, optional>":"yes|partial|no"},
 "gaps":"","sources":["URL"],"confidence":"high|medium|low"}
```

Scores are integers 0 to 5, with the rubric written in `config.json`. Scores are the writer's judgement and the page labels them that way.

## landscape.jsonl (w8: long list up to 50)

```json
{"id":"w8-l1","name":"","org":"","group":"","what":"one sentence","url":"","why_listed":"","source":"URL","confidence":"high|medium|low"}
```

## pricing_history.jsonl (w2)

`{"id","date","plan","price","unit","change","source","source_kind","confidence"}`. Input for the synthesis. Scripts do not read this file, so a price that matters also goes in as an event row, which gets checked.

## people.jsonl (w6)

`{"id","name","function","start","end","basis","confidence","source"}`. Public-role facts only. Never store personal emails or home addresses. Input for the synthesis. Scripts do not read this file, so tenure dates that matter also go in as event rows.

## verify/ledger.jsonl

Written by `ledger.py merge`. Rows may also carry `merged_ids`, and bulk metric series carry `series_size`, `series_ids` and `note`, so one long series counts as one row sampled at one point. Merged data rows gain `ws`.

```json
{"id":"w3-c7","ws":"w3-traction","origin":"claims|events|gtm","text":"","value":null,"source":"","source_kind":"",
 "basis":"","confidence":"","load_bearing":false,"cited_in":[]}
```

## verify/sample.jsonl

Ledger rows plus `"stratum":"load_bearing|low_or_aggregator|random|second_sample"` and `"in_random":true|false`. Only `in_random` rows feed the overall wrong rate. Random rows are drawn from what the first two strata leave. Second-sample rows count for their workstream only.

`probe.json` is one JSON object: `{"surfaces":[...rows...],"expected_rows":...}`, where `expected_rows` is an integer, or an object keyed by workstream. `treg-plan.json` is a JSON list. The ten sample events go in `sample-events.jsonl` at the run root.

## verify/verdicts.jsonl

```json
{"id":"w3-c7","status":"confirmed|partly|wrong|unreachable|unsupported","evidence_quote":"max 25 words","checked_url":"","note":"","verifier":"v1"}
```

- `unsupported`: the row has no checkable source, or the source does not contain the claim.
- `unreachable`: the source could not be opened after one retry on a second page.
- Corrections after a `wrong` verdict go in `verify/corrections.jsonl`: `{"id","action":"corrected|downgraded|removed","note"}`.

## config.json

Written at the end of the probe, and used by the merge, the verifier and the page.

```json
{"name":"Acme","lede":"one line","cutoff":"YYYY-MM-DD",
 "periods":[{"id":"all","label":"Full history","from":"YYYY-MM-DD","to":"YYYY-MM-DD"}],"default_period":"all",
 "lanes":[{"id":"feature","label":"Features","family":"product|growth|money|people|risk|turning_point"}],
 "people":[{"name":"","group":"founder|core|community|ai"}],
 "kpis":[{"label":"","metric":"metric_name or stat id","agg":"last|sum7|max|stat","fmt":"int|usd|pct|text"}],
 "metric_cards":[{"id":"","title":"","note":"","kind":"line|bar|range","series":[{"metric":"","label":""}],"default":true}],
 "response_curves":[{"id":"","label":"","metric":"","default":true}],
 "channels":[{"id":"","label":"","match":{"channel":[],"actor":[]}}],
 "competition":{"groups":[{"id":"","label":""}],"scores":[{"id":"","label":"","rubric":""}],
   "default_x":"","default_y":"","components":[{"id":"","label":""}]},
 "market":null,"impact":null}
```

- `components` may be empty, and the coverage matrix hides itself.
- `market` is null unless the brief names a lens question. When set it holds `{"title","domains","tiers","fits","supply":[...],"demand":[...]}`, and the page shows a Market tab. Most runs leave it null.

## dashboard/prose.json

```json
{"overview":{"summary":[{"heading":"","body":"markdown","goto":"timeline"}]},
 "so_what":[{"heading":"","kind":"verdict|lesson|risk|implication|call|next|flip","body":"markdown"}]}
```

`prose.moves` and `prose.bands` are described in `references/presentation.md`.

Numbers in prose use tokens: `{{stat:id}}` or `{{kpi:label}}`, resolved at build time. Prose may cite `[c:id]`.

## Optional page keys

`references/presentation.md` lists the optional keys the page also reads, such as `config.stats` and `kpis[].note`.

## dashboard/bundle.json

Written by `build_dashboard.py assemble`. Contents: `meta`, `config`, `prose`, `stats`, `events`, `metrics`, `gtm`, `competitors`, `landscape`, `library`, `claims`, `verification`. Field-level contract: `references/presentation.md`.
