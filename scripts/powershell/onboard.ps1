#!/usr/bin/env pwsh

# Spec-Kit Onboarding Script (PowerShell)
#
# Phase 3: Non-Invasive Onboarding
#
# This script onboards existing projects discovered in Phase 1/2 by creating
# a parallel .speckit/ structure without modifying existing code.
#
# Usage: ./onboard.ps1 [OPTIONS]
#
# OPTIONS:
#   -All                Onboard all discovered projects
#   -Projects <ids>     Onboard specific projects (comma-separated IDs)
#   -FromDiscovery      Use discovery cache (.speckit/cache/discovery.json)
#   -ConstitutionType   Constitution type: universal, microservices, custom
#   -Force              Overwrite existing onboarding
#   -DryRun             Show what would be done without making changes
#   -Json               Output results in JSON format
#   -Help, -h           Show help message

[CmdletBinding()]
param(
    [switch]$All,
    [string]$Projects,
    [switch]$FromDiscovery,
    [string]$ConstitutionType = "universal",
    [switch]$Force,
    [switch]$DryRun,
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: onboard.ps1 [OPTIONS]

Onboard existing projects discovered in Phase 1/2 by creating a parallel
.speckit/ structure without modifying existing code.

OPTIONS:
  -All                Onboard all discovered projects
  -Projects <ids>     Onboard specific projects (comma-separated IDs)
  -FromDiscovery      Use discovery cache (.speckit/cache/discovery.json)
  -ConstitutionType   Constitution type: universal, microservices, custom
                      (default: universal)
  -Force              Overwrite existing onboarding
  -DryRun             Show what would be done without making changes
  -Json               Output results in JSON format
  -Help, -h           Show this help message

EXAMPLES:
  # Onboard all discovered projects
  .\onboard.ps1 -All -FromDiscovery

  # Onboard specific projects
  .\onboard.ps1 -Projects "api,frontend" -FromDiscovery

  # Dry run to see what would happen
  .\onboard.ps1 -All -FromDiscovery -DryRun

  # Use microservices constitution
  .\onboard.ps1 -All -FromDiscovery -ConstitutionType microservices

  # Force re-onboarding
  .\onboard.ps1 -All -FromDiscovery -Force

"@
    exit 0
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get repository root
$repoRoot = Get-RepoRoot

#region Helper Functions

function Initialize-SpeckitStructure {
    param([string]$RepoRoot)

    <#
    .SYNOPSIS
    Initialize .speckit/ and specs/ directory structure
    #>

    Write-Verbose "Initializing spec-kit structure"

    $structure = @(
        ".speckit",
        ".speckit/metadata",
        ".speckit/cache",
        "specs",
        "specs/projects"
    )

    foreach ($dir in $structure) {
        $fullPath = Join-Path $RepoRoot $dir
        if (-not (Test-Path $fullPath)) {
            if (-not $DryRun) {
                New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
                Write-Host "  Created: $dir" -ForegroundColor Green
            } else {
                Write-Host "  [DRY RUN] Would create: $dir" -ForegroundColor Cyan
            }
        } else {
            Write-Verbose "  Already exists: $dir"
        }
    }
}

function Get-DiscoveryResults {
    param([string]$RepoRoot)

    <#
    .SYNOPSIS
    Load discovery results from cache
    #>

    $cacheFile = Join-Path $RepoRoot ".speckit" "cache" "discovery.json"

    if (-not (Test-Path $cacheFile)) {
        throw "Discovery cache not found at: $cacheFile. Run project-analysis.ps1 -Discover first."
    }

    try {
        $discovery = Get-Content $cacheFile -Raw | ConvertFrom-Json
        Write-Verbose "Loaded discovery results: $($discovery.total_projects) projects"
        return $discovery
    } catch {
        throw "Failed to load discovery cache: $_"
    }
}

function Get-SpeckitConfig {
    param([string]$RepoRoot)

    <#
    .SYNOPSIS
    Load existing spec-kit configuration or create new one
    #>

    $configFile = Join-Path $RepoRoot ".speckit" "config.json"

    if (Test-Path $configFile) {
        try {
            $config = Get-Content $configFile -Raw | ConvertFrom-Json
            Write-Verbose "Loaded existing spec-kit configuration"
            return $config
        } catch {
            Write-Warning "Failed to load existing config: $_. Creating new one."
        }
    }

    # Create new configuration
    Write-Verbose "Creating new spec-kit configuration"

    $config = [PSCustomObject]@{
        version = "1.0"
        initialized_at = (Get-Date).ToString("o")
        repo_root = $RepoRoot
        discovery = [PSCustomObject]@{
            last_scan = $null
            total_projects = 0
            deep_analysis_enabled = $false
        }
        projects = @()
        constitution = [PSCustomObject]@{
            type = $ConstitutionType
            path = "constitution.md"
        }
        settings = [PSCustomObject]@{
            auto_discovery = $false
            deep_analysis_default = $false
            exclude_patterns = @()
            template_preference = "standard"
        }
    }

    return $config
}

function Save-SpeckitConfig {
    param(
        [string]$RepoRoot,
        [PSCustomObject]$Config
    )

    <#
    .SYNOPSIS
    Save spec-kit configuration
    #>

    $configFile = Join-Path $RepoRoot ".speckit" "config.json"

    if (-not $DryRun) {
        $Config | ConvertTo-Json -Depth 10 | Out-File $configFile -Encoding UTF8
        Write-Verbose "Saved spec-kit configuration to: $configFile"
    } else {
        Write-Host "  [DRY RUN] Would save config to: $configFile" -ForegroundColor Cyan
    }
}

function New-ProjectMetadata {
    param([PSCustomObject]$Project)

    <#
    .SYNOPSIS
    Generate metadata for an onboarded project
    #>

    $metadata = [PSCustomObject]@{
        id = $Project.id
        name = $Project.name
        path = $Project.path
        type = $Project.type
        technology = $Project.technology
        framework = if ($Project.framework) { $Project.framework } else { "unknown" }
        onboarded_at = (Get-Date).ToString("o")
        discovery_info = [PSCustomObject]@{
            size_bytes = $Project.size_bytes
            file_count = $Project.file_count
            last_modified = $Project.last_modified
            indicator_file = $Project.indicator_file
        }
    }

    # Add deep analysis info if available
    if ($Project.PSObject.Properties.Name -contains "runtime") {
        $metadata | Add-Member -NotePropertyName "runtime" -NotePropertyValue $Project.runtime
        $metadata | Add-Member -NotePropertyName "runtime_version" -NotePropertyValue $Project.runtime_version
        $metadata | Add-Member -NotePropertyName "build_tools" -NotePropertyValue $Project.build_tools
        $metadata | Add-Member -NotePropertyName "test_frameworks" -NotePropertyValue $Project.test_frameworks
        $metadata | Add-Member -NotePropertyName "key_dependencies" -NotePropertyValue $Project.key_dependencies
    }

    return $metadata
}

function Save-ProjectMetadata {
    param(
        [string]$RepoRoot,
        [PSCustomObject]$Metadata
    )

    <#
    .SYNOPSIS
    Save project metadata to .speckit/metadata/
    #>

    $metadataFile = Join-Path $RepoRoot ".speckit" "metadata" "$($Metadata.id).json"

    if (-not $DryRun) {
        $Metadata | ConvertTo-Json -Depth 10 | Out-File $metadataFile -Encoding UTF8
        Write-Verbose "  Saved metadata: $metadataFile"
    } else {
        Write-Host "  [DRY RUN] Would save metadata: $metadataFile" -ForegroundColor Cyan
    }

    return $metadataFile
}

function New-ProjectSpecDirectory {
    param(
        [string]$RepoRoot,
        [PSCustomObject]$Project
    )

    <#
    .SYNOPSIS
    Create spec directory for project
    #>

    $specDir = Join-Path $RepoRoot "specs" "projects" $Project.id

    if (Test-Path $specDir) {
        if ($Force) {
            Write-Warning "  Project spec directory already exists: $specDir (using -Force)"
        } else {
            Write-Warning "  Project spec directory already exists: $specDir (skipping, use -Force to overwrite)"
            return $null
        }
    }

    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $specDir -Force | Out-Null
        Write-Verbose "  Created spec directory: $specDir"
    } else {
        Write-Host "  [DRY RUN] Would create spec directory: $specDir" -ForegroundColor Cyan
    }

    return "projects/$($Project.id)"
}

