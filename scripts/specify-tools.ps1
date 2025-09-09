# PowerShell wrapper for spec-kit scripts
# Provides Windows-native PowerShell integration for common spec-kit operations

param(
    [Parameter(Position=0, Mandatory=$true)]
    [ValidateSet("create-feature", "setup-plan", "check-prerequisites", "update-context", "get-paths")]
    [string]$Command,
    
    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Arguments = @(),
    
    [switch]$Json,
    [switch]$Help
)

# Get script directory and repository root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) {
    Write-Error "Not in a git repository"
    exit 1
}

# Map commands to script names
$ScriptMapping = @{
    "create-feature" = "create_new_feature"
    "setup-plan" = "setup_plan"
    "check-prerequisites" = "check_task_prerequisites"
    "update-context" = "update_agent_context"
    "get-paths" = "get_feature_paths"
}

$ScriptName = $ScriptMapping[$Command]
if (-not $ScriptName) {
    Write-Error "Unknown command: $Command"
    exit 1
}

# Build command arguments
$CmdArgs = @()
if ($Json) { $CmdArgs += "--json" }
if ($Help) { $CmdArgs += "--help" }
$CmdArgs += $Arguments

# Try Python script first, then bash as fallback
$PythonScript = Join-Path $RepoRoot "scripts\py\$ScriptName.py"
$BashScript = Join-Path $RepoRoot "scripts\$($ScriptName -replace '_', '-').sh"

if (Test-Path $PythonScript) {
    Write-Verbose "Using Python script: $PythonScript"
    & python $PythonScript @CmdArgs
} elseif (Test-Path $BashScript) {
    Write-Verbose "Using bash script: $BashScript"
    & bash $BashScript @CmdArgs
} else {
    Write-Error "Script not found: $ScriptName"
    exit 1
}

exit $LASTEXITCODE