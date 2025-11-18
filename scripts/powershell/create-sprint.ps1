#!/usr/bin/env pwsh

param(
    [switch]$Json,
    [string]$Duration = "2w",
    [string]$Goal = "",
    [string]$Criteria = "",
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$SprintNameParts
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

# Get sprint name from remaining args
$sprintName = $SprintNameParts -join " "

if ([string]::IsNullOrWhiteSpace($sprintName)) {
    Write-Error "Sprint name is required`nUsage: create-sprint.ps1 [-Json] [-Duration 2w] 'Sprint Name'"
    exit 1
}

# Check if active sprint already exists
$activeDir = Join-Path $repoRoot ".specify/sprints/active"
$sprintFile = Join-Path $activeDir "sprint.md"

if (Test-Path $sprintFile) {
    Write-Error "Active sprint already exists at $activeDir`nComplete the current sprint with '/speckit.sprint complete' or '/speckit.archive' first"
    exit 1
}

# Determine next sprint number
$archiveDir = Join-Path $repoRoot ".specify/sprints/archive"
$sprintNumber = 1

if (Test-Path $archiveDir) {
    $sprintDirs = Get-ChildItem -Path $archiveDir -Directory -Filter "sprint-*" -ErrorAction SilentlyContinue
    $sprintNumber = $sprintDirs.Count + 1
}

# Format sprint number with leading zeros
$sprintNumFormatted = "{0:D3}" -f $sprintNumber

# Use provided goal and criteria (passed as parameters)
$sprintGoal = $Goal
$successCriteria = $Criteria

# Calculate dates
$startDate = Get-Date -Format "yyyy-MM-dd"
$durationText = ""
$endDate = ""
$numWeeks = 2

switch -Regex ($Duration) {
    "^1w|1week$" {
        $endDate = (Get-Date).AddDays(7).ToString("yyyy-MM-dd")
        $durationText = "1 week"
        $numWeeks = 1
    }
    "^2w|2weeks$" {
        $endDate = (Get-Date).AddDays(14).ToString("yyyy-MM-dd")
        $durationText = "2 weeks"
        $numWeeks = 2
    }
    "^3w|3weeks$" {
        $endDate = (Get-Date).AddDays(21).ToString("yyyy-MM-dd")
        $durationText = "3 weeks"
        $numWeeks = 3
    }
    "^4w|4weeks|1m|1month$" {
        $endDate = (Get-Date).AddDays(28).ToString("yyyy-MM-dd")
        $durationText = "4 weeks"
        $numWeeks = 4
    }
    default {
        Write-Warning "Unknown duration format '$Duration', defaulting to 2 weeks"
        $endDate = (Get-Date).AddDays(14).ToString("yyyy-MM-dd")
        $durationText = "2 weeks"
        $numWeeks = 2
    }
}

$createdDate = Get-Date -Format "yyyy-MM-dd"

# Generate sprint backlog weeks
$backlogWeeks = ""
for ($i = 1; $i -le $numWeeks; $i++) {
    $backlogWeeks += "### Week $i`n"
    $backlogWeeks += "[Add tasks for week $i]"
    if ($i -lt $numWeeks) {
        $backlogWeeks += "`n`n"
    }
}

# Create active sprint directory
New-Item -ItemType Directory -Path $activeDir -Force | Out-Null

# Copy sprint template
$templateFile = Join-Path $repoRoot ".specify/templates/sprint-template.md"
$sprintFile = Join-Path $activeDir "sprint.md"

if (-not (Test-Path $templateFile)) {
    Write-Error "Sprint template not found at $templateFile"
    exit 1
}

# Copy and replace placeholders
$content = Get-Content $templateFile -Raw
$content = $content -replace '\[NUMBER\]', $sprintNumFormatted
$content = $content -replace '\[NAME\]', $sprintName
$content = $content -replace '\[DURATION\]', $durationText
$content = $content -replace '\[START_DATE\]', $startDate
$content = $content -replace '\[END_DATE\]', $endDate
$content = $content -replace '\[DATE\]', $createdDate
$content = $content -replace '\$ARGUMENTS', $sprintName
$content = $content -replace '\[SPRINT_BACKLOG_WEEKS\]', $backlogWeeks

# Replace goal and success criteria if provided
if ($sprintGoal) {
    $content = $content -replace '\[To be defined - use /speckit\.clarify to set sprint goal\]', $sprintGoal
}

if ($successCriteria) {
    # Convert pipe-separated criteria to markdown list
    $criteriaArray = $successCriteria -split '\|'
    $formattedCriteria = ($criteriaArray | ForEach-Object { "- [ ] $_" }) -join "`n"
    $content = $content -replace '- \[ \] \[To be defined - use /speckit\.clarify to set success criteria\]', $formattedCriteria
}

$content | Set-Content $sprintFile -NoNewline

# Create backlog.md
$backlogContent = @"
# Sprint $sprintNumFormatted Backlog

## Features

No features added yet. Use ``/speckit.sprint add <feature-id>`` to add features.

## Notes

[Sprint planning notes]
"@
$backlogContent | Set-Content (Join-Path $activeDir "backlog.md")

# Create decisions.md
$decisionsContent = @"
# Sprint $sprintNumFormatted Decisions

Document key decisions made during this sprint.

## Decision Log

No decisions recorded yet.
"@
$decisionsContent | Set-Content (Join-Path $activeDir "decisions.md")

# Output result
if ($Json) {
    $result = @{
        success = $true
        sprint_number = $sprintNumFormatted
        sprint_name = $sprintName
        duration = $durationText
        start_date = $startDate
        end_date = $endDate
        active_dir = $activeDir
        files_created = @(
            $sprintFile,
            (Join-Path $activeDir "backlog.md"),
            (Join-Path $activeDir "decisions.md")
        )
    }
    $result | ConvertTo-Json
} else {
    Write-Host "✅ Sprint $sprintNumFormatted created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Sprint: $sprintName"
    Write-Host "Duration: $durationText ($startDate - $endDate)"
    Write-Host "Location: $activeDir"
    Write-Host ""
    Write-Host "Files created:"
    Write-Host "  - sprint.md"
    Write-Host "  - backlog.md"
    Write-Host "  - decisions.md"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Add features: /speckit.sprint add <feature-id>"
    Write-Host "  2. Define sprint goals in sprint.md"
    Write-Host "  3. Start working on features"
}
