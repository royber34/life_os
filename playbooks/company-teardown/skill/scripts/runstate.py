#!/usr/bin/env python3
"""Record run state in run.json, so state is kept by code and not by memory.

    python -I runstate.py <run-dir> start  <ws> [--agent-id ID]
    python -I runstate.py <run-dir> resume <ws> [--agent-id ID]
    python -I runstate.py <run-dir> done   <ws>
    python -I runstate.py <run-dir> failed <ws> [--why TEXT]
    python -I runstate.py <run-dir> stage  <S0..S6 or a name>
    python -I runstate.py <run-dir> gate   <G0..G4> --words TEXT
    python -I runstate.py <run-dir> show

Every change is timestamped (UTC) and appended to run-log.jsonl in the run folder.
run.json is written to a temporary file first and then swapped in, so a crash never leaves it half written.
Exit 0 on success, 2 on a usage or run-folder error.
"""
import argparse, json, os, sys
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(run):
    path = run / "run.json"
    if not path.exists():
        raise SystemExit(f"ERROR: {path} does not exist")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except ValueError as e:
        raise SystemExit(f"ERROR: {path} is not valid JSON: {e}")
    data.setdefault("workstreams", {})
    data.setdefault("gates", {})
    data.setdefault("stage_history", [])
    return data


def save(run, data, event):
    path = run / "run.json"
    tmp = path.with_name("run.json.tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    with open(run / "run-log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("action", choices=["start", "resume", "done", "failed", "stage", "gate", "show"])
    ap.add_argument("name", nargs="?")
    ap.add_argument("--agent-id")
    ap.add_argument("--why")
    ap.add_argument("--words")
    args = ap.parse_args(argv)
    run = args.run_dir
    if not run.is_dir():
        print(f"ERROR: {run} is not a folder", file=sys.stderr)
        return 2
    data = load(run)
    if args.action == "show":
        ws = data["workstreams"]
        print(f"stage {data.get('stage')}  workstreams {len(ws)}  "
              + "  ".join(f"{k}:{v.get('status')}" for k, v in sorted(ws.items())))
        return 0
    if not args.name:
        print(f"ERROR: {args.action} needs a name", file=sys.stderr)
        return 2
    ts, name = now(), args.name
    event = {"ts": ts, "action": args.action, "name": name}
    if args.action in ("start", "resume"):
        info = data["workstreams"].get(name) or {"status": "pending", "agent_id": None, "started": None, "resumes": 0}
        if args.action == "resume":
            info["resumes"] = int(info.get("resumes") or 0) + 1
        else:
            info["started"] = ts
        info["status"] = "running"
        if args.agent_id:
            info["agent_id"] = args.agent_id
        data["workstreams"][name] = info
    elif args.action in ("done", "failed"):
        info = data["workstreams"].get(name)
        if info is None:
            print(f"ERROR: {name} was never started; run start first", file=sys.stderr)
            return 2
        info["status"] = args.action
        info["ended"] = ts
        if args.why:
            info["why"] = event["why"] = args.why
    elif args.action == "stage":
        data["stage"] = name
        data["stage_history"].append({"stage": name, "ts": ts})
    elif args.action == "gate":
        if not args.words:
            print("ERROR: gate needs --words, the decision in the approver's own words (or the automatic check that passed it)",
                  file=sys.stderr)
            return 2
        data["gates"][name] = {"passed": True, "words": args.words, "date": ts[:10], "ts": ts}
        event["words"] = args.words
        # The parts of the page the brief leaves out are fixed once, at G1, when the probe has written config.json.
        # rubric_check honours only these, so a later edit to config.scope_out can't silence a rule.
        if name == "G1" and "scope_out" not in data:
            try:
                cfg = json.loads((run / "config.json").read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                cfg = {}
            data["scope_out"] = {"items": sorted(str(x) for x in cfg.get("scope_out") or []), "gate": "G1", "ts": ts}
            event["scope_out"] = data["scope_out"]["items"]
    save(run, data, event)
    print(f"{args.action} {name} at {ts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
