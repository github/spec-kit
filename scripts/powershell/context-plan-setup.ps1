#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output @"
Usage: context-plan-setup.ps1 [-Json]

Ensure the workflow-specific plan file exists and report key artifact paths.
"@
    exit 0
}

. "$PSScriptRoot/common.ps1"

$paths = Get-FeaturePaths
[System.IO.Directory]::CreateDirectory($paths.FEATURE_DIR) | Out-Null

if (-not (Test-Path $paths.PLAN_FILE -PathType Leaf)) {
    [System.IO.Directory]::CreateDirectory((Split-Path $paths.PLAN_FILE)) | Out-Null
    switch ($paths.WORKFLOW) {
        'free-style' {
            @"
# Implementation Plan (Free-Style Workflow)

## Summary

## Workstreams
- Frontend:
- Backend:
- Data & Storage:
- QA & Tooling:

## Sequencing

## Risks & Mitigations

## Validation Strategy

"@ | Set-Content -Encoding UTF8 $paths.PLAN_FILE
        }
        'prp' {
            @"
# Execution Plan (PRP Workflow)

## PRP Alignment
- Reference PRP file:

## Objectives & Deliverables

## Task Breakdown

## Risks & Dependencies

## Validation Strategy

"@ | Set-Content -Encoding UTF8 $paths.PLAN_FILE
        }
        'all-in-one' {
            @"
# Plan Notes (All-in-One Workflow)

Use this file to track any plan details that need to live outside the main all-in-one record.

## Focus Areas

## Risks & Blockers

## Follow-ups

"@ | Set-Content -Encoding UTF8 $paths.PLAN_FILE
        }
        default {
            @"
# Implementation Plan

"@ | Set-Content -Encoding UTF8 $paths.PLAN_FILE
        }
    }

    if ($paths.CHECKLIST_TEMPLATE -and (Test-Path $paths.CHECKLIST_TEMPLATE)) {
        Add-Content -Encoding UTF8 -Path $paths.PLAN_FILE -Value "## Full Implementation Checklist"
        Get-Content -Path $paths.CHECKLIST_TEMPLATE | Add-Content -Encoding UTF8 -Path $paths.PLAN_FILE
    }
}

if ($Json) {
    [PSCustomObject]@{
        WORKFLOW = $paths.WORKFLOW
        PLAN_FILE = $paths.PLAN_FILE
        PRIMARY_FILE = $paths.PRIMARY_FILE
        RESEARCH_FILE = $paths.RESEARCH_FILE
        TASKS_FILE = $paths.TASKS_FILE
        CHECKLIST_TEMPLATE = $paths.CHECKLIST_TEMPLATE
    } | ConvertTo-Json -Compress
} else {
    Write-Output "WORKFLOW: $($paths.WORKFLOW)"
    Write-Output "PLAN_FILE: $($paths.PLAN_FILE)"
    Write-Output "PRIMARY_FILE: $($paths.PRIMARY_FILE)"
    Write-Output "RESEARCH_FILE: $($paths.RESEARCH_FILE)"
    Write-Output "TASKS_FILE: $($paths.TASKS_FILE)"
    Write-Output "CHECKLIST_TEMPLATE: $($paths.CHECKLIST_TEMPLATE)"
}
