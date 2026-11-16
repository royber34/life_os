#!/usr/bin/env python3
"""Check a run against the code rules of its rubric.

    python -I rubric_check.py <run-dir> [--rubric <path>] [--previous <prose.json>]

Reads dashboard/bundle.json, verify/verdicts.jsonl, dashboard/screens/layout.json, dashboard/index.html,
dashboard/onepager.html and onepager.pdf (each when present), and the rubric (default <run>/rubric.json).
Writes verify/rubric-code.json: a list with one row per code rule,
{id, level, status: pass|fail|n/a, failures: [{where, text, why}], note}, and prints one line per rule.
Exit 0 when no must rule fails, 1 when one does, 2 when the run folder or the rubric is unusable.

Standard library only. The contract is in references/client-mode.md. The rubric is read only for id,
level and check; each check below follows that rule's check_detail.
"""
import argparse
import datetime as dt
import html.parser
import json
import re
import sys
from pathlib import Path

CLIENT_KINDS = {"Measured", "Public record", "One day's check"}
TABS = {"moves", "overview", "sowhat", "timeline", "gtm", "ai", "competition", "market", "deepdive"}
NAV_TABS = ["overview", "sowhat", "timeline", "gtm", "ai", "competition", "deepdive"]
VIZ_TYPES = {"dots", "pips", "bars", "range", "share"}
CARD_FIELDS = ("so", "value", "label", "means")
# Every reader-facing text field of a move: the card (title to further) and its fold (what to if_wrong).
MOVE_FIELDS = ("title", "stat", "found", "matters", "idea", "further", "what", "why", "trigger", "money",
               "check_first", "test", "watch", "if_wrong")
FURTHER_PREFIX = "Where to look further:"
REPORT_LINK = "{{report_link}}"
# Built-in stats count the research itself (rows, docs, cutoff), so a typed number equal to one is chance.
RUN_STATS = {"events_total", "metrics_total", "gtm_actions", "gtm_views_total", "competitors_total",
             "landscape_total", "lanes_total", "docs_total", "cutoff"}
IMPERATIVES = set("""add ask audit build buy call check claim compare confirm count cut decide draft extend find fix
give have keep launch look make move offer plan post publish pull put reply review run send set ship shift spend
split start state test trace track try use weigh write""".split())
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"

CITE_RE = re.compile(r"\[c:([^\]\s]+)\]")
TOKEN_RE = re.compile(r"\{\{[^{}]*\}\}")
STAT_TOKEN_RE = re.compile(r"\{\{\s*(stat|kpi)\s*:[^{}]*\}\}")
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\((?:[^()\s]+)\)")
WORD_RE = re.compile(r"[A-Za-z0-9][\w'%.,-]*")
SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
BLOCK_RE = re.compile(r"\n\s*\n|\n(?=[ \t]*(?:[-*+]|\d+[.)])[ \t])")
NUM_RE = re.compile(r"\$?\d[\d,.\-]*\d%?[KMB]?|\$?\d%?[KMB]?")
LONG_DATE_RE = re.compile(rf"\b\d{{1,2}} ({MONTHS}) 20\d\d\b")
ISO_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
URL_RE = re.compile(r"https?://\S+")
QUOTED_RE = re.compile(r"\"[^\"]*\"|“[^”]*”")
MAY_DATE_RE = re.compile(r"\b\d{1,2} May\b|\bMay \d{1,2}\b|\bMay 20\d\d\b")
NUMBER_WORD_RE = re.compile(r"(?i)\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|half|dozen|hundred|thousand|million|billion)\b")

# The rubric's own patterns, copied from each rule's check_detail.
R02_ESTIMATE = re.compile(r"(?i)\b(revenue|turnover|estimated?|modell?ed|assumed model)\b")
R02_DISCLAIMER = re.compile(r"(?i)directional only|error rate|wrong rate|may be wrong|isn't perfect|least reliable|not legal advice|how far to trust|\b1 in \d+ facts")
R04_SELLING = re.compile(r"(?i)\b(book|schedule|call us|contact us|get in touch|reach out|let's talk|our (team|services?)|we can help|we help|consult(ing|ation|ant)?|engagement|workshop|proposal|free (call|session|audit))\b")
R12_YOU = re.compile(r"(?i)\b(you|your|yours|you'd|you'll|you're)\b")
R12_SHOULD = re.compile(r"(?i)\bshould\b")
R12_PHRASES = re.compile(r"(?i)first thing to do|if you only do|cheap(est)? (test|check)|quick check|test you can run|easy fix|\bsimply\b")
R13_INTERNAL = re.compile(r"(?i)\b(internal|in-house|company's own|its own)\s+(data|numbers|records|sales|figures)\b[^.]{0,40}\b(would|could|can|will)\s+(show|settle|answer|tell|confirm|prove)\b|only internal data")
R15_HEDGE = re.compile(r"(?i)\b(may|might|could|possibly|perhaps|likely|unclear|appears?|seems?|rough(ly)?)\b|isn't known|is unknown|not known|isn't public|can't (show|tell)|cannot (show|tell)|can't be ruled out")
R25_ASKS = re.compile(r"(?i)\b(access|connect(ing|ion)? to|share|send|grant|provide|give us|request|held by|we need|read-only|should|you|your)\b")
# Result claims: the rubric names 'would show' and 'would prove'; the same verbs as R13(b) are added.
RESULT_CLAIM = re.compile(r"(?i)\b(would|will)\s+(show|prove|confirm|settle|reveal|tell)\b")
# R13(a): a further line has to name a record or a place. A vocabulary check, so it errs towards passing.
RECORD_RE = re.compile(r"(?i)\b(sales|orders?|returns?|repairs?|tickets?|requests?|accounts?|crm|analytics|search console|"
                       r"dealers?|sell-through|registers?|registry|records?|invoices?|inventory|stock|reviews?|warrant(y|ies)|"
                       r"registrations?|ads manager|google ads|meta|shopify|amazon|seller central|vendor central|customs|"
                       r"filings?|court|librar(y|ies)|logs?|data|reports?|database|back end|back-end|erp|emails?|campaigns?|"
                       r"listings?|prices?|pricing|contracts?|files?|surveys?|support|service|complaints?|claims?|traffic|"
                       r"search terms?|keywords?|trends|archives?|forums?|reddit|youtube|website|site|store|pages?|ledger)\b")
IMPACT_FLOOR_RE = re.compile(r"(?i)\b(smallest|detect\w*|noise|normal range|floor)\b|wouldn't show|would not show|too small to show")


class Unusable(Exception):
    """The run folder, the bundle or the rubric can't be read."""


# ---------------------------------------------------------------- reading

