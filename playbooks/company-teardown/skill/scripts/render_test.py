#!/usr/bin/env python3
"""Open a built dashboard in Chromium and check that it renders and behaves.

    python render_test.py <index.html> <outdir>

Writes <outdir>/render-report.md and screenshots, and exits non-zero on any failure.
Needs Playwright with Chromium installed.
"""
import json
import math
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

TOLERANCE = 0.01  # SVG marks against bundle counts: within 1%, at least 1 mark.
WIDE, PHONE = 1440, 390
CHART_FLOOR = 900  # A chart first shown at 1440 wide must fill the page, well above the 640 minimum.
TILE_HEIGHT = 2000
MAX_TILES = 14


class Report:
    def __init__(self):
        self.rows = []

    def check(self, name, ok, detail=""):
        self.rows.append((name, bool(ok), str(detail)))
        return ok

    def near(self, name, got, want):
        allowed = max(1, math.ceil(want * TOLERANCE))
        self.check(name, abs(got - want) <= allowed, f"got {got}, expected {want}, tolerance {allowed}")

    def exact(self, name, got, want):
        self.check(name, got == want, f"got {got}, expected {want}")

    @property
    def failed(self):
        return [r for r in self.rows if not r[1]]


def settle(page, ms=60):
    page.evaluate("() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))")
    page.wait_for_timeout(ms)


def click_tab(page, tab):
    page.click(f'.tt-tab[data-tab="{tab}"]')
    settle(page)


def count(page, selector):
    return page.locator(selector).count()


def type_search(page, key, text):
    page.fill(f'input[data-q="{key}"]', text)
    page.wait_for_timeout(350)
    settle(page)


def select(page, bind, value):
    page.select_option(f'select[data-bind="{bind}"]', value)
    settle(page)


def num(page, selector):
    return int(page.locator(selector).first.inner_text().replace(",", ""))


def chart_width(page, selector):
    return page.evaluate(f"() => {{ const e = document.querySelector('{selector}'); return e ? e.getBoundingClientRect().width : 0; }}")


def shot(page, outdir, name):
    height = page.evaluate("() => document.documentElement.scrollHeight")
    width = page.viewport_size["width"]
    if height <= TILE_HEIGHT:
        page.screenshot(path=str(outdir / f"{name}.png"), full_page=True)
        return
    tiles = min(MAX_TILES, math.ceil(height / TILE_HEIGHT))
    for i in range(tiles):
        clip = {"x": 0, "y": i * TILE_HEIGHT, "width": width, "height": min(TILE_HEIGHT, height - i * TILE_HEIGHT)}
        page.screenshot(path=str(outdir / f"{name}-{i + 1}.png"), full_page=True, clip=clip)


