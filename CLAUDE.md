# CLAUDE.md - Spectrena Development Guide

## Project Overview

**Spectrena** is a Python CLI toolkit for Spec-Driven Development (SDD), extending the Spec Kit framework with lineage tracking and worktree support. It helps development teams create structured specifications before implementation, supporting multiple AI coding assistants.

### Key Entry Points

| Command | Module | Description |
|---------|--------|-------------|
| `spectrena` | `src/spectrena/__init__.py` | Main CLI - project initialization, tool checks |
| `spectrena-sw` | `src/spectrena/worktrees.py` | Git worktree management for parallel spec development |
| `spectrena-mcp` | `src/spectrena/lineage/server.py` | MCP server for lineage tracking |

## Repository Structure

```
spectrena/
├── src/spectrena/           # Main Python package
│   ├── __init__.py          # CLI entry point (typer-based)
│   ├── commands.py          # Configuration management
│   ├── config.py            # Config dataclasses and YAML parsing
│   ├── discover.py          # Pre-architecture exploration (Phase -2)
│   ├── new.py               # Spec creation with auto-generated IDs
│   ├── worktrees.py         # Git worktree commands (sw)
│   └── lineage/             # Lineage tracking subsystem
│       ├── db.py            # SurrealDB backend
│       ├── server.py        # MCP server entry point
│       └── schema.surql     # Database schema
├── templates/               # Spec templates and slash commands
│   ├── commands/            # Slash command definitions (*.md)
│   ├── spec-template.md     # Feature specification template
│   ├── plan-template.md     # Implementation plan template
│   ├── tasks-template.md    # Task breakdown template
│   └── checklist-template.md
├── scripts/                 # Shell scripts for workflows
│   ├── bash/                # POSIX shell scripts
│   └── powershell/          # Windows PowerShell scripts
├── memory/                  # Project constitution template
├── docs/                    # Documentation (DocFX)
└── .github/workflows/       # CI/CD (lint, release, docs)
```

## Technology Stack

- **Python 3.11+** with type hints
- **typer** - CLI framework
- **rich** - Terminal formatting, progress, panels
- **httpx** - HTTP client (GitHub API, AI APIs)
- **gitpython** - Git operations
- **SurrealDB** (optional) - Lineage database
- **FastMCP** (optional) - MCP server for Claude integration

## Development Setup

```bash
# Install dependencies
uv sync

# Run CLI directly
uv run spectrena --help
uv run spectrena check  # Verify tool installation

# Install globally for testing
uv tool install --from . spectrena

# Run with optional lineage support
uv pip install ".[lineage-surreal]"
```

## Key Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package metadata, dependencies, entry points |
| `.markdownlint-cli2.jsonc` | Markdown linting rules |
| `.github/workflows/lint.yml` | CI markdown linting |
| `.github/workflows/release.yml` | Release automation |

## Code Conventions

### Python Style

- Use type hints for all function signatures
- Dataclasses for configuration objects (`@dataclass`)
- Rich `Console` for all terminal output
- `typer.Typer()` for CLI commands with decorators
- Async functions for database operations
- `Path` objects (not strings) for file paths

### Error Handling Pattern

```python
try:
    # Operation
except subprocess.CalledProcessError as e:
    console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(1)
```

### CLI Output Style

- Use rich markup: `[cyan]`, `[green]`, `[red]`, `[yellow]`, `[dim]`
- Success: `[green]✓[/green]` prefix
- Errors: `[red]✗[/red]` prefix
- Panel boxes for important messages
- Tree structures for hierarchical data
- Tables for structured data

## Agent Configuration

The `AGENT_CONFIG` dictionary in `__init__.py` is the single source of truth for AI agent metadata:

```python
AGENT_CONFIG: dict[str, AgentConfig] = {
    "claude": {
        "name": "Claude Code",
        "folder": ".claude/",
        "install_url": "https://docs.anthropic.com/en/docs/claude-code/setup",
        "requires_cli": True,
    },
    # ... more agents
}
```

