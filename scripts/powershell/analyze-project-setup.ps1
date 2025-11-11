#!/usr/bin/env pwsh
# Setup analysis workspace for reverse engineering an existing project

[CmdletBinding()]
param(
    [switch]$Json,
    [string]$ProjectPath = "",
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output "Usage: ./analyze-project-setup.ps1 [-Json] [-ProjectPath PATH] [-Help]"
    Write-Output "  -Json          Output results in JSON format"
    Write-Output "  -ProjectPath   Path to project to analyze (required)"
    Write-Output "  -Help          Show this help message"
    exit 0
}

# Get repository root (where this script is run from)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "../..")).Path

# Validate PROJECT_PATH
if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
    Write-Error "ERROR: -ProjectPath is required"
    Write-Output "Use -Help for usage information"
    exit 1
}

# Convert to absolute path and validate
$ProjectPath = (Resolve-Path $ProjectPath -ErrorAction SilentlyContinue).Path
if (-not $ProjectPath -or -not (Test-Path $ProjectPath -PathType Container)) {
    Write-Error "ERROR: Project path does not exist or is not accessible: $ProjectPath"
    exit 1
}

# Extract project name from path
$projectName = Split-Path -Leaf $ProjectPath

# Create timestamp for this analysis
$timestamp = Get-Date -Format "yyyy-MM-dd-HHmmss"

# Create analysis directory structure
$analysisRoot = Join-Path $repoRoot ".analysis"
$analysisDir = Join-Path $analysisRoot "$projectName-$timestamp"

New-Item -ItemType Directory -Path $analysisDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $analysisDir "checkpoints") -Force | Out-Null

# Define output file paths
$analysisReport = Join-Path $analysisDir "analysis-report.md"
# Note: upgrade-plan.md and recommended-constitution.md removed in Phase 8
# Replaced by stage-prompts/ directory and new workflow artifacts
$recommendedSpec = Join-Path $analysisDir "recommended-spec.md"
$dependencyAudit = Join-Path $analysisDir "dependency-audit.json"
$metricsSummary = Join-Path $analysisDir "metrics-summary.json"
$decisionMatrix = Join-Path $analysisDir "decision-matrix.md"

# Copy templates to analysis directory (if they exist)
$templatesDir = Join-Path $repoRoot ".specify/templates"

$templateFiles = @{
    "analysis-report-template.md" = $analysisReport
    # Phase 8: upgrade-plan and recommended-constitution templates removed
    # These have been replaced by stage-prompts/ directory with 6 prompt files
}

foreach ($template in $templateFiles.Keys) {
    $templatePath = Join-Path $templatesDir $template
    if (Test-Path $templatePath) {
        Copy-Item $templatePath $templateFiles[$template] -Force
    }
}

# Check if we have git in the target project (optional)
$targetHasGit = "false"
try {
    Push-Location $ProjectPath
    $null = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0) {
        $targetHasGit = "true"
    }
} catch {
    # Git not available or not a git repo
} finally {
    Pop-Location
}

# Output results
if ($Json) {
    $result = [PSCustomObject]@{
        PROJECT_PATH = $ProjectPath
        PROJECT_NAME = $projectName
        ANALYSIS_DIR = $analysisDir
        ANALYSIS_REPORT = $analysisReport
        RECOMMENDED_SPEC = $recommendedSpec
        DEPENDENCY_AUDIT = $dependencyAudit
        METRICS_SUMMARY = $metricsSummary
        DECISION_MATRIX = $decisionMatrix
        TARGET_HAS_GIT = $targetHasGit
        TIMESTAMP = $timestamp
    }
    $result | ConvertTo-Json -Compress
} else {
    Write-Output "PROJECT_PATH: $ProjectPath"
    Write-Output "PROJECT_NAME: $projectName"
    Write-Output "ANALYSIS_DIR: $analysisDir"
    Write-Output "ANALYSIS_REPORT: $analysisReport"
    Write-Output "RECOMMENDED_SPEC: $recommendedSpec"
    Write-Output "DEPENDENCY_AUDIT: $dependencyAudit"
    Write-Output "METRICS_SUMMARY: $metricsSummary"
    Write-Output "DECISION_MATRIX: $decisionMatrix"
    Write-Output "TARGET_HAS_GIT: $targetHasGit"
    Write-Output "TIMESTAMP: $timestamp"
}
