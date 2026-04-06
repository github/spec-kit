# Git Branching Workflow Extension

Git repository initialization, feature branch creation, numbering (sequential/timestamp), validation, remote detection, and auto-commit for Spec Kit.

## Overview

This extension provides Git operations as an optional, self-contained module. It manages:

- **Repository initialization** with configurable commit messages
- **Feature branch creation** with sequential (`001-feature-name`) or timestamp (`20260319-143022-feature-name`) numbering
- **Branch validation** to ensure branches follow naming conventions
- **Git remote detection** for GitHub integration (e.g., issue creation)
- **Auto-commit** after core commands (configurable per-command with custom messages)

## Commands

| Command | Description |
|---------|-------------|
| `speckit.git.initialize` | Initialize a Git repository with a configurable commit message |
| `speckit.git.feature` | Create a feature branch with sequential or timestamp numbering |
| `speckit.git.validate` | Validate current branch follows feature branch naming conventions |
| `speckit.git.remote` | Detect Git remote URL for GitHub integration |
| `speckit.git.commit` | Auto-commit changes (configurable per-command enable/disable and messages) |

## Hooks

| Event | Command | Optional | Description |
|-------|---------|----------|-------------|
| `before_constitution` | `speckit.git.initialize` | No | Init git repo before constitution |
| `before_specify` | `speckit.git.feature` | No | Create feature branch before specification |
| `before_clarify` | `speckit.git.commit` | Yes | Commit outstanding changes before clarification |
| `before_plan` | `speckit.git.commit` | Yes | Commit outstanding changes before planning |
| `before_tasks` | `speckit.git.commit` | Yes | Commit outstanding changes before task generation |
| `before_implement` | `speckit.git.commit` | Yes | Commit outstanding changes before implementation |
| `before_checklist` | `speckit.git.commit` | Yes | Commit outstanding changes before checklist |
| `before_analyze` | `speckit.git.commit` | Yes | Commit outstanding changes before analysis |
| `before_taskstoissues` | `speckit.git.commit` | Yes | Commit outstanding changes before issue sync |
| `after_constitution` | `speckit.git.commit` | Yes | Auto-commit after constitution update |
| `after_specify` | `speckit.git.commit` | Yes | Auto-commit after specification |
| `after_clarify` | `speckit.git.commit` | Yes | Auto-commit after clarification |
| `after_plan` | `speckit.git.commit` | Yes | Auto-commit after planning |
| `after_tasks` | `speckit.git.commit` | Yes | Auto-commit after task generation |
| `after_implement` | `speckit.git.commit` | Yes | Auto-commit after implementation |
| `after_checklist` | `speckit.git.commit` | Yes | Auto-commit after checklist |
| `after_analyze` | `speckit.git.commit` | Yes | Auto-commit after analysis |
| `after_taskstoissues` | `speckit.git.commit` | Yes | Auto-commit after issue sync |

## Configuration

Configuration is stored in `.specify/extensions/git/git-config.yml`:

```yaml
# Branch numbering strategy: "sequential" or "timestamp"
branch_numbering: sequential

# Custom commit message for git init
init_commit_message: "[Spec Kit] Initial commit"

# Auto-commit per command (all disabled by default)
auto_commit:
  default: false
  after_specify:
    enabled: true
    message: "[Spec Kit] Add specification"
```

## Installation

```bash
# Install the bundled git extension (no network required)
specify extension add git
```

## Disabling

```bash
# Disable the git extension (spec creation continues without branching)
specify extension disable git

# Re-enable it
specify extension enable git
```

## Graceful Degradation

When Git is not installed or the directory is not a Git repository:
- Spec directories are still created under `specs/`
- Branch creation is skipped with a warning
- Branch validation is skipped with a warning
- Remote detection returns empty results

## Scripts

The extension bundles cross-platform scripts:

- `scripts/bash/create-new-feature.sh` — Bash implementation
- `scripts/bash/git-common.sh` — Shared Git utilities (Bash)
- `scripts/powershell/create-new-feature.ps1` — PowerShell implementation
- `scripts/powershell/git-common.ps1` — Shared Git utilities (PowerShell)
