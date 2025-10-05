#!/usr/bin/env pwsh
# Decompose parent feature spec into capabilities

param(
    [Parameter(Position=0)]
    [string]$SpecPath,

    [switch]$Json,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: decompose-feature.ps1 [-Json] [path/to/parent/spec.md]"
    Write-Host "Decomposes a parent feature spec into capability-based breakdown"
    exit 0
}

# Determine spec path
if ([string]::IsNullOrEmpty($SpecPath)) {
    # Try to find spec.md in current branch's specs directory
    $repoRoot = git rev-parse --show-toplevel
    $branchName = git rev-parse --abbrev-ref HEAD

    # Extract feature ID from branch name (username/jira-123.feature-name -> jira-123.feature-name)
    $featureId = $branchName -replace '^[^/]*/', ''

    $SpecPath = Join-Path $repoRoot "specs" $featureId "spec.md"
}

# Validate spec exists
if (-not (Test-Path $SpecPath)) {
    Write-Error "ERROR: Spec file not found at $SpecPath"
    Write-Host "Usage: decompose-feature.ps1 [path/to/parent/spec.md]"
    exit 1
}

$specDir = Split-Path -Parent $SpecPath
$repoRoot = git rev-parse --show-toplevel

# Create capabilities.md from template
$decomposeTemplate = Join-Path $repoRoot "templates" "decompose-template.md"
$capabilitiesFile = Join-Path $specDir "capabilities.md"

if (-not (Test-Path $decomposeTemplate)) {
    Write-Error "ERROR: Decompose template not found at $decomposeTemplate"
    exit 1
}

# Copy template to capabilities.md
Copy-Item -Path $decomposeTemplate -Destination $capabilitiesFile -Force

# Output results
if ($Json) {
    $output = @{
        SPEC_PATH = $SpecPath
        CAPABILITIES_FILE = $capabilitiesFile
        SPEC_DIR = $specDir
    }
    $output | ConvertTo-Json -Compress
} else {
    Write-Host "SPEC_PATH: $SpecPath"
    Write-Host "CAPABILITIES_FILE: $capabilitiesFile"
    Write-Host "SPEC_DIR: $specDir"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Edit $capabilitiesFile to define capabilities"
    Write-Host "2. AI will create capability subdirectories (cap-001/, cap-002/, ...)"
    Write-Host "3. AI will generate scoped spec.md in each capability directory"
}
