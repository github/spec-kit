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

# Strip a single optional path segment (e.g. gitflow "feat/004-name" -> "004-name").
# Only when the full name is exactly two slash-free segments; otherwise returns the raw name.
function Get-SpecKitEffectiveBranchName {
    param([string]$Branch)
    if ($Branch -match '^([^/]+)/([^/]+)$') {
        return $Matches[2]
    }
    return $Branch
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

    $raw = $Branch
    $Branch = Get-SpecKitEffectiveBranchName $raw
    
    # Accept sequential prefix (3+ digits) but exclude malformed timestamps
    # Malformed: 7-or-8 digit date + 6-digit time with no trailing slug (e.g. "2026031-143022" or "20260319-143022")
    $hasMalformedTimestamp = ($Branch -match '^[0-9]{7}-[0-9]{6}-') -or ($Branch -match '^(?:\d{7}|\d{8})-\d{6}$')
    $isSequential = ($Branch -match '^[0-9]{3,}-') -and (-not $hasMalformedTimestamp)
    if (-not $isSequential -and $Branch -notmatch '^\d{8}-\d{6}-') {
        [Console]::Error.WriteLine("ERROR: Not on a feature branch. Current branch: $raw")
        [Console]::Error.WriteLine("Feature branches should be named like: 001-feature-name, 1234-feature-name, or 20260319-143022-feature-name")
        return $false
    }
    return $true
}

# True when .specify/feature.json pins an existing feature directory that matches the
# active FEATURE_DIR from Get-FeaturePathsEnv (so /speckit.plan can skip git branch pattern checks).
function Test-FeatureJsonMatchesFeatureDir {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$ActiveFeatureDir
    )

    $featureJson = Join-Path (Join-Path $RepoRoot '.specify') 'feature.json'
    if (-not (Test-Path -LiteralPath $featureJson -PathType Leaf)) {
        return $false
    }

    try {
        $raw = Get-Content -LiteralPath $featureJson -Raw
        $cfg = $raw | ConvertFrom-Json
    } catch {
        return $false
    }

    $fd = $cfg.feature_directory
    if ([string]::IsNullOrWhiteSpace([string]$fd)) {
        return $false
    }

    if (-not [System.IO.Path]::IsPathRooted($fd)) {
        $fd = Join-Path $RepoRoot $fd
    }

    if (-not (Test-Path -LiteralPath $fd -PathType Container)) {
        return $false
    }

    # Resolve both paths to canonical absolute form. Prefer Resolve-Path (follows
    # symlinks and is the canonical PS way); fall back to [Path]::GetFullPath when
    # Resolve-Path can't produce a value. Mirrors the pattern used by Find-SpecifyRoot.
    $resolvedJson = Resolve-Path -LiteralPath $fd -ErrorAction SilentlyContinue
    if ($resolvedJson) {
        $normJson = $resolvedJson.Path
    } else {
        $normJson = [System.IO.Path]::GetFullPath($fd)
    }

    $resolvedActive = Resolve-Path -LiteralPath $ActiveFeatureDir -ErrorAction SilentlyContinue
    if ($resolvedActive) {
        $normActive = $resolvedActive.Path
    } else {
        $normActive = [System.IO.Path]::GetFullPath($ActiveFeatureDir)
    }

    # Use case-insensitive compare only on Windows; POSIX filesystems are case-sensitive.
    # PowerShell 5.1 is Windows-only and does not define $IsWindows, so treat its
    # absence as "we're on Windows".
    if ($null -ne $IsWindows) {
        $onWindows = $IsWindows
    } else {
        $onWindows = $true
    }

    if ($onWindows) {
        $comparison = [System.StringComparison]::OrdinalIgnoreCase
    } else {
        $comparison = [System.StringComparison]::Ordinal
    }

    return [string]::Equals($normJson, $normActive, $comparison)
}

