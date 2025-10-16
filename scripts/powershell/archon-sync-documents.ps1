#!/usr/bin/env pwsh
# Archon Document Sync - Silent Bidirectional Synchronization (PowerShell)
# CRITICAL: This script MUST be completely silent (no stdout/stderr)
# Called by slash commands for pull-before/push-after operations

# NOTE: This script creates marker files for the AI agent to process
# Only the AI agent (Claude Code) can make actual MCP calls

$ErrorActionPreference = 'SilentlyContinue'

$scriptDir = Split-Path -Parent $PSCommandPath
. (Join-Path $scriptDir "archon-common.ps1")

# Arguments: feature_dir, mode (pull|push)
$featureDir = $args[0]
$syncMode = if ($args[1]) { $args[1] } else { "pull" }

if (-not $featureDir) {
    exit 0  # Silent exit if no feature directory provided
}

if ($syncMode -notmatch '^(pull|push)$') {
    exit 0  # Invalid mode, silent exit
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
    exit 0  # No project ID, can't sync
}

# Document types to sync
$documentTypes = @(
    @{filename = "spec.md"; doc_type = "spec"}
    @{filename = "plan.md"; doc_type = "plan"}
    @{filename = "research.md"; doc_type = "research"}
    @{filename = "data-model.md"; doc_type = "data-model"}
    @{filename = "quickstart.md"; doc_type = "quickstart"}
    @{filename = "tasks.md"; doc_type = "tasks"}
)

# Create sync request for AI agent
$stateDir = Get-ArchonStateDir
$syncRequestFile = Join-Path $stateDir "${featureName}.sync-request"

try {
    if (-not (Test-Path $stateDir)) {
        New-Item -ItemType Directory -Path $stateDir -Force -ErrorAction SilentlyContinue | Out-Null
    }

    # Build document list
    $docs = @()
    foreach ($docEntry in $documentTypes) {
        $filename = $docEntry.filename
        $docType = $docEntry.doc_type
        $filepath = Join-Path $featureDir $filename
        $docId = Get-DocumentMapping -FeatureName $featureName -DocFilename $filename

        $docs += @{
            filename = $filename
            doc_type = $docType
            filepath = $filepath
            doc_id = if ($docId) { $docId } else { "" }
        }
    }

    $timestamp = Get-Timestamp
    $syncRequest = @{
        feature_name = $featureName
        project_id = $projectId
        feature_dir = $featureDir
        sync_mode = $syncMode
        documents = $docs
        timestamp = $timestamp
        status = "pending"
    }

    $syncRequest | ConvertTo-Json -Depth 10 | Out-File -FilePath $syncRequestFile -Force -ErrorAction SilentlyContinue
} catch {
    # Silently handle errors
}

# Exit silently
exit 0
