#!/usr/bin/env pwsh
# Create a new feature
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$ShortName,
    [int]$Number = 0,
    [string]$JiraNumber,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$FeatureDescription
)
$ErrorActionPreference = 'Stop'

# Show help if requested (BEFORE any validation)
if ($Help) {
    Write-Host "Usage: ./create-new-feature.ps1 [-Json] [-ShortName <name>] [-Number N] [-JiraNumber <jira>] <feature description>"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json                 Output in JSON format"
    Write-Host "  -ShortName <name>     Provide a custom short name (2-4 words) for the branch"
    Write-Host "  -Number N             Specify branch number manually (overrides auto-detection)"
    Write-Host "  -JiraNumber <jira>    Jira ticket number (e.g., C12345-7890)"
    Write-Host "  -Help                 Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  ./create-new-feature.ps1 'Add user authentication system' -ShortName 'user-auth' -JiraNumber 'C12345-7890'"
    Write-Host "  ./create-new-feature.ps1 'Implement OAuth2 integration for API' -JiraNumber 'C12345-7890'"
    exit 0
}

# Load branch configuration from .guidelines/branch-config.json
function Load-BranchConfig {
    $configPath = ".guidelines/branch-config.json"

    if (Test-Path $configPath) {
        try {
            $config = Get-Content $configPath -Raw | ConvertFrom-Json
            return @{
                BranchPrefix = if ($config.branch_prefix) { $config.branch_prefix } else { "feature/" }
                BranchPattern = if ($config.branch_pattern) { $config.branch_pattern } else { "feature/<num>-<jira>-<shortname>" }
                JiraRequired = if ($null -ne $config.jira.required) { $config.jira.required } else { $true }
                JiraRegex = if ($config.jira.regex) { $config.jira.regex } else { "^C[0-9]{5}-[0-9]{4}$" }
                JiraFormat = if ($config.jira.format) { $config.jira.format } else { "C12345-7890" }
                NumberDigits = if ($config.number_format.digits) { $config.number_format.digits } else { 3 }
                NumberZeroPadded = if ($null -ne $config.number_format.zero_padded) { $config.number_format.zero_padded } else { $true }
                Separator = if ($config.separator) { $config.separator } else { "-" }
                DirIncludesPrefix = if ($null -ne $config.directory.includes_prefix) { $config.directory.includes_prefix } else { $false }
                DirBasePath = if ($config.directory.base_path) { $config.directory.base_path } else { "specs" }
            }
        } catch {
            Write-Warning "Failed to parse branch config, using defaults: $_"
        }
    }

    # Fallback to defaults (current behavior)
    return @{
        BranchPrefix = "feature/"
        BranchPattern = "feature/<num>-<jira>-<shortname>"
        JiraRequired = $true
        JiraRegex = "^C[0-9]{5}-[0-9]{4}$"
        JiraFormat = "C12345-7890"
        NumberDigits = 3
        NumberZeroPadded = $true
        Separator = "-"
        DirIncludesPrefix = $false
        DirBasePath = "specs"
    }
}

# Load configuration
$branchConfig = Load-BranchConfig

# Validate Jira number if provided or required
if ($branchConfig.JiraRequired -and -not $JiraNumber) {
    Write-Error "Error: Jira number is required by configuration but not provided`nUse -JiraNumber to specify (format: $($branchConfig.JiraFormat))"
    exit 1
}

if ($JiraNumber -and $JiraNumber -notmatch $branchConfig.JiraRegex) {
    Write-Error "Error: Jira number must match format $($branchConfig.JiraFormat)`nProvided: $JiraNumber`nPattern: $($branchConfig.JiraRegex)"
    exit 1
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

function Get-NextBranchNumber {
    param(
        [string]$ShortName,
        [string]$SpecsDir
    )

    # Fetch all remotes to get latest branch info (suppress errors if no remotes)
    try {
        git fetch --all --prune 2>$null | Out-Null
    } catch {
        # Ignore fetch errors
    }

    # Find remote branches matching both old and new patterns using git ls-remote
    # Old pattern: refs/heads/001-short-name
    # New pattern: refs/heads/feature/001-C12345-7890-short-name
    # Match only 3-digit spec-kit branches (001-, 002-, etc.) to avoid false positives
    $remoteBranches = @()
    try {
        $remoteRefs = git ls-remote --heads origin 2>$null
        if ($remoteRefs) {
            $remoteBranches = $remoteRefs | Where-Object { $_ -match "refs/heads/(feature/)?\d{3}-" } | ForEach-Object {
                if ($_ -match "refs/heads/(?:feature/)?(\d{3})-") {
                    [int]$matches[1]
                }
            }
        }
    } catch {
        # Ignore errors
    }

    # Check local branches (both patterns)
    # Match only 3-digit spec-kit branches to avoid matching unrelated numeric branches
    $localBranches = @()
    try {
        $allBranches = git branch 2>$null
        if ($allBranches) {
            $localBranches = $allBranches | Where-Object { $_ -match "^\*?\s*(feature/)?\d{3}-" } | ForEach-Object {
                if ($_ -match "(?:feature/)?(\d{3})-") {
                    [int]$matches[1]
                }
            }
        }
    } catch {
        # Ignore errors
    }

    # Check specs directory (directory name doesn't have feature/ prefix)
    # Match only 3-digit spec-kit directories (001-*, 002-*, etc.)
    $specDirs = @()
    if (Test-Path $SpecsDir) {
        try {
            $specDirs = Get-ChildItem -Path $SpecsDir -Directory | Where-Object { $_.Name -match "^(\d{3})-" } | ForEach-Object {
                if ($_.Name -match "^(\d{3})-") {
                    [int]$matches[1]
                }
            }
        } catch {
            # Ignore errors
        }
    }

    # Combine all sources and get the highest number
    $maxNum = 0
    foreach ($num in ($remoteBranches + $localBranches + $specDirs)) {
        if ($num -gt $maxNum) {
            $maxNum = $num
        }
    }

    # Return next number
    return $maxNum + 1
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

$specsDir = Join-Path $repoRoot $branchConfig.DirBasePath
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
        $result = $Description.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
        $fallbackWords = ($result -split '-') | Where-Object { $_ } | Select-Object -First 3
        return [string]::Join('-', $fallbackWords)
    }
}

