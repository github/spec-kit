#!/usr/bin/env pwsh
# Common PowerShell functions analogous to common.sh

function Get-RepoRoot {
    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }
    
    # Fall back to script location for non-git repos
    $cand = (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
    if ([IO.Path]::GetFileName($cand) -eq '.specs') {
        return ([IO.Directory]::GetParent($cand).FullName)
    }
    return $cand
}

function Get-CurrentBranch {
    # First check if SPECIFY_FEATURE environment variable is set
    if ($env:SPECIFY_FEATURE) {
        return $env:SPECIFY_FEATURE
    }
    
    # Then check git if available
    try {
        $result = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }
    
    # For non-git repos, try to find the latest feature directory (search nested)
    $repoRoot = Get-RepoRoot
    $layout = & (Join-Path $PSScriptRoot 'read-layout.ps1')
    $roots = @((Join-Path $repoRoot '.specs/.specify/specs'), (Join-Path $repoRoot 'specs'))
    foreach ($r in $layout.SPEC_ROOTS) { $roots += (Join-Path $repoRoot $r) }
    $latestFeature = ''
    $highest = 0
    foreach ($base in $roots) {
        if (-not (Test-Path $base)) { continue }
        try {
            Get-ChildItem -Path $base -Recurse -Directory -ErrorAction SilentlyContinue | ForEach-Object {
                if ($_.Name -match '^(\d{3})-') {
                    $num = [int]$matches[1]
                    if ($num -gt $highest) { $highest = $num; $latestFeature = $_.Name }
                }
            }
        } catch {}
    }
    if ($latestFeature) { return $latestFeature }
    
    # Final fallback
    return "main"
}

function Test-HasGit {
    try {
        git rev-parse --show-toplevel 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Test-FeatureBranch {
    param(
        [string]$Branch,
        [bool]$HasGit = $true
    )
    
    # For non-git repos, we can't enforce branch naming but still provide output
    if (-not $HasGit) {
        Write-Warning "[specify] Warning: Git repository not detected; skipped branch validation"
        return $true
    }
    
    if ($Branch -notmatch '^[0-9]{3}-') {
        Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"
        Write-Output "Feature branches should be named like: 001-feature-name"
        return $false
    }
    return $true
}

function Get-FeatureDir {
    param([string]$RepoRoot, [string]$Branch)
    $layout = & (Join-Path $PSScriptRoot 'read-layout.ps1')
    $roots = @()
    if ($layout.SPEC_ROOTS) { $roots = $layout.SPEC_ROOTS } else { $roots = @('.specs/.specify/specs','specs') }
    # choose first existing root or first configured
    $chosenRoot = $null
    foreach ($r in $roots) {
        $cand = Join-Path $RepoRoot $r
        if (Test-Path $cand) { $chosenRoot = $cand; break }
    }
    if (-not $chosenRoot) { $chosenRoot = Join-Path $RepoRoot $roots[0] }

    # honor existing folder if present
    try {
        $match = Get-ChildItem -Path $chosenRoot -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq $Branch } | Select-Object -First 1
        if ($match) { return $match.FullName }
    } catch {}

    $epic = $env:SPECIFY_EPIC; if (-not $epic) { $epic = 'uncategorized' }
    $product = $env:SPECIFY_PRODUCT; if (-not $product) { $product = 'default' }
    $slug = { param($s) ($s.ToLower() -replace '[^a-z0-9]', '-') -replace '-{2,}', '-' -replace '^-','' -replace '-$','' }
    $epic = & $slug $epic; $product = & $slug $product

    switch ($layout.FOLDER_STRATEGY) {
        'product' { return (Join-Path $chosenRoot ("products/$product/epics/$epic/$Branch")) }
        'epic'    { return (Join-Path $chosenRoot ("epics/$epic/$Branch")) }
        default   { return (Join-Path $chosenRoot $Branch) }
    }
}

function Get-FeaturePathsEnv {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit
    $specsRoot = Join-Path $repoRoot '.specs'
    if (-not (Test-Path $specsRoot)) {
        New-Item -ItemType Directory -Path $specsRoot | Out-Null
    }
    $specifyRoot = Join-Path $specsRoot '.specify'
    if (-not (Test-Path $specifyRoot)) {
        New-Item -ItemType Directory -Path $specifyRoot | Out-Null
    }
    $layout = & (Join-Path $PSScriptRoot 'read-layout.ps1')
    $featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $currentBranch
    
    [PSCustomObject]@{
        REPO_ROOT     = $repoRoot
        CURRENT_BRANCH = $currentBranch
        HAS_GIT       = $hasGit
        FEATURE_DIR   = $featureDir
        FEATURE_SPEC  = Join-Path $featureDir ($layout.FILES.FPRD)
        IMPL_PLAN     = Join-Path $featureDir ($layout.FILES.DESIGN)
        TASKS         = Join-Path $featureDir ($layout.FILES.TASKS)
        RESEARCH      = Join-Path $featureDir ($layout.FILES.RESEARCH)
        DATA_MODEL    = Join-Path $featureDir 'data-model.md'
        QUICKSTART    = Join-Path $featureDir ($layout.FILES.QUICKSTART)
        CONTRACTS_DIR = Join-Path $featureDir ($layout.FILES.CONTRACTS_DIR)
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
