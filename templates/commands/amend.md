---
description: Amend a completed feature specification with new edge cases, scenarios, or behavioral corrections, then cascade changes through existing tests and implementation.
handoffs:
  - label: Analyze Consistency
    agent: speckit.analyze
    prompt: Verify the amendment is consistent across all artifacts
    send: true
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Apply a targeted amendment to a feature that has already been through the full `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement` cycle. This command handles the common case where an edge case, missing scenario, or behavioral correction is discovered **after implementation** and needs to cascade through the spec, tests, and code without re-running the full pipeline.

This is a **micro-cycle**: it updates the spec as the source of truth, then cascades only the necessary changes to affected files, preserving everything that already works.

## When to Use

- **Post-implementation edge case**: A missing behavior discovered in production, during review, or through testing
- **Behavioral correction**: An existing scenario needs modification (e.g., threshold change, new validation rule)
- **New acceptance scenario**: A stakeholder or tester identifies a scenario not covered by the original spec
- **Regression prevention**: Encoding a discovered bug as a scenario before fixing it

## When NOT to Use

- **Pre-implementation changes**: Use `/speckit.clarify` instead (spec not yet implemented)
- **Large scope changes**: If the amendment affects multiple user stories or requires architectural changes, create a new feature with `/speckit.specify`
- **Constitution changes**: Use `/speckit.constitution` for governance updates

## Outline

### Phase 1: Context Loading

1. Run `{SCRIPT}` from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. Load and validate the implementation context:
   - **REQUIRED**: Read spec.md — the source of truth being amended
   - **REQUIRED**: Read tasks.md — for traceability of completed work
   - **REQUIRED**: Read plan.md — for tech stack, testing framework, and project structure
   - **IF EXISTS**: Read data-model.md — for entity context
   - **IF EXISTS**: Read contracts/ — for API specifications

3. Verify implementation state:
   - Confirm that tasks.md has completed tasks (lines matching `- [x]` or `- [X]`)
   - If NO completed tasks exist, warn: "No completed tasks found. Consider using `/speckit.clarify` for pre-implementation amendments instead." Ask user to confirm before proceeding.

4. Parse the amendment description from user input. Extract:
   - **Amendment type**: edge case | new scenario | behavioral correction | regression fix
   - **Affected user story**: Which user story (US1, US2, etc.) is impacted — infer from context or ask
   - **Behavioral statement**: The core behavior being added or changed

### Phase 2: Spec Amendment (Source of Truth)

5. Update spec.md with the amendment. Apply changes to **three sections**:

   a. **Clarifications section** — Add traceability entry:
      - Ensure `## Clarifications` section exists (create after overview section if missing)
      - Create or append to `### Amendment YYYY-MM-DD` subheading (distinct from Clarification sessions)
      - Add entry: `- [AMENDMENT] <amendment type>: <description> → Affected: <user story>`

   b. **Acceptance Scenarios** — Add the new or modified scenario:
      - Locate the affected user story section in "User Scenarios & Testing"
      - Append the new acceptance scenario using the existing format:
        `N. **Given** [initial state], **When** [action], **Then** [expected outcome]`
      - Number it sequentially after the last existing scenario for that story
      - If modifying an existing scenario, replace it and add a note: `(Amended YYYY-MM-DD: <reason>)`

   c. **Edge Cases section** — Add edge case entry if applicable:
      - If the amendment addresses an edge case, add it to the Edge Cases list
      - Format: `- <edge case description> → <handling behavior> (Added YYYY-MM-DD)`

   **Validation**: After writing, verify:
   - No duplicate scenarios exist
   - The new scenario does not contradict existing scenarios
   - Markdown structure remains valid

6. Save the updated spec.md.

### Phase 3: Locate Affected Implementation

7. Scan the project to identify files affected by this amendment:

   a. **Test files** — Search for existing test files related to the affected user story:
      - Check test directories from plan.md project structure (e.g., `tests/`, `test/`, `spec/`, `__tests__/`)
      - Look for files matching the affected user story's components
      - Identify the testing framework from plan.md (pytest, jest, mocha, rspec, junit, etc.)

   b. **Implementation files** — Search for source files that implement the affected behavior:
      - Check source directories from plan.md project structure
      - Match against file paths referenced in completed tasks for the affected user story

   c. **Build an impact map**:

      ```text
      Amendment: <description>
      Affected User Story: <USN>
      Test files to update: [list]
      Implementation files to update: [list]
      New files needed: [list, if any]
      ```

   d. Present the impact map to the user and ask: "Proceed with these changes? (yes/no)"
      - If "no", halt and suggest adjustments
      - If "yes", continue to Phase 4

