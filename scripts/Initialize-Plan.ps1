<#
.SYNOPSIS
    Setup implementation plan structure for current branch
.DESCRIPTION
    This script sets up the implementation plan structure for the current branch
    and returns the paths needed for implementation plan generation.
.PARAMETER Json
    Output results in JSON format
.EXAMPLE
    .\Initialize-Plan.ps1
    Set up plan with human-readable output
.EXAMPLE
    .\Initialize-Plan.ps1 -Json
    Set up plan with JSON output
#>

[CmdletBinding()]
param(
    [Parameter()]
    [switch]$Json
)

# Import common functions
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module (Join-Path $scriptPath "Common.psm1") -Force

try {
    # Get feature paths
    $paths = Get-FeaturePaths
    
    # Check if on feature branch
    if (-not (Test-FeatureBranch -Branch $paths.CurrentBranch)) {
        exit 1
    }
    
    # Create feature directory if it doesn't exist
    if (-not (Test-Path -Path $paths.FeatureDir -PathType Container)) {
        New-Item -ItemType Directory -Path $paths.FeatureDir -Force | Out-Null
    }
    
    # Copy plan template if it exists
    $templatePath = Join-Path $paths.RepoRoot "templates\plan-template.md"
    if (Test-Path -Path $templatePath -PathType Leaf) {
        Copy-Item -Path $templatePath -Destination $paths.ImplPlan -Force
    } elseif (-not (Test-Path -Path $paths.ImplPlan -PathType Leaf)) {
        # Create a default plan if template doesn't exist and plan doesn't exist
        $defaultPlan = @"
# Implementation Plan

## Overview
[Brief description of the implementation approach]

## Tasks
- [ ] Task 1
- [ ] Task 2

## Dependencies
- None

## Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Notes
[Any additional notes or considerations]
"@
        Set-Content -Path $paths.ImplPlan -Value $defaultPlan -NoNewline
    }
    
    # Output results
    if ($Json) {
        @{
            FEATURE_SPEC = $paths.FeatureSpec
            IMPL_PLAN = $paths.ImplPlan
            SPECS_DIR = $paths.FeatureDir
            BRANCH = $paths.CurrentBranch
        } | ConvertTo-Json -Compress
    } else {
        Write-Host "FEATURE_SPEC: $($paths.FeatureSpec)"
        Write-Host "IMPL_PLAN: $($paths.ImplPlan)"
        Write-Host "SPECS_DIR: $($paths.FeatureDir)"
        Write-Host "BRANCH: $($paths.CurrentBranch)"
        
        if (Test-Path -Path $paths.ImplPlan -PathType Leaf) {
            Write-Host "`n$($PSStyle.Foreground.Green)✓$($PSStyle.Reset) Implementation plan created at: $($paths.ImplPlan)"
            Write-Host "   Edit this file to define your implementation plan."
        }
    }
    
    exit 0
} catch {
    if ($Json) {
        @{ error = $_.Exception.Message } | ConvertTo-Json -Compress
    } else {
        Write-Error $_.Exception.Message
    }
    exit 1
}
