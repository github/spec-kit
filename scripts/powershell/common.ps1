#!/usr/bin/env pwsh
# Common PowerShell functions analogous to common.sh

# Find repository root by searching upward for .specify directory
# This is the primary marker for spec-kit projects
function Find-SpecifyRoot {
    param([string]$StartDir = (Get-Location).Path)

    # Normalize to absolute path to prevent issues with relative paths
    # Use -LiteralPath to handle paths with wildcard characters ([, ], *, ?)
    $resolved = Resolve-Path -LiteralPath $StartDir -ErrorAction SilentlyContinue
    $current = if ($resolved) { $resolved.Path } else { $null }
    if (-not $current) { return $null }

    while ($true) {
        if (Test-Path -LiteralPath (Join-Path $current ".specify") -PathType Container) {
            return $current
        }
        $parent = Split-Path $current -Parent
        if ([string]::IsNullOrEmpty($parent) -or $parent -eq $current) {
            return $null
        }
        $current = $parent
    }
}

# Resolve an explicit SPECIFY_INIT_DIR project override (the directory that
# *contains* .specify/), for non-interactive / CI use -- e.g. running a Spec Kit
# command against a member project from a monorepo root without cd.
#
# Precondition: $env:SPECIFY_INIT_DIR is set. Returns the validated project root,
# or writes an error and exits 1 unless -ReturnNullOnError is set. Strict by
# design: the path must exist and
# contain .specify/, with no silent fallback. (An empty string is falsy, so the
# caller's `if ($env:SPECIFY_INIT_DIR)` guard treats empty as unset.)
#
# This is the single resolver: bundled extensions inherit it by sourcing core
# (e.g. the git extension's create-new-feature-branch) rather than duplicating it.
function Resolve-SpecifyInitDir {
    param([switch]$ReturnNullOnError)

    $initDir = $env:SPECIFY_INIT_DIR
    # Normalize: relative paths resolve against the current directory.
    if (-not [System.IO.Path]::IsPathRooted($initDir)) {
        $initDir = Join-Path (Get-Location).Path $initDir
    }
    $resolved = Resolve-Path -LiteralPath $initDir -ErrorAction SilentlyContinue
    # Resolve-Path also succeeds for files, so check the resolved path is a
    # directory; otherwise a file value would slip through to the less accurate
    # "not a Spec Kit project" error below.
    if (-not $resolved -or -not (Test-Path -LiteralPath $resolved.Path -PathType Container)) {
        [Console]::Error.WriteLine("ERROR: SPECIFY_INIT_DIR does not point to an existing directory: $($env:SPECIFY_INIT_DIR)")
        if ($ReturnNullOnError) { return $null }
        exit 1
    }
    # Resolve-Path echoes back any trailing separator from the input; trim it so
    # the returned root matches the bash resolver, whose `cd && pwd` never yields
    # one. TrimEnd (not [Path]::TrimEndingDirectorySeparator, which is .NET Core
    # only) keeps this working on Windows PowerShell 5.1 / .NET Framework, as
    # Get-FeaturePathsEnv already does below. Unlike a bare TrimEnd, the
    # GetPathRoot check preserves a path that *is* its own root ('C:\' must not
    # become 'C:', which every later API re-resolves against the current
    # directory instead of the drive root). No-op on a path with no trailing
    # separator.
    $initRoot = $resolved.Path.TrimEnd('/', '\')
    if ($initRoot.Length -lt [System.IO.Path]::GetPathRoot($resolved.Path).Length) {
        $initRoot = $resolved.Path
    }
    if (-not (Test-Path -LiteralPath (Join-Path $initRoot '.specify') -PathType Container)) {
        [Console]::Error.WriteLine("ERROR: SPECIFY_INIT_DIR is not a Spec Kit project (no .specify/ directory): $initRoot")
        if ($ReturnNullOnError) { return $null }
        exit 1
    }
    return $initRoot
}

# Get repository root, prioritizing .specify directory
# This prevents using a parent repository when spec-kit is initialized in a subdirectory
function Get-RepoRoot {
    param([switch]$ReturnNullOnError)

    # Explicit project override wins (see Resolve-SpecifyInitDir).
    if ($env:SPECIFY_INIT_DIR) {
        return (Resolve-SpecifyInitDir -ReturnNullOnError:$ReturnNullOnError)
    }

    # First, look for .specify directory (spec-kit's own marker)
    $specifyRoot = Find-SpecifyRoot
    if ($specifyRoot) {
        return $specifyRoot
    }

    # Final fallback to script location
    # Use -LiteralPath to handle paths with wildcard characters
    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "../../..")).Path
}

