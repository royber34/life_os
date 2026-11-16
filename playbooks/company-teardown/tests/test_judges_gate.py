"""Tests for judges.py and gate.py, on synthetic runs with invented companies and text only.
Run: python -I -m unittest discover -s tests -p "test_judges_gate.py" """
import importlib.util, json, os, re, shutil, subprocess, sys, tempfile, time, unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "scripts"
COMPANY, RIVAL, OTHER = "Quillfen Kettles", "Marrowby Pots", "Tessaly Ware"
TRAIL_F1 = "Every first-page listing checked was held by a reseller, so resellers set the price shoppers saw there."
TRAIL_GTM = "Inference: the copper wording appears in reviews and never on the store, so the store misses buyer words."
LEDGER_F1 = "Resellers held 41 of 60 first-page kettle listings on 3 March 2026."
QUOTE_F1 = "41 of 60 listings were sold by third-party resellers"
EM_DASH = chr(0x2014)

RUBRIC = [
    {"id": "R01", "level": "must", "check": "judge:insight", "applies_to": "one-pager, tab tops",
     "rule": "Invented test rule: each headline states the strongest finding."},
    {"id": "R02", "level": "must", "check": "code", "applies_to": "one-pager, tab tops",
     "rule": "Invented test rule: no estimates on the first screen."},
    {"id": "R06", "level": "must", "check": "judge:cold-reader", "applies_to": "one-pager",
     "rule": "Invented test rule: four role readers react well to each finding."},
    {"id": "R07", "level": "must", "check": "judge:insight", "applies_to": "all prose",
     "rule": "Invented test rule: findings fail the rival swap."},
    {"id": "R08", "level": "must", "check": "judge:insight", "applies_to": "one-pager, tab tops, moves",
     "rule": "Invented test rule: each finding says what it means."},
    {"id": "R09", "level": "should", "check": "judge:sceptical-owner", "applies_to": "one-pager, tab tops",
     "rule": "Invented test rule: findings are new to the owner."},
    {"id": "R10", "level": "must", "check": "judge:cold-reader", "applies_to": "one-pager, tab tops, moves",
     "rule": "Invented test rule: a stranger can restate each item."},
    {"id": "R11", "level": "should", "check": "code", "applies_to": "one-pager, tab tops, moves",
     "rule": "Invented test rule: short sentences."},
    {"id": "R14", "level": "must", "check": "judge:sceptical-owner", "applies_to": "all prose",
     "rule": "Invented test rule: nothing presumptuous."},
    {"id": "R19", "level": "must", "check": "judge:source", "applies_to": "one-pager, tab tops, moves",
     "rule": "Invented test rule: each sentence says what its source says."},
    {"id": "R21", "level": "must", "check": "judge:sceptical-owner", "applies_to": "all prose",
     "rule": "Invented test rule: the weakest number is labelled."},
]


def run_script(name, *args):
    return subprocess.run([sys.executable, "-I", str(SCRIPTS / f"{name}.py"), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8")


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data, indent=1), encoding="utf-8")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def config():
    return {"name": COMPANY, "report_mode": "client", "cutoff": "2026-03-05", "reader": "a chemist who founded the brand",
            "competition": {"self": "w8-p1"},
            "brand": {"name": "Northgate Notes", "footer": "Northgate Notes reads public sources."}}


def bundle():
    findings = [
        {"id": "f1", "so": "Resellers set the marketplace price", "value": "41 of 60",
         "label": "first-page kettle listings were sold by resellers on 3 March 2026 [c:w9-c1]",
         "means": "Shoppers there see prices the company does not choose.", "reasoning": TRAIL_F1,
         "kind": "One day's check", "claims": ["w9-c1"]},
        {"id": "f2", "so": "Reviews praise the copper base", "value": "18 of 40",
         "label": "buyer reviews mention the copper base [c:w7-c2]",
         "means": "Buyers praise a feature the store page never names.",
         "reasoning": "Eighteen reviews name the base, and the store copy was read in full.", "kind": "Measured",
         "claims": ["w7-c2"]},
        {"id": "f3", "so": "A rival buys the brand's search ads", "value": "12",
         "label": "live search ads on the brand name were bought by Marrowby Pots [c:w9-c3]",
         "means": "A search for the brand can land on a rival's page.",
         "reasoning": "Twelve ads were live on the read date.", "kind": "Measured", "claims": ["w9-c3"]},
    ]
    overview = {"headline": "Resellers set the price of Quillfen's kettles on the main marketplace",
                "points": [dict(f, trail=f["id"]) for f in findings]}
    gtm = {"headline": "Buyers talk about the copper base, and the store never does",
           "points": [{"so": "Copper is the buyers' word", "value": "18 of 40", "trail": "gtm.0",
                       "label": "reviews use the word copper [c:w7-c2]", "means": "The store's wording misses how buyers talk.",
                       "reasoning": TRAIL_GTM, "kind": "Measured"},
                      {"so": "One video carries most views", "value": "70%", "trail": "gtm.1",
                       "label": "of views on the brand's channel came from one unboxing video [c:w7-c4]",
                       "means": "Reach rests on a single post.", "reasoning": "One video held most of the views counted.",
                       "kind": "Measured"}]}
    moves = {"items": [
        {"id": "m1", "title": "Resellers decide what shoppers pay", "stat": "41 of 60 listings [c:w9-c1]",
         "found": "Resellers held 41 of 60 listings on the read date [c:w9-c1].",
         "matters": "Price shoppers compare against the store's own price.",
         "idea": "Compare reseller prices with the store's own each month.",
         "further": "Where to look further: marketplace orders by seller, last 12 months."},
        {"id": "m2", "title": "Name the copper base on the store", "stat": "18 of 40 reviews [c:w7-c2]",
         "found": "Reviews use the word copper and the store does not.", "matters": "Buyers search with that word.",
         "idea": "Put the word on the product page.", "further": "Where to look further: store search terms."}],
        "swot": {"strengths": [{"point": "Buyers praise the copper base", "so_what": "It is a reason to buy.",
                                "kind": "Measured", "evidence": "strong"}],
                 "weaknesses": [{"point": "The store never names it", "so_what": "Search misses it.", "kind": "Measured",
                                 "evidence": "medium"}],
                 "opportunities": [{"point": "Kettle searches rise each winter", "so_what": "A seasonal window.",
                                    "kind": "Public record", "evidence": "medium"}],
                 "threats": [{"point": "A rival buys the brand's ads", "so_what": "Searches leak away.",
                              "kind": "Measured", "evidence": "strong"}]}}
    trails = {f["id"]: {"title": f["so"], "value": f["value"], "reasoning": f["reasoning"],
                        "claims": [{"id": f["claims"][0], "source": "https://example.com/x", "quote": QUOTE_F1}]}
              for f in findings}
    trails["gtm.0"] = {"title": "Copper is the buyers' word", "value": "18 of 40", "reasoning": TRAIL_GTM, "claims": []}
    trails["gtm.1"] = {"title": "One video carries most views", "value": "70%",
                       "reasoning": "One video held most of the views counted.", "claims": []}
    onepager = {"headline": overview["headline"], "findings": findings,
                "basis": "Public sources read up to 5 March 2026, each number checked against its source.",
                "way_in": "The full report, with every source: {{report_link}}. The passphrase is in this email."}
    return {"meta": {"name": COMPANY, "cutoff": "2026-03-05"}, "config": config(), "stats": {},
            "prose": {"onepager": onepager, "top": {"overview": overview, "gtm": gtm}, "moves": moves,
                      "so_what": [{"heading": "Price", "kind": "risk", "body": "Resellers price below the store [c:w9-c1]."}]},
            "competitors": [{"id": "w8-p1", "name": COMPANY, "threat_level": "low"},
                            {"id": "w8-p3", "name": OTHER, "threat_level": "medium", "positioning_line": "Cast iron pots"},
                            {"id": "w8-p2", "name": RIVAL, "threat_level": "high", "positioning_line": "Copper kettles"}],
            "trails": trails,
            "library": [{"id": "07-deep-dive#0", "doc": "07-deep-dive", "idx": 0, "heading": "Imports",
                         "md": "An import broker cleared the first shipment in 2021. The rest of this section is plain."}]}


