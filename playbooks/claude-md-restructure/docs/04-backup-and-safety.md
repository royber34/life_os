# 04 — Backup and safety

Restructuring your global `CLAUDE.md` is a high-stakes edit. That file is loaded into the context of every Claude Code session you start. If you break it, every session is broken until you fix it — and "fix it" without a backup means rebuilding from memory under pressure.

This phase exists so the rest of the work can be aggressive without being reckless. Treat it as non-optional.

## Why backup first

File changes are reversible only if you can revert them. There is no undo button for a file you overwrote three sessions ago and forgot about. The restructure work involves:

- Moving content out of the global file into skills.
- Moving content out of the global file into project-level `CLAUDE.md` files.
- Deleting content that fails the "would removing this cause mistakes" test.
- Re-ordering, re-grouping, and re-writing what stays.

Any one of those steps can introduce a regression that you only notice three days later when Claude does something subtly wrong. A clean, hash-verified backup is what lets you say "this used to work — here's what it used to look like" without ambiguity.

## The backup pattern

Use a date-stamped directory under `~/.claude/backups/`, with three components inside it:

```
~/.claude/backups/YYYY-MM-DD-pre-restructure/
  MANIFEST.md              # human-readable index of what's backed up
  restore.ps1              # idempotent PowerShell restore script
  restore.sh               # idempotent bash restore script
  files/                   # mirrored original paths
    Users/<you>/.claude/CLAUDE.md
    Users/<you>/.claude/projects/.../MEMORY.md
    ...
```

Three components, three jobs. `MANIFEST.md` is what you read six months from now when you've forgotten what's in here. The restore scripts are what you run when you need to roll back. The `files/` subdirectory is the actual content.

## What to back up

Back up everything Claude Code reads automatically at session start, plus anything you're about to modify:

- Every `CLAUDE.md` (global at `~/.claude/CLAUDE.md`, and project-level ones inside your project trees).
- Every `CLAUDE.local.md` (machine-local overrides, often forgotten).
- Every `MEMORY.md` under `~/.claude/projects/` (auto-memory captured by Claude over time).

Skip the rest unless you're modifying it in this restructure:

- `settings.json` — only back up if you're editing settings.
- Skills (`~/.claude/skills/`) — only back up if you're rewriting existing skills, not when you're authoring new ones.
- Plugins, hooks, MCP configs — only if you're touching them.

The principle: back up the inputs to the restructure, not your entire Claude Code installation.

## The mirror-path layout

Store each backed-up file under its full original path inside `files/`. This makes the backup self-documenting — you can read the directory tree and know exactly where every file came from without consulting the manifest.

```
files/
  Users/
    <you>/
      .claude/
        CLAUDE.md
        CLAUDE.local.md
        projects/
          some-project/
            CLAUDE.md
            memory/
              MEMORY.md
          another-project/
            CLAUDE.md
```

This matters for restore. When the restore script walks `files/`, every file it finds already knows where it belongs. No mapping table, no fragile lookups.

## SHA256 verification at every step

Hashes are how you prove that the bytes you backed up are the bytes you restore. Without them you have a copy operation that you hope worked.

Capture the hash at backup time:

```powershell
# PowerShell
Get-FileHash -Algorithm SHA256 "$HOME\.claude\CLAUDE.md" | Select-Object Hash, Path
```

```bash
# bash
sha256sum ~/.claude/CLAUDE.md
```

Record each hash in `MANIFEST.md` alongside the file entry. When `restore.ps1` runs, it should:

1. Read the recorded hash for each file from the manifest.
2. Hash the current live file at the target path.
3. If the live hash matches the backed-up hash, the file hasn't changed since backup — restore is a no-op.
4. If the live hash differs, prompt before overwriting: "Live file has changed since this backup was taken. Overwrite anyway? [y/N]".

That prompt is what saves you from blowing away three days of post-restructure work because you ran the restore script by reflex.

## The MANIFEST.md content

Treat the manifest as the document you'd hand to a stranger (including future you) to explain what this backup is. It should contain:

- **Header.** Date the backup was taken. Reason ("pre-restructure of global CLAUDE.md"). File count. Total size.
- **Index table.** One row per backed-up file: backup path → original path → file size → SHA256 hash.
- **Restore instructions, three ways.**
  - The Claude prompt: paste this prompt into a Claude Code session and it'll walk the restore. ("Read `<manifest path>` and restore every file listed to its original path. Hash-verify before overwriting. Prompt me if any target file has drifted since backup.")
  - The PowerShell one-liner: `& "<backup dir>\restore.ps1"`.
  - Single-file manual restore: `Copy-Item "<backup dir>\files\<path>" "<original path>" -Force`, with the warning to hash-check first.
- **Embedded restore script copy.** Paste the contents of `restore.ps1` and `restore.sh` into the manifest itself as a fenced code block. If the script files are ever lost, the manifest still contains the recipe.

## The "extra safety snapshot" pattern

Phase 6 (staging the new global as `.proposed`) → Phase 7 (atomic swap) is where the actual cutover happens. The master backup is your insurance policy for catastrophic recovery, but it's overkill for the most recent edit you made five minutes ago.

For the cutover specifically, take a pre-swap snapshot:

```powershell
# Before the atomic swap
Copy-Item "$HOME\.claude\CLAUDE.md" "$HOME\.claude\CLAUDE.md.pre-swap-$(Get-Date -Format yyyyMMdd-HHmmss)"
```

```bash
# Same idea in bash
cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.pre-swap-$(date +%Y%m%d-%H%M%S)
```

This is a single-step rollback: if the new live file misbehaves immediately after the swap, you can `Move-Item` the pre-swap snapshot back over the live file and you're done. No digging through a master backup, no running a script, no manifest lookup. One command.

## A two-tier rollback model

You now have two tiers of rollback, each scoped to a different kind of failure:

- **Tier 1: pre-swap snapshot.** For the most recent change (the swap itself, or any edit you made in the last few minutes). Single file, single command to restore. Use this 95% of the time.
- **Tier 2: master backup.** For catastrophic recovery — multiple files corrupted, multiple changes that need to unwind together, "I have no idea what state I'm in" panic mode. Slower, scripted, hash-verified. Use this when Tier 1 isn't enough.

Knowing which tier you're reaching for tells you how serious the problem is.

## Test your restore before you trust it

A backup you've never restored from is a backup you don't actually have. Before you start the restructure work in earnest:

1. Pick a low-stakes file from the backup (e.g., a small project `CLAUDE.md`, not the global).
2. Modify the live file slightly (add a comment line, save).
3. Run the restore script.
4. Confirm:
   - The script detected the live file had drifted.
   - The prompt appeared.
   - After accepting, the file was restored to the backed-up bytes.
   - Re-running the script is a no-op (idempotent — restore.ps1/restore.sh should re-hash, see match, and do nothing).

If any of those steps fail, fix the script before you proceed. The restore path is the one path you cannot afford to debug under stress.

## Templates

Working `restore.ps1` and `restore.sh` scripts that implement everything above — hash capture, drift detection, prompts, idempotent re-runs — are in `templates/`. Copy them into your backup directory and edit the file list to match what you backed up.

## What to do before Phase 4

By the time you exit this phase, you should have:

- A date-stamped backup directory with `files/`, `MANIFEST.md`, `restore.ps1`, `restore.sh`.
- SHA256 hashes recorded for every file in the manifest.
- A tested restore (you've actually run the script against a drifted file and watched it work).
- The location of the backup written down somewhere you'll find it under stress.

Now you can move fast.
