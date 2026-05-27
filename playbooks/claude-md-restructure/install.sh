#!/usr/bin/env bash
#
# Install the claude-md-restructure skill into ~/.claude/skills/.
#
# One-liner usage:
#   curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/claude-md-restructure/install.sh | bash
#
# What this does:
#   1. Verifies ~/.claude/ exists (Claude Code is installed).
#   2. Creates ~/.claude/skills/claude-md-restructure/ if missing.
#   3. Downloads SKILL.md from the repo into that directory.
#   4. Prompts before overwriting if a previous install exists.
#
# After install, in any Claude Code session, ask:
#   "restructure my CLAUDE.md"
#   "audit my CLAUDE.md"
#   "my CLAUDE.md is bloated"
# and the skill will fire.

set -euo pipefail

SKILL_NAME="claude-md-restructure"
SKILL_URL="https://raw.githubusercontent.com/royber34/life_os/main/playbooks/claude-md-restructure/skill/SKILL.md"
TARGET_DIR="$HOME/.claude/skills/$SKILL_NAME"
TARGET_FILE="$TARGET_DIR/SKILL.md"

echo "Installing the $SKILL_NAME skill..."

# Pre-flight: Claude Code installed?
if [ ! -d "$HOME/.claude" ]; then
  echo "ERROR: $HOME/.claude does not exist. Is Claude Code installed?" >&2
  exit 1
fi

# Check for collision with an existing install
if [ -f "$TARGET_FILE" ]; then
  echo "Note: $TARGET_FILE already exists."
  if [ -t 0 ] || [ -e /dev/tty ]; then
    if [ -e /dev/tty ]; then
      read -p "Overwrite? [y/N] " -n 1 -r REPLY < /dev/tty || REPLY=""
    else
      read -p "Overwrite? [y/N] " -n 1 -r REPLY || REPLY=""
    fi
    echo
    if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
      echo "Aborted. Existing skill left unchanged."
      exit 0
    fi
  else
    echo "No terminal available for confirmation. Skipping overwrite. Re-run with a TTY or remove the existing file first."
    exit 0
  fi
fi

# Create target directory
mkdir -p "$TARGET_DIR"

# Download SKILL.md
echo "Downloading SKILL.md from $SKILL_URL ..."
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$SKILL_URL" -o "$TARGET_FILE"
elif command -v wget >/dev/null 2>&1; then
  wget -q "$SKILL_URL" -O "$TARGET_FILE"
else
  echo "ERROR: need curl or wget on PATH" >&2
  exit 1
fi

# Verify the download is non-empty
if [ ! -s "$TARGET_FILE" ]; then
  echo "ERROR: download appears empty" >&2
  rm -f "$TARGET_FILE"
  exit 1
fi

echo ""
echo "Installed: $TARGET_FILE"
echo ""
echo "Next: in any Claude Code session, ask:"
echo "  'restructure my CLAUDE.md'"
echo "  'audit my CLAUDE.md'"
echo "  'my CLAUDE.md is bloated'"
echo "or similar. The skill walks you through the seven phases with safety gates."
echo ""
echo "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/claude-md-restructure"
