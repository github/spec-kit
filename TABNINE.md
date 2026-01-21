# Tabnine Context: GitHub Spec Kit

**Project Type**: Python CLI Tool + Spec-Driven Development Framework  
**Primary Language**: Python 3.11+  
**Package Manager**: uv  
**Distribution**: PyPI package + GitHub releases

---

## Project Overview

**GitHub Spec Kit** (also known as **Specify CLI**) is an open-source toolkit that implements **Spec-Driven Development (SDD)** - a methodology that inverts the traditional software development paradigm by making specifications executable. Instead of code being the source of truth with specs as documentation, SDD treats specifications as the primary artifact that generates implementation.

### Core Concept

Spec-Driven Development transforms how software is built:

- **Specifications drive code**, not the other way around
- **Natural language becomes executable** through AI-powered code generation
- **Structured workflows** guide teams from requirements → planning → implementation
- **Constitutional principles** enforce architectural consistency across all generated code
- **Template-driven quality** ensures LLMs produce maintainable, testable specifications

### Key Components

1. **Specify CLI** (`src/specify_cli/__init__.py`): Command-line tool that bootstraps SDD projects
2. **Templates** (`templates/`): Structured templates for specs, plans, tasks, and commands
3. **Scripts** (`scripts/`): Automation scripts for feature management (bash/PowerShell)
4. **Agent Commands** (`templates/commands/`): Slash commands for AI coding assistants
5. **Constitution** (`memory/constitution.md`): Architectural principles that govern development

---

## Architecture

### CLI Structure

The Specify CLI is a single-file Python application built with:

- **Typer**: CLI framework for command handling
- **Rich**: Terminal UI with progress tracking, tables, and panels
- **httpx**: HTTP client for GitHub API integration (with truststore for SSL)
- **platformdirs**: Cross-platform path resolution

### Supported AI Agents

Spec Kit integrates with 17+ AI coding assistants via agent-specific command files:

| Agent | Directory | Format | CLI Required |
|-------|-----------|--------|--------------|
| Claude Code | `.claude/commands/` | Markdown | ✅ |
| GitHub Copilot | `.github/agents/` | Markdown | ❌ (IDE) |
| Gemini CLI | `.gemini/commands/` | TOML | ✅ |
| Cursor | `.cursor/commands/` | Markdown | ❌ (IDE) |
| Windsurf | `.windsurf/workflows/` | Markdown | ❌ (IDE) |
| Qwen Code | `.qwen/commands/` | TOML | ✅ |
| Qoder CLI | `.qoder/commands/` | Markdown | ✅ |
| Amazon Q | `.amazonq/prompts/` | Markdown | ✅ |
| And 9 more... | See AGENTS.md | Varies | Varies |

**Agent Configuration**: Centralized in `AGENT_CONFIG` dict in `__init__.py` with metadata:
- Display name, folder path, install URL, CLI requirement flag

### Slash Commands Workflow

The SDD methodology is implemented through five core slash commands:

```
/speckit.constitution  →  Establish project principles
/speckit.specify       →  Create feature specification
/speckit.plan          →  Generate technical implementation plan
/speckit.tasks         →  Break down plan into executable tasks
/speckit.implement     →  Execute implementation
```

**Optional quality commands**:
- `/speckit.clarify`: Structured questioning to resolve ambiguities
- `/speckit.analyze`: Cross-artifact consistency validation
- `/speckit.checklist`: Generate quality validation checklists

---

## Development Workflow

### Installing from Source

```bash
# Clone repository
git clone https://github.com/github/spec-kit.git
cd spec-kit

# Install dependencies
uv sync

# Run CLI locally
uv run specify --help
```

### Testing Changes Locally

Since `uv tool install` pulls from GitHub releases, test local changes by creating release packages:

```bash
# Generate local packages
./.github/workflows/scripts/create-release-packages.sh v1.0.0

# Copy to test project
cp -r .genreleases/sdd-copilot-package-sh/. <test-project>/

# Test in the project
cd <test-project>
code .  # or your AI agent
```

### Building & Distribution

**Version Management**:
- Version defined in `pyproject.toml`
- Updated via `.github/workflows/scripts/update-version.sh`
- CHANGELOG.md must be updated for every release

