#!/usr/bin/env python3
"""Judge packets and verdicts for client-mode runs. The briefs are in references/judges.md.

    python -I judges.py prepare <run-dir>
    python -I judges.py prepare-compare <run-dir>
    python -I judges.py collect <run-dir>

Scripts never call a model: the orchestrator launches one fresh agent per brief.

prepare          Writes verify/judges/<judge>/packet.json for every judge the run's rubric.json names, holding only
                 the items and context that judge's brief allows, plus one agent-<name>.json per cold-reader agent
                 (the only file such an agent reads). Files left in a judge folder from an earlier round move to
                 archive-<n>/ first, so old verdicts never count again, except one way: an item whose fingerprint
                 (everything its judge sees for it) matches the round before keeps that round's decided verdict,
                 written to verdicts-carried.jsonl, and leaves the packet's items, so a fix round judges only what
                 changed. Only a verdict every run agreed on is carried (an item the runs split on is judged again),
                 and an exceptions-mode pass is carried from the closing row. The cold reader and the sceptical owner
                 run three times (REPEATS), each run in its own verdicts file, listed under the packet's agents.
prepare-compare  After the R10 restaters finish: writes verify/judges/cold-reader/compare-packet.json, pairing each
                 restatement with what the writer meant (the item's evidence trail, a move's own lines, or the
                 cards a headline sums up).
collect          Checks every row in the verdicts files of each judge folder that count as runs (the files its
                 packet's agents write, or verdicts.jsonl when it lists none, plus verdicts-carried.jsonl and the
                 cold reader's verdicts-compare.jsonl; any other verdicts file is ignored with a warning), lists
                 malformed rows and unanswered items, and writes verify/judges.json: per rule, pass or fail, with the
                 failing items and their quotes. Unknown, missing and malformed all count as fail. Each verdicts file
                 is one run: within a run an item's worst row counts, across runs the majority decides (a tie fails),
                 and a carried verdict stands. A failing run the majority outvoted, and a fresh row on a carried
                 item, are listed as warnings.

A rule with more than 150 items (other than R06 and R10) is marked "exceptions" in the packet's modes: its judge
writes rows only for items that fail or are unknown, then one closing row {"rule", "item": "*", "verdict": "complete",
"read": N, "reason"}. An unlisted item passes only when that closing row exists and read equals the number of items the
packet lists for the rule (carried items are not listed); otherwise the rule has no result and gate.py holds.

Item ids are stable and count positions from 1: onepager.headline, onepager.f1 (the finding's own id),
top.gtm.headline, top.gtm.2, move.m3, move.m3.found.s1 (first sentence of the found line), swot.strengths.1.

Exit codes: 0 done; 1 when prepare-compare lacks restatements or collect finds malformed or missing rows
(rules may fail with exit 0: that is content, for gate.py); 2 on an unusable run folder.
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

JUDGES = ("source", "insight", "cold-reader", "sceptical-owner")
RULE_JUDGE = {"R19": "source", "R01": "insight", "R07": "insight", "R08": "insight", "R06": "cold-reader",
              "R10": "cold-reader", "R09": "sceptical-owner", "R14": "sceptical-owner", "R21": "sceptical-owner"}
VERDICTS = ("pass", "fail", "unknown")
ROLES = {"owner": "owner", "ceo": "CEO", "cmo": "CMO", "head-of-marketing": "head of marketing"}
LABELS = ("sounds right", "want to see more", "so what", "knew that", "don't get it", "sales pitch")
PASS_LABELS = ("sounds right", "want to see more")
STEPS = ("restate", "compare")
SUPPORT = ("supported", "stretched", "unsupported")
STRETCHES = ("case-to-pattern", "level-to-trend", "proxy-to-outcome", "more-exact", "wrong-row")
CALLS = ("knew it", "new to me")
FLAGS = ("a", "b", "c", "d", "e")
QUADS = ("strengths", "weaknesses", "opportunities", "threats")
BATCH = 8
EXCEPTIONS_OVER = 150  # above this many items a rule's judge writes only fail and unknown rows, plus one closing row
PER_ITEM_ALWAYS = ("R06", "R10")
# Judges whose single runs flipped on unchanged text (first client shadow run, November 2026): each runs this many times and
# the majority of runs decides an item. The R10 comparison step stays a single run.
REPEATS = {"cold-reader": 3, "sceptical-owner": 3}
RUN_LETTERS = "abcdefghij"
CARRIED_FILE = "verdicts-carried.jsonl"
COMPARE_FILE = "verdicts-compare.jsonl"
CLOSING_ITEM, CLOSING_VERDICT = "*", "complete"
DEFAULT_READER = "the owner of the business"
PROBE_TERMS = ["buy box", "importer of record", "IEEPA", "GEO", "llms.txt", "JSON-LD", "hreflang", "compare-at price",
               "ASIN", "CPC", "ROAS", "MAP", "sell-through", "doors"]
R14_PREFILTER = re.compile(r"(?i)\b(lawyer|counsel|attorney|legal review|broker|consultant)\b|written for|whoever runs"
                           r"|small team|tracked staff")
CITE_RE = re.compile(r"\[c:([^\]\s]+)\]")
TOKEN_RE = re.compile(r"\{\{\s*([a-zA-Z_]+)\s*:\s*([^}]*?)\s*\}\}")
REPORT_LINK = "{{report_link}}"
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
MOVE_TEXT = ("title", "stat", "found", "matters", "idea", "what", "why", "money", "trigger", "test", "watch",
             "if_wrong", "check_first", "further", "from", "to")
# Keys whose strings are ids, switches or chart data, never prose a reader judges.
SKIP_KEYS = {"id", "goto", "goto_label", "trail", "claims", "viz", "type", "priority", "impact", "effort", "moves",
             "on", "focus", "short", "series", "shade", "step", "channel", "depends", "when", "group", "default_from"}
WHERE = {"overview": "overview", "so_what": "overview", "moves": "sowhat", "gtm": "gtm", "ai": "ai",
         "compare": "competition"}


# ---------------------------------------------------------------- reading and text

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def read_jsonl(path, warn=None):
    rows = []
    if not path.exists():
        return rows
    for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            row = None
        if isinstance(row, dict):
            rows.append(row)
        elif warn is not None:
            warn.append(f"{path.name} line {n}: not a JSON object, skipped")
    return rows


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve(value, stats):
    """Fill {{stat:id}} and {{kpi:label}} from bundle.stats; {{report_link}} reads as the page does before delivery."""
    text = "" if value is None else str(value)
    text = text.replace(REPORT_LINK, "the full report")

    def sub(m):
        kind, name = m.group(1), m.group(2)
        entry = stats.get(f"kpi:{name}" if kind == "kpi" else name) or {}
        shown = entry.get("text") if entry.get("text") not in (None, "") else entry.get("value")
        return m.group(0) if shown is None or entry.get("missing") else str(shown)
    return TOKEN_RE.sub(sub, text).strip()


def no_cites(text):
    text = re.sub(r"\s*\[c:[^\]\s]+\]", "", text or "")
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def plain(text):
    """What a cold reader sees: no citations, no URLs, no markdown links or emphasis."""
    text = no_cites(text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    text = text.replace("**", "").replace("__", "")
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def sentences(text):
    return [s.strip() for s in SENTENCE_END.split(text or "") if s.strip()]


def cites(text):
    return list(dict.fromkeys(CITE_RE.findall(text or "")))


def dotted(keys):
    out = ""
    for k in keys:
        out += f"[{k}]" if isinstance(k, int) else (f".{k}" if out else str(k))
    return out


def leaves(node, keys=()):
    if isinstance(node, str):
        yield keys, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from leaves(v, keys + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from leaves(v, keys + (i,))


def cited_ids(item):
    """Claim ids a finding or card rests on: its claims list, then any cited in its text (as build_dashboard.py)."""
    out = list(item.get("claims") or [])
    for key in ("so", "value", "label", "means", "reasoning"):
        out += CITE_RE.findall(str(item.get(key) or ""))
    return list(dict.fromkeys(out))


# ---------------------------------------------------------------- the judged parts of a bundle

class Report:
    """Items in the bundle with stable ids. Text keeps [c:id] markers; each packet strips what its judge may not see."""

    def __init__(self, bundle, config):
        self.bundle = bundle
        self.config = config or {}
        self.prose = bundle.get("prose") or {}
        self.stats = bundle.get("stats") or {}
        self.trails = bundle.get("trails") or {}
        self.onepager = self.prose.get("onepager") or None
        self.name = self.config.get("name") or (bundle.get("meta") or {}).get("name") or "the company"

    def r(self, value):
        return resolve(value, self.stats)

    def tops(self):
        """Every tab top except the Overview's when the one-pager supplies it (client mode builds one from the other)."""
        for tab, top in (self.prose.get("top") or {}).items():
            if tab == "overview" and self.onepager:
                continue
            yield tab, top or {}

    def headlines(self):
        out = []
        if self.onepager:
            out.append({"item": "onepager.headline", "where": "one-pager", "scope": "report",
                        "text": self.r(self.onepager.get("headline"))})
        for tab, top in self.tops():
            if top.get("headline"):
                out.append({"item": f"top.{tab}.headline", "where": tab, "scope": "report" if tab == "overview" else tab,
                            "text": self.r(top["headline"])})
        return out

    def finding_ids(self):
        return [str(f.get("id") or f"f{i}") for i, f in enumerate((self.onepager or {}).get("findings") or [], 1)]

    def findings(self):
        """One-pager findings, then every other tab top's cards."""
        out = []
        for fid, f in zip(self.finding_ids(), (self.onepager or {}).get("findings") or []):
            out.append(self._point(f"onepager.{fid}", "one-pager", f, fid))
        for tab, top in self.tops():
            for i, p in enumerate(top.get("points") or [], 1):
                out.append(self._point(f"top.{tab}.{i}", tab, p, p.get("trail") or f"{tab}.{i - 1}"))
        return out

    def _point(self, item, where, p, trail):
        d = {"item": item, "where": where, "trail": trail, "kind": p.get("kind"), "claims": cited_ids(p)}
        for key in ("so", "value", "label", "means", "reasoning", "date"):
            d[key] = self.r(p.get(key))
        return d

    def move_ids(self):
        return [str(m.get("id") or f"m{i}") for i, m in enumerate((self.prose.get("moves") or {}).get("items") or [], 1)]

    def moves(self):
        out = []
        for mid, m in zip(self.move_ids(), (self.prose.get("moves") or {}).get("items") or []):
            d = {"item": f"move.{mid}", "id": mid, "where": "sowhat"}
            for key in MOVE_TEXT:
                if m.get(key) not in (None, ""):
                    d[key] = self.r(m[key])
            out.append(d)
        return out

    def part_ids(self):
        return [str(p.get("id") or j) for j, p in enumerate((self.prose.get("ai") or {}).get("parts") or [], 1)]

    def swot(self):
        out = []

        def add(prefix, where, quads):
            for quad in QUADS:
                for i, s in enumerate((quads or {}).get(quad) or [], 1):
                    if isinstance(s, dict):
                        text = self.r(s.get("point"))
                        if s.get("so_what"):
                            text += f" So what: {self.r(s['so_what'])}"
                    else:
                        text = self.r(s)
                    out.append({"item": f"{prefix}.{quad}.{i}", "where": where, "text": text})
        add("swot", "overview", (self.prose.get("moves") or {}).get("swot"))
        for pid, part in zip(self.part_ids(), (self.prose.get("ai") or {}).get("parts") or []):
            add(f"ai.{pid}.swot", "ai", part.get("swot"))
        return out

    def rivals(self):
        own = (self.config.get("competition") or {}).get("self")
        order = {"high": 0, "medium": 1, "low": 2}
        rows = [c for c in self.bundle.get("competitors") or [] if c.get("id") != own and c.get("name") != self.name]
        rows.sort(key=lambda c: order.get(c.get("threat_level"), 3))
        return [{k: c.get(k) for k in ("name", "short_name", "group", "positioning_line", "threat_level")} for c in rows]

    def blocks(self):
        """All of the page's own prose, grouped into blocks a reader takes in one go (a card, a move, a SWOT point)."""
        fids, mids, pids = self.finding_ids(), self.move_ids(), self.part_ids()
        blocks = {}
        for keys, value in leaves(self.prose):
            if any(isinstance(k, str) and k in SKIP_KEYS for k in keys[1:]) or not value.strip():
                continue
            placed = self._block_of(keys, fids, mids, pids)
            if placed is None:
                continue
            item, where, field = placed
            block = blocks.setdefault(item, {"item": item, "where": where, "fields": {}})
            name, n = field, 2
            while name in block["fields"]:
                name, n = f"{field}#{n}", n + 1
            block["fields"][name] = self.r(value)
        return list(blocks.values())

    def _block_of(self, keys, fids, mids, pids):
        k0 = keys[0]
        if k0 == "onepager":
            if len(keys) >= 4 and keys[1] == "findings" and isinstance(keys[2], int) and keys[2] < len(fids):
                return f"onepager.{fids[keys[2]]}", "one-pager", dotted(keys[3:])
            return f"onepager.{dotted(keys[1:])}", "one-pager", "text"
        if k0 == "top" and len(keys) >= 3:
            tab = keys[1]
            if tab == "overview" and self.onepager:
                return None
            if keys[2] == "points" and len(keys) >= 5 and isinstance(keys[3], int):
                return f"top.{tab}.{keys[3] + 1}", tab, dotted(keys[4:])
            if keys[2] == "headline":
                return f"top.{tab}.headline", tab, "text"
        if keys[:2] == ("moves", "items") and len(keys) >= 4 and isinstance(keys[2], int) and keys[2] < len(mids):
            return f"move.{mids[keys[2]]}", "sowhat", dotted(keys[3:])
        if keys[:2] == ("moves", "swot") and len(keys) >= 4 and isinstance(keys[3], int):
            return f"swot.{keys[2]}.{keys[3] + 1}", "overview", dotted(keys[4:]) or "text"
        if (keys[:2] == ("ai", "parts") and len(keys) >= 6 and isinstance(keys[2], int) and keys[2] < len(pids)
                and keys[3] == "swot" and isinstance(keys[5], int)):
            return f"ai.{pids[keys[2]]}.swot.{keys[4]}.{keys[5] + 1}", "ai", dotted(keys[6:]) or "text"
        last = max((i for i, x in enumerate(keys) if isinstance(x, int)), default=None)
        base = keys[:last + 1] if last is not None else (keys[:-1] or keys)
        where = (keys[1] if len(keys) > 1 else "bands") if k0 == "bands" else WHERE.get(k0, k0)
        if k0 == "top":
            where = keys[1] if len(keys) > 1 else "top"
        return "prose." + dotted(base), str(where), dotted(keys[len(base):]) or "text"

    def library_hits(self):
        """Deep dive sentences the R14 word filter catches. The Deep dive itself is too long to hand a judge whole."""
        out = []
        for row in self.bundle.get("library") or []:
            for n, s in enumerate(sentences(str(row.get("md") or "")), 1):
                if R14_PREFILTER.search(s):
                    out.append({"item": f"deepdive.{row.get('doc')}.{row.get('idx')}.s{n}", "where": "deepdive",
                                "fields": {"sentence": s}})
        return out

    def page(self):
        """The one-pager as build_dashboard.py onepager prints it, with source links left out."""
        op = self.onepager or {}
        meta = self.bundle.get("meta") or {}
        brand = (self.bundle.get("config") or self.config).get("brand") or {}
        header = " | ".join(str(x) for x in (brand.get("name"), meta.get("name"), meta.get("cutoff")) if x)
        findings = [{"item": p["item"], "value": plain(p["value"]), "title": plain(p["so"]), "label": plain(p["label"]),
                     "means": plain(p["means"]), "link": "How we got here"}
                    for p in self.findings() if p["where"] == "one-pager"]
        return {"header": header, "headline": plain(self.r(op.get("headline"))), "findings": findings,
                "basis": plain(self.r(op.get("basis"))), "way_in": plain(self.r(op.get("way_in"))),
                "footer": plain(str(brand.get("footer") or ""))}

    def r10_items(self):
        """Every headline, card and move title, interleaved across tabs so one batch never holds one tab's story."""
        groups = {}
        for h in self.headlines():
            groups.setdefault(h["where"], []).append(
                {"item": h["item"], "kind": "headline", "scope": h["scope"], "fields": {"headline": plain(h["text"])}})
        for p in self.findings():
            groups.setdefault(p["where"], []).append(
                {"item": p["item"], "kind": "card", "trail": p["trail"],
                 "fields": {"title": plain(p["so"]), "value": plain(p["value"]), "label": plain(p["label"]),
                            "means": plain(p["means"])}})
        for m in self.moves():
            groups.setdefault("moves", []).append(
                {"item": f"{m['item']}.title", "kind": "move title", "move": m["id"],
                 "fields": {"title": plain(m.get("title", ""))}})
        queues, out = [list(g) for g in groups.values()], []
        while any(queues):
            for q in queues:
                if q:
                    out.append(q.pop(0))
        return out


