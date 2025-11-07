param(
    [switch]$Json,
    [int]$Limit = 10,
    [ValidateSet("all", "code", "docs", "tests")]
    [string]$Type = "all",
    [string]$Feature,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$QueryParts,
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Write-Host "Usage: semantic-search.ps1 [-Json] [options] 'query'"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json              Output in JSON format"
    Write-Host "  -Limit N           Show top N results (default: 10)"
    Write-Host "  -Type TYPE         Filter by type: code, docs, tests, all (default: all)"
    Write-Host "  -Feature NAME      Search only in specific feature"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\semantic-search.ps1 'authentication handling'"
    Write-Host "  .\semantic-search.ps1 -Type code 'validation logic'"
    Write-Host "  .\semantic-search.ps1 -Feature 001-tasks 'status update'"
    exit 0
}

# Source common functions
. "$PSScriptRoot\common.ps1"

# Build query from remaining arguments
$Query = ($QueryParts -join " ").Trim()

if ([string]::IsNullOrWhiteSpace($Query)) {
    Write-Error "ERROR: No search query provided"
    Write-Host "Usage: semantic-search.ps1 'your search query'" -ForegroundColor Yellow
    exit 1
}

# Get repository root
$RepoRoot = Get-RepoRoot

# Extract keywords from query (remove common stop words)
function Extract-Keywords {
    param([string]$QueryText)

    $StopWords = @("the", "is", "are", "where", "what", "how", "does", "do", "for", "to", "in", "on", "at", "from", "by", "with")

    $Keywords = $QueryText.ToLower() -split '\s+' |
        Where-Object { $_ -notin $StopWords -and $_.Length -gt 0 } |
        Sort-Object -Unique

    return $Keywords
}

# Determine file type
function Get-FileType {
    param([string]$FilePath)

    $FileName = [System.IO.Path]::GetFileName($FilePath)

    if ($FileName -match '\.(py|js|ts|tsx|jsx|go|rs|java|c|cpp|h)$') {
        return "code"
    }
    elseif ($FileName -match 'test.*\.(py|js|ts)|_test\.go|Test\.java') {
        return "test"
    }
    elseif ($FilePath -match '\.md$') {
        if ($FilePath -match '[\\/]specs[\\/]') {
            return "docs"
        }
        return "docs"
    }
    else {
        return "other"
    }
}

# Calculate relevance score
function Calculate-Score {
    param(
        [int]$Matches,
        [string]$Proximity,
        [string]$FileType,
        [bool]$IsQuickRef
    )

    $Score = $Matches * 40

    # Proximity bonus
    if ($Proximity -eq "high") {
        $Score += 30
    }
    elseif ($Proximity -eq "medium") {
        $Score += 15
    }

    # File type bonus
    switch ($FileType) {
        "docs" {
            $Score += 20
            if ($IsQuickRef) { $Score += 10 }
        }
        "code" { $Score += 15 }
        "test" { $Score += 10 }
    }

    # Cap at 100
    if ($Score -gt 100) { $Score = 100 }

    return $Score
}

# Extract keywords
$Keywords = Extract-Keywords -QueryText $Query

# Build search pattern (regex OR)
$GrepPattern = ($Keywords -join '|')

# Determine search locations
$SearchDirs = @()
$SpecsDir = Join-Path $RepoRoot "specs"
if (Test-Path $SpecsDir) {
    $SearchDirs += $SpecsDir
}

if ($Type -eq "all" -or $Type -eq "code") {
    $SrcDir = Join-Path $RepoRoot "src"
    if (Test-Path $SrcDir) { $SearchDirs += $SrcDir }

    $LibDir = Join-Path $RepoRoot "lib"
    if (Test-Path $LibDir) { $SearchDirs += $LibDir }
}

if ($Type -eq "all" -or $Type -eq "tests") {
    $TestsDir = Join-Path $RepoRoot "tests"
    if (Test-Path $TestsDir) { $SearchDirs += $TestsDir }

    $TestDir = Join-Path $RepoRoot "test"
    if (Test-Path $TestDir) { $SearchDirs += $TestDir }
}

# Apply feature filter
if (-not [string]::IsNullOrWhiteSpace($Feature)) {
    $SearchDirs = @(Join-Path $RepoRoot "specs\$Feature")
}

# Perform search
$StartTime = Get-Date

$Results = @()

