#!/usr/bin/env pwsh
# Create a new Context Engineering Kit feature
[CmdletBinding()]
param(
    [switch]$Json,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$FeatureDescription
)
$ErrorActionPreference = 'Stop'

if (-not $FeatureDescription -or $FeatureDescription.Count -eq 0) {
    Write-Error "Usage: ./create-new-feature.ps1 [-Json] <feature description>"
    exit 1
}
$featureDesc = ($FeatureDescription -join ' ').Trim()

. (Join-Path $PSScriptRoot 'common.ps1')

$repoRoot = Get-RepoRoot
$workflow = Get-Workflow -RepoRoot $repoRoot
$hasGit = Test-HasGit
Set-Location $repoRoot

$highest = 0
if ($hasGit) {
    git for-each-ref --format='%(refname:short)' refs/heads | ForEach-Object {
        if ($_ -match '^(\d{3})-') {
            $num = [int]$matches[1]
            if ($num -gt $highest) { $highest = $num }
        }
    }
}

if ($highest -eq 0) {
    $candidateDirs = @(
        Join-Path $repoRoot 'specs',
        Join-Path $repoRoot 'context-eng/prp',
        Join-Path $repoRoot 'context-eng/all-in-one'
    )
    foreach ($dir in $candidateDirs) {
        if (-not (Test-Path $dir)) { continue }
        Get-ChildItem -Path $dir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{3})-') {
                $num = [int]$matches[1]
                if ($num -gt $highest) { $highest = $num }
            }
        }
    }
}

$next = $highest + 1
$featureNum = ('{0:000}' -f $next)

$slug = $featureDesc.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
$words = ($slug -split '-') | Where-Object { $_ } | Select-Object -First 3
if (-not $words) { $words = @('feature') }
$branchName = "$featureNum-$([string]::Join('-', $words))"

if ($hasGit) {
    try {
        git checkout -b $branchName | Out-Null
    } catch {
        Write-Warning "Failed to create git branch: $branchName"
    }
} else {
    Write-Warning "[cek] Warning: Git repository not detected; skipped branch creation for $branchName"
}

$contextDir = Join-Path $repoRoot '.context-eng'
$checklistTemplate = Join-Path $contextDir 'checklists/full-implementation-checklist.md'

$featureDir = $null
$primaryTemplate = $null
$primaryFile = $null
$planFile = $null
$researchFile = $null
$tasksFile = $null
$prpFile = $null
$initialFile = $null

switch ($workflow) {
    'free-style' {
        $featureDir = Join-Path $repoRoot "specs/$branchName"
        $primaryTemplate = Join-Path $contextDir 'workflows/free-style/templates/context-spec-template.md'
        $primaryFile = Join-Path $featureDir 'context-spec.md'
        $planFile = Join-Path $featureDir 'plan.md'
        $researchFile = Join-Path $featureDir 'research.md'
        $tasksFile = Join-Path $featureDir 'tasks.md'
    }
    'prp' {
        $featureDir = Join-Path $repoRoot "context-eng/prp/$branchName"
        $primaryTemplate = Join-Path $contextDir 'workflows/prp/templates/initial-template.md'
        $primaryFile = Join-Path $repoRoot 'PRPs/INITIAL.md'
        $prpFile = Join-Path $repoRoot "PRPs/$branchName.md"
        $planFile = Join-Path $featureDir 'plan.md'
        $researchFile = Join-Path $featureDir 'research.md'
        $tasksFile = Join-Path $featureDir 'tasks.md'
        $initialFile = $primaryFile
    }
    'all-in-one' {
        $featureDir = Join-Path $repoRoot "context-eng/all-in-one/$branchName"
        $primaryTemplate = Join-Path $contextDir 'workflows/all-in-one/templates/all-in-one-template.md'
        $primaryFile = Join-Path $featureDir 'record.md'
        $planFile = Join-Path $featureDir 'plan.md'
        $researchFile = Join-Path $featureDir 'research.md'
        $tasksFile = Join-Path $featureDir 'tasks.md'
    }
    default {
        $featureDir = Join-Path $repoRoot "specs/$branchName"
        $primaryTemplate = Join-Path $contextDir 'workflows/free-style/templates/context-spec-template.md'
        $primaryFile = Join-Path $featureDir 'context-spec.md'
        $planFile = Join-Path $featureDir 'plan.md'
        $researchFile = Join-Path $featureDir 'research.md'
        $tasksFile = Join-Path $featureDir 'tasks.md'
    }
}

New-Item -ItemType Directory -Path $featureDir -Force | Out-Null
[System.IO.Directory]::CreateDirectory((Split-Path $primaryFile)) | Out-Null
[System.IO.Directory]::CreateDirectory((Split-Path $planFile)) | Out-Null
[System.IO.Directory]::CreateDirectory((Split-Path $researchFile)) | Out-Null
[System.IO.Directory]::CreateDirectory((Split-Path $tasksFile)) | Out-Null

if ($workflow -eq 'prp') {
    [System.IO.Directory]::CreateDirectory((Split-Path $prpFile)) | Out-Null
    $prpTemplate = Join-Path $contextDir 'workflows/prp/templates/prp-template.md'
    if ((-not (Test-Path $prpFile)) -and (Test-Path $prpTemplate)) {
        Copy-Item $prpTemplate $prpFile
    }
}

if ((Test-Path $primaryTemplate) -and (-not (Test-Path $primaryFile))) {
    Copy-Item $primaryTemplate $primaryFile
} elseif (-not (Test-Path $primaryFile)) {
    New-Item -ItemType File -Path $primaryFile | Out-Null
}

$env:CONTEXT_FEATURE = $branchName
$env:SPECIFY_FEATURE = $branchName

$output = [ordered]@{
    BRANCH_NAME = $branchName
    FEATURE_NUM = $featureNum
    WORKFLOW = $workflow
    PRIMARY_FILE = $primaryFile
    TEMPLATE_FILE = $primaryTemplate
    FEATURE_DIR = $featureDir
    PLAN_FILE = $planFile
    RESEARCH_FILE = $researchFile
    TASKS_FILE = $tasksFile
    PRP_FILE = $prpFile
    INITIAL_FILE = $initialFile
    CHECKLIST_TEMPLATE = $checklistTemplate
}

if ($Json) {
    [PSCustomObject]$output | ConvertTo-Json -Compress
} else {
    $output.GetEnumerator() | ForEach-Object {
        if ($_.Value) { Write-Output "$($_.Key): $($_.Value)" }
    }
    Write-Output "CONTEXT_FEATURE environment variable set to: $branchName"
}
