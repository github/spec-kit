param(
    [switch]$Json,
    [string]$File,
    [int]$Line,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ErrorMessageParts,
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Write-Host "Usage: error-analysis.ps1 [-Json] [-File FILE] [-Line LINE] ERROR_MESSAGE"
    Write-Host ""
    Write-Host "Analyze errors with specification context."
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json          Output in JSON format"
    Write-Host "  -File FILE     File where error occurred"
    Write-Host "  -Line LINE     Line number where error occurred"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\error-analysis.ps1 'TypeError: Cannot read property status of undefined'"
    Write-Host "  .\error-analysis.ps1 -File src\api\tasks.py -Line 145 'TypeError'"
    exit 0
}

# Source common functions
. "$PSScriptRoot\common.ps1"

# Build error message from remaining arguments
$ErrorMessage = ($ErrorMessageParts -join " ").Trim()

if ([string]::IsNullOrWhiteSpace($ErrorMessage)) {
    Write-Error "Error: No error message provided"
    exit 1
}

# Get repository root
$RepoRoot = Get-RepoRoot

# Extract keywords from error message
function Extract-Keywords {
    param([string]$Text)

    $StopWords = @("the", "is", "are", "where", "what", "when", "how", "a", "an", "and", "or", "of", "to", "in", "for", "on", "at", "by", "with", "from")

    $Keywords = $Text.ToLower() -replace '[^a-z0-9\s]', ' ' -split '\s+' |
        Where-Object { $_.Length -ge 3 -and $_ -notin $StopWords } |
        Sort-Object -Unique

    return $Keywords
}

# Classify error type
function Get-ErrorType {
    param([string]$Error)

    if ($Error -match "(TypeError|AttributeError|NullReferenceException|Cannot read property|undefined)") {
        return "type_error"
    }
    elseif ($Error -match "(Test failed|Assertion|Expected .* but got)") {
        return "test_failure"
    }
    elseif ($Error -match "(SyntaxError|ImportError|Module not found|cannot find module)") {
        return "build_error"
    }
    elseif ($Error -match "(500|Database error|Connection refused|ECONNREFUSED)") {
        return "runtime_error"
    }
    else {
        return "unknown"
    }
}

# Search specs for related requirements
function Search-Specs {
    param(
        [string[]]$Keywords,
        [string]$RepoRoot
    )

    $SpecsDir = Join-Path $RepoRoot "specs"

    if (-not (Test-Path $SpecsDir)) {
        return @()
    }

    $Results = @()
    $SpecFiles = Get-ChildItem -Path $SpecsDir -Filter "spec.md" -Recurse -ErrorAction SilentlyContinue

    foreach ($SpecFile in $SpecFiles) {
        $FeatureName = Split-Path (Split-Path $SpecFile.FullName -Parent) -Leaf
        $Content = Get-Content $SpecFile.FullName -Raw -ErrorAction SilentlyContinue

        if ([string]::IsNullOrEmpty($Content)) { continue }

        $Lines = Get-Content $SpecFile.FullName -ErrorAction SilentlyContinue
        $LineNum = 0
        $CurrentReq = ""
        $CurrentReqText = ""

        foreach ($LineContent in $Lines) {
            $LineNum++

            # Detect requirement ID
            if ($LineContent -match "^(REQ-[0-9]+|#### REQ-[0-9]+)") {
                $CurrentReq = if ($LineContent -match "REQ-[0-9]+") { $Matches[0] } else { "" }
                $CurrentReqText = $LineContent
            }

            # If we have a current requirement, check for keyword matches
            if ($CurrentReq) {
                $MatchCount = 0
                foreach ($Keyword in $Keywords) {
                    if ($LineContent -match $Keyword) {
                        $MatchCount++
                    }
                }

                if ($MatchCount -gt 0) {
                    # Calculate relevance score
                    $Score = $MatchCount * 40

                    # File proximity bonus
                    if ($File -and $CurrentReqText -match [regex]::Escape((Split-Path $File -Leaf))) {
                        $Score += 30
                    }

                    # Check if already added
                    $Key = "$FeatureName`:$CurrentReq"
                    if (-not ($Results | Where-Object { $_.feature -eq $FeatureName -and $_.requirement -eq $CurrentReq })) {
                        $ReqText = $CurrentReqText -replace '^####\s*', '' -replace '^REQ-[0-9]+:\s*', ''

                        $Results += [PSCustomObject]@{
                            feature = $FeatureName
                            requirement = $CurrentReq
                            text = $ReqText.Trim()
                            file = "$($SpecFile.FullName):$LineNum"
                            relevance = $Score
                        }
                    }
                }
            }
        }
    }

    return $Results | Sort-Object -Property relevance -Descending
}

