# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**MiniSpec** is a pair programming workflow for AI-assisted development. Instead of AI generating large artifacts for engineers to review, MiniSpec structures collaboration as real-time pairing where engineers navigate and AI drives.

Key insight: Engineers need to understand code going to production. Reviewing 500-line AI-generated PRs doesn't build mental models. Small chunks with continuous dialogue does.

## MiniSpec vs SpecKit

This is a fork of SpecKit with a fundamentally different approach:

| Aspect           | SpecKit                | MiniSpec                   |
| ---------------- | ---------------------- | -------------------------- |
| Planning         | AI generates documents | Interactive conversation   |
| Implementation   | Batch generation       | Small chunks (20-80 lines) |
| Engineer role    | Reviewer (post-hoc)    | Navigator (real-time)      |
| Documentation    | Manual                 | Automatic byproduct        |

## Directory Structure

```text
.minispec/
├── memory/
│   └── constitution.md          # Project principles + preferences
├── specs/
│   └── [feature-name]/
│       ├── design.md            # Feature design (interactive)
│       ├── tasks.md             # Implementation tasks
│       └── checklists/          # Quality checklists
└── knowledge/
    ├── architecture.md          # System overview
    ├── conventions.md           # Code patterns
    ├── decisions/               # ADRs (auto-created during design)
    ├── patterns/                # Code patterns (auto-created)
    └── modules/                 # Module docs (auto-created)
```

## Slash Commands

| Command                  | Purpose                                      |
| ------------------------ | -------------------------------------------- |
| `/minispec.constitution` | Set up project principles + preferences      |
| `/minispec.walkthrough`  | Guided codebase tour                         |
| `/minispec.import`       | Import SpecKit/OpenSpec specs into workflow  |
| `/minispec.design`       | Interactive design conversation              |
| `/minispec.tasks`        | Break design into reviewable chunks          |
| `/minispec.analyze`      | Validate design ↔ tasks alignment            |
| `/minispec.next`         | Implement next chunk (pair programming loop) |
| `/minispec.checklist`    | Generate quality checklists                  |
| `/minispec.validate-docs`| Check documentation freshness                |
| `/minispec.status`       | Show progress dashboard                      |

## Development Commands

```bash
# Install dependencies
uv sync

# Run CLI directly
python -m src.minispec_cli --help
python -m src.minispec_cli init demo --ai claude --ignore-agent-tools

# Editable install
uv venv && source .venv/bin/activate
uv pip install -e .
minispec --help

# Build
uv build

# Upgrade existing project
minispec upgrade              # auto-detect agent and script type
minispec upgrade --ai claude  # explicit agent
minispec upgrade --force      # accept all command changes
```

## Source Structure

- `src/minispec_cli/__init__.py` - CLI implementation (Typer)
- `templates/commands/` - MiniSpec command templates
- `templates/knowledge/` - Knowledge base document templates
- `scripts/bash/` and `scripts/powershell/` - Shell scripts
- `memory/constitution.md` - Constitution template with MiniSpec preferences

## Key Files Changed from SpecKit

- `templates/commands/*.md` - All commands now use `/minispec.*` prefix
- `scripts/` - Use `.minispec/` paths, `MINISPEC_FEATURE` env var
- `memory/constitution.md` - Added MiniSpec preferences section
- Old commands removed: `specify.md`, `plan.md`, `implement.md`, `clarify.md`

## Template Placeholders

- `$ARGUMENTS` - User input for command
- `{SCRIPT}` - Script path during generation
- `__AGENT__` - Agent name

## Current State

MiniSpec is release-ready:

- All slash commands: constitution, design, tasks, analyze, next, walkthrough, validate-docs, status, checklist
- CLI rebranded to `minispec` with updated banner, tagline, and all references
- Template files renamed (design-template.md, tasks-template.md)
- Documentation updated (README, AGENTS, CONTRIBUTING, SUPPORT, CHANGELOG)

To release:

- Create GitHub releases with template assets for `minispec init` to work
