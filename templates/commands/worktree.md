---
description: Manage git worktrees for parallel AI agent development workflows
---

## Overview

This command provides full lifecycle management for git worktrees in spec-kit:
- **Default (no args)**: Create worktree for current feature branch
- **list**: Display all worktrees with status
- **remove [branch]**: Remove specific worktree
- **cleanup**: Remove all stale worktrees

## Usage

### Create Worktree (Default)

Creates a worktree for the current feature branch at `.worktrees/<branch-name>/`.

```bash
# Detect platform and run appropriate script
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    .specify/scripts/powershell/manage-worktrees.ps1 create
else
    .specify/scripts/bash/manage-worktrees.sh create
fi
```

### List Worktrees

Displays all worktrees with their status (active/stale/orphaned) and disk usage.

**Implementation**:
```bash
# Detect platform and source script
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    . .specify/scripts/powershell/manage-worktrees.ps1
    list_worktrees
else
    source .specify/scripts/bash/manage-worktrees.sh
    list_worktrees
fi
```

**Expected output**:
```
┌─────────────────────────────┬──────────────────────────────────────────┬────────────┬──────────────┐
│ Branch                      │ Path                                     │ Status     │ Disk Usage   │
├─────────────────────────────┼──────────────────────────────────────────┼────────────┼──────────────┤
│ → 001-feature-name          │ .worktrees/001-feature-name              │ active     │ 150M         │
│ 002-another-feature         │ .worktrees/002-another-feature           │ stale      │ 200M         │
└─────────────────────────────┴──────────────────────────────────────────┴────────────┴──────────────┘

Total worktrees: 2
Total disk usage: 350M
```

**Features**:
- Current branch highlighted with `→` prefix
- Table format with box-drawing characters
- Shows active (branch exists) and stale (branch deleted) worktrees
- Individual and total disk usage calculated

### Remove Worktree

Removes a specific worktree with safety checks for uncommitted changes.

**Implementation**:
```bash
# Detect platform and source script, then call remove_worktree
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    . .specify/scripts/powershell/manage-worktrees.ps1
    # With branch name argument
    remove_worktree "001-feature-name"
    # Or without argument for interactive selection
    # remove_worktree
else
    source .specify/scripts/bash/manage-worktrees.sh
    # With branch name argument
    remove_worktree "001-feature-name"
    # Or without argument for interactive selection
    # remove_worktree
fi
```

**Behavior**:
1. **Interactive menu** (if no branch specified):
   ```
   [specify] Select worktree to remove:

     1) 001-feature-name
     2) 002-another-feature
     0) Cancel

   Enter choice (0-2):
   ```

2. **Uncommitted changes warning**:
   - Checks for uncommitted changes using `git status --porcelain`
   - If detected, shows warning and requires "yes" confirmation
   - Displays list of uncommitted files before prompting

3. **Safe removal**:
   - Runs `git worktree remove <path> --force`
   - Cleans up directory if needed
   - Reports disk space reclaimed
   - **Never deletes** the feature branch or specs directory

### Cleanup Stale Worktrees

Automatically detects and batch-removes all stale worktrees (deleted branches or orphaned directories).

**Implementation**:
```bash
# Detect platform and source script, then call cleanup_stale_worktrees
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    . .specify/scripts/powershell/manage-worktrees.ps1
    cleanup_stale_worktrees
else
    source .specify/scripts/bash/manage-worktrees.sh
    cleanup_stale_worktrees
fi
```

**Behavior**:
1. **Automatic detection** of two types of stale worktrees:
   - **Deleted branch**: Git tracks the worktree but the branch no longer exists
   - **Orphaned**: Directory exists in `.worktrees/` but git doesn't track it

2. **Display summary** before removal:
   - Lists all detected stale worktrees
   - Shows path and disk usage for each
   - Displays total disk usage across all stale worktrees

3. **Batch confirmation**: Requires Y/N confirmation before proceeding
   - User must explicitly confirm to proceed with deletion

4. **Safe removal**:
   - Loops through each stale worktree
   - Uses `git worktree remove --force`
   - Cleans up directories if needed
   - Skips locked or in-use worktrees (git prevents removal automatically)
   - Shows progress with checkmarks (✓ removed, ✗ skipped)

5. **Summary report**:
   - Count of removed worktrees
   - Count of skipped worktrees (if any)
   - Total disk space reclaimed

## Features

- **Automatic creation**: Worktrees created automatically by `/speckit.specify`
- **Conflict handling**: Interactive prompts if worktree already exists (stop/cleanup/skip)
- **Status tracking**: List shows active, stale, or orphaned worktrees
- **Safe removal**: Warns about uncommitted changes before removing
- **Batch cleanup**: Removes all stale worktrees in one operation
- **Cross-platform**: Works on macOS, Linux, and Windows

## Requirements

- Git 2.5+ (worktree support)
- Spec-kit initialized with `specify init`
- Feature branch following ###-feature-name convention

## Benefits

Enable parallel AI agent development:
1. Main repo: Refine specifications, update plans
2. Worktree: Implement features, run tests

Both can work simultaneously without conflicts!
