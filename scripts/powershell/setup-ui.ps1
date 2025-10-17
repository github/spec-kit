#!/usr/bin/env pwsh
# setup-ui.ps1: Prepare UI blueprint files for the current feature.
# Emits JSON with absolute paths for downstream automation.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"

$envs = Get-FeaturePathsEnv

$branchOk = Test-FeatureBranch -Branch $($envs.CURRENT_BRANCH) -HasGit $($envs.HAS_GIT)
if (-not $branchOk) { exit 1 }

$uiDir = Join-Path $($envs.FEATURE_DIR) 'ui'
New-Item -ItemType Directory -Path $uiDir -Force | Out-Null

# Resolve template root for both packaged projects and repo checkouts
$specifyTemplates = Join-Path $($envs.REPO_ROOT) '.specify/templates/ui'
$repoTemplates = Join-Path $($envs.REPO_ROOT) 'templates/ui'
if (Test-Path $specifyTemplates -PathType Container) {
  $templateRoot = $specifyTemplates
} elseif (Test-Path $repoTemplates -PathType Container) {
  $templateRoot = $repoTemplates
} else {
  Write-Error "[speckit.ui] UI templates not found. Expected at either:`n  - $specifyTemplates`n  - $repoTemplates`nPlease initialize the project via 'specify init' or ensure templates/ui exists."
  exit 1
}

function Copy-Or-Fail {
  param([string]$Src, [string]$Dest, [string]$Name)
  if (Test-Path $Src -PathType Leaf) { Copy-Item -Path $Src -Destination $Dest -Force }
  else { throw "Missing template: $Name at $Src" }
}

$tokensFile = Join-Path $uiDir 'tokens.json'
$componentsSpec = Join-Path $uiDir 'components.md'
$flowsFile = Join-Path $uiDir 'flows.mmd'
$htmlSkeleton = Join-Path $uiDir 'skeleton.html'
$bddFile = Join-Path $uiDir 'stories.feature'
$typesTs = Join-Path $uiDir 'types.ts'
$typesSchema = Join-Path $uiDir 'types.schema.json'
$readmeFile = Join-Path $uiDir 'README.md'

Copy-Or-Fail (Join-Path $templateRoot 'tokens.json') $tokensFile 'tokens.json'
Copy-Or-Fail (Join-Path $templateRoot 'components.md') $componentsSpec 'components.md'
Copy-Or-Fail (Join-Path $templateRoot 'flows.mmd') $flowsFile 'flows.mmd'
Copy-Or-Fail (Join-Path $templateRoot 'skeleton.html') $htmlSkeleton 'skeleton.html'
Copy-Or-Fail (Join-Path $templateRoot 'stories.feature') $bddFile 'stories.feature'
Copy-Or-Fail (Join-Path $templateRoot 'types.ts') $typesTs 'types.ts'
if (Test-Path (Join-Path $templateRoot 'types.schema.json') -PathType Leaf) {
  Copy-Item -Path (Join-Path $templateRoot 'types.schema.json') -Destination $typesSchema -Force
}
Copy-Or-Fail (Join-Path $templateRoot 'README.md') $readmeFile 'README.md'

$json = [ordered]@{
  UI_DIR = $uiDir
  TOKENS_FILE = $tokensFile
  COMPONENTS_SPEC = $componentsSpec
  FLOWS_FILE = $flowsFile
  HTML_SKELETON = $htmlSkeleton
  BDD_FILE = $bddFile
  TYPES_TS = $typesTs
  TYPES_SCHEMA = if (Test-Path $typesSchema -PathType Leaf) { $typesSchema } else { '' }
  README_FILE = $readmeFile
} | ConvertTo-Json -Compress

Write-Output $json
