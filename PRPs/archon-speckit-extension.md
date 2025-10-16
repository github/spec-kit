# Implementation Plan: Archon-Spec Kit Silent Integration Extension

## Overview

This plan outlines the development of a **completely transparent extension layer** for Spec Kit that silently integrates with the Archon MCP server when available. The integration is **invisible to regular users** - they will never know Archon exists unless they explicitly enable the MCP server. The extension operates as a **zero-configuration, silent enhancement** that only activates when the Archon MCP server is detected.

## Core Philosophy: Silent Bidirectional Integration

**Key Principles**:
1. **Zero User-Facing Changes**: No new slash commands, no UI changes, no documentation for regular users
2. **MCP Detection Only**: Extension activates ONLY if Archon MCP server responds to health check
3. **Silent Fallback**: If Archon unavailable, do absolutely nothing (no errors, no warnings, no logs)
4. **Bidirectional Sync**: All artifacts (spec.md, plan.md, tasks.md, research.md, etc.) sync to/from Archon
5. **Archon as Source of Truth**: Spec Kit always operates on latest version from Archon (silent pull before operations)
6. **Advanced User Discovery**: Only developers and advanced users who read fork documentation know about Archon
7. **No Configuration Required**: Works automatically when MCP is available, disabled when it's not

## Requirements Summary

### Core Requirements
- **Silent Bidirectional Document Sync**: All artifacts (spec.md, plan.md, research.md, tasks.md, etc.) sync to/from Archon
- **Archon as Source of Truth**: Spec Kit pulls latest versions before each operation
- **Silent Project Tracking**: Automatically create Archon projects and documents in background
- **Silent Task Synchronization**: Automatically sync tasks to Archon if MCP available (zero user interaction)
- **Silent RAG Enhancement**: Automatically enhance research with knowledge base if available
- **Completely Invisible**: Regular users never see "Archon" mentioned anywhere in their workflow
- **Zero-Config**: No `.archon-config.json`, no setup commands, no user-facing options
- **MCP-Gated**: All Archon features gated behind MCP server availability check
- **Automatic Conflict Resolution**: Archon always wins (latest timestamp), no user prompts

### Technical Constraints
- Python 3.11+ for CLI extensions
- Bash/PowerShell for script extensions
- Follow existing Spec Kit patterns (JSON output, absolute paths, phase-based execution)
- Preserve fork management workflow documented in `FORK_CUSTOMIZATIONS.md`
- **NO** new slash commands visible to users
- **NO** user-facing error messages about Archon
- **NO** configuration files
- Archon operations must be **completely silent** (no stdout/stderr for regular users)

### Success Criteria
- [x] Automated Archon project creation when `/speckit.specify` completes (if MCP available) ✅
- [x] **Bidirectional document sync**: spec.md, plan.md, research.md, tasks.md ↔ Archon documents ✅
- [x] **Pull-before-operation**: All SIX commands pull latest from Archon before execution ✅
- [x] **Push-after-generation**: All SIX commands push updates to Archon after completion ✅
- [x] Automated Archon task creation from `tasks.md` generation (if MCP available) ✅
- [x] Archon RAG integration in `/speckit.plan` research phase (if MCP available) ✅
- [x] Silent status synchronization (Archon ↔ tasks.md) (if MCP available) ✅
- [x] **Spec Kit operates on latest Archon artifacts** (always up-to-date) ✅
- [x] **Zero indication of Archon existence for regular users** ✅
- [x] Extension completely dormant if MCP unavailable (no errors, no warnings) ✅
- [x] Upstream sync process remains functional ✅
- [x] Documentation ONLY in fork-specific files (FORK_CUSTOMIZATIONS.md, CLAUDE.md) ✅

**Phase 3 Achievement**: All six commands (specify, plan, tasks, implement, analyze, clarify) now have complete pull-before/push-after hooks implemented, ensuring seamless bidirectional synchronization with Archon MCP server.

---

## Research Findings

### Best Practices from Codebase Analysis

**Slash Command Architecture**:
- Command templates use YAML frontmatter with script paths
- Scripts must output JSON with absolute paths when called with `--json` flag
- AI agents parse JSON to locate files for read/write operations
- Commands organized in `templates/commands/` with `.md` extension

**Script Patterns**:
- All scripts source `scripts/bash/common.sh` for shared utilities
- Error handling: `set -e`, `set -u`, `set -o pipefail`
- Git detection with fallback to `SPECIFY_FEATURE` env variable
- Feature lookup via numeric prefix matching (`001-*`)

**Agent Context Management**:
- Agent-specific files updated via `update-agent-context.sh`
- Tech stack extracted from `plan.md` and propagated to agent files
- Recent changes tracked (last 3 entries)
- Timestamp updates for each modification

**Task Format (from tasks.md analysis)**:
```
- [ ] [TaskID] [P?] [Story?] Description with file path
```
- TaskID: Sequential (T001, T002, T003...)
- [P]: Parallel execution marker
- [Story]: User story label (US1, US2, etc.)
- Description: Action + exact file path

### Reference Implementations

**Similar Integration Patterns**:
1. **`/speckit.tasks` command** (templates/commands/tasks.md:1-100)
   - Loads multiple docs (plan.md, spec.md, data-model.md, etc.)
   - Generates structured output (tasks.md)
   - Uses check-prerequisites.sh for validation
   - **Pattern to replicate** for Archon task sync

2. **`/execute-plan` command** (.claude/commands/execute-plan.md:1-50)
   - Creates Archon project upfront
   - Creates all tasks in Archon before implementation
   - Maintains task status throughout execution
   - **Pattern to replicate** for automated sync

3. **`update-agent-context.sh`** (scripts/bash/update-agent-context.sh)
   - Parses markdown files for structured data
   - Updates multiple agent-specific files
   - Preserves manual additions
   - **Pattern to replicate** for bidirectional sync

### Technology Decisions

