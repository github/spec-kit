#!/usr/bin/env pwsh
<#!
.SYNOPSIS
Update agent context files with information from plan.md (PowerShell version)

.DESCRIPTION
Mirrors the behavior of scripts/bash/update-agent-context.sh:
 1. Environment Validation
 2. Plan Data Extraction
 3. Agent File Management (create from template or update existing)
 4. Content Generation (technology stack, recent changes, timestamp)
 5. Multi-Agent Support (claude, gemini, copilot, cursor, qwen, opencode, codex, windsurf)

.PARAMETER AgentType
Optional agent key to update a single agent. If omitted, updates all existing agent files (creating a default Claude file if none exist).

.EXAMPLE
./update-agent-context.ps1 -AgentType claude

.EXAMPLE
./update-agent-context.ps1   # Updates all existing agent files

.NOTES
Relies on common helper functions in common.ps1
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet('claude', 'gemini', 'copilot', 'cursor', 'qwen', 'opencode', 'codex', 'windsurf', 'kilocode', 'auggie', 'roo')]
    [string]$AgentType
)

$ErrorActionPreference = 'Stop'

# Import common helpers
. "$PSScriptRoot/common.ps1"

# Acquire environment paths
$envData = Get-FeaturePathsEnv
$REPO_ROOT = $envData.REPO_ROOT
$CURRENT_BRANCH = $envData.CURRENT_BRANCH
$HAS_GIT = $envData.HAS_GIT
$IMPL_PLAN = $envData.IMPL_PLAN
$NEW_PLAN = $IMPL_PLAN

# Agent file paths
$CLAUDE_FILE = Join-Path $REPO_ROOT 'CLAUDE.md'
$GEMINI_FILE = Join-Path $REPO_ROOT 'GEMINI.md'
$COPILOT_FILE = Join-Path $REPO_ROOT '.github/copilot-instructions.md'
$CURSOR_FILE = Join-Path $REPO_ROOT '.cursor/rules/specify-rules.mdc'
$QWEN_FILE = Join-Path $REPO_ROOT 'QWEN.md'
$AGENTS_FILE = Join-Path $REPO_ROOT 'AGENTS.md'
$WINDSURF_FILE = Join-Path $REPO_ROOT '.windsurf/rules/specify-rules.md'
$KILOCODE_FILE = Join-Path $REPO_ROOT '.kilocode/rules/specify-rules.md'
$AUGGIE_FILE = Join-Path $REPO_ROOT '.augment/rules/specify-rules.md'
$ROO_FILE = Join-Path $REPO_ROOT '.roo/rules/specify-rules.md'

$TEMPLATE_FILE = Join-Path $REPO_ROOT '.specify/templates/agent-file-template.md'

# Parsed plan data placeholders
$script:NEW_LANG = ''
$script:NEW_FRAMEWORK = ''
$script:NEW_DB = ''
$script:NEW_PROJECT_TYPE = ''

Validate-Environment
Write-Info "=== Updating agent context files for feature $CURRENT_BRANCH ==="
if (-not (Parse-PlanData -PlanFile $NEW_PLAN)) { Write-Err 'Failed to parse plan data'; exit 1 }
$success = $true
if ($AgentType) {
    Write-Info "Updating specific agent: $AgentType"
    if (-not (Update-SpecificAgent -Type $AgentType)) { $success = $false }
} else {
    Write-Info 'No agent specified, updating all existing agent files...'
    if (-not (Update-AllExistingAgents)) { $success = $false }
}
Show-Summary
if ($success) { Write-Success 'Agent context update completed successfully'; exit 0 } else { Write-Err 'Agent context update completed with errors'; exit 1 }
