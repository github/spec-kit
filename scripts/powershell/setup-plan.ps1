#!/usr/bin/env pwsh
# Setup implementation plan for a feature

[CmdletBinding()]
param(
    [switch]$Json,
    [int]$ScanDepth = 0,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output "Usage: ./setup-plan.ps1 [-Json] [-ScanDepth N] [-Help]"
    Write-Output "  -Json        Output results in JSON format"
    Write-Output "  -ScanDepth N Max directory depth for nested repo discovery (default: 2)"
    Write-Output "  -Help        Show this help message"
    exit 0
}

# Load common functions
. "$PSScriptRoot/common.ps1"

# Get all paths and variables from common functions
$paths = Get-FeaturePathsEnv

# Check if we're on a proper feature branch (only for git repos)
if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -HasGit $paths.HAS_GIT)) { 
    exit 1 
}

# Ensure the feature directory exists
New-Item -ItemType Directory -Path $paths.FEATURE_DIR -Force | Out-Null

# Copy plan template if it exists, otherwise note it or create empty file
$template = Resolve-Template -TemplateName 'plan-template' -RepoRoot $paths.REPO_ROOT
if ($template -and (Test-Path $template)) { 
    Copy-Item $template $paths.IMPL_PLAN -Force
    Write-Output "Copied plan template to $($paths.IMPL_PLAN)"
} else {
    Write-Warning "Plan template not found"
    # Create a basic plan file if template doesn't exist
    New-Item -ItemType File -Path $paths.IMPL_PLAN -Force | Out-Null
}

# Discover nested independent git repositories (for AI agent to analyze)
$nestedReposResult = @()
if ($paths.HAS_GIT -eq 'true' -or $paths.HAS_GIT -eq $true) {
    $effectiveDepth = if ($ScanDepth -gt 0) { $ScanDepth } else { 2 }
    $initOptions = Join-Path $paths.REPO_ROOT '.specify' 'init-options.json'
    $explicitPaths = @()

    # Read explicit nested_repos from init-options.json if available
    if (Test-Path -LiteralPath $initOptions) {
        try {
            $opts = Get-Content $initOptions -Raw | ConvertFrom-Json
            if ($opts.nested_repos -and $opts.nested_repos.Count -gt 0) {
                $explicitPaths = @($opts.nested_repos)
            }
        } catch { }
    }

    if ($explicitPaths.Count -gt 0) {
        $nestedRepos = Find-NestedGitRepos -RepoRoot $paths.REPO_ROOT -MaxDepth $effectiveDepth -ExplicitPaths $explicitPaths
    } else {
        $nestedRepos = Find-NestedGitRepos -RepoRoot $paths.REPO_ROOT -MaxDepth $effectiveDepth
    }
    foreach ($nestedPath in $nestedRepos) {
        $relPath = $nestedPath.Substring($paths.REPO_ROOT.Length).TrimStart('\', '/')
        $nestedReposResult += [PSCustomObject]@{ path = $relPath }
    }
}

# Output results
if ($Json) {
    $result = [PSCustomObject]@{ 
        FEATURE_SPEC = $paths.FEATURE_SPEC
        IMPL_PLAN = $paths.IMPL_PLAN
        SPECS_DIR = $paths.FEATURE_DIR
        BRANCH = $paths.CURRENT_BRANCH
        HAS_GIT = $paths.HAS_GIT
        NESTED_REPOS = $nestedReposResult
    }
    $result | ConvertTo-Json -Compress
} else {
    Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
    Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
    Write-Output "SPECS_DIR: $($paths.FEATURE_DIR)"
    Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
    Write-Output "HAS_GIT: $($paths.HAS_GIT)"
    if ($nestedReposResult.Count -gt 0) {
        Write-Output "NESTED_REPOS:"
        foreach ($nr in $nestedReposResult) {
            Write-Output "  $($nr.path)"
        }
    }
}