# Generate possible causes based on error type
function Get-PossibleCauses {
    param([string]$ErrorType, [string]$ErrorMsg)

    switch ($ErrorType) {
        "type_error" {
            return @(
                "Object not initialized before property access",
                "Async operation not awaited",
                "Null/undefined returned from function or database",
                "Missing null/undefined check"
            )
        }
        "test_failure" {
            return @(
                "Expected behavior not matching specification",
                "Missing edge case handling",
                "Incorrect test assertion",
                "Implementation incomplete"
            )
        }
        "build_error" {
            return @(
                "Missing dependency in package.json/requirements.txt",
                "Incorrect import path",
                "Module not installed",
                "Syntax error in recent changes"
            )
        }
        "runtime_error" {
            return @(
                "External service not running",
                "Incorrect configuration",
                "Network connectivity issue",
                "Database connection problem"
            )
        }
        default {
            return @("Unknown error type - manual analysis required")
        }
    }
}

# Generate suggestions based on error analysis
function Get-Suggestions {
    param([string]$ErrorType, [array]$RelatedSpecs)

    $Suggestions = @()

    # Add spec-based suggestions
    if ($RelatedSpecs.Count -gt 0) {
        $TopSpec = $RelatedSpecs[0]
        $Suggestions += "Check requirement $($TopSpec.requirement) in specs\$($TopSpec.feature)\spec.md"

        if ($ErrorType -eq "type_error") {
            $Suggestions += "Verify null handling requirements in $($TopSpec.requirement)"
        }
    }

    # Add generic suggestions based on error type
    switch ($ErrorType) {
        "type_error" {
            $Suggestions += "Add null/undefined checks before property access"
            $Suggestions += "Ensure objects are properly initialized"
        }
        "test_failure" {
            $Suggestions += "Review acceptance criteria in specification"
            $Suggestions += "Check edge cases documented in spec"
        }
        "build_error" {
            $Suggestions += "Check technology stack in plan.md"
            $Suggestions += "Verify dependencies are installed"
        }
        "runtime_error" {
            $Suggestions += "Check non-functional requirements for error handling"
            $Suggestions += "Verify external service configuration"
        }
    }

    return $Suggestions
}

# Main analysis
$ErrorType = Get-ErrorType -Error $ErrorMessage
$Keywords = Extract-Keywords -Text $ErrorMessage

# Search for related specs
$RelatedSpecs = Search-Specs -Keywords $Keywords -RepoRoot $RepoRoot

# Generate possible causes and suggestions
$PossibleCauses = Get-PossibleCauses -ErrorType $ErrorType -ErrorMsg $ErrorMessage
$Suggestions = Get-Suggestions -ErrorType $ErrorType -RelatedSpecs $RelatedSpecs

# Output results
if ($Json) {
    $Output = @{
        error = $ErrorMessage
        error_type = $ErrorType
        location = @{
            file = $File
            line = $Line
        }
        related_specs = @($RelatedSpecs | Select-Object -First 5 | ForEach-Object {
            @{
                feature = $_.feature
                requirement = $_.requirement
                text = $_.text
                file = $_.file
                relevance = $_.relevance
            }
        })
        possible_causes = $PossibleCauses
        suggestions = $Suggestions
    }

    $Output | ConvertTo-Json -Depth 10
}
else {
    Write-Host "Error Analysis"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host ""
    Write-Host "🔴 Error: $ErrorMessage"

    if ($File) {
        Write-Host ""
        $LocationStr = $File
        if ($Line) { $LocationStr += ":$Line" }
        Write-Host "📍 Location: $LocationStr"
    }

    # Display related specs
    if ($RelatedSpecs.Count -gt 0) {
        Write-Host ""
        Write-Host "📋 Related Requirements ($($RelatedSpecs.Count) found):"
        Write-Host ""

        $Index = 0
        foreach ($Spec in ($RelatedSpecs | Select-Object -First 3)) {
            $Index++
            Write-Host "  $Index. $($Spec.requirement) in $($Spec.feature) (relevance: $($Spec.relevance)%)"
            Write-Host "     `"$($Spec.text)`""
            Write-Host "     → $($Spec.file)"
            Write-Host ""
        }
    }
    else {
        Write-Host ""
        Write-Host "📋 Related Requirements: None found in specifications"
        Write-Host ""
        Write-Host "This may indicate:"
        Write-Host "  • Infrastructure/environment issue (not spec-related)"
        Write-Host "  • Missing specification coverage"
        Write-Host "  • Error in external dependency"
    }

    # Display possible causes
    Write-Host ""
    Write-Host "🔍 Possible Causes:"
    Write-Host ""
    foreach ($Cause in $PossibleCauses) {
        Write-Host "  • $Cause"
    }

    # Display suggestions
    Write-Host ""
    Write-Host "💡 Suggestions:"
    Write-Host ""
    $SuggIndex = 0
    foreach ($Suggestion in ($Suggestions | Select-Object -First 5)) {
        $SuggIndex++
        Write-Host "  $SuggIndex. $Suggestion"
    }

    Write-Host ""
}
