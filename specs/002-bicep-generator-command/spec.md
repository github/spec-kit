# Feature Specification: Bicep Generator Command

**Feature Branch**: `002-bicep-generator-command`  
**Created**: 2025-10-21  
**Status**: Draft  
**Input**: User description: "I want to implement a new command for GitHub Copilot that will generate bicep templates to deploy Azure resources for a project, which can later on be used by another command to implement Ev2 deployment. It should use PowerShell scripts for things that can be done locally and the main functionality should be on a bicep generator MCP Server. The new command will be able to understand the current project and existing ARM/Bicep templates and ask smart questions to understand the architecture, regions where to deploy, etc to determine what type of resources the project requires to deploy and will come up with an .md file that will clearly explain the architecture and will create a bicep-templates folder that will contain all of the bicep-templates to be used by the next command that will use them to configure an Ev2 deployment."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Basic Bicep Templates from Project Analysis (Priority: P1)

A developer working on a new Azure project wants to generate the initial set of Bicep templates needed for deployment. They run the new command, answer a few questions about their project requirements (region, environment, scale), and receive a complete set of ready-to-use Bicep templates along with architectural documentation.

**Why this priority**: This is the core value proposition - automating the creation of deployment infrastructure from project analysis. Without this, users have no automation and must manually create all templates.

**Independent Test**: Can be fully tested by running the command on a sample project and verifying that syntactically correct Bicep templates are generated that match the project's resource requirements.

**Acceptance Scenarios**:

1. **Given** a project with application code but no existing Bicep templates, **When** the developer runs the bicep generator command, **Then** the system analyzes the project, asks relevant questions, and generates a complete set of Bicep templates with documentation
2. **Given** a project requiring common Azure resources (App Service, SQL Database, Storage), **When** the command analyzes the project, **Then** it generates appropriate Bicep templates for each identified resource type
3. **Given** the generated templates, **When** a developer attempts to deploy them, **Then** the templates execute without syntax errors and create the intended Azure resources

---

### User Story 2 - Update Existing Templates Based on Project Changes (Priority: P2)

A developer has an existing project with Bicep templates that were previously generated. After making changes to the application (adding new dependencies, changing storage requirements, etc.), they want to update only the affected Bicep templates rather than regenerating everything from scratch.

**Why this priority**: This provides ongoing value for existing projects and prevents the need to completely regenerate templates when only small changes are needed, saving time and reducing risk.

**Independent Test**: Can be tested by modifying a project with existing templates, running the update command, and verifying that only the relevant templates are modified while others remain unchanged.

**Acceptance Scenarios**:

1. **Given** an existing project with generated Bicep templates and recent code changes, **When** the developer runs the update command, **Then** the system identifies which Bicep templates need updates and modifies only those Bicep templates
2. **Given** a project where new Azure service dependencies have been added, **When** the update process runs, **Then** new Bicep templates are created for the additional services while existing Bicep templates are preserved
3. **Given** Bicep templates that are already up-to-date with the current project, **When** the update command runs, **Then** no changes are made and the user is informed that Bicep templates are current

---

### User Story 3 - Interactive Architecture Review and Optimization (Priority: P3)

An experienced developer wants to review and optimize the generated Bicep templates before deployment. The system provides an interactive review mode where it explains the architectural decisions, highlights potential improvements, and allows the developer to make informed adjustments to the Bicep templates.

**Why this priority**: This adds sophistication for advanced users but isn't essential for basic functionality. It provides value for complex projects or experienced developers who want more control.

**Independent Test**: Can be tested by generating templates, entering review mode, and verifying that the system provides meaningful architectural insights and allows template modifications.

**Acceptance Scenarios**:

1. **Given** generated Bicep templates, **When** the developer enters review mode, **Then** the system explains each architectural decision and provides optimization suggestions
2. **Given** a complex multi-service architecture, **When** reviewing the Bicep templates, **Then** the system identifies potential cost optimizations, security improvements, and scalability enhancements
3. **Given** developer feedback during review, **When** the developer accepts suggested changes, **Then** the Bicep templates are updated accordingly and validated for correctness

