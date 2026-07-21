#!/usr/bin/env pwsh
# Git extension: create-new-feature-branch.ps1
# Creates a git feature branch only. The feature directory and spec file
# are created by the core create-new-feature.ps1 script.
# Sources common.ps1 from the project's installed scripts, falling back to
# git-common.ps1 for minimal git helpers.
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$AllowExistingBranch,
    [switch]$DryRun,
    [string]$ShortName,
    [Parameter()]
    [long]$Number = 0,
    [switch]$Timestamp,
    [switch]$Help,
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$FeatureDescription
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Host "Usage: ./create-new-feature-branch.ps1 [-Json] [-DryRun] [-AllowExistingBranch] [-ShortName <name>] [-Number N] [-Timestamp] <feature description>"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json               Output in JSON format"
    Write-Host "  -DryRun             Compute branch name without creating the branch"
    Write-Host "  -AllowExistingBranch  Switch to branch if it already exists instead of failing"
    Write-Host "  -ShortName <name>   Provide a custom short name (2-4 words) for the branch"
    Write-Host "  -Number N           Specify branch number manually (overrides auto-detection)"
    Write-Host "  -Timestamp          Use timestamp prefix (YYYYMMDD-HHMMSS) instead of sequential numbering"
    Write-Host "  -Help               Show this help message"
    Write-Host ""
    Write-Host "Environment variables:"
    Write-Host "  GIT_BRANCH_NAME     Use this exact branch name, bypassing all prefix/suffix generation"
    Write-Host ""
    Write-Host "Configuration:"
    Write-Host "  branch_template     Optional git-config.yml template with {author}, {app}, {number}, {slug}"
    Write-Host "  branch_prefix       Optional shorthand namespace expanded before {number}-{slug}"
    Write-Host ""
    exit 0
}

# -Number is [long], so PowerShell binds "-5" as -5 rather than rejecting it
# the way the bash/Python twins do (`^[0-9]+$`). A negative value would format
# via '{0:000}' to e.g. "-005" and produce a branch name starting with "-",
# which git refuses (refs cannot begin with a dash). Reject it here, before the
# description check, matching the bash twin's parse-time validation order.
if ($Number -lt 0) {
    Write-Error 'Error: --number must be a non-negative integer'
    exit 1
}

if (-not $FeatureDescription -or $FeatureDescription.Count -eq 0) {
    Write-Error "Usage: ./create-new-feature-branch.ps1 [-Json] [-DryRun] [-AllowExistingBranch] [-ShortName <name>] [-Number N] [-Timestamp] <feature description>"
    exit 1
}

$featureDesc = ($FeatureDescription -join ' ').Trim()

if ([string]::IsNullOrWhiteSpace($featureDesc)) {
    Write-Error "Error: Feature description cannot be empty or contain only whitespace"
    exit 1
}

function Get-HighestNumberFromSpecs {
    param([string]$SpecsDir)

    [long]$highest = 0
    if (Test-Path $SpecsDir) {
        Get-ChildItem -Path $SpecsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{3,})-' -and $_.Name -notmatch '^\d{8}-\d{6}-') {
                [long]$num = 0
                if ([long]::TryParse($matches[1], [ref]$num) -and $num -gt $highest) {
                    $highest = $num
                }
            }
        }
    }
    return $highest
}

function Get-HighestNumberFromNames {
    param(
        [string[]]$Names,
        [string]$ScopePrefix = ''
    )

    [long]$highest = 0
    foreach ($name in $Names) {
        if ($ScopePrefix -and -not $name.StartsWith($ScopePrefix, [System.StringComparison]::Ordinal)) {
            continue
        }
        if ($ScopePrefix) {
            $name = $name.Substring($ScopePrefix.Length)
        }
        $name = ($name -split '/')[-1]
        $hasTimestampPrefix = $name -match '^\d{8}-\d{6}-'
        $hasMalformedTimestamp = ($name -match '^\d{7}-\d{6}-') -or ($name -match '^(?:\d{7}|\d{8})-\d{6}$')
        if ($name -match '^(\d{3,})-' -and -not $hasTimestampPrefix -and -not $hasMalformedTimestamp) {
            [long]$num = 0
            if ([long]::TryParse($matches[1], [ref]$num) -and $num -gt $highest) {
                $highest = $num
            }
        }
    }
    return $highest
}