# ---------------------------------------------------------------- packets, one builder per judge

def mode_for(rule, n):
    """'exceptions' when a rule has more items than a judge can answer one by one; R06 and R10 always answer each
    item, since R06 rows are per role and R10 restatements feed the comparison."""
    return "exceptions" if n > EXCEPTIONS_OVER and rule not in PER_ITEM_ALWAYS else "every"


def expected_keys(rule, items):
    if rule == "R06":
        return [{"item": it["item"], "role": role} for it in items for role in ROLES]
    if rule == "R10":
        return [{"item": it["item"], "step": step} for it in items for step in STEPS]
    return [{"item": it["item"]} for it in items]


def build_source(rep, ctx, rules):
    items = []

    def add(item, text, ids):
        ids = list(dict.fromkeys(ids))
        if text and ids:
            items.append({"item": item, "text": text, "cited": ids})

    def by_sentence(prefix, field, raw):
        for n, s in enumerate(sentences(raw), 1):
            if cites(s):
                add(f"{prefix}.{field}.s{n}", s, cites(s))

    for p in rep.findings():
        card = f"{p['value']} {p['label']}".strip()
        add(f"{p['item']}.card", card, cites(card) + p["claims"])
        add(f"{p['item']}.so", p["so"], cites(p["so"]) or p["claims"])
        by_sentence(p["item"], "means", p["means"])
    for m in rep.moves():
        add(f"{m['item']}.title", m.get("title", ""), cites(m.get("title", "")) or cites(m.get("stat", "")))
        for field in MOVE_TEXT[1:]:
            by_sentence(m["item"], field, m.get(field, ""))
    rows, evidence = {}, {}
    for cid in dict.fromkeys(c for it in items for c in it["cited"]):
        row = ctx["ledger"].get(cid)
        rows[cid] = ({k: row.get(k) for k in ("text", "value", "source", "source_kind", "basis")}
                     if row else {"missing": True})
        evidence[cid] = [{k: v.get(k) for k in ("status", "evidence_quote", "checked_url", "verifier", "note")
                          if k != "note" or v.get("note")}
                         for v in ctx["verdicts"].get(cid, [])]
    return {"items": {"R19": items} if "R19" in rules else {}, "rows": rows, "evidence": evidence}


