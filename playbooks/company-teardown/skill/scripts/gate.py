#!/usr/bin/env python3
"""Release gate for client-mode runs: pass, revise or hold (references/client-mode.md, references/judges.md).

    python -I gate.py <run-dir> [--round N]

Reads rubric.json (each rule's level and check), verify/rubric-code.json (code rules, rows {id, level, status:
pass|fail|n/a, failures[], note}), verify/judges.json (judge rules, from judges.py collect), verify/finalize.json,
dashboard/screens/render-report.md, the caps in run.json budgets (model_usd_cap, treg_usd_cap) and the spend lines in
cost-report.md ("Model use total: X USD", "Total logged spend: X USD").

Every input except rubric.json and run.json must be at least as new as dashboard/bundle.json, judges.json must name
the current bundle, and cost-report.md must be at least as new as verify/judges.json, so the judges' model use is
counted. A missing or stale input holds the run: nothing passes by default.

  pass    every must rule and every hard gate (finalize, render test, model and data spend under their caps) passes.
          Should rules are reported and never block.
  revise  a must rule fails, every input and hard gate is fine, and the round is under 2. scorecard.json lists the
          items to fix with the judges' quotes; fix them, rebuild, re-judge, then run gate.py with --round N+1.
  hold    anything else. HOLD.md at the run root says which gate failed, the failing items with quotes, and the
          options. An earlier HOLD.md moves to verify/holds/ first.

Round 0 is the first check. Writes verify/scorecard.json every time.
Exit 0 pass, 3 revise, 1 hold, 2 unusable run folder.
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_ROUNDS = 2
EXIT = {"pass": 0, "hold": 1, "revise": 3}
MODEL_LINE = re.compile(r"Model use total:\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*USD")
DATA_LINE = re.compile(r"Total logged spend:\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*USD")
RENDER_PASS = re.compile(r"Result:\s*\*\*PASS\*\*")
CODE_STATUS = ("pass", "fail", "n/a")
# Which part of the pipeline a re-run would repeat, what it involves, and whether it may buy data.
MODULES = {
    "onepager": ("One-pager rewrite", "rewrite the flagged one-pager findings in dashboard/prose.json, rebuild the "
                 "bundle, page and one-pager, then re-run rubric_check.py and every judge", False),
    "synthesis": ("Synthesis fix", "rewrite the flagged headlines, cards, moves and SWOT points in dashboard/prose.json, "
                  "check each rewording against its rows, rebuild, then re-run rubric_check.py and every judge", False),
    "source": ("Source check", "re-read each flagged sentence against its rows, fix or downgrade it, verify any newly "
               "cited row with a fresh verifier (references/verification.md), rebuild, then re-run every judge", True),
    "present": ("Page rebuild", "rebuild the bundle and page, then re-run render_test.py", False),
    "close": ("Close", "fix the failed finalize.py checks, then re-run finalize.py", False),
    "judges": ("Judges", "run judges.py prepare, the judge agents in references/judges.md, then judges.py collect", False),
    "rubric": ("Rubric check", "re-run rubric_check.py on the current bundle", False),
    "cost": ("Cost report", "re-run cost_report.py after the judges, so it counts all model use", False),
    "budget": ("Budget", "set the missing cap in run.json budgets; that is the user's decision, never the run's", False),
    "cap": ("Spend", "spend is past a cap, and any re-run adds to it; only the user who set the cap can raise it", False),
}
RULE_MODULE = {"R03": "onepager", "R04": "onepager", "R05": "onepager", "R06": "onepager",
               "R18": "source", "R19": "source", "R20": "source", "R22": "present"}


def now():
    return datetime.now(timezone.utc)


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def money(text, pattern):
    m = pattern.search(text or "")
    return float(m.group(1).replace(",", "")) if m else None


def as_failure(f, rule):
    """A code failure may be a string or a dict; a judge failure is a dict. Either becomes {rule, item, quote, reason}."""
    if isinstance(f, dict):
        out = {"rule": rule, "item": f.get("item"), "quote": f.get("quote"), "reason": f.get("reason") or f.get("detail")}
        out.update({k: v for k, v in f.items() if k not in out})
        return out
    return {"rule": rule, "item": None, "quote": None, "reason": str(f)}


class Gate:
    def __init__(self, run, meta, rnd):
        self.run, self.meta, self.round = run, meta, rnd
        self.inputs, self.gates, self.rules = [], [], []
        bundle = run / "dashboard" / "bundle.json"
        self.bundle_time = bundle.stat().st_mtime if bundle.exists() else None
        self.bundle_sha = sha256(bundle) if bundle.exists() else None
        self.note("dashboard/bundle.json", bundle.exists(), "present" if bundle.exists() else
                  "missing: build the page first", "present")

    def note(self, rel, ok, detail, module):
        self.inputs.append({"file": rel, "ok": bool(ok), "detail": detail, "module": module})

    def stale(self, rel):
        path = self.run / rel
        return self.bundle_time is not None and path.stat().st_mtime < self.bundle_time

    # ------------------------------------------------------------ inputs

    def load_rubric(self):
        rubric = read_json(self.run / "rubric.json")
        rows = [r for r in rubric if isinstance(r, dict) and r.get("id")] if isinstance(rubric, list) else []
        if not rows:
            self.note("rubric.json", False, "missing, empty or not a list: copy the rubric into the run root at intake",
                      None)
        else:
            self.note("rubric.json", True, f"{len(rows)} rules", None)
        return rows

    def load_code(self):
        rel = "verify/rubric-code.json"
        data = read_json(self.run / rel)
        rows = data if isinstance(data, list) else (data.get("rows") or data.get("rules")) if isinstance(data, dict) else None
        if data is None:
            self.note(rel, False, "missing: run rubric_check.py", "rubric")
            return None
        if not isinstance(rows, list):
            self.note(rel, False, "unreadable: expected a list of rows {id, level, status, failures, note}", "rubric")
            return None
        if self.stale(rel):
            self.note(rel, False, "older than dashboard/bundle.json: run rubric_check.py again", "rubric")
            return None
        self.note(rel, True, f"{len(rows)} rows", "rubric")
        return {str(r.get("id")): r for r in rows if isinstance(r, dict) and r.get("id")}

    def load_judges(self):
        rel = "verify/judges.json"
        data = read_json(self.run / rel)
        if not isinstance(data, dict) or not isinstance(data.get("rules"), dict):
            self.note(rel, False, "missing or unreadable: run judges.py prepare, the judges, then judges.py collect", "judges")
            return None
        if data.get("bundle_sha") != self.bundle_sha:
            self.note(rel, False, "judged an older bundle: run judges.py prepare, the judges and collect again", "judges")
            return None
        self.note(rel, True, f"{len(data['rules'])} judge rules", "judges")
        return data["rules"]

    # ------------------------------------------------------------ hard gates

    def gate(self, name, ok, detail, module, **extra):
        row = {"gate": name, "ok": bool(ok), "detail": detail, "module": None if ok else module}
        row.update(extra)
        self.gates.append(row)

    def check_finalize(self):
        rel = "verify/finalize.json"
        data = read_json(self.run / rel)
        if data is None:
            return self.gate("finalize", False, "verify/finalize.json is missing: run finalize.py", "close")
        checks = data if isinstance(data, list) else data.get("checks") if isinstance(data, dict) else None
        top_ok = data.get("ok") is True if isinstance(data, dict) else True
        if not isinstance(checks, list) or not checks:
            return self.gate("finalize", False, "verify/finalize.json has no checks", "close")
        if self.stale(rel):
            return self.gate("finalize", False, "verify/finalize.json is older than the bundle: run finalize.py again", "close")
        failed = [str(c.get("check") or c) for c in checks if not (isinstance(c, dict) and c.get("ok") is True)]
        ok = top_ok and not failed
        self.gate("finalize", ok, "every check passed" if ok else "failed: " + ("; ".join(failed) or "ok is not true"),
                  "close")

    def check_render(self):
        rel = "dashboard/screens/render-report.md"
        text = read_text(self.run / rel)
        if text is None:
            return self.gate("render test", False, f"{rel} is missing: run render_test.py", "present")
        if self.stale(rel):
            return self.gate("render test", False, f"{rel} is older than the bundle: rebuild and run render_test.py", "present")
        ok = bool(RENDER_PASS.search(text))
        self.gate("render test", ok, "Result: PASS" if ok else f"{rel} has no 'Result: **PASS**' line", "present")

    def check_spend(self):
        rel = "cost-report.md"
        text = read_text(self.run / rel)
        budgets = self.meta.get("budgets") if isinstance(self.meta.get("budgets"), dict) else {}
        judges = self.run / "verify" / "judges.json"
        problem = None
        if text is None:
            problem = "cost-report.md is missing: run cost_report.py"
        elif self.stale(rel) or (judges.exists() and (self.run / rel).stat().st_mtime < judges.stat().st_mtime):
            problem = "cost-report.md is older than the bundle or verify/judges.json: run cost_report.py again"
        for name, line, cap_key, label in (("model spend", MODEL_LINE, "model_usd_cap", "Model use total"),
                                           ("data spend", DATA_LINE, "treg_usd_cap", "Total logged spend")):
            cap = budgets.get(cap_key)
            cap = float(cap) if isinstance(cap, (int, float)) and not isinstance(cap, bool) else None
            spend = None if problem else money(text, line)
            if problem:
                self.gate(name, False, problem, "cost", spend=None, cap=cap)
            elif spend is None:
                self.gate(name, False, f"cost-report.md has no '{label}: X USD' line, so this spend was not measured",
                          "cost", spend=None, cap=cap)
            elif cap is None:
                self.gate(name, False, f"run.json budgets has no {cap_key}, so spend can't be checked against a cap",
                          "budget", spend=spend, cap=None)
            else:
                ok = spend <= cap
                self.gate(name, ok, f"{spend:.2f} USD against a cap of {cap:.2f} USD", "cap", spend=spend, cap=cap)

    # ------------------------------------------------------------ rules and decision

    def score_rules(self, rubric, code, judges):
        for r in rubric:
            rid, check = str(r["id"]), str(r.get("check") or "")
            level = r.get("level") if r.get("level") in ("must", "should") else "must"
            entry = {"id": rid, "level": level, "check": check, "status": "missing", "failures": [], "note": ""}
            if check == "code":
                row = (code or {}).get(rid)
                if code is None:
                    entry["note"] = "verify/rubric-code.json is missing or stale"
                elif row is None:
                    entry["note"] = "no row in verify/rubric-code.json"
                elif row.get("status") not in CODE_STATUS:
                    entry["note"] = f"status {row.get('status')!r} is not pass, fail or n/a"
                else:
                    entry.update(status=row["status"], note=str(row.get("note") or ""),
                                 failures=[as_failure(f, rid) for f in row.get("failures") or []])
            elif check.startswith("judge:"):
                row = (judges or {}).get(rid)
                if judges is None:
                    entry["note"] = "verify/judges.json is missing or stale"
                elif not isinstance(row, dict) or row.get("status") not in ("pass", "fail"):
                    entry["note"] = "no result in verify/judges.json"
                elif row.get("problems") or row.get("missing"):
                    # The judge did not finish, so there is no result to fix from: an incomplete input, never a revise.
                    gaps = list(row.get("problems") or [])
                    if row.get("missing"):
                        gaps.append(f"{len(row['missing'])} items have no verdict row, such as "
                                    + ", ".join(row["missing"][:3]))
                    entry["note"] = "judging incomplete: " + "; ".join(gaps)
                else:
                    entry["status"] = row["status"]
                    entry["failures"] = [as_failure(f, rid) for f in row.get("failing") or []]
                    entry["note"] = f"{check[6:]} judge"
            else:
                entry["note"] = f"unknown check {check!r}"
            entry["blocking"] = level == "must" and entry["status"] in ("fail", "missing")
            self.rules.append(entry)

    def decide(self):
        bad_inputs = [i for i in self.inputs if not i["ok"]]
        bad_gates = [g for g in self.gates if not g["ok"]]
        must_missing = [e for e in self.rules if e["level"] == "must" and e["status"] == "missing"]
        must_fail = [e for e in self.rules if e["level"] == "must" and e["status"] == "fail"]
        reasons = [f"Missing or stale input, {i['file']}: {i['detail']}." for i in bad_inputs]
        reasons += [f"Hard gate failed, {g['gate']}: {g['detail']}." for g in bad_gates]
        reasons += [f"Must rule {e['id']} has no result ({e['note']})." for e in must_missing]
        if bad_inputs or bad_gates or must_missing:
            release = "hold"
            reasons += [f"Must rule {e['id']} fails." for e in must_fail]
        elif must_fail and self.round < MAX_ROUNDS:
            release = "revise"
            reasons += [f"Must rule {e['id']} fails: fix round {self.round + 1} of {MAX_ROUNDS}." for e in must_fail]
        elif must_fail:
            release = "hold"
            reasons += [f"Must rule {e['id']} still fails after {self.round} fix rounds." for e in must_fail]
        else:
            release = "pass"
        return release, reasons, must_fail

    def scorecard(self):
        release, reasons, must_fail = self.decide()
        return {"ts": now().isoformat(timespec="seconds"), "round": self.round, "max_rounds": MAX_ROUNDS,
                "release": release, "exit": EXIT[release], "reasons": reasons,
                "inputs": self.inputs, "hard_gates": self.gates, "rules": self.rules,
                "must_failing": [e["id"] for e in must_fail],
                "should_failing": [e["id"] for e in self.rules if e["level"] == "should" and e["status"] in ("fail", "missing")],
                "fix": [f for e in must_fail for f in e["failures"]]}


# ---------------------------------------------------------------- HOLD.md

def describe(f):
    head = f"`{f['item']}`" if f.get("item") else ""
    extras = [f"{k} {f[k]}" for k in ("role", "label", "step", "support", "stretch", "call", "flag") if f.get(k)]
    if extras:
        head += (" " if head else "") + "(" + ", ".join(extras) + ")"
    body = ". ".join(x for x in (f"\"{f['quote']}\"" if f.get("quote") else "", str(f.get("reason") or "")) if x)
    return ": ".join(x for x in (head, body) if x) or "no detail given"


def headroom(gates, name, label):
    g = next((g for g in gates if g["gate"] == name), {})
    spend, cap = g.get("spend"), g.get("cap")
    if spend is None or cap is None:
        return f"the {label} left under its cap is unknown"
    if spend > cap:
        return f"the {label} cap is already passed ({spend:.2f} of {cap:.2f} USD), so this needs a higher cap first"
    return f"{cap - spend:.2f} USD of {label} left under the cap of {cap:.2f} USD"


def module_of(entry):
    if entry["status"] == "missing":
        return "rubric" if entry["check"] == "code" else "judges"
    items = [str(f.get("item") or "") for f in entry["failures"]]
    if items and all(i.startswith("onepager.") for i in items):
        return "onepager"
    return RULE_MODULE.get(entry["id"], "synthesis")


def onepager_option(card, rubric_by_id):
    hurt, unknown = [], []
    for e in card["rules"]:
        if not e["blocking"]:
            continue
        if e["status"] == "missing":
            unknown.append(e["id"])
            continue
        ops = [str(f.get("item")) for f in e["failures"] if str(f.get("item") or "").startswith("onepager.")]
        if ops:
            hurt.append(f"{e['id']} ({', '.join(sorted(set(ops))[:4])})")
        elif e["check"] == "code" and "one-pager" in str(rubric_by_id.get(e["id"], {}).get("applies_to") or ""):
            hurt.append(f"{e['id']} (a code rule that covers the one-pager: its failures above say where)")
    if hurt:
        text = "Not clean yet. The one-pager itself fails " + "; ".join(hurt) + "."
    elif unknown:
        text = "Unclear: " + ", ".join(unknown) + " have no result, so the one-pager's own state is unknown."
    else:
        text = ("The one-pager passes every must rule that covers it. Its \"How we got here\" links and its way-in line "
                "point to the full report, so they need removing or rewording before it goes out alone.")
    if any(g["gate"] == "render test" and not g["ok"] for g in card["hard_gates"]):
        text += " The render test failed too, so look at dashboard/onepager.pdf before sending it."
    return text


def hold_md(card, meta, rubric_by_id):
    name = meta.get("target") or meta.get("slug") or "this"
    lines = [f"# On hold: the {name} report was not released", "",
             f"gate.py checked this run at {card['ts']}, at fix round {card['round']} of {card['max_rounds']}. "
             "Nothing was sent.", "", "## What stopped it", ""]
    lines += [f"- {r}" for r in card["reasons"]]
    lines += ["", "## Failing items", ""]
    blocking = [e for e in card["rules"] if e["blocking"]]
    for e in blocking:
        lines.append(f"### {e['id']} ({e['level']}, {e['check']})")
        rule_text = rubric_by_id.get(e["id"], {}).get("rule")
        if rule_text:
            lines += ["", str(rule_text)]
        lines.append("")
        if e["status"] == "missing":
            lines.append(f"- No result: {e['note']}.")
        for f in e["failures"][:20]:
            lines.append(f"- {describe(f)}")
        if len(e["failures"]) > 20:
            lines.append(f"- {len(e['failures']) - 20} more in verify/scorecard.json.")
        lines.append("")
    if not blocking:
        lines += ["No must rule failed. The hold comes from the inputs or hard gates above.", ""]
    should = [e for e in card["rules"] if e["level"] == "should" and e["status"] in ("fail", "missing")]
    if should:
        lines += ["Should rules that also failed (reported only, never a reason to hold): "
                  + ", ".join(e["id"] for e in should) + ".", ""]
    mods = {}
    for e in blocking:
        mods.setdefault(module_of(e), []).append(e["id"])
    for x in [i for i in card["inputs"] if not i["ok"] and i.get("module")] + [g for g in card["hard_gates"] if not g["ok"]]:
        mods.setdefault(x["module"], []).append(x.get("file") or x.get("gate"))
    model = headroom(card["hard_gates"], "model spend", "model use")
    data = headroom(card["hard_gates"], "data spend", "data spend")
    lines += ["## Options", "", f"1. **Ship the one-pager only.** {onepager_option(card, rubric_by_id)}", "",
              "2. **Re-run a module.** Each line names what it would fix, what it involves and its cost."]
    for key, what in mods.items():
        title, work, buys_data = MODULES.get(key, (key, "see the reasons above", False))
        if key in ("budget", "cap"):
            cost = "No re-run helps until the cap question is settled."
        elif buys_data:
            cost = f"Cost: model use ({model}), plus a few paid data calls if a verifier needs one ({data})."
        else:
            cost = f"Cost: model use only, no paid data ({model})."
        lines.append(f"   - {title}, for {', '.join(dict.fromkeys(what))}: {work}. {cost}")
    lines += ["", "3. **Decline.** Send nothing. The run stays on disk as it is, and this file and "
              "verify/scorecard.json record why.", ""]
    return "\n".join(lines)


def archive_hold(run):
    old = run / "HOLD.md"
    if not old.exists():
        return
    dest_dir = run / "verify" / "holds"
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = now().strftime("%Y%m%dT%H%M%SZ")
    dest, n = dest_dir / f"HOLD-{stamp}.md", 2
    while dest.exists():
        dest, n = dest_dir / f"HOLD-{stamp}-{n}.md", n + 1
    old.replace(dest)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--round", type=int, default=0, help="fix rounds already run; 0 on the first check")
    args = ap.parse_args(argv)
    run = args.run_dir
    meta = read_json(run / "run.json") if run.is_dir() else None
    if not isinstance(meta, dict):
        print(f"ERROR: {run} is not a usable run folder (no readable run.json)", file=sys.stderr)
        return 2
    if args.round < 0:
        print("ERROR: --round counts fix rounds already run, from 0", file=sys.stderr)
        return 2
    g = Gate(run, meta, args.round)
    rubric = g.load_rubric()
    code, judges = g.load_code(), g.load_judges()
    g.check_finalize()
    g.check_render()
    g.check_spend()
    g.score_rules(rubric, code, judges)
    card = g.scorecard()
    (run / "verify").mkdir(exist_ok=True)
    (run / "verify" / "scorecard.json").write_text(json.dumps(card, indent=1, ensure_ascii=False) + "\n",
                                                   encoding="utf-8", newline="\n")
    archive_hold(run)
    if card["release"] == "hold":
        (run / "HOLD.md").write_text(hold_md(card, meta, {str(r["id"]): r for r in rubric}), encoding="utf-8", newline="\n")
    for e in card["rules"]:
        print(f"{e['status']:<7} {e['id']} ({e['level']}, {e['check']}){': ' + e['note'] if e['note'] else ''}")
    for x in card["hard_gates"]:
        print(f"{'pass' if x['ok'] else 'FAIL':<7} gate {x['gate']}: {x['detail']}")
    for i in card["inputs"]:
        if not i["ok"]:
            print(f"FAIL    input {i['file']}: {i['detail']}")
    if card["release"] == "revise":
        print(f"Fix these {len(card['fix'])} items, then rebuild, re-judge and run gate.py --round {args.round + 1}:")
        for f in card["fix"]:
            print(f"- {f['rule']}: {describe(f)}")
    print(f"RELEASE: {card['release'].upper()}" + (" (see HOLD.md)" if card["release"] == "hold" else ""))
    return card["exit"]


if __name__ == "__main__":
    sys.exit(main())