function Get-HighestNumberFromBranches {
    param([string]$ScopePrefix = '')

    try {
        $branches = git branch -a 2>$null
        if ($LASTEXITCODE -eq 0 -and $branches) {
            $cleanNames = $branches | ForEach-Object {
                $_.Trim() -replace '^[+*]?\s+', '' -replace '^remotes/[^/]+/', ''
            }
            return Get-HighestNumberFromNames -Names $cleanNames -ScopePrefix $ScopePrefix
        }
    } catch {
        Write-Verbose "Could not check Git branches: $_"
    }
    return 0
}

function Get-HighestNumberFromRemoteRefs {
    param([string]$ScopePrefix = '')

    [long]$highest = 0
    try {
        $remotes = git remote 2>$null
        if ($remotes) {
            foreach ($remote in $remotes) {
                $env:GIT_TERMINAL_PROMPT = '0'
                $refs = git ls-remote --heads $remote 2>$null
                $env:GIT_TERMINAL_PROMPT = $null
                if ($LASTEXITCODE -eq 0 -and $refs) {
                    $refNames = $refs | ForEach-Object {
                        if ($_ -match 'refs/heads/(.+)$') { $matches[1] }
                    } | Where-Object { $_ }
                    $remoteHighest = Get-HighestNumberFromNames -Names $refNames -ScopePrefix $ScopePrefix
                    if ($remoteHighest -gt $highest) { $highest = $remoteHighest }
                }
            }
        }
    } catch {
        Write-Verbose "Could not query remote refs: $_"
    }
    return $highest
}

function Get-NextBranchNumber {
    param(
        [string]$SpecsDir,
        [switch]$SkipFetch,
        [string]$ScopePrefix = ''
    )

    if ($SkipFetch) {
        $highestBranch = Get-HighestNumberFromBranches -ScopePrefix $ScopePrefix
        $highestRemote = Get-HighestNumberFromRemoteRefs -ScopePrefix $ScopePrefix
        $highestBranch = [Math]::Max($highestBranch, $highestRemote)
    } else {
        try {
            git fetch --all --prune 2>$null | Out-Null
        } catch { }
        $highestBranch = Get-HighestNumberFromBranches -ScopePrefix $ScopePrefix
    }

    $highestSpec = Get-HighestNumberFromSpecs -SpecsDir $SpecsDir
    $maxNum = [Math]::Max($highestBranch, $highestSpec)
    return $maxNum + 1
}

function ConvertTo-CleanBranchName {
    param([string]$Name)
    return $Name.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
}

# ---------------------------------------------------------------------------
# Source common.ps1 from the project's installed scripts.
# Search locations in priority order:
#  1. .specify/scripts/powershell/common.ps1 under the project root
#  2. scripts/powershell/common.ps1 under the project root (source checkout)
#  3. git-common.ps1 next to this script (minimal fallback)
# ---------------------------------------------------------------------------
function Find-ProjectRoot {
    param([string]$StartDir)
    $current = Resolve-Path $StartDir
    while ($true) {
        foreach ($marker in @('.specify', '.git')) {
            if (Test-Path (Join-Path $current $marker)) {
                return $current
            }
        }
        $parent = Split-Path $current -Parent
        if ($parent -eq $current) { return $null }
        $current = $parent
    }
}

$projectRoot = Find-ProjectRoot -StartDir $PSScriptRoot
$commonLoaded = $false

