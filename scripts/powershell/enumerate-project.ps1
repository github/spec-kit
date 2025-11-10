#!/usr/bin/env pwsh
#
# enumerate-project.ps1 - Enumerate all files in a project for AI analysis
#
# Usage:
#   ./enumerate-project.ps1 -Project PATH [-Output FILE] [-MaxSize BYTES]
#
# This script performs a full recursive scan of a project directory and outputs
# a JSON manifest of all files with metadata. AI will use this to decide what
# to include/exclude and how to read each file.
#

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$Project,

    [Parameter(Mandatory=$false)]
    [string]$Output = "",

    [Parameter(Mandatory=$false)]
    [int64]$MaxSize = 10485760,  # 10MB default

    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Script metadata
$SCRIPT_VERSION = "1.0.0"
$SCRIPT_NAME = "enumerate-project.ps1"
$SCAN_START = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: $SCRIPT_NAME -Project PATH [OPTIONS]

Enumerate all files in a project directory for AI analysis.

Required Parameters:
  -Project PATH        Path to project root directory

Optional Parameters:
  -Output FILE         Output JSON file (default: stdout)
  -MaxSize BYTES       Maximum file size to include (default: 10485760 = 10MB)
  -Help               Show this help message

Output Format:
  JSON object with project structure, file metadata, and statistics

Examples:
  # Scan current directory, output to stdout
  .\$SCRIPT_NAME -Project .

  # Scan project, save to file
  .\$SCRIPT_NAME -Project C:\path\to\legacy -Output manifest.json

  # Scan with custom size limit (50MB)
  .\$SCRIPT_NAME -Project . -Output manifest.json -MaxSize 52428800

"@
    exit 0
}

# Validate project path
if (-not (Test-Path $Project -PathType Container)) {
    Write-Error "ERROR: Project path does not exist or is not a directory: $Project"
    exit 1
}

# Convert to absolute path
$Project = (Resolve-Path $Project).Path

# Determine if we should show progress
$ShowProgress = $Output -ne ""

# Progress functions
function Write-Progress-Info {
    param([string]$Message)
    if ($ShowProgress) {
        Write-Host "ℹ $Message" -ForegroundColor Blue
    }
}

function Write-Progress-Success {
    param([string]$Message)
    if ($ShowProgress) {
        Write-Host "✓ $Message" -ForegroundColor Green
    }
}

function Write-Progress-Warning {
    param([string]$Message)
    if ($ShowProgress) {
        Write-Host "⚠ $Message" -ForegroundColor Yellow
    }
}

# Detect if a file is binary
function Test-BinaryFile {
    param([string]$Path)

    try {
        # Read first 8KB and check for null bytes
        $bytes = Get-Content -Path $Path -Encoding Byte -TotalCount 8192 -ErrorAction Stop
        $nullCount = ($bytes | Where-Object { $_ -eq 0 }).Count
        return $nullCount -gt 0
    }
    catch {
        # If we can't read it, assume it's binary
        return $true
    }
}

# Get file category based on extension
function Get-FileCategory {
    param([string]$Extension)

    switch -Regex ($Extension) {
        # Code files
        '^\.(js|ts|jsx|tsx|mjs|cjs)$' { return "code" }
        '^\.(cs|fs|vb)$' { return "code" }
        '^\.(java|kt|scala|groovy)$' { return "code" }
        '^\.(py|pyw|pyx)$' { return "code" }
        '^\.(rb|rake|gemspec)$' { return "code" }
        '^\.go$' { return "code" }
        '^\.rs$' { return "code" }
        '^\.(php|phtml)$' { return "code" }
        '^\.(c|cpp|cc|cxx|h|hpp)$' { return "code" }
        '^\.(swift|m|mm)$' { return "code" }

        # Markup and styles
        '^\.(html|htm|xhtml)$' { return "markup" }
        '^\.(css|scss|sass|less)$' { return "style" }
        '^\.(vue|svelte)$' { return "component" }

        # Configuration
        '^\.(json|yaml|yml|toml|ini|conf|config)$' { return "config" }
        '^\.(xml|plist)$' { return "config" }
        '^\.(env|properties)$' { return "config" }

        # Build and project files
        '^\.(csproj|sln|fsproj|vbproj)$' { return "project" }
        '^\.(gradle|pom)$' { return "project" }
        '^\.(gemfile|rakefile)$' { return "project" }
        '^\.lock$' { return "lockfile" }

        # Database
        '^\.(sql|psql|mysql)$' { return "database" }

        # Scripts
        '^\.(sh|bash|zsh|fish)$' { return "script" }
        '^\.(ps1|psm1|psd1)$' { return "script" }
        '^\.(bat|cmd)$' { return "script" }

        # Documentation
        '^\.(md|markdown|txt|rst|adoc)$' { return "documentation" }

        # Data
        '^\.(csv|tsv|dat)$' { return "data" }

        # Binary/compiled
        '^\.(dll|exe|so|dylib|a|o|obj|pdb)$' { return "binary" }
        '^\.(class|jar|war|ear)$' { return "binary" }
        '^\.(pyc|pyo)$' { return "binary" }

        # Images
        '^\.(jpg|jpeg|png|gif|svg|ico|webp)$' { return "image" }

        # Archives
        '^\.(zip|tar|gz|bz2|xz|7z|rar)$' { return "archive" }

        # Default
        default {
            if ($Extension -eq "") {
                return "no_extension"
            }
            return "other"
        }
    }
}