def read_json(path, required=False):
    if not path.exists():
        if required:
            raise Unusable(f"missing {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as err:
        raise Unusable(f"{path}: {err}")


def read_jsonl(path):
    if not path.exists():
        return []
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError as err:
                raise Unusable(f"{path} line {n}: {err}")
    return rows


def read_rubric(path):
    rules = read_json(path, required=True)
    if not isinstance(rules, list) or not all(isinstance(r, dict) and r.get("id") and r.get("check") for r in rules):
        raise Unusable(f"{path}: the rubric must be a list of rules, each with an id and a check")
    return rules


def newest_draft(folder):
    """The newest file in verify/drafts/. The folder only ever holds earlier drafts."""
    drafts = sorted((p for p in folder.glob("*.json") if p.is_file()), key=lambda p: p.stat().st_mtime) if folder.is_dir() else []
    return drafts[-1] if drafts else None


class Run:
    def __init__(self, folder, previous=None):
        if not folder.is_dir():
            raise Unusable(f"not a folder: {folder}")
        self.dir = folder
        self.bundle = read_json(folder / "dashboard" / "bundle.json", required=True)
        if not isinstance(self.bundle, dict) or not isinstance(self.bundle.get("prose"), dict):
            raise Unusable("dashboard/bundle.json has no prose")
        self.prose = self.bundle["prose"]
        self.config = self.bundle.get("config") or {}
        self.client = self.config.get("report_mode") == "client"
        self.onepager = self.prose.get("onepager") or None
        self.tops = {t: v for t, v in (self.prose.get("top") or {}).items() if isinstance(v, dict)}
        self.moves = (self.prose.get("moves") or {}).get("items") or []
        self.trails = self.bundle.get("trails")
        self.claims = self.bundle.get("claims") or {}
        self.verdicts = read_jsonl(folder / "verify" / "verdicts.jsonl")
        self.ledger = {}
        for row in read_jsonl(folder / "verify" / "ledger.jsonl"):
            for key in [row.get("id"), *(row.get("merged_ids") or [])]:
                self.ledger.setdefault(key, row)
        self.layout = read_json(folder / "dashboard" / "screens" / "layout.json")
        page = folder / "dashboard" / "index.html"
        self.page = page.read_text(encoding="utf-8", errors="replace") if page.exists() else None
        path = previous or newest_draft(folder / "verify" / "drafts")
        prev = read_json(path, required=True) if path else None
        if isinstance(prev, dict) and isinstance(prev.get("prose"), dict):
            prev = prev["prose"]  # a whole bundle was given
        self.previous, self.previous_name = prev, (path.name if path else None)


# ---------------------------------------------------------------- text

def norm(text):
    """Curly apostrophes count as straight ones, so "isn't" and "isn’t" match the same patterns."""
    return ("" if text is None else str(text)).replace("’", "'").replace("‘", "'")


def plain(text):
    """The text a reader sees, minus [c:id] markers, {{...}} tokens and markdown markup."""
    t = norm(text)
    t = CITE_RE.sub("", t)
    t = TOKEN_RE.sub("", t)
    t = MD_LINK_RE.sub(r"\1", t)
    t = re.sub(r"\*\*|__|`", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r" ([.,;:!?)])", r"\1", t).strip()


def words(text):
    return len(WORD_RE.findall(plain(text)))


def blocks(text):
    """Paragraphs and list items: a field without breaks is one block."""
    return [b.strip() for b in BLOCK_RE.split(str(text or "")) if b.strip()]


def sentences(text):
    """Split at . ! or ? followed by a space and a capital, after splitting into blocks. Keeps the markup."""
    return [s.strip() for b in blocks(norm(text)) for s in SENT_RE.split(b) if s.strip()]


def has_digit(text):
    return any(ch.isdigit() for ch in text)


def cites(text):
    return bool(CITE_RE.search(str(text or "")) or STAT_TOKEN_RE.search(str(text or "")))


def clip(text, n=200):
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    return t if len(t) <= n else t[: n - 3] + "..."


def is_date(text):
    t = str(text or "")
    return bool(LONG_DATE_RE.search(t) or ISO_DATE_RE.search(t))


def iso_dates(text):
    out = set(ISO_DATE_RE.findall(str(text or "")))
    for m in LONG_DATE_RE.finditer(str(text or "")):
        try:
            out.add(dt.datetime.strptime(m.group(0), "%d %B %Y").date().isoformat())
        except ValueError:
            pass
    return out


def first_word(text):
    m = re.search(r"[A-Za-z]+", plain(text))
    return m.group(0) if m else ""


def walk(node, path):
    """(path, text) for every string under node. Lists of claim ids are skipped, they're ids."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            if k != "claims":
                yield from walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")


def cited_ids(item):
    """Claim ids a finding or point rests on: its claims list first, then any cited in its text, in order."""
    out = [str(x) for x in item.get("claims") or []]
    for key in ("value", "label", "means", "reasoning"):
        out += CITE_RE.findall(str(item.get(key) or ""))
    return list(dict.fromkeys(out))


def all_cited(node):
    """Every claim id in a prose tree: [c:id] markers and claims lists."""
    ids = set()
    if isinstance(node, str):
        ids.update(CITE_RE.findall(node))
    elif isinstance(node, dict):
        for k, v in node.items():
            if k == "claims" and isinstance(v, list):
                ids.update(str(x) for x in v if isinstance(x, str))
            else:
                ids |= all_cited(v)
    elif isinstance(node, list):
        for v in node:
            ids |= all_cited(v)
    return ids


def F(where, text, why):
    return {"where": where, "text": clip(text), "why": why}


def result(failures, note=""):
    return {"status": "fail" if failures else "pass", "failures": failures, "note": note}


def na(note):
    return {"status": "n/a", "failures": [], "note": note}


# ---------------------------------------------------------------- the first screen: one-pager and tab tops

def onepager_fields(run):
    """(where, text) for every line the one-pager prints."""
    op = run.onepager or {}
    out = [("onepager.headline", op.get("headline"))]
    for i, f in enumerate(op.get("findings") or []):
        out += [(f"onepager.findings[{i}].{k}", f.get(k)) for k in CARD_FIELDS]
    out += [("onepager.basis", op.get("basis")), ("onepager.way_in", op.get("way_in"))]
    return [(w, t) for w, t in out if isinstance(t, str) and t.strip()]


def viz_strings(viz):
    viz = viz or {}
    out = [r.get(k) for r in viz.get("rows") or [] for k in ("label", "text")]
    out += list(viz.get("names") or []) + [viz.get(k) for k in ("min_label", "max_label", "unit")]
    return [s for s in out if isinstance(s, str)]


def top_fields(run, links=True, viz=False):
    """(where, text) for every line a tab top shows: headline, note, cards, and with links their link labels."""
    out = []
    for tab, top in run.tops.items():
        base = f"top.{tab}"
        out += [(f"{base}.headline", top.get("headline")), (f"{base}.note", top.get("note"))]
        for i, p in enumerate(top.get("points") or []):
            out += [(f"{base}.points[{i}].{k}", p.get(k)) for k in CARD_FIELDS]
            if links:
                out.append((f"{base}.points[{i}].goto_label", p.get("goto_label")))
            if viz:
                out += [(f"{base}.points[{i}].viz", s) for s in viz_strings(p.get("viz"))]
        if links:
            out += [(f"{base}.doors[{i}].label", d.get("label")) for i, d in enumerate(top.get("doors") or [])]
    return [(w, t) for w, t in out if isinstance(t, str) and t.strip()]


def cards(run):
    """(where, tab, card) for every one-pager finding and tab-top card. tab is None on the one-pager."""
    out = [(f"onepager.findings[{i}]", None, f) for i, f in enumerate((run.onepager or {}).get("findings") or [])]
    for tab, top in run.tops.items():
        out += [(f"top.{tab}.points[{i}]", tab, p) for i, p in enumerate(top.get("points") or [])]
    return out


def headlines(run):
    out = [("onepager.headline", (run.onepager or {}).get("headline"))] if run.onepager else []
    return out + [(f"top.{tab}.headline", top.get("headline")) for tab, top in run.tops.items()]


def card_text(card):
    return " ".join(str(card.get(k) or "") for k in CARD_FIELDS)


def onepager_missing(run):
    """No one-pager: n/a outside client mode, a failure in it."""
    if run.client:
        return result([F("prose.onepager", "", "client mode needs prose.onepager")])
    return na("no one-pager: this run is not in client mode")


# ---------------------------------------------------------------- rules

def r02(run):
    """Estimates, modelled numbers, disclaimers and the error rate stay off the first screen."""
    if not run.onepager and not run.tops:
        return na("no one-pager and no tab tops")
    fails = []
    for where, tab, card in cards(run):
        kind = card.get("kind")
        # The AI tab's inside-the-company cards may be Inferred (R23). Cards carry no other marker for
        # "inside the company", so any Inferred card on the AI top is allowed.
        if kind not in CLIENT_KINDS and not (kind == "Inferred" and tab == "ai"):
            fails.append(F(f"{where}.kind", kind, "(a) card kind outside Measured, Public record, One day's check"))
    for where, text in onepager_fields(run) + top_fields(run, viz=True):
        t = norm(text)
        fails += [F(where, t, f"(b) '{m.group(0)}': estimate or modelled number") for m in R02_ESTIMATE.finditer(t)]
        fails += [F(where, t, f"(c) '{m.group(0)}': disclaimer or error rate, which belongs in the checking details") for m in R02_DISCLAIMER.finditer(t)]
    return result(fails)


def headline_form(where, text, run):
    """R01's code precheck, which R03 asks of the one-pager headline."""
    out, t = [], norm(text)
    if not plain(t):
        return [F(where, t, "no headline")]
    if len(sentences(t)) != 1:
        out.append(F(where, t, "the headline is more than one sentence"))
    if words(t) >= 20:
        out.append(F(where, t, f"the headline runs {words(t)} words; it must stay under 20"))
    # "Names a number or a specific outside actor": a digit, a number word, or a capitalised word after the
    # first that isn't part of the company's own name. Only a proxy for "outside actor".
    own = {w.lower() for w in re.findall(r"[A-Za-z]+", str(run.config.get("name") or ""))}
    later = re.findall(r"(?<!^)\b[A-Z][a-z]+", plain(t))
    if not (has_digit(plain(t)) or NUMBER_WORD_RE.search(t) or any(w.lower() not in own for w in later)):
        out.append(F(where, t, "the headline names no number and no outside actor"))
    out += [F(where, t, f"hedge '{m.group(0)}' in the headline") for m in R15_HEDGE.finditer(MAY_DATE_RE.sub("", t))]
    out += [F(where, t, f"'{m.group(0)}' in the headline (R02)") for p in (R02_ESTIMATE, R02_DISCLAIMER) for m in p.finditer(t)]
    return out


def finding_anatomy(i, f, run):
    where = f"onepager.findings[{i}]"
    out = []
    if not has_digit(plain(f.get("value"))):
        out.append(F(f"{where}.value", f.get("value"), "the value holds no number"))
    if not (is_date(f.get("date")) or is_date(f.get("label"))):
        out.append(F(f"{where}.date", f.get("date"), "no read date (ISO, or as in 5 November 2026)"))
    text_ids = [c for k in CARD_FIELDS for c in CITE_RE.findall(str(f.get(k) or ""))]
    if not any(str((run.claims.get(c) or {}).get("source") or "").startswith(("http://", "https://")) for c in text_ids):
        out.append(F(where, f.get("label"), "no source link: no [c:id] in the finding's text has an http(s) source"))
    means = f.get("means")
    if not plain(means):
        out.append(F(f"{where}.means", means, "no line on what it means"))
    elif len(sentences(means)) != 1 or words(means) > 25:
        out.append(F(f"{where}.means", means, f"the means line must be one sentence up to 25 words ({len(sentences(means))} sentences, {words(means)} words)"))
    if f.get("id") not in (run.trails or {}):
        out.append(F(f"{where}.id", f.get("id"), "the 'how we got here' link has no evidence trail to open"))
    return out


def onepager_pdf(run):
    """Fails when onepager.pdf exists and isn't one page. The render test checks A4 and Letter itself."""
    pdf = run.dir / "dashboard" / "onepager.pdf"
    if not pdf.exists():
        return [], "PDF page count not checked: no dashboard/onepager.pdf yet (render_test.py checks A4 and Letter)"
    pages = len(re.findall(rb"/Type\s*/Page(?![s\w])", pdf.read_bytes()))
    fails = [] if pages == 1 else [F("dashboard/onepager.pdf", f"{pages} pages", "the one-pager must print on exactly 1 A4 page")]
    return fails, "Letter page count is checked by render_test.py"


def r03(run):
    """One headline, 3 to 5 complete findings, a basis line and a way-in line, on one printed page."""
    op = run.onepager
    if not op:
        return onepager_missing(run)
    fails = headline_form("onepager.headline", op.get("headline"), run)
    findings = op.get("findings") or []
    if not 3 <= len(findings) <= 5:
        fails.append(F("onepager.findings", f"{len(findings)} findings", "the one-pager holds 3 to 5 findings"))
    for i, f in enumerate(findings):
        fails += finding_anatomy(i, f, run)
    basis, cutoff = op.get("basis"), run.config.get("cutoff") or (run.bundle.get("meta") or {}).get("cutoff")
    if not re.search(r"(?i)\bpublic\b", norm(basis)):
        fails.append(F("onepager.basis", basis, "the basis line must say the sources are public"))
    if not iso_dates(basis) or (cutoff and cutoff not in iso_dates(basis)):
        fails.append(F("onepager.basis", basis, f"the basis line must name the cutoff date{f' ({cutoff})' if cutoff else ''}"))
    way = norm(op.get("way_in"))
    if REPORT_LINK not in way and not URL_RE.search(way):
        fails.append(F("onepager.way_in", way, f"the way-in line has no report link ({REPORT_LINK})"))
    # "How to open it": a passphrase, a password or an instruction to open. A wording check only.
    if not re.search(r"(?i)\b(passphrase|password|passcode|pass phrase|open)\b", way):
        fails.append(F("onepager.way_in", way, "the way-in line doesn't say how to open the report"))
    total = sum(words(t) for _, t in onepager_fields(run)) + 4 * len(findings)  # plus each "How we got here" link
    if total > 350:
        fails.append(F("onepager", f"{total} words", "the one-pager runs over 350 words"))
    pdf_fails, note = onepager_pdf(run)
    return result(fails + pdf_fails, note)


class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs += [v for k, v in attrs if k == "href" and v]


def onepager_links(run):
    """Links in the built one-pager that are neither a source nor a finding's trail."""
    path = run.dir / "dashboard" / "onepager.html"
    if not path.exists():
        return [], "dashboard/onepager.html not built yet, so only the text was checked for links"
    parser = Links()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    sources = {str(c.get("source")) for c in run.claims.values()}
    for t in (run.trails or {}).values():
        sources |= {str(c.get(k)) for c in t.get("claims") or [] for k in ("source", "checked_url")}
    ids = {str(f.get("id")) for f in run.onepager.get("findings") or []}
    other = [h for h in parser.hrefs if h not in sources and not ("#trail=" in h and h.split("#trail=", 1)[1] in ids)]
    if len(other) == 1:
        return [], ""
    return [F("dashboard/onepager.html", " ".join(other) or "none", f"{len(other)} links are neither a source nor a trail; the one-pager has exactly one full-report link")], ""


def r04(run):
    """The one-pager never sells, and the full report is its only next step."""
    if not run.onepager:
        return onepager_missing(run)
    fails = []
    for where, text in onepager_fields(run):
        t = norm(text)
        fails += [F(where, t, f"'{m.group(0)}' reads as selling") for m in R04_SELLING.finditer(t)]
        for m in list(URL_RE.finditer(t)) + list(MD_LINK_RE.finditer(t)):
            fails.append(F(where, t, f"'{clip(m.group(0), 60)}' is a link that is neither a source, a trail nor the report"))
    n = sum(norm(t).count(REPORT_LINK) for _, t in onepager_fields(run))
    if n != 1:
        fails.append(F("onepager.way_in", run.onepager.get("way_in"), f"{REPORT_LINK} appears {n} times; the full-report link appears once"))
    link_fails, note = onepager_links(run)
    return result(fails + link_fails, note)


def r05(run):
    """The one-pager and the Overview top show the same headline, values and claims in the same order."""
    op = run.onepager
    if not op:
        return onepager_missing(run)
    ov = run.tops.get("overview")
    if not ov:
        return result([F("top.overview", "", "no Overview top to compare with the one-pager")])
    fails = []
    if plain(op.get("headline")) != plain(ov.get("headline")):
        fails.append(F("top.overview.headline", ov.get("headline"), f"differs from the one-pager headline: {clip(op.get('headline'), 90)}"))
    mine = [(plain(f.get("value")), cited_ids(f)) for f in op.get("findings") or []]
    theirs = [(plain(p.get("value")), cited_ids(p)) for p in ov.get("points") or []]
    for i in range(max(len(mine), len(theirs))):
        if i >= len(theirs):
            fails.append(F(f"onepager.findings[{i}]", mine[i][0], "the Overview top has no card for this finding"))
        elif i >= len(mine):
            fails.append(F(f"top.overview.points[{i}]", theirs[i][0], "an Overview top card the one-pager lacks"))
        elif mine[i] != theirs[i]:
            fails.append(F(f"top.overview.points[{i}]", f"{theirs[i][0]} {theirs[i][1]}", f"differs from the one-pager finding: {mine[i][0]} {mine[i][1]}"))
    return result(fails)


def r11_units(run):
    """(area, where, text): one-pager lines, tab-top lines and every text field of every move."""
    out = [("one-pager", w, t) for w, t in onepager_fields(run)]
    out += [("tab tops", w, t) for w, t in top_fields(run, links=False)]
    for i, m in enumerate(run.moves):
        out += [("moves", f"moves.items[{i}] {m.get('id')}.{k}", m.get(k)) for k in MOVE_FIELDS if isinstance(m.get(k), str) and m.get(k).strip()]
    return out


def r11(run):
    """No sentence over 30 words, no paragraph or card field over 60."""
    units = r11_units(run)
    if not units:
        return na("no one-pager, tab tops or moves")
    fails, tally = [], {}
    for area, where, text in units:
        t = tally.setdefault(area, [0, 0, 0, 0])  # sentences, long sentences, fields, long fields
        for block in blocks(text):
            t[2] += 1
            if words(block) > 60:
                t[3] += 1
                fails.append(F(where, block, f"{words(block)} words in one field or paragraph (limit 60)"))
            for s in sentences(block):
                t[0] += 1
                if words(s) > 30:
                    t[1] += 1
                    fails.append(F(where, s, f"{words(s)} words in one sentence (limit 30)"))
    note = "; ".join(f"{a}: {t[1]} of {t[0]} sentences over 30, {t[3]} of {t[2]} fields over 60" for a, t in tally.items())
    return result(fails, note)


def outside_quotes(text):
    return QUOTED_RE.sub(" ", norm(text))


def r12(run):
    """No you, your or should; no command phrasing; nothing on the first screen opens with a command."""
    fails = []
    for where, text in walk(run.prose, "prose"):
        if "quote" in where.rsplit(".", 1)[-1]:
            continue  # quoted source passages
        bare = outside_quotes(text)
        for m in list(R12_YOU.finditer(bare)) + list(R12_SHOULD.finditer(bare)):
            fails.append(F(where, text, f"(a) '{m.group(0)}' addresses the reader"))
        fails += [F(where, text, f"(b) '{m.group(0)}' reads as a command") for m in R12_PHRASES.finditer(norm(text))]
    # (c) the first word of each headline, card line and link label. The note above the cards is neither.
    # Compared without case, so a noun such as "Offer" or "Review" at the start fails too.
    lines = [x for x in onepager_fields(run) + top_fields(run) if not x[0].endswith(".note")]
    for where, text in lines:
        if first_word(text).lower() in IMPERATIVES:
            fails.append(F(where, text, f"(c) opens with the command '{first_word(text)}'"))
    return result(fails)


def further_problems(where, line):
    t = norm(line)
    if not t.strip():
        return [F(where, "", "(a) no 'Where to look further:' line")]
    out = []
    if not t.startswith(FURTHER_PREFIX):
        out.append(F(where, t, f"(a) must start '{FURTHER_PREFIX}'"))
    if words(t) > 30:  # the whole line, its opening words included
        out.append(F(where, t, f"(a) runs {words(t)} words (limit 30)"))
    if not RECORD_RE.search(t[len(FURTHER_PREFIX):] if t.startswith(FURTHER_PREFIX) else t):
        out.append(F(where, t, "(a) names no record or place to look in"))
    out += [F(where, t, f"(a) '{m.group(0)}': second person or should") for p in (R12_YOU, R12_SHOULD) for m in p.finditer(t)]
    out += [F(where, t, f"(a) '{m.group(0)}': a claim about what it would show") for m in RESULT_CLAIM.finditer(t)]
    return out


def r13(run):
    """Each move ends with a Where to look further line; no 'internal data would show' anywhere."""
    fails = []
    for i, m in enumerate(run.moves):
        fails += further_problems(f"moves.items[{i}] {m.get('id')}.further", m.get("further"))
    hits = [F(where, text, f"(b) '{m.group(0)}': says what internal data would show")
            for where, text in walk(run.prose, "prose") for m in R13_INTERNAL.finditer(norm(text))]
    in_heads = sum(1 for h in hits if h["where"].endswith(".headline"))
    note = f"(b): {len(hits)} matches, {in_heads} in a headline" + ("" if run.moves else "; (a) not checked: no moves")
    return result(fails + hits, note)


def hedges(text):
    """Hedge words, with the month May left out."""
    return [m.group(0) for m in R15_HEDGE.finditer(MAY_DATE_RE.sub(" ", norm(plain(text))))]


def r15(run):
    """No hedge in a headline, at most one per card or finding, at most two in a move's found and matters."""
    fails = []
    for where, text in headlines(run):
        found = hedges(text)
        if found:
            fails.append(F(where, text, f"hedge in a headline ({', '.join(found)}); limit 0"))
    for where, _, card in cards(run):
        found = hedges(card_text(card))
        if len(found) > 1:
            fails.append(F(where, card_text(card), f"{len(found)} hedges in one card ({', '.join(found)}); limit 1"))
    for i, m in enumerate(run.moves):
        text = f"{m.get('found') or m.get('what') or ''} {m.get('matters') or m.get('why') or ''}"
        found = hedges(text)
        if len(found) > 2:
            fails.append(F(f"moves.items[{i}] {m.get('id')}", text, f"{len(found)} hedges in found and why it matters ({', '.join(found)}); limit 2"))
    if not headlines(run) and not run.moves:
        return na("no one-pager, tab tops or moves")
    return result(fails, "the one-time list of limits at the end is not checked by code")


def live_tabs(run):
    tabs = set(TABS)
    if not run.prose.get("ai"):
        tabs.discard("ai")
    if not run.config.get("market"):
        tabs.discard("market")
    return tabs


def goto_resolves(run, target):
    t = str(target or "")
    kind, _, rest = t.partition(":")
    if not rest:
        return t in live_tabs(run)  # a bare tab id, as older bundles write it
    if kind == "move":
        return rest in {str(m.get("id")) for m in run.moves}
    if kind == "part":
        ai = run.prose.get("ai") or {}
        return rest in {str(p.get("id")) for p in ai.get("parts") or []} | ({"uses"} if ai.get("uses") else set())
    if kind == "tab":
        return rest in live_tabs(run)
    if kind == "doc":
        return rest in {r.get("doc") for r in run.bundle.get("library") or []}
    if kind == "id":
        # Element ids are drawn by the page script, so only the tab is checked here.
        tab, _, element = rest.partition("/")
        return tab in live_tabs(run) and bool(element)
    if kind == "trail":
        return rest in (run.trails or {})
    return False


def r16_card(where, tab, p, run):
    out = []
    limits = (("so", 10), ("value", 6), ("label", 25), ("means", 25))
    for key, limit in limits:
        if not plain(p.get(key)):
            out.append(F(f"{where}.{key}", "", f"no {key}"))
        elif words(p.get(key)) > limit:
            out.append(F(f"{where}.{key}", p.get(key), f"{key} runs {words(p.get(key))} words (limit {limit})"))
    value = norm(p.get("value"))
    if plain(value) and not (has_digit(plain(value)) or QUOTED_RE.search(value)):
        out.append(F(f"{where}.value", value, "the value holds no number and no quoted term"))
    if not p.get("kind"):
        out.append(F(f"{where}.kind", "", "no evidence kind"))
    # The link to the detail. In client mode the Overview cards link to their trail instead of a goto.
    linked = goto_resolves(run, p.get("goto")) or (tab == "overview" and p.get("trail") in (run.trails or {}))
    if not linked:
        out.append(F(f"{where}.goto", p.get("goto") or "", "no link to the detail" if not p.get("goto") else "the link doesn't resolve"))
    return out


def r16(run):
    """Every tab top: a headline, 3 to 5 complete cards, and no more than a short note above them."""
    if not run.tops:
        return na("no tab tops")
    fails = []
    for tab, top in run.tops.items():
        points = top.get("points") or []
        if not plain(top.get("headline")):
            fails.append(F(f"top.{tab}.headline", "", "no headline"))
        if not 3 <= len(points) <= 5:
            fails.append(F(f"top.{tab}.points", f"{len(points)} cards", "a tab top holds 3 to 5 cards"))
        if top.get("note") and words(top["note"]) > 40:
            fails.append(F(f"top.{tab}.note", top["note"], f"the note above the cards runs {words(top['note'])} words (limit 40)"))
        for i, p in enumerate(points):
            fails += r16_card(f"top.{tab}.points[{i}]", tab, p, run)
    return result(fails)


def r17(run):
    """Each tab top ends at or above 900 px at 1440 x 900."""
    if run.layout is None:
        return na("no dashboard/screens/layout.json: run render_test.py first")
    if not run.tops:
        return na("no tab tops")
    fails = []
    for tab in run.tops:
        row = run.layout.get(tab) if isinstance(run.layout, dict) else None
        if not isinstance(row, dict) or not isinstance(row.get("top_bottom_px"), (int, float)):
            fails.append(F(f"layout.{tab}", "", "the render didn't measure this tab's top, so it didn't show"))
            continue
        if list(row.get("viewport") or []) != [1440, 900]:
            fails.append(F(f"layout.{tab}.viewport", row.get("viewport"), "measured at another size than 1440 x 900"))
        if row["top_bottom_px"] > 900:
            fails.append(F(f"layout.{tab}.top_bottom_px", row["top_bottom_px"], "the last card ends below the first screen (900 px)"))
    return result(fails)


def verdict_index(run):
    """The latest verdict per id, and the distinct passes (verifiers) that confirmed it."""
    latest, passes = {}, {}
    for n, r in enumerate(run.verdicts):
        latest[r.get("id")] = r
        if r.get("status") == "confirmed":
            passes.setdefault(r.get("id"), set()).add(r.get("verifier") or f"row {n}")
    return latest, passes


def card_statements(where, card):
    """A card reads as its title, then value and label as one sentence, then what it means.
    A number in the title restates the value, so the value's citation covers it."""
    lead = f"{card.get('value') or ''} {card.get('label') or ''}".strip()
    out = [(f"{where}.value+label", s) for s in sentences(lead)]
    out += [(f"{where}.means", s) for s in sentences(card.get("means"))]
    if not cites(lead):
        out += [(f"{where}.so", s) for s in sentences(card.get("so"))]
    return out


def first_screen_statements(run):
    """Every sentence on the first screen. The one-pager's basis and way-in lines are left out: their only
    numbers are the run's cutoff date, which no ledger row holds."""
    out = []
    for where, text in headlines(run):
        out += [(where, s) for s in sentences(text)]
    for tab, top in run.tops.items():
        out += [(f"top.{tab}.note", s) for s in sentences(top.get("note"))]
    for where, _, card in cards(run):
        out += card_statements(where, card)
    return out


def first_screen_ids(run):
    """(where, id, on_onepager) for every claim the first screen cites."""
    out = []
    for where, tab, card in cards(run):
        ids = cited_ids(card) + CITE_RE.findall(str(card.get("so") or ""))
        out += [(where, i, tab is None) for i in dict.fromkeys(ids)]
    for where, text in headlines(run):
        out += [(where, i, where.startswith("onepager")) for i in CITE_RE.findall(str(text or ""))]
    for tab, top in run.tops.items():
        out += [(f"top.{tab}.note", i, False) for i in CITE_RE.findall(str(top.get("note") or ""))]
    return out


def value_numbers(value):
    """What a value says, for comparing: its numbers in order, or the plain text when it has none.
    Comparing the numbers keeps '25% to 35%' and '25% to 35% lower' together and tells '270' from '265 to 275'."""
    nums = NUM_RE.findall(plain(value))
    return " ".join(nums) if nums else plain(value).lower()


def value_conflicts(run):
    """Places across the prose where the same claim, cited first for a value, shows a different value."""
    seen = {}
    for where, node in value_cards(run.prose, "prose"):
        first = ([str(x) for x in node.get("claims") or []] + CITE_RE.findall(f"{node.get('value')} {node.get('label')}"))[:1]
        if first:
            seen.setdefault(first[0], []).append((where, node.get("value")))
    out = []
    for cid, places in seen.items():
        if len({value_numbers(v) for _, v in places}) > 1:
            shown = "; ".join(f"{w}: {plain(v)}" for w, v in places)
            out.append(F(places[0][0], shown, f"claim {cid} shows different values across the report"))
    return out


def value_cards(node, path):
    """Every object in the prose that shows a value with a label: tab-top cards, findings, key facts, stats."""
    if isinstance(node, dict):
        if isinstance(node.get("value"), str) and isinstance(node.get("label"), str):
            yield path, node
        for k, v in node.items():
            yield from value_cards(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from value_cards(v, f"{path}[{i}]")


def typed_stats(run):
    """Typed numbers on the first screen that repeat a stat about the company (config stats, KPIs, metric aggregates).
    Stats shown in one or two characters are left out: small numbers such as 34 recur in text by chance."""
    stats = {s.get("text"): sid for sid, s in (run.bundle.get("stats") or {}).items()
             if sid not in RUN_STATS and isinstance(s, dict) and has_digit(str(s.get("text") or ""))
             and len(str(s.get("text"))) >= 3 and not s.get("missing")}
    out = []
    for where, text in onepager_fields(run) + top_fields(run, links=False):
        if where in ("onepager.basis", "onepager.way_in"):
            continue
        for num in NUM_RE.findall(plain(text)):
            if num in stats:
                out.append(F(where, text, f"typed number {num} repeats {{{{stat:{stats[num]}}}}}; use the token"))
    return out


def r18(run):
    """Every first-screen number cites a confirmed row (twice for the one-pager) and shows one value everywhere."""
    if not run.onepager and not run.tops:
        return na("no one-pager and no tab tops")
    fails = []
    for where, s in first_screen_statements(run):
        if has_digit(plain(s)) and not cites(s):
            fails.append(F(where, s, "a number with no [c:id] or {{stat:id}} token"))
    latest, passes = verdict_index(run)
    for where, cid, on_onepager in first_screen_ids(run):
        status = (latest.get(cid) or {}).get("status")
        if status != "confirmed":
            fails.append(F(where, cid, f"claim {cid}: latest verdict is {status or 'missing'}, not confirmed"))
        elif on_onepager and len(passes.get(cid, ())) < 2:
            fails.append(F(where, cid, f"claim {cid}: confirmed by {len(passes.get(cid, ()))} pass; one-pager numbers need 2"))
    fails += value_conflicts(run) + typed_stats(run) + unmatched_figures(run)
    return result(fails, "" if run.verdicts else "no verify/verdicts.jsonl")


FIGURE_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)(?:\s*(K|M|B|bn|thousand|million|billion)\b)?")
SCALES = {"K": 1e3, "thousand": 1e3, "M": 1e6, "million": 1e6, "B": 1e9, "bn": 1e9, "billion": 1e9}
# A change a row states as two figures: "32.3 vs 23.9", "19.4 against 36.6", "from 120 to 90".
COMPARED_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)%?\s+(?:vs\.?|versus|against)\s+(\d[\d,]*(?:\.\d+)?)"
                         r"|\bfrom\s+(\d[\d,]*(?:\.\d+)?)%?\s+to\s+(\d[\d,]*(?:\.\d+)?)", re.I)


