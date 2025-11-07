#!/usr/bin/env pwsh
# Setup AI documentation for a feature

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$FeatureIdentifier = "",
    [switch]$Json,
    [switch]$All,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output "Usage: ./setup-ai-doc.ps1 [-Json] [-All | FeatureIdentifier]"
    Write-Output ""
    Write-Output "Parameters:"
    Write-Output "  FeatureIdentifier    Feature name, number, or branch name (optional)"
    Write-Output "                       If not provided, uses current branch"
    Write-Output ""
    Write-Output "Options:"
    Write-Output "  -Json                Output results in JSON format"
    Write-Output "  -All                 Process all features in specs/ directory"
    Write-Output "  -Help                Show this help message"
    Write-Output ""
    Write-Output "Examples:"
    Write-Output "  ./setup-ai-doc.ps1                  # Use current branch"
    Write-Output "  ./setup-ai-doc.ps1 -All             # Process all features"
    Write-Output "  ./setup-ai-doc.ps1 -Json -All       # Process all features with JSON output"
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

# Get template paths
$templateFile = Join-Path $repoRoot "templates/ai-doc-template.md"
$quickRefTemplate = Join-Path $repoRoot "templates/quick-ref-template.md"
if (-not (Test-Path $templateFile)) {
    $templateFile = Join-Path $repoRoot ".specify/templates/ai-doc-template.md"
}
if (-not (Test-Path $quickRefTemplate)) {
    $quickRefTemplate = Join-Path $repoRoot ".specify/templates/quick-ref-template.md"
}

# Function to process a single feature
function Process-Feature {
    param(
        [string]$FeatureDir,
        [string]$TemplateFile,
        [string]$QuickRefTemplate
    )

    $featureName = Split-Path -Leaf $FeatureDir
    $specFile = Join-Path $FeatureDir "spec.md"
    $aiDocFile = Join-Path $FeatureDir "ai-doc.md"
    $quickRefFile = Join-Path $FeatureDir "quick-ref.md"
    $currentDate = Get-Date -Format "yyyy-MM-dd"

    # Skip if spec.md doesn't exist
    if (-not (Test-Path $specFile)) {
        return @{
            feature = $featureName
            status = "skipped"
            reason = "spec.md not found"
        }
    }

    # Determine if creating or updating ai-doc.md
    if (-not (Test-Path $aiDocFile)) {
        # Create new ai-doc.md
        $content = Get-Content -Path $TemplateFile -Raw
        $content = $content -replace '\[FEATURE NAME\]', $featureName
        $content = $content -replace '\[###-feature-name\]', $featureName
        $content = $content -replace '\[DATE\]', $currentDate
        $content = $content -replace '\[Draft/Complete\]', 'Draft'
        Set-Content -Path $aiDocFile -Value $content -NoNewline
        $status = "created"
    } else {
        # Update existing ai-doc.md - update the date
        $content = Get-Content -Path $aiDocFile -Raw
        $content = $content -replace '\*\*Updated\*\*: \d{4}-\d{2}-\d{2}', "**Updated**: $currentDate"
        Set-Content -Path $aiDocFile -Value $content -NoNewline
        $status = "updated"
    }

    # Create or update quick-ref.md (always create if template exists)
    $quickRefStatus = "template_not_found"
    if (Test-Path $QuickRefTemplate) {
        if (-not (Test-Path $quickRefFile)) {
            # Create new quick-ref.md
            $content = Get-Content -Path $QuickRefTemplate -Raw
            $content = $content -replace '\[FEATURE NAME\]', $featureName
            Set-Content -Path $quickRefFile -Value $content -NoNewline
            $quickRefStatus = "created"
        } else {
            # Quick ref exists - mark as exists (AI should update manually)
            $quickRefStatus = "exists"
        }
    }

    # Get additional file paths
    $planFile = Join-Path $FeatureDir "plan.md"
    $tasksFile = Join-Path $FeatureDir "tasks.md"

    return @{
        feature = $featureName
        status = $status
        quick_ref_status = $quickRefStatus
        ai_doc_file = $aiDocFile
        quick_ref_file = $quickRefFile
        spec_file = $specFile
        plan_file = $planFile
        tasks_file = $tasksFile
    }
}

# Handle -All mode
if ($All) {
    # Check if specs directory exists
    if (-not (Test-Path $specsDir)) {
        if ($Json) {
            $error = @{
                error = "Specs directory not found"
                path = $specsDir
            } | ConvertTo-Json -Compress
            Write-Output $error
        } else {
            Write-Error "ERROR: Specs directory not found: $specsDir"
        }
        exit 1
    }

    # Find all feature directories
    $featureDirs = Get-ChildItem -Path $specsDir -Directory | Sort-Object Name

    if ($featureDirs.Count -eq 0) {
        if ($Json) {
            $result = @{
                features = @()
                total = 0
                message = "No feature directories found"
            } | ConvertTo-Json -Compress
            Write-Output $result
        } else {
            Write-Output "No feature directories found in $specsDir"
        }
        exit 0
    }

    # Process all features
    $results = @()
    foreach ($featureDir in $featureDirs) {
        $result = Process-Feature -FeatureDir $featureDir.FullName -TemplateFile $templateFile -QuickRefTemplate $quickRefTemplate
        $results += $result

        if (-not $Json) {
            Write-Output "Processing: $($result.feature)"
        }
    }

    # Output results
    if ($Json) {
        $output = @{
            features = $results
            total = $results.Count
        } | ConvertTo-Json -Compress
        Write-Output $output
    } else {
        Write-Output ""
        Write-Output "Processed $($results.Count) feature(s)"
    }

    exit 0
}

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

# Check if template exists
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

# Process the single feature
$result = Process-Feature -FeatureDir $featureDir -TemplateFile $templateFile -QuickRefTemplate $quickRefTemplate

# Output results
if ($Json) {
    $result | ConvertTo-Json -Compress
} else {
    $featureName = Split-Path -Leaf $featureDir
    $aiDocFile = Join-Path $featureDir "ai-doc.md"
    $quickRefFile = Join-Path $featureDir "quick-ref.md"
    $specFile = Join-Path $featureDir "spec.md"
    $planFile = Join-Path $featureDir "plan.md"
    $tasksFile = Join-Path $featureDir "tasks.md"

    Write-Output "AI Documentation Setup Complete"
    Write-Output ""
    Write-Output "Feature: $featureName"
    Write-Output "Documentation files:"
    Write-Output "  - AI Doc: $aiDocFile (status: $($result.status))"
    if ($result.quick_ref_status -ne "template_not_found") {
        Write-Output "  - Quick Ref: $quickRefFile (status: $($result.quick_ref_status))"
    }
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
