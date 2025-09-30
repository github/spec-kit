---
description: "Perform a comprehensive, read-only audit of the project against its constitution, specifications, and plans."
scripts:
  sh: scripts/bash/collect-debug-context.sh --json
  ps: scripts/powershell/collect-debug-context.ps1 -Json
---

User input: $ARGUMENTS

1. Run {SCRIPT} to collect all context.
2. Analyze the context against memory/constitution.md, spec.md, and plan.md.
3. Identify violations, inconsistencies, and quality issues.
4. Generate a structured report in reports/debug-report-YYYY-MM-DD-HHMMSS.md.
5. Present a summary of the findings to the user.