---
description: Execute implementation plan by processing all tasks in tasks.md.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## Input

```text
$ARGUMENTS
```

Consider user input before proceeding (if not empty).

## Pre-Execution

Check `.specify/extensions.yml` for `hooks.before_implement`. Run mandatory hooks, show optional. Skip silently if missing/invalid.

## Workflow

1. Run `{SCRIPT}`, parse FEATURE_DIR and AVAILABLE_DOCS.

2. **Check checklists** (if FEATURE_DIR/checklists/ exists):
   - Count total/completed/incomplete items per checklist
   - If incomplete: show status table, ask user to confirm proceeding
   - If all pass: auto-proceed

3. **Load context**: tasks.md (required), plan.md (required), data-model.md, contracts/, research.md, quickstart.md (if exist).

4. **Setup verification**: Create/verify ignore files (.gitignore, .dockerignore, etc.) based on detected tech stack from plan.md. Append missing patterns to existing files, create full set for missing files.

5. **Parse tasks.md**: Extract phases, dependencies, task details, parallel markers [P].

6. **Execute phase-by-phase**:
   - Setup → Tests (if any) → Core → Integration → Polish
   - Sequential tasks in order, [P] tasks can run together
   - Mark completed tasks as `[X]` in tasks.md
   - Report progress after each task
   - Halt on non-parallel task failure, continue others for [P] failures

7. **Validate**: All tasks complete, features match spec, tests pass.

8. Check `.specify/extensions.yml` for `hooks.after_implement`. Run mandatory, show optional. Skip silently if missing.

## Rules

- If tasks.md incomplete/missing: suggest `/speckit.tasks` first
- Provide clear error messages with debugging context
