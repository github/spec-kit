#!/usr/bin/env pwsh
# update-agent-context.ps1
#
# Refresh the managed Spec Kit section in the coding agent's context file
# (e.g. CLAUDE.md, .github/copilot-instructions.md, AGENTS.md).
#
# Reads `context_file` and `context_markers.{start,end}` from the
# agent-context extension config:
#   .specify/extensions/agent-context/agent-context-config.yml
#
# Usage: update-agent-context.ps1 [plan_path]

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$PlanPath
)

$ErrorActionPreference = 'Stop'
$DefaultStart = '<!-- SPECKIT START -->'
$DefaultEnd   = '<!-- SPECKIT END -->'
$ProjectRoot  = (Get-Location).Path
$ExtConfig    = Join-Path $ProjectRoot '.specify/extensions/agent-context/agent-context-config.yml'

if (-not (Test-Path -LiteralPath $ExtConfig)) {
    Write-Host "agent-context: $ExtConfig not found; nothing to do."
    exit 0
}

try {
    $Options = Get-Content -LiteralPath $ExtConfig -Raw | ConvertFrom-Yaml -ErrorAction Stop
} catch {
    # ConvertFrom-Yaml may not be available on all systems.
    # Fall back to Python+PyYAML for consistent parsing semantics.
    $pythonCmd = $null
    foreach ($candidate in @('python3', 'python')) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            $pythonCmd = $candidate
            break
        }
    }

    if ($pythonCmd) {
        try {
            $jsonOut = & $pythonCmd -c @'
import json
import sys
try:
    import yaml
except Exception:
    yaml = None

try:
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) if yaml else {}
except Exception:
    data = {}

if not isinstance(data, dict):
    data = {}

print(json.dumps(data))
'@ $ExtConfig
            if ($LASTEXITCODE -eq 0 -and $jsonOut) {
                $Options = $jsonOut | ConvertFrom-Json -AsHashtable -ErrorAction Stop
            }
        } catch {
            $Options = $null
        }
    }

    if (-not $Options) {
        Write-Warning "agent-context: unable to parse $ExtConfig; skipping update."
        exit 0
    }
}

$ContextFile = $Options['context_file']
if (-not $ContextFile) {
    Write-Host 'agent-context: context_file not set in extension config; nothing to do.'
    exit 0
}

$MarkerStart = $DefaultStart
$MarkerEnd   = $DefaultEnd
$cm = $Options['context_markers']
if ($cm) {
    if ($cm['start'] -is [string] -and $cm['start']) {
        $MarkerStart = $cm['start']
    }
    if ($cm['end'] -is [string] -and $cm['end']) {
        $MarkerEnd = $cm['end']
    }
}

if (-not $PlanPath) {
    # Discover plan.md exactly one level deep (specs/<feature>/plan.md),
    # matching the bash glob specs/*/plan.md. Wrap in try/catch so access errors under
    # $ErrorActionPreference = 'Stop' don't abort the script.
    try {
        $specsDir = Join-Path $ProjectRoot 'specs'
        $candidate = Get-ChildItem -Path $specsDir -Directory -ErrorAction SilentlyContinue |
            ForEach-Object { Get-Item -LiteralPath (Join-Path $_.FullName 'plan.md') -ErrorAction SilentlyContinue } |
            Where-Object { $_ } |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($candidate) {
            $PlanPath = [System.IO.Path]::GetRelativePath($ProjectRoot, $candidate.FullName).Replace('\','/')
        }
    } catch {
        # Non-fatal: continue without a plan path.
    }
}

$CtxPath = Join-Path $ProjectRoot $ContextFile
$CtxDir  = Split-Path -Parent $CtxPath
if ($CtxDir -and -not (Test-Path -LiteralPath $CtxDir)) {
    New-Item -ItemType Directory -Path $CtxDir -Force | Out-Null
}

$lines = @($MarkerStart,
           'For additional context about technologies to be used, project structure,',
           'shell commands, and other important information, read the current plan')
if ($PlanPath) {
    $lines += "at $PlanPath"
}
$lines += $MarkerEnd
$Section = ($lines -join "`n") + "`n"

if (Test-Path -LiteralPath $CtxPath) {
    $rawBytes = [System.IO.File]::ReadAllBytes($CtxPath)
    # Strip UTF-8 BOM if present
    if ($rawBytes.Length -ge 3 -and $rawBytes[0] -eq 0xEF -and $rawBytes[1] -eq 0xBB -and $rawBytes[2] -eq 0xBF) {
        $content = [System.Text.Encoding]::UTF8.GetString($rawBytes, 3, $rawBytes.Length - 3)
    } else {
        $content = [System.Text.Encoding]::UTF8.GetString($rawBytes)
    }

    $s = $content.IndexOf($MarkerStart)
    $e = if ($s -ge 0) { $content.IndexOf($MarkerEnd, $s) } else { $content.IndexOf($MarkerEnd) }

    if ($s -ge 0 -and $e -ge 0 -and $e -gt $s) {
        $endOfMarker = $e + $MarkerEnd.Length
        if ($endOfMarker -lt $content.Length -and $content[$endOfMarker] -eq "`r") { $endOfMarker++ }
        if ($endOfMarker -lt $content.Length -and $content[$endOfMarker] -eq "`n") { $endOfMarker++ }
        $newContent = $content.Substring(0, $s) + $Section + $content.Substring($endOfMarker)
    } elseif ($s -ge 0) {
        $newContent = $content.Substring(0, $s) + $Section
    } elseif ($e -ge 0) {
        $endOfMarker = $e + $MarkerEnd.Length
        if ($endOfMarker -lt $content.Length -and $content[$endOfMarker] -eq "`r") { $endOfMarker++ }
        if ($endOfMarker -lt $content.Length -and $content[$endOfMarker] -eq "`n") { $endOfMarker++ }
        $newContent = $Section + $content.Substring($endOfMarker)
    } else {
        if ($content -and -not $content.EndsWith("`n")) { $content += "`n" }
        if ($content) { $newContent = $content + "`n" + $Section } else { $newContent = $Section }
    }
} else {
    $newContent = $Section
}

$newContent = $newContent.Replace("`r`n", "`n").Replace("`r", "`n")
[System.IO.File]::WriteAllText($CtxPath, $newContent, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "agent-context: updated $ContextFile"
