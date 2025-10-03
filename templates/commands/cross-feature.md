---
description: Analyze how the current feature aligns with existing features using systems thinking to identify conflicts, dependencies, and emergent behaviors.
scripts:
  sh: scripts/bash/cross-feature-check-all-features.sh --json "{ARGS}"
  ps: scripts/powershell/cross-feature-check-all-features.ps1 -Json "{ARGS}"
---

The text the user typed after `/cross-feature` in the triggering message **is** optional analysis focus. If empty, perform comprehensive alignment analysis. Assume you always have it available in this conversation even if `{ARGS}` appears literally below.

Given the current feature specification and optional analysis focus, do this:

1. Run the script `{SCRIPT}` from repo root and parse its JSON output for CURRENT_SPEC, ALL_SPECS, and ANALYSIS_FILE. All file paths must be absolute.
   **IMPORTANT** You must only ever run this script once. The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for.

2. Load `templates/cross-feature-analysis-template.md` to understand the alignment analysis framework structure.

3. Read the current feature specification from CURRENT_SPEC to understand:
   - Feature purpose and user scenarios
   - Functional requirements
   - Key entities and relationships

4. Analyze ALL_SPECS (array of paths to existing specifications) to identify ONLY actual issues:
   - **Real conflicts**: Does this feature conflict with existing features? (shared resources, timing issues, contradictory behavior)
   - **Dependencies**: Does this feature depend on or modify behavior from existing features?
   - **Side effects**: Will this feature cause unexpected problems in other features?
   - **Questions**: What needs clarification about cross-feature interactions?

5. Be concise and action-oriented:
   - **Skip empty sections**: If there are no issues in a category, remove that section entirely
   - **One-line summaries**: Issues, impacts, and fixes should each be one line
   - **Questions not essays**: Raise specific questions, don't explain systems theory
   - **Actionable only**: Only include information that requires a decision or action
   - **Target length**: 50-100 lines total, not 500+ lines

6. Write the alignment analysis to ANALYSIS_FILE using the template structure, including ONLY:
   - Impact summary (interactions, risk level, action needed)
   - Specific questions that need answers (if any)
   - Actual issues found with other features (if any)
   - Concrete recommendations (if any)
   - Remove any sections that don't apply

7. Add a single clarification line to the current spec.md file in the Requirements section:
   - Add: `- [NEEDS CLARIFICATION: Review cross-feature alignment analysis in cross-feature-analysis.md - potential conflicts identified that may require spec adjustments]`
   - This ensures `/clarify` will pick up alignment issues naturally
   - **Note:** Scripts should extract this clarification text programmatically from this template to avoid duplication

8. Report completion with analysis file path, key alignment insights discovered, and any clarification needs identified.

Note: This command should be run after `/specify` but before `/plan` to ensure systems thinking informs the technical implementation planning phase.