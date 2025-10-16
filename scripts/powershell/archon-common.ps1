#!/usr/bin/env pwsh
# Archon MCP Integration - Silent Utilities (PowerShell)
# CRITICAL: All functions in this file MUST be completely silent (no stdout/stderr)

# Silent MCP detection - returns $true if available, $false if not
# NO stdout/stderr output
function Test-ArchonAvailable {
    try {
        # Check if claude command exists
        if (Get-Command claude -ErrorAction SilentlyContinue) {
            # Try to call health check via MCP (completely silent)
            # Note: This assumes MCP tools are available in the environment
            # In practice, we'll check for the existence of Archon state or previous successful calls
            return $true  # For now, assume available if Claude is available
        }
    } catch {
        # Silently handle any errors
    }
    return $false
}

# Get the Archon state directory for a feature
# Returns the state directory relative to where archon-common.ps1 is located
# This ensures all scripts use the same state directory consistently
function Get-ArchonStateDir {
    # Get the directory containing archon-common.ps1 (this file)
    # $PSCommandPath in this context always refers to archon-common.ps1
    $commonScriptDir = Split-Path -Parent $PSCommandPath
    # State directory is always relative to where archon-common.ps1 lives
    return Join-Path $commonScriptDir ".archon-state"
}

# Save project ID mapping (completely silent, atomic write)
# Args: feature_name, project_id
function Save-ProjectMapping {
    param(
        [string]$FeatureName,
        [string]$ProjectId
    )

    try {
        $stateDir = Get-ArchonStateDir

        # Create state directory silently
        if (-not (Test-Path $stateDir)) {
            New-Item -ItemType Directory -Path $stateDir -Force -ErrorAction SilentlyContinue | Out-Null
        }

        # Write project ID to state file atomically (temp file + move)
        $pidFile = Join-Path $stateDir "${FeatureName}.pid"
        $tempFile = "$pidFile.tmp"

        $ProjectId | Out-File -FilePath $tempFile -NoNewline -Force -ErrorAction Stop
        Move-Item -Path $tempFile -Destination $pidFile -Force -ErrorAction Stop

        return $true
    } catch {
        # Cleanup temp file if it exists
        if (Test-Path "$pidFile.tmp") {
            Remove-Item -Path "$pidFile.tmp" -Force -ErrorAction SilentlyContinue
        }
        return $false
    }
}

# Load project ID mapping (silent, outputs to pipeline only on success)
# Args: feature_name
# Returns: project_id via pipeline, or empty string if not found
function Get-ProjectMapping {
    param([string]$FeatureName)

    try {
        $stateDir = Get-ArchonStateDir
        $pidFile = Join-Path $stateDir "${FeatureName}.pid"

        if (Test-Path $pidFile) {
            return Get-Content -Path $pidFile -Raw -ErrorAction SilentlyContinue | ForEach-Object { $_.Trim() }
        }
    } catch {
        # Silently handle errors
    }
    return ""
}

# Save document ID mapping (completely silent, atomic write)
# Args: feature_name, document_filename, document_id
function Save-DocumentMapping {
    param(
        [string]$FeatureName,
        [string]$DocFilename,
        [string]$DocId
    )

    try {
        $stateDir = Get-ArchonStateDir

        if (-not (Test-Path $stateDir)) {
            New-Item -ItemType Directory -Path $stateDir -Force -ErrorAction SilentlyContinue | Out-Null
        }

        # Append or update document mapping
        $docsFile = Join-Path $stateDir "${FeatureName}.docs"
        $tempFile = "$docsFile.tmp"

        # Remove existing entry for this document if it exists
        $content = @()
        if (Test-Path $docsFile) {
            $content = Get-Content -Path $docsFile -ErrorAction SilentlyContinue | Where-Object { -not $_.StartsWith("${DocFilename}:") }
        }

        # Write to temp file atomically
        $content | Out-File -FilePath $tempFile -Force -ErrorAction Stop
        "${DocFilename}:${DocId}" | Out-File -FilePath $tempFile -Append -NoNewline -Force -ErrorAction Stop
        "`n" | Out-File -FilePath $tempFile -Append -NoNewline -Force -ErrorAction Stop

        Move-Item -Path $tempFile -Destination $docsFile -Force -ErrorAction Stop

        return $true
    } catch {
        # Cleanup temp file if it exists
        if (Test-Path "$docsFile.tmp") {
            Remove-Item -Path "$docsFile.tmp" -Force -ErrorAction SilentlyContinue
        }
        return $false
    }
}

# Load document ID mapping (silent, outputs to pipeline only on success)
# Args: feature_name, document_filename
# Returns: document_id via pipeline, or empty string if not found
function Get-DocumentMapping {
    param(
        [string]$FeatureName,
        [string]$DocFilename
    )

    try {
        $stateDir = Get-ArchonStateDir
        $docsFile = Join-Path $stateDir "${FeatureName}.docs"

        if (Test-Path $docsFile) {
            $content = Get-Content -Path $docsFile -ErrorAction SilentlyContinue
            $match = $content | Where-Object { $_.StartsWith("${DocFilename}:") } | Select-Object -First 1
            if ($match) {
                return ($match -split ':', 2)[1]
            }
        }
    } catch {
        # Silently handle errors
    }
    return ""
}

