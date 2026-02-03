---
description: Convert SpecKit tasks.md into beads (and optional gastown convoy) for the current feature.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from repo root and parse FEATURE_DIR. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Validate prerequisites**:
   - Ensure `tasks.md` exists at `FEATURE_DIR/tasks.md`
   - Ensure `.beads/` exists in repo root (otherwise instruct user to run `bd init`)
   - Ensure `bd` CLI is available in PATH
   - Check `gt` CLI availability (optional; warn if missing)

3. **Execute bridge**:
   - Run `.specify/scripts/bash/taskstoepic-helper.sh` from repo root, passing `$ARGUMENTS` through unchanged.
   - The helper script runs the Python library, creates beads, links dependencies, and optionally creates a convoy.

4. **Report**: Show the helper script output verbatim. If errors occur, stop and report the error message and exit code.

Context for run: $ARGUMENTS
