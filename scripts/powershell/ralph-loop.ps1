<#
.SYNOPSIS
    Ralph loop orchestrator for autonomous implementation.

.DESCRIPTION
    Executes GitHub Copilot CLI in a controlled loop, processing tasks from tasks.md.
    Each iteration spawns a fresh agent context with the speckit.implement profile.
    
    The loop terminates when:
    - Agent outputs <promise>COMPLETE</promise>
    - Max iterations reached
    - All tasks in tasks.md are complete
    - User interrupts with Ctrl+C

.PARAMETER FeatureName
    Name of the feature being implemented (e.g., "001-ralph-loop-implement")

.PARAMETER TasksPath
    Path to tasks.md file

.PARAMETER SpecDir
    Path to the spec directory containing plan.md, spec.md, etc.

.PARAMETER MaxIterations
    Maximum number of iterations before stopping (default: 10)

.PARAMETER Model
    AI model to use (default: claude-sonnet-4.5)

.PARAMETER DetailedOutput
    Show detailed iteration output

.EXAMPLE
    .\ralph-loop.ps1 -FeatureName "001-feature" -TasksPath "specs/001-feature/tasks.md" -SpecDir "specs/001-feature" -MaxIterations 10 -Model "claude-sonnet-4.5"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$FeatureName,
    
    [Parameter(Mandatory = $true)]
    [string]$TasksPath,
    
    [Parameter(Mandatory = $true)]
    [string]$SpecDir,
    
    [Parameter(Mandatory = $false)]
    [int]$MaxIterations = 10,
    
    [Parameter(Mandatory = $false)]
    [string]$Model = "claude-sonnet-4.5",
    
    [Parameter(Mandatory = $false)]
    [string]$WorkingDirectory = "",
    
    [switch]$DetailedOutput
)

# Import common functions if available
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CommonScript = Join-Path $ScriptDir "common.ps1"
if (Test-Path $CommonScript) {
    . $CommonScript
}

# Resolve working directory - if not provided, use the directory containing tasks.md
if (-not $WorkingDirectory) {
    # Infer from TasksPath - go up to find the repo root (directory with .git or .specify)
    $taskDir = Split-Path -Parent ([System.IO.Path]::GetFullPath($TasksPath))
    $searchDir = $taskDir
    while ($searchDir -and -not (Test-Path (Join-Path $searchDir ".git")) -and -not (Test-Path (Join-Path $searchDir ".specify"))) {
        $parent = Split-Path -Parent $searchDir
        if ($parent -eq $searchDir) { break }
        $searchDir = $parent
    }
    if ($searchDir -and ((Test-Path (Join-Path $searchDir ".git")) -or (Test-Path (Join-Path $searchDir ".specify")))) {
        $WorkingDirectory = $searchDir
    } else {
        $WorkingDirectory = (Get-Location).Path
    }
}

# Resolve paths
$RepoRoot = $WorkingDirectory
$TasksPath = [System.IO.Path]::GetFullPath($TasksPath)
$SpecDir = [System.IO.Path]::GetFullPath($SpecDir)
$ProgressPath = Join-Path $SpecDir "progress.md"

#region Helper Functions

function Write-RalphHeader {
    param([int]$Iteration, [int]$Max)
    
    $border = "=" * 60
    Write-Host ""
    Write-Host $border -ForegroundColor Cyan
    Write-Host "  Ralph Loop - $FeatureName" -ForegroundColor Cyan
    Write-Host "  Iteration $Iteration of $Max" -ForegroundColor White
    Write-Host $border -ForegroundColor Cyan
    Write-Host ""
}

function Write-IterationStatus {
    param(
        [int]$Iteration,
        [string]$Status,
        [string]$Message
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $statusIcon = switch ($Status) {
        "running"   { "o" }
        "success"   { "*" }
        "failure"   { "x" }
        "skipped"   { "-" }
        default     { "o" }
    }
    $statusColor = switch ($Status) {
        "running"   { "Cyan" }
        "success"   { "Green" }
        "failure"   { "Red" }
        "skipped"   { "Yellow" }
        default     { "White" }
    }
    
    Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
    Write-Host $statusIcon -NoNewline -ForegroundColor $statusColor
    Write-Host " Iteration $Iteration" -NoNewline -ForegroundColor White
    if ($Message) {
        Write-Host " - $Message" -ForegroundColor DarkGray
    } else {
        Write-Host ""
    }
}

function Get-IncompleteTasks {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        return @()
    }
    
    $content = Get-Content $Path -Raw
    $taskMatches = [regex]::Matches($content, '- \[ \] (T\d+.*?)(?=\r?\n|$)')
    
    return $taskMatches | ForEach-Object { $_.Groups[1].Value }
}

function Get-IncompleteTaskCount {
    param([string]$Path)
    
    return (Get-IncompleteTasks -Path $Path).Count
}

function Initialize-ProgressFile {
    param([string]$Path, [string]$Feature)
    
    if (-not (Test-Path $Path)) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $header = @"
# Ralph Progress Log

Feature: $Feature
Started: $timestamp

## Codebase Patterns

[Patterns discovered during implementation - updated by agent]

---

"@
        Set-Content -Path $Path -Value $header -Encoding UTF8
        Write-Host "Created progress log: $Path" -ForegroundColor DarkGray
    }
}