def figures(text):
    """(figure, scale) for every number in the text a reader sees: 'USD 3.2M' gives (3.2, 1000000)."""
    return [(float(m.group(1).replace(",", "")), SCALES.get(m.group(2) or "", 1.0)) for m in FIGURE_RE.finditer(plain(text))]


def row_figures(row):
    """The figures a ledger row holds, as written and at full scale, plus the percent change between any two
    figures it compares."""
    text = f"{row.get('text') or ''} {row.get('value') or ''}"
    out = []
    for x, scale in figures(text):
        out += [x, x * scale] if scale != 1 else [x]
    for m in COMPARED_RE.finditer(text):
        a, b = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        a, b = float(a.replace(",", "")), float(b.replace(",", ""))
        if a:
            out.append(abs(b - a) / a * 100)
    return out


def figure_in(x, scale, pool):
    """A card figure matches a row figure when it rounds to it. One written in thousands, millions or billions also
    matches the full figure within 5% (USD 3.2M for 3,215,000)."""
    for y in pool:
        if abs(x - y) <= 0.5 or (y >= 100 and abs(x - y) <= 0.005 * y):
            return True
        if scale != 1 and y and abs(x * scale - y) <= 0.05 * y:
            return True
    return False


def unmatched_figures(run):
    """Card numbers (value and label) that none of the card's cited rows holds. Confirming a row confirms what the row
    says, so a first-screen number has to be in its row: a figure worked out from rows needs a row of its own."""
    if not run.ledger:
        return [F("verify/ledger.jsonl", "", "missing, so first-screen numbers can't be matched to their rows")]
    out = []
    for where, _, card in cards(run):
        lead = f"{card.get('value') or ''} {card.get('label') or ''}"
        ids = cited_ids(card) + CITE_RE.findall(str(card.get("so") or ""))
        rows = [run.ledger[i] for i in ids if i in run.ledger]
        if not rows:
            continue  # uncited or unknown ids fail R18's other checks
        pool = [y for row in rows for y in row_figures(row)]
        missing = [x for x, scale in figures(lead) if not figure_in(x, scale, pool)]
        if missing:
            shown = ", ".join(f"{x:g}" for x in missing)
            out.append(F(where, plain(lead), f"{shown} {'is' if len(missing) == 1 else 'are'} in none of its cited rows ({', '.join(ids)}): cite the row "
                                              f"that holds it, or add a row for a figure worked out from others"))
    return out