def ledger_rows():
    rows = [{"id": "w9-c1", "text": LEDGER_F1, "value": "41 of 60", "source": "https://example.com/listings",
             "source_kind": "primary", "basis": "fact", "confidence": "high"}]
    for cid, text in (("w7-c2", "18 of 40 reviews mention the copper base."),
                      ("w9-c3", "12 search ads on the brand name were live."),
                      ("w7-c4", "One video held 70% of channel views.")):
        rows.append({"id": cid, "text": text, "value": None, "source": f"https://example.com/{cid}",
                     "source_kind": "secondary", "basis": "fact", "confidence": "medium"})
    return rows


def make_run(root, with_onepager=True, extra_blocks=0):
    run = Path(root) / "teardown-quillfen"
    b = bundle()
    if not with_onepager:
        del b["prose"]["onepager"]
    b["prose"]["so_what"] += [{"heading": f"Kettle note {i}", "kind": "implication",
                               "body": f"Invented note {i} on how resellers list the copper kettle."}
                              for i in range(extra_blocks)]
    write(run / "dashboard" / "bundle.json", b)
    old = time.time() - 1000
    os.utime(run / "dashboard" / "bundle.json", (old, old))
    write(run / "config.json", config())
    write(run / "rubric.json", RUBRIC)
    write(run / "run.json", {"slug": "quillfen", "target": COMPANY,
                             "budgets": {"treg_usd_cap": 5, "model_usd_cap": 40}})
    write_jsonl(run / "verify" / "ledger.jsonl", ledger_rows())
    write_jsonl(run / "verify" / "verdicts.jsonl",
                [{"id": r["id"], "status": "confirmed", "evidence_quote": QUOTE_F1 if r["id"] == "w9-c1" else r["text"],
                  "checked_url": r["source"], "note": "", "verifier": "v1"} for r in ledger_rows()])
    return run


def packet_text(packet, rule, item):
    for e in (packet.get("items") or {}).get(rule) or []:
        if e.get("item") == item:
            return e.get("text") or " ".join(str(v) for v in (e.get("fields") or {}).values())
    return ""


def good_row(rule, key, text):
    words = (text or "41 of 60").split()
    row = {"rule": rule, "item": key["item"], "verdict": "pass", "quote": " ".join(words[:4]),
           "reason": "Invented reason for a test."}
    if rule == "R06":
        row.update(role=key["role"], label="sounds right")
    elif rule == "R10":
        row["step"] = key["step"]
        if key["step"] == "restate":
            row.update(restatement="A plain restatement of the item.", unclear_terms=[])
    elif rule == "R19":
        row.update(support="supported", stretch=None)
    elif rule == "R09":
        row.update(call="new to me", system=None)
    elif rule == "R14":
        row["flag"] = None
    elif rule == "R07":
        row["rival"] = RIVAL
    elif rule == "R01":
        row["top_item"] = "onepager.f1"
    elif rule == "R21":
        row.update(weakest="41 of 60", relies_on=[])
    return row


def closing_row(rule, n):
    return {"rule": rule, "item": "*", "verdict": "complete", "read": n, "reason": "Read every item."}


