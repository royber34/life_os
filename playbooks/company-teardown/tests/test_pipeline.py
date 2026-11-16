"""Tests for merge_events.py, ledger.py, watch.py, cost_report.py, runstate.py and finalize.py.
Run: python -m unittest discover -s tests"""
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
    bd = load("build_dashboard")

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

    def test_workstream_checked_after_the_sample_is_reported_as_checked_and_kept_out_of_the_rate(self):
        self.setup_verdicts(40, {"w1-timeline": 1})
        rows = [json.loads(l) for l in (self.run_dir / "verify/ledger.jsonl").read_text(encoding="utf-8").splitlines()]
        self.write_ledger(rows + [{"id": f"g{i}", "ws": "w7-gtm"} for i in range(10)])
        with open(self.run_dir / "verify/verdicts.jsonl", "a", encoding="utf-8") as f:
            for i, status in enumerate(["confirmed"] * 5 + ["wrong", "partly"]):
                f.write(json.dumps({"id": f"g{i}", "status": status, "evidence_quote": "", "checked_url": "", "note": "", "verifier": "v9"}) + "\n")
            f.write(json.dumps({"id": "g7", "status": "unreachable", "evidence_quote": "", "checked_url": "", "note": "", "verifier": "v9"}) + "\n")
        data, md = self.report()
        ws = data["per_workstream"]["w7-gtm"]
        self.assertEqual(ws["label"], "CHECKED OUTSIDE THE RANDOM SAMPLE (7 of 10 rows, 1 open)")  # the unreachable row is not a check
        self.assertEqual((ws["checked"], ws["outside_checked"], ws["outside_open"]), (0, 7, 1))
        self.assertEqual(data["random_checked"], 40)
        self.assertAlmostEqual(data["wrong_rate"], 1 / 40)
        self.assertNotIn("NOT CHECKED", md)
        self.assertIn("outside the random sample and still wrong or unsupported, with no correction: g5", md)
        page = self.bd.load_verification(self.run_dir, "2026-06-01")["workstreams"]["w7-gtm"]
        self.assertEqual(page, "CHECKED OUTSIDE THE RANDOM SAMPLE (7 of 10 rows, 1 open)")  # no "(0 checked, 0 wrong)" beside it
        write_jsonl(self.run_dir / "verify/corrections.jsonl", [{"id": "g5", "action": "corrected", "note": "fixed"}])
        data, md = self.report()
        self.assertEqual(data["per_workstream"]["w7-gtm"]["label"], "CHECKED OUTSIDE THE RANDOM SAMPLE (7 of 10 rows, 0 open)")
        self.assertNotIn("no correction: g5", md)

    def test_too_few_to_rate_still_credits_rows_checked_outside_the_sample(self):
        self.setup_verdicts(40, {}, per_ws={"w1-timeline": 38, "w7-gtm": 2})
        rows = [json.loads(l) for l in (self.run_dir / "verify/ledger.jsonl").read_text(encoding="utf-8").splitlines()]
        self.write_ledger(rows + [{"id": f"g{i}", "ws": "w7-gtm"} for i in range(30)])
        write_jsonl(self.run_dir / "verify/verdicts.jsonl", [json.loads(l) for l in (self.run_dir / "verify/verdicts.jsonl").read_text(encoding="utf-8").splitlines()]
                    + [{"id": f"g{i}", "status": "confirmed", "evidence_quote": "", "checked_url": "", "note": "", "verifier": "v9"} for i in range(25)])
        data, md = self.report()
        self.assertEqual(data["per_workstream"]["w7-gtm"]["label"], "TOO FEW TO RATE; 25 more rows checked outside the random sample, 0 open")
        self.assertIn("Too few random checks", md)
        page = self.bd.load_verification(self.run_dir, "2026-06-01")["workstreams"]["w7-gtm"]
        self.assertTrue(page.endswith("(2 in the random sample, 0 wrong)"))

    def test_workstream_with_no_verdict_at_all_is_still_not_checked(self):
        self.setup_verdicts(40, {})
        rows = [json.loads(l) for l in (self.run_dir / "verify/ledger.jsonl").read_text(encoding="utf-8").splitlines()]
        self.write_ledger(rows + [{"id": f"g{i}", "ws": "w7-gtm"} for i in range(3)])
        self.assertEqual(self.report()[0]["per_workstream"]["w7-gtm"]["label"], "NOT CHECKED")


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

    def test_heartbeat_by_prefix_keeps_a_named_workstream_fresh(self):
        self.setup_ws(**{"w9-marketplace": (20, 60, 0), "w10-store": (1, 60, 0)})
        stamp = datetime.now(timezone.utc).isoformat()
        (self.run_dir / "heartbeat.log").write_text(f"{stamp} w9 5 amazon page\n", encoding="utf-8")
        self.assertIn("all fresh", self.watch()[0])

    def test_untracked_workstream_folder_asks_to_register(self):
        self.setup_ws(**{"w1-timeline": (1, 30, 0), "w2-economics": (1, 30, 0)})
        (self.run_dir / "research" / "w22-social-history").mkdir(parents=True)
        (self.run_dir / "research" / "merged").mkdir(parents=True)
        last, _ = self.watch()
        self.assertIn("REGISTER w22-social-history", last)
        self.assertNotIn("merged", last)

    def test_untracked_folder_blocks_all_finished(self):
        self.set_run({"w1-a": {"status": "done", "resumes": 0}})
        (self.run_dir / "research" / "w9-late").mkdir(parents=True)
        last, _ = self.watch()
        self.assertNotIn("ALL-FINISHED", last)
        self.assertIn("REGISTER w9-late", last)

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

    def test_model_use_from_transcripts_counts_each_message_once_and_checks_cap(self):
        self.set_run([], budgets={"model_usd_cap": 1})
        self.ws("w7-gtm", "calls.jsonl", [self.call()])

        def msg(mid, ts, model="claude-opus-5-5", out=100_000):
            return json.dumps({"type": "assistant", "timestamp": ts, "message": {"id": mid, "model": model, "usage": {
                "input_tokens": 0, "output_tokens": out, "cache_read_input_tokens": 1_000_000,
                "cache_creation_input_tokens": 100_000, "cache_creation": {"ephemeral_5m_input_tokens": 100_000,
                                                                           "ephemeral_1h_input_tokens": 0}}}})
        t = self.run_dir / "t.jsonl"
        # m1 streamed twice (counts once), m2 outside the window, m3 an unknown model.
        t.write_text("\n".join([msg("m1", "2026-01-01T10:00:00Z"), msg("m1", "2026-01-01T10:00:00Z"),
                                msg("m2", "2026-01-02T10:00:00Z"), msg("m3", "2026-01-01T11:00:00Z", model="claude-new")]) + "\n",
                     encoding="utf-8")
        res = run_script("cost_report", self.run_dir, "--transcripts", t, "--until", "2026-01-02")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        text = (self.run_dir / "cost-report.md").read_text(encoding="utf-8")
        # opus: 0.1M out x 20 + 1M read x 0.2 + 0.1M 5m write x 4 x 1.25 = 2.00 + 0.20 + 0.50 = 2.70
        self.assertIn("| claude-opus-5-5 | 1 | 100,000 | 2.70 |", text)
        self.assertIn("not priced", text)
        self.assertIn("Model use total: 2.70 USD", text)
        self.assertIn("model cap of 1 USD: 2.70 USD. Passed the cap: YES", text)

    def test_model_use_from_headless_results(self):
        self.set_run([])
        self.ws("w7-gtm", "calls.jsonl", [self.call()])
        (self.run_dir / "usage").mkdir()
        (self.run_dir / "usage" / "s2.json").write_text(json.dumps({"total_cost_usd": 12.5}), encoding="utf-8")
        (self.run_dir / "usage" / "s4.json").write_text(json.dumps({"total_cost_usd": 7.25}), encoding="utf-8")
        run_script("cost_report", self.run_dir)
        self.assertIn("Model use total: 19.75 USD", (self.run_dir / "cost-report.md").read_text(encoding="utf-8"))

    def test_model_use_unmeasured_is_said(self):
        self.set_run([])
        self.ws("w7-gtm", "calls.jsonl", [self.call()])
        run_script("cost_report", self.run_dir)
        self.assertIn("Model use: not measured", (self.run_dir / "cost-report.md").read_text(encoding="utf-8"))


