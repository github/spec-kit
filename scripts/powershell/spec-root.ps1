#!/usr/bin/env pwsh
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"
$repo = Get-RepoRoot
$layout = & (Join-Path $PSScriptRoot 'read-layout.ps1')

$roots = @('specs', '.specs/.specify/specs')
if ($layout -and $layout.SPEC_ROOTS) { $roots = $layout.SPEC_ROOTS }

$chosen = $null
foreach ($r in $roots) {
  $cand = Join-Path $repo $r
  if (Test-Path $cand -PathType Container) { $chosen = $cand; break }
}
if (-not $chosen) {
  $chosen = Join-Path $repo $roots[0]
  New-Item -ItemType Directory -Path $chosen -Force | Out-Null
}

Write-Output $chosen

