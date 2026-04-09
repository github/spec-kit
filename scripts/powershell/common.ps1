#!/usr/bin/env pwsh
# Common PowerShell functions analogous to common.sh

# Find repository root by searching upward for .specify directory
# This is the primary marker for spec-kit projects
function Find-SpecifyRoot {
    param([string]$StartDir = (Get-Location).Path)

    # Normalize to absolute path to prevent issues with relative paths
    # Use -LiteralPath to handle paths with wildcard characters ([, ], *, ?)
    $resolved = Resolve-Path -LiteralPath $StartDir -ErrorAction SilentlyContinue
    $current = if ($resolved) { $resolved.Path } else { $null }
    if (-not $current) { return $null }

    while ($true) {
        if (Test-Path -LiteralPath (Join-Path $current ".specify") -PathType Container) {
            return $current
        }
        $parent = Split-Path $current -Parent
        if ([string]::IsNullOrEmpty($parent) -or $parent -eq $current) {
            return $null
        }
        $current = $parent
    }
}

# Get repository root, prioritizing .specify directory over git
# This prevents using a parent git repo when spec-kit is initialized in a subdirectory
function Get-RepoRoot {
    # First, look for .specify directory (spec-kit's own marker)
    $specifyRoot = Find-SpecifyRoot
    if ($specifyRoot) {
        return $specifyRoot
    }

    # Fallback to git if no .specify found
    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }

    # Final fallback to script location for non-git repos
    # Use -LiteralPath to handle paths with wildcard characters
    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "../../..")).Path
}

