#!/usr/bin/env python3
"""Sum paid calls and model use, reconcile against balance checks, flag cap breaches, write cost-report.md.

Usage: python -I cost_report.py <run-dir> [--subagent-logs <folder>]
                                [--transcripts <file-or-folder> ...] [--since ISO] [--until ISO]
Model use comes from <run-dir>/usage/*.json (the result of `claude -p --output-format json`, one file per stage),
and from Claude Code transcripts given with --transcripts (main .jsonl and the subagents folder), counted once per
message id and priced at the list prices in PRICES. A budgets.model_usd_cap in run.json is checked.
Exit 0 on success, 1 on malformed call rows, 2 on an unusable run folder.
"""
import argparse, json, sys
from collections import defaultdict
from pathlib import Path

CALL_KEYS = "ts ws endpoint provider_served price purpose status hit claim_ids".split()

# USD per million tokens: input, output, cache read. Cache writes cost 1.25x input (5-minute) or 2x input (1-hour).
# Anthropic list prices as cached on 2026-11-03; update this table when prices change.
PRICES = {
    "claude-fable-5-2": (8.0, 40.0, 0.20), "claude-fable-5-1": (10.0, 50.0, 0.25), "claude-fable-5": (10.0, 50.0, 0.25),
    "claude-opus-5-5": (4.0, 20.0, 0.20), "claude-opus-5": (5.0, 25.0, 0.50),
    "claude-sonnet-5-5": (2.0, 10.0, 0.10), "claude-sonnet-5": (2.0, 10.0, 0.20),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
}


def usage_cost(model, u):
    """Return the list-price USD of one usage block, or None when the model is not in PRICES."""
    p = PRICES.get(model)
    if p is None:
        return None
    pin, pout, pread = p
    cc = u.get("cache_creation") or {}
    w1h, w5m = cc.get("ephemeral_1h_input_tokens"), cc.get("ephemeral_5m_input_tokens")
    if w1h is None and w5m is None:  # split not recorded: price as 1-hour, the upper bound
        w1h, w5m = u.get("cache_creation_input_tokens") or 0, 0
    return ((u.get("input_tokens") or 0) * pin + (u.get("output_tokens") or 0) * pout
            + (u.get("cache_read_input_tokens") or 0) * pread + (w5m or 0) * pin * 1.25 + (w1h or 0) * pin * 2.0) / 1e6


def transcript_usage(paths, since=None, until=None):
    """Sum usage from Claude Code transcripts. Streamed chunks repeat a message's usage, so each id counts once per file."""
    by_model = defaultdict(lambda: {"usd": 0.0, "output_tokens": 0, "messages": 0, "unpriced": False})
    files = []
    for p in paths:
        files += sorted(p.rglob("*.jsonl")) if p.is_dir() else [p]
    for fp in files:
        seen = set()
        for raw in fp.read_bytes().split(b"\n"):
            if not raw.strip():
                continue
            try:
                d = json.loads(raw.decode("utf-8-sig"))
            except ValueError:
                continue
            if not isinstance(d, dict) or d.get("type") != "assistant":
                continue
            ts = str(d.get("timestamp") or "")
            if (since and ts < since) or (until and ts >= until):
                continue
            m = d.get("message") or {}
            mid, model, u = m.get("id"), m.get("model", "?"), m.get("usage") or {}
            if not u or mid in seen or model.startswith("<"):
                continue
            seen.add(mid)
            row = by_model[model]
            cost = usage_cost(model, u)
            row["usd"] += cost or 0.0
            row["unpriced"] |= cost is None
            row["output_tokens"] += u.get("output_tokens") or 0
            row["messages"] += 1
    return dict(by_model), len(files)


def headless_usage(run):
    """Sum total_cost_usd from saved `claude -p --output-format json` results in <run>/usage/."""
    rows = []
    for fp in sorted((run / "usage").glob("*.json")) if (run / "usage").is_dir() else []:
        try:
            d = json.loads(fp.read_text(encoding="utf-8-sig"))
        except ValueError:
            rows.append((fp.name, None))
            continue
        rows.append((fp.name, d.get("total_cost_usd") if isinstance(d, dict) else None))
    return rows