function Get-CurrentBranch {
    # Return feature name from explicit state only.
    # Feature state is set by SPECIFY_FEATURE (from create-new-feature or
    # the git extension) or implicitly via .specify/feature.json.
    if ($env:SPECIFY_FEATURE) {
        return $env:SPECIFY_FEATURE
    }

    # No explicit feature set - return empty to signal "unknown".
    return ""
}



# Persist a feature_directory value to .specify/feature.json.
# Writes only when the file is missing or the value differs from what's stored.
function Save-FeatureJson {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$FeatureDirectory
    )

    # Strip repo root prefix if the value is absolute and under repo root.
    # Use case-insensitive comparison on Windows only (case-sensitive filesystems elsewhere).
    $prefix = $RepoRoot + [System.IO.Path]::DirectorySeparatorChar
    if ($null -ne $IsWindows) { $onWin = $IsWindows } else { $onWin = $true }
    if ($onWin) {
        $cmp = [System.StringComparison]::OrdinalIgnoreCase
    } else {
        $cmp = [System.StringComparison]::Ordinal
    }
    if ($FeatureDirectory.StartsWith($prefix, $cmp)) {
        $FeatureDirectory = $FeatureDirectory.Substring($prefix.Length)
    }

    $fjPath = Join-Path (Join-Path $RepoRoot '.specify') 'feature.json'

    # Read current value and skip write when unchanged
    if (Test-Path -LiteralPath $fjPath -PathType Leaf) {
        try {
            $raw = Get-Content -LiteralPath $fjPath -Raw
            $cfg = $raw | ConvertFrom-Json
            if ($cfg.feature_directory -eq $FeatureDirectory) {
                return
            }
        } catch {
            # File is corrupt or unreadable - overwrite it
        }
    }

    # Ensure .specify/ directory exists
    $specifyDir = Join-Path $RepoRoot '.specify'
    if (-not (Test-Path -LiteralPath $specifyDir -PathType Container)) {
        New-Item -ItemType Directory -Path $specifyDir -Force | Out-Null
    }

    # Write feature.json
    $json = @{ feature_directory = $FeatureDirectory } | ConvertTo-Json -Compress
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($fjPath, $json, $utf8NoBom)
}

