#!/usr/bin/env pwsh
# Archon Status Pull - Silent Status Synchronization (PowerShell)
# CRITICAL: This script MUST be completely silent (no stdout/stderr)
# Called before /speckit.implement to sync task statuses

# NOTE: This script creates marker files for the AI agent to process
# Only the AI agent (Claude Code) can make actual MCP calls

$ErrorActionPreference = 'SilentlyContinue'

$scriptDir = Split-Path -Parent $PSCommandPath
. (Join-Path $scriptDir "archon-common.ps1")

# Feature directory passed as argument
$featureDir = $args[0]

if (-not $featureDir) {
    exit 0  # Silent exit if no feature directory provided
}

# Extract feature name
$featureName = Get-FeatureName -FeatureDir $featureDir

if (-not $featureName) {
    exit 0  # Silent exit if feature name extraction fails
}

# Check if Archon MCP available (completely silent)
if (-not (Test-ArchonAvailable)) {
    exit 0  # MCP not available, do nothing
}

# Check if project exists
$projectId = Get-ProjectMapping -FeatureName $featureName
if (-not $projectId) {
    exit 0  # No project ID, can't sync status
}

# Load tasks.md path
$tasksFile = Join-Path $featureDir "tasks.md"
if (-not (Test-Path $tasksFile)) {
    exit 0  # No tasks file, nothing to sync
}

# Create status pull request for AI agent
# Conflict resolution strategy: "archon_wins"
# - Always trust Archon status over local checkboxes
# - Overwrite tasks.md without prompting (silent resolution)
# - No UI, no user interaction, no conflict markers
# - Advanced users can manually edit tasks.md if needed
$stateDir = Get-ArchonStateDir
$statusRequestFile = Join-Path $stateDir "${featureName}.status-request"

try {
    if (-not (Test-Path $stateDir)) {
        New-Item -ItemType Directory -Path $stateDir -Force -ErrorAction SilentlyContinue | Out-Null
    }

    $timestamp = Get-Timestamp
    $statusRequest = @{
        feature_name = $featureName
        project_id = $projectId
        tasks_file = $tasksFile
        timestamp = $timestamp
        status = "pending"
        conflict_strategy = "archon_wins"
    }

    $statusRequest | ConvertTo-Json -Depth 10 | Out-File -FilePath $statusRequestFile -Force -ErrorAction SilentlyContinue
} catch {
    # Silently handle errors
}

# Exit silently
exit 0
