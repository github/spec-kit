#!/usr/bin/env pwsh
# Git extension: auto-commit.ps1
# Automatically commit changes after a Spec Kit command completes.
# Checks per-command config keys in git-config.yml before committing.
#
# Usage: auto-commit.ps1 <event_name> [generated_message]
#        auto-commit.ps1 <event_name> -MessageFile <path>
#   e.g.: auto-commit.ps1 after_specify
#   e.g.: auto-commit.ps1 after_specify -MessageFile C:\temp\commit-msg.txt  (commit_style: conventional)
#
# -MessageFile is the preferred way to supply an agent-generated commit
# message: it reads the message from a file instead of a shell argument,
# so message content (which may contain quotes, $(...), backticks, etc.)
# is never interpolated into a shell command line.
param(
    [Parameter(Position = 0, Mandatory = $true)]
    [string]$EventName,

    # Optional agent-generated commit message (used when commit_style: conventional is configured).
    # Prefer -MessageFile over passing the message directly as a shell argument.
    [Parameter(Position = 1, Mandatory = $false)]
    [string]$GeneratedMessage = "",

    [Parameter(Mandatory = $false)]
    [string]$MessageFile = ""
)
$ErrorActionPreference = 'Stop'

if ($MessageFile) {
    if (-not (Test-Path $MessageFile -PathType Leaf)) {
        Write-Warning "[specify] Error: message file '$MessageFile' not found"
        exit 1
    }
    $GeneratedMessage = (Get-Content -Path $MessageFile -Raw)
    if ($null -ne $GeneratedMessage) {
        $GeneratedMessage = $GeneratedMessage.TrimEnd("`r", "`n")
    }
    # The message file is a transport-only artifact: its content is now
    # captured above, so remove it immediately. Otherwise, if it was written
    # inside the worktree, it would be picked up as an untracked change by
    # both the "any changes?" check below and by `git add .`, polluting the
    # commit or defeating the no-changes short-circuit even when nothing
    # else changed.
    Remove-Item -Path $MessageFile -Force -ErrorAction SilentlyContinue
}

function Find-ProjectRoot {
    param([string]$StartDir)
    $current = Resolve-Path $StartDir
    while ($true) {
        foreach ($marker in @('.specify', '.git')) {
            if (Test-Path (Join-Path $current $marker)) {
                return $current
            }
        }
        $parent = Split-Path $current -Parent
        if ($parent -eq $current) { return $null }
        $current = $parent
    }
}

$repoRoot = Find-ProjectRoot -StartDir $PSScriptRoot
if (-not $repoRoot) { $repoRoot = Get-Location }
Set-Location $repoRoot

# Check if git is available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Warning "[specify] Warning: Git not found; skipped auto-commit"
    exit 0
}

# Temporarily relax ErrorActionPreference so git stderr warnings
# (e.g. CRLF notices on Windows) do not become terminating errors.
$savedEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    git rev-parse --is-inside-work-tree 2>$null | Out-Null
    $isRepo = $LASTEXITCODE -eq 0
} finally {
    $ErrorActionPreference = $savedEAP
}
if (-not $isRepo) {
    Write-Warning "[specify] Warning: Not a Git repository; skipped auto-commit"
    exit 0
}

# Read per-command config from git-config.yml
$configFile = Join-Path $repoRoot ".specify/extensions/git/git-config.yml"
$enabled = $false
$commitMsg = ""
$commitStyle = "fixed"

