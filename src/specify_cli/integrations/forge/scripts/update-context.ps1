# update-context.ps1 — Forge integration: create/update AGENTS.md
#
# Thin wrapper that delegates to the shared update-agent-context script.
# Activated in Stage 7 when the shared script uses integration.json dispatch.
#
# Until then, this delegates to the shared script as a subprocess.

$ErrorActionPreference = 'Stop'

# Derive repo root from script location (walks up to find .specify/)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot = try { git rev-parse --show-toplevel 2>$null } catch { $null }
# If git did not return a repo root, or the git root does not contain .specify,
# fall back to walking up from the script directory to find the initialized project root.
if (-not $repoRoot -or -not (Test-Path (Join-Path $repoRoot '.specify'))) {
    $repoRoot = $scriptDir
    $fsRoot = [System.IO.Path]::GetPathRoot($repoRoot)
    while ($repoRoot -and $repoRoot -ne $fsRoot -and -not (Test-Path (Join-Path $repoRoot '.specify'))) {
        $repoRoot = Split-Path -Parent $repoRoot
    }
}

$sharedScript = "$repoRoot/.specify/scripts/powershell/update-agent-context.ps1"
# If the shared dispatcher already knows about "forge", delegate to it.
if ((Test-Path $sharedScript) -and (Select-String -Path $sharedScript -Pattern "'forge'|`"forge`"" -Quiet)) {
    & $sharedScript -AgentType forge
    exit $LASTEXITCODE
}

# Forge-specific handling: update or create AGENTS.md directly until the shared
# dispatcher script supports -AgentType forge.
$agentsFile = Join-Path $repoRoot 'AGENTS.md'
if (Test-Path $agentsFile) {
    $agentsContent = Get-Content -Path $agentsFile -ErrorAction Stop
    # Only add a Forge entry if one does not already exist.
    if (-not ($agentsContent | Where-Object { $_ -match '\bForge\b' })) {
        Add-Content -Path $agentsFile -Value ''
        Add-Content -Path $agentsFile -Value '## Forge'
        Add-Content -Path $agentsFile -Value '- Forge integration agent context'
    }
} else {
    $newContent = @(
        '# Agents'
        ''
        '## Forge'
        '- Forge integration agent context'
    )
    $newContent | Set-Content -Path $agentsFile -Encoding UTF8
}
exit 0
