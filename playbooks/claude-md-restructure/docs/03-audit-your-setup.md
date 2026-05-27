# Audit your setup

This is where the restructure starts to feel concrete. You've done the research pass and have a reference file with principles and citations. Now you turn that lens on your own setup. The audit produces one deliverable: a per-file table showing every section of every CLAUDE.md file you have, classified as KEEP, MOVE, or DELETE, with a target destination for anything that's moving.

Budget one to three hours. The audit is the longest single phase of the restructure, but it's where most of the value is created. If you skip it, you'll cut blindly. If you do it well, the actual restructure is mechanical.

## Goal of the audit

For every CLAUDE.md file on your machine, every section gets classified into one of three buckets:

- **KEEP**: it's a standing cross-cutting rule at the right scope. Stays where it is.
- **MOVE**: it's useful but in the wrong place. Move to a skill, a project CLAUDE.md, a README, or another doc.
- **DELETE**: it's state, stale, duplicated, or fails the "would removing this cause Claude to make mistakes" test.

Every section gets an explicit verdict. No section gets to remain by default. This is the discipline.

## Discovery: find every CLAUDE.md you have

You probably have more CLAUDE.md files than you remember. Discovery is the first move.

On PowerShell (Windows):

```powershell
# Global and project CLAUDE.mds in common locations
Get-ChildItem -Path $env:USERPROFILE -Recurse -Force `
  -Include CLAUDE.md, CLAUDE.local.md, MEMORY.md `
  -ErrorAction SilentlyContinue |
  Select-Object FullName, Length, LastWriteTime
```

On bash/zsh (macOS, Linux, WSL):

```bash
# Same discovery, POSIX style
find ~ -type f \( -name 'CLAUDE.md' -o -name 'CLAUDE.local.md' -o -name 'MEMORY.md' \) \
  2>/dev/null | xargs -I {} wc -l {}
```

If you're using Claude Code's Glob tool directly inside a session:

```
**/CLAUDE.md
**/CLAUDE.local.md
**/MEMORY.md
```

Run all three patterns. List the results sorted by size descending. The biggest files are usually the ones with the most work to do.

A few things to expect:

- A global at `~/.claude/CLAUDE.md` (the one this playbook is mostly about).
- One or more project-level CLAUDE.mds in your code directories.
- Auto-memory files at `~/.claude/projects/<some-encoded-path>/memory/MEMORY.md`. These are written by Claude Code itself; they're not the same shape as CLAUDE.md and follow different rules. Note them but don't restructure them; the harness manages them.
- Possibly orphans: CLAUDE.mds in old project directories you haven't touched in months. These still load when you cd into them. Worth noting.

## The classification framework

For every section in every file you found, walk through the framework below. The categories overlap a little, and that's fine; assign to the dominant category.

### State

**Definition:** Content that describes the current status of something. It was true when you wrote it; it may not be true now; it'll definitely change.

**Examples:**
- "Currently migrating database from MySQL to Postgres, expected completion Q3."
- A task list with checkboxes.
- "Project X is on hold pending the customer's response."
- A changelog of what got done last sprint.

**Verdict:** DELETE from CLAUDE.md. State doesn't belong in a file the model reads on every turn. Move task lists to your actual task tracker. Move project status to project docs. Auto-memory is the right place for transient state (the harness manages it; you don't have to).

**Why:** State decays. The moment it's stale, it's actively misleading; Claude reads it as current truth and acts on outdated information.

### Procedures

**Definition:** Multi-step recipes. "To do X, first do A, then B, then C, with these caveats."

**Examples:**
- "Deploy checklist for the main API"
- "Steps to debug a failing CI job"
- "How to cut a new release: bump version, tag, push, verify CI, post to changelog"
- "Database backup procedure for the staging environment"

**Verdict:** MOVE to a skill. Claude Code skills are the right home for procedural content; they're loaded on demand, not on every turn, and they can be parameterized.

A 30-line procedure in your global CLAUDE.md costs you 30 lines of context on every conversation, even when you're not running that procedure. The same procedure as a skill costs you one line in the skill index and zero lines in CLAUDE.md until you invoke it.

**Why:** Procedures are exactly the use case skills were designed for. Procedural content in CLAUDE.md is a category mistake.

### Reference content

**Definition:** Encyclopedic context. Architecture documentation, API descriptions, tool inventories, glossaries.

**Examples:**
- "Our backend has three services: API gateway, worker queue, notification dispatcher..."
- "Here are the columns in our `users` table: id, email, created_at..."
- A list of MCP servers you've configured and what they do.

**Verdict:** MOVE to a README, a docs file, or a project CLAUDE.md with a pointer rather than the content itself. Replace the section in your global with a one-liner: `For service architecture, see backend/README.md.`

**Why:** Reference content scales badly. Once you've documented one architecture, you'll want to document another, and another. CLAUDE.md grows linearly with the number of things you reference. README files are the right place for "stable facts about a codebase."

### Standing rules

**Definition:** Cross-cutting preferences about how you want Claude to behave, that apply across projects.

**Examples:**
- "Never push to a remote without asking."
- "Use PowerShell syntax on Windows; bash is also available."
- "Find root causes, not bandaids."
- "Match scope to the ask; don't refactor things I didn't ask you to touch."

