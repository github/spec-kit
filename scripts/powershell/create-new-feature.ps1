#!/usr/bin/env pwsh
# Create a new feature
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$ShortName,
    [int]$Number = 0,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$FeatureDescription
)
$ErrorActionPreference = 'Stop'

# Import common functions (for Get-ConfigValue)
. (Join-Path $PSScriptRoot "common.ps1")

# Show help if requested
if ($Help) {
    Write-Host "Usage: ./create-new-feature.ps1 [-Json] [-ShortName <name>] [-Number N] <feature description>"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json               Output in JSON format"
    Write-Host "  -ShortName <name>   Provide a custom short name (2-4 words) for the branch"
    Write-Host "  -Number N           Specify branch number manually (overrides auto-detection)"
    Write-Host "  -Help               Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  ./create-new-feature.ps1 'Add user authentication system' -ShortName 'user-auth'"
    Write-Host "  ./create-new-feature.ps1 'Implement OAuth2 integration for API'"
    exit 0
}

# Check if feature description provided
if (-not $FeatureDescription -or $FeatureDescription.Count -eq 0) {
    Write-Error "Usage: ./create-new-feature.ps1 [-Json] [-ShortName <name>] <feature description>"
    exit 1
}

$featureDesc = ($FeatureDescription -join ' ').Trim()

# Resolve repository root. Prefer git information when available, but fall back
# to searching for repository markers so the workflow still functions in repositories that
# were initialized with --no-git.
function Find-RepositoryRoot {
    param(
        [string]$StartDir,
        [string[]]$Markers = @('.git', '.specify')
    )
    $current = Resolve-Path $StartDir
    while ($true) {
        foreach ($marker in $Markers) {
            if (Test-Path (Join-Path $current $marker)) {
                return $current
            }
        }
        $parent = Split-Path $current -Parent
        if ($parent -eq $current) {
            # Reached filesystem root without finding markers
            return $null
        }
        $current = $parent
    }
}

function Get-HighestNumberFromSpecs {
    param([string]$SpecsDir)
    
    $highest = 0
    if (Test-Path $SpecsDir) {
        Get-ChildItem -Path $SpecsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d+)') {
                $num = [int]$matches[1]
                if ($num -gt $highest) { $highest = $num }
            }
        }
    }
    return $highest
}

function Get-HighestNumberFromBranches {
    param()
    
    $highest = 0
    try {
        $branches = git branch -a 2>$null
        if ($LASTEXITCODE -eq 0) {
            foreach ($branch in $branches) {
                # Clean branch name: remove leading markers and remote prefixes
                $cleanBranch = $branch.Trim() -replace '^\*?\s+', '' -replace '^remotes/[^/]+/', ''
                
                # Extract feature number if branch matches pattern ###-*
                if ($cleanBranch -match '^(\d+)-') {
                    $num = [int]$matches[1]
                    if ($num -gt $highest) { $highest = $num }
                }
            }
        }
    } catch {
        # If git command fails, return 0
        Write-Verbose "Could not check Git branches: $_"
    }
    return $highest
}

function Get-NextBranchNumber {
    param(
        [string]$SpecsDir
    )

    # Fetch all remotes to get latest branch info (suppress errors if no remotes)
    try {
        git fetch --all --prune 2>$null | Out-Null
    } catch {
        # Ignore fetch errors
    }

    # Get highest number from ALL branches (not just matching short name)
    $highestBranch = Get-HighestNumberFromBranches

    # Get highest number from ALL specs (not just matching short name)
    $highestSpec = Get-HighestNumberFromSpecs -SpecsDir $SpecsDir

    # Take the maximum of both
    $maxNum = [Math]::Max($highestBranch, $highestSpec)

    # Return next number
    return $maxNum + 1
}

function ConvertTo-CleanBranchName {
    param([string]$Name)

    return $Name.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
}