# Save task ID mapping (completely silent, atomic write)
# Args: feature_name, task_id_local (e.g., T001), task_id_archon (UUID)
function Save-TaskMapping {
    param(
        [string]$FeatureName,
        [string]$TaskLocal,
        [string]$TaskArchon
    )

    try {
        $stateDir = Get-ArchonStateDir

        if (-not (Test-Path $stateDir)) {
            New-Item -ItemType Directory -Path $stateDir -Force -ErrorAction SilentlyContinue | Out-Null
        }

        $tasksFile = Join-Path $stateDir "${FeatureName}.tasks"
        $tempFile = "$tasksFile.tmp"

        # Remove existing entry if it exists
        $content = @()
        if (Test-Path $tasksFile) {
            $content = Get-Content -Path $tasksFile -ErrorAction SilentlyContinue | Where-Object { -not $_.StartsWith("${TaskLocal}:") }
        }

        # Write to temp file atomically
        $content | Out-File -FilePath $tempFile -Force -ErrorAction Stop
        "${TaskLocal}:${TaskArchon}" | Out-File -FilePath $tempFile -Append -NoNewline -Force -ErrorAction Stop
        "`n" | Out-File -FilePath $tempFile -Append -NoNewline -Force -ErrorAction Stop

        Move-Item -Path $tempFile -Destination $tasksFile -Force -ErrorAction Stop

        return $true
    } catch {
        # Cleanup temp file if it exists
        if (Test-Path "$tasksFile.tmp") {
            Remove-Item -Path "$tasksFile.tmp" -Force -ErrorAction SilentlyContinue
        }
        return $false
    }
}

# Load task ID mapping (silent, outputs to pipeline only on success)
# Args: feature_name, task_id_local (e.g., T001)
# Returns: task_id_archon (UUID) via pipeline, or empty string if not found
function Get-TaskMapping {
    param(
        [string]$FeatureName,
        [string]$TaskLocal
    )

    try {
        $stateDir = Get-ArchonStateDir
        $tasksFile = Join-Path $stateDir "${FeatureName}.tasks"

        if (Test-Path $tasksFile) {
            $content = Get-Content -Path $tasksFile -ErrorAction SilentlyContinue
            $match = $content | Where-Object { $_.StartsWith("${TaskLocal}:") } | Select-Object -First 1
            if ($match) {
                return ($match -split ':', 2)[1]
            }
        }
    } catch {
        # Silently handle errors
    }
    return ""
}

# Save sync metadata (timestamp for conflict resolution, atomic write)
# Args: feature_name, filename, timestamp (ISO 8601)
function Save-SyncMetadata {
    param(
        [string]$FeatureName,
        [string]$Filename,
        [string]$Timestamp
    )

    try {
        $stateDir = Get-ArchonStateDir

        if (-not (Test-Path $stateDir)) {
            New-Item -ItemType Directory -Path $stateDir -Force -ErrorAction SilentlyContinue | Out-Null
        }

        $metaFile = Join-Path $stateDir "${FeatureName}.meta"
        $tempFile = "$metaFile.tmp"

        # Remove existing entry if it exists (using | as delimiter to avoid conflict with : in ISO timestamps)
        $content = @()
        if (Test-Path $metaFile) {
            $content = Get-Content -Path $metaFile -ErrorAction SilentlyContinue | Where-Object { -not $_.StartsWith("${Filename}|") }
        }

        # Write to temp file atomically
        $content | Out-File -FilePath $tempFile -Force -ErrorAction Stop
        "${Filename}|${Timestamp}" | Out-File -FilePath $tempFile -Append -NoNewline -Force -ErrorAction Stop
        "`n" | Out-File -FilePath $tempFile -Append -NoNewline -Force -ErrorAction Stop

        Move-Item -Path $tempFile -Destination $metaFile -Force -ErrorAction Stop

        return $true
    } catch {
        # Cleanup temp file if it exists
        if (Test-Path "$metaFile.tmp") {
            Remove-Item -Path "$metaFile.tmp" -Force -ErrorAction SilentlyContinue
        }
        return $false
    }
}

# Load sync metadata (silent, outputs to pipeline only on success)
# Args: feature_name, filename
# Returns: timestamp via pipeline, or empty string if not found
function Get-SyncMetadata {
    param(
        [string]$FeatureName,
        [string]$Filename
    )

    try {
        $stateDir = Get-ArchonStateDir
        $metaFile = Join-Path $stateDir "${FeatureName}.meta"

        if (Test-Path $metaFile) {
            $content = Get-Content -Path $metaFile -ErrorAction SilentlyContinue
            $match = $content | Where-Object { $_.StartsWith("${Filename}|") } | Select-Object -First 1
            if ($match) {
                return ($match -split '\|', 2)[1]
            }
        }
    } catch {
        # Silently handle errors
    }
    return ""
}

# Extract feature name from feature directory path
# Args: feature_dir (absolute path)
# Returns: feature name (e.g., "001-feature-name")
function Get-FeatureName {
    param([string]$FeatureDir)

    try {
        return Split-Path -Leaf $FeatureDir
    } catch {
        return ""
    }
}

# Get current timestamp in ISO 8601 format (UTC)
function Get-Timestamp {
    try {
        return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    } catch {
        return ""
    }
}
