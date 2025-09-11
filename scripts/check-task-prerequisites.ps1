# Check that implementation plan exists and find optional design documents
# Usage:  ./check-task-prerequisites.ps1 [--json]

[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [switch]$Json
)

# Source common functions
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir -ChildPath "common.ps1")

try {
  # Get all paths for the current feature
  $paths = Get-FeaturePaths
}
catch {
  # If Get-FeaturePaths throws (e.g., not a feature branch), exit gracefully
  Write-Error $_.Exception.Message
  exit 1
}

# Check if feature directory exists
if (-not (Test-Path -Path $paths.FEATURE_DIR -PathType Container)) {
  Write-Error "ERROR: Feature directory not found: $($paths.FEATURE_DIR)"
  Write-Error "Run /specify first to create the feature structure."
  exit 1
}

# Check for implementation plan (required)
if (-not (Test-Path -Path $paths.IMPL_PLAN -PathType Leaf)) {
  Write-Error "ERROR: plan.md not found in $($paths.FEATURE_DIR)"
  Write-Error "Run /plan first to create the plan."
  exit 1
}

if ($Json) {
  # Build an array of available optional design documents
  $docs = [System.Collections.Generic.List[string]]::new()
  if (Test-Path -Path $paths.RESEARCH -PathType Leaf) { $docs.Add("research.md") }
  if (Test-Path -Path $paths.DATA_MODEL -PathType Leaf) { $docs.Add("data-model.md") }
  if ((Test-Path -Path $paths.CONTRACTS_DIR -PathType Container) -and (Get-ChildItem $paths.CONTRACTS_DIR)) { $docs.Add("contracts/") }
  if (Test-Path -Path $paths.QUICKSTART -PathType Leaf) { $docs.Add("quickstart.md") }

  # Output the results as a JSON object
  @{
    FEATURE_DIR    = $paths.FEATURE_DIR
    AVAILABLE_DOCS = $docs
  } | ConvertTo-Json -Compress
}
else {
  # Output in a human-readable format
  Write-Host "FEATURE_DIR: $($paths.FEATURE_DIR)"
  Write-Host "AVAILABLE_DOCS:"

  # Use common check functions to display status
  Test-SpecFile -File $paths.RESEARCH -Description "research.md"
  Test-SpecFile -File $paths.DATA_MODEL -Description "data-model.md"
  Test-SpecDirectory -Directory $paths.CONTRACTS_DIR -Description "contracts/"
  Test-SpecFile -File $paths.QUICKSTART -Description "quickstart.md"
}
