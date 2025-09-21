---
description: Create a new local issue specification using spec-kit templates for issue-resolution flow.
scripts:
  sh: scripts/bash/create-issue.sh --json "{ARGS}"
  ps: scripts/powershell/create-issue.ps1 -Json "{ARGS}"
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

The text the user typed after `/issue` in the triggering message **is** the issue description. Assume you always have it available in this conversation even if `{ARGS}` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that issue description, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for ISSUE_NUM, ISSUE_DIR, and ISSUE_SPEC. All file paths must be absolute.
  **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

2. Load `templates/issue-template.md` to understand the required issue structure and sections.

3. Write the issue specification to ISSUE_SPEC using the template structure, replacing placeholders with concrete details derived from the issue description (arguments) while preserving section order and headings.

4. Report completion with issue number, issue directory path, and readiness for the next phase.

Note: The script creates a new issue directory in `issues/` following the pattern `issues/###-issue-name/` and initializes the issue specification file. This follows the same pattern as feature specifications but for issue-resolution flow.
