---
description: "Initialize projects with spec-kit configuration and templates"
tools:
  - 'specify-mcp/initialize'
---

# Initialize Project

Set up a new or existing project with spec-kit configuration.

## Purpose

Initialize spec-kit in a project to enable:
- Specification-driven development workflow
- Constitution-based governance
- Structured feature management
- Progress tracking

## Prerequisites

1. Specify MCP server running
2. Target directory exists

## User Input

$ARGUMENTS

## Steps

### Step 1: Initialize Project

Set up spec-kit configuration:

Use MCP tool: `specify-mcp/initialize`

Parameters:
- `project_path`: Path to project root (default: current directory)
- `project_name`: Project name (optional, defaults to directory name)
- `template`: Project template (optional: "default", "minimal", "enterprise")

```json
{
  "project_path": "/path/to/project",
  "project_name": "my-awesome-project",
  "template": "default"
}
```

### Step 2: Review Generated Structure

The initialization creates:

```
project/
├── .specify/
│   ├── config.yml           # Project configuration
│   ├── constitution.md      # Project governance (if not exists)
│   └── scripts/             # Workflow scripts
│       └── update-agent-context.sh
├── specs/                   # Feature specifications directory
│   └── .gitkeep
└── templates/               # Custom templates (optional)
```

### Step 3: Configure Constitution

Edit the constitution to define project governance:

```bash
# Review generated constitution
cat .specify/constitution.md

# Customize for your project
# - Add coding standards
# - Define architectural constraints
# - Set quality gates
```

### Step 4: Verify Setup

Confirm initialization was successful:

```bash
ls -la .specify/
ls -la specs/
```

## Templates

| Template | Description |
|----------|-------------|
| `default` | Standard setup with all features |
| `minimal` | Basic configuration only |
| `enterprise` | Extended governance and compliance |

## Configuration Reference

The `.specify/config.yml` contains:

```yaml
project:
  name: "my-project"
  version: "0.1.0"

workflow:
  phases:
    - constitution
    - specify
    - clarify
    - plan
    - tasks
    - implement

templates:
  spec: "default"
  plan: "default"
```

## Examples

### Initialize Current Directory

```json
{
  "project_path": "."
}
```

### Initialize with Enterprise Template

```json
{
  "project_path": "/path/to/enterprise-project",
  "project_name": "Enterprise App",
  "template": "enterprise"
}
```

### Minimal Setup

```json
{
  "project_path": "./my-lib",
  "template": "minimal"
}
```

## Notes

- Re-running initialize preserves existing configuration
- Constitution is not overwritten if it exists
- Add `.specify/` to version control
- Use enterprise template for regulated industries

---

*For more information: `specify extension info specify-mcp`*
