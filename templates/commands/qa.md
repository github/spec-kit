---
description: Run systematic QA testing against the implemented feature, validating acceptance criteria through browser-driven or CLI-based testing.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before QA)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_qa` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Goal

Perform systematic quality assurance testing of the implemented feature by validating acceptance criteria from the specification against actual application behavior. Supports two modes: **Browser QA** for web applications (using Playwright or similar browser automation) and **CLI QA** for non-web applications (using test runners, API calls, and command-line validation).

## Operating Constraints

**NON-DESTRUCTIVE**: QA testing should not corrupt production data or leave the application in a broken state. Use test databases, test accounts, and cleanup procedures where applicable.

**Evidence-Based**: Every pass/fail determination must include evidence (screenshots, response payloads, console output, or test results).

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load QA Context**:
   - **REQUIRED**: Read `spec.md` for acceptance criteria, user stories, and success criteria
   - **REQUIRED**: Read `tasks.md` to identify implemented features and affected areas
   - **IF EXISTS**: Read `plan.md` for technical details, routes, and API endpoints
   - **IF EXISTS**: Read review reports in FEATURE_DIR/reviews/ for known issues to verify
   - **IF EXISTS**: Read `/memory/constitution.md` for quality standards

3. **Extract Test Scenarios**:
   From the loaded artifacts, build a structured test plan:
   - Map each user story to one or more test scenarios
   - Map each acceptance criterion to a verifiable test case
   - Identify happy paths, error paths, and edge cases
   - Prioritize scenarios: critical user flows → error handling → edge cases → performance

   Output the test plan as a numbered list:
   ```
   QA Test Plan:
   TC-001: [User Story X] - [Scenario description] - [Expected outcome]
   TC-002: [User Story Y] - [Scenario description] - [Expected outcome]
   ...
   ```

4. **Detect QA Mode**:
   Determine the appropriate testing approach based on the project:

   **Browser QA Mode** (for web applications):
   - Detect if the project is a web application (check for: package.json with dev/start scripts, index.html, web framework in plan.md)
   - Check for browser automation tools: Playwright, Puppeteer, Cypress, Selenium
   - If available, use browser automation for UI testing
   - If not available but project is a web app, use `curl`/`fetch` for API-level testing

   **CLI QA Mode** (for non-web applications):
   - Use the project's existing test runner (npm test, pytest, go test, cargo test, etc.)
   - Execute CLI commands and validate output
   - Use API calls for service validation
   - Check database state for data integrity

5. **Environment Setup**:
   - Attempt to start the application if it's not already running:
     - Check for common start commands: `npm run dev`, `npm start`, `python manage.py runserver`, `go run .`, `cargo run`, etc.
     - Use the dev/start command from `plan.md` if specified
     - Wait for the application to be responsive (health check endpoint or port availability)
   - If the application cannot be started, fall back to running the existing test suite
   - Create the QA output directories:
     - `FEATURE_DIR/qa/` for reports
     - `FEATURE_DIR/qa/screenshots/` for visual evidence (browser mode)
     - `FEATURE_DIR/qa/responses/` for API response captures (CLI mode)

6. **Execute Test Scenarios — Browser QA Mode**:
   For each test scenario in the plan:
   - Navigate to the relevant route/page
   - Perform the user actions described in the scenario
   - Capture a screenshot at each key state transition
   - Validate the expected outcome:
     - UI element presence/absence
     - Text content verification
     - Form submission results
     - Navigation behavior
     - Error message display
   - Record the result: ✅ PASS, ❌ FAIL, ⚠️ PARTIAL, ⏭️ SKIPPED
   - For failures: capture the screenshot, console errors, and network errors
   - For partial passes: document what worked and what didn't

7. **Execute Test Scenarios — CLI QA Mode**:
   For each test scenario in the plan:
   - Run the appropriate command or API call
   - Capture stdout, stderr, and exit codes
   - Validate the expected outcome:
     - Command output matches expected patterns
     - Exit codes are correct (0 for success, non-zero for expected errors)
     - API responses match expected schemas and status codes
     - Database state reflects expected changes
     - File system changes are correct
   - Record the result: ✅ PASS, ❌ FAIL, ⚠️ PARTIAL, ⏭️ SKIPPED
   - For failures: capture full output, error messages, and stack traces

8. **Run Existing Test Suites**:
   In addition to scenario-based testing, run the project's existing test suites:
   - Detect test runner: `npm test`, `pytest`, `go test ./...`, `cargo test`, `dotnet test`, `mvn test`, etc.
   - Run the full test suite and capture results
   - Report: total tests, passed, failed, skipped, coverage percentage (if available)
   - Flag any pre-existing test failures vs. new failures from implementation changes

9. **Generate QA Report**:
   Create the QA report at `FEATURE_DIR/qa/qa-{timestamp}.md` using the canonical QA report template at `templates/qa-template.md`, following it verbatim (do not add, remove, or reorder sections). The report must include:

   - **QA Summary**: Overall verdict (✅ ALL PASSED / ⚠️ PARTIAL PASS / ❌ FAILURES FOUND)
   - **Test Results Table**: Each scenario with ID, description, mode, result, evidence link
   - **Acceptance Criteria Coverage**: Matrix of criteria vs. test status
   - **Test Suite Results**: Existing test suite pass/fail summary
   - **Failures Detail**: For each failed scenario — steps to reproduce, expected vs. actual, evidence
   - **Environment Info**: OS, browser (if applicable), runtime versions, application URL
   - **Metrics**: Total scenarios, passed, failed, partial, skipped, coverage percentage

10. **Provide QA Verdict**:
    Based on results, provide one of:
    - ✅ **ALL PASSED**: All critical scenarios pass, no blockers. Safe to proceed to `/speckit.ship`
    - ⚠️ **PARTIAL PASS**: Critical paths pass but some edge cases or non-critical scenarios failed. List items.
    - ❌ **FAILURES FOUND**: Critical user flows or acceptance criteria are not met. Must fix and re-test.

## Post-QA Actions

Suggest next steps based on verdict:
- If ALL PASSED: "Run `/speckit.ship` to prepare the release"
- If PARTIAL PASS: "Address noted items if possible, then run `/speckit.ship`"
- If FAILURES FOUND: "Fix failing scenarios, then run `/speckit.qa` again to re-test"

**Check for extension hooks (after QA)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_qa` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently
