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
    [Parameter(Mandatory=$false)]
    [string]$Project = "",

    [Parameter(Mandatory=$false)]
    [string]$Output = "",

    [Parameter(Mandatory=$false)]
    [int64]$MaxSize = 10485760,  # 10MB default

    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Script metadata
$SCRIPT_VERSION = "1.0.2"
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

# Validate required parameters
if ([string]::IsNullOrWhiteSpace($Project)) {
    Write-Error "ERROR: -Project parameter is required"
    Write-Output "Use -Help for usage information"
    exit 1
}

# Validate max size parameter
if ($MaxSize -lt 0) {
    Write-Error "ERROR: -MaxSize must be a positive integer (bytes)"
    exit 1
}

# Validate project path
if (-not (Test-Path $Project -PathType Container)) {
    Write-Error "ERROR: Project path does not exist or is not a directory: $Project"
    exit 1
}

# Convert to absolute path
$Project = (Resolve-Path $Project).Path

# Determine if we should show progress
$ShowProgress = $Output -ne "" -and [Console]::IsErrorRedirected -eq $false

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

# Get file category based on extension
function Get-FileCategory {
    param([string]$Extension)

    # Remove leading dot if present
    $ext = $Extension.TrimStart('.')

    switch -Regex ($ext) {
        # Code files
        '^(js|ts|jsx|tsx|mjs|cjs)$' { return "code" }
        '^(cs|fs|vb)$' { return "code" }
        '^(java|kt|scala|groovy)$' { return "code" }
        '^(py|pyw|pyx)$' { return "code" }
        '^(rb|rake|gemspec)$' { return "code" }
        '^go$' { return "code" }
        '^rs$' { return "code" }
        '^(php|phtml)$' { return "code" }
        '^(c|cpp|cc|cxx|h|hpp)$' { return "code" }
        '^(swift|m|mm)$' { return "code" }

        # Markup and styles
        '^(html|htm|xhtml)$' { return "markup" }
        '^(css|scss|sass|less)$' { return "style" }
        '^(vue|svelte)$' { return "component" }

        # Configuration
        '^(json|yaml|yml|toml|ini|conf|config)$' { return "config" }
        '^(xml|plist)$' { return "config" }
        '^(env|properties)$' { return "config" }

        # Build and project files
        '^(csproj|sln|fsproj|vbproj)$' { return "project" }
        '^(gradle|pom)$' { return "project" }
        '^(gemfile|rakefile)$' { return "project" }
        '^lock$' { return "lockfile" }

        # Database
        '^(sql|psql|mysql)$' { return "database" }

        # Scripts
        '^(sh|bash|zsh|fish)$' { return "script" }
        '^(ps1|psm1|psd1)$' { return "script" }
        '^(bat|cmd)$' { return "script" }

        # Documentation
        '^(md|markdown|txt|rst|adoc)$' { return "documentation" }

        # Data
        '^(csv|tsv|dat)$' { return "data" }

        # Binary/compiled
        '^(dll|exe|so|dylib|a|o|obj|pdb)$' { return "binary" }
        '^(class|jar|war|ear)$' { return "binary" }
        '^(pyc|pyo)$' { return "binary" }

        # Images
        '^(jpg|jpeg|png|gif|svg|ico|webp|bmp)$' { return "image" }

        # Archives
        '^(zip|tar|gz|bz2|xz|7z|rar)$' { return "archive" }

        # Default
        default {
            if ([string]::IsNullOrEmpty($ext)) {
                return "no_extension"
            }
            return "other"
        }
    }
}

# Detect if file is binary by checking for null bytes (IDENTICAL to bash version)
# Returns: $true or $false
function Test-BinaryFile {
    param([string]$Path)

    try {
        # Read first 8KB as bytes (compatible with both Windows PowerShell and PowerShell Core)
        if ($PSVersionTable.PSVersion.Major -ge 6) {
            # PowerShell Core 6+ uses -AsByteStream
            $bytes = Get-Content -Path $Path -AsByteStream -TotalCount 8192 -ErrorAction Stop
        } else {
            # Windows PowerShell 5.1 uses -Encoding Byte
            $bytes = Get-Content -Path $Path -Encoding Byte -TotalCount 8192 -ErrorAction Stop
        }

        # Count null bytes (0x00)
        $nullCount = ($bytes | Where-Object { $_ -eq 0 }).Count

        return $nullCount -gt 0
    }
    catch {
        # If we can't read it, assume it's binary
        return $true
    }
}

# Extract file extension properly (IDENTICAL to bash version logic)
function Get-FileExtensionSafe {
    param([string]$FilePath)

    $basename = Split-Path -Leaf $FilePath

    # Handle dotfiles without extension (.gitignore)
    if ($basename.StartsWith('.') -and (-not $basename.Contains('.', 1))) {
        return ""
    }

    # Extract extension
    if ($basename.Contains('.')) {
        $ext = [System.IO.Path]::GetExtension($basename)
        return $ext
    }

    return ""
}

