---
description: Analyze current project and recommend which agents/MCP servers to keep or remove for optimal context management
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

This command analyzes the current project context and provides actionable recommendations for managing Claude Code agents and MCP servers to optimize performance and context window usage.

1. **Analyze Current Configuration**: Scan the project for:
   - Active agents (from agent context files)
   - Installed MCP servers (from configuration)
   - Recent conversation history
   - Project characteristics (language, framework, dependencies)

2. **Usage Pattern Analysis**: Review recent interactions to determine:
   - Which tools/servers were actually used
   - Frequency of usage per agent/MCP server
   - Context window pressure indicators
   - Redundant capabilities

3. **Generate Recommendations**: Create a structured analysis with:
   - KEEP: Essential agents/servers for this project
   - REMOVE: Unused or redundant agents/servers
   - CONSIDER: Optional servers based on project type
   - Action items with justifications

4. **Report**: Output findings in a clear, actionable format

## Execution Flow

### Phase 1: Discovery

1. **Identify Agent Context Files**:
   - Search for agent-specific files: `.claude/`, `CLAUDE.md`, `GEMINI.md`, etc.
   - Parse active agent configurations
   - Extract enabled features and tools

2. **Scan MCP Server Configuration**:
   - Check for MCP server installations
   - List configured servers
   - Identify server capabilities

3. **Analyze Project Type**:
   - Detect primary language(s)
   - Identify frameworks and tools
   - Assess project complexity

### Phase 2: Usage Analysis

1. **Review Recent Activity** (if conversation history available):
   - Count tool invocations per server
   - Track which agents were used
   - Measure context window consumption

2. **Identify Patterns**:
   - Frequently used capabilities
   - Unused features consuming context
   - Overlapping functionality

### Phase 3: Recommendation Generation

**Format your recommendations as follows:**

```markdown
# Agent & MCP Server Recommendations

**Project Type**: [Detected type - e.g., "Python web application", "React frontend"]
**Analysis Date**: [Current date]

## Current Configuration

### Agents
- [List all detected agents with status]

### MCP Servers
- [List all detected MCP servers with status]

## Recommendations

### ✅ KEEP (Essential)

**Agents:**
- **[Agent Name]**: [Justification based on project needs]
  - **Why**: [Specific reason - e.g., "Primary development agent for this project"]
  - **Usage**: [Frequency/importance]

**MCP Servers:**
- **[Server Name]**: [Justification]
  - **Why**: [Specific reason]
  - **Features Used**: [List actually used features]
  - **Impact**: [Context/performance impact]

### ❌ REMOVE (Unused/Redundant)

**Agents:**
- **[Agent Name]**: [Reason for removal]
  - **Why Remove**: [Specific reason - e.g., "Not used in last 50 interactions"]
  - **Savings**: [Estimated context window savings]

**MCP Servers:**
- **[Server Name]**: [Reason for removal]
  - **Why Remove**: [Specific reason]
  - **Alternative**: [If applicable - what to use instead]
  - **Savings**: [Estimated context/memory savings]

### 🤔 CONSIDER (Project-Specific)

**Might Add:**
- **[Server/Agent Name]**: [Use case]
  - **When to Add**: [Condition - e.g., "If you start working with databases"]
  - **Benefits**: [What it would enable]

**Might Remove:**
- **[Server/Agent Name]**: [Condition]
  - **When to Remove**: [Condition - e.g., "If you finish the API integration work"]

## Action Items

1. [ ] Remove unused agent configurations:
   ```bash
   # Commands to remove specific agents
   ```

2. [ ] Uninstall redundant MCP servers:
   ```bash
   # Commands to uninstall specific servers
   ```

3. [ ] Update agent context files to reflect changes

4. [ ] (Optional) Add recommended servers for this project type:
   ```bash
   # Installation commands for suggested additions
   ```

## Expected Impact

- **Context Window Savings**: ~[X]% reduction
- **Startup Time**: ~[X]s faster
- **Memory Usage**: ~[X]MB reduction
- **Maintained Capabilities**: [List essential features preserved]

## Notes

[Any additional context-specific observations or warnings]
```

## Analysis Guidelines

### Red Flags for Removal

An agent/MCP server should be marked for **REMOVE** if:

- **Zero Usage**: Not invoked in recent conversation history (last 30+ messages)
- **Redundant**: Another server provides identical/better functionality
- **Overhead**: Large context footprint with minimal value
- **Project Mismatch**: Server capabilities don't align with project type
  - Example: Database MCP server in a pure frontend project
  - Example: Python-specific tools in a Node.js project

### Must Keep Criteria

An agent/MCP server should be marked as **KEEP** if:

- **Actively Used**: Invoked multiple times in recent history
- **Project-Critical**: Essential for primary development tasks
  - Example: `filesystem` MCP for file operations
  - Example: `git` MCP for version control
- **No Alternative**: Provides unique capabilities
- **Low Overhead**: Minimal context consumption with high utility

### Project Type Heuristics

Use these guidelines to match servers to project types:

**Web Development:**
- KEEP: `browser-automation`, `fetch`, `filesystem`
- CONSIDER: `playwright` for testing, `figma` for design integration

**Data/ML Projects:**
- KEEP: `sqlite`, `filesystem`
- CONSIDER: `jupyter`, database-specific MCPs

**API Development:**
- KEEP: `fetch`, `filesystem`, `git`
- CONSIDER: `sequential-thinking` for complex logic

**Frontend Only:**
- REMOVE: Database MCPs, backend-specific tools
- KEEP: `browser-automation`, design tools

**General Development:**
- KEEP: `filesystem`, `git`, `sequential-thinking`
- REMOVE: Specialty MCPs not matching tech stack

## Error Handling

- **If no agents detected**: WARN "No agent configurations found. This might be a new project."
- **If no MCP servers**: INFORM "No MCP servers installed. Consider adding based on project needs."
- **If cannot determine usage**: Note in recommendations that usage analysis was unavailable, base recommendations solely on project type

## Example Output

For a React frontend project with database, playwright, and figma MCPs:

```markdown
## Recommendations

### ✅ KEEP (Essential)

**MCP Servers:**
- **filesystem**: File operations essential for all development
- **git**: Version control integration for commits and PRs
- **browser-automation** (if present): Critical for testing React UIs

### ❌ REMOVE (Unused/Redundant)

**MCP Servers:**
- **sqlite**: Database operations not needed for frontend-only project
  - **Why Remove**: No backend code detected, no database files
  - **Savings**: ~15% context window reduction
  - **Alternative**: Use API calls to backend services

### 🤔 CONSIDER (Project-Specific)

**Keep if used:**
- **figma**: Useful if actively integrating design assets
  - **When to Remove**: After initial design implementation phase

**Add if needed:**
- **playwright**: Consider adding for E2E testing as project matures
```

## Final Notes

- Recommendations are **non-destructive** - this command only analyzes and suggests
- Users must manually execute removal commands
- Context window optimization is iterative - re-run this command as project evolves
- When in doubt, keep servers with low overhead (filesystem, git, sequential-thinking)
