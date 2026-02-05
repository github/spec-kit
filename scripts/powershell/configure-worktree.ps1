#!/usr/bin/env pwsh
# Configure git worktree preferences for Spec Kit

[CmdletBinding()]
param(
    [ValidateSet("branch", "worktree")]
    [string]$Mode,

    [ValidateSet("nested", "sibling", "custom")]
    [string]$Strategy,

    [string]$Path,

    [switch]$Show,

    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Import common functions
. (Join-Path $PSScriptRoot "common.ps1")

function Show-Help {
    Write-Host @"
Usage: configure-worktree.ps1 [OPTIONS]

Configure git worktree preferences for Spec Kit feature creation.

Options:
  -Mode <branch|worktree>           Set git mode (default: branch)
  -Strategy <nested|sibling|custom> Set worktree placement strategy
  -Path <path>                      Custom base path (required if strategy is 'custom')
  -Show                             Display current configuration
  -Help                             Show this help message

Strategies:
  nested   - Worktrees in .worktrees/ directory inside the repository
  sibling  - Worktrees as sibling directories to the repository
  custom   - Worktrees in a custom directory (requires -Path)

Examples:
  # Enable worktree mode with nested strategy
  ./configure-worktree.ps1 -Mode worktree -Strategy nested

  # Enable worktree mode with sibling strategy
  ./configure-worktree.ps1 -Mode worktree -Strategy sibling

  # Enable worktree mode with custom path
  ./configure-worktree.ps1 -Mode worktree -Strategy custom -Path /tmp/worktrees

  # Switch back to branch mode
  ./configure-worktree.ps1 -Mode branch

  # Show current configuration
  ./configure-worktree.ps1 -Show
"@
}

# Show help if requested
if ($Help) {
    Show-Help
    exit 0
}

# Get repository root and config file path
$repoRoot = Get-RepoRoot
$configFile = Join-Path $repoRoot ".specify/config.json"

# Show current configuration
if ($Show) {
    if (-not (Test-Path $configFile)) {
        Write-Host "No configuration file found. Using defaults:"
        Write-Host "  git_mode: branch"
        Write-Host "  worktree_strategy: sibling"
        Write-Host "  worktree_custom_path: (none)"
    }
    else {
        Write-Host "Current configuration ($configFile):"
        Write-Host "  git_mode: $(Get-ConfigValue -Key 'git_mode' -Default 'branch')"
        Write-Host "  worktree_strategy: $(Get-ConfigValue -Key 'worktree_strategy' -Default 'sibling')"
        $customPath = Get-ConfigValue -Key 'worktree_custom_path' -Default ''
        if ($customPath) {
            Write-Host "  worktree_custom_path: $customPath"
        }
        else {
            Write-Host "  worktree_custom_path: (none)"
        }
    }
    exit 0
}

# If no options provided, show help
if (-not $Mode -and -not $Strategy -and -not $Path) {
    Show-Help
    exit 0
}

# Validate custom path requirements
if ($Strategy -eq "custom" -and -not $Path) {
    Write-Error "Error: -Path is required when strategy is 'custom'"
    exit 1
}

# Validate custom path is absolute
if ($Path) {
    if (-not [System.IO.Path]::IsPathRooted($Path)) {
        Write-Error "Error: -Path must be an absolute path (got: $Path)"
        exit 1
    }
    # Check if parent directory exists and is writable
    $parentPath = Split-Path $Path -Parent
    if (-not (Test-Path $parentPath)) {
        Write-Error "Error: Parent directory does not exist: $parentPath"
        exit 1
    }
    # Test writability by attempting to create a temp file
    $testFile = Join-Path $parentPath ".specify-write-test-$(Get-Random)"
    try {
        New-Item -ItemType File -Path $testFile -Force -ErrorAction Stop | Out-Null
    }
    catch {
        Write-Error "Error: Parent directory is not writable: $parentPath"
        exit 1
    }
    finally {
        Remove-Item $testFile -Force -ErrorAction SilentlyContinue
    }
}

# Ensure .specify directory exists
$specifyDir = Join-Path $repoRoot ".specify"
if (-not (Test-Path $specifyDir)) {
    New-Item -ItemType Directory -Path $specifyDir -Force | Out-Null
}

# Read existing config or create empty object
$config = @{}
if (Test-Path $configFile) {
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json -AsHashtable
    }
    catch {
        Write-Verbose "Could not parse existing config, starting fresh"
        $config = @{}
    }
}

# Update configuration
if ($Mode) {
    $config['git_mode'] = $Mode
}

if ($Strategy) {
    $config['worktree_strategy'] = $Strategy
}

if ($Path) {
    $config['worktree_custom_path'] = $Path
}
elseif ($Strategy -eq "nested" -or $Strategy -eq "sibling") {
    # Clear custom path when switching to non-custom strategy
    $config['worktree_custom_path'] = ""
}

# Write configuration
$config | ConvertTo-Json | Set-Content $configFile -Encoding UTF8

Write-Host "Configuration updated:"
Write-Host "  git_mode: $(Get-ConfigValue -Key 'git_mode' -Default 'branch')"
Write-Host "  worktree_strategy: $(Get-ConfigValue -Key 'worktree_strategy' -Default 'sibling')"
$customPath = Get-ConfigValue -Key 'worktree_custom_path' -Default ''
if ($customPath) {
    Write-Host "  worktree_custom_path: $customPath"
}
