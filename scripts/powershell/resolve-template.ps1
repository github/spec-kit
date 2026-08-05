#!/usr/bin/env pwsh

param(
    [Parameter(Position=0)]
    [string]$TemplateName,
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output "Usage: resolve-template.ps1 <template-name> [-Json]"
    exit 0
}

if (-not $TemplateName) {
    [Console]::Error.WriteLine("ERROR: Template name is required")
    exit 1
}

. "$PSScriptRoot/common.ps1"

$repoRoot = Get-RepoRoot
$templateContent = Resolve-TemplateContent -TemplateName $TemplateName -RepoRoot $repoRoot
if ($null -eq $templateContent) {
    [Console]::Error.WriteLine("ERROR: Could not resolve required $TemplateName from the template override stack for $repoRoot")
    exit 1
}

if ($Json) {
    [PSCustomObject]@{
        TEMPLATE_NAME = $TemplateName
        TEMPLATE_CONTENT = $templateContent
    } | ConvertTo-Json -Compress
} else {
    [Console]::Out.Write($templateContent)
}
