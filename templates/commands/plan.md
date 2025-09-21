---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

Given the implementation details provided as an argument, do this:

1. Load Spec Kit configuration:
   - Check for `/.specify.yaml` at the host project root; if it exists, load that file
   - Otherwise load `/config-default.yaml`
   - Extract the root `spec-kit` entry and store it as `SPEC_KIT_CONFIG`
   - Output the resulting `SPEC_KIT_CONFIG` for operator visibility

2. Run `{SCRIPT}` from the repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. All future file paths must be absolute.
3. Read and analyze the feature specification to understand:
   - The feature requirements and user stories
   - Functional and non-functional requirements
   - Success criteria and acceptance criteria
   - Any technical constraints or dependencies mentioned

4. If defined, read documents from `SPEC_KIT_CONFIG.plan.documents`:
   - For each item, resolve `path` to an absolute path from the repo root
   - Read the file and consider its `context` to guide planning decisions
   - If a file is missing, note it and continue

5. Read the constitution at the path specified by `SPEC_KIT_CONFIG.constitution.path` to understand constitutional requirements.

6. Execute the implementation plan template:
   - Load `/templates/plan-template.md` (already copied to IMPL_PLAN path)
   - Set Input path to FEATURE_SPEC
   - Run the Execution Flow (main) function steps 1-9
   - The template is self-contained and executable
   - Follow error handling and gate checks as specified
   - Let the template guide artifact generation in $SPECS_DIR:
     * Phase 0 generates research.md
     * Phase 1 generates data-model.md, contracts/, quickstart.md
     * Phase 2 generates tasks.md
   - Incorporate user-provided details from arguments into Technical Context: {ARGS}
   - Update Progress Tracking as you complete each phase

7. Verify execution completed:
   - Check Progress Tracking shows all phases complete
   - Ensure all required artifacts were generated
   - Confirm no ERROR states in execution

8. Report results with branch name, file paths, and generated artifacts.

Use absolute paths with the repository root for all file operations to avoid path issues.
