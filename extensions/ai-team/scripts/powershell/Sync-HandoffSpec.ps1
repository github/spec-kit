#!/usr/bin/env pwsh
# AI Team extension: fetch handoff requirement URL and build spec.override.md

param(
    [switch]$Json,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/HandoffSpecCommon.ps1"

$argsText = ($RemainingArgs -join ' ').Trim()
$repoRoot = Find-HandoffSpecProjectRoot -StartDir $PSScriptRoot
if (-not $repoRoot) { $repoRoot = (Get-Location).Path }
Set-Location $repoRoot

. (Join-Path $repoRoot '.specify/scripts/powershell/common.ps1')
$paths = Get-FeaturePathsEnv -NoPersist

$overrideName = Get-HandoffOverrideFileName -RepoRoot $repoRoot
$overrideFile = Join-Path $paths.FEATURE_DIR $overrideName
$specFile = $paths.FEATURE_SPEC
$effectiveSpec = Resolve-EffectiveSpecPath -FeatureDir $paths.FEATURE_DIR -OverrideName $overrideName

$url = Get-HandoffRequirementUrl -RepoRoot $repoRoot -ArgsText $argsText -Paths $paths
if (-not $url) {
    if ($Json) {
        Write-Output (Write-HandoffSpecJson -Skipped $true -FeatureDir $paths.FEATURE_DIR -FeatureSpec $specFile -EffectiveSpec $effectiveSpec)
    } else {
        Write-Output 'SKIPPED: no handoff_requirement_url found'
    }
    exit 0
}

$bootstrapped = $false
if (-not (Test-Path $specFile -PathType Leaf)) {
    Write-SpecPointer -SpecFile $specFile -Url $url
    $bootstrapped = $true
}

try {
    $fetched = Get-RemoteRequirementContent -Url $url
} catch {
    Write-Error "Failed to fetch handoff requirement URL: $url ($_)"
}

Write-MergedOverride -OverrideFile $overrideFile -Url $url -SpecFile $specFile -FetchedContent $fetched
Ensure-GitignorePattern -RepoRoot $repoRoot -Pattern "**/$overrideName"
$effectiveSpec = Resolve-EffectiveSpecPath -FeatureDir $paths.FEATURE_DIR -OverrideName $overrideName

if ($Json) {
    Write-Output (Write-HandoffSpecJson -Skipped $false -FeatureDir $paths.FEATURE_DIR -FeatureSpec $specFile -EffectiveSpec $effectiveSpec -HandoffUrl $url -SpecBootstrapped $bootstrapped)
} else {
    Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
    Write-Output "FEATURE_SPEC: $specFile"
    Write-Output "EFFECTIVE_SPEC: $effectiveSpec"
    Write-Output "HANDOFF_REQUIREMENT_URL: $url"
    Write-Output "SPEC_BOOTSTRAPPED: $bootstrapped"
}