class RunStateTests(RunCase):
    def setUp(self):
        super().setUp()
        (self.run_dir / "run.json").write_text(json.dumps({"slug": "acme", "workstreams": {}}), encoding="utf-8")

    def rs(self, *args):
        return run_script("runstate", self.run_dir, *args)

    def test_start_resume_done_and_log(self):
        self.assertEqual(self.rs("start", "w9-market", "--agent-id", "a1").returncode, 0)
        self.assertEqual(self.rs("resume", "w9-market").returncode, 0)
        self.assertEqual(self.rs("done", "w9-market").returncode, 0)
        ws = self.read_json("run.json")["workstreams"]["w9-market"]
        self.assertEqual((ws["status"], ws["agent_id"], ws["resumes"]), ("done", "a1", 1))
        self.assertTrue(ws["started"] and ws["ended"])
        self.assertEqual([r["action"] for r in self.read_jsonl("run-log.jsonl")], ["start", "resume", "done"])

    def test_done_before_start_is_refused(self):
        self.assertEqual(self.rs("done", "w1-x").returncode, 2)

    def test_stage_and_gate_are_timestamped(self):
        self.rs("stage", "S2")
        self.assertEqual(self.rs("gate", "G2").returncode, 2)  # needs --words
        self.rs("gate", "G2", "--words", "coverage checks passed")
        data = self.read_json("run.json")
        self.assertEqual(data["stage"], "S2")
        self.assertEqual(data["stage_history"][0]["stage"], "S2")
        self.assertEqual(data["gates"]["G2"]["words"], "coverage checks passed")
        self.assertIn("T", data["gates"]["G2"]["ts"])

    def test_g1_locks_scope_out_once_and_the_page_names_only_locked_parts(self):
        cfg = self.read_json("config.json")
        cfg["scope_out"] = ["gtm.impact", "sowhat.budget"]
        (self.run_dir / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        self.rs("gate", "G1", "--words", "auto: probe checks passed")
        self.assertEqual(self.read_json("run.json")["scope_out"]["items"], ["gtm.impact", "sowhat.budget"])
        cfg["scope_out"].append("ai.uses")  # an edit after G1
        (self.run_dir / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        self.rs("gate", "G1", "--words", "again")
        self.assertEqual(self.read_json("run.json")["scope_out"]["items"], ["gtm.impact", "sowhat.budget"])
        bd = load("build_dashboard")
        self.assertEqual(bd.left_out(self.run_dir), ["the campaign impact study", "budget moves"])


class FinalizeTests(RunCase):
    def build_ok_run(self, label="DIRECTIONAL ONLY"):
        (self.run_dir / "run.json").write_text(json.dumps({"workstreams": {"w1-timeline": {"status": "done"}}}), encoding="utf-8")
        (self.run_dir / "research" / "w1-timeline").mkdir()
        report = {"label": label, "claims_total": 10, "load_bearing_checked": 3, "load_bearing_total": 3, "random_checked": 5,
                  "wrong_rate": 0.0, "interval_low": 0.0, "interval_high": 0.5, "cutoff": "2026-06-01", "findings": []}
        (self.run_dir / "verify" / "report.json").write_text(json.dumps(report), encoding="utf-8")
        dash = self.run_dir / "dashboard"
        (dash / "screens").mkdir(parents=True)
        (dash / "bundle.json").write_text(json.dumps({"verification": {"label": label, "claims_total": 10}}), encoding="utf-8")
        (dash / "prose.json").write_text("{}", encoding="utf-8")
        (dash / "index.html").write_text("<html></html>", encoding="utf-8")
        (dash / "screens" / "render-report.md").write_text("Result: **PASS**, 1 of 1 checks passed.\n", encoding="utf-8")
        now = time.time()
        for rel, age in (("verify/report.json", 40), ("dashboard/bundle.json", 30), ("dashboard/prose.json", 30),
                         ("dashboard/index.html", 20), ("dashboard/screens/render-report.md", 10)):
            os.utime(self.run_dir / rel, (now - age, now - age))
        (self.run_dir / "raw-research-README.md").write_text("# Archive\n\nHand-written part.\n", encoding="utf-8")

    def fin(self, *args):
        return run_script("finalize", self.run_dir, *args)

    def test_consistent_run_finalizes_and_writes_readme_section(self):
        self.build_ok_run()
        res = self.fin()
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        readme = (self.run_dir / "raw-research-README.md").read_text(encoding="utf-8")
        self.assertIn("Hand-written part.", readme)
        self.assertIn("Label: **DIRECTIONAL ONLY**", readme)
        self.assertEqual(self.read_json("run.json")["stage"], "S6 done")
        self.assertEqual(self.fin().returncode, 0)  # idempotent: the section is replaced, not duplicated
        self.assertEqual((self.run_dir / "raw-research-README.md").read_text(encoding="utf-8").count("finalize:verification"), 1)

    def test_untracked_workstream_conflict_copy_and_label_fail(self):
        self.build_ok_run(label="NOT RELIABLE YET")
        (self.run_dir / "research" / "w22-late").mkdir()
        (self.run_dir / "research" / "w1-timeline" / "section (# Name clash 2026-11-06 abc #).md").write_text("x", encoding="utf-8")
        res = self.fin()
        self.assertEqual(res.returncode, 1)
        for expected in ("FAIL  Every workstream folder is in run.json: w22-late", "FAIL  No sync-conflict copies",
                         "FAIL  Verification label allowed: NOT RELIABLE YET"):
            self.assertIn(expected, res.stdout)
        self.assertNotIn("finalize:verification", (self.run_dir / "raw-research-README.md").read_text(encoding="utf-8"))

    def test_stale_page_and_render_fail(self):
        self.build_ok_run()
        now = time.time()
        os.utime(self.run_dir / "verify" / "report.json", (now, now))  # report changed after the page was built
        res = self.fin()
        self.assertEqual(res.returncode, 1)
        self.assertIn("FAIL  Page built after its inputs", res.stdout)

    def test_render_older_than_page_fails(self):
        self.build_ok_run()
        now = time.time()
        os.utime(self.run_dir / "dashboard" / "index.html", (now, now))  # page rebuilt, render not rerun
        self.assertIn("FAIL  Render test passed on the current page", self.fin().stdout)

    def test_page_label_mismatch_fails(self):
        self.build_ok_run()
        (self.run_dir / "dashboard" / "bundle.json").write_text(json.dumps({"verification": {"label": "NOT RELIABLE YET",
                                                                                              "claims_total": 10}}), encoding="utf-8")
        now = time.time()
        os.utime(self.run_dir / "dashboard" / "bundle.json", (now - 30, now - 30))
        self.assertIn("FAIL  Page carries the report's label", self.fin().stdout)

    def test_home_directory_path_in_page_fails(self):
        self.build_ok_run()
        for leak in ("C:/Users/someone/runs/acme/research/w1/rows.csv", "C:\\\\Users\\\\someone\\\\runs\\\\x.json", "/home/someone/runs/x.json"):
            with self.subTest(leak=leak):
                page = self.run_dir / "dashboard" / "index.html"
                st = page.stat()
                page.write_text(f'<html><script>{{"source":"{leak}"}}</script></html>', encoding="utf-8")
                os.utime(page, (st.st_atime, st.st_mtime))
                res = self.fin()
                self.assertEqual(res.returncode, 1)
                self.assertIn("FAIL  No local home-directory path in the page", res.stdout)

    def test_urls_api_paths_and_page_words_are_not_flagged(self):
        self.build_ok_run()
        page = self.run_dir / "dashboard" / "index.html"
        st = page.stat()
        page.write_text('<html><a href="https://example.com/Users/guide">x</a> GET /users/me, '
                        '<a href="https://app.example.com/#/home/dashboard">y</a> login?next=/home/garden '
                        'and the /home/bedding range</html>', encoding="utf-8")
        os.utime(page, (st.st_atime, st.st_mtime))
        self.assertIn("pass  No local home-directory path in the page", self.fin().stdout)


class ScrubPathsTests(unittest.TestCase):
    """assemble scrubs local paths out of everything it embeds in the page, by exact folder, never by pattern."""

    def setUp(self):
        self.bd = load("build_dashboard")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name) / "home" / "someone"
        self.run = self.home / "runs" / "teardown-acme"
        self.run.mkdir(parents=True)
        self.R, self.H = self.run.resolve(), self.home.resolve()

    def scrub(self, s):
        return self.bd.scrub_paths(s, self.run, home=self.home)

    def test_run_folder_paths_become_relative(self):
        self.assertEqual(self.scrub(f"{self.R.as_posix()}/research/w19/rows.csv"), "research/w19/rows.csv")
        self.assertEqual(self.scrub(f"{self.R}\\research\\w21\\series.csv").replace("\\", "/"), "research/w21/series.csv")
        self.assertEqual(self.scrub(json.dumps(f"{self.R}\\research\\x.json")[1:-1]), "research\\\\x.json")  # escaped stays escaped
        self.assertEqual(self.scrub(self.R.as_posix()), ".")

    def test_other_home_paths_lose_their_folders(self):
        # a whole value keeps only its file name, so other folders (and other clients) don't show
        self.assertEqual(self.scrub(f"{self.H}\\Drive\\clients\\Other\\notes.md"), "notes.md")
        self.assertEqual(self.scrub(f"{self.R.as_posix()}-old/research/x.csv"), "x.csv")
        self.assertEqual(self.scrub(f"read from {self.H.as_posix()}/Downloads/x.json today"), "read from ~/Downloads/x.json today")

    def test_urls_api_paths_and_page_words_are_untouched(self):
        for s in ("GET /users/me returns the profile", "https://app.example.com/#/home/dashboard", "login?next=/home/garden",
                  "see /home/bedding", "https://example.com/Users/page", "/home/someone-else/x.csv"):
            self.assertEqual(self.scrub(s), s)
        self.assertEqual(self.bd.scrub_paths({"n": 3, "k": [None, True]}, self.run, home=self.home), {"n": 3, "k": [None, True]})

    def test_finalize_and_build_share_one_folder_matcher(self):
        fin = load("finalize")
        self.assertEqual(fin.SEP, self.bd.SEP)
        for folder in (self.run, self.home, Path(self.run.anchor)):
            a, b = fin.folder_re(folder), self.bd.folder_re(folder)
            self.assertEqual((a.pattern, a.flags) if a else None, (b.pattern, b.flags) if b else None)

    def test_assemble_writes_no_local_path_into_the_bundle(self):
        run = self.run
        (run / "dashboard").mkdir()
        (run / "config.json").write_text(json.dumps({"name": "Acme", "cutoff": "2026-06-01", "lanes": [{"id": "feature"}]}), encoding="utf-8")
        (run / "dashboard" / "prose.json").write_text(json.dumps({"overview": {"summary": [{"heading": "A", "body": "Launch [c:e1]."}]}}), encoding="utf-8")
        merged = run / "research" / "merged"
        merged.mkdir(parents=True)
        (merged / "events.json").write_text(json.dumps([event("e1", source=f"{self.R.as_posix()}/research/w1/raw/page.html",
                                                               detail=f"Saved at {self.R}\\research\\w1\\raw\\page.html")]), encoding="utf-8")
        with mock.patch.object(Path, "home", return_value=self.home):
            self.bd.assemble(run)
        text = (run / "dashboard" / "bundle.json").read_text(encoding="utf-8")
        self.assertNotIn(self.R.as_posix(), text)
        self.assertIsNone(self.bd.folder_re(self.home).search(text))
        self.assertIn("research/w1/raw/page.html", text)


class ClientModeTests(unittest.TestCase):
    """Client mode: the one-pager drives the Overview top, trails carry the evidence, the validator holds the contract."""

    def setUp(self):
        self.bd = load("build_dashboard")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.run_dir = Path(tmp.name) / "teardown-acme"
        (self.run_dir / "verify").mkdir(parents=True)
        (self.run_dir / "dashboard").mkdir()
        write_jsonl(self.run_dir / "verify" / "ledger.jsonl", [
            {"id": "w9-c1", "text": "Twelve of twelve listings sold by resellers.", "source": "https://example.com/a", "basis": "fact"},
            {"id": "w3-c2", "text": "Most recent reviews mention slow repairs.", "source": "https://example.com/b", "basis": "fact"}])
        write_jsonl(self.run_dir / "verify" / "verdicts.jsonl", [
            {"id": "w9-c1", "status": "confirmed", "evidence_quote": "12 listings, all resellers", "checked_url": "https://example.com/a", "note": "", "verifier": "v1"},
            {"id": "w9-c1", "status": "confirmed", "evidence_quote": "all 12 resellers", "checked_url": "https://example.com/a", "note": "", "verifier": "g1"}])

    def finding(self, i, **kw):
        f = {"id": f"f{i}", "so": f"Point {i}", "value": f"{i} of 12", "kind": "Measured", "date": "2026-06-01",
             "label": "Listings counted on the first results page [c:w9-c1].", "means": "Resellers set the price shown.",
             "reasoning": "All counted listings had a reseller. Inference: the reseller sets the price.", "claims": ["w9-c1"]}
        f.update(kw)
        return f

    def prose(self, n=3):
        return {"onepager": {"headline": "Resellers set the price buyers see.", "findings": [self.finding(i) for i in range(1, n + 1)],
                             "basis": "Public sources read up to 1 June 2026.", "way_in": "Full report: {{report_link}}."},
                "top": {"gtm": {"headline": "Ads lead with discounts.", "points": [
                    {"so": "Discount ads", "value": "8 of 30", "label": "Ads read [c:w3-c2].", "kind": "Measured", "reasoning": "Counted."}]}},
                "overview": {"further": {"heading": "Where to look further", "rows": [{"source": f"S{i}", "clarifies": "x"} for i in range(5)]}},
                "moves": {"items": [{"id": "m1", "further": "Where to look further: repair tickets by channel."}]}}

    def test_overview_top_is_the_one_pager(self):
        p = self.prose()
        top = self.bd.overview_top_from_onepager(p["onepager"], {"doors": [{"label": "More", "goto": "tab:sowhat"}]})
        self.assertEqual(top["headline"], p["onepager"]["headline"])
        self.assertEqual([pt["trail"] for pt in top["points"]], ["f1", "f2", "f3"])
        self.assertEqual(top["doors"][0]["label"], "More")

    def test_trails_carry_quotes_status_and_confirmations(self):
        p = self.prose()
        trails = self.bd.build_trails(self.run_dir, p, "2026-06-01")
        c = trails["f1"]["claims"][0]
        self.assertEqual((c["id"], c["status"], c["confirmations"], c["quote"], c["read"]),
                         ("w9-c1", "confirmed", 2, "all 12 resellers", "2026-06-01"))
        self.assertEqual(trails["gtm.0"]["claims"][0]["status"], "unchecked")
        self.assertEqual(p["top"]["gtm"]["points"][0]["trail"], "gtm.0")

    def problems_for(self, prose):
        bundle = {"claims": {"w9-c1": {}, "w3-c2": {}}}
        prose.setdefault("top", {})["overview"] = self.bd.overview_top_from_onepager(prose["onepager"]) if prose.get("onepager") else {}
        bundle["trails"] = self.bd.build_trails(self.run_dir, prose, "2026-06-01")
        problems = []
        self.bd.check_client(prose, bundle, problems)
        return problems

    def test_complete_client_prose_passes(self):
        self.assertEqual(self.problems_for(self.prose()), [])

    def test_client_contract_failures_are_named(self):
        p = self.prose(n=2)
        p["onepager"]["findings"][0]["kind"] = "Estimate"
        p["onepager"]["way_in"] = "Full report attached."
        p["overview"]["connections"] = {"rows": []}
        p["overview"]["further"]["rows"] = p["overview"]["further"]["rows"][:3]
        p["moves"]["items"][0]["further"] = "Look at the tickets."
        del p["top"]["gtm"]["points"][0]["reasoning"]
        text = "\n".join(self.problems_for(p))
        for expected in ("give 3 to 5, found 2", "kind Estimate", "{{report_link}}", "use prose.overview.further",
                         "at least 5 rows", "further must start with 'Where to look further:'", "reasoning is required"):
            self.assertIn(expected, text)

    def test_onepager_page_links_sources_trails_and_report(self):
        p = self.prose()
        p["top"]["overview"] = self.bd.overview_top_from_onepager(p["onepager"])
        bundle = {"meta": {"name": "Acme", "cutoff": "2026-06-01"}, "config": {"brand": {"name": "Firm"}}, "prose": p,
                  "claims": {"w9-c1": {"source": "https://example.com/a"}}}
        (self.run_dir / "dashboard" / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
        self.assertTrue(self.bd.build_onepager(self.run_dir, "https://reports.example.com/x/"))
        page = (self.run_dir / "dashboard" / "onepager.html").read_text(encoding="utf-8")
        self.assertIn('href="https://example.com/a"', page)
        self.assertIn('href="https://reports.example.com/x/#trail=f2"', page)
        self.assertIn('<a href="https://reports.example.com/x/">https://reports.example.com/x/</a>', page)
        self.assertNotIn("{{report_link}}", page)
        self.assertEqual(page.count('class="op-f"'), 3)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.cfg = self.root / "mcp.json"
        self.cfg.write_text(json.dumps({"mcpServers": {"other": {"type": "http", "url": "https://example.invalid/"}}}), encoding="utf-8")

    def pf(self, run, *args):
        run.mkdir(parents=True, exist_ok=True)
        return run_script("preflight", run, "--mcp-config", self.cfg, *args)

    def test_synced_folder_fails(self):
        res = self.pf(self.root / "Proton Drive" / "teardown-acme")
        self.assertEqual(res.returncode, 1)
        self.assertIn("FAIL  Run folder is outside synced folders: inside proton drive", res.stdout)

    def test_missing_treg_warns_unless_required(self):
        local = self.root / "runs" / "teardown-acme"
        res = self.pf(local)
        self.assertIn("WARN  treg MCP configured", res.stdout)
        self.assertNotIn("FAIL  treg", res.stdout)
        self.assertIn("FAIL  treg MCP configured", self.pf(local, "--require-treg").stdout)


    def test_regress_refuses_a_folder_that_is_not_a_fixture(self):
        self.assertEqual(run_script("regress", self.root).returncode, 2)


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
