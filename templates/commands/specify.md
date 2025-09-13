---
description: Create or update the feature specification from a natural language feature description.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

Given the feature description provided as an argument, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME, SPEC_FILE, and TEST_CASES_FILE. All file paths must be absolute.
2. Load `templates/spec-template.md` to understand required sections.
3. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.
4. Load `templates/test-cases-template.md` to understand test case structure.
5. Generate test cases in TEST_CASES_FILE by:
   - Analyzing each functional requirement (FR-001, FR-002, etc.) from the specification
   - Analyzing each non-functional requirement (NFR-001, NFR-002, etc.) from the specification
   - Creating Given-When-Then test scenarios for each requirement
   - Categorizing tests by type (Critical Path, Edge Case, Integration, Performance, Security)
   - Mapping requirement IDs to test case IDs (FR-001 → TC-001)
   - Flagging any untestable or vague requirements for clarification
6. Report completion with branch name, spec file path, test cases file path, and readiness for the next phase.

Note: The script creates and checks out the new branch and initializes both the spec file and test-cases file before writing.
