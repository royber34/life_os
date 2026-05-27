---
name: claude-md-restructure
description: Guided restructure of a bloated Claude Code global CLAUDE.md, applying the full methodology end to end. Use when the user says "restructure my CLAUDE.md", "shrink my CLAUDE.md", "audit my CLAUDE.md", "my CLAUDE.md is bloated", "my Claude Code feels slow", "my CLAUDE.md has grown too big", "fix my CLAUDE.md", "apply the CLAUDE.md restructure playbook", or "sharpen my CLAUDE.md". Walks the user through seven phases (research, audit, backup, build skills, move project content, stage proposed, atomic swap) with safety gates at each step. The user makes all judgment calls; the skill executes the mechanical work.
---

# CLAUDE.md Restructure (guided methodology)

This skill walks the user through the [claude-md-restructure playbook](https://github.com/royber34/life_os/tree/main/playbooks/claude-md-restructure) end to end. The skill executes the mechanical work (audit discovery, backup with hash verification, atomic swap, fresh-session test). The user makes the judgment calls (what to keep, what to move, what to delete). Every destructive action has a backup first, a hash check, and a one-command rollback.

## Operating principles for this skill

1. **Safety first, always.** No destructive action proceeds without an explicit user confirmation and a verified backup. If a gate fails verification, stop and report. Never silently work around a failed check.
2. **One phase at a time.** Each phase ends with a clear gate. The user must explicitly approve before the next phase starts. Do not chain phases automatically.
3. **The user decides; the skill executes.** When in doubt, surface the question. Don't infer intent on cuts, moves, or deletions.
4. **Reference the public docs.** The skill is the runner. Deeper context lives in [the playbook docs](https://github.com/royber34/life_os/tree/main/playbooks/claude-md-restructure/docs). When a user asks "why does this rule exist", point at the relevant doc, don't re-explain.
5. **Em-dash convention.** Per the playbook's style preference, never use em-dash characters in any output produced by this skill. Use commas, colons, parentheses, or restructured sentences instead. Hyphens and en-dashes (in number ranges) are fine.

## Pre-conditions

Confirm before starting:

- The user is running Claude Code locally (not a hosted session, not a sandbox).
- A global `~/.claude/CLAUDE.md` exists. If it does not, ask whether the user wants to create one from the playbook's `templates/global-claude-example.md` instead of running a full restructure.
- The user understands this skill modifies files. State explicitly: "This will modify your global CLAUDE.md and may create new files under `~/.claude/skills/`, `~/.claude/backups/`, and inside any project directories you choose to scope. Every change is backed up first, but proceed only if you are ready for me to do this now."

If any pre-condition is not met, stop and report. Do not start Phase 1.

## Phase 1: Research surface

**Goal:** Anchor the user's eventual cuts in citations, not opinions.

**Steps:**

1. Surface the eight principles from the playbook (read them from the public docs or summarize from memory):
   - "Would removing this cause Claude to make mistakes?" test (Boris Cherny's articulated test)
   - State doesn't belong in CLAUDE.md
   - Procedures don't belong in CLAUDE.md (use skills)
   - Reference content doesn't belong in CLAUDE.md (use README/docs)
   - Global file is a router, not a content dump
   - Failure-log discipline
   - Hierarchy is the auto-loader's job
   - Skills > CLAUDE.md bullets for procedural content
2. Offer the user the option to do their own deeper research pass (point at `docs/02-research-pass.md` in the playbook) or to skip and trust the playbook's research.
3. Explicitly state what the size targets are: under 200 lines per CLAUDE.md (Anthropic memory docs), ~100 lines as Boris Cherny's published baseline.

**Gate:** User confirms readiness to audit. Do not proceed otherwise.

## Phase 2: Audit your existing setup

**Goal:** Discover every CLAUDE.md and MEMORY.md across the filesystem, classify content, and produce a verdict per section.

**Steps:**

1. Run a discovery sweep using the Glob tool. Patterns to find:
   - `**/CLAUDE.md`
   - `**/CLAUDE.local.md`
   - `**/MEMORY.md` (limited to under `~/.claude/projects/`)
   Start from the user's home directory. If a discovery glob times out on a large home directory, narrow the scope by checking common project parent directories (e.g., `~/Repositories/`, `~/code/`, `~/projects/`, `~/clients/`) one at a time.
2. For each discovered file, report: full path, line count, byte count, last-modified date.
3. Read each file's top-level section headers (lines starting with `## `). For the global `~/.claude/CLAUDE.md`, also read full content.
4. Classify each section into one of three categories using the playbook's framework:
   - **KEEP**: cross-project standing rules, identity, values, hard rules, generalizable mistakes
   - **MOVE**: project-specific content (route to a project CLAUDE.md), procedural runbooks (route to a skill), reference docs (route to project README/architecture)
   - **DELETE**: status trackers, task lists, dated changelogs, redundant lists already covered by auto-discovery, research notes that are not instructional
5. Identify duplicates: same content appearing in the global plus one or more project files. Flag the "triple-duplicate" pattern explicitly: same content in nested project directories that all auto-load when the user `cd`s deep into that subtree.
6. Produce an audit table for the user with columns: file path, section header, line range, classification verdict, target destination (if MOVE), reasoning.

**Gate:** User reviews the audit table and explicitly approves or adjusts each verdict. Do not proceed without that review. If the user adjusts verdicts, update the table and re-show.

## Phase 3: Backup with hash verification

**Goal:** Make the entire restructure reversible with a single command.

**Steps:**

1. Generate a backup directory at `~/.claude/backups/YYYY-MM-DD-pre-restructure/` (use today's date, with a suffix if the directory already exists).
2. Inside, create a `files/` subdirectory mirroring the full original path of each file being backed up. For example, `~/.claude/CLAUDE.md` becomes `<backup_root>/files/C/Users/<user>/.claude/CLAUDE.md` on Windows or `<backup_root>/files/Users/<user>/.claude/CLAUDE.md` on macOS/Linux.
3. Copy every file flagged in the audit into its mirrored backup location.
4. Compute the SHA256 hash of each source file at copy time. Verify the backup matches: recompute the hash on the backup file and confirm equality. If any file fails hash verification, stop and report.
5. Generate a `MANIFEST.md` at the backup root containing: header (date, reason, total file count, total size), a table mapping every backup path to its original path with sizes, three restore options for the user (one-prompt-to-Claude, single-command, manual single-file), and an embedded copy of the restore script for reference.
6. Generate a `restore.ps1` (Windows) or `restore.sh` (macOS/Linux), or both if cross-platform. Use the templates at `playbooks/claude-md-restructure/templates/restore.ps1` and `restore.sh` as the structure. The script must be idempotent (skip files that already match), hash-verify before overwriting, and prompt before overwriting any file that has changed since backup.
7. Test the restore by running it with the `-WhatIf` (PowerShell) or `--dry-run` (bash) flag. Verify it correctly identifies that all targets match their backups (so nothing would be overwritten).

**Gate:** User confirms the backup completed cleanly (all hash checks passed) and the dry-run output looks right. Show the rollback command explicitly: "If anything goes wrong from here, run this single command to restore everything: `<command>`."

## Phase 4: Build skills for procedures

**Goal:** Pull every multi-step procedure out of the global CLAUDE.md into invokable skills.

**Steps:**

1. For each section the user classified as MOVE-to-skill in Phase 2, draft a skill scaffold:
   - Suggest a skill name in kebab-case (e.g., `deploy-checklist`, `billing-cooldown-fix`, `incident-response`).
   - Draft a frontmatter `description` that names trigger phrases the user is likely to use when they want the skill to fire. Be specific. Vague descriptions mean the skill never triggers.
   - Draft the body: pre-conditions, numbered steps with verification at each step, "Source:" attribution (where the procedure came from, so future-user knows what they trust), and a "what does NOT belong in this skill" footer.
2. For each drafted skill, show the user the full draft and confirm before writing. The user can adjust the name, description, or content.
3. Write each approved skill to `~/.claude/skills/<skill-name>/SKILL.md`. Verify the file was written and the skill becomes auto-discoverable (the next system reminder in the session should list it).

**Gate:** User confirms each skill draft individually. Skills are not batch-written without per-skill approval.

## Phase 5: Move project content to project CLAUDE.mds

**Goal:** Relocate project-specific content from the global to project-scoped CLAUDE.md files where it loads only when relevant.

**Steps:**

1. For each section the user classified as MOVE-to-project in Phase 2:
   - Confirm the target project directory exists (e.g., `~/Repositories/<project>/`).
   - Check whether a project-level CLAUDE.md already exists there. If yes, read it and propose where the new content should slot in (append, merge with existing section, or replace).
   - If no project CLAUDE.md exists, draft a new one using the structure from `templates/project-claude-example.md` in the playbook: orientation paragraph, folder structure, key cross-references table, conventions, do-not rules.
2. Surface each draft for user approval. The user reviews, adjusts, and confirms.
3. After approval, write the file. If the project repo is git-tracked, suggest committing the new project CLAUDE.md to version control so it travels with the repo.
4. If the audit revealed substantial infrastructure documentation that does not belong in a CLAUDE.md (architecture details, command cheatsheets, status trackers), propose creating companion files (`ARCHITECTURE.md`, `USEFUL-COMMANDS.md`, `STATUS.md`, `PLANS.md`) alongside the project CLAUDE.md. CLAUDE.md keeps cross-references pointing at these companion files. Frequently-changing state never goes inside CLAUDE.md.

**Gate:** User confirms each project file before write. Migration is destination-by-destination, not batch.

## Phase 6: Stage the new global as `.proposed`

**Goal:** Build the new slim global as a sibling file. Do not touch the live global yet.

**Steps:**

1. Draft the new global CLAUDE.md following the eight-section structure from `templates/global-claude-example.md`:
   - Who I am (identity, how to engage)
   - How I want you to work (cross-cutting working-style rules)
   - Environment (OS, shell, model defaults)
   - Hard rules (cross-project, no-exceptions)
   - Quality bar (Pass 1 always; Pass 2 as a skill pointer if a recipient-POV review skill exists)
   - General mistakes to avoid (failure log at global scope)
   - Where project-specific context lives (pointer table to project CLAUDE.mds and skills)
   - Long-form personal records (journals, auto-memory)
2. Pull rules from the user's existing global that the audit classified as KEEP. Discard everything else.
3. Add the failure-log discipline rule as an explicit bullet under "How I want you to work" if it is not already there. This is the mechanism that prevents the file from calcifying.
4. Write to `~/.claude/CLAUDE.md.proposed`. Do not touch the live `~/.claude/CLAUDE.md`.
5. Run a forward-reference pre-flight check. For every pointer in the proposed file (skill names like `<skill-name>` or paths like `~/Repositories/<project>/CLAUDE.md`), verify the referenced target exists. If any pointer is broken, stop and report which one. Fix before swap.
6. Show the user a structural diff of the proposed file against the current live file (sections gained, sections lost, line count change). Show byte count and estimated token count for both.

**Gate:** User reads the proposed file end-to-end and explicitly approves. The user can request edits at this stage. Loop until approved.

## Phase 7: Atomic swap + live verification

**Goal:** Replace the live global with the proposed file, with a single-command rollback ready if anything is wrong.

**Steps:**

1. Take an extra safety snapshot of the current live global: `Copy-Item ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.pre-swap-<timestamp>` (PowerShell) or `cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.pre-swap-<timestamp>` (bash). This snapshot is the fast-rollback path, independent of the master backup from Phase 3.
2. Capture the SHA256 hash of the proposed file before the swap.
3. Atomically swap: `Move-Item ~/.claude/CLAUDE.md.proposed ~/.claude/CLAUDE.md -Force` (PowerShell) or `mv ~/.claude/CLAUDE.md.proposed ~/.claude/CLAUDE.md` (bash).
4. Verify: recompute the SHA256 of the new live file. It must match the proposed-file hash captured before the swap. If it does not match, stop and report. Use the pre-swap snapshot to roll back if needed.
5. Verify the `.proposed` file no longer exists (it should have been moved cleanly).
6. Show the user the rollback command: `Move-Item <pre-swap-snapshot> ~/.claude/CLAUDE.md -Force` (PowerShell) or `mv <pre-swap-snapshot> ~/.claude/CLAUDE.md` (bash). This is the one-step rollback if the new global misbehaves.
7. Prompt the user to open a brand-new Claude Code session and run live verification prompts. Suggested prompts:
   - "What do you know about how I work?" (should reflect the slim global accurately)
   - "Help me push this code change" (should ask for explicit approval if the user has an external-approval hard rule)
   - "Draft a client follow-up email" or any externally-bound deliverable (should mention any recipient-POV review skill the user installed)
   - `cd` into a project that has its own CLAUDE.md and ask about the project (should load that project's CLAUDE.md correctly)
8. The user reports back: pass or fail. If pass, the restructure is complete. If fail, the rollback command is one step away.

**Gate:** Final user confirmation that the fresh-session test passed.

## Rollback at any phase

If any phase fails verification or the user wants to abort, stop immediately and report the rollback path:

- **Phases 1, 2:** No file changes yet. Nothing to roll back. Exit cleanly.
- **Phase 3 (backup created but nothing else changed):** No rollback needed. The backup is harmless. The user can delete it (`Remove-Item -Recurse <backup-dir>`) or keep it.
- **Phases 4, 5 (new files written, live global untouched):** Delete the new skill files or project CLAUDE.md files written this session. The live global is still the old one.
- **Phase 6 (proposed file staged, live global untouched):** Delete the `.proposed` file. `Remove-Item ~/.claude/CLAUDE.md.proposed`.
- **Phase 7 after swap:** Single-command rollback using the pre-swap snapshot. If that snapshot is somehow corrupt, fall back to the master backup from Phase 3: `& <backup-dir>/restore.ps1` or `bash <backup-dir>/restore.sh`.

## What this skill does NOT do

- **Does not run the research pass for the user.** Surfaces the principles and source list; the user reads if they want the deeper context. The full research is documented in `docs/02-research-pass.md`.
- **Does not make judgment calls on KEEP vs MOVE vs DELETE.** Suggests classifications; the user decides.
- **Does not auto-push changes to git.** Project CLAUDE.md files written to git-tracked repos are left uncommitted. The user commits when they are ready.
- **Does not modify settings.json, hooks, or other Claude Code configuration outside CLAUDE.md, skills, and project files.** Out of scope.
- **Does not run on hosted Claude environments or sandboxes.** Local Claude Code only. If pre-flight detects a hosted environment, stop and report.
- **Does not act as a maintenance schedule.** This is a "sharpening the pencil" skill: invoke it when the global file feels heavy. The skill itself does not run on a schedule.
