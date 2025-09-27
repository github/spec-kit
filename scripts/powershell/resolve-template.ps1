#!/usr/bin/env pwsh
[CmdletBinding()]
param(
  [switch]$Json,
  [Parameter(Mandatory=$true, Position=0)]
  [string]$Key
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"
$paths = Get-FeaturePathsEnv  # Provides REPO_ROOT; does not require feature branch

$templatesDir = Join-Path $paths.REPO_ROOT '.specs/.specify/templates'
$assetsDir = Join-Path $templatesDir 'assets'

$resolved = $null
if (Test-Path $assetsDir) {
  $needle = "$Key-template.md"
  $match = Get-ChildItem -Path $assetsDir -File | Where-Object { $_.Name -ieq $needle } | Select-Object -First 1
  if ($match) { $resolved = $match.FullName }
}

if (-not $resolved) {
  $fallback = Join-Path $templatesDir "$Key-template.md"
  if (Test-Path $fallback) {
    $resolved = $fallback
  } else {
    Write-Error "No template found for key '$Key'. Looked for assets/$Key-template.md and $fallback"
  }
}

if ($Json) {
  [PSCustomObject]@{ TEMPLATE_PATH = $resolved } | ConvertTo-Json -Compress
} else {
  Write-Output $resolved
}

