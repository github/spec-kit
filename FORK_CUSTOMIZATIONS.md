# Fork Customizations - aloyxa1226/spec-kit

This document tracks all customizations made to this fork of `github/spec-kit`. It serves as a reference for upstream sync operations and helps prevent accidental loss of custom changes.

## Repository Information

- **Parent Repository**: `github/spec-kit`
- **Fork Repository**: `aloyxa1226/spec-kit`
- **Fork Created**: 2025-10-15
- **Purpose**: Custom enhancements and modifications to the Spec-Driven Development workflow

## Last Upstream Sync

- **Date**: Not yet performed (initial fork)
- **Upstream Commit**: [Record SHA on first sync]
- **Conflicts Resolved**: None yet
- **Status**: ✅ Clean fork

## Modified Files

### Documentation Files

#### `CLAUDE.md`
- **Status**: Added (fork-specific)
- **Reason**: Comprehensive guidance for Claude Code working in this repository
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-16
- **Upstream Conflicts**: None (fork-specific file)
- **Notes**: This file provides architectural overview and fork management guidelines
- **Recent Updates** (2025-10-16):
  - Enhanced Section 4: Implementation Phase with explicit Archon workflow
  - Added step-by-step implementation cycle (A-E)
  - Documented bulk task creation, one-task-at-a-time enforcement
  - Added critical rules checklist for Archon workflow
  - Inspired by `/execute-plan` from archon-example-workflow
  - **Added "CRITICAL: Script Consistency Rule" section** - Mandatory dual-script development policy (bash + PowerShell)

#### `FORK_CUSTOMIZATIONS.md`
- **Status**: Added (fork-specific)
- **Reason**: Track all fork customizations and sync history
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-15
- **Upstream Conflicts**: None (fork-specific file)
- **Notes**: This file itself

#### `docs/archon-integration-internals.md`
- **Status**: Added (fork-specific)
- **Reason**: Developer-only documentation for Archon MCP silent integration
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-16
- **Upstream Conflicts**: None (fork-specific file)
- **Notes**: Internal architecture for advanced users only, never in user-facing docs

### Archon MCP Integration Scripts

**CRITICAL**: All Archon integration files are fork-specific and completely silent. Regular users will never see these mentioned or know they exist. MCP-gated operation only.

#### `scripts/bash/archon-common.sh`
- **Status**: Added (fork-specific)
- **Reason**: Silent MCP detection and data mapping utilities
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-16
- **Upstream Conflicts**: None (fork-specific file, separate namespace)
- **Notes**: Completely silent operations, zero user visibility

#### `scripts/bash/archon-auto-init.sh`
- **Status**: Added (fork-specific)
- **Reason**: Silent project and document auto-creation
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-16
- **Notes**: Called in background by slash commands, zero output

#### `scripts/bash/archon-sync-documents.sh`
- **Status**: Added (fork-specific)
- **Reason**: Bidirectional document synchronization (pull-before/push-after)
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-16
- **Notes**: Ensures Spec Kit operates on latest Archon versions, completely silent

#### `scripts/bash/archon-auto-sync-tasks.sh`
- **Status**: Added (fork-specific)
- **Reason**: Silent task synchronization to Archon
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-16
- **Notes**: Parses tasks.md and creates Archon tasks automatically

#### `scripts/bash/archon-auto-pull-status.sh`
- **Status**: Added (fork-specific)
- **Reason**: Silent status sync from Archon to tasks.md
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-16
- **Notes**: Updates checkboxes based on Archon task status

#### `scripts/bash/archon-daemon.sh`
- **Status**: Added (fork-specific)
- **Reason**: Optional background sync daemon (advanced users only)
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-16
- **Notes**: NOT started automatically, NOT documented for regular users, opt-in only for advanced users