# Generate branch name
if ($ShortName) {
    # Use provided short name, just clean it up
    $branchSuffix = $ShortName.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
} else {
    # Generate from description with smart filtering
    $branchSuffix = Get-BranchName -Description $featureDesc
}

# Determine branch number
if ($Number -eq 0) {
    if ($hasGit) {
        # Check existing branches on remotes
        $Number = Get-NextBranchNumber -ShortName $branchSuffix -SpecsDir $specsDir
    } else {
        # Fall back to local directory check
        $highest = 0
        if (Test-Path $specsDir) {
            Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
                if ($_.Name -match '^(\d{3})') {
                    $num = [int]$matches[1]
                    if ($num -gt $highest) { $highest = $num }
                }
            }
        }
        $Number = $highest + 1
    }
}

# Format branch number according to configuration
if ($branchConfig.NumberZeroPadded) {
    $formatString = "{0:D$($branchConfig.NumberDigits)}"
    $featureNum = $formatString -f $Number
} else {
    $featureNum = "$Number"
}

# Build branch name based on configuration pattern
# Pattern placeholders: <num>, <jira>, <shortname>
$branchName = $branchConfig.BranchPattern
$branchName = $branchName -replace '<num>', $featureNum
$branchName = $branchName -replace '<shortname>', $branchSuffix

if ($JiraNumber) {
    $branchName = $branchName -replace '<jira>', $JiraNumber
} else {
    # Remove jira placeholder and extra separators if jira not provided
    $sep = [regex]::Escape($branchConfig.Separator)
    $branchName = $branchName -replace "$sep<jira>$sep", $branchConfig.Separator
    $branchName = $branchName -replace "$sep<jira>", ""
    $branchName = $branchName -replace "<jira>$sep", ""
    $branchName = $branchName -replace "<jira>", ""
}

# GitHub enforces a 244-byte limit on branch names
# Validate and truncate if necessary
$maxBranchLength = 244
if ($branchName.Length -gt $maxBranchLength) {
    # Calculate how much we need to trim from suffix
    # Account for: "feature/" (8) + feature number (3) + hyphens + optional Jira number
    $prefixLength = 8 + 3 + 1  # feature/ + 001 + hyphen
    if ($JiraNumber) {
        $prefixLength = $prefixLength + $JiraNumber.Length + 1  # + jira + hyphen
    }
    $maxSuffixLength = $maxBranchLength - $prefixLength

    # Truncate suffix
    $truncatedSuffix = $branchSuffix.Substring(0, [Math]::Min($branchSuffix.Length, $maxSuffixLength))
    # Remove trailing hyphen if truncation created one
    $truncatedSuffix = $truncatedSuffix -replace '-$', ''

    $originalBranchName = $branchName
    if ($JiraNumber) {
        $branchName = "feature/$featureNum-$JiraNumber-$truncatedSuffix"
    } else {
        $branchName = "feature/$featureNum-$truncatedSuffix"
    }

    Write-Warning "[specify] Branch name exceeded GitHub's 244-byte limit"
    Write-Warning "[specify] Original: $originalBranchName ($($originalBranchName.Length) bytes)"
    Write-Warning "[specify] Truncated to: $branchName ($($branchName.Length) bytes)"
}

if ($hasGit) {
    try {
        git checkout -b $branchName | Out-Null
    } catch {
        Write-Warning "Failed to create git branch: $branchName"
    }
} else {
    Write-Warning "[specify] Warning: Git repository not detected; skipped branch creation for $branchName"
}

# Feature directory naming depends on configuration
# Extract directory name from branch name (remove prefix if configured)
if ($branchConfig.DirIncludesPrefix) {
    $dirName = $branchName
} else {
    # Remove the branch prefix if present
    $prefixPattern = [regex]::Escape($branchConfig.BranchPrefix)
    $dirName = $branchName -replace "^$prefixPattern", ""
}
$featureDir = Join-Path $specsDir $dirName
New-Item -ItemType Directory -Path $featureDir -Force | Out-Null

$template = Join-Path $repoRoot '.specify/templates/spec-template.md'
$specFile = Join-Path $featureDir 'spec.md'
if (Test-Path $template) { 
    Copy-Item $template $specFile -Force 
} else { 
    New-Item -ItemType File -Path $specFile | Out-Null 
}

# Set the SPECIFY_FEATURE environment variable for the current session
$env:SPECIFY_FEATURE = $branchName

if ($Json) {
    $obj = [PSCustomObject]@{ 
        BRANCH_NAME = $branchName
        SPEC_FILE = $specFile
        FEATURE_NUM = $featureNum
        HAS_GIT = $hasGit
    }
    $obj | ConvertTo-Json -Compress
} else {
    Write-Output "BRANCH_NAME: $branchName"
    Write-Output "SPEC_FILE: $specFile"
    Write-Output "FEATURE_NUM: $featureNum"
    Write-Output "HAS_GIT: $hasGit"
    Write-Output "SPECIFY_FEATURE environment variable set to: $branchName"
}

