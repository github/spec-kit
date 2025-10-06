#!/usr/bin/env pwsh
# check-task-prerequisites.ps1
# Validates prerequisites for tasks generation command

param(
    [switch]$Json,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Show help if requested
if ($Help) {
    Write-Host "Usage: .\check-task-prerequisites.ps1 [-Json] [-Help]"
    Write-Host ""
    Write-Host "Validates prerequisites for the /tasks command"
    Write-Host ""
    Write-Host "  -Json    Output results in JSON format"
    Write-Host "  -Help    Show this help message"
    exit 0
}

# Get script directory and load common functions
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")

# Get feature paths (now capability-aware)
try {
    $FeaturePaths = Get-FeaturePathsEnv
} catch {
    if ($Json) {
        @{error = "Failed to get feature paths: $_"} | ConvertTo-Json
    } else {
        Write-Error "ERROR: Failed to get feature paths: $_"
    }
    exit 1
}

# Check if we're on a valid feature branch
if (-not (Test-FeatureBranch -Branch $FeaturePaths.CURRENT_BRANCH)) {
    if ($Json) {
        @{error = "Not on a valid feature branch. Feature branches should be named like: username/proj-123.feature-name or username/proj-123.feature-name-cap-001"} | ConvertTo-Json
    } else {
        Write-Host "ERROR: Not on a valid feature branch" -ForegroundColor Red
        Write-Host "Current branch: $($FeaturePaths.CURRENT_BRANCH)" -ForegroundColor Yellow
        Write-Host "Expected format: username/proj-123.feature-name or username/proj-123.feature-name-cap-001" -ForegroundColor Yellow
    }
    exit 1
}

# Check for required files
$MissingFiles = @()
if (-not (Test-Path $FeaturePaths.IMPL_PLAN)) { $MissingFiles += "plan.md" }

if ($MissingFiles.Count -gt 0) {
    if ($Json) {
        @{error = "Missing required files: $($MissingFiles -join ', '). Run /plan command first"} | ConvertTo-Json
    } else {
        Write-Host "ERROR: Missing required files: $($MissingFiles -join ', ')" -ForegroundColor Red
        Write-Host "Run /plan command first" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Expected file:"
        Write-Host "  - $($FeaturePaths.IMPL_PLAN)"
    }
    exit 1
}

# Build list of available design documents
$AvailableDocs = @()
if (Test-Path $FeaturePaths.FEATURE_SPEC) { $AvailableDocs += "spec.md" }
if (Test-Path $FeaturePaths.IMPL_PLAN) { $AvailableDocs += "plan.md" }
if (Test-Path $FeaturePaths.DATA_MODEL) { $AvailableDocs += "data-model.md" }
if (Test-Path $FeaturePaths.RESEARCH) { $AvailableDocs += "research.md" }
if (Test-Path $FeaturePaths.QUICKSTART) { $AvailableDocs += "quickstart.md" }
if ((Test-Path $FeaturePaths.CONTRACTS_DIR) -and (Get-ChildItem $FeaturePaths.CONTRACTS_DIR -ErrorAction SilentlyContinue).Count -gt 0) {
    $AvailableDocs += "contracts/"
}

# Output results
if ($Json) {
    $Result = @{
        repo_root = $FeaturePaths.REPO_ROOT
        feature_dir = $FeaturePaths.FEATURE_DIR
        plan_path = $FeaturePaths.IMPL_PLAN
        branch = $FeaturePaths.CURRENT_BRANCH
        capability_id = $FeaturePaths.CAPABILITY_ID
        parent_feature_dir = $FeaturePaths.PARENT_FEATURE_DIR
        feature_spec = $FeaturePaths.FEATURE_SPEC
        data_model = $FeaturePaths.DATA_MODEL
        contracts_dir = $FeaturePaths.CONTRACTS_DIR
        research = $FeaturePaths.RESEARCH
        quickstart = $FeaturePaths.QUICKSTART
        available_docs = $AvailableDocs
    }
    $Result | ConvertTo-Json
} else {
    Write-Host "Task Generation Prerequisites Check" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host "Repository: $($FeaturePaths.REPO_ROOT)"
    Write-Host "Feature Branch: $($FeaturePaths.CURRENT_BRANCH) " -ForegroundColor Green

    if ($FeaturePaths.CAPABILITY_ID) {
        Write-Host "Capability Mode: $($FeaturePaths.CAPABILITY_ID) (atomic PR workflow)" -ForegroundColor Cyan
        Write-Host "Parent Feature: $($FeaturePaths.PARENT_FEATURE_DIR)"
    }

    Write-Host "Feature Directory: $($FeaturePaths.FEATURE_DIR)"
    Write-Host ""
    Write-Host "Required Files:" -ForegroundColor Yellow
    Write-Host "   Plan: $($FeaturePaths.IMPL_PLAN)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Optional Design Documents:" -ForegroundColor Yellow

    if (Test-Path $FeaturePaths.FEATURE_SPEC) {
        Write-Host "   Specification: Found" -ForegroundColor Green
    } else {
        Write-Host "   Specification: Not found" -ForegroundColor DarkYellow
    }

    if (Test-Path $FeaturePaths.DATA_MODEL) {
        Write-Host "   Data Model: Found" -ForegroundColor Green
    } else {
        Write-Host "   Data Model: Not found" -ForegroundColor DarkYellow
    }

    if (Test-Path $FeaturePaths.RESEARCH) {
        Write-Host "   Research: Found" -ForegroundColor Green
    } else {
        Write-Host "   Research: Not found" -ForegroundColor DarkYellow
    }

    if (Test-Path $FeaturePaths.QUICKSTART) {
        Write-Host "   Quickstart: Found" -ForegroundColor Green
    } else {
        Write-Host "   Quickstart: Not found" -ForegroundColor DarkYellow
    }

    if ((Test-Path $FeaturePaths.CONTRACTS_DIR) -and (Get-ChildItem $FeaturePaths.CONTRACTS_DIR -ErrorAction SilentlyContinue).Count -gt 0) {
        Write-Host "   Contracts: Found" -ForegroundColor Green
    } else {
        Write-Host "   Contracts: Not found" -ForegroundColor DarkYellow
    }

    Write-Host ""
    Write-Host "=€ Ready to generate tasks!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Available docs: $($AvailableDocs -join ', ')" -ForegroundColor Cyan
}
