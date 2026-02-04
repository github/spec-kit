---
description: Configure AI agents, skills, and MCP server for the project
semantic_anchors:
  - Single Responsibility    # Each agent has one clear purpose
  - Separation of Concerns   # Skills vs workflow orchestration
  - Capability Mapping       # Skills to agent assignment
scripts:
  sh: scripts/bash/setup-hooks.sh --json --agent-dir __AGENT_DIR__
  ps: scripts/powershell/setup-hooks.ps1 -Json -AgentDir __AGENT_DIR__
---

## User Input

```text
$ARGUMENTS
```

Options: `--skip-skills`, `--skip-agents`, `--skip-mcp`

## Purpose

Configure the AI tooling for the project in 3 steps:
1. **Skills**: Create domain-specific skills from detected frameworks
2. **Agents**: Generate specialized subagents for SpecKit workflow
3. **MCP**: Configure MCP server for testing and automation

---

## Step 1: Detect Project

### 1.1 Run Detection Script

Run `{SCRIPT}` from repo root and parse the JSON output:

```json
{
  "PROJECT_TYPE": "node-typescript | python | rust | go | ...",
  "DETECTED_TOOLS": ["npm", "typescript", "jest", ...],
  "DETECTED_FRAMEWORKS": [
    {"name": "react", "docs_url": "...", "github_url": "..."},
    {"name": "next", "docs_url": "...", "github_url": "..."}
  ],
  "AGENT_DIR": "/path/to/__AGENT_DIR__",
  "SKILLS_DIR": "/path/to/__AGENT_DIR__/skills"
}
```

---

## Step 2: Skills

### 2.1 Generate Skills from Detected Frameworks

For each detected framework, create a skill file in `{SKILLS_DIR}/`:

**Example**: `{SKILLS_DIR}/react-patterns.md`

```markdown
---
name: react-patterns
description: React best practices and patterns for this project
---

# React Patterns

## Component Structure
- Use functional components with hooks
- Co-locate styles, tests, and types

## State Management
[Based on detected: zustand/redux/context]

## Conventions
[Extracted from codebase or defaults]
```

### 2.2 Skill Categories

| Category | Skill Example | Source |
|----------|---------------|--------|
| Frontend | react-patterns, next-conventions | Detected frameworks |
| Backend | express-patterns, prisma-usage | Detected frameworks |
| Testing | jest-conventions, playwright-setup | Detected test tools |
| Project | project-standards | README, CLAUDE.md |

**Skip if**: `--skip-skills` flag provided

---

## Step 3: Agents

### 3.1 Create Agent Directory

```bash
mkdir -p {AGENT_DIR}/agents/speckit
```

### 3.2 Generate SpecKit Workflow Agents

Create specialized agents in `{AGENT_DIR}/agents/speckit/`:

| Agent | Purpose | Skills Used |
|-------|---------|-------------|
| **spec-analyzer** | Analyzes specifications | project-standards |
| **designer** | Creates technical designs | project-standards, {backend-skill} |
| **implementer** | Implements code | {frontend-skill}, {backend-skill} |
| **tester** | Writes and runs tests | {test-skill} |
| **researcher** | Codebase exploration | project-standards |

**Example**: `{AGENT_DIR}/agents/speckit/implementer.md`

```markdown
---
name: implementer
tools: Read, Glob, Grep, Bash, Edit, Write
model: sonnet
skills: project-standards, react-patterns, prisma-usage
---

# Implementer Agent

You implement features according to the plan and design documents.

## Workflow
1. Read the task from tasks.md
2. Load relevant skills for the technology
3. Implement following project conventions
4. Write tests as specified in the plan

## Skills Loaded
{{skills}}
```

**Skip if**: `--skip-agents` flag provided

---

## Step 4: MCP Server

### 4.1 Detect Services

```bash
# Check for Docker
ls docker-compose.yml docker-compose.yaml 2>/dev/null

# Check for package.json scripts
cat package.json | jq '.scripts' 2>/dev/null
```

### 4.2 Generate MCP Configuration

Create `.mcp/project-server/` with tools for:

| Tool | Purpose |
|------|---------|
| `start_service` | Start backend/frontend/db |
| `stop_service` | Stop services |
| `view_logs` | Stream service logs |
| `run_tests` | Execute test suite |
| `http_request` | API testing |

**Example MCP config** (for agent settings):

```json
{
  "mcpServers": {
    "project": {
      "command": "node",
      "args": [".mcp/project-server/index.js"],
      "env": {}
    }
  }
}
```

**Skip if**: `--skip-mcp` flag provided

---

## Completion Report

```markdown
## Agents Setup Complete

### Skills Created
| Skill | Description |
|-------|-------------|
| {skill} | {description} |

### Agents Created
| Agent | Skills | Path |
|-------|--------|------|
| {agent} | {skills} | {path} |

### MCP Server
- Status: ✓ Configured / Skipped
- Path: .mcp/project-server/
- Tools: start_service, stop_service, view_logs, run_tests

### Next Steps
1. Review generated skills in {SKILLS_DIR}/
2. Customize agent prompts in {AGENT_DIR}/agents/speckit/
3. Test MCP server: `node .mcp/project-server/index.js`
```
