#!/usr/bin/env pwsh
# Git extension: initialize-repo.ps1
# Initialize a Git repository with an initial commit.
# Customizable — replace this script to add .gitignore templates,
# default branch config, git-flow, LFS, signing, etc.
$ErrorActionPreference = 'Stop'

# Find project root
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

$repoRoot = Find-ProjectRoot -StartDir $PSScriptRoot
if (-not $repoRoot) { $repoRoot = Get-Location }
Set-Location $repoRoot

# Read commit message from extension config, fall back to default
$commitMsg = "Initial commit from Specify template"
$configFile = Join-Path $repoRoot ".specify/extensions/git/git-config.yml"
if (Test-Path $configFile) {
    foreach ($line in Get-Content $configFile) {
        if ($line -match '^init_commit_message:\s*(.+)$') {
            $val = $matches[1].Trim() -replace '^["'']' -replace '["'']$'
            if ($val) { $commitMsg = $val }
            break
        }
    }
}

# Check if git is available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Warning "[specify] Warning: Git not found; skipped repository initialization"
    exit 0
}

# Check if already a git repo
try {
    git rev-parse --is-inside-work-tree 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Warning "[specify] Git repository already initialized; skipping"
        exit 0
    }
} catch { }

# Initialize
try {
    $out = git init -q 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { throw "git init failed: $out" }
    $out = git add . 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { throw "git add failed: $out" }
    $out = git commit -q -m $commitMsg 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { throw "git commit failed: $out" }
} catch {
    Write-Warning "[specify] Error: $_"
    exit 1
}

Write-Host "✓ Git repository initialized"
