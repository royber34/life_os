# The bloat problem

If you've been using Claude Code for more than a few months, your `~/.claude/CLAUDE.md` has probably grown. A workflow rule here. A project preference there. A "from now on, never do X again" line after a mistake. Multiply by every domain you work in, every tool you've connected, every footgun you've stepped on, and the file quietly drifts past 500 lines. Then 1,000. Then more.

This document is the case for taking that growth seriously. It walks through what bloated CLAUDE.md files actually look like, what the research says happens when context windows fill with low-signal text, what Anthropic's own engineers recommend, and how to self-diagnose whether your setup has the problem.

## What a bloated CLAUDE.md looks like

The shape is consistent across the practitioners I've seen post about this. Most bloated globals contain some mix of:

- **Standing rules that belong there.** "Never push to a remote without asking." "Match scope to the ask." Genuine cross-project preferences.
- **Standing rules that don't.** Project-specific conventions ("in the foo repo, use snake_case for table names") that should live in that project's CLAUDE.md, not the global.
- **Procedures.** Multi-step recipes — "to deploy, first run X, then Y, then check Z" — that read like runbooks. These are typically dozens of lines each.
- **Reference content.** API descriptions, architecture summaries, tool inventories. Encyclopedic context that the model doesn't need on every turn.
- **State.** Status of in-flight projects. Task lists. "Currently working on the migration to Postgres." All of which goes stale within days.
- **Failure-log entries.** "Last time you forgot to escape backticks in PowerShell here-strings — don't do that again." Useful, but they accumulate without ever being culled.
- **Duplicated content.** The same rule, sometimes verbatim, appearing in the global file *and* in two or three project CLAUDE.mds further down the tree — all of which load simultaneously when Claude Code walks up the directory tree from your current working directory.

None of these are evil in isolation. The problem is that Claude Code concatenates all of it into your system prompt on every turn, and then layers your MCP tool schemas, recent transcript, file contents, and tool outputs on top.

## Context rot — what the research actually shows

The intuition that "more context = better answers" is wrong, and there's a growing body of empirical evidence for why.

Chroma Research's [Context Rot](https://www.trychroma.com/research/context-rot) study (2025) tested 18 LLMs — including the frontier Claude, GPT, and Gemini families — on tasks where they varied input length while holding task complexity constant. Their finding, in their own words: "model performance degrades as input length increases, often in surprising and non-uniform ways." Translation: the failure isn't at 200k tokens, where you'd expect it. It starts much earlier, and it's not predictable from length alone.

This builds on Liu et al.'s ["Lost in the Middle"](https://arxiv.org/abs/2307.03172) paper (TACL 2024), which documented a U-shaped attention pattern across long-context models: information at the beginning and end of the context gets attended to, while information in the middle gets neglected. A 1,500-line CLAUDE.md doesn't just cost tokens — it pushes some of your most important rules into a low-attention zone.

Anthropic's own engineering blog post on [effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) treats context as "a finite resource with diminishing marginal returns." Their guidance is to find "the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome." That framing — context as a budget you spend, not a bucket you fill — is the right mental model for a CLAUDE.md.

## What Anthropic says about CLAUDE.md specifically

Anthropic's [Claude Code best practices](https://code.claude.com/docs/en/best-practices) is unusually direct on this point. Two passages stand out:

> "There's no required format for CLAUDE.md files, but keep it short and human-readable."

> "Bloated CLAUDE.md files cause Claude to ignore your actual instructions!"

