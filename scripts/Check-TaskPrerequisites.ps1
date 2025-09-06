<#
.SYNOPSIS
    Check that implementation plan exists and find optional design documents
.DESCRIPTION
    This script verifies the presence of required implementation plan and checks for
    optional design documents in a feature directory.
.PARAMETER Json
    Output results in JSON format
.EXAMPLE
    .\Check-TaskPrerequisites.ps1
    Check prerequisites with human-readable output
.EXAMPLE
    .\Check-TaskPrerequisites.ps1 -Json
    Check prerequisites with JSON output
#>

[CmdletBinding()]
param(
    [Parameter()]
    [switch]$Json
)

# Import common functions
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module (Join-Path $scriptPath "Common.psm1") -Force

# Get feature paths
$paths = Get-FeaturePaths

# Check if on feature branch
if (-not (Test-FeatureBranch -Branch $paths.CurrentBranch)) {
    exit 1
}

# Check if feature directory exists
if (-not (Test-Path -Path $paths.FeatureDir -PathType Container)) {
    Write-Error "Feature directory not found: $($paths.FeatureDir)"
    Write-Error "Run /specify first to create the feature structure."
    exit 1
}

# Check for implementation plan (required)
if (-not (Test-Path -Path $paths.ImplPlan -PathType Leaf)) {
    Write-Error "plan.md not found in $($paths.FeatureDir)"
    Write-Error "Run /plan first to create the plan."
    exit 1
}

if ($Json) {
    # Build JSON output
    $output = @{
        FEATURE_DIR = $paths.FeatureDir
        AVAILABLE_DOCS = @()
    }

    # Check for optional documents
    if (Test-Path -Path $paths.Research -PathType Leaf) {
        $output.AVAILABLE_DOCS += "research.md"
    }
    
    if (Test-Path -Path $paths.DataModel -PathType Leaf) {
        $output.AVAILABLE_DOCS += "data-model.md"
    }
    
    if (Test-Path -Path $paths.ContractsDir -PathType Container -and 
        (Get-ChildItem -Path $paths.ContractsDir -File -Recurse -ErrorAction SilentlyContinue).Count -gt 0) {
        $output.AVAILABLE_DOCS += "contracts/"
    }
    
    if (Test-Path -Path $paths.QuickStart -PathType Leaf) {
        $output.AVAILABLE_DOCS += "quickstart.md"
    }

    # Output as JSON
    $output | ConvertTo-Json -Compress
} else {
    # Human-readable output
    Write-Host "`n$($PSStyle.Bold)Feature Directory:$($PSStyle.Reset) $($paths.FeatureDir)"
    Write-Host "`n$($PSStyle.Underline)Required Documents:$($PSStyle.Reset)"
    
    # Check required documents
    $hasAllRequired = $true
    if (-not (Test-FileExists -Path $paths.ImplPlan -Description "Implementation plan")) {
        $hasAllRequired = $false
    }

    # Check optional documents
    Write-Host "`n$($PSStyle.Underline)Optional Documents:$($PSStyle.Reset)"
    $hasResearch = Test-FileExists -Path $paths.Research -Description "Research document"
    $hasDataModel = Test-FileExists -Path $paths.DataModel -Description "Data model document"
    $hasContracts = Test-DirectoryHasFiles -Path $paths.ContractsDir -Description "Contracts directory"
    $hasQuickStart = Test-FileExists -Path $paths.QuickStart -Description "Quick start guide"

    # Summary
    Write-Host "`n$($PSStyle.Bold)Summary:$($PSStyle.Reset)"
    if ($hasAllRequired) {
        Write-Host "$($PSStyle.Foreground.Green)✓$($PSStyle.Reset) All required documents are present"
    } else {
        Write-Host "$($PSStyle.Foreground.Red)✗$($PSStyle.Reset) Missing required documents"
    }
    
    $optionalCount = @($hasResearch, $hasDataModel, $hasContracts, $hasQuickStart) -eq $true
    Write-Host "$($PSStyle.Foreground.Cyan)ℹ$($PSStyle.Reset) $($optionalCount.Count) of 4 optional documents found"
}

exit 0