| Decision | Technology | Rationale |
|----------|-----------|-----------|
| Extension Commands | Markdown templates with YAML frontmatter | Follows existing slash command pattern |
| Script Language | Bash (with PowerShell variants) | Maintains consistency with Spec Kit architecture |
| Data Format | JSON for script output | Enables AI parsing of absolute paths |
| MCP Integration | Direct MCP tool calls in command templates | Leverages existing Archon MCP server connection |
| Configuration | Environment variables + .archon-config.json | Non-invasive, per-project configuration |
| State Management | Archon MCP server as source of truth | Persistent across sessions, multi-agent compatible |

---

## Implementation Tasks

### Phase 1: Foundation & Silent Detection (Setup)

#### 1.1 Create Silent Archon Utilities

**Task**: Create internal Archon utilities (completely hidden from users)
- **Description**: Implement silent MCP detection and data mapping utilities
- **Files to create**:
  - `scripts/bash/archon-common.sh` - Internal Archon utilities
  - `scripts/bash/.archon-state/` - Hidden state directory for mappings
- **Dependencies**: None
- **Estimated effort**: 2 hours
- **Details**:
  ```bash
  # archon-common.sh

  # Silent MCP detection - returns 0 if available, 1 if not
  # NO stdout/stderr output
  check_archon_available() {
    # Suppress ALL output
    if command -v mcp__archon__health_check &>/dev/null; then
      mcp__archon__health_check &>/dev/null && return 0
    fi
    return 1
  }

  # Silent project ID storage in hidden state file
  save_project_mapping() {
    local feature_name="$1"
    local project_id="$2"
    mkdir -p "$(get_repo_root)/.specify/scripts/bash/.archon-state"
    echo "$project_id" > "$(get_repo_root)/.specify/scripts/bash/.archon-state/${feature_name}.pid"
  }
  ```

#### 1.2 Add Silent MCP Detection to Common Scripts

**Task**: Integrate silent Archon detection into existing common.sh
- **Description**: Add MCP availability check without any user-visible changes
- **Files to modify**:
  - `scripts/bash/common.sh` - Add source for archon-common.sh at end
- **Dependencies**: 1.1
- **Estimated effort**: 0.5 hours
- **Details**:
  ```bash
  # At end of common.sh

  # Silently source Archon utilities if they exist
  # This has zero impact if files don't exist
  ARCHON_COMMON="$SCRIPT_DIR/archon-common.sh"
  if [[ -f "$ARCHON_COMMON" ]]; then
    source "$ARCHON_COMMON" 2>/dev/null || true
  fi
  ```

#### 1.3 Create Fork-Only Documentation

**Task**: Document Archon integration in fork-specific files ONLY
- **Description**: Update fork documentation (never in user-facing docs)
- **Files to modify**:
  - `FORK_CUSTOMIZATIONS.md` - Add Archon section
  - `CLAUDE.md` - Update with silent integration notes
- **Files to create**:
  - `docs/archon-integration-internals.md` - Developer-only documentation
- **Dependencies**: None
- **Estimated effort**: 1.5 hours
- **Details**:
  - Document in FORK_CUSTOMIZATIONS.md that Archon integration exists
  - Explain it's completely silent and MCP-gated
  - NO mention in README.md or user-facing docs
  - Only advanced users reading fork docs will discover this

### Phase 2: Silent Backend Integration (Foundational)

#### 2.1 Create Silent Project and Document Auto-Creation

**Task**: Silently create Archon project AND sync all initial documents
- **Description**: Background script called by existing commands (completely silent)
- **Files to create**:
  - `scripts/bash/archon-auto-init.sh` - Silent project and document creation
- **Dependencies**: 1.1, 1.2
- **Estimated effort**: 3 hours
- **Workflow** (ALL silent, zero output):
  1. Check if Archon MCP available (via check_archon_available)
  2. If not available: exit 0 (success, do nothing)
  3. If available: Load spec.md to extract feature name and description
  4. Create Archon project via `manage_project("create", ...)` 2>&1 >/dev/null
  5. Store project_id in hidden state file (.archon-state/${feature}.pid)
  6. **NEW**: Create Archon document for spec.md via `manage_document("create", document_type="spec", content=...)` 2>&1 >/dev/null
  7. Store document_id mapping in .archon-state/${feature}.docs
  8. Exit 0 (never fail, never output anything)
- **Critical**: Script MUST suppress ALL output, even on errors

#### 2.2 Create Silent Bidirectional Document Sync

**Task**: Pull latest documents from Archon before operations, push after
- **Description**: Ensures Spec Kit always operates on latest Archon versions
- **Files to create**:
  - `scripts/bash/archon-sync-documents.sh` - Bidirectional document sync
- **Dependencies**: 2.1
- **Estimated effort**: 4 hours
- **Workflow** (ALL silent, zero output):
  1. Check if Archon MCP available
  2. If not available: exit 0 (do nothing)
  3. Load project_id and document mappings from state files
  4. **PULL phase** (before operation):
     - For each document type (spec, plan, research, data-model, etc.):
       - Query Archon via `find_documents(project_id, document_type=...)` 2>&1 >/dev/null
       - If document exists and is newer than local: overwrite local file silently
       - If document doesn't exist locally but exists in Archon: create local file
  5. **PUSH phase** (after operation):
     - For each local document that changed:
       - If document_id exists: `manage_document("update", ...)` 2>&1 >/dev/null
       - If new document: `manage_document("create", ...)` 2>&1 >/dev/null
       - Update document_id mapping in state files
  6. Exit 0 (never fail, never output)

#### 2.3 Create Silent Task Auto-Sync

**Task**: Silently synchronize tasks.md to Archon when generated
- **Description**: Background script to sync tasks (completely silent)
- **Files to create**:
  - `scripts/bash/archon-auto-sync-tasks.sh` - Silent task sync
