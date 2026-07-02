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
| `--script sh\|ps`        | Script type: `sh` (bash/zsh) or `ps` (PowerShell)                       |
| `--here`                 | Initialize in the current directory instead of creating a new one        |
| `--force`                | Force merge/overwrite when initializing in an existing directory         |
| `--ignore-agent-tools`   | Skip checks for AI coding agent CLI tools                                |
| `--preset <id>`          | Install a preset during initialization                                   |

Creates a new Spec Kit project with the necessary directory structure, templates, scripts, and AI coding agent integration files.

> [!NOTE]
> Git repository initialization and branching are managed by the **git extension**, which is not installed by default. Run `specify extension add git` after init to enable git workflows.

Use `<project_name>` to create a new directory, or `--here` (or `.`) to initialize in the current directory. If the directory already has files, use `--force` to merge without confirmation.

When `--integration` is omitted, interactive terminals prompt you to choose an integration. Non-interactive sessions, such as CI or piped runs, default to GitHub Copilot; pass `--integration <key>` to choose a different integration explicitly.

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
```

### Environment Variables

| Variable          | Description                                                              |
| ----------------- | ------------------------------------------------------------------------ |
| `SPECIFY_INIT_DIR` | Target a member project from outside its directory (e.g. a monorepo root) without `cd`, for non-interactive / CI use. Set it to the **project root** — the directory *containing* `.specify/` (relative paths resolve against the current directory). The path must exist and contain `.specify/`, otherwise the command errors and does **not** fall back to the current directory. Resolved once in the core root helper (`get_repo_root` in Bash, `Get-RepoRoot` in PowerShell), so it is honored by the core feature scripts (`/speckit.plan`, `/speckit.tasks`, …) and the Git extension's feature-branch creation, which inherit it. The `specify` CLI applies the **same** validation rules to every project-scoped subcommand (`specify integration …`, `specify extension …`, `specify workflow …`, `specify preset …`, and the rest that operate on a `.specify/` project), so those can target a member project too. When unset, Bash/PowerShell helpers keep their existing upward search; the `specify` CLI keeps its project-scoped resolver cwd-only unless a command explicitly defines broader detection (for example, bundle commands). |
| `SPECIFY_FEATURE_DIRECTORY` | Override the active feature directory *within* the resolved project (takes precedence over `.specify/feature.json`). Relative paths resolve under the project root. Combine with `SPECIFY_INIT_DIR` to pick both the project and the feature non-interactively. |
| `SPECIFY_FEATURE` | Override feature detection for non-Git repositories. Set to the feature directory name (e.g., `001-photo-albums`) to work on a specific feature when not using Git branches. Must be set in the context of the agent prior to using `/speckit.plan` or follow-up commands. |

> **Two resolution axes.** `SPECIFY_INIT_DIR` selects the **project** (which directory contains `.specify/`); `SPECIFY_FEATURE_DIRECTORY` / `.specify/feature.json` select the **feature** within that project. They are independent — project first, then feature.

> **Symlinked project roots.** `SPECIFY_INIT_DIR` relocates *where* the project is, not *how* a command treats symlinks: each command keeps its existing cwd-path stance. Commands that traverse and write project files through broad input paths (`bundle`, `workflow run <file>`) refuse a symlinked `.specify/` to preserve write confinement. Other project-scoped commands keep their existing behavior when `SPECIFY_INIT_DIR` points at a project root, which may include following a symlinked `.specify/`.

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
specify version --features --json
```

The JSON form is intended for scripts and coding agents that need to choose a
workflow based on the installed CLI's supported features.

A quick version check is also available via:

```bash
specify --version
specify -V
```
