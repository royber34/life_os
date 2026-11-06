#!/usr/bin/env python3
"""Validate workstream rows, dedupe events, write research/merged/* and 02-coverage.md.

Usage: python -I merge_events.py <run-dir> [--force]
Exit 0 on success, 1 on invalid rows (without --force), 2 on an unusable run folder.
"""
import argparse, json, re, sys, unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

EVENT_KEYS = ("id date date_end date_precision lane kind title detail metric_name metric_value metric_unit "
              "person function basis confidence source source_kind load_bearing tags").split()
GTM_KEYS = ("id date time_utc channel actor format title hook cta asset_url linked_product views likes reposts "
            "replies bookmarks metrics_observed_at lift_metric lift_before lift_after lift_window basis "
            "confidence source source_kind load_bearing notes").split()
PROFILE_KEYS = ("id name short_name org group hq founded ownership overall business_model pricing size revenue "
                "traction funding positioning positioning_line icp gtm moat weaknesses recent_moves scores "
                "threat_level threat_why partner_level partner_shape partner_why coverage gaps sources "
                "confidence").split()
LANDSCAPE_KEYS = "id name org group what url why_listed source confidence".split()
FILES = {"events.jsonl": EVENT_KEYS, "gtm_actions.jsonl": GTM_KEYS,
         "profiles.jsonl": PROFILE_KEYS, "landscape.jsonl": LANDSCAPE_KEYS}
