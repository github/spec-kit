---
description: Create or update the feature specification from a natural language feature description.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

The text the user typed after `/specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `{ARGS}` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, do this:

1. Run pre-specify hook if available (ignore errors):
   - Try `.specify/hooks/pre-specify{HOOK_EXT} "{ARGS}"`
2. Check for prepare-feature-num hook and get custom number:
   - Try `.specify/hooks/prepare-feature-num{HOOK_EXT} "{ARGS}"`
   - If hook returns a number, use `--feature-num $FEATURE_NUM` with the script
3. Run the script `{SCRIPT}` from repo root (with optional --feature-num parameter) and parse its JSON output for BRANCH_NAME, SPEC_FILE, and FEATURE_NUM. All file paths must be absolute.
  **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.
4. Run post-checkout hook if available (ignore errors):
   - Try `.specify/hooks/post-checkout{HOOK_EXT} "{ARGS}" "$FEATURE_NUM" "$BRANCH_NAME" "$SPEC_FILE"`
5. Load `templates/spec-template.md` to understand required sections.
6. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.
7. Run post-specify hook if available (ignore errors):
   - Try `.specify/hooks/post-specify{HOOK_EXT} "{ARGS}" "$FEATURE_NUM" "$BRANCH_NAME" "$SPEC_FILE"`
8. Report completion with branch name, spec file path, and readiness for the next phase.

Note: The script creates and checks out the new branch and initializes the spec file before writing. 
Hooks follow Git-style naming: pre-specify for validation, prepare-feature-num for custom numbering, post-checkout after branch creation, and post-specify after spec completion.