# Calculate worktree path based on strategy
# Naming convention: <repo_name>-<branch_name> for sibling/custom strategies
function Get-WorktreePath {
    param(
        [string]$BranchName,
        [string]$RepoRoot
    )

    $cfgFile = Join-Path $RepoRoot ".specify/config.json"
    $strategy = Get-ConfigValue -Key "worktree_strategy" -Default "sibling" -ConfigFile $cfgFile
    $customPath = Get-ConfigValue -Key "worktree_custom_path" -Default "" -ConfigFile $cfgFile
    $repoName = Split-Path $RepoRoot -Leaf

    switch ($strategy) {
        "nested" {
            # Nested uses just branch name since it's inside the repo
            return Join-Path $RepoRoot ".worktrees/$BranchName"
        }
        "sibling" {
            # Sibling uses repo_name-branch_name for clarity
            return Join-Path (Split-Path $RepoRoot -Parent) "$repoName-$BranchName"
        }
        "custom" {
            if ($customPath) {
                # Custom also uses repo_name-branch_name for clarity
                return Join-Path $customPath "$repoName-$BranchName"
            }
            else {
                # Fallback to nested if custom path not set
                return Join-Path $RepoRoot ".worktrees/$BranchName"
            }
        }
        default {
            return Join-Path $RepoRoot ".worktrees/$BranchName"
        }
    }
}

# Check if a git branch exists (locally or remotely)
function Test-BranchExists {
    param([string]$BranchName)

    # Check local branches
    try {
        git rev-parse --verify $BranchName 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
    }
    catch { }

    # Check remote branches
    try {
        git rev-parse --verify "origin/$BranchName" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
    }
    catch { }

    return $false
}

$fallbackRoot = (Find-RepositoryRoot -StartDir $PSScriptRoot)
if (-not $fallbackRoot) {
    Write-Error "Error: Could not determine repository root. Please run this script from within the repository."
    exit 1
}

try {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0) {
        $hasGit = $true
    } else {
        throw "Git not available"
    }
} catch {
    $repoRoot = $fallbackRoot
    $hasGit = $false
}

Set-Location $repoRoot

$specsDir = Join-Path $repoRoot 'specs'
New-Item -ItemType Directory -Path $specsDir -Force | Out-Null

# Function to generate branch name with stop word filtering and length filtering
function Get-BranchName {
    param([string]$Description)
    
    # Common stop words to filter out
    $stopWords = @(
        'i', 'a', 'an', 'the', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'with', 'from',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall',
        'this', 'that', 'these', 'those', 'my', 'your', 'our', 'their',
        'want', 'need', 'add', 'get', 'set'
    )
    
    # Convert to lowercase and extract words (alphanumeric only)
    $cleanName = $Description.ToLower() -replace '[^a-z0-9\s]', ' '
    $words = $cleanName -split '\s+' | Where-Object { $_ }
    
    # Filter words: remove stop words and words shorter than 3 chars (unless they're uppercase acronyms in original)
    $meaningfulWords = @()
    foreach ($word in $words) {
        # Skip stop words
        if ($stopWords -contains $word) { continue }
        
        # Keep words that are length >= 3 OR appear as uppercase in original (likely acronyms)
        if ($word.Length -ge 3) {
            $meaningfulWords += $word
        } elseif ($Description -match "\b$($word.ToUpper())\b") {
            # Keep short words if they appear as uppercase in original (likely acronyms)
            $meaningfulWords += $word
        }
    }
    
    # If we have meaningful words, use first 3-4 of them
    if ($meaningfulWords.Count -gt 0) {
        $maxWords = if ($meaningfulWords.Count -eq 4) { 4 } else { 3 }
        $result = ($meaningfulWords | Select-Object -First $maxWords) -join '-'
        return $result
    } else {
        # Fallback to original logic if no meaningful words found
        $result = ConvertTo-CleanBranchName -Name $Description
        $fallbackWords = ($result -split '-') | Where-Object { $_ } | Select-Object -First 3
        return [string]::Join('-', $fallbackWords)
    }
}