foreach ($SearchDir in $SearchDirs) {
    if (-not (Test-Path $SearchDir)) { continue }

    try {
        $Files = Get-ChildItem -Path $SearchDir -Recurse -File -Include *.md, *.py, *.js, *.ts, *.tsx, *.jsx, *.go, *.rs, *.java, *.c, *.cpp, *.h -ErrorAction SilentlyContinue

        foreach ($File in $Files) {
            try {
                $LineNumber = 0
                $Content = Get-Content $File.FullName -ErrorAction SilentlyContinue

                foreach ($Line in $Content) {
                    $LineNumber++

                    # Check if line matches pattern
                    if ($Line -match $GrepPattern) {
                        # Count keyword matches
                        $MatchCount = 0
                        foreach ($Keyword in $Keywords) {
                            if ($Line -match $Keyword) {
                                $MatchCount++
                            }
                        }

                        if ($MatchCount -eq 0) { continue }

                        # Determine proximity
                        $Proximity = "low"
                        $AllInLine = $true
                        foreach ($Keyword in $Keywords) {
                            if ($Line -notmatch $Keyword) {
                                $AllInLine = $false
                                break
                            }
                        }
                        if ($AllInLine) { $Proximity = "high" }

                        # Get file type
                        $FileType = Get-FileType -FilePath $File.FullName

                        # Check if quick ref
                        $IsQuickRef = $File.Name -eq "quick-ref.md"

                        # Calculate score
                        $Score = Calculate-Score -Matches $MatchCount -Proximity $Proximity -FileType $FileType -IsQuickRef $IsQuickRef

                        # Store result
                        $Results += [PSCustomObject]@{
                            File = $File.FullName
                            Line = $LineNumber
                            Context = $Line.Trim()
                            Type = $FileType
                            Score = $Score
                        }
                    }
                }
            }
            catch {
                # Skip files that can't be read
                continue
            }
        }
    }
    catch {
        continue
    }
}

$EndTime = Get-Date
$SearchTime = [int](($EndTime - $StartTime).TotalMilliseconds)

# Sort results by score (descending)
$SortedResults = $Results | Sort-Object -Property Score -Descending

# Limit results
$TopResults = $SortedResults | Select-Object -First $Limit
$TotalResults = $Results.Count

# Output results
if ($Json) {
    $Output = @{
        query = $Query
        results = @($TopResults | ForEach-Object {
            @{
                file = $_.File
                line = $_.Line
                type = $_.Type
                context = $_.Context
                relevance = $_.Score
            }
        })
        total_results = $TotalResults
        search_time_ms = $SearchTime
    }

    $Output | ConvertTo-Json -Depth 10 -Compress
}
else {
    # Human-readable output
    Write-Host "Search Results: `"$Query`""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if ($TotalResults -eq 0) {
        Write-Host "No matches found."
        Write-Host ""
        Write-Host "Try:"
        Write-Host "  • Broader search terms"
        Write-Host "  • Different keywords"
        Write-Host "  • Check spelling"
    }
    else {
        Write-Host "Found $TotalResults matches (showing top $Limit):"
        Write-Host ""

        $Count = 0
        foreach ($Result in $TopResults) {
            $Count++

            # Determine icon
            $Icon = "📄"
            switch ($Result.Type) {
                "code" { $Icon = "🔧" }
                "docs" { $Icon = "📝" }
                "test" { $Icon = "🧪" }
            }

            # Make file path relative
            $RelFile = $Result.File.Replace("$RepoRoot\", "").Replace("$RepoRoot/", "")

            Write-Host "$Count. $RelFile:$($Result.Line) (relevance: $($Result.Score)%)"

            # Truncate context to 80 chars
            $ContextPreview = $Result.Context
            if ($ContextPreview.Length -gt 80) {
                $ContextPreview = $ContextPreview.Substring(0, 80) + "..."
            }
            Write-Host "   $Icon $ContextPreview"
            Write-Host ""
        }

        # Quick ref suggestion
        $QuickRefResult = $SortedResults | Where-Object { $_.File -match 'quick-ref\.md$' } | Select-Object -First 1
        if ($QuickRefResult) {
            $RelFile = $QuickRefResult.File.Replace("$RepoRoot\", "").Replace("$RepoRoot/", "")
            Write-Host "💡 Quick Reference Available:"
            Write-Host "  $RelFile (~200 tokens)"
            Write-Host ""
            Write-Host "Read this first for an overview!"
        }
    }

    Write-Host "Search completed in ${SearchTime}ms"
}
