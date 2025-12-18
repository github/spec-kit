#!/usr/bin/env pwsh
#requires -Version 7.0

<#
.SYNOPSIS
    Build SpecLite template release archives for each supported AI assistant and script type.

.DESCRIPTION
    create-release-packages.ps1 (workflow-local)
    Build SpecLite template release archives for each supported AI assistant and script type.

.PARAMETER Version
    Version string with leading 'v' (e.g., v0.2.0)

.PARAMETER Agents
    Comma or space separated subset of agents to build (default: all)
    Valid agents: claude, gemini, copilot, cursor-agent, codex

.PARAMETER Scripts
    Comma or space separated subset of script types to build (default: both)
    Valid scripts: sh, ps

.EXAMPLE
    .\create-release-packages.ps1 -Version v0.2.0

.EXAMPLE
    .\create-release-packages.ps1 -Version v0.2.0 -Agents claude,copilot -Scripts sh

.EXAMPLE
    .\create-release-packages.ps1 -Version v0.2.0 -Agents claude -Scripts ps
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$Agents = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Scripts = ""
)

$ErrorActionPreference = "Stop"

# Validate version format
if ($Version -notmatch '^v\d+\.\d+\.\d+$') {
    Write-Error "Version must look like v0.0.0"
    exit 1
}

Write-Host "Building release packages for $Version"