function Get-FeaturePathsEnv {
    # Read-only callers (e.g. check-prerequisites.ps1 -PathsOnly) pass -NoPersist
    # so pure path resolution never writes .specify/feature.json, which would
    # dirty the working tree or overwrite a pinned value (issue #3025).
    param(
        [switch]$NoPersist,
        [switch]$ReturnNullOnError
    )

    $repoRoot = Get-RepoRoot -ReturnNullOnError:$ReturnNullOnError
    if (-not $repoRoot) { return $null }
    $currentBranch = Get-CurrentBranch

    # Resolve feature directory.  Priority:
    #   1. SPECIFY_FEATURE_DIRECTORY env var (explicit override)
    #   2. .specify/feature.json "feature_directory" key (persisted by specify command)
    #   3. Error - no feature context available
    $featureJson = Join-Path $repoRoot '.specify/feature.json'
    if ($env:SPECIFY_FEATURE_DIRECTORY) {
        $featureDir = $env:SPECIFY_FEATURE_DIRECTORY
        # Normalize relative paths to absolute under repo root
        if (-not [System.IO.Path]::IsPathRooted($featureDir)) {
            $featureDir = Join-Path $repoRoot $featureDir
        }
        # Persist to feature.json so future sessions without the env var still
        # work - unless the caller opted out for read-only resolution (#3025).
        if (-not $NoPersist) {
            Save-FeatureJson -RepoRoot $repoRoot -FeatureDirectory $env:SPECIFY_FEATURE_DIRECTORY
        }
    } elseif (Test-Path $featureJson) {
        $featureJsonRaw = Get-Content -LiteralPath $featureJson -Raw
        try {
            $featureConfig = $featureJsonRaw | ConvertFrom-Json
        } catch {
            [Console]::Error.WriteLine("ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY or ensure .specify/feature.json contains feature_directory.")
            if ($ReturnNullOnError) { return $null }
            exit 1
        }
        if ($featureConfig.feature_directory) {
            $featureDir = $featureConfig.feature_directory
            # Normalize relative paths to absolute under repo root
            if (-not [System.IO.Path]::IsPathRooted($featureDir)) {
                $featureDir = Join-Path $repoRoot $featureDir
            }
        } else {
            [Console]::Error.WriteLine("ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY or ensure .specify/feature.json contains feature_directory.")
            if ($ReturnNullOnError) { return $null }
            exit 1
        }
    } else {
        [Console]::Error.WriteLine("ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY or run the specify command to create .specify/feature.json.")
        if ($ReturnNullOnError) { return $null }
        exit 1
    }

    # When no branch context exists (no SPECIFY_FEATURE, feature resolved via
    # SPECIFY_FEATURE_DIRECTORY or feature.json), fall back to the feature
    # directory basename so CURRENT_BRANCH is a usable identifier rather than
    # an empty, misleading value (issue #3026).
    if (-not $currentBranch) {
        # TrimEnd (not [Path]::TrimEndingDirectorySeparator, which is .NET Core
        # only) keeps this working on Windows PowerShell 5.1 / .NET Framework.
        $featureDirTrimmed = $featureDir.TrimEnd('/', '\')
        $currentBranch = Split-Path -Leaf $featureDirTrimmed
    }

    [PSCustomObject]@{
        REPO_ROOT     = $repoRoot
        CURRENT_BRANCH = $currentBranch
        FEATURE_DIR   = $featureDir
        FEATURE_SPEC  = Join-Path $featureDir 'spec.md'
        IMPL_PLAN     = Join-Path $featureDir 'plan.md'
        TASKS         = Join-Path $featureDir 'tasks.md'
        RESEARCH      = Join-Path $featureDir 'research.md'
        DATA_MODEL    = Join-Path $featureDir 'data-model.md'
        QUICKSTART    = Join-Path $featureDir 'quickstart.md'
        CONTRACTS_DIR = Join-Path $featureDir 'contracts'
    }
}

function Test-FileExists {
    param([string]$Path, [string]$Description)
    if (Test-Path -Path $Path -PathType Leaf) {
        Write-Output "  [OK] $Description"
        return $true
    } else {
        Write-Output "  [FAIL] $Description"
        return $false
    }
}

function Test-DirHasFiles {
    param([string]$Path, [string]$Description)
    # A directory counts as non-empty when Get-ChildItem returns any entry
    # (files or subdirectories) -- matching the JSON contracts checks in
    # check-prerequisites.ps1 / setup-tasks.ps1, and treating a directory whose
    # only contents are subdirectories (e.g. contracts/v1/openapi.yaml) as
    # non-empty like bash check_dir. Filtering out subdirectories would
    # mis-report such a directory as empty.
    if ((Test-Path -Path $Path -PathType Container) -and (Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Select-Object -First 1)) {
        Write-Output "  [OK] $Description"
        return $true
    } else {
        Write-Output "  [FAIL] $Description"
        return $false
    }
}

function Get-InvokeSeparator {
    param([string]$RepoRoot = (Get-RepoRoot))

    if ($null -eq $script:SpecKitInvokeSeparatorCache) {
        $script:SpecKitInvokeSeparatorCache = @{}
    }
    if ($script:SpecKitInvokeSeparatorCache.ContainsKey($RepoRoot)) {
        return $script:SpecKitInvokeSeparatorCache[$RepoRoot]
    }

    $separator = '.'
    $integrationJson = Join-Path $RepoRoot '.specify/integration.json'
    if (Test-Path -LiteralPath $integrationJson -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $integrationJson -Raw | ConvertFrom-Json
            $key = if ($state.default_integration) { [string]$state.default_integration } elseif ($state.integration) { [string]$state.integration } else { '' }
            if ($key -and $state.integration_settings) {
                $settingProperty = $state.integration_settings.PSObject.Properties[$key]
                if ($settingProperty) {
                    $setting = $settingProperty.Value
                    if ($setting -and ($setting.invoke_separator -eq '.' -or $setting.invoke_separator -eq '-')) {
                        $separator = [string]$setting.invoke_separator
                    }
                }
            }
        } catch {
            $separator = '.'
        }
    }

    $script:SpecKitInvokeSeparatorCache[$RepoRoot] = $separator
    return $separator
}

