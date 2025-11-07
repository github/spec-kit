#!/usr/bin/env pwsh

# Project Analysis Script (PowerShell)
#
# This script performs comprehensive project analysis against all SpecKit specifications
# to verify whether the project meets defined expectations.
#
# It also supports Universal Adoption features: discovering existing projects in any codebase.
#
# Usage: ./project-analysis.ps1 [OPTIONS]
#
# OPTIONS:
#   -Json               Output in JSON format
#   -CheckPatterns      Enable code pattern analysis (Security, DRY, KISS, SOLID)
#   -Discover           Discover all projects in repository (Universal Adoption)
#   -Cached             Use cached discovery results (0 tokens!)
#   -Force              Force rescan, ignore cache
#   -Help, -h           Show help message

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$CheckPatterns,
    [switch]$Discover,
    [switch]$Cached,
    [switch]$Force,
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
  -Discover           Discover all projects in repository (Universal Adoption)
  -Cached             Use cached discovery results (0 tokens!)
  -Force              Force rescan, ignore cache
  -Help, -h           Show this help message

EXAMPLES:
  # Basic project analysis (existing specs)
  .\project-analysis.ps1 -Json

  # Analysis with pattern checking
  .\project-analysis.ps1 -Json -CheckPatterns

  # Discover all projects (Universal Adoption)
  .\project-analysis.ps1 -Discover -Json

  # Use cached discovery (0 tokens!)
  .\project-analysis.ps1 -Discover -Cached -Json

  # Force rescan
  .\project-analysis.ps1 -Discover -Force -Json

"@
    exit 0
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get repository root
$repoRoot = Get-RepoRoot

#region Universal Adoption - Project Discovery Functions

function Get-ProjectIndicators {
    <#
    .SYNOPSIS
    Returns list of file indicators for different project types
    #>
    return @(
        @{ Pattern = "package.json"; Type = "nodejs"; Priority = 1 }
        @{ Pattern = "requirements.txt"; Type = "python"; Priority = 1 }
        @{ Pattern = "pyproject.toml"; Type = "python"; Priority = 1 }
        @{ Pattern = "go.mod"; Type = "go"; Priority = 1 }
        @{ Pattern = "Cargo.toml"; Type = "rust"; Priority = 1 }
        @{ Pattern = "pom.xml"; Type = "java"; Priority = 1 }
        @{ Pattern = "build.gradle"; Type = "java"; Priority = 1 }
        @{ Pattern = "*.csproj"; Type = "csharp"; Priority = 1 }
        @{ Pattern = "*.sln"; Type = "csharp"; Priority = 2 }
        @{ Pattern = "Gemfile"; Type = "ruby"; Priority = 1 }
        @{ Pattern = "composer.json"; Type = "php"; Priority = 1 }
        @{ Pattern = "CMakeLists.txt"; Type = "cpp"; Priority = 1 }
    )
}

function Get-ExcludedDirectories {
    <#
    .SYNOPSIS
    Returns list of directories to exclude from discovery
    #>
    return @(
        "node_modules",
        "venv",
        ".venv",
        "env",
        ".env",
        ".git",
        "build",
        "dist",
        "target",
        "__pycache__",
        ".next",
        ".nuxt",
        "bin",
        "obj",
        "packages",
        ".speckit"
    )
}

function Test-PathExcluded {
    param(
        [string]$Path,
        [string[]]$ExcludePatterns
    )

    foreach ($pattern in $ExcludePatterns) {
        if ($Path -match [regex]::Escape($pattern)) {
            return $true
        }
    }
    return $false
}

function Get-CacheHash {
    param([string]$RepoRoot)

    <#
    .SYNOPSIS
    Compute hash of indicator files for cache invalidation
    #>

    $indicators = Get-ProjectIndicators
    $excludePatterns = Get-ExcludedDirectories

    $allFiles = @()
    foreach ($indicator in $indicators) {
        $found = Get-ChildItem -Path $RepoRoot -Filter $indicator.Pattern -Recurse -File -ErrorAction SilentlyContinue `
            | Where-Object { -not (Test-PathExcluded -Path $_.FullName -ExcludePatterns $excludePatterns) } `
            | Select-Object -ExpandProperty FullName

        $allFiles += $found
    }

    if ($allFiles.Count -eq 0) {
        return "empty"
    }

    # Sort and join for consistent hashing
    $hashInput = ($allFiles | Sort-Object) -join "`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($hashInput)
    $stream = [System.IO.MemoryStream]::new($bytes)
    $hash = Get-FileHash -InputStream $stream -Algorithm MD5
    $stream.Dispose()

    return $hash.Hash
}