def trail_id(run, tab, i, card):
    if tab is None:
        return card.get("id")
    goto = str(card.get("goto") or "")
    if card.get("trail"):
        return card["trail"]
    if goto.startswith("trail:"):
        return goto[6:]
    if tab == "overview" and run.onepager:
        findings = run.onepager.get("findings") or []
        return findings[i].get("id") if i < len(findings) else None
    return f"{tab}.{i}"


def trail_problems(where, trail, card):
    out = []
    claims = trail.get("claims") or []
    if not claims:
        out.append(F(where, "", "the trail lists no claim"))
    for c in claims:
        cw = f"{where} claim {c.get('id')}"
        if not any(str(c.get(k) or "").startswith(("http://", "https://")) for k in ("checked_url", "source")):
            out.append(F(cw, c.get("source"), "no source URL"))
        if not 1 <= words(c.get("quote")) <= 25:
            out.append(F(cw, c.get("quote"), f"the quoted passage runs {words(c.get('quote'))} words; it needs 1 to 25"))
        if not is_date(c.get("read")):
            out.append(F(cw, c.get("read"), "no read date"))
        if not c.get("status") or c.get("status") == "unchecked":
            out.append(F(cw, c.get("status"), "no verdict"))
    steps = sentences(trail.get("reasoning"))
    if not steps:
        out.append(F(where, "", "no reasoning joins the claims to the finding"))
    # Code can't tell which step no source states. It checks the two cases it can see: a claim whose basis is
    # inference, and a card of kind Inferred, each need a step labelled 'Inference:'.
    labelled = any(re.match(r"(?i)inference:", plain(s)) for s in steps)
    if not labelled and (any(c.get("basis") == "inference" for c in claims) or card.get("kind") == "Inferred"):
        out.append(F(where, trail.get("reasoning"), "rests on inference, and no step is labelled 'Inference:'"))
    return out


