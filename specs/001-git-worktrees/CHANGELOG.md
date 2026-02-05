# Git Worktree Support - Feature Changelog

**Feature Branch**: `001-git-worktrees`
**Date**: 2026-01-16
**AI Disclosure**: This feature was developed with assistance from Claude Code (Claude Opus 4.5).

## Overview

This feature adds comprehensive git worktree support to Spec Kit, allowing users to develop multiple features simultaneously in parallel directories rather than switching branches in a single working copy.

## Summary of Changes

### New CLI Options for `specify init`

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--git-mode` | `branch` / `worktree` | `branch` | Git workflow mode for feature development |
| `--worktree-strategy` | `sibling` / `nested` / `custom` | `sibling` | Where worktrees are created |
| `--worktree-path` | absolute path | - | Custom base path (required if strategy is `custom`) |

### Usage Examples

```bash
# Interactive mode (prompts for all options)
specify init my-project --ai claude

# Explicit worktree mode with sibling strategy
specify init my-project --ai claude --git-mode worktree --worktree-strategy sibling

# Worktree mode with nested strategy (inside .worktrees/)
specify init my-project --git-mode worktree --worktree-strategy nested

# Worktree mode with custom path
specify init my-project --git-mode worktree --worktree-strategy custom --worktree-path /tmp/worktrees
```

## Feature Details

### 1. Worktree Naming Convention

Worktree directories use a clear naming convention that includes the repository name:

| Strategy | Directory Format | Example |
|----------|-----------------|---------|
| **nested** | `<repo>/.worktrees/<branch>` | `spec-kit/.worktrees/001-user-auth` |
| **sibling** | `../<repo>-<branch>` | `../spec-kit-001-user-auth` |
| **custom** | `<path>/<repo>-<branch>` | `/tmp/worktrees/spec-kit-001-user-auth` |

### 2. Interactive Selection Flow

When options aren't provided via CLI, users get interactive arrow-key selection menus:

1. **AI Assistant Selection** (existing)
2. **Script Type Selection** (existing)
3. **Git Workflow Selection** (new) - Choose between `branch` or `worktree`
4. **Worktree Strategy Selection** (new, if worktree mode) - Choose `sibling`, `nested`, or `custom`
5. **Custom Path Prompt** (new, if custom strategy)

### 3. Configuration Storage

Settings are persisted to `.specify/config.json`:

```json
{
  "git_mode": "worktree",
  "worktree_strategy": "sibling",
  "worktree_custom_path": ""
}
```

This configuration is read by `create-new-feature.sh` and `create-new-feature.ps1` when creating new features.

### 4. Worktree Location Preview

After selecting worktree options, users see a preview of where features will be created:

```
Worktree preview: Features will be created at /Users/user/projects/my-project-<feature-branch>
```

### 5. Post-Init Worktree Notice

When worktree mode is enabled, a prominent notice is displayed:

```
╭─────────────────────────────── Worktree Mode ────────────────────────────────╮
│                                                                              │
│ Git Worktree Mode Enabled                                                    │
│                                                                              │
│ When you run /speckit.specify, each feature will be created in its own      │
│ directory alongside this repo (e.g., ../my-project-<feature-branch>).       │
│                                                                              │
│ Important: After creating a feature, you must switch your coding agent/IDE  │
│ to the new worktree directory to continue working on that feature.          │
│                                                                              │
│ To change this later, run: .specify/scripts/bash/configure-worktree.sh      │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 6. Agent Notification (specify.md Template)

The `/speckit.specify` command template now instructs agents to display a prominent warning when worktree mode is used:

```markdown
## ⚠️ ACTION REQUIRED: Switch to Worktree

This feature was created in **worktree mode**. Your files are in a separate directory:

**Worktree Path**: `/Users/user/projects/my-project-001-user-auth`

**You must switch your coding agent/IDE to this directory** before running any
subsequent commands (`/speckit.clarify`, `/speckit.plan`, `/speckit.implement`, etc.).
```

## Safety & Validation Improvements

### 1. Git Version Check

