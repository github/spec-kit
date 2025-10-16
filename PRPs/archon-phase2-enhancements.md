# Implementation Plan: Archon-Spec Kit Phase 2 Future Enhancements

## Overview

This plan outlines the next phase of enhancements to the Archon-Spec Kit silent integration, building upon the successfully completed Phase 1 implementation. Phase 2 focuses on **cross-platform compatibility**, **extended integration hooks**, **real-time synchronization**, **multi-project management**, and **intelligent automation**.

**Building on Phase 1 Success**: All Phase 1 objectives completed:
- ✅ Silent bidirectional document sync (spec.md, plan.md, research.md, tasks.md, etc.)
- ✅ Six slash commands with pull-before/push-after hooks
- ✅ Automatic project and task creation
- ✅ RAG enhancement during planning
- ✅ Status synchronization
- ✅ Zero user-facing changes (completely invisible)
- ✅ MCP-gated operation with graceful degradation

**Phase 2 Goals**: Enhance and expand the silent integration capabilities while maintaining complete transparency to regular users.

## Requirements Summary

### Core Requirements

1. **PowerShell Variants**: Cross-platform compatibility for Windows users
   - Mirror all 6 archon-*.sh bash scripts with .ps1 PowerShell equivalents
   - Maintain identical silent operation characteristics
   - Follow established PowerShell conventions from existing scripts

2. **Extended Integration Hooks**: Add silent hooks to remaining slash commands
   - `/speckit.constitution` - Track constitutional principles in Archon
   - `/speckit.checklist` - Sync quality checklists to Archon documents
   - Any future slash commands added by upstream

3. **Webhook Support**: Real-time push notifications from Archon
   - Optional webhook listener for task status changes
   - Silent background updates when tasks modified externally
   - Opt-in feature for advanced users only

4. **Multi-Project Dashboard**: Aggregate view across Spec Kit projects
   - Query all Spec Kit projects from Archon
   - Generate cross-project status reports
   - Track dependencies between related features
   - Advanced user feature, not visible to regular users

5. **AI-Assisted Conflict Resolution**: Intelligent merge strategies
   - Use LLM to analyze conflicting changes
   - Suggest merge strategies for document conflicts
   - Preserve intent from both sources
   - Always provide manual override option

### Technical Constraints

- Maintain zero user-facing changes principle
- All new features must be MCP-gated
- Silent operation (no stdout/stderr for regular users)
- No new configuration files (environment-based only)
- Cross-platform compatibility (Linux, macOS, Windows)
- Backward compatible with Phase 1 implementation
- Fork-only documentation (never in upstream README)

### Success Criteria

- [ ] All 6 archon-*.sh scripts have PowerShell equivalents
- [ ] PowerShell scripts pass identical test suite as bash versions
- [ ] Constitution and checklist commands have silent integration hooks
- [ ] Webhook listener runs as optional background service
- [ ] Dashboard command generates multi-project reports
- [ ] AI conflict resolution suggests merge strategies for 90%+ conflicts
- [ ] Zero additional user-facing changes
- [ ] Performance remains under 2 seconds for all operations
- [ ] Complete documentation in `docs/archon-integration-internals.md`

---

## Research Findings

### Best Practices from Codebase Analysis

**PowerShell Script Conventions** (from `scripts/powershell/*.ps1`):
- Shebang: `#!/usr/bin/env pwsh` for cross-platform compatibility
- Parameter handling: `[CmdletBinding()]` with typed parameters
- JSON output: `ConvertTo-Json -Compress` for single-line output
- Error handling: `$ErrorActionPreference = 'Stop'` with try-catch blocks
- Silent operations: `2>$null | Out-Null` or `-ErrorAction SilentlyContinue`
- File paths: `Join-Path` and `Split-Path` instead of string concatenation
- Functions: Verb-noun naming (e.g., `Test-ArchonAvailable`, `Save-ProjectMapping`)
- Git detection: Check `$LASTEXITCODE -eq 0`, fallback to marker-based search

**State Management Patterns** (from Phase 1):
- Hidden state directory: `.specify/scripts/bash/.archon-state/`
- Project mapping: `{feature}.pid` (single-line project UUID)
- Document mapping: `{feature}.docs` (filename:doc-uuid pairs)
- Task mapping: `{feature}.tasks` (TaskID:task-uuid pairs)
- Sync metadata: `{feature}.meta` (timestamp tracking)

**Slash Command Integration** (from Phase 1 implementation):
- Pre-check hook: `bash archon-sync-documents.sh "$FEATURE_DIR" pull 2>/dev/null || true`
- Post-generation hook: `bash archon-sync-documents.sh "$FEATURE_DIR" push & 2>/dev/null || true`
- Background execution: Use `&` for non-blocking operations
- Graceful degradation: `|| true` ensures never fails

### Reference Implementations

**PowerShell Equivalents in Codebase**:
1. **common.ps1** (scripts/powershell/common.ps1:1-300)
   - Repository navigation functions
   - Feature path resolution
   - Git detection with fallback
   - **Pattern to replicate** for archon-common.ps1

2. **check-prerequisites.ps1** (scripts/powershell/check-prerequisites.ps1:1-150)
   - JSON output with `-Compress`
   - Validation logic with clear error messages
   - Dual output mode (text vs JSON)
   - **Pattern to replicate** for PowerShell archon scripts