if ($projectRoot) {
    $candidates = @(
        (Join-Path $projectRoot ".specify/scripts/powershell/common.ps1"),
        (Join-Path $projectRoot "scripts/powershell/common.ps1")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            . $candidate
            $commonLoaded = $true
            break
        }
    }
}

if (-not $commonLoaded -and (Test-Path "$PSScriptRoot/git-common.ps1")) {
    . "$PSScriptRoot/git-common.ps1"
    $commonLoaded = $true
}

if (-not $commonLoaded) {
    throw "Unable to locate common script file. Please ensure the Specify core scripts are installed."
}

# SPECIFY_INIT_DIR is resolved (and validated) by the core resolver. If only the
# minimal git-common.ps1 was loaded, or an older core common.ps1 without the
# resolver was loaded, refuse rather than silently falling back to the wrong root.
if ($env:SPECIFY_INIT_DIR -and -not (Get-Command Resolve-SpecifyInitDir -CommandType Function -ErrorAction SilentlyContinue)) {
    throw "SPECIFY_INIT_DIR requires updated Spec Kit core scripts (common.ps1 with Resolve-SpecifyInitDir), which were not found."
}

# Resolve repository root. When the core scripts are present, Get-RepoRoot
# honors SPECIFY_INIT_DIR (the explicit project override for non-interactive /
# CI use) and hard-fails on an invalid value with no silent fallback.
if (Get-Command Get-RepoRoot -ErrorAction SilentlyContinue) {
    $repoRoot = Get-RepoRoot
} elseif ($projectRoot) {
    $repoRoot = $projectRoot
} else {
    throw "Could not determine repository root."
}

# Check if git is available
if (Get-Command Test-HasGit -ErrorAction SilentlyContinue) {
    # Call without parameters for compatibility with core common.ps1 (no -RepoRoot param)
    # and git-common.ps1 (has -RepoRoot param with default).
    $hasGit = Test-HasGit
} else {
    try {
        git -C $repoRoot rev-parse --is-inside-work-tree 2>$null | Out-Null
        $hasGit = ($LASTEXITCODE -eq 0)
    } catch {
        $hasGit = $false
    }
}

Set-Location $repoRoot

$specsDir = Join-Path $repoRoot 'specs'
$configFile = Join-Path $repoRoot ".specify/extensions/git/git-config.yml"

function Read-GitConfigValue {
    param([string]$Key)

    if (-not (Test-Path -LiteralPath $configFile -PathType Leaf)) { return '' }
    $escapedKey = [regex]::Escape($Key)
    foreach ($line in Get-Content -LiteralPath $configFile) {
        if ($line -match "^\s*$escapedKey\s*:\s*(.*)$") {
            $val = ($matches[1] -replace '\s+#.*$', '').Trim()
            $val = $val -replace '^["'']', '' -replace '["'']$', ''
            return $val
        }
    }
    return ''
}

function ConvertTo-BranchToken {
    param(
        [string]$Value,
        [string]$Fallback
    )

    $cleaned = ConvertTo-CleanBranchName -Name $Value
    if ($cleaned) { return $cleaned }
    return $Fallback
}

function Get-GitAuthorToken {
    $author = ''
    if (Get-Command git -ErrorAction SilentlyContinue) {
        try { $author = (git config user.name 2>$null | Out-String).Trim() } catch {}
        if (-not $author) {
            try {
                $email = (git config user.email 2>$null | Out-String).Trim()
                if ($email) { $author = ($email -split '@')[0] }
            } catch {}
        }
    }
    if (-not $author) { $author = if ($env:USER) { $env:USER } elseif ($env:USERNAME) { $env:USERNAME } else { 'unknown' } }
    return ConvertTo-BranchToken -Value $author -Fallback 'unknown'
}

function Get-AppToken {
    return ConvertTo-BranchToken -Value (Split-Path $repoRoot -Leaf) -Fallback 'app'
}

