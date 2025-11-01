# Reference Documentation

Technical reference for commands, templates, configuration, and APIs.

## Quick Links

- **[Specify CLI Reference](./cli-commands.md)** - `specify` command options and flags
- **[Slash Commands](./slash-commands.md)** - `/specify`, `/plan`, `/tasks`, `/implement`, etc.
- **[Template Reference](./templates.md)** - Available templates and their structure
- **[Configuration](./configuration.md)** - `.specify/` directory structure and config files
- **[Workspace Configuration](./workspace-config.md)** - `workspace.yml` reference for multi-repo
- **[API Contracts](./api-contracts.md)** - API endpoint specifications from plans

## By Audience

### For Users Getting Started
- [CLI Commands](./cli-commands.md) - How to use `specify init`
- [Slash Commands](./slash-commands.md) - How to use `/specify`, `/plan`, etc.

### For Understanding Project Structure
- [Configuration](./configuration.md) - What gets created in `.specify/`
- [Templates](./templates.md) - What's in template files

### For Multi-Repo Projects
- [Workspace Configuration](./workspace-config.md) - `workspace.yml` format and options

### For Developers
- [API Contracts](./api-contracts.md) - API specifications from implementation plans

## Command Reference

### Installation
```bash
specify init [project-name] [OPTIONS]
```

See [CLI Commands](./cli-commands.md) for full reference.

### Specification
```bash
/specify [description]
```

Creates or updates feature specification. See [Slash Commands](./slash-commands.md).

### Planning
```bash
/plan [tech stack description]
/plan --capability cap-001
```

Creates or updates implementation plan. See [Slash Commands](./slash-commands.md).

### Task Breakdown
```bash
/tasks
```

Generates actionable task list. See [Slash Commands](./slash-commands.md).

### Implementation
```bash
implement specs/[feature-id]/plan.md
```

Executes implementation plan. See [Slash Commands](./slash-commands.md).

## Common Tasks

**How do I...?**

- [Find my specifications](./configuration.md) - Look in `specs/` directory
- [Understand my project structure](./configuration.md) - See what's in `.specify/`
- [Configure for my team](./configuration.md) - Update `.specify/` settings
- [Set up multi-repo](./workspace-config.md) - Configure `workspace.yml`
- [Understand a feature's architecture](./api-contracts.md) - Read the implementation plan

## File Formats

### Specification Format
- File: `specs/[feature-id]/spec.md`
- Structure: [Templates](./templates.md)
- Contents: Requirements, constraints, acceptance criteria

### Implementation Plan Format
- File: `specs/[feature-id]/plan.md`
- Structure: [Templates](./templates.md)
- Contents: Architecture, technology choices, data models

### Configuration Format
- File: `.specify/config.yml` (project-level)
- File: `workspace.yml` (workspace-level)
- See: [Configuration](./configuration.md) and [Workspace Config](./workspace-config.md)

## Examples

- [Example Specification](./examples/example-spec.md)
- [Example Implementation Plan](./examples/example-plan.md)
- [Example Workspace Config](./examples/example-workspace.yml)

## Troubleshooting

**Q: Where do my specs live?**
A: In `specs/` directory at repo or workspace root. See [Configuration](./configuration.md).

**Q: How do I customize templates?**
A: Place custom templates in `.specify/templates/`. See [Templates](./templates.md).

**Q: How do I set up multiple repos?**
A: Create `workspace.yml`. See [Workspace Configuration](./workspace-config.md).

**Q: What's the exact format for acceptance criteria?**
A: See the specification template in [Templates](./templates.md).

## Related

- **Learn concepts**: [Concepts](../concepts/)
- **Step-by-step guides**: [Guides](../guides/)
- **Getting started**: [Getting Started](../getting-started/)
