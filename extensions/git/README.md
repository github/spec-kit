# Git Branching Workflow Extension

Feature branch creation, numbering (sequential/timestamp), validation, and Git remote detection for Spec Kit.

## Overview

This extension provides Git branching operations as an optional, self-contained module. It manages:

- **Feature branch creation** with sequential (`001-feature-name`) or timestamp (`20260319-143022-feature-name`) numbering
- **Branch validation** to ensure branches follow naming conventions
- **Git remote detection** for GitHub integration (e.g., issue creation)

## Commands

| Command | Description |
|---------|-------------|
| `speckit.git.feature` | Create a feature branch with sequential or timestamp numbering |
| `speckit.git.validate` | Validate current branch follows feature branch naming conventions |
| `speckit.git.remote` | Detect Git remote URL for GitHub integration |

## Hooks

| Event | Command | Optional | Description |
|-------|---------|----------|-------------|
| `before_specify` | `speckit.git.feature` | No | Create feature branch before specification |
| `after_implement` | `speckit.git.validate` | Yes | Validate branch naming after implementation |

## Configuration

Configuration is stored in `.specify/extensions/git/git-config.yml`:

```yaml
# Branch numbering strategy: "sequential" or "timestamp"
branch_numbering: sequential
```

## Installation

```bash
# Install from the bundled extension directory
specify extension add --dev extensions/git
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
