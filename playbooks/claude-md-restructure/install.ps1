# Install the claude-md-restructure skill into ~/.claude/skills/.
#
# One-liner usage:
#   irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/claude-md-restructure/install.ps1 | iex
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

$ErrorActionPreference = "Stop"

$SkillName  = "claude-md-restructure"
$SkillUrl   = "https://raw.githubusercontent.com/royber34/life_os/main/playbooks/claude-md-restructure/skill/SKILL.md"
$TargetDir  = Join-Path $env:USERPROFILE ".claude\skills\$SkillName"
$TargetFile = Join-Path $TargetDir "SKILL.md"

Write-Host "Installing the $SkillName skill..." -ForegroundColor Cyan

# Pre-flight: Claude Code installed?
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
if (-not (Test-Path $ClaudeDir)) {
  Write-Host "ERROR: $ClaudeDir does not exist. Is Claude Code installed?" -ForegroundColor Red
  exit 1
}

# Check for collision
if (Test-Path $TargetFile) {
  Write-Host "Note: $TargetFile already exists." -ForegroundColor Yellow
  $resp = Read-Host "Overwrite? [y/N]"
  if ($resp -notmatch "^[Yy]$") {
    Write-Host "Aborted. Existing skill left unchanged."
    exit 0
  }
}

# Create target directory
if (-not (Test-Path $TargetDir)) {
  New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

# Download SKILL.md
Write-Host "Downloading SKILL.md from $SkillUrl ..."
try {
  Invoke-WebRequest -Uri $SkillUrl -OutFile $TargetFile -UseBasicParsing -ErrorAction Stop
} catch {
  Write-Host "ERROR: download failed: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
}

# Verify the download is non-empty
if (-not (Test-Path $TargetFile) -or (Get-Item $TargetFile).Length -eq 0) {
  Write-Host "ERROR: download appears empty" -ForegroundColor Red
  if (Test-Path $TargetFile) { Remove-Item $TargetFile -Force }
  exit 1
}

Write-Host ""
Write-Host "Installed: $TargetFile" -ForegroundColor Green
Write-Host ""
Write-Host "Next: in any Claude Code session, ask:"
Write-Host "  'restructure my CLAUDE.md'"
Write-Host "  'audit my CLAUDE.md'"
Write-Host "  'my CLAUDE.md is bloated'"
Write-Host "or similar. The skill walks you through the seven phases with safety gates."
Write-Host ""
Write-Host "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/claude-md-restructure"
