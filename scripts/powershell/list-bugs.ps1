#!/usr/bin/env pwsh
# List unresolved bugs from validation
#
# This script scans validation/bugs/ directory and returns bugs that haven't been resolved.
# Used by the fix command to automatically load bugs to fix.
#
# Usage: ./list-bugs.ps1 [OPTIONS]
#
# OPTIONS:
#   -Json               Output in JSON format
#   -All                Include resolved bugs (default: unresolved only)
#   -Summary            Show summary counts only
#   -Help               Show help message

param(
    [switch]$Json,
    [switch]$All,
    [switch]$Summary,
    [switch]$Help
)

if ($Help) {
    @"
Usage: list-bugs.ps1 [OPTIONS]

List unresolved bugs from validation/bugs/ directory.

OPTIONS:
  -Json               Output in JSON format
  -All                Include resolved bugs (default: unresolved only)
  -Summary            Show summary counts only
  -Help               Show this help message

BUG FILE FORMAT:
  Each bug file in validation/bugs/ should be named: BUG-{number}-{short-desc}.md
  The file must contain YAML frontmatter with at least:
    - status: open | in_progress | resolved | wont_fix
    - severity: critical | high | medium | low
    - user_story: US identifier (e.g., US1, US2)

EXAMPLES:
  # List unresolved bugs in JSON (for fix command)
  ./list-bugs.ps1 -Json

  # Show all bugs including resolved
  ./list-bugs.ps1 -All

  # Get summary counts only
  ./list-bugs.ps1 -Summary
"@
    exit 0
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get feature paths
$paths = Get-FeaturePathsEnv
$bugsDir = Join-Path $paths.FEATURE_DIR "validation/bugs"

# Initialize counters
$stats = @{
    total = 0
    open = 0
    in_progress = 0
    resolved = 0
    wont_fix = 0
    critical = 0
    high = 0
    medium = 0
    low = 0
}

# Initialize bug list
$bugs = @()

# Check if bugs directory exists
if (-not (Test-Path $bugsDir)) {
    if ($Json) {
        $output = @{
            FEATURE_DIR = $paths.FEATURE_DIR
            BUGS = @()
            SUMMARY = @{
                total = 0
                unresolved = 0
                open = 0
                in_progress = 0
                resolved = 0
                critical = 0
                high = 0
                medium = 0
                low = 0
            }
        }
        $output | ConvertTo-Json -Depth 3 -Compress
    } else {
        Write-Output "No bugs directory found at: $bugsDir"
        Write-Output "This feature has no recorded validation bugs."
    }
    exit 0
}

# Process each bug file
Get-ChildItem -Path $bugsDir -Filter "BUG-*.md" | ForEach-Object {
    $bugFile = $_
    $stats.total++

    $bugId = $bugFile.BaseName

    # Parse frontmatter
    $content = Get-Content $bugFile.FullName -Raw
    $status = ""
    $severity = ""
    $bugType = ""
    $userStory = ""
    $title = ""
    $scenario = ""
    $component = ""

    if ($content -match '(?s)^---\r?\n(.+?)\r?\n---') {
        $frontmatter = $matches[1]

        if ($frontmatter -match 'status:\s*(.+)') { $status = $matches[1].Trim() }
        if ($frontmatter -match 'severity:\s*(.+)') { $severity = $matches[1].Trim() }
        if ($frontmatter -match 'type:\s*(.+)') { $bugType = $matches[1].Trim() }
        if ($frontmatter -match 'user_story:\s*(.+)') { $userStory = $matches[1].Trim() }
        if ($frontmatter -match 'title:\s*(.+)') { $title = $matches[1].Trim() }
        if ($frontmatter -match 'scenario:\s*(.+)') { $scenario = $matches[1].Trim() }
        if ($frontmatter -match 'component:\s*(.+)') { $component = $matches[1].Trim() }
    }

    # Update counters
    switch ($status) {
        "open" { $stats.open++ }
        "in_progress" { $stats.in_progress++ }
        "resolved" { $stats.resolved++ }
        "wont_fix" { $stats.wont_fix++ }
    }

    switch ($severity) {
        "critical" { $stats.critical++ }
        "high" { $stats.high++ }
        "medium" { $stats.medium++ }
        "low" { $stats.low++ }
    }

    # Skip resolved bugs unless -All
    if (-not $All -and ($status -eq "resolved" -or $status -eq "wont_fix")) {
        return
    }

    # Add to bug list
    $bugs += @{
        id = $bugId
        status = $status
        severity = $severity
        type = $bugType
        user_story = $userStory
        title = $title
        scenario = $scenario
        component = $component
        file = $bugFile.FullName
    }

    if (-not $Json -and -not $Summary) {
        $statusIcon = switch ($status) {
            "open" { "🔴" }
            "in_progress" { "🟡" }
            "resolved" { "🟢" }
            "wont_fix" { "⚪" }
            default { "?" }
        }

        $severityBadge = switch ($severity) {
            "critical" { "[CRITICAL]" }
            "high" { "[HIGH]" }
            "medium" { "[MEDIUM]" }
            "low" { "[LOW]" }
            default { "" }
        }

        Write-Output "$statusIcon $bugId $severityBadge - $title ($userStory)"
    }
}

# Calculate unresolved count
$unresolved = $stats.open + $stats.in_progress

# Output results
if ($Json) {
    $output = @{
        FEATURE_DIR = $paths.FEATURE_DIR
        BUGS = $bugs
        SUMMARY = @{
            total = $stats.total
            unresolved = $unresolved
            open = $stats.open
            in_progress = $stats.in_progress
            resolved = $stats.resolved
            wont_fix = $stats.wont_fix
            critical = $stats.critical
            high = $stats.high
            medium = $stats.medium
            low = $stats.low
        }
    }
    $output | ConvertTo-Json -Depth 3 -Compress
} else {
    if ($Summary -or $stats.total -gt 0) {
        Write-Output ""
        Write-Output "=== Bug Summary ==="
        Write-Output "Total: $($stats.total)"
        Write-Output "  Open: $($stats.open)"
        Write-Output "  In Progress: $($stats.in_progress)"
        Write-Output "  Resolved: $($stats.resolved)"
        Write-Output "  Won't Fix: $($stats.wont_fix)"
        Write-Output ""
        Write-Output "By Severity:"
        Write-Output "  Critical: $($stats.critical)"
        Write-Output "  High: $($stats.high)"
        Write-Output "  Medium: $($stats.medium)"
        Write-Output "  Low: $($stats.low)"
        Write-Output ""
        if ($unresolved -gt 0) {
            Write-Output "⚠️  $unresolved bug(s) need attention"
        } else {
            Write-Output "✅ All bugs resolved"
        }
    }
}
