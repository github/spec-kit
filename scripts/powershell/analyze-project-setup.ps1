#!/usr/bin/env pwsh
# Setup analysis workspace for reverse engineering an existing project

[CmdletBinding()]
param(
    [switch]$Json,
    [string]$ProjectPath = "",
    [ValidateSet("QUICK", "STANDARD", "COMPREHENSIVE")]
    [string]$Depth = "STANDARD",
    [ValidateSet("ALL", "SECURITY", "PERFORMANCE", "ARCHITECTURE", "DEPENDENCIES")]
    [string]$Focus = "ALL",
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output "Usage: ./analyze-project-setup.ps1 [-Json] [-ProjectPath PATH] [-Depth LEVEL] [-Focus AREAS] [-Help]"
    Write-Output "  -Json          Output results in JSON format"
    Write-Output "  -ProjectPath   Path to project to analyze (required)"
    Write-Output "  -Depth         Analysis depth: QUICK|STANDARD|COMPREHENSIVE (default: STANDARD)"
    Write-Output "  -Focus         Focus areas: ALL|SECURITY|PERFORMANCE|ARCHITECTURE|DEPENDENCIES (default: ALL)"
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
$upgradePlan = Join-Path $analysisDir "upgrade-plan.md"
$recommendedConstitution = Join-Path $analysisDir "recommended-constitution.md"
$recommendedSpec = Join-Path $analysisDir "recommended-spec.md"
$dependencyAudit = Join-Path $analysisDir "dependency-audit.json"
$metricsSummary = Join-Path $analysisDir "metrics-summary.json"
$decisionMatrix = Join-Path $analysisDir "decision-matrix.md"

# Copy templates to analysis directory (if they exist)
$templatesDir = Join-Path $repoRoot ".specify/templates"

$templateFiles = @{
    "analysis-report-template.md" = $analysisReport
    "upgrade-plan-template.md" = $upgradePlan
    "reverse-engineering-constitution-template.md" = $recommendedConstitution
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

# Run Python analyzer if available
$pythonAnalyzerAvailable = "false"
$pythonAnalysisStatus = "not_run"
$pythonAnalysisError = ""

# Check if python3 or python is available
$pythonCmd = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
}

if ($pythonCmd) {
    $pythonAnalyzerAvailable = "true"

    # Try to run the Python analyzer
    Write-Host "Running Python analyzer..." -ForegroundColor Yellow

    try {
        $logPath = Join-Path $analysisDir "analyzer-log.txt"

        & $pythonCmd -m scripts.python.analyzer `
            --project $ProjectPath `
            --output $analysisDir `
            --depth $Depth `
            --focus $Focus `
            --json 2>&1 | Tee-Object -FilePath $logPath | Select-Object -Last 20

        if ($LASTEXITCODE -eq 0) {
            $pythonAnalysisStatus = "success"
            Write-Host "✓ Python analyzer completed successfully" -ForegroundColor Green
        } else {
            $pythonAnalysisStatus = "failed"
            $pythonAnalysisError = "Python analyzer failed - see analyzer-log.txt"
            Write-Host "⚠ Python analyzer failed - will use AI-guided analysis fallback" -ForegroundColor Yellow
        }
    } catch {
        $pythonAnalysisStatus = "failed"
        $pythonAnalysisError = "Exception during Python analyzer: $_"
        Write-Host "⚠ Python analyzer failed - will use AI-guided analysis fallback" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ Python not available - will use AI-guided analysis" -ForegroundColor Yellow
}

# Output results
if ($Json) {
    $result = [PSCustomObject]@{
        PROJECT_PATH = $ProjectPath
        PROJECT_NAME = $projectName
        ANALYSIS_DIR = $analysisDir
        ANALYSIS_REPORT = $analysisReport
        UPGRADE_PLAN = $upgradePlan
        RECOMMENDED_CONSTITUTION = $recommendedConstitution
        RECOMMENDED_SPEC = $recommendedSpec
        DEPENDENCY_AUDIT = $dependencyAudit
        METRICS_SUMMARY = $metricsSummary
        DECISION_MATRIX = $decisionMatrix
        ANALYSIS_DEPTH = $Depth
        FOCUS_AREAS = $Focus
        TARGET_HAS_GIT = $targetHasGit
        TIMESTAMP = $timestamp
        PYTHON_ANALYZER_AVAILABLE = $pythonAnalyzerAvailable
        PYTHON_ANALYSIS_STATUS = $pythonAnalysisStatus
        PYTHON_ANALYSIS_ERROR = $pythonAnalysisError
    }
    $result | ConvertTo-Json -Compress
} else {
    Write-Output "PROJECT_PATH: $ProjectPath"
    Write-Output "PROJECT_NAME: $projectName"
    Write-Output "ANALYSIS_DIR: $analysisDir"
    Write-Output "ANALYSIS_REPORT: $analysisReport"
    Write-Output "UPGRADE_PLAN: $upgradePlan"
    Write-Output "RECOMMENDED_CONSTITUTION: $recommendedConstitution"
    Write-Output "RECOMMENDED_SPEC: $recommendedSpec"
    Write-Output "DEPENDENCY_AUDIT: $dependencyAudit"
    Write-Output "METRICS_SUMMARY: $metricsSummary"
    Write-Output "DECISION_MATRIX: $decisionMatrix"
    Write-Output "ANALYSIS_DEPTH: $Depth"
    Write-Output "FOCUS_AREAS: $Focus"
    Write-Output "TARGET_HAS_GIT: $targetHasGit"
    Write-Output "TIMESTAMP: $timestamp"
    Write-Output "PYTHON_ANALYZER_AVAILABLE: $pythonAnalyzerAvailable"
    Write-Output "PYTHON_ANALYSIS_STATUS: $pythonAnalysisStatus"
    Write-Output "PYTHON_ANALYSIS_ERROR: $pythonAnalysisError"
}
