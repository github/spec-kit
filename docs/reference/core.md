# Core Commands

The core `specify` commands handle project initialization, system checks, and version information.

## Initialize a Project

```bash
specify init [<project_name>]
```

| Option                   | Description                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| `--integration <key>`    | AI coding agent integration to use (e.g. `copilot`, `claude`, `gemini`). See the [Integrations reference](integrations.md) for all available keys |
| `--integration-options`  | Options for the integration (e.g. `--integration-options="--commands-dir .myagent/cmds"`) |
| `--script sh\|ps\|py`    | Script type: `sh` (bash/zsh), `ps` (PowerShell), or `py` (Python)       |
| `--here`                 | Initialize in the current directory instead of creating a new one        |
| `--force`                | Force merge/overwrite when initializing in an existing directory         |
| `--non-interactive`      | Never prompt; use safe documented defaults where available               |
| `--json`                 | Emit the preview machine-readable init contract; implies non-interactive behavior |
| `--ignore-agent-tools`   | Skip checks for AI coding agent CLI tools                                |
| `--preset <id>`          | Install a preset during initialization                                   |
| `--extension <spec>`     | Install an optional bundled, local, catalog, or HTTPS extension; repeatable |
| `--trust-extension-urls` | Explicitly authorize HTTPS extension installs without a trust prompt     |

Creates a new Spec Kit project with the necessary directory structure, templates, scripts, and AI coding agent integration files.

> [!NOTE]
> Git repository initialization and branching are managed by the **git extension**, which is not installed by default. Run `specify extension add git` after init to enable git workflows.

Use `<project_name>` to create a new directory, or `--here` (or `.`) to initialize in the current directory. If the directory already has files, use `--force` to merge without confirmation.

