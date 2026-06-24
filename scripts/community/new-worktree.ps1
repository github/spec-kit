[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Branch,

    [string]$WorktreeName = '',

    [string]$RepoRoot = '',

    [string]$Base = 'main'
)

$ErrorActionPreference = 'Stop'

if ($RepoRoot -eq '') {
    $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
}

if ($Branch -notmatch '^community/(?:\d+-)?[a-z0-9][a-z0-9._-]*$') {
    throw "Community integration branches must match community/(<issue>-)?<kebab-slug>: $Branch"
}

$repoRootPath = (Resolve-Path -LiteralPath $RepoRoot).Path
$parentPath = (Resolve-Path -LiteralPath (Join-Path $repoRootPath '..')).Path

if ($WorktreeName -eq '') {
    $WorktreeName = 'spec-kit-pr-' + (($Branch -replace '^community/', '') -replace '[^a-zA-Z0-9._-]', '-')
}

$targetPath = Join-Path $parentPath $WorktreeName
if (Test-Path -LiteralPath $targetPath) {
    throw "Worktree target already exists: $targetPath"
}

$resolvedParent = [System.IO.Path]::GetFullPath($parentPath)
$resolvedTarget = [System.IO.Path]::GetFullPath($targetPath)
if (-not $resolvedTarget.StartsWith($resolvedParent, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to create a worktree outside the repository parent: $resolvedTarget"
}

git -C $repoRootPath fetch --all --prune
$existingBranch = git -C $repoRootPath branch --list $Branch

if ($existingBranch) {
    git -C $repoRootPath worktree add $targetPath $Branch
} else {
    git -C $repoRootPath worktree add -b $Branch $targetPath $Base
}

Write-Host "Created community integration worktree:"
Write-Host "  Branch: $Branch"
Write-Host "  Path:   $targetPath"
