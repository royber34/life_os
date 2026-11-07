# Install the company-teardown skill into ~/.claude/skills/.
#
# One-liner usage:
#   irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/company-teardown/install.ps1 | iex
#
# What this does:
#   1. Verifies ~/.claude/ exists (Claude Code is installed).
#   2. Creates ~/.claude/skills/company-teardown/.
#   3. Downloads the skill files from the repo.
#   4. Prompts before overwriting if the skill is already installed.
#
# After install, in any Claude Code session, ask:
#   "do a company teardown of [company]"

# Wrapped in a script block so 'return' stops the install without closing
# the PowerShell window when run via 'irm ... | iex'.
& {
  $ErrorActionPreference = "Stop"

  $Base = "https://raw.githubusercontent.com/royber34/life_os/main/playbooks/company-teardown/skill"
  $Dest = Join-Path $env:USERPROFILE ".claude\skills\company-teardown"
  $Files = @(
    "SKILL.md",
    "example/treg-2026-10-28/README.md",
    "example/treg-2026-10-28/bundle-sample.json",
    "references/agent-brief-common.md",
    "references/geo-ai.md",
    "references/intake-questions.md",
    "references/moves.md",
    "references/performance-briefs.md",
    "references/insights.md",
    "references/presentation.md",
    "references/review-panel.md",
    "references/probe.md",
    "references/schemas.md",
    "references/style.md",
    "references/synthesis.md",
    "references/targets.md",
    "references/templates.md",
    "references/treg.md",
    "references/verification.md",
    "references/workstreams.md",
    "scripts/build_dashboard.py",
    "scripts/cost_report.py",
    "scripts/campaign_impact.py",
    "scripts/ledger.py",
    "scripts/merge_events.py",
    "scripts/render_test.py",
    "scripts/watch.py",
    "template/ai.js",
    "template/compare.js",
    "template/competition.js",
    "template/core.js",
    "template/d3.LICENSE.txt",
    "template/d3.v7.min.js",
    "template/dash.css",
    "template/gtm.js",
    "template/index.html",
    "template/library.js",
    "template/market.js",
    "template/moves.js",
    "template/impact.js",
    "template/shim.js",
    "template/timeline.js"
  )

  Write-Host "Installing the company-teardown skill..." -ForegroundColor Cyan

  # Pre-flight: Claude Code installed?
  $ClaudeDir = Join-Path $env:USERPROFILE ".claude"
  if (-not (Test-Path $ClaudeDir)) {
    Write-Host "ERROR: $ClaudeDir does not exist. Is Claude Code installed?" -ForegroundColor Red
    return
  }

  if (Test-Path $Dest) {
    $resp = Read-Host "Note: company-teardown already exists. Overwrite? [y/N]"
    if ($resp -notmatch "^[Yy]$") {
      Write-Host "Skipping (existing install left unchanged)."
      return
    }
  }

  Write-Host "Installing company-teardown ..."
  foreach ($f in $Files) {
    $out = Join-Path $Dest ($f -replace '/', '\')
    $dir = Split-Path $out -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    try {
      Invoke-WebRequest -Uri "$Base/$f" -OutFile $out -UseBasicParsing -ErrorAction Stop
    } catch {
      Write-Host "ERROR: download failed for $f : $($_.Exception.Message)" -ForegroundColor Red
      return
    }
    if (-not (Test-Path $out) -or (Get-Item $out).Length -eq 0) {
      Write-Host "ERROR: download appears empty: $f" -ForegroundColor Red
      return
    }
  }

  Write-Host ""
  Write-Host "Installed into $Dest" -ForegroundColor Green
  Write-Host ""
  Write-Host "Next: in any Claude Code session, ask:"
  Write-Host "  'do a company teardown of [company]'"
  Write-Host ""
  Write-Host "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/company-teardown"
}
