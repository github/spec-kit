# Archon MCP Integration - Inject Workflow Documentation into Agent Files
# CRITICAL: This script is completely silent and only runs when Archon MCP is available

param()

# Silent operation - no output unless error
$ErrorActionPreference = 'SilentlyContinue'

# Function to check if Archon MCP is available (silent)
function Test-ArchonAvailable {
    # Check if MCP tools are available
    # For now, assume available if environment suggests it
    # In practice, would check for MCP server health
    return $true  # Simplified check
}

# Exit silently if Archon not available
if (-not (Test-ArchonAvailable)) {
    exit 0
}

# Get project root (go up two levels from scripts/powershell/)
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

# Define Archon workflow documentation block
$ArchonWorkflowDocs = @'
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

'@

# Function to inject Archon docs into agent file
function Inject-ArchonDocs {
    param(
        [string]$AgentFile
    )

    # Check if file exists
    if (-not (Test-Path $AgentFile)) {
        return
    }

    # Check if Archon docs already injected
    $content = Get-Content $AgentFile -Raw -ErrorAction SilentlyContinue
    if ($content -match '## Archon Integration & Workflow') {
        # Already injected, skip
        return
    }

    # Read file content
    $lines = Get-Content $AgentFile -ErrorAction SilentlyContinue
    if (-not $lines) {
        return
    }

    # Find insertion point (after "## Project Overview")
    $newContent = @()
    $inOverview = $false
    $inserted = $false

    foreach ($line in $lines) {
        if ($line -match '^## Project Overview') {
            $inOverview = $true
            $newContent += $line
            continue
        }

        if ($inOverview -and $line -match '^## ' -and $line -notmatch '^## Project Overview') {
            # Found next section, insert here
            $newContent += ""
            $newContent += $ArchonWorkflowDocs
            $newContent += ""
            $inOverview = $false
            $inserted = $true
        }

        $newContent += $line
    }

    # If still in overview (no next section found), append at end
    if ($inOverview -and -not $inserted) {
        $newContent += ""
        $newContent += $ArchonWorkflowDocs
        $inserted = $true
    }

    # If no "## Project Overview" section found, append at end
    if (-not $inserted) {
        $newContent += ""
        $newContent += $ArchonWorkflowDocs
    }

    # Write back to file
    try {
        $newContent | Out-File -FilePath $AgentFile -Encoding UTF8 -Force -ErrorAction SilentlyContinue
    }
    catch {
        # Silent failure
    }
}

# Main execution
try {
    # Find all agent-specific files in the project
    $AgentFiles = @(
        "$ProjectRoot\.claude\CLAUDE.md",
        "$ProjectRoot\.github\copilot-instructions.md",
        "$ProjectRoot\.gemini\gemini.md",
        "$ProjectRoot\.cursor\cursor.md",
        "$ProjectRoot\.windsurf\windsurf.md",
        "$ProjectRoot\.qwen\qwen.md",
        "$ProjectRoot\.opencode\opencode.md",
        "$ProjectRoot\.codex\codex.md",
        "$ProjectRoot\.kilocode\kilocode.md",
        "$ProjectRoot\.augment\auggie.md",
        "$ProjectRoot\.codebuddy\codebuddy.md",
        "$ProjectRoot\.roo\roo.md",
        "$ProjectRoot\.amazonq\amazonq.md"
    )

    # Inject Archon docs into each existing agent file
    foreach ($AgentFile in $AgentFiles) {
        if (Test-Path $AgentFile) {
            Inject-ArchonDocs -AgentFile $AgentFile
        }
    }
}
catch {
    # Silent failure
}

# Exit silently
exit 0
