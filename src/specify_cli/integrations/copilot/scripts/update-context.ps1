# update-context.ps1 — Copilot integration: create/update .github/copilot-instructions.md
#
# This is the copilot-specific implementation that produces the GitHub
# Copilot instructions file. The shared dispatcher reads
# .specify/integration.json and calls this script.
#
# NOTE: This script is not yet active. It will be activated in Stage 7
# when the shared update-agent-context.ps1 replaces its switch statement
# with integration.json-based dispatch. The shared script must also be
# refactored to support SPECKIT_SOURCE_ONLY (guard the Main call) before
# dot-sourcing will work.
#
# Until then, this delegates to the shared script as a subprocess.

$ErrorActionPreference = 'Stop'

$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) { $repoRoot = $PWD.Path }

# Invoke shared update-agent-context script as a separate process.
# Dot-sourcing is unsafe until that script guards its Main call.
& "$repoRoot/.specify/scripts/powershell/update-agent-context.ps1" -AgentType copilot
