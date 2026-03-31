# update-context.ps1 — Copilot integration: update .github/copilot-instructions.md
#
# Called by the shared dispatcher after it has sourced common functions
# (Update-AgentFile, etc.). This script only contains the copilot-specific
# target path and agent name.

$ErrorActionPreference = 'Stop'

if (-not $repoRoot) {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    if (-not $repoRoot) { $repoRoot = $PWD.Path }
}

$copilotFile = Join-Path $repoRoot '.github/copilot-instructions.md'

Update-AgentFile -TargetFile $copilotFile -AgentName 'GitHub Copilot'