function Copy-ConstitutionTemplate {
    param(
        [string]$RepoRoot,
        [string]$Type
    )

    <#
    .SYNOPSIS
    Copy constitution template to specs/
    #>

    $targetFile = Join-Path $RepoRoot "specs" "constitution.md"

    if (Test-Path $targetFile) {
        Write-Verbose "Constitution already exists, skipping"
        return
    }

    # Determine source template
    $templateFile = switch ($Type) {
        "microservices" {
            Join-Path $RepoRoot "templates" "microservices" "constitution-microservices.md"
        }
        "universal" {
            # Universal constitution (to be created)
            Join-Path $RepoRoot "templates" "constitution-universal.md"
        }
        default {
            $null
        }
    }

    if ($templateFile -and (Test-Path $templateFile)) {
        if (-not $DryRun) {
            Copy-Item $templateFile $targetFile
            Write-Host "  Created constitution: specs/constitution.md ($Type)" -ForegroundColor Green
        } else {
            Write-Host "  [DRY RUN] Would copy constitution: $templateFile -> specs/constitution.md" -ForegroundColor Cyan
        }
    } else {
        # Create basic constitution
        if (-not $DryRun) {
            $basicConstitution = @"
# Platform Constitution

**Purpose:** Define platform-wide principles, standards, and best practices.

---

## Core Principles

1. **Consistency:** Maintain consistent patterns across all projects
2. **Simplicity:** Prefer simple, maintainable solutions
3. **Documentation:** All changes must be documented
4. **Testing:** All code must have appropriate test coverage
5. **Security:** Security is a top priority

---

## Technical Standards

### Code Quality
- Follow language-specific style guides
- Maintain test coverage above 80%
- Use linters and formatters consistently

### Architecture
- Prefer composition over inheritance
- Keep components loosely coupled
- Design for testability

### Version Control
- Use semantic versioning
- Write meaningful commit messages
- Use feature branches

---

## Review Process

All changes must:
1. Pass automated tests
2. Be reviewed by at least one team member
3. Follow the constitution guidelines

---

**Status:** Initial version (customize for your needs)
"@
            $basicConstitution | Out-File $targetFile -Encoding UTF8
            Write-Host "  Created basic constitution: specs/constitution.md" -ForegroundColor Green
        } else {
            Write-Host "  [DRY RUN] Would create basic constitution: specs/constitution.md" -ForegroundColor Cyan
        }
    }
}

