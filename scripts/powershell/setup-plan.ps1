#!/usr/bin/env pwsh
[CmdletBinding(DefaultParameterSetName="Default")]
param(
    [switch]$Json,
    [switch]$Help
)

if ($Help) {
    & "$PSScriptRoot/context-plan-setup.ps1" -Help
    exit 0
}

if ($Json) {
    & "$PSScriptRoot/context-plan-setup.ps1" -Json
} else {
    & "$PSScriptRoot/context-plan-setup.ps1"
}
    $result | ConvertTo-Json -Compress
} else {
    Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
    Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
    Write-Output "SPECS_DIR: $($paths.FEATURE_DIR)"
    Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
    Write-Output "HAS_GIT: $($paths.HAS_GIT)"
}
