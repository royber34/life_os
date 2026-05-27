# The research pass

Before you delete anything, read. The point of a research pass is not to become an expert on context engineering. It's to anchor your eventual cuts in citations and patterns you can point to, not in opinions. When you later sit down to remove 800 lines from a CLAUDE.md file you spent a year building, you want a clear answer to "why am I cutting this?" beyond "it felt long."

This document is a reading list with a method attached. Budget two to four focused hours. The output is a short personal reference file you'll use during the audit and restructure phases.

## Why research first

Two failure modes if you skip this step:

1. **Cuts that don't stick.** You delete a section, then in two weeks you re-add it because you can't remember why you cut it. With citations, the rationale lives in your reference file and survives the gap.
2. **Cuts in the wrong places.** It's easy to cut what feels long and keep what feels comfortable. The research pass gives you principles ("state doesn't belong here," "procedures belong in skills") that let you cut the right things rather than just the obvious ones.

Researched cuts also make this defensible if you're sharing your setup with teammates or writing about it publicly. "I removed this because Anthropic's best-practices guide says CLAUDE.md files over 200 lines start to dilute" is a stronger justification than "I felt like it."

## The four source categories

Read across four categories. Skim more than you read deeply; most of what you need is in summary statements, not full papers.

### 1. Anthropic's official documentation

Start here because Anthropic is the source of truth for how Claude Code actually processes CLAUDE.md files and what it's designed for.

