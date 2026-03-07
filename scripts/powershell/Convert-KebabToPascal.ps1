# Convert-KebabToPascal.ps1
# Helper script to convert kebab-case arguments to PowerShell PascalCase
# Usage: Convert-KebabToPascal.ps1 <target-script> <args...>
#
# Escape hatch: Use -- to stop conversion for remaining arguments
# Example: script.ps1 --json -- --custom-flag value
#          Converts: --json to -Json
#          Passes through: --custom-flag value (unchanged)

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$TargetScript,
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$convertedArgs = @()
$stopConversion = $false

foreach ($arg in $Arguments) {
    # Check for -- separator (stop conversion for remaining args)
    if ($arg -eq '--' -and -not $stopConversion) {
        $stopConversion = $true
        if ($env:DEBUG_WRAPPER) {
            Write-Host "[DEBUG] Stop conversion marker found, passing through remaining args" -ForegroundColor Magenta
        }
        continue  # Don't include the -- itself
    }
    
    if (-not $stopConversion -and $arg -match '^--([a-z]+(-[a-z]+)*)$') {
        # Convert --kebab-case to -PascalCase
        $parts = $matches[1] -split '-'
        $pascalCase = $parts | ForEach-Object {
            $_.Substring(0,1).ToUpper() + $_.Substring(1).ToLower()
        }
        $converted = '-' + ($pascalCase -join '')
        $convertedArgs += $converted
        
        # Debug output (only if DEBUG_WRAPPER env var is set)
        if ($env:DEBUG_WRAPPER) {
            Write-Host "[DEBUG] Converted: $arg -> $converted" -ForegroundColor Cyan
        }
    }
    elseif (-not $stopConversion -and $arg -eq '-h') {
        # Special case: -h -> -Help
        $convertedArgs += '-Help'
        if ($env:DEBUG_WRAPPER) {
            Write-Host "[DEBUG] Converted: $arg -> -Help" -ForegroundColor Cyan
        }
    }
    else {
        # Pass through unchanged (values, already-converted flags, post-separator args, etc.)
        $convertedArgs += $arg
        if ($env:DEBUG_WRAPPER -and $stopConversion) {
            Write-Host "[DEBUG] Pass-through: $arg" -ForegroundColor Gray
        }
    }
}

# Debug output: show final command
if ($env:DEBUG_WRAPPER) {
    Write-Host "[DEBUG] Executing: $TargetScript $($convertedArgs -join ' ')" -ForegroundColor Yellow
}

# Execute target script with converted arguments
& $TargetScript @convertedArgs
exit $LASTEXITCODE
