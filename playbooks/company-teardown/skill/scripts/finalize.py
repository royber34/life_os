#!/usr/bin/env python3
"""Close a run only when its files agree. Read-mostly: writes verify/finalize.json and, on success,
the generated verification section of raw-research-README.md and the run stage.

    python -I finalize.py <run-dir> [--allow-label LABEL ...] [--no-stage]

Checks, each reported pass or FAIL:
  1. Every research/w*/ folder is listed in run.json, and none is still running.
  2. No sync-conflict copies anywhere in the run folder (Proton Drive, OneDrive, Dropbox naming).
  3. verify/report.json exists, and its label is one of the allowed labels (default: ACCURATE TO SOURCES,
     DIRECTIONAL ONLY), with no load-bearing row left without a verdict.
  4. dashboard/bundle.json carries the same verification label and claim count as report.json.
  5. The page was built after its inputs: index.html is newer than bundle.json and prose.json,
     and bundle.json is newer than report.json.
  6. dashboard/screens/render-report.md is newer than index.html and says PASS.
  7. Neither index.html nor onepager.html holds a home-directory path (C:\\Users\\<name>, /home/<name>,
     /Users/<name>), which would show a local folder and username to anyone reading the page source.
On success the README section between the finalize markers is rewritten from report.json, so the archive
README can never disagree with the page, and run.json stage becomes "S6 done" (unless --no-stage).
Exit 0 when every check passes, 1 when any fails, 2 on an unusable run folder.
"""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LABELS = ["ACCURATE TO SOURCES", "DIRECTIONAL ONLY"]
SEP = r"(?:\\{1,2}|/)"
# Any user folder, written as a local path: C:\Users\<name>\..., /home/<name>/..., /Users/<name>/..., /mnt/c/Users/<name>/.
# Case-sensitive and anchored to the start of a token, so URLs and API paths such as /users/me or #/home/x don't match.
USER_FOLDER_RE = re.compile(rf"(?<![\w])[A-Za-z]:{SEP}(?:Users|Documents and Settings){SEP}[^\\/\s\"'<>]+{SEP}"
                            rf"|(?<![^\s\"'(>=:,\[])(?:/mnt/[a-z])?/(?:home|Users)/[^/\s\"'<>]+/")


def folder_re(folder):
    """Same function as build_dashboard.folder_re (a test pins them together): an absolute folder, exactly."""
    p = Path(folder).resolve()
    parts = [re.escape(x) for x in p.as_posix().split("/") if x]
    if not parts:
        return None
    body = SEP.join(parts)
    if p.drive:
        rest = SEP.join(parts[1:])
        body = rf"(?:{body}|/mnt/{re.escape(p.drive[0].lower())}/{rest})"
    else:
        body = SEP + body
    return re.compile(rf"(?<![\w.]){body}(?={SEP}|$|[\s\"'<>)\],;])", re.I if p.drive else 0)


def home_paths(run, home=None):
    """Local user-folder paths found in the built page and one-pager, as (file, path) pairs: the home folder of
    whoever runs this, exactly, and any other user folder by pattern."""
    pats = [r for r in (folder_re(home if home is not None else Path.home()),) if r] + [USER_FOLDER_RE]
    hits = []
    for rel in ("dashboard/index.html", "dashboard/onepager.html"):
        p = run / rel
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            hits += [(rel, m.group(0)) for pat in pats for m in pat.finditer(text)]
    return hits
START, END = "<!-- finalize:verification -->", "<!-- /finalize -->"


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def conflict_copies(run):
    hits = []
    for p in run.rglob("*"):
        name = p.name
        if "Edit conflict" in name or "Name clash" in name or "conflicted copy" in name.lower():
            hits.append(p.relative_to(run).as_posix())
    return sorted(hits)


