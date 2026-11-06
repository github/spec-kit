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
#
# When `plan_path` is omitted, the script derives it from `.specify/feature.json`
# (written by /speckit-specify). Falls back to the most recently modified
# `specs/**/plan.md` only when feature.json is absent or its plan does not exist yet.

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$PlanPath
)

function Add-MdcFrontmatter {
    <#
        Ensure .mdc content has YAML frontmatter with alwaysApply: true.

        Cursor only auto-loads .mdc rule files that carry frontmatter with
        alwaysApply: true. Prepend it when missing, or repair the value while
        preserving any existing frontmatter comments/formatting.
    #>
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content)

    $leading = ''
    $stripped = $Content
    $m = [regex]::Match($Content, '^\s*')
    if ($m.Success) {
        $leading = $m.Value
        $stripped = $Content.Substring($m.Length)
    }

    if (-not $stripped.StartsWith('---')) {
        return "---`nalwaysApply: true`n---`n`n" + $Content
    }

    $fm = [regex]::Match($stripped, '^(---[ \t]*\r?\n)(.*?)(\r?\n---[ \t]*)(\r?\n|$)(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if (-not $fm.Success) {
        return "---`nalwaysApply: true`n---`n`n" + $Content
    }

    $opening = $fm.Groups[1].Value
    $fmText  = $fm.Groups[2].Value
    $closing = $fm.Groups[3].Value
    $sep     = $fm.Groups[4].Value
    $rest    = $fm.Groups[5].Value
    $newline = if ($opening.Contains("`r`n")) { "`r`n" } else { "`n" }

    if ([regex]::IsMatch($fmText, '(?m)^[ \t]*alwaysApply[ \t]*:[ \t]*true[ \t]*(?:#.*)?$')) {
        return $Content
    }

    if ([regex]::IsMatch($fmText, '(?m)^[ \t]*alwaysApply[ \t]*:')) {
        $alwaysApplyRegex = [regex]'(?m)^([ \t]*)alwaysApply[ \t]*:.*?([ \t]*(?:#.*)?)$'
        $fmText = $alwaysApplyRegex.Replace($fmText, '${1}alwaysApply: true${2}', 1)
    } elseif ($fmText.Trim()) {
        $fmText = $fmText + $newline + 'alwaysApply: true'
    } else {
        $fmText = 'alwaysApply: true'
    }

    return "$leading$opening$fmText$closing$sep$rest"
}

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

