"""Tests for rubric_check.py. Every company, product and sentence here is invented.
Run: python -I -m unittest discover -s tests -p "test_rubric_check.py" """
import copy, importlib.util, io, json, os, sys, tempfile, time, unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent.parent / "skill" / "scripts"
spec = importlib.util.spec_from_file_location("rubric_check", SCRIPTS / "rubric_check.py")
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)

CODE_RULES = ["R02", "R03", "R04", "R05", "R11", "R12", "R13", "R15", "R16", "R17", "R18", "R20", "R22", "R23", "R24", "R25", "R26"]
RUBRIC = [{"id": i, "level": "should" if i in ("R11", "R15", "R26") else "must", "check": "code"} for i in CODE_RULES]
RUBRIC.append({"id": "R07", "level": "must", "check": "judge:insight"})
CLAIMS = [f"q1-c{n}" for n in range(1, 8)]
FURTHER = "Where to look further: store orders and returns by where the kettle was bought, over the last 12 months."


def trail(card, inference=False):
    reasoning = "Every listing checked showed the same pattern [c:q1-c1]."
    if inference:
        reasoning += " Inference: owners who find no answer write to support instead."
    return {"title": card.get("so", ""), "value": card.get("value", ""), "reasoning": reasoning,
            "claims": [{"id": "q1-c1", "text": "An invented fact.", "source": "https://example.org/q1-c1",
                        "checked_url": "https://example.org/q1-c1", "quote": "18 of 20 listings showed an outside seller",
                        "status": "confirmed", "confirmations": 2, "basis": "fact", "read": "2026-11-05"}]}


def finding(fid, so, value, label, means, kind="Measured", viz=None, claim="q1-c1"):
    return {"id": fid, "so": so, "value": value, "label": f"{label} [c:{claim}]", "means": means, "kind": kind,
            "date": "2026-11-05", "reasoning": f"The page checked shows it [c:{claim}].", "claims": [claim],
            "viz": viz or {"type": "dots", "n": 3, "d": 4}}


def point(so, value, label, means, goto, claim, kind="Measured", viz=None):
    return {"so": so, "value": value, "label": f"{label} [c:{claim}]", "means": means, "kind": kind, "goto": goto,
            "goto_label": "The detail", "reasoning": f"The page checked shows it [c:{claim}].", "viz": viz}


def move(mid, mtype, priority=False):
    return {"id": mid, "type": mtype, "priority": priority, "title": f"Kettle area {mid} draws outside sellers",
            "found": "Outside sellers hold most kettle listings on the day checked [c:q1-c1].",
            "matters": "The price most shoppers see is set elsewhere.", "idea": "A seller list kept against the dealer list.",
            "further": FURTHER}


