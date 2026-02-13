#!/usr/bin/env pwsh
[CmdletBinding()]
param(
  [switch]$Json,
  [switch]$Help,
  [switch]$NoMetadata,
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = 'Stop'

if ($Help) {
  Write-Host "Usage: ./create-new-ticket.ps1 [-Json] [-NoMetadata] <TICKET-ID>"
  exit 0
}

if (-not $Args -or $Args.Count -lt 1 -or [string]::IsNullOrWhiteSpace($Args[0])) {
  Write-Error "Error: Missing required TICKET-ID argument."
  exit 1
}

$ticketId = $Args[0].Trim()

function Find-RepositoryRoot {
  param(
    [string]$StartDir,
    [string[]]$Markers = @('.git', '.specify')
  )
  $current = Resolve-Path $StartDir
  while ($true) {
    foreach ($marker in $Markers) {
      if (Test-Path (Join-Path $current $marker)) {
        return $current
      }
    }
    $parent = Split-Path $current -Parent
    if ($parent -eq $current) { return $null }
    $current = $parent
  }
}

$repoRoot = Find-RepositoryRoot -StartDir $PSScriptRoot
if (-not $repoRoot) {
  Write-Error "Error: Could not determine repository root."
  exit 1
}

try {
  $gitRoot = git rev-parse --show-toplevel 2>$null
  if ($LASTEXITCODE -eq 0) { $repoRoot = $gitRoot }
} catch {
  # ignore
}

Set-Location $repoRoot

$tasksDir = Join-Path $repoRoot 'tasks'
$ticketDir = Join-Path $tasksDir $ticketId
$referencesDir = Join-Path $ticketDir 'references'
$planningDir = Join-Path $ticketDir 'planning'
$reviewsDir = Join-Path $ticketDir 'reviews'
$stepsDir = Join-Path $planningDir 'steps'

New-Item -ItemType Directory -Path $tasksDir -Force | Out-Null
New-Item -ItemType Directory -Path $ticketDir -Force | Out-Null
New-Item -ItemType Directory -Path $referencesDir -Force | Out-Null
New-Item -ItemType Directory -Path $planningDir -Force | Out-Null
New-Item -ItemType Directory -Path $reviewsDir -Force | Out-Null
New-Item -ItemType Directory -Path $stepsDir -Force | Out-Null

$ticketFile = Join-Path $ticketDir 'ticket.md'
$initialPlan = Join-Path $planningDir 'initial-plan.md'
$whatDone = Join-Path $planningDir 'what-has-been-done.md'
$metadataFile = Join-Path $ticketDir 'metadata.yaml'

$templateDir = Join-Path $repoRoot 'templates/ticket-mode'

function Copy-TemplateIfMissing {
  param(
    [string]$TemplatePath,
    [string]$DestPath,
    [hashtable]$Replacements = @{}
  )

  if (Test-Path $DestPath) { return }

  if (-not (Test-Path $TemplatePath)) {
    New-Item -ItemType File -Path $DestPath -Force | Out-Null
    return
  }

  $content = Get-Content -LiteralPath $TemplatePath -Raw
  foreach ($key in $Replacements.Keys) {
    $content = $content.Replace($key, $Replacements[$key])
  }
  Set-Content -LiteralPath $DestPath -Value $content -Encoding UTF8
}

$repl = @{ '<TICKET-ID>' = $ticketId }

Copy-TemplateIfMissing -TemplatePath (Join-Path $templateDir 'ticket.template.md') -DestPath $ticketFile -Replacements $repl
Copy-TemplateIfMissing -TemplatePath (Join-Path $templateDir 'planning-initial-plan.template.md') -DestPath $initialPlan -Replacements $repl
Copy-TemplateIfMissing -TemplatePath (Join-Path $templateDir 'planning-what-has-been-done.template.md') -DestPath $whatDone -Replacements $repl

if (-not $NoMetadata) {
  Copy-TemplateIfMissing -TemplatePath (Join-Path $templateDir 'metadata.template.yaml') -DestPath $metadataFile -Replacements $repl
}

if ($Json) {
  [PSCustomObject]@{
    TICKET_ID       = $ticketId
    REPO_ROOT       = $repoRoot
    TASKS_DIR       = $tasksDir
    TICKET_DIR      = $ticketDir
    TICKET_FILE     = $ticketFile
    METADATA_FILE   = (Get-Item -LiteralPath $metadataFile -ErrorAction SilentlyContinue)?.FullName
    REFERENCES_DIR  = $referencesDir
    PLANNING_DIR    = $planningDir
    STEPS_DIR       = $stepsDir
    INITIAL_PLAN    = $initialPlan
    WHAT_DONE       = $whatDone
    REVIEWS_DIR     = $reviewsDir
  } | ConvertTo-Json -Compress
} else {
  Write-Output "TICKET_ID: $ticketId"
  Write-Output "TICKET_DIR: $ticketDir"
  Write-Output "TICKET_FILE: $ticketFile"
}