3. **create-new-feature.ps1** (scripts/powershell/create-new-feature.ps1:1-200)
   - Parameter validation
   - Directory creation
   - Git operations with error handling
   - **Pattern to replicate** for archon-auto-init.ps1

**Webhook Patterns** (industry best practices):
- Express.js or FastAPI for webhook receivers
- HMAC signature verification for security
- Event queue for asynchronous processing
- Retry logic with exponential backoff
- **Adaptation**: Lightweight PowerShell/bash HTTP listener

**Dashboard Patterns** (from similar tools):
- Query aggregation across multiple projects
- Status rollup (total tasks, completed %, blockers)
- Dependency graph visualization
- **Adaptation**: Simple text-based dashboard for CLI

### Technology Decisions

| Decision | Technology | Rationale |
|----------|-----------|-----------|
| PowerShell Version | PowerShell 7+ (pwsh) | Cross-platform compatibility (Linux, macOS, Windows) |
| Webhook Listener | Python FastAPI or bash nc | Lightweight, minimal dependencies, optional feature |
| Dashboard Format | Markdown tables + ASCII graphs | CLI-friendly, no additional dependencies |
| AI Conflict Resolution | Claude API via MCP | Reuses existing Archon MCP connection |
| State Storage | Continue using flat files | Simple, no DB dependency, version-controllable |

---

## Implementation Tasks

### Phase 2.1: PowerShell Cross-Platform Support

#### 2.1.1 Create archon-common.ps1

**Task**: PowerShell equivalent of archon-common.sh
- **Description**: Core utilities for Archon integration (completely silent)
- **Files to create**:
  - `scripts/powershell/archon-common.ps1`
- **Dependencies**: None
- **Estimated effort**: 3 hours
- **Details**:
  ```powershell
  #!/usr/bin/env pwsh
  # Archon MCP Integration - Silent Utilities (PowerShell)

  function Test-ArchonAvailable {
      # Silent MCP detection - returns $true/$false, no output
      if (Get-Command claude -ErrorAction SilentlyContinue) {
          return $true
      }
      return $false
  }

  function Get-ArchonStateDir {
      $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
      Join-Path $scriptDir '.archon-state'
  }

  function Save-ProjectMapping {
      param([string]$FeatureName, [string]$ProjectId)
      $stateDir = Get-ArchonStateDir
      New-Item -ItemType Directory -Path $stateDir -Force -EA SilentlyContinue | Out-Null
      $pidFile = Join-Path $stateDir "${FeatureName}.pid"
      Set-Content -Path $pidFile -Value $ProjectId -NoNewline -EA SilentlyContinue
  }

  # Additional helper functions...
  ```

#### 2.1.2 Create archon-auto-init.ps1

**Task**: PowerShell equivalent of archon-auto-init.sh
- **Description**: Silent project and document auto-creation
- **Files to create**:
  - `scripts/powershell/archon-auto-init.ps1`
- **Dependencies**: 2.1.1
- **Estimated effort**: 3.5 hours
- **Workflow** (ALL silent):
  1. Check Archon MCP available (exit 0 if not)
  2. Load spec.md to extract feature name and description
  3. Create Archon project via manage_project (suppress all output)
  4. Store project_id in .archon-state/{feature}.pid
  5. Create document for spec.md
  6. Store document_id mapping
  7. Exit 0 (never fail, never output)

#### 2.1.3 Create archon-sync-documents.ps1

**Task**: PowerShell equivalent of archon-sync-documents.sh
- **Description**: Bidirectional document sync (pull-before/push-after)
- **Files to create**:
  - `scripts/powershell/archon-sync-documents.ps1`
- **Dependencies**: 2.1.1
- **Estimated effort**: 4.5 hours
- **Workflow** (ALL silent):
  1. Check Archon MCP available
  2. Load project_id and document mappings
  3. PULL phase: Query Archon, overwrite local if newer
  4. PUSH phase: Update/create Archon documents
  5. Update state files
  6. Exit 0

#### 2.1.4 Create archon-auto-sync-tasks.ps1

**Task**: PowerShell equivalent of archon-auto-sync-tasks.sh
- **Description**: Silent task synchronization
- **Files to create**:
  - `scripts/powershell/archon-auto-sync-tasks.ps1`
- **Dependencies**: 2.1.1
- **Estimated effort**: 3.5 hours
- **Workflow** (ALL silent):
  1. Parse tasks.md (regex matching)
  2. For each task: manage_task("create", ...)
  3. Store task mappings
  4. Exit 0

#### 2.1.5 Create archon-auto-pull-status.ps1

**Task**: PowerShell equivalent of archon-auto-pull-status.sh
- **Description**: Silent status sync from Archon to tasks.md
- **Files to create**:
  - `scripts/powershell/archon-auto-pull-status.ps1`
- **Dependencies**: 2.1.1
- **Estimated effort**: 2.5 hours
- **Workflow** (ALL silent):
  1. Query Archon for task statuses
  2. Update tasks.md checkboxes (done → [X])
  3. Exit 0

#### 2.1.6 Create archon-daemon.ps1