def check(run, allowed):
    rows = []

    def add(name, ok, detail=""):
        rows.append({"check": name, "ok": bool(ok), "detail": str(detail)})

    meta = load_json(run / "run.json")
    if not isinstance(meta, dict):
        raise SystemExit(2)
    ws = meta.get("workstreams") or {}
    folders = sorted(p.name for p in (run / "research").iterdir()
                     if p.is_dir() and p.name[:1] == "w" and p.name.split("-", 1)[0][1:].isdigit()) \
        if (run / "research").is_dir() else []
    missing = [f for f in folders if f not in ws]
    running = [k for k, v in ws.items() if (v or {}).get("status") == "running"]
    add("Every workstream folder is in run.json", not missing, ", ".join(missing) or f"{len(folders)} folders")
    add("No workstream still running", not running, ", ".join(running) or "none running")

    copies = conflict_copies(run)
    add("No sync-conflict copies", not copies, "; ".join(copies[:8]) + (f" (+{len(copies) - 8} more)" if len(copies) > 8 else "") or "none")

    report = load_json(run / "verify" / "report.json")
    if not isinstance(report, dict):
        add("verify/report.json exists", False, "missing or unreadable; run ledger.py report")
        label = None
    else:
        label = report.get("label")
        add("Verification label allowed", label in allowed, f"{label} (allowed: {', '.join(allowed)})")
        open_lb = [f for f in report.get("findings") or [] if "no verdict" in str(f).lower()]
        add("No load-bearing row without a verdict", not open_lb, " | ".join(map(str, open_lb))[:300] or "none")

    bundle = load_json(run / "dashboard" / "bundle.json")
    if isinstance(bundle, dict) and isinstance(report, dict):
        v = bundle.get("verification") or {}
        same = v.get("label") == label and v.get("claims_total") == report.get("claims_total")
        add("Page carries the report's label and claim count", same,
            f"page {v.get('label')} / {v.get('claims_total')}, report {label} / {report.get('claims_total')}")
    else:
        add("Page carries the report's label and claim count", False, "dashboard/bundle.json missing or unreadable")

    def mtime(rel):
        p = run / rel
        return p.stat().st_mtime if p.exists() else None

    idx, bun, pro, rep = (mtime("dashboard/index.html"), mtime("dashboard/bundle.json"),
                          mtime("dashboard/prose.json"), mtime("verify/report.json"))
    order_ok = None not in (idx, bun, pro, rep) and idx >= bun and idx >= pro and bun >= rep
    add("Page built after its inputs", order_ok,
        "index.html >= bundle.json, prose.json; bundle.json >= report.json" if order_ok else "rebuild: assemble, then build")

    rr = run / "dashboard" / "screens" / "render-report.md"
    text = rr.read_text(encoding="utf-8", errors="replace") if rr.exists() else ""
    rendered = rr.exists() and idx is not None and rr.stat().st_mtime >= idx and "Result: **PASS**" in text
    add("Render test passed on the current page", rendered,
        "PASS, after the last build" if rendered else "run render_test.py on the current index.html")

    leaks = home_paths(run)
    add("No local home-directory path in the page", not leaks,
        "; ".join(f"{f}: {p}" for f, p in sorted(set(leaks))[:5]) + " (rebuild: assemble scrubs these)" if leaks else "none")
    return rows, report, meta


def readme_section(report):
    ci = f"{100 * report['interval_low']:.1f}% to {100 * report['interval_high']:.1f}%" \
        if report.get("interval_low") is not None and report.get("interval_high") is not None else "n/a"
    rate = f"{100 * report['wrong_rate']:.1f}%" if report.get("wrong_rate") is not None else "n/a"
    lines = [START, "## Verification (generated by finalize.py, do not edit by hand)", "",
             f"- Label: **{report.get('label')}**",
             f"- Claims in the ledger: {report.get('claims_total')}",
             f"- Load-bearing rows checked: {report.get('load_bearing_checked')} of {report.get('load_bearing_total')}",
             f"- Random rows checked: {report.get('random_checked')}; wrong rate {rate}, 95% interval {ci}",
             f"- Cutoff: {report.get('cutoff')}", "- Full report: `verify/report.md`", END]
    return "\n".join(lines)


def write_readme(run, report):
    path = run / "raw-research-README.md"
    section = readme_section(report)
    text = path.read_text(encoding="utf-8") if path.exists() else "# Raw research archive\n"
    if START in text and END in text:
        text = text[:text.index(START)] + section + text[text.index(END) + len(END):]
    else:
        text = text.rstrip("\n") + "\n\n" + section + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--allow-label", action="append")
    ap.add_argument("--no-stage", action="store_true")
    args = ap.parse_args(argv)
    run = args.run_dir
    if not run.is_dir() or not (run / "run.json").exists():
        print(f"ERROR: {run} is not a run folder (no run.json)", file=sys.stderr)
        return 2
    try:
        rows, report, meta = check(run, args.allow_label or DEFAULT_LABELS)
    except SystemExit:
        print(f"ERROR: {run / 'run.json'} is unreadable", file=sys.stderr)
        return 2
    ok = all(r["ok"] for r in rows)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (run / "verify").mkdir(exist_ok=True)
    (run / "verify" / "finalize.json").write_text(json.dumps({"ts": ts, "ok": ok, "checks": rows}, indent=1) + "\n",
                                                   encoding="utf-8")
    for r in rows:
        print(f"{'pass' if r['ok'] else 'FAIL'}  {r['check']}: {r['detail']}")
    if not ok:
        print(f"FINALIZE FAILED: {sum(not r['ok'] for r in rows)} check(s). Nothing closed.")
        return 1
    write_readme(run, report)
    if not args.no_stage:
        meta["stage"] = "S6 done"
        meta.setdefault("stage_history", []).append({"stage": "S6 done", "ts": ts})
        tmp = run / "run.json.tmp"
        tmp.write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(run / "run.json")
    print("FINALIZED: all checks pass; README verification section and run stage written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
