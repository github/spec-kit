#!/usr/bin/env pwsh
# Archon Auto-Init - Silent Project and Document Creation (PowerShell)
# CRITICAL: This script MUST be completely silent (no stdout/stderr)
# Called in background by /speckit.specify command

# NOTE: This script creates a marker file that the AI agent will process
# Only the AI agent (Claude Code) can make actual MCP calls

$ErrorActionPreference = 'SilentlyContinue'

$scriptDir = Split-Path -Parent $PSCommandPath
. (Join-Path $scriptDir "archon-common.ps1")

# Feature directory passed as argument
$featureDir = $args[0]

if (-not $featureDir) {
    exit 0  # Silent exit if no feature directory provided
}

# Extract feature name from directory path
$featureName = Get-FeatureName -FeatureDir $featureDir

if (-not $featureName) {
    exit 0  # Silent exit if feature name extraction fails
}

# Check if Archon MCP available (completely silent)
if (-not (Test-ArchonAvailable)) {
    exit 0  # MCP not available, do nothing
}

# Check if project already exists
$existingProjectId = Get-ProjectMapping -FeatureName $featureName
if ($existingProjectId) {
    exit 0  # Project already exists, nothing to do
}

# Load spec.md to extract title and description
$specFile = Join-Path $featureDir "spec.md"
if (-not (Test-Path $specFile)) {
    exit 0  # No spec file, can't create project
}

# Extract title from spec.md (first # heading)
$projectTitle = ""
try {
    $content = Get-Content -Path $specFile -ErrorAction SilentlyContinue
    $headingLine = $content | Where-Object { $_ -match '^#\s+(.+)$' } | Select-Object -First 1
    if ($headingLine -match '^#\s+(.+)$') {
        $projectTitle = $matches[1].Trim()
    }
} catch {
    # Silently handle errors
}

if (-not $projectTitle) {
    $projectTitle = "Feature: $featureName"
}

# Extract description from spec.md (content after first heading, before next ##)
$projectDesc = ""
try {
    $content = Get-Content -Path $specFile -Raw -ErrorAction SilentlyContinue
    if ($content -match '(?s)^#\s+[^\n]+\n(.+?)(?=\n##|\z)') {
        $descLines = ($matches[1] -split '\n' | Select-Object -First 3) -join ' '
        $projectDesc = $descLines.Trim()
    }
} catch {
    # Silently handle errors
}

if (-not $projectDesc) {
    $projectDesc = "Implementation of $featureName"
}

# Create initialization request for AI agent to process
$stateDir = Get-ArchonStateDir
$initRequestFile = Join-Path $stateDir "${featureName}.init-request"

try {
    if (-not (Test-Path $stateDir)) {
        New-Item -ItemType Directory -Path $stateDir -Force -ErrorAction SilentlyContinue | Out-Null
    }

    $timestamp = Get-Timestamp
    $initRequest = @{
        feature_name = $featureName
        project_title = $projectTitle
        project_description = $projectDesc
        spec_file = $specFile
        feature_dir = $featureDir
        timestamp = $timestamp
        status = "pending"
    }

    $initRequest | ConvertTo-Json -Depth 10 | Out-File -FilePath $initRequestFile -Force -ErrorAction SilentlyContinue
} catch {
    # Silently handle errors
}

# Exit silently
exit 0
