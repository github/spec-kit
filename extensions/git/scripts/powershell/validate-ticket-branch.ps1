#!/usr/bin/env pwsh

param(
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

try {
    git rev-parse --is-inside-work-tree 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'not a git repository' }
} catch {
    [Console]::Error.WriteLine('ERROR: Git repository not detected. Ticket branch workflow requires an existing git branch.')
    exit 1
}

$branchName = (git rev-parse --abbrev-ref HEAD).Trim()
if ($branchName -eq 'HEAD') {
    [Console]::Error.WriteLine('ERROR: Detached HEAD is not valid for ticket branch workflow.')
    exit 1
}

$ticketKey = ''
$branchPrefix = ''

if ($branchName -match '^([A-Za-z0-9._-]+)/([A-Z]+-[0-9]+)$') {
    $branchPrefix = $Matches[1]
    $ticketKey = $Matches[2]
} elseif ($branchName -match '^([A-Z]+-[0-9]+)$') {
    $ticketKey = $Matches[1]
} else {
    [Console]::Error.WriteLine("ERROR: Current branch '$branchName' is not a valid ticket branch.")
    [Console]::Error.WriteLine('Expected: GDEV-1234, MSPS-1234, feature/GDEV-1234, fix/GDEV-1234, hotfix/GDEV-1234, or chore/GDEV-1234')
    exit 1
}

if ($branchPrefix -and $branchPrefix -notmatch '^(feature|fix|hotfix|chore)$') {
    [Console]::Error.WriteLine("ERROR: Branch prefix '$branchPrefix' is not allowed for ticket branch workflow.")
    [Console]::Error.WriteLine('Allowed prefixes: feature, fix, hotfix, chore')
    exit 1
}

if ($Json) {
    [PSCustomObject]@{
        BRANCH_NAME = $branchName
        TICKET_KEY = $ticketKey
        BRANCH_PREFIX = $branchPrefix
        BRANCH_STRATEGY = 'existing-ticket'
    } | ConvertTo-Json -Compress
} else {
    Write-Output "BRANCH_NAME: $branchName"
    Write-Output "TICKET_KEY: $ticketKey"
    if ($branchPrefix) { Write-Output "BRANCH_PREFIX: $branchPrefix" }
}
