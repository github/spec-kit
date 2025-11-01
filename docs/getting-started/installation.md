# Installation Guide

## Prerequisites

- **Linux/macOS** (or Windows; PowerShell scripts now supported without WSL)
- AI coding agent: [Claude Code](https://www.anthropic.com/claude-code), [GitHub Copilot](https://code.visualstudio.com/), or [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads())
- [Git](https://git-scm.com/downloads)

> **📝 Note**: If you plan to use [multi-repository workspaces](../guides/multi-repo-workspaces.md), the workspace directory must be initialized as a git repository to version control your specifications. This is a critical requirement for team collaboration and spec tracking.

## Installation

### Initialize a New Project

The easiest way to get started is to initialize a new project:

```bash
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init <PROJECT_NAME>
```

Or initialize in the current directory:

```bash
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init --here
```

### Specify AI Agent

You can proactively specify your AI agent during initialization:

```bash
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init <project_name> --ai claude
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init <project_name> --ai gemini
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init <project_name> --ai copilot
```

### Specify Script Type (Shell vs PowerShell)

All automation scripts now have both Bash (`.sh`) and PowerShell (`.ps1`) variants.

Auto behavior:
- Windows default: `ps`
- Other OS default: `sh`
- Interactive mode: you'll be prompted unless you pass `--script`

Force a specific script type:
```bash
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init <project_name> --script sh
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init <project_name> --script ps
```

### Ignore Agent Tools Check

If you prefer to get the templates without checking for the right tools:

```bash
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init <project_name> --ai claude --ignore-agent-tools
```

## Verification

After initialization, you should see the following commands available in your AI agent:
- `/specify` - Create specifications
- `/plan` - Generate implementation plans  
- `/tasks` - Break down into actionable tasks

The `.specify/scripts` directory will contain both `.sh` and `.ps1` scripts.

## Updating Existing Projects

> **⚠️ Critical**: After global install, existing projects continue using their local `.specify/` templates. You must explicitly update them.

### Why Update?

When you run `/specify` or `/plan`, these commands use:
- **Scripts**: `.specify/scripts/bash/create-new-feature.sh` (local copy in your project)
- **Templates**: `.specify/templates/spec-template.md` (local copy in your project)
- **NOT**: The latest templates from GitHub or your global CLI installation

Installing the `specify` CLI globally does NOT automatically update existing projects. Each project maintains its own `.specify/` directory with templates and scripts.

### Update Methods

#### Single Project

Update one project with the latest templates:

```bash
cd my-existing-project
specify init --here --ai claude
# Preserves specs/ and (optionally) constitution.md
```

When prompted, choose whether to preserve your existing `constitution.md`.

#### Multiple Projects (Recommended for Bulk Updates)

If you have multiple projects to update, use `init.sh --all-repos`:

```bash
# Clone spec-kit if you haven't already
git clone https://github.com/hcnimi/spec-kit.git ~/git/spec-kit

# Bulk update all projects
cd ~/git
./spec-kit/init.sh --all-repos --ai claude --search-path . --max-depth 3
```

This will:
1. Find all repositories with `.specify/` directories
2. Show a preview of what will be updated
3. Ask for confirmation
4. Update each project's templates

#### Force Clean Update

If you want to completely replace all template files:

```bash
cd my-existing-project
specify init --here --ai claude --force
# Overwrites all template files, preserves specs/
```

### What Gets Updated vs Preserved

**Updated:**
- ✅ `.specify/templates/` → Latest spec/plan templates
- ✅ `.specify/scripts/` → Latest automation scripts
- ✅ `.specify/memory/` → Latest memory files (except constitution if preserved)
- ✅ `.claude/commands/spec-kit/` (or `.gemini/`, etc.) → Latest slash commands
- ✅ `.specify/docs/` → Latest documentation

**Preserved:**
- ✅ `specs/` → All your specifications
- ✅ `constitution.md` → If you chose to preserve during update
- ✅ Your project code → Never touched

### Verification After Update

Check that your project is using the latest templates:

```bash
# 1. Check template files were updated
ls -la .specify/templates/
git diff .specify/

# 2. Test a slash command
# Open project in your AI agent (Claude Code, etc.)
# Type /specify and verify it works

# 3. Check script permissions (Unix/macOS only)
ls -la .specify/scripts/bash/*.sh
# Should show executable permissions: -rwxr-xr-x
```

For comprehensive migration instructions, see the [Migration Guide](../guides/migration-init-to-cli.md).

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