function New-ProjectReadme {
    param(
        [string]$RepoRoot,
        [PSCustomObject]$Project,
        [string]$SpecDir
    )

    <#
    .SYNOPSIS
    Create README.md for project's spec directory
    #>

    $readmePath = Join-Path $RepoRoot "specs" $SpecDir "README.md"

    if (Test-Path $readmePath) {
        Write-Verbose "  README already exists, skipping"
        return
    }

    $readme = @"
# $($Project.name)

**Type:** $($Project.type)
**Technology:** $($Project.technology)
**Framework:** $($Project.framework)
**Location:** ``$($Project.path)``

---

## Overview

This directory contains specifications for the **$($Project.name)** project.

$(if ($Project.framework -and $Project.framework -ne "unknown") {
"This is a **$($Project.framework)** $($Project.type) project."
} else {
"This is a $($Project.type) project."
})

---

## Project Structure

```
$($Project.path)/
$(if ($Project.indicator_file) { "  └── $($Project.indicator_file)  (entry point)" } else { "" })
```

---

## Features

Features for this project are organized as:

```
001-existing-code/     - Reverse-engineered from existing implementation
002-new-feature/       - New features developed with spec-kit
003-another-feature/   - Additional features
```

Each feature directory contains:
- ``spec.md`` - Feature specification
- ``plan.md`` - Implementation plan
- ``tasks.md`` - Task breakdown
- ``ai-doc.md`` - AI-optimized documentation

---

## Getting Started

### 1. Review Existing Code

The existing codebase is located at:
```
$($Project.path)
```

### 2. Create New Feature

To add a new feature:

``````bash
# Create feature directory
cd specs/projects/$($Project.id)
mkdir 002-my-feature

# Generate spec
/speckit.specify

# Generate plan
/speckit.plan

# Implement
/speckit.implement
``````

---

## Quick Reference

- **Project ID:** ``$($Project.id)``
- **Size:** $([math]::Round($Project.size_bytes / 1024, 1)) KB ($($Project.file_count) files)
$(if ($Project.runtime_version) { "- **Runtime:** $($Project.runtime) $($Project.runtime_version)" } else { "" })
$(if ($Project.build_tools -and $Project.build_tools.Count -gt 0) { "- **Build Tools:** $($Project.build_tools -join ', ')" } else { "" })
$(if ($Project.test_frameworks -and $Project.test_frameworks.Count -gt 0) { "- **Test Frameworks:** $($Project.test_frameworks -join ', ')" } else { "" })

---

**Status:** Onboarded - Ready for spec-driven development
"@

    if (-not $DryRun) {
        $readme | Out-File $readmePath -Encoding UTF8
        Write-Verbose "  Created README: $readmePath"
    } else {
        Write-Host "  [DRY RUN] Would create README: $readmePath" -ForegroundColor Cyan
    }
}