The Claude Code [memory documentation](https://code.claude.com/docs/en/memory) is even more specific about size: target under 200 lines per CLAUDE.md file. That's not 200 lines per *workspace*. It's 200 lines per *file* — and since Claude Code loads multiple CLAUDE.md files concurrently (global plus every level of the project tree it walks through), the aggregate matters too.

For a real-world anchor, Boris Cherny — the engineer behind Claude Code — has shared his own personal global CLAUDE.md. The community-maintained [howborisusesclaudecode.com](https://howborisusesclaudecode.com) aggregates the patterns from it. It clocks in at roughly 100 lines. The contents are mostly meta-rules about how Boris wants Claude to *behave*, not encyclopedic context about his work. The signal is dense.

The implication: if your global CLAUDE.md is 5x or 10x the size of the file written by the person who designed the tool, you're operating outside the design intent.

## Token math — what a bloated setup actually costs

Walk through the numbers for a representative session.

Suppose your global CLAUDE.md is 1,200 lines. At roughly 8-12 tokens per line for prose-with-markdown, that's around 10,000 tokens. Now add a few project CLAUDE.mds that load when you cd into a project — say 500 lines each, two of them, another 8,000 tokens. You're at 18,000 tokens of instruction surface before Claude has read a single file.

Now layer MCP tool schemas. A modestly configured Claude Code setup with five or six MCP servers (filesystem, browser, search, a couple of integrations) easily hits 25,000-50,000 tokens just in tool definitions and parameter schemas. The schemas are large because every tool advertises its parameters, types, and descriptions on every turn.

You're now at 43,000 to 68,000 tokens consumed before any actual work. On Claude's 200k context window, that's 22% to 34% of the budget spent on overhead. On the 1M context model, the percentage is smaller but the absolute attention cost — per the Chroma and Liu et al. findings — is not.

That overhead doesn't go away during the session. It compounds. Every tool call adds its output. Every file you read gets included. Every back-and-forth grows the transcript. By the time you're deep in a multi-step task, your CLAUDE.md content is competing with thousands of tokens of live work product for the model's attention — and it's losing.

A second-order effect worth naming: the longer your CLAUDE.md, the more likely it contains *contradictions*. After 800 lines of accumulated rules, you almost certainly have two lines that pull in different directions — one written six months ago, one written last week, neither cross-referenced. The model has to resolve those silently, and you don't get to see how it resolved them. Shorter files are not just faster; they're more internally consistent because there's less surface for drift.

## Prompt caching doesn't save you

A reasonable objection: "Doesn't prompt caching make this free? The first turn pays the cost, the rest of the session reads from cache."

Caching helps with *one* problem and not the others. Anthropic's [prompt caching documentation](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching) is explicit that caching reduces time-to-first-token and per-call cost on cache hits. What it does not do is reduce the model's *attention* over those tokens. The cached content is still inside the context window. The model still has to attend to it. The Chroma context-rot findings still apply. The Liu et al. lost-in-the-middle findings still apply.

In other words: caching makes your bloated CLAUDE.md *cheap*. It does not make it *accurate*. If your rules are getting ignored because they're buried in a 1,500-line file, caching the 1,500-line file doesn't help.

There's a related trap. Because caching makes the cost mostly invisible (no obvious per-call dollar signal), there's no natural feedback loop pushing you to keep the file small. With a paid model called via API, you'd notice the cost climb. With a Claude Code session backed by cached system prompts, you mostly don't. The economic incentive to prune is muted; the attention incentive to prune is not. The restructure exists to enforce what the economics don't.

## Self-diagnosis — is this your problem?

You can self-diagnose without instrumentation. The symptoms cluster:

- **Repeated rule-drops.** You wrote "never X" in your CLAUDE.md and Claude is doing X anyway, two months later. Especially if it followed the rule when the file was smaller.
- **Slow first response.** Time-to-first-token visibly lags on a fresh session, even before any tool calls. Long prompt = more processing.
- **Accuracy degradation in long sessions.** Early turns are sharp, later turns get sloppier. Some of this is normal, but if rules that should be load-bearing get forgotten mid-session, your CLAUDE.md is competing with the transcript for attention and losing.
- **Forgotten preferences.** "Use PowerShell syntax on Windows" is in your file, and Claude keeps writing bash. The rule is present but not surfacing.
- **The "I told you this already" frustration.** You're correcting the same mistake more than twice. Either the rule isn't written down, or it is written down but buried.
- **Triple-duplicates.** When you run a discovery pass (covered in [docs/03-audit-your-setup.md](03-audit-your-setup.md)), you find the same workflow rule in your global file *and* in two nested project CLAUDE.mds that all load when you cd deep enough.
- **You can't remember what's in it.** A robust test: open your global CLAUDE.md and skim the headings. If more than a quarter of them surprise you, the file has outgrown your ability to mentally model it — and if you can't model it, you can't trust that Claude is faithfully following it either.
- **Stale content survives.** You find a section referring to a project you abandoned eight months ago, or a tool you no longer use. The file has become an archive rather than a working document.

A quick way to put a number on it: run a word count on your global file. Anything under 2,500 words is roughly Boris's scale and probably fine. 2,500-7,000 words is the gray zone — workable but worth pruning. Over 7,000 words and you're well outside design intent; the symptoms above are likely already showing up, even if you've been attributing them to other causes.

If three or more of the symptoms above resonate, your CLAUDE.md is likely the problem — not your prompting, not the model. The fix is structural, and the rest of this playbook walks through it.

The first move, before touching anything, is a research pass to anchor your cuts in citations rather than opinions. That's [docs/02-research-pass.md](02-research-pass.md).
