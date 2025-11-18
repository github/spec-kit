#!/usr/bin/env pwsh

param(
    [switch]$Json,
    [string]$Summary = ""
)

$ErrorActionPreference = "Stop"

# Function to find repository root by searching for project markers
function Find-RepoRoot {
    param([string]$StartDir)
    
    $dir = $StartDir
    while ($dir -ne [System.IO.Path]::GetPathRoot($dir)) {
        if ((Test-Path (Join-Path $dir ".git")) -or (Test-Path (Join-Path $dir ".specify"))) {
            return $dir
        }
        $dir = Split-Path -Parent $dir
    }
    return $null
}

# Get script directory and repo root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Try git first, then fall back to searching for markers
try {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    if (-not $repoRoot) { throw }
} catch {
    $repoRoot = Find-RepoRoot $scriptDir
    if (-not $repoRoot) {
        Write-Error "Could not determine repository root. Please run this script from within the repository."
        exit 1
    }
}

# Source common functions
. (Join-Path $scriptDir "common.ps1")

# Check if active sprint exists
$activeDir = Join-Path $repoRoot ".specify/sprints/active"
$sprintFile = Join-Path $activeDir "sprint.md"

if (-not (Test-Path $sprintFile)) {
    Write-Error "No active sprint found at $activeDir`nCreate a sprint with '/speckit.sprint start' first"
    exit 1
}

# Extract sprint number and name from sprint.md
$sprintContent = Get-Content $sprintFile -Raw
if ($sprintContent -match '^# Sprint (\d+): (.+)$') {
    $sprintNumber = $matches[1]
    $sprintName = $matches[2].Trim()
} else {
    Write-Error "Could not extract sprint number or name from sprint.md"
    exit 1
}

# Create slug from sprint name
$sprintSlug = $sprintName.ToLower() -replace '[^a-z0-9]+', '-' -replace '^-|-$', ''

# Create archive directory
$archiveDir = Join-Path $repoRoot ".specify/sprints/archive"
$sprintArchiveDir = Join-Path $archiveDir "sprint-$sprintNumber-$sprintSlug"

if (Test-Path $sprintArchiveDir) {
    Write-Error "Archive directory already exists: $sprintArchiveDir"
    exit 1
}

New-Item -ItemType Directory -Path $sprintArchiveDir -Force | Out-Null

# Move active sprint files to archive
Copy-Item (Join-Path $activeDir "sprint.md") $sprintArchiveDir -ErrorAction SilentlyContinue
Copy-Item (Join-Path $activeDir "backlog.md") $sprintArchiveDir -ErrorAction SilentlyContinue
Copy-Item (Join-Path $activeDir "decisions.md") $sprintArchiveDir -ErrorAction SilentlyContinue

# Extract dates from sprint.md
$startDate = ""
$endDate = ""
if ($sprintContent -match '\*\*Duration\*\*: (\d{4}-\d{2}-\d{2}) - (\d{4}-\d{2}-\d{2})') {
    $startDate = $matches[1]
    $endDate = $matches[2]
}
$archivedDate = Get-Date -Format "yyyy-MM-dd"

# Create specs directory in archive
$specsArchiveDir = Join-Path $sprintArchiveDir "specs"
New-Item -ItemType Directory -Path $specsArchiveDir -Force | Out-Null