### Phase 4: Test Amendment

8. Add the test for the new scenario. The approach depends on the project's testing framework (determined from plan.md):

   **General pattern** (adapt to project's testing conventions):
   - Open the identified test file(s) for the affected user story
   - Add a new test case that:
     - Describes the scenario from the spec amendment
     - Follows the project's existing test naming conventions
     - Uses the project's existing test fixtures and helpers
     - Is placed logically near related existing tests
   - If no relevant test file exists, create one following the project's test directory structure

   **Test naming**: Include a marker indicating this is a post-implementation amendment:
   - In the test name or description, include the amendment date or a reference to the spec scenario number
   - Example patterns (adapt to framework):
     - `test_<behavior>_amendment_YYYYMMDD`
     - `describe('amendment: <behavior>')`
     - `it('should <behavior> (amended YYYY-MM-DD)')`

9. Run the new test to confirm it **fails** (RED state):
   - Execute only the new test using the project's test runner
   - If the test **passes** (the behavior already works): Report that the amendment is already handled in code but was missing from the spec. Mark as "spec-only amendment" and skip Phase 5.
   - If the test **fails** (expected): Proceed to Phase 5.
   - If the test **errors** (setup issue): Fix the test setup, do not proceed to implementation until the test runs cleanly and fails for the right reason.

### Phase 5: Implementation Amendment

10. Make the targeted code change to satisfy the new test:
    - Open the identified implementation file(s)
    - Make the minimal change necessary to handle the new scenario
    - Do NOT refactor surrounding code — keep the change focused on the amendment
    - Follow the project's existing code style and patterns

11. Run the full test suite for the affected user story:
    - Execute all tests (not just the new one) for regression validation
    - **If all tests pass** (GREEN): Proceed to Phase 6
    - **If existing tests fail** (REGRESSION): Revert the implementation change. Report the conflict and suggest the user resolve it manually or reconsider the amendment.
    - **If only the new test fails**: Debug and fix the implementation. Retry up to 2 times before halting and reporting the issue.

### Phase 6: Traceability Update

12. Append an amendment entry to tasks.md:

    ```markdown
    ## Post-Implementation Amendments

    - [x] AMEND-001 [USN] <Amendment description> (YYYY-MM-DD)
      - Spec: Scenario N in spec.md User Story N
      - Test: <test file path>:<test name>
      - Code: <implementation file path>
      - Type: <edge case | new scenario | behavioral correction | regression fix>
    ```

    - If a "Post-Implementation Amendments" section already exists, append to it
    - If not, create it after the last phase section
    - Increment AMEND-NNN sequentially from any existing amendment entries

### Phase 7: Report

13. Output a structured completion report:

    ```text
    ## Amendment Complete

    | Aspect | Detail |
    |--------|--------|
    | Type | <amendment type> |
    | User Story | <affected story> |
    | Spec scenario | #N in User Story N |
    | Test | <file>:<test name> |
    | Implementation | <file>:<function/method> |
    | All tests | ✓ PASS / ✗ FAIL |

    ### Files Modified
    - spec.md (scenario added, edge case added, clarification logged)
    - <test file> (new test added)
    - <implementation file> (targeted change)
    - tasks.md (amendment entry added)

    ### Suggested Next Steps
    - Run `/speckit.analyze` to verify cross-artifact consistency
    - Review the amendment in a pull request before merging
    ```

## Behavior Rules

- **Spec is always first**: Never modify tests or code before updating spec.md. The spec is the source of truth.
- **Minimal blast radius**: Only modify files directly affected by the amendment. Do not refactor, clean up, or "improve" surrounding code.
- **Fail-safe**: If any phase encounters an unrecoverable error, halt and report clearly. Do not leave artifacts in an inconsistent state.
- **No spec, no change**: If spec.md is missing, instruct user to run `/speckit.specify` first.
- **No tasks, no amend**: If tasks.md is missing or has no completed tasks, suggest `/speckit.clarify` instead.
- **One amendment per invocation**: Handle exactly one amendment at a time. For multiple amendments, run `/speckit.amend` multiple times.
- **Preserve existing work**: Never delete or modify existing acceptance scenarios unless the amendment is explicitly a correction to a specific scenario number.
- **Test before implement**: Always write the failing test before making the implementation change (RED → GREEN).
- **Respect user control**: Present the impact map and ask for confirmation before making changes. Halt on user's request at any point.

## Context

{ARGS}
