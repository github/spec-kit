---
description: Complete project setup - configures hooks, skills, agents, and constitution in one command
scripts:
  sh: scripts/bash/setup-hooks.sh --json
  ps: scripts/powershell/setup-hooks.ps1 -Json
---

# SpecKit Project Setup

You are the **Setup Orchestrator**. Complete the full initial setup for this SpecKit project in **3 phases**.

## User Input

```text
$ARGUMENTS
```

Consider any user preferences from the input above.

---

## Phase 1: Detect Project & Configure Hooks/Skills

### Step 1.1: Run Detection Script

Run `{SCRIPT}` from repo root and parse the JSON output:

```json
{
  "PROJECT_TYPE": "node-typescript | python | rust | go | java-maven | scala-sbt | ...",
  "DETECTED_TOOLS": ["npm", "typescript", "jest", ...],
  "DETECTED_FRAMEWORKS": [
    {"name": "react", "docs_url": "https://react.dev"},
    {"name": "next", "docs_url": "https://nextjs.org/docs"}
  ],
  "CLAUDE_DIR": "/path/to/.claude",
  "SKILLS_DIR": "/path/to/.claude/skills",
  "HOOKS_DIR": "/path/to/.claude/hooks"
}
```

### Step 1.2: Create Skills for Detected Frameworks

For each detected framework, create a skill folder structure:

```
.claude/skills/{framework}-architecture/
├── SKILL.md           # Quick reference (trigger phrases, core patterns)
└── references/        # Detailed docs
    ├── patterns.md    # Common patterns
    └── best-practices.md
```

**SKILL.md format:**
```markdown
---
name: {Framework} Architecture
description: "Best practices and patterns for {Framework} development"
triggers: ["{framework}", "{framework} pattern", "{framework} best practice"]
---

# {Framework} Architecture Skill

## Quick Reference
| Pattern | When to Use |
|---------|-------------|
| ... | ... |

## See Also
- references/patterns.md
- references/best-practices.md
```

Use WebFetch on `docs_url` to gather framework-specific patterns and best practices.

### Step 1.4: Create Universal Skills (Always Created)

Create these skills for every project:

**Code Review Skill** (`.claude/skills/code-review/`):
```
.claude/skills/code-review/
├── SKILL.md
└── references/
    ├── review-checklist.md
    └── security-review.md
```

Copy from `.specify/templates/skills/code-review/` if available, or create with:
- Review checklist (correctness, security, performance, maintainability)
- Security review patterns (OWASP Top 10, language-specific)
- Quality gates and thresholds

**Tech Debt Skill** (`.claude/skills/tech-debt/`):
```
.claude/skills/tech-debt/
├── SKILL.md
└── references/
    ├── debt-patterns.md
    └── refactoring-strategies.md
```

Copy from `.specify/templates/skills/tech-debt/` if available, or create with:
- Debt categories (design, code, test, doc, dependency, infrastructure)
- Common debt patterns and indicators
- Refactoring strategies and prioritization

### Step 1.5: Configure Hooks

Create `.claude/settings.local.json` with hooks based on PROJECT_TYPE:

**For Node/TypeScript projects:**
```json
{
  "hooks": {
    "SessionStart": [{"command": "npm install"}],
    "PostToolUse": [
      {"event": "Edit", "command": "npx prettier --write $FILE_PATH"}
    ],
    "Stop": [{"command": "npm test"}]
  }
}
```

**For Python projects:**
```json
{
  "hooks": {
    "SessionStart": [{"command": "pip install -r requirements.txt"}],
    "PostToolUse": [
      {"event": "Edit", "command": "ruff format $FILE_PATH"}
    ],
    "Stop": [{"command": "pytest"}]
  }
}
```

Adapt for other project types (Rust: cargo, Go: go mod, etc.)

---

## Phase 2: Create Project Agents

### Step 2.1: Create Agents Directory

```bash
mkdir -p .claude/agents/speckit
```

### Step 2.2: Create Workflow Agents

