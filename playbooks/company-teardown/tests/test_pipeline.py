"""Tests for merge_events.py, ledger.py, watch.py and cost_report.py. Run: python -m unittest discover -s tests"""
import argparse, importlib.util, json, os, subprocess, sys, tempfile, time, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent.parent / "skill" / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ledger_mod, merge_mod, watch_mod = load("ledger"), load("merge_events"), load("watch")


def run_script(name, *args):
    return subprocess.run([sys.executable, "-I", str(SCRIPTS / f"{name}.py"), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8")


def event(id, ws_date="2026-01-05", **kw):
    row = {"id": id, "date": ws_date, "date_end": None, "date_precision": "day", "lane": "feature", "kind": "event",
           "title": f"Title {id}", "detail": "Plain detail.", "metric_name": None, "metric_value": None, "metric_unit": None,
           "person": None, "function": None, "basis": "fact", "confidence": "high", "source": f"https://example.com/{id}",
           "source_kind": "primary", "load_bearing": False, "tags": []}
    row.update(kw)
    return row


def metric(id, day, **kw):
    return event(id, f"2026-01-{day:02d}", kind="metric", title="Stars", metric_name="github_stars", metric_value=day,
                 source="https://example.com/stars", **kw)


def claim(id, **kw):
    row = {"id": id, "text": f"Claim {id}", "type": "number", "value": "1", "source": f"https://example.com/{id}",
           "source_kind": "secondary", "basis": "fact", "confidence": "medium", "load_bearing": False}
    row.update(kw)
    return row


def gtm(id, **kw):
    row = dict.fromkeys(("time_utc cta asset_url linked_product views likes reposts replies bookmarks metrics_observed_at "
                         "lift_metric lift_before lift_after lift_window notes").split())
    row.update(id=id, date="2026-02-01", channel="x", actor="founder", format="post", title="Launch post", hook="short hook",
               basis="fact", confidence="high", source="https://example.com/g", source_kind="primary", load_bearing=False)
    row.update(kw)
    return row


def profile(id, **kw):
    row = dict.fromkeys(("name short_name org hq founded overall business_model pricing size revenue traction funding positioning "
                         "positioning_line icp gtm moat weaknesses threat_why partner_shape partner_why gaps").split(), "x")
    row.update(id=id, group="direct", ownership="public", recent_moves=[{"date": "2026-01-01", "event": "x", "source": "u"}],
               scores={"reach": 3}, threat_level="high", partner_level="none", coverage={}, sources=["https://example.com/p"],
               confidence="low")
    row.update(kw)
    return row


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


class RunCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.run_dir = Path(tmp.name) / "teardown-acme"
        (self.run_dir / "research").mkdir(parents=True)
        (self.run_dir / "verify").mkdir()
        (self.run_dir / "config.json").write_text(json.dumps({
            "cutoff": "2026-06-01", "lanes": [{"id": "feature"}, {"id": "funding"}],
            "competition": {"groups": [{"id": "direct"}], "scores": [{"id": "reach"}], "components": []}}), encoding="utf-8")

    def ws(self, name, filename, rows):
        write_jsonl(self.run_dir / "research" / name / filename, rows)

    def read_json(self, rel):
        return json.loads((self.run_dir / rel).read_text(encoding="utf-8"))

    def read_jsonl(self, rel):
        return [json.loads(x) for x in (self.run_dir / rel).read_text(encoding="utf-8").splitlines()]

    def write_ledger(self, rows):
        base = {"origin": "claims", "text": "t", "value": None, "source": "s", "source_kind": "primary", "basis": "fact",
                "confidence": "high", "load_bearing": False, "cited_in": []}
        write_jsonl(self.run_dir / "verify" / "ledger.jsonl", [{**base, **r} for r in rows])


class MergeTests(RunCase):
    def test_validation_failure_reports_every_bad_row_and_writes_nothing(self):
        bad_date = event("w1-2", "2026-13-40")
        bad_lane = event("w1-3", lane="nope")
        no_key = event("w1-4")
        del no_key["detail"]
        self.ws("w1-timeline", "events.jsonl", [event("w1-1"), bad_date, bad_lane, no_key, event("w1-1"), event("w1-5", source=" "),
                                                event("w1-6", confidence=["list"])])
        self.ws("w8-competitors", "profiles.jsonl", [profile("w8-p1", group="ghost", scores={"ghost": 9})])
        with (self.run_dir / "research/w1-timeline/events.jsonl").open("a", encoding="utf-8") as f:
            f.write("{broken\n")
        res = run_script("merge_events", self.run_dir)
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        for expected in ("events.jsonl:2", "events.jsonl:3", "events.jsonl:4", "events.jsonl:5", "events.jsonl:6", "events.jsonl:7",
                         "events.jsonl:8", "profiles.jsonl:1", "already used", "'detail'", "score id 'ghost'"):
            self.assertIn(expected, res.stdout)
        self.assertFalse((self.run_dir / "research/merged").exists())

    def test_force_drops_and_reports(self):
        self.ws("w1-timeline", "events.jsonl", [event("w1-1"), event("w1-2", lane="nope")])
        res = run_script("merge_events", self.run_dir, "--force")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("DROPPED", res.stdout)
        self.assertEqual([e["id"] for e in self.read_json("research/merged/events.json")], ["w1-1"])
        self.assertIn("w1-2", (self.run_dir / "02-coverage.md").read_text(encoding="utf-8").replace("events.jsonl:2", "w1-2"))

    def test_dedupe_keeps_higher_confidence_across_workstreams_only(self):
        a = event("w1-1", title="Series A: raised!", confidence="medium", ws="w1")
        b = event("w2-1", title="series a raised", confidence="high", load_bearing=False, ws="w2")
        c = event("w3-1", title="SERIES A RAISED", confidence="low", load_bearing=True, ws="w3")
        same_ws = event("w2-2", title="Series A raised", confidence="low", ws="w2")
        other_day = event("w3-2", "2026-01-06", title="Series A raised", ws="w3")
        kept, merged = merge_mod.dedupe([a, b, c, same_ws, other_day])
        ids = {r["id"] for r in kept}
        self.assertEqual(ids, {"w2-1", "w2-2", "w3-2"})
        self.assertCountEqual(b["tags"], ["merged:w1-1", "merged:w3-1"])
        self.assertTrue(b["load_bearing"], "a load-bearing flag must survive the merge")
        self.assertEqual(sum(merged.values()), 2)

    def test_differing_metric_readings_stay_apart(self):
        kept, _ = merge_mod.dedupe([metric("w3-1", 1), metric("w2-1", 1, tags=[]) | {"metric_value": 99}])
        self.assertEqual(len(kept), 2)

    def test_outputs_and_coverage(self):
        self.ws("w1-timeline", "events.jsonl", [event("w1-1", basis="inference", confidence="low"), metric("w1-2", 2)])
        self.ws("w1-timeline", "progress.jsonl", [{"ts": "2026-01-01T10:00:00Z", "item": "x", "n": 1, "rows": 2}])
        self.ws("w7-gtm", "gtm_actions.jsonl", [gtm("w7-1")])
        self.ws("w8-competitors", "profiles.jsonl", [profile("w8-p1")])
        self.ws("w8-competitors", "landscape.jsonl", [{"id": "w8-l1", "name": "n", "org": "o", "group": "direct", "what": "w",
                                                       "url": "u", "why_listed": "y", "source": "s", "confidence": "high"}])
        (self.run_dir / "probe.json").write_text(json.dumps({"expected_rows": 50}), encoding="utf-8")
        res = run_script("merge_events", self.run_dir)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        for name, n in (("events", 1), ("metrics", 1), ("gtm", 1), ("competitors", 1), ("landscape", 1)):
            self.assertEqual(len(self.read_json(f"research/merged/{name}.json")), n, name)
        cov = (self.run_dir / "02-coverage.md").read_text(encoding="utf-8")
        for expected in ("2026-01-01T10:00:00Z", "w1-1, w8-p1", "funding", "expected 50, found 5"):
            self.assertIn(expected, cov)
        self.assertRegex(cov, r"no progress.jsonl\s+w7-gtm, w8-competitors")

    def test_missing_config_fails_loudly(self):
        (self.run_dir / "config.json").unlink()
        self.ws("w1-timeline", "events.jsonl", [event("w1-1")])
        res = run_script("merge_events", self.run_dir)
        self.assertEqual(res.returncode, 2)
        self.assertIn("config.json", res.stderr)

    def test_utf8_bom_and_crlf_tolerated(self):
        path = self.run_dir / "research/w1-timeline/events.jsonl"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"\xef\xbb\xbf" + json.dumps(event("w1-1", title="Café launch"), ensure_ascii=False).encode() + b"\r\n")
        res = run_script("merge_events", self.run_dir)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(self.read_json("research/merged/events.json")[0]["title"], "Café launch")


class LedgerBuildTests(RunCase):
    def build(self):
        self.ws("w1-timeline", "events.jsonl", [event("w1-1"), event("w1-2", basis="inference", detail="SECRET REASONING rests on w1-1")])
        self.ws("w3-traction", "events.jsonl", [metric(f"w3-{d}", d) for d in range(1, 26)] + [metric("w3-26", 26, load_bearing=True)])
        self.ws("w3-traction", "claims.jsonl", [claim("w3-c1")])
        self.ws("w7-gtm", "gtm_actions.jsonl", [gtm("w7-1", notes="SECRET NOTE")])
        res = run_script("merge_events", self.run_dir)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        res = run_script("ledger", "merge", self.run_dir)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_series_counts_once_and_notes_size(self):
        self.build()
        rows = self.read_jsonl("verify/ledger.jsonl")
        series = [r for r in rows if r.get("series_size")]
        self.assertEqual(len(series), 1)
        self.assertEqual(series[0]["series_size"], 26)
        self.assertIn("26", series[0]["note"])
        self.assertIn("w3-26", {r["id"] for r in rows}, "a load-bearing point stays its own row")
        self.assertEqual(len(rows), 2 + 2 + 1 + 1)
        self.assertEqual({r["origin"] for r in rows}, {"events", "gtm", "claims"})

    def test_mark_resolves_series_points_merged_ids_and_reports_unknown(self):
        self.build()
        hidden = next(r for r in self.read_jsonl("verify/ledger.jsonl") if r.get("series_size"))["series_ids"][0]
        (self.run_dir / "03-overview.md").write_text(
            f"# Heading 2026\nStars hit 5 [c:{hidden}]. Revenue was 7 million. No digits here.\n\nBad ref [c:w9-9].\n", encoding="utf-8")
        (self.run_dir / "dashboard").mkdir()
        (self.run_dir / "dashboard/prose.json").write_text(json.dumps({"so_what": [{"heading": "h", "body": "See {{stat:w2}} [c:w1-1]"}]}), encoding="utf-8")
        res = run_script("ledger", "mark", self.run_dir)
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertIn("[c:w9-9]", res.stdout)
        self.assertIn("Revenue was 7 million", res.stdout)
        self.assertNotIn("Heading 2026", res.stdout)
        self.assertNotIn("stat:w2", res.stdout)
        rows = {r["id"]: r for r in self.read_jsonl("verify/ledger.jsonl")}
        self.assertTrue(rows[hidden]["load_bearing"], "a cited series point becomes its own row")
        self.assertEqual(rows[hidden]["cited_in"], ["03-overview.md"])
        self.assertEqual(rows["w1-1"]["cited_in"], ["dashboard/prose.json"])

    def test_merged_alias_citation_lands_on_kept_row(self):
        self.ws("w1-timeline", "events.jsonl", [event("w1-1", title="Same", confidence="high")])
        self.ws("w2-economics", "events.jsonl", [event("w2-1", title="Same", confidence="low")])
        run_script("merge_events", self.run_dir)
        run_script("ledger", "merge", self.run_dir)
        (self.run_dir / "04-so-what.md").write_text("Claim [c:w2-1].\n", encoding="utf-8")
        self.assertEqual(run_script("ledger", "mark", self.run_dir).returncode, 0)
        rows = self.read_jsonl("verify/ledger.jsonl")
        self.assertEqual([(r["id"], r["load_bearing"]) for r in rows], [("w1-1", True)])

    def test_split_batches_are_blind(self):
        self.build()
        self.assertEqual(run_script("ledger", "sample", self.run_dir, "--seed", 1, "--min", 100).returncode, 0)
        res = run_script("ledger", "split", self.run_dir, "--verifiers", 3)
        self.assertEqual(res.returncode, 0, res.stderr)
        seen = []
        for i in (1, 2, 3):
            text = (self.run_dir / f"verify/batch-v{i}.jsonl").read_text(encoding="utf-8")
            self.assertNotIn("SECRET", text)
            for row in map(json.loads, text.splitlines()):
                self.assertEqual(set(row), {"id", "text", "value", "source"})
                seen.append(row["id"])
        self.assertEqual(sorted(seen), sorted(r["id"] for r in self.read_jsonl("verify/sample.jsonl")))
        self.assertEqual(len(seen), len(set(seen)))

    def test_end_to_end_from_rows_to_citation_gate(self):
        self.build()
        (self.run_dir / "03-overview.md").write_text("Launch happened [c:w1-1]. Claim [c:w3-c1].\n", encoding="utf-8")
        self.assertEqual(run_script("ledger", "mark", self.run_dir).returncode, 0)
        self.assertEqual(run_script("ledger", "sample", self.run_dir, "--seed", 3).returncode, 0)
        self.assertEqual(run_script("ledger", "split", self.run_dir).returncode, 0)
        self.assertEqual(run_script("ledger", "check-citations", self.run_dir).returncode, 1)
        ids = [r["id"] for i in (1, 2, 3) for r in self.read_jsonl(f"verify/batch-v{i}.jsonl")]
        write_jsonl(self.run_dir / "verify/verdicts.jsonl", [
            {"id": i, "status": "confirmed", "evidence_quote": "q", "checked_url": "u", "note": "", "verifier": "v1"} for i in ids])
        self.assertEqual(run_script("ledger", "check-citations", self.run_dir).returncode, 0)
        self.assertEqual(run_script("ledger", "report", self.run_dir).returncode, 0)
        report = self.read_json("verify/report.json")
        self.assertEqual(report["load_bearing_checked"], 3)
        self.assertIn("Sample too small", " ".join(report["findings"]))

    def test_delta_lists_new_load_bearing_without_verdict(self):
        self.write_ledger([{"id": "a", "ws": "w1", "load_bearing": True}, {"id": "b", "ws": "w1", "load_bearing": True}, {"id": "c", "ws": "w1"}])
        write_jsonl(self.run_dir / "verify/verdicts.jsonl", [{"id": "a", "status": "confirmed", "evidence_quote": "", "checked_url": "", "note": "", "verifier": "v1"}])
        self.assertEqual(run_script("ledger", "delta", self.run_dir).returncode, 0)
        self.assertEqual([r["id"] for r in self.read_jsonl("verify/batch-delta.jsonl")], ["b"])


class SampleTests(RunCase):
    def population(self):
        rows = []
        for i in range(600):
            rows.append({"id": f"a{i:04d}", "ws": "w1-timeline", "source_kind": "primary"})
        for i in range(300):
            rows.append({"id": f"b{i:04d}", "ws": "w2-economics", "source_kind": "secondary"})
        for i in range(97):
            rows.append({"id": f"c{i:04d}", "ws": "w2-economics", "source_kind": "aggregator"})
        rows += [{"id": "d0001", "ws": "w4-legal", "source_kind": "aggregator"},
                 {"id": "lb1", "ws": "w4-legal", "source_kind": "primary", "load_bearing": True},
                 {"id": "low1", "ws": "w4-legal", "source_kind": "aggregator", "cited_in": ["03-overview.md"]},
                 {"id": "low2", "ws": "w4-legal", "source_kind": "secondary", "confidence": "low", "load_bearing": True}]
        return rows

    def sample(self, seed, *extra):
        res = run_script("ledger", "sample", self.run_dir, "--seed", seed, *extra)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        return (self.run_dir / "verify/sample.jsonl").read_bytes()

    def test_deterministic_for_seed_and_varies_between_seeds(self):
        self.write_ledger(self.population())
        first = self.sample(7)
        self.assertEqual(first, self.sample(7))
        self.assertNotEqual(first, self.sample(8))

    def test_deterministic_whatever_the_ledger_order(self):
        rows = self.population()
        self.write_ledger(rows)
        first = self.sample(7)
        self.write_ledger(list(reversed(rows)))
        self.assertEqual(first, self.sample(7))

    def test_strata_and_proportions(self):
        self.write_ledger(self.population())
        (self.run_dir / "research/w4-legal").mkdir(parents=True)
        (self.run_dir / "research/w4-legal/section.md").write_text("Cited [c:low1].", encoding="utf-8")
        self.sample(7)
        rows = self.read_jsonl("verify/sample.jsonl")
        by_id = {r["id"]: r for r in rows}
        self.assertEqual(by_id["lb1"]["stratum"], "load_bearing")
        self.assertEqual(by_id["low2"]["stratum"], "low_or_aggregator")
        self.assertEqual(by_id["low1"]["stratum"], "low_or_aggregator")
        drawn = [r for r in rows if r["in_random"]]
        self.assertTrue(all(r["stratum"] == "random" for r in drawn))
        self.assertEqual(len(drawn), 100)  # remainder 998: 5 percent is 50, so the min of 100 applies
        meta = self.read_json("verify/sample-meta.json")
        self.assertEqual(meta["seed"], 7)
        self.assertEqual(meta["strata"], {"load_bearing": 1, "low_or_aggregator": 2, "random": 100})
        counts = {k: v["drawn"] for k, v in meta["random_strata"].items()}
        self.assertEqual(counts["w4-legal|aggregator"], 1, "a stratum of one still gets one")
        self.assertAlmostEqual(counts["w1-timeline|primary"], 60, delta=1)
        self.assertAlmostEqual(counts["w2-economics|secondary"], 30, delta=1)
        self.assertAlmostEqual(counts["w2-economics|aggregator"], 10, delta=1)
        self.assertEqual(sum(counts.values()), 100)

    def test_rate_can_exceed_min_and_min_is_capped_at_remainder(self):
        self.write_ledger(self.population())
        self.sample(1, "--rate", "0.2")
        self.assertEqual(self.read_json("verify/sample-meta.json")["strata"]["random"], 200)
        self.write_ledger([{"id": f"x{i}", "ws": "w1", "source_kind": "primary"} for i in range(40)])
        self.sample(1)
        self.assertEqual(self.read_json("verify/sample-meta.json")["strata"]["random"], 40)

    def test_allocate_gives_each_stratum_one_even_when_target_is_smaller(self):
        self.assertEqual(ledger_mod.allocate({"a": 5, "b": 5, "c": 5}, 2), {"a": 1, "b": 1, "c": 1})


class SmallSampleLabelTests(unittest.TestCase):
    def test_small_clean_sample_cannot_earn_the_top_label(self):
        src = (SCRIPTS / "ledger.py").read_text(encoding="utf-8")
        self.assertIn("0 < len(judged) < 30 and label == ACCURATE", src)


class CampaignImpactTests(unittest.TestCase):
    """The study must find a planted lift, stay quiet on noise, and refuse to read a category shock."""

    def weeks(self, n=300):
        start = datetime(2020, 1, 6)
        return [(start + timedelta(days=7 * i)).strftime("%Y-%m-%d") for i in range(n)]

    def wave(self, i, seed):
        return 50 + 3 * ((i * seed) % 7) / 7 + (i % 52) / 26

    def build(self, own_fn, ctrl_fn=None, campaigns=None):
        ci = load("campaign_impact")
        days = self.weeks()
        own = [[d, own_fn(i)] for i, d in enumerate(days)]
        controls = {f"c{k}": [[d, (ctrl_fn or self.wave)(i, k + 3)] for i, d in enumerate(days)] for k in range(3)}
        spec = {"campaigns": campaigns or [{"id": "a", "name": "A", "type": "launch", "start": days[200]}],
                "metrics": [{"id": "search", "label": "Search", "unit": "index", "cadence": "weekly", "pulls": [{"own": own, "controls": controls}]}]}
        rows, series, summary = ci.study(spec)
        return rows, series, summary

    def test_quiet_series_stays_within_noise(self):
        rows, _, _ = self.build(lambda i: self.wave(i, 5))
        self.assertEqual(rows[0]["verdict"], "within noise")

    def test_planted_lift_is_above_noise(self):
        rows, _, _ = self.build(lambda i: self.wave(i, 5) * (1.8 if 200 <= i < 208 else 1))
        self.assertEqual(rows[0]["verdict"], "above noise")
        self.assertGreater(rows[0]["net_pct"], rows[0]["noise_band_pct"])

    def test_category_shock_is_not_measurable(self):
        rows, _, _ = self.build(lambda i: self.wave(i, 5) * (2 if 200 <= i < 208 else 1), lambda i, k: self.wave(i, k) * (2 if 200 <= i < 208 else 1))
        self.assertEqual(rows[0]["verdict"], "not measurable")
        self.assertIn("category shock", rows[0]["verdict_reason"])

    def test_year_precision_is_not_measurable(self):
        days = self.weeks()
        rows, _, _ = self.build(lambda i: self.wave(i, 5), campaigns=[{"id": "a", "name": "A", "type": "t", "start": days[200], "precision": "year"}])
        self.assertEqual(rows[0]["verdict"], "not measurable")

    def test_overlaps_are_flagged(self):
        days = self.weeks()
        rows, _, _ = self.build(lambda i: self.wave(i, 5), campaigns=[{"id": "a", "name": "A", "type": "t", "start": days[200]}, {"id": "b", "name": "B", "type": "t", "start": days[202]}])
        self.assertEqual(rows[0]["overlaps"], ["b"])

    def test_summary_states_chance(self):
        _, _, summary = self.build(lambda i: self.wave(i, 5))
        self.assertEqual(summary["tested"], 1)
        self.assertEqual(summary["expected_each_tail_by_chance"], 0.1)

    def test_percentile_matches_linear_rule(self):
        ci = load("campaign_impact")
        self.assertEqual(ci.percentile([1, 2, 3, 4, 5], 50), 3)
        self.assertAlmostEqual(ci.percentile([1, 2, 3, 4], 5), 1.15)


class CostReportVerifierTests(unittest.TestCase):
    def test_verifier_calls_are_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            row = dict(ts="2026-01-01T00:00:00Z", ws="w1", endpoint="a.b", provider_served="a", price=0.5, purpose="p", status=200, hit=True, claim_ids=[])
            write_jsonl(run / "research" / "w1" / "calls.jsonl", [row])
            write_jsonl(run / "verify" / "raw-v1" / "calls.jsonl", [dict(row, ws="verify", price=0.25)])
            rows, _ = load("cost_report").read_calls(run)
            self.assertAlmostEqual(sum(r["price"] for r in rows), 0.75)


class MovesValidationTests(unittest.TestCase):
    """prose.moves is what the reader acts on, so an incomplete move must fail the build."""

    def good(self):
        q = [{"point": "p", "so_what": "s", "evidence": "thin", "kind": "Measured"}]
        return {"moves": {"answer": {"body": "do this"},
                          "headlines": [{"value": "1", "label": "x", "kind": "Measured"}] * 3,
                          "rules": [{"if": "a", "then": "b"}],
                          "data_request": [{"data": "d", "holder": "h", "decides": "x"}],
                          "opportunities": [{"title": "t", "evidence": "e", "proof": "p"}],
                          "working": [{"title": "t", "evidence": "e", "proof": "p"}],
                          "not_working": [{"title": "t", "evidence": "e", "proof": "p", "moves": ["m1"]}],
                          "swot": {"strengths": q, "weaknesses": q, "opportunities": q, "threats": q},
                          "crossings": [{"pair": "S x O", "text": "t", "moves": ["m1"]}],
                          "items": [{"id": "m%d" % n, "priority": True, "trigger": "if x", "short": "s", "channel": "c", "when": "now", "depends": "none", "type": "quick_win", "title": "t", "what": "w", "why": "y", "impact": 4, "effort": 1,
                                     "confidence": "low", "if_wrong": "x", "test": "t", "watch": "n"} for n in range(1, 6)]}}

    def problems(self, prose):
        bd = load("build_dashboard")
        out = []
        bd.check_moves(prose, set(), None, out)
        bd.check_insights(prose, {}, None, out)
        return out

    def test_ai_tab_needs_a_body_and_complete_findings(self):
        p = self.good()
        p["ai"] = {"body": "", "parts": [{"id": "offsite", "findings": [{"title": "t", "found": "f"}]}], "uses": {"items": [{"title": "u", "effort": 1}]}}
        got = "\n".join(self.problems(p))
        self.assertIn("prose.ai: body is required", got)
        self.assertIn("a finding needs matters", got)
        self.assertIn("needs impact", got)

    def test_ai_tab_passes_when_complete(self):
        p = self.good()
        p["ai"] = {"body": "b", "parts": [{"id": "offsite", "findings": [{"title": "t", "found": "f", "matters": "m"}]}], "uses": {"items": [{"title": "u", "effort": 1, "impact": 2, "evidence": "thin"}]}}
        self.assertEqual(self.problems(p), [])

    def test_top_of_tab_rules(self):
        p = self.good()
        p["top"] = {"sowhat": {"headline": "h", "points": [{"value": "24 of 24", "label": "listings", "kind": "Measured", "viz": {"type": "pie"}}]}, "nope": {"headline": "h"}}
        got = "\n".join(self.problems(p))
        self.assertIn("nope is not a tab", got)
        self.assertIn("unknown viz pie", got)
        self.assertIn("a number needs a citation", got)

    def test_method_points_need_no_citation(self):
        p = self.good()
        p["top"] = {"sowhat": {"headline": "h", "points": [{"value": "6.4%", "label": "estimated wrong", "kind": "Method"}]}}
        self.assertEqual(self.problems(p), [])

    def test_good_moves_pass(self):
        self.assertEqual(self.problems(self.good()), [])

    def test_addressing_the_reader_fails(self):
        p = self.good()
        p["moves"]["answer"]["body"] = "Your team should do this"
        self.assertTrue(any("descriptive" in x for x in self.problems(p)))

    def test_too_few_headlines_fails(self):
        p = self.good()
        p["moves"]["headlines"] = []
        self.assertTrue(any("headlines" in x for x in self.problems(p)))

    def test_priority_move_needs_a_trigger(self):
        p = self.good()
        del p["moves"]["items"][0]["trigger"]
        self.assertTrue(any("trigger" in x for x in self.problems(p)))

    def test_so_what_needs_opportunities(self):
        p = self.good()
        del p["moves"]["opportunities"]
        self.assertTrue(any("opportunities" in x for x in self.problems(p)))

    def test_insight_needs_a_use(self):
        p = self.good()
        p["gtm"] = {"insights": {"lenses": [{"id": "a", "working": [{"title": "t", "evidence": "e", "proof": "p"}]}]}}
        self.assertTrue(any("how a team" in x for x in self.problems(p)))

    def test_prescriptive_wording_fails(self):
        p = self.good()
        p["moves"]["answer"]["body"] = "Written for the owner: the first job for the company is this"
        self.assertTrue(any("instruction" in x for x in self.problems(p)))

    def test_old_runs_without_moves_pass(self):
        self.assertEqual(self.problems({}), [])

    def test_missing_test_field_fails(self):
        p = self.good()
        del p["moves"]["items"][0]["test"]
        self.assertTrue(any("test is required" in x for x in self.problems(p)))

    def test_budget_move_needs_from_and_to(self):
        p = self.good()
        p["moves"]["items"][0]["type"] = "budget"
        self.assertTrue(any("from and to" in x for x in self.problems(p)))

    def test_score_must_be_one_to_five(self):
        p = self.good()
        p["moves"]["items"][0]["impact"] = 9
        self.assertTrue(any("whole number" in x for x in self.problems(p)))

    def test_empty_swot_quadrant_fails(self):
        p = self.good()
        p["moves"]["swot"]["threats"] = []
        self.assertTrue(any("threats is empty" in x for x in self.problems(p)))

    def test_crossing_to_missing_move_fails(self):
        p = self.good()
        p["moves"]["crossings"][0]["moves"] = ["m9"]
        self.assertTrue(any("m9 does not exist" in x for x in self.problems(p)))

    def test_band_on_unknown_tab_fails(self):
        self.assertTrue(any("not a tab" in x for x in self.problems({"bands": {"nope": "x"}})))


class ClopperPearsonTests(unittest.TestCase):
    def test_published_values(self):
        cp = ledger_mod.clopper_pearson
        self.assertAlmostEqual(cp(0, 40)[1], 0.0881, places=3)
        self.assertAlmostEqual(cp(1, 40)[1], 0.1316, places=3)
        self.assertAlmostEqual(cp(3, 100)[1], 0.0852, places=3)
        self.assertEqual(cp(0, 40)[0], 0.0)
        self.assertAlmostEqual(cp(1, 40)[0], 0.00063, places=4)
        self.assertAlmostEqual(cp(3, 100)[0], 0.00623, places=4)
        self.assertEqual(cp(5, 5)[1], 1.0)
        self.assertEqual(cp(0, 0), (0.0, 1.0))

    def test_large_sample_does_not_overflow(self):
        low, high = ledger_mod.clopper_pearson(60, 3000)
        self.assertTrue(low < 0.02 < high)


class ReportTests(RunCase):
    def setup_verdicts(self, n, wrong_by_ws, statuses=None, lb=(), corrections=(), per_ws=None):
        """Build n random rows spread over workstreams; wrong_by_ws says how many are wrong in each."""
        per_ws = per_ws or {"w1-timeline": n}
        rows, sample, verdicts, i = [], [], [], 0
        for ws, count in per_ws.items():
            for j in range(count):
                rid = f"r{i:04d}"
                i += 1
                rows.append({"id": rid, "ws": ws})
                sample.append({"id": rid, "ws": ws, "in_random": True, "stratum": "random"})
                status = "wrong" if j < wrong_by_ws.get(ws, 0) else "confirmed"
                verdicts.append({"id": rid, "status": status, "evidence_quote": "", "checked_url": "", "note": "", "verifier": "v1"})
        for rid, status in lb:
            rows.append({"id": rid, "ws": "w1-timeline", "load_bearing": True})
            sample.append({"id": rid, "ws": "w1-timeline", "in_random": False, "stratum": "load_bearing"})
            if status:
                verdicts.append({"id": rid, "status": status, "evidence_quote": "", "checked_url": "", "note": "", "verifier": "v1"})
        for rid, status in statuses or ():
            rows.append({"id": rid, "ws": "w1-timeline"})
            sample.append({"id": rid, "ws": "w1-timeline", "in_random": True, "stratum": "random"})
            verdicts.append({"id": rid, "status": status, "evidence_quote": "", "checked_url": "", "note": "", "verifier": "v1"})
        self.write_ledger(rows)
        write_jsonl(self.run_dir / "verify/sample.jsonl", sample)
        write_jsonl(self.run_dir / "verify/verdicts.jsonl", verdicts)
        if corrections:
            write_jsonl(self.run_dir / "verify/corrections.jsonl", [{"id": c, "action": "corrected", "note": "fixed"} for c in corrections])

    def add_unsampled(self, ws, n=5):
        """Leave rows outside the sample, so a second draw from this workstream is still possible."""
        rows = [json.loads(l) for l in (self.run_dir / "verify/ledger.jsonl").read_text(encoding="utf-8").splitlines()]
        self.write_ledger(rows + [{"id": f"u{i}", "ws": ws} for i in range(n)])

    def report(self):
        res = run_script("ledger", "report", self.run_dir)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        return self.read_json("verify/report.json"), (self.run_dir / "verify/report.md").read_text(encoding="utf-8")

    def test_three_percent_is_accurate(self):
        self.setup_verdicts(100, {"w1-timeline": 3})
        data, md = self.report()
        self.assertEqual(data["label"], "ACCURATE TO SOURCES")
        self.assertAlmostEqual(data["wrong_rate"], 0.03)
        self.assertAlmostEqual(data["interval_high"], 0.0852, places=3)
        self.assertEqual(data["cutoff"], "2026-06-01")
        self.assertIn("95 of 100", md)
        for field in ("claims_total", "load_bearing_checked", "load_bearing_wrong_open", "random_checked", "interval_low", "unreachable", "per_workstream"):
            self.assertIn(field, data)

    def test_between_three_and_six_asks_for_second_sample_on_worst(self):
        self.setup_verdicts(100, {"w1-timeline": 1, "w2-economics": 3}, per_ws={"w1-timeline": 40, "w2-economics": 60})
        self.add_unsampled("w2-economics")
        data, md = self.report()
        self.assertEqual(data["label"], "SECOND SAMPLE NEEDED")
        self.assertIn("second sample on the worst workstream, w2-economics", md)

    def test_six_percent_exactly_is_not_directional(self):
        self.setup_verdicts(100, {"w1-timeline": 6})
        self.add_unsampled("w1-timeline")
        self.assertEqual(self.report()[0]["label"], "SECOND SAMPLE NEEDED")

    def test_worst_workstream_checked_in_full_needs_no_second_sample(self):
        self.setup_verdicts(100, {"w1-timeline": 1, "w2-economics": 3}, per_ws={"w1-timeline": 40, "w2-economics": 60})
        data, md = self.report()
        self.assertEqual(data["label"], "ACCURATE TO SOURCES")
        self.assertIn("checked in full", md)

    def test_over_six_in_one_workstream_makes_overall_directional(self):
        self.setup_verdicts(100, {"w2-economics": 2}, per_ws={"w1-timeline": 80, "w2-economics": 20})
        data, _ = self.report()
        self.assertEqual(data["per_workstream"]["w2-economics"]["label"], "DIRECTIONAL ONLY")
        self.assertEqual(data["per_workstream"]["w2-economics"]["wrong"], 2)
        self.assertEqual(data["per_workstream"]["w1-timeline"]["label"], "ACCURATE TO SOURCES")
        self.assertEqual(data["label"], "DIRECTIONAL ONLY")

    def test_small_workstream_is_too_few_to_rate_and_does_not_flip_overall(self):
        self.setup_verdicts(100, {"w2-economics": 1}, per_ws={"w1-timeline": 90, "w2-economics": 10})
        data, md = self.report()
        self.assertEqual(data["per_workstream"]["w2-economics"]["label"], "TOO FEW TO RATE")
        self.assertEqual(data["label"], "ACCURATE TO SOURCES")
        self.assertIn("Too few random checks", md)

    def test_second_sample_counts_for_workstream_only_and_resolves_the_label(self):
        self.setup_verdicts(100, {"w1-timeline": 1, "w2-economics": 3}, per_ws={"w1-timeline": 40, "w2-economics": 60})
        ledger = (self.run_dir / "verify/ledger.jsonl").read_text(encoding="utf-8")
        self.write_ledger([json.loads(l) for l in ledger.splitlines()] + [{"id": f"s{i}", "ws": "w2-economics"} for i in range(40)])
        with open(self.run_dir / "verify/sample.jsonl", "a", encoding="utf-8") as f:
            for i in range(40):
                f.write(json.dumps({"id": f"s{i}", "ws": "w2-economics", "in_random": False, "stratum": "second_sample"}) + "\n")
        with open(self.run_dir / "verify/verdicts.jsonl", "a", encoding="utf-8") as f:
            for i in range(40):
                f.write(json.dumps({"id": f"s{i}", "status": "confirmed", "evidence_quote": "", "checked_url": "", "note": "", "verifier": "v1"}) + "\n")
        data, _ = self.report()
        self.assertEqual(data["random_checked"], 100)
        self.assertAlmostEqual(data["wrong_rate"], 0.04)
        self.assertEqual(data["per_workstream"]["w2-economics"]["checked"], 100)
        self.assertEqual(data["label"], "ACCURATE TO SOURCES")

    def test_open_load_bearing_wrong_beats_everything_until_corrected(self):
        self.setup_verdicts(50, {}, lb=[("lb1", "wrong")])
        data, _ = self.report()
        self.assertEqual((data["label"], data["load_bearing_wrong_open"]), ("NOT RELIABLE YET", 1))
        write_jsonl(self.run_dir / "verify/corrections.jsonl", [{"id": "lb1", "action": "corrected", "note": "fixed"}])
        data, _ = self.report()
        self.assertEqual((data["label"], data["load_bearing_wrong_open"]), ("ACCURATE TO SOURCES", 0))

    def test_unsupported_counts_as_wrong_partly_apart_unreachable_named(self):
        self.setup_verdicts(30, {}, statuses=[("u1", "unsupported"), ("p1", "partly")] + [(f"x{i}", "unreachable") for i in range(9)])
        data, md = self.report()
        self.assertEqual(data["random_checked"], 32)
        self.assertAlmostEqual(data["wrong_rate"], 1 / 32)
        self.assertEqual(data["partly"], 1)
        self.assertEqual(data["unreachable"], 9)
        self.assertAlmostEqual(data["unreachable_share"], 9 / 41)
        self.assertIn("above the 15% limit", md)

    def test_small_sample_is_stated(self):
        self.setup_verdicts(29, {})
        self.assertIn("Sample too small", self.report()[1])

    def test_load_bearing_without_verdict_is_not_reliable(self):
        self.setup_verdicts(40, {}, lb=[("lb1", None)])
        data, md = self.report()
        self.assertEqual(data["label"], "NOT RELIABLE YET")
        self.assertIn("lb1", md)

    def test_verdict_on_unknown_id_fails(self):
        self.setup_verdicts(5, {})
        with (self.run_dir / "verify/verdicts.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "ghost", "status": "confirmed", "evidence_quote": "", "checked_url": "", "note": "", "verifier": "v1"}) + "\n")
        res = run_script("ledger", "report", self.run_dir)
        self.assertEqual(res.returncode, 2)
        self.assertIn("ghost", res.stderr)

    def test_check_citations(self):
        self.write_ledger([{"id": i, "ws": "w1"} for i in ("ok", "part", "bad", "fixed", "gone", "none")])
        v = lambda i, s: {"id": i, "status": s, "evidence_quote": "", "checked_url": "", "note": "", "verifier": "v1"}
        write_jsonl(self.run_dir / "verify/verdicts.jsonl", [v("ok", "confirmed"), v("part", "partly"), v("bad", "wrong"), v("fixed", "wrong"), v("gone", "wrong")])
        write_jsonl(self.run_dir / "verify/corrections.jsonl", [{"id": "fixed", "action": "corrected", "note": ""}, {"id": "gone", "action": "removed", "note": ""}])
        doc = self.run_dir / "03-overview.md"
        doc.write_text("[c:ok] [c:part] [c:fixed]", encoding="utf-8")
        self.assertEqual(run_script("ledger", "check-citations", self.run_dir).returncode, 0)
        doc.write_text("[c:ok] [c:bad] [c:gone] [c:none] [c:ghost]", encoding="utf-8")
        res = run_script("ledger", "check-citations", self.run_dir)
        self.assertEqual(res.returncode, 1)
        for cid in ("bad", "gone", "none", "ghost"):
            self.assertIn(f"[c:{cid}]", res.stdout)
        self.assertNotIn("[c:ok]", res.stdout)

    def test_run_dir_first_argument_order_also_works(self):
        self.setup_verdicts(5, {})
        self.assertEqual(run_script("ledger", self.run_dir, "report").returncode, 0)


class WatchTests(RunCase):
    def setup_ws(self, **workstreams):
        """Each value: (age of progress.jsonl in minutes or None, minutes since start, resumes)."""
        meta = {}
        for ws, (progress_age, since_start, resumes) in workstreams.items():
            started = datetime.now(timezone.utc) - timedelta(minutes=since_start)
            meta[ws] = {"status": "running", "agent_id": None, "started": started.isoformat(), "resumes": resumes}
            if progress_age is not None:
                self.save_progress(ws, progress_age)
        self.set_run(meta)
        (self.run_dir / "heartbeat.log").write_text("", encoding="utf-8")

    def save_progress(self, ws, age_min):
        stamp = (datetime.now(timezone.utc) - timedelta(minutes=age_min)).isoformat()
        write_jsonl(self.run_dir / "research" / ws / "progress.jsonl", [{"ts": stamp, "item": "x", "n": 4, "rows": 1}])

    def set_run(self, workstreams):
        (self.run_dir / "run.json").write_text(json.dumps({"workstreams": workstreams}), encoding="utf-8")

    def watch(self, *args):
        res = run_script("watch", self.run_dir, *args)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        return res.stdout.strip().splitlines()[-1], res.stdout

    def test_all_fresh(self):
        self.setup_ws(a=(1, 30, 0), b=(2, 30, 0))
        last, _ = self.watch()
        self.assertIn("all fresh", last)
        self.assertTrue(last.startswith("WATCH"))

    def test_save_missing(self):
        self.setup_ws(a=(None, 12, 0), b=(1, 12, 0))
        self.assertIn("SAVE-MISSING a", self.watch()[0])

    def test_no_save_missing_before_limit(self):
        self.setup_ws(a=(None, 5, 0), b=(1, 12, 0))
        self.assertIn("all fresh", self.watch()[0])

    def test_one_stale_other_fresh_resumes_from_next_item(self):
        self.setup_ws(a=(20, 60, 0), b=(1, 60, 0))
        self.assertIn("RESUME a from item 5", self.watch()[0])

    def test_all_stale_is_shared_outage_and_relaunches_nothing(self):
        self.setup_ws(a=(50, 90, 1), b=(50, 90, 2))
        last, out = self.watch()
        self.assertIn("SHARED-OUTAGE", last)
        self.assertNotIn("RELAUNCH", out)

    def test_dead_with_resume_relaunches_and_without_resumes(self):
        self.setup_ws(a=(50, 90, 1), b=(1, 90, 0), c=(50, 90, 0))
        last, _ = self.watch()
        self.assertIn("RELAUNCH a from progress", last)
        self.assertIn("RESUME c from item 5", last)

    def test_single_running_stale_is_not_called_an_outage(self):
        self.setup_ws(a=(50, 90, 1))
        last, _ = self.watch()
        self.assertIn("RELAUNCH a", last)

    def test_custom_limits(self):
        self.setup_ws(a=(6, 60, 0), b=(1, 60, 0))
        self.assertIn("all fresh", self.watch()[0])
        self.assertIn("RESUME a", self.watch("--stale-min", "5")[0])

    def test_heartbeat_keeps_a_workstream_fresh(self):
        self.setup_ws(a=(20, 60, 0), b=(1, 60, 0))
        stamp = datetime.now(timezone.utc).isoformat()
        (self.run_dir / "heartbeat.log").write_text(f"{stamp} a 5 pricing page\nnot a heartbeat\n", encoding="utf-8")
        last, out = self.watch()
        self.assertIn("all fresh", last)
        self.assertIn("heartbeat.log:2", out)

    def test_only_running_workstreams_count(self):
        self.setup_ws(a=(50, 90, 0))
        meta = json.loads((self.run_dir / "run.json").read_text(encoding="utf-8"))["workstreams"]
        meta["b"] = {"status": "done", "started": None, "resumes": 0}
        meta["c"] = {"status": "pending", "started": None, "resumes": 0}
        self.set_run(meta)
        self.assertIn("RESUME a", self.watch()[0])

    def test_invalid_run_folder_exits_two(self):
        self.assertEqual(run_script("watch", self.run_dir).returncode, 2)  # no run.json yet
        self.assertEqual(run_script("watch", self.run_dir / "nope").returncode, 2)

    def test_until_change_exits_when_all_done(self):
        self.set_run({"a": {"status": "done", "resumes": 0}, "b": {"status": "done", "resumes": 0}})
        self.assertIn("ALL-FINISHED", self.watch("--until-change")[0])

    def test_until_change_exits_at_once_on_recommendation(self):
        self.setup_ws(a=(20, 60, 0), b=(1, 60, 0))
        self.assertIn("RESUME a", self.watch("--until-change")[0])

    def _loop(self, *flags, then):
        """Run the loop in process; the first sleep applies `then`, the second fails the test."""
        calls = []

        def fake_sleep(seconds):
            calls.append(seconds)
            if len(calls) > 1:
                self.fail("loop did not exit after the change")
            then()
        argv = ["watch.py", str(self.run_dir), "--until-change", *flags]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(watch_mod.time, "sleep", fake_sleep), \
                mock.patch("sys.stdout.reconfigure", create=True), mock.patch("builtins.print"):
            self.assertEqual(watch_mod.main(), 0)
        return calls

    def test_until_change_polls_every_60_seconds_until_a_change(self):
        self.setup_ws(a=(1, 60, 0), b=(1, 60, 0))
        self.assertEqual(self._loop(then=lambda: self.save_progress("a", 20)), [60])

    def test_outage_reported_keeps_polling_through_outage(self):
        self.setup_ws(a=(20, 60, 0), b=(20, 60, 0))
        self.assertIn("SHARED-OUTAGE", self.watch("--until-change")[0])
        self.assertEqual(self._loop("--outage-reported", then=lambda: self.save_progress("b", 0)), [60])

    def test_age_comes_from_ts_even_when_the_file_was_just_copied(self):
        self.setup_ws(a=(20, 60, 0), b=(1, 60, 0))  # both files have a fresh mtime
        now = time.time()
        os.utime(self.run_dir / "research/a/progress.jsonl", (now, now))
        self.assertIn("RESUME a from item 5", self.watch()[0])

    def test_newest_ts_wins_across_rows_and_heartbeat(self):
        self.setup_ws(a=(50, 90, 0), b=(1, 90, 0))
        stamp = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
        with open(self.run_dir / "research/a/progress.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": stamp, "item": "y", "n": 5, "rows": 1}) + "\n")
            f.write(json.dumps({"ts": "2020-01-01T00:00:00Z", "item": "z", "n": 6, "rows": 1}) + "\n")
        self.assertIn("all fresh", self.watch()[0])

    def test_mtime_is_the_fallback_when_no_ts_exists(self):
        self.setup_ws(a=(1, 60, 0), b=(1, 60, 0))
        path = self.run_dir / "research/a/progress.jsonl"
        write_jsonl(path, [{"item": "x", "n": 4, "rows": 1}])
        self.assertIn("all fresh", self.watch()[0])
        old = time.time() - 20 * 60
        os.utime(path, (old, old))
        self.assertIn("RESUME a from item 5", self.watch()[0])

    def test_shared_outage_line_covers_a_new_session(self):
        self.setup_ws(a=(50, 90, 1), b=(50, 90, 2))
        self.assertIn("if this is a new session and the agents are gone, relaunch each workstream from its last saved item", self.watch()[0])

    def test_until_change_stops_at_the_cap_and_says_so(self):
        self.setup_ws(a=(1, 60, 0), b=(1, 60, 0))
        last, _ = self.watch("--until-change", "--max-min", "0")
        self.assertTrue(last.startswith("WATCH"))
        self.assertIn("stopped polling after 0 min", last)

    def test_cap_also_ends_a_reported_outage(self):
        self.setup_ws(a=(50, 90, 0), b=(50, 90, 0))
        self.assertIn("stopped polling", self.watch("--until-change", "--outage-reported", "--max-min", "0")[0])

    def test_default_cap_is_120_minutes(self):
        self.setup_ws(a=(1, 60, 0), b=(1, 60, 0))
        ticks = iter([0.0, 119 * 60.0, 120 * 60.0])
        with mock.patch.object(watch_mod.time, "monotonic", lambda: next(ticks)):
            self.assertEqual(self._loop(then=lambda: None), [60])


