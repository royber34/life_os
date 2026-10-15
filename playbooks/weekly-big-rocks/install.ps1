# Install the weekly-big-rocks skill into ~/.claude/skills/.
#
# One-liner usage:
#   irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/weekly-big-rocks/install.ps1 | iex
#
# What this does:
#   1. Verifies ~/.claude/ exists (Claude Code is installed).
#   2. Creates ~/.claude/skills/weekly-big-rocks/.
#   3. Downloads the skill (SKILL.md, the north-star template, the connector gotchas).
#   4. Prompts before overwriting if the skill is already installed.
#
# After install, in any Claude Code session, ask:
#   "plan my big rocks for next week"

# Wrapped in a script block so 'return' stops the install without closing
# the PowerShell window when run via 'irm ... | iex'.
& {
  $ErrorActionPreference = "Stop"

  $Base = "https://raw.githubusercontent.com/royber34/life_os/main/playbooks/weekly-big-rocks/skill"
  $Dest = Join-Path $env:USERPROFILE ".claude\skills\weekly-big-rocks"
  $Files = @("SKILL.md", "templates/north-star.md", "references/connector-gotchas.md")

  Write-Host "Installing the weekly-big-rocks skill..." -ForegroundColor Cyan

  # Pre-flight: Claude Code installed?
  $ClaudeDir = Join-Path $env:USERPROFILE ".claude"
  if (-not (Test-Path $ClaudeDir)) {
    Write-Host "ERROR: $ClaudeDir does not exist. Is Claude Code installed?" -ForegroundColor Red
    return
  }

  if (Test-Path $Dest) {
    $resp = Read-Host "Note: weekly-big-rocks already exists. Overwrite? [y/N]"
    if ($resp -notmatch "^[Yy]$") {
      Write-Host "Skipping (existing install left unchanged)."
      return
    }
  }

  Write-Host "Installing weekly-big-rocks ..."
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
  Write-Host "  'plan my big rocks for next week'"
  Write-Host ""
  Write-Host "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/weekly-big-rocks"
}
