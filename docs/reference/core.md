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
| `--no-git`               | Skip git repository initialization                                       |
| `--ignore-agent-tools`   | Skip checks for AI coding agent CLI tools                                |
| `--preset <id>`          | Install a preset during initialization                                   |
| `--branch-numbering`     | Branch numbering strategy: `sequential` (default) or `timestamp`         |

Creates a new Spec Kit project with the necessary directory structure, templates, scripts, and AI coding agent integration files.

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

# Skip git initialization
specify init my-project --integration copilot --no-git

# Install a preset during initialization
specify init my-project --integration copilot --preset compliance

# Use timestamp-based branch numbering (useful for distributed teams)
specify init my-project --integration copilot --branch-numbering timestamp
```

### Environment Variables

| Variable          | Description                                                              |
| ----------------- | ------------------------------------------------------------------------ |
| `SPECIFY_FEATURE` | Override feature detection for non-Git repositories. Set to the feature directory name (e.g., `001-photo-albums`) to work on a specific feature when not using Git branches. Must be set in the context of the agent prior to using `/speckit.plan` or follow-up commands. |

## Check Installed Tools

```bash
specify check
```

Checks that required tools are available on your system: `git` and any CLI-based AI coding agents. IDE-based agents are skipped since they don't require a CLI tool.

## Version Information

```bash
specify version
```

Displays the Spec Kit CLI version, Python version, platform, and architecture.

A quick version check is also available via:

```bash
specify --version
specify -V
```
