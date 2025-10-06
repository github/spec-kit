#!/usr/bin/env pwsh
# check-implementation-prerequisites.ps1
# Validates prerequisites for implementation command

param(
    [switch]$Json,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Show help if requested
if ($Help) {
    Write-Host "Usage: .\check-implementation-prerequisites.ps1 [-Json] [-Help]"
    Write-Host ""
    Write-Host "Validates prerequisites for the /implement command"
    Write-Host ""
    Write-Host "  -Json    Output results in JSON format"
    Write-Host "  -Help    Show this help message"
    exit 0
}

# Get script directory and load common functions
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")

# Get repository root and current branch
try {
    $RepoRoot = Get-RepoRoot
    $CurrentBranch = Get-CurrentBranch
} catch {
    if ($Json) {
        @{error = "Not in a git repository or git not available"} | ConvertTo-Json
    } else {
        Write-Error "ERROR: Not in a git repository or git not available"
    }
    exit 1
}

# Validate feature branch
if (-not (Test-FeatureBranch -Branch $CurrentBranch)) {
    if ($Json) {
        @{error = "Not on a valid feature branch. Feature branches should be named like: username/proj-123.feature-name"} | ConvertTo-Json
    } else {
        Write-Host "ERROR: Not on a valid feature branch" -ForegroundColor Red
        Write-Host "Current branch: $CurrentBranch" -ForegroundColor Yellow
        Write-Host "Expected format: username/proj-123.feature-name" -ForegroundColor Yellow
    }
    exit 1
}

# Get feature paths (now capability-aware via Get-FeaturePathsEnv)
$FeaturePaths = Get-FeaturePathsEnv

# Check for required files
$MissingFiles = @()
if (-not (Test-Path $FeaturePaths.IMPL_PLAN)) { $MissingFiles += "plan.md" }
if (-not (Test-Path $FeaturePaths.TASKS)) { $MissingFiles += "tasks.md" }

if ($MissingFiles.Count -gt 0) {
    if ($Json) {
        @{error = "Missing required files: $($MissingFiles -join ', ')"} | ConvertTo-Json
    } else {
        Write-Host "ERROR: Missing required files: $($MissingFiles -join ', ')" -ForegroundColor Red
        Write-Host "Run /plan and /tasks commands first" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Expected files:"
        Write-Host "  - $($FeaturePaths.IMPL_PLAN)"
        Write-Host "  - $($FeaturePaths.TASKS)"
    }
    exit 1
}

# Check for constitution
$ConstitutionPath = Join-Path $RepoRoot "memory\constitution.md"
if (-not (Test-Path $ConstitutionPath)) { $ConstitutionPath = "" }

# Check for optional files
$AvailableDocs = @()
if (Test-Path $FeaturePaths.FEATURE_SPEC) { $AvailableDocs += "spec.md" }
if (Test-Path $FeaturePaths.IMPL_PLAN) { $AvailableDocs += "plan.md" }
if (Test-Path $FeaturePaths.TASKS) { $AvailableDocs += "tasks.md" }
if (Test-Path $FeaturePaths.DATA_MODEL) { $AvailableDocs += "data-model.md" }
if (Test-Path $FeaturePaths.RESEARCH) { $AvailableDocs += "research.md" }
if (Test-Path $FeaturePaths.QUICKSTART) { $AvailableDocs += "quickstart.md" }
if ((Test-Path $FeaturePaths.CONTRACTS_DIR) -and (Get-ChildItem $FeaturePaths.CONTRACTS_DIR -ErrorAction SilentlyContinue).Count -gt 0) {
    $AvailableDocs += "contracts/"
}

# Check for recent validation
$LastValidation = ""
try {
    $ValidationLog = git log -1 --oneline --grep="validate" 2>$null
    if ($ValidationLog) { $LastValidation = $ValidationLog.Split("`n")[0] }
} catch {}

# Check git status for uncommitted changes
$UncommittedChanges = $false
try {
    $GitStatus = git status --porcelain 2>$null
    if ($GitStatus) { $UncommittedChanges = $true }
} catch {}

# Check test status (TDD validation)
$TestStatus = ""
if ((Test-Path (Join-Path $RepoRoot "package.json")) -and (Get-Command npm -ErrorAction SilentlyContinue)) {
    try {
        npm test --silent 2>$null | Out-Null
        $TestStatus = "passing"
    } catch {
        $TestStatus = "failing"
    }
} elseif (((Test-Path (Join-Path $RepoRoot "pyproject.toml")) -or (Test-Path (Join-Path $RepoRoot "setup.py"))) -and (Get-Command python -ErrorAction SilentlyContinue)) {
    try {
        python -m pytest --quiet 2>$null | Out-Null
        $TestStatus = "passing"
    } catch {
        $TestStatus = "failing"
    }
} elseif ((Test-Path (Join-Path $RepoRoot "go.mod")) -and (Get-Command go -ErrorAction SilentlyContinue)) {
    try {
        go test ./... 2>$null | Out-Null
        $TestStatus = "passing"
    } catch {
        $TestStatus = "failing"
    }
}

# Output results
if ($Json) {
    $Result = @{
        repo_root = $FeaturePaths.REPO_ROOT
        feature_dir = $FeaturePaths.FEATURE_DIR
        feature_spec = $FeaturePaths.FEATURE_SPEC
        impl_plan = $FeaturePaths.IMPL_PLAN
        tasks = $FeaturePaths.TASKS
        branch = $FeaturePaths.CURRENT_BRANCH
        capability_id = $FeaturePaths.CAPABILITY_ID
        parent_feature_dir = $FeaturePaths.PARENT_FEATURE_DIR
        constitution = $ConstitutionPath
        data_model = $FeaturePaths.DATA_MODEL
        contracts_dir = $FeaturePaths.CONTRACTS_DIR
        research = $FeaturePaths.RESEARCH
        quickstart = $FeaturePaths.QUICKSTART
        available_docs = $AvailableDocs
        last_validation = $LastValidation
        uncommitted_changes = $UncommittedChanges
        test_status = $TestStatus
    }
    $Result | ConvertTo-Json
} else {
    Write-Host "Implementation Prerequisites Check" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host "Repository: $($FeaturePaths.REPO_ROOT)"
    Write-Host "Feature Branch: $($FeaturePaths.CURRENT_BRANCH) ✓" -ForegroundColor Green

    if ($FeaturePaths.CAPABILITY_ID) {
        Write-Host "Capability Mode: $($FeaturePaths.CAPABILITY_ID) (atomic PR workflow)" -ForegroundColor Cyan
        Write-Host "Parent Feature: $($FeaturePaths.PARENT_FEATURE_DIR)"
    }

    Write-Host "Feature Directory: $($FeaturePaths.FEATURE_DIR)"
    Write-Host ""
    Write-Host "Required Files:" -ForegroundColor Yellow
    Write-Host "  ✓ Plan: $($FeaturePaths.IMPL_PLAN)" -ForegroundColor Green
    Write-Host "  ✓ Tasks: $($FeaturePaths.TASKS)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Optional Files:" -ForegroundColor Yellow

    if (Test-Path $FeaturePaths.FEATURE_SPEC) {
        Write-Host "  ✓ Specification: Found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Specification: Not found" -ForegroundColor DarkYellow
    }

    if ($ConstitutionPath) {
        Write-Host "  ✓ Constitution: Found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Constitution: Not found" -ForegroundColor DarkYellow
    }

    if (Test-Path $FeaturePaths.DATA_MODEL) {
        Write-Host "  ✓ Data Model: Found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Data Model: Not found" -ForegroundColor DarkYellow
    }

    if (Test-Path $FeaturePaths.RESEARCH) {
        Write-Host "  ✓ Research: Found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Research: Not found" -ForegroundColor DarkYellow
    }

    if (Test-Path $FeaturePaths.QUICKSTART) {
        Write-Host "  ✓ Quickstart: Found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Quickstart: Not found" -ForegroundColor DarkYellow
    }

    if ((Test-Path $FeaturePaths.CONTRACTS_DIR) -and (Get-ChildItem $FeaturePaths.CONTRACTS_DIR -ErrorAction SilentlyContinue).Count -gt 0) {
        Write-Host "  ✓ Contracts: Found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Contracts: Not found" -ForegroundColor DarkYellow
    }

    Write-Host ""
    Write-Host "Status Checks:" -ForegroundColor Yellow

    if ($LastValidation) {
        Write-Host "  ✓ Recent validation: $LastValidation" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ No recent validation found" -ForegroundColor DarkYellow
    }

    if ($UncommittedChanges) {
        Write-Host "  ⚠ Uncommitted changes detected" -ForegroundColor DarkYellow
    } else {
        Write-Host "  ✓ Working directory clean" -ForegroundColor Green
    }

    switch ($TestStatus) {
        "passing" { Write-Host "  ⚠ Tests passing (TDD expects failing tests initially)" -ForegroundColor DarkYellow }
        "failing" { Write-Host "  ✓ Tests failing (good for TDD red phase)" -ForegroundColor Green }
        default { Write-Host "  ℹ No test framework detected" -ForegroundColor Blue }
    }

    Write-Host ""
    Write-Host "🚀 Ready to implement!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Available docs: $($AvailableDocs -join ', ')" -ForegroundColor Cyan
}