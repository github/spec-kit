# Quickstart: Validating `/speckit.converge`

This guide validates the feature end-to-end. It assumes a checkout of the `spec-kit` repo
with the local CLI installed (`uv sync --extra test && uv pip install -e .`).

## Prerequisites

- Python 3.11+, `uv`, and a supported AI coding agent.
- A test project scaffolded from your local branch:

  ```bash
  uv run specify init /tmp/converge-test --integration copilot
  cd /tmp/converge-test
  ```

- A feature taken through `specify → plan → tasks → implement` so that `spec.md`,
  `plan.md`, and `tasks.md` exist and some code has been written.

## Scenario 1 — Remaining work becomes tasks (FR-003, FR-005, FR-006; SC-001)

1. In the test feature, intentionally leave one functional requirement unimplemented in the
   code.
2. Run the command in your agent:

   ```text
   /speckit.converge
   ```

3. **Expected**: An in-session findings summary lists the unmet requirement, and a new
   `## Phase N — Convergence` section is appended to `tasks.md` containing a task that
   traces to that requirement with a `(missing)` label. No other file changes.

## Scenario 2 — Appended tasks are completed by implement (SC-005)

1. After Scenario 1, run:

   ```text
   /speckit.implement
   ```

2. **Expected**: The Convergence tasks are executed like any other task and checked off.
3. Run `/speckit.converge` again.
4. **Expected**: Fewer or zero new findings; if the gap is closed, a clean result.

## Scenario 3 — Clean converged result (FR-011; SC-002)

1. Start from a feature whose code satisfies its spec, plan, and tasks.
2. Run `/speckit.converge`.
3. **Expected**: A clean "converged" summary with counts of requirements, acceptance
   criteria, and plan decisions checked; `tasks.md` is unchanged (no empty phase added).

## Scenario 4 — Read-only boundaries (FR-008–FR-010; SC-004)

1. Record the contents/hashes of `spec.md`, `plan.md`, and the pre-existing portion of
   `tasks.md`.
2. Run `/speckit.converge`.
3. **Expected**: `spec.md` and `plan.md` are byte-for-byte unchanged; `tasks.md` differs
   only by the appended Convergence phase; no application source files were modified.

## Scenario 5 — Missing prerequisites (FR-013)

1. In a feature directory with no `tasks.md`, run `/speckit.converge`.
2. **Expected**: The command stops with a clear message instructing you to run the tasks
   command first; nothing is written.

## Scenario 6 — Cross-integration availability (FR-016, FR-017)

1. Re-init a test project for a different integration (e.g. `--integration gemini`).
2. **Expected**: The converge command is installed under that agent's command directory and
   invocable with the agent's separator; it also appears in the post-init guidance after
   the implement step.

## Automated checks (run from the spec-kit repo)

```bash
uv run python -m pytest tests/test_agent_config_consistency.py tests/integrations -q
```

**Expected**: All pass, including the `COMMAND_STEMS`/command-list assertions that now
include `converge`.

## Reporting

Capture agent, OS/shell, and pass/fail per scenario for the PR, per the manual-testing
guidance in `CONTRIBUTING.md`.
