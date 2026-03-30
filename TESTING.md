# Testing Guide

This document is the detailed testing companion to [`CONTRIBUTING.md`](./CONTRIBUTING.md).

Use it for three things:

1. running quick automated checks before manual testing,
2. manually testing affected slash commands through an AI agent, and
3. capturing the results in a PR-friendly format.

Any change that affects a slash command's behavior requires manually testing that command through an AI agent and submitting results with the PR.

## Recommended order

1. **Sync your environment** — install the project and test dependencies.
2. **Run focused automated checks** — especially for packaging, scaffolding, agent config, and generated-file changes.
3. **Run manual agent tests** — for any affected slash commands.
4. **Paste results into your PR** — include both command-selection reasoning and manual test results.

## Quick automated checks

Run these before manual testing when your change affects packaging, scaffolding, templates, release artifacts, or agent wiring.

### Environment setup

```bash
cd <spec-kit-repo>
uv sync --extra test
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Generated package structure and content

```bash
uv run python -m pytest tests/test_core_pack_scaffold.py -q
```

This validates the generated files that CI-style packaging depends on, including directory layout, file names, frontmatter/TOML validity, placeholder replacement, `.specify/` path rewrites, and parity with `create-release-packages.sh`.

### Agent configuration and release wiring consistency

```bash
uv run python -m pytest tests/test_agent_config_consistency.py -q
```

Run this when you change agent metadata, release scripts, context update scripts, or artifact naming.

### Optional single-agent packaging spot check

```bash
AGENTS=copilot SCRIPTS=sh ./.github/workflows/scripts/create-release-packages.sh v1.0.0
```

Inspect `.genreleases/sdd-copilot-package-sh/` and the matching ZIP in `.genreleases/` when you want to review the exact packaged output for one agent/script combination.

## Manual testing process

1. **Identify affected commands** — use the [prompt below](#determining-which-tests-to-run) to have your agent analyze your changed files and determine which commands need testing.
2. **Set up a test project** — scaffold from your local branch (see [Setup](#setup)).
3. **Run each affected command** — invoke it in your agent, verify it completes successfully, and confirm it produces the expected output (files created, scripts executed, artifacts populated).
4. **Run prerequisites first** — commands that depend on earlier commands (e.g., `/speckit.tasks` requires `/speckit.plan` which requires `/speckit.specify`) must be run in order.
5. **Report results** — paste the [reporting template](#reporting-results) into your PR with pass/fail for each command tested.

## Setup

```bash
# Install the project and test dependencies from your local branch
cd <spec-kit-repo>
uv sync --extra test
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
# Ensure the `specify` binary in this environment points at your working tree so the agent runs the branch you're testing.

# Initialize a test project using your local changes
uv run specify init /tmp/speckit-test --ai <agent> --offline
cd /tmp/speckit-test

# Open in your agent
```

If you are testing the packaged output rather than the live source tree, create a local release package first as described in [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Reporting results

Paste this into your PR:

~~~markdown
## Manual test results

**Agent**: [e.g., GitHub Copilot in VS Code]  |  **OS/Shell**: [e.g., macOS/zsh]

| Command tested | Notes |
|----------------|-------|
| `/speckit.command` | |
~~~

## Determining which tests to run

Copy this prompt into your agent. Include the agent's response (selected tests plus a brief explanation of the mapping) in your PR.

~~~text
Read TESTING.md, then run `git diff --name-only main` to get my changed files.
For each changed file, determine which slash commands it affects by reading
the command templates in templates/commands/ to understand what each command
invokes. Use these mapping rules:

- templates/commands/X.md → the command it defines
- scripts/bash/Y.sh or scripts/powershell/Y.ps1 → every command that invokes that script (grep templates/commands/ for the script name). Also check transitive dependencies: if the changed script is sourced by other scripts (e.g., common.sh is sourced by create-new-feature.sh, check-prerequisites.sh, setup-plan.sh, update-agent-context.sh), then every command invoking those downstream scripts is also affected
- templates/Z-template.md → every command that consumes that template during execution
- src/specify_cli/*.py → CLI commands (`specify init`, `specify check`, `specify extension *`, `specify preset *`); test the affected CLI command and, for init/scaffolding changes, at minimum test /speckit.specify
- extensions/X/commands/* → the extension command it defines
- extensions/X/scripts/* → every extension command that invokes that script
- extensions/X/extension.yml or config-template.yml → every command in that extension. Also check if the manifest defines hooks (look for `hooks:` entries like `before_specify`, `after_implement`, etc.) — if so, the core commands those hooks attach to are also affected
- presets/*/* → test preset scaffolding via `specify init` with the preset
- pyproject.toml → packaging/bundling; test `specify init` and verify bundled assets

Include prerequisite tests (e.g., T5 requires T3 requires T1).

Output in this format:

### Test selection reasoning

| Changed file | Affects | Test | Why |
|---|---|---|---|
| (path) | (command) | T# | (reason) |

### Required tests

Number each test sequentially (T1, T2, ...). List prerequisite tests first.

- T1: /speckit.command — (reason)
- T2: /speckit.command — (reason)
~~~
