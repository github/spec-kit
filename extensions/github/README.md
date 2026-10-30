# GitHub Integration Extension

This bundled, **opt-in** extension is the home for Spec Kit's GitHub *platform* functionality. Today it provides one command, `speckit.github.taskstoissues`, which turns a feature's `tasks.md` into dependency-ordered GitHub issues.

> NOTE: `git` and `github` are deliberately separate domains. The [`git` extension](../git/README.md) owns local version-control workflow (feature branches, commits, remote detection); this extension owns interactions with the GitHub platform itself.

## Why an extension?

Creating GitHub issues is provider-specific project management, not part of the provider-neutral Spec-Driven Development lifecycle. Keeping it in a dedicated, opt-in extension lets users:

- **Choose whether to install it at all** — `specify init` does **not** install it.
- **Use a different issue tracker** without having to work around a GitHub-specific core command.
- **Depend on a stable, namespaced command** from other extensions.

## Installation

From the root of an initialized Spec Kit project:

```bash
specify extension add github
```

The `generic` (bring your own agent) integration registers this command under
its configured `--commands-dir` in both commands and skills layouts. Installing
`github` creates `speckit.github.taskstoissues.md` in commands mode or
`speckit-github-taskstoissues/SKILL.md` in skills mode. See
[integration-specific options](https://github.github.io/spec-kit/integrations/cli.html#integration-specific-options).

## Removal

```bash
specify extension remove github
```

## Commands

| Command                        | Description                                                          |
| ------------------------------ | -------------------------------------------------------------------- |
| `speckit.github.taskstoissues` | Recommended: convert tasks from `tasks.md` into dependency-ordered GitHub issues. |

> NOTE: The command ID above is canonical. Invoke it using the syntax for your integration: `/speckit.github.taskstoissues` for dot-command integrations; `/speckit-github-taskstoissues` for slash-hyphen integrations (including Forge and Cline); `$speckit-github-taskstoissues` for Codex, ZCode, or Command Code in skills mode; or `/skill:speckit-github-taskstoissues` for Kimi.

### What the command does

1. Resolves the active feature and loads its `tasks.md` (via this extension's own `resolve-tasks` script — see [Scripts](#scripts)).
2. Reads the Git remote and **stops unless it points at GitHub**.
3. Lists existing repository issues — open *and* closed — and matches their titles against the task IDs in `tasks.md` (`\bT\d{3,}\b`, so four-digit and longer IDs are handled).
4. Creates issues titled `T001: <description>` only for task IDs that do not already have one, in the repository identified by the remote.

## Hooks

This extension consumes the existing `before_taskstoissues` and `after_taskstoissues` hook points, which are read from `.specify/extensions.yml` at run time. The hook keys are unchanged from the core command, so hooks registered by other extensions — for example the `git` extension's auto-commit hooks — keep firing exactly as before.

## Requirements

- Spec Kit **0.12.17 or newer**. Extension-local `scripts/...` path rewriting arrived in
  0.12.6, but auto-registered skills did not resolve `__SPECKIT_COMMAND_*__` references
  until 0.12.17. Earlier releases cannot render this command correctly in every supported
  layout, so `specify extension add github` refuses to install below 0.12.17.
- A Git remote pointing at GitHub.
- The **GitHub MCP server** available to your coding agent, providing the `list_issues` and `issue_write` tools.

> NOTE: Agents without MCP support (for example the Pi Coding Agent out of the box) cannot run this command as intended.

## Scripts

The extension ships its own feature-resolution script in all three supported runtimes, so it is self-contained and does not reach into core:

| Runtime    | Script                                   |
| ---------- | ---------------------------------------- |
| Bash       | `scripts/bash/resolve-tasks.sh`          |
| PowerShell | `scripts/powershell/resolve-tasks.ps1`   |
| Python     | `scripts/python/resolve_tasks.py`        |

Once installed they live under `.specify/extensions/github/scripts/`. The script is a trimmed twin of core's `check-prerequisites`: it resolves the project root and active feature directory, requires `plan.md` and `tasks.md`, and reports the design docs alongside them. `spec.md` stays optional. By default, a `SPECIFY_FEATURE_DIRECTORY` override is persisted to `.specify/feature.json` so a later run without the variable resolves to the same feature. When `SPECIFY_FEATURE_NO_PERSIST=1` or `true`, the override still selects the feature for this run, but the script does not create or modify `feature.json`.

Prerequisite errors name the Spec Kit command without assuming an integration's invocation syntax. Use the syntax described under [Commands](#commands) for your integration.

## Migrating from the core `taskstoissues` command

**Breaking change:** the core command has been removed. Integration upgrades
delete old manifest-tracked `taskstoissues` command and skill files, rather than
replacing them with an updated prompt. Back up customized legacy and extension
command or skill files outside the generated directories **before** upgrading;
forcing the upgrade with `--force` also authorizes deletion of customized legacy
files. Reapply customizations only after the migration steps below, because the
upgrade can overwrite generated extension files. Installing this extension does
not restore the old invocation or provide a compatibility alias.

For existing projects, upgrading the CLI alone does not refresh the generated
core command files. After upgrading the CLI, run this from the project root:

```bash
specify integration upgrade <integration>
```

Replace `<integration>` with the installed integration key, or omit it to upgrade
the default integration. Repeat for each installed integration. If locally
modified files block the upgrade, back them up before deciding whether to
delete the legacy files with `--force`. See
[Upgrade an Integration](https://github.github.io/spec-kit/integrations/cli.html#upgrade-an-integration).

Then install the extension, **skipping this step if `github` is already
installed**, and use the namespaced command instead:

```bash
specify extension add github
```

An already-installed, enabled extension is re-registered when upgrading the
default integration only. Before using the replacement in a non-default
integration, run `specify integration use <integration>` to select it and register
the extension there. After upgrading, installing if needed, and selecting the
integration, reapply customizations from your separate backup to the namespaced
extension command. See the [public upgrade guide](https://github.github.io/spec-kit/upgrade.html#breaking-core-taskstoissues-removal)
for the complete migration sequence.

The `generic` integration supports this migration in both commands and skills
layouts under its configured `--commands-dir`.

| Core command              | Recommended extension command     |
| ------------------------- | --------------------------------- |
| `/speckit.taskstoissues`  | `/speckit.github.taskstoissues`   |

Conversion behavior is unchanged: the same feature resolution, the same `plan.md` and `tasks.md` prerequisites, the same remote validation, the same deduplication across open and closed issues, the same issue titles, and the same hook contract. This extension does **not** register `speckit.taskstoissues` as an alias.

### Presets and dependent extensions

Audit references to `speckit.taskstoissues`
in presets, extension prompts, workflow steps, handoffs, and project automation.
For GitHub issue conversion, use the canonical `speckit.github.taskstoissues`
command ID and render it with the agent-specific syntax under [Commands](#commands).
Replace `__SPECKIT_COMMAND_TASKSTOISSUES__` cross-command references with
`__SPECKIT_COMMAND_GITHUB_TASKSTOISSUES__` where template rendering is supported.
Document `specify extension add github` as a setup prerequisite.

If an extension proposal or external dependency declaration uses
`requires.commands: [speckit.taskstoissues]`, update its target to
`speckit.github.taskstoissues`. `requires.commands` is not an enforced dependency
field in the current extension manifest API, so do not rely on that declaration
to install or check the GitHub extension. Follow the supported requirements in
the [extension API reference](../EXTENSION-API-REFERENCE.md#extension-manifest).

Preset command overrides are separate from command references: an override of
`speckit.taskstoissues` does not automatically customize the namespaced GitHub
command. Review and port any needed customization, then verify the installed
command in a sample project before retiring the old override. A preset that
uses another issue tracker should retain its own provider-specific workflow
rather than redirecting it to the GitHub command.