def build_insight(rep, ctx, rules):
    findings = [{"item": p["item"], "where": p["where"], "so": plain(p["so"]), "value": plain(p["value"]),
                 "label": plain(p["label"]), "means": plain(p["means"])} for p in rep.findings()]
    items = {}
    if "R01" in rules:
        items["R01"] = [{"item": h["item"], "scope": h["scope"], "text": plain(h["text"])} for h in rep.headlines()]
    if "R07" in rules:
        items["R07"] = [{"item": f["item"], "where": f["where"],
                         "text": f"{f['so']}: {f['value']} {f['label']}".strip(" :")} for f in findings]
        items["R07"] += [{"item": s["item"], "where": s["where"], "text": plain(s["text"])} for s in rep.swot()]
    if "R08" in rules:
        items["R08"] = [{"item": f"{f['item']}.means", "number": f"{f['value']} {f['label']}".strip(),
                         "text": f["means"]} for f in findings]
        items["R08"] += [{"item": f"{m['item']}.matters", "number": plain(m.get("stat", "")),
                          "found": plain(m.get("found", "")), "text": plain(m.get("matters", ""))} for m in rep.moves()]
    rivals = rep.rivals()
    return {"company": rep.name, "rivals": rivals, "closest_rival": rivals[0]["name"] if rivals else None,
            "findings": findings, "items": items}


def run_names(base, repeats):
    """Agent names for the runs of one agent: the base name alone for a single run, else base-a, base-b, ..."""
    return [base] if repeats <= 1 else [f"{base}-{RUN_LETTERS[k]}" for k in range(repeats)]


