---
description: "Generate detailed implementation plans from specifications"
tools:
  - 'specify-mcp/plan'
  - 'specify-mcp/get_context'
---

# Generate Implementation Plan

Create detailed technical implementation plans from feature specifications.

## Purpose

Transform specifications into actionable implementation plans:
- Technical approach and architecture decisions
- Component breakdown and responsibilities
- API contracts and data models
- Implementation phases and milestones

## Prerequisites

1. Feature specification exists in `specs/{feature-id}/spec.md`
2. Specify MCP server running
3. Domain analysis complete (if applicable)

## User Input

$ARGUMENTS

## Steps

### Step 1: Get Current Context

Understand current planning state:

Use MCP tool: `specify-mcp/get_context`

Parameters:
- `phase`: "plan"
- `project_path`: Current project path

### Step 2: Generate Implementation Plan

Create the technical plan:

Use MCP tool: `specify-mcp/plan`

Parameters:
- `spec_path`: Path to specification file
- `project_path`: Project root path
- `include_research`: Include technology research (default: true)
- `include_data_model`: Include data model design (default: true)

```json
{
  "spec_path": "specs/001-oauth-authentication/spec.md",
  "project_path": ".",
  "include_research": true,
  "include_data_model": true
}
```

### Step 3: Review Generated Plan

The tool generates in `specs/{feature-id}/`:

**plan.md** - Implementation plan containing:
- **Technical Approach**: Architecture and design patterns
- **Component Breakdown**: Modules and their responsibilities
- **API Contracts**: Endpoint definitions and schemas
- **Data Models**: Entity relationships and storage
- **Implementation Phases**: Ordered delivery milestones

**research.md** (if enabled):
- Technology options and trade-offs
- Library and framework recommendations
- Integration considerations

**data-model.md** (if enabled):
- Entity definitions
- Relationships and cardinality
- Database schema suggestions

### Step 4: Validate Plan

Ensure plan aligns with specification:

```bash
# Review generated files
ls specs/001-oauth-authentication/
cat specs/001-oauth-authentication/plan.md
```

## Output Structure

```
specs/
└── 001-{feature-name}/
    ├── spec.md           # Input specification
    ├── plan.md           # Generated implementation plan
    ├── research.md       # Technology research (optional)
    └── data-model.md     # Data model design (optional)
```

## Examples

### Basic Planning

```json
{
  "spec_path": "specs/001-dark-mode/spec.md",
  "project_path": "."
}
```

### Full Planning with Research

```json
{
  "spec_path": "specs/002-notification-system/spec.md",
  "project_path": ".",
  "include_research": true,
  "include_data_model": true
}
```

## Notes

- Plans are living documents - update as you learn
- Include domain analysis results for data-rich features
- Review research.md for technology decisions
- Use data-model.md as starting point for schema design

---

*For more information: `specify extension info specify-mcp`*
