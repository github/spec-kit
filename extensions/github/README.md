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

## Removal

```bash
specify extension remove github

# Or keep it installed but inert
specify extension disable github
specify extension enable github
```

## Commands

| Command                        | Description                                                          |
| ------------------------------ | -------------------------------------------------------------------- |
| `speckit.github.taskstoissues` | Convert tasks from `tasks.md` into dependency-ordered GitHub issues. |

> NOTE: The command ID above is canonical. Invoke it using the syntax for your integration: `/speckit.github.taskstoissues` for dot-command integrations; `/speckit-github-taskstoissues` for hyphen/skills integrations (including Forge and Cline); `$speckit-github-taskstoissues` for Codex or ZCode in skills mode; or `/skill:speckit-github-taskstoissues` for Kimi.

### What the command does

1. Resolves the active feature and loads its `tasks.md` (via this extension's own `resolve-tasks` script — see [Scripts](#scripts)).
2. Reads the Git remote and **stops unless it points at GitHub**.
3. Lists existing repository issues — open *and* closed — and matches their titles against the task IDs in `tasks.md` (`\bT\d{3,}\b`, so four-digit and longer IDs are handled).
4. Creates issues titled `T001: <description>` only for task IDs that do not already have one, in the repository identified by the remote.

## Hooks

This extension consumes the existing `before_taskstoissues` and `after_taskstoissues` hook points, which are read from `.specify/extensions.yml` at run time. The hook keys are unchanged from the core command, so hooks registered by other extensions — for example the `git` extension's auto-commit hooks — keep firing exactly as before.

## Requirements

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

Once installed they live under `.specify/extensions/github/scripts/`. The script is a trimmed twin of core's `check-prerequisites`: it resolves the project root and active feature directory, requires `tasks.md`, and reports the design docs alongside it. It performs none of core's `plan.md`/`spec.md` gating, and it never writes `.specify/feature.json`.

## Migrating from the core `taskstoissues` command

Spec Kit is moving GitHub issue tracking out of core in three stages:

1. **Now** — this extension is available, and the core `/speckit.taskstoissues` command remains available and unchanged. Nothing breaks if you do nothing.
2. **Next** — the core command is deprecated once the replacement has been available for a release.
3. **Later** — the core command is removed in a minor release.

To migrate, install the extension and use the namespaced command instead:

```bash
specify extension add github
```

| Before                    | After                             |
| ------------------------- | --------------------------------- |
| `/speckit.taskstoissues`  | `/speckit.github.taskstoissues`   |

Behavior is unchanged: the same remote validation, the same deduplication across open and closed issues, the same issue titles, and the same hook contract. This extension does **not** register `speckit.taskstoissues` as an alias, so the two commands coexist without shadowing each other while the core command still exists.
