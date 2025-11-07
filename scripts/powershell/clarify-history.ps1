param(
    [switch]$Json,
    [string]$Search,
    [switch]$Verify,
    [string]$Feature,
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Write-Host "Usage: clarify-history.ps1 [-Json] [-Search QUERY] [-Verify] [FEATURE]"
    Write-Host ""
    Write-Host "View clarification history for a feature specification."
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json       Output in JSON format"
    Write-Host "  -Search QUERY Search for specific keywords in Q&A"
    Write-Host "  -Verify       Check that all clarifications are integrated"
    Write-Host "  FEATURE      Feature name or number (default: current)"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\clarify-history.ps1                          # Current feature history"
    Write-Host "  .\clarify-history.ps1 001-task-management      # Specific feature"
    Write-Host "  .\clarify-history.ps1 -Search 'authentication'  # Search Q&A"
    Write-Host "  .\clarify-history.ps1 -Verify                   # Verify integration"
    exit 0
}

# Source common functions
. "$PSScriptRoot\common.ps1"

# Get repository root
$RepoRoot = Get-RepoRoot

# Determine feature
if ([string]::IsNullOrWhiteSpace($Feature)) {
    # Use current branch
    $CurrentBranch = Get-CurrentBranch
    $FeatureDir = Find-FeatureDirByPrefix -RepoRoot $RepoRoot -BranchName $CurrentBranch

    if (-not $FeatureDir) {
        Write-Error "Error: Could not determine current feature. Provide feature name as argument."
        exit 1
    }

    $FeatureName = Split-Path $FeatureDir -Leaf
}
else {
    # Find feature by name/number
    $FeatureDir = Find-FeatureDir -RepoRoot $RepoRoot -FeatureName $Feature

    if (-not $FeatureDir) {
        Write-Error "Error: Feature not found: $Feature"
        exit 1
    }

    $FeatureName = Split-Path $FeatureDir -Leaf
}

$SpecFile = Join-Path $FeatureDir "spec.md"

if (-not (Test-Path $SpecFile)) {
    Write-Error "Error: Spec file not found: $SpecFile"
    exit 1
}

# Parse clarifications from spec
function Parse-Clarifications {
    param([string]$SpecFilePath, [string]$SearchQuery)

    $InClarifications = $false
    $CurrentSession = ""
    $SessionCount = 0
    $TotalQuestions = 0

    $Sessions = @{}
    $SessionQuestions = @{}

    $Content = Get-Content $SpecFilePath -ErrorAction SilentlyContinue

    foreach ($Line in $Content) {
        # Detect clarifications section start
        if ($Line -match "^## Clarifications") {
            $InClarifications = $true
            continue
        }

        # Exit clarifications section on next ## heading
        if ($InClarifications -and $Line -match "^## [^#]") {
            $InClarifications = $false
            break
        }

        # Parse session date
        if ($InClarifications -and $Line -match "^### Session (\d{4}-\d{2}-\d{2})") {
            $CurrentSession = $Matches[1]
            $SessionCount++
            $Sessions[$CurrentSession] = @()
            $SessionQuestions[$CurrentSession] = 0
            continue
        }

        # Parse Q&A pairs
        if ($InClarifications -and $CurrentSession) {
            if ($Line -match "^\s*-\s*Q:\s*(.+?)\s*→\s*A:\s*(.+)") {
                $Question = $Matches[1].Trim()
                $Answer = $Matches[2].Trim()

                # Filter by search query if provided
                if ($SearchQuery) {
                    if ($Line -notmatch $SearchQuery) {
                        continue
                    }
                }

                # Add to session
                $Sessions[$CurrentSession] += @{
                    question = $Question
                    answer = $Answer
                }

                $SessionQuestions[$CurrentSession]++
                $TotalQuestions++
            }
        }
    }

    return @{
        sessions = $Sessions
        session_questions = $SessionQuestions
        session_count = $SessionCount
        total_questions = $TotalQuestions
    }
}

# Verify mode
if ($Verify) {
    Write-Host "Verification not yet implemented" -ForegroundColor Yellow
    exit 1
}

# Main execution
$ParsedData = Parse-Clarifications -SpecFilePath $SpecFile -SearchQuery $Search

# Output results
if ($Json) {
    $JsonSessions = @()

    foreach ($SessionDate in ($ParsedData.sessions.Keys | Sort-Object)) {
        $QAPairs = $ParsedData.sessions[$SessionDate]
        $QuestionCount = $ParsedData.session_questions[$SessionDate]

        $JsonSessions += @{
            date = $SessionDate
            questions = $QuestionCount
            qa_pairs = $QAPairs
        }
    }

    $Output = @{
        feature = $FeatureName
        spec_file = $SpecFile
        total_sessions = $ParsedData.session_count
        total_questions = $ParsedData.total_questions
        sessions = $JsonSessions
    }

    $Output | ConvertTo-Json -Depth 10
}
else {
    Write-Host "Clarification History: $FeatureName"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host ""

    if ($ParsedData.session_count -eq 0) {
        Write-Host "No clarification sessions found."
        Write-Host ""
        Write-Host "The spec.md file does not contain a ## Clarifications section."
        Write-Host ""
        Write-Host "Recommendation: Run /speckit.clarify to identify ambiguities"
        return
    }

    Write-Host "📊 Summary:"
    Write-Host "  Total Sessions: $($ParsedData.session_count)"
    Write-Host "  Total Questions: $($ParsedData.total_questions)"
    Write-Host "  Spec File: $SpecFile"
    Write-Host ""

    if ($Search) {
        Write-Host "🔍 Search Results for: `"$Search`""
        Write-Host ""
    }

    # Display each session
    foreach ($SessionDate in ($ParsedData.sessions.Keys | Sort-Object)) {
        $QAPairs = $ParsedData.sessions[$SessionDate]
        $QuestionCount = $ParsedData.session_questions[$SessionDate]

        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Write-Host ""
        Write-Host "Session $SessionDate ($QuestionCount questions)"
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Write-Host ""

        $QAIndex = 1
        foreach ($QA in $QAPairs) {
            Write-Host "Q$QAIndex`: $($QA.question)"
            Write-Host "→  $($QA.answer)"
            Write-Host ""
            $QAIndex++
        }
    }

    if (-not $Search -and $ParsedData.total_questions -gt 0) {
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Write-Host ""
        Write-Host "✓ All clarifications recorded"
        Write-Host ""
        Write-Host "Next steps:"
        Write-Host "  • Review history: .\clarify-history.ps1 -Search 'keyword'"
        Write-Host "  • Continue to planning: /speckit.plan"
    }
}
