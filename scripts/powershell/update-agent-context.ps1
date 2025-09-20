#!/usr/bin/env pwsh
[CmdletBinding()]
param([string]$AgentType)
$ErrorActionPreference = 'Stop'

# Load common functions
. "$PSScriptRoot/common.ps1"

# Get all paths and variables from common functions
$paths = Get-FeaturePathsEnv

$newPlan = $paths.IMPL_PLAN
if (-not (Test-Path $newPlan)) { 
    Write-Error "ERROR: No plan.md found at $newPlan"
    if (-not $paths.HAS_GIT) {
        Write-Output "Use: `$env:SPECIFY_FEATURE='your-feature-name' or create a new feature first"
    }
    exit 1 
}

$claudeFile = Join-Path $paths.REPO_ROOT 'CLAUDE.md'
$geminiFile = Join-Path $paths.REPO_ROOT 'GEMINI.md'
$copilotFile = Join-Path $paths.REPO_ROOT '.github/copilot-instructions.md'
$cursorFile = Join-Path $paths.REPO_ROOT '.cursor/rules/specify-rules.mdc'
$qwenFile = Join-Path $paths.REPO_ROOT 'QWEN.md'
$agentsFile = Join-Path $paths.REPO_ROOT 'AGENTS.md'
$windsurfFile = Join-Path $paths.REPO_ROOT '.windsurf/rules/specify-rules.md'

Write-Output "=== Updating agent context files for feature $($paths.CURRENT_BRANCH) ==="

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

function Format-TechnologyStack($lang, $framework) {
    $parts = @()
    
    # Add non-empty parts (excluding "NEEDS CLARIFICATION" and "N/A")
    if ($lang -and $lang -ne 'NEEDS CLARIFICATION') { $parts += $lang }
    if ($framework -and $framework -ne 'NEEDS CLARIFICATION' -and $framework -ne 'N/A') { $parts += $framework }
    
    # Join with proper formatting
    if ($parts.Count -eq 0) {
        return ''
    } elseif ($parts.Count -eq 1) {
        return $parts[0]
    } else {
        return ($parts -join ' + ')
    }
}

function Initialize-AgentFile($targetFile, $agentName) {
    if (Test-Path $targetFile) { return }
    $template = Join-Path $paths.REPO_ROOT '.specify/templates/agent-file-template.md'
    if (-not (Test-Path $template)) { Write-Error "Template not found: $template"; return }
    $content = Get-Content $template -Raw
    $content = $content.Replace('[PROJECT NAME]', (Split-Path $paths.REPO_ROOT -Leaf))
    $content = $content.Replace('[DATE]', (Get-Date -Format 'yyyy-MM-dd'))
    
    $techStack = Format-TechnologyStack $newLang $newFramework
    if ($techStack) {
        $content = $content.Replace('[EXTRACTED FROM ALL PLAN.MD FILES]', "- $techStack ($($paths.CURRENT_BRANCH))")
    } else {
        $content = $content.Replace('[EXTRACTED FROM ALL PLAN.MD FILES]', '')
    }
    if ($newProjectType -match 'web') { $structure = "backend/`nfrontend/`ntests/" } else { $structure = "src/`ntests/" }
    $content = $content.Replace('[ACTUAL STRUCTURE FROM PLANS]', $structure)
    if ($newLang -match 'Python') { $commands = 'cd src && pytest && ruff check .' }
    elseif ($newLang -match 'Rust') { $commands = 'cargo test && cargo clippy' }
    elseif ($newLang -match 'JavaScript|TypeScript') { $commands = 'npm test && npm run lint' }
    else { $commands = "# Add commands for $newLang" }
    $content = $content.Replace('[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]', $commands)
    $content = $content.Replace('[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]', "${newLang}: Follow standard conventions")
    
    $techStack = Format-TechnologyStack $newLang $newFramework
    if ($techStack) {
        $content = $content.Replace('[LAST 3 FEATURES AND WHAT THEY ADDED]', "- $($paths.CURRENT_BRANCH): Added $techStack")
    } else {
        $content = $content.Replace('[LAST 3 FEATURES AND WHAT THEY ADDED]', '')
    }
    $content | Set-Content $targetFile -Encoding UTF8
}

