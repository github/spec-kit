#!/usr/bin/env pwsh
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"
$repoRoot = Get-RepoRoot
$cfgPath = Join-Path $repoRoot '.specs/.specify/layout.yaml'

# Defaults
$cfg = [ordered]@{
  VERSION = 1
  SPEC_ROOTS = @('specs', '.specs/.specify/specs')
  FOLDER_STRATEGY = 'epic'
  FILES = [ordered]@{
    FPRD='fprd.md'; PPRD='pprd.md'; REQUIREMENTS='requirements.md'; DESIGN='design.md'; TASKS='tasks.md'; RESEARCH='research.md'; QUICKSTART='quickstart.md'; TRACEABILITY_INDEX='traceability_index.md'; CONTRACTS_DIR='contracts'; PROGRESS_LOG='progress_log.md'; PARKING_LOT='parking_lot.md'; INDEX='index.yaml'
  }
  COMPAT = [ordered]@{ WRITE_STUB_SPEC=$true; STUB_NAME='spec.md' }
  CATALOG_PATH = 'specs/catalog.yaml'
}

if (Test-Path $cfgPath) {
  $section = ''
  Get-Content -LiteralPath $cfgPath | ForEach-Object {
    $line = ($_ -replace '#.*$','').TrimEnd()
    if (-not $line.Trim()) { return }
    if ($line -match '^version:\s*(\d+)') { $cfg.VERSION = [int]$matches[1]; return }
    if ($line -match '^spec_roots:') { $section = 'spec_roots'; return }
    if ($line -match '^files:') { $section = 'files'; return }
    if ($line -match '^compat:') { $section = 'compat'; return }
    if ($line -match '^catalog:') { $section = 'catalog'; return }
    if ($line -match '^folder_strategy:\s*"?([A-Za-z0-9_-]+)"?') { $cfg.FOLDER_STRATEGY = $matches[1]; return }

    switch ($section) {
      'spec_roots' {
        if ($line -match '^-\s*"?([^"']+)"?') { $cfg.SPEC_ROOTS += $matches[1] }
      }
      'files' {
        if ($line -match 'fprd:\s*"?([^"']+)"?') { $cfg.FILES.FPRD = $matches[1] }
        if ($line -match 'pprd:\s*"?([^"']+)"?') { $cfg.FILES.PPRD = $matches[1] }
        if ($line -match 'requirements:\s*"?([^"']+)"?') { $cfg.FILES.REQUIREMENTS = $matches[1] }
        if ($line -match 'design:\s*"?([^"']+)"?') { $cfg.FILES.DESIGN = $matches[1] }
        if ($line -match 'tasks:\s*"?([^"']+)"?') { $cfg.FILES.TASKS = $matches[1] }
        if ($line -match 'research:\s*"?([^"']+)"?') { $cfg.FILES.RESEARCH = $matches[1] }
        if ($line -match 'quickstart:\s*"?([^"']+)"?') { $cfg.FILES.QUICKSTART = $matches[1] }
        if ($line -match 'traceability_index:\s*"?([^"']+)"?') { $cfg.FILES.TRACEABILITY_INDEX = $matches[1] }
        if ($line -match 'contracts_dir:\s*"?([^"']+)"?') { $cfg.FILES.CONTRACTS_DIR = $matches[1] }
        if ($line -match 'progress_log:\s*"?([^"']+)"?') { $cfg.FILES.PROGRESS_LOG = $matches[1] }
        if ($line -match 'parking_lot:\s*"?([^"']+)"?') { $cfg.FILES.PARKING_LOT = $matches[1] }
        if ($line -match 'index:\s*"?([^"']+)"?') { $cfg.FILES.INDEX = $matches[1] }
      }
      'compat' {
        if ($line -match 'write_redirect_stub_spec_md:\s*(true|false)') { $cfg.COMPAT.WRITE_STUB_SPEC = ($matches[1] -eq 'true') }
        if ($line -match 'stub_name:\s*"?([^"']+)"?') { $cfg.COMPAT.STUB_NAME = $matches[1] }
      }
      'catalog' {
        if ($line -match 'path:\s*"?([^"']+)"?') { $cfg.CATALOG_PATH = $matches[1] }
      }
    }
  }
}

$cfg