**Release Process**:
1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with changes
3. Commit changes
4. Create GitHub release (automated via `.github/workflows/release.yml`)
5. Release workflow packages templates for all agents (sh/ps variants)
6. Packages uploaded as release artifacts

### Key Files & Their Roles

| File/Directory | Purpose |
|----------------|---------|
| `src/specify_cli/__init__.py` | Main CLI implementation (single file) |
| `pyproject.toml` | Package metadata, dependencies, version |
| `AGENT_CONFIG` dict | Central configuration for all AI agents |
| `templates/` | Spec/plan/task templates + agent commands |
| `templates/commands/` | Slash command implementations |
| `scripts/bash/` | POSIX shell automation scripts |
| `scripts/powershell/` | PowerShell automation scripts |
| `.github/workflows/` | CI/CD pipelines |
| `AGENTS.md` | Guide for adding new agent support |
| `spec-driven.md` | Deep dive into SDD methodology |

---

## Key Commands

### CLI Commands

```bash
# Initialize new project
specify init <project-name>
specify init . --ai claude              # Current directory
specify init --here --ai copilot        # Alternative syntax
specify init --force --here             # Skip confirmation

# With options
specify init my-app --ai gemini --script ps --no-git
specify init my-app --github-token ghp_xxx  # Corporate environments

# Check installed tools
specify check

# Show version
specify version
```

### Development Commands

```bash
# Run locally
uv run specify init test-project

# Install globally
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# Upgrade
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git
```

---

## Coding Conventions

### Python Style

- **Type hints**: Used throughout for clarity
- **Rich console**: All user-facing output via Rich library (panels, tables, progress)
- **Error handling**: Graceful failures with detailed error messages
- **Cross-platform**: Support Windows (PowerShell), macOS, Linux (bash)

### Template Conventions

- **Markdown frontmatter**: YAML metadata for description, scripts, handoffs
- **Placeholders**: 
  - `$ARGUMENTS`: User input after slash command
  - `{SCRIPT}`: Replaced with script path (bash/PowerShell)
  - `{ARGS}`: JSON-escaped arguments for script calls
- **Instruction style**: Imperative, step-by-step workflows for LLMs

### Architecture Principles (from Constitution)

1. **Library-First**: Every feature starts as a standalone library
2. **CLI Interface**: All functionality exposed via command-line
3. **Test-First (NON-NEGOTIABLE)**: Write tests → get approval → implement
4. **Integration Testing**: Real environments over mocks
5. **Simplicity**: Maximum 3 projects initially, justify complexity
6. **Anti-Abstraction**: Use framework directly, avoid unnecessary layers

---

## Testing Strategy

### Current Test Coverage

⚠️ **Note**: As of this writing, formal automated tests are minimal. The project relies on:

1. **Manual testing**: Using `specify init` in real projects
2. **Integration testing**: Testing with actual AI agents
3. **Release validation**: Packaging scripts verify template structure

### Recommended Test Additions

If contributing tests:

```bash
# Unit tests for CLI functions
pytest tests/unit/

# Integration tests for template downloads
pytest tests/integration/

# End-to-end tests for project initialization
pytest tests/e2e/
```

---

## Common Development Tasks

### Adding a New AI Agent

Follow `AGENTS.md` guide:

1. Add to `AGENT_CONFIG` dict (use actual CLI tool name as key!)
2. Update `--ai` help text
3. Update `README.md` supported agents table
4. Modify release packaging script (`.github/workflows/scripts/create-release-packages.sh`)
5. Update agent context scripts (bash + PowerShell)
6. Optionally add to devcontainer (`.devcontainer/`)

**Critical**: Use actual executable name as dictionary key (e.g., `"cursor-agent"` not `"cursor"`)

### Modifying Templates

Templates live in `templates/`:

- `spec-template.md`: Feature specification structure
- `plan-template.md`: Implementation plan structure
- `tasks-template.md`: Task breakdown structure
- `commands/*.md`: Slash command implementations

**After modifying**:
1. Test locally by creating release packages
2. Verify with multiple AI agents
3. Update version in `pyproject.toml`
4. Document in `CHANGELOG.md`

### Updating Scripts

