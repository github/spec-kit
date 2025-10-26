---
description: Create or update the feature specification from a natural language feature description.
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

## Strict Contract

- **Required Inputs**
  - `feature_description`: Provided via `$ARGUMENTS` (may be empty when updating an existing feature).
- **Allowed Tools**
  - Invoke `{SCRIPT}` exactly once to hydrate feature context.
  - Read/write files within the feature directory returned by the script.
- **Outputs**
  - Write `spec.md` using `templates/spec-template.md`.
  - Write/update `checklists/requirements.md` for quality validation.
  - Respond with a single JSON code block matching the schema:

    ```json
    {
      "status": "success" | "error",
      "branch": "<branch-name>",
      "spec_path": "<absolute-path>",
      "checklist_path": "<absolute-path>",
      "summary": {
        "highlights": ["<key takeaway>", "..."]
      },
      "clarifications": [
        {
          "id": "Q1",
          "question": "<clarification question>",
          "context": "<section reference>",
          "impact": "<why it matters>"
        }
      ]
    }
    ```

- **Idempotency**
  - Re-running with the same description must update `spec.md` in place without duplicating sections or regenerating branch metadata.
- **Stop Conditions**
  - Stop after writing files and emitting the JSON summary. Do not request user replies or spawn additional workflows.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Execution Flow

1. **Hydrate Feature Context**
   - Run `{SCRIPT}` from the repository root to obtain `BRANCH_NAME`, `FEATURE_DIR`, `SPEC_FILE`, and `CHECKLIST_FILE`.
   - Shell guidance:
     - **Bash**: Prefer double quotes (e.g., `"I'm Groot"`). Escape embedded quotes as `\"` when required.
     - **PowerShell**: Wrap arguments in double quotes and escape embedded quotes by doubling them (e.g., `""I'm Groot""`).
   - Execute the script exactly once.

2. **Load Authoritative Artifacts**
   - Read `templates/spec-template.md` and `/memory/constitution.md` to understand required sections and principles.
   - If `spec.md` already exists, parse it to retain resolved clarifications and history sections.

3. **Draft Specification**
   - Transform the feature description into a complete specification adhering to the template headings.
   - Populate new sections: Assumptions, Out of Scope, Risks, Open Questions, Traceability Matrix.
   - Cap `[NEEDS CLARIFICATION]` markers at **three**. Prefer informed assumptions recorded in the Assumptions section when reasonable.

4. **Quality Validation**
   - Generate `checklists/requirements.md` using the checklist format defined below.
   - Evaluate each checklist item against the drafted spec. Update the spec until all non-clarification issues are resolved.
   - Extract up to three unresolved clarifications for inclusion in the output JSON.

5. **Persist Artifacts**
   - Write the finalized `spec.md` and `checklists/requirements.md` (create directories as needed).
   - Ensure Markdown front matter remains at the top of each file.

6. **Respond**
   - Summarize key highlights and list clarification questions (if any) using the contract schema.

## Checklist Template

```markdown
# Specification Quality Checklist: [FEATURE NAME]

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: [DATE]
**Feature**: [Link to spec.md]

## Content Quality
- [ ] No implementation details
- [ ] Focused on user and business value
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

## Requirement Completeness
- [ ] No `[NEEDS CLARIFICATION]` markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable and outcome-focused
- [ ] Acceptance scenarios cover primary flows and edge cases

## Scope Discipline
- [ ] Assumptions documented and defensible
- [ ] Out-of-scope items explicitly listed
- [ ] Risks include owner and mitigation
- [ ] Open questions tracked with owners

## Notes
- [Document follow-ups or remaining risks]
```

## Authoring Principles

- Focus on **what** and **why**; avoid implementation details.
- Prefer informed assumptions over clarifications when impact is low.
- Keep success criteria measurable and technology agnostic.
- Maintain consistency with constitution principles and previously resolved clarifications.
