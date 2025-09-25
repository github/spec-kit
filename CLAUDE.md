# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Dependencies
```bash
# Install dependencies using uv
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run CLI directly (development)
python -m src.specify_cli --help

# Install in editable mode
uv pip install -e .

# Test CLI after installation
specify --help
```

### Testing and Development
```bash
# Test CLI functionality
specify check
specify init test-project --ai claude --ignore-agent-tools

# Run CLI with development flags
specify init demo --ai copilot --ignore-agent-tools --debug

# Build package
uv build

# Run uvx directly from source
uvx --from . specify --help
```

### Linting and Code Quality
Currently no enforced lint configuration, but basic import validation can be done:
```bash
python -c "import specify_cli; print('Import OK')"
```

## Architecture Overview

### Core Components

**CLI Application (`src/specify_cli/__init__.py`)**
- Main entry point for the `specify` command
- Built with Typer for CLI framework
- Handles project initialization and tool checking
- Downloads and extracts templates from GitHub releases
- Supports multiple AI assistants: Claude Code, GitHub Copilot, Gemini CLI, Cursor, Qwen

**Template System (`templates/`)**
- `spec-template.md` - Product specification template
- `plan-template.md` - Technical implementation plan template
- `tasks-template.md` - Task breakdown template
- `commands/` - AI assistant command definitions for `/specify`, `/plan`, `/tasks`
- `agent-file-template.md` - Agent context template

**Script Automation (`scripts/`)**
- `bash/` - POSIX shell scripts for project automation
- `powershell/` - PowerShell scripts for Windows environments
- Common utilities for feature management and git workflows

**Memory System (`memory/`)**
- Constitution and guidelines for AI assistants
- Project governance and decision-making principles

### Key Design Patterns

**Specification-Driven Development (SDD)**
- Specifications are executable - they generate code directly
- Three-phase workflow: `/specify` → `/plan` → `/tasks`
- Specifications become the source of truth, not just documentation
- Supports parallel implementation exploration and iterative enhancement

**Multi-Agent Support**
- Unified template system works across different AI coding agents
- Agent-specific files and command structures
- Cross-platform script support (bash/PowerShell)

**Release and Distribution**
- GitHub Actions automatically create template releases
- Version-tagged ZIP files for each AI agent and script type
- CLI downloads latest release directly from GitHub API

## Project Workflow

### Spec-Driven Development Process

1. **Specification Phase (`/specify`)**
   - Create detailed product requirements document
   - Define user stories and acceptance criteria
   - Focus on "what" and "why", not technical implementation

2. **Planning Phase (`/plan`)**
   - Generate technical implementation plan
   - Choose technology stack and architecture
   - Create API specifications and data models

3. **Task Phase (`/tasks`)**
   - Break down implementation into actionable tasks
   - Generate development workflow
   - Create implementation roadmap

4. **Implementation**
   - Execute tasks systematically
   - Use generated specifications as source of truth
   - Iterate and refine based on feedback

### Branch Management
- Work on feature branches for specification development
- Use git workflow for tracking specification evolution
- Templates include git automation scripts

### Multi-AI Agent Support
The project supports these AI coding assistants:
- **Claude Code**: Primary focus, rich VS Code integration
- **GitHub Copilot**: VS Code and other editor support
- **Gemini CLI**: Google's AI assistant
- **Cursor**: AI-native editor
- **Qwen**: Open source alternative

Each agent has customized templates and command structures while maintaining workflow consistency.

## Key Files and Dependencies

### Configuration
- `pyproject.toml` - Python package configuration and dependencies
- `.github/workflows/release.yml` - Automated release process

### Core Dependencies
- `typer` - CLI framework
- `rich` - Terminal formatting and UI
- `httpx` - HTTP client for GitHub API
- `readchar` - Cross-platform keyboard input
- `truststore` - SSL/TLS certificate management

### Important Directories
- `docs/` - User documentation and guides
- `media/` - Images and video assets
- `.github/` - GitHub Actions and project governance

## Development Notes

### Template Updates
Templates are automatically packaged and released when changes are pushed to main branch. Each AI agent gets separate ZIP files with appropriate configurations.

### Script Permissions
The CLI automatically sets execute permissions on shell scripts after template extraction (POSIX systems only).

### Cross-Platform Support
Project supports both POSIX shell and PowerShell environments, with automatic script type selection based on operating system.

### SSL/TLS Handling
Uses `truststore` for proper certificate validation when downloading templates. Supports `--skip-tls` flag for development environments.