function Get-LinkTarget {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    # Read a link's target. Get-Item is the Windows PowerShell 5.1
    # path, but its cmdlets normalize backslashes on Unix, so a link
    # whose path contains a backslash cannot be read that way; .NET's
    # LinkTarget (pwsh 7+ on Unix) preserves Unix filename semantics.
    # Returns $null when the target cannot be read, so the caller
    # treats the link as unresolvable instead of following a wrong path.
    if ($Path.Contains('\') -and [System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
        # Use the .NET lookup first here, not only after a provider
        # exception: when the normalized spelling also exists, Get-Item
        # succeeds on that entry and returns the wrong target, so the
        # fallback below is never reached. A $null result means the
        # literal path has no readable target; return it rather than
        # falling through to the provider, which would resolve the
        # normalized spelling.
        $linkTargetProperty = [System.IO.FileInfo].GetProperty('LinkTarget')
        if ($null -ne $linkTargetProperty) {
            try {
                return $linkTargetProperty.GetValue([System.IO.FileInfo]::new($Path))
            } catch {
                return $null
            }
        }
    }
    try {
        $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
        $target = $item.Target
        if ($target -is [System.Array]) {
            $target = $target[0]
        }
        return $target
    } catch {
        try {
            $linkTargetProperty = [System.IO.FileInfo].GetProperty('LinkTarget')
            if ($null -ne $linkTargetProperty) {
                return $linkTargetProperty.GetValue([System.IO.FileInfo]::new($Path))
            }
        } catch {
            # Cannot read the target; fall through to $null.
        }
        return $null
    }
}

function Resolve-ContextPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        # Optional, not mandatory: a link that targets a filesystem
        # root resolves to an empty relative path, and a mandatory
        # string parameter rejects the empty string at bind time,
        # aborting the whole fallback. Empty means the base directory.
        [string]$RelativePath = '',
        [string]$Base = $null,
        [int]$Depth = 10
    )

    # Resolve $RelativePath segment-by-segment from $Base (the project
    # root by default; a link's parent dir when following a link
    # target), following one link per segment. '..' pops the last
    # already-resolved component instead of being collapsed lexically:
    # a symlinked parent must win over the lexical spelling, so
    # plans/alias/../current.md (alias -> archive/nested) reaches
    # archive/current.md, not plans/current.md. Link chains are bounded
    # by $Depth so a cycle terminates; the caller re-runs until the
    # result stabilizes.
    if (-not $Base) {
        $Base = $Root
    }
    $resolved = [System.IO.Path]::GetFullPath($Base)

    # Split only on the host platform's separators: on Unix a backslash
    # is a valid filename character, not a separator, so splitting on it
    # would turn one filename into two components and let a symlink
    # target escape the containment check.
    $separators = [char[]]@(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
    foreach ($segment in $RelativePath.Split($separators)) {
        # Skip only empty components and '.': a whitespace-only
        # component is a valid Unix directory name, so it must be
        # preserved — discarding it lets a later '..' validate
        # against a path the write never follows. Compare with
        # ordinal equality: PowerShell's culture-sensitive -eq
        # treats a name of '.' or '..' plus an ignorable Unicode
        # character (e.g. U+034F) as a dot segment, so the resolver
        # would skip or pop a real directory instead of inspecting it.
        if ([string]::IsNullOrEmpty($segment) -or [string]::Equals($segment, '.', [System.StringComparison]::Ordinal)) {
            continue
        }

        if ([string]::Equals($segment, '..', [System.StringComparison]::Ordinal)) {
            # Parent of the resolved path, clamped at the filesystem
            # root (GetDirectoryName returns null above it). Never
            # collapse '..' against an unresolved spelling.
            # GetDirectoryName, not Split-Path: the cmdlet normalizes
            # backslashes on Unix, so the parent of a backslash-named
            # directory would be wrong.
            # Require the preceding component to be an existing
            # directory first: a missing or non-directory component
            # followed by '..' must not be popped lexically, or a
            # broken link rewrites to an existing file and gets
            # selected by mistake. Reject the resolution instead.
            $precedingAttributes = $null
            try {
                $precedingAttributes = [System.IO.File]::GetAttributes($resolved)
            } catch {
                return $null
            }
            if (($precedingAttributes -band [System.IO.FileAttributes]::Directory) -eq 0) {
                return $null
            }
            $parent = [System.IO.Path]::GetDirectoryName($resolved)
            if ($parent) {
                $resolved = $parent
            }
            continue
        }

        # Concatenate, do not Join-Path: the cmdlet normalizes
        # backslashes on Unix, turning one filename into two components.
        $candidate = [System.IO.Path]::GetFullPath($resolved + [System.IO.Path]::DirectorySeparatorChar + $segment)
        # File.GetAttributes, not Test-Path/Get-Item: the cmdlets
        # normalize backslashes on Unix and cannot see a path that
        # contains one. GetAttributes reports the link itself.
        $attributes = $null
        try {
            $attributes = [System.IO.File]::GetAttributes($candidate)
        } catch {
            # Missing or unreadable: not a link, keep walking.
        }
        if ($null -ne $attributes -and ($attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
            if ($Depth -le 0) {
                # Depth exhausted: the link cannot be followed, so the
                # rest of the path cannot be resolved reliably — a
                # later '..' would collapse against the unresolved
                # spelling and validate a path the write never follows.
                # Return unresolved instead of walking on.
                return $null
            }
            $target = Get-LinkTarget -Path $candidate
            if ($target) {
                # Per-candidate total link-follow budget: each
                # followed link spends one unit, shared across
                # that candidate's recursive calls and fallback
                # passes alike. The per-chain depth bound alone
                # cannot stop a structure that re-expands the
                # same targets (L1 -> L0/L0/..., L2 -> L1/L1/...),
                # so total work is capped here; when it is spent,
                # the candidate cannot be resolved and the null
                # propagates up the chain for the caller to reject.
                if ($script:LinkFollowBudgetRemaining -le 0) {
                    return $null
                }
                $script:LinkFollowBudgetRemaining--
                if ([System.IO.Path]::IsPathRooted($target)) {
                    # Absolute target: walk its components from the
                    # filesystem root, not from the project root.
                    $targetRoot = [System.IO.Path]::GetPathRoot($target)
                    $followed = Resolve-ContextPath -Root $Root -RelativePath $target.Substring($targetRoot.Length) -Base $targetRoot -Depth ($Depth - 1)
                } else {
                    # Relative target: walk its components from the
                    # link's parent dir ($resolved here).
                    $followed = Resolve-ContextPath -Root $Root -RelativePath $target -Base $resolved -Depth ($Depth - 1)
                }
                if ($null -eq $followed) {
                    return $null
                }
                $candidate = $followed
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

function ConvertTo-SlashPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    # Normalize '\' to '/' for string prefix comparisons on Windows
    # only: on Unix a backslash is a valid filename character and must
    # be preserved, or a plan under a backslash-named directory is
    # resolved at a path that does not exist.
    if ([System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT) {
        return $Path.Replace('\', '/')
    }
    return $Path
}

# Link follows allowed per resolution unit (one candidate, or one
# context file), shared across that unit's recursion and fallback
# passes. The per-chain depth bound alone cannot stop a structure
# that re-expands the same targets, so total work is capped; when it
# is spent, the unit cannot be resolved. Scoped per unit: a rejected
# candidate must not consume the budget of later ones.
$script:LinkFollowBudget = 1000
$script:LinkFollowBudgetRemaining = $script:LinkFollowBudget

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
        $Options = Get-Content -LiteralPath $ExtConfig -Raw -Encoding UTF8 | ConvertFrom-Yaml -ErrorAction Stop
    } catch {
        # fall through to ConvertFrom-Json fallback
    }
}

if ($null -eq $Options) {
    # ConvertFrom-Yaml unavailable or failed; try ConvertFrom-Json (no external deps,
    # works when the config file is valid JSON, which is a subset of YAML).
    try {
        $raw = Get-Content -LiteralPath $ExtConfig -Raw -Encoding UTF8
        $Options = $raw | ConvertFrom-Json -ErrorAction Stop
        if (-not (Test-ConfigObject -Object $Options)) { $Options = $null }
    } catch {
        $Options = $null
    }
}

if ($null -eq $Options) {
    # ConvertFrom-Yaml/Json unavailable or failed; fall back to Python+PyYAML.
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
    # Self-seed: the agent-context extension owns its lifecycle, so when its
    # own config declares no target it derives one from the active integration
    # recorded in init-options.json, using the extension's OWN bundled mapping
    # (agent-context-defaults.json). Independent of the Specify CLI by design.
    $initOptionsPath = Join-Path $ProjectRoot '.specify/init-options.json'
    if (Test-Path -LiteralPath $initOptionsPath) {
        try {
            $initOpts = Get-Content -LiteralPath $initOptionsPath -Raw | ConvertFrom-Json -ErrorAction Stop
            $integrationKey = $null
            if ($initOpts.PSObject.Properties['integration'] -and $initOpts.integration) {
                $integrationKey = [string]$initOpts.integration
            } elseif ($initOpts.PSObject.Properties['ai'] -and $initOpts.ai) {
                $integrationKey = [string]$initOpts.ai
            }
            if ($integrationKey) {
                $defaultsPath = Join-Path $ProjectRoot '.specify/extensions/agent-context/agent-context-defaults.json'
                if (Test-Path -LiteralPath $defaultsPath) {
                    $defaults = Get-Content -LiteralPath $defaultsPath -Raw | ConvertFrom-Json -ErrorAction Stop
                    $derived = $null
                    if ($defaults.PSObject.Properties['agents'] -and $defaults.agents.PSObject.Properties[$integrationKey]) {
                        $derived = [string]$defaults.agents.PSObject.Properties[$integrationKey].Value
                    }
                    if ($derived -and -not [string]::IsNullOrWhiteSpace($derived)) {
                        $ContextFiles += $derived.Trim()
                    } else {
                        Write-Warning ("agent-context: no default context file is known for integration '{0}'; set 'context_file' in the extension config to choose one." -f $integrationKey)
                    }
                } else {
                    Write-Warning ("agent-context: unable to read {0}; cannot self-seed the context file. Set 'context_file' in the extension config." -f $defaultsPath)
                }
            }
        } catch {
            # Non-fatal: fall through to the nothing-to-do guard below.
        }
    }
}
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
    # Fresh budget per context file: the budget is scoped to one
    # resolution unit, not shared across unrelated paths.
    $script:LinkFollowBudgetRemaining = $script:LinkFollowBudget
    # Resolve the complete link chain before the containment check:
    # a single Resolve-ContextPath pass stops at its depth bound and
    # returns a partially resolved path, so an in-project spelling can
    # pass containment while the later write follows the remaining
    # links outside the project. Re-run until the result stabilizes,
    # like the mtime fallback; a chain that never stabilizes (or
    # leaves the project) is rejected.
    $cmp = if ([System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT) { [System.StringComparison]::OrdinalIgnoreCase } else { [System.StringComparison]::Ordinal }
    $resolvedTarget = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $ContextFile))
    $stabilized = $false
    for ($depth = 0; $depth -lt 10; $depth++) {
        $relPath = ConvertTo-SlashPath -Path $resolvedTarget
        $normRoot = (ConvertTo-SlashPath -Path $ProjectRoot).TrimEnd('/') + '/'
        if (-not $relPath.StartsWith($normRoot, $cmp)) { break }
        $next = Resolve-ContextPath -Root $ProjectRoot -RelativePath $relPath.Substring($normRoot.Length)
        if ($null -eq $next) { break }
        if ([string]::Equals($next, $resolvedTarget, $cmp)) { $stabilized = $true; break }
        $resolvedTarget = $next
    }
    if (-not $stabilized -or $null -eq $resolvedTarget -or -not (Test-IsSubPath -Root $ProjectRoot -Path $resolvedTarget)) {
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
    # Prefer .specify/feature.json (written by /speckit-specify) over mtime heuristic.
    $FeatureJson = Join-Path $ProjectRoot '.specify/feature.json'
    if (Test-Path -LiteralPath $FeatureJson) {
        try {
            $fj = Get-Content -LiteralPath $FeatureJson -Raw -Encoding UTF8 | ConvertFrom-Json
            $featureDir = $fj.feature_directory
            if ($featureDir -isnot [string] -or -not $featureDir) {
                $featureDir = $null
            } else {
                $featureDir = $featureDir.TrimEnd('\', '/')
            }
            if ($featureDir) {
                # Join-Path on Unix does not treat absolute ChildPath as "wins"; check explicitly.
                if ([System.IO.Path]::IsPathRooted($featureDir)) {
                    $candidatePlan = Join-Path $featureDir 'plan.md'
                } else {
                    $candidatePlan = Join-Path (Join-Path $ProjectRoot $featureDir) 'plan.md'
                }
                if (Test-Path -LiteralPath $candidatePlan) {
                    # Resolve ./ .. segments before relativizing (mirrors bash Path.resolve()).
                    # GetFullPath is available in .NET Framework 4.x (PS 5.1 compatible).
                    $resolvedPlan = [System.IO.Path]::GetFullPath($candidatePlan)
                    $resolvedDir  = [System.IO.Path]::GetDirectoryName($resolvedPlan)
                    $normRoot = $ProjectRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
                    $normDir  = $resolvedDir.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
                    $cmp = if ([System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT) { [System.StringComparison]::OrdinalIgnoreCase } else { [System.StringComparison]::Ordinal }
                    if ($normDir.StartsWith($normRoot, $cmp)) {
                        $relDir = $normDir.Substring($normRoot.Length).TrimEnd('\', '/')
                        $PlanPath = if ($relDir) { $relDir.Replace('\', '/') + '/plan.md' } else { 'plan.md' }
                    } else {
                        $PlanPath = $resolvedPlan.Replace('\', '/')
                    }
                }
            }
        } catch {
            # Non-fatal: fall through to mtime heuristic.
        }
    }

    # Fall back to mtime only when feature.json is absent or its plan does not exist yet.
    if (-not $PlanPath) {
        try {
            $specsDir = Join-Path $ProjectRoot 'specs'
            # Recurse (rather than the old one-level specs/*/plan.md scan) so scoped
            # layouts created via SPECIFY_FEATURE_DIRECTORY, e.g.
            # specs/<scope>/<feature>/plan.md, are still discovered when
            # feature.json is absent (#3024).
            # Mirror the bash/python mtime fallback (#5222): follow file links
            # and keep only candidates whose fully resolved target is a
            # regular file inside the project. Resolve the complete link
            # chain and check containment before reporting: a link to a file
            # outside the project must not be reported at its in-project
            # link path. Eligibility is decided from target metadata only:
            # the old probe opened each link, which blocks forever on a
            # Unix named pipe with no writer. Sort by the resolved
            # target's mtime, like p.stat().st_mtime in the twins:
            # GetLastWriteTime follows links on Windows but reports the
            # link's own time on Linux, so call it on the resolved path.
            # Use case-insensitive comparison on Windows only (matches
            # common.ps1 pattern).
            $cmp = if ([System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT) { [System.StringComparison]::OrdinalIgnoreCase } else { [System.StringComparison]::Ordinal }
            $resolvedCandidates = Get-ChildItem -Path $specsDir -Filter 'plan.md' -File -Recurse -ErrorAction SilentlyContinue |
                ForEach-Object {
                    # Fresh budget per candidate: the budget is scoped
                    # to this candidate's recursion and fallback
                    # passes, so a rejected candidate cannot suppress
                    # later ones.
                    $script:LinkFollowBudgetRemaining = $script:LinkFollowBudget
                    $resolved = $_.FullName
                    # Resolve-ContextPath follows link chains up to its
                    # depth bound; re-run until the result stabilizes,
                    # so a chain longer than the bound (or a cycle)
                    # never stabilizes and is rejected below.
                    $stabilized = $false
                    for ($depth = 0; $depth -lt 10; $depth++) {
                        $relPath = ConvertTo-SlashPath -Path $resolved
                        $normRoot = (ConvertTo-SlashPath -Path $ProjectRoot).TrimEnd('/') + '/'
                        if (-not $relPath.StartsWith($normRoot, $cmp)) { break }
                        $next = Resolve-ContextPath -Root $ProjectRoot -RelativePath $relPath.Substring($normRoot.Length)
                        # A null result means the shared link-follow
                        # budget is spent: the chain cannot be resolved,
                        # so the candidate is rejected below.
                        if ($null -eq $next) { break }
                        # Platform-aware equality: PowerShell's -eq is
                        # case-insensitive even on Unix, so a link to a
                        # case-only-differing path would stop the loop
                        # before $resolved is updated.
                        if ([string]::Equals($next, $resolved, $cmp)) { $stabilized = $true; break }
                        $resolved = $next
                    }
                    # Reject candidates whose chain never stabilized
                    # within the pass bound: $resolved may still hold an
                    # unresolved directory link (possibly leading outside
                    # the project), which the lexical containment check
                    # below cannot see.
                    if (-not $stabilized) { return }
                    # Skip candidates that resolve outside the project.
                    if (-not (Test-IsSubPath -Root $ProjectRoot -Path $resolved)) { return }
                    try {
                        if ($resolved.Contains('\') -and [System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
                            # Retrieve metadata for the literal Unix path
                            # before using the provider lookup: Get-Item
                            # normalizes backslashes, so when the
                            # normalized spelling also exists it reports
                            # that entry's type instead of this file's —
                            # a directory at the normalized spelling
                            # would discard a valid regular plan. .NET
                            # preserves Unix filename semantics.
                            $attributes = [System.IO.File]::GetAttributes($resolved)
                            if ($attributes -band [System.IO.FileAttributes]::Directory) { return }
                            if ($attributes -band [System.IO.FileAttributes]::ReparsePoint) { return }
                            # No provider metadata is available here: .NET
                            # reports no Unix file type, and the provider
                            # cannot see the path. The regular-file check
                            # below still applies: test -f stats the
                            # literal path directly. Nothing in the fallback
                            # opens the file, so a special file here is a
                            # wrong plan reference, not a hang.
                            $target = [System.IO.FileInfo]::new($resolved)
                        } else {
                            $target = Get-Item -LiteralPath $resolved -Force -ErrorAction Stop
                        }
                    } catch [System.IO.FileNotFoundException] { return }
                    catch [System.IO.DirectoryNotFoundException] { return }
                    catch [System.Management.Automation.ItemNotFoundException] { return }
                    # Directories (including links to directories) are not plans.
                    if ($target -is [System.IO.DirectoryInfo]) { return }
                    # Still a link: dangling, or a target that could not be
                    # resolved (e.g. through a non-directory).
                    if ($target.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { return }
                    # Special files (named pipe, socket, device): reject from
                    # metadata instead of opening them. `test -f` stats the
                    # resolved target and is true only for a regular file;
                    # it never opens the file, so a named pipe with no
                    # writer cannot hang the update. It is the same check
                    # the bash twin uses, and it is POSIX-identical on
                    # Linux and macOS. UnixMode (pwsh 7+ on Unix) is not
                    # sufficient on its own: the fifo-link tests failed on
                    # macOS CI while passing on Linux. Windows
                    # PowerShell 5.1 has no such files as link targets and
                    # no test command, so the check runs on Unix only; if
                    # test is unavailable, fall back to the UnixMode letter.
                    if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
                        # The resolver drops a trailing '/.' or '/' from a
                        # link target, so a link to 'current.md/.' resolves
                        # to the regular file 'current.md' and would pass
                        # the check below — but opening the link itself fails
                        # on Unix (ENOTDIR), and the bash/Python twins stat
                        # the original candidate and reject it. Stat the
                        # original candidate too, so a broken suffix cannot
                        # displace a valid plan. `test -f` stats through
                        # the link, like the twins' p.stat().
                        $isOriginalRegularFile = $null
                        try {
                            $null = & test -f $_.FullName 2>$null
                            $isOriginalRegularFile = ($LASTEXITCODE -eq 0)
                        } catch {
                            $isOriginalRegularFile = $null
                        }
                        if ($isOriginalRegularFile -eq $false) { return }
                        $isRegularFile = $null
                        try {
                            $null = & test -f $resolved 2>$null
                            $isRegularFile = ($LASTEXITCODE -eq 0)
                        } catch {
                            $isRegularFile = $null
                        }
                        if ($null -eq $isRegularFile) {
                            $unixMode = $target.PSObject.Properties['UnixMode']
                            if ($null -ne $unixMode -and $unixMode.Value -is [string] -and $unixMode.Value.Length -gt 0 -and $unixMode.Value[0] -ne '-') { return }
                        } elseif (-not $isRegularFile) {
                            return
                        }
                    } else {
                        # Windows has no `test` command, and .NET path
                        # handling normalizes a trailing '/.' or '/' away,
                        # so Test-Path and File.Exists cannot see a broken
                        # suffix. Read the candidate's own link target
                        # instead: a target ending in '/.', '/', '\.', or
                        # '\' never denotes a regular file (it is a
                        # directory reference, or invalid when the
                        # preceding component is a file), so the twins
                        # reject it by stat. Reject it here too, so a
                        # broken suffix cannot displace a valid plan.
                        $ownTarget = Get-LinkTarget -Path $_.FullName
                        if ($ownTarget -and (
                            $ownTarget.EndsWith('/.', [System.StringComparison]::Ordinal) -or
                            $ownTarget.EndsWith('/', [System.StringComparison]::Ordinal) -or
                            $ownTarget.EndsWith('\.', [System.StringComparison]::Ordinal) -or
                            $ownTarget.EndsWith('\', [System.StringComparison]::Ordinal)
                        )) { return }
                    }
                    [PSCustomObject]@{
                        ResolvedPath = $resolved
                        Mtime = [System.IO.File]::GetLastWriteTime($resolved)
                    }
                }
            $candidate = $resolvedCandidates | Sort-Object Mtime -Descending | Select-Object -First 1
            if ($candidate) {
                # GetRelativePath is .NET 5+ only; strip prefix manually for PS 5.1 compat.
                $fullPath = ConvertTo-SlashPath -Path $candidate.ResolvedPath
                $normRoot = (ConvertTo-SlashPath -Path $ProjectRoot).TrimEnd('/') + '/'
                if ($fullPath.StartsWith($normRoot, $cmp)) {
                    $PlanPath = $fullPath.Substring($normRoot.Length)
                } else {
                    $PlanPath = $fullPath
                }
            }
        } catch {
            # Non-fatal: continue without a plan path.
        }
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
    if ($ContextFile -match '\.mdc$') {
        $newContent = Add-MdcFrontmatter -Content $newContent
    }
    [System.IO.File]::WriteAllText($CtxPath, $newContent, (New-Object System.Text.UTF8Encoding($false)))

    Write-Host "agent-context: updated $ContextFile"
}
