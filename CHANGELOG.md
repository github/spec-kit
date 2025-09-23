# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to the Spec Kit Azure DevOps extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.17] - 2025-09-22

### Added

- New `/clarify` command template to surface up to 5 targeted clarification questions for an existing spec and persist answers into a Clarifications section in the spec.
- New `/analyze` command template providing a non-destructive cross-artifact discrepancy and alignment report (spec, clarifications, plan, tasks, constitution) inserted after `/tasks` and before `/implement`.
	- Note: Constitution rules are explicitly treated as non-negotiable; any conflict is a CRITICAL finding requiring artifact remediation, not weakening of principles.

## [0.0.16] - 2025-09-22

### Added

- `--force` flag for `init` command to bypass confirmation when using `--here` in a non-empty directory and proceed with merging/overwriting files.

## [Unreleased]

### Added
- Initial release of Spec Kit Azure DevOps extension
- Project Hub with workflow orchestration (/specify → /plan → /tasks)
- Work Item Tab integration for AI-powered specification assistance
- Dashboard widgets for throughput, lead time, effort tracking, and guardrails monitoring
- LLM service connections with multi-provider support (OpenAI, Azure OpenAI, Anthropic)
- Pipeline tasks for repository seeding and workflow execution
- Comprehensive telemetry and audit trail functionality
- Security and compliance features with guardrails engine
- Cost tracking and usage monitoring
- Repository and wiki integration for artifact management

### Security
- Encrypted API key storage for LLM service connections
- OAuth integration with Azure DevOps permissions model
- Audit logging for all workflow executions and configuration changes
- Data privacy controls with optional anonymization

## [1.0.0] - 2024-01-XX

### Added
- **Project Hub**
  - Workflow execution interface with real-time progress tracking
  - Execution history with detailed metrics and cost tracking
  - Repository seeding with project constitution and best practices
  - Team dashboard with analytics and insights

- **Work Item Tab (Spec Assist)**
  - AI-powered specification generation from work item requirements
  - Implementation planning with dependency analysis and effort estimation
  - Task breakdown with automatic child work item creation
  - Artifact management with repository and wiki integration

- **Dashboard Widgets**
  - Throughput widget: Velocity tracking across specification workflows
  - Lead time widget: Time-to-delivery analytics with bottleneck identification
  - Effort widget: Resource allocation and estimation accuracy metrics
  - Guardrails widget: Compliance monitoring and quality gate tracking

- **LLM Service Connections**
  - Multi-provider support: OpenAI, Azure OpenAI, Anthropic, custom endpoints
  - Secure configuration with encrypted credential storage
  - Cost controls with per-user and per-project usage limits
  - Template management for customizable prompts

- **Pipeline Tasks**
  - SpecKitSeed: Automated repository initialization with project structure
  - SpecKitRun: Workflow execution within CI/CD pipelines
  - Integration with Azure DevOps work items and repositories

- **Core Services**
  - WorkflowOrchestrator: Central coordination of specification workflows
  - LLMService: AI provider abstraction and prompt management
  - RepositoryService: Git operations and artifact management
  - TelemetryService: Analytics, audit trails, and cost tracking

- **Security & Compliance**
  - Guardrails engine with configurable security and performance rules
  - Comprehensive audit trail for all user actions and system events
  - Data privacy controls with GDPR compliance features
  - Role-based access control integration with Azure DevOps

- **Developer Experience**
  - TypeScript-based architecture with comprehensive type definitions
  - Jest testing framework with 80%+ code coverage
  - Webpack build system with development and production configurations
  - Comprehensive documentation and contribution guidelines

### Technical Details
- Built with Azure DevOps Extension SDK 4.0.2
- TypeScript 5.0+ with strict type checking
- Webpack 5.88 for optimized bundling
- Jest 29.5 for comprehensive testing
- PowerShell Core for cross-platform pipeline tasks
- Azure DevOps REST API integration

### Supported Platforms
- Azure DevOps Services (cloud)
- Azure DevOps Server 2022+ (on-premises)
- Cross-platform pipeline tasks (Windows, Linux, macOS)

### Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Dependencies
- Node.js 18.0+
- Azure DevOps organization with appropriate permissions
- LLM service provider account (OpenAI, Azure OpenAI, etc.)

---

## Version History Guidelines

### Version Numbering
- **Major (X.0.0)**: Breaking changes, major new features, architectural changes
- **Minor (1.X.0)**: New features, enhancements, non-breaking changes
- **Patch (1.0.X)**: Bug fixes, security updates, minor improvements

### Change Categories
- **Added**: New features, capabilities, or enhancements
- **Changed**: Changes to existing functionality
- **Deprecated**: Features that will be removed in future versions
- **Removed**: Features that have been removed
- **Fixed**: Bug fixes and error corrections
- **Security**: Security-related fixes and improvements

### Release Notes Format
Each release includes:
- Summary of major changes and new features
- Migration guide for breaking changes
- Known issues and workarounds
- Performance improvements and optimizations
- Security updates and compliance enhancements

### Support Policy
- **Current version (1.x)**: Full support with bug fixes and security updates
- **Previous major version**: Security updates only for 12 months
- **Older versions**: Community support through GitHub issues

### Roadmap Preview
Upcoming features and improvements:
- Advanced analytics with predictive insights
- Multi-language prompt template support
- Enhanced cost optimization algorithms
- Real-time collaboration features
- Custom workflow designer
- Enterprise-grade audit and compliance enhancements