#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output "Usage: ./validate-arch-artifacts.ps1 [-Json] [-Help]"
    Write-Output "  -Json     Output readiness result as JSON"
    Write-Output "  -Help     Show this help message"
    exit 0
}

function Find-SpecifyRoot {
    param([string]$StartDir = (Get-Location).Path)

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

function Get-RepoRoot {
    $specifyRoot = Find-SpecifyRoot
    if ($specifyRoot) {
        return $specifyRoot
    }

    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
    }

    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "../../../../..")).Path
}

function Convert-ToPlainPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if ($Path -like 'Microsoft.PowerShell.Core\FileSystem::*') {
        return $Path.Substring('Microsoft.PowerShell.Core\FileSystem::'.Length)
    }
    return $Path
}

function Add-Blocker {
    param(
        [Parameter(Mandatory = $true)][string]$Code,
        [Parameter(Mandatory = $true)][string]$Artifact,
        [string]$SectionId = "",
        [Parameter(Mandatory = $true)][string]$Message
    )

    $script:blockers += [PSCustomObject]@{
        code = $Code
        artifact = $Artifact
        sectionId = $SectionId
        message = $Message
    }
}

function Test-SectionExists {
    param(
        [AllowEmptyCollection()][AllowEmptyString()][string[]]$Lines,
        [Parameter(Mandatory = $true)][string]$Heading
    )

    $pattern = '^##\s+' + [regex]::Escape($Heading) + '\s*$'
    return [bool]($Lines | Where-Object { $_ -match $pattern } | Select-Object -First 1)
}

function Test-SectionHasContent {
    param(
        [AllowEmptyCollection()][AllowEmptyString()][string[]]$Lines,
        [Parameter(Mandatory = $true)][string]$Heading
    )

    $pattern = '^##\s+' + [regex]::Escape($Heading) + '\s*$'
    $inSection = $false
    foreach ($line in $Lines) {
        if ($line -match $pattern) {
            $inSection = $true
            continue
        }
        if ($inSection -and $line -match '^##\s+') {
            break
        }
        if (-not $inSection) {
            continue
        }

        $trimmed = $line.Trim()
        if (-not $trimmed) { continue }
        if ($trimmed -match 'NEEDS ARCH UPDATE|NEEDS REPO FACTS UPDATE') { continue }
        if ($trimmed -match '^[-|:\s]+$') { continue }
        if ($trimmed -match '^\|\s*[-:]') { continue }
        return $true
    }

    return $false
}

$repoRoot = Convert-ToPlainPath (Get-RepoRoot)
$archDir = Join-Path $repoRoot ".specify/memory"
$blockers = @()

$files = [ordered]@{
    "architecture-synthesis" = Join-Path $archDir "architecture.md"
    "scenario-view" = Join-Path $archDir "architecture-scenario-view.md"
    "logical-view" = Join-Path $archDir "architecture-logical-view.md"
    "process-view" = Join-Path $archDir "architecture-process-view.md"
    "development-view" = Join-Path $archDir "architecture-development-view.md"
    "physical-view" = Join-Path $archDir "architecture-physical-view.md"
}

$sectionHeadings = @{
    "view-index" = "View Index"
    "architecture-intent" = "Architecture Intent"
    "central-design-forces" = "Central Design Forces"
    "primary-tradeoffs" = "Primary Tradeoffs"
    "stable-boundaries" = "Stable Boundaries"
    "change-axes" = "Change Axes"
    "anti-patterns" = "Anti-patterns"
    "cross-view-architecture-model" = "Cross-View Architecture Model"
    "key-architecture-conclusions" = "Key Architecture Conclusions"
    "cross-cutting-constraints" = "Cross-Cutting Constraints"
    "open-risks-and-review-triggers" = "Open Risks and Review Triggers"
    "core-tensions" = "Core Tensions"
    "invariants" = "Invariants"
    "non-goals-anti-patterns" = "Non-goals / Anti-patterns"
    "actors-and-participants" = "Actors and Participants"
    "use-cases" = "Use Cases"
    "scenario-paths" = "Scenario Paths"
    "acceptance-semantics" = "Acceptance Semantics"
    "source-traceability" = "Source Traceability"
    "scenario-gaps" = "Scenario Gaps"
    "capability-boundaries" = "Capability Boundaries"
    "domain-objects-and-relationships" = "Domain Objects and Relationships"
    "state-and-lifecycle" = "State and Lifecycle"
    "logical-decisions" = "Logical Decisions"
    "logical-gaps" = "Logical Gaps"
    "main-runtime-links" = "Main Runtime Links"
    "handoffs-and-approvals" = "Handoffs and Approvals"
    "receipts-and-user-participation" = "Receipts and User Participation"
    "failure-degradation-and-closure" = "Failure, Degradation, and Closure"
    "process-gaps" = "Process Gaps"
    "architecture-level-components" = "Architecture-Level Components"
    "package-boundary-intent" = "Package Boundary Intent"
    "contracts-and-artifacts" = "Contracts and Artifacts"
    "dependency-rules" = "Dependency Rules"
    "dependency-matrix" = "Dependency Matrix"
    "development-view-gaps" = "Development View Gaps"
    "deployment-and-hosting-boundaries" = "Deployment and Hosting Boundaries"
    "external-system-collaboration" = "External System Collaboration"
    "fact-sources-and-observability" = "Fact Sources and Observability"
    "operations-and-release-boundaries" = "Operations and Release Boundaries"
    "physical-view-gaps" = "Physical View Gaps"
}

