[CmdletBinding()]
param(
    [string]$RepoRoot = '',
    [string]$Branch = '',
    [string]$PrBodyFile = '',
    [switch]$ShowWarnings
)

$ErrorActionPreference = 'Stop'

if ($RepoRoot -eq '') {
    $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
}

$script = Join-Path $PSScriptRoot 'validate_integration.py'
$argsList = @($script, '--repo-root', $RepoRoot)

if ($Branch -ne '') {
    $argsList += @('--branch', $Branch)
}

if ($PrBodyFile -ne '') {
    $argsList += @('--pr-body-file', $PrBodyFile)
}

if ($ShowWarnings) {
    $argsList += '--show-warnings'
}

python @argsList
