---
description: "Resolve effective spec path (spec.override.md when present) for downstream SDD commands"
scripts:
  sh: scripts/bash/resolve-handoff-spec.sh --json
  ps: scripts/powershell/Resolve-HandoffSpec.ps1 -Json
---

# Handoff Spec Resolve

Lightweight resolver for tasks, analyze, implement, and converge.
Does not fetch remote content unless override is missing while a handoff URL is
configured (error with remediation).

## Execution

Run `{SCRIPT}` from the repository root and use `EFFECTIVE_SPEC` from JSON when
loading requirement content (see preset `ai-team-handoff-spec`).