class CoverageMarkerTests(RunCase):
    MARKER = "<!-- tables below are generated -->"

    def merge(self):
        self.ws("w1-timeline", "events.jsonl", [event("w1-1")])
        res = run_script("merge_events", self.run_dir)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        return (self.run_dir / "02-coverage.md").read_text(encoding="utf-8")

    def test_first_merge_writes_the_marker_above_the_tables(self):
        self.assertTrue(self.merge().startswith(self.MARKER + "\n# Coverage"))

    def test_text_above_the_marker_survives_every_merge(self):
        (self.run_dir / "02-coverage.md").write_text(f"# My summary\n\nGaps: no filings.\n{self.MARKER}\nold table\n", encoding="utf-8")
        once = self.merge()
        self.assertTrue(once.startswith(f"# My summary\n\nGaps: no filings.\n{self.MARKER}\n# Coverage"))
        self.assertNotIn("old table", once)
        self.assertEqual(once, self.merge())

    def test_a_line_that_only_contains_the_marker_does_not_count(self):
        (self.run_dir / "02-coverage.md").write_text(f"see {self.MARKER}\nold\n", encoding="utf-8")
        self.assertTrue(self.merge().startswith(self.MARKER))


class CitationScopeTests(RunCase):
    def doc(self, rel, text):
        path = self.run_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def rows(self):
        return {r["id"]: r for r in self.read_jsonl("verify/ledger.jsonl")}

    def test_sample_scans_sections_before_synthesis(self):
        self.write_ledger([{"id": "weak", "ws": "w7", "source_kind": "aggregator"}, {"id": "low", "ws": "w7", "confidence": "low"},
                           {"id": "plain", "ws": "w7", "source_kind": "aggregator"}, {"id": "firm", "ws": "w7"}])
        self.doc("research/w7/section.md", "Shown [c:weak] [c:low] [c:firm].")
        res = run_script("ledger", "sample", self.run_dir, "--seed", 1)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        sample = {r["id"]: r for r in self.read_jsonl("verify/sample.jsonl")}
        self.assertEqual(sample["weak"]["stratum"], "low_or_aggregator")
        self.assertEqual(sample["low"]["stratum"], "low_or_aggregator")
        self.assertEqual(sample["plain"]["stratum"], "random")
        self.assertEqual(sample["firm"]["stratum"], "random")
        self.assertFalse(self.rows()["weak"]["load_bearing"], "a section citation does not make a row load-bearing")
        self.assertEqual(self.rows()["weak"]["cited_in"], ["research/w7/section.md"])

    def test_sample_with_no_documents_still_works(self):
        self.write_ledger([{"id": "a", "ws": "w1", "source_kind": "aggregator"}])
        res = run_script("ledger", "sample", self.run_dir, "--seed", 1)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(self.read_jsonl("verify/sample.jsonl")[0]["stratum"], "random")

    def test_fresh_sample_skips_rows_already_drawn(self):
        self.write_ledger([{"id": f"r{i}", "ws": "w1"} for i in range(30)])
        self.assertEqual(run_script("ledger", "sample", self.run_dir, "--seed", 1, "--rate", 0.05, "--min", 5).returncode, 0)
        first = {r["id"] for r in self.read_jsonl("verify/sample.jsonl") if r["in_random"]}
        res = run_script("ledger", "sample", self.run_dir, "--seed", 2, "--fresh", 5)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        rows = self.read_jsonl("verify/sample.jsonl")
        fresh = {r["id"] for r in rows if r["in_random"]}
        self.assertEqual(len(fresh), 5)
        self.assertFalse(fresh & first)

    def test_second_n_limits_the_second_sample(self):
        self.write_ledger([{"id": f"a{i}", "ws": "w1"} for i in range(30)] + [{"id": f"b{i}", "ws": "w9-new"} for i in range(30)])
        self.assertEqual(run_script("ledger", "sample", self.run_dir, "--seed", 1, "--rate", 0.05, "--min", 10).returncode, 0)
        before = {r["id"] for r in self.read_jsonl("verify/sample.jsonl")}
        res = run_script("ledger", "sample", self.run_dir, "--seed", 2, "--second-ws", "w9-new", "--second-n", 4)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        extra = [r for r in self.read_jsonl("verify/sample.jsonl") if r["id"] not in before]
        self.assertEqual(len(extra), 4)
        self.assertTrue(all(r["stratum"] == "second_sample" and not r["in_random"] for r in extra))

    def test_mark_sets_load_bearing_from_core_docs_only(self):
        self.write_ledger([{"id": i, "ws": "w1"} for i in ("core", "side", "sec", "lens")])
        self.doc("08-decision-memo.md", "Memo [c:core].")
        self.doc("06-competition.md", "Rival [c:side].")
        self.doc("09-lens.md", "Lens [c:lens].")
        self.doc("research/w1/section.md", "Section [c:sec].")
        self.assertEqual(run_script("ledger", "mark", self.run_dir).returncode, 0)
        rows = self.rows()
        self.assertTrue(rows["core"]["load_bearing"])
        for i, rel in (("side", "06-competition.md"), ("lens", "09-lens.md"), ("sec", "research/w1/section.md")):
            self.assertFalse(rows[i]["load_bearing"], i)
            self.assertEqual(rows[i]["cited_in"], [rel])

    def test_doc_goto_is_not_a_missing_citation(self):
        self.write_ledger([{"id": "a", "ws": "w1"}])
        self.doc("dashboard/prose.json", json.dumps({"so_what": [{"heading": "h", "body": "Plain [c:a].", "goto": "doc:04-so-what"},
                                                                 {"heading": "h", "body": "Revenue was 7 million."}]}))
        res = run_script("ledger", "mark", self.run_dir)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertNotIn("doc:04-so-what", res.stdout)
        self.assertIn("NO CITATION dashboard/prose.json: Revenue was 7 million", res.stdout)

    def test_check_citations_reads_every_doc(self):
        self.write_ledger([{"id": "ok", "ws": "w1"}, {"id": "bad", "ws": "w1"}, {"id": "gone", "ws": "w1"}, {"id": "open", "ws": "w1"}])
        v = lambda i, s: {"id": i, "status": s, "evidence_quote": "", "checked_url": "", "note": "", "verifier": "v1"}
        write_jsonl(self.run_dir / "verify/verdicts.jsonl", [v("ok", "confirmed"), v("bad", "wrong"), v("gone", "wrong")])
        write_jsonl(self.run_dir / "verify/corrections.jsonl", [{"id": "gone", "action": "removed", "note": ""}])
        self.doc("05-gtm.md", "[c:ok] [c:bad]")
        self.doc("09-lens.md", "[c:ghost]")
        self.doc("research/w1/section.md", "[c:gone]")
        res = run_script("ledger", "check-citations", self.run_dir)
        self.assertEqual(res.returncode, 1)
        for text in ("05-gtm.md: [c:bad]", "09-lens.md: [c:ghost]", "research/w1/section.md: [c:gone]"):
            self.assertIn(text, res.stdout)

    def test_check_citations_notes_unchecked_rows_outside_the_core_docs(self):
        self.write_ledger([{"id": "open", "ws": "w1"}, {"id": "lb", "ws": "w1", "load_bearing": True}])
        self.doc("07-deep-dive.md", "[c:open]")
        res = run_script("ledger", "check-citations", self.run_dir)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("NOTE: 1 rows cited outside the load-bearing docs have no verdict: open", res.stdout)
        self.doc("06-competition.md", "[c:lb]")
        self.assertEqual(run_script("ledger", "check-citations", self.run_dir).returncode, 1)

    def test_second_sample_with_nothing_left_says_checked_in_full(self):
        self.write_ledger([{"id": "a", "ws": "w1"}, {"id": "b", "ws": "w1"}])
        run_script("ledger", "sample", self.run_dir, "--seed", 1)
        before = (self.run_dir / "verify/sample.jsonl").read_bytes()
        res = run_script("ledger", "sample", self.run_dir, "--seed", 2, "--second-ws", "w1")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Report w1 as checked in full", res.stderr)
        self.assertEqual(before, (self.run_dir / "verify/sample.jsonl").read_bytes())

    def test_second_sample_on_an_unknown_workstream_is_not_called_checked(self):
        self.write_ledger([{"id": "a", "ws": "w1"}])
        run_script("ledger", "sample", self.run_dir, "--seed", 1)
        res = run_script("ledger", "sample", self.run_dir, "--seed", 2, "--second-ws", "w9")
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("checked in full", res.stderr)


