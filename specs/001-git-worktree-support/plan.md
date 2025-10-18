# Implementation Plan: Git Worktree Integration

**Branch**: `001-git-worktree-support` | **Date**: 2025-10-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-git-worktree-support/spec.md`

## Summary

Add native git worktree support to spec-kit to enable parallel AI agent development workflows. When developers create feature specifications with `/speckit.specify`, automatically create isolated worktrees in `.worktrees/<branch-name>/` for parallel implementation work. Provide unified `/speckit.worktree` command with subcommands (list, remove, cleanup) for worktree lifecycle management. Query git directly without metadata tracking, following spec-kit's simplicity principles.

## Technical Context

**Language/Version**: Bash 4.0+ (Unix/Linux/macOS), PowerShell 5.1+ (Windows/cross-platform)
**Primary Dependencies**:
- Git 2.5+ (worktree support)
- readchar library (for interactive prompts in Python CLI if needed)
- Standard Unix tools: grep, sed, awk, du (bash version)
- PowerShell built-ins (Windows version)

**Storage**: Filesystem only (`.worktrees/` directory, `.gitignore` file)
**Testing**: Manual testing with multiple spec-kit feature branches, cross-platform validation
**Target Platform**: macOS, Linux, Windows (any platform running spec-kit)
**Project Type**: Single project (scripts integrated into existing spec-kit structure)
**Performance Goals**:
- Worktree creation <2s overhead
- List command <500ms even with 50+ worktrees
**Constraints**:
- Must not break existing spec-kit workflows
- Must work with `--no-git` repositories (graceful degradation)
- Must handle paths with spaces cross-platform
**Scale/Scope**:
- Support 50+ simultaneous worktrees per repository
- Work with repository sizes up to several GB
- Handle branch names up to 244 bytes (GitHub limit)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Spec-kit does not currently have a defined constitution. For this feature, we'll follow spec-kit's existing patterns:

### Simplicity Principles
- ✅ **Single-file scripts**: Keep bash/PowerShell scripts focused (one file per function)
- ✅ **No metadata tracking**: Query git directly, no state files
- ✅ **Hardcoded defaults**: Use `.worktrees/` directory, defer customization
- ✅ **Minimal dependencies**: Use only git CLI and shell builtins

### Integration Principles
- ✅ **Non-breaking**: Worktree creation failure doesn't break feature creation
- ✅ **Backward compatible**: Works with existing feature branches
- ✅ **Cross-platform**: Both bash and PowerShell implementations

### Quality Principles
- ✅ **Error handling**: Clear messages, graceful degradation
- ✅ **Safety**: Warn before destructive operations (uncommitted changes)
- ✅ **Consistency**: Follow existing spec-kit command patterns

**No violations** - This design adheres to spec-kit's existing patterns.

## Project Structure

### Documentation (this feature)

```
specs/001-git-worktree-support/
├── plan.md              # This file
├── research.md          # Phase 0: bash vs PowerShell patterns, git worktree best practices
├── data-model.md        # Phase 1: Worktree state model (queried from git)
├── quickstart.md        # Phase 1: Quick validation scenarios
└── contracts/           # Phase 1: Command interface specifications
    ├── worktree-create.md
    ├── worktree-list.md
    ├── worktree-remove.md
    └── worktree-cleanup.md
```

### Source Code (repository root)

```
scripts/
├── bash/
│   ├── common.sh                  # [EXISTING] Shared utilities
│   ├── create-new-feature.sh     # [MODIFY] Add worktree creation
│   └── manage-worktrees.sh       # [NEW] Worktree lifecycle functions
└── powershell/
    ├── common.ps1                 # [EXISTING] Shared utilities
    ├── create-new-feature.ps1    # [MODIFY] Add worktree creation
    └── manage-worktrees.ps1      # [NEW] Worktree lifecycle functions

.claude/commands/
└── speckit.worktree.md           # [NEW] Claude Code command

templates/commands/
└── worktree.md                   # [NEW] Command template for other agents

