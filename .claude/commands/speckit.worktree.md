---
description: Manage git worktrees for parallel AI agent development workflows
---

## User Input

```text
$ARGUMENTS
```

## Overview

This command provides full lifecycle management for git worktrees in spec-kit:
- **Default (no args)**: Create worktree for current feature branch
- **list**: Display all worktrees with status
- **remove [branch]**: Remove specific worktree
- **cleanup**: Remove all stale worktrees

## Command Parsing

Parse `$ARGUMENTS` to determine subcommand:

1. **If empty or just branch name**: Create worktree (default behavior)
2. **If starts with "list"**: Execute list functionality
3. **If starts with "remove"**: Execute remove functionality
4. **If starts with "cleanup"**: Execute cleanup functionality

## Execution

### Default: Create Worktree

Run when no subcommand provided or user wants to create a worktree for existing branch.

```bash
# From repository root
.specify/scripts/bash/manage-worktrees.sh create
```

Or if the script is set up to be called directly, source it and call `create_worktree` with the current branch name from `get_current_branch`.

**Expected behavior**:
- Gets current branch using `get_current_branch()` from common.sh
- Validates branch follows ###-feature-name pattern
- Creates worktree at `.worktrees/<branch-name>/`
- Prompts if worktree exists (stop/cleanup/skip)
- Reports success with worktree path

**Error cases**:
- Not on a feature branch → "Error: Not on a feature branch. Use ###-feature-name pattern."
- Not in git repo → "Error: Not in a git repository"
- Invalid branch name → "Error: Branch doesn't follow spec-kit convention"

### List: Show All Worktrees

Run when user types `/speckit.worktree list`

**Implementation**:
```bash
# Source the script and call list_worktrees function
source .specify/scripts/bash/manage-worktrees.sh
list_worktrees
```

**Expected output**:
```
┌─────────────────────────────┬──────────────────────────────────────────┬────────────┬──────────────┐
│ Branch                      │ Path                                     │ Status     │ Disk Usage   │
├─────────────────────────────┼──────────────────────────────────────────┼────────────┼──────────────┤
│ → 001-git-worktree-support  │ .worktrees/001-git-worktree-support      │ active     │ 150M         │
│ 002-user-auth               │ .worktrees/002-user-auth                 │ stale      │ 200M         │
│ 003-payment-flow            │ .worktrees/003-payment-flow              │ active     │ 180M         │
└─────────────────────────────┴──────────────────────────────────────────┴────────────┴──────────────┘

Total worktrees: 3
Total disk usage: 530M
```

**Features**:
- Current branch highlighted with `→` prefix
- Table format with box-drawing characters
- Status per worktree (active/stale)
- Individual and total disk usage
- Empty state message if no worktrees exist

**Status definitions**:
- **active**: Branch exists and worktree tracked by git
- **stale**: Branch deleted but worktree remains
- **orphaned**: Directory exists but not tracked by git (won't appear in list)

### Remove: Delete Specific Worktree

Run when user types `/speckit.worktree remove [branch]`

**Implementation**:
```bash
# Source the script and call remove_worktree function
source .specify/scripts/bash/manage-worktrees.sh

# With branch name argument
remove_worktree "001-user-auth"

# Without argument (interactive selection)
remove_worktree
```

**Expected behavior**:
1. **If no branch arg**: Show interactive numbered menu to select worktree:
   ```
   [specify] Select worktree to remove:

     1) 001-git-worktree-support
     2) 002-user-auth
     3) 003-payment-flow
     0) Cancel

   Enter choice (0-3):
   ```

2. **Check for uncommitted changes**: Uses `check_uncommitted_changes()` function
   - If uncommitted changes detected, displays:
     ```
     [specify] Warning: Worktree '001-user-auth' has uncommitted changes!

     Uncommitted files:
      M src/file1.js
     ?? new-file.js

     Are you sure you want to remove this worktree? (yes/no):
     ```
   - User must type "yes" (not just "y") to confirm removal

3. **Execute removal**:
   - Runs `git worktree remove <path> --force`
   - Cleans up directory if it still exists after git command
   - **NEVER** deletes the feature branch or specs directory

4. **Report results**:
   ```
   [specify] Removing worktree for branch '001-user-auth'...
   [specify] Note: Feature branch and specs directory will be preserved
   [specify] Worktree removed successfully
   [specify] Disk space reclaimed: 150M
   ```

**Error cases**:
- Not in git repo → "Error: Not in a git repository"
- Worktree not found → "Error: Worktree not found at: .worktrees/<branch>"
- Invalid choice in menu → "Error: Invalid choice"
- User cancels → "Removal cancelled"

### Cleanup: Remove Stale Worktrees

Run when user types `/speckit.worktree cleanup`

**Implementation**:
```bash
# Source the script and call cleanup_stale_worktrees function
source .specify/scripts/bash/manage-worktrees.sh
cleanup_stale_worktrees
```

**Expected behavior**:
1. **Detect stale worktrees**: Two types detected automatically:
   - **Deleted branch**: Git tracks worktree but branch doesn't exist
   - **Orphaned**: Directory exists in `.worktrees/` but git doesn't track it

2. **Display detected worktrees**:
   ```
   [specify] Stale worktrees detected:

     1. 001-old-feature
        Path: /path/to/repo/.worktrees/001-old-feature
        Disk usage: 150M

     2. 002-deleted-branch
        Path: /path/to/repo/.worktrees/002-deleted-branch
        Disk usage: 200M

     3. 003-orphaned (orphaned)
        Path: /path/to/repo/.worktrees/003-orphaned
        Disk usage: 80M

   Total stale worktree disk usage: 430M

   Remove all stale worktrees? (Y/N):
   ```

3. **Batch confirmation**: User must type Y or y to proceed
   - Any other input cancels the operation

4. **Removal process**:
   - Loops through each stale worktree
   - Runs `git worktree remove <path> --force`
   - Cleans up directory if still exists
   - Skips locked/in-use worktrees with warning (git will prevent removal)
   - Displays progress with checkmarks:
     ```
     [specify] Removing stale worktrees...
       ✓ Removed: 001-old-feature
       ✓ Removed: 002-deleted-branch
       ✗ Skipped: 003-orphaned (locked or in use)
     ```

5. **Summary report**:
   ```
   [specify] Cleanup complete!
     Removed: 2 worktree(s)
     Skipped: 1 worktree(s)
     Total disk space reclaimed: 430M
   ```

**Empty state**:
- If no stale worktrees found: "[specify] No stale worktrees found"

**Safety features**:
- Only removes worktrees (never branches or specs)
- Git protects locked/in-use worktrees automatically
- Batch confirmation required before any deletion
- Clear feedback for each operation

## Implementation Notes

- All operations use `.specify/scripts/bash/manage-worktrees.sh` (or PowerShell equivalent)
- Query `git worktree list --porcelain` for current state (no metadata files)
- Worktrees stored in `.worktrees/<branch-name>/` (hardcoded location)
- Operations are non-destructive to branches and specs
- Error handling ensures feature creation isn't blocked by worktree failures

## Example Usage

```
# Create worktree for current branch
/speckit.worktree

# List all worktrees
/speckit.worktree list

# Remove specific worktree
/speckit.worktree remove 001-user-auth

# Remove all stale worktrees
/speckit.worktree cleanup
```
