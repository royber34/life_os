#!/usr/bin/env bash
#
# Install the cold-eye-review skill into ~/.claude/skills/.
#
# One-liner usage:
#   curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/cold-eye-review/install.sh | bash
#
# What this does:
#   1. Verifies ~/.claude/ exists (Claude Code is installed).
#   2. Creates ~/.claude/skills/cold-eye-review/.
#   3. Downloads the skill body (SKILL.md) from the repo.
#   4. Prompts before overwriting if the skill is already installed.
#
# After install, in any Claude Code session, ask:
#   "cold-eye review this before I send it"

set -euo pipefail

BASE="https://raw.githubusercontent.com/royber34/life_os/main/playbooks/cold-eye-review/skill"
DEST="$HOME/.claude/skills/cold-eye-review"
FILES="SKILL.md"

echo "Installing the cold-eye-review skill..."

# Pre-flight: Claude Code installed?
if [ ! -d "$HOME/.claude" ]; then
  echo "ERROR: $HOME/.claude does not exist. Is Claude Code installed?" >&2
  exit 1
fi

fetch() {
  # fetch <url> <out>
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$1" -o "$2"
  elif command -v wget >/dev/null 2>&1; then
    wget -q "$1" -O "$2"
  else
    echo "ERROR: need curl or wget on PATH" >&2
    exit 1
  fi
}

if [ -d "$DEST" ]; then
  echo "Note: $DEST already exists."
  if [ -e /dev/tty ]; then
    read -p "Overwrite cold-eye-review? [y/N] " -n 1 -r REPLY < /dev/tty || REPLY=""
    echo
    if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
      echo "Skipping (existing install left unchanged)."
      exit 0
    fi
  else
    echo "No terminal for confirmation; skipping. Remove it first to reinstall."
    exit 0
  fi
fi

echo "Installing cold-eye-review ..."
for f in $FILES; do
  mkdir -p "$DEST/$(dirname "$f")"
  fetch "$BASE/$f" "$DEST/$f"
  if [ ! -s "$DEST/$f" ]; then
    echo "ERROR: download appears empty: $f" >&2
    exit 1
  fi
done

echo ""
echo "Installed into $DEST/"
echo ""
echo "Next: in any Claude Code session, ask:"
echo "  'cold-eye review this before I send it'"
echo ""
echo "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/cold-eye-review"