def base_bundle():
    """A complete client-mode bundle that passes every code rule."""
    onepager = {
        "headline": "Outside sellers on Marketplace Nine set the Quillfern price, below the brand's own store.",
        "findings": [
            finding("f1", "Outside sellers set the price", "18 of 20",
                    "Quillfern listings on Marketplace Nine were sold by outside sellers on 5 November 2026",
                    "Those sellers decide the price most online shoppers see.", claim="q1-c1"),
            finding("f2", "The store sits above the market", "22% higher",
                    "is the median gap between the brand's store and Marketplace Nine on matched models",
                    "Shoppers who compare can find the same kettle for less.", claim="q1-c2",
                    viz={"type": "bars", "rows": [{"label": "Store", "value": 100}, {"label": "Market", "value": 78}]}),
            finding("f3", "Repair answers are missing", "0 of 4", "repair questions are answered on the warranty page",
                    "Owners with a broken kettle find no repair price or time.", kind="Public record", claim="q1-c3",
                    viz={"type": "pips", "n": 0, "names": ["Price", "Time", "Address", "Parts"]}),
        ],
        "basis": "Public sources read up to 5 November 2026, each number checked against its source.",
        "way_in": "The full report, with every source and how each finding was reached: {{report_link}}. The passphrase is in this email.",
    }
    overview = {"headline": onepager["headline"], "points": []}
    for f in onepager["findings"]:
        pt = {k: f[k] for k in ("so", "value", "viz", "label", "means", "kind", "reasoning", "claims")}
        pt["trail"] = f["id"]
        overview["points"].append(pt)
    sowhat = {"headline": "Outside sellers on Marketplace Nine undercut the Quillfern store on most kettles.", "points": [
        point("Most listings belong to outside sellers", "18 of 20", "listings on Marketplace Nine were sold by outside sellers",
              "The brand does not set the price most shoppers see online.", "move:m1", "q1-c1", viz={"type": "dots", "n": 18, "d": 20}),
        point("The store sits above the market", "22% higher", "is the median store premium over Marketplace Nine",
              "Shoppers who compare find the same kettle for less.", "move:m2", "q1-c2"),
        point("Repair pages leave owners guessing", "0 of 4", "repair questions are answered on the warranty page",
              "Owners with a broken kettle find no repair price or time.", "tab:timeline", "q1-c3", kind="Public record"),
    ]}
    ai = {"headline": "Answer engines name Quillfern in fewer buying answers than its rival Tessaline.", "points": [
        point("Answer engines often skip the brand", "31%", "of answers to general kettle questions name Quillfern",
              "Shoppers new to the brand rarely meet it there.", "part:offsite", "q1-c4", kind="One day's check",
              viz={"type": "share", "part": 31, "whole": 100}),
        point("The site never uses the buyers' word", "0 of 6", "pages checked on the site say \"gooseneck\", the word buyers use",
              "Answers about gooseneck kettles have little on the site to draw on.", "part:content", "q1-c5",
              viz={"type": "dots", "n": 0, "d": 6}),
        point("Support replies drafted with a model", "12% faster", "replies per hour in a published support study",
              "Support complaints lead the review sites, so this is a fitting place to start.", "part:uses", "q1-c6", kind="Inferred"),
    ]}
    for tab, top in (("sowhat", sowhat), ("ai", ai)):
        for i, p in enumerate(top["points"]):
            p["trail"] = f"{tab}.{i}"
    trails = {f["id"]: trail(f) for f in onepager["findings"]}
    trails.update({f"sowhat.{i}": trail(p) for i, p in enumerate(sowhat["points"])})
    trails.update({f"ai.{i}": trail(p, inference=p["kind"] == "Inferred") for i, p in enumerate(ai["points"])})
    item = {"title": "Gift guides bring steady visits", "evidence": "Seen in two guides [c:q1-c7]", "use": "A guide list", "proof": "Measured"}
    lenses = [{"id": i, "label": lab, "working": [item], "not": [item], "open": [item]}
              for i, lab in (("channels", "Channels"), ("angles", "Campaign angles"), ("offers", "Offers"), ("formats", "Formats"))]
    swot_item = {"point": "Outside sellers hold most listings [c:q1-c1].", "so_what": "The market price is set elsewhere."}
    prose = {
        "onepager": onepager,
        "top": {"overview": overview, "sowhat": sowhat, "ai": ai},
        "overview": {"further": {"heading": "Where to look further", "intro": "Records and tools worth looking into next.",
                                 "rows": [{"source": f"Record {n}", "clarifies": "which kettle models bring repeat buyers"} for n in range(5)]}},
        "moves": {"items": [move("m1", "quick_win", True), move("m2", "double_down", True), move("m3", "budget"), move("m4", "bet")],
                  "swot": {q: [dict(swot_item)] for q in ("strengths", "weaknesses", "opportunities", "threats")}},
        "gtm": {"insights": {"lenses": lenses},
                "impact_intro": "Campaign effects smaller than the normal range of about 12% would not stand out here [c:q1-c7]."},
        "ai": {"body": "Five engines were asked.", "parts": [
            {"id": "offsite", "findings": [{"title": "Review sites shape answers"}]},
            {"id": "technical", "findings": [{"title": "No llms.txt file and no JSON-LD product data"}]},
            {"id": "content", "findings": [{"title": "Product pages skip the buyers' word"}]}],
            "uses": {"items": [{"title": "Support drafts"}]}},
        "compare": {"brands": [{"id": "quillfern", "focus": True}, {"id": "tessaline"}, {"id": "corvantis"}],
                    "indicators": [{"id": "search", "label": "Searches"}, {"id": "reddit", "label": "Reddit mentions"}],
                    "series": {"search": {"quillfern": [["2016-01", 1], ["2026-01", 2]]}, "reddit": {"quillfern": [["2017-07", 3]]}}},
    }
    return {
        "meta": {"name": "Quillfern", "cutoff": "2026-11-05"},
        "config": {"name": "Quillfern", "cutoff": "2026-11-05", "report_mode": "client", "market": None,
                   "impact": {"views": [{"id": "w", "metric": "m", "series": "s", "controls": []}]},
                   "competition": {"scores": [{"id": "a"}, {"id": "b"}]}},
        "prose": prose, "stats": {}, "library": [], "competitors": [{"id": "c1"}],
        "claims": {c: {"source": f"https://example.org/{c}", "status": "confirmed"} for c in CLAIMS},
        "impact": {"rows": [{"campaign": "spring"}], "series": []},
        "trails": trails,
    }