# Generate branch name
if ($ShortName) {
    # Use provided short name, just clean it up
    $branchSuffix = ConvertTo-CleanBranchName -Name $ShortName
} else {
    # Generate from description with smart filtering
    $branchSuffix = Get-BranchName -Description $featureDesc
}

# Determine branch number
if ($Number -eq 0) {
    if ($hasGit) {
        # Check existing branches on remotes
        $Number = Get-NextBranchNumber -SpecsDir $specsDir
    } else {
        # Fall back to local directory check
        $Number = (Get-HighestNumberFromSpecs -SpecsDir $specsDir) + 1
    }
}

$featureNum = ('{0:000}' -f $Number)
$branchName = "$featureNum-$branchSuffix"

# GitHub enforces a 244-byte limit on branch names
# Validate and truncate if necessary
$maxBranchLength = 244
if ($branchName.Length -gt $maxBranchLength) {
    # Calculate how much we need to trim from suffix
    # Account for: feature number (3) + hyphen (1) = 4 chars
    $maxSuffixLength = $maxBranchLength - 4
    
    # Truncate suffix
    $truncatedSuffix = $branchSuffix.Substring(0, [Math]::Min($branchSuffix.Length, $maxSuffixLength))
    # Remove trailing hyphen if truncation created one
    $truncatedSuffix = $truncatedSuffix -replace '-$', ''
    
    $originalBranchName = $branchName
    $branchName = "$featureNum-$truncatedSuffix"
    
    Write-Warning "[specify] Branch name exceeded GitHub's 244-byte limit"
    Write-Warning "[specify] Original: $originalBranchName ($($originalBranchName.Length) bytes)"
    Write-Warning "[specify] Truncated to: $branchName ($($branchName.Length) bytes)"
}

# Determine git mode and create feature
$configFile = Join-Path $repoRoot ".specify/config.json"
$gitMode = Get-ConfigValue -Key "git_mode" -Default "branch" -ConfigFile $configFile

# Worktree-specific pre-flight checks (only in worktree mode)
if ($hasGit -and $gitMode -eq "worktree") {
    # Check for uncommitted changes (warning only, per FR-013)
    $status = git status --porcelain 2>$null
    if ($status) {
        Write-Warning "[specify] Warning: Uncommitted changes in working directory will not appear in new worktree."
    }

    # Check for orphaned worktrees (warning only, per FR-012)
    $worktreeInfo = git worktree list --porcelain 2>$null
    if ($worktreeInfo -match "prunable") {
        Write-Warning "[specify] Warning: Orphaned worktree entries detected. Run 'git worktree prune' to clean up."
    }
}
$creationMode = "branch"
$featureRoot = $repoRoot
$worktreePath = ""

