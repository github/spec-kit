#!/usr/bin/env pwsh

# Create release packages for Spec Kit templates
#
# This script generates zip archives for each supported AI agent,
# containing pre-configured command files and directory structures.

#==============================================================================
# Configuration
#==============================================================================

# All supported agents
$AllAgents = @('copilot','claude','gemini','cursor-agent','qwen','opencode','codex','windsurf','kilocode','auggie','codebuddy','qodercli','roo','kiro-cli','amp','shai','tabnine','agy','bob','vibe','kimi','generic')

# Version from git tag or default
$Version = if ($env:VERSION) { $env:VERSION } else {
    try {
        (git describe --tags --always 2>$null) | Out-String -Stream | Select-Object -First 1
    } catch {
        'dev'
    }
}
if (-not $Version) { $Version = 'dev' }

# Output directory
$OutputDir = ".genreleases"

#==============================================================================
# Functions
#==============================================================================

# Generate command files for an agent
function Generate-Commands {
    param(
        [string]$Agent,
        [string]$Format,
        [string]$Args,
        [string]$DestDir,
        [string]$Script
    )
    
    # Command names follow the speckit.* pattern
    $Commands = @(
        "speckit.constitution",
        "speckit.specify",
        "speckit.clarify",
        "speckit.plan",
        "speckit.tasks",
        "speckit.analyze",
        "speckit.checklist",
        "speckit.implement",
        "speckit.taskstoissues",
        "add-dir"
    )
    
    foreach ($Cmd in $Commands) {
        $Filename = "${Cmd}.${Format}"
        $Filepath = Join-Path $DestDir $Filename
        
        # Create command file with appropriate format
        switch ($Format) {
            'md' {
                @"`
---
description: "${Cmd} command for Spec Kit"
---

# ${Cmd}

Execute the ${Cmd} workflow with arguments: ${Args}
"@ | Set-Content -Path $Filepath -Encoding UTF8
            }
            'toml' {
                @"`
description = "${Cmd} command for Spec Kit"

prompt = """
Execute the ${Cmd} workflow with arguments: ${Args}
"""
"@ | Set-Content -Path $Filepath -Encoding UTF8
            }
        }
    }
}

# Create Kimi Code skills in .kimi/skills/<name>/SKILL.md format.
# Kimi CLI discovers skills as directories containing a SKILL.md file.
function New-KimiSkills {
    param([string]$SkillsDir)

    $skills = @('constitution', 'specify', 'clarify', 'plan', 'tasks', 'analyze', 'checklist', 'implement', 'taskstoissues')
    foreach ($skill in $skills) {
        $skillName = "speckit.$skill"
        $skillDir = Join-Path $SkillsDir $skillName
        New-Item -ItemType Directory -Force -Path $skillDir | Out-Null
        @"
---
name: "$skillName"
description: "Spec Kit: $skill workflow"
---

Execute the $skillName workflow.
"@ | Set-Content -Path (Join-Path $skillDir "SKILL.md") -Encoding UTF8
    }

    # add-dir skill
    $addDirDir = Join-Path $SkillsDir "add-dir"
    New-Item -ItemType Directory -Force -Path $addDirDir | Out-Null
    @'
---
name: "add-dir"
description: "Add a directory to the Spec Kit project structure"
---

Execute the add-dir workflow with arguments: $ARGUMENTS
'@ | Set-Content -Path (Join-Path $addDirDir "SKILL.md") -Encoding UTF8
}

# Create release package for an agent
function Create-Package {
    param(
        [string]$Agent,
        [string]$Script  # sh or ps
    )
    
    $BaseDir = Join-Path $OutputDir "temp-${Agent}-${Script}"
    
    # Create directory structure based on agent type
    switch ($Agent) {
        'copilot' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.github\agents" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.github\agents" -Script $Script
        }
        'claude' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.claude\commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.claude\commands" -Script $Script
        }
        'gemini' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.gemini\commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'toml' -Args '{{args}}' -DestDir "$BaseDir/.gemini\commands" -Script $Script
        }
        'cursor-agent' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.cursor\commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.cursor\commands" -Script $Script
        }
        'qwen' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.qwen\commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'toml' -Args '{{args}}' -DestDir "$BaseDir/.qwen\commands" -Script $Script
        }
        'opencode' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.opencode\command" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.opencode\command" -Script $Script
        }
        'codex' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.codex\prompts" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.codex\prompts" -Script $Script
        }
        'windsurf' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.windsurf\workflows" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.windsurf\workflows" -Script $Script
        }
        'kilocode' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.kilocode\workflows" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.kilocode\workflows" -Script $Script
        }
        'auggie' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.augment\commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.augment\commands" -Script $Script
        }
        'codebuddy' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.codebuddy\commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.codebuddy\commands" -Script $Script
        }
        'qodercli' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.qoder\commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.qoder\commands" -Script $Script
        }
        'roo' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.roo\commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.roo\commands" -Script $Script
        }
        'kiro-cli' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.kiro/prompts" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.kiro/prompts" -Script $Script
        }
        'amp' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.agents\commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.agents\commands" -Script $Script
        }
        'shai' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.shai/commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.shai/commands" -Script $Script
        }
        'agy' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.agent/workflows" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.agent/workflows" -Script $Script
        }
        'bob' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.bob\commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.bob\commands" -Script $Script
        }
        'tabnine' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.tabnine/agent/commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'toml' -Args '{{args}}' -DestDir "$BaseDir/.tabnine/agent/commands" -Script $Script
        }
        'vibe' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.vibe\prompts" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.vibe\prompts" -Script $Script
        }
        'generic' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.speckit\commands" | Out-Null
            Generate-Commands -Agent $Agent -Format 'md' -Args '$ARGUMENTS' -DestDir "$BaseDir/.speckit\commands" -Script $Script
        }
        'kimi' {
            New-Item -ItemType Directory -Force -Path "$BaseDir/.kimi/skills" | Out-Null
            New-KimiSkills -SkillsDir "$BaseDir/.kimi/skills"
        }
    }
    
    # Create the zip archive
    $ZipName = "spec-kit-template-${Agent}-${Script}-${Version}.zip"
    $ZipPath = Join-Path $OutputDir $ZipName
    
    if (Test-Path $ZipPath) {
        Remove-Item $ZipPath -Force
    }
    
    Compress-Archive -Path "$BaseDir\*" -DestinationPath $ZipPath -Force
    
    # Cleanup temp directory
    Remove-Item $BaseDir -Recurse -Force
    
    Write-Host "Created: $ZipName"
}

#==============================================================================
# Main
#==============================================================================

# Create output directory
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# Clean up old temp directories
Get-ChildItem -Path $OutputDir -Filter "temp-*" -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

# Generate packages for all agents
Write-Host "Generating release packages for version: $Version"
Write-Host ""

foreach ($Agent in $AllAgents) {
    Write-Host "Processing agent: $Agent"
    
    # Create bash/zsh package
    Create-Package -Agent $Agent -Script 'sh'
    
    # Create PowerShell package
    Create-Package -Agent $Agent -Script 'ps'
}

Write-Host ""
Write-Host "All packages created in: $OutputDir"
Write-Host "Packages:"
Get-ChildItem -Path "$OutputDir\spec-kit-template-*-${Version}.zip" -ErrorAction SilentlyContinue | ForEach-Object { $_.Name }
