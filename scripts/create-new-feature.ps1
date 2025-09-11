# Create a new feature branch, directory structure, and template
# Usage:  ./create-new-feature.ps1 "feature description"
#         ./create-new-feature.ps1 --json "feature description"

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true, Position = 0, ValueFromRemainingArguments = $true)]
  [string[]]$FeatureDescriptionWords,

  [Parameter(Mandatory = $false)]
  [switch]$Json
)

# Source common functions by dot-sourcing the common script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path -Path $ScriptDir -ChildPath "common.ps1")

$FeatureDescription = $FeatureDescriptionWords -join " "

$RepoRoot = Get-RepoRoot
$SpecsDir = Join-Path -Path $RepoRoot -ChildPath "specs"

# Create specs directory if it doesn't exist
if (-not (Test-Path -Path $SpecsDir -PathType Container)) {
  New-Item -Path $SpecsDir -ItemType Directory | Out-Null
}

# Find the highest numbered feature directory to determine the next number
$Highest = 0
Get-ChildItem -Path $SpecsDir -Directory | ForEach-Object {
  if ($_.Name -match '^(\d+)') {
    $number = [int]$matches[1]
    if ($number -gt $Highest) {
      $Highest = $number
    }
  }
}

# Generate next feature number with three-digit padding
$Next = $Highest + 1
$FeatureNum = "{0:D3}" -f $Next

# Sanitize the feature description to create git-friendly branch name
$BranchNameSlug = $FeatureDescription.ToLower() -replace '[^a-z0-9\s]', '' -replace '\s+', '-' -replace '-+', '-' -replace '^-|-$', ''

# Extract 2-3 meaningful words for a concise branch name
$Words = ($BranchNameSlug -split '-')[0..2] -join '-'

# Final branch name format: ###-short-description
$BranchName = "$FeatureNum-$Words"

# Create and switch to the new git branch
git checkout -b $BranchName

# Create the feature-specific directory
$FeatureDir = Join-Path -Path $SpecsDir -ChildPath $BranchName
New-Item -Path $FeatureDir -ItemType Directory | Out-Null

# Copy the spec template int the new feature directory
$Template = Join-Path -Path $RepoRoot -ChildPath "templates/spec-template.md"
$SpecFile = Join-Path -Path $FeatureDir -ChildPath "spec.md"

if (Test-Path -Path $Template -PathType Leaf) {
  Copy-Item -Path $Template -Destination $SpecFile
}
else {
  Write-Warning "Template not found at $Template"
  New-Item -Path $SpecFile -ItemType File | Out-Null
}

# Output results in the requested format (JSON or key-value)
if ($Json) {
  $output = @{
    BRANCH_NAME = $BranchName
    SPEC_FILE   = $SpecFile
    FEATURE_NUM = $FeatureNum
  }
  $output | ConvertTo-Json -Compress
}
else {
  Write-Host "BRANCH_NAME: $BranchName"
  Write-Host "SPEC_FILE:   $SpecFile"
  Write-Host "FEATURE_NUM: $FeatureNum"
}