Worktree mode requires Git 2.5+. The CLI validates this before allowing worktree mode:

```
Error: Cannot use --git-mode worktree: Git 2.4 found, but worktree requires Git 2.5+
```

### 2. Conflict Detection

The CLI detects conflicting options:

```bash
$ specify init my-project --no-git --git-mode worktree
Error: Cannot use --git-mode worktree with --no-git (worktrees require git)
```

### 3. Git Availability Handling

- If git isn't installed, worktree prompts are skipped entirely
- If git is available but version < 2.5, a note is shown and branch mode is used

### 4. Automatic `.gitignore` Update

When using **nested** worktree strategy, `.worktrees/` is automatically added to `.gitignore`:

```gitignore
# Git worktrees (nested strategy)
.worktrees/
```

## Files Changed

### Core Implementation

| File | Changes |
|------|---------|
| `src/specify_cli/__init__.py` | Added CLI options, interactive selection, config writing, validation, previews, notices |
| `scripts/bash/create-new-feature.sh` | Updated `calculate_worktree_path()` for new naming convention |
| `scripts/powershell/create-new-feature.ps1` | Updated `Get-WorktreePath` for new naming convention |
| `templates/commands/specify.md` | Added worktree notification instructions for agents |

### Documentation

| File | Changes |
|------|---------|
| `WORKTREE_DESIGN.md` | Updated naming convention documentation |

### Supporting Scripts (Existing)

| File | Purpose |
|------|---------|
| `scripts/bash/configure-worktree.sh` | Change worktree settings after init |
| `scripts/powershell/configure-worktree.ps1` | PowerShell equivalent |

## New Functions Added

### Python (`src/specify_cli/__init__.py`)

```python
def get_git_version() -> Optional[Tuple[int, int, int]]:
    """Get the installed git version as a tuple (major, minor, patch)."""

def check_git_worktree_support() -> Tuple[bool, Optional[str]]:
    """Check if git version supports worktrees (requires 2.5+)."""
```

### New Constants

```python
GIT_MODE_CHOICES = {
    "branch": "Switch branches in place (traditional)",
    "worktree": "Parallel directories per feature"
}

WORKTREE_STRATEGY_CHOICES = {
    "sibling": "Alongside repo (../feature-name)",
    "nested": "Inside repo (.worktrees/feature-name)",
    "custom": "Custom path (specify location)"
}
```

## Testing Instructions

### Manual Testing

1. **Test interactive flow**:
   ```bash
   uv run specify init test-project --ai claude
   # Select "worktree" when prompted for git workflow
   # Select "sibling" for strategy
   # Verify preview shows correct path
   ```

2. **Test CLI options**:
   ```bash
   uv run specify init test-project --ai claude --git-mode worktree --worktree-strategy sibling
   ```

3. **Test validation**:
   ```bash
   # Should error
   uv run specify init test-project --no-git --git-mode worktree
   ```

4. **Test feature creation**:
   ```bash
   cd test-project
   # Run /speckit.specify in your AI agent
   # Verify worktree is created at ../test-project-<feature-branch>
   ```

### Verify Config Written

After init, check `.specify/config.json`:

```bash
cat test-project/.specify/config.json
```

Expected output:
```json
{
  "git_mode": "worktree",
  "worktree_strategy": "sibling",
  "worktree_custom_path": ""
}
```

## Backward Compatibility

- **Default behavior unchanged**: Without `--git-mode`, the CLI defaults to `branch` mode
- **Existing projects**: The `configure-worktree.sh` script allows changing settings after init
- **Script compatibility**: `create-new-feature.sh` reads config and falls back gracefully if not present

## Known Limitations

1. **Sandbox environments**: Sibling worktrees (`../`) may fail in restricted container environments if the parent directory isn't mounted
2. **IDE/Agent switching**: Users must manually switch their IDE or coding agent to the worktree directory after feature creation

## Future Considerations

- Add `specify worktree list` command to show active worktrees
- Add `specify worktree clean` command to prune orphaned worktrees
- Consider auto-detecting IDE and providing copy-paste commands for switching