function Format-SpecKitCommand {
    param(
        [Parameter(Mandatory = $true)][string]$CommandName,
        [string]$RepoRoot = (Get-RepoRoot)
    )

    $separator = Get-InvokeSeparator -RepoRoot $RepoRoot
    $name = $CommandName.TrimStart('/')
    if ($name.StartsWith('speckit.')) {
        $name = $name.Substring(8)
    } elseif ($name.StartsWith('speckit-')) {
        $name = $name.Substring(8)
    }
    $name = $name -replace '\.', $separator

    return "/speckit$separator$name"
}

# Find a usable Python 3 executable (python3, python, or py -3).
# Returns the command/arguments as an array, or $null if none found.
function Get-Python3Command {
    if (Get-Command python3 -ErrorAction SilentlyContinue) { return @('python3') }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $ver = & python --version 2>&1
        if ($ver -match 'Python 3') { return @('python') }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $ver = & py -3 --version 2>&1
        if ($ver -match 'Python 3') { return @('py', '-3') }
    }
    return $null
}

function Get-NormalizedPriority {
    param($Value)

    if ($Value -is [bool]) { return 10 }
    if ($Value -is [string]) {
        $integerText = $Value.Trim()
        if ($integerText -cnotmatch '^[+-]?[0-9]+(?:_[0-9]+)*$') { return 10 }
        $Value = $integerText.Replace('_', '')
    }
    try {
        $parsedPriority = [System.Numerics.BigInteger]$Value
    } catch {
        return 10
    }
    return $(if ($parsedPriority -ge 1) { $parsedPriority } else { 10 })
}

function Get-SortedExtensionIds {
    param([Parameter(Mandatory=$true)][string]$ExtensionsDir)

    $registeredNames = @()
    $ranked = @()
    $registryFile = Join-Path $ExtensionsDir '.registry'
    # Detect any filesystem entry at the registry path without following symlinks.
    # Test-Path follows links and reports $false for a dangling symlink, so a
    # broken .registry symlink would otherwise bypass this guard and let the
    # directory scan below enable every on-disk extension. Enumerating the parent
    # directory still observes a broken symlink as an entry.
    $registryEntry = Get-ChildItem -LiteralPath $ExtensionsDir -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq '.registry' } |
        Select-Object -First 1
    if ($registryEntry) {
        if (-not (Test-Path -LiteralPath $registryFile -PathType Leaf)) {
            throw "Invalid extension registry ${registryFile}: not a regular file"
        }
        try {
            $data = [System.IO.File]::ReadAllText($registryFile, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
        } catch {
            throw "Invalid extension registry ${registryFile}: $($_.Exception.Message)"
        }
        if ($null -eq $data -or $data -isnot [PSCustomObject]) {
            throw "Invalid extension registry ${registryFile}: root must be a mapping"
        }
        $extensionsProperty = $data.PSObject.Properties['extensions']
        if ($extensionsProperty) {
            if ($extensionsProperty.Value -isnot [PSCustomObject]) {
                throw "Invalid extension registry ${registryFile}: 'extensions' must be a mapping"
            }
            $extensions = $extensionsProperty.Value
        } else {
            $extensions = [PSCustomObject]@{}
        }
        $registeredNames = @($extensions.PSObject.Properties | ForEach-Object { $_.Name })
        foreach ($entry in $extensions.PSObject.Properties) {
            if ($entry.Name -cnotmatch '^[a-z0-9-]+$' -or $entry.Value -isnot [PSCustomObject]) {
                continue
            }
            $enabledProperty = $entry.Value.PSObject.Properties['enabled']
            if ($enabledProperty -and -not [bool]$enabledProperty.Value) { continue }
            $priority = 10
            $priorityProperty = $entry.Value.PSObject.Properties['priority']
            if ($priorityProperty) {
                $priority = Get-NormalizedPriority -Value $priorityProperty.Value
            }
            $ranked += [PSCustomObject]@{ Priority = $priority; Id = $entry.Name }
        }
    }

    foreach ($directory in Get-ChildItem -Path $ExtensionsDir -Directory -ErrorAction SilentlyContinue) {
        if ($directory.Name -cmatch '^[a-z0-9-]+$' -and $directory.Name -cnotin $registeredNames) {
            $ranked += [PSCustomObject]@{ Priority = 10; Id = $directory.Name }
        }
    }
    return $ranked | Sort-Object Priority, Id | ForEach-Object { $_.Id }
}