def die(msg, code=2):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def read_calls(run):
    """Return (rows, [workstream folders without calls.jsonl]); exit 1 listing every bad row."""
    rows, bad, without = [], [], []
    verifiers = sorted((run / "verify").glob("raw-*")) if (run / "verify").is_dir() else []
    research = sorted(p for p in (run / "research").iterdir() if p.is_dir() and p.name != "merged")
    for ws_dir in research + [p for p in verifiers if (p / "calls.jsonl").exists()]:
        path = ws_dir / "calls.jsonl"
        if not path.exists():
            without.append(ws_dir.name)
            continue
        for n, raw in enumerate(path.read_bytes().split(b"\n"), 1):
            if not raw.strip():
                continue
            where = f"{ws_dir.parent.name}/{ws_dir.name}/calls.jsonl:{n}"
            try:
                row = json.loads(raw.decode("utf-8-sig"))
            except ValueError as e:
                bad.append(f"{where}: not valid UTF-8 JSON: {e}")
                continue
            if not isinstance(row, dict):
                bad.append(f"{where}: line is not a JSON object")
                continue
            errs = [f"missing key '{k}'" for k in CALL_KEYS if k not in row]
            price = row.get("price")
            if "price" in row and (isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0):
                errs.append(f"price={price!r} must be a number at or above 0")
            if "hit" in row and not isinstance(row["hit"], bool):
                errs.append(f"hit={row['hit']!r} must be true or false")
            if errs:
                bad.append(f"{where}: " + "; ".join(errs))
                continue
            row["_where"] = where
            rows.append(row)
    if bad:
        print(f"MALFORMED CALL ROWS ({len(bad)}), no report written:")
        for b in bad:
            print(f"  {b}")
        sys.exit(1)
    return rows, without


def table(rows, field, title):
    groups = defaultdict(list)
    for r in rows:
        groups[str(r[field])].append(r)
    out = [f"## By {title}", "", f"| {title.capitalize()} | Calls | Hits | Hit rate | Misses paid | Spend USD |", "|---|---|---|---|---|---|"]
    for key, group in sorted(groups.items(), key=lambda kv: -sum(r["price"] for r in kv[1])):
        hits = sum(r["hit"] for r in group)
        paid_miss = sum(1 for r in group if not r["hit"] and r["price"] > 0)
        out.append(f"| {key} | {len(group)} | {hits} | {100 * hits / len(group):.0f}% | {paid_miss} | {sum(r['price'] for r in group):.4f} |")
    return out + [""]


