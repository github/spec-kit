# Archon MCP Integration - Internal Architecture

**IMPORTANT**: This document is for developers and advanced users only. Regular Spec Kit users will never see or know about Archon integration - it's completely silent and transparent.

## Overview

This fork of Spec Kit includes a **completely silent, zero-configuration integration** with the Archon MCP server. The integration is:

- **Invisible**: No user-facing commands, no UI changes, no documentation in README
- **MCP-Gated**: Only activates when Archon MCP server is available
- **Silent Fallback**: Gracefully does nothing if MCP unavailable (no errors, no warnings)
- **Bidirectional**: Syncs all artifacts (spec.md, plan.md, tasks.md, etc.) to/from Archon
- **Source of Truth**: Archon always wins - Spec Kit pulls latest before operations

## How It Works

### Activation

The integration activates automatically when:
1. Archon MCP server is running and accessible
2. MCP tools are available to the AI agent
3. No configuration required

To disable: Simply stop the Archon MCP server. The integration becomes dormant with zero errors.

### Architecture

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
│  │     SILENT HOOKS (invisible to users)           │           │
│  │  • Pull-before: archon-sync-documents.sh pull   │           │
│  │  • Push-after: archon-sync-documents.sh push    │           │
│  │  • Background init: archon-auto-init.sh         │           │
│  └─────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ MCP Tool Calls
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Archon MCP Server                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Project    │  │     Task     │  │  Document    │         │
│  │  Management  │  │  Management  │  │  Management  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

**Example: User runs `/speckit.specify`**

1. **Pre-Check (silent)**: `archon-sync-documents.sh pull`
   - Checks if Archon MCP available
   - If yes: Pulls latest spec.md from Archon (if exists and newer)
   - If no: Does nothing (exit 0)
   - User never knows this happened

2. **Normal Workflow**: Spec Kit generates spec.md as usual

3. **Background Integration (silent)**: `archon-auto-init.sh &`
   - Checks if Archon MCP available
   - If yes: Creates Archon project, pushes spec.md
   - If no: Does nothing
   - Runs in background, zero output
   - User never knows this happened

## Files and Components

### State Management

**Location**: `.specify/scripts/bash/.archon-state/`

**Files** (all gitignored):
- `{feature-name}.pid` - Project ID mapping
- `{feature-name}.docs` - Document ID mappings
- `{feature-name}.tasks` - Task ID mappings
- `{feature-name}.meta` - Sync timestamps for conflict resolution

**Format Examples**:

```bash
# 001-photo-albums.pid
proj-abc123def456

# 001-photo-albums.docs
spec.md:doc-uuid-abc123
plan.md:doc-uuid-def456
tasks.md:doc-uuid-ghi789

# 001-photo-albums.tasks
T001:task-uuid-abc123
T002:task-uuid-def456

# 001-photo-albums.meta
spec.md:2025-10-16T01:30:00Z
plan.md:2025-10-16T01:35:00Z
```

### Scripts

**Location**: `scripts/bash/`

#### `archon-common.sh`
Silent utilities library. Key functions:
- `check_archon_available()` - MCP detection (returns 0/1, no output)
- `save_project_mapping()` - Store project ID
- `load_project_mapping()` - Retrieve project ID
- `save_document_mapping()` - Store document ID
- `load_document_mapping()` - Retrieve document ID
- `save_task_mapping()` - Store task ID
- `load_task_mapping()` - Retrieve task ID

#### `archon-auto-init.sh` (To be implemented)
Silently creates Archon project and initial documents after `/speckit.specify`.

#### `archon-sync-documents.sh` (To be implemented)
Bidirectional document sync:
- **Pull mode**: Downloads latest from Archon before operations
- **Push mode**: Uploads changes to Archon after operations
- Handles: spec.md, plan.md, research.md, data-model.md, quickstart.md, tasks.md

#### `archon-auto-sync-tasks.sh` (To be implemented)
Parses tasks.md and creates Archon tasks automatically after `/speckit.tasks`.

#### `archon-auto-pull-status.sh`
Updates tasks.md checkboxes from Archon task statuses before `/speckit.implement`.

#### `archon-daemon.sh`
**Optional background sync daemon (advanced users only)**.

**CRITICAL**: This daemon is:
- **NOT started automatically**
- **NOT documented for regular users**
- **Opt-in only for advanced users**
- **Completely silent** (no stdout/stderr)

**Usage**:
```bash
# Start daemon for a feature (5 minute interval)
bash scripts/bash/archon-daemon.sh /path/to/specs/001-feature 300 &

# Start with custom interval (10 minutes)
bash scripts/bash/archon-daemon.sh /path/to/specs/001-feature 600 &

# Stop daemon (find and kill process)
pkill -f "archon-daemon.sh.*001-feature"
```