**Task**: PowerShell equivalent of archon-daemon.sh
- **Description**: Optional background sync daemon
- **Files to create**:
  - `scripts/powershell/archon-daemon.ps1`
- **Dependencies**: 2.1.1, 2.1.5
- **Estimated effort**: 3 hours
- **Features**:
  - Polls every 5 minutes
  - Updates tasks.md silently
  - Started manually by advanced users only

#### 2.1.7 Update Template Commands for PowerShell Support

**Task**: Add PowerShell script paths to slash command templates
- **Description**: Enable PowerShell execution alongside bash
- **Files to modify**:
  - `templates/commands/specify.md`
  - `templates/commands/plan.md`
  - `templates/commands/tasks.md`
  - `templates/commands/implement.md`
  - `templates/commands/analyze.md`
  - `templates/commands/clarify.md`
- **Dependencies**: 2.1.1-2.1.6
- **Estimated effort**: 2 hours
- **Modification** (example):
  ```yaml
  ---
  scripts:
    sh: scripts/bash/archon-auto-init.sh "$FEATURE_DIR" 2>/dev/null || true
    ps: scripts/powershell/archon-auto-init.ps1 -FeatureDir "$FEATURE_DIR" 2>$null
  ---
  ```

### Phase 2.2: Extended Integration Hooks

#### 2.2.1 Add Silent Sync to /speckit.constitution

**Task**: Track constitutional principles in Archon
- **Description**: Sync constitution.md to Archon documents
- **Files to modify**:
  - `templates/commands/constitution.md`
- **Dependencies**: Phase 1 (archon-sync-documents.sh)
- **Estimated effort**: 1.5 hours
- **Implementation**:
  ```markdown
  1. **Pre-Check** (invisible):
     - bash archon-sync-documents.sh "$REPO_ROOT/memory" pull 2>/dev/null || true

  [... existing constitution workflow ...]

  Final Step: **Background Sync** (invisible):
     - bash archon-sync-documents.sh "$REPO_ROOT/memory" push & 2>/dev/null || true
  ```

#### 2.2.2 Add Silent Sync to /speckit.checklist

**Task**: Sync quality checklists to Archon
- **Description**: Store generated checklists in Archon documents
- **Files to modify**:
  - `templates/commands/checklist.md`
- **Dependencies**: Phase 1 (archon-sync-documents.sh)
- **Estimated effort**: 1.5 hours
- **Implementation**:
  ```markdown
  1. **Pre-Check** (invisible):
     - bash archon-sync-documents.sh "$FEATURE_DIR/checklists" pull 2>/dev/null || true

  [... existing checklist generation ...]

  Final Step: **Background Sync** (invisible):
     - bash archon-sync-documents.sh "$FEATURE_DIR/checklists" push & 2>/dev/null || true
  ```

### Phase 2.3: Webhook Support for Real-Time Sync (KISS Approach)

**Design Principle**: Webhooks are just triggers - they call existing sync scripts instead of duplicating logic.

#### 2.3.1 Create Simple Webhook Listener

**Task**: Lightweight HTTP listener that triggers existing sync scripts
- **Description**: Minimal webhook receiver - just verify and trigger
- **Files to create**:
  - `scripts/bash/archon-webhook-listener.sh` - Bash version (nc-based)
  - `scripts/powershell/archon-webhook-listener.ps1` - PowerShell version
- **Dependencies**: Phase 1 sync scripts (archon-auto-pull-status.sh, archon-sync-documents.sh)
- **Estimated effort**: 2.5 hours (reduced from 9 hours!)
- **Features**:
  - Listens on localhost:8765 (configurable)
  - HMAC signature verification for security
  - Maps webhook events to existing sync script calls
  - NOT started automatically (advanced users only)

**Simplified Implementation** (KISS):
```bash
#!/usr/bin/env bash
# archon-webhook-listener.sh - KISS: Just trigger existing scripts

PORT="${ARCHON_WEBHOOK_PORT:-8765}"
SECRET="${ARCHON_WEBHOOK_SECRET:-changeme}"

while true; do
  REQUEST=$(echo -e "HTTP/1.1 200 OK\n\n" | nc -l -p $PORT)

  # Extract event payload
  PAYLOAD=$(echo "$REQUEST" | tail -n 1)
  EVENT_TYPE=$(echo "$PAYLOAD" | jq -r '.event' 2>/dev/null)
  FEATURE_DIR=$(echo "$PAYLOAD" | jq -r '.feature_dir' 2>/dev/null)

  # Verify HMAC signature
  if ! verify_hmac "$PAYLOAD" "$SECRET"; then
    continue  # Reject invalid signatures silently
  fi

  # Map events to existing sync scripts (KISS!)
  case "$EVENT_TYPE" in
    task.updated|task.created|task.deleted)
      # Use existing status pull script - it already handles everything
      bash archon-auto-pull-status.sh "$FEATURE_DIR" 2>/dev/null &
      ;;

    document.updated|document.created)
      # Use existing document sync script - it already handles everything
      bash archon-sync-documents.sh "$FEATURE_DIR" pull 2>/dev/null &
      ;;

    project.updated)
      # Refresh both documents and tasks
      bash archon-sync-documents.sh "$FEATURE_DIR" pull 2>/dev/null &
      bash archon-auto-pull-status.sh "$FEATURE_DIR" 2>/dev/null &
      ;;
  esac

  # That's it! No queue, no processor, just call existing scripts
done
```