class CostTests(RunCase):
    def call(self, ws="w7-gtm", endpoint="treg.x.posts", provider="anyapi", price=0.1, hit=True):
        return {"ts": "2026-01-01T00:00:00Z", "ws": ws, "endpoint": endpoint, "provider_served": provider, "price": price,
                "purpose": "p", "status": 200, "hit": hit, "claim_ids": []}

    def set_run(self, checks, budgets=None):
        (self.run_dir / "run.json").write_text(json.dumps({"budgets": budgets if budgets is not None else {"treg_usd_cap": 1, "treg_usd_per_call": 0.3},
                                                           "balance_checks": checks}), encoding="utf-8")

    def test_sums_gap_and_caps(self):
        self.set_run([{"label": "before", "usd": 10}, {"label": "after", "usd": 8.5}])
        self.ws("w7-gtm", "calls.jsonl", [self.call(), self.call(price=0.2, hit=False), self.call(price=0.9, provider="other")])
        self.ws("w3-traction", "calls.jsonl", [self.call(ws="w3-traction", endpoint="treg.y", price=0.0, hit=False)])
        (self.run_dir / "research/w1-timeline").mkdir()
        res = run_script("cost_report", self.run_dir)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        text = (self.run_dir / "cost-report.md").read_text(encoding="utf-8")
        for expected in ("Total logged spend: 1.2000", "Hit rate: 50%", "Misses paid for: 1 (0.2000", "GAP (balance drop minus logged spend): +0.3000",
                         "over the per-call cap of 0.3 USD: 1", "OVER CAP 0.9", "Passed the cap: YES", "no calls.jsonl: w1-timeline",
                         "| w3-traction | 1 | 0 | 0% | 0 | 0.0000 |", "| other | 1 | 1 | 100% | 0 | 0.9000 |"):
            self.assertIn(expected, text)

    def test_gap_stated_when_it_cannot_be_computed_and_caps_absent(self):
        self.set_run([{"label": "before", "usd": 10}], budgets={})
        self.ws("w7-gtm", "calls.jsonl", [self.call()])
        res = run_script("cost_report", self.run_dir)
        self.assertIn("GAP: cannot be computed", res.stdout)
        self.assertIn("Per-call cap: not set", res.stdout)

    def test_malformed_row_fails_listing_all(self):
        self.set_run([])
        bad = self.call()
        del bad["price"]
        self.ws("w7-gtm", "calls.jsonl", [self.call(), bad, self.call(hit="yes")])
        res = run_script("cost_report", self.run_dir)
        self.assertEqual(res.returncode, 1)
        self.assertIn("calls.jsonl:2", res.stdout)
        self.assertIn("calls.jsonl:3", res.stdout)
        self.assertFalse((self.run_dir / "cost-report.md").exists())

    def test_subagent_logs(self):
        self.set_run([])
        self.ws("w7-gtm", "calls.jsonl", [self.call()])
        logs = self.run_dir / "logs"
        logs.mkdir()
        use = lambda i: json.dumps({"message": {"content": [{"type": "tool_use", "id": i}, {"type": "text", "text": "x"}]}})
        (logs / "a.jsonl").write_text("\n".join([use("1"), use("1"), use("2"), "{torn"]) + "\n", encoding="utf-8")
        self.assertEqual(run_script("cost_report", self.run_dir, "--subagent-logs", logs).returncode, 0)
        self.assertIn("| a.jsonl | 2 | 1 |", (self.run_dir / "cost-report.md").read_text(encoding="utf-8"))
        self.assertEqual(run_script("cost_report", self.run_dir, "--subagent-logs", self.run_dir / "nope").returncode, 2)


class InstallerTests(unittest.TestCase):
    """Both installers fetch a fixed file list, so a new skill file must be added to each, or fresh installs break."""

    def test_installers_list_every_skill_file(self):
        import re
        root = SCRIPTS.parent
        files = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
                 and "dashboard" not in p.parts and "__pycache__" not in p.parts}
        files = {f for f in files if not f.startswith("example/") or f.endswith(("README.md", "bundle-sample.json"))}
        for name in ("install.ps1", "install.sh"):
            text = (root.parent / name).read_text(encoding="utf-8")
            listed = set(re.findall(r"((?:SKILL\.md)|(?:(?:references|scripts|template|example)/[\w./-]+))", text))
            self.assertEqual(files - listed, set(), f"{name} misses files")
            self.assertEqual(listed - files, set(), f"{name} lists files that don't exist")


if __name__ == "__main__":
    unittest.main()