PAGE = """<html><body><nav class="tt-tabs"></nav>
<section class="tt-page" data-page="overview" id="overview" hidden>
  <div data-band="overview" hidden></div>
  <section class="tt-card" id="swot"></section>
  <details class="tt-card tt-fold" id="connections"></details>
</section>
<section class="tt-page" data-page="sowhat" id="sowhat" hidden>
  <div data-band="sowhat" hidden></div>
  <section class="tt-card" id="areas"></section>
  <section class="tt-card" id="signals"></section>
</section>
<section class="tt-page" data-page="deepdive" id="deepdive" hidden><section class="tt-card"></section></section>
<details class="tt-card tt-fold" id="trust"></details>
<script id="bundle" type="application/json">{"x": 1}</script>
<script>
  const TABS = ['overview', 'sowhat', 'timeline', 'gtm', 'ai', 'competition', 'market', 'deepdive'];
  const firstTab = () => 'overview';
  const further = mk('details', 'tt-allmoves');
  const groups = [['opportunities', 'Opportunities'], ['working', "What's working"], ['not_working', "What isn't"]];
</script></body></html>"""


def base_ledger():
    """One invented row per claim, each holding every figure the base bundle's cards show, so R18 finds them."""
    prose = base_bundle()["prose"]
    cards = list(prose["onepager"]["findings"]) + [p for top in prose["top"].values() for p in top.get("points") or []]
    text = " ".join(f"{c.get('value', '')} {c.get('label', '')}" for c in cards)
    return [{"id": c, "text": f"Invented row: {text}", "value": ""} for c in CLAIMS]


BASE_LEDGER = base_ledger()