#### `scripts/bash/archon-inject-agent-docs.sh`
- **Status**: Added (fork-specific)
- **Reason**: Silently inject Archon workflow documentation into agent files during `specify init`
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-16
- **Notes**:
  - Called automatically by CLI after template extraction (bash variant)
  - Injects Archon workflow docs into CLAUDE.md, copilot-instructions.md, etc.
  - Only runs if Archon MCP is available (silent detection)
  - Completely transparent to users (zero output)
  - Inserts docs after "## Project Overview" section

#### `scripts/powershell/archon-inject-agent-docs.ps1`
- **Status**: Added (fork-specific)
- **Reason**: PowerShell variant of Archon doc injection for cross-platform support
- **Merge Strategy**: Keep ours (`--ours`)
- **Last Modified**: 2025-10-16
- **Notes**:
  - PowerShell equivalent of archon-inject-agent-docs.sh
  - Called when user selects PowerShell scripts (--script ps)
  - Identical functionality to bash version
  - Windows/cross-platform support

### Modified CLI

#### `src/specify_cli/__init__.py`
- **Status**: Modified (lines 489, 974-998)
- **Reason**: Point to fork repository + silent Archon doc injection on init (cross-platform)
- **Merge Strategy**: Manual merge required
- **Last Modified**: 2025-10-16
- **Upstream Conflicts**: Likely (actively maintained file)
- **Modification Details**:
  ```python
  # Line 489: Changed repository owner
  - repo_owner = "github"
  + repo_owner = "aloyxa1226"

  # Lines 974-998: Added silent Archon doc injection (bash + PowerShell)
  # After ensure_executable_scripts(), before git init:
  if selected_script == "sh":
      archon_inject_script = project_path / ".specify" / "scripts" / "bash" / "archon-inject-agent-docs.sh"
      if archon_inject_script.exists():
          subprocess.run(["bash", str(archon_inject_script)],
                        cwd=project_path, capture_output=True, timeout=5)
  else:  # PowerShell
      archon_inject_script = project_path / ".specify" / "scripts" / "powershell" / "archon-inject-agent-docs.ps1"
      if archon_inject_script.exists():
          subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(archon_inject_script)],
                        cwd=project_path, capture_output=True, timeout=5)
  ```
- **Impact**:
  - `specify init` downloads from fork with Archon integration
  - Archon workflow docs automatically injected into agent files when MCP available
  - Cross-platform support (bash for Unix, PowerShell for Windows)

### Modified Core Scripts

#### `scripts/bash/common.sh`
- **Status**: Modified
- **Reason**: Added silent sourcing of archon-common.sh
- **Merge Strategy**: Manual merge required
- **Last Modified**: 2025-10-16
- **Upstream Conflicts**: Possible (actively maintained file)
- **Notes**: Added 8 lines at end to silently source Archon utilities (2>/dev/null || true pattern)
- **Modification Details**:
  ```bash
  # Lines 157-163: Silent Archon integration
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  ARCHON_COMMON="$SCRIPT_DIR/archon-common.sh"
  if [[ -f "$ARCHON_COMMON" ]]; then
      source "$ARCHON_COMMON" 2>/dev/null || true
  fi
  ```

---

## Unmodified Files (Safe to Update from Upstream)

The following files remain unmodified and should be updated directly from upstream during syncs:

### Core Templates

All template files remain unmodified and should be updated directly from upstream during syncs:

- `templates/spec-template.md`
- `templates/plan-template.md`
- `templates/tasks-template.md`
- `templates/agent-file-template.md`
- `templates/checklist-template.md`

### Command Templates

