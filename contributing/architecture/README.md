# Architecture Documentation

Implementation details and design decisions for Spec Kit.

## Multi-Repository Support

- **[Multi-Repo Implementation](./multi-repo-implementation.md)** - How multi-repo workspaces work internally
- **[Multi-Repo Modes Comparison](./multi-repo-modes-comparison.md)** - Batch mode vs workspace mode
- **[Multi-Repo Testing](./multi-repo-testing.md)** - Testing strategies for multi-repo features

## Core Architecture

### CLI Architecture

The `specify` CLI is built with Python and Typer, providing:
- Cross-platform support (Windows, macOS, Linux)
- Script generation (bash and PowerShell)
- Template management and distribution
- Git repository initialization

### Template System

Templates are distributed as part of the package and extracted during initialization:
- Spec templates (standard, lightweight, quick)
- Plan templates (standard, lightweight)
- Command templates for AI agents
- Custom template support

### Script System

Dual-script system supporting both platforms:
- **Bash scripts** (`.sh`) for Unix-like systems
- **PowerShell scripts** (`.ps1`) for Windows and cross-platform

Scripts handle:
- Feature creation and branching
- Path resolution (workspace vs single-repo)
- Git operations
- Template processing

### Multi-Repo Workspace Architecture

Workspaces provide centralized spec management:
- Single `.specify/workspace.yml` configuration
- Convention-based routing to target repos
- Per-repo Jira requirements
- Shared specifications across repos

## Design Decisions

### Why Python for CLI?

- Cross-platform compatibility
- Rich ecosystem (typer, rich, httpx)
- Easy distribution (pip, uv, uvx)
- Good template/file management libraries

### Why Dual Scripts (Bash + PowerShell)?

- Native support for Unix and Windows users
- Better performance than cross-platform alternatives
- Leverage platform-specific capabilities
- Maintain user experience on each platform

### Why Convention-Based Routing?

- Reduces configuration burden
- Intuitive for developers
- Customizable when needed
- Scales well for multiple repos

## Implementation Notes

See individual architecture documents for detailed implementation information.

## Contributing

When making architectural changes:
1. Document the rationale
2. Update affected architecture docs
3. Add tests for new behavior
4. Update user-facing guides if needed

## Related

- [Development Setup](../development-setup.md) - Setting up for development
- [User Documentation](../../docs/) - User-facing docs