def make_run(folder, bundle, verdicts=None, layout="default", page=PAGE, files=None):
    folder = Path(folder)
    (folder / "dashboard" / "screens").mkdir(parents=True, exist_ok=True)
    (folder / "verify").mkdir(exist_ok=True)
    (folder / "dashboard" / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
    if verdicts is None:
        verdicts = [{"id": c, "status": "confirmed", "verifier": v} for c in CLAIMS for v in ("v1", "v2")]
    (folder / "verify" / "verdicts.jsonl").write_text("".join(json.dumps(v) + "\n" for v in verdicts), encoding="utf-8")
    (folder / "verify" / "ledger.jsonl").write_text("".join(json.dumps(r) + "\n" for r in BASE_LEDGER), encoding="utf-8")
    if layout == "default":
        layout = {t: {"top_bottom_px": 700, "viewport": [1440, 900]} for t in bundle["prose"].get("top") or {}}
    if layout is not None:
        (folder / "dashboard" / "screens" / "layout.json").write_text(json.dumps(layout), encoding="utf-8")
    if page is not None:
        (folder / "dashboard" / "index.html").write_text(page, encoding="utf-8")
    for name, content in (files or {}).items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content) if isinstance(content, bytes) else path.write_text(content, encoding="utf-8")
    (folder / "rubric.json").write_text(json.dumps(RUBRIC), encoding="utf-8")
    return folder


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "run"
        self.b = base_bundle()

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, rule, previous=None, **kw):
        make_run(self.dir, self.b, **kw)
        return rc.RULES[rule](rc.Run(self.dir, previous))

    def assertPass(self, rule, **kw):
        out = self.check(rule, **kw)
        self.assertEqual(out["status"], "pass", out["failures"])
        return out

    def assertFail(self, rule, why, **kw):
        out = self.check(rule, **kw)
        self.assertEqual(out["status"], "fail")
        self.assertTrue(any(why in f["why"] for f in out["failures"]), [f["why"] for f in out["failures"]])
        return out

    @property
    def op(self):
        return self.b["prose"]["onepager"]

    def top(self, tab):
        return self.b["prose"]["top"][tab]


class BaseBundle(Case):
    def test_every_rule_passes_on_the_base_bundle(self):
        make_run(self.dir, self.b)
        run = rc.Run(self.dir)
        for rule in CODE_RULES:
            out = rc.RULES[rule](run)
            self.assertEqual(out["status"], "pass", f"{rule}: {out['failures']}")


class Text(unittest.TestCase):
    def test_words_skip_citations_and_tokens(self):
        self.assertEqual(rc.words("Twelve kettles [c:q1-c1] sold {{stat:sold_total}} times."), 4)

    def test_sentences_split_before_a_capital(self):
        self.assertEqual(len(rc.sentences("It rose 3.5 times. Then it fell. e.g. not here")), 2)


class R02(Case):
    def test_estimate_kind_fails(self):
        self.top("sowhat")["points"][1]["kind"] = "Estimate"
        self.assertFail("R02", "(a)")

    def test_inferred_passes_on_ai_only(self):
        self.assertPass("R02")
        self.top("sowhat")["points"][1]["kind"] = "Inferred"
        self.assertFail("R02", "(a)")

    def test_modelled_number_and_error_rate_fail(self):
        self.top("ai")["points"][0]["means"] = "A modelled figure puts the error rate near 6%."
        out = self.assertFail("R02", "(b)")
        self.assertTrue(any("(c)" in f["why"] for f in out["failures"]))


class R03(Case):
    def test_too_few_findings_fail(self):
        self.op["findings"] = self.op["findings"][:2]
        self.assertFail("R03", "3 to 5 findings")

    def test_means_of_two_sentences_fails(self):
        self.op["findings"][0]["means"] = "Sellers set the price. Buyers see it first."
        self.assertFail("R03", "one sentence up to 25 words")

    def test_basis_without_cutoff_fails(self):
        self.op["basis"] = "Public sources, each number checked against its source."
        self.assertFail("R03", "cutoff date")

    def test_pdf_pages(self):
        self.assertPass("R03", files={"dashboard/onepager.pdf": b"%PDF /Type /Pages /Type /Page"})
        self.assertFail("R03", "exactly 1 A4 page", files={"dashboard/onepager.pdf": b"%PDF /Type /Pages /Type /Page /Type /Page"})

    def test_no_onepager_is_na_outside_client_mode_and_fails_in_it(self):
        del self.b["prose"]["onepager"]
        self.assertFail("R03", "client mode needs")
        self.b["config"]["report_mode"] = None
        self.assertEqual(self.check("R03")["status"], "n/a")