# Main enumeration function - streams JSON output
function Invoke-FileEnumeration {
    Write-Progress-Info "Starting full recursive scan of: $Project"

    $fileCount = 0
    $totalSize = 0
    $binaryCount = 0
    $oversizedCount = 0
    $errorCount = 0

    $categoryCounts = @{}
    $extensionCounts = @{}
    $largestFiles = @{}  # key="size:path"

    # Open output stream
    if ($Output -ne "") {
        $stream = [System.IO.StreamWriter]::new($Output, $false, [System.Text.Encoding]::UTF8)
    } else {
        $stream = [System.IO.StreamWriter]::new([Console]::OpenStandardOutput())
        $stream.AutoFlush = $true
    }

    try {
        # Write JSON header
        $scanInfo = @{
            project_path = $Project
            scanner = "powershell-$($PSVersionTable.PSVersion)"
            script_version = $SCRIPT_VERSION
            scan_start = $SCAN_START
            scan_end = $null
            max_file_size_bytes = $MaxSize
        } | ConvertTo-Json -Compress

        $stream.WriteLine("{")
        $stream.WriteLine("`"scan_info`": $scanInfo,")
        $stream.WriteLine("`"files`": [")

        $firstFile = $true

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
            $ext = Get-FileExtensionSafe -FilePath $file.FullName
            $extForCategory = $ext.TrimStart('.')

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

            # Track largest files (keep top 10)
            $key = "${size}:$($file.FullName)"
            if ($largestFiles.Count -lt 10) {
                $largestFiles[$key] = $relPath
            } else {
                # Find smallest in top 10
                $smallestKey = ($largestFiles.Keys | Sort-Object { [int64]($_ -split ':')[0] } | Select-Object -First 1)
                $smallestSize = [int64]($smallestKey -split ':')[0]
                if ($size -gt $smallestSize) {
                    $largestFiles.Remove($smallestKey)
                    $largestFiles[$key] = $relPath
                }
            }

            # Determine file properties
            $readable = $true
            $isBinary = $false
            $sizeCategory = "normal"
            $skipReason = ""

            # Check readability
            try {
                $null = Get-Content -Path $file.FullName -TotalCount 1 -ErrorAction Stop
            }
            catch [UnauthorizedAccessException] {
                $readable = $false
                $skipReason = "permission_denied"
                $errorCount++
            }
            catch {
                $readable = $false
                $skipReason = "read_error"
                $errorCount++
            }

            # Check size before doing binary detection (CRITICAL FIX)
            if ($readable -and $size -gt $MaxSize) {
                $sizeCategory = "oversized"
                $skipReason = "exceeds_max_size"
                $oversizedCount++
            }
            # Check if binary by extension first
            elseif ($category -in @("binary", "image", "archive")) {
                $isBinary = $true
                $binaryCount++
            }
            # Only now check binary by content (after size check!)
            elseif ($readable) {
                $isBinary = Test-BinaryFile -Path $file.FullName
                if ($isBinary) {
                    $binaryCount++
                }
            }

            # Determine size category for readable files
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

            # Build file object (using ConvertTo-Json for safety - CRITICAL FIX)
            $fileObj = @{
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

            # Write JSON (streaming, no buffering)
            if (-not $firstFile) {
                $stream.WriteLine(",")
            }
            $firstFile = $false

            $json = ($fileObj | ConvertTo-Json -Compress)
            $stream.Write($json)
        }

        Write-Progress-Success "Scanned $fileCount files"

        # Close files array
        $stream.WriteLine()
        $stream.WriteLine("],")

        # Build statistics
        $scanEnd = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

        # Build largest files array
        $largestFilesArray = @()
        foreach ($key in ($largestFiles.Keys | Sort-Object { [int64]($_ -split ':')[0] } -Descending | Select-Object -First 10)) {
            $size = [int64]($key -split ':')[0]
            $path = $largestFiles[$key]
            $largestFilesArray += @{
                path = $path
                size_bytes = $size
            }
        }

        $statistics = @{
            total_files = $fileCount
            total_size_bytes = $totalSize
            binary_files = $binaryCount
            oversized_files = $oversizedCount
            unreadable_files = $errorCount
            by_category = $categoryCounts
            by_extension = $extensionCounts
            largest_files = $largestFilesArray
        }

        $statsJson = ($statistics | ConvertTo-Json -Compress -Depth 10)
        $stream.WriteLine("`"statistics`": $statsJson")
        $stream.WriteLine("}")

    } finally {
        $stream.Close()
        $stream.Dispose()
    }

    # Update scan_end timestamp
    if ($Output -ne "") {
        $content = Get-Content -Path $Output -Raw | ConvertFrom-Json
        $content.scan_info.scan_end = $scanEnd
        $content | ConvertTo-Json -Depth 100 | Set-Content -Path $Output -Encoding UTF8
    }
}

# Main execution
Write-Progress-Info "enumerate-project.ps1 v$SCRIPT_VERSION"
Write-Progress-Info "Project: $Project"

Invoke-FileEnumeration

Write-Progress-Success "Enumeration complete"
if ($Output -ne "") {
    Write-Progress-Success "Output: $Output"
}