def cold_agents(page, items, repeats):
    """(agents, files) for the cold-reader items left to judge: each role reader and each restater batch runs
    `repeats` times, every run with its own input and verdicts file."""
    agents, files = [], {}
    folder = "verify/judges/cold-reader"
    if items.get("R06"):
        for role, role_name in ROLES.items():
            for name in run_names(f"r06-{role}", repeats):
                files[f"agent-{name}.json"] = {"agent": name, "rule": "R06", "role": role, "role_name": role_name,
                                               "page": page}
                agents.append({"agent": name, "rule": "R06", "role": role, "role_name": role_name,
                               "input": f"{folder}/agent-{name}.json", "writes": f"{folder}/verdicts-{name}.jsonl"})
    r10 = items.get("R10") or []
    for b in range(0, len(r10), BATCH):
        batch = [{"item": it["item"], "kind": it["kind"], "fields": it["fields"]} for it in r10[b:b + BATCH]]
        for name in run_names(f"r10-{b // BATCH + 1}", repeats):
            files[f"agent-{name}.json"] = {"agent": name, "rule": "R10", "step": "restate",
                                           "probe_terms": PROBE_TERMS, "items": batch}
            agents.append({"agent": name, "rule": "R10", "step": "restate", "input": f"{folder}/agent-{name}.json",
                           "writes": f"{folder}/verdicts-{name}.jsonl"})
    return agents, files


def build_cold_reader(rep, ctx, rules):
    items = {}
    page = rep.page()
    if "R06" in rules:
        items["R06"] = [{"item": f["item"], "text": " ".join(f[k] for k in ("value", "title", "label", "means"))}
                        for f in page["findings"]]
    if "R10" in rules:
        items["R10"] = rep.r10_items()
    agents, files = cold_agents(page, items, 1)
    packet = {"items": items, "agents": agents,
              "compare": "after every r10 agent finishes, run judges.py prepare-compare and one comparison agent"}
    return packet, files


def build_owner(rep, ctx, rules):
    blocks = rep.blocks()
    persona = str(rep.config.get("reader") or DEFAULT_READER)
    items = {}
    if "R09" in rules:
        items["R09"] = [{"item": p["item"], "where": p["where"],
                         "text": f"{p['so']}: {p['value']} {p['label']} What it means: {p['means']}".strip()}
                        for p in rep.findings()]
    if "R14" in rules:
        items["R14"] = blocks + rep.library_hits()
    if "R21" in rules:
        items["R21"] = [{"item": "report", "text": "",
                         "note": "one row for the whole report: the text is in blocks when the packet has them, else in "
                                 "items.R14; the basis of each cited number is in claims"}]
    hits = [{"item": b["item"], "sentence": s} for b in blocks for v in b["fields"].values() for s in sentences(v)
            if R14_PREFILTER.search(s)]
    claims = {}
    for b in blocks:
        for v in b["fields"].values():
            for cid in cites(v):
                row = ctx["ledger"].get(cid) or {}
                latest = (ctx["verdicts"].get(cid) or [{}])[-1]
                claims[cid] = {"basis": row.get("basis"), "confidence": row.get("confidence"),
                               "source_kind": row.get("source_kind"), "value": row.get("value"),
                               "status": latest.get("status") or "unchecked", "in_ledger": bool(row)}
    packet = {"persona": persona, "company": rep.name, "items": items, "claims": claims, "prefilter_hits": hits}
    if "R14" not in rules:
        packet["blocks"] = blocks

    return packet


BUILDERS = {"source": build_source, "insight": build_insight, "cold-reader": build_cold_reader,
            "sceptical-owner": build_owner}


# ---------------------------------------------------------------- run context

def judge_rules(rubric):
    """{judge: [(rule id, level)]} for every rubric rule checked by a judge."""
    out = {}
    for r in rubric if isinstance(rubric, list) else []:
        check = str((r or {}).get("check") or "")
        if check.startswith("judge:") and r.get("id"):
            out.setdefault(check.split(":", 1)[1], []).append((str(r["id"]), r.get("level") or "must"))
    return out


def load_run(run, need_rubric=True):
    """Bundle, rubric and config, or a message saying why the run is unusable."""
    if not run.is_dir():
        return None, f"not a folder: {run}"
    bundle_file = run / "dashboard" / "bundle.json"
    bundle = read_json(bundle_file)
    if not isinstance(bundle, dict):
        return None, f"{bundle_file} is missing or unreadable: run build_dashboard.py assemble first"
    rubric = read_json(run / "rubric.json")
    if need_rubric and not isinstance(rubric, list):
        return None, f"{run / 'rubric.json'} is missing or not a list: copy the rubric into the run root at intake"
    config = read_json(run / "config.json")
    if not isinstance(config, dict):
        config = bundle.get("config") or {}
    return {"bundle": bundle, "bundle_sha": sha256(bundle_file), "rubric": rubric, "config": config}, None


def ledger_context(run, warnings):
    ledger_file, verdict_file = run / "verify" / "ledger.jsonl", run / "verify" / "verdicts.jsonl"
    for f in (ledger_file, verdict_file):
        if not f.exists():
            warnings.append(f"{f.relative_to(run).as_posix()} is missing, so the source judge will see cited rows as missing")
    ledger = {}
    for row in read_jsonl(ledger_file, warnings):
        ledger.setdefault(row.get("id"), row)
        for alias in row.get("merged_ids") or []:
            ledger.setdefault(alias, row)
    verdicts = {}
    for row in read_jsonl(verdict_file, warnings):
        verdicts.setdefault(row.get("id"), []).append(row)
    # A correction comes after the check it answers, so it is the row's latest state: "corrected" (the row text was
    # fixed to match the source), "downgraded" (kept at a weaker basis) or "removed".
    corrections_file = run / "verify" / "corrections.jsonl"
    if corrections_file.exists():
        for c in read_jsonl(corrections_file, warnings):
            verdicts.setdefault(c.get("id"), []).append(
                {"id": c.get("id"), "status": c.get("action"), "evidence_quote": "", "checked_url": None,
                 "verifier": "correction", "note": c.get("note")})
    return ledger, verdicts


def archive(folder):
    """Move every file left from an earlier round into archive-<n>/, so old verdicts never count again."""
    if not folder.is_dir():
        return None
    old = [p for p in folder.iterdir() if p.is_file()]
    if not old:
        return None
    n = 1
    while (folder / f"archive-{n}").exists():
        n += 1
    dest = folder / f"archive-{n}"
    dest.mkdir()
    for p in old:
        p.replace(dest / p.name)
    return dest


# ---------------------------------------------------------------- rounds: fingerprints, runs and carried verdicts

def fingerprint(*parts):
    return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:16]


def item_fingerprints(judge, body, rep):
    """{rule: {item: fingerprint}} over everything the judge sees for each item, so an unchanged fingerprint means
    an unchanged judgement. A rule judged against its context takes the context too: R06 the printed one-pager, R01
    every finding, R07 the rivals, R10 what the writer meant, R19 the cited rows and evidence, R21 every block and claim."""
    items = body.get("items") or {}
    findings = [{k: f.get(k) for k in ("item", "so", "value", "label", "means")} for f in body.get("findings") or []]
    page = rep.page() if judge == "cold-reader" else None
    fmap = {p["item"]: p for p in rep.findings()} if judge == "cold-reader" else {}
    mmap = {m["id"]: m for m in rep.moves()} if judge == "cold-reader" else {}
    out = {}
    for rid, entries in items.items():
        fps = {}
        for e in entries:
            if rid == "R19":
                ctx = {c: [(body.get("rows") or {}).get(c), (body.get("evidence") or {}).get(c)] for c in e.get("cited") or []}
            elif rid == "R01":
                ctx = findings
            elif rid == "R07":
                ctx = [body.get("closest_rival"), body.get("rivals")]
            elif rid == "R06":
                ctx = page
            elif rid == "R10":
                ctx = meant(e, rep, fmap, mmap)
            elif rid == "R21":
                ctx = [items.get("R14"), body.get("blocks"), body.get("claims")]
            else:
                ctx = None
            fps[e["item"]] = fingerprint(e, ctx)
        out[rid] = fps
    return out