.gitignore                        # [MODIFY] Add .worktrees/ if not present
```

**Structure Decision**: Single project structure. This is a script-based feature that integrates directly into spec-kit's existing structure. No separate projects needed - bash and PowerShell scripts live side-by-side in `scripts/` as they do currently.

## Complexity Tracking

*No constitutional violations - this section intentionally left empty.*

## Phase 0: Research & Validation

### Research Tasks

1. **Git Worktree Command Investigation**
   - Study `git worktree add`, `list --porcelain`, `remove`, `prune` commands
   - Understand worktree locking mechanisms
   - Test behavior with uncommitted changes, branch deletion
   - Document error codes and failure modes

2. **Cross-Platform Path Handling**
   - Research bash vs PowerShell path manipulation for spaces
   - Test absolute path resolution across platforms
   - Validate `.worktrees/` creation with various repo locations
   - Document quoting strategies for each platform

3. **Interactive Prompt Patterns**
   - Review existing `specify init` arrow key navigation code
   - Investigate readchar library limitations (if used in Python CLI)
   - Research bash `read` with arrow keys vs simple number selection
   - Document cross-platform interactive prompt approach

4. **Disk Space Calculation**
   - Research `du` command for bash (disk usage)
   - Research PowerShell equivalent (`Get-ChildItem | Measure-Object`)
   - Test performance with large repositories
   - Document human-readable format conversion

5. **Integration Points**
   - Analyze `create-new-feature.sh` structure for insertion point
   - Review `common.sh` utilities for reusable functions
   - Study error handling patterns in existing scripts
   - Document integration strategy

### Research Output

See [research.md](./research.md) for detailed findings and decisions.

## Phase 1: Design & Contracts

### Data Model

**Note**: This feature uses git as the source of truth, not internal state. The "data model" describes what we query from git.

See [data-model.md](./data-model.md) for complete entity definitions:

- **Worktree**: Path, branch, HEAD commit, locked status
- **Feature Branch**: Name (###-feature-name pattern), exists in git, has worktree
- **Stale Worktree**: Directory exists, branch doesn't, or git doesn't track it

### API Contracts

Worktree commands follow spec-kit's slash command pattern. See [contracts/](./contracts/) for detailed specifications:

1. **`/speckit.worktree` (no args)** - Create worktree for current branch
   - Input: Current git branch (or `SPECIFY_FEATURE` env var)
   - Output: Worktree path, success/failure message
   - Errors: Not on feature branch, worktree exists, insufficient disk space

2. **`/speckit.worktree list`** - List all worktrees
   - Input: None
   - Output: Table with columns: Branch, Path, Status, Disk Usage
   - Status values: Active, Stale, Orphaned

3. **`/speckit.worktree remove [branch]`** - Remove specific worktree
   - Input: Optional branch name (interactive selection if omitted)
   - Output: Disk space reclaimed, success message
   - Prompts: Confirm if uncommitted changes exist

4. **`/speckit.worktree cleanup`** - Remove all stale worktrees
   - Input: None
   - Output: List of stale worktrees, batch confirmation prompt
   - Confirmation: Required before removal

### Key Functions

**In `scripts/bash/manage-worktrees.sh`**:

```bash
create_worktree()         # Create worktree with conflict handling
list_worktrees()          # Parse git worktree list, show status
remove_worktree()         # Safe removal with uncommitted change check
cleanup_stale_worktrees() # Detect and batch-remove orphaned worktrees
ensure_worktree_gitignore() # Add .worktrees/ to .gitignore if missing
get_worktree_status()     # Check if worktree is active/stale/orphaned
calculate_disk_usage()    # Get human-readable size for worktree
prompt_conflict_resolution() # Interactive: stop/cleanup/skip
```

**In `scripts/powershell/manage-worktrees.ps1`** (mirror of above with PowerShell idioms)

### Integration with Existing Scripts

**Modify `create-new-feature.sh`** (after line 191: `export SPECIFY_FEATURE`):

```bash
# NEW: Create worktree for parallel development
if [[ "$HAS_GIT" = true ]]; then
    source "$(dirname "${BASH_SOURCE[0]}")/manage-worktrees.sh"
    create_worktree "$BRANCH_NAME" || echo "Warning: Worktree creation failed (non-fatal)" >&2
