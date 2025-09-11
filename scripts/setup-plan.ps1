# Setup implementation plan structure for current branch
# Returns paths needed for implementation plan generation
# Usage:  ./setup-plan.ps1 [--json]

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
  Write-Error $_.Exception.Message
  exit 1
}

# Create specs directory if it doesn't exist
if (-not (Test-Path -Path $paths.FEATURE_DIR -PathType Container)) {
  New-Item -Path $paths.FEATURE_DIR -ItemType Directory | Out-Null
}

# Copy plan template if it exists
$Template = Join-Path -Path $paths.REPO_ROOT -ChildPath "templates/plan-template.md"
if (Test-Path -Path $Template -PathType Leaf) {
  Copy-Item -Path $Template -Destination $paths.IMPL_PLAN
}

# Output results in the requested format
if ($Json) {
  @{
    FEATURE_SPEC = $paths.FEATURE_SPEC
    IMPL_PLAN    = $paths.IMPL_PLAN
    SPECS_DIR    = $paths.FEATURE_DIR
    BRANCH       = $paths.CURRENT_BRANCH
  } | ConvertTo-Json -Compress
}
else {
  Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
  Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
  Write-Output "SPECS_DIR: $($paths.FEATURE_DIR)"
  Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
}
