# LinkedIn Voice: analyze your tone, then write in it

Two Claude Code skills that work as a pipeline. The first reads your LinkedIn posts and builds an evidence-cited voice profile. The second turns that profile into a copywriting guideline an agent can follow to write posts that sound like you, with hard anti-AI-tell bans and a built-in self-check.

This is the approach I landed on after trying the usual "here are my posts, mimic my tone" prompts and watching them produce generic LinkedIn slop. The difference here is that both outputs are falsifiable: every voice trait is tied to a verbatim quote and how often it occurs, and every draft is checked against explicit pass/fail rules instead of vibes. Doing it this way made the AI-written drafts noticeably closer to my own voice. Whether it generalizes is your call; sharing what's worked so far in case any of it lands for you.

---

## Two ways to use this

**Read and get inspired.** The taxonomy, the writing principles, and the anti-AI-tell ban list below stand on their own. If you write your own posts, the patterns are still worth knowing, especially the tells that make text read as machine-written. Absorb what fits and ignore the rest.

**Install the skills and run them on your own profile.** When you want an agent to draft in your voice, install the two skills (one PowerShell or bash line in [Quick start](#quick-start-install-the-skills) below) and run them in order. You make the judgment calls; the skills do the mechanical work (collecting posts, computing the objective metrics, scanning drafts against the bans).

---

## The problem

Most "write in my voice" tools do one of three things: they bundle your posts and tell the model to "read a few and match the vibe," they emit abstract tone scores, or they impose generic "viral 2026" rules. None of them tie a single claim about your voice to evidence, and none combine your actual voice with a check that catches the patterns that scream "an AI wrote this."

The result is drafts that are confidently off. Close enough to feel like you at a glance, wrong enough that you would never post them.

This playbook takes a different path. The analyzer makes every trait auditable (quote plus frequency). The writer fuses your evidence-derived voice with universal LinkedIn writing principles and a hard ban list, then self-checks against it. Not a definitive answer; what's been working for me so far.

---

## The two skills

| Skill | Input | Output |
|---|---|---|
| **linkedin-profile-tov-analyzer** | your posts (browser-collected or pasted) | `analysis.md` plus a machine-readable `voice-profile.json`, every trait quote-backed and frequency-gated, with a confidence tier set by corpus size |
| **linkedin-postwriter-guideline-writer** | the `voice-profile.json` | a long-form guideline (voice principles, hook formulas, micro-mechanics, a hard ban list, a self-check) plus sample posts written in your voice |

Run them in order. The analyzer's profile is the hand-off artifact the writer consumes. If you only have a written analysis and no JSON, the writer accepts that too.

---

## Who this is useful for

You'll get value from this if any of these are true:

- You want an agent (or a ghostwriter) to draft LinkedIn posts that actually sound like you.
- You have posted enough that there is a real voice to capture (aim for at least 12 posts).
- You keep noticing AI tells in drafts and want them caught mechanically, not by eye.
- You want a voice guide you can hand off and reuse, not a one-off prompt.

This is **not** for you if:

- You have only a handful of posts. The analysis will run, but it will say "low confidence" and mean it.
- You want a generic high-engagement template. The whole point here is your voice, not a viral formula.

---

## Before you start (new to Claude Code?)

These skills run in **Claude Code**, which is part of Claude, not a separate terminal install. If you have only used the Chat side, Claude Code is the same Claude in build mode: open the **Code tab in the Claude desktop app**, or go to **[claude.ai/code](https://claude.ai/code)** in your browser.

Claude Code is included with a paid Claude plan (Pro or Max).

To add these skills, open Claude Code and either paste the one-line installer below, or simply ask it: *"install the linkedin-voice skills from github.com/royber34/life_os."* It is safe: it downloads two skill folders to your computer, does not touch your LinkedIn login, and sends nothing anywhere.

**What you need:** Claude (Pro or Max) with Code, about 12 or more of your own LinkedIn posts, and about 10 minutes.

Not ready? The sections below still work as a read on their own.

---

## Quick start: install the skills

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/linkedin-voice/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/linkedin-voice/install.ps1 | iex
```

This installs both skill folders (each SKILL.md plus its scripts, references, and templates) into `~/.claude/skills/`. Then, in any Claude Code session:

- *"analyze my LinkedIn voice"* triggers the analyzer.
- *"turn my voice profile into a writing guideline"* triggers the writer.

---

## How the analyzer gets your posts

LinkedIn has no public posts API and blocks third-party scrapers, so the skill uses two routes:

1. **Default: Claude collects from your own logged-in browser session.** It opens your activity feed and reads what renders. LinkedIn's feed is virtualized (only a handful of posts render at a time), many entries are non-hydrating "Boost" stubs, and some are deleted, so browser capture often returns fewer posts than you would expect. The skill reports exactly how many it got.
2. **Optional reliability upgrade: the official data export.** Settings, then Data privacy, then Download my data, then Request new archive, then tick the Posts/Shares file. It returns your full post history as a CSV. LinkedIn rate-limits archive requests to roughly one per 2 hours. Use this when the browser capture is thin or you want the most complete read.

No browser tool connected, or you just want the simplest path? You can also paste your posts into a plain text file (one post per block) and point the skill at that. The export is the most complete route.

Use only your own data, through your own session or export. Third-party scrapers violate LinkedIn's User Agreement and can get your account restricted.

---

## Why the post count matters

The analysis is only as reliable as the corpus behind it, so the skill reports three numbers every run (attempted, captured, used) and a confidence tier:

- Under 8 posts: **low**. Provisional only, no firm rules.
- 8 to 19 posts: **moderate**. Directional.
- 20 or more: **strong**.

This is not a formality. In testing, a 5-post sample read a voice as "we"-dominant with no exclamation marks. At 15 posts the same voice came back balanced first-person and a regular (if sparing) user of exclamation marks. More posts, truer profile. Aim for at least 12.

---

## The falsifiability edge

- **Analyzer.** Every claimed trait carries a quote and a frequency. No claim without evidence. A `stylometry.py` script (standard library only) computes the objective layer: sentence-length variance, point-of-view ratios, punctuation density, emoji and hashtag habits, lexical richness. The interpretive layers are written by the model reading the posts, anchored to that data.
- **Writer.** The guideline ships with a hard ban list (the negation-reframe "it's not X, it's Y" is ban number one, plus em-dashes, tilde approximations, body links, engagement bait, and buzzwords) and a `lint_post.py` script that scans a draft against the mechanical bans. The lint assists; it never auto-rejects. Human judgment always overrides.

---

## What's in this repo

For the curious. You do not need to understand any of this to use the skills.

<details>
<summary>Full repo layout</summary>

```
.
├── README.md            ← This file
├── install.sh           ← One-line bash installer (both skills)
├── install.ps1          ← One-line PowerShell installer (both skills)
└── skills/
    ├── linkedin-profile-tov-analyzer/
    │   ├── SKILL.md             ← Analyzer workflow (5 phases, gates, reporting)
    │   ├── scripts/
    │   │   └── stylometry.py    ← Deterministic objective metrics
    │   ├── references/
    │   │   ├── ingestion.md         ← Browser-first capture, export option, ToS
    │   │   └── voice-taxonomy.md    ← The four-layer voice taxonomy
    │   └── templates/
    │       ├── analysis-template.md      ← The evidence-cited report shape
    │       └── voice-profile.schema.json ← The machine hand-off artifact
    └── linkedin-postwriter-guideline-writer/
        ├── SKILL.md             ← Writer workflow (6 phases, native self-check)
        ├── scripts/
        │   └── lint_post.py     ← Advisory mechanical scan of a draft
        ├── references/
        │   ├── ai-tells-banlist.md            ← The hard bans, sourced
        │   ├── linkedin-writing-principles.md ← Hooks, length, CTA, links
        │   └── self-check-protocol.md         ← The "is this them?" checklist
        └── templates/
            └── guideline-template.md          ← The output guideline shape
```

</details>

---

## What this is NOT

- **Not a framework.** It's a pair of focused skills with a clear hand-off.
- **Not a scraper.** It reads your own data, in your own session or export. Nothing else.
- **Not a viral-post generator.** It optimizes for sounding like you, not for chasing reach.
- **Not magic on a thin corpus.** Under 8 posts, it tells you the read is provisional rather than pretending otherwise.

---

## Sources

The writer's principles draw on public methodology and platform analyses. The voice taxonomy builds on Nielsen Norman Group's tone-of-voice dimensions and standard stylometric features. The anti-AI-tell list builds on the community-maintained "Signs of AI writing" catalogue. LinkedIn engagement statistics referenced in the principles come from creator and marketing-firm analyses, not LinkedIn's official disclosures, so treat them as directional.

- [Nielsen Norman Group: The Four Dimensions of Tone of Voice](https://www.nngroup.com/articles/tone-of-voice-dimensions/)
- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- [LinkedIn Help: Download your account data](https://www.linkedin.com/help/linkedin/answer/a1339364/downloading-your-account-data)

---

## Notes

- The skills run in Claude Code or claude.ai; they need no MCP server. Browser collection uses whatever browser tool you have connected.
- The Python scripts are standard library only (no install) and force UTF-8 output so emoji do not crash a Windows console.

---

## License

MIT (see the repository root).
