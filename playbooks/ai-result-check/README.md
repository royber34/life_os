# AI Result Check: test an AI result before you rely on it

Copy-paste prompts and a Claude Code skill for checking whether an AI result can be relied on: a report, an analysis, a research file, a summary, a calculation.

AI output usually reads well and makes sense on a first read, and that is the tricky part. It can still be wrong, have missed things, or have made things up. So for me, most of the work now comes after the first output: verifying it, shaping it and verifying it again. This is the routine I've been using. Sharing what's worked so far in case any of it helps.

---

## Two ways to use this

**Copy and paste, in any AI tool.** The prompts in [prompts.md](prompts.md) work in ChatGPT, Copilot, Gemini or Claude. Nothing to install.

**Install the skill, if you use Claude Code.** It runs the checks in order and labels the result. See [Quick start](#quick-start-install-the-skill).

---

## The method

**1. Test the whole thing first.** I give the AI the full prompt for the outcome I want and run it several times. If the result is accurate, complete and consistent across runs, I can start to trust it for that task.

**2. If it varies, break it down.** This happens often with bigger or multi-step work. I split it into smaller steps, check each one until it's reliable, then link the steps back together as a workflow.

**3. Check against what you already know.** Start with facts you can verify: the row count of the file, a handful of values, a result someone has already worked out by hand. An AI tool can skip rows in a spreadsheet on a first pass. On my [Hidden Tide](https://hiddentide.com) project, the AI's reading of a lighthouse logbook page matched an existing volunteer transcription on 14 of 14 days before I trusted it on a book nobody had transcribed.

**4. Use an independent checker.** Same-model review can be biased, so I use, in increasing order of strength:
   - a fresh agent, with no memory of the work, on the same model
   - a different model reviewing the first one's work
   - a workflow that routes work between models automatically

**5. Say what the result is.** Label it as accurate to the raw data, or as directional only. A result can be right in direction and off in the detail, and the next reader should know which they're holding.

**6. A person decides.** The AI flags. The person responsible makes the call.

## What I check for

The main three: **repeatable, accurate, complete**. Underneath those, more as style: **not overstated, not overbuilt**. When I correct an AI, I also tell it to avoid overcorrecting and to keep it simple.

## What it costs

For me, a first deep prompt takes 20 to 30 minutes. Checking and testing take three to five times that, depending on how complex the information is. I'd build that into what you expect AI to save you. Once a workflow is repeatable, building the checks into the prompt shortens this a lot.

---

## Quick start: install the skill

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/ai-result-check/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/ai-result-check/install.ps1 | iex
```

Then, in any Claude Code session, ask: *"check this AI result before I rely on it"*.

---

## What's in this folder

```
.
├── README.md      ← This file
├── prompts.md     ← Copy-paste prompts for any AI tool
├── install.sh     ← One-line bash installer
├── install.ps1    ← One-line PowerShell installer
└── skill/
    └── SKILL.md   ← The installable Claude Code skill
```

---

## Limits

- These checks catch a lot and still miss things. For anything that matters, a person checks the items that matter most.
- A check can only be as good as its sources. If you can't give it the raw data, it can only tell you what it could not check.
- Don't paste confidential data into a tool your company hasn't approved.

---

## License

MIT (see the repository root).