def judge_all(run, tweak=lambda row: row, closing=closing_row):
    """Play every judge with passing rows; tweak(row) may change a row, or return None to drop it. A rule in
    exceptions mode gets only its non-pass rows, then closing(rule, expected count), unless that returns None."""
    vj = run / "verify" / "judges"
    for judge in ("source", "insight", "sceptical-owner"):
        packet = read(vj / judge / "packet.json")
        out = []
        for rule, keys in packet["expected"].items():
            left = {e["item"] for e in (packet.get("items") or {}).get(rule) or []}
            keys = [k for k in keys if k["item"] in left]  # carried items are not judged again
            rows = [r for r in (tweak(good_row(rule, key, packet_text(packet, rule, key["item"]))) for key in keys) if r]
            if packet["modes"][rule] == "exceptions":
                rows = [r for r in rows if r["verdict"] != "pass"] + [x for x in [closing(rule, len(keys))] if x]
            out += rows
        for target in [run / a["writes"] for a in packet.get("agents") or []] or [vj / judge / "verdicts.jsonl"]:
            write_jsonl(target, out)  # every run of a repeated judge gives the same rows
    cold = read(vj / "cold-reader" / "packet.json")
    for agent in cold["agents"]:
        data = read(run / agent["input"])
        if agent["rule"] == "R06":
            rows = [good_row("R06", {"item": f["item"], "role": agent["role"]}, f["label"]) for f in data["page"]["findings"]]
        else:
            rows = [good_row("R10", {"item": it["item"], "step": "restate"}, " ".join(it["fields"].values()))
                    for it in data["items"]]
        write_jsonl(run / agent["writes"], [r for r in map(tweak, rows) if r])
    res = run_script("judges", "prepare-compare", run)
    assert res.returncode in (0, 1), res.stderr
    comp = read(vj / "cold-reader" / "compare-packet.json")
    rows = [good_row("R10", {"item": it["item"], "step": "compare"}, it["restatement"]) for it in comp["items"]]
    write_jsonl(vj / "cold-reader" / "verdicts-compare.jsonl", [r for r in map(tweak, rows) if r])


def gate_inputs(run, model_usd="12.40", data_usd="1.2500"):
    write(run / "verify" / "rubric-code.json",
          [{"id": "R02", "level": "must", "status": "pass", "failures": [], "note": ""},
           {"id": "R11", "level": "should", "status": "pass", "failures": [], "note": ""}])
    write(run / "verify" / "finalize.json", {"ts": "2026-03-06T00:00:00+00:00", "ok": True,
                                              "checks": [{"check": "Render test passed", "ok": True, "detail": ""}]})
    write(run / "dashboard" / "screens" / "render-report.md", "# Render test\n\nResult: **PASS**, 4 of 4 checks passed.\n")
    lines = ["# Cost report", "", "- Calls logged: 3", f"- Total logged spend: {data_usd} USD", "", "## Model use", ""]
    if model_usd is not None:
        lines.append(f"- Model use total: {model_usd} USD")
    write(run / "cost-report.md", "\n".join(lines) + "\n")
    later = time.time() + 10
    os.utime(run / "cost-report.md", (later, later))


class RunCase(unittest.TestCase):
    EXTRA = 0  # extra prose blocks; over 150 R14 items switches R14 to failures plus a closing row

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.run_dir = make_run(self.tmp, extra_blocks=self.EXTRA)
        res = run_script("judges", "prepare", self.run_dir)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.vj = self.run_dir / "verify" / "judges"

    def packet(self, judge):
        return read(self.vj / judge / "packet.json")

    def collect(self):
        res = run_script("judges", "collect", self.run_dir)
        return res, read(self.run_dir / "verify" / "judges.json")

    def full_pass(self, tweak=lambda row: row, closing=closing_row):
        judge_all(self.run_dir, tweak, closing)
        res, out = self.collect()
        gate_inputs(self.run_dir)
        return res, out

    def gate(self, *args):
        res = run_script("gate", self.run_dir, *args)
        card = read(self.run_dir / "verify" / "scorecard.json") if (self.run_dir / "verify" / "scorecard.json").exists() else None
        return res, card


