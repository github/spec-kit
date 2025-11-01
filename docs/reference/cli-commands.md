# Specify CLI Commands Reference

Complete reference for the `specify` CLI tool.

## Installation

```bash
specify init [project-name] [OPTIONS]
```

Initialize a new Spec Kit project.

### Arguments
- `[project-name]` - Name of project directory to create (optional if `--here`)

### Options
- `--ai <agent>` - AI assistant to use: `claude`, `gemini`, `copilot`, `cursor`
- `--script <type>` - Script type: `sh` (bash), `ps` (PowerShell)
- `--here` - Initialize in current directory
- `--no-git` - Skip git repository initialization
- `--ignore-agent-tools` - Skip checking for AI agent tools
- `--skip-tls` - Skip TLS verification (not recommended)
- `--debug` - Enable debug output
- `--repo-owner <owner>` - GitHub repo owner (auto-detected from uvx)
- `--repo-name <name>` - GitHub repo name (default: `spec-kit`)
- `--repo-branch <branch>` - Branch to download from
- `--help` - Show help message

### Examples

```bash
# Create new project with Claude Code
specify init my-project --ai claude

# Initialize in current directory
specify init --here --ai claude

# With PowerShell scripts
specify init my-project --ai copilot --script ps

# From custom fork/branch
specify init my-project --ai claude --repo-owner myorg --repo-branch dev
```

### Updating Existing Projects

> **⚠️ Critical**: Use `--here` to update projects initialized with `init.sh` or older `specify` versions. Slash commands like `/specify` and `/plan` use local templates from `.specify/templates/`, not the global CLI.

**Update single project:**

```bash
# Update existing project with latest templates
cd existing-project
specify init --here --ai claude

# Preserves:
# - specs/ directory (all your specifications)
# - constitution.md (optional, you'll be prompted)
# - Your project code (never touched)

# Updates:
# - .specify/templates/ (latest spec/plan templates)
# - .specify/scripts/ (latest automation scripts)
# - .claude/commands/ (or .gemini/, etc.)
```

**Force overwrite all templates:**

```bash
cd existing-project
specify init --here --ai claude --force

# Use --force when:
# - Templates are corrupted
# - You want to revert custom modifications
# - Upgrading from very old version
```

**Update multiple projects (use init.sh):**

```bash
# For bulk updates, init.sh is more efficient
cd ~/git
./spec-kit/init.sh --all-repos --ai claude --search-path . --max-depth 3
```

**Why update is needed:**

When you run `/specify` in a project, it executes:
- Script: `.specify/scripts/bash/create-new-feature.sh` (local)
- Template: `.specify/templates/spec-template.md` (local)
- NOT: Latest templates from GitHub or global CLI

Without updating, your project uses stale templates even after global install.

**See also**: [Migration Guide](../guides/migration-init-to-cli.md) for comprehensive instructions.

## Check Command

```bash
specify check
```

Check if required tools are installed (`git`, AI agent, `code`/`code-insiders`, etc.).

### Examples

```bash
# Verify system setup
specify check

# Skip TLS on corporate network
specify check --skip-tls
```

## Environment Variables

- `SPECIFY_REPO_OWNER` - Override default repo owner
- `SPECIFY_REPO_NAME` - Override default repo name
- `SPECIFY_REPO_BRANCH` - Override default branch

## Installation Methods

### Via uvx (Temporary)
```bash
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init my-project
```

### Global Installation with uv
```bash
uv tool install git+https://github.com/hcnimi/spec-kit.git
```

### Global Installation with pip
```bash
pip install git+https://github.com/hcnimi/spec-kit.git
```

### From Local Clone
```bash
./init.sh my-project --ai claude
```

## Next Steps

- [Slash Commands](./slash-commands.md) - `/specify`, `/plan`, `/tasks`, etc.
- [Configuration](./configuration.md) - Project structure
- [Getting Started](../getting-started/) - Hands-on tutorial
