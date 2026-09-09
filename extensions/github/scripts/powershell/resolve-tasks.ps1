#!/usr/bin/env pwsh

# Resolve the active feature and its tasks.md for the github extension.
#
# Deliberately self-contained: the github extension owns this script so that
# speckit.github.taskstoissues keeps working when the core taskstoissues
# command (and its check-prerequisites helper invocation) is deprecated and
# removed. It is a trimmed twin of core check-prerequisites.ps1 -- it resolves
# the project root and the active feature directory, requires tasks.md, and
# reports the optional design docs that sit next to it. It performs none of
# core's plan.md/spec.md gating and never writes .specify/feature.json.
#
# Usage: ./resolve-tasks.ps1 [-Json]
#
# OPTIONS:
#   -Json       Output in JSON format
#   -Help       Show help message
#
# OUTPUTS:
#   JSON mode: {"FEATURE_DIR":"...","TASKS":"...","AVAILABLE_DOCS":["..."]}
#   Text mode: FEATURE_DIR:... / TASKS:... / AVAILABLE_DOCS: list

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output @"
Usage: resolve-tasks.ps1 [OPTIONS]

Resolve the active feature and its tasks.md for the github extension.

OPTIONS:
  -Json       Output in JSON format
  -Help       Show this help message

EXAMPLES:
  ./resolve-tasks.ps1 -Json
"@
    exit 0
}

# Find the project root by searching upward for the .specify marker directory.
function Find-SpecifyRoot {
    param([string]$StartDir = (Get-Location).Path)

    $resolved = Resolve-Path -LiteralPath $StartDir -ErrorAction SilentlyContinue
    $current = if ($resolved) { $resolved.Path } else { $null }
    if (-not $current) { return $null }

    while ($true) {
        if (Test-Path -LiteralPath (Join-Path $current ".specify") -PathType Container) {
            return $current
        }
        $parent = Split-Path $current -Parent
        if ([string]::IsNullOrEmpty($parent) -or $parent -eq $current) {
            return $null
        }
        $current = $parent
    }
}