function Get-CurrentBranch {
    # First check if SPECIFY_FEATURE environment variable is set
    if ($env:SPECIFY_FEATURE) {
        return $env:SPECIFY_FEATURE
    }

    # Then check git if available at the spec-kit root (not parent)
    $repoRoot = Get-RepoRoot
    if (Test-HasGit) {
        try {
            $result = git -C $repoRoot rev-parse --abbrev-ref HEAD 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $result
            }
        } catch {
            # Git command failed
        }
    }

    # For non-git repos, try to find the latest feature directory
    $specsDir = Join-Path $repoRoot "specs"
    
    if (Test-Path $specsDir) {
        $latestFeature = ""
        $highest = 0
        $latestTimestamp = ""

        Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{8}-\d{6})-') {
                # Timestamp-based branch: compare lexicographically
                $ts = $matches[1]
                if ($ts -gt $latestTimestamp) {
                    $latestTimestamp = $ts
                    $latestFeature = $_.Name
                }
            } elseif ($_.Name -match '^(\d{3,})-') {
                $num = [long]$matches[1]
                if ($num -gt $highest) {
                    $highest = $num
                    # Only update if no timestamp branch found yet
                    if (-not $latestTimestamp) {
                        $latestFeature = $_.Name
                    }
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

# Check if we have git available at the spec-kit root level
# Returns true only if git is installed and the repo root is inside a git work tree
# Handles both regular repos (.git directory) and worktrees/submodules (.git file)
function Test-HasGit {
    # First check if git command is available (before calling Get-RepoRoot which may use git)
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        return $false
    }
    $repoRoot = Get-RepoRoot
    # Check if .git exists (directory or file for worktrees/submodules)
    # Use -LiteralPath to handle paths with wildcard characters
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot ".git"))) {
        return $false
    }
    # Verify it's actually a valid git work tree
    try {
        $null = git -C $repoRoot rev-parse --is-inside-work-tree 2>$null
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
    
    # Accept sequential prefix (3+ digits) but exclude malformed timestamps
    # Malformed: 7-or-8 digit date + 6-digit time with no trailing slug (e.g. "2026031-143022" or "20260319-143022")
    $hasMalformedTimestamp = ($Branch -match '^[0-9]{7}-[0-9]{6}-') -or ($Branch -match '^(?:\d{7}|\d{8})-\d{6}$')
    $isSequential = ($Branch -match '^[0-9]{3,}-') -and (-not $hasMalformedTimestamp)
    if (-not $isSequential -and $Branch -notmatch '^\d{8}-\d{6}-') {
        Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"
        Write-Output "Feature branches should be named like: 001-feature-name, 1234-feature-name, or 20260319-143022-feature-name"
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
    $hasGit = Test-HasGit

    # Resolve feature directory.  Priority:
    #   1. SPECIFY_FEATURE_DIRECTORY env var (explicit override)
    #   2. .specify/feature.json "feature_directory" key (persisted by /speckit.specify)
    #   3. Exact branch-to-directory mapping via Get-FeatureDir (legacy fallback)
    $featureJson = Join-Path $repoRoot '.specify/feature.json'
    if ($env:SPECIFY_FEATURE_DIRECTORY) {
        $featureDir = $env:SPECIFY_FEATURE_DIRECTORY
        # Normalize relative paths to absolute under repo root
        if (-not [System.IO.Path]::IsPathRooted($featureDir)) {
            $featureDir = Join-Path $repoRoot $featureDir
        }
    } elseif (Test-Path $featureJson) {
        try {
            $featureConfig = Get-Content $featureJson -Raw | ConvertFrom-Json
            if ($featureConfig.feature_directory) {
                $featureDir = $featureConfig.feature_directory
                # Normalize relative paths to absolute under repo root
                if (-not [System.IO.Path]::IsPathRooted($featureDir)) {
                    $featureDir = Join-Path $repoRoot $featureDir
                }
            } else {
                $featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $currentBranch
            }
        } catch {
            $featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $currentBranch
        }
    } else {
        $featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $currentBranch
    }
    
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

# Discover nested independent git repositories under RepoRoot.
# Searches up to 2 directory levels deep for subdirectories containing .git
# (directory or file, covering worktrees/submodules). Excludes the root repo
# itself and common non-project directories.
# Returns an array of absolute paths. Scan depth is configurable (default 2).
# If ExplicitPaths are provided, validates and returns those directly (no scanning).
function Find-NestedGitRepos {
    param(
        [string]$RepoRoot = (Get-RepoRoot),
        [int]$MaxDepth = 2,
        [string[]]$ExplicitPaths = @()
    )

    # If explicit paths are provided, validate and return them directly
    if ($ExplicitPaths.Count -gt 0) {
        $found = @()
        foreach ($relPath in $ExplicitPaths) {
            $absPath = Join-Path $RepoRoot $relPath
            $gitMarker = Join-Path $absPath '.git'
            if (Test-Path -LiteralPath $gitMarker) {
                try {
                    $null = git -C $absPath rev-parse --is-inside-work-tree 2>$null
                    if ($LASTEXITCODE -eq 0) {
                        $found += $absPath
                    }
                } catch { }
            }
        }
        return $found
    }

    # Fallback: scan using .gitignore-based filtering
    function ScanDir {
        param([string]$Dir, [int]$CurrentDepth)
        $found = @()
        $children = Get-ChildItem -Path $Dir -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ne '.git' }

        foreach ($child in $children) {
            $gitMarker = Join-Path $child.FullName '.git'
            if (Test-Path -LiteralPath $gitMarker) {
                # Directory has its own .git — it's a nested repo (even if gitignored in parent)
                try {
                    $null = git -C $child.FullName rev-parse --is-inside-work-tree 2>$null
                    if ($LASTEXITCODE -eq 0) {
                        $found += $child.FullName
                    }
                } catch { }
            } elseif ($CurrentDepth -lt $MaxDepth) {
                # Skip gitignored directories (they won't contain nested repos)
                $null = git -C $RepoRoot check-ignore -q $child.FullName 2>$null
                if ($LASTEXITCODE -eq 0) { continue }
                $found += ScanDir -Dir $child.FullName -CurrentDepth ($CurrentDepth + 1)
            }
        }
        return $found
    }

    return ScanDir -Dir $RepoRoot -CurrentDepth 1
}

# Resolve a template name to a file path using the priority stack:
#   1. .specify/templates/overrides/
#   2. .specify/presets/<preset-id>/templates/ (sorted by priority from .registry)
#   3. .specify/extensions/<ext-id>/templates/
#   4. .specify/templates/ (core)
function Resolve-Template {
    param(
        [Parameter(Mandatory=$true)][string]$TemplateName,
        [Parameter(Mandatory=$true)][string]$RepoRoot
    )

    $base = Join-Path $RepoRoot '.specify/templates'

    # Priority 1: Project overrides
    $override = Join-Path $base "overrides/$TemplateName.md"
    if (Test-Path $override) { return $override }

    # Priority 2: Installed presets (sorted by priority from .registry)
    $presetsDir = Join-Path $RepoRoot '.specify/presets'
    if (Test-Path $presetsDir) {
        $registryFile = Join-Path $presetsDir '.registry'
        $sortedPresets = @()
        if (Test-Path $registryFile) {
            try {
                $registryData = Get-Content $registryFile -Raw | ConvertFrom-Json
                $presets = $registryData.presets
                if ($presets) {
                    $sortedPresets = $presets.PSObject.Properties |
                        Sort-Object { if ($null -ne $_.Value.priority) { $_.Value.priority } else { 10 } } |
                        ForEach-Object { $_.Name }
                }
            } catch {
                # Fallback: alphabetical directory order
                $sortedPresets = @()
            }
        }

        if ($sortedPresets.Count -gt 0) {
            foreach ($presetId in $sortedPresets) {
                $candidate = Join-Path $presetsDir "$presetId/templates/$TemplateName.md"
                if (Test-Path $candidate) { return $candidate }
            }
        } else {
            # Fallback: alphabetical directory order
            foreach ($preset in Get-ChildItem -Path $presetsDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike '.*' }) {
                $candidate = Join-Path $preset.FullName "templates/$TemplateName.md"
                if (Test-Path $candidate) { return $candidate }
            }
        }
    }

    # Priority 3: Extension-provided templates
    $extDir = Join-Path $RepoRoot '.specify/extensions'
    if (Test-Path $extDir) {
        foreach ($ext in Get-ChildItem -Path $extDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike '.*' } | Sort-Object Name) {
            $candidate = Join-Path $ext.FullName "templates/$TemplateName.md"
            if (Test-Path $candidate) { return $candidate }
        }
    }

    # Priority 4: Core templates
    $core = Join-Path $base "$TemplateName.md"
    if (Test-Path $core) { return $core }

    return $null
}

