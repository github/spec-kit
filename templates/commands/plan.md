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

1. Run `{SCRIPT}` from the repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. All future file paths must be absolute.
   - BEFORE proceeding, inspect FEATURE_SPEC for a `## Clarifications` section with at least one `Session` subheading. If missing or clearly ambiguous areas remain (vague adjectives, unresolved critical choices), PAUSE and instruct the user to run `/clarify` first to reduce rework. Only continue if: (a) Clarifications exist OR (b) an explicit user override is provided (e.g., "proceed without clarification"). Do not attempt to fabricate clarifications yourself.
2. Read and analyze the feature specification to understand:
   - The feature requirements and user stories
   - Functional and non-functional requirements
   - Success criteria and acceptance criteria
   - Any technical constraints or dependencies mentioned

3. Read the constitution at `/memory/constitution.md` to understand constitutional requirements.

4. Execute the implementation plan template:
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

5. Verify execution completed:
   - Check Progress Tracking shows all phases complete
   - Ensure all required artifacts were generated
   - Confirm no ERROR states in execution

6. Report results with branch name, file paths, and generated artifacts.

Use absolute paths with the repository root for all file operations to avoid path issues.