class PacketTests(RunCase):
    def test_item_ids_are_stable_and_count_from_one(self):
        ins = self.packet("insight")
        r07 = [e["item"] for e in ins["items"]["R07"]]
        self.assertEqual(r07[:5], ["onepager.f1", "onepager.f2", "onepager.f3", "top.gtm.1", "top.gtm.2"])
        self.assertIn("swot.strengths.1", r07)
        self.assertNotIn("top.overview.1", r07)  # the Overview top is the one-pager in client mode
        self.assertEqual([e["item"] for e in ins["items"]["R01"]], ["onepager.headline", "top.gtm.headline"])
        self.assertIn("move.m1.matters", [e["item"] for e in ins["items"]["R08"]])
        src = [e["item"] for e in self.packet("source")["items"]["R19"]]
        self.assertIn("move.m1.found.s1", src)
        self.assertIn("onepager.f1.card", src)
        self.assertIn("move.m1", [e["item"] for e in self.packet("sceptical-owner")["items"]["R14"]])

    def test_cold_reader_gets_no_citations_links_or_background(self):
        files = [self.vj / "cold-reader" / "packet.json", *sorted((self.vj / "cold-reader").glob("agent-*.json"))]
        self.assertEqual(len(files), 1 + (4 + 2) * 3)  # 4 role readers and 2 restater batches for 9 items, 3 runs each
        for f in files:
            text = f.read_text(encoding="utf-8")
            self.assertNotIn("[c:", text, f.name)
            self.assertNotIn("http", text, f.name)
            self.assertNotIn(LEDGER_F1, text, f.name)
            self.assertNotIn("Every first-page listing checked", text, f.name)  # trail reasoning
            self.assertNotIn(RIVAL + "\", \"threat", text, f.name)
            self.assertNotIn("{{report_link}}", text, f.name)

    def test_role_reader_sees_only_the_onepager(self):
        data = read(self.vj / "cold-reader" / "agent-r06-cmo-a.json")
        self.assertEqual(set(data), {"agent", "rule", "role", "role_name", "page"})
        self.assertEqual(data["role_name"], "CMO")
        page = json.dumps(data["page"])
        self.assertNotIn("Buyers talk about the copper base", page)  # a tab headline, outside the one-pager
        self.assertNotIn("Resellers decide what shoppers pay", page)  # a move title
        self.assertEqual([f["item"] for f in data["page"]["findings"]], ["onepager.f1", "onepager.f2", "onepager.f3"])
        self.assertIn("the full report", data["page"]["way_in"])

    def test_restater_batches_mix_tabs_and_hold_no_trail_ids(self):
        batch = read(self.vj / "cold-reader" / "agent-r10-1-a.json")
        self.assertEqual(len(batch["items"]), 8)
        self.assertEqual({k for it in batch["items"] for k in it}, {"item", "kind", "fields"})
        self.assertEqual(batch["items"][0]["item"], "onepager.headline")
        self.assertEqual(batch["items"][1]["item"], "top.gtm.headline")
        self.assertIn("IEEPA", batch["probe_terms"])

    def test_source_judge_gets_only_sentences_rows_and_quotes(self):
        p = self.packet("source")
        self.assertEqual(set(p) - {"judge", "built", "bundle_sha", "brief", "rules", "verdicts", "expected", "modes",
                                   "exceptions_over", "repeats", "fingerprints", "carried"},
                         {"items", "rows", "evidence"})
        text = json.dumps(p)
        self.assertNotIn("Every first-page listing checked", text)  # no trail reasoning
        self.assertNotIn("Cast iron pots", text)  # no rivals or background
        self.assertNotIn("a chemist who founded", text)
        for item in p["items"]["R19"]:
            self.assertTrue(item["cited"], item["item"])
        self.assertEqual(p["rows"]["w9-c1"]["text"], LEDGER_F1)
        self.assertEqual(p["evidence"]["w9-c1"][-1]["evidence_quote"], QUOTE_F1)

    def test_a_correction_is_the_latest_evidence(self):
        # A row fixed after a "wrong" check must reach the judges as corrected, or they fail sentences that match it.
        write_jsonl(self.run_dir / "verify" / "corrections.jsonl",
                    [{"id": "w9-c1", "action": "corrected", "note": "Count re-read from the saved page."}])
        self.assertEqual(run_script("judges", "prepare", self.run_dir).returncode, 0)
        last = self.packet("source")["evidence"]["w9-c1"][-1]
        self.assertEqual((last["status"], last["verifier"], last["note"]),
                         ("corrected", "correction", "Count re-read from the saved page."))
        self.assertEqual(self.packet("source")["evidence"]["w9-c1"][0]["status"], "confirmed")
        self.assertEqual(self.packet("sceptical-owner")["claims"]["w9-c1"]["status"], "corrected")

    def test_insight_rivals_leave_the_company_out(self):
        p = self.packet("insight")
        self.assertEqual([r["name"] for r in p["rivals"]], [RIVAL, OTHER])
        self.assertEqual(p["closest_rival"], RIVAL)

    def test_owner_persona_comes_from_config_with_a_default(self):
        self.assertEqual(self.packet("sceptical-owner")["persona"], "a chemist who founded the brand")
        cfg = config()
        del cfg["reader"]
        write(self.run_dir / "config.json", cfg)
        self.assertEqual(run_script("judges", "prepare", self.run_dir).returncode, 0)
        self.assertEqual(self.packet("sceptical-owner")["persona"], "the owner of the business")

    def test_owner_sees_claim_basis_and_deep_dive_filter_hits(self):
        p = self.packet("sceptical-owner")
        self.assertEqual(p["claims"]["w9-c1"]["status"], "confirmed")
        blocks = {e["item"]: e for e in p["items"]["R14"]}
        self.assertEqual(blocks["onepager.f3"]["fields"]["value"], "12")  # a bare number still reaches R21
        self.assertEqual(blocks["top.gtm.2"]["fields"]["value"], "70%")
        hits = [e for e in p["items"]["R14"] if e["where"] == "deepdive"]
        self.assertEqual([h["item"] for h in hits], ["deepdive.07-deep-dive.0.s1"])
        self.assertEqual(p["items"]["R21"][0]["item"], "report")

    def test_prepare_archives_the_earlier_round(self):
        write_jsonl(self.vj / "insight" / "verdicts.jsonl", [{"rule": "R07", "item": "onepager.f1", "verdict": "fail"}])
        self.assertEqual(run_script("judges", "prepare", self.run_dir).returncode, 0)
        self.assertFalse((self.vj / "insight" / "verdicts.jsonl").exists())
        self.assertTrue((self.vj / "insight" / "archive-1" / "verdicts.jsonl").exists())

    def test_prepare_refuses_a_run_without_a_onepager(self):
        run = make_run(self.tmp / "other", with_onepager=False)
        res = run_script("judges", "prepare", run)
        self.assertEqual(res.returncode, 2)
        self.assertIn("onepager", res.stderr)


