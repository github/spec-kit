# Resumption Instructions Generator - Creates precise instructions to resume interrupted mvp-to-full execution
param(
    [switch]$Json,
    [string]$Reason = "execution_interrupted",
    [string]$NextSpecs = "",
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\generate-resumption-instructions.ps1 [-Json] [-Reason <reason>] [-NextSpecs <spec_list>]"
    Write-Host "Generates resumption instructions for interrupted mvp-to-full execution"
    Write-Host "  -Reason: Reason for interruption (e.g., 'token_limit', 'manual_stop')"
    Write-Host "  -NextSpecs: Comma-separated list of remaining specs to process"
    exit 0
}

# Get repository root
$repoRoot = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: Not in a git repository. Run this script from within a git repository."
    exit 1
}

# Analyze current project state
Write-Host "🔍 Analyzing current project state..." -ForegroundColor Yellow

$specAnalysisScript = Join-Path $repoRoot ".specify/scripts/powershell/analyze-spec-completion.ps1"
$projectStateScript = Join-Path $repoRoot ".specify/scripts/powershell/analyze-project-state.ps1"

$specAnalysisJson = & $specAnalysisScript -Json
$projectStateJson = & $projectStateScript -Json

$specAnalysis = $specAnalysisJson | ConvertFrom-Json
$projectState = $projectStateJson | ConvertFrom-Json

# Extract key information
$incompleteSpecs = $specAnalysis.specs | Where-Object { $_.status -eq "incomplete" -or $_.status -eq "partially_complete" } | Select-Object -ExpandProperty spec_name
$inProgressSpecs = $specAnalysis.specs | Where-Object { $_.status -eq "implementation_in_progress" } | Select-Object -ExpandProperty spec_name
$readySpecs = $specAnalysis.specs | Where-Object { $_.status -eq "ready_for_implementation" } | Select-Object -ExpandProperty spec_name

# Determine next action based on current state
$nextAction = ""
$prioritySpec = ""
$resumptionContext = ""

if ($inProgressSpecs.Count -gt 0) {
    $prioritySpec = $inProgressSpecs[0]
    $nextAction = "continue_implementation"
    $resumptionContext = "Continue implementing tasks in spec: $prioritySpec"
} elseif ($incompleteSpecs.Count -gt 0) {
    $prioritySpec = $incompleteSpecs[0]
    $nextAction = "complete_spec_artifacts"
    $resumptionContext = "Complete missing artifacts in spec: $prioritySpec"
} elseif ($readySpecs.Count -gt 0) {
    $prioritySpec = $readySpecs[0]
    $nextAction = "start_implementation"
    $resumptionContext = "Begin implementation of spec: $prioritySpec"
} else {
    $nextAction = "continue_planning"
    $resumptionContext = "Continue creating new specs from remaining features"
}

# Get the specific missing artifacts for priority spec
$missingArtifacts = ""
if ($prioritySpec) {
    $prioritySpecData = $specAnalysis.specs | Where-Object { $_.spec_name -eq $prioritySpec }
    if ($prioritySpecData.missing_artifacts) {
        $missingArtifacts = $prioritySpecData.missing_artifacts -join ","
    }
}

# Generate timestamp
$timestamp = Get-Date -Format "o"

# Create resumption instructions
if ($Json) {
    $result = @{
        interruption_timestamp = $timestamp
        interruption_reason = $Reason
        next_action = $nextAction
        priority_spec = $prioritySpec
        missing_artifacts = $missingArtifacts
        resumption_context = $resumptionContext
        resumption_command = "Start a new chat and use this prompt: '/mvp-to-full Resume interrupted execution from $timestamp. $resumptionContext. Current state analysis: $($specAnalysisJson | ConvertTo-Json -Compress)'"
        current_state = $specAnalysis
        project_state = $projectState
    }
    $result | ConvertTo-Json -Depth 10
} else {
    Write-Host "=== RESUMPTION INSTRUCTIONS ===" -ForegroundColor Green
    Write-Host "Generated: $timestamp"
    Write-Host "Reason: $Reason"
    Write-Host ""
    Write-Host "🚀 TO RESUME IN NEW CHAT WINDOW:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Copy this EXACT command and paste in new chat:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   /mvp-to-full Resume interrupted execution from $timestamp. $resumptionContext." -ForegroundColor White
    Write-Host ""
    Write-Host "2. Include this state context:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Current incomplete specs: $($incompleteSpecs -join ' ')"
    Write-Host "   Specs in progress: $($inProgressSpecs -join ' ')"
    Write-Host "   Ready for implementation: $($readySpecs -join ' ')"
    Write-Host ""
    Write-Host "3. Priority Action: $nextAction" -ForegroundColor Yellow
    Write-Host "   Focus Spec: $prioritySpec"
    if ($missingArtifacts) {
        Write-Host "   Missing artifacts: $missingArtifacts"
    }
    Write-Host ""
    Write-Host "4. The system will automatically:" -ForegroundColor Yellow
    Write-Host "   - Detect existing spec folders and their completion status"
    Write-Host "   - Continue from the exact interruption point"
    Write-Host "   - Avoid creating duplicate numbered specs"
    Write-Host "   - Complete missing artifacts before starting new specs"
    Write-Host ""
    Write-Host "=== DETAILED STATE ANALYSIS ===" -ForegroundColor Green
    foreach ($spec in $specAnalysis.specs) {
        Write-Host "Spec: $($spec.spec_name) | Status: $($spec.status) | Completion: $($spec.completion_percentage)% | Tasks: $($spec.task_completion)"
    }
    Write-Host ""
}