class R04(Case):
    def test_booking_line_fails(self):
        self.op["way_in"] += " Book a short call with our team."
        self.assertFail("R04", "reads as selling")

    def test_links_in_built_onepager(self):
        good = ('<a href="https://example.org/q1-c1">1</a><a href="index.html#trail=f1">How we got here</a>'
                '<a href="index.html">the full report</a>')
        self.assertPass("R04", files={"dashboard/onepager.html": good})
        bad = good + '<a href="https://example.net/pricing">Plans</a>'
        self.assertFail("R04", "neither a source nor a trail", files={"dashboard/onepager.html": bad})


class R05(Case):
    def test_headline_mismatch_fails(self):
        self.top("overview")["headline"] = "Marketplace Nine sellers set the price."
        self.assertFail("R05", "differs from the one-pager headline")

    def test_extra_overview_card_fails(self):
        self.top("overview")["points"].append(copy.deepcopy(self.top("overview")["points"][0]))
        self.assertFail("R05", "the one-pager lacks")


class R11(Case):
    def test_long_field_and_long_sentence_fail(self):
        self.b["prose"]["moves"]["items"][0]["found"] = " ".join(["Kettle sellers listed more models."] * 13)
        self.assertFail("R11", "field or paragraph")
        self.b["prose"]["moves"]["items"][0]["found"] = " ".join(["word"] * 31) + "."
        self.assertFail("R11", "in one sentence")


class R12(Case):
    def test_second_person_fails_outside_quotes(self):
        self.b["prose"]["moves"]["items"][0]["matters"] = "A buyer wrote \"you get what you pay for\" about the lid."
        self.assertPass("R12")
        self.b["prose"]["moves"]["items"][0]["matters"] = "Your store should list the repair price."
        self.assertFail("R12", "(a)")

    def test_command_phrase_fails(self):
        self.b["prose"]["moves"]["items"][0]["idea"] = "A quick check of the seller list."
        self.assertFail("R12", "(b)")

    def test_headline_opening_with_a_command_fails(self):
        self.top("sowhat")["headline"] = "Check who sells Quillfern kettles on Marketplace Nine."
        self.assertFail("R12", "(c)")


class R13(Case):
    def test_missing_or_presumptuous_further_fails(self):
        self.b["prose"]["moves"]["items"][1]["further"] = None
        self.assertFail("R13", "no 'Where to look further:' line")
        self.b["prose"]["moves"]["items"][1]["further"] = "Where to look further: store orders, which would show the cause."
        self.assertFail("R13", "what it would show")

    def test_internal_data_claim_fails(self):
        self.b["prose"]["overview"]["further"]["intro"] = "Internal data would show which kettles sell."
        self.assertFail("R13", "(b)")


class R15(Case):
    def test_hedge_in_headline_fails_and_the_month_may_does_not(self):
        self.top("sowhat")["headline"] = "Outside sellers may set most Quillfern prices on Marketplace Nine."
        self.assertFail("R15", "hedge in a headline")
        self.top("sowhat")["headline"] = "Outside sellers set most Quillfern prices on Marketplace Nine on 4 May 2026."
        self.assertPass("R15")

    def test_card_and_move_limits(self):
        self.top("ai")["points"][0]["means"] = "Shoppers may never see it, and the cause is unclear."
        self.assertFail("R15", "in one card")
        self.b = base_bundle()
        self.b["prose"]["moves"]["items"][0]["found"] = "Sellers may lead. The cause is unclear."
        self.b["prose"]["moves"]["items"][0]["matters"] = "It could matter."
        self.assertFail("R15", "found and why it matters")


