# update-context.ps1 — Copilot integration: create/update .github/copilot-instructions.md
#
# This is the copilot-specific implementation that produces the GitHub
# Copilot instructions file. The shared dispatcher reads
# .specify/integration.json and calls this script.
#
# Sources common.ps1 and the shared update-agent-context functions,
# then calls Update-AgentFile with the copilot target path.

$ErrorActionPreference = 'Stop'

$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) { $repoRoot = $PWD.Path }

# Source shared utilities
. "$repoRoot/.specify/scripts/powershell/common.ps1"

# Source update-agent-context functions
# SPECKIT_SOURCE_ONLY prevents the shared script from running its own main.
$env:SPECKIT_SOURCE_ONLY = '1'
. "$repoRoot/.specify/scripts/powershell/update-agent-context.ps1"

# Gather feature paths and parse plan data
$paths = Get-FeaturePaths
$implPlan = $paths.IMPL_PLAN
Read-PlanData -PlanFile $implPlan

# Create or update the copilot instructions file
$copilotFile = Join-Path $repoRoot '.github/copilot-instructions.md'
Update-AgentFile -TargetFile $copilotFile -AgentName 'GitHub Copilot'
