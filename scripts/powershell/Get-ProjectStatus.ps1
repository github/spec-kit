#!/usr/bin/env pwsh

# Project status discovery script for /speckit.status command
#
# This script discovers project structure and artifact existence.
# It does NOT parse file contents - that's left to the AI agent.
#
# Usage: ./Get-ProjectStatus.ps1 [OPTIONS]
#
# OPTIONS:
#   -Json               Output in JSON format (default: text)
#   -Feature <name>     Focus on specific feature (name, number, or path)
#   -Help               Show help message

[CmdletBinding()]
param(
    [switch]$Json,
    [string]$Feature,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: Get-ProjectStatus.ps1 [OPTIONS]

Discover project structure and artifact existence for /speckit.status.

OPTIONS:
  -Json               Output in JSON format (default: text)
  -Feature <name>     Focus on specific feature (by name, number prefix, or path)
  -Help               Show this help message

EXAMPLES:
  # Get full project status in JSON
  .\Get-ProjectStatus.ps1 -Json

  # Get status for specific feature
  .\Get-ProjectStatus.ps1 -Json -Feature 002-dashboard

  # Get status by feature number
  .\Get-ProjectStatus.ps1 -Json -Feature 002

"@
    exit 0
}

# Function to find repository root
function Find-RepoRoot {
    param([string]$StartPath)

    $dir = $StartPath
    while ($dir -and $dir -ne [System.IO.Path]::GetPathRoot($dir)) {
        if ((Test-Path (Join-Path $dir ".git")) -or (Test-Path (Join-Path $dir ".specify"))) {
            return $dir
        }
        $dir = Split-Path $dir -Parent
    }
    return $null
}

# Function to get project name
function Get-ProjectName {
    param([string]$RepoRoot)

    # Try package.json first
    $packageJson = Join-Path $RepoRoot "package.json"
    if (Test-Path $packageJson) {
        try {
            $pkg = Get-Content $packageJson -Raw | ConvertFrom-Json
            if ($pkg.name) {
                return $pkg.name
            }
        } catch {
            # Ignore parse errors
        }
    }

    # Try pyproject.toml
    $pyproject = Join-Path $RepoRoot "pyproject.toml"
    if (Test-Path $pyproject) {
        $content = Get-Content $pyproject -Raw
        if ($content -match 'name\s*=\s*"([^"]+)"') {
            return $matches[1]
        }
    }

    # Fall back to directory name
    return Split-Path $RepoRoot -Leaf
}

# Function to check if path exists (file or non-empty directory)
function Test-Exists {
    param([string]$Path)

    if (Test-Path $Path -PathType Leaf) {
        return $true
    }
    if ((Test-Path $Path -PathType Container) -and (Get-ChildItem $Path -ErrorAction SilentlyContinue | Select-Object -First 1)) {
        return $true
    }
    return $false
}

# Function to get feature info
function Get-FeatureInfo {
    param(
        [string]$FeatureName,
        [string]$SpecsDir,
        [string]$CurrentBranch,
        [bool]$IsFeatureBranch
    )

    $featureDir = Join-Path $SpecsDir $FeatureName

    $info = [ordered]@{
        name = $FeatureName
        path = $featureDir
        is_current = $false
        has_spec = Test-Exists (Join-Path $featureDir "spec.md")
        has_plan = Test-Exists (Join-Path $featureDir "plan.md")
        has_tasks = Test-Exists (Join-Path $featureDir "tasks.md")
        has_research = Test-Exists (Join-Path $featureDir "research.md")
        has_data_model = Test-Exists (Join-Path $featureDir "data-model.md")
        has_quickstart = Test-Exists (Join-Path $featureDir "quickstart.md")
        has_contracts = Test-Exists (Join-Path $featureDir "contracts")
        has_checklists = Test-Exists (Join-Path $featureDir "checklists")
        checklist_files = @()
    }

    # Check if this is the current feature
    if ($IsFeatureBranch -and $CurrentBranch -match '^(\d{3})-' -and $FeatureName -match '^(\d{3})-') {
        $currentPrefix = $CurrentBranch -replace '^(\d{3})-.*', '$1'
        $featurePrefix = $FeatureName -replace '^(\d{3})-.*', '$1'
        if ($currentPrefix -eq $featurePrefix) {
            $info.is_current = $true
        }
    }

    # Get checklist files if they exist
    $checklistsDir = Join-Path $featureDir "checklists"
    if (Test-Path $checklistsDir -PathType Container) {
        $info.checklist_files = @(Get-ChildItem $checklistsDir -Filter "*.md" -File | Select-Object -ExpandProperty Name | Sort-Object)
    }

    return $info
}

# Resolve repository root
$ScriptDir = $PSScriptRoot

try {
    $gitRoot = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0) {
        $RepoRoot = $gitRoot
        $HasGit = $true
        $CurrentBranch = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -ne 0) { $CurrentBranch = "unknown" }
    } else {
        throw "Not a git repo"
    }
} catch {
    $RepoRoot = Find-RepoRoot $ScriptDir
    if (-not $RepoRoot) {
        Write-Error "Error: Could not determine repository root."
        exit 1
    }
    $HasGit = $false
    $CurrentBranch = ""
}

# Determine specs directory
$SpecsDir = if (Test-Path (Join-Path $RepoRoot ".specify/specs")) {
    Join-Path $RepoRoot ".specify/specs"
} elseif (Test-Path (Join-Path $RepoRoot "specs")) {
    Join-Path $RepoRoot "specs"
} else {
    Join-Path $RepoRoot ".specify/specs"  # Default
}

# Determine memory directory
$MemoryDir = if (Test-Path (Join-Path $RepoRoot ".specify/memory")) {
    Join-Path $RepoRoot ".specify/memory"
} elseif (Test-Path (Join-Path $RepoRoot "memory")) {
    Join-Path $RepoRoot "memory"
} else {
    Join-Path $RepoRoot ".specify/memory"  # Default
}

# Check constitution
$ConstitutionPath = Join-Path $MemoryDir "constitution.md"
$ConstitutionExists = Test-Path $ConstitutionPath -PathType Leaf

# Get project name
$ProjectName = Get-ProjectName $RepoRoot

# Check if on feature branch
$IsFeatureBranch = $CurrentBranch -match '^\d{3}-'

# Collect all features
$Features = @()
if (Test-Path $SpecsDir -PathType Container) {
    $Features = @(Get-ChildItem $SpecsDir -Directory | Where-Object { $_.Name -match '^\d{3}-' } | Sort-Object Name | Select-Object -ExpandProperty Name)
}

# Resolve target feature if specified
$ResolvedTarget = $null
if ($Feature) {
    # Try exact match first
    if (Test-Path (Join-Path $SpecsDir $Feature) -PathType Container) {
        $ResolvedTarget = $Feature
    }
    # Try as path
    elseif (Test-Path $Feature -PathType Container) {
        $ResolvedTarget = Split-Path $Feature -Leaf
    }
    # Try as number prefix
    elseif ($Feature -match '^\d+$') {
        $prefix = "{0:D3}" -f [int]$Feature
        $match = $Features | Where-Object { $_ -match "^$prefix-" } | Select-Object -First 1
        if ($match) { $ResolvedTarget = $match }
    }
    # Try partial match
    else {
        $match = $Features | Where-Object { $_ -like "*$Feature*" } | Select-Object -First 1
        if ($match) { $ResolvedTarget = $match }
    }

    if (-not $ResolvedTarget) {
        Write-Error "Error: Feature not found: $Feature"
        exit 1
    }
}

# Build output
if ($Json) {
    $featuresInfo = @()
    foreach ($f in $Features) {
        $featuresInfo += Get-FeatureInfo -FeatureName $f -SpecsDir $SpecsDir -CurrentBranch $CurrentBranch -IsFeatureBranch $IsFeatureBranch
    }

    $output = [ordered]@{
        project = $ProjectName
        repo_root = $RepoRoot
        specs_dir = $SpecsDir
        has_git = $HasGit
        branch = $CurrentBranch
        is_feature_branch = $IsFeatureBranch
        constitution = [ordered]@{
            exists = $ConstitutionExists
            path = $ConstitutionPath
        }
        feature_count = $Features.Count
        target_feature = $ResolvedTarget
        features = $featuresInfo
    }

    $output | ConvertTo-Json -Depth 10 -Compress
} else {
    Write-Output "Project Status Discovery"
    Write-Output "========================"
    Write-Output ""
    Write-Output "Project: $ProjectName"
    Write-Output "Root: $RepoRoot"
    Write-Output "Specs: $SpecsDir"
    Write-Output "Git: $HasGit"
    Write-Output "Branch: $CurrentBranch"
    Write-Output "Feature Branch: $IsFeatureBranch"
    Write-Output "Constitution: $ConstitutionExists ($ConstitutionPath)"
    Write-Output ""

    if ($ResolvedTarget) {
        Write-Output "Target Feature: $ResolvedTarget"
        Write-Output ""
    }

    Write-Output "Features ($($Features.Count)):"
    Write-Output ""

    if ($Features.Count -eq 0) {
        Write-Output "  (none)"
    } else {
        foreach ($f in $Features) {
            $info = Get-FeatureInfo -FeatureName $f -SpecsDir $SpecsDir -CurrentBranch $CurrentBranch -IsFeatureBranch $IsFeatureBranch
            Write-Output "  Name: $($info.name)"
            Write-Output "  Path: $($info.path)"
            Write-Output "  Current: $($info.is_current)"
            Write-Output "  Artifacts:"
            Write-Output "    spec.md: $($info.has_spec)"
            Write-Output "    plan.md: $($info.has_plan)"
            Write-Output "    tasks.md: $($info.has_tasks)"
            Write-Output "    research.md: $($info.has_research)"
            Write-Output "    data-model.md: $($info.has_data_model)"
            Write-Output "    quickstart.md: $($info.has_quickstart)"
            Write-Output "    contracts/: $($info.has_contracts)"
            Write-Output "    checklists/: $($info.has_checklists)"
            if ($info.checklist_files.Count -gt 0) {
                Write-Output "    checklist_files: $($info.checklist_files -join ', ')"
            }
            Write-Output ""
        }
    }
}