**Why This is Better**:
- ✅ **Reuses Phase 1 logic** - No duplicate sync code
- ✅ **Simpler** - Just a trigger layer (30 lines vs 200+ lines)
- ✅ **Consistent** - Same behavior whether manual or webhook-triggered
- ✅ **Less code** - Fewer files = fewer bugs
- ✅ **Maintainable** - One source of truth for sync logic

**Files Removed** (complexity reduction):
- ~~`archon-webhook-processor.sh`~~ ❌ Not needed! Scripts handle processing
- ~~`archon-webhook-processor.ps1`~~ ❌ Not needed!
- ~~`.archon-state/webhook-queue.jsonl`~~ ❌ No queue needed!
- ~~Daemon integration task~~ ❌ Webhook listener IS the daemon if needed!

### Phase 2.4: Multi-Project Dashboard

#### 2.4.1 Create Dashboard Query Script

**Task**: Aggregate data across all Spec Kit projects
- **Description**: Query Archon for all projects, collect stats
- **Files to create**:
  - `scripts/bash/archon-dashboard.sh`
  - `scripts/powershell/archon-dashboard.ps1`
- **Dependencies**: None
- **Estimated effort**: 4 hours
- **Features**:
  - List all Archon projects (filter by github_repo pattern)
  - For each project:
    - Total tasks, completed tasks, percentage
    - Recent activity (last updated)
    - Current phase/status
  - Output as Markdown table

#### 2.4.2 Create Dashboard Visualization

**Task**: Generate visual dashboard reports
- **Description**: CLI-friendly dashboard with ASCII graphs
- **Files to modify**:
  - `scripts/bash/archon-dashboard.sh` (add --visual flag)
  - `scripts/powershell/archon-dashboard.ps1` (add -Visual switch)
- **Dependencies**: 2.4.1
- **Estimated effort**: 3 hours
- **Output format**:
  ```
  ╔════════════════════════════════════════════════════════════════╗
  ║          Archon-Spec Kit Multi-Project Dashboard             ║
  ╚════════════════════════════════════════════════════════════════╝

  Project: Feature: Photo Albums (001-photo-albums)
  Status: ████████████████░░░░ 80% complete (24/30 tasks)
  Last Updated: 2 hours ago

  Project: Feature: User Auth (002-user-auth)
  Status: ████░░░░░░░░░░░░░░░░ 20% complete (5/25 tasks)
  Last Updated: 1 day ago

  Overall Progress: ████████░░░░░░░░░░░░ 40% (29/55 tasks)
  ```

#### 2.4.3 Create Dependency Graph Visualization

**Task**: Show dependencies between projects/features
- **Description**: Parse task descriptions for references to other features
- **Files to modify**:
  - `scripts/bash/archon-dashboard.sh` (add --dependencies flag)
- **Dependencies**: 2.4.1
- **Estimated effort**: 3.5 hours
- **Output format**:
  ```
  Feature Dependencies:

  001-photo-albums
    ├─ depends on: 002-user-auth (authentication required)
    └─ blocks: 003-sharing (needs album structure)

  002-user-auth
    └─ blocks: 001-photo-albums, 004-admin-panel

  003-sharing
    └─ depends on: 001-photo-albums
  ```

### Phase 2.5: AI-Assisted Conflict Resolution

#### 2.5.1 Create Conflict Detection Script

**Task**: Detect conflicts between Archon and local versions
- **Description**: Compare timestamps and content hashes
- **Files to create**:
  - `scripts/bash/archon-detect-conflicts.sh`
  - `scripts/powershell/archon-detect-conflicts.ps1`
- **Dependencies**: Phase 1 (archon-sync-documents.sh)
- **Estimated effort**: 2.5 hours
- **Workflow**:
  1. Load sync metadata ({feature}.meta)
  2. For each document:
     - Compare local timestamp vs Archon timestamp
     - If both modified since last sync: CONFLICT
  3. Output conflicted files as JSON

#### 2.5.2 Create AI Conflict Analyzer

**Task**: Use Claude API to analyze conflicts
- **Description**: LLM-assisted merge strategy suggestions
- **Files to create**:
  - `scripts/bash/archon-ai-resolve-conflict.sh`
  - `scripts/powershell/archon-ai-resolve-conflict.ps1`
- **Dependencies**: 2.5.1
- **Estimated effort**: 4 hours
- **Workflow**:
  1. Load conflicting document versions (local + Archon)
  2. Construct prompt for Claude:
     ```
     Analyze these two versions of a spec document and suggest a merge strategy:

     LOCAL VERSION:
     {local_content}

     ARCHON VERSION:
     {archon_content}

     Please suggest:
     1. Changes that can be safely auto-merged
     2. Conflicts requiring manual review
     3. Recommended resolution for each conflict
     ```
  3. Parse Claude response
  4. Generate merge suggestions
  5. Present to user for approval

#### 2.5.3 Create Interactive Conflict Resolution

