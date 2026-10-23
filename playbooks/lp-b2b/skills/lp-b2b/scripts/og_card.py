"""Render the link preview image and favicons in the page's design.

Usage:
  python -I og_card.py <outdir> --title "Headline" --line "One line under it" \
      --bg "#1F4D42" --fg "#FFFFFF" --accent "#F6C945" --font "Schibsted Grotesk" --mark "AC"

Writes <outdir>/og.png (1200x630), favicon-32.png and favicon-180.png.
The card is laid out in HTML and rendered by Chromium, so it uses the page's web font
(loaded from Google Fonts for rendering only; nothing is published by this script).
"""
import argparse
import html
import pathlib
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("outdir")
ap.add_argument("--title", required=True)
ap.add_argument("--line", default="")
ap.add_argument("--bg", default="#111111")
ap.add_argument("--fg", default="#FFFFFF")
ap.add_argument("--accent", default="#F6C945")
ap.add_argument("--font", default="Inter Tight")
ap.add_argument("--mark", default="", help="2 to 3 letters for the favicon; defaults to the title's first letters")
a = ap.parse_args()
out = pathlib.Path(a.outdir)
out.mkdir(parents=True, exist_ok=True)
family = a.font.replace(" ", "+")
mark = a.mark or "".join(w[0] for w in a.title.split()[:2]).upper()

card = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family={family}:wght@500;800&display=swap" rel="stylesheet">
<style>
body{{margin:0;width:1200px;height:630px;background:{a.bg};color:{a.fg};font-family:'{a.font}',sans-serif;
display:flex;flex-direction:column;justify-content:center;padding:0 90px;box-sizing:border-box}}
h1{{font-size:76px;line-height:1.04;font-weight:800;margin:0 0 28px;letter-spacing:-0.02em;max-width:980px}}
p{{font-size:34px;line-height:1.3;margin:0;max-width:960px;font-weight:500}}
.bar{{width:120px;height:12px;background:{a.accent};margin-bottom:40px;border-radius:6px}}
</style></head><body><div class="bar"></div><h1>{html.escape(a.title)}</h1><p>{html.escape(a.line)}</p></body></html>"""

icon = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family={family}:wght@800&display=swap" rel="stylesheet">
<style>body{{margin:0;width:180px;height:180px;background:{a.bg};color:{a.accent};font-family:'{a.font}',sans-serif;
display:flex;align-items:center;justify-content:center;font-weight:800;font-size:{88 if len(mark) <= 2 else 64}px;letter-spacing:-0.03em}}</style>
</head><body>{html.escape(mark)}</body></html>"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.set_content(card, wait_until="networkidle")
    pg.screenshot(path=str(out / "og.png"))
    pg = b.new_page(viewport={"width": 180, "height": 180})
    pg.set_content(icon, wait_until="networkidle")
    pg.screenshot(path=str(out / "favicon-180.png"))
    b.close()

from PIL import Image  # noqa: E402  (only needed for the small favicon)
Image.open(out / "favicon-180.png").resize((32, 32), Image.LANCZOS).save(out / "favicon-32.png")
print("wrote", out / "og.png", out / "favicon-180.png", out / "favicon-32.png")
