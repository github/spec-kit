#!/usr/bin/env pwsh
# Common PowerShell functions analogous to common.sh (moved to powershell/)

function Get-RepoRoot {
    git rev-parse --show-toplevel
}

function Get-CurrentBranch {
    git rev-parse --abbrev-ref HEAD
}

function Test-FeatureBranch {
    param([string]$Branch)
    if ($Branch -notmatch '^[a-zA-Z0-9_-]+/[a-z]+-[0-9]+\.[a-z0-9.-]+') {
        Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"
        Write-Output "Feature branches should be named like: username/jira-123.feature-name"
        return $false
    }
    return $true
}

function Get-FeatureId {
    param([string]$Branch)
    # Extract jira-123.feature-name part from username/jira-123.feature-name
    return ($Branch -split '/')[-1]
}

function Get-FeatureDir {
    param([string]$RepoRoot, [string]$Branch)
    $featureId = Get-FeatureId -Branch $Branch
    Join-Path $RepoRoot "specs/$featureId"
}

# Extract capability ID from branch name if present
# Example: username/jira-123.feature-cap-001 → cap-001
function Get-CapabilityIdFromBranch {
    param([string]$Branch)
    if ($Branch -match '-cap-\d{3}$') {
        if ($Branch -match '(cap-\d{3})$') {
            return $Matches[1]
        }
    }
    return ""
}

# Extract parent feature ID from capability branch
# Example: username/jira-123.feature-name-cap-001 → jira-123.feature-name
function Get-ParentFeatureId {
    param([string]$Branch)
    $featureId = Get-FeatureId -Branch $Branch
    # Remove -cap-XXX suffix if present
    return $featureId -replace '-cap-\d{3}$', ''
}

function Get-FeaturePathsEnv {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $capabilityId = Get-CapabilityIdFromBranch -Branch $currentBranch
    $specsDir = Join-Path $repoRoot "specs"

    # Capability mode: branch pattern username/jira-123.feature-name-cap-001
    if ($capabilityId) {
        $parentFeatureId = Get-ParentFeatureId -Branch $currentBranch
        $parentFeatureDir = Join-Path $specsDir $parentFeatureId

        # Find capability directory matching pattern cap-XXX-*/
        $capabilityDir = ""
        if (Test-Path $parentFeatureDir) {
            $matchingDirs = Get-ChildItem -Path $parentFeatureDir -Directory -Filter "$capabilityId-*" -ErrorAction SilentlyContinue
            if ($matchingDirs) {
                $capabilityDir = $matchingDirs[0].FullName
            }
        }

        # Fallback to generic path if directory not found yet
        if (-not $capabilityDir) {
            $capabilityDir = Join-Path $parentFeatureDir $capabilityId
        }

        return [PSCustomObject]@{
            REPO_ROOT = $repoRoot
            CURRENT_BRANCH = $currentBranch
            CAPABILITY_ID = $capabilityId
            PARENT_FEATURE_ID = $parentFeatureId
            PARENT_FEATURE_DIR = $parentFeatureDir
            FEATURE_DIR = $capabilityDir
            FEATURE_SPEC = Join-Path $capabilityDir 'spec.md'
            IMPL_PLAN = Join-Path $capabilityDir 'plan.md'
            TASKS = Join-Path $capabilityDir 'tasks.md'
            RESEARCH = Join-Path $capabilityDir 'research.md'
            DATA_MODEL = Join-Path $capabilityDir 'data-model.md'
            QUICKSTART = Join-Path $capabilityDir 'quickstart.md'
            CONTRACTS_DIR = Join-Path $capabilityDir 'contracts'
        }
    } else {
        # Parent feature mode: standard branch pattern
        $featureId = Get-FeatureId -Branch $currentBranch
        $featureDir = Join-Path $specsDir $featureId

        return [PSCustomObject]@{
            REPO_ROOT = $repoRoot
            CURRENT_BRANCH = $currentBranch
            CAPABILITY_ID = ""
            PARENT_FEATURE_ID = ""
            PARENT_FEATURE_DIR = ""
            FEATURE_DIR = $featureDir
            FEATURE_SPEC = Join-Path $featureDir 'spec.md'
            IMPL_PLAN = Join-Path $featureDir 'plan.md'
            TASKS = Join-Path $featureDir 'tasks.md'
            RESEARCH = Join-Path $featureDir 'research.md'
            DATA_MODEL = Join-Path $featureDir 'data-model.md'
            QUICKSTART = Join-Path $featureDir 'quickstart.md'
            CONTRACTS_DIR = Join-Path $featureDir 'contracts'
        }
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