def runs_needed(rid, key, repeats):
    """Runs an item needs before it counts as answered: one for the R10 comparison step, else every repeat."""
    return 1 if rid == "R10" and key[1] == "compare" else max(1, int(repeats or 1))


def run_files(folder, judge, packet):
    """(files that count as runs, other verdicts files). Runs are the files the packet's agents write (verdicts.jsonl
    when it lists none), plus the carried rows and, for the cold reader, the comparison. Any other verdicts file, such
    as a retry an agent saved on the side, is no run of this round."""
    names = {Path(str(a.get("writes") or "")).name for a in (packet or {}).get("agents") or []} or {"verdicts.jsonl"}
    names |= {CARRIED_FILE} | ({COMPARE_FILE} if judge == "cold-reader" else set())
    found = sorted(folder.glob("verdicts*.jsonl")) if folder and folder.is_dir() else []
    return [p for p in found if p.name in names], [p for p in found if p.name not in names]


def run_rows(files, judge, rule_ids, expected, modes):
    """Every valid row per rule and key, tagged with its run (the verdicts file it came from), closing rows per rule
    and run, the malformed lines, and the valid rows in file order for per-row checks."""
    answers = {rid: {} for rid in rule_ids}
    closings = {rid: {} for rid in rule_ids}
    malformed, ordered = [], []
    for path in files:
        for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError as e:
                malformed.append((path, n, f"bad JSON: {e}", line))
                continue
            placed, probs = check_row(row, judge, rule_ids, expected, modes)
            if probs:
                malformed.append((path, n, "; ".join(probs), line))
                continue
            rid, key = placed
            if key[0] == CLOSING_ITEM:
                closings[rid][path.name] = row  # a run's last closing row counts
                continue
            row = dict(row, _run=path.name)
            answers[rid].setdefault(key, []).append(row)
            ordered.append((path, n, rid, key, row))
    return answers, closings, malformed, ordered


def decide(rows, need, pass_runs=()):
    """(verdict, rows behind it, runs counted, minority) for one item. A carried row stands. Otherwise each run counts
    once, by its worst row; a run in pass_runs with no row for the item passed it under its closing row. The item fails
    when at least half its runs fail. Fewer runs than `need` gives verdict None: unanswered. `minority` holds the
    failing runs' rows of an item the majority passed."""
    carried = [r for r in rows if r.get("carried")]
    if carried:
        return carried[-1]["verdict"], carried[-1:], 1, []
    worst = {}
    for r in rows:
        if r["_run"] not in worst or (worst[r["_run"]]["verdict"] == "pass" and r["verdict"] != "pass"):
            worst[r["_run"]] = r
    runs = len(worst) + len([p for p in pass_runs if p not in worst])
    if runs < need:
        return None, [], runs, []
    fails = [r for r in worst.values() if r["verdict"] != "pass"]
    if fails and 2 * len(fails) >= runs:
        return ("unknown" if all(r["verdict"] == "unknown" for r in fails) else "fail"), fails, runs, []
    return "pass", [r for r in worst.values() if r["verdict"] == "pass"][:1], runs, fails


def listed(packet, rid):
    """How many items the packet lists for a rule to judge: the count a closing row's read must equal."""
    return len(((packet or {}).get("items") or {}).get(rid) or [])


def pass_runs_for(mode, closings, to_judge):
    """Runs whose closing row read every item listed to judge, so their unlisted items passed (exceptions mode only)."""
    if mode != "exceptions":
        return []
    return [run for run, c in closings.items() if c.get("read") == to_judge]


def previous_round(dest, judge, rule_ids):
    """(fingerprints, decided) from an archived round: decided holds, per rule and item, the (key, verdict, row) of
    every key when all of the item's keys were decided pass or fail, every run agreeing, with a row behind them. An
    item an exceptions-mode rule passed under its closing rows gets a pass row made here. Empty when the archive has no
    packet with fingerprints."""
    packet = read_json(dest / "packet.json") if dest else None
    if not isinstance(packet, dict) or not packet.get("fingerprints"):
        return {}, {}
    expected = {rid: {(k["item"], k.get("role") or k.get("step") or ""): None for k in keys}
                for rid, keys in (packet.get("expected") or {}).items() if rid in rule_ids}
    modes, repeats = packet.get("modes") or {}, packet.get("repeats") or 1
    answers, closings, _, _ = run_rows(run_files(dest, judge, packet)[0], judge, set(expected), expected, modes)
    decided = {}
    for rid, keys in expected.items():
        passed = pass_runs_for(modes.get(rid, "every"), closings[rid], listed(packet, rid))
        by_item = {}
        for key in keys:
            verdict, rows, runs, minority = decide(answers[rid].get(key, []), runs_needed(rid, key, repeats), passed)
            if minority or (verdict != "pass" and len(rows) < runs):
                verdict = None  # the runs split, so the item is judged again
            row = rows[0] if rows else None
            if verdict == "pass" and row is None and passed:
                row = {"rule": rid, "item": key[0], "verdict": "pass", "closing": True,
                       "reason": "No fail row, so it passed under the closing row of every run."}
            by_item.setdefault(key[0], []).append((key, verdict, row))
        for item, entries in by_item.items():
            if all(v in ("pass", "fail") and row for _, v, row in entries):
                decided.setdefault(rid, {})[item] = entries
    return packet["fingerprints"], decided


def carry_forward(body, rid_list, fps, prev_fps, decided, source_name):
    """Take every item whose fingerprint matches the round before, and whose keys that round all decided, out of
    body["items"]. Returns the carried rows (marked carried, with where they came from) and the keys carried per rule."""
    items = body.get("items") or {}
    rows, counts = [], {}
    for rid in rid_list:
        keep = []
        for e in items.get(rid) or []:
            prev = (decided.get(rid) or {}).get(e["item"])
            if prev and (prev_fps.get(rid) or {}).get(e["item"]) == (fps.get(rid) or {}).get(e["item"]):
                for _, _, row in prev:
                    rows.append({**{k: v for k, v in row.items() if k != "_run"}, "carried": True,
                                 "carried_from": row.get("carried_from") or source_name})
                counts[rid] = counts.get(rid, 0) + len(prev)
            else:
                keep.append(e)
        if rid in items:
            items[rid] = keep
    return rows, counts