if (Test-Path $configFile) {
    # Top-level scalar key: commit_style (fixed | conventional)
    foreach ($line in Get-Content $configFile) {
        if ($line -match '^commit_style:\s*(.+)$') {
            $styleVal = (($matches[1] -replace '\s+#.*$', '').Trim()) -replace '^["'']' -replace '["'']$'
            if ($styleVal) {
                $styleVal = $styleVal.ToLower()
                if ($styleVal -eq 'fixed' -or $styleVal -eq 'conventional') {
                    $commitStyle = $styleVal
                } else {
                    Write-Warning "[specify] Warning: unknown commit_style '$styleVal' in git-config.yml (expected 'fixed' or 'conventional'); defaulting to 'fixed'"
                }
            }
            break
        }
    }

    # Parse YAML to find auto_commit section
    $inAutoCommit = $false
    $inEvent = $false
    $defaultEnabled = $false

    foreach ($line in Get-Content $configFile) {
        # Detect auto_commit: section
        if ($line -match '^auto_commit:') {
            $inAutoCommit = $true
            $inEvent = $false
            continue
        }

        # Exit auto_commit section on next top-level key
        if ($inAutoCommit -and $line -match '^[a-z]') {
            break
        }

        if ($inAutoCommit) {
            # Check default key
            if ($line -match '^\s+default:\s*(.+)$') {
                $val = $matches[1].Trim().ToLower()
                if ($val -eq 'true') { $defaultEnabled = $true }
            }

            # Detect our event subsection
            if ($line -match "^\s+${EventName}:") {
                $inEvent = $true
                continue
            }

            # Inside our event subsection
            if ($inEvent) {
                # Exit on next sibling key (2-space indent, not 4+)
                if ($line -match '^\s{2}[a-z]' -and $line -notmatch '^\s{4}') {
                    $inEvent = $false
                    continue
                }
                if ($line -match '\s+enabled:\s*(.+)$') {
                    $val = $matches[1].Trim().ToLower()
                    if ($val -eq 'true') { $enabled = $true }
                    if ($val -eq 'false') { $enabled = $false }
                }
                if ($line -match '\s+message:\s*(.+)$') {
                    $commitMsg = $matches[1].Trim() -replace '^["'']' -replace '["'']$'
                }
            }
        }
    }

    # If event-specific key not found, use default
    if (-not $enabled -and $defaultEnabled) {
        $hasEventKey = Select-String -Path $configFile -Pattern "^\s*${EventName}:" -Quiet
        if (-not $hasEventKey) {
            $enabled = $true
        }
    }
} else {
    # No config file -- auto-commit disabled by default
    exit 0
}

if (-not $enabled) {
    exit 0
}

# Check if there are changes to commit
# Relax ErrorActionPreference so CRLF warnings on stderr do not terminate.
$savedEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    git diff --quiet HEAD 2>$null; $d1 = $LASTEXITCODE
    git diff --cached --quiet 2>$null; $d2 = $LASTEXITCODE
    $untracked = git ls-files --others --exclude-standard 2>$null
} finally {
    $ErrorActionPreference = $savedEAP
}

if ($d1 -eq 0 -and $d2 -eq 0 -and -not $untracked) {
    Write-Host "[specify] No changes to commit after $EventName" -ForegroundColor DarkGray
    exit 0
}

# In conventional mode, the commit message must be supplied by the agent
# (via the GeneratedMessage argument); never fall back to the fixed message.
if ($commitStyle -eq 'conventional') {
    if ($GeneratedMessage) {
        $commitMsg = $GeneratedMessage
    } else {
        Write-Warning "[specify] Error: commit_style is 'conventional' but no generated commit message was supplied; aborting auto-commit (pass -MessageFile <path>, or a raw message as arg 2, or set commit_style: fixed)"
        exit 1
    }
}

# Derive a human-readable command name from the event
$commandName = $EventName -replace '^after_', '' -replace '^before_', ''
$phase = if ($EventName -match '^before_') { 'before' } else { 'after' }

# Use custom message if configured, otherwise default
if (-not $commitMsg) {
    $commitMsg = "[Spec Kit] Auto-commit $phase $commandName"
}

# Stage and commit
# Relax ErrorActionPreference so CRLF warnings on stderr do not terminate,
# while still allowing redirected error output to be captured for diagnostics.
$savedEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    $out = git add . 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { throw "git add failed: $out" }
    $out = git commit -q -m $commitMsg 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { throw "git commit failed: $out" }
} catch {
    Write-Warning "[specify] Error: $_"
    exit 1
} finally {
    $ErrorActionPreference = $savedEAP
}

Write-Host "[OK] Changes committed $phase $commandName"
