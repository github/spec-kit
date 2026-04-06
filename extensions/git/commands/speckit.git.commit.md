---
description: "Auto-commit changes after a Spec Kit command completes"
scripts:
  sh: ../../scripts/bash/auto-commit.sh
  ps: ../../scripts/powershell/auto-commit.ps1
---

# Auto-Commit Changes

Automatically stage and commit all changes after a Spec Kit command completes.

## Behavior

This command is invoked as a post-hook after core commands. It:

1. Checks `.specify/extensions/git/git-config.yml` for the `auto_commit` section
2. Looks up the specific event key (e.g., `after_specify`) to see if auto-commit is enabled
3. Falls back to `auto_commit.default` if no event-specific key exists
4. Uses the per-command `message` if configured, otherwise a default message
5. If enabled and there are uncommitted changes, runs `git add .` + `git commit`

## Execution

The hook system passes the event name to the script:

- **Bash**: `.specify/extensions/git/scripts/bash/auto-commit.sh after_specify`
- **PowerShell**: `.specify/extensions/git/scripts/powershell/auto-commit.ps1 after_specify`

## Configuration

In `.specify/extensions/git/git-config.yml`:

```yaml
auto_commit:
  default: false          # Global toggle — set true to enable for all commands
  after_specify:
    enabled: true          # Override per-command
    message: "[Spec Kit] Add specification"
  after_plan:
    enabled: false
    message: "[Spec Kit] Add implementation plan"
```

## Graceful Degradation

- If Git is not available or not a repository: skips silently
- If no config file exists: skips (disabled by default)
- If no changes to commit: skips with a message