# Create and use .genreleases directory for all build artifacts
$GenReleasesDir = ".genreleases"
if (Test-Path $GenReleasesDir) {
    Remove-Item -Path $GenReleasesDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $GenReleasesDir -Force | Out-Null

function Rewrite-Paths {
    param([string]$Content)

    $Content = $Content -replace '(/?)\bmemory/', '.speclite/memory/'
    $Content = $Content -replace '(/?)\bscripts/', '.speclite/scripts/'
    $Content = $Content -replace '(/?)\btemplates/', '.speclite/templates/'
    return $Content
}

function Generate-Commands {
    param(
        [string]$Agent,
        [string]$Extension,
        [string]$ArgFormat,
        [string]$OutputDir,
        [string]$ScriptVariant
    )
    
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    
    $templates = Get-ChildItem -Path "templates/commands/*.md" -File -ErrorAction SilentlyContinue
    
    foreach ($template in $templates) {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($template.Name)
        
        # Read file content and normalize line endings
        $fileContent = (Get-Content -Path $template.FullName -Raw) -replace "`r`n", "`n"
        
        # Extract description from YAML frontmatter
        $description = ""
        if ($fileContent -match '(?m)^description:\s*(.+)$') {
            $description = $matches[1]
        }
        
        # Extract script command from YAML frontmatter
        $scriptCommand = ""
        if ($fileContent -match "(?m)^\s*${ScriptVariant}:\s*(.+)$") {
            $scriptCommand = $matches[1]
        }
        
        if ([string]::IsNullOrEmpty($scriptCommand)) {
            Write-Warning "No script command found for $ScriptVariant in $($template.Name)"
            $scriptCommand = "(Missing script command for $ScriptVariant)"
        }
        
        # Extract agent_script command from YAML frontmatter if present
        $agentScriptCommand = ""
        if ($fileContent -match "(?ms)agent_scripts:.*?^\s*${ScriptVariant}:\s*(.+?)$") {
            $agentScriptCommand = $matches[1].Trim()
        }
        
        # Replace {SCRIPT} placeholder with the script command
        $body = $fileContent -replace '\{SCRIPT\}', $scriptCommand
        
        # Replace {AGENT_SCRIPT} placeholder with the agent script command if found
        if (-not [string]::IsNullOrEmpty($agentScriptCommand)) {
            $body = $body -replace '\{AGENT_SCRIPT\}', $agentScriptCommand
        }
        
        # Remove the scripts: and agent_scripts: sections from frontmatter
        $lines = $body -split "`n"
        $outputLines = @()
        $inFrontmatter = $false
        $skipScripts = $false
        $dashCount = 0
        
        foreach ($line in $lines) {
            if ($line -match '^---$') {
                $outputLines += $line
                $dashCount++
                if ($dashCount -eq 1) {
                    $inFrontmatter = $true
                } else {
                    $inFrontmatter = $false
                }
                continue
            }
            
            if ($inFrontmatter) {
                if ($line -match '^(scripts|agent_scripts):$') {
                    $skipScripts = $true
                    continue
                }
                if ($line -match '^[a-zA-Z].*:' -and $skipScripts) {
                    $skipScripts = $false
                }
                if ($skipScripts -and $line -match '^\s+') {
                    continue
                }
            }
            
            $outputLines += $line
        }
        
        $body = $outputLines -join "`n"
        
        # Apply other substitutions
        $body = $body -replace '\{ARGS\}', $ArgFormat
        $body = $body -replace '__AGENT__', $Agent
        $body = Rewrite-Paths -Content $body
        
        # Generate output file based on extension
        $outputFile = Join-Path $OutputDir "sl.$name.$Extension"
        
        switch ($Extension) {
            'toml' {
                $body = $body -replace '\\', '\\'
                $output = "description = `"$description`"`n`nprompt = `"`"`"`n$body`n`"`"`""
                Set-Content -Path $outputFile -Value $output -NoNewline
            }
            'md' {
                Set-Content -Path $outputFile -Value $body -NoNewline
            }
            'agent.md' {
                Set-Content -Path $outputFile -Value $body -NoNewline
            }
        }
    }
}

function Generate-CopilotPrompts {
    param(
        [string]$AgentsDir,
        [string]$PromptsDir
    )

    New-Item -ItemType Directory -Path $PromptsDir -Force | Out-Null

    $agentFiles = Get-ChildItem -Path "$AgentsDir/sl.*.agent.md" -File -ErrorAction SilentlyContinue
    
    foreach ($agentFile in $agentFiles) {
        $basename = $agentFile.Name -replace '\.agent\.md$', ''
        $promptFile = Join-Path $PromptsDir "$basename.prompt.md"
        
        $content = @"
---
agent: $basename
---
"@
        Set-Content -Path $promptFile -Value $content
    }
}

function Build-Variant {
    param(
        [string]$Agent,
        [string]$Script
    )
    
    $baseDir = Join-Path $GenReleasesDir "sdd-${Agent}-package-${Script}"
    Write-Host "Building $Agent ($Script) package..."
    New-Item -ItemType Directory -Path $baseDir -Force | Out-Null
    
    # Copy base structure but filter scripts by variant
    $specDir = Join-Path $baseDir ".speclite"
    New-Item -ItemType Directory -Path $specDir -Force | Out-Null

    # Copy memory directory
    if (Test-Path "memory") {
        Copy-Item -Path "memory" -Destination $specDir -Recurse -Force
        Write-Host "Copied memory -> .speclite"
    }

    # Only copy the relevant script variant directory
    if (Test-Path "scripts") {
        $scriptsDestDir = Join-Path $specDir "scripts"
        New-Item -ItemType Directory -Path $scriptsDestDir -Force | Out-Null

        switch ($Script) {
            'sh' {
                if (Test-Path "scripts/bash") {
                    Copy-Item -Path "scripts/bash" -Destination $scriptsDestDir -Recurse -Force
                    Write-Host "Copied scripts/bash -> .speclite/scripts"
                }
            }
            'ps' {
                if (Test-Path "scripts/powershell") {
                    Copy-Item -Path "scripts/powershell" -Destination $scriptsDestDir -Recurse -Force
                    Write-Host "Copied scripts/powershell -> .speclite/scripts"
                }
            }
        }

        # Copy any script files that aren't in variant-specific directories
        Get-ChildItem -Path "scripts" -File -ErrorAction SilentlyContinue | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $scriptsDestDir -Force
        }
    }

    # Copy templates (excluding commands directory and vscode-settings.json)
    if (Test-Path "templates") {
        $templatesDestDir = Join-Path $specDir "templates"
        New-Item -ItemType Directory -Path $templatesDestDir -Force | Out-Null

        Get-ChildItem -Path "templates" -Recurse -File | Where-Object {
            $_.FullName -notmatch 'templates[/\\]commands[/\\]' -and $_.Name -ne 'vscode-settings.json'
        } | ForEach-Object {
            $relativePath = $_.FullName.Substring((Resolve-Path "templates").Path.Length + 1)
            $destFile = Join-Path $templatesDestDir $relativePath
            $destFileDir = Split-Path $destFile -Parent
            New-Item -ItemType Directory -Path $destFileDir -Force | Out-Null
            Copy-Item -Path $_.FullName -Destination $destFile -Force
        }
        Write-Host "Copied templates -> .speclite/templates"
    }
    
    # Generate agent-specific command files
    switch ($Agent) {
        'claude' {
            $cmdDir = Join-Path $baseDir ".claude/commands"
            Generate-Commands -Agent 'claude' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'gemini' {
            $cmdDir = Join-Path $baseDir ".gemini/commands"
            Generate-Commands -Agent 'gemini' -Extension 'toml' -ArgFormat '{{args}}' -OutputDir $cmdDir -ScriptVariant $Script
            if (Test-Path "agent_templates/gemini/GEMINI.md") {
                Copy-Item -Path "agent_templates/gemini/GEMINI.md" -Destination (Join-Path $baseDir "GEMINI.md")
            }
        }
        'copilot' {
            $agentsDir = Join-Path $baseDir ".github/agents"
            Generate-Commands -Agent 'copilot' -Extension 'agent.md' -ArgFormat '$ARGUMENTS' -OutputDir $agentsDir -ScriptVariant $Script

            # Generate companion prompt files
            $promptsDir = Join-Path $baseDir ".github/prompts"
            Generate-CopilotPrompts -AgentsDir $agentsDir -PromptsDir $promptsDir

            # Create VS Code workspace settings
            $vscodeDir = Join-Path $baseDir ".vscode"
            New-Item -ItemType Directory -Path $vscodeDir -Force | Out-Null
            if (Test-Path "templates/vscode-settings.json") {
                Copy-Item -Path "templates/vscode-settings.json" -Destination (Join-Path $vscodeDir "settings.json")
            }
        }
        'cursor-agent' {
            $cmdDir = Join-Path $baseDir ".cursor/commands"
            Generate-Commands -Agent 'cursor-agent' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
        'codex' {
            $cmdDir = Join-Path $baseDir ".codex/prompts"
            Generate-Commands -Agent 'codex' -Extension 'md' -ArgFormat '$ARGUMENTS' -OutputDir $cmdDir -ScriptVariant $Script
        }
    }

    # Create zip archive
    $zipFile = Join-Path $GenReleasesDir "speclite-template-${Agent}-${Script}-${Version}.zip"
    Compress-Archive -Path "$baseDir/*" -DestinationPath $zipFile -Force
    Write-Host "Created $zipFile"
}

# Define all agents and scripts
$AllAgents = @('claude', 'gemini', 'copilot', 'cursor-agent', 'codex')
$AllScripts = @('sh', 'ps')

function Normalize-List {
    param([string]$Input)
    
    if ([string]::IsNullOrEmpty($Input)) {
        return @()
    }
    
    # Split by comma or space and remove duplicates while preserving order
    $items = $Input -split '[,\s]+' | Where-Object { $_ } | Select-Object -Unique
    return $items
}

function Validate-Subset {
    param(
        [string]$Type,
        [string[]]$Allowed,
        [string[]]$Items
    )
    
    $ok = $true
    foreach ($item in $Items) {
        if ($item -notin $Allowed) {
            Write-Error "Unknown $Type '$item' (allowed: $($Allowed -join ', '))"
            $ok = $false
        }
    }
    return $ok
}

# Determine agent list
if (-not [string]::IsNullOrEmpty($Agents)) {
    $AgentList = Normalize-List -Input $Agents
    if (-not (Validate-Subset -Type 'agent' -Allowed $AllAgents -Items $AgentList)) {
        exit 1
    }
} else {
    $AgentList = $AllAgents
}

# Determine script list
if (-not [string]::IsNullOrEmpty($Scripts)) {
    $ScriptList = Normalize-List -Input $Scripts
    if (-not (Validate-Subset -Type 'script' -Allowed $AllScripts -Items $ScriptList)) {
        exit 1
    }
} else {
    $ScriptList = $AllScripts
}

Write-Host "Agents: $($AgentList -join ', ')"
Write-Host "Scripts: $($ScriptList -join ', ')"

# Build all variants
foreach ($agent in $AgentList) {
    foreach ($script in $ScriptList) {
        Build-Variant -Agent $agent -Script $script
    }
}

Write-Host "`nArchives in ${GenReleasesDir}:"
Get-ChildItem -Path $GenReleasesDir -Filter "speclite-template-*-${Version}.zip" | ForEach-Object {
    Write-Host "  $($_.Name)"
}