class CollectTests(RunCase):
    def test_complete_rows_pass_every_rule(self):
        res, out = self.full_pass()
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertTrue(out["ok"])
        self.assertEqual(out["malformed"], [])
        self.assertEqual(out["warnings"], [])
        self.assertEqual({k: v["status"] for k, v in out["rules"].items()},
                         dict.fromkeys(["R01", "R06", "R07", "R08", "R09", "R10", "R14", "R19", "R21"], "pass"))
        self.assertEqual(out["rules"]["R06"]["expected"], 12)  # 3 findings x 4 roles
        self.assertEqual(len(out["calls"]["R09"]), 5)

    def test_malformed_rows_are_listed(self):
        judge_all(self.run_dir)
        path = self.vj / "cold-reader" / "verdicts-r06-ceo-a.jsonl"  # the first of the three runs
        lines = path.read_text(encoding="utf-8").splitlines()
        bad_label = json.loads(lines[0])
        bad_label.update(label="so what")  # a failing label with verdict pass
        lines[0] = json.dumps(bad_label)
        lines[1] = "{not json"
        extra = {"rule": "R06", "item": "onepager.f9", "role": "ceo", "label": "sounds right", "verdict": "pass",
                 "quote": "x", "reason": "y"}
        wrong_rule = {"rule": "R19", "item": "onepager.f1.card", "verdict": "pass", "quote": "x", "reason": "y"}
        path.write_text("\n".join(lines + [json.dumps(extra), json.dumps(wrong_rule)]) + "\n", encoding="utf-8")
        res, out = self.collect()
        self.assertEqual(res.returncode, 1)
        found = {(m["line"], m["problem"].split(" ")[0]) for m in out["malformed"]}
        self.assertEqual(len(out["malformed"]), 4, out["malformed"])
        self.assertIn((2, "bad"), found)
        problems = " | ".join(m["problem"] for m in out["malformed"])
        self.assertIn("needs verdict fail", problems)
        self.assertIn("onepager.f9", problems)
        self.assertIn("judged by source", problems)
        self.assertEqual(out["rules"]["R06"]["status"], "fail")
        self.assertIn("onepager.f1 (ceo), 2 of 3 runs", out["rules"]["R06"]["missing"])
        self.assertIn("MALFORMED", res.stdout)

    def test_unknown_fails_a_must_rule(self):
        def tweak(row):
            if row["rule"] == "R07" and row["item"] == "swot.opportunities.1":
                row.update(verdict="unknown", rival=None, reason="Can't tell whether the season is the point.")
            return row
        res, out = self.full_pass(tweak)
        self.assertEqual(res.returncode, 0)  # rows complete and well formed; the rule itself fails
        r07 = out["rules"]["R07"]
        self.assertEqual(r07["status"], "fail")
        self.assertEqual([(f["item"], f["verdict"]) for f in r07["failing"]], [("swot.opportunities.1", "unknown")])
        self.assertTrue(r07["failing"][0]["quote"])

    def test_r10_needs_the_comparison_step(self):
        judge_all(self.run_dir)
        (self.vj / "cold-reader" / "verdicts-compare.jsonl").unlink()
        res, out = self.collect()
        self.assertEqual(res.returncode, 1)
        r10 = out["rules"]["R10"]
        self.assertEqual(r10["status"], "fail")
        self.assertEqual(len(r10["missing"]), 9)
        self.assertTrue(all(m.endswith("(compare)") for m in r10["missing"]))

    def test_packets_from_an_older_bundle_fail(self):
        judge_all(self.run_dir)
        b = read(self.run_dir / "dashboard" / "bundle.json")
        b["prose"]["onepager"]["headline"] = "A rewritten headline about kettle prices"
        write(self.run_dir / "dashboard" / "bundle.json", b)
        res, out = self.collect()
        self.assertEqual(res.returncode, 1)
        self.assertTrue(all(r["status"] == "fail" for r in out["rules"].values()))
        self.assertIn("older bundle", out["rules"]["R19"]["problems"][0])

    def test_compare_pairs_each_restatement_with_what_the_writer_meant(self):
        judge_all(self.run_dir)
        comp = {e["item"]: e for e in read(self.vj / "cold-reader" / "compare-packet.json")["items"]}
        self.assertEqual(comp["onepager.f1"]["meant"]["reasoning"], TRAIL_F1)
        self.assertEqual(comp["onepager.f1"]["restatement"], "A plain restatement of the item.")
        self.assertEqual(comp["top.gtm.1"]["meant"]["reasoning"], TRAIL_GTM)
        self.assertEqual(comp["move.m1.title"]["meant"]["matters"], "Price shoppers compare against the store's own price.")
        self.assertEqual(len(comp["onepager.headline"]["meant"]["cards"]), 3)
        self.assertNotIn("[c:", json.dumps(comp))

    def test_prepare_compare_reports_missing_restatements(self):
        res = run_script("judges", "prepare-compare", self.run_dir)
        self.assertEqual(res.returncode, 1)
        self.assertEqual(len(read(self.vj / "cold-reader" / "compare-packet.json")["missing_restatement"]), 9)


