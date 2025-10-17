#!/usr/bin/env bash
# Archon MCP Integration - Inject Workflow Documentation into Agent Files
# CRITICAL: This script is completely silent and only runs when Archon MCP is available

set -e

# Silent operation - no output unless error
SILENT=true

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/archon-common.sh" ]]; then
    source "$SCRIPT_DIR/archon-common.sh" 2>/dev/null || exit 0
fi

# Check if Archon MCP is available (silent)
if ! check_archon_available 2>/dev/null; then
    # Archon not available, exit silently
    exit 0
fi

# Get project root (go up two levels from scripts/bash/)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Define Archon workflow documentation block
read -r -d '' ARCHON_WORKFLOW_DOCS <<'EOF' || true
## Archon Integration & Workflow

**CRITICAL: This project uses Archon MCP server for task tracking and knowledge management.**

### Core Workflow: Task-Driven Development

**MANDATORY task cycle before coding:**

1. **Get Task** → `find_tasks(filter_by="status", filter_value="todo")`
2. **Start Work** → `manage_task("update", task_id="...", status="doing")`
3. **Research** → Use knowledge base: `rag_search_knowledge_base(query="...", match_count=5)`
4. **Implement** → Write code based on research
5. **Review** → `manage_task("update", task_id="...", status="review")`
6. **Done** → `manage_task("update", task_id="...", status="done")` (only after validation)

### Implementation Phase Workflow

**A. Project Setup** (if not exists):
```bash
# Create Archon project for feature
project_id = manage_project("create",
  title="Feature: [feature name]",
  description="Implementation of spec ###-feature-name"
)
```

**B. Bulk Task Creation** (upfront, before coding):
```bash
# Parse tasks.md and create ALL tasks in Archon
# For each task in tasks.md:
manage_task("create", project_id="proj-xxx",
  title="[task title]",
  description="[task details]",
  task_order=10  # Higher = higher priority
)
```

**C. Implementation Cycle** (one task at a time):
```bash
# Find next task
tasks = find_tasks(filter_by="status", filter_value="todo")

# Start work (ONLY ONE task in "doing" at a time)
manage_task("update", task_id=tasks[0].id, status="doing")

# Research if needed
rag_search_knowledge_base(query="relevant keywords", match_count=5)

# Implement following TDD (tests first, then code)

# Mark for review (NOT done yet)
manage_task("update", task_id=tasks[0].id, status="review")
```

**D. Validation Phase** (after ALL tasks in review):
```bash
# Run tests, validate against spec.md
# For each validated task:
manage_task("update", task_id="task-xxx", status="done")
```

**E. Critical Rules**:
- ✅ Create ALL tasks upfront (bulk creation before coding)
- ✅ Only ONE task in "doing" status at any time
- ✅ Complete each task before starting next
- ✅ Move to "review" after implementation (not "done")
- ✅ Move to "done" only after validation passes
- ❌ NEVER skip task status updates
- ❌ NEVER work on multiple tasks simultaneously

### Archon Tool Reference

**Projects:**
- `find_projects(query="...")` - Search projects
- `manage_project("create"/"update"/"delete", ...)` - Manage projects

**Tasks:**
- `find_tasks(filter_by="status"/"project", filter_value="...")` - Filter tasks
- `manage_task("create"/"update"/"delete", ...)` - Manage tasks

**Knowledge Base:**
- `rag_get_available_sources()` - List all sources
- `rag_search_knowledge_base(query="...", source_id="...")` - Search docs
- `rag_search_code_examples(query="...")` - Find code examples

**Important Notes:**
- Task status flow: `todo` → `doing` → `review` → `done`
- Keep queries SHORT (2-5 keywords) for better search results
- Higher `task_order` = higher priority (0-100)
- Tasks should be 30 min - 4 hours of work

EOF

# Function to inject Archon docs into agent file
inject_archon_docs() {
    local agent_file="$1"

    # Check if file exists
    if [[ ! -f "$agent_file" ]]; then
        return 0
    fi

    # Check if Archon docs already injected
    if grep -q "## Archon Integration & Workflow" "$agent_file" 2>/dev/null; then
        # Already injected, skip
        return 0
    fi

    # Find insertion point (after project overview, before other sections)
    # Insert after "## Project Overview" or at the end of file if not found

    local temp_file="${agent_file}.archon.tmp"
    local inserted=false

    # Try to insert after "## Project Overview" section
    if grep -q "^## Project Overview" "$agent_file" 2>/dev/null; then
        # Find the next section heading after Project Overview
        awk -v docs="$ARCHON_WORKFLOW_DOCS" '
            /^## Project Overview/ {
                in_overview = 1
                print
                next
            }
            in_overview && /^## / && !/^## Project Overview/ {
                # Found next section, insert here
                print ""
                print docs
                print ""
                in_overview = 0
            }
            { print }
            END {
                # If still in overview (no next section found), append at end
                if (in_overview) {
                    print ""
                    print docs
                }
            }
        ' "$agent_file" > "$temp_file"
        inserted=true
    else
        # No "## Project Overview" section, append at end of file
        cat "$agent_file" > "$temp_file"
        echo "" >> "$temp_file"
        echo "$ARCHON_WORKFLOW_DOCS" >> "$temp_file"
        inserted=true
    fi

    # Replace original file if insertion successful
    if [[ "$inserted" == "true" ]] && [[ -f "$temp_file" ]]; then
        mv "$temp_file" "$agent_file" 2>/dev/null || true
    else
        rm -f "$temp_file" 2>/dev/null || true
    fi

    return 0
}

# Main execution
main() {
    # Find all agent-specific files in the project
    local agent_files=(
        "$PROJECT_ROOT/.claude/CLAUDE.md"
        "$PROJECT_ROOT/.github/copilot-instructions.md"
        "$PROJECT_ROOT/.gemini/gemini.md"
        "$PROJECT_ROOT/.cursor/cursor.md"
        "$PROJECT_ROOT/.windsurf/windsurf.md"
        "$PROJECT_ROOT/.qwen/qwen.md"
        "$PROJECT_ROOT/.opencode/opencode.md"
        "$PROJECT_ROOT/.codex/codex.md"
        "$PROJECT_ROOT/.kilocode/kilocode.md"
        "$PROJECT_ROOT/.augment/auggie.md"
        "$PROJECT_ROOT/.codebuddy/codebuddy.md"
        "$PROJECT_ROOT/.roo/roo.md"
        "$PROJECT_ROOT/.amazonq/amazonq.md"
    )

    # Inject Archon docs into each existing agent file
    for agent_file in "${agent_files[@]}"; do
        if [[ -f "$agent_file" ]]; then
            inject_archon_docs "$agent_file" 2>/dev/null || true
        fi
    done

    # Exit silently
    exit 0
}

# Run main function (completely silent)
main 2>/dev/null || exit 0
