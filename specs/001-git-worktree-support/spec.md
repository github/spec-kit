# Feature Specification: Git Worktree Integration

**Feature Branch**: `001-git-worktree-support`
**Created**: 2025-10-17
**Status**: Draft
**Input**: User description: "Add native git worktree support to spec-kit enabling parallel AI agent development workflows. Automatically create worktrees when running /speckit.specify and provide worktree lifecycle management through unified /speckit.worktree command with subcommands for list, remove, and cleanup. All worktrees stored in .worktrees/ directory. Enable developers to run multiple AI coding agents simultaneously on different features without workspace conflicts. Query git worktree list directly with no metadata tracking."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Worktree Creation (Priority: P1)

When a developer creates a new feature specification using `/speckit.specify`, the system automatically creates an isolated git worktree for that feature. This enables immediate parallel development where the developer can refine the specification in the main repository while another AI agent implements the feature in the worktree, both working simultaneously without conflicts.

**Why this priority**: This is the core value proposition - enabling parallel AI agent workflows. Without automatic creation, adoption will be low as developers won't think to create worktrees manually.

**Independent Test**: Can be fully tested by running `/speckit.specify` with any feature description and verifying that a worktree directory is created at `.worktrees/<branch-name>/` and is properly linked to the feature branch. Delivers immediate value by allowing a developer to open two terminal windows and work on spec and implementation simultaneously.

**Acceptance Scenarios**:

1. **Given** I run `/speckit.specify` with a feature description, **When** the feature branch is created, **Then** a corresponding worktree is automatically created at `.worktrees/<branch-name>/` and linked to that branch
2. **Given** the `.worktrees/` directory doesn't exist, **When** the first worktree is created, **Then** `.worktrees/` is created and added to `.gitignore`
3. **Given** a worktree already exists for a branch, **When** I try to create it again, **Then** I am prompted with options: stop, cleanup (remove and recreate), or skip
4. **Given** worktree creation fails, **When** the error occurs, **Then** the feature branch and spec directory are still created successfully (worktree is optional)
5. **Given** I select "cleanup" when prompted about existing worktree, **When** the cleanup executes, **Then** the old worktree is removed and a fresh one is created

---

### User Story 2 - Manual Worktree Creation (Priority: P2)

For developers who have existing feature branches created before worktree support was added, they can run `/speckit.worktree` on that branch to create a worktree retroactively. This ensures the feature is backward-compatible and allows gradual adoption.

**Why this priority**: Essential for backward compatibility and migration. Allows users with existing feature branches to adopt the worktree workflow without starting over.

**Independent Test**: Can be fully tested by checking out an existing spec-kit feature branch (like `002-some-feature`) and running `/speckit.worktree`, then verifying the worktree is created. Delivers value by allowing existing work to benefit from parallel development.

**Acceptance Scenarios**:

1. **Given** I am on a valid feature branch (e.g., `001-user-auth`), **When** I run `/speckit.worktree`, **Then** a worktree is created at `.worktrees/001-user-auth/`
2. **Given** I am on the main branch, **When** I run `/speckit.worktree`, **Then** I receive an error explaining that worktrees are only for feature branches
3. **Given** I am in a subdirectory of the repository, **When** I run `/speckit.worktree`, **Then** the worktree is still created correctly in `.worktrees/` at the repository root
4. **Given** the branch doesn't follow spec-kit naming convention, **When** I run `/speckit.worktree`, **Then** I receive a clear error explaining the naming requirement (###-feature-name)

---

### User Story 3 - View Worktree Status (Priority: P2)

Developers working on multiple features need visibility into which worktrees exist, which branches they're tracking, and whether any are stale (orphaned). The list command provides this overview to help manage parallel work effectively.

**Why this priority**: Critical for managing multiple parallel features. Without visibility, developers will lose track of what worktrees exist and waste disk space on stale ones.

**Independent Test**: Can be fully tested by creating several worktrees, deleting some branches, and running `/speckit.worktree list` to verify accurate status reporting. Delivers value by providing clear visibility into the parallel development landscape.

**Acceptance Scenarios**:

1. **Given** I have multiple worktrees created, **When** I run `/speckit.worktree list`, **Then** I see a table showing branch name, path, and status for each worktree
2. **Given** I have deleted a feature branch but its worktree still exists, **When** I run `/speckit.worktree list`, **Then** that worktree is marked as "Stale"
3. **Given** I have no worktrees, **When** I run `/speckit.worktree list`, **Then** I see a message indicating zero worktrees exist
4. **Given** I am currently on a branch with a worktree, **When** I run `/speckit.worktree list`, **Then** my current branch's worktree is highlighted in the output
5. **Given** multiple worktrees exist, **When** I run `/speckit.worktree list`, **Then** I see total disk usage across all worktrees

---

### User Story 4 - Remove Specific Worktree (Priority: P3)