- **Dependencies**: 2.1
- **Estimated effort**: 3 hours
- **Workflow** (ALL silent, zero output):
  1. Check if Archon MCP available
  2. If not available: exit 0 (do nothing)
  3. Load project_id from hidden state file
  4. If no project_id: silently create project first
  5. Parse tasks.md format: `- [ ] [TaskID] [P?] [Story?] Description`
  6. For each task, silently call `manage_task("create", ...)` 2>&1 >/dev/null
  7. Store task mappings in .archon-state/${feature}.tasks
  8. Exit 0 (never fail, never output)

#### 2.4 Create Silent Status Pull Mechanism

**Task**: Silently pull Archon task status and update tasks.md checkboxes
- **Description**: Background sync from Archon to tasks.md (completely silent)
- **Files to create**:
  - `scripts/bash/archon-auto-pull-status.sh` - Silent status sync
- **Dependencies**: 2.1, 2.3
- **Estimated effort**: 2.5 hours
- **Workflow** (ALL silent, zero output):
  1. Check if Archon MCP available
  2. If not available: exit 0 (do nothing)
  3. Load project_id and task mappings from state files
  4. Query Archon for task statuses via `find_tasks(...)` 2>&1 >/dev/null
  5. Update tasks.md checkboxes: `done` → `[X]`, others → `[ ]`
  6. Exit 0 (never fail, never output)

### Phase 3: Silent Hook Integration (Enhancement) ✅ COMPLETED

**Status**: All six commands now have pull-before/push-after hooks implemented.

**Completed**: All four core commands (specify, plan, tasks, implement) plus two enhancement commands (analyze, clarify) now show pull-before/push-after bidirectional sync hooks.

#### 3.1 Add Bidirectional Sync to `/speckit.specify` ✅

**Task**: Pull latest spec before editing, push after generation
- **Status**: ✅ COMPLETED
- **Description**: Modify specify command to sync documents bidirectionally
- **Files modified**:
  - `templates/commands/specify.md` (added SILENT pre/post hooks)
- **Dependencies**: 2.1, 2.2
- **Estimated effort**: 1.5 hours
- **Implementation**:
  ```markdown
  1. **Pre-Check** (invisible to user):
     - Silently execute: `bash archon-sync-documents.sh "$FEATURE_DIR" pull`
     - Pulls latest spec.md from Archon if available
     - User never knows this happened

  [... existing spec generation workflow ...]

  6. **Background Integration** (invisible to user):
     - Silently execute: `bash archon-auto-init.sh "$FEATURE_DIR" &`
     - Creates project and pushes spec.md to Archon
     - Runs in background, zero output, never blocks
  ```

#### 3.2 Add Bidirectional Sync to `/speckit.plan` ✅

**Task**: Pull latest docs before planning, push after generation, enhance with RAG
- **Status**: ✅ COMPLETED
- **Description**: Modify plan command for full bidirectional sync + RAG
- **Files modified**:
  - `templates/commands/plan.md` (added SILENT pre/post hooks + RAG)
- **Files created**:
  - `scripts/bash/archon-silent-rag.sh` - Silent RAG enhancement
- **Dependencies**: 2.2
- **Estimated effort**: 2.5 hours
- **Implementation**:
  ```markdown
  1. **Pre-Check** (invisible to user):
     - Silently execute: `bash archon-sync-documents.sh "$FEATURE_DIR" pull`
     - Pulls latest spec.md, plan.md, research.md from Archon
     - Ensures working with latest versions

  Phase 0: Research
  - Research best practices for chosen tech stack
  - **[SILENT]** Attempt RAG enhancement via archon-silent-rag.sh
  - Continue with research regardless of RAG availability

  [... existing plan generation workflow ...]

  Final Step: **Background Sync** (invisible to user):
     - Silently execute: `bash archon-sync-documents.sh "$FEATURE_DIR" push &`
     - Pushes plan.md, research.md, data-model.md, quickstart.md to Archon
  ```
- **archon-silent-rag.sh workflow** (ALL silent):
  1. Check if Archon MCP available
  2. If not: exit 0 (do nothing)
  3. Extract tech keywords from user input
  4. Call `rag_search_knowledge_base(...)` 2>&1 >/dev/null
  5. Append findings to research.md (if any found)
  6. Exit 0 (never fail)

#### 3.3 Add Bidirectional Sync to `/speckit.tasks` ✅

**Task**: Pull latest docs before task generation, push after
- **Status**: ✅ COMPLETED
- **Description**: Modify tasks command to sync all relevant documents
- **Files modified**:
  - `templates/commands/tasks.md` (added SILENT pre/post hooks)
- **Dependencies**: 2.2, 2.3
- **Estimated effort**: 1.5 hours
- **Implementation**:
  ```markdown
  1. **Pre-Check** (invisible to user):
     - Silently execute: `bash archon-sync-documents.sh "$FEATURE_DIR" pull`
     - Pulls latest spec.md, plan.md, tasks.md from Archon
     - Ensures task generation based on latest versions

  [... existing task generation workflow ...]

  6. **Background Integration** (invisible to user):
     - Silently execute: `bash archon-auto-sync-tasks.sh "$FEATURE_DIR" &`
     - Pushes tasks.md to Archon and creates Archon tasks
     - Runs in background, zero output
  ```

#### 3.4 Add Bidirectional Sync to `/speckit.implement` ✅

**Task**: Pull ALL latest artifacts before implementation
- **Status**: ✅ COMPLETED
- **Description**: Ensure implementation uses absolute latest from Archon
- **Files modified**:
  - `templates/commands/implement.md` (added SILENT pre-check)
- **Dependencies**: 2.2, 2.4
- **Estimated effort**: 1 hour
- **Implementation**:
  ```markdown
  1. **Pre-Check** (invisible to user):
     - Silently execute: `bash archon-sync-documents.sh "$FEATURE_DIR" pull`
     - Pulls ALL documents (spec, plan, tasks, research, etc.)
     - Silently execute: `bash archon-auto-pull-status.sh "$FEATURE_DIR"`
     - Updates tasks.md checkboxes from Archon task statuses
     - User never knows, always working with latest versions

  [... existing implementation workflow ...]
  ```

