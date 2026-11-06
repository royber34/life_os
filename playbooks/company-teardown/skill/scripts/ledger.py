#!/usr/bin/env python3
"""Claim ledger for a research run: merge, mark, sample, split, delta, report, check-citations.

Usage: python -I ledger.py <subcommand> <run-dir> [options]   (ledger.py <run-dir> <subcommand> also works)
Exit 0 on success, 1 when the subcommand found errors to fix, 2 on unusable input.
"""
import argparse, hashlib, json, math, random, re, sys
from collections import Counter, defaultdict
from pathlib import Path

LOAD_BEARING_DOCS = ["03-overview.md", "04-so-what.md", "08-decision-memo.md", "09-moves.md", "dashboard/prose.json"]  # a citation here makes a row load-bearing
DOC_NAME = re.compile(r"0[3-9]-.*\.md")
CITE = re.compile(r"\[c:([^\]]+)\]")
CLAIM_KEYS = "id text type value source source_kind basis confidence load_bearing".split()
VERDICT_KEYS = "id status evidence_quote checked_url note verifier".split()
STATUSES = {"confirmed", "partly", "wrong", "unreachable", "unsupported"}
ACTIONS = {"corrected", "downgraded", "removed"}
WRONG = {"wrong", "unsupported"}
SERIES_LIMIT = 20
ACCURATE, SECOND, DIRECTIONAL, NOT_RELIABLE = "ACCURATE TO SOURCES", "SECOND SAMPLE NEEDED", "DIRECTIONAL ONLY", "NOT RELIABLE YET"
TOO_FEW, MIN_WS_RATED = "TOO FEW TO RATE", 20


def die(msg, code=2):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def read_jsonl(path, keys=()):
    """Read one JSONL file. Every malformed line is listed, then the script exits."""
    rows, bad = [], []
    try:
        lines = path.read_bytes().split(b"\n")
    except OSError as e:
        die(f"cannot read {path}: {e}")
    for n, raw in enumerate(lines, 1):
        if raw.strip():
            try:
                row = json.loads(raw.decode("utf-8-sig"))
                missing = [k for k in keys if k not in row] if isinstance(row, dict) else ["(not an object)"]
                if missing:
                    bad.append(f"{path}:{n}: missing {', '.join(missing)}")
                else:
                    rows.append(row)
            except ValueError as e:
                bad.append(f"{path}:{n}: not valid UTF-8 JSON: {e}")
    if bad:
        die("malformed rows:\n  " + "\n  ".join(bad))
    return rows


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        die(f"cannot read {path}: {e}. Run the earlier pipeline step first.")


def write_jsonl(path, rows):
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def event_row(e):
    # An inference row keeps its reasoning in detail, and verifiers must not see a writer's reasoning.
    text = f"{e['date']}: {str(e['title']).rstrip('. ')}"
    if e["basis"] == "fact" and e.get("detail"):
        text += f". {e['detail']}"
    value = f"{e['metric_value']} {e.get('metric_unit') or ''}".strip() if e["kind"] == "metric" else e["date"]
    merged = [t[7:] for t in e.get("tags") or [] if str(t).startswith("merged:")]
    return {"id": e["id"], "ws": e["ws"], "origin": "events", "text": text, "value": value, "source": e["source"],
            "source_kind": e["source_kind"], "basis": e["basis"], "confidence": e["confidence"],
            "load_bearing": e["load_bearing"], "cited_in": [], "merged_ids": merged}


def gtm_row(g):
    stats = [f"{k}={g[k]}" for k in ("views", "likes", "reposts", "replies", "bookmarks") if g.get(k) is not None]
    return {"id": g["id"], "ws": g["ws"], "origin": "gtm", "text": f"{g['date']} {g['actor']} ({g['channel']}, {g['format']}): {g['title']}",
            "value": "; ".join([g["date"]] + stats), "source": g["source"], "source_kind": g["source_kind"], "basis": g["basis"],
            "confidence": g["confidence"], "load_bearing": g["load_bearing"], "cited_in": []}


