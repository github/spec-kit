param(
    [switch]$Json,
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Write-Host "Usage: session-prune.ps1 [-Json]"
    Write-Host ""
    Write-Host "Creates a session summary to help AI agents compress context."
    Write-Host "This script gathers current project state for the AI to use"
    Write-Host "when creating a compressed session summary."
    exit 0
}

# Source common functions
. "$PSScriptRoot\common.ps1"

# Get repository root
$RepoRoot = Get-RepoRoot
$MemoryDir = Join-Path $RepoRoot ".speckit\memory"

# Ensure memory directory exists
if (-not (Test-Path $MemoryDir)) {
    New-Item -ItemType Directory -Path $MemoryDir -Force | Out-Null
}

# Get current date and time
$CurrentDate = Get-Date -Format "yyyy-MM-dd"
$CurrentTime = Get-Date -Format "HH:mm"

# Detect current feature
$CurrentBranch = Get-CurrentBranch
if ([string]::IsNullOrEmpty($CurrentBranch)) {
    $CurrentBranch = "unknown"
}

$FeatureDir = Find-FeatureDirByPrefix -RepoRoot $RepoRoot -BranchName $CurrentBranch

# Collect project state
$FeatureName = ""
$SpecStatus = "not_found"
$PlanStatus = "not_found"
$TasksStatus = "not_found"

if ($FeatureDir -and (Test-Path $FeatureDir)) {
    $FeatureName = Split-Path $FeatureDir -Leaf

    if (Test-Path (Join-Path $FeatureDir "spec.md")) {
        $SpecStatus = "exists"
    }
    if (Test-Path (Join-Path $FeatureDir "plan.md")) {
        $PlanStatus = "exists"
    }
    if (Test-Path (Join-Path $FeatureDir "tasks.md")) {
        $TasksStatus = "exists"
    }
}

# Count total features
$TotalFeatures = 0
$SpecsDir = Join-Path $RepoRoot "specs"
if (Test-Path $SpecsDir) {
    $TotalFeatures = (Get-ChildItem -Path $SpecsDir -Directory -ErrorAction SilentlyContinue).Count
}

# Check constitution
$ConstitutionFile = Join-Path $RepoRoot "memory\constitution.md"
$ConstitutionExists = Test-Path $ConstitutionFile

# Estimate token savings (heuristic: assume typical session is at 80-100K)
# Pruning typically saves 40-60K tokens
$EstimatedSavings = 50000

$SummaryFile = Join-Path $MemoryDir "session-summary-$CurrentDate.md"

# Output results
if ($Json) {
    $Output = @{
        timestamp = "$CurrentDate $CurrentTime"
        current_feature = $FeatureName
        current_branch = $CurrentBranch
        spec_status = $SpecStatus
        plan_status = $PlanStatus
        tasks_status = $TasksStatus
        total_features = $TotalFeatures
        constitution_exists = $ConstitutionExists
        memory_dir = $MemoryDir
        summary_file = $SummaryFile
        estimated_token_savings = $EstimatedSavings
    }

    $Output | ConvertTo-Json -Depth 10
}
else {
    Write-Host "Session Prune - Data Collection"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host ""
    Write-Host "Current State:"
    Write-Host "  Feature: $FeatureName"
    Write-Host "  Branch: $CurrentBranch"
    Write-Host "  Total Features: $TotalFeatures"
    Write-Host "  Constitution: $ConstitutionExists"
    Write-Host ""
    Write-Host "Specification Status:"
    Write-Host "  spec.md: $SpecStatus"
    Write-Host "  plan.md: $PlanStatus"
    Write-Host "  tasks.md: $TasksStatus"
    Write-Host ""
    Write-Host "Next Steps:"
    Write-Host "  The AI agent will now create a compressed session summary"
    Write-Host "  based on the conversation history and this project state."
    Write-Host ""
    Write-Host "  Summary will be saved to:"
    Write-Host "  $SummaryFile"
    Write-Host ""
    Write-Host "  Expected token savings: ~$EstimatedSavings tokens"
}