#### 3.5 Add Bidirectional Sync to `/speckit.analyze` ✅

**Task**: Pull latest docs before analysis, push analysis results after
- **Status**: ✅ COMPLETED
- **Description**: Modify analyze command to sync documents bidirectionally
- **Files modified**:
  - `templates/commands/analyze.md` (added SILENT pre/post hooks)
- **Dependencies**: 2.2
- **Estimated effort**: 1 hour
- **Implementation**:
  ```markdown
  1. **Pre-Check** (invisible to user):
     - Silently execute: `bash archon-sync-documents.sh "$FEATURE_DIR" pull`
     - Pulls latest spec.md, plan.md, tasks.md for analysis
     - Ensures analysis based on latest versions

  [... existing analysis workflow ...]

  Final Step: **Background Sync** (invisible to user):
     - Silently execute: `bash archon-sync-documents.sh "$FEATURE_DIR" push &`
     - Pushes analysis results/reports to Archon if generated
  ```

#### 3.6 Add Bidirectional Sync to `/speckit.clarify` ✅

**Task**: Pull latest spec before clarification, push updated spec after
- **Status**: ✅ COMPLETED
- **Description**: Modify clarify command to sync documents bidirectionally
- **Files modified**:
  - `templates/commands/clarify.md` (added SILENT pre/post hooks)
- **Dependencies**: 2.2
- **Estimated effort**: 1 hour
- **Implementation**:
  ```markdown
  1. **Pre-Check** (invisible to user):
     - Silently execute: `bash archon-sync-documents.sh "$FEATURE_DIR" pull`
     - Pulls latest spec.md from Archon
     - Ensures clarification works on latest spec version

  [... existing clarification workflow ...]

  Final Step: **Background Sync** (invisible to user):
     - Silently execute: `bash archon-sync-documents.sh "$FEATURE_DIR" push &`
     - Pushes updated spec.md with clarifications to Archon
  ```

### Phase 4: Silent Bidirectional Sync (Advanced)

#### 4.1 Add Silent Status Pull to `/speckit.implement`

**Task**: Silently pull Archon status before implementation starts
- **Description**: Update tasks.md with latest Archon status (completely transparent)
- **Files to modify**:
  - `templates/commands/implement.md` (add silent pre-check)
- **Dependencies**: 2.3
- **Estimated effort**: 1.5 hours
- **Modification** (add to beginning of implement.md workflow):
  ```markdown
  1. **Background Sync** (invisible to user):
     - Silently execute: `bash archon-auto-pull-status.sh "$FEATURE_DIR"`
     - Updates tasks.md checkboxes from Archon (if MCP available)
     - Zero output, never blocks, user never knows
  ```

#### 4.2 Add Silent Conflict Resolution

**Task**: Automatically resolve sync conflicts (Archon wins strategy)
- **Description**: When both sources modified, Archon is source of truth (silent)
- **Files to modify**:
  - `scripts/bash/archon-auto-pull-status.sh` (add conflict resolution)
- **Dependencies**: 2.3
- **Estimated effort**: 2 hours
- **Strategy** (ALL silent):
  - Always trust Archon status over local checkboxes
  - Overwrite tasks.md checkboxes without prompting
  - No conflict detection UI, no user interaction
  - Advanced users can manually edit if needed

#### 4.3 Add Periodic Background Sync (Optional)

**Task**: Optionally enable background polling for status updates
- **Description**: Daemon that silently syncs every N minutes (opt-in for advanced users)
- **Files to create**:
  - `scripts/bash/archon-daemon.sh` - Background sync daemon (advanced users only)
- **Dependencies**: 4.1, 4.2
- **Estimated effort**: 3 hours
- **Features**:
  - Runs ONLY if explicitly started by advanced user
  - Polls Archon every 5 minutes
  - Updates tasks.md silently
  - NOT started automatically, NOT documented for regular users
  - Only mentioned in `docs/archon-integration-internals.md`

### Phase 5: Testing & Documentation (Quality Assurance)

**NOTE**: Phase 5 is now ONLY about testing and fork documentation. NO user-facing commands.

#### 5.1 Create Silent Integration Test Suite

**Task**: Test suite for silent Archon integration
- **Description**: Automated tests that verify silent operation
- **Files to create**:
  - `tests/archon/test_silent_integration.sh` - Main integration tests
  - `tests/archon/test_mcp_detection.sh` - MCP availability tests
  - `tests/archon/test_state_management.sh` - Hidden state file tests
  - `tests/archon/run_all_silent_tests.sh` - Test runner
- **Dependencies**: All Phase 1-4 tasks
- **Estimated effort**: 3 hours
- **Coverage**:
  - MCP detection returns correct boolean (no output)
  - Project creation is completely silent
  - Task sync produces zero stdout/stderr
  - Status pull doesn't block or error
  - Graceful degradation when MCP unavailable

#### 5.2 Update Fork Documentation (Developer-Only)

**Task**: Document silent integration in fork files ONLY
- **Description**: Add Archon documentation to fork-specific files
- **Files to modify**:
  - `FORK_CUSTOMIZATIONS.md` - List silent integration files
  - `CLAUDE.md` - Update workflow with silent integration notes
- **Files to create**:
  - `docs/archon-integration-internals.md` - Developer documentation
- **Dependencies**: All implementation tasks
- **Estimated effort**: 2 hours
- **Content**:
  - In `FORK_CUSTOMIZATIONS.md`:
    - List all archon-*.sh scripts (merge strategy: keep ours)
    - Note that integration is completely silent
    - Explain MCP-gated operation
  - In `docs/archon-integration-internals.md`:
    - Architecture diagram
    - State file locations and format
    - MCP tool usage patterns
    - How to enable Archon MCP server
    - Debugging tips (for developers only)
  - **NO** mention in README.md or user-facing docs

