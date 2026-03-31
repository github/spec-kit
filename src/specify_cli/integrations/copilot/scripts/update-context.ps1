# update-context.ps1 — Copilot integration: update .github/copilot-instructions.md
#
# Sources the shared update-agent-context.ps1 (which defines Update-AgentFile
# and friends) and calls Update-AgentFile with the copilot-specific target path.
#
# In the final architecture (Stage 7) the shared dispatcher reads
# .specify/integration.json and invokes this script. Until then, the
# shared script's switch statement still works for copilot.

$ErrorActionPreference = 'Stop'

$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) { $repoRoot = $PWD.Path }

$copilotFile = Join-Path $repoRoot '.github/copilot-instructions.md'

# Source the shared script to get Update-AgentFile and friends.
# Use $env:SPECKIT_SOURCE_ONLY=1 to load functions without running main.
$env:SPECKIT_SOURCE_ONLY = '1'
. "$repoRoot/.specify/scripts/powershell/update-agent-context.ps1"

Update-AgentFile -TargetFile $copilotFile -AgentName 'GitHub Copilot' @args
