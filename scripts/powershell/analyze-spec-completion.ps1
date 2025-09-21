# Spec Completion Analyzer - Detailed analysis of spec folder completeness
param(
    [switch]$Json,
    [string]$SpecPath = "",
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\analyze-spec-completion.ps1 [-Json] [-SpecPath <path>]"
    Write-Host "Analyzes completion status of specs. If SpecPath provided, analyzes single spec."
    Write-Host "Otherwise analyzes all specs in specs/ directory."
    exit 0
}

# Get repository root
$repoRoot = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: Not in a git repository. Run this script from within a git repository."
    exit 1
}

$specsDir = Join-Path $repoRoot "specs"

# Define required artifacts for a complete spec
$requiredArtifacts = @(
    "spec.md",
    "plan.md", 
    "tasks.md",
    "data-model.md",
    "research.md",
    "quickstart.md"
)

# Function to analyze a single spec folder
function Analyze-Spec {
    param([string]$SpecPath)
    
    $specName = Split-Path $SpecPath -Leaf
    
    # Check if directory exists
    if (!(Test-Path $SpecPath -PathType Container)) {
        Write-Error "ERROR: Spec directory not found: $SpecPath"
        return $null
    }
    
    $missingArtifacts = @()
    $presentArtifacts = @()
    $completionPercentage = 0
    $taskCompletion = ""
    $totalTasks = 0
    $completedTasks = 0
    
    # Check required artifacts
    foreach ($artifact in $requiredArtifacts) {
        $artifactPath = Join-Path $SpecPath $artifact
        if (Test-Path $artifactPath) {
            $presentArtifacts += $artifact
        } else {
            $missingArtifacts += $artifact
        }
    }
    
    # Special analysis for tasks.md
    $tasksPath = Join-Path $SpecPath "tasks.md"
    if (Test-Path $tasksPath) {
        $tasksContent = Get-Content $tasksPath -Raw
        $totalTasks = ([regex]::Matches($tasksContent, "^- \[ \]", [System.Text.RegularExpressions.RegexOptions]::Multiline)).Count
        $completedTasks = ([regex]::Matches($tasksContent, "^- \[x\]", [System.Text.RegularExpressions.RegexOptions]::Multiline)).Count
        
        if ($totalTasks -gt 0) {
            $taskCompletion = "$completedTasks/$totalTasks"
        } else {
            $taskCompletion = "0/0"
        }
    }
    
    # Calculate completion percentage
    $totalRequired = $requiredArtifacts.Length
    $presentCount = $presentArtifacts.Length
    $completionPercentage = [math]::Round(($presentCount * 100) / $totalRequired)
    
    # Determine completion status
    $status = ""
    if ($completionPercentage -eq 100) {
        if ($totalTasks -gt 0 -and $completedTasks -eq $totalTasks) {
            $status = "fully_complete"
        } elseif ($totalTasks -gt 0 -and $completedTasks -gt 0) {
            $status = "implementation_in_progress"
        } else {
            $status = "ready_for_implementation"
        }
    } elseif ($completionPercentage -ge 50) {
        $status = "partially_complete"
    } else {
        $status = "incomplete"
    }
    
    # Check for contracts directory
    $contractsPath = Join-Path $SpecPath "contracts"
    $contractsStatus = "missing"
    if (Test-Path $contractsPath -PathType Container) {
        $contractFiles = Get-ChildItem $contractsPath -Filter "*.md" -File
        if ($contractFiles.Count -gt 0) {
            $contractsStatus = "present"
        } else {
            $contractsStatus = "empty"
        }
    }
    
    $result = @{
        spec_name = $specName
        status = $status
        completion_percentage = $completionPercentage
        present_artifacts = $presentArtifacts
        missing_artifacts = $missingArtifacts
        task_completion = $taskCompletion
        contracts_status = $contractsStatus
        total_tasks = $totalTasks
        completed_tasks = $completedTasks
    }
    
    if ($Json) {
        return $result
    } else {
        Write-Host "=== Spec: $specName ==="
        Write-Host "Status: $status"
        Write-Host "Completion: $completionPercentage%"
        Write-Host "Task Progress: $taskCompletion"
        Write-Host "Contracts: $contractsStatus"
        if ($presentArtifacts.Length -gt 0) {
            Write-Host "Present: $($presentArtifacts -join ', ')"
        }
        if ($missingArtifacts.Length -gt 0) {
            Write-Host "Missing: $($missingArtifacts -join ', ')"
        }
        Write-Host ""
    }
}

# Main execution
if ($SpecPath) {
    # Analyze single spec
    if (![System.IO.Path]::IsPathRooted($SpecPath)) {
        # Relative path, make it absolute
        $SpecPath = Join-Path $specsDir $SpecPath
    }
    $result = Analyze-Spec -SpecPath $SpecPath
    if ($Json -and $result) {
        $result | ConvertTo-Json -Depth 10
    }
} else {
    # Analyze all specs
    if (!(Test-Path $specsDir -PathType Container)) {
        if ($Json) {
            @{error = "No specs directory found"; specs = @()} | ConvertTo-Json
        } else {
            Write-Host "No specs directory found at: $specsDir"
        }
        exit 1
    }
    
    $allResults = @()
    
    Get-ChildItem $specsDir -Directory | ForEach-Object {
        $result = Analyze-Spec -SpecPath $_.FullName
        if ($Json -and $result) {
            $allResults += $result
        }
    }
    
    if ($Json) {
        @{
            specs = $allResults
            analysis_date = Get-Date -Format "o"
        } | ConvertTo-Json -Depth 10
    } else {
        Write-Host "=== Spec Completion Analysis ==="
        Write-Host "Date: $(Get-Date)"
        Write-Host ""
        
        Get-ChildItem $specsDir -Directory | ForEach-Object {
            Analyze-Spec -SpecPath $_.FullName | Out-Null
        }
    }
}