#!/usr/bin/env python3
"""Read-only health check of running workstreams. The last printed line is a one-line summary.

Usage: python -I watch.py <run-dir> [--stale-min 15] [--dead-min 45] [--no-progress-min 10]
                                    [--until-change] [--max-min 120] [--outage-reported]
Age comes from the newest ts in progress.jsonl and heartbeat.log, and from the progress.jsonl mtime only when neither has a ts.
--until-change polls every 60 seconds and exits when a recommendation appears or all workstreams finish.
--max-min stops that loop after this many minutes and says so.
--outage-reported keeps that loop polling through a SHARED-OUTAGE the user has already been told about.
Exit 0 always, unless the run folder is invalid (exit 2).
"""
import argparse, json, sys, time
from datetime import datetime, timezone
from pathlib import Path


class RunError(Exception):
    pass


def parse_ts(value):
    try:
        dt = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).timestamp()


def read_run(run):
    if not run.is_dir():
        raise RunError(f"{run} is not a folder")
    try:
        data = json.loads((run / "run.json").read_text(encoding="utf-8-sig"))
        workstreams = data["workstreams"]
        if not isinstance(workstreams, dict) or not all(isinstance(v, dict) for v in workstreams.values()):
            raise TypeError("workstreams must be an object of objects")
        for info in workstreams.values():
            int(info.get("resumes") or 0)
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise RunError(f"cannot use {run / 'run.json'}: {type(e).__name__}: {e}")
    return workstreams


def read_heartbeats(run, warnings):
    """Return {ws: (latest timestamp, n)} from heartbeat.log, warning on every malformed line."""
    path, beats = run / "heartbeat.log", {}
    if not path.exists():
        warnings.append("heartbeat.log is missing")
        return beats
    for lineno, line in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").split("\n"), 1):
        if not line.strip():
            continue
        parts = line.split(None, 3)
        ts = parse_ts(parts[0]) if parts else None
        if ts is None or len(parts) < 3 or not parts[2].isdigit():
            warnings.append(f"heartbeat.log:{lineno} is malformed: {line[:60]!r}")
        elif parts[1] not in beats or ts >= beats[parts[1]][0]:
            beats[parts[1]] = (ts, int(parts[2]))
    return beats


def read_progress(path, warnings):
    """Return (the n of the last valid progress.jsonl row or None, the newest readable ts or None)."""
    n, newest = None, None
    for lineno, raw in enumerate(path.read_bytes().split(b"\n"), 1):
        if raw.strip():
            try:
                row = json.loads(raw.decode("utf-8-sig"))
                ts = parse_ts(row.get("ts")) if isinstance(row, dict) else None
                if ts is not None and (newest is None or ts > newest):
                    newest = ts
                n = int(row["n"])
            except (ValueError, KeyError, TypeError) as e:
                warnings.append(f"{path.parent.name}/progress.jsonl:{lineno} is malformed ({e})")
    return n, newest


def assess(run, args, now=None):
    """Return (report lines, recommendations, all finished)."""
    now = time.time() if now is None else now
    workstreams = read_run(run)
    warnings, states = [], []
    beats = read_heartbeats(run, warnings)
    running = {ws: info for ws, info in workstreams.items() if info.get("status") == "running"}
    for ws, info in sorted(running.items()):
        path = run / "research" / ws / "progress.jsonl"
        has_progress = path.exists()
        started = parse_ts(info["started"]) if info.get("started") else None
        if info.get("started") and started is None:
            warnings.append(f"{ws} has an unreadable started time: {info['started']!r}")
        saved, progress_ts = read_progress(path, warnings) if has_progress else (None, None)
        marks = [t for t in (progress_ts, beats[ws][0] if ws in beats else None) if t is not None]
        if not marks and has_progress:
            marks.append(path.stat().st_mtime)
        base = max(marks) if marks else started
        age = None if base is None else max(0.0, now - base) / 60
        if base is None:
            warnings.append(f"{ws} is running with no started time and no activity; its age is unknown")
        missing = not has_progress and started is not None and (now - started) / 60 >= args.no_progress_min
        states.append({"ws": ws, "age": age, "saved": saved, "items": saved if saved is not None else beats.get(ws, (0, 0))[1],
                       "stale": age is not None and age > args.stale_min, "dead": age is not None and age > args.dead_min,
                       "resumes": int(info.get("resumes") or 0), "missing": missing})
    recs, lines = [], [f"WARN {w}" for w in warnings]
    stale = [s for s in states if s["stale"]]
    # One running workstream gives no second signal to tell an outage from a hang, so per-workstream rules apply.
    outage = len(states) >= 2 and len(stale) == len(states)
    if outage:
        recs.append(f"SHARED-OUTAGE, most likely this computer slept ({len(stale)} running, all stale): relaunch nothing, report once to the user, keep polling; "
                    "if this is a new session and the agents are gone, relaunch each workstream from its last saved item")
    for s in states:
        notes, resume_at = [], (s["saved"] or 0) + 1
        if outage:
            notes.append("HOLD (shared outage)")
        elif s["dead"] and s["resumes"] >= 1:
            notes.append(f"RELAUNCH {s['ws']} from progress, item {resume_at}")
        elif s["stale"]:
            notes.append(f"RESUME {s['ws']} from item {resume_at}")
        if s["missing"]:
            notes.append(f"SAVE-MISSING {s['ws']}: no progress.jsonl {args.no_progress_min:g}+ min after start")
        if not outage:
            recs += notes
        age = "unknown" if s["age"] is None else f"{s['age']:.1f}m"
        lines.append(f"{s['ws']}  age {age}  items {s['items']}  resumes {s['resumes']}  {'; '.join(notes) or 'OK'}")
    finished = bool(workstreams) and all(i.get("status") in ("done", "failed") for i in workstreams.values())
    if finished:
        recs_text = "ALL-FINISHED"
    elif not states:
        recs_text = "nothing running"
    else:
        recs_text = "; ".join(recs) or "all fresh"
    lines.append(f"WATCH running={len(states)} stale={len(stale)} total={len(workstreams)} | {recs_text}")
    return lines, recs, finished


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--stale-min", type=float, default=15)
    ap.add_argument("--dead-min", type=float, default=45)
    ap.add_argument("--no-progress-min", type=float, default=10)
    ap.add_argument("--until-change", action="store_true")
    ap.add_argument("--max-min", type=float, default=120, help="stop --until-change after this many minutes")
    ap.add_argument("--outage-reported", action="store_true")
    args = ap.parse_args()
    first, deadline = True, time.monotonic() + args.max_min * 60
    while True:
        try:
            lines, recs, finished = assess(args.run_dir, args)
        except RunError as e:
            if first:
                print(f"ERROR: {e}", file=sys.stderr)
                return 2
            lines, recs, finished = [], [], False  # run.json may be mid-rewrite; the next poll rereads it
        first = False
        actionable = [r for r in recs if not (args.outage_reported and r.startswith("SHARED-OUTAGE"))]
        if not args.until_change or actionable or finished:
            print("\n".join(lines), flush=True)
            return 0
        left = deadline - time.monotonic()
        if left <= 0:
            stop = f"stopped polling after {args.max_min:g} min (--max-min) with nothing to act on"
            lines = lines[:-1] + [f"{lines[-1]} | {stop}"] if lines else [f"WATCH {stop}"]
            print("\n".join(lines), flush=True)
            return 0
        time.sleep(min(60, left))


if __name__ == "__main__":
    sys.exit(main())
