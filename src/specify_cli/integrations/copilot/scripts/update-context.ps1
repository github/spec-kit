# update-context.ps1 — Copilot integration update-context script
#
# Thin wrapper that delegates to the shared update-agent-context.ps1
# with the copilot agent type. Installed by the integration into
# .specify/integrations/copilot/scripts/ and referenced from
# .specify/agent.json so the shared dispatcher can find it.

$ErrorActionPreference = 'Stop'

$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) { $repoRoot = $PWD.Path }

# Delegate to the shared update-agent-context script
& "$repoRoot/.specify/scripts/powershell/update-agent-context.ps1" -AgentType copilot @args