Scripts in `scripts/bash/` and `scripts/powershell/` must maintain feature parity:

- `create-new-feature.{sh,ps1}`: Branch creation and spec initialization
- `setup-plan.{sh,ps1}`: Plan setup after specification
- `update-agent-context.{sh,ps1}`: Refresh agent context files
- `check-prerequisites.{sh,ps1}`: Validate tool installations

**Testing**: Run both variants on their respective platforms

---

## Troubleshooting

### GitHub API Rate Limits

**Symptoms**: `403 Forbidden` when downloading templates

**Solutions**:
```bash
# Use GitHub token
specify init my-app --github-token ghp_your_token

# Or set environment variable
export GITHUB_TOKEN=ghp_your_token
specify init my-app
```

**Rate Limits**: 
- Unauthenticated: 60 requests/hour
- Authenticated: 5,000 requests/hour

### Git Not Found

**Symptoms**: Git initialization fails

**Solutions**:
```bash
# Skip git initialization
specify init my-app --no-git

# Or install git first
brew install git  # macOS
apt-get install git  # Debian/Ubuntu
```

### SSL/TLS Verification Issues

**Corporate environments** with custom CAs:

```bash
# Skip TLS verification (not recommended)
specify init my-app --skip-tls

# Better: Install truststore
pip install truststore
```

---

## Contributing

### Before Submitting PRs

1. **Read `CONTRIBUTING.md`**: Understand contribution guidelines
2. **Test changes**: Use release packaging script to test locally
3. **Update docs**: README, spec-driven.md, AGENTS.md as needed
4. **Bump version**: Update `pyproject.toml` and `CHANGELOG.md`
5. **Disclose AI usage**: Per contribution guidelines

### AI Contribution Disclosure

**Required for all AI-assisted contributions**:

- State which AI tools were used
- Describe extent of AI assistance (comments vs. implementation)
- Ensure you understand and have tested the changes
- Human review and validation is mandatory

### PR Checklist

- [ ] Changes tested with `uv run specify init`
- [ ] Templates tested with at least one AI agent
- [ ] Version bumped in `pyproject.toml`
- [ ] `CHANGELOG.md` updated
- [ ] Documentation updated (README, AGENTS.md)
- [ ] AI assistance disclosed (if applicable)

---

## Resources

- **Main Documentation**: README.md
- **Methodology Deep Dive**: spec-driven.md
- **Agent Integration Guide**: AGENTS.md
- **Contributing Guidelines**: CONTRIBUTING.md
- **Published Docs**: https://github.github.io/spec-kit/
- **Releases**: https://github.com/github/spec-kit/releases

---

## Quick Reference

### Project Structure

```
spec-kit/
├── src/specify_cli/__init__.py    # Main CLI (single file, ~2000 lines)
├── pyproject.toml                 # Package metadata & version
├── templates/                     # All templates
│   ├── spec-template.md          # Feature specification
│   ├── plan-template.md          # Implementation plan
│   ├── tasks-template.md         # Task breakdown
│   └── commands/                 # Slash commands
│       ├── specify.md            # /speckit.specify
│       ├── plan.md               # /speckit.plan
│       ├── tasks.md              # /speckit.tasks
│       └── implement.md          # /speckit.implement
├── scripts/                      # Automation
│   ├── bash/                     # POSIX shell scripts
│   └── powershell/               # PowerShell scripts
├── memory/constitution.md         # Architecture principles template
├── .github/workflows/            # CI/CD
└── docs/                         # GitHub Pages docs

Generated in user projects after `specify init`:
project/
├── .specify/
│   ├── memory/constitution.md
│   ├── scripts/
│   ├── specs/001-feature-name/
│   └── templates/
└── .{agent}/                     # Agent-specific commands
    └── commands/
        ├── specify.md
        ├── plan.md
        └── ...
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `SPECIFY_FEATURE` | Override feature detection for non-Git repos |
| `GH_TOKEN` / `GITHUB_TOKEN` | GitHub API authentication |
| `CODEX_HOME` | Required for Codex CLI (set to `.codex` in project) |

---

**Last Updated**: 2025-01-21  
**Spec Kit Version**: 0.0.22  
**Python Requirement**: 3.11+
