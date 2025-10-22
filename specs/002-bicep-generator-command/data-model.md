# Data Model: Bicep Generator Command

**Feature**: 002-bicep-generator-command  
**Date**: 2025-10-21  
**Phase**: 1 - Design & Data Modeling

## Core Entities

### Project Analysis

Represents the comprehensive analysis of a project to determine Azure service requirements.

**Attributes**:
- `project_path`: string - Absolute path to the project root directory
- `analysis_timestamp`: datetime - When the analysis was performed
- `file_count`: integer - Total number of files analyzed
- `detected_services`: array[ResourceRequirement] - List of identified Azure services
- `configuration_files`: array[string] - Paths to configuration files found
- `documentation_files`: array[string] - Paths to documentation files analyzed
- `script_files`: array[string] - Paths to script files analyzed
- `analysis_confidence`: float - Confidence score (0.0-1.0) in the analysis results

**Validation Rules**:
- `project_path` must exist and be readable
- `analysis_timestamp` cannot be in the future
- `file_count` must be greater than 0
- `analysis_confidence` must be between 0.0 and 1.0
- `detected_services` must contain at least one service for successful analysis

**Relationships**:
- Contains multiple `ResourceRequirement` instances
- Associated with one `DeploymentConfiguration`
- May reference existing `BicepTemplate` instances during updates

### Resource Requirement

Represents an identified need for a specific Azure service based on project analysis.

**Attributes**:
- `service_type`: string - Azure resource type (e.g., "Microsoft.Storage/storageAccounts")
- `confidence_level`: float - Confidence in requirement detection (0.0-1.0)
- `evidence_files`: array[string] - Files that indicated this requirement
- `required_features`: array[string] - Specific features needed for this service
- `scale_indicators`: object - Detected scale requirements (connections, storage, etc.)
- `dependencies`: array[string] - Other Azure services this depends on
- `environment_specific`: boolean - Whether requirements differ per environment

**Validation Rules**:
- `service_type` must be valid Azure resource type format
- `confidence_level` must be between 0.0 and 1.0
- `evidence_files` must contain at least one valid file path
- `required_features` cannot be empty
- All dependency service types must be valid Azure resource types

**State Transitions**:
- `Detected` → `Validated` (after schema retrieval)
- `Validated` → `Templated` (after Bicep template generation)
- `Templated` → `Deployed` (after successful ARM validation)

**Relationships**:
- Belongs to one `ProjectAnalysis`
- Generates one or more `BicepTemplate` instances
- May be referenced by other `ResourceRequirement` dependencies

### Bicep Template

Individual Bicep file representing specific Azure resources with proper parameterization.

**Attributes**:
- `template_path`: string - Relative path within bicep-templates folder
- `resource_type`: string - Primary Azure resource type this template creates
- `template_content`: string - The actual Bicep template content
- `parameters`: array[TemplateParameter] - Template parameters definition
- `api_version`: string - Azure API version used in template
- `dependencies`: array[string] - Other templates this depends on
- `validation_status`: enum[Valid, Invalid, Warning, NotValidated]
- `validation_errors`: array[string] - Any validation errors or warnings
- `custom_markers`: array[string] - Lines marked with // CUSTOM comments
- `backup_path`: string - Path to backup file if template was updated
- `last_modified`: datetime - When template was last generated or updated

**Validation Rules**:
- `template_path` must follow resource type organization structure
- `resource_type` must be valid Azure format
- `template_content` must be valid Bicep syntax
- `api_version` must be current Azure API version
- `validation_status` must be Valid before deployment
- `parameters` must include all required parameters for resource type

**State Transitions**:
- `Generated` → `Validating` (during validation process)
- `Validating` → `Valid|Invalid|Warning` (after validation)
- `Valid` → `Ready` (ready for deployment)
- `Valid` → `Updating` (during incremental updates)

**Relationships**:
- Generated from one `ResourceRequirement`
- Associated with multiple `ParameterFile` instances
- May reference other `BicepTemplate` dependencies

### Template Parameter

Represents a parameter definition within a Bicep template.

**Attributes**:
- `name`: string - Parameter name
- `type`: string - Bicep parameter type (string, int, bool, object, array)
- `description`: string - Human-readable parameter description
- `default_value`: any - Default value if provided
- `allowed_values`: array[any] - Constrained list of allowed values
- `min_length`: integer - Minimum length for string parameters
- `max_length`: integer - Maximum length for string parameters
- `environment_specific`: boolean - Whether value varies by environment

**Validation Rules**:
- `name` must be valid Bicep parameter name format
- `type` must be valid Bicep type
- `description` must be non-empty
- `default_value` must match parameter type if provided
- `allowed_values` must all match parameter type
- String length constraints must be positive integers

**Relationships**:
- Belongs to one `BicepTemplate`
- Has values defined in multiple `ParameterFile` instances

### Parameter File

Environment-specific parameter file (e.g., dev.parameters.json, prod.parameters.json).

**Attributes**:
- `environment`: string - Environment name (dev, staging, prod)
- `file_path`: string - Path to parameter file
- `parameters`: object - Key-value pairs of parameter values
- `schema_version`: string - Parameter file schema version
- `description`: string - Environment-specific description