# Interactive check for near-complete features (if not in JSON mode)
$nearCompleteFeatures = @()
if (-not $Json -and (Test-Path $backlogFile)) {
    Write-Host ""
    Write-Host "Checking for near-complete features..." -ForegroundColor Cyan
    Write-Host ""
    
    $backlogContent = Get-Content $backlogFile
    
    foreach ($line in $backlogContent) {
        # Look for In Progress, In Review, or Blocked features
        if ($line -match '\| ([0-9]+-[^\|]+) \|.*\| (In Progress|In Review|Blocked)') {
            $featureId = $matches[1].Trim()
            $currentStatus = $matches[2].Trim()
            $specDir = Join-Path $specsDir $featureId
            
            if (Test-Path $specDir) {
                $specFile = Join-Path $specDir "spec.md"
                $featureName = "Unknown"
                if (Test-Path $specFile) {
                    $specContent = Get-Content $specFile -Raw
                    if ($specContent -match '^# Feature Specification: (.+)$') {
                        $featureName = $matches[1].Trim()
                    }
                }
                
                Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
                Write-Host "Feature: $featureId" -ForegroundColor Yellow
                Write-Host "Name: $featureName"
                Write-Host "Current Status: $currentStatus"
                Write-Host ""
                
                # Check completion indicators
                $hasSpec = Test-Path $specFile
                $hasPlan = Test-Path (Join-Path $specDir "plan.md")
                $hasTasks = Test-Path (Join-Path $specDir "tasks.md")
                
                Write-Host "Completion indicators:"
                if ($hasSpec) { Write-Host "  ✅ Spec exists" -ForegroundColor Green } else { Write-Host "  ❌ Spec missing" -ForegroundColor Red }
                if ($hasPlan) { Write-Host "  ✅ Plan exists" -ForegroundColor Green } else { Write-Host "  ❌ Plan missing" -ForegroundColor Red }
                if ($hasTasks) { Write-Host "  ✅ Tasks exists" -ForegroundColor Green } else { Write-Host "  ❌ Tasks missing" -ForegroundColor Red }
                
                # Check for common incomplete markers
                if ($hasSpec) {
                    $todoCount = (Select-String -Path $specFile -Pattern "TODO|FIXME|XXX" -AllMatches).Matches.Count
                    if ($todoCount -gt 0) {
                        Write-Host "  ⚠️  $todoCount TODO/FIXME markers in spec" -ForegroundColor Yellow
                    }
                }
                
                Write-Host ""
                $response = Read-Host "Archive this feature as complete? (y/n/skip-all)"
                
                switch ($response.ToLower()) {
                    { $_ -in 'y', 'yes' } {
                        $nearCompleteFeatures += $featureId
                        Write-Host "  → Will archive $featureId" -ForegroundColor Green
                    }
                    'skip-all' {
                        Write-Host "  → Skipping all remaining near-complete checks" -ForegroundColor Yellow
                        break
                    }
                    default {
                        Write-Host "  → Keeping $featureId in active specs/" -ForegroundColor Gray
                    }
                }
                Write-Host ""
            }
        }
    }
}

# Move completed features from specs directory to archive
$completedFeatures = 0
$featureList = ""
$specsDir = Join-Path $repoRoot "specs"
$backlogFile = Join-Path $activeDir "backlog.md"

if ((Test-Path $specsDir) -and (Test-Path $backlogFile)) {
    $backlogContent = Get-Content $backlogFile
    
    # Extract completed feature IDs from backlog (status: Done, Completed, or ✅)
    $backlogContent | ForEach-Object {
        if ($_ -match '\| ([0-9]+-[^\|]+) \|.*\| (Done|Completed|✅)') {
            $featureId = $matches[1].Trim()
            $specDir = Join-Path $specsDir $featureId
            
            if (Test-Path $specDir) {
                # Move spec to archive
                Move-Item $specDir $specsArchiveDir -Force
                
                # Extract feature name
                $specFile = Join-Path $specsArchiveDir "$featureId/spec.md"
                $featureName = "Unknown"
                if (Test-Path $specFile) {
                    $specContent = Get-Content $specFile -Raw
                    if ($specContent -match '^# Feature Specification: (.+)$') {
                        $featureName = $matches[1].Trim()
                    }
                }
                
                # Add to feature list with relative link
                $featureList += "| $featureId | $featureName | ✅ Complete | [spec](./specs/$featureId/spec.md) |`n"
                $completedFeatures++
            }
        }
    }
    
    # Also move near-complete features that user approved
    foreach ($featureId in $nearCompleteFeatures) {
        $specDir = Join-Path $specsDir $featureId
        if (Test-Path $specDir) {
            Move-Item $specDir $specsArchiveDir -Force
            
            $specFile = Join-Path $specsArchiveDir "$featureId/spec.md"
            $featureName = "Unknown"
            if (Test-Path $specFile) {
                $specContent = Get-Content $specFile -Raw
                if ($specContent -match '^# Feature Specification: (.+)$') {
                    $featureName = $matches[1].Trim()
                }
            }
            
            $featureList += "| $featureId | $featureName | ✅ Complete | [spec](./specs/$featureId/spec.md) |`n"
            $completedFeatures++
        }
    }
}

# Create features.md
$featuresContent = @"
# Sprint $sprintNumber Features

## Completed Features

| Feature ID | Feature Name | Status | Spec |
|------------|--------------|--------|------|
$featureList

## Notes

