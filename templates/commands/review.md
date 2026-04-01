---
description: Perform a staff-level code review of implementation changes, focused on correctness, security, performance, and spec compliance.
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

**Check for extension hooks (before review)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_review` key
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

Conduct a thorough, staff-engineer-level code review of all changes made during the implementation phase. This review acts as a quality gate before shipping, catching bugs, security issues, performance regressions, and deviations from the specification. The review is **read-only** — it produces a structured report but does NOT modify code.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any source files. Output a structured review report to the reviews directory. If critical issues are found, recommend specific fixes but do NOT apply them.

**Constitution Authority**: The project constitution (`/memory/constitution.md`) defines non-negotiable quality standards. Any violation is automatically a 🔴 Blocker.

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Gather Review Context**:
   - **REQUIRED**: Read `spec.md` for functional requirements and acceptance criteria
   - **REQUIRED**: Read `plan.md` for architecture decisions and technical constraints
   - **REQUIRED**: Read `tasks.md` for the full task list and implementation scope
   - **IF EXISTS**: Read `/memory/constitution.md` for quality standards and principles
   - **IF EXISTS**: Read any existing review reports in FEATURE_DIR/reviews/ for context

3. **Identify Changes to Review**:
   - Run `git diff main --stat` (or appropriate base branch) to identify all changed files
   - If no git diff is available, use the file paths referenced in `tasks.md` as the review scope
   - Group changes by category: source code, tests, configuration, documentation
   - Prioritize review order: security-sensitive files → core logic → API surfaces → tests → config → docs

4. **Review Pass 1 — Correctness & Logic**:
   - Verify each implementation matches its corresponding requirement in `spec.md`
   - Check for off-by-one errors, null/undefined handling, boundary conditions
   - Validate error handling: are errors caught, logged, and surfaced appropriately?
   - Check for race conditions in concurrent/async code
   - Verify data validation at trust boundaries (user input, API responses, file reads)
   - Ensure state management is consistent (no orphaned state, proper cleanup)

5. **Review Pass 2 — Security**:
   - Check for injection vulnerabilities (SQL, XSS, command injection, path traversal)
   - Verify authentication and authorization checks on all protected endpoints
   - Look for hardcoded secrets, credentials, or API keys
   - Validate input sanitization and output encoding
   - Check for insecure dependencies or known vulnerability patterns
   - Verify CORS, CSP, and other security header configurations
   - Check for sensitive data exposure in logs, error messages, or responses

6. **Review Pass 3 — Performance & Scalability**:
   - Identify N+1 query patterns or unnecessary database calls
   - Check for unbounded loops, missing pagination, or large in-memory collections
   - Look for blocking operations in async contexts
   - Verify caching strategies are appropriate and cache invalidation is correct
   - Check for resource leaks (file handles, connections, event listeners)
   - Validate that performance-critical paths noted in `plan.md` are optimized

7. **Review Pass 4 — Spec Compliance & Architecture**:
   - Cross-reference each functional requirement (FR-###) against implementation
   - Verify architecture decisions from `plan.md` are followed (patterns, layers, boundaries)
   - Check API contracts match specification (request/response shapes, status codes)
   - Validate that acceptance criteria from user stories are testable and tested
   - Flag any implemented functionality NOT in the spec (scope creep)
   - Flag any spec requirements NOT implemented (missing coverage)

8. **Review Pass 5 — Test Quality**:
   - Verify test coverage for critical paths and edge cases
   - Check test assertions are meaningful (not just "doesn't throw")
   - Validate test isolation (no shared mutable state between tests)
   - Verify mock/stub usage is appropriate and doesn't hide real bugs
   - Check that acceptance criteria have corresponding test cases
   - Flag untested error paths and boundary conditions

9. **Severity Classification**:
   Apply the following severity levels to each finding:

   - 🔴 **Blocker**: Security vulnerability, data corruption risk, crashes, constitution violation, missing core functionality. **Must fix before shipping.**
   - 🟡 **Warning**: Performance issue, incomplete error handling, missing edge case coverage, test gap, architectural deviation. **Should fix before shipping.**
   - 🟢 **Suggestion**: Code clarity improvement, refactoring opportunity, documentation gap, minor style inconsistency. **Nice to fix but non-blocking.**

10. **Generate Review Report**:
    Create the review report in a new file at `FEATURE_DIR/reviews/review-{YYYYMMDD-HHMMSS}.md` using the `templates/review-template.md` review report template. Ensure the `FEATURE_DIR/reviews/` directory exists (create it if necessary). The report must include:

    - **Executive Summary**: Overall assessment (APPROVED / APPROVED WITH CONDITIONS / CHANGES REQUIRED)
    - **Findings Table**: All findings with ID, severity, file, line(s), description, recommendation
    - **Spec Coverage Matrix**: Requirements vs implementation status
    - **Test Coverage Assessment**: Coverage gaps relative to acceptance criteria
    - **Metrics**: Total findings by severity, files reviewed, spec coverage percentage
    - **Recommended Actions**: Prioritized list of fixes, grouped by severity

11. **Provide Verdict**:
    Based on findings, provide one of:
    - ✅ **APPROVED**: No blockers, minimal warnings. Safe to proceed to `/speckit.ship`
    - ⚠️ **APPROVED WITH CONDITIONS**: No blockers, but warnings should be addressed. List conditions.
    - ❌ **CHANGES REQUIRED**: Blockers found. Must fix and re-review before shipping. List blocking items.

## Post-Review Actions

Suggest next steps based on verdict:
- If APPROVED: "Run `/speckit.ship` to prepare the release"
- If APPROVED WITH CONDITIONS: "Address warnings, then run `/speckit.ship`"
- If CHANGES REQUIRED: "Fix blocker issues, then run `/speckit.review` again"

**Check for extension hooks (after review)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_review` key
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
