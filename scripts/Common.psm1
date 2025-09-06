<#
.SYNOPSIS
    Common functions for Spec-Kit PowerShell scripts
.DESCRIPTION
    This module contains shared functions used across Spec-Kit PowerShell scripts.
#>

# Get repository root directory
function Get-RepoRoot {
    [CmdletBinding()]
    [OutputType([string])]
    param()
    
    try {
        return (git rev-parse --show-toplevel 2>$null).Trim()
    } catch {
        Write-Error "Not a git repository or git is not installed"
        exit 1
    }
}

# Get current git branch
function Get-CurrentBranch {
    [CmdletBinding()]
    [OutputType([string])]
    param()
    
    try {
        return (git rev-parse --abbrev-ref HEAD).Trim()
    } catch {
        Write-Error "Failed to get current branch"
        exit 1
    }
}

# Check if current branch is a feature branch
function Test-FeatureBranch {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Branch
    )
    
    if ($Branch -match '^\d{3}-') {
        return $true
    }
    
    Write-Error "Not on a feature branch. Current branch: $Branch`nFeature branches should be named like: 001-feature-name"
    return $false
}

# Get feature directory path
function Get-FeatureDir {
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory=$true)]
        [string]$RepoRoot,
        [Parameter(Mandatory=$true)]
        [string]$Branch
    )
    
    return Join-Path $RepoRoot "specs" $Branch
}

# Get all standard paths for a feature
function Get-FeaturePaths {
    [CmdletBinding()]
    param()
    
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $currentBranch
    
    return [PSCustomObject]@{
        RepoRoot = $repoRoot
        CurrentBranch = $currentBranch
        FeatureDir = $featureDir
        FeatureSpec = Join-Path $featureDir "spec.md"
        ImplPlan = Join-Path $featureDir "plan.md"
        Tasks = Join-Path $featureDir "tasks.md"
        Research = Join-Path $featureDir "research.md"
        DataModel = Join-Path $featureDir "data-model.md"
        QuickStart = Join-Path $featureDir "quickstart.md"
        ContractsDir = Join-Path $featureDir "contracts"
    }
}

# Check if a file exists and report
function Test-FileExists {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path,
        [string]$Description = "File"
    )
    
    if (Test-Path -Path $Path -PathType Leaf) {
        Write-Host "$($PSStyle.Foreground.Green)✓$($PSStyle.Reset) $Description found: $Path"
        return $true
    } else {
        Write-Host "$($PSStyle.Foreground.Red)✗$($PSStyle.Reset) $Description not found: $Path"
        return $false
    }
}

# Check if a directory exists and has files
function Test-DirectoryHasFiles {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path,
        [string]$Description = "Directory"
    )
    
    if (-not (Test-Path -Path $Path -PathType Container)) {
        Write-Host "$($PSStyle.Foreground.Yellow)⚠$($PSStyle.Reset) $Description does not exist: $Path"
        return $false
    }
    
    $hasFiles = (Get-ChildItem -Path $Path -File -Recurse -ErrorAction SilentlyContinue).Count -gt 0
    
    if ($hasFiles) {
        Write-Host "$($PSStyle.Foreground.Green)✓$($PSStyle.Reset) $Description found with files: $Path"
    } else {
        Write-Host "$($PSStyle.Foreground.Yellow)⚠$($PSStyle.Reset) $Description is empty: $Path"
    }
    
    return $hasFiles
}

# Export module members
export-modulemember -function * -alias *
