#!/usr/bin/env pwsh
# Create a new issue
[CmdletBinding()]
param(
    [switch]$Json,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$IssueDescription
)
$ErrorActionPreference = 'Stop'

if (-not $IssueDescription -or $IssueDescription.Count -eq 0) {
    Write-Error "Usage: ./create-issue.ps1 [-Json] <issue description>"
    exit 1
}
$issueDesc = ($IssueDescription -join ' ').Trim()

# Resolve repository root. Prefer git information when available, but fall back
# to searching for repository markers so the workflow still functions in repositories that
# were initialised with --no-git.
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
        $repoRoot = $fallbackRoot
        $hasGit = $false
    }
} catch {
    $repoRoot = $fallbackRoot
    $hasGit = $false
}

Set-Location $repoRoot

$issuesDir = Join-Path $repoRoot "issues"
if (-not (Test-Path $issuesDir)) {
    New-Item -ItemType Directory -Path $issuesDir -Force | Out-Null
}

# Find the highest issue number
$highest = 0
if (Test-Path $issuesDir) {
    Get-ChildItem -Path $issuesDir -Directory | ForEach-Object {
        $dirname = $_.Name
        if ($dirname -match '^(\d+)') {
            $number = [int]$matches[1]
            if ($number -gt $highest) {
                $highest = $number
            }
        }
    }
}

$next = $highest + 1
$issueNum = "{0:D3}" -f $next

# Create branch name from issue description
$issueName = $issueDesc.ToLower() -replace '[^a-z0-9]', '-' -replace '-+', '-' -replace '^-|-$', ''
$words = ($issueName -split '-' | Where-Object { $_ -ne '' } | Select-Object -First 3) -join '-'
$issueName = "$issueNum-$words"

if ($hasGit) {
    git checkout -b $issueName
} else {
    Write-Warning "[specify] Warning: Git repository not detected; skipped branch creation for $issueName"
}

$issueDir = Join-Path $issuesDir $issueName
if (-not (Test-Path $issueDir)) {
    New-Item -ItemType Directory -Path $issueDir -Force | Out-Null
}

$template = Join-Path $repoRoot "templates" "issue-template.md"
$issueSpec = Join-Path $issueDir "issue.md"
if (Test-Path $template) {
    Copy-Item $template $issueSpec
} else {
    New-Item -ItemType File -Path $issueSpec -Force | Out-Null
}

# Set the SPECIFY_FEATURE environment variable for the current session
$env:SPECIFY_FEATURE = $issueName

if ($Json) {
    $result = @{
        ISSUE_NUM = $issueNum
        ISSUE_DIR = $issueDir
        ISSUE_SPEC = $issueSpec
    } | ConvertTo-Json -Compress
    Write-Output $result
} else {
    Write-Output "ISSUE_NUM: $issueNum"
    Write-Output "ISSUE_DIR: $issueDir"
    Write-Output "ISSUE_SPEC: $issueSpec"
    Write-Output "SPECIFY_FEATURE environment variable set to: $issueName"
}