function Resolve-BranchTemplate {
    $template = Read-GitConfigValue -Key 'branch_template'
    if ($template) { return $template }

    $prefix = Read-GitConfigValue -Key 'branch_prefix'
    if (-not $prefix) { return '' }
    if ($prefix.EndsWith('/')) { return "${prefix}{number}-{slug}" }
    return "$prefix/{number}-{slug}"
}

function Expand-BranchTemplate {
    param(
        [string]$Template,
        [string]$FeatureNum,
        [string]$BranchSuffix
    )

    $rendered = $Template.Replace('{author}', $authorToken)
    $rendered = $rendered.Replace('{app}', $appToken)
    $rendered = $rendered.Replace('{number}', $FeatureNum)
    $rendered = $rendered.Replace('{slug}', $BranchSuffix)
    return $rendered
}

function Assert-BranchTemplateValid {
    param([string]$Template)

    if ($Template -and -not $Template.Contains('{number}')) {
        throw "branch_template must include the {number} token so generated branches remain valid feature branches."
    }
    if ($Template) {
        $numberIndex = $Template.IndexOf('{number}', [System.StringComparison]::Ordinal)
        $slugIndex = $Template.IndexOf('{slug}', [System.StringComparison]::Ordinal)
        if ($slugIndex -ge 0 -and $slugIndex -lt $numberIndex) {
            throw "branch_template must not place {slug} before {number}; use {slug} only in the final feature segment."
        }
        $featureSegment = ($Template -split '/')[-1]
        if (-not $featureSegment.StartsWith('{number}-', [System.StringComparison]::Ordinal)) {
            throw "branch_template must put {number}- at the start of the final path segment so generated branches remain valid feature branches."
        }
    }
}

function New-BranchName {
    param(
        [string]$FeatureNum,
        [string]$BranchSuffix
    )

    if ($branchTemplate) {
        return Expand-BranchTemplate -Template $branchTemplate -FeatureNum $FeatureNum -BranchSuffix $BranchSuffix
    }
    return "$FeatureNum-$BranchSuffix"
}

function Get-BranchScopePrefix {
    param(
        [string]$Template,
        [string]$BranchSuffix
    )

    if (-not $Template) { return '' }
    $numberIndex = $Template.IndexOf('{number}', [System.StringComparison]::Ordinal)
    $slugIndex = $Template.IndexOf('{slug}', [System.StringComparison]::Ordinal)
    $indexes = @($numberIndex, $slugIndex) | Where-Object { $_ -ge 0 } | Sort-Object
    if (-not $indexes) { return '' }
    $prefix = $Template.Substring(0, $indexes[0])
    return Expand-BranchTemplate -Template $prefix -FeatureNum '' -BranchSuffix $BranchSuffix
}

function Get-FeatureNumberFromBranchName {
    param([string]$BranchName)

    $featureSegment = ($BranchName -split '/')[-1]
    if ($featureSegment -match '^(\d{8}-\d{6})-') {
        return $matches[1]
    }
    if ($featureSegment -match '^(\d+)-') {
        return $matches[1]
    }
    return $BranchName
}

function Get-Utf8ByteCount {
    param([string]$Value)
    return [System.Text.Encoding]::UTF8.GetByteCount($Value)
}

$authorToken = Get-GitAuthorToken
$appToken = Get-AppToken
$branchTemplate = Resolve-BranchTemplate
Assert-BranchTemplateValid -Template $branchTemplate

