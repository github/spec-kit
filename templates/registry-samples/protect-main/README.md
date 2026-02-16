# protect-main

Prevents AI agents from committing directly to `main` or `master` branches.

## What it does

This hook intercepts `git commit` commands and checks the current branch. If you're on `main` or `master`, the commit is blocked with a message suggesting you create a feature branch first.

## How it works

- **Event**: `PreToolUse` (fires before any Bash command runs)
- **Matcher**: `Bash` (only checks shell commands)
- **Exit code 2**: Blocks the action and shows the error message

The hook reads the tool input JSON from stdin, extracts the command, and only activates for `git commit` commands.

## Installed files

| File | Purpose |
|------|---------|
| `.minispec/hooks/scripts/protect-main.sh` | The guard script |
| `.claude/settings.json` | Claude Code hooks config (merged) |

## Customization

Edit `.minispec/hooks/scripts/protect-main.sh` to:

- Add more protected branches (e.g., `develop`, `release/*`)
- Allow certain commit patterns (e.g., version bumps)
- Change the error message
