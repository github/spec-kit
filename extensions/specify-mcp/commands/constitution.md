---
description: "Manage project constitution and governance rules"
tools:
  - 'specify-mcp/constitution'
---

# Manage Constitution

Create and manage the project constitution for governance.

## Purpose

The constitution defines:
- Foundational principles and values
- Quality standards and gates
- Architectural constraints
- Decision-making frameworks
- Team agreements

## Prerequisites

1. Specify MCP server running
2. Project initialized with spec-kit

## User Input

$ARGUMENTS

## Steps

### Step 1: Get Current Constitution

View existing constitution:

Use MCP tool: `specify-mcp/constitution`

Parameters:
- `action`: "get"
- `project_path`: Project root path

```json
{
  "action": "get",
  "project_path": "."
}
```

### Step 2: Create Constitution (if needed)

Initialize a new constitution:

Use MCP tool: `specify-mcp/constitution`

Parameters:
- `action`: "create"
- `project_path`: Project root path
- `template`: Constitution template (optional)

```json
{
  "action": "create",
  "project_path": ".",
  "template": "default"
}
```

### Step 3: Update Constitution

Modify constitution rules:

Use MCP tool: `specify-mcp/constitution`

Parameters:
- `action`: "update"
- `project_path`: Project root path
- `section`: Section to update (optional)
- `content`: New content (optional)

```json
{
  "action": "update",
  "project_path": ".",
  "section": "quality-standards",
  "content": "All code must have >80% test coverage"
}
```

### Step 4: Validate Constitution

Check constitution validity:

Use MCP tool: `specify-mcp/constitution`

Parameters:
- `action`: "validate"
- `project_path`: Project root path

```json
{
  "action": "validate",
  "project_path": "."
}
```

## Constitution Structure

The constitution (`.specify/constitution.md`) includes:

```markdown
# Project Constitution

## Principles
- Core values and beliefs
- Team commitments

## Quality Standards
- Code quality requirements
- Testing standards
- Documentation requirements

## Architectural Constraints
- Technology choices
- Design patterns
- System boundaries

## Decision Framework
- How decisions are made
- Escalation paths
- Consensus building

## Working Agreements
- Code review process
- Release cadence
- Communication norms
```

## Constitution Templates

| Template | Description |
|----------|-------------|
| `default` | Standard software project |
| `enterprise` | Compliance-focused |
| `startup` | Fast-moving, minimal process |
| `opensource` | Community-driven project |

## Examples

### View Constitution

```json
{
  "action": "get",
  "project_path": "."
}
```

### Create Enterprise Constitution

```json
{
  "action": "create",
  "project_path": ".",
  "template": "enterprise"
}
```

### Update Quality Standards

```json
{
  "action": "update",
  "project_path": ".",
  "section": "quality-standards",
  "content": "- All PRs require 2 approvals\n- No direct commits to main"
}
```

## Notes

- Constitution is the source of truth for project governance
- Review and update constitution as project evolves
- All team members should understand the constitution
- Use constitution to guide AI-assisted development

---

*For more information: `specify extension info specify-mcp`*
