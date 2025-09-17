#!/usr/bin/env pwsh

# ==============================================================================
# Common Functions Library (PowerShell)
# ==============================================================================
#
# DESCRIPTION:
#   PowerShell equivalent of the bash common.sh library. Provides shared utility
#   functions and path resolution logic used across all Spec-Driven Development
#   workflow scripts. This library ensures consistent behavior for git operations,
#   feature branch validation, and file system path management in Windows and
#   cross-platform PowerShell environments.
#
# FUNCTIONS:
#   Get-RepoRoot()           - Returns the root directory of the git repository
#   Get-CurrentBranch()      - Returns the name of the current git branch
#   Test-FeatureBranch()     - Validates feature branch naming convention
#   Get-FeatureDir()         - Constructs feature directory path from repo root and branch
#   Get-FeaturePathsEnv()    - Generates all standard feature-related file paths
#   Test-FileExists()        - Displays file existence status with checkmark/X
#   Test-DirHasFiles()       - Displays directory existence status with contents check
#
# FEATURE BRANCH NAMING CONVENTION:
#   Feature branches must follow the pattern: XXX-feature-name
#   Where XXX is a 3-digit zero-padded number (001, 002, etc.)
#   Examples: 001-user-authentication, 042-payment-integration
#
# STANDARD FEATURE DIRECTORY STRUCTURE:
#   specs/XXX-feature-name/
#   ├── spec.md           # Feature specification (required)
#   ├── plan.md           # Implementation plan (required)
#   ├── tasks.md          # Task breakdown (optional)
#   ├── research.md       # Research notes (optional)
#   ├── data-model.md     # Data model documentation (optional)
#   ├── quickstart.md     # Quick start guide (optional)
#   └── contracts/        # API contracts and interfaces (optional)
#
# USAGE:
#   This file should be dot-sourced by other PowerShell scripts:
#   . "$PSScriptRoot/common.ps1"
#   $paths = Get-FeaturePathsEnv
#
# DEPENDENCIES:
#   - git (for repository operations)
#   - PowerShell 5.1+ or PowerShell Core 6+ (for cross-platform support)
#
# CROSS-PLATFORM NOTES:
#   - Uses Join-Path for proper path handling across Windows/Linux/macOS
#   - Compatible with both Windows PowerShell and PowerShell Core
#   - Handles both forward and backward slashes appropriately
#
# ==============================================================================

function Get-RepoRoot {
    git rev-parse --show-toplevel
}

function Get-CurrentBranch {
    git rev-parse --abbrev-ref HEAD
}

function Test-FeatureBranch {
    param([string]$Branch)
    if ($Branch -notmatch '^[0-9]{3}-') {
        Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"
        Write-Output "Feature branches should be named like: 001-feature-name"
        return $false
    }
    return $true
}

function Get-FeatureDir {
    param([string]$RepoRoot, [string]$Branch)
    Join-Path $RepoRoot "specs/$Branch"
}

function Get-FeaturePathsEnv {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $currentBranch
    [PSCustomObject]@{
        REPO_ROOT    = $repoRoot
        CURRENT_BRANCH = $currentBranch
        FEATURE_DIR  = $featureDir
        FEATURE_SPEC = Join-Path $featureDir 'spec.md'
        IMPL_PLAN    = Join-Path $featureDir 'plan.md'
        TASKS        = Join-Path $featureDir 'tasks.md'
        RESEARCH     = Join-Path $featureDir 'research.md'
        DATA_MODEL   = Join-Path $featureDir 'data-model.md'
        QUICKSTART   = Join-Path $featureDir 'quickstart.md'
        CONTRACTS_DIR = Join-Path $featureDir 'contracts'
    }
}

function Test-FileExists {
    param([string]$Path, [string]$Description)
    if (Test-Path -Path $Path -PathType Leaf) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}

function Test-DirHasFiles {
    param([string]$Path, [string]$Description)
    if ((Test-Path -Path $Path -PathType Container) -and (Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer } | Select-Object -First 1)) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}
