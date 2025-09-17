#!/usr/bin/env pwsh

# ==============================================================================
# Check Task Prerequisites Script (PowerShell)
# ==============================================================================
#
# DESCRIPTION:
#   PowerShell equivalent of the bash check-task-prerequisites.sh script.
#   Validates that all required prerequisites are in place before starting
#   implementation tasks in the Spec-Driven Development workflow. This script
#   ensures that the current branch is a valid feature branch, that the feature
#   directory structure exists, and that essential planning documents are present.
#
# USAGE:
#   .\check-task-prerequisites.ps1 [-Json]
#
# PARAMETERS:
#   -Json         Output results in JSON format for programmatic consumption
#
# PREREQUISITES:
#   - Must be run from within a git repository
#   - Must be on a feature branch (format: XXX-feature-name)
#   - Feature directory must exist in specs/
#   - plan.md must exist in the feature directory
#   - PowerShell 5.1+ or PowerShell Core 6+
#
# OUTPUT:
#   In default mode: Displays feature directory path and available documentation files
#   In JSON mode: Returns structured JSON with FEATURE_DIR and AVAILABLE_DOCS array
#
# EXIT CODES:
#   0 - All prerequisites met successfully
#   1 - Missing prerequisites or invalid branch/directory structure
#
# EXAMPLES:
#   .\check-task-prerequisites.ps1
#   .\check-task-prerequisites.ps1 -Json
#
# RELATED SCRIPTS:
#   - common.ps1: Provides shared functions for path resolution and validation
#   - create-new-feature.ps1: Creates the feature structure that this script validates
#   - setup-plan.ps1: Creates the plan.md file that this script requires
#   - check-task-prerequisites.sh: Bash equivalent of this script
#
# ==============================================================================

[CmdletBinding()]
param([switch]$Json)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/common.ps1"

$paths = Get-FeaturePathsEnv
if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH)) { exit 1 }

if (-not (Test-Path $paths.FEATURE_DIR -PathType Container)) {
    Write-Output "ERROR: Feature directory not found: $($paths.FEATURE_DIR)"
    Write-Output "Run /specify first to create the feature structure."
    exit 1
}
if (-not (Test-Path $paths.IMPL_PLAN -PathType Leaf)) {
    Write-Output "ERROR: plan.md not found in $($paths.FEATURE_DIR)"
    Write-Output "Run /plan first to create the plan."
    exit 1
}

if ($Json) {
    $docs = @()
    if (Test-Path $paths.RESEARCH) { $docs += 'research.md' }
    if (Test-Path $paths.DATA_MODEL) { $docs += 'data-model.md' }
    if ((Test-Path $paths.CONTRACTS_DIR) -and (Get-ChildItem -Path $paths.CONTRACTS_DIR -ErrorAction SilentlyContinue | Select-Object -First 1)) { $docs += 'contracts/' }
    if (Test-Path $paths.QUICKSTART) { $docs += 'quickstart.md' }
    [PSCustomObject]@{ FEATURE_DIR=$paths.FEATURE_DIR; AVAILABLE_DOCS=$docs } | ConvertTo-Json -Compress
} else {
    Write-Output "FEATURE_DIR:$($paths.FEATURE_DIR)"
    Write-Output "AVAILABLE_DOCS:"
    Test-FileExists -Path $paths.RESEARCH -Description 'research.md' | Out-Null
    Test-FileExists -Path $paths.DATA_MODEL -Description 'data-model.md' | Out-Null
    Test-DirHasFiles -Path $paths.CONTRACTS_DIR -Description 'contracts/' | Out-Null
    Test-FileExists -Path $paths.QUICKSTART -Description 'quickstart.md' | Out-Null
}