**Verdict:** KEEP at the right scope. Cross-cutting rules go in the global. Project-specific conventions go in the project CLAUDE.md (e.g., "in this repo, all SQL identifiers are snake_case").

**Why:** This is what CLAUDE.md is *for*. Boris's own file is mostly standing rules. The signal-to-noise ratio is high.

### Failure-log entries

**Definition:** "Last time you forgot X, don't forget it again" notes. The accumulation of corrections over time.

**Examples:**
- "When writing PowerShell here-strings, never indent the closing `'@`."
- "Don't use `cat >` on a shell; it silently overwrites."
- "For MCP calls into a specific tool, always use the configured account, not the default."

**Verdict:** KEEP, but organize by scope, and prune ruthlessly. Cross-cutting failures (PowerShell syntax) belong in global. Project-specific failures (a particular API quirk) belong in that project's CLAUDE.md. Failures specific to a procedure should live in the skill for that procedure, not in CLAUDE.md.

**Why:** Failure logs are high-signal; they encode mistakes you've already made and want to prevent. But left uncurated, they accumulate forever. Every few months, re-read them and cut the ones that no longer apply (e.g., the underlying tool fixed the bug, or you've internalized the rule and don't need it written down).

## The "triple-duplicate" pattern

One of the highest-value findings the audit surfaces is duplication.

Claude Code loads CLAUDE.md files hierarchically: it walks up the directory tree from your current working directory and concatenates every CLAUDE.md it finds, then layers the global on top. If you have nested project structures, this means deep cwds load multiple files simultaneously.

The triple-duplicate pattern looks like this. You have:

- `~/.claude/CLAUDE.md`: global, contains "Always run tests before committing."
- `~/code/CLAUDE.md`: top of your code dir, also contains "Always run tests before committing."
- `~/code/some-project/CLAUDE.md`: same line again.

When you cd into `~/code/some-project/`, Claude Code loads all three. The instruction appears three times. Triple-duplicates dilute the rest of the file and waste tokens, and they're surprisingly common; you forget you wrote it at one level and add it again at another.

How to find them: after discovery, grep for distinctive phrases across all your CLAUDE.mds.

```powershell
Select-String -Path (Get-ChildItem -Path $env:USERPROFILE -Recurse -Force `
  -Include CLAUDE.md -ErrorAction SilentlyContinue).FullName `
  -Pattern "run tests before committing" -SimpleMatch
```

```bash
grep -rn "run tests before committing" $(find ~ -name 'CLAUDE.md' 2>/dev/null)
```

Pick five or six load-bearing rules from your global and grep each one. If any rule appears more than once across files, you've found duplication. Decide which level it should live at (usually the highest applicable scope) and delete it from the others.

## Global vs project duplicates

The other common duplication pattern: the same content in the global and in a project file, where the project file was created later as a "just in case" copy. Same fix: pick the right scope, delete the duplicates.

A useful heuristic: if a rule applies to every project you work on, it's global. If it applies to a single repo, it's project. If you're not sure, ask: "Would I want this rule active when I'm working on something completely unrelated?" If yes, global. If no, project.

## The audit deliverable

Produce a per-file table. Plain markdown is fine. Don't over-engineer the format; the goal is a working document, not a published artifact.

Suggested columns:

| Section | File | Lines | Category | Verdict | Target destination |
| --- | --- | --- | --- | --- | --- |
| "Backend service architecture" | `~/code/backend/CLAUDE.md` | 12-44 | Reference content | MOVE | `~/code/backend/README.md` |
| "Deploy checklist" | `~/.claude/CLAUDE.md` | 230-310 | Procedure | MOVE | new skill: `deploy-checklist` |
| "Current Q3 migration status" | `~/.claude/CLAUDE.md` | 410-450 | State | DELETE | n/a |
| "Match scope to the ask" | `~/.claude/CLAUDE.md` | 50-58 | Standing rule | KEEP | n/a |
| "PowerShell here-string fix" | `~/.claude/CLAUDE.md` | 600-605 | Failure-log | KEEP | n/a (already global-scoped, applies broadly) |

One row per section. Resist the urge to skip "obvious keeps"; the discipline of explicit verdicts is the point. When you're done, you should be able to look at any line in any of your CLAUDE.md files and point to its row in the table.

## The decision tree

When you're stuck on a section, walk this in order:

1. **Is it state?** (Status, task list, changelog.) → DELETE.
2. **Is it a procedure?** (Multi-step recipe.) → MOVE to a skill.
3. **Is it reference content?** (Architecture, API, encyclopedia.) → MOVE to README/docs, leave a pointer.
4. **Is it duplicated at a higher scope?** → DELETE from the lower scope.
5. **Is it duplicated at a lower scope?** → DELETE from the higher scope if it's truly scoped to one project.
6. **Does it pass "would removing this cause Claude to make mistakes"?** If no → DELETE. If yes → continue.
7. **Is it at the right scope?** Global rule in global? Project rule in project? If no, MOVE.
8. **Else** → KEEP.

Most sections will be classifiable in under thirty seconds with this tree. The hard cases are the ones that pass the mistake test but might be in the wrong file; those are worth more thought, since the wrong-file failure mode (the rule fires when it shouldn't) is often worse than the missing-rule failure mode (the rule doesn't fire when it should).

When the audit is complete and you have a table covering every file, you're ready to back up, build the skills you flagged, move the project content, and stage the new global. Those phases are mechanical compared to this one.
