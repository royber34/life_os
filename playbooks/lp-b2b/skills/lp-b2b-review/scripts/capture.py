"""Capture a page the way reviewers need it.

Usage: python -I capture.py <url or file:///path/index.html> <outdir>

Writes to <outdir>:
  desktop-first-screen.png, desktop-tile-NN.png   (1440 wide)
  mobile-first-screen.png, mobile-tile-NN.png     (390 wide, touch, DPR 2)
  page-text.txt         all visible text, collapsed <details> opened
  link-preview-meta.txt title, description, og and twitter tags
  og.png                the og:image rendered at 1200x630, when the page has one
Prints warnings that each caught a real defect in past builds:
  images that did not render (lazy loading), elements past the screen edge outside
  scroll containers, fixed or sticky bars covering text in the first screen.
"""
import re
import sys
import pathlib
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

url, out = sys.argv[1], pathlib.Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
TILE = 2400  # tile height in CSS px; Chromium repeats the top of very tall single shots
NL = chr(10)

LOAD_ALL_IMAGES = "() => document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')"
BROKEN_IMAGES = "() => [...document.images].filter(i => i.naturalWidth === 0).map(i => i.getAttribute('src'))"
PAST_EDGE = """() => {
  const inScroller = e => { for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) {
    if (/(auto|scroll)/.test(getComputedStyle(p).overflowX)) return true; } return false; };
  return [...document.querySelectorAll('body *')].filter(e => {
    const r = e.getBoundingClientRect();
    return r.width > 0 && (r.right > window.innerWidth + 1 || r.left < -1) && !inScroller(e);
  }).slice(0, 10).map(e => e.tagName + '.' + (typeof e.className === 'string' ? e.className : ''));
}"""
COVERED_TEXT = """() => {
  const bars = [...document.querySelectorAll('body *')].filter(e => {
    const s = getComputedStyle(e); const r = e.getBoundingClientRect();
    return (s.position === 'fixed' || s.position === 'sticky') && r.height > 0 && r.top < window.innerHeight && r.bottom > 0
      && s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity || '1') > 0.05;
  });
  const texts = [...document.querySelectorAll('p, li, h1, h2, h3, small, span, a, label, strong')].filter(e => {
    const r = e.getBoundingClientRect(); return e.textContent.trim().length > 3 && r.height > 0 && r.top < window.innerHeight && r.bottom > 0;
  });
  const hits = [];
  for (const b of bars) { const br = b.getBoundingClientRect();
    for (const t of texts) { if (b.contains(t) || t.contains(b)) continue; const tr = t.getBoundingClientRect();
      const overlap = Math.min(br.bottom, tr.bottom) - Math.max(br.top, tr.top);
      if (overlap > 4 && Math.min(br.right, tr.right) - Math.max(br.left, tr.left) > 4) hits.push(t.textContent.trim().slice(0, 60)); } }
  return [...new Set(hits)].slice(0, 6);
}"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    og_url = None
    for name, w, h, mobile in [("desktop", 1440, 900, False), ("mobile", 390, 844, True)]:
        ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=2 if mobile else 1,
                                  is_mobile=mobile, has_touch=mobile, color_scheme="light")
        pg = ctx.new_page()
        pg.goto(url, wait_until="networkidle")
        # first screen exactly as a visitor sees it, before any scrolling changes sticky bars
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(out / f"{name}-first-screen.png"))
        covered = pg.evaluate(COVERED_TEXT)
        # load lazy images: switch to eager, scroll through, wait until every image is complete
        pg.evaluate(LOAD_ALL_IMAGES)
        height = pg.evaluate("document.documentElement.scrollHeight")
        for y in range(0, height, h // 2):
            pg.evaluate(f"window.scrollTo(0, {y})")
            pg.wait_for_timeout(120)
        pg.evaluate("window.scrollTo(0, 0)")
        try:
            pg.wait_for_function("() => [...document.images].every(i => i.complete)", timeout=15000)
        except Exception:
            print(name, "WARNING: some images still loading after 15 s")
        pg.wait_for_timeout(500)
        total = pg.evaluate("document.documentElement.scrollHeight")
        n = 0
        for y in range(0, total, TILE):
            n += 1
            pg.screenshot(path=str(out / f"{name}-tile-{n:02d}.png"), full_page=True,
                          clip={"x": 0, "y": y, "width": w, "height": min(TILE, total - y)})
        print(f"{name}: height {total}px, {n} tiles")
        broken = pg.evaluate(BROKEN_IMAGES)
        if broken:
            print(f"{name} WARNING images not rendered: {broken}")
        wide = pg.evaluate(PAST_EDGE)
        if wide:
            print(f"{name} WARNING elements past the screen edge: {wide}")
        if covered:
            print(f"{name} WARNING text covered by a fixed or sticky bar in the first screen: {covered}")
        if name == "desktop":
            pg.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
            (out / "page-text.txt").write_text(pg.inner_text("body"), encoding="utf-8")
            # read the head through the DOM, so attribute order and quoting do not matter
            meta = pg.evaluate("""() => [...document.querySelectorAll('meta')].map(m => [m.getAttribute('property') || m.getAttribute('name') || '', m.getAttribute('content') || ''])
                .filter(([k]) => k.startsWith('og:') || k.startsWith('twitter:') || k === 'description')""")
            title = pg.title().strip()
            lines = [f"title: {title}"] + [f"{k}: {v}" for k, v in meta]
            if not any(k == "og:title" for k, _ in meta):
                lines.append("(no og:title: the share card falls back to the page title)")
            (out / "link-preview-meta.txt").write_text(NL.join(lines), encoding="utf-8")
            og = [v for k, v in meta if k == "og:image"]
            if og:
                og_url = urljoin(pg.url, og[0])
        ctx.close()
    if og_url:
        try:
            pg = browser.new_page(viewport={"width": 1200, "height": 630})
            pg.goto(og_url)
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(out / "og.png"))
            print("og image rendered to og.png")
        except Exception as e:  # a placeholder domain before deploy is normal
            print("og image not reachable:", og_url, "|", type(e).__name__)
    else:
        print("WARNING no og:image tag: the link preview will have no image")
    browser.close()
