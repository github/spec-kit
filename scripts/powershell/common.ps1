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
        [bool]$HasGit = $true,
        [string]$RepoRoot = (Get-RepoRoot)
    )
    
    # For non-git repos, we can't enforce branch naming but still provide output
    if (-not $HasGit) {
        Write-Warning "[specify] Warning: Git repository not detected; skipped branch validation"
        return $true
    }
    
    # Load branch template to build validation pattern
    $template = Get-BranchTemplate -RepoRoot $RepoRoot
    if (-not $template) {
        $template = '{number}-{short_name}'
    }
    
    # Build a regex pattern from template by replacing placeholders.
    # First, substitute placeholders with temporary markers so we can safely escape
    # all other characters, then replace markers with regex fragments:
    # {number}      -> [0-9]{3}
    # {short_name}  -> .+
    # {username}    -> [a-z0-9-]+
    # {email_prefix}-> [a-z0-9.-]+
    $pattern = $template
    # Replace placeholders with marker tokens
    $pattern = $pattern -replace '\{number\}', '__NUMBER__'
    $pattern = $pattern -replace '\{short_name\}', '__SHORT_NAME__'
    $pattern = $pattern -replace '\{username\}', '__USERNAME__'
    $pattern = $pattern -replace '\{email_prefix\}', '__EMAIL_PREFIX__'
    # Escape all non-placeholder characters so the template is treated as literal text
    $pattern = [regex]::Escape($pattern)
    # Replace markers with their regex fragments
    $pattern = $pattern -replace '__NUMBER__', '[0-9]{3}'
    $pattern = $pattern -replace '__SHORT_NAME__', '.+'
    $pattern = $pattern -replace '__USERNAME__', '[a-z0-9-]+'
    $pattern = $pattern -replace '__EMAIL_PREFIX__', '[a-z0-9.-]+'
    
    $pattern = "^${pattern}$"
    
    if ($Branch -notmatch $pattern) {
        # Build example from template
        $example = $template
        $example = $example -replace '\{number\}', '001'
        $example = $example -replace '\{short_name\}', 'feature-name'
        $example = $example -replace '\{username\}', 'jdoe'
        $example = $example -replace '\{email_prefix\}', 'jdoe'
        
        Write-Output "ERROR: Not on a feature branch. Current branch: $Branch"
        Write-Output "Feature branches should match pattern: $template"
        Write-Output "Example: $example"
        return $false
    }
    return $true
}

<#
.SYNOPSIS
    Find feature directory by numeric prefix instead of exact branch match
.DESCRIPTION
    This allows multiple branches to work on the same spec (e.g., 004-fix-bug, 004-add-feature).
    Supports template-based branch names like "jdoe/001-feature" where number appears after prefix.
.PARAMETER RepoRoot
    Repository root path
.PARAMETER Branch
    Branch name to find spec directory for
.RETURNS
    Path to the feature directory
#>
function Get-FeatureDir {
    param(
        [string]$RepoRoot,
        [string]$Branch
    )
    
    $specsDir = Join-Path $RepoRoot 'specs'
    
    # Load branch template to understand where {number} appears
    $template = Get-BranchTemplate -RepoRoot $RepoRoot
    if (-not $template) {
        $template = '{number}-{short_name}'
    }
    
    # Build regex to extract the numeric portion based on template structure
    # Replace {number} with capture group, other placeholders with matchers
    $extractPattern = $template
    $extractPattern = $extractPattern -replace '\{number\}', '([0-9]{3})'
    $extractPattern = $extractPattern -replace '\{short_name\}', '.+'
    $extractPattern = $extractPattern -replace '\{username\}', '[a-z0-9-]+'
    $extractPattern = $extractPattern -replace '\{email_prefix\}', '[a-z0-9.-]+'
    $extractPattern = "^${extractPattern}$"
    
    # Extract numeric prefix from branch based on template pattern
    if ($Branch -notmatch $extractPattern) {
        # If branch doesn't match template, fall back to exact match
        return Join-Path $specsDir $Branch
    }
    
    $prefix = $matches[1]
    
    # Search for directories in specs/ that contain this prefix number
    # For template "jdoe/{number}-{short_name}", branch "jdoe/001-feature" -> look in specs/jdoe/001-*
    # For template "{number}-{short_name}", branch "001-feature" -> look in specs/001-*
    
    # Determine the search path based on template structure (prefix before {number})
    $templatePrefix = ''
    if ($template -match '^(.*?)\{number\}') {
        $templatePrefix = $matches[1]
    }
    
    if ($templatePrefix -and $templatePrefix.Contains('/')) {
        # Template has path prefix (e.g., "{username}/") - extract from branch
        $branchPrefix = ''
        if ($Branch -match "^(.*?)${prefix}-") {
            $branchPrefix = $matches[1]
        }
        $searchDir = Join-Path $specsDir $branchPrefix.TrimEnd('/')
    } else {
        $searchDir = $specsDir
    }
    
    if (-not (Test-Path $searchDir)) {
        return Join-Path $specsDir $Branch
    }
    
    # Search for directories starting with this prefix
    $matchingDirs = @()
    Get-ChildItem -Path $searchDir -Directory | ForEach-Object {
        if ($_.Name -match "^${prefix}-") {
            $matchingDirs += $_
        }
    }
    
    # Handle results
    if ($matchingDirs.Count -eq 0) {
        # No match found - return the branch name path
        return Join-Path $specsDir $Branch
    } elseif ($matchingDirs.Count -eq 1) {
        # Exactly one match
        return $matchingDirs[0].FullName
    } else {
        # Multiple matches - warn and return first
        Write-Warning "Multiple spec directories found with prefix '$prefix': $($matchingDirs.Name -join ', ')"
        Write-Warning "Please ensure only one spec directory exists per numeric prefix."
        return Join-Path $specsDir $Branch
    }
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
    
    # Escape special regex characters in prefix for branch matching
    $escapedPrefix = [regex]::Escape($Prefix)
    
    # Check specs directory for matching directories
    # For slashed prefixes (e.g., "johndoe/"), the structure is specs/johndoe/001-feature/
    # We need to navigate into the prefix path and match numbered directories there
    if (Test-Path $specsDir) {
        # Normalize prefix: remove trailing slash for path joining
        $prefixPath = $Prefix.TrimEnd('/')
        
        if ($prefixPath -match '/') {
            # Slashed prefix: navigate to the nested directory and look for numbered dirs
            $prefixDir = Join-Path $specsDir $prefixPath
            if (Test-Path $prefixDir) {
                Get-ChildItem -Path $prefixDir -Directory | ForEach-Object {
                    # Match directories starting with 3-digit number
                    if ($_.Name -match '^(\d{3})-') {
                        $num = [int]$matches[1]
                        if ($num -gt $highest) {
                            $highest = $num
                        }
                    }
                }
            }
        } else {
            # Non-slashed prefix: look at immediate children with prefix pattern
            Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
                if ($_.Name -match "^$escapedPrefix(\d{3})-") {
                    $num = [int]$matches[1]
                    if ($num -gt $highest) {
                        $highest = $num
                    }
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