def prepare(run):
    ctx, err = load_run(run)
    if err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2
    rep = Report(ctx["bundle"], ctx["config"])
    if not rep.onepager:
        print("ERROR: the bundle has no prose.onepager; judges run in client mode only", file=sys.stderr)
        return 2
    warnings = []
    ctx["ledger"], ctx["verdicts"] = ledger_context(run, warnings)
    by_judge = judge_rules(ctx["rubric"])
    for judge, rules in by_judge.items():
        for rid, _ in rules:
            if RULE_JUDGE.get(rid) != judge:
                warnings.append(f"{rid} (judge:{judge}): judges.py has no items for this rule under this judge, "
                                f"so collect will fail it until a builder exists")
        if judge not in BUILDERS:
            warnings.append(f"judge:{judge} has no brief in references/judges.md and no packet")
    for judge in JUDGES:
        rules = [(rid, lvl) for rid, lvl in by_judge.get(judge, []) if RULE_JUDGE.get(rid) == judge]
        if not rules:
            continue
        folder = run / "verify" / "judges" / judge
        moved = archive(folder)
        if moved:
            print(f"Archived the earlier {judge} files to {moved.relative_to(run).as_posix()}/")
        ids = [rid for rid, _ in rules]
        built = BUILDERS[judge](rep, ctx, ids)
        body, files = built if isinstance(built, tuple) else (built, {})
        repeats = REPEATS.get(judge, 1)
        expected = {rid: expected_keys(rid, (body.get("items") or {}).get(rid) or []) for rid in ids}
        fps = item_fingerprints(judge, body, rep)
        all_blocks = list((body.get("items") or {}).get("R14") or [])
        prev_fps, decided = previous_round(moved, judge, set(ids))
        carried_rows, carried = carry_forward(body, ids, fps, prev_fps, decided, moved.name if moved else "")
        if judge == "source":  # rows and evidence only for the sentences left to judge
            keep = {c for e in body["items"].get("R19") or [] for c in e.get("cited") or []}
            body["rows"] = {c: v for c, v in body["rows"].items() if c in keep}
            body["evidence"] = {c: v for c, v in body["evidence"].items() if c in keep}
        if judge == "sceptical-owner" and carried.get("R14") and body["items"].get("R21"):
            body["blocks"] = all_blocks  # R21 weighs the whole report, so its judge reads every block
        left = {rid: len(expected[rid]) - carried.get(rid, 0) for rid in ids}
        if judge == "cold-reader":
            body["agents"], files = cold_agents(rep.page(), body.get("items") or {}, repeats)
        elif repeats > 1 and any(left.values()):
            body["agents"] = [{"agent": name, "writes": f"verify/judges/{judge}/verdicts-{name}.jsonl"}
                              for name in run_names(judge, repeats)]
        packet = {"judge": judge, "built": now(), "bundle_sha": ctx["bundle_sha"],
                  "brief": f"references/judges.md, {judge}", "rules": [{"id": rid, "level": lvl} for rid, lvl in rules],
                  "verdicts": f"verify/judges/{judge}/verdicts.jsonl" if repeats == 1 else
                              f"one verdicts file per run, as listed under agents"}
        packet.update(body)
        packet["expected"] = expected
        packet["modes"] = {rid: mode_for(rid, left[rid]) for rid in ids}
        packet["exceptions_over"] = EXCEPTIONS_OVER
        packet.update(repeats=repeats, fingerprints=fps, carried=carried)
        write_json(folder / "packet.json", packet)
        for name, data in files.items():
            write_json(folder / name, data)
        if carried_rows:
            (folder / CARRIED_FILE).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in carried_rows),
                                               encoding="utf-8", newline="\n")
        counts = ", ".join(
            (f"{rid} {left[rid]} rows" if packet["modes"][rid] == "every" else
             f"{rid} {left[rid]} items, rows only for fail or unknown plus 1 closing row")
            + (f" ({carried[rid]} carried from {moved.name})" if carried.get(rid) else "") for rid in ids)
        runs = f"; {repeats} runs" if repeats > 1 else ""
        extra = f"; {len(packet.get('agents') or [])} agents to launch" if packet.get("agents") else ""
        print(f"Wrote verify/judges/{judge}/packet.json: {counts}{runs}{extra}")
    for w in warnings:
        print(f"WARNING: {w}")
    return 0


def prepare_compare(run):
    ctx, err = load_run(run, need_rubric=False)
    if err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2
    folder = run / "verify" / "judges" / "cold-reader"
    packet = read_json(folder / "packet.json")
    if not isinstance(packet, dict) or "R10" not in (packet.get("items") or {}):
        print("ERROR: no cold-reader packet with R10 items: run judges.py prepare first", file=sys.stderr)
        return 2
    if packet.get("bundle_sha") != ctx["bundle_sha"]:
        print("ERROR: the bundle changed after prepare: run judges.py prepare again and re-run the restaters",
              file=sys.stderr)
        return 2
    rep = Report(ctx["bundle"], ctx["config"])
    restated = {}
    for path in run_files(folder, "cold-reader", packet)[0]:
        for row in read_jsonl(path):
            if (row.get("rule") == "R10" and row.get("step") == "restate"
                    and isinstance(row.get("restatement"), str) and row["restatement"].strip()):
                restated.setdefault(row.get("item"), row)  # with several runs, the first run's restatement is compared
    findings = {p["item"]: p for p in rep.findings()}
    moves = {m["id"]: m for m in rep.moves()}
    items, missing = [], []
    for it in packet["items"]["R10"]:
        row = restated.get(it["item"])
        if row is None:
            missing.append(it["item"])
            continue
        items.append({"item": it["item"], "kind": it["kind"], "original": it["fields"],
                      "restatement": row["restatement"], "unclear_terms": row.get("unclear_terms") or [],
                      "meant": meant(it, rep, findings, moves)})
    out = {"rule": "R10", "step": "compare", "built": now(), "bundle_sha": ctx["bundle_sha"], "items": items,
           "missing_restatement": missing, "writes": "verify/judges/cold-reader/verdicts-compare.jsonl"}
    write_json(folder / "compare-packet.json", out)
    print(f"Wrote verify/judges/cold-reader/compare-packet.json: {len(items)} items to compare")
    if missing:
        print(f"MISSING: {len(missing)} items have no restatement yet: {', '.join(missing[:10])}")
        return 1
    return 0


def meant(it, rep, findings, moves):
    """What the writer meant: the evidence trail's reasoning, a move's own lines, or the cards a headline sums up."""
    if it["kind"] == "card":
        trail = rep.trails.get(str(it.get("trail")))
        if trail:
            return {"from": "evidence trail", "title": plain(rep.r(trail.get("title"))),
                    "value": plain(rep.r(trail.get("value"))), "reasoning": plain(rep.r(trail.get("reasoning")))}
        p = findings.get(it["item"]) or {}
        return {"from": "card, no trail found", "reasoning": plain(p.get("reasoning", "")), "means": plain(p.get("means", ""))}
    if it["kind"] == "move title":
        m = moves.get(it.get("move")) or {}
        return {"from": "move", "found": plain(m.get("found", "")), "matters": plain(m.get("matters", "")),
                "idea": plain(m.get("idea", ""))}
    scope = it.get("scope")
    cards = [p for p in findings.values()
             if (p["where"] == "one-pager" if scope == "report" and rep.onepager else p["where"] == scope)]
    return {"from": "the cards under this headline",
            "cards": [f"{plain(p['so'])}: {plain(p['means'])}".strip(" :") for p in cards]}