ENUMS = {
    "date_precision": {"day", "week", "month", "year"}, "kind": {"event", "span", "metric"},
    "basis": {"fact", "inference"}, "confidence": {"high", "medium", "low"},
    "source_kind": {"primary", "secondary", "aggregator"},
    "channel": set("x youtube linkedin instagram tiktok tiktok_shop amazon retail meta_ads google_ads influencer pr product_hunt review_site docs changelog blog "
                   "podcast hackernews reddit community newsletter email website seo_page agent_seo marketplace "
                   "github partner referral pricing_hook event other".split()),
    "format": set("video thread post reply page listing repo ad email talk podcast article launch program other".split()),
    "ownership": set("private_vc public nonprofit academic government big_tech_unit open_source_project "
                     "bootstrapped family".split()),
    "threat_level": {"high", "medium", "low"}, "partner_level": {"high", "medium", "low", "none"},
}
CONTRACT_WS = set("w1-timeline w2-economics w3-traction w4-legal w5-product w6-team w7-gtm w8-competitors".split())
RANK = {"high": 3, "medium": 2, "low": 1}
KIND_RANK = {"primary": 3, "secondary": 2, "aggregator": 1}


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def is_date(v):
    try:
        return isinstance(v, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", v)) and bool(date.fromisoformat(v))
    except ValueError:
        return False


def one_of(v, allowed):
    return isinstance(v, str) and v in allowed


def load_config(run):
    path = run / "config.json"
    try:
        cfg = json.loads(path.read_text(encoding="utf-8-sig"))
        comp = cfg.get("competition") or {}
        return {"lanes": {l["id"] for l in cfg["lanes"]}, "groups": {g["id"] for g in comp.get("groups", [])},
                "scores": {s["id"] for s in comp.get("scores", [])},
                "components": {c["id"] for c in comp.get("components", [])}}
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        die(f"cannot use {path}: {type(e).__name__}: {e}")


def check_row(name, r, cfg):
    """Return the list of problems with one parsed row."""
    errs = [f"missing key '{k}'" for k in FILES[name] if k not in r]
    get = r.get
    for k, allowed in ENUMS.items():
        if k in FILES[name] and k in r and not one_of(r[k], allowed):
            errs.append(f"{k}={r[k]!r} is not an allowed value")
    if not (isinstance(get("id"), str) and get("id")):
        errs.append("id must be a non-empty string")
    if "date" in FILES[name] and "date" in r and not is_date(r["date"]):
        errs.append(f"date={r['date']!r} is not YYYY-MM-DD")
    if "source" in FILES[name] and "source" in r and not (isinstance(r["source"], str) and r["source"].strip()):
        errs.append("source is empty")
    if "load_bearing" in FILES[name] and "load_bearing" in r and not isinstance(r["load_bearing"], bool):
        errs.append("load_bearing must be true or false")
    if name == "events.jsonl":
        if get("date_end") is not None and not is_date(get("date_end")):
            errs.append(f"date_end={get('date_end')!r} is not YYYY-MM-DD")
        if "lane" in r and not one_of(r["lane"], cfg["lanes"]):
            errs.append(f"lane={r['lane']!r} is not in config.json lanes")
        if not isinstance(get("tags", []), list):
            errs.append("tags must be a list")
        if get("kind") == "metric":
            if not re.fullmatch(r"[a-z0-9_]+", str(get("metric_name"))):
                errs.append(f"metric row needs a snake_case metric_name, got {get('metric_name')!r}")
            if get("metric_value") is None:
                errs.append("metric row needs a metric_value")
    if name == "gtm_actions.jsonl" and get("metrics_observed_at") is not None \
            and not is_date(str(get("metrics_observed_at"))[:10]):
        errs.append(f"metrics_observed_at={get('metrics_observed_at')!r} is not a date")
    if name in ("profiles.jsonl", "landscape.jsonl") and "group" in r and not one_of(r["group"], cfg["groups"]):
        errs.append(f"group={r['group']!r} is not in config.json competition.groups")
    if name == "profiles.jsonl":
        sources = get("sources")
        if "sources" in r and not (isinstance(sources, list) and any(isinstance(s, str) and s.strip() for s in sources)):
            errs.append("sources is empty")
        scores = get("scores")
        for k, v in (scores.items() if isinstance(scores, dict) else ()):
            if k not in cfg["scores"]:
                errs.append(f"score id {k!r} is not in config.json competition.scores")
            if not (type(v) is int and 0 <= v <= 5):
                errs.append(f"score {k}={v!r} must be an integer 0 to 5")
        if "scores" in r and not isinstance(scores, dict):
            errs.append("scores must be an object")
        cover = get("coverage")
        for k, v in (cover.items() if isinstance(cover, dict) else ()):
            if k not in cfg["components"] or v not in ("yes", "partial", "no"):
                errs.append(f"coverage {k}={v!r} has an unknown component or value")
        for m in get("recent_moves") if isinstance(get("recent_moves"), list) else ():
            if not (isinstance(m, dict) and is_date(m.get("date"))):
                errs.append(f"recent_moves entry has a bad date: {m!r}")
    return errs


def read_rows(run, cfg):
    """Return ({file name: [rows]}, [bad row reports with file and line])."""
    good, bad, seen = defaultdict(list), [], {}
    for ws_dir in sorted(p for p in (run / "research").iterdir() if p.is_dir() and p.name != "merged"):
        if ws_dir.name not in CONTRACT_WS:
            if not re.fullmatch(r"w(9|\d\d)-[a-z0-9-]+", ws_dir.name):
                print(f"WARNING: research/{ws_dir.name} is not a workstream named in the contract; reading it anyway")
        for name in FILES:
            path = ws_dir / name
            if not path.exists():
                continue
            label = f"research/{ws_dir.name}/{name}"
            for n, raw in enumerate(path.read_bytes().split(b"\n"), 1):
                if not raw.strip():
                    continue
                try:
                    row = json.loads(raw.decode("utf-8-sig"))
                    errs = check_row(name, row, cfg) if isinstance(row, dict) else ["line is not a JSON object"]
                except ValueError as e:
                    row, errs = None, [f"not valid UTF-8 JSON: {e}"]
                rid = row.get("id") if isinstance(row, dict) else None
                if isinstance(rid, str) and rid in seen:
                    errs.append(f"id {rid!r} already used at {seen[rid]}")
                if errs:
                    bad.append(f"{label}:{n}: " + "; ".join(errs))
                    continue
                seen[rid] = f"{label}:{n}"
                row["ws"] = ws_dir.name
                good[name].append(row)
    return good, bad


def norm_title(title):
    text = unicodedata.normalize("NFKC", str(title)).casefold()
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def dedupe(rows):
    """Merge rows sharing date and normalised title across workstreams. Returns (kept, Counter of merged per ws)."""
    groups = defaultdict(list)
    for r in rows:
        key = (r["date"], norm_title(r["title"]))
        if r["kind"] == "metric":  # differing readings of one metric are a conflict to show, so they stay apart
            key += (r["metric_name"], str(r["metric_value"]))
        groups[key].append(r)
    kept, merged = [], Counter()
    for group in groups.values():
        best = max(group, key=lambda r: (RANK[r["confidence"]], KIND_RANK[r["source_kind"]]))
        for r in group:
            if r is best or r["ws"] == best["ws"]:
                kept.append(r)
            else:
                best["tags"] = list(best["tags"]) + [f"merged:{r['id']}"] + [t for t in r["tags"] if str(t).startswith("merged:")]
                best["load_bearing"] = best["load_bearing"] or r["load_bearing"]
                merged[r["ws"]] += 1
    return kept, merged


def last_progress(path, warnings):
    last = None
    for n, raw in enumerate(path.read_bytes().split(b"\n"), 1):
        if raw.strip():
            try:
                last = json.loads(raw.decode("utf-8-sig"))["ts"]
            except (ValueError, KeyError, TypeError) as e:
                warnings.append(f"{path.parent.name}/progress.jsonl:{n} is malformed ({e})")
    return last


def pct(n, total):
    return f"{100 * n / total:.0f}%" if total else "n/a"


def stat_cells(rows):
    basis, conf, kind = (Counter(r.get(k) for r in rows) for k in ("basis", "confidence", "source_kind"))
    with_basis, with_kind = basis["fact"] + basis["inference"], sum(kind[k] for k in KIND_RANK)
    return [pct(basis["fact"], with_basis), pct(basis["inference"], with_basis), conf["high"], conf["medium"], conf["low"],
            pct(kind["primary"], with_kind), pct(kind["aggregator"], with_kind)]


COVERAGE_MARKER = "<!-- tables below are generated -->"


def kept_coverage_text(path):
    """Return the lines above the marker in an existing 02-coverage.md. Those belong to the orchestrator."""
    lines = path.read_text(encoding="utf-8-sig").split("\n") if path.exists() else []
    return lines[:lines.index(COVERAGE_MARKER)] if COVERAGE_MARKER in lines else []


def coverage(run, all_rows, events_all, merged, bad, force, cfg_lanes, warnings):
    workstreams = {p.name for p in (run / "research").iterdir() if p.is_dir() and p.name != "merged"}
    if (run / "run.json").exists():
        try:
            workstreams |= set(json.loads((run / "run.json").read_text(encoding="utf-8-sig")).get("workstreams", {}))
        except (ValueError, AttributeError) as e:
            warnings.append(f"run.json is unreadable, workstream list comes from folders only ({e})")
    out = ["# Coverage", "", f"Rows after dedupe: {len(all_rows)}. Rows merged away: {sum(merged.values())}.", "",
           "## Per workstream", "",
           "| Workstream | Rows | Merged away | Fact | Inference | High | Medium | Low | Primary | Aggregator | Last progress |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    no_progress, by_ws = [], defaultdict(list)
    for r in all_rows:
        by_ws[r["ws"]].append(r)
    for ws in sorted(workstreams):
        path = run / "research" / ws / "progress.jsonl"
        ts = last_progress(path, warnings) if path.exists() else None
        if not path.exists():
            no_progress.append(ws)
        cells = [ws, len(by_ws[ws]), merged[ws]] + stat_cells(by_ws[ws]) + [ts or "none"]
        out.append("| " + " | ".join(map(str, cells)) + " |")
    out += ["", "## Per lane", "", "| Lane | Rows | Fact | Inference | High | Medium | Low | Primary | Aggregator |",
            "|---|---|---|---|---|---|---|---|---|"]
    empty = []
    for lane in sorted(cfg_lanes):
        rows = [r for r in events_all if r["lane"] == lane]
        if not rows:
            empty.append(lane)
        out.append("| " + " | ".join(map(str, [lane, len(rows)] + stat_cells(rows))) + " |")
    low = sorted(r["id"] for r in all_rows if r.get("confidence") == "low")
    out += ["", "## Low-confidence rows", "", ", ".join(low) or "None.", "",
            "## Workstreams with no progress.jsonl", "", ", ".join(no_progress) or "None.", "",
            "## Empty lanes", "", ", ".join(empty) or "None.", "", "## Row expectation from probe.json", ""]
    probe = run / "probe.json"
    expected = None
    if probe.exists():
        try:
            expected = json.loads(probe.read_text(encoding="utf-8-sig")).get("expected_rows")
        except (ValueError, AttributeError) as e:
            warnings.append(f"probe.json is unreadable ({e})")
    if isinstance(expected, dict):
        out += [f"- {ws}: expected {n}, found {len(by_ws[ws])}" for ws, n in sorted(expected.items())]
    elif expected is not None:
        out.append(f"- Total: expected {expected}, found {len(all_rows)}")
    else:
        out.append("No expected_rows in probe.json, or no probe.json.")
    if force and bad:
        out += ["", f"## Dropped rows ({len(bad)}, --force)", ""] + [f"- {b}" for b in bad]
    if warnings:
        out += ["", "## Warnings", ""] + [f"- {w}" for w in warnings]
    path = run / "02-coverage.md"
    path.write_text("\n".join(kept_coverage_text(path) + [COVERAGE_MARKER] + out) + "\n", encoding="utf-8", newline="\n")
    return low, no_progress, empty


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--force", action="store_true", help="drop invalid rows, report them, and continue")
    args = ap.parse_args()
    run = args.run_dir
    if not (run / "research").is_dir():
        die(f"{run} has no research/ folder, so it is not a run folder")
    cfg = load_config(run)
    good, bad = read_rows(run, cfg)
    if bad:
        print(f"{'DROPPED' if args.force else 'INVALID'} ROWS ({len(bad)}):")
        for b in bad:
            print(f"  {b}")
        if not args.force:
            print("Nothing written. Fix the rows, or rerun with --force to drop them.")
            return 1
    if not any(good.values()):
        die(f"no valid rows found under {run / 'research'}")
    events, merged = dedupe(good["events.jsonl"])
    key = lambda r: (r["date"], r["id"])
    outputs = {"events.json": sorted((e for e in events if e["kind"] != "metric"), key=key),
               "metrics.json": sorted((e for e in events if e["kind"] == "metric"), key=key),
               "gtm.json": sorted(good["gtm_actions.jsonl"], key=key),
               "competitors.json": sorted(good["profiles.jsonl"], key=lambda r: r["id"]),
               "landscape.json": sorted(good["landscape.jsonl"], key=lambda r: r["id"])}
    (run / "research" / "merged").mkdir(exist_ok=True)
    for name, rows in outputs.items():
        (run / "research" / "merged" / name).write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n",
                                                        encoding="utf-8", newline="\n")
        print(f"research/merged/{name}: {len(rows)} rows")
    all_rows = events + good["gtm_actions.jsonl"] + good["profiles.jsonl"] + good["landscape.jsonl"]
    warnings = []
    low, no_progress, empty = coverage(run, all_rows, events, merged, bad, args.force, cfg["lanes"], warnings)
    for w in warnings:
        print(f"WARNING: {w}")
    print(f"02-coverage.md: merged away {sum(merged.values())}, low confidence {len(low)}, "
          f"no progress file {len(no_progress)}, empty lanes {len(empty)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
