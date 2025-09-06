<#
.SYNOPSIS
    Get paths for current feature branch without creating anything
.DESCRIPTION
    This script outputs the paths for the current feature branch's files and directories.
    It's used by other commands that need to find existing feature files.
.EXAMPLE
    .\Get-FeaturePaths.ps1
    Get paths for the current feature branch
#>

# Import common functions
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module (Join-Path $scriptPath "Common.psm1") -Force

try {
    # Get feature paths
    $paths = Get-FeaturePaths
    
    # Check if on feature branch
    if (-not (Test-FeatureBranch -Branch $paths.CurrentBranch)) {
        exit 1
    }
    
    # Output paths in key: value format for compatibility with shell scripts
    @(
        "REPO_ROOT: $($paths.RepoRoot)",
        "BRANCH: $($paths.CurrentBranch)",
        "FEATURE_DIR: $($paths.FeatureDir)",
        "FEATURE_SPEC: $($paths.FeatureSpec)",
        "IMPL_PLAN: $($paths.ImplPlan)",
        "TASKS: $($paths.Tasks)",
        "RESEARCH: $($paths.Research)",
        "DATA_MODEL: $($paths.DataModel)",
        "QUICKSTART: $($paths.QuickStart)",
        "CONTRACTS_DIR: $($paths.ContractsDir)"
    ) | ForEach-Object { Write-Output $_ }
    
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