[Add any additional notes about features]
"@
$featuresContent | Set-Content (Join-Path $sprintArchiveDir "features.md")

# Create summary.md from template
$summaryTemplate = Join-Path $repoRoot ".specify/templates/sprint-summary-template.md"
$summaryFile = Join-Path $sprintArchiveDir "summary.md"

if (Test-Path $summaryTemplate) {
    $summaryContent = Get-Content $summaryTemplate -Raw
    $summaryContent = $summaryContent -replace '\[NUMBER\]', $sprintNumber
    $summaryContent = $summaryContent -replace '\[NAME\]', $sprintName
    $summaryContent = $summaryContent -replace '\[START_DATE\]', $startDate
    $summaryContent = $summaryContent -replace '\[END_DATE\]', $endDate
    $summaryContent = $summaryContent -replace '\[DATE\]', $archivedDate
    
    if ($Summary) {
        $summaryContent = $summaryContent -replace '\[Paragraph 1: What was the sprint goal and was it achieved\?\]', $Summary
    }
    
    $summaryContent | Set-Content $summaryFile -NoNewline
} else {
    $summaryContent = @"
# Sprint $sprintNumber Summary: $sprintName

**Duration**: $startDate - $endDate  
**Status**: Completed  
**Archived**: $archivedDate

## Executive Summary

$Summary

## Completed Features

$completedFeatures features completed.

See [features.md](./features.md) for details.
"@
    $summaryContent | Set-Content $summaryFile
}

# Create decisions.md
$decisionsFile = Join-Path $activeDir "decisions.md"
$archiveDecisionsFile = Join-Path $sprintArchiveDir "decisions.md"

if ((Test-Path $decisionsFile) -and ((Get-Item $decisionsFile).Length -gt 0)) {
    Copy-Item $decisionsFile $archiveDecisionsFile
} else {
    $decisionsContent = @"
# Sprint $sprintNumber Decisions

## Key Decisions

[Extract key decisions from feature specs]

## Pivots & Course Corrections

[Document any pivots that occurred during the sprint]
"@
    $decisionsContent | Set-Content $archiveDecisionsFile
}

# Create retrospective template
$retroTemplate = Join-Path $repoRoot ".specify/templates/retrospective-template.md"
$retroFile = Join-Path $sprintArchiveDir "retrospective.md"

if (Test-Path $retroTemplate) {
    $retroContent = Get-Content $retroTemplate -Raw
    $retroContent = $retroContent -replace '\[NUMBER\]', $sprintNumber
    $retroContent = $retroContent -replace '\[NAME\]', $sprintName
    $retroContent = $retroContent -replace '\[START_DATE\]', $startDate
    $retroContent = $retroContent -replace '\[END_DATE\]', $endDate
    $retroContent = $retroContent -replace '\[DATE\]', $archivedDate
    $retroContent | Set-Content $retroFile -NoNewline
} else {
    $retroContent = @"
# Sprint $sprintNumber Retrospective

**Sprint**: $sprintName  
**Date**: $archivedDate  
**Duration**: $startDate - $endDate

Run ``/speckit.retrospective`` to conduct the retrospective.
"@
    $retroContent | Set-Content $retroFile
}

# Clean up active directory
Remove-Item (Join-Path $activeDir "*") -Force -ErrorAction SilentlyContinue

# Output result
if ($Json) {
    $result = @{
        success = $true
        sprint_number = $sprintNumber
        sprint_name = $sprintName
        archive_dir = $sprintArchiveDir
        completed_features = $completedFeatures
        files_created = @(
            $summaryFile,
            $archiveDecisionsFile,
            (Join-Path $sprintArchiveDir "features.md"),
            $retroFile
        )
    }
    $result | ConvertTo-Json
} else {
    Write-Host "✅ Sprint $sprintNumber archived successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Location: $sprintArchiveDir"
    Write-Host ""
    Write-Host "Summary:"
    Write-Host "  - Features completed: $completedFeatures"
    Write-Host ""
    Write-Host "Files created:"
    Write-Host "  - summary.md - High-level sprint summary"
    Write-Host "  - decisions.md - Key decisions and pivots"
    Write-Host "  - features.md - Feature list with links"
    Write-Host "  - retrospective.md - Retrospective template"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Review summary.md for accuracy"
    Write-Host "  2. Run '/speckit.retrospective' to conduct retrospective"
    Write-Host "  3. Run '/speckit.sprint start' to begin next sprint"
}
