#!/usr/bin/env bash
# restore.sh — hash-verified restore of CLAUDE.md and related config files
#
# Usage:
#   ./restore.sh                  # restore any files that are missing or differ from backup
#   ./restore.sh --dry-run        # preview what would change, make no edits
#   ./restore.sh --force          # skip the prompt when a target file has diverged
#
# What it does:
#   - Iterates over a fixed mapping of (backup-path -> target-path) pairs.
#   - For each pair, compares SHA256 of backup vs. target.
#   - If target is missing OR matches backup, restores silently (idempotent).
#   - If target exists AND differs from backup, prompts before overwriting.
#   - The mapping list below is the source of truth — edit it to suit your setup.
#
# Works on Linux (sha256sum) and macOS (shasum -a 256).

set -euo pipefail

DRY_RUN=0
FORCE=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --force)   FORCE=1 ;;
        -h|--help)
            sed -n '2,15p' "$0"; exit 0 ;;
        *) echo "Unknown arg: $arg" >&2; exit 2 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Pick the right SHA256 tool.
if command -v sha256sum >/dev/null 2>&1; then
    sha256() { sha256sum "$1" | awk '{print $1}'; }
elif command -v shasum >/dev/null 2>&1; then
    sha256() { shasum -a 256 "$1" | awk '{print $1}'; }
else
    echo "ERROR: need sha256sum or shasum on PATH" >&2
    exit 1
fi

# <!-- TODO: customize this list for your files -->
# Each entry: "BACKUP_PATH|TARGET_PATH"
# Use $HOME and $SCRIPT_DIR as needed.
restore_map=(
    "$SCRIPT_DIR/backup/global-CLAUDE.md|$HOME/.claude/CLAUDE.md"
    "$SCRIPT_DIR/backup/settings.json|$HOME/.claude/settings.json"
    # Add more entries here. Example:
    # "$SCRIPT_DIR/backup/project-CLAUDE.md|$HOME/Repositories/<your-project>/CLAUDE.md"
)

restored=0; skipped=0; skipped_user=0; missing=0

for entry in "${restore_map[@]}"; do
    backup="${entry%%|*}"
    target="${entry##*|}"

    if [[ ! -f "$backup" ]]; then
        echo "WARN: backup not found: $backup" >&2
        missing=$((missing+1))
        continue
    fi

    backup_hash=$(sha256 "$backup")
    if [[ -f "$target" ]]; then
        target_hash=$(sha256 "$target")
    else
        target_hash=""
    fi

    if [[ -n "$target_hash" && "$target_hash" == "$backup_hash" ]]; then
        skipped=$((skipped+1))
        continue
    fi

    if [[ -n "$target_hash" && $FORCE -eq 0 ]]; then
        echo ""
        echo "DIVERGED: $target"
        echo "  backup hash: $backup_hash"
        echo "  target hash: $target_hash"
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "  (dry-run) would prompt; treating as 'skip'"
            skipped_user=$((skipped_user+1))
            continue
        fi
        read -r -p "Overwrite with backup? [y/N] " answer
        if [[ ! "$answer" =~ ^[Yy]$ ]]; then
            echo "  skipped by user"
            skipped_user=$((skipped_user+1))
            continue
        fi
    fi

    target_dir="$(dirname "$target")"
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "(dry-run) would restore: $target"
    else
        mkdir -p "$target_dir"
        cp -f "$backup" "$target"
        echo "Restored: $target"
    fi
    restored=$((restored+1))
done

echo ""
echo "Done. Restored: $restored  Skipped (match): $skipped  Skipped (user): $skipped_user  Missing backups: $missing"
