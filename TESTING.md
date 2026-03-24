# Manual Testing Guide

Any change that affects a slash command's behavior requires manually testing that command through an AI agent and submitting results with the PR.

## Process

1. **Identify affected commands** — use the [prompt below](#determining-which-tests-to-run) to have your agent analyze your changed files and determine which commands need testing.
2. **Set up a test project** — scaffold from your local branch (see [Setup](#setup)).
3. **Run each affected command** — invoke it in your agent, verify it completes successfully, and confirm it produces the expected output (files created, scripts executed, artifacts populated).
4. **Run prerequisites first** — commands that depend on earlier commands (e.g., `/speckit.tasks` requires `/speckit.plan` which requires `/speckit.specify`) must be run in order.
5. **Report results** — paste the [reporting template](#reporting-results) into your PR with pass/fail for each command tested.

## Setup

```bash
# Install the CLI from your local branch
cd <spec-kit-repo>
uv pip install -e .

# Initialize a test project using your local changes
specify init /tmp/speckit-test --ai <agent> --offline
cd /tmp/speckit-test

# Open in your agent
```

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
