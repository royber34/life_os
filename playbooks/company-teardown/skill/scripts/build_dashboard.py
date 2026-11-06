#!/usr/bin/env python3
"""Assemble, validate and build the single-file teardown dashboard.

    python -I build_dashboard.py assemble <run-dir>
    python -I build_dashboard.py validate <run-dir>
    python -I build_dashboard.py build <run-dir>

Standard library only. The field contract is in references/presentation.md.
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

MAX_BYTES = 5 * 1024 * 1024
EM_DASH = "\u2014"
TEMPLATE = Path(__file__).resolve().parent.parent / "template"
TABS = ["moves", "overview", "sowhat", "timeline", "gtm", "competition", "market", "deepdive"]
FAMILIES = {"product", "growth", "money", "people", "risk", "turning_point"}
KPI_AGGS = {"last", "sum7", "max", "stat"}
FORMATS = {"int", "usd", "pct", "text", "compact"}
BASIS = {"fact", "inference"}
CONFIDENCE = {"high", "medium", "low"}
LEVELS = {"high", "medium", "low"}
PARTNER_LEVELS = {"high", "medium", "low", "none"}
COVERAGE = {"yes", "partial", "no"}
SO_WHAT_KINDS = {"verdict", "lesson", "risk", "implication", "call", "next", "flip"}
MARKET_KEYS = ["title", "domains", "tiers", "fits", "supply", "demand"]

# Phrasing the playbook does not publish. Checked sentence by sentence, ignoring case.
BANNED_PHRASES = [
    r"\bnot\s+just\b.*\bbut\b",
    r"\bnot\s+only\b.*\bbut\b",
    r"\bnot\s+merely\b.*\bbut\b",
    r"\bnot\s+(?:a|an|the|about|because|for|in|on|to)?\s*[\w'-]+(?:\s+[\w'-]+){0,5},?\s+but\s",
    r"\bit'?s\s+not\b.*\bit'?s\b",
    r"\bthis\s+isn'?t\b.*\bit'?s\b",
    r"\bthat\s+isn'?t\b.*\bit'?s\b",
    r"\bthe\s+hard\s+part\s+was\s+never\b",
    r"\bwas\s+never\s+about\b",
]

TOKEN_RE = re.compile(r"\{\{\s*([a-zA-Z_]+)\s*:\s*([^}]*?)\s*\}\}")
OPEN_TOKEN_RE = re.compile(r"\{\{|\}\}")
CITE_RE = re.compile(r"\[c:([^\]\s]+)\]")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DOC_RE = re.compile(r"^0[3-9]-.*\.md$")


# ---------------------------------------------------------------- reading

def read_json(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path):
    if not path.exists():
        return []
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as err:
            raise SystemExit(f"{path.name} line {n}: bad JSON: {err}")
    return rows


def bundle_path(run):
    """A run has dashboard/bundle.json. The example folder has bundle-sample.json."""
    main = run / "dashboard" / "bundle.json"
    sample = run / "bundle-sample.json"
    return main if main.exists() or not sample.exists() else sample


# ---------------------------------------------------------------- formatting

def compact(v):
    v = float(v)
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= limit:
            text = f"{v / limit:.1f}".rstrip("0").rstrip(".")
            return text + suffix
    return f"{v:.1f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))


def fmt_value(v, fmt):
    if v is None:
        return None
    if fmt == "text":
        return str(v)
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    if fmt == "usd":
        return "$" + compact(v)
    if fmt == "pct":
        return f"{v * 100:.0f}%"
    if fmt == "compact":
        return compact(v)
    return f"{v:,.0f}" if v == int(v) else f"{v:,.1f}"


# ---------------------------------------------------------------- stats

def metric_rows(metrics, name):
    return sorted((r for r in metrics if r.get("metric_name") == name and r.get("metric_value") is not None), key=lambda r: r.get("date") or "")


def metric_agg(metrics, name, agg):
    rows = metric_rows(metrics, name)
    if not rows:
        return None, None
    if agg == "last":
        return float(rows[-1]["metric_value"]), rows[-1]["date"]
    if agg == "sum7":
        week = rows[-7:]
        return sum(float(r["metric_value"]) for r in week), week[-1]["date"]
    if agg == "max":
        top = max(rows, key=lambda r: float(r["metric_value"]))
        return float(top["metric_value"]), top["date"]
    return None, None


def stat_entry(value, fmt, date=None):
    return {"value": value, "text": fmt_value(value, fmt), "fmt": fmt, "date": date, "missing": value is None}


def walk_strings(node, path=""):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, f"{path}[{i}]")


def custom_stat(spec, sources, done):
    """One config.stats entry: {id, from, where, since, contains, agg, of, fmt}."""
    rows = sources.get(spec.get("from"), [])
    where = spec.get("where") or {}
    since = spec.get("since")
    contains = spec.get("contains") or {}
    needle = str(contains.get("text") or "").lower()
    def keep(r):
        for field, allowed in where.items():
            if r.get(field) not in allowed:
                return False
        if since and str(r.get("date") or "") < since:
            return False
        if needle and needle not in " ".join(str(r.get(f) or "") for f in contains.get("fields") or []).lower():
            return False
        if spec.get("positive") and not float(r.get(spec["positive"]) or 0) > 0:
            return False
        return True
    picked = [r for r in rows if keep(r)]
    agg = spec.get("agg") or "count"
    if agg == "count":
        value = len(picked)
    elif agg.startswith("sum:"):
        value = sum(float(r.get(agg[4:]) or 0) for r in picked)
    else:
        value = None
    of = spec.get("of")
    if of is not None:
        base = (done.get(of) or {}).get("value")
        value = value / base if value is not None and base else None
    return value


def compute_stats(config, prose, library, events, metrics, gtm, competitors, landscape, cutoff):
    stats = {
        "events_total": stat_entry(len(events), "int"),
        "metrics_total": stat_entry(len(metrics), "int"),
        "gtm_actions": stat_entry(len(gtm), "int"),
        "gtm_views_total": stat_entry(sum(float(r.get("views") or 0) for r in gtm), "compact"),
        "competitors_total": stat_entry(len(competitors), "int"),
        "landscape_total": stat_entry(len(landscape), "int"),
        "lanes_total": stat_entry(len(config.get("lanes") or []), "int"),
        "docs_total": stat_entry(len({r["doc"] for r in library}), "int"),
        "cutoff": stat_entry(cutoff, "text"),
    }
    sources = {"events": events, "metrics": metrics, "gtm": gtm, "competitors": competitors, "landscape": landscape}
    for spec in config.get("stats") or []:
        value = custom_stat(spec, sources, stats)
        stats[spec["id"]] = stat_entry(value, spec.get("fmt") or "int")
    for k in config.get("kpis") or []:
        fmt = k.get("fmt") or "int"
        if k.get("agg") == "stat":
            base = stats.get(k.get("metric")) or {}
            entry = stat_entry(base.get("value"), fmt)
        else:
            value, date = metric_agg(metrics, k.get("metric"), k.get("agg"))
            entry = stat_entry(value, fmt, date)
            if k.get("metric_high"):
                high, _ = metric_agg(metrics, k["metric_high"], k.get("agg"))
                if value is None or high is None:
                    entry = stat_entry(None, fmt)
                else:
                    entry["high"] = high
                    entry["text"] = f"{fmt_value(value, fmt)}\u2013{fmt_value(high, fmt)}"
        stats[f"kpi:{k.get('label')}"] = entry
    # Metric tokens in prose such as {{stat:last.github_stars}}, computed on demand.
    texts = [t for _, t in walk_strings(prose)] + [r["md"] for r in library]
    for text in texts:
        for kind, name in TOKEN_RE.findall(text):
            if kind == "stat" and name not in stats and "." in name:
                agg, metric = name.split(".", 1)
                value, date = metric_agg(metrics, metric, agg)
                unit = next((r.get("metric_unit") for r in metrics if r.get("metric_name") == metric), None)
                stats[name] = stat_entry(value, "usd" if unit == "usd" else "int", date)
    return stats


# ---------------------------------------------------------------- assemble

def split_markdown(text):
    """Split on H1 and H2, outside code fences. Text before the first heading is its own section."""
    sections, current, heading, level, fence = [], [], "", 1, False
    def close():
        body = "\n".join(current).strip()
        if body:
            sections.append((heading, level, body))
    for line in text.replace("\r", "").split("\n"):
        if line.startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^(#{1,2})\s+(.*)$", line)
        if m:
            close()
            current, heading, level = [], m.group(2).strip(), len(m.group(1))
        current.append(line)
    close()
    return sections


def humanise(stem):
    return re.sub(r"^\d+-", "", stem).replace("-", " ").replace("_", " ").strip().capitalize()


def load_library(run):
    rows = []
    def add(path, slug, group, order):
        sections = split_markdown(path.read_text(encoding="utf-8"))
        h1 = next((h for h, lv, _ in sections if lv == 1 and h), None)
        title = h1 or humanise(path.stem if path.name != "section.md" else path.parent.name)
        for idx, (heading, level, md) in enumerate(sections):
            rows.append({"id": f"{slug}-{idx}", "doc": slug, "doc_title": title, "group": group, "doc_order": order, "idx": idx, "heading": heading, "level": level, "md": md})
    for path in sorted(run.glob("*.md")):
        if DOC_RE.match(path.name):
            add(path, path.stem, "Reports", int(path.name[:2]))
    for n, path in enumerate(sorted(run.glob("research/*/section.md"))):
        add(path, path.parent.name, "Research", 100 + n)
    return rows


def load_claims(run, events, metrics, gtm, cited):
    verify = run / "verify"
    source = {}
    for r in read_jsonl(verify / "ledger.jsonl"):
        source[r.get("id")] = r.get("source")
    for path in run.glob("research/*/claims.jsonl"):
        for r in read_jsonl(path):
            source.setdefault(r.get("id"), r.get("source"))
    for r in list(events) + list(metrics) + list(gtm):
        source.setdefault(r.get("id"), r.get("source"))
    status = {r.get("id"): r.get("status") for r in read_jsonl(verify / "verdicts.jsonl")}
    return {i: {"source": source[i], "status": status.get(i, "unchecked")} for i in sorted(cited) if i in source}


def load_verification(run, cutoff):
    """Returns None when no verification has run, and the page then says so."""
    verify = run / "verify"
    report = read_json(verify / "report.json")
    # A row re-checked later has several verdict lines, and only the last one counts.
    verdicts = list({r.get("id"): r for r in read_jsonl(verify / "verdicts.jsonl")}.values())
    if report is None and not verdicts:
        return None
    report = report or {}
    counts = {}
    for r in verdicts:
        counts[r.get("status")] = counts.get(r.get("status"), 0) + 1
    low, high = report.get("interval_low"), report.get("interval_high")
    workstreams = {}
    for ws, row in (report.get("per_workstream") or {}).items():
        workstreams[ws] = f"{row.get('label')} ({row.get('checked')} checked, {row.get('wrong')} wrong)"
    return {
        "label": report.get("label") or "partial: no report written",
        "claims_total": report.get("claims_total", len(read_jsonl(verify / "ledger.jsonl")) or None),
        "checked": len(verdicts) or None,
        "random_checked": report.get("random_checked"),
        "load_bearing_checked": report.get("load_bearing_checked"),
        "counts": counts,
        "wrong_rate": report.get("wrong_rate"),
        "findings": report.get("findings") or [],
        "wrong_rate_ci": [low, high] if low is not None and high is not None else None,
        "unreachable": report.get("unreachable", counts.get("unreachable")),
        "workstreams": workstreams,
        "cutoff": report.get("cutoff") or cutoff,
    }


def channel_of(row, channels):
    for c in channels:
        match = c.get("match") or {}
        chans, actors = match.get("channel") or [], match.get("actor") or []
        if chans and row.get("channel") not in chans:
            continue
        if actors and row.get("actor") not in actors:
            continue
        return c["id"]
    return None


METRIC_FIELDS = ["id", "date", "metric_name", "metric_value", "metric_unit", "person", "title", "basis", "confidence"]


def assemble(run):
    config = read_json(run / "config.json")
    if config is None:
        raise SystemExit(f"Missing config.json in {run.name}")
    prose = read_json(run / "dashboard" / "prose.json")
    if prose is None:
        raise SystemExit("Missing dashboard/prose.json")
    merged = run / "research" / "merged"
    raw_events = read_json(merged / "events.json", [])
    metrics = list(read_json(merged / "metrics.json", []))
    events = []
    for r in raw_events:  # A merged file may still hold metric rows. They belong in metrics.
        (metrics if r.get("kind") == "metric" else events).append(r)
    gtm = read_json(merged / "gtm.json", [])
    competitors = read_json(merged / "competitors.json", [])
    landscape = read_json(merged / "landscape.json", [])
    library = load_library(run)

    labels = {l["id"]: l.get("label") for l in config.get("lanes") or []}
    groups = {p["name"]: p.get("group") for p in config.get("people") or []}
    for r in events:
        r["lane_label"] = labels.get(r.get("lane"))
        r["person_group"] = groups.get(r.get("person"))
    for r in gtm:
        r["row"] = channel_of(r, config.get("channels") or [])

    cited = set()
    for _, text in list(walk_strings(prose)) + [("", r["md"]) for r in library]:
        cited.update(CITE_RE.findall(text))
    claims = load_claims(run, events, metrics, gtm, cited)
    slim_metrics = [{k: r.get(k) for k in METRIC_FIELDS} for r in metrics]

    cutoff = config.get("cutoff")
    dates = [r.get("date") for r in events + slim_metrics + gtm if r.get("date")]
    dates += [r.get("date_end") for r in events if r.get("date_end")]
    if cutoff:
        dates.append(cutoff)
    good = sorted(d for d in dates if is_date(d))
    data_range = [good[0], good[-1]] if good else [cutoff, cutoff]

    stats = compute_stats(config, prose, library, events, slim_metrics, gtm, competitors, landscape, cutoff)
    bundle = {
        "meta": {
            "name": config.get("name"), "lede": config.get("lede"), "cutoff": cutoff, "data_range": data_range,
            "counts": {
                "events": len(events), "metrics": len(slim_metrics), "gtm": len(gtm), "competitors": len(competitors), "landscape": len(landscape),
                "library_docs": len({r["doc"] for r in library}), "library_sections": len(library), "claims": len(claims),
            },
        },
        "config": config, "prose": prose, "stats": stats, "events": events, "metrics": slim_metrics, "gtm": gtm,
        "competitors": competitors, "landscape": landscape, "library": library, "claims": claims,
        "verification": load_verification(run, cutoff),
    }
    impact_rows, impact_series = [], []
    for path in sorted(run.glob("research/*/campaign_impact.jsonl")):
        impact_rows += read_jsonl(path)
        series_path = path.with_name("series.json")
        if series_path.exists():
            impact_series += json.loads(series_path.read_text(encoding="utf-8"))
    if impact_rows:
        wanted = {x for v in (config.get("impact") or {}).get("views", []) for x in [v.get("series"), *v.get("controls", [])]}
        bundle_impact = {"rows": impact_rows, "series": [x for x in impact_series if x.get("metric") in wanted]}
    else:
        bundle_impact = None
    if bundle_impact:
        bundle["impact"] = bundle_impact
    out = run / "dashboard" / "bundle.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    c = bundle["meta"]["counts"]
    print(f"Wrote dashboard/bundle.json: {out.stat().st_size:,} bytes; {c['events']} events, {c['metrics']} metrics, {c['gtm']} gtm, {c['competitors']} competitors, {c['landscape']} landscape, {c['library_docs']} docs, {c['claims']} claims")


# ---------------------------------------------------------------- validate

def is_date(s):
    if not isinstance(s, str) or not DATE_RE.match(s):
        return False
    try:
        dt.date.fromisoformat(s)
        return True
    except ValueError:
        return False


def ids_unique(rows, name, problems):
    seen = set()
    for r in rows:
        i = r.get("id")
        if not i:
            problems.append(f"{name}: row without an id: {str(r)[:80]}")
        elif i in seen:
            problems.append(f"{name}: duplicate id {i}")
        seen.add(i)


def check_text(node, where, problems):
    for path, text in walk_strings(node, where):
        if EM_DASH in text:
            problems.append(f"{path}: em-dash character (U+2014)")
        for sentence in re.split(r"(?<=[.!?:;])\s+|\n+", text):
            for pattern in BANNED_PHRASES:
                if re.search(pattern, sentence, re.I):
                    problems.append(f'{path}: banned phrasing "{sentence.strip()[:90]}"')
                    break


def check_tokens(text, where, bundle, problems):
    stats = bundle.get("stats") or {}
    for kind, name in TOKEN_RE.findall(text):
        key = f"kpi:{name}" if kind == "kpi" else name
        if kind not in ("stat", "kpi"):
            problems.append(f"{where}: unknown token kind {{{{{kind}:{name}}}}}")
        elif key not in stats or stats[key].get("missing"):
            problems.append(f"{where}: unresolved token {{{{{kind}:{name}}}}}")
    if OPEN_TOKEN_RE.search(TOKEN_RE.sub("", text)):
        problems.append(f"{where}: malformed token in text")
    for i in CITE_RE.findall(text):
        if i not in (bundle.get("claims") or {}):
            problems.append(f"{where}: claim id {i} is absent")


def check_goto(target, where, docs, market, problems):
    if target is None:
        return
    text = str(target)
    if text.startswith("doc:"):
        if text[4:] not in docs:
            problems.append(f"{where}: doc slug {text[4:]} is absent")
    elif text not in TABS:
        problems.append(f"{where}: goto {text} is not a tab")
    elif text == "market" and not market:
        problems.append(f"{where}: goto market, and config.market is null")


def check_market(market, problems):
    missing = [k for k in MARKET_KEYS if not market.get(k)]
    if missing:
        problems.append(f"config.market: partial block, missing or empty: {', '.join(missing)}")
        return
    domains = {x.get("id") for x in market["domains"]}
    tiers = {x.get("id") for x in market["tiers"]}
    fits = {x.get("id") for x in market["fits"]}
    ids_unique(market["supply"], "market.supply", problems)
    ids_unique(market["demand"], "market.demand", problems)
    supply_ids = {r.get("id") for r in market["supply"]}
    for r in market["supply"]:
        if r.get("domain") not in domains:
            problems.append(f"market.supply {r.get('id')}: domain {r.get('domain')} is absent from config")
        if r.get("access_tier") not in tiers:
            problems.append(f"market.supply {r.get('id')}: access_tier {r.get('access_tier')} is absent from config")
        if r.get("fit") not in fits:
            problems.append(f"market.supply {r.get('id')}: fit {r.get('fit')} is absent from config")
    for r in market["demand"]:
        if not isinstance(r.get("key_supply"), list):
            problems.append(f"market.demand {r.get('id')}: key_supply must be a list of supply ids")
            continue
        for i in r["key_supply"]:
            if i not in supply_ids:
                problems.append(f"market.demand {r.get('id')}: supply id {i} is absent")
        if not isinstance(r.get("priority_score"), (int, float)):
            problems.append(f"market.demand {r.get('id')}: priority_score must be a number")


def validate_bundle(b):
    problems, warnings = [], []
    for key in ("meta", "config", "prose", "stats", "events", "metrics", "gtm", "competitors", "landscape", "library", "claims"):
        if key not in b:
            problems.append(f"bundle: missing field {key}")
    if problems:
        return problems, warnings
    cfg, prose = b["config"], b["prose"]
    events, metrics, gtm = b["events"], b["metrics"], b["gtm"]
    competitors, landscape, library = b["competitors"], b["landscape"], b["library"]

    for key in ("name", "lede", "cutoff", "lanes", "periods", "default_period"):
        if cfg.get(key) in (None, "", []):
            problems.append(f"config.{key}: missing or empty")
    if cfg.get("cutoff") and not is_date(cfg["cutoff"]):
        problems.append(f"config.cutoff: bad date {cfg['cutoff']}")
    period_ids = set()
    for per in cfg.get("periods") or []:
        period_ids.add(per.get("id"))
        for k in ("from", "to"):
            if per.get(k) is not None and not is_date(per[k]):
                problems.append(f"config.periods {per.get('id')}: bad {k} date {per[k]}")
        if per.get("from") and per.get("to") and per["from"] > per["to"]:
            problems.append(f"config.periods {per.get('id')}: from is after to")
    if cfg.get("default_period") not in period_ids:
        problems.append(f"config.default_period {cfg.get('default_period')} is not a listed period")

    lanes = {l.get("id") for l in cfg.get("lanes") or []}
    for l in cfg.get("lanes") or []:
        if l.get("family") not in FAMILIES:
            problems.append(f"config.lanes {l.get('id')}: family {l.get('family')} is not one of {sorted(FAMILIES)}")

    # Rows
    ids_unique(events, "events", problems)
    ids_unique(gtm, "gtm", problems)
    ids_unique(competitors, "competitors", problems)
    ids_unique(landscape, "landscape", problems)
    for r in events:
        rid = r.get("id")
        if r.get("lane") not in lanes:
            problems.append(f"events {rid}: lane {r.get('lane')} is absent from config.lanes")
        if not is_date(r.get("date")):
            problems.append(f"events {rid}: bad date {r.get('date')}")
        if r.get("date_end") is not None and not is_date(r["date_end"]):
            problems.append(f"events {rid}: bad date_end {r['date_end']}")
        if r.get("kind") not in ("event", "span"):
            problems.append(f"events {rid}: kind {r.get('kind')} is not event or span")
        if r.get("basis") not in BASIS:
            problems.append(f"events {rid}: basis {r.get('basis')}")
        if r.get("confidence") not in CONFIDENCE:
            problems.append(f"events {rid}: confidence {r.get('confidence')}")
    for r in metrics:
        if not is_date(r.get("date")):
            problems.append(f"metrics {r.get('id')}: bad date {r.get('date')}")
        if not isinstance(r.get("metric_value"), (int, float)):
            problems.append(f"metrics {r.get('id')}: metric_value is not a number")
    for r in gtm:
        if not is_date(r.get("date")):
            problems.append(f"gtm {r.get('id')}: bad date {r.get('date')}")
        if not r.get("row"):
            problems.append(f"gtm {r.get('id')}: channel {r.get('channel')} and actor {r.get('actor')} match no config.channels entry")
        if r.get("basis") not in BASIS:
            problems.append(f"gtm {r.get('id')}: basis {r.get('basis')}")
        if r.get("confidence") not in CONFIDENCE:
            problems.append(f"gtm {r.get('id')}: confidence {r.get('confidence')}")

    # Config references into the data
    metric_names = {r.get("metric_name") for r in metrics}
    channel_ids = {c.get("id") for c in cfg.get("channels") or []}
    for c in cfg.get("channels") or []:
        if not any(r.get("row") == c.get("id") for r in gtm):
            warnings.append(f"config.channels {c.get('id')}: no gtm row uses it")
    for r in gtm:
        if r.get("row") and r["row"] not in channel_ids:
            problems.append(f"gtm {r.get('id')}: row {r['row']} is absent from config.channels")
    for l in lanes:
        if not any(r.get("lane") == l for r in events):
            warnings.append(f"config.lanes {l}: no event uses it")
    for card in cfg.get("metric_cards") or []:
        if card.get("kind") not in ("line", "bar", "range"):
            problems.append(f"metric_cards {card.get('id')}: kind {card.get('kind')}")
        for s in card.get("series") or []:
            if s.get("metric") not in metric_names:
                problems.append(f"metric_cards {card.get('id')}: metric {s.get('metric')} is absent from the data")
            elif s.get("person") and not any(r.get("metric_name") == s["metric"] and r.get("person") == s["person"] for r in metrics):
                problems.append(f"metric_cards {card.get('id')}: no {s['metric']} rows for person {s['person']}")
        if card.get("kind") == "range" and len(card.get("series") or []) != 2:
            problems.append(f"metric_cards {card.get('id')}: a range card needs two series, low then high")
    for c in cfg.get("response_curves") or []:
        if c.get("metric") not in metric_names:
            problems.append(f"response_curves {c.get('id')}: metric {c.get('metric')} is absent from the data")
    for k in cfg.get("kpis") or []:
        label = k.get("label")
        if k.get("agg") not in KPI_AGGS:
            problems.append(f"kpis {label}: agg {k.get('agg')} is not one of {sorted(KPI_AGGS)}")
        if k.get("fmt") not in FORMATS:
            problems.append(f"kpis {label}: fmt {k.get('fmt')} is not one of {sorted(FORMATS)}")
        if k.get("agg") == "stat":
            if k.get("metric") not in b["stats"]:
                problems.append(f"kpis {label}: stat {k.get('metric')} is absent")
        else:
            for key in ("metric", "metric_high"):
                if k.get(key) and k[key] not in metric_names:
                    problems.append(f"kpis {label}: metric {k[key]} is absent from the data")
        stat = b["stats"].get(f"kpi:{label}")
        if not stat or stat.get("missing"):
            problems.append(f"kpis {label}: no value computed, the page would show a missing marker")
    for spec in cfg.get("stats") or []:
        s = b["stats"].get(spec.get("id"))
        if not s or s.get("missing"):
            problems.append(f"config.stats {spec.get('id')}: no value computed")

    # Competition
    comp = cfg.get("competition") or {}
    groups = {g.get("id") for g in comp.get("groups") or []}
    scores = {s.get("id") for s in comp.get("scores") or []}
    components = {c.get("id") for c in comp.get("components") or []}
    if scores:
        for key in ("default_x", "default_y"):
            if comp.get(key) not in scores:
                problems.append(f"competition.{key} {comp.get(key)} is not a score id")
    for r in competitors:
        rid = r.get("id")
        if r.get("group") not in groups:
            problems.append(f"competitors {rid}: group {r.get('group')} is absent from config")
        for k, v in (r.get("scores") or {}).items():
            if k not in scores:
                problems.append(f"competitors {rid}: score id {k} is absent from config")
            if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 5:
                problems.append(f"competitors {rid}: score {k} must be an integer 0 to 5, got {v}")
        for k in scores:
            if k not in (r.get("scores") or {}):
                problems.append(f"competitors {rid}: score {k} is missing")
        for k, v in (r.get("coverage") or {}).items():
            if k not in components:
                problems.append(f"competitors {rid}: coverage id {k} is absent from config")
            if v not in COVERAGE:
                problems.append(f"competitors {rid}: coverage {k} value {v}")
        if r.get("threat_level") not in LEVELS:
            problems.append(f"competitors {rid}: threat_level {r.get('threat_level')}")
        if r.get("partner_level") not in PARTNER_LEVELS:
            problems.append(f"competitors {rid}: partner_level {r.get('partner_level')}")
        for m in r.get("recent_moves") or []:
            if not is_date(m.get("date")):
                problems.append(f"competitors {rid}: recent move has bad date {m.get('date')}")
    for r in landscape:
        if r.get("group") not in groups:
            problems.append(f"landscape {r.get('id')}: group {r.get('group')} is absent from config")

    # Market
    if cfg.get("market") is not None:
        check_market(cfg["market"], problems)

    # Prose and library
    docs = {r.get("doc") for r in library}
    check_text(cfg, "config", problems)
    check_text(prose, "prose", problems)
    for path, text in walk_strings(prose, "prose"):
        check_tokens(text, path, b, problems)
    for s in library:
        check_tokens(s.get("md", ""), f"library {s.get('id')}", b, problems)
    summary = (prose.get("overview") or {}).get("summary") or []
    for i, s in enumerate(summary):
        check_goto(s.get("goto"), f"prose.overview.summary[{i}]", docs, cfg.get("market"), problems)
    for i, s in enumerate(prose.get("so_what") or []):
        check_goto(s.get("goto"), f"prose.so_what[{i}]", docs, cfg.get("market"), problems)
        if s.get("kind") not in SO_WHAT_KINDS:
            problems.append(f"prose.so_what[{i}]: kind {s.get('kind')} is not one of {sorted(SO_WHAT_KINDS)}")

    check_moves(prose, docs, cfg.get("market"), problems)
    check_insights(prose, cfg, b.get("impact"), problems)

    # Size: the page is the bundle plus the template.
    template_size = sum(p.stat().st_size for p in TEMPLATE.iterdir() if p.is_file() and p.suffix in (".js", ".css", ".html"))
    size = len(json.dumps(b, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) + template_size
    if size > MAX_BYTES:
        problems.append(f"output would be {size:,} bytes, over the {MAX_BYTES:,} byte limit")
    return problems, warnings


def check_insights(prose, cfg, impact, problems):
    """The go-to-market insights, the impact study and the connections list are optional, and must be complete when present."""
    def items(where, lst):
        for i, it in enumerate(lst or []):
            for key in ("title", "evidence", "proof"):
                if not it.get(key):
                    problems.append(f"{where}[{i}]: {key} is required")
    ins = (prose.get("gtm") or {}).get("insights")
    if ins:
        if not ins.get("lenses"):
            problems.append("prose.gtm.insights: lenses are required")
        for lens in ins.get("lenses") or []:
            for col in ("working", "not", "open"):
                items(f"prose.gtm.insights {lens.get('id')}.{col}", lens.get(col))
                for i, it in enumerate(lens.get(col) or []):
                    if not it.get("use"):
                        problems.append(f"prose.gtm.insights {lens.get('id')}.{col}[{i}]: say how a team can use it")
        for path, text in walk_strings(ins, "prose.gtm.insights"):
            if re.search(r"\b(you|your|yours|you'd|you're|you've|you'll)\b", text, re.I):
                problems.append(f"{path}: keep the voice neutral, instead of addressing the reader")
    moves = prose.get("moves")
    if moves:
        for key in ("opportunities", "working", "not_working"):
            if not moves.get(key):
                problems.append(f"prose.moves.{key} is required: the So what tab runs moves, opportunities, then what is working and what is not")
            items(f"prose.moves.{key}", moves.get(key))
            ids = {m.get("id") for m in moves.get("items") or []}
            for i, it in enumerate(moves.get(key) or []):
                for mid in it.get("moves") or []:
                    if mid not in ids:
                        problems.append(f"prose.moves.{key}[{i}]: move {mid} does not exist")
    conn = (prose.get("overview") or {}).get("connections")
    if conn:
        for i, r in enumerate(conn.get("rows") or []):
            if not r.get("tool") or not r.get("adds") or not r.get("settles"):
                problems.append(f"prose.overview.connections.rows[{i}]: tool, adds and settles are required")
    if impact:
        have = {s.get("metric") for s in impact.get("series") or []}
        for v in (cfg.get("impact") or {}).get("views") or []:
            for name in [v.get("series"), *(v.get("controls") or [])]:
                if name not in have:
                    problems.append(f"config.impact.views {v.get('id')}: series {name} is absent")
        if not (cfg.get("impact") or {}).get("views"):
            problems.append("config.impact.views is required when a campaign impact study exists")


MOVE_TYPES = {"find_out", "double_down", "quick_win", "dealer", "budget", "bet"}
MOVE_REQUIRED = ("id", "short", "type", "channel", "when", "depends", "title", "what", "why", "impact", "effort", "confidence", "if_wrong", "test", "watch")
LEVELS = {"high", "medium", "low"}
EVIDENCE_LEVELS = {"strong", "medium", "thin"}
PRESCRIPTIVE = ("written for", "first job", "the company should", "the company can", "whoever runs", "what to do first", "first thing")
SOURCE_KINDS = {"Measured", "Public record", "Vendor estimate", "Assumed model", "Judgement", "Mixed"}
BAND_TABS = {"overview", "sowhat", "timeline", "gtm", "competition", "market", "deepdive"}


def check_moves(prose, docs, market, problems):
    """prose.moves is optional for older runs. When present, every move must be complete enough to act on."""
    for tab in prose.get("bands") or {}:
        if tab not in BAND_TABS:
            problems.append(f"prose.bands: {tab} is not a tab with a band")
    moves = prose.get("moves")
    if moves is None:
        return
    if not (moves.get("answer") or {}).get("body"):
        problems.append("prose.moves.answer: body is required")
    if not 3 <= len(moves.get("headlines") or []) <= 6:
        problems.append("prose.moves.headlines: give 3 to 6 hard findings, so the tab opens on evidence")
    for i, h in enumerate(moves.get("headlines") or []):
        if not h.get("value") or not h.get("label") or h.get("kind") not in SOURCE_KINDS:
            problems.append(f"prose.moves.headlines[{i}]: value, label and a kind from {sorted(SOURCE_KINDS)} are required")
    if not moves.get("rules"):
        problems.append("prose.moves.rules: give the if-then decision rules")
    if not moves.get("data_request"):
        problems.append("prose.moves.data_request: list the internal data in one place")
    for path, text in walk_strings(moves, "prose.moves"):
        for phrase in PRESCRIPTIVE:
            if phrase in text.lower():
                problems.append(f"{path}: \"{phrase}\" reads as an instruction or names the reader. Describe the area instead")
        if re.search(r"\b(you|your|yours|you'd|you're|you've|you'll)\b", text, re.I) and not path.endswith(".test_quote"):
            problems.append(f"{path}: keep the voice descriptive, instead of addressing the reader")
    swot = moves.get("swot") or {}
    for quad in ("strengths", "weaknesses", "opportunities", "threats"):
        if not swot.get(quad):
            problems.append(f"prose.moves.swot: {quad} is empty")
        for i, r in enumerate(swot.get(quad) or []):
            where = f"prose.moves.swot.{quad}[{i}]"
            if not r.get("point") or not r.get("so_what"):
                problems.append(f"{where}: point and so_what are required")
            if r.get("kind") not in SOURCE_KINDS:
                problems.append(f"{where}: kind {r.get('kind')} is not one of {sorted(SOURCE_KINDS)}")
            if r.get("evidence") not in EVIDENCE_LEVELS:
                problems.append(f"{where}: evidence {r.get('evidence')} is not one of {sorted(EVIDENCE_LEVELS)}")
    items = moves.get("items") or []
    if not items:
        problems.append("prose.moves.items is empty")
    ids = [m.get("id") for m in items]
    top = [m for m in items if m.get("priority")]
    if not 5 <= len(top) <= 10:
        problems.append(f"prose.moves.items: mark 5 to 10 as priority, found {len(top)}. The others stay in the expanded view")
    for m in top:
        if not m.get("trigger"):
            problems.append(f"prose.moves.items {m.get('id')}: a priority move needs a trigger, the decision rule")
    for dup in {x for x in ids if ids.count(x) > 1}:
        problems.append(f"prose.moves.items: duplicate id {dup}")
    for m in items:
        where = f"prose.moves.items {m.get('id')}"
        for key in MOVE_REQUIRED:
            if m.get(key) in (None, ""):
                problems.append(f"{where}: {key} is required")
        if m.get("type") not in MOVE_TYPES:
            problems.append(f"{where}: type {m.get('type')} is not one of {sorted(MOVE_TYPES)}")
        if m.get("confidence") not in LEVELS:
            problems.append(f"{where}: confidence {m.get('confidence')} is not one of {sorted(LEVELS)}")
        for key in ("impact", "effort"):
            if m.get(key) not in (1, 2, 3, 4, 5):
                problems.append(f"{where}: {key} must be a whole number from 1 to 5")
        if m.get("type") == "budget" and not (m.get("from") and m.get("to")):
            problems.append(f"{where}: a budget move needs from and to")
        check_goto(m.get("goto"), where, docs, market, problems)
    for i, x in enumerate(moves.get("crossings") or []):
        for mid in x.get("moves") or []:
            if mid not in ids:
                problems.append(f"prose.moves.crossings[{i}]: move {mid} does not exist")


def validate(run):
    path = bundle_path(run)
    if not path.exists():
        print(f"FAIL: no bundle at {path.name}. Run assemble first.")
        return False
    bundle = json.loads(path.read_text(encoding="utf-8"))
    problems, warnings = validate_bundle(bundle)
    for w in warnings:
        print(f"warning: {w}")
    if problems:
        print(f"FAIL: {len(problems)} problems")
        for p in problems:
            print(f"- {p}")
        return False
    print(f"OK: {path.name} passes ({len(warnings)} warnings)")
    return True


# ---------------------------------------------------------------- build

def script_safe(js):
    return js.replace("</script", "<\\/script")


def embed_json(bundle):
    text = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    # Every < is escaped, so </script> and <!-- in bundle text cannot end the block.
    return text.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def build(run):
    if not validate(run):
        return False
    bundle = json.loads(bundle_path(run).read_text(encoding="utf-8"))
    read = lambda name: (TEMPLATE / name).read_text(encoding="utf-8")
    title = re.sub(r"[<>&\"']", "", str(bundle["meta"].get("name") or "Teardown"))
    parts = {
        "/*__CSS__*/": read("dash.css"),
        "/*__D3__*/": script_safe(read("d3.v7.min.js")),
        "/*__SHIM__*/": script_safe(read("shim.js")),
        "/*__CORE__*/": script_safe(read("core.js")),
        "/*__TIMELINE__*/": script_safe(read("timeline.js")),
        "/*__GTM__*/": script_safe(read("gtm.js")),
        "/*__COMPETITION__*/": script_safe(read("competition.js")),
        "/*__MARKET__*/": script_safe(read("market.js")),
        "/*__LIBRARY__*/": script_safe(read("library.js")),
        "/*__IMPACT__*/": script_safe(read("impact.js")),
        "/*__MOVES__*/": script_safe(read("moves.js")),
        "__TITLE__": title,
        "__BUNDLE__": embed_json(bundle),
    }
    html = read("index.html")
    pattern = re.compile("|".join(re.escape(k) for k in parts))
    html = pattern.sub(lambda m: parts[m.group(0)], html)
    out = run / "dashboard" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8", newline="\n")
    size = out.stat().st_size
    print(f"Wrote dashboard/index.html: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")
    if size > MAX_BYTES:
        print(f"FAIL: output is over the {MAX_BYTES:,} byte limit")
        return False
    return True


def main(argv):
    if len(argv) != 3 or argv[1] not in ("assemble", "validate", "build"):
        print(__doc__)
        return 2
    run = Path(argv[2])
    if not run.is_dir():
        print(f"Not a folder: {run}")
        return 2
    if argv[1] == "assemble":
        assemble(run)
        return 0
    ok = validate(run) if argv[1] == "validate" else build(run)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
