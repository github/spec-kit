# Installation Guide

## Prerequisites

- **Linux/macOS** (or Windows; PowerShell scripts now supported without WSL)
- AI coding agent: [Claude Code](https://www.anthropic.com/claude-code), [GitHub Copilot](https://code.visualstudio.com/), [CodeBuddy CLI](https://www.codebuddy.cn/docs/cli/installation), [Gemini CLI](https://github.com/google-gemini/gemini-cli), [Pi Coding Agent](https://pi.dev), or [Oh My Pi](https://www.npmjs.com/package/@oh-my-pi/pi-coding-agent)
- [uv](https://docs.astral.sh/uv/) for package management (recommended) or [pipx](https://pipx.pypa.io/) for persistent installation
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads) _(optional — required only when the git extension is enabled)_

## Installation

> [!IMPORTANT]
> This repository is the independent AI Team distribution. Install the pinned
> `v0.12.5+teamwork.1` tag from `EuphoriaYan/spec-kit`; do not substitute the
> upstream `github/spec-kit` URL when setting up an AI Team workspace.

> [!WARNING]
> Packages named `specify-cli` on PyPI are not this distribution. Use the
> pinned GitHub command below, or a wheel built directly from this tagged
> repository for offline and air-gapped environments.

### Persistent Installation (Recommended)

Install the pinned AI Team release once and use it everywhere:

> [!NOTE]
> The command below requires **[uv](https://docs.astral.sh/uv/)**. If you see `command not found: uv`, [install uv first](./install/uv.md).

```bash
uv tool install specify-cli --from git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.1
```

Then initialize a project:

```bash
specify init <PROJECT_NAME> --integration copilot
```

### One-time Usage

Run directly without installing — see the [One-time usage (uvx)](install/one-time.md) guide.

### Alternative Package Managers

- **pipx** — see the [pipx installation guide](install/pipx.md)
- **Enterprise / Air-Gapped** — see the [air-gapped installation guide](install/air-gapped.md)

### Specify Integration

Interactive terminals prompt you to choose a coding agent integration during initialization. Non-interactive sessions, such as CI or piped runs, default to GitHub Copilot unless you pass `--integration`.

You can proactively specify your coding agent integration during initialization:

```bash
specify init <project_name> --integration claude
specify init <project_name> --integration gemini
specify init <project_name> --integration copilot
specify init <project_name> --integration codebuddy
specify init <project_name> --integration pi
specify init <project_name> --integration omp
```

### Specify Script Type (Shell vs PowerShell)

All automation scripts now have both Bash (`.sh`) and PowerShell (`.ps1`) variants.

Auto behavior:

- Windows default: `ps`
- Other OS default: `sh`
- Interactive mode: you'll be prompted unless you pass `--script`

Force a specific script type:

```bash
specify init <project_name> --script sh
specify init <project_name> --script ps
```

### Ignore Agent Tools Check

If you prefer to get the templates without checking for the right tools:

```bash
specify init <project_name> --integration claude --ignore-agent-tools
```

## Verification

After installation, run the following command to confirm the correct version is installed:

```bash
specify version
```

This helps verify you are running the official Spec Kit build from GitHub, not an unrelated package with the same name.

**Stay consistent:** this distribution does not advertise automatic self-update.
Use the fixed-tag command in the [Upgrade Guide](./upgrade.md) to repair or
standardize an installation.

After initialization, you should see the following commands available in your coding agent:

- `/speckit.specify` - Create specifications
- `/speckit.plan` - Generate implementation plans
- `/speckit.tasks` - Break down into actionable tasks
- `/speckit.implement` - Execute implementation tasks
- `/speckit.analyze` - Validate cross-artifact consistency
- `/speckit.clarify` - Identify and resolve ambiguities
- `/speckit.checklist` - Generate quality checklists
- `/speckit.constitution` - Create or update project principles
- `/speckit.converge` - Assess codebase against artifacts and append remaining tasks
- `/speckit.taskstoissues` - Convert tasks to issues

Scripts are installed into a variant subdirectory matching the chosen script type:

- `.specify/scripts/bash/` — contains `.sh` scripts (default on Linux/macOS)
- `.specify/scripts/powershell/` — contains `.ps1` scripts (default on Windows)

## Troubleshooting

### Enterprise / Air-Gapped Installation

If your environment blocks access to PyPI or GitHub, see the [Enterprise / Air-Gapped Installation](install/air-gapped.md) guide for step-by-step instructions on creating portable wheel bundles.

### Git Credential Manager on Linux

If you're having issues with Git authentication on Linux, see the [Air-Gapped Installation guide](install/air-gapped.md#git-credential-manager-on-linux) for Git Credential Manager setup instructions.
