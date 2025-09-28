description: Execute context engineering deliverables defined during planning and research.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeTasks
---

Consider any command argument or surrounding discussion as part of the implementation context.

User input:

$ARGUMENTS

1. Run `{SCRIPT}` to gather context. Capture `WORKFLOW`, `FEATURE_DIR`, `PRIMARY_FILE`, `PLAN_FILE`, `RESEARCH_FILE`, and the list `AVAILABLE_DOCS`.

2. Load the core artifacts for the workflow:
   - Free-Style → `PRIMARY_FILE` (context spec), `RESEARCH_FILE`, `PLAN_FILE`.
   - PRP → `PRIMARY_FILE` (INITIAL brief), `PRP_FILE`, `PLAN_FILE`.
   - All-in-One → `PRIMARY_FILE` (single record).

3. If `tasks.md` exists in `FEATURE_DIR`, treat it as the authoritative task list; otherwise derive tasks from the plan and PRP sections and document them as you work.

4. Execute implementation iteratively:
   - Follow sequencing defined in the plan or PRP.
   - Keep artifacts synchronized: update plan/prp notes as decisions change.
   - Document test coverage, data migrations, and API changes inline with code changes.

5. After completing work, validate outcomes against the success criteria captured during `specify`/PRP creation. Record validation evidence in `PLAN_FILE` (or in the all-in-one record).

6. Summarize what changed, note remaining open items, and suggest the next command (e.g., `/context-engineer` follow-ups, regression testing, or review steps).