#### `templates/commands/implement.md`
- **Status**: Modified (2025-10-16)
- **Reason**: Added Archon workflow enhancements from archon-example-workflow analysis
- **Merge Strategy**: Manual merge required
- **Last Modified**: 2025-10-16
- **Upstream Conflicts**: Possible (actively maintained file)
- **Modification Details**:
  ```markdown
  # Step 2: Silent Background Sync (lines 20-28)
  - Added silent Archon status pull before implementation

  # Step 9: Progress Tracking (line 127)
  - Added: "CRITICAL: Only ONE task in 'doing' status at any time in Archon"

  # Step 10: Post-Implementation Validation (lines 135-157)
  - Added comprehensive validation phase inspired by validator agent pattern
  - Validates TDD adherence (tests written before code per Article III)
  - Automated test verification (run full suite, check coverage)
  - Manual validation (user stories, quickstart scenarios)
  - Archon status updates (review → done only after validation)

  # Step 11: Completion Report (lines 159-168)
  - Enhanced with detailed metrics (total tasks, completed, in review)
  - Added test coverage and feature summary
  ```

#### `templates/commands/plan.md`
- **Status**: Modified (2025-10-16, 2025-10-17)
- **Reason**: Added brownfield analysis mode + interactive ignore pattern confirmation + Archon sync hooks
- **Merge Strategy**: Manual merge required
- **Last Modified**: 2025-10-17
- **Upstream Conflicts**: Possible (actively maintained file)
- **Modification Details**:
  ```markdown
  # Outline steps renumbered (1-7 instead of 1-4)

  # Step 2: Silent Background Sync (NEW 2025-10-17, lines 23-31)
  - Added silent Archon document pull before planning
  - Ensures we work with latest spec.md from Archon

  # Step 3: Detect Brownfield Mode (lines 33-36)
  - Added optional brownfield detection for existing codebases

  # Step 6: Silent Push to Archon (NEW 2025-10-17, lines 49-55)
  - Added silent Archon document push after planning
  - Syncs plan.md, research.md, data-model.md to Archon

  # New Section: Brownfield Analysis (lines 59-191)
  - Pattern discovery process for existing codebases
  - **NEW (2025-10-17)**: Interactive ignore pattern confirmation (lines 72-149)
    * Auto-detects large directories (>1000 files or >100MB)
    * Scans for common patterns (node_modules, bin, obj, *.min.js, etc.)
    * Presents interactive table with size/file counts
    * User chooses: A (exclude all), B (no filtering), C (custom), D (show samples)
    * Environment variable `$SPECKIT_IGNORE` for automation (skip prompt)
    * NO dotfiles created - everything done interactively
    * Prevents context overload with large files/dependencies
    * Applied to ALL Glob/Grep operations during analysis
  - Discovers: architecture patterns, naming conventions, testing patterns
  - Documents constraints (including exclusion metrics) in research.md
  - Feeds discovered patterns into plan generation
  - Only activates for codebases >20 files with established architecture
  ```

#### `templates/commands/specify.md`
- **Status**: Modified (2025-10-17)
- **Reason**: Added Archon sync hook to push spec.md after creation
- **Merge Strategy**: Manual merge required
- **Last Modified**: 2025-10-17
- **Upstream Conflicts**: Possible (actively maintained file)
- **Modification Details**:
  ```markdown
  # Outline steps renumbered (1-8 instead of 1-7)

  # Step 6: Silent push to Archon (NEW 2025-10-17, lines 75-83)
  - Added silent Archon document push after spec creation
  - Syncs spec.md to Archon MCP and creates project if needed
  - Zero output, never blocks, never fails
  ```

#### `templates/commands/tasks.md`
- **Status**: Modified (2025-10-17)
- **Reason**: Added Archon sync hooks for document pull and task creation
- **Merge Strategy**: Manual merge required
- **Last Modified**: 2025-10-17
- **Upstream Conflicts**: Possible (actively maintained file)
- **Modification Details**:
  ```markdown
  # Outline steps renumbered (1-7 instead of 1-5)

  # Step 2: Silent Background Sync (NEW 2025-10-17, lines 20-28)
  - Added silent Archon document pull before task generation
  - Ensures we work with latest plan.md, spec.md from Archon

  # Step 6: Silent push to Archon (NEW 2025-10-17, lines 59-65)
  - Added silent Archon task sync after tasks.md generation
  - Syncs tasks.md to Archon MCP and creates manageable tasks
  - Zero output, never blocks, never fails
  ```

