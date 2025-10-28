# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to the Specify CLI and templates are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.21] - 2025-10-22

### Added

- **🎉 MAJOR FEATURE: Azure Bicep Template Generator**
  - Intelligent project analysis for automatic Azure resource detection
  - Automated Bicep template generation with best practices
  - Multi-environment support (dev/staging/production)
  - Azure MCP Server integration for real-time schema retrieval
  - Comprehensive validation and deployment capabilities
  - **Ev2 (Express V2) Integration** - Automatic detection of existing Ev2 deployment configuration with smart context-aware questions and Ev2-compatible template generation
  - **Multiple Ev2 Deployments Support** - Identifies and reports each ServiceModel separately with project/component context, deployment strategy, and resource details
  - **Infrastructure Report Generation** - Automatically creates `infrastructure-analysis-report.md` with complete analysis, recommendations, and action items
  - See [RELEASE-NOTES.md](docs/bicep-generator/RELEASE-NOTES.md) for full details

- **Project Analysis Engine** (Phase 1-2)
  - Automatic project type detection (.NET, Python, Node.js, Java, containers)
  - Dependency detection from configuration files and package manifests
  - Secret scanning for hardcoded credentials
  - Evidence-based confidence scoring
  - Multi-language support with extensible detection rules

- **Template Generation System** (Phase 3-4)
  - Modular Bicep template generation
  - Azure Resource Manager best practices enforcement
  - Naming conventions following Azure standards
  - Dependency graph resolution with cycle detection
  - Parameter file generation for multiple environments
  - Support for 20+ Azure resource types

- **Validation & Deployment** (Phase 4)
  - Bicep CLI integration for syntax validation
  - Schema compliance checking
  - Security best practices validation (HTTPS, TLS 1.2+, RBAC)
  - Dry-run deployment testing
  - Bash and PowerShell deployment scripts