When finished with a feature implementation, developers can remove the worktree to reclaim disk space. The remove command provides safe removal with warnings about uncommitted changes and does not affect the feature branch or specifications.

**Why this priority**: Important for disk space management but not critical for core workflow. Developers can manually use `git worktree remove` if needed.

**Independent Test**: Can be fully tested by creating a worktree, making changes, and running `/speckit.worktree remove` to verify interactive selection, uncommitted change warnings, and successful removal. Delivers value by providing a safe, guided removal process.

**Acceptance Scenarios**:

1. **Given** I run `/speckit.worktree remove`, **When** multiple worktrees exist, **Then** I see an interactive menu to select which worktree to remove
2. **Given** I specify a branch name, **When** I run `/speckit.worktree remove 001-user-auth`, **Then** that worktree is removed without an interactive menu
3. **Given** the worktree has uncommitted changes, **When** I attempt to remove it, **Then** I receive a warning and must explicitly confirm removal
4. **Given** I successfully remove a worktree, **When** the removal completes, **Then** I see a message showing disk space reclaimed
5. **Given** I remove a worktree, **When** the removal completes, **Then** the feature branch and specs directory remain intact (only worktree is removed)

---

### User Story 5 - Clean Up Stale Worktrees (Priority: P3)

Over time, developers delete feature branches after merging but forget to remove worktrees, leaving orphaned directories. The cleanup command automatically detects and removes these stale worktrees to reclaim disk space.

**Why this priority**: Nice-to-have maintenance feature. Stale worktrees don't harm functionality, just waste disk space. Can be done manually if needed.

**Independent Test**: Can be fully tested by creating worktrees, deleting their branches, and running `/speckit.worktree cleanup` to verify automatic detection and batch removal. Delivers value by automating a tedious maintenance task.

**Acceptance Scenarios**:

1. **Given** I have deleted feature branches but their worktrees remain, **When** I run `/speckit.worktree cleanup`, **Then** I see a list of stale worktrees detected
2. **Given** stale worktrees are detected, **When** I confirm batch removal, **Then** all stale worktrees are removed and disk space is reported
3. **Given** no stale worktrees exist, **When** I run `/speckit.worktree cleanup`, **Then** I see a message indicating no cleanup needed
4. **Given** I am prompted for batch removal, **When** I decline, **Then** no worktrees are removed and the operation cancels safely

---

### Edge Cases

