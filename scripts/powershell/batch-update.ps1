#!/usr/bin/env pwsh
<#
.SYNOPSIS
Batch update script for installing/updating specify-cli and running specify update in multiple directories

.DESCRIPTION
This script automates two main tasks:
1. Installs/updates the specify-cli tool from GitHub
2. Runs 'specify update' command in configured project directories

.PARAMETER ConfigFile
Optional path to configuration file containing project directories list.
Defaults to 'project-dirs.conf' in the same directory as the script.

.PARAMETER Force
Force reinstall of specify-cli tool even if already installed.

.EXAMPLE
./batch-update.ps1
Runs with default configuration file

.EXAMPLE
./batch-update.ps1 -ConfigFile "C:\my-config.txt" -Force
Runs with custom config file and forces reinstall

.NOTES
Configuration file should contain one project directory path per line.
Lines starting with '#' are treated as comments and ignored.
#>
param(
    [Parameter(Position=0)]
    [string]$ConfigFile = "",
    
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

# Import common helpers
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir 'common.ps1')

function Write-Info { 
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
    Write-Host "INFO: $Message" 
}

function Write-Success { 
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
    Write-Host "$([char]0x2713) $Message" -ForegroundColor Green
}

function Write-WarningMsg { 
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
    Write-Warning $Message 
}

function Write-Err { 
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Test-CommandExists {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Command
    )
    
    try {
        $cmd = Get-Command $Command -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Install-SpecifyCLI {
    param(
        [switch]$ForceInstall
    )
    
    Write-Info "Installing/updating specify-cli..."
    
    # Check if uv is installed
    if (-not (Test-CommandExists "uv")) {
        Write-Err "uv is not installed. Please install uv first: https://docs.astral.sh/uv/"
        return $false
    }
    
    try {
        $installArgs = @("tool", "install", "specify-cli", "--from", "git+https://github.com/rj-wangbin6/spec-kit.git")
        
        if ($ForceInstall) {
            $installArgs += "--force"
        }
        
        & uv @installArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Successfully installed/updated specify-cli"
            return $true
        } else {
            Write-Err "Failed to install/update specify-cli"
            return $false
        }
    }
    catch {
        Write-Err "Exception occurred while installing specify-cli: $_"
        return $false
    }
}

function Get-ProjectDirectories {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ConfigFilePath
    )
    
    if (-not (Test-Path $ConfigFilePath)) {
        Write-Err "Configuration file not found: $ConfigFilePath"
        Write-Info "Please create a configuration file with project directory paths, one per line."
        Write-Info "Example config file content:"
        Write-Info "  # Project directories"
        Write-Info "  C:\Projects\project1"
        Write-Info "  C:\Projects\project2"
        Write-Info "  D:\Dev\another-project"
        return @()
    }
    
    try {
        $directories = Get-Content -Path $ConfigFilePath | Where-Object {
            $_.Trim() -ne "" -and -not $_.StartsWith("#")
        } | ForEach-Object {
            $_.Trim()
        }
        
        Write-Info "Found $($directories.Count) project directories in config file"
        return $directories
    }
    catch {
        Write-Err "Error reading configuration file: $_"
        return @()
    }
}

function Invoke-SpecifyUpdate {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ProjectDirectory
    )
    
    Write-Info "Running 'specify init --here --force --ai copilot --script ps' in: $ProjectDirectory"
    
    if (-not (Test-Path $ProjectDirectory)) {
        Write-WarningMsg "Directory does not exist: $ProjectDirectory"
        return $false
    }
    
    try {
        Push-Location $ProjectDirectory
        
        if (-not (Test-CommandExists "specify")) {
            Write-Err "specify command not found. Make sure specify-cli is properly installed."
            Pop-Location
            return $false
        }
        
        & specify init --here --force --ai copilot --script ps
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Successfully ran specify init --here --force --ai copilot --script ps in $ProjectDirectory"
            Pop-Location
            return $true
        } else {
            Write-Err "Failed to run specify init --here --force --ai copilot --script ps in $ProjectDirectory"
            Pop-Location
            return $false
        }
    }
    catch {
        Write-Err "Exception occurred while running specify init --here --force --ai copilot --script ps in $ProjectDirectory : $_"
        Pop-Location
        return $false
    }
}

function Main {
    Write-Info "=== Batch Update Script for specify-cli ==="
    
    # Determine config file path
    if (-not $ConfigFile) {
        $ConfigFile = Join-Path $ScriptDir "project-dirs.conf"
    }
    
    Write-Info "Using config file: $ConfigFile"
    
    # Install/update specify-cli
    if (-not (Install-SpecifyCLI -ForceInstall:$Force)) {
        Write-Err "Failed to install/update specify-cli. Exiting."
        exit 1
    }
    
    # Get project directories
    $projectDirs = Get-ProjectDirectories -ConfigFilePath $ConfigFile
    
    if ($projectDirs.Count -eq 0) {
        Write-WarningMsg "No project directories found. Nothing to update."
        exit 0
    }
    
    # Process each directory
    $successCount = 0
    $failCount = 0
    
    foreach ($dir in $projectDirs) {
        Write-Host ""
        if (Invoke-SpecifyUpdate -ProjectDirectory $dir) {
            $successCount++
        } else {
            $failCount++
        }
    }
    
    Write-Host ""
    Write-Info "=== Summary ==="
    Write-Info "Successful updates: $successCount"
    Write-Info "Failed updates: $failCount"
    Write-Info "Total processed: $($successCount + $failCount)"
    
    if ($failCount -eq 0) {
        Write-Success "All updates completed successfully!"
        exit 0
    } else {
        Write-Err "Some updates failed. Please check the logs above."
        exit 1
    }
}

Main