function Invoke-CopilotIteration {
    param(
        [string]$Model,
        [int]$Iteration,
        [string]$WorkDir,
        [switch]$Verbose
    )
    
    # Simple prompt - the speckit.ralph agent already knows to complete one work unit
    $prompt = "Iteration $Iteration - Complete one work unit from tasks.md"
    
    # Only show debug info when verbose
    if ($Verbose) {
        Write-Host "DEBUG: Prompt = $prompt" -ForegroundColor Magenta
        Write-Host "DEBUG: WorkDir = $WorkDir" -ForegroundColor Magenta
    }
    
    try {
        # Change to working directory so copilot finds the correct agents
        $originalDir = Get-Location
        if ($WorkDir -and (Test-Path $WorkDir)) {
            Push-Location $WorkDir
            if ($Verbose) {
                Write-Host "DEBUG: Changed to $WorkDir" -ForegroundColor Magenta
            }
        }
        
        # Refresh PATH to ensure pwsh is available (copilot CLI requires PowerShell 7+)
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        try {
            # Always stream copilot output in real-time so user can see what the agent is doing
            Write-Host ""
            Write-Host "--- Copilot Agent Output ---" -ForegroundColor DarkCyan
            $outputLines = @()
            # Use speckit.ralph agent - it already knows to complete one work unit
            & copilot --agent speckit.ralph -p $prompt --model $Model --allow-all-tools -s 2>&1 | ForEach-Object {
                Write-Host $_
                $outputLines += $_
            }
            $output = $outputLines -join "`n"
            $exitCode = $LASTEXITCODE
            Write-Host "--- End Agent Output ---" -ForegroundColor DarkCyan
            Write-Host ""
        }
        finally {
            if ($WorkDir -and (Test-Path $WorkDir)) {
                Pop-Location
            }
        }
        
        if ($Verbose) {
            Write-Host "DEBUG: copilot exit code = $exitCode" -ForegroundColor Magenta
        }
    }
    catch {
        $output = "Error invoking copilot: $_"
        $exitCode = 1
    }
    
    return @{
        Output = $output
        ExitCode = $exitCode
    }
}

function Test-CompletionSignal {
    param([string]$Output)
    
    return $Output -match '<promise>COMPLETE</promise>'
}

#endregion

#region Main Loop

# Initialize progress file
Initialize-ProgressFile -Path $ProgressPath -Feature $FeatureName

# Check initial task count
$initialTasks = Get-IncompleteTaskCount -Path $TasksPath
if ($initialTasks -eq 0) {
    Write-Host "All tasks are already complete!" -ForegroundColor Green
    Write-Host "<promise>COMPLETE</promise>"
    exit 0
}

Write-Host "Found $initialTasks incomplete task(s)" -ForegroundColor White

# Iteration tracking
$iteration = 1
$consecutiveFailures = 0
$maxConsecutiveFailures = 3
$completed = $false

# Register Ctrl+C handler
$interrupted = $false
[Console]::TreatControlCAsInput = $false

try {
    while ($iteration -le $MaxIterations -and -not $completed -and -not $interrupted) {
        Write-RalphHeader -Iteration $iteration -Max $MaxIterations
        Write-IterationStatus -Iteration $iteration -Status "running" -Message "Starting iteration"
        
        # Invoke Copilot CLI with speckit.ralph agent (agent already knows to complete one work unit)
        $verboseSwitch = @{}
        if ($DetailedOutput) { $verboseSwitch['Verbose'] = $true }
        $result = Invoke-CopilotIteration -Model $Model -Iteration $iteration -WorkDir $WorkingDirectory @verboseSwitch
        
        if ($DetailedOutput -or $result.ExitCode -ne 0) {
            Write-Host $result.Output
        }
        
        # Check for completion signal
        if (Test-CompletionSignal -Output $result.Output) {
            Write-IterationStatus -Iteration $iteration -Status "success" -Message "COMPLETE signal received"
            $completed = $true
            break
        }
        
        # Check exit code
        if ($result.ExitCode -ne 0) {
            $consecutiveFailures++
            Write-IterationStatus -Iteration $iteration -Status "failure" -Message "Exit code $($result.ExitCode) (failure $consecutiveFailures/$maxConsecutiveFailures)"
            
            if ($consecutiveFailures -ge $maxConsecutiveFailures) {
                Write-Host "Too many consecutive failures. Stopping loop." -ForegroundColor Red
                exit 1
            }
        } else {
            $consecutiveFailures = 0
            Write-IterationStatus -Iteration $iteration -Status "success" -Message "Iteration completed"
        }
        
        # Check remaining tasks
        $remainingTasks = Get-IncompleteTaskCount -Path $TasksPath
        if ($remainingTasks -eq 0) {
            Write-Host "All tasks complete!" -ForegroundColor Green
            $completed = $true
            break
        }
        
        Write-Host "$remainingTasks task(s) remaining" -ForegroundColor DarkGray
        
        $iteration++
    }
}
catch {
    if ($_.Exception.GetType().Name -eq "PipelineStoppedException") {
        $interrupted = $true
        Write-Host "`nInterrupted by user" -ForegroundColor Yellow
    } else {
        throw
    }
}
finally {
    [Console]::TreatControlCAsInput = $false
}

#endregion

#region Summary

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  Ralph Loop Summary" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

$finalTasks = Get-IncompleteTaskCount -Path $TasksPath
$tasksCompleted = $initialTasks - $finalTasks

Write-Host "  Iterations run: $($iteration - 1)" -ForegroundColor White
Write-Host "  Tasks completed: $tasksCompleted" -ForegroundColor White
Write-Host "  Tasks remaining: $finalTasks" -ForegroundColor White

if ($completed) {
    Write-Host "  Status: " -NoNewline -ForegroundColor White
    Write-Host "COMPLETED" -ForegroundColor Green
    exit 0
} elseif ($interrupted) {
    Write-Host "  Status: " -NoNewline -ForegroundColor White
    Write-Host "INTERRUPTED" -ForegroundColor Yellow
    exit 130
} else {
    Write-Host "  Status: " -NoNewline -ForegroundColor White
    Write-Host "ITERATION LIMIT REACHED" -ForegroundColor Yellow
    exit 1
}

#endregion
