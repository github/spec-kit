#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output @"
Usage: context-feature-info.ps1 [-Json]

Emit metadata about the active Context Engineering feature and workflow.
Outputs include workflow name, feature directory, key artifact paths, and checklist template hints.
"@
    exit 0
}

. "$PSScriptRoot/common.ps1"

$paths = Get-FeaturePaths
if (-not (Test-FeatureBranch -Branch $paths.FEATURE_NAME -HasGit:$paths.HAS_GIT)) {
    exit 1
}

if ($Json) {
    [PSCustomObject]@{
        REPO_ROOT = $paths.REPO_ROOT
        FEATURE = $paths.FEATURE_NAME
        WORKFLOW = $paths.WORKFLOW
        FEATURE_DIR = $paths.FEATURE_DIR
        PRIMARY_FILE = $paths.PRIMARY_FILE
        PLAN_FILE = $paths.PLAN_FILE
        RESEARCH_FILE = $paths.RESEARCH_FILE
        TASKS_FILE = $paths.TASKS_FILE
        PRP_FILE = $paths.PRP_FILE
        INITIAL_FILE = $paths.INITIAL_FILE
        CHECKLIST_TEMPLATE = $paths.CHECKLIST_TEMPLATE
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
    if ($paths.INITIAL_FILE) { Write-Output "INITIAL_FILE: $($paths.INITIAL_FILE)" }
    Write-Output "CHECKLIST_TEMPLATE: $($paths.CHECKLIST_TEMPLATE)"
}
