#!/usr/bin/env pwsh
# Setup AI documentation for a feature

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$FeatureIdentifier = "",
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output "Usage: ./setup-ai-doc.ps1 [-Json] [FeatureIdentifier]"
    Write-Output ""
    Write-Output "Parameters:"
    Write-Output "  FeatureIdentifier    Feature name, number, or branch name (optional)"
    Write-Output "                       If not provided, uses current branch"
    Write-Output ""
    Write-Output "Options:"
    Write-Output "  -Json                Output results in JSON format"
    Write-Output "  -Help                Show this help message"
    Write-Output ""
    Write-Output "Examples:"
    Write-Output "  ./setup-ai-doc.ps1                  # Use current branch"
    Write-Output "  ./setup-ai-doc.ps1 user-auth        # Use feature by name"
    Write-Output "  ./setup-ai-doc.ps1 5                # Use feature by number"
    Write-Output "  ./setup-ai-doc.ps1 5-user-auth      # Use feature by full branch name"
    Write-Output "  ./setup-ai-doc.ps1 -Json user-auth  # JSON output"
    exit 0
}

# Load common functions
. "$PSScriptRoot/common.ps1"

# Get repository root
$repoRoot = Get-RepoRoot
$specsDir = Join-Path $repoRoot "specs"

# Function to find feature directory by identifier
function Find-FeatureDirectory {
    param([string]$Identifier, [string]$SpecsPath)

    # Case 1: Full branch name (e.g., "5-user-auth")
    if ($Identifier -match '^(\d{1,3})-([a-z0-9-]+)$') {
        $num = [int]$matches[1]
        $normalized = "{0:000}" -f $num
        $rest = $matches[2]
        $path = Join-Path $SpecsPath "$normalized-$rest"
        if (Test-Path $path) {
            return $path
        }
    }

    # Case 2: Just a number (e.g., "5")
    if ($Identifier -match '^\d+$') {
        $num = [int]$Identifier
        $normalized = "{0:000}" -f $num
        $matches = Get-ChildItem -Path $SpecsPath -Directory -Filter "$normalized-*" -ErrorAction SilentlyContinue
        if ($matches) {
            return $matches[0].FullName
        }
    }

    # Case 3: Feature name (e.g., "user-auth")
    $matches = Get-ChildItem -Path $SpecsPath -Directory -Filter "*-$Identifier" -ErrorAction SilentlyContinue
    if ($matches) {
        return $matches[0].FullName
    }

    # Case 4: Exact match
    $path = Join-Path $SpecsPath $Identifier
    if (Test-Path $path) {
        return $path
    }

    return $null
}

# Determine feature directory
if (-not $FeatureIdentifier) {
    # No identifier provided - use current branch
    $currentBranch = Get-CurrentBranch

    if ($currentBranch -notmatch '^(\d{3})-') {
        if ($Json) {
            $error = @{
                error = "Not on a feature branch. Please specify feature identifier or switch to a feature branch."
            } | ConvertTo-Json -Compress
            Write-Output $error
        } else {
            Write-Error "ERROR: Not on a feature branch (current: $currentBranch)"
            Write-Error "Please specify feature name/number or switch to a feature branch."
        }
        exit 1
    }

    # Extract prefix and find feature directory
    $featureDir = Join-Path $specsDir $currentBranch
    if (-not (Test-Path $featureDir)) {
        # Try finding by prefix
        $num = [int]$matches[1]
        $normalized = "{0:000}" -f $num
        $matches = Get-ChildItem -Path $specsDir -Directory -Filter "$normalized-*" -ErrorAction SilentlyContinue
        if ($matches) {
            $featureDir = $matches[0].FullName
        }
    }
} else {
    # Identifier provided - find the feature directory
    $featureDir = Find-FeatureDirectory -Identifier $FeatureIdentifier -SpecsPath $specsDir

    if (-not $featureDir) {
        if ($Json) {
            $error = @{
                error = "No feature directory found for: $FeatureIdentifier"
            } | ConvertTo-Json -Compress
            Write-Output $error
        } else {
            Write-Error "ERROR: No feature directory found for: $FeatureIdentifier"
            Write-Error "Looked in: $specsDir"
        }
        exit 1
    }
}

