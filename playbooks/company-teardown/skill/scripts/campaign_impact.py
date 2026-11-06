#!/usr/bin/env python3
"""Before-and-after study of campaigns against key metrics, net of season and controls.

Usage: python -I campaign_impact.py <study.json>

Reads a study file and writes campaign_impact.jsonl, series.json and summary.json next to it. build_dashboard.py picks up
the first two from research/*/. Nothing here measures sales: the verdicts say whether a metric moved beyond its normal
range. Format of the study file is in references/performance-briefs.md.

Exit 0 on success, 2 on unusable input.
"""
import datetime as dt, json, statistics as st, sys
from collections import Counter, defaultdict
from pathlib import Path

WINDOWS = {"weekly": dict(before=8, after=8, lag=52, span=56), "monthly": dict(before=3, after=3, lag=12, span=92)}
MIN_PLACEBO = 20
MODE_TEXT = {
    "full": "net = own ratio / (own prior-year ratio x control ratio / control prior-year ratio) - 1",
    "cat": "net = own ratio / control ratio - 1 (no prior-year window)",
    "seas": "net = own ratio / own prior-year ratio - 1 (no valid control)",
}


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def percentile(values, q):
    """Linear interpolation, the same rule as numpy's default, so results don't depend on numpy being installed."""
    v = sorted(values)
    k = (len(v) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def mean_window(series, lo, hi):
    if lo < 0 or hi > len(series):
        return None
    window = series[lo:hi]
    return None if any(x is None for x in window) else sum(window) / len(window)


def change(series, i, before, after, lag=0):
    b, a = mean_window(series, i - before - lag, i - lag), mean_window(series, i - lag, i - lag + after)
    if b is None or a is None or b == 0:
        return None
    return b, a, (a / b - 1) * 100


def parts(own, controls, i, win):
    c = change(own, i, win["before"], win["after"])
    if c is None:
        return None
    moves = [x[2] for x in (change(s, i, win["before"], win["after"]) for s in controls) if x]
    prior = [x[2] for x in (change(s, i, win["before"], win["after"], win["lag"]) for s in controls) if x]
    py = change(own, i, win["before"], win["after"], win["lag"])
    return c, st.median(moves) if len(moves) >= 3 else None, py[2] if py else None, st.median(prior) if len(prior) >= 3 else None


def ratio(p):
    return 1 + p / 100.0


def net_from(c, cm, py, cpy, mode):
    if mode == "full":
        if None in (cm, py, cpy):
            return None
        den = ratio(py) * ratio(cm) / ratio(cpy)
    elif mode == "cat":
        if cm is None:
            return None
        den = ratio(cm)
    elif mode == "seas":
        if py is None:
            return None
        den = ratio(py)
    else:
        return None
    return (ratio(c[2]) / den - 1) * 100 if den > 0 else None


def control_move(cm, cpy):
    return None if cm is None else ratio(cm) / (ratio(cpy) if cpy is not None else 1.0)


def detail(own, controls, i, win, seasonal_only):
    p = parts(own, controls, i, win)
    if p is None:
        return None
    c, cm, py, cpy = p
    if seasonal_only:
        mode = "seas" if py is not None else None
    else:
        mode = "full" if None not in (cm, py, cpy) else "cat" if cm is not None else "seas" if py is not None else None
    return dict(before=c[0], after=c[1], change=c[2], py=py, cm=cm, cpy=cpy, mode=mode, net=net_from(c, cm, py, cpy, mode) if mode else None,
                gate=control_move(cm, cpy) if mode in ("full", "cat") else None)


def placebo_band(own, controls, win, mode):
    nets, gates = [], []
    for j in range(win["before"], len(own) - win["after"] + 1):
        p = parts(own, controls, j, win)
        if p is None:
            continue
        v = net_from(*p, mode)
        if v is not None:
            nets.append(v)
        g = control_move(p[1], p[3])
        if g is not None:
            gates.append(g)
    if len(nets) < MIN_PLACEBO:
        return None
    out = dict(lo=percentile(nets, 5), hi=percentile(nets, 95), n=len(nets))
    if len(gates) >= MIN_PLACEBO:
        out.update(glo=percentile(gates, 5), ghi=percentile(gates, 95))
    return out


def judge(d, band):
    if d is None or d["net"] is None or band is None:
        return "not measurable", "window, adjustment data or placebo sample missing"
    if d.get("gate") is not None and "glo" in band and not band["glo"] <= d["gate"] <= band["ghi"]:
        return "not measurable", "category shock: controls moved outside their normal range, so the adjustment can't be trusted"
    if d["net"] > band["hi"]:
        return "above noise", "net above the 95th percentile of placebo windows"
    if d["net"] < band["lo"]:
        return "negative", "net below the 5th percentile of placebo windows"
    return "within noise", "net inside the middle 90% of placebo windows"


def month_key(day):
    """A date after the 15th counts from the next month, so the after window holds mostly post-campaign days."""
    y, m, d_ = int(day[:4]), int(day[5:7]), int(day[8:10])
    if d_ > 15:
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return f"{y:04d}-{m:02d}"


def align(points, axis):
    values = {str(d)[:len(axis[0])]: v for d, v in points}
    return [None if values.get(a) is None else float(values[a]) for a in axis]


def weekly_to_monthly(points, axis):
    groups = defaultdict(list)
    for d, v in points:
        if v is not None:
            groups[str(d)[:7]].append(float(v))
    return [sum(groups[a]) / len(groups[a]) if len(groups.get(a, [])) >= 3 else None for a in axis]


def prepare_pull(pull, cadence):
    own = sorted((str(d), v) for d, v in pull["own"])
    if not own:
        die(f"pull {pull.get('id')} has no points")
    axis = [d for d, _ in own]
    if cadence == "monthly":
        axis = [d[:7] for d in axis]
        controls = {k: (weekly_to_monthly(v, axis) if pull.get("controls_weekly") else align(v, axis)) for k, v in (pull.get("controls") or {}).items()}
    else:
        controls = {k: align(v, axis) for k, v in (pull.get("controls") or {}).items()}
    return dict(id=pull.get("id", "main"), axis=axis, own=[None if v is None else float(v) for _, v in own], controls=list(controls.values()))


def locate(pull, cadence, start):
    if cadence == "monthly":
        key = month_key(start)
        return pull["axis"].index(key) if key in pull["axis"] else None
    if start < pull["axis"][0]:
        return None
    last = dt.date.fromisoformat(pull["axis"][-1]) + dt.timedelta(days=7)
    if start >= last.isoformat():
        return None
    return max(i for i, d in enumerate(pull["axis"]) if d <= start)


def overlaps(campaign, campaigns, span):
    day = dt.date.fromisoformat(campaign["start"])
    return [c["id"] for c in campaigns if c["id"] != campaign["id"] and abs((dt.date.fromisoformat(c["start"]) - day).days) < span]


def study(spec):
    campaigns, rows, series = spec.get("campaigns") or [], [], []
    for key in ("id", "name", "type", "start"):
        missing = [c.get("id", "?") for c in campaigns if not c.get(key)]
        if missing:
            die(f"campaigns missing {key}: {missing}")
    for metric in spec.get("metrics") or []:
        cadence = metric.get("cadence")
        if cadence not in WINDOWS:
            die(f"metric {metric.get('id')}: cadence must be weekly or monthly")
        win = WINDOWS[cadence]
        pulls = [prepare_pull(p, cadence) for p in metric.get("pulls") or []]
        for raw in metric.get("pulls") or []:
            series.append(dict(metric=raw.get("series_id") or metric["id"], label=raw.get("label") or metric["label"], unit=metric.get("unit"), points=sorted([str(d), v] for d, v in raw["own"])))
            for name, pts in (raw.get("controls") or {}).items():
                series.append(dict(metric=f"control_{name.replace(' ', '_')}_{raw.get('id', 'main')}", label=f"Control: {name}", unit=metric.get("unit"), points=sorted([str(d), v] for d, v in pts)))
        seasonal_only = metric.get("adjust") == "seasonal"
        for c in campaigns:
            row = dict(campaign=c["name"], campaign_id=c["id"], campaign_type=c["type"], start=c["start"], start_precision=c.get("precision", "day"),
                       metric=metric["id"], metric_label=metric["label"], unit=metric.get("unit"), window=None, before=None, after=None, change_pct=None,
                       prior_year_change_pct=None, control_change_pct=None, control_prior_year_change_pct=None, net_pct=None, noise_band_pct=None,
                       noise_band_lo_pct=None, placebo_windows=None, adjustment=None, verdict="not measurable", verdict_reason=None,
                       overlaps=overlaps(c, campaigns, win["span"]), kind=cadence, note=c.get("note") or "", source=c.get("source"), claim_id=c.get("claim_id"), event_id=c.get("event_id"))
            precision = row["start_precision"]
            if cadence == "weekly" and precision != "day":
                row["verdict_reason"] = f"start precision is {precision}; weekly windows need a day"
                rows.append(row)
                continue
            if precision == "year":
                row["verdict_reason"] = "start precision is year; monthly windows need at least a month"
                rows.append(row)
                continue
            best = None
            for order, pull in enumerate(pulls):
                i = locate(pull, cadence, c["start"])
                if i is None or i - win["before"] < 0 or i + win["after"] > len(pull["axis"]):
                    continue
                d = detail(pull["own"], pull["controls"], i, win, seasonal_only)
                if d is None:
                    continue
                score = (d["mode"] == "full", d["mode"] is not None, order)
                if best is None or score > best[0]:
                    best = (score, pull, i, d)
            if best is None:
                row["verdict_reason"] = "no data covers a full window on each side, or the baseline is zero"
                rows.append(row)
                continue
            _, pull, i, d = best
            band = placebo_band(pull["own"], pull["controls"], win, d["mode"]) if d["mode"] else None
            verdict, reason = judge(d, band)
            row.update(window=f"{win['before']} before against {win['after']} after, from {pull['axis'][i]}; {MODE_TEXT.get(d['mode'], 'no adjustment possible')}",
                       before=round(d["before"], 2), after=round(d["after"], 2), change_pct=round(d["change"], 1),
                       prior_year_change_pct=None if d["py"] is None else round(d["py"], 1), control_change_pct=None if d["cm"] is None else round(d["cm"], 1),
                       control_prior_year_change_pct=None if d["cpy"] is None else round(d["cpy"], 1), net_pct=None if d["net"] is None else round(d["net"], 1),
                       noise_band_pct=None if not band else round(band["hi"], 1), noise_band_lo_pct=None if not band else round(band["lo"], 1),
                       placebo_windows=None if not band else band["n"], adjustment=d["mode"], verdict=verdict, verdict_reason=reason)
            rows.append(row)
    tested = [r for r in rows if r["verdict"] != "not measurable"]
    by_type = defaultdict(Counter)
    for r in tested:
        by_type[r["campaign_type"]][r["verdict"]] += 1
    summary = dict(rows=len(rows), tested=len(tested), verdicts=dict(Counter(r["verdict"] for r in rows)),
                   expected_each_tail_by_chance=round(0.05 * len(tested), 1), by_type={k: dict(v) for k, v in by_type.items()})
    return rows, series, summary


def main(argv):
    if len(argv) != 2:
        die(__doc__.splitlines()[2])
    path = Path(argv[1])
    try:
        spec = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        die(f"cannot read {path}: {e}")
    rows, series, summary = study(spec)
    (path.parent / "campaign_impact.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8", newline="\n")
    (path.parent / "series.json").write_text(json.dumps(series, ensure_ascii=False), encoding="utf-8", newline="\n")
    (path.parent / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv)