def r20(run):
    """Every one-pager finding and tab-top card opens a complete evidence trail."""
    if not run.onepager and not run.tops:
        return na("no one-pager and no tab tops")
    fails, trails = [], run.trails or {}
    for where, tab, card in cards(run):
        tid = trail_id(run, tab, int(re.search(r"\[(\d+)\]$", where).group(1)), card)
        if tid not in trails:
            fails.append(F(where, card.get("so") or card.get("value"), f"no evidence trail ({tid})"))
            continue
        fails += trail_problems(f"trails.{tid}", trails[tid], card)
    note = "" if run.trails is not None else "bundle.trails is absent; assemble builds trails in client mode only"
    return result(fails, note)


def page_markup(run):
    """The built page without its embedded bundle."""
    return re.sub(r"<script id=\"bundle\"[^>]*>.*?</script>", "", run.page, flags=re.S)


def page_tabs(run, markup):
    out = []
    m = re.search(r"\bTABS\s*=\s*\[([^\]]*)\]", markup)
    if not m:
        return [F("dashboard/index.html", "", "can't find the tab list in the page script")]
    tabs = [t for t in re.findall(r"['\"](\w+)['\"]", m.group(1)) if t in live_tabs(run)]
    if tabs != NAV_TABS:
        out.append(F("page nav", " | ".join(tabs), f"the tabs must run {' | '.join(NAV_TABS)}"))
    first = re.search(r"\bfirstTab\s*=\s*\(\)\s*=>\s*['\"](\w+)['\"]", markup)
    if not first or first.group(1) != "overview":
        out.append(F("page nav", first.group(1) if first else "", "the page must open on Overview"))
    return out