**Task**: User interface for conflict resolution
- **Description**: CLI tool to review and apply merge suggestions
- **Files to create**:
  - `scripts/bash/archon-resolve-conflicts-interactive.sh`
  - `scripts/powershell/archon-resolve-conflicts-interactive.ps1`
- **Dependencies**: 2.5.2
- **Estimated effort**: 4 hours
- **Features**:
  - List conflicted documents
  - For each conflict:
    - Show AI suggestion
    - Options: [A]ccept Archon, [L]ocal, [M]erge with AI, [E]dit manually, [S]kip
  - Apply selected resolution
  - Update sync metadata

#### 2.5.4 Integrate AI Resolution into Sync

**Task**: Optional AI resolution during automatic sync
- **Description**: Add --auto-resolve flag to sync scripts
- **Files to modify**:
  - `scripts/bash/archon-sync-documents.sh`
  - `scripts/powershell/archon-sync-documents.ps1`
- **Dependencies**: 2.5.2
- **Estimated effort**: 2 hours
- **Implementation**:
  ```bash
  # If conflict detected and ARCHON_AUTO_RESOLVE=true
  if detect_conflict "$file"; then
    if [[ "$ARCHON_AUTO_RESOLVE" == "true" ]]; then
      suggestion=$(bash archon-ai-resolve-conflict.sh "$file")
      apply_merge_suggestion "$file" "$suggestion"
    else
      # Default: Archon wins
      overwrite_with_archon "$file"
    fi
  fi
  ```

### Phase 2.6: Testing & Documentation

#### 2.6.1 Create PowerShell Test Suite

**Task**: Mirror bash test suite for PowerShell scripts
- **Description**: Pester tests for all PowerShell archon scripts
- **Files to create**:
  - `tests/archon/test-archon-common.Tests.ps1`
  - `tests/archon/test-archon-auto-init.Tests.ps1`
  - `tests/archon/test-archon-sync-documents.Tests.ps1`
  - `tests/archon/test-archon-auto-sync-tasks.Tests.ps1`
  - `tests/archon/test-archon-auto-pull-status.Tests.ps1`
  - `tests/archon/run-all-tests.ps1`
- **Dependencies**: 2.1.1-2.1.6
- **Estimated effort**: 5 hours
- **Coverage**:
  - MCP detection (silent operation)
  - State file management
  - Document sync (pull/push)
  - Task synchronization
  - Status updates
  - Error handling

#### 2.6.2 Create Integration Test Suite

**Task**: End-to-end testing for new features
- **Files to create**:
  - `tests/archon/test-webhook-integration.sh`
  - `tests/archon/test-dashboard-generation.sh`
  - `tests/archon/test-ai-conflict-resolution.sh`
- **Dependencies**: All Phase 2 tasks
- **Estimated effort**: 4 hours
- **Coverage**:
  - Webhook listener receives and processes events
  - Dashboard generates correct statistics
  - AI conflict resolution produces valid suggestions
  - Multi-project queries work correctly

#### 2.6.3 Update Documentation

**Task**: Document Phase 2 enhancements (fork-only)
- **Description**: Update developer documentation with new features
- **Files to modify**:
  - `docs/archon-integration-internals.md`
  - `FORK_CUSTOMIZATIONS.md`
  - `CLAUDE.md`
- **Dependencies**: All Phase 2 tasks
- **Estimated effort**: 3 hours
- **Content**:
  - PowerShell script usage and patterns
  - Webhook setup instructions (advanced users)
  - Dashboard commands and options
  - AI conflict resolution configuration
  - Environment variables reference
  - Troubleshooting guide

---

## Codebase Integration Points

### Files to Create (Phase 2)

**PowerShell Scripts** (scripts/powershell/):
- `archon-common.ps1` - Core utilities
- `archon-auto-init.ps1` - Project creation
- `archon-sync-documents.ps1` - Bidirectional sync
- `archon-auto-sync-tasks.ps1` - Task synchronization
- `archon-auto-pull-status.ps1` - Status updates
- `archon-daemon.ps1` - Background daemon
- `archon-webhook-listener.ps1` - Webhook receiver (KISS - just triggers sync scripts)
- `archon-dashboard.ps1` - Multi-project dashboard
- `archon-detect-conflicts.ps1` - Conflict detection
- `archon-ai-resolve-conflict.ps1` - AI merge suggestions
- `archon-resolve-conflicts-interactive.ps1` - Interactive resolution

**Bash Scripts** (scripts/bash/):
- `archon-webhook-listener.sh` - Webhook receiver (KISS - triggers existing scripts)
- `archon-dashboard.sh` - Multi-project dashboard
- `archon-detect-conflicts.sh` - Conflict detection
- `archon-ai-resolve-conflict.sh` - AI merge suggestions
- `archon-resolve-conflicts-interactive.sh` - Interactive resolution

**Test Files** (tests/archon/):
- `test-archon-common.Tests.ps1`
- `test-archon-auto-init.Tests.ps1`
- `test-archon-sync-documents.Tests.ps1`
- `test-archon-auto-sync-tasks.Tests.ps1`
- `test-archon-auto-pull-status.Tests.ps1`
- `test-webhook-integration.sh`
- `test-dashboard-generation.sh`
- `test-ai-conflict-resolution.sh`
- `run-all-tests.ps1`

