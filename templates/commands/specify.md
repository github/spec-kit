---
description: Create or update the feature specification from a natural language feature description.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

Given the feature description provided as an argument, do this:

1. Load Spec Kit configuration:
   - Check for `/.specify.yaml` at the host project root; if it exists, load that file
   - Otherwise load `/config-default.yaml`
   - Extract the root `spec-kit` entry and store it as `SPEC_KIT_CONFIG`
   - Output the resulting `SPEC_KIT_CONFIG` for operator visibility

2. Run the script `{SCRIPT}` from the repo root and parse its JSON output for BRANCH_NAME and SPEC_FILE. All future file paths must be absolute.
  **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

3. If defined, read documents from `SPEC_KIT_CONFIG.specify.documents`:
   - For each item, resolve `path` to an absolute path from the repo root
   - Read the file and consider its `context` to guide specification details
   - If a file is missing, note it and continue

4. Load `/templates/spec-template.md` to understand required sections.

5. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.

6. Report completion with branch name, spec file path, and readiness for the next phase.

Note: The script creates and checks out the new branch and initializes the spec file before writing.

Use absolute paths with the repository root for all file operations to avoid path issues.