# Resolve specs/<feature-dir> by numeric/timestamp prefix (mirrors scripts/bash/common.sh find_feature_dir_by_prefix).
function Find-FeatureDirByPrefix {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$Branch
    )
    $specsDir = Join-Path $RepoRoot 'specs'
    $branchName = Get-SpecKitEffectiveBranchName $Branch

    $prefix = $null
    if ($branchName -match '^(\d{8}-\d{6})-') {
        $prefix = $Matches[1]
    } elseif ($branchName -match '^(\d{3,})-') {
        $prefix = $Matches[1]
    } else {
        return (Join-Path $specsDir $branchName)
    }

    $dirMatches = @()
    if (Test-Path -LiteralPath $specsDir -PathType Container) {
        $dirMatches = @(Get-ChildItem -LiteralPath $specsDir -Filter "$prefix-*" -Directory -ErrorAction SilentlyContinue)
    }

    if ($dirMatches.Count -eq 0) {
        return (Join-Path $specsDir $branchName)
    }
    if ($dirMatches.Count -eq 1) {
        return $dirMatches[0].FullName
    }
    $names = ($dirMatches | ForEach-Object { $_.Name }) -join ' '
    [Console]::Error.WriteLine("ERROR: Multiple spec directories found with prefix '$prefix': $names")
    [Console]::Error.WriteLine('Please ensure only one spec directory exists per prefix.')
    return $null
}

# Branch-based prefix resolution; mirrors bash get_feature_paths failure (stderr + exit 1).
function Get-FeatureDirFromBranchPrefixOrExit {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$CurrentBranch
    )
    $resolved = Find-FeatureDirByPrefix -RepoRoot $RepoRoot -Branch $CurrentBranch
    if ($null -eq $resolved) {
        [Console]::Error.WriteLine('ERROR: Failed to resolve feature directory')
        exit 1
    }
    return $resolved
}

