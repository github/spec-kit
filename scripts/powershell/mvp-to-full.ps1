#!/usr/bin/env pwsh
# MVP to Full Product Orchestrator - PowerShell version
[CmdletBinding()]
param(
    [switch]$Json,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ProjectDescription
)
$ErrorActionPreference = 'Stop'

if (-not $ProjectDescription -or $ProjectDescription.Count -eq 0) {
    Write-Error "Usage: ./mvp-to-full.ps1 [-Json] <project description>"; exit 1
}
$projectDesc = ($ProjectDescription -join ' ').Trim()

$repoRoot = git rev-parse --show-toplevel
$specsDir = Join-Path $repoRoot 'specs'
New-Item -ItemType Directory -Path $specsDir -Force | Out-Null

# Analyze project state (brownfield vs greenfield)
Write-Host "🔍 Analyzing project state..." -ForegroundColor Cyan
$projectStateScript = Join-Path $repoRoot '.specify/scripts/powershell/analyze-project-state.ps1'
$projectStateResult = & $projectStateScript -Json | ConvertFrom-Json
$projectType = $projectStateResult.project_type
Write-Host "📊 Project type detected: $projectType" -ForegroundColor Green

# Create MVP plan file if it doesn't exist
$mvpPlanFile = Join-Path $repoRoot 'mvp-plan.md'
if (-not (Test-Path $mvpPlanFile)) {
    $templateFile = Join-Path $repoRoot 'templates/mvp-plan-template.md'
    if (Test-Path $templateFile) {
        Copy-Item $templateFile $mvpPlanFile -Force
    } else {
        @"
# MVP to Full Product Plan

**Project**: [PROJECT_NAME]
**Description**: $projectDesc

## MVP Features (Priority 1)
- [ ] Core Feature 1
- [ ] Core Feature 2  
- [ ] Basic Auth

## Full Product Features (Priority 2)
- [ ] Advanced Feature 1
- [ ] Analytics
- [ ] Advanced Auth

## Full Product Features (Priority 3)
- [ ] Premium Features
- [ ] Integrations
- [ ] Admin Panel

## Dependencies
``````
MVP Features -> Full Product P2 -> Full Product P3
``````

## Execution Plan
1. Analyze and identify specific features from project description
2. Create dependency graph
3. Execute workflow for each feature in order
"@ | Out-File -FilePath $mvpPlanFile -Encoding UTF8
    }
}

# Generate execution plan with project state awareness
$executionPlan = Join-Path $repoRoot 'execution-plan.json'
$planData = @{
    project_description = $projectDesc
    project_type = $projectType
    project_state = $projectStateResult
    mvp_plan_file = $mvpPlanFile
    specs_directory = $specsDir
    features = @()
    dependencies = @{}
    execution_order = @()
    status = "initialized"
} | ConvertTo-Json -Depth 3

$planData | Out-File -FilePath $executionPlan -Encoding UTF8

if ($Json) {
    $result = @{
        MVP_PLAN_FILE = $mvpPlanFile
        EXECUTION_PLAN = $executionPlan
        SPECS_DIR = $specsDir
        PROJECT_TYPE = $projectType
        PROJECT_STATE = $projectStateResult
        STATUS = "ready_for_analysis"
    } | ConvertTo-Json -Compress
    Write-Output $result
} else {
    Write-Output "MVP_PLAN_FILE: $mvpPlanFile"
    Write-Output "EXECUTION_PLAN: $executionPlan"
    Write-Output "SPECS_DIR: $specsDir"
    Write-Output "PROJECT_TYPE: $projectType"
    Write-Output "STATUS: ready_for_analysis"
}