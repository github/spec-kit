# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spec Kit is a Python CLI tool that implements Spec-Driven Development (SDD) - a methodology where specifications become executable artifacts that generate code. The tool bootstraps projects with templates, scripts, and commands that enable AI-assisted development through structured workflows.

**Core Philosophy**: Specifications don't serve code—code serves specifications. The PRD generates implementation, not the other way around.

## Development Commands

### Install & Run Locally

```bash
# Install dependencies
uv sync

# Run the CLI
uv run specify --help

# Test init command locally
uv run specify init test-project
uv run specify init . --ai claude
uv run specify init --here --ai copilot

# Check tool availability
uv run specify check
```

### Installation Methods (for testing)

```bash
# Option 1: Persistent installation
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# Option 2: One-time usage
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>

# Upgrade
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git
```

### Testing Changes

When modifying templates, scripts, or CLI behavior:

1. Test with `uv run specify init test-project --ai <agent> --debug`
2. Verify template files extracted correctly in `.specify/`
3. Test scripts work on target platforms (bash/PowerShell)
4. Ensure slash commands (`/speckit.*`) work in chosen AI agent
5. Test both new project creation and `--here` (current directory) mode

## Architecture & Code Structure

### Single-File CLI Architecture

The entire CLI is contained in `src/specify_cli/__init__.py` (~1,126 lines). This deliberate design choice keeps the codebase simple and maintainable:

**Key Components**:
- **AGENT_CONFIG**: Maps 12+ AI agents to their folder paths, install URLs, and CLI requirements
- **StepTracker**: Hierarchical progress tracking with live Rich UI updates
- **select_with_arrows()**: Cross-platform interactive menu using keyboard navigation
- **download_template_from_github()**: Fetches latest release via GitHub API
- **download_and_extract_template()**: Template extraction with nested directory flattening
- **ensure_executable_scripts()**: Sets execute permissions on .sh files (Unix)

### Template System

Templates live in `templates/` and are packaged as GitHub release assets:
- `templates/commands/*.md` - Slash command prompts for AI agents
- `templates/*-template.md` - Feature spec, plan, tasks, checklist templates
- Agent-specific files organized by folder (`.claude/`, `.github/`, `.gemini/`, etc.)

**Template Distribution**: During releases, GitHub Actions packages templates into ZIP files per agent/script combination (e.g., `spec-kit-template-claude-sh.zip`). The CLI downloads these from GitHub releases.

### Constitutional Framework

`memory/constitution.md` defines immutable development principles that govern all generated code:
- **Article I**: Library-First Principle (every feature starts as a library)
- **Article II**: CLI Interface Mandate (text in/out for observability)
- **Article III**: Test-First Imperative (TDD non-negotiable)
- **Articles VII-VIII**: Simplicity & Anti-Abstraction (combat over-engineering)
- **Article IX**: Integration-First Testing (real environments, not mocks)

These principles are enforced through implementation plan templates with "Phase -1 Gates" that block progression without justification.

### Script Organization

`scripts/` contains both bash and PowerShell versions:
- `common.sh` / `common.ps1` - Shared utilities
- `check-prerequisites.sh/.ps1` - Tool verification
- `create-new-feature.sh/.ps1` - Branch/directory setup
- `setup-plan.sh/.ps1` - Implementation plan scaffolding
- `update-agent-context.sh/.ps1` - Context file updates

**Cross-Platform**: CLI detects OS and prompts for script type (sh/ps). Windows defaults to PowerShell, Unix to bash.

### Supported AI Agents (12+)

The CLI supports multiple AI coding assistants through a unified configuration:
- **CLI-based**: Claude Code, Gemini CLI, Qwen Code, opencode, Codex CLI, Auggie CLI, CodeBuddy, Amazon Q Developer CLI
- **IDE-based**: GitHub Copilot, Cursor, Windsurf, Kilo Code, Roo Code

Each agent has specific folder paths (`.claude/`, `.github/`, etc.) and the CLI checks for required tools unless `--ignore-agent-tools` is used.

