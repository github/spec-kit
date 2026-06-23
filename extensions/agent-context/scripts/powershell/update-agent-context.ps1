#!/usr/bin/env pwsh
# update-agent-context.ps1
#
# Refresh the managed Spec Kit section in the coding agent's context file(s)
# (e.g. CLAUDE.md, .github/copilot-instructions.md, AGENTS.md).
#
# Reads `context_files` or `context_file`, plus `context_markers.{start,end}`, from the
# agent-context extension config:
#   .specify/extensions/agent-context/agent-context-config.yml
#
# Usage: update-agent-context.ps1 [plan_path]

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$PlanPath
)

function Get-ConfigValue {
    param(
        [AllowNull()][object]$Object,
        [Parameter(Mandatory = $true)][string]$Key
    )

    if ($null -eq $Object) {
        return $null
    }
    if ($Object -is [System.Collections.IDictionary]) {
        return $Object[$Key]
    }
    $prop = $Object.PSObject.Properties[$Key]
    if ($prop) {
        return $prop.Value
    }
    return $null
}

function Test-ConfigObject {
    param(
        [AllowNull()][object]$Object
    )

    if ($null -eq $Object) {
        return $false
    }
    if ($Object -is [System.Collections.IDictionary]) {
        return $true
    }
    if ($Object -is [System.Management.Automation.PSCustomObject]) {
        return $true
    }
    return $false
}

function Resolve-ContextPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$RelativePath
    )

    $rootFull = [System.IO.Path]::GetFullPath($Root)
    $segments = $RelativePath -split '/'
    $resolved = $rootFull

    foreach ($segment in $segments) {
        if ([string]::IsNullOrWhiteSpace($segment) -or $segment -eq '.') {
            continue
        }

        $candidate = [System.IO.Path]::GetFullPath((Join-Path $resolved $segment))
        if (Test-Path -LiteralPath $candidate) {
            $item = Get-Item -LiteralPath $candidate -Force
            if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
                $target = $item.Target
                if ($target -is [System.Array]) {
                    $target = $target[0]
                }
                if ($target) {
                    if ([System.IO.Path]::IsPathRooted($target)) {
                        $candidate = [System.IO.Path]::GetFullPath($target)
                    } else {
                        $candidate = [System.IO.Path]::GetFullPath(
                            (Join-Path (Split-Path -Parent $candidate) $target)
                        )
                    }
                }
            }
        }
        $resolved = $candidate
    }

    return $resolved
}

function Test-IsSubPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $comparison = if ([System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT) {
        [System.StringComparison]::OrdinalIgnoreCase
    } else {
        [System.StringComparison]::Ordinal
    }
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
    $pathFull = [System.IO.Path]::GetFullPath($Path)
    return $pathFull.Equals($rootFull, $comparison) -or
        $pathFull.StartsWith($rootFull + [System.IO.Path]::DirectorySeparatorChar, $comparison)
}

$ErrorActionPreference = 'Stop'
$DefaultStart = '<!-- SPECKIT START -->'
$DefaultEnd   = '<!-- SPECKIT END -->'
$ProjectRoot  = (Get-Location).Path
$ExtConfig    = Join-Path $ProjectRoot '.specify/extensions/agent-context/agent-context-config.yml'

if (-not (Test-Path -LiteralPath $ExtConfig)) {
    Write-Warning "agent-context: $ExtConfig not found; nothing to do."
    exit 0
}

$Options = $null
if (Get-Command ConvertFrom-Yaml -ErrorAction SilentlyContinue) {
    try {
        $Options = Get-Content -LiteralPath $ExtConfig -Raw | ConvertFrom-Yaml -ErrorAction Stop
    } catch {
        # fall through to Python fallback
    }
}

if ($null -eq $Options) {
    # ConvertFrom-Yaml unavailable or failed; fall back to Python+PyYAML.
    $pythonCmd = $null
    $pythonCandidates = @()
    if ($env:SPECKIT_PYTHON) {
        $pythonCandidates += $env:SPECKIT_PYTHON
    }
    $pythonCandidates += @('python3', 'python')
    foreach ($candidate in $pythonCandidates) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            # Verify it is Python 3 with PyYAML available.
            $null = & $candidate -c "import sys; import yaml; sys.exit(0 if sys.version_info[0] == 3 else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $pythonCmd = $candidate
                break
            }
        }
    }

    if ($pythonCmd) {
        $pyScript = $null
        try {
            $pyScript = [System.IO.Path]::GetTempFileName()
            Set-Content -LiteralPath $pyScript -Encoding UTF8 -Value @'
import json
import sys
try:
    import yaml
except ImportError:
    print(
        "agent-context: PyYAML is required to parse extension config; cannot update context.",
        file=sys.stderr,
    )
    sys.exit(2)

try:
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
except Exception as exc:
    print(
        f"agent-context: unable to parse {sys.argv[1]} ({exc}); cannot update context.",
        file=sys.stderr,
    )
    sys.exit(2)

if not isinstance(data, dict):
    data = {}

print(json.dumps(data))
'@
            $jsonOut = & $pythonCmd $pyScript $ExtConfig
            if ($LASTEXITCODE -eq 0 -and $jsonOut) {
                $Options = $jsonOut | ConvertFrom-Json -ErrorAction Stop
            }
        } catch {
            $Options = $null
        } finally {
            if ($pyScript -and (Test-Path -LiteralPath $pyScript)) {
                Remove-Item -LiteralPath $pyScript -Force -ErrorAction SilentlyContinue
            }
        }
    }

    if (-not $Options) {
        Write-Warning "agent-context: unable to parse $ExtConfig; skipping update."
        exit 0
    }
}

