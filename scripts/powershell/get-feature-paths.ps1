#!/usr/bin/env pwsh

# ==============================================================================
# Get Feature Paths Script (PowerShell)
# ==============================================================================
#
# DESCRIPTION:
#   PowerShell equivalent of the bash get-feature-paths.sh script.
#   Displays all relevant file and directory paths for the current feature branch
#   in the Spec-Driven Development workflow. This utility script helps developers
#   quickly identify where feature-related files are located and provides a
#   convenient way to inspect the current workspace configuration.
#
# USAGE:
#   .\get-feature-paths.ps1
#
# PREREQUISITES:
#   - Must be run from within a git repository
#   - Must be on a valid feature branch (format: XXX-feature-name)
#   - PowerShell 5.1+ or PowerShell Core 6+
#
# OUTPUT:
#   Displays the following paths:
#   - REPO_ROOT: Git repository root directory
#   - BRANCH: Current git branch name
#   - FEATURE_DIR: Feature-specific directory in specs/
#   - FEATURE_SPEC: Path to spec.md file
#   - IMPL_PLAN: Path to plan.md file
#   - TASKS: Path to tasks.md file
#
# EXIT CODES:
#   0 - Successfully displayed paths
#   1 - Not on a valid feature branch or other error
#
# EXAMPLES:
#   .\get-feature-paths.ps1
#
#   Example output:
#   REPO_ROOT: C:\Users\user\my-project
#   BRANCH: 001-user-authentication
#   FEATURE_DIR: C:\Users\user\my-project\specs\001-user-authentication
#   FEATURE_SPEC: C:\Users\user\my-project\specs\001-user-authentication\spec.md
#   IMPL_PLAN: C:\Users\user\my-project\specs\001-user-authentication\plan.md
#   TASKS: C:\Users\user\my-project\specs\001-user-authentication\tasks.md
#
# USE CASES:
#   - Debugging workflow scripts
#   - Setting up IDE workspace paths
#   - Creating custom automation scripts
#   - Troubleshooting missing files or directories
#
# RELATED SCRIPTS:
#   - common.ps1: Provides the path generation functions
#   - check-task-prerequisites.ps1: Uses these paths for validation
#   - get-feature-paths.sh: Bash equivalent of this script
#
# ==============================================================================

param()
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"

$paths = Get-FeaturePathsEnv
if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH)) { exit 1 }

Write-Output "REPO_ROOT: $($paths.REPO_ROOT)"
Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
Write-Output "TASKS: $($paths.TASKS)"
