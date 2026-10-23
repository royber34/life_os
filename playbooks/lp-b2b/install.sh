#!/usr/bin/env bash
#
# Install the lp-b2b skills (page builder + review) into ~/.claude/skills/.
#
# One-liner usage:
#   curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/lp-b2b/install.sh | bash
#
# What this does:
#   1. Verifies ~/.claude/ exists (Claude Code is installed).
#   2. Creates ~/.claude/skills/<skill>/ for both skills.
#   3. Downloads each skill's files (SKILL.md, references, scripts) from the repo.
#   4. Prompts before overwriting if a skill is already installed.
#      To update without a prompt (for example when Claude Code runs it), set LP_B2B_OVERWRITE=1:
#        curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/lp-b2b/install.sh | LP_B2B_OVERWRITE=1 bash
#
# After install, in a Claude Code session started in your page's folder, ask:
#   "build me a landing page for my offer"    (the builder)
#   "review my landing page as a cold buyer"  (the review)

set -euo pipefail

BASE="https://raw.githubusercontent.com/royber34/life_os/main/playbooks/lp-b2b/skills"
DEST="$HOME/.claude/skills"

BUILDER="lp-b2b"
BUILDER_FILES="SKILL.md references/brief-questions.md references/templates.md references/style.md references/stage-page.md references/stage-build.md references/golive-checklist.md scripts/check_page.py scripts/og_card.py"

REVIEW="lp-b2b-review"
REVIEW_FILES="SKILL.md references/rubric.md references/personas.md references/fix-brief-template.md references/prompts/visitor-quick.md references/prompts/visitor-full.md references/prompts/compliance.md references/prompts/designer.md references/prompts/judge-ab.md scripts/capture.py scripts/lint.py scripts/scoreboard.py"

echo "Installing the lp-b2b skills..."

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
    if [ "${LP_B2B_OVERWRITE:-}" != "1" ]; then
      REPLY=""
      if [ -e /dev/tty ]; then
        read -p "Overwrite $skill? [y/N] " -n 1 -r REPLY < /dev/tty 2>/dev/null || REPLY=""
        echo
      else
        echo "No terminal for confirmation. To update, run again with LP_B2B_OVERWRITE=1."
      fi
      if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
        echo "Skipping $skill (existing install left unchanged)."
        return 0
      fi
    fi
    # Remove the old copy so files dropped in a newer version don't linger.
    rm -rf "${DEST:?}/$skill"
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

install_skill "$BUILDER" "$BUILDER_FILES"
install_skill "$REVIEW" "$REVIEW_FILES"

echo ""
echo "Installed into $DEST/"
echo ""
echo "Next: start a NEW Claude Code session in your page's folder (a session that was already open won't see the new skills) and ask:"
echo "  'build me a landing page for my offer'    (starts with the key questions)"
echo "  'review my landing page as a cold buyer'  (the review on its own)"
echo ""
echo "Screenshots and page checks use Python with Playwright and Pillow:"
echo "  pip install playwright pillow && playwright install chromium"
echo ""
echo "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/lp-b2b"
