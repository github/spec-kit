#!/usr/bin/env pwsh

# ==============================================================================
# Create New Feature Script (PowerShell)
# ==============================================================================
#
# DESCRIPTION:
#   PowerShell equivalent of the bash create-new-feature.sh script.
#   Initializes a new feature in the Spec-Driven Development workflow by:
#   1. Creating a new feature branch with proper naming convention
#   2. Setting up the feature directory structure in specs/
#   3. Copying the specification template to start feature definition
#   4. Auto-incrementing feature numbers for consistent organization
#
# USAGE:
#   .\create-new-feature.ps1 [-Json] <feature_description>
#
# PARAMETERS:
#   -Json                  Output results in JSON format for programmatic consumption
#   FeatureDescription     A descriptive name for the feature (multiple words allowed)
#                         Will be normalized to lowercase with hyphens
#
# FEATURE NUMBERING:
#   Features are automatically numbered starting from 001, incrementing based on
#   existing feature directories. The script finds the highest existing number
#   and adds 1 to ensure sequential, non-conflicting feature numbers.
#
# BRANCH NAMING:
#   Created branches follow the pattern: XXX-first-few-words
#   - XXX: 3-digit zero-padded feature number
#   - Only first 3 words of description are used for brevity
#   - All text converted to lowercase with hyphens as separators
#   - Special characters are removed or converted to hyphens
#
# DIRECTORY STRUCTURE CREATED:
#   specs/XXX-feature-name/
#   └── spec.md           # Feature specification (copied from template)
#
# OUTPUT:
#   In default mode: Displays branch name, spec file path, and feature number
#   In JSON mode: Returns structured JSON with BRANCH_NAME, SPEC_FILE, FEATURE_NUM
#
# EXIT CODES:
#   0 - Feature created successfully
#   1 - Missing feature description or other error
#
# EXAMPLES:
#   .\create-new-feature.ps1 "User Authentication System"
#   .\create-new-feature.ps1 -Json "Payment Processing Integration"
#   .\create-new-feature.ps1 "Advanced Search and Filtering Capabilities"
#
# RELATED SCRIPTS:
#   - setup-plan.ps1: Next step to create implementation plan
#   - check-task-prerequisites.ps1: Validates the created structure
#   - create-new-feature.sh: Bash equivalent of this script
#
# ==============================================================================

[CmdletBinding()]
param(
    [switch]$Json,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$FeatureDescription
)
$ErrorActionPreference = 'Stop'

if (-not $FeatureDescription -or $FeatureDescription.Count -eq 0) {
    Write-Error "Usage: ./create-new-feature.ps1 [-Json] <feature description>"; exit 1
}
$featureDesc = ($FeatureDescription -join ' ').Trim()

$repoRoot = git rev-parse --show-toplevel
$specsDir = Join-Path $repoRoot 'specs'
New-Item -ItemType Directory -Path $specsDir -Force | Out-Null

$highest = 0
if (Test-Path $specsDir) {
    Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
        if ($_.Name -match '^(\d{3})') {
            $num = [int]$matches[1]
            if ($num -gt $highest) { $highest = $num }
        }
    }
}
$next = $highest + 1
$featureNum = ('{0:000}' -f $next)

$branchName = $featureDesc.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
$words = ($branchName -split '-') | Where-Object { $_ } | Select-Object -First 3
$branchName = "$featureNum-$([string]::Join('-', $words))"

git checkout -b $branchName | Out-Null

$featureDir = Join-Path $specsDir $branchName
New-Item -ItemType Directory -Path $featureDir -Force | Out-Null

$template = Join-Path $repoRoot 'templates/spec-template.md'
$specFile = Join-Path $featureDir 'spec.md'
if (Test-Path $template) { Copy-Item $template $specFile -Force } else { New-Item -ItemType File -Path $specFile | Out-Null }

if ($Json) {
    $obj = [PSCustomObject]@{ BRANCH_NAME = $branchName; SPEC_FILE = $specFile; FEATURE_NUM = $featureNum }
    $obj | ConvertTo-Json -Compress
} else {
    Write-Output "BRANCH_NAME: $branchName"
    Write-Output "SPEC_FILE: $specFile"
    Write-Output "FEATURE_NUM: $featureNum"
}
