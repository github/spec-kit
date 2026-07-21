#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = 'Stop'

# Help wins over unknown-argument validation to match the Bash/Python
# variants, which stop at --help and exit 0.
if ($Help) {
    Write-Output "Usage: setup-tasks.ps1 [-Json] [-Help]"
    exit 0
}

if ($RemainingArgs.Count -gt 0) {
    [Console]::Error.WriteLine("ERROR: Unknown option '$($RemainingArgs[0])'")
    exit 1
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get feature paths
$paths = Get-FeaturePathsEnv -ReturnNullOnError
if (-not $paths) {
    [Console]::Error.WriteLine("ERROR: Failed to resolve feature paths")
    exit 1
}

if (-not (Test-Path $paths.IMPL_PLAN -PathType Leaf)) {
    [Console]::Error.WriteLine("ERROR: plan.md not found in $($paths.FEATURE_DIR)")
    $planCommand = Format-SpecKitCommand -CommandName 'plan' -RepoRoot $paths.REPO_ROOT
    [Console]::Error.WriteLine("Run $planCommand first to create the implementation plan.")
    exit 1
}

if (-not (Test-Path $paths.FEATURE_SPEC -PathType Leaf)) {
    [Console]::Error.WriteLine("ERROR: spec.md not found in $($paths.FEATURE_DIR)")
    $specifyCommand = Format-SpecKitCommand -CommandName 'specify' -RepoRoot $paths.REPO_ROOT
    [Console]::Error.WriteLine("Run $specifyCommand first to create the feature structure.")
    exit 1
}

# Build available docs list
$docs = @()
if (Test-Path $paths.RESEARCH) { $docs += 'research.md' }
if (Test-Path $paths.DATA_MODEL) { $docs += 'data-model.md' }
if ((Test-Path $paths.CONTRACTS_DIR) -and (Get-ChildItem -Path $paths.CONTRACTS_DIR -ErrorAction SilentlyContinue | Select-Object -First 1)) {
    $docs += 'contracts/'
}
if (Test-Path $paths.QUICKSTART) { $docs += 'quickstart.md' }

# Resolve tasks template through override stack
$tasksTemplate = Resolve-Template -TemplateName 'tasks-template' -RepoRoot $paths.REPO_ROOT
if (-not $tasksTemplate -or -not (Test-Path -LiteralPath $tasksTemplate -PathType Leaf)) {
    [Console]::Error.WriteLine("ERROR: Could not resolve required tasks-template from the template override stack for $($paths.REPO_ROOT)")
    [Console]::Error.WriteLine("Template 'tasks-template' was not found in any supported location (overrides, presets, extensions, or shared core). Add an override at .specify/templates/overrides/tasks-template.md, or run 'specify init' / reinstall shared infra to restore the core .specify/templates/tasks-template.md template.")
    exit 1
}
$tasksTemplate = (Resolve-Path -LiteralPath $tasksTemplate).Path

# Output results
if ($Json) {
    [PSCustomObject]@{
        FEATURE_DIR    = $paths.FEATURE_DIR
        AVAILABLE_DOCS = $docs
        TASKS_TEMPLATE = $tasksTemplate
    } | ConvertTo-Json -Compress
} else {
    Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
    Write-Output "TASKS_TEMPLATE: $(if ($tasksTemplate) { $tasksTemplate } else { 'not found' })"
    Write-Output "AVAILABLE_DOCS:"
    Test-FileExists -Path $paths.RESEARCH -Description 'research.md' | Out-Null
    Test-FileExists -Path $paths.DATA_MODEL -Description 'data-model.md' | Out-Null
    Test-DirHasFiles -Path $paths.CONTRACTS_DIR -Description 'contracts/' | Out-Null
    Test-FileExists -Path $paths.QUICKSTART -Description 'quickstart.md' | Out-Null
}
