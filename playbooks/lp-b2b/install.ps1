# Install the lp-b2b skills (page builder + review) into ~/.claude/skills/.
#
# One-liner usage:
#   irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/lp-b2b/install.ps1 | iex
#
# What this does:
#   1. Verifies ~/.claude/ exists (Claude Code is installed).
#   2. Creates ~/.claude/skills/<skill>/ for both skills.
#   3. Downloads each skill's files (SKILL.md, references, scripts) from the repo.
#   4. Prompts before overwriting if a skill is already installed.
#      To update without a prompt (for example when Claude Code runs it), set LP_B2B_OVERWRITE=1:
#        $env:LP_B2B_OVERWRITE = "1"; irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/lp-b2b/install.ps1 | iex
#
# After install, in a Claude Code session started in your page's folder, ask:
#   "build me a landing page for my offer"    (the builder)
#   "review my landing page as a cold buyer"  (the review)

# Wrapped in a script block so 'return' stops the install without closing
# the PowerShell window when run via 'irm ... | iex'.
& {
  $ErrorActionPreference = "Stop"

  $Base = "https://raw.githubusercontent.com/royber34/life_os/main/playbooks/lp-b2b/skills"
  $Dest = Join-Path $env:USERPROFILE ".claude\skills"

  # Ordered so the builder installs first.
  $SkillOrder = @("lp-b2b", "lp-b2b-review")
  $Files = @{
    "lp-b2b" = @(
      "SKILL.md",
      "references/brief-questions.md",
      "references/templates.md",
      "references/style.md",
      "references/stage-page.md",
      "references/stage-build.md",
      "references/golive-checklist.md",
      "scripts/check_page.py",
      "scripts/og_card.py"
    )
    "lp-b2b-review" = @(
      "SKILL.md",
      "references/rubric.md",
      "references/personas.md",
      "references/fix-brief-template.md",
      "references/prompts/visitor-quick.md",
      "references/prompts/visitor-full.md",
      "references/prompts/compliance.md",
      "references/prompts/designer.md",
      "references/prompts/judge-ab.md",
      "scripts/capture.py",
      "scripts/lint.py",
      "scripts/scoreboard.py"
    )
  }

  Write-Host "Installing the lp-b2b skills..." -ForegroundColor Cyan

  # Pre-flight: Claude Code installed?
  $ClaudeDir = Join-Path $env:USERPROFILE ".claude"
  if (-not (Test-Path $ClaudeDir)) {
    Write-Host "ERROR: $ClaudeDir does not exist. Is Claude Code installed?" -ForegroundColor Red
    return
  }

  foreach ($skill in $SkillOrder) {
    $skillDir = Join-Path $Dest $skill

    if (Test-Path $skillDir) {
      $overwrite = ($env:LP_B2B_OVERWRITE -eq "1")
      if (-not $overwrite) {
        # Read-Host throws when there is no console to ask (for example when Claude Code runs this).
        try {
          $resp = Read-Host "Note: $skill already exists. Overwrite? [y/N]"
          $overwrite = ($resp -match "^[Yy]$")
        } catch {
          Write-Host "No terminal for confirmation. To update, run again with `$env:LP_B2B_OVERWRITE = `"1`"."
        }
      }
      if (-not $overwrite) {
        Write-Host "Skipping $skill (existing install left unchanged)."
        continue
      }
      # Remove the old copy so files dropped in a newer version don't linger.
      Remove-Item -Recurse -Force $skillDir
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
        return
      }
      if (-not (Test-Path $out) -or (Get-Item $out).Length -eq 0) {
        Write-Host "ERROR: download appears empty: $skill/$f" -ForegroundColor Red
        return
      }
    }
  }

  Write-Host ""
  Write-Host "Installed into $Dest" -ForegroundColor Green
  Write-Host ""
  Write-Host "Next: start a NEW Claude Code session in your page's folder (a session that was already open won't see the new skills) and ask:"
  Write-Host "  'build me a landing page for my offer'    (starts with the key questions)"
  Write-Host "  'review my landing page as a cold buyer'  (the review on its own)"
  Write-Host ""
  Write-Host "Screenshots and page checks use Python with Playwright and Pillow:"
  Write-Host "  pip install playwright pillow; playwright install chromium"
  Write-Host ""
  Write-Host "Full playbook: https://github.com/royber34/life_os/tree/main/playbooks/lp-b2b"
}