**Validation Rules**:
- `environment` must be non-empty valid identifier
- `file_path` must end with .parameters.json
- `parameters` must contain values for all required template parameters
- `schema_version` must be current Azure parameter file schema
- Parameter values must match template parameter types

**Relationships**:
- Associated with multiple `BicepTemplate` instances
- Belongs to one `DeploymentConfiguration`

### Deployment Configuration

Settings for target environment including region, subscription, and naming patterns.

**Attributes**:
- `target_environments`: array[string] - List of target environments (dev, staging, prod)
- `primary_region`: string - Primary Azure region for deployment
- `secondary_region`: string - Secondary region for multi-region deployments
- `subscription_id`: string - Target Azure subscription ID
- `resource_group_pattern`: string - Template for resource group naming
- `resource_naming_convention`: string - Pattern for individual resource names
- `tags`: object - Default tags to apply to all resources
- `scaling_requirements`: object - Performance and scale targets
- `security_requirements`: object - Security constraints and requirements

**Validation Rules**:
- `target_environments` must contain at least one valid environment
- `primary_region` must be valid Azure region
- `subscription_id` must be valid GUID format
- `resource_group_pattern` must contain valid naming placeholders
- `resource_naming_convention` must follow Azure naming rules
- `tags` must contain valid Azure tag key-value pairs

**Relationships**:
- Associated with one `ProjectAnalysis`
- References multiple `ParameterFile` instances
- Influences all `BicepTemplate` generation

### Template Update Manifest

Information about which templates have changed and why, used for incremental updates.

**Attributes**:
- `update_timestamp`: datetime - When the update analysis was performed
- `changed_files`: array[string] - Project files that changed since last generation
- `affected_templates`: array[string] - Templates that need updating
- `new_requirements`: array[ResourceRequirement] - Newly detected service requirements
- `removed_requirements`: array[string] - Service types no longer needed
- `update_summary`: string - Human-readable summary of changes
- `backup_created`: boolean - Whether backup files were created
- `validation_required`: boolean - Whether updated templates need validation

**Validation Rules**:
- `update_timestamp` cannot be in the future
- `changed_files` must contain valid file paths
- `affected_templates` must reference existing template files
- `new_requirements` must be valid ResourceRequirement instances
- `removed_requirements` must be valid Azure resource types

**Relationships**:
- References multiple `BicepTemplate` instances
- Associated with `ProjectAnalysis` comparison
- May trigger generation of new `ResourceRequirement` instances

### Architecture Documentation

Markdown file explaining the generated infrastructure, design decisions, and deployment guidance.

**Attributes**:
- `document_path`: string - Path to the architecture markdown file
- `architecture_overview`: string - High-level architecture description
- `resource_inventory`: array[object] - List of all generated resources with descriptions
- `design_decisions`: array[object] - Key architectural decisions and rationale
- `deployment_instructions`: string - Step-by-step deployment guidance
- `troubleshooting_guide`: string - Common issues and solutions
- `cost_estimates`: object - Estimated monthly costs per environment
- `security_considerations`: string - Security implications and recommendations
- `monitoring_recommendations`: string - Suggested monitoring and alerting setup

**Validation Rules**:
- `document_path` must end with .md extension
- `architecture_overview` must be non-empty
- `resource_inventory` must include all generated templates
- `design_decisions` must explain major choices
- `deployment_instructions` must be actionable

**Relationships**:
- Generated from one `ProjectAnalysis`
- References all associated `BicepTemplate` instances
- Incorporates information from `DeploymentConfiguration`

## Data Flow Relationships

```text
ProjectAnalysis
├── generates → ResourceRequirement[]
├── creates → DeploymentConfiguration
└── produces → ArchitectureDocumentation

ResourceRequirement
├── generates → BicepTemplate
└── influences → ParameterFile values

BicepTemplate
├── contains → TemplateParameter[]
├── uses → ParameterFile[]
└── references → other BicepTemplate[] (dependencies)

DeploymentConfiguration
├── creates → ParameterFile[] (per environment)
└── influences → BicepTemplate generation

TemplateUpdateManifest
├── identifies → BicepTemplate[] (for updates)
├── triggers → ResourceRequirement[] (new/removed)
└── preserves → custom modifications
```

## Persistence Strategy

### File System Organization

```text
bicep-templates/
├── compute/
│   ├── app-service.bicep
│   └── function-app.bicep
├── storage/
│   ├── storage-account.bicep
│   └── key-vault.bicep
├── networking/
│   └── virtual-network.bicep
├── security/
│   └── managed-identity.bicep
├── parameters/
│   ├── dev.parameters.json
│   ├── staging.parameters.json
│   └── prod.parameters.json
├── backups/
│   └── [timestamp]/
└── architecture.md
```

### State Tracking

- **Project analysis state**: Stored in `.bicep-generator/analysis.json`
- **Template metadata**: Stored in `.bicep-generator/templates.json`
- **Update tracking**: Stored in `.bicep-generator/updates.json`
- **Validation cache**: Stored in `.bicep-generator/validation-cache.json`

This data model provides the foundation for robust template generation, validation, and incremental updates while maintaining clear separation of concerns and enabling comprehensive project analysis.