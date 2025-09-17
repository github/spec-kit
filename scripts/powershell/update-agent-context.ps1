#!/usr/bin/env pwsh

# ==============================================================================
# Update Agent Context Script (PowerShell)
# ==============================================================================
#
# DESCRIPTION:
#   PowerShell equivalent of the bash update-agent-context.sh script.
#   Updates AI coding assistant context files with information from the current
#   feature's implementation plan. This script extracts technical details like
#   programming language, frameworks, database choices, and project structure
#   from plan.md and updates the appropriate agent configuration files to ensure
#   the AI assistant has current project context.
#
# USAGE:
#   .\update-agent-context.ps1 [AgentType]
#
# PARAMETERS:
#   AgentType     Specific agent to update (optional)
#                 Options: claude, gemini, copilot, cursor
#                 If omitted, updates all existing agent files or creates Claude by default
#
# SUPPORTED AGENTS:
#   - claude: Updates CLAUDE.md (Claude Code)
#   - gemini: Updates GEMINI.md (Gemini CLI)
#   - copilot: Updates .github/copilot-instructions.md (GitHub Copilot)
#   - cursor: Updates .cursor/rules/specify-rules.mdc (Cursor IDE)
#
# EXTRACTED INFORMATION:
#   From plan.md, the script extracts:
#   - **Language/Version**: Programming language and version
#   - **Primary Dependencies**: Main frameworks and libraries
#   - **Testing**: Testing frameworks and approaches
#   - **Storage**: Database and storage solutions
#   - **Project Type**: Application type (web, mobile, CLI, etc.)
#
# AGENT FILE UPDATES:
#   For existing files:
#   - Updates "Active Technologies" section with new tech stack
#   - Updates "Recent Changes" section with latest feature info
#   - Updates "Last updated" timestamp
#   - Uses regex-based text processing for reliable updates
#
#   For new files:
#   - Creates from agent-file-template.md if available
#   - Populates with project-specific information
#   - Sets up appropriate commands based on detected technology
#   - Configures project structure based on project type
#
# PREREQUISITES:
#   - Must be run from within a git repository
#   - plan.md must exist in current feature directory
#   - PowerShell 5.1+ or PowerShell Core 6+
#
# EXIT CODES:
#   0 - Agent context files updated successfully
#   1 - Missing plan.md file or invalid agent type
#
# EXAMPLES:
#   .\update-agent-context.ps1              # Update all agent files
#   .\update-agent-context.ps1 claude       # Update only Claude context
#   .\update-agent-context.ps1 copilot      # Update only GitHub Copilot context
#
# TEMPLATE DEPENDENCIES:
#   - agent-file-template.md: Base template for creating new agent files
#   - Must be located at .specify/templates/agent-file-template.md
#
# RELATED SCRIPTS:
#   - setup-plan.ps1: Creates the plan.md file that this script reads
#   - common.ps1: Could be used for shared functionality (currently not used)
#   - update-agent-context.sh: Bash equivalent of this script
#
# ==============================================================================

[CmdletBinding()]
param([string]$AgentType)
$ErrorActionPreference = 'Stop'

$repoRoot = git rev-parse --show-toplevel
$currentBranch = git rev-parse --abbrev-ref HEAD
$featureDir = Join-Path $repoRoot "specs/$currentBranch"
$newPlan = Join-Path $featureDir 'plan.md'
if (-not (Test-Path $newPlan)) { Write-Error "ERROR: No plan.md found at $newPlan"; exit 1 }

$claudeFile = Join-Path $repoRoot 'CLAUDE.md'
$geminiFile = Join-Path $repoRoot 'GEMINI.md'
$copilotFile = Join-Path $repoRoot '.github/copilot-instructions.md'
$cursorFile = Join-Path $repoRoot '.cursor/rules/specify-rules.mdc'

Write-Output "=== Updating agent context files for feature $currentBranch ==="

function Get-PlanValue($pattern) {
    if (-not (Test-Path $newPlan)) { return '' }
    $line = Select-String -Path $newPlan -Pattern $pattern | Select-Object -First 1
    if ($line) { return ($line.Line -replace "^\*\*$pattern\*\*: ", '') }
    return ''
}

$newLang = Get-PlanValue 'Language/Version'
$newFramework = Get-PlanValue 'Primary Dependencies'
$newTesting = Get-PlanValue 'Testing'
$newDb = Get-PlanValue 'Storage'
$newProjectType = Get-PlanValue 'Project Type'

