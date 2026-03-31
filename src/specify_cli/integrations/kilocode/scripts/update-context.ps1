# update-context.ps1 — Kilo Code integration: create/update .kilocode/rules/specify-rules.md
#
# Thin wrapper that delegates to the shared update-agent-context script.
# Activated in Stage 7 when the shared script uses integration.json dispatch.
#
# Until then, this delegates to the shared script as a subprocess.

$ErrorActionPreference = 'Stop'

$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) { $repoRoot = $PWD.Path }

& "$repoRoot/.specify/scripts/powershell/update-agent-context.ps1" -AgentType kilocode
