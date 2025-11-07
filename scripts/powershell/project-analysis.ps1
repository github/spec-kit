#!/usr/bin/env pwsh

# Project Analysis Script (PowerShell)
#
# This script performs comprehensive project analysis against all SpecKit specifications
# to verify whether the project meets defined expectations.
#
# Usage: ./project-analysis.ps1 [OPTIONS]
#
# OPTIONS:
#   -Json               Output in JSON format
#   -CheckPatterns      Enable code pattern analysis (Security, DRY, KISS, SOLID)
#   -Help, -h           Show help message

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$CheckPatterns,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: project-analysis.ps1 [OPTIONS]

Perform comprehensive project analysis against all SpecKit specifications.

OPTIONS:
  -Json               Output in JSON format
  -CheckPatterns      Enable code pattern analysis (Security, DRY, KISS, SOLID)
  -Help, -h           Show this help message

EXAMPLES:
  # Basic project analysis
  .\project-analysis.ps1 -Json

  # Analysis with pattern checking
  .\project-analysis.ps1 -Json -CheckPatterns

"@
    exit 0
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get repository root
$repoRoot = Get-RepoRoot
$specsDir = Join-Path $repoRoot "specs"
$constitutionFile = Join-Path $repoRoot "memory" "constitution.md"

# Check if specs directory exists
if (-not (Test-Path $specsDir -PathType Container)) {
    if ($Json) {
        [PSCustomObject]@{
            error = "Specs directory not found"
            specs_dir = $specsDir
        } | ConvertTo-Json -Compress
    } else {
        Write-Error "ERROR: Specs directory not found: $specsDir"
    }
    exit 1
}

# Function to check if a file exists
function Test-SpecFile {
    param(
        [string]$SpecDir,
        [string]$FileName
    )
    $filePath = Join-Path $SpecDir $FileName
    Test-Path $filePath -PathType Leaf
}

# Function to count lines in a file
function Get-LineCount {
    param([string]$FilePath)

    if (Test-Path $FilePath -PathType Leaf) {
        (Get-Content $FilePath | Measure-Object -Line).Lines
    } else {
        0
    }
}

# Collect all spec directories
$specDirs = Get-ChildItem -Path $specsDir -Directory | Select-Object -ExpandProperty Name

# Sort spec directories by numeric prefix
$sortedSpecs = $specDirs | Sort-Object

# Check if constitution file exists
$constitutionExists = Test-Path $constitutionFile -PathType Leaf

# Detect programming languages in the repository
function Get-DetectedLanguages {
    $languages = @()

    if (Test-Path (Join-Path $repoRoot "package.json")) { $languages += "JavaScript/TypeScript" }
    if (Test-Path (Join-Path $repoRoot "pyproject.toml")) { $languages += "Python" }
    if (Test-Path (Join-Path $repoRoot "setup.py")) { $languages += "Python" }
    if (Test-Path (Join-Path $repoRoot "requirements.txt")) { $languages += "Python" }
    if (Test-Path (Join-Path $repoRoot "go.mod")) { $languages += "Go" }
    if (Test-Path (Join-Path $repoRoot "Cargo.toml")) { $languages += "Rust" }
    if (Test-Path (Join-Path $repoRoot "pom.xml")) { $languages += "Java" }
    if (Test-Path (Join-Path $repoRoot "build.gradle")) { $languages += "Java" }
    if (Test-Path (Join-Path $repoRoot "Gemfile")) { $languages += "Ruby" }
    if (Test-Path (Join-Path $repoRoot "composer.json")) { $languages += "PHP" }
    if (Get-ChildItem -Path $repoRoot -Filter "*.csproj" -File) { $languages += "C#" }

    if ($languages.Count -eq 0) {
        return "Unknown"
    } else {
        return ($languages -join ",")
    }
}

$detectedLanguages = Get-DetectedLanguages