# Resolve a template name to a file path using the priority stack:
#   1. .specify/templates/overrides/
#   2. .specify/presets/<preset-id>/templates/ (sorted by priority from .registry)
#   3. .specify/extensions/<ext-id>/templates/
#   4. .specify/templates/ (core)
function Resolve-Template {
    param(
        [Parameter(Mandatory=$true)][string]$TemplateName,
        [Parameter(Mandatory=$true)][string]$RepoRoot
    )

    if ($TemplateName -cnotmatch '^[a-z0-9-]+$') { return $null }

    $base = Join-Path $RepoRoot '.specify/templates'

    # Priority 1: Project overrides
    $override = Join-Path $base "overrides/$TemplateName.md"
    if (Test-Path $override) { return $override }

    # Priority 2: Installed presets (sorted by priority from .registry)
    $presetsDir = Join-Path $RepoRoot '.specify/presets'
    if (Test-Path $presetsDir) {
        $registryFile = Join-Path $presetsDir '.registry'
        $sortedPresets = @()
        $registryParsed = $false
        if (Test-Path $registryFile) {
            try {
                $registryData = [System.IO.File]::ReadAllText($registryFile, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
                if ($null -eq $registryData -or $registryData -isnot [PSCustomObject]) {
                    throw 'Registry root must be an object'
                }
                $presetsProperty = $registryData.PSObject.Properties['presets']
                if ($presetsProperty) {
                    $presets = $presetsProperty.Value
                    if ($null -eq $presets -or $presets -isnot [PSCustomObject]) {
                        throw 'Registry presets must be an object'
                    }
                    $presetEntries = @($presets.PSObject.Properties)
                    $priorityFor = {
                        param($Entry)
                        if ($Entry.Value -is [PSCustomObject]) {
                            $priorityProperty = $Entry.Value.PSObject.Properties['priority']
                            if ($priorityProperty) {
                                return Get-NormalizedPriority -Value $priorityProperty.Value
                            }
                        }
                        return 10
                    }
                    $sortedPresets = $presetEntries |
                        Where-Object { $_.Value -is [PSCustomObject] } |
                        Where-Object {
                            $enabled = $_.Value.PSObject.Properties['enabled']
                            -not $enabled -or [bool]$enabled.Value
                        } |
                        Where-Object { $_.Name -cmatch '^[a-z0-9-]+$' } |
                        Sort-Object @{ Expression = { & $priorityFor $_ } }, @{ Expression = { $_.Name } } |
                        ForEach-Object { $_.Name }
                }
                $registryParsed = $true
            } catch {
                $registryParsed = $false
            }
        }

        if ($registryParsed) {
            foreach ($presetId in $sortedPresets) {
                $candidate = Join-Path $presetsDir "$presetId/templates/$TemplateName.md"
                if (Test-Path $candidate) { return $candidate }
                $candidate = Join-Path $presetsDir "$presetId/$TemplateName.md"
                if (Test-Path $candidate) { return $candidate }
            }
        } else {
            # Fallback: alphabetical directory order
            foreach ($preset in Get-ChildItem -Path $presetsDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike '.*' } | Sort-Object Name) {
                $candidate = Join-Path $preset.FullName "templates/$TemplateName.md"
                if (Test-Path $candidate) { return $candidate }
                $candidate = Join-Path $preset.FullName "$TemplateName.md"
                if (Test-Path $candidate) { return $candidate }
            }
        }
    }

    # Priority 3: Extension-provided templates
    $extDir = Join-Path $RepoRoot '.specify/extensions'
    if (Test-Path $extDir) {
        foreach ($extensionId in Get-SortedExtensionIds -ExtensionsDir $extDir) {
            $candidate = Join-Path $extDir "$extensionId/templates/$TemplateName.md"
            if (-not (Test-Path $candidate)) {
                $candidate = Join-Path $extDir "$extensionId/$TemplateName.md"
            }
            if (Test-Path $candidate) { return $candidate }
        }
    }

    # Priority 4: Core templates
    $core = Join-Path $base "$TemplateName.md"
    if (Test-Path $core) { return $core }

    return $null
}

