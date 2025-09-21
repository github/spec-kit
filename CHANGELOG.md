# Changelog

All notable changes to the Specify CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.11] - 2025-09-20

### Added

- **Orchestrated Workflows**: New automated workflows for feature development and MVP to full product transition
  - `execute-feature-workflow.sh/ps1` scripts for end-to-end feature development automation
  - `mvp-to-full.sh/ps1` scripts for seamless MVP to full product orchestration
  - Project state analysis capabilities to determine greenfield vs brownfield projects
- **Enhanced Resumption Capabilities**: Comprehensive analysis and resumption tools for interrupted development
  - `analyze-spec-completion.sh/ps1` scripts for detailed project state assessment
  - `generate-resumption-instructions.sh/ps1` for intelligent continuation guidance
  - Enhanced `docs/resumable-execution.md` with detailed resumption strategies
- **GitHub Copilot Integration Enhancements**: Improved context instructions and agent documentation
  - New `agent_templates/copilot/copilot-instructions.md` template for better Copilot integration
  - Enhanced agent documentation in `AGENTS.md` with comprehensive integration guidelines
- **MVP Transition Templates**: New template system for MVP planning and execution
  - `templates/mvp-plan-template.md` for structured MVP planning
  - `templates/commands/mvp-to-full.md` command template for transition workflows
- Codex CLI support (thank you [@honjo-hiroaki-gtt](https://github.com/honjo-hiroaki-gtt) for the contribution in [#14](https://github.com/guercheLE/spec-kit/pull/14))
- Codex-aware context update tooling (Bash and PowerShell) so feature plans refresh `AGENTS.md` alongside existing assistants without manual edits.

### Enhanced

- **Multi-AI Assistant Documentation**: Expanded `docs/multiple-ai-assistants.md` with comprehensive workflow guidance
- **Task Templates**: Enhanced task management templates with better structure and automation support
- **CLI Capabilities**: Improved CLI with enhanced project analysis and workflow orchestration features

## [0.0.10] - 2025-09-20

### Fixed

- Addressed [#378](https://github.com/guercheLE/spec-kit/issues/378) where a GitHub token may be attached to the request when it was empty.

## [0.0.9] - 2025-09-19

### Changed

- Improved agent selector UI with cyan highlighting for agent keys and gray parentheses for full names

## [0.0.8] - 2025-09-19

### Added

- Windsurf IDE support as additional AI assistant option (thank you [@raedkit](https://github.com/raedkit) for the work in [#151](https://github.com/guercheLE/spec-kit/pull/151))
- GitHub token support for API requests to handle corporate environments and rate limiting (contributed by [@zryfish](https://github.com/@zryfish) in [#243](https://github.com/guercheLE/spec-kit/pull/243))

### Changed

- Updated README with Windsurf examples and GitHub token usage
- Enhanced release workflow to include Windsurf templates

## [0.0.7] - 2025-09-18

### Changed

- Updated command instructions in the CLI.
- Cleaned up the code to not render agent-specific information when it's generic.


## [0.0.6] - 2025-09-17

### Added

- opencode support as additional AI assistant option

## [0.0.5] - 2025-09-17

### Added

- Qwen Code support as additional AI assistant option

## [0.0.4] - 2025-09-14

### Added

- SOCKS proxy support for corporate environments via `httpx[socks]` dependency

### Fixed

N/A

### Changed

N/A
