# update-context.ps1 — Goose integration: create/update AGENTS.md
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

# Always delegate to the shared updater; fail clearly if it is unavailable.
if (-not (Test-Path $sharedScript)) {
    Write-Error "Error: shared agent context updater not found: $sharedScript"
    Write-Error "Goose integration requires support in scripts/powershell/update-agent-context.ps1."
    exit 1
}

& $sharedScript -AgentType goose
exit $LASTEXITCODE