class R16(Case):
    def test_card_without_link_fails(self):
        del self.top("sowhat")["points"][2]["goto"]
        self.assertFail("R16", "no link to the detail")
        self.top("sowhat")["points"][2]["goto"] = "move:m99"
        self.assertFail("R16", "doesn't resolve")

    def test_card_count_note_and_means_length(self):
        self.top("ai")["points"] = self.top("ai")["points"][:2]
        self.top("ai")["note"] = " ".join(["word"] * 41)
        self.top("sowhat")["points"][0]["means"] = " ".join(["word"] * 26)
        out = self.assertFail("R16", "3 to 5 cards")
        whys = " ".join(f["why"] for f in out["failures"])
        self.assertIn("limit 40", whys)
        self.assertIn("means runs 26 words", whys)


class R17(Case):
    def test_layout(self):
        self.assertEqual(self.check("R17", layout=None)["status"], "n/a")
        layout = {t: {"top_bottom_px": 700, "viewport": [1440, 900]} for t in ("overview", "sowhat", "ai")}
        layout["ai"]["top_bottom_px"] = 950
        self.assertFail("R17", "below the first screen", layout=layout)


class R18(Case):
    def test_number_without_citation_fails(self):
        self.top("ai")["points"][1]["means"] = "About 40 buyer comments use the word."
        self.assertFail("R18", "no [c:id]")

    def test_unconfirmed_and_once_confirmed(self):
        verdicts = [{"id": c, "status": "confirmed", "verifier": v} for c in CLAIMS for v in ("v1", "v2")]
        self.assertFail("R18", "latest verdict is partly", verdicts=verdicts + [{"id": "q1-c4", "status": "partly", "verifier": "v3"}])
        once = [v for v in verdicts if not (v["id"] == "q1-c2" and v["verifier"] == "v2")]
        self.assertFail("R18", "one-pager numbers need 2", verdicts=once)

    def test_same_claim_two_values_fails(self):
        self.top("sowhat")["points"][0]["value"] = "17 of 20"
        self.assertFail("R18", "different values")

    def test_typed_number_that_repeats_a_stat_fails(self):
        self.b["stats"] = {"kpi:Kettle models": {"value": 140, "text": "140", "missing": False}}
        self.top("ai")["points"][1]["label"] = "of 140 models carry the word [c:q1-c5]"
        self.assertFail("R18", "repeats {{stat:kpi:Kettle models}}")


class R18Figures(Case):
    def test_card_number_missing_from_its_rows_fails(self):
        self.top("sowhat")["points"][0]["label"] = "listings on Marketplace Nine were sold by outside sellers, 731 of them new [c:q1-c1]"
        out = self.assertFail("R18", "731 is in none of its cited rows (q1-c1)")
        self.assertEqual(len([f for f in out["failures"] if "cited rows" in f["why"]]), 1)

    def test_a_rounded_figure_matches(self):
        rows = [dict(r, text="Median gap on matched models was 21.7 percent.") if r["id"] == "q1-c2" else r for r in BASE_LEDGER]
        self.assertPass("R18", files={"verify/ledger.jsonl": "".join(json.dumps(r) + "\n" for r in rows)})

    def test_compared_scaled_and_year_figures(self):
        pool = rc.row_figures({"text": "Searches 32.3 vs 23.9 in 2025; sales of 3,215,000 units", "value": ""})
        self.assertTrue(rc.figure_in(26, 1.0, pool))  # the change between two figures the row compares
        self.assertTrue(rc.figure_in(3.2, 1e6, pool))  # USD 3.2M for 3,215,000
        self.assertFalse(rc.figure_in(2, 1.0, pool))  # a bare 2 never matches the year
        self.assertFalse(rc.figure_in(35, 1.0, rc.row_figures({"text": "median 25.1%, range 5.3% to 47.9%"})))
        self.assertEqual(rc.figures("USD 3.2M and 60,000 followers"), [(3.2, 1e6), (60000.0, 1.0)])

    def test_a_missing_ledger_fails(self):
        make_run(self.dir, self.b)
        (self.dir / "verify" / "ledger.jsonl").unlink()
        out = rc.RULES["R18"](rc.Run(self.dir))
        self.assertTrue(any("can't be matched to their rows" in f["why"] for f in out["failures"]))


