# Git Worktree Integration for Spec-Kit

## Feature Overview

Add native git worktree support to spec-kit enabling parallel AI agent development workflows. When `/speckit.specify` creates a feature branch, automatically create a corresponding worktree in `.worktrees/` for isolated parallel development. Provide lifecycle management through a unified `/speckit.worktree` command with subcommands for listing, removing, and cleaning up worktrees.

## Problem Statement

Currently, spec-kit creates git branches for each feature but developers work in a single workspace. This prevents:
- Running multiple AI agents in parallel (one working on spec refinement in main repo while another implements in a worktree)
- Safe experimentation with different implementation approaches without affecting the main workspace
- True isolation between feature work and specification refinement
- Clean separation of concerns (specs maintained in main repo, implementations executed in worktrees)

The AI coding community has shown strong interest in combining worktrees with AI agents for parallel development (GitHub issue #518, multiple blog posts about "parallelizing AI coding agents"). This feature addresses that need while staying true to spec-kit's simplicity principles.

## User Stories

### US-1: Automatic Worktree Creation
**As a** developer using spec-kit to create a new feature
**I want** worktrees to be automatically created when I run `/speckit.specify`
**So that** I can immediately start parallel development without manual git commands

**Acceptance Criteria:**
- When `/speckit.specify` creates a new feature branch (e.g., `001-user-auth`), it automatically creates a corresponding worktree at `.worktrees/001-user-auth/`
- The worktree is properly linked to the feature branch via `git worktree add`
- The `.worktrees/` directory is automatically added to `.gitignore` if not already present
- Success message displays both branch name and worktree path for easy reference
- If worktree already exists at that path, user is prompted with clear options:
  - **Stop**: Cancel operation with error message
  - **Cleanup**: Remove old worktree and create fresh one
  - **Skip**: Keep existing worktree, continue without creating new one
- Interactive prompt uses arrow key navigation (consistent with AI assistant selection in `specify init`)
- If worktree creation fails, the feature branch and spec directory are still created successfully (worktree is optional)

### US-2: Manual Worktree Creation
**As a** developer with existing feature branches created before worktree support
**I want** to manually create worktrees for those branches
**So that** I can migrate existing features to the worktree workflow

**Acceptance Criteria:**
- Command `/speckit.worktree` (no arguments) creates a worktree for the current feature branch
- Detects current branch using same logic as other spec-kit commands (git + `SPECIFY_FEATURE` fallback)
- Validates that current branch follows spec-kit naming convention (001-*, 002-*, etc.)
- Same conflict handling as automatic creation (stop/cleanup/skip interactive prompt)
- Works from any directory within the repository (uses `git rev-parse --show-toplevel`)
- Reports full absolute path to created worktree
- Fails gracefully with helpful error message if not on a valid feature branch

### US-3: List Active Worktrees
**As a** developer managing multiple features in parallel
**I want** to see all my active worktrees at a glance
**So that** I know which features have worktrees and their current status

**Acceptance Criteria:**
- Command `/speckit.worktree list` displays all worktrees in table format
- For each worktree, display: branch name, relative path, absolute path, status
- Status indicators:
  - **Active**: Branch exists and worktree is tracked by git
  - **Stale**: Branch no longer exists but worktree directory remains
  - **Orphaned**: Directory exists but not tracked by `git worktree list`
- Highlight current branch's worktree (if any)
- Show total number of worktrees and total disk usage
- Parse `git worktree list --porcelain` for machine-readable output
- Filter to only show worktrees in `.worktrees/` directory (ignore other worktrees)
- Works correctly even if `.worktrees/` doesn't exist (reports zero worktrees)

### US-4: Remove Specific Worktree
**As a** developer finished with a feature implementation
**I want** to remove the worktree for that feature
**So that** I can free up disk space and keep my workspace clean

**Acceptance Criteria:**
- Command `/speckit.worktree remove` presents interactive selection of available worktrees
- Also accepts branch name argument: `/speckit.worktree remove 001-user-auth`
- Arrow key navigation for worktree selection (if no argument provided)
- Shows worktree details before removal: path, branch, disk usage
- Warns if worktree has uncommitted changes and requires explicit confirmation
- Safely executes `git worktree remove <path>` followed by directory cleanup
- Reports disk space reclaimed after removal
- Does NOT delete the feature branch (only removes worktree)
- Does NOT delete specs directory (only removes worktree)
- Provides clear success/failure messages with next steps

### US-5: Clean Up Stale Worktrees
**As a** developer who has deleted feature branches
**I want** to automatically detect and remove orphaned worktrees
**So that** I don't waste disk space on worktrees whose branches are gone

**Acceptance Criteria:**
- Command `/speckit.worktree cleanup` automatically detects stale worktrees
- A worktree is considered "stale" if:
  - Branch no longer exists (deleted via `git branch -d`), OR
  - Directory exists in `.worktrees/` but not tracked by `git worktree list` (orphaned)
- Displays list of stale worktrees with details: path, original branch, disk usage
- Prompts for batch confirmation before removing all stale worktrees
- Option to remove stale worktrees individually (interactive selection)
- Reports total disk space reclaimed after cleanup
- Safely handles locked or in-use worktrees (skip with warning)
- Suggests cleanup command when branch deletion warnings occur

## Functional Requirements

### FR-1: Worktree Directory Structure
- All worktrees MUST be created in `.worktrees/<branch-name>/` relative to repository root
- Directory naming MUST match feature branch naming exactly (001-feature, 002-feature, etc.)
- The `.worktrees/` directory MUST be automatically added to `.gitignore` if not present
- Script MUST create `.worktrees/` directory if it doesn't exist
- No environment variable for custom directory location (hardcoded `.worktrees/` initially)

### FR-2: Cross-Platform Support
- MUST work with both bash scripts (`scripts/bash/manage-worktrees.sh`) and PowerShell scripts (`scripts/powershell/manage-worktrees.ps1`)
- Interactive prompts MUST work on Windows, macOS, and Linux
- Path handling MUST use cross-platform compatible approaches
- MUST handle spaces in paths correctly on all platforms
- MUST respect platform-specific line endings

### FR-3: Integration with Existing Workflow
- Worktree creation MUST be seamlessly added to `/speckit.specify` command flow
- MUST NOT break existing spec-kit workflows for users who ignore worktrees
- If worktree creation fails, the feature branch and spec MUST still be created successfully
- MUST integrate with existing `create-new-feature.sh` script
- MUST respect `SPECIFY_FEATURE` environment variable for non-git repos
- MUST work correctly when `--no-git` flag was used during `specify init`

### FR-4: Single Unified Command Structure
- Single command: `/speckit.worktree [subcommand] [arguments]`
- Subcommands:
  - (no subcommand) - Create worktree for current branch (default behavior)
  - `list` - Display all worktrees
  - `remove [branch]` - Remove specific worktree
  - `cleanup` - Remove all stale worktrees
- MUST provide `--help` documentation for each subcommand
- MUST validate subcommand names and provide helpful errors for typos

### FR-5: Conflict Handling
- When a worktree already exists at the target path, MUST present interactive menu:
  - **Stop**: Exit with error code 1, no changes made
  - **Cleanup**: Run `git worktree remove`, delete directory, create fresh worktree
  - **Skip**: Continue without creating worktree, exit code 0
- MUST use arrow key navigation for selection (consistent with `specify init`)
- MUST show clear context in prompt (which branch, which path)
- MUST handle Ctrl+C gracefully (treat as Stop)

### FR-6: Safety and Validation
- NEVER remove worktrees with uncommitted changes without explicit user confirmation
- MUST validate git worktree operations succeed before updating filesystem
- MUST provide clear error messages when worktree operations fail
- MUST check for git availability before attempting worktree operations
- MUST handle locked worktrees gracefully (skip with warning)
- MUST validate branch names match spec-kit convention before creating worktrees

### FR-7: No Metadata Tracking
- MUST NOT create metadata files (no `.specify/worktrees.json`)
- MUST query `git worktree list --porcelain` directly each time
- Single source of truth: git itself
- Parse git output on-the-fly, no caching
- Keep implementation simple following spec-kit's existing pattern (no branch tracking either)

## Non-Functional Requirements

### NFR-1: Performance
- Worktree creation MUST add no more than 2 seconds to `/speckit.specify` execution time
- Listing worktrees MUST complete in under 500ms even with 50+ worktrees
- Cleanup operations MUST provide progress feedback for operations taking >2 seconds

### NFR-2: Usability
- All commands MUST provide clear, actionable feedback messages
- Interactive prompts MUST be keyboard-navigable (arrows, Enter, Esc)
- Help text MUST explain each subcommand's purpose and usage
- Error messages MUST suggest next steps for resolution
- Success messages MUST include relevant paths and context

### NFR-3: Documentation
- Update `CLAUDE.md` with worktree workflow patterns and command reference
- Update `README.md` with parallel development examples and use cases
- Add troubleshooting section for common worktree issues
- Document integration with existing spec-kit commands
- Provide examples of parallel AI agent workflows

## Technical Constraints

- Requires Git 2.5+ (git worktree support introduced)
- Must work with existing spec-kit installation and structure
- Must use bash or PowerShell (no Python dependencies in scripts)
- Must respect existing `.gitignore` patterns
- Must not interfere with other git operations (rebase, merge, etc.)

## Out of Scope

- Switching between worktrees (users use `cd` or open new terminal)
- IDE integration (VS Code worktree support is handled by VS Code itself)
- Worktree-specific `.gitignore` rules (use global `.gitignore`)
- Automatic worktree creation for non-spec-kit branches
- Merging worktree changes back to main (standard git workflow)
- Custom worktree directory location via environment variable (defer to future release)
- Worktree metadata tracking (not needed, query git directly)

## Success Metrics

- Users can successfully run multiple AI agents in parallel on different features
- Worktree operations complete successfully >99% of the time
- Cleanup command successfully recovers disk space from stale worktrees
- Zero reports of worktree-related data loss or branch corruption
- Positive community feedback on parallel development workflow
- At least 3 documented use cases of parallel AI agent workflows in docs

## Dependencies

- Git 2.5+ (worktree support)
- Existing spec-kit installation via `specify init`
- Bash (Unix/Linux/macOS) or PowerShell (Windows/cross-platform)
- Write access to repository root (to create `.worktrees/`)

## Risk Assessment

**Low Risk:**
- Git worktree is stable feature (10+ years old)
- No metadata to get out of sync (query git directly)
- Worktree failure doesn't break feature creation
- Operations are isolated to `.worktrees/` directory

**Mitigation Strategies:**
- Extensive error handling and validation
- Clear warning messages before destructive operations
- Dry-run capability for cleanup operations
- Comprehensive documentation and examples

## Open Questions

All questions resolved through discussion:

✅ **Auto-remove on branch deletion?**
Decision: Yes, but with warning message allowing user to skip if desired

✅ **Support custom directory location?**
Decision: No, hardcode `.worktrees/` initially. Can add `SPECIFY_WORKTREE_DIR` env var later if users request it

✅ **Track worktree status in metadata?**
Decision: No, query `git worktree list` directly. Follows spec-kit's existing pattern (no branch tracking either)

## Implementation Notes

This spec is ready for `/speckit.plan` phase. The implementation will need:
- New command template: `templates/commands/worktree.md`
- New helper scripts: `scripts/bash/manage-worktrees.sh` and `scripts/powershell/manage-worktrees.ps1`
- Updates to: `scripts/bash/create-new-feature.sh` (integrate automatic creation)
- Updates to: `scripts/powershell/create-new-feature.ps1` (integrate automatic creation)
- Updates to: `CLAUDE.md` (document new commands and workflow)
- Updates to: `README.md` (add parallel development section)
- Updates to: `.gitignore` template (ensure `.worktrees/` is ignored)