### Files to Modify (Minimal Changes)

| File | Change Type | Purpose |
|------|-------------|---------|
| `templates/commands/specify.md` | Add PS script path | PowerShell support |
| `templates/commands/plan.md` | Add PS script path | PowerShell support |
| `templates/commands/tasks.md` | Add PS script path | PowerShell support |
| `templates/commands/implement.md` | Add PS script path | PowerShell support |
| `templates/commands/analyze.md` | Add PS script path | PowerShell support |
| `templates/commands/clarify.md` | Add PS script path | PowerShell support |
| `templates/commands/constitution.md` | Add silent sync hooks | Constitution tracking |
| `templates/commands/checklist.md` | Add silent sync hooks | Checklist tracking |
| `scripts/bash/archon-daemon.sh` | Add webhook processing | Real-time sync |
| `scripts/bash/archon-sync-documents.sh` | Add conflict resolution | AI-assisted merge |
| `docs/archon-integration-internals.md` | Document Phase 2 | Developer reference |
| `FORK_CUSTOMIZATIONS.md` | List Phase 2 files | Fork maintenance |
| `CLAUDE.md` | Update workflow notes | Agent guidance |

---

## Technical Design

### PowerShell Architecture

**Mirroring Bash Structure**:
```
scripts/bash/                    scripts/powershell/
├── archon-common.sh        →   ├── archon-common.ps1
├── archon-auto-init.sh     →   ├── archon-auto-init.ps1
├── archon-sync-documents.sh →  ├── archon-sync-documents.ps1
├── archon-auto-sync-tasks.sh → ├── archon-auto-sync-tasks.ps1
├── archon-auto-pull-status.sh→ ├── archon-auto-pull-status.ps1
└── archon-daemon.sh        →   └── archon-daemon.ps1
```

**Key Differences** (intentional):
- PowerShell uses `[switch]` parameters instead of `--flag` arguments
- JSON output via `ConvertTo-Json -Compress`
- Error handling via `$ErrorActionPreference` and `try-catch`
- File paths via `Join-Path` instead of string concatenation
- Functions use verb-noun naming (e.g., `Test-ArchonAvailable`)

### Webhook Event Flow (KISS - Simplified)

```
┌─────────────────────────────────────────────────────────────┐
│                    Archon MCP Server                        │
│  (Task status changes, document updates, etc.)              │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP POST webhook
                  ▼
┌─────────────────────────────────────────────────────────────┐
│          archon-webhook-listener (localhost:8765)           │
│  - Verify HMAC signature                                    │
│  - Map event type to existing sync script                   │
│  - Call script in background (& operator)                   │
└─────────────────┬───────────────────────────────────────────┘
                  │ Direct script calls
                  ▼
┌─────────────────────────────────────────────────────────────┐
│         Existing Phase 1 Sync Scripts                       │
│  - archon-auto-pull-status.sh (for task events)            │
│  - archon-sync-documents.sh (for document events)           │
│  - Update local files using existing logic                  │
└─────────────────────────────────────────────────────────────┘

MUCH SIMPLER: No queue, no processor, just trigger existing scripts!
```

### Multi-Project Dashboard Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│              archon-dashboard.sh --visual                   │
└─────────────────┬───────────────────────────────────────────┘
                  │ Query all projects
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Archon MCP Server                        │
│  find_projects() - Filter by github_repo pattern            │
│  For each project:                                          │
│    find_tasks(project_id) - Get task statistics             │
└─────────────────┬───────────────────────────────────────────┘
                  │ Aggregate data
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Generate Markdown Dashboard                    │
│  - Project list with progress bars                          │
│  - Total statistics                                         │
│  - Dependency graph (if --dependencies)                     │
│  - ASCII charts (if --visual)                               │
└─────────────────────────────────────────────────────────────┘
```

### AI Conflict Resolution Flow

```
┌─────────────────────────────────────────────────────────────┐
│       Conflict Detected During Sync                         │
│  (Local and Archon both modified since last sync)           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│         archon-detect-conflicts.sh                          │
│  - Compare timestamps                                       │
│  - Identify conflicted files                                │
│  - Output: { "spec.md": {local: "...", archon: "..."} }    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│         archon-ai-resolve-conflict.sh                       │
│  - Load both versions                                       │
│  - Call Claude API via MCP                                  │
│  - Parse merge suggestions                                  │
│  - Output: { "strategy": "merge", "conflicts": [...] }     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│   archon-resolve-conflicts-interactive.sh (if manual)       │
│  - Present suggestions to user                              │
│  - Get user decision: Accept/Local/Merge/Edit/Skip          │
│  - Apply resolution                                         │
│  - Update sync metadata                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Dependencies and Libraries

**Existing Dependencies** (no change):
- Python 3.11+ with Typer, Rich, httpx
- Bash 4.0+ or PowerShell 7+
- Git (optional)
- Archon MCP server

**New Dependencies** (optional, for advanced features):
- `jq` - JSON parsing in bash (optional, Python fallback available)
- `nc` (netcat) - For bash webhook listener (optional)
- `FastAPI` (Python) - For production webhook receiver (optional)
- `Pester` (PowerShell) - For PowerShell testing (dev only)

