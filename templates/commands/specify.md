---
description: Create or update the feature specification from a natural language feature description.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

Given the feature description provided as an argument, do this:

1. Run pre-specify hook if available (ignore errors):
   - Windows: Try `.specify/hooks/pre-specify.ps1 "{ARGS}"` then `.specify/hooks/pre-specify "{ARGS}"`
   - Unix/Linux: Try `.specify/hooks/pre-specify "{ARGS}"`
2. Check for prepare-feature-num hook and get custom number:
   - Windows: Try `.specify/hooks/prepare-feature-num.ps1 "{ARGS}"` then `.specify/hooks/prepare-feature-num "{ARGS}"`
   - Unix/Linux: Try `.specify/hooks/prepare-feature-num "{ARGS}"`
   - If hook returns a number, use `--feature-num $FEATURE_NUM` with the script
3. Run the script `{SCRIPT}` from repo root (with optional --feature-num parameter) and parse its JSON output for BRANCH_NAME, SPEC_FILE, and FEATURE_NUM. All file paths must be absolute.
  **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.
4. Export environment variables: `export BRANCH_NAME SPEC_FILE FEATURE_NUM` (Unix) or `$env:BRANCH_NAME = $BRANCH_NAME; $env:SPEC_FILE = $SPEC_FILE; $env:FEATURE_NUM = $FEATURE_NUM` (Windows)
5. Run post-checkout hook if available (ignore errors):
   - Windows: Try `.specify/hooks/post-checkout.ps1 "{ARGS}" "$FEATURE_NUM" "$BRANCH_NAME" "$SPEC_FILE"` then `.specify/hooks/post-checkout "{ARGS}" "$FEATURE_NUM" "$BRANCH_NAME" "$SPEC_FILE"`
   - Unix/Linux: Try `.specify/hooks/post-checkout "{ARGS}" "$FEATURE_NUM" "$BRANCH_NAME" "$SPEC_FILE"`
6. Load `templates/spec-template.md` to understand required sections.
7. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.
8. Run post-specify hook if available (ignore errors):
   - Windows: Try `.specify/hooks/post-specify.ps1 "{ARGS}" "$FEATURE_NUM" "$BRANCH_NAME" "$SPEC_FILE"` then `.specify/hooks/post-specify "{ARGS}" "$FEATURE_NUM" "$BRANCH_NAME" "$SPEC_FILE"`
   - Unix/Linux: Try `.specify/hooks/post-specify "{ARGS}" "$FEATURE_NUM" "$BRANCH_NAME" "$SPEC_FILE"`
9. Report completion with branch name, spec file path, and readiness for the next phase.

Note: The script creates and checks out the new branch and initializes the spec file before writing. Hooks follow Git-style naming: pre-specify for validation, prepare-feature-num for custom numbering, post-checkout after branch creation, and post-specify after spec completion.
