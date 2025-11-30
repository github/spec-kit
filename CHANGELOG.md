# Changelog

All notable changes to Spectrena will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-XX-XX

### Added

- **Core CLI Commands**
  - `spectrena init` - Project initialization with wizard
  - `spectrena discover` - Discovery phase document generation
  - `spectrena new` - Create new specs with configurable IDs
  - `spectrena plan-init` - Initialize implementation plans
  - `spectrena doctor` - Check dependencies
  - `spectrena update-context` - Sync CLAUDE.md with plans
  - `spectrena config` - View and migrate configuration

- **Worktree Management (`sw`)**
  - `sw list` - List spec branches
  - `sw ready` - Show unblocked specs
  - `sw create` - Create worktree
  - `sw open` - Open in terminal
  - `sw merge` - Merge and cleanup
  - `sw status` - Show active worktrees

- **Dependency Management (`sw dep`)**
  - `sw dep add` - Add dependency
  - `sw dep rm` - Remove dependency
  - `sw dep check` - Validate graph
  - `sw dep show` - Visualize (ASCII/Mermaid)
  - `sw dep sync` - Sync file ↔ database
  - Mermaid format for deps.mermaid

- **Lineage Tracking**
  - SurrealDB embedded backend (SurrealKV)
  - SQLite fallback option
  - Spec → Plan → Task → Code tracking
  - MCP server for Claude integration

- **MCP Integration**
  - `spectrena-mcp` server
  - Phase/task management tools
  - Dependency analysis tools
  - Serena integration for code change tracking

- **Slash Commands**
  - `/spectrena.specify` - Create specs
  - `/spectrena.clarify` - Refine specs
  - `/spectrena.plan` - Generate plans
  - `/spectrena.tasks` - Break into tasks
  - `/spectrena.deps` - Analyze dependencies

- **Configuration**
  - Configurable spec ID patterns
  - Per-component numbering
  - Late-binding format changes
  - Migration support

### Changed

- Forked from spec-kit
- Replaced bash/PowerShell scripts with pure Python
- Changed from `dependencies.txt` to `deps.mermaid`

### Technical

- Python 3.11+ required
- Built with Typer, Rich, GitPython
- SurrealDB for lineage (optional)
- 100% cross-platform (no shell scripts)

---

## Comparison with spec-kit

| Feature | spec-kit | Spectrena |
|---------|----------|-----------|
| Spec IDs | Fixed `NNN-slug` | Configurable patterns |
| Components | Not supported | Built-in |
| Discovery | Not supported | Phase -2 |
| Dependencies | Not tracked | Mermaid + DB |
| Lineage | Not tracked | Full traceability |
| Scripts | Bash + PowerShell | Pure Python |
| Windows | Via PowerShell | Native |

[Unreleased]: https://github.com/rghsoftware/spectrena/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/rghsoftware/spectrena/releases/tag/v0.1.0