# Main enumeration function
function Invoke-FileEnumeration {
    Write-Progress-Info "Starting full recursive scan of: $Project"

    $fileCount = 0
    $totalSize = 0
    $binaryCount = 0
    $oversizedCount = 0
    $errorCount = 0

    # Collections
    $files = @()
    $errors = @()
    $categoryCounts = @{}
    $extensionCounts = @{}
    $largestFiles = @()

    # Enumerate all files
    Get-ChildItem -Path $Project -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $fileCount++

        # Show progress every 100 files
        if ($fileCount % 100 -eq 0) {
            Write-Progress-Info "Scanned $fileCount files..."
        }

        $file = $_
        $relPath = $file.FullName.Substring($Project.Length).TrimStart('\', '/')

        # Get file size
        $size = $file.Length

        $totalSize += $size

        # Get extension
        $ext = $file.Extension

        # Get category
        $category = Get-FileCategory -Extension $ext

        # Update counters
        if ($categoryCounts.ContainsKey($category)) {
            $categoryCounts[$category]++
        } else {
            $categoryCounts[$category] = 1
        }

        if ($ext -ne "") {
            if ($extensionCounts.ContainsKey($ext)) {
                $extensionCounts[$ext]++
            } else {
                $extensionCounts[$ext] = 1
            }
        }

        # Check file properties
        $readable = $true
        $isBinary = $false
        $sizeCategory = "normal"
        $skipReason = ""

        try {
            # Check if file is readable
            if (-not $file.PSIsContainer -and -not (Get-Content -Path $file.FullName -TotalCount 1 -ErrorAction Stop)) {
                # File exists and is readable (even if empty)
            }
        }
        catch [UnauthorizedAccessException] {
            $readable = $false
            $skipReason = "permission_denied"
            $errorCount++
        }
        catch {
            # Other read errors
            $readable = $false
            $skipReason = "read_error"
            $errorCount++
        }

        if ($size -gt $MaxSize) {
            $sizeCategory = "oversized"
            $skipReason = "exceeds_max_size"
            $oversizedCount++
        }
        elseif ($category -in @("binary", "image", "archive")) {
            $isBinary = $true
            $binaryCount++
        }
        elseif ($readable) {
            # Check if actually binary
            $isBinary = Test-BinaryFile -Path $file.FullName
            if ($isBinary) {
                $binaryCount++
            }
        }

        # Determine size category
        if ($sizeCategory -ne "oversized" -and $readable) {
            if ($size -lt 10KB) {
                $sizeCategory = "tiny"
            }
            elseif ($size -lt 100KB) {
                $sizeCategory = "small"
            }
            elseif ($size -lt 1MB) {
                $sizeCategory = "medium"
            }
            else {
                $sizeCategory = "large"
            }
        }

        # Build file object
        $fileObj = [PSCustomObject]@{
            path = $relPath
            absolute_path = $file.FullName
            size_bytes = $size
            extension = $ext
            category = $category
            size_category = $sizeCategory
            is_binary = $isBinary
            readable = $readable
            skip_reason = $skipReason
        }

        $files += $fileObj

        # Track largest files
        $largestFiles += [PSCustomObject]@{
            path = $relPath
            size_bytes = $size
        }

        # Log errors
        if (-not $readable) {
            $errors += [PSCustomObject]@{
                path = $relPath
                reason = $skipReason
            }
        }
    }

    Write-Progress-Success "Scanned $fileCount files"

    # Get top 10 largest files
    $largestFiles = $largestFiles | Sort-Object -Property size_bytes -Descending | Select-Object -First 10

    # Build final result
    $scanEnd = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

    $result = [PSCustomObject]@{
        scan_info = [PSCustomObject]@{
            project_path = $Project
            scanner = "powershell-$($PSVersionTable.PSVersion)"
            script_version = $SCRIPT_VERSION
            scan_start = $SCAN_START
            scan_end = $scanEnd
            max_file_size_bytes = $MaxSize
        }
        statistics = [PSCustomObject]@{
            total_files = $fileCount
            total_size_bytes = $totalSize
            binary_files = $binaryCount
            oversized_files = $oversizedCount
            unreadable_files = $errorCount
            by_category = $categoryCounts
            by_extension = $extensionCounts
            largest_files = $largestFiles
        }
        files = $files
        errors = $errors
    }

    return $result
}

# Main execution
Write-Progress-Info "enumerate-project.ps1 v$SCRIPT_VERSION"
Write-Progress-Info "Project: $Project"

$result = Invoke-FileEnumeration

if ($Output -ne "") {
    Write-Progress-Info "Output: $Output"
    $result | ConvertTo-Json -Depth 10 -Compress:$false | Out-File -FilePath $Output -Encoding utf8
    Write-Progress-Success "Enumeration complete: $Output"
}
else {
    # Output to stdout
    $result | ConvertTo-Json -Depth 10 -Compress:$false
}