if ($hasGit) {
    if ($gitMode -eq "worktree") {
        # Worktree mode
        $worktreePath = Get-WorktreePath -BranchName $branchName -RepoRoot $repoRoot
        $worktreeParent = Split-Path $worktreePath -Parent

        # Check if parent path is writable (T033)
        if (-not (Test-Path $worktreeParent)) {
            try {
                New-Item -ItemType Directory -Path $worktreeParent -Force -ErrorAction Stop | Out-Null
            }
            catch {
                Write-Error "[specify] Error: Cannot create worktree parent directory: $worktreeParent"
                Write-Error "[specify] Suggestions:"
                Write-Error "[specify]   - Use nested strategy: configure-worktree.ps1 -Strategy nested"
                Write-Error "[specify]   - Switch to branch mode: configure-worktree.ps1 -Mode branch"
                Write-Error "[specify]   - Create the directory manually and retry"
                exit 1
            }
        }
        else {
            # Test writability by attempting to create a temp file
            $testFile = Join-Path $worktreeParent ".specify-write-test-$(Get-Random)"
            try {
                New-Item -ItemType File -Path $testFile -Force -ErrorAction Stop | Out-Null
            }
            catch {
                Write-Error "[specify] Error: Worktree parent directory is not writable: $worktreeParent"
                Write-Error "[specify] Suggestions:"
                Write-Error "[specify]   - Use nested strategy: configure-worktree.ps1 -Strategy nested"
                Write-Error "[specify]   - Switch to branch mode: configure-worktree.ps1 -Mode branch"
                Write-Error "[specify]   - Fix directory permissions and retry"
                exit 1
            }
            finally {
                Remove-Item $testFile -Force -ErrorAction SilentlyContinue
            }
        }
    }

    if ($gitMode -eq "worktree") {
        # Check if branch already exists
        if (Test-BranchExists -BranchName $branchName) {
            # Attach worktree to existing branch (without -b flag)
            try {
                git worktree add $worktreePath $branchName 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    $creationMode = "worktree"
                    $featureRoot = $worktreePath
                }
                else {
                    throw "Worktree creation failed"
                }
            }
            catch {
                Write-Error "[specify] Error: Failed to create worktree for existing branch '$branchName' at $worktreePath"
                Write-Error "[specify] Suggestions:"
                Write-Error "[specify]   - Check existing worktrees: git worktree list"
                Write-Error "[specify]   - Remove stale worktree: git worktree remove <path>"
                Write-Error "[specify]   - Prune orphaned entries: git worktree prune"
                Write-Error "[specify]   - Switch to branch mode: configure-worktree.ps1 -Mode branch"
                exit 1
            }
        }
        else {
            # Create new branch with worktree
            try {
                git worktree add $worktreePath -b $branchName 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    $creationMode = "worktree"
                    $featureRoot = $worktreePath
                }
                else {
                    throw "Worktree creation failed"
                }
            }
            catch {
                Write-Error "[specify] Error: Failed to create worktree for new branch '$branchName' at $worktreePath"
                Write-Error "[specify] Suggestions:"
                Write-Error "[specify]   - Check existing worktrees: git worktree list"
                Write-Error "[specify]   - Prune orphaned entries: git worktree prune"
                Write-Error "[specify]   - Switch to branch mode: configure-worktree.ps1 -Mode branch"
                exit 1
            }
        }
    }
    else {
        # Standard branch mode
        try {
            git checkout -b $branchName | Out-Null
        }
        catch {
            Write-Warning "Failed to create git branch: $branchName"
        }
        $creationMode = "branch"
        $featureRoot = $repoRoot
    }
}
else {
    Write-Warning "[specify] Warning: Git repository not detected; skipped branch creation for $branchName"
    $creationMode = "branch"
    $featureRoot = $repoRoot
}

# Create feature directory and spec file
# In worktree mode, create specs in the worktree; in branch mode, create in main repo
if ($creationMode -eq "worktree") {
    $featureDir = Join-Path $featureRoot "specs/$branchName"
}
else {
    $featureDir = Join-Path $specsDir $branchName
}
New-Item -ItemType Directory -Path $featureDir -Force | Out-Null

$template = Join-Path $repoRoot '.specify/templates/spec-template.md'
$specFile = Join-Path $featureDir 'spec.md'
if (Test-Path $template) {
    Copy-Item $template $specFile -Force
}
else {
    New-Item -ItemType File -Path $specFile | Out-Null
}

# Set the SPECIFY_FEATURE environment variable for the current session
$env:SPECIFY_FEATURE = $branchName

if ($Json) {
    $obj = [PSCustomObject]@{
        BRANCH_NAME  = $branchName
        SPEC_FILE    = $specFile
        FEATURE_NUM  = $featureNum
        FEATURE_ROOT = $featureRoot
        MODE         = $creationMode
        HAS_GIT      = $hasGit
    }
    $obj | ConvertTo-Json -Compress
}
else {
    Write-Output "BRANCH_NAME: $branchName"
    Write-Output "SPEC_FILE: $specFile"
    Write-Output "FEATURE_NUM: $featureNum"
    Write-Output "FEATURE_ROOT: $featureRoot"
    Write-Output "MODE: $creationMode"
    Write-Output "HAS_GIT: $hasGit"
    Write-Output "SPECIFY_FEATURE environment variable set to: $branchName"
}

