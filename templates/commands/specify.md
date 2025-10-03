---
description: Create or update the feature specification from a natural language feature description.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

The text the user typed after `/specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `$ARGUMENTS` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, do this:

1. Inspect the user input for an explicit feature name directive. Treat any line matching (case-insensitive) `feature-name:`, `feature name:`, `branch-name:`, or `branch name:` as providing the feature name; trim the value. Remove that directive line from the text you consider the feature description. If the trimmed value is empty, treat it as though no directive was supplied.
2. If no explicit name was provided, synthesize a concise feature name from the description before continuing:
   - Summarize the feature into a short 3–5 word phrase (Title Case, human readable).
   - Avoid punctuation except spaces and basic hyphens.
   - Use that generated phrase when passing `-FeatureName` in the next step.
3. From repo root, run the script `.specify/scripts/powershell/create-new-feature.ps1 -Json` **exactly once**:
   - Pass the cleaned feature description as positional arguments.
   - Always include `-FeatureName "<value>"` where `<value>` is either the explicit directive or the synthesized name.
   - Parse the JSON output for `BRANCH_NAME` and `SPEC_FILE`. All file paths must be absolute.
4. Load `.specify/templates/spec-template.md` to understand required sections.
5. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description while preserving section order and headings.
6. Report completion with branch name, spec file path, and readiness for the next phase.

Note: The script creates and checks out the new branch and initializes the spec file before writing.
