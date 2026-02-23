# Architecture

## Overview
Spec Kit is a Spec-Driven Development (SDD) toolkit delivered as a Python CLI (`specify`) plus a set of templates, scripts, and optional extensions. The CLI bootstraps projects by downloading a release template that installs:

- `.specify/` for core SDD artifacts (templates, scripts, memory)
- Agent-specific command files (e.g., `.claude/commands/`, `.gemini/commands/`)
- Optional agent skills derived from command templates

The workflow centers on structured slash commands (`/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, `/speckit.deployment`) that move a project from specification to plan to tasks and implementation.

## High-Level Flow

### 1) Project Initialization (`specify init`)

- Validates inputs and selected AI agent.
- Optionally checks required CLI tools for the selected agent.
- Fetches the latest release asset from GitHub (zip file per agent + script type).
- Extracts template content into a new directory or merges into the current one.
- Ensures scripts are executable (POSIX) and initializes a constitution if missing.
- Optionally installs agent skills and removes extracted command files on new projects.
- Initializes a git repository unless `--no-git` is used or git is unavailable.

### 2) Spec-Driven Workflow

- `/speckit.constitution` captures project principles and constraints.
- `/speckit.specify` generates a feature specification under `specs/<feature>/spec.md`.
- `/speckit.plan` produces an implementation plan and supporting artifacts.
- `/speckit.tasks` derives executable tasks from the plan.
- `/speckit.implement` executes tasks using the agent and local tooling.
- `/speckit.deployment` guides deployment options after implementation.

### 3) Extensions (Optional)

- Extensions add additional slash commands and hooks without bloating core templates.
- An extension ships with `extension.yml` plus command files.
- `specify extension add` registers commands into detected agent folders.

## Core Components

### CLI Entry Point

- File: `src/specify_cli/__init__.py`
- Uses `typer` for commands and `rich` for UI.
- Maintains `AGENT_CONFIG` for agent metadata (folder, command subdir, CLI requirement).
- Downloads release templates via GitHub API and release assets.
- Merges into current directory with safe handling of `.vscode/settings.json`.

### Templates

- Location: `templates/`
- Contains the canonical spec, plan, tasks, and command templates.
- The release pipeline packages agent-specific command files and scripts into zip assets.
- Template content is the source of truth for generated project files.

### Scripts

- Location: `scripts/bash/` and `scripts/powershell/`
- Provide platform-specific automation used by commands and workflows.
- Copied into `.specify/scripts/` during initialization.

### Extensions System

- File: `src/specify_cli/extensions.py`
- Responsibilities:
  - Validate extension manifests (`extension.yml`).
  - Install from directory or zip with safe extraction (zip-slip prevention).
  - Register commands into agent directories with placeholder conversion.
  - Maintain a registry in `.specify/extensions/.registry`.
  - Manage extension catalogs with cached fetches.

## Key Directories in a Bootstrapped Project

- `.specify/`
- `.specify/templates/` – spec, plan, tasks, constitution templates.
- `.specify/scripts/` – automation used by slash commands.
- `.specify/memory/` – constitution and shared memory files.
- `.specify/extensions/` – installed extensions and registry.
- `specs/` – feature specifications and generated artifacts.
- Agent command folders – e.g., `.claude/commands/`, `.gemini/commands/`, `.github/agents/`.

## Integration Points

- AI agent command files (Markdown or TOML) installed per agent.
- CLI tools for agent detection and optional checks (`claude`, `gemini`, `qwen`, `codex`, etc.).
- GitHub API for release discovery and template asset download.
- Local git initialization for new projects.

## Security and Operational Considerations

- Release downloads use HTTPS and can be authenticated via `GH_TOKEN`/`GITHUB_TOKEN`.
- Zip extraction validates paths to prevent path traversal (extensions) and merges safely for `--here`.
- Agent folders may contain credentials and are recommended for `.gitignore`.
- `--skip-tls` disables TLS verification (intended for troubleshooting only).

## Non-Goals

- Spec Kit does not execute remote models directly; it prepares the local project structure and commands.
- Spec Kit does not replace an agent; it standardizes how agents interact with the project.
- Spec Kit does not enforce a specific tech stack; it enforces a spec-first workflow.