fi
```

**Same integration for `create-new-feature.ps1`**

### Quickstart Validation

See [quickstart.md](./quickstart.md) for end-to-end test scenarios:

1. **Automatic Creation**: Run `/speckit.specify`, verify worktree exists
2. **Manual Creation**: Checkout existing branch, run `/speckit.worktree`
3. **List Worktrees**: Create multiple, delete branch, verify stale detection
4. **Remove Worktree**: Remove with uncommitted changes, verify prompt
5. **Cleanup**: Delete branches, run cleanup, verify batch removal

## Phase 2: Implementation Tasks

**Note**: Implementation tasks will be generated by `/speckit.tasks` command. This plan provides the technical foundation for that task generation.

### Task Categories

1. **Core Worktree Functions** (bash + PowerShell)
   - Implement `create_worktree()` with git commands
   - Implement `list_worktrees()` parsing `git worktree list --porcelain`
   - Implement `remove_worktree()` with safety checks
   - Implement `cleanup_stale_worktrees()` with batch logic

2. **Helper Utilities**
   - Implement `ensure_worktree_gitignore()`
   - Implement `get_worktree_status()` (active/stale/orphaned)
   - Implement `calculate_disk_usage()`
   - Implement `prompt_conflict_resolution()` (stop/cleanup/skip)

3. **Integration**
   - Modify `create-new-feature.sh` to call `create_worktree()`
   - Modify `create-new-feature.ps1` with same integration
   - Test integration doesn't break existing workflows

4. **Command Templates**
   - Create `.claude/commands/speckit.worktree.md`
   - Create `templates/commands/worktree.md` for other agents
   - Document subcommand structure (list, remove, cleanup)

5. **Documentation**
   - Update `CLAUDE.md` with worktree workflow section
   - Update `README.md` with parallel development examples
   - Add troubleshooting section for common worktree issues

6. **Testing & Validation**
   - Test all commands on macOS (bash)
   - Test all commands on Linux (bash)
   - Test all commands on Windows (PowerShell)
   - Test with spaces in repository paths
   - Test with `--no-git` repositories (graceful degradation)
   - Verify `.gitignore` updates work correctly

## Implementation Strategy

### Incremental Development

1. **Phase 1**: Core create function
   - Implement basic worktree creation in bash
   - Test with single worktree
   - Add to `create-new-feature.sh`

2. **Phase 2**: List and status
   - Parse `git worktree list --porcelain`
   - Detect stale worktrees
   - Display in table format

3. **Phase 3**: Remove and cleanup
   - Implement safe removal with prompts
   - Add batch cleanup for stale worktrees
   - Test disk space calculation

4. **Phase 4**: PowerShell parity
   - Port all bash functions to PowerShell
   - Test on Windows
   - Ensure identical behavior

5. **Phase 5**: Polish and docs
   - Add command templates
   - Update documentation
   - Create troubleshooting guide

### Testing Approach

**Manual Testing Checklist**:
- [ ] Create worktree automatically with `/speckit.specify`
- [ ] Create worktree manually with `/speckit.worktree`
- [ ] Handle conflict when worktree exists (stop/cleanup/skip)
- [ ] List worktrees with correct status
- [ ] Remove worktree with uncommitted changes (verify prompt)
- [ ] Remove worktree without uncommitted changes
- [ ] Cleanup stale worktrees after branch deletion
- [ ] Verify `.gitignore` contains `.worktrees/`
- [ ] Test with repository paths containing spaces
- [ ] Test with `--no-git` repository (graceful failure)
- [ ] Verify feature creation succeeds even if worktree creation fails

## Risk Mitigation

### Known Risks

1. **Git Version Compatibility**
   - Risk: Users with git <2.5 can't use worktrees
   - Mitigation: Check git version, provide clear error message
   - Fallback: Feature creation still works, just no worktree

2. **Disk Space Exhaustion**
   - Risk: Multiple worktrees consume significant disk space
   - Mitigation: Show disk usage in list command, easy cleanup
   - Warning: Alert when disk space low during creation

3. **Path Handling Issues**
   - Risk: Special characters or spaces in paths break scripts
   - Mitigation: Proper quoting in both bash and PowerShell
   - Testing: Explicit test cases with problematic paths

4. **Cross-Platform Inconsistencies**
   - Risk: Bash and PowerShell behave differently
   - Mitigation: Comprehensive testing on all platforms
   - Parity Check: Automated script to compare outputs

5. **Git State Corruption**
   - Risk: Interrupted operations leave git in bad state
   - Mitigation: Use git's built-in safety mechanisms
   - Recovery: Document `git worktree prune` for cleanup

## Success Metrics

These align with the success criteria in spec.md:

1. **Functional**: All worktree commands work on macOS, Linux, Windows
2. **Performance**: Creation <2s, listing <500ms (excluding git checkout time)
3. **Reliability**: 95%+ success rate in normal conditions
4. **Usability**: Users can perform basic operations without docs
5. **Safety**: Zero reports of data loss or branch corruption

## Open Questions

All resolved in spec phase. Implementation can proceed.

## Next Steps

1. ✅ Complete this plan
2. → Run `/speckit.tasks` to generate implementation task list
3. → Execute `/speckit.implement` to build the feature
4. → Test cross-platform functionality
5. → Update documentation
6. → Submit PR to spec-kit repository
