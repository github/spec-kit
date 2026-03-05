# Specify MCP Extension

Integrate the [specify-mcp](https://github.com/jlwainwright/specify-mcp) server with spec-kit for enhanced specification-driven development and domain analysis.

## Features

- **Domain Analysis**: Extract business entities and rules from JSON/CSV data files
- **Specification Generation**: Create structured specs from natural language
- **Implementation Planning**: Generate technical plans from specifications
- **Task Breakdown**: Create dependency-aware task lists
- **Constitution Management**: Define and enforce project governance
- **Validation**: Cross-artifact consistency and compliance checking

## Installation

### Prerequisites

1. Specify MCP server installed and configured
2. Spec Kit v0.1.0 or higher

### Install Extension

```bash
# From spec-kit extensions directory
specify extension add --dev /path/to/spec-kit/extensions/specify-mcp

# Or install from URL (when published)
specify extension add specify-mcp
```

### Configure MCP Server

Add to your AI agent's MCP configuration:

```json
{
  "mcpServers": {
    "specify-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/specify-mcp", "run", "speckit_mcp"]
    }
  }
}
```

## Commands

| Command | Description |
|---------|-------------|
| `/speckit.specify-mcp.analyze-domain` | Extract entities from data files |
| `/speckit.specify-mcp.specify` | Create feature specification |
| `/speckit.specify-mcp.plan` | Generate implementation plan |
| `/speckit.specify-mcp.tasks` | Break down into tasks |
| `/speckit.specify-mcp.initialize` | Initialize project |
| `/speckit.specify-mcp.constitution` | Manage governance |
| `/speckit.specify-mcp.validate` | Validate consistency |

### Aliases

Short aliases are available:
- `/speckit.analyze-domain`
- `/speckit.specify`
- `/speckit.plan`
- `/speckit.tasks`
- `/speckit.initialize`
- `/speckit.constitution`
- `/speckit.validate`

## Workflow

```
1. /speckit.initialize          → Set up project
2. /speckit.constitution        → Define governance
3. /speckit.analyze-domain      → Extract domain model (optional)
4. /speckit.specify             → Create specification
5. /speckit.plan                → Generate plan
6. /speckit.tasks               → Break down tasks
7. /speckit.validate            → Check consistency
```

## Configuration

Edit `.specify/extensions/specify-mcp/specify-mcp-config.yml`:

```yaml
analysis:
  domain_templates: [financial, ecommerce, crm]
  validation_strict: false

workflow:
  auto_validate: false
  track_progress: true
  default_granularity: fine

specification:
  include_research: true
  include_data_model: true
```

### Environment Variables

Override configuration with:
- `SPECKIT_SPECIFY_MCP_DOMAIN_TEMPLATES`
- `SPECKIT_SPECIFY_MCP_VALIDATION_STRICT`
- `SPECKIT_SPECIFY_MCP_AUTO_VALIDATE`

## Hooks

The extension provides a hook that runs after task generation:

- **after_tasks**: Prompts to run `/speckit.validate` for consistency checking

## Examples

### Analyze Financial Data

```
/speckit.analyze-domain

User provides:
{
  "data_path": "./sample-data/financial/",
  "domain_type": "financial"
}
```

### Create Feature Specification

```
/speckit.specify

User provides:
{
  "description": "Add user authentication with OAuth2 support",
  "project_path": "."
}
```

### Generate Tasks

```
/speckit.tasks

User provides:
{
  "plan_path": "specs/001-auth/spec.md",
  "granularity": "fine"
}
```

## Requirements

- **specify-mcp** MCP server v0.0.52 or higher
- **spec-kit** CLI v0.1.0 or higher

## License

MIT

## Links

- [Specify MCP Server](https://github.com/jlwainwright/specify-mcp)
- [Spec Kit](https://github.com/github/spec-kit)
- [MCP Protocol](https://modelcontextprotocol.io)
