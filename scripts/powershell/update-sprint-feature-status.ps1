#!/usr/bin/env pwsh

param(
    [Parameter(Mandatory=$true)]
    [string]$Status
)

$ErrorActionPreference = "Stop"

# Function to find repository root
function Find-RepoRoot {
    param([string]$StartDir)
    
    $dir = $StartDir
    while ($dir -ne [System.IO.Path]::GetPathRoot($dir)) {
        if ((Test-Path (Join-Path $dir ".git")) -or (Test-Path (Join-Path $dir ".specify"))) {
            return $dir
        }
        $dir = Split-Path -Parent $dir
    }
    return $null
}

# Get repo root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

try {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    if (-not $repoRoot) { throw }
} catch {
    $repoRoot = Find-RepoRoot $scriptDir
    if (-not $repoRoot) {
        Write-Error "Could not determine repository root."
        exit 1
    }
}

# Get feature ID from current branch or SPECIFY_FEATURE env var
$featureId = ""
if ($env:SPECIFY_FEATURE) {
    $featureId = $env:SPECIFY_FEATURE
} else {
    try {
        $branch = git rev-parse --abbrev-ref HEAD 2>$null
        if ($branch -match '^\d{3}-') {
            $featureId = $branch
        }
    } catch {}
}

if (-not $featureId) {
    Write-Error "Could not determine feature ID from branch or SPECIFY_FEATURE env var"
    exit 1
}

# Update status in active sprint files
$activeSprint = Join-Path $repoRoot ".specify/sprints/active/sprint.md"
$backlogFile = Join-Path $repoRoot ".specify/sprints/active/backlog.md"

if (Test-Path $activeSprint) {
    $content = Get-Content $activeSprint
    $content = $content -replace "^(\| $featureId \|[^|]*\|[^|]*\|) [^|]* (\|.*)$", "`$1 $Status `$2"
    $content | Set-Content $activeSprint
}

if (Test-Path $backlogFile) {
    $content = Get-Content $backlogFile
    $content = $content -replace "^(\| $featureId \|[^|]*\|[^|]*\|) [^|]* (\|.*)$", "`$1 $Status `$2"
    $content | Set-Content $backlogFile
}

Write-Host "✅ Updated $featureId status to: $Status" -ForegroundColor Green
