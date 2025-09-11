# Common functions and variables for all PowerShell scripts

# Get repository root
function Get-RepoRoot {
  return git rev-parse --show-toplevel
}

# Get current branch
function Get-CurrentBranch {
  return git rev-parse --abbrev-ref HEAD
}

# Check if current branch is a feature branch
# Throws a terminating error if the branch is not valid
function Test-FeatureBranch {
  param(
    [string]$Branch
  )
  if ($Branch -notmatch '^[0-9]{3}-') {
    throw "ERROR: Not a feature branch. Current branch: $Branch. Feature branches should be named like: 001-feature-name"
  }
}

# Get feature directory path
function Get-FeatureDir {
  param(
    [string]$RepoRoot,
    [string]$Branch
  )
  return Join-Path -Path $RepoRoot -ChildPath "specs/$Branch"
}

# Get all standard paths for a feature
# Returns a PSCustomObject with all paths for the calling scripts to use
function Get-FeaturePaths {
  $repoRoot = Get-RepoRoot
  $currentBranch = Get-CurrentBranch
  $featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $currentBranch

  # Ensure the branch is a valid feature branch before returning paths
  Test-FeatureBranch -Branch $currentBranch

  return [PSCustomObject]@{
    REPO_ROOT      = $repoRoot
    CURRENT_BRANCH = $currentBranch
    FEATURE_DIR    = $featureDir
    FEATURE_SPEC   = Join-Path -Path $featureDir -ChildPath "spec.md"
    IMPL_PLAN      = Join-Path -Path $featureDir -ChildPath "plan.md"
    TASKS          = Join-Path -Path $featureDir -ChildPath "tasks.md"
    RESEARCH       = Join-Path -Path $featureDir -ChildPath "research.md"
    DATA_MODEL     = Join-Path -Path $featureDir -ChildPath "data-model.md"
    QUICKSTART     = Join-Path -Path $featureDir -ChildPath "quickstart.md"
    CONTRACTS_DIR  = Join-Path -Path $featureDir -ChildPath "contracts"
  }
}

# Check if a file exists and report its status to the console
function Test-SpecFile {
  param(
    [string]$File,
    [string]$Description
  )
  if (Test-Path -Path $File -PathType Leaf) {
    Write-Host " ✓ $Description" -ForegroundColor Green
    return $true
  }
  else {
    Write-Host " ✗ $Description" -ForegroundColor Yellow
    return $false
  }
}

# Check if a directory exists and is not empty, reporting its status
function Test-SpecDirectory {
  param(
    [string]$Directory,
    [string]$Description
  )
  if ((Test-Path -Path $Directory -PathType Container) -and (Get-ChildItem -Path $Directory)) {
    Write-Host " ✓ $Description" -ForegroundColor Green
    return $true
  }
  else {
    Write-Host " ✗ $Description" -ForegroundColor Yellow
    return $false
  }
}

# Export functions so they can be imported by other scripts using dot-sourcing
Export-ModuleMember -Function Get-RepoRoot, Get-CurrentBranch, Test-FeatureBranch, Get-FeatureDir, Get-FeaturePaths, Test-SpecFile, Test-SpecDirectory
