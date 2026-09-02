# Compose multiple evaluator results with deterministic precedence.
#
# Usage:
#   .\compose-results.ps1 -ResultsDir <path> -Phase <phase> [-Strategy strict|majority|optimistic] [-Output <path>]
#
# Reads evaluator result JSON files from a results directory and produces a
# composed result.

param(
    [Parameter(Mandatory=$true)]
    [string]$ResultsDir,

    [Parameter(Mandatory=$true)]
    [string]$Phase,

    [ValidateSet("strict", "majority", "optimistic")]
    [string]$Strategy = "strict",

    [string]$Output
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ResultsDir -PathType Container)) {
    Write-Error "Results directory not found: $ResultsDir"
    exit 1
}

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Collect result files for the phase (exclude previously composed files)
$resultFiles = Get-ChildItem -Path $ResultsDir -Filter "*-$Phase-*.json" |
    Where-Object { $_.Name -notlike "composed-*" } |
    Sort-Object Name

if ($resultFiles.Count -eq 0) {
    $composed = @{
        schema_version = "1.0"
        composed = $true
        phase = $Phase
        composition_strategy = $Strategy
        composed_outcome = "pass"
        composed_summary = "No evaluator results found for this phase."
        evaluator_results = @()
        findings = @()
        next_action = @{
            kind = "pass"
            target_phase = $null
            message = "No evaluator results found."
        }
        evaluator_states = @{}
        metadata = @{
            timestamp = $timestamp
            evaluator_count = 0
            contradictory_findings = @()
        }
    }
} else {
    $allResults = @()
    $allFindings = @()
    $evaluatorSummaries = @()
    $outcomes = @()
    $evaluatorStates = @{}

    $severityOrder = @{
        critical = 0
        high = 1
        medium = 2
        low = 3
        info = 4
    }

    foreach ($file in $resultFiles) {
        try {
            $data = Get-Content -Path $file.FullName -Raw | ConvertFrom-Json
        } catch {
            Write-Warning "Skipping invalid result file: $($file.Name): $_"
            continue
        }

        if (-not $data.PSObject.Properties["schema_version"] -or
            -not $data.PSObject.Properties["evaluator"] -or
            -not $data.PSObject.Properties["outcome"] -or
            -not $data.PSObject.Properties["findings"]) {
            Write-Warning "Skipping $($file.Name): missing required keys"
            continue
        }

        $allResults += $data
        $outcomes += $data.outcome

        $evaluatorSummaries += @{
            evaluator_id = $data.evaluator.id
            outcome = $data.outcome
            findings_count = if ($data.findings) { $data.findings.Count } else { 0 }
        }

        if ($data.findings) {
            foreach ($finding in $data.findings) {
                $finding | Add-Member -NotePropertyName "_evaluator_id" -NotePropertyValue $data.evaluator.id -Force
                $allFindings += $finding
            }
        }

        if ($data.PSObject.Properties["state"]) {
            $evaluatorStates[$data.evaluator.id] = $data.state
        }
    }

    # Sort findings by severity
    $allFindings = $allFindings | Sort-Object {
        $sev = if ($_.PSObject.Properties["severity"]) { $_.severity } else { "info" }
        if ($severityOrder.ContainsKey($sev)) { $severityOrder[$sev] } else { 99 }
    }, { if ($_.PSObject.Properties["id"]) { $_.id } else { "" } }

    # Resolve composed outcome
    function Resolve-Outcome {
        param([string[]]$Outcomes, [string]$Strategy)

        $precedence = @("block", "gather_evidence", "iterate", "clarify", "warn", "pass")

        switch ($Strategy) {
            "optimistic" {
                for ($i = $precedence.Count - 1; $i -ge 0; $i--) {
                    if ($Outcomes -contains $precedence[$i]) { return $precedence[$i] }
                }
                return "pass"
            }
            "majority" {
                $grouped = $Outcomes | Group-Object | Sort-Object Count -Descending
                $maxCount = $grouped[0].Count
                $tied = $grouped | Where-Object { $_.Count -eq $maxCount } | ForEach-Object { $_.Name }
                foreach ($c in $precedence) {
                    if ($tied -contains $c) { return $c }
                }
                return $grouped[0].Name
            }
            default {
                foreach ($c in $precedence) {
                    if ($Outcomes -contains $c) { return $c }
                }
                return "pass"
            }
        }
    }

    $composedOutcome = Resolve-Outcome -Outcomes $outcomes -Strategy $Strategy

    $composed = @{
        schema_version = "1.0"
        composed = $true
        phase = $Phase
        composition_strategy = $Strategy
        composed_outcome = $composedOutcome
        composed_summary = "$($allResults.Count) evaluator(s) ran. $($allFindings.Count) finding(s) total."
        evaluator_results = $evaluatorSummaries
        findings = $allFindings
        next_action = @{
            kind = $composedOutcome
            target_phase = $null
            message = "Composed outcome: $composedOutcome."
        }
        evaluator_states = $evaluatorStates
        metadata = @{
            timestamp = $timestamp
            evaluator_count = $allResults.Count
            contradictory_findings = @()
        }
    }
}

$json = $composed | ConvertTo-Json -Depth 10

if ($Output) {
    $parent = Split-Path $Output -Parent
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    $json | Set-Content -Path $Output -Encoding UTF8
    Write-Host "Composed result written to $Output"
} else {
    Write-Output $json
}