- What happens when the `.worktrees/` directory is manually deleted but git still tracks worktrees? System detects orphaned git worktree entries and offers to clean them up.
- How does system handle insufficient disk space during worktree creation? Clear error message indicating disk space issue, feature branch still created.
- What if user manually runs `git worktree remove` outside of spec-kit commands? The `/speckit.worktree list` command will still show accurate information by querying git directly.
- What happens if multiple branches point to the same worktree path (corrupt state)? Error detected and reported with instructions to manually resolve using `git worktree list` and `git worktree prune`.
- How does system handle worktree creation when branch name contains special characters? Branch names follow spec-kit conventions (###-kebab-case), which are already safe for filesystem paths.
- What if git worktree command fails due to permissions issues? Clear error message with specific git error and suggestion to check directory permissions.
- How does cleanup handle worktrees that are currently in use (open in another terminal)? Git prevents removal of in-use worktrees - system skips with warning and continues with other worktrees.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST automatically create a git worktree when `/speckit.specify` creates a new feature branch
- **FR-002**: System MUST store all worktrees in `.worktrees/<branch-name>/` directory relative to repository root
- **FR-003**: System MUST automatically add `.worktrees/` to `.gitignore` if not already present
- **FR-004**: System MUST provide interactive conflict resolution when a worktree already exists (options: stop, cleanup, skip)
- **FR-005**: System MUST allow manual worktree creation for existing feature branches via `/speckit.worktree` command
- **FR-006**: System MUST provide `/speckit.worktree list` command to display all worktrees with status information
- **FR-007**: System MUST mark worktrees as "Stale" when their corresponding branch no longer exists
- **FR-008**: System MUST provide `/speckit.worktree remove` command with interactive selection or branch name argument
- **FR-009**: System MUST warn users when attempting to remove worktrees with uncommitted changes
- **FR-010**: System MUST provide `/speckit.worktree cleanup` command to batch-remove stale worktrees
- **FR-011**: System MUST query `git worktree list --porcelain` directly without caching or metadata files
- **FR-012**: System MUST work cross-platform (bash scripts for Unix/Linux/macOS, PowerShell scripts for Windows)
- **FR-013**: System MUST validate that current branch follows spec-kit naming convention (###-feature-name) before creating worktrees
- **FR-014**: System MUST NOT delete feature branches or spec directories when removing worktrees
- **FR-015**: System MUST report disk space reclaimed after removing worktrees
- **FR-016**: System MUST continue feature creation even if worktree creation fails (worktree is optional enhancement)
- **FR-017**: System MUST use arrow key navigation for interactive prompts (consistent with `specify init` behavior)
- **FR-018**: System MUST handle spaces in repository paths correctly across all platforms

### Key Entities

- **Worktree**: An isolated working directory linked to a specific git branch, stored in `.worktrees/<branch-name>/` directory. Contains a full checkout of the repository at that branch's state. Enables parallel work without switching branches.
- **Feature Branch**: A git branch following spec-kit naming convention (###-feature-name) that represents a single feature specification. Has a corresponding directory in `specs/` and optionally a corresponding worktree in `.worktrees/`.
- **Stale Worktree**: A worktree directory that remains in `.worktrees/` but whose corresponding feature branch has been deleted. Identified by checking branch existence in `git branch --list`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can successfully run two AI agents simultaneously (one on main repo, one in worktree) without conflicts or workspace interference
- **SC-002**: Worktree creation adds no more than 2 seconds to `/speckit.specify` execution time
- **SC-003**: 95% of worktree operations (create, list, remove, cleanup) complete successfully without errors
- **SC-004**: Cleanup command successfully identifies and removes 100% of truly stale worktrees (branches deleted, directories remain)
- **SC-005**: Zero reports of worktree-related data loss, branch corruption, or spec directory deletion
- **SC-006**: Developers can create, list, and remove worktrees using intuitive commands without consulting documentation for basic usage
- **SC-007**: Cross-platform compatibility verified on macOS, Linux, and Windows with both bash and PowerShell scripts

## Assumptions *(mandatory)*

1. **Git Version**: Users have Git 2.5 or later installed (worktree support introduced in 2.5.0, July 2015)
2. **Disk Space**: Users have sufficient disk space for multiple worktrees (each worktree is a full repository checkout)
3. **Repository State**: Users are working in a valid git repository initialized by spec-kit
4. **Terminal Environment**: Users have a terminal that supports arrow key input for interactive menus
5. **Path Safety**: Repository paths do not contain exotic characters that break filesystem operations
6. **Single User**: Worktrees are intended for single-developer parallel work, not multi-user collaboration on same machine
7. **Branch Naming**: Users follow spec-kit branch naming conventions (###-feature-name)
8. **No Nested Worktrees**: Users will not attempt to create worktrees inside other worktrees

## Dependencies

- **Git CLI**: Requires git command-line tools installed and available in PATH
- **Bash/PowerShell**: Requires bash (Unix) or PowerShell (Windows) for script execution
- **Spec-kit Installation**: Requires spec-kit initialized via `specify init` with `.specify/` structure present
- **Write Permissions**: Requires write access to repository root to create `.worktrees/` directory

## Out of Scope

- **IDE Integration**: VS Code worktree support is handled by VS Code itself, not spec-kit
- **Worktree Switching**: Users manually `cd` to worktrees or open new terminals - no automatic switching
- **Custom Directories**: Initial release hardcodes `.worktrees/` - custom locations deferred to future release
- **Non-Spec-Kit Branches**: Worktree commands only work with spec-kit feature branches (###-feature-name)
- **Multi-User Scenarios**: Worktrees are per-machine, not designed for multiple developers on same machine
- **Automated Merging**: Users handle git merge/rebase operations manually using standard git workflow
- **Metadata Tracking**: No `.specify/worktrees.json` file - all state queried from git directly
- **Auto-Removal on Merge**: Worktrees are not automatically removed when branches are merged (requires manual cleanup or `/speckit.worktree cleanup`)

## Non-Functional Requirements

### Performance
- Worktree creation must complete within 2 seconds (excluding git checkout time which varies by repository size)
- Listing worktrees must complete within 500ms even with 50+ worktrees
- Cleanup operations must provide progress feedback for batch operations

### Usability
- All commands must provide clear success/failure messages with actionable next steps
- Interactive prompts must support keyboard navigation (arrows, Enter, Esc)
- Error messages must explain the problem and suggest solutions
- Help text must be available via `--help` flag for each subcommand

### Reliability
- Commands must handle git errors gracefully without corrupting repository state
- Failures in worktree operations must not affect feature branch or spec creation
- System must detect and prevent operations that could cause data loss (uncommitted changes)

### Documentation
- CLAUDE.md must include worktree workflow patterns and command reference
- README.md must include parallel development examples with multiple AI agents
- Troubleshooting section must cover common worktree issues

## Clarifications

All design decisions have been resolved through discussion. No clarifications needed at this time.

## Notes

This feature follows spec-kit's philosophy of keeping things simple:
- No metadata tracking (query git directly)
- Hardcoded directory (`.worktrees/`) with option to customize later if needed
- Single unified command with subcommands (not multiple separate commands)
- Worktree creation failure doesn't break core workflow (optional enhancement)

The implementation should integrate seamlessly with existing `create-new-feature.sh` script and work cross-platform with both bash and PowerShell versions.