**Important**: Dictionary keys must match actual CLI executable names (e.g., `"cursor-agent"` not `"cursor"`).

## Slash Commands

Templates in `templates/commands/` define slash commands for AI agents:

| Command | File | Purpose |
|---------|------|---------|
| `/spectrena.constitution` | `constitution.md` | Create project principles |
| `/spectrena.specify` | `specify.md` | Create feature specification |
| `/spectrena.plan` | `plan.md` | Create implementation plan |
| `/spectrena.tasks` | `tasks.md` | Generate task breakdown |
| `/spectrena.implement` | `implement.md` | Execute implementation |
| `/spectrena.clarify` | `clarify.md` | Clarify requirements |
| `/spectrena.analyze` | `analyze.md` | Cross-artifact analysis |
| `/spectrena.checklist` | `checklist.md` | Quality checklists |

Command files use YAML frontmatter with `$ARGUMENTS` and `{SCRIPT}` placeholders.

## Testing Changes Locally

```bash
# Generate release packages locally
./.github/workflows/scripts/create-release-packages.sh v1.0.0

# Copy to test project
cp -r .genreleases/sdd-copilot-package-sh/. <test-project>/

# Test slash commands in the agent
```

## Version Management

Changes to `__init__.py` require:
1. Version bump in `pyproject.toml`
2. Entry in `CHANGELOG.md`

## Important Design Decisions

### Spec ID Templates

Configurable via `.spectrena/config.yml`:
- Simple: `{NNN}-{slug}` → `001-feature-name`
- Component: `{component}-{NNN}-{slug}` → `CORE-001-feature`
- Full: `{project}-{component}-{NNN}-{slug}` → `APP-CORE-001-feature`

### Numbering Sources

- `directory` - Count existing `specs/` folders
- `branch` - Parse git branches matching `spec/*`
- `component` - Per-component numbering
- `global` - Across all components

### Lineage Tracking (Optional)

SurrealDB-backed tracking for:
- Spec dependencies and status
- Task progress and timing
- Code change attribution
- Impact analysis

## Common Tasks

### Adding a New AI Agent

1. Add entry to `AGENT_CONFIG` in `__init__.py`
2. Update CLI help text for `--ai` option
3. Update README.md supported agents table
4. Update `create-release-packages.sh`
5. Update agent context scripts (`update-agent-context.sh/ps1`)

### Adding a New CLI Command

```python
@app.command()
def new_command(
    arg: str = typer.Argument(..., help="Description"),
    option: bool = typer.Option(False, "--flag", help="Description"),
):
    """Command docstring shown in --help."""
    # Implementation
```

### Modifying Templates

Templates in `templates/` use placeholders:
- `{FEATURE_TITLE}`, `{SPEC_ID}`, `{DATE}` - Spec metadata
- `{SCRIPT}` - Script path for shell commands
- `$ARGUMENTS` - User input from slash command
- `{ARGS}` - JSON-escaped arguments

## CI/CD Pipeline

- **lint.yml**: Markdown linting on all PRs
- **release.yml**: Creates release packages per agent/script type
- **docs.yml**: DocFX documentation to GitHub Pages

## Common Gotchas

1. **Script permissions**: POSIX scripts need `+x` bit; `ensure_executable_scripts()` handles this
2. **GitHub rate limits**: Use `--github-token` or `GH_TOKEN` env var for init
3. **Claude local path**: After `claude migrate-installer`, check `~/.claude/local/claude`
4. **JSON escaping**: Single quotes in args need shell escape: `'I'\''m Groot'`
5. **Config parsing**: Simple regex-based YAML parsing in `config.py` (no external dependency)

## File Modification Guidelines

- **Never** modify `templates/` without testing with actual AI agents
- **Always** update both bash and PowerShell scripts together
- **Update** `AGENTS.md` when adding/modifying agent integration
- **Test** CLI changes with `uv run spectrena` before committing
