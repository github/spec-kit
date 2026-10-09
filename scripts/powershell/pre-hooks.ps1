#!/usr/bin/env pwsh

function Convert-HookScalar {
    param([string]$Raw)
    $raw = $Raw.Trim()
    if ($raw.StartsWith("'")) {
        if ($raw.Length -lt 2 -or -not $raw.EndsWith("'") -or $raw.Substring(1, $raw.Length - 2) -replace "''", "" -match "'") {
            throw "Unsupported YAML scalar"
        }
        return @{ Value = $raw.Substring(1, $raw.Length - 2).Replace("''", "'"); Quoted = $true }
    }
    if ($raw.StartsWith('"')) {
        if ($raw.Length -lt 2 -or -not $raw.EndsWith('"')) { throw "Unsupported YAML scalar" }
        $json = [Text.StringBuilder]::new()
        for ($i = 0; $i -lt $raw.Length; $i++) {
            if ($raw[$i] -ne '\') {
                $null = $json.Append($raw[$i])
                continue
            }
            $i++
            if ($i -ge $raw.Length) { throw "Unsupported YAML escape" }
            $escaped = [string]$raw[$i]
            if ($escaped -ceq 'x' -or $escaped -ceq 'U') {
                $count = if ($escaped -ceq 'x') { 2 } else { 8 }
                if ($i + $count -ge $raw.Length) { throw "Unsupported YAML escape" }
                $hex = $raw.Substring($i + 1, $count)
                if ($hex -notmatch '^[0-9a-fA-F]+$') { throw "Unsupported YAML escape" }
                $number = [Convert]::ToInt32($hex, 16)
                if ($number -eq 0 -or $number -gt 0x10ffff -or
                    ($number -ge 0xd800 -and $number -le 0xdfff)) {
                    throw "Unsupported YAML escape"
                }
                if ($escaped -ceq 'x') {
                    $null = $json.Append('\u00').Append($hex)
                } else {
                    $null = $json.Append([char]::ConvertFromUtf32($number))
                }
                $i += $count
                continue
            }
            $replacement = switch -CaseSensitive ($escaped) {
                'a' { '\u0007' }
                'v' { '\u000B' }
                'e' { '\u001B' }
                'N' { '\u0085' }
                '_' { '\u00A0' }
                'L' { '\u2028' }
                'P' { '\u2029' }
                default { '\' + $escaped }
            }
            $null = $json.Append($replacement)
        }
        try { $value = ConvertFrom-Json -InputObject $json.ToString() -ErrorAction Stop }
        catch { throw "Unsupported YAML escape: $($_.Exception.Message)" }
        if ($value -isnot [string]) { throw "Unsupported YAML scalar" }
        if ($value.Contains([char]0)) { throw "Unsupported YAML NUL character" }
        return @{ Value = $value; Quoted = $true }
    }
    $raw = ($raw -replace '\s+#.*$', '').TrimEnd()
    if ($raw -cmatch '^(~|null|Null|NULL)$') { $raw = '' }
    if ($raw -match '[\[\]{}]|: |^[&*!|>]') { throw "Unsupported YAML scalar" }
    return @{ Value = $raw; Quoted = $false }
}

function Add-HookField {
    param([hashtable]$Hook, [string]$Text, [string]$Event)
    if ($Text -notmatch '^([a-z_]+):(?:\s|$)(.*)$') { throw "Unsupported YAML hook field" }
    $key = $Matches[1]
    $parsed = Convert-HookScalar $Matches[2]
    $value = $parsed.Value
    $typed = -not $parsed.Quoted -and (Test-HookTypedScalar $value)
    if ($key -in @('extension', 'command') -and (-not $value -or $typed)) {
        throw "hooks.$Event needs extension and command"
    }
    if ($key -eq 'condition' -and $typed) {
        throw "condition must be a string or null"
    }
    if ($key -in @('enabled', 'optional') -and ($parsed.Quoted -or $value -notin @('true', 'false'))) {
        throw "$key must be a boolean"
    }
    if ($key -in @('prompt', 'description') -and -not $parsed.Quoted -and
        (Test-HookTypedScalar $value)) {
        throw "$key must be a string"
    }
    $Hook[$key] = $value
    if ($key -eq 'priority') { $Hook.priority_quoted = $parsed.Quoted }
}

function Test-InstalledField {
    param([string]$Text)
    if ($Text -notmatch '^([a-z_]+):(?:\s|$)(.*)$') {
        throw "Unsupported YAML installed entry"
    }
    $raw = $Matches[2]
    if ($raw -match '^(.*["''])\s+#.*$') { $raw = $Matches[1] }
    $null = Convert-HookScalar $raw
}

function Test-HookTypedScalar {
    param([string]$Value)
    return $Value -match '^(true|false|yes|no|on|off)$' -or
        $Value -match '^[+-]?(0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|[0-9][0-9_]*(\.[0-9_]*)?([eE][+-]?[0-9]+)?|\.[0-9_]+([eE][+-]?[0-9]+)?|\.([iI][nN][fF]|[nN][aA][nN]))$' -or
        $Value -match '^[0-9]+(:[0-9]+)+$' -or
        $Value -match '^[0-9]{4}-[0-9]{2}-[0-9]{2}([Tt ]|$)'
}

function Get-HookPriority {
    param([string]$Raw, [bool]$Quoted)
    $digits = $Raw.Replace('_', '')
    if ($Raw -match '^-') { return 10 }
    try {
        if (-not $Quoted -and $Raw -cmatch '^\+?0x[0-9a-fA-F_]+$') {
            $number = [Convert]::ToInt64($digits.TrimStart('+').Substring(2), 16)
        } elseif (-not $Quoted -and $Raw -cmatch '^\+?0b[01_]+$') {
            $number = [Convert]::ToInt64($digits.TrimStart('+').Substring(2), 2)
        } elseif (-not $Quoted -and $Raw -match '^\+?0[0-7_]+$') {
            $number = [Convert]::ToInt64($digits.TrimStart('+'), 8)
        } elseif (-not $Quoted -and $Raw -match '^\+?[1-9][0-9_]*(:[0-5]?[0-9])+$') {
            $number = [long]0
            foreach ($part in ($digits.TrimStart('+') -split ':')) {
                $number = $number * 60 + [long]::Parse($part)
                if ($number -gt [int]::MaxValue) { return 10 }
            }
        } elseif ($Raw -match '^\+?[0-9][0-9_]*$') {
            $number = [long]::Parse($digits.TrimStart('+'), [Globalization.CultureInfo]::InvariantCulture)
        } elseif (-not $Quoted -and $Raw -match '^\+?[0-9][0-9_]*\.[0-9_]*([eE][+-][0-9]+)?$') {
            $number = [double]::Parse(
                $digits, [Globalization.NumberStyles]::Float,
                [Globalization.CultureInfo]::InvariantCulture
            )
        } else {
            return 10
        }
        if ($number -lt 1 -or $number -ge ([double][int]::MaxValue + 1)) { return 10 }
        return [int][Math]::Truncate($number)
    } catch [FormatException], [OverflowException] {
        return 10
    }
}

function Resolve-HookConfig {
    param([string]$Event, [string]$Path)
    $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 -ErrorAction Stop
    if (-not $text.Trim()) { throw "Invalid .specify/extensions.yml: expected a hooks mapping" }
    $hooks = [Collections.Generic.List[hashtable]]::new()
    $inHooks = $false
    $section = ''
    $hooksEmpty = $false
    $seenHooks = $false
    $seenEvent = $false
    $target = $false
    $empty = $false
    $itemIndent = -1
    $installedIndent = -1
    $hook = $null
    foreach ($line in ($text -split '\r?\n')) {
        if ($line -match '^\s*(#|$)') { continue }
        if ($line.Contains("`t")) { throw "Tabs are not supported in canonical YAML" }
        if ($line -notmatch '^( *)(.*)$') { throw "Unsupported YAML hook layout" }
        $indent = $Matches[1].Length
        $body = $Matches[2]
        if ($section -eq 'installed' -and $indent -in @(0, 2) -and $body -match '^- \S') {
            if ($body.Substring(2) -match '^[a-z_]+:(?:\s|$)') {
                $installedIndent = $indent
                Test-InstalledField $body.Substring(2)
            } else {
                $installedIndent = -1
                $null = Convert-HookScalar $body.Substring(2)
            }
            continue
        }
        if ($indent -eq 0) {
            $target = $false
            $installedIndent = -1
            if ($body -in @('hooks:', 'hooks: {}')) {
                if ($seenHooks) { throw "Duplicate hooks mapping" }
                $seenHooks = $true
                $inHooks = $true
                $section = 'hooks'
                $hooksEmpty = $body -eq 'hooks: {}'
            } elseif ($body -match '^hooks:') {
                throw "Invalid .specify/extensions.yml: expected a hooks mapping"
            } elseif ($body -in @('installed:', 'installed: []')) {
                $inHooks = $false
                $section = 'installed'
            } elseif ($body -in @('settings:', 'settings: {}')) {
                $inHooks = $false
                $section = 'settings'
            } else {
                throw "Unsupported YAML top-level layout"
            }
            continue
        }
        if (-not $inHooks) {
            if ($section -eq 'installed' -and $installedIndent -ge 0 -and
                $indent -eq $installedIndent + 2) {
                Test-InstalledField $body
                continue
            }
            if ($section -eq 'settings' -and $indent -eq 2 -and $body -match '^([a-z_]+):(?:\s|$)(.*)$') {
                $null = Convert-HookScalar $Matches[2]
                continue
            }
            throw "Unsupported YAML top-level layout"
        }
        if ($hooksEmpty) { throw "Unsupported YAML hook layout" }
        if ($indent -eq 2 -and $body -match '^([a-z][a-z0-9_]*):(?:\s|$)(.*)$') {
            $key = $Matches[1]
            $value = $Matches[2].Trim()
            $target = $key -eq $Event
            if ($target) {
                if ($seenEvent) { throw "Duplicate hook event" }
                $seenEvent = $true
            }
            if ($value -notin @('', '[]')) { throw "hooks.$key must be a list" }
            $empty = $value -eq '[]'
            $itemIndent = -1
            continue
        }
        if ($indent -in @(2, 4) -and $body.StartsWith('- ') -and -not $empty) {
            $itemIndent = $indent
            $hook = @{ enabled = 'true'; optional = 'true'; priority = '10'; priority_quoted = $false
                       target = $target; hook_event = $key }
            $hooks.Add($hook)
            Add-HookField $hook $body.Substring(2) $Event
            continue
        }
        if ($itemIndent -ge 0 -and $indent -eq $itemIndent + 2) {
            Add-HookField $hook $body $Event
            continue
        }
        throw "Unsupported YAML hook layout"
    }
    $ordered = [Collections.Generic.List[hashtable]]::new()
    for ($i = 0; $i -lt $hooks.Count; $i++) {
        $hook = $hooks[$i]
        if (-not $hook.extension -or -not $hook.command) {
            throw "hooks.$($hook.hook_event) needs extension and command"
        }
        if (-not $hook.target -or $hook.enabled -eq 'false' -or $hook.condition) { continue }
        $ordered.Add(@{
            extension = $hook.extension
            command = $hook.command
            optional = $hook.optional -eq 'true'
            description = if ($hook.description) { $hook.description } else { '' }
            prompt = if ($hook.prompt) { $hook.prompt } else { '' }
            priority = Get-HookPriority $hook.priority $hook.priority_quoted
            index = $i
        })
    }
    $result = @($ordered | Sort-Object priority, index | ForEach-Object {
        @{ extension = $_.extension; command = $_.command; optional = $_.optional
           description = $_.description; prompt = $_.prompt; priority = $_.priority }
    })
    return $result
}

function Invoke-HookResolver {
    param([string]$Phase, [string]$Command)
    $event = "${Phase}_${Command}"
    try {
        if ($event -notmatch '^(before|after)_[a-z][a-z0-9_]*$') {
            throw "Invalid hook event: $event"
        }
        $config = Join-Path (Get-Location) '.specify/extensions.yml'
        $cache = Join-Path (Get-Location) '.specify/hook-dispatch'
        if ((Test-Path -LiteralPath $config -PathType Leaf) -and
            -not (Test-Path -LiteralPath $cache -PathType Container)) {
            $firstLine = Get-Content -LiteralPath $config -TotalCount 1 -Encoding UTF8 -ErrorAction Stop
            if ($firstLine -ceq '# Hook projection: .specify/hook-dispatch') {
                throw "Hook projection is missing; reinstall the extension or refresh the project"
            }
        }
        if (Test-Path -LiteralPath $cache -PathType Container) {
            $snapshot = Join-Path $cache 'source.yml'
            $events = Join-Path $cache 'events.txt'
            if (-not (Test-Path -LiteralPath $config -PathType Leaf) -or
                -not (Test-Path -LiteralPath $snapshot -PathType Leaf) -or
                -not (Test-Path -LiteralPath $events -PathType Leaf)) {
                throw "Hook projection is stale; reinstall the extension or refresh the project"
            }
            $source = [Convert]::ToBase64String([IO.File]::ReadAllBytes($config))
            if ($source -cne [Convert]::ToBase64String([IO.File]::ReadAllBytes($snapshot))) {
                throw "Hook projection is stale; reinstall the extension or refresh the project"
            }
            $indexDigest = Join-Path $cache 'events.txt.sha256'
            if (-not (Test-Path -LiteralPath $indexDigest -PathType Leaf)) {
                throw "Hook projection index is incomplete; reinstall the extension or refresh the project"
            }
            $eventBytes = [IO.File]::ReadAllBytes($events)
            $eventHash = [IO.File]::ReadAllText($indexDigest, [Text.Encoding]::UTF8).Trim()
            if ($eventHash -cnotmatch '^[0-9a-f]{64}$' -or
                [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($eventBytes)) -cne $eventHash.ToUpperInvariant()) {
                throw "Hook projection index is invalid; reinstall the extension or refresh the project"
            }
            $projected = Join-Path $cache "$event.json"
            if (Test-Path -LiteralPath $projected -PathType Leaf) {
                $digest = Join-Path $cache "$event.sha256"
                if (-not (Test-Path -LiteralPath $digest -PathType Leaf)) {
                    throw "Hook projection is incomplete; reinstall the extension or refresh the project"
                }
                $bytes = [IO.File]::ReadAllBytes($projected)
                $expected = [IO.File]::ReadAllText($digest, [Text.Encoding]::UTF8).Trim()
                if ($expected -cnotmatch '^[0-9a-f]{64}$' -or
                    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $expected.ToUpperInvariant()) {
                    throw "Hook projection is invalid; reinstall the extension or refresh the project"
                }
                $text = [Text.Encoding]::UTF8.GetString($bytes)
                try { $data = ConvertFrom-Json -InputObject $text -AsHashtable -ErrorAction Stop }
                catch { throw "Invalid hook projection: $($_.Exception.Message)" }
                if ($data -isnot [Collections.IDictionary] -or $data.event -cne $event -or
                    $data.hooks -isnot [array]) {
                    throw "Invalid hook projection; reinstall the extension or refresh the project"
                }
                foreach ($entry in $data.hooks) {
                    if ($entry -isnot [Collections.IDictionary] -or
                        $entry.extension -isnot [string] -or -not $entry.extension -or
                        $entry.command -isnot [string] -or -not $entry.command -or
                        $entry.optional -isnot [bool] -or
                        $entry.description -isnot [string] -or
                        $entry.prompt -isnot [string] -or
                        $entry.priority -isnot [long] -or $entry.priority -lt 1) {
                        throw "Invalid hook projection; reinstall the extension or refresh the project"
                    }
                }
                $result = $text.TrimEnd("`r", "`n")
            } elseif (@([Text.Encoding]::UTF8.GetString($eventBytes) -split "`n") -ccontains $event) {
                throw "Hook projection is incomplete; reinstall the extension or refresh the project"
            } else {
                $result = @{ event = $event; hooks = @() } | ConvertTo-Json -Depth 5 -Compress
            }
            if ($source -cne [Convert]::ToBase64String([IO.File]::ReadAllBytes($config)) -or
                $source -cne [Convert]::ToBase64String([IO.File]::ReadAllBytes($snapshot))) {
                throw "Hook projection changed during resolution; retry the command"
            }
            [Console]::WriteLine($result)
            exit 0
        }
        $hooks = @()
        if (Test-Path -LiteralPath $config) {
            $hooks = @(Resolve-HookConfig $event $config)
        }
        @{ event = $event; hooks = $hooks } | ConvertTo-Json -Depth 5 -Compress
        exit 0
    } catch {
        @{ event = $event; hooks = @(); error = $_.Exception.Message } |
            ConvertTo-Json -Depth 5 -Compress
        exit 1
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    Invoke-HookResolver before $args[0]
}
