#!/usr/bin/env pwsh
# Setup project-level 4+1 architecture artifacts

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output "Usage: ./setup-arch.ps1 [-Json] [-Help]"
    Write-Output "  -Json     Output results in JSON format"
    Write-Output "  -Help     Show this help message"
    exit 0
}

function Find-SpecifyRoot {
    param([string]$StartDir = (Get-Location).Path)

    $resolved = Resolve-Path -LiteralPath $StartDir -ErrorAction SilentlyContinue
    $current = if ($resolved) { $resolved.Path } else { $null }
    if (-not $current) { return $null }

    while ($true) {
        if (Test-Path -LiteralPath (Join-Path $current ".specify") -PathType Container) {
            return $current
        }
        $parent = Split-Path $current -Parent
        if ([string]::IsNullOrEmpty($parent) -or $parent -eq $current) {
            return $null
        }
        $current = $parent
    }
}

function Get-RepoRoot {
    $specifyRoot = Find-SpecifyRoot
    if ($specifyRoot) {
        return $specifyRoot
    }

    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
    }

    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "../../../../..")).Path
}

function Resolve-ArchitectureTemplate {
    param(
        [Parameter(Mandatory = $true)][string]$TemplateName,
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )

    $override = Join-Path $RepoRoot ".specify/templates/overrides/$TemplateName.md"
    if (Test-Path -LiteralPath $override -PathType Leaf) {
        return $override
    }

    $candidate = Join-Path $RepoRoot ".specify/extensions/arch/templates/$TemplateName.md"
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        return $candidate
    }

    return $null
}

function Convert-ToPlainPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if ($Path -like 'Microsoft.PowerShell.Core\FileSystem::*') {
        return $Path.Substring('Microsoft.PowerShell.Core\FileSystem::'.Length)
    }
    return $Path
}

$repoRoot = Convert-ToPlainPath (Get-RepoRoot)
$archDir = Join-Path $repoRoot ".specify/memory"
$archFile = Join-Path $archDir "architecture.md"
$scenarioView = Join-Path $archDir "architecture-scenario-view.md"
$logicalView = Join-Path $archDir "architecture-logical-view.md"
$processView = Join-Path $archDir "architecture-process-view.md"
$developmentView = Join-Path $archDir "architecture-development-view.md"
$physicalView = Join-Path $archDir "architecture-physical-view.md"

New-Item -ItemType Directory -Path $archDir -Force | Out-Null

function Copy-TemplateIfMissing {
    param(
        [Parameter(Mandatory = $true)][string]$TemplateName,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        return
    }

    $template = Resolve-ArchitectureTemplate -TemplateName $TemplateName -RepoRoot $repoRoot
    if ($template -and (Test-Path -LiteralPath $template -PathType Leaf)) {
        Copy-Item -LiteralPath $template -Destination $Destination -Force
        Write-Output "Copied $TemplateName template to $Destination"
    } else {
        Write-Warning "$TemplateName template not found"
        New-Item -ItemType File -Path $Destination -Force | Out-Null
    }
}

Copy-TemplateIfMissing -TemplateName "architecture-template" -Destination $archFile
Copy-TemplateIfMissing -TemplateName "architecture-scenario-template" -Destination $scenarioView
Copy-TemplateIfMissing -TemplateName "architecture-logical-template" -Destination $logicalView
Copy-TemplateIfMissing -TemplateName "architecture-process-template" -Destination $processView
Copy-TemplateIfMissing -TemplateName "architecture-development-template" -Destination $developmentView
Copy-TemplateIfMissing -TemplateName "architecture-physical-template" -Destination $physicalView

if ($Json) {
    [PSCustomObject]@{
        ARCH_FILE = $archFile
        ARCH_DIR = $archDir
        SCENARIO_VIEW = $scenarioView
        LOGICAL_VIEW = $logicalView
        PROCESS_VIEW = $processView
        DEVELOPMENT_VIEW = $developmentView
        PHYSICAL_VIEW = $physicalView
    } | ConvertTo-Json -Compress
} else {
    Write-Output "ARCH_FILE: $archFile"
    Write-Output "ARCH_DIR: $archDir"
    Write-Output "SCENARIO_VIEW: $scenarioView"
    Write-Output "LOGICAL_VIEW: $logicalView"
    Write-Output "PROCESS_VIEW: $processView"
    Write-Output "DEVELOPMENT_VIEW: $developmentView"
    Write-Output "PHYSICAL_VIEW: $physicalView"
}
