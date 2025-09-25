---
description: Create or update the feature specification from a natural language feature description.
---

The user has described a new feature they want to build. Your job is to create a feature specification from that description.

The previous conversation you had with the user about the feature **is** the feature description. Insert the feature description into the variable `$FEATURE_DESCRIPTION` below when running the script.

Given that feature description, do this:

1. Run the script `.specify/scripts/bash/create-new-feature.sh --json "$FEATURE_DESCRIPTION"` from repo root and parse its JSON output for BRANCH_NAME and SPEC_FILE. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.
1. Load `.specify/templates/spec-template.md` to understand required sections.
1. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.
1. Report completion with branch name, spec file path, and readiness for the next phase.

Note: The script creates and checks out the new branch and initializes the spec file before writing.
