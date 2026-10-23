"""Behaviour checks for an lp-b2b page that capture.py does not cover.

Usage: python -I check_page.py <url or file:///.../site/index.html>

Relies on the markup conventions in the lp-b2b skill's references/stage-build.md:
  a form with hidden page_version and source inputs and a spam honeypot
  (Netlify: data-netlify, netlify-honeypot and a hidden form-name input; Formspree: an input named _gotcha);
  [data-step="1"] and [data-step="2"] for a two-step form;
  [data-sticky-cta] on the mobile sticky bar.
Prints one line per check, PASS or FAIL or SKIP, and exits 0 (advisory).
"""
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1]
sep = "&" if "?" in url else "?"
results = []


def check(name, ok, detail=""):
    results.append(("PASS" if ok else "FAIL", name, detail))


VISIBLE = """sel => { const e = document.querySelector(sel); if (!e) return null;
  const s = getComputedStyle(e); const r = e.getBoundingClientRect();
  return s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity || '1') > 0.05 && r.height > 0; }"""

with sync_playwright() as p:
    b = p.chromium.launch()
    for w in (375, 390):
        ctx = b.new_context(viewport={"width": w, "height": 812}, device_scale_factor=2, is_mobile=True,
                            has_touch=True, color_scheme="light")
        pg = ctx.new_page()
        pg.goto(f"{url}{sep}ref=lp-b2b-check", wait_until="networkidle")
        pg.wait_for_timeout(400)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        check(f"{w}px no horizontal scroll", sw <= w, f"scrollWidth {sw}")
        form = pg.query_selector("form[data-netlify]") or pg.query_selector("form")
        if w == 375:
            check("request form present", form is not None)
            fields = ["page_version", "source"] + (["form-name"] if pg.query_selector("form[data-netlify]") else [])
            for field in fields:
                check(f"hidden field {field}", pg.query_selector(f"form input[type=hidden][name='{field}']") is not None)
            check("spam honeypot set", pg.evaluate(
                "() => !!document.querySelector('form[netlify-honeypot], form input[name=_gotcha], form input[name*=honeypot i], form input[name=bot-field]')"))
            src = pg.evaluate("() => (document.querySelector('input[name=source]') || {}).value || ''")
            check("source filled from ?ref=", src == "lp-b2b-check", repr(src))
            check("light-only colour scheme declared", pg.evaluate(
                "() => /light/.test((document.querySelector('meta[name=color-scheme]') || {}).content || '') && !/dark/.test((document.querySelector('meta[name=color-scheme]') || {}).content || '')"))
        if pg.query_selector('[data-step="1"]'):
            s1, s2 = pg.evaluate(VISIBLE, '[data-step="1"]'), pg.evaluate(VISIBLE, '[data-step="2"]')
            check(f"{w}px two-step form shows only step 1 at first render", bool(s1) and not s2, f"step1 {s1}, step2 {s2}")
        else:
            results.append(("SKIP", f"{w}px two-step form", "no [data-step] markup"))
        # skip what is not a tap target: inline text links, radio and checkbox inputs (their label is the target),
        # the honeypot, anything off screen or in the footer
        small = pg.evaluate("""() => {
            const f = document.querySelector('form[netlify-honeypot]'); const pot = f ? f.getAttribute('netlify-honeypot') : null;
            return [...document.querySelectorAll('a, button, summary, input:not([type=hidden]):not([type=radio]):not([type=checkbox]), select, label.choice')].filter(e => {
              const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
              if (e.tagName === 'A' && s.display === 'inline') return false;
              if (pot && e.getAttribute('name') === pot) return false;
              if (r.right <= 0 || r.left >= window.innerWidth) return false;
              return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && r.height < 44 && !e.closest('footer'); })
              .map(e => (e.tagName + ' ' + (e.textContent || e.name || '').trim()).slice(0, 40) + ' h=' + Math.round(e.getBoundingClientRect().height));
        }""")
        check(f"{w}px tap targets at least 44px (outside footer)", not small, "; ".join(small[:5]))
        bar = pg.query_selector("[data-sticky-cta]")
        if bar:
            check(f"{w}px sticky bar hidden on load", not pg.evaluate(VISIBLE, "[data-sticky-cta]"))
            pg.evaluate("window.scrollTo(0, document.documentElement.scrollHeight * 0.4)")
            pg.wait_for_timeout(500)
            check(f"{w}px sticky bar shows mid-page", bool(pg.evaluate(VISIBLE, "[data-sticky-cta]")))
            if form:
                form.scroll_into_view_if_needed()
                pg.wait_for_timeout(500)
                check(f"{w}px sticky bar hidden at the form", not pg.evaluate(VISIBLE, "[data-sticky-cta]"))
        else:
            results.append(("SKIP", f"{w}px sticky bar", "no [data-sticky-cta] markup"))
        ctx.close()
    # dark-mode phone keeps the light palette
    bgs = []
    for scheme in ("light", "dark"):
        ctx = b.new_context(viewport={"width": 390, "height": 812}, color_scheme=scheme)
        pg = ctx.new_page()
        pg.goto(url, wait_until="networkidle")
        bgs.append(pg.evaluate("getComputedStyle(document.body).backgroundColor"))
        ctx.close()
    check("dark-mode phone keeps the light palette", bgs[0] == bgs[1], f"light {bgs[0]} vs dark {bgs[1]}")
    b.close()

for status, name, detail in results:
    print(f"{status:4} {name}" + (f" ({detail})" if detail else ""))
print("summary:", ", ".join(f"{s} {sum(1 for r in results if r[0] == s)}" for s in ("PASS", "FAIL", "SKIP")))