#### 5.3 Create .gitignore Entry for State Files

**Task**: Ensure Archon state files aren't committed to git
- **Description**: Add .archon-state/ to .gitignore
- **Files to modify**:
  - `.gitignore` or `templates/.gitignore-template`
- **Dependencies**: 1.1
- **Estimated effort**: 0.5 hours
- **Content**:
  ```gitignore
  # Archon MCP integration state (generated, don't commit)
  .specify/scripts/bash/.archon-state/
  ```

---

## Codebase Integration Points

### Files to Modify (Minimal, Silent Changes)

| File | Change Type | Purpose | User Visibility |
|------|-------------|---------|-----------------|
| `scripts/bash/common.sh` | Add silent source | Source archon-common.sh if exists | **ZERO** - completely invisible |
| `templates/commands/specify.md` | Add background call | Silently call archon-auto-init.sh & | **ZERO** - runs in background |
| `templates/commands/plan.md` | Add silent RAG step | Silently enhance research if MCP available | **ZERO** - transparent enhancement |
| `templates/commands/tasks.md` | Add background call | Silently call archon-auto-sync-tasks.sh & | **ZERO** - runs in background |
| `templates/commands/implement.md` | Add silent pre-step | Silently pull status before execution | **ZERO** - transparent sync |
| `.gitignore` or `templates/.gitignore-template` | Add state directory | Exclude .archon-state/ | **ZERO** - internal state only |
| `FORK_CUSTOMIZATIONS.md` | Document extension | List Archon integration files | **Developer-only** |
| `CLAUDE.md` | Add integration notes | Explain silent workflow | **Developer-only** |

### New Files to Create (All Internal/Hidden)

**Bash Scripts** (scripts/bash/) - ALL completely silent:
- `archon-common.sh` - Silent MCP detection and utilities
- `archon-auto-init.sh` - Silent project creation (called in background)
- `archon-auto-sync-tasks.sh` - Silent task synchronization (called in background)
- `archon-auto-pull-status.sh` - Silent status update (called before implement)
- `archon-silent-rag.sh` - Silent RAG enhancement (called during plan)
- `archon-daemon.sh` - Optional background sync daemon (advanced users only)

**PowerShell Scripts** (scripts/powershell/):
- Mirror all bash scripts with `.ps1` extension
- Maintain same silent operation

**Hidden State** (scripts/bash/.archon-state/):
- `{feature-name}.pid` - Project ID mapping files
- `{feature-name}.tasks` - Task ID mapping files
- **Never committed to git**, **never visible to users**

**Fork-Only Documentation**:
- `docs/archon-integration-internals.md` - Developer/advanced user documentation
- **NO user-facing docs**, **NO README mention**, **NO quickstart guides**

**Tests** (tests/archon/):
- `test_silent_integration.sh` - Verify zero output
- `test_mcp_detection.sh` - Test MCP availability check
- `test_state_management.sh` - Test hidden state files
- `run_all_silent_tests.sh` - Test runner

**REMOVED from Plan** (user-facing commands that would expose Archon):
- ~~`/speckit.archon.init`~~ - Removed, automatic background operation
- ~~`/speckit.archon.sync-tasks`~~ - Removed, automatic background operation
- ~~`/speckit.archon.status`~~ - Removed, users don't need to know
- ~~`/speckit.archon.pull-status`~~ - Removed, automatic silent operation
- ~~`/speckit.archon.search`~~ - Removed, happens automatically in /speckit.plan
- ~~`/speckit.archon.task`~~ - Removed, users use normal workflow
- ~~`/speckit.archon.report`~~ - Removed, not needed for silent operation

### Existing Patterns to Follow

1. **Script Structure**:
   ```bash
   #!/usr/bin/env bash
   set -e
   set -u
   set -o pipefail

   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   source "$SCRIPT_DIR/common.sh"
   source "$SCRIPT_DIR/archon-common.sh"  # New

   JSON_MODE=false
   for arg in "$@"; do
     case "$arg" in
       --json) JSON_MODE=true ;;
       *) ARGS+=("$arg") ;;
     esac
   done

   # Main logic...

   if $JSON_MODE; then
     printf '{"KEY":"%s"}\n' "$value"
   else
     echo "KEY: $value"
   fi
   ```

2. **Command Template Structure**:
   ```yaml
   ---
   description: Brief command description
   scripts:
     sh: scripts/bash/archon-command.sh --json "{ARGS}"
     ps: scripts/powershell/archon-command.ps1 -Json "{ARGS}"
   ---

   ## User Input
   ```text
   $ARGUMENTS
   ```

   ## Outline
   1. Setup step
   2. Execution step
   3. Report step
   ```

3. **JSON Output Pattern**:
   ```json
   {
     "ARCHON_PROJECT_ID": "proj-abc123",
     "FEATURE_DIR": "/absolute/path/to/specs/001-feature",
     "TASKS_SYNCED": 24,
     "STATUS": "success"
   }
   ```

4. **Error Handling**:
   ```bash
   if ! command_that_might_fail; then
     if $JSON_MODE; then
       printf '{"ERROR":"%s"}\n' "Error description"
     else
       echo "Error: Error description" >&2
     fi
     exit 1
   fi
   ```

---