function Get-CachedDiscovery {
    param(
        [string]$RepoRoot,
        [bool]$ForceRescan
    )

    <#
    .SYNOPSIS
    Load cached discovery results if valid
    #>

    $cacheFile = Join-Path $RepoRoot ".speckit" "cache" "discovery.json"

    if ($ForceRescan) {
        Write-Verbose "Force rescan requested, ignoring cache"
        return $null
    }

    if (-not (Test-Path $cacheFile)) {
        Write-Verbose "No cache file found"
        return $null
    }

    try {
        $cached = Get-Content $cacheFile -Raw | ConvertFrom-Json

        # Validate cache hash
        $currentHash = Get-CacheHash -RepoRoot $RepoRoot
        if ($cached.cache_hash -eq $currentHash) {
            Write-Host "✓ Using cached discovery (0 tokens!)" -ForegroundColor Green
            Write-Verbose "Cache hit! Last scan: $($cached.scanned_at)"
            return $cached
        } else {
            Write-Verbose "Cache invalid (file structure changed)"
            return $null
        }
    } catch {
        Write-Verbose "Failed to load cache: $_"
        return $null
    }
}

function Save-DiscoveryCache {
    param(
        [string]$RepoRoot,
        [PSCustomObject]$Discovery
    )

    <#
    .SYNOPSIS
    Save discovery results to cache
    #>

    $cacheDir = Join-Path $RepoRoot ".speckit" "cache"
    $cacheFile = Join-Path $cacheDir "discovery.json"

    # Create cache directory if it doesn't exist
    if (-not (Test-Path $cacheDir)) {
        New-Item -ItemType Directory -Path $cacheDir -Force | Out-Null
    }

    # Save cache
    $Discovery | ConvertTo-Json -Depth 10 | Out-File $cacheFile -Encoding UTF8

    Write-Verbose "Discovery cached to: $cacheFile"
}

function Find-Projects {
    param([string]$RepoRoot)

    <#
    .SYNOPSIS
    Discover all projects in repository (metadata-only, no code reading)
    #>

    Write-Verbose "Scanning repository: $RepoRoot"

    $indicators = Get-ProjectIndicators
    $excludePatterns = Get-ExcludedDirectories
    $projects = @()
    $projectDirs = @{}  # Track unique project directories

    foreach ($indicator in $indicators) {
        Write-Verbose "Searching for: $($indicator.Pattern)"

        $found = Get-ChildItem -Path $RepoRoot -Filter $indicator.Pattern -Recurse -File -ErrorAction SilentlyContinue `
            | Where-Object {
                $path = $_.FullName
                $excluded = Test-PathExcluded -Path $path -ExcludePatterns $excludePatterns
                -not $excluded
            }

        foreach ($file in $found) {
            $projectPath = $file.DirectoryName
            $relativePath = $projectPath.Replace($RepoRoot, "").TrimStart('\', '/')

            # Generate project ID (normalize path)
            $projectId = $relativePath -replace '[\\/]', '-' -replace '^-', '' -replace '-$', ''
            if ([string]::IsNullOrWhiteSpace($projectId)) {
                $projectId = "root"
            }

            # Check if we've already found this project
            if ($projectDirs.ContainsKey($projectPath)) {
                # Update if this indicator has higher priority
                $existing = $projectDirs[$projectPath]
                if ($indicator.Priority -lt $existing.Priority) {
                    $projectDirs[$projectPath] = @{
                        Type = $indicator.Type
                        Indicator = $file.Name
                        Priority = $indicator.Priority
                    }
                }
            } else {
                $projectDirs[$projectPath] = @{
                    Type = $indicator.Type
                    Indicator = $file.Name
                    Priority = $indicator.Priority
                }
            }
        }
    }

    # Convert to project objects
    foreach ($projectPath in $projectDirs.Keys) {
        $info = $projectDirs[$projectPath]
        $relativePath = $projectPath.Replace($RepoRoot, "").TrimStart('\', '/')

        # Generate project ID
        $projectId = $relativePath -replace '[\\/]', '-' -replace '^-', '' -replace '-$', ''
        if ([string]::IsNullOrWhiteSpace($projectId)) {
            $projectId = "root"
        }

        # Generate project name (from directory name)
        $projectName = Split-Path $projectPath -Leaf
        if ([string]::IsNullOrWhiteSpace($projectName)) {
            $projectName = "Root Project"
        }

        # Get project metadata (size, file count)
        $files = Get-ChildItem -Path $projectPath -Recurse -File -ErrorAction SilentlyContinue `
            | Where-Object {
                -not (Test-PathExcluded -Path $_.FullName -ExcludePatterns $excludePatterns)
            }

        $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
        $fileCount = $files.Count

        # Get last modified time
        $lastModified = ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
        if (-not $lastModified) {
            $lastModified = Get-Date
        }

        # Classify project type (basic heuristic)
        $projectType = "unknown"
        if (Test-Path (Join-Path $projectPath "src" "components")) {
            $projectType = "frontend"
        } elseif (Test-Path (Join-Path $projectPath "api")) {
            $projectType = "backend-api"
        } elseif (Test-Path (Join-Path $projectPath "cmd")) {
            $projectType = "cli"
        } elseif ($info.Indicator -match "\.sln$|\.csproj$") {
            if (Test-Path (Join-Path $projectPath "Controllers")) {
                $projectType = "backend-api"
            }
        } elseif ($projectPath -match "service") {
            $projectType = "backend-api"
        } else {
            # Default based on indicator type
            switch ($info.Type) {
                "nodejs" { $projectType = "unknown" }  # Could be frontend or backend
                "python" { $projectType = "backend-api" }
                "go" { $projectType = "backend-api" }
                "rust" { $projectType = "cli" }
                "csharp" { $projectType = "backend-api" }
                default { $projectType = "unknown" }
            }
        }

        $projects += [PSCustomObject]@{
            id = $projectId
            name = $projectName
            path = $relativePath
            abs_path = $projectPath
            type = $projectType
            technology = $info.Type
            framework = "unknown"  # Will be detected in Phase 2
            indicator_file = $info.Indicator
            size_bytes = $totalSize
            file_count = $fileCount
            last_modified = $lastModified.ToString("o")
        }
    }

    Write-Host "Found $($projects.Count) projects" -ForegroundColor Green

    return $projects
}

