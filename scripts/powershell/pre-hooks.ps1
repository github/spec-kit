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
        try { $value = ConvertFrom-Json -InputObject $raw -ErrorAction Stop }
        catch { throw "Unsupported YAML escape: $($_.Exception.Message)" }
        if ($value -isnot [string]) { throw "Unsupported YAML scalar" }
        return @{ Value = $value; Quoted = $true }
    }
    $raw = ($raw -replace '\s+#.*$', '').TrimEnd()
    if ($raw -match '^(~|null)$') { $raw = '' }
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
    if ($key -in @('prompt', 'description') -and -not $parsed.Quoted -and $value -match '^(true|false|[0-9]+)$') {
        throw "$key must be a string"
    }
    $Hook[$key] = $value
}

function Test-HookTypedScalar {
    param([string]$Value)
    return $Value -match '^(true|false|yes|no|on|off)$' -or
        $Value -match '^[+-]?(0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|[0-9][0-9_]*(\.[0-9_]*)?([eE][+-]?[0-9]+)?|\.[0-9_]+([eE][+-]?[0-9]+)?|\.([iI][nN][fF]|[nN][aA][nN]))$' -or
        $Value -match '^[0-9]+(:[0-9]+)+$' -or
        $Value -match '^[0-9]{4}-[0-9]{2}-[0-9]{2}([Tt ]|$)'
}

function Get-HookPriority {
    param([string]$Raw)
    if ($Raw -notmatch '^[+-]?[0-9]+(\.[0-9]+)?$') { return 10 }
    $number = 0.0
    if (-not [double]::TryParse($Raw, [Globalization.NumberStyles]::Float,
            [Globalization.CultureInfo]::InvariantCulture, [ref]$number)) { return 10 }
    if ($number -lt 1 -or $number -gt [int]::MaxValue) { return 10 }
    return [int][Math]::Truncate($number)
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
    $hook = $null
    foreach ($line in ($text -split '\r?\n')) {
        if ($line -match '^\s*(#|$)') { continue }
        if ($line.Contains("`t")) { throw "Tabs are not supported in canonical YAML" }
        if ($line -notmatch '^( *)(.*)$') { throw "Unsupported YAML hook layout" }
        $indent = $Matches[1].Length
        $body = $Matches[2]
        if ($indent -eq 0) {
            if ($section -eq 'installed' -and $body -match '^- \S') {
                $null = Convert-HookScalar $body.Substring(2)
                continue
            }
            $target = $false
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
            if ($target) {
                $hook = @{ enabled = 'true'; optional = 'true'; priority = '10' }
                $hooks.Add($hook)
                Add-HookField $hook $body.Substring(2) $Event
            }
            continue
        }
        if ($itemIndent -ge 0 -and $indent -eq $itemIndent + 2) {
            if ($target) { Add-HookField $hook $body $Event }
            continue
        }
        throw "Unsupported YAML hook layout"
    }
    $ordered = [Collections.Generic.List[hashtable]]::new()
    for ($i = 0; $i -lt $hooks.Count; $i++) {
        $hook = $hooks[$i]
        if ($hook.enabled -eq 'false' -or $hook.condition) { continue }
        if (-not $hook.extension -or -not $hook.command) {
            throw "hooks.$Event needs extension and command"
        }
        $ordered.Add(@{
            extension = $hook.extension
            command = $hook.command
            optional = $hook.optional -eq 'true'
            description = if ($hook.description) { $hook.description } else { '' }
            prompt = if ($hook.prompt) { $hook.prompt } else { '' }
            priority = Get-HookPriority $hook.priority
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
