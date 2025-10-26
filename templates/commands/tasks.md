---
description: Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## Strict Contract

- **Required Inputs**
  - Feature directory, plan/spec paths, and available documents returned by `{SCRIPT}`.
  - Optional `$ARGUMENTS` to emphasize focus areas.
- **Allowed Tools**
  - Run `{SCRIPT}` exactly once from the repository root.
  - Read from `spec.md`, `plan.md`, `data-model.md`, `contracts/`, `research.md`, and `quickstart.md` when present.
  - Write to `tasks.md` only.
- **Outputs**
  - Produce `tasks.md` using `templates/tasks-template.md`, including dependency registry and Mermaid graph.
  - Respond with a JSON code block:

    ```json
    {
      "status": "success" | "error",
      "branch": "<branch-name>",
      "tasks_path": "<absolute-path>",
      "totals": {
        "tasks": <int>,
        "parallel": <int>
      },
      "story_breakdown": {
        "US1": <int>,
        "US2": <int>,
        "US3": <int>
      },
      "dependency_violations": ["<issue>", "..."]
    }
    ```

    Include every user story identifier present in the generated tasks.
- **Idempotency**
  - Re-running must regenerate `tasks.md` deterministically from current artifacts without duplicating phases.
- **Stop Conditions**
  - Abort (set `status` to `error`) if prerequisites are missing or specification still contains `[NEEDS CLARIFICATION]` markers.
  - End after writing `tasks.md` and emitting JSON.

## User Input

```text
$ARGUMENTS
```

Use the input to adjust emphasis or highlight constraints.

## Execution Flow

1. **Setup**
   - Execute `{SCRIPT}` once to obtain `FEATURE_DIR`, `BRANCH_NAME`, and `AVAILABLE_DOCS`.
   - Shell guidance:
     - **Bash**: Wrap parameters in double quotes; escape embedded quotes as `\"`.
     - **PowerShell**: Use double quotes; escape embedded quotes by doubling them.
   - Fail if `plan.md` or `spec.md` is missing.

2. **Load Artifacts**
   - Parse specification for user stories, priorities, and success criteria.
   - Extract architecture, structure, and exit criteria from `plan.md`.
   - Load optional artifacts (`data-model.md`, `contracts/`, `research.md`, `quickstart.md`) to enrich tasks and dependencies.

3. **Synthesize Task Graph**
   - Generate machine-parseable task IDs (T001…Tnnn) with dependency metadata.
   - Populate the Dependency Registry and Mermaid graph sections using calculated relationships.
   - Ensure each user story phase includes a Definition of Done checklist populated with feature-specific outcomes.
   - Highlight parallelizable tasks with `[P]` based on dependency analysis.

4. **Validate**
   - Confirm every functional requirement maps to at least one task.
   - Ensure dependencies do not introduce cycles; record violations if detected.
   - Verify Definition of Done checklists exist for each story referenced in tasks.

5. **Persist and Report**
   - Write `tasks.md` following the template structure.
   - Emit JSON summary with totals, story breakdown, and any dependency issues.

## Task Authoring Standards

- Reference concrete file paths and modules defined in the plan.
- Keep task descriptions implementation-ready and independently completable.
- Align phase ordering with priority (Setup → Foundational → User Stories → Polish).
- Prefer grouping tasks by story to maintain incremental delivery.
