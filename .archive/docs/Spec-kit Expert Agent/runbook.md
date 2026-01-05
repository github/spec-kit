# runbook.md

## Overview
This runbook defines I/O contracts, gates, stop conditions, and recovery paths for the Spec Kit Expert Agent. Explain each concept to the users in a way that they can implement the execution and operations in their own terminal.

---

## State Model
`IDLE` → `/specify` → `SPEC_READY` → `/plan` → `PLAN_READY` → `/tasks` → `TASKS_READY`

Transitions require all **gates** for the current phase to pass and **clarifications** to be resolved.

---

## Commands
These are the commands available to the users when interacting with the framework, explain how to use them in their terminal and what to expect from each one.
### `/specify "<feature-description>"`
**Input**: concise description of user outcomes and journeys.  
**Actions**:
1. `create_feature` (JSON parse; absolute paths)
2. Write spec from template; preserve headings; add `[NEEDS CLARIFICATION]` where needed
**Artifacts**:  
- `/specs/<branch>/spec.md`  
**Gates**:
- Spec completeness checklist contains no unresolved markers
**Stop Conditions**:
- Any `[NEEDS CLARIFICATION]` present → STOP with questions
- Script/JSON failure
**Errors & Remedies**:
- `E_CREATE_FEATURE/GIT`: initialize git, re-run
- `E_WRITE/FS`: verify permissions; ensure parent directories

---

### `/plan "<technical-constraints and context>"`
**Input**: stack constraints, libraries, limits, non-functional requirements  
**Actions**:
1. `setup_plan`
2. Read `FEATURE_SPEC` + `/memory/constitution.md`
3. Execute plan template (phases 0–1); **STOP at step 7**
   - Generate: `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
4. Update progress tracking and constitution checks in `plan.md`
**Artifacts**:
- `/specs/<branch>/plan.md`
- `/specs/<branch>/research.md`
- `/specs/<branch>/data-model.md`
- `/specs/<branch>/contracts/…`
- `/specs/<branch>/quickstart.md`
**Gates**:
- No “ERROR” block in plan
- Constitution checks either fully pass or document justified exceptions
**Stop Conditions**:
- Unresolved clarifications
- Constitution violation w/o justification
**Errors & Remedies**:
- `E_PLAN/SPEC_MISSING`: create spec first via `/specify`
- `E_CONSTITUTION`: simplify approach or adjust design until passes

---

### `/tasks "<context>"`
**Input**: optional priorities/constraints; otherwise infer from plan & docs  
**Actions**:
1. `get_paths`; read plan + optional docs (contracts, data-model, research, quickstart)
2. Generate `tasks.md`:
   - Numbering: `T001`, `T002`, …
   - Order: Setup → Tests → Models → Services → Endpoints → Polish
   - Mark parallel-safe tasks with `[P]`
   - Every task lists specific file paths it touches/creates
**Artifacts**:
- `/specs/<branch>/tasks.md`
**Gates**:
- Each contract → a contract test task `[P]`
- Each user story → an integration test `[P]`
- No pair of `[P]` tasks modifies the same file
**Stop Conditions**:
- Missing core docs (plan)
- Conflicting dependencies
**Errors & Remedies**:
- `E_TASKS/NO_PLAN`: run `/plan` first
- `E_TASKS/PARALLEL_CONFLICT`: remove `[P]` or split files

---

## Error Object (standard)
```json
{
  "code": "E_*",
  "cause": "short explanation",
  "remediation": ["actionable step 1", "actionable step 2"],
  "where": "command|tool|file path",
  "details": {}
}
````

---

## Final Line Protocol
Each command must end with a single-line JSON `REPORT` (machine-readable), then stop.

---

## Rollback

* Wrong branch: `git switch -` to previous; delete created feature directory if empty
* Wrong files written: `git restore --source=HEAD~1 -- <path>` (or `git checkout <commit> -- <path>`)

---

## Security & Safety
* Disallow path traversal (`..`) on all `fs.*` calls
* Never write outside repo root
* No network or package installation during these phases
* Do not execute code or tests; only author specs/plans/tasks