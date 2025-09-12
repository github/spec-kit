---
description: Create or update the feature specification from a natural language feature description.
---
<!-- VARIANT:sh 1. Run the script `scripts/bash/create-new-feature.sh --json "{ARGS}"` from repo root and parse its JSON output for BRANCH_NAME and SPEC_FILE. All file paths must be absolute. -->
<!-- VARIANT:ps 1. Run the script `scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"` from repo root and parse its JSON output for BRANCH_NAME and SPEC_FILE. All file paths must be absolute. -->

Given the feature description provided as an argument, do this:

1. VARIANT-INJECT
2. Load `templates/spec-template.md` to understand required sections.
3. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.
4. Report completion with branch name, spec file path, and readiness for the next phase.

Note: The script creates and checks out the new branch and initializes the spec file before writing.