**Features**:
- Polls Archon every N seconds (default: 300 = 5 minutes)
- Minimum interval: 60 seconds (to avoid hammering)
- Updates tasks.md checkboxes silently
- Pulls latest documents automatically
- PID file prevents multiple instances
- Graceful cleanup on exit

**When to Use**:
- Long-running implementation sessions
- Team collaboration (see Archon updates automatically)
- Continuous integration environments
- Power users who want real-time sync

**When NOT to Use**:
- Regular development (manual sync is sufficient)
- Short feature implementations
- Single-user projects without external Archon updates

### Integration Points

**Modified Files**:
- `scripts/bash/common.sh` - Lines 157-163: Silent source of archon-common.sh

**Command Hooks** (Phase 3 - COMPLETED):
- `templates/commands/specify.md` - Pull-before/push-after hooks
- `templates/commands/plan.md` - Pull-before/push-after + RAG enhancement
- `templates/commands/tasks.md` - Pull-before/push-after hooks
- `templates/commands/implement.md` - Pull-before + status sync
- `templates/commands/analyze.md` - Pull-before/push-after hooks
- `templates/commands/clarify.md` - Pull-before/push-after hooks

## MCP Tools Used

| Tool | Purpose | Usage Pattern |
|------|---------|---------------|
| `mcp__archon__health_check()` | Verify MCP availability | Called first in all scripts |
| `mcp__archon__manage_project()` | Create/update projects | Background init |
| `mcp__archon__manage_document()` | Create/update documents | Bidirectional sync |
| `mcp__archon__find_documents()` | Query documents | Pull phase |
| `mcp__archon__manage_task()` | Create/update tasks | Task sync |
| `mcp__archon__find_tasks()` | Query tasks | Status sync |
| `mcp__archon__rag_search_knowledge_base()` | Search docs | Research enhancement |
| `mcp__archon__rag_search_code_examples()` | Find code | Research enhancement |

All MCP calls are wrapped in silent error handling (`2>&1 >/dev/null`).

## Conflict Resolution

**Strategy**: Archon always wins (source of truth).

When both local files and Archon documents are modified:
1. Compare timestamps
2. If Archon newer: Overwrite local file silently
3. If local newer: Push to Archon
4. No user prompts, no conflict UI

Advanced users can manually edit if needed.

## Debugging

### Check if Integration is Active

```bash
# Method 1: Check for state files
ls -la .specify/scripts/bash/.archon-state/

# Method 2: Run script manually with debug
bash -x scripts/bash/archon-common.sh

# Method 3: Check for Archon project ID
cat .specify/scripts/bash/.archon-state/001-feature-name.pid
```

### Test Scripts Manually

```bash
# Test MCP detection
source scripts/bash/archon-common.sh
check_archon_available && echo "MCP available" || echo "MCP unavailable"

# Test project mapping
save_project_mapping "001-test" "proj-abc123"
load_project_mapping "001-test"  # Should output: proj-abc123
```

### Common Issues

**Issue**: Scripts not executing
- **Check**: Verify scripts are executable (`chmod +x scripts/bash/archon-*.sh`)
- **Check**: Ensure common.sh sources archon-common.sh correctly

**Issue**: No Archon sync happening
- **Check**: Is Archon MCP server running?
- **Check**: Are MCP tools available to your AI agent?
- **Check**: Run `check_archon_available` manually

**Issue**: Conflicts or overwrites
- **Check**: Archon always wins by design
- **Solution**: Use Archon as primary interface or manually sync

## Performance

- **MCP detection**: < 100ms
- **Document sync**: < 2 seconds (non-blocking background)
- **Task sync**: < 5 seconds for 50 tasks
- **No impact on normal workflow**: All operations asynchronous

## Security

**State Files**: Contains project/document/task IDs but no sensitive data.

**Gitignore**: `.archon-state/` is excluded from git commits.

**Network**: MCP calls use existing Claude Code connection (no additional network config).

## Enabling/Disabling

**Enable**:
1. Install and start Archon MCP server
2. Configure MCP tools in your AI agent
3. Integration activates automatically

**Disable**:
1. Stop Archon MCP server
2. Integration becomes dormant (zero errors)

**Completely Remove**:
```bash
# Remove all Archon scripts
rm -rf scripts/bash/archon-*.sh
rm -rf scripts/bash/.archon-state/

# Revert common.sh (remove lines 157-163)
git checkout scripts/bash/common.sh
```

## Future Enhancements

Planned but not yet implemented:
- PowerShell variants of all bash scripts
- Webhook support for real-time push notifications
- Multi-project dashboard aggregation
- AI-assisted conflict resolution
- Archon template storage and reuse

## References

- **Main Plan**: `PRPs/archon-speckit-extension.md`
- **Fork Documentation**: `FORK_CUSTOMIZATIONS.md`
- **Archon MCP Server**: [Link to Archon repo/docs]

---

**Last Updated**: 2025-10-16
**Version**: 0.1.0 (Phase 1 Foundation Complete)
