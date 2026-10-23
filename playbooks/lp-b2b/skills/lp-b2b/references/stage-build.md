# Stage 3: build, and stage 5: go live

Use the approved copy word for word; change it only to fix a layout-forced line break. The scripts named here live in this skill's `scripts/` folder and in the `lp-b2b-review` skill's `scripts/` folder; they need Python with Playwright (Chromium) and Pillow (`pip install playwright pillow`, then `playwright install chromium`).

## Design direction (gate G3)
1. Plan two different directions: four to six colours, type roles with real fonts, a layout sketch, the one bold element. Ground both in the subject and the buyer. Avoid the generic AI-built look (default sans fonts, purple gradients, three identical cards, everything centred) and avoid a bare white page. If the `frontend-design` skill is installed, follow it.
2. Build each as a first-screen-only mock with the real first-screen copy (`site/_directions/a.html`, `b.html`) and capture them with `capture.py` from the review skill.
3. Show both phone first screens with two lines each on what they do for a cold buyer on a phone, and your pick. Record the user's choice in `STATE.md`.

## The page
- `site/index.html`: one static file, inline CSS, a little inline JavaScript only where needed, mobile first. Declare light only (`<meta name="color-scheme" content="light only">`) unless the design was built for dark: phones in dark mode otherwise repaint parts of the page.
- Visuals show real numbers as real-looking artefacts built in HTML and CSS (stat cards, a before and after table, a calendar strip, a post card). Never fake a screenshot. Missing photos get a calm placeholder (initials) and an `<!-- ASSET: ... -->` comment.
- `site/thanks/index.html` in the same fonts, colours and theme.
- Link preview and icons: `python -I scripts/og_card.py site/assets --title "..." --line "..." --bg "#..." --fg "#..." --accent "#..." --font "..."` writes `og.png` (1200x630) and favicons.
- Head tags: title, description, `og:title`, `og:description`, `og:image` with a cache-buster (`og.png?v=1`, raise it on every image change, chat apps cache hard), `og:url`, `twitter:card` `summary_large_image`, PNG favicons, and `noindex` while the page is unlisted.

### Form (Netlify Forms shown; Formspree or Tally work the same way)
```html
<form name="request" method="POST" action="/thanks/" data-netlify="true" netlify-honeypot="company_url">
  <input type="hidden" name="form-name" value="request">
  <p hidden><label>Leave empty <input name="company_url"></label></p>
  <input type="hidden" name="page_version" value="v1">
  <input type="hidden" name="source" value="">  <!-- a few lines of JS fill it from ?ref= or utm_source -->
  ...
</form>
```
- Raise `page_version` on every release, so you can count requests per version.
- Two steps only with more than four fields; mark them `data-step="1"` and `data-step="2"`. If a container uses `display:flex` or `grid`, add `[hidden]{display:none !important}`: otherwise every field shows at once (this shipped live once, unnoticed, for three versions).
- A mobile sticky button carries `data-sticky-cta`, appears only after the main button scrolls out of view and hides while the form is on screen; a bar visible on load covered the guarantee and the price line once.

### Check before review
1. `python -I <lp-b2b-review>/scripts/capture.py file:///<path>/site/index.html review/capture-v1/` and fix every warning (images not loaded, elements past the screen edge, text covered by a fixed bar). Look at every screenshot.
2. `python -I scripts/check_page.py file:///<path>/site/index.html` and fix every FAIL (form fields, source, two-step first render, sticky bar, tap targets, dark-mode phone).
3. Write `site/build-report.md`: the checklist in `golive-checklist.md`, each item marked done (with evidence), at deploy, or needs the user (with what).
4. Run the `lp-b2b-review` skill in full mode. It brings the user to G4.

## Go live (gate G5, only after G4)
1. Work through `golive-checklist.md`; show the user every "needs you" item before the push, not after.
2. Publish only the page files (index.html, thanks/, assets/). Iterate on a preview branch where your host offers free previews; publish once per approved release, with a rollback point.
3. Ask for an explicit yes to publish. Send one test request through the live form and confirm it arrives. Test the link preview in a chat app with a fresh `?v=` and in LinkedIn's Post Inspector.