function Invoke-ProjectOnboarding {
    param(
        [string]$RepoRoot,
        [PSCustomObject]$Project,
        [PSCustomObject]$Config
    )

    <#
    .SYNOPSIS
    Onboard a single project
    #>

    Write-Host ""
    Write-Host "Onboarding: $($Project.name)" -ForegroundColor Cyan
    Write-Host "  ID: $($Project.id)" -ForegroundColor Gray
    Write-Host "  Path: $($Project.path)" -ForegroundColor Gray
    Write-Host "  Type: $($Project.type)" -ForegroundColor Gray
    Write-Host "  Technology: $($Project.technology)" -ForegroundColor Gray
    if ($Project.framework -and $Project.framework -ne "unknown") {
        Write-Host "  Framework: $($Project.framework)" -ForegroundColor Gray
    }

    # Check if already onboarded
    $existing = $Config.projects | Where-Object { $_.id -eq $Project.id }
    if ($existing -and -not $Force) {
        Write-Warning "  Already onboarded (use -Force to re-onboard)"
        return $false
    }

    # Create spec directory
    $specDir = New-ProjectSpecDirectory -RepoRoot $RepoRoot -Project $Project
    if (-not $specDir) {
        return $false
    }

    # Generate metadata
    $metadata = New-ProjectMetadata -Project $Project
    $metadataFile = Save-ProjectMetadata -RepoRoot $RepoRoot -Metadata $metadata

    # Create README
    New-ProjectReadme -RepoRoot $RepoRoot -Project $Project -SpecDir $specDir

    # Add to config
    $projectConfig = [PSCustomObject]@{
        id = $Project.id
        name = $Project.name
        path = $Project.path
        type = $Project.type
        technology = $Project.technology
        framework = if ($Project.framework) { $Project.framework } else { "unknown" }
        onboarded_at = (Get-Date).ToString("o")
        spec_dir = $specDir
        metadata_file = "metadata/$($Project.id).json"
        constitution = "constitution.md"
        templates = @()
        status = "onboarded"
    }

    # Remove existing if force
    if ($existing -and $Force) {
        $Config.projects = @($Config.projects | Where-Object { $_.id -ne $Project.id })
    }

    $Config.projects += $projectConfig

    Write-Host "  ✓ Onboarded successfully" -ForegroundColor Green

    return $true
}

#endregion

#region Main Execution

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host " Spec-Kit Onboarding (Phase 3)" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "** DRY RUN MODE - No changes will be made **" -ForegroundColor Yellow
    Write-Host ""
}

# Step 1: Initialize structure
Write-Host "Step 1: Initializing spec-kit structure..." -ForegroundColor Cyan
Initialize-SpeckitStructure -RepoRoot $repoRoot

# Step 2: Load discovery results
Write-Host ""
Write-Host "Step 2: Loading discovery results..." -ForegroundColor Cyan
if (-not $FromDiscovery) {
    throw "Discovery results required. Use -FromDiscovery flag."
}

$discovery = Get-DiscoveryResults -RepoRoot $repoRoot
Write-Host "  Found $($discovery.total_projects) projects" -ForegroundColor Green

# Step 3: Load or create configuration
Write-Host ""
Write-Host "Step 3: Loading configuration..." -ForegroundColor Cyan
$config = Get-SpeckitConfig -RepoRoot $repoRoot

# Update discovery info
$config.discovery.last_scan = $discovery.scanned_at
$config.discovery.total_projects = $discovery.total_projects
$config.discovery.deep_analysis_enabled = $discovery.projects[0].PSObject.Properties.Name -contains "runtime"

# Step 4: Create constitution
Write-Host ""
Write-Host "Step 4: Setting up constitution..." -ForegroundColor Cyan
Copy-ConstitutionTemplate -RepoRoot $repoRoot -Type $ConstitutionType

# Step 5: Select projects to onboard
Write-Host ""
Write-Host "Step 5: Selecting projects..." -ForegroundColor Cyan
$projectsToOnboard = @()

if ($All) {
    $projectsToOnboard = $discovery.projects
    Write-Host "  Selected: All $($projectsToOnboard.Count) projects" -ForegroundColor Green
} elseif ($Projects) {
    $selectedIds = $Projects -split ','
    foreach ($id in $selectedIds) {
        $project = $discovery.projects | Where-Object { $_.id -eq $id.Trim() }
        if ($project) {
            $projectsToOnboard += $project
        } else {
            Write-Warning "  Project not found: $id"
        }
    }
    Write-Host "  Selected: $($projectsToOnboard.Count) projects" -ForegroundColor Green
} else {
    throw "Must specify -All or -Projects <ids>"
}

# Step 6: Onboard projects
Write-Host ""
Write-Host "Step 6: Onboarding projects..." -ForegroundColor Cyan

$successCount = 0
$skipCount = 0

foreach ($project in $projectsToOnboard) {
    $result = Invoke-ProjectOnboarding -RepoRoot $repoRoot -Project $project -Config $config
    if ($result) {
        $successCount++
    } else {
        $skipCount++
    }
}

# Step 7: Save configuration
Write-Host ""
Write-Host "Step 7: Saving configuration..." -ForegroundColor Cyan
Save-SpeckitConfig -RepoRoot $repoRoot -Config $config

# Summary
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host " Onboarding Complete!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results:" -ForegroundColor Green
Write-Host "  ✓ Successfully onboarded: $successCount" -ForegroundColor Green
if ($skipCount -gt 0) {
    Write-Host "  ⊘ Skipped: $skipCount" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Structure created:" -ForegroundColor Green
Write-Host "  .speckit/config.json        - Configuration" -ForegroundColor Gray
Write-Host "  .speckit/metadata/          - Project metadata" -ForegroundColor Gray
Write-Host "  specs/constitution.md       - Platform principles" -ForegroundColor Gray
Write-Host "  specs/projects/*/           - Project specifications" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review specs/constitution.md and customize" -ForegroundColor Gray
Write-Host "  2. Explore specs/projects/{project-id}/ for each project" -ForegroundColor Gray
Write-Host "  3. Use /speckit.specify to create new features" -ForegroundColor Gray
Write-Host "  4. Run Phase 4 reverse engineering: /speckit.reverse-engineer" -ForegroundColor Gray
Write-Host ""

if ($Json) {
    $result = [PSCustomObject]@{
        success = $true
        onboarded = $successCount
        skipped = $skipCount
        total = $projectsToOnboard.Count
        config_file = ".speckit/config.json"
        constitution = "specs/constitution.md"
        projects = $config.projects | Select-Object id, name, spec_dir, status
    }

    $result | ConvertTo-Json -Depth 10
}

#endregion