## Technical Design

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Spec Kit Core                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ /speckit.    │  │ /speckit.    │  │ /speckit.    │         │
│  │  specify     │  │  plan        │  │  tasks       │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────────────────────────────────────────┐           │
│  │           Spec Kit Script Layer                 │           │
│  │  (scripts/bash/create-new-feature.sh, etc.)    │           │
│  └─────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ Optional Hooks
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Archon Extension Layer                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Extension Commands                         │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │    │
│  │  │ /speckit.   │  │ /speckit.   │  │ /speckit.   │   │    │
│  │  │  archon.    │  │  archon.    │  │  archon.    │   │    │
│  │  │  init       │  │  sync-tasks │  │  status     │   │    │
│  │  └─────┬───────┘  └─────┬───────┘  └─────┬───────┘   │    │
│  └────────┼────────────────┼────────────────┼───────────┘    │
│           │                │                │                 │
│           ▼                ▼                ▼                 │
│  ┌─────────────────────────────────────────────────┐         │
│  │       Archon Extension Scripts                  │         │
│  │  (scripts/bash/archon-*.sh)                    │         │
│  └────────────────────┬────────────────────────────┘         │
│                       │                                       │
└───────────────────────┼───────────────────────────────────────┘
                        │
                        │ MCP Tool Calls
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Archon MCP Server                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Project    │  │     Task     │  │   Knowledge  │         │
│  │  Management  │  │  Management  │  │     Base     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  Persistent Storage: PostgreSQL + pgvector                     │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

**Workflow 1: Feature Specification with Auto-Init**
```
1. User: /speckit.specify "Build photo albums feature"
2. Spec Kit: Generate spec.md in specs/001-photo-albums/
3. Extension Hook: archon-post-specify.sh detects .archon-config.json
4. Extension: Call manage_project("create", title="Feature: Photo Albums")
5. Extension: Store project_id in .archon-config.json
6. Extension: Update CLAUDE.md with project reference
7. Report: "Archon project created: proj-abc123"
```

**Workflow 2: Task Generation with Auto-Sync**
```
1. User: /speckit.tasks
2. Spec Kit: Generate tasks.md with 24 tasks
3. Extension Hook: archon-post-tasks.sh detects .archon-config.json
4. Extension: Parse tasks.md (format: - [ ] [T001] [P?] [US1?] Description)
5. Extension: For each task, call manage_task("create", ...)
6. Extension: Map phases to priorities (Phase 1=100, Phase 2=90, etc.)
7. Report: "24 tasks synced to Archon (proj-abc123)"
```

**Workflow 3: Implementation with Status Sync**
```
1. User: /speckit.implement
2. Agent: Load tasks from Archon via find_tasks(filter_by="project")
3. Agent: For each task:
   a. manage_task("update", task_id="...", status="doing")
   b. Implement code
   c. manage_task("update", task_id="...", status="review")
4. Extension: archon-pull-status.sh syncs back to tasks.md
5. Extension: Update checkboxes: done → [X], others → [ ]
6. Report: "tasks.md updated with latest Archon status"
```

**Workflow 4: Research with RAG Integration**
```
1. User: /speckit.plan "Use React + Vite for frontend"
2. Spec Kit: Start research phase
3. Extension: Extract keywords: "React", "Vite"
4. Extension: Call rag_search_knowledge_base(query="React Vite", match_count=5)
5. Extension: Call rag_search_code_examples(query="Vite setup", match_count=3)
6. Extension: Append findings to research.md
7. Spec Kit: Continue with Phase 1 (design)
```

### State File Format (Hidden from Users)

**NO configuration files** - Everything is automatic and MCP-gated.

**Hidden State Files** (in `.specify/scripts/bash/.archon-state/`):

**Project ID Mapping** (`{feature-name}.pid`):
```
proj-abc123def456
```
- Single line containing the Archon project ID
- Created automatically when project is created
- Never shown to user

**Document ID Mapping** (`{feature-name}.docs`):
```
spec.md:doc-uuid-abc123
plan.md:doc-uuid-def456
research.md:doc-uuid-ghi789
data-model.md:doc-uuid-jkl012
tasks.md:doc-uuid-mno345
quickstart.md:doc-uuid-pqr678
```
- One line per document: `{filename}:{Archon_Document_UUID}`
- Created automatically during document sync
- Used for update operations (vs create)
- Never shown to user

**Task ID Mapping** (`{feature-name}.tasks`):
```
T001:task-uuid-abc123
T002:task-uuid-def456
T003:task-uuid-ghi789
```
- One line per task: `{TaskID}:{Archon_Task_UUID}`
- Created automatically during task sync
- Never shown to user

**Sync Metadata** (`{feature-name}.meta`):
```
spec.md:2025-10-15T16:45:22Z
plan.md:2025-10-15T16:50:10Z
tasks.md:2025-10-15T17:02:33Z
last_task_pull:2025-10-15T17:05:00Z
```
- Tracks last sync time per document
- Used for conflict detection (Archon always wins if newer)
- Never shown to user

### API Endpoints (Archon MCP Tools Used)

| MCP Tool | Purpose | Usage in Extension |
|----------|---------|-------------------|
| `mcp__archon__health_check()` | Check Archon availability | archon-common.sh detection |
| `mcp__archon__find_projects()` | Search/get projects | archon-status.sh display |
| `mcp__archon__manage_project()` | Create/update/delete projects | archon-init.sh project creation |
| `mcp__archon__find_tasks()` | Search/filter tasks | archon-status.sh, archon-task.sh |
| `mcp__archon__manage_task()` | Create/update/delete tasks | archon-sync-tasks.sh bulk operations |
| `mcp__archon__rag_get_available_sources()` | List knowledge sources | archon-search.sh, archon-rag-research.sh |
| `mcp__archon__rag_search_knowledge_base()` | Search documentation | archon-rag-research.sh during /speckit.plan |
| `mcp__archon__rag_search_code_examples()` | Find code examples | archon-rag-research.sh during /speckit.plan |

---

## Dependencies and Libraries

**Core Dependencies** (already in Spec Kit):
- Python 3.11+ with Typer, Rich, httpx
- Bash 4.0+ (for associative arrays)
- PowerShell 5.1+ (Windows compatibility)
- Git (optional)

**New Dependencies** (Archon extension):
- `jq` - JSON parsing in bash scripts (optional, fallback to Python)
- `fswatch` or `inotifywait` - File watching for live sync (optional)

