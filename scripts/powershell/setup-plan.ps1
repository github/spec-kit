#!/usr/bin/env pwsh
# Setup implementation plan for a feature

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help,
    # Capture extra positional arguments to match Bash/Python behavior.
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output "Usage: ./setup-plan.ps1 [-Json] [-Help]"
    Write-Output "  -Json     Output results in JSON format"
    Write-Output "  -Help     Show this help message"
    exit 0
}

if ($RemainingArgs.Count -gt 0) {
    [Console]::Error.WriteLine("ERROR: Unknown option '$($RemainingArgs[0])'")
    exit 1
}

# Load common functions
. "$PSScriptRoot/common.ps1"

# Get all paths and variables from common functions
$paths = Get-FeaturePathsEnv -ReturnNullOnError
if (-not $paths) {
    [Console]::Error.WriteLine("ERROR: Failed to resolve feature paths")
    exit 1
}

# Ensure the feature directory exists
New-Item -ItemType Directory -Path $paths.FEATURE_DIR -Force | Out-Null

$planEntry = Get-ChildItem -LiteralPath $paths.FEATURE_DIR -Force -ErrorAction Stop |
    Where-Object { $_.Name -eq 'plan.md' } | Select-Object -First 1
if ($planEntry -and ($planEntry.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
    [Console]::Error.WriteLine("ERROR: Plan destination must not be a symbolic link.")
    exit 1
}

# Copy plan template if plan doesn't already exist
if (Test-Path -LiteralPath $paths.IMPL_PLAN -PathType Leaf) {
    if ($Json) {
        [Console]::Error.WriteLine("Plan already exists at $($paths.IMPL_PLAN), skipping template copy")
    } else {
        Write-Output "Plan already exists at $($paths.IMPL_PLAN), skipping template copy"
    }
} else {
    $content = Resolve-TemplateContent -TemplateName 'plan-template' -RepoRoot $paths.REPO_ROOT
    if ($null -ne $content) {
        if ($content.Length -eq 0) {
            [Console]::Error.WriteLine(
                "ERROR: Plan template is empty; no new plan.md was created."
            )
            [Console]::Error.WriteLine("Restore a valid plan template and rerun plan setup.")
            exit 1
        }
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        try {
            $plan = [System.IO.File]::Open(
                $paths.IMPL_PLAN, [System.IO.FileMode]::CreateNew,
                [System.IO.FileAccess]::Write, [System.IO.FileShare]::None
            )
            try {
                $bytes = $utf8NoBom.GetBytes($content)
                $plan.Write($bytes, 0, $bytes.Length)
            } finally {
                $plan.Dispose()
            }
        } catch {
            [Console]::Error.WriteLine("ERROR: Cannot create plan: $($_.Exception.Message)")
            exit 1
        }
        # Emit the copy status like the bash twin (setup-plan.sh); route to stderr
        # in -Json mode so stdout stays pure JSON, matching the sibling messages.
        if ($Json) {
            [Console]::Error.WriteLine("Copied plan template to $($paths.IMPL_PLAN)")
        } else {
            Write-Output "Copied plan template to $($paths.IMPL_PLAN)"
        }
    } else {
        [Console]::Error.WriteLine(
            "ERROR: Plan template not found; no new plan.md was created."
        )
        [Console]::Error.WriteLine("Restore a valid plan template and rerun plan setup.")
        exit 1
    }
}

# Output results
if ($Json) {
    $result = [PSCustomObject]@{
        FEATURE_SPEC = $paths.FEATURE_SPEC
        IMPL_PLAN = $paths.IMPL_PLAN
        FEATURE_DIR = $paths.FEATURE_DIR
        BRANCH = $paths.CURRENT_BRANCH
    }
    $result | ConvertTo-Json -Compress
} else {
    Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
    Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
    Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
    Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
}
