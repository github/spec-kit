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
| `SPECIFY_FEATURE` | Override feature detection for non-Git repositories. Set to the feature directory name (e.g., `001-photo-albums`) to work on a specific feature when not using Git branches. Must be set in the context of the agent prior to using `/speckit.plan` or follow-up commands. |

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