# Find source code directories
function Get-SourceDirs {
    $sourceDirs = @()

    if (Test-Path (Join-Path $repoRoot "src") -PathType Container) { $sourceDirs += "src" }
    if (Test-Path (Join-Path $repoRoot "lib") -PathType Container) { $sourceDirs += "lib" }
    if (Test-Path (Join-Path $repoRoot "app") -PathType Container) { $sourceDirs += "app" }
    if (Test-Path (Join-Path $repoRoot "source") -PathType Container) { $sourceDirs += "source" }
    if (Test-Path (Join-Path $repoRoot "pkg") -PathType Container) { $sourceDirs += "pkg" }

    if ($sourceDirs.Count -eq 0) {
        return ""
    } else {
        return ($sourceDirs -join ",")
    }
}

$sourceDirs = Get-SourceDirs

# Build spec information
$specs = @()
foreach ($specName in $sortedSpecs) {
    $specDir = Join-Path $specsDir $specName

    $hasSpec = Test-SpecFile -SpecDir $specDir -FileName "spec.md"
    $hasPlan = Test-SpecFile -SpecDir $specDir -FileName "plan.md"
    $hasTasks = Test-SpecFile -SpecDir $specDir -FileName "tasks.md"
    $hasResearch = Test-SpecFile -SpecDir $specDir -FileName "research.md"
    $hasDataModel = Test-SpecFile -SpecDir $specDir -FileName "data-model.md"
    $hasQuickstart = Test-SpecFile -SpecDir $specDir -FileName "quickstart.md"
    $hasContracts = Test-Path (Join-Path $specDir "contracts") -PathType Container

    $specLines = Get-LineCount -FilePath (Join-Path $specDir "spec.md")
    $planLines = Get-LineCount -FilePath (Join-Path $specDir "plan.md")
    $tasksLines = Get-LineCount -FilePath (Join-Path $specDir "tasks.md")

    $specs += [PSCustomObject]@{
        name = $specName
        dir = $specDir
        has_spec = $hasSpec
        has_plan = $hasPlan
        has_tasks = $hasTasks
        has_research = $hasResearch
        has_data_model = $hasDataModel
        has_quickstart = $hasQuickstart
        has_contracts = $hasContracts
        spec_lines = $specLines
        plan_lines = $planLines
        tasks_lines = $tasksLines
    }
}

# Output results
if ($Json) {
    [PSCustomObject]@{
        repo_root = $repoRoot
        specs_dir = $specsDir
        constitution_exists = $constitutionExists
        constitution_file = $constitutionFile
        pattern_check_enabled = $CheckPatterns.IsPresent
        detected_languages = $detectedLanguages
        source_dirs = $sourceDirs
        total_specs = $sortedSpecs.Count
        specs = $specs
    } | ConvertTo-Json -Compress -Depth 10
} else {
    Write-Output "=== Project Analysis ==="
    Write-Output ""
    Write-Output "Repository Root: $repoRoot"
    Write-Output "Specs Directory: $specsDir"
    Write-Output "Constitution: $(if ($constitutionExists) { '✓ Found' } else { '✗ Missing' })"
    Write-Output "Detected Languages: $detectedLanguages"
    Write-Output "Source Directories: $sourceDirs"
    Write-Output "Pattern Check: $(if ($CheckPatterns) { 'Enabled' } else { 'Disabled' })"
    Write-Output ""
    Write-Output "Total Specifications: $($sortedSpecs.Count)"
    Write-Output ""

    foreach ($spec in $specs) {
        Write-Output "[$($spec.name)]"
        Write-Output "  spec.md:       $(if ($spec.has_spec) { 'true' } else { 'false' })"
        Write-Output "  plan.md:       $(if ($spec.has_plan) { 'true' } else { 'false' })"
        Write-Output "  tasks.md:      $(if ($spec.has_tasks) { 'true' } else { 'false' })"
        Write-Output "  research.md:   $(if ($spec.has_research) { 'true' } else { 'false' })"
        Write-Output "  data-model.md: $(if ($spec.has_data_model) { 'true' } else { 'false' })"
        Write-Output ""
    }
}
