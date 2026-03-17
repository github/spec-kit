# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Specify CLI** is a Python CLI tool that bootstraps projects for Spec-Driven Development (SDD). It sets up directory structures, templates, and AI agent integrations for multiple coding assistants (Claude Code, Copilot, Cursor, Gemini, etc.).

## Development Commands

```bash
# Install dependencies
uv sync

# Run CLI locally
uv run specify --help
uv run specify init <project-name> --ai claude
uv run specify check

# Run tests
uv run pytest                           # All tests
uv run pytest tests/test_extensions.py  # Single file
uv run pytest -k "test_name"            # Single test by name

# Test with coverage
uv run pytest --cov=src --cov-report=term-missing

# Generate release packages locally (for testing template changes)
./.github/workflows/scripts/create-release-packages.sh v1.0.0
```

## Architecture

### Source Structure

- `src/specify_cli/__init__.py` - Main CLI implementation (typer-based)
- `src/specify_cli/agents.py` - CommandRegistrar for agent-specific command formats
- `src/specify_cli/extensions.py` - Extension manager for modular packages
- `src/specify_cli/presets.py` - Preset manager for versioned template collections

### Key Components

**AGENT_CONFIG** (in `__init__.py`): Single source of truth for all supported AI agents. Dictionary key must match the actual CLI tool name (e.g., `"cursor-agent"` not `"cursor"`). Fields:

- `name`: Display name
- `folder`: Agent directory (e.g., `.claude/`)
- `commands_subdir`: Where commands live (e.g., `commands`, `workflows`, `prompts`)
- `requires_cli`: Whether agent needs CLI tool check

**CommandRegistrar** (in `agents.py`): Handles writing command files to agent directories. Has its own `AGENT_CONFIGS` dict with format-specific details (file extension, argument placeholder style). Must stay in sync with `AGENT_CONFIG` when adding new agents.

**Extension System** (in `extensions.py`):

- `ExtensionManifest`: Validates `extension.yml` files
- `ExtensionManager`: Handles install/remove lifecycle
- `ExtensionCatalog`: Fetches from remote catalog with caching
- `HookExecutor`: Manages extension hooks

**Preset System** (in `presets.py`):

- `PresetManifest`: Validates `preset.yml` files
- `PresetManager`: Handles preset install/remove lifecycle
- `PresetCatalog`: Fetches presets from remote catalogs with priority stacking

### Templates

- `templates/commands/` - Command templates (Markdown format with frontmatter)
- `templates/*.md` - Spec, plan, tasks, and constitution templates

## Version Management

Changes to `__init__.py` require:

1. Version bump in `pyproject.toml`
2. Entry in `CHANGELOG.md`

## Adding New Agent Support

1. Add to `AGENT_CONFIG` in `__init__.py` using actual CLI tool name as key
2. Update `--ai` help text in `init()` command
3. Update README.md supported agents table
4. Update release scripts in `.github/workflows/scripts/`
5. Update context scripts in `scripts/bash/` and `scripts/powershell/`

See [AGENTS.md](AGENTS.md) for detailed guide.

## Testing Guidelines

- Tests are in `tests/` using pytest
- `test_extensions.py` - Extension system tests
- `test_presets.py` - Preset system tests
- `test_ai_skills.py` - AI skills/command generation tests
- `test_agent_config_consistency.py` - Validates AGENT_CONFIG consistency
- `test_cursor_frontmatter.py` - Cursor-specific frontmatter handling

## GitHub PR Reviews

The GraphQL API with `reviewThreads` and `isResolved` filter is the reliable way to get unresolved Copilot review comments. The REST API does not expose resolution status.

```bash
# Get unresolved review comments on a PR
gh api graphql -f query='
query {
  repository(owner: "github", name: "spec-kit") {
    pullRequest(number: PR_NUMBER) {
      reviewThreads(first: 50) {
        nodes {
          isResolved
          isOutdated
          path
          line
          comments(first: 3) {
            nodes {
              body
              author { login }
              createdAt
            }
          }
        }
      }
    }
  }
}' --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false) | {path, line, outdated: .isOutdated, comment: .comments.nodes[0].body[0:200]}'
```

Replace `PR_NUMBER` with the actual PR number. This returns only unresolved threads with their file path, line number, and whether the comment is outdated (code changed since comment).
