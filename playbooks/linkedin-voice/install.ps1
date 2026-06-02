# Install the linkedin-voice skills (analyzer + guideline writer) into ~/.claude/skills/.
#
# One-liner usage:
#   irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/linkedin-voice/install.ps1 | iex
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

$ErrorActionPreference = "Stop"

$Base = "https://raw.githubusercontent.com/royber34/life_os/main/playbooks/linkedin-voice/skills"
$Dest = Join-Path $env:USERPROFILE ".claude\skills"

# Ordered so the analyzer installs first.
$SkillOrder = @("linkedin-profile-tov-analyzer", "linkedin-postwriter-guideline-writer")
$Files = @{
  "linkedin-profile-tov-analyzer" = @(
    "SKILL.md",
    "scripts/stylometry.py",
    "references/ingestion.md",
    "references/voice-taxonomy.md",
    "templates/analysis-template.md",
    "templates/voice-profile.schema.json"
  )
  "linkedin-postwriter-guideline-writer" = @(
    "SKILL.md",
    "scripts/lint_post.py",
    "references/ai-tells-banlist.md",
    "references/linkedin-writing-principles.md",
    "references/self-check-protocol.md",
    "templates/guideline-template.md"
  )
}

Write-Host "Installing the linkedin-voice skills..." -ForegroundColor Cyan

# Pre-flight: Claude Code installed?
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
if (-not (Test-Path $ClaudeDir)) {
  Write-Host "ERROR: $ClaudeDir does not exist. Is Claude Code installed?" -ForegroundColor Red
  exit 1
}

foreach ($skill in $SkillOrder) {
  $skillDir = Join-Path $Dest $skill

  if (Test-Path $skillDir) {
    $resp = Read-Host "Note: $skill already exists. Overwrite? [y/N]"
    if ($resp -notmatch "^[Yy]$") {
      Write-Host "Skipping $skill (existing install left unchanged)."
      continue
    }
  }

  Write-Host "Installing $skill ..."
  foreach ($f in $Files[$skill]) {
    $out = Join-Path $skillDir ($f -replace '/', '\')
    $dir = Split-Path $out -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    try {
      Invoke-WebRequest -Uri "$Base/$skill/$f" -OutFile $out -UseBasicParsing -ErrorAction Stop
    } catch {
      Write-Host "ERROR: download failed for $skill/$f : $($_.Exception.Message)" -ForegroundColor Red
      exit 1
    }
    if (-not (Test-Path $out) -or (Get-Item $out).Length -eq 0) {
      Write-Host "ERROR: download appears empty: $skill/$f" -ForegroundColor Red
      exit 1
    }
  }
}

Write-Host ""
Write-Host "Installed into $Dest" -ForegroundColor Green
Write-Host ""
Write-Host "Next: in any Claude Code session, ask:"
Write-Host "  'analyze my LinkedIn voice'               (builds your voice profile)"
Write-Host "  'turn my voice profile into a guideline'  (writes the copywriter guide)"
Write-Host ""
Write-Host "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/linkedin-voice"
