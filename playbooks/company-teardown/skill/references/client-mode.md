# Client mode

Client mode turns a run into a deliverable for the company itself: a one-page teaser and the full interactive report, checked against a rubric and released without a person in between when every gate passes. A run is in client mode when `config.report_mode` is `"client"`. Without it, everything here is optional and older runs build unchanged.

## What the client receives

1. **The one-pager** (`dashboard/onepager.pdf`, also `onepager.html`): a headline, 3 to 5 key findings, a basis line and a way-in line. It is useful on its own, never sells, and each finding links to its evidence trail in the full report.
2. **The full report** (`dashboard/index.html`): the usual tabs, opening on Overview, whose top shows the same headline and findings as the one-pager, in the same order.

Both are built from one list, `prose.onepager`, so they cannot disagree.

## Rubric

The rubric is a JSON list of rules: `{id, rule, applies_to, level: must|should, level_note, check: code|judge:<name>, check_detail, source, fail_example, pass_example}`. Copy it into the run root as `rubric.json` at intake. When the brief leaves a part of the page out (for example no ad study, so no campaign impact), list it in `config.scope_out` (`sowhat.<move type>`, `gtm.lenses`, `gtm.impact`, `ai.uses`, `competition.compare`): the rubric's R23 then names the part as left out instead of failing it, and the report says so in its checking details. Write it before G1: `runstate.py gate G1` locks the list into `run.json`, and R23 honours only locked entries, so a part added to `scope_out` later can't silence a rule (R23's note names it). The rubric itself is kept privately by whoever runs the skill; the scripts read only `id`, `level` and `check`, and implement the checks.

## prose.json additions

### `prose.onepager` (required in client mode)

```json
{"headline": "one sentence under 20 words stating the strongest finding",
 "findings": [
   {"id": "f1",
    "so": "the takeaway in a few words",
    "value": "24 of 24",
    "label": "what was counted, in words a stranger follows, with [c:id] citations",
    "date": "2026-11-05",
    "means": "one sentence, up to 25 words, on what it means for buyers, price, sales or exposure",
    "reasoning": "1 to 3 sentences joining the cited facts to the finding; a sentence no source states starts with 'Inference:'",
    "kind": "Measured|Public record|One day's check",
    "viz": null,
    "claims": ["w9-c1"]}],
 "basis": "Public sources read up to 5 November 2026, each number checked against its source.",
 "way_in": "The full report, with every source and how each finding was reached: {{report_link}}. The passphrase is in this email."}
```

- 3 to 5 findings. `viz` takes the same shapes as tab-top points.
- `claims` lists every claim id the finding rests on; ids cited in `label` are added automatically.
- `{{report_link}}` is filled at delivery. Until then it renders as the text "the full report".

### Overview top

In client mode, `prose.top.overview` is built from `prose.onepager`: the headline, and one point per finding (`so, value, viz, label, means, kind`, with `goto` set to the finding's trail). Do not write `top.overview` by hand in client mode; the validator rejects one that disagrees.

### Tab-top points: `reasoning` and `claims`

Every other `prose.top.<tab>.points[]` item in client mode also carries `reasoning` and may carry `claims`, as on one-pager findings. Points of kind Estimate or Method do not belong in a tab top in client mode: estimates and the checking method sit in the checking details at the end.

### `prose.overview.further` (replaces `connections` in client mode)

```json
{"heading": "Where to look further",
 "intro": "optional, one sentence",
 "rows": [{"source": "Meta Ads Manager", "clarifies": "which ad angles bring full-price buyers, and which bring only discount buyers", "moves": ["m6"]}]}
```

At least 5 rows. Rows suggest what to look into and where. They never name a team, ask for access, or say what the data would show.

### Moves: `further`

Each `prose.moves.items[]` carries `further`: one line that starts `Where to look further:` and names the records or public places worth looking into, up to 30 words. `data_request` is not used in client mode (the Overview's `further` rows replace it). The idea line may still propose a first move in neutral wording.

## Evidence trails

`assemble` builds `bundle.trails`, one entry per one-pager finding and per tab-top point that cites anything:

```json
{"f1": {"title": "", "value": "", "reasoning": "",
        "claims": [{"id": "w9-c1", "text": "", "source": "", "checked_url": "", "quote": "", "status": "confirmed",
                    "confirmations": 2, "basis": "fact|inference", "read": "2026-11-05"}]}}
```

- Trail ids: the finding id for one-pager findings, `<tab>.<index>` for other tab-top points.
- `quote` and `checked_url` come from the latest verdict; `confirmations` counts distinct `confirmed` verdicts on the id; `read` is the verdict's `checked_at` when present, else the run cutoff.
- The page opens a trail from each card's "How we got here" link, and from the URL hash `#trail=<id>`, which is what the one-pager links to.

## Files a client-mode run adds

| File | Written by | What |
|---|---|---|
| `rubric.json` | intake | The rubric for this run |
| `dashboard/onepager.html`, `onepager.pdf` | `build_dashboard.py onepager` | The teaser |
| `dashboard/screens/layout.json` | `render_test.py` | Per tab, where the top's last card ends at 1440 x 900 |
| `verify/rubric-code.json` | `rubric_check.py` | One row per code rule: pass, fail or n/a, with the items that failed |
| `verify/judges/<judge>/packet.json`, `verdicts*.jsonl` | `judges.py prepare`, the judge agents | What each judge saw and said, one verdicts file per run, plus `verdicts-carried.jsonl` for items unchanged since the last round |
| `verify/scorecard.json` | `gate.py` | Every rule's result, the hard gates, and the release decision |
| `HOLD.md` | `gate.py` | Only when the run is held: which gate, which items, the options |

## Release

`gate.py` releases a run only when every must rule passes (code and judges), `finalize.py` passes, the render test passes, and model and data spend are under their caps. A failed must rule gets up to two fix rounds from the judges' quotes before a hold. Should rules are reported and never hold a run.