When `--integration` is omitted, interactive terminals prompt you to choose an integration. Non-interactive sessions, such as CI or piped runs, default to GitHub Copilot; pass `--integration <key>` to choose a different integration explicitly, or set `SPECKIT_INTEGRATION_DEFAULT` to change the fallback (see [Environment Variables](#environment-variables)).

### Examples

```bash
# Create a new project with an integration
specify init my-project --integration copilot

# Initialize in the current directory
specify init --here --integration copilot

# Force merge into a non-empty directory
specify init --here --force --integration copilot

# Use PowerShell scripts (Windows/cross-platform)
specify init my-project --integration copilot --script ps

# Install a preset during initialization
specify init my-project --integration copilot --preset compliance

# Initialize non-interactively with machine-readable output
specify init my-project --json
```

### Preview JSON contract

`specify init --json` is the preview machine-readable contract for project
initialization. It always behaves non-interactively, even when stdin is a TTY:
it never renders the banner, Rich panels, progress/Live output, pickers, or
confirmation prompts, and it never waits for terminal input.

JSON mode does **not** imply authorization. In particular, it does not imply
`--force`, `--trust-extension-urls`, `--ignore-agent-tools`, overwrite consent,
or any other destructive or trust decision. Supply those flags explicitly when
their documented behavior is intended. The only automatic choices are safe
defaults:

- the default integration (`copilot`, or a valid
  `SPECKIT_INTEGRATION_DEFAULT` value);
- `sh` scripts on POSIX systems or `ps` scripts on Windows.

The success object reports `integration.defaulted` and `script.defaulted` so
callers can distinguish defaults from explicit selections.

On success, stdout contains exactly one UTF-8 JSON object followed by a newline,
and stderr is empty. The object is command-specific; it does not use the
obsolete universal `schema_version` / `ok` / `result` wrapper.

```json
{
  "project": {
    "name": "my-project",
    "path": "/work/my-project",
    "operation": "created"
  },
  "integration": {
    "key": "copilot",
    "defaulted": true,
    "status": "installed"
  },
  "script": {
    "type": "sh",
    "defaulted": true
  },
  "components": {
    "shared_infrastructure": {
      "status": "installed",
      "script_type": "sh"
    },
    "workflow": {
      "id": "speckit",
      "status": "installed",
      "version": "1.0.1"
    },
    "constitution": {
      "status": "created",
      "path": "/work/my-project/.specify/memory/constitution.md",
      "source": "copied"
    },
    "script_permissions": {
      "status": "completed",
      "detail": "6 updated"
    },
    "preset": null,
    "extensions": []
  },
  "warnings": [],
  "next_steps": [
    {
      "action": "change_directory",
      "path": "/work/my-project"
    },
    {
      "action": "start_agent",
      "integration": "copilot",
      "working_directory": "/work/my-project"
    },
    {
      "action": "run_spec_kit",
      "commands": [
        "constitution",
        "specify",
        "plan",
        "tasks",
        "implement",
        "converge"
      ],
      "working_directory": "/work/my-project"
    }
  ]
}
```

`project.operation` has precise target-state semantics:

- `created`: the target directory did not exist before initialization;
- `merged`: initialization used a pre-existing directory that was not already a
  Spec Kit project;
- `reinitialized`: the target already contained a `.specify/` directory.

Optional preset, extension, workflow, constitution, or permission failures that
do not prevent initialization are represented in their component outcome and in
the structured `warnings` array. Best-effort extension and preset
re-registration failures are warning-only. No caught failure is printed as a
terminal warning or silently discarded. `next_steps` uses machine-usable
actions and paths rather than shell-formatted prose.

On failure, stdout is empty and stderr contains exactly one UTF-8 JSON error
object followed by a newline:

```json
{"error":{"code":"target_not_empty","message":"The current directory is not empty; pass --force to merge into it.","details":{"item_count":3,"path":"/work/existing"}}}
```

Stable init error codes are:

| Code | Meaning |
| ---- | ------- |
| `target_required` | Neither a project name, `.` nor `--here` was supplied |
| `conflicting_target_options` | A project name and `--here` were supplied together |
| `target_exists` | A named target directory already exists without `--force` |
| `target_not_empty` | The `--here` target is non-empty without `--force` |
| `target_not_directory` | The target exists but is not a directory |
| `target_unavailable` | The target directory cannot be inspected or created |
| `invalid_arguments` | Command-line syntax or option parsing failed before initialization |
| `invalid_integration` | The requested integration is not registered |
| `invalid_integration_options` | Integration options are unknown, malformed, conflicting, or incomplete |
| `invalid_script_type` | `--script` is not one of `sh`, `ps`, or `py` |
| `missing_agent_tool` | A required agent tool is unavailable and `--ignore-agent-tools` was not supplied |
| `extension_url_trust_required` | An HTTPS extension was requested without `--trust-extension-urls` |
| `initialization_failed` | A known fatal initialization boundary failed |
| `internal_error` | An unexpected exception was sanitized |
| `rollback_failed` | Initialization failed and cleanup of a newly created target also failed |

All target, option, required-tool, and URL-trust checks run before filesystem
mutation. URL extension trust is default-deny. If a later fatal error occurs
after a new target was created, init removes that target; a pre-existing target
is never deleted. A cleanup failure is returned as `rollback_failed` with the
original error nested in `details`.

JSON mode has the same successful side effects as human mode: it installs the
selected integration, shared templates and scripts, bundled workflow,
constitution, optional preset, and requested extensions, and it writes the
normal `.specify/` state. `--force` retains its existing merge/overwrite
behavior. Reinitialization does not perform command-to-skills or
skills-to-command layout migrations for an already installed dual-mode
integration, or move an installed generic integration to a different command
directory. JSON mode rejects those changes before mutation and reports a
machine-usable `integration_upgrade` recommendation.

**Preview compatibility:** field names, operation values, error envelope, and
error codes above are the supported preview contract. New optional fields,
component statuses, warning codes, or next-step actions may be added during the
preview; consumers should ignore unknown fields. A future stabilization will be
documented before any incompatible contract change.

### Environment Variables

| Variable          | Description                                                              |
| ----------------- | ------------------------------------------------------------------------ |
| `SPECKIT_INTEGRATION_DEFAULT` | Override the fallback integration used by `specify init` when `--integration` is omitted (interactive prompt default and non-interactive fallback). Set it to any registered integration key (e.g. `gemini`, `claude`). An unrecognized value is ignored with a warning and the built-in default (`copilot`) is used. An explicit `--integration <key>` always takes precedence. |
| `SPECIFY_INIT_DIR` | Target a member project from outside its directory (e.g. a monorepo root) without `cd`, for non-interactive / CI use. Set it to the **project root** — the directory *containing* `.specify/` (relative paths resolve against the current directory). The path must exist and contain `.specify/`, otherwise the command errors and does **not** fall back to the current directory. Resolved once in the core root helper (`get_repo_root` in Bash, `Get-RepoRoot` in PowerShell), so it is honored by the core feature scripts (`/speckit.plan`, `/speckit.tasks`, …) and the Git extension's feature-branch creation, which inherit it. The `specify` CLI applies the **same** validation rules to every project-scoped subcommand (`specify integration …`, `specify extension …`, `specify workflow …`, `specify preset …`, and the rest that operate on a `.specify/` project), so those can target a member project too. When unset, Bash/PowerShell helpers keep their existing upward search; the `specify` CLI keeps its project-scoped resolver cwd-only unless a command explicitly defines broader detection (for example, bundle commands). |
| `SPECIFY_FEATURE_DIRECTORY` | Override the active feature directory (takes precedence over `.specify/feature.json`). A relative path is joined to the project root without a containment check, so a value like `../shared-feature` still resolves outside it; an absolute path is used as-is and may likewise point outside the project root. The project root still identifies the Spec Kit project and its command/configuration context, but the selected feature directory itself is not required to live under it. Combine with `SPECIFY_INIT_DIR` to pick both the project and the feature non-interactively. |
| `SPECIFY_FEATURE` | Explicitly override the active feature **label** (e.g. `001-photo-albums`) — the identifier the core helpers report as the current feature/branch (`get_current_branch` in Bash, `Get-CurrentBranch` in PowerShell). Those helpers never inspect Git: when the variable is set they return it verbatim, and when it is unset they return an empty string. The basename fallback happens later — `get_feature_paths` / `Get-FeaturePathsEnv` substitute the resolved feature directory's basename so the reported label is still usable — so calling the named helpers directly does **not** give you that fallback. You set it yourself: the Bash and Python feature scripts only **print** a commented `export SPECIFY_FEATURE=…` / `$env:SPECIFY_FEATURE = …` hint for you to run, because a child process cannot change its parent's environment, and `/speckit.specify` persists `feature_directory` to `.specify/feature.json` instead of setting this variable. (The PowerShell feature scripts do assign `$env:SPECIFY_FEATURE`, but that only reaches you when the script runs inside your current PowerShell session.) It does **not** locate the feature directory: with only `SPECIFY_FEATURE` set, `get_feature_paths` fails with *"Feature directory not found. Set `SPECIFY_FEATURE_DIRECTORY` or run the specify command to create `.specify/feature.json`."* Use `SPECIFY_FEATURE_DIRECTORY` (above) or `.specify/feature.json` to select the directory. |
| `SPECIFY_FEATURE_NO_PERSIST` | Set to `1` or `true` to stop every core script from writing `.specify/feature.json`, even when it would otherwise persist `SPECIFY_FEATURE_DIRECTORY` on read. Useful when multiple agents run concurrently against the same checkout, each with its own `SPECIFY_FEATURE_DIRECTORY`: without it, each invocation's persist step can overwrite another agent's pinned feature directory. |

> **Two resolution axes.** `SPECIFY_INIT_DIR` selects the **project** (which directory contains `.specify/`); `SPECIFY_FEATURE_DIRECTORY` / `.specify/feature.json` select the **feature** — its default location is under `specs/` in that project, but an explicitly selected feature directory is not restricted to living inside it. They are independent — project first, then feature.
>
> **Version control.** `specify init` scaffolds a managed `.specify/.gitignore` that excludes machine-local state — `feature.json` (the current-feature pointer, rewritten on every feature switch) and per-machine extension `extensions/*/local-config.yml` overrides — while leaving everything else under `.specify/` (constitution, templates, scripts, extension config) shareable so teams stay aligned. Like the rest of `.specify/`'s shared scripts and templates, the file is tracked in the shared-infrastructure manifest: your edits are preserved on re-init and `specify init --here --force` restores the managed content. It is intentionally left in place by `specify integration uninstall`, which only removes the uninstalled agent's own files.
>
> **Symlinked project roots.** `SPECIFY_INIT_DIR` relocates *where* the project is, not *how* a command treats symlinks: each command keeps its existing cwd-path stance. Commands that traverse and write project files through broad input paths (`bundle`, `workflow run <file>`) refuse a symlinked `.specify/` to preserve write confinement. Other project-scoped commands keep their existing behavior when `SPECIFY_INIT_DIR` points at a project root, which may include following a symlinked `.specify/`.

## Naming Features with the Helper Scripts

When calling the bundled `create-new-feature` helper scripts directly, generated
names retain Unicode letters and decimal digits in UTF-8, so a description such as
`添加用户` produces `001-添加用户`. Descriptions made only of punctuation can still
produce an empty suffix such as `001-`; the scripts warn on stderr when this
happens, including during a dry run. JSON output remains parseable.

To choose a different name, keep the original description and supply a short name:

```bash
bash .specify/scripts/bash/create-new-feature.sh --json --short-name 用户管理 "添加用户"
```

The Python helper also accepts `--short-name`; the PowerShell helper uses
`-ShortName`. A supplied short name is cleaned by the same rules, so it must
contain at least one letter or digit. For non-ASCII names, the Bash helper needs
an installed UTF-8 locale and a Python 3 interpreter for Unicode classification.
ASCII input, including tabs and newlines, is sanitized without either requirement.
If `LC_ALL` is non-empty, Bash uses that locale rather than selecting another:
Unicode names fail with an error if the selected locale is not usable for UTF-8
names. With `LC_ALL` unset or empty, Bash selects an installed UTF-8 locale even
when `LANG` or `LC_CTYPE` names a non-UTF-8 locale.
ASCII capitals are lowercased; non-ASCII letter casing is preserved across the
script variants.

## Check Installed Tools

```bash
specify check
```

Checks that CLI-based AI coding agents are available on your system. IDE-based agents are skipped since they don't require a CLI tool.

This command stays offline. If a command behaves like an older Spec Kit version or an expected CLI feature is missing, run `specify self check` to check whether your local CLI is behind the latest release.

## Version Information

```bash
specify version
```

Displays the Spec Kit CLI version, Python version, platform, and architecture.

To inspect local CLI capabilities without checking the network:

```bash
specify version --features
```

To print complete version, runtime, system, and feature information as JSON,
use:

```bash
specify version --json
```

Combining `--features` and `--json` emits the same complete JSON output;
`--features` does not filter the result in JSON mode. If OpenSSL information
is unavailable, `runtime.openssl` is `null`.
Successful JSON output is written only to stdout. Failures leave stdout empty
and write one sanitized JSON error object to stderr.

A quick version check is also available via:

```bash
specify --version
specify -V
```

## Experimental MCP Server

```bash
specify mcp
```

Starts the experimental stdio-only MCP server. The initial server exposes only
the stable `version` JSON command through generic list, describe, and run tools.
See the [MCP Server reference](mcp.md) for the tool names, result contract, and
current limitations.