function Update-AgentFile($targetFile, $agentName) {
    if (-not (Test-Path $targetFile)) { Initialize-AgentFile $targetFile $agentName; return }
    $content = Get-Content $targetFile -Raw
    
    $techStack = Format-TechnologyStack $newLang $newFramework
    if ($techStack -and ($content -notmatch [regex]::Escape($techStack))) { 
        $content = $content -replace '(## Active Technologies\n)', "`$1- $techStack ($($paths.CURRENT_BRANCH))`n" 
    }
    
    if ($newDb -and $newDb -ne 'N/A' -and $newDb -ne 'NEEDS CLARIFICATION' -and ($content -notmatch [regex]::Escape($newDb))) { 
        $content = $content -replace '(## Active Technologies\n)', "`$1- $newDb ($($paths.CURRENT_BRANCH))`n" 
    }
    
    if ($content -match '## Recent Changes\n([\s\S]*?)(\n\n|$)') {
        $changesBlock = $matches[1].Trim().Split("`n")
        
        if ($techStack) {
            $changesBlock = ,"- $($paths.CURRENT_BRANCH): Added $techStack" + $changesBlock
        } elseif ($newDb -and $newDb -ne 'N/A' -and $newDb -ne 'NEEDS CLARIFICATION') {
            $changesBlock = ,"- $($paths.CURRENT_BRANCH): Added $newDb" + $changesBlock
        }
        
        $changesBlock = $changesBlock | Where-Object { $_ } | Select-Object -First 3
        $joined = ($changesBlock -join "`n")
        $content = [regex]::Replace($content, '## Recent Changes\n([\s\S]*?)(\n\n|$)', "## Recent Changes`n$joined`n`n")
    }
    $content = [regex]::Replace($content, 'Last updated: \d{4}-\d{2}-\d{2}', "Last updated: $(Get-Date -Format 'yyyy-MM-dd')")
    $content | Set-Content $targetFile -Encoding UTF8
    Write-Output "✓ $agentName context file updated successfully"
}

switch ($AgentType) {
    'claude' { Update-AgentFile $claudeFile 'Claude Code' }
    'gemini' { Update-AgentFile $geminiFile 'Gemini CLI' }
    'copilot' { Update-AgentFile $copilotFile 'GitHub Copilot' }
    'cursor' { Update-AgentFile $cursorFile 'Cursor IDE' }
    'qwen' { Update-AgentFile $qwenFile 'Qwen Code' }
    'opencode' { Update-AgentFile $agentsFile 'opencode' }
    'windsurf' { Update-AgentFile $windsurfFile 'Windsurf' }
    'codex'    { Update-AgentFile $agentsFile 'Codex CLI' }
    '' {
        foreach ($pair in @(
            @{file=$claudeFile; name='Claude Code'},
            @{file=$geminiFile; name='Gemini CLI'},
            @{file=$copilotFile; name='GitHub Copilot'},
            @{file=$cursorFile; name='Cursor IDE'},
            @{file=$qwenFile; name='Qwen Code'},
            @{file=$agentsFile; name='opencode'},
            @{file=$windsurfFile; name='Windsurf'},
            @{file=$agentsFile; name='Codex CLI'}
        )) {
            if (Test-Path $pair.file) { Update-AgentFile $pair.file $pair.name }
        }
        if (-not (Test-Path $claudeFile) -and -not (Test-Path $geminiFile) -and -not (Test-Path $copilotFile) -and -not (Test-Path $cursorFile) -and -not (Test-Path $qwenFile) -and -not (Test-Path $agentsFile) -and -not (Test-Path $windsurfFile)) {
            Write-Output 'No agent context files found. Creating Claude Code context file by default.'
            Update-AgentFile $claudeFile 'Claude Code'
        }
    }
    Default { Write-Error "ERROR: Unknown agent type '$AgentType'. Use: claude, gemini, copilot, cursor, qwen, opencode, windsurf, codex or leave empty for all."; exit 1 }
}

Write-Output ''
Write-Output 'Summary of changes:'
if ($newLang) { Write-Output "- Added language: $newLang" }
if ($newFramework) { Write-Output "- Added framework: $newFramework" }
if ($newDb -and $newDb -ne 'N/A') { Write-Output "- Added database: $newDb" }

Write-Output ''
Write-Output 'Usage: ./update-agent-context.ps1 [claude|gemini|copilot|cursor|qwen|opencode|windsurf|codex]'