# ---------------------------------------------------------------- collect

def norm(value):
    return str(value or "").strip().lower().replace("’", "'")


def item_text(entry):
    if not isinstance(entry, dict):
        return ""
    parts = [str(entry.get("text") or "")]
    for key in ("fields", "original", "meant"):
        for v in leaves(entry.get(key) or {}):
            parts.append(v[1])
    if entry.get("restatement"):
        parts.append(str(entry["restatement"]))
    return " ".join(p for p in parts if p)


def quote_found(quote, text):
    def flat(s):
        s = plain(s).replace("’", "'").replace("“", '"').replace("”", '"')
        return re.sub(r"\s+", " ", s).strip().lower()
    hay = flat(text)
    parts = [p.strip(" .,;:\"'") for p in re.split(r"\.\.\.|…", flat(quote))]
    return all(p in hay for p in parts if p)


def check_closing(row, rule, modes):
    """The one closing row an exceptions-mode rule ends with: {rule, item: "*", verdict: "complete", read, reason}."""
    probs = []
    if modes.get(rule) != "exceptions":
        return None, [f"{rule} wants a row per item, so it takes no closing row"]
    if row.get("item") != CLOSING_ITEM or row.get("verdict") != CLOSING_VERDICT:
        probs.append(f"a closing row has item {CLOSING_ITEM!r} and verdict {CLOSING_VERDICT!r}")
    read = row.get("read")
    if not isinstance(read, int) or isinstance(read, bool) or read < 0:
        probs.append("read must be the number of items read")
    if not isinstance(row.get("reason"), str) or not row["reason"].strip():
        probs.append("reason is required")
    return (None, probs) if probs else ((rule, (CLOSING_ITEM, "")), [])