class GateTests(RunCase):
    def test_every_pass_releases(self):
        self.full_pass()
        res, card = self.gate()
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertEqual(card["release"], "pass")
        self.assertFalse((self.run_dir / "HOLD.md").exists())
        self.assertEqual({g["gate"] for g in card["hard_gates"]}, {"finalize", "render test", "model spend", "data spend"})
        self.assertEqual(len(card["rules"]), len(RUBRIC))

    def test_should_rules_never_block(self):
        def tweak(row):
            if row["rule"] == "R09":
                row.update(verdict="fail", call="knew it", system="the order book")
            return row
        self.full_pass(tweak)
        write(self.run_dir / "verify" / "rubric-code.json",
              [{"id": "R02", "level": "must", "status": "pass", "failures": [], "note": ""},
               {"id": "R11", "level": "should", "status": "fail", "failures": ["a 41-word sentence"], "note": ""}])
        res, card = self.gate()
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertEqual(card["release"], "pass")
        self.assertEqual(card["should_failing"], ["R09", "R11"])

    def test_a_must_failure_revises_with_quotes_until_the_round_limit(self):
        def tweak(row):
            if row["rule"] == "R19" and row["item"] == "onepager.f1.so":
                row.update(verdict="fail", support="stretched", stretch="case-to-pattern",
                           quote="Resellers set the marketplace price", reason="One day's check written as a pattern.")
            return row
        self.full_pass(tweak)
        for rnd, code, release in ((0, 3, "revise"), (1, 3, "revise"), (2, 1, "hold")):
            res, card = self.gate("--round", str(rnd))
            self.assertEqual((res.returncode, card["release"]), (code, release), res.stdout)
            self.assertEqual(card["must_failing"], ["R19"])
            self.assertEqual(card["fix"][0]["quote"], "Resellers set the marketplace price")
            self.assertEqual(card["fix"][0]["item"], "onepager.f1.so")
            self.assertEqual((self.run_dir / "HOLD.md").exists(), release == "hold")
        self.assertIn("still fails after 2 fix rounds", " ".join(card["reasons"]))

    def test_a_missing_input_holds(self):
        cases = {
            "finalize": lambda: (self.run_dir / "verify" / "finalize.json").unlink(),
            "judges": lambda: (self.run_dir / "verify" / "judges.json").unlink(),
            "code": lambda: (self.run_dir / "verify" / "rubric-code.json").unlink(),
            "render": lambda: write(self.run_dir / "dashboard" / "screens" / "render-report.md", "Result: **FAIL**\n"),
            "model line": lambda: gate_inputs(self.run_dir, model_usd=None),
            "code row": lambda: write(self.run_dir / "verify" / "rubric-code.json",
                                      [{"id": "R11", "level": "should", "status": "pass", "failures": [], "note": ""}]),
            "unfinished judging": lambda: ((self.vj / "cold-reader" / "verdicts-compare.jsonl").unlink(),
                                           run_script("judges", "collect", self.run_dir),
                                           gate_inputs(self.run_dir)),
        }
        self.full_pass()
        snapshot = self.tmp / "snapshot"
        shutil.copytree(self.run_dir, snapshot)
        for name, damage in cases.items():
            with self.subTest(name):
                shutil.rmtree(self.run_dir)
                shutil.copytree(snapshot, self.run_dir)
                damage()
                res, card = self.gate()
                self.assertEqual((res.returncode, card["release"]), (1, "hold"), res.stdout)
                self.assertTrue((self.run_dir / "HOLD.md").exists())
                if name == "unfinished judging":
                    self.assertIn("judging incomplete: 9 items have no verdict row", " ".join(card["reasons"]))

    def test_judging_an_older_bundle_holds(self):
        self.full_pass()
        b = read(self.run_dir / "dashboard" / "bundle.json")
        b["prose"]["moves"]["items"][0]["title"] = "A rewritten move title"
        write(self.run_dir / "dashboard" / "bundle.json", b)
        res, card = self.gate()
        self.assertEqual(res.returncode, 1)
        self.assertIn("older bundle", " ".join(card["reasons"]))

    def test_spend_over_a_cap_holds(self):
        self.full_pass()
        gate_inputs(self.run_dir, model_usd="41.00")
        res, card = self.gate()
        self.assertEqual(res.returncode, 1)
        model = next(g for g in card["hard_gates"] if g["gate"] == "model spend")
        self.assertEqual((model["ok"], model["spend"], model["cap"]), (False, 41.0, 40.0))

    def test_hold_md_names_the_gate_the_items_and_the_options(self):
        def tweak(row):
            if row["rule"] == "R06" and row["item"] == "onepager.f2" and row["role"] == "cmo":
                row.update(verdict="fail", label="so what", quote="buyer reviews mention the copper base",
                           reason="True, and it changes nothing for marketing.")
            return row
        self.full_pass(tweak)
        (self.run_dir / "verify" / "finalize.json").unlink()
        res, card = self.gate("--round", "2")
        self.assertEqual(res.returncode, 1)
        hold = (self.run_dir / "HOLD.md").read_text(encoding="utf-8")
        self.assertIn(f"the {COMPANY} report was not released", hold)
        self.assertIn("Hard gate failed, finalize", hold)
        self.assertIn("### R06 (must, judge:cold-reader)", hold)
        self.assertIn("Invented test rule: four role readers", hold)
        self.assertIn('`onepager.f2` (role cmo, label so what): "buyer reviews mention the copper base". True, and', hold)
        self.assertIn("**Ship the one-pager only.** Not clean yet. The one-pager itself fails R06 (onepager.f2)", hold)
        self.assertIn("One-pager rewrite, for R06", hold)
        self.assertIn("Close, for finalize", hold)
        self.assertIn("27.60 USD of model use left under the cap of 40.00 USD", hold)
        self.assertIn("**Decline.**", hold)
        self.assertNotIn(EM_DASH, hold)
        # A later run that passes moves the old HOLD.md aside instead of leaving it to mislead.
        gate_inputs(self.run_dir)
        res, card = self.gate("--round", "1")
        self.assertEqual(card["release"], "revise")
        self.assertFalse((self.run_dir / "HOLD.md").exists())
        self.assertEqual(len(list((self.run_dir / "verify" / "holds").glob("HOLD-*.md"))), 1)

    def test_an_unusable_run_exits_2(self):
        res = run_script("gate", self.tmp / "nowhere")
        self.assertEqual(res.returncode, 2)
        (self.run_dir / "run.json").write_text("{broken", encoding="utf-8")
        self.assertEqual(run_script("gate", self.run_dir).returncode, 2)
        self.assertEqual(run_script("judges", "collect", self.tmp / "nowhere").returncode, 2)