def in_order(markup, start, markers):
    """Positions of each marker after start, in the order given. None when one is missing."""
    pos, out = start, []
    for marker in markers:
        found = [markup.find(x, pos) for x in marker if markup.find(x, pos) >= 0]
        if not found:
            return None
        pos = min(found)
        out.append(pos)
    return out


def page_sections(markup):
    out = []
    ov = markup.find('data-page="overview"')
    if in_order(markup, ov, [['data-band="overview"'], ['id="swot"'], ['id="connections"', 'id="further"']]) is None:
        out.append(F("overview", "", "the Overview must run top, SWOT, then where to look further"))
    sw = markup.find('data-page="sowhat"')
    if in_order(markup, sw, [['data-band="sowhat"'], ['id="areas"'], ['id="signals"']]) is None:
        out.append(F("sowhat", "", "the So what must run top, the areas, then opportunities and what's working"))
    if "tt-allmoves" not in markup:
        out.append(F("sowhat", "", "no fold for the further areas (tt-allmoves) in the page script"))
    if not re.search(r"\[\s*'opportunities'.*?\[\s*'working'.*?\[\s*'not_working'", markup):
        out.append(F("sowhat", "", "opportunities, working and not working are not drawn in that order"))
    cards_ = re.findall(r"<(?:section|details)\b[^>]*class=\"[^\"]*\btt-card\b[^\"]*\"[^>]*>", markup)
    last = cards_[-1] if cards_ else ""
    if not re.search(r"id=\"(trust|checking[\w-]*)\"", last):
        out.append(F("checking details", clip(last, 90), "the checking-details section (method, error rate, coverage) must be the page's last section"))
    return out