def tab_checks(page, rep, bundle):
    meta, cfg = bundle["meta"], bundle["config"]
    counts = meta["counts"]
    has_all = any(p["id"] == "all" for p in cfg["periods"])

    tabs = page.eval_on_selector_all(".tt-tab", "els => els.map((e) => e.dataset.tab)")
    want_tabs = ["overview", "sowhat", "timeline", "gtm"] + (["ai"] if bundle["prose"].get("ai") else []) + ["competition"] + (["market"] if cfg.get("market") else []) + ["deepdive"]
    rep.exact("Tabs in the agreed order", tabs, want_tabs)
    moves = bundle["prose"].get("moves")
    if moves:
        rep.exact("Page opens on the overview", page.eval_on_selector('.tt-tab[aria-selected="true"]', "e => e.dataset.tab"), "overview")
        click_tab(page, "sowhat")
        rep.exact("Moves: SWOT quadrants", count(page, ".tt-swot"), 4)
        rep.exact("Moves: SWOT rows", count(page, ".tt-swot-row"), sum(len(v) for v in moves["swot"].values()))
        rep.exact("Moves: crossings", count(page, ".tt-cross"), len(moves.get("crossings") or []))
        rep.exact("Moves: rows", count(page, ".tt-mrow.tt-move"), len(moves["items"]))
        rep.exact("Moves: headline findings", count(page, ".tt-fact"), len(moves["headlines"]))
        rep.exact("Moves: decision rules", count(page, '[data-draw="movesrules"] .tt-rules tbody tr'), len(moves["rules"]))
        rep.exact("Moves: data request rows", count(page, '[data-draw="movesrequest"] tbody tr'), len(moves["data_request"]))
        rep.exact("Moves: matrix dots", count(page, ".tt-mdot"), len(moves["items"]))
        top = [m for m in moves["items"] if m.get("priority")]
        rep.exact("Moves: opens on the main areas", page.locator(".tt-mrow.tt-move:visible").count(), len(top))
        others = len(moves["items"]) - len(top)
        rep.exact("Moves: further moves are in the fold", count(page, ".tt-allmoves .tt-mrow.tt-move"), others)
        rep.check("Moves: further moves fold is visible", page.locator(".tt-allmoves > summary").is_visible())
        rep.check("Moves: further moves fold names its count", f"({others})" in page.locator(".tt-allmoves > summary").inner_text())
        page.locator(".tt-allmoves > summary").click()
        rep.exact("Moves: opening the fold shows every area", page.locator(".tt-mrow.tt-move:visible").count(), len(moves["items"]))
        page.get_by_role("button", name="Most impact for the effort").click()
        rep.exact("Moves: sorting keeps every row", page.locator(".tt-mrow.tt-move:visible").count(), len(moves["items"]))
        page.get_by_role("button", name="Most impact for the effort").click()
        page.locator(".tt-allmoves > summary").click()
        hidden_id = next(m["id"] for m in moves["items"] if not m.get("priority"))
        page.get_by_role("button", name="Impact and effort chart").click()
        page.locator(f'.tt-mdot[title^="{[m["id"] for m in moves["items"]].index(hidden_id) + 1}."]').click()
        page.wait_for_timeout(200)
        rep.check("Moves: jumping to a folded area opens it", page.locator(f"#move-{hidden_id} .tt-mrow-body").is_visible())
        page.locator(".tt-allmoves > summary").click()
        rep.exact("So what: signals panel holds every item", count(page, '[data-draw="sowsignals"] .tt-srow'), len(moves["opportunities"]) + len(moves["working"]) + len(moves["not_working"]))
        rep.exact("So what: opens on opportunities", page.locator('[data-draw="sowsignals"] .tt-srow:visible').count(), len(moves["opportunities"]))
    conn = (bundle["prose"].get("overview") or {}).get("connections")
    if conn:
        click_tab(page, "overview")
        rep.exact("Overview: data connections", count(page, ".tt-connections tbody tr"), len(conn["rows"]))
    ins = (bundle["prose"].get("gtm") or {}).get("insights")
    if ins:
        total = sum(len(l.get(k) or []) for l in ins["lenses"] for k in ("working", "not", "open"))
        click_tab(page, "gtm")
        rep.exact("GTM: insight cards", count(page, '[data-draw="gtminsights"] .tt-insight'), total)
    if bundle.get("impact"):
        click_tab(page, "gtm")
        rep.check("GTM: impact types table", count(page, ".tt-impact-types tbody tr") > 0, count(page, ".tt-impact-types tbody tr"))
        rep.check("GTM: impact table has a row per campaign", count(page, ".tt-impact-table tbody tr") > 0, count(page, ".tt-impact-table tbody tr"))
        rep.check("GTM: campaigns marked on the chart", count(page, ".tt-impact-mark") > 0, count(page, ".tt-impact-mark"))
    rep.exact("So-what bands shown", count(page, ".tt-band"), len([k for k, v in (bundle["prose"].get("bands") or {}).items() if v and k not in (bundle["prose"].get("top") or {})]))
    click_tab(page, "overview")

    ai = bundle["prose"].get("ai")
    if ai:
        click_tab(page, "ai")
        rep.exact("AI: parts", count(page, '[data-draw="aiparts"] .tt-ai-part'), len(ai.get("parts") or []) + (1 if ai.get("uses") else 0))
        rep.exact("AI: findings", count(page, '[data-draw="aiparts"] .tt-ai-find'), sum(len(q.get("findings") or []) for q in ai.get("parts") or []))
        rep.exact("AI: use areas", count(page, '[data-draw="aiparts"] .tt-ai-use'), len((ai.get("uses") or {}).get("items") or []))
        click_tab(page, "overview")
    for tab, tp in (bundle["prose"].get("top") or {}).items():
        click_tab(page, tab)
        rep.exact(f"Top of {tab}: key points", count(page, f'[data-band="{tab}"] .tt-top-tile'), len(tp.get("points") or []))
    click_tab(page, "overview")
    cmp = bundle["prose"].get("compare")
    if cmp:
        click_tab(page, "competition")
        on = [x for x in cmp["indicators"] if x.get("on")]
        rep.exact("Compare: opens on the default charts", count(page, ".tt-cmp-panel"), len(on))
        off = next((x for x in cmp["indicators"] if not x.get("on")), None)
        if off:
            page.locator(f'.tt-cmp .tt-chip[data-id="{off["id"]}"]').click()
            rep.exact("Compare: clicking adds a chart", count(page, ".tt-cmp-panel"), len(on) + 1)
            page.locator(f'.tt-cmp .tt-chip[data-id="{off["id"]}"]').click()
            rep.exact("Compare: clicking again removes it", count(page, ".tt-cmp-panel"), len(on))
        lines = count(page, ".tt-cmp-panel:first-child .tt-cmp-line")
        rival = next(b for b in cmp["brands"] if not b.get("focus") and b.get("on") is not False)
        page.locator(f'.tt-cmp-brand[data-id="{rival["id"]}"]').click()
        rep.check("Compare: clicking a brand removes its line", count(page, ".tt-cmp-panel:first-child .tt-cmp-line") == lines - 1, lines)
        page.locator(f'.tt-cmp-brand[data-id="{rival["id"]}"]').click()
        click_tab(page, "overview")
    raw = []
    for tab in page.eval_on_selector_all(".tt-tab", "els => els.map((e) => e.dataset.tab)"):
        click_tab(page, tab)
        if "{{" in page.locator(f'[data-page="{tab}"]').inner_text():
            raw.append(tab)
    click_tab(page, "overview")
    rep.exact("No raw tokens on any tab", raw, [])
    rep.exact("Overview: KPI cards", count(page, '[data-draw="kpis"] .tt-kpi'), len(cfg.get("kpis") or []))
    rep.exact("Overview: summary cards", count(page, '[data-draw="summary"] .tt-card'), len(bundle["prose"]["overview"]["summary"]))
    rep.check("Overview: nav cards present", count(page, ".tt-navcard") >= 5, count(page, ".tt-navcard"))
    if bundle.get("verification"):
        rep.check("Overview: verification block", count(page, ".tt-verify:not(.tt-verify-none)") == 1, bundle["verification"].get("label"))
    else:
        rep.check("Overview: 'Not verified yet' shown", "Not verified yet" in page.locator(".tt-verify-none").inner_text())

    click_tab(page, "sowhat")
    items = bundle["prose"].get("so_what") or []
    rep.exact("So what: cards", count(page, '[data-draw="sowhat"] .tt-ins') + count(page, '[data-draw="sowhat"] section.tt-card'), len(items))

    click_tab(page, "timeline")
    w = chart_width(page, '[data-draw="swim"] svg')
    rep.check("Timeline: chart width on first show above floor", w > CHART_FLOOR, f"{w:.0f}px, floor {CHART_FLOOR}px")
    shown = num(page, '[data-draw="count"]')
    rep.exact("Timeline: table rows match the count text", count(page, '[data-draw="rows"] tr'), shown)
    rep.near("Timeline: marks match the rows", count(page, '[data-draw="swim"] .tt-mark'), shown)
    rep.exact("Timeline: metric cards at defaults", page.evaluate("() => document.querySelectorAll('[data-mcard]:not([hidden])').length"), len([c for c in cfg.get("metric_cards") or [] if c.get("default")]))
    if has_all:
        select(page, "tperiod", "all")
        rep.exact("Timeline: period all shows every event", count(page, '[data-draw="rows"] tr'), counts["events"])
        rep.near("Timeline: period all marks", count(page, '[data-draw="swim"] .tt-mark'), counts["events"])
        select(page, "tperiod", cfg["default_period"])

    click_tab(page, "gtm")
    if counts["gtm"]:
        w = chart_width(page, '[data-draw="gtmchart"] svg')
        rep.check("GTM: chart width on first show above floor", w > CHART_FLOOR, f"{w:.0f}px, floor {CHART_FLOOR}px")
    shown = num(page, '[data-draw="gtmcount"]')
    rep.exact("GTM: table rows match the count text", count(page, '[data-draw="gtmrows"] tr'), shown)
    rep.near("GTM: bubbles match the rows", count(page, '[data-draw="gtmchart"] .tt-mark'), shown)
    if has_all:
        select(page, "gperiod", "all")
        rep.exact("GTM: period all shows every action", count(page, '[data-draw="gtmrows"] tr'), counts["gtm"])
        rep.near("GTM: period all bubbles", count(page, '[data-draw="gtmchart"] .tt-mark'), counts["gtm"])
        select(page, "gperiod", cfg["default_period"])

    click_tab(page, "competition")
    comp = cfg.get("competition") or {}
    n = counts["competitors"]
    if n:
        w = chart_width(page, '[data-draw="compmap"] svg')
        rep.check("Competition: chart width on first show above floor", w > CHART_FLOOR, f"{w:.0f}px, floor {CHART_FLOOR}px")
        rep.exact("Competition: scatter marks", count(page, '[data-draw="compmap"] .tt-mark'), n)
        rep.exact("Competition: players table rows", count(page, '[data-draw="comprows"] tr'), n)
        rep.exact("Competition: threat by partner chips", count(page, '[data-draw="compquad"] .tt-chip'), n - (1 if comp.get("self") else 0))
        comps = len(comp.get("components") or [])
        if comps:
            rep.exact("Competition: coverage cells", count(page, '[data-draw="compmatrix"] .tt-cell'), n * (comps + 2))
        else:
            rep.check("Competition: coverage hidden with no components", not page.locator('[data-needs="components"]').is_visible())
    else:
        rep.check("Competition: empty state shown", page.locator('[data-hide-unless-empty="competitors"]').is_visible())
    if counts["landscape"]:
        rep.exact("Competition: long list rows", count(page, '[data-draw="landrows"] tr'), counts["landscape"])
    else:
        rep.check("Competition: long list hidden when empty", not page.locator('[data-needs="landscape"]').is_visible())

    if cfg.get("market"):
        click_tab(page, "market")
        m = cfg["market"]
        rep.exact("Market: supply rows", count(page, '[data-draw="supplyrows"] tr'), len(m["supply"]))
        rep.exact("Market: demand bars", count(page, '[data-draw="demandbars"] .tt-mark'), len(m["demand"]))
        rep.check("Market: both matrices drawn", count(page, '[data-draw="supplymatrix"] .tt-cell') > 0 and count(page, '[data-draw="sdmatrix"] .tt-cell') > 0)
        page.locator('[data-draw="demandbars"] .tt-mark').first.click(force=True)
        settle(page)
        rep.check("Market: segment selection opens detail", count(page, '[data-draw="demanddetail"] h3') == 1)
        page.click('[data-act="market-clear"]')
        settle(page)

    click_tab(page, "deepdive")
    if counts["library_docs"]:
        rep.exact("Deep dive: doc list", count(page, ".tt-ldoc"), counts["library_docs"])
        rep.check("Deep dive: reader shows a document", count(page, ".tt-lbody .tt-lh") > 0)
        word = bundle["library"][0]["md"].split()[1].strip("#*:,.") or "the"
        type_search(page, "lq", word)
        rep.check("Deep dive: search finds sections", count(page, ".tt-hit") > 0, f"query {word!r}: {count(page, '.tt-hit')} hits")
        page.click(".tt-hit")
        settle(page)
        rep.check("Deep dive: a hit opens the reader", count(page, ".tt-lbody .tt-lh") > 0)
    else:
        rep.check("Deep dive: empty state shown", "No documents" in page.locator('[data-draw="libdocs"]').inner_text())
    page.click('.tt-tab[data-tab="timeline"]')
    settle(page)
    page.click('[data-page="timeline"] [data-act="reset"]')
    settle(page)


