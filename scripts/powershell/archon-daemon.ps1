#!/usr/bin/env pwsh
# Archon Background Sync Daemon - Optional Periodic Synchronization (PowerShell)
# CRITICAL: This script is for ADVANCED USERS ONLY
# CRITICAL: This script MUST be completely silent (no stdout/stderr)
# CRITICAL: NOT started automatically, NOT documented for regular users

# Usage: pwsh archon-daemon.ps1 <feature-dir> [interval-seconds]
# Example: pwsh archon-daemon.ps1 /path/to/specs/001-feature 300

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $PSCommandPath
. (Join-Path $scriptDir "archon-common.ps1")

# Feature directory passed as argument
$featureDir = $args[0]
$syncInterval = if ($args[1]) { [int]$args[1] } else { 300 }  # Default: 5 minutes (300 seconds)

if (-not $featureDir) {
    exit 1  # Require feature directory
}

# Validate interval (must be positive integer)
if ($syncInterval -lt 60) {
    exit 1  # Minimum 60 seconds to avoid hammering
}

# Extract feature name
$featureName = Get-FeatureName -FeatureDir $featureDir

if (-not $featureName) {
    exit 1  # Feature name required
}

# Check if Archon MCP available
if (-not (Test-ArchonAvailable)) {
    exit 0  # MCP not available, exit gracefully
}

# Check if project exists
$projectId = Get-ProjectMapping -FeatureName $featureName
if (-not $projectId) {
    exit 0  # No project, nothing to sync
}

# Create PID file to prevent multiple daemons
$stateDir = Get-ArchonStateDir
$pidFile = Join-Path $stateDir "${featureName}.daemon.pid"

try {
    if (-not (Test-Path $stateDir)) {
        New-Item -ItemType Directory -Path $stateDir -Force -ErrorAction SilentlyContinue | Out-Null
    }
} catch {
    exit 1
}

# Check if daemon already running
if (Test-Path $pidFile) {
    try {
        $oldPid = Get-Content -Path $pidFile -Raw -ErrorAction SilentlyContinue | ForEach-Object { $_.Trim() }
        if ($oldPid) {
            $process = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
            if ($process) {
                # Daemon already running, exit silently
                exit 0
            }
        }
    } catch {
        # Process not found or error checking, continue
    }
}

# Write current PID
try {
    $PID | Out-File -FilePath $pidFile -NoNewline -Force -ErrorAction Stop
} catch {
    exit 1
}

# Cleanup function to remove PID file on exit
$cleanup = {
    try {
        if (Test-Path $pidFile) {
            Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
        }
    } catch {
        # Silently handle cleanup errors
    }
}

# Register cleanup on exit
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action $cleanup | Out-Null

try {
    # Background sync loop (completely silent)
    while ($true) {
        # Pull status from Archon (silent, with defensive error handling)
        try {
            & pwsh -NoProfile -File (Join-Path $scriptDir "archon-auto-pull-status.ps1") $featureDir 2>$null
        } catch {
            # Silently handle errors
        }

        # Sync documents if they exist (silent, with defensive error handling)
        if (Test-Path $featureDir) {
            try {
                & pwsh -NoProfile -File (Join-Path $scriptDir "archon-sync-documents.ps1") $featureDir "pull" 2>$null
            } catch {
                # Silently handle errors
            }
        }

        # Sleep for interval
        try {
            Start-Sleep -Seconds $syncInterval
        } catch {
            break
        }
    }
} finally {
    # Cleanup PID file
    & $cleanup
}

# Exit silently
exit 0
