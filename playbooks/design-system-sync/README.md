# Design System Sync: what breaks when you hand your components to a design agent

Notes from syncing a React + Tailwind design system into [Claude Design](https://claude.ai/design), where the design agent builds screens out of your real components instead of generic ones.

The sync itself is one command and it mostly works. What surprised me was the failure mode: everything reports success, the component cards look perfect in the picker, and the designs the agent produces are still subtly wrong. Wrong fonts. Unstyled spacing. Colours from your own brand doc that do nothing.

All three causes were the same shape, and I think they generalize to any component library you hand to an agent. Sharing them in case they save someone the debugging.

---

## The mental model that explains all of it

A design the agent builds receives exactly two things:

1. Your compiled JS bundle
2. `styles.css` **and its transitive `@import` closure**

That is the whole environment. No host page. No build step. No Tailwind running. No `index.html` you wrote.

Almost every fidelity bug I hit was me assuming something else came along for the ride. Once I started asking "is this reachable from `styles.css`, or is it in the bundle?" before assuming anything worked, the failures became predictable.

The dangerous part is that violations are **silent**. Nothing errors. The component renders, and the wrongness only shows up as design output that looks a bit off.

---

## Trap 1: your fonts do not ship

Most projects load webfonts with a `<link>` in `index.html`. That file never reaches the design environment, so the fonts never load and everything silently falls back to the next family in the stack.

If your brand rests on a typeface pairing, this quietly removes it from every design the agent will ever produce.

**Check it.** Look for `@font-face` or a font-host `@import` in the stylesheet the sync actually ships. If the only reference is in your HTML, you have this bug:

```bash
grep -l "@font-face\|fonts.googleapis" dist/*.css || echo "no fonts in the shipped CSS"
```

**Fix it.** Move the font loading into the stylesheet itself, at the top of your CSS entry:

```css
@import url('https://fonts.googleapis.com/css2?family=...&display=swap');

@tailwind base;
```

Now the fonts travel with the compiled CSS, so anything importing it gets them, including consuming apps. Self-hosting the woff2 files works too and removes the network dependency, which matters if the render environment ever blocks the font host.

**Verify it properly.** `document.fonts.check()` is a trap here: it tests one exact size and weight pair, so it returns `false` for a font that is demonstrably rendering. Read the loaded set instead:

```js
await document.fonts.ready
;[...document.fonts].filter(f => f.status === 'loaded').map(f => `${f.family} ${f.weight}`)
```

---

## Trap 2: preview cards mount named exports only

The preview harness scans your compiled preview module for **PascalCase named exports** and mounts one card cell per export. `export default` is skipped.

I had written all my previews as a single default export each. Every card rendered "no PascalCase exports" and the render check failed on all of them at once.

```jsx
// dead: renders nothing
export default function Preview() { ... }

// works: one labeled card cell per export
export function Variants() { ... }
export function Sizes() { ... }
```

Worth knowing because the failure is total (every card at once) but reads like a build problem, which sent me looking in the wrong place first. Splitting into 2 to 6 named exports per component also gives you better cards, since each one gets its own label in the picker.

---

## Trap 3: your compiled CSS does not contain the classes your docs promise

This is the one I would not have predicted, and I think it is the most generalizable.

Tailwind compiles only the classes it finds in the files it scans. That is the whole point of JIT, and it is correct for a website. But the design environment has **no Tailwind runtime**, so the shipped stylesheet is the complete and final set of classes that exist. Anything not compiled is inert.

Your design system's own source only uses a fraction of the utility surface. Mine compiled to about 400 classes. So when the agent writes perfectly ordinary layout glue:

```jsx
<section className="mx-auto max-w-5xl px-8 py-16">
  <h2 className="mb-8 text-2xl">...</h2>
  <div className="grid gap-12 md:grid-cols-3">
```

most of that does nothing, because none of those classes were in my source. Components render correctly, everything around them does not.

It gets worse if you wrote a conventions doc for the agent. Mine documented brand colours the agent was told to use, and several of them had never been compiled, because no component happened to use that exact utility. The doc confidently named classes that did not exist. The agent trusts the doc, writes the class, gets nothing.

**Check it.** Take the class vocabulary your docs promise and grep the shipped CSS for each one. Remember Tailwind escapes `:` in selectors, so `md:grid-cols-3` appears as `.md\:grid-cols-3`:

```js
const has = n => new RegExp('\\.' + n.replace(/[:\/.\[\]()]/g, c => '\\\\' + c).replace(/-/g, '\\-') + '(?![A-Za-z0-9_-])').test(css)
```

**Fix it.** Build a second stylesheet for the design bundle with a safelist covering the documented vocabulary plus the common layout and type surface, and point the sync at that one. Your site keeps its lean build:

```js
// tailwind.design.js
import base from './tailwind.config.js'

export default {
  ...base,
  safelist: [
    ...colors.flatMap(c => [`bg-${c}`, `text-${c}`, `border-${c}`]),
    ...spacing.flatMap(n => [`p-${n}`, `py-${n}`, `mb-${n}`, `gap-${n}`]),
    // responsive variants need pattern form; plain strings do not expand
    { pattern: /^grid-cols-(1|2|3|4|6|12)$/, variants: ['sm', 'md', 'lg'] },
  ],
}
```

Mine went from 18 KB to 62 KB, which is nothing for the environment it ships to, and the site build was left untouched.

**Then tell the agent the boundary exists.** A safelist is finite, so arbitrary values (`p-[13px]`, `bg-[#123456]`) still silently fail. That belongs in the conventions doc explicitly, along with what to do instead (inline `style` for one-off values).

---

## The pre-flight check I would run next time

Before trusting a sync, in this order:

1. **Fonts.** Are `@font-face` rules or a font `@import` reachable from `styles.css`? Confirm in a real browser via `document.fonts`, not `check()`.
2. **Previews.** Named exports only. One render of one card confirms the convention before you write twenty of them.
3. **Class vocabulary.** Grep every class your conventions doc names against the shipped CSS. Then grep a sample of ordinary glue the agent will plausibly write (`py-16`, `text-2xl`, `md:grid-cols-3`, `rounded-lg`).
4. **Exports.** `Object.keys(window.YourGlobal)` in a rendered preview should list everything your docs claim exists.
5. **Look at the screenshots.** The automated render check catches empty and blank. It does not catch "rendered, but the background never applied." I only caught a missing background because I looked at the picture.

Point 5 generalizes past this whole topic. Every mechanical gate I had passed on a component that was visibly wrong.

---

## A build-order trap worth its own line

If your Tailwind `content` glob includes your preview files (it probably should, so preview-only utilities compile), then **previews feed the CSS build**. Author a preview using a class nothing else uses, and that class does not exist until you rebuild the CSS.

So the order is: write previews, rebuild CSS, then build the bundle. I got this wrong once and spent a while on a background colour that refused to appear.

---

## Who this is useful for

- You maintain a component library and want an agent building with it rather than approximating it.
- You already synced one and the output looks *almost* right.
- You are writing the conventions doc an agent reads, and want to know which promises it can actually keep.

Not useful if you have not built a design system yet. Start there.

---

## What this is NOT

- **Not a tutorial for the sync itself.** The tooling walks you through that. These are the failure modes it cannot detect for you.
- **Not Tailwind-specific in principle.** Trap 3 applies to any system where the shipped stylesheet is the final word: CSS modules, a compiled token set, anything without a runtime. Traps 1 and 2 are not Tailwind-specific at all.
- **Not a checklist I ran cleanly the first time.** All three of these are things I shipped wrong and caught afterward.

---

## Notes

One sync, one design system, so treat the specifics as one data point. The mental model in the first section is the part I would keep: work out exactly what the render environment receives, and check each assumption against that instead of against your dev setup, where everything works for reasons that do not travel.

---

## License

MIT (see the repository root).
