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
            if ($_.Name -match '^(\d{3})-') {
                $num = [int]$matches[1]
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
    
    if ($Branch -notmatch '^[0-9]{3}-') {
        Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"
        Write-Output "Feature branches should be named like: 001-feature-name"
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
    $featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $currentBranch
    
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

# =============================================================================
# TOML Settings Functions (for branch template customization)
# =============================================================================

<#
.SYNOPSIS
    Parse a single key from a TOML file
.DESCRIPTION
    Extracts a value from a TOML file, supporting dotted keys like "branch.template"
.PARAMETER File
    Path to the TOML file
.PARAMETER Key
    Key to extract (supports dotted notation like "branch.template")
.EXAMPLE
    Get-TomlValue -File ".specify/settings.toml" -Key "branch.template"
#>
function Get-TomlValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$File,
        [Parameter(Mandatory = $true)]
        [string]$Key
    )
    
    if (-not (Test-Path $File)) {
        return $null
    }
    
    $content = Get-Content $File -Raw -ErrorAction SilentlyContinue
    if (-not $content) {
        return $null
    }
    
    # Handle dotted keys like "branch.template"
    if ($Key -match '\.') {
        $parts = $Key -split '\.', 2
        $section = $parts[0]
        $subkey = $parts[1]
        
        # Find the section and extract the key
        $inSection = $false
        foreach ($line in ($content -split "`n")) {
            $line = $line.Trim()
            
            # Check for section header
            if ($line -match '^\[([^\]]+)\]$') {
                $inSection = ($matches[1] -eq $section)
                continue
            }
            
            # If in the right section, look for the key
            if ($inSection -and $line -match "^$subkey\s*=\s*`"([^`"]*)`"") {
                return $matches[1]
            }
        }
    }
    else {
        # Simple key without section
        if ($content -match "$Key\s*=\s*`"([^`"]*)`"") {
            return $matches[1]
        }
    }
    
    return $null
}

<#
.SYNOPSIS
    Load branch template from settings file
.PARAMETER RepoRoot
    Repository root path (defaults to current repo root)
.RETURNS
    Template string or $null if not found
#>
function Get-BranchTemplate {
    param(
        [string]$RepoRoot = (Get-RepoRoot)
    )
    
    $settingsFile = Join-Path $RepoRoot '.specify/settings.toml'
    
    if (Test-Path $settingsFile) {
        return Get-TomlValue -File $settingsFile -Key 'branch.template'
    }
    
    return $null
}

# =============================================================================
# Username and Email Resolution Functions
# =============================================================================

<#
.SYNOPSIS
    Resolve {username} variable from Git config or OS fallback
.RETURNS
    Normalized username (lowercase, hyphens for special chars)
#>
function Resolve-Username {
    $username = $null
    
    try {
        $username = git config user.name 2>$null
    }
    catch {
        # Git command failed
    }
    
    if (-not $username) {
        # Fallback to OS username
        $username = $env:USERNAME
        if (-not $username) {
            $username = $env:USER
        }
        if (-not $username) {
            $username = 'unknown'
        }
    }
    
    # Normalize: lowercase, replace non-alphanumeric with hyphens, collapse multiple hyphens
    $normalized = $username.ToLower() -replace '[^a-z0-9]', '-' -replace '-+', '-' -replace '^-', '' -replace '-$', ''
    return $normalized
}

<#
.SYNOPSIS
    Resolve {email_prefix} variable from Git config
.RETURNS
    Email prefix (portion before @) or empty string
#>
function Resolve-EmailPrefix {
    $email = $null
    
    try {
        $email = git config user.email 2>$null
    }
    catch {
        # Git command failed
    }
    
    if ($email -and $email -match '^([^@]+)@') {
        return $matches[1].ToLower()
    }
    
    # Returns empty string if no email configured (per FR-002 clarification)
    return ''
}

# =============================================================================
# Branch Name Validation Functions
# =============================================================================

<#
.SYNOPSIS
    Validate branch name against Git rules
.PARAMETER Name
    Branch name to validate
.RETURNS
    $true if valid, $false if invalid (writes error to host)
#>
function Test-BranchName {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )
    
    # Cannot be empty
    if (-not $Name) {
        Write-Error "Error: Branch name cannot be empty"
        return $false
    }
    
    # Cannot start with hyphen
    if ($Name -match '^-') {
        Write-Error "Error: Branch name cannot start with hyphen: $Name"
        return $false
    }
    
    # Cannot contain ..
    if ($Name -match '\.\.') {
        Write-Error "Error: Branch name cannot contain '..': $Name"
        return $false
    }
    
    # Cannot contain forbidden characters: ~ ^ : ? * [ \
    if ($Name -match '[~\^:\?\*\[\\]') {
        Write-Error "Error: Branch name contains invalid characters (~^:?*[\): $Name"
        return $false
    }
    
    # Cannot end with .lock
    if ($Name -match '\.lock$') {
        Write-Error "Error: Branch name cannot end with '.lock': $Name"
        return $false
    }
    
    # Cannot end with /
    if ($Name -match '/$') {
        Write-Error "Error: Branch name cannot end with '/': $Name"
        return $false
    }
    
    # Cannot contain //
    if ($Name -match '//') {
        Write-Error "Error: Branch name cannot contain '//': $Name"
        return $false
    }
    
    # Check max length (244 bytes for GitHub)
    if ($Name.Length -gt 244) {
        Write-Warning "Warning: Branch name exceeds 244 bytes (GitHub limit): $Name"
        # Return success but warn - truncation handled elsewhere
    }
    
    return $true
}

# =============================================================================
# Per-User Number Scoping Functions
# =============================================================================

<#
.SYNOPSIS
    Get highest feature number for a specific prefix pattern
.PARAMETER Prefix
    Prefix to match (e.g., "johndoe/" or "feature/johndoe/")
.PARAMETER RepoRoot
    Repository root path (defaults to current repo root)
.RETURNS
    Highest number found (0 if none)
#>
function Get-HighestNumberForPrefix {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Prefix,
        [string]$RepoRoot = (Get-RepoRoot)
    )
    
    $specsDir = Join-Path $RepoRoot 'specs'
    $highest = 0
    
    # Escape special regex characters in prefix
    $escapedPrefix = [regex]::Escape($Prefix)
    
    # Check specs directory for matching directories
    if (Test-Path $specsDir) {
        Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
            if ($_.Name -match "^$escapedPrefix(\d{3})-") {
                $num = [int]$matches[1]
                if ($num -gt $highest) {
                    $highest = $num
                }
            }
        }
    }
    
    # Also check git branches if available
    try {
        $branches = git branch -a 2>$null
        if ($LASTEXITCODE -eq 0 -and $branches) {
            foreach ($branch in $branches) {
                # Clean branch name
                $cleanBranch = $branch.Trim() -replace '^\*?\s+', '' -replace '^remotes/[^/]+/', ''
                
                # Check if branch matches prefix pattern
                if ($cleanBranch -match "^$escapedPrefix(\d{3})-") {
                    $num = [int]$matches[1]
                    if ($num -gt $highest) {
                        $highest = $num
                    }
                }
            }
        }
    }
    catch {
        # Git not available or command failed
    }
    
    return $highest
}