---

### Edge Cases

- What happens when the project has no clear indicators of required Azure services?
- How does the system handle conflicting requirements (e.g., high availability vs. cost optimization)?
- What occurs when existing Bicep templates have manual customizations that conflict with generated updates?
- How does the system respond to projects with mixed cloud dependencies (Azure + other clouds)?
- What happens when the Azure MCP Server is unavailable or returns errors?
- How does the system handle projects with deprecated Azure service dependencies?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST analyze all project files (code, configuration, documentation, scripts) to identify Azure service dependencies and requirements
- **FR-002**: System MUST generate syntactically correct Bicep templates that can be deployed without errors
- **FR-003**: System MUST create an architectural documentation file explaining the generated infrastructure and design decisions
- **FR-004**: System MUST ask intelligent questions to gather missing information about deployment requirements and generate parameterized templates with environment-specific parameter files (intelligent defined as: contextual to detected services, max 5 questions, provide reasonable defaults, avoid redundant information)
- **FR-005**: System MUST integrate with Azure MCP Server for Bicep template generation and validation
- **FR-006**: System MUST validate generated templates using Azure Resource Manager validation for syntax errors and resource compatibility
- **FR-007**: System MUST support incremental updates to existing templates without requiring full regeneration
- **FR-008**: System MUST organize generated templates in a resource type-based folder hierarchy (compute/, storage/, networking/, security/) suitable for Ev2 deployment
- **FR-009**: System MUST preserve manual customizations marked with special comments (e.g., // CUSTOM) and create backup files of original templates during updates
- **FR-010**: System MUST provide fallback specifications for creating a custom Bicep MCP Server when Azure MCP Server capabilities are insufficient
- **FR-011**: System MUST support common Azure resource types including App Services, Databases, Storage Accounts, Key Vaults, and Application Insights
- **FR-012**: System MUST generate templates that follow Azure best practices for security, naming conventions, and resource organization
- **FR-013**: System MUST generate environment-specific parameter files (dev.parameters.json, staging.parameters.json, prod.parameters.json) for parameterized templates

### Key Entities

- **Project Analysis**: Represents the analysis of existing project code, configuration files, and dependencies to understand Azure service requirements
- **Bicep Template**: Individual Bicep files representing specific Azure resources or resource groups with proper parameterization
- **Architecture Documentation**: Markdown file explaining the generated infrastructure, design decisions, and deployment guidance
- **Template Update Manifest**: Information about which templates have changed and why, used for incremental updates
- **Resource Requirement**: Identified need for specific Azure services based on project analysis (e.g., database, storage, compute)
- **Deployment Configuration**: Settings for target environment including region, subscription, resource naming patterns, and scaling requirements

## Clarifications

### Session 2025-10-21

- Q: How should Bicep templates be organized within the bicep-templates folder? → A: By resource type (compute/, storage/, networking/, security/)
- Q: What file types should the system analyze to identify Azure service requirements? → A: All project files including documentation and scripts
- Q: How should generated Bicep templates be validated before delivery? → A: ARM template validation using Azure Resource Manager
- Q: How should the system handle manual customizations in existing Bicep templates during updates? → A: Preserve changes marked with special comments and create backup files
- Q: How should the system handle multiple deployment environments (dev, staging, prod)? → A: Single parameterized templates with environment-specific parameter files

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can generate complete, deployable Bicep templates for a typical web application project in under 10 minutes including question answering
- **SC-002**: Generated Bicep templates have zero syntax errors and deploy successfully to Azure on first attempt in 90% of cases (success defined as: no deployment errors, all specified resources created, ARM validation passes)
- **SC-003**: Template updates complete in under 3 minutes and modify only the templates that actually need changes
- **SC-004**: System correctly identifies required Azure services for 95% of common project patterns (ASP.NET Core web apps, REST APIs, microservices with containers, console applications, Azure Functions)
- **SC-005**: Generated templates follow Azure Well-Architected Framework best practices as validated by Azure Advisor
- **SC-006**: Architectural documentation provides sufficient detail for developers unfamiliar with the project to understand the infrastructure design