def r22(run):
    """Tabs in order, Overview first, sections in order, checking details last. Read from the built page."""
    if run.page is None:
        return na("no dashboard/index.html: build the page first")
    markup = page_markup(run)
    note = "read from the static page; the further-areas fold and the signals order are checked in the page script"
    return result(page_tabs(run, markup) + page_sections(markup), note)


def r23_overview(run):
    swot = (run.prose.get("moves") or {}).get("swot") or {}
    out = []
    for quad in ("strengths", "weaknesses", "opportunities", "threats"):
        items = swot.get(quad) or []
        if not items:
            out.append(F(f"Overview SWOT {quad}", "", "empty quadrant"))
        for i, it in enumerate(items):
            text = f"{it.get('point') or ''} {it.get('so_what') or ''}"
            if not plain(it.get("point")) or not plain(it.get("so_what")):
                out.append(F(f"prose.moves.swot.{quad}[{i}]", text, "a SWOT item needs a point and a so-what"))
            elif not CITE_RE.search(text):
                out.append(F(f"prose.moves.swot.{quad}[{i}]", text, "a SWOT item needs a citation"))
    return out


def scope_lock(run):
    """(locked items or None, config items). runstate.py locks config.scope_out into run.json at gate G1."""
    asked = {str(x) for x in run.config.get("scope_out") or []}
    meta = read_json(run.dir / "run.json")
    lock = (meta or {}).get("scope_out") if isinstance(meta, dict) else None
    return ({str(x) for x in lock.get("items") or []} if isinstance(lock, dict) else None), asked


def scoped_out(run):
    """Parts the brief left out, listed in config.scope_out (sowhat.<move type>, gtm.lenses, gtm.impact, ai.uses,
    competition.compare) and locked at G1. R23 reports them as left out instead of failing them; an entry added to
    config after G1 is not honoured."""
    locked, asked = scope_lock(run)
    return asked if locked is None else asked & locked


def r23_sowhat(run):
    groups = {"double_down": "existing strengths", "quick_win": "high impact, low effort", "budget": "budget shifts", "bet": "larger questions"}
    have = {m.get("type") for m in run.moves}
    out = scoped_out(run)
    return [F("So what groups", label, f"no move of type {t}") for t, label in groups.items()
            if t not in have and f"sowhat.{t}" not in out]


def r23_gtm(run):
    gtm = run.prose.get("gtm") or {}
    lenses = (gtm.get("insights") or {}).get("lenses") or []
    out = []
    left = scoped_out(run)
    for word, name in (("channel", "channels"), ("angle", "campaign angles"), ("offer", "offers"), ("format", "formats")):
        if "gtm.lenses" in left:
            break
        lens = next((x for x in lenses if word in f"{x.get('id')} {x.get('label')}".lower()), None)
        if not lens:
            out.append(F("Go-to-market lenses", name, "lens missing"))
            continue
        out += [F(f"Go-to-market lens {lens.get('id')}", col, "empty column") for col in ("working", "not", "open") if not lens.get(col)]
    impact = run.bundle.get("impact") or {}
    if "gtm.impact" in left:
        pass
    elif not impact.get("rows") or not (run.config.get("impact") or {}).get("views"):
        out.append(F("Go-to-market campaign impact", "", "no campaign impact view (bundle.impact rows and config.impact.views)"))
    elif not IMPACT_FLOOR_RE.search(norm(gtm.get("impact_intro"))):
        out.append(F("prose.gtm.impact_intro", gtm.get("impact_intro"), "doesn't state the smallest effect the study could detect"))
    return out


def r23_ai(run):
    ai = run.prose.get("ai")
    if not ai:
        return [F("AI tab", "", "no prose.ai")]
    parts = {str(p.get("id")): p for p in ai.get("parts") or []}
    out = [F("AI tab parts", pid, "part missing or without findings") for pid in ("offsite", "technical", "content") if not (parts.get(pid) or {}).get("findings")]
    tech = json.dumps(parts.get("technical") or {}, ensure_ascii=False).lower()
    out += [F("AI tab technical", term, f"the technical part doesn't cover {term}") for term in ("llms.txt", "json-ld") if term not in tech]
    if "ai.uses" in scoped_out(run):
        return out
    if not (ai.get("uses") or {}).get("items"):
        out.append(F("AI tab uses", "", "no inferred AI uses inside the company"))
    inferred = sum(1 for p in (run.tops.get("ai") or {}).get("points") or [] if p.get("kind") == "Inferred")
    if inferred not in (1, 2):
        out.append(F("top.ai", f"{inferred} inferred cards", "the AI top shows 1 or 2 inferred uses inside the company"))
    return out


def r23_competition(run):
    comp = run.prose.get("compare") or {}
    out = []
    if "competition.compare" in scoped_out(run):
        if len((run.config.get("competition") or {}).get("scores") or []) < 2 or not run.bundle.get("competitors"):
            out.append(F("Competition map", "", "the map needs two or more score axes and competitor profiles"))
        return out
    months = [str(pt[0]) for ser in (comp.get("series") or {}).values() if isinstance(ser, dict)
              for brand in ser.values() for pt in (brand or []) if isinstance(pt, (list, tuple)) and pt]
    years = {int(m[:4]) for m in months if re.match(r"^\d{4}", m)}
    if not years or max(years) - min(years) + 1 < 10:
        out.append(F("Competition compare", f"{len(years)} years", "no 10-year time axis (prose.compare.series)"))
    brands, indicators = comp.get("brands") or [], comp.get("indicators") or []
    if len(brands) < 3 or not any(b.get("focus") for b in brands):
        out.append(F("Competition compare brands", len(brands), "the company and at least two rivals, the company marked focus"))
    if len(indicators) < 2:
        out.append(F("Competition compare indicators", len(indicators), "at least two metrics to toggle"))
    forum = [i for i in indicators if re.search(r"(?i)reddit|forum", f"{i.get('id')} {i.get('label')}") and (comp.get("series") or {}).get(i.get("id"))]
    if not forum:
        out.append(F("Competition", "", "no Reddit or forum mentions over time"))
    if len((run.config.get("competition") or {}).get("scores") or []) < 2 or not run.bundle.get("competitors"):
        out.append(F("Competition map", "", "the map needs two or more score axes and competitor profiles"))
    return out