### GitHub Integration

- **API Usage**: Fetches latest release metadata and downloads template ZIPs
- **Authentication**: Supports `--github-token` flag or `GH_TOKEN`/`GITHUB_TOKEN` env vars
- **TLS**: Uses `truststore` for SSL certificate validation (can be skipped with `--skip-tls`)

## SDD Workflow (Slash Commands)

After `specify init`, projects get these commands for structured development:

### Core Workflow
1. `/speckit.constitution` - Establish governing principles (Article I-IX)
2. `/speckit.specify` - Define WHAT to build (requirements, user stories)
3. `/speckit.plan` - Define HOW to build (tech stack, architecture)
4. `/speckit.tasks` - Break down into actionable tasks (ordered, parallelizable)
5. `/speckit.implement` - Execute all tasks following the plan

### Optional Quality Commands
- `/speckit.clarify` - Structured questioning to resolve ambiguities (before `/speckit.plan`)
- `/speckit.analyze` - Cross-artifact consistency validation (after `/speckit.tasks`)
- `/speckit.checklist` - Generate quality validation checklists

### Git Worktree Commands
- `/speckit.worktree` - Create worktree for current feature branch (manual)
- `/speckit.worktree list` - Display all worktrees with status (active/stale/orphaned) [PLANNED]
- `/speckit.worktree remove [branch]` - Remove specific worktree [PLANNED]
- `/speckit.worktree cleanup` - Remove all stale worktrees [PLANNED]

## Git Worktree Workflow

Spec-kit now supports **automatic worktree creation** for parallel AI agent development.

### Automatic Worktree Creation

When you run `/speckit.specify`, the workflow now:

1. Creates feature branch (e.g., `001-user-auth`)
2. Creates spec directory (`specs/001-user-auth/`)
3. Copies spec template to `specs/001-user-auth/spec.md`
4. **Commits the spec template** with message "Initialize spec for 001-user-auth"
5. **Creates worktree at `.worktrees/001-user-auth/`**
6. Automatically adds `.worktrees/` to `.gitignore`

This enables **parallel development**:
- **Main repo**: Refine specifications, update plans, manage documentation
- **Worktree**: Implement features, run tests, execute code

Both can run simultaneously without conflicts!

### Workflow Order & Commits

**Important**: The spec template is committed BEFORE the worktree is created. This ensures:
- Main repo has a committed baseline spec to refine
- Worktree starts clean with the committed spec (no uncommitted files)
- Clear separation: spec work (main) vs implementation work (worktree)

**Commit happens automatically** at:
```bash
create-new-feature.sh line 195:
git add specs/001-feature/spec.md
git commit -m "Initialize spec for 001-feature"
```

Then worktree is created (line 200).

### Parallel Development Pattern

```bash
# Terminal 1 (main repo) - Specification work
cd /path/to/spec-kit
claude  # Work on specs/001-user-auth/spec.md, refine requirements

# Terminal 2 (worktree) - Implementation work
cd /path/to/spec-kit/.worktrees/001-user-auth
claude  # Implement features, run tests, execute code
```

### Conflict Handling

If a worktree already exists when creating a feature, you'll be prompted:

```
Worktree already exists for branch '001-user-auth'

Choose action:
  1) Stop - Cancel operation with error
  2) Cleanup - Remove old worktree and create fresh
  3) Skip - Keep existing worktree, continue

Enter choice (1-3):
```

### Manual Worktree Creation

For existing feature branches created before worktree support:

```bash
# Checkout the feature branch
git checkout 002-existing-feature

# Create worktree manually
/speckit.worktree
```

### Worktree Location

All worktrees are stored in `.worktrees/` directory at repository root:
```
spec-kit/
├── .worktrees/              # Git worktrees (gitignored)
│   ├── 001-user-auth/       # Full repo checkout for feature 001
│   ├── 002-payment-flow/    # Full repo checkout for feature 002
│   └── 003-dashboard/       # Full repo checkout for feature 003
├── specs/                   # Specifications (committed to git)
│   ├── 001-user-auth/
│   ├── 002-payment-flow/
│   └── 003-dashboard/
└── src/                     # Source code
```