if (-not (Test-ConfigObject -Object $Options)) {
    Write-Warning "agent-context: $ExtConfig must contain a YAML mapping; skipping update."
    exit 0
}

$ConfiguredContextFiles = Get-ConfigValue -Object $Options -Key 'context_files'
$ContextFiles = @()
if ($null -ne $ConfiguredContextFiles) {
    foreach ($item in @($ConfiguredContextFiles)) {
        if ($item -is [string] -and -not [string]::IsNullOrWhiteSpace($item)) {
            $ContextFiles += $item.Trim()
        }
    }
}
if ($ContextFiles.Count -eq 0) {
    $ContextFile = Get-ConfigValue -Object $Options -Key 'context_file'
    if ($ContextFile -is [string] -and -not [string]::IsNullOrWhiteSpace($ContextFile)) {
        $ContextFiles += $ContextFile.Trim()
    }
}
$pathComparison = if ([System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT) {
    [System.StringComparer]::OrdinalIgnoreCase
} else {
    [System.StringComparer]::Ordinal
}
$seenContextFiles = [System.Collections.Generic.HashSet[string]]::new($pathComparison)
$dedupedContextFiles = @()
foreach ($ContextFile in $ContextFiles) {
    if ($seenContextFiles.Add($ContextFile)) {
        $dedupedContextFiles += $ContextFile
    }
}
$ContextFiles = $dedupedContextFiles
if ($ContextFiles.Count -eq 0) {
    Write-Warning 'agent-context: context_files/context_file not set in extension config; nothing to do.'
    exit 0
}

foreach ($ContextFile in $ContextFiles) {
    # Reject absolute paths, drive-qualified paths, backslash separators, and '..' path segments in context files
    if ($ContextFile -match '^[A-Za-z]:') {
        Write-Warning "agent-context: context files must be project-relative paths; got '$ContextFile'."
        exit 1
    }
    if ([System.IO.Path]::IsPathRooted($ContextFile)) {
        Write-Warning "agent-context: context files must be project-relative paths; got '$ContextFile'."
        exit 1
    }
    if ($ContextFile.Contains('\')) {
        Write-Warning "agent-context: context files must not contain backslash separators; got '$ContextFile'."
        exit 1
    }
    $cfSegments = $ContextFile -split '[/\\]'
    if ($cfSegments -contains '..') {
        Write-Warning "agent-context: context files must not contain '..' path segments; got '$ContextFile'."
        exit 1
    }
    $resolvedTarget = Resolve-ContextPath -Root $ProjectRoot -RelativePath $ContextFile
    if (-not (Test-IsSubPath -Root $ProjectRoot -Path $resolvedTarget)) {
        Write-Warning "agent-context: context file path resolves outside the project root; got '$ContextFile'."
        exit 1
    }
}

$MarkerStart = $DefaultStart
$MarkerEnd   = $DefaultEnd
$cm = Get-ConfigValue -Object $Options -Key 'context_markers'
if ($cm) {
    $cmStart = Get-ConfigValue -Object $cm -Key 'start'
    if ($cmStart -is [string] -and $cmStart) {
        $MarkerStart = $cmStart
    }
    $cmEnd = Get-ConfigValue -Object $cm -Key 'end'
    if ($cmEnd -is [string] -and $cmEnd) {
        $MarkerEnd = $cmEnd
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

$lines = @($MarkerStart,
           'For additional context about technologies to be used, project structure,',
           'shell commands, and other important information, read the current plan')
if ($PlanPath) {
    $lines += "at $PlanPath"
}
$lines += $MarkerEnd
$Section = ($lines -join "`n") + "`n"

foreach ($ContextFile in $ContextFiles) {
    $CtxPath = Join-Path $ProjectRoot $ContextFile
    $CtxDir  = Split-Path -Parent $CtxPath
    if ($CtxDir -and -not (Test-Path -LiteralPath $CtxDir)) {
        New-Item -ItemType Directory -Path $CtxDir -Force | Out-Null
    }

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
}