def r23(run):
    """Each tab carries the parts the corrections asked for, except parts the brief left out (config.scope_out)."""
    left = sorted(scoped_out(run))
    locked, asked = scope_lock(run)
    notes = [f"left out by the brief: {', '.join(left)}"] if left else []
    if locked is None and asked:
        notes.append("scope_out was not locked at G1 (runstate.py gate G1), so it is taken from config as it stands")
    late = sorted(asked - locked) if locked is not None else []
    if late:
        notes.append(f"added to scope_out after G1, so not honoured: {', '.join(late)}")
    note = "; ".join(notes)
    return result(r23_overview(run) + r23_sowhat(run) + r23_gtm(run) + r23_ai(run) + r23_competition(run), note)


def r24(run):
    """At most 8 priority moves; nothing cited in the previous draft or the synthesis files goes missing."""
    fails, notes = [], []
    if run.moves:
        top = [m.get("id") for m in run.moves if m.get("priority")]
        if len(top) > 8:
            fails.append(F("prose.moves.items", ", ".join(map(str, top)), f"{len(top)} priority moves (limit 8)"))
        notes.append("(a) the expander for the other moves is drawn by moves.js")
    if run.previous is None:
        notes.append("(b) not checked: no --previous and no verify/drafts/")
        return na("; ".join(notes)) if not run.moves else result(fails, "; ".join(notes))
    now = all_cited(run.prose) | {i for r in run.bundle.get("library") or [] for i in CITE_RE.findall(str(r.get("md") or ""))}
    excused = {r.get("id") for r in read_jsonl(run.dir / "verify" / "corrections.jsonl")
               if r.get("action") in ("corrected", "removed") and str(r.get("note") or "").strip()}
    before = {i: run.previous_name for i in all_cited(run.previous)}
    for path in sorted(run.dir.glob("0[3-9]-*.md")):
        for i in CITE_RE.findall(path.read_text(encoding="utf-8", errors="replace")):
            before.setdefault(i, path.name)
    for cid in sorted(set(before) - now - excused):
        fails.append(F(before[cid], cid, f"claim {cid} was cited in {before[cid]} and is cited nowhere in the report now"))
    notes.append(f"(b) compared with {run.previous_name} and the synthesis files 03 to 09")
    return result(fails, "; ".join(notes))


def further_section(run):
    """The Overview's where-to-look-further section as (heading, intro, rows of (source, clarifies, extra))."""
    ov = run.prose.get("overview") or {}
    if ov.get("further"):
        f = ov["further"]
        return f.get("heading"), f.get("intro"), [(r.get("source"), r.get("clarifies"), "") for r in f.get("rows") or []], "further"
    if ov.get("connections"):  # older runs: the connections list stands in, read with the same rules
        c = ov["connections"]
        return c.get("heading"), c.get("intro"), [(r.get("tool"), r.get("settles"), r.get("adds")) for r in c.get("rows") or []], "connections"
    return None


def r25(run):
    """The Overview's Where to look further: 5 or more rows, each a source and what it helps clarify, no asks."""
    found = further_section(run)
    if not found:
        return result([F("prose.overview.further", "", "the Overview has no 'Where to look further' section")])
    heading, intro, rows, key = found
    base, fails = f"prose.overview.{key}", []
    if plain(heading).rstrip(":").lower() != "where to look further":
        fails.append(F(f"{base}.heading", heading, "the section must be headed 'Where to look further'"))
    if len(rows) < 5:
        fails.append(F(f"{base}.rows", f"{len(rows)} rows", "at least 5 rows"))
    body = [(f"{base}.intro", intro)]
    for i, (source, clarifies, extra) in enumerate(rows):
        if not plain(source) or not plain(clarifies):
            fails.append(F(f"{base}.rows[{i}]", f"{source} | {clarifies}", "a row needs a source and what it helps clarify"))
        body += [(f"{base}.rows[{i}]", t) for t in (source, clarifies, extra)]
    for where, text in body:
        t = norm(text)
        fails += [F(where, t, f"'{m.group(0)}': an ask, a presumption or the reader addressed") for m in R25_ASKS.finditer(t)]
        fails += [F(where, t, f"'{m.group(0)}': a claim about the result") for m in RESULT_CLAIM.finditer(t)]
    return result(fails, "" if key == "further" else "no prose.overview.further; read prose.overview.connections instead")


def top_words(top):
    """Headline, note and cards (title, value, label, means, link label)."""
    total = words(top.get("headline")) + words(top.get("note"))
    return total + sum(words(p.get(k)) for p in top.get("points") or [] for k in CARD_FIELDS + ("goto_label",))


def r26(run):
    """Each tab top stays within 220 words and draws two of its numbers as charts (one when it has 3 cards)."""
    if not run.tops:
        return na("no tab tops")
    fails, counts = [], []
    for tab, top in run.tops.items():
        n, points = top_words(top), top.get("points") or []
        counts.append(f"{tab} {n}")
        if n > 220:
            fails.append(F(f"top.{tab}", f"{n} words", "the top runs over 220 words"))
        charts = sum(1 for p in points if (p.get("viz") or {}).get("type") in VIZ_TYPES)
        need = 2 if len(points) > 3 else 1
        if charts < need:
            fails.append(F(f"top.{tab}", f"{charts} of {len(points)} cards draw a chart", f"at least {need} cards need a chart"))
    return result(fails, "words: " + ", ".join(counts))


RULES = {
    "R02": r02, "R03": r03, "R04": r04, "R05": r05, "R11": r11, "R12": r12, "R13": r13, "R15": r15,
    "R16": r16, "R17": r17, "R18": r18, "R20": r20, "R22": r22, "R23": r23, "R24": r24, "R25": r25, "R26": r26,
}


# ---------------------------------------------------------------- main

def check(run, rules):
    rows = []
    for rule in rules:
        if str(rule.get("check")) != "code":
            continue
        fn = RULES.get(rule["id"])
        out = fn(run) if fn else result([F(rule["id"], "", "no code check for this rule in rubric_check.py")])
        rows.append({"id": rule["id"], "level": rule.get("level"), **out})
    return rows


def report(rows, out):
    for r in rows:
        first = r["failures"][0] if r["failures"] else None
        detail = f"{len(r['failures'])} items; first: {first['where']}: {first['why']}" if first else r["note"]
        print(f"{r['id']}  {str(r['level']):6}  {r['status'].upper():4}  {clip(detail, 150)}")
    fails = [r for r in rows if r["status"] == "fail"]
    must = [r["id"] for r in fails if r["level"] == "must"]
    passed = sum(1 for r in rows if r["status"] == "pass")
    print(f"{len(rows)} code rules: {passed} pass, {len(fails)} fail ({len(must)} must{': ' + ', '.join(must) if must else ''}), "
          f"{len(rows) - passed - len(fails)} n/a. Wrote {out}")
    return 1 if must else 0


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description="Check a run against the code rules of its rubric.")
    ap.add_argument("run", type=Path)
    ap.add_argument("--rubric", type=Path)
    ap.add_argument("--previous", type=Path, help="an earlier prose.json, for R24")
    args = ap.parse_args(argv)
    try:
        rules = read_rubric(args.rubric or args.run / "rubric.json")
        run = Run(args.run, args.previous)
    except Unusable as err:
        print(f"Unusable: {err}")
        return 2
    rows = check(run, rules)
    out = args.run / "verify" / "rubric-code.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return report(rows, out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
