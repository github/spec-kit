#!/usr/bin/env pwsh
# Common helpers for the Context Engineering Kit scripts

function Get-RepoRoot {
    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # ignore
    }
    return (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
}

function Get-Workflow {
    param([string]$RepoRoot)
    $configPath = Join-Path $RepoRoot '.context-eng/workflow.json'
    if (Test-Path $configPath) {
        try {
            $json = Get-Content $configPath -Raw | ConvertFrom-Json
            if ($json.workflow) { return $json.workflow }
        } catch {
            # fall through to default
        }
    }
    return 'free-style'
}

function Get-CurrentFeature {
    if ($env:CONTEXT_FEATURE) {
        return $env:CONTEXT_FEATURE
    }
    try {
        $branch = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0 -and $branch -and $branch -ne 'HEAD') {
            return $branch
        }
    } catch {
        # ignore
    }

    $repoRoot = Get-RepoRoot
    $searchDirs = @(
        (Join-Path $repoRoot 'specs'),
        (Join-Path $repoRoot 'context-eng/prp'),
        (Join-Path $repoRoot 'context-eng/all-in-one')
    )
    $candidate = $null
    $highest = -1
    foreach ($dir in $searchDirs) {
        if (-not (Test-Path $dir)) { continue }
        Get-ChildItem -Path $dir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{3})-') {
                $num = [int]$Matches[1]
                if ($num -gt $highest) {
                    $highest = $num
                    $candidate = $_.Name
                }
            }
        }
    }
    if ($candidate) { return $candidate }
    return '000-unspecified'
}

function Test-HasGit {
    try {
        git rev-parse --show-toplevel 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Test-FeatureBranch {
    param(
        [string]$Branch,
        [bool]$HasGit = $true
    )
    if (-not $HasGit) {
        Write-Warning "[cek] Warning: Git repository not detected; skipped branch validation"
        return $true
    }
    if ($Branch -notmatch '^[0-9]{3}-') {
        Write-Output "ERROR: Not on a context feature branch. Current branch: $Branch"
        Write-Output "Use branches like 001-feature-name."
        return $false
    }
    return $true
}

function Get-FeaturePaths {
    $repoRoot = Get-RepoRoot
    $workflow = Get-Workflow -RepoRoot $repoRoot
    $featureName = Get-CurrentFeature
    $hasGit = Test-HasGit
    $contextDir = Join-Path $repoRoot '.context-eng'
    $checklistTemplate = Join-Path $contextDir 'checklists/full-implementation-checklist.md'

    $result = [ordered]@{
        REPO_ROOT = $repoRoot
        WORKFLOW = $workflow
        FEATURE_NAME = $featureName
        HAS_GIT = $hasGit
        FEATURE_DIR = $null
        PRIMARY_FILE = $null
        PLAN_FILE = $null
        RESEARCH_FILE = $null
        TASKS_FILE = $null
        PRP_FILE = $null
        INITIAL_FILE = $null
        CHECKLIST_TEMPLATE = $checklistTemplate
        CURRENT_BRANCH = $featureName
        FEATURE_SPEC = $primary_file
        IMPL_PLAN = $plan_file
        TASKS = $tasks_file
        RESEARCH = $research_file
    }

    switch ($workflow) {
        'free-style' {
            $featureDir = Join-Path $repoRoot "specs/$featureName"
            $result['FEATURE_DIR'] = $featureDir
            $result['PRIMARY_FILE'] = Join-Path $featureDir 'context-spec.md'
            $result['PLAN_FILE'] = Join-Path $featureDir 'plan.md'
            $result['RESEARCH_FILE'] = Join-Path $featureDir 'research.md'
            $result['TASKS_FILE'] = Join-Path $featureDir 'tasks.md'
        }
        'prp' {
            $featureDir = Join-Path $repoRoot "context-eng/prp/$featureName"
            $result['FEATURE_DIR'] = $featureDir
            $result['PRIMARY_FILE'] = Join-Path $repoRoot 'PRPs/INITIAL.md'
            $result['INITIAL_FILE'] = $result['PRIMARY_FILE']
            $result['PRP_FILE'] = Join-Path $repoRoot "PRPs/$featureName.md"
            $result['PLAN_FILE'] = Join-Path $featureDir 'plan.md'
            $result['RESEARCH_FILE'] = Join-Path $featureDir 'research.md'
            $result['TASKS_FILE'] = Join-Path $featureDir 'tasks.md'
        }
        'all-in-one' {
            $featureDir = Join-Path $repoRoot "context-eng/all-in-one/$featureName"
            $result['FEATURE_DIR'] = $featureDir
            $result['PRIMARY_FILE'] = Join-Path $featureDir 'record.md'
            $result['PLAN_FILE'] = Join-Path $featureDir 'plan.md'
            $result['RESEARCH_FILE'] = Join-Path $featureDir 'research.md'
            $result['TASKS_FILE'] = Join-Path $featureDir 'tasks.md'
        }
        default {
            $featureDir = Join-Path $repoRoot "specs/$featureName"
            $result['FEATURE_DIR'] = $featureDir
            $result['PRIMARY_FILE'] = Join-Path $featureDir 'context-spec.md'
            $result['PLAN_FILE'] = Join-Path $featureDir 'plan.md'
            $result['RESEARCH_FILE'] = Join-Path $featureDir 'research.md'
            $result['TASKS_FILE'] = Join-Path $featureDir 'tasks.md'
        }
    }

    return [PSCustomObject]$result
}

function Test-FileExists {
    param([string]$Path, [string]$Description)
    if (Test-Path -Path $Path -PathType Leaf) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}

function Test-DirHasFiles {
    param([string]$Path, [string]$Description)
    if ((Test-Path -Path $Path -PathType Container) -and (Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer } | Select-Object -First 1)) {
        Write-Output "  ✓ $Description"
        return $true
    } else {
        Write-Output "  ✗ $Description"
        return $false
    }
}
