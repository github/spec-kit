# Borgesoft Fork Changes

This document summarizes all changes made in the Borgesoft fork of spec-kit, as well as synchronizations between the wowsome project and this fork.

## New Features

### 1. `import-existing-product.sh` - Product Import Script

A new bash script for creating feature branches when importing existing product baselines.

**Location**: `scripts/bash/import-existing-product.sh`

**Usage**:
```bash
./import-existing-product.sh [--json] [--version <name>] [--no-branch] [version_identifier]
```

**Options**:
- `--json` - Output in JSON format
- `--version <name>` - Custom version name for the import (default: "import-baseline")
- `--no-branch` - Skip git branch creation (use current branch)
- `--help, -h` - Show help message

**Features**:
- Creates next sequential branch number by checking both `specs/` directory and git branches (local + remote)
- Creates directory structure:
  ```
  specs/###-import-[name]/
  ├── spec.md              # Copied from template
  ├── analysis/
  │   ├── architecture.md  # Placeholder
  │   ├── entities.md      # Placeholder
  │   └── features.md      # Placeholder
  └── checklists/          # Empty directory
  ```
- Sets `SPECIFY_FEATURE` environment variable for session persistence
- Works in both git and non-git repositories

**Output** (JSON mode):
```json
{
  "BRANCH_NAME": "001-import-baseline",
  "SPEC_DIR": "/path/to/specs/001-import-baseline",
  "SPEC_FILE": "/path/to/specs/001-import-baseline/spec.md",
  "ANALYSIS_DIR": "/path/to/specs/001-import-baseline/analysis",
  "IMPORT_DATE": "2025-12-08",
  "FEATURE_NUM": "001"
}
```

## Bug Fixes

### 1. Octal Conversion Fix in `create-new-feature.sh`

**Issue**: Branch numbers starting with `0` (like `010`) were being interpreted as octal numbers, causing incorrect feature numbering.

**Fix**: Added explicit base-10 interpretation:
```bash
# Before (problematic)
FEATURE_NUM=$(printf "%03d" "$BRANCH_NUMBER")

# After (fixed)
FEATURE_NUM=$(printf "%03d" "$((10#$BRANCH_NUMBER))")
```

This ensures `010` is interpreted as decimal `10`, not octal `8`.

## Code Improvements

### 1. Simplified `check_existing_branches` in `create-new-feature.sh`

**Before** (complex, pattern-matching approach):
```bash
check_existing_branches() {
    local short_name="$1"
    local specs_dir="$2"

    # Complex pattern matching against short_name
    local remote_branches=$(git ls-remote --heads origin 2>/dev/null | grep -E "refs/heads/[0-9]+-${short_name}$" | ...)
    local local_branches=$(git branch 2>/dev/null | grep -E "^[* ]*[0-9]+-${short_name}$" | ...)
    # ...
}
```

**After** (simplified, reuses existing functions):
```bash
check_existing_branches() {
    local specs_dir="$1"

    git fetch --all --prune 2>/dev/null || true

    # Get highest from ALL branches (not just matching)
    local highest_branch=$(get_highest_from_branches)
    local highest_spec=$(get_highest_from_specs "$specs_dir")

    local max_num=$highest_branch
    if [ "$highest_spec" -gt "$max_num" ]; then
        max_num=$highest_spec
    fi

    echo $((max_num + 1))
}
```

