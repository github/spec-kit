# Bicep Generator - Architecture Guide

## Table of Contents

- [Overview](#overview)
- [Design Principles](#design-principles)
- [System Architecture](#system-architecture)
- [Component Design](#component-design)
- [Data Flow](#data-flow)
- [Integration Points](#integration-points)
- [Security Architecture](#security-architecture)
- [Performance Optimization](#performance-optimization)
- [Error Handling Strategy](#error-handling-strategy)
- [Extension Points](#extension-points)

## Overview

The Bicep Generator is a sophisticated system for automatically generating Azure infrastructure templates from application code analysis. It combines static analysis, Azure MCP Server integration, and intelligent template generation to create production-ready infrastructure-as-code.

### Key Capabilities

- **Intelligent Analysis**: Detects Azure service dependencies from code patterns
- **Schema-Driven Generation**: Uses real Azure schemas via MCP Server
- **Best Practices**: Applies Azure Well-Architected Framework principles
- **Security First**: Built-in security analysis and hardening
- **Performance**: Caching and async processing for speed
- **Extensible**: Plugin architecture for custom analysis

## Design Principles

### 1. Separation of Concerns

Each component has a single, well-defined responsibility:

```
Analysis → Generation → Validation → Deployment
```

Components communicate through well-defined interfaces and data models.

### 2. Async-First Design

All I/O operations are asynchronous to maximize throughput:

```python
# Async throughout the stack
async def analyze() -> ProjectAnalysis
async def generate() -> GenerationResult
async def deploy() -> DeploymentResult
```

### 3. Fail-Fast with Recovery

Errors are detected early but recovery strategies are provided:

```python
try:
    result = await generator.generate()
except GenerationError as e:
    recovery = error_handler.handle_error(e)
    if recovery.can_retry:
        result = await generator.generate()  # Retry with adjusted params
```

### 4. Cache-Aware

Expensive operations are cached with appropriate TTL:

- Schema lookups: 1 hour
- Analysis results: 30 minutes
- Validation results: 15 minutes

### 5. Security by Default

Secure configurations are the default:

- HTTPS only
- TLS 1.2+ minimum
- No public endpoints
- RBAC enabled
- Key Vault for secrets

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Specify CLI                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Analyze  │→→│  Generate  │→→│  Validate  │→→Deploy    │
│  └────────────┘  └────────────┘  └────────────┘            │
└────────┬────────────────┬────────────────┬──────────────────┘
         │                │                │
         ↓                ↓                ↓
┌────────────────┐ ┌─────────────────────────────────────────┐
│   File System  │ │        Azure MCP Server                 │
│   - Config     │ │  ┌──────────────┐  ┌────────────────┐  │
│   - Source     │ │  │ Schema API   │  │ Best Practices │  │
│   - Templates  │ │  └──────────────┘  └────────────────┘  │
└────────────────┘ └─────────────────────────────────────────┘
                                     ↓
                            ┌─────────────────┐
                            │   Azure Portal  │
                            │   ARM/Bicep     │
                            └─────────────────┘
```

### Component Architecture

```
src/specify_cli/bicep/
│
├── Core Components
│   ├── analyzer.py           # Project analysis engine
│   ├── generator.py          # Template generation
│   ├── validator.py          # Template validation
│   └── deployer.py           # Azure deployment
│
├── Integration Layer
│   ├── mcp_client.py         # Azure MCP Server client
│   └── bicep_utils.py        # Bicep CLI integration
│
├── Advanced Features
│   ├── cost_estimator.py     # Cost analysis
│   ├── security_analyzer.py  # Security scanning
│   ├── template_editor.py    # Interactive editing
│   └── explanation_engine.py # Template explanations
│
├── Cross-Cutting Concerns
│   ├── error_handler.py      # Error management
│   ├── performance.py        # Caching & monitoring
│   ├── security.py           # Input validation, auth
│   └── type_checker.py       # Code quality
│
└── Data Models
    └── models/
        ├── analysis_models.py
        ├── template_models.py
        └── deployment_models.py
```

## Component Design

### 1. ProjectAnalyzer

**Purpose**: Analyze project for Azure resource requirements

**Inputs**:
- Project directory path
- Configuration file (optional)
- Analysis options

**Outputs**:
- `ProjectAnalysis` object
- List of detected resources
- Configuration settings
- Secret references

**Key Algorithms**:

1. **Dependency Detection**
```python
def detect_dependencies(self) -> List[ServiceDependency]:
    # 1. Scan configuration files (appsettings.json, etc.)
    # 2. Parse connection strings
    # 3. Detect SDK usage patterns
    # 4. Analyze import statements
    # 5. Calculate confidence scores
    # 6. Return ranked dependencies
```

2. **Secret Scanning**
```python
def detect_secrets(self) -> List[SecretReference]:
    # 1. Pattern matching for common secret formats
    # 2. Entropy analysis for random strings
    # 3. Check against known secret patterns
    # 4. Return locations and severity
```

**Performance Considerations**:
- Uses async file I/O for large projects
- Skips common directories (node_modules, .git, etc.)
- Caches analysis results for incremental updates
- Parallel processing for multiple file types

---

### 2. BicepGenerator

**Purpose**: Generate Bicep templates from analysis

**Inputs**:
- `ProjectAnalysis` object
- Generator configuration
- Target environment

**Outputs**:
- Bicep template files
- Parameter files
- Module files
- README documentation

**Generation Pipeline**:

```
Analysis → Resource Specification → Schema Retrieval → Template Generation
```

**Key Algorithms**:

1. **Resource Graph Building**
```python
def build_resource_graph(self) -> ResourceGraph:
    # 1. Create nodes for each resource
    # 2. Identify dependencies
    # 3. Build directed acyclic graph (DAG)
    # 4. Topological sort for deployment order
    # 5. Detect and break circular dependencies
```

2. **Template Synthesis**
```python
def synthesize_template(self, resource: ResourceSpec) -> str:
    # 1. Retrieve schema from MCP Server
    # 2. Map analysis data to schema properties
    # 3. Apply best practices (naming, SKUs, etc.)
    # 4. Generate Bicep syntax
    # 5. Add inline documentation
    # 6. Format output
```

**Design Patterns**:
- **Strategy Pattern**: Different generation strategies (modular vs monolithic)
- **Builder Pattern**: Incremental template construction
- **Template Method**: Common generation flow with customization hooks

---

### 3. MCPClient

**Purpose**: Interface with Azure MCP Server

**Responsibilities**:
- Schema retrieval
- Best practices queries
- Resource provider information

**Architecture**:

```
┌──────────────────┐
│   MCPClient      │
├──────────────────┤
│  - session       │
│  - transport     │
│  - schema_cache  │
├──────────────────┤
│  + get_schema()  │
│  + get_practices()│
│  + list_providers()│
└──────────────────┘
         ↓
┌──────────────────┐
│  MCP Protocol    │
│  (stdio/JSON-RPC)│
└──────────────────┘
         ↓
┌──────────────────┐
│  Azure MCP       │
│  Server (Python) │
└──────────────────┘
```

**Connection Management**:

```python
class MCPClient:
    async def __aenter__(self):
        # 1. Start MCP server process
        # 2. Establish stdio connection
        # 3. Initialize client session
        # 4. Verify connectivity
        return self
    
    async def __aexit__(self, *args):
        # 1. Close client session
        # 2. Terminate server process
        # 3. Cleanup resources
```

**Caching Strategy**:
- Schema cache: LRU with 1-hour TTL, 500 entries, 50MB limit
- Automatic cache warming on startup
- Cache invalidation on schema updates

---

### 4. TemplateValidator

**Purpose**: Comprehensive template validation

**Validation Layers**:

```
1. Syntax Validation (Bicep CLI)
   ↓
2. Schema Validation (Azure schemas)
   ↓
3. Best Practices (Well-Architected Framework)
   ↓
4. Security Validation (Security policies)
   ↓
5. Deployment Validation (Azure ARM)
```

**Validation Rules**:

- **Syntax**: Valid Bicep syntax, no compilation errors
- **Schema**: Properties match Azure resource schemas
- **Naming**: Follow Azure naming conventions
- **Security**: No insecure configurations
- **Cost**: No unnecessarily expensive SKUs
- **Dependencies**: All dependencies resolvable

---

### 5. BicepDeployer

**Purpose**: Deploy templates to Azure

**Deployment Flow**:

```
Pre-Deployment Checks
   ↓
Create Deployment
   ↓
Monitor Progress
   ↓
Handle Errors
   ↓
Post-Deployment Validation
```

**Safety Features**:

1. **Dry Run Mode**: Validate without deploying
2. **Incremental Mode**: Only update changed resources
3. **Rollback Support**: Automatic rollback on failure
4. **Progress Tracking**: Real-time deployment status

## Data Flow

### Analysis to Deployment Flow

```
┌──────────────────┐
│  Project Files   │
└────────┬─────────┘
         ↓
┌────────────────────────────────┐
│  ProjectAnalyzer               │
│  - Scans files                 │
│  - Detects dependencies        │
│  - Extracts configuration      │
└────────┬───────────────────────┘
         ↓
    ProjectAnalysis (JSON)
         ↓
┌────────────────────────────────┐
│  BicepGenerator                │
│  - Builds resource graph       │
│  - Retrieves schemas (MCP)     │
│  - Generates templates         │
└────────┬───────────────────────┘
         ↓
    Bicep Templates (.bicep)
         ↓
┌────────────────────────────────┐
│  TemplateValidator             │
│  - Validates syntax            │
│  - Checks security             │
│  - Verifies best practices     │
└────────┬───────────────────────┘
         ↓
    ValidationResult
         ↓
┌────────────────────────────────┐
│  BicepDeployer                 │
│  - Creates deployment          │
│  - Monitors progress           │
│  - Returns results             │
└────────┬───────────────────────┘
         ↓
    Azure Resources
```

### Data Model Relationships

```
ProjectAnalysis
  ├── resources: List[ResourceSpec]
  ├── dependencies: List[ServiceDependency]
  ├── configuration: Dict[str, Any]
  └── secrets: List[SecretReference]

ResourceSpec
  ├── resource_type: str
  ├── properties: Dict[str, Any]
  ├── sku: SkuSpec
  └── dependencies: List[str]

GenerationResult
  ├── files: List[Path]
  ├── errors: List[GenerationError]
  └── warnings: List[str]

ValidationResult
  ├── errors: List[ValidationError]
  ├── warnings: List[ValidationWarning]
  └── info: List[str]

DeploymentResult
  ├── resources: List[str]
  ├── outputs: Dict[str, Any]
  └── errors: List[DeploymentError]
```

## Integration Points

### 1. Azure MCP Server

**Protocol**: JSON-RPC over stdio

**Communication Pattern**:

```python
# Request
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "mcp_bicep_experim_get_az_resource_type_schema",
        "arguments": {
            "azResourceType": "Microsoft.Storage/storageAccounts",
            "apiVersion": "2023-01-01"
        }
    }
}

# Response
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "content": [{
            "type": "text",
            "text": "{\"properties\": {...}, \"required\": [...]}"
        }]
    }
}
```

**Error Handling**:
- Connection failures → Retry with exponential backoff
- Schema not found → Use fallback templates
- Timeout → Cancel request, use cache

---

### 2. Azure CLI

**Purpose**: Resource deployment and management

**Integration Pattern**:

```python
async def deploy_template(self, template_path: Path) -> DeploymentResult:
    # Use Azure CLI for deployment
    cmd = [
        "az", "deployment", "group", "create",
        "--resource-group", self.resource_group,
        "--template-file", str(template_path),
        "--parameters", f"@{self.parameters_file}"
    ]
    
    result = await run_command(cmd)
    return self.parse_deployment_result(result)
```

**Fallback Strategy**:
If Azure CLI unavailable → Use Azure SDK directly

---

### 3. Bicep CLI

**Purpose**: Template compilation and validation

**Integration Pattern**:

```python
async def validate_syntax(self, template_path: Path) -> List[ValidationError]:
    # Use Bicep CLI for validation
    cmd = ["bicep", "build", str(template_path), "--stdout"]
    
    result = await run_command(cmd)
    
    if result.returncode != 0:
        return self.parse_bicep_errors(result.stderr)
    
    return []
```

**Version Management**:
- Check Bicep CLI version on startup
- Warn if version < 0.15.0
- Adjust output for different versions

## Security Architecture

### Defense in Depth

```
Layer 1: Input Validation
   ↓
Layer 2: Authentication & Authorization
   ↓
Layer 3: Secure Communication
   ↓
Layer 4: Audit Logging
   ↓
Layer 5: Secret Management
```

### Security Components

#### 1. Input Validation

```python
from specify_cli.bicep.security import InputValidator

validator = InputValidator()

# Validate all user inputs
resource_name = validator.validate(
    user_input,
    ValidationRule.AZURE_RESOURCE_NAME
)

# Sanitize file paths
safe_path = validator.is_safe_path(Path(user_path))
```

**Validation Rules**:
- Resource names: Length, characters, patterns
- File paths: No directory traversal
- Configuration: No injection attacks

#### 2. Credential Management

```python
from specify_cli.bicep.security import credential_manager

# Secure credential storage with encryption
credential_manager.set_credential("azure_token", token)

# Automatic rotation
credential_manager.rotate_credential("azure_token", new_token)

# Secure retrieval
token = credential_manager.get_credential("azure_token")
```

**Security Features**:
- HMAC-SHA256 encryption
- Environment variable priority
- No credentials in logs
- Automatic expiration

#### 3. Rate Limiting

```python
from specify_cli.bicep.security import rate_limited

@rate_limited(max_calls=100, time_window=60)
async def call_azure_api():
    # Protected from abuse
    pass
```

**Rate Limits**:
- Analysis: 10 per minute
- Generation: 20 per minute
- Deployment: 5 per minute

#### 4. Audit Logging

```python
from specify_cli.bicep.security import security_auditor

# All security events logged
security_auditor.log_event(
    event_type="deployment",
    resource="my-resource-group",
    action="create",
    user=current_user,
    success=True,
    level=SecurityLevel.MEDIUM
)
```

**Audit Events**:
- Authentication attempts
- Resource access
- Configuration changes
- Deployment operations
- Security violations

## Performance Optimization

### Caching Strategy

```
┌─────────────────┐
│  Schema Cache   │  ← 1-hour TTL, 500 entries
├─────────────────┤
│  Analysis Cache │  ← 30-min TTL, 100 entries
├─────────────────┤
│  Validation     │  ← 15-min TTL, 200 entries
└─────────────────┘
```

**Cache Implementation**:

```python
from specify_cli.bicep.performance import cached, schema_cache

@cached(cache=schema_cache)
async def get_bicep_schema(resource_type: str, api_version: str):
    # Expensive operation cached
    return await mcp_client.get_schema(resource_type, api_version)
```

### Async Processing

**Pattern**: Concurrent resource generation

```python
async def generate_all_resources(resources: List[ResourceSpec]) -> List[str]:
    # Generate multiple resources concurrently
    tasks = [generate_resource(r) for r in resources]
    return await asyncio.gather(*tasks)
```

**Benefits**:
- 5-10x faster for multiple resources
- Better resource utilization
- Responsive UI during long operations

### Performance Monitoring

```python
from specify_cli.bicep.performance import PerformanceTimer

async with PerformanceTimer("operation_name", items_processed=count):
    result = await expensive_operation()

# Automatically tracks:
# - Duration
# - Throughput
# - Memory usage
# - Error rate
```

### Optimization Techniques

1. **Lazy Loading**: Load schemas only when needed
2. **Batch Processing**: Group similar operations
3. **Connection Pooling**: Reuse MCP connections
4. **Memory Management**: Clear caches proactively
5. **Parallel Processing**: Use multiple workers

## Error Handling Strategy

### Error Hierarchy

```
BicepError (base)
├── AnalysisError
│   ├── DependencyDetectionError
│   └── ConfigurationError
├── GenerationError
│   ├── TemplateGenerationError
│   └── SchemaError
├── ValidationError
│   ├── SyntaxError
│   ├── SchemaValidationError
│   └── SecurityValidationError
└── DeploymentError
    ├── AuthenticationError
    ├── PermissionError
    └── ResourceConflictError
```

### Error Recovery

```python
class ErrorRecovery:
    can_retry: bool              # Can operation be retried?
    suggested_action: str        # What user should do
    recovery_steps: List[str]    # Automated recovery steps
    fallback_available: bool     # Is there a fallback?
```

**Recovery Strategies**:

1. **Retry with Backoff**: Transient network errors
2. **Fallback Templates**: Missing schemas
3. **Skip and Continue**: Non-critical validations
4. **Manual Intervention**: Permission errors

### Logging

**Log Levels**:

- **DEBUG**: Detailed diagnostic information
- **INFO**: General progress updates
- **WARNING**: Non-critical issues
- **ERROR**: Operation failures
- **CRITICAL**: System-level failures

**Structured Logging**:

```python
{
    "timestamp": "2025-01-21T10:30:00Z",
    "level": "ERROR",
    "category": "generation",
    "message": "Failed to generate template",
    "resource_type": "Microsoft.Storage/storageAccounts",
    "error_code": "SCHEMA_RETRIEVAL_FAILED",
    "can_retry": true
}
```

## Extension Points

### Custom Analyzers

```python
from specify_cli.bicep import BaseAnalyzer

class CustomAnalyzer(BaseAnalyzer):
    def analyze(self) -> List[ServiceDependency]:
        # Custom analysis logic
        pass

# Register plugin
analyzer.register_plugin(CustomAnalyzer())
```

### Template Customization

```python
from specify_cli.bicep import TemplateCustomizer

class CustomTemplateCustomizer(TemplateCustomizer):
    def customize(self, template: str, resource: ResourceSpec) -> str:
        # Custom template modifications
        pass

generator.add_customizer(CustomTemplateCustomizer())
```

### Validation Rules

```python
from specify_cli.bicep import ValidationRule

class CustomValidationRule(ValidationRule):
    def validate(self, template: str) -> List[ValidationError]:
        # Custom validation logic
        pass

validator.add_rule(CustomValidationRule())
```

## Testing Strategy

### Unit Tests

- Each component tested in isolation
- Mock external dependencies (Azure MCP Server, Azure CLI)
- Fast execution (< 1 second per test)

### Integration Tests

- Test component interactions
- Use test fixtures for Azure resources
- Longer execution (5-30 seconds per test)

### End-to-End Tests

- Full workflow from analysis to deployment
- Use test Azure subscriptions
- Cleanup after tests

### Performance Tests

- Benchmark key operations
- Track performance regression
- Test with large projects

## Deployment Architecture

### Development Environment

```
Local Machine
├── Python 3.11+ virtual environment
├── Azure CLI
├── Bicep CLI
├── Azure MCP Server (local)
└── Test Azure subscription
```

### Production Environment

```
CI/CD Pipeline (GitHub Actions)
├── Build and test
├── Package for PyPI
├── Deploy documentation
└── Create GitHub release
```

## Future Architecture Considerations

### Planned Enhancements

1. **Plugin System**: Third-party extensions
2. **Terraform Support**: Generate Terraform instead of Bicep
3. **Multi-Cloud**: AWS CloudFormation, Google Deployment Manager
4. **GUI**: Visual template editor
5. **CI/CD Integration**: GitHub Actions, Azure DevOps pipelines

### Scalability

Current architecture supports:
- Projects up to 100,000 files
- Templates with 1,000+ resources
- Concurrent analysis of multiple projects

## Additional Resources

- [API Reference](./api-reference.md)
- [User Guide](./user-guide.md)
- [Troubleshooting Guide](./troubleshooting.md)
- [Azure MCP Server Documentation](https://github.com/microsoft/azure-mcp-server)
- [Azure Bicep Documentation](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)
