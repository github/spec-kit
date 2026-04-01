# Installation Guide

## Prerequisites

- **Linux/macOS** (or Windows; PowerShell scripts now supported without WSL)
- AI coding agent: [Claude Code](https://www.anthropic.com/claude-code), [GitHub Copilot](https://code.visualstudio.com/), [Codebuddy CLI](https://www.codebuddy.ai/cli) or [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## Installation

### Initialize a New Project

The easiest way to get started is to initialize a new project:

```bash
uvx --from git+https://github.com/github/infrakit.git infrakit init <PROJECT_NAME> --iac crossplane
```

Or initialize in the current directory:

```bash
uvx --from git+https://github.com/github/infrakit.git infrakit init . --iac crossplane
# or use the --here flag
uvx --from git+https://github.com/github/infrakit.git infrakit init --here --iac crossplane
```

### Choose your AI Agent

You can proactively specify your AI agent during initialization:

```bash
uvx --from git+https://github.com/github/infrakit.git infrakit init <project_name> --ai claude --iac crossplane
uvx --from git+https://github.com/github/infrakit.git infrakit init <project_name> --ai gemini --iac crossplane
uvx --from git+https://github.com/github/infrakit.git infrakit init <project_name> --ai copilot --iac crossplane
uvx --from git+https://github.com/github/infrakit.git infrakit init <project_name> --ai codebuddy --iac crossplane
```

### Specify Script Type (Shell vs PowerShell)

All automation scripts now have both Bash (`.sh`) and PowerShell (`.ps1`) variants.

Auto behavior:

- Windows default: `ps`
- Other OS default: `sh`
- Interactive mode: you'll be prompted unless you pass `--script`

Force a specific script type:

```bash
uvx --from git+https://github.com/github/infrakit.git infrakit init <project_name> --iac crossplane --script sh
uvx --from git+https://github.com/github/infrakit.git infrakit init <project_name> --iac crossplane --script ps
```

### Ignore Agent Tools Check

If you prefer to get the templates without checking for the right tools:

```bash
uvx --from git+https://github.com/github/infrakit.git infrakit init <project_name> --ai claude --iac crossplane --ignore-agent-tools
```

## Verification

After initialization, you should see the following commands available in your AI agent:

- `/infrakit:specify` - Create specifications
- `/infrakit:plan` - Generate implementation plans
- `/infrakit:tasks` - Break down into actionable tasks

The `.infrakit/scripts` directory will contain both `.sh` and `.ps1` scripts.

## Troubleshooting

### Git Credential Manager on Linux

If you're having issues with Git authentication on Linux, you can install Git Credential Manager:

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```