function Get-BranchName {
    param([string]$Description)

    $stopWords = @(
        'i', 'a', 'an', 'the', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'with', 'from',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall',
        'this', 'that', 'these', 'those', 'my', 'your', 'our', 'their',
        'want', 'need', 'add', 'get', 'set'
    )

    $cleanName = $Description.ToLower() -replace '[^a-z0-9\s]', ' '
    $words = $cleanName -split '\s+' | Where-Object { $_ }

    $meaningfulWords = @()
    foreach ($word in $words) {
        if ($stopWords -contains $word) { continue }
        if ($word.Length -ge 3) {
            $meaningfulWords += $word
        } elseif ($Description -cmatch "\b$($word.ToUpper())\b") {
            # Case-sensitive (-cmatch) to mirror the bash twin's case-sensitive
            # whole-word acronym match: keep a short word only when its UPPERCASE
            # form appears in the original (an acronym). -match is case-insensitive
            # and would keep every short word.
            $meaningfulWords += $word
        }
    }

    if ($meaningfulWords.Count -gt 0) {
        $maxWords = if ($meaningfulWords.Count -eq 4) { 4 } else { 3 }
        $result = ($meaningfulWords | Select-Object -First $maxWords) -join '-'
        return $result
    } else {
        $result = ConvertTo-CleanBranchName -Name $Description
        $fallbackWords = ($result -split '-') | Where-Object { $_ } | Select-Object -First 3
        return [string]::Join('-', $fallbackWords)
    }
}

# Check for GIT_BRANCH_NAME env var override (exact branch name, no prefix/suffix)
if ($env:GIT_BRANCH_NAME) {
    $branchName = $env:GIT_BRANCH_NAME
    # Check 244-byte limit (UTF-8) for override names
    $branchNameUtf8ByteCount = Get-Utf8ByteCount -Value $branchName
    if ($branchNameUtf8ByteCount -gt 244) {
        throw "GIT_BRANCH_NAME must be 244 bytes or fewer in UTF-8. Provided value is $branchNameUtf8ByteCount bytes; please supply a shorter override branch name."
    }
    $featureNum = Get-FeatureNumberFromBranchName -BranchName $branchName
} else {
    if ($ShortName) {
        $branchSuffix = ConvertTo-CleanBranchName -Name $ShortName
    } else {
        $branchSuffix = Get-BranchName -Description $featureDesc
    }

    # Warn if -Number and -Timestamp are both specified. Use ContainsKey (not
    # `-ne 0`) so an explicit `-Number 0` is also detected, matching the bash twin's
    # `[ -n "$BRANCH_NUMBER" ]` check.
    if ($Timestamp -and $PSBoundParameters.ContainsKey('Number')) {
        Write-Warning "[specify] Warning: -Number is ignored when -Timestamp is used"
        $Number = 0
    }

    if ($Timestamp) {
        $featureNum = Get-Date -Format 'yyyyMMdd-HHmmss'
        $branchName = New-BranchName -FeatureNum $featureNum -BranchSuffix $branchSuffix
    } else {
        $branchScopePrefix = Get-BranchScopePrefix -Template $branchTemplate -BranchSuffix $branchSuffix
        # Auto-detect the next number only when -Number was not supplied; an
        # explicit value (including 0) is honored, matching the bash twin's
        # `[ -z "$BRANCH_NUMBER" ]` check.
        if (-not $PSBoundParameters.ContainsKey('Number')) {
            if ($DryRun -and $hasGit) {
                $Number = Get-NextBranchNumber -SpecsDir $specsDir -SkipFetch -ScopePrefix $branchScopePrefix
            } elseif ($DryRun) {
                $Number = (Get-HighestNumberFromSpecs -SpecsDir $specsDir) + 1
            } elseif ($hasGit) {
                $Number = Get-NextBranchNumber -SpecsDir $specsDir -ScopePrefix $branchScopePrefix
            } else {
                $Number = (Get-HighestNumberFromSpecs -SpecsDir $specsDir) + 1
            }
        }

        $featureNum = ('{0:000}' -f $Number)
        $branchName = New-BranchName -FeatureNum $featureNum -BranchSuffix $branchSuffix
    }
}

