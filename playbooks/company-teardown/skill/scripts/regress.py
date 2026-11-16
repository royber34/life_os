#!/usr/bin/env python3
"""Replay the deterministic end of a run on a frozen fixture and compare it with the golden output.

    python -I regress.py <fixture-dir> [--no-render] [--keep] [--rebaseline]

A fixture is a copy of a finished run's S5 inputs (config.json, run.json, the 03-09 files, research/*/section.md,
claims.jsonl, campaign files, research/merged/, verify/ledger.jsonl, verdicts, report, corrections, and
dashboard/prose.json) plus golden copies in <fixture>/frozen/ (bundle.json, index.html) and, optionally,
verify/report.frozen.json. The fixture itself is never changed: everything runs in a temporary copy.

Steps, each must pass: ledger report, ledger check-citations, build_dashboard assemble, validate and build,
byte comparison of report.json, bundle.json and index.html with the golden copies, and the render test.
It costs no research spend and no model tokens. It tests scripts and templates; a change in what the
writing stage produces needs a model-backed replay instead.
After a reviewed, intended change to the scripts or the template, --rebaseline copies the new outputs over the
golden copies, but only when every step other than the byte comparisons passed (render test included).
Exit 0 when every step passes, 1 otherwise, 2 on an unusable fixture.
"""
import argparse, hashlib, shutil, subprocess, sys, tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16] if path.exists() else None


def step(name, cmd, cwd):
    res = subprocess.run([sys.executable, *cmd], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = (res.stdout + res.stderr).strip().splitlines()[-1:] or [""]
    return res.returncode == 0, f"exit {res.returncode}: {tail[0][:160]}"


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("fixture", type=Path)
    ap.add_argument("--no-render", action="store_true", help="skip the browser render test")
    ap.add_argument("--keep", action="store_true", help="keep the temporary copy and print its path")
    ap.add_argument("--rebaseline", action="store_true", help="accept the new outputs as golden, if all other steps pass")
    args = ap.parse_args(argv)
    fx = args.fixture.resolve()
    golden = fx / "frozen"
    if not (fx / "run.json").exists() or not (golden / "index.html").exists():
        print(f"ERROR: {fx} is not a fixture (needs run.json and frozen/index.html)", file=sys.stderr)
        return 2
    tmp = Path(tempfile.mkdtemp(prefix="regress-"))
    work = tmp / fx.name
    shutil.copytree(fx, work, ignore=shutil.ignore_patterns("frozen"))
    rows = []
    py = ["-I"]
    rows.append(("ledger report", *step("ledger report", py + [str(SCRIPTS / "ledger.py"), "report", str(work)], tmp)))
    rows.append(("ledger check-citations", *step("check", py + [str(SCRIPTS / "ledger.py"), "check-citations", str(work)], tmp)))
    for cmd in ("assemble", "validate", "build"):
        rows.append((f"build_dashboard {cmd}", *step(cmd, py + [str(SCRIPTS / "build_dashboard.py"), cmd, str(work)], tmp)))
    pairs = [("verify/report.json", fx / "verify" / "report.frozen.json"),
             ("dashboard/bundle.json", golden / "bundle.json"),
             ("dashboard/index.html", golden / "index.html")]
    for rel, gold in pairs:
        if not gold.exists():
            rows.append((f"same {rel}", True, "no golden copy, skipped"))
            continue
        got, want = sha(work / rel), sha(gold)
        rows.append((f"same {rel}", got == want, f"{got} vs golden {want}"))
    if not args.no_render:
        rows.append(("render test", *step("render", [str(SCRIPTS / "render_test.py"), str(work / "dashboard" / "index.html"),
                                                      str(work / "dashboard" / "screens")], tmp)))
    for name, ok, detail in rows:
        print(f"{'pass' if ok else 'FAIL'}  {name}: {detail}")
    failed = [r for r in rows if not r[1]]
    if args.rebaseline:
        other = [r for r in failed if not r[0].startswith("same ")]
        if other:
            print(f"NOT REBASELINED: {len(other)} step(s) other than the byte comparisons failed")
        else:
            for rel, gold in pairs:
                if (work / rel).exists():
                    gold.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(work / rel, gold)
            print("REBASELINED: the golden copies now match this build")
            failed = []
    print("REGRESSION OK" if not failed else f"REGRESSION FAILED: {len(failed)} step(s)")
    if args.keep:
        print(f"Kept: {work}")
    else:
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
