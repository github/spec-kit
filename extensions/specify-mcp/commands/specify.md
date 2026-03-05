---
description: "Create feature specifications from natural language descriptions"
tools:
  - 'specify-mcp/specify'
  - 'specify-mcp/get_context'
  - 'specify-mcp/constitution'
---

# Create Feature Specification

Generate structured feature specifications from natural language descriptions.

## Purpose

Transform natural language feature ideas into structured specifications with:
- Clear requirements and acceptance criteria
- User stories and use cases
- Technical constraints and dependencies
- Success metrics and validation criteria

## Prerequisites

1. Specify MCP server running
2. Project initialized with spec-kit configuration
3. Constitution defined (optional but recommended)

## User Input

$ARGUMENTS

## Steps

### Step 1: Get Current Context

Understand current project state:

Use MCP tool: `specify-mcp/get_context`

Parameters:
- `phase`: "specify"
- `project_path`: Current project path (optional)

### Step 2: Review Constitution (Optional)

Check project governance rules:

Use MCP tool: `specify-mcp/constitution`

Parameters:
- `action`: "get"
- `project_path`: Current project path

### Step 3: Create Specification

Generate the feature specification:

Use MCP tool: `specify-mcp/specify`

Parameters:
- `description`: Natural language feature description
- `project_path`: Project root path
- `feature_name`: Short feature identifier (optional)
- `template`: Specification template (optional)

```json
{
  "description": "User authentication with OAuth2 support including Google and GitHub providers",
  "project_path": "/path/to/project",
  "feature_name": "oauth-authentication"
}
```

### Step 4: Review Generated Specification

The tool generates `specs/{feature-id}/spec.md` containing:

- **Overview**: Feature summary and objectives
- **Requirements**: Functional and non-functional requirements
- **User Stories**: Formatted as "As a... I want... So that..."
- **Acceptance Criteria**: Testable conditions
- **Constraints**: Technical and business limitations
- **Dependencies**: External systems and features

### Step 5: Refine Specification

Iterate on the specification:

```bash
# Review generated spec
cat specs/001-oauth-authentication/spec.md

# Manually refine as needed
# The spec serves as the source of truth for planning
```

## Output Structure

```
specs/
└── 001-{feature-name}/
    ├── spec.md           # Main specification
    └── .meta/            # Metadata (auto-generated)
```

## Configuration Reference

- **workflow.track_progress**: Track specification progress
  - Type: boolean
  - Default: `true`

## Examples

### Simple Feature

```json
{
  "description": "Add dark mode theme support to the dashboard",
  "project_path": "."
}
```

### Complex Feature

```json
{
  "description": "Implement a real-time notification system with WebSocket support, including notification preferences, read/unread status, and email digest for offline users",
  "project_path": ".",
  "feature_name": "realtime-notifications"
}
```

## Notes

- Start with clear, concise descriptions
- Include user perspective when possible
- Mention any known constraints upfront
- The specification can be refined iteratively

---

*For more information: `specify extension info specify-mcp`*
