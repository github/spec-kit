#!/usr/bin/env pwsh

. "$PSScriptRoot/pre-hooks.ps1"
Invoke-HookResolver after $args[0]