def cmd_merge(run, a):
    merged = run / "research" / "merged"
    rows = [event_row(e) for e in read_json(merged / "events.json")] + [gtm_row(g) for g in read_json(merged / "gtm.json")]
    series = defaultdict(list)
    for m in read_json(merged / "metrics.json"):
        series[(m["metric_name"], m["source"])].append(m)
    collapsed = 0
    for (name, source), points in sorted(series.items()):
        if len(points) <= SERIES_LIMIT:
            rows += [event_row(p) for p in points]
            continue
        rows += [event_row(p) for p in points if p["load_bearing"]]  # stated as load-bearing: checked individually
        rest = sorted((p for p in points if not p["load_bearing"]), key=lambda p: p["id"])
        if rest:
            stable = int(hashlib.sha256(f"{name}|{source}".encode("utf-8")).hexdigest()[:16], 16)
            row = event_row(random.Random(stable).choice(rest))
            row.update(series_size=len(points), series_ids=[p["id"] for p in rest if p["id"] != row["id"]],
                       note=f"one random point standing for a series of {len(points)} {name} rows from one source")
            rows.append(row)
            collapsed += len(rest) - 1
    bad_claims = []
    for path in sorted((run / "research").glob("*/claims.jsonl")):
        for c in read_jsonl(path, CLAIM_KEYS):
            if c["confidence"] not in ("high", "medium", "low") or c["basis"] not in ("fact", "inference") \
                    or c["source_kind"] not in ("primary", "secondary", "aggregator") or not isinstance(c["load_bearing"], bool) \
                    or not (isinstance(c["source"], str) and c["source"].strip()):
                bad_claims.append(f"{path}: {c['id']} has a bad confidence, basis, source_kind, load_bearing or source")
                continue
            rows.append({**{k: c[k] for k in ("id", "text", "value", "source", "source_kind", "basis", "confidence", "load_bearing")},
                         "type": c.get("type"), "ws": path.parent.name, "origin": "claims", "cited_in": []})
    if bad_claims:
        die("invalid claims:\n  " + "\n  ".join(bad_claims), 1)
    dupes = [i for i, n in Counter(r["id"] for r in rows).items() if n > 1]
    if dupes:
        die(f"ids used more than once across events, gtm and claims: {', '.join(sorted(dupes))}", 1)
    write_jsonl(run / "verify" / "ledger.jsonl", sorted(rows, key=lambda r: r["id"]))
    print(f"verify/ledger.jsonl: {len(rows)} rows, {collapsed} metric rows folded into series rows")


def load_ledger(run):
    return read_jsonl(run / "verify" / "ledger.jsonl", "id ws text value source source_kind confidence load_bearing cited_in".split())


def doc_paths(run):
    """Every document that can cite a row: 03 to 09 at the run root, the page prose and the workstream sections."""
    rels = sorted(p.name for p in run.glob("0*.md") if DOC_NAME.fullmatch(p.name))
    if (run / "dashboard" / "prose.json").exists():
        rels.append("dashboard/prose.json")
    return rels + sorted(p.relative_to(run).as_posix() for p in run.glob("research/*/section.md"))


def prose_strings(node, parts):
    """Collect the strings in prose.json. A goto is a navigation target and holds no claim, so it is skipped."""
    if isinstance(node, str):
        parts.append(node)
    elif isinstance(node, dict):
        for k, v in node.items():
            if k != "goto":
                prose_strings(v, parts)
    elif isinstance(node, list):
        for v in node:
            prose_strings(v, parts)
    return parts


def read_docs(run, required=True):
    """Return {doc: text}. When required, a missing load-bearing doc is reported and having no doc at all is fatal."""
    if required:
        for rel in LOAD_BEARING_DOCS:
            if not (run / rel).exists():
                print(f"WARNING: {rel} not found, so it was not scanned")
    docs = {}
    for rel in doc_paths(run):
        if rel.endswith(".json"):
            docs[rel] = "\n\n".join(prose_strings(read_json(run / rel), []))
        else:
            docs[rel] = (run / rel).read_text(encoding="utf-8-sig")
    if required and not docs:
        die(f"no document to scan in {run}: expected 03 to 09 at the run root, dashboard/prose.json or research/*/section.md")
    return docs