function Get-FeaturePathsEnv {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit

    # Resolve feature directory.  Priority:
    #   1. SPECIFY_FEATURE_DIRECTORY env var (explicit override)
    #   2. .specify/feature.json "feature_directory" key (persisted by /speckit.specify)
    #   3. Branch-name-based prefix lookup (same as scripts/bash/common.sh)
    $featureJson = Join-Path $repoRoot '.specify/feature.json'
    if ($env:SPECIFY_FEATURE_DIRECTORY) {
        $featureDir = $env:SPECIFY_FEATURE_DIRECTORY
        # Normalize relative paths to absolute under repo root
        if (-not [System.IO.Path]::IsPathRooted($featureDir)) {
            $featureDir = Join-Path $repoRoot $featureDir
        }
    } elseif (Test-Path $featureJson) {
        $featureJsonRaw = Get-Content -LiteralPath $featureJson -Raw
        try {
            $featureConfig = $featureJsonRaw | ConvertFrom-Json
        } catch {
            [Console]::Error.WriteLine("ERROR: Failed to parse .specify/feature.json: $_")
            exit 1
        }
        if ($featureConfig.feature_directory) {
            $featureDir = $featureConfig.feature_directory
            # Normalize relative paths to absolute under repo root
            if (-not [System.IO.Path]::IsPathRooted($featureDir)) {
                $featureDir = Join-Path $repoRoot $featureDir
            }
        } else {
            $featureDir = Get-FeatureDirFromBranchPrefixOrExit -RepoRoot $repoRoot -CurrentBranch $currentBranch
        }
    } else {
        $featureDir = Get-FeatureDirFromBranchPrefixOrExit -RepoRoot $repoRoot -CurrentBranch $currentBranch
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

# Find a usable Python 3 executable (python3, python, or py -3).
# Returns the command/arguments as an array, or $null if none found.
function Get-Python3Command {
    if (Get-Command python3 -ErrorAction SilentlyContinue) { return @('python3') }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $ver = & python --version 2>&1
        if ($ver -match 'Python 3') { return @('python') }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $ver = & py -3 --version 2>&1
        if ($ver -match 'Python 3') { return @('py', '-3') }
    }
    return $null
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
                        Where-Object { $null -eq $_.Value.enabled -or $_.Value.enabled -ne $false } |
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

# Resolve a template name to composed content using composition strategies.
# Reads strategy metadata from preset manifests and composes content
# from multiple layers using prepend, append, or wrap strategies.
function Resolve-TemplateContent {
    param(
        [Parameter(Mandatory=$true)][string]$TemplateName,
        [Parameter(Mandatory=$true)][string]$RepoRoot
    )

    $base = Join-Path $RepoRoot '.specify/templates'

    # Collect all layers (highest priority first)
    $layerPaths = @()
    $layerStrategies = @()

    # Priority 1: Project overrides (always "replace")
    $override = Join-Path $base "overrides/$TemplateName.md"
    if (Test-Path $override) {
        $layerPaths += $override
        $layerStrategies += 'replace'
    }

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
                        Where-Object { $null -eq $_.Value.enabled -or $_.Value.enabled -ne $false } |
                        Sort-Object { if ($null -ne $_.Value.priority) { $_.Value.priority } else { 10 } } |
                        ForEach-Object { $_.Name }
                }
            } catch {
                $sortedPresets = @()
            }
        }

        if ($sortedPresets.Count -gt 0) {
            $pyCmd = Get-Python3Command
            if (-not $pyCmd) {
                # Check if any preset has strategy fields that would be ignored
                foreach ($pid in $sortedPresets) {
                    $mf = Join-Path $presetsDir "$pid/preset.yml"
                    if ((Test-Path $mf) -and (Select-String -Path $mf -Pattern 'strategy:' -Quiet -ErrorAction SilentlyContinue)) {
                        Write-Warning "No Python 3 found; preset composition strategies will be ignored"
                        break
                    }
                }
            }
            $yamlWarned = $false
            foreach ($presetId in $sortedPresets) {
                # Read strategy and file path from preset manifest
                $strategy = 'replace'
                $manifestFilePath = ''
                $manifest = Join-Path $presetsDir "$presetId/preset.yml"
                if ((Test-Path $manifest) -and $pyCmd) {
                    try {
                        # Use Python to parse YAML manifest for strategy and file path
                        $pyArgs = if ($pyCmd.Count -gt 1) { $pyCmd[1..($pyCmd.Count-1)] } else { @() }
                        $pyStderrFile = [System.IO.Path]::GetTempFileName()
                        $stratResult = & $pyCmd[0] @pyArgs -c @"
import sys
try:
    import yaml
except ImportError:
    print('yaml_missing', file=sys.stderr)
    print('replace\t')
    sys.exit(0)
try:
    with open(sys.argv[1]) as f:
        data = yaml.safe_load(f)
    for t in data.get('provides', {}).get('templates', []):
        if t.get('name') == sys.argv[2] and t.get('type', 'template') == 'template':
            print(t.get('strategy', 'replace') + '\t' + t.get('file', ''))
            sys.exit(0)
    print('replace\t')
except Exception:
    print('replace\t')
"@ $manifest $TemplateName 2>$pyStderrFile
                        if ($stratResult) {
                            $parts = $stratResult.Trim() -split "`t", 2
                            $strategy = $parts[0].ToLowerInvariant()
                            if ($parts.Count -gt 1 -and $parts[1]) { $manifestFilePath = $parts[1] }
                        }
                        if (-not $yamlWarned -and (Test-Path $pyStderrFile) -and (Get-Content $pyStderrFile -Raw -ErrorAction SilentlyContinue) -match 'yaml_missing') {
                            Write-Warning "PyYAML not available; composition strategies may be ignored"
                            $yamlWarned = $true
                        }
                        Remove-Item $pyStderrFile -Force -ErrorAction SilentlyContinue
                    } catch {
                        $strategy = 'replace'
                        if ($pyStderrFile) { Remove-Item $pyStderrFile -Force -ErrorAction SilentlyContinue }
                    }
                }
                # Try manifest file path first, then convention path
                $candidate = $null
                if ($manifestFilePath) {
                    # Reject absolute paths and parent traversal
                    if ([System.IO.Path]::IsPathRooted($manifestFilePath) -or $manifestFilePath -match '\.\.[\\/]') {
                        $manifestFilePath = ''
                    }
                }
                if ($manifestFilePath) {
                    $mf = Join-Path $presetsDir "$presetId/$manifestFilePath"
                    if (Test-Path $mf) { $candidate = $mf }
                }
                if (-not $candidate) {
                    $cf = Join-Path $presetsDir "$presetId/templates/$TemplateName.md"
                    if (Test-Path $cf) { $candidate = $cf }
                }
                if ($candidate) {
                    $layerPaths += $candidate
                    $layerStrategies += $strategy
                }
            }
        } else {
            # Fallback: alphabetical directory order (no registry or parse failure)
            foreach ($preset in Get-ChildItem -Path $presetsDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike '.*' }) {
                $candidate = Join-Path $preset.FullName "templates/$TemplateName.md"
                if (Test-Path $candidate) {
                    $layerPaths += $candidate
                    $layerStrategies += 'replace'
                }
            }
        }
    }

    # Priority 3: Extension-provided templates (always "replace")
    $extDir = Join-Path $RepoRoot '.specify/extensions'
    if (Test-Path $extDir) {
        foreach ($ext in Get-ChildItem -Path $extDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike '.*' } | Sort-Object Name) {
            $candidate = Join-Path $ext.FullName "templates/$TemplateName.md"
            if (Test-Path $candidate) {
                $layerPaths += $candidate
                $layerStrategies += 'replace'
            }
        }
    }

    # Priority 4: Core templates (always "replace")
    $core = Join-Path $base "$TemplateName.md"
    if (Test-Path $core) {
        $layerPaths += $core
        $layerStrategies += 'replace'
    }

    if ($layerPaths.Count -eq 0) { return $null }

    # If the top (highest-priority) layer is replace, it wins entirely —
    # lower layers are irrelevant regardless of their strategies.
    if ($layerStrategies[0] -eq 'replace') {
        return (Get-Content $layerPaths[0] -Raw)
    }

    # Check if any layer uses a non-replace strategy
    $hasComposition = $false
    foreach ($s in $layerStrategies) {
        if ($s -ne 'replace') { $hasComposition = $true; break }
    }

    if (-not $hasComposition) {
        return (Get-Content $layerPaths[0] -Raw)
    }

    # Find the effective base: scan from highest priority (index 0) downward
    # to find the nearest replace layer. Only compose layers above that base.
    $baseIdx = -1
    for ($i = 0; $i -lt $layerPaths.Count; $i++) {
        if ($layerStrategies[$i] -eq 'replace') {
            $baseIdx = $i
            break
        }
    }
    if ($baseIdx -lt 0) { return $null }

    $content = Get-Content $layerPaths[$baseIdx] -Raw

    for ($i = $baseIdx - 1; $i -ge 0; $i--) {
        $path = $layerPaths[$i]
        $strat = $layerStrategies[$i]
        $layerContent = Get-Content $path -Raw

        switch ($strat) {
            'replace' { $content = $layerContent }
            'prepend' { $content = "$layerContent`n`n$content" }
            'append'  { $content = "$content`n`n$layerContent" }
            'wrap'    {
                if (-not $layerContent.Contains('{CORE_TEMPLATE}')) {
                    throw "Wrap strategy missing {CORE_TEMPLATE} placeholder"
                }
                $content = $layerContent.Replace('{CORE_TEMPLATE}', $content)
            }
            default { throw "Unknown strategy: $strat" }
        }
    }

    return $content
}