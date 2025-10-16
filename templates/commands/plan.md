---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
scripts:
  sh: scripts/bash/setup-plan.sh --json {ARGS}
  ps: scripts/powershell/setup-plan.ps1 -Json {ARGS}
---

Given the implementation details provided as an argument, do this:

## Capability Mode Detection

**Check for --capability flag in arguments:**
- If `$ARGUMENTS` contains `--capability cap-XXX`:
  - Set CAPABILITY_MODE=true
  - Extract capability ID (e.g., cap-001)
  - Adjust paths to capability subdirectory
- Else:
  - Set CAPABILITY_MODE=false
  - Use parent feature paths (existing behavior)

## Path Resolution

1. Run `{SCRIPT}` from the repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. All future file paths must be absolute.

2. **If CAPABILITY_MODE=true:**
   - Determine capability directory from current location or arguments
   - Set FEATURE_SPEC to capability spec: `specs/[feature-id]/cap-XXX-[name]/spec.md`
   - Set IMPL_PLAN to capability plan: `specs/[feature-id]/cap-XXX-[name]/plan.md`
   - Load parent spec at `specs/[feature-id]/spec.md` for context
   - Load capabilities.md for dependency information
3. Read and analyze the specification to understand:
   - The feature requirements and user stories
   - Functional and non-functional requirements
   - Success criteria and acceptance criteria
   - Any technical constraints or dependencies mentioned

4. **If CAPABILITY_MODE=true:**
   - Verify LOC budget from capability spec (impl ≤500, tests ≤500, total ≤1000)
   - Check dependencies on other capabilities (from capabilities.md)
   - Ensure capability scope is clear and bounded
   - Warn if impl >500 OR tests >500 OR total >1000

5. Read the constitution at `/memory/constitution.md` to understand constitutional requirements.

6. Execute the implementation plan template:
   - Load `/templates/plan-template.md` (already copied to IMPL_PLAN path)
   - Set Input path to FEATURE_SPEC
   - Run the Execution Flow (main) function steps 1-10
   - The template is self-contained and executable
   - Follow error handling and gate checks as specified
   - Let the template guide artifact generation in $SPECS_DIR:
     * Phase 0 generates research.md
     * Phase 1 generates data-model.md, contracts/, quickstart.md
     * Phase 2 generates tasks.md
   - Incorporate user-provided details from arguments into Technical Context: {ARGS}
   - Update Progress Tracking as you complete each phase

7. **If CAPABILITY_MODE=true:**
   - Validate LOC Budget Tracking section shows impl ≤500, tests ≤500, total ≤1000
   - If any limit exceeded: Require justification OR suggest further decomposition
   - Ensure capability dependencies are documented
   - Verify all components scoped to this capability only

8. Verify execution completed:
   - Check Progress Tracking shows all phases complete
   - Ensure all required artifacts were generated
   - Confirm no ERROR states in execution

9. Report results with branch name, file paths, and generated artifacts.

---

## Usage Examples

**Parent feature planning (simple features <1000 LOC total):**
```bash
/plan "Use FastAPI + PostgreSQL + React"
→ Generates plan.md for entire feature on current branch
→ Single PR workflow
```

**Capability planning (atomic PRs, 400-1000 LOC total each):**
```bash
/plan --capability cap-001 "Use FastAPI + JWT for auth"
→ Creates NEW branch: username/jira-123.feature-cap-001
→ Generates cap-001/plan.md scoped to 400-1000 LOC total
→ Atomic PR: cap-001 branch → main
```

## Atomic PR Workflow (Capability Mode)

When using `--capability cap-XXX`, the script:

1. **Creates capability branch** from parent feature branch:
   - Parent: `username/jira-123.user-system`
   - Capability: `username/jira-123.user-system-cap-001`

2. **Sets up isolated workspace**:
   - Spec: `specs/jira-123.user-system/cap-001-auth/spec.md`
   - Plan: `specs/jira-123.user-system/cap-001-auth/plan.md`
   - All work happens on capability branch

3. **PR workflow**:
   - Implement on `cap-001` branch (400-1000 LOC total)
   - Create PR: `cap-001` → `main`
   - After merge, checkout parent branch
   - Pull latest main into parent
   - Repeat for `cap-002`, `cap-003`, etc.

4. **Benefits**:
   - Fast reviews (1-2 days vs 7+ days for large PRs)
   - Manageable TDD scope per capability
   - Parallel development (team members work on different caps)
   - Early integration feedback

Use absolute paths with the repository root for all file operations to avoid path issues.
