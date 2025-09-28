#!/usr/bin/env pwsh

# Context Engineering Kit prerequisite checker (PowerShell)

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RequireTasks,
    [switch]$IncludeTasks,
    [switch]$PathsOnly,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output @"
Usage: check-prerequisites.ps1 [OPTIONS]

Ensure required artifacts exist for the active context engineering workflow.

OPTIONS:
  -Json               Return JSON output
  -RequireTasks       Fail when tasks.md is missing
  -IncludeTasks       Include tasks.md in AVAILABLE_DOCS list
  -PathsOnly          Emit paths only, skip validation
  -Help, -h           Show this help message
"@
    exit 0
}

. "$PSScriptRoot/common.ps1"

$paths = Get-FeaturePaths
if (-not (Test-FeatureBranch -Branch $paths.FEATURE_NAME -HasGit:$paths.HAS_GIT)) {
    exit 1
}

if ($PathsOnly) {
    if ($Json) {
        [PSCustomObject]@{
            REPO_ROOT   = $paths.REPO_ROOT
            FEATURE     = $paths.FEATURE_NAME
            WORKFLOW    = $paths.WORKFLOW
            FEATURE_DIR = $paths.FEATURE_DIR
            PRIMARY_FILE = $paths.PRIMARY_FILE
            PLAN_FILE    = $paths.PLAN_FILE
            RESEARCH_FILE = $paths.RESEARCH_FILE
            TASKS_FILE    = $paths.TASKS_FILE
            PRP_FILE      = $paths.PRP_FILE
        } | ConvertTo-Json -Compress
    } else {
        Write-Output "REPO_ROOT: $($paths.REPO_ROOT)"
        Write-Output "FEATURE: $($paths.FEATURE_NAME)"
        Write-Output "WORKFLOW: $($paths.WORKFLOW)"
        Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
        Write-Output "PRIMARY_FILE: $($paths.PRIMARY_FILE)"
        Write-Output "PLAN_FILE: $($paths.PLAN_FILE)"
        Write-Output "RESEARCH_FILE: $($paths.RESEARCH_FILE)"
        Write-Output "TASKS_FILE: $($paths.TASKS_FILE)"
        if ($paths.PRP_FILE) { Write-Output "PRP_FILE: $($paths.PRP_FILE)" }
    }
    exit 0
}

if (-not ($paths.FEATURE_DIR -and (Test-Path $paths.FEATURE_DIR -PathType Container))) {
    Write-Output "ERROR: Feature directory not found: $($paths.FEATURE_DIR)"
    Write-Output "Run /specify to bootstrap the workflow artifacts."
    exit 1
}

if (-not (Test-Path $paths.PRIMARY_FILE -PathType Leaf)) {
    Write-Output "ERROR: Primary context file missing at $($paths.PRIMARY_FILE)"
    Write-Output "Run /specify to regenerate the initial artifact."
    exit 1
}

if (-not (Test-Path $paths.PLAN_FILE -PathType Leaf)) {
    switch ($paths.WORKFLOW) {
        'free-style' {
            Write-Output "ERROR: Plan file missing at $($paths.PLAN_FILE)"
            Write-Output "Run /create-plan before continuing."
        }
        'prp' {
            Write-Output "ERROR: Plan file missing at $($paths.PLAN_FILE)"
            Write-Output "Run /execute-prp to derive the execution plan."
        }
        'all-in-one' {
            Write-Output "ERROR: Plan file missing at $($paths.PLAN_FILE)"
            Write-Output "Run /context-engineer to update the plan section."
        }
    }
    exit 1
}

if ($RequireTasks -and -not (Test-Path $paths.TASKS_FILE -PathType Leaf)) {
    Write-Output "ERROR: tasks.md missing for $($paths.FEATURE_NAME)"
    Write-Output "Capture tasks from your plan or PRP before implementation."
    exit 1
}

$docs = @()
if (Test-Path $paths.PRIMARY_FILE) { $docs += (Split-Path $paths.PRIMARY_FILE -Leaf) }
if (Test-Path $paths.PLAN_FILE) { $docs += (Split-Path $paths.PLAN_FILE -Leaf) }
if (Test-Path $paths.RESEARCH_FILE) { $docs += (Split-Path $paths.RESEARCH_FILE -Leaf) }
if ($paths.PRP_FILE -and (Test-Path $paths.PRP_FILE)) { $docs += (Split-Path $paths.PRP_FILE -Leaf) }
if ($IncludeTasks -and (Test-Path $paths.TASKS_FILE)) { $docs += 'tasks.md' }

if ($Json) {
    [PSCustomObject]@{
        FEATURE_DIR = $paths.FEATURE_DIR
        WORKFLOW = $paths.WORKFLOW
        AVAILABLE_DOCS = $docs
    } | ConvertTo-Json -Compress
} else {
    Write-Output "FEATURE_DIR:$($paths.FEATURE_DIR)"
    Write-Output "WORKFLOW:$($paths.WORKFLOW)"
    Write-Output "AVAILABLE_DOCS:"
    foreach ($doc in $docs) {
        Write-Output "  ✓ $doc"
    }
    if ($IncludeTasks -and -not (Test-Path $paths.TASKS_FILE)) {
        Write-Output "  ✗ tasks.md"
    }
}