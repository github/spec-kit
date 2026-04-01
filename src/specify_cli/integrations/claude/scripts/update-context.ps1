# update-context.ps1 — Claude Code integration: create/update CLAUDE.md
#
# Thin wrapper that delegates to the shared update-agent-context script.
# Activated in Stage 7 when the shared script uses integration.json dispatch.
#
# Until then, this delegates to the shared script as a subprocess.

$ErrorActionPreference = 'Stop'

# Derive repo root from script location (walks up to find .specify/)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot = git rev-parse --show-toplevel 2>$null
# If git did not return a repo root, or the git root does not contain .specify,
# fall back to walking up from the script directory to find the initialized project root.
if (-not $repoRoot -or -not (Test-Path (Join-Path $repoRoot '.specify'))) {
    $repoRoot = $scriptDir
    $fsRoot = [System.IO.Path]::GetPathRoot($repoRoot)
    while ($repoRoot -and $repoRoot -ne $fsRoot -and -not (Test-Path (Join-Path $repoRoot '.specify'))) {
        $repoRoot = Split-Path -Parent $repoRoot
    }
}

& "$repoRoot/.specify/scripts/powershell/update-agent-context.ps1" -AgentType claude