# Resolve the project root, honouring an explicit SPECIFY_INIT_DIR override.
# Mirrors core Get-RepoRoot: strict on an invalid override, no silent fallback.
function Get-ProjectRoot {
    if ($env:SPECIFY_INIT_DIR) {
        $initDir = $env:SPECIFY_INIT_DIR
        if (-not [System.IO.Path]::IsPathRooted($initDir)) {
            $initDir = Join-Path (Get-Location).Path $initDir
        }
        $resolved = Resolve-Path -LiteralPath $initDir -ErrorAction SilentlyContinue
        if (-not $resolved -or -not (Test-Path -LiteralPath $resolved.Path -PathType Container)) {
            [Console]::Error.WriteLine("ERROR: SPECIFY_INIT_DIR does not point to an existing directory: $($env:SPECIFY_INIT_DIR)")
            exit 1
        }
        # TrimEnd (not [Path]::TrimEndingDirectorySeparator, which is .NET Core
        # only) keeps this working on Windows PowerShell 5.1, while the
        # GetPathRoot check preserves a path that *is* its own root ('C:\').
        $initRoot = $resolved.Path.TrimEnd('/', '\')
        if ($initRoot.Length -lt [System.IO.Path]::GetPathRoot($resolved.Path).Length) {
            $initRoot = $resolved.Path
        }
        if (-not (Test-Path -LiteralPath (Join-Path $initRoot '.specify') -PathType Container)) {
            [Console]::Error.WriteLine("ERROR: SPECIFY_INIT_DIR is not a Spec Kit project (no .specify/ directory): $initRoot")
            exit 1
        }
        return $initRoot
    }

    $specifyRoot = Find-SpecifyRoot
    if ($specifyRoot) { return $specifyRoot }

    # Installed scripts live at .specify/extensions/github/scripts/powershell/.
    $fromScript = Find-SpecifyRoot -StartDir $PSScriptRoot
    if ($fromScript) { return $fromScript }

    [Console]::Error.WriteLine("ERROR: Not inside a Spec Kit project (no .specify/ directory found).")
    exit 1
}

$repoRoot = Get-ProjectRoot

# Resolve the feature directory. Priority:
#   1. SPECIFY_FEATURE_DIRECTORY (explicit override)
#   2. .specify/feature.json "feature_directory"
# Read-only by design: unlike core, this never persists feature.json (#3025).
$featureJson = Join-Path $repoRoot '.specify/feature.json'
if ($env:SPECIFY_FEATURE_DIRECTORY) {
    $featureDir = $env:SPECIFY_FEATURE_DIRECTORY
} elseif (Test-Path -LiteralPath $featureJson -PathType Leaf) {
    # Read as UTF-8 explicitly: Windows PowerShell 5.1 otherwise decodes with
    # the legacy ANSI code page and mangles non-ASCII feature paths (#4359).
    $featureJsonRaw = [System.IO.File]::ReadAllText($featureJson, [System.Text.Encoding]::UTF8)
    try {
        $featureConfig = $featureJsonRaw | ConvertFrom-Json
    } catch {
        [Console]::Error.WriteLine("ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY or ensure .specify/feature.json contains feature_directory.")
        exit 1
    }
    if ($featureConfig.feature_directory) {
        $featureDir = $featureConfig.feature_directory
    } else {
        [Console]::Error.WriteLine("ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY or ensure .specify/feature.json contains feature_directory.")
        exit 1
    }
} else {
    [Console]::Error.WriteLine("ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY or run the specify command to create .specify/feature.json.")
    exit 1
}

if (-not [System.IO.Path]::IsPathRooted($featureDir)) {
    $featureDir = Join-Path $repoRoot $featureDir
}

if (-not (Test-Path -LiteralPath $featureDir -PathType Container)) {
    [Console]::Error.WriteLine("ERROR: Feature directory not found: $featureDir")
    [Console]::Error.WriteLine("Run the Spec Kit specify command (e.g. /speckit.specify) first to create the feature structure.")
    exit 1
}

$tasks = Join-Path $featureDir 'tasks.md'
if (-not (Test-Path -LiteralPath $tasks -PathType Leaf)) {
    [Console]::Error.WriteLine("ERROR: tasks.md not found in $featureDir")
    [Console]::Error.WriteLine("Run the Spec Kit tasks command (e.g. /speckit.tasks) first to create the task list.")
    exit 1
}

$docs = @()
if (Test-Path -LiteralPath (Join-Path $featureDir 'research.md') -PathType Leaf) { $docs += 'research.md' }
if (Test-Path -LiteralPath (Join-Path $featureDir 'data-model.md') -PathType Leaf) { $docs += 'data-model.md' }
$contractsDir = Join-Path $featureDir 'contracts'
if ((Test-Path -LiteralPath $contractsDir -PathType Container) -and
    (Get-ChildItem -LiteralPath $contractsDir -Force -ErrorAction SilentlyContinue | Select-Object -First 1)) {
    $docs += 'contracts/'
}
if (Test-Path -LiteralPath (Join-Path $featureDir 'quickstart.md') -PathType Leaf) { $docs += 'quickstart.md' }
$docs += 'tasks.md'

if ($Json) {
    # -Compress keeps the payload on a single line, matching the bash twin.
    $payload = [ordered]@{
        FEATURE_DIR    = $featureDir
        TASKS          = $tasks
        AVAILABLE_DOCS = @($docs)
    }
    Write-Output ($payload | ConvertTo-Json -Compress)
} else {
    Write-Output "FEATURE_DIR:$featureDir"
    Write-Output "TASKS:$tasks"
    Write-Output "AVAILABLE_DOCS:"
    foreach ($d in $docs) {
        Write-Output "  [OK] $d"
    }
}