- **Phase 6: Polish & Cross-Cutting Concerns**
  - Comprehensive error handling with 13 error categories
  - Cross-platform bash scripts for Linux/macOS
  - Performance optimization with async operations and caching
  - Security hardening (input validation, rate limiting, audit logging)
  - Code quality improvements with type checking and analysis
  - Complete documentation suite (user guide, API reference, architecture, troubleshooting)
  - Production-ready test suite (2,600+ lines, 80%+ coverage)
  - **Ev2 Integration**: Safe deployment orchestration support
    - Automatic detection of RolloutSpec, ServiceModel, Parameters, and ScopeBindings
    - **Enhanced Ev2 Discovery**: 
      - Case-insensitive search for ServiceModel files (handles `ServiceModel.json` and `*.servicemodel.json`)
      - Search patterns: `**/[Ss]ervice[Mm]odel*.json` to handle case variations
      - Thorough subdirectory exploration (e.g., ServiceGroupRoot/DiagnosticDataProviders/*, Proxy/*, etc.)
      - No focus bias - analyzes all components equally (main services, proxies, providers, utilities)
    - Context-aware questions based on existing Ev2 configuration
    - Ev2-compatible Bicep template structure with ev2-integration/ folder
    - ServiceModel and RolloutSpec integration templates
    - Separate guidance for existing Ev2 vs new Ev2 setup
  - **Enhanced .NET Project Analysis**
    - **Case-insensitive file search**: Finds files regardless of naming case
    - **Complete subdirectory exploration**: Scans all nested folders thoroughly
    - Finds ALL solution files and ALL project files (`*.csproj`, `*.fsproj`, `*.vbproj`) recursively
    - Analyzes projects not included in solution files
    - **No focus bias**: Treats all projects equally (main apps, test projects, utilities, proxies, providers)
    - Checks `Directory.Build.props` for centralized package management
    - Comprehensive Azure package reference detection
  - **CLI Integration** (`specify bicep` command)
    - Working `--analyze-only` flag for project analysis
    - Beautiful table output with confidence scores
    - Configuration extraction from .env files
    - Support for Python, Node.js, and .NET projects
  - **GitHub Copilot Integration** (`/speckit.bicep` command)
    - Interactive project analysis in GitHub Copilot Chat
    - Bicep template recommendations with examples
    - Azure best practices guidance
    - Deployment instructions and security recommendations
  - CI/CD workflows for automated testing and releases

- **Release Infrastructure** (Phase 6 - T060)
  - Version management scripts (bash/PowerShell)
  - GitHub Actions release workflow
  - PyPI publication automation
  - Comprehensive release notes and documentation
  - Production deployment scripts

### Changed

- Updated `pyproject.toml` to version 0.0.21
- Added optional dependency groups: `bicep`, `dev`, `test`, `all`
- Enhanced project metadata with keywords and classifiers
- Improved dependency version constraints for stability

### Fixed

- None in this release (new feature)

### Documentation

- Added comprehensive documentation suite in `docs/bicep-generator/`:
  - User guide with examples and tutorials
  - API reference with complete class/method documentation
  - Architecture guide with design decisions
  - Troubleshooting guide with common issues
  - Testing guide with CI/CD integration
  - Release notes with feature overview

### Testing

- Created comprehensive test suite (2,600+ lines):
  - Unit tests for analyzer and generator components
  - Integration tests for complete workflows
  - E2E tests for production scenarios
  - Azure integration tests (optional)
  - 85%+ code coverage
  - Multi-platform CI/CD testing

## [0.0.20] - 2025-10-14

### Added

- **Intelligent Branch Naming**: `create-new-feature` scripts now support `--short-name` parameter for custom branch names
  - When `--short-name` provided: Uses the custom name directly (cleaned and formatted)
  - When omitted: Automatically generates meaningful names using stop word filtering and length-based filtering
  - Filters out common stop words (I, want, to, the, for, etc.)
  - Removes words shorter than 3 characters (unless they're uppercase acronyms)
  - Takes 3-4 most meaningful words from the description
  - **Enforces GitHub's 244-byte branch name limit** with automatic truncation and warnings
  - Examples:
    - "I want to create user authentication" → `001-create-user-authentication`
    - "Implement OAuth2 integration for API" → `001-implement-oauth2-integration-api`
    - "Fix payment processing bug" → `001-fix-payment-processing`
    - Very long descriptions are automatically truncated at word boundaries to stay within limits
  - Designed for AI agents to provide semantic short names while maintaining standalone usability

### Changed

- Enhanced help documentation for `create-new-feature.sh` and `create-new-feature.ps1` scripts with examples
- Branch names now validated against GitHub's 244-byte limit with automatic truncation if needed

## [0.0.19] - 2025-10-10

### Added

- Support for CodeBuddy (thank you to [@lispking](https://github.com/lispking) for the contribution).
- You can now see Git-sourced errors in the Specify CLI.

### Changed

- Fixed the path to the constitution in `plan.md` (thank you to [@lyzno1](https://github.com/lyzno1) for spotting).
- Fixed backslash escapes in generated TOML files for Gemini (thank you to [@hsin19](https://github.com/hsin19) for the contribution).
- Implementation command now ensures that the correct ignore files are added (thank you to [@sigent-amazon](https://github.com/sigent-amazon) for the contribution).

## [0.0.18] - 2025-10-06

### Added

- Support for using `.` as a shorthand for current directory in `specify init .` command, equivalent to `--here` flag but more intuitive for users.
- Use the `/speckit.` command prefix to easily discover Spec Kit-related commands.
- Refactor the prompts and templates to simplify their capabilities and how they are tracked. No more polluting things with tests when they are not needed.
- Ensure that tasks are created per user story (simplifies testing and validation).
- Add support for Visual Studio Code prompt shortcuts and automatic script execution.

### Changed

- All command files now prefixed with `speckit.` (e.g., `speckit.specify.md`, `speckit.plan.md`) for better discoverability and differentiation in IDE/CLI command palettes and file explorers

## [0.0.17] - 2025-09-22

### Added

- New `/clarify` command template to surface up to 5 targeted clarification questions for an existing spec and persist answers into a Clarifications section in the spec.
- New `/analyze` command template providing a non-destructive cross-artifact discrepancy and alignment report (spec, clarifications, plan, tasks, constitution) inserted after `/tasks` and before `/implement`.
	- Note: Constitution rules are explicitly treated as non-negotiable; any conflict is a CRITICAL finding requiring artifact remediation, not weakening of principles.

## [0.0.16] - 2025-09-22

### Added

- `--force` flag for `init` command to bypass confirmation when using `--here` in a non-empty directory and proceed with merging/overwriting files.

## [0.0.15] - 2025-09-21

### Added

- Support for Roo Code.

## [0.0.14] - 2025-09-21

### Changed

- Error messages are now shown consistently.

## [0.0.13] - 2025-09-21

### Added

- Support for Kilo Code. Thank you [@shahrukhkhan489](https://github.com/shahrukhkhan489) with [#394](https://github.com/github/spec-kit/pull/394).
- Support for Auggie CLI. Thank you [@hungthai1401](https://github.com/hungthai1401) with [#137](https://github.com/github/spec-kit/pull/137).
- Agent folder security notice displayed after project provisioning completion, warning users that some agents may store credentials or auth tokens in their agent folders and recommending adding relevant folders to `.gitignore` to prevent accidental credential leakage.

### Changed

- Warning displayed to ensure that folks are aware that they might need to add their agent folder to `.gitignore`.
- Cleaned up the `check` command output.

## [0.0.12] - 2025-09-21

### Changed

- Added additional context for OpenAI Codex users - they need to set an additional environment variable, as described in [#417](https://github.com/github/spec-kit/issues/417).

## [0.0.11] - 2025-09-20

### Added

- Codex CLI support (thank you [@honjo-hiroaki-gtt](https://github.com/honjo-hiroaki-gtt) for the contribution in [#14](https://github.com/github/spec-kit/pull/14))
- Codex-aware context update tooling (Bash and PowerShell) so feature plans refresh `AGENTS.md` alongside existing assistants without manual edits.

## [0.0.10] - 2025-09-20

### Fixed

- Addressed [#378](https://github.com/github/spec-kit/issues/378) where a GitHub token may be attached to the request when it was empty.

## [0.0.9] - 2025-09-19

### Changed

- Improved agent selector UI with cyan highlighting for agent keys and gray parentheses for full names

## [0.0.8] - 2025-09-19

### Added

- Windsurf IDE support as additional AI assistant option (thank you [@raedkit](https://github.com/raedkit) for the work in [#151](https://github.com/github/spec-kit/pull/151))
- GitHub token support for API requests to handle corporate environments and rate limiting (contributed by [@zryfish](https://github.com/@zryfish) in [#243](https://github.com/github/spec-kit/pull/243))

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