**MCP Server Requirements**:
- Archon MCP server running and accessible
- MCP tools registered in Claude Code / agent environment
- Network connectivity to Archon server

---

## Testing Strategy

### Unit Tests

**File**: `tests/archon/test_archon_init.sh`
```bash
#!/usr/bin/env bash
source "scripts/bash/archon-common.sh"

# Test 1: Detect Archon availability
test_archon_detection() {
  result=$(check_archon_available)
  assert_equals "true" "$result"
}

# Test 2: Create project
test_project_creation() {
  project_id=$(create_archon_project "Test Feature" "Test Description")
  assert_not_empty "$project_id"
  assert_starts_with "proj-" "$project_id"
}

# Test 3: Configuration handling
test_config_read_write() {
  write_archon_config "001-test" "$project_id"
  retrieved=$(read_archon_config "001-test")
  assert_equals "$project_id" "$retrieved"
}

run_all_tests
```

### Integration Tests

**File**: `tests/archon/test_integration.sh`
```bash
#!/usr/bin/env bash

# End-to-end test: Specify → Init → Tasks → Sync
test_full_workflow() {
  # Setup
  cd test_project

  # 1. Create spec
  bash .specify/scripts/bash/create-new-feature.sh --short-name "test-feature"

  # 2. Initialize Archon
  bash .specify/scripts/bash/archon-init.sh --json "001-test-feature"

  # 3. Generate tasks.md
  # (manually create for test)

  # 4. Sync tasks
  result=$(bash .specify/scripts/bash/archon-sync-tasks.sh --json)
  tasks_count=$(echo "$result" | jq -r '.TASKS_SYNCED')

  # Assertions
  assert_greater_than "$tasks_count" 0

  # Cleanup
  cd ..
}

run_integration_tests
```

### Edge Cases to Cover

1. **Archon Unavailable**:
   - Extension commands gracefully degrade
   - Non-blocking failures with clear messaging
   - Fallback to manual workflow

2. **Sync Conflicts**:
   - Tasks modified in both Archon and tasks.md
   - Conflict resolution strategy applied correctly
   - Manual resolution option available

3. **Malformed tasks.md**:
   - Invalid task format detected
   - Parsing errors reported clearly
   - Partial sync with warnings

4. **Network Failures**:
   - Retry logic for transient failures
   - Timeout handling
   - Offline mode support

5. **Multiple Features**:
   - Correct feature directory detection
   - Proper project_id mapping
   - No cross-contamination

---

## Success Criteria

### Functional Requirements
- [ ] Silent MCP detection (zero output, returns boolean only)
- [ ] Automated Archon project creation after `/speckit.specify` (completely silent)
- [ ] Automated task synchronization after `/speckit.tasks` (completely silent)
- [ ] Silent RAG enhancement during `/speckit.plan` research phase
- [ ] Silent bidirectional status sync (Archon ↔ tasks.md)
- [ ] Silent conflict resolution (Archon wins, no prompts)
- [ ] **ZERO user-facing changes** - users never see "Archon" mentioned
- [ ] Graceful silent degradation when Archon unavailable (no errors, no warnings)

### Non-Functional Requirements
- [ ] **NO configuration required** - works automatically when MCP available
- [ ] **NO user-facing commands** - completely transparent operation
- [ ] No breaking changes to existing Spec Kit commands
- [ ] Upstream sync process remains functional
- [ ] Fork customization documented in `FORK_CUSTOMIZATIONS.md` ONLY
- [ ] All scripts have corresponding PowerShell variants
- [ ] Extension works across all supported agents (Claude, Copilot, Gemini, etc.)
- [ ] **Documentation ONLY in developer/fork files** (not user-facing)

### Quality Gates
- [ ] All integration tests passing (verify zero output)
- [ ] Manual testing confirms users never see Archon
- [ ] MCP unavailable scenario produces zero errors/warnings
- [ ] Background processes don't block workflow
- [ ] Performance acceptable (sync < 2 seconds, non-blocking)
- [ ] State files properly excluded from git

---

## Notes and Considerations

### Potential Challenges

1. **Task ID Mapping**:
   - **Challenge**: Tasks in tasks.md have IDs like T001, but Archon generates UUIDs
   - **Solution**: Maintain mapping in `.archon-config.json`: `{"T001": "task-uuid-abc123"}`
   - **Consideration**: Mapping must persist across sessions

2. **Bi-directional Sync Complexity**:
   - **Challenge**: Determining source of truth when both modified
   - **Solution**: Timestamp-based resolution with manual override option
   - **Consideration**: Clear conflict messaging to user

3. **Performance with Large Projects**:
   - **Challenge**: 100+ tasks may slow sync operations
   - **Solution**: Batch MCP calls, implement incremental sync
   - **Consideration**: Cache Archon state locally for comparison

4. **Multi-Agent Compatibility**:
   - **Challenge**: Different agents have different capabilities
   - **Solution**: Detect agent type, adjust MCP call formatting
   - **Consideration**: Test thoroughly with Copilot, Gemini, Claude

5. **Upstream Sync Conflicts**:
   - **Challenge**: Parent `github/spec-kit` may add conflicting features
   - **Solution**: Keep extension in separate namespace (`archon-*.sh`, `archon-*.md`)
   - **Consideration**: Document merge strategy in `FORK_CUSTOMIZATIONS.md`

### Future Enhancements (Out of Scope)

- **Archon Document Management**: Sync spec.md, plan.md to Archon documents
- **Archon Version Control**: Track document versions in Archon
- **Multi-Project Dashboard**: Aggregate view across all Spec Kit projects
- **Webhooks**: Real-time push notifications from Archon
- **AI-Assisted Conflict Resolution**: Use LLM to suggest merge strategies
- **Archon Templates**: Store reusable spec/plan templates in Archon

### Migration Path

**For Existing Spec Kit Users**:
1. Extension is opt-in (disabled by default)
2. Enable via `.archon-config.json` creation
3. Run `/speckit.archon.init` on existing features to retrofit
4. Run `/speckit.archon.sync-tasks` to import existing tasks
5. Continue normal workflow with automatic synchronization

