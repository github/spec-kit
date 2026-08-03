---
description: "Validate that a previously fixed bug is resolved and record the verification report"
---

# Test Bug Fix

Validate that the fix recorded by `__SPECKIT_COMMAND_BUG_FIX__` actually resolves the bug described by `__SPECKIT_COMMAND_BUG_ASSESS__`. The output is a verification report at `.specify/bugs/<slug>/test.md`.

## User Input

```text
$ARGUMENTS
```

The user input should identify the bug to validate. Accept any of:

- `slug=<bug-slug>` or `--slug <bug-slug>` or a bare slug-like token.
- A path that contains the slug (e.g. `.specify/bugs/login-timeout/`).
- **Nothing** — fall back to context (see below).

## Slug Resolution

Resolve `BUG_SLUG` in this order, stopping at the first match:

1. **Explicit user input** — a slug passed in `$ARGUMENTS` (any of the forms above).
2. **Conversation context** — if the current session has just run `__SPECKIT_COMMAND_BUG_ASSESS__` or `__SPECKIT_COMMAND_BUG_FIX__`, the slug it reported is the working slug. Reuse it without re-prompting. Confirm it by checking that `.specify/bugs/<slug>/fix.md` exists; if it does not, fall through.
3. **Single candidate on disk** — list `.specify/bugs/*/fix.md`. If exactly one bug has a `fix.md`, use it.
4. **Disambiguate**:
   - **Interactive mode**: ask the user which bug to validate and list the candidates.
   - **Automated mode**: stop with an error listing the candidates. Do not guess.

Once resolved, set `BUG_SLUG` and `BUG_DIR = .specify/bugs/<BUG_SLUG>`, and briefly state in your reply which resolution path was used (explicit / from context / single candidate / asked).

## Prerequisites

- `BUG_DIR/assessment.md` MUST exist.
- `BUG_DIR/fix.md` MUST exist. If not, stop and instruct the user to run `__SPECKIT_COMMAND_BUG_FIX__` first.
- If `BUG_DIR/test.md` already exists, ask the user whether to overwrite it (interactive mode) or refuse (automated mode).
- Read both `assessment.md` and `fix.md` in full so you know:
  - The original symptom and reproduction steps (from `assessment.md`).
  - The actual code changes and tests added (from `fix.md`).

## Execution

1. **Plan the validation**
   - Decide which checks prove the bug is gone:
     - Re-run the reproduction steps from the assessment (or their automated equivalent).
     - Run the tests added or updated in the fix.
     - Run any broader regression suite that touches the changed files.
   - Decide which checks prove nothing was broken:
     - Existing test suites for the changed modules.
     - Lint / type-check if the project uses them.

2. **Run the checks**
   - Execute each planned check. Capture command, exit status, and a short excerpt of relevant output (last few lines, or the failing assertion).
   - If a check is destructive, network-dependent, or expensive, skip it and record it as `skipped` with a reason; do not run it without explicit user consent.
   - If you cannot run a check at all (missing tooling, no test framework configured), record it as `not-run` with a reason instead of fabricating a result.

3. **Judge the outcome**
   - Mark the fix as:
     - **verified** — all critical checks pass and the original symptom no longer reproduces.
     - **partial** — the original symptom is gone but unrelated regressions appeared, or some checks are inconclusive.
     - **failed** — the symptom still reproduces or the regression suite is broken by the fix.
   - Do not over-claim. If reproduction was not actually performed (e.g., the bug required a production environment), say so explicitly.

4. **Write the verification report**

   Write to `BUG_DIR/test.md` using this structure:

   ```markdown
   # Bug Verification: <short title>

   - **Slug**: <BUG_SLUG>
   - **Tested**: <ISO 8601 date>
   - **Assessment**: ./assessment.md
   - **Fix**: ./fix.md
   - **Result**: verified | partial | failed

   ## Summary

   <One or two sentences: does the bug reproduce, did the fix hold, were any regressions found.>

   ## Checks Performed

   | Check | Command / Action | Result | Notes |
   |-------|------------------|--------|-------|
   | Reproduction (post-fix) | <command or manual steps> | pass / fail / skipped / not-run | <short note> |
   | New / updated tests | `<command>` | pass / fail | <short note> |
   | Regression suite | `<command>` | pass / fail / skipped | <short note> |
   | Lint / type-check | `<command>` | pass / fail / skipped | <short note> |

   ## Output Excerpts

   <Short snippets of relevant output (e.g., final summary line of a test run, the failing assertion). Keep it tight — no full logs.>

   ## Residual Risks

   - <known limitation, environment not covered, etc.>

   ## Recommendation

   <One paragraph. Examples:>
   - "Close the bug — verified end-to-end."
   - "Hold — reproduction inconclusive; needs verification in staging."
   - "Reopen — symptom still reproduces; rerun `__SPECKIT_COMMAND_BUG_ASSESS__`."
   ```

5. **Report back** with:
   - The slug and `BUG_DIR/test.md` path.
   - The result (`verified`, `partial`, `failed`).
   - If the result is `failed`, recommend re-running `__SPECKIT_COMMAND_BUG_ASSESS__` with the new evidence captured in `test.md`.

## Guardrails

- This command MUST NOT modify source code. It only runs checks and writes inside `.specify/bugs/<slug>/`.
- Never overwrite an existing `test.md` without confirmation.
- Never mark a fix as `verified` based on tests alone if the original assessment listed a reproduction that you did not actually exercise — downgrade to `partial` and say so.