function Invoke-ProjectDiscovery {
    param(
        [string]$RepoRoot,
        [bool]$UseCache,
        [bool]$ForceRescan
    )

    <#
    .SYNOPSIS
    Main discovery function - checks cache or performs scan
    #>

    # Check cache first (unless force)
    if ($UseCache -and -not $ForceRescan) {
        $cached = Get-CachedDiscovery -RepoRoot $RepoRoot -ForceRescan $ForceRescan
        if ($cached) {
            return $cached
        }
    }

    Write-Host "Scanning repository..." -ForegroundColor Cyan

    # Perform discovery
    $projects = Find-Projects -RepoRoot $RepoRoot

    # Compute cache hash
    $cacheHash = Get-CacheHash -RepoRoot $RepoRoot

    # Build discovery result
    $discovery = [PSCustomObject]@{
        version = "1.0"
        scanned_at = (Get-Date).ToString("o")
        repo_root = $RepoRoot
        cache_hash = $cacheHash
        total_projects = $projects.Count
        projects = $projects
    }

    # Cache results
    Save-DiscoveryCache -RepoRoot $RepoRoot -Discovery $discovery

    return $discovery
}

function Format-DiscoveryReport {
    param([PSCustomObject]$Discovery)

    <#
    .SYNOPSIS
    Format discovery results as human-readable report
    #>

    Write-Output ""
    Write-Output "# Project Discovery Report"
    Write-Output ""
    Write-Output "**Scanned:** $($Discovery.repo_root)"
    Write-Output "**Cache:** $(if ($Discovery.scanned_at) { 'Fresh scan' } else { 'Using cached' })"
    Write-Output "**Projects Found:** $($Discovery.total_projects)"
    Write-Output ""
    Write-Output "## Quick Summary"
    Write-Output ""
    Write-Output "| # | Name | Type | Tech | Path | Size |"
    Write-Output "|---|------|------|------|------|------|"

    $i = 1
    foreach ($project in $Discovery.projects) {
        $sizeKB = [math]::Round($project.size_bytes / 1024, 0)
        $path = if ($project.path) { $project.path } else { "(root)" }
        Write-Output "| $i | $($project.name) | $($project.type) | $($project.technology) | $path | ${sizeKB}KB |"
        $i++
    }

    Write-Output ""
    Write-Output "## Next Steps"
    Write-Output ""
    Write-Output "``````powershell"
    Write-Output "# View detailed info for a project"
    Write-Output "/speckit.project-analysis --project=<project-id>"
    Write-Output ""
    Write-Output "# Onboard all projects"
    Write-Output "/speckit.onboard --all"
    Write-Output ""
    Write-Output "# Onboard specific projects"
    Write-Output "/speckit.onboard --projects=<id1>,<id2>"
    Write-Output "``````"
    Write-Output ""

    if (-not $Discovery.cache_hash) {
        Write-Output "**Note:** Run again with -Cached to use zero tokens!"
        Write-Output ""
    }
}

#endregion

# Main execution logic
if ($Discover) {
    # Universal Adoption: Discover existing projects
    Write-Verbose "Running in discovery mode"

    $discovery = Invoke-ProjectDiscovery -RepoRoot $repoRoot -UseCache $Cached.IsPresent -ForceRescan $Force.IsPresent

    if ($Json) {
        $discovery | ConvertTo-Json -Compress -Depth 10
    } else {
        Format-DiscoveryReport -Discovery $discovery
    }

    exit 0
}

# Standard mode: Analyze existing specs

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
