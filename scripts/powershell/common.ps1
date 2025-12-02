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
    return (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
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
    
    # For non-git repos, try to find the latest feature directory
    $repoRoot = Get-RepoRoot
    $specsDir = Join-Path $repoRoot "specs"
    
    if (Test-Path $specsDir) {
        $latestFeature = ""
        $highest = 0
        
        Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
            # Support both formats: 001-name or feature/001-name
            if ($_.Name -match '^(([a-z]+/)?(\d{3,}))-') {
                $num = [int]$matches[3]
                if ($num -gt $highest) {
                    $highest = $num
                    $latestFeature = $_.Name
                }
            }
        }
        
        if ($latestFeature) {
            return $latestFeature
        }
    }
    
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
    
    # Support both simple format (001-name) and prefixed format (feature/001-name)
    if ($Branch -notmatch '^([a-z]+/)?[0-9]{3,}-') {
        Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"
        Write-Output "Feature branches should be named like:"
        Write-Output "  - 001-feature-name"
        Write-Output "  - feature/001-feature-name"
        Write-Output "  - bugfix/042-fix-name"
        return $false
    }
    return $true
}

function Get-FeatureDir {
    param([string]$RepoRoot, [string]$Branch)
    Join-Path $RepoRoot "specs/$Branch"
}

# Find feature directory by numeric prefix instead of exact branch match
# This allows multiple branches to work on the same spec (e.g., 004-fix-bug, 004-add-feature)
# Also handles branch names with prefixes like feature/004-name or bugfix/042-fix
function Find-FeatureDirByPrefix {
    param(
        [string]$RepoRoot,
        [string]$BranchName
    )
    
    $specsDir = Join-Path $RepoRoot "specs"
    
    # Extract numeric prefix from branch (e.g., "004" from "004-whatever" or "feature/004-whatever")
    # Pattern: optional prefix (feature/, bugfix/, etc.) followed by at least 3 digits
    if ($BranchName -notmatch '^(([a-z]+/)?(\d{3,}))-') {
        # If branch doesn't have numeric prefix, fall back to exact match
        return (Join-Path $specsDir $BranchName)
    }
    
    $number = $matches[3]  # Just the numeric part
    
    # Search for directories in specs/ that contain this number
    # Could be in format: 004-name or feature/004-name or bugfix/004-name
    $matchedDirs = @()
    
    if (Test-Path $specsDir) {
        Get-ChildItem -Path $specsDir -Directory | Where-Object {
            # Check if directory name contains our number and matches the pattern
            $_.Name -match "^(([a-z]+/)?$number)-"
        } | ForEach-Object {
            $matchedDirs += $_.Name
        }
    }
    
    # Handle results
    if ($matchedDirs.Count -eq 0) {
        # No match found - return the branch name path (will fail later with clear error)
        return (Join-Path $specsDir $BranchName)
    } elseif ($matchedDirs.Count -eq 1) {
        # Exactly one match - perfect!
        return (Join-Path $specsDir $matchedDirs[0])
    } else {
        # Multiple matches - this shouldn't happen with proper naming convention
        Write-Warning "ERROR: Multiple spec directories found with number '$number': $($matchedDirs -join ', ')"
        Write-Warning "Please ensure only one spec directory exists per numeric prefix."
        return (Join-Path $specsDir $BranchName)  # Return something to avoid breaking the script
    }
}

function Get-FeaturePathsEnv {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit
    
    # Use prefix-based lookup to support multiple branches per spec and branch prefixes
    $featureDir = Find-FeatureDirByPrefix -RepoRoot $repoRoot -BranchName $currentBranch
    
    [PSCustomObject]@{
        REPO_ROOT     = $repoRoot
        CURRENT_BRANCH = $currentBranch
        HAS_GIT       = $hasGit
        FEATURE_DIR   = $featureDir
        FEATURE_SPEC  = Join-Path $featureDir 'spec.md'
        IMPL_PLAN     = Join-Path $featureDir 'plan.md'
        TASKS         = Join-Path $featureDir 'tasks.md'
        RESEARCH      = Join-Path $featureDir 'research.md'
        DATA_MODEL    = Join-Path $featureDir 'data-model.md'
        QUICKSTART    = Join-Path $featureDir 'quickstart.md'
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

