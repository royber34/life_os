# Install the home-exchange-listing skill into ~/.claude/skills/.
#
# One-liner usage:
#   irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/home-exchange-listing/install.ps1 | iex
#
# What this does:
#   1. Verifies ~/.claude/ exists (Claude Code is installed).
#   2. Creates ~/.claude/skills/home-exchange-listing/.
#   3. Downloads the skill (SKILL.md, the home-facts template, the platform notes).
#   4. Prompts before overwriting if the skill is already installed.
#
# After install, in a Claude Code session started in your place's folder, ask:
#   "set up my home exchange listing"

# Wrapped in a script block so 'return' stops the install without closing
# the PowerShell window when run via 'irm ... | iex'.
& {
  $ErrorActionPreference = "Stop"

  $Base = "https://raw.githubusercontent.com/royber34/life_os/main/playbooks/home-exchange-listing/skill"
  $Dest = Join-Path $env:USERPROFILE ".claude\skills\home-exchange-listing"
  $Files = @("SKILL.md", "templates/home-facts.md", "references/platform-notes.md")

  Write-Host "Installing the home-exchange-listing skill..." -ForegroundColor Cyan

  # Pre-flight: Claude Code installed?
  $ClaudeDir = Join-Path $env:USERPROFILE ".claude"
  if (-not (Test-Path $ClaudeDir)) {
    Write-Host "ERROR: $ClaudeDir does not exist. Is Claude Code installed?" -ForegroundColor Red
    return
  }

  if (Test-Path $Dest) {
    $resp = Read-Host "Note: home-exchange-listing already exists. Overwrite? [y/N]"
    if ($resp -notmatch "^[Yy]$") {
      Write-Host "Skipping (existing install left unchanged)."
      return
    }
  }

  Write-Host "Installing home-exchange-listing ..."
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
  Write-Host "Next: in a Claude Code session started in your place's folder, ask:"
  Write-Host "  'set up my home exchange listing'"
  Write-Host ""
  Write-Host "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/home-exchange-listing"
}
