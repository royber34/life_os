# restore.ps1 — hash-verified restore of CLAUDE.md and related config files
#
# Usage:
#   .\restore.ps1                # restore any files that are missing or differ from backup
#   .\restore.ps1 -WhatIf        # preview what would change, make no edits
#   .\restore.ps1 -Force         # skip the prompt when a target file has diverged
#
# What it does:
#   - Iterates over a fixed mapping of (backup-path -> target-path) pairs.
#   - For each pair, compares SHA256 of backup vs. target.
#   - If target is missing OR matches backup, restores silently (idempotent).
#   - If target exists AND differs from backup, prompts before overwriting.
#   - The mapping list below is the source of truth — edit it to suit your setup.
#
# Why hash-verify: prevents stomping on a file the user has edited since the
# backup was taken. The prompt is the last line of defense against data loss.

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$Force
)

# <!-- TODO: customize this list for your files -->
# Each entry: @{ Backup = "path/to/backup"; Target = "path/to/restore/to" }
# Paths can use $env:USERPROFILE, $PSScriptRoot, or absolute paths.
$restoreMap = @(
    @{
        Backup = Join-Path $PSScriptRoot "backup\global-CLAUDE.md"
        Target = Join-Path $env:USERPROFILE ".claude\CLAUDE.md"
    },
    @{
        Backup = Join-Path $PSScriptRoot "backup\settings.json"
        Target = Join-Path $env:USERPROFILE ".claude\settings.json"
    }
    # Add more entries here. Example:
    # @{
    #     Backup = Join-Path $PSScriptRoot "backup\project-CLAUDE.md"
    #     Target = Join-Path $env:USERPROFILE "Repositories\<your-project>\CLAUDE.md"
    # }
)

function Get-FileHashSafe {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

$summary = @{ Restored = 0; Skipped = 0; SkippedByUser = 0; Missing = 0 }

foreach ($entry in $restoreMap) {
    $backup = $entry.Backup
    $target = $entry.Target

    if (-not (Test-Path -LiteralPath $backup)) {
        Write-Warning "Backup not found: $backup"
        $summary.Missing++
        continue
    }

    $backupHash = Get-FileHashSafe -Path $backup
    $targetHash = Get-FileHashSafe -Path $target

    if ($null -ne $targetHash -and $targetHash -eq $backupHash) {
        Write-Verbose "Match, skipping: $target"
        $summary.Skipped++
        continue
    }

    if ($null -ne $targetHash -and -not $Force) {
        Write-Host ""
        Write-Host "DIVERGED: $target" -ForegroundColor Yellow
        Write-Host "  backup hash: $backupHash"
        Write-Host "  target hash: $targetHash"
        $answer = Read-Host "Overwrite with backup? [y/N]"
        if ($answer -notmatch '^[Yy]') {
            Write-Host "  skipped by user"
            $summary.SkippedByUser++
            continue
        }
    }

    $targetDir = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $targetDir)) {
        if ($PSCmdlet.ShouldProcess($targetDir, "Create directory")) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
    }

    if ($PSCmdlet.ShouldProcess($target, "Restore from $backup")) {
        Copy-Item -LiteralPath $backup -Destination $target -Force
        Write-Host "Restored: $target" -ForegroundColor Green
        $summary.Restored++
    }
}

Write-Host ""
Write-Host "Done. Restored: $($summary.Restored)  Skipped (match): $($summary.Skipped)  Skipped (user): $($summary.SkippedByUser)  Missing backups: $($summary.Missing)"
