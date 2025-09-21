#!/usr/bin/env pwsh
# Check issue prerequisites
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RequireTasks,
    [switch]$IncludeTasks,
    [switch]$PathsOnly
)
$ErrorActionPreference = 'Stop'

# Source common functions
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$commonScript = Join-Path $scriptDir "common.ps1"
if (Test-Path $commonScript) {
    . $commonScript
} else {
    Write-Error "Common script not found: $commonScript"
    exit 1
}

# Get feature paths and validate branch
$featurePaths = Get-FeaturePaths
$repoRoot = $featurePaths.REPO_ROOT
$currentBranch = $featurePaths.CURRENT_BRANCH
$hasGit = $featurePaths.HAS_GIT

# Validate branch
if (-not (Test-FeatureBranch -Branch $currentBranch -HasGit $hasGit)) {
    exit 1
}

# For issue-resolution flow, we look in issues/ directory instead of specs/
$issuesDir = Join-Path $repoRoot "issues"
$issueDir = Join-Path $issuesDir $currentBranch
$issueSpec = Join-Path $issueDir "issue.md"
$issuePlan = Join-Path $issueDir "plan.md"
$issueTasks = Join-Path $issueDir "tasks.md"
$issueResearch = Join-Path $issueDir "research.md"
$issueDataModel = Join-Path $issueDir "data-model.md"
$issueContractsDir = Join-Path $issueDir "contracts"
$issueQuickstart = Join-Path $issueDir "quickstart.md"

# If paths-only mode, output paths and exit
if ($PathsOnly) {
    Write-Output "REPO_ROOT: $repoRoot"
    Write-Output "BRANCH: $currentBranch"
    Write-Output "ISSUE_DIR: $issueDir"
    Write-Output "ISSUE_SPEC: $issueSpec"
    Write-Output "ISSUE_PLAN: $issuePlan"
    Write-Output "ISSUE_TASKS: $issueTasks"
    exit 0
}

# Validate required directories and files
if (-not (Test-Path $issueDir)) {
    Write-Error "ERROR: Issue directory not found: $issueDir"
    Write-Error "Run /issue first to create the issue structure."
    exit 1
}

if (-not (Test-Path $issueSpec)) {
    Write-Error "ERROR: issue.md not found in $issueDir"
    Write-Error "Run /issue first to create the issue specification."
    exit 1
}

# Check for tasks.md if required
if ($RequireTasks -and -not (Test-Path $issueTasks)) {
    Write-Error "ERROR: tasks.md not found in $issueDir"
    Write-Error "Run /plan first to create the task list for this issue."
    exit 1
}

# Build list of available documents
$docs = @()

# Always check these optional docs
if (Test-Path $issueResearch) { $docs += "research.md" }
if (Test-Path $issueDataModel) { $docs += "data-model.md" }

# Check contracts directory (only if it exists and has files)
if ((Test-Path $issueContractsDir) -and (Get-ChildItem $issueContractsDir -ErrorAction SilentlyContinue)) {
    $docs += "contracts/"
}

if (Test-Path $issueQuickstart) { $docs += "quickstart.md" }

# Include tasks.md if requested and it exists
if ($IncludeTasks -and (Test-Path $issueTasks)) {
    $docs += "tasks.md"
}

# Output results
if ($Json) {
    $result = @{
        ISSUE_DIR = $issueDir
        AVAILABLE_DOCS = $docs
    } | ConvertTo-Json -Compress
    Write-Output $result
} else {
    Write-Output "ISSUE_DIR:$issueDir"
    Write-Output "AVAILABLE_DOCS:"
    
    # Show status of each potential document
    Test-File -Path $issueResearch -Name "research.md"
    Test-File -Path $issueDataModel -Name "data-model.md"
    Test-Directory -Path $issueContractsDir -Name "contracts/"
    Test-File -Path $issueQuickstart -Name "quickstart.md"
    
    if ($IncludeTasks) {
        Test-File -Path $issueTasks -Name "tasks.md"
    }
}