def check_row(row, judge, rules, expected, modes=None):
    """(rule, key) of a valid row, or None with the problems found."""
    if not isinstance(row, dict):
        return None, ["not a JSON object"]
    rule = row.get("rule")
    if rule not in rules:
        owner = RULE_JUDGE.get(str(rule))
        where = f" (judged by {owner})" if owner and owner != judge else ""
        return None, [f"rule {rule!r} is not judged here{where}"]
    if row.get("item") == CLOSING_ITEM or row.get("verdict") == CLOSING_VERDICT:
        return check_closing(row, rule, modes or {})
    if row.get("carried") and row.get("closing") is True:  # a pass carried from a closing row has no quote or fields
        key = (str(row.get("item")), "")
        probs = [] if row.get("verdict") == "pass" else ["a pass carried from a closing row has verdict pass"]
        if key not in expected.get(rule, {}):
            probs.append(f"item {row.get('item')!r} is not in the packet for {rule}")
        return (None, probs) if probs else ((rule, key), [])
    probs = []
    verdict = row.get("verdict")
    if verdict not in VERDICTS:
        probs.append(f"verdict {verdict!r} is not pass, fail or unknown")
    for key in ("quote", "reason"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            probs.append(f"{key} is required")
    item = row.get("item")
    decided = verdict in ("pass", "fail")
    extra = ""
    if rule == "R06":
        extra = norm(row.get("role")).replace(" ", "-").replace("_", "-")
        label = norm(row.get("label"))
        if extra not in ROLES:
            probs.append(f"role {row.get('role')!r} is not one of {', '.join(ROLES)}")
        if decided and label not in LABELS:
            probs.append(f"label {row.get('label')!r} is not one of the six")
        elif decided and (label in PASS_LABELS) != (verdict == "pass"):
            probs.append(f"label {label!r} needs verdict {'pass' if label in PASS_LABELS else 'fail'}")
    elif rule == "R10":
        extra = norm(row.get("step"))
        if extra not in STEPS:
            probs.append(f"step {row.get('step')!r} is not restate or compare")
        if extra == "restate":
            terms = row.get("unclear_terms")
            if decided and (not isinstance(row.get("restatement"), str) or not row["restatement"].strip()):
                probs.append("restatement is required")
            if terms is None and not decided:
                pass
            elif not isinstance(terms, list) or not all(isinstance(t, str) for t in terms):
                probs.append("unclear_terms must be a list of strings")
            elif terms and verdict == "pass":
                probs.append("a restatement with unclear terms fails")
    elif rule == "R19":
        support, stretch = norm(row.get("support")), row.get("stretch")
        if decided and support not in SUPPORT:
            probs.append(f"support {row.get('support')!r} is not supported, stretched or unsupported")
        elif decided and (support == "supported") != (verdict == "pass"):
            probs.append(f"support {support!r} needs verdict {'pass' if support == 'supported' else 'fail'}")
        if stretch not in (None, "") and stretch not in STRETCHES:
            probs.append(f"stretch {stretch!r} is not one of {', '.join(STRETCHES)}")
        if support == "stretched" and stretch not in STRETCHES:
            probs.append("a stretched sentence names its stretch")
    elif rule == "R09":
        call = norm(row.get("call"))
        if decided and call not in CALLS:
            probs.append(f"call {row.get('call')!r} is not 'knew it' or 'new to me'")
        elif decided and (call == "new to me") != (verdict == "pass"):
            probs.append(f"call {call!r} needs verdict {'pass' if call == 'new to me' else 'fail'}")
        if call == "knew it" and not str(row.get("system") or "").strip():
            probs.append("a 'knew it' call names the internal system that shows it")
    elif rule == "R14":
        flag = row.get("flag")
        if verdict == "fail" and flag not in FLAGS:
            probs.append("a failed block names its flag, a to e")
        if verdict == "pass" and flag not in (None, ""):
            probs.append("a passed block has no flag")
    elif rule == "R07":
        if decided and not str(row.get("rival") or "").strip():
            probs.append("rival is required: the name swapped in")
    elif rule == "R01":
        if decided and not str(row.get("top_item") or "").strip():
            probs.append("top_item is required: the finding ranked first in the scope")
    elif rule == "R21":
        if decided and not str(row.get("weakest") or "").strip():
            probs.append("weakest is required: the number as written")
        if not isinstance(row.get("relies_on", []), list):
            probs.append("relies_on must be a list")
    key = (str(item), extra)
    if key not in expected.get(rule, {}):
        label = f"{item!r}" + (f" ({extra})" if extra else "")
        probs.append(f"item {label} is not in the packet for {rule}")
    return (None, probs) if probs else ((rule, key), [])


EXTRA_FIELDS = ("role", "label", "step", "restatement", "unclear_terms", "support", "stretch", "call", "system",
                "flag", "rival", "top_item", "weakest", "relies_on")


def collect(run):
    ctx, err = load_run(run)
    if err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2
    result = {"ts": now(), "bundle_sha": ctx["bundle_sha"], "ok": True, "rules": {}, "malformed": [],
              "warnings": [], "calls": {}}
    for judge, rules in judge_rules(ctx["rubric"]).items():
        folder = run / "verify" / "judges" / judge
        packet = read_json(folder / "packet.json")
        problem = None
        if not isinstance(packet, dict):
            problem = "no packet: run judges.py prepare and this judge"
        elif packet.get("bundle_sha") != ctx["bundle_sha"]:
            problem = "the packet was built from an older bundle: run judges.py prepare again and re-run this judge"
        expected, texts = {}, {}
        if problem is None:
            for rid, _ in rules:
                keys = (packet.get("expected") or {}).get(rid)
                if keys:
                    expected[rid] = {(k["item"], k.get("role") or k.get("step") or ""): None for k in keys}
                for entry in (packet.get("items") or {}).get(rid) or []:
                    texts[(rid, entry.get("item"))] = item_text(entry)
            compare = read_json(folder / "compare-packet.json")
            if isinstance(compare, dict) and compare.get("bundle_sha") == ctx["bundle_sha"]:
                for entry in compare.get("items") or []:
                    texts[("R10", entry.get("item"))] = texts.get(("R10", entry.get("item")), "") + " " + item_text(entry)
            elif isinstance(compare, dict):
                result["warnings"].append(f"{judge}: compare-packet.json is from an older bundle: run prepare-compare again")
            if "R21" in expected:
                texts[("R21", "report")] = " ".join(item_text(e) for e in packet.get("blocks") or
                                                    (packet.get("items") or {}).get("R14") or [])
        rule_ids = {rid for rid, _ in rules}
        modes = (packet.get("modes") or {}) if isinstance(packet, dict) else {}
        repeats = (packet.get("repeats") or 1) if isinstance(packet, dict) else 1
        carried = (packet.get("carried") or {}) if isinstance(packet, dict) else {}
        files, strays = run_files(folder, judge, packet if isinstance(packet, dict) else None)
        for path in strays:
            result["warnings"].append(f"{path.relative_to(run).as_posix()} is not a file this round's {judge} agents "
                                      f"write, so it is ignored and counts as no run")
        answers, closings, bad, ordered = run_rows(files, judge, rule_ids, expected, modes)
        for path, n, problem_text, line in bad:
            result["malformed"].append({"file": path.relative_to(run).as_posix(), "line": n, "problem": problem_text,
                                        "text": line[:200]})
        for path, n, rid, key, row in ordered:
            text = texts.get((rid, key[0]))
            if text and not row.get("carried") and not quote_found(row["quote"], text):
                result["warnings"].append(f"{path.relative_to(run).as_posix()} line {n}: the quote is not in "
                                          f"{key[0]}'s text: {row['quote'][:80]!r}")
        for rid in sorted(answers):
            for key, rows in answers[rid].items():
                fresh = sorted({r["_run"] for r in rows if not r.get("carried")})
                if fresh and any(r.get("carried") for r in rows):
                    result["warnings"].append(
                        f"{judge}: {rid} {key[0]}" + (f" ({key[1]})" if key[1] else "") + " was carried from an "
                        f"earlier round, so the new row in {', '.join(fresh)} is ignored and the carried verdict stands")
        for rid, level in rules:
            mode = modes.get(rid, "every")
            entry = {"judge": judge, "level": level, "mode": mode, "status": "pass", "expected": 0, "answered": 0,
                     "runs": repeats, "carried": int(carried.get(rid) or 0), "failing": [], "missing": [], "problems": []}
            to_judge = listed(packet, rid) if isinstance(packet, dict) else 0
            done = closings.get(rid) or {}
            passed = pass_runs_for(mode, done, to_judge)
            if problem:
                entry["problems"].append(problem)
            elif rid not in expected:
                entry["problems"].append(f"judges.py prepared no items for {rid} under judge:{judge}")
            elif mode == "exceptions" and to_judge and not done:
                entry["problems"].append(f"no closing row for {rid}, so its unlisted items have no result: the judge "
                                         f"ends with {{\"rule\":\"{rid}\",\"item\":\"*\",\"verdict\":\"complete\",\"read\":N}}")
            elif mode == "exceptions" and to_judge and len(passed) < repeats:
                short = [c["read"] for c in done.values() if c.get("read") != to_judge]
                entry["problems"].append(
                    f"the closing row for {rid} read {short[0] if short else 0}, and the packet lists {to_judge} items "
                    f"for {rid}, so the unlisted items have no result" if short else
                    f"{len(passed)} of {repeats} runs of {rid} wrote a closing row, so the unlisted items have no result")
            if not entry["problems"]:
                entry["expected"] = len(expected[rid])
                for key in expected[rid]:
                    verdict, rows, counted, minority = decide(answers[rid].get(key, []), runs_needed(rid, key, repeats),
                                                              passed)
                    for row in minority:  # the majority passed it; the failing run stays visible
                        result["warnings"].append(
                            f"{judge}: {rid} {key[0]}" + (f" ({key[1]})" if key[1] else "")
                            + f" passed, but {len(minority)} of {counted} runs failed it; {row['_run']}: "
                            f"{row['quote']!r}, {row['reason']}")
                    if verdict is None:
                        need = runs_needed(rid, key, repeats)
                        entry["missing"].append(key[0] + (f" ({key[1]})" if key[1] else "")
                                                + (f", {counted} of {need} runs" if need > 1 else ""))
                        continue
                    entry["answered"] += 1
                    if rid == "R09" and rows:  # one call per finding, the decided one, for the calibration log
                        result["calls"].setdefault("R09", []).append(
                            {"item": key[0], "call": norm(rows[0].get("call")) or None, "system": rows[0].get("system"),
                             "verdict": verdict})
                    if verdict != "pass":
                        seen = set()
                        for row in rows:
                            fail = {"item": key[0], "verdict": row["verdict"], "quote": row["quote"], "reason": row["reason"]}
                            fail.update({k: row[k] for k in EXTRA_FIELDS if row.get(k) not in (None, "", [])})
                            if row.get("carried"):
                                fail["carried_from"] = row.get("carried_from")
                            elif counted > 1:
                                fail["runs"] = f"{len(rows)} of {counted} runs failed it"
                            sig = json.dumps(fail, sort_keys=True)
                            if sig not in seen:  # identical rows from several runs are listed once
                                seen.add(sig)
                                entry["failing"].append(fail)
            if entry["problems"] or entry["missing"] or entry["failing"]:
                entry["status"] = "fail"
            if entry["problems"] or entry["missing"]:
                result["ok"] = False
            result["rules"][rid] = entry
    if result["malformed"]:
        result["ok"] = False
    write_json(run / "verify" / "judges.json", result)
    for rid, e in sorted(result["rules"].items()):
        tail = "; ".join(e["problems"]) if e["problems"] else f"{len(e['failing'])} failing, {len(e['missing'])} missing"
        print(f"{'pass' if e['status'] == 'pass' else 'FAIL'}  {rid} ({e['level']}, {e['judge']}): {tail}")
    for m in result["malformed"]:
        print(f"MALFORMED {m['file']} line {m['line']}: {m['problem']}")
    for w in result["warnings"]:
        print(f"warning: {w}")
    print(f"Wrote verify/judges.json: {'complete' if result['ok'] else 'INCOMPLETE, see the lines above'}")
    return 0 if result["ok"] else 1


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    commands = {"prepare": prepare, "prepare-compare": prepare_compare, "collect": collect}
    if len(argv) != 3 or argv[1] not in commands:
        print(__doc__)
        return 2
    return commands[argv[1]](Path(argv[2]))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
