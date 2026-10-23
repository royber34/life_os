"""Scoreboard from reviewer JSON files.

Panel round: python -I scoreboard.py review/round-1/
  reads every *.json with "overall" and prints one row per seat plus means.
A/B:         python -I scoreboard.py review/ab/ --key review/ab-key.txt
  reads <dir>/<judge>/result.json, maps A and B to page names with the key file
  (lines like "q1: A=draft B=live"), prints per-page means and preferences.
"""
import sys
import json
import pathlib
import statistics as st

LINES = ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9", "L10"]


def fmt(v):
    return "" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v))


def mean(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    return st.mean(vals) if vals else None


def panel(d: pathlib.Path):
    rows = []
    for f in sorted(d.glob("*.json")):
        j = json.loads(f.read_text(encoding="utf-8"))
        if "overall" in j:
            rows.append((f.stem, j))
    print("| seat | overall | act | submit % | " + " | ".join(LINES) + " |")
    print("|" + "---|" * (4 + len(LINES)))
    for name, j in rows:
        lines = j.get("lines", {})
        print(f"| {name} | {j.get('overall')} | {j.get('act')} | {j.get('submit_pct')} | " + " | ".join(fmt(lines.get(k)) for k in LINES) + " |")
    print(f"| mean | {fmt(mean([j.get('overall') for _, j in rows]))} | | {fmt(mean([j.get('submit_pct') for _, j in rows]))} | "
          + " | ".join(fmt(mean([j.get('lines', {}).get(k) for _, j in rows])) for k in LINES) + " |")


def ab(d: pathlib.Path, key: pathlib.Path):
    plan = {}
    for line in key.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            judge, rest = line.split(":", 1)
            plan[judge.strip()] = dict(x.split("=") for x in rest.split())
    pages, prefs = {}, []
    for judge, mapping in plan.items():
        j = json.loads((d / judge / "result.json").read_text(encoding="utf-8"))
        for label, page in mapping.items():
            pages.setdefault(page, []).append(j[label])
        prefs.append(f"{judge}: {mapping.get(j.get('prefer'), j.get('prefer'))}")
    names = list(pages)
    print("| line | " + " | ".join(names) + " |")
    print("|" + "---|" * (1 + len(names)))
    for field in ["overall", "submit_pct"] + LINES:
        vals = []
        for n in names:
            if field in ("overall", "submit_pct"):
                vals.append(mean([e.get(field) for e in pages[n]]))
            else:
                vals.append(mean([e.get("lines", {}).get(field) for e in pages[n]]))
        if any(v is not None for v in vals):
            print(f"| {field} | " + " | ".join(fmt(v) for v in vals) + " |")
    print("preferences: " + "; ".join(prefs))


if __name__ == "__main__":
    target = pathlib.Path(sys.argv[1])
    if "--key" in sys.argv:
        ab(target, pathlib.Path(sys.argv[sys.argv.index("--key") + 1]))
    else:
        panel(target)