**Rollback Strategy**:
1. Delete `.archon-config.json` to disable extension
2. Remove `archon-*` scripts and commands if desired
3. Core Spec Kit functionality unaffected
4. Archon data remains in MCP server for future use

---

## Implementation References

### Key Files to Reference During Development

**Command Template Examples**:
- `templates/commands/tasks.md` - Complex multi-doc parsing, JSON output
- `templates/commands/specify.md` - User input handling, template substitution
- `.claude/commands/execute-plan.md` - Archon integration patterns

**Script Examples**:
- `scripts/bash/common.sh` - Utility functions, error handling
- `scripts/bash/check-prerequisites.sh` - JSON output, validation
- `scripts/bash/create-new-feature.sh` - Feature directory creation
- `scripts/bash/update-agent-context.sh` - File parsing, multi-agent updates

**Documentation Examples**:
- `FORK_CUSTOMIZATIONS.md` - Fork management documentation
- `docs/installation.md` - User-facing installation guide
- `README.md` - High-level overview and quick start

### Similar Patterns in Spec Kit

**Pattern: Optional Post-Execution Hooks**
```yaml
# In command template
5. **Post-execution (optional)**: If `.archon-config.json` exists:
   - Run `archon-post-specify.sh` with feature details
   - Report Archon integration status
   - Non-blocking if fails
```

**Pattern: JSON Output for Parsing**
```bash
if $JSON_MODE; then
  printf '{"FEATURE_DIR":"%s","PROJECT_ID":"%s"}\n' \
    "$feature_dir" "$project_id"
else
  echo "Feature Directory: $feature_dir"
  echo "Archon Project: $project_id"
fi
```

**Pattern: Graceful Degradation**
```bash
if check_archon_available; then
  sync_to_archon
else
  warn "Archon unavailable - skipping sync"
  warn "Run '/speckit.archon.sync-tasks' manually later"
fi
```

---

## Appendix: Silent Integration Overview

### User-Visible Commands (UNCHANGED)

**Regular users see ZERO changes**:

| Command | Behavior | Archon Integration |
|---------|----------|-------------------|
| `/speckit.specify` | Creates spec.md as normal | **Silent**: Pull-before/push-after + background project creation if MCP available ✅ |
| `/speckit.plan` | Creates plan.md as normal | **Silent**: Pull-before/push-after + RAG enhancement during research if MCP available ✅ |
| `/speckit.tasks` | Creates tasks.md as normal | **Silent**: Pull-before/push-after + background task sync if MCP available ✅ |
| `/speckit.implement` | Implements tasks as normal | **Silent**: Pull-before + status pull before execution if MCP available ✅ |
| `/speckit.analyze` | Analyzes artifacts as normal | **Silent**: Pull-before/push-after for analysis artifacts if MCP available ✅ |
| `/speckit.clarify` | Clarifies spec as normal | **Silent**: Pull-before/push-after for updated spec if MCP available ✅ |

### Background Scripts (Hidden)

**Advanced users (via fork docs only) can discover these**:

| Script | Trigger | MCP Check | Output |
|--------|---------|-----------|--------|
| `archon-auto-init.sh` | After `/speckit.specify` | First line | **ZERO** (all 2>&1 >/dev/null) |
| `archon-silent-rag.sh` | During `/speckit.plan` research | First line | **ZERO** (appends to research.md only) |
| `archon-auto-sync-tasks.sh` | After `/speckit.tasks` | First line | **ZERO** (all 2>&1 >/dev/null) |
| `archon-auto-pull-status.sh` | Before `/speckit.implement` | First line | **ZERO** (updates tasks.md only) |
| `archon-daemon.sh` | Manual start only (advanced) | Continuous | **ZERO** (daemon process) |

### For Advanced Users Only

**Enabling Archon integration**:
1. Install and configure Archon MCP server
2. Ensure MCP tools are available to your AI agent
3. **That's it** - integration activates automatically

**Disabling Archon integration**:
1. Stop/disable Archon MCP server
2. **That's it** - integration becomes dormant (zero errors)

**Debugging (for developers)**:
- Check `.specify/scripts/bash/.archon-state/` for state files
- Run scripts manually with bash debug: `bash -x archon-auto-init.sh feature-dir`
- Read `docs/archon-integration-internals.md` for architecture

---

**This plan is ready for execution with `/execute-plan PRPs/archon-speckit-extension.md`**

## Plan Summary

**Total Effort**: ~23 hours (reduced from 49 hours by removing all user-facing commands)

**Phase Breakdown**:
- Phase 1: Foundation (4 hours) - Silent utilities, detection, fork docs
- Phase 2: Core Integration (7.5 hours) - Auto-init, auto-sync, auto-pull
- **Phase 3: Silent Hooks (6 hours) - ✅ COMPLETED - Inject into all SIX commands**
- Phase 4: Bidirectional Sync (6.5 hours) - Status pull, conflicts, optional daemon
- Phase 5: Testing & Docs (5.5 hours) - Tests, fork documentation, .gitignore

**Files Modified**: 8 (minimal silent changes)
  - Core commands: `specify.md`, `plan.md`, `tasks.md`, `implement.md` ✅
  - Enhancement commands: `analyze.md`, `clarify.md` ✅
  - Scripts: `common.sh`, `.gitignore`

**Files Created**: ~12 scripts + 1 doc file + tests
**User-Facing Commands Added**: **ZERO**
**User-Visible Changes**: **ZERO**

**Phase 3 Achievement**: All six commands (specify, plan, tasks, implement, analyze, clarify) now have complete pull-before/push-after hooks implemented for seamless bidirectional synchronization.

**Key Achievement**: Complete Archon integration that is 100% invisible to regular users while providing powerful persistent tracking for advanced users who enable the MCP server.
