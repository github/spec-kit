# Research: Bicep Generator Command

**Feature**: 002-bicep-generator-command  
**Date**: 2025-10-21  
**Phase**: 0 - Research & Technical Validation

## Technical Decisions

### Azure MCP Server Integration

**Decision**: Use Azure MCP Server with bicepschema_get tool for real-time Bicep schema retrieval

**Rationale**: 
- Provides direct access to Azure Resource Provider APIs for latest schema definitions
- Eliminates need to maintain static schema files
- Supports all Azure resource types with current API versions
- Built-in authentication integration with Azure Identity library

**Alternatives considered**:
- Static Bicep schema files: Rejected due to maintenance overhead and staleness risk
- Direct Azure REST API calls: Rejected due to complexity and authentication challenges
- Azure Resource Manager templates: Rejected as less modern than Bicep approach

### PowerShell Cross-Platform Strategy

**Decision**: Target PowerShell 7.x with PowerShell 5.1 fallback for Windows

**Rationale**:
- PowerShell 7.x provides true cross-platform support (Windows, macOS, Linux)
- PowerShell 5.1 still widely used on Windows enterprise environments
- Azure PowerShell module (Az) works on both versions
- Enables consistent experience across development environments

**Alternatives considered**:
- PowerShell 5.1 only: Rejected due to Windows-only limitation
- PowerShell 7.x only: Rejected due to enterprise Windows compatibility needs
- Bash scripts: Rejected as less aligned with existing Specify CLI PowerShell patterns

### Template Validation Approach

**Decision**: Multi-layered validation using Bicep CLI and Azure Resource Manager

**Rationale**:
- Bicep CLI provides fast syntax validation without Azure connectivity
- Azure Resource Manager validation ensures deployment compatibility
- Layered approach catches errors at multiple stages
- Provides comprehensive feedback to users before deployment

**Alternatives considered**:
- Bicep CLI only: Rejected as insufficient for deployment validation
- ARM validation only: Rejected as slower and requires Azure connectivity for all checks
- No validation: Rejected as user experience would be poor with deployment failures

### Project Analysis Strategy

**Decision**: Comprehensive file analysis including documentation and scripts

**Rationale**:
- Documentation often contains architecture decisions and requirements
- Scripts may reveal deployment patterns and service dependencies
- Configuration files contain explicit Azure service references
- Comprehensive analysis reduces missed dependencies

**Alternatives considered**:
- Configuration files only: Rejected as potentially missing implicit dependencies
- Source code only: Rejected as may miss deployment-specific requirements
- Git history analysis: Rejected as too complex and potentially misleading

### Template Organization Pattern

**Decision**: Resource type-based folder hierarchy (compute/, storage/, networking/, security/)

**Rationale**:
- Aligns with Azure Well-Architected Framework organization principles
- Facilitates template reuse across projects and environments
- Clear separation of concerns for different infrastructure layers
- Supports Ev2 deployment patterns and conventions

**Alternatives considered**:
- Environment-based folders: Rejected as creates template duplication
- Flat structure: Rejected as unscalable for complex projects
- Component-based: Rejected as less aligned with Azure service boundaries

### Environment Configuration Strategy

**Decision**: Parameterized templates with environment-specific parameter files

**Rationale**:
- Single template reduces maintenance overhead
- Parameter files enable environment-specific configurations
- Follows Azure deployment best practices
- Supports CI/CD pipeline integration

**Alternatives considered**:
- Environment-specific templates: Rejected due to duplication and maintenance burden
- Single universal template: Rejected as insufficient for environment differences
- Environment overlays: Rejected as more complex than parameter file approach

## Integration Architecture

### MCP Server Communication Pattern

```text
GitHub Copilot Command → PowerShell Script → Python MCP Client → Azure MCP Server → Azure APIs
```

**Authentication Flow**:
1. Use Azure Identity DefaultAzureCredential
2. Fall back through: Azure CLI → Azure PowerShell → Visual Studio → Managed Identity
3. Cross-platform authentication detection and selection

### File Generation Workflow

```text
Project Analysis → Dependency Detection → Schema Retrieval → Template Generation → Validation → Organization
```

**Validation Layers**:
1. Syntax validation via Bicep CLI
2. Schema validation via Azure MCP Server
3. Deployment validation via Azure Resource Manager
4. Best practices validation via custom rules

### Update Detection Strategy

**Approach**: File timestamp comparison with dependency graph analysis

**Components**:
- Configuration file modification tracking
- Dependency manifest change detection
- Manual customization preservation via comment markers
- Backup file generation for safety

## Technology Stack Validation

### Core Dependencies

- **Azure MCP Server**: Bicep schema operations and Azure integration
- **PowerShell 7.x/5.1**: Cross-platform scripting and Azure PowerShell modules
- **Python 3.11+**: MCP client implementation and integration logic
- **Bicep CLI**: Template compilation and syntax validation
- **Azure CLI**: Authentication and resource management

### Development Tools

- **Pester**: PowerShell script testing framework
- **pytest**: Python component testing framework
- **ARM Template Validation**: Azure Resource Manager deployment testing

### Performance Considerations

- **Template Generation**: Target under 10 minutes for typical projects
- **Validation**: Target under 2 minutes for template validation
- **File Analysis**: Parallel processing for large projects (1000+ files)
- **Caching**: Schema caching to improve repeated operations

## Risk Mitigation

### Azure MCP Server Unavailability

**Fallback Strategy**: Provide specifications for custom Bicep MCP Server development
- Repository: https://github.com/ajsharm_microsoft/applens-mcp-servers
- Minimal viable implementation for schema retrieval
- Local schema caching for offline scenarios

### Authentication Failures

**Mitigation**: Multi-tier authentication fallback with clear error messages
- Detect available authentication methods
- Guide users through authentication setup
- Provide manual authentication alternatives

### Template Validation Failures

**Mitigation**: Graceful degradation with informative feedback
- Continue with warnings for non-critical validation failures
- Provide detailed error context for syntax issues
- Offer manual review and override options

## Research Validation Complete

All technical unknowns have been researched and resolved. The architecture provides a robust foundation for implementation with clear fallback strategies for potential integration challenges.