def interaction_checks(page, rep, bundle):
    counts = bundle["meta"]["counts"]
    click_tab(page, "gtm")
    gtm_rows = count(page, '[data-draw="gtmrows"] tr')
    gtm_first = page.locator('[data-draw="gtmrows"] tr td').first.inner_text() if gtm_rows else ""
    click_tab(page, "competition")
    comp_n = num(page, '[data-draw="compcount"]')
    click_tab(page, "timeline")
    base = count(page, '[data-draw="rows"] tr')
    pressed = page.eval_on_selector_all(".tt-chip[aria-pressed='true']", "els => els.length")

    # Sort stays per tab.
    page.click('[data-sortable="t"] button')
    settle(page)
    dates = page.eval_on_selector_all('[data-draw="rows"] tr td:first-child', "els => els.map((e) => e.textContent)")
    rep.check("Timeline: sort flips to newest first", dates == sorted(dates, reverse=True), f"{dates[0] if dates else ''} first")
    # Search stays per tab.
    probe = next((w for w in bundle["events"][len(bundle["events"]) // 2]["title"].split() if len(w) > 4), "a")
    type_search(page, "tq", probe)
    after = count(page, '[data-draw="rows"] tr')
    rep.check("Timeline: search narrows the rows", after < base, f"{base} to {after}, query {probe!r}")
    click_tab(page, "gtm")
    rep.exact("Timeline search leaves GTM rows unchanged", count(page, '[data-draw="gtmrows"] tr'), gtm_rows)
    if gtm_rows:
        rep.exact("Timeline sort leaves GTM order unchanged", page.locator('[data-draw="gtmrows"] tr td').first.inner_text(), gtm_first)
    # Confidence stays per tab.
    click_tab(page, "timeline")
    select(page, "tconf", "high")
    click_tab(page, "competition")
    rep.exact("Timeline confidence leaves Competition count unchanged", num(page, '[data-draw="compcount"]'), comp_n)
    # Zoom stays per tab.
    click_tab(page, "timeline")
    page.locator('[data-draw="zoomstrip"][data-scope="t"] svg').scroll_into_view_if_needed()
    box = page.locator('[data-draw="zoomstrip"][data-scope="t"] svg').bounding_box()
    y = box["y"] + 12
    page.mouse.move(box["x"] + box["width"] * 0.6, y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * 0.9, y, steps=6)
    page.mouse.up()
    settle(page)
    zoomed = page.evaluate("() => dash.params().tfrom")
    rep.check("Timeline: brush on the zoom strip sets a range", bool(zoomed), zoomed)
    rep.check("Timeline: Reset zoom appears", page.locator('[data-page="timeline"] [data-act="zoom-reset"]').is_visible())
    click_tab(page, "gtm")
    rep.exact("Timeline zoom leaves GTM rows unchanged", count(page, '[data-draw="gtmrows"] tr'), gtm_rows)
    # Reset all.
    click_tab(page, "timeline")
    page.click('[data-act="lanes-none"]')
    settle(page)
    page.click('[data-page="timeline"] [data-act="reset"]')
    settle(page)
    same = page.evaluate("""() => {
      const p = dash.params(), d = dash.defaults();
      return Object.keys(d).filter((k) => k !== 'tab' && JSON.stringify(p[k]) !== JSON.stringify(d[k]));
    }""")
    rep.check("Reset all restores every default", not same, f"differs: {same}")
    rep.exact("Reset all restores the Timeline rows", count(page, '[data-draw="rows"] tr'), base)
    rep.exact("Reset all restores the pressed chips", page.eval_on_selector_all(".tt-chip[aria-pressed='true']", "els => els.length"), pressed)
    rep.exact("Reset all clears the search box", page.input_value('input[data-q="tq"]'), "")
    # Selecting events, Previous and Next.
    if base > 1:
        page.locator('[data-draw="rows"] tr').nth(0).click()
        settle(page)
        title = page.locator('[data-draw="detail"] h3').inner_text()
        rep.check("Timeline: row click opens detail", bool(title), title[:50])
        page.locator('[data-draw="detail"] .tt-btn', has_text="Next").click()
        settle(page)
        rep.check("Timeline: Next moves the detail", page.locator('[data-draw="detail"] h3').inner_text() != title or count(page, '[data-draw="rows"] tr.is-sel') == 1)
        page.locator('[data-draw="detail"] .tt-btn', has_text="Clear selection").click()
        settle(page)
    cards = bundle["config"].get("metric_cards") or []
    if cards:
        on = page.evaluate("() => document.querySelectorAll('[data-mcard]:not([hidden])').length")
        page.click(f'.tt-chip[data-metric="{cards[0]["id"]}"]')
        settle(page)
        now = page.evaluate("() => document.querySelectorAll('[data-mcard]:not([hidden])').length")
        rep.check("Timeline: metric chip toggles only one card", abs(now - on) == 1, f"{on} to {now}")
        page.click('[data-page="timeline"] [data-act="reset"]')
        settle(page)
    if counts["gtm"]:
        click_tab(page, "gtm")
        page.locator('[data-draw="gtmchart"] .tt-mark').first.click(force=True)
        settle(page)
        rep.check("GTM: bubble click opens selected action", count(page, '[data-draw="gtmdetail"] h3') == 1)
        curves = bundle["config"].get("response_curves") or []
        if curves:
            rep.check("GTM: response curves drawn", count(page, '[data-draw="gtmlift"] svg path') > 0)
        page.click('[data-page="gtm"] [data-act="reset"]')
        settle(page)
    if counts["competitors"]:
        click_tab(page, "competition")
        page.locator('[data-draw="compmap"] .tt-mark').first.click(force=True)
        settle(page)
        rep.check("Competition: dot click opens the profile", count(page, '[data-draw="compdetail"] h3') == 1)
        scores = bundle["config"]["competition"]["scores"]
        if len(scores) > 2:
            select(page, "cx", scores[2]["id"])
            rep.exact("Competition: axis change keeps all marks", count(page, '[data-draw="compmap"] .tt-mark'), counts["competitors"])
        select(page, "cconf", "high")
        high = sum(1 for r in bundle["competitors"] if r.get("confidence") == "high")
        rep.exact("Competition: own confidence filter works", num(page, '[data-draw="compcount"]'), high)
        page.click('[data-act="comp-clear"]')
        settle(page)
        select(page, "cx", bundle["config"]["competition"]["default_x"])

    prose_text = json.dumps(bundle["prose"])
    if bundle["claims"] and "[c:" in prose_text:
        click_tab(page, "overview")
        click_tab(page, "sowhat")
        click_tab(page, "overview")
        cites = page.locator(".tt-cite:visible").count()
        if not cites:
            click_tab(page, "sowhat")
            cites = page.locator(".tt-cite:visible").count()
        rep.check("Citations: superscript links rendered", cites > 0, cites)
        if cites:
            page.locator(".tt-cite:visible").first.hover()
            settle(page)
            pop = page.locator(".tt-cite-pop").inner_text() if count(page, ".tt-cite-pop") else ""
            rep.check("Citations: hover shows source and status", "Verification:" in pop, pop[:90].replace("\n", " "))
            page.mouse.move(0, 0)
            page.mouse.click(1, 1)


def run_all_tabs(page, fn):
    tabs = page.eval_on_selector_all(".tt-tab", "els => els.map((e) => e.dataset.tab)")
    for t in tabs:
        click_tab(page, t)
        fn(t)


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    html = Path(argv[1]).resolve()
    outdir = Path(argv[2]).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    rep = Report()
    errors, failed, external = [], [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": WIDE, "height": 900}, color_scheme="light")
        page = ctx.new_page()
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("requestfailed", lambda r: failed.append(r.url))
        page.on("request", lambda r: external.append(r.url) if not r.url.startswith(("file:", "data:", "about:")) else None)
        page.goto(html.as_uri())
        page.wait_for_selector(".tt-tab")
        settle(page, 200)
        bundle = page.evaluate("() => dash.bundle")
        tab_checks(page, rep, bundle)
        interaction_checks(page, rep, bundle)

        # Visit every tab, then look for missing markers anywhere on the page.
        markers = []
        run_all_tabs(page, lambda t: markers.extend(page.eval_on_selector_all(".tt-missing", "els => els.map((e) => e.textContent)")))
        rep.check("No missing markers on any tab", not markers, markers[:5])

        page.click('.tt-tab[data-tab="overview"]')
        settle(page)
        run_all_tabs(page, lambda t: shot(page, outdir, f"{t}-{WIDE}"))

        # Phone: a fresh load, so first-show sizing is real at this width too.
        phone = browser.new_context(viewport={"width": PHONE, "height": 844}, color_scheme="light", has_touch=True, is_mobile=True)
        pp = phone.new_page()
        pp.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pp.on("pageerror", lambda e: errors.append(str(e)))
        pp.goto(html.as_uri())
        pp.wait_for_selector(".tt-tab")
        settle(pp, 200)
        over = []
        def phone_tab(t):
            sw = pp.evaluate("() => document.documentElement.scrollWidth")
            iw = pp.evaluate("() => document.documentElement.clientWidth")
            if sw > iw + 1:
                over.append(f"{t}: {sw} wide in {iw}")
            shot(pp, outdir, f"{t}-{PHONE}")
        run_all_tabs(pp, phone_tab)
        rep.check("Phone width: no horizontal page scroll on any tab", not over, over or f"checked at {PHONE}px")
        phone.close()

        # Dark theme: a quick look that the tokens switch.
        dark = browser.new_context(viewport={"width": WIDE, "height": 900}, color_scheme="dark")
        dp = dark.new_page()
        dp.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        dp.goto(html.as_uri())
        dp.wait_for_selector(".tt-tab")
        settle(dp, 200)
        bg = dp.evaluate("() => getComputedStyle(document.body).backgroundColor")
        rep.check("Dark theme: tokens switch", bg != "rgb(250, 249, 245)", bg)
        click_tab(dp, "timeline")
        shot(dp, outdir, f"timeline-{WIDE}-dark")
        dark.close()
        browser.close()

    rep.check("No console errors", not errors, errors[:5])
    rep.check("No failed requests", not failed, failed[:5])
    rep.check("No network requests to any other host", not external, external[:5])

    lines = ["# Render report", "", f"Tolerance for SVG marks against bundle counts: {TOLERANCE:.0%}, at least 1 mark. Everything else is exact.", ""]
    lines += [f"Result: **{'FAIL' if rep.failed else 'PASS'}**, {len(rep.rows) - len(rep.failed)} of {len(rep.rows)} checks passed.", "", "| Check | Result | Detail |", "|---|---|---|"]
    for name, ok, detail in rep.rows:
        lines.append(f"| {name} | {'pass' if ok else 'FAIL'} | {detail.replace('|', '/')[:160]} |")
    report = outdir / "render-report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(rep.rows) - len(rep.failed)} of {len(rep.rows)} checks passed.")
    for name, _, detail in rep.failed:
        print(f"FAIL {name}: {detail[:200]}")
    print(f"Report: {report}")
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
