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

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and SPEC_FILE. All file paths must be absolute.
  **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.
2. Load `templates/spec-template.md` to understand required sections.
3. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.
4. **ADDON STRATEGY ASSESSMENT & REQUIREMENTS**:
   - **First, assess addon strategy** using constitutional framework:
     * Analyze user input against single vs multi-addon indicators
     * Consider customer flexibility needs, localization, technology choices
     * Choose single addon for cohesive processes, multi-addon for complex/optional features
   - **If SINGLE ADDON strategy chosen**:
     * Define comprehensive addon with all related features
     * Include all necessary models, views, security, and functionality
     * Ensure addon serves coherent business purpose
   - **If MULTI-ADDON strategy chosen**:
     * Break into coherent feature groups (not micro-addons)
     * Map dependencies between custom addons and shared functionality
     * Classify as core (required) vs optional (customer choice, localization, integrations)
     * Define clear interfaces and data contracts between addons
     * Ensure base functionality works without optional addons
   - **For each addon identified**:
     * Business domain and coherent feature group purpose
     * Data models and relationships within the addon
     * Views and UI components specific to the addon
     * Security model (groups, rules, permissions)
     * Integration points with other addons (if multi-addon)
     * Demo data and localization needs
5. Report completion with branch name, spec file path, and readiness for the next phase.

Note: The script creates and checks out the new branch and initializes the spec file before writing.
