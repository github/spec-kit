---
description: "Prepare a project for autopilot runs: install the workflows, configure the verification gate from the project's own test, lint and type commands, prove it is green, and commit the setup"
---

# Autopilot Setup

Fill the autopilot's **verification gate** with this project's real commands and prove the gate passes on the current commit. An unattended pipe can only exit through this gate, so a gate that is empty, wrong, or already red makes every later run meaningless.

## User Input

```text
$ARGUMENTS
```

Treat the input as extra instructions (for example "lint is `make lint`, skip type checks"). It may be empty.

## Files

- Config: `.specify/extensions/autopilot/autopilot-config.yml` (created by `specify extension add autopilot`; if missing, copy `.specify/extensions/autopilot/config-template.yml` to that path first).
- Gate runner: `python3 .specify/extensions/autopilot/scripts/python/autopilot.py` (use `python` where `python3` is not available).

## Steps

0. **Install the workflows.** If `.specify/workflows/autopilot-epic/workflow.yml` or `.specify/workflows/autopilot/workflow.yml` is missing, run `specify workflow add autopilot-epic` and `specify workflow add autopilot`. The pipes run `autopilot-epic` headlessly; `autopilot` is the same conductor for CI and terminal use. If `specify` is not on PATH, stop and say so.

1. **Find the commands, do not invent them.** Read, in this order, whatever exists: `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `CONTRIBUTING.md`, `DEVELOPMENT.md`, `README.md`, then the build manifests (`package.json` scripts, `pyproject.toml`, `Makefile`, `justfile`, `Cargo.toml`, `go.mod`, `build.gradle`, `pom.xml`, `.github/workflows/*.yml`). Collect the commands the project documents or CI runs for: **tests**, **lint/format check**, **type check**, and any project-specific verification (schema validation, docs build, secret scan, plugin validation).
   - Prefer the exact command CI runs over a guess.
   - Use non-interactive, non-watch, check-only forms (`--check`, `--ci`, `run` not `watch`, no auto-fix).
   - Each command must run from the repository root and exit non-zero on failure.

2. **Write `gate.checks`.** One entry per command, each with a short `name` and the `run` command, for example:

   ```yaml
   gate:
     checks:
       - name: test
         run: "uv run pytest -q"
       - name: lint
         run: "uv run ruff check ."
       - name: types
         run: "uv run mypy src"
   ```

   Edit only `gate.checks` unless the user input asks for more. If dependencies must be installed in a fresh git worktree before these commands work (for example `npm ci` or `uv sync`), set `run.setup` to that command.

3. **Prove it.** Run `python3 .specify/extensions/autopilot/scripts/python/autopilot.py checks` and read the JSON. Every check must pass on the current commit.
   - If a check fails because the command is wrong, fix the command and run again.
   - If a check fails because the project itself is red, **do not weaken or delete the check** and do not change application code. Report it: the autopilot must not start until the base is green.

4. **Ask about the limits.** Show the current `pipe.max_iterations`, `run.max_parallel`, `run.timeout_minutes` and `run.max_agent_calls` (the cost ceiling for unattended runs) and change any the user wants changed.

5. **Check autonomy conflicts.** If the project's agent instructions would stop an unattended pipe (for example a `CLAUDE.md` rule like "one skill per turn, then stop", or "always ask before editing"), show the rule and propose an exception scoped to autopilot runs. Edit it only with the user's yes.

6. **Offer to commit.** Pipes run in git worktrees created from commits. List what this setup created or changed (`.specify/`, the agent's command or skill folder, the config, and any instruction-file edit) and ask whether to commit it. Commit only those paths, only with the user's yes, and never anything that looks like a secret.

7. **Report** a table of the configured checks with pass/fail, any `run.setup` command, the limits, and the next step: put requirements under `docs/requirements/` (or anywhere) and run `__SPECKIT_COMMAND_AUTOPILOT_RUN__`.

## Rules

- Never push, and never modify application code or tests in this command. Commit only as in step 6.
- Never add a check that always passes (`true`, `exit 0`, `|| true`). A gate that cannot fail is worse than no gate.