**Environment Variables** (new, optional):
- `ARCHON_WEBHOOK_PORT` - Webhook listener port (default: 8765)
- `ARCHON_WEBHOOK_SECRET` - HMAC secret for signature verification
- `ARCHON_AUTO_RESOLVE` - Enable AI conflict resolution (default: false)
- `ARCHON_DASHBOARD_REFRESH` - Dashboard auto-refresh interval (default: 0 = off)

---

## Testing Strategy

### Unit Tests

**PowerShell Unit Tests** (Pester framework):
```powershell
# test-archon-common.Tests.ps1
Describe "Test-ArchonAvailable" {
    It "Returns true when MCP available" {
        Mock Get-Command { return $true }
        Test-ArchonAvailable | Should -Be $true
    }

    It "Returns false when MCP unavailable" {
        Mock Get-Command { return $null }
        Test-ArchonAvailable | Should -Be $false
    }

    It "Produces no output" {
        $output = Test-ArchonAvailable 6>&1
        $output | Should -BeNullOrEmpty
    }
}

Describe "Save-ProjectMapping" {
    It "Creates state file with correct content" {
        Save-ProjectMapping "test-feature" "proj-123"
        $content = Get-Content ".archon-state/test-feature.pid"
        $content | Should -Be "proj-123"
    }
}
```

### Integration Tests

**Webhook Integration Test**:
```bash
#!/usr/bin/env bash
# test-webhook-integration.sh

# Start webhook listener in background
bash archon-webhook-listener.sh &
LISTENER_PID=$!

# Wait for listener to start
sleep 1

# Send test webhook event
curl -X POST http://localhost:8765/webhook \
  -H "Content-Type: application/json" \
  -H "X-Archon-Signature: $(sign_payload "$PAYLOAD" "$SECRET")" \
  -d '{"event":"task.updated","task_id":"task-123","status":"done"}'

# Wait for processing
sleep 2

# Verify queue file created
assert_file_exists ".archon-state/webhook-queue.jsonl"

# Cleanup
kill $LISTENER_PID
```

**Dashboard Generation Test**:
```bash
#!/usr/bin/env bash
# test-dashboard-generation.sh

# Generate dashboard
output=$(bash archon-dashboard.sh --visual)

# Verify output contains expected sections
assert_contains "$output" "Multi-Project Dashboard"
assert_contains "$output" "Overall Progress"
assert_contains "$output" "████"  # Progress bar

# Verify JSON output
json_output=$(bash archon-dashboard.sh --json)
project_count=$(echo "$json_output" | jq '.projects | length')
assert_greater_than $project_count 0
```

### Edge Cases

1. **PowerShell on Linux/macOS**:
   - Test all scripts with pwsh on non-Windows platforms
   - Verify path handling works cross-platform

2. **Webhook Signature Verification**:
   - Test with invalid signatures (should reject)
   - Test with missing signatures (should reject if required)
   - Test with valid signatures (should accept)

3. **AI Conflict Resolution Edge Cases**:
   - Completely different documents (no overlap)
   - Identical changes (no conflict)
   - Partial overlap (suggest merge)
   - Malformed documents (graceful degradation)

4. **Dashboard with No Projects**:
   - Handle empty project list gracefully
   - Display helpful message

5. **Multi-Feature Branch Scenario**:
   - Correct feature detection when multiple branches exist
   - Proper state file isolation

---

## Success Criteria

### Functional Requirements
- [ ] All 6 bash archon scripts have PowerShell equivalents
- [ ] PowerShell scripts pass identical test suite
- [ ] Cross-platform compatibility (Linux, macOS, Windows tested)
- [ ] Constitution and checklist commands have silent hooks
- [ ] Webhook listener receives and processes events correctly
- [ ] Dashboard generates accurate multi-project statistics
- [ ] AI conflict resolution produces helpful merge suggestions
- [ ] All new features remain completely invisible to regular users

### Non-Functional Requirements
- [ ] Zero user-facing changes maintained
- [ ] All operations remain under 2 seconds (excluding AI calls)
- [ ] Webhook processing handles 100+ events without issue
- [ ] Dashboard supports 50+ projects without performance degradation
- [ ] AI conflict resolution works for 90%+ of real conflicts
- [ ] PowerShell memory usage comparable to bash versions
- [ ] All features work without Archon MCP (graceful degradation)

### Quality Gates
- [ ] All unit tests passing (bash and PowerShell)
- [ ] All integration tests passing
- [ ] Code coverage > 80% for new features
- [ ] Manual testing on all 3 platforms (Linux, macOS, Windows)
- [ ] Documentation complete and accurate
- [ ] No performance regressions from Phase 1
- [ ] Fork sync process still functional

---

## Notes and Considerations

### Potential Challenges

1. **PowerShell Cross-Platform Behavior**:
   - **Challenge**: Path separators differ (\ vs /)
   - **Solution**: Always use `Join-Path` and `Split-Path`
   - **Consideration**: Test on all platforms before release

2. **Webhook Security**:
   - **Challenge**: Ensuring only Archon can send events
   - **Solution**: HMAC signature verification
   - **Consideration**: Document secret generation and rotation

3. **AI Conflict Resolution Reliability**:
   - **Challenge**: LLM may suggest incorrect merges
   - **Solution**: Always provide manual override
   - **Consideration**: Test with diverse conflict scenarios