def uncited_numbers(text):
    """Sentences holding a digit outside citations, stat tokens and links, and no citation."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    blocks, in_para, found = [], False, []
    for raw in text.split("\n"):
        s = raw.strip()
        if not s or s.startswith("#"):
            in_para = False
            continue
        if in_para and not re.match(r"[|>*+-]|\d+[.)]\s", s):
            blocks[-1] += " " + s  # rejoin a hard-wrapped line
        else:
            blocks.append(s)
        in_para = not s.startswith("|")
    for block in blocks:
        line = re.sub(r"^(\d+[.)]|[-*+>])\s+", "", block)
        for s in [line] if line.startswith("|") else re.split(r"(?<=[.!?])\s+(?!\[c:)", line):
            bare = re.sub(r"\[c:[^\]]*\]|\{\{[^}]*\}\}|https?://\S+|\]\([^)]*\)", "", s)
            if re.search(r"\d", bare) and not CITE.search(s):
                found.append(s.strip())
    return found


def scan_citations(run, rows, required=True):
    """Fill cited_in from every doc and promote cited series points. Only LOAD_BEARING_DOCS set load_bearing.
    Changes rows in place and returns (docs, unresolved citations)."""
    by_id = {r["id"]: r for r in rows}
    alias = {m: r["id"] for r in rows for m in r.get("merged_ids", [])}
    series = {p: r for r in rows for p in r.get("series_ids", [])}
    for r in rows:
        r["cited_in"] = []
    unresolved, points = [], None
    docs = read_docs(run, required)
    for rel, text in docs.items():
        for cid in CITE.findall(text):
            if cid in series and cid not in by_id:  # a cited series point becomes its own checkable row
                points = points or {m["id"]: m for m in read_json(run / "research" / "merged" / "metrics.json")}
                by_id[cid] = event_row(points[cid])
                rows.append(by_id[cid])
                series[cid]["series_ids"].remove(cid)
            target = by_id.get(alias.get(cid, cid))
            if target is None:
                unresolved.append(f"{rel}: [c:{cid}]")
            else:
                target["load_bearing"] = target["load_bearing"] or rel in LOAD_BEARING_DOCS
                target["cited_in"] = sorted(set(target["cited_in"]) | {rel})
    return docs, unresolved


def cmd_mark(run, a):
    rows = load_ledger(run)
    docs, unresolved = scan_citations(run, rows)
    write_jsonl(run / "verify" / "ledger.jsonl", sorted(rows, key=lambda r: r["id"]))
    print(f"Marked {sum(1 for r in rows if r['cited_in'])} cited rows; {sum(r['load_bearing'] for r in rows)} load-bearing in total")
    for rel, text in docs.items():
        for s in uncited_numbers(text) if rel in LOAD_BEARING_DOCS else ():
            if len(s) > 6:  # short strings are ids and scores, not sentences
                print(f"NO CITATION {rel}: {s[:160]}")
    if unresolved:
        print(f"ERROR: {len(unresolved)} citations resolve to nothing:\n  " + "\n  ".join(unresolved))
        return 1


def allocate(sizes, n):
    """Proportional allocation with largest remainders, at least one per stratum, never above a stratum's size."""
    total = sum(sizes.values())
    alloc = {k: max(1, n * s // total) for k, s in sizes.items()}
    while sum(alloc.values()) > n and max(alloc.values()) > 1:
        alloc[max(sorted(alloc), key=lambda k: alloc[k])] -= 1
    order = sorted(sizes, key=lambda k: (-(n * sizes[k] % total), k))
    while sum(alloc.values()) < n:
        for k in order:
            if alloc[k] < sizes[k] and sum(alloc.values()) < n:
                alloc[k] += 1
    return alloc


def second_sample(run, a):
    """Append a fresh draw from one workstream. It counts for that workstream, never for the overall rate."""
    rows = load_ledger(run)
    sample = read_jsonl(run / "verify" / "sample.jsonl", ["id", "in_random"])
    drawn = {r["id"] for r in sample}
    pool = sorted((r for r in rows if r["ws"] == a.second_ws and r["id"] not in drawn), key=lambda r: r["id"])
    known = sorted({r["ws"] for r in rows})
    if a.second_ws not in known:
        die(f"{a.second_ws} is not a workstream in the ledger: {', '.join(known)}")
    if not pool:
        die(f"nothing left to draw in {a.second_ws}: every row in it is already in the sample. No rows were added. Report {a.second_ws} as checked in full.", 1)
    n = min(len(pool), a.second_n or sum(1 for r in sample if r["in_random"]))
    extra = [{**r, "stratum": "second_sample", "in_random": False} for r in random.Random(a.seed).sample(pool, n)]
    write_jsonl(run / "verify" / "sample.jsonl", sample + extra)
    print(f"verify/sample.jsonl: added {n} second-sample rows from {a.second_ws}, seed {a.seed}. Run split, then report.")


def fresh_sample(run, a):
    """After corrections: earlier random rows stop counting, and a new draw measures the corrected run."""
    rows = load_ledger(run)
    sample = read_jsonl(run / "verify" / "sample.jsonl", ["id", "in_random"])
    drawn = {r["id"] for r in sample}
    pool = sorted((r for r in rows if r["id"] not in drawn and r.get("type") != "process"), key=lambda r: r["id"])
    if not pool:
        die("nothing left to draw")
    groups = defaultdict(list)
    for r in pool:
        groups[f"{r['ws']}|{r['source_kind']}"].append(r)
    target = min(a.fresh, len(pool))
    alloc = allocate({k: len(v) for k, v in groups.items()}, target)
    rng = random.Random(a.seed)
    fresh = [{**r, "stratum": "random", "in_random": True} for k in sorted(alloc) for r in rng.sample(groups[k], alloc[k])]
    earlier = [{**r, "stratum": "first_random" if r["in_random"] else r.get("stratum"), "in_random": False} for r in sample]
    write_jsonl(run / "verify" / "sample.jsonl", earlier + fresh)
    print(f"verify/sample.jsonl: fresh draw of {len(fresh)} from {len(pool)} unsampled rows, seed {a.seed}. Copy report.json to report-pass1.json first. Run split, then report.")


def cmd_sample(run, a):
    if a.fresh:
        return fresh_sample(run, a)
    if not 0 < a.rate <= 1 or a.min < 0:
        die("--rate must be above 0 and at most 1, and --min must not be negative")
    if a.second_ws:
        return second_sample(run, a)
    rows = load_ledger(run)
    docs, unresolved = scan_citations(run, rows, required=False)  # sample can run before synthesis, when only section.md files exist
    rows.sort(key=lambda r: r["id"])
    write_jsonl(run / "verify" / "ledger.jsonl", rows)
    print(f"Scanned {len(docs)} documents: {sum(1 for r in rows if r['cited_in'])} rows cited, {sum(r['load_bearing'] for r in rows)} load-bearing")
    if unresolved:
        print(f"WARNING: {len(unresolved)} citations resolve to nothing:\n  " + "\n  ".join(unresolved))
    rng = random.Random(a.seed)
    picked, remainder = [], []
    for r in rows:
        if (r["confidence"] == "low" or r["source_kind"] == "aggregator") and (r["load_bearing"] or r["cited_in"]):
            picked.append({**r, "stratum": "low_or_aggregator", "in_random": False})
        elif r["load_bearing"]:
            picked.append({**r, "stratum": "load_bearing", "in_random": False})
        elif r.get("type") != "process":
            remainder.append(r)
    target = min(len(remainder), max(math.ceil(a.rate * len(remainder)), a.min))
    groups = defaultdict(list)
    for r in remainder:
        groups[f"{r['ws']}|{r['source_kind']}"].append(r)
    alloc = allocate({k: len(v) for k, v in groups.items()}, target) if target else {}
    for key in sorted(alloc):
        picked += [{**r, "stratum": "random", "in_random": True} for r in rng.sample(groups[key], alloc[key])]
    write_jsonl(run / "verify" / "sample.jsonl", sorted(picked, key=lambda r: r["id"]))
    counts = Counter(r["stratum"] for r in picked)
    meta = {"seed": a.seed, "rate": a.rate, "min": a.min, "ledger_rows": len(rows), "remainder": len(remainder), "target": target,
            "strata": {k: counts[k] for k in ("load_bearing", "low_or_aggregator", "random")},
            "random_strata": {k: {"population": len(groups[k]), "drawn": alloc[k]} for k in sorted(alloc)}}
    (run / "verify" / "sample-meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"verify/sample.jsonl: {len(picked)} rows {dict(meta['strata'])}, seed {a.seed}")


def load_verdicts(run, known_ids, required=False):
    path = run / "verify" / "verdicts.jsonl"
    if not path.exists():
        if required:
            die(f"{path} does not exist; verification has not run")
        return {}
    verdicts, errs, repeats = {}, [], 0
    for v in read_jsonl(path, VERDICT_KEYS):
        if v["status"] not in STATUSES:
            errs.append(f"{v['id']}: unknown status {v['status']!r}")
        if v["id"] not in known_ids:
            errs.append(f"{v['id']}: not in the ledger")
        repeats += v["id"] in verdicts
        verdicts[v["id"]] = v
    if repeats:
        print(f"NOTE: {repeats} rows have more than one verdict; the last one counts")
    if errs:
        die("bad verdicts:\n  " + "\n  ".join(errs))
    return verdicts


def load_corrections(run, known_ids):
    path = run / "verify" / "corrections.jsonl"
    rows = read_jsonl(path, ["id", "action", "note"]) if path.exists() else []
    errs = [f"{c['id']}: unknown id or action {c['action']!r}" for c in rows if c["id"] not in known_ids or c["action"] not in ACTIONS]
    if errs:
        die("bad corrections:\n  " + "\n  ".join(errs))
    return {c["id"]: c for c in rows}


def blind(r):
    return {k: r[k] for k in ("id", "text", "value", "source")}


def cmd_split(run, a):
    if a.verifiers < 1:
        die("--verifiers must be at least 1")
    sample = read_jsonl(run / "verify" / "sample.jsonl", ["id", "ws", "text", "value", "source"])
    done = load_verdicts(run, {r["id"] for r in load_ledger(run)})
    todo = sorted((r for r in sample if r["id"] not in done), key=lambda r: (r["ws"], r["id"]))
    for old in (run / "verify").glob("batch-v*.jsonl"):
        old.unlink()  # generated files; a smaller split must not leave stale batches behind
    for i in range(a.verifiers):
        batch = [blind(r) for r in todo[i::a.verifiers]]
        write_jsonl(run / "verify" / f"batch-v{i + 1}.jsonl", batch)
        print(f"verify/batch-v{i + 1}.jsonl: {len(batch)} rows")


def cmd_delta(run, a):
    rows = load_ledger(run)
    done = load_verdicts(run, {r["id"] for r in rows})
    todo = [r for r in rows if r["load_bearing"] and r["id"] not in done]
    write_jsonl(run / "verify" / "batch-delta.jsonl", [blind(r) for r in todo])
    print(f"verify/batch-delta.jsonl: {len(todo)} load-bearing rows with no verdict")
    for r in todo:
        print(f"  {r['id']}")


def binom_cdf(k, n, p):
    """P(X <= k) for X ~ Binomial(n, p), summed in log space so large n cannot overflow."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    lp, lq = math.log(p), math.log1p(-p)
    return min(1.0, sum(math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq) for i in range(k + 1)))


def clopper_pearson(k, n, alpha=0.05):
    """Exact two-sided interval for a binomial proportion, by bisection on the binomial tails."""
    if n == 0:
        return 0.0, 1.0

    def solve(tail_is_low):  # tail_is_low(p) falls from True to False as p rises
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if tail_is_low(mid) else (lo, mid)
        return (lo + hi) / 2
    low = 0.0 if k == 0 else solve(lambda p: 1 - binom_cdf(k - 1, n, p) < alpha / 2)
    high = 1.0 if k == n else solve(lambda p: binom_cdf(k, n, p) > alpha / 2)
    return low, high


def rate_label(rate):
    return ACCURATE if rate <= 0.03 else SECOND if rate <= 0.06 else DIRECTIONAL


def cmd_report(run, a):
    rows = load_ledger(run)
    ledger = {r["id"]: r for r in rows}
    sample = read_jsonl(run / "verify" / "sample.jsonl", ["id", "in_random"])
    second_ids = [r["id"] for r in sample if r.get("stratum") == "second_sample"]
    gone = [r["id"] for r in sample if r["id"] not in ledger]
    if gone:
        die(f"sample rows missing from the ledger (rerun sample?): {', '.join(gone)}")
    verdicts = load_verdicts(run, set(ledger), required=True)
    corrections = load_corrections(run, set(ledger))
    random_ids = [r["id"] for r in sample if r["in_random"]]
    judged = [i for i in random_ids if i in verdicts and verdicts[i]["status"] != "unreachable"]
    wrong = [i for i in judged if verdicts[i]["status"] in WRONG]
    partly = [i for i in judged if verdicts[i]["status"] == "partly"]
    pending = [i for i in random_ids if i not in verdicts]
    low, high = clopper_pearson(len(wrong), len(judged))
    rate = len(wrong) / len(judged) if judged else None
    lb = [r for r in rows if r["load_bearing"]]
    lb_open = [r["id"] for r in lb if r["id"] in verdicts and verdicts[r["id"]]["status"] in WRONG and r["id"] not in corrections]
    lb_none = [r["id"] for r in lb if r["id"] not in verdicts]
    per_ws = {}
    for ws in sorted({r["ws"] for r in rows}):
        extra = [i for i in second_ids if i in verdicts and verdicts[i]["status"] != "unreachable"]
        ids = [i for i in judged + extra if ledger[i]["ws"] == ws]
        bad = sum(1 for i in ids if verdicts[i]["status"] in WRONG)
        # One wrong row in a handful of checks says little, so a workstream needs MIN_WS_RATED checks to earn a rating.
        label = "NOT CHECKED" if not ids else TOO_FEW if len(ids) < MIN_WS_RATED else rate_label(bad / len(ids))
        ws_rows = [r["id"] for r in rows if r["ws"] == ws]
        if not ids and ws_rows and all(i in verdicts for i in ws_rows):
            bad_all = sum(1 for i in ws_rows if verdicts[i]["status"] in WRONG and i not in corrections)
            label = f"CHECKED IN FULL, NO RANDOM SAMPLE ({len(ws_rows)} rows, {bad_all} open)"
        if any(ledger[i]["ws"] == ws for i in lb_open + lb_none):
            label = NOT_RELIABLE
        per_ws[ws] = {"label": label, "checked": len(ids), "wrong": bad}
    unreachable = sum(1 for v in verdicts.values() if v["status"] == "unreachable")
    share = unreachable / len(verdicts) if verdicts else 0.0
    worst = max((w for w in per_ws if per_ws[w]["checked"]), key=lambda w: (per_ws[w]["wrong"] / per_ws[w]["checked"], per_ws[w]["wrong"], w), default=None)
    findings = []
    if lb_open:
        findings.append(f"Load-bearing rows wrong or unsupported with no correction: {', '.join(lb_open)}.")
    lb_unreach = [r["id"] for r in lb if r["id"] in verdicts and verdicts[r["id"]]["status"] == "unreachable"]
    if lb_unreach:
        findings.append(f"Load-bearing rows that could not be checked, so they stay unconfirmed: {', '.join(lb_unreach)}.")
    if lb_none:
        findings.append(f"Load-bearing rows with no verdict yet, run `delta`: {', '.join(lb_none)}.")
    if not judged:
        findings.append("No random-stratum row has a usable verdict, so no error rate exists.")
    if pending:
        findings.append(f"{len(pending)} random-stratum rows have no verdict yet and are outside the estimate.")
    if 0 < len(judged) < 30:
        findings.append(f"Sample too small to be meaningful: {len(judged)} random rows checked, and 30 is the floor.")
    if share > 0.15:
        findings.append(f"Unreachable sources are {100 * share:.1f}% of verdicts, above the 15% limit. Those rows are unjudged.")
    if lb_open or lb_none or not judged:
        label = NOT_RELIABLE
    elif any(v["label"] == DIRECTIONAL for v in per_ws.values()):
        label = DIRECTIONAL
    else:
        label = rate_label(rate)
    if judged and 0.03 < rate <= 0.06:
        exhausted = worst and all(r["id"] in verdicts for r in rows if r["ws"] == worst)
        if label == SECOND and (exhausted or any(i in verdicts for i in second_ids)):
            label = ACCURATE
            findings.append(f"Wrong rate is between 3 and 6 percent. A second sample ran, or the worst workstream was checked in full, and no workstream exceeded 6 percent, so this passes. Read the interval.")
        elif label == SECOND:
            findings.append(f"Wrong rate is between 3 and 6 percent: run a second sample on the worst workstream, {worst} (`sample --seed N --second-ws {worst}`).")
    if 0 < len(judged) < 30 and label == ACCURATE:
        label = SECOND  # a clean result on a very small sample proves little, so it can't earn the top label
    thin = [w for w, v in per_ws.items() if v["label"] == TOO_FEW]
    if thin:
        findings.append(f"Too few random checks to rate on their own (under {MIN_WS_RATED}): {', '.join(thin)}.")
    # Rows added after the random draw, such as the moves pass, get their own rate and never mix into the main one.
    later = [ws for ws, v in per_ws.items() if v["checked"] and not any(ledger[i]["ws"] == ws for i in random_ids)]
    if later:
        ids = [i for i in second_ids if i in verdicts and verdicts[i]["status"] != "unreachable" and ledger[i]["ws"] in later]
        bad = sum(1 for i in ids if verdicts[i]["status"] in WRONG)
        soft = sum(1 for i in ids if verdicts[i]["status"] == "partly")
        lo, hi = clopper_pearson(bad, len(ids))
        findings.append(f"Moves evidence: a separate random check of {len(ids)} rows from {', '.join(later)} found {bad} wrong or unsupported ({100 * bad / len(ids):.1f}%, range {100 * lo:.1f}% to {100 * hi:.1f}%), and {soft} partly right. The main rate above doesn't cover these rows.")
    first = run / "verify" / "report-pass1.json"
    if first.exists():
        f = read_json(first)
        findings.append(f"Before corrections, the first random sample had a wrong rate of {100 * f['wrong_rate']:.1f}% ({100 * f['interval_low']:.1f}% to {100 * f['interval_high']:.1f}%), on {f['random_checked']} rows. The rate above is a fresh sample drawn after the corrections.")
    meta = read_json(run / "run.json") if (run / "run.json").exists() else {}
    config = read_json(run / "config.json") if (run / "config.json").exists() else {}
    cutoff = config.get("cutoff") or meta.get("cutoff_date")
    if not cutoff:
        findings.append("No cutoff date found in config.json or run.json.")
    result = {"label": label, "claims_total": len(rows), "load_bearing_checked": sum(1 for r in lb if r["id"] in verdicts and verdicts[r["id"]]["status"] != "unreachable"),
              "load_bearing_unreachable": sum(1 for r in lb if r["id"] in verdicts and verdicts[r["id"]]["status"] == "unreachable"),
              "load_bearing_total": len(lb),
              "load_bearing_wrong_open": len(lb_open), "random_checked": len(judged), "wrong_rate": rate, "interval_low": low,
              "interval_high": high, "unreachable": unreachable, "per_workstream": per_ws, "cutoff": cutoff,
              "unreachable_share": share, "partly": len(partly), "findings": findings}
    (run / "verify" / "report.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    pc = lambda x: f"{100 * x:.1f}%"
    md = ["# Verification report", "", f"**Label: {label}**", "", f"- Claims in the ledger: {len(rows)}", f"- Cutoff: {cutoff}",
          f"- Load-bearing rows checked: {result['load_bearing_checked']} of {len(lb)}, with {result['load_bearing_unreachable']} unreachable; wrong or unsupported with no correction: {len(lb_open)}",
          f"- Random rows checked: {len(judged)}; wrong or unsupported: {len(wrong)}; partly right (reported apart, outside the rate): {len(partly)}",
          f"- Wrong rate: {pc(rate) if judged else 'not available'}, 95% interval {pc(low)} to {pc(high)}",
          f"- Unreachable after retry: {unreachable} ({pc(share)} of verdicts), left out of the rate", "",
          f"The interval is an exact Clopper-Pearson range: the data fit a true wrong rate anywhere from {pc(low)} to {pc(high)}, "
          "and 95 of 100 intervals built this way contain the true rate. It treats the stratified draw as a simple random sample.",
          "", "## Findings", ""] + ([f"- {f}" for f in findings] or ["None."]) + ["", "## Per workstream", "",
          "| Workstream | Label | Checked | Wrong | Rate |", "|---|---|---|---|---|"]
    md += [f"| {w} | {v['label']} | {v['checked']} | {v['wrong']} | {pc(v['wrong'] / v['checked']) if v['checked'] else 'n/a'} |" for w, v in per_ws.items()]
    (run / "verify" / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print(f"verify/report.md: {label}; wrong rate {pc(rate) if judged else 'n/a'} ({pc(low)} to {pc(high)}), {len(findings)} findings")


def cmd_check_citations(run, a):
    rows = load_ledger(run)
    ids = {r["id"] for r in rows}
    alias = {m: r["id"] for r in rows for m in r.get("merged_ids", [])}
    load_bearing = {r["id"] for r in rows if r["load_bearing"]}
    verdicts, corrections, problems, unchecked = load_verdicts(run, ids), load_corrections(run, ids), [], set()
    for rel, text in read_docs(run).items():
        for cid in sorted(set(CITE.findall(text))):
            rid = alias.get(cid, cid)
            action = corrections.get(rid, {}).get("action")
            status = verdicts.get(rid, {}).get("status")
            if rid not in ids:
                problems.append(f"{rel}: [c:{cid}] resolves to nothing (a series point needs `mark` first)")
            elif action == "removed":
                problems.append(f"{rel}: [c:{cid}] was removed by a correction but is still cited")
            elif not status and not action and rid not in load_bearing and rel not in LOAD_BEARING_DOCS:
                unchecked.add(rid)  # delta and the sample cover load-bearing rows only; the page shows this one as unchecked
            elif not action and status not in ("confirmed", "partly"):
                problems.append(f"{rel}: [c:{cid}] verdict is {status or 'missing'} with no correction")
    if problems:
        print(f"CITATION PROBLEMS ({len(problems)}):\n  " + "\n  ".join(problems))
        return 1
    if unchecked:
        print(f"NOTE: {len(unchecked)} rows cited outside the load-bearing docs have no verdict: {', '.join(sorted(unchecked))}")
    print("All citations resolve. None is open as wrong or removed, and every load-bearing citation has a verdict.")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmds = {"merge": cmd_merge, "mark": cmd_mark, "sample": cmd_sample, "split": cmd_split, "delta": cmd_delta,
            "report": cmd_report, "check-citations": cmd_check_citations}
    argv = sys.argv[1:]
    if len(argv) >= 2 and argv[0] not in cmds and argv[1] in cmds:
        argv[0], argv[1] = argv[1], argv[0]
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    parsers = {name: sub.add_parser(name) for name in cmds}
    for p in parsers.values():
        p.add_argument("run_dir", type=Path)
    parsers["sample"].add_argument("--seed", type=int, required=True)
    parsers["sample"].add_argument("--rate", type=float, default=0.05)
    parsers["sample"].add_argument("--min", type=int, default=100)
    parsers["sample"].add_argument("--fresh", type=int, default=0, help="after corrections: draw this many new random rows, which replace the earlier ones in the rate")
    parsers["sample"].add_argument("--second-ws", default=None, help="append a second sample from this workstream")
    parsers["sample"].add_argument("--second-n", type=int, default=0, help="rows to draw with --second-ws; default is the size of the random sample")
    parsers["split"].add_argument("--verifiers", type=int, default=3)
    a = ap.parse_args(argv)
    if not a.run_dir.is_dir():
        die(f"{a.run_dir} is not a folder")
    return cmds[a.cmd](a.run_dir, a) or 0


if __name__ == "__main__":
    sys.exit(main())
