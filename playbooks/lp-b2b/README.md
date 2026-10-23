# LP B2B: sales pages a business buyer acts on without a call

Two Claude Code skills for B2B landing pages: the kind you send as a link after a LinkedIn message or a cold email, where the reader should understand the offer, believe it and request a start (or book, order, sign up) on their own. The first skill builds the page with you, stage by stage. The second reviews any page the way a first-time visitor sees it.

I built two B2B sales pages with Claude in October 2026. One went through 20 versions in two days, most of them fixing things a better start would have settled. The other went through four rounds of simulated buyer reviews, and none of them caught what I saw in one look when I opened the live page as a stranger would: it asked people to pick an option before it said what the product was. All of those simulated buyers had been briefed on me and my offer. This playbook is what I'd do from the start next time. In a blind test, a draft of these skills rebuilt one of those pages from two call transcripts, with every question left on its default, and four simulated buyers who had seen neither page all preferred the result to the live version. Whether it generalizes is your call; sharing what's worked so far in case any of it lands for you.

**Fastest way** (on a computer, in the Code tab of the Claude desktop app; new to it? see [Before you start](#before-you-start-new-to-claude-code)): start a session in a new folder for your page, with any call notes or offer docs you have inside it, and paste:

> *Install the skills at https://github.com/royber34/life_os/tree/main/playbooks/lp-b2b and use them to build a landing page for my offer.*

---

## The problem

A B2B page read cold has seconds to answer six questions: what is this, is it for me, what do I get, over how long, for how much, and what happens if I click. Most pages answer them in the wrong order, hide the price, or bury the one line that matters under jargon.

Reviewing doesn't catch it as often as you'd think. Reviewers who know you or your offer fill the gaps themselves and score the page too high. Reviewers who don't know your decisions keep asking for the caveats and detail you left out on purpose. And iterating on scores runs forever, because the scores move by a point or two between identical runs.

---

## How it works

You answer a few questions (or hand over call notes, transcripts or an offer doc). Claude does the rest in five stages and stops for your yes after each one.

| Stage | What happens | You approve |
|---|---|---|
| 1 Brief | The goal of the page in one paragraph, your answers, what proof exists and what's missing | the goal and the answers |
| 2 Page | The section order and the wording as plain text, read by three simulated first-time visitors before anything is designed; then the final copy | the wireframe |
| 3 Build | Two first-screen design options; then one static HTML page with a working form, link preview and thanks page | the design |
| 4 Review | A panel of simulated visitors who know nothing about you scores the page, then one or two rounds of fixes | the rendered page |
| 5 Go live | A checklist of everything that broke on real pages; publishing only when you say so | each publish |

The questions it starts with:

1. What should a visitor do on the page, and what happens after?
2. What do you sell, in one sentence, and to whom?
3. How do visitors arrive, and on what device?
4. What are the options and prices?
5. What risk reversal can you carry (money back, nothing binding until you confirm, a paid first step)?
6. What proof do you have?
7. Anything fixed: brand, domain, language, market, rules for your profession about what you may claim, words you never use, things that must never be on the page?

Every question comes with a sensible default, so "go with your defaults" works too.

### The review on its own

`lp-b2b-review` works on any page, built with this or not. Point it at a URL or a file:

> *"Review my landing page at example.com/offer as a cold buyer would see it. Is it ready to send?"*

It takes phone and desktop screenshots, writes a few personas like your buyers who have never heard of you, and asks each to read the page cold: what is this, is it for me, what do I get, how long, how much, what happens next. A skeptic who was burnt by the alternative reads it too, plus a claims-and-legal read and a designer. You get a scoreboard, a fix list that respects the decisions you already made, and a clear "stop" or "one more round". There's also a blind A/B mode for "which version is better".

---

## Who this is useful for

- You sell a B2B service or product and want a page people can act on without booking a call first.
- You send the link yourself (outbound, LinkedIn, referrals) more than you buy traffic.
- You want a reviewer that tells you whether a stranger gets it, not whether a colleague likes it.
- You can put a price and a duration on at least one way to start, such as a fixed package or a paid first step.

This is **not** for you if:

- You price every project only after a call and want no price on the page.
- You sell to consumers from paid ads with many page variants. That calls for a different structure and real A/B traffic.
- You want a full website or a CMS. This builds one page.

---

## Before you start (new to Claude Code?)

These skills run in **Claude Code**, which is part of Claude and included with a paid plan (Pro or Max). If you've only used the chat, open the **Code** tab in the Claude desktop app on your computer, and choose a folder for your page when you start a session. Use the desktop app for this one: the web and phone versions of Claude Code run in the cloud and work from a GitHub repository.

For screenshots, page checks and the link preview image, the skills use Python with Playwright and Pillow. If they're missing, ask Claude to set them up, Python first if you don't have it (`pip install playwright pillow`, then `playwright install chromium`). Without them, the quick review of your page text still runs; the screenshots, page checks and full review need them.

**What you need:** a computer with the Claude desktop app (Pro or Max plan), a clear idea of your offer (or notes from a call about it), and an hour or two spread over a day for the first page. To go live you also need an account with a web host that handles forms (Netlify by default; it has a free plan), plus your own domain if you want the page on it.

---

## Quick start: install the skills

The simplest way: ask Claude Code *"install the lp-b2b skills from github.com/royber34/life_os."* If you'd rather use a terminal, paste one of these lines. Each script only downloads the two skill folders; you can read it first.

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/lp-b2b/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/lp-b2b/install.ps1 | iex
```

Both skills go into `~/.claude/skills/`. Then start a Claude Code session in your page's folder (in the desktop app, choose that folder when you start the session) and ask:

- *"Build me a landing page for my offer."* starts at the questions.
- *"Where are we with my landing page?"* picks up where you left off.
- *"Review my landing page as a cold buyer."* runs the review on its own.

---

## What stays with you

Claude never signs in for you, and it publishes, pushes or sends a test request through your live form only after you say yes to that step. You approve each of the five stages, and you do the parts that need your accounts: signing up with a web host, connecting a domain, switching on form handling.

Claude also never invents customers, testimonials, logos or results. If your proof is thin, it tells you so and asks for what would fix it (real numbers, photos, a client who agrees to be named), and it can add a clearly labelled example of what you deliver.

---

## Good to know

- **The page has one job.** Everything on it serves one action, and the first screen carries the promise, who it's for, the button, the risk line directly under the button, a short proof line and a link to prices.
- **Options come after the explanation.** Visitors need to know what the product is before they choose, and every option shows its price and duration where it's chosen.
- **First-time visitors over familiar ones.** The simulated reviewers never see your brief or your history. That's the point.
- **A stop rule.** The loop ends when every cold visitor gets the six answers right and nothing fixable is left. Two rounds at most, then it recommends and you decide.
- **One HTML file by default.** A template engine with tests only pays off with several language versions, a calculator or a generated order document.
- **The go-live checklist** lists what actually broke: form handling switched off, every field of a two-step form showing at once, no link preview image, a README served publicly, a stale thanks page, a sticky button covering the price.
- **The full review is the heavy part.** Each round runs five to nine simulated reviewers that read screenshots, which can use a good share of a Pro plan's usage. The quick review of page text is light.
- **Legal notes are examples, not advice.** The checklist names the German and Swiss imprint rules and the EU privacy notice as examples; check your own market.

<details>
<summary>What's in this folder</summary>

```
.
├── README.md                    ← This file
├── install.sh / install.ps1     ← One-line installers (both skills)
└── skills/
    ├── lp-b2b/
    │   ├── SKILL.md             ← The five stages and the gates
    │   ├── references/
    │   │   ├── brief-questions.md   ← The key questions, with defaults
    │   │   ├── templates.md         ← GOAL.md, brief, decisions, STATE
    │   │   ├── style.md             ← Writing and claim rules
    │   │   ├── stage-page.md        ← Section order, wireframe, copy
    │   │   ├── stage-build.md       ← Design, form, link preview, go live
    │   │   └── golive-checklist.md  ← What broke on real pages
    │   └── scripts/
    │       ├── check_page.py        ← Form, sticky button, tap targets, dark mode
    │       └── og_card.py           ← Link preview image and favicons
    └── lp-b2b-review/
        ├── SKILL.md             ← Quick, full and A/B review, the stop rule
        ├── references/
        │   ├── rubric.md, personas.md, fix-brief-template.md
        │   └── prompts/             ← Visitor, judge, claims-and-legal, designer
        └── scripts/
            ├── capture.py           ← Phone and desktop screenshots, page text, warnings
            ├── lint.py              ← Style check of the page text
            └── scoreboard.py        ← Scores across reviewers or A/B judges
```

</details>

---

## License

MIT (see the repository root).
