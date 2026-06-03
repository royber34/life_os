# Install the cold-eye-review skill into ~/.claude/skills/.
#
# One-liner usage:
#   irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/cold-eye-review/install.ps1 | iex
#
# What this does:
#   1. Verifies ~/.claude/ exists (Claude Code is installed).
#   2. Creates ~/.claude/skills/cold-eye-review/.
#   3. Downloads the skill body (SKILL.md) from the repo.
#   4. Prompts before overwriting if the skill is already installed.
#
# After install, in any Claude Code session, ask:
#   "cold-eye review this before I send it"

$ErrorActionPreference = "Stop"

$Base = "https://raw.githubusercontent.com/royber34/life_os/main/playbooks/cold-eye-review/skill"
$Dest = Join-Path $env:USERPROFILE ".claude\skills\cold-eye-review"
$Files = @("SKILL.md")

Write-Host "Installing the cold-eye-review skill..." -ForegroundColor Cyan

# Pre-flight: Claude Code installed?
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
if (-not (Test-Path $ClaudeDir)) {
  Write-Host "ERROR: $ClaudeDir does not exist. Is Claude Code installed?" -ForegroundColor Red
  exit 1
}

if (Test-Path $Dest) {
  $resp = Read-Host "Note: cold-eye-review already exists. Overwrite? [y/N]"
  if ($resp -notmatch "^[Yy]$") {
    Write-Host "Skipping (existing install left unchanged)."
    exit 0
  }
}

Write-Host "Installing cold-eye-review ..."
foreach ($f in $Files) {
  $out = Join-Path $Dest ($f -replace '/', '\')
  $dir = Split-Path $out -Parent
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  try {
    Invoke-WebRequest -Uri "$Base/$f" -OutFile $out -UseBasicParsing -ErrorAction Stop
  } catch {
    Write-Host "ERROR: download failed for $f : $($_.Exception.Message)" -ForegroundColor Red
    exit 1
  }
  if (-not (Test-Path $out) -or (Get-Item $out).Length -eq 0) {
    Write-Host "ERROR: download appears empty: $f" -ForegroundColor Red
    exit 1
  }
}

Write-Host ""
Write-Host "Installed into $Dest" -ForegroundColor Green
Write-Host ""
Write-Host "Next: in any Claude Code session, ask:"
Write-Host "  'cold-eye review this before I send it'"
Write-Host ""
Write-Host "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/cold-eye-review"
