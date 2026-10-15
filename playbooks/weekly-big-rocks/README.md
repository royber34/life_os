# Weekly Big Rocks: plan next week from what actually happened

A Claude Code skill that reads your last week (sent email, calendar, notes, and any other sources you connect), checks it against a short "north star" file of your goals, and hands back 3 to 5 Big Rocks for the coming week. Each rock gets a reason, a next action, a definition of done and a time block, with exactly one marked as the week's #1.

I've run a fuller version of this every Sunday since early July 2026, 12 weekly plans so far. What made it useful was the evidence rules more than the planning frameworks: early on it told me, more than once, that I hadn't replied to emails I had in fact answered. This playbook is the core of that routine plus every connector trap I hit along the way. Whether it generalizes is your call; sharing what's worked so far in case any of it lands for you.

---

## Two ways to use this

**Read and get inspired.** The rock criteria, the selection steps and the [connector gotchas](skill/references/connector-gotchas.md) stand on their own. If you plan your week by hand, the five tests of a good rock below are worth stealing.

**Install the skill and run it on your own week.** One line to install (see [Quick start](#quick-start-install-the-skill)). Run it by hand first; once you trust it, make it a weekly scheduled task.

---

## The problem

Weekly plans tend to fail in four ways. They are reactive (the inbox sets the agenda), overloaded (everything is a priority), disconnected (a busy week that moves nothing you care about) or vague (a list of areas instead of actions).

An AI planner adds a fifth: it states things about your week that aren't true. "You still haven't replied to X" is easy to write and often wrong, because search tools cut threads short and the reply sits in a channel the agent can't see. A plan built on a false claim costs more than no plan.

This skill answers the first four with a short selection routine borrowed from well-known planning books, and the fifth with hard evidence rules: negative claims need the sent folder and the full thread, stale sources get named, and an independent reviewer checks the draft before you see it.

---

## Who this is useful for

You'll get value from this if:

- You juggle several roles (client work, your own business, family, health) and the week keeps getting eaten by whatever is loudest.
- Your email and calendar are connected to Claude, or you're happy to connect them.
- You want a short plan on Monday morning that you could defend line by line.

This is **not** for you if:

- You want a task manager or a calendar that books itself. This picks the few things that matter; it doesn't manage the rest.
- You'd rather not let Claude read your email. The skill is read-only, but it does read.

---

## Before you start (new to Claude Code?)

This runs in **Claude Code**, which is part of Claude, not a separate install. If you've only used the Chat side, open the **Code tab in the Claude desktop app**. Use the desktop app for this one: your north star and plans are saved on your computer, and weekly runs happen there. It's included with a paid Claude plan (Pro or Max).

Connect at least your email and calendar under Settings, Connectors (Gmail and Google Calendar both have official connectors). Notes, meeting transcripts, Slack and others are optional.

To add the skill, open Claude Code and either paste the one-liner below, or just ask: *"install the weekly-big-rocks skill from github.com/royber34/life_os."* It downloads one skill folder to your computer and sends nothing anywhere.

**What you need:** Claude (Pro or Max) with Code, email and calendar connected, and about 15 minutes for the first run.

---

## Quick start: install the skill

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/weekly-big-rocks/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/weekly-big-rocks/install.ps1 | iex
```

Then, in a new Claude Code session, ask: *"plan my big rocks for next week"* or *"run my weekly review."*

**The first run** asks you six short questions (how you want your weeks to feel, goals, roles, values, this quarter's focus, what you're deliberately not chasing) and saves the answers as `~/.claude/weekly-big-rocks/north-star.md`. Every rock has to tie back to a line in that file, so it's worth ten honest minutes. Plans are saved next to it, one file per week.

**Pre-commit a rock (optional).** If you already know something has to happen next week, create next week's plan file yourself (`plan-YYYY-MM-DD.md`, dated that Monday) and write it in. The skill keeps your text word for word and plans around it.

---

## Make it weekly (optional)

Once a few hand-run plans look right, make it a Desktop scheduled task: in the Code tab, open **Routines**, click **New routine**, choose **Local**, and set it to weekly (for example Sunday 17:00) with the prompt *"plan my big rocks for next week"*. You can also just ask Claude to set it up. Three things to know:

- **Pre-approve the read tools it uses**, one by one. A single permission prompt can stall an unattended run for as long as nobody is there to click it. Never approve send or reply tools for it. The optional Slack post needs Slack's send tool: approve that one only if you're comfortable with it, otherwise skip Slack and read the plan file.
- **It runs on your computer**, so the app has to be open and the computer awake. A missed run catches up once when the computer wakes, which can mean Sunday's plan arrives Monday morning.
- **Do the first run by hand.** The north-star questions need you there.

---

## How it works

**What makes a rock a Big Rock.** Five tests: it's important over urgent (Covey's Quadrant II), it ties to a named line in your north star, it's a lead measure you control this week (4DX), it has a verb-first next action and a definition of done, and it has a time block (an implementation intention). Three to five rocks, one #1, picked with the Focusing Question from *The ONE Thing*.

**The routine, in five steps:**

1. **Orient.** Read the north star and last week's plan. Keep any rock you pre-committed.
2. **Gather.** Each connected source gets its own read-only subagent, and each returns the same thing: candidate rocks, open loops, hard commitments, a source citation and a "discussed or done" tag for every item, and a line on how fresh the source is. Duplicates are merged, later decisions override earlier ones, and last week's rocks are scored done, partial, slipped or dropped.
3. **Choose.** Candidates per role, urgent vs important, tie to the north star, convert outcomes into actions you control, cut to 3 to 5 with one #1, nest related tasks under their rock, keep a short "Also this week" list and an explicit "Not this week" list, then check the time blocks fit your free hours.
4. **Check.** A separate reviewer with a fresh context runs ten yes/no checks. The non-negotiables: no claim without a source, no "you didn't send it" without the sent folder and the full thread, stale sources named, your pre-committed text untouched.
5. **Save.** Write the plan to a local markdown file, re-reading it first so nothing you added mid-run gets overwritten. Optionally post it to your own Slack channel.

See [`examples/sample-plan.md`](examples/sample-plan.md) for what a finished plan looks like.

---

## The gotchas

The most reusable part of this playbook. Each of these produced a wrong finding, or nearly did, in my runs. The full list is in [`connector-gotchas.md`](skill/references/connector-gotchas.md); the skill reads it before every run.

- **The sent folder is the evidence.** "You didn't send it" needs the sent folder and drafts of every channel you send from. Unreachable channel: "unverifiable", never "not sent".
- **Gmail thread search cuts threads short.** It returned at most 5 messages per thread and dropped the newest. One thread showed 5 and had 11. Open the full thread before claiming "no reply".
- **Slack channel search misses DMs.** Search DMs separately; they often hold the most important message of the week.
- **Meeting summaries invent details.** A summary named a person and a city that appear nowhere in the transcript. Names and numbers come from the transcript only.
- **Self-checks are lenient.** A reviewer that hadn't written the draft failed it on 6 of the 11 checks in my fuller version; checks run inside the drafting context had let the same kind of error through.

---

## What's in this repo

For the curious. You don't need any of this to use the skill.

<details>
<summary>Full layout</summary>

```
.
├── README.md                          ← This file
├── install.sh                         ← One-line bash installer
├── install.ps1                        ← One-line PowerShell installer
├── examples/
│   └── sample-plan.md                 ← A fictional finished plan
└── skill/
    ├── SKILL.md                       ← The routine
    ├── templates/
    │   └── north-star.md              ← The goals file every rock ties back to
    └── references/
        └── connector-gotchas.md       ← The traps, read before every run
```

</details>

---

## What this is NOT

- **Not a task manager.** Your to-do list stays where it is. The skill picks the few things that matter this week.
- **Not autonomous.** It reads your sources and writes files in its own folder. It never sends, replies, accepts or deletes anything, apart from the optional post to your own Slack channel.
- **Not a coach with opinions about your life.** Every rock ties back to goals you wrote down yourself.
- **Not my full routine.** Mine has more sources, three review stages and some personal rules. This is the part I'd expect to transfer.

---

## Sources

The selection steps borrow from these books and papers. The connector gotchas come from my own runs between July and October 2026; connectors change, so treat them as things to check.

- Stephen R. Covey, A. Roger Merrill, Rebecca R. Merrill: *First Things First* (1994), which popularized the big rocks illustration
- Stephen R. Covey: *The 7 Habits of Highly Effective People* (1989), the urgent/important matrix and weekly planning by roles
- Chris McChesney, Sean Covey, Jim Huling: *The 4 Disciplines of Execution* (2012), lead and lag measures
- Gary Keller, Jay Papasan: *The ONE Thing* (2013), the Focusing Question
- Peter M. Gollwitzer: [Implementation intentions: Strong effects of simple plans](https://doi.org/10.1037/0003-066X.54.7.493) (1999), *American Psychologist*
- David Allen: *Getting Things Done* (2001), the weekly review

---

## Notes

- Everything stays on your computer: the north star and the plans are plain markdown files in `~/.claude/weekly-big-rocks/`. The skill only reads your connected sources.
- A run uses one subagent per source plus a reviewer, so it takes a few minutes and more usage than a normal chat. If subagents aren't available, it runs the same steps in one thread and says the check was self-run.

---

## License

MIT (see the repository root).