- [Claude Code best practices](https://code.claude.com/docs/en/best-practices): the canonical post. Read the CLAUDE.md section closely. Note the "Bloated CLAUDE.md files cause Claude to ignore your actual instructions!" line.
- [Memory documentation](https://code.claude.com/docs/en/memory): covers the loading hierarchy (Claude Code walks up the directory tree from your cwd), the 200-line target, and the difference between global, project, and local files.
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents): broader piece on context as a finite resource. The framing is more useful than any specific tactic.
- [Prompt caching docs](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching): read this to understand what caching does and doesn't help with, so you don't talk yourself out of restructuring on the assumption that caching makes bloat free.

### 2. Boris Cherny's CLAUDE.md and adjacent commentary

Boris is the engineer behind Claude Code, and his personal CLAUDE.md is the closest thing we have to a reference implementation.

- [howborisusesclaudecode.com](https://howborisusesclaudecode.com): fan site aggregating tips and patterns sourced from Boris's public posts since early 2026. The most accessible reference for the structure and scale of his CLAUDE.md.
- HumanLayer's [Writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md) and adjacent posts have field-tested examples of compact CLAUDE.mds in real codebases.

What to take away: scale, density, and what kinds of content earn a spot.

### 3. Context-rot research

The empirical case for keeping things short.

- Chroma Research, [Context Rot](https://www.trychroma.com/research/context-rot) (2025): read the executive summary. Note the finding that degradation happens well below stated context limits.
- Liu et al., ["Lost in the Middle: How Language Models Use Long Contexts"](https://arxiv.org/abs/2307.03172) (TACL 2024): read the abstract and the U-shape attention figure. You don't need the math.
- Anthropic's [context engineering blog post](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), revisited with this lens.

What to take away: the empirical floor under the "keep it short" rule.

### 4. Real-world exemplars

The most useful category for pattern-matching. Read several CLAUDE.mds from real public repos. Note what they include, what they exclude, and how they structure scope (global vs project vs nested).

- [josix/awesome-claude-md](https://github.com/josix/awesome-claude-md): curated list of public CLAUDE.md files across projects. Start here.
- [Trail of Bits](https://github.com/trailofbits): security firm; their CLAUDE.mds focus on tooling conventions and code-review expectations.
- [Ory dockertest](https://github.com/ory/dockertest): short, scoped to the repo.
- [Serial-Studio](https://github.com/Serial-Studio/Serial-Studio): focused on a single C++/Qt codebase, demonstrates project-scoped CLAUDE.md done right.
- [PyTorch tutorials](https://github.com/pytorch/tutorials): large project, narrow CLAUDE.md.
- [Sourcegraph CodeScaleBench](https://github.com/sourcegraph/CodeScaleBench): research-grade repo.
- [quayside](https://github.com/quayside-app/quayside): open-source project management, illustrates a mid-sized CLAUDE.md.

What to take away: patterns you'll want to copy (e.g., "this is where build/test/lint commands go"), and anti-patterns to avoid (e.g., long task lists, stale roadmap notes, encyclopedic context dumps).

## Using parallel subagents for the research pass

Claude Code itself is well-suited to running this research pass. There's a pleasing recursion to using Claude Code to research how to fix Claude Code. The pattern that works:

1. Open a fresh Claude Code session with a clean cwd.
2. Ask Claude Code to spawn parallel subagents (the Task tool), one per source category. Give each subagent a focused brief: "Read these three URLs about context rot, extract the three or four most citable findings, return them as a short bulleted list with inline links."
3. Synthesize the subagent outputs in the main thread. You read the synthesis, not the raw transcripts.

Sample brief for a subagent:

> Research the official Anthropic guidance on CLAUDE.md sizing and structure. Sources to read: [list URLs]. Return a short brief with: (1) the strongest direct quotes about CLAUDE.md bloat and size, with URLs, (2) the recommended size targets with URLs, (3) the hierarchy/loading model with URLs. No commentary, just citable findings.

Three or four subagents running in parallel can compress this pass from hours to under an hour. Their outputs go straight into your reference file.

## A worked example: applying the test

The test that does most of the work is Boris's: *"Would removing this cause Claude to make mistakes?"*

Suppose your CLAUDE.md contains this section:

> ## Backend service architecture
> Our backend has three services: API gateway (port 8080), worker queue (port 8081), and notification dispatcher (port 8082). The API gateway routes to the workers via Redis pub/sub on channel `tasks`. Workers write results to Postgres table `task_results`. The notification dispatcher polls `task_results` every 10 seconds for rows with `notified_at IS NULL`.

You're tempted to keep it because it feels load-bearing; it's context Claude needs to work in this codebase. Run the test:

- Would removing this cause Claude to make mistakes? Possibly, if Claude is making architectural changes and doesn't otherwise know about the worker queue.
- But is this *global* CLAUDE.md content? No. It's project-specific. It belongs in the backend repo's CLAUDE.md, not in your `~/.claude/CLAUDE.md`.
- Even at the project level, is it the right shape for CLAUDE.md? Probably not. It's reference content. A 30-line architecture diagram belongs in the repo README, with a one-liner in CLAUDE.md saying "see README.md for service architecture."

The test is layered. First: would removing this cause mistakes? Second: is this the right *scope*? Third: is this the right *file*?

Most content fails one of the second two checks even when it passes the first.

## The output: your rules and citations file

The deliverable from the research pass is a short personal reference file. Roughly 50-100 lines. Markdown. Live in your `~/.claude/` directory but not as `CLAUDE.md` itself; name it something like `restructure-references.md` so it's not auto-loaded.

The structure that works:

```
# Restructure references

## The eight principles
[brief list of principles you've extracted from the research, each with a citation link]

## Size targets
- Global CLAUDE.md: under 200 lines per file ([Anthropic memory docs](URL))
- Boris's reference point: ~100 lines ([howborisusesclaudecode.com](URL))

## Anchor quotes
- "A bloated file can dilute its influence and cause Claude to ignore your actual instructions" ([best-practices guide](URL))
- "Context as a finite resource with diminishing marginal returns" ([context engineering blog](URL))

## Patterns to copy
[from the real-world exemplars]

## Anti-patterns to avoid
[from the same exemplars and from your own audit]
```

This file is your reference during the audit and restructure phases. When you're about to cut something and feel hesitant, you re-read this. When something stays in, you cite *why*. The discipline keeps the restructure honest.

Next: applying this to your own setup, starting with discovery and classification. That's [docs/03-audit-your-setup.md](03-audit-your-setup.md).