$requiredSections = @{
    "architecture-synthesis" = @("view-index", "architecture-intent", "central-design-forces", "primary-tradeoffs", "stable-boundaries", "change-axes", "anti-patterns", "cross-view-architecture-model", "key-architecture-conclusions", "cross-cutting-constraints", "open-risks-and-review-triggers")
    "scenario-view" = @("architecture-intent", "core-tensions", "stable-boundaries", "change-axes", "invariants", "non-goals-anti-patterns", "actors-and-participants", "use-cases", "scenario-paths", "acceptance-semantics", "source-traceability", "scenario-gaps")
    "logical-view" = @("architecture-intent", "core-tensions", "stable-boundaries", "change-axes", "invariants", "non-goals-anti-patterns", "capability-boundaries", "domain-objects-and-relationships", "state-and-lifecycle", "logical-decisions", "source-traceability", "logical-gaps")
    "process-view" = @("architecture-intent", "core-tensions", "stable-boundaries", "change-axes", "invariants", "non-goals-anti-patterns", "main-runtime-links", "handoffs-and-approvals", "receipts-and-user-participation", "failure-degradation-and-closure", "source-traceability", "process-gaps")
    "development-view" = @("architecture-intent", "core-tensions", "stable-boundaries", "change-axes", "invariants", "non-goals-anti-patterns", "architecture-level-components", "package-boundary-intent", "contracts-and-artifacts", "dependency-rules", "dependency-matrix", "source-traceability", "development-view-gaps")
    "physical-view" = @("architecture-intent", "core-tensions", "stable-boundaries", "change-axes", "invariants", "non-goals-anti-patterns", "deployment-and-hosting-boundaries", "external-system-collaboration", "fact-sources-and-observability", "operations-and-release-boundaries", "source-traceability", "physical-view-gaps")
}

foreach ($artifact in $files.Keys) {
    $file = $files[$artifact]
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        Add-Blocker -Code "ARCH_ARTIFACT_MISSING" -Artifact $artifact -Message "Required architecture artifact is missing: $file"
        continue
    }

    $lines = Get-Content -LiteralPath $file
    $content = $lines -join "`n"
    if ($content -match 'NEEDS ARCH UPDATE|NEEDS REPO FACTS UPDATE') {
        Add-Blocker -Code "ARCH_PLACEHOLDER_PRESENT" -Artifact $artifact -Message "Artifact still contains placeholder update markers."
    }

    foreach ($section in $requiredSections[$artifact]) {
        $heading = $sectionHeadings[$section]
        if (-not (Test-SectionExists -Lines $lines -Heading $heading)) {
            if ($section -eq "dependency-matrix") {
                Add-Blocker -Code "ARCH_DEPENDENCY_MATRIX_MISSING" -Artifact $artifact -SectionId $section -Message "Development View must include Dependency Matrix."
            } else {
                Add-Blocker -Code "ARCH_REQUIRED_SECTION_MISSING" -Artifact $artifact -SectionId $section -Message "Required section is missing."
            }
            continue
        }
        if (-not (Test-SectionHasContent -Lines $lines -Heading $heading)) {
            if ($section -eq "dependency-matrix") {
                Add-Blocker -Code "ARCH_DEPENDENCY_MATRIX_EMPTY" -Artifact $artifact -SectionId $section -Message "Dependency Matrix has no supported records."
            } elseif ($section -eq "source-traceability") {
                Add-Blocker -Code "ARCH_TRACEABILITY_MISSING" -Artifact $artifact -SectionId $section -Message "Source Traceability has no supported records."
            } else {
                Add-Blocker -Code "ARCH_REQUIRED_SECTION_EMPTY" -Artifact $artifact -SectionId $section -Message "Required section has no supported records."
            }
        }
    }
}

$readyGate = if ($blockers.Count -eq 0) { "PASS" } else { "BLOCKED" }
$result = [PSCustomObject]@{
    ready_gate = $readyGate
    blockers = $blockers
}

if ($Json) {
    $result | ConvertTo-Json -Compress -Depth 5
} else {
    Write-Output "ready_gate: $readyGate"
    foreach ($blocker in $blockers) {
        Write-Output ($blocker | ConvertTo-Json -Compress)
    }
}

if ($blockers.Count -gt 0) {
    exit 1
}
