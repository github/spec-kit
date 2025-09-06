<#
.SYNOPSIS
    Create a new feature with branch, directory structure, and template
.DESCRIPTION
    This script creates a new feature branch and directory structure with template files.
.PARAMETER FeatureDescription
    Description of the new feature
.PARAMETER Json
    Output results in JSON format
.EXAMPLE
    .\New-Feature.ps1 -FeatureDescription "Add user authentication"
    Create a new feature with human-readable output
.EXAMPLE
    .\New-Feature.ps1 -FeatureDescription "Add user authentication" -Json
    Create a new feature with JSON output
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$FeatureDescription,
    
    [Parameter()]
    [switch]$Json
)

# Import common functions
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module (Join-Path $scriptPath "Common.psm1") -Force

try {
    # Get repository root and create specs directory if it doesn't exist
    $repoRoot = Get-RepoRoot
    $specsDir = Join-Path $repoRoot "specs"
    
    if (-not (Test-Path -Path $specsDir -PathType Container)) {
        New-Item -ItemType Directory -Path $specsDir | Out-Null
    }

    # Find the highest numbered feature directory
    $highest = 0
    if (Test-Path -Path $specsDir -PathType Container) {
        Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
            $dirName = $_.Name
            if ($dirName -match '^(\d+)') {
                $number = [int]$matches[1]
                if ($number -gt $highest) {
                    $highest = $number
                }
            }
        }
    }

    # Generate new feature number and name
    $newNumber = $highest + 1
    $branchNumber = "{0:D3}" -f $newNumber
    
    # Create branch name (replace spaces with hyphens and make lowercase)
    $branchName = "$branchNumber-$($FeatureDescription.ToLower() -replace '[^a-z0-9]', '-' -replace '-+', '-' -trim('-' -split ''))"
    $featureDir = Join-Path $specsDir $branchName

    # Create and checkout new branch
    git checkout -b $branchName 2>&1 | Out-Null
    
    # Create directory structure
    $directories = @(
        $featureDir,
        (Join-Path $featureDir "contracts")
    )
    
    $directories | ForEach-Object {
        if (-not (Test-Path -Path $_ -PathType Container)) {
            New-Item -ItemType Directory -Path $_ -Force | Out-Null
        }
    }

    # Create template files
    $templates = @{
        "spec.md" = @"
# $FeatureDescription

## Overview
[Brief description of the feature]

## Goals
- [ ] Goal 1
- [ ] Goal 2

## Non-Goals
- Out of scope items

## User Stories
- As a [user role], I want [feature] so that [benefit]

## Technical Details
[Technical implementation details]
"@

        "plan.md" = @"
# Implementation Plan: $FeatureDescription

## Tasks
- [ ] Task 1
- [ ] Task 2

## Dependencies
- None

## Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing
"@
    }

    $templates.GetEnumerator() | ForEach-Object {
        $filePath = Join-Path $featureDir $_.Key
        if (-not (Test-Path -Path $filePath -PathType Leaf)) {
            Set-Content -Path $filePath -Value $_.Value -NoNewline
        }
    }

    # Add and commit the new files
    git add $featureDir
    git commit -m "feat: add initial structure for $FeatureDescription" 2>&1 | Out-Null

    # Output results
    if ($Json) {
        @{
            branch = $branchName
            directory = $featureDir
            files = @(
                (Join-Path $featureDir "spec.md"),
                (Join-Path $featureDir "plan.md")
            )
        } | ConvertTo-Json -Depth 3
    } else {
        Write-Host "$($PSStyle.Foreground.Green)✓$($PSStyle.Reset) Created feature '$FeatureDescription'"
        Write-Host "  Branch: $branchName"
        Write-Host "  Directory: $featureDir"
        Write-Host "  Files created:"
        Get-ChildItem -Path $featureDir -File -Recurse | ForEach-Object {
            Write-Host "    - $($_.FullName.Replace($repoRoot, '').TrimStart('\'))"
        }
        Write-Host "\nNext steps:"
        Write-Host "  1. Edit $featureDir\spec.md to define the feature requirements"
        Write-Host "  2. Update $featureDir\plan.md with implementation details"
        Write-Host "  3. Push the branch: git push -u origin $branchName"
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
