# Before and after: one anonymized case

This is the actual transformation produced by applying the methodology to one Claude Code setup. Numbers are real. Specifics of the work are not. Your before-and-after will differ; the *shape* of the change is what generalizes.

---

## Starting state: the bloated global

The global `~/.claude/CLAUDE.md` had accumulated over roughly six months. Content fell into the following categories:

| Section | Approx. lines | Type | Pre-restructure verdict |
|---|---:|---|---|
| Identity & cross-project preferences | ~15 | Standing | KEEP |
| Cross-project working-style rules | ~30 | Standing | KEEP |
| Infrastructure docs for a side project | ~150 | Reference + state | MOVE to project repo |
| Architecture details for that side project | ~80 | Reference | MOVE to project repo |
| Known-issues / bug-numbers list | ~30 | State | MOVE to project repo |
| Security hardening status checklist (✅/⬜) | ~30 | Frequently-changing state | MOVE, out of CLAUDE.md |
| Active work-tracks roadmap | ~30 | Planning state | MOVE to a `PLANS.md` |
| Architecture for a second side project | ~80 | Reference | MOVE to that project's own CLAUDE.md |
| Integration-setup runbook (multi-step) | ~70 | Procedural | MOVE to a skill |
| Provider-auth-fix operational runbook | ~30 | Procedural | MOVE to a skill |
| Operational-commands cheatsheet | ~25 | Reference | MOVE to a `USEFUL-COMMANDS.md` |
| Conventions + do-not rules (mixed scope) | ~25 | Mixed | SPLIT by scope |
| Scaling research notes | ~10 | Notes | DELETE, not instructional |
| Custom-skills directory listing | ~20 | Redundant | DELETE, skills auto-discover |
| Dated update log | ~50 | Changelog | DELETE, git history serves this |
| **Total** | **~540 lines / ~10,000 tokens** | | |

The file consumed roughly 5% of a 200k context window before any work began. Combined with MCP tool schemas typically loaded into a session (often another 25–35k tokens), the *pre-prompt* overhead landed around 18–23% of the window, measurably degrading both accuracy on long-context work and how quickly Claude Code's auto-compaction triggered.

---

## Where each part landed after the restructure

Generic destinations only: the *kinds* of places content moved to. Your destinations will differ depending on your project layout.

| Original content | Where it went | Why |
|---|---|---|
| Identity + cross-project preferences | **Stayed in global**, condensed | Applies every session; cross-cutting |
| Cross-project working-style rules | **Stayed in global**, condensed | Same |
| Infrastructure side-project docs | **New project repo `~/<your-infra-repo>/CLAUDE.md`** + companion files | Auto-loads only when working in that subtree |
| Bug-numbers + architecture details | Same project repo's CLAUDE.md | Same |
| Security hardening status checklist | **`~/<your-infra-repo>/STATUS.md`** | Frequently-changing state, Anthropic's explicit anti-pattern for CLAUDE.md |
| Active work-tracks roadmap | **`~/<your-infra-repo>/PLANS.md`** | Planning state |
| Second side-project architecture | **That project's own CLAUDE.md** | Project-scoped |
| Integration-setup runbook | **New skill `~/.claude/skills/<setup-skill>/SKILL.md`** | Multi-step procedure; loads on demand |
| Provider-auth-fix runbook | **Skill `~/.claude/skills/<ops-skill>/SKILL.md`** | Same |
| Operational commands cheatsheet | **`~/<your-infra-repo>/USEFUL-COMMANDS.md`** | Single-command reference, not instruction |
| Cross-cutting do-not rules | **Stayed in global** | Apply every session |
| Project-specific do-not rules | **Moved to relevant project CLAUDE.md** | Apply only in that project's territory |
| Scaling research notes | **Deleted** | Notes for the author, not instructions for the AI |
| Custom-skills directory listing | **Deleted** | Skills auto-discover; the list went stale |
| Dated update log | **Deleted** | Replaced by `git log` on the new project repos |

---

## End state: the slim global

| Metric | Before | After | Change |
|---|---:|---:|---:|
| Lines | ~540 | ~62 | **−88%** |
| Bytes | ~36,000 | ~6,500 | **−82%** |
| Tokens (rough estimate) | ~10,000 | ~1,500 | **−85%** |
| Context window consumed by global at session start (200k window) | ~5% | ~0.75% | **~6× freed** |
| Sections | 14+ (sprawling) | 8 (focused) | Halved |
| Procedural content in global | Multiple embedded runbooks (~150 lines) | 0 | Moved to skills |
| Frequently-changing state in global | ~100 lines | 0 | Moved to dedicated files / git |

## The shape of the slim global

Eight sections, ~62 lines total:

1. **Who I am**: identity paragraph; how to engage with the user
2. **How I want you to work**: 10–12 cross-cutting working-style bullets
3. **Environment**: OS, shell, default model (~3 lines)
4. **Hard rules**: 4–6 cross-project, no-exceptions rules
5. **Quality bar**: Pass 1 (always-run fact-check) inline + Pass 2 (recipient-POV review) as a one-line skill pointer
6. **General mistakes to avoid**: 3–5 generalizable failure-log entries
7. **Where project-specific context lives**: pointer table to project repos and skills
8. **Long-form personal records**: pointers to journals, auto-memory

---

## What you can expect for your own case

The exact numbers will differ. What generalizes:

- **The ratio.** Going from `<a sprawling everything-file>` to `<a slim router>` typically lands in the 5-10× range on bytes and tokens. This case (~8.7× on lines, ~5.5× on bytes) is mid-range, not extreme.
- **The distribution of moves.** Most line-count lands in project CLAUDE.mds (the workhorses). A smaller share but disproportionate value lands in skills (loaded on demand). A slice gets deleted outright (changelogs, redundant lists, notes that were never instruction).
- **The qualitative shift in sessions.** Cleaner main thread. Skills fire when relevant. Project context auto-loads when you `cd` into a project. Cross-cutting rules are not buried under hundreds of lines of project-specific text.
- **What you'll likely notice within days.** Faster responses at session start (less to read). Higher adherence to rules Claude had been missing. Cleaner outputs (less context-mixing across unrelated projects). Auto-compaction triggers later in long sessions.

---

## What does *not* generalize

- **Your file's content.** This case was a specific person's specific work. Yours will have completely different sections, projects, and rules.
- **The specific destinations.** The author had two side-projects and a set of project-scoped skills. You might have one project, or ten; you might need three skills, or zero.
- **The order in which sections were cut.** This case had a large infrastructure section that dominated the bloat. Yours might be dominated by client work, by a single overgrown procedure, or by stale changelog entries.

What transfers exactly is the **methodology**: the seven phases and the eight principles. The specific file you produce is yours.
