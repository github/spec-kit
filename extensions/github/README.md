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
`speckit-github-taskstoissues/SKILL.md` in skills mode. It also installs the
deprecated `speckit.taskstoissues` compatibility alias. Neither invocation is
installed by core. Use the namespaced command for new workflows. See
[integration-specific options](../../docs/reference/integrations.md#integration-specific-options).

## Removal

```bash
specify extension remove github
```

## Commands

| Command                        | Description                                                          |
| ------------------------------ | -------------------------------------------------------------------- |
| `speckit.github.taskstoissues` | Recommended: convert tasks from `tasks.md` into dependency-ordered GitHub issues. |
| `speckit.taskstoissues` | Deprecated compatibility alias; warns and runs the same workflow and hooks once. |

> NOTE: The command ID above is canonical. Invoke it using the syntax for your integration: `/speckit.github.taskstoissues` for dot-command integrations; `/speckit-github-taskstoissues` for slash-hyphen integrations (including Forge and Cline); `$speckit-github-taskstoissues` for Codex, ZCode, or Command Code in skills mode; or `/skill:speckit-github-taskstoissues` for Kimi.

### What the command does

1. Resolves the active feature and loads its `tasks.md` (via this extension's own `resolve-tasks` script — see [Scripts](#scripts)).
2. Reads the Git remote and **stops unless it points at GitHub**.
3. Lists existing repository issues — open *and* closed — and matches their titles against the task IDs in `tasks.md` (`\bT\d{3,}\b`, so four-digit and longer IDs are handled).
4. Creates issues titled `T001: <description>` only for task IDs that do not already have one, in the repository identified by the remote.

## Hooks

This extension consumes the existing `before_taskstoissues` and `after_taskstoissues` hook points, which are read from `.specify/extensions.yml` at run time. The hook keys are unchanged from the core command, so hooks registered by other extensions — for example the `git` extension's auto-commit hooks — keep firing exactly as before.

## Requirements

- Spec Kit **1.2.3.dev0 or newer** from the core-removal development line.
  Earlier hosts still own `speckit.taskstoissues` and reject the compatibility
  alias. Extension 1.0.2 remains the pre-removal replacement for those hosts.
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

**Breaking change:** `taskstoissues` has been removed from core after the
replacement shipped in 1.0.13 and deprecation shipped in 1.1.3. This removal
is intended for the next minor release, not a patch release. New projects do
not receive either invocation unless this extension is explicitly installed.

After upgrading to a CLI containing the removal, run from the project root:

```bash
specify integration upgrade <integration>
specify extension add github
```

Replace `<integration>` with the installed integration key, or omit it to
refresh the default integration. Upgrade first to retire old core artifacts
before installing the alias; generic registration refuses unowned collisions.
If `github` is already installed, run
`specify extension update github` instead of `add`. Integration upgrade
removes manifest-tracked obsolete core files, then re-registers enabled
extensions for the default integration, including the compatibility alias.
Upgrading the CLI alone does not refresh generated files. Inspect local edits
before deciding whether to use `--force`. Projects without an integration
manifest need manual review and cleanup of old generated commands; `upgrade`
reports that it cannot refresh them.

The `generic` integration supports both commands and skills layouts under its
configured `--commands-dir`. For multiple installed integrations, upgrade each
one; use `specify integration use <integration>` to register extension commands
when changing the default. See [Upgrade an Integration](../../docs/reference/integrations.md#upgrade-an-integration).

| Deprecated compatibility alias | Canonical extension command |
| ------------------------- | --------------------------------- |
| `/speckit.taskstoissues`  | `/speckit.github.taskstoissues`   |

The extension owns both invocations. The alias warns and executes the same
workflow once; it does not invoke the canonical command a second time.
Conversion behavior is unchanged: feature resolution, `plan.md` and `tasks.md`
prerequisites, GitHub remote validation, open/closed issue deduplication,
issue titles, and hooks are preserved. Removing the extension removes its
unchanged canonical and alias artifacts without affecting core SDD commands.

### Presets and dependent extensions

Audit references to `speckit.taskstoissues`
in presets, extension prompts, workflow steps, handoffs, and project automation.
For GitHub issue conversion, use the canonical `speckit.github.taskstoissues`
command ID and render it with the agent-specific syntax under [Commands](#commands).
Replace `__SPECKIT_COMMAND_TASKSTOISSUES__` cross-command references with
`__SPECKIT_COMMAND_GITHUB_TASKSTOISSUES__` where template rendering is supported.
Document `specify extension add github` as a setup prerequisite; core never
installs this dependency.

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
hide the compatibility warning, so communicate the migration to their users.

Keep the `before_taskstoissues` and `after_taskstoissues` hook keys unchanged;
the canonical command and alias consume them. Only update a hook's command
reference if it invokes the deprecated alias. Do not invoke both names for
the same conversion, since that also runs their hooks twice.

Related proposals such as [milestone grouping (github/spec-kit#4370)](https://github.com/github/spec-kit/issues/4370)
should target `speckit.github.taskstoissues`, not a core command.
[Jira support (github/spec-kit#2223)](https://github.com/github/spec-kit/issues/2223)
belongs in a provider-specific extension rather than an override of a
GitHub-specific core command. Existing third-party presets targeting the old
core name need their authors to port and verify those overrides.
