# Changelog

All notable changes to the Specify MCP extension are documented here.

## [1.0.0] - 2025-02-12

### Added

- Initial release of Specify MCP extension
- Commands for full spec-kit workflow:
  - `analyze-domain` - Extract business entities from data files
  - `specify` - Create feature specifications
  - `plan` - Generate implementation plans
  - `tasks` - Break down into structured tasks
  - `initialize` - Set up project configuration
  - `constitution` - Manage project governance
  - `validate` - Cross-artifact consistency checking
- Configuration template with analysis and workflow settings
- Hook for automatic validation after task generation
- Short command aliases (e.g., `/speckit.specify`)
- Multi-agent support for Claude, Gemini, Copilot, etc.
- Environment variable configuration overrides
