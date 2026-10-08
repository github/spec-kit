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
`speckit-github-taskstoissues/SKILL.md` in skills mode. The core
`speckit.taskstoissues` command is deprecated but remains available during migration.
Use this extension's recommended command instead. See
[integration-specific options](../../docs/reference/integrations.md#integration-specific-options).

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

Once installed they live under `.specify/extensions/github/scripts/`. The script is a trimmed twin of core's `check-prerequisites`: it resolves the project root and active feature directory, requires `plan.md` and `tasks.md`, and reports the design docs alongside them. It matches the invocation the core command makes (`--require-tasks --include-tasks`), so `spec.md` stays optional. By default, a `SPECIFY_FEATURE_DIRECTORY` override is persisted to `.specify/feature.json` so a later run without the variable resolves to the same feature. When `SPECIFY_FEATURE_NO_PERSIST=1` or `true`, the override still selects the feature for this run, but the script does not create or modify `feature.json`.

Prerequisite errors name the Spec Kit command without assuming an integration's invocation syntax. Use the syntax described under [Commands](#commands) for your integration.

## Migrating from the core `taskstoissues` command

Spec Kit is moving GitHub issue tracking out of core in three stages:

1. **Initial stage (completed)** — this extension shipped with the core `/speckit.taskstoissues` command still available.
2. **Next (current stage)** — the replacement has been available for at least one release, so the core command is now deprecated. It displays a migration warning and continues its existing workflow. It does not install or enable the extension automatically or run the replacement command.
3. **Later** — the core command will be removed in a future minor release.

To migrate, install the extension and use the namespaced command instead:

```bash
specify extension add github
```

The `generic` integration supports this migration in both commands and skills
layouts under its configured `--commands-dir`. The core command remains
available during this deprecation period until the removal stage.

| Deprecated core command   | Recommended extension command     |
| ------------------------- | --------------------------------- |
| `/speckit.taskstoissues`  | `/speckit.github.taskstoissues`   |

Apart from the core command's deprecation warning, conversion behavior is unchanged: the same feature resolution, the same `plan.md` and `tasks.md` prerequisites, the same remote validation, the same deduplication across open and closed issues, the same issue titles, and the same hook contract. This extension does **not** register `speckit.taskstoissues` as an alias, so the two commands coexist without shadowing each other while the core command still exists.

### Presets and dependent extensions

Before the core command is removed, audit references to `speckit.taskstoissues`
in presets, extension prompts, workflow steps, handoffs, and project automation.
For GitHub issue conversion, use the canonical `speckit.github.taskstoissues`
command ID and render it with the agent-specific syntax under [Commands](#commands).
Replace `__SPECKIT_COMMAND_TASKSTOISSUES__` cross-command references with
`__SPECKIT_COMMAND_GITHUB_TASKSTOISSUES__` where template rendering is supported.
Document `specify extension add github` as a setup prerequisite; the deprecation
warning does not install this dependency.

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
rather than redirecting it to the GitHub command. Existing overrides may also
hide the core deprecation warning, so communicate the migration to their users.

Keep the `before_taskstoissues` and `after_taskstoissues` hook keys unchanged;
both commands consume them. Only update a hook's command reference if it invokes
the deprecated command. Do not invoke both core and replacement commands for
the same conversion, since that also runs their hooks twice. Publish and test
updated preset/extension versions before the later core-removal release.
