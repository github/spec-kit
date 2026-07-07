#!/usr/bin/env pwsh
# AI Team extension: resolve effective spec path

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

if (-not (Test-Path $overrideFile -PathType Leaf)) {
    if ($specFile -and (Test-Path $specFile)) {
        $head = (Get-Content -LiteralPath $specFile -TotalCount 40) -join "`n"
        if (Get-HandoffUrlFromText -Text $head) {
            throw 'spec.override.md missing but handoff URL present in spec.md. Re-run speckit.plan or speckit.ai-team.handoff-spec-sync.'
        }
    }
    $configuredUrl = Get-HandoffRequirementUrl -RepoRoot $repoRoot -ArgsText $argsText -Paths $paths
    if ($configuredUrl) {
        throw 'handoff URL configured but spec.override.md missing. Re-run speckit.ai-team.handoff-spec-sync.'
    }
}

if ($Json) {
    Write-Output (Write-HandoffSpecJson -Skipped $false -FeatureDir $paths.FEATURE_DIR -FeatureSpec $specFile -EffectiveSpec $effectiveSpec)
} else {
    Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
    Write-Output "FEATURE_SPEC: $specFile"
    Write-Output "EFFECTIVE_SPEC: $effectiveSpec"
}