class R20(Case):
    def test_missing_trail_fails(self):
        del self.b["trails"]["sowhat.1"]
        self.assertFail("R20", "no evidence trail")

    def test_long_quote_and_unlabelled_inference_fail(self):
        self.b["trails"]["f1"]["claims"][0]["quote"] = " ".join(["word"] * 30)
        self.b["trails"]["ai.2"]["reasoning"] = "Support studies show faster replies [c:q1-c6]."
        out = self.assertFail("R20", "1 to 25")
        self.assertTrue(any("Inference:" in f["why"] for f in out["failures"]))


class R22(Case):
    def test_no_page_is_na(self):
        self.assertEqual(self.check("R22", page=None)["status"], "n/a")

    def test_tab_order_and_checking_details(self):
        swapped = PAGE.replace("'overview', 'sowhat'", "'sowhat', 'overview'")
        self.assertFail("R22", "the tabs must run", page=swapped)
        moved = PAGE.replace('<details class="tt-card tt-fold" id="trust"></details>\n', "").replace(
            '<div data-band="overview" hidden></div>', '<div data-band="overview" hidden></div><details class="tt-card" id="trust"></details>')
        self.assertFail("R22", "last section", page=moved)


class R23(Case):
    def test_missing_move_group_fails(self):
        self.b["prose"]["moves"]["items"] = self.b["prose"]["moves"]["items"][:3]
        self.assertFail("R23", "no move of type bet")

    def test_ai_top_and_short_time_axis_fail(self):
        for p in self.top("ai")["points"]:
            p["kind"] = "Inferred"
        self.b["prose"]["compare"]["series"] = {"search": {"quillfern": [["2022-01", 1], ["2026-01", 2]]}, "reddit": {"quillfern": [["2023-07", 3]]}}
        out = self.assertFail("R23", "1 or 2 inferred")
        self.assertTrue(any("10-year" in f["why"] for f in out["failures"]))

    def test_parts_the_brief_left_out_are_named_not_failed(self):
        self.b["prose"]["moves"]["items"] = [m for m in self.b["prose"]["moves"]["items"] if m["type"] != "budget"]
        self.b["prose"]["compare"] = {}
        self.b["prose"]["ai"]["uses"] = {}
        for p in self.top("ai")["points"]:
            p["kind"] = "Measured"
        self.assertFail("R23", "no move of type budget")
        self.b["config"]["scope_out"] = ["sowhat.budget", "competition.compare", "ai.uses"]
        out = self.assertPass("R23")
        self.assertIn("left out by the brief: ai.uses, competition.compare, sowhat.budget", out["note"])
        self.assertIn("not locked at G1", out["note"])

    def test_scope_out_added_after_g1_is_not_honoured(self):
        self.b["prose"]["moves"]["items"] = [m for m in self.b["prose"]["moves"]["items"] if m["type"] != "budget"]
        self.b["prose"]["compare"] = {}
        self.b["config"]["scope_out"] = ["sowhat.budget", "competition.compare"]
        locked = {"run.json": json.dumps({"scope_out": {"items": ["competition.compare"], "gate": "G1", "ts": "2026-06-01T00:00:00+00:00"}})}
        out = self.assertFail("R23", "no move of type budget", files=locked)
        self.assertIn("added to scope_out after G1, so not honoured: sowhat.budget", out["note"])
        self.assertIn("left out by the brief: competition.compare", out["note"])


