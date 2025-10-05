---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
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
   - Verify LOC budget from capability spec (should be 200-500 LOC)
   - Check dependencies on other capabilities (from capabilities.md)
   - Ensure capability scope is clear and bounded
   - Warn if estimated total >500 LOC

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
   - Validate LOC Budget Tracking section shows ≤500 LOC
   - If >500 LOC: Require justification OR suggest further decomposition
   - Ensure capability dependencies are documented
   - Verify all components scoped to this capability only

8. Verify execution completed:
   - Check Progress Tracking shows all phases complete
   - Ensure all required artifacts were generated
   - Confirm no ERROR states in execution

9. Report results with branch name, file paths, and generated artifacts.

---

## Usage Examples

**Parent feature planning (original workflow):**
```bash
/plan "Use FastAPI + PostgreSQL + React"
→ Generates plan.md for entire feature
```

**Capability planning (new workflow):**
```bash
/plan --capability cap-001 "Use FastAPI + JWT for auth"
→ Generates cap-001/plan.md scoped to 200-500 LOC
```

Use absolute paths with the repository root for all file operations to avoid path issues.