Create these agent files in `.claude/agents/speckit/`:

**researcher.md:**
```markdown
---
name: researcher
tools: Read, Glob, Grep, WebFetch, WebSearch
model: sonnet
skills: {detected-framework-skills}
---

# Researcher Agent

Expert at exploring codebases and gathering technical information.

## Responsibilities
- Search codebase for patterns and implementations
- Research external documentation
- Analyze dependencies and architecture
- Provide detailed technical reports
```

**planner.md:**
```markdown
---
name: planner
tools: Read, Glob, Grep, Write, Edit
model: sonnet
skills: {detected-framework-skills}
---

# Planner Agent

Decomposes complex tasks into actionable implementation steps.

## Responsibilities
- Break down features into tasks
- Identify dependencies between tasks
- Estimate complexity and order of execution
- Create detailed implementation plans
```

**backend-coder.md:**
```markdown
---
name: backend-coder
tools: Read, Glob, Grep, Bash, Edit, Write
model: sonnet
skills: {detected-framework-skills}
---

# Backend Coder Agent

Implements backend services, APIs, and data layers.

## Responsibilities
- Implement API endpoints
- Database operations and migrations
- Business logic implementation
- Integration with external services
```

**frontend-coder.md:**
```markdown
---
name: frontend-coder
tools: Read, Glob, Grep, Bash, Edit, Write
model: sonnet
skills: {detected-framework-skills}
---

# Frontend Coder Agent

Implements user interfaces and frontend logic.

## Responsibilities
- Component implementation
- State management
- Styling and responsive design
- User interaction handling
```

**tester.md:**
```markdown
---
name: tester
tools: Read, Glob, Grep, Bash, Edit, Write
model: sonnet
skills: {detected-framework-skills}
---

# Tester Agent

Creates and maintains test suites.

## Responsibilities
- Write unit tests
- Write integration tests
- Test coverage analysis
- Fix failing tests
```

**reviewer.md:**
```markdown
---
name: reviewer
tools: Read, Glob, Grep, Bash
model: sonnet
skills: code-review, tech-debt, {detected-framework-skills}
---

# Code Reviewer Agent

Analyzes code quality and identifies technical debt.

## Responsibilities
- Review code for quality issues
- Identify security vulnerabilities
- Detect technical debt patterns
- Provide refactoring recommendations
- Generate code health reports
```

Replace `{detected-framework-skills}` with the actual skill names created in Phase 1.

---

## Phase 3: Initialize Constitution

### Step 3.1: Load Constitution Template

Read `.specify/memory/constitution.md` template.

### Step 3.2: Gather Project Information

Analyze the project to fill constitution placeholders:
- **PROJECT_NAME**: From package.json, Cargo.toml, pyproject.toml, or directory name
- **PROJECT_PURPOSE**: Infer from README or ask user
- **CORE_PRINCIPLES**: Based on detected frameworks and project type

### Step 3.3: Create Constitution

Write the filled constitution to `.specify/memory/constitution.md` with:
- Project name and purpose
- 3-5 core principles based on the project type
- Governance section with versioning policy
- Ratification date (today)

---

## Completion Summary

After all phases complete, output a summary:

```markdown
## SpecKit Setup Complete

### Phase 1: Hooks & Skills
- Project Type: {PROJECT_TYPE}
- Detected Frameworks: {list}
- Framework Skills: {list of framework-specific skills}
- Universal Skills: code-review, tech-debt
- Hooks Configured: SessionStart, PostToolUse, Stop

### Phase 2: Agents
- Created: researcher, planner, backend-coder, frontend-coder, tester, reviewer
- Location: .claude/agents/speckit/

### Phase 3: Constitution
- Created: .specify/memory/constitution.md
- Principles: {count} core principles defined

### Next Steps
1. Run `/speckit.specify` to create your first feature specification
2. Run `/speckit.plan` to create an implementation plan
3. Run `/speckit.review` before/after implementation for quality checks
```
