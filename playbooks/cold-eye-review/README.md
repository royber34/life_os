# Cold-Eye Review: read your work as the recipient before you send it

A Claude Code skill that reviews anything about to leave your hands — a client email, a proposal, a deck, a post, any public-facing doc — through the eyes of the person who'll receive it. It reports how the work lands in three levels of depth (a 5-second skim, a 1–2 minute read, and the between-the-lines interpretation), flags tone friction and missing pieces, fixes them, and loops until it's at "I'd send this as-is" quality.

This is the pass I kept doing by hand, badly and inconsistently, before I wrote it down: re-reading my own draft pretending to be the client, and catching the thing that reads fine to me but lands wrong to them. Writing it as a skill made it repeatable instead of something I'd remember to do only when the stakes were obvious. Whether it generalizes is your call; sharing what's worked so far in case any of it lands for you.

---

## Two ways to use this

**Read and get inspired.** The method below — the three depth-levels, the recipient-context-first rule, the "I'd send this as-is" bar — stands on its own. You can run it in your head on your next important email without installing anything.

**Install the skill and let it run the pass.** When you're finalizing something that matters, install it (one line in [Quick start](#quick-start-install-the-skill)) and ask Claude to cold-eye review the draft. You make the judgment calls; the skill does the structured read, surfaces what would land wrong, and iterates.

---

## The problem

You wrote it, so you can't unsee what you meant. You read your own draft and your brain fills in the context, the tone, the intent — all the things the recipient doesn't have. So the email that reads as "warm and direct" to you reads as "curt" to them. The proposal that feels thorough to you feels like it's burying the ask. The post that sounds confident to you sounds defensive to someone reading between the lines.

The fix isn't "proofread again." It's to read it as someone who isn't you, with only what *they* know, and report honestly how it lands. That's a different cognitive stance, and it's exactly the kind of thing a fresh-context model is good at — if you give it the recipient's perspective and a structure to report against.

This skill is that structure. Not a definitive answer; what's been working for me so far.

---

## When to reach for it

Run it on anything that will be **sent, shown, or published to someone other than you**:

- Client and prospect emails, especially first contact or anything sensitive
- Proposals, SOWs, quotes, paid deliverables
- Decks and one-pagers going to an external audience
- Public posts (LinkedIn, Reddit, anywhere your name is attached)
- A reply you're about to fire off while annoyed

Skip it for internal notes, throwaway messages, or anything low-stakes where a fresh read buys nothing. The bar is *"would I be embarrassed if this landed wrong?"* If yes, run it.

**One sequencing rule:** run it *last*. Cold-eye review is a Pass 2. It assumes the facts, numbers, citations, and math are already correct (Pass 1) and asks the separate question of *how it lands*. Don't use it to catch a wrong figure — fix those first, then review for landing. The skill enforces this and will stop you if Pass 1 isn't clean.

---

## How it works

Five steps, run by the skill once invoked:

1. **Gather recipient context** — prior call transcripts, past emails, their role, their priorities, how they read. No context? It asks you for a quick brief rather than guessing.
2. **Read end-to-end as the recipient** — hunting for tone friction, missing pieces they'd expect, confusion points, implicit asks, and off-brand bits.
3. **Report in three depth-levels** — the 5-second skim impression, the 1–2 minute working understanding, and the 3–5 minute between-the-lines read (what they'd suspect, push back on, conclude about you as a counterparty).
4. **Fix and iterate** — patch what you'd want fixed, say what changed and why, loop to "I'd send this as-is."
5. **Red-team the high-stakes ones** — for first impressions, paid work, or anything irreversible, it spawns a separate reviewer with the recipient context loaded fresh, to pressure-test independently before you see it.

---

## Who this is useful for

- You send a lot of work to clients, partners, or prospects and want a consistent last look.
- You've shipped something that landed wrong and only saw why afterward.
- You want the "read it as them" pass to happen every time, not just when you remember.

This is **not** for you if:

- Most of what you write is internal or low-stakes. The overhead won't pay off.
- You want a grammar or fact checker. This reviews *how it lands*, not whether it's correct — that's a separate (earlier) pass.

---

## Before you start (new to Claude Code?)

This runs in **Claude Code**, which is part of Claude, not a separate install. If you've only used the Chat side, open the **Code tab in the Claude desktop app** or go to **[claude.ai/code](https://claude.ai/code)**. It's included with a paid Claude plan (Pro or Max).

To add the skill, open Claude Code and either paste the one-liner below, or just ask: *"install the cold-eye-review skill from github.com/royber34/life_os."* It downloads one skill folder to your computer and sends nothing anywhere.

---

## Quick start: install the skill

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/cold-eye-review/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/cold-eye-review/install.ps1 | iex
```

Then, in any Claude Code session, ask: *"cold-eye review this before I send it"*, *"how does this land for the client?"*, or *"review this as the recipient."* The skill kicks in, asks for recipient context if it needs it, and runs the pass.

---

## What's in this repo

```
.
├── README.md      ← This file
├── install.sh     ← One-line bash installer
├── install.ps1    ← One-line PowerShell installer
└── skill/
    └── SKILL.md   ← The installable Claude Code skill body
```

---

## What this is NOT

- **Not a framework.** It's one focused review pass with a clear bar.
- **Not a fact-checker or proofreader.** It assumes correctness is already handled and reviews how the work lands.
- **Not a tone-softener.** If direct is right for the relationship, it keeps it direct. It optimizes for the recipient responding the way you want, not for being inoffensive.
- **Not autopilot.** It surfaces and fixes, but you make the call on what ships. It stops and tells you when something's blocking rather than grinding silently.

---

## Notes

The three-depth-levels framing is a homegrown heuristic, not a cited methodology — it just maps to how people actually read (skim, then read, then occasionally read between the lines). Use only your own recipient context (your emails, your call notes). The skill needs no MCP server, though it'll use call-transcript or email tools if you have them connected.

---

## License

MIT (see the repository root).