class ExceptionsModeTests(RunCase):
    EXTRA = 160  # R14 then holds 177 blocks; every other rule stays under 150

    def test_large_rules_switch_to_failures_plus_a_closing_row(self):
        owner, source = self.packet("sceptical-owner"), self.packet("source")
        self.assertEqual(owner["modes"], {"R09": "every", "R14": "exceptions", "R21": "every"})
        self.assertEqual(len(owner["expected"]["R14"]), 177)
        self.assertEqual(source["modes"], {"R19": "every"})
        res = run_script("judges", "prepare", self.run_dir)
        self.assertIn("R14 177 items, rows only for fail or unknown plus 1 closing row", res.stdout)
        spec = importlib.util.spec_from_file_location("judges_mod", SCRIPTS / "judges.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual([mod.mode_for("R19", 253), mod.mode_for("R19", 150), mod.mode_for("R10", 400),
                          mod.mode_for("R06", 400)], ["exceptions", "every", "every", "every"])

    def test_a_complete_closing_row_passes_unlisted_items(self):
        res, out = self.full_pass()
        self.assertEqual(res.returncode, 0, res.stdout)
        r14 = out["rules"]["R14"]
        self.assertEqual((r14["status"], r14["mode"], r14["expected"], r14["answered"]), ("pass", "exceptions", 177, 177))
        rows = (self.vj / "sceptical-owner" / "verdicts-sceptical-owner-a.jsonl").read_text(encoding="utf-8").count('"R14"')
        self.assertEqual(rows, 1)  # the closing row alone
        res, card = self.gate()
        self.assertEqual((res.returncode, card["release"]), (0, "pass"), res.stdout)

    def test_a_missing_closing_row_holds(self):
        res, out = self.full_pass(closing=lambda rule, n: None)
        self.assertEqual(res.returncode, 1)
        self.assertIn("no closing row for R14", out["rules"]["R14"]["problems"][0])
        self.assertEqual(out["rules"]["R14"]["missing"], [])  # 177 missing items are one problem, not 177 lines
        res, card = self.gate()
        self.assertEqual((res.returncode, card["release"]), (1, "hold"))
        self.assertIn("judging incomplete: no closing row for R14", " ".join(card["reasons"]))

    def test_a_short_read_holds(self):
        res, out = self.full_pass(closing=lambda rule, n: closing_row(rule, n - 1))
        self.assertEqual(res.returncode, 1)
        self.assertIn("read 176, and the packet lists 177 items", out["rules"]["R14"]["problems"][0])
        res, card = self.gate("--round", "0")
        self.assertEqual((res.returncode, card["release"]), (1, "hold"))

    def test_a_fail_row_is_still_reported(self):
        def tweak(row):
            if row["rule"] == "R14" and row["item"] == "move.m2":
                row.update(verdict="fail", flag="a", quote="the store does not", reason="Grades the store team's copy.")
            return row
        res, out = self.full_pass(tweak)
        self.assertEqual(res.returncode, 0, res.stdout)
        r14 = out["rules"]["R14"]
        self.assertEqual(r14["status"], "fail")
        self.assertEqual([(f["item"], f["flag"], f["quote"]) for f in r14["failing"]], [("move.m2", "a", "the store does not")])
        res, card = self.gate()
        self.assertEqual((res.returncode, card["release"]), (3, "revise"))
        self.assertEqual(card["fix"][0]["quote"], "the store does not")

    def test_a_closing_row_on_a_per_item_rule_is_malformed(self):
        judge_all(self.run_dir)
        path = self.vj / "sceptical-owner" / "verdicts-sceptical-owner-a.jsonl"  # a file the packet's agents write
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(closing_row("R09", 5)) + chr(10))
        res, out = self.collect()
        self.assertEqual(res.returncode, 1)
        self.assertIn("R09 wants a row per item", out["malformed"][0]["problem"])

    def test_an_unchanged_round_carries_every_item(self):
        self.full_pass()
        res = run_script("judges", "prepare", self.run_dir)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        owner = self.packet("sceptical-owner")
        self.assertEqual((owner["items"]["R14"], owner["carried"]["R14"]), ([], 177))  # passes under the closing row
        self.assertFalse(owner.get("agents"))
        carried = (self.vj / "sceptical-owner" / "verdicts-carried.jsonl").read_text(encoding="utf-8")
        self.assertEqual(carried.count('"R14"'), 177)
        res, out = self.collect()
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertEqual((out["rules"]["R14"]["status"], out["rules"]["R14"]["answered"]), ("pass", 177))
        self.assertEqual(out["warnings"], [])

    def test_a_judge_following_the_brief_with_one_carried_item_passes(self):
        # Round one: every run passes move.m2 with a row of its own and leaves out the closing row, so only move.m2
        # is decided and carried. Round two lists the other 176 blocks.
        judge_all(self.run_dir, closing=lambda rule, n: None)
        packet = self.packet("sceptical-owner")
        row = good_row("R14", {"item": "move.m2"}, packet_text(packet, "R14", "move.m2"))
        for agent in packet["agents"]:
            with (self.run_dir / agent["writes"]).open("a", encoding="utf-8") as f:
                f.write(json.dumps(row) + chr(10))
        self.assertEqual(run_script("judges", "prepare", self.run_dir).returncode, 0)
        packet = self.packet("sceptical-owner")
        self.assertEqual((len(packet["items"]["R14"]), packet["carried"]["R14"]), (176, 1))
        # The brief: read is the number of items listed for the rule in the judge's own packet.
        res, out = self.full_pass(closing=lambda rule, n: closing_row(rule, len(packet["items"][rule])))
        self.assertEqual(res.returncode, 0, res.stdout)
        r14 = out["rules"]["R14"]
        self.assertEqual((r14["status"], r14["problems"], r14["expected"], r14["answered"], r14["carried"]),
                         ("pass", [], 177, 177, 1))
        # The old brief's count, every block in expected, now names the listed count instead of passing.
        for agent in packet["agents"]:
            path = self.run_dir / agent["writes"]
            path.write_text(path.read_text(encoding="utf-8").replace('"read": 176', '"read": 177'), encoding="utf-8")
        res, out = self.collect()
        self.assertIn("read 177, and the packet lists 176 items", out["rules"]["R14"]["problems"][0])


def edit_bundle(run, change):
    path = run / "dashboard" / "bundle.json"
    data = read(path)
    change(data)
    write(path, data)


def set_label(path, item, label, verdict):
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for r in rows:
        if r["item"] == item:
            r.update(label=label, verdict=verdict)
    write_jsonl(path, rows)


