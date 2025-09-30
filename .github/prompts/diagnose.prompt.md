---
description: "Run a pre-flight check on spec.md or plan.md for blocking issues."
---

User input: $ARGUMENTS

1. Run .specify/scripts/bash/run-diagnose.sh --json to determine the current project phase and scan the relevant input file (spec.md or plan.md).
2. Report any unresolved [NEEDS CLARIFICATION] markers or other predictable blockers.
3. Provide a recommendation to the user to fix the issues before proceeding.
