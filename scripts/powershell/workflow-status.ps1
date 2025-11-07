#!/usr/bin/env pwsh
#requires -version 5.1

<#
.SYNOPSIS
    Workflow Status Script - Detects current feature state and provides status information
.DESCRIPTION
    Analyzes the current Speckit workflow state and provides comprehensive status information
.PARAMETER Json
    Output results in JSON format
#>

param(
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

# Get repository root
function Get-RepoRoot {
    try {
        $gitRoot = git rev-parse --show-toplevel 2>$null
        if ($gitRoot) {
            return $gitRoot
        }
    } catch {
        # Not a git repository
    }
    return $PWD.Path
}

$RepoRoot = Get-RepoRoot

# Detect current feature
$CurrentBranch = ""
$FeatureNum = ""
$FeatureName = ""

try {
    $CurrentBranch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($CurrentBranch -match '^(\d+)-(.+)$') {
        $FeatureNum = $Matches[1]
        $FeatureName = $Matches[2]
    }
} catch {
    # Not on a git branch
}

# Detect specs directory
$SpecsDir = Join-Path $RepoRoot "specs"
$FeatureDir = ""
if ($FeatureNum -and (Test-Path (Join-Path $SpecsDir "$FeatureNum-$FeatureName"))) {
    $FeatureDir = Join-Path $SpecsDir "$FeatureNum-$FeatureName"
}

# Check file existence
$ConstitutionExists = Test-Path (Join-Path $RepoRoot "memory/constitution.md")
$SpecExists = $false
$PlanExists = $false
$TasksExists = $false
$ImplementationExists = $false

if ($FeatureDir) {
    $SpecExists = Test-Path (Join-Path $FeatureDir "spec.md")
    $PlanExists = Test-Path (Join-Path $FeatureDir "plan.md")
    $TasksExists = Test-Path (Join-Path $FeatureDir "tasks.md")
}

# Check for implementation files
$SrcDir = Join-Path $RepoRoot "src"
if ((Test-Path $SrcDir) -or
    (Get-ChildItem -Path $RepoRoot -Recurse -Depth 3 -Include "*.js","*.ts","*.py","*.go","*.java","*.cs","*.rs" -ErrorAction SilentlyContinue | Select-Object -First 1)) {
    $ImplementationExists = $true
}

# Calculate task completion
$TotalTasks = 0
$CompletedTasks = 0
$CompletionPercentage = 0

if ($TasksExists) {
    $TasksFile = Join-Path $FeatureDir "tasks.md"
    $Content = Get-Content $TasksFile -Raw

    $AllTasks = [regex]::Matches($Content, '^\s*- \[[ Xx]\]', 'Multiline')
    $TotalTasks = $AllTasks.Count

    $CompletedMatches = [regex]::Matches($Content, '^\s*- \[[Xx]\]', 'Multiline')
    $CompletedTasks = $CompletedMatches.Count

    if ($TotalTasks -gt 0) {
        $CompletionPercentage = [math]::Floor(($CompletedTasks / $TotalTasks) * 100)
    }
}

# Determine phase
$Phase = "0"
$PhaseName = "Setup"
$NextCommand = ""
$Explanation = ""

if (-not $ConstitutionExists) {
    $Phase = "0"
    $PhaseName = "Setup"
    $NextCommand = "/speckit.constitution"
    $Explanation = "Establish project principles and development guidelines that will guide all subsequent development."
}
elseif (-not $FeatureDir) {
    $Phase = "1"
    $PhaseName = "Ready for Feature"
    $NextCommand = "/speckit.specify [feature description]"
    $Explanation = "Create a new feature specification. Describe what you want to build in plain language."
}
elseif ($SpecExists -and -not $PlanExists) {
    $Phase = "2"
    $PhaseName = "Specification Complete"
    $NextCommand = "/speckit.plan [tech stack]"
    $Explanation = "Create a technical implementation plan. Specify your tech stack (e.g., 'Next.js 14, PostgreSQL, Prisma')."
}
elseif ($PlanExists -and -not $TasksExists) {
    $Phase = "3"
    $PhaseName = "Planning Complete"
    $NextCommand = "/speckit.tasks"
    $Explanation = "Generate a detailed task breakdown from your implementation plan."
}
elseif ($TasksExists -and $CompletionPercentage -eq 0) {
    $Phase = "4"
    $PhaseName = "Ready for Implementation"
    $NextCommand = "/speckit.implement"
    $Explanation = "Execute all tasks and build your feature according to the plan."
}
elseif ($TasksExists -and $CompletionPercentage -gt 0 -and $CompletionPercentage -lt 100) {
    $Phase = "5"
    $PhaseName = "Implementation in Progress"
    $NextCommand = "/speckit.implement"
    $Explanation = "Continue implementation. Current progress: $CompletionPercentage%"
}
elseif ($TasksExists -and $CompletionPercentage -eq 100) {
    $Phase = "6"
    $PhaseName = "Implementation Complete"
    $NextCommand = "/speckit.document"
    $Explanation = "Generate documentation for your completed feature."
}

# Calculate token budget (approximate)
$TokenBudgetUsed = 0
$TokenBudgetTotal = 200

if ($FeatureDir) {
    $SpecFile = Join-Path $FeatureDir "spec.md"
    if (Test-Path $SpecFile) {
        $SpecWords = (Get-Content $SpecFile -Raw | Measure-Object -Word).Words
        $TokenBudgetUsed += [math]::Floor($SpecWords * 4 / 3)
    }

    $PlanFile = Join-Path $FeatureDir "plan.md"
    if (Test-Path $PlanFile) {
        $PlanWords = (Get-Content $PlanFile -Raw | Measure-Object -Word).Words
        $TokenBudgetUsed += [math]::Floor($PlanWords * 4 / 3)
    }

    $TasksFile = Join-Path $FeatureDir "tasks.md"
    if (Test-Path $TasksFile) {
        $TasksWords = (Get-Content $TasksFile -Raw | Measure-Object -Word).Words
        $TokenBudgetUsed += [math]::Floor($TasksWords * 4 / 3)
    }
}

$TokenPercentage = 0
if ($TokenBudgetTotal -gt 0) {
    $TokenPercentage = [math]::Floor(($TokenBudgetUsed / $TokenBudgetTotal) * 100)
}

# Spec quality score (simple heuristic)
$SpecQuality = 0
if ($SpecExists) {
    $SpecFile = Join-Path $FeatureDir "spec.md"
    $SpecContent = Get-Content $SpecFile -Raw
    $SpecSize = $SpecContent.Length
    $Clarifications = ([regex]::Matches($SpecContent, '\[NEEDS CLARIFICATION')).Count

    $MandatorySections = 0
    if ($SpecContent -match '## User Scenarios') { $MandatorySections++ }
    if ($SpecContent -match '## Requirements') { $MandatorySections++ }
    if ($SpecContent -match '## Success Criteria') { $MandatorySections++ }

    if ($SpecSize -gt 2000 -and $MandatorySections -eq 3 -and $Clarifications -eq 0) {
        $SpecQuality = 10
    }
    elseif ($SpecSize -gt 1000 -and $MandatorySections -ge 2) {
        $SpecQuality = 7
    }
    elseif ($MandatorySections -gt 0) {
        $SpecQuality = 5
    }
    else {
        $SpecQuality = 3
    }
}

# Count checklists
$ChecklistsTotal = 0
$ChecklistsComplete = 0
$ChecklistsDir = Join-Path $FeatureDir "checklists"
if (Test-Path $ChecklistsDir) {
    $Checklists = Get-ChildItem -Path $ChecklistsDir -Filter "*.md"
    $ChecklistsTotal = $Checklists.Count

    foreach ($Checklist in $Checklists) {
        $Content = Get-Content $Checklist.FullName -Raw
        $Incomplete = ([regex]::Matches($Content, '^\s*- \[ \]', 'Multiline')).Count
        if ($Incomplete -eq 0) {
            $ChecklistsComplete++
        }
    }
}

# Output
if ($Json) {
    $Output = @{
        feature_number = $FeatureNum
        feature_name = $FeatureName
        branch = $CurrentBranch
        phase = $Phase
        phase_name = $PhaseName
        next_command = $NextCommand
        explanation = $Explanation
        constitution_exists = $ConstitutionExists
        spec_exists = $SpecExists
        plan_exists = $PlanExists
        tasks_exists = $TasksExists
        implementation_exists = $ImplementationExists
        total_tasks = $TotalTasks
        completed_tasks = $CompletedTasks
        completion_percentage = $CompletionPercentage
        token_budget_used = $TokenBudgetUsed
        token_budget_total = $TokenBudgetTotal
        token_percentage = $TokenPercentage
        spec_quality = $SpecQuality
        validation_status = "not_run"
        checklists_total = $ChecklistsTotal
        checklists_complete = $ChecklistsComplete
        feature_dir = $FeatureDir
        specs_dir = $SpecsDir
    }

    $Output | ConvertTo-Json -Depth 10
}
else {
    # Human-readable output
    Write-Host "Status information:"
    Write-Host "  Feature: $FeatureNum-$FeatureName"
    Write-Host "  Branch: $CurrentBranch"
    Write-Host "  Phase: $Phase - $PhaseName"
    Write-Host "  Progress: $CompletionPercentage%"
    Write-Host "  Next: $NextCommand"
}
