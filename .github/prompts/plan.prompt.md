---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
---

# Plan

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

Given the implementation details provided as an argument, do this:

1. Run `.specify/scripts/powershell/setup-plan.ps1 -Json` from the repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. All future file paths must be absolute.
   - BEFORE proceeding, inspect FEATURE_SPEC for a `## Clarifications` section with at least one `Session` subheading. If missing or clearly ambiguous areas remain (vague adjectives, unresolved critical choices), PAUSE and instruct the user to run `/clarify` first to reduce rework. Only continue if: (a) Clarifications exist OR (b) an explicit user override is provided (e.g., "proceed without clarification"). Do not attempt to fabricate clarifications yourself.
2. Read and analyze the feature specification to understand:
   - The feature requirements and user stories
   - Functional and non-functional requirements
   - Success criteria and acceptance criteria
   - Any technical constraints or dependencies mentioned

3. Read the constitution at `.specify/memory/constitution.md` to understand constitutional requirements.

4. Execute the implementation plan template:
   - Load `.specify/templates/plan-template.md` (already copied to IMPL_PLAN path)
   - Set Input path to FEATURE_SPEC
   - Run the Execution Flow (main) function steps 1-9
   - The template is self-contained and executable
   - Follow error handling and gate checks as specified
   - Let the template guide artifact generation in $SPECS_DIR:
     * Phase 0 generates research.md
     * Phase 1 generates data-model.md, contracts/, quickstart.md
     * Phase 2 generates tasks.md
   - Incorporate user-provided details from arguments into Technical Context: $ARGUMENTS
   - Update Progress Tracking as you complete each phase

5. Verify execution completed:
   - Check Progress Tracking shows all phases complete
   - Ensure all required artifacts were generated
   - Confirm no ERROR states in execution

6. Commit and push the changes:
   - Stage all generated artifacts and modified files
   - Create a commit with a descriptive message summarizing the plan
   - Push the branch (BRANCH) to remote

7. Create or update a Pull Request:
   - The PR must be against the default branch.
   - The PR must be opened as a draft.
   - Determine the PR type and icon based on the changes:

     | Type of change | Icon | Label |
     |-|-|-|
     | Docs | 📖 | Docs |
     | Fix | 🪲 | Fix, Patch |
     | Security fix | ⚠️ | Fix |
     | Patch | 🩹 | Patch |
     | Feature | 🚀 | Minor |
     | Breaking change | 🌟 | Major |

   - Create PR title: `<Icon> [Type of change]: <Short description>`
   - Create PR description:
     * Start with a summary paragraph describing the key outcome and changes for user
     * DO NOT add a title before the leading paragraph
     * At the end of the PR paragraph, add a "- Fixes #<issue-number>" line to link the PR to the issue
     * Follow with additional details answering Why, How, and What
     * Avoid superfluous headers or sections
     * We do not need details, we need to add what changes for the user of the code
   - Apply appropriate label(s) based on the type of change
   - Link the PR to the associated issue

8. Update issue labels:
   - Remove 'specification' label from the linked issue
   - Add 'plan' label to the linked issue

9. Report results with branch name, PR URL, file paths, and generated artifacts.

Use absolute paths with the repository root for all file operations to avoid path issues.
