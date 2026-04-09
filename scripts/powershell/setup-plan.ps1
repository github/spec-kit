#!/usr/bin/env pwsh
# Setup implementation plan for a feature

[CmdletBinding()]
param(
    [switch]$Json,
    [ValidateRange(1, [int]::MaxValue)]
    [int]$ScanDepth,
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
    $initOptions = Join-Path $paths.REPO_ROOT '.specify' 'init-options.json'
    $explicitPaths = @()
    $configDepth = $null

    # Read explicit nested_repos and nested_repo_scan_depth from init-options.json if available
    if (Test-Path -LiteralPath $initOptions) {
        try {
            $opts = Get-Content $initOptions -Raw | ConvertFrom-Json
            if ($opts.nested_repos -and $opts.nested_repos.Count -gt 0) {
                $explicitPaths = @($opts.nested_repos)
            }
            if ($null -ne $opts.nested_repo_scan_depth) {
                $parsedConfigDepth = [int]$opts.nested_repo_scan_depth
                if ($parsedConfigDepth -ge 1) {
                    $configDepth = $parsedConfigDepth
                } else {
                    Write-Warning "nested_repo_scan_depth in init-options.json must be >= 1, got $parsedConfigDepth — using default"
                }
            }
        } catch { }
    }

    # Priority: CLI -ScanDepth > init-options nested_repo_scan_depth > default 2
    $effectiveDepth = if ($PSBoundParameters.ContainsKey('ScanDepth')) { $ScanDepth } elseif ($configDepth) { $configDepth } else { 2 }

    if ($explicitPaths.Count -gt 0) {
        try {
            $nestedRepos = Find-NestedGitRepos -RepoRoot $paths.REPO_ROOT -MaxDepth $effectiveDepth -ExplicitPaths $explicitPaths
        } catch {
            Write-Warning "Nested repo discovery failed: $_"
            $nestedRepos = @()
        }
    } else {
        try {
            $nestedRepos = Find-NestedGitRepos -RepoRoot $paths.REPO_ROOT -MaxDepth $effectiveDepth
        } catch {
            Write-Warning "Nested repo discovery failed: $_"
            $nestedRepos = @()
        }
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