class R24(Case):
    def test_too_many_priority_moves_fail(self):
        self.b["prose"]["moves"]["items"] = [move(f"m{n}", "quick_win", True) for n in range(9)]
        self.assertFail("R24", "9 priority moves")

    def test_claim_dropped_since_previous_draft(self):
        prev = copy.deepcopy(self.b["prose"])
        prev["moves"]["items"][0]["found"] += " A kettle line sold out twice [c:q1-c9]."
        path = Path(self.tmp.name) / "prose-before.json"
        path.write_text(json.dumps(prev), encoding="utf-8")
        self.assertFail("R24", "claim q1-c9", previous=path)
        excuse = json.dumps({"id": "q1-c9", "action": "removed", "note": "The source was withdrawn."}) + "\n"
        self.assertPass("R24", previous=path, files={"verify/corrections.jsonl": excuse})

    def test_newest_draft_is_read(self):
        old = copy.deepcopy(self.b["prose"])
        new = copy.deepcopy(self.b["prose"])
        new["moves"]["items"][0]["found"] += " Dropped later [c:q1-c8]."
        make_run(self.dir, self.b, files={"verify/drafts/round-1.json": json.dumps(old)})
        time.sleep(0.05)
        (self.dir / "verify" / "drafts" / "round-2.json").write_text(json.dumps(new), encoding="utf-8")
        later = time.time() + 5
        os.utime(self.dir / "verify" / "drafts" / "round-2.json", (later, later))
        out = rc.RULES["R24"](rc.Run(self.dir))
        self.assertEqual(out["status"], "fail")
        self.assertIn("round-2.json", out["note"])


class R25(Case):
    def test_short_or_asking_section_fails(self):
        rows = self.b["prose"]["overview"]["further"]["rows"]
        del rows[4]
        self.assertFail("R25", "at least 5 rows")
        self.b = base_bundle()
        self.b["prose"]["overview"]["further"]["intro"] = "With read-only access, the study could rerun."
        self.assertFail("R25", "an ask")

    def test_wrong_heading_fails(self):
        self.b["prose"]["overview"]["further"]["heading"] = "More data"
        self.assertFail("R25", "headed 'Where to look further'")


class R26(Case):
    def test_long_top_and_missing_charts_fail(self):
        self.top("sowhat")["points"][0]["label"] = " ".join(["word"] * 200) + " [c:q1-c1]"
        self.assertFail("R26", "over 220 words")
        self.b = base_bundle()
        for p in self.top("ai")["points"]:
            p["viz"] = None
        self.assertFail("R26", "need a chart")


class Main(Case):
    def main(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = rc.main([str(a) for a in args])
        return code, buf.getvalue()

    def test_exit_codes_and_output(self):
        make_run(self.dir, self.b)
        code, out = self.main(self.dir)
        self.assertEqual(code, 0, out)
        rows = json.loads((self.dir / "verify" / "rubric-code.json").read_text(encoding="utf-8"))
        self.assertEqual([r["id"] for r in rows], CODE_RULES)
        self.assertTrue(all(set(r) == {"id", "level", "status", "failures", "note"} for r in rows))
        self.b["prose"]["moves"]["items"][0]["further"] = ""
        make_run(self.dir, self.b)
        self.assertEqual(self.main(self.dir)[0], 1)

    def test_a_should_failure_alone_exits_0(self):
        self.top("ai")["points"][0]["means"] = "Shoppers may never see it, and the cause is unclear."
        make_run(self.dir, self.b)
        code, out = self.main(self.dir)
        self.assertEqual(code, 0, out)
        self.assertIn("R15", out)

    def test_unusable_run_or_rubric_exits_2(self):
        self.assertEqual(self.main(self.dir)[0], 2)
        make_run(self.dir, self.b)
        (self.dir / "rubric.json").write_text("{}", encoding="utf-8")
        self.assertEqual(self.main(self.dir)[0], 2)

    def test_unimplemented_code_rule_fails(self):
        make_run(self.dir, self.b)
        (self.dir / "rubric.json").write_text(json.dumps(RUBRIC + [{"id": "R99", "level": "must", "check": "code"}]), encoding="utf-8")
        code, out = self.main(self.dir)
        self.assertEqual(code, 1)
        self.assertIn("no code check", out)


if __name__ == "__main__":
    unittest.main()
