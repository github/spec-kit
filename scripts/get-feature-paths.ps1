# Get paths for current feature branch without creating anything.
# Used by commands that need to find existing feature files.

# Source common functions
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir -ChildPath "common.ps1")

try {
  # Get all paths for the current feature
  $paths = Get-FeaturePaths

  # Output paths in key: value format
  Write-Host "REPO_ROOT: $($paths.REPO_ROOT)"
  Write-Host "BRANCH: $($paths.CURRENT_BRANCH)"
  Write-Host "FEATURE_DIR: $($paths.FEATURE_DIR)"
  Write-Host "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
  Write-Host "IMPL_PLAN: $($paths.IMPL_PLAN)"
  Write-Host "TASKS: $($paths.TASKS)"
}
catch {
  # If Get-FeaturePaths throws (e.g., not on a feature branch), exit gracefully
  Write-Error $_.Exception.Message
  exit 1
}
