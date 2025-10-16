#!/usr/bin/env pwsh
# Archon Task Auto-Sync - Silent Task Synchronization (PowerShell)
# CRITICAL: This script MUST be completely silent (no stdout/stderr)
# Called in background by /speckit.tasks command

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
    exit 0  # No project ID, can't sync tasks
}

# Load tasks.md
$tasksFile = Join-Path $featureDir "tasks.md"
if (-not (Test-Path $tasksFile)) {
    exit 0  # No tasks file, nothing to sync
}

# Parse tasks.md and extract tasks
# Format: - [ ] [TaskID] [P?] [Story?] Description
$tasks = @()

try {
    $content = Get-Content -Path $tasksFile -ErrorAction SilentlyContinue

    foreach ($line in $content) {
        # Match task lines: - [ ] or - [X] or - [x]
        if ($line -match '^-\s*\[[\sxX]\]\s*(.+)$') {
            $taskContent = $matches[1]

            # Check if completed
            $status = if ($line -match '^-\s*\[[xX]\]') { "done" } else { "todo" }

            # Extract task ID if present: [T001] or [T002]
            $taskId = ""
            if ($taskContent -match '^\[T(\d+)\]\s*(.+)$') {
                $taskId = "T$($matches[1])"
                $taskContent = $matches[2]
            }

            # Extract parallel marker [P] if present
            $parallel = $false
            if ($taskContent -match '^\[P\]\s*(.+)$') {
                $parallel = $true
                $taskContent = $matches[1]
            }

            # Extract story marker [US1], [US2], etc. if present
            $story = ""
            if ($taskContent -match '^\[US(\d+)\]\s*(.+)$') {
                $story = "US$($matches[1])"
                $taskContent = $matches[2]
            }

            # The rest is the task title/description
            $taskTitle = $taskContent.Trim()

            # Build task object
            $tasks += @{
                task_id = if ($taskId) { $taskId } else { "" }
                title = $taskTitle
                status = $status
                parallel = $parallel
                story = if ($story) { $story } else { "" }
            }
        }
    }
} catch {
    # Silently handle errors
}

# Create task sync request for AI agent
$stateDir = Get-ArchonStateDir
$syncRequestFile = Join-Path $stateDir "${featureName}.task-sync-request"

try {
    if (-not (Test-Path $stateDir)) {
        New-Item -ItemType Directory -Path $stateDir -Force -ErrorAction SilentlyContinue | Out-Null
    }

    $timestamp = Get-Timestamp
    $taskSyncRequest = @{
        feature_name = $featureName
        project_id = $projectId
        tasks_file = $tasksFile
        tasks = $tasks
        timestamp = $timestamp
        status = "pending"
    }

    $taskSyncRequest | ConvertTo-Json -Depth 10 | Out-File -FilePath $syncRequestFile -Force -ErrorAction SilentlyContinue
} catch {
    # Silently handle errors
}

# Exit silently
exit 0