# Verify feature directory exists
if (-not (Test-Path $featureDir)) {
    if ($Json) {
        $error = @{
            error = "Feature directory not found: $featureDir"
        } | ConvertTo-Json -Compress
        Write-Output $error
    } else {
        Write-Error "ERROR: Feature directory not found: $featureDir"
        Write-Error "Please ensure the feature exists in .specify/specs/"
    }
    exit 1
}

# Verify spec.md exists
$specFile = Join-Path $featureDir "spec.md"
if (-not (Test-Path $specFile)) {
    if ($Json) {
        $error = @{
            error = "Spec file not found: $specFile"
            warning = "Feature directory exists but spec.md is missing"
        } | ConvertTo-Json -Compress
        Write-Output $error
    } else {
        Write-Error "ERROR: Spec file not found: $specFile"
        Write-Error "The feature directory exists but spec.md is missing."
    }
    exit 1
}

# Define AI doc file path
$aiDocFile = Join-Path $featureDir "ai-doc.md"

# Get template path
$templateFile = Join-Path $repoRoot "templates/ai-doc-template.md"

# Check if template exists
if (-not (Test-Path $templateFile)) {
    # Fall back to .specify/templates
    $templateFile = Join-Path $repoRoot ".specify/templates/ai-doc-template.md"

    if (-not (Test-Path $templateFile)) {
        if ($Json) {
            $error = @{
                error = "Template file not found: ai-doc-template.md"
            } | ConvertTo-Json -Compress
            Write-Output $error
        } else {
            Write-Error "ERROR: Template file not found"
            Write-Error "Expected at: $repoRoot/templates/ai-doc-template.md"
            Write-Error "Or at: $repoRoot/.specify/templates/ai-doc-template.md"
        }
        exit 1
    }
}

# Extract feature name from directory
$featureName = Split-Path -Leaf $featureDir

# Get current date
$currentDate = Get-Date -Format "yyyy-MM-dd"

# Create ai-doc.md from template if it doesn't exist
if (-not (Test-Path $aiDocFile)) {
    # Read template and do basic replacements
    $content = Get-Content -Path $templateFile -Raw
    $content = $content -replace '\[FEATURE NAME\]', $featureName
    $content = $content -replace '\[###-feature-name\]', $featureName
    $content = $content -replace '\[DATE\]', $currentDate
    $content = $content -replace '\[Draft/Complete\]', 'Draft'

    # Write to ai-doc.md
    Set-Content -Path $aiDocFile -Value $content -NoNewline

    $status = "created"
} else {
    $status = "exists"
}

# Get additional file paths for reference
$planFile = Join-Path $featureDir "plan.md"
$tasksFile = Join-Path $featureDir "tasks.md"

# Output results
if ($Json) {
    $result = @{
        AI_DOC_FILE = $aiDocFile
        FEATURE_DIR = $featureDir
        FEATURE_NAME = $featureName
        SPEC_FILE = $specFile
        PLAN_FILE = $planFile
        TASKS_FILE = $tasksFile
        STATUS = $status
        TEMPLATE_USED = $templateFile
    }
    $result | ConvertTo-Json -Compress
} else {
    Write-Output "AI Documentation Setup Complete"
    Write-Output ""
    Write-Output "Feature: $featureName"
    Write-Output "Documentation file: $aiDocFile"
    Write-Output "Status: $status"
    Write-Output ""
    Write-Output "Related files:"
    Write-Output "  - Spec: $specFile"
    if (Test-Path $planFile) {
        Write-Output "  - Plan: $planFile"
    }
    if (Test-Path $tasksFile) {
        Write-Output "  - Tasks: $tasksFile"
    }
}