def count_tool_calls(path):
    """Return (tool-call count, malformed line count) for one JSONL log. Repeated tool-use ids count once."""
    ids, anonymous, malformed = set(), 0, 0

    def walk(node):
        nonlocal anonymous
        if isinstance(node, dict):
            if node.get("type") == "tool_use":
                if node.get("id"):
                    ids.add(node["id"])
                else:
                    anonymous += 1
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for raw in path.read_bytes().split(b"\n"):
        if raw.strip():
            try:
                walk(json.loads(raw.decode("utf-8-sig")))
            except ValueError:
                malformed += 1
    return len(ids) + anonymous, malformed


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--subagent-logs", type=Path)
    ap.add_argument("--transcripts", type=Path, nargs="+", help="Claude Code transcript .jsonl files or folders")
    ap.add_argument("--since", help="ISO time; count transcript messages at or after it")
    ap.add_argument("--until", help="ISO time; count transcript messages before it")
    args = ap.parse_args()
    run = args.run_dir
    if not (run / "research").is_dir():
        die(f"{run} has no research/ folder, so it is not a run folder")
    try:
        meta = json.loads((run / "run.json").read_text(encoding="utf-8-sig"))
        budgets, checks = meta.get("budgets") or {}, meta.get("balance_checks") or []
        checks = [(c["label"], float(c["usd"])) for c in checks]
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        die(f"cannot use {run / 'run.json'}: {type(e).__name__}: {e}")
    rows, without = read_calls(run)
    total = sum(r["price"] for r in rows)
    hits = sum(r["hit"] for r in rows)
    misses = [r for r in rows if not r["hit"] and r["price"] > 0]
    out = ["# Cost report", "", f"- Calls logged: {len(rows)}", f"- Total logged spend: {total:.4f} USD",
           f"- Hit rate: {100 * hits / len(rows):.0f}%" if rows else "- Hit rate: n/a, no calls logged",
           f"- Misses paid for: {len(misses)} ({sum(r['price'] for r in misses):.4f} USD)"]
    if without:
        out.append(f"- Workstreams with no calls.jsonl: {', '.join(without)}")
    out += ["", "## Reconciliation against balance checks", ""]
    out += [f"- {label}: {usd:.4f} USD" for label, usd in checks]
    if len(checks) >= 2:
        drop = checks[0][1] - checks[-1][1]
        out += [f"- Balance drop, {checks[0][0]} to {checks[-1][0]}: {drop:.4f} USD", f"- Logged spend: {total:.4f} USD",
                f"- GAP (balance drop minus logged spend): {drop - total:+.4f} USD",
                "- A positive gap means money left the balance with no logged call. A negative gap means rows were logged "
                "that did not draw on this balance, or the balance was topped up. Every logged row is assumed to draw on it."]
    else:
        out.append(f"- GAP: cannot be computed, run.json has {len(checks)} balance check(s) and two are needed.")
    out += ["", "## Caps", ""]
    per_call, cap = budgets.get("treg_usd_per_call"), budgets.get("treg_usd_cap")
    if per_call is None:
        out.append("- Per-call cap: not set in run.json budgets, so it was not checked.")
    else:
        over = [r for r in rows if r["price"] > per_call]
        out.append(f"- Calls over the per-call cap of {per_call} USD: {len(over)}")
        out += [f"  - OVER CAP {r['price']} USD, {r['endpoint']}, {r['_where']}" for r in over]
    if cap is None:
        out.append("- Total cap: not set in run.json budgets, so it was not checked.")
    else:
        out.append(f"- Total against the cap of {cap} USD: {total:.4f} USD. Passed the cap: {'YES' if total > cap else 'no'}.")
    out.append("")
    out += ["## Model use", ""]
    model_total, model_known = 0.0, False
    headless = headless_usage(run)
    if headless:
        model_known = True
        out += ["From saved headless results in usage/:", "", "| File | USD |", "|---|---|"]
        for name, usd in headless:
            out.append(f"| {name} | {'unreadable' if usd is None else f'{usd:.2f}'} |")
            model_total += usd or 0.0
        out.append("")
    if args.transcripts:
        missing = [str(p) for p in args.transcripts if not p.exists()]
        if missing:
            die(f"--transcripts: not found: {', '.join(missing)}")
        by_model, nfiles = transcript_usage(args.transcripts, args.since, args.until)
        model_known = True
        window = f", from {args.since or 'start'} to {args.until or 'end'}"
        out += [f"From {nfiles} transcript file(s){window}, each message counted once, at list prices:", "",
                "| Model | Messages | Output tokens | USD |", "|---|---|---|---|"]
        for model, r in sorted(by_model.items(), key=lambda kv: -kv[1]["usd"]):
            usd = "not priced (add it to PRICES)" if r["unpriced"] and not r["usd"] else f"{r['usd']:.2f}"
            out.append(f"| {model} | {r['messages']} | {r['output_tokens']:,} | {usd} |")
            model_total += r["usd"]
        out.append("")
        if headless:
            out.append("- Note: headless results and transcripts were both given; if they cover the same work, the total double-counts it.")
    if model_known:
        out.append(f"- Model use total: {model_total:.2f} USD")
    else:
        out.append("- Model use: not measured. Save each stage's `claude -p --output-format json` result to usage/, or pass --transcripts.")
    model_cap = budgets.get("model_usd_cap")
    if model_cap is not None and model_known:
        out.append(f"- Against the model cap of {model_cap} USD: {model_total:.2f} USD. Passed the cap: {'YES' if model_total > model_cap else 'no'}.")
    out.append("")
    if rows:
        out += table(rows, "ws", "workstream") + table(rows, "endpoint", "endpoint") + table(rows, "provider_served", "provider")
    if args.subagent_logs is not None:
        logs = sorted(args.subagent_logs.rglob("*.jsonl")) if args.subagent_logs.is_dir() else []
        if not logs:
            die(f"--subagent-logs {args.subagent_logs}: folder is missing or holds no .jsonl files")
        out += ["## Subagent tool calls", "", "| Log | Tool calls | Malformed lines |", "|---|---|---|"]
        for log in logs:
            count, malformed = count_tool_calls(log)
            out.append(f"| {log.relative_to(args.subagent_logs).as_posix()} | {count} | {malformed} |")
        out.append("")
    if not rows:
        print("WARNING: no calls logged anywhere under research/; confirm this run really made no paid calls.")
    text = "\n".join(out)
    (run / "cost-report.md").write_text(text, encoding="utf-8", newline="\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