4. **Dashboard Performance with Many Projects**:
   - **Challenge**: 100+ projects may slow dashboard generation
   - **Solution**: Implement pagination and caching
   - **Consideration**: Limit to 50 projects per query by default

5. **PowerShell Version Compatibility**:
   - **Challenge**: PowerShell 5.1 (Windows) vs PowerShell 7+ (cross-platform)
   - **Solution**: Target PowerShell 7+ only (pwsh)
   - **Consideration**: Document version requirement clearly

### Future Enhancements (Beyond Phase 2)

- **Archon Templates**: Store reusable spec/plan templates in Archon knowledge base
- **Automated Testing**: Run tests automatically before sync
- **Diff Visualization**: Side-by-side diff for conflict resolution
- **Mobile Dashboard**: Web-based dashboard accessible from mobile devices
- **Slack/Teams Integration**: Post status updates to team channels
- **Metric Tracking**: Track velocity, lead time, cycle time across projects
- **Predictive Analytics**: Use AI to predict completion dates

### Migration Path

**Existing Phase 1 Users**:
1. Pull latest fork changes (Phase 2 scripts)
2. **No action required** - PowerShell support is automatic
3. Optional: Enable webhook listener for real-time sync
4. Optional: Use dashboard commands for multi-project view
5. Optional: Enable AI conflict resolution (`ARCHON_AUTO_RESOLVE=true`)

**Rollback Strategy**:
1. Phase 2 features are additive (no breaking changes)
2. Remove new scripts to disable features
3. Phase 1 functionality remains intact
4. State files remain compatible

---

## Implementation References

### Key Files to Reference

**PowerShell Script Patterns**:
- `scripts/powershell/common.ps1` - Parameter handling, JSON output
- `scripts/powershell/check-prerequisites.ps1` - Validation, dual output mode
- `scripts/powershell/create-new-feature.ps1` - Directory operations, git handling

**Bash Script Patterns**:
- `scripts/bash/archon-common.sh` - Silent operations, state management
- `scripts/bash/archon-sync-documents.sh` - Bidirectional sync logic

**Command Template Patterns**:
- `templates/commands/specify.md` - Pre/post hook integration
- `templates/commands/plan.md` - RAG integration example

### Conversion Checklist (Bash → PowerShell)

When converting bash scripts to PowerShell:
- [ ] Replace `#!/usr/bin/env bash` with `#!/usr/bin/env pwsh`
- [ ] Replace `set -e -u -o pipefail` with `$ErrorActionPreference = 'Stop'`
- [ ] Replace `$(dirname)` with `Split-Path -Parent`
- [ ] Replace `source file` with `. "$PSScriptRoot/file.ps1"`
- [ ] Replace `if [[ condition ]];` with `if (condition) {`
- [ ] Replace `$var` with `$var` (same, but typed)
- [ ] Replace `echo` with `Write-Output` or direct string
- [ ] Replace `2>/dev/null` with `2>$null`
- [ ] Replace `&& true` with `; $true`
- [ ] Replace JSON parsing with `ConvertFrom-Json` and `ConvertTo-Json`
- [ ] Add `[CmdletBinding()]` and typed parameters
- [ ] Add comment-based help (`.SYNOPSIS`, `.DESCRIPTION`, etc.)

---

**This plan is ready for execution with `/execute-plan PRPs/archon-phase2-enhancements.md`**

## Plan Summary

**Total Effort**: ~60.5 hours (**6.5 hours saved** with KISS approach!)

**Phase Breakdown**:
- Phase 2.1: PowerShell Support (22 hours) - 6 scripts + template updates
- Phase 2.2: Extended Hooks (3 hours) - Constitution and checklist integration
- Phase 2.3: Webhook Support (**2.5 hours** ✅ reduced from 9!) - Simple listener triggers existing scripts
- Phase 2.4: Multi-Project Dashboard (10.5 hours) - Query, visualization, dependencies
- Phase 2.5: AI Conflict Resolution (12.5 hours) - Detection, AI analysis, interactive resolution
- Phase 2.6: Testing & Documentation (10 hours) - Tests and fork documentation

**Complexity Reduction** (KISS wins!):
- ❌ **Removed**: `archon-webhook-processor.sh/ps1` (not needed!)
- ❌ **Removed**: webhook queue system (not needed!)
- ❌ **Removed**: daemon integration task (listener IS the daemon!)
- ✅ **Result**: 3 fewer files, 6.5 hours saved, simpler design

**Files Created**: **~24 new files** (11 PowerShell + 5 bash + tests) - down from 30!
**Files Modified**: ~15 files (command templates + documentation)
**User-Facing Changes**: **STILL ZERO**
**Advanced User Features**: 4 new capabilities (webhooks, dashboard, AI resolution, PowerShell support)

**Key Achievements**:
- ✅ Complete cross-platform support
- ✅ Advanced automation features
- ✅ **Simpler, more maintainable codebase** (KISS principle)
- ✅ Reuses existing Phase 1 logic (no duplication)
- ✅ Maintains Phase 1's invisibility principle

---

*Archon Project ID: cab86909-e19b-457a-9bbb-c1049232f7a3*
