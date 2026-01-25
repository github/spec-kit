---
description: Create or update the project constitution from interactive or provided principle inputs, ensuring all dependent templates stay in sync.
handoffs: 
  - label: Build Specification
    agent: speckit.specify
    prompt: Implement the feature specification based on the updated constitution. I want to build...
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Memory Provider Detection

Before performing any memory operations, detect the memory provider:

1. Check for `.specify/config.json` in repo root
2. Parse JSON and read `memory.provider`:
   - If `"hindsight"`: Use Hindsight MCP tools with `bank_id` from `memory.hindsight.bank_id`
   - If `"local"` or config missing: Use `/memory/constitution.md` file
3. If Hindsight configured but MCP tools unavailable: Warn user and fallback to local file

Store the detected mode for use in later steps.

## Hindsight Mode: Reading Existing Constitution

When updating an existing constitution in Hindsight mode, first retrieve current state:

```
mcp__hindsight__recall(
  query: "project constitution principles governance version",
  bank_id: {bank_id from config}
)
```

This provides context about existing principles before making changes.

## Outline

You are updating the project constitution at `/memory/constitution.md`. This file is a TEMPLATE containing placeholder tokens in square brackets (e.g. `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`). Your job is to (a) collect/derive concrete values, (b) fill the template precisely, and (c) propagate any amendments across dependent artifacts.

Follow this execution flow:

1. Load the existing constitution template at `/memory/constitution.md`.
   - Identify every placeholder token of the form `[ALL_CAPS_IDENTIFIER]`.
   **IMPORTANT**: The user might require less or more principles than the ones used in the template. If a number is specified, respect that - follow the general template. You will update the doc accordingly.

2. Collect/derive values for placeholders:
   - If user input (conversation) supplies a value, use it.
   - Otherwise infer from existing repo context (README, docs, prior constitution versions if embedded).
   - For governance dates: `RATIFICATION_DATE` is the original adoption date (if unknown ask or mark TODO), `LAST_AMENDED_DATE` is today if changes are made, otherwise keep previous.
   - `CONSTITUTION_VERSION` must increment according to semantic versioning rules:
     - MAJOR: Backward incompatible governance/principle removals or redefinitions.
     - MINOR: New principle/section added or materially expanded guidance.
     - PATCH: Clarifications, wording, typo fixes, non-semantic refinements.
   - If version bump type ambiguous, propose reasoning before finalizing.

3. Draft the updated constitution content:
   - Replace every placeholder with concrete text (no bracketed tokens left except intentionally retained template slots that the project has chosen not to define yet—explicitly justify any left).
   - Preserve heading hierarchy and comments can be removed once replaced unless they still add clarifying guidance.
   - Ensure each Principle section: succinct name line, paragraph (or bullet list) capturing non‑negotiable rules, explicit rationale if not obvious.
   - Ensure Governance section lists amendment procedure, versioning policy, and compliance review expectations.

4. Consistency propagation checklist (convert prior checklist into active validations):
   - Read `/templates/plan-template.md` and ensure any "Constitution Check" or rules align with updated principles.
   - Read `/templates/spec-template.md` for scope/requirements alignment—update if constitution adds/removes mandatory sections or constraints.
   - Read `/templates/tasks-template.md` and ensure task categorization reflects new or removed principle-driven task types (e.g., observability, versioning, testing discipline).
   - Read each command file in `/templates/commands/*.md` (including this one) to verify no outdated references (agent-specific names like CLAUDE only) remain when generic guidance is required.
   - Read any runtime guidance docs (e.g., `README.md`, `docs/quickstart.md`, or agent-specific guidance files if present). Update references to principles changed.

5. Produce a Sync Impact Report (prepend as an HTML comment at top of the constitution file after update):
   - Version change: old → new
   - List of modified principles (old title → new title if renamed)
   - Added sections
   - Removed sections
   - Templates requiring updates (✅ updated / ⚠ pending) with file paths
   - Follow-up TODOs if any placeholders intentionally deferred.

6. Validation before final output:
   - No remaining unexplained bracket tokens.
   - Version line matches report.
   - Dates ISO format YYYY-MM-DD.
   - Principles are declarative, testable, and free of vague language ("should" → replace with MUST/SHOULD rationale where appropriate).

7. Save the constitution based on detected memory provider:

   **Local Mode** (default):
   - Write the completed constitution to `/memory/constitution.md` (overwrite)

   **Hindsight Mode** (when `memory.provider == "hindsight"`):
   - First, write to `/memory/constitution.md` for local reference (always keep a local copy)
   - Then store each component in Hindsight using `mcp__hindsight__retain`:

   a. **Project metadata**:
      ```
      mcp__hindsight__retain(
        content: "Project: {PROJECT_NAME}, Version: {CONSTITUTION_VERSION}, Ratified: {RATIFICATION_DATE}, Last Amended: {LAST_AMENDED_DATE}",
        context: "constitution-metadata",
        bank_id: {bank_id from config}
      )
      ```

   b. **Each principle** (repeat for all principles):
      ```
      mcp__hindsight__retain(
        content: "Principle {N}: {PRINCIPLE_NAME}\n{DESCRIPTION}\nRationale: {RATIONALE}",
        context: "constitution-principle",
        bank_id: {bank_id from config}
      )
      ```

   c. **Governance rules**:
      ```
      mcp__hindsight__retain(
        content: "{Full governance section text}",
        context: "constitution-governance",
        bank_id: {bank_id from config}
      )
      ```

   **Fallback**: If Hindsight tools fail (e.g., MCP not connected), warn user and confirm local save succeeded.

8. Output a final summary to the user with:
   - New version and bump rationale.
   - Any files flagged for manual follow-up.
   - Suggested commit message (e.g., `docs: amend constitution to vX.Y.Z (principle additions + governance update)`).

Formatting & Style Requirements:

- Use Markdown headings exactly as in the template (do not demote/promote levels).
- Wrap long rationale lines to keep readability (<100 chars ideally) but do not hard enforce with awkward breaks.
- Keep a single blank line between sections.
- Avoid trailing whitespace.

If the user supplies partial updates (e.g., only one principle revision), still perform validation and version decision steps.

If critical info missing (e.g., ratification date truly unknown), insert `TODO(<FIELD_NAME>): explanation` and include in the Sync Impact Report under deferred items.

Do not create a new template; always operate on the existing `/memory/constitution.md` file.