$maxBranchLength = 244
if ((Get-Utf8ByteCount -Value $branchName) -gt $maxBranchLength) {
    $originalBranchName = $branchName
    $truncatedSuffix = $branchSuffix
    while ((Get-Utf8ByteCount -Value $branchName) -gt $maxBranchLength -and $truncatedSuffix.Length -gt 0) {
        $truncatedSuffix = $truncatedSuffix.Substring(0, $truncatedSuffix.Length - 1) -replace '-$', ''
        $branchName = New-BranchName -FeatureNum $featureNum -BranchSuffix $truncatedSuffix
    }
    if ((Get-Utf8ByteCount -Value $branchName) -gt $maxBranchLength) {
        throw "Branch template prefix exceeds GitHub's 244-byte branch name limit."
    }

    Write-Warning "[specify] Branch name exceeded GitHub's 244-byte limit"
    Write-Warning "[specify] Original: $originalBranchName ($(Get-Utf8ByteCount -Value $originalBranchName) bytes)"
    Write-Warning "[specify] Truncated to: $branchName ($(Get-Utf8ByteCount -Value $branchName) bytes)"
}

if (-not $DryRun) {
    if ($hasGit) {
        $branchCreated = $false
        $branchCreateError = ''
        try {
            $branchCreateError = git checkout -q -b $branchName 2>&1 | Out-String
            if ($LASTEXITCODE -eq 0) {
                $branchCreated = $true
            }
        } catch {
            $branchCreateError = $_.Exception.Message
        }

        if (-not $branchCreated) {
            $currentBranch = ''
            try { $currentBranch = (git rev-parse --abbrev-ref HEAD 2>$null).Trim() } catch {}
            $existingBranch = git branch --list $branchName 2>$null
            if ($existingBranch) {
                if ($AllowExistingBranch) {
                    if ($currentBranch -eq $branchName) {
                        # Already on the target branch
                    } else {
                        $switchBranchError = git checkout -q $branchName 2>&1 | Out-String
                        if ($LASTEXITCODE -ne 0) {
                            if ($switchBranchError) {
                                Write-Error "Error: Branch '$branchName' exists but could not be checked out.`n$($switchBranchError.Trim())"
                            } else {
                                Write-Error "Error: Branch '$branchName' exists but could not be checked out. Resolve any uncommitted changes or conflicts and try again."
                            }
                            exit 1
                        }
                    }
                } elseif ($Timestamp) {
                    Write-Error "Error: Branch '$branchName' already exists. Rerun to get a new timestamp or use a different -ShortName."
                    exit 1
                } else {
                    Write-Error "Error: Branch '$branchName' already exists. Please use a different feature name or specify a different number with -Number."
                    exit 1
                }
            } else {
                if ($branchCreateError) {
                    Write-Error "Error: Failed to create git branch '$branchName'.`n$($branchCreateError.Trim())"
                } else {
                    Write-Error "Error: Failed to create git branch '$branchName'. Please check your git configuration and try again."
                }
                exit 1
            }
        }
    } else {
        if ($Json) {
            [Console]::Error.WriteLine("[specify] Warning: Git repository not detected; skipped branch creation for $branchName")
        } else {
            Write-Warning "[specify] Warning: Git repository not detected; skipped branch creation for $branchName"
        }
    }

    $env:SPECIFY_FEATURE = $branchName
}

if ($Json) {
    $obj = [PSCustomObject]@{
        BRANCH_NAME = $branchName
        FEATURE_NUM = $featureNum
    }
    # $hasGit is computed for branch-creation logic only; it is intentionally not
    # emitted so this output contract matches the bash twin: BRANCH_NAME and
    # FEATURE_NUM, plus DRY_RUN (added just below) on dry runs.
    if ($DryRun) {
        $obj | Add-Member -NotePropertyName 'DRY_RUN' -NotePropertyValue $true
    }
    $obj | ConvertTo-Json -Compress
} else {
    Write-Output "BRANCH_NAME: $branchName"
    Write-Output "FEATURE_NUM: $featureNum"
    if (-not $DryRun) {
        Write-Output "SPECIFY_FEATURE environment variable set to: $branchName"
    }
}
