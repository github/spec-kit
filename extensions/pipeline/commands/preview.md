---
description: "Print the resolved Spec Kit pipeline phase plan for the given --skip/--add flags without running anything — a dry run of the deterministic phase resolver."
scripts:
  sh: scripts/bash/resolve-phases.sh
  ps: scripts/powershell/resolve-phases.ps1
---

# Pipeline: preview

Show the phase plan `/speckit.pipeline.run` *would* execute for a given set of flags, without running any phase. Use it to confirm a tailored pipeline (skips/adds) resolves the way you expect before committing to a full run.

## Input

`$ARGUMENTS` — optional flags only (no feature description needed):

- `--skip <csv>` — default phases to drop.
- `--add <csv>` — insertable phases to add (`constitution`, `checklist`).

## Behavior

Run the resolver and print its output:

```
{SCRIPT}  --skip "<skip csv>" --add "<add csv>"
```

Each line is `order  phase  command  gate  description`, in the exact order `run` would execute. `--list` (no flags) dumps the full registry of orderable phases.

Report the resolver's exit code and, on any non-zero code (`10`–`14`), its stderr message verbatim — the same validation `run` performs, so a bad flag combination is caught here first. This command never edits files and never invokes a `/speckit.*` phase.
