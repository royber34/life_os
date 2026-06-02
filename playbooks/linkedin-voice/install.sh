#!/usr/bin/env bash
#
# Install the linkedin-voice skills (analyzer + guideline writer) into ~/.claude/skills/.
#
# One-liner usage:
#   curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/linkedin-voice/install.sh | bash
#
# What this does:
#   1. Verifies ~/.claude/ exists (Claude Code is installed).
#   2. Creates ~/.claude/skills/<skill>/ for both skills.
#   3. Downloads each skill's files (SKILL.md, scripts, references, templates) from the repo.
#   4. Prompts before overwriting if a skill is already installed.
#
# After install, in any Claude Code session, ask:
#   "analyze my LinkedIn voice"               (the analyzer)
#   "turn my voice profile into a guideline"  (the writer)

set -euo pipefail

BASE="https://raw.githubusercontent.com/royber34/life_os/main/playbooks/linkedin-voice/skills"
DEST="$HOME/.claude/skills"

ANALYZER="linkedin-profile-tov-analyzer"
ANALYZER_FILES="SKILL.md scripts/stylometry.py references/ingestion.md references/voice-taxonomy.md templates/analysis-template.md templates/voice-profile.schema.json"

WRITER="linkedin-postwriter-guideline-writer"
WRITER_FILES="SKILL.md scripts/lint_post.py references/ai-tells-banlist.md references/linkedin-writing-principles.md references/self-check-protocol.md templates/guideline-template.md"

echo "Installing the linkedin-voice skills..."

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

install_skill() {
  local skill="$1"
  local files="$2"

  if [ -d "$DEST/$skill" ]; then
    echo "Note: $DEST/$skill already exists."
    if [ -e /dev/tty ]; then
      read -p "Overwrite $skill? [y/N] " -n 1 -r REPLY < /dev/tty || REPLY=""
      echo
      if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
        echo "Skipping $skill (existing install left unchanged)."
        return 0
      fi
    else
      echo "No terminal for confirmation; skipping $skill. Remove it first to reinstall."
      return 0
    fi
  fi

  echo "Installing $skill ..."
  for f in $files; do
    mkdir -p "$DEST/$skill/$(dirname "$f")"
    fetch "$BASE/$skill/$f" "$DEST/$skill/$f"
    if [ ! -s "$DEST/$skill/$f" ]; then
      echo "ERROR: download appears empty: $skill/$f" >&2
      exit 1
    fi
  done
}

install_skill "$ANALYZER" "$ANALYZER_FILES"
install_skill "$WRITER" "$WRITER_FILES"

echo ""
echo "Installed into $DEST/"
echo ""
echo "Next: in any Claude Code session, ask:"
echo "  'analyze my LinkedIn voice'               (builds your voice profile)"
echo "  'turn my voice profile into a guideline'  (writes the copywriter guide)"
echo ""
echo "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/linkedin-voice"
