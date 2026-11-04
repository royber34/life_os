#!/usr/bin/env bash
#
# Install the ai-result-check skill into ~/.claude/skills/.
#
# One-liner usage:
#   curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/ai-result-check/install.sh | bash
#
# What this does:
#   1. Verifies ~/.claude/ exists (Claude Code is installed).
#   2. Creates ~/.claude/skills/ai-result-check/.
#   3. Downloads the skill body (SKILL.md) from the repo.
#   4. Prompts before overwriting if the skill is already installed.
#
# After install, in any Claude Code session, ask:
#   "check this AI result before I rely on it"

set -euo pipefail

BASE="https://raw.githubusercontent.com/royber34/life_os/main/playbooks/ai-result-check/skill"
DEST="$HOME/.claude/skills/ai-result-check"
FILES="SKILL.md"

echo "Installing the ai-result-check skill..."

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
    read -p "Overwrite ai-result-check? [y/N] " -n 1 -r REPLY < /dev/tty || REPLY=""
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

echo "Installing ai-result-check ..."
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
echo "  'check this AI result before I rely on it'"
echo ""
echo "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/ai-result-check"
