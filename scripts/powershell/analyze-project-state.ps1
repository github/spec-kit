#!/usr/bin/env pwsh
# Project State Analyzer - Compare constitution against implementation (PowerShell)
[CmdletBinding()]
param(
    [switch]$Json
)
$ErrorActionPreference = 'Stop'

$repoRoot = git rev-parse --show-toplevel
$constitutionFile = Join-Path $repoRoot '.specify/memory/constitution.md'
$srcDir = Join-Path $repoRoot 'src'
$testsDir = Join-Path $repoRoot 'tests'
$docsDir = Join-Path $repoRoot 'docs'
$specsDir = Join-Path $repoRoot 'specs'

# Check if this is a brownfield project
$isBrownfield = $false
$projectType = "greenfield"

if ((Test-Path $srcDir) -or (Test-Path $testsDir) -or (Test-Path $docsDir)) {
    $isBrownfield = $true
    $projectType = "brownfield"
}

# Analyze existing specs and their completion status
$existingSpecs = @()
$completedFeatures = @()
$incompleteFeatures = @()
$missingImplementations = @()

if (Test-Path $specsDir) {
    Get-ChildItem -Path $specsDir -Directory | ForEach-Object {
        $specName = $_.Name
        $existingSpecs += $specName
        
        # Check if tasks.md exists and analyze completion
        $tasksFile = Join-Path $_.FullName 'tasks.md'
        if (Test-Path $tasksFile) {
            $content = Get-Content $tasksFile -Raw
            $totalTasks = ([regex]::Matches($content, '^- \[ \]', 'Multiline')).Count
            $completedTasks = ([regex]::Matches($content, '^- \[x\]', 'Multiline')).Count
            
            if ($totalTasks -eq $completedTasks -and $totalTasks -gt 0) {
                $completedFeatures += $specName
            } elseif ($completedTasks -gt 0) {
                $incompleteFeatures += "$specName`:$completedTasks/$totalTasks"
            } else {
                $missingImplementations += $specName
            }
        } else {
            $missingImplementations += $specName
        }
    }
}

# Analyze implementation folders
$srcFilesCount = 0
$testFilesCount = 0
$docFilesCount = 0

if (Test-Path $srcDir) {
    $srcFilesCount = (Get-ChildItem -Path $srcDir -Recurse -File | Where-Object { $_.Extension -in @('.py', '.js', '.ts', '.java', '.cs', '.go', '.rs') }).Count
}

if (Test-Path $testsDir) {
    $testFilesCount = (Get-ChildItem -Path $testsDir -Recurse -File | Where-Object { $_.Extension -in @('.py', '.js', '.ts', '.java', '.cs', '.go', '.rs') }).Count
}

if (Test-Path $docsDir) {
    $docFilesCount = (Get-ChildItem -Path $docsDir -Recurse -File | Where-Object { $_.Extension -in @('.md', '.rst', '.txt') }).Count
}

# Constitution analysis
$constitutionPrinciples = @()
$constitutionRequirements = @()

if (Test-Path $constitutionFile) {
    $constitutionContent = Get-Content $constitutionFile -Raw
    
    # Extract principle names (lines starting with ###)
    $principleMatches = [regex]::Matches($constitutionContent, '^###\s*(.+)', 'Multiline')
    foreach ($match in $principleMatches) {
        $constitutionPrinciples += $match.Groups[1].Value.Trim()
    }
    
    # Extract key requirements from constitution
    if ($constitutionContent -match 'Library-First|library') {
        $constitutionRequirements += "Library-First Architecture"
    }
    if ($constitutionContent -match 'CLI Interface|CLI') {
        $constitutionRequirements += "CLI Interface"
    }
    if ($constitutionContent -match 'Test-First|TDD|NON-NEGOTIABLE') {
        $constitutionRequirements += "Test-First Development"
    }
    if ($constitutionContent -match 'Integration Testing') {
        $constitutionRequirements += "Integration Testing"
    }
    if ($constitutionContent -match 'Observability|logging') {
        $constitutionRequirements += "Observability"
    }
}

# Gap analysis
$constitutionalGaps = @()
$implementationGaps = @()

# Check for constitutional compliance
if ($constitutionRequirements -contains "Test-First Development" -and $testFilesCount -eq 0) {
    $constitutionalGaps += "Missing test implementation - Constitution requires Test-First"
}

if ($constitutionRequirements -contains "CLI Interface" -and $srcFilesCount -gt 0) {
    # Check if CLI files exist
    $cliFiles = 0
    if (Test-Path $srcDir) {
        $cliFiles = (Get-ChildItem -Path $srcDir -Recurse -File | Where-Object { $_.Name -like "*cli*" -or $_.Name -like "*command*" }).Count
    }
    if ($cliFiles -eq 0) {
        $constitutionalGaps += "Missing CLI interface - Constitution requires CLI for all libraries"
    }
}

# Generate analysis summary
$analysisDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

if ($Json) {
    $result = @{
        project_type = $projectType
        analysis_date = $analysisDate
        existing_specs = $existingSpecs
        completed_features = $completedFeatures
        incomplete_features = $incompleteFeatures
        missing_implementations = $missingImplementations
        src_files = $srcFilesCount
        test_files = $testFilesCount
        doc_files = $docFilesCount
        constitution_principles = $constitutionPrinciples
        constitution_requirements = $constitutionRequirements
        constitutional_gaps = $constitutionalGaps
        implementation_gaps = $implementationGaps
    } | ConvertTo-Json -Depth 3
    Write-Output $result
} else {
    Write-Output "PROJECT TYPE: $projectType"
    Write-Output "ANALYSIS DATE: $analysisDate"
    Write-Output ""
    Write-Output "=== EXISTING SPECS ==="
    $existingSpecs | ForEach-Object { Write-Output $_ }
    Write-Output ""
    Write-Output "=== COMPLETED FEATURES ==="
    $completedFeatures | ForEach-Object { Write-Output $_ }
    Write-Output ""
    Write-Output "=== INCOMPLETE FEATURES ==="
    $incompleteFeatures | ForEach-Object { Write-Output $_ }
    Write-Output ""
    Write-Output "=== MISSING IMPLEMENTATIONS ==="
    $missingImplementations | ForEach-Object { Write-Output $_ }
    Write-Output ""
    Write-Output "=== IMPLEMENTATION STATUS ==="
    Write-Output "Source files: $srcFilesCount"
    Write-Output "Test files: $testFilesCount"
    Write-Output "Doc files: $docFilesCount"
    Write-Output ""
    Write-Output "=== CONSTITUTION ANALYSIS ==="
    Write-Output "Principles:"
    $constitutionPrinciples | ForEach-Object { Write-Output "  - $_" }
    Write-Output "Requirements:"
    $constitutionRequirements | ForEach-Object { Write-Output "  - $_" }
    Write-Output ""
    Write-Output "=== GAPS IDENTIFIED ==="
    Write-Output "Constitutional gaps:"
    $constitutionalGaps | ForEach-Object { Write-Output "  - $_" }
    Write-Output "Implementation gaps:"
    $implementationGaps | ForEach-Object { Write-Output "  - $_" }
}