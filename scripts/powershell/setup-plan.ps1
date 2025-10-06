#!/usr/bin/env pwsh
param(
    [switch]$Json,
    [string]$Capability = ""
)

$ErrorActionPreference = "Stop"

if ($args -contains "--help" -or $args -contains "-h") {
    Write-Host "Usage: setup-plan.ps1 [-Json] [-Capability cap-XXX]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Capability cap-XXX  Create capability branch and plan for atomic PR"
    Write-Host "  -Json                Output in JSON format"
    exit 0
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir/common.ps1"

$paths = Get-FeaturePathsEnv
$REPO_ROOT = $paths.REPO_ROOT
$CURRENT_BRANCH = $paths.CURRENT_BRANCH
$FEATURE_DIR = $paths.FEATURE_DIR
$FEATURE_SPEC = $paths.FEATURE_SPEC
$IMPL_PLAN = $paths.IMPL_PLAN

if (-not (Test-FeatureBranch $CURRENT_BRANCH)) {
    Write-Error "Not on a feature branch. Current branch: $CURRENT_BRANCH"
    Write-Error "Feature branches should be named like: username/jira-123.feature-name or username/jira-123.feature-name-cap-001"
    exit 1
}

# Capability mode: create new branch for atomic PR
if ($Capability) {
    # Extract feature ID from current branch
    $FEATURE_ID = Get-FeatureId $CURRENT_BRANCH
    $PARENT_BRANCH = $CURRENT_BRANCH

    # Verify capability directory exists
    $CAPABILITY_DIR = Join-Path $FEATURE_DIR $Capability
    if (-not (Test-Path $CAPABILITY_DIR)) {
        Write-Error "Capability directory not found at $CAPABILITY_DIR"
        Write-Error "Run /decompose first to create capability structure"
        exit 1
    }

    # Create capability branch: username/jira-123.feature-cap-001
    $USERNAME = $CURRENT_BRANCH.Split('/')[0]
    $CAPABILITY_BRANCH = "$USERNAME/$FEATURE_ID-$Capability"

    # Check if capability branch already exists
    $branchExists = git show-ref --verify --quiet "refs/heads/$CAPABILITY_BRANCH"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Checking out existing capability branch: $CAPABILITY_BRANCH"
        git checkout $CAPABILITY_BRANCH
    } else {
        Write-Host "Creating new capability branch: $CAPABILITY_BRANCH from $PARENT_BRANCH"
        git checkout -b $CAPABILITY_BRANCH $PARENT_BRANCH
    }

    # Set paths for capability
    $FEATURE_SPEC = Join-Path $CAPABILITY_DIR "spec.md"
    $IMPL_PLAN = Join-Path $CAPABILITY_DIR "plan.md"
    $SPECS_DIR = $CAPABILITY_DIR
    $CURRENT_BRANCH = $CAPABILITY_BRANCH

    New-Item -ItemType Directory -Force -Path $CAPABILITY_DIR | Out-Null
} else {
    # Parent feature mode: use existing branch
    New-Item -ItemType Directory -Force -Path $FEATURE_DIR | Out-Null
    $SPECS_DIR = $FEATURE_DIR
}

$TEMPLATE = Join-Path $REPO_ROOT ".specify/templates/plan-template.md"
if (Test-Path $TEMPLATE) {
    Copy-Item $TEMPLATE $IMPL_PLAN -Force
}

if ($Json) {
    if ($Capability) {
        $output = @{
            FEATURE_SPEC = $FEATURE_SPEC
            IMPL_PLAN = $IMPL_PLAN
            SPECS_DIR = $SPECS_DIR
            BRANCH = $CURRENT_BRANCH
            CAPABILITY_ID = $Capability
            PARENT_BRANCH = $PARENT_BRANCH
        }
    } else {
        $output = @{
            FEATURE_SPEC = $FEATURE_SPEC
            IMPL_PLAN = $IMPL_PLAN
            SPECS_DIR = $SPECS_DIR
            BRANCH = $CURRENT_BRANCH
        }
    }
    $output | ConvertTo-Json -Compress
} else {
    Write-Host "FEATURE_SPEC: $FEATURE_SPEC"
    Write-Host "IMPL_PLAN: $IMPL_PLAN"
    Write-Host "SPECS_DIR: $SPECS_DIR"
    Write-Host "BRANCH: $CURRENT_BRANCH"
    if ($Capability) {
        Write-Host "CAPABILITY_ID: $Capability"
        Write-Host "PARENT_BRANCH: $PARENT_BRANCH"
        Write-Host ""
        Write-Host "Capability branch created for atomic PR workflow"
    }
}
