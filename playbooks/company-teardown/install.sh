#!/usr/bin/env bash
#
# Install the company-teardown skill into ~/.claude/skills/.
#
# One-liner usage:
#   curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/company-teardown/install.sh | bash
#
# What this does:
#   1. Verifies ~/.claude/ exists (Claude Code is installed).
#   2. Creates ~/.claude/skills/company-teardown/.
#   3. Downloads the skill files from the repo.
#   4. Prompts before overwriting if the skill is already installed.
#
# After install, in any Claude Code session, ask:
#   "do a company teardown of [company]"

set -euo pipefail

BASE="https://raw.githubusercontent.com/royber34/life_os/main/playbooks/company-teardown/skill"
DEST="$HOME/.claude/skills/company-teardown"
FILES="SKILL.md
example/treg-2026-10-28/README.md
example/treg-2026-10-28/bundle-sample.json
references/agent-brief-common.md
references/intake-questions.md
references/moves.md
references/performance-briefs.md
references/insights.md
references/presentation.md
references/review-panel.md
references/probe.md
references/schemas.md
references/style.md
references/synthesis.md
references/targets.md
references/templates.md
references/treg.md
references/verification.md
references/workstreams.md
scripts/build_dashboard.py
scripts/cost_report.py
scripts/campaign_impact.py
scripts/ledger.py
scripts/merge_events.py
scripts/render_test.py
scripts/watch.py
template/competition.js
template/core.js
template/d3.LICENSE.txt
template/d3.v7.min.js
template/dash.css
template/gtm.js
template/index.html
template/library.js
template/market.js
template/moves.js
template/impact.js
template/shim.js
template/timeline.js"

echo "Installing the company-teardown skill..."

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
    read -p "Overwrite company-teardown? [y/N] " -n 1 -r REPLY < /dev/tty || REPLY=""
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

echo "Installing company-teardown ..."
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
echo "  'do a company teardown of [company]'"
echo ""
echo "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/company-teardown"
