---
description: "Perform a comprehensive, read-only audit of the project against its constitution, specifications, and plans."
---

User input: $ARGUMENTS

1. Run .specify/scripts/bash/collect-debug-context.sh --json to collect all context.
2. Analyze the context against .specify/memory/constitution.md, spec.md, and plan.md.
3. Identify violations, inconsistencies, and quality issues.
4. Generate a structured report in reports/debug-report-YYYY-MM-DD-HHMMSS.md.
5. Present a summary of the findings to the user.