**Benefits**:
- Reduced code complexity
- Reuses existing helper functions
- More reliable branch number detection (doesn't depend on short name matching)

## Agent Support

The fork maintains support for 17 AI agents in `update-agent-context.sh`:

1. **Claude Code** (`CLAUDE.md`)
2. **Gemini CLI** (`GEMINI.md`)
3. **GitHub Copilot** (`.github/agents/copilot-instructions.md`)
4. **Cursor IDE** (`.cursor/rules/specify-rules.mdc`)
5. **Qwen Code** (`QWEN.md`)
6. **opencode** (`AGENTS.md`)
7. **Codex CLI** (`AGENTS.md`)
8. **Windsurf** (`.windsurf/rules/specify-rules.md`)
9. **Kilo Code** (`.kilocode/rules/specify-rules.md`)
10. **Auggie CLI** (`.augment/rules/specify-rules.md`)
11. **Roo Code** (`.roo/rules/specify-rules.md`)
12. **CodeBuddy CLI** (`CODEBUDDY.md`)
13. **Qoder CLI** (`QODER.md`) - *New in upstream*
14. **Amp** (`AGENTS.md`)
15. **SHAI** (`SHAI.md`)
16. **Amazon Q Developer CLI** (`AGENTS.md`)
17. **IBM Bob** (`AGENTS.md`)

## Command Updates (from wowsome)

### New Commands

#### 1. `import.md` - Codebase Analysis & Spec Generation

Analyzes existing codebases to generate product specifications, bootstrapping the speckit workflow for existing projects.

**Key Features**:
- Product documentation integration (vision, personas, journeys, MVP)
- Domain discovery for multi-team development
- Generates comprehensive analysis artifacts

**Generated Artifacts**:
- `spec.md` - Product specification with domains
- `analysis/architecture.md` - Architecture details
- `analysis/entities.md` - Data model documentation
- `analysis/features.md` - Feature inventory
- `analysis/domains.md` - **Domain separation for multi-team development**

#### 2. `iterate.md` - Feature Ideas to Linear Issues

Transforms natural language feature descriptions into Linear issues with TDD workflow.

**Key Features**:
- Creates parent User Story issue with TDD labels
- Generates TDD-ordered subtasks: `[TEST]` → `[IMPL]` → `[REFACTOR]`
- 3-level hierarchy for complex test breakdowns
- Task registry mapping task IDs to Linear issue IDs

**TDD Labels**:
- `tdd-red` - Test writing phase (RED)
- `tdd-green` - Implementation phase (GREEN)
- `tdd-refactor` - Refactoring phase

### Updated Commands

#### `implement.md` - Major Overhaul

Complete rewrite with Linear integration and strict TDD enforcement.

**Linear Integration**:
- Syncs with Linear project, maps issues to tasks.md
- Real-time status updates (Backlog → In Progress → Done)
- Acceptance criteria results in issue descriptions
- Phase completion updates Epic status

**TDD Enforcement**:
- Mandatory test execution after EVERY task
- Test gates block task completion on failures
- Coverage threshold enforcement (default: 80%)
- TDD cycle: RED → GREEN → REFACTOR

**Git Workflow**:
- Phase branches for each implementation phase
- Pull Request creation per phase
- Commit per completed task

#### `tasks.md` - TDD Task Generation

Updated with strict TDD task markers and validation.

**New Task Format**:
```
- [ ] [TaskID] [TDD] [P?] [Story?] Description with file path
```

**TDD Markers**:
- `[TEST]` - Write failing tests (must come FIRST)
- `[IMPL]` - Implementation to pass tests
- `[REFACTOR]` - Cleanup while keeping tests green

**TDD Validation**:
- Confirms every `[IMPL]` has preceding `[TEST]`
- Test framework setup mandatory in Phase 1

#### `taskstoissues.md` - Linear Migration

Complete rewrite migrating from GitHub to Linear.

**Issue Hierarchy**:
```
Feature Epic [epic, feature, tdd]
├── Phase Epic [epic, phase]
│   ├── [TEST] Task [test, tdd-red]
│   ├── [IMPL] Task [implementation, tdd-green]
│   └── [REFACTOR] Task [refactor, tdd-refactor]
```

**Features**:
- Creates TDD labels automatically
- Acceptance Criteria sections in every issue
- Task Registry in tasks.md
- Dependency tracking in descriptions

#### `plan.md` - Domain-Aware Planning

Updated with domain context for multi-team development.

**Domain Context**:
- Loads `analysis/domains.md` for domain boundaries
- Identifies primary/secondary domains per feature
- Requires contracts for cross-domain dependencies

**New Section**: Domain Context
```markdown
## Domain Context

### Target Domain(s)
| Domain | Role | Impact Level |
|--------|------|--------------|
| Auth   | Owner | High |
| Core   | Consumer | Medium |
```

**Phase 2 Domain Validation**:
- No shared entity ownership
- All cross-domain contracts defined
- Coupling concerns flagged

## Synchronization Notes

### From wowsome to spec-kit:
- `import-existing-product.sh` - New script for product imports
- `import.md` - New command for codebase analysis
- `iterate.md` - New command for Linear TDD workflow
- `implement.md` - Updated with Linear + TDD enforcement
- `tasks.md` - Updated with TDD markers
- `taskstoissues.md` - Rewritten for Linear
- `plan.md` - Updated with domain-aware planning

### From spec-kit to wowsome:
- `create-new-feature.sh` - Simplified function + octal fix
- `update-agent-context.sh` - Qoder CLI support

### Identical Files (no changes needed):
- `common.sh`
- `check-prerequisites.sh`
- `setup-plan.sh`
- All template files:
  - `spec-template.md`
  - `plan-template.md`
  - `tasks-template.md`
  - `checklist-template.md`
  - `agent-file-template.md`

### Project-Specific Files (not synced):
- `memory/constitution.md` - wowsome has a filled-in constitution specific to the Wowsome project; spec-kit has the generic template

## Version Information

- **Base version**: spec-kit v0.0.22
- **Fork date**: 2025-12-08
- **Last updated**: 2025-12-08
- **Changes documented in**: `CHANGELOG.md` under `[Unreleased] - Borgesoft Fork`
