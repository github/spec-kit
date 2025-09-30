---
description: "Fix a specific issue identified by the /debug command."
scripts:
  sh: scripts/bash/apply-align.sh --id "{ARGS}"
  ps: scripts/powershell/apply-align.ps1 -Id "{ARGS}"
---

User input: $ARGUMENTS

1. Run {SCRIPT} to load the debug report by ID from `$ARGUMENTS`.
2. Locate the specific issue entry in the report using the ID from `$ARGUMENTS`.
3. Apply the suggested fix from the report to the target file(s).
4. Run automated verification (tests and linter).
5. If verification passes, commit the change.
6. If verification fails, discard the changes and generate a failure report.