#### Other Command Templates (unmodified - safe for upstream)
- `templates/commands/constitution.md`
- `templates/commands/clarify.md`
- `templates/commands/analyze.md`
- `templates/commands/checklist.md`

### Scripts (if unmodified)
- `scripts/bash/common.sh`
- `scripts/bash/create-new-feature.sh`
- `scripts/bash/setup-plan.sh`
- `scripts/bash/check-prerequisites.sh`
- `scripts/bash/update-agent-context.sh`
- `scripts/powershell/*.ps1`

### CLI Source
- `src/specify_cli/__init__.py`
- `pyproject.toml`

### Documentation

#### `README.md`
- **Status**: Modified (2025-10-16)
- **Reason**: Added brownfield mode documentation to make feature more discoverable
- **Merge Strategy**: Manual merge required
- **Last Modified**: 2025-10-16
- **Upstream Conflicts**: Possible (actively maintained file)
- **Modification Details**:
  - Added brownfield note in "Step 4" (quick start section)
  - Added comprehensive brownfield explanation in "STEP 4" (detailed walkthrough)
  - Documents automatic detection (>20 files), pattern discovery process, and research.md integration

#### Other Documentation (unmodified - safe for upstream)
- `spec-driven.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- `docs/*.md`

---

## Planned Customizations

Document planned modifications here before implementing them:

### High Priority
- [ ] None currently planned

### Medium Priority
- [ ] None currently planned

### Low Priority
- [ ] None currently planned

---

## Sync History

### Initial Fork (2025-10-15)
- **Action**: Forked from `github/spec-kit`
- **Upstream Commit**: e2f0f06 (Update installation commands in README)
- **Changes**: Added `.claude/CLAUDE.md` and `FORK_CUSTOMIZATIONS.md`
- **Status**: ✅ Successfully created fork with initial documentation

### Archon Workflow Enhancements (2025-10-16)
- **Action**: Analyzed archon-example-workflow and adapted best practices
- **Changes**:
  - Enhanced `templates/commands/implement.md` with validation phase and one-task-at-a-time enforcement
  - Added brownfield analysis mode to `templates/commands/plan.md`
  - Enhanced CLAUDE.md Section 4 with explicit Archon workflow documentation
  - Created `archon-inject-agent-docs.sh` for silent doc injection during project init
  - Modified CLI to call injection script after template extraction
- **Learnings Applied**:
  - ✅ Adopted: One task in "doing" at a time enforcement
  - ✅ Adopted: Post-implementation validation pattern (modified to respect TDD)
  - ✅ Adopted: Brownfield codebase analysis for plan.md
  - ✅ Adopted: Silent Archon workflow doc injection into agent files on init
  - ❌ Rejected: `validator` agent (violates Test-First Imperative)
  - ❌ Rejected: `codebase-analyst` agent (replaced with inline pattern in plan.md)
  - ❌ Rejected: `/create-plan` command (inferior to `/speckit.plan`)
- **Silent Integration Enhancement**:
  - Archon workflow docs now automatically appear in agent files (CLAUDE.md, etc.)
  - Only activates when Archon MCP server is available
  - Zero user visibility (completely transparent)
  - Injected after "## Project Overview" section
- **Status**: ✅ Enhanced SDD workflow with Archon best practices while maintaining constitutional integrity and silent integration model

### Archon Runtime Sync + Interactive Brownfield Filtering (2025-10-17)
- **Action**: Fixed Archon integration not executing during workflow + Added interactive confirmation for brownfield path exclusions
- **Changes**:
  - **Added Archon sync hooks to ALL workflow commands**:
    - `templates/commands/specify.md`: Added silent push after spec creation (step 6)
    - `templates/commands/plan.md`: Added silent pull (step 2) and push (step 6)
    - `templates/commands/tasks.md`: Added silent pull (step 2) and push (step 6 with task creation)
    - `templates/commands/implement.md`: Already had sync (step 2) - no changes needed
  - **Added interactive brownfield ignore pattern confirmation**:
    - Enhanced `templates/commands/plan.md` brownfield section (lines 72-149):
      - Auto-detection of large directories (>1000 files or >100MB)
      - Scan for common patterns: node_modules, bin, obj, dist, *.min.js, etc.
      - Interactive table showing detected directories with size/file count
      - User confirmation with 4 options:
        * A: Exclude all recommended (default)
        * B: No filtering (analyze everything)
        * C: Custom selection (pick individually)
        * D: Show sample files first
      - Environment variable override: `$SPECKIT_IGNORE` for silent automation
      - Documents exclusions in research.md with detailed metrics
  - **Documentation**: Updated `FORK_CUSTOMIZATIONS.md` with these enhancements
- **Problem Solved**:
  - ❌ **Before**: Archon integration only ran during `specify init` (CLI-level injection)
  - ✅ **After**: Archon sync runs automatically during EVERY workflow command
  - ❌ **Before**: Brownfield analysis could overload context with large files/dependencies
  - ✅ **After**: Interactive confirmation lets user decide what to exclude (no dotfiles needed)
- **User Impact**:
  - **Archon users**: Documents now sync automatically to/from Archon during workflow (completely silent)
  - **Brownfield users**: AI assistant detects and asks permission before excluding large directories
  - **No dotfiles**: No `.speckit-ignore` file clutter - everything done interactively
  - **Automation available**: Use `$SPECKIT_IGNORE` env var to skip confirmation
  - **No breaking changes**: All enhancements are additive and gracefully degrade if unavailable
- **Status**: ✅ Archon integration now fully operational + Brownfield analysis with user-friendly interactive filtering

---

## Merge Conflict Resolution Guidelines

### Automatic Resolution (Keep Ours)
Use `git checkout --ours <file>` for:
- `.claude/CLAUDE.md`
- `FORK_CUSTOMIZATIONS.md`
- Any file explicitly listed as "Keep ours" in Modified Files section

### Automatic Resolution (Keep Theirs)
Use `git checkout --theirs <file>` for:
- Files listed in "Unmodified Files" section
- Security patches and bug fixes
- Core functionality improvements

### Manual Review Required
Carefully merge both changes for:
- Command templates with custom modifications
- Scripts with fork-specific logic additions
- Templates with extended sections
- CLI modifications that need upstream bug fixes

### Priority Rules
1. **Security fixes**: ALWAYS take upstream immediately
2. **Bug fixes**: Prefer upstream, verify doesn't break customizations
3. **New features**: Evaluate compatibility with fork customizations
4. **Documentation**: Merge both (upstream + fork-specific additions)
5. **Custom enhancements**: Keep fork version, cherry-pick useful upstream changes

---

## Testing Checklist After Sync

After each upstream sync, verify:

- [ ] CLI installs correctly: `uvx --from . specify init test-project`
- [ ] All slash commands work: `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`
- [ ] Scripts execute without errors: `bash scripts/bash/check-prerequisites.sh --json`
- [ ] Templates generate correctly: Verify `spec.md`, `plan.md`, `tasks.md` format
- [ ] No merge conflict artifacts remain in files (search for `<<<<<<<`, `=======`, `>>>>>>>`)
- [ ] Custom modifications still present and functional
- [ ] Documentation updated with sync information

---

## Notes

- Always create backup branch before syncing: `git branch backup-fork-main-$(date +%Y%m%d)`
- Test thoroughly in a separate test project before merging to main
- Update this file immediately after each sync with new modifications and resolutions
- Keep commit messages descriptive: `sync: Merge upstream changes (SHA)`
- Document any breaking changes or major differences from upstream

---

## Contact

For questions about these customizations:
- **Repository**: https://github.com/aloyxa1226/spec-kit
- **Parent Repository**: https://github.com/github/spec-kit

---

**Last Updated**: 2025-10-16