# Resolve a template name to composed content using composition strategies.
# Reads strategy metadata from preset manifests and composes content
# from multiple layers using prepend, append, or wrap strategies.
function Resolve-TemplateContent {
    param(
        [Parameter(Mandatory=$true)][string]$TemplateName,
        [Parameter(Mandatory=$true)][string]$RepoRoot
    )

    if ($TemplateName -cnotmatch '^[a-z0-9-]+$') {
        return $null
    }

    $base = Join-Path $RepoRoot '.specify/templates'

    # Collect all layers (highest priority first)
    $layerPaths = @()
    $layerStrategies = @()

    # Priority 1: Project overrides (always "replace")
    $override = Join-Path $base "overrides/$TemplateName.md"
    if (Test-Path $override) {
        return [System.IO.File]::ReadAllText(
            $override,
            [System.Text.Encoding]::UTF8
        )
    }

    $effectiveBaseFound = $false

    # Priority 2: Installed presets (sorted by priority from .registry)
    $presetsDir = Join-Path $RepoRoot '.specify/presets'
    if (Test-Path $presetsDir) {
        $registryFile = Join-Path $presetsDir '.registry'
        $sortedPresets = @()
        $registryParsed = $false
        if (Test-Path $registryFile) {
            try {
                $registryData = [System.IO.File]::ReadAllText($registryFile, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
                if ($null -eq $registryData -or $registryData -isnot [PSCustomObject]) {
                    throw 'Registry root must be an object'
                }
                $presetsProperty = $registryData.PSObject.Properties['presets']
                if ($presetsProperty) {
                    $presets = $presetsProperty.Value
                    if ($null -eq $presets -or $presets -isnot [PSCustomObject]) {
                        throw 'Registry presets must be an object'
                    }
                    $presetEntries = @($presets.PSObject.Properties)
                    $priorityFor = {
                        param($Entry)
                        if ($Entry.Value -is [PSCustomObject]) {
                            $priorityProperty = $Entry.Value.PSObject.Properties['priority']
                            if ($priorityProperty) {
                                return Get-NormalizedPriority -Value $priorityProperty.Value
                            }
                        }
                        return 10
                    }
                    $sortedPresets = $presetEntries |
                        Where-Object { $_.Value -is [PSCustomObject] } |
                        Where-Object {
                            $enabled = $_.Value.PSObject.Properties['enabled']
                            -not $enabled -or [bool]$enabled.Value
                        } |
                        Where-Object { $_.Name -cmatch '^[a-z0-9-]+$' } |
                        Sort-Object @{ Expression = { & $priorityFor $_ } }, @{ Expression = { $_.Name } } |
                        ForEach-Object { $_.Name }
                }
                $registryParsed = $true
            } catch {
                $registryParsed = $false
            }
        }

        if (-not $registryParsed) {
            $sortedPresets = Get-ChildItem -Path $presetsDir -Directory -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -cmatch '^[a-z0-9-]+$' } |
                Sort-Object Name |
                ForEach-Object { $_.Name }
        }

        $pyCmd = @(Get-Python3Command)
        foreach ($presetId in $sortedPresets) {
                # Read strategy and file path from preset manifest
                $strategy = 'replace'
                $manifestFilePath = ''
                $manifestDeclared = $false
                $manifest = Join-Path $presetsDir "$presetId/preset.yml"
                if ((Test-Path $manifest) -and -not $pyCmd) {
                    throw "Python 3 and PyYAML are required to resolve preset template composition"
                }
                if (Test-Path $manifest) {
                    try {
                        # Use Python to parse YAML manifest for strategy and file path
                        $pyArgs = if ($pyCmd.Count -gt 1) { $pyCmd[1..($pyCmd.Count-1)] } else { @() }
                        $pyStderrFile = [System.IO.Path]::GetTempFileName()
                        $stratResult = & $pyCmd[0] @pyArgs -c @"
import sys
try:
    import yaml
except ImportError:
    print('yaml_missing', file=sys.stderr)
    sys.exit(2)
try:
    with open(sys.argv[1], encoding='utf-8') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError('manifest root must be a mapping')
    if 'provides' not in data:
        raise ValueError('manifest missing provides section')
    provides = data['provides']
    if not isinstance(provides, dict):
        raise ValueError('manifest provides must be a mapping')
    if 'templates' not in provides:
        raise ValueError('manifest provides missing templates')
    templates = provides['templates']
    if not isinstance(templates, list):
        raise ValueError('manifest templates must be a list')
    if not templates:
        raise ValueError('manifest must provide at least one template')
    valid_types = ('template', 'command', 'script')
    valid_strategies = ('replace', 'prepend', 'append', 'wrap')
    for t in templates:
        if not isinstance(t, dict):
            raise ValueError('manifest template entries must be mappings')
        if 'type' not in t or 'name' not in t or 'file' not in t:
            raise ValueError('manifest template entry missing type, name, or file')
        for field in ('type', 'name', 'file'):
            if not isinstance(t[field], str):
                raise ValueError('manifest template ' + field + ' must be a string')
        if t['type'] not in valid_types:
            raise ValueError('invalid manifest template type')
        strategy = t.get('strategy', 'replace')
        if not isinstance(strategy, str):
            raise ValueError('manifest template strategy must be a string')
        strategy = strategy.lower()
        if strategy not in valid_strategies:
            raise ValueError('invalid manifest template strategy')
        if t['type'] == 'script' and strategy not in ('replace', 'wrap'):
            raise ValueError('invalid manifest script strategy')
    for t in templates:
        if t.get('name') == sys.argv[2] and t.get('type', 'template') == 'template':
            file_value = t.get('file', '')
            strategy = t.get('strategy', 'replace')
            print('found\t' + strategy + '\t' + file_value)
            sys.exit(0)
    print('absent\treplace\t')
except Exception as exc:
    print(f'manifest_invalid: {exc}', file=sys.stderr)
    sys.exit(3)
"@ $manifest $TemplateName 2>$pyStderrFile
                        if ($LASTEXITCODE -ne 0) {
                            if ($LASTEXITCODE -eq 2) {
                                throw "PyYAML is required to resolve preset template composition"
                            }
                            throw "Invalid preset manifest $manifest"
        }
                        if ($stratResult) {
                            $parts = $stratResult.Trim() -split "`t", 3
                            $manifestDeclared = $parts[0] -eq 'found'
                            $strategy = $parts[1].ToLowerInvariant()
                            if ($parts.Count -gt 2 -and $parts[2]) { $manifestFilePath = $parts[2] }
                        }
                        Remove-Item $pyStderrFile -Force -ErrorAction SilentlyContinue
                    } catch {
                        if ($pyStderrFile) { Remove-Item $pyStderrFile -Force -ErrorAction SilentlyContinue }
                        throw
                    }
                }
                # Try manifest file path first, then convention path
                $candidate = $null
                if ($manifestFilePath) {
                    # Reject absolute paths and parent traversal
                    if ([System.IO.Path]::IsPathRooted($manifestFilePath) -or $manifestFilePath -match '\.\.[\\/]') {
                        $manifestFilePath = ''
                    }
                }
                if ($manifestFilePath) {
                    $mf = Join-Path $presetsDir "$presetId/$manifestFilePath"
                    if (Test-Path $mf) { $candidate = $mf }
                }
                if (-not $candidate -and -not $manifestDeclared) {
                    $cf = Join-Path $presetsDir "$presetId/templates/$TemplateName.md"
                    if (Test-Path $cf) { $candidate = $cf }
                    if (-not $candidate) {
                        $cf = Join-Path $presetsDir "$presetId/$TemplateName.md"
                        if (Test-Path $cf) { $candidate = $cf }
                    }
                }
                if ($candidate) {
                    $layerPaths += $candidate
                    $layerStrategies += $strategy
                    if ($strategy -eq 'replace') {
                        $effectiveBaseFound = $true
                        break
                    }
                }
            }
    }

    # Priority 3: Extension-provided templates (always "replace")
    $extDir = Join-Path $RepoRoot '.specify/extensions'
    if (-not $effectiveBaseFound -and (Test-Path $extDir)) {
        foreach ($extensionId in Get-SortedExtensionIds -ExtensionsDir $extDir) {
            $candidate = Join-Path $extDir "$extensionId/templates/$TemplateName.md"
            if (-not (Test-Path $candidate)) {
                $candidate = Join-Path $extDir "$extensionId/$TemplateName.md"
            }
            if (Test-Path $candidate) {
                $layerPaths += $candidate
                $layerStrategies += 'replace'
                $effectiveBaseFound = $true
                break
            }
        }
    }

    # Priority 4: Core templates (always "replace")
    $core = Join-Path $base "$TemplateName.md"
    if (-not $effectiveBaseFound -and (Test-Path $core)) {
        $layerPaths += $core
        $layerStrategies += 'replace'
    }

    if ($layerPaths.Count -eq 0) { return $null }

    # If the top (highest-priority) layer is replace, it wins entirely --
    # lower layers are irrelevant regardless of their strategies.
    if ($layerStrategies[0] -eq 'replace') {
        return [System.IO.File]::ReadAllText($layerPaths[0], [System.Text.Encoding]::UTF8)
    }

    # Check if any layer uses a non-replace strategy
    $hasComposition = $false
    foreach ($s in $layerStrategies) {
        if ($s -ne 'replace') { $hasComposition = $true; break }
    }

    if (-not $hasComposition) {
        return [System.IO.File]::ReadAllText($layerPaths[0], [System.Text.Encoding]::UTF8)
    }

    # Find the effective base: scan from highest priority (index 0) downward
    # to find the nearest replace layer. Only compose layers above that base.
    $baseIdx = -1
    for ($i = 0; $i -lt $layerPaths.Count; $i++) {
        if ($layerStrategies[$i] -eq 'replace') {
            $baseIdx = $i
            break
        }
    }
    if ($baseIdx -lt 0) {
        throw "Template '$TemplateName' has composing layers but no replace base"
    }

    $content = [System.IO.File]::ReadAllText(
        $layerPaths[$baseIdx],
        [System.Text.Encoding]::UTF8
    )

    for ($i = $baseIdx - 1; $i -ge 0; $i--) {
        $path = $layerPaths[$i]
        $strat = $layerStrategies[$i]
        $layerContent = [System.IO.File]::ReadAllText(
            $path,
            [System.Text.Encoding]::UTF8
        )

        switch ($strat) {
            'replace' { $content = $layerContent }
            'prepend' { $content = "$layerContent`n`n$content" }
            'append'  { $content = "$content`n`n$layerContent" }
            'wrap'    {
                if (-not $layerContent.Contains('{CORE_TEMPLATE}')) {
                    throw "Wrap strategy missing {CORE_TEMPLATE} placeholder"
                }
                $content = $layerContent.Replace('{CORE_TEMPLATE}', $content)
            }
            default { throw "Unknown strategy: $strat" }
        }
    }

    return $content
}
