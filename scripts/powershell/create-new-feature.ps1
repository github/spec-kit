#!/usr/bin/env pwsh
# Create a new feature
[CmdletBinding()]
param(
    [switch]$Json,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$FeatureDescription
)
$ErrorActionPreference = 'Stop'

if (-not $FeatureDescription -or $FeatureDescription.Count -eq 0) {
    Write-Error "Usage: ./create-new-feature.ps1 [-Json] <feature description>"
    exit 1
}
$featureDesc = ($FeatureDescription -join ' ').Trim()

# Resolve repository root. Prefer git information when available, but fall back
# to searching for repository markers so the workflow still functions in repositories that
# were initialised with --no-git.
function Find-RepositoryRoot {
    param(
        [string]$StartDir,
    [string[]]$Markers = @('.git', '.specs', '.specify')
    )
    $current = Resolve-Path $StartDir
    while ($true) {
        foreach ($marker in $Markers) {
            if (Test-Path (Join-Path $current $marker)) {
                # If we stopped inside the .specs folder, return its parent
                if ([IO.Path]::GetFileName($current) -eq '.specs') {
                    return ([IO.Directory]::GetParent($current).FullName)
                }
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
        throw "Git not available"
    }
} catch {
    $repoRoot = $fallbackRoot
    $hasGit = $false
}

Set-Location $repoRoot
. "$PSScriptRoot/common.ps1"

$specsRoot = Join-Path $repoRoot '.specs'
New-Item -ItemType Directory -Path $specsRoot -Force | Out-Null
$specifyRoot = Join-Path $specsRoot '.specify'
New-Item -ItemType Directory -Path $specifyRoot -Force | Out-Null
# Load layout and determine parent directory using a dummy branch
$layout = & (Join-Path $PSScriptRoot 'read-layout.ps1')
$dummy = '000-placeholder'
$featureDirDummy = Get-FeatureDir -RepoRoot $repoRoot -Branch $dummy
$parentDir = Split-Path $featureDirDummy -Parent

$highest = 0
if (Test-Path $parentDir) {
    Get-ChildItem -Path $parentDir -Directory | ForEach-Object {
        if ($_.Name -match '^(\d{3})') {
            $num = [int]$matches[1]
            if ($num -gt $highest) { $highest = $num }
        }
    }
}
$next = $highest + 1
$featureNum = ('{0:000}' -f $next)

$branchName = $featureDesc.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
$words = ($branchName -split '-') | Where-Object { $_ } | Select-Object -First 3
$branchName = "$featureNum-$([string]::Join('-', $words))"

if ($hasGit) {
    try {
        git checkout -b $branchName | Out-Null
    } catch {
        Write-Warning "Failed to create git branch: $branchName"
    }
} else {
    Write-Warning "[specify] Warning: Git repository not detected; skipped branch creation for $branchName"
}

# Recompute featureDir now that we have branch
$featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $branchName
New-Item -ItemType Directory -Path $featureDir -Force | Out-Null

$specFile = Join-Path $featureDir $layout.FILES.FPRD
# Resolve template path via resolver (assets override if present)
$resolvedTemplate = Join-Path $specifyRoot 'templates/spec-template.md'
$resolver = Join-Path $PSScriptRoot 'resolve-template.ps1'
try {
    if (Test-Path $resolver) {
        $json = & $resolver -Json spec 2>$null | ConvertFrom-Json
        if ($json -and $json.TEMPLATE_PATH) { $resolvedTemplate = $json.TEMPLATE_PATH }
    }
} catch { }
if (Test-Path $resolvedTemplate) { 
    Copy-Item $resolvedTemplate $specFile -Force 
} else { 
    New-Item -ItemType File -Path $specFile | Out-Null 
}

# Optional legacy stub for spec.md if enabled
if ($layout.COMPAT.WRITE_STUB_SPEC) {
    $stub = $layout.COMPAT.STUB_NAME
    if ($stub -and ($stub -ne [IO.Path]::GetFileName($specFile))) {
        "# Legacy spec stub`n`nThis repository uses a declarative layout. The canonical feature PRD lives at:`n`n- $([IO.Path]::GetFileName($specFile))`n" | Out-File -LiteralPath (Join-Path $featureDir $stub) -Encoding utf8 -Force
    }
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