function Initialize-AgentFile($targetFile, $agentName) {
    if (Test-Path $targetFile) { return }
    $template = Join-Path $repoRoot '.specify/templates/agent-file-template.md'
    if (-not (Test-Path $template)) { Write-Error "Template not found: $template"; return }
    $content = Get-Content $template -Raw
    $content = $content.Replace('[PROJECT NAME]', (Split-Path $repoRoot -Leaf))
    $content = $content.Replace('[DATE]', (Get-Date -Format 'yyyy-MM-dd'))
    $content = $content.Replace('[EXTRACTED FROM ALL PLAN.MD FILES]', "- $newLang + $newFramework ($currentBranch)")
    if ($newProjectType -match 'web') { $structure = "backend/`nfrontend/`ntests/" } else { $structure = "src/`ntests/" }
    $content = $content.Replace('[ACTUAL STRUCTURE FROM PLANS]', $structure)
    if ($newLang -match 'Python') { $commands = 'cd src && pytest && ruff check .' }
    elseif ($newLang -match 'Rust') { $commands = 'cargo test && cargo clippy' }
    elseif ($newLang -match 'JavaScript|TypeScript') { $commands = 'npm test && npm run lint' }
    else { $commands = "# Add commands for $newLang" }
    $content = $content.Replace('[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]', $commands)
    $content = $content.Replace('[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]', "${newLang}: Follow standard conventions")
    $content = $content.Replace('[LAST 3 FEATURES AND WHAT THEY ADDED]', "- ${currentBranch}: Added ${newLang} + ${newFramework}")
    $content | Set-Content $targetFile -Encoding UTF8
}

function Update-AgentFile($targetFile, $agentName) {
    if (-not (Test-Path $targetFile)) { Initialize-AgentFile $targetFile $agentName; return }
    $content = Get-Content $targetFile -Raw
    if ($newLang -and ($content -notmatch [regex]::Escape($newLang))) { $content = $content -replace '(## Active Technologies\n)', "`$1- $newLang + $newFramework ($currentBranch)`n" }
    if ($newDb -and $newDb -ne 'N/A' -and ($content -notmatch [regex]::Escape($newDb))) { $content = $content -replace '(## Active Technologies\n)', "`$1- $newDb ($currentBranch)`n" }
    if ($content -match '## Recent Changes\n([\s\S]*?)(\n\n|$)') {
        $changesBlock = $matches[1].Trim().Split("`n")
    $changesBlock = ,"- ${currentBranch}: Added ${newLang} + ${newFramework}" + $changesBlock
        $changesBlock = $changesBlock | Where-Object { $_ } | Select-Object -First 3
        $joined = ($changesBlock -join "`n")
        $content = [regex]::Replace($content, '## Recent Changes\n([\s\S]*?)(\n\n|$)', "## Recent Changes`n$joined`n`n")
    }
    $content = [regex]::Replace($content, 'Last updated: \d{4}-\d{2}-\d{2}', "Last updated: $(Get-Date -Format 'yyyy-MM-dd')")
    $content | Set-Content $targetFile -Encoding UTF8
    Write-Output "✅ $agentName context file updated successfully"
}

switch ($AgentType) {
    'claude' { Update-AgentFile $claudeFile 'Claude Code' }
    'gemini' { Update-AgentFile $geminiFile 'Gemini CLI' }
    'copilot' { Update-AgentFile $copilotFile 'GitHub Copilot' }
    'cursor' { Update-AgentFile $cursorFile 'Cursor IDE' }
    '' {
        foreach ($pair in @(
            @{file=$claudeFile; name='Claude Code'},
            @{file=$geminiFile; name='Gemini CLI'},
            @{file=$copilotFile; name='GitHub Copilot'},
            @{file=$cursorFile; name='Cursor IDE'}
        )) {
            if (Test-Path $pair.file) { Update-AgentFile $pair.file $pair.name }
        }
        if (-not (Test-Path $claudeFile) -and -not (Test-Path $geminiFile) -and -not (Test-Path $copilotFile) -and -not (Test-Path $cursorFile)) {
            Write-Output 'No agent context files found. Creating Claude Code context file by default.'
            Update-AgentFile $claudeFile 'Claude Code'
        }
    }
    Default { Write-Error "ERROR: Unknown agent type '$AgentType'. Use: claude, gemini, copilot, cursor or leave empty for all."; exit 1 }
}

Write-Output ''
Write-Output 'Summary of changes:'
if ($newLang) { Write-Output "- Added language: $newLang" }
if ($newFramework) { Write-Output "- Added framework: $newFramework" }
if ($newDb -and $newDb -ne 'N/A') { Write-Output "- Added database: $newDb" }

Write-Output ''
Write-Output 'Usage: ./update-agent-context.ps1 [claude|gemini|copilot|cursor]'