### Troubleshooting Worktrees

**Worktree creation fails**:
- Feature branch and spec still created successfully (worktree is optional)
- Create worktree later with `/speckit.worktree`
- Check git version ≥2.5 (worktree support)

**Disk space issues**:
- Each worktree is a full repository checkout
- Use `/speckit.worktree cleanup` to remove stale worktrees [PLANNED]
- Manually: `git worktree remove .worktrees/001-feature`

**Invalid branch name**:
- Worktrees only work with spec-kit feature branches (###-feature-name)
- Main/master branches not supported for worktrees

## Important Patterns & Constraints

### Directory Flattening
When extracting templates, if the ZIP contains a single nested directory, the CLI automatically flattens it to avoid `project/project-name/` structure.

### Git Repository Handling
- Checks if directory is already a git repo before initializing
- Uses `--no-git` to skip initialization
- Git Credential Manager recommended for Linux (see README troubleshooting)

### Environment Variables
- `SPECIFY_FEATURE`: Override feature detection for non-Git workflows
- `GH_TOKEN` / `GITHUB_TOKEN`: GitHub API authentication
- `CODEX_HOME`: Required for Codex CLI (auto-generated setup instruction)

### Cross-Platform Keyboard Input
Uses `readchar` library for arrow key navigation (↑/↓) in menus. Handles differences between Unix and Windows terminal input.

### Security Considerations
Agent folders (`.claude/`, `.github/`, etc.) may contain credentials. CLI displays security notice recommending these be added to `.gitignore`.

## Development Workflow Philosophy

From the constitution and methodology:

1. **Specifications are source of truth** - Code regenerates from specs
2. **Test-first always** - Tests written before implementation (Article III)
3. **Simplicity over cleverness** - Max 3 projects initially (Article VII)
4. **No premature abstraction** - Use frameworks directly (Article VIII)
5. **Integration testing priority** - Real databases over mocks (Article IX)

## Testing Checklist Before PRs

- [ ] Run `uv run specify init test-project --ai claude` successfully
- [ ] Test `--here` mode: `cd /tmp/empty && uv run /path/to/spec-kit specify init --here --ai copilot`
- [ ] Verify template extraction creates proper `.specify/` structure
- [ ] Check script permissions set correctly on Unix (`*.sh` files executable)
- [ ] Confirm slash commands appear in AI agent after initialization
- [ ] Test with `--debug` flag if making network/extraction changes
- [ ] Verify changes work with multiple AI agents (not just one)

## Common Pitfalls

**Don't**:
- Add complex multi-file architectures - keep CLI in single `__init__.py`
- Break template structure without updating release workflow
- Modify constitution.md without understanding its role as immutable principles
- Add dependencies without strong justification (minimize external deps)
- Create platform-specific code without cross-platform testing

**Do**:
- Follow the established patterns in the codebase
- Test on both Unix and Windows when modifying scripts/paths
- Update documentation (README.md, spec-driven.md) for user-facing changes
- Maintain the single-file CLI architecture for simplicity
- Use Rich library for terminal output formatting

## AI Contribution Disclosure

Per CONTRIBUTING.md: **All AI-assisted contributions must be disclosed** in PRs/issues. This includes extent of use (comments vs. code generation). Exception: trivial typo/spacing fixes.

## Key Files Reference

- `src/specify_cli/__init__.py` - Entire CLI implementation
- `templates/commands/*.md` - AI agent slash command prompts
- `memory/constitution.md` - Development principles (Articles I-IX)
- `pyproject.toml` - Python project config (specify-cli package)
- `README.md` - User documentation and quick start
- `spec-driven.md` - Deep dive into SDD methodology
- `CONTRIBUTING.md` - Contribution guidelines and AI disclosure policy
