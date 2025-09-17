#!/usr/bin/env pwsh

# ==============================================================================
# Setup Implementation Plan Script (PowerShell)
# ==============================================================================
#
# DESCRIPTION:
#   PowerShell equivalent of the bash setup-plan.sh script.
#   Creates the implementation plan (plan.md) for the current feature by copying
#   the plan template into the feature directory. This is the second step in the
#   Spec-Driven Development workflow, following the feature specification creation.
#   The plan.md file contains technical implementation details, architecture
#   decisions, and step-by-step implementation guidance.
#
# USAGE:
#   .\setup-plan.ps1 [-Json]
#
# PARAMETERS:
#   -Json         Output results in JSON format for programmatic consumption
#
# PREREQUISITES:
#   - Must be run from within a git repository
#   - Must be on a valid feature branch (format: XXX-feature-name)
#   - Feature directory should exist (created by create-new-feature.ps1)
#   - PowerShell 5.1+ or PowerShell Core 6+
#
# TEMPLATE LOCATION:
#   The script looks for the plan template at:
#   $REPO_ROOT/templates/plan-template.md
#   If the template doesn't exist, the script will still create the target
#   directory structure but won't copy any template content.
#
# OUTPUT:
#   In default mode: Displays paths for feature spec, implementation plan,
#                   feature directory, and current branch
#   In JSON mode: Returns structured JSON with the same information
#
# EXIT CODES:
#   0 - Plan setup completed successfully
#   1 - Not on a valid feature branch or other error
#
# WORKFLOW INTEGRATION:
#   This script is typically called as part of the /plan command in AI coding
#   assistants, after the initial feature specification has been created but
#   before implementation begins.
#
# EXAMPLES:
#   .\setup-plan.ps1
#   .\setup-plan.ps1 -Json
#
# RELATED SCRIPTS:
#   - create-new-feature.ps1: Previous step that creates the feature structure
#   - check-task-prerequisites.ps1: Validates that plan.md exists before implementation
#   - common.ps1: Provides shared path resolution functions
#   - setup-plan.sh: Bash equivalent of this script
#
# ==============================================================================

[CmdletBinding()]
param([switch]$Json)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/common.ps1"

$paths = Get-FeaturePathsEnv
if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH)) { exit 1 }

New-Item -ItemType Directory -Path $paths.FEATURE_DIR -Force | Out-Null
$template = Join-Path $paths.REPO_ROOT 'templates/plan-template.md'
if (Test-Path $template) { Copy-Item $template $paths.IMPL_PLAN -Force }

if ($Json) {
    [PSCustomObject]@{ FEATURE_SPEC=$paths.FEATURE_SPEC; IMPL_PLAN=$paths.IMPL_PLAN; SPECS_DIR=$paths.FEATURE_DIR; BRANCH=$paths.CURRENT_BRANCH } | ConvertTo-Json -Compress
} else {
    Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
    Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
    Write-Output "SPECS_DIR: $($paths.FEATURE_DIR)"
    Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
}