class RoundTests(RunCase):
    """Repeated judges decide by majority, and a fix round judges only what changed."""

    def test_two_of_three_runs_fail_an_item_and_one_does_not(self):
        judge_all(self.run_dir)
        set_label(self.vj / "cold-reader" / "verdicts-r06-cmo-a.jsonl", "onepager.f1", "so what", "fail")
        res, out = self.collect()
        self.assertEqual(out["rules"]["R06"]["status"], "pass", res.stdout)  # one run of three
        set_label(self.vj / "cold-reader" / "verdicts-r06-cmo-b.jsonl", "onepager.f1", "so what", "fail")
        res, out = self.collect()
        r06 = out["rules"]["R06"]
        self.assertEqual(r06["status"], "fail")
        self.assertEqual([(f["item"], f["role"], f["runs"]) for f in r06["failing"]],
                         [("onepager.f1", "cmo", "2 of 3 runs failed it")])

    def test_an_unchanged_round_carries_every_verdict(self):
        self.full_pass()
        res = run_script("judges", "prepare", self.run_dir)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("carried from archive-1", res.stdout)
        for judge in ("source", "insight", "cold-reader", "sceptical-owner"):
            p = self.packet(judge)
            self.assertEqual({k: v for k, v in p["items"].items() if v}, {}, judge)
            self.assertFalse(p.get("agents"), judge)
        res, out = self.collect()  # no judge ran again: the carried rows decide
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertEqual({v["status"] for v in out["rules"].values()}, {"pass"})

    def test_a_carried_fail_stays_failed(self):
        def tweak(row):
            if row["rule"] == "R07" and row["item"] == "swot.opportunities.1":
                row.update(verdict="fail", reason="Any kettle brand sees winter demand.")
            return row
        self.full_pass(tweak)
        run_script("judges", "prepare", self.run_dir)
        res, out = self.collect()
        r07 = out["rules"]["R07"]
        self.assertEqual(r07["status"], "fail")
        self.assertEqual([(f["item"], f["carried_from"]) for f in r07["failing"]], [("swot.opportunities.1", "archive-1")])

    def test_a_changed_line_is_judged_again_and_the_rest_carried(self):
        self.full_pass()
        edit_bundle(self.run_dir, lambda b: b["prose"]["moves"]["items"][1].update(
            matters="Buyers type copper when they search."))
        run_script("judges", "prepare", self.run_dir)
        ins = self.packet("insight")
        self.assertEqual([e["item"] for e in ins["items"]["R08"]], ["move.m2.matters"])
        self.assertEqual(ins["items"]["R07"], [])
        owner = self.packet("sceptical-owner")
        self.assertEqual([e["item"] for e in owner["items"]["R14"]], ["move.m2"])
        self.assertEqual([e["item"] for e in owner["items"]["R21"]], ["report"])  # weighs the whole report again
        self.assertGreater(len(owner["blocks"]), 1)  # so its judge reads every block
        self.assertEqual(len(owner["agents"]), 3)
        cold = self.packet("cold-reader")
        self.assertEqual(cold["items"]["R06"], [])  # the one-pager did not change
        self.assertEqual([e["item"] for e in cold["items"]["R10"]], ["move.m2.title"])  # its meaning includes the line
        self.assertEqual({a["rule"] for a in cold["agents"]}, {"R10"})
        judge_all(self.run_dir)
        res, out = self.collect()
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertEqual({v["status"] for v in out["rules"].values()}, {"pass"})

    def test_a_changed_onepager_sends_every_role_reader_again(self):
        self.full_pass()
        edit_bundle(self.run_dir, lambda b: b["prose"]["onepager"]["findings"][2].update(
            means="A brand search can open a rival's page."))
        run_script("judges", "prepare", self.run_dir)
        cold = self.packet("cold-reader")
        self.assertEqual(len(cold["items"]["R06"]), 3)  # each finding reads in the light of the others
        self.assertEqual(sum(a["rule"] == "R06" for a in cold["agents"]), 12)  # 4 roles, 3 runs each

    def test_a_minority_fail_is_a_warning_and_a_split_item_is_judged_again(self):
        judge_all(self.run_dir)
        cold = self.vj / "cold-reader"
        set_label(cold / "verdicts-r06-cmo-a.jsonl", "onepager.f1", "so what", "fail")  # 1 of 3: passes
        for run in "ab":
            set_label(cold / f"verdicts-r06-ceo-{run}.jsonl", "onepager.f2", "so what", "fail")  # 2 of 3: fails
        res, out = self.collect()
        self.assertEqual([f["item"] for f in out["rules"]["R06"]["failing"]], ["onepager.f2"])
        minority = [w for w in out["warnings"] if "onepager.f1 (cmo)" in w]
        self.assertEqual(len(minority), 1, out["warnings"])
        self.assertIn("R06 onepager.f1 (cmo) passed, but 1 of 3 runs failed it; verdicts-r06-cmo-a.jsonl", minority[0])
        self.assertIn("Invented reason for a test.", minority[0])  # the failing run's quote and reason
        self.assertEqual(run_script("judges", "prepare", self.run_dir).returncode, 0)
        cold_packet = self.packet("cold-reader")
        self.assertEqual([e["item"] for e in cold_packet["items"]["R06"]], ["onepager.f1", "onepager.f2"])
        self.assertEqual(cold_packet["carried"]["R06"], 4)  # onepager.f3, all four roles agreeing

    def test_a_fresh_row_on_a_carried_item_warns_and_the_carried_verdict_stands(self):
        self.full_pass()
        run_script("judges", "prepare", self.run_dir)
        write_jsonl(self.vj / "insight" / "verdicts.jsonl",
                    [{"rule": "R07", "item": "swot.opportunities.1", "verdict": "fail", "rival": RIVAL,
                      "quote": "Kettle searches rise each winter", "reason": "Any kettle brand sees winter demand."}])
        res, out = self.collect()
        self.assertEqual(out["rules"]["R07"]["status"], "pass")
        self.assertEqual([w for w in out["warnings"] if "swot.opportunities.1" in w],
                         ["insight: R07 swot.opportunities.1 was carried from an earlier round, so the new row in "
                          "verdicts.jsonl is ignored and the carried verdict stands"])

    def test_a_stray_verdicts_file_counts_as_no_run(self):
        judge_all(self.run_dir)
        cold = self.vj / "cold-reader"
        set_label(cold / "verdicts-r06-cmo-a.jsonl", "onepager.f1", "so what", "fail")
        shutil.copy(cold / "verdicts-r06-cmo-a.jsonl", cold / "verdicts-retry.jsonl")  # a retry saved on the side
        res, out = self.collect()
        self.assertEqual(out["rules"]["R06"]["status"], "pass", res.stdout)  # still 1 of 3, not 2 of 4
        self.assertIn("verify/judges/cold-reader/verdicts-retry.jsonl is not a file this round's cold-reader agents "
                      "write, so it is ignored and counts as no run", out["warnings"])


class StyleTests(unittest.TestCase):
    FILES = [ROOT / "skill" / "references" / "judges.md", SCRIPTS / "judges.py", SCRIPTS / "gate.py", Path(__file__)]

    def test_no_em_dash_in_these_files(self):
        for f in self.FILES:
            self.assertNotIn(EM_DASH, f.read_text(encoding="utf-8"), f.name)

    def test_judges_md_avoids_negation_reframes(self):
        text = (ROOT / "skill" / "references" / "judges.md").read_text(encoding="utf-8")
        for pattern in (r"(?i)\bit'?s not\b[^.]*\bit'?s\b", r"(?i)\bnot just\b", r"(?i)\bnot only\b",
                        r"(?i)\bisn'?t\b[^.]*\bit'?s\b", r"(?i)\bwas never\b"):
            self.assertIsNone(re.search(pattern, text), pattern)


if __name__ == "__main__":
    unittest.main()
