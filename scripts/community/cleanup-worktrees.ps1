[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$RepoRoot = '',
    [string]$NamePattern = '^spec-kit-pr-',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

if ($RepoRoot -eq '') {
    $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
}

$repoRootPath = (Resolve-Path -LiteralPath $RepoRoot).Path
$parentPath = (Resolve-Path -LiteralPath (Join-Path $repoRootPath '..')).Path

$worktreeOutput = git -C $repoRootPath worktree list --porcelain
$paths = @()
foreach ($line in $worktreeOutput) {
    if ($line -match '^worktree\s+(.+)$') {
        $paths += $Matches[1]
    }
}

foreach ($path in $paths) {
    $fullPath = [System.IO.Path]::GetFullPath($path)
    $name = Split-Path -Leaf $fullPath

    if ($fullPath -ieq $repoRootPath) {
        continue
    }
    if ($name -notmatch $NamePattern) {
        continue
    }
    if (-not $fullPath.StartsWith($parentPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove worktree outside repository parent: $fullPath"
    }

    $dirtyLines = @(git -C $fullPath status --porcelain)
    if ($dirtyLines.Count -gt 0 -and -not $Force) {
        Write-Warning "Skipping dirty worktree: $fullPath"
        continue
    }

    if ($PSCmdlet.ShouldProcess($fullPath, 'git worktree remove')) {
        if ($Force) {
            git -C $repoRootPath worktree remove --force $fullPath
        } else {
            git -C $repoRootPath worktree remove $fullPath
        }
    }
}

git -C $repoRootPath worktree prune
git -C $repoRootPath worktree list
