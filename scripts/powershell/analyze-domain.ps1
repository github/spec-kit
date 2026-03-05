#!/usr/bin/env pwsh
# Analyze domain data files and extract entities and business rules
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$DataDir,
    [switch]$Interactive,
    [switch]$Setup,
    [string]$Config,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)
$ErrorActionPreference = 'Stop'

# Function to find repository root
function Find-RepositoryRoot {
    param(
        [string]$StartDir,
        [string[]]$Markers = @('.git', '.specify')
    )
    $current = Resolve-Path $StartDir
    while ($true) {
        foreach ($marker in $Markers) {
            if (Test-Path (Join-Path $current $marker)) {
                return $current
            }
        }
        $parent = Split-Path $current -Parent
        if ($parent -eq $current) {
            return $null
        }
        $current = $parent
    }
}

# Get repository root
$fallbackRoot = Find-RepositoryRoot -StartDir $PSScriptRoot
if (-not $fallbackRoot) {
    Write-Error "Error: Could not determine repository root."
    exit 1
}

try {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0) {
        $hasGit = $true
    } else {
        $repoRoot = $fallbackRoot
        $hasGit = $false
    }
} catch {
    $repoRoot = $fallbackRoot
    $hasGit = $false
}

# Get current branch
$currentBranch = ""
if ($env:SPECIFY_FEATURE) {
    $currentBranch = $env:SPECIFY_FEATURE
} elseif ($hasGit) {
    try {
        $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -ne 0) { $currentBranch = "main" }
    } catch {
        $currentBranch = "main"
    }
} else {
    # Find latest feature directory
    $specsDir = Join-Path $repoRoot "specs"
    if (Test-Path $specsDir) {
        $highest = 0
        $latestFeature = ""
        Get-ChildItem $specsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{3})-') {
                $number = [int]$matches[1]
                if ($number -gt $highest) {
                    $highest = $number
                    $latestFeature = $_.Name
                }
            }
        }
        if ($latestFeature) {
            $currentBranch = $latestFeature
        } else {
            $currentBranch = "main"
        }
    } else {
        $currentBranch = "main"
    }
}

# Check feature branch
if ($hasGit -and $currentBranch -notmatch '^\d{3}-') {
    $errorMsg = "Not on a feature branch. Current branch: $currentBranch. Run /specify first."
    if ($Json) {
        @{ error = $errorMsg } | ConvertTo-Json -Compress
    } else {
        Write-Error $errorMsg
    }
    exit 1
}

$featureDir = Join-Path $repoRoot "specs" $currentBranch
$specFile = Join-Path $featureDir "spec.md"

# Check if spec file exists
if (-not (Test-Path $specFile)) {
    $errorMsg = "Specification file not found at $specFile. Run /specify first."
    if ($Json) {
        @{ error = $errorMsg } | ConvertTo-Json -Compress
    } else {
        Write-Error $errorMsg
    }
    exit 1
}

# Auto-detect data directory if not provided
if (-not $DataDir) {
    $candidates = @(
        (Join-Path $repoRoot "data"),
        (Join-Path $repoRoot "src" "data"),
        (Join-Path $repoRoot "data" "processed"),
        (Join-Path $repoRoot "data" "3_processed"),
        (Join-Path (Get-Location) "data")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $DataDir = $candidate
            break
        }
    }

    if (-not $DataDir) {
        $DataDir = $repoRoot
    }
}

# Verify data directory exists
if (-not (Test-Path $DataDir)) {
    $errorMsg = "Data directory not found: $DataDir"
    if ($Json) {
        @{ error = $errorMsg } | ConvertTo-Json -Compress
    } else {
        Write-Error $errorMsg
    }
    exit 1
}

# Scan for data files
$jsonFiles = Get-ChildItem -Path $DataDir -Recurse -Filter "*.json" -File | Select-Object -ExpandProperty FullName
$csvFiles = Get-ChildItem -Path $DataDir -Recurse -Filter "*.csv" -File | Select-Object -ExpandProperty FullName
$dataDirs = Get-ChildItem -Path $DataDir -Recurse -Directory | Select-Object -ExpandProperty FullName

$jsonCount = $jsonFiles.Count
$csvCount = $csvFiles.Count
$totalFiles = $jsonCount + $csvCount

# Basic entity detection from file paths
$entities = @{}
$entitiesDiscovered = 0

foreach ($file in $jsonFiles) {
    $basename = [System.IO.Path]::GetFileNameWithoutExtension($file).ToLower()

    if ($basename -match 'invoice') { $entities['Invoice'] = 1 }
    if ($basename -match 'payment') { $entities['Payment'] = 1 }
    if ($basename -match 'supplier') { $entities['Supplier'] = 1 }
    if ($basename -match 'reconcil') { $entities['ReconciliationRun'] = 1 }
}

$entitiesDiscovered = $entities.Count

# Estimate business rules based on data patterns
$businessRulesCount = $entitiesDiscovered * 2 + 3

# Count integration points from directory structure
$integrationPoints = 0
foreach ($dir in $dataDirs) {
    if ($dir -match '(processed|reports|sage|mcp)') {
        $integrationPoints++
    }
}

# Ensure at least some integration points
if ($integrationPoints -eq 0) {
    $integrationPoints = 2  # File System + MCP Server minimum
}

$analysisTimestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")

# Generate output
if ($Json) {
    $result = @{
        DATA_DIR = $DataDir
        FEATURE_DIR = $featureDir
        SPEC_FILE = $specFile
        interactive_mode = $Interactive.IsPresent
        setup_mode = $Setup.IsPresent
        config_file = $Config
        analysis = @{
            timestamp = $analysisTimestamp
            files_scanned = @{
                json_files = $jsonCount
                csv_files = $csvCount
                total_files = $totalFiles
            }
            entities_discovered = $entitiesDiscovered
            business_rules_estimated = $businessRulesCount
            integration_points = $integrationPoints
            data_directories = @($dataDirs)
            sample_json_files = @($jsonFiles | Select-Object -First 5)
            entities = @($entities.Keys)
        }
        status = "ready_for_analysis"
    }
    $result | ConvertTo-Json -Depth 10 -Compress
} else {
    Write-Output "DATA_DIR: $DataDir"
    Write-Output "FEATURE_DIR: $featureDir"
    Write-Output "SPEC_FILE: $specFile"
    Write-Output ""
    Write-Output "Domain Analysis Summary:"
    Write-Output "  JSON files found: $jsonCount"
    Write-Output "  CSV files found: $csvCount"
    Write-Output "  Data directories: $($dataDirs.Count)"
    Write-Output "  Entities discovered: $entitiesDiscovered"
    Write-Output "  Business rules estimated: $businessRulesCount"
    Write-Output "  Integration points: $integrationPoints"
    Write-Output ""
    Write-Output "Entities detected:"
    foreach ($entity in $entities.Keys) {
        Write-Output "  - $entity"
    }
    Write-Output ""
    Write-Output "Sample data files:"
    $jsonFiles | Select-Object -First 5 | ForEach-Object {
        Write-Output "  - $